# Slide plan schema

The plan is a UTF-8 JSON file. Coordinates use source-image pixels so the plan remains independent of the authoring library.

## Top-level fields

- `version`: integer, currently `1`.
- `sources`: non-empty array of source records.
- `slides`: non-empty array of slide records, normally one per source.

## Source record

- `id`: stable unique string.
- `path`: source filename or path.
- `width_px`, `height_px`: positive integers.
- `sha256`: optional source digest.

## Slide record

- `index`: one-based integer, unique across the plan.
- `source_id`: ID of a source record.
- `classification`: `flat-diagram`, `dashboard`, `infographic`, `rendered-slide`, or `mixed-raster`.
- `elements`: array of element records in back-to-front z-order.

## Element record

- `id`: stable unique string within the plan.
- `type`: `text`, `shape`, `connector`, `table`, `chart`, `svg`, `image`, or `group`.
- `bbox_px`: `[x, y, width, height]`. Values must be non-negative and remain inside the source bounds. Connectors may use a thin bounding box but width and height cannot both be zero.
- `editable`: boolean. `text`, `shape`, `connector`, `table`, and `chart` must be `true`.
- `text`: required for `text`; preserve visible wording.
- `role`: optional semantic role such as `title`, `body`, `label`, `background`, or `icon`.
- `fallback_reason`: required for every raster `image` element.
- `notes`: optional implementation detail that affects fidelity.

See `assets/slide-plan.sample.json` for a complete small plan. Start new work from `assets/slide-plan.template.json`. Example invocation requests are in [examples.md](examples.md).
