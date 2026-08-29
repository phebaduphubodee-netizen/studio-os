# What a professional interior workflow assumes but does not say — TRN-003

> **Tier: REFERENCE (staged).** Source: *How to Make a Realistic Interior in Blender (New
> Technique)*, 3D Shaker, `dHS4u9YaIDw`, 36:42, auto-captions pulled 2026-08-29 (805
> segments) plus this studio's own reproduction of the same photograph end to end.
> **n = 1 tutorial, n = 1 reproduction.** Everything below is either quoted from the video
> or measured on our own frames; where it is neither, it says so.
>
> The reproduction-curriculum charter makes distillation a GATE CONDITION, not a follow-up:
> *"a round whose measurements produced transferable knowledge does not close until that
> knowledge is written to `knowledge/_inbox/`"*. This is that payment for TRN-003.

---

## 1. THE STAGE ORDER IS THE TEACHING, AND IT IS NOT THE ORDER MOST PEOPLE WORK IN

He says it out loud at 05:00: *"what most people do is they first model just walls then set
up some lightning and then they model the rest of the scene also with adding some textures
— but what I like to do is first finish modeling the whole scene and then work with
lighting, in this way when I set up my lighting I will do it only once and won't have to
constantly change it, because after adding some more objects to the scene the composition
and the mood have changed."*

    reference  ->  camera  ->  BLOCK OUT EVERYTHING  ->  mood  ->  material split  ->  texture  ->  post

This studio reached the same order independently and wrote it down as
`build-order-dimension-objects-light`. Two sources agreeing is worth more than either.

**The corollary nobody states:** the mood stage is done on ONE grey override material, and
its whole purpose is that colour, exposure and shadow contrast get settled while there is
nothing else to blame. Every later stage inherits that decision.

## 2. THE MOOD STAGE HAS EXACTLY FOUR MOVES, AND HE MAKES THEM IN THIS ORDER

1. **An OVERCAST HDRI even for a sunny room** (10:15). *"even though we are creating an
   sunny interior we first need to create overcast lighting"* — the sky supplies the cold
   reflections; the sun is added afterwards as a separate, controllable thing.
2. **Darken the override shader** (11:00). *"if you would put for example piece of paper
   somewhere in that kitchen it would be brighter than everything else, that's why we need
   to make that shader darker."* A default grey is a white-paper room.
3. **Raise exposure, but not all the way** (11:45). *"we are not going to go extreme with it
   because we still need to leave some space for the sun."*
4. **Take the reference's AVERAGE COLOUR from a Photoshop Average Blur** (12:15) and put it
   in the shader. Ours reproduces his hex byte for byte: `#A39583`.

**And one thing he does that is worth stealing outright:** the shadow-contrast check at
14:31. Desaturate both images, eyedropper a lit patch and a shadow patch **on the same
material**, compare the two differences. On his reference marble he gets 170/80, 250/150,
210/110 — about 100 every time — and on his render 150/50, 210/100.

## 3. THE THREE TRAPS THAT INSTRUMENT HIDES, WHICH WE FOUND BY BUILDING IT

We built his eyedropper as `shadow_delta.py`. It was wrong three times, and each way is
general.

* **A PEAK IS NOT A LOBE.** The first version took the two tallest histogram peaks. The
  shadow side of a floor patch has two humps, so it returned 104 and 122 and reported a
  difference of 18 where the answer is 76. Otsu plus the MEDIAN of each side fixes it.
* **THE DIFFERENCE IS NOT EXPOSURE-INVARIANT, AND THE DOCSTRING SAID IT WAS.** We wrote
  *"exposure cannot fake it: raising exposure raises both samples together."* Measured on
  our own frames, same lights, only the exposure knob moving:
  `-2.0 → 244/117 = 128 FAIL` · `-1.0 → 253/154 = 99 PASS` · `0.0 → 255/185 = 70 PASS`.
  The knob walks the rung from fail to pass. **Why:** raising exposure lifts both lobes only
  while both CAN move; once the lit lobe is against the top of the range it stops, the
  shadow lobe keeps climbing, and the difference collapses. The tutorial never meets this
  because he eyedroppers marble mid-tones by hand and would never sample a blown highlight.
  **The fix is to make his discipline a refusal:** refuse the patch when either lobe is
  within 7 levels of the end of the range, or more than 2% of it is pinned there.
* **TWO FRAMES MUST SIT AT THE SAME PLACE ON THE TONE CURVE.** AgX is steep in the
  mid-tones and flat near white, so a frame reading 232 and one reading 176 cannot have
  their differences compared. Match the LIT level with exposure first, then compare the
  shadow. This also removes the knob: exposure is now spent on the match and is no longer
  free to move the answer.

