# Structured3D unit-adoption lane — OPTION C: the plan-symbol unit is now the headline unit (2026-07-10)

**TIER: BLIND headline (closed loop, disclosed).** Preds re-derived EXACTLY as the
committed blind-walls run (same oriented synth + gt wall ink, same detector, same
barrier), then scored under the newly-adopted plan-symbol unit. Machine report + cards:
`C:/Users/teza_/studio-datasets/structured3d/unit-adoption-3500/`.

## 1. Question and answer

symbol_unit_lane (2026-07-10b) proved the per-object scoring unit is ~SATURATED (13.3%
reached vs ~15.4% derived structural ceiling; 86.7% of the gap is decor + granularity +
dense-region, only 8.7% real symbol-grain work) and named the next lever: **adopt the
plan-symbol unit for scoring.** This lane does the adoption — a single canonical unit
definition, a headline scoreboard, and the doctrine that makes the number durable.

**Answer: the 2D reader reads 67.0% symbol recall / 64.7% member coverage / 77.9% symbol
precision (BLIND, plan-symbol/gt-wall-partitioned-90mm/v1, n_sym=89,094) on n=3,500;
oracle-walls 67.2% / 64.8% / 77.9% (alarm clear, blind ≤ oracle on all three metrics).**
The per-object detection unit (13.3% recall) is DEMOTED to a diagnostic tier. The headline
value is unchanged from the committed sym-tier instrument — what changed is the unit is now
**frozen** (canvas is a pure function of gt.json; /v1 constants pinned) rather than
floating on the reader's ink.

## 2. What "adopting the unit" concretely means

