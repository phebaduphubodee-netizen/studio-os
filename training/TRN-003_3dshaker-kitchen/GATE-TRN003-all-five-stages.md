# GATE — TRN-003, all five tutorial stages run · 2026-08-29

Closing frame: `06_post/out/TRN003_final.png` (uncommitted — `training/**/*.png` is
gitignored). Before/after: `06_post/out/BEFORE_AFTER.png`.

## WHAT WAS DECIDED, AND HOW TO UNDO EACH ONE

| # | decided | reverse by |
|---|---|---|
| 1 | The island slab is a **stadium** with the arris in the mesh, not a bevelled box | `stadium(..., arris=0)` in `build_kitchen.build_room`, or go back to `box()` + a BEVEL modifier |
| 2 | `DRUM_R` 231 → **194**, `ISL_CENTRE_X` 2318 → **2347** | edit `NEAR["u_right"]` in `derive_island2.py` back to 925.0 and re-run `make_plan.py` |
| 3 | `TRANSOM_Z` 2352 → **2460** | edit `room_spec.py` |
| 4 | `B4_island_top` **withdrawn** from `guide_lines()` | uncomment it in `room_spec.guide_lines()` |
| 5 | The orthogonality "check" in `solved-camera.json` is **withdrawn as an identity** | restore the old `checks.orthogonality` string |
| 6 | `shadow_delta` **refuses** a clipped lobe and refuses to compare two frames at different points on the tone curve | raise `CLIP_HI` above 255 and `LIT_MATCH` above 255 |
| 7 | The mood is settled with **the sheer IN** — it is the fill light | `keep_sheer: false` in the palette file's `light` block |
| 8 | Albedos are **solved**, and the light's colour error is reported rather than absorbed | `CHROMA_OWN = 1.0` in `palette_solve.py` makes it absorb everything again |
| 9 | No ceiling texture; **the plate's own sd of 1.8 decided it** | put `"plaster"` back in `materials_trn003.TEXTURE` |
| 10 | Post does **not** run a generative upscaler | the reasons are in `06_post/post.py`'s docstring; `pipeline/scripts/upscale.py` is the disclosed alternative |
| 11 | `critique_bundle` **refuses** a prompt carrying build history | delete `blindness_scan`'s call site |

## SPEND

Renders: 24 (4 blockout · 13 mood/balance sweeps · 7 split/texture). One 36-minute video
transcript. Three CC0 texture fetches (~40 MB). One Gemini `2.5-pro` C3 call. One local C2
agent. One five-agent recon workflow with adversarial verification.

## THE MEASUREMENTS THAT MOVED

| what | before | after |
|---|---|---|
| blockout vs plate, rms over the fitted guide lines | 33.59 px (max 74.81) | **4.36 px (max 9.4)** |
| built scene vs `room_spec.boxes()` | never compared | **15 masses, 0.00 mm, blocking** |
| floor lit−shadow vs the plate's 76 | 128–154 whatever the sun or sky did | **96, PASS at +20** |
| our light's chroma vs the plate's | not measured | 1.258/1.005/0.845 → **1.139/1.002/0.910** |
| drum diameter | 462 mm | **389 mm** (near silhouette 188.93 px, far corroborates to 3.4%) |
| `recurrence` width self-check | 0.0000% — could not fail | **3.4% — a reading** |

## TRIAGE — C3 (Gemini 2.5 Pro, cross-vendor)

Archived: `06_post/out/critique/critique-TRN003_final/ANSWER_gemini25pro.md`. Five items.

1. **No contact shadow at the drum bases** (high) — **ACCEPTED, and measured.** At the near
   drum's contact the plate's floor is at 31% of its far-field luminance; ours is at 87%.
   Ours is **5.4× weaker**. Lane: lighting; the drums have no enclosure under the slab and
   the fill is almost uniform. Named in RESUME as open item 3.
2. **Stool frames too thin to be structural** (high) — **REFUTED, with a number.** The tubes
   are r = 11 mm, i.e. 22 mm diameter, read off the plate's own stool at the same camera. A
   22 mm steel bar-stool tube is a stocked section. What Gemini is reading is not the
   diameter but the absence of a seat pad and stretcher detail, which is item 5's territory.
