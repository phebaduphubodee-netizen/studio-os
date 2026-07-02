> ⚠️ **SUPERSEDED 2026-07-01 — priority only, not the facts.** This DR recommended BUYING a hybrid paid-asset furniture/material
> library to reach modern-luxury render quality. Later the SAME day, the **3D→Gemini "Nano Banana" image-pass** (~PORS quality for
> ~$0.039/image) demoted the furniture-pack purchase to LOWER priority (buy only if a client needs a specific real SKU) — see
> `docs/DECISIONS-render-assets.md` (the authority). The source list + licenses below stay valid; the "buy a pack now" verdict does not.

---

## QUESTION DECOMPOSITION — the sub-questions that must be answered.

1.  **Free Asset Sources:** What are the best sources for free, commercially-usable (CC0 or similar) 3D models and materials for a "warm modern-luxury" aesthetic, compatible with Blender (glTF/FBX)? What is the specific license and realistic quality level of each?
2.  **Paid Asset Marketplaces:** Which affordable, paid marketplaces and libraries offer the best selection of high-quality, modern-luxury 3D assets (e.g., bouclé sofas, marble/brass items)? What are their typical price ranges, license terms for commercial client deliverables, and overall value for achieving a photorealistic, high-end look?
3.  **Professional Asset Library Strategy:** How do professional visualization studios and interior designers build, organize, and maintain a curated, reusable asset library to ensure consistency, efficiency, and quality?
4.  **Authoritative Grounding:** What do canonical interior design, lighting, and visualization textbooks and standards say about material specification, lighting, and object selection that would inform the choice and use of these 3D assets?
5.  **AI Pipeline Integration:** What are the concrete implications of these findings for an automated, spec-driven AI drafting pipeline? What specific data fields, rules, and quality checks are necessary to produce a "complete" and professional deliverable?

---

## EVIDENCE / FINDINGS — substantive content, organized by topic, with the authoritative textbook/standard named for each block.

### 1. Free (CC0 / Commercially-Usable) Asset Sources for Modern-Luxury

Finding true high-end, stylistically-specific assets for free is challenging, as top-tier models require significant labor. However, several platforms provide a solid starting point. The key is to be selective and potentially modify assets to meet exacting standards.

*   **Poly Haven:**
    *   **Assets:** Primarily known for extremely high-quality, physically-based rendering (PBR) texture maps (materials) and HDRIs (for lighting), which are crucial for photorealism. Their 3D model library is growing.
    *   **License:** CC0 (Public Domain Dedication). You can copy, modify, distribute, and perform the work, even for commercial purposes, without asking permission.
    *   **Quality:** Excellent for materials and HDRIs. Models are generally of high quality but the selection is not as vast as paid libraries. You may find good base models for decor and some furniture.
    *   **Relevance to Modern-Luxury:** Excellent source for foundational materials like wood flooring, plaster, and metals. The HDRIs are essential for achieving realistic lighting, a cornerstone of luxury aesthetics as detailed in Gary Gordon's *"Interior Lighting for Designers"*.

*   **BlenderKit:**
    *   **Assets:** A large, integrated library of models, materials, and brushes accessible directly within Blender via an add-on.
    *   **License:** Offers a mix of free and paid assets. Free assets are typically under a Creative Commons license (often requiring attribution) or a royalty-free license. It is crucial to check the license for each specific asset. The full paid plan provides a royalty-free license for all assets, suitable for commercial use.
    *   **Quality:** Varies significantly. The free tier contains many user-submitted models that can range from basic to quite good. The paid "Full" plan generally offers more consistent, higher-quality assets curated by the platform.
    *   **Relevance to Modern-Luxury:** You can find some modern furniture pieces, but the "luxury" aspect (e.g., perfect fabric folds on a bouclé sofa) is more reliably found in the paid tier or on specialized marketplaces.

