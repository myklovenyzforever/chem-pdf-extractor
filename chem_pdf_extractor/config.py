from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "minicpm-v:latest"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MAX_CHARS = 80000
DEFAULT_NUM_CTX = 8192
DEFAULT_CLOUD_SERVICE_NAME = "openai_compatible"
DEFAULT_CLOUD_MODEL = "provider/model-name"
DEFAULT_CLOUD_BASE_URL = "https://api.example.com/v1"
DEFAULT_CLOUD_API_KEY = ""
LOCAL_CONFIG_NAME = "config.local.json"
DEFAULT_PDF_MODE = "pymupdf4llm"
PDF_MODE_CHOICES = ["auto", "pypdf_text", "pymupdf4llm", "pymupdf_text", "mineru"]
PLACEHOLDER_CLOUD_BASE_URL_MARKERS = {"api.example.com"}
PLACEHOLDER_CLOUD_MODELS = {"provider/model-name", "model-name", "your-model-name"}
PLACEHOLDER_CLOUD_API_KEYS = {
    "your_api_key_here",
    "your_api_key",
    "api_key_here",
    "your-key-here",
    "your-api-key",
    "sk-your-api-key",
}
MAX_ARTIFACT_NAME_CHARS = 80
OUTPUT_EXCEL_NAME = "提取结果.xlsx"
ERROR_LOG_NAME = "错误日志.txt"
PARTIAL_JSONL_NAME = "提取结果.partial.jsonl"
BAD_ROWS_EXCEL_NAME = "坏数据.xlsx"
BAD_ROWS_JSONL_NAME = "坏数据.jsonl"
SUSPICIOUS_ROWS_EXCEL_NAME = "可疑数据.xlsx"
SUSPICIOUS_ROWS_JSONL_NAME = "可疑数据.jsonl"
ERROR_STATS_EXCEL_NAME = "错误统计.xlsx"
ERROR_STATS_JSONL_NAME = "错误统计.jsonl"
MARKDOWN_DIR_NAME = "md文件"
CACHE_DIR_NAME = "抽取缓存"
FAILED_SOURCES_DIR_NAME = "提取失败源文件"
BUNDLED_RUNTIME_DIR_NAME = "bundled_runtime"
LEGACY_BUNDLED_RUNTIME_DIR_NAMES = ["YiLaiHuanJing", "运行依赖"]
BAD_ROW_MIN_FILL_RATE = 0.40
BAD_ROW_EMPTY_MARKERS = {"n/a", "na", "null", "none", "-999"}
BAD_ROW_FIELD_WEIGHTS = {"required": 1.0, "recommended": 0.5, "optional": 0.0}
EXTRACTION_CACHE_VERSION = "2026-05-quality-v2"
CLOUD_RETRY_COUNT = 3
CLOUD_RETRY_BASE_DELAY_SECONDS = 2.0
CLOUD_RETRY_MAX_DELAY_SECONDS = 20.0
DEFAULT_CLOUD_MODEL_SUGGESTIONS = ["provider/model-name"]

MINERU_COMMAND = os.environ.get("MINERU_COMMAND") or os.environ.get("MINERU_EXE") or "mineru"
MINERU_EXE = Path(MINERU_COMMAND)
MINERU_OUTPUT_ROOT = Path(os.environ.get("MINERU_OUTPUT_ROOT", str(PROJECT_ROOT / ".mineru_outputs")))
MINERU_DEFAULT_BACKEND = os.environ.get("MINERU_BACKEND", "pipeline")
MINERU_DEFAULT_METHOD = os.environ.get("MINERU_METHOD", "txt")
MINERU_DEFAULT_FORMULA = os.environ.get("MINERU_FORMULA", "false")
MINERU_DEFAULT_TABLE = os.environ.get("MINERU_TABLE", "false")

CORE_REQUIRED_PACKAGES = {
    "pypdf": "pypdf",
    "langchain": "langchain",
    "langchain_core": "langchain-core",
    "langchain_ollama": "langchain-ollama",
    "pydantic": "pydantic",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
}

OPTIONAL_PDF_BACKEND_PACKAGES = {
    "pymupdf4llm": "pymupdf4llm",
    "pymupdf": "pymupdf",
}

