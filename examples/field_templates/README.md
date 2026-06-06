# Field Templates

## Purpose

These JSON files provide starting field sets for common chemical literature extraction workflows. They are meant to help users quickly choose and adapt configurable extraction fields without reading the source code.

These templates are not official reporting standards. They contain field definitions only, not extracted research results. Users should adapt the fields to their own literature review task, run a small test batch first, and manually verify extracted values against the original paper.

## Available templates

- `catalysis_reaction.json`: fields for catalysis reactions, thermal catalysis, fixed-bed tests, batch reactions, and gas-solid reaction studies.
- `materials_synthesis.json`: fields for materials synthesis, adsorbents, catalyst preparation, composite materials, oxides, carbon materials, MOFs, zeolites, and related workflows.
- `environmental_treatment.json`: fields for water treatment, pollutant removal, adsorption, photocatalysis, oxidation/reduction, membrane separation, and environmental remediation.
- `electrochemistry.json`: fields for electrochemical energy systems, electrocatalysis, batteries, supercapacitors, water splitting, oxygen reactions, carbon dioxide reduction, cyclic voltammetry, and charge/discharge tests.

## How to use

1. Open one JSON file.
2. Copy or load the fields into Chem-PDF-Extractor.
3. Remove fields that are not needed.
4. Add task-specific fields.
5. Run a small test batch first.
6. Manually verify extracted values.

## Safety and limitations

- Templates contain field definitions only, not extracted research results.
- Do not upload copyrighted papers, private PDFs, API keys, `config.local.json`, logs, or confidential outputs to public issues or pull requests.
- These templates do not guarantee extraction accuracy.
- Units and field meanings should be checked against the original paper.
- Manual verification is required before scientific use.

## 中文说明

这些模板只提供字段配置起点，不代表官方标准，也不包含真实论文数据。使用时请根据自己的文献综述任务删改字段，并对大模型抽取结果进行人工核验。不要在公开 issue 或 PR 中上传私有 PDF、API Key、日志、`config.local.json` 或保密输出文件。
