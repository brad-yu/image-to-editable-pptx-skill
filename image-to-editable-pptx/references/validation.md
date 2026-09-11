# Validation and acceptance

Passing one class of checks does not imply the others passed.

| Check | What it proves | What it does not prove |
| --- | --- | --- |
| Plan validation | The reconstruction inventory is internally consistent | The PPTX follows the plan |
| PPTX package validation | The ZIP/XML package opens and expected native objects exist | The rendered slide looks correct |
| Full-size render inspection | Text fit, placement, z-order, and visible layout are acceptable | Objects remain editable |
| Pixel diagnostics | Large visual differences can be located | The slide is correct or editable |
| Content comparison | Wording, numbers, and relationships match | Fonts and geometry match |

## Required final checks

1. Open the PPTX package successfully and verify every ZIP member.
2. Confirm the intended slide count and slide dimensions.
3. Confirm expected native text, shapes, connectors, tables, and charts.
4. Search embedded media for a byte-identical copy of the supplied source image.
5. Flag any picture covering at least 90 percent of a slide.
6. Render every slide and inspect it individually at full size.
7. Compare each render with its reference and inspect the generated difference image.
8. Confirm no placeholder, crop, plan, preview, or QA file remains beside the final deliverable.

## Interpreting similarity

`compare_renders.py` reports normalized root mean square error, mean absolute error, and a convenience similarity value. Use the score to find regressions between iterations. Do not impose one universal threshold across diagrams, screenshots, photographs, fonts, or rendering engines.

## Reporting

Use one of these labels for each check: `passed`, `warning`, `failed`, or `not run`. A wrapper process exit code is not enough evidence; inspect the expected files and validation results. Do not describe structural checks as visual acceptance.
