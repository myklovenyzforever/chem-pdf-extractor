# Configuration

## English

No real API key is included in this repository.

Users can enter API keys in the web interface. The tool may save local configuration to:

```text
config.local.json
```

`config.local.json` is ignored by Git and should remain on the user's computer.

`config.example.json` is only a template:

```json
{
  "llm_service_name": "silicon",
  "api_key": "YOUR_API_KEY_HERE",
  "base_url": "https://api.example.com/v1",
  "model": "provider/model-name",
  "cloud_active": true
}
```

Environment variables are optional for advanced users, not required:

```powershell
$env:CHEM_PDF_EXTRACTOR_API_KEY="YOUR_API_KEY_HERE"
$env:CHEM_PDF_EXTRACTOR_BASE_URL="https://api.example.com/v1"
$env:CHEM_PDF_EXTRACTOR_MODEL="provider/model-name"
```

OpenAI-compatible API providers can be used by setting the Base URL, API key, and model name in the web page.

Local Ollama models can also be used. Start Ollama first, then select the local provider and model in the web interface.

Do not commit real keys, `.env`, `config.local.json`, or private PDF files.

# 配置说明

## 中文

本仓库不内置任何真实 API Key、token 或密码。

普通用户可以直接在网页界面填写 API Key。点击“保存本地配置”后，工具会在本地生成：

```text
config.local.json
```

`config.local.json` 已加入 `.gitignore`，只应保存在用户自己的电脑上，不应上传 GitHub。

`config.example.json` 只是模板，里面只能写占位符：

```json
{
  "llm_service_name": "silicon",
  "api_key": "YOUR_API_KEY_HERE",
  "base_url": "https://api.example.com/v1",
  "model": "provider/model-name",
  "cloud_active": true
}
```

环境变量是高级用法，不是必须：

```powershell
$env:CHEM_PDF_EXTRACTOR_API_KEY="YOUR_API_KEY_HERE"
$env:CHEM_PDF_EXTRACTOR_BASE_URL="https://api.example.com/v1"
$env:CHEM_PDF_EXTRACTOR_MODEL="provider/model-name"
```

OpenAI-compatible API 服务只需要在网页里填写 Base URL、API Key 和模型名称。

本地 Ollama 也可以使用。先启动 Ollama，再在网页里选择本地模型。

不要提交真实密钥、`.env`、`config.local.json` 或私有论文 PDF。
