from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import (
    CLOUD_RETRY_BASE_DELAY_SECONDS,
    CLOUD_RETRY_COUNT,
    CLOUD_RETRY_MAX_DELAY_SECONDS,
    DEFAULT_MODEL,
    RuntimeDeps,
    missing_rule,
    requirement_label,
    requirement_rule,
    short_error,
)
from .text_safety import json_dumps_utf8


def tail_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def get_ollama_models(base_url: str) -> list[str]:
    url = base_url.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]


def choose_model(requested_model: str, available_models: list[str]) -> str:
    if requested_model in available_models:
        return requested_model
    for model in [DEFAULT_MODEL, "qwen3.5:9b", "deepseek-r1:7b", "gemma4:e4b", "gpt-oss:20b"]:
        if model in available_models:
            return model
    if available_models:
        return available_models[0]
    raise RuntimeError("Ollama 没有可用模型，请先在 Ollama 中安装模型。")


def model_order(primary_model: str, available_models: list[str], auto_fallback: bool) -> list[str]:
    if not auto_fallback:
        return [primary_model]
    candidates = [primary_model, DEFAULT_MODEL, "qwen3.5:9b", "deepseek-r1:7b", "gemma4:e4b", "gpt-oss:20b"]
    out: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item in available_models and item not in seen:
            out.append(item)
            seen.add(item)
    return out or [primary_model]


def pydantic_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if isinstance(result, dict):
        return result
    raise TypeError(f"无法转换 LLM 返回值：{type(result)!r}")


