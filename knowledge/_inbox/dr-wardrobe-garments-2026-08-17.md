# DR — wardrobe garment fills — how delivered renders stock an open closet (fired late in the 08-17 batch, completed 08-18)

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `6cac307d-83f2-4210-bba1-9b12994485a2 "DR: wardrobe garment fills 2026-08-17"` |
| conversation | `e8bb1b43-e484-4963-8b14-c3633e73d6c3`, turn 1 |
| fired | 2026-08-17, builder-initiated (owner order this session: "spend all DR on this" — the Blender craft gap) |
| sources | 69 imported, 64 ready, 5 error |
| asked because | flat-cutout wardrobe clothing filed by both critics in all five critique rounds; the stiffness lever was declared procurement (D-031) and never sourced; P2r-20's face-on-hang mechanism is R1-gated — this is DR trigger 1 (R1 stop names a mechanism mystery) plus trigger 4 (first build of a domain class done right). |
| consumed by | P2r-20 when it reopens as a NEW mechanism; the wardrobe fill's procurement ask (named packs with prices arm it); build_room.py garment staging (hanging lengths, palette discipline). Nothing consumes it yet at staging time. |

## Caveats stated before anything here is believed

Synthesised-self-source pattern present ("Production-Grade Methodologies for Populating Open Wardrobes..."); pack prices/licences quoted from vendor listing pages as captured — re-verify at checkout, and several Free3D rows carry licence NOT IN SOURCES so they fail R8's licence law until someone opens the page. The actionable core: capsule-wardrobe palette discipline (neutral colours, sorted by colour family then type then hanging length — the styling answer to rail composition, which the trade counts per COMPARTMENT: shirts 80 cm hang / 90 cm compartment, jackets 100/110, dresses 110); single-shell thin + thickness AFTER drape (double-shell sim refused, matches our cloth-stack-contact-law); the MD shape-key retopo pipeline and the Pin-Box hanger-slippage fix for a future MD lane (ASK-026, owner's money call); garments-per-meter and gap distribution honestly NOT IN SOURCES — measure from delivered dressing-room anchors (R4). Repetition threshold: recognisable garments repeat-detected across 5-6 views — variety count is a scene-level constraint, not per-rail.

## The answer as returned (source titles inline; [n] markers as returned)

### 1. SOURCING PRACTICE

*   **Sourcing Methods**: Professional architectural visualization studios fill open closets efficiently by balancing **bought garment packs**, **per-garment cloth simulation**, and **photogrammetry** [1, 2]. This hybrid approach is necessary because fully stocking a virtual closet manually can quickly become a **\\(20\times\\)** time sink (Source Title: *"Production-Grade Methodologies for Populating Open Wardrobes in Architectural Visualization"*) relative to standard scene staging [1, 2].
*   **Marketplaces & Sections**:
    *   **TurboSquid**: Dedicated sections like *"3D-Models/clothes-hanger"* (containing **2,909** models; Source Title: *"Download Free & Premium Clothes Hanger 3D Models | TurboSquid"*) and *"3D-Models/clothing"* (hosting over **100,000+** assets; Source Title: *"Download Free & Premium Clothing 3D Models | TurboSquid"*) are heavily utilized [1-4].
    *   **CGTrader**: Dedicated sections like *"3D-models/clothes-hanger"* (containing **27,550** models; Source Title: *"Clothes hanger 3D Models – Free & Premium Downloads | CGTrader"*) and *"3D-models/hanging-clothes"* (hosting **43,174** models; Source Title: *"Hanging clothes 3D Models – Free & Premium Downloads - CGTrader"*) are standard [1, 2, 5, 6]. 
    *   **CGMood**: For high-end styling, individual high-fidelity items (such as jackets, dresses, and bathrobes) are acquired on CGMood based on credit ratings of **3**, **4**, or **5 CREDITS** (Source Title: *"Hanging clothes 3D Models | CGMood"*) [1, 2, 7-9].
    *   **Free3D**: Labeled *"premium-3D-models/obj-hanger-clothes"* section [1, 2].
*   **Interactive Apps & Photogrammetry**:
    *   **VORTEK Spaces**: Real-time presentation tool featuring a live rendering capability supported by a free library of high-resolution, 3D-processed apparel, shoes, panels, and flooring from popular brands [10-13].
    *   **Photogrammetry**: Rarely used for modular wardrobes because photoscanning does not result in an assembly of parts, but instead creates a **single, watertight outer skin** (Source Title: *"Production-Grade Methodologies for Populating Open Wardrobes in Architectural Visualization"*), making it impossible to separate individual garments from hangers, slide items along a rail, or adjust their folding patterns [12, 13]. However, some practitioners do use individual **3D Scan assets** as "Obj to garment" simulation inputs because they are pre-welded and less likely to fall apart [14].
