from __future__ import annotations

import argparse

from .config import (
    DEFAULT_CLOUD_BASE_URL,
    DEFAULT_CLOUD_MODEL,
    DEFAULT_CLOUD_SERVICE_NAME,
    DEFAULT_FIELDS,
    DEFAULT_MAX_CHARS,
    DEFAULT_MODEL,
    DEFAULT_NUM_CTX,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_PDF_MODE,
    PDF_MODE_CHOICES,
    BAD_ROW_MIN_FILL_RATE,
    load_local_config,
)
from .diagnostics import log_startup_event
from .text_safety import json_dumps_utf8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chem-PDF-Extractor")
    parser.add_argument("--cli", action="store_true", help="不启动网页，直接用命令行参数处理。")
    parser.add_argument("--port", type=int, default=8766, help="网页端口，默认 8766。")
    parser.add_argument("--open-browser", action="store_true", help="启动 Web UI 后自动打开浏览器。")
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--llm-provider", default="cloud", choices=["ollama", "cloud"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--no-translate-to-chinese", action="store_true")
    parser.add_argument("--cloud-service-name", default=DEFAULT_CLOUD_SERVICE_NAME)
    parser.add_argument("--cloud-model", default=DEFAULT_CLOUD_MODEL)
    parser.add_argument("--cloud-api-key", default="")
    parser.add_argument("--cloud-base-url", default=DEFAULT_CLOUD_BASE_URL)
    parser.add_argument("--cloud-active", action="store_true")
    parser.add_argument("--pdf-mode", default=DEFAULT_PDF_MODE, choices=PDF_MODE_CHOICES)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX)
    parser.add_argument("--llm-timeout", type=int, default=0, help="0 表示不限制。")
    parser.add_argument("--bad-row-min-fill-percent", type=float, default=BAD_ROW_MIN_FILL_RATE * 100)
    parser.add_argument("--ollama-base-url", default=DEFAULT_OLLAMA_BASE_URL)
    parser.set_defaults(recursive=True)
    parser.add_argument("--recursive", dest="recursive", action="store_true")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false")
    parser.add_argument("--auto-fallback", action="store_true")
    parser.add_argument("--no-auto-install", action="store_true")
    return parser.parse_args()


def run_cli(args: argparse.Namespace) -> int:
    from .config import default_input_dir, default_output_path, ensure_dependencies, import_runtime_dependencies
    from .extractor import JobState, run_extraction_job
    log_startup_event(mode="cli")
    ensure_dependencies(auto_install=not args.no_auto_install)
    runtime = import_runtime_dependencies()
    state = JobState()
    local_cloud_config = load_local_config()
    config = {
        "input_dir": args.input_dir or str(default_input_dir()),
        "output_path": args.output or str(default_output_path()),
        "llm_provider": args.llm_provider,
        "model": args.cloud_model if args.llm_provider == "cloud" and args.model == DEFAULT_MODEL else args.model,
        "translate_to_chinese": not args.no_translate_to_chinese,
        "cloud_service_name": args.cloud_service_name or local_cloud_config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
        "cloud_model": args.cloud_model or local_cloud_config.get("cloud_model") or DEFAULT_CLOUD_MODEL,
        "cloud_api_key": (
            args.cloud_api_key
            or local_cloud_config.get("cloud_api_key")
            or ""
        ),
        "cloud_base_url": args.cloud_base_url or local_cloud_config.get("cloud_base_url") or DEFAULT_CLOUD_BASE_URL,
        "cloud_active": args.cloud_active or args.llm_provider == "cloud",
        "pdf_mode": args.pdf_mode,
        "max_chars": args.max_chars,
        "num_ctx": args.num_ctx,
        "llm_timeout": args.llm_timeout,
        "bad_row_min_fill_percent": args.bad_row_min_fill_percent,
        "ollama_base_url": args.ollama_base_url,
        "recursive": args.recursive,
        "auto_fallback": args.auto_fallback,
        "fields": DEFAULT_FIELDS,
    }
    run_extraction_job(config, runtime, state)
    snapshot = state.snapshot()
    print(json_dumps_utf8(snapshot, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    if args.cli:
        return run_cli(args)
    from .server import start_web_app
    return start_web_app(
        args.port,
        auto_install=not args.no_auto_install,
        open_browser=args.open_browser,
        initial_pdf_mode=args.pdf_mode,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户中断。")
