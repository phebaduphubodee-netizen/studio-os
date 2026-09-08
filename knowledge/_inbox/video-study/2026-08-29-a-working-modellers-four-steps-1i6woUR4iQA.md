# A working modeller's four steps — and the one his bevel chapter convicts us on

**Source (REFERENCE tier).** `1i6woUR4iQA` — <https://www.youtube.com/watch?v=1i6woUR4iQA> ·
Vertex Arcade, *"Make ANY FURNITURE in Blender in 15 Minutes"* · 16 min 00 s · 2023-03-08 ·
171,638 views. Chapters as published: Introduction 00:00 · Research 00:38 · Modelling 01:16 ·
Materials 11:07 · Lighting/Rendering 13:11 · Outro 15:24.

Watched 2026-08-29. Frames via `pipeline/scripts/watch_local.py` (100 scene-aware over the full
clip) plus a uniform 5-second `ffmpeg` pass over 01:16–08:30 (87 frames), because scene-change
selection returns almost nothing on a continuous screen recording and left the modelling section
— the meat — with four frames in three minutes. Transcript via `youtube-transcript-api`
(278 cues); the skill's own caption path is still SSL-broken on this machine.

**Why this clip and not another.** R8 splits BUILD from ACQUIRE, and the repo's own count is that
48 hand-built loose pieces drew **7.56 critic items each** against millwork's 1.01. Every other
entry in the curriculum critiques a finished room. This is the only one that builds **one loose
piece of furniture end to end** — research, model, material, light — by someone who does it for a
living, so it is the only one that can be laid beside `build_room.py` step for step.

**Method note, because it changed the answer twice.** Each claim of the video was audited against
our code by an independent agent and then handed to a second agent told to REFUTE it. Thirty
findings went in; **eleven came back refuted**, including two the builder had already written
into an earlier draft of this file. Every number below either survived that pass or was measured
by the builder afterwards on the live artefact.

---

## 0. His four steps, and the sentence he repeats three times

**Research → Modelling → Materials → Lighting/Rendering.** He states them at `[00:13]` and closes
at `[15:53]` with a three-item takeaway he has already given twice: **use reference, get
measurements, and apply the transforms.** The apply-transforms card is on screen full-frame at
`[02:46]`; his reason is mechanical — `[02:49]` *"in most cases, if you're having any troubles
with modifiers in Blender, it's likely because of bad transforms."*

---

## 1. THE FINDING THAT JUSTIFIES THE HOUR — his bevel chapter, in our units

At `[07:14]` he stops on a finished model and says it is still missing something. His reason is a
reading of the reference, not a preference: **every reference photo carries a highlight along the
edges**, and a bevel is how you get one. Prescription: every wooden part, **segments = 2**, **a
few millimetres at most**, judged by eye.

**His number does not transfer. His reason does — and separating the two is the whole finding.**
He is shooting a PRODUCT on a white sweep, where the object fills the frame and 3 mm is many
pixels. Ours is a room. Measured in-engine on the scene of record
(`room_bedroom_suite_eye_p2r90_ql.blend`, 18 mm lens), converted to the delivered 2400×1800:

| in-frame mass | area | bevel | mm/px | delivered px |
|---|---:|---:|---:|---:|
| `floor` | 107.79 m² | 5.00 mm ×3 | 3.11 | **1.61** |
| `wall_4` | 33.37 m² | 5.00 mm ×3 | 5.46 | **0.92** |
| `wall_3z` | 23.94 m² | 5.00 mm ×3 | 6.55 | **0.76** |
| `mill__ตู้/ชั้น_BF10_(dressing)__carcass` | 20.12 m² | 1.20 mm ×3 | 3.26 | **0.37** |
| `mill__ผนังระแนงหัวเตียง_BF14__slats` | 16.26 m² | 1.20 mm ×3 | 2.48 | **0.48** |

**127 of 168 in-frame bevelled masses — 76% — subtend less than one pixel in the delivered frame.
Three reach two pixels.**

