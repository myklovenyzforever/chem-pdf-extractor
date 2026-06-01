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
- Reuse of `md鏂囦欢/` and `鎶藉彇缂撳瓨/`.
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

# 涓枃璇存槑

## 椤圭洰绠€浠?
Chem-PDF-Extractor 闈㈠悜鍖栧伐銆佹潗鏂欍€佸偓鍖栥€佺幆澧冪瓑鏂瑰悜鐮旂┒鐢熷拰绉戠爺浜哄憳锛岀敤浜庢壒閲忓鐞?PDF 鏂囩尞锛屽苟灏嗗疄楠屾潯浠躲€佸偓鍖栧墏銆佸師鏂欍€佹俯搴︺€佸帇鍔涖€佽浆鍖栫巼銆侀€夋嫨鎬х瓑淇℃伅鎻愬彇涓?Excel/CSV 琛ㄦ牸銆?
鏈伐鍏烽€傚悎鍋氭枃鐚患杩般€佸疄楠屾暟鎹暣鐞嗐€佺鐮旀暟鎹寲鎺樼殑鍒濇缁撴瀯鍖栧鐞嗐€傚ぇ妯″瀷杈撳嚭缁撴灉闇€瑕佷汉宸ユ牳楠岋紝涓嶈兘鐩存帴浣滀负鏈€缁堢鐮旂粨璁恒€?
## 鏍稿績鍔熻兘

- 鎵归噺澶勭悊 PDF 鏂囩尞銆?- PDF 杞?Markdown / 鏂囨湰銆?- 浣跨敤 OpenAI-compatible API 鎴栨湰鍦?Ollama 妯″瀷鎶藉彇瀛楁銆?- 鏀寔鐢ㄦ埛鑷畾涔夋娊鍙栧瓧娈点€?- 涓€绡囨枃鐚鏉℃暟鎹啓鎴愬琛屻€?- 瀵煎嚭 Excel / CSV銆?- 鑷姩杩囨护浣庡～鍐欑巼鍧忔暟鎹€?- 鐢熸垚閿欒鏃ュ織銆佸潖鏁版嵁銆佸彲鐤戞暟鎹€?- 鏀寔鏆傚仠銆佺户缁€佸仠姝㈠拰鏂偣缁窇銆?- 鏀寔澶嶇敤 `md鏂囦欢/` 鍜?`鎶藉彇缂撳瓨/`銆?
## 蹇€熷紑濮?
鏅€氱敤鎴峰彲浠ヤ娇鐢ㄥ甫 `YiLaiHuanJing/` 鐨勪竴閿繍琛屽寘锛?
1. 瑙ｅ帇宸ュ叿鍖呫€?2. 鍙屽嚮 `YiJianQiDong.bat`銆?3. 鎵撳紑榛戣壊绐楀彛鏄剧ず鐨勭綉鍧€銆?4. 鍦ㄧ綉椤甸噷濉啓 API Key銆?5. 閫夋嫨 PDF 鏂囦欢澶广€?6. 閰嶇疆鎶藉彇瀛楁銆?7. 鐐瑰嚮寮€濮嬪鐞嗐€?8. 鏌ョ湅 `鎻愬彇缁撴灉.xlsx`銆乣閿欒鏃ュ織.txt`銆乣鍧忔暟鎹?xlsx`銆乣鍙枒鏁版嵁.xlsx`銆?
婧愮爜鐢ㄦ埛鍙互杩愯锛?
```powershell
python -m pip install -r requirements.txt
python ShuJuTiQuJiaoBen.py
```

## 閰嶇疆璇存槑

- 浠撳簱涓嶅唴缃湡瀹?API Key銆?- 鐢ㄦ埛鍙湪缃戦〉濉啓 API Key銆?- 鍙繚瀛樺埌 `config.local.json`銆?- `config.local.json` 涓嶄笂浼?GitHub銆?- `config.example.json` 鍙槸妯℃澘銆?- 鐜鍙橀噺鍙槸楂樼骇鐢ㄦ硶锛屼笉鏄繀椤汇€?
## 娉ㄦ剰浜嬮」

- 涓嶈涓婁紶鐪熷疄璁烘枃 PDF銆?- 涓嶈涓婁紶 API Key銆乼oken銆佸瘑鐮佹垨 `config.local.json`銆?- 澶фā鍨嬫彁鍙栫粨鏋滈渶瑕佷汉宸ユ牳楠屻€?- 鍏堢敤 3-5 绡囨枃鐚祴璇曪紝鍐嶆壒閲忓鐞嗐€?- 浜戠 API 鍙兘浜х敓璐圭敤銆?
