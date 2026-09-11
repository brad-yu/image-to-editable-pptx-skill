#!/usr/bin/env python3
"""Validate the image-to-editable-PPTX reconstruction plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


CLASSIFICATIONS = {
    "flat-diagram",
    "dashboard",
    "infographic",
    "rendered-slide",
    "mixed-raster",
}
ELEMENT_TYPES = {"text", "shape", "connector", "table", "chart", "svg", "image", "group"}
NATIVE_TYPES = {"text", "shape", "connector", "table", "chart"}


def validate(plan: object, strict: bool) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {kind: 0 for kind in sorted(ELEMENT_TYPES)}
    if not isinstance(plan, dict):
        return ["top level must be an object"], warnings, counts
    if plan.get("version") != 1:
        errors.append("version must be 1")

    sources = plan.get("sources")
    slides = plan.get("slides")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
        sources = []
    if not isinstance(slides, list) or not slides:
        errors.append("slides must be a non-empty array")
        slides = []

    source_map: dict[str, tuple[float, float]] = {}
    for i, source in enumerate(sources):
        label = f"sources[{i}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
            continue
        if source_id in source_map:
            errors.append(f"duplicate source id: {source_id}")
            continue
        width = source.get("width_px")
        height = source.get("height_px")
        if not isinstance(width, (int, float)) or width <= 0:
            errors.append(f"{label}.width_px must be positive")
        if not isinstance(height, (int, float)) or height <= 0:
            errors.append(f"{label}.height_px must be positive")
        if isinstance(width, (int, float)) and width > 0 and isinstance(height, (int, float)) and height > 0:
            source_map[source_id] = (float(width), float(height))
        if not isinstance(source.get("path"), str) or not source["path"].strip():
            errors.append(f"{label}.path must be a non-empty string")

    slide_indices: set[int] = set()
    element_ids: set[str] = set()
    for i, slide in enumerate(slides):
        label = f"slides[{i}]"
        if not isinstance(slide, dict):
            errors.append(f"{label} must be an object")
            continue
        index = slide.get("index")
        if not isinstance(index, int) or index < 1:
            errors.append(f"{label}.index must be a positive integer")
        elif index in slide_indices:
            errors.append(f"duplicate slide index: {index}")
        else:
            slide_indices.add(index)
        source_id = slide.get("source_id")
        if source_id not in source_map:
            errors.append(f"{label}.source_id does not reference a valid source")
            width = height = 0.0
        else:
            width, height = source_map[source_id]
        if slide.get("classification") not in CLASSIFICATIONS:
            errors.append(f"{label}.classification is invalid")
        elements = slide.get("elements")
        if not isinstance(elements, list):
            errors.append(f"{label}.elements must be an array")
            continue
        for j, element in enumerate(elements):
            elabel = f"{label}.elements[{j}]"
            if not isinstance(element, dict):
                errors.append(f"{elabel} must be an object")
                continue
            element_id = element.get("id")
            if not isinstance(element_id, str) or not element_id.strip():
                errors.append(f"{elabel}.id must be a non-empty string")
            elif element_id in element_ids:
                errors.append(f"duplicate element id: {element_id}")
            else:
                element_ids.add(element_id)
            kind = element.get("type")
            if kind not in ELEMENT_TYPES:
                errors.append(f"{elabel}.type is invalid")
                continue
            counts[kind] += 1
            bbox = element.get("bbox_px")
            if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(v, (int, float)) for v in bbox):
                errors.append(f"{elabel}.bbox_px must contain four numbers")
                continue
            x, y, box_width, box_height = map(float, bbox)
            if x < 0 or y < 0 or box_width < 0 or box_height < 0 or box_width + box_height <= 0:
                errors.append(f"{elabel}.bbox_px has invalid geometry")
            if width and height and (x + box_width > width + 0.5 or y + box_height > height + 0.5):
                errors.append(f"{elabel}.bbox_px exceeds source bounds")
            editable = element.get("editable")
            if kind in NATIVE_TYPES and editable is not True:
                errors.append(f"{elabel} must be editable")
            if kind == "text" and (not isinstance(element.get("text"), str) or not element["text"].strip()):
                errors.append(f"{elabel}.text must be a non-empty string")
            if kind == "image":
                reason = element.get("fallback_reason")
                if not isinstance(reason, str) or not reason.strip():
                    message = f"{elabel} requires fallback_reason"
                    (errors if strict else warnings).append(message)
                if width and height and box_width * box_height >= width * height * 0.90:
                    message = f"{elabel} covers at least 90% of the source page"
                    (errors if strict else warnings).append(message)

    if slide_indices and slide_indices != set(range(1, len(slide_indices) + 1)):
        errors.append("slide indices must be contiguous starting at 1")
    return errors, warnings, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors, warnings, counts = validate(plan, args.strict)
    result = {"status": "failed" if errors else "passed", "strict": args.strict, "counts": counts, "warnings": warnings, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