DEFAULT_FIELDS = [
    {"label": "工艺名称", "requirement": "required", "description": "文本（中文/英文）。抽取论文中的工艺、反应路线或过程名称。"},
    {"label": "原料", "requirement": "required", "description": "下拉列表。抽取主要原料、反应物或进料名称，可用分号分隔多个原料。"},
    {"label": "CAS号", "requirement": "required", "description": "文本，格式 xx-xx-x。抽取原料或核心物质 CAS 号，多个用分号分隔。"},
    {"label": "催化剂通用名", "requirement": "required", "description": "文本。抽取催化剂通用名称、简称或体系名称。"},
    {"label": "具体型号/牌号", "requirement": "recommended", "description": "文本（重要）。抽取商业牌号、型号、批号或论文中给出的具体催化剂编号。"},
    {"label": "催化剂制备方法", "requirement": "optional", "description": "文本描述。概括浸渍、沉淀、水热、焙烧、还原等制备步骤。"},
    {"label": "催化剂类型", "requirement": "recommended", "description": "下拉列表。归纳为金属、氧化物、分子筛、负载型、均相、酶、电催化剂等类型。"},
    {"label": "物理形状", "requirement": "optional", "description": "下拉列表。抽取粉末、颗粒、片状、球形、蜂窝、膜、电极等形态。"},
    {"label": "催化剂寿命", "requirement": "optional", "description": "文本。抽取寿命、稳定运行时间、循环次数、失活信息或再生信息。"},
    {"label": "反应温度（℃）", "requirement": "required", "description": "数字（℃）。只填摄氏温度数值；若原文为 K 或其他单位，换算为 ℃。"},
    {"label": "温度误差", "requirement": "recommended", "description": "数字 (℃)。抽取温度波动、误差或范围半宽；没有明确误差则留空。"},
    {"label": "反应压力（MPa）", "requirement": "required", "description": "数字（MPa）。只填 MPa 数值；若原文为 bar、atm、Pa 等，换算为 MPa。"},
    {"label": "压力误差", "requirement": "recommended", "description": "数字 (MPa)。抽取压力误差、波动或范围半宽；没有明确误差则留空。"},
    {"label": "反应规模/空速", "requirement": "recommended", "description": "数字 (h^-1)。优先抽取 GHSV、WHSV、LHSV、空速或规模；无法换算时保留原文表达。"},
    {"label": "数据类型/实验室/工业化", "requirement": "recommended", "description": "实验室小试/中试放大/工业化。根据论文实验规模和装置描述判断。"},
    {"label": "反应器形式", "requirement": "required", "description": "下拉列表。抽取固定床、釜式、管式、流化床、微反应器、电解槽、膜反应器等。"},
    {"label": "物性方法", "requirement": "required", "description": "下拉列表。抽取 GC、HPLC、GC-MS、NMR、滴定、在线分析、模拟方法或物性计算方法。"},
    {"label": "转化率（%）", "requirement": "required", "description": "数字（0-100）。抽取主要原料转化率，填百分数数值。"},
    {"label": "选择性（%）", "requirement": "required", "description": "下拉列表/数字。抽取目标产物选择性；若为数值，填百分数；若为定性分类，保留原文。"},
    {"label": "产物组成", "requirement": "required", "description": "抽取产物组成总体描述，包括主产物、副产物和组成比例来源。"},
    {"label": "产物1: 名称", "requirement": "required", "description": "文本。抽取第一种主要产物名称。"},
    {"label": "产物1: CAS号", "requirement": "required", "description": "文本。抽取第一种主要产物 CAS 号。"},
    {"label": "产物1: 数值", "requirement": "required", "description": "数字 (%)。抽取第一种产物的组成、选择性、收率或占比百分数。"},
    {"label": "产物2: 名称", "requirement": "required", "description": "文本。抽取第二种主要产物名称。"},
    {"label": "产物2: CAS号", "requirement": "required", "description": "文本。抽取第二种主要产物 CAS 号。"},
    {"label": "产物2: 数值", "requirement": "required", "description": "数字 (%)。抽取第二种产物的组成、选择性、收率或占比百分数。"},
    {"label": "产物3: 名称", "requirement": "recommended", "description": "文本。抽取第三种产物名称；没有第三种产物则留空。"},
    {"label": "产物3: 数值", "requirement": "recommended", "description": "数字 (%)。抽取第三种产物对应百分数；没有则留空。"},
    {"label": "产物4: 名称", "requirement": "optional", "description": "文本。抽取第四种产物名称；没有则留空。"},
    {"label": "产物4: 数值", "requirement": "optional", "description": "文本/数字。抽取第四种产物对应数值或原文描述；没有则留空。"},
    {"label": "数据来源", "requirement": "optional", "description": "文本。记录数据来自正文、表格、图、补充材料或具体表/图编号。"},
    {"label": "产品分离", "requirement": "recommended", "description": "文本描述。抽取分离方法、纯化步骤、收集方式或后处理条件。"},
    {"label": "反应热", "requirement": "recommended", "description": "放热/吸热/无反应热。根据原文热效应、焓变或工艺描述判断。"},
    {"label": "反应机理", "requirement": "optional", "description": "文本描述，第一句话是主要反应式；随后简述关键中间体、活性位点或机理结论。"},
    {"label": "文献出处-链接", "requirement": "required", "description": "以 http 或 https 开始的 url。优先 DOI 链接、出版社链接或论文网页。"},
    {"label": "文献题目", "requirement": "required", "description": "文本描述。抽取论文正式题目。"},
    {"label": "流程图", "requirement": "recommended", "description": "图片。若当前文本无法直接提取图片，记录流程图编号、图题、页码或简要流程描述。"},
]

