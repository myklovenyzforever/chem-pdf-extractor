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


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
