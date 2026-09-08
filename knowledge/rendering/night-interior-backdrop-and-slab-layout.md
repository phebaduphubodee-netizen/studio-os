# Night interiors: the backdrop as key light, and stone that reads as stone

**Tier: REFERENCE (technique), with our own MEASUREMENTS marked.**
Distilled 2026-08-29 from TRN-004 — a reproduction of one public Blender interior
tutorial (a luxury penthouse bathroom, ~24 min, watched frame-by-frame; index row
`_7_HiynmdOc` in `qa/video-curriculum.json`; reproduction and gate in
`training/TRN-004_penthouse-bath/GATE-TRN004.md`). Everything here was either **read off the Blender
UI in a frame** (marked `VID`) or **measured in our own renders** (marked
`MEASURED`). Nothing here is a Thai dimension, a clearance or a code — one
tutorial is a source for TECHNIQUE only.

> **The one thing this source is NOT.** The tutorial's reference image is
> generated from a text prompt in an AI image tool. A synthesised image is a
> PRIOR, not a measurement: it cannot be cited for a dimension. See §5 — the
> repo currently has no tier for it, which is itself a finding.

---

## 1. The view out of the window is a LIGHT, not a picture

The move: put the exterior on **one plane, far outside the glass, and give its
material an EMISSION**. `VID`: the plane sits ~113 m from the room, and emission
strength is 55.

Why it is not decoration. A night interior lit only by its own fixtures has
nothing to model the window reveals, the mullions or the glass, so the glazing
renders as a black hole and the room reads as a box with black rectangles in it.
An emissive backdrop puts light on the reveal **from outside**, which is a
direction no lamp in the room can supply.

**MEASURED** (`pipeline/output/trn004_r1.png` vs `trn004_r1_noemit.png`, same
scene, one knob): with emission the glazing is the brightest thing in frame and
the mullions are modelled; without it the glazing goes black and the frame reads
as a corridor. This is a positive control, not an impression — the two files
differ in exactly one material property.

### The trap that ships with it, and it is silent
A plane ~113 m away is beyond the viewport's default far clip. It **disappears
from the viewport while still rendering**, so the builder works blind on the one
object carrying the scene's light. `VID`: clip end raised to 1415 m.

A number that only affects what you can SEE while working is exactly the kind
that gets left wrong. `pipeline/scripts/trn004_geom.py::clip_end_is_sufficient`
derives the requirement from the backdrop's own distance rather than trusting a
typed value.

### Our own lane, checked
`build_room.py` has **no backdrop plane at all** — the entire view out is an HDRI
world at infinity. An HDRI has no parallax, no occlusion, and cannot be a
rectangular bright source in the room's coordinate frame. Confirmed against the
scene of record (`room_bedroom_suite_eye_p2r90_ql.scene.json`, 496 objects): no
mass lies beyond the outer wall face except the Juliet rail.

---

## 2. A stone wall needs JOINTS, and the joints must be derived

The move: a **Brick Texture node used as a slab grid** rather than as bricks —
the stone map into Color1, a dark joint into Color2/Mortar, and the node's own
per-row offset means consecutive slabs sample the photo at different places. One
photo therefore stops reading as one photo.

**MEASURED, and it changes the recipe.** Reproducing the tutorial's node values
verbatim (`VID`: Scale 5.0, Brick Width 0.5, Row Height 0.25, Mortar Size 0.02)
and solving them out gives **100 × 50 mm units with a 4 mm joint**. That is
subway tile. It is a good ceiling and it is not a marble slab — and the node
panel cannot tell you which you built, because `Brick Width 0.5` has no unit
until you divide by Scale and fix the mapping.

This is the texture-scale defect this studio has already paid for twice, wearing
a different hat: **a shader number with no asserted real-world size.** So do not
copy the values. Name the slab in millimetres and solve:

```
pipeline/scripts/trn004_geom.py :: brick_settings_for_slab(w_m, h_m, joint_m)
    -> {"scale", "brick_width", "row_height", "mortar_size", ...}
```
Verified: `brick_settings_for_slab(1.2, 0.6, 0.004)` renders 1200 × 600 mm slabs
with a 4.0 mm joint.

