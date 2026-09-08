# DR — Thai residential bedroom SERVICES: switch/socket heights, skirting, shadow gap

> PROVENANCE: NotebookLM Deep Research, fired by the builder on its own trigger
> (DR-INITIATION rule 4: *building an object/domain class for the first time*)
> on 2026-08-17 during round p2r49, after the vault was searched FIRST and found
> to hold nothing on the subject — `knowledge/ergonomics/casework-fixture-
> clearances-th-practice.md` carries KITCHEN outlet clearances only (4.3), and a
> repo-wide grep for skirting returns a search string, a prose passage in
> docs/strategy.md that records "Nothing was built: it touches wall geometry",
> and critic text.
> - notebook: `7864b15c-68f8-4649-810f-36f3f7c31618` (fresh, created by `notebooklm_dr.py --new`)
> - conversation: `1bee1917-f6c2-437a-a769-41af92b96163`, turn 1 of 1
> - raw transcript: `qa-history.json` beside this file.
> **Tier REFERENCE — practice-report grounding, not domain truth, not statute.**
> NLM does NOT hold Thai law and volunteers statutory numbers from model memory:
> nothing here may be cited as a code value. `knowledge/codes-th/` always outranks.
> The bracketed markers are NotebookLM's own source indices and are NOT yet
> resolved to source titles — that resolution is owed before this unit is
> distilled into `knowledge/` proper.

## WHAT CONSUMED IT, in the same commit (the rule the DR lane exists to satisfy)

`pipeline/scripts/build_room.py` — `_build_services` / `_build_service_plates`, and
the constants at their head:

| constant | value | the line of this answer it comes from |
|---|---|---|
| `_SKIRT_H_MM` | 100 | high-ceiling volumes (2700-3200 AFFL): 100-150 mm |
| `_SKIRT_PROJ_MM` | 15 | projection 6-16 mm for flat polymer or solid timber |
| `_PLATE_MM` | 86 | 86 x 86 mm square faceplate |
| `_SWITCH_Z_MM` | 1225 | door-side switch 1200-1250 mm AFFL to the box centreline |
| `_SWITCH_DOOR_OFF_MM` | 125 | 100-150 mm clear of the finished architrave edge |
| `_BEDSIDE_SWITCH_Z_MM` | 700 | bedside two-way switch 600-700 mm AFFL |
| `_SOCKET_Z_MM` | 325 | concealed bedside socket 300-350 mm AFFL |

WHAT WAS **NOT** TAKEN, and why, so the next reader does not think it was missed:
the shadow-gap alternative (a 10-15 mm recessed band at the floor line) is the
contemporary detail this room's language would plausibly use, and it was NOT built
— it is a RECESS, which means cutting the wall prism rather than adding a box, and
R8's test sends a box to the builder while a cut into a wall is a different
mechanism with its own first round. The skirting is the reversible choice; the
shadow gap stays available and is named as the reversal in the decision row.

Prices in the answer (THB per linear metre) are NOT consumed anywhere and are not
a quotation for this project; they are recorded because the DR volunteered them.

## THE QUESTION AS ASKED

For residential bedroom interiors in Thailand (condominiums and houses), what are the standard mounting heights and placement conventions, given in millimetres above finished floor, for: (1) wall light-switch plates beside a bedroom door, including two-way switching at the bed; (2) power sockets beside a bed or nightstand, and how many per bedside; (3) skirting / baseboard where a plastered wall meets a wood floor - typical height and projection, and how it is detailed at a door architrave; (4) the recessed shadow-gap detail used instead of skirting in contemporary interiors - typical gap height and depth, and what it costs to build. For each, give the typical numeric range, what drives the number ergonomically or by code, and how a Thai interior designer draws it on an interior elevation.

## THE ANSWER, VERBATIM

#### 1. Wall Light-Switch Plates and Two-Way Switching Circuits