- `pipeline/scripts/plan_symbol_unit.py` — the ONE canonical unit definition (imported,
  never re-implemented). Two variants, each with a stamped id:
  - `UNIT_PLAIN` = `plan-symbol/plain-90mm/v1` (68,517 symbols corpus-wide)
  - `UNIT_GTWALL` = `plan-symbol/gt-wall-partitioned-90mm/v1` (89,094) — **the headline**.
  - `build_unit(gt_doc, unit_id)` is a **pure function of gt.json** — no ink, no preds in
    the API. This fixes the committed instrument's canvas wart: `symbol_unit_lane.
    wall_regions` sized the partition canvas from the SHEET'S ink bbox, so the same
    scene's unit shifted with what the reader happened to read (committed n_sym read
    89,098 in one lane, 89,108 in another). The canonical canvas is sized from gt element
    footprints + wall endpoints only.
  - `_assert_frozen()` pins the /v1 constants (FUSE_GAP_MM 90, THIN_MM 150, ZONE_PAD_MM
    100, BASE_RES_MM 6, MAX_RASTER_PX 3000, BARRIER_DILATE_PX 1); a drift RAISES —
    a tuned constant is a NEW unit, never a silent redefinition of v1.
  - `require_same_unit` / `agg_cards` REFUSE to average two units (a delta across units
    is a definition change, not a reader change).
- `pipeline/scripts/unit_adoption_lane.py` — the scoreboard. Re-derives blind/oracle preds
  as the committed run, then per scene pins FIVE faces against the committed blind-walls
  cards — detection tuples (both arms), the ink-canvas symbol instrument (both arms),
  n_regions — so the bridge from the committed instrument to the new frozen unit is
  COMPUTED, not asserted. Reports the OFFICIAL headline, the full unit matrix (same preds,
  every unit), the measured ink→gt canvas delta, and the demoted per-object tier.

## 3. Full corpus (3,500/3,500, 0 errors, 0 skips, ALL-GREEN, 5,639 s)

**Bridge pins (COMPUTED per scene vs the committed blind-walls after-arm + sym instrument):
3,500 compared — 0 mismatch, 0 absent, 0 pinned-but-unscored.** That is the license for
the canvas-delta measurement and for quoting the committed references beside this run.

### OFFICIAL headline — symbol tier (`plan-symbol/gt-wall-partitioned-90mm/v1`)
| metric | BLIND (headline) | oracle-walls (alarm ref) |
|---|---|---|
| symbol recall | **67.0%** (59,730/89,094) | 67.2% (59,874/89,094) |
| member coverage | **64.7%** | 64.8% |
| symbol precision | **77.9%** | 77.9% |

Alarm clear: blind ≤ oracle on all three metrics.

### unit matrix — same preds, every unit, one run
| unit (id, corpus n_sym) | blind recall / coverage | oracle recall / coverage |
|---|---|---|
| `plan-symbol/plain-90mm/v1` (68,517) | 76.7% / 65.5% | 76.9% / 65.6% |
| ink-canvas instrument, committed def (89,108) | 67.0% / 64.7% | 67.2% / 64.8% |
| **`plan-symbol/gt-wall-partitioned-90mm/v1` — OFFICIAL** (89,094) | **67.0% / 64.7%** | 67.2% / 64.8% |

The PLAIN 76.9/65.6 (oracle) reproduces the committed symbol-unit headline; it is a
DIFFERENT unit (~30% coarser denominator) and is NOT comparable to the 89,094-symbol
gt-wall headline at any n. The ink-canvas row reproduces the committed blind-walls sym
tier bit-exact (67.0/64.7 blind, 67.2/64.8 oracle) — the bridge.

### canvas delta — the definitional fix, MEASURED (LICENSED: pins GREEN)
- n_sym: 89,108 (ink-canvas) → 89,094 (gt-canvas), **delta −14** (0.016% of the unit)
- scenes where the partition region count changed: 39 / 3,500
- blind headline shift: symbol recall **+0.01pp**, member coverage −0.00pp

The ink-canvas instability the finding named was real but tiny (14 symbols, 39 scenes,
+0.01pp); freezing the canvas to gt.json removes it and makes the unit reproducible forever.

### per-object unit — DEMOTED to diagnostic (never the headline)
- detection recall 13.3% (59,059/444,405), precision 77.0% (blind); oracle matched 59,196.
- ~SATURATED: ~15.4% derived structural ceiling vs 13.3% reached — one-to-one matching
  yields ~1 match/symbol, so progress on it measures the unit, not the reader. It remains
  the committed detection metric elsewhere, quoted with its own label.

## 4. Adversarial review (3 lenses → 3-vote refutation panel; 2 rounds)

Round 1 (69 agents) surfaced 22 findings; a mid-run spend-limit outage killed 15 verify
agents, so 12 were panel-confirmed and 10 left unverified. All 22 were then resolved
(the 10 unverified were re-judged directly, two — U7/U8 — were legitimate majors):

- **alarm broader in prose than code** (3 lenses): `_alarm_line` checked only 2 of 3
  symbol metrics while doctrine said "any" → now checks recall + coverage + PRECISION on
  every matrix row, and the clear message names exactly what it checked.
- **canvas-delta licensing was prose** (flattery + doctrine): "licensed by the bridge pins
  above" printed on unbridged / NOT-GREEN runs → the section is now gated on GREEN, prints
  UNLICENSED otherwise, and coalesces None → n/a instead of a fabricated ±0.00.
- **limit-truncation invisible**: a partial run read as "N scored / N" → n captured before
  truncation; PARTIAL RUN banner + forced NOT GREEN.
- **trivial-partition share undisclosed + no_walls missed degenerate walls**: scenes whose
  gt partition never fires score plain geometry under the GTWALL stamp → now counted and
  disclosed (0/3,500 here); `_has_usable_walls` catches all-zero-length wall_lines.
- **headline quotable when NOT GREEN**: the OFFICIAL HEADLINE header now carries
  QUOTABLE / UNQUOTABLE.
- **`gt_wall_regions` IndexError** (geometry, repro'd): a very long wall + narrow element
  column drove a raster axis to int()=0 → 1px floor; the "pure function of gt.json"
  contract no longer crashes on legal input.
- **U7 — /v1 not actually frozen** (major, panel died → re-judged): the unit floated on
  constants living in other modules → `_assert_frozen()` pins them and RAISES on drift.
- **U8 — ink instrument unstamped yet quoted** (major, panel died → re-judged): stamped
  with its own id (`.../ink-canvas-instrument/committed-mirror`); the UNIT LAW now states
  the green-gated canvas delta is the LONE sanctioned cross-unit arithmetic.
- **enrichment shortcut** (U0/U3, would have failed the pin corpus-wide): the committed
  card scored the F2-ENRICHED pred (with `_attach_rot`'s 0.1mm rounding), the lane scored
  the raw pred — a knife-edge IoU≈0.5 pair could flip between them → the lane now scores
  the ENRICHED pred for detection, exactly as the committed run, making the bridge pin
  exact-by-construction rather than rot-invariant-up-to-rounding.

New sub-lesson: **a "frozen /v1" unit whose geometry is assembled from constants in other
modules is not frozen** — freeze the constants explicitly or the version id lies. And the
flattering-scorer shape recurred an 8th time (the alarm claiming "any metric" while
checking two): every verification SENTENCE the report prints must be a check the code runs.

## 5. Honesty ledger

- CLOSED LOOP: walls are drawn from gt (as F2 strips are); ink-recovery through a real
  detector, not generalization. IN-SAMPLE detector thresholds (disclosed in the blind-walls
  report). The unit consumes gt wall_lines on the ANSWER-KEY side only; pred tier is
  orthogonal and stamped in every pred's meta.
- The headline VALUE (67.0/64.7) is unchanged from the committed sym-tier instrument; what
  this lane adds is a frozen, self-labelling, pin-verified DEFINITION and the demotion of
  the saturated per-object unit — not a new recall claim.
- Decor (<150mm) and single-object merged blobs stay OUT of the symbol unit and IN the
  per-object denominator — no denominator shrank.
- Tests: 22 pins in test_plan_symbol_unit + test_unit_adoption_lane (unit purity, the
  ink-canvas wart reproduced + gt-canvas immunity, the 5 pin faces, frozen-constants drift,
  the raster crash, limit disclosure, alarm-precision, canvas-delta gating); adjacent
  suites (wall_detect / blind_wall / wall_aware / symbol_unit / f2_facing / synth) untouched
  and green — 111/111.

## 6. Consequence for the roadmap

- The plan-symbol unit is ADOPTED: headline = 67.0% symbol recall / 64.7% member coverage
  (BLIND, frozen gt-wall unit). The per-object unit is a diagnostic tier from here on.
- Next lever is unchanged from the symbol-unit decomposition: to move the headline, either
  a symbol-level splitter (addressable mass ~9–15% of the gap) or — the bigger prize — port
  the whole doctrine (frozen unit + wall_detect parallel-pair detector) to FloorPlanCAD
  REAL ink, un-oracling `svg_plan_reader --baseline walls oracle` on real sheets (constants
  re-derived per sheet family, in-sample disclosure stands).

## 7. Repro

```
cd pipeline/scripts
python -m pytest test_plan_symbol_unit.py test_unit_adoption_lane.py -q   # 22 pins
python unit_adoption_lane.py --score \
    C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled \
    C:/Users/teza_/studio-datasets/structured3d/unit-adoption-3500 \
    --pin-cards C:/Users/teza_/studio-datasets/structured3d/blind-walls-3500
```

engines: unit_adoption_lane v1.0 / plan_symbol_unit v1.0 / wall_detect / wall_aware_lane
v1.0 / f2_facing_lane v1.0 / svg_plan_reader v2 (UNEDITED) / synth_plan_2d v1.1 · run dir
`unit-adoption-3500/`
