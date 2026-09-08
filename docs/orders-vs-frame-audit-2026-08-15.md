# Orders vs the frame — why the owner's orders do not reach the model

**Audit date 2026-08-15.** Triggered by the owner: *"ทำไมผมสั่งอะไรไปยังไง model ก็พังไม่เปลี่ยน"*.
Method: five independent measurement passes over the repo's own history, each one then
handed to a second agent whose instructions were to REFUTE it with a different command or
a different file. Everything below is what survived that pass. Numbers that did not
reproduce are recorded as refuted, including the ones that supported the builder's first
hypothesis.

---

## 0. THE FIRST HYPOTHESIS WAS WRONG, AND IT WAS THE BUILDER'S OWN

The opening hypothesis was the flattering one: *"his orders get converted into machinery
instead of into geometry"*. It does not survive.

- Classifying every commit in the four days after each of the eleven dated owner orders,
  **instrument churn exceeds geometry churn in only 5 of 11 windows.** The sign FLIPS in
  R7b/R9, R7c, R10/R10b and the ACQUIRE window once `build_room.py` is attributed by
  filename instead of by a hunk-split heuristic; every flipped margin is under 5% of the
  window's code churn, so the metric cannot carry the claim in either direction.
- `build_room.py` is **>89% geometry/material code by hunk** — 218 of 5,260 changed lines
  sit under `_score_deliverable` and `_outdir`; counting the 346 lines of CLI plumbing
  under `__main__` as instrument raises it only to 564/5,260 = 10.7%.
- **All 32 consecutive full-fidelity frame pairs on disk differ in pixels. Zero are
  identical.** Smallest change p2r10 at 0.635% (sampler noise), largest p2r8 at 99.02%.
- **26 of 32 measurable rounds changed the BUILT geometry** (from the scene dumps, not
  from commit messages). The 6 that did not: p2r10, r12, r15, r16, r20, r31.

So the frame changes every round and the geometry changes most rounds. The complaint is
still correct, and it is about something else.

## 1. WHAT NEVER CHANGES IS THE CLASS OF THE OBJECT

Measured from the built scene `room_bedroom_suite_eye_p2r35.scene.json` (569 meshes,
369 in frustum) and the shipped id mask:

| | |
|---|---|
| hand-built masses | **467 of 569 (82.07%)**, 288 in frustum |
| acquired imports | 102 of 569 (17.93%), 81 in frustum, from **5 distinct source files** |
| acquired share of the delivered pixels | **163,380 px = 3.7819%** of 4,320,000, bounded ≤ 5.6540% by two shared materials |
| hand-built FREE-FORM masses — the class R8 forbids hand-modelling | **74 built, 61 in frustum** |
| critic-debt rows closed against a geometry change | **0 of 21** |

The two rows that do carry `closed_by` (DEBT-09, DEBT-21) both declare `door: image_row`
and both cite the same file, `room_bedroom_suite_eye_p2r8.png`. All three `scene_row`
rows and all three `guard` rows are open.

**`soft-goods-read-rigid` is filed in 49 of 49 rounds** across both lanes (TRN 16/16,
DELIV 33/33), including all 5 of the newest. First filed at r14. Status: open.

## 2. THE MECHANISM — AN ORDER BECOMES A TEST THE BUILDER WRITES AND THEN JUDGES

R8 was written from the owner's 2026-08-01 order that hand-modelled free-form geometry
always comes out deformed. Its test is *"can this be produced by boxes with radii, a swept
profile, or an extruded outline?"* — a test the builder chose. Bed, bench, nightstand and
rug all pass it. **The rule made from the order licenses exactly the class the order was
about.**

Then every audition of the acquire leg was decided by the same builder:

- **r33** — four classes auditioned, four refused. *(Recorded in the gate prose only; no
  build log for r32–r35 exists anywhere in `pipeline/output`, so no run-time artifact
  corroborates the numbers.)*
- **r31** — an acquired bed-cloth set imported, scale-asserted at 2198.1 mm, then
  R1-STOPPED and defaulted OFF: `_BED_CLOTH_ACQ = False`, `build_room.py:1593`.
