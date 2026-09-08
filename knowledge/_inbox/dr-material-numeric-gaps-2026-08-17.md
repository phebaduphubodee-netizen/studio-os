# DR — material numeric gaps — F0 table, normal green channel, emissive bounds, roughness deltas, Cycles fabric sheen, albedo reconciliation

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `56227928-a36a-415f-a850-45bf565b88cf "DR: material numeric gaps F0 sheen emissive 2026-08-17"` |
| conversation | `b9d45c71-cdaf-4706-8c4d-67a6020aa839`, turn 1 |
| fired | 2026-08-17, builder-initiated (owner order this session: "spend all DR on this" — the Blender craft gap) |
| sources | 106 imported, 89 ready, 17 error |
| asked because | pbr-material-behavior.md declares four do-not-invent GAPs in its own words ('no studio value exists, anywhere'): dielectric F0, normal green-channel convention, emissive bounds, roughness-variation amplitudes — plus the two albedo bands carried unreconciled by design, and Cycles-native fabric sheen existing only as one bouclé row. |
| consumed by | pbr-material-behavior.md gap sections (distillation owed); build_room.py material assignment (green-channel handling per source shelf; velvet sheen); albedo_plausible() thresholds remain PR-only — the reconciliation MATH is now sourced but moving a threshold stays its own decision. Nothing consumes it yet at staging time. |

## Caveats stated before anything here is believed

The prize is §6: the 30-240 sRGB and 0.04-0.9 float albedo bands RECONCILE to the same physical values through the sRGB OETF (30→0.013, 50→0.032, 240→0.871 — landing exactly on the ACEScg filter bounds), with the math shown and sourced; the two bands are one standard at two pipeline stages, not rivals. Honest per-family refusals stand: F0 for finished wood/stone/painted wall/ceramics/leather NOT IN SOURCES (generic dielectric 2-5% band + marble/porcelain IOR 1.500 are the fallback); per-class textile sheen values NOT IN SOURCES except velvet (sheen weight 2.0 typed past the 1.0 slider, sheen tint 1.0, sheen roughness ~0.3 — Blender Artists, single-source); interior-fixture emissive bands NOT IN SOURCES (real photometry anchors instead: 683 lm/W peak efficacy, candela=watts×683/4π, display/appliance nits tables); roughness DELTA amplitudes per family NOT IN SOURCES (wear-zone concentration logic + AO-drives-roughness-in-crevices recipe carried instead — the amplitude-bisect instrument stays ours). Quixel's green-channel convention is CONTESTED across three sources (all shown per grounding rules) — treat per-asset detection (the two visual tests) as the law, never the brand default. Synthesised-self-source ("Shading Standards and Asset Pipeline Reconciliation in Blender Cycles") mostly signs refusals and the reconciliation math — verify the OETF arithmetic locally before wiring (it is checkable by hand). qa-history holds 2 turns because attempt 1 died in an RPC decoder error and the retry re-asked — the answer of record is the FINAL turn.

## The answer as returned (source titles inline; [n] markers as returned)

### 1. Dielectric \\(F_0\\) Table

Based on standard physical models, the Fresnel reflectance of a dielectric surface at normal incidence (\\(F_0\\)) is derived from its index of refraction (IOR) `[1, 2]`. Real-world dielectric materials generally display a reflectance range between **2% and 5%**, which translates to a linear specular level range of **0.02 to 0.05** or display-referred sRGB values between **40 and 75** `[3, 4]` (Source: **The PBR Guide - Part 2 - Adobe**). The standard baseline reflectance for common dielectric materials is defined as **4%** (linear specular level of **0.5**, or a standard IOR of **1.5**) `[3, 4]` (Source: **The PBR Guide - Part 2 - Adobe** / **Filament Materials Guide - Google**). 

The empirical values structured below represent the available data across requested dielectric families:

