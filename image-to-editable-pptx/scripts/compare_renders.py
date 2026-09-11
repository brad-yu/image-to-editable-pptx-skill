#!/usr/bin/env python3
"""Compare a reference image with a rendered slide and write diagnostic images."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("render", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        from PIL import Image, ImageChops, ImageEnhance, ImageStat
    except ImportError:
        print("ERROR: Pillow is required: python -m pip install Pillow", file=sys.stderr)
        return 2
    if not args.reference.is_file() or not args.render.is_file():
        print("ERROR: both input images must exist", file=sys.stderr)
        return 2

    with Image.open(args.reference) as source_image, Image.open(args.render) as render_image:
        reference = source_image.convert("RGB")
        candidate = render_image.convert("RGB")
    resized = candidate.size != reference.size
    if resized:
        candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)
    difference = ImageChops.difference(reference, candidate)
    stats = ImageStat.Stat(difference)
    channel_rms = stats.rms
    channel_mean = stats.mean
    normalized_rms = math.sqrt(sum(value * value for value in channel_rms) / len(channel_rms)) / 255.0
    mean_absolute_error = sum(channel_mean) / len(channel_mean) / 255.0
    result = {
        "reference_size": list(reference.size),
        "render_size": list(candidate.size),
        "render_resized_for_comparison": resized,
        "normalized_rms_error": round(normalized_rms, 6),
        "mean_absolute_error": round(mean_absolute_error, 6),
        "similarity": round(max(0.0, 1.0 - normalized_rms), 6),
    }
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        difference.save(args.output_dir / "difference.png")
        ImageEnhance.Contrast(difference).enhance(4.0).save(args.output_dir / "difference-enhanced.png")
        Image.blend(reference, candidate, 0.5).save(args.output_dir / "overlay.png")
        (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
