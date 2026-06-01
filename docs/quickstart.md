# Quick Start

## English

1. Clone the repository.

```powershell
git clone https://github.com/myklovenyzforever/chem-pdf-extractor.git
cd chem-pdf-extractor
```

2. Install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

3. Configure an API key using the web interface or `config.local.json`.

4. Run the program.

```powershell
python ShuJuTiQuJiaoBen.py
```

5. Open the local web URL printed in the terminal.

6. Select the PDF folder.

7. Configure extraction fields.

8. Start processing.

9. Check output files such as `提取结果.xlsx`, `错误日志.txt`, `坏数据.xlsx`, and `可疑数据.xlsx`.

For non-programming users, a bundled Windows one-click package may be provided through GitHub Releases.

Start with 3-5 PDFs before large batch processing.

# 快速开始

## 中文

1. 下载或解压工具。

2. 将 PDF 文献放入一个单独文件夹。

3. 如果使用一键运行包，双击：

```text
YiJianQiDong.bat
```

4. 打开黑色窗口显示的网址。

5. 在网页里填写 API Key。也可以保存到本地 `config.local.json`。

6. 配置抽取字段，例如工艺名称、原料、催化剂、温度、压力、转化率、选择性等。

7. 点击开始处理。

8. 查看输出文件：

- `提取结果.xlsx`
- `错误日志.txt`
- `坏数据.xlsx`
- `可疑数据.xlsx`
- `md文件/`
- `抽取缓存/`

建议先用 3-5 篇文献测试，再批量处理大量 PDF。