CHINESE_TRANSLATION_FIELDS = {
    "工艺名称", "原料", "CAS号", "催化剂通用名", "具体型号/牌号",
    "催化剂制备方法", "催化剂类型", "物理形状", "催化剂寿命",
    "反应温度（℃）", "温度误差", "反应压力（MPa）", "压力误差",
    "反应规模/空速", "数据类型/实验室/工业化", "反应器形式", "物性方法",
    "转化率（%）", "选择性（%）", "产物组成",
    "产物1: 名称", "产物1: CAS号", "产物1: 数值",
    "产物2: 名称", "产物2: CAS号", "产物2: 数值",
    "产物3: 名称", "产物3: 数值", "产物4: 名称", "产物4: 数值",
    "数据来源", "产品分离", "反应热", "反应机理",
}

EXPORT_EXCLUDED_COLUMNS = [
    "source_path", "source_file", "record_index", "record_count",
    "llm_provider", "llm_service", "llm_model", "ollama_model",
    "pdf_to_md_mode", "markdown_chars_total", "markdown_chars_used",
    "was_truncated", "quality_retry_used",
]

REVIEW_AID_FIELD_LABELS = [
    "source_evidence",
    "source_hint",
    "verification_status",
    "review_note",
    "page_hint",
    "section_hint",
    "table_hint",
]

REVIEW_AID_FIELDS = [
    {
        "label": "source_evidence",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Extract a short source excerpt from the converted PDF text that supports the row. "
            "Prefer the sentence, table row, caption fragment, or nearby phrase that directly "
            "supports the extracted values. Keep it short. Do not invent evidence. If no clear "
            "source evidence is found, leave empty."
        ),
    },
    {
        "label": "source_hint",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Indicate where the evidence appears to come from. Use one of: body_text, table, "
            "figure_caption, supplementary, ocr_text, not_clear. Do not invent source hints. "
            "If uncertain, use not_clear."
        ),
    },
    {
        "label": "verification_status",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Provide a review-oriented status, not a statistical confidence score. Use one of: "
            "direct_text_match, inferred, needs_review, low_confidence. Use direct_text_match "
            "only when the value is directly supported by nearby text or a table. Use inferred "
            "when interpretation or unit conversion was needed. Use needs_review when the source "
            "is unclear or multiple interpretations are possible. Use low_confidence when evidence "
            "is weak. Do not invent verification support."
        ),
    },
    {
        "label": "review_note",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Briefly explain why the row should or should not be reviewed. Mention uncertainty, "
            "unit conversion, missing context, OCR ambiguity, table complexity, or unclear source "
            "when applicable. Keep it short. Do not include long paper text. Do not invent "
            "provenance details."
        ),
    },
    {
        "label": "page_hint",
        "type": "str",
        "requirement": "optional",
        "description": (
            'Optional review aid. Use visible page markers such as "Page 3" only if '
            "available in the converted text. Do not invent page numbers. Leave empty "
            "when unclear."
        ),
    },
    {
        "label": "section_hint",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Optional review aid. Prefer abstract, experimental, results, table caption, "
            "figure caption, or nearby heading when clear. Do not invent sections. Leave "
            "empty when unclear."
        ),
    },
    {
        "label": "table_hint",
        "type": "str",
        "requirement": "optional",
        "description": (
            "Optional review aid. Prefer table number, table caption, or nearby row/caption "
            "when clear. Do not invent table identifiers. Leave empty when unclear."
        ),
    },
]


