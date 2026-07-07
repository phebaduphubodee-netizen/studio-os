# FloorPlanCAD — ORACLE-WALL lane (wall-aware promote() ceiling measurement)

**ORACLE LANE — uses GT-side wall geometry. NOT the blind headline; the honest
baseline of record remains `floorplancad-baseline-2026-07-06.md`.**

**Date:** 2026-07-07 · **Engine:** `svg_plan_reader.py` v1 `walls oracle` →
`glazing_candidates.promote()` with the adapter's new `wall_lines` channel
(class 1 = wall, both stuff and instanced; curtain_wall deliberately excluded — it is
glazing ink) · **Corpus:** same 5,502-sheet test-00 split, gt regenerated as
`gt-test-00-w1` (adapter v1.1; 3-file equivalence EQUAL, selftest PASS 5,502/5,502)
· **Artifacts:** `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle\`
· **Wall-clock:** 428 s (blind: 865 s — fewer candidates, less downstream work)

## Blind vs oracle (same 2,245 mm-calibrated sheets; skips identical: svg-unit 3,257)

| Metric | Blind (2026-07-06, headline) | Oracle walls | Δ |
|---|---|---|---|
| detection recall | 9.8 % (1,014/10,347) | **9.8 % (1,014/10,347)** | IDENTICAL (required: walls must not leak into the element lane) |
| detection precision | 14.3 % (1,014/7,097) | **14.3 % (1,014/7,097)** | IDENTICAL |
| F1 identity | 0.0 % on 1,014 | 0.0 % on 1,014 | structural (no classifier) |
| F4 recall | 44.6 % (4,569/10,235) | **45.1 % (4,617/10,235)** | +48 matched |
| **F4 precision** | **2.9 % (4,569/159,582)** | **3.4 % (4,617/135,931)** | **n_pred −23,651 (−14.8 %); precision +0.5 pt (+17 % rel)** |
| door recall | 14.6 % (895/6,124) | 15.3 % (938/6,124) | +43 (wall-contact runs catch some leaf ink) |
| sliding recall | 87.8 % (733/835) | 88.1 % (736/835) | floor was ≥78 % — held |
| window recall | 90.2 % (2,850/3,160) | 90.3 % (2,852/3,160) | floor was ≥80 % — held |
| bare opening recall | 78.4 % (91/116) | 78.4 % (91/116) | unchanged |

Oracle wall segs fed: **153,410** (9,456 diagonal/unusable — `axis_run=None`,
contribute nothing to suppression or contact). Row labeling: 5,502/5,502 cards rows
carry `wall_source="oracle"`, 0 unlabeled.

## Score histogram (why the ceiling is modest)

Blind lane could only produce scores 2 (pair) and 3 (pair+length). Oracle:

| score | count | reading |
|---|---|---|
| 2 | 38,991 | pairless contact-only runs (dim lines spanning wall-to-wall) — NEW flood source the contact term admits |
| 3 | 55,211 | pair+length, no wall evidence |
| 4 | 28,051 | wall-anchored pairs |
| 5 | 13,678 | wall-anchored pairs + length — the highest-confidence family |

Coverage suppression killed **36,203** wall-face runs (`dropped_wall_covered`), but the
contact term re-admitted ~12.5 k pairless score-2 candidates, so net n_pred fell only
14.8 %. **The finding (reported, not tuned around):** with mm-true walls, the flood is
NOT dominated by suppressible collinear wall-face pairs — most of it is furniture/dim
pair-runs that carry no wall relationship at all. The oracle CEILING for wall-aware
precision via the current promote() scoring is ~3.4 %; a big precision jump needs
either tier-filtering on the consumer side (scores 4–5 only: 41,729 candidates, a
−74 % flood cut worth measuring in a follow-up) or a typed classifier (separate slices).
No promote() constant was tuned (several are boundary-pinned by tests; tuning is an
owner-visible slice).

## What this licenses next

1. `wall_source="self"` — an honest own-ink wall-hypothesis lane (annotation-blind by
   construction), eligible to replace the blind headline if it beats it.
2. The swing-door arc+leaf detector (PLAN-swing-door-arc-lane) — door recall 15.3 % is
   still the majority-class wound; walls alone barely move it.
3. Tier-aware F4 scoring (consume only score ≥4 when walls exist) — measured, labeled,
   separate slice.

reader: svg_plan_reader v1 · adapter: floorplancad_adapter v1.1 · scrutiny: 0
blocker/major, 8 minors → guards + label fixes applied, 2 test gaps mutation-pinned
(strict `gt["wall_lines"]` indexing; skip/error-row labeling)
