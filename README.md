# Image to Editable PPTX Skill

A reusable Codex Skill for rebuilding reference images as structurally editable PowerPoint slides, with separate checks for editability, package integrity, content fidelity, and visual fidelity.

## Install

Copy the `image-to-editable-pptx` directory into your Codex skills directory, or clone this repository and link that directory from your Codex configuration. Restart or begin a new Codex conversation after installation.

## Use

Invoke `$image-to-editable-pptx` and provide one or more reference images. The Skill creates a reconstruction plan, rebuilds each page with native PowerPoint objects where practical, renders the result, and validates the PPTX before delivery.

## Included checks

- source-image dimensions and aspect ratio;
- slide-plan schema, bounds, and raster-fallback policy;
- PPTX ZIP/XML integrity and native-object inventory;
- full-slide raster shortcut detection;
- render comparison diagnostics.

The validation scripts use Python 3.10 or later. `compare_renders.py` and `probe_image.py` require Pillow.