| Material Family | Index of Refraction (IOR) | Normal Reflectance (\\(F_0\\)) | Linear Specular Level (0.0 to 1.0 Scale) | Source Document Title |
| :--- | :--- | :--- | :--- | :--- |
| **Fabric / Textiles** | **1.5 to 1.62** | **4% to 5.6%** | **0.5 to 0.59** | **Filament Materials Guide - Google** `[5, 6]` |
| **Glass / Plastics (General)** | **1.5 to 1.58** | **4% to 5%** | **0.5 to 0.56** | **Filament Materials Guide - Google** `[5, 6]` |
| **Glass (Soda-lime)** | **1.520** | **4.26%** | **0.53** | **Physically Based - The PBR values database** / **Filament Materials Guide - Google** `[5, 6]` |
| **Glass (Borosilicate)** | **1.520** | **4.26%** | **0.53** | **Physically Based - The PBR values database** / **Filament Materials Guide - Google** `[5, 6]` |
| **Paper (Office)** | **1.500** | **4%** | **0.5** | **Physically Based - The PBR values database** / **Filament Materials Guide - Google** `[5, 6]` |
| **Cardboard** | **1.500** | **4%** | **0.5** | **Physically Based - The PBR values database** / **Filament Materials Guide - Google** `[5, 6]` |
| **Finished Wood** | **NOT IN SOURCES** | **NOT IN SOURCES** | **NOT IN SOURCES** | **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** `[5, 6]` |
| **Natural Stone** | **NOT IN SOURCES** | **NOT IN SOURCES** | **NOT IN SOURCES** | **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** `[5, 6]` |
| **Painted Wall** | **NOT IN SOURCES** | **NOT IN SOURCES** | **NOT IN SOURCES** | **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** `[5, 6]` |
| **Ceramics** | **NOT IN SOURCES** | **NOT IN SOURCES** | **NOT IN SOURCES** | **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** `[5, 6]` |
| **Leather** | **NOT IN SOURCES** | **NOT IN SOURCES** | **NOT IN SOURCES** | **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** `[5, 6]` |

*(Note: While specific specular/IOR ranges for **Finished Wood**, **Natural Stone**, **Painted Wall**, **Ceramics**, and **Leather** are **NOT IN SOURCES**, the **Filament Materials Guide - Google** notes that general unspecified "other dielectric materials" fall within an IOR range of **1.33 to 1.58**, \\(F_0\\) of **2% to 5%**, and specular of **0.35 to 0.56** `[5, 6]`. Additionally, generic **marble** is listed with an IOR of **1.500** and **Porcelain** with an IOR of **1.500** in **Physically Based - The PBR values database** `[5-7]`).*

---

### 2. Normal Map Green Channel

