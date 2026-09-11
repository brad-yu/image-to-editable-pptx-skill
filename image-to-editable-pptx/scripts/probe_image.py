#!/usr/bin/env python3
"""Report image geometry and a practical PowerPoint slide-size recommendation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def recommend_size(ratio: float) -> dict[str, object]:
    if abs(ratio - 16 / 9) <= 0.025:
        return {"kind": "16:9", "width_in": 13.333333, "height_in": 7.5}
    if abs(ratio - 4 / 3) <= 0.025:
        return {"kind": "4:3", "width_in": 10.0, "height_in": 7.5}
    if ratio >= 1:
        width = 13.333333
        height = width / ratio
    else:
        height = 10.0
        width = height * ratio
    return {
        "kind": "custom",
        "width_in": round(width, 6),
        "height_in": round(height, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow is required: python -m pip install Pillow", file=sys.stderr)
        return 2

    if not args.image.is_file():
        print(f"ERROR: image not found: {args.image}", file=sys.stderr)
        return 2

    raw = args.image.read_bytes()
    with Image.open(args.image) as image:
        width, height = image.size
        result = {
            "path": str(args.image.resolve()),
            "format": image.format,
            "mode": image.mode,
            "width_px": width,
            "height_px": height,
            "aspect_ratio": round(width / height, 8),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "slide_size": recommend_size(width / height),
        }

    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