- **9d8dded** — five classes surveyed, one landed, three refused.

**58 of the 61 rows in `qa/open-decisions.json` were decided by the builder; 3 by the
owner.** (The file carries 61 rows but only 60 unique ids — D-038 appears twice, same
date, two different questions.)

Four mechanism flags are CLI-only opt-in and ship OFF by default: `_ADULT_SCALE:1514`,
`_DUVET_TUCKS:1556`, `_KEY_SUN:1561`, `_BED_CLOTH_ACQ:1593`.

## 3. THE REVERSE CHANNEL DROPS THINGS TOO

- The **procurement flat-file ask** was routed in the r27 gate and restated in four
  further gates (r28 ×4, r29 ×2, r30 ×1, r31 ×1) — then **r33, r34 and r35 mention
  procurement zero times.** It was not answered and not withdrawn; it stopped being asked.
- **R11 does not run on this lane.** The canonical spec carries neither a `masses` key nor
  a `pixel_claims` key — 0 claims — `pixel_check.unclaimed()` short-circuits at
  `pipeline/scripts/pixel_check.py:270-272`, and `rule_gate.py:474` declares R11
  **STRUCTURALLY INAPPLICABLE** for DELIV-001 by name. The 2026-08-09 order that every
  mechanism must open the picture is inert on the lane being built.

## 4. THREE PLACES WHERE A DOCUMENT AND THE PIXELS DISAGREE

Recorded because each is the same defect shape, not to relitigate the rounds.

1. **The r34 gate says "รอบนี้ไม่แตะเรขาคณิตเลยแม้แต่บรรทัดเดียว".** The scene dumps
   disagree: p2r32 carries `bed__cloth__acq0/acq1` (5,924 polys); p2r34 carries
   `bed__coverlet` + `bed__duvet` + `bed__throw` (23,182 polys). Visible polys move
   541,861 → 559,119 and 76.33% of pixels differ.
2. **p2r32 — the frame gate #32 shipped as "(ไม่เปลี่ยน)" — is the only frame of the six in
   r30–r35 actually built on the acquired-cloth leg**, i.e. the leg D-052 defaulted OFF.
3. **Four of the 25 masked bed/bench objects render ZERO pixels** (`bed__base_welt_c2`,
   `_c3`, `_e`, `_n`) while all four carry `in_frustum=true`; and the three acquired
   tub-chair meshes render 0 px with `in_frustum=false` while the spec item still declares
   `model: tub_chair_c`. Only 25 of 569 masses have a per-object mask at all.

Also: 5 rendered full p2 frames have no gate artifact (r2, r9, r10, r11, r32), and gate
number #31 is absent from the #1–#33 sequence.

## 5. WHAT THIS CHANGES

1. **R8's test is the wrong cut for loose furniture.** The practitioner cut — built-in is
   modelled, loose is bought — is in `knowledge/_inbox/dr-id-workflow-and-3d-render-2026-08-15.md`
   and matches the critic record. In the built scene that is `mill` 377 correctly
   hand-built against **bed 20 + nightstand 14 + bench 5 + deco 9 = 48 loose pieces we
   build ourselves.** The headboard stays hand-built: the client's sheet draws it as
   custom joinery (R12).
2. **The builder must stop being the judge of the acquire-vs-build comparison.** The
   verdict goes to the blind RANK sheet and C2/C3, never to the eye that made the
   alternative.
3. **A round that satisfies an order must change a PIECE, not a value.**

## 6. HOW TO REPRODUCE

```
git log --since=<order date> --until=<+4d> --numstat -w --format=format:'%h %ad %s'
python -c "import json; d=json.load(open('pipeline/output/room_bedroom_suite_eye_p2r35.scene.json',encoding='utf-8'))"
python pipeline/scripts/id_mask.py <blend>          # per-object pixel counts
python -c "import sys; sys.path.insert(0,'scripts'); import asset_license; print(asset_license.licence_id('CC-BY-NC 4.0'))"
```

The scene json fails to load under the Windows cp1252 default; pass `encoding='utf-8'`.
