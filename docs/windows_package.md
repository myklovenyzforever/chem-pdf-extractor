# Windows One-click Package Guide

This document is for packaging and safety guidance only.

The source repository does not include `bundled_runtime/` or `YiLaiHuanJing/`. `bundled_runtime/` is the recommended runtime directory name for Windows packages. `YiLaiHuanJing/` is a legacy bundled runtime name. Runtime folders are large, machine-specific, and better distributed through a release package when needed. Do not commit packaged runtime folders to the source repository. Do not include private PDFs, API keys, logs, outputs, caches, or `config.local.json` in release packages.

## Purpose

This guide explains how a Windows one-click package may be prepared for non-programming users.

It is intended for maintainers or advanced users who want to build a local Windows package. It does not replace the source-based installation workflow.

## Why bundled_runtime/ is not in the source repository

`bundled_runtime/` is the recommended bundled runtime or dependency environment name. `YiLaiHuanJing/` remains supported as a legacy bundled runtime name.

It is excluded from the source repository because:

- it can be large;
- it may be machine-specific;
- it may contain generated files;
- it should not be reviewed like source code;
- the source repository should stay small, auditable, and safe.

If a bundled package is provided, it should be attached to a GitHub Release, not committed to `main`.

## Recommended package structure

An example Windows package may look like this:

```text
Chem-PDF-Extractor-Windows/
  Start-Chem-PDF-Extractor.bat
  install_and_start.ps1
  run_chem_pdf_extractor.py
  requirements.txt
  requirements-core.txt
  constraints.txt
  requirements-mineru.txt
  config.example.json
  README or quick-start note
  chem_pdf_extractor/
  docs/windows_package.md
```

Optional legacy compatibility files:

```text
  YiJianQiDong.bat
  YiLaiHuanJing/
```

The exact structure may change, but the package should make it clear how the user starts the application and where local outputs are written.

## Package types

### A. GitHub Download ZIP

This is a source package. It does not include Python, `.venv/`, installed dependencies, MinerU models, or a bundled runtime. Users can still run `Start-Chem-PDF-Extractor.bat`; the first-run launcher will install dependencies online when the network and Python installer are available.

### B. Online first-run release package

This is the recommended release packaging mode for now.

User flow:

1. Download and extract the release zip.
2. Double-click `Start-Chem-PDF-Extractor.bat`.
3. The launcher runs `install_and_start.ps1`.
4. The launcher checks Python, creates `.venv/`, asks for a PDF backend choice, installs matching dependencies, starts the local Web UI, and opens the browser.

### C. Fully offline package

This is not implemented by default. A fully offline package would require bundling Python, wheelhouse files, MinerU dependencies/models, and possibly large runtime assets. It would be much larger and should not be committed to the repository.

## Release dependency constraints

Normal users can install with `requirements.txt` or `requirements-core.txt` directly. The release constraints file is for maintainer verification, not mandatory development setup.

For a release package check, maintainers may install with:

```powershell
python -m pip install -r requirements.txt -c constraints.txt
```

or, for the smaller fallback dependency set:

```powershell
python -m pip install -r requirements-core.txt -c constraints.txt
```

`constraints.txt` intentionally uses broad upper bounds instead of exact pins. Refresh it when testing support for a new major dependency version, after a dependency deprecates a current version range, or before preparing a release that should validate newer package families.

## PDF backend choices

`pypdf_text`:

- smallest install;
- fastest installation;
- best fallback compatibility;
- weaker layout, table, and multi-column handling.

`pymupdf4llm`:

- recommended default;
- balanced install size and extraction quality;
- suitable for most research PDFs.

`mineru`:

- optional enhanced backend;
- large install size;
- slower first-time installation;
- suitable for complex layouts, tables, scanned PDFs, and high-performance PCs;
- may require more disk space, memory, installation time, and external downloads.

## Files that may be included

