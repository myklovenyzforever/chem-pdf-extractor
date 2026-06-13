from __future__ import annotations

import copy
import re
import unicodedata
from typing import Any


_API_KEY_RE = re.compile(r"\b(?:sk|tp)-[A-Za-z0-9_\-]{8,}\b")
_BEARER_RE = re.compile(r"(?i)\b(Authorization\s*:\s*Bearer|Bearer)\s+([^\s,;\"']+)")
_KEY_VALUE_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|token|password|secret|key)(\s*[:=]\s*)([^\s,;\"']+)"
)
_JSON_SECRET_RE = re.compile(
    r"(?i)([\"'](?:api[_-]?key|apikey|token|password|secret|key)[\"']\s*:\s*[\"'])([^\"']+)([\"'])"
)
_FLAG_EQ_RE = re.compile(r"(?i)(--(?:cloud-api-key|api-key|key)=)([^\s]+)")
_FLAG_VALUE_RE = re.compile(r"(?i)(--(?:cloud-api-key|api-key|key)\s+)([^\s]+)")
_SECRET_FLAGS = {"--cloud-api-key", "--api-key", "--key"}
_FULLWIDTH_FORMULA_PREFIXES = {"＝", "＋", "－", "＠"}
_MOJIBAKE_FULLWIDTH_PREFIXES = ("锛漙", "锛媊", "锛峘", "锛燻")
_FORMULA_PREFIXES = {"=", "+", "-", "@"} | _FULLWIDTH_FORMULA_PREFIXES


def redact_sensitive_text(text: str) -> str:
    """Redact common API keys, bearer tokens, and key-like values from text."""
    value = str(text)
    value = _API_KEY_RE.sub("<redacted>", value)
    value = _BEARER_RE.sub(r"\1 <redacted>", value)
    value = _JSON_SECRET_RE.sub(r"\1<redacted>\3", value)
    value = _FLAG_EQ_RE.sub(r"\1<redacted>", value)
    value = _FLAG_VALUE_RE.sub(r"\1<redacted>", value)
    return _KEY_VALUE_RE.sub(r"\1\2<redacted>", value)


def redact_sensitive_obj(obj: Any) -> Any:
    """Recursively redact secret-like values from JSON-compatible objects."""
    if isinstance(obj, str):
        return redact_sensitive_text(obj)
    if isinstance(obj, dict):
        output: dict[Any, Any] = {}
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("api_key", "apikey", "api-key", "token", "password", "secret", "key")):
                output[key] = "<redacted>" if value else value
            else:
                output[key] = redact_sensitive_obj(value)
        return output
    if isinstance(obj, list):
        return [redact_sensitive_obj(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(redact_sensitive_obj(item) for item in obj)
    try:
        return copy.deepcopy(obj)
    except Exception:
        return obj


def _trim_for_formula_check(value: str) -> str:
    text = value.lstrip("\ufeff")
    index = 0
    while index < len(text):
        char = text[index]
        category = unicodedata.category(char)
        if char.isspace() or category.startswith("C"):
            index += 1
            continue
        break
    return text[index:]


def is_spreadsheet_formula_risk(value: Any) -> bool:
    """Return True when a string could be interpreted as a spreadsheet formula."""
    if not isinstance(value, str) or value == "":
        return False
    if value[0] in {"\t", "\r", "\n"}:
        return True
    if value.startswith("'"):
        return False
    checked = _trim_for_formula_check(value)
    if checked.startswith(_MOJIBAKE_FULLWIDTH_PREFIXES):
        return True
    return bool(checked) and checked[0] in _FORMULA_PREFIXES


def sanitize_spreadsheet_cell(value: Any) -> Any:
    """Prefix risky formula-like strings with a single quote for Excel/CSV viewing."""
    if not isinstance(value, str):
        return value
    if not is_spreadsheet_formula_risk(value):
        return value
    return "'" + value


def sanitize_spreadsheet_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return spreadsheet-safe copies of rows without mutating internal cache data."""
    return [
        {key: sanitize_spreadsheet_cell(value) for key, value in row.items()}
        for row in rows
    ]