### The degeneracy that only a render finds
Blender's Brick node consumes **only x and y** of its input vector; z is ignored.
So on any surface where x or y is constant — i.e. **every vertical wall** — the
grid loses an axis and collapses into **stripes**. Ceilings and floors tile
correctly while walls do not, which means the trick can look like it works on the
surface it was never aimed at.

**MEASURED**: `trn004_r1.png` (Object coords) shows vertical striping on both
side walls; `trn004_r2.png` differs only by a world-aligned box UV and tiles
correctly. The fix is per-face — take the dominant normal axis, feed the other
two **world** axes as u,v (`trn004_build.py::box_uv`). Doing it on the mesh keeps
it one Brick node instead of a triplanar blend of three, and because u,v are
world coordinates the grid runs unbroken across a corner, the way a real
setting-out does.

### Our own lane, checked — and the claim narrowed
It is **not** true that our wall wood has no per-board variation. `_image_wood`
(`build_room.py:1898`) already carries a 180 mm leaf grid that snaps the mapped
coordinate to a leaf id and gives each leaf its own sampling window of the flitch
(`:2018`, `:2027-2054`), per-leaf tone stepping 0.96–1.04 (`:2085-2096`), and a
per-object random offset via Object Info → Random (`:1956-1971`).

What it genuinely lacks:
- **no joint of any kind** — no mortar, no groove, in any wall/floor/casework
  material in the lane that renders;
- the leaf grid is **world-space and tied to no built board**, so a modelled
  groove and a shader leaf edge need not coincide;
- `_slat_rhythm` (`:3254`) *does* paint a batten rhythm with a groove — and is
  unreachable, gated behind `SLAT_FIELD_AS_TEXTURE = False` (`millwork.py:62`);
- **TRN-002 already solved this properly and it was never wired back**:
  `trn002_geom.herringbone(joint=2.0)` shrinks every plank so a darker joint
  shows through, and `trn002_build._herringbone` gives each of 458 planks its own
  UV frame with a position-derived offset *and* flip. `build_room.py` uses none
  of it. The studio's own distilled-but-never-wired shape, again.

**NOT established**: I could not attribute the C2 item "a visible mirror axis
mid-wall" to the `PINGPONG` fold at `:2062`. That fold is on Z with period 1.0
against `grain_run_m = 2.8` on a 2.8 m wall, so it lands at the wall **top**, not
mid-wall. The mirror C2 saw is still unexplained.

---

## 3. Lights are a physical tuple, not a brightness

`VID` reads two light panels: **4248 K / 326.8 W / square / 1 m / 126° spread**,
and later **451.6 W / disk / 1 m / 75.3°**. Every one of the five fields is a
physical quantity with a unit. None of them is "brightness".

Our lane carries **kelvin** (`cct_k` is a canonical spec key, allowlist-validated
and fail-closed to 2200–3000 K, and it reaches real light datablocks) and
**watts**. It carries **size** for only some fixture families, and it carries
**shape** and **spread** nowhere — every area light is left at Blender's default
square with a 180° spread.

Spread is the one worth having: it is the difference between a wash that stays on
its wall and one that fogs the whole room, and it cannot be recovered by changing
the wattage.

### The sconce is geometry, not a light
`VID`: the wall sconce is an **emissive plane behind a frosted panel**, hex
`#FFD389`, strength dialled 34.7 → 15.0 after one look. The reason to prefer this
over a light object is not the trick — it is that **the glowing thing is visible
geometry**, so the frame contains a source for its own highlight. A light object
with no fixture is the "lit from nowhere" defect by construction.

---

## 4. Small props, built the cheap honest way

All four pass the build/acquire test (boxes with radii, a swept measured profile,
an extruded outline) — none of them needs a sim or a sculpt:

