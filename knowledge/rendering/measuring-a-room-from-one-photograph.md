# Measuring a room's LIGHT and MATERIALS from one photograph

Promoted from `knowledge/_inbox/trn003-3dshaker-study/what-a-tutorial-workflow-actually-assumes.md`
(TRN-003, 2026-08-29). Source evidence: the 3D Shaker tutorial `dHS4u9YaIDw` plus this
studio's own reproduction of the same plate, measured end to end. **n = 1 room.** Every
number below was measured on that plate or on our renders of it; where something could not
be measured it says so.

Sibling: `knowledge/rendering/practitioner-consensus-eye-light-camera.md` (what practitioners
say), `knowledge/lighting/lumen-method-and-fixture-placement.md` (fixtures from geometry).
This file is the other direction — pulling the light back OUT of a photograph.

---

## 1. THE SUN IS A VECTOR, AND ONE PHOTOGRAPH GIVES YOU BOTH ANGLES

**Do not fit shadow-BAND edges.** Fitting the edges of sunlight bands on a floor gives a
plan direction **modulo 180°** and nothing else, and it is easy to fit the wrong pixels. On
this plate four such "parallel" edges disagreed by **7.75°** at rms 6.3–10.6 px, were
averaged into a single number, and produced an azimuth that put no beam anywhere in frame.

**Use a GNOMON.** Any vertical object whose floor contact is visible in sunlight settles the
whole vector:

* **Azimuth.** Unproject the base to the floor plane, then search a **single parameter — the
  WORLD plan angle — for the darkest ray leaving that base.** The search parameter is a world
  angle, so no image slope is ever read, which is what keeps it out of the chord trap. Four
  bar-stool legs here returned 92.53 / 92.46 / 91.98 / 92.00, spread **0.55°**.
* **Elevation.** Any member of known height whose shadow feature can be located gives
  `h/tan(e)`. Four routes returned 17.60 / 17.96 / 18.20 / 17.55, spread **0.65°**.
* **What the photograph ACTUALLY measures is `h/tan(e)`**, not the angle. Here it is
  585 ± 4 mm, robustly, from a joint fit of eight rail shadows. Splitting it into a height
  and an angle is only as good as the member height you assume: 175 mm → 16.75°, 185 → 17.50,
  193 → 18.25, 200 → 19.00. **Record the invariant, not just the angle** — then a better
  height later costs no re-measurement.

**Break the 180° ambiguity with pixels, never with a sentence.** Sample luminance along BOTH
opposite rays from one base. Along the true one the floor is **continuously dark from the
base outward**; along the false one it is dark only in short intervals — and on this plate
those intervals sat exactly on the other three legs' independently measured bases, with
bright floor beyond the last. **A cast shadow is continuous and attached to its caster; a row
of objects is not.**

**Positive control for any unprojection onto a floor:** find a world line whose heading is
known by construction (a cabinet toe/floor junction along a room axis is 90.000° by
definition). Here it unprojected to 90.214° at rms 0.11 px. **rms is what tells you which fit
to believe** — the same fitter on dirtier stretches of the same physical line gave rms
1.6–1.7 px and headings 86.6–86.8°.

**The cheapest disproof of a wrong sun costs no measurement at all: ask where the ray
ENTERS.** A plan azimuth plus one lit point fixes where the ray must cross the glazing plane.
At the refuted 21.58° that crossing was **x = −8615 mm** — 8.4 m outside the glass, for every
elevation, because it is a plan-direction argument. Any azimuth that cannot get its own light
into the room is refuted before a frame is rendered.

**Rejections are part of the method.** A tapered or leaning leg is not a gnomon (base and tip
are not on one vertical). An object standing inside another object's shadow has no shadow to
trace. An object whose outline depends on an ASSERTED dimension calibrates against your own
assumption.

## 2. IN A ROOM WITH A SHEER, THE SHEER IS THE FILL LIGHT

Measured on this plate, chasing the reference's lit-minus-shadow ratio on the floor
(target 76):

| lever | range swept | result |
|---|---|---|
| sun irradiance, sheer hidden | 120 → 900 W/m² (7.5×) | 152 → 128 |
| sky / HDRI strength, sheer hidden | 0.5 → 5.0 (10×) | 152 → 145 |
| removing the tree canopy | on → off | 150 → 134 |
| **sheer back in, with its own shader** | — | **90** |
| sheer in AND the sun measured rather than dialled | az 90/el 26 → 92.3/18.3 | **88** |

**Why the sky lever did almost nothing:** in a room like this the shadow is lit by SUN
BOUNCE, not by sky — so turning the sun down turns the fill down with it and the ratio
barely moves. A 10× change in sky strength moved the shadow lobe from 64 to 72.

**Rule:** a sheer across the glazing is the largest area light in the scene. Hide the curtain
to READ the mood; never hide it to SET the mood. Note also that a material OVERRIDE turns the
sheer opaque and blacks the room, exactly as it does to glass — which is a mechanical reason
a mood stage may appear to say the curtain does not matter.

## 3. A COLOUR SAMPLED FROM A PHOTOGRAPH IS ILLUMINANT × ALBEDO

