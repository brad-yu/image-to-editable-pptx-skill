#!/usr/bin/env python3
"""Validate PPTX package integrity and native-object coverage for image reconstruction."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")


def slide_number(name: str) -> int:
    match = SLIDE_RE.match(name)
    return int(match.group(1)) if match else 0


def plan_expectations(plan_path: Path | None) -> tuple[int | None, list[Counter[str]]]:
    if not plan_path:
        return None, []
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slides = sorted(plan.get("slides", []), key=lambda item: item.get("index", 0))
    return len(slides), [Counter(element.get("type") for element in slide.get("elements", [])) for slide in slides]


def inspect_slide(xml_bytes: bytes, slide_width: int, slide_height: int) -> dict[str, object]:
    root = ET.fromstring(xml_bytes)
    shapes = root.findall(".//p:sp", NS)
    connectors = root.findall(".//p:cxnSp", NS)
    pictures = root.findall(".//p:pic", NS)
    frames = root.findall(".//p:graphicFrame", NS)
    text_shapes = sum(1 for shape in shapes if any((node.text or "").strip() for node in shape.findall(".//a:t", NS)))
    tables = 0
    charts = 0
    for frame in frames:
        for data in frame.findall(".//a:graphicData", NS):
            uri = data.attrib.get("uri", "")
            tables += int(uri.endswith("/table"))
            charts += int(uri.endswith("/chart"))
    full_slide_pictures = 0
    picture_areas: list[float] = []
    for picture in pictures:
        transform = picture.find("./p:spPr/a:xfrm", NS)
        if transform is None:
            continue
        offset = transform.find("a:off", NS)
        extent = transform.find("a:ext", NS)
        if offset is None or extent is None:
            continue
        x = int(offset.attrib.get("x", 0))
        y = int(offset.attrib.get("y", 0))
        width = int(extent.attrib.get("cx", 0))
        height = int(extent.attrib.get("cy", 0))
        area = (width * height) / (slide_width * slide_height) if slide_width and slide_height else 0.0
        picture_areas.append(area)
        if x <= slide_width * 0.02 and y <= slide_height * 0.02 and area >= 0.90:
            full_slide_pictures += 1
    text_values = [(node.text or "").strip() for node in root.findall(".//a:t", NS)]
    return {
        "native_shapes": len(shapes),
        "native_text_shapes": text_shapes,
        "connectors": len(connectors),
        "pictures": len(pictures),
        "tables": tables,
        "charts": charts,
        "full_slide_pictures": full_slide_pictures,
        "largest_picture_area_ratio": round(max(picture_areas, default=0.0), 6),
        "text": [value for value in text_values if value],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--source-image", type=Path, action="append", default=[])
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, object] = {"pptx": str(args.pptx.resolve())}

    if not args.pptx.is_file():
        print(f"ERROR: PPTX not found: {args.pptx}", file=sys.stderr)
        return 2
    try:
        expected_slide_count, expected_by_slide = plan_expectations(args.plan)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read plan: {exc}", file=sys.stderr)
        return 2

    try:
        with zipfile.ZipFile(args.pptx) as package:
            corrupt = package.testzip()
            if corrupt:
                errors.append(f"corrupt ZIP member: {corrupt}")
            names = package.namelist()
            required = {"[Content_Types].xml", "ppt/presentation.xml"}
            missing = sorted(required.difference(names))
            if missing:
                errors.append(f"missing package members: {', '.join(missing)}")
            presentation = ET.fromstring(package.read("ppt/presentation.xml"))
            size = presentation.find("p:sldSz", NS)
            slide_width = int(size.attrib["cx"]) if size is not None else 0
            slide_height = int(size.attrib["cy"]) if size is not None else 0
            slide_names = sorted((name for name in names if SLIDE_RE.match(name)), key=slide_number)
            slides = [inspect_slide(package.read(name), slide_width, slide_height) for name in slide_names]
            media_names = [name for name in names if name.startswith("ppt/media/") and not name.endswith("/")]
            media_hashes = {hashlib.sha256(package.read(name)).hexdigest(): name for name in media_names}
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        print(f"ERROR: invalid PPTX package: {exc}", file=sys.stderr)
        return 2

    report.update({
        "slide_count": len(slides),
        "slide_size_emu": [slide_width, slide_height],
        "media_count": len(media_names),
        "slides": slides,
    })
    if expected_slide_count is not None and len(slides) != expected_slide_count:
        errors.append(f"slide count {len(slides)} does not match plan {expected_slide_count}")
    for index, slide in enumerate(slides):
        if slide["full_slide_pictures"]:
            errors.append(f"slide {index + 1} contains a picture covering at least 90% of the slide")
        if index >= len(expected_by_slide):
            continue
        expected = expected_by_slide[index]
        minimums = {
            "native_shapes": expected["shape"] + expected["text"],
            "native_text_shapes": expected["text"],
            "connectors": expected["connector"],
            "pictures": expected["image"] + expected["svg"],
            "tables": expected["table"],
            "charts": expected["chart"],
        }
        for key, minimum in minimums.items():
            if slide[key] < minimum:
                errors.append(f"slide {index + 1} has {slide[key]} {key}; plan requires at least {minimum}")
    for source in args.source_image:
        if not source.is_file():
            errors.append(f"source image not found: {source}")
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest in media_hashes:
            errors.append(f"source image is embedded byte-for-byte as {media_hashes[digest]}")
    if not any(slide["native_text_shapes"] for slide in slides):
        warnings.append("PPTX contains no native text shapes")

    report.update({"status": "failed" if errors else "passed", "warnings": warnings, "errors": errors})
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
