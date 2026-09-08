# q2-glass-transmission (grounded pass)

- vendor: Gemini `gemini-2.5-pro` mode `pro` (google_search grounded)
- date: 2026-08-08
- prompt: `q2-glass-transmission.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. FROSTED / ACID-ETCHED / SATIN GLASS

[MEASURED] Manufacturer datasheets provide the following visible light transmittance (VLT) values for single-sided satin/acid-etched glass. Haze values are not typically published on architectural glass datasheets.
*   **Pilkington Optifloat™ Satin:**
    *   4mm thickness: 84% VLT
    *   6mm thickness: 82% VLT
    *   9.5mm thickness: 80% VLT
    (Source: Pilkington Optifloat™ Satin product literature, retrieved from firstglass.co.nz)
*   **Guardian Glass SatinDeco®:** Guardian datasheets describe this as a translucent acid-etched glass that allows uniform, diffused light but do not provide specific VLT or Haze percentages in the documents found.
*   **Guardian UltraClear® (Low-Iron) Substrate:** For comparison, the low-iron base glass used for high-clarity products has a VLT of 91% at 3mm thickness. Standard clear float glass has a VLT of ~91% at 4mm, dropping to 88% at 10mm.

[PRACTICE] For a 6–10 mm satin/acid-etched interior partition panel, the VLT should be modelled in the **80–82%** band. [INFERENCE] This is based on the Pilkington datasheet values for monolithic glass of that thickness.

[PRACTICE] Double-sided acid-etched glass offers more opacity and enhanced privacy compared to single-sided etched glass. [INFERENCE] This implies a lower VLT and/or higher haze value, but manufacturer datasheets with specific comparative numbers were not found.

[MEASURED] Haze is a measure of the percentage of transmitted light that is scattered by more than 2.5 degrees. While it is a standard optical measurement, it is not commonly specified in architectural glass datasheets. Instead, manufacturers provide qualitative descriptions of obscuration. [INFERENCE] The Pilkington datasheet for Optifloat™ Satin includes photographs showing that an object 1cm behind the glass is heavily blurred but its basic form is visible, while at 40cm it is completely obscured.

### 2. MODELLING FROSTED GLASS IN CYCLES

[PRACTICE] The correct construction for acid-etched or frosted glass in Blender 4.x's Principled BSDF uses the transmission properties of the shader. The typical setup is:
*   **Geometry:** The glass panel must be modelled as a solid object with real-world thickness (e.g., 6-10mm). Thin-walled (a single plane) will not refract light correctly.
*   **Transmission Weight:** Set to 1.0 to make the material fully transmissive.
*   **Base Color:** Set to pure white (Value = 1.0) for neutral-coloured frosted glass.
*   **IOR (Index of Refraction):** Set to the value for soda-lime glass, which is approximately **1.52**. A commonly used value in practice is 1.45, which is the default in Blender's Principled BSDF.
*   **Roughness vs. Transmission Roughness:** The "frosted" effect is controlled by **Transmission Roughness**. In the Blender 4.x Principled BSDF, this is a distinct parameter. Increasing this value will blur the light that passes through the object, creating the diffuse appearance. Surface `Roughness` controls the blurriness of reflections on the glass surface itself. For a typical acid-etched panel, the surface is smooth to the touch, so `Roughness` can be low (e.g., 0.05-0.15), while `Transmission Roughness` would be higher (e.g., 0.2-0.5) to create the frosted effect.

[PRACTICE] The "rough transmission is slow and noisy" problem is a well-known issue in path tracing. Production workflows handle this in several ways:
*   **Increase Samples & Denoising:** The most direct approach is to increase the render sample count (e.g., 1024-4096 samples for complex interiors) and use Blender's built-in OpenImageDenoise or OptiX denoisers. However, denoising can sometimes produce blotchy artifacts on large, uniform frosted surfaces.
*   **Light Path & Caustics Settings:** For interior scenes, it is common practice to disable Refractive Caustics in the Light Path settings. While physically inaccurate, this eliminates a major source of noise and significantly reduces render times. The "Filter Glossy" setting (e.g., a value of 0.2) can also help reduce noise from caustics without eliminating them entirely, though this is a legacy setting and disabling caustics is more common.
*   **Shader-based Approximations (Faking It):** A very common production cheat is to create a material that looks like frosted glass to the camera but behaves like simple transparent glass for light transport. This is done using the `Light Path` node to mix a full Glass/Principled BSDF with a simple `Transparent BSDF`. The `Is Shadow Ray` output is used as the mix factor. This allows light to pass through the panel without undergoing complex, noisy refraction calculations, drastically cleaning up and speeding up the render of the rest of the scene, at the cost of losing accurate caustics from the panel.

### 3. WHAT A FROSTED PANEL LOOKS LIKE PHOTOMETRICALLY

[PRACTICE] When a camera sees a lit room through an acid-etched partition, the image is diffused. The scattering of light obscures details.
*   **Silhouette Resolution:** The ability to resolve silhouettes depends on the level of frosting/haze and the distance of the object from the panel. Objects very close to the glass have more defined (though still blurred) outlines. As the distance between the object and the glass increases, the silhouette becomes completely indistinct. One manufacturer datasheet illustrates this visually, showing a vase 1cm behind the glass as a recognizable shape, while at 20-40cm it becomes an unidentifiable blur.
*   **Apparent Brightness:** The apparent brightness of the panel is directly related to the brightness of the space behind it. With more light behind the glass, it appears brighter and more luminous. If the space behind the glass is dark, the panel will appear darker and more muted, often taking on a greyish appearance. The general rule is that visibility increases from the darker side looking toward the brighter side.
*   **Brightness vs. White Wall:** [INFERENCE] A frosted glass panel with a lit room behind it will generally appear less bright than an adjacent, equally lit, diffuse white wall. The wall reflects the light from the room's luminaires directly back at the camera. The glass panel transmits light from the room *behind* it, and this transmitted light has been attenuated by the glass's VLT (e.g., 80-82%). Therefore, unless the room behind the panel is significantly brighter than the room the camera is in, the panel will read as a slightly lower luminance value than a lit white wall. NO SOURCED VALUE FOUND for a direct measured comparison.

### 4. MIRRORS

[PRACTICE] An interior mirror is correctly built in Cycles using a metallic workflow.
*   **BSDF:** Use the **Principled BSDF**.
*   **Metallic:** Set the `Metallic` value to **1.0**.
*   **Roughness:** Set `Roughness` to a very low value, typically **0.0**. Any increase will create a blurry or "brushed" look.
*   **Base Colour:** This defines the reflectivity. For a perfect mirror, use pure white (Value = 1.0).

[MEASURED] Real silvered mirror glass has a very high reflectance across the visible spectrum.
*   Silver reflects approximately **95%** of visible light. Some sources cite values as high as 97-98%. For rendering, setting the Base Color to a value of **0.95** is a physically-based starting point.

[MEASURED] The greenish tint of standard float glass comes from iron oxide impurities in the silica. This is most apparent when viewing the glass from the edge or in thick pieces. Low-iron glass (such as Guardian UltraClear®) is used to create a more neutral, colorless mirror. NO SOURCED VALUE FOUND for the specific CIELAB or RGB value of this green tint. [INFERENCE] To simulate this, one could introduce a very slight green hue into the Base Color of the metallic shader, or more accurately, model a thin layer of glass (with IOR 1.52 and a subtle green `Volume Absorption` color) in front of the metallic surface.

[PRACTICE] The secondary reflection from the front surface of the glass is a key visual cue.
*   **Modelling:** The most physically accurate way to model this is to have a solid piece of geometry representing the glass (e.g., 3-6mm thick) with a standard glass material (Transmission 1.0, IOR 1.52), placed directly in front of a separate plane with the metallic mirror material. This will naturally create the faint secondary reflection from the front glass surface and the primary reflection from the silvered back surface.

[PRACTICE] Common failure modes that make a rendered mirror read as a white or emissive panel include:
*   **Incorrect BSDF:** Using a simple `Glossy BSDF` without a Fresnel input can look fake. Using an `Emission` shader will make it glow.
*   **Incorrect Metallic Workflow:** Setting `Metallic` to 0 and trying to use the `Specular` parameter will create a dielectric (non-metal) reflection, which is incorrect.
*   **Environment:** A mirror in a pure white or black void will reflect that void, appearing as a flat white or black panel. It needs a detailed environment to reflect to read correctly.
*   **Light Bounces:** If `Glossy` light path bounces are set too low (e.g., 0 or 1), reflections of other reflective objects will not appear, making the scene look flat and incorrect.

### 5. CLEAR GLAZING AND WINDOWS

[PRACTICE] For interior renders, practitioners use several methods for window glass, balancing realism and render time:
*   **Real Glass:** A solid pane with thickness, using a Principled BSDF with `Transmission` at 1.0, `Roughness` near 0, and an IOR of ~1.52. This is the most physically accurate but can be slow and noisy, as all light entering the interior must be transmitted through it.
*   **Shadow-Catching Invisible Plane / Architectural Glass:** A common optimization is to use a material that is visible to the camera (showing reflections of the interior) but transparent to light rays. This is done with a `Light Path` node, mixing a `Glass BSDF` (for camera rays) with a `Transparent BSDF` (for all other rays). This lets light flood into the scene as if there were no glass, dramatically reducing noise and render time, while preserving reflections.
*   **Nothing at All:** In scenes where the window is not visible in reflection or is out of frame, it is often removed entirely to allow the HDRI environment light to enter unimpeded.

[MEASURED] Key values for clear glazing:
*   **Float Glass IOR:** The refractive index for standard soda-lime float glass is **~1.52**.
*   **Low-E Coating VLT:** Low-E coatings are designed to block infrared and UV radiation while transmitting visible light. Typical Visible Light Transmittance (VLT) for residential glazing units with low-E coatings is in the band of **40% to 80%**. (Source: "Low-E Glass Windows", windowsmanufacturer.com)
*   **Typical Residential VLT:** For residential windows, VLT values between **30% and 70%** are common, balancing natural light with glare and heat control. Some practitioners recommend 40-70% as an optimal range.

### 6. GLASS AND LIGHT TRANSPORT

[PRACTICE] The following Cycles settings materially change the quality and cost of rendering glass in an interior scene:
*   **Caustics:** This is a major factor. Path tracing engines like Cycles are inefficient at rendering caustics. For architectural interiors, it is standard practice to **disable Refractive Caustics** under the `Light Paths` settings. This single change can dramatically reduce noise and render times with minimal visual impact on the overall scene lighting. Reflective caustics can sometimes be left on but are often disabled as well.
*   **Light Path Bounces:** The default `Total` bounces (12) is often higher than needed.
    *   **Recommended Interior Values:** A `Total` of **4 to 8** is often sufficient.
    *   **Transmission:** This is critical for glass. It needs enough bounces to pass through all layers of glass in a scene. A value of **4 to 8** is a common starting point. If glass appears dark, it's often because the transmission bounces are too low.
    *   **Glossy:** Affects reflections within reflections. A value of **2 to 4** is typically adequate.
    *   **Diffuse:** Affects indirect lighting. A value of **2 to 4** is usually enough for interiors.
*   **Filter Glossy:** This setting blurs glossy reflections, which can soften and reduce noise from caustics at the cost of accuracy. A value of 0.1 to 0.5 can help clean up noise if caustics are enabled. However, this is now a less common approach than simply disabling caustics.
*   **Portals:** Adding an `Area Light` set to be a `Portal` in window openings is a critical optimization for interior scenes lit by an environment map (HDRI). It tells Cycles where to focus its light-sampling rays, leading to much faster noise reduction for the same number of samples.

[INFERENCE] **Cost Trade-off Summary:**
*   **Highest Cost/Noise:** Refractive Caustics ON, High bounce counts (>12).
*   **Medium Cost/Noise:** Refractive Caustics OFF, Moderate bounce counts (Total 6-8), No portals.
*   **Optimized for Interiors:** Refractive Caustics OFF, Moderate bounce counts (Total 6-8), Portals on all windows, using "Architectural Glass" shader tricks where possible.

### 7. VERIFICATION

NO SOURCED VALUE FOUND for a method to *quantitatively automate* the verification of a glass material from a rendered image alone using the specific checks requested. However, the physical principles that should be visually checked are well-established.

[PRACTICE] A visual, qualitative verification would check for these key physical behaviours:
*   **Fresnel Effect:** The most important check. For a dielectric like glass, reflections should be very faint when viewed straight-on (at normal incidence) and should increase to near 100% reflectivity at grazing angles (viewing along the surface). A material that has uniform reflection intensity across its surface is physically incorrect for glass. This can be checked by placing a sphere with the glass material in the scene; the reflections should be almost invisible in the center and strongest at the very edges.
*   **Reflectivity at Normal Incidence:** For glass with an IOR of 1.5, the reflectance at normal incidence (looking straight at it) should be approximately 4%. [INFERENCE] One could render a test scene with the glass plane facing the camera, lit by a known-intensity light, and measure the pixel value of the reflection to see if it corresponds to ~4% of the light's intensity, but this requires a carefully controlled test setup and is not a simple check from a typical render.
*   **Conservation of Energy:** The combination of reflected light and transmitted light (plus any absorbed light) should not exceed the incident light. A physically correct BSDF will handle this automatically. A "fake" material (e.g., using an `Add Shader`) could violate this.

## CONFLICTS AND UNCERTAINTY

*   **IOR of Glass:** Values cited range from 1.45 (Blender default) to 1.55. The most common measured value for soda-lime float glass is ~1.52. The difference is subtle but present.
*   **Mirror Reflectivity:** Values range from 90% to 99%. The most consistently cited value for high-quality silvered mirrors is in the 95-98% band. Using a value of 0.95 for the shader's base color is a reliable starting point.
*   **Handling Noisy Glass:** There is a conflict between physical accuracy and render efficiency. The physically correct method is to use a full glass shader and increase samples until the noise converges. The common [PRACTICE] is to use "cheats" like the Light Path node to create glass that is invisible to shadow rays, which is physically incorrect but often visually acceptable and much faster. The choice depends on the project's requirements for accuracy versus speed.

## WHAT I COULD NOT SOURCE

*   **Haze % for Architectural Glass:** I could not find any manufacturer datasheets (Pilkington, Guardian, etc.) that specify a quantitative Haze percentage for their satin, acid-etched, or frosted glass products.
*   **VLT of Double-Sided Etched Glass:** While sources state that double-sided etching increases opacity, I could not find a datasheet that gives a specific VLT value for a double-sided product to compare against its single-sided equivalent.
*   **Quantitative Obscurity Metric:** I could not find a standard or measured value that defines at what haze level or diffusion angle an object's silhouette ceases to be resolvable at a given distance.
*   **Measured Luminance of Frosted Glass vs. Wall:** I could not find a published study or measurement comparing the apparent luminance of a backlit frosted glass panel to an adjacent illuminated white wall in a typical interior.
*   **CIELAB/RGB Value for Float Glass Tint:** While the green tint of standard float glass is widely acknowledged to be from iron oxides, I could not find a sourced, standard CIELAB or sRGB value for this color.
*   **Automated Render Verification Method:** I could not find any published tools, scripts, or established methodologies for automatically and quantitatively verifying the physical accuracy of a glass material from a final rendered image based on the criteria requested (luminance ratios, Fresnel curve). The verification process appears to be primarily qualitative and based on the artist's visual assessment of physical phenomena like the Fresnel effect.
---

## GROUNDING (vendor-reported)

- search queries issued: 51
  - `architectural frosted glass optical properties datasheet`
  - `acid-etched glass visible light transmittance haze`
  - `Pilkington Optifloat Satin glass datasheet`
  - `Guardian Glass SatinDeco datasheet`
  - `Saint-Gobain SGG SATINOVO MATE datasheet`
  - `one-side vs two-side etched glass transmittance`
  - `visible light transmittance 6mm 10mm satin glass interior partition`
  - `Blender 4.x Principled BSDF frosted glass tutorial`
  - `Cycles transmission roughness vs surface roughness glass`
  - `Blender thin-walled vs solid geometry for glass`
  - `Cycles noisy glass transmission solution`
  - `Blender render caustics settings for interior`
  - `photometric properties of frosted glass partition`
  - `visual obscurity haze measurement frosted glass`
  - `luminance ratio frosted glass vs white wall`
  - `Blender Cycles realistic mirror material setup`
  - `reflectance curve of silver-backed float glass`
  - `CIE standard for float glass color`
  - `modeling secondary reflection in mirror Blender`
  - `common rendering errors for mirrors in Cycles`
  - `Blender interior render window setup`
  - `IOR of architectural float glass`
  - `low-E coating visible light transmittance values`
  - `typical VLT for residential double glazing`
  - `Cycles render settings for interior glass`
  - `Cycles caustics performance impact`
  - `Cycles light path bounces transmission interior`
  - `Blender filter glossy explained`
  - `verifying physical accuracy of rendered materials`
  - `automated render verification Fresnel`
  - `measuring luminance from render`
  - `Guardian Glass SatinDeco VLT haze datasheet`
  - `acid-etched glass optical properties haze measurement`
  - `double-sided vs single-sided etched glass light transmission`
  - `Blender 4.2 manual Principled BSDF glass`
  - `Blender 4.x official documentation transmission roughness`
  - `production rendering workflow noisy glass Cycles`
  - `light diffusion through frosted glass angular distribution`
  - `luminance measurement of translucent building materials`
  - `perceived brightness of frosted glass partition`
  - `spectral reflectance of silver-backed float glass`
  - `CIELAB L*a*b* values for standard clear float glass`
  - `Blender Cycles setup for two-surface mirror reflection`
  - `refractive index of architectural soda-lime glass`
  - `Cycles architectural interior rendering settings guide`
  - `quantitative validation of PBR glass materials from render`
  - `measuring Fresnel reflectance in rendered images`
  - `Pilkington SaniTise™ float glass datasheet optical properties`
  - `Guardian UltraClear float glass datasheet`
  - `reflectivity of silver mirror coating`
  - `CIE 1931 color of standard float glass`

- grounding chunks: 33
  - advancedtechnicalprod.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETCdrmyQsvGme0qd5Eg6w8125X2fpC01ll5S51njm5TlyyY8VRWjG3g83wP_5TqoBpp054ZJQHMnitRHg3FkAB7UFrF6zdESsjvmSYaTwgTsalV8NHADdpkLjLp-jJuT7JRxUKomuGjOHeWA_gMQ8oH-LgjtuvTa690wmIfckIxWEvFkruuz64ly4qzxAPb3yyFOBuEEEbkThwa5RASY2plXrfJL0=
  - bfymirror.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH94sl8SWOrCAtb8973943ZGfI9IdxYsbmjrSAr1OpBWHNxZfmGnAvoekJRscaHmdMufCxJzYLI50hqxUgDqfOI0bbzl8hIq2U-O3E7jg4-pIFhXyi8y7_ZWrUhPNne2riFzy96NCw=
  - vagon.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEJY3giiRDNOwUZdnk_sA32s3fVOWI3cqKDZWniiITVcXP6RqBvPUDNQppjB0FjNuwscpm-W58RmtWzhZ6qOg85y7DIAOdkx01h4AYglbF66FU9idZw2PDffBIOJ73O7N5rtiIbxrOpvX2OjyiDRkmmyjxHMmg=
  - t4design.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFK4q2m8X7KFCxjuwvJPf1YrsGLcN0cmVFX6qFem1Z3eAIzjiF7STfSvhNQQ0fb_qsILIbp9L5dy-GBAOVZFy4-4m5mcanmIcJgs_SVPC09abwk4ccHwnWuJ9HAQXfbo3BAsXKBcuWqm3k2cmh8DeNQfb-olxed0jitwttpKJqt1BFrC9axNK11F9WprRM=
  - guardianglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1NYnZPwLb9_3-VZilusueT0qq1qDRimCQJzyk9Xa_toI4y2uBZeQzW2LqjiObs6n7WKxu9tULJ93ItAwLZfcm8V1sW1noYEj8LiOGVnGNFIzm7SIKx46fK7irQwnyncTivO4RPocP2XXiFF16XSJlmg8oSO_qWpcj70cQ5FHux0dZojs94oGoQZehEMdli5A=
  - groupesvr.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG2H-DxedMDdhlbtCviGDjah9aHnoV_DaYHwBxDJCDtSlJkIwXVTjXmVO_uHnBnbLxeHQLerx-6SW3SnDatqS5ybWZgIkhjNQ_idaBl6OGrwyPPyCMudnNZhc4MjSnKzO6oX9PGSxCWda1PihSxnYf170G5g0Jg5mzVyuxb4aj1TaG1MUxjt0U1A855QUz3wBRFN6yvvQ==
  - shhipanda.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFy8QxAuwDukiTqLBQh8kg3QJQxXlAimC9JfXf9oUbOeam2kT2CNT2O7YYBGzaWPDAiWBXr1HePKilqspzIhppfng7Wc7wAZM31XHdNuHq2BTa9HusF4qye6Yn61n7Izu4g-_cBK3slBYxHnJYQM6vbYECY-rgaQ0gbnqT1qEloE95Uy-kU30bDY7X8LPUZTxk9-FZ9xd5J-ssBUZyxSK9L
  - walkerglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHSXiUIvT6hOovA3fvL1CmbmKaxKUg3Q-ou6NJP9BEfqvUj1pVv5OUMFm30hm7bocLKMAIX21TWBZIA0lD6e2vmPOBeTXtF-lZNVdk0kUf8J8Cn-BoNepAZeDzdzURnEg5fuKGnbCX5Qd3IfJa6PVc4_AEo8Ai9hAtb7K0=
  - walkerglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHARc2xO9ST5Z3oWU3fZbZuQ_fCRffjasf0woZ6CYSZG4BO57so4wt0R8hs_7y0k_I8394vJmmvVlMZearOPRvfQrcmX11whGzpss58Gx4hMp1T8Wlo5l-JiImrwcv2LLd6XvZWklw_lGrwc01eEhsH6FGaaYPbTs4V9jcUJw==
  - livehome3d.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGbqg6hc4oNyZWgYmAAAH2BxvKEo-FlWNbjNKeMmL3rAtEDquaH_7op5F-TCHbgnM2ztO2h90ezE91wWluTQ_0trNEWl3jonBHbHtW-daI8-wFQUfN7t6T-8mzdRQxXf9PhKpDYWvPGco7WDUBAQ5fBnrKUfw0ZWahHTKOmsGbj
  - luminitco.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFmMrzbUhD0Sb5w3AMCkNLwBkNE77oi2FnhptXF-YSMxrzZAs1v6BPh4ykcSOFg3poluy0LPL0a2sq071iuak_kZ5QeY88etXcwD9KlSuaep_qylaPJBbmJKSOYaIclWiUNwjVs-XIjI68gAUZNM6pX7mDd8r8yoRT23C1JRfCu34WBPY1OGbORJTYYLTYdU-c5Z56bsGQiJQ==
  - wikipedia.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF8ss18y-U-sgKdr-SMji9h_-w9SNX3O0T0PY5RrXqwWWgLULIYu0qY4ExJNVNsP5rXpJYbR0BtkbERmm9OYF9cJjTx878R9hfTaUFDy2m1fGh0A84AvVhk6T-GFrUIq_xAPrLsESYSfq3hWF9lFrw3
  - odederell3d.blog — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGve-lCYi5vGO1NbnD-X03svaaB21XTpJ0063RCR3V5_iAFSVnl4r5driH_HfW5X3pTMdfdqYjNWHYF6wtm51GdB1WzKieBJx0VQxzFfQIeihBBF-MUsMrOSS66aySKHNZ8f1d8HEuwoDKAHghUJDCyGhPQ
  - luck-glass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCF6zwwYQXlnpOubUQX4Bi2XYwvPM9UEaO1S_YsYVlbZBvdYdjEE8ju6TBHQpe_XLt7l3vf3rAZKyhtn2qerxT3Osy31zh5zbwCPYOgLfjCFUQU1Y5RCu91VFEPZrXd9kjgceVg96-VQIm0-bKlbXovpv3dAjECTiMjnT6sdprvbq9kIHH0pjoMp9JXxf7QznSXIFdi743cw==
  - quora.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEXzOrDY6XGiPzoM6VXj5Ic3PY7nkPl1zVuYZx_7wEseCEWwxCYTL0riYNOC56SWd9h3GznklkbkD9H2W8A1kC2lbkdaFuc6oXyVf6JwM6zvQJIHeL6pjJu0fyKAWn8VQb5qx30rD63PrmPpeteLpV0eLAUuOWqrMt-vWVcvgXR2WmkvNKUNj19vi4LHk8E4NZzNhAOd2aoP7jCaY5CS54MKf5PiFayF8d3_13xSv9ic8CkHt3rMJlzWbZ-HldDohmgcCExoLjqHzUZdyg=
  - blenderartists.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGhfCidLRW7OYrEmN09vXdZ2r5RMYNoVHCvPoPkIHDx4Z6ahY6ZJ6hZBaTy2y2PBabH3QfZfNrRPIA9Kkey4-BJnaHsv0ZqeDqdJYJhhru2DCvv1EhexZU_J2wTNR5kTiEBthwqG8U2lWCCGje-JM_h9PaVIeT0WAHCvFN9JHqv2t78UmkHos7bGqFZ
  - nih.gov — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGMGapTmloEvhJMsRf79fr0EioCMlvDNG8-2Q5pJCyuiIdA9OjqgVhROVeitQgoftptTqqylCPkvldinfnCpkw5e49SIWcq7zsdVirHAAfOHHrCAy7dn3NlfdYTDgQ28B4bXq4h1fZWdZMGbPA=
  - guardianglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGkl0wXMFtxYwx4fUTxoMQJz5co97fKCuiWGjttk_6IQlL3foWhb800BkKEaC0sQqBjSCEwuiWeNHDhDyzZlgrTtHmSgZJLlWMhw3u70VMMIZbvGFHMJORVaAiY15_VNvpXBsGs3Qjh993AFvJidg5SoPmmu_6g8aHpC4s6z0FaT39vipof5Ys=
  - rp-photonics.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHrEIwWNwJwyXADe4Ekp6PXo1-6tb3zz31zG2Y4Qi0kXr30Qyn7ayWtaqo6iaAWLZ2oqcFsjKT5eMzT2XAZfLpOSeQB4b5hvRVqu4cO5CDNS8_gwhIo3RZT92bpYMlfRmC6s1MNhZg=
  - mandmgutters.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFhipd0a08jof8w-sjyo-GL60WgSi4deM-tA5cOVwt9mbthOAbyQReQvb9cA_crikeFhHPYLh5-IhlGE52DSz-7J2nIJxNTo7vFV5CZ2j4h-x5PcE2kqC0clFmA9qZc8fylSGQ8bbUmgahWhHobAFXJkdT68u4K866zVtRA6wZSsdCS37AZHlg7wjXj4uPqMLDISzj3
  - sanssoucie.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGqAhdFf0J6kq_o07eKfOCd8oSRuBaKXq-2oP_4fFrPJRt62uxnbSaNQhoeGbpTeIGjJfIa2_DxYz7c6M2_XHmyA-Rx7HS9YbTlPsMI3I4_qMLRwQ5Uu-sS9uwyUulp22kpbeNkc9xmiAwgcS61BU-oJDxoAGb3mDlRxu_zQVxOe4ypNVKDP9_9DOrhMZLqLcs--gZI0bYie3wziq7wAvgnydK4hVwHQQ==
  - sharrettsplating.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG8OnWmHQCfEyoY5xKu3_EhhzLI1QQmWBpKN-NEP4rNPYKlGdY-fpNkadEXrv4aOkXBtsHkLfr1KXfA0uHsE1Ln1W1IkXJljS5LSkvG47zBnUdBtuYzJFgSO9oaJK9DHu200V63mPoekhM5lY9sYWi4_8JQbLrDqvSggqH7D3weyw==
  - photonics.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQERXQSS4-fjeJu5h4aob6UlQxbJmiegtG76BI1riz7K2ZYOVaynaOF-edj5kY8A26oH8Y6rVWSkPo2g3Epbczgt-_TZR7mAQcBNB3J4OJJQ3LAd09mDHDCdO8ge-5oQXLyFCgeYZSczOoB2qWaH8EAU9-VUMAkNwEXhdBWe_t3F8e-48K0SDmWbUpB4UiPI
  - google.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFN_RLBoG2oblu-k6H9bMaQYqYoOJojaL6fcCG1DAZI4PzHTm5gx_tSipli9tqZ9HcSGHJmskuO7Zk5Y2DVZc-caXWlJTbmQjlED_8GwllwpHyUVqvQacEQ4A3r5fDjt-YYYsLCjluTiCLH
  - chinanorthglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQExflMHP49vCsez3wKgy7q9eNjMMuAKrqUsuKcJgfIZgfWuu_OuZkIvRL21aWP2bUDZOvh0uPbJnMz5oibEuSWJ9QBsKEUfGqibQkMgy1mL7obtz3OQmShAP7XMRGyNBHawtcv_rYt57u53invSuR3NoiYXLQfQ-PKDTI2yHBalIGr926X0V2eZbg==
  - researchgate.net — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGyhzqKcJhPBcYeG_LkF5rdVSjJCzlCioot3aQ0dc9GNe50WGA1Nxit3DY1-oLxSHJydzPZ_qCMtAp7RPiFo1YzIaTA9e_4tsZ4bRahLlsTIRiYLtHnfawYVuuKxpue0dSDmXZogQdJMJsLM5up0iLD3DqkKwkYcyeeaNg1RdFycfQQz6pauroVWWnNkr_YWhogj6EIP8eMDBnwcGzAgDw0Bxd2ftbrv-GNv5d6nRpIiMs=
  - 3drender.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFigBHGyA0CgU0Mt8ENr8OVfVPZ9tgrtH9E6k4lXK5Zd6lmSFVk_MORZMUksJjhGXDKwuTE1CrGBybo4wxpljMHJ-RyDkQuDoaZGeXCVR2hXpPt0Ijo29pD4U2e-G4FRypRXYq8DQZR7KrpFTLITw==
  - guardianglass.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGnpipUd6GEgaqlWbGwbXYSPDUBng0s9POF_8ES7oWzBwAOPN9cD9wJ-R4luWpCr-Z9j0nPC2g6Ur3hhldoQjsj8ljrAFR2EX3is_qaDrTSMYekHL9BuDfm6eutYf3Te_TgZI8m2gSw2wTqt8BsXICoboN985g6Vyl2cQ1ISbTAYTXSFZi2ulHWFBQrYzuU9OsTVlHKEP0OkL8fYZyGfwkri5dM51SEVIYE4msdXv-7DWPtnQz_2Dc_vO4qokO6eFT5j-Ad
  - superrendersfarm.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH6p8Fp-Wv108TsMFKQ05ihQjsWcjrgAbNWKz7bfusbJV0YFWOval4nHeF2HVbZdNnvEY01Zz8NsQnEHDKE6uPTgTXWyAD7QqmwXSELF-5PP8sa-C-Wv5ceUaB9xI3oLrgM_1nx0ydhFvD5NmLC5ieh_n7gU3EKnbsT7pUtMzM5PEykRwoGkKl8QW8=
  - thomasnet.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFpRghRSd7SDl5Kif02cNoPosBm1F7A-M2756zI3hMwbkHIxmP6g1u47tby68JXjQ7Z4h4dHkbbfTY3C-qNlL9vb_QEUuL2ZiT5LsweDcuq1OVcZkfrJrAPc7PTUu9yINOFBEPyYOeVz2G9syz1NKYxb9nJAKF4OX4t9euq4GcuKMaxcXUgMZg=
  - sgpinc.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEoNgMK4CABuyjvkaPitmCqwRd1CBTsKmbHTetLUxmKZ9lF5y6qLQeojhIfA1Q6tHoMgsVoSS2oqysBh4_-4UnZBLyece0NW1muANfhgPujPLvRYcHVxbwh7Byj2e6b8WTBZVsGSnZF6vD8yYPeUMxO_QkoL4hixB-pzhbB1Ta4IWvGoA==
  - stackexchange.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHL_vjLDmvJrHlSAAQ2-vDsBLXYz6Ug_QVcHg19jQqjZ8ODjej0rR0sM-LUQA9MbVJX9JJUN0J6zPx5fUvXNfZY00KsSI-n2XjtHs2LHdM5m_gSRHj1ebFq1sxVn0iOYjxbfAn26MYuWGO0jkTf8RbpZCfJOzfUUt34biMA_vYeYgdI3ho5raZ2dbceH3M1kVtrzU3t
  - cornell.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZNyQPMSIe50s3eT7IW-Jq6slF9ATc_vcK9qPNwMKIwhg-4tpudGN8WoovxaU3VoWzuSs1cBhxF01Ky2adjnaDfofLAwr95A9sWlq-tPuNxZzUUKNvevu7yG5F8frXuT-Q70H9AdWAF0174c_61xsSEvD7IP0=