#### Supplier Conventions
*   **Poly Haven**: Standardizes its texture distributions on the **OpenGL (Y+)** format, delivering maps labeled with the suffix `nor_gl` `[8, 9]`. The coordinate maps are authored as **16-bit** PNG files, and the platform automatically generates DirectX configurations labeled as `nor_dx` during download packaging `[8, 9]` (Source: **Texture Requirements | Poly Haven Wiki** / **3D Model Standards | Poly Haven Wiki**).
*   **ambientCG**: Primarily distributes **DirectX (Y-)** style normal maps `[8, 9]` (Source: **Switch normal map convention from OpenGL-style (Y-) to DirectX-style (Y+) · Issue #2989 · godotengine/godot-proposals - GitHub**). Importer scripts designed to parse ambientCG assets check for an OpenGL texture first and fall back to the DirectX map, inverting its green channel upon import to ensure compatibility with Blender `[8, 9]` (Source: **AmbientCG material importer add-on : r/blender - Reddit**).
*   **Quixel / Fab**: Discrepancies exist between reports regarding Quixel's default export convention `[8, 9]`:
    1. One report states that Quixel Megascans distribute normal maps using **DirectX** because it is the default in Unreal Engine `[8-10]`. However, the same thread notes that scanned Megascans asset normal maps are processed and saved in the **OpenGL** format `[8, 9, 11]` (Source: **OpenGL or DirectX for Normal maps? - Asset Creation - Epic Developer Community Forums**).
    2. Another source confirms that Quixel exports using the **OpenGL** standard by default `[8, 9, 12]` (Source: **Normal map more visibile in rendering - Daz 3D Forums**).
    3. Conversely, a third workflow guide indicates that Quixel Mixer exports maps in **DirectX** format by default, relying on its preset systems to automatically convert them for target engines `[8, 9, 13]` (Source: **Quixel Mixer To Unreal Engine 4: Seamless Workflow**).
*   **Substance Outputs**: Substance Painter project layers default to exporting normal maps in the **DirectX** format `[8, 9]` (Source: **Normal map format question : r/Substance3D - Reddit**). However, the export template system allows the user to export in either OpenGL or DirectX regardless of how the project’s internal tangent space is configured `[8, 9]` (Source: **OpenGL or DirectX for Normal maps? - Asset Creation - Epic Developer Community Forums** / **Normal map format question : r/Substance3D - Reddit**).

#### Visual Inversion Detection Tests
To identify whether a normal map's green channel is inverted, two primary visual verification techniques are used `[14, 15]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**):
*   **The Aspect-Elevation Verification Test**: The artist inspects localized micro-geometry, such as holes, cracks, or extruded rivets, under standard viewport shading. In an OpenGL-configured environment, downward light causes the upper lip of a hole to cast a shadow while illuminating the lower inner rim `[14, 15]`. If the green channel is inverted (DirectX format in an OpenGL viewport), this physical shading is reversed: recessed holes appear as raised bumps, and raised edges appear as recessed cavities `[14-17]` (Source: **Add a vmt shader parameter that inverts specific channels on a normalmaps. · Issue #3166 · Facepunch/garrysmod-requests - GitHub**).
*   **The Dual-Color Directional Light Test**: The artist visualizes the map as an illuminated sphere or bump, imagining a green light source positioned directly above the object (+Y) and a red light source positioned to the right (+X) `[14, 15]`. Under a correct OpenGL convention, top-facing slopes must show high green values (appearing green, cyan, or yellow), while bottom-facing slopes contain low green values (appearing red or purple) `[14, 15]`. If the green channel is inverted, the green highlights concentrate on the bottom-facing slopes, indicating the surface is incorrectly lit from below `[14, 15]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**).

---

### 3. Emissive Bounds

The specific pipeline requirements and numeric luminance bands for **LED cove strips**, **recessed downlight apertures**, and **fabric lamp shades (transmitted)** are **NOT IN SOURCES** `[18, 19]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**). The only mention of lamp shades is a recommendation to place a low-level emissive map on the shade to simulate light bleed, but no numbers are provided `[18, 19]` (Source: **hi does anyone know how to light a lamp in iray daz studio**).

However, real-world displays, standards, and specific environmental lighting categories are heavily documented with verified physical ranges `[18, 19]`:

*   **Typical LCD Screen White Point**: **200 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **Display Metrology and the Effects of Ambient Illumination - Pro-Lite Technology**).
*   **Typical LCD Screen Black Point**: **2 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **Display Metrology and the Effects of Ambient Illumination - Pro-Lite Technology**).
*   **Typical LCD Display (Maximum)**: **500 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **Display Metrology and the Effects of Ambient Illumination - Pro-Lite Technology**).
*   **General Computer Display**: **200 to 1,000 nits** `[22]` (Source: **Filament Materials Guide - Google**).
*   **Standard Display Brightness Study**: **52.4, 287.6, and 422.6 nits** `[20, 21, 23]` (Source: **What Is the Relationship Between Peak Brightness and Contrast Perception? - KTC**).
*   **18% Grey Point (on 170-nit display)**: **31 nits** `[20, 21, 24]` (Source: **What Is the Relationship Between Peak Brightness and Contrast Perception? - KTC**).
*   **Home Appliance Displays**: **200 to 400 nits** `[20, 21]` (Source: **Nits vs Lumens vs Luminance: Understanding Display Brightness Metrics - Riverdi**).
*   **Military & Marine Displays**: **800 to 1,500 nits** `[20, 21]` (Source: **Nits vs Lumens vs Luminance: Understanding Display Brightness Metrics - Riverdi**).
*   **DisplayHDR 400 Peak Luminance**: **400 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR 500 Peak Luminance**: **500 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR 600 Peak Luminance**: **600 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR 1000 Peak Luminance**: **1,000 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR 1400 Peak Luminance**: **1,400 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR 1400 Full-Screen Sustained**: At least **700 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **DisplayHDR True Black (All Tiers Black Level)**: **0.0005 \\(\text{cd/m}^2\\)** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **OLED Displays (Peak HDR Range)**: **1,300 to 1,500 nits** `[20, 21]` (Source: **What DisplayHDR True Black 1400 means for the future of gaming and productivity monitors**).
*   **Transparent OLED (Office Partition)**: **150 to 250 nits** `[20, 21, 25]` (Source: **Transparent OLED Displays | Transmittance Rate, Brightness & AR Applic - DisplayModule**).
*   **Transparent OLED (Commercial Window)**: **450 to 550 nits** `[20, 21, 25]` (Source: **Transparent OLED Displays | Transmittance Rate, Brightness & AR Applic - DisplayModule**).
*   **Transparent OLED (Underground Window)**: **600 to 800 nits** `[20, 21, 25]` (Source: **Transparent OLED Displays | Transmittance Rate, Brightness & AR Applic - DisplayModule**).
*   **Outdoor AR Navigation Lens**: **3,000 to 5,000 nits** `[20, 21, 25]` (Source: **Transparent OLED Displays | Transmittance Rate, Brightness & AR Applic - DisplayModule**).
*   **Iray Render Light Preset Default**: **1,500 \\(\text{cd/m}^2\\)** `[20, 21, 26]` (Source: **hi does anyone know how to light a lamp in iray daz studio**).
*   **Bright Sunlight (Fully Lit Clouds)**: **10,000 \\(\text{cd/m}^2\\)** `[20, 21, 27]` (Source: **4.19 Physical Lights - Page 8 - Rendering - Epic Developer Community Forums**).
*   **Modern LED Headlights (High Beam)**: **15,000 - 30,000 nits** `[28]` (Source: **Physically Based Lighting - Introduction**).
*   **Halogen Headlights (High Beam)**: **7,000 - 12,000 nits** `[28]` (Source: **Physically Based Lighting - Introduction**).
*   **Digital Signage**: **450 nits** `[29]` (Source: **Physically Based Lighting - Introduction**).
*   **Tunnel Signage**: **130 nits** `[29]` (Source: **Physically Based Lighting - Introduction**).

