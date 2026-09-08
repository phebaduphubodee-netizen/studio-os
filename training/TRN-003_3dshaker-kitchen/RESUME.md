# TRN-003 — 3D Shaker kitchen reproduction · ALL FIVE STAGES RUN 2026-08-29

Following *How to Make a Realistic Interior in Blender (New Technique)* — 3D Shaker,
`dHS4u9YaIDw`, 36:42 — by DOING it, not summarising it. Plate is est living's `gh-11` of
Garden House by McCluskey Studio, photography Timothy Kaye.

`training/**` is TEXT ONLY (owner decision 2026-08-04, enforced by `.gitignore:52`): every
`.png` under this tree is local and uncommitted, including the plate and every render.

## State

| Stage | Status | Artefact |
|---|---|---|
| 1 Reference | DONE | `01_reference/plates/` — 19 project photos, hero 1440×1920 |
| 2 Camera | DONE, with one withdrawn check | `02_camera/solved-camera.json`, `camera_solve.py` |
| 3 Blockout | DONE, island re-measured twice more | `03_blockout/room_spec.py`, `derive_island2.py`, `derive_island3.py` |
| 3b Mood | **SETTLED BY MEASUREMENT** | `04_mood/palette-from-plate.json` → `light`, `shadow_delta.py` |
| 4 Split + Texture | RUN | `05_build/materials_trn003.py`, `04_mood/palette_solve.py` |
| 5 Post | RUN | `06_post/post.py`, `06_post/out/TRN003_final.png`, `BEFORE_AFTER.png` |

Run it end to end:

```bash
cd training/TRN-003_3dshaker-kitchen
python 03_blockout/fit_and_overlay.py --fixed          # camera vs plate: rms 4.36 px
python 03_blockout/make_plan.py                        # plans + poses + the negative control
blender -b --factory-startup -P 05_build/build_kitchen.py -- \
        --stage texture --samples 256 --res-pct 100 --passes \
        --out 05_build/out/p9_sun_noisy.png                # light comes from the palette file
blender -b --factory-startup -P 05_build/build_kitchen.py -- \
        --stage texture --samples 256 --res-pct 100 --passes --denoise \
        --out 05_build/out/p9_sun_denoised.png
python 06_post/post.py 05_build/out/p9_sun_noisy.png 05_build/out/p9_sun_denoised.png \
        --out 06_post/out/TRN003_final.png --hp-opacity 0.15 --sheet 06_post/out/BEFORE_AFTER.png
python 04_mood/shadow_delta.py 01_reference/plates/REF-HERO.png <render> \
        --patch floor 250 1620 1440 1900
python 04_mood/palette_solve.py <render>               # report; --apply writes back
```

## What is solid, and what the number is

* **The blockout lands on the plate to rms 4.36 px, max 9.4** (was 33.59 / 74.81 this
  morning). Two things moved it: the transom was re-derived from its own fitted line
  (2352 → 2460 mm, and the unprojected height has a spread of 1.0 mm across 1.9 m of the
  glazing plane, which is the check), and a guide line that was not on the feature it named
  was withdrawn.
* **`spec_agreement()` in the builder, 15 masses at 0.00 mm.** It reads the BUILT scene and
  compares every mass to `room_spec.boxes()`, and it fails the render closed. It found an
  11 mm error on its first run (a stool built to its overall height at the tube CENTRELINE),
  a 12 mm one (the glazing straddling the wall datum instead of sitting in it), and a bevel
  modifier that GREW the island by 10 mm instead of rounding it.
* **The mood is settled by a measurement, not a dial** — `04_mood/palette-from-plate.json`
  → `light`. With the MEASURED sun in, the floor reads lit 180 / shadow 92 = 88 against the
  plate's 176 / 100 = 76 — **PASS at +12** on a tolerance of 25, with the lit levels only 4
  apart. **The finding that got it there: the sheer is the fill light.** With the curtain
  hidden as the tutorial does it, a 7.5× sun sweep and a 10× sky sweep both stayed at
  128–154, because the shadow in this room is lit by sun BOUNCE and not by sky — turning the
  sun down turns the fill down with it. Put the sheer back and the same scene lands at 90;
  put the measured sun in as well and it lands at 88 with the levels matched.
