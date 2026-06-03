# Usage Case: Catalysis Literature Data Extraction

## 1. Scenario

This usage case is designed for literature data organization in chemical engineering, catalysis, and materials research. The goal is to extract experimental conditions and reported results from PDF papers into Excel / CSV tables for literature reviews, preliminary dataset construction, and later human verification.

## 2. Problem

Manual literature data organization can be slow and inconsistent because researchers often need to:

- Read PDF papers one by one.
- Manually record fields such as catalysts, reaction temperatures, pressures, conversions, selectivities, products, and related notes.
- Handle missing information, inconsistent wording, and mixed table / paragraph formats.
- Spend significant time checking whether extracted tables are complete and consistent.
- Manually review the organized tables after extraction.

## 3. Input

Typical inputs include:

- A folder containing PDF literature files.
- User-defined extraction field configuration.
- An optional API key for an OpenAI-compatible cloud model or a local Ollama model.
- An optional PDF conversion mode.

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

## 5. Workflow

1. Prepare PDF files.
2. Configure extraction fields.
3. Choose PDF conversion mode.
4. Run extraction.
5. Review Excel / CSV output.
6. Check error logs and bad rows.
7. Manually verify extracted results.

## 6. Output

Expected outputs may include:

- Excel file
- CSV file
- Markdown text cache
- Error log
- Bad-row records
- Suspicious-row records

## 7. Limitations

- AI extraction results must be manually reviewed.
- Scanned PDFs may require OCR or MinerU.
- `pypdf_text` is more stable but weaker for complex tables and two-column layouts.
- The tool is intended for first-pass literature data organization, not final scientific judgment.

## 8. Reproducibility and Safety

- Do not upload copyrighted PDFs to the repository.
- Do not commit API keys or `config.local.json`.
- Use synthetic examples or publicly shareable materials when reporting issues.

## 9. Next Steps

Future extensions may include:

- More field templates.
- Domain knowledge context.
- Better table extraction.
- More examples.
