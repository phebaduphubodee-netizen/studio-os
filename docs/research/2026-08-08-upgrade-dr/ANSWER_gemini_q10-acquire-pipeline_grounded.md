# q10-acquire-pipeline (grounded pass)

- vendor: Gemini `gemini-2.5-pro` mode `pro` (google_search grounded)
- date: 2026-08-08
- prompt: `q10-acquire-pipeline.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. Asset Sources: Ranking, Quality, and Cleanup

Based on practitioner discussions and library offerings, the ranking of asset sources for a professional archviz studio is generally based on a trade-off between quality, integration, and cost.

1.  **Integrated/Curated Libraries (First Choice for Speed & Consistency):**
    *   **Chaos Cosmos:** [PRACTICE] Professionals using V-Ray, Corona, or Enscape reach for this first due to its deep integration. The assets are high-quality, curated, and render-ready, requiring no material setup or geometry optimization. The library is organized into categories like furniture, vegetation, and people, and assets automatically adjust their level of detail for viewport performance vs. render quality. It includes content from reputable creators like Globe Plants.
        *   **Geometry/Quality:** High-quality, consistent, and pre-optimized for the Chaos ecosystem. Scale is correct within the system.
        *   **Cleanup Needed:** None. The primary value is that assets are drag-and-drop ready.
    *   **Quixel Megascans (now part of Fab):** [PRACTICE] The industry standard for photorealistic, photoscanned assets, especially surfaces, plants, and environmental debris. Its integration via Quixel Bridge makes it a top choice for adding realism. The entire library is free for use with Unreal Engine, and by extension, Twinmotion.
        *   **Geometry/Quality:** Extremely high-quality photogrammetry scans with high-resolution PBR textures and multiple levels of detail (LODs). Each asset undergoes a detailed manual cleanup process by Quixel.
        *   **Cleanup Needed:** Generally none. Assets are ingested via Bridge and are ready to use.

2.  **High-End Paid Libraries (First Choice for "Hero" & Specialist Assets):**
    *   **Examples:** 3D Sky, Maxtree, Globe Plants, VIZPARK, Poliigon, Evermotion.
    *   [PRACTICE] These are marketplaces and specialized vendor libraries where studios purchase high-quality, specific models, particularly for hero furniture, detailed plants, and accessories. They are often the source for the most current and trend-focused interior design pieces.
        *   **Geometry/Quality:** Generally very high. Models are built for production with clean topology, proper UVs, and PBR materials. Quality can vary slightly by vendor, but reputable ones are reliable.
        *   **Cleanup Needed:** Minimal. A practitioner might replace materials with their own library shaders for absolute consistency, but the geometry is typically sound. Scale is usually correct.

3.  **Free, High-Quality Libraries (Go-to for General Purpose Assets):**
    *   **Poly Haven:** [PRACTICE] Highly regarded for its completely free (CC0 license) library of high-quality PBR textures, models, and HDRIs. It is a common source for supplementary assets.
        *   **Geometry/Quality:** Good quality, with clean topology and PBR textures. The library is curated, ensuring a consistent standard.
        *   **Cleanup Needed:** Little to none. Assets are designed to be ready for use.
    *   **BlenderKit:** [PRACTICE] An integrated library within Blender, offering a mix of free and paid assets. Its convenience makes it a frequent choice for Blender-based workflows.
        *   **Geometry/Quality:** Varies. The library is large and contains user-submitted content, so quality is not as consistent as a curated library like Cosmos or Quixel.
        *   **Cleanup Needed:** Varies by asset. May require material adjustments, scale checks, and minor geometry fixes.

4.  **Broad Marketplaces & Community Repositories (Used with Caution):**
    *   **Sketchfab / Fab:** [PRACTICE] Fab now integrates the Sketchfab marketplace, offering a massive, searchable library with a built-in 3D preview. It's an excellent source for finding specific or unusual objects.
        *   **Geometry/Quality:** Highly variable. Ranges from professional, production-ready models to low-quality user uploads. The user must vet each model.
        *   **Cleanup Needed:** Almost always requires cleanup. Common issues include incorrect scale, messy topology (n-gons, non-manifold geometry), poor UVs, and non-PBR materials.
    *   **3D Warehouse:** [PRACTICE] Primarily for SketchUp users, it's invaluable for concept and massing stages due to its vast library of manufacturer-specific and user-generated models.
        *   **Geometry/Quality:** Extremely variable. Manufacturer-certified models are generally accurate in scale and form but may have high polycounts or be optimized for CAD, not rendering. User-submitted models are often messy, with poor topology and no proper materials.
        *   **Cleanup Needed:** Significant cleanup is the norm. This includes removing unnecessary layers, rebuilding geometry, simplifying polycounts, and creating proper PBR materials from scratch.

5.  **Manufacturer BIM/3D Portals:**
    *   [PRACTICE] Used when a specific, real-world product must be represented accurately (e.g., a particular chair or faucet).
        *   **Geometry/Quality:** The model will be dimensionally accurate, but the geometry is often CAD-based (NURBS, solids) or a high-poly conversion, not optimized for rendering. Topology is frequently triangulated and messy.
        *   **Cleanup Needed:** Extensive. Models must be retopologized or heavily optimized, and materials must be built from scratch.

### 2. SCALE

[PRACTICE] The standard archviz workflow emphasizes the importance of maintaining consistent units from the beginning of a project. (Maxon, "What Is Architectural Visualization? A Complete Guide to Archviz", 2026).

The most common procedure for verifying scale is manual and comparative:
1.  **Import and Group:** The asset is imported into a clean scene.
2.  **Create a Reference:** A simple box primitive is created with known real-world dimensions (e.g., a 1.8m tall human reference, a 0.75m high table reference).
3.  **Compare and Scale:** The imported asset is visually compared to the reference object. If incorrect, it is scaled to match the expected real-world size, and this scale is "applied" or "frozen" to its geometry.

**Common Format Issues:**
*   [INFERENCE] Different software applications default to different units (e.g., inches, centimeters, meters). FBX and OBJ formats do not have a universally enforced unit system. An FBX exported from a program set to inches will import into a program set to meters at 1/2.54th of its intended size if the import/export settings are not managed correctly. glTF is specified to use meters as its standard unit, making it generally more reliable for scale.

**Automated Checks:**
*   NO SOURCED VALUE FOUND. There are no widely published, standard scripts or addons that automatically validate an asset's bounding box against its class (e.g., flag a "chair" that is 10m tall). This remains a manual verification step.

### 3. TOPOLOGY AND CLEANUP

[PRACTICE] For a downloaded model in a still render, the primary concerns are visual correctness and render performance, not animation-readiness. The standard cleanup sequence is:

1.  **Check Scale:** As above, this is the first step.
2.  **Isolate and Purge:** Remove any extraneous objects imported with the asset (cameras, lights, helper objects).
3.  **Review Geometry:**
    *   **N-gons:** While problematic for animation (deformation) and UV unwrapping, n-gons on a perfectly flat, static surface are often acceptable for a still render and do not need to be fixed if they are not causing visible shading artifacts. [INFERENCE]
    *   **Doubled Vertices/Edges:** These should be merged (`Merge by Distance` in Blender). They add to the vertex count for no reason and can cause shading errors. [INFERENCE]
    *   **Normals:** Flipped normals will render incorrectly (often black or transparent). Normals should be recalculated to point outwards. This is a critical step. [INFERENCE]
4.  **Shading:** Check for shading artifacts. Often, applying an "auto-smooth" setting or adding a "Weighted Normal" modifier can fix shading issues on hard-surface models without altering the geometry. [INFERENCE]
5.  **Material Replacement:** This is a key step. Even if an asset comes with materials, studios often replace them with their own curated, high-quality PBR materials to ensure consistency across the entire scene. [INFERENCE]
6.  **Decimation/Optimization:** If the polycount is excessively high (common with CAD or scanned models), a decimation modifier can be used to reduce it. For a still render, this is only necessary if the asset is significantly impacting viewport performance or memory usage.

**What Actually Matters for a Still Render (2-6m distance):**
*   **Correct Normals:** Absolutely critical for correct shading.
*   **Material Quality:** The single most important factor for realism.
*   **Scale:** Essential for the scene to be believable.
*   **Major Shading Artifacts:** Any visible errors must be fixed.

**What is Often "Cargo-Culted":**
*   **All-Quad Topology:** While essential for subdivision modeling and animation, it is not necessary for a static prop that will not be deformed. A mix of quads and triangles is perfectly acceptable.
*   **Perfect UVs:** If you are replacing the materials entirely with procedural shaders or using triplanar mapping, the asset's original UVs may not matter at all. They only become critical if you are applying a specific texture map that relies on them.

### 4. FORMAT

[PRACTICE] The consensus is that different formats serve different interchange purposes, and none is perfect for every round trip.

*   **glTF / GLB:** [PRACTICE] Increasingly preferred as the modern interchange target for delivering assets. It is an open standard designed for efficient transmission and rendering, often called the "JPEG of 3D". It robustly supports PBR materials (metallic-roughness workflow), which maintain high visual fidelity between different render engines.
    *   **What Breaks:** Can lose complex, non-standard shader node setups. Conversion from other formats can sometimes lose data if the features are not supported by the glTF spec.
*   **FBX:** [PRACTICE] The long-standing workhorse for moving assets between digital content creation (DCC) tools, especially in game and VFX pipelines. It is the most robust format for carrying complex scene data, including geometry, materials, animation, rigs, and cameras.
    *   **What Breaks:** It is a proprietary Autodesk format, which can lead to compatibility issues between different software versions or vendors. Material translation is often imperfect, especially between different renderers (e.g., V-Ray materials to Blender's Cycles).
*   **OBJ:** [PRACTICE] A simple, universal, and decades-old format. It is excellent for transferring static geometry.
    *   **What Breaks:** Animation data is not supported. Material support is very basic, relying on a companion `.mtl` file that does not support modern PBR workflows. Materials almost always need to be rebuilt from scratch.

For archviz props, which are typically static geometry with PBR materials, **glTF is emerging as the most reliable choice for preserving material intent**, while **FBX is the legacy standard for preserving the core geometry and UVs**.

### 5. AUTOMATION

*   **Poly Haven:** [MEASURED] Provides a free public API (api.polyhaven.com) that can be used for commercial purposes to access and download assets. They also offer a paid Blender Add-on ($49 once-off or via Patreon subscription) that integrates the library directly into the Blender Asset Browser for drag-and-drop use. The add-on itself uses the API. There are no stated rate limits or auth requirements for the public API, but they ask for attribution.
*   **BlenderKit:** NO SOURCED VALUE FOUND for a public-facing, documented API for third-party tool integration. Access is primarily through their official Blender add-on.
*   **Fab / Quixel:** [PRACTICE] Programmatic access is provided through the **Quixel Bridge** application, which acts as a desktop client and plugin for various DCC tools, including Blender. This allows for searching and direct import of assets into a scene. Direct API access for third-party development is not a publicly advertised feature.
*   **3D Warehouse:** NO SOURCED VALUE FOUND for a public API for programmatic search and download of models. Access is via the web interface.

### 6. LIBRARY DISCIPLINE

[PRACTICE] While no single, universal naming standard is published, professional practice and DAM (Digital Asset Management) software documentation point to a consistent set of principles for organizing asset libraries.

*   **Directory Structure:** [PRACTICE] Libraries are organized in a hierarchical folder structure, typically by category, then sub-category, then asset name. For example: `_3D_Assets/Furniture/Chairs/Manufacturer_ModelName_Variant.blend`.
*   **Naming Conventions:** [INFERENCE] Names are descriptive and consistent, often using fields separated by underscores or hyphens. A common pattern is `Category_ObjectName_Manufacturer_Details`. For example: `Chair_Armchair_HermanMiller_EamesLounge_Walnut`.
*   **Blender Asset Browser:** [PRACTICE] Blender's built-in Asset Browser is the primary tool for organizing assets within the Blender ecosystem. It uses a "Catalog" system, which functions like folders. Assets can be marked and assigned to specific catalogs (e.g., `Furniture > Seating > Chairs`) for easy filtering and drag-and-drop access.
*   **Tagging and Metadata:** [PRACTICE] More advanced systems use metadata tagging. An asset can have multiple tags (e.g., "chair", "wood", "mid-century", "lounge"). This allows for more flexible searching than a rigid folder structure. Some studios use dedicated DAM software like Connecter to manage this.

### 7. THE HONEST TEST

NO SOURCED VALUE FOUND for a formal, published, quantitative comparison (e.g., a peer-reviewed paper or a large-scale studio survey) of time cost vs. quality for hand-modeled vs. acquired assets.

However, there is a strong and consistent [PRACTICE] consensus reported in articles aimed at professionals:

*   **The Hybrid Approach:** [PRACTICE] The most effective workflow is a hybrid one. Studios model "hero" assets from scratch and acquire everything else.
*   **Model it Yourself When:**
    1.  The asset is a unique, central piece that defines the project's identity (e.g., a bespoke architectural feature, a signature piece of furniture that is the focus of the shot).
    2.  The asset has a very specific client brief (e.g., exact dimensions, branding) that cannot be met by any existing model.
*   **Acquire it When:**
    1.  The asset is part of the "entourage" or set dressing—it fills the world but does not define it (e.g., background chairs, books, plants, cutlery).
    2.  The asset is complex and time-consuming to create to a high standard (e.g., realistic plants, scanned food, detailed electronics). [INFERENCE]

[PRACTICE] The economic argument is that the cost of a subscription to a high-quality library is significantly less than the billable hours required to model even a few high-quality assets from scratch.

### 8. Plants and Greenery

[PRACTICE] This is a class of asset that professionals almost always acquire from specialized sources due to the difficulty of achieving realism.

*   **Sources Used:**
    *   **Specialized Scanned Libraries:** These are the top choice for photorealism. Commonly cited vendors include **Maxtree**, **Globe Plants**, **VIZPARK**, and **Poliigon**. Many of these assets are now integrated into broader libraries like Chaos Cosmos.
    *   **Generators/Scattering Tools:** For landscapes or scenes with dense foliage, plugins like **Forest Pack** (for 3ds Max) or Blender equivalents like **Graswald**, **Botaniq**, or **The Grove** are used. These tools provide not only the plant models but also powerful systems for distributing, randomizing, and optimizing vast numbers of instances.
*   **Polycount and Instancing Guidance:**
    *   NO SOURCED VALUE FOUND for a specific, published numerical guideline (e.g., "an interior plant should be between X and Y polygons").
    *   [PRACTICE] The guidance is procedural rather than numerical:
        1.  **Use Instances:** Always use instancing (or "linked duplicates" in Blender) for any plant that appears more than once. This allows the renderer to load the geometry into memory only once, drastically reducing memory consumption.
        2.  **Use Proxies/LODs:** For heavy scenes, use low-poly viewport proxies that are automatically swapped for the high-poly render-time version by the render engine. Integrated libraries like Chaos Cosmos do this automatically.
        3.  **Distance Matters:** Use lower-poly models for plants that are far from the camera and reserve high-poly, detailed models for foreground elements. [INFERENCE]

## CONFLICTS AND UNCERTAINTY

*   **Quality of 3D Warehouse:** Sources are in agreement that the quality is highly variable, but they differ in emphasis. Some dismiss it as only useful for massing models, while others highlight the growing collection of over 700,000 certified manufacturer models that are accurate and ready for professional workflows. The builder should assume that any asset from this source requires careful vetting.
*   **"Best" Interchange Format:** There is no single "best" format, only the best for a specific task. While this isn't a direct conflict, the choice of FBX vs. glTF depends entirely on whether the priority is preserving complex scene data for interchange between authoring tools (FBX) or delivering a standardized, PBR-correct asset to a final platform (glTF).

## WHAT I COULD NOT SOURCE

*   **Automated Scale-Checking Tools:** I could not find any published, named script, addon, or tool that automatically validates the bounding box of an imported asset against its semantic class (e.g., a "chair validator").
*   **Programmatic Access for BlenderKit and 3D Warehouse:** I could not find documentation for a public-facing API for third-party developers for either BlenderKit or 3D Warehouse.
*   **Published Naming Conventions:** While I found descriptions of common-sense practices for organizing libraries, I could not find a formal, published naming standard from a specific studio or standards body (e.g., an "Archviz Naming Standard v2.0").
*   **Quantitative "Honest Test":** I could not find a published study that quantitatively compares hand-modeling vs. acquisition with metrics for time, cost, and final image quality. The current guidance is based on professional consensus and anecdotal evidence.
*   **Specific Polycount for Interior Plants:** I could not find a published, measurable guideline (e.g., a polygon range) for what constitutes an acceptable polycount for a high-quality interior plant in a still render. The guidance is qualitative (use high-poly for foreground, low-poly for background).
---

## GROUNDING (vendor-reported)

- search queries issued: 31
  - `archviz asset sources ranking professional`
  - `3d warehouse archviz quality`
  - `poly haven archviz quality`
  - `blenderkit archviz quality`
  - `quixel megascans archviz quality`
  - `chaos cosmos archviz quality`
  - `paid 3d model libraries for archviz`
  - `manufacturer 3d models for archviz quality`
  - `archviz asset cleanup process`
  - `archviz asset scale verification`
  - `blender import scale issues fbx obj skp gltf usd`
  - `automated 3d model scale validation tool`
  - `blender 3d model cleanup addon`
  - `archviz still render optimization topology`
  - `best 3d interchange format for archviz props`
  - `fbx vs obj vs gltf vs usd for archviz materials`
  - `poly haven api blender`
  - `blenderkit api`
  - `quixel bridge blender programmatic access`
  - `sketchfab api blender`
  - `3d warehouse api terms of service`
  - `archviz asset library organization`
  - `blender asset browser naming conventions`
  - `published archviz pipeline standards`
  - `hand-modelled vs scanned assets archviz comparison`
  - `when to model vs buy 3d assets archviz`
  - `what 3d assets do archviz professionals model by hand`
  - `archviz plant and greenery sources`
  - `best 3d plant models for archviz`
  - `graswald vs botaniq vs the grove blender`
  - `archviz interior plant polycount guidance`

- grounding chunks: 32
  - storekonia.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE2nxTkDspHzs09VnsLV7E-io7KW8qwSLHsiTSQIcwWMpnekevslNupsq32rB0M2PSubftyD-OYYYoZMeA2RfZPhBILWqwhrWpTKnpPWCW-jSU4xjQQ5xvyAi2dczD9APEwZr-KrOHbpwvjb3kKwHfn
  - chaos.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHjnOFJx1GQedyPvWlleuESHybZ6PHzWcEhNFqn_Vaj9HDBtqL0M_L0E5fKYYlWJRJdt1JJpGCzwaVeC22T4tRmfGW_LQ0fsh1L4VKr3g5pGWkZsTlsjAA=
  - chaos.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEB8DOPY_IM2RTHooPWEUOZIC9rN18a7uxbqPxLTI2d1QPmdGBGSDWh7IAem29jlo_poRN0hnik-bHlC3tZ4rHh9uy7TzntYUd-MkiTzCD_5UyqwLDT6ZO816j0Y4jsjsEopSnlFPWAp_YwUwXnImxPAC-c1aa3XjW09vcBLsnREpIUnWCCNW6ZMWQXYFl_dyVSN-KMyCraM1nwkl2CHdrZUds=
  - twinmotion.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFFImq_aJYMrJpcQhYEciEHzAUXC9p0axW7o4Oa6B9i9t1U10QhNiEg3n9qjt0Sc1mOr06yRMapzIPVGEi9k7y2tmwTNw97MZzHn_6vQ23y_v1XMstBbydEDduBp5ulruIhthTFeYWDDiFIyQ2V0i0rq_ITZU4pH5ohi8rYPwubXHtAun1xxPCf31T-g39r8A==
  - archdaily.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEbJtWhVGwQHPKY7HxxqYAfFjDtKMwdPy14v1d4bnqfOc7UiRnC1CIHfDObPR6dohX2jS79Hb0u0NV5WnWF1V4tDnPzAhw5Wdu-HjjC125MSTyYWZkcQm2zcaTtjXLKyJtscve13sdE6CoxDBfmr7sqqZiPErqwnffygFP9ifcRML5sWhoJKyUoRBdTwFS8FptTJAUrohtpjJhGJ24=
  - archvizartist.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHA1geX10c2BuAofttF10Jc0pu6XmRcqjyzR5U1Hg2LTJmrOo_5LLRMFazsPuQdJCWgkxsUGhETF9m_6yiorTW9qxZG-sE1l5MfFo-EuML7GMgLPISfMXlnytAZBFcZYMumTLCmYSFYhDy6IXlPy0MyLMSV9WW54GVR8hRt1fjbhnbphAzEhaZAHIoSZd25
  - ronenbekerman.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGggON2j8t6lOmqc9Hsqox4LJfMsUNAIb414a0PBi3BEnM5geAORNUbdmmOoG_M6ka9liFOFkIy115fVg76LBsVA3DaiIxsEx3PpXv9lsWbb7A9kiNZDhI869n-1JbtOOq6nvS0Le25aIykgsdxOJ1sgjj6AzbtjlbcxgOAlilEYEZmZn8GSW3G5G-4
  - archviz.supply — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGnMjxuTSmDY_qFnFY7KiqvxyqgsE_ZMVRoL8JINrGZQ50SL_DRjP_csEC7fsKHpQwKlLu6Elc2VpOxeYUccvfduCvnqSrwNItWgQllEPAC_5IOnPb9oQ==
  - reddit.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFgKLQXg4JZNw8KTTtLpCRHGnSvs-qg82X0YT5r8nVHmuXotct3yysgmq-Gb5goODv-pEHoOlRDdykhW0qVZVhwkyvQg15Oh_Ao8vN3YNolSGIj2niQDIVPRB-wQrW6xO3GettV_j4JsF3ojwjYHhXS_iaxWbeydLyBx2T9GuyGYbVNm0aBZ-sMmO5dmVlcIKM=
  - 3dcollective.es — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzB_XxOX_jxXiDly5NIqMSQMOyGfot2A82irJdXqgnM-WeDbLnOt66EjMP5SwRp_KthV_J17h2-_v75w8_f4VpF5mlLoa9Sa9RojI6VRkfiZq82Jug5Q-vBJKbqYHHzJ0=
  - vizpark.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFPtARoCoHAhBpfu5ZvcbknGdRIocA5nnB0dUCOg7LI1CMU6wzr-u1RAdTrlQNyRu1W3gFPQ1rc1s9I6dYXZdMeTcPBRrkzH4T6ZYULfs89ajUzgi3g6R5eO1DZOkYTd-doPqI=
  - globeplants.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGDHMv4HavfA5nvoH_8vLUjGkjPrmv2YnOJP6aoz3j7y5Du1ASNihjx0PssmHN6mlfiE-HhFRS634SdAwViLOjNcUy3TgR1zBCsH710lhLbsMdlsA==
  - maverickframe.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEXvP3egBElj4zR46LMfY_cqABP9BLe8aBlEjkAHsufmVVFkuW0uVddMDIITfZJSUpkAN26IQkbUDrHCHBMdtc9SLj9i6b5KwXsn-3hRNRPYVBakNbQPDEcY6MJjl22Ve2sUSry2pEO2iC3rATOmFgx9kK2W-ZEQZfC2DhikAg=
  - chasingillusions.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGdNrwcNyWyTt-ip-_NaH2GSlNldGMxxRtvPRaqnaNZGj6fhnsDl3C_BFF0qFfoR6cg5qd9fLtXkSU1uPwMnpwt_hbuf9PxHRKFtJjFd7kL81FH7XC1dwsWMcKB7KUsOPLdfonnokRD1NikemlhI2eIcpMaw0AVfMOTdll-7amViTMm9AmLNQ==
  - worldteams.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8ABk4-n7dDrwUJW1sp0TgiZj1_OBrjh762a49WKXkmyaf18YV4sYpeTGHRFCwu1RF5ct8nVSQazqbJ_9PJNhuMM7QquDd8SuNFdAKKmfp_3isDlWGnhrHr67umyBnHK8NNA_1i9C39xksPZykPf3NbNOjlwq_umlJ8fLbTEQN9MuNk5e4odfkAZZmuw==
  - design8.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGuDffjfYbMV5-Alb8HFZVi5jlRH8g-6sip_afs2-rkATY5VJTzW0JnIOd9B0wUJFZ5acO-90wdik1R3F7hU6ox8awn4qADxiRfEiqUxbmaTcaTvYX-1EqRmLW4Hmsl7y8I08DER7xEJ9xVPVof6PoNnrA0MhgimG3cMrYgKbZ_dt_dwUY6JwS2eBJLWMtFromVtmsd4aZ6e4LAA1ysX10A-1A=
  - superrendersfarm.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHKvVQFPbE-IBvHq0OXBZHAgiJJ8MxFnbe2djsFiMHli4z6h_lGob5_EhPRV1Sl6H9FQxyLAyDae00E8wRcX0-pvJVAv3D5X8aU7HZWMZxXXMDiN5ESizNbphQr1q0t9ar7KYrEgn9Fnp22SZBO3wHpOeAEWFO_ccY51w0MsqF4I2touVNVu_u5A1M=
  - maxon.net — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHyyR7-kiGwdr34wNiWM4cfd3b36kFY48-2ItTBCQFj4oIkJTSVKZ2p0htFZ0rcLjYzVfc-sBnr8jXd9nVvLmOtk1ftlnZuyXWi0t4JiMv23Is_CNLJqmOgtv3igKV8Vv39Gr5ZZGNm4CEl9fAOxnRrlb_swED0Lat6TRvy2Q==
  - photolibsoftware.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGLLcMvizEq8RqvIOw65u1c8_br7HPfVxYXQcEW76SAfvl_ccRdmyE46vvDIrsZpRidxNeaUOow_BuKAzXLvCOehxVqK2ldep5kH3IEbJHO-LlTW9fNDzbREa6IzYbF8ro4G8bleTCfFGcgEOMrkHTYPiA6CL88RTIW
  - alpha3d.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyEAUwNCMHhbBk_avRyK7GFSRfmSrS7NBJQvggHLd2ttV2wU6dXD1xrHpj4jIYFE30OlXn6tGRq7BYIhKSpy-BIBNEnlpQOMic09HTTWrnV7foGFRoe3mTE5d6e27mgRJDISLx0F96B24WlbI_xw==
  - threedium.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFLEvHuwJMBT5RDDHvkYUgpxyQYy3Zt-v0MzTU_fjo13KIHnLm_fU8-0I_IVS7UhUB7kZzq-DCKswFA4uNVLajENdwCYDetZ5RA2cvSo_RVIeq3QlXt7ukWgf0yI31nxeVniWxRrw==
  - adobe.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZyAQRZ07OtVZm_KL_oMzi8aS5vV5Gb27VLdhRP-ik29jnyCOXA7rgpH-ZC8N_qe81XRLYRWco0WtaWMmOXmd1Xy28bwu-8pYfqb0PmcgAj2f9aGVf1AAEarVWK3awQh9XAGzz12Lf6TNdAG3qGpij0yfyHIO3d7le7PQ3YzQswC33HIU=
  - reddit.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEaHsmuwcJ0ZPolORwyFA02IEFk1RSo6M5M25AzFtLI3m0a46ZBUk0p-Ccpg3t2hImbDEabp768F5Drhvu94dZLoreGnFzUGT3GwJqDwAOXvJ84jSaQWXIstNKyoUz44g22bDpVTy2AuaArmQ5_9LzbgmEAM0eJHb00gUppG5BvK1pBS1q3ZIWZgWTCLEag9HAoChmHHqtcW9h6TjXQ
  - polyhaven.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH9t8HgvVlSRi7OWdNySyR09BkWcJsATGSZdnMr3-zYR5Gpxy1z6ZYyL8AcIPKCxjI7pN07MQHGqIsngpjaVIkClCtXlKAU4S0xZRYrLKKE0KJ3mNGcsoHZ
  - polyhaven.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH_TbFaJfCcD7_zehRpiQJFOJvcquNNVryhgdtTDFbuph_IEqVSGvnZBCNi-fLFwk0tInHGQLKjVMwEp6nI265YTiwwdEE7TZwz1NEfw8oJ5Gh37hcMDJpcQWHwTUN7bW8=
  - connecterapp.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHVal6zkpSRc1pzLN4jUck5STElxSsLk0x6m9f3VbFCbujHAgvI_dpWwDUtrVDJBWjggGu-JDLUoJjJJ8rPFE6OcaFu0VB4vQ2lu7E5MP-SY-I01dAp_reP6mYaX68DtObWqqJVBi0yerQwDtPxtKYLcTVakvG1V8PfyfXFoXETPA-pluksEQ4U5cUOFGg=
  - cgarchitect.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEW8Il5WrtlBjDOqp17P_PTas4GTNqgp96swJdsrcRj-IOck5rY6sMDhmQqG1SIumAIMPk9TS8GA7SXmthCWiTTVAOxdlUibsMy6IEEJDhyfwUlPMozpuI__AHjxqtHRxeubnQ8W-4pfyOO_crMNq2-isffj-q9_QCny-yKQw7MgZ9lhCiVvFwUsQ-2KJvVNI6ZUQ==
  - syr.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFMCAKAoa_pYBRGzSmlQbuUOkqgBFC4G7dKjFdAjb3lYq8e1rC2MagDgw1GGucqMCMMyirO0MB3CqhlnUwyrrfrxOjHWbv8BFztszV7HHKzAlG1JjXdhra_gONidgM27Tdls9Gzn6fzNzC76zj0uzAyM1enWpC_zyvqt5Su7A==
  - chaos.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGgtVyugYXEk--PiXkqzuWxCkqxm4yDFqTI26TxWZ3kocJdYxPoMjFy3mho2WibbEr3x29aPJAiGz9YV7LEsDHLZjDhpUW07aQOgrqzxtXJuqDDEadSwMAOlmiDWwyJPiWoxMBlbSfw-iID_0QS9Q==
  - korvix3d.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE1PHtApv9oeTNwxDv7rqKH_qiC177L3dnV3iIhAXDg7G2i7qPTdQgQTtPgfOq9djXnCz2zRJIXDoFs9VnehwdUg4HRZ9cHKVyK3lkiPhZJyKDIrVTyQ1CgYRhcaJkRceqbMjfkWRqoIkN8w9aD5acbNPJ3jBUAicPrL6meVTI=
  - poliigon.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFSl3quwPjt1wojTCY7St5LuWfVjjoozZHjbnp1chg_LXvuVqaRNqPXzUt4h9gLlRr5YMsn0jezc4LG0g1CTv8N284u7C-_FBmuT4FzEY4krr_GZk9H0ySwpUr3GRx9VmQ_QGVI8w==
  - reddit.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHH3T4b5iekj4to-pz1g9ymidRZZQoqaYi21X3Ij2HlOjUNE2PY0S0tQPIIrwijjkCrQ3oahpoO5PFx68yvR4pHX0PwzDE6Zz3EtWKfHmQQtQrBQFQ_PQgPKHPHOGrphKjO7ou5tpqt7Zo1a5ohGUay6WGuIbLd7Eppni9QoTNtKn3XJCp0R7WElsYqXQcz1-FV81_ORup2RmKiQ7Q=
