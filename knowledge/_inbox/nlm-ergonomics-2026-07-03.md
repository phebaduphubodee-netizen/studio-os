# NLM Deep Research — interior human-factors & ergonomics (2026-07-03)

**Tier:** REFERENCE (NotebookLM DR — distill into `knowledge/ergonomics/` before any value gates a deliverable).
**Notebook:** `5de4bb36-e53b-45b9-b31c-774ed0ffdeff` — "Interior human-factors & ergonomics (functional layout)".
**Conversation:** `e9ee5f92-a526-45c1-a1e9-7ffba750a792`, final answer = **turn 3** (turns 1–2 were the model's streaming partials of the same question; **turns 4–6 drifted OFF-TOPIC into motion-capture / industrial DHM and are DISCARDED** — the `--iterate 3` auto-follow-up chased NotebookLM's own suggestions off the residential brief).
**DR corpus:** 429 sources fired, **238 ready / 191 errored**. Reference basis CONFIRMED in the source titles: Neufert 58, "human dimension" 47, ergonomics 46, NKBA 27, Panero&Zelnik 23, ANSI/BIFMA 18, anthropometric 19, SMPTE 7, THX 4. Some values also lean on secondary web summaries (e.g. a TV-mount-height calculator) consistent with the named standards.
**Transcript:** `nlm-ergonomics-2026-07-03-qa-history.json` (this dir).
**Marker note:** `[n]` in the answer are NotebookLM answer-local citations into the 238-source corpus; the CLI exposes no answer→title map, so provenance is carried at the STANDARD level (each value names its standard: SMPTE/THX, Panero&Zelnik, NKBA, Neufert, ANSI/BIFMA) + this notebook. Verify against codes-th for any statutory overlap (codes-th always outranks).

## Question (verbatim)
> Compile authoritative human-factors and ergonomic standards for RESIDENTIAL interior design layout, with specific metric numeric dimensions and their sources. Cover: (1) TV viewing distance/height/angles; (2) standard furniture dimensions; (3) living-room seating arrangement; (4) bathroom clearances + wet/dry zoning + frequency ordering; (5) kitchen work-triangle; (6) circulation + bed clearance; (7) reach zones + door swing. Prioritize Panero&Zelnik, Neufert, NKBA, THX/SMPTE, ANSI/BIFMA. Give metric number + context + source.

## Answer (turn 3, verbatim)

**1. TV/Flat-Screen Viewing**
- **Viewing distance** (by horizontal FOV): **SMPTE** (30° FOV) = screen diagonal × **1.6**; **THX** 36° (balanced) = × **1.4**; THX 40° (immersive) = × **1.2**. E.g. a 65-in (1651 mm) screen → 2642 mm (SMPTE) / 2311 mm (THX 36°) / 1981 mm (THX 40°). [SMPTE/THX]
- **Screen mount height** (center above finished floor): living-room seated = **1016–1118 mm (40–44 in)** at relaxed eye level; bedroom reclined ≈ **1270 mm (50 in)**, tilted down **10°–15°**. [web-summary of AV practice]
- **Viewing angles:** vertical **≤ 15°** above/below seated eye level (absolute max **35°**); horizontal off-axis **≤ 40°** (THX) or 45° (cinema). [THX]

**2. Standard Furniture Dimensions**
- **Bed sizes (Panero&Zelnik):** Twin/Single **991 × 1905 mm**; Double/Full **1372 × 1905 mm**; Queen **1524 × 2032 mm**; Eastern King **1930 × 2032 mm**.
- **Seating:** seat height **400–450 mm**; sofa seat depth **400–550 mm**; lounge/easy chair depth **500–660 mm**.
- **Table heights:** dining/desk **720–760 mm**; coffee **300–460 mm**; side/end **380–480 mm** (match sofa armrest).
- **Casework depth:** wardrobe **600 mm** (min 500–550 mm with sliding doors); dressers/chests **457–500 mm**.

**3. Living-Room Seating Arrangement**
- **Sofa-to-coffee-table:** min **300 mm** (tight); **460 mm (18 in)** comfort, no passage; **920 mm (36 in)** if a person passes.
- **Conversation:** seats angled **180° (face-to-face)** or **90° (L-shape)**; min **100 mm** between independent pieces. (Max face-to-face distance not in sources; vault residential-clearances has 2134–2845 mm from P&Z.)

**4. Bathroom Clearances**
- **WC (NKBA):** min compartment **762 × 1524 mm (30×60 in)**; clear floor **762 × 1219 mm (30×48 in)**; WC centerline **406–457 mm (16–18 in)** from side wall.
- *GAP: basin/shower/tub-to-fixture spacing, wet/dry zoning, and frequency-of-use ordering NOT in the corpus.*

**5. Kitchen Work-Triangle** — *GAP: named but no metric leg/perimeter limits in the corpus.*

**6. Circulation & Walkways**
- **Walkway (Neufert):** min **600 mm** (1 person); comfortable **800–900 mm**; two-person **1200–1500 mm**.
- **Bed:** under-bed-drawer kneel/activity zone **1168–1575 mm** beside the bed; +**762 mm (30 in)** if circulation bypasses the activity zone.

**7. Reach Zones & Door Swing**
- **Reach:** bathroom frequent-use storage **381–1219 mm (15–48 in)** above floor; wheelchair forward reach **1219 mm**, obstructed high **1117 mm**; high-shelf comfortable reach ≈ **1981–2286 mm** (M) / **1854–2007 mm** (F), typically placed lower for 5th-percentile.
- **Door:** interior door width **800–900 mm**; *swing-arc clearance metric not in sources beyond leaf width.*

## Remaining gaps → follow-up DR (fired 2026-07-03)
Bathroom fixture-to-fixture spacing + wet/dry zoning + frequency ordering (GS-05); kitchen work-triangle metric limits.