`MILL_BEVEL_M = 0.0012` was chosen for a good reason, written at its own definition: *"joinery
arris: a cabinet edge is nearly sharp, not a 5mm round-over."* **That is true about the world and
it renders as 0.37 px — nothing.** Meanwhile the global suite bevel that `_bevel_edges`' own
docstring calls impossible (*"a 5 mm round-over on a cabinet door is not a thing that exists"*)
is the only one still wider than a pixel out there — and `scene_dump`'s docstring independently
complains about the same 5 mm from the other direction, that it rounds a small box "into a
lozenge".

**So three parts of this repo argue about a millimetre and none of them ever asked what it is
worth in pixels.** Every bevel decision in our history was taken in the mm domain; the mapping
between the domains was never an instrument. That is the class of defect this repo keeps paying
for — a number that is correct about the world and wrong about the picture — and R11 exists
because of it.

**BUILT THIS SESSION** (see §6): `scene_dump` now computes `mm_per_px` per object against the real
camera, and `edge_highlight.py` does the division and prints it into the render path. It is a
**reporting line, not a cut**, because the pixel width an edge highlight needs has never been
measured off delivered work — and a threshold invented in the rung would carry the rung's
authority instead of the anchor pool's.

---

## 2. RESEARCH — and the correction the refutation pass forced

His research step is a **retailer product page** for reference images *and* dimensions (IKEA first:
several angles, several lighting conditions and the measurements on one page; Amazon second for
360° views). `[01:02]` *"make sure that you find the measurements, because if you want to model
realistic furniture, you NEED to use real world scale."* Then, before geometry: **a cube at the
object's overall dimensions**, kept as a guideline box everything must fit inside (`[01:16]`; he
types 32 × 36 × 30 in). Only then is the reference dragged in as an **image plane**, aligned,
fitted inside the box, and its **opacity dropped** so he can model over it.

**The builder's first draft said "we have no retailer tier and 8 declared-assumption heights need
one." The refutation pass killed the example and left a better finding.** What survives:

* the heights ladder really carries **no catalogue/retailer tier** — 0 occurrences of
  retail/catalog/manufactur/ikea/sku/link across all 19 rows;
* but **the retailer research already exists in this repo** as `ffe-candidates.json`, and **none of
  its five consumers is reachable from `rule_gate.py`, `build_room.py` or `plan_status.py`** — so
  sourced retail dimensions never touch a render. The queue-with-no-consumer defect, landing on
  the exact step the video calls the most important;
* **and it has one live pixel consequence, which is the whole value of the finding:** the spec's
  `side_table h=480` drives the built nightstand (measured 481 mm in the p2r90 dump) while the
  selected IKEA BRIMNES is **530 mm**. Any catalogue tier must first resolve that against
  `dim_check`'s live side_table band of 380–480 ±25, which the 530 mm pick fails.

Two smaller ones, both verified: the **guideline box for acquired meshes is derived FROM the mesh
it is checking** (55 of 64 model-fit verdicts) — a flattering scorer, the shape this repo has now
filed fourteen times; and **no reference image ever enters the Blender scene** (`EMPTY_IMAGE` 0
hits repo-wide). Our reference is only ever opened *beside* the work by a human or a critic, never
in the same coordinate frame as the model.

---

## 3. MODELLING

Low-poly first — `[02:32]` keep it low and deal with smoothness later. Sharp edges get a **crease**
(Shift+E); visible faceting is fixed with **Shade Auto Smooth**, and he warns against reaching for
more subdivisions instead. Thicknesses are **typed in real units** (Solidify 2 in for the arm, 1 in
for the seat shell). The second leg is a **Mirror** with clipping — after transforms are applied.

Verified against us: **every hand-built curved mesh is smoothed at 100% with no angle rule**, so
hard rims are smeared — the opposite half of his crease-then-auto-smooth pair. And **SUBSURF is 0
on the delivered frame** although the code path exists.