Eyedroppering a reference and typing the result into a Base Color is wrong for every surface
except a whole-frame average used as a mood override. A photograph's pixel is the light times
the surface: a white ceiling under a warm low sun reads 208,189,163, and feeding that in as
albedo applies the warm light twice.

**Solve it instead:** render, measure the same surface in both images, divide.

**And split the ratio, or the solve will hide a wrong light inside your materials.** A
per-channel albedo divide absorbs ANY difference. Here it proposed a floor albedo of
`#ABBCF0` and a marble of `#98A7B5` — a blue kitchen that renders correctly under one light
and is wrong the moment the light moves.

* the **geometric mean** of the ratio is a LEVEL and belongs to the albedo — apply it;
* what remains is **CHROMA** and belongs to the LIGHT — report it, do not absorb it.

Reported that way the defect becomes actionable: *our light is 1.258 / 1.005 / 0.845 times
the reference's, 49% warm on R/B — fix it at the sun.* Two iterations took it to 25%.

**A ratio at the clamp means the model is wrong, not that the albedo is far out.** A 4×
difference on a diffuse surface is not an albedo error; look for specular, for the wrong
face, or for a patch straddling two objects. On this plate it fired on a black oven: 14,14,14
in the reference against 186,159,129 in ours, because our oven was a flat glossy plane aimed
at a large window and was mirroring it.

**Read the AMBIENT, not the mean.** Two frames rarely put their beams in the same places, so
a mean over a patch compares your sunlit fraction against theirs. Take the dark lobe. And use
**the same lobe in both images or neither** — comparing one image's shadow lobe against the
other's whole patch returned a spurious 4× here.

**Derive the patch, never type it.** Every sampling box should be a world rectangle on a named
face of a named mass, projected through the solved camera, so it cannot drift off its subject
without the object moving.

## 4. TEXTURE ORDER: REFLECTIONS BEFORE COLOUR

From the tutorial, and it is the single most portable thing in it: *"the reason why we are
starting with reflections is because if we plug in the color first then we won't be able to
see very well how much reflections we got."*

Two knobs and they are not the same knob: **roughness changes how SHARP the reflection is;
IOR changes how MUCH of it there is.** Practitioner preference in this source is IOR.

Chain worth copying: roughness map → ColorRamp to black-and-white → **invert** → RGB curves
darker and more contrast. Driving IOR instead: identical, minus the invert. Colour LAST, and
**mixed with the flat colour from the material split** so the map supplies the pattern and the
measurement supplies the hue and brightness. Stone adds subsurface — weight 1, radius about
(1, 0.7, 0.5), scale ~3 cm — with the colour texture through a ColorRamp as the **weight**, so
pale stone transmits and dark veins do not.

Glass goes back on LAST with **diffuse, glossy and shadow rays disabled**, so putting it back
does not re-light the room you just settled.

**Do not spend a map on a surface the picture cannot show.** The ceiling here measured a patch
standard deviation of 1.8 / 1.1 / 1.4 grey levels over 11,200 px — the flattest surface in the
frame by an order of magnitude. A plaster map on it rendered visible blotches the reference
does not have. A flat colour was the measurement's answer.

## 5. WHAT ONE PHOTOGRAPH COULD NOT MEASURE, AND WHY

* **A plan dimension read through a nearly parallel plane.** The camera sat at 1421 mm and the
  island slab at 827–899 mm, so a ray through the slab plane grazes it: changing the assumed
  height by the slab's own thickness (72 mm) moved the unprojected X by **512 mm**. Refused.
  The route that settles it is a SECOND CAMERA STATION where the dimension runs across the
  view instead of along it.
* **The floor's plank width.** No autocorrelation maximum anywhere in 80–400 mm on three
  world-space profiles; the only repeating feature sat at the cut-off of the detrend window,
  i.e. it was the filter's own shape. **Its positive control passed in the same image** — the
  sun bands, which certainly exist, gave a real maximum at 2194 mm against an asserted mullion
  pitch of 2150 (2.0% apart). The instrument finds periodicity when periodicity is there.
* **Small, specular or half-occluded objects.** A red leather chair 16–20 px wide gave patch
  standard deviations of 25–45 per channel and hues moving from 355° to 16° between two
  patches. A mean over a dirty box is not a reading.

## 6. WHAT POST-PRODUCTION IN THIS SOURCE ACTUALLY IS

The published workflow's post stage runs a **generative AI upscaler over the finished frame,
four passes at rising "creativity", painting in the parts the artist likes.** At the higher
settings the model is writing wood grain, fabric weave and stone veining that no part of the
3D scene produced.

**Anyone benchmarking a hand-built render against a result made this way is comparing against
a hybrid.** That is a fact about the target, not a criticism of it, and it belongs in any
comparison this studio makes.

The defensible part of that stage ports cleanly. Render the frame twice, denoised and not,
and blend them by a statistic rather than a brush: take `d = noisy − denoised`; where the
denoiser removed real detail `d` is locally **COHERENT**, so `|mean(d)|` is comparable to
`sd(d)`; where `d` is Monte Carlo noise it is zero-mean and incoherent and the ratio
collapses. **Coherence, not magnitude** — weighting by magnitude produces an output grainier
than either input, because magnitude cannot tell noise from detail: both are large.
