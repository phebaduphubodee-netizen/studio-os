# DR — integrating an acquired third-party mesh into a decided palette

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `1277ca41-b2bd-48b6-9a32-262bf73fe864` "Acquired-mesh integration into a decided palette" |
| turn | 1 (first ask after the sources settled) |
| fired | 2026-08-10 |
| sources | 86 imported, 77 ready, 9 error |
| asked because | the vault returned **NO COVERAGE** on this question (knowledge-manager sweep, 2026-08-10) while P2a/P2f were placing this lane's first acquired mesh |
| consumed by | `pipeline/scripts/build_room.py` (`_normalise_acquired`, and the keep-vs-replace branch of the acquire path) · `pipeline/scripts/asset_scale.py` (`pbr_map_roles`, `carries_a_pbr_surface`) |

## The first firing returned ZERO sources, and that is part of the record

Asked narrow — "how do studios reconcile an incoming model's PBR materials with a
decided palette" — Google's DR returned an empty set. Re-fired as a BROAD topic
("how do archviz studios prepare and integrate third-party models: asset library
workflows, material standardisation, cleanup, UVs, units") it returned 86 sources.
**DR retrieves against a TOPIC, not against a question.** The wrapper's own recovery
menu says so; this is a second data point for it.

## Source mix, stated before anything here is believed

55 vendor/article, 21 forum or community, 10 docs/wiki. This studio has already
recorded one DR that fabricated prices and licences, so the shape of the pool is part
of the answer: a number from a forum post is weaker than one from tool documentation,
and every citation below is resolved to its title so the difference is visible.
Citation [1] resolves to a forum post whose cited text is the single word "Cheers!" —
the marker is real; the substance behind that one is not.

## What was ALREADY TRUE in our code before this arrived

Recorded so the DR is not credited with work it did not do:

* Our retint already disconnects the Base Color link and leaves the Roughness and
  Normal links untouched — which is exactly this answer's §2.
* The keep-vs-replace rule shipped an hour BEFORE this answer, and it was derived from
  measuring our own two shelves rather than from the DR: Poly Haven assets carry normal
  + metallic-roughness maps, 3D Warehouse assets carry base colour only
  (`asset_scale.pbr_map_roles`). The DR's §1 is compatible and adds a criterion we did
  not have — hero/foreground versus background — which our vanity chair satisfies.

## What it CHANGED

`_normalise_acquired`: weld split vertices at 0.01 mm, then shade smooth while keeping
genuine hard edges sharp — straight from §4 "Shading Normals and Smoothing". On the
first acquired mesh it welded **4,652 split vertices**: the mesh was split at every
face, which is why its curved rim rendered as facets.

## What is NOT adopted, and why

* **The 3ds Max / Revit unit ritual** (§4, units) — we ingest glTF and assert scale on
  every import already; that procedure is for a toolchain we do not run.
* **Texel-density targets** (2048-4096 px/m hero, 200-512 px/m props) — real and
  citable, but we have no texel-density instrument, and adopting a number we cannot
  measure is how a threshold becomes decoration.
* **Polygon budgets** (500-5,000 tris for background props) — our acquired chair is
  2,440 polys, inside the band; but it is a games-pipeline number and this is a still.
  Recorded, not enforced.
* **The albedo band** (whites below **240 sRGB**, darks above **30-50 sRGB**) is the
  most directly checkable number here, and our `albedo_plausible()` currently allows up
  to ~249 sRGB. Deliberately NOT changed in this commit: moving a threshold is its own
  decision with its own A/B, and slipping one in beside unrelated work is how the nine
  flattering scorers happened.

---

## The answer as returned, every [n] resolved to its source

### 1. Keep vs. Strip: Deciding Asset Material Treatment
Studios assess several technical and production factors when deciding whether to **keep** a downloaded asset's incoming texture set or **strip** it to apply the studio's own calibrated library shaders:

*   **When to KEEP the incoming texture set:**
    *   **Tight Deadlines:** If the project is on a tight deadline and the artist wants to save time by avoiding complete rebuilding or manual remodeling [Archviz workflow, how does it go? - Reddit].
    *   **Distance from Camera (Background Props):** If the model is a standard environment or background asset that will only be seen from far away, where high optimization isn't as critical as it is for first-person or close-up models [3D Asset Workflow: UV Mapping - Frozenbyte Wiki; Standardized Asset Integration and Pipeline Calibration in].
    *   **PBR Technical Compliance:** If the asset’s textures are pre-calibrated to physically based standards—specifically keeping albedo whites strictly below **240 sRGB** and darks above **30–50 sRGB** [Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe; Confusion about albedo in color and textures - Keeping con]—and render accurately under default level **1.0** [Confusion about albedo in color and textures - Keeping con].
*   **When to STRIP and apply studio materials:**
    *   **Hero Foreground Assets:** If the asset is a foreground "hero" prop where close-up shots require complex physically accurate behaviors (such as subsurface scattering for white marble [8 Key Architectural Visualization Tips for 2026 | VirtualT; Stone Textures for Archviz: 2026 Reference Guide - Texture], anisotropic reflections on metals [PBR Materials for Architectural Rendering: A Practical Gui; Stone Textures for Archviz: 2026 Reference Guide - Texture], or micro-roughness detailing [8 Key Architectural Visualization Tips for 2026 | VirtualT; Enscape vs V-Ray: A Complete Rendering Comparison Guide]).
    *   **Non-Physical / Uncalibrated Data:** If the incoming textures violate the laws of energy conservation (e.g., containing pure whites of **255 sRGB** or baked-in lighting and shadows in the diffuse map), which slows down renders and washes out scene structures [PBR Materials for Architectural Rendering: A Practical Gui; Standardized Asset Integration and Pipeline Calibration in].
    *   **Platform/Render Engine Mismatches:** If the asset is imported from CAD or Revit where default materials convert poorly or render completely black in production engines like V-Ray [Revit to Max Workflow - CAD Software - CGarchitect Forums].
    *   **Topology and Viewport Lag:** If the model's geometry or hierarchy is unoptimized (such as having dozens of heavy multimat layers [Revit to Max Workflow - CAD Software - CGarchitect Forums]), stripping the materials and remodeling from scratch in a DCC tool ensures clean, organized group structures [Archviz workflow, how does it go? - Reddit].

---

### 2. Re-Tinting Albedo Without Destroying Roughness and Normals
Because modern PBR pipelines handle color and data maps through completely separate channels, you can easily alter the color of an asset without degrading its micro-surface details [An Idiot's Guide to ACES – Toadstorm Nerdblog; Standardized Asset Integration and Pipeline Calibration in]. 

**The Node Setup and Workflow:**
1.  **Differentiate Color and Data Spaces:** Set the **Albedo/Diffuse map** to load in **sRGB color space** [An Idiot's Guide to ACES – Toadstorm Nerdblog; Standardized Asset Integration and Pipeline Calibration in]. Crucially, make sure your **Roughness** and **Normal maps** are imported in **Linear (Non-Color) space** so their mathematical details bypass color transformations [An Idiot's Guide to ACES – Toadstorm Nerdblog; Standardized Asset Integration and Pipeline Calibration in].
2.  **Insert the Correction Node:** Place a color correction node (such as a **CoronaColorCorrect** map in 3ds Max [Confusion about albedo in color and textures - Keeping con; One Texture, Full Material | Corona Renderer 3ds Max Tutor], a **Material Color Blend** node in Substance [Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe], or a standard Hue/Saturation/Value shift node) directly between the Albedo file output and the shader's diffuse input.
3.  **Adjust the Color Parameters:** Adjust the Hue, Saturation, and Exposure/Brightness sliders to reach the target tint [Confusion about albedo in color and textures - Keeping con; One Texture, Full Material | Corona Renderer 3ds Max Tutor]. Keep the final brightness range verified within PBR limits (whites ≤ 240 sRGB, darks ≥ 30–50 sRGB) [Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe; Standardized Asset Integration and Pipeline Calibration in].
4.  **Connect directly to the Shader:** Plug the output of this correction node into your shader's **Base Color / Diffuse Color** slot [Mastering PBR Materials | Babylon.js Documentation; PBR Texture Maps Explained – Albedo, Normal, Roughness, Me]. Connect the untouched, Linear-space **Roughness** and **Normal maps** directly into their native slots (Roughness/Glossiness and Normal/Bump) [An Idiot's Guide to ACES – Toadstorm Nerdblog; PBR Texture Maps Explained – Albedo, Normal, Roughness, Me]. The shader will calculate light scatter correctly based on the new base color while preserving every scratch and normal detail [An Idiot's Guide to ACES – Toadstorm Nerdblog; Confusion about albedo in color and textures - Keeping con].

---

### 3. The Visual "Tells" of a Disconnected Imported Asset
When an imported model is poorly integrated, several distinct visual errors immediately reveal its digital nature:

*   **Excessive/Uncalibrated Brightness (Glowing):** If the albedo exceeds physical limits (e.g., pure 255 sRGB white), the material violates energy conservation [Standardized Asset Integration and Pipeline Calibration in]. This results in an unrealistic, "glowing" appearance and excessive light bounces that flatten shadows [Standardized Asset Integration and Pipeline Calibration in; Confusion about albedo in color and textures - Keeping con; Lookdev: What It Actually Means and How Production Does It].
*   **Flat Specular Response:** Every surface on the asset responds identically to the daylight, showing a total lack of roughness variation or edge penumbra [8 Key Architectural Visualization Tips for 2026 | VirtualT].
*   **"Plastic" Metals:** Metals (such as aluminum cladding or brass) appear like shiny plastic because their metallic mask isn't set to **1.0** [PBR Materials for Architectural Rendering: A Practical Gui; PBR Texture Maps Explained – Albedo, Normal, Roughness, Me], or because their specular glossiness lacks a subtle, varied roughness map [PBR Materials for Architectural Rendering: A Practical Gui].
*   **Fresnel Violations at Grazing Angles:** The model fails to become more reflective at glancing/grazing angles [Lookdev: What It Actually Means and How Production Does It]. Smooth dielectrics must reflect nearly **100%** at grazing angles while staying down at **2% to 5%** perpendicular to the camera [Mastering PBR Materials | Babylon.js Documentation].
*   **Texel Density Mismatches:** The asset appears noticeably blurry or muddy next to a highly detailed, sharp foreground surface (or vice versa), revealing inconsistent resolution targets [Standardized Asset Integration and Pipeline Calibration in; Texel Density - Foundry Learn].
*   **Obvious Tiling Repetition:** A repetitive sediment grid or distinct blemish repeating infinitely across the mesh surface (such as "leopard spots" on a sandstone panel) [Stone Textures for Archviz: 2026 Reference Guide - Texture].
*   **Shading Gradients and Pinching:** Discarding explicit vertex normals during DCC editing creates dark shading gradients, weird smoothing, and corner faceting [Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe; Standardized Asset Integration and Pipeline Calibration in].
*   **Edge Halos (Fringes):** Low map resolutions or poor UV scaling produce ugly white or black edge fringes in the transitional spaces between metallic and dielectric parts [Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe].
*   **Geometry Glitches:** Overlapping coplanar surfaces creating flickering/shimmering artifacts in motion [Revit and 3ds Max Workflows Using Iray for Realistic Rende], visible light leaks in dropped ceiling seams [Revit and 3ds Max Workflows Using Iray for Realistic Rende], or random black spots due to inverted normals and split edges [3D Max Retopology: What It Is and when It's Necessary - CG; 3dsMax 2021.3 Retopology Modifier Quick Start – Part.2 - C].

---

### 4. Studio Mesh Normalisation Checklist
Before any third-party mesh enters the master environment, it must pass this normalization checklist:

#### ☐ Units and Scale Calibration
*   Verify the asset is built to **1:1 real-world scale** against standard dimensional cues (e.g., a door leaf should measure ~2.1 meters) [8 Key Architectural Visualization Tips for 2026 | VirtualT; Enscape vs V-Ray: A Complete Rendering Comparison Guide].
*   To prevent scale offsets from breaking modifiers (like chamfers or UV maps) when importing Revit FBX files into millimeter DCCs [Standardized Asset Integration and Pipeline Calibration in]:
    1.  Initialize a clean scene with global System Units set to **Feet** (\\(1\text{ Unit} = 304.8\text{ mm}\\)) and disable "respect system units in files" [Standardized Asset Integration and Pipeline Calibration in].
    2.  Import the FBX with "automatic units" disabled, forcing the file units to **Feet** (locking the scale factor to 1.0) [Standardized Asset Integration and Pipeline Calibration in].
    3.  Save the scene as a temporary database file and reset the workspace [Standardized Asset Integration and Pipeline Calibration in].
    4.  Set System Units to millimeter standards (\\(1\text{ Unit} = 1.0\text{ mm}\\)), re-enable "respect system units" [Standardized Asset Integration and Pipeline Calibration in].
    5.  **Merge** the intermediate file to scale the geometry to its true size without scale-matrix offsets [Standardized Asset Integration and Pipeline Calibration in].

#### ☐ Shading Normals and Smoothing
*   Run automated diagnostic tools (e.g., 3ds Max *Mesh Cleaner* or Rhino *CheckMesh*) to catch non-manifold edges, naked boundaries, and degenerate faces [Standardized Asset Integration and Pipeline Calibration in].
*   Weld split vertex boundaries along smooth regions using a tight threshold (**0.001 mm to 0.01 mm**) [Standardized Asset Integration and Pipeline Calibration in], keeping sharp edges unwelded to preserve clean corners [Standardized Asset Integration and Pipeline Calibration in; Rhino 3D Tip: Scan Mesh Cleanup and Retopology Workflow fo].
*   Run normal unification and enable **backface coloring** in the viewport to identify and correct inverted polygons [Standardized Asset Integration and Pipeline Calibration in; Rhino 3D Tip: Scan Mesh Cleanup and Retopology Workflow fo].
*   **Lock explicit vertex normals** on imported CAD files to prevent DCC software from recomputing smoothing groups and creating shading gradients [Standardized Asset Integration and Pipeline Calibration in].

#### ☐ UVs and Texel Density Target
*   Check that there is **only one UV set** in the file, named exactly **"map1"** (critical for animators and riggers) [3D Asset Workflow: UV Mapping - Frozenbyte Wiki].
*   Set a dedicated **UV seam** on every hard edge to prevent baking artifacts [3D Asset Workflow: UV Mapping - Frozenbyte Wiki]. Keep seams aligned with corners and hidden away from important viewing angles [UV Layout Best Practices — Omniverse SimReady; What is UV Mapping in Architectural Texture Rendering?].
*   Enforce **non-overlapping shells** and restrict coordinates to **UV Channel 1** [UV Layout Best Practices — Omniverse SimReady].
*   Straighten cylindrical islands horizontally/vertically to prevent diagonal texture aliasing [UV Layout Best Practices — Omniverse SimReady].
*   Normalize UVs using a density tool to match targets [Standardized Asset Integration and Pipeline Calibration in] based on camera distance:
    *   *Hero Foreground:* **2048 px/m to 4096 px/m** [Standardized Asset Integration and Pipeline Calibration in].
    *   *Midground Structure:* **512 px/m to 1024 px/m** [Standardized Asset Integration and Pipeline Calibration in].
    *   *Standard Environment/Props:* **200 px/m to 512 px/m** [Standardized Asset Integration and Pipeline Calibration in].
    *   *Background Vistas:* **50 px/m to 128 px/m** [Standardized Asset Integration and Pipeline Calibration in].

#### ☐ Material Naming Conventions
*   Standardize names using a clear prefix system (e.g., `SM_` for static mesh [Unreal Engine 3D modeling: a practical pipeline guide - Ga], `MAT_` for materials [Enscape vs V-Ray: A Complete Rendering Comparison Guide]) and add model-specific descriptive suffixes (e.g., `_mat` [3D Asset Workflow: UV Mapping - Frozenbyte Wiki] or `Concrete_Precast_GreyFinish` [Unreal Engine BIM Workflows: Turning Revit Models Into Str]).
*   Avoid generic material assignments (such as "Material #1" or "Concrete") to stop import plugins from merging unrelated surfaces [Unreal Engine BIM Workflows: Turning Revit Models Into Str].
*   Audit the mesh for missing materials; objects without assigned materials default to "Generic", leading to rendering errors [Revit and 3ds Max Workflows Using Iray for Realistic Rende].

#### ☐ Polygon Budget Verification
*   Audit mesh density against cross-platform target budgets [Unreal Engine 3D modeling: a practical pipeline guide - Ga]:
    *   *Hero Cinematic/Console Skeletal Assets:* **80,000–150,000 tris** [Unreal Engine 3D modeling: a practical pipeline guide - Ga].
    *   *Gameplay Characters:* **30,000–60,000 tris** [Unreal Engine 3D modeling: a practical pipeline guide - Ga].
    *   *Background Props:* **500–5,000 tris** [Unreal Engine 3D modeling: a practical pipeline guide - Ga].
    *   *Foliage Card / Billboard:* **50–500 tris** [Unreal Engine 3D modeling: a practical pipeline guide - Ga].
*   Use `ReduceMesh` or retopology solvers (like 3ds Max *ReForm*) to reconstruct triangulated wireframes into quad-dominant structures [Rhino 3D Tip: Scan Mesh Cleanup and Retopology Workflow fo; Standardized Asset Integration and Pipeline Calibration in].
*   Delete micro-components or floating scan debris below a threshold size using selection filters like `SelSmall` [Standardized Asset Integration and Pipeline Calibration in; Rhino 3D Tip: Scan Mesh Cleanup and Retopology Workflow fo].

#### ☐ Pivot Placement & Scene Structure
*   Group assets strategically by design layers (flooring, millwork, ceilings) to maintain efficient memory and re-import handling [3dsMax and Datasmith export vs. standard FBX approach - Pi; Standardized Asset Integration and Pipeline Calibration in].
*   Enable model origin helpers during file linking to stabilize scene assemblies [Standardized Asset Integration and Pipeline Calibration in; Revit and 3ds Max Workflows Using Iray for Realistic Rende].

---
📊 I can generate a structured, print-ready PDF checklist of this normalization pipeline so your artists have a quick reference guide on their local machines.

---

## Sources cited above

- Archviz workflow, how does it go? - Reddit — https://www.reddit.com/r/archviz/comments/1gwnvml/archviz_workflow_how_does_it_go/
- 3D Asset Workflow: UV Mapping - Frozenbyte Wiki — https://wiki.frozenbyte.com/index.php/3D_Asset_Workflow:_UV_Mapping
- 8 Key Architectural Visualization Tips for 2026 | VirtualTourEasy — https://virtualtoureasy.com/articles/architectural-visualization-tips/
- Standardized Asset Integration and Pipeline Calibration in Professional Architectural Visualization
- Learn Substance 3D Designer The PBR Guide - Part 2 - Adobe — https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2
- Confusion about albedo in color and textures - Keeping consistency - Corona for 3ds Max :: Help Required - Chaos Forum — https://forums.chaos.com/t/confusion-about-albedo-in-color-and-textures-keeping-consistency/157510
- Lookdev: What It Actually Means and How Production Does It - CG Lounge — https://cglounge.studio/journal/lookdev-the-technical-guide
- Stone Textures for Archviz: 2026 Reference Guide - TextureX — https://texturex.com/stone-textures-archviz-reference-guide-2026
- PBR Materials for Architectural Rendering: A Practical Guide - Archfine — https://archfine.com/rendering-techniques/pbr-materials-architectural-rendering
- Enscape vs V-Ray: A Complete Rendering Comparison Guide — https://www.archivinci.com/blogs/enscape-vs-vray-comparison-guide
- Revit to Max Workflow - CAD Software - CGarchitect Forums — https://forums.cgarchitect.com/topic/38212-revit-to-max-workflow/
- An Idiot's Guide to ACES – Toadstorm Nerdblog — https://www.toadstorm.com/blog/?p=694
- One Texture, Full Material | Corona Renderer 3ds Max Tutorial - YouTube — https://www.youtube.com/watch?v=fzpheIi5-78
- Mastering PBR Materials | Babylon.js Documentation — https://doc.babylonjs.com/features/featuresDeepDive/materials/using/masterPBR
- PBR Texture Maps Explained – Albedo, Normal, Roughness, Metallic, ORM | AITEXTURED — https://aitextured.com/articles/pbr_texture_maps_explained_albedo_normal_roughness_metallic_orm.html
- Texel Density - Foundry Learn — https://learn.foundry.com/modo/content/help/pages/uving/texel_density.html
- Revit and 3ds Max Workflows Using Iray for Realistic Rendering - Autodesk — https://static.au-uw2-stg.autodesk.com/handout_9960_2015-AV9960-IRayWorkflows.pdf
- 3D Max Retopology: What It Is and when It's Necessary - CGIFurniture — https://cgifurniture.com/blog/3d-max-retopology-for-furniture-visualization/
- 3dsMax 2021.3 Retopology Modifier Quick Start – Part.2 - Changsoo Eun — https://cganimator.com/3dsmax-2021-3-retopology-modifier-quick-start-part-2/
- Rhino 3D Tip: Scan Mesh Cleanup and Retopology Workflow for Rhino | NOVEDGE Blog — https://novedge.com/blogs/design-news/rhino-3d-tip-scan-mesh-cleanup-and-retopology-workflow-for-rhino
- UV Layout Best Practices — Omniverse SimReady — https://docs.omniverse.nvidia.com/simready/latest/simready-asset-creation/uv-best-practices.html
- What is UV Mapping in Architectural Texture Rendering? — https://www.archivinci.com/blogs/uv-mapping-in-texture-rendering
- Unreal Engine 3D modeling: a practical pipeline guide - Game-Ace — https://game-ace.com/blog/unreal-engine-3d-modeling-a-step-by-step-guide/
- Unreal Engine BIM Workflows: Turning Revit Models Into Streamable, Interactive 3D — https://www.eagle3dstreaming.com/blog/unreal-engine-bim-workflows-turning-revit-models-into-streamable-interactive-3d
- 3dsMax and Datasmith export vs. standard FBX approach - Pipeline & Plugins — https://forums.unrealengine.com/t/3dsmax-and-datasmith-export-vs-standard-fbx-approach/120470