#### Photometric Mapping Guidance
In physical lighting design, radiant power is mapped to perceived brightness using the SI maximum luminous efficacy of **683 lm/W** (lumens per watt) at **555 nm** `[30-32]` (Source: **Physically Based Lighting - Introduction**). For an isotropic point light, **1 W** of radiometric energy is equivalent to **683 lm** `[30-32]`. For directional spotlights, the radiant power is converted to isotropic luminous intensity (candelas) using the following formula:
\\[\text{candela} = \frac{\text{watts} \times 683}{4\pi}\\]
Under this conversion, **1 radiometric watt** yields approximately **54.35 candelas**, regardless of the spotlight cone angle `[30, 33, 34]` (Source: **Physically Based Lighting - Introduction**).

For emissive fixture surfaces, the texture color and nits intensity work together:
1. Keep emissive color values within the standard SDR range (**0-255**) `[35]`.
2. Use the nits intensity value as the peak brightness for the SDR texture, not overbright color values above **255** `[35, 36]`.
3. The texture modulates the emissive output: full white/color means **100%** of the set nits value is used, whereas darker texture values reduce the emitted brightness proportionally (e.g., a **50% gray** pixel at **1000 nits** emits roughly **500 nits**) `[35, 37]` (Source: **Physically Based Lighting - Introduction**).

