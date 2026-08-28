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
> - `knowledge/_inbox/video-study/2026-08-28-two-long-form-a-designer-lecture-and-a-live-render-clinic-9eImuRVG4qM.md`
>   (§8-§9, promoted in the second pass)
> - `knowledge/_inbox/video-study/2026-08-28-drapery-grammar-and-the-triforce-of-realism-JgQdCad1Iiw.md`
>   (§4 only — the realism unit; the drapery half of that unit belongs elsewhere)
>
> **TIER: REFERENCE.** Trade and craft practice spoken on camera, not measurement of any
> artefact and not statute. Nothing here outranks `knowledge/codes-th/`, the client
> contract, an owner-signed decision, or **a measurement of the work being reproduced**
> (the anchor pool). Every number is a STARTING POINT for a render.


> **SOURCE VIDEO IDS carried by this file** (the staged units above hold the full
> quotations and timestamps; a video whose content did NOT reach this file is
> deliberately absent): `vXVLTBvLCbo` · `UmJaVnO3Sxw` · `aRWwOhjbvfs` · `4ORbpY6d9Zk` · `pkMssQPul9o` · `_XmBszDmyck` · `-VgtSL5ZpYc` · `Sz4TC-VJ2PQ` · `qbZoZiZg6I4` · `0OVEJVbklV0`

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

## 6. THE THREE FORCES STATED AS ONE CLAIM — AND A THIRD ACQUISITION ROUTE THE RULES NEVER NAMED

> Source video id for this section: `0OVEJVbklV0` (Kaizen, *"The Key to Realism in Blender
> (or 3D)"*, 14 min 34 s). Staged unit:
> `knowledge/_inbox/video-study/2026-08-28-drapery-grammar-and-the-triforce-of-realism-JgQdCad1Iiw.md`
> §4 — the unit's other half is drapery and does not belong to this file.
> **6.2 is SINGLE-SOURCE AND SPONSORED; read its disclosure before using any of it.**

### 6.1 SUBJECT · LIGHTING · CAMERA — an independent arrival at this file's own shape

`[00:44]` The three forces that decide whether an image reads as real are named as **the
subject, the lighting, and the camera**. The example given is an animation of *"only simple
models in a simple scene"* that was removed from r/blender for being judged real footage:
*"The combination of model quality, environment, natural lighting and a hero role for the
camera work had many believe that this was real."*

**What this ADDS is exactly one thing: the triad as a single claim.** Every value in this
file arrived from a source speaking about ONE force — the eye-and-brightness question (§1),
the contrast argument (§2), the camera band (§4) — and the three-way split above them is
**this file's own assembly**, never something a source stated. Here a fourth discipline (a
Blender generalist; not the archviz reviewers, not the lighting director, not the interiors
photographers) opens with the same split unprompted — though **only the opening carries
it**: from `[02:49]` the video is a sponsored scanning tutorial, so this is a corroborating
OPENING FRAMING and not a video built on the triad. **That is still an independent arrival at
the STRUCTURE, so count it as the corroborating voice for the file's shape** — one source per force previously, now one source for the shape itself.

**What it does NOT add, said plainly so nobody reads it as more:** no measurement, no
threshold, no procedure, no fixture, no focal length. It cannot settle a single disagreement
recorded in §2, §4.2 or §10, because it carries no number at all.

**The one operational consequence.** The frame in the anecdote passed as real on *simple
models* — so "the frame reads fake" is not by itself evidence that the geometry is at fault,
and the unit's own reading is that a defect of this kind is unlikely to sit in any one of the
three. This repo has repeatedly spent whole rounds inside one force. When a critic reads a
frame as unreal, the triage names **which of the three** before a round is planned; *"unreal"*
alone does not select a lane. Conviction still comes from C2, C3 or the owner (R7d) — this
paragraph changes how a round is FRAMED, not who may close it.

### 6.2 SCAN — a third branch beside build and acquire · **[1SRC · SPONSORED · unverified]**

**THE DISCLOSURE FIRST, because it is the reason this is knowledge and not an advert.** The
rest of that video is a sponsored tutorial for the scanning app it recommends, and it says so
on camera `[02:49]`: *"my personal 3D scanning app of choice is Kiri, who — to be fully
transparent — also sponsored this video."* Its content from that point is photogrammetry
technique sold by an interested party, not general realism.

**And it fails this file's own admission bar** (see the PROVENANCE block: two or more
independent professionals, or it stays in `_inbox`). It is carried here anyway as a **POINTER
with a debt**, not as a rule: **the technique must be confirmed from a non-sponsored source
before any spend, any purchase, and before it is written into a rule.** Until that
confirmation exists, nothing in 6.2 outranks anything.

The claim `[02:07]`: *"we can take a huge shortcut in creating realistic models by using the
power of **3D scanning** — this technique will let you capture **minute details,
imperfections, textures** and the most complex geometry you can think of in a matter of
minutes… all you really need is a **phone**."*

**Why it is worth the row at all:** the studio's acquisition rule (R8) is a two-way fork —
BUILD what can be produced from measured boxes, radii, profiles and outlines, or ACQUIRE
everything free-form. **Photogrammetry from a phone is a third branch**, and it is the branch
that yields the *"imperfections"* that neither of the other two gives: a built object has only
the imperfections someone parameterised, and a bought object has only the ones its author
modelled. This file is REFERENCE tier and **does not amend R8** — the amendment is an owed
decision row, and its precondition is the non-sponsored confirmation above.

