# Structured3D wall-aware lane — cross-wall fusion split, before/after (2026-07-10)

**TIER: ORACLE-WALLS (disclose wherever quoted).** The barrier consumes `gt['wall_lines']`
(the answer-key side). Every number here is the CEILING a real wall-detector
(`pdf_extract_walls` on production sheets) can unlock — NEVER the blind headline. The
blind headline remains qa/reports/structured3d-synth-f2-2026-07-09.md. Precedents:
floorplancad-oracle-walls-2026-07-07.md, `svg_plan_reader --baseline walls oracle`, the
f2 wall-prior. Walls leak position only — no kind/rot/indoor.

## 1. Question and answer

The full-corpus F2 run (4c4bf42) measured the reader's ceiling as FUSION: detection
recall 10.7%, 10/12 wrong-facing forensics = fused-neighbour strips. This lane asks:
**how much of that ceiling is CROSS-WALL fusion?** — by severing exactly there and
re-scoring the same ink.

**Answer: cross-wall closing-fusion is worth +2.6pp detection recall (10.7% → 13.3%,
+24.8% relative, +11,759 matched) and +4.5pp precision (72.5% → 77.0%) at zero
meaningful cost (6 scenes lost exactly 1 match each; 1 F2 pair regressed corpus-wide).
It does NOT move F2 facing accuracy (95.3% → 95.3%): the split adds +1,998 eligible
pairs at the same accuracy and fixes 24 old misses while the new population brings its
own — the fusion wound is DETECTION mass, not facing angle.**

## 2. Mechanism (wrapper — zero edits to parallel-session files)

`pipeline/scripts/wall_aware_lane.py` re-runs the reader's own morphology with the
closing DECOMPOSED (scipy `binary_closing` = `erosion(dilation(x))` at these defaults)
and the wall barrier applied in between:

    dil    = binary_dilation(ink, r)            # the reader's own bridge step
    cut    = dilate(rasterize(walls), 1) & ~ink # wall pixels that carry NO real ink
    dil   &= ~cut                               # phantom mass severed AT the wall
    closed = binary_erosion(dil, r) | ink       # stranded far-side mass erodes back;
                                                # real ink restored

Zero-walls path = verbatim `binary_closing` → elements geometry-identical to the unedited
reader (x/y/w/d/curve/fill + order, pinned; ids intentionally w### vs c### to mark the
lane). Primitives (`_rasterize`, `_screen_component`) imported from plan_cluster, never
re-implemented.

Two mechanism iterations were killed by forensics before this one (both pinned in
tests):
1. **cut real ink** → wall-hugging elements (curtains/windows/wardrobe bands) shredded
   below the 150 mm size screen; probe scenes lost up to half their matches.
2. **cut AFTER closing (bridge-only, post-hoc)** → adversarial review reproduced a leak:
   real ink poking ≥1 px past the wall centreline punches a hole in the ~3 px band and
   the surviving bridge mass BEYOND the band reconnects the rooms. Severing mid-closing
   lets the erosion half eat the stranded mass back at any overlap depth.

## 3. Full corpus (3,500/3,500 scenes, 0 errors, 0 no-wall scenes, 4,807 s)

### detection — the fusion-ceiling headline
| metric | before (unedited reader) | after (wall barrier) | delta |
|---|---|---|---|
| recall | 10.7% | **13.3%** | **+2.6pp (+24.8% rel)** |
| precision | 72.5% | **77.0%** | +4.5pp |
| matched | 47,437 | 59,196 | +11,759 |
| n_pred | 65,430 | 76,858 | +11,428 |

Scene-level: **2,914 scenes gained matches / 580 unchanged / 6 lost (exactly 1 each)**.
Before-side reproduces the committed baseline exactly (recall 10.7%, F2 95.3% n=7,795)
— the wrapper does not perturb the before lane.

