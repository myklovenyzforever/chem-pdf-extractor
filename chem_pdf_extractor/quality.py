from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import (
    BAD_ROW_EMPTY_MARKERS,
    BAD_ROW_FIELD_WEIGHTS,
    BAD_ROW_MIN_FILL_RATE,
    CHINESE_TRANSLATION_FIELDS,
    ERROR_STATS_JSONL_NAME,
    EXPORT_EXCLUDED_COLUMNS,
    short_error,
)
from .export import append_jsonl


def clean_extracted_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and float(value) == -999:
        return ""
    if isinstance(value, (list, tuple, set)):
        parts = [clean_extracted_value(item) for item in value]
        return "；".join(part for part in parts if part)
    if isinstance(value, dict):
        compact = {str(k): clean_extracted_value(v) for k, v in value.items()}
        compact = {k: v for k, v in compact.items() if v}
        if not compact:
            return ""
        return json.dumps(compact, ensure_ascii=False)
    text = str(value).strip()
    MISSING_TEXT_MARKERS = {
        "", "n/a", "na", "none", "null", "nil", "nan",
        "not mentioned", "not reported", "not available", "unknown",
        "未提及", "未报道", "无", "空", "-999",
    }
    return "" if text.casefold() in MISSING_TEXT_MARKERS else text


