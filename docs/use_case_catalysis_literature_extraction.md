# Usage Case: Catalysis Literature Data Extraction

## 1. Scenario

This usage case is designed for literature data organization in chemical engineering, catalysis, and materials research. The goal is to extract experimental conditions and reported results from PDF papers into Excel / CSV tables for literature reviews, preliminary dataset construction, and later human verification.

The workflow is intended for researchers who need a structured first pass over a batch of papers. It helps organize recurring fields such as catalyst identity, feedstock, reaction conditions, and reported performance, while still keeping the original papers as the source of truth.

## 2. Problem

Manual literature data organization can be slow and inconsistent because researchers often need to:

- Read PDF papers one by one.
- Manually record fields such as catalysts, reaction temperatures, pressures, conversions, selectivities, products, and related notes.
- Handle missing information, inconsistent wording, and mixed table / paragraph formats.
- Spend significant time checking whether extracted tables are complete and consistent.
- Manually review the organized tables after extraction.

Even after a table has been created, the values still need expert review. The tool is meant to reduce repetitive first-pass table construction, not to replace scientific judgment.

## 3. Input

Typical inputs include:

- A folder containing PDF literature files.
- User-defined extraction field configuration.
- An optional API key for an OpenAI-compatible cloud model or a local Ollama model.
- An optional PDF conversion mode.

The PDF folder can contain a small test batch first. Starting with a few files helps users evaluate whether the selected fields, PDF conversion mode, and model settings are suitable before processing a larger collection.

## Example Folder Layout

```text
literature_batch/
  paper_001.pdf
  paper_002.pdf
  paper_003.pdf

outputs/
  提取结果.xlsx
  错误日志.txt
  坏数据.xlsx
  可疑数据.xlsx
  md文件/
```

These file names are examples only. They do not mean that this repository contains real copyrighted papers or extracted real research results.

## 4. Example Fields

Example extraction fields may include:

- Catalyst
- Feedstock
- Reaction temperature
- Reaction pressure
- Reactor type
- Conversion
- Selectivity
- Product
- Notes

| Field                | Requirement | Notes                                                |
| -------------------- | ----------- | ---------------------------------------------------- |
| Catalyst             | required    | Catalyst name, formula, or sample ID.                |
| Feedstock            | required    | Main reactant or feed composition.                   |
| Reaction temperature | required    | Prefer numeric value and unit.                       |
| Reaction pressure    | recommended | Preserve unit if conversion is uncertain.            |
| Reactor type         | recommended | Fixed-bed, batch reactor, tubular reactor, etc.      |
| Conversion           | required    | Extract reported conversion value.                   |
| Selectivity          | required    | Extract reported selectivity value.                  |
| Product              | recommended | Main product or target compound.                     |
| Notes                | optional    | Important caveats, table number, or source sentence. |

The field list can be adjusted for a specific review topic. For example, a catalyst screening review may emphasize catalyst composition and preparation method, while a reactor comparison review may emphasize reactor type, operating conditions, and product distribution.

## 5. Workflow

1. Prepare PDF files.
2. Configure extraction fields.
3. Choose PDF conversion mode.
4. Run extraction.
5. Review Excel / CSV output.
6. Check error logs and bad rows.
7. Manually verify extracted results.

### CLI example

```bash
python run_chem_pdf_extractor.py --cli --input-dir ./literature_batch --output ./outputs/提取结果.xlsx --pdf-mode pypdf_text
```

- `pypdf_text` is used here as the most compatible fallback mode.
- Users can choose `auto`, `mineru`, `pymupdf4llm`, or `pymupdf_text` when the corresponding backend is available.
- The output path is only an example and can be changed.

### Web UI example

```bash
python run_chem_pdf_extractor.py
```

The program prints a local URL in the terminal. Copy that URL into a browser to open the Web UI.

If users want to open the browser automatically, they can run:

```bash
python run_chem_pdf_extractor.py --open-browser
```

In the Web UI, users can choose the PDF folder, configure extraction fields, select the model provider, choose the PDF conversion mode, and monitor progress from the running log.

## 6. Output

Expected outputs may include:

- Excel file
- CSV file
- Markdown text cache
- Error log
- Bad-row records
- Suspicious-row records

The Markdown cache can help users inspect what the PDF conversion backend produced before the model extraction step. Error logs, bad-row records, and suspicious-row records are useful for deciding which papers require manual follow-up.

Exported review/provenance aid columns include `source_evidence`, `source_hint`, `verification_status`, `review_note`, `page_hint`, `section_hint`, and `table_hint`. The page/section/table hints are optional model-written review aids based on visible converted text such as page markers, headings, captions, or nearby table text. They are not guaranteed full provenance, PDF highlighting, or page-coordinate source anchors, so human verification against the original paper is still required.

## Example Output Table Shape

| Source file   | Catalyst | Feedstock | Reaction temperature | Reaction pressure | Conversion | Selectivity | Product | Notes |
| ------------- | -------- | --------- | -------------------- | ----------------- | ---------- | ----------- | ------- | ----- |
| paper_001.pdf |          |           |                      |                   |            |             |         |       |
| paper_002.pdf |          |           |                      |                   |            |             |         |       |

The empty cells above are intentional. They show the expected table structure without fabricating scientific values.

## 7. Limitations

- AI extraction results must be manually reviewed.
- Scanned PDFs may require OCR or MinerU.
- `pypdf_text` is more stable but weaker for complex tables and two-column layouts.
- The tool is intended for first-pass literature data organization, not final scientific judgment.
- Empty cells do not always mean the paper lacks the information; they may indicate that the model or PDF conversion backend failed to capture it.
- Extracted values should be checked against the original paper before being used in analysis, publication, or model training.
- Different PDF conversion modes may produce different extraction quality.
- Complex tables, scanned pages, two-column layouts, and figure-only information may require additional manual checking.
- Page, section, and table hints are practical review aids only; full PDF source highlighting remains future work.

## 8. Reproducibility and Safety

- Do not upload copyrighted PDFs to the repository.
- Do not commit API keys or `config.local.json`.
- Use synthetic examples or publicly shareable materials when reporting issues.
- When sharing a reproduction case, prefer synthetic PDFs, public-domain papers, or minimal text excerpts that are safe to share.
- Do not upload full copyrighted papers into GitHub issues or pull requests.
- Do not include private API keys, local configuration files, unpublished manuscripts, or confidential industrial data.

## 9. Next Steps

Future extensions may include:

- More field templates.
- Domain knowledge context.
- Better table extraction.
- More examples.

## 10. Why this usage case matters

Many chemical engineering, catalysis, and materials literature reviews require structured comparison of reaction conditions and reported performance. Chem-PDF-Extractor does not replace expert reading, but it can reduce repetitive first-pass table construction work and make manual review more organized.

The main value of this workflow is traceable organization: users can define fields, run extraction, inspect generated tables, review logs, and then verify the results against the original papers before using the data in analysis or writing.