---

### 4. Roughness Variation Maps

Typical roughness delta amplitude bands (e.g., base **0.4 \\(\pm\\) how much**) and physical mask scales specifically for painted walls, oak floors, marble, brushed metals, and fabrics are **NOT IN SOURCES** `[33, 34]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**).

However, physical microscale wear measurements and environmental weathering parameters are documented and can be mapped directly to shader network values to maintain physical consistency:

*   **Microscale Ceramic Wear Deltas**: In tribological chewing simulations subjected to **240,000 cycles** at **20N of force**, standard ceramic blocks display physical delta values representing the variation in roughness (\\(Ra\\) in microns) introduced by friction over time `[38, 39]` (Source: **Wear and roughness analysis of two highly filled flowable composites - PMC**):
    *   *Fine Ceramic (CMf10) wear delta*: **0.40 (\\(\pm\\) 0.19)** (Initial: **0.27 \\(\pm\\) 0.13** \\(\rightarrow\\) Final: **0.66 \\(\pm\\) 0.12**) `[40, 41]`
    *   *Ultra-Fine Ceramic (CMf80) wear delta*: **0.29 (\\(\pm\\) 0.10)** (Initial: **0.13 \\(\pm\\) 0.05** \\(\rightarrow\\) Final: **0.42 \\(\pm\\) 0.10**) `[40, 41]`
    *   *Rough Ceramic (CM10) wear delta*: **0.29 (\\(\pm\\) 0.20)** (Initial: **0.50 \\(\pm\\) 0.29** \\(\rightarrow\\) Final: **0.79 \\(\pm\\) 0.15**) `[40, 41]`
    *   *Standard Polished Ceramic (CM80) wear delta*: **0.17 (\\(\pm\\) 0.21)** (Initial: **0.52 \\(\pm\\) 0.23** \\(\rightarrow\\) Final: **0.69 \\(\pm\\) 0.12**) `[40, 41]`
*   **Wood Weathering and Physical Scales**: Weathering processes (simulating UV light and rain) alter the wood surface profile up to a maximum of **38% change** `[40, 41]` (Source: **Effect of weathering conditions on wood surface roughness: Optimal parameters determined via Taguchi analysis - BioResources**). Surface roughness measurements utilize a limit wavelength cut-off of **8 mm**, scanning at a speed of **0.5 mm/s** over a **12 mm** scanning length `[38, 39, 42]` (Source: **Effect of weathering conditions on wood surface roughness: Optimal parameters determined via Taguchi analysis - BioResources**). These millimeter-scale dimensions provide a physical guide for scaling procedural noise in wood shaders.
*   **Flank Roughness and Cut-Off Scales**: High-load gear tooth flanks are specified with finishes of \\(Ra\\) **< 4 microinches** (or \\(Ra\\) **< 0.1 microns**) `[38, 39, 43]` (Source: **Measuring Tooth Flank Roughness - Gear Solutions magazine**). Standard profiling filters isolate roughness using cut-off wavelengths of **0.08 mm, 0.25 mm, 0.8 mm, 2.5 mm, and 8.0 mm** `[38, 39, 44]` (Source: **Measuring Tooth Flank Roughness - Gear Solutions magazine**).

#### Visual Concentration of Roughness Variations
To replicate realistic wear in a shader network, roughness variations must concentrate within specific logical zones `[45, 46]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles** / **Roughness Maps in PBR: Why They Matter - 3DSkillUp**):
*   **High-Touch Zones**: Frequently touched surfaces (e.g., handles, buttons, grips, handrails) are polished by human contact, locally reducing roughness `[45-48]`. Untouched metal parts exposed to sweat or environmental oils can experience oxidation, which locally increases roughness `[45, 46, 49]`.
*   **Hard-Surface Edges**: Exposed corners and edges on hand tools or metal boxes undergo paint chipping, exposing a highly reflective, low-roughness raw metal substrate beneath a higher-roughness paint coating `[45, 46, 50]`.
*   **Recessed Areas and Crevices**: Moisture, oxidation, and grime build up in recesses and seams, locally increasing roughness `[45, 46, 51]`. Mapping ambient occlusion (AO) data directly to drive roughness values upward inside crevices replicates this behavior `[45, 46, 52]`.
*   **Friction and Contact Planes**: Polished planes (e.g., kitchen countertops, tables) exhibit localized smudges and fingerprints that act as masks, disrupting the uniform specular response of a clean surface `[45, 46, 52]`.

