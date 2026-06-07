# Chem-PDF-Extractor

Chem-PDF-Extractor is an open-source tool for extracting structured experimental data from chemical engineering, catalysis, materials, energy, and environmental research PDFs into Excel/CSV tables. It is designed for literature reviews, preliminary dataset construction, and manual verification workflows.

Chem-PDF-Extractor 是一个面向化工、催化、材料、能源与环境领域论文的开源 PDF 数据抽取工具，可将文献中的实验条件和结果整理为 Excel/CSV 表格，适用于文献综述、初步数据集构建和后续人工核验流程。

**Language / 语言:** [English](#english) | [中文](#chinese)

<a id="english"></a>

## Overview

The project provides an inspectable first-pass workflow for converting PDF papers to Markdown/text, defining configurable LLM-based extraction fields, extracting multiple records from one paper, and exporting structured results for review. It also supports low-quality row filtering, error logs, suspicious-data records, bad-data records, resumable processing, cache reuse, OpenAI-compatible APIs, and local Ollama models.

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

By default, the program prints the local Web UI URL in the terminal and does not open the browser automatically. Copy the printed URL into your browser, select a PDF folder, configure extraction fields, and start processing. Test with 3-5 PDFs before running a large batch.

If you want the program to open the browser automatically, run:

```powershell
python ShuJuTiQuJiaoBen.py --open-browser
```

If `pymupdf4llm` / `pymupdf` fails to install or import on Windows + Python 3.12, use the core dependency fallback:

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

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

See [Windows One-click Package Guide](docs/windows_package.md) for packaging structure, safety checklist, and release notes.

## Examples

The `examples/` directory contains synthetic demonstration files:

- `sample_fields.json`: chemistry/catalysis-oriented extraction fields.
- `sample_output.csv`: expected CSV output structure.
- `sample_output.xlsx`: expected Excel output structure.
- `demo_literature_batch/`: complete synthetic batch demo with input PDFs, field configuration, and expected output shape.
- `demo_literature_batch/`：完整合成批处理示例，包含输入 PDF、字段配置和期望输出表格结构。
- `field_templates/`: reusable field templates for catalysis, materials synthesis, environmental treatment, and electrochemistry workflows.
- `field_templates/`：面向催化反应、材料合成、环境处理和电化学方向的可复用字段模板。

The example data is synthetic and does not represent real published papers.

## Project Docs

- [Usage Case: Catalysis Literature Data Extraction](docs/use_case_catalysis_literature_extraction.md)
- [Roadmap](ROADMAP.md)
- [Windows One-click Package Guide](docs/windows_package.md)
- [Windows 一键包说明](docs/windows_package.md)

## Screenshots

The current web interface screenshot and a synthetic Excel/CSV output preview are shown below.

![Web UI](docs/screenshots/web-ui-zh+en.png)

![Synthetic Excel Output Preview](docs/screenshots/excel-output-example.svg)

The output preview uses synthetic data only and does not represent real published papers or real extracted research results.

## Limitations

- LLM extraction results should be reviewed manually.
- Complex scanned PDFs may require OCR or MinerU support.
- The project does not include any built-in commercial API key.
- Example data is synthetic and does not represent real published papers.
- Python 3.11 is recommended for the broadest PDF-backend compatibility.
- On Windows + Python 3.12, `pymupdf4llm` / `pymupdf` may fail during import in some environments. These packages are treated as optional PDF backends; if that happens, use `python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text`.
- `pypdf_text` is more stable as a fallback, but it is weaker for complex tables, two-column layouts, figures, and scanned PDFs.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned maintenance directions, including PDF layout handling, tests, documentation, field templates, and safer review workflows.

## License

MIT License. See `LICENSE`.

<a id="chinese"></a>

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

更多打包结构、安全检查和发布注意事项见 [Windows 一键包说明](docs/windows_package.md)。

源码用户可以运行：

```powershell
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```

默认情况下，程序只会在终端打印本地 Web UI 地址，不会自动打开浏览器。请复制终端显示的地址到浏览器打开。

如果希望自动打开浏览器，可以运行：

```powershell
python ShuJuTiQuJiaoBen.py --open-browser
```

如果 Windows + Python 3.12 环境下 `pymupdf4llm` / `pymupdf` 安装或导入失败，可以使用核心依赖降级路线：

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

## 配置说明

- 仓库不内置真实 API Key。
- 用户可在网页填写 API Key。
- 可保存到 `config.local.json`。
- `config.local.json` 不上传 GitHub。
- `config.example.json` 只是模板。
- 环境变量只是高级用法，不是必须。
- 本地 Ollama 可作为可选模型后端。
- 使用 OpenAI-compatible API 时，需要自行填写 Base URL、模型名称和 API Key。

## 截图

当前网页界面截图和合成 Excel/CSV 输出预览如下。

![网页界面](docs/screenshots/web-ui-zh+en.png)

![合成 Excel 输出预览](docs/screenshots/excel-output-example.svg)

输出预览仅使用合成数据，不代表真实发表论文或真实抽取结果。

## 注意事项

- 不要上传真实论文 PDF。
- 不要上传 API Key、token、密码或 `config.local.json`。
- 大模型提取结果需要人工核验。
- 先用 3-5 篇文献测试，再批量处理。
- 云端 API 可能产生费用。
- 扫描版 PDF 和复杂双栏论文的解析效果取决于 PDF 转换/OCR 工具。
- 示例数据是合成数据，不代表真实发表论文结果。
- 推荐使用 Python 3.11，以获得更好的 PDF 后端兼容性。
- Windows + Python 3.12 环境下，`pymupdf4llm` / `pymupdf` 在部分机器上可能导入失败。它们现在作为可选 PDF 后端处理；如遇导入错误，可使用 `python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text`。
- `pypdf_text` 更稳定，但对复杂表格、双栏排版、图文混排和扫描版 PDF 的解析能力较弱。