@dataclass
class RuntimeDeps:
    pd: Any
    PdfReader: Any
    ChatPromptTemplate: Any
    ChatOllama: Any
    Field: Any
    create_model: Any
    pymupdf4llm: Any | None = None
    pymupdf: Any | None = None


def script_dir() -> Path:
    return PROJECT_ROOT


def default_input_dir() -> Path:
    path = script_dir() / "input_pdfs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_path() -> Path:
    return script_dir() / OUTPUT_EXCEL_NAME


def local_config_path() -> Path:
    return script_dir() / LOCAL_CONFIG_NAME


def mask_api_key(key: str) -> str:
    key = (key or "").strip()
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "..."
    return key[:4] + "..." + key[-2:]


def _bool_config_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def normalize_local_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw or {}
    return {
        "cloud_service_name": str(
            raw.get("cloud_service_name")
            or raw.get("llm_service_name")
            or raw.get("service_name")
            or DEFAULT_CLOUD_SERVICE_NAME
        ).strip(),
        "cloud_api_key": str(raw.get("cloud_api_key") or raw.get("api_key") or "").strip(),
        "cloud_base_url": str(raw.get("cloud_base_url") or raw.get("base_url") or DEFAULT_CLOUD_BASE_URL).strip(),
        "cloud_model": str(raw.get("cloud_model") or raw.get("model") or DEFAULT_CLOUD_MODEL).strip(),
        "cloud_active": _bool_config_value(raw.get("cloud_active"), False),
        "copy_failed_sources": _bool_config_value(raw.get("copy_failed_sources"), False),
    }


def load_local_config() -> dict[str, Any]:
    path = local_config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return normalize_local_config(data)
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def save_local_config(config: dict[str, Any]) -> Path:
    normalized = normalize_local_config(config)
    payload = {
        "llm_service_name": normalized["cloud_service_name"],
        "api_key": normalized["cloud_api_key"],
        "base_url": normalized["cloud_base_url"],
        "model": normalized["cloud_model"],
        "cloud_active": normalized["cloud_active"],
        "copy_failed_sources": normalized["copy_failed_sources"],
    }
    path = local_config_path()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def public_local_config() -> dict[str, Any]:
    config = load_local_config()
    api_key = str(config.get("cloud_api_key") or "").strip()
    return {
        "cloud_service_name": config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
        "cloud_base_url": config.get("cloud_base_url") or DEFAULT_CLOUD_BASE_URL,
        "cloud_model": config.get("cloud_model") or DEFAULT_CLOUD_MODEL,
        "cloud_active": bool(config.get("cloud_active", False)),
        "has_cloud_api_key": bool(api_key),
        "cloud_api_key_prefix": mask_api_key(api_key),
        "copy_failed_sources": bool(config.get("copy_failed_sources", False)),
    }