## 4. THE FINDING THIS REPRODUCTION PAID FOR: **THE CURTAIN IS THE FILL LIGHT**

At 13:08 he disables the curtain during the mood stage. Following that literally, nothing
we could do reached the reference's shadow contrast:

| what we swept | range | floor lit−shadow (target 76) |
|---|---|---|
| sun irradiance, sheer hidden | 120 → 900 W/m² (7.5×) | 152 → 128 |
| sky/HDRI strength, sheer hidden | 0.5 → 5.0 (10×) | 152 → 145 |
| removing the tree canopy | on → off | 150 → 134 |
| **putting the sheer back with its own shader** | — | **90 · PASS** |

**Why the sky lever did almost nothing:** in this room the shadow is lit by SUN BOUNCE, not
by sky, so turning the sun down turns the fill down with it and the ratio barely moves. A
10× change in sky strength moved the shadow lobe from 64 to 72.

**Transferable rule:** in a room whose glazing carries a sheer, the sheer is not decoration
— it is the largest area light in the scene, and the mood cannot be settled without it. Hide
the curtain to READ the mood if you like; do not hide it to SET the mood.

## 5. THE TEXTURE STAGE HAS ONE ORDER RULE AND IT IS THE WHOLE LESSON

**REFLECTIONS BEFORE COLOUR** (23:30). *"the reason why we are starting with reflections is
because if we plug in the color first then we won't be able to see very well how much
reflections we got."* Two knobs, and he tells you which he prefers: roughness changes how
SHARP the reflection is, IOR changes how MUCH of it there is, *"I think the IOR works
better for me more often than roughness."*

His chain, worth copying node for node:

* roughness: texture → ColorRamp to black-and-white → **flip to invert** → RGB Curves darker
  and more contrast. (Driving IOR instead: identical, minus the invert — 25:00.)
* colour LAST, and **mixed with the flat colour from the split stage** so the map supplies
  the pattern and the split supplies the hue and brightness.
* marble adds subsurface: weight 1, radius ≈ (1, 0.7, 0.5), scale ~3 cm, with the colour
  texture through a ColorRamp as the **weight**, so the pale stone transmits and the dark
  veins do not (26:00).
* glass goes back on LAST with diffuse, glossy and shadow rays DISABLED (28:30) — *"to get
  the exact same lighting as I had"*. A pane that starts bouncing light re-lights the room
  you just settled.

## 6. A NUMBER OFF A PHOTOGRAPH IS ILLUMINANT × ALBEDO, AND HIS METHOD INVITES THE ERROR

Eyedroppering the reference and typing the result into a Base Color is the natural reading
of his split stage. It is wrong for every family except the average-blur override, because
a photograph's pixel is the light times the surface. The plate's ceiling reads 208,189,163
— strongly warm — because the light is warm. The ceiling is white.

Feed those triples in as albedo and the render applies the warm light to an already-warm
surface; ours went pink across the whole frame. **The fix is to SOLVE, not to judge:** render,
measure the same surface in both images, divide.

**And the trap inside the fix**, which cost us a round: a per-channel albedo divide will
absorb ANY difference, including one that is not the albedo's fault. It proposed a floor
albedo of `#ABBCF0` and a marble of `#98A7B5` — a blue kitchen — because our LIGHT was
warmer than the plate's and the solve was quietly paying for it out of the surfaces.
**Split the ratio: the geometric mean is a LEVEL and belongs to the albedo; what remains is
CHROMA and belongs to the light.** Ours then reported the actual defect as a number — *"our
light is 1.258/1.005/0.845 times the plate's, 49% warm on R/B, fix it at the sun"* — which
is something a person can act on. Two iterations took it to 25%.

## 7. WHAT THE TUTORIAL DOES IN POST THAT CHANGES WHAT ITS RESULT MEANS

The post stage (28:45–34:20) is: save the noisy frame; denoise in the compositor and save
that too; paint the denoised back over the noisy by hand, *"and in some cases like the
curtain here I will only use 50% opacity of the brush because the denoised image killed too
much detail of the curtain"*; then **downscale by half and run four Magnific AI passes at
rising "creativity" (0, 2, 4, 6) and paint in the parts you like**; then a high-pass on a
smart object in soft light at ~20%; then check before-and-after and pull the opacity back if
you overdid it.

