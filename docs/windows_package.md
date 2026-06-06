# Windows One-click Package Guide

This document is for packaging and safety guidance only.

The source repository does not include `YiLaiHuanJing/`. `YiLaiHuanJing/` is excluded because it is large, machine-specific, and better distributed through a release package when needed. Do not commit packaged runtime folders to the source repository. Do not include private PDFs, API keys, logs, outputs, caches, or `config.local.json` in release packages.

## Purpose

This guide explains how a Windows one-click package may be prepared for non-programming users.

It is intended for maintainers or advanced users who want to build a local Windows package. It does not replace the source-based installation workflow.

## Why YiLaiHuanJing/ is not in the source repository

`YiLaiHuanJing/` is a bundled runtime or dependency environment.

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
  ShuJuTiQuJiaoBen.py
  YiJianQiDong.bat
  requirements.txt
  requirements-core.txt
  config.example.json
  README or quick-start note
  YiLaiHuanJing/
```

The exact structure may change, but the package should make it clear how the user starts the application and where local outputs are written.

## Files that may be included

- `ShuJuTiQuJiaoBen.py`
- `YiJianQiDong.bat`
- `requirements.txt`
- `requirements-core.txt`
- `config.example.json`
- `LICENSE`
- `README` or a short quick-start note
- `YiLaiHuanJing/` only in release packages, not in source commits

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
- `md文件/`
- `抽取缓存/`
- error logs
- suspicious-data records
- bad-data records
- `.env`
- `.venv` if it contains local user state
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
3. Double-click `YiJianQiDong.bat` if provided.
4. If the browser does not open automatically, copy the local URL printed in the terminal.
5. Start with 3-5 PDFs before running a large batch.
6. Enter API keys only in the local UI or local config.
7. Do not share `config.local.json`.

Windows environments vary. If the bundled package fails, users may still use the source installation workflow.

## Troubleshooting

### The browser does not open

Copy the local URL printed in the terminal and open it manually.

### PDF parsing fails

Try a smaller batch first. If optional PDF backends fail, use the core fallback route when available.

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

## 中文说明

这个文档用于说明 Windows 一键包的打包边界和安全检查。源码仓库不包含 `YiLaiHuanJing/`，因为该目录通常较大、与机器环境相关，更适合作为 release 包的一部分，而不是提交到 `main` 分支。

一键包中不得包含真实 API Key、`config.local.json`、私有 PDF、未发表论文、真实输出表格、日志、缓存、`md文件/`、`抽取缓存/` 或任何工业/科研保密数据。

用户启动时可以双击 `YiJianQiDong.bat`。如果浏览器没有自动打开，应复制终端中打印的本地 URL 到浏览器。大模型抽取结果必须人工核验，不能直接作为最终科研结论。
