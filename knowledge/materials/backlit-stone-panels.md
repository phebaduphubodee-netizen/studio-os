# หินธรรมชาติส่องไฟจากด้านหลัง / Backlit natural stone — reading as STONE, not as a lightbox

> PROVENANCE: promoted 2026-08-02 from
> `knowledge/_inbox/nlm-backlit-stone/2026-07-31-backlit-stone.md`
> (NotebookLM, notebook `79476082-dfe5-4842-8daf-d78c9249f939`, 290 sources,
> conversation `b738f058-74fc-4182-bfd0-825701eff7ea` turn 1).
> **Tier REFERENCE — a research answer, not domain truth and not statute.**
> No number here may gate a deliverable on its own.

**Why this file exists.** `bsdf-material-presets.md` carries marble ROUGHNESS bands
(honed 0.4–0.7, polished 0.0–0.15) and one passing note that SSS may be used
"sparingly for high-end realism". Neither says anything about stone lit **from
behind**, and a backlit slab is a different material problem, not a brighter version
of the same one. This closes that gap at REFERENCE tier.

## ลำดับอำนาจ / Authority + precedence

1. A MEASUREMENT of the artefact being reproduced outranks this file.
2. `knowledge/materials/pbr-material-behavior.md` §2 channel bounds still bind —
   in particular the "avoid absolute 0.0 / 1.0 roughness" rule.
3. `bsdf-material-presets.md` for the front-lit marble starting values. This file
   does not replace them; it adds the transmission behaviour they never described.
4. This file.

## 1. The mechanism, and why more light never fixes it

**An opaque Principled BSDF with a lamp behind it cannot read as backlit stone at
any power.** Transmission is the mechanism; without it the panel is a lit surface,
not a lit *volume*, and every remaining knob is tuning the wrong thing. This is the
same shape as a feature disabled for want of a collision term that was one line: the
fix is a material property never switched on, not more of the light already there.

## 2. Luminance variation — the falloff IS the depth cue

With the LED concealed around the perimeter, luminance should be **highest at the
edges and decay smoothly toward the centre**: the farther light travels through a
translucent medium, the more of it is absorbed and scattered. Emissive intensity
must be modulated to reproduce that falloff. **Uniform brightness across the panel
is the single loudest lightbox tell** — it removes depth and reads as an
unnaturally glowing plane.

## 3. Subsurface scattering — essential, and thickness-coupled

SSS is not an enhancement here; without it marble and jade render flat, sterile or
simply opaque. Light must penetrate, scatter internally and exit elsewhere, and the
strength of that scattering **depends on the object's thickness**. Calibrate it
strongly enough that perimeter light bleeds into the slab, but constrained by the
stone's internal density so it does not transmit like thin plastic or glass. A slab
that glows evenly like acrylic has SSS that is too free, not too weak.

## 4. Vein structure — what the backlight is actually revealing

A uniform procedural pattern reads as artificial. Real stone carries structural
irregularity, and under backlight the veins are doing optical work:

- veins vary **wildly in width and direction** — never a regular noise field;
- value contrast shifts organically, because **denser mineral deposits block more
  backlight and appear DARKER, while thinner or quartz-like veins pass more light
  and appear BRIGHTER**;
- micro-variation must break up uniformity, or tiling artifacts betray the origin.

Note this is a claim about the ALBEDO/transmission map's correlation with
thickness, not about a noise setting. Veins that are merely dark in reflected light
and neutral in transmission are the frosted-acrylic failure again.

## 5. Specular behaviour — microfacet + Fresnel

- **Fresnel:** lowest reflectivity viewed straight on (0°), rising to nearly
  mirror-like at **grazing** angles near 90°.
- **Focused highlights:** polished stone has near-parallel microfacets, so speculars
  stay tight and bright. Per **microfacet** theory this is a roughness consequence,
  not a highlight-size setting.
- **Real-world imperfection:** sharp highlights on an otherwise perfect surface read
  as extruded acrylic. Fine scratches, subtle grain, dust and handling marks in the
  roughness/bump channel break the digital symmetry of the gloss.

## 6. What to measure first — this file is UNTESTED against any frame

The source is a research answer and none of it has been verified against a
reproduction target. Test in this order, each independently falsifiable:

1. perimeter-to-centre luminance falloff (a profile, not a look);
2. SSS strength scaled to the slab's modelled thickness;
3. vein width / direction / value variation, and the density↔darkness correlation;
4. Fresnel response at grazing angle.

## 7. ช่องว่าง / Gaps — do not fill from model knowledge

- **No numeric values whatsoever.** The source gives mechanisms and directions of
  effect, no SSS radii, no falloff exponents, no thickness figures. Anything
  numeric must come from a measurement, not from here.
- No Thai-market stone data: no local marble/onyx species, no slab thicknesses, no
  supplier information.
- Nothing on the LED side — no CCT, no CRI, no linear-metre output, no driver or
  dimming behaviour. Lighting values live in `knowledge/lighting/`.
- No guidance on the front-lit case; for that, `bsdf-material-presets.md` still owns
  the roughness bands.
