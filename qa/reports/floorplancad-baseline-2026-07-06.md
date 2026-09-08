# FloorPlanCAD baseline — OUR reader vs machine ground truth (first real numbers)

**Date:** 2026-07-06 · **Engine:** `pipeline/scripts/svg_plan_reader.py` v1 →
`benchmark_reader.py` · **Corpus:** FloorPlanCAD v2 test split, 5,502 sheets
(`C:\Users\teza_\studio-datasets\floorplancad\`, run artifacts in `baseline-test-00\`:
per-sheet `cards.jsonl`, `preds/`, `overlays/`, `report.md`) · **Wall-clock:** 865 s

The first time any of our reads has been scored by a machine instead of the owner's eye:
2,245 mm-calibrated sheets (10,347 GT furniture instances, 10,235 GT typed openings)
scored against the adapter's answer keys. The 3,257 sheets the adapter could not
calibrate to mm were **skipped and counted** — mm-threshold morphology on unknown-scale
ink would be noise wearing numbers.

## What was measured (and what "our reader" means)

No new intelligence was built for the benchmark. The reader is the production stack,
fed raw SVG ink **annotation-blind** (the corpus SVGs carry the answer key inline;
blindness is enforced by a behavioral strip-equivalence test through `read_sheet` plus
a static string scan — `test_svg_plan_reader.py`):

- **elements** — `plan_cluster.cluster_segments`, the same rasterize→CLOSE→label
  morphology the placement gate trusts (res parameterized, capped at 3,000 px/axis).
- **openings** — `glazing_candidates.promote` pair-runs with an EMPTY wall set (this
  corpus draws every stroke at width 0.1: the PDF lane's 0.6 pt wall gate has no signal
  here), emitted as `type="candidate"` — deliberately outside the F4 vocabulary.
- **identity** — none. Production identity is owner-signed semantic truth; the reader
  emits no `kind`.
- scale per sheet comes from the gt manifest (calib-from-manifest, same pattern as the
  gate; the adapter derived it from unannotated dimension ink).

## Numbers

| Metric | Result | Reading |
|---|---|---|
| detection recall | **9.8 %** (1,014/10,347) | wall-connected symbols merge into the sheet-wide wall component and die in the `merged_blob` screen; only free-standing furniture survives |
| detection precision | 14.3 % (1,014/7,097) | dim blocks / annotation symbols cluster as phantoms |
| F1 identity | **0.0 %** on 1,014 matched | structural: no classifier exists. The baseline to beat, not a bug |
| F4 recall (all openings) | 44.6 % (4,569/10,235) | |
| F4 — **sliding** | **87.8 %** (733/835) | the F4 wound is geometrically FINDABLE by the existing pair-run lane |
| F4 — window | 90.2 % (2,850/3,160) | parallel-line symbols = pair lane's home turf |
| F4 — bare opening | 78.4 % (91/116) | |
| F4 — hinged door | **14.6 %** (895/6,124) | arc-and-leaf symbols have no parallel pair; lane was never designed for swings |
| F4 precision | **2.9 %** (159,582 candidates) | with no wall set, every wall face pair scores ≥2 — the flood is the price of the empty-wall run |
| F2 / F3 / F5 | UNWIRED | corpus carries no rot / indoor / floor GT — waits on 3D-FRONT / Structured3D / Thai lanes |

Per-sheet F4 verdicts: 0 PASS (subtype accuracy is structurally 0 for an untyped
candidate lane, so no sheet can rubber-stamp) — verified `subtype_accuracy > 0` on
**zero** of 2,245 cards.

## What the numbers actually say

1. **The two-layer split now has numbers.** Geometric findability of thin-line openings
   (sliding 87.8 %, window 90.2 %) is already high with zero new code; identity (F1 0.0)
   and typing (subtype 0) are the semantic layer, exactly where the owner-signed ledger
   lives. The machine's next wins are precision and swing-door geometry, not a rebuild.
2. **Detection is wall-context-starved, not morphology-broken.** The 9.8 % recall is
   dominated by wall-merge deaths: this corpus gives no stroke-width wall signal, and
   the reader was run without any wall extraction. The PDF lane (which HAS the width
   gate) does not inherit this number.
3. **Precision 2.9 % is the honest cost of no wall suppression** — `covered_by_walls`
   had nothing to suppress with. Wiring any wall hypothesis (even the corpus's own
   1=wall stuff channel as an ORACLE lane, clearly labeled) would collapse the flood;
   that is the next slice's cheapest lever.

## Scrutiny record (2 rounds)

Round 1 (6 lenses; 8 agents lost to a spend-limit outage, findings recovered from the
journal and verified inline): 5 confirmed defects, all fixed + pinned —
(1) `type='opening'` sentinel collided with the real F4 subtype vocabulary and earned
unearned subtype credit (5/15 smoke sheets, a verdict flip) → `type='candidate'`;
(2) static blindness guard could not bind (attribute names live in string literals) →
behavioral strip-equivalence test through `read_sheet`; (3) one corrupt gt.json killed
the whole run and lost every completed row → per-sheet try + rows stream to
`cards.jsonl`; (4) CLI typo → raw traceback → usage exit; (5) `_zero_mask` converted
mask rects with global RES while the raster used the caller's res (latent, silent
mislocation both directions) → res threaded through.

Round 2 (mutation lens + per-fix adversarial verification, after the corrected rerun):
4/5 fixes verified holding; the blindness fix was proven **under-dense** — a leak gated
on >10 annotated attrs slipped the 3-attr fixture while firing on 89.5 % of real sheets
→ added a 4,100-prim dense twin (above the corpus max 3,905) + a real-corpus-sheet twin.
5 surviving mutants (self-referential res-cap assert, uncounted error rows, two per-type
recall corruptions incl. a gt/pred index-set inversion that would flip the sliding
headline, and the density leak) → all killed and pinned; every killer was verified to
fail on its mutant and pass on pristine code. One residual hardened: an overlay render
failure no longer error-counts (or double-rows) an already-scored sheet. Suite: 465.

## Next slices (in leverage order)

1. **Wall-aware second pass** — give `promote()` a wall set (corpus wall-stuff as a
   labeled oracle lane first, our own thin-wall extraction later): F4 precision is the
   single number that moves.
2. **Swing-door geometry** — arc+leaf detector (quarter-circle + radial leaf) for the
   14.6 % door recall; the adapter's arc-sampling machinery already exists.
3. **Deterministic size/curve identity priors** (wardrobe 2.1×0.56 m etc.) to put a
   first honest nonzero on F1 — priors are cited rules, not a learned classifier.
4. svg-unit sheets stay out until a second calibration anchor lands (door-band pattern).
