"""Alternative script entry point for Chem-PDF-Extractor.

Recommended:
  python -m chem_pdf_extractor

Alternative script entry:
  python run_chem_pdf_extractor.py
"""

from chem_pdf_extractor.entrypoint import run


if __name__ == "__main__":
    raise SystemExit(run(mode="script"))
