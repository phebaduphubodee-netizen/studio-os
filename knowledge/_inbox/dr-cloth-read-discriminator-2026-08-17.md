# DR — what makes cloth read as cloth — the discriminator P2r-12's three refuted instruments were looking for

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `026cdd5b-20e4-4bd8-94d7-9bb5396698ef "DR: what makes cloth read as cloth 2026-08-17"` |
| conversation | `6c60fa62-5492-41be-aa1c-1cdc8805d0e1`, turn 1 |
| fired | 2026-08-17, builder-initiated (owner order this session: "spend all DR on this" — the Blender craft gap) |
| sources | 106 imported, 72 ready, 34 error |
| asked because | P2r-12 built two instruments in one afternoon and refuted both by measurement (readable-perimeter 89.8-96.0% on everything incl. the failing duvet; flat-share 0.91-0.94%), tessellation density was refuted at p2r47 (2.4x range read identically) — three instruments dead and no measurement separates frames the judges fail from frames they pass. DR trigger 1/2: an R1-class mystery on its 2nd+ round. |
| consumed by | the NEXT P2r-12-class instrument design; bed-cloth-state-mechanisms.md §6 chaos bands. Nothing consumes it yet at staging time. |

## Caveats stated before anything here is believed

THE CENTRAL HONEST FINDING: the fold-statistics instrument we hoped to copy does NOT exist — crease frequency spectra, fold radius distributions, and a scale hierarchy are all NOT IN SOURCES, stated by the corpus's own synthesis. What IS sourced and buildable: (1) the PNAS draping scaling laws — gravity length ell_g=(B/rho g h)^(1/3), fold wavelength lambda ~ ell_g^(3/4) L^(1/4), fold count n ~ (R/ell_g)^(3/4) — a PREDICTOR instrument: compute the expected fold count/wavelength for a fabric class and drop, then measure our frame against the prediction (this is a new instrument class, not a rehash of the three refuted ones); (2) the plastic-tell mechanism — uniform roughness + smooth silhouette + missing grazing-angle sheen lobe + missing anisotropic thread-direction scattering (Sadeghi microcylinder; Disney BSDF notes); (3) distance thresholds — >3 m normal maps carry the weave, <1.5-2 m needs displacement + 2-5 mm physical bevels on fabric-wrapped edges; velvet weave repeats 0.5-2 mm; (4) perception literature warns STATIC image judgments confound optical with mechanical properties — which is a caution for our whole sighted-panel method, recorded not resolved. Synthesised-self-source pattern present ("Physical and Perceptual Metrics of Fabric Realism...") but here it mostly SIGNS THE REFUSALS, which makes them stronger, not weaker. 34/106 sources errored on import — the academic-paper share of this pool is partly unread; a re-fire with the same question could land differently.

## The answer as returned (source titles inline; [n] markers as returned)

### **1. Fold Statistics**