### The cushion — the class R8 sends to ACQUIRE, built from boxes

His recipe, `[04:17]`–`[07:14]`: two **cubes matched to the visible seams** (the seams are the
datum) → **bevel weight 1** on all edges → Subdivision → **holding edge loops** rather than creases,
because a cushion should read soft so the corners are *supported* not sharpened → ~5 loops each way
across the top → proportional editing to lift the crown, **Alt+S to inflate** → apply → Sculpt
**Mesh Filter/Smooth**, a little (`[06:12]` don't go too far or the definition is lost) → **Cloth
brush** for a few wrinkles, with the warning that decides it, `[06:24]` *"be subtle with this
because this cushion is fairly rigid so it wouldn't have a lot of wrinkles"* → a **Bevel modifier
in WEIGHT mode**, 2 segments, ~3 mm, profile pushed off 0.5, to cut the seams → **Alt+S the seam
centres inward** for depth.

* **The metric for upholstery is the SEAM.** R8 sends free-form to ACQUIRE because *"free form has
  no metric to iterate against."* His cushion has one, it is visible in any reference photo, and it
  is where the geometry starts rather than where it ends.
* **His fold count is deliberately LOW**, on a designer's reasoning about stiffness. That agrees
  with our instrument and not with our frame: the p2r78rc exit crops read the throw at **3.682×**
  and the duvet at **2.115×** the delivered comforter's fold energy. Verified addition: **on the
  acquired path there is no knob** — the folds arrive with the purchase.
* **What not to take:** one hero object at product-shot distance is not a licence to hand-model the
  room's soft goods, and R8's two-iteration stop-loss stands. **No weight-mode seam bevel exists
  anywhere in this repo**, which is the one piece of his cushion technique that is pure millwork
  and would transfer.

---

## 4. MATERIALS — where we match him exactly, and where the frame does not

`[11:29]` *"you can try and create these procedurally… but that is a huge waste of time, so just go
and download some."* Minimum set at `[12:23]`: **Colour + Roughness + Normal**. He repeats the two
silent traps twice each: **Roughness and Normal must be Non-Color**, and the **normal texture needs
a Normal Map node** because the BSDF socket is purple and the texture output is yellow.

**Our shipping builder matches that line for line.** `_pbr_material` (in `build_room.py`) wires
Diffuse as sRGB, Rough/Metal/**nor_gl** as Non-Color, and puts a `ShaderNodeNormalMap` between the
normal texture and the BSDF; `_img_node` sets the colorspace explicitly at every one of the 8
texture-load sites rather than inheriting it; the set is even the **OpenGL** normal variant, so the
DirectX green-channel convention is already handled. Four things the builder expected to find
wrong, all already right.

**And then the frame.** Builder's census of the 135 materials actually worn in the scene of record:

| | count | what they are |
|---|---:|---|
| a real `NORMAL_MAP` node | **73** | **every one a vendor material off an ACQUIRED mesh** — `Box`, `Cork`, `Fabric.001`, `Handle`, `Medieval market_grain` |
| a `BUMP` node only | 16 | **every one ours** — `m_mill_cement`, `m_mill_backing`, `curtain_sheer`, `curtain_opaque`, `bed_base`, `bed_duvet`, `bed_mattress`, `ceiling_paint`, `e5_pelmet` |
| neither | 46 | |

**Not one material this pipeline BUILDS carries a normal map. The only real relief in our frame was
bought.** And the Bump the millwork does get is worse than it looks: the verifier measured
`oak_veneer_01_Displacement_2k.jpg` at raw **249–253, with 3.75 M of 4.19 M pixels at exactly 251**
— so `Distance = 0.0004` delivers about **6.4 µm** of relief, tilt mean 0.001°, while the unused
`nor_gl` carries tilt mean **2.24°**. Three orders of magnitude. **This also mis-attributes a
parked conclusion in our own code** — the `--wood-bump` bracket that concluded "the surviving
suspect is the ROUGH-MAP's contrast" was turning a knob attached to a near-constant map.

Verified alongside it, all on the pixels:

* **the sheers are 100% procedural noise on 17.640% of the frame** — colour, roughness and normal
  all from `TEX_NOISE`, on the one surface the window light passes *through*; 14 of 21 `_woven`
  call sites pass no `maps=`, and the `if maps and _FABRIC_MAPS:` plumbing already works on the
  Object-coord box projection, so no UV work is needed to fix it;
* **the signed floor rendered base-colour-only** — constant roughness 0.5, flat normal — because its
  set was Diffuse-only at render time. Its `Rough_2k` and `nor_gl_2k` landed in `a1188c1`
  (2026-08-29 09:52), two days after that blend; the next build picks all three up, **and nothing
  in the repo records that a signed surface's map roster moved**;
* **our retint deletes the acquired mesh's COLOUR texture on 9.811% of the frame** — two sites,
  `_retint_upholstery` and `_retint_legs`, both removing `bc.links`. The vendor roughness and normal
  survive, so it does not read as plastic; what is lost is albedo break-up;
* **the microcement is stamped with a wood leaf grid.** `_image_wood` has no wood/not-wood branch,
  so `plastered_wall_03` gets `PLANK_PITCH_MM` leaves and per-leaf tone steps of ±4%. On 37 objects
  / 61.1 m², the BF09-3 drawer fronts at 878 mm carry **≈5 hard vertical block seams each** — it
  reads as large-format travertine tile, not monolithic microcement. A manufacturing impossibility
  on the frame's second-largest millwork material, **found by opening the picture**.

### UVs and the colour-grid test — the question is live, our answer is a different mechanism

`[08:26]`–`[11:07]`. He unwraps, assigns a **4K Colour Grid**, and reads three measurements off it:
even squares / equal letter size (**texel density**), **letter direction** (`[10:30]` — it decides
which way the wood grain runs and which way the fabric runs), and no overlapping islands. Fix:
**Average Island Scale**, then **Pack Islands with rotation disabled** so the direction work
survives.

The vocabulary is absent repo-wide: `average_islands_scale` 0 files, `pack_islands` 0,
`smart_project` 0, `cube_project` 0, `Color Grid`/`color_grid`/`colorgrid` 0. We hand-write UVs for
three surfaces only (`_planar_uv` rug + floor, `_wall_uv` walls) and the largest material in the
frame — the millwork veneer at 23.13% — is **box-projected**, never unwrapped.

**That is not simply a gap, and the refutation pass is what made this paragraph honest.** Four
separate grain-direction findings were filed against the veneer and **all four were refuted** on
re-measurement of the artefact. What stands:

* **on SCALE our instrument is stronger than his.** `texture_scale.py` asserts every mapped tile
  against the vendor's own dimension metadata **at ingest** — it is what caught the floor at
  **1.4118×** and the rug at **4.8134×**. A checker shows a problem; the sidecar names the wrong
  number. Keep ours.
* **on DIRECTION we have nothing that is not refuted, and one that stands:** which way the
  floorboards run is a side effect of a hard-coded `co.x` in `_planar_uv` — decided by nobody,
  checked by nothing.
* **and the box projection is what blocks the normal-map fix**, which is why §4's first row is not a
  one-line change: a tangent-space normal map needs a UV layer, and the millwork has none.

---

## 5. LIGHTING / RENDERING — half transfers, half must not

**Transfers, and we already do it.** `[14:38]` the 4096 default is far too high; use **128–256**
plus the **Denoising Data** pass and a **Denoise node**; heavy sampling only pays for reflections,
fog or SSS. `configure_cycles(samples=128)` with adaptive sampling at 0.01 and `OPENIMAGEDENOISE`
(`configure_cycles` in `build_room.py`) is already exactly there, and a probe in the repo shows the render-time OIDN
route is equivalent to his compositor node. Wall-clock is recorded at ~25–28 min per frame at 256
samples / 2400×1800. **Nothing to change.** Our HDRI wiring is a line-for-line match to his as
well — Poly Haven, Environment Texture, Mapping node, Vector = Generated.

**Does not transfer.** The rest is a **product shot**: a white sweep, lit by **one neutral studio
HDRI**, deliberately colourless so it does not tint the white ground. Our frame is an interior whose
light must come from its own openings and fixtures, and this repo has already paid for one source
carrying both the power and the colour temperature. *"Just use an HDRI"* is right for a catalogue
plate and wrong for the bedroom.

*(An audit finding that our client-facing world HDRI is "a green foliage map" was **refuted**: the
verifier decoded all three RGBE files and measured `brown_photostudio_02_4k` at R/G 1.027,
B/G 0.9 — neutral, and the one actually in use.)*

---

## 6. WHAT WAS BUILT FROM THIS CLIP

Two rungs, both wired into `_score_deliverable` on the render path, both registered in
`qa/coverage-map.json`, 46 tests:

* **`transform_check.py`** (blocking) — a mesh carrying `SOLIDIFY/BEVEL/MIRROR/ARRAY/SCREW/SKIN/`
  `WIREFRAME` must stand at scale 1, because those read their widths in LOCAL space while every
  AABB-reading rung in this repo reads WORLD size and stays green. **It passes on the scene of
  record — 496 meshes, 0 non-unit, 244 bevel modifiers, none of them scaled — and that is why it
  was worth building.** The invariant was held by `_bake_transform_to_mesh`, whose 45-line docstring
  argues its case entirely in TEXTURE space and never mentions a modifier;
  `bpy.ops.object.transform_apply` appears **0 times repo-wide**. It was true by a side effect
  nobody wrote down. A positive control fires every run, and a dump written before the `scale` key
  exits 2 rather than reading as clean.
* **`edge_highlight.py`** (reporting line) — §1's measurement, in the render path at every round.

And one design correction found **by running it on a real artefact instead of a synthetic one**:
the first live report read the millwork carcass at 0.18 px, because a `_ql` playblast blend stores
**1200×900** where the delivered frame is 2400×1800. Both numbers say the same thing here, which is
exactly why it would have been easy to keep and wrong to keep. `scene_dump` now ships `render_res`
and `edge_highlight` **refuses without it** — R11's pixel rung already wrote that law in its own
words, that a sub-pixel comparison at half resolution is a different measurement.

---

## 7. What the clip is actually worth, said plainly

It **refuted more of the builder's expectations than it confirmed**. Going in, the guesses were:
missing bevels, roughness maps loaded as sRGB, a normal texture wired straight into the BSDF, and
brute-force sample counts. **All four were already right in this repo**, two with a recorded reason,
one (`nor_gl`) a detail the video never reaches.

What it actually bought:

1. **The bevel chapter, converted into our units** — 76% of in-frame bevelled masses invisible at
   delivery resolution, and a whole class of decision that had never been asked in pixels.
2. **The materials chapter, measured** — not one material we build carries a normal map; the only
   real relief in the frame was bought; the microcement wears a wood grid.
3. **`ffe-candidates.json` has five consumers and none of them is on the render path** — his step 1
   exists here and never reaches a picture.

And one thing arrived **twice**: *apply the transforms* is his closing line, and the identical
advice has sat in this repo since **2026-08-23** in the BlenderKit DR
(`knowledge/_inbox/blenderkit-month/2026-08-23-dr-maximizing-the-month.md`) — with **no
DISTILLATION-LEDGER row** and **no code that reads it**. Now guarded.

See [[choose-the-mechanism-from-the-failure]] · [[reference-before-build]] ·
[[texture-scale-asserted-and-instrument-blindness]] · [[eye-finds-what-measurement-finds-how-much]] ·
[[rule-with-no-reader]]
