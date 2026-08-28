# สิ่งที่มืออาชีพเช็คก่อน / What practitioners check first — eye, light, camera, repetition

> **PROVENANCE: promoted 2026-08-28 from the video-study units staged the same day.**
> The staged units are the record of what was said and where; this file carries only what
> **two or more INDEPENDENT professionals, in different disciplines, said the same thing
> about.** A rule stated once by one person stays in `_inbox` and is not here.
>
> Units distilled into this file:
> - `knowledge/_inbox/video-study/2026-08-28-render-review-where-does-your-eye-go-vXVLTBvLCbo.md`
> - `knowledge/_inbox/video-study/2026-08-28-archviz-critique-seven-renders-UmJaVnO3Sxw.md`
> - `knowledge/_inbox/video-study/2026-08-28-lighting-and-composition-aRWwOhjbvfs.md`
> - `knowledge/_inbox/video-study/2026-08-28-lighting-plan-process-and-the-grid-argument-4ORbpY6d9Zk.md`
> - `knowledge/_inbox/video-study/2026-08-28-interior-photography-the-editorial-look-is-a-focal-length-pkMssQPul9o.md`
> - `knowledge/_inbox/video-study/2026-08-28-surface-realism-tiling-and-fabric--VgtSL5ZpYc.md`
> - `knowledge/_inbox/video-study/2026-08-28-why-a-room-feels-off-Sz4TC-VJ2PQ.md`
>
> **TIER: REFERENCE.** Trade and craft practice spoken on camera, not measurement of any
> artefact and not statute. Nothing here outranks `knowledge/codes-th/`, the client
> contract, an owner-signed decision, or **a measurement of the work being reproduced**
> (the anchor pool). Every number is a STARTING POINT for a render.


> **SOURCE VIDEO IDS carried by this file** (the staged units above hold the full
> quotations and timestamps; a video whose content did NOT reach this file is
> deliberately absent): `vXVLTBvLCbo` · `UmJaVnO3Sxw` · `aRWwOhjbvfs` · `4ORbpY6d9Zk` · `pkMssQPul9o` · `_XmBszDmyck` · `-VgtSL5ZpYc` · `Sz4TC-VJ2PQ` · `qbZoZiZg6I4`

## ลำดับอำนาจ / Authority

1. A **measurement of the artefact being reproduced** outranks everything below.
2. `knowledge/rendering/render-defaults.md` and `cycles-lighting-camera-presets.md` remain
   the live defaults; this file supplies *questions to ask of a frame*, not replacements
   for those values.
3. This file.

---

## 1. THE FIRST QUESTION: WHERE DOES THE EYE GO

**Two independent sources, one archviz reviewer and one lighting design director, both open
with it.**

