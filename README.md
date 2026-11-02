# Fresco product-image automation

An **agent-run instruction harness** for turning raw garment phone photos into polished website images. There is no always-on worker or GitHub Action: each scheduled Codex run reads `AGENTS.md`, `categories.json`, and `prompt.md`, uses the connected **Fresco NY Google Drive** connector and built-in **`$imagegen`**, then uploads results and a run log. The repository never stores images or credentials.

## Google Drive folders (My Drive root)

```text
Unprocessed Garment Images/
  tshirts/  sweatshirts/  shirts/  outerwear/
  _done/<category>/        # archived originals after successful upload
  _failed/<category>/      # unsuccessful originals
Processed Images/
  <category>/              # final 1200x1200 WebP product photos
  _logs/                   # YYYY-MM-DD_HHMM.txt per run
```

The first run creates missing category, `_done`, `_failed`, and `_logs` folders. It scans only direct images in the four raw category folders, processes **at most 20** per run, never overwrites a matching output, and moves each original to `_done` only after verifying the final upload. Failures go to `_failed`; every run gets a log, including empty runs.

## Customize

- **Change the image look:** edit only `prompt.md`. Its text becomes the imagegen editing instruction on the next run.
- **Add a garment category:** add a string to the JSON array in `categories.json`. The next run creates the corresponding Drive folders automatically; upload new raw photos into the new raw category folder.
- **Prepare the helper:** `bash setup.sh` (installs Pillow and pillow-heif), then `python scripts/finalize.py generated.png out/tshirts/example.webp` to normalize a locally generated photo. The helper is intentionally the only image-processing code.

## Test and schedule

1. In **Fresco NY** My Drive, upload one flat-lay photo to `Unprocessed Garment Images/tshirts/`.
2. In a Codex environment with the **Google Drive connector** and **built-in imagegen** enabled, open this repository and request: **“Run the product-image pipeline following AGENTS.md. Limit this test to one new image. Do not edit or commit repository files.”**
3. Check `Processed Images/tshirts/` for its WebP, `Unprocessed Garment Images/_done/tshirts/` for the original, and `Processed Images/_logs/` for the run log.
4. To automate subsequent runs, create a **scheduled Codex task** for this repository using the instruction: **“Follow AGENTS.md for one product-image pipeline run. Use the Fresco NY Google Drive connector and built-in imagegen; do not edit or commit the repo.”** Choose the desired cadence (for example, every morning). Confirm that the scheduling environment can access both connected tools; a plain GitHub Actions cron job cannot call these ChatGPT-connected tools by itself.

If an output filename already exists, the raw file is intentionally left in the input folder and logged as a collision for human review, rather than risking a wrong archive or overwrite.