*   **Crease Frequency Spectra:** **NOT IN SOURCES** [1]. This is explicitly confirmed in the paper ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"***, which notes that systematic spectral distributions of fabric creases are not covered in the literature [1].
*   **Fold Radius Distributions:** **NOT IN SOURCES** [1]. The paper ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"*** notes that empirical fold radius distributions for bedding-weight fabrics are not in the sources [1]. 
*   **Hierarchy of Fold Scales:** **NOT IN SOURCES** [1]. The paper ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"*** states that a formalized, mathematical hierarchy of fold scales specific to textiles is not covered [1].
*   **Fold Spacing vs. Fabric Bending Stiffness:**
    *   Governed by the **gravity length** scale (\\(\ell_g\\)), formulated in the study ***"The elements of draping - PNAS"*** [2] and ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"*** [3] as:
        \\[\ell_g = \left(\frac{B}{\rho g h}\right)^{1/3}\\]
        where \\(B\\) is the fabric bending stiffness, \\(h\\) is thickness, \\(\rho\\) is mass density, and \\(g\\) is the gravitational acceleration constant [2, 3]. This gravity length represents the physical scaling boundary where bending and gravitational energy balance dictates fold wavelengths [2, 3].
    *   According to ***"The elements of draping - PNAS"***, a heavy elastic rubber sheet exhibits a gravity length of \\(\ell_g \approx 1\text{ cm}\\) (with a thickness \\(50\\) times that of wrapping paper), whereas thin, stiff wrapping paper exhibits a gravity length of \\(\ell_g \approx 3\text{ cm}\\) [2, 4].
    *   The transition where fabric begins to undergo visible stretching (membrane tension) in addition to pure bending is defined by the **critical system size** (\\(R_s\\)):
        \\[R_s \sim \left(\frac{Eh}{\rho g}\right)^{1/2}\\]
        where \\(E\\) represents the Young's modulus [5]. For wrapping paper, this boundary is approximately \\(R_s \approx 1\text{ m}\\), whereas for highly stretchable rubber, the boundary drops to \\(R_s \approx 10\text{ cm}\\) [5].
    *   When a fabric sheet is draped symmetrically over a circular table of radius \\(R_i \approx 12\text{ cm}\\) using a sheet of radius \\(R \approx 52\text{ cm}\\) (yielding a hanging length \\(L = R - R_i \approx 40\text{ cm}\\)), the optimal fold wavelength (\\(\lambda\\)) scales as:
        \\[\lambda \sim \left(\frac{B}{K}\right)^{1/4} \sim \ell_g^{3/4} L^{1/4}\\]
        where \\(K \sim \frac{h\rho g}{L}\\) represents the stiffness of the "effective" elastic foundation supporting the hanging fabric [6].
    *   The resulting **number of folds** (\\(n\\)) is given by:
        \\[n = \frac{2\pi R_i}{\lambda_i} \sim \frac{R}{(\ell_g^3 L)^{1/4}}\\]
        When \\(R \sim L \gg R_i\\), this relationship simplifies to \\(n \sim (R/\ell_g)^{3/4}\\) [7]. For these parameters, the scaling equations predict \\(n \approx 15\\) folds, closely aligning with the experimental observation of \\(n = 10\text{ folds}\\) on the real physical sheet [7].
    *   When a fabric sheet of length \\(L \approx 2.5\text{ m}\\) and width \\(W \approx 1\text{ m}\\) is bunched together along a linear clamped boundary with a displacement of \\(\Delta \approx 20\text{ cm}\\), it establishes an initial boundary wavelength of \\(\lambda_d \approx 5\text{ cm}\\) [8]. As folds propagate away, the first generation of wrinkles has a characteristic **persistence length** measured at \\(L_d \approx 10\text{ cm}\\) [8].
*   **Canonical Numbers for Bedding-Weight Fabrics:** **NOT IN SOURCES** [1].

---

### **2. Perceptual Studies**