*   **Typical Numeric Ranges:**
    *   **Door-Side Switches:** The standard mounting height for primary wall-mounted switch plates beside the bedroom entrance door is **1200 mm to 1250 mm Above Finished Floor Level (AFFL)**, measured directly to the horizontal centerline of the electrical box [1]. 
    *   **Universal Design (UD) / Senior Living:** For accessible or senior living units, the Engineering Institute of Thailand (วสท. / EIT) recommends a lowered centerline of **900 mm to 1000 mm AFFL** [2].
    *   **Horizontal Door Frame Offset:** The switch plate centerline must maintain a horizontal clearance margin of **100 mm to 150 mm** from the outer finished edge of the door frame or decorative architrave [2].
    *   **Bedside Two-Way Switches (*สวิตช์สองทาง* - Swith Song Tang):** Bedside switches are mounted at **600 mm to 700 mm AFFL** [3]. This coordinates with premium nightstands that typically stand between 500 mm and 550 mm high, allowing a clear vertical spacing of **100 mm to 150 mm** above the nightstand deck [3].
*   **Ergonomic and Code Drivers:**
    *   The standard **1200–1250 mm height** optimizes ergonomics for the standing reach envelope of the average-height Thai adult [1]. The lowered **900–1000 mm UD standard** complies with ADA-aligned accessibility criteria by restricting maximum side-approach wheelchair reach to 1100–1200 mm [2].
    *   The **100–150 mm horizontal door offset** is structurally driven to prevent physical collisions between the sub-wall conduit box and the door sub-frame (such as timber, WPC, or synthetic doors) during installation, while visually separating the faceplate from the door trim [2].
    *   The bedside switch provides **two-way switching topology** to control primary bedroom lighting from both the entrance and bed [3]. Mounting it 100–150 mm above the nightstand deck allows users to easily operate lighting from a reclined mattress level without having to sit up or strain [3].
*   **Drafting Conventions on Elevation:**
    *   Thai interior designers represent switches on elevations at a scale of **1:20 or 1:25** [4].
    *   They draw a scaled rectangular bounding box corresponding to standard faceplates (typically **120 mm × 70 mm** for rectangular plates, or **86 mm × 86 mm** for square plates) [4].
    *   The faceplate is overlaid with an electrical symbol: a circle containing an **"S"** with a subscript **"3"** or **"2W"** to denote the two-way/three-way wiring pathway [4].
    *   The construction drawings show a vertical dimension string from the Finished Floor Line (FFL) to the centerline of the switch box, paired with a horizontal offset dimension from the adjacent door frame finished edge [4].

---

#### 2. Bedside Power Sockets and Connectivity Configurations

*   **Typical Numeric Ranges:**
    *   **Concealed Sockets:** Sockets intended to be hidden behind bedside nightstands are mounted at **300 mm to 350 mm AFFL** [5].
    *   **Exposed Counter-Level Sockets:** Sockets intended for easy daily access are mounted at **600 mm to 700 mm AFFL**, matching the bedside switches [5].
    *   **Universal Design Sockets:** Raised to a minimum of **900 mm AFFL** [6].
    *   **Quantity:** Premium guidelines specify at least **two duplex plates (yielding 4 outlets)** per bedside [7].
*   **Ergonomic and Code Drivers:**
    *   The low-level height (**300–350 mm**) matches the standard height of general-purpose wall outlets across living spaces and is driven by visual ergonomics to hide cables for permanent fixtures like bedside lamps [5]. The counter-level height (**600–700 mm**) is driven by user convenience to enable easy charging of temporary devices like mobile phones or laptops without bending down [5].
    *   A typical bedside setup combines one duplex plate featuring two Type O grounded outlets (TIS 166-2549 compliant for 3-pin plugs with round pins) and one hybrid plate containing one Type O outlet and integrated dual USB-A / USB-C ports (minimum 2.1A output) [7]. This density ensures simultaneous power for a dedicated lamp, smart devices, and medical or comfort gear (such as a CPAP machine) [8].
    *   Under EIT (วสท.) code, there are no rigid residential height limits for outlets in dry spaces [8]. Sockets are raised to **900 mm** in elderly units to prevent Lower back strain and slip-and-fall hazards associated with bending [6]. 
    *   For ground floors of landed homes located in flood-prone zones, EIT code mandates that lower-level power circuits (installed below standard flood lines) must be protected by a residual current device (RCD / RCBO) with a tripping sensitivity rating of no greater than **30 mA** [6].