3. **The pelmet's underside is wavy** (medium) — **ACCEPTED.** It is the sheer's own free top
   edge: `build_curtain` gives the head a wave and there is no track, pocket or return. Same
   class as the DELIV lane's curtain-track item. Lane: geometry.
4. **Walls read flat and digital** (medium) — **PARTLY ACCEPTED, and the split matters.** The
   CEILING's flatness is defended by a measurement (patch sd 1.8/1.1/1.4 over 11,200 px — the
   plate's ceiling is that flat). The WALLS have no such measurement, so the item stands
   against them and is recorded as an open measurement, not as a refutation.
5. **Terrazzo top clashing with the marble splash** (low, self-declared opinion) —
   **ACCEPTED.** Our procedural stone is too speckly and the post blend keeps that speckle;
   the plate's island top is a pale stone with soft directional veins. Lane: materials.

## TRIAGE — C2 (blind local cold critic)

Archived: `.../ANSWER_claude-local-c2.md`. **27 items.** Its own top three:

1. **"A kitchen with no kitchen in it"** — no sink, tap, hob, extractor, cabinet door,
   drawer line, handle, socket or switch anywhere. **ACCEPTED WITHOUT ARGUMENT and it is the
   most important item either critic filed.** It is also the honest state of the round: this
   was a BLOCKOUT taken through the tutorial's material and post stages, and the tutorial's
   own stage 1 is *"first finish modeling the whole scene"*. We ran stages 3b–5 on a scene
   that had never finished stage 1. Lane: geometry, and it is the next round.
2. **Nothing casts a shadow on the floor** — the same defect C3 ranked first, found
   independently by a different vendor on the same frame. Two-vendor agreement.
3. **The sheer is a flat card with a tiled repeat of identical hard-edged shapes** —
   **ACCEPTED.** Those shapes are our canopy's 4,200 flat leaf quads projected through the
   glazing; every leaf is the same quad, so the shadow pattern is a stamp. Lane: geometry.

Of the remaining 24, the ones that are new information rather than restatements of 1–3:
**items 6 and 8** (the stools have no lap clearance and pass into the counter face — our
stools are at X = 3250 against an island face at 2972, so they sit 278 mm clear of it and
that IS a real overlap in the frame: ACCEPTED, geometry); **item 9** (the stone speckle is
the same pixel size at every distance — ACCEPTED, our procedural noise is in object space
but the aggregate reads as a screen effect); **item 10** (the underside of the slab is
brighter than its top — ACCEPTED, same root as C3's item 1); **item 21** (visible black
speckle noise — ACCEPTED, 256 samples is not enough for this glass-and-sheer scene, and the
post blend's coherence floor keeps some of it). **Item 11** (no walkway) — **REFUTED with a
measurement, and the refutation is itself hedged**: the walkway is 1072 mm, which is a
walkway; but `room_spec` records that the same number cannot decide NKBA's 1067 mm because
its inputs are worth ±100 mm, so the honest answer is "there is a walkway, and its
compliance is undecidable from this plate".

## THE ITEM ABOUT THE RUNG, AND IT IS FIXED

C2 filed, under NOTES ON THE BUNDLE, that the blind prompt itself leaked: it named an
earlier render, reported how many items a previous critic filed against it, and narrated
this studio's own headline defect with its offset in millimetres. **Confirmed by grep.** The
bundle builder refused the target and the anchors by construction and had never looked at
the prose it copied in.

Fixed both ways: `templates/cold-critic-prompt.md` no longer names a round, a render, a
date, an item count or a past defect, and `critique_bundle.blindness_scan()` now REFUSES to
write a bundle whose prompt carries any of those. It is tested against the exact text that
leaked (convicts) and against the cleaned template (passes), and the negative control
already earned its keep — it caught the first regex missing `trn002_mat_r34_quick` because
of a word boundary that could not match after an underscore.

**What it cannot catch, and this is not a hedge:** paraphrase. "A previous round had trouble
with the island" leaks exactly as much and no pattern will see it.

## WHAT THIS GATE DOES NOT CLAIM

The frame is not close to the plate and nobody should read this as saying otherwise. Two
critics on two vendors independently ranked the same first defect, and C2's top item is that
the room has none of the objects a kitchen is for. What closed here is the **workflow** —
all five of the tutorial's stages now run end to end from a spec of record, with the mood
settled by a measurement instead of a dial, and with three instruments that could not fail
turned into instruments that can.