- `run_chem_pdf_extractor.py`
- `Start-Chem-PDF-Extractor.bat`
- `install_and_start.ps1`
- `YiJianQiDong.bat` as a legacy compatibility launcher
- `requirements.txt`
- `requirements-core.txt`
- `constraints.txt`
- `requirements-mineru.txt`
- `config.example.json`
- `LICENSE`
- `README` or a short quick-start note
- `bundled_runtime/` only in release packages, not in source commits
- `YiLaiHuanJing/` as a legacy compatibility runtime directory only

## Files that must not be included

- `config.local.json`
- real API keys
- tokens
- passwords
- private PDFs
- unpublished manuscripts
- user input folders
- extracted Excel or CSV outputs
- logs containing local paths or extracted private data
- `logs/`
- `md文件/`
- `抽取缓存/`
- error logs
- suspicious-data records
- bad-data records
- `.env`
- `.venv` if it contains local user state
- `.runtime/`
- `.mineru_outputs/`
- `mineru_models/`
- wheel caches or downloaded model caches
- `__pycache__/`
- `.pytest_cache/`
- local absolute paths
- private industrial or research data

## Packaging safety checklist

Before creating a Windows package, check:

- The package was built from a clean working tree.
- No API key, token, password, or `config.local.json` is included.
- No private PDF or unpublished manuscript is included.
- No output Excel/CSV file from a real user run is included.
- No logs, caches, `md文件/`, `抽取缓存/`, or temporary files are included.
- No local absolute paths are visible in documentation or logs.
- The package starts correctly on a clean Windows machine or a clean test folder.
- The terminal prints a local Web UI URL.
- The Web UI can be opened manually in a browser.
- A small synthetic test can run without using private data.
- The package is scanned or inspected before release upload.

## User quick start

1. Unzip the package to a simple path.
2. Avoid paths with special characters if startup fails.
3. Double-click `Start-Chem-PDF-Extractor.bat`.
4. Choose a PDF backend in the PowerShell menu. Press Enter for `pymupdf4llm` unless a previous backend choice is shown.
5. Let the launcher install dependencies and start the local Web UI.
6. If the browser does not open automatically, copy the local URL printed in the terminal.
7. Start with 3-5 PDFs before running a large batch.
8. Enter API keys only in the local UI or local config.
9. Do not share `config.local.json`.

Windows environments vary. If the bundled package fails, users may still use the source installation workflow.

## Troubleshooting

### The browser does not open

Copy the local URL printed in the terminal and open it manually.

### PDF parsing fails

Try a smaller batch first. If optional PDF backends fail, rerun `Start-Chem-PDF-Extractor.bat` and choose a different backend. Use option `[1] pypdf_text` for the smallest fallback install, option `[2] pymupdf4llm` for the recommended default, or option `[3] mineru` for the larger enhanced backend.

### MinerU installation fails

MinerU is optional and may require a larger download, more disk space, and more installation time. MinerU 3.x uses `mineru.exe` as the primary CLI; `magic-pdf` is only a legacy fallback. If MinerU installation fails, check `logs/install.log`. The launcher should let you retry MinerU installation, continue immediately with option `[2] pymupdf4llm`, or exit.

### Windows + Python 3.12 PDF backend issues

Some optional PDF backends may fail in certain Windows + Python 3.12 environments. Use Python 3.11 for the broadest compatibility, or use `requirements-core.txt` and the `pypdf_text` fallback where applicable.

### API key errors

Check local configuration. Do not commit or upload API keys. Do not post keys in public GitHub issues.

### Output looks incomplete

LLM extraction results are first-pass results. Check the original paper manually. Try reducing the number of fields or processing a small batch first.

## Maintainer release notes

When preparing a GitHub Release package:

- Use a clean checkout.
- Build the package in a temporary folder.
- Do not package the repository's local test outputs.
- Do not include user data.
- Verify the package contents manually before upload.
- Prefer synthetic examples for testing.
- Mention in the release notes that AI extraction results require manual verification.
- Do not claim 100% extraction accuracy.
- Do not claim the package contains built-in commercial API credits or keys.

## Release checklist

Before publishing the release zip:

