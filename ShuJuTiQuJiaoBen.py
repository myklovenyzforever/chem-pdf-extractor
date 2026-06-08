"""Legacy compatibility entry point for Chem-PDF-Extractor.

Recommended:
  python -m chem_pdf_extractor

Legacy:
  python ShuJuTiQuJiaoBen.py
"""

from chem_pdf_extractor.entrypoint import run


if __name__ == "__main__":
    raise SystemExit(run(mode="legacy_script"))
