# Roadmap

Chem-PDF-Extractor is an early-stage open-source tool for extracting structured experimental data from chemical engineering, catalysis, materials, energy, and environmental research PDFs into Excel / CSV tables.

This roadmap focuses on practical improvements for literature review workflows, extraction reliability, documentation, and manual verification support.

## Short term

- Improve PDF parsing stability across different PDF layouts.
- Add more example field templates for catalysis, materials, energy, and environmental engineering papers.
- Improve bad-row and suspicious-row detection.
- Improve error logs so users can more easily identify failed or low-confidence extraction cases.
- Add more usage cases and reproducible examples.
- Maintain synthetic/public-safe benchmark cases and first-pass evaluation notes.
- Keep installation and Windows startup behavior stable.

## Medium term

- Add lightweight domain knowledge context support.
- Improve prompt workflow for scientific extraction tasks.
- Add better guidance for choosing PDF conversion modes.
- Improve table extraction and post-processing for common scientific paper layouts.
- Add more tests for CLI behavior, PDF backend fallback behavior, and output validation.

## Long term

- Explore RAG-style domain knowledge support when it can be added without making the project too complex.
- Explore packaged Windows releases for users who are not familiar with Python environments.
- Explore optional desktop or simplified local UI packaging.
- Explore full PDF source highlighting and page-coordinate anchoring after the
  current optional page/section/table review hints are evaluated.
- Improve support for larger literature batches.
- Encourage external issue reports, field template suggestions, and reproducible bug reports.

## Non-goals

Chem-PDF-Extractor is not intended to:

- Replace expert reading or scientific judgment.
- Guarantee 100% extraction accuracy.
- Automatically produce publication-ready datasets without manual review.
- Store or redistribute copyrighted papers.
- Require users to upload private PDFs or API keys to the repository.

## Contribution areas

Useful contributions include:

- Bug reports with reproducible examples.
- Suggestions for field templates in specific research domains.
- Documentation improvements.
- Tests for PDF backend behavior.
- Examples using synthetic, public-domain, or otherwise shareable materials.

## Review principle

All extracted results should be checked against the original papers before being used in scientific analysis, publication, or model training.
