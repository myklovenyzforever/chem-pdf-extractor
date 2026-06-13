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

## Local Web UI and API keys

The Web UI is intended for local loopback use only. Do not expose it to a LAN, public server, shared workstation, or remote environment where other users can reach the local service.

Cloud API keys should be treated as secrets. The application should not return full API keys through local configuration APIs, and logs or diagnostics should redact common API key, bearer-token, password, token, and secret patterns before writing user-visible files.

Cloud Base URLs should be checked before sending API keys. Use HTTPS for cloud providers. Plain HTTP should be used only for localhost-style local services.

## Spreadsheet export safety

Excel and CSV outputs may be opened in spreadsheet software that interprets values beginning with formula characters. Exported spreadsheet cells should sanitize formula-like values to reduce spreadsheet formula-injection risk.

Sanitization is a defense-in-depth measure, not a guarantee. Users should still review exported files before sharing them or opening them in sensitive environments.

## Failed source PDF copies

Copying failed source PDFs for debugging can duplicate private PDFs, unpublished manuscripts, copyrighted papers, or confidential industrial data. This behavior should remain opt-in and should be enabled only when the user needs local debugging copies.

Do not upload copied failed-source folders to public issues or pull requests unless the files are public-domain, synthetic, or otherwise permission-safe.

## Safe reporting checklist

Before reporting, please check:

- API keys and tokens have been removed.
- Private PDFs have not been uploaded.
- Local absolute paths have been anonymized.
- Output files contain only synthetic or permission-safe data.
- Logs have been redacted.

## Manual review reminder

AI extraction results must be manually reviewed before scientific use.
