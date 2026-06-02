"""Chem-PDF-Extractor: local web UI for extracting chemical data from PDFs.

Default usage:
  python ShuJuTiQuJiaoBen.py

The script opens a local browser page. From that page you can:
  - choose the real Ollama model used for processing
  - define up to 30 extraction fields
  - switch among three PDF-to-Markdown/text conversion modes
  - process large PDF batches with a progress bar

No cloud API is used. Ollama must be running locally.
"""

from chem_pdf_extractor.app import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户中断。")