| prop | how | number |
|---|---|---|
| undermount basin | inset the counter top face, then shrink/fatten the inset face down; **the shrink offset IS the vessel wall thickness**, so it is never typed twice | `VID` −10.1 mm |
| folded towel | a rounded box plus one thin lip slab along the front edge that reads as the fold; the stack is that box repeated, each **resting** on the one below | stack of 3 `VID` |
| rolled towel | a cylinder laid on the stack, axis one radius above its top face | — |
| mirror | a plane extruded a few mm — not zero, because a mirror with no thickness has no edge, and the edge is what makes it read as glass on a wall rather than a hole in it | `VID` 4.898 mm |

Plus **shade-smooth-by-angle with sharp edges kept** (`VID` 30°) so curved parts
read smooth while the box edges stay crisp.

Our lane already has a folded-stack vocabulary (`softgoods.folded_stack`,
`folded_knit`, `cushion`) and hollow-shell precedents (`bathroom.bathtub_parts`,
`build_room._arc_shell`). What it does **not** do is smooth generated geometry by
angle: every smooth-shading site sets `use_smooth = True` on 100% of polygons
with no dihedral test, and the angle-based split that exists
(`_normalise_acquired`, `build_room.py:11555`) is wired **only to imported
meshes**. The capability is present and pointed at the wrong half of the scene.

---

## 5. Two gaps this reproduction opened that are not about pixels

**(a) There is no tier for a synthesised reference.** All four of the repo's
ladders are closed and exhaustive — the dimensional order, the heights ladder,
R4b's reference-of-record (delivered work only), R12's sheet-first — and none of
them contains a rung for an AI-generated image used as an input you build FROM.
The repo codifies generated imagery only as an OUTPUT. Until a tier exists, a
generated reference should be treated as what it is: a **declared assumption**,
ranked below every measured source, and never cited for a number.

**(b) ambientCG is not reachable from this repo, and it publishes the one number
our own rung wants.** The asset pages carry the map's real-world size next to the
download links (`VID`: a travertine set declared "ca. 1.2 m"), which is exactly
the `dimensions_mm` that `texture_scale.py` exists to assert. Our only fetcher
knows Poly Haven (`assets.py:31`). The sidecar schema is already
publisher-agnostic — `write_sidecar` takes `source` as a free string — so the
blocker is one function: `texture_scale.py::_backfill`, whose publisher URL is
hard-coded.

---

## 6. What the reproduction cost, and what it caught

Following the video rather than summarising it is what produced everything above.
Two of the findings are defects in **our** code, and neither was reachable by
reading:

1. **`build_room._add_key_sun` built the sun and never linked it to a
   collection**, from commit `2a13fe6` until 2026-08-29. It passed its own
   fail-closed beam-direction check, printed its success line and returned 1
   while contributing **zero light**. Measured: an identical 8 W sun over one
   plane, unlinked vs linked, renders mean luma **0.084 vs 134.008**; `key_sun`
   occurs **zero times** in the three most recent scene dumps of record. Every
   check in that function interrogates the datablock — energy, elevation,
   azimuth, beam-vs-glass dot — and **all of them are true of a light that is not
   in the scene.** The repo had already written "a direction cannot be verified
   by an amount"; the third face of the same trap is that neither can be verified
   without asking whether the thing is there at all.

2. **`p2_exit.autocorr_peak`'s noise floor could exceed the signal's own
   ceiling.** A normalised autocorrelation cannot exceed 1.0, yet the shipped
   floor (`mean + 3·sd` over 8 shuffled surrogates) reached **1.260** on a
   perfect self-tiled repeat — so the rung printed `not periodic` on an input
   that is a literal repeat. Across 12 surrogate seeds at n=8 the floor ranged
   0.541–1.260 and **seed 0, the one pinned in the code, was the single seed of
   twelve that blocked it**. Pinning a seed made the number reproducible without
   making it right. Fixed two ways: 32 surrogates (0.625–0.980 across the same
   seeds, none above 1.0), and a structural refusal — a floor ≥ 1.0 is now
   `could_not_run`, never a pass.

Both are instances of the same law this studio keeps re-learning under new
names: **a rung that can only return "clear" has not been shown to work.**