*   **Real vs. Synthetic Fabric Perception Cues:**
    *   **Dynamic Video Cues:** The human visual system discounts optical and environmental variations (like wind direction) in dynamic scenes to isolate true mechanical properties [9]. In the study ***"Perceptual Dimensions of Material Properties of Fabrics in Dynamic Scenes"***, a 2D perceptual embedding of dynamic fabric videos moving under oscillating wind showed that one axis correlated with mass and the other with bending stiffness [9].
    *   In ***"Manipulating patterns of dynamic deformation elicits the impression of cloth with varying stiffness"***, researchers demonstrated that static image judgments remain heavily confounded by optical appearances, but dynamic deformation in videos allows observers to isolate stiffness, driven by **"movement uniformity"** which is computationally quantified using six optical flow features [10]. In a visual-haptic match-to-sample task with \\(20\\) observers, dynamic videos communicated fabric feel significantly better than static pictures [10].
    *   **Tactile Alignment and Drape Cues:** In the master's thesis ***"Evaluating Expected Real-World Tactile Experience From Virtual Fabric Perception - RIT Digital Institutional Repository"***, Julianna Gross evaluated 14 participants (mean age 34, range 18 to 57) rating 4 gray fabrics (100% cotton, 80%/20% nylon/spandex blend, 100% polyester, and 65%/35% polyester/cotton blend) under daylight (D65, 6500K CCT) and warm retail (3200K CCT) lighting across 8 images [11-14]. The study concluded that **mannequin-draped and hand-held images** (providing a 3D context of how cloth falls on a body or hand) aligned closest with physical, real-world touch ratings [11, 15, 16]. Specifically:
        *   **Stretchiness** was the most difficult attribute to assess digitally, with some of the highest differences from tactile baselines [17, 18]. Observers struggled most with high-stretch nylon/spandex (mean difference \\(M = -40.9\\), \\(SE = 7.02\\)) compared to 100% cotton (\\(M = 14.3\\), \\(SE = 3.98\\)) [19, 20]. Pictures showing hands (loosely holding or stretching) performed with the highest overall accuracy [21].
        *   **Luster/Gloss** was also poorly assessed digitally, with nylon/spandex showing a heavily underestimated/exaggerated sheen compared to tactile ratings [22, 23].
        *   **Thickness** was the best performing and most accurate to real-world perception [24]. For flat photos, participants tended to overestimate thickness, while they underestimated it for mannequin and hand photos [25].
    *   **Statistical Texture Models vs. Physics Inversion:** Static foveal vision fails to explain fabric categorization via statistical texture metrics [26]. In ***"Portilla-Simoncelli Texture Model for Material Perception"***, baseline material classification accuracy fell well below baseline when shown randomized textures generated from the high-dimensional Portilla-Simoncelli model for a \\(1\text{ second}\\) foveal viewing duration, demonstrating that foveal fabric perception requires structural and semantic cues rather than simple visual image statistics [26].
    *   **Painting vs. Rendering Cues:** Human judgments of fabric paintings versus photorealistic renderings are dominated by (1) the sharpness, contrast, and spatial placement of highlights; (2) the contrast between diffuse shadows and lit areas (lowlight intensity); and (3) reflections visible within shadow regions, as analyzed in ***"Perception of material appearance: A comparison between painted and rendered images - PMC"*** [27].
*   **Perceptual Metrics Validated against Human Judgments:**
    *   **PerceptionRubrics:** Gated scoring mechanisms where "Must-Right" rubrics serve as mandatory gatekeepers to penalize visual errors in multimodal models, aligning significantly better with human preferences than conventional benchmarks like DOCCI [28].
    *   **3D Physical Analysis-by-Synthesis:** Tested human shape recovery of completely occluded objects under draped cloth; top-down generative models that invert cloth physics accurately predict human judgments, whereas standard DCNNs and pixel-based observers perform no better than chance [28].
    *   **Machine- vs. Human-Derived Embeddings:** In ***"Human perception and machine vision reveal rich latent structure in human figure drawings"***, VGG-19 convolutional network embeddings were shown to be highly sensitive to stroke density, whereas human embeddings align with overall shape [28].
