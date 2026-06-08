"""Chem-PDF-Extractor: local Web UI and CLI for extracting structured chemical data from PDFs.

Default Web usage:
  python ShuJuTiQuJiaoBen.py

CLI usage example:
  python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text

The script starts a local Web UI by default. From the page you can:
  - choose local Ollama or an OpenAI-compatible cloud API provider
  - configure custom extraction fields
  - choose a PDF conversion backend
  - export extracted data to Excel / CSV with logs for review

AI extraction results must be manually reviewed before scientific use.
"""

from chem_pdf_extractor.app import main
from chem_pdf_extractor.diagnostics import (
    append_diagnostic_log,
    install_global_exception_hook,
    log_exception,
    log_process_exit,
    log_startup_event,
)


def _run() -> int:
    install_global_exception_hook()
    log_startup_event(mode="entrypoint")
    exit_code = 0
    try:
        result = main()
        exit_code = int(result or 0)
        return exit_code
    except KeyboardInterrupt:
        exit_code = 130
        append_diagnostic_log("startup.log", "interrupted by user")
        print("\nInterrupted by user.")
        return exit_code
    except Exception as exc:
        exit_code = 1
        log_exception(exc, context="top_level")
        print("Fatal error. See logs/crash.log for details.")
        return exit_code
    finally:
        log_process_exit(exit_code)


if __name__ == "__main__":
    raise SystemExit(_run())