### F2 facing — visual lane, beds excluded (closed-loop ink recovery)
| metric | before | after |
|---|---|---|
| cardinal_correct | 95.3% | 95.3% (COMPOSITION-DRIVEN — see decomposition) |
| n / hits | 7,795 / 7,431 | 9,793 / 9,332 (+1,998 / +1,901) |

Per-pair decomposition (the honest view — aggregate compares two populations):
- of 7,795 before-matched pairs: **7,770 unchanged; 24 improved**
  (unreported→exact 22 — de-spoofed strips; wrong→exact 2 — two of the twelve
  forensically-inspected fused-strip misses fixed by the split); **1 regressed**
  (exact→unreported).
- newly matched: 1,998 pairs — exact 1,878 / unreported 112 / wrong 5 / flipped 3
  (94.0% exact ≈ the old population's 95.3%, hence the flat aggregate).
- blind baseline MEASURED (not asserted): 0.0% both sides, buckets all-unreported.
- beds included (contaminated, S3D bed rot = length axis): 94.1% → 94.1% (n 9,326 → 11,633).

### F3 indoor (pred stays indoor-silent; delta = matched-set composition)
- 94.4% (n=31,384) → 92.8% (n=37,208). The split matches more GT elements that carry
  indoor=False (balcony/outwall side), which pred-silence (defaulted indoor=True)
  gets wrong — the drop is the honest price of seeing more of the sheet.

### secondary — wall-prior rot band (DOUBLE ORACLE: split + prior)
- beds excluded: 35.9% → 34.1% (n 7,795 → 9,793). New matched mass includes more
  off-wall/interior elements the backing-wall prior cannot call.

## 4. What remains of the fusion ceiling (measured, not guessed)

| residual bucket | count | note |
|---|---|---|
| kept components spanning ≥2 wall-partitioned regions | 20,968 (3,315 scenes) | REAL-INK continuity across walls (windows/curtains/wardrobe bands) — barrier keeps them whole by design |
| merged_blob still dropped after the barrier | 2,684 | >3.6 m on both axes even after wall cuts — within-room / real-ink fusions |
| partial-trace route-arounds | not counterable | bridge routes around door gaps & junction-broken/adapter-skipped traces (pinned, documented) |
| within-room fusion + sub-object granularity | the bulk of the remaining 86.7% recall gap | untouched by design |

**Consequence for the roadmap:** walls are NOT the next lever anymore. The remaining
recall gap is dominated by within-room fusion against sub-object GT granularity —
the next lane is symbol-level separation (per-symbol grouping on the pred side, or
scoring against plan-symbol-grouped GT as in synth_plan_2d v1.1), not better walls.

## 5. Honesty ledger

- ORACLE-WALLS tier end-to-end; the pred meta carries `wall_aware.tier="ORACLE-WALLS"`
  so the pred can never be mistaken for a blind read.
- CLOSED LOOP: same oriented back-strip synth as f2_facing_lane — ink-recovery fidelity,
  not generalization to real symbol ink.
- The F2 aggregate delta cell is labelled COMPOSITION-DRIVEN in the machine report and
  the per-pair transition decomposition prints beside it (adversarial-review finding;
  the flattering-scorer hole recurring in per-lane form — this time caught pre-run).
- Blind baseline is measured per run on the un-enriched preds, never asserted.
- Adversarial review (3 lenses → refutation panel, 7 agents): 4 majors confirmed, all
  fixed before the corpus run; the leak repro (#2 above) is now a regression test.

## 6. Repro

```
cd pipeline/scripts
python -m pytest test_wall_aware_lane.py -q          # 15 pins
python wall_aware_lane.py --score C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled C:/Users/teza_/studio-datasets/structured3d/wall-aware-3500
```

engines: wall_aware_lane v1.0 / f2_facing_lane v1.0 / svg_plan_reader v2 (UNEDITED) /
synth_plan_2d v1.1 · run dir `wall-aware-3500/` (cards.jsonl + report.md)