def apply_cloud_config_defaults(config: dict[str, Any]) -> dict[str, Any]:
    local_config = load_local_config()
    env_api_key = os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY") or os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY") or ""
    defaults = {
        "cloud_service_name": local_config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
        "cloud_model": local_config.get("cloud_model") or os.environ.get("CHEM_PDF_EXTRACTOR_MODEL") or DEFAULT_CLOUD_MODEL,
        "cloud_base_url": local_config.get("cloud_base_url") or os.environ.get("CHEM_PDF_EXTRACTOR_BASE_URL") or DEFAULT_CLOUD_BASE_URL,
        "cloud_api_key": local_config.get("cloud_api_key") or env_api_key or DEFAULT_CLOUD_API_KEY,
        "cloud_active": local_config.get("cloud_active", False),
        "copy_failed_sources": local_config.get("copy_failed_sources", False),
    }
    for key, value in defaults.items():
        if key == "cloud_active":
            config.setdefault(key, value)
        elif not str(config.get(key) or "").strip():
            config[key] = value
    return config


def validate_cloud_base_url_security(base_url: str) -> str | None:
    raw = str(base_url or "").strip()
    if not raw:
        return "Please enter an OpenAI-compatible Base URL."
    parsed = urllib.parse.urlsplit(raw)
    if not parsed.scheme or not parsed.netloc:
        return "Please enter a valid OpenAI-compatible Base URL."
    if parsed.username or parsed.password:
        return "Base URL must not include username/password credentials."
    if parsed.query or parsed.fragment:
        return "Base URL must not include query string or fragment."
    lowered = raw.rstrip("/").lower()
    if any(marker in lowered for marker in PLACEHOLDER_CLOUD_BASE_URL_MARKERS):
        return "Please enter a real OpenAI-compatible Base URL."
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if scheme == "https":
        return None
    if scheme == "http" and host in {"127.0.0.1", "localhost", "::1"}:
        return None
    if scheme == "http":
        return "For cloud providers, use HTTPS Base URL. Plain HTTP is allowed only for localhost."
    return "Unsupported Base URL scheme. Use HTTPS for cloud providers."


def validate_cloud_start_config(config: dict[str, Any]) -> str | None:
    if str(config.get("llm_provider") or "").strip().lower() != "cloud":
        return None

    api_key = str(config.get("cloud_api_key") or config.get("api_key") or "").strip()
    if not api_key:
        return (
            "Cloud API Key is required for --llm-provider cloud. "
            "Set CHEM_PDF_EXTRACTOR_API_KEY, pass --cloud-api-key, save config.local.json, "
            "or stay local with --llm-provider ollama."
        )
    if is_placeholder_cloud_api_key(api_key):
        return (
            "Cloud API Key looks like a placeholder. Set CHEM_PDF_EXTRACTOR_API_KEY "
            "or pass a real --cloud-api-key. To avoid cloud processing, use --llm-provider ollama."
        )

    base_url = str(config.get("cloud_base_url") or config.get("base_url") or "").strip()
    if not base_url:
        return (
            "Cloud Base URL is required for --llm-provider cloud. "
            "Set CHEM_PDF_EXTRACTOR_BASE_URL or pass --cloud-base-url."
        )
    base_url_error = validate_cloud_base_url_security(base_url)
    if base_url_error:
        return base_url_error

    model = str(config.get("cloud_model") or config.get("model") or "").strip()
    if not model:
        return (
            "Cloud model name is required. Set CHEM_PDF_EXTRACTOR_MODEL, pass --cloud-model, "
            "or pass --model as a legacy cloud model alias. 云端模型名称不能为空。"
        )
    if model.lower() in PLACEHOLDER_CLOUD_MODELS:
        return (
            "Cloud model name looks like a placeholder. Set CHEM_PDF_EXTRACTOR_MODEL, "
            "pass --cloud-model, or pass --model as a legacy cloud model alias. "
            "请填写真实的云端模型名称。"
        )

    return None


def is_placeholder_cloud_api_key(api_key: str) -> bool:
    lowered = str(api_key or "").strip().lower()
    compact = re.sub(r"[\s_]+", "_", lowered)
    if compact in PLACEHOLDER_CLOUD_API_KEYS:
        return True
    dashed = re.sub(r"[\s_]+", "-", lowered)
    if dashed in PLACEHOLDER_CLOUD_API_KEYS:
        return True
    return "your" in lowered and "key" in lowered


