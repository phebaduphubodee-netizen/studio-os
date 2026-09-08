# NLM — backlit natural stone: reading as stone, not as a lightbox

**Tier: REFERENCE** (research answer, not domain truth, not statute — distil into
`knowledge/` before any value here gates a deliverable.)

- **Notebook:** `79476082-dfe5-4842-8daf-d78c9249f939` — INTERIOR-AI design
  lighting rendering 2026-06 (290 sources)
- **Conversation:** `b738f058-74fc-4182-bfd0-825701eff7ea` · **turn** 1 · **asked** 2026-07-31
- **Trigger (CLAUDE.md §External research lane):** a defect class reaching its
  2nd build round. A backlit stone panel was the top-ranked item of two
  INDEPENDENT cold critics in consecutive rounds ("veins too fine and uniform,
  no sweeping figure", then "reads as a frosted acrylic lightbox, not stone").
- **Vault checked first, and the gap is real:** `knowledge/materials/bsdf-material-presets.md`
  and the 2026-07-01 photoreal DR both carry marble ROUGHNESS bands (honed
  0.4–0.7, polished 0.0–0.15) and one passing mention that SSS may be used
  "sparingly for high-end realism" — nothing on stone lit FROM BEHIND.
- **Privacy:** generic technique question; no client, project, dimension or plan
  detail left this machine.

## Why this matters to a live build

Our slab is an opaque Principled BSDF with the concealed LED behind it. Per the
answer below, that construction cannot read as backlit stone at any power —
transmission is the mechanism and we have none of it. Same shape as the
2026-07-22 lesson (a feature disabled for want of a collision term that was one
line): the fix is a material property never switched on, not more tuning of the
light already there.

## Answer (citation markers resolved to source titles at staging time)

To successfully render a photorealistic backlit natural stone panel rather than a frosted acrylic lightbox, you must accurately simulate the physical properties of the stone, its interaction with light, and its surface imperfections.

**Luminance Variation**
Because the LED light source is concealed around the perimeter, the luminance should be highest at the edges and smoothly decay toward the center of the slab. In physics, the farther light travels through a translucent material, the more its energy is absorbed and scattered (What is PBR (physically based rendering)?). To replicate this, emissive intensity should be modulated to simulate natural light falloff (Accurate Emissive PBR Textures for Realistic Light E…). If the luminance is uniformly bright across the entire panel, the material will lack depth and appear unnaturally flat or excessively glowing, breaking immersion (Accurate Emissive PBR Textures for Realistic Light E…). 

**Translucency and Subsurface Scattering**
**Subsurface scattering (SSS)** is absolutely essential; without it, materials like marble and jade will appear flat, sterile, or completely opaque (Technical Manual of Interior Design Project Delivery). SSS simulates the behavior of light penetrating the surface, scattering randomly inside the material, and exiting at a different point [7-10]. The strength of the scattering and absorption is heavily dependent on the object's thickness (What is PBR (physically based rendering)?). Therefore, SSS should be calibrated strongly enough to allow the perimeter light to bleed into the stone, but constrained by the varying physical density of the stone's internal structure so that it does not transmit light as easily as thin plastic or glass.

**Vein Structure**
While procedural textures rely on mathematical noise functions and gradient ramps (Accurate Emissive PBR Textures for Realistic Light E…), using a uniform procedural pattern will make the stone look artificial. Real stone possesses complex spatial emission properties and structural irregularities (Accurate Emissive PBR Textures for Realistic Light E…). To look natural, the vein structure must incorporate **micro-variations to break up uniformity** and prevent repetitive tiling artifacts that betray a digital origin (Accurate Emissive PBR Textures for Realistic Light E…). The veins should vary wildly in width and direction, and the value contrast should shift organically—with thicker, denser mineral deposits blocking more of the backlight (appearing darker) and thinner or quartz-like veins allowing more light through (appearing brighter). 

**Specular and Gloss Behavior**
For the surface to read as polished stone, it must accurately follow **microfacet theory** and the **Fresnel Effect** (Technical Manual of Interior Design Project Delivery). 
*   **Fresnel Reflections:** The stone should exhibit its lowest baseline reflectivity when viewed straight-on (at a $0^{\circ}$ perpendicular angle) and become highly reflective, almost mirror-like, at grazing angles near $90^{\circ}$ (What is PBR (physically based rendering)?; Technical Manual of Interior Design Project Delivery).
*   **Focused Highlights:** Because polished stone is generally smooth, its microfacets are parallel, which keeps specular reflections focused and creates bright, sharp highlights [7-10]. 
*   **Real-World Imperfections:** To prevent the sharp highlights from making the stone look like perfectly extruded acrylic, you must apply high-quality roughness, bump, or normal maps to introduce subtle, real-world flaws [17-20]. Incorporating micro-details like fine surface scratches, subtle grain, dust layers, and fingerprints breaks up the digital symmetry of the gloss and ensures the material feels authentic and "lived-in" (Photorealistic Architectural Rendering)

## Sources cited in this turn

- Accurate Emissive PBR Textures for Realistic Light Effects - aiTextured
- Photorealistic Architectural Rendering: Guide & Tips - Fox Render Farm
- Photorealistic Architectural Rendering: Guide & Tips : r/archviz - Reddit
- Photorealistic Architectural Renderings: Techniques & Tips - Xrender Studio
- Photorealistic Interior Rendering for Real Estate | PIXREADY
- Technical Manual of Interior Design Project Delivery: Comprehensive Process, ADA Clearances, Millwork Fabrication, Lighting Physics, and Photorealistic Visualization
- What is PBR (physically based rendering)? - Adobe Substance 3D

## Not yet actioned

Distillation into `knowledge/materials/` is deliberately NOT done here — the
answer is untested against our own frame. The measurable claims to test first:
(1) perimeter-to-centre luminance falloff, (2) SSS strength scaled to slab
thickness, (3) vein width/direction/value variation, (4) Fresnel grazing-angle
response. They belong to the TRN-001 round-5 material lane.
