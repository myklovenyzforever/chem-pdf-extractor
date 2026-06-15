# Release and Feedback Path

This page gives maintainers a small release checklist and gives users a safe way to report issues. Chem-PDF-Extractor is an early-stage, first-pass extraction tool. Results still require human verification against the source PDF.

## Maintainer Release Checklist

Before preparing a release or release candidate:

- Confirm the working tree is clean.
- Run the unit test suite: `python -m unittest discover -s tests -v`.
- Run CLI help: `python -m chem_pdf_extractor --help`.
- Run the packaging and wheel check when packaging changes are part of the release.
- Check documentation links.
- Check that no generated artifacts are staged, including `dist/`, `build/`, `.egg-info/`, caches, logs, PDFs, Excel/CSV outputs, or temporary files.
- Check that no private config, API keys, tokens, passwords, or private local paths are included.
- Summarize user-visible changes in the release notes.
- Note limitations honestly, especially around PDF parsing, LLM extraction quality, optional cloud configuration, and the need for human review.

## User Feedback Paths

Useful feedback areas include:

- Extraction quality issues.
- Incorrect or missing fields.
- Field template suggestions.
- PDF mode or parser problems.
- Local Ollama setup issues.
- Optional cloud provider configuration issues.
- Packaging or Windows install issues.
- Documentation gaps.

## What To Include In A Good Report

When possible, include:

- Operating system and version.
- Install method, such as source checkout, wheel, or Windows package.
- Command or Web UI workflow used.
- PDF mode, such as `pymupdf4llm`, `pypdf_text`, `auto`, or optional `mineru`.
- Provider type, such as local Ollama or optional cloud provider, without API keys.
- Field template name or a short `fields.json` shape.
- Expected result and actual result.
- A minimal synthetic or public-safe reproduction when possible.

## Safety Guidance

When opening an issue, discussion, or pull request:

- Do not upload private PDFs.
- Do not paste API keys, tokens, passwords, or secrets.
- Do not paste copyrighted paper text.
- Do not paste confidential user, project, laboratory, institution, or customer data.
- Redact private local paths, user names, and machine-specific directories.
- Avoid pasting full cloud responses; share a short redacted error summary instead.
- Prefer synthetic examples, public-safe examples, or clearly shareable snippets.

## Feedback Triage

Maintainers can classify reports as:

- Bug.
- Docs.
- Extraction quality.
- Template suggestion.
- Packaging/install.
- Security/privacy concern.

For security or privacy concerns, avoid posting secrets or private data in public threads. Use the project security policy when a report could expose credentials, private documents, or sensitive data.