**The scanning conditions, recorded because they are the part that would generalise** (if
confirmed) `[04:57]` — they are lighting and coverage discipline, which is why they read like
the rest of this file rather than like a product:

| Condition | Statement |
|---|---|
| light quality | soft, **single-colour**, **EVEN** — the one place in this file where even light is the goal rather than the defect, because the scanner is reading surface colour, not composing a frame (§2 is unaffected) |
| direct sun | never |
| best free condition | overcast — *"nature's softbox"* |
| the object | needs **feature points**; **featureless objects scan badly** |
| capture | **overlap every frame** |

**What does NOT transfer, so it is not rediscovered later:** this is a route to a model of a
**real object physically in front of the camera**. It does nothing for the work being
reproduced — the anchor pool is another studio's delivered photographs, and a photograph
cannot be scanned. It also says nothing about licence, scale assertion on ingest, or trade
dress, all of which still bind whatever route the mesh arrives by.

---

## 7. COMPOSITION — promoted 2026-08-28 once a second and third source arrived

> Source video ids for this section: `sdIMItJ8sx8` (composition rule set) · `pkMssQPul9o` and `_XmBszDmyck` (two interior photographers) · `2stNv09sbe8` (facing).

At first promotion the composition material was single-source and was held in `_inbox` under
this file's own two-source rule. Three sources now carry it.

- **A focal point needs a COUNTERWEIGHT, not just a position.** *"you cannot just simply put
  your focal point in one of the intersections and finish there. The best result will be
  achieved when you **balance it with something**."* Thirds can also divide CONTENT, not only
  mark points.
- **Gaze direction is load-bearing.** *"even the **look direction** of the character is
  important, because we naturally look in the same way the character is looking"*, and *"the
  image will look really weird if she will look the other way."* Two more sources apply the
  same rule to non-human objects: a chair turned inward *"directs her attention this way"*, and
  pillows faced toward the door for the first impression. **Objects are oriented toward where a
  person arrives from or looks toward.**
- **Symmetry is about visual WEIGHT**: *"two things don't have to be exactly identical but they
  should have the **same visual weight** and balance on both sides."*
- **Colour can carry the focal point**: one saturated element in an otherwise restrained field.
- **Add canvas before cropping**, then crop to a stated ratio on the thirds — so the crop is not
  limited by what the camera happened to capture.
- **Foreground closes the edges** and pushes the eye to the subject; work the environment,
  background and foreground, not only the model.
- **A viewport composition OVERLAY is used at the camera-setup stage** — thirds, diagonals,
  golden ratio and triangle, and a centre cross for symmetry, drawn over the live camera.
- The disclaimer every source repeats: *"these are only guidelines… artists should know them
  but should never see them as limitations."*

## 8. FOUR CHECKS THAT ARE ARITHMETIC ON AN EXISTING FRAME

Promoted with §7. None needs a re-render.

1. **Clipping.** *"**maximum black and maximum white are wrong**… areas that have **no detail,
   just black holes** in your image… would be considered a mistake"*, and *"we **get lost** in
   this area because that's just black and there's nothing interesting to guide our eyes."*
   Measure: the fraction of pixels at 0 or 1 carrying no detail.
2. **Brightest and most saturated region versus the subject** (§1's question, made numeric).
3. **A lamp cannot beat the sun.** *"you cannot really see the daylight inside of the shot
   because you're **overwhelming it with the light that's inside**… no lamp, no light bulb can be
   stronger than the sun."* Measure: the interior-fixture contribution against the daylight
   opening in the same frame.
4. **Verticals at 0° and focal length in band** — both known before the render from the camera
   itself.

And one thing to ADD rather than measure: **deliberate small imperfection is praised and asked
for more of** — *"you've added a small **wobble** on your tiles, which is absolutely amazing…
this just helps us fool our viewer a little bit better, and this is something that you just need
to do **MORE of**."*

## 9. THREE IDEAS FROM PRACTICE THAT ARE NOT RULES

Recorded because they change how a round is framed, not what a value is set to.

- **The lift comes from the move that was not necessary.** The 1936 Bugatti Atlantic's riveted
  seam existed because the alloy could not be welded — and was KEPT on the later cars that could
  have been welded, because people liked it. *"**You always want a reason for doing something,
  but you're looking for the thing that isn't necessarily the logical or necessary move that
  brings, that LIFTS a project.**"* A room assembled entirely from necessary moves is complete
  and inert. R10 forbids an object that cannot be justified; it does not forbid one whose
  justification is not functional.
- **Two named orders of work.** *Diagram first, architecture follows*: **"she makes a diagram of
  how she's going to use the room and the architecture falls into place around it"** (Eileen
  Gray; and Le Corbusier's own cabin). *Room first, furniture dropped in*: **"the room was
  designed as an environment and the chair was dropped into it."** Both are legitimate; a lane
  that has only ever run the second should at least know that it has.
- **The same room without curation.** A palace bedroom photographed decades later with the same
  canopies, the same light fixtures and *"some decent modernist furniture"* — *"it shows what
  happens when you get sloppy."* Same content, no curation, visibly worse. That is the
  half-made verdict named by an elite practitioner, with the cause placed on **curation** rather
  than on content.

---

## 10. WHAT THIS FILE DELIBERATELY DOES NOT CARRY

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


---
