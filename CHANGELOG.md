# Changelog

## v0.3.0 - Release readiness, safer workflows, and Windows package polish

- Hardened local UI security boundaries, export safety, diagnostics, and secret redaction.
- Added pause/resume behavior for transient cloud/API/network failures after retries.
- Hardened cloud structured-output validation so malformed provider responses are normalized or reported safely.
- Changed the default extraction text budget to `max_chars = 80000`; explicit `0` still means no truncation.
- Added first-pass evaluation documentation, synthetic benchmark cases, and a mock end-to-end workflow test.
- Added optional provenance/review hint fields for page, section, table, source evidence, and verification review.
- Documented the field template workflow and contribution loop.
- Improved packaging maturity with console script metadata, wheel/package-data checks, dependency constraints guidance, and CI coverage.
- Fixed default PDF input discovery so source mode no longer scans the project root, bundled examples, or generated `.mineru_outputs` by default.
- Added bilingual Windows launchers and a user-root package layout for `input_pdfs/`, `logs/`, `.runtime/`, and `提取结果/`.
- Expanded README, release/feedback, project-status, configuration, Windows-package, and related documentation for safer user workflows.

## v0.2.2 - Web UI layout and statistics polish

- Refined the Web UI into a fixed-height, bottom-aligned three-column desktop workbench.
- Restored the intended dashboard structure after layout experimentation:
  - left column: Task Settings and Statistics;
  - middle column: LLM API Config and compact Progress;
  - right column: Run Logs.
- Kept Run Logs as the only main internally scrollable panel so long logs do not stretch the whole page.
- Added task statistics counters for extracted rows, suspicious rows, bad rows, and cache hits.
- Changed the Progress panel to a compact progress bar with ratio text such as `Done 0 / 0 = 0%`.
- Added and updated lightweight tests for layout behavior, task statistics, log scrolling, and Cloud/Ollama UI display logic.
- Kept Windows launcher behavior, release metadata structure, requirements files, MinerU behavior, PDF conversion behavior, LLM prompts, OpenAI-compatible cloud API behavior, and local Ollama behavior unchanged.

## v0.2.1 - Windows launcher UTF-8 and release metadata patch

- Fixed Windows launcher UTF-8 console setup to reduce Chinese output and path mojibake in CMD / PowerShell.
- Set `PYTHONUTF8` and `PYTHONIOENCODING` in the Windows batch launcher.
- Set PowerShell console input/output encoding to UTF-8 on a best-effort basis.
- Replaced a mojibake legacy runtime path candidate with the correct Chinese path.
- Updated package metadata to `0.2.1`.
- Kept backend extraction, MinerU behavior, cloud API behavior, and Web UI behavior unchanged.

## v0.2.0 - Windows first-run launcher, optional MinerU, and improved Web UI

- Added a Windows first-run launcher using `Start-Chem-PDF-Extractor.bat` and `install_and_start.ps1`.
- The launcher can create or reuse `.venv/`, install dependencies, start the local Web UI, and open the browser.
- Added backend selection for `pypdf_text`, `pymupdf4llm`, and optional `mineru`.
- Added optional MinerU support for complex layouts, tables, scanned PDFs, and high-performance Windows machines.
- Updated MinerU command discovery to prefer `.venv\Scripts\mineru.exe`, with `magic-pdf` kept only as a legacy fallback.
- Added safer MinerU installation fallback behavior: retry, continue with `pymupdf4llm`, or exit.
- Added OpenAI-compatible cloud model discovery through the provider `/models` endpoint when supported.
- Replaced the cloud model datalist with a real model dropdown plus manual model-name fallback.
- Moved advanced LLM service-name settings out of the normal UI while preserving config compatibility.
- Improved Cloud/Ollama UI behavior so Ollama-only fields are hidden in Cloud mode.
- Made PDF Mode visible and full-width for both Cloud and Ollama workflows.
- Simplified the Cloud API Config panel and removed the misleading local `Refresh Models` button from the cloud panel.
- Added a three-column Web UI workbench layout.
- Fixed Run Logs so long logs scroll inside the log panel instead of stretching the whole page.
- Preserved log auto-scroll behavior when the user is already near the bottom.
- Updated Windows package documentation and safety guidance.
- Added or updated lightweight tests for launcher behavior, MinerU command detection, cloud model UI behavior, and Web UI layout behavior.

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
