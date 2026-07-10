# Structured3D blind-wall lane — the wall tier UN-ORACLED (2026-07-10)

**TIER: BLIND headline (closed loop, disclosed).** The blind arm's walls come from
`wall_detect` on the sheet ink only — no gt field reaches it past the DRAWING step.
The sheet is the committed oriented synth + gt wall centerlines drawn as **double
parallel lines at ±50 mm** (the standard architectural convention, the same signal
`pdf_extract_walls` keys on for real sheets via stroke thickness — `read_ink` is
width-blind, so the double line IS the width channel here). Machine report + cards:
`C:/Users/teza_/studio-datasets/structured3d/blind-walls-3500/`.

## 1. Question and answer

wall_aware_lane (b7cfbb6) put the wall split at ORACLE-WALLS: +2.6pp detection recall
(10.7 → 13.3) consuming `gt['wall_lines']`, because the synth sheet carried NO wall ink
— a wall that is never drawn cannot be detected blind. This lane asks: **make walls
observable the way real sheets make them observable; what does a real detector cost vs
the oracle?**

**Answer: nothing that survives rounding. On the same walls-drawn sheet, n=3,500 /
n_gt=444,405: naive (walls unknown) 3.7% → BLIND 13.3% → oracle 13.3% detection recall
(matched 59,059 vs 59,196 = the detector costs 137 elements, 0.23% relative); precision
77.0% both; F2 nobed 95.1% vs 95.3% (25 downgraded pairs of 9,793); symbol tier
(wall-partitioned unit) 67.0%/64.7% vs 67.2%/64.8%. The ORACLE-WALLS ceiling of the
wall tier is now a BLIND number.**