* **Camera 106 mm, f = 4236 px, yaw 30.85° off the kitchen wall.** 3D Shaker's own fSpy
  solve of this photo gave rotation Z −30.302°; ours −30.85°, 0.55° apart.
* **Average-blur colour `#A39583`** — byte-identical to the hex he eyedroppers at 15:00.
* **The island is a STADIUM, and its arris is in the mesh.** It was a bevelled box in every
  frame this lane produced before today.

## What was WRONG and is now fixed — read this before trusting an old number

* **THE BUILD SCRIPT HAD NOT IMPORTED SINCE THE ISLAND FIX.** `build_kitchen.py` asked for
  `RS.DRUM_X` and `RS.ISL_STONE_X0`, which `room_spec.py` stopped defining when the island
  was turned onto its true axis. Every image in `05_build/out/` older than today was made by
  the wrong island, and nothing said so. The spec and the builder were two transcriptions of
  the same numbers; fourteen dimensions have been moved into the spec and `spec_agreement()`
  now convicts on the difference.
* **THE DRUMS WERE 19% TOO FAT.** `derive_island2.py` read the near drum's right silhouette
  at u = 925. There is no edge at 925: the strongest gradient anywhere in u ∈ [900, 950] is
  0.4–2.3 grey levels per px, and at u = 891 it is 4.2–83.2. `DRUM_R` 231 → 194,
  `ISL_CENTRE_X` 2318 → 2347. Confirmed by an independent adversarial re-measure that
  reproduced 890.95 ± 0.04 px and supplied the vertical-silhouette control the first read
  never had.
* **`recurrence`'s SELF-CHECK COULD NOT FAIL.** `make_plan.drum_block()` COMPUTED the far
  drum's silhouette width from the near drum's radius, and `recurrence.solve` then "checked"
  the two against each other: `width_agreement = 0.0000%`, exactly zero, on both instances.
  Both widths are now read off the plate. The far one corroborates the near to 3.4% — a real
  number, inside the 5% bar.
* **THE CAMERA SOLVE'S HEADLINE CHECK WAS AN IDENTITY.** This file used to say *"the two
  horizontal axes come out 90.02° apart and nothing forced that."* Something did:
  `camera_solve.focal()` sets `f = sqrt(-(vpA-px)(vpB-px))`, which is exactly the focal that
  makes them perpendicular. Force the principal point to x = 300, 600, 720 or 900 and the
  orthogonality is 90.0000° every time while f moves from 3983 to 4331 px. Four nonsense
  input lines also return 90.000000000. **The check that CAN fail** is the reproduction of
  the fitted lines with the derived camera, and it is the 4.36 px above.
* **`shadow_delta` COULD BE PASSED WITH THE EXPOSURE KNOB.** Same lights, only exposure
  moving: −2.0 → 128 FAIL, −1.0 → 99 PASS, 0.0 → 70 PASS. Its own docstring argued this was
  impossible. It is now refused two ways: a lobe against the end of the range is not a
  reading, and two frames must sit at the same place on the tone curve before their
  differences are compared. Both refusals are in the file with the numbers that earned them.
* **`--stage split` and `--stage texture` did not exist.** The docstring described them; the
  only use of `o.stage` was `if o.stage in ("blockout", "mood")`, so both were accepted
  silently and rendered an un-overridden scene. Both are implemented now.
* **TRANSOM_Z 2352 → 2460**, untagged before, DERIVED now.
* **`WALKWAY_MM` is 1072 and CANNOT decide the code question.** NKBA's one-cook aisle is
  1067 and the walkway lands 5 mm over it, while ±10 px of drum base row — which is what
  those rows are actually worth — swings it from 1026 to 1194, and `ISL_W` is separately
  declared not measurable from this plate. The honest verdict is 1050–1150 mm, UNDECIDABLE
  here. A verdict sized smaller than its own inputs' noise is the defect, not the number.

## What is NOT solid — pick this up first

