from __future__ import annotations

import json
import re
from typing import Any

_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def utf8_safe_text(text: str) -> str:
    """Replace lone surrogate code points so text can be UTF-8 encoded."""
    return _SURROGATE_RE.sub("\uFFFD", text)


def utf8_safe_obj(obj: Any) -> Any:
    """Recursively sanitize common JSON/export-like containers."""
    if isinstance(obj, str):
        return utf8_safe_text(obj)
    if isinstance(obj, dict):
        return {
            utf8_safe_text(key) if isinstance(key, str) else key: utf8_safe_obj(value)
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [utf8_safe_obj(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(utf8_safe_obj(item) for item in obj)
    return obj


def json_dumps_utf8(obj: Any, **kwargs: Any) -> str:
    kwargs.setdefault("ensure_ascii", False)
    text = json.dumps(utf8_safe_obj(obj), **kwargs)
    return utf8_safe_text(text)
