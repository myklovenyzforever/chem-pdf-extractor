# Quick Start

## English

### Route A: full installation

Use this route for normal development and full PDF backend support.

```powershell
git clone https://github.com/myklovenyzforever/chem-pdf-extractor.git
cd chem-pdf-extractor
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```

Open the local URL printed in the terminal, select a PDF folder, configure extraction fields, and start processing.

### Route B: Windows compatibility fallback

If `pymupdf4llm` / `pymupdf` fails to install or import on Windows + Python 3.12, install the core dependencies and use the stable text fallback:

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

`pypdf_text` is more stable, but it is weaker for complex tables, two-column layouts, mixed figure/text pages, and scanned PDFs. Complex scanned PDFs may require OCR or MinerU support.

Start with 3-5 PDFs before large batch processing. AI extraction results must be manually reviewed before scientific use.

Expected output files include:

- `提取结果.xlsx`
- `错误日志.txt`
- `坏数据.xlsx`
- `可疑数据.xlsx`
- `md文件/`
- `抽取缓存/`

## 中文

### 路线 A：完整功能安装

普通源码用户优先使用这条路线，可获得完整 PDF 后端支持。

```powershell
git clone https://github.com/myklovenyzforever/chem-pdf-extractor.git
cd chem-pdf-extractor
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```

终端会显示本地网页地址。打开该地址后，选择 PDF 文件夹、配置抽取字段，然后开始处理。

### 路线 B：Windows 兼容降级

如果 Windows + Python 3.12 环境中 `pymupdf4llm` / `pymupdf` 安装或导入失败，可以只安装核心依赖，并使用更稳定的文本 fallback：

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

`pypdf_text` 更稳定，但对复杂表格、双栏排版、图文混排和扫描版 PDF 的解析能力较弱。复杂扫描版 PDF 可能需要 OCR 或 MinerU 支持。

建议先用 3-5 篇 PDF 测试，再处理大批量文献。AI 抽取结果必须人工核验，不能直接作为最终科研结论。

常见输出文件包括：

- `提取结果.xlsx`
- `错误日志.txt`
- `坏数据.xlsx`
- `可疑数据.xlsx`
- `md文件/`
- `抽取缓存/`
