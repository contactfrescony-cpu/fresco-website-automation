#!/usr/bin/env python3
"""Normalize a generated product image to a 1200x1200 cream-padded WebP."""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError as exc:
    raise SystemExit("Pillow is missing; run: bash setup.sh") from exc

try:
    from pillow_heif import register_heif_opener
except ImportError:
    register_heif_opener = None
else:
    register_heif_opener()


CREAM = (251, 248, 243)  # #FBF8F3
SIZE = 1200


def finalize(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Input image does not exist: {source}")
    if source.suffix.lower() in {".heic", ".heif"} and register_heif_opener is None:
        raise RuntimeError("HEIC support is missing; run: bash setup.sh")
    if destination.suffix.lower() != ".webp":
        raise ValueError(f"Output filename must end in .webp: {destination}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite an existing output: {destination}")

    try:
        with Image.open(source) as opened:
            opened.load()
            image = ImageOps.exif_transpose(opened)
            # Flatten transparency against the same cream used for square padding.
            if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                rgba = image.convert("RGBA")
                backdrop = Image.new("RGBA", rgba.size, CREAM + (255,))
                image = Image.alpha_composite(backdrop, rgba).convert("RGB")
            else:
                image = image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise RuntimeError(f"Could not open/decode input image {source}: {exc}") from exc

    width, height = image.size
    if not width or not height:
        raise ValueError(f"Input image has invalid dimensions: {width}x{height}")

    edge = max(width, height)
    square = Image.new("RGB", (edge, edge), CREAM)
    square.paste(image, ((edge - width) // 2, (edge - height) // 2))
    resized = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS)

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        resized.save(destination, format="WEBP", quality=85, method=6)
    except OSError as exc:
        raise RuntimeError(f"Could not save WebP to {destination}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Generated input image")
    parser.add_argument("output", type=Path, help="New .webp output path")
    args = parser.parse_args()

    try:
        finalize(args.input, args.output)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"finalize.py: error: {exc}", file=sys.stderr)
        return 1

    print(f"Created {args.output} (1200x1200 WebP, quality 85)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
