# Scheduled product-image runbook

This repository is an **instruction-only harness**, not a background service. On each scheduled Codex run, follow this file using the connected **Fresco NY Google Drive** account and the built-in **`$imagegen`** tool. Never use rclone, Drive REST/SDK credentials, service accounts, API keys, or the image-generation CLI fallback. No photos, outputs, logs, or secrets belong in Git.

## Rules for every scheduled run

1. Read `categories.json` and `prompt.md` afresh. Treat the JSON array as the sole list of **exact output-folder names** (including `Others`) and the complete text of `prompt.md` as the editable image-generation instruction. Run `bash setup.sh` if Pillow dependencies are unavailable. Do not modify repository files.
2. Use **only the connected Google Drive connector** for Drive discovery, download, folder creation, upload, and move operations. Select the Fresco NY account, not another connected Drive. Find the exact `Unprocessed Garment Images` and `Processed Images` folders directly under **My Drive root**; fail the run with a clearly reported blocker if either is inaccessible. Resolve folder IDs from connector results; do not assume names are globally unique.
3. Keep **`Unprocessed Garment Images/` flat**: admins upload all raw photos directly into this folder, with **no category or control subfolders**. Ensure `Processed Images/<category>/` exists for every name in `categories.json`, plus `Processed Images/_done/`, `Processed Images/_failed/`, and `Processed Images/_logs/`. Create missing folders via the connector, then read back IDs. Reuse existing folders and preserve any archived originals; `_done`, `_failed`, and `_logs` are control folders, not product categories.
4. List **direct children only** of `Unprocessed Garment Images/`, following connector pagination when necessary. Accept regular files with case-insensitive `.jpg`, `.jpeg`, `.png`, `.heic`, or `.webp` extensions; ignore folders and other files. Sort by filename and Drive file ID for reproducibility. Never scan the `Processed Images/` tree for raw input.
5. For each raw photo, inspect the garment and classify it into **exactly one** category from `categories.json`, using the garment's visible construction rather than the filename or uploader's guess:
   - `T-shirts`: knit tees, including crew/V-necks, graphic and long-sleeve tees, **without a polo collar**.
   - `Polo shirts`: collared knit polos with a short button or zip placket.
   - `Sweatshirts & hoodies`: fleece/knit pullovers, hooded tops, and sweatshirts (not structured outer jackets).
   - `Shirts & overshirts`: collared woven/button-front shirts and overshirts, including checked shirts.
   - `Outerwear`: jackets, coats, fleece zip jackets, and structured outer layers; a denim jacket also belongs here.
   - `Denim`: jeans and denim trousers, not denim jackets.
   - `Trousers`: full-length non-denim pants, chinos, joggers, and utility trousers.
   - `Shorts`: any short-length trousers, including denim shorts.
   - `Others`: garments outside these categories or **visually ambiguous** photos. Do not guess a confident category when evidence is insufficient.
6. Before generation, search **all product-category folders** in `Processed Images/` for an existing `<original-stem>.webp`, not just the predicted category. If it exists anywhere, **do not generate or overwrite**. Log `skipped_existing_output` and leave the raw photo untouched for manual reconciliation; same-named photos may differ. Keep a run-local set of output names to prevent batch collisions.
7. Attempt **at most 20 new images per run** (including failures). Leave all other candidates directly in the raw root for the next run. If there are no eligible new images, upload a `no new images` log to `Processed Images/_logs/` and stop. Existing-output skips do not consume image-generation quota.

## Per-image transaction

For each selected image, isolate errors and continue to the next image:

1. Download the original using the **Drive connector** and materialize its returned authenticated file reference into `./inbox/`, preserving the original filename (use a unique local name if needed). Never call Google Drive HTTP endpoints directly, use separate Drive clients, or introduce credentials. A connector-returned temporary file reference may be materialized with the runtime's supported file-transfer mechanism.
2. Inspect the local source image, then use built-in **`$imagegen` in edit/reference mode**, passing that raw photo as the image reference and the exact text of `prompt.md` as the instruction. Do not use text-only generation and do not use a CLI/API fallback. Save the generated image locally; no generated image is committed.
3. Run `python scripts/finalize.py <generated-local-image> "./out/<category>/<original-stem>.webp"` with the actual quoted output path. The helper makes a centered cream-padded, square **1200 × 1200 WebP, quality 85**. Use a fresh output path; do not overwrite an existing local or Drive output.
4. Upload the finalized WebP with the **Drive connector** to `Processed Images/<classified-category>/` (including `Others` when uncertain). Verify upload success from its returned file ID/metadata and destination parent **before** changing the original. An error or ambiguous upload result is not success: check destination metadata before retrying, to prevent duplicate files.
5. **Only after verified upload**, move the original Drive file from the raw root directly into `Processed Images/_done/` using a Drive connector parent move (add the destination parent; remove only the verified source parent). Verify its new parent. Never copy the original and leave a second active input behind.
6. If any step fails, record the filename, predicted category, stage, and error. Attempt to move the original into `Processed Images/_failed/` with the connector and verify the move; log a second error if that move fails. If the output upload had succeeded but the move to `_done` failed, **do not upload/generate again**; flag the item for manual reconciliation. Never allow one image failure to stop the rest of the batch.

## Run log and safety

- Maintain `processed`, `failed`, `skipped_existing_output`, `classified_others`, and `remaining` counts; list each original filename, **classified category**, final filename, and every error (including failure to archive an original). Explain uncertain cases classified as `Others`. Count an image as processed only after final upload **and** a verified `_done` move. Record start/end time in the scheduled run's local timezone and the selected account/folder identifiers.
- **Always finish** by writing a human-readable log as `./logs/YYYY-MM-DD_HHMM.txt` and uploading it with the Drive connector to `Processed Images/_logs/YYYY-MM-DD_HHMM.txt`. If a name already exists, use a unique time suffix rather than overwrite. An empty batch must contain the literal phrase `no new images`. If Drive is unavailable and the log cannot be uploaded, retain the local log and report that explicit blocker.
- During scheduled runs: **never ask for confirmation, open a PR, commit, push, change branches, or edit any tracked repository file**. Keep everything transient under ignored `inbox/`, `out/`, and `logs/` directories.
- Do not assume AI can reproduce minute garment details perfectly. Preserve print, color, logos, seams, pockets, buttons, and labels as faithfully as possible; if a generated result visibly violates the source, count it as a failed image rather than publishing it.
