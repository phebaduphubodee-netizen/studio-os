# Structured3D symbol-unit lane — what the remaining recall gap is MADE OF (2026-07-10)

**TIER: mixed, per side (disclose wherever quoted).** BEFORE side = the blind reader on the
closed-loop oriented synth (same as the committed baseline). AFTER side consumes
`gt['wall_lines']` via the wall barrier = ORACLE-WALLS; the wall-partitioned grouping unit
additionally consumes walls on the SCORING side = DOUBLE ORACLE. The plan-symbol grouping
itself reads GT footprints on the scoring side only — it never touches the pred (v1.1
doctrine). Per-object recall headlines (10.7% blind / 13.3% oracle ceiling) are UNCHANGED;
nothing here is a new recall claim.

## 1. Question and answer

The wall-aware lane (structured3d-wall-aware-2026-07-10.md) attributed the remaining 86.7%
per-object recall gap to "within-room fusion + sub-object granularity" WITHOUT splitting the
two. The split decides the next lane: scoring-unit change vs symbol-level splitter.

**Answer (AFTER side, gap = 385,209 of 444,405 GT elements):**

| what the gap is | share of gap | share of GT | fix class |
|---|---|---|---|
| decor below the reader's own 150 mm screen (micro 30.7% + elongated-thin 24.8%) | **55.5%** | 48.1% | not reader work — GT is finer than what a 2D plan draws; thin elements matched only 456× corpus-wide (measured, micro+elongated combined) |
| granularity: unmatched members of symbols the reader DID match | **26.0%** | 22.6% | SCORING UNIT, not reader |
| union-oversize dense regions (grouping-proxy limit) | 9.6% | 8.3% | 4.6pp of it = cross-wall chaining (resolves under wall-partitioned grouping); 5.0% genuinely dense in-room mass |
| REAL symbol-grain detection work (fused_cross_symbol 3.6 + dropped 2.0 + touched 2.5 + drift 0.5) | **8.7%** | 7.5% | the splitter's actual target |

On the wall-clean unit (wall-partitioned grouping, DOUBLE ORACLE) the real-work share is
15.1% of the gap (fused 7.6 + dropped 4.2 + touched 2.9 + drift 0.4) — the finer unit
reclassifies chain members into real work; that is its honest upper framing.

**Consequences:**
- The per-object unit is nearly SATURATED: one-to-one matching can yield at most ~one match
  per symbol (~68.5k symbols → ≈15.4% per-object recall, derived estimate), and the oracle
  ceiling already sits at 13.3%. The UNIT, not the reader, is now the bottleneck.
- At symbol grain the same preds already read: **symbol recall 76.9%, member coverage 65.6%**
  (oracle-walls; blind-before: 71.8% / 60.6%). The reader is far better than the per-object
  number says.
