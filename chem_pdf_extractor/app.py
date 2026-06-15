from __future__ import annotations

import argparse
import os
import sys

from .config import (
    BAD_ROW_MIN_FILL_RATE,
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
    load_local_config,
    validate_cloud_start_config,
)
from .diagnostics import log_startup_event
from .security import redact_sensitive_text
from .text_safety import json_dumps_utf8


VALID_LLM_PROVIDERS = ("cloud", "ollama")


CLI_HELP_EPILOG = """\
Workflow notes:
  Local/private Ollama:
    python -m chem_pdf_extractor --cli --llm-provider ollama --model qwen2.5:7b

  Optional OpenAI-compatible cloud:
    set CHEM_PDF_EXTRACTOR_API_KEY, CHEM_PDF_EXTRACTOR_BASE_URL, and CHEM_PDF_EXTRACTOR_MODEL
    then run with --cli --llm-provider cloud.

Provider values:
  cloud   OpenAI-compatible cloud API. Converted PDF text is sent to the configured provider.
  ollama  Local Ollama. Use --no-translate-to-chinese if you want to avoid optional cloud translation from saved cloud config.

Extraction output is first-pass data for human verification; check source PDFs before using results.
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="chem-pdf-extractor",
        description="Chem-PDF-Extractor local-first PDF extraction workbench.",
        epilog=CLI_HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cli", action="store_true", help="Run command-line extraction instead of starting the Web UI.")
    parser.add_argument("--port", type=int, default=8766, help="Web UI port when not using --cli. Default: 8766.")
    parser.add_argument("--open-browser", action="store_true", help="Open the local Web UI in a browser after startup.")
    parser.add_argument("--input-dir", default=None, help="PDF input directory for --cli runs. Defaults to input_pdfs/.")
    parser.add_argument("--output", default=None, help="Output .xlsx path or output directory for --cli runs.")
    parser.add_argument(
        "--llm-provider",
        default="cloud",
        choices=VALID_LLM_PROVIDERS,
        metavar="{cloud,ollama}",
        help="LLM provider for extraction. Valid values: cloud, ollama. Default remains cloud for compatibility.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=(
            "Ollama model for --llm-provider ollama. In cloud mode, this is accepted as a "
            "legacy model alias when --cloud-model is not provided."
        ),
    )
    parser.add_argument("--no-translate-to-chinese", action="store_true", help="Disable optional Chinese translation/cleanup after extraction.")
    parser.add_argument("--cloud-service-name", default=None, help="Cloud service label for exported metadata. Default: openai_compatible.")
    parser.add_argument(
        "--cloud-model",
        default=None,
        help="OpenAI-compatible cloud model name. Can also be set with CHEM_PDF_EXTRACTOR_MODEL.",
    )
    parser.add_argument(
        "--cloud-api-key",
        default="",
        help="Cloud API key. Prefer CHEM_PDF_EXTRACTOR_API_KEY or local config so secrets are not stored in shell history.",
    )
    parser.add_argument(
        "--cloud-base-url",
        default=None,
        help="OpenAI-compatible Base URL, e.g. https://api.example.com/v1. Can also be set with CHEM_PDF_EXTRACTOR_BASE_URL.",
    )
    parser.add_argument("--cloud-active", action="store_true", help="Compatibility flag for saved cloud config; CLI cloud mode validates credentials directly.")
    parser.add_argument("--pdf-mode", default=DEFAULT_PDF_MODE, choices=PDF_MODE_CHOICES, help="PDF conversion mode.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="Max extracted markdown characters. 0 means no truncation.")
    parser.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX, help="Ollama context window hint.")
    parser.add_argument("--llm-timeout", type=int, default=0, help="LLM timeout seconds. 0 means no explicit timeout.")
    parser.add_argument("--bad-row-min-fill-percent", type=float, default=BAD_ROW_MIN_FILL_RATE * 100, help="Delete rows below this field-fill percentage.")
    parser.add_argument("--ollama-base-url", default=DEFAULT_OLLAMA_BASE_URL, help="Local Ollama base URL.")
    parser.set_defaults(recursive=True)
    parser.add_argument("--recursive", dest="recursive", action="store_true", help="Process PDF files recursively. Enabled by default.")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Only process PDF files directly inside --input-dir.")
    parser.add_argument("--auto-fallback", action="store_true", help="For Ollama, try fallback local models when the requested model fails.")
    parser.add_argument("--copy-failed-sources", action="store_true", help="Copy failed source PDFs for debugging.")
    parser.add_argument("--no-auto-install", action="store_true", help="Do not auto-install missing Python dependencies.")
    return parser.parse_args(argv)


def _first_non_empty(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def build_cli_config(args: argparse.Namespace) -> dict[str, object]:
    local_cloud_config = load_local_config()
    env_api_key = _first_non_empty(
        os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY"),
        os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY"),
    )
    cloud_service_name = _first_non_empty(
        args.cloud_service_name,
        local_cloud_config.get("cloud_service_name"),
        DEFAULT_CLOUD_SERVICE_NAME,
    )
    cloud_model_arg = _first_non_empty(args.cloud_model)
    if not cloud_model_arg and args.llm_provider == "cloud" and args.model != DEFAULT_MODEL:
        cloud_model_arg = str(args.model or "").strip()
    cloud_model = _first_non_empty(
        cloud_model_arg,
        local_cloud_config.get("cloud_model"),
        os.environ.get("CHEM_PDF_EXTRACTOR_MODEL"),
        DEFAULT_CLOUD_MODEL,
    )
    cloud_base_url = _first_non_empty(
        args.cloud_base_url,
        local_cloud_config.get("cloud_base_url"),
        os.environ.get("CHEM_PDF_EXTRACTOR_BASE_URL"),
        DEFAULT_CLOUD_BASE_URL,
    )
    selected_model = cloud_model if args.llm_provider == "cloud" else args.model
    return {
        "input_dir": args.input_dir,
        "output_path": args.output,
        "llm_provider": args.llm_provider,
        "model": selected_model,
        "translate_to_chinese": not args.no_translate_to_chinese,
        "cloud_service_name": cloud_service_name,
        "cloud_model": cloud_model,
        "cloud_api_key": _first_non_empty(
            args.cloud_api_key,
            local_cloud_config.get("cloud_api_key"),
            env_api_key,
        ),
        "cloud_base_url": cloud_base_url,
        "cloud_active": args.cloud_active or args.llm_provider == "cloud",
        "pdf_mode": args.pdf_mode,
        "max_chars": args.max_chars,
        "num_ctx": args.num_ctx,
        "llm_timeout": args.llm_timeout,
        "bad_row_min_fill_percent": args.bad_row_min_fill_percent,
        "ollama_base_url": args.ollama_base_url,
        "recursive": args.recursive,
        "auto_fallback": args.auto_fallback,
        "copy_failed_sources": args.copy_failed_sources,
        "fields": DEFAULT_FIELDS,
    }


def print_cli_config_error(error: str) -> None:
    safe_error = redact_sensitive_text(str(error or "Invalid CLI configuration."))
    print(f"CLI configuration error: {safe_error}", file=sys.stderr)


def run_cli(args: argparse.Namespace) -> int:
    from .config import default_input_dir, default_output_path, ensure_dependencies, import_runtime_dependencies
    from .extractor import JobState, run_extraction_job

    config = build_cli_config(args)
    config["input_dir"] = config["input_dir"] or str(default_input_dir())
    config["output_path"] = config["output_path"] or str(default_output_path())
    validation_error = validate_cloud_start_config(config)
    if validation_error:
        print_cli_config_error(validation_error)
        return 2

    log_startup_event(mode="cli")
    ensure_dependencies(auto_install=not args.no_auto_install)
    runtime = import_runtime_dependencies()
    state = JobState()
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
        print("\nInterrupted by user.")
