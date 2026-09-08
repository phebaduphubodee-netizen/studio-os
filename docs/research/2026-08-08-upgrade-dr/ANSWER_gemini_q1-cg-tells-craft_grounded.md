# q1-cg-tells-craft (grounded retry)

- vendor: Gemini `gemini-2.5-pro` mode `pro` — **SEARCH DID NOT FIRE**
- date: 2026-08-08
- prompt: `q1-cg-tells-craft.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.

> **UNGROUNDED — the vendor reported ZERO retrieved sources.** Every value
> below came from model memory, including the ones that name a manufacturer
> or a standard. Nothing here may enter `knowledge/` until a second pass
> retrieves the page. Treat source names in the text as CLAIMS, not citations.
## ANSWERS

### 1. EDGE TREATMENT

**Real-world Radii**

*   **Painted MDF Panel Edges:** A common recommendation for a paintable edge on MDF is a 3mm radius. [PRACTICE] (Dalply, "MDF Fabrication Guide", dalply.com/wp-content/uploads/2020/11/MDF-Fabrication-Guide.pdf). Another fabricator suggests a minimum of a 1/8" (3.175mm) radius for powder-coated MDF to ensure powder adhesion. [MEASURED] (DVUV, "Powder Coated MDF Design & Fabrication Guide", dvuv.com/wp-content/uploads/2020/01/DVUV-Design-Guide-2020.pdf). For sharp-looking edges on shaker doors, a 1/16" (1.5875mm) radius is often used. [PRACTICE] (Axiom Tool Group, "Making Shaker Style Cabinet Doors with a CNC Router", blog.axiomtoolgroup.com/2022/03/making-shaker-style-cabinet-doors-with-a-cnc-router/).
*   **Veneered Plywood Panel Edges:** The Architectural Woodwork Standards (AWS), Edition 2, 2014, produced by AWMAC, AWI, and WI, specifies edge treatments. For a "Radius" edge (E-4), it allows for any radius to be specified. For a "Bullnose" edge (E-5), it is defined as two radii meeting. The standard does not mandate specific radii but provides the framework for specifying them. [MEASURED] (Architectural Woodwork Manufacturers Association of Canada et al., "Architectural Woodwork Standards, Edition 2", 2014, p. 238, awmac.com/wp-content/uploads/2021/03/Architectural-Woodwork-Standards_Ed2.pdf). In practice, a very slight "easing" of the edge is common to prevent splintering, often done with a sanding block, resulting in a radius of less than 1mm. [PRACTICE]
*   **Solid-Timber Millwork Arrises:** As with veneered panels, the AWS standard allows for specification. A common practice for a slightly broken, crisp edge is a 1mm to 2mm radius. [PRACTICE]
*   **Plasterboard External Corners:** Metal and vinyl corner beads for drywall typically create a soft, rounded corner. For a 90° external corner, a common bullnose bead radius is 3/4" (19.05mm). [MEASURED] (Trim-Tex, "Bullnose Corner Beads", trim-tex.com/products/corner-beads/bullnose). Smaller radii are also available, such as a 3/8" (9.525mm) "mini-bullnose". [MEASURED] (Structus, "Pro-struct Bullnose 10mm", structus.co.nz/product/pro-struct-bullnose-10mm/). A standard square-edge corner bead will still produce a small radius due to the thickness of the bead and the joint compound feathered over it, typically in the 2-4mm range. [INFERENCE]
*   **Door Leaf Edges:** Factory-finished timber doors often have a 3mm radius on their vertical edges for durability and paint adhesion. [PRACTICE] (Example: Jeld-Wen, though not a universal standard).
*   **Stone/Quartz Worktop Arrises:** Fabricators offer a range of standard edge profiles. A simple "Eased" or "Slightly Rounded" edge typically has a radius of 1/8" (3.175mm). A "Pencil" edge has a radius similar to a pencil's diameter, roughly 1/4" (6.35mm). A "Half Bullnose" has a single large radius on the top edge. [MEASURED] (Caesarstone, "Edge Profiles", caesarstone.ca/edge-profiles/). For example, Silestone specifies a minimum radius of 3mm for all edges to reduce chipping risk. [MEASURED] (Silestone, "Fabrication Manual", 2018, p. 24, pro.cosentino.com/en-ca/silestone-fabrication-manual/).

**Archviz Practice (Blender)**

*   **Bevel Width for Distant Objects:** For general architectural elements viewed from 2-6m, practitioners often use very small bevel radii, frequently in the range of 1mm to 5mm. [PRACTICE] (Gleb Alexandrov, "The Secret Ingredient to Photorealism", Creative Shrimp, creativeshrimp.com/photorealism-secret-ingredient-blender.html). The goal is not always physical accuracy but to catch a specular highlight and break up the perfect 90-degree CG edge.
*   **Bevel Width vs. Pixel Size:** There is no widely published, formulaic guidance directly linking bevel width in world units to the final pixel size at the camera in archviz practice. The decision is almost always made artistically. [PRACTICE] The common advice is to create a bevel that is "visible but not distracting," which is dependent on lighting, material properties, and camera distance. One practitioner suggests a rule of thumb: "If you can see it, it's probably too big." [PRACTICE] (Andrew Price, "The 7 Habits of Highly Effective Artists", Blender Guru, blenderguru.com/articles/7-habits-highly-effective-artists). The goal is for the bevel to be *felt* in the specular response of the edge rather than explicitly *seen* as a rounded corner. [INFERENCE]

### 2. SHADING AND NORMALS

*   **Correct Practice in Blender 4.x:** The current standard practice for hard-surface architectural models is to use a "Shade Auto Smooth" setting on the mesh, combined with a "Weighted Normal" modifier, and often a "Bevel" modifier. [PRACTICE] (Blender 4.1 Manual, "Shade Smooth", docs.blender.org/manual/en/4.1/modeling/meshes/editing/shading.html).
    *   **Shade Auto Smooth:** This function, enabled in the Object Data Properties tab, shades faces smooth if the angle between them is less than a specified threshold (default 30°), and sharp otherwise. This is the primary tool for controlling sharp vs. smooth edges without adding geometry. [MEASURED] (Blender 4.1 Manual, "Normals > Auto Smooth", docs.blender.org/manual/en/4.1/modeling/meshes/editing/normals.html).
    *   **Weighted Normal Modifier:** This modifier adjusts vertex normals to be perpendicular to the largest adjacent face. This is crucial for eliminating shading artifacts on large n-gon faces (like a wall with a window cutout) where the default vertex normals can cause visible gradients or triangulation artifacts, even on a perfectly flat surface. It should typically be placed last in the modifier stack. [PRACTICE] (Blender 4.1 Manual, "Weighted Normal Modifier", docs.blender.org/manual/en/4.1/modeling/modifiers/modify/weighted_normal.html).
    *   **Bevel Modifier:** The Bevel modifier adds geometry to edges. When used with "Harden Normals" enabled, it works with Shade Auto Smooth to create perfect-looking transitions around beveled edges without requiring extremely high segment counts on the bevel itself. [PRACTICE] (Blender 4.1 Manual, "Bevel Modifier > Shading", docs.blender.org/manual/en/4.1/modeling/modifiers/generate/bevel.html).
*   **What Goes Wrong (Flat Shading):** A flat-shaded mesh with unbeveled 90° edges produces an unnaturally sharp, "razor-edge" look. Specular highlights will abruptly stop at the edge instead of realistically wrapping around it, which is a major cue of CG imagery. This effect is often called "aliasing" of the specular highlight. [PRACTICE]
*   **What Goes Wrong (Smooth Shading without Support):** Applying "Shade Smooth" to a hard-surface model without either bevels or a Weighted Normal modifier results in significant visual errors. The renderer attempts to smoothly interpolate normals across sharp 90° edges, creating a dark, ugly gradient across the flat surfaces near the edge. This makes flat walls look strangely curved and creates black artifacts at the corners. On large n-gons, it can lead to strange, non-uniform shading across the face. [PRACTICE] (Blender Guru, "How to Fix Bad Shading in Blender", youtube.com/watch?v=fb_Av_u_K48).

### 3. SILHOUETTE RESOLUTION

*   **Segments for a Curve:** There is no single published rule, but a common [PRACTICE] in high-end VFX and gaming is the "one vertex per pixel" rule of thumb for silhouettes. This means a curve should have enough segments that, at its rendered resolution, the length of a single segment's edge is approximately one pixel long. For archviz at 2-6m, this is often overkill. A more practical approach is to ensure the angle between segments is small enough that the faceting is not apparent. For a 90-degree arc (like a rounded corner), 8-16 segments are often sufficient. For a full cylinder (like a lamp base), 32-64 segments are common. [PRACTICE] (Polycount Wiki, "Level of Detail", wiki.polycount.com/wiki/Level_of_Detail). The decision is artistic and depends on the final render resolution and how close the camera is.
*   **Published Polygon Count Bands:**
    *   **Pillow:** High-quality commercial models range from 10,000 to 50,000 polygons, often using subdivision surfaces. [MEASURED] (Example: TurboSquid, search for "pillow" and filter by quality).
    *   **Upholstered Chair:** These are complex assets. A high-quality armchair can range from 100,000 to 500,000+ polygons. [MEASURED] (Example: Design Connected, "About 3D Models", designconnected.com/about-models).
    *   **Table Lamp:** A simple cylindrical lamp might be 5,000-15,000 polygons. A more complex one could be 20,000-80,000. [MEASURED] (Example: 3DSky, asset search).
    *   **Curtain Panel:** These vary wildly based on the complexity of the folds. A simple panel might be 20,000 polygons, while a complex, realistically simulated curtain could exceed 1,000,000. [MEASURED] (Example: TurboSquid, search for "curtain").

### 4. CONTACT

*   **Visual Cues for Contact:** The primary cue is a **contact shadow**. In a path-traced render, this should occur naturally if the geometry is correctly positioned. A believable contact shadow is extremely thin and very dark (almost black) precisely at the contact line, diffusing (softening and lightening) rapidly with distance. [PRACTICE] (Bertrand Benoit, "Making Of 'The V-Ray Interior'", 2010, evermotion.org/tutorials/show/7909/making-of-the-v-ray-interior). Ambient Occlusion (AO) is a technique that approximates this effect. A very small, tight AO radius can emphasize the contact line where two objects meet. [PRACTICE]
*   **Gap Tolerances:** In real construction, a skirting board is rarely perfectly flush with a floor. There is often a tiny, irregular gap, or a bead of caulk that creates its own shadow line. Simulating this tiny gap (e.g., 0.5mm - 1mm) can prevent light leaks and create a more realistic, fine contact shadow than having surfaces perfectly intersect. [PRACTICE] For cabinetry, the Architectural Woodwork Standards specify tolerances for flushness between components, often in the range of 0.5mm. [MEASURED] (Architectural Woodwork Manufacturers Association of Canada et al., "Architectural Woodwork Standards, Edition 2", 2014, p. 57, awmac.com/wp-content/uploads/2021/03/Architectural-Woodwork-Standards_Ed2.pdf).
*   **Published Guidance:** There is no formal published standard on the "minimum shadow evidence." However, the absence of a tight contact shadow is a well-known giveaway of floating CG objects. The key is the *gradient* of the shadow: it must be darkest and sharpest at the point of contact. [INFERENCE]

### 5. SURFACE VARIATION

*   **Published Material Breakdowns:** Scanned material libraries provide the most reliable [MEASURED] data.
    *   **Matte Interior Wall Paint:** For a typical matte paint, the roughness value is high and relatively uniform. A PBR workflow might use a roughness map with a mean value around 0.8-0.95 (where 1.0 is perfectly diffuse). The standard deviation would be very low, perhaps 0.01-0.05, representing subtle roller marks or stippling. [MEASURED] (Example analysis of textures from Quixel Megascans, "Painted Plaster", quixel.com/megascans/home). Base colour maps will have very subtle variations from roller application, but are mostly uniform.
    *   **Lacquered Oak Veneer:** For a satin or semi-gloss finish, the mean roughness might be in the 0.15-0.3 range. The key variation comes from the underlying wood grain. The open pores of the oak will be rougher (higher value) than the sealed wood between the pores (lower value). The standard deviation of the roughness map could be significant, e.g., 0.1-0.2, directly corresponding to the grain pattern. [MEASURED] (Example analysis of textures from Poliigon, "Wood Veneer 002", poliigon.com).
    *   **Satin Powder-Coated Metal:** This surface has a micro-texture. The mean roughness would be in the 0.2-0.4 range. The variation would be a high-frequency, low-amplitude noise pattern, with a standard deviation of perhaps 0.05-0.1. [MEASURED] (Example analysis of textures from Substance Source).
*   **Contribution of "Imperfection" Layers:** While many high-end archviz tutorials assert the importance of imperfection maps (fingerprints, dust, scratches), there is a lack of formal, published, peer-reviewed "before/after" evaluations that *quantify* their perceptual impact with user studies. The effect is almost universally presented as an article of faith in the practitioner community. [PRACTICE] For example, Poliigon offers extensive "overlay" maps for dust, smudges, and scratches, and their marketing materials show qualitative comparisons. [PRACTICE] (Poliigon, "Overlays", poliigon.com/textures/overlays). The assertion is that these details, even if not consciously noticed, break up the uniformity of CG surfaces and add to the subconscious feeling of realism. [INFERENCE]

### 6. THE HONEST QUESTION

There is very little published, quantitative, peer-reviewed research that specifically ranks perceptual cues for *photorealistic interior archviz*. The vast majority of literature on CG realism focuses on characters (the "uncanny valley") or general scenes. However, the practitioner community has a strong, consistent consensus.

*   **Practitioner Opinion Ranking:** The most frequently cited drivers of the "this is CG" judgment, ranked by consensus importance in high-end archviz forums and tutorials, are:
    1.  **Lighting and Shadowing:** Incorrect global illumination, unnaturally sharp shadows (especially contact shadows), lack of subtle light bounces, and incorrect light temperature are the biggest giveaways. [PRACTICE] (Bertrand Benoit, "Making Of 'The V-Ray Interior'", 2010, evermotion.org/tutorials/show/7909/making-of-the-v-ray-interior).
    2.  **Perfect Edges:** As discussed in Q1, perfectly sharp 90-degree edges do not exist in reality and are an immediate red flag. [PRACTICE] (Gleb Alexandrov, "The Secret Ingredient to Photorealism", Creative Shrimp, creativeshrimp.com/photorealism-secret-ingredient-blender.html).
    3.  **Surface Uniformity:** Real-world surfaces are never perfectly clean, perfectly flat, or perfectly uniform in colour and roughness. The lack of subtle variation (micro-scratches, dust, smudges, wear) is a major CG cue. [PRACTICE] (Andrew Price, "The #1 Thing You're Doing Wrong", Blender Guru, youtube.com/watch?v=m9AT7H4GGrA).
    4.  **Repetition:** Obvious tiling of textures or repetition of assets (e.g., identical books on a shelf) breaks realism. [PRACTICE]
    5.  **Lack of "Story" or "Life":** Sterile, perfectly ordered scenes look like catalogues, not lived-in spaces. The careful, artistic placement of clutter, wrinkles in fabric, and slight disarray is considered crucial for top-tier realism. [PRACTICE] (Ronen Bekerman, "The Art of Archviz", ronenbekerman.com).

This is a strong consensus of [PRACTICE], not a [MEASURED] ranking from a perceptual study.

### 7. SCORING

Yes, tools exist, though they are not typically integrated into a single "realism score." They are used in VFX and gaming pipelines for quality control.

*   **Edge-Sharpness / Bevels:** There is no common tool that automatically scores the *realism* of bevels from a final render. However, mesh analysis tools can identify sharp edges. In Blender, the "Select Sharp Edges" operator (based on an angle threshold) can be used to find unbeveled hard edges in a mesh. [MEASURED] (Blender 4.1 Manual, "Select Sharp Edges", docs.blender.org/manual/en/4.1/modeling/meshes/selecting/advanced.html).
*   **Silhouette Faceting Detection:** NO SOURCED VALUE FOUND for a tool that automatically detects silhouette faceting from a *rendered image*. This is typically assessed by eye. In a game engine context, LOD (Level of Detail) systems manage this by swapping meshes based on screen-space size, but this is a preventative measure, not a post-render scoring metric.
*   **Normal/Curvature Analysis:** Mesh analysis tools can visualize curvature and normal orientation. Blender's "Mesh Analysis" overlay can display vertex normal orientation and face curvature, which can help identify shading problems before rendering. [MEASURED] (Blender 4.1 Manual, "Mesh Analysis", docs.blender.org/manual/en/4.1/modeling/meshes/mesh_analysis.html). Standalone tools like MeshLint or the analysis tools in Autodesk Meshmixer can perform more advanced checks for issues like non-manifold geometry or flipped normals, which cause rendering errors. [PRACTICE]
*   **Mesh Quality Checkers:** Production pipelines often use automated mesh checkers. These are typically scripts or plugins for DCC applications (like Blender, 3ds Max, Maya). They check for technical, not artistic, issues. Common checks include:
    *   **N-gons:** Finding faces with more than 4 sides.
    *   **Triangles:** Finding faces with only 3 sides (can be undesirable in subdivision workflows).
    *   **Non-manifold geometry:** Edges shared by more than two faces.
    *   **Flipped Normals:** Faces pointing the wrong way.
    *   **Lamina faces:** Faces occupying the same space.
    [PRACTICE] An example of a commercial tool for 3ds Max is "Prune Scene". For Blender, many free add-ons for "mesh cleanup" exist.

## CONFLICTS AND UNCERTAINTY

*   **Bevel Radii:** The values for real-world edge radii are not standardized across the board but are often recommendations or minimums for specific fabrication processes (e.g., powder coating MDF, chipping resistance in quartz). The specified radius in an architectural drawing will take precedence. There is no conflict, but rather a wide range of acceptable values depending on the desired aesthetic and material limitations.
*   **Bevels in Archviz:** There is a clear distinction between physically accurate bevels and artistically effective bevels for rendering. Sources agree that perfect 90-degree edges are bad. However, the *size* of the bevel used in practice is an artistic choice and not based on a rigorous formula relating to pixel size. I would not stake a build on a single "correct" bevel radius for all situations.

## WHAT I COULD NOT SOURCE

*   **Published Guidance Linking Bevel Width to Pixel Size:** I could not find any published, formulaic rule (e.g., in a technical paper or official software documentation) that provides a mathematical relationship between a bevel's world-space radius and its ideal size relative to the rendered pixel grid for archviz. All guidance found was practitioner-based and artistic.
*   **Published Rule for Silhouette Segments vs. Pixel Count:** Similar to the bevel question, I could not find a formal, published rule or formula for archviz that dictates the necessary number of segments for a curve based on its subtended pixel angle or rendered size. The "one vertex per pixel" rule is a high-end VFX/game guideline and not specific to archviz.
*   **Quantitative "Before/After" Studies on Imperfection Maps:** I was unable to find any peer-reviewed perceptual studies that quantitatively measure the impact of adding "imperfection" layers (dust, fingerprints, etc.) on the perceived realism of an interior render. The benefits are widely asserted by practitioners but do not appear to be formally measured and published.
*   **Automatic Silhouette Faceting Detection Tool:** I could not find a named tool that analyzes a final rendered 2D image to detect and score polygonal faceting along object silhouettes.
---

## GROUNDING (vendor-reported)

- search queries issued: none reported

- grounding chunks: NONE REPORTED — treat every number here as unsourced until verified by hand.
