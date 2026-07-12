# FloorPlanCAD wall lane — a VERIFIED NEGATIVE (the synth wall detector does NOT transfer to real CAD, and wall-merge is a MINORITY of the recall loss)

**Date:** 2026-07-10 · **Engine:** `wall_detect.detect_walls` + `svg_plan_reader.read_ink/read_sheet`
+ `benchmark_reader.match_elements` (all imported UNCHANGED — read-only wrapper smokes, zero
edits to any script) · **Corpus:** `gt-test-00-w1` (5,502 gt.json, the wall-enriched
regeneration that carries `wall_lines`) + `test-00` SVGs, mm-calibrated sheets only ·
**Artifacts (scratchpad, not repo):** `fpc_wall_transfer_smoke.py`, `fpc_recall_decomp.py`

## Why this was run

Session-opening option A proposed: *un-oracle `svg_plan_reader --baseline walls oracle` on
real FloorPlanCAD sheets — port the synth `blind_wall_lane` doctrine (detect → mask → barrier,
`wall_detect` = gap-window + ring-pair veto + mutual-best) to real ink to lift the 9.8%
detection recall that `floorplancad-f1-curve-priors` attributed to "wall-merge deaths."*

Before spending the estimated 1–2 sessions, two premises under A were tested (both had been
ASSERTED, never measured on this corpus): **(1) does the synth wall detector find real CAD
walls at all?** and **(2) is the recall loss actually caused by wall-merge?** Both returned
negative.

## Premise 1 — detector transfer: FAILS (10.2% wall recall)

`detect_walls` on real CAD ink (60 mm sheets), detected centerlines scored vs gt `wall_lines`
by the module's own `coverage_vs_gt`:

| | value |
|---|---|
| wall recall (length-weighted) | **10.2%** |
| gt walls zero-covered (real, ≥ MIN_LINE) | **3,482 / 4,034** |

**Verified not a scale/harness bug:** the recall-decomposition harness below shares the exact
`read_ink → ×scale_mm_per_unit` path and reproduces the committed furniture recall band
(9.4% on 80 sheets vs committed 9.8% full-corpus), so the mm scaling is correct — the 10.2% is
a genuine transfer failure. Confirmed independently by the detector's own internal stats over
40 sheets:

| detector stage | count | note |
|---|---|---|
| `n_segs` | 202,766 | real CAD ink |
| `n_short` (< MIN_LINE_MM = 80) | **184,182 (90.8%)** | discarded before pairing |
| `pairs_checked` | 243,527 | |
| `pairs_geo_ok` | **2,097 (0.86%)** | pass the double-line window |
| `pairs_accepted` | 966 | |

**Mechanism (corpus-level, not sample noise):** the detector is built for the synth
convention — walls DRAWN by `append_wall_ink` as long, clean, end-aligned parallel `<line>`
faces exactly `WALL_T_MM = 100 mm` apart. Real CAD (a) draws everything as *many short
segments* (90.8% below the 80 mm floor — polyline vertices, hatching, sampled arcs, detail),
and (b) does not present wall faces as clean matched pairs (parallel + gap ∈ [50, 250] +
constant-offset ± 15 + end-aligned ± 5 + length-ratio ≥ 0.85) — real faces are cut by doors,
columns, joins and dimension lines, so < 1% of survivor pairs pass. **This is an architecture
mismatch, not a parameter tune.** A real-CAD wall detector would key on a different signal
(lineweight / stroke-width, layer geometry, or hatch/fill regions) — genuinely new work, not a
port.

## Premise 2 — is wall-merge the recall killer? NO, it is a minority (≤ 40.5%, upper bound)

Real reader (`read_sheet`) run, IoU-matched vs gt; every UNMATCHED (missed) gt element
categorized by whether wall-masking could *even plausibly* recover it. `WALL_ADJ` is a loose
UPPER BOUND — "a gt wall passes within 200 mm of the footprint" — proximity ≠ merge-death
(beds, sofas, cabinets sit against walls regardless of why they went undetected).

