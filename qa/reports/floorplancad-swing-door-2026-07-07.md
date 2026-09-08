# FloorPlanCAD — swing-door arc lane (the majority F4 class, typed on earned evidence)

**Date:** 2026-07-07 · **Engine:** `svg_plan_reader.py` v2 (`swing_door_candidates.detect`)
→ `benchmark_reader.py` · **Corpus:** test-00, 2,245 mm-calibrated sheets (gt-test-00-w1)
· **Artifacts:** `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-01\`
· **Wall-clock:** 928 s

The pair-run lane could never see a swing door — an arc-and-leaf symbol has no parallel
face pair. Hinged doors are the **majority F4 class** (6,124 of 10,235 GT openings) and sat
at 14.6 % recall. `swing_door_candidates.detect` finds a quarter-arc (sampled via the shared
W3C F.6.5 `arc_center_params` sweep, never the chord) whose radius matches a radial leaf
line — or a mirrored double-arc — and emits a **typed** `type="door"` candidate.

## Blind lane: before vs after the swing lane

| Metric | Blind (2026-07-06) | + swing lane | Δ |
|---|---|---|---|
| detection recall/precision | 9.8 % / 14.3 % | 9.8 % / 14.3 % | IDENTICAL (swing touches openings only) |
| F4 recall (all openings) | 44.6 % (4,569/10,235) | **78.1 % (7,991/10,235)** | **+3,422 matched** |
| **F4 — hinged door** | **14.6 % (895/6,124)** | **70.4 % (4,312/6,124)** | **+3,417 — the headline** |
| F4 — sliding | 87.8 % (733/835) | 87.8 % (733/835) | unchanged (no regression) |
| F4 — window | 90.2 % (2,850/3,160) | 90.2 % (2,851/3,160) | unchanged |
| F4 — bare opening | 78.4 % (91/116) | 81.9 % (95/116) | +4 |
| F4 precision | 2.9 % (4,569/159,582) | **4.9 % (7,991/164,361)** | UP — swing adds ~3.4k true matches for ~4.8k candidates |

## The subtype credit is EARNED, not fabricated

The repo's recurring wound is unearned subtype credit (the retired `type="opening"` sentinel
silently scored against GT bare-opening symbols). The swing lane emits `type="door"` ONLY on
real arc+leaf / mirrored-double geometry. Corpus-wide subtype confusion (GT type → pred type,
mismatches only) proves it:

- swing `door` preds that matched a GT **door**: **3,727** (subtype HITS — the earned credit)
- swing `door` preds that matched a **non-door** GT: **5** total (4 `opening→door`, 1 `window→door`)
- → type-precision on matched pairs ≈ **99.87 %**; the remaining matched doors (585) were
  found by the untyped pair lane (`door→candidate`), which claims no subtype credit.

Pair-lane openings still ship `type="candidate"` (outside the GT vocabulary → zero subtype
credit); the two lanes never blur. A per-sheet F4 PASS still needs recall AND precision ≥ 0.9,
which the empty-wall candidate flood keeps out of reach until the wall-aware pass (item A) —
so the geometric win shows in recall/precision, not the verdict column (still REVIEW).

## Honesty invariants held

- No rot/facing/indoor/floor key on any emitted opening (F2 invisibility; pinned).
- Annotation-blind: `read_ink` collects arcs from path geometry only; strip-equivalence
  twins + static tripwire green. Detection lane byte-unchanged (elements never see arcs).
- Adapter `gt.json` emission unchanged by the shared `arc_center_params` refactor (selftest
  5,502/5,502, gt equivalence preserved) — the swing slice reads arcs, never re-types GT.

## Next

- The door miss (29.6 %) is line-only doors (arc without a drawn leaf) + non-quarter sweeps;
  a follow-up tier can admit arc-only evidence as weak `candidate` (untyped) without claiming
  door credit.
- Wall-aware pass (item A) is the precision lever; swing is the recall lever — they compose.

reader: svg_plan_reader v2 · suite: 514 passed