def normalize_cloud_value(value: Any, field_type: str) -> Any:
    text = clean_extracted_value(value)
    if not text:
        return ""
    if field_type == "str":
        return text
    number_match = re.search(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    try:
        if field_type == "int":
            return int(float(number_match.group(0) if number_match else text))
        return float(number_match.group(0) if number_match else text)
    except (TypeError, ValueError):
        return ""


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[一-鿿]", text))


def should_translate_to_chinese(field_name: str, value: Any) -> bool:
    text = clean_extracted_value(value)
    if not text:
        return False
    if field_name not in CHINESE_TRANSLATION_FIELDS:
        return False
    if "CAS号" in field_name or field_name == "CAS号":
        return False
    if text.startswith(("http://", "https://", "doi.org/")):
        return False
    if has_chinese(text):
        return False
    compact = text.replace(",", "").strip()
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?\s*(?:%|°c|℃|k|mpa|bar|atm|pa|h\^-?1|h-1)?", compact, flags=re.IGNORECASE):
        return False
    if re.fullmatch(r"\d{2,7}-\d{2}-\d", compact):
        return False
    return True


def is_filled_cell(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return text.casefold() not in BAD_ROW_EMPTY_MARKERS
    return True


def field_weight(field: dict[str, str]) -> float:
    return BAD_ROW_FIELD_WEIGHTS.get(field.get("requirement", "optional"), 0.0)


def row_quality_stats(row: dict[str, Any], fields: list[dict[str, str]]) -> dict[str, Any]:
    filled_count = 0
    filled_weight = 0.0
    total_weight = 0.0
    missing_required: list[str] = []
    missing_recommended: list[str] = []
    for item in fields:
        label = item["label"]
        requirement = item.get("requirement", "optional")
        filled = is_filled_cell(row.get(label))
        if filled:
            filled_count += 1
        weight = field_weight(item)
        total_weight += weight
        if filled:
            filled_weight += weight
        elif requirement == "required":
            missing_required.append(label)
        elif requirement == "recommended":
            missing_recommended.append(label)
    weighted_rate = filled_weight / total_weight if total_weight else 1.0
    simple_rate = filled_count / len(fields) if fields else 1.0
    return {
        "filled_count": filled_count, "field_count": len(fields),
        "filled_weight": filled_weight, "total_weight": total_weight,
        "weighted_rate": weighted_rate, "simple_rate": simple_rate,
        "missing_required": missing_required, "missing_recommended": missing_recommended,
    }


def calculate_fill_rate(row: dict[str, Any], fields: list[dict[str, str]]) -> float:
    return float(row_quality_stats(row, fields)["weighted_rate"])


def row_is_bad_data(row: dict[str, Any], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> bool:
    stats = row_quality_stats(row, fields)
    return bool(stats["total_weight"]) and float(stats["weighted_rate"]) < min_fill_rate


def is_bad_data(row: dict[str, Any], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> bool:
    return row_is_bad_data(row, fields, min_fill_rate)


def rows_quality_score(rows: list[dict[str, Any]], fields: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    return sum(float(row_quality_stats(row, fields)["weighted_rate"]) for row in rows) / len(rows)


def quality_retry_hint(rows: list[dict[str, Any]], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> str:
    if not rows:
        return (
            "上一次没有抽取到有效 records。请重点核查标题、摘要、实验方法、表格、图注和结果部分，"
            "尽量补齐必填字段；原文确实没有的信息仍然留空，禁止编造。"
        )
    problem_lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        stats = row_quality_stats(row, fields)
        missing_required = stats["missing_required"]
        if missing_required or float(stats["weighted_rate"]) < min_fill_rate:
            problem_lines.append(
                f"第 {index} 条记录加权填写率 {float(stats['weighted_rate']):.1%}；"
                f"缺失必填字段：{', '.join(missing_required) if missing_required else '无'}；"
                f"缺失建议字段：{', '.join(stats['missing_recommended'][:10]) if stats['missing_recommended'] else '无'}。"
            )
    if not problem_lines:
        return ""
    return (
        "上一次抽取结果质量偏低，请重新阅读全文中的实验方法、表格、表注、图注和结果讨论，"
        "优先补齐必填字段。不要编造；原文确实没有的信息仍然留空。\n"
        + "\n".join(problem_lines[:8])
    )


def log_bad_data_row(
    error_log_path: Path, pdf_path: Path, *,
    row_number: int, stats: dict[str, Any], row: dict[str, Any],
    min_fill_rate: float = BAD_ROW_MIN_FILL_RATE,
) -> None:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    preview = {
        key: value for key, value in row.items()
        if key not in EXPORT_EXCLUDED_COLUMNS and is_filled_cell(value)
    }
    preview_text = json.dumps(preview, ensure_ascii=False)
    if len(preview_text) > 3000:
        preview_text = preview_text[:2997] + "..."
    bad_rows_path = error_log_path.with_name("坏数据.jsonl")
    review_row = {
        "源文件名": pdf_path.name, "源文件路径": str(pdf_path),
        "记录序号": row_number,
        "加权填写率": round(float(stats["weighted_rate"]), 4),
        "普通填写率": round(float(stats["simple_rate"]), 4),
        "已填字段数": int(stats["filled_count"]),
        "总字段数": int(stats["field_count"]),
        "已填权重": round(float(stats["filled_weight"]), 3),
        "总权重": round(float(stats["total_weight"]), 3),
        "缺失必填字段": "；".join(stats["missing_required"]),
        "缺失建议字段": "；".join(stats["missing_recommended"]),
    }
    for key, value in row.items():
        if key not in EXPORT_EXCLUDED_COLUMNS:
            review_row[key] = value
    append_jsonl(bad_rows_path, review_row)
    append_jsonl(
        error_log_path.with_name(ERROR_STATS_JSONL_NAME),
        {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "源文件名": pdf_path.name, "源文件路径": str(pdf_path),
            "失败环节": "bad_data_low_fill_rate",
            "错误类型": "BadDataLowFillRate",
            "错误原因": (
                f"加权填写率 {float(stats['weighted_rate']):.1%} 低于 {min_fill_rate:.0%}，"
                f"缺失必填字段：{'；'.join(stats['missing_required']) or '无'}"
            ),
        },
    )
    with error_log_path.open("a", encoding="utf-8") as handle:
        handle.write("=" * 80 + "\n")
        handle.write(f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        handle.write(f"file: {pdf_path}\n")
        handle.write("stage: bad_data_low_fill_rate\n")
        handle.write(
            "error: "
            f"坏数据行已删除；第 {row_number} 条记录填写率 "
            f"{float(stats['weighted_rate']):.1%}，低于 {min_fill_rate:.0%} "
            f"阈值；已填写 {int(stats['filled_count'])}/{int(stats['field_count'])} 个抽取字段，"
            f"缺失必填字段：{'；'.join(stats['missing_required']) or '无'}。\n"
        )
        handle.write(f"bad_rows_file: {bad_rows_path}\n")
        handle.write(f"row_preview: {preview_text}\n")
        handle.write("\n")


def filter_bad_data_rows(
    rows: list[dict[str, Any]], fields: list[dict[str, str]], error_log_path: Path, *,
    default_pdf_path: Path, state: Any = None, log_prefix: str = "",
    min_fill_rate: float = BAD_ROW_MIN_FILL_RATE,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    removed = 0
    for row_number, row in enumerate(rows, start=1):
        stats = row_quality_stats(row, fields)
        if row_is_bad_data(row, fields, min_fill_rate):
            source_path = str(row.get("source_path") or "").strip()
            pdf_path = Path(source_path) if source_path else default_pdf_path
            log_bad_data_row(error_log_path, pdf_path, row_number=row_number, stats=stats, row=row, min_fill_rate=min_fill_rate)
            removed += 1
            continue
        kept.append(row)
    if removed and state is not None:
        prefix = f"{log_prefix} " if log_prefix else ""
        state.add_log(f"{prefix}坏数据过滤：删除 {removed} 行（填写率低于 {min_fill_rate:.0%}），详见 错误日志.txt")
    return kept


def split_multi_values(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;；,，、\s]+", text) if item.strip()]


def parse_numbers(value: Any) -> list[float]:
    text = clean_extracted_value(value)
    if not text:
        return []
    numbers: list[float] = []
    for match in re.findall(r"[-+]?\d+(?:\.\d+)?", text):
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    return numbers


def is_valid_cas(cas: str) -> bool:
    if not re.fullmatch(r"\d{2,7}-\d{2}-\d", cas):
        return False
    digits = cas.replace("-", "")
    check_digit = int(digits[-1])
    body = digits[:-1][::-1]
    checksum = sum((index + 1) * int(digit) for index, digit in enumerate(body)) % 10
    return checksum == check_digit


def validate_row_values(row: dict[str, Any], fields: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    for item in fields:
        label = item["label"]
        value = row.get(label)
        text = clean_extracted_value(value)
        if not text:
            continue
        compact_label = label.replace(" ", "")
        if "CAS" in compact_label:
            candidates = [part for part in split_multi_values(text) if "-" in part or part.lower() != "cas"]
            if candidates and not any(is_valid_cas(part) for part in candidates):
                issues.append(f"{label}: CAS号格式或校验位可疑（{text}）")
        if "文献出处" in compact_label or "链接" in compact_label:
            if not text.startswith(("http://", "https://")):
                issues.append(f"{label}: 链接不是 http/https 开头（{text}）")
        if "温度" in compact_label:
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到温度数字（{text}）")
            elif any(number < -273.15 or number > 2000 for number in numbers):
                issues.append(f"{label}: 温度数值超出常规范围（{text}）")
        if "压力" in compact_label:
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到压力数字（{text}）")
            elif any(number < 0 or number > 1000 for number in numbers):
                issues.append(f"{label}: 压力数值超出常规范围（{text}）")
        if any(keyword in compact_label for keyword in ["转化率", "选择性", "产率"]):
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到百分比数字（{text}）")
            elif any(number < 0 or number > 100 for number in numbers):
                issues.append(f"{label}: 百分比数值不在 0-100 范围内（{text}）")
    return issues


def log_suspicious_rows(
    rows: list[dict[str, Any]], fields: list[dict[str, str]],
    suspicious_jsonl_path: Path, *, default_pdf_path: Path,
    issue_type: str = "value_validation",
) -> int:
    count = 0
    for row_number, row in enumerate(rows, start=1):
        issues = validate_row_values(row, fields)
        if not issues:
            continue
        source_path = str(row.get("source_path") or "").strip()
        pdf_path = Path(source_path) if source_path else default_pdf_path
        review_row = {
            "问题类型": issue_type, "源文件名": pdf_path.name,
            "源文件路径": str(pdf_path), "记录序号": row_number,
            "问题说明": "；".join(issues),
        }
        for key, value in row.items():
            if key not in EXPORT_EXCLUDED_COLUMNS:
                review_row[key] = value
        append_jsonl(suspicious_jsonl_path, review_row)
        count += 1
    return count


def clean_duplicate_value(value: Any) -> str:
    text = clean_extracted_value(value).lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，,;；。:.：%（）()]+", "", text)
    return text


def find_label_by_keywords(row: dict[str, Any], keywords: list[str]) -> str:
    for label in row:
        if any(keyword in label for keyword in keywords):
            value = clean_duplicate_value(row.get(label))
            if value:
                return value
    return ""


def duplicate_signature(row: dict[str, Any]) -> tuple[str, ...] | None:
    values = [
        find_label_by_keywords(row, ["工艺名称"]),
        find_label_by_keywords(row, ["催化剂通用名", "催化剂"]),
        find_label_by_keywords(row, ["反应温度", "温度"]),
        find_label_by_keywords(row, ["反应压力", "压力"]),
        find_label_by_keywords(row, ["转化率"]),
        find_label_by_keywords(row, ["选择性"]),
    ]
    nonempty = [value for value in values if value]
    if len(nonempty) < 4:
        return None
    return tuple(values)


def log_near_duplicates(rows: list[dict[str, Any]], suspicious_jsonl_path: Path) -> int:
    seen: dict[tuple[str, ...], dict[str, Any]] = {}
    duplicate_count = 0
    for row_number, row in enumerate(rows, start=1):
        signature = duplicate_signature(row)
        if signature is None:
            continue
        first = seen.get(signature)
        if first is None:
            seen[signature] = row
            continue
        review_row = {
            "问题类型": "near_duplicate",
            "源文件名": row.get("源文件名") or Path(str(row.get("source_path") or "")).name,
            "源文件路径": str(row.get("source_path") or ""),
            "记录序号": row_number,
            "问题说明": f"疑似与较早记录重复；签名={signature}",
            "首条源文件名": first.get("源文件名") or Path(str(first.get("source_path") or "")).name,
            "首条源文件路径": str(first.get("source_path") or ""),
        }
        for key, value in row.items():
            if key not in EXPORT_EXCLUDED_COLUMNS:
                review_row[key] = value
        append_jsonl(suspicious_jsonl_path, review_row)
        duplicate_count += 1
    return duplicate_count


def parse_translation_payload(raw: dict[str, Any]) -> dict[str, str]:
    translated: dict[str, str] = {}
    for item in raw.get("items", []):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "").strip()
        value = clean_extracted_value(item.get("translation"))
        if item_id and value:
            translated[item_id] = value
    return translated


def translate_rows_to_chinese(
    rows: list[dict[str, Any]], fields: list[dict[str, str]],
    batch_translator: Any, batch_size: int = 24,
) -> int:
    target_labels = [item["label"] for item in fields if item["label"] in CHINESE_TRANSLATION_FIELDS]
    pending: list[dict[str, str]] = []
    refs: list[tuple[str, dict[str, Any], str]] = []
    counter = 1
    for row in rows:
        for label in target_labels:
            value = row.get(label, "")
            if not should_translate_to_chinese(label, value):
                continue
            item_id = f"t{counter}"
            counter += 1
            pending.append({"id": item_id, "field": label, "text": str(value).strip()})
            refs.append((item_id, row, label))
    changed = 0
    translations: dict[str, str] = {}
    for start in range(0, len(pending), batch_size):
        translations.update(batch_translator(pending[start : start + batch_size]))
    for item_id, row, label in refs:
        translated = translations.get(item_id, "")
        if translated:
            row[label] = translated
            changed += 1
    return changed