- Archviz: *"where does your eye go?"* — asked once per submitted image across nine images,
  and the answer was never the subject. The thieves he names are **brightness** (*"it's a
  little too bright, a little bit too intense"*), **saturation** (*"the saturation is like
  way out of whack"*), **specularity** (*"my eye is kind of ping-ponging"*), and **empty
  bright exterior**.
- Lighting design: *"as we enter a space the eye is naturally drawn to the brightest
  point"*, and therefore *"think what are the most important features in your space — this
  is where you should be creating the most intense illumination."*

**Runnable form for this repo.** On the frame of record, report (a) the brightest region,
(b) the most saturated region, (c) whether either is the intended subject. Both are
computable from the render plus `id_mask`; the gap has never been the instrument, it has
been that **nobody asked the question**.

Corollary, from the same lighting source: *"the most challenging aspect of a lighting design
can often be **deciding what NOT to light** — by lighting too many features you're at risk of
having a washed out effect."* Stated independently by the architect drawing a lighting plan
(*"resist this tendency to really light and centre on every object"*) and by the archviz
reviewer (*"make sure your project is in light"*). **Three sources.**

---

## 2. UNIFORM LIGHT IS THE DEFECT; CONTRAST IS THE GOAL

**Four independent sources, and it is the single most-agreed statement in the study.**

| Source | Statement |
|---|---|
| lighting design director | *"please no more grids of downlights on the ceiling… the grid layout produces a very flat and lifeless effect, everything is lit with the same intensity"* |
| architect / lighting plans | *"designing the lighting is not about evenly lighting spaces, it's developing contrast"*; *"what I don't want to do is create an even grid of fixtures across the whole ceiling"* |
| archviz critic | *"if you have the sun facing both this front and the side you'll not see correctly the dimensions of the building"* — one plane lit, one in shadow, *"this gives the three dimension"* |
| designer (recessed layouts) | *"contractors, electricians in particular, are really fond of the grid, and there's a reason for that: the lights run straight down one bay, it's not complicated. That's not what we're aiming for."* |

**The synthesis, and it is the useful part:** an evenly-lit floor is the answer to an
INSTALLATION question, not a design one. Spacing formulas (ceiling height ÷ 2; ≤ 4 ft
apart, ≥ 2 ft off the wall) are defaults for uniform ambient coverage; **the same study
contains a designer calling those formulas "all nonsense"** and the architect who states the
÷2 rule immediately qualifying it with *"of course that's going to be informed by the actual
light fixture that you choose."* **Record the disagreement; do not average it.**

### 2.1 CONSEQUENCES THAT ARE BUILDABLE
- **Never one source, one type.** *"never ever use just one source, one type. One. Never."*
  A room's ambient being N identical recessed fixtures and nothing else is named as a
  failure by two sources.
- **Layer**: ambient / task / accent, stated identically by the lighting director and the
  architect.
- **Aim, don't just place**: gimbal fixtures *"so it adjusts and hits artwork or cabinetry"*.
- **The ceiling can be the source.** *"we could have this ceiling act as a sort of luminous
  plane… adjustable mono points that are really starting to wash this ceiling with light…
  and if this is a wood ceiling this creates a nice ambient light surface to light up the
  room."* This is the only proposal found that answers "bright with no source in frame"
  **without putting a fixture in the shot**.
- **Conceal the source so the lit thing is the bright thing.** *"if you are lighting a
  shelving unit… the light positioned in the underside of the shelf is always visible, and
  with the light being the brightest part of the unit, it's what you notice… shouldn't you
  be focusing on the items displayed on the shelves instead?"* A luminaire must be
  **baffled** — the lamp recessed inside a housing that is itself flush; *"if the source of
  light is flush on the ceiling or floor it's likely to be very glary."*

### 2.2 THE PHOTOGRAPHER'S VERSION — subtract, then split into key and fill
An interiors photographer physically blocks the secondary window *"because I didn't want any
natural light coming from the right to flatten and fill in the shadows"*, then:

> *"I will do my best to take the natural light within the space and then take it down to a
> point where the ambient light has now become what you might consider **fill** light — but
> then I build back up the rest of the light, or what you might consider **key** light, with
> the flash."*

**Directly implementable in a render engine**: demote the ambient/portal until it reads as
fill, then introduce a controlled directional key. This repo reached the same lever
empirically at p2r78, when dimming the daylight portal was what finally moved D2/D3/D6.

### 2.3 LUMINANCE RATIOS — the only quantitative frame found
From a lighting engineer, for a **workplace** (so the numbers do not transfer wholesale to a
bedroom; the STRUCTURE does): task **1:1**, immediate surrounding **3:1**, surrounding
**5:1**, background/walls **10:1**, measured as surface luminance in cd/m². The failure mode
he opens with is ours inverted: *"when you're using downlights or luminaires which have low
luminance, then it might occur that the top of the walls and the ceiling being too dark."*

A frame whose whole content sits inside ~1.5:1 is flat **by definition**, whatever its
exposure.

---

## 3. A FIELD OF ONE REPEATED THING READS FAKE

**Four independent sources across three disciplines. This is the most transferable finding
in the study.**

- Archviz critic, on assets: *"they're all placed at the same scale, rotation"* — the fix is
  *"just rotate the tree"*, and on an interior, *"I can see the same grain of wood. Like make
  this one and then make this two and then just move them, shift them around, change the
  scale a little bit."*
- Second archviz critic: *"it's okay to use the same asset but at least try to rotate the
  asset, maybe change a little bit the colour"*, and *"in nature you never have exactly the
  same green tone throughout the whole forest."*
- Texture craft: **beyond ~10 tiles the eye always sees the pattern**; and the refutation of
  the obvious fix — going 1k → 8k costs *"53 times the amount of memory"* and still cannot be
  approached closely. The four levers are **per-tile rotation** (with noise to break the
  seams), **hue/saturation/value variation at two scales**, **a second similar material
  blended in at MATCHED VALUE**, and **real height displacement**.
- Interior designer, on objects rather than textures: *"when it's just art print, art print,
  art print, art print — just all flat things on the wall — that falls flat. When it's just
  all shelves everywhere, that can fall flat."* The prescribed fix is *"something sculptural
  and three-dimensional"* — **a different KIND of object, not more of the same.**

### 3.1 THE ONE PLACE THE RULE INVERTS
For **boards and veneer**, free random rotation is wrong: the trade produces a *controlled
drift*, not randomness (see `knowledge/materials/veneer-figure-and-panel-layout.md` §7). Use
the archviz rule for scattered props and textures; use the trade rule for anything laid up
from sequential leaves.

---

## 4. CAMERA — three numbers, from three professionals

| Property | Value | Source |
|---|---|---|
| **focal length** | **≥ 35 mm; aim ~50 mm** for an editorial interior | interiors photographer: *"most interior photos and those editorial pieces you're probably going to find are shot somewhere around 35 millimetres and above"*; he aimed at 50 and shot 38 |
| **eye height** | **≤ ~120 cm** | archviz critic: *"most of the interior photography it's done with the camera at chest level, so it's probably maximum height about around 120"* |
| **verticals** | **0°** | architectural photographer: *"it is a rule, it's not even up for grabs — your photographs must be vertical… if the image is not completely straight that's the first sign of an amateur"*; independently, the archviz critic fixes verticals on every submission |

**Why the focal length matters more than it looks.** Our deliverable is judged beside
delivered studio work, i.e. beside editorial images. A wide lens is identified on sight:
*"it increases the perspective of the floor which makes it look like the floor is ramping
up… it can look a bit estate-agenty"*, and a third source names the artefact from the other
end — *"that's when the focal length is like super low, you know, like a 15 or 12, and it
just kind of distorts all of it."*

### 4.1 TWO FRAME-LEVEL DEFECTS WITH CAMERA FIXES
- **Merging masses.** *"they're just kind of blending in together and I just wanted a sliver
  of separation between those two items — so I raised the camera a little bit and moved the
  camera a little bit more forward."* A silhouette collision is a CAMERA property.
- **Too much of an object**: a mass that dominates without being the subject is cropped down
  until it merely *frames* the bottom of the image.

### 4.2 RECORDED DISAGREEMENT — aperture
Architectural photography uses **f/8-f/11** on a tripod. This repo's own ground-truth study
of professional archviz .blend files found **f/1.4-2.4**. Both conventions are real and they
disagree; settle it against the anchor pool, not against one source.

---

## 5. TWO MORE THINGS SAID TWICE

- **Styling is done FOR THE FRAME, at the camera.** A photographer with the designer beside
  him: *"we start refining and fine-tuning placement of little tchotchkes, knick-knacks and
  items within the shot… move the blanket a little bit to the right… some more fine tuning
  with the rotation of one of the books on the coffee table"*, and only then *"I'm going to
  start taking my official exposures."* A studio's shoot-day footage shows the same act.
  **A per-camera styling pass is a distinct step from styling the room.**
- **Objects are habitually chosen too small.** Two designers agreeing unprompted about
  bedside lamps: *"everybody goes too small on their bedside table lamps. If whatever size
  you pick, it's too small."* — *"Go like two sizes bigger. I promise you."* A third states
  it as a room rule: *"let each element be large and unapologetic."* And the reason it is not
  a trivial finish item: *"having the correct bowl or the correct vase almost feels like a
  frivolous thing… but it ridiculously really can tie the space together… it IS actually a
  focal point."*

---

## 6. WHAT THIS FILE DELIBERATELY DOES NOT CARRY

- **Anything said once.** Single-source rules stay in the staged units.
- **Numbers for a bedroom's luminance ratios.** §2.3 is a workplace standard; a residential
  target has to come from the anchor pool.
- **Colour temperature.** The study contains 2200-2700 K (luxury residential lighting
  design) against 3000 K (US electrical practice, and one archviz source), plus a warning
  that a warm source on **brown walls read pink** until it was changed to 4000 K. Three
  positions and a coupling to our own wood-dominant palette: unresolved, and it belongs to
  the lighting solve with the anchor pool as arbiter.
- **Judgements of beauty.** Nothing here lets the builder convict its own frame (R7d); these
  are questions to ask and report, and conviction still comes from C2, C3 or the owner.
