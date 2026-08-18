# DR — made-bed asset procurement spec + refit practice (arms ASK-002)

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not statute.
Nothing here outranks `knowledge/codes-th/`, the client contract, or an owner-signed
decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `8c7220de-1f0e-42d0-ad6e-295f7e7aaa40 "DR: made-bed asset procurement + refit 2026-08-17"` |
| conversation | `3179bec1-e1d7-47a2-9616-4d538c8cf391`, turn 1 |
| fired | 2026-08-17, builder-initiated (owner order this session: "spend all DR on this" — the Blender craft gap) |
| sources | 96 imported, 87 ready, 9 error |
| asked because | the plan's own words: the bed route is ASK-002 and nothing else, but nothing in the repo said how to recognise a MADE-authored set pre-purchase, which paid shelves hold them, or what the trade does when the bought mattress size differs (P2r-18 proved no transform reaches the 0.80 duvet-share cut from a folded-back-authored set; rescale probe ceiling 63.5%). |
| consumed by | ASK-002 (the owner's paid-tier purchase decision — this DR turns it from 'which subscription' into named candidate assets with prices and a pre-purchase checklist); qa/sourcing-tiers.json; wholebed_bench.py acceptance filters. Nothing consumes it yet at staging time. |

## Caveats stated before anything here is believed

Same synthesised-self-source pattern as the 2026-08-08 bedding-mass unit: "3D Bedding Asset Acquisition and Pipeline Integration Report" is the DR's own report imported back as a source, and it co-signs nearly every item. Items also carrying a REAL vendor page (3dsky Blog / How to Buy, Dimensiva Pricing, Design Connected Terms, TurboSquid RF License, CGTrader/TurboSquid listings, Maxtree EULA) are usable at REFERENCE tier; items citing ONLY the synthesised report (e.g. 'Chocofur transitioned to subscription', the '£7 fixed price' needs the vendor-page co-cite check) are quarantined until re-traced. Named single assets (Bedding 151, Hotel Bed Duvet Cover Style, Bed Linen Set PBR) are LISTINGS, not endorsements — every one still passes wholebed_bench + the R8 licence law before purchase, and a SPEND stays the owner's call per purchase. Prices are quoted from vendor pages AS THE SOURCES CAPTURED THEM — re-verify at checkout; this repo has caught fabricated prices twice, and two Design Connected subscription tables in this very answer disagree with each other (both shown, per the grounding rules).

## The answer as returned (source titles inline; [n] markers as returned)

### 1. WHICH SHELVES: MADE Beds vs. Showroom Styling

Marketplace offerings differ significantly in how their bed models are styled, authored, and cataloged:

*   **3DSky / 3ddd**: Standalone soft-good assets uploaded by specialized drapery designers are authored as fully **MADE** bedding sets with duvets covering the full sleeping surface (e.g., **Bedding 151**, designed for a mattress size of **180 x 200 cm** [1], or **Bedding 1**, modeled for a mattress of **160 x 200 cm** [2]) [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [3, 4]. However, complete bed frame listings on this shelf often display folded-back, messy, or rumpled showroom styling (such as **luxury bed** [5] or **careless male bed** [6]) [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [3, 4].
*   **CGTrader**: Sells both fully made configurations (such as **Hotel Bed Duvet Cover Style - King size - W180cm** [7]) and messy, folded showroom stylings (such as **SAMOA BED RELAXED** [8]) [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [9, 10].
*   **TurboSquid**: Offers a split inventory. Standalone duvet assets like **Bed Linen Set PBR** [11] are authored as fully made coverings, whereas products like the **Ikea Trolldom Duvet Set** [12] represent folded-back arrangements [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [9, 10].
*   **Design Connected**: Premium bed assets are constructed to match manufacturer catalogs, such as **IKEA Birkenland Bed Frame** [13] which provides mattress and linen coverings [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [14, 15].
*   **Dimensiva**: Focuses on clean, optimized, manufacturer-aligned assets, keeping standard bed styling optimized and simple [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [14, 15].
*   **Evermotion, Chocofur, BlenderKit, and Maxtree-adjacent libraries**: Whether these vendors sell made bed models on their official vendor pages is **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [14, 15].

#### Styling Filterability
Bedding styling (whether a duvet is fully laid out or folded back) is **NOT IN SOURCES** as a listed or filterable attribute on any of these marketplaces [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [16, 17]. No site allows filtering specifically by styling [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [16, 17]. Instead, search structures are restricted to high-level categories (such as **Furniture -> Bed** [18]) or broad tags like "bedding", "duvet", "blanket", or "pillow" [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [16, 17].

---

### 2. PRE-PURCHASE RECOGNITION

To ensure a purchased bed model meets professional production standards and achieves the minimum plan coverage, buyers must verify several geometric and structural properties before purchasing:

*   **(a) Duvet Plan Coverage**: Buyers must confirm this by checking the exact dimensions provided in the asset metadata [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20]. For example, in **Hotel Bed Duvet Cover Style - Collection** (from *3D Bed Duvet Model - TurboSquid 1677055*), sheets for a Double Twin bed are sized at **H506 x W1641 x D2082 mm** for a mattress measuring **W1400 x D2000 mm** [21, 22], verifying a substantial drape length [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20].
*   **(b) Object and Layer Separation**: Professional assets specify individual sub-meshes [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20]. For example, in *3D Bed Duvet Model - TurboSquid 1677055*, the **bed frame, bed base, and sheets are listed as distinct elements** with different dimensional data [21]. Conversely, on platforms like **Dimensiva**, models are packaged "with a centered pivot and all elements attached as a single object" (from *Pricing - Dimensiva | 3D Models Subscription Plans*), indicating the bedding is not delivered as a separate layer by default [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20].
*   **(c) Simulation-Grade vs. Shrinkwrapped Mesh**: Simulation-grade soft goods require high polygon densities to resolve physical folds [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20]. 
    *   **High-fidelity simulation soft stacks** typically contain massive polycounts: **1,712,880 polygons and 866,662 vertices** (from *Bedding 151 - Bed - 3D model - 3dsky*) [1] or **1,502,622 polygons and 1,501,381 vertices** (from *3D Bed Duvet Model - TurboSquid 1677055*) [23].
    *   **Mid-range simulation setups** feature around **500,000 polygons** (from *Bedding 1 - Bed - 3D model - 3dsky*) [24].
    *   **Real-time/shrinkwrapped meshes** optimized for real-time engines use highly simplified meshes (from *Low-poly Bedding 3D Models – Free & Premium Downloads | CGTrader*) to reduce computing load and lack simulated cloth details [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20].

#### Listing Details Correlating with Usable Bedding
1.  **Polycount Bands**: High polygon densities (typically **500,000 to 1,700,000+ polygons** [19, 20]) indicate simulation-grade, soft-fold geometry, whereas low-poly models (often **under 10,000 to 30,000 polygons** [25, 26]) indicate rigid or shrinkwrapped real-time assets [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20].
2.  **PBR Map Sets**: High-resolution, un-tiled PBR maps (resolutions of **8K to 16K** [21] are standard for close-up fidelity on *3D Bed Duvet Model - TurboSquid 1677055*) correlate with professional, usable bedding [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20]. "PBR Textures" options can be filtered directly in *Bedding 3D Models – Free & Premium Downloads | CGTrader* [27, 28].
3.  **Named Bed Sizes**: Standardized sizes like "King size," "Double Twin," or explicit mattress measurements like **180 x 200 cm** or **160 x 200 cm** are used in professional listings to verify scale (as seen in *3DSky Bedding 151* [1], *3DSky Bedding 1* [2], and *3D Bed Duvet Model - TurboSquid 1677055* [21, 22]) [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [19, 20].

---

### 3. REFIT PRACTICE

When a purchased bedding set's mattress size does not match the mattress in the scene, professional 3D artists avoid simple scaling in DCC applications, as it introduces severe visual distortions [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [29, 30]. Instead, professionals utilize specialized cloth simulation tools, with **Marvelous Designer** serving as the industry standard [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [29, 30].

#### Re-Simulation Pipeline
According to *3D Bedding Asset Acquisition and Pipeline Integration Report* [31, 32], the standard professional pipeline (referencing *Antonio Bosi: Realistic Bed Maya Tutorial* [31] and *Reddit Marvelous Designer: Cloth Simulation Thread* [31]) involves the following 12 steps:

| Step | Action | Detail Specification & Parameters | Source Document |
| :--- | :--- | :--- | :--- |
| **1** | Create base mesh | Create a beveled poly box primitive in Maya (e.g., W**39 x D42 x H4 inches** [31, 32]) above Y=0 origin point to avoid simulation errors [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **2** | Export mattress | Export the mattress selection as an OBJ file and import it into Marvelous Designer with a scale of **10,000** [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **3** | Draft bedding patterns | Use the 2D rectangle tool to draft the bedding patterns (e.g., **4000 x 4500 mm** [31, 32] for a sheet) and float them directly above the mattress avatar in the 3D viewport [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **4** | Adjust pattern sizes | Scale pattern pieces uniformly by dragging edges while holding down the **Shift** key [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* / *Reddit Marvelous Designer: Cloth Simulation Thread* |
| **5** | Set fabric properties | Set pattern's particle distance to **40** and apply physical properties like the "**Cotton_CLO**" fabric preset [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **6** | Drape simulation | Run simulation to drape sheet over the mattress, then pause [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **7** | Edge elasticity wrapping | Enable "elasticity" property on all external edges of pattern, set elasticity parameter to **20** [31, 32], run simulation again to wrap the sheet tightly around the mattress [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **8** | Increase resolution | Increase simulation resolution by reducing particle distance to **20, 10, or 5** [31, 32] to capture fine folds [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* / *Reddit Marvelous Designer: Cloth Simulation Thread* |
| **9** | Fix simulation glitches | Type a value of **0.1** into the "**Time step**" settings [31, 32] to eliminate rendering or simulation glitches [31, 32]. | *Reddit Marvelous Designer: Cloth Simulation Thread* |
| **10** | Export simulated cloth | Export the clothing and sheets as OBJ files using a scale of **1%** [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **11** | Smooth imported mesh | Import OBJ back into Maya and use an artisan tool to smooth and relax the hard triangulated geometry [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |
| **12** | Apply poly reduction | Apply a poly reduce of around **90%** [31, 32] to generate a lightweight version of the simulation-grade mesh [31, 32]. | *Antonio Bosi: Realistic Bed Maya Tutorial* |

#### Artifacts Produced
*   **Triangulation**: Marvelous Designer triangulates the imported object as a garment on import [33]. The simulated objects exported back are triangulated and their vertex numbers are changed, meaning they are **no longer morphable versions of their originals** [33] [*Marvelous Design 8 vertex count between import/export - Daz 3D Forums*].
*   **Workflow Workaround**: To preserve textures, professionals import the triangulated mesh back into the DCC and **copy/paste the original UV surfaces** onto the new simulated versions, which renders perfectly [33] [*Marvelous Design 8 vertex count between import/export - Daz 3D Forums*].
*   **scaling**: Simple scaling in DCCs is avoided as it results in **severe visual distortions** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [29, 30].

---

### 4. SCENE EXTRACTION & LICENSING RESTRAINTS

*   ** bedroom scene products (Evermotion Archinteriors etc.) reliably contain made beds?**
    Whether full bedroom scene products reliably contain made beds is **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [34, 35].

*   **Do their licenses permit extracting the bed asset for reuse in a different client scene?**
    The legal extraction of individual assets for reuse in separate client projects is strictly regulated by each vendor's End User License Agreement (EULA):

    *   **Evermotion Archinteriors**: Under standard licensing (*Evermotion Archinteriors Vol 17 PDF - Scribd*), **resale of the scene data is strictly prohibited**, and models can be used for commercial purposes only by owners who purchased the original volume [34, 35]. Under Unreal Engine distributions (*Get an Evermotion Archinterior scene for free | CG Channel*), assets can be utilized in "any engine or tool" for commercial projects, subject to the standard Fab Standard license EULA [34, 35].
    *   **TurboSquid**: Under standard terms (*Royalty Free License | TurboSquid Help Center*), the purchaser receives a non-exclusive, perpetual, worldwide license to use stock media within creations [34, 35]. As clarified in *Royalty Free License FAQ | TurboSquid Help Center*, **a designer is permitted to reuse purchased assets across multiple client projects indefinitely**, provided only final rendered imagery is delivered [34, 35]. If raw files are shared with a client, the client may reuse the model under the contractor's license, but sharing the raw model with multiple separate clients requires a new license purchase for each client [34, 35].
    *   **Design Connected**: Under the perpetual, non-exclusive, non-transferable worldwide license (*General Terms of Use - Design Connected*), sharing files with external clients is permitted solely for reproduction within permitted projects, and clients receive no independent rights to access or use the raw assets [34, 35]. Furthermore, **systematic extraction of substantial portions of the database is strictly prohibited** [*General Terms of Use - Design Connected*] [34, 35].
    *   **Dimensiva**: Under standard terms (*License - Dimensiva - How You Can Use Our 3D Models*), downloaded assets may be modified and used in private or commercial projects, but **cannot be sold, assigned, or redistributed separately** in their original or modified formats [34, 35].
    *   **Maxtree**: Under standard terms (*End User License Agreement - Maxtree*), the license requires that linear media output must be an irreversible final pixel format from which 3D geometry cannot be extracted [34, 35]. **Standalone distribution is prohibited** [34, 35].

---

### 5. MARKETPLACE PRICES

Per-model, per-set, and subscription rate bands as compiled from official vendor pages among the sources:

*   **3DSky / 3ddd**:
    *   *Per-Model*: Fixed price of **\$7** per PRO asset, with a minimum cart purchase of **\$14** (2 models) [*3dsky — the fixed-price 3D marketplace for ArchViz creators and beyond - 3dsky Blog*] [36, 37] / [*How to Buy - 3dsky*] [38] / [*Credits & Subscription*] [39].
    *   *Per-Set / Volume*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Subscription Plans*: Daily limit upgrade for FREE models (from 3 up to 30 free downloads per day) is priced at: **\$6** for 5 days, **\$9** for 10 days, **\$18** for 1 month, **\$36** for 2 months, **\$54** for 3 months, **\$108** for 6 months, or **\$216** for 12 months [*Credits & Subscription*] [39, 42].
*   **Dimensiva**:
    *   *Per-Model*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Per-Set / Volume*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Subscription Plans* (All tiers cap at **500** downloads/month): **49€** for 1 Month (was 54€/56€), **79€** for 2 Months (was 109€), **99€** for 3 Months (was 140€), and **289€** for 1 Year (was 299€/398€) [*Pricing - Dimensiva | 3D Models Subscription Plans*] [43].
*   **Design Connected**:
    *   *Per-Model*: On-demand pricing on official vendor pages is **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Per-Set / Volume*: Collections are discounted up to **30%** off list price [*General Terms of Use - Design Connected*] [40, 41, 44] (for instance, **Bedroom Set 1** containing 6 models is priced at **EUR 66**, saving EUR 28 from the list price of **EUR 94** [*Husk Bed 3d model | B&B Italia, Italy*] [45]). Volume discounts are structured as: **10%** discount for 101–300 models, **15%** discount for 301–600 models, **20%** discount for 601–1200 models, **25%** discount for 1201–1600 models, and **30%** discount for over 1600 models [*General Terms of Use - Design Connected*] [44].
    *   *Subscription Plans*:
        *   According to *FAQ & Support for all services by Design Connected* [46]: **19 EUR/mo** (annual) / **24 EUR/mo** (monthly) for Starter (3 models); **29 EUR/mo** (annual) / **44 EUR/mo** (monthly) for Starter+ (6 models); **39 EUR/mo** (annual) / **59 EUR/mo** (monthly) for Personal (9 models); **69 EUR/mo** (annual) / **79 EUR/mo** (monthly) for Professional (18 models); **99 EUR/mo** (annual) / **109 EUR/mo** (monthly) for Business (36 models) [40, 41, 46].
        *   According to *Design Connected Subscription plans* [47]: **€59/mo** for Professional (25 models & materials/month, €708 annual plan paid monthly); **€84/mo** for Business (50 models & materials/month, €1008 annual plan paid monthly).
*   **CGTrader**:
    *   *Per-Model*: Ranges from **Free** up to **\$65** (e.g., Templewebster Bed) [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41] / [*Page 2 of Duvet 3D Models – Free & Premium Downloads | CGTrader*] [48]. Individual listings are priced at: **\$1.50, \$2, \$2.77, \$3.50, \$4.13, \$4.50, \$5.60, \$6.30, \$7.50, \$8, \$8.40, \$10, \$11.40, \$12, \$13.30, \$14.50, \$22.50, \$32, \$41.89, \$59, or \$62.50** [*Bedding 3D Models – Free & Premium Downloads | CGTrader*] [49-52]. High-end individual assets (such as **Bed Ring** or **Bed Boca Slim**) are listed at **\$97.30** [*Bedding 3D Models – Free & Premium Downloads | CGTrader*] [53, 54].
    *   *Per-Set / Volume*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Subscription Plans*: **\$9.99/mo** for 25 premium models per month [*Bed 3D Models – Free & Premium Downloads | CGTrader*] [55] / [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
*   **TurboSquid**:
    *   *Per-Model*: Ranges from **Free** up to **\$80** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41] (e.g., **Hotel Bed Duvet Cover Style - Collection** is priced at **\$80** [*3D Bed Duvet Model - TurboSquid 1677055*] [56]). Individual listings are priced at: **\$1, \$2, \$3, \$4, \$4.99, \$5, \$7, \$8, \$9, \$9.99, \$10, \$12, \$13, \$14, \$14.95, \$15, \$16, \$17, \$18, \$19, \$19.49, \$20, \$22, \$22.99, \$24, \$25, \$28, \$29, \$32, \$34, \$35, \$36, \$38, \$39, \$44, \$45, \$49, \$50, \$59, \$70, or \$80** [*Download Free & Premium Bed 3D Models | TurboSquid*] [11, 57-67] / [*Download Free & Premium Bed Sheets 3D Models | TurboSquid*] [12, 68-76].
    *   *Per-Set / Volume*: **Bed Collection 04** (10 items) is priced at **\$70** [*Download Free & Premium Bedding 3D Models | TurboSquid*] [77], and **Bed Sheets Pack 01** is **\$16** [*Download Free & Premium Bed Sheets 3D Models | TurboSquid*] [69].
    *   *Subscription Plans*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
*   **Evermotion**:
    *   *Per-Model*: Vendor page on-demand pricing is **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41]. Reseller volumes on *Evermotion - Archmodels, Archinteriors, Archexteriors | Vray.us* start at **\$100**, and **Archmodels Vol. 277 - Modern Wardrobes** is priced at **\$64.31** [78].
    *   *Per-Set / Volume*: Volume scenes (e.g., **Archinteriors vol. 63**) are priced at **\$120** [*Evermotion – CG River*] [79]. **Archexteriors** volumes (such as Vol. 36 to 42) are priced from **\$99** up to **\$138.80** [*Evermotion - Archmodels, Archinteriors, Archexteriors | Vray.us*] [78] / [*Evermotion – CG River*] [79].
    *   *Subscription Plans*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
*   **Chocofur**:
    *   Per-model, per-set, and subscription rates are **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41]. Note that Chocofur "transitioned to a subscription-based model" [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41], but details are **NOT IN SOURCES**.
*   **BlenderKit**:
    *   **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
*   **Maxtree**:
    *   *Per-Model*: Custom models cost **\$120–\$350** (Non-Exclusive) or **\$2000–\$5000** (Exclusive) [*Custom Service – Maxtree*] [80]. Individual standard species are priced from **\$26 to \$368** [*High Poly – Page 10 – Maxtree*] [81].
    *   *Per-Set / Volume*: Plant models packages cost **\$125–\$1,770** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].
    *   *Subscription Plans*: **NOT IN SOURCES** [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [40, 41].

---

### 6. FORMAT/ENGINE & COMPATIBILITY

*   **Which shelves deliver Blender-native or OBJ/FBX with PBR textures that survive import into Blender/Cycles without vendor's engine (Corona/V-Ray materials)?**
    
    *   **CGTrader** and **TurboSquid** host Blender-native assets with ready-to-render PBR mappings [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [82, 83]. CGTrader offers search filters for "PBR Textures" [82, 83], while TurboSquid provides PBR-compliant assets [82, 83].
    *   **3DSky**, **Dimensiva**, and **Design Connected** primarily deliver 3ds Max files (.max) bundled with V-Ray or Corona materials [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [82, 83].

*   **What is the standard conversion practice?**
    The standard pipeline for converting proprietary shaders to Blender involves several practices:
    
    1.  **DCC Conversion**: Proprietary V-Ray/Corona shaders are converted to **Standard Materials in 3ds Max** before exporting via FBX [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [82, 83].
    2.  **Automation Plugins**: Automatic utility plugins like **maxToBlender** can be utilized to streamline the migration [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [82, 83] / [*Creating a Max to Blender plugin to convert vray/fstorm/corona files to Blender Octane/cycles - Paid Work*] [84].
    3.  **Substance Painter Texturing Pipeline**: Importing the V-Ray/Corona-assigned files, **converting them within Substance Painter's texturing pipeline**, and exporting standard PBR textures directly for Blender [*3D Bedding Asset Acquisition and Pipeline Integration Report*] [82, 83].

*   **What is lost?**
    Standard DCC conversion and automatic translation utility methods (like *maxToBlender*) are **not suitable for complex shading networks** and are **good only for basic shaders** [*Creating a Max to Blender plugin to convert vray/fstorm/corona files to Blender Octane/cycles - Paid Work*] [84]. Complex shader logic, custom procedural setups, and intricate material blends do not translate directly and must be manually rebuilt in Blender/Cycles [*Creating a Max to Blender plugin to convert vray/fstorm/corona files to Blender Octane/cycles - Paid Work*] [84].

---
📊 I can run a calculation in our offline sandbox of the average price per model on CGTrader and TurboSquid to help you budget our next model purchase.
