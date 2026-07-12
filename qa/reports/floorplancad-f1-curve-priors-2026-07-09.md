# FloorPlanCAD F1 — curve-signature prior: a VERIFIED NEGATIVE (size+curve still can't identify furniture)

**Date:** 2026-07-09 · **Engine:** `svg_plan_reader.py` + `kind_priors.py` v2 (curve tie-break)
→ `benchmark_reader.py` · **Corpus:** test-00, 2,245 mm sheets (1,014 IoU-matched pairs) ·
**Curve signatures derived from:** gt-train-00 + gt-train-01, 3,525 mm sheets, 1,500 matched
train pairs, 11 kinds ≥20 pairs · **Artifacts:** `.../priors/kind-priors-train-curve.json`,
`.../baseline-test-00-curve/`, `.../baseline-test-00-sizeonly-v2/` (outside repo, CC BY-NC)

Follow-up to the 2026-07-07 F1 size-priors slice (0.0%→0.4%), whose "Next" and
`kind_priors.py`'s own docstring both deferred a curve signature. Built it, ran it, and it is
an **honest negative**: curve does not improve identity on this corpus.

## Result: F1 0.4% → 0.4% (no gain; precision slightly WORSE)

| | size-only (@0.1) | size **+ curve** (@0.2) |
|---|---|---|
| F1 accuracy on 1,014 matched | 0.4% (4 correct) | **0.4% (4 correct)** |
| kind emitted | 85/1,014 | **96/1,014** (+11) |
| emitted precision | 4.7% | **4.2%** (worse — the +11 were all wrong) |

The +11 curve-resolved emissions were wrong (mostly `stairs` 46→54: a large element tied
{stairs=ambiguous, elevator=boxy} resolves to stairs on curve, but stairs precision fell
6.5%→5.6%). **Verified not a bug:** detection (GT 10,347 vs pred 7,097 → matched 1,014, recall
9.8%, precision 14.3%) and F4 (matched 7,991, door 70.4%, sliding 87.8%, window 90.2%) are
**byte-identical** across both runs — the edit touched only `kind`.

## Why it fails (three honest reasons)

1. **The probe lied at small scale.** The 250-sheet probe showed chair 100% curved; at scale
   (389 train chairs) chair is **22% curved — AMBIGUOUS**. So curve cannot break the chair/table
   size overlap that is the biggest identity wound (chair = 334 GT, the largest matched class).
2. **The kinds curve CAN split have no detections.** Curve cleanly separates curved fixtures
   (squat_toilet 100%, sink 98%, toilet 94%, refrigerator 100%, bed 100%) from boxy items
   (air_conditioner 1%, elevator 7%). But every one of those curved fixtures has ~0% detection
   recall on test — a correct disambiguation lands on an element that was never matched.
3. **F1 is detection-bound, not classifier-bound.** Only 1,014 of 10,347 GT furniture are
   matched at all (9.8% recall — wall-merge deaths). Even a perfect classifier on that thin,
   geometry-ambiguous matched set caps F1 low. The lever is upstream (detection) or the
   owner-signed ledger — not richer geometry priors.

## What this is worth (the salvage)

- **Reinforces the two-layer thesis empirically, harder:** size AND curve — the two strongest
  geometry signals a plan symbol carries — still cannot identify furniture. Identity is the
  owner-signed semantic layer, exactly as the 07-07 report predicted ("the real identity lever
  remains the owner-signed ledger"). This is now measured, not asserted.
- **A real diagnostic artifact:** per-kind curve fractions (which CAD furniture is drawn with
  arcs). curved = squat_toilet/sink/toilet/refrigerator/bed; boxy = AC/elevator; ambiguous =
  chair/table/sofa/cabinet.
- **A tested, reusable, backward-compatible capability** (`kind_priors` v2 + `derive_curve_priors.py`,
  90 tests): if a future corpus lands with real detection recall, curve tie-breaking is ready.

## Disposition

- **`kind-priors-train.json` (size-only, @0.1) stays the priors of record.** The curve doc made
  precision worse; it is NOT adopted as default. `kind_priors` v2 is backward-compatible
  (curve OFF unless a curve-signature doc is passed; size-only lane byte-identical — the 0.4%
  reproduced exactly on current code, `baseline-test-00-sizeonly-v2/`).
- **Do not re-attempt geometry identity priors on FloorPlanCAD** without first fixing detection
  recall. Next real identity lever = owner-signed ledger (`confirmed_kind`) or a detection pass.

## Honesty note

This was a benchmark-YARDSTICK investigation (flagged as such before it started), not a
real-goal (end-to-end 2D→3D) move. It returned negative. Recording the negative + the diagnostic
is the value; the F1 number did not move.

reader: svg_plan_reader · priors: kind_priors v2 (@0.2 curve) · suite: 90 passed