*   **Drafting Conventions on Elevation:**
    *   Sockets are drawn at a scale of **1:20** on elevations [9].
    *   They are represented as a scaled bounding box containing a circle with **two parallel slash lines** (the standard symbol for a duplex convenience receptacle) [9].
    *   Designers draft a vertical dimension line from the FFL to the horizontal centerline of the socket plate, alongside horizontal dimension strings from the edge of the finished wall or column line [9].
    *   On coordination plans, designers overlay a dashed outline of the nightstand to verify that concealed outlets fall safely within the furniture profile and exposed sockets clear the tabletop deck with proper space for plug bending radii [9].

---

#### 3. Traditional Baseboard (Skirting) and Architrave Detailing

*   **Typical Numeric Ranges:**
    *   **Skirting Heights (*Bua Cherng Pa-nang* - บัวเชิงผนัง):**
        *   *Low-Ceiling Volumes (2400 mm to 2600 mm AFFL):* **70 mm to 80 mm** (nominally 3 inches) [10].
        *   *High-Ceiling Volumes (2700 mm to 3200 mm AFFL):* **100 mm to 150 mm** (nominally 4 to 6 inches) [10].
    *   **Projection (Thickness):** Protrusion from the finished plaster wall typically ranges from **6 mm to 16 mm** for flat polymer or solid timber, up to **20 mm or 25 mm** for classic molded profiles or hollow skirting assemblies [10].
*   **Ergonomic and Climatic Drivers:**
    *   Sizing proportions prevent vertical compression of standard rooms [10]. A 70–80 mm height provides a subtle wall-to-floor transition under lower ceilings, while taller skirting (100–150 mm) serves as a deliberate visual design element in high-ceiling spaces [10].
    *   Climatically, baseboards absorb expansion in wood floors and protect plastered masonry walls from moisture, wet-mopping, and impact [11]. Thailand's high humidity makes traditional wood-fiber composites (MDF or HDF) highly susceptible to moisture swelling, surface delamination, and rot [12]. High-durability alternatives are standard:
        *   *PVC/Polystyrene (PS):* Termite-proof and water-resistant [12]. PVC profiles (**6–16 mm** thick) cost **40 THB to 120 THB** per linear meter [12]. Polystyrene profiles (**15–21 mm** thick) provide sharper detail lines for **150 THB to 300 THB** per linear meter [12, 13].
        *   *Solid Teak Wood (*Mai Sak* - ไม้สัก):* The gold standard for high-end luxury interiors [12]. Naturally termite and rot-resistant when kiln-dried, it is typically milled to **90 mm** high and **12 mm to 14 mm** thick, costing **250 THB to 350 THB** per linear meter [12].
*   **Detailing at the Door Architrave (*Sub-Wong-Kob* - ซับวงกบ):**
    *   **Method A: Flush Butt Joint (Architrave > Skirting Thickness):** The preferred upscale standard [14]. An architrave profile that is thicker than the skirting (e.g., a 20 mm or 21 mm thick architrave paired with a 12–14 mm thick skirting) allows the horizontal skirting to run directly and butt squarely against the vertical edge of the architrave casing [14]. The skirting is inset relative to the architrave's face, creating a clean shadow line that masks wall flatness deviations [14].
    *   **Method B: 45-Degree Back-Bevel Taper (Skirting > Architrave Thickness):** If a thin architrave profile (like a 5 mm UPVC wrap) is paired with a thicker skirting board (such as a 16 mm or 20 mm thick hollow PVC baseboard), a butt joint would expose the raw, unfinished end profile of the skirting [15]. To resolve this, installers cut a **45-degree back-bevel** at the termination of the skirting board, tapering its face profile down to meet the outer face of the door architrave [15]. The joint is filled with color-matched acrylic sealant (known in Thai as **DAP / แด๊ป**) mixed with wood dust or color pigments [15].
