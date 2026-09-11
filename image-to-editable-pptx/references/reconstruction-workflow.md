# Reconstruction workflow

Use this workflow after the source images and requested output scope are known.

## 1. Inventory the sources

For each source, record its filename, pixel dimensions, aspect ratio, page order, and legibility. Identify whether the user supplied a target deck or template. A supplied PPTX controls slide size, theme, and repeated furniture only when the user asks to follow it.

## 2. Segment each page

Inventory the page background, section bands, text blocks, shapes, connectors, icons, tables, charts, photos, and intentional overlaps. Record bounding boxes in source pixels. Keep the exact visible wording and observed line breaks when they carry meaning.

| Reference region | Preferred PowerPoint object |
| --- | --- |
| Heading, label, paragraph, number | Text box or shape text |
| Card, panel, band, divider | Native shape |
| Arrow, leader, relationship | Native connector |
| Repeated rows and columns | Native table |
| Quantitative data graphic | Native chart with editable data |
| Flat icon or logo | Separate SVG |
| Photograph or complex texture | Cropped raster image |

Do not combine several independent objects into a single raster merely to improve pixel similarity.

## 3. Decide fallback boundaries

Raster fallback is reasonable for photographs, photorealistic composites, complex textures, and detail that cannot be recovered from the source. Record the fallback region and reason in the plan. Keep surrounding labels and overlays editable.

Never invent unreadable wording. Mark it as unresolved in working notes and ask the user only when it materially changes the result.

## 4. Build the slide

Use source coordinates as the geometric truth. Preserve aspect ratio and crop rather than stretching assets. Rebuild in this order:

1. background and large regions;
2. connectors and lines that belong behind nodes;
3. shapes, tables, charts, and visual assets;
4. native text and foreground labels.

Match fonts when available. Otherwise select a metrically close installed font and verify every line break in the render. Keep icons and logos proportional.

## 5. Iterate against renders

Render every slide after the first complete pass. Fix defects in this order:

1. missing or incorrect content;
2. clipping, overflow, and unwanted wrapping;
3. wrong hierarchy, region sizes, or connector direction;
4. incorrect asset placement or z-order;
5. minor color, shadow, and anti-aliasing differences.

Rebuild only affected output and previews. Keep the source images and validated plan stable unless the segmentation itself was wrong.

## 6. Finalize

Run plan validation, PPTX package/editability validation, and full-size visual inspection. Keep validation artifacts outside the delivery directory. Report any remaining raster fallback or font substitution.
