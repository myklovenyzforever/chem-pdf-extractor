# Codex for Open Source Application Draft

## Project

- Repository: https://github.com/myklovenyzforever/chem-pdf-extractor
- Project name: Chem-PDF-Extractor
- License: MIT
- Primary maintainer: myklovenyzforever
- Current release: v0.1.2

Chem-PDF-Extractor is an early-stage but actively maintained open-source tool for extracting structured experimental data from chemical engineering, catalysis, materials, energy, and environmental research PDFs into Excel/CSV tables. It supports literature review, preliminary dataset construction, and manual verification workflows.

AI/LLM extraction results require manual review. The project does not include built-in commercial API keys. The repository avoids private PDFs, copyrighted papers, private logs, and real confidential outputs. Synthetic examples are used for demonstration and testing. The project is early-stage and should not be described as widely adopted.

## 1. Describe your role: are you a primary or core maintainer?

I am the original author and primary maintainer of Chem-PDF-Extractor.

I maintain the following areas of the project:

- PDF-to-text / Markdown conversion workflow;
- configurable extraction fields;
- LLM-based extraction workflow;
- Excel/CSV output workflow;
- Windows launcher and Windows packaging guidance;
- examples and synthetic demos;
- documentation;
- issue templates and contribution guidance;
- tests and GitHub Actions CI;
- release preparation.

## 2. What does this repository do?

Chem-PDF-Extractor helps users convert chemistry-related research PDFs into structured Excel/CSV tables for literature review and preliminary dataset construction.

The project is focused on workflows in:

- chemical engineering;
- catalysis;
- materials;
- energy;
- environmental research.

The repository currently supports:

- batch PDF processing;
- PDF to Markdown/text conversion;
- configurable extraction fields;
- multiple records from one paper as multiple rows;
- Excel/CSV export;
- low-fill bad row filtering;
- error logs;
- suspicious-data and bad-data records;
- cache reuse / resumable workflow;
- OpenAI-compatible API support;
- local Ollama support;
- Windows local workflow support.

The tool is intended for first-pass structured extraction and manual verification, not for fully automated scientific conclusions.

## 3. Why does this repository qualify?

### Public and open-source

- The project is maintained in a public GitHub repository.
- The repository is MIT-licensed.
- The project does not include built-in commercial API keys.
- Configuration is handled through user-provided local settings.

### Active maintenance evidence

Recent maintenance work has focused on making the repository clearer, safer, more reproducible, and easier to evaluate:

- README positioning was improved to clearly explain the project scope.
- A catalysis literature extraction usage case was added.
- A ROADMAP was added for short-term, medium-term, and long-term maintenance directions.
- A synthetic Excel/CSV output preview was added.
- Governance files were added: `SECURITY.md`, `CODE_OF_CONDUCT.md`, and a pull request template.
- GitHub Actions CI was expanded to include Ubuntu and Windows test jobs.
- A complete synthetic literature batch demo was added.
- Reusable field templates were added for catalysis, materials synthesis, environmental treatment, and electrochemistry.
- A Windows one-click package guide was added.
- README roadmap content was streamlined to point to `ROADMAP.md`.

Recent merged maintenance PRs include documentation, CI, examples, governance, and field-template improvements.

### Reproducibility and safety

- The project includes synthetic examples rather than copyrighted or private papers.
- The synthetic demo includes input PDFs, field configuration, expected CSV/XLSX output shape, and offline tests.
- Field templates contain field definitions only, not real research results.
- Security guidance warns against uploading API keys, private PDFs, `config.local.json`, logs, caches, and confidential outputs.
- The PR template includes checklist items to reduce accidental sensitive-data commits.

### CI and tests

- GitHub Actions runs a small matrix across Ubuntu and Windows.
- The CI matrix includes:
  - Ubuntu Python 3.11 with full dependencies;
  - Windows Python 3.11 with full dependencies;
  - Windows Python 3.12 with core dependencies.
- Tests are offline and do not require real API keys.
- The current local test count is 20.

## 4. How will you use API credits for your project?

I would use API credits to support open-source maintenance tasks that are hard to test with only local resources, including:

- improving extraction prompts for chemistry-related literature;
- comparing prompt behavior across different OpenAI-compatible model configurations;
- testing diverse PDF layout cases using permission-safe or synthetic examples;
- building regression examples for common extraction failures;
- expanding field templates for chemical engineering, catalysis, materials, energy, and environmental workflows;
- improving issue triage by reproducing user-reported extraction problems with sanitized examples;
- validating documentation examples without requiring contributors to use their own paid API credits;
- improving safer review workflows that remind users to verify AI outputs manually.

API credits would not be embedded into the repository or distributed to users as built-in keys.

The project will continue to support user-provided API keys and local Ollama workflows.

## 5. Impact and users

This project is intended for students, researchers, and engineers who need a local, inspectable workflow for first-pass literature data extraction in chemistry-related fields.

Potential workflows include:

- literature review table construction;
- preliminary dataset preparation;
- extracting experimental conditions and results for manual review;
- comparing catalysts, materials, reaction conditions, or environmental treatment results;
- preparing structured tables before deeper expert validation.

The project is early-stage and does not claim broad adoption yet.

The current value is in reducing repetitive first-pass organization work while keeping the final scientific judgment with the human user.

## 6. Safety, privacy, and responsible use

Users may process private PDFs, unpublished manuscripts, local logs, API keys, and confidential industrial or research data. The repository therefore includes security and contribution guidance.

Users are told not to upload private PDFs, API keys, `config.local.json`, logs, outputs, caches, or confidential data to public issues or pull requests.

Synthetic examples are preferred for bug reports and demos.

LLM extraction results must be manually checked against original papers. The project does not guarantee extraction accuracy.

## 7. Current evidence links

- README: https://github.com/myklovenyzforever/chem-pdf-extractor
- Roadmap: [ROADMAP.md](../ROADMAP.md)
- Contributing: [CONTRIBUTING.md](../CONTRIBUTING.md)
- Security Policy: [SECURITY.md](../SECURITY.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- Usage Case: [docs/use_case_catalysis_literature_extraction.md](use_case_catalysis_literature_extraction.md)
- Synthetic demo: [examples/demo_literature_batch/](../examples/demo_literature_batch/)
- Field templates: [examples/field_templates/](../examples/field_templates/)
- Windows package guide: [docs/windows_package.md](windows_package.md)
- GitHub Actions workflow: [.github/workflows/tests.yml](../.github/workflows/tests.yml)
- PR template: [.github/pull_request_template.md](../.github/pull_request_template.md)

## 8. Short version for application form

I am the original author and primary maintainer of Chem-PDF-Extractor, an MIT-licensed open-source tool for extracting structured experimental data from chemical engineering, catalysis, materials, energy, and environmental research PDFs into Excel/CSV tables. The project is designed for literature reviews, preliminary dataset construction, and manual verification workflows.

The repository is early-stage but actively maintained. Recent work includes clearer README positioning, a catalysis usage case, a roadmap, governance and security files, a Windows CI matrix, a synthetic literature batch demo, reusable field templates, a synthetic Excel/CSV output preview, and Windows package safety guidance. The test suite is offline and the CI matrix covers Ubuntu and Windows environments.

I would use API credits to improve extraction prompts, test diverse PDF layouts with synthetic or permission-safe examples, expand chemistry-oriented field templates, build regression examples, and improve issue triage and documentation. API credits would not be embedded in the repository or distributed as built-in user keys.

The project does not claim fully automated or publication-ready extraction. LLM outputs require manual verification against the original papers. The repository avoids real private PDFs, API keys, confidential outputs, and copyrighted paper content in examples and tests.