---

### 5. Cycles-Native Fabric Shading

Values for specific textile classes, including **percale/cotton, sateen, linen, bouclé**, and **wool knit**, are **NOT IN SOURCES** `[53, 54]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**).

However, general dielectric fabric values and detailed configurations for velvet are documented:

*   **Velvet / Crushed Velvet**: Sheen Weight Value: **2.0**, Sheen Roughness: **approx. 0.3**, Sheen Tint: **1.0** (tint to match base color), Base Diffuse Roughness: **0.3** `[55-57]` (Source: **Velvet shader using NEW Principled BSDF Branch! - Blender Artists Community**).
*   **General Fabric (Filament)**: Sheen color (specular tint) is typically in the range **0.5 to 0.59** linear value (equivalent to **4% to 5.6%** reflectance) to match the standard reflectance of common fabrics, while base and subsurface color properties define diffuse behavior `[55, 56, 58, 59]` (Source: **Filament Materials Guide - Google**).
*   **General Fabric (Substance)**: Specular range (\\(F_0\\)) is **0.02 to 0.05** linear (display-referred sRGB **40 to 75**, overlapping the **2% to 5%** reflectance range) `[55, 56, 60]` (Source: **The PBR Guide - Part 2 - Adobe**).

#### Porting and Shading Caveats
V-Ray uses native Sheen parameters in `VRayMtl` which DCC Importer can convert directly to glTF using the `KHR_materials_sheen` extension `[61]` (Source: **3ds Max Guidelines - RapidPipeline Docs**). When porting these concepts and configuring fabric shading natively in Blender Cycles (Principled BSDF v2), several behaviors must be managed:
*   **Avoid Falloff Nodes**: "Falloff nodes should be avoided" `[61]` for sheen mapping, as they interfere with standardized PBR glTF exports. Use native Sheen parameters instead `[61]` (Source: **3ds Max Guidelines - RapidPipeline Docs**).
*   **Slider Range Limit Overrides**: Although standard sheen sliders default to a **0.0 to 1.0** scale, the Principled BSDF v2 sheen weight accepts values above **1.0** `[62, 63]`. A sheen weight value of **2.0** is necessary to simulate the lush depth of crushed velvet, which requires typing the value in manually because the default slider scale stops at **1.0** `[57, 64]` (Source: **Velvet shader using NEW Principled BSDF Branch! - Blender Artists Community**).
*   **Sheen Tint Integration**: Standard dielectrics have colorless specular highlights, but fabrics exhibit tinted grazing highlights matching their underlying diffuse color `[62, 63]`. The Sheen Tint parameter must be set to **1.0** to force the grazing reflections to match the base color, preventing the edges from washing out to white under standard environment lighting `[62, 63, 65]` (Source: **Sheen Properties in Principled BSDF Node | Blender Advanced training** / **Velvet shader using NEW Principled BSDF Branch! - Blender Artists Community**).
*   **Ambient Occlusion Shading Conflicts**: Combining standard ambient occlusion (AO) maps with the Principled BSDF node can destroy edge highlights on fabrics `[62, 63]`. To maintain a realistic fabric response when global illumination AO is active, the AO input should bypass the fabric's sheen channels `[62, 63]`. If the Principled shader fails to preserve micro-fiber highlights, a custom node group built with the dedicated Velvet Shader node should be used `[62, 63, 66]` (Source: **Sheen Properties in Principled BSDF Node | Blender Advanced training**).

---

### 6. Albedo Reconciliation

The albedo authoring bounds for non-metals are governed by two parallel standards representing the same physical properties measured at different stages of the color pipeline `[67, 68]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**):