def validate_cloud_test_config(config: dict[str, Any]) -> str | None:
    api_key = str(config.get("cloud_api_key") or config.get("api_key") or "").strip()
    if not api_key:
        return "Please enter an LLM API key."
    if is_placeholder_cloud_api_key(api_key):
        return "Please enter a real LLM API key."

    base_url = str(config.get("cloud_base_url") or config.get("base_url") or "").strip()
    base_url_error = validate_cloud_base_url_security(base_url)
    if base_url_error:
        return base_url_error

    model = str(config.get("cloud_model") or config.get("model") or "").strip()
    if not model:
        return "Please enter a model name."
    if model.lower() in PLACEHOLDER_CLOUD_MODELS:
        return "Please enter a real model name."
    return None


def short_error(exc: BaseException, limit: int = 500) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}小时{minutes}分{secs}秒"
    if minutes:
        return f"{minutes}分{secs}秒"
    if seconds < 10:
        return f"{seconds:.1f}秒"
    return f"{secs}秒"


def add_stat(stats: dict[str, float] | None, key: str, value: float = 1.0) -> None:
    if stats is not None:
        stats[key] = stats.get(key, 0.0) + value


def eta_text(started_at: float, done: int, total: int) -> str:
    import time as _time
    if done <= 0 or total <= 0 or done >= total:
        return "预计剩余 0秒"
    elapsed = _time.perf_counter() - started_at
    remaining = max(0, total - done)
    eta = elapsed / done * remaining
    return f"预计剩余 {format_duration(eta)}"


def stage_summary(stats: dict[str, float]) -> str:
    if not stats:
        return ""
    parts = []
    mapping = [
        ("pdf_to_md", "PDF转MD"),
        ("llm_extraction", "LLM抽取"),
        ("quality_retry", "二次抽取"),
        ("translation", "翻译"),
    ]
    for key, label in mapping:
        value = stats.get(key, 0.0)
        if value:
            parts.append(f"{label}{format_duration(value)}")
    cache_hits = int(stats.get("extract_cache_hit", 0))
    if cache_hits:
        parts.append(f"抽取缓存命中{cache_hits}次")
    return "；".join(parts)


def infer_field_type(label: str, description: str) -> str:
    text = f"{label} {description}".lower()
    desc = description.strip().lower()
    if desc.startswith("数字") or "只填" in text:
        return "float"
    return "str"


def normalize_requirement(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "必填": "required", "required": "required",
        "建议": "recommended", "推荐": "recommended", "recommended": "recommended",
        "选填": "optional", "可选": "optional", "optional": "optional",
    }
    return mapping.get(text, "optional")


def requirement_label(value: str) -> str:
    return {"required": "必填", "recommended": "建议", "optional": "选填"}.get(value, "选填")


def requirement_rule(value: str) -> str:
    if value == "required":
        return "【必填】必须优先检索全文、表格、图注和补充材料中的相关信息，尽最大努力抽取；只有原文确实不存在或无法判断时才留空，严禁编造"
    if value == "recommended":
        return "【建议】尽量抽取；若原文没有明确给出或无法可靠判断，可以留空"
    return "【选填】有明确证据时抽取；没有就留空"