*   **Simulation Tools & Scene Packs**:
    *   **Simulation Tools**: Advanced 3D design packages most notably **Marvelous Designer**, **CLO3D**, and **Style3D** [15, 16].
    *   **Commercial Scene Packs**: Packages like Evermotion’s **Vol. 277 - Modern wardrobes** (Source Title: *"Evermotion | Vol. 277 - Modern wardrobes | Download free 3D models"*) ship with fully integrated, pre-staged wardrobes containing realistic clothes and organizer systems [15-17].

---

### 2. GARMENT MESH CONVENTIONS

*   **Shoulder Volume vs. Drape**: To pass visual review, virtual garments must project a **realistic volume** that mimics real-world drape and gravity rather than reading as a flat cutout [18, 19]. To establish realistic depth, clothing requires a complex interaction of fabric physics, curvature, and dimensional thickness [18, 19].
*   **Polycount Bands**: Viewport-manageable garment configurations generally remain **under 200k polygons (400k tris)** (Source Title: *"Inquiry: How many of you use Marvelous Designer? - Daz 3D Forums"*) [20]. Background assets are blocked out at a particle distance of **12-15** (Source Title: *"Creating Animation-Ready Clothes Simulation in Marvelous Designer - 80 Level"*), dropping to **10** or **5** for final simulation frames to capture detailed wrinkles without slowing down viewport performance [21-24].
*   **Single vs. Double Shell**: Workflows dictate simulating clothing as a **single-shell thin mesh** and adding thickness *after* the drape is finalized [25, 26]. Double-shell active simulation is avoided because it more than doubles final polycount, hurts viewport performance, and triggers severe intersection bugs/mesh explosions because physics engines treat closed objects as empty sacks [25, 26].
*   **Solidify & Hem Thickness**: Specific solidify and hem thickness values are **NOT IN SOURCES** [27, 28]. In Marvelous Designer, thickness is adjusted dynamically using the *"add'l thickness - rendering"* property, allowing artists to increase thickness by a **couple of mm** (Source Title: *"Garment layer thickness? : r/MarvelousDesigner - Reddit"*) and extruding in "Both", "Forward", or "Backward" directions [29-33].
*   **Workarounds for Texture Stretching**:
    1.  *Material Isolation and Re-Unwrapping*: Isolating extruded rim edge loops into a separate material zone in Blender, pinning the main UV coordinates, and re-unwrapping only the extruded hem margins [27, 28, 34].
    2.  *Tailored Fold Hems*: Creating a real-world fold-over pattern edge sewn to the inside face in Marvelous Designer [27, 28, 34]. To maintain simulation stability, the folded pattern piece must be modeled to a width that is at least equal to or wider than the average polygon size of the simulated mesh [27, 28, 34].
*   **Visual Separators at 2-4 m**: The specific visual separators distinguishing a realistic garment from a cutout at **2-4 m** are **NOT IN SOURCES** [18, 19].

---

### 3. RAIL COMPOSITION

