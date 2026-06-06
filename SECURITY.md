# Security Policy

## Reporting security and privacy issues

If you find a security or privacy issue in Chem-PDF-Extractor, please do not post sensitive details publicly.

This project may be used with:

- private PDFs;
- unpublished manuscripts;
- local logs;
- API keys;
- `config.local.json`;
- extracted Excel / CSV outputs;
- confidential industrial or research data.

Do not include API keys, private PDFs, full logs, local absolute paths, unpublished data, or confidential output files in public GitHub issues or pull requests.

If the issue can be described without sensitive material, open a GitHub issue with a minimal, sanitized reproduction.

If the issue involves sensitive material, describe the problem at a high level first and remove or replace private data with synthetic examples.

## Scope

Security and privacy issues may include:

- accidental exposure of API keys or tokens;
- accidental commit of `config.local.json`;
- logs containing private file paths or extracted confidential data;
- examples containing copyrighted papers or unpublished data;
- unsafe handling of local files or outputs.

## Safe reporting checklist

Before reporting, please check:

- API keys and tokens have been removed.
- Private PDFs have not been uploaded.
- Local absolute paths have been anonymized.
- Output files contain only synthetic or permission-safe data.
- Logs have been redacted.

## Manual review reminder

AI extraction results must be manually reviewed before scientific use.
