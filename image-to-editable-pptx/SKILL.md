---
name: image-to-editable-pptx
description: Rebuild one or more reference images, screenshots, diagrams, dashboards, infographics, or rendered slides as structurally editable PowerPoint slides. Use when the user asks to convert, reproduce, trace, or redraw images into PPTX while preserving layout and visual hierarchy; do not use for ordinary slide authoring without an image reference.
---

# Image to Editable PPTX

Reconstruct each supplied reference image as a PowerPoint slide whose text, simple geometry, connectors, tables, and charts remain editable. Preserve the source's communication job and page order. Do not silently improve or rewrite visible copy.

## Before authoring

1. Read the host's presentation-authoring Skill and follow its supported PPTX workflow. Prefer the platform's native presentation tooling; do not introduce a new dependency when the host already supplies one.
2. Inspect every source at original resolution. Run `scripts/probe_image.py <image>` to record dimensions, aspect ratio, color mode, and a slide-size recommendation.
3. Classify each page as `flat-diagram`, `dashboard`, `infographic`, `rendered-slide`, or `mixed-raster`.
4. State material limits before building when photos, textured illustration, illegible text, or 3D content prevent full editability.

For the full planning and reconstruction loop, read [references/reconstruction-workflow.md](references/reconstruction-workflow.md).

## Output contract

- Preserve the requested slide count. One source image normally maps to one slide, in input order.
- Preserve a supplied deck's dimensions and theme. Otherwise use the source aspect ratio; use 16:9 or 4:3 only when the ratio is close.
- Write a new PPTX. Do not overwrite the source or an existing deck unless the user explicitly requests it.
- Deliver only the PPTX unless the user asks for plans, renders, or reports. Keep crops, plans, diffs, and previews in scratch space.
- Keep source attribution in speaker notes when source files, external facts, or third-party assets require traceability.

## Editability contract

Use the most editable object that faithfully represents each region:

- readable wording: native text;
- cards, panels, dividers, simple icons, and decorations: native shapes;
- arrows and relationship lines: native connectors;
- tabular data: native tables;
- quantitative plots: native charts with editable data;
- logos and complex pictograms: separate SVG objects when available;
- photos and genuinely complex artwork: cropped raster objects with an explicit fallback reason in the plan.

Never leave the complete source image as a visible or hidden full-slide background. Do not claim full editability when a meaningful region remains rasterized.

## Reconstruction plan

Create a JSON plan before authoring. Start from `assets/slide-plan.template.json` and follow [references/slide-plan-schema.md](references/slide-plan-schema.md). Use stable element IDs and source-pixel bounding boxes.

Validate before authoring:

```powershell
python scripts/validate_slide_plan.py <slide-plan.json>
```

Run `--strict` before final delivery. Strict mode rejects unexplained raster fallbacks and full-slide raster elements.

## Geometry

Map source pixels to the target slide without changing relative geometry:

```text
x_slide = x_px / source_width_px * slide_width
y_slide = y_px / source_height_px * slide_height
w_slide = w_px / source_width_px * slide_width
h_slide = h_px / source_height_px * slide_height
```

Build large background regions first, then connectors, content shapes and assets, and text last. Preserve deliberate overlaps and z-order. Apply only small optical corrections for baselines, stroke alignment, and centering.

## Validation

Read [references/validation.md](references/validation.md) before final delivery. Keep three separate decisions:

1. **Structural editability:** expected native objects exist, source images are not embedded as full-slide shortcuts, and the PPTX package is valid.
2. **Visual fidelity:** every slide is rendered and compared side by side at full size; clipping, wrapping, z-order, connectors, colors, and spacing are inspected.
3. **Content fidelity:** visible wording, numbers, sequence, and relationships match the reference; unreadable content is marked instead of invented.

Run the deterministic checks:

```powershell
python scripts/validate_slide_plan.py <slide-plan.json> --strict
python scripts/validate_pptx.py <output.pptx> --plan <slide-plan.json> --source-image <source.png>
python scripts/compare_renders.py <source.png> <rendered-slide.png> --output-dir <qa-dir>
```

For multiple sources, run the image-specific PPTX and render comparisons once per mapped slide. Treat similarity scores as diagnostics rather than a universal pass threshold.

## Delivery report

Report the PPTX path, slide count, editable coverage estimate, and any font substitutions or raster fallbacks. Distinguish checks actually run from checks not available in the environment.
