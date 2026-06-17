# AGENTS.md

## Project Overview

Chem-PDF-Extractor is a local-first, human-verifiable PDF extraction tool for chemistry and chemical engineering literature review workflows. Extraction results are first-pass outputs and must be checked against source PDFs before scientific use.

The project supports local Ollama and optional OpenAI-compatible cloud APIs. Cloud usage is opt-in and requires user-provided API configuration.

## Required Validation

Run these commands when relevant:

```powershell
python -m unittest discover -s tests -v
python -m chem_pdf_extractor --help
git diff --check
```

Targeted tests are acceptable during iteration. Run the full test suite before a PR that changes behavior, documentation contracts, packaging, CLI, Web UI, security-sensitive code, or exported output shape.

## Safety And Privacy

- Do not commit `release_artifacts/`, `dist/`, `build/`, `.egg-info/`, caches, logs, generated Excel/CSV outputs, generated PDFs, `.runtime/`, `.venv/`, or local package artifacts.
- Do not add real API keys, tokens, passwords, private PDFs, copyrighted paper text, private local paths, unpublished data, or confidential output files.
- Do not commit `config.local.json`.
- Use synthetic or public-safe fixtures only.
- Keep Cloud API keys local-only.
- Never expose full keys through docs, tests, logs, screenshots, or UI payload examples.
- Keep the Web UI local-loopback safety model.

## Contribution Style

- Prefer small focused PRs.
- Update tests when behavior, documentation contracts, packaging, CLI, Web UI layout, security behavior, or exported output shape changes.
- Keep Windows packaging and user-root behavior safe.
- Do not commit built release packages.
- Keep documentation honest.
- Do not claim broad adoption, production scientific accuracy, OCR guarantees, provenance guarantees, or benchmark strength unless supported by repository-visible evidence.
