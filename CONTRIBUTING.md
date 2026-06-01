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

Do not upload copyrighted papers, private documents, unpublished data, API keys, tokens, passwords, or `config.local.json` in issues, pull requests, examples, or screenshots.

When reporting a problem, prefer synthetic examples or permission-safe excerpts. Remove personal paths, institution names, private project data, and API credentials from logs.

LLM extraction results should be manually reviewed. They should not be treated as final scientific conclusions without human verification.

## Running Tests

Run the lightweight local test suite:

```powershell
python -m unittest discover -s tests -v
```

You can also check syntax:

```powershell
python -m py_compile ShuJuTiQuJiaoBen.py
```

The tests should not call real cloud APIs and do not require repository secrets.

# 贡献说明

欢迎提交 bug 报告、字段模板建议和文档改进。

请不要在 issue、PR、示例文件或截图中上传受版权保护的论文 PDF、真实 API Key、token、密码、`config.local.json` 或私有数据。

复现问题时，建议使用合成示例或确认可以公开分享的材料。大模型抽取结果需要人工核验，不能直接作为最终科研结论。