*   **3dassets.one:**
    *   **Assets:** This is a search engine that aggregates free 3D models from various sources across the web.
    *   **License:** Varies by the source site. The platform helps you filter by license type, including "Commercial Use." You must verify the license on the original source page for every asset.
    *   **Quality:** Highly variable, as it pulls from a wide range of creators and platforms. It requires a discerning eye to find high-quality models suitable for professional work.
    *   **Relevance to Modern-Luxury:** Can be useful for finding specific decor items or secondary furniture pieces if you are willing to invest the time in searching and vetting.

*   **Manufacturer Websites (Speculative but common practice):**
    *   **Assets:** Many high-end furniture manufacturers (e.g., Herman Miller, Knoll, Cassina) provide 3D models of their products for architects and designers to use in specifications.
    *   **License:** These are typically for specification purposes only and may have restrictive licenses that do not permit use in all types of commercial client deliverables without permission. Always check the terms and conditions. This is a common practice but treads into a gray area if not used for specifying that exact product in the project.
    *   **Quality:** Usually very high, as the models are created or commissioned by the manufacturer to represent their products accurately.
    *   **Relevance to Modern-Luxury:** The most direct way to get specific, iconic designer pieces. The challenge is the licensing and the effort required to collect models from numerous individual sites.

### 2. Affordable Paid Marketplaces for Modern-Luxury Assets

Paid platforms are the professional standard for high-quality, consistent, and correctly licensed assets.

*   **Poliigon:**
    *   **Assets:** Primarily a material and texture library, but also offers models, decals, and HDRIs. Founded by Andrew Price (Blender Guru), it is highly respected for quality.
    *   **License:** Subscription-based, royalty-free license for commercial use in renders and animations. Redistribution of the assets themselves is prohibited.
    *   **Price:** Subscriptions range from approximately $17/month (billed annually) for a starter tier to higher levels for more downloads.
    *   **Quality:** Exceptional. Materials are meticulously scanned and processed for photorealistic PBR workflows. This aligns with the principles in Binggeli's *"Materials for Interior Environments"*, which emphasizes the importance of accurate material representation.
    *   **Relevance to Modern-Luxury:** Essential for this aesthetic. High-resolution marble, brass, specific wood species, and fabric weaves (like bouclé) are their specialty. The quality of materials is often what separates a good render from a photorealistic one.

*   **Dimensiva:**
    *   **Assets:** Curated library of high-end, designer 3D furniture models. They focus exclusively on iconic and contemporary pieces.
    *   **License:** Royalty-free for commercial projects.
    *   **Price:** Offers a free section with a limited selection. Paid access is via subscription, starting around €29/month, or through purchasing individual models.
    *   **Quality:** Very high. Models are crafted for photorealism with clean topology and high-resolution textures.
    *   **Relevance to Modern-Luxury:** Excellent fit. This is a go-to source for the specific "designer" look common in warm modern-luxury projects. You will find the types of sofas, chairs, and tables prevalent in high-end Thai and international design studios.

*   **3D Sky:**
    *   **Assets:** A massive marketplace with a vast number of models submitted by various artists.
    *   **License:** Most models are sold under a royalty-free license. They offer a mix of individual purchases and a subscription model.
    *   **Price:** Individual models often range from $5 to $15. The subscription offers a set number of downloads per day.
    *   **Quality:** Highly variable, but generally good to excellent, especially for "Pro" models. It is crucial to inspect the wireframes and texture resolutions shown in the previews. The user-based rating system is a helpful guide.
    *   **Relevance to Modern-Luxury:** Unmatched selection. You can find almost any piece of furniture or decor, including very specific bouclé sofas and marble/brass combinations. It is a workhorse for many professional visualization artists.

*   **Design Connected:**
    *   **Assets:** Similar to Dimensiva, this platform focuses on high-end, licensed 3D models from real designer brands.
    *   **License:** Royalty-free license for use in commercial work.
    *   **Price:** Generally more expensive, often selling models individually for $50-$200+. They also offer subscription plans.
    *   **Quality:** Superlative. Considered one of the highest-quality sources, with models that are essentially digital replicas of the real products, often verified by the manufacturers.
    *   **Relevance to Modern-Luxury:** The premium choice. If a project requires a specific, iconic piece of furniture rendered with absolute fidelity, this is a top source. The cost is justified when accuracy and quality are non-negotiable.

