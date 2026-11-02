# Scheduled product-image runbook

This repository is an **instruction-only harness**, not a background service. On each scheduled Codex run, follow this file using the connected **Fresco NY Google Drive** account and the built-in **`$imagegen`** tool. Never use rclone, Drive REST/SDK credentials, service accounts, API keys, or the image-generation CLI fallback. No photos, outputs, logs, or secrets belong in Git.

## Rules for every scheduled run

1. Read `categories.json` and `prompt.md` afresh. Treat the JSON array as the sole list of categories and the complete text of `prompt.md` as the editable image-generation instruction. Run `bash setup.sh` if Pillow dependencies are unavailable. Do not modify repository files.
2. Use **only the connected Google Drive connector** for Drive discovery, download, folder creation, upload, and move operations. Select the Fresco NY account, not another connected Drive. Find the exact `Unprocessed Garment Images` and `Processed Images` folders directly under **My Drive root**; fail the run with a clearly reported blocker if either is inaccessible. Resolve folder IDs from connector results; do not assume names are globally unique.
3. Ensure the following folders exist; create each missing folder using the Drive connector, then read back its ID:
   - `Unprocessed Garment Images/<category>/` for every category
   - `Unprocessed Garment Images/_done/<category>/` for every category
   - `Unprocessed Garment Images/_failed/<category>/` for every category
   - `Processed Images/<category>/` for every category
   - `Processed Images/_logs/`
   Reuse existing folders instead of creating duplicates. `_done`, `_failed`, and `_logs` are control folders, never input categories.
4. List **direct children only** of each `Unprocessed Garment Images/<category>/`, following Drive connector pagination when necessary. Accept regular files with case-insensitive `.jpg`, `.jpeg`, `.png`, `.heic`, or `.webp` extensions; ignore folders and other files. Sort by category order from `categories.json`, then by filename and Drive file ID for reproducibility. Never recursively scan `_done` or `_failed`.
5. Before attempting an image, check for an existing final file named `<original-stem>.webp` directly in the matching `Processed Images/<category>/`. If present, **do not generate or overwrite it**. Log the collision as `skipped_existing_output` and leave the raw file untouched for manual reconciliation; identical names can contain different photos. An original already under `_done` is not a candidate. Keep a run-local set of output names so same-name inputs in one batch do not overwrite one another.
6. Attempt **at most 20 new images per run** (including failures). Leave all remaining candidates in their input folders for the next run. If there are no eligible new images, upload a `no new images` log to `Processed Images/_logs/` and stop. Existing-output skips do not consume image-generation quota.

## Per-image transaction

For each selected image, isolate errors and continue to the next image:

1. Download the original with the **Drive connector** into `./inbox/<category>/`, preserving the original filename (use a unique local name if needed). Materialize the connector's authenticated file reference locally; never fetch Drive media with `curl`, `requests`, direct URLs, or a separate client.
2. Inspect the local source image, then use built-in **`$imagegen` in edit/reference mode**, passing that raw photo as the image reference and the exact text of `prompt.md` as the instruction. Do not use text-only generation and do not use a CLI/API fallback. Save the generated image locally; no generated image is committed.
3. Run `python scripts/finalize.py <generated-local-image> ./out/<category>/<original-stem>.webp`. The helper makes a centered cream-padded, square **1200 × 1200 WebP, quality 85**. Use a fresh output path; do not overwrite an existing local or Drive output.
4. Upload the finalized WebP with the **Drive connector** to `Processed Images/<category>/`. Verify upload success from its returned file ID/metadata and destination parent **before** changing the original. An error or ambiguous upload result is not success: check destination metadata before retrying, to prevent duplicate files.
5. **Only after verified upload**, move the original Drive file to `Unprocessed Garment Images/_done/<category>/` using a Drive connector parent move (add the destination parent; remove only the verified source parent). Verify its new parent. Never copy the original and leave a second active input behind.
6. If any step fails, record the filename, category, stage, and error. Attempt to move the original to `Unprocessed Garment Images/_failed/<category>/` with the connector and verify the move; log a second error if that move fails. If the output upload had succeeded but the move to `_done` failed, **do not upload/generate again**; flag the item for manual reconciliation. Never allow one image failure to stop the rest of the batch.

## Run log and safety

- Maintain `processed`, `failed`, `skipped_existing_output`, and `remaining` counts; list the relevant category/filenames and every error (including failure to archive an original). Count an image as processed only after final upload **and** a verified `_done` move. Record start/end time in the scheduled run's local timezone and the selected account/folder identifiers.
- **Always finish** by writing a human-readable log as `./logs/YYYY-MM-DD_HHMM.txt` and uploading it with the Drive connector to `Processed Images/_logs/YYYY-MM-DD_HHMM.txt`. If a name already exists, use a unique time suffix rather than overwrite. An empty batch must contain the literal phrase `no new images`. If Drive is unavailable and the log cannot be uploaded, retain the local log and report that explicit blocker.
- During scheduled runs: **never ask for confirmation, open a PR, commit, push, change branches, or edit any tracked repository file**. Keep everything transient under ignored `inbox/`, `out/`, and `logs/` directories.
- Do not assume AI can reproduce minute garment details perfectly. Preserve print, color, logos, seams, pockets, buttons, and labels as faithfully as possible; if a generated result visibly violates the source, count it as a failed image rather than publishing it.
