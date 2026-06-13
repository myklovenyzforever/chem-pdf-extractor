from __future__ import annotations

import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .security import redact_sensitive_obj, redact_sensitive_text
from .text_safety import json_dumps_utf8, utf8_safe_text

_INSTALLED_EXCEPTHOOK = False
_SECRET_KEYWORDS = ("api_key", "apikey", "api-key", "token", "password", "secret", "key")
_SECRET_FLAGS = {"--cloud-api-key", "--api-key", "--key"}


def diagnostics_log_dir() -> Path:
    configured = os.environ.get("CHEM_PDF_EXTRACTOR_LOG_DIR")
    log_dir = Path(configured).expanduser() if configured else PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def diagnostic_log_path(name: str) -> Path:
    file_name = Path(str(name or "diagnostic.log")).name or "diagnostic.log"
    return diagnostics_log_dir() / file_name


def sanitize_argv(argv: list[str] | None = None) -> list[str]:
    source = list(sys.argv if argv is None else argv)
    sanitized: list[str] = []
    redact_next = False
    for arg in source:
        if redact_next:
            sanitized.append("<redacted>")
            redact_next = False
            continue
        lowered = arg.lower()
        if lowered in _SECRET_FLAGS:
            sanitized.append(arg)
            redact_next = True
            continue
        if any(lowered.startswith(flag + "=") for flag in _SECRET_FLAGS):
            key, _, _value = arg.partition("=")
            sanitized.append(f"{key}=<redacted>")
            continue
        sanitized.append(redact_sensitive_text(arg))
    return sanitized


def _sensitive_env_keys() -> list[str]:
    keys = []
    for key in os.environ:
        lowered = key.lower()
        if any(keyword in lowered for keyword in _SECRET_KEYWORDS):
            keys.append(f"{key}=<redacted>")
    return sorted(keys)


def append_diagnostic_log(name: str, message: str) -> None:
    try:
        path = diagnostic_log_path(name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_message = redact_sensitive_text(utf8_safe_text(str(message)))
        with path.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"[{timestamp}] {safe_message}\n")
    except Exception:
        return


def log_startup_event(mode: str, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "event": "startup",
        "mode": mode,
        "python_executable": sys.executable,
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "project_root": str(PROJECT_ROOT),
        "argv": sanitize_argv(),
        "sensitive_env": _sensitive_env_keys(),
    }
    if extra:
        payload["extra"] = redact_sensitive_obj(extra)
    append_diagnostic_log("startup.log", json_dumps_utf8(payload, sort_keys=True))


def log_process_exit(exit_code: int | str | None) -> None:
    append_diagnostic_log("startup.log", f"process exited; exit code: {exit_code}")


def log_exception(exc: BaseException, context: str = "") -> None:
    try:
        payload = {
            "context": context,
            "exception_type": type(exc).__name__,
            "exception_message": redact_sensitive_text(str(exc)),
            "traceback": redact_sensitive_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__))),
        }
        append_diagnostic_log("crash.log", json_dumps_utf8(payload, sort_keys=True))
    except Exception:
        return


def install_global_exception_hook() -> None:
    global _INSTALLED_EXCEPTHOOK
    if _INSTALLED_EXCEPTHOOK:
        return
    original_hook = sys.excepthook

    def diagnostic_excepthook(exc_type: type[BaseException], exc: BaseException, tb: Any) -> None:
        if exc_type is KeyboardInterrupt:
            append_diagnostic_log("startup.log", "interrupted by user")
        else:
            exc.__traceback__ = tb
            log_exception(exc, context="unhandled_exception")
        original_hook(exc_type, exc, tb)

    sys.excepthook = diagnostic_excepthook
    _INSTALLED_EXCEPTHOOK = True
