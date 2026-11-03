# Fresco product-image automation

An **agent-run instruction harness** for turning raw garment phone photos into polished website images. There is no always-on worker or GitHub Action: each scheduled Codex run reads `AGENTS.md`, `categories.json`, and `prompt.md`, uses the connected **Fresco NY Google Drive** connector and built-in **`$imagegen`**, **visually classifies each garment**, then uploads results and a run log. The repository never stores images or credentials.

## Google Drive folders (My Drive root)

```text
Unprocessed Garment Images/
  <raw images directly here — no subfolders>
Processed Images/
  T-shirts/
  Polo shirts/
  Sweatshirts & hoodies/
  Shirts & overshirts/
  Outerwear/
  Denim/
  Trousers/
  Shorts/
  Others/                  # unclear or unmatched garments
  _done/                   # archived originals after verified upload
  _failed/                 # originals that failed processing
  _logs/                   # YYYY-MM-DD_HHMM.txt per run
```

The first run creates missing category, `_done`, `_failed`, and `_logs` folders **inside Processed Images**. Admins upload all raw photos straight into the unprocessed root. The agent recognizes the garment from the photo, chooses one of eight website categories, or uses `Others` if uncertain. It processes **at most 20** per run, never overwrites a matching output in any category, and archives each original only after verifying the final upload. Corrupted sources and persistent product-quality failures go to `_failed`; shared service outages leave originals in input. Every run gets a log, including empty runs.

## Customize

- **Change the image look:** edit only `prompt.md`. Its text becomes the initial imagegen editing instruction on the next run. Conservative editing is the default; accurate flat-lay is accepted. `retry_prompt.md` supplies a single original-only conservative retry when quality review fails.
- **Add a garment category:** add its exact output-folder name to the JSON array in `categories.json`, and add a clear classification rule in `AGENTS.md`. The next run creates the new processed folder. Raw photos always go in the same unprocessed root.
- **Prepare the helper:** `bash setup.sh` (installs Pillow and pillow-heif), then `python scripts/finalize.py generated.png out/tshirts/example.webp` to normalize a locally generated photo. The helper is intentionally the only image-processing code.

## Test and schedule

1. In **Fresco NY** My Drive, upload one flat-lay photo directly to `Unprocessed Garment Images/`, without making any subfolder.
2. In a Codex environment with the **Google Drive connector** and **built-in imagegen** enabled, open this repository and request: **“Run the product-image pipeline following AGENTS.md. Limit this test to one new image. Do not edit or commit repository files.”**
3. Check the visually matched category under `Processed Images/` (or `Others/` if uncertain) for its WebP, `Processed Images/_done/` for the original, and `Processed Images/_logs/` for the run log.
4. To automate subsequent runs, create a **scheduled Codex task** for this repository using the instruction: **“Follow AGENTS.md for one product-image pipeline run. Use the Fresco NY Google Drive connector and built-in imagegen; do not edit or commit the repo.”** Choose the desired cadence (for example, every morning). Confirm that the scheduling environment can access both connected tools; a plain GitHub Actions cron job cannot call these ChatGPT-connected tools by itself.

If an output filename already exists, the raw file is intentionally left in the input folder and logged as a collision for human review, rather than risking a wrong archive or overwrite.

## Product accuracy and quality review

Imagegen may redraw small lettering or invent fabric detail even with a source reference. These prompts reduce the risk; they cannot guarantee success. The agent visually compares source and candidate before upload and logs a pass/fail/unverifiable verdict for color, fabric, construction, branding and composition. This review is not an automated product-accuracy test. `scripts/finalize.py` handles format and dimensions only.

A failed first candidate gets at most one retry using the original photo as the only reference and `retry_prompt.md`. Rejected candidates are never used as product outputs or references for that retry. Failed originals remain recoverable in `_failed`; ordinary runs do not automatically reprocess them. The repository contains instructions and a format helper, not a background service or a segmentation-based pixel-preserving editor.