| bucket | 80 sheets | 300 sheets | wall-mask can recover? |
|---|---|---|---|
| DECOR (< 150 mm, below reader screen) | 0.0% | **0.0%** | no |
| WALL_ADJ (wall ≤ 200 mm — merge upper bound) | 53.1% | **40.5%** | maybe (upper bound) |
| ISOLATED (no wall near) | 46.9% | **59.5%** | **no** — reader detection failure |
| — of which ≥ 500 mm real furniture | 142 | **634** | |

At the larger sample the wall-merge upper bound *fell* (53.1 → 40.5%) while the
wall-independent failure *rose* to a **majority (59.5%)** — the honest direction (a flattering
result would have moved the other way). Even a *perfect* real-CAD wall detector therefore caps
the recall gain at ≤ 40.5% of misses (true share lower), because the dominant wound — ≥ 59.5%,
including 634 large isolated furniture items with no wall anywhere near — is the reader's
`plan_cluster` morphology failing to detect real CAD symbols, which no wall work touches.

## What this is worth (the salvage)

- **Closes option A with evidence in ~4 min of compute instead of a dead 1–2 session port.**
  The "un-oracle on real ink" question is answered: the synth doctrine does not transfer, and
  the lever it targets (wall-merge) is a minority of the loss.
- **Reinforces, harder, that FloorPlanCAD is a benchmark YARDSTICK, not the real 2D→3D goal**
  (the curve-priors report flagged its own FloorPlanCAD work the same way). On arbitrary
  published CAD the reader gives ~10–19% detection (sample-dependent) and ~0% identity
  (F1 0.4%, curve report). The real end-to-end lever is the owner-signed pipeline on the
  studio's OWN plans, where the drawing convention is known and identity is owner-signed.
- **A diagnostic artifact:** the real-CAD recall wound is 60% reader-detection / ≤ 40%
  wall-adjacent / 0% decor — the OPPOSITE shape of the synth symbol-unit decomposition
  (55.5% decor / 26% granularity / 9.6% dense / 8.7% real). The corpora fail differently;
  a synth-derived fix should never be assumed to port.

## Disposition

- **Do NOT port or tune `wall_detect` for FloorPlanCAD.** It is the wrong detector architecture
  for real CAD (90.8% ink discarded, < 1% pairs pass); a real-CAD wall detector is separate,
  uncertain, from-scratch work with a payoff capped at ≤ 40% of the recall loss.
- **Do NOT re-attempt a wall-recall lift on FloorPlanCAD** as a real-goal move — it is a
  yardstick with a majority-share reader-detection wound. If a wall detector is ever built,
  build and tune it on the studio's own plan convention, not on arbitrary benchmark CAD.
- The committed `baseline-test-00-oracle/` remains a valid oracle-OPENINGS baseline; note its
  `walls oracle` path feeds `promote()` (glazing candidates) only and is a **no-op for
  furniture detection recall** (smoke-oracle 13.1% ≡ smoke-blind 13.1%) — it is not, and never
  was, the detect→mask→barrier mechanism.

## Honesty note

Absolute furniture recall is sample-sensitive (9.4% on 80 sheets, 18.6% on the first 300,
9.8% committed full-corpus 2,245) — the **decomposition ratio** and the **detector-mechanism**
finding (both corpus-level) are the decision-relevant, robust signals, not the absolute recall.
`WALL_ADJ` is deliberately a generous upper bound; the conclusion (wall-work ≤ a minority of the
loss) only strengthens under a tighter threshold or a larger sample. This was a benchmark-lane
transfer probe, flagged as such — it returned negative; recording the negative + the mechanism
is the value.

reader: svg_plan_reader (unchanged) · detector: wall_detect (unchanged) · wrapper smokes only, zero committed-file edits
