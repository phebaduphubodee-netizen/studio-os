# TRN-003 — 3D Shaker kitchen reproduction · PAUSED 2026-08-29 (owner: "พักงานนี้ชั่วคราว")

Following *How to Make a Realistic Interior in Blender (New Technique)* — 3D Shaker,
`dHS4u9YaIDw`, 36:42 — by DOING it, not summarising it. Plate is est living's
`gh-11` of Garden House by McCluskey Studio, photography Timothy Kaye.

## State: stages 1–3 of 5 done, 4–5 not started

| Stage | Status | Artefact |
|---|---|---|
| 1 Reference | DONE | `01_reference/plates/` — 19 project photos, hero at 1440×1920 (he used 750×1000); `board/contact-sheet.png` |
| 2 Camera (fSpy) | DONE | `02_camera/solved-camera.json`, `camera_solve.py`, `edgefit.py` |
| 3 Blockout | DONE, island corrected twice; PLAN + POSE + CLEARANCE now run on it | `03_blockout/room_spec.py`, `derive_island2.py`, `make_plan.py`, `poses.json`, `PLAN_*.png` |
| 3b Mood | PARTIAL | `05_build/build_kitchen.py`, `04_mood/shadow_delta.py`, `sun_solve.py` |
| 4 Texture | NOT STARTED | — |
| 5 Post | NOT STARTED | — |

## What is solid

* **Camera.** f = 4236 px (≈106 mm on 36 mm), horizon v = 1031, level, principal point
  (720, 1031). The check that matters: the two horizontal axes come out **90.02°** apart
  and nothing forced that. 3D Shaker's own fSpy solve of this photo gave rot Z −30.302°;
  mine, from sub-pixel edge fits, −30.85°.
* **Scale.** Camera height 1421 mm from the SP01 Michelle **LOW** stool (815 mm). Cross
  check: Wolf 30″ double oven measures 771 vs published 762.
* **Average-blur colour** of the plate = **#A39583** — byte-identical to the hex he
  eyedroppers at 15:00. `04_mood/reference-average-color.json`.
* **HDRI** — Poly Haven *Kloofendal Overcast (Pure Sky)*, the exact file, CC0, in
  `assets/shared/cc0/hdris/`.
* **`shadow_delta.py`** — his Photoshop lit-vs-shadow eyedropper as an instrument
  (desaturate → Otsu → median of each lobe → refuse when not bimodal). Plate floor reads
  lit 176 / shadow 100.
* **Island axis = 87.3°, parallel to the kitchen wall**, from the two bronze drums.
  Walkway **1043 mm** to the bench front (the earlier "1094" was a stale comment from
  a previous island centre; `WALKWAY_MM` computes 1043). That is a REVIEW, not a PASS:
  under NKBA's 1067 mm one-cook aisle and well under P&Z's 1219 mm opposing-counter
  figure. Overlay proof: `03_blockout/island_MEASURED.png`; plans:
  `03_blockout/PLAN_corrected.png` and `PLAN_as-built-WRONG.png`.

## What is NOT solid — pick this up first

1. **Light balance.** The sun/sky ratio is still a dial, not a measurement. Best
   `shadow_delta` so far: floor delta 68 vs the plate's 76, on a clipped frame.
   `sun_solve.py` measured the azimuth at 21.6° off the window wall but renders at that
   azimuth put no beam in frame; the last renders used az 90 as a dial. **Unresolved.**
2. **The blockout has not been re-rendered since the island was corrected** — every image
   in `05_build/out/` predates the fix.
3. Stools, curtain and canopy are stand-ins, not the real products.

## Resume commands

```bash
cd training/TRN-003_3dshaker-kitchen
python 03_blockout/fit_and_overlay.py --fixed        # camera vs plate, wireframe
blender -b --factory-startup -P 05_build/build_kitchen.py -- \
        --stage mood --quick --sun-w 900 --sun-az 90 --sun-el 30 \
        --hdri-strength 0.5 --exposure -2.5 --out 05_build/out/next.png
python 04_mood/shadow_delta.py 01_reference/plates/REF-HERO.png <render> \
        --patch floor 250 1620 1440 1900
```