**The Magnific step means the tutorial's final image is substantially generated.** At
creativity 4 and 6 the model is writing wood grain, fabric weave and stone veining that no
part of the 3D scene produced. Anyone benchmarking a hand-built render against that result
is comparing against a hybrid, and should know it. We did not run it — a spend is the
owner's call, and a lane whose purpose is learning to MAKE detail should not ship detail it
hallucinated.

**What replaced the brush, and it is better rather than merely different:** the blend
between the noisy and denoised frames is driven by a statistic. Take `d = noisy − denoised`.
Where the denoiser removed REAL DETAIL, `d` is locally COHERENT — a plank joint pushes a
whole neighbourhood the same way — so `|mean(d)|` is comparable to `sd(d)`. Where `d` is
Monte Carlo noise it is zero-mean and incoherent and the ratio collapses. **Coherence, not
magnitude.** Our first attempt weighted by magnitude and produced an output grainier than
either input, because magnitude cannot tell noise from detail — both are large. That is
exactly the judgement his brush is making, said as a number, per pixel.

## 8. WHERE HE IS SOLVING AND WHERE HE IS DIALLING — INTERROGATING THE REFERENCE

The charter requires naming where the reference made a CHOICE rather than a measurement.

* **fSpy camera: a solve.** Two vanishing lines per axis, one known dimension. Sound, and he
  is careful to use edges far from the image centre and on opposite corners.
* **Camera height: a dial, and he says so** — *"it feels way too big and that's because the
  camera is placed too low… it was taken somewhere around human eye level so we will set its
  height to 1.5 m."* A round number chosen because a box felt wrong.
* **Sun rotation: a dial** — *"adjust its rotation to have the shadows in similar way as in
  our reference."* A direction is not something an amount can confirm.
* **BLOCKING THE WINDOW: a deliberate, defensible cheat, and the best line in the video**
  (14:00): *"remember that the fact that the window is there doesn't necessarily mean that
  the light should be coming from there — photographers in some cases also block the light
  from the windows to get a better photo."* He also boxes out a foreground shadow he does
  not like. This is not an error; it is the thing an archviz artist is actually paid for,
  and it is the part a measurement-driven pipeline will never propose on its own.
* **Trees exist to CAST, not to be seen** (13:15). He copies a tree in purely for the leaf
  shadows and names the collection for it. Our own version of this failed the first time
  because the canopy sat outside the sun's path — geometry that exists to cast a shadow must
  be IN the path, and the path is set by the sun angle, not by where a tree would look right.
* **"Take a five minute break"** (22:00). *"our eyes are getting used to what they see
  pretty quickly and we can miss some mistakes."* The cheapest quality rung in the video,
  and the studio equivalent is the independent critic.

## 9. WHAT COULD NOT BE MEASURED FROM ONE PHOTOGRAPH, SAID AS REFUSALS

* **The island's plan WIDTH.** The camera is at 1421 mm and the slab at 827–899 mm, so a ray
  through the slab plane is grazing: changing the assumed height by the slab's own thickness
  (72 mm) moves the unprojected X by **512 mm**. A depth read through a nearly parallel plane
  is not a measurement. Two spans of the traced edge also returned +2.87° and +25.35°, which
  is the chord refusal again. **The route that would settle it is a second camera station** —
  the same house's wide shot shows the island where its width is across the view instead of
  along it.
* **The floor's plank WIDTH.** No autocorrelation maximum anywhere in 80–400 mm on three
  world-space profiles; the only repeating feature sat at the cut-off of the detrend window,
  i.e. it was the filter's own shape. **Its positive control passed in the same image:** the
  sun bands, which certainly exist, gave a real maximum at 2194 mm against an asserted
  mullion pitch of 2150 (2.0%). The instrument finds periodicity when periodicity is there.
* **The red leather and the black tap.** Patch standard deviations of 25–45 and 78–83 per
  channel. A mean over a dirty box is not a reading, and both are recorded as unmeasured
  rather than reported anyway.

## 10. WHAT TO CONFIRM OR KILL THIS WITH

* §4 (the sheer is the fill) is **n = 1 room**. Kill it by finding a sheered room where
  hiding the curtain still reaches the reference's contrast; confirm it by reproducing the
  sweep in a second one.
* §3's clip guard has a threshold (248 / 2%) chosen from one frame's failure. Confirm it by
  running the exposure sweep on a second scene and checking the guard fires at the same
  place the eye says the highlight went.
* §6's CHROMA_OWN = 0.10 is asserted, not derived. What would settle it: the spread of
  chroma across families on a scene whose light IS correct.
* §7's coherence blend has one parameter (`coherence_full = 0.9`). It has not been tested
  against a render with a known ground truth — a very high sample-count frame of the same
  scene would give one.