### 3. Building a Professional, Reusable Asset Library

Professionals do not hunt for assets on a per-project basis. They build a curated internal library over time. This practice is about efficiency, quality control, and maintaining a consistent aesthetic.

1.  **Acquisition & Curation:** Start with a foundational set of high-quality, versatile assets from a trusted marketplace (e.g., a few classic modern sofas, chairs, tables, and a core library of PBR materials from Poliigon). Be highly selective. An asset must have clean geometry (quad-based topology is preferred), high-resolution PBR textures (Albedo, Roughness, Normal, etc.), and a realistic scale. This aligns with the principles of dimensioning and anthropometrics found in Panero & Zelnik's *"Human Dimension & Interior Space"*, ensuring objects are not just visually appealing but also correctly sized.
2.  **Standardization:** Convert all incoming assets to a consistent format (e.g., .blend files with packed textures or a standardized folder structure). Check and adjust material shaders to work optimally within Blender's Cycles or Eevee render engines. This might involve building a standard "uber-shader" node group that all materials in the library use.
3.  **Organization:** Use a clear, logical folder structure. A common professional approach is to organize by category, then sub-category, then object name/style (e.g., `/FURNITURE/Seating/Sofa_Modern_L-Shape_BoucleWhite/`). Use Blender's Asset Browser to create a visual, searchable library directly within the software. Tag assets with metadata: style (e.g., "modern," "minimalist"), material ("bouclé," "marble," "brass"), designer, and source.
4.  **Licensing:** Maintain a simple database or spreadsheet that tracks each asset, its source, and its license terms. This is critical for avoiding legal issues when delivering projects to clients.
5.  **Refinement:** Over time, refine and improve library assets. You might re-texture an old model with new, higher-quality materials from Poliigon or adjust the geometry for better performance.

---

## CANONICAL SOURCES — a bulleted list of the specific books/standards a builder should acquire, with author + title (+ edition/year if known) and what each is the authority FOR.

*   **Ching, Francis D.K. "Interior Design Illustrated" (4th Edition, 2018):**
    *   **Authority for:** Foundational principles of space, form, scale, proportion, and the relationship between design elements. Use this to validate the *placement* and *selection* of assets within a scene to create a coherent design.

*   **Panero, Julius, and Martin Zelnik. "Human Dimension & Interior Space: A Source Book of Design Reference Standards":**
    *   **Authority for:** Anthropometrics and ergonomics. This is the ground truth for the *dimensions* of furniture and the clearance spaces required around them. An asset is not just a shape; it must conform to human scale. A sofa's seat height (typically 16-18 inches) and depth (typically 21-24 inches) are critical for realism.

*   **Binggeli, Corky. "Materials for Interior Environments" (2nd Edition, 2013):**
    *   **Authority for:** The properties and applications of real-world materials. Use this to gut-check the PBR materials you acquire. Does the "marble" have the correct amount of subsurface scattering? Does the "brass" have the right reflectivity and color? This book provides the physical basis for your digital materials.

*   **Gordon, Gary. "Interior Lighting for Designers" (6th Edition, 2015):**
    *   **Authority for:** Principles of architectural lighting design. Essential for understanding how to use digital light sources (e.g., IES profiles in Blender) to create mood, define space, and realistically illuminate the materials and furniture you've selected. It explains concepts like layers of light (ambient, task, accent) that are directly applicable to 3D rendering.

*   **IES (Illuminating Engineering Society) "The Lighting Handbook" (10th Edition):**
    *   **Authority for:** The technical standard for illumination. Provides specific quantitative recommendations for light levels (measured in foot-candles or lux) for different tasks and spaces. Real lighting manufacturers provide IES profiles for their fixtures, which can be used in Blender to simulate their exact light distribution, adding a high degree of realism.

---

## SYNTHESIS — an integrated, builder-usable answer to the original question.

For your automated Blender pipeline targeting a warm modern-luxury aesthetic, a hybrid asset strategy is the professional standard. Do not rely solely on free sources.

