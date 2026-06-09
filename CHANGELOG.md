# Changelog

## v0.1.2 - Windows compatibility and release cleanup

- Kept a lightweight script launcher after modularization.
- Moved main implementation into the `chem_pdf_extractor/` package modules.
- Removed hardcoded cloud API key exposure from Web UI defaults.
- Added safer local configuration handling for cloud API settings.
- Refactored PDF backend loading so `pymupdf4llm` and `pymupdf` are no longer imported during startup.
- Treated `pymupdf4llm` and `pymupdf` as optional lazy-loaded PDF backends.
- Fixed startup failure on some Windows + Python 3.12 environments when `pymupdf4llm` fails during import.
- Added fallback behavior from `auto` / `mineru` modes to `pypdf_text`.
- Added tests to ensure optional PDF backends are not loaded during startup.
- Updated documentation for Python 3.11 recommendation and `pypdf_text` fallback usage.
- Updated release metadata and entry script documentation.
- Cleaned Markdown encoding issues in documentation files.
- Made Web UI browser opening optional: the server now prints the local URL by default, and automatic browser opening is available with `--open-browser`.

## v0.1.1 - Bilingual Web UI

- Added Chinese / English language switch in the Web UI.
- Added bilingual UI labels, buttons, placeholders, status text, and field descriptions.
- Added README language navigation for quick switching between English and Chinese sections.
- Improved Web UI layout for bilingual text.
- Fixed overflow issues in the API configuration area and extraction field table.
- Updated the Web UI screenshot path and README display.

## v0.1.0 - Initial open-source preparation

- Removed hardcoded API keys.
- Added local configuration template.
- Added bilingual README, quickstart, configuration, and examples documentation.
- Added examples and basic tests.
- Preserved the Windows one-click workflow.