#### Display-Referred 8-bit sRGB Limit (30 - 240 sRGB)
This rule is designed for artists authoring base color maps from 8-bit source files (such as texture photos or scans) `[69, 70]`. 
*   **Substance PBR Guide / Substance 3D Painter**: Establishes that non-metals should not fall below **30 sRGB** (tolerant range) or **50 sRGB** (strict range) on the low end, and must not exceed **240 sRGB** (or **243** on the 0–255 scale) on the high end `[69-72]` (Source: **The PBR Guide - Part 1 - Adobe** / **Game-Ready 3D Models: Requirements, Creation, and Export**).
*   **Marmoset Toolbag**: Establishes a low-end limit between **30 and 50 sRGB** and a high-end limit of **240 sRGB** `[69, 70]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**). 

#### Scene-Linear Float Limit (0.04 - 0.9 Linear Float)
This standard is utilized by physical shaders and rendering engines operating in scene-linear float space `[69, 70]`.
*   **Filament Materials Guide**: Defines this standard as **0.04 to 0.94** linear float (equivalent to **10 to 240** on a normalized 0–255 scale) `[69, 70]`.
*   **ACEScg Pipelines**: Enforces a minimum safe albedo of **0.0134** and a maximum of **0.871** under Substance guidelines `[69, 70]` (Source: **New filters for rendering ACES in Substance Painter**).

#### Mathematical Reconciliation of the Standards
By normalizing the 8-bit boundaries to the \\([73]\\) range (\\(C_{\text{sRGB}} = \text{Value} / 255\\)) and applying the sRGB-to-linear opto-electronic transfer function (OETF), the display-referred and scene-linear scales resolve to the exact same physical values `[74, 75]` (Source: **Shading Standards and Asset Pipeline Reconciliation in Blender Cycles**):

*   **Reconciliation of the 30 sRGB Tolerant Minimum**:
    \\[\text{Normalized Value: } \frac{30}{255} \approx 0.11765\\]
    Applying the transfer function:
    \\[C_{\text{linear}} = \left(\frac{0.11765 + 0.055}{1.055}\right)^{2.4} \approx 0.012983 \approx \mathbf{0.013}\\]
    This is mathematically identical to the **0.0134** linear float boundary enforced by ACEScg color management filters `[74-76]` (Source: **New filters for rendering ACES in Substance Painter**).
*   **Reconciliation of the 50 sRGB Strict Minimum**:
    \\[\text{Normalized Value: } \frac{50}{255} \approx 0.19608\\]
    Applying the transfer function:
    \\[C_{\text{linear}} = \left(\frac{0.19608 + 0.055}{1.055}\right)^{2.4} \approx 0.031896 \approx \mathbf{0.032}\\]
    This matches the **0.032** scene-linear value used to validate safe dark limits for carbon-based materials under ACES standards `[74, 75, 77]` (Source: **PBR safe range in ACES**).
*   **Reconciliation of the 240 sRGB Maximum**:
    \\[\text{Normalized Value: } \frac{240}{255} \approx 0.94118\\]
    Applying the transfer function:
    \\[C_{\text{linear}} = \left(\frac{0.94118 + 0.055}{1.055}\right)^{2.4} \approx 0.871367 \approx \mathbf{0.871}\\]
    This aligns with the **0.871** linear float boundary used to validate light-colored surfaces in HDR scenes `[74-76]` (Source: **New filters for rendering ACES in Substance Painter**).

---

🎨 If you need to construct a custom Blender node tree to automate the green-channel normal map inversion and specular scaling math on import, let me know and we can build that setup next!