- A symbol-level splitter's TOTAL addressable mass ≈ 9–15% of the gap (~33.4k–58.1k members).
  Worth having, not the main lever. The main lever is adopting the plan-symbol unit for
  scoring (synth v1.1's argument, now corpus-quantified) + a real wall detector to cash the
  oracle tier.

## 2. Mechanism

`pipeline/scripts/symbol_unit_lane.py` (detection-only; F2/F3 enrichment stack never runs):

1. **Pred re-derivation, pinned**: the run dir stores score cards, not pred boxes, so preds
   are re-derived deterministically (same oriented synth → unedited reader → wall barrier)
   and cross-checked per scene against the committed wall-aware cards.jsonl:
   n_gt / n_pred / matched / exact missed-id set, both sides. **3,500/3,500 equal, 0
   mismatched, 0 absent, 0 pinned-but-unscored — ALL GREEN** (before side reproduces the
   committed 47,437 matched verbatim).
2. **Plan-symbol unit**: `synth_plan_2d.group_symbols` (v1.1, fuse gap 90 mm) mirrored to
   expose member→symbol assignment; the mirror is asserted equal to `group_symbols`' own
   output PER SCENE (drift raises, and a raise can NOT hide — see §4).
3. **Exhaustive buckets**: every sanitized GT element lands in exactly one of
   matched / decor_micro / decor_thin_elongated / oversize_single / granularity /
   union_oversize_region / fused_cross_symbol / geometric_drift / touched_only /
   dropped_no_pred; the sum equals n_gt per scene (asserted). fused/drift/touched classify
   unmatched symbols by majority-coverage (bar 0.5; sensitivity 0.25/0.75 printed:
   13,101–15,646 around the 14,054 headline — stable).
4. **Wall-partitioned grouping** (AFTER only): same fuse rule, but members union only within
   the same wall-region (barrier's own labelling; on-barrier centre = wildcard). Splits the
   v1.1 mega-chains: union_oversize_region 36,994 → 19,321 members; n_symbols 68,517 →
   89,098; member coverage stays ~65% (unit-consistency check).

## 3. Full corpus (3,500/3,500 scenes, 0 errors, 0 drift asserts, 6,233 s)

Full tables: `symbol-unit-3500/report.md` (+ cards.jsonl per scene). Key rows (AFTER):

| bucket | elements | % of GT | % of gap |
|---|---|---|---|
| matched | 59,196 | 13.3% | |
| decor_micro | 118,366 | 26.6% | 30.7% |
| decor_thin_elongated | 95,638 | 21.5% | 24.8% |
| granularity | 100,254 | 22.6% | 26.0% |
| union_oversize_region | 36,994 | 8.3% | 9.6% |
| fused_cross_symbol | 14,054 | 3.2% | 3.6% |
| geometric_drift + touched_only + dropped_no_pred | 19,340 | 4.3% | 5.0% |
| oversize_single | 563 | 0.1% | 0.1% |

Pred purity (AFTER): of 76,858 kept preds, 65.6% majority-cover exactly 1 symbol, 7.7%
cover ≥2 (the fusion population), 26.6% cover 0 (decor-mass/phantom clusters).

## 4. Honesty ledger

- **Anti-flattery instrument printed, not promised**: matched-symbol IoU histogram — only
  3.0–3.1% of matched symbols sit in the barely-matched [0.5,0.6) band, so `granularity`
  is not inflated by bloated near-bar matches.
- **The flattering-scorer hole recurred (5th lane in a row), caught pre-run** by a 3-lens →
  refutation-panel adversarial workflow (54 agents): (a) the promised IoU-quartile guardrail
  was computed but never printed → replaced with the aggregated histogram above; (b) the
  blanket per-scene `except` converted the lane's OWN loud-drift asserts into quiet skips
  while the pin flag still read ALL GREEN → drift asserts now have their own counted bucket,
  and the flag requires zero mismatches AND zero absents AND zero pinned-but-unscored AND
  zero raises (denominator cannot shrink silently; test-pinned); (c) the slice artifact
  predated the last code edit → regenerated; (d) "union-oversize cannot match by design" was
  false (a one-axis-oversize kept pred can match it) → now MEASURED: 196 matched-though-
  oversize (their members honestly count as granularity — the reader genuinely emitted the
  cluster).
- Thin-screen cost measured, never asserted: 456 thin GT elements DID match a kept pred
  (matched-despite-thin-screen), out of ~214k thin.
- Plain-grouping `granularity` absorbs cross-wall lumps on the BEFORE side (v1.1 mega-chain
  limit) — the AFTER + wall-partitioned table is the wall-clean decomposition.
- The ~15.4% per-object structural ceiling in §1 is a DERIVED estimate (one match per
  symbol), not a measured bound.

## 5. Repro

```
cd pipeline/scripts
python -m pytest test_symbol_unit_lane.py -q          # 14 pins
python symbol_unit_lane.py --score C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled C:/Users/teza_/studio-datasets/structured3d/symbol-unit-3500 --pin-cards C:/Users/teza_/studio-datasets/structured3d/wall-aware-3500
```

engines: symbol_unit_lane v1.0 / wall_aware_lane v1.0 / svg_plan_reader v2 (UNEDITED) /
synth_plan_2d v1.1 (UNEDITED) · run dir `symbol-unit-3500/` (cards.jsonl + report.md)
