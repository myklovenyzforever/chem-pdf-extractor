# Chem-PDF-Extractor

## Overview

Chem-PDF-Extractor is an open-source tool for extracting structured experimental data from scientific PDF papers, with a focus on chemical engineering, catalysis, materials, and environmental research.

It helps researchers convert PDF papers to Markdown/text, define configurable LLM-based extraction fields, extract multiple records from one paper, and export structured results to Excel/CSV. It also supports low-quality row filtering, error logs, suspicious-data records, bad-data records, resumable processing, cache reuse, OpenAI-compatible APIs, and local Ollama models.

## Why This Project

Experimental information in scientific papers is often scattered across paragraphs, tables, figures, captions, and supplementary materials. Manually collecting feedstocks, catalysts, reaction temperature, pressure, conversion, selectivity, yield, and product information is slow and error-prone. This project provides a local, inspectable workflow for building first-pass structured datasets that still require human review.

## Features

- Batch PDF processing.
- PDF to Markdown/text conversion.
- Configurable LLM-based extraction fields.
- Multiple records from one paper written as multiple rows.
- Excel and CSV output.
- Low-fill-rate bad row filtering.
- Error logs, suspicious-data records, and bad-data records.
- Pause, resume, stop, and resumable processing.
- Reuse of `md文件/` and `抽取缓存/`.
- OpenAI-compatible API support.
- Local Ollama model support.

## Quick Start

```powershell
git clone https://github.com/myklovenyzforever/chem-pdf-extractor.git
cd chem-pdf-extractor
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```

Open the local URL printed in the terminal, select a PDF folder, configure extraction fields, and start processing. Test with 3-5 PDFs before running a large batch.

## Configuration

This repository does not include any real API key, token, or password.

Normal users can enter the API key in the web interface. The configuration can be saved to `config.local.json`, which is ignored by Git. `config.example.json` is only a template and contains placeholders.

Environment variables are supported for advanced users, but they are optional and not required for normal use.

```powershell
$env:CHEM_PDF_EXTRACTOR_API_KEY="YOUR_API_KEY_HERE"
$env:CHEM_PDF_EXTRACTOR_BASE_URL="https://api.example.com/v1"
$env:CHEM_PDF_EXTRACTOR_MODEL="provider/model-name"
```

## One-click Windows Package

The GitHub source repository does not include `YiLaiHuanJing/`. A bundled Windows package may be provided through GitHub Releases for non-programming users.

The one-click package may include:

- `ShuJuTiQuJiaoBen.py`
- `YiJianQiDong.bat`
- `YiLaiHuanJing/`

The runtime folder is excluded from the source repository because it is large and machine-specific.

## Examples

The `examples/` directory contains synthetic demonstration files:

- `sample_fields.json`: chemistry/catalysis-oriented extraction fields.
- `sample_output.csv`: expected CSV output structure.
- `sample_output.xlsx`: expected Excel output structure.

The example data is synthetic and does not represent real published papers.

## Limitations

- LLM extraction results should be reviewed manually.
- Complex scanned PDFs may require OCR or MinerU support.
- The project does not include any built-in commercial API key.
- Example data is synthetic and does not represent real published papers.
- The current version keeps the main app as a single Python file to preserve the existing Windows workflow.

## Roadmap

- More field templates for chemical engineering and catalysis.
- Better PDF layout handling.
- Regression examples.
- More tests.
- Optional English UI.
- Documentation improvements.

## License

MIT License. See `LICENSE`.

# 中文说明

## 项目简介

Chem-PDF-Extractor 面向化工、材料、催化、环境等方向的研究生和科研人员，用于批量处理 PDF 文献，并将实验条件、催化剂、原料、温度、压力、转化率、选择性等信息提取为 Excel/CSV 表格。

本工具适合用于文献综述、实验数据整理和科研数据挖掘的初步结构化处理。大模型输出结果需要人工核验，不能直接作为最终科研结论。

## 核心功能

- 批量处理 PDF 文献。
- PDF 转 Markdown / 文本。
- 使用 OpenAI-compatible API 或本地 Ollama 模型抽取字段。
- 支持用户自定义抽取字段。
- 一篇文献多条数据写成多行。
- 导出 Excel / CSV。
- 自动过滤低填写率坏数据。
- 生成错误日志、坏数据、可疑数据。
- 支持暂停、继续、停止和断点续跑。
- 支持复用 `md文件/` 和 `抽取缓存/`。

## 快速开始

普通用户可以使用带 `YiLaiHuanJing/` 的一键运行包：

1. 解压工具包。
2. 双击 `YiJianQiDong.bat`。
3. 打开黑色窗口显示的网址。
4. 在网页里填写 API Key。
5. 选择 PDF 文件夹。
6. 配置抽取字段。
7. 点击开始处理。
8. 查看 `提取结果.xlsx`、`错误日志.txt`、`坏数据.xlsx`、`可疑数据.xlsx`。

源码用户可以运行：

```powershell
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```