## The four findings owed to the pipeline — ALL FOUR ARE NOW BUILT (2026-08-29)

Owner order the same day: *"ทำให้หมดเลย ไม่ต้องรอถาม ผมจะไปนอนแล้ว"*. Row:
`qa/owner-orders.json` -> `ORD-2026-08-29-pose-blindness-six-lanes`. Report:
`docs/research/2026-08-29-pose-blindness/FINDINGS.md`.

1. **Never read a direction off a straight line fitted to a curved edge.** Two spans of
   the island's oval edge gave -0.031 and -0.049 and I walked past it.
   -> `pipeline/scripts/edge_direction.straight_direction` REFUSES on disagreement and
   says in the refusal not to average, because the mean of two chords is a third chord.
2. **A vanishing point far off-frame is ill-conditioned.** 7711 vs 7917 decided the
   island's axis; the true answer was -1546.
   -> `edge_direction.require_conditioning` + `vanishing_check.MIN_AXIS_ANGLE_DEG`.
   **And the fix turned out to be sharper than the finding.** An angular FAMILY test
   would not have caught it: the chord sits 0.03 deg off family B's vanishing ray and
   is a textbook member of it. What was rotten was the FAMILY — B's two supporting
   lines are **4.24 deg** apart, against family A's 25.97. Conditioning is the gate,
   computed before any assignment is allowed to mean anything. Note also that
   `vanishing_check.py`, written the day before from this same tutorial, had a
   conditioning refusal that would have PASSED family B: its `1e-6` scaled determinant
   is sin^2(theta), i.e. **0.057 deg** — a singularity guard, not a usability gate.
3. **Two identical objects at two depths are the best direction instrument in a photo.**
   -> `pipeline/scripts/recurrence.py`, with the self-check that makes it a measurement:
   base-row depth vs silhouette-width depth must agree to 5% or the answer is REFUSED.
   `pose_check` now DERIVES a reference heading from it rather than accepting a typed
   one — R9's law ("a position that can be derived must never be typed") reaching the
   rotation axis.
4. **Nothing in this repo checked kitchen clearance** — and the reason was worse than
   "no instrument". `clearance_check.py` existed, `dimensional_rules.v0.2.json` had held
   `kitchen_NKBA.island_clearance_all_sides` since 2026-07-02, and
   `knowledge/ergonomics/residential-clearances.md` had held the 1219 mm opposing-counter
   figure for months. **51 of the 75 rule keys in that file had no reader in any script.**
   -> `clearance_check._kitchen` reads all seven; `Item.penetration_to` gives an overlap
   its MAGNITUDE (`gap_to` clamped to 0.0, so 420 mm of interpenetration and a hairline
   touch returned the same number); and `rules_reader_check.py` is the ratchet that stops
   it recurring — a NEW rule with no consumer fails the gate. 44 today, down from 51.

Plus the two the report ranked above them:

5. **Orientation is now a checked quantity** — `pipeline/scripts/pose_check.py`, angular
   distance, wired into `rule_gate.check` AND `check_room`. The island as built prints
   **90.0 deg** and exits 1.
6. **The plan view is a required artefact** — `pipeline/scripts/planview.py`, and
   `rule_gate.audit_planview` fails a lane that has a blockout and no plan newer than it.
   `03_blockout/make_plan.py` draws both islands side by side; in plan the defect takes
   a quarter of a second.

Also standing, from the render loop itself:
* the material override turns glass opaque and blacks the room (his 10:57);
* geometry that exists to cast a shadow must be IN the sun's path, which is set by the
  sun angle, not by where a tree would look right;
* `8.100 W/m²` in the video is a Photographer-addon unit, not stock Blender's.