*   **Effect Sizes:** **NOT IN SOURCES** [27]. Standard statistical effect sizes (such as Cohen's \\(d\\) or \\(\eta_p^2\\)) comparing these perceptual cues are not covered in the sources [27].

---

### **3. Specular/Sheen Behaviour**

*   **Real Woven Fabric Reflectance vs. Smooth Dielectrics:**
    *   Standard physically based rendering (PBR) pipelines treat non-metals as smooth dielectrics, assuming a constant, colorless specular reflection of approximately \\(4\%\\) at normal incidence (\\(F_0 = 0.04\\)) and a tinted diffuse base color derived from isotropic subsurface scattering [29].
    *   Real woven fabrics fundamentally violate this, as analyzed in the physically based **Sadeghi microcylinder model** from ***"A practical microcylinder appearance model for cloth rendering - University of California San Diego"*** [30] and ***"Cloth Shading - CS Topics"*** [31]:
        1.  **Anisotropic Scattering:** Light scatters preferentially in directions perpendicular to the cylindrical fiber axis, creating the characteristic directional sheen of fabrics like velvet and satin [32].
        2.  **Dual-Lobe Reflectance:** Real cloth exhibits a forward-scattering specular lobe along the fiber direction (responsible for highlights and sheen) and a wider diffuse lobe from multiple scattering between fibers (which determines base albedo) [32, 33].
        3.  **Fiber-Level Absorption and Color-Shift:** Dyes affect light absorption differently along and across cylindrical fibers. This results in an oblique color-shift where the fabric's hue and value change drastically depending on the light-view angle [32].
*   **Measurable Reflectance Profiles:**
    *   **Linen Plain:** Consists of a repeating grid of twisted threads [34]. Normal-plane BRDF measurements show a smooth reflection with no specular peaks under most conditions, but at grazing angles under grazing incident light, reflectance increases substantially (grazing-angle sheen lobe) with minimal shadowing and masking [34, 35].
    *   **Silk Crepe de Chine:** Composed of densely twisted warp fibers and thin, untwisted flat weft fibers [36]. The flat fibers show very little absorption, producing a highly translucent, asymmetric surface [36]. Parallel to the flat threads, it shows two off-specular peaks and a distinct drop at grazing angles (heavy shadowing/masking). Perpendicular to flat threads, it displays two grazing-angle peaks visible under all lighting conditions [35, 36].
    *   **Polyester Satin Charmeuse:** An asymmetric satin weave where flat fibers remain exposed on the top surface, making the fabric two-sided [37]. Along the flat threads, BRDF measurements show three distinct specular peaks (one in the standard mirror direction, and two in equal but opposite off-specular directions) due to the three constant slope segments inside the tangent distribution of flat threads [37, 38]. The perpendicular plane exhibits strong grazing-angle peaks under all lighting conditions [35, 37].
    *   **Retroreflection:** Retroreflection returning incident light directly along its incoming path (\\(l = v\\)) is much higher than standard specular peaks in safety fabrics [39, 40]. This is achieved via a two-layer structure: a fabric base layer covered with glass micro-balls (ranging from \\(25\text{ to }75\text{ microns}\\) in diameter) hemispherically embedded adjacent to a dielectric or aluminum mirror to enforce phase agreement (US Patent *US3700305A* [39] and ***"BRDF Measurements and Analysis of Retroreflective Materials - HAL-Inria"*** [41]).
*   **What a Standard Microfacet BRDF Misses:**
    *   Standard microfacet models assume that reflections occur on a distribution of flat, mirror-like planar facets and only account for a single bounce of light, making them fundamentally incapable of modeling fabric [42].
    *   At high roughness, this single-bounce approximation causes a severe loss of energy because rays reflected back onto other microfacets are discarded by the masking/shadowing term (unlike multiscattering models where the rays escape the microfacet field back toward the viewer), as detailed in ***"MatterGen"*** [43].
    *   They lack secondary specular or TRT (Transmission-Reflection-Transmission) highlights, where light passes through the interior of transmissive fibers and picks up the material color near silhouettes, as detailed in ***"Physically Based Shading at Disney"*** [44] and ***"Light Collab - Help Documents"*** [45].
*   **The "Plastic" Tell in Renderings:**
    *   **Inadequate Roughness Mapping:** A standard dielectric shader applies a flat or uniform roughness map, which reflects light as a uniform, blurry specular highlight rather than scattering it along anisotropic thread directions, making the fabric look flat and plastic [37, 46].
    *   **Lack of Displacement and Beveling:** Normal maps only fake local surface angles but leave the silhouette completely smooth [46, 47]. On curved edges or hemlines, a smooth dielectric silhouette without micro-geometry immediately betrays the object as clay or molded plastic [46].
    *   Additionally, denim rendered with a traditional microfacet BRDF appears rigid, almost plastic-like, and more similar to a tarp because it lacks the softer specular lobe caused by absorption and scattering, as shown in ***"MatterGen"*** [48, 49].

---

### **4. Shading vs. Geometry**

*   **Geometry vs. Shading across Visual Scales:**
    *   According to production guidelines in ***"Get Realistic Textiles in Interior Design Renders - Blog"*** [47] and ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"*** [50, 51], the standard PBR stack must be deployed according to strict distance thresholds:
        *   **Distant Views (3 Meters or More):** Realism is primarily driven by the **shading/normal map** which encodes weave detail at a distance [51]. Normal maps must be tiled to match real-world weave scales [51]. For example, velvet pile repeats at intervals of \\(0.5\text{ mm}\\) to \\(2\text{ mm}\\), requiring \\(225\\) to \\(900\\) tiling repeats across a standard \\(450\text{ mm}\\) cushion to prevent flat, synthetic reflections [51].
        *   **Close-Up Views (Under 1.5 to 2 Meters):** A **displacement map / physical geometry** is required to physically deform the underlying mesh geometry [51]. This is because a normal map cannot alter the silhouette, leaving the edges of sofa cushions, folded sheets, and button tufts unnaturally smooth [51]. High-quality soft furnishings must include physical bevels of \\(2\text{ mm}\\) to \\(5\text{ mm}\\) on fabric-wrapped edges to ensure edge-catching highlights read correctly [51].
        *   **Physics-Based Folds:** At macroscopic scales, bedding and sheets benefit strongly from physics-based draping simulations (e.g., Marvelous Designer or FLeX engine) to produce natural gravity-based folds that distinguish a photographed bed from a statically modeled, regular, and frozen one [52-54].
        *   **Yarn-Level and Fiber-Level details:** For near-field views, surface-based models lack the fine-grained, fuzzy details necessary for close-up realism [55, 56]. Procedural real-time GPU pipelines explicitly render fiber curves (generating over \\(20\text{M}\\) individual fiber curves from \\(356\text{K}\\) yarn control points, or up to \\(1.5\text{G}\\) segments from \\(681\text{K}\\) control points) to avoid memory limits [56]. Yarns are modeled using three fiber categories: migration fibers (which twist regularly around the ply center), loop fibers, and hair/flyaway fibers sticking outside of plies, which are visually critical to reproducing a fabric's fuzzy silhouette [56, 57].
*   **Viewing Distance Threshold for Fiber-Level Detail:**
    *   Shading-based normal maps are the primary driver at distances of **3 meters or more** [51].
    *   Displacement maps physically deform geometry and are required for shots **under 1.5 to 2 meters** [47, 51].
    *   Level-of-Detail (LOD) systems automatically minimize or eliminate fiber-level geometry in far-field foveal views when pixel coverage drops, transitioning to far-field BRDF models [56, 58].

---

### **5. Contact and Occlusion**

*   **Self-Shadowing & Macroscopic Shadows:** Incorporating self-shadowing and macroscopic shadow boundaries on polygonal meshes is an essential ingredient to preserve the authentic "look and feel" of different textiles under directional light sources, as demonstrated in ***"Efficient and Realistic Visualization of Cloth"*** [59-61].
*   **Woven Ambient Occlusion Approximation:** In Cem Yuksel's ***"Real-time Cloth Rendering with Fiber-level Detail"***, an approximate ambient occlusion metric for woven surfaces is calculated by scaling the reflected intensity by:
    \\[(1 - \Delta x^2 + \Delta y^2)\\]
    where \\(\Delta x\\) and \\(\Delta y\\) represent local mesh deformation. This mathematical approximation reduces unrealistic specularity, brightening and smoothing shaded areas on woven surfaces to reveal true material colors in creases [61, 62].
*   **Wrinkle AO Baking:** Baking ambient occlusion is critical in digital fashion models to visually communicate the depth of fabric wrinkles and folds, as detailed in ***"Baking AO in digital fashion models - RapidPipeline"*** [63].
*   **Contact Shadows:** Soft contact shadows on plain neutral backdrops are noted as key to anchors, yet can make a scene read as a 3D render rather than a photograph if not paired with photographic artifacts like sensor noise, as discussed in ***"3D render prompts: copy, paste, adapt - Morphic"*** [64].
*   **Shadowing and Masking between Threads:** Shadowing and masking occurring between neighboring threads is critical at grazing angles to prevent the overestimation of grazing reflections, as discussed in ***"A practical microcylinder appearance model for cloth rendering - University of California San Diego"*** [65, 66].

---

### **6. Failure Taxonomy**

*   **Specific Failure Modes Named in Sources:**
    *   **Zero-Thickness Hems:** Thin polygonal sheets mathematically have zero thickness [67]. This zero-thickness profile is highly visible on exposed hemlines, collars, and cuffs, which look unnaturally two-dimensional and fake [67]. This is mitigated by using Collision Depth/Offset extrusion dials (\\(0.1\text{ to }10\text{ cm}\\)) or "Force Multiply" workflows, as documented in ***"Step 2: Cloth Controls - Poser"*** [68] and ***"9 Tips and Tricks to Achieve Realism in VStitcher - Browzwear"*** [69, 70].
    *   **Membrane Locking (Over-Smooth Curvature / Unrealistically Stiff Bending):** Constant strain triangles over-constrain bending modes, manifesting as unrealistically stiff, over-smooth, or clay-like bending, with exceedingly sharp and kinked edges, or drapes stuck in unnatural fold-overs [70, 71]. This is mitigated via quadratic interpolation sampling membrane strains at hinge edge midpoints (***"Smoothed Hinge Model for Cloth Simulation - HKU DataHub"*** [70]), or mass-spring networks that resist locking (***"Learning Simulatable Models of Cloth with Spatially-varying Constitutive Properties - arXiv"*** [72, 73]).
    *   **Collision Tunneling:** Discrete Collision Detection (DCD) misses inter-frame intersections, manifesting as interpenetrations where fast-moving cloth passes through itself [70]. Mitigated by trajectory sweeping Continuous Collision Detection (CCD) (***"ClothTransformer: Unified Latent-Space Transformers for Scalable Cloth Simulation - arXiv"*** [70]) or stabilized cubic barriers [70].
    *   **Super-Elastic Stretching:** Implicit integration overshoots node positions over large timesteps, causing the cloth to act like a super-elastic sheet, stretching far beyond physical rest limits [70]. Mitigated by coupling integration with iterative constraint enforcement and edge spring corrections [70].
*   **Grounding Evaluation on Missing Taxonomy Elements:**
    *   According to ***"Physical and Perceptual Metrics of Fabric Realism in Computer Graphics and Materials Science"*** [74], the following failure modes and studies are **NOT IN SOURCES**:
        *   Specific visual failure modes labeled "uniform fold wavelength (resonator artifacts)".
        *   Specific visual failure modes labeled "tension without wrinkles".
        *   Any empirical, validated "ranking" of which of these numerical simulation failures (locking, zero-thickness, or tunneling) betrays the visual simulation to observers first [74].
    *   While individual engineering strategies exist to mitigate these failure cases, there are no studies in the sources that rank their perceptual impact on human realism thresholds [74].

***

📊 I can write a Python script using matplotlib to plot the estimated marginal means of stretchiness and thickness across different pictures from the RIT master's thesis to help you visualize these perceptual discrepancies. Let me know if you would like me to generate that plot!