*   **Garments per Meter of Rail**: **NOT IN SOURCES** [35, 36].
*   **Gap Distribution**: **NOT IN SOURCES** [35, 36].
*   **Orientation and Variety Mixing**: Styled wardrobes must avoid highly recognizable, trendy, or bright assets. Repeating recognizable clothing across **5-6** render views (Source Title: *"Diverse people, POC - Ideas Asset/Material Library - Chaos Forum"*) makes repetition obvious and distracts from the architecture [35-37].
*   **Colour/Palette Discipline**: Stylists design virtual closets as structured **"capsule wardrobes"** utilizing plain, neutrally colored clothing (basic slacks, button-up shirts, plain jeans, blouses, and skirts) [35-37]. Garments are sorted systematically **by color family first**, and then grouped by type and hanging length to maintain cohesion [35, 36, 38, 39].
*   **Clearance & Spacing Standards** (Source Title: *"Design your own wardrobe | Try our 3D wardrobe designer now"* unless noted otherwise):
    *   *Upper-Body Basics (Shirts, Pullovers, T-Shirts, Skirts, Pants)*: Hanging length of **80 cm** with a recommended compartment height of **90 cm** (including hangers) [40-42].
    *   *Jackets and Outerwear*: Hanging length of **100 cm** with a minimum compartment height of **110 cm** [40-42].
    *   *Medium-Length Dresses*: Hanging length of **110 cm** [40-42].
    *   *Bespoke Wardrobe Width*: Configurable up to **6 m** wide [40, 43, 44].
    *   *Bespoke Wardrobe Height*: Configurable up to **2.75 m** high [40, 43, 44].
    *   *Single-Wall Sliding Wardrobe*: Linear dressing width of **1.3 to 2.1 m** (Source Title: *"Online Wardrobe Planner - Design your closet in 3D | SCHMIDT"*) [43-45].
    *   *Single-Wall Open Dressing*: Linear dressing width of **1.8 to 3.1 m** (Source Title: *"Online Wardrobe Planner - Design your closet in 3D | SCHMIDT"*) [43-45].
    *   *Single-Wall Hinged Wardrobe*: Linear dressing width of **2.4 to 4.1 m** (Source Title: *"Online Wardrobe Planner - Design your closet in 3D | SCHMIDT"*) [43, 44, 46].
    *   *L-Shape Open Corner Dressing*: Corner dressing floor area of **6.8 m²** (Source Title: *"Online Wardrobe Planner - Design your closet in 3D | SCHMIDT"*) [43-45].
    *   *U-Shape Open Corner Dressing*: Corner dressing floor area of **8.8 m²** (Source Title: *"Online Wardrobe Planner - Design your closet in 3D | SCHMIDT"*) [43, 44, 46].
    *   *Assembly Gap*: Minimum **3 cm** clearance to sides and ceiling [43, 44, 47].
    *   *Fascia Board Height*: **0.25 cm** for premium decor or **0.28 cm** for real wood veneer [43, 44, 47].

---

### 4. KNOWN-GOOD PACKS

The following packs are detailed on vendor pages in the sources:

*   **Hanging Clothes Set Low Poly Game Ready** (Vendor Page: CGTrader):
    *   *Format*: `.blend`, `.dae`, `.obj`, `.fbx` [48, 49].
    *   *Polycount*: Low-poly / Game-ready [48, 50].
    *   *License*: Royalty Free License (no AI) [50].
    *   *Price*: **\$20.99** one-time purchase (**\$14.69** on sale) or Premium subscription starting from **\$1.40** per model [50].
    *   *Source Title*: *"3D model Hanging Clothes Set Low Poly Game Ready VR / AR / low-poly | CGTrader"* [50].
*   **Clothing Racks and Clothes Hangers Collection** (Vendor Page: TurboSquid):
    *   *Format*: `.max` (3ds Max [+5] format options) [51].
    *   *Polycount*: Low Poly [52].
    *   *License*: Enhanced Licenses or Non-editorial [52].
    *   *Price*: **\$59.00** [51].
    *   *Source Title*: *"Download Free & Premium Clothes Hanger 3D Models | TurboSquid"* [51].
*   **Clothes on Hangers Collection** (Vendor Page: TurboSquid):
    *   *Format*: `.max` (3ds Max [+5] formats) [53].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: Enhanced Licenses or Non-editorial [52].
    *   *Price*: **\$99.00** [53].
    *   *Source Title*: *"Download Free & Premium Clothes Hanger 3D Models | TurboSquid"* [53].
*   **Clothing for Wardrobe** (Vendor Page: TurboSquid):
    *   *Format*: `.max` (3ds Max [+2] formats) [54].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: Enhanced Licenses or Non-editorial [52].
    *   *Price*: **\$129.00** [54].
    *   *Source Title*: *"Download Free & Premium Clothes Hanger 3D Models | TurboSquid"* [54].
*   **Casual Mens Clothing 3D Model Set - Hanging and Folded** (Vendor Page: TurboSquid):
    *   *Format*: `.c4d` (Cinema 4D [+4] formats) [55].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: Enhanced Licenses or Non-editorial [52].
    *   *Price*: **\$28.00** [55].
    *   *Source Title*: *"Download Free & Premium Clothes Hanger 3D Models | TurboSquid"* [55].
*   **Wardrobe Essentials For Men** (Vendor Page: Free3D):
    *   *Format*: `.max`, `.fbx`, `.obj` [56].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: **NOT IN SOURCES**.
    *   *Price*: **\$99.00** [56].
    *   *Source Title*: *"Hanger Clothes 3D Models obj - .obj download - Page 4 - Free3D.com"* [56].
*   **Blouse on Hanger Low Poly** (Vendor Page: Free3D):
    *   *Format*: `.obj`, `.max`, `.fbx`, `.3ds` [57].
    *   *Polycount*: Low Poly [57].
    *   *License*: **NOT IN SOURCES**.
    *   *Price*: **\$10.00** [57].
    *   *Source Title*: *"Hanger Clothes 3D Models obj - .obj download - Page 4 - Free3D.com"* [57].