1. ~~THE SUN'S AZIMUTH IS STILL A DIAL~~ — **CLOSED, and it was closed by the gnomon.**
   Azimuth **92.3° ± 0.55**, elevation **18.3° ± 0.65**, from four bar-stool hoop legs whose
   floor contact is visible in sunlight: each base unprojects to the floor plane and a
   1-parameter search over WORLD plan azimuth finds the darkest ray leaving it, so the
   search parameter is a world angle and no image slope is ever read. Positive control: the
   cabinet toe/floor junction is a world line along +Y, true heading 90.000 by construction,
   and it unprojects to 90.214° at rms 0.11 px. The 180° ambiguity was broken by pixels, not
   by a sentence. `sun_solve.py`'s 21.58° is refuted with no new measurement needed: at that
   azimuth the ray to a lit stool base must cross the glazing at x = −8615 mm, missing the
   glass by 8.4 m for EVERY elevation — which is exactly why renders at it put no beam in
   frame, and why the lane turned it into a dial instead of doubting it. **The frame now
   reads floor lit 180 / shadow 92 = 88 against the plate's 176 / 100 = 76 — PASS at +12
   with the lit levels 4 apart, the best this lane has produced.**
2. **THE FRAME GOT FLATTER AS THE COLOUR SOLVE CONVERGED.** The light-chroma error fell
   49% → 25% across two iterations and the picture lost contrast and material separation
   while it did. That is a metric improving and the picture getting worse, and it is
   recorded rather than argued away.
3. **CONTACT SHADOW, and it is measured.** At the near drum's base the plate's floor is
   darkened to 31% of its far-field value; ours is darkened to 87%. Ours is 5.4× weaker.
   C3 filed it as the single item to fix first and the measurement agrees.
4. **Two DECLARED GAPS in the texture stage.** No free marble slab and no free travertine
   exist: Poly Haven's entire marble holding is 17 assets and not one is a slab, and
   `travertine` returns zero across 854. Both are procedural stand-ins. Escalating them is a
   priced procurement ask, not a modelling task — but run the two zero-cost probes named in
   the sourcing report first, because *unbought* is not *unavailable*.
5. **The tall bank has no door joints and the oven is a flat glossy plane**, which is why
   `palette_solve` refused the `black` family by name: a 4× difference on a diffuse surface
   is not an albedo error, and it was specular.
6. **Cryptomatte passes are not produced.** Blender 5.1 moved the whole scene compositor
   (`scene.node_tree` is gone, `CompositorNodeComposite` is undefined, `OutputFile` has no
   `base_path`); the noisy/denoised pair is made by rendering twice instead. Nothing in our
   post step needs a mask, and `id_mask.py` already does that job if a later round does.

## The critic ladder on the closing frame

* **C3 (Gemini, cross-vendor)** ran and is archived at
  `06_post/out/critique/critique-TRN003_final/ANSWER_gemini25pro.md`. Five items. Its top
  one is the contact shadow above — accepted, with the measurement.
* **C2 (blind local cold critic)** was spawned on the same bundle; its answer archives as
  `ANSWER_claude-local-c2.md` in the same directory.
* Bundle contents are our own render plus PROMPT.md and nothing else, by construction.

## Standing notes from the video that are still true

* **the elevation was the bigger error, not the azimuth.** The dial sat at az 90 / el 26;
  the measurement says 92.3 / 18.3. The azimuth was accidentally within 2.3° and the
  elevation was 7.7° out — so the number that *looked* settled was the wrong one to trust;
* the material override turns glass opaque and blacks the room (his 10:57) — and it does the
  same to the sheer, which is why `--keep-sheer` in the mood stage renders a black frame;
* geometry that exists to cast a shadow must be IN the sun's path, which is set by the sun
  angle, not by where a tree would look right;
* `8.100 W/m²` in the video is a Photographer-addon unit, not stock Blender's;
* **his post stage runs four Magnific AI passes at rising creativity and paints in the
  results.** The tutorial's final image is substantially generated. We do not run it, and
  the reason is in `06_post/post.py`'s docstring.

The distillation this round owed the reproduction charter is at
`knowledge/_inbox/trn003-3dshaker-study/what-a-tutorial-workflow-actually-assumes.md`.
