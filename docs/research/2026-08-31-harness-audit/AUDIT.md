# Harness audit — "ของเค้าอ่านแบบได้เก่งกว่า … ก็ปั้นได้ดีกว่า ทั้งที่ fable เหมือนกัน"

**Owner order (2026-08-31, verbatim):** observation *"ของเค้าอ่านแบบได้เก่งกว่าคุณเยอะมากทั้ง ๆ ที่ก็ fable เหมือนกัน"* then *"ก็ปั้นได้ดีกว่า"*, then, on the A/B/C proposal: **"ลุยให้หมดตามดุลพินิจคุณ"**.
This file is where those words live for `qa/owner-orders.json` (`recorded_at` cites here).

Trigger evidence: video BEHlmJCKvTA (TheSketchUpEssentials tests Fable 5 via SketchUp
MCP), note at `knowledge/_inbox/video-study/2026-08-31-fable5-sketchup-mcp-sofa-and-floorplan-BEHlmJCKvTA.md`.
This is the owner's THIRD cross-project observation (R8 2026-08-01, R9 2026-08-02 —
both were right, both became rules). Formula per those audits: measure → name the
mechanism → rule with a pre-work test → guard proven on a real defect → declared blind spots.

## The claim, made falsifiable

Same model (claude-fable-5), two harnesses, different outcomes. Hypothesised mechanism
(recorded in memory `owner-cross-project-observations` before any experiment ran):

| # | His harness | Ours | Repo evidence it matters |
|---|---|---|---|
| H1 | reads the sheet AND builds in ONE context, chain-sums live | reading stored in derivation files another context consumes | R12: scene-graph 0-for-3 on BF bands; headboard missing 3 weeks |
| H2 | high-level CAD vocabulary (profiles, sweeps, mirrored components) | raw-vertex bpy generators (2,177 hand-written lines, R8b audit) | R8: "the parameterisation IS the guess" |
| H3 | a sighted eye on every round, minutes per round | builder self-look = 0/367 convictions (R7d); C2/C3 hours per round | planted-defect memory: C2 filed 285 with the SAME model — context, not eyes |
| H4 | constraints wired into the toolpath (SketchUp skills) | 44/75 knowledge rules with no reader | rules_reader_check ratchet exists for exactly this |

## Experiment B — reading (one-context blind readers vs the derivation path)

- Materials: floor-2 furniture plan (drawing of record, 00_intake snapshot), 3 crops
  per arm at 4.5x/7x; answer key = the three committed stroke-level ink reads,
  **pre-registered in `ANSWER-KEY.json` before any reader ran**.
- Reproducibility: the crop PNGs are not committed — regenerate with
  `python make_crops.py` against the committed intake PDF (as-run: pymupdf 1.28.0,
  pillow 12.2.0; builds ran on Blender 5.1, eevee). `ref_sofa.png` IS committed:
  its source video download was deleted per disk law, so it does not regenerate.
- Arms: A = RAW crops; B = RECOLOR (vector replay coloured by pen weight: black
  structure / blue furniture+labels / red dims+hatch) — the video's
  dims-separable-from-walls lever, implemented for this sheet (arm C of the order).
- Readers: 6 fresh-context agents (3 per arm), blind by bundle construction
  (prompt names only the bundle dir; PROMPT.md forbids leaving it). One pass each,
  no iteration — measuring the FIRST-pass, which is where the historical path failed.
- Scored on: found/missed elements; label-vs-drawn discrepancy catches (the BF11
  600-vs-498 trap); bed head direction (the 3-week class error); mm error bands
  (5/30/100); chain checks; declared unmeasurables; contamination tells.
