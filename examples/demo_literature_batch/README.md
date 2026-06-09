# Synthetic Literature Batch Demo

## Purpose

This demo shows a minimal literature-extraction workflow:

input PDFs -> field configuration -> expected Excel/CSV output shape.

It uses synthetic content only. The PDFs are not real papers, the values are not real experimental results, and the demo is intended to show the workflow shape rather than validate extraction accuracy. LLM extraction results must always be manually reviewed.

## Files

- `input_pdfs/`: two small synthetic PDF notes for demonstration.
- `fields.json`: example extraction field configuration.
- `expected_output.csv`: reference CSV table shape.
- `expected_output.xlsx`: reference Excel table shape.

## How to run with the Web UI

1. Start the application from the repository root:

   ```powershell
   python run_chem_pdf_extractor.py
   ```

2. Open the local Web UI URL printed in the terminal.
3. Select this input folder:

   ```text
   examples/demo_literature_batch/input_pdfs
   ```

4. Load or copy the fields from:

   ```text
   examples/demo_literature_batch/fields.json
   ```

5. Start a small extraction run.
6. Compare the generated output shape with:

   ```text
   examples/demo_literature_batch/expected_output.csv
   ```

Different models may not produce exactly identical wording. `expected_output.csv` is a structure reference and expected table shape, not a guarantee of byte-for-byte model output. Real papers require manual verification against the original source.

## How to run with CLI

The current CLI workflow may still require interactive configuration depending on your setup. Use the Web UI workflow above for the most reliable demo path.

## Expected output shape

| source_file | catalyst | feedstock | reaction_temperature | reaction_pressure | conversion | selectivity | main_product | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic_catalysis_note_001.pdf | Catalyst A | Feedstock A | 350 C | 1 atm | 85% | 92% | Product A | Synthetic demo row only |
| synthetic_catalysis_note_002.pdf | Catalyst B | Feedstock B | 420 C | 2 MPa | 78% | 88% | Product B | Synthetic demo row only |

## Safety notes

- Do not upload copyrighted papers to public issues.
- Do not commit private PDFs, API keys, `config.local.json`, logs, or confidential outputs.
- Use synthetic or permission-safe examples when reporting problems.

## 中文说明

这个 demo 只使用合成 PDF 和合成数据，不代表真实论文或真实实验结果。它的作用是展示输入文件夹、字段配置和输出表格的基本形态。大模型抽取结果必须人工核验。
