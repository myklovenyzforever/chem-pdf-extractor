# Evaluation

This document describes the current evaluation approach for Chem-PDF-Extractor.
It is a first-pass, human-verifiable extraction evaluation for literature review
workflows. It does not claim production scientific accuracy, final curation
quality, or correctness without expert review.

All benchmark material in this repository must be synthetic or public-safe. Do
not add private PDFs, copyrighted paper text, real API keys, local private paths,
or generated outputs from real papers.

## Current Benchmark Scope

The initial benchmark cases live in `examples/benchmark_cases/`. They are small
synthetic Markdown/text-style inputs with matching field definitions and golden
CSV rows. The goal is to validate reproducible workflow behavior and output
shape, not to prove broad model accuracy.

The first case set covers:

- Catalysis reaction conditions.
- Materials synthesis.
- Environmental treatment.
- Electrochemistry.

## Benchmark Metrics

Each evaluation run should record these fields:

- `case_id`: stable case directory or identifier.
- `domain`: chemistry or chemical engineering area.
- `input_type`: synthetic PDF, synthetic Markdown, synthetic text, or
  public-safe text.
- `field_template`: field schema or template used for extraction.
- `golden_output_rows`: expected rows from the benchmark case.
- `observed_output_rows`: rows produced by the extractor.
- `field_level_exact_match`: exact field/value match rate after normalization.
- `missing_field_rate`: expected non-empty fields that were empty in output.
- `hallucinated_field_rate`: output fields with values unsupported by the case
  input or golden row.
- `bad_row_count` and `bad_row_rate`: rows removed by the bad-data filter.
- `suspicious_row_count` and `suspicious_row_rate`: rows flagged for manual
  review.
- `pdf_backend_used`: PDF conversion backend used, such as `pypdf_text`,
  `pymupdf4llm`, `pymupdf_text`, `mineru`, or mocked conversion.
- `page_hint`, `section_hint`, and `table_hint`: optional review aids from
  visible page markers, headings, captions, or table text when available. They
  are not full provenance, PDF highlighting, or page-coordinate anchors.
- `notes_limitations`: notes about synthetic scope, known ambiguity, and manual
  review needs.

## PDF Backend Comparison Hook

Auto-mode backend evaluation should use only synthetic or public-safe cases and
record:

| Column | Meaning |
| --- | --- |
| `case_id` | Stable benchmark case identifier. |
| `backend` | `pypdf_text`, `pymupdf4llm`, `pymupdf_text`, `mineru`, `auto`, or mocked conversion. |
| `markdown_chars` | Character count in converted Markdown/text before extraction truncation. |
| `table_line_count` | Count of Markdown-style table lines or equivalent table markers. |
| `extracted_rows` | Number of rows produced by the extraction step. |
| `field_match_rate` | Field-level exact-match rate against the golden row after normalization. |
| `notes` | Backend limitations, fallback behavior, and manual-review notes. |

Current `auto` mode is intentionally heuristic-based. It tries `pymupdf4llm`
first, may try optional MinerU when the initial Markdown is short, has repeated
table mentions without table-like rows, or appears image-heavy, and falls back to
usable `pymupdf4llm` text or `pypdf_text` if MinerU is unavailable. CI should not
require MinerU; tests cover the heuristic path with mocks.

## How To Reproduce

The repository currently uses mock tests for reproducibility. These tests avoid
network access, real cloud APIs, Ollama, MinerU, and private files.

Run:

```bash
python -m unittest tests.test_benchmark_cases -v
python -m unittest tests.test_e2e_mock_workflow -v
python -m unittest discover -s tests -v
```

`tests/test_benchmark_cases.py` validates the benchmark fixture structure and
safety constraints. `tests/test_e2e_mock_workflow.py` runs a synthetic mocked
workflow through `run_extraction_job`, verifies partial JSONL and Excel output,
checks bad/suspicious row artifacts, and confirms reruns skip already processed
PDFs.

## Interpreting Results

Benchmark output is useful for regression checks and workflow confidence. It is
not a substitute for reading the original paper. Extracted rows and optional
page/section/table hints should be reviewed against source evidence before
scientific analysis, publication, or model training.

The initial benchmark is intentionally small. It should be treated as a smoke
test and fixture contract, not as a statistical performance claim.

## Next Evaluation Work

- Add more public-safe cases across domains and document the case source type.
- Fill backend comparison reports across `pypdf_text`, `pymupdf4llm`,
  `pymupdf_text`, and optional MinerU where available.
- Add model comparison for OpenAI-compatible providers and local Ollama models
  using the same synthetic/public-safe cases.
- Add stronger provenance/page/table hint evaluation against human-checked
  synthetic or public-safe cases.
- Add malformed output repair/retry evaluation after the current structured
  output validation path has more public-safe coverage.
- Expand from smoke tests to a larger public-safe benchmark set before making
  any accuracy claims.
