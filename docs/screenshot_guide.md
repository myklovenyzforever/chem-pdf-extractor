# Screenshot Guide

This guide is for maintainers refreshing README screenshots or adding new documentation images.

Screenshots are documentation artifacts. They should help reviewers understand the current user workflow without exposing private research data, local machine details, secrets, or copyrighted paper text.

## Current Images

- `docs/screenshots/web-ui-zh+en.png`: compact Web UI workbench with bilingual labels.
- `docs/screenshots/excel-output-example.svg`: synthetic Excel/CSV output preview.

The existing output preview is synthetic and does not represent real extracted research results.

## What Screenshots Should Show

Use screenshots to show:

- the local Web UI running on `127.0.0.1` or `localhost`;
- the compact three-column workbench described in [UI Layout Contract](ui_layout_contract.md);
- task settings, API/model configuration, progress, statistics, and logs visible in the first workbench;
- field templates or field editing only when the screenshot is specifically about fields;
- exported table shape using synthetic/public-safe data only.

## Refresh Checklist

Before replacing or adding screenshots:

- Use synthetic or public-safe demo content only.
- Do not show private PDFs, unpublished manuscripts, confidential industrial data, or copyrighted paper excerpts.
- Do not show API keys, tokens, passwords, `config.local.json`, `.env`, or provider account details.
- Do not show private local paths, usernames, drive-specific project folders, logs, caches, or generated outputs from real papers.
- Do not add fake screenshots or manually edited images that misrepresent current behavior.
- Verify the Web UI screenshot against the current layout contract, ideally at 1366x768 and 100% browser zoom.
- Keep image files reasonably small for repository review.
- Update README links if filenames change.

## Suggested Capture Flow

1. Start the local app from a clean checkout:

   ```powershell
   python -m chem_pdf_extractor
   ```

2. Open the printed local URL in a browser.
3. Use only synthetic examples from `examples/` or a public-safe temporary fixture.
4. Confirm there are no secrets, private paths, private PDF names, or real-paper text visible.
5. Capture the image and save it under `docs/screenshots/`.
6. Run the documentation tests and `git diff --check` before committing.

Screenshots are illustrative only. They do not prove extraction accuracy, model quality, or scientific correctness.