Your primary investment should be in a high-quality **PBR material library subscription**. **Poliigon** is the best starting point for this. Photorealistic materials are the bedrock of a luxury look, and Poliigon provides the necessary accuracy for surfaces like Italian marble, brushed brass, and woven fabrics like bouclé.

For **3D furniture and decor models**, begin by curating a small, core library from a high-value paid marketplace. **Dimensiva** and **3D Sky** (specifically the "Pro" models) offer the best balance of quality, style, and affordability for the bouclé/marble/brass aesthetic. While **Design Connected** represents the highest quality, its price point may be better suited for hero assets in bespoke projects rather than building a large base library.

Use **free sources strategically**. **Poly Haven** is excellent for supplementary PBR textures and essential HDRIs for realistic lighting. The **BlenderKit** add-on is useful for secondary, background items, but vet the quality and license of each free asset carefully. Reserve manufacturer websites for when a project requires specifying an exact, iconic piece, and be prepared to navigate their licensing terms.

The professional workflow is not to hunt for new assets for every project, but to **build a standardized, curated internal library** over time. Organize assets logically within Blender's Asset Browser, ensure all materials are optimized for Cycles, and maintain a separate record of licenses. This initial investment in curation and standardization is what enables speed and consistency in a professional pipeline.

---

## ACTIONABLE FOR AN AI DRAFTING PIPELINE — concrete elements/fields/checks this implies for a spec-driven generator.

A "complete" deliverable from an AI pipeline must contain more than just a render. It requires a structured set of specifications. Your AI should be built to understand and populate the following fields for any given object or material:

**1. Asset Specification Fields:**
*   `asset_ID`: A unique identifier for the library item.
*   `asset_Source`: The marketplace or vendor it was acquired from (e.g., "Poliigon," "Dimensiva").
*   `asset_License`: The specific license type (e.g., "CC0," "Royalty-Free Commercial Use").
*   `asset_Category`: Hierarchical tag (e.g., `FURNITURE > SEATING > SOFA`).
*   `asset_Style`: Tags for aesthetics (e.g., `modern`, `luxury`, `minimalist`, `warm`).

**2. Geometric & Spatial Rules (Derived from Panero & Zelnik):**
*   `dimensions_mm`: (X, Y, Z) dimensions of the asset's bounding box.
*   `clearance_zone_mm`: A defined perimeter around the asset for circulation (e.g., a dining chair needs ~750mm behind it for push-back). The AI must check for clearance violations.
*   `anthropometric_compliance`: A check to ensure key dimensions are within standard ranges (e.g., `seat_height_mm` is between 400-460mm).

**3. Material Specification Fields (Derived from Binggeli):**
*   `material_Name`: Common name (e.g., "Carrara Marble," "Brushed Brass," "White Bouclé").
*   `material_Type`: `METAL`, `STONE`, `FABRIC`, `WOOD`.
*   `pbr_Maps`: A checklist of required textures (`Albedo`, `Roughness`, `Normal`, `Metallic`, `Displacement`). The AI should flag any material missing critical maps.
*   `physical_Properties`: Speculative but advanced: encode real-world data like hardness or slip resistance where relevant for construction documents.

**4. Lighting Specification Fields (Derived from Gordon & IES):**
*   `fixture_ID`: Unique ID for a light source.
*   `fixture_Type`: `recessed_downlight`, `pendant`, `cove_light`.
*   `light_Profile`: Path to the IES file for accurate light distribution.
*   `color_Temperature_K`: Color temperature in Kelvin (e.g., `2700K` for warm, residential light).
*   `luminous_Flux_lm`: Light output in lumens.
*   `lighting_Layer`: The function of the light (`ambient`, `task`, `accent`).

The AI pipeline's core logic should be to take high-level design intent (e.g., "place a modern bouclé sofa for three people in the living area") and translate it into a query against this structured asset library. It would then place the selected asset, checking for violations of clearance and anthropometric rules, and apply validated PBR materials to ensure a photorealistic, professionally-grounded result.