def normalize_fields(fields: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    source = fields or DEFAULT_FIELDS
    normalized: list[dict[str, str]] = []
    for item in source:
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        description = str(item.get("description", "")).strip() or label
        field_type = str(item.get("type") or infer_field_type(label, description)).strip().lower()
        if field_type not in {"str", "float", "int"}:
            field_type = infer_field_type(label, description)
        requirement = normalize_requirement(item.get("requirement"))
        normalized.append({
            "label": label, "type": field_type,
            "requirement": requirement, "description": description,
        })
    if not normalized:
        first = DEFAULT_FIELDS[0]
        description = str(first.get("description", "")).strip() or str(first.get("label", "字段")).strip()
        normalized = [{
            "label": str(first.get("label", "字段")).strip() or "字段",
            "type": str(first.get("type") or infer_field_type(str(first.get("label", "")), description)),
            "requirement": normalize_requirement(first.get("requirement")),
            "description": description,
        }]
    used: dict[str, int] = {}
    for item in normalized:
        label = item["label"]
        used[label] = used.get(label, 0) + 1
        if used[label] > 1:
            item["label"] = f"{label} ({used[label]})"
    return normalized


def append_review_aid_fields(fields: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Append manual-review aid fields without mutating user field definitions."""
    normalized = normalize_fields(fields)
    review_labels = set(REVIEW_AID_FIELD_LABELS)
    by_label = {item["label"]: dict(item) for item in normalized}
    result = [dict(item) for item in normalized if item["label"] not in review_labels]

    for template in REVIEW_AID_FIELDS:
        label = template["label"]
        item = dict(by_label.get(label, template))
        item["label"] = label
        item["type"] = "str"
        item["requirement"] = "optional"
        if not str(item.get("description", "")).strip():
            item["description"] = str(template["description"])
        result.append({
            "label": str(item["label"]),
            "type": str(item["type"]),
            "requirement": str(item["requirement"]),
            "description": str(item["description"]),
        })
    return result


def python_type(type_name: str) -> type:
    return str


def missing_rule(type_name: str) -> str:
    if type_name in {"float", "int"}:
        return "缺失时留空；若有数据，只输出纯数字"
    return "缺失时留空，不要输出 N/A、null、-999 或自行编造内容"


def field_instructions(fields: list[dict[str, str]]) -> str:
    lines = []
    for index, item in enumerate(fields, start=1):
        requirement = item.get("requirement", "optional")
        lines.append(
            f"{index}. {item['label']} [{requirement_label(requirement)}]: "
            f"{item['description']}；{requirement_rule(requirement)}；{missing_rule(item['type'])}"
        )
    return "\n".join(lines)


def build_dynamic_model(fields: list[dict[str, str]], runtime: RuntimeDeps):
    from pydantic import Field as _Field, create_model as _create_model
    record_fields: dict[str, Any] = {}
    key_to_label: dict[str, str] = {}
    for index, item in enumerate(fields, start=1):
        key = f"field_{index:02d}"
        key_to_label[key] = item["label"]
        desc = (
            f"字段名：{item['label']}。"
            f"字段要求：{requirement_rule(item.get('requirement', 'optional'))}。"
            f"字段说明：{item['description']}。"
            f"{missing_rule(item['type'])}。"
            "中英文文献均可抽取，保留原文中最清楚的表达。"
        )
        record_fields[key] = (python_type(item["type"]), _Field(default="", description=desc))
    record_model = _create_model("ExtractionRecord", **record_fields)
    model = _create_model(
        "ExtractionResult",
        records=(
            list[record_model],
            _Field(
                default_factory=list,
                description=(
                    "抽取到的数据记录列表。同一篇文献中如果有多个工艺、催化剂、实验条件、"
                    "数据表行或可独立成行的结果，就拆成多条 records；只有一条时也放在列表中。"
                ),
            ),
        ),
    )
    return model, key_to_label


def bad_row_min_fill_rate_from_config(config: dict[str, Any]) -> float:
    raw = config.get("bad_row_min_fill_percent", config.get("bad_row_min_fill_rate", BAD_ROW_MIN_FILL_RATE))
    if raw is None or raw == "":
        return BAD_ROW_MIN_FILL_RATE
    try:
        numeric = float(raw)
    except (TypeError, ValueError):
        return BAD_ROW_MIN_FILL_RATE
    if numeric > 1:
        numeric = numeric / 100.0
    return max(0.0, min(1.0, numeric))


def candidate_pythons() -> list[Path]:
    candidates: list[Path] = []
    bundled_python = PROJECT_ROOT / BUNDLED_RUNTIME_DIR_NAME / "python" / "python.exe"
    candidates.append(bundled_python)
    candidates.append(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
    for runtime_dir_name in LEGACY_BUNDLED_RUNTIME_DIR_NAMES:
        candidates.append(PROJECT_ROOT / runtime_dir_name / "python" / "python.exe")
    env_python = os.environ.get("CHEM_PDF_EXTRACTOR_PYTHON") or os.environ.get("CHEM_EXTRACTOR_PYTHON")
    if env_python:
        candidates.append(Path(env_python))
    current = Path(sys.executable).resolve()
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        key = str(resolved).casefold()
        if key == str(current).casefold() or key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def python_has_required_packages(python_exe: Path) -> bool:
    if not python_exe.exists():
        return False
    code = "import " + ", ".join(CORE_REQUIRED_PACKAGES.keys())
    result = subprocess.run(
        [str(python_exe), "-c", code],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    return result.returncode == 0


def try_reexec_with_ready_python() -> None:
    if os.environ.get("CHEM_EXTRACTOR_REEXECED") == "1":
        return
    for python_exe in candidate_pythons():
        if python_has_required_packages(python_exe):
            print(f"当前 Python 缺依赖：{sys.executable}")
            print(f"找到已安装依赖的 Python：{python_exe}")
            print("正在自动切换并重启脚本...")
            sys.stdout.flush()
            sys.stderr.flush()
            os.environ["CHEM_EXTRACTOR_REEXECED"] = "1"
            wrapper = PROJECT_ROOT / "run_chem_pdf_extractor.py"
            os.execv(str(python_exe), [str(python_exe), str(wrapper), *sys.argv[1:]])


def clean_pip_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in [
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
        "PIP_PROXY", "pip_proxy",
    ]:
        env.pop(key, None)
    return env


def find_missing_imports() -> list[str]:
    missing: list[str] = []
    for import_name, package_name in CORE_REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ModuleNotFoundError:
            missing.append(package_name)
    return sorted(set(missing))


def run_pip_install(packages: list[str]) -> bool:
    commands = [
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *packages],
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
         "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
         "--trusted-host", "pypi.tuna.tsinghua.edu.cn", *packages],
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
         "-i", "https://mirrors.aliyun.com/pypi/simple/",
         "--trusted-host", "mirrors.aliyun.com", *packages],
    ]
    for command in commands:
        print("\n正在尝试安装依赖：")
        print(" ".join(command))
        result = subprocess.run(command, check=False, env=clean_pip_env())
        if result.returncode == 0:
            return True
    return False


def ensure_dependencies(auto_install: bool = True) -> None:
    missing = find_missing_imports()
    if not missing:
        return
    print("当前 Python 缺少依赖：", ", ".join(missing))
    try_reexec_with_ready_python()
    if auto_install:
        installed = run_pip_install(missing)
        if installed and not find_missing_imports():
            print("依赖安装完成，继续执行。")
            return
    mirror_command = (
        f'"{sys.executable}" -m pip install '
        "-i https://pypi.tuna.tsinghua.edu.cn/simple "
        "--trusted-host pypi.tuna.tsinghua.edu.cn "
        + " ".join(missing)
    )
    raise SystemExit(
        "\n依赖没有安装成功，脚本无法继续。\n"
        "你可以手动复制下面这条命令到 PowerShell 执行：\n"
        f"{mirror_command}\n"
    )


def import_runtime_dependencies() -> RuntimeDeps:
    import pandas as pd
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import ChatOllama
    from pydantic import Field, create_model
    from pypdf import PdfReader
    return RuntimeDeps(
        pd=pd, PdfReader=PdfReader,
        ChatPromptTemplate=ChatPromptTemplate, ChatOllama=ChatOllama,
        Field=Field, create_model=create_model,
    )


def _optional_backend_error(name: str, exc: BaseException) -> RuntimeError:
    reason = short_error(exc, limit=300)
    package = OPTIONAL_PDF_BACKEND_PACKAGES.get(name, name)
    return RuntimeError(
        f"{name} PDF 后端当前不可用。该依赖已改为可选懒加载，"
        f"请切换到 pypdf_text，或安装/修复 {package} 后重试。原因：{reason}"
    )


def load_pymupdf4llm(runtime: RuntimeDeps) -> Any:
    if runtime.pymupdf4llm is not None:
        return runtime.pymupdf4llm
    try:
        runtime.pymupdf4llm = importlib.import_module("pymupdf4llm")
        return runtime.pymupdf4llm
    except Exception as exc:
        raise _optional_backend_error("pymupdf4llm", exc) from exc


def load_pymupdf(runtime: RuntimeDeps) -> Any:
    if runtime.pymupdf is not None:
        return runtime.pymupdf
    try:
        runtime.pymupdf = importlib.import_module("pymupdf")
        return runtime.pymupdf
    except Exception as exc:
        raise _optional_backend_error("pymupdf", exc) from exc