The naive column is the production justification: a wall-UNAWARE reader on a realistic
(walls-drawn) sheet collapses from 10.7% to 3.7% — detect→mask→barrier is load-bearing
infrastructure, exactly why the PDF lane strips thick strokes before clustering
(`plan_cluster.extract_clusters`' `w >= 0.6: continue`).

## 2. Mechanism (all wrappers — zero edits to parallel-session files)

- `pipeline/scripts/wall_detect.py` — pure-geometry detector: candidate parallel pairs
  at face gap ∈ [50, 250] mm, **gap-constancy** |d1−d2| ≤ 15 mm at both endpoints
  (same side), co-terminous ends (±5 mm) with length ratio ≥ 0.85, **ring-pair veto**
  (outline ink × outline ink is furniture geometry, never a wall), then **mutual-best
  matching in rounds** (a real double line is two strokes that CHOOSE each other;
  rounds recover exact-tie orphans deterministically). Classified wall segments are
  masked out of the symbol ink by LIST identity (never raster erasure — the pinned
  cut-real-ink trap), and merged centerlines drive the unedited `wall_aware_lane`
  mid-closing barrier.
- `pipeline/scripts/blind_wall_lane.py` — three arms on the SAME sheet (naive / BLIND /
  oracle-same-sheet), F2 enrichment per arm on its own post-mask ink, symbol-tier
  decomposition (imported from symbol_unit_lane) on blind + oracle preds, detector
  quality vs gt, and a **computed equivalence pin**: `--pin-cards` compares the oracle
  arm per scene against the committed wall-aware after-arm card.

Detector dead-ends killed by evidence during pilots (all pinned in tests):
1. excluding ALL ring members from pairing ate double-wall **cavity faces** (the 140 mm
   cavity closes an exact rectangle of wall-face ink) — real walls went undetected;
2. a furniture-size ring screen turned the detector into an accidental **thin-decor
   stripper** (fp 2 → 3,081; blind BEAT oracle — the paradox is an alarm, not a win);
3. same-ring-only veto let **aligned twins'** facing edges pair at a wall-like gap;
4. single-pass mutual-best broke exact-score ties by dict insertion order and orphaned
   whole walls (spacing = 2×offset); rounds fix it;
5. midpoint-only gap testing passed a ≤5°-tilted end-aligned stroke (85 mm lateral
   divergence at 1 m); gap-constancy at both endpoints rejects it.

## 3. Full corpus (3,500/3,500, 0 errors, 0 skips, ALL-GREEN, 6,803 s)

**Equivalence pin (COMPUTED, not prose): 3,500 scenes compared vs the committed
wall-aware after-arm — 0 mismatches, 0 absent.** That is the license for quoting the
committed 10.7/13.3 beside this run.

### detection — the un-oracled headline
| metric | naive (walls unknown) | **BLIND (detector)** | oracle (same sheet) |
|---|---|---|---|
| recall | 3.7% | **13.3%** | 13.3% |
| precision | 91.9% | **77.0%** | 77.0% |
| matched | 16,629 | **59,059** | 59,196 |

### detector quality (measured)
| metric | value |
|---|---|
| wall-segment classification | precision 99.8% / recall 99.3% (tp 527,690; fp 1,102; fn 3,550 = 2,910 micro-faces <80 mm by construction + **640 real**) |
| centerline length coverage | 100.0% recall / 99.9% precision of 533.7 km gt wall (tol: lat 60 mm / ang 6°) |
| gt walls with zero coverage | 1,348 / 265,620 — 1,285 micro <80 mm (undetectable by construction) + **63 REAL (0.024%, longest 6,681 mm)** |
| back-strips eaten | 121 (48 scenes, max 16/scene) |
| scenes with length-recall < 90% | 0 / 3,500 |

### F2 facing (beds excluded) + F3
- naive 88.7% (n=1,504 — **WALL-PRIOR-CONTAMINATED, measured: 20/1,680 naive rot
  emissions vanish when wall ink is masked** = answer-key geometry read as strips;
  quote the naive column for detection only) / **BLIND 95.1% (n=9,791)** / oracle
  95.3% (n=9,793).
- per-pair, oracle→blind: 9,768/9,793 unchanged; **25 downgrades** (11 left matched
  set, 11 exact→unreported, 3 direction errors); 9 newly-matched-in-blind flagged
  gt-assisted (fn wall ink as prior), never counted as improvement.
- rot-silent baselines 0.0% all three arms (measured, beds-excluded, same population).
- F3 92.8% all three arms (n blind 37,206 vs oracle 37,208).

### symbol tier (wall-partitioned unit; unit definition = answer-key side, disclosed)
| metric | BLIND pred | oracle pred |
|---|---|---|
| symbol recall | **67.0%** (59,732/89,108) | 67.2% (59,876/89,108) |
| member coverage | **64.7%** | 64.8% |

**UNIT WARNING:** the committed 76.9%/65.6% headline is the PLAIN 90 mm unit (68,517
symbols); this lane scores the finer wall-partitioned unit (89,108 symbols, ~30% larger
denominator) — the two are not comparable at any n. The same-sheet oracle column is the
reference, and the detector's symbol-tier cost is 0.2 pp / 0.1 pp.

## 4. Forensics (inspected, not asserted)

- **63 real wall misses** concentrate in 27 scenes and are one family: S3D
  **duplicate-collinear wall annotations of unequal extents** (pairs like 2,800/1,700 mm
  and 3,900/2,498 mm on the same line). One face of each duplicate is consumed into a
  cross-pair, mutual-best leaves the leftover faces orphaned, and their own pair fails
  the ≥0.85 length-ratio screen. Known shape, counted; barrier loses those walls'
  splits (also the fn-leak source in those scenes' downgrades).
- **25 F2 downgrades** co-locate with those scenes: masking/barrier deltas move a
  cluster enough to leave the matched set (11), erase a strip's pair (11), or let a
  residual fn wall face spoof direction (3) — the measured price of detector error.
- **121 eaten strips**: parallel strip pairs at wall-like gaps that pass co-terminous
  screens; F2 cost bounded by the 11 exact→unreported transitions above.

## 5. Honesty ledger

- CLOSED LOOP: walls are drawn from gt (as F2 strips are drawn from gt rot); the claim
  is ink-recovery through a real detector, not generalization. **IN-SAMPLE THRESHOLDS**:
  detector constants were iterated on pilot slices (scenes 0–199) of this same corpus.
  What transfers is the doctrine — classify wall strokes, mask them out of symbol ink,
  split at them — which is how the production PDF lane already treats thick strokes.
- Glazing is NOT drawn; F4/openings inherit the naive read (non-deliverable here).
- The blind>oracle direction is treated as an ALARM everywhere (decor-stripper pilot;
  gt-assisted upgrade flags in the transition table).
- Adversarial review: 2 rounds (3 lenses → 3-vote refutation panel; round 2 resumed
  after a spend-limit outage killed the geometry lens). 16 findings confirmed total,
  all fixed pre-run: computed equivalence pin replacing prose, naive-contamination
  instrument, unit-mismatch warning, micro/real splits (fn + walls_zero), beds-excluded
  baselines, gt-assisted upgrade flags, tie-rounds, gap-constancy, low_scenes
  denominator, tolerance disclosure, SYNTH_VERSION stamp.
- Tests: 29 pins in test_wall_detect + test_blind_wall_lane (dead-ends pinned);
  adjacent suites (wall_aware / symbol_unit / f2_facing) untouched and green — 77/77.

## 6. Consequence for the roadmap

- The wall tier is closed blind end-to-end on this corpus: **walls are confirmed NOT
  the next lever** (13.3% blind = the measured fusion ceiling; the remaining 86.7% gap
  decomposition stands: decor 55.5 / granularity 26.0 / dense-region 9.6 / real 8.7).
- Next: adopt the plan-symbol scoring unit as the headline unit (option C — definition
  + doctrine + report), and port the `wall_detect` parallel-pair doctrine to
  FloorPlanCAD real sheets to un-oracle `svg_plan_reader --baseline walls oracle` on
  real ink (constants re-derived per sheet family, as disclosed).

## 7. Repro

```
cd pipeline/scripts
python -m pytest test_wall_detect.py test_blind_wall_lane.py -q     # 29 pins
python blind_wall_lane.py --score C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled \
    C:/Users/teza_/studio-datasets/structured3d/blind-walls-3500 \
    --pin-cards C:/Users/teza_/studio-datasets/structured3d/wall-aware-3500
```

engines: blind_wall_lane v1.0 / wall_detect / wall_aware_lane v1.0 / f2_facing_lane
v1.0 / svg_plan_reader v2 (UNEDITED) / synth_plan_2d v1.1 · run dir `blind-walls-3500/`
