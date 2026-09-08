# DR — veneer per-panel variety + anti-tiling authoring recipes (the fix lane for the ~200 px repeat)

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `bedcb991-c431-4a2b-a5b9-9857143a67b5 "DR: veneer variety + anti-tiling authoring 2026-08-17"` |
| conversation | `0a50a0c7-4b07-438e-929b-a4323e759826`, turn 1 |
| fired | 2026-08-17, builder-initiated (owner order this session: "spend all DR on this" — the Blender craft gap) |
| sources | 100 imported, 82 ready, 18 error |
| asked because | P2r-2's instrument robustly measures a ~198-202 px periodic repeat (0.829 peak vs 0.444 floor) that survived two mapping fixes; the vault held only the DETECTOR vocabulary (MA-03) and leaf geometry (152-305 mm, center-balance) but no authoring recipe for making adjacent panels DIFFER — declared gap in veneer-figure-and-panel-layout.md §5 and in the vault-coverage sweep. |
| consumed by | build_room.py veneer mapping (P2r-2's named fix: per-panel offset/rotation — now with parameter bands: 180-degree rotation step for directional wood, ~2.5% hue/sat/gamma jitter, 4-8 distinct leaf sets, Random-Per-Island + White Noise node recipe); edge-band/arris geometry for P2r-10. Nothing consumes it yet at staging time. |

## Caveats stated before anything here is believed

Synthesised-self-source pattern again ("Tectonic and Computational Frameworks for Mitigating Pattern Repetition in Wood-Veneer Wall Visualizations") co-signing most items; real co-cites are strong here (AWI 3.3/3.4 aesthetic standards, ANSI/WDMA IS-1A, Oregon Door, Poliigon blog, V-Ray/Corona docs, Bertrand Benoit's Floor Generator walkthrough). Engine-specific jitter numbers (V-Ray scale 10-150%, VRayEnmesh Hue 5/Sat 3/Gamma 8; Corona hue/sat/gamma ~2.5%) port to Cycles as TEST STARTING POINTS, not thresholds of record — same law as the Corona card caveat in texture-sets-discord §5.3. Honest refusals: Blender-native jitter amplitude ranges, roughness-variation amplitudes, tile-size-vs-camera-distance — the amplitude-bisect method (LOUD pass then ~70%) remains our own instrument for those.

## The answer as returned (source titles inline; [n] markers as returned)

### 1. Real Layup Variety

*   **Figure Continuity and Variation across Leaves**: Sequentially sliced veneer sheets (leaves) are kept in the exact order of slicing, commonly in quantities of **24 to 32 leaves per bundle** (source title: *Tectonic and Computational Frameworks for Mitigating Pattern Repetition in Wood-Veneer Wall Visualizations*) [1, 2]. Because wood is an organic product, the grain changes subtly from leaf to leaf [3], but keeping them in sequence allows fabricators to reassemble them with "only a very gradual transition in grain and figure across adjacent leaves" (source titles: *3.2 Material - Architectural Woodwork Institute* [4], *vt industries / VENEER GUIDELINES* [5]). Across consecutive panels, prominent characteristics will "ascend" or "descend" as the leaves progress (source title: *Surfaces - Oregon Door*) [6, 7].
*   **Cathedral Figure Repetition**: 
    *   **Book Match (Mirrored)**: Alternates and flips every other leaf of veneer like the pages of a book, creating a symmetrical, mirrored grain pattern at the joint line (source titles: *Surfaces - Oregon Door* [6], *Tectonic and Computational Frameworks...* [8, 9]). This mirrors the cathedral arches. However, because the "tight" and "loose" sides of the sliced veneer alternate, they reflect light and absorb finishes differently, resulting in an alternating light-and-dark striped "barber pole" optical effect (source titles: *Ansi Wdma - Is 1a 2013 Flush* [10, 11], *Tectonic and Computational Frameworks...* [8, 9]).
    *   **Slip Match (Translated)**: Translates sequential sheets side-by-side without flipping, exposing the same face side across all leaves (source titles: *Surfaces - Oregon Door* [12], *Tectonic and Computational Frameworks...* [13, 14]). The cathedral grain repeats as a translated pattern across the joint rather than mirroring (source title: *Ansi Wdma - Is 1a 2013 Flush*) [11, 15]. While this provides uniform color and light reflection under grazing angles, it does not show mirrored grain matches at joints, and can cause a leaning/sloping appearance on tall surfaces (source titles: *A Pacific Northwest Company - Cloudfront.net* [16], *Tectonic and Computational Frameworks...* [13, 14]).
    *   **Random Match**: Leaves are placed out of order (often from different logs) with a conscious effort to mismatch the grain, producing a random, board-by-board rustic aesthetic (source titles: *A Pacific Northwest Company - Cloudfront.net* [17], *Surfaces - Oregon Door* [18], *Tectonic and Computational Frameworks...* [13, 14]).
*   **Breaking Patterns at Panel Joints**: In physical installations, repeating patterns are naturally broken at joint boundaries by structural layout, fabricative tolerances, and specific rules:
    *   **Flitch Transitions**: When a single flitch yield is insufficient to sequence-match an entire room, a flitch transition must be placed at wall openings or changes in plane (like corners) to naturally interrupt and reset the grain pattern (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [19, 20], *Tectonic and Computational Frameworks...* [21, 22]).
    *   **Pre-Manufactured Sets**: Pre-manufactured veneer panel sets typically consist of **6 to 12 panels** (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [23], *Tectonic and Computational Frameworks...* [24, 25]). Sequence matching between independent sets is not required [23, 26].
    *   **Layup Symmetrical Offsets**: Made-to-order sets require balance matching (uniform leaf width) or center-balance matching (even number of uniform leaves with a center joint line) [26, 27]. At the outer edges, the flitch width can differ by up to a maximum of **1 inch (25.4 mm)** in custom layouts, or **1/2 inch (12.7 mm)** in Premium layouts (source titles: *A Pacific Northwest Company - Cloudfront.net* [28, 29], *Tectonic and Computational Frameworks...* [24, 25]). 
    *   **Misalignment Tolerances**: The allowable end-matching misalignment at panel joints must not exceed **4.8 mm [0.188 in]** for Premium grade and **9.5 mm [0.375 in]** for Custom grade (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [20], *Tectonic and Computational Frameworks...* [21, 22]).

### 2. Multi-Leaf Texture Sets

*   **Distinct Texture Counts**:
    *   The Poliigon Wood Plank Generator workflow recommends creating and exporting a minimum of **4 unique plank sets**, though the custom PlankCombiner node group can accept up to **8 unique texture sets** to maximize variation (source titles: *Poliigon Blog* [30, 31], *Tectonic and Computational Frameworks...* [32, 33]).
    *   High-quality seamless collections (such as the 3Dsky wood veneer libraries) ship sets consisting of **5 unique textures** with distinct wood patterns to ensure board-to-board variety (source titles: *Wood veneer texture seamless 81 - Wood - 3D model* [34], *Tectonic and Computational Frameworks...* [32, 33]).
    *   In flooring layouts, artists commonly utilize at least **4 of perhaps 20 distinct plank maps** to prevent repeating patterns (source titles: *Using Floor Generator Script by Bertrand Benoit* [35], *Tectonic and Computational Frameworks...* [32, 33]).
*   **Professional Texture Offerings**: Yes, professional products ship as multi-leaf/multi-plank sets. For example, Poliigon offers scanned libraries of **47 wood cladding textures** and customizable flooring generator sbsar tools to export individual boards [36, 37]. 3Dsky libraries provide sets of **5 unique textures** with matched diffuse, reflection, and normal maps [38, 39].
*   **Texel Densities and Physical Resolutions**:
    *   **Poliigon Large Surfaces**: Cover a physical size of **2.5 m x 2.5 m** [40, 41]. This maps to:
        *   **8K (8192 x 8192 px)**: **32 px/cm** texel density.
        *   **4K (4096 x 4096 px)**: **16 px/cm** texel density.
        *   **2K (2048 x 2048 px)**: **8 px/cm** texel density.
        *   **1K (1024 x 1024 px)**: **4 px/cm** texel density.
        *   (Source titles: *Poliigon Blog* [40], *Tectonic and Computational Frameworks...* [42, 43]).
    *   **VAST Gigapixel Cherry Veneer**: Physical coverage of **48 in x 22 in to 96 in x 44 in** with a scanning resolution of **83,463 x 38,622 px**, yielding a colossal **3,224 megapixel** file (source titles: *Medium Cherry Wood Veneer Texture - VAST Photos* [44], *Tectonic and Computational Frameworks...* [42, 43]).
    *   **Materials of the World Scanned Oak**: Covers a physical size of **260 x 121 cm** scanned in ultra-high resolutions up to **32k (32768 px)**; texel density is *NOT IN SOURCES* (source titles: *Seamless Oak Wood Veneer Texture - Materials Of The World* [45], *Tectonic and Computational Frameworks...* [42, 43]).
    *   **Viz-People Free Wood Textures**: Large-scale seamless textures at **8192px x 8192px** with physical sizes of **200 cm x 200 cm** (Aspen wood) and **400 cm x 400 cm** (Exotic planks decking); texel densities are *NOT IN SOURCES* (source titles: *Free wood textures - Viz-People* [46, 47], *Tectonic and Computational Frameworks...* [42, 43]).
    *   **Roblox Wood Planks (Standard)**: Maps a **1024 x 1024 px** texture over an **8 studs x 8 studs** region, resulting in a texel density of **128 px/stud** [42, 43, 48].
    *   **Roblox Wood Planks (Optimized)**: Maps a **1024 x 1024 px** texture over a **10 studs x 10 studs** region, resulting in a texel density of **102.4 px/stud** [42, 43, 49].

### 3. Randomization Operators

*   **CGSource MultiTexture Map & Floor Generator**:
    *   Randomly assigns multiple bitmaps across individual objects or Material IDs [50, 51].
    *   **Gamma Jitter**: Bertrand Benoit’s default layout setup utilizes a slight Gamma variation of **0.2** per board to make some boards subtly darker [52-54].
    *   **Scale Jitter**: Floor boards are randomized with a scale variation of **30%** [53-55].
    *   **Tilt Parameter**: Applies micro-level random rotations to individual boards to catch highlights realistically [53-55].
    *   *UV Offset Jitter, Rotation Jitter (degrees), and Hue/Value Jitter ranges for MultiTexture*: **NOT IN SOURCES** [53, 54].
*   **V-Ray (VRayUVWRandomizer & VRayMultiSubTex)**:
    *   Offers randomization by Render ID, Object ID, Node Name, Mesh Element, Stochastic Tiling, Instance ID, Particle ID, Face ID, and Node Handle [56-59].
    *   **UV Offset Jitter**: Allowed interval is from **0 to 1** (representing up to a full tile offset) [57-59].
    *   **Rotation Jitter**: Spans a range of **0 to 360 degrees** [57-59]. "Steps" define the step angle; for example, a rotation step of **5** restricts rotation to multiples of **72 degrees** [56, 58, 59]. Rotation can be locked to **0 to 0** to maintain strict parallel row alignment [57-59].
    *   **Scale Jitter**: UV scale variance can range from **10% to 150%**, with the option to unlock Scale V from Scale U for independent stretching [56-59].
    *   **Color Jitter**: Per-board VRayMultiSubTex controls allow Hue, Saturation, and Gamma offsets. VRayEnmeshMod setups demonstrate usable parameter values of **Hue = 5, Saturation = 3, and Gamma = 8** [58-60].
*   **Corona Renderer (CoronaUvwRandomizer & CoronaMultiMap / Multi-Shader)**:
    *   Supports randomization by Mesh Element, instance, polygon, or material ID [61-63].
    *   **UV Offset & Scale Jitter**: Offsets are supported via the UVW Randomizer, but the exact ranges are *NOT IN SOURCES* [64, 65].
    *   **Rotation Jitter**: A step value of **180 degrees** is commonly specified for directional wood textures to keep the grain oriented realistically while reversing direction [64-66].
    *   **Color Jitter**: Corona Multi Shader (supporting up to **100 inputs**) provides Hue and Gamma randomizations [67, 68]. In tile setups, applying a value of around **2.5%** for hue, saturation, and gamma random offsets successfully breaks visual repetition without causing unnatural color shifts (source titles: *Can yall help me please? im a beginner... : r/3dsmax - Reddit* [69], *Tectonic and Computational Frameworks...* [68, 70]).
*   **Blender Shader Nodes (Object Info, Geometry, White Noise)**:
    *   Uses the Geometry node's **Random Per Island** output or the Object Info node's **Random** value, passed through a 1D or 2D White Noise Texture node to generate unique coordinate shift vectors [71-74].
    *   **Rotation Jitter**: Shader networks achieve random **180-degree flips** or scale inversions on the X or Y axis by running a White Noise 2D node through a Math (Greater Than) node acting as a **0 or 1** boolean gate, converted to a scale factor of **-1 or 1** via Math (Multiply Add) to drive a Mapping Node [73-75].
    *   *UV Offset Jitter, exact Scale Jitter (%), and direct Hue/Saturation/Value node ranges*: **NOT IN SOURCES** [73, 74].
    *   **Procedural Plank Patterning**: CarlG uses a 2D noise with a scale of **42.5**, detail of **0**, roughness of **0**, and distortion of **42.5** to drive a 1D white noise vector for faking plank arrays on a plane [72-74].
    *   **Geometry Nodes Realization**: When Geometry Nodes instances are realized (using a Realize Instances node for boolean operations like window cutouts), the Object Info random parameter is destroyed [76-78]. To preserve randomization, a custom attribute on a **0 to 1** range must be assigned to each instance in Geometry Nodes, which remains readable in the Shader Editor after realization [77-79].

### 4. General Anti-Tiling

*   **Hue/Value/Roughness Amplitudes**: Physical reflectivity transitions are driven by subtle roughness variations rather than metallic parameters (source title: *Physically Plausible Materials in D5 Render...*) [80-82]. However, specific global anti-tiling roughness, value, or hue variation amplitudes (outside of engine-specific Multi-Shader settings) are **NOT IN SOURCES** [81, 82].
*   **Noise-Mask Scale Bands**: Unreal Engine utilizes macro variation to break up repeating patterns on far-field surfaces by multiplying together **3 samples of a macro variation texture** (such as *T_Default_MacroVariation*) at **3 different coordinates**, found by multiplying the incoming UV value by **3 different constant values** (source titles: *Landscapes - Material Concepts | Unrealcode.net* [83, 84], *Tectonic and Computational Frameworks...* [85, 86]).
*   **Texture-Bombing / Decal Scattering Parameters**:
    *   Unreal Engine standard Texture Bombing/Cell Bombing uses height-based blending (heightlerp) to offset, rotate, and flip multiple adjacent samples. This requires **4 texture lookups per layer**, which increases to **7** if displacement is utilized (source titles: *Texture Bombing - Rendering - Epic Developer...* [87], *Tectonic and Computational Frameworks...* [88, 89]).
    *   In Cell Bombing setups, a good range for **Min and Max Scale** parameters is **0.9 to 1.1** (source title: *Removing Texture Repetition! Cell Bombing in Unreal Engine - Hoj Dee*) [90].
    *   To ensure random offset movement in all directions, multiply the cell texture's Red and Green channels (U and V) by **2** and subtract **1** to expand the coordinate values into a **-1 to 1** range [91, 92].
    *   Rotation is controlled by multiplying a scalar rotation parameter by the cell texture's Blue channel and dividing by **360** to match rotation degrees [93]. 
    *   For correct normal map shading when randomized tiling coordinates are rotated, a Rotate About World Axis node must be added, with the rotation amount multiplied by **-1** to invert the direction and world coordinates added to the texture's Z-axis (source titles: *Removing Texture Repetition! Cell Bombing...* [92, 93], *Tectonic and Computational Frameworks...* [94, 95]).
    *   *Note on limits*: Cell Bombing works well with organic textures (dirt, grass, moss) but can disrupt uniform layouts like brick walls or tiled wood floors, making them look unnatural [96].
*   **Minimum Seamless-Tile Sizes for given Camera Distances**:
    *   Poliigon standard surfaces are captured at physical sizes of **2.5 m x 2.5 m** for large surfaces and **30 cm x 30 cm** for small decorative surfaces [40, 41, 94, 95].
    *   Viz-People free wood textures use physical sizes of **200 cm x 200 cm** for veneers (Aspen, Palisander, Wenge) and **400 cm x 400 cm** for exotic decking planks [46, 47, 97].
    *   Materials of the World seamless oak veneer uses a physical size of **260 x 121 cm** [42, 43, 45].
    *   *Minimum seamless-tile sizes mapped to specific camera distances*: **NOT IN SOURCES** (the sources state that physical tile sizes must match the camera viewing distance to prevent micro-detail from collapsing into visual noise, but specific camera distance ranges are not provided) [44, 94, 95].

### 5. Edges

*   **Edge-Band Thicknesses and Widths**:
    *   Panel parts, visible splines, and reveals must be edgebanded with solid wood, veneer, or veneer tape with a minimum thickness of **0.5 mm [0.018 in / 0.020 in]** to preclude show-through of the core material (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [56, 98], *Tectonic and Computational Frameworks...* [99, 100]).
    *   Standard case edge bands have a thickness of **0.3 mm [0.012 in]** for Premium Grade, **0.4 mm [0.016 in]** for Custom Grade, and **0.6 mm [0.025 in]** for Economy Grade (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [60, 76], *Tectonic and Computational Frameworks...* [99, 100]).
    *   Heavy-duty casework edge bands require a thickness of **3 mm [0.118 in]** across Premium, Custom, and Economy grades [99, 100].
    *   Solid wood flush door stiles require a **3/4 inch [19 mm]** minimum matching hardwood outer stile bonded to a **7/8 inch [22 mm]** minimum inner stile (total stiles net = 1-1/2 inches) (source title: *A Pacific Northwest Company - Cloudfront.net*) [101, 102].
    *   *Edge-band width ranges*: Horizontal and vertical edge-band width ranges are not given explicitly in the sources other than matching the thickness of the panel core. Veneer-faced panels have a minimum overall thickness of **18 mm [.709 in]** under paneling material standards [4], and flat panels have a minimum thickness of **6.4 mm [.250 in]** under aesthetic requirements [79].
*   **End-Grain Exposure Conventions**:
    *   Visible end grain at exposed surfaces is **"Not permitted"** under Premium grade standards, must be **"Compatible for color and grain"** under Custom grade standards, and is left **"At the option of the manufacturer/supplier"** in Economy grade (source titles: *3.4 Aesthetic - Architectural Woodwork Institute* [103], *Tectonic and Computational Frameworks...* [99, 100, 104, 105]).
    *   To hide core edges at outside corners, Premium and Custom specifications require that outside corner joinery of veneer-faced paneling and MDF be fully **"Mitered"** (source titles: *3.3 Structural - Architectural Woodwork Institute* [106], *3.4 Aesthetic - Architectural Woodwork Institute* [75], *Tectonic and Computational Frameworks...* [104, 105]). Miters are factory-prepared and machined for visual uniformity [104-106].
*   **Arris/Chamfer at Veneer Edges**:
    *   An arris is a sharp edge formed by the meeting of two flat or curved surfaces (source title: *Glossary Archive - Architectural Woodwork Institute*) [107].
    *   In physical woodwork, sharp arris lines or edges are **not permitted** because they are highly vulnerable to impact damage and fail to hold finishes properly [108, 109].
    *   Veneer edges are traditionally **"eased"** by lightly striking the sharp edge with a fine abrasive, or machined to a small radius (source titles: *Glossary of Terms - Leininger Cabinet & Woodworking* [110], *Ansi Wdma - Is 1a 2013 Flush* [111], *Tectonic and Computational Frameworks...* [108, 109]).
    *   Manual woodworking edgeplanes and trimmers apply tungsten steel bevel blades to edge bandings and veneers at chamfer angles of **45 degrees and 60 degrees** (source titles: *Levoite™ Manual Arc Edge Banding Trimmer...* [112], *Edge Banding Trimmer & Chamfer Plane – 3 Tungsten Steel Blades...* [102], *Tectonic and Computational Frameworks...* [99, 100]).

***

📊 I can write a Python script to mathematically generate a randomized, seamless veneer layup pattern directly as a texture map if you want a custom, non-repeating coordinate template.