- Run `python -m py_compile run_chem_pdf_extractor.py`.
- Run `python -m unittest discover -s tests -v`.
- Run `python -m build`.
- Install the built wheel into a clean virtual environment and run `chem-pdf-extractor --help`.
- For release dependency verification, test `python -m pip install -r requirements.txt -c constraints.txt`.
- Create a clean copy of the repository.
- Do not include `.git/`.
- Do not include `.venv/`.
- Do not include `.runtime/`.
- Do not include `logs/`.
- Do not include PDFs.
- Do not include extracted outputs.
- Do not include `config.local.json`.
- Include `Start-Chem-PDF-Extractor.bat`.
- Include `install_and_start.ps1`.
- Include `requirements.txt`.
- Include `requirements-core.txt`.
- Include `constraints.txt`.
- Include `requirements-mineru.txt`.
- Include `chem_pdf_extractor/`.
- Include `run_chem_pdf_extractor.py`.
- Include `README.md`.
- Include `docs/windows_package.md`.

## Manual Windows test plan

Test A: Fresh Windows machine with no Python

1. Double-click `Start-Chem-PDF-Extractor.bat`.
2. Confirm the launcher attempts Python 3.11 installation through winget.
3. Confirm the launcher creates `.venv/`.
4. Choose option `[2] pymupdf4llm`.
5. Confirm dependencies install.
6. Confirm the web app starts.
7. Confirm the browser opens `http://127.0.0.1:8766/`.

Test B: Windows machine with Python 3.11 installed

1. Double-click `Start-Chem-PDF-Extractor.bat`.
2. Confirm the launcher creates `.venv/`.
3. Choose option `[1] pypdf_text`.
4. Confirm it installs `requirements-core.txt`.
5. Confirm it starts with `--pdf-mode pypdf_text`.

Test C: Recommended mode

1. Choose option `[2]` or press Enter when no previous backend is configured.
2. Confirm it installs `requirements.txt`.
3. Confirm it starts with `--pdf-mode pymupdf4llm`.

Test D: MinerU mode

1. Choose option `[3] mineru`.
2. Confirm the launcher installs `requirements.txt`.
3. Confirm the launcher installs `uv`.
4. Confirm the launcher installs `requirements-mineru.txt` through `uv`.
5. Confirm `.venv\Scripts\mineru.exe` exists after installation.
6. Confirm the launcher sets `MINERU_COMMAND` to `.venv\Scripts\mineru.exe` and starts with `--pdf-mode mineru`.
7. If MinerU installation fails, confirm the launcher offers retry, continue with `[2] pymupdf4llm`, or exit, and points to `logs/install.log`.

Test E: Relaunch

1. Relaunch `Start-Chem-PDF-Extractor.bat`.
2. Confirm `.runtime/launcher_settings.json` remembers the previous backend.
3. Press Enter to reuse the previous backend.
4. Confirm choosing a different backend updates the saved setting.

Test F: No secrets check

1. Confirm no API keys are included.
2. Confirm `config.local.json` is not included.
3. Confirm PDFs, extracted outputs, `.venv/`, `.runtime/`, logs, cache folders, and runtime settings are not committed.

## 中文说明

这个文档用于说明 Windows 一键包的打包边界和安全检查。源码仓库不包含推荐运行时目录 `bundled_runtime/`，也不包含旧兼容运行时目录 `YiLaiHuanJing/`，因为这些目录通常较大、与机器环境相关，更适合作为 release 包的一部分，而不是提交到 `main` 分支。

一键包中不得包含真实 API Key、`config.local.json`、私有 PDF、未发表论文、真实输出表格、日志、缓存、`md文件/`、`抽取缓存/` 或任何工业/科研保密数据。

用户启动时推荐双击 `Start-Chem-PDF-Extractor.bat`。`YiJianQiDong.bat` 和 `YiLaiHuanJing/` 作为兼容旧包保留。如果浏览器没有自动打开，应复制终端中打印的本地 URL 到浏览器。大模型抽取结果必须人工核验，不能直接作为最终科研结论。