- Historical baseline (R12's record): scene-graph first pass = 0-for-3 band
  placements, label typed as drawn size, bed head read NORTH (ink: EAST).

RESULTS (workflow wf_031bc1de-f6b, 6/6 readers, ~1.24M subagent tokens; scores in
`READER-SCORES.{json,md}`, scored mechanically against the pre-registered key,
spot-checked by hand against reader A1's raw output):

- **Zero WRONG bands across 90 numeric reads.** A-raw: 28 EXACT (≤5 mm) / 13 GOOD /
  4 CLASS / 0 WRONG / 0 MISSING, median |Δ| 2.2 mm. B-recolor: 28/11/5/0/1,
  median 2.25 mm. At 3.78 mm/px these EXACT counts come from real instrument work
  (ink-weighted tick centroids, cross-checked calibrations at 0.05%), not eyeballing.
- **All 6 readers caught BOTH label-vs-drawn depth traps** (BF09-2 drawn ~499 vs
  label 600; BF11 drawn ~497 vs label 600) and filed trust verdicts — several
  phrased as an RFI to the designer, which is the professionally correct move.
  **All 6 read the bed head EAST from the pillow/fold ink and mapped the feet
  label to the right axes.** The historical derivation path scored 0-for-3 on band
  placements, typed the label as the drawn size, and read the head NORTH.
- The one shared miss is a CONVENTION, not a measurement: 5/6 reported bed E-W as
  the mattress stroke (~1941) where the key's 1999.6 includes the frame; A1 alone
  matched the key's convention (2000). Party-wall thickness was the only key where
  visual estimation degraded (A: two EXACT at 100; B: 108/117/144).
- Bonus class-error find: reader B3 flagged BF13 as drawn OVERLAPPING the piers
  (~100 mm each end, clear bay 3894 vs label 4100) — a cannot-be-built catch (R10's
  question) from a blind first pass.
- **Arm C (recolor) — NO measurable gain, one instrument bug found.** B ≈ A on
  accuracy, but the vector replay dropped every FONT-rendered string (the dim-chain
  numerals); only outlined-curve text (the BF labels) survived, so B readers lost
  the chain-sum rung (C5 2/3 vs 3/3) for lack of numbers, not lack of skill.
  Confirmed by direct LOOK at both bundles. The video's recolor lever remains
  UNTESTED on this sheet until the replay also re-draws text; as-implemented it is
  not worth promoting.
- Contamination tells: none in any reader.

## Experiment A2 — modelling (parameterisation vocabulary vs raw bpy)

- Interpreter `model-exp/build_plan.py`: executes ONLY R8's YES-branch (box+radius,
  measured-profile extrude, mirror instance) with R9 placement law (positions derived
  from rest_on + face anchors; typed coordinates do not exist; unknown refs fail
  closed). Proven before use: positive control BUILD-OK (4 components, 2,396 tris,
  correct frame) and negative control BUILD-FAIL on an unknown ref.
- Planner: fresh-context agent, sees ONLY the reference photo + VOCABULARY.md,
  chooses the parameterisation itself, budget ≤8k tris. Reference = the same
  charcoal rolled-arm sofa the video tested (frame t=425, full res), so the video's
  own 2-round result is the cross-harness benchmark.
- Loop: plan → build → sighted comparator (R10b local rung, ref beside render) →
  one revision. **Stop-loss 2 shape rounds (R8) — hard.**
- Comparison lines: our historical free-form record (5-6 rounds, still approximate;
  loose hand-built 7.56 critique items/piece) and the video's Fable-via-SketchUp
  (usable in 2 rounds).

RESULTS (2 rounds run, stop-loss hit; plans in `model-exp/plan{1,2}.json`, renders in
`model-exp/round{1,2}/`, comparator reports in the session record):

- **Round 1** (planner cold, 14 components, 7,864 tris): fresh comparator verdict
  **NO-DIFFERENT-PRODUCT** — but frame proportions near-exact (W/H 1.88 vs ref 1.91;
  arm apex 74.2% vs 74.1% of height). Ranked items: arm = canted thin slab not a
  rolled mass; see-through holes at arm/back junctions; cushions thin+domed;
  crown-spike artifact (interpreter bug — REDUCED engine-side by crowning only the
  top-face interior, but a residual mid-edge tent from the two interior verts
  flanking the front edge survived into round 2, where the fresh comparator filed
  it again); balloon back cushions;
  untapered legs (op didn't exist — added `taper_bottom_frac`).
- **Round 2** (same planner context, comparator items fed back — the video's
  iterate shape): 7,080 tris, corners closed, cushions boxed, legs tapered,
  arithmetic closure 2×280+3×490=2030 exact. Fresh cold comparator:
  **still NO-DIFFERENT-PRODUCT** — W/H now 1.93 vs 1.91 and 3-over-3 layout
  "almost exactly right", but the arm is still a flared wing, not a cylinder roll
  (outer edge +7.8° vs ref −9.0°), back cushions read as coplanar tiles, seat
  boxing ~0.10 H vs ref 0.16 H, plus two interpreter artifacts (edge pinch
  points, a notch where arm meets panel).
- **R8 stop-loss (2 shape rounds) = STOP.** Judge-variance note: the two
  comparators disagreed about the reference's own legs (r1 "tapers to half width",
  r2 "near-straight block") — single-judge items near the noise floor.

## Findings

1. **The reading half of the owner's observation transfers to us CHEAPLY and
   COMPLETELY.** Six fresh-context readers, one pass, blind, with instrument use:
   0 WRONG bands in 90 reads, median |Δ| 2.2 mm, 6/6 on both label-vs-drawn traps,
   6/6 on bed-head EAST — against a derivation-path history of 0-for-3 and NORTH.
   H1 (one-context read) and H3 (fresh eyes) are CONFIRMED as the mechanism; the
   model's eyes were never the problem. The video's floor-plan result is
   reproduced on our own sheet at better-than-video accuracy (2.2 mm median vs
   his 9.5–12.7 mm walls).
2. **The modelling half does NOT transfer through a thin vocabulary.** Given the
   parameterisation choice and an iterate round, the same model got massing
   near-exact twice and part construction wrong twice. The video harness's
   advantage is the EXECUTION KERNEL (SketchUp's full solid toolset + its skills
   layer), not the model's choice of parameters — H2 needs sharpening: "let the
   model pick the parameterisation" is necessary but nowhere near sufficient; the
   vocabulary's expressiveness is the binding constraint. A 3-op interpreter
   written in an afternoon is measurably not that kernel (2 of round-2's six
   items were MY interpreter's artifacts, not the planner's). Pre-commit scrutiny
   of the as-run scripts logged two more interpreter defects, neither
   conclusion-flipping: `add_material` walks mirror components too, and a
   hint-less mirror of a wood leg re-assigns "fabric" onto the SHARED mesh — so
   every leg rendered charcoal fabric, not wood (comparators were instructed to
   judge geometry/proportion only, and their leg items are shape items); and the
   recolor replay flattens dash patterns to solid as well as dropping font text
   (one more reason arm C is recorded UNTESTED rather than refuted). Scripts are
   kept byte-as-run; fixes belong to the P3 promotion if it is ratified.
3. **Arm C (dim recolor): no measured gain on this sheet**, and the test was
   partially voided by the replay dropping font-rendered text. Not worth
   promoting as-is.
4. **Free bonus rung discovered:** a blind first-pass reader fleet also files
   cannot-be-built items (B3: BF13 overlaps its piers by ~100 mm/end) — R10's
   question answered from ink alone, before any build exists.

## Rules proposed (for the owner to ratify — none wired yet)

- **P1 — FRESH-READ-BEFORE-EDIT (R12 extension):** any round editing a canonical
  mass must open with a fresh in-context instrumented read of that element's crop
  (tick-centroid calibration, cross-checked; the reader-prompt in `bundle-A-raw/`
  is the template). The spec row is a CACHE; a >30 mm disagreement between fresh
  read and spec reopens the derivation (never the sheet). Wire: a `sheet_read`
  step logged in the round record; sheet_recon stays the after-the-fact gate.
- **P2 — LOOSE-FURNITURE GEOMETRY GOES TO A REAL KERNEL, NOT A GROWN
  INTERPRETER:** the measured lesson is that expressiveness is the constraint, so
  the route for sofa-class geometry is (a) ACQUIRE, as R8 already orders, or
  (b) the SketchUp MCP + skills path the video used — which this repo already
  interops with — as a scout that must still pass our gates. Growing
  build_plan.py op-by-op is the third instance of hand-writing what a kernel
  already has (R8b). Owner call, since (b) touches his SketchUp seat.
- **P3 — the blind reader fleet becomes a callable instrument** (it is one
  Workflow invocation + a bundle dir), used at minimum before P2-exit-class
  gates on drawn elements. Cost measured this run: ~1.2M subagent tokens for 6
  readers on 3 crops.
- **NOT proposed:** recolor promotion (finding 3) — fix the text replay first,
  re-test on one round, then decide.
