# Structured3D adapter — backwards-benchmark GT lane (2026-07-08)

`pipeline/scripts/structured3d_adapter.py` (+ `test_structured3d_adapter.py`) is the SECOND
corpus adapter for `benchmark_reader.py`, after `floorplancad_adapter.py`. It converts
Structured3D `annotation_3d.json` (+ `bbox_3d.json`) into the benchmark's `gt.json` schema,
grounded in the real data and proven selftest-clean.

## What this WIRES (new)

- **F3_indoor — first time on ANY corpus.** FloorPlanCAD carried no indoor/floor/rotation
  GT, so F2/F3/F5 scored UNWIRED everywhere. Structured3D's per-room floor polygons +
  balcony/garden OUTDOOR semantics give a machine-checkable `indoor` bool per element
  (point-in-room-polygon of the bbox centroid). This is the answer key for the exact class
  of error the v4 self-audit review flagged live (terrace-vs-lounge, balcony-vs-bedroom).
- **F4_openings** — door + window boundary semantics → `{type, x, y, w, d}`.
- **F6_glazing** — the single `outwall` semantic's floor-level wall segments → `glazing_lines`.

Selftest verdicts (gt-vs-gt, 200 scenes): **detection PASS, F3_indoor PASS (n>0),
F4_openings PASS, F6_glazing PASS; F2_facing UNWIRED, F5_floor UNWIRED; F1_identity
identity-blind** (per_kind keys ⊆ {""}). Aggregate: det recall 1.0, F3 acc 1.0, F4 recall
1.0, F6 recall 1.0.

## What stays BLOCKED and why

- **F1_identity — identity-blind, NOT scored as real identity.** `bbox_3d.json` carries NO
  per-object class label (labels live in the un-downloaded render zips). Elements are
  emitted with NO `kind` key. `score_identity` has no empty-kind guard, so kind-less matched
  pairs score as a single `""` bucket and verdict PASS on gt-vs-gt — this is NOT a real F1
  score. The adapter/selftest asserts no REAL class was fabricated (per_kind ⊆ {""}); it
  never claims F1 UNWIRED (impossible while geometry matches). Honest label: identity-blind.
- **F2_facing — UNWIRED.** No kind ⇒ no facing to score; `rot` (computed for provenance) is
  omitted, so `score_facing` skips every element. Unblocking needs render-zip class labels
  (or 3D-FRONT).
- **F5_floor — UNWIRED.** Corpus is single-storey; every element would be `floor=True`, an
  uninformative metric. The `floor` key is omitted so F5 honestly reports UNWIRED (house
  doctrine: no silent pass).
- **This is the GT half only.** There is no reader-vs-S3D score yet — a 2D-plan SYNTHESIZER
  (render/rasterize the S3D scene into a plan our reader can ingest) is still needed before
  real reader-vs-S3D numbers exist. What lands today is a clean, regressable GROUND-TRUTH
  lane that F3/F4/F6 can score against once that synthesizer exists.

## Corpus stats (first 200 scenes → `C:/Users/teza_/studio-datasets/structured3d/gt-sample`)

- 200/200 converted, 0 parse-failed, 0 scenes missing a bbox file (in this slice).
- **elements** 26,946 · **openings** 2,433 (door 1,255 / window 1,178) · **glazing** 2,738
- **rooms** by type: bedroom 284, undefined 205, bathroom 203, living room 163, balcony 129,
  kitchen 115, study 38, store room 19, dining room 10, corridor 9, studio 8, garden 1.
- **element indoor split**: True 19,348 / False 954 / unknown-or-no-key 6,644.
- skips (counted, not dropped silently): zero-area footprints 3; centroids in no room 2,692
  (indoor key omitted — wall-embedded / boundary bboxes); room polygons failed to close 0.

## coeffs-units verdict applied

**coeffs are mm half-extents — NO rescale.** Per the verified 50-scene/7,947-object scan
(median object max-horizontal-dim 447 mm; 20% <100 mm genuine decor; 61% in the 300–3000 mm
furniture band; object 0 = a real ~38 mm table-top prop, not a scaling artifact). `meta.units
= "mm"`, so benchmark_reader's default 300 mm opening tol + 250 mm glaze-perp tol apply with
no caller-supplied `open_tol`. Large >10 m boxes (whole-wall/floor-spanning annotations) are
tolerated as-is, never rescaled.

## Honesty caveats

- 21/200 scenes contributed no F3-eligible element (only `undefined` rooms, or all centroids
  in no room) — legitimately no indoor data, not a silent pass. The selftest now holds each
  WIRED channel to a **coverage floor** (carry on ≥50% of eligible files), not a `>0`
  total-death check: F3 179/200, F4 200/200, F6 200/200 clear it; a regression that silently
  collapses emission to a handful of scenes now FAILS the gate (it used to pass green).
- Footprints are axis-aligned; the earlier claim that the 2D footprint is rows-vs-columns
  **interpretation-invariant is RETRACTED** — it was true only for the sub-40 mm decor sampled
  on scene_00000. At corpus scale the footprint is invariant for properly-yawed / freely-
  rotated boxes (all 833 gave diff 0.0, AABB exact) but **NOT** for tipped / axis-swapped
  boxes: **470 of 26,949 objects (~1.7%) diverge by >50 mm**, 11 furniture-scale (400–1,731 mm;
  worst scene_00160 obj52 [208,33,898] → ROWS 1796×416 mm vs COLS 65×1796 mm). The adapter
  deliberately COMMITS to the ROWS = SUN RGB-D / Structured3D corner convention and now COUNTS
  the divergent population into `meta.transpose_divergent` (batch total 470) instead of
  claiming invariance.
- `centroid_in_no_room` (2,692) is expected: many bboxes are wall-embedded frames/panels
  whose centroid falls outside every room polygon; those emit a footprint but no indoor key.

## Selftest / honesty hardening (2026-07-08 review)

- **F1 aggregate surfaced loudly.** `benchmark_reader.aggregate()` strips `per_kind`, so a
  corpus rollup of these cards reads `F1_identity {n=26,946, accuracy=1.0}` with no signal it
  is the kind-less `''` bucket. The selftest now prints an explicit `F1 identity-blind …
  NOT a real identity score; do not roll up as solved` line so no consumer mistakes it for a
  solved, high-n identity metric. (The empty-kind guard would have to live in
  `benchmark_reader.score_identity`; emitting no `kind` remains the correct non-fabricating
  choice here.)
- **Per-file guard in the selftest.** One corrupt/foreign `*.gt.json` (interrupted write,
  disk-full, stray file) now costs ONE `SELFTEST-FAIL` row and the run continues, mirroring
  `run_batch` — it no longer aborts the whole regression gate on a `JSONDecodeError`.
- **`NO_BBOX_SCENES` wired.** Previously prose-only; `run_batch` now warns if a discovered
  no-bbox scene is not in the enumeration, so the constant can't silently go stale.
- **Selftest ⊕ unit tests are a pair.** gt-vs-gt is a SCHEMA / honesty-contract check: it
  cannot catch drift symmetric across `gt==pred` (a coordinate-convention flip, a units
  error, an over-emitted indoor flag all self-match distance 0). The correctness anchor is the
  synthetic unit file (exact-pinned projection math + indoor True/False/no-key pins). Run both.

## Files

- `pipeline/scripts/structured3d_adapter.py`
- `pipeline/scripts/test_structured3d_adapter.py` — 7 tests pass (incl. real scene_00000 +
  transpose-divergence counter)
- `C:/Users/teza_/studio-datasets/structured3d/gt-sample/` — 200 `*.gt.json` + manifest.jsonl + summary.md