*   **Set of Clothes and Shoes** (Vendor Page: Free3D):
    *   *Format*: `.max`, `.fbx`, `.obj` [58].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: **NOT IN SOURCES**.
    *   *Price*: **\$49.00** [58].
    *   *Source Title*: *"Hanger Clothes 3D Models obj - .obj download - Page 4 - Free3D.com"* [58].
*   **Wooden coat hanger 2** (Vendor Page: Free3D):
    *   *Format*: `.blend`, `.fbx`, `.obj` [58].
    *   *Polycount*: **NOT IN SOURCES**.
    *   *License*: **NOT IN SOURCES**.
    *   *Price*: **\$5.00** [58].
    *   *Source Title*: *"Hanger Clothes 3D Models obj - .obj download - Page 4 - Free3D.com"* [58].

---

### 5. MARVELOUS DESIGNER FOR PROPS

*   **Practitioner Use**: Yes, architectural visualization studios regularly use Marvelous Designer for prop-level closet fills (such as simulating folded/hanging clothes, draping bathrobes, or casually tossing garments over chairs) [59, 60].
*   **MD-to-DCC Shape-Key Pipeline** (Source Title: *"Marvelous Designer to Blender - Mesh - Second Life Community"*):
    1.  *Export Simulated State*: Select simulated 3D garments and export as an OBJ with settings: *"Select All Patterns"* (no avatars), *"Single Object"*, *"Unweld"*, *"Thin"*, and *"Unified UV Coordinates"* [61, 62]. Import into Blender as "MD".
    2.  *Export Flat State*: Select *"Reset 2D Arrangement (Selected)"* in MD to flatten patterns [61, 62]. Export using the identical settings. Import into Blender as "MD-Flat".
    3.  *Retopology & Morphing*: Duplicate "MD-Flat", retopologize the flat shape using clean quads, and name it "Retopo" [61, 62]. Join "MD" to "MD-Flat" as a Shape Key ("Join as Shapes") set to 0. Apply a *Surface Deform* modifier on the "Retopo" mesh targeting "MD-Flat" as the deform source, and bind [61, 62]. Increase the shape key on "MD-Flat" to **1** to cleanly warp the retopologized quad mesh into the final draped shape [61, 62].
*   **Remeshing Options**: Property Editor Mesh Type can be set to "Quad" before export [63, 64]. Version **2024.2** (Source Title: *"Simulation – Marvelous Designer"*) features *"Quad (Optimized)"* for auto-retology and *"Quad (Grid)"* for forcing uniform grid layouts [63, 64].
*   **Simulation Quality Presets** (Source Title: *"Simulation – Marvelous Designer"*): *"Normal (Default)"* is fastest for initial layout [63, 64]; *"Animation (Stable)"* is for recording movements [63, 64]; *"Fitting (Accurate Fabric)"* is slowest but realistically expresses stretch and drape [63, 64].
*   **Critical Pitfalls & Mitigations**:
    *   *Seam-Loss Pitfall*: Welding on export deletes visually defined seams [23, 24]. Mitigation: Export in FBX format with *"Normal Map"* enabled under Unified UV Coordinates to bake seam details into the map [23, 24].
    *   *Thickness/Smoothing Pitfall*: Seams break in ZBrush when subdivision/smoothing higher than **2** (Source Title: *"Advice on Creating Thickness in Clothing - Daz 3D Forums"*) is applied to welded thick exports [23, 24, 65]. Mitigation: Isolate hem edge loops in Blender into separate material zones, pin UV coordinates, and unwrap only the extruded margins [23, 24, 34].
    *   *GPU Simulation Puffiness*: GPU-based simulation can make garments look unnaturally puffy [23, 24]. Mitigation: Position garments quickly using the GPU engine, then switch the simulator back to CPU for **1 to 2 minutes** (Source Title: *"Inquiry: How many of you use Marvelous Designer? - Daz 3D Forums"*) to finalize realistic folds [20, 23, 24]. Block background assets at a particle distance of **12-15** and only drop to **10** or **5** for the final frame to avoid viewport lag [22-24].
    *   *Hanger Slippage*: Fabric slips off hangers due to gravity [23, 24]. Mitigation: Use the *"Pin Box"* brush tool to apply static pins along shoulders and collars in non-simulation mode [23, 24]. These serve as non-destructive staging tools as they do not render [23, 24].

🧩 We could compile this retopology and thickness workflow into a custom PDF cheat-sheet if you want an easy reference guide to keep on your secondary monitor while modeling.
