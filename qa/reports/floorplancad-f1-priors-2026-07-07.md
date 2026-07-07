# FloorPlanCAD — F1 identity priors (first nonzero, and exactly where size can/can't identify)

**Date:** 2026-07-07 · **Engine:** `svg_plan_reader.py` v2 + `kind_priors.py`
(`--baseline ... priors kind-priors-train.json`) → `benchmark_reader.py` · **Corpus:**
test-00, 2,245 mm sheets (1,014 IoU-matched element pairs) · **Priors derived from:**
gt-train-00 (3,760) + gt-train-01 (6,401), 19 kinds n≥50 · **Artifacts:**
`C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors\` +
`.../priors/kind-priors-train.json` (both outside the repo — CC BY-NC) ·
**Wall-clock:** 444 s

F1 identity was structurally **0.0 %** (the reader emits no `kind` — identity is
owner-signed in production). `kind_priors.suggest_kind` emits a kind ONLY when an
element's size/aspect falls in exactly ONE train-derived band (uniqueness rule);
ambiguous or out-of-band sizes stay **unreported** — never a best-guess. It is
OFF BY DEFAULT and benchmark-only: the owner project lane never imports it.

## F1 identity: 0.0 % → 0.4 % (first honest nonzero)

| | Blind (2026-07-06) | + size priors |
|---|---|---|
| F1 accuracy on 1,014 matched | 0.0 % | **0.4 %** (4 correct) |
| kind emitted | 0 | 85/1,014 (emitted precision 4.7 %) |
| unreported (scored WRONG, never skipped) | 1,014 | 929 |

Detection (1,014 matched, 9.8 %/14.3 %) and F4 (7,991 matched, door 70.4 %) are
**identical** to the swing-door run — priors touch element `kind` only, nothing else.

## The per-class breakdown is the real finding (honest about where size works)

Size alone uniquely identifies a class only when its footprint is distinctive. The
report shows exactly where that holds and where it doesn't:

| kind | GT | pred | hit | recall | note |
|---|---|---|---|---|---|
| **stairs** | 4 | 46 | 3 | **75.0 %** | large distinctive footprint — size finds it, over-emits (precision 6.5 %) |
| **sofa** | 4 | 5 | 1 | 25.0 % | precision 20 % |
| squat_toilet | 172 | 1 | 0 | 0.0 % | band nearly always overlaps → stays unreported |
| chair | 334 | 0 | 0 | 0.0 % | biggest class: size overlaps table/others → **honestly unreported, not guessed** |
| table, elevator, air_conditioner, refrigerator, sink, bed, toilet, … | — | 0 | 0 | 0.0 % | overlapping bands → unreported |
| urinal | 0 | 31 | 0 | n/a | FALSE emissions (precision 0 %) — the urinal band catches non-urinal ink; reported, not hidden |

**What this says:** cited size priors buy a real but small F1, and their value is
diagnostic — they show that in a plan drawing, size **uniquely** identifies only a few
distinctive classes (stairs), while the high-frequency furniture (chair/table/elevator)
is size-ambiguous and correctly stays silent. That silence is the scorer-honesty
doctrine working: an ambiguous element is unreported (scored wrong), never a flattering
guess. The urinal over-emission (31 pred / 0 GT) is surfaced with precision 0 %, not
buried — a concrete "where the band is too loose" signal for the next iteration.

## Honesty invariants held

- **OFF by default / blind lane byte-identical:** with no priors, elements carry no
  `kind` and the meta gains no `kind_priors` key (pinned; no-priors F1 = 0.0 confirmed
  on the same 300-sheet smoke where priors-on = 0.7 %).
- **No leakage:** bands derived from TRAIN, scored on TEST; `suggest_kind` never reads
  the test sheet's GT.
- **Owner lane untouched:** `kind_priors` is imported only by `svg_plan_reader.py` (+ its
  tests) — never by `placement_gate`, `gen_floor2_v4_specs`, `raster_overlay`, or
  `build_floor`. Production identity stays owner-signed (see `confirmed_kind`, same session).
- **Unreported never defaulted:** ambiguity → None → absent `kind` → scored as wrong in
  accuracy, honestly (929 of 1,014 unreported).

## Next

- Tighten distinctive-class bands (urinal false-emit) and add aspect/curve signatures so
  a few more classes clear the uniqueness bar without guessing the overlapping ones.
- The real identity lever remains the owner-signed ledger (`confirmed_kind`); priors are
  a benchmark yardstick + at most an overlay SUGGESTION, never an auto-applied label.

reader: svg_plan_reader v2 · priors: kind-priors-train.json (19 kinds) · suite: 528 passed
