# AEP redraw test

## Method
The canonical 16-unit open mark was reconstructed from descriptive prose, not coordinate transcription.

On every pass, the reconstruction step withheld:
- the numbered rectangle list under **Canonical 16-unit construction**;
- the entire **Pinned dimensions** list;
- both finished `M...Z` path strings;
- every SVG and PNG;
- `favicon.ico` and the Apple touch icon;
- the construction sheet.

Each reconstruction was rasterized on a 16 × 16 binary grid and diffed pixel-for-pixel against the canonical SVG raster.

## Iteration 1 — failed
The pre-repair prose fixed the one-unit right overhang and horizontal relationships, but once the lists and paths were withheld it did not independently pin the canonical mark's vertical placement and extent. A prose-only reconstruction preserved the horizontal relationships but placed the 10-unit-tall doorway at y = 2 through 12 instead of y = 3 through 13.

Differing pixels: **20**.

That discrepancy was treated as a prose defect.

### Repair
The prose was amended to say that the doorway occupies the region 3 units in from the left and right grid edges, 3 units below the top, and 3 units above the bottom; the top bar occupies the upper 2 units; two 2-unit legs descend from it; the opening is 5 units; and the right leg ends 1 unit before the top bar.

## Iteration 2 — passed
The same materials were withheld again. Reconstruction used only the repaired descriptive prose.

Differing pixels: **0**.

Result: **exact match**.

## Final result
Iterations required: **2**.

The final descriptive prose reconstructs the canonical 16-unit filled geometry exactly without the coordinate rectangle list, pinned-dimension list, path strings, SVGs, PNGs, favicon, Apple touch icon, or construction sheet.
