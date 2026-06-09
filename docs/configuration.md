# Configuration

## English

No real API key, token, or password is included in this repository.

Users can enter API keys in the Web UI. The tool may save local configuration to:

```text
config.local.json
```

`config.local.json` is ignored by Git and should remain on the user's computer.

`config.example.json` is only a template:

```json
{
  "llm_service_name": "openai_compatible",
  "api_key": "YOUR_API_KEY_HERE",
  "base_url": "https://api.example.com/v1",
  "model": "provider/model-name",
  "cloud_active": false
}
```

Environment variables are optional for advanced users:

```powershell
$env:CHEM_PDF_EXTRACTOR_API_KEY="YOUR_API_KEY_HERE"
$env:CHEM_PDF_EXTRACTOR_BASE_URL="https://api.example.com/v1"
$env:CHEM_PDF_EXTRACTOR_MODEL="provider/model-name"
```

OpenAI-compatible API providers can be used by setting the Base URL, API key, and model name in the Web UI. Local Ollama models can also be used; start Ollama first, then select the local provider and model.

Python 3.11 is recommended for the broadest PDF-backend compatibility. On some Windows + Python 3.12 environments, `pymupdf4llm` / `pymupdf` may fail during install or import. These packages are optional lazy-loaded PDF backends, so startup does not require importing them.

For full installation:

```powershell
python -m pip install -r requirements.txt
```

For the compatibility fallback:

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

Do not commit real keys, `.env`, `config.local.json`, private PDFs, output files, logs, or caches.

## 中文

本仓库不内置任何真实 API Key、token 或密码。

普通用户可以直接在网页界面填写 API Key。点击保存本地配置后，工具会在本地生成：

```text
config.local.json
```

`config.local.json` 已加入 `.gitignore`，只应保存在用户自己的电脑上，不应上传 GitHub。

`config.example.json` 只是模板，里面只能写占位符：

```json
{
  "llm_service_name": "openai_compatible",
  "api_key": "YOUR_API_KEY_HERE",
  "base_url": "https://api.example.com/v1",
  "model": "provider/model-name",
  "cloud_active": false
}
```

环境变量是高级用法，不是必须：

```powershell
$env:CHEM_PDF_EXTRACTOR_API_KEY="YOUR_API_KEY_HERE"
$env:CHEM_PDF_EXTRACTOR_BASE_URL="https://api.example.com/v1"
$env:CHEM_PDF_EXTRACTOR_MODEL="provider/model-name"
```

使用 OpenAI-compatible API 时，只需要在网页里填写 Base URL、API Key 和模型名称。本地 Ollama 也可以使用；先启动 Ollama，再在网页里选择本地模型。

推荐使用 Python 3.11，以获得更好的 PDF 后端兼容性。Windows + Python 3.12 环境下，`pymupdf4llm` / `pymupdf` 在部分机器上可能安装或导入失败。它们现在作为可选的懒加载 PDF 后端处理，项目启动时不会强制导入。

完整安装：

```powershell
python -m pip install -r requirements.txt
```

兼容降级安装：

```powershell
python -m pip install -r requirements-core.txt
python ShuJuTiQuJiaoBen.py --cli --pdf-mode pypdf_text
```

不要提交真实密钥、`.env`、`config.local.json`、私有 PDF、输出文件、日志或缓存。
