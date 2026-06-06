# Contributing

Thank you for considering a contribution to Chem-PDF-Extractor.

This project is early-stage and focused on practical literature data extraction for chemical engineering, catalysis, materials, and environmental research.

## Helpful Contributions

We welcome:

- Bug reports.
- Field template suggestions.
- Documentation improvements.
- Synthetic examples that reproduce a problem.
- Permission-safe examples where sharing is allowed.
- Suggestions for safer extraction, validation, and review workflows.

## Safety and Privacy

Do not upload copyrighted papers, private documents, unpublished data, API keys, tokens, passwords, local file paths, or `config.local.json` in issues, pull requests, examples, logs, or screenshots.

When reporting a problem, prefer synthetic PDFs, synthetic examples, or permission-safe excerpts. Remove personal paths, institution names, private project data, and API credentials from logs.

LLM extraction results should be manually reviewed. They should not be treated as final scientific conclusions without human verification.

For related project policies, see:

- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

Pull requests should follow the checklist in `.github/pull_request_template.md`.

## Running Tests

Before opening a pull request, run at least:

```powershell
python -m py_compile ShuJuTiQuJiaoBen.py
python -m unittest discover -s tests -v
```

The tests should not call real cloud APIs and do not require repository secrets.

## Documentation Encoding

Markdown files should be saved as UTF-8 without BOM. Chinese and English content should display correctly on GitHub.

## 中文说明

欢迎提交 bug 报告、字段模板建议、文档改进和安全的复现样例。

提交 issue 或 PR 时，请不要上传真实 API Key、token、私有 PDF、本机绝对路径、`config.local.json`、输出文件、日志中的隐私信息或未授权公开的论文材料。

复现问题时，建议使用合成 PDF、合成数据或确认可以公开分享的样例。大模型抽取结果必须人工核验，不能直接作为最终科研结论。

相关项目规范：

- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

Pull requests should follow the checklist in `.github/pull_request_template.md`.

提交 PR 前至少运行：

```powershell
python -m py_compile ShuJuTiQuJiaoBen.py
python -m unittest discover -s tests -v
```

文档文件请使用 UTF-8 without BOM 保存，并确认中文在 GitHub 页面中正常显示。
