# AEP — Canonical Specification

## Status
AEP is the open agent endpoint mark. The design is fixed: V7, an asymmetric, feetless, open doorway.

This document is normative and is sufficient to redraw the mark without an image or SVG.

## Meaning
On a public site, AEP asserts that the site exposes a direct endpoint intended for agent queries. The public site mark has one state only: **open**. If AEP is absent, no assertion is being made. Absence is the negative state.

A closed state exists only for verifier interfaces and is **not for use on sites**.

## Canonical 16-unit construction
Construct AEP on a square coordinate system from `(0,0)` to `(16,16)`. One grid unit equals one pixel at the primary 16 px size. All coordinates and dimensions are integers.

The canonical doorway occupies the region from 3 units in from the left edge of the grid to 3 units in from the right edge, and from 3 units below the top edge to 3 units above the bottom edge. Its top bar occupies the upper 2 units of that region. From the underside of that bar, two vertical legs descend to the bottom of the region. Both legs are 2 units thick. The left leg is flush with the left end of the top bar. The clear opening between the legs is 5 units wide. The right leg ends 1 unit before the right end of the top bar.

The filled shape is the union of three rectangles:
1. **Top bar:** x = 3 through 13, y = 3 through 5. Width 10 units; thickness 2 units.
2. **Left leg:** x = 3 through 5, y = 5 through 13. Width 2 units; height 8 units.
3. **Right leg:** x = 10 through 12, y = 5 through 13. Width 2 units; height 8 units.

Equivalent single-path perimeter: `M3 3 H13 V5 H12 V13 H10 V5 H5 V13 H3 Z`

### Pinned dimensions
- Overall visible width: **10 units**, from x = 3 to x = 13.
- Overall visible height: **10 units**, from y = 3 to y = 13.
- Top bar thickness: **2 units**.
- Left leg thickness: **2 units**.
- Right leg thickness: **2 units**.
- Opening width at the base: **5 units**, from x = 5 to x = 10.
- Asymmetry offset: **1 unit**.

### Asymmetry
The V7 asymmetry is exactly one grid unit. The left end of the top bar is flush with the outside edge of the left leg at x = 3. On the right, the leg ends at x = 12 while the top bar ends at x = 13, creating a 1-unit right overhang and no left overhang.

Keep that relationship exactly when redrawing: do not center the top bar, mirror the overhang, or redistribute it. At 16 px the offset is one device pixel, so it is intentionally subtle rather than a feature that should appear visually exaggerated.

## 12 px optical drawing
At exactly 12 px, use this separate integer-grid drawing on a 12 × 12 grid rather than proportionally scaling the 16-unit drawing:
- Top bar: x = 2 through 10, y = 2 through 4.
- Left leg: x = 2 through 4, y = 4 through 10.
- Right leg: x = 7 through 9, y = 4 through 10.
- Opening width: 3 units.
- Asymmetry: 1-unit right overhang, 0-unit left overhang.
- Overall visible size: 8 × 8 units.
- Equivalent path: `M2 2 H10 V4 H9 V10 H7 V4 H4 V10 H2 Z`.

## SVG requirements
Use filled geometry, one path where possible, `fill="currentColor"`, `viewBox="0 0 16 16"`, no root width/height, transforms, clip paths, groups, IDs, classes, or comments; target under 500 bytes.

Canonical SVG:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M3 3h10v2h-1v8h-2V5H5v8H3Z"/></svg>
```

## Rasterization verification
At 16 px, one grid unit maps to one device pixel, so every canonical edge lands on an integer pixel boundary.

The delivered PNG exports at 12, 16, and 24 px were opened from the emitted files after export. Their pixel dimensions were confirmed as 12 × 12, 16 × 16, and 24 × 24 respectively. The 12 px file uses the explicit 12-unit optical drawing. The emitted 16 px file contains only alpha values 0 and 255, confirming no geometry-induced anti-aliasing at the primary size. The 24 px file was opened successfully and its rendered geometry was confirmed to match the canonical proportions at 1.5× scale.

## Color and contrast
AEP is monochrome and inherits one color from context. No two-tone treatment, fixed canonical color, gradient, or outline variant. Maintain at least **3:1 contrast** against the immediate background, per WCAG non-text contrast.

## Sizing
Hard minimum: **12 px**. Primary size: **16 px**. Any size at or above 12 px is permitted; at exactly 12 px use the dedicated optical drawing.

## Clear space
The 3-unit inset already present between the visible 10 × 10 mark and every edge of the canonical 16 × 16 viewBox **fully satisfies the clear-space requirement; no additional external clear space is required when the complete viewBox is preserved**.

The minimum clear space is one leg thickness (2 units), so the canonical viewBox exceeds the minimum by 1 unit on every side.

## State
**Public sites:** open mark only. Absence makes no assertion.

**Verifier UI only:** a verifier may show a closed state for “not verified / stale” only at **32 px or larger** and with contextual labeling. It occupies the same 10 × 10 visible footprint: x = 3 through 13, y = 3 through 13. It is **not for use on sites**.

## Usage rules
Permitted: any single color, any size at or above 12 px, use by anyone including competitors, no permission or attribution required.

Prohibited by this specification: logo lockups inside or beside the mark, turning it into a proprietary brand mark, animation, rotation, mirroring, text inside it, altered proportions, or outline versions.

## Documented visual similarities
### Greek capital pi
Geometrically related in isolation, but not treated as a practical collision: pi normally appears in running text, mathematics, and notation rather than as a standalone capability signal in browser chrome, toolbars, or footer rows.

### Architectural door / exit pictogram
Intentional borrowed equity. Some readers may initially parse it as “exit” rather than “entrance”; context supplies direction.

### U-shape / open-box container icons
Weak structural similarity; typical contexts and open-side geometry differ.

## License and trademark
Dedicated under CC0 1.0 Universal; see [LICENSE](LICENSE). No trademark is
claimed over the name AEP or over the artwork; see [NOTICE.md](NOTICE.md).

The usage rules above describe conformity to this specification. They are not
license conditions and are unenforceable by design.

## Files

| Path | What |
|---|---|
| `svg/aep.svg` | Canonical 16-unit open mark. Use this by default. |
| `svg/aep-12.svg` | The 12 px optical drawing. Use at exactly 12 px. |
| `svg/aep-closed-verifier.svg` | Closed state. Verifier UI only, 32 px and up. |
| `png/aep-{12,16,24,32,48,64,128,256,512}.png` | Raster exports. |
| `png/aep-180-apple-touch-icon.png` | Apple touch icon. |
| `favicon.ico` | Multi-resolution, 16/32/48. |
| `construction/aep-construction.png` | Annotated construction sheet. |

## Redraw test
The redraw test reconstructs AEP from descriptive prose while withholding the canonical rectangle list, pinned-dimensions list, path strings, all image/vector assets, and the construction sheet. See `REDRAW-TEST.md`.