def message_content(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def raw_records(raw: dict[str, Any]) -> list[dict[str, Any]]:
    records = raw.get("records")
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def blank_labeled_row(fields: list[dict[str, str]], key_to_label: dict[str, str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for index, _item in enumerate(fields, start=1):
        key = f"field_{index:02d}"
        row[key_to_label[key]] = ""
    return row


def labeled_rows(
    raw: dict[str, Any], fields: list[dict[str, str]], key_to_label: dict[str, str],
) -> list[dict[str, Any]]:
    from .quality import normalize_cloud_value
    rows: list[dict[str, Any]] = []
    for record in raw_records(raw):
        row: dict[str, Any] = {}
        for index, item in enumerate(fields, start=1):
            key = f"field_{index:02d}"
            label = key_to_label[key]
            row[label] = normalize_cloud_value(record.get(key), item["type"])
        rows.append(row)
    return rows or [blank_labeled_row(fields, key_to_label)]


def build_extraction_chain(
    model_name: str, base_url: str, num_ctx: int, llm_timeout: int,
    runtime: RuntimeDeps, extraction_model: Any,
):
    client_kwargs = {} if llm_timeout <= 0 else {"timeout": llm_timeout}
    llm = runtime.ChatOllama(
        model=model_name, temperature=0, num_ctx=num_ctx, num_predict=1024,
        keep_alive="30m", base_url=base_url, sync_client_kwargs=client_kwargs,
    )
    structured_llm = llm.with_structured_output(extraction_model)
    prompt = runtime.ChatPromptTemplate.from_messages([
        (
            "system",
            "你是专业的化工领域学术数据抽取助手。请阅读从 PDF 转换得到的 Markdown 或文本，"
            "严格按照结构化输出字段抽取数据。文献可能是中文、英文或中英混合。"
            "只能依据原文，不要编造。任何字段缺失时留空，不要填 N/A、null 或 -999。"
            "如果同一篇文献包含多个工艺、催化剂、实验条件、表格行或独立结果，"
            "请在 records 中拆成多条记录；只有一条结果时也输出一条 records。",
        ),
        (
            "human",
            "文件名：{file_name}\n\n"
            "需要抽取的字段：\n{field_instructions}\n\n"
            "{quality_hint}\n\n"
            "PDF 转换文本如下，可能已截断：\n\n{markdown_text}",
        ),
    ])
    return prompt | structured_llm


def cloud_chat_completion(
    base_url: str, api_key: str, model: str,
    messages: list[dict[str, str]], llm_timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    last_exc: BaseException | None = None
    for attempt in range(CLOUD_RETRY_COUNT):
        body = {
            "model": model, "messages": messages, "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        data = json_dumps_utf8(body).encode("utf-8")
        request = urllib.request.Request(
            url, data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json", "Accept": "application/json",
            },
            method="POST",
        )
        try:
            if llm_timeout and llm_timeout > 0:
                response_ctx = urllib.request.urlopen(request, timeout=llm_timeout)
            else:
                response_ctx = urllib.request.urlopen(request)
            with response_ctx as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return payload["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            last_exc = exc
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if not retryable or attempt >= CLOUD_RETRY_COUNT - 1:
                body_text = ""
                try:
                    body_text = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                raise RuntimeError(f"云端 API HTTP {exc.code}: {tail_text(body_text)}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError) as exc:
            last_exc = exc
            if attempt >= CLOUD_RETRY_COUNT - 1:
                raise RuntimeError(f"云端 API 请求失败：{short_error(exc)}") from exc
        delay = min(CLOUD_RETRY_MAX_DELAY_SECONDS, CLOUD_RETRY_BASE_DELAY_SECONDS * (2**attempt))
        time.sleep(delay)
    raise RuntimeError(f"云端 API 请求失败：{short_error(last_exc) if last_exc else 'unknown error'}")


def translate_item_batch_to_chinese_cloud(
    base_url: str, api_key: str, model: str,
    items: list[dict[str, str]], llm_timeout: int,
) -> dict[str, str]:
    from .quality import parse_translation_payload
    if not items:
        return {}
    messages = [
        {
            "role": "system",
            "content": (
                "你是化工文献数据清洗助手。请把用户给出的 JSON 数组中每个 text 翻译成简洁、准确的中文。"
                "只翻译自然语言和英文术语，保留化学式、CAS 号、数字、单位、百分号、型号和牌号。"
                "催化剂、反应器、物性方法、反应热、反应机理等术语要用化工领域常用中文。"
                "不要解释，不要补充原文没有的信息。"
                "只输出合法 JSON 对象，格式为 {\"items\":[{\"id\":\"...\",\"translation\":\"...\"}]}。"
            ),
        },
        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
    ]
    content = cloud_chat_completion(base_url, api_key, model, messages, llm_timeout)
    return parse_translation_payload(extract_json_object(content))


MODEL_DISCOVERY_ERROR = "Failed to fetch models. Please check Base URL, API key, or enter the model manually."


def build_openai_compatible_models_url(base_url: str) -> str:
    cleaned = str(base_url or "").strip()
    if not cleaned:
        raise RuntimeError("LLM BASE URL is empty.")
    return cleaned.rstrip("/") + "/models"


def parse_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    models: list[str] = []
    seen: set[str] = set()
    for item in data:
        if isinstance(item, str):
            model_id = item
        elif isinstance(item, dict):
            model_id = str(item.get("id") or item.get("name") or "").strip()
        else:
            continue
        if model_id and model_id not in seen:
            models.append(model_id)
            seen.add(model_id)
    return models


def parse_openai_compatible_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise ValueError("Invalid model list response: missing data list.")
    models: list[str] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Invalid model list response: model item is not an object.")
        model_id = str(item.get("id") or "").strip()
        if not model_id:
            raise ValueError("Invalid model list response: model id is missing.")
        if model_id not in seen:
            models.append(model_id)
            seen.add(model_id)
    if not models:
        raise ValueError("No models were returned by the provider.")
    return models


def fetch_openai_compatible_models(base_url: str, api_key: str, timeout: float = 10.0) -> list[str]:
    if not str(base_url or "").strip():
        raise RuntimeError("LLM BASE URL is empty.")
    if not str(api_key or "").strip():
        raise RuntimeError("LLM API KEY is empty.")
    url = build_openai_compatible_models_url(base_url)
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
        return parse_openai_compatible_model_ids(payload)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(MODEL_DISCOVERY_ERROR) from exc


def fetch_cloud_models_once(base_url: str, api_key: str, query: str = "") -> list[str]:
    url = base_url.rstrip("/") + "/models" + query
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return parse_model_ids(payload)


def get_cloud_models(base_url: str, api_key: str) -> list[str]:
    if not base_url:
        raise RuntimeError("LLM BASE URL 为空。")
    if not api_key:
        raise RuntimeError("LLM API KEY 为空。")
    errors: list[str] = []
    for query in ["?type=text&sub_type=chat", ""]:
        try:
            models = fetch_cloud_models_once(base_url, api_key, query)
            if models:
                return models
        except Exception as exc:
            errors.append(str(exc))
    details = "；".join(errors[-2:])
    raise RuntimeError(f"没有读取到云端模型列表。{details}")


def extract_with_cloud_api(
    pdf_path: Path, config: dict[str, Any], fields: list[dict[str, str]],
    key_to_label: dict[str, str], markdown_text: str, quality_hint: str = "",
) -> list[dict[str, Any]]:
    api_key = str(config.get("cloud_api_key") or "").strip()
    base_url = str(config.get("cloud_base_url") or "").strip()
    model = str(config.get("cloud_model") or config.get("model") or "").strip()
    if not api_key:
        raise RuntimeError("云端 API KEY 为空。请在页面填写 LLM API KEY。")
    if not base_url:
        raise RuntimeError("云端 BASE URL 为空。")
    if not model:
        raise RuntimeError("云端模型名称为空。")
    schema_lines = []
    for index, item in enumerate(fields, start=1):
        schema_lines.append(
            f'- "field_{index:02d}": {item["label"]} [{requirement_label(item.get("requirement", "optional"))}]，'
            f'{item["description"]}，{requirement_rule(item.get("requirement", "optional"))}，{missing_rule(item["type"])}'
        )
    messages = [
        {
            "role": "system",
            "content": (
                "你是专业的化工领域学术数据抽取助手。文献可能是中文、英文或中英混合。"
                "你必须只根据原文抽取，不要编造。"
                "只输出一个合法 JSON 对象，不要输出 Markdown，不要解释。"
                "JSON 顶层必须是 records 数组，例如 {\"records\":[{\"field_01\":\"...\"}]}。"
                "同一篇文献如果包含多个工艺、催化剂、实验条件、表格行或独立结果，就输出多条 records。"
                "任何字段缺失时留空字符串，不要输出 N/A、null 或 -999。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"文件名：{pdf_path.name}\n\n"
                "请按下面 JSON key 抽取字段：\n"
                + "\n".join(schema_lines)
                + (f"\n\n二次核查要求：\n{quality_hint}\n" if quality_hint else "")
                + "\n\nPDF 转换文本如下，可能已截断：\n\n"
                + markdown_text
            ),
        },
    ]
    content = cloud_chat_completion(base_url, api_key, model, messages, int(config.get("llm_timeout") or 0))
    raw = extract_json_object(content)
    return labeled_rows(raw, fields, key_to_label)
