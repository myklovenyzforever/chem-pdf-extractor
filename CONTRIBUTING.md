# Contributing to Chem-PDF-Extractor

Thank you for considering a contribution. This project is practical and early-stage, so privacy, safety, and manual scientific verification matter more than broad claims.

## Project Scope

Chem-PDF-Extractor is for local-first, human-verifiable scientific PDF extraction. It supports first-pass literature review and dataset preparation, but it is not a guarantee of scientific correctness. Extracted rows must be checked against source PDFs before scientific use.

## Good Contribution Types

- Bug fixes.
- Windows packaging or installation fixes.
- Web UI clarity improvements.
- CLI usability improvements.
- Field templates.
- Synthetic or public-safe benchmark cases.
- Documentation improvements.
- Security and privacy hardening.
- Test coverage improvements.

## Before Opening An Issue

Search existing issues first. When reporting a problem, include:

- Operating system.
- Install method: source checkout, wheel, or Windows package.
- PDF mode.
- Provider type: local Ollama or optional cloud provider.
- Field template or `fields.json` shape when relevant.
- Expected result and actual result.
- A minimal synthetic or public-safe reproduction when possible.

Never include API keys, tokens, passwords, private PDFs, copyrighted paper text, private logs, local absolute paths, unpublished data, or confidential outputs.

## Pull Request Expectations

- Keep PRs small and focused.
- Explain user-visible changes.
- Add or update tests when behavior or documentation contracts change.
- Do not commit generated artifacts or local configs.
- Do not commit `release_artifacts/`, `dist/`, `build/`, `.egg-info/`, caches, logs, generated Excel/CSV files, generated PDFs, `.runtime/`, `.venv/`, or `config.local.json`.

Run these before final review:

```powershell
python -m unittest discover -s tests -v
python -m chem_pdf_extractor --help
git diff --check
```

## Field Template Contributions

Prefer field names, descriptions, required/recommended/optional flags, and synthetic examples. Explain the research domain, why the fields matter, common extraction difficulties, and the expected output shape.

Do not paste full copyrighted paper text. Use public-safe or synthetic examples only.

For field template suggestions, use issue #11 or the field-template suggestion workflow described in [examples/field_templates/README.md](examples/field_templates/README.md).

## Security And Privacy

See [SECURITY.md](SECURITY.md) for security and privacy reporting guidance. Do not post sensitive details publicly.

Redact secrets, private paths, private PDFs, unpublished data, confidential outputs, and full cloud responses before sharing logs, screenshots, examples, or issue reports.

## Release Artifacts

`release_artifacts/` is for local release building only and must remain untracked. GitHub Releases may contain built packages, but the repository should not commit built packages or local runtime artifacts.

## Related Docs

- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Release and Feedback Path](docs/release_and_feedback.md)
- [Project Status and Maintainer Roadmap](docs/project_status_and_roadmap.md)
