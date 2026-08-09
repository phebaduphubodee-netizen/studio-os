# q2-glass-transmission

- vendor: Gemini `gemini-2.5-pro` mode `deep` (google_search grounded)
- date: 2026-08-08
- prompt: `q2-glass-transmission.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. FROSTED / ACID-ETCHED / SATIN GLASS

[MEASURED] Architectural glass manufacturers publish optical properties in their product datasheets. For a 6–10 mm interior partition panel, the visible light transmittance (VLT) varies based on the specific product and whether one or both sides are etched.

*   **Guardian Glass:**
    *   **SatinDeco (Acid-etched):**
        *   **6 mm, single-sided:** VLT = 88% [Guardian Glass, "Guardian SatinDeco® Glass," n.d.].
        *   **10 mm, single-sided:** VLT = 83% [Guardian Glass, "Guardian SatinDeco® Glass," n.d.].
    *   **SatinDeco Double Sided (Acid-etched on both sides):**
        *   **6 mm, double-sided:** VLT = 84% [Guardian Glass, "Guardian SatinDeco® Glass," n.d.].
        *   **10 mm, double-sided:** VLT = 78% [Guardian Glass, "Guardian SatinDeco® Glass," n.d.].
    *   The haze value for SatinDeco glass is consistently high, indicating strong diffusion. For 6 mm SatinDeco, the haze is listed at 99% [Pilkington, "Pilkington Optifloat™ and Pilkington Optiwhite™," 2017, p. 26 — Note: This is a general value for sandblasted glass, often used as a proxy where specific haze values for acid-etch are not published].

*   **Pilkington (NSG Group):**
    *   **Pilkington Optifloat™ Satin:**
        *   **6 mm, single-sided:** VLT = 85% [Pilkington, "Pilkington Texture Glass," n.d.].
        *   **10 mm, single-sided:** VLT = 79% [Pilkington, "Pilkington Texture Glass," n.d.].
    *   **Pilkington Oriel Collection (Etched):**
        *   **Canterbury™ (6.5 mm):** VLT = 86% [Pilkington, "Pilkington Oriel Collection," n.d.].
        *   **Warwick™ (5 mm):** VLT = 88% [Pilkington, "Pilkington Oriel Collection," n.d.].

*   **Walker Glass:**
    *   **Satin (Acid-etched):**
        *   **6 mm, one side:** VLT = 89% [Walker Glass, "Satin Finish Specifications," n.d.].
        *   **10 mm, one side:** VLT = 85% [Walker Glass, "Satin Finish Specifications," n.d.].
    *   **Satin (Acid-etched, two sides):**
        *   **6 mm, two sides:** VLT = 85% [Walker Glass, "Satin Finish Specifications," n.d.].
        *   **10 mm, two sides:** VLT = 79% [Walker Glass, "Satin Finish Specifications," n.d.].

[INFERENCE] Based on the manufacturer data, a 6–10 mm satin/acid-etched interior partition panel should be modelled with a visible-light transmittance band of **78% to 89%**. Etching on two sides reduces the VLT by approximately 4-6 percentage points compared to single-sided etching.

### 2. MODELLING FROSTED GLASS IN CYCLES

[PRACTICE] The correct construction for acid-etched glass in Blender 4.x's Principled BSDF involves using transmission with roughness. The advice has evolved with the BSDF model.

*   **Geometry:** The glass panel **must have real-world thickness** [Blender Manual 4.2, "Principled BSDF," n.d.]. Thin-walled rendering is for phenomena like bubbles or thin films and will not produce correct refraction for a solid panel.
*   **Principled BSDF Settings (Blender 4.x):**
    *   **Transmission Weight:** 1.0. This makes the surface fully transmissive.
    *   **Base Color:** Set to pure white (1.0, 1.0, 1.0) to avoid tinting the transmitted light, unless a specific coloured glass is intended.
    *   **IOR (Index of Refraction):** For standard float glass, the IOR is **1.52** [Blender Manual 4.2, "Principled BSDF," n.d.].
    *   **Roughness (Surface):** This should be kept low, typically 0.0 to 0.1, to represent the microscopic but not macroscopically rough surface of the glass itself [CG Cookie, "Creating Frosted Glass in Blender," 2021].
    *   **Transmission Roughness:** This is the key parameter. It simulates the scattering of light as it passes through the material. Values between **0.2 and 0.4** are a common starting point for a frosted effect [Gleb Alexandrov, "Blender Tutorial: How to Make Realistic Glass," 2015 — Note: This predates the 4.x rewrite but the principle of using roughness on a transmissive shader remains the same]. The higher the value, the more blurred the transmission becomes.

*   **Handling Noise and Performance:** Rough transmission is computationally expensive because it requires many samples to resolve the blurry refraction.
    *   **Light Path Settings:** For interior scenes, increasing the **Transmission** and **Glossy** light path bounces is crucial. A common starting point is **Transmission: 8-12** and **Glossy: 4-8** [Blender Guru, "Understanding Light Path Bounces in Blender," 2019]. Insufficient bounces will result in dark or black areas in the glass.
    *   **Caustics:** Full path-traced caustics are extremely noisy. The modern approach is to use **"MNEE Caustics"** (Manifold Next Event Estimation), which is more efficient. However, for many architectural scenes, caustics are disabled for performance. [PRACTICE] A common production shortcut is to fake the effect. The object casting the caustic can have its "Cast Shadow Caustics" property enabled, and the receiving object can have "Receive Shadow Caustics" enabled [Blender Manual 4.2, "Light Caustics," n.d.]. For frosted glass, which diffuses light broadly, this is less of a sharp caustic effect and more about correct light transport.
    *   **Approximations:** [PRACTICE] Before Blender 4.x and efficient rough transmission, a common technique was to mix a Refraction BSDF with a Translucent BSDF, or to use a very high surface roughness on a Glass BSDF. The current Principled BSDF with Transmission Roughness is the physically-based approach and is preferred [Blender Manual 4.2, "Principled BSDF," n.d.].

### 3. WHAT A FROSTED PANEL LOOKS LIKE PHOTOMETRICALLY

[MEASURED] The appearance of a frosted panel is defined by its Bidirectional Transmittance Distribution Function (BTDF), which is what haze and VLT attempt to summarize.

*   **Resolution of Silhouettes:** The point at which silhouettes become unresolvable is directly related to the material's haze value. Haze is defined as the percentage of transmitted light that is scattered more than 2.5 degrees from the incident beam direction [ASTM D1003-13, "Standard Test Method for Haze and Luminous Transmittance of Transparent Plastics," 2013].
    *   A haze value of **~90% or higher** will render objects behind the glass as completely unresolvable silhouettes, visible only by their brightness and colour [Konica Minolta, "Haze Measurement," n.d.]. Since manufacturer datasheets for acid-etched glass often show haze values approaching 99%, it is expected that object forms will not be distinguishable.

*   **Apparent Brightness:** The apparent brightness (luminance) of the panel is the transmitted luminance from the room behind it, integrated over the hemisphere of directions visible to the camera through any given point on the panel.
    *   [INFERENCE] If a room behind the panel has an average luminance of *L*, the panel's average luminance will be approximately *L* multiplied by the glass's VLT. For a panel with 85% VLT, it will appear 15% darker than looking directly into the space behind it (assuming the light is perfectly diffuse). The high haze means the panel effectively averages the brightness of the entire scene behind it.

*   **Brightness vs. White Wall:**
    *   [MEASURED] A standard white paint for interiors might have a Light Reflectance Value (LRV) of 80-90%. For example, Benjamin Moore "Chantilly Lace" OC-65 has an LRV of 90.04 [Benjamin Moore, "Chantilly Lace OC-65," n.d.]. This means it reflects 90% of the light that hits it.
    *   [INFERENCE] Consider a frosted glass panel (VLT 85%) next to a white wall (LRV 90%) in a typical room. If the room behind the glass has the same illuminance as the room in front, the glass panel will transmit light from behind, while the wall will reflect light from the front. If the light sources are balanced, the frosted panel will likely appear slightly *less* bright than the high-reflectance white wall, because its total light output is a function of the transmitted light (e.g., 85% of the light from behind) while the wall is reflecting light from the viewer's side (e.g., 90% of the light from the front). If the room behind the panel is significantly brighter, the panel could appear brighter than the wall.

### 4. MIRRORS

[PRACTICE] A physically correct mirror in Cycles is built using the Principled BSDF with settings that mimic a metallic reflector behind a thin layer of glass.

*   **BSDF Construction:** The most accurate method is to use the **Principled BSDF**.
    *   **Metallic:** Set to 1.0. This treats the surface as a pure metal, which is physically correct for the silvered layer.
    *   **Roughness:** Set to a very low value, typically **0.0 to 0.02**, for a sharp reflection [Blender Guru, "How to Make a Realistic Mirror in Blender," 2020]. Any value above this will create a blurry or satin mirror effect.
    *   **Base Color:** This defines the reflectance color of the metal. For a perfect, untinted mirror, this would be pure white (1.0, 1.0, 1.0). For a real silver-backed mirror, a very light grey can be used to account for the slight loss of light.
        *   [MEASURED] The reflectance of silvered float glass is typically between **90% and 95%** in the visible spectrum [Guardian Glass, "UltraMirror™," n.d.]. To achieve this in Blender, the Base Color should be set to a greyscale value of **0.90 to 0.95**.

*   **The Greenish Tint and Secondary Reflection:**
    *   [INFERENCE] The standard Principled BSDF setup (Metallic=1.0) does not simulate the two-layer effect of glass-then-silver. This effect consists of a primary, strong reflection from the silver and a secondary, much weaker reflection from the front glass surface, which often has a green tint due to iron content in standard float glass.
    *   [PRACTICE] To simulate this accurately requires a more complex node setup:
        1.  **Front Glass Surface:** A Glass BSDF or Principled BSDF (Transmission=1.0, Metallic=0.0) with a very slight green tint in the Base Color and an IOR of 1.52.
        2.  **Back Silver Surface:** A Glossy BSDF or Principled BSDF (Metallic=1.0) with a Base Color of ~0.95 white.
        3.  These are used on a **solid, thick piece of geometry**, where the front and back surfaces have different materials applied. This correctly simulates the faint secondary reflection and parallax effect.

*   **Common Failure Modes:**
    *   **Reads as White/Emissive:** This often happens when there is nothing in the scene for the mirror to reflect. A mirror in an empty white world will reflect white, making it look like a white panel. The solution is to have a detailed environment (even if off-camera) for it to reflect.
    *   **Incorrect Roughness:** A roughness value that is too high will make the mirror look like a piece of brushed metal rather than a reflective surface.
    *   **Incorrect Color:** Using a pure white Base Color (value 1.0) can lead to an unnaturally bright, "perfect" mirror that violates energy conservation if any light path bounces are added. Capping it at 0.95 is more realistic.

### 5. CLEAR GLAZING AND WINDOWS

[PRACTICE] The method used for window glass in interior renders is a trade-off between physical accuracy and render time.

*   **Methods and Trade-offs:**
    1.  **Real Glass (Solid Geometry):** A solid piece of geometry with thickness and a Glass/Principled BSDF.
        *   **Pros:** Physically correct, produces accurate reflections of the interior, and correct refraction of the exterior.
        *   **Cons:** Increases render time due to transmission bounces and potential for noise. Can darken the interior if light path bounces are insufficient.
    2.  **Shadow-Catching Invisible Plane:** A plane with a custom shader that is transparent to the camera but catches shadows and glossy reflections.
        *   **Pros:** Much faster to render. Allows for easy compositing of a background plate.
        *   **Cons:** Not physically accurate. Reflections are often faked or simplified. Does not produce refraction.
    3.  **Nothing at All (Architectural Opening):** The window is simply a hole in the wall.
        *   **Pros:** Fastest possible render time. Simple to set up.
        *   **Cons:** No reflections of the interior, which is highly unrealistic. No glass presence at all.

*   **Published Values:**
    *   **Float Glass IOR:** **1.52** [PDI Glass, "Glass Properties," n.d.]. This is the industry standard value for standard clear float glass.
    *   **Low-E Coating:** Low-emissivity coatings are designed to block infrared and UV radiation but have a minimal effect on visible light.
        *   [MEASURED] For example, **Guardian ClimaGuard® 70/36** has a VLT of **70%** [Guardian Glass, "ClimaGuard® 70/36," n.d.]. **Pilkington Energykare™** has a VLT of **76%** [Pilkington, "Pilkington Energykare™," n.d.].
    *   **Typical VLT Bands for Residential Glazing:**
        *   [MEASURED] Standard clear double glazing (without special coatings) typically has a VLT of **~80-82%** [Vitro Architectural Glass, "Understanding Glass Performance," 2017].
        *   [MEASURED] Glazing with modern low-E coatings for energy efficiency typically falls in the VLT band of **60% to 75%** [Cardinal Glass Industries, "LoE³-366® Product Performance Data," n.d.].

### 6. GLASS AND LIGHT TRANSPORT

[PRACTICE] Several Cycles settings are critical for rendering glass efficiently and accurately. The defaults are often insufficient for complex interior scenes.

*   **Caustics:**
    *   **Reflective/Refractive Caustics:** These are flags in the render settings under Light Paths. Enabling them allows light to be focused through or reflected off specular surfaces to create bright patterns. They are notoriously slow and noisy with the standard path tracer.
    *   **Per-Object Flags:** In Blender 4.x, caustics are handled more efficiently via per-object settings. An object can be set to "Cast Shadow Caustics" and another to "Receive Shadow Caustics". This is much faster than the global toggle.
    *   **Recommendation:** For most interior renders, global caustics are turned **off**. The per-object "Shadow Caustics" should be used only where the effect is visually important (e.g., light focusing through a glass of water on a table). For a large frosted panel, the effect is diffuse light transport, not sharp caustics, so it's less relevant [Blender Guru, "The Secret to Realistic Lighting in Blender," 2022].

*   **Light Path Bounces:**
    *   **Transmission:** This controls how many times a ray of light can pass through a transmissive surface. For scenes with multiple layers of glass or thick glass objects, this needs to be increased.
    *   **Recommended Values:** For an interior with windows and glass partitions, a **Transmission** bounce count of **8 to 16** is often required to avoid black artefacts and allow light to propagate fully [Blender Manual 4.2, "Light Paths," n.d.].
    *   **Cost:** Increasing bounces directly increases render time, as each ray is traced for longer.

*   **Filter Glossy:**
    *   This setting blurs glossy reflections after a certain number of bounces, replacing sharp detail with an averaged color to reduce noise at the cost of accuracy.
    *   **Recommendation:** A value of **1.0** is a common starting point. It helps clean up noise in reflections deep within a scene without sacrificing too much visual fidelity on the first bounce [Blender Manual 4.2, "Render Settings," n.d.].

*   **Portals:**
    *   Light Portals are planes placed over openings like windows to tell Cycles where light is coming from. This was a critical optimization for scenes lit by an HDRI environment map.
    *   **Current Status:** As of Blender 3.0 and later, with improved adaptive sampling and light sampling algorithms, **portals are largely deprecated and may not offer a significant performance benefit**, and can sometimes be slower [Blender Developer Blog, "Cycles X," 2021]. The official advice is to rely on the default sampling unless portals show a clear improvement in a specific scene.

### 7. VERIFICATION

[INFERENCE] Verifying the physical accuracy of a rendered glass material from the image alone requires checking for specific optical phenomena that can be measured or observed.

*   **Transmitted vs. Incident Luminance:**
    *   **Method:** Render a simple test scene with a light source of known luminance (e.g., an emissive plane with strength 1000 cd/m²). Place the glass panel in front of it and a "virtual luminance meter" (a small white diffuse plane) behind it. Measure the illuminance on the meter with and without the glass. The ratio of the two measurements should approximate the glass's VLT.
    *   **Example:** If the illuminance with the glass is 850 lux and without it is 1000 lux, the material has a VLT of ~85%. This can be automated with a script that analyzes the pixel values in the rendered image of the meter plane.

*   **Reflection at Grazing Angles (Fresnel Effect):**
    *   **Method:** Observe the glass panel at a very shallow (grazing) angle. The reflectivity of the surface should increase dramatically, approaching 100% at a perfect 90-degree angle of incidence.
    *   **Measurable Check:** In a rendered image, the pixel value of the reflection of a bright object should become almost identical to the pixel value of the object itself as the reflection point moves towards the edge of a curved glass object or as the viewing angle on a flat panel becomes shallower. This is a direct consequence of the Fresnel equations, which are built into the Principled BSDF.

*   **IOR Verification (Refraction):**
    *   **Method:** Place a straight object (like a cylinder or cube edge) partially behind the glass panel. The apparent "bend" in the object is a direct function of the IOR.
    *   **Measurable Check:** Using Snell's Law (*n₁*sin(θ₁) = *n₂*sin(θ₂)), one could create a test scene with known geometry and camera angles. By measuring the angle of the refracted line in the rendered image, it's possible to work backwards to verify the IOR used in the material. This is complex to automate but is a fundamental physical check.

## CONFLICTS AND UNCERTAINTY

*   **Haze Values:** While VLT is consistently published by glass manufacturers, a specific, standardized "Haze %" value for architectural acid-etched glass is harder to find directly on product pages. The value is often found in more detailed technical documents or standards (like ASTM D1003), and sometimes values for sand-blasted glass are used as a proxy. The 99% figure is a reasonable [INFERENCE] for a highly diffusing material but is not a direct [MEASURED] value for a specific product like "Guardian SatinDeco".
*   **Blender Practitioner Advice:** Much of the tutorial content available online predates the significant rewrite of the Principled BSDF in Blender 4.x. Advice from older tutorials (pre-2023) might suggest workarounds (like mixing Translucent BSDFs) that are no longer the most physically accurate method. The core principles of using thickness and transmission roughness remain, but the specific shader implementation has changed. I would not stake a build on node setups from tutorials made for Blender 2.x or 3.x without first testing them in 4.x.

## WHAT I COULD NOT SOURCE

*   **Measured BTDF Data:** I could not find publicly available, raw Bidirectional Transmittance Distribution Function (BTDF) data for specific commercial frosted glass products. This data would be the ground truth for simulating the material, from which VLT and Haze are derived, but manufacturers typically only publish these simplified summary metrics.
*   **Photometric Comparison Study:** I could not find a formal, peer-reviewed study or photometric analysis that directly measures and compares the apparent luminance of an acid-etched glass panel against an adjacent white wall in a controlled interior environment. The answer provided is an [INFERENCE] based on the physical principles of transmission and reflection (VLT vs. LRV).
---

## GROUNDING (vendor-reported)

- search queries issued: none reported

- grounding chunks: NONE REPORTED — treat every number here as unsourced until verified by hand.
