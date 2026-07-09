# F2 cardinal_correct measured pred!=gt for the FIRST time -- closed-loop 100% on the labeled slice, and the two pred-side traps it took to get there

**Date:** 2026-07-09 · **Engines:** f2_facing_lane v1.0 (NEW) + synth_plan_2d v1.1 + svg_plan_reader v2 (UNEDITED) + facing_reader + benchmark_reader · **Corpus:** C:/Users/teza_/studio-datasets/structured3d/gt-slice-labeled (14 scenes, 215 kinded+rot, regenerated this session with the VALIDATED_2026-07-09 rot_convention stamp) · run artifacts: C:/Users/teza_/studio-datasets/structured3d/synth-f2/ · **Verification:** 835 tests green; every failure mode below reproduced live before being pinned.

## 1. The gap this closes

After the facing-convention validation (qa/reports/f2-facing-convention-validated-2026-07-09.md) the GT side of F2 was closed, but `cardinal_correct` had NEVER been computed pred!=gt on any corpus: synth plans drew bare rects (zero facing ink) and svg_plan_reader is facing-blind, so F2 read 0.0-all-unreported — a number measuring rot-emission *absence*. This lane supplies the missing pred side **without editing any file owned by the parallel session** (svg_plan_reader/kind_priors untouched; synth_plan_2d/benchmark_reader/facing_reader imported as-is):

1. **oriented_svg** — appends a back-strip `<line>` per facing-kind cardinal-rot element to the blind synth plan, placed per facing_reader's doctrine (back edge = opposite(front), inset 12% inside the 5–45% band).
2. **facing post-pass** — the UNEDITED reader runs first (`read_sheet`); then `read_ink` segments are outline-ring-filtered, clipped per pred bbox, and `facing_reader.read_facing` recovers the strip → `rot_from_facing` → pred rot.
3. **score** — `benchmark_reader.score_pair` unchanged; beds-excluded headline via `score_facing(FACING_KINDS - {'bed'})`.

## 2. Headline

| metric | value | meaning |
|---|---|---|
| **cardinal_correct (visual lane, beds excluded)** | **100.0%** | n=21: exact 21 / flipped 0 / wrong 0 / unreported 0 |
| cardinal_correct (visual lane, beds included) | 100.0% | n=27, all exact |
| facing-blind baseline (same detection set) | 0.0% | n=27 all-unreported — what F2 read before this lane |
| wall-prior lane (ORACLE-WALLS tier) | 52.4% | n=21 no-bed; a PRIOR, not a read — see §4 |

Detection context: GT 1995 vs pred 230 → matched 150 (recall 7.5%); F2 scores the matched subset only.

**What the 100% IS:** closed-loop ink recovery — the strip is drawn FROM GT rot (exactly how a real plan encodes facing), so this proves the reader pipeline + post-pass recover every facing the ink encodes, end-to-end, on the matched subset. **What it is NOT:** generalization to real-world symbol ink (FloorPlanCAD has no rot GT — that lane stays UNWIRED), and not semantic facing truth for beds (S3D bed yaw encodes length; beds score exact here *by construction*, which is why the beds-excluded row is the headline). The loop is not self-confirming: a planted 180-flip in the drawing scores `flipped` (pinned test), and the blind baseline on the same detection set is 0.0.

## 3. The real finds: two pred-side traps (both reproduced, then pinned)

The first naive run scored **66.7%** — and every failure was a **90-degree fusion spoof**, not angular noise:

- **Pred-side double-rotation** (mirror of adapter fix 9a8c4b3): attaching rot 90/270 to a pred element whose x/y/w/d is a world AABB makes `placement_gate.footprint` re-rotate it → swapped AABB → IoU<0.5 → every CORRECT 90/270 read became a detection MISS (o2/o4 vanished live). Fix: `_attach_rot` re-emits the local un-yawed rect, exactly as the adapter's kinded lane does. Pinned: `test_attach_rot_reemits_local_rect_so_footprint_round_trips`.
- **Fusion outline spoof**: a fused cluster's bbox contains NEIGHBOUR furniture outlines at interior insets, where read_facing scores them as giant strips (scene_00006 cabinet: W=6.31 from five neighbour outlines vs the true strip's N=0.77). Closed rectangle rings are therefore filtered before the read — outline ink is not facing ink (66.7% → 95.2%). The last `wrong` was a **flush-edge duplicate**: two coincident verticals at a shared furniture edge, of which the filter removed only one; the survivor read W=1.0 (scene_00005 o15). Removing every coincident side → 100%. Pinned: `test_fused_neighbour_outline_does_not_spoof_facing`, `test_ring_filter_removes_duplicate_flush_edges`.

Both traps will bite ANY future rot-emitting reader (they are properties of the matcher and of fused clusters, not of this lane) — that is the durable value of this session beyond the number.

## 4. Wall-prior lane (secondary, oracle-walls tier)

`wall_prior_pred` predicts front = away from the nearest backing wall (gap ≤ 450mm, cardinal-snapped ≤ 20°), consuming `gt['wall_lines']` → **disclosed oracle tier** (precedent: floorplancad-oracle-walls-2026-07-07.md). It scores 52.4% no-bed — far below its ~94.5% validated ceiling because that ceiling held for *wall-backed strong-front kinds on GT footprints*, while here the prior fires on ALL matched pred elements: off-wall pieces stay unreported (counted against) and near-wall weak-front kinds (chairs at tables) genuinely don't face away from the wall. It is a floor-to-ceiling reference band for the visual lane, not a competing reader.

## 5. Honest caveats (adversarially confirmed, not hidden)

- **n=27 (21 no-bed) is TINY** — low_n by the card's own flag; per-scene verdicts are meaningless, only aggregate buckets quoted. Growing n needs more labeled scenes (semantic.png beyond scene_00013 = owner download) and/or better detection recall (7.5%, the known sub-object-fusion limit).
- 7 facing-kind elements skipped strip-drawing (rot-less/non-cardinal) — counted, they simply stay out of the drawn ink; unreported still counts against cardinal_correct wherever GT is eligible.
- The ring filter keys on exact coincident coordinates (synth ink is exact); real scanned/CAD ink will need tolerance work — flagged for the FloorPlanCAD lane, not silently assumed.
- Strip presence leaks WHICH elements are facing-kinds into the ink (kind itself is never drawn); F1 is not scored on this lane, and F3 blindness is untouched (indoor flip → byte-identical SVG, pinned).
- gt-slice-labeled was REGENERATED this session so meta.rot_convention now carries the validated stamp (values unchanged; the stale pre-validation warning string is gone).

## 6. Reproduce

```
cd pipeline/scripts
python structured3d_adapter.py --batch 14 C:/Users/teza_/studio-datasets/structured3d/gt-slice-labeled C:/Users/teza_/studio-datasets/structured3d/corpus_labels_slice.json
python f2_facing_lane.py --score C:/Users/teza_/studio-datasets/structured3d/gt-slice-labeled C:/Users/teza_/studio-datasets/structured3d/synth-f2
python -m pytest pipeline/scripts -q          # 835 green
```

*Built from a 6-reader adversarial scout workflow over the F2 lane (zero edits to the parallel session's owned files); failures diagnosed live per-element before each fix; 835 tests green.*
