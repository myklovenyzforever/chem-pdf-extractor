# Project Status and Maintainer Roadmap

Chem-PDF-Extractor is an early-stage, local-first tool for chemistry and chemical engineering PDF extraction. It is intended for first-pass literature review and dataset preparation workflows, not automated scientific correctness. Every extracted row should be checked by a human against the source PDF before use in analysis, publication, or model training.

## Current Status

The project is strongest where the workflow is explicit, inspectable, and easy to reproduce:

- Local Web UI and CLI workflows for PDF-to-text conversion, field configuration, extraction, and Excel/CSV export.
- Local Ollama workflow for users who want prompts and PDF text to stay on their own machine.
- Optional cloud-provider workflow for users who intentionally configure an external model endpoint.
- Tests covering core extraction flow, output safety, UI layout contracts, PDF mode behavior, cloud configuration validation, packaging metadata, and documentation links.
- Documentation for configuration, evaluation notes, benchmark cases, field templates, UI layout, Windows packaging, and release/feedback handling.
- Synthetic/public-safe benchmark examples and demo fixtures.
- Field templates for common chemistry and chemical engineering extraction workflows.
- Release checklist and feedback path for maintainers and users.

Known limitations remain:

- OCR and parser quality vary across scanned PDFs, two-column layouts, tables, figures, and supplementary materials.
- Model output varies by provider, model, prompt, PDF conversion backend, and input length.
- The benchmark set is useful as a first pass, but it is still small and synthetic/public-safe.
- Review/provenance hints help manual checking, but they are not full PDF highlighting or page-coordinate anchoring.
- Maintenance capacity is limited by a single maintainer, so broad feature requests may be deferred.

## Community Evidence

This repository should not claim broad adoption unless that evidence exists. Current project maturity is better represented by repository-visible signals:

- Unit and workflow tests.
- Safety and configuration documentation.
- Synthetic benchmark examples.
- Field template documentation.
- Issue and feedback guidance.
- Release checklist.
- Contribution guidance.

Broader adoption evidence should be added only when it exists and can be verified without exposing private data.

## Single-Maintainer Expectations

The project is maintained with limited review bandwidth. Contributions are most useful when they are small, focused, and easy to verify.

Good issues and pull requests should:

- Include minimal synthetic or public-safe reproductions.
- Avoid private PDFs, copyrighted paper text, API keys, private config, and private local paths.
- State the operating system, install method, PDF mode, provider type, and field template or `fields.json` shape when relevant.
- Keep changes aligned with local-first, privacy-conscious, human-verifiable extraction.
- Add or update tests when behavior, documentation contracts, or exported outputs change.

Maintainers may defer broad feature requests, large rewrites, or changes that reduce manual verifiability. Maintenance decisions are guided by safer local workflows, clear review artifacts, and reproducible tests.

## Issue #7 And RAG-Like Work

Issue #7 and RAG-like ideas remain future exploration. RAG is not current functionality in this project, and no accuracy improvement should be claimed before evaluation.

Possible future directions include:

- Retrieval-assisted chunk selection for long PDFs.
- Local-first indexing that avoids sending private documents to external services by default.
- Evidence linking that helps reviewers find source passages more quickly.
- Table-aware and section-aware retrieval for methods, results, captions, and supplementary text.
- Benchmark-driven evaluation before enabling any user-facing RAG feature.

No timeline is promised. Reliability, evaluation evidence, provenance hints, and packaging safety remain higher priority than adding new retrieval features.