*   **Drafting Conventions on Elevation:**
    *   On **1:20** elevation sheets, the skirting is drawn as a continuous, horizontal band running along the wall base [16].
    *   Detail sheets feature vertical wall-to-floor details at a scale of **1:2 or 1:5** [16]. These details illustrate:
        *   The concrete structural slab and structural screed [16].
        *   The PE foam underlayment and flooring layer (e.g., 12 mm engineered timber) with a specified **8 mm to 10 mm** peripheral expansion gap [16].
        *   The lightweight concrete block (Superblock) wall or drywall stud [16].
        *   The **15 mm** cement plaster/skim coat layer [16].
        *   The skirting profile, including adhesive cavities, attached to the wall using structural adhesive or finish pins [16].

---

#### 4. Recessed Shadow-Gap Details (*Bua Fang* / บัวฝัง or *Seh-Rong* / เซาะร่อง)

*   **Typical Numeric Ranges:**
    *   **Gap Height (Vertical):** **10 mm to 15 mm** [17].
    *   **Gap Depth (Horizontal):** **10 mm to 12 mm** [17].
*   **Ergonomic and Construction Drivers:**
    *   The gap dimensions are standardized to fit pre-fabricated extruded aluminum or UV-stable PVC shadow-gap profiles (such as U-channel or Z-profile plaster beads) designed to guide plastering trowels [17].
    *   This contemporary recessed shadow gap forms a neat, dark recess at the wall-to-floor boundary, replacing protruding baseboards [17, 18]. This creates a minimalist "floating wall" look and allows furniture to sit completely flush against the wall surface [18].
    *   **Tropical Construction Challenge:** Most Thai residential walls consist of structural concrete frames with lightweight autoclaved aerated concrete (AAC) block infills (such as Superblock or Q-CON), finished with a **15 mm to 20 mm** hand-applied cement-sand plaster layer [19]. Manually creating a straight, clean shadow gap in wet cement plaster is extremely labor-intensive, and any structural waviness in the wall is ruthlessly highlighted by the shadow line [19]. To resolve this, a rigid, extruded aluminum or PVC shadow-gap guide bead is mechanically fastened and leveled to the base of the raw block wall using cement mortar or construction adhesive before plastering [20]. The plastering team uses the profile's integrated plaster stop flange to align their screed guides, applying and skimming the plaster flush with the outer nose of the profile to hide fasteners while leaving a crisp, recessed channel [20]. The wood flooring is laid beneath the plaster line, sliding slightly into the horizontal recess of the channel, which conceals the wood's structural expansion gap while permitting free movement [20].
*   **Construction Cost Breakdown (Thailand):**
    *   **Material Costs:**
        *   *PVC Shadow Gap Beads (Standard):* **25 THB to 50 THB** per linear meter [21].
        *   *Anodized/Powder-coated Aluminum Profiles (Premium):* **150 THB to 350 THB** per linear meter [21].
    *   **Installation and Plastering Labor:**
        *   *Labor Premium:* Creating a clean plaster guide-edge along the floor line using skilled masons adds **400 THB to 850 THB** per linear meter [22].
        *   *Total Installed Cost (Bangkok luxury condo):* Fully completed, painted, and finished standard recessed shadow gaps range from **600 THB to 1200 THB** per linear meter [22].
    *   **Integrated LED Shadow Gaps:** If the detail incorporates an aluminum profile with a mounting slot for LED ribbon lighting to create a glowing perimeter "floating wall" effect, the total installed cost increases to **1500 THB to 2500 THB** per linear meter (excluding the LED driver and lighting controller) [22].
*   **Drafting Conventions on Elevation:**
    *   On **1:20** elevations, the shadow gap is drawn as a solid, thick black horizontal band (or a hatched dark-gray band) exactly **10 mm to 15 mm** tall directly above the FFL line [23].
    *   It is paired with a mandatory **1:1 or 1:2** technical detail section illustrating:
        *   The raw concrete structural slab and level screed [23].
        *   The moisture barrier underlayment and engineered wood floor [23].
        *   The AAC block masonry substrate [23].
        *   The anchoring detail of the aluminum or PVC shadow-gap guide bead to the blockwork [23].
        *   The plaster layer ending cleanly at the plaster stop flange [23].
        *   The expansion clearance cavity beneath the wall [23].

---

📊 Would you like me to compile these heights, offsets, and detailing rules into a standardized technical drawing coordination sheet that you can share with your site engineers or draftspersons?
