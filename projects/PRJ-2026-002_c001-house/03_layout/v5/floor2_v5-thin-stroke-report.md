# floor2 v5 phase-2 — thin-stroke pass: can geometry recover the owner wall layer?

**Date:** 2026-07-10 · **Method:** a geometry-only thin-wall PREDICTOR scored against v4's 19
`manual_additions` as the answer key. **Honesty reframe:** this is NOT blind — the owner coords
were seen in the v5-vs-v4 diff. But the predictor keys ONLY on stroke geometry (thin width +
axis-alignment + collinear-extends / gap-fills a thick wall); it never reads v4 coords. So it is a
legitimate predictor-vs-GT measurement (the repo's standard answer-key pattern), just not a blind one.

## Probe — width + colour cannot separate walls from furniture
Stroke-width histogram on the floor-2 page: 0.12 pt ×3947, **0.48 pt ×2839**, 0.60 ×296, 0.84 ×269.
The wall gate keeps ≥ 0.6 pt. Every thin stroke is BLACK (grey band = 0) → colour is no lever, and
the owner's thin walls sit at 0.48 pt **in the same bucket as all furniture + dimension lines**.
1,331 thin axis-aligned black segments exist; only ~19 are walls → a width/colour classifier caps at
~1.4 % precision. **The only geometric hope is the gap-spanning signal.**

## Predictor — thin strokes that extend / fill a thick-wall line
Keep a thin segment if it is collinear with a thick wall (same axis, perp < 60 mm) AND adds new
coverage (fills a gap or continues the run). From 1,957 thin axis segments → **706 candidates.**

| metric | value | robustness |
|---|---|---|
| **RECALL** of the 19 owner walls | **16 / 19 = 84 %** | stable 15–16/19 across cover tolerances (not a slack artifact) |
| **PRECISION** (candidates hitting a real owner wall) | **48 / 706 = 6.8 %** | 658 furniture/detail edges also qualify |

### The 3 owner walls geometry CANNOT recover (no thin ink at all)
- `[[5654,3400],[5752,3400]]` and `[[5654,4622],[5752,4622]]` — two 98 mm caps = the **s2 sliding-door
  frame head/sill** the owner INFERRED (not drawn).
- `[[5654,-799],[5654,-149]]` — a terrace return with no ink.

These are pure owner knowledge — the machine cannot find what was never drawn.

## Verdict — the two-layer law, QUANTIFIED on a real sheet

- **Thick walls (machine): 100 % reproducible** (v5 blind ≡ v4, phase-1 diff).
- **Thin owner walls (19):**
  - **16/19 (84 %) are recoverable as CANDIDATES** — the gap-spanning geometry proposes them — **but at
    ~7 % precision**: the machine must emit 706 to contain the ~16 real ones. It can PROPOSE, it cannot
    SELECT.
  - **3/19 (16 %) have no ink** — pure owner inference (slider frame, terrace return).
- **So the owner's irreducible job is (a) SELECTION** — pick the ~16 real from 706 look-alikes, the
  judgment geometry can't make — **and (b) INFERENCE** — the 3 undrawn. This is *exactly* why the
  boundary layer is owner-signed, now measured, not asserted.

This is the same shape as the FloorPlanCAD baseline (findability ≫ precision) and validates the
`glazing_candidates` design (emit high-recall candidates for owner review; never auto-place). The
`floor2_v5-thin-predicted.json` (706 candidates) is exactly such a candidate set — a review queue,
not walls.

Artifacts: `floor2_v5-thin-predicted.json` (706 candidates), `floor2_v5-thin-predict-overlay.png`
(grey thick / orange candidates / green owner GT).
