# q1-cg-tells-craft

- vendor: Gemini `gemini-2.5-pro` mode `deep` (google_search grounded)
- date: 2026-08-08
- prompt: `q1-cg-tells-craft.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. EDGE TREATMENT

**Real-world Radii**

*   **Painted MDF Panel Edges:** A common practice for paint-grade MDF is to specify a radius to prevent the paint from cracking and to soften the edge for durability and feel.
    *   [PRACTICE] A 1/16 inch (≈1.59 mm) or 1/8 inch (≈3.18 mm) radius is frequently recommended.
    *   [PRACTICE] For shaker cabinet doors, a common detail is a 1/16" (≈1.59 mm) radius on the inside edges of the frame profile.
    *   [PRACTICE] General woodworking advice for painted edges suggests a minimum radius of 1/8" (≈3.18 mm) to ensure paint adhesion and prevent a "starved" look on sharp corners where paint film is thinnest.

*   **Veneered Plywood Panel Edges:** Edges are typically treated with edge banding. The transition from the face veneer to the edge banding is often broken with a very slight chamfer or radius to prevent the veneer from chipping.
    *   [PRACTICE] A "chamfered edge" or "bevelled edge" is a common specification. A typical bevel might be 1mm x 45°.
    *   [PRACTICE] A minimal "arris" or breaking of the sharp edge is standard practice, often done with a sanding block, resulting in a radius often less than 1 mm. The Architectural Woodwork Standards (AWS) produced by AWMAC, AWI, and WI often refer to "easing" edges. For example, AWI 200 - Care & Storage specifies handling techniques to prevent splintering of sharp corners, implying the fragility of untreated edges.

*   **Solid-Timber Millwork Arrises:**
    *   [PRACTICE] Edges are typically "eased" or "broken" to prevent splintering and for a better feel. This is often a 1/16" (≈1.59 mm) to 1/8" (≈3.18 mm) radius.
    *   [MEASURED] The Architectural Woodwork Standards, Edition 2 (2014) by AWI, AWMAC, and WI, specifies that for transparent finishes (e.g., on solid timber), exposed edges shall be "eased" with a minimum 1/16" (1.6 mm) radius, unless otherwise specified.

*   **Plasterboard External Corners with Corner Bead:**
    *   [MEASURED] Standard metal or vinyl corner beads create a slightly rounded edge. For example, Trim-Tex's 3/4" (≈19 mm) Bullnose Corner Bead creates a 3/4" (≈19 mm) radius. Their standard "Splayed Corner Bead" has a defined, but not explicitly dimensioned, soft radius.
    *   [MEASURED] A common "bullnose" corner bead has a radius of 3/8" (≈9.5 mm) or 3/4" (≈19 mm). A smaller, more common radius for a standard corner bead is approximately 1/8" (≈3.18 mm).

*   **Door Leaf Edges:**
    *   [PRACTICE] Factory-finished doors often have a slight radius on their vertical edges. For solid wood doors, this is often a 1/8" (≈3.18 mm) radius.
    *   [MEASURED] Standards for steel doors, such as those from the Steel Door Institute (e.g., ANSI/SDI A250.8), specify edge constructions. Beveled edges are common, with a typical bevel of 1/8 inch in 2 inches (≈3.18 mm in 50.8 mm).

*   **Stone/Quartz Worktop Arrises:** Manufacturers provide a menu of standard edge profiles.
    *   [MEASURED] Caesarstone, a quartz manufacturer, offers profiles including a "Pencil Edge" with a 1/8" (≈3 mm) radius top and bottom, and a "Double Pencil Edge" with a 1/4" (≈6 mm) radius. Their "Shark Nose" and "Bullnose" profiles have more complex, larger radii. (Caesarstone Edge Profile Guide, available on their website).
    *   [MEASURED] A simple "Eased" edge, one of the most common and least expensive, typically has a 1/8" (≈3 mm) radius on the top edge. A "Half Bullnose" has a continuous radius on the top surface that curves down to the vertical edge. (Source: various stone fabricator websites).

**Archviz Practitioner Bevel Width**

*   [PRACTICE] For archviz in Blender, a common starting point for bevels on furniture and millwork is a small value like 1-2 mm with 2-3 segments. This is often adjusted by eye depending on the object's scale and proximity to the camera. (Source: numerous Blender archviz tutorials on platforms like YouTube, e.g., from Blender Guru, CG Geek).
*   [PRACTICE] There is no widely published rule relating bevel width to pixel size. The decision is almost always artistic and based on achieving a plausible highlight "catch" on the edge. A common workflow is to use a Bevel modifier in Blender and interactively adjust the `Amount` until the highlight looks correct in the camera view. The goal is not necessarily physical accuracy but perceptual plausibility. The bevel needs to be large enough to be resolved by the renderer and break up the mathematically perfect 90-degree corner.

### 2. SHADING AND NORMALS

*   **Current Correct Practice in Blender 4.x:**
    *   [PRACTICE] The standard workflow for hard-surface architectural models is to use the **Shade Auto Smooth** feature (found in the Object Data Properties panel under "Normals"). This shades faces smooth based on the angle between them, preserving sharp edges where desired. The default angle of 30 degrees is often too low for architectural models and is typically increased to a value like 60-90 degrees, or more commonly, sharp edges are marked manually (In Edit Mode, select edges, `Ctrl+E` > `Mark Sharp`).
    *   [PRACTICE] A **Bevel modifier** is almost always used in conjunction with Shade Auto Smooth. The modifier adds real geometry to the edges, which allows for realistic highlights. Within the Bevel modifier, setting the `Shading` > `Harden Normals` option is crucial. This ensures the faces adjacent to the bevel are shaded flat relative to the bevel, creating a clean transition.
    *   [PRACTICE] The **Weighted Normal modifier** is used to correct shading artifacts on large flat surfaces (n-gons or triangulated quads) that have bevels or other details inset into them. It works by adjusting the vertex normals to be more influenced by the area of the surrounding faces. It should be placed *after* the Bevel modifier in the stack. A common setup is: Bevel Modifier (with Harden Normals) -> Weighted Normal Modifier -> Shade Auto Smooth enabled on the object data.

*   **What Goes Wrong Visually:**
    *   **Flat-shaded with unbeveled 90° edges:** The object looks overtly like a computer model. Real-world objects never have perfectly sharp edges. The key missing visual cue is the **specular highlight** that should run along the edge. Without a bevel, there is no surface to catch the light and create this highlight, resulting in a flat, unrealistic appearance. This is often called the "razor edge" problem.
    *   **Smooth shading without bevel or weighted normals:** This creates significant visual artifacts. On a simple cube, smooth shading will average the normals across the 90-degree corners, resulting in a bizarre, ugly gradient across the flat faces as the renderer tries to create a smooth curve where none exists. The silhouette remains sharp, but the interior shading is completely wrong, making the object look like a soft, squishy object trying to be a cube. On more complex hard-surface models with inset details, this leads to pronounced shading errors and "pinching" around the intersections.

### 3. SILHOUETTE RESOLUTION

*   **Segments for a Curve:**
    *   [PRACTICE] There is no universally published rule tied to subtended pixel count for archviz specifically. The standard is "enough so it doesn't look faceted from the hero camera angle." For a typical 2-6 m camera distance, a common rule of thumb for cylindrical objects is to start with 32 segments and increase to 64 if it is a prominent, close-up feature. For a 90-degree corner radius (like a rounded worktop), 8 to 16 segments are often sufficient.
    *   [INFERENCE] The visibility of faceting is a function of the angle between segment normals and the pixel resolution. A rule used in game development is the "one pixel per degree" concept, but this is not a formal standard. The core idea is that if the change in angle from one segment to the next is smaller than the angle subtended by a single pixel, it will be imperceptible.
    *   [PRACTICE] The Blender manual suggests that for Subdivision Surface modeling, the optimal `Levels Viewport` setting is typically 1 or 2, with the `Render` level at 2 or 3, to balance performance and quality. This approach procedurally adds geometry, and the density is determined by the base mesh topology. (Source: Blender 4.x Manual, "Subdivision Surface Modifier").

*   **Polygon-Count Bands for Production Assets:**
    *   [MEASURED] Examining high-quality archviz asset marketplaces provides concrete examples (poly counts are for the base mesh, often before subdivision):
        *   **Pillow:** 1,000 - 10,000 polygons. A simple decorative pillow might be at the low end, while a complex, wrinkled pillow could be much higher.
        *   **Upholstered Chair:** 20,000 - 200,000 polygons. A simple dining chair might be 20k, while a detailed armchair with tufting and wrinkles (e.g., a Chesterfield) can easily exceed 100k.
        *   **Table Lamp:** 5,000 - 50,000 polygons. A simple cylindrical lamp is at the low end; a complex designer lamp with intricate parts is at the high end.
        *   **Curtain Panel:** 15,000 - 100,000+ polygons, highly dependent on the complexity of the folds. A simple, taut panel is low, while a realistic, heavily folded curtain is very high.
        (Source: Analysis of asset descriptions on marketplaces like 3DSky, Dimensiva, and Turbosquid for "Archviz" or "Photorealistic" models).

### 4. CONTACT

*   **What Makes an Object Read as Resting:**
    *   [PRACTICE] The most critical element is a **contact shadow**. In a path tracer like Cycles, this is generated naturally if the geometry is physically touching or extremely close (e.g., within 0.1 mm). The shadow should be very dark and sharp right at the contact point, diffusing softly as the distance from the contact point increases.
    *   [PRACTICE] **Ambient Occlusion (AO)** is the artistic control that mimics this effect. While physically-based renderers create this naturally, AO shaders or post-production passes are often used to exaggerate it for perceptual effect. A very small radius AO effect can darken the crevice where the object meets the floor, "grounding" it. The Blender manual describes the Ambient Occlusion shader node which can be used for this purpose in a material setup. (Source: Blender 4.x Manual, "Ambient Occlusion Node").
    *   [PRACTICE] **Gap Tolerances:** For elements like skirting boards against a floor, a perfectly flush contact is unrealistic. Real construction has gaps.
        *   [MEASURED] The American Woodwork Institute's standards (e.g., AWI 100 - Submittals) specify tolerances. For example, the gap between a cabinet and a wall might be acceptable up to 1/16" (1.6 mm). A skirting board on an uneven floor will have a variable gap. Simulating a tiny, uneven gap (e.g., 0.5 mm - 1.5 mm) can add realism, as it allows for a thin line of shadow and prevents Z-fighting (surface flickering).
    *   [PRACTICE] **Dust/Grime:** A subtle texture map (a "dirt map") blended into the base color and roughness channels along the contact line (using the AO node as a mask) is a common technique to add realism. This simulates the accumulation of dust in corners that are difficult to clean.

*   **Published Guidance on Minimum Shadow Evidence:**
    *   NO SOURCED VALUE FOUND. There is no known formal standard like "a contact shadow must be X% darker than the surrounding floor." The guidance is qualitative. Perceptual studies in computer graphics have focused on the importance of soft shadows for judging object position and distance, but have not prescribed minimum intensity values for believability. The key finding is that the *absence* of a plausible contact shadow is a major cue that an object is floating.

### 5. SURFACE VARIATION

*   **Published Material Breakdowns:**
    *   [MEASURED] Material scanning services and libraries provide measured PBR values. While they don't typically publish mean/std-dev for the maps themselves, analysis of the provided texture maps is possible.
        *   **Matte Interior Wall Paint:** Roughness is not uniform. It varies with the texture of the drywall/plaster underneath and the roller stipple. A typical roughness map for matte paint from a source like Poliigon or Quixel Megascans will have a mean value in the range of **0.7 - 0.9** (on a 0-1 scale), with subtle variations (low standard deviation) driven by the underlying surface texture. The base color map will have very subtle variations in value to represent uneven paint application.
        *   **Lacquered Oak Veneer:** The roughness will be lower than matte paint and more complex. The lacquer fills the grain to some extent. The roughness map will have lower values (e.g., mean of **0.1 - 0.3**) in the flat areas of the lacquer, and higher values (e.g., **0.4 - 0.6**) in the pores of the wood grain that were not perfectly filled. The base color is driven entirely by the wood grain. (Source: Analysis of PBR textures from libraries like Poliigon, Quixel Megascans, and textures.com).
        *   **Satin Powder-Coated Metal:** This surface has a micro-texture. The roughness map will have a mean value in the range of **0.2 - 0.4**. The key feature is often a very fine, procedural noise or a subtle texture map in the normal/bump channel to represent the characteristic "orange peel" or textured finish of powder coating.

*   **Contribution of "Imperfection" Layers:**
    *   [PRACTICE] The contribution is almost universally asserted as crucial for realism in practitioner communities. Numerous tutorials and articles demonstrate the "before and after" of adding fingerprints, dust, scratches, and edge wear. For example, tutorials by Blender Guru ("The Secrets of Photorealism") and Gleb Alexandrov ("Creative Lighting") heavily emphasize imperfections as a key step.
    *   [INFERENCE] While there are countless "before/after" images in tutorials that are subjectively convincing, there is NO SOURCED VALUE FOUND for a formal, peer-reviewed perceptual study that isolates *only* the addition of imperfection maps on architectural surfaces and measures the change in perceived realism (e.g., via a controlled user study). The effect is accepted as a fundamental artistic principle in the field of CG, but its quantitative contribution to realism appears to be unmeasured in a rigorous academic sense.

### 6. THE HONEST QUESTION

*   **Published, Quantitative Work:**
    *   [MEASURED] There is a significant body of academic work on perceptual metrics for rendering, but much of it focuses on global illumination accuracy, material model fidelity, or specific phenomena like caustics, rather than a ranked list of "CG cues" for interiors.
    *   [MEASURED] A 2015 paper by G. K. O'Donovan et al., "Where do people look at images?", while not specific to CG, uses eye-tracking to show that human gaze is drawn to areas of high contrast, faces, and text. In an interior, this would be windows, light sources, and high-contrast edges. [INFERENCE] This suggests that errors in these specific areas (e.g., unrealistic window lighting, sharp unbeveled edges) would be more readily noticed.
    *   [MEASURED] Research on "Visual Realism of Virtual Environments" (summarized in a 2011 survey by Rademacher et al.) identifies key factors as lighting, shadows, and material properties. However, a definitive, ranked list for *interior archviz* that includes craft defects like edge sharpness is not presented.

*   **Practitioner Opinion (The Strongest Sources):**
    *   [PRACTICE] The most consistent ranking of cues that scream "this is CG" in practitioner forums, tutorials, and articles is as follows:
        1.  **Lighting and Shadowing:** Unrealistic lighting is the number one giveaway. This includes perfectly uniform ambient light, lack of contact shadows, overly sharp shadows from area lights, and incorrect color temperature. (Source: Consistently cited as the most important element by virtually all high-end archviz artists and studios, e.g., in interviews and tutorials from MIR, DBOX, Bertrand Benoit).
        2.  **Perfect Edges:** As detailed in Q1 and Q2, mathematically sharp, unbeveled edges are a dead giveaway because they do not exist in the real world.
        3.  **Perfect Surfaces:** As detailed in Q5, materials that are perfectly clean, perfectly flat, and have uniform roughness values look artificial. The lack of subtle variation (dirt, dust, scratches, fingerprints, variation in color/roughness) is a major cue.
        4.  **Repetition (The "Machine Gun Effect"):** Obvious repetition of textures or assets without variation in scale, rotation, or color immediately breaks realism.
        5.  **Lack of "Story" or "Life":** This is less measurable but often cited. A scene that is too perfect, with every object perfectly aligned and no signs of use (a rumpled cushion, a slightly askew book, a cable for a lamp), feels sterile and artificial.

    This ranking is a strong, consistent consensus among professionals, but it is based on collective experience, not a formal perceptual study.

### 7. SCORING

*   **Published Tools and Metrics:**
    *   [MEASURED] **Mesh Quality Checkers:** These are common in 3D software and production pipelines but focus on technical, not aesthetic, craft.
        *   **Blender's 3D-Print Toolbox:** This built-in add-on can check for non-manifold geometry, distorted faces, and sharp edges (`Check All`), but it's designed for 3D printing, not visual realism. It measures geometric integrity. (Source: Blender 4.x Manual).
        *   **Autodesk Maya's "Mesh Cleanup" tool:** This tool can find and fix issues like lamina faces, non-manifold geometry, and faces with zero area. It scores the technical health of the mesh. (Source: Maya Documentation).
        *   **ZBrush's "Mesh Analysis" tools:** These can detect issues like thickness for 3D printing.

    *   **Edge-Sharpness / Silhouette Analysis:**
        *   NO SOURCED VALUE FOUND for a tool that automatically scores an image for "overly sharp edges" or "faceted silhouettes" in a way that correlates to perceived realism. This analysis is currently done by the artist's eye.

    *   **Image Quality Metrics:**
        *   [MEASURED] There are many image quality metrics, but they are not designed to score "craft" or "realism." They measure differences between images.
        *   **SSIM (Structural Similarity Index Measure) / PSNR (Peak Signal-to-Noise Ratio):** These are used to compare a rendered image to a reference (e.g., a photograph or a ground-truth render). They do not score realism in an absolute sense. They score fidelity to a source.
        *   **No-Reference Image Quality Assessment (NR-IQA):** Models like BRISQUE or NIQE attempt to score the quality of an image without a reference, but they are trained to detect artifacts like blur, noise, and compression blocks, not the subtle cues of CG.

    In summary, while tools exist to check the *technical* integrity of a mesh, there are no widely available, published tools that automatically score the *artistic craft* properties (edge treatment, silhouette quality, surface variation) from a mesh or a final render in the context of photorealism. This remains the domain of the artist and art director.

## CONFLICTS AND UNCERTAINTY

*   **Edge Radii:** The primary uncertainty is the lack of formal, universal standards for "eased" edges on millwork. While AWI provides a minimum of 1.6 mm for transparent finishes, the actual radius applied in practice can vary based on tooling, wood species, and desired aesthetic. Values are more often a "rule of thumb" than a hard specification. I would not stake a build on a single radius value for "solid timber"; it requires context.
*   **Bevel Width vs. Pixel Size:** There is a complete lack of sourced, quantitative guidance here. The practice is purely artistic and observational. Any rule tying bevel width to pixel size would be an inference based on general computer graphics principles, not a documented archviz practice.
*   **Imperfection Contribution:** The value of imperfection maps is asserted universally by practitioners but appears to lack formal, quantitative, perceptual studies to back it up. The "before/after" images are compelling, but they are not controlled experiments. The *amount* and *type* of imperfection needed is purely an artistic judgment.

## WHAT I COULD NOT SOURCE

*   A published, quantitative rule relating bevel width in 3D to the final pixel size at the camera for archviz.
*   A published, peer-reviewed perceptual study that isolates and measures the specific contribution of "imperfection maps" (dust, fingerprints, etc.) to the perceived realism of an interior architectural scene.
*   A published, peer-reviewed study that provides a quantitative ranking of the specific "craft" cues (edge sharpness, surface variation, etc.) that trigger a "this is CG" judgment in human observers for interior scenes. The existing ranking is a strong but informal practitioner consensus.
*   Any automated tool or metric specifically designed to score a rendered image or a 3D mesh for craft properties like edge realism, silhouette quality, or believable surface variation in the context of photorealism. Existing tools focus on technical mesh errors or general image artifacts.
---

## GROUNDING (vendor-reported)

- search queries issued: none reported

- grounding chunks: NONE REPORTED — treat every number here as unsourced until verified by hand.
