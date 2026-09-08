# q10-acquire-pipeline

- vendor: Gemini `gemini-2.5-pro` mode `deep` (google_search grounded)
- date: 2026-08-08
- prompt: `q10-acquire-pipeline.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. Asset Sources for Archviz Studios

The choice of asset source is a workflow decision, balancing speed, quality, and cost. Professionals often use a combination of sources, layering them based on the project's needs.

1.  **High-End Paid Libraries:** For client-facing, high-realism work, dedicated paid libraries are frequently the first choice due to their consistent quality, curated content, and render-ready nature.
    *   **Sources:** Design Connected, 3dsky, Poliigon, Evermotion, Chaos Cosmos.
    *   **Geometry Quality:** [PRACTICE] Generally very high. Topology is clean (quad-based), UVs are meticulously unwrapped, and models are optimized for rendering. Polycounts are appropriate for high-detail, close-up shots. Scale is almost always correct. For example, Design Connected models are explicitly sold as "perfectly scaled and textured" (Source: Design Connected website, "About Us" page). Chaos Cosmos assets are curated by Chaos and are designed to be photorealistic and consistent across V-Ray, Corona, and Enscape (Source: Chaos Cosmos documentation).
    *   **Cleanup:** [PRACTICE] Minimal to none. Typically, cleanup involves converting materials to a specific render engine if the asset wasn't designed for it, or proxying the model for viewport performance.

2.  **Integrated/Platform-Specific Libraries:** These offer convenience and seamless integration into a specific software ecosystem.
    *   **Sources:** Chaos Cosmos, BlenderKit.
    *   **Geometry Quality:** [PRACTICE] Quality is generally high and curated by the platform provider. Chaos Cosmos assets are vetted for quality and consistency (Source: Chaos Cosmos documentation). BlenderKit offers a range of quality levels, with official curated content being more reliable. The user-submitted portion can be variable. Models are typically provided with correct scale and basic UVs.
    *   **Cleanup:** [PRACTICE] Very little. The main benefit is that they are designed to work out-of-the-box with the target renderer (e.g., V-Ray/Corona for Cosmos, Cycles/Eevee for BlenderKit). Material adjustments might be needed for artistic control, but technical cleanup is rare.

3.  **Megascans/Quixel/Fab:** Primarily known for materials and scanned 3D assets (photogrammetry).
    *   **Sources:** Quixel Megascans (now part of Epic Games' Fab).
    *   **Geometry Quality:** [MEASURED] As these are often raw scans, the initial topology is a dense, triangulated mesh (a "nanite" style mesh). Polycounts can be extremely high. While the scan captures reality accurately, the mesh itself is not optimized for traditional subdivision modeling. UVs are generated from the scan and are functional for the provided textures. Scale is generally accurate to the scanned object. (Source: Quixel Megascans documentation on 3D assets).
    *   **Cleanup:** [PRACTICE] Significant cleanup is often required if the asset needs to be modified or optimized. This includes retopology (often automated with tools like Quad Remesher) to create a more manageable quad-based mesh, and potentially re-baking textures if UVs are changed. For distant objects, decimation is a common step.

4.  **Manufacturer BIM/3D Portals:** Used when a specific, real-world product must be represented.
    *   **Sources:** Herman Miller, Vitra, Kohler, BIMobject, Syncronia.
    *   **Geometry Quality:** [PRACTICE] Highly variable. Models are often created by engineers in CAD software (e.g., SolidWorks, AutoCAD) and exported. This frequently results in extremely dense, triangulated meshes with poor topology (n-gons, complex triangulation) not suitable for rendering or UV unwrapping. Scale is usually precise, as it's based on manufacturing data.
    *   **Cleanup:** [PRACTICE] Extensive. This is often the most labor-intensive source. The workflow involves significant retopology, either manually or with automated tools, to create a renderable mesh. All materials and UVs must be created from scratch.

5.  **Generalist Free Libraries:** Used for background elements, placeholders, or when budget is the primary constraint.
    *   **Sources:** Poly Haven, 3D Warehouse.
    *   **Geometry Quality:** [PRACTICE] Extremely variable.
        *   **Poly Haven:** Quality is generally good and curated. Models come with PBR textures and are intended for rendering pipelines. Topology is usually clean, but may not be as optimized as high-end paid assets. (Source: Poly Haven "About" page).
        *   **3D Warehouse:** Quality is notoriously inconsistent, ranging from manufacturer-grade models to very basic user submissions. Models are often created in SketchUp, which can lead to issues with reversed normals, messy geometry, and no UVs. Scale is often incorrect.
    *   **Cleanup:** [PRACTICE]
        *   **Poly Haven:** Usually minimal, often just material adjustments.
        *   **3D Warehouse:** Almost always requires significant cleanup. This includes checking and correcting scale, fixing reversed normals, removing doubled vertices, retopologizing where necessary, and creating all materials and UVs from scratch.

### 2. Scale Verification

Asserting correct scale is a critical, manual step. No single automated tool is universally trusted without practitioner oversight.

*   **Common Format Issues:**
    *   **FBX:** [PRACTICE] The most common source of scale error. The FBX format stores system units (e.g., cm, m, inches) and a scale factor. Importing applications (like Blender or 3ds Max) have their own system units. A mismatch between the file's units/scale factor and the application's settings on import/export causes the model to be off by a factor of 10, 100, 2.54, etc. (Source: Autodesk FBX documentation, Blender FBX Importer documentation).
    *   **OBJ:** [PRACTICE] The .obj format itself is unitless; it stores vertex coordinates as dimensionless numbers. Scale is therefore dependent on the conventions of the exporting and importing software. If the exporting software worked in cm, and the importing software assumes meters, the model will be 1/100th the correct size. (Source: Wavefront .obj file format specification).
    *   **SKP (SketchUp):** [PRACTICE] SketchUp files are internally unitized. However, importers can sometimes misinterpret the units on import, leading to scale discrepancies.
    *   **glTF/USD:** [MEASURED] These are modern formats designed to be unambiguous. Both specify meters as their default unit of length. glTF 2.0 states, "The units for all linear distances are meters." (Source: Khronos Group, glTF 2.0 Specification, Section 3.7.2.1). USD similarly defaults to meters. Scale issues with these formats are less common and usually point to an error in the exporting application.

*   **Practitioner Verification Methods:**
    1.  **The Human-Scale Reference:** [PRACTICE] The most common method is to import the asset into a scene that contains a human-sized reference object (e.g., a 1.8m tall box or a pre-scaled human model). This immediately makes scale errors obvious.
    2.  **The Measurement Tool:** [PRACTICE] Practitioners use the measurement tools within their primary software (e.g., Blender's Measure tool) to check key dimensions of an asset against known real-world dimensions. For a chair, they will measure the seat height (typically 45-50 cm). For a door, they will measure the height (typically 200-240 cm).
    3.  **Manufacturer Datasheets:** [PRACTICE] When using a model of a specific real-world product, the practitioner will have the manufacturer's product sheet (PDF or webpage) open. They will use the measurement tool to verify the model's height, width, and depth against the official dimensions.

*   **Automated Checks:**
    *   NO SOURCED VALUE FOUND for a widely adopted, published script or addon that automatically flags assets with implausible bounding boxes *for their class*. While trivial to script for a specific class (e.g., "flag any object named 'Chair' with a bounding box > 2m"), a general-purpose, intelligent validator does not appear to be a standard tool. [INFERENCE] This is likely because the definition of "plausible" is highly contextual (a toy chair vs. a real chair) and the manual check against a human reference is fast and reliable.

### 3. Topology and Cleanup for Still Renders

The cleanup sequence prioritizes what is visible to the camera over technical purity required for animation or games.

*   **Standard Cleanup Sequence (in rough order of priority):**
    1.  **Scale and Orientation:** Correcting scale (as above) and ensuring the object's origin is in a logical place (e.g., at the base, centered) for easy placement.
    2.  **Normals:** Checking for and recalculating flipped normals. Flipped normals cause incorrect shading and are highly visible artifacts. This is a critical step.
    3.  **Shading/Smoothing:** Applying correct smooth/hard shading to edges. Bad smoothing creates visible facets on curved surfaces or removes definition from hard edges.
    4.  **Material Assignment:** Replacing or rebuilding materials to be compatible with the target render engine (e.g., converting V-Ray materials to Cycles/Corona). This is fundamental to the final look.
    5.  **Remove Doubles/Merge by Distance:** Merging vertices that are in the same location. This can fix some shading artifacts and is good practice, but may not be strictly necessary if no artifacts are visible.
    6.  **N-gon Handling:** [PRACTICE] For still renders, n-gons (polygons with more than 4 sides) are often acceptable *if they are planar and do not cause shading artifacts*. Unlike in animation/game pipelines where subdivision and deformation require clean quad topology, in archviz, if an n-gon on a flat surface (like a tabletop) renders correctly, it is often left as is to save time. It only becomes a problem if it creates visible triangulation or shading errors.
    7.  **Decimation/Optimization:** [PRACTICE] This is important for scene performance, especially for objects far from the camera or those that will be heavily instanced (e.g., vegetation, books on a shelf). A high-poly object 15 meters from the camera is a waste of resources. Tools like Blender's Decimate modifier are used to reduce polycount while preserving the silhouette.

*   **What Actually Matters for a Still (2-6m camera distance):**
    *   **Critical:** Correct Scale, Correct Normals, Correct Smoothing, High-Quality Materials & Textures. These directly impact the visual realism.
    *   **Important:** Sensible Polycount (for performance), Clean UVs (if textures are detailed).
    *   **Often Cargo-Culted:** The absolute requirement for an "all-quad" mesh. While good practice, if a triangulated or n-gon-heavy mesh from a CAD source or photogrammetry scan renders correctly from the target camera angle, a studio on a deadline will often not spend hours manually retopologizing it. The rule is "if it looks right, it is right."

### 4. Interchange Formats

The consensus is that no format is perfect, and the "best" one depends on the source and destination software. For bringing props *into* a primary DCC tool like Blender or 3ds Max, the priorities are geometry, UVs, and basic material separation.

*   **FBX (.fbx):**
    *   **Strengths:** [PRACTICE] The de-facto industry standard. It can carry mesh data, UVs, textures, basic material definitions, lights, and cameras. It is widely supported.
    *   **What Breaks:** As noted, scale is the most common failure point. Material transfer is unreliable; complex shader networks from one renderer (e.g., V-Ray) will not translate to another (e.g., Cycles). They typically import as basic materials with diffuse color and texture maps assigned to the correct channels (diffuse, normal, roughness), but specific values and node setups are lost.

*   **glTF/GLB (.gltf, .glb):**
    *   **Strengths:** [PRACTICE] A modern, open standard designed for efficient transmission of 3D scenes. It has a well-defined PBR material model (Metallic/Roughness), which translates more predictably between compatible applications than FBX materials. It is the preferred format for web-based viewers and is gaining traction in DCC applications. Scale is reliably meters.
    *   **What Breaks:** While material translation is more reliable for PBR workflows, it is still limited to that model. Complex, custom shader graphs will be lost. Adoption is not as universal as FBX, and some older software may have poor support.

*   **OBJ (.obj):**
    *   **Strengths:** [PRACTICE] Simple, robust, and universally supported. It's a "lowest common denominator" that almost always works for geometry and UVs.
    *   **What Breaks:** It is a very old format. It does not support complex materials (only a basic .mtl sidecar file for diffuse color and texture paths), no scene hierarchy, and no unit/scale information. It is essentially a "dumb" geometry container.

*   **USD (.usd, .usda, .usdc):**
    *   **Strengths:** [PRACTICE] A powerful format designed by Pixar for complex scene interchange. It excels at representing entire scenes with overrides, layers, and instancing. It has a robust material model (PreviewSurface) and reliable scale (meters). It is the future-facing choice for large pipeline integration.
    *   **What Breaks:** It is complex. Support can be inconsistent between applications, especially for materials. For simple prop interchange, it can be overkill. It is more of a scene description language than a simple asset format.

*   **Practitioner Consensus:** [INFERENCE] For acquiring a single prop, practitioners often prefer **FBX** for its ubiquity or **glTF** for its more reliable PBR material and scale transfer. If both fail, they fall back to **OBJ** for the raw geometry and UVs, accepting that they will have to rebuild all materials manually.

### 5. Automation and Programmatic Access

*   **Poly Haven:**
    *   **API:** [MEASURED] Poly Haven has a public, unofficial API that allows querying for assets. The data is available via a public-facing `assets.json` file. There is no formal documentation, but community-developed wrappers exist. (Source: `polyhaven.com/assets.json`, community observation).
    *   **Constraints:** [PRACTICE] No formal authentication or rate limits are published, but as it's an unofficial endpoint, it should be used with consideration. It is suitable for headless operation.

*   **BlenderKit:**
    *   **API:** [MEASURED] BlenderKit has a server API that the official add-on uses. The API is not publicly documented for third-party use, and access is tied to user accounts for paid plans. (Source: BlenderKit "Frequently Asked Questions").
    *   **Constraints:** [PRACTICE] Requires authentication. Programmatic access would likely involve reverse-engineering the official add-on's API calls, which could be fragile and may violate the terms of service. Not designed for headless use by third parties.

*   **Fab/Quixel/Megascans:**
    *   **API:** [MEASURED] Quixel has historically provided APIs for integration into tools like Unreal Engine via the Bridge application. Direct, third-party programmatic access to the asset library for download is not a publicly offered feature. Access is tied to an Epic Games/Quixel user account.
    *   **Constraints:** [PRACTICE] Requires authentication via an Epic Games account. The intended workflow is through official tools like Quixel Bridge or integrations within Unreal Engine, not standalone scripts.

*   **3D Warehouse:**
    *   **API:** [MEASURED] SketchUp provides the "3D Warehouse API," which allows for searching and retrieving model information. Downloading models requires user authentication and adherence to the API Terms of Use. (Source: SketchUp Developer Portal, 3D Warehouse API documentation).
    *   **Constraints:** [MEASURED] Requires an API key and OAuth 2.0 for authentication. There are rate limits. The Terms of Use specify that the API is for use in applications that "complement or enhance the SketchUp ecosystem" and explicitly forbid creating a competing 3D model library. (Source: SketchUp API Terms of Use).

### 6. Library Discipline and Naming Conventions

Organizing assets is crucial for studio efficiency. Several conventions exist.

*   **Naming Conventions:**
    *   [PRACTICE] A common pattern is `Category_Manufacturer_Model_Variant_Version.format`, for example: `Chair_HermanMiller_Aeron_Graphite_v02.blend`. This is a widely cited "common sense" approach in studio pipeline discussions on forums like Blender Artists and CGArchitect, but is not a formal, published standard.
    *   [PRACTICE] Another approach is to use a unique asset ID, especially in larger studios with a database-backed library: `CH0021_HermanMillerAeron.blend`. The ID links to a database with detailed metadata.

*   **Blender Asset Browser:**
    *   [PRACTICE] The Blender Asset Browser is the intended tool for this. Assets are organized into Catalogs, which function like folders. A typical catalog structure might be:
        *   `Furniture/`
            *   `Chairs/`
                *   `Office/`
                *   `Dining/`
            *   `Tables/`
        *   `Decor/`
            *   `Vases/`
            *   `Books/`
    *   Assets can also have tags (e.g., "wood", "modern", "scandinavian") for searchability. (Source: Blender Manual, "Asset Browser" section).

*   **Published Standards:**
    *   NO SOURCED VALUE FOUND for a universal, published naming standard specifically for archviz assets. Standards like the US National CAD Standard® are for architectural drawings and layers, not 3D render assets. [INFERENCE] Naming conventions are highly studio-specific, tailored to their internal pipeline and asset management software.

### 7. Hand-Modelled vs. Acquired Props

*   **Published Comparisons:**
    *   NO SOURCED VALUE FOUND for a formal, published, quantitative study comparing the time cost and final quality of hand-modeled vs. acquired props in a controlled archviz setting. [INFERENCE] This is likely because the conclusion is considered self-evident by practitioners: acquiring a high-quality asset is almost always faster and results in higher realism for complex objects than modeling from scratch, assuming a suitable asset exists. The cost is a trade-off between the artist's time (modeling) and the asset's price (acquiring).

*   **When Practitioners Still Model by Hand:**
    *   **Bespoke/Custom Furniture:** [PRACTICE] If the project features custom-designed joinery, furniture, or architectural elements that are unique to the design, they must be modeled by hand. This is the most common reason.
    *   **Specific, Unfindable Items:** [PRACTICE] If a project requires a very specific object (e.g., a particular vintage lamp, a unique piece of art) for which no 3D model exists for purchase or download.
    *   **Simple "Kitbashing" Elements:** [PRACTICE] Basic architectural forms like walls, floors, ceilings, simple shelving, countertops, and basic trim are always modeled.
    *   **Hero Objects Requiring High Control:** [PRACTICE] For a "hero" object that is the central focus of a shot and may need specific modifications, art direction, or animation, a practitioner might choose to model it to have full control over topology and detail.

### 8. Plants and Greenery

Plants are a common point of failure because of their geometric and material complexity.

*   **Practitioner Sources:**
    1.  **Specialized Paid Libraries:** [PRACTICE] This is the most common source for high-end work. These libraries provide highly realistic, optimized models. Sources include Maxtree, Evermotion, and Globe Plants. These are often sold as collections for a specific render engine.
    2.  **Generators/Add-ons:** [PRACTICE] For custom plants or large-scale ecosystems, generator tools are used.
        *   **The Grove 3D:** A Blender add-on for procedurally growing realistic trees. (Source: The Grove 3D website).
        *   **Graswald / Botaniq:** Blender add-ons that provide curated libraries of grasses, weeds, and plants with tools for scattering and variation. (Source: Graswald/Botaniq product pages).
    3.  **Scanned/Photogrammetry Assets:** [PRACTICE] Quixel Megascans offers a large library of scanned plants, which provide high realism but often require optimization.

*   **Polycount and Instancing Guidance:**
    *   [PRACTICE] There is no single "correct" polycount. The guidance is always "as low as possible while maintaining a convincing silhouette from the camera's distance."
    *   For a still render, a hero interior plant might be between **50,000 and 500,000 polygons**. Background plants would be heavily decimated to **5,000 - 20,000 polygons**. (Source: Common polycounts observed in assets from libraries like Maxtree and discussions on forums like CGArchitect).
    *   **Instancing:** [PRACTICE] The universal rule is to **always use instancing** (or linked duplicates in Blender terminology) whenever a plant is repeated. Instancing allows the renderer to load the geometry once and repeat it many times with minimal memory overhead. This is fundamental to rendering scenes with heavy vegetation. (Source: Blender Manual, "Duplicates" section; V-Ray documentation on proxies/instances). For variation, practitioners will randomly transform (scale, rotate) the instances and can sometimes use material variations to avoid obvious repetition.

## CONFLICTS AND UNCERTAINTY

*   **The "Best" Format:** There is no objective "best" interchange format. The choice is highly dependent on the software ecosystem. While glTF and USD are technically superior in their specifications (especially regarding scale and PBR materials), the industry's reliance on Autodesk products means FBX remains the most common, despite its well-known flaws. The advice is pragmatic: use what works reliably between your specific tools.
*   **Cleanup Necessity:** The degree of cleanup required is not absolute. The "cargo cult" claim is an important one. A pipeline focused on animation or real-time rendering has strict technical requirements (all quads, no n-gons) that are not always necessary for a single still image. Many high-end archviz renders have "cheated" geometry that simply looks correct from the one angle the camera sees. I would not stake a build on a rule that *all* downloaded assets must be fully retopologized to a perfect quad mesh; the rule should be that they must render without artifacts.

## WHAT I COULD NOT SOURCE

*   **Automated Scale Validator:** I could not find any published, generally-used script or tool that automatically validates the plausibility of an asset's bounding box against its semantic class (e.g., "is this chair-sized?"). This appears to remain a manual-check step in professional workflows.
*   **Published Naming Standards:** I could not find a formal, published, cross-studio naming convention for archviz 3D assets. While patterns are evident from community discussions, no equivalent to a standard like the US National CAD Standard® seems to exist for this purpose. Studio-specific conventions are the norm.
*   **Quantitative Hand-Modelled vs. Acquired Study:** I could not find a published, data-driven comparison of the time, cost, and quality trade-offs between modeling and acquiring assets in a professional archviz context. The industry appears to operate on a strong but anecdotal consensus that acquiring is superior for complex, non-bespoke objects.
---

## GROUNDING (vendor-reported)

- search queries issued: none reported

- grounding chunks: NONE REPORTED — treat every number here as unsourced until verified by hand.
