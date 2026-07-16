# Element 1 — the oak signature wall (BF14 slat headboard + BF09-3 open dressing wall)
## Design-Development decision record — 2026-07-16

> **What this is.** The first *detailed-design* element of the PRJ-2026-002 master suite,
> per the direction reset (design a room, don't measure one). Takeoff is CLOSED; this designs
> the flat brown slab the eye-render exposed (`pipeline/output/room_bedroom_suite_eye_canon16eye.png`)
> into an articulated warm-oak OPEN dressing wall. Mood = owner in-session image #3
> (light-oak open wardrobe, brass rails, floating drawers, open shelving, floating oak
> nightstand + mushroom lamp, slatted oak headboard). Feeds `../master-suite.CANONICAL.spec.json`
> geometry AFTER owner sign-off, then distils to `knowledge/` as reusable studio library.
>
> **Method:** vault-first → NLM DR (notebook `a5a43395`) fired on the vault GAPS only.
> **Privacy:** generic/banded questions; no client identity left the machine.

---

## 0. The two pieces (from the canonical spec — geometry is fixed, this designs the FACE)

- **BF14 — vertical-slat headboard.** East wall, `x5150`, `y110→2650` (**length 2540 mm**),
  `h2800` full-height, 100 mm thick. Stands IN FRONT of the black-alu glass return
  (`glz-east`); the bed head pins to this SOLID wall. N end meets BF09-3 @ y2650; S end meets
  the curtain track @ ~y110 `[est — owner to confirm]`.
- **BF09-3 — open dressing wall.** Runs along `y2650`, `x2300→5600` (**length 3300 mm**),
  **600 mm deep**, `h2800`, `open:true` — oak carcass, brass hang-rails, floating drawers,
  open shelves, **NO doors**. The signature piece.
- They meet at the **NE inside corner** → must read as ONE oak system turning the corner.
- **The load-bearing risk (already proven):** oak floor + oak BF14 + oak BF09-3 =
  the *mono-timber "wood monopoly"* the interior-render-critique DR caught scoring 5/5-blind
  (commit 94648d3). The black-alu glass, brass, and a contrast tone are the levers out.

---

## 1. GROUNDED evidence (NLM a5a43395, cited — safe to gate a decision)

### 1a. Ergonomics — Ask 1, source `a1383994` (anthropometric drawings; P&Z-class)
| Datum | Value | Design consequence |
|---|---|---|
| Seated makeup-mirror centre / eye level | **1120–1267 mm AFF** | mirror centre ≈ 1.2 m at the vanity (element 2, west) |
| Face-to-mirror viewing distance | **457–610 mm** | vanity depth / mirror set-back |
| Useful mirror field height | **610–762 mm** | |
| Vanity seated work-surface height | **711–762 mm** | (matches spec BF11 h750 ✓) |
| Vanity usable width | **1067–1372 mm** | |
| Knee/thigh clearance under vanity | **≥ 196 mm** | apron/drawer underside limit |
| **Vanity-in-a-wardrobe-run circulation aisle** | **1067–1168 mm** (NOT 914) | where the dressing aisle doubles as seated-vanity + standing-wardrobe use it must **widen past 914 mm** |
| Hang-rail arm-swing aisle | **914 mm** min | clear in front of BF09-3 rails |
| Rod-to-shelf-above clearance | **+102 mm** | hanger lift-off |
| Folded-shelf comfortable reach depth | **457 mm** (5th-pct F) | **BF09-3 is 600 mm deep** → the back ~150 mm is a stretch: put daily folded goods ≤450 mm front, seasonal at back |

### 1b. Composition — Ask 4, sources `28fa10cb` (Albers, *Interaction of Color*), `109b32e1` (Postell, *Furniture Design*), `56678948` (design-principles)
- **60-30-10 + "quantity = size × recurrence"** (Albers): oak in the floor (60%) *and* the wall
  (30%) is what manufactures the monopoly. **Escape:** demote the floor's visual weight
  (large soft rug at the bed) so oak reads as the **30% secondary**; keep brass as the **10% accent**.
- **Offset the oak** (Albers "a ground subtracts its own hue"): warm-painted walls would *wash the
  oak out*. Put the remaining 60% in **matte, cool-toned off-white limewash / plaster / textured
  linen** — low-frequency texture that rests the eye and lets the oak grain read.
- **Black-alu glass is an ASSET, not a clash** (Albers "hard boundary = separation"): the black
  frame enforces an intentional split between warm interior and glass — it *frames* the oak.
- **Four functions → THREE masses** (Odd Rule + "stripes read almost shapeless"): compose BF09-3
  so the wall is legible, not busy — slat field as a calm continuous backdrop, joinery grouped
  into three architectural masses (below).

## 2. CONVENTION — verify before CDs (NLM model-memory Ask 2/3 + vault; NOT statute)

> NLM honestly flagged detailing + material-durability as *outside its sources* and answered from
> model memory. Treated here as **candidate conventions to verify** against AWI / supplier / Thai
> practice — never cited as grounded. Vault corroboration noted where it exists.

- **Slat rhythm:** 1:1–2:1 slat:gap, **50–66 % solid**; section **20–25 mm deep × 20–50 mm face**
  [NLM-unsourced]. *Vault:* Wall-Thailand `SQW10` 10×150 slat, `AKUWALL` oak-veneer acoustic slat
  27 mm @ 13 mm gap, NRC 0.8, offered for headboard use
  (`knowledge/materials/wall-cladding-and-decorative-mouldings-th.md`).
- **Backing + termination:** continuous ply/MDF backing (matte-black or matching veneer), **10–15 mm
  shadow-gap reveal** at floor/ceiling/wall, terminate into a solid corner post [NLM] — *vault:*
  render-critique DR requires resolved terminations (wrap / mitre / L-bead) + 10–20 mm Z-reveals +
  10–15 mm zocalo (`knowledge/_inbox/interior-render-critique-DR-2026-07-15.md`).
- **Fixing:** concealed — French cleat / Z-clip for the slat panel; wall-hung joinery on concealed
  steel suspension brackets into blocking; **no face screws** [NLM-unsourced].
- **Floating plausibility:** 10–20 mm shadow reveal behind carcass; recessed zocalo set back
  100–150 mm if full-float can't be structural; **shelf span ≤ 800–900 mm** before a divider;
  **cantilever depth ≤ 300–400 mm** (600-deep floating drawers therefore need suspension brackets,
  not pure cantilever) [NLM + vault load-path rule].
- **Material build (humidity):** veneer over **engineered core (MR-MDF / exterior ply), not solid
  oak**; EMC target **~10–14 %** (Thailand); acclimatise **72 h–1 wk with AC on** before fixing;
  **film-forming finish (satin PU / lacquer) over open-pore oil** to slow moisture exchange and
  resist veneer delamination; **edge-band every exposed edge** (the moisture seal) [NLM + vault:
  engineered > solid in tropics, edge-banding = moisture seal — `residential-materials.md`,
  `millwork-casework.md`].
- **Open-wardrobe reality:** open airing is *anti-mildew* (good in the tropics) **but collects
  dust** → keep dust-sensitive items in the closed drawer stack; consider a garment-bag zone for
  seasonal hanging [NLM-unsourced].
- **Brass finish:** **satin/brushed hides fingerprints + water-spots**; polished shows every mark;
  lacquer prevents tarnish but chips blotchily [NLM] — *vault:* AELLA Satin Brass (SB) line exists
  (`knowledge/materials/aella-hardware-th.md`).

## 3. OPEN — supplier / owner-gated (NOT answerable by NLM; do not fabricate)
- AELLA brass: **solid vs plated**, base-metal, load rating (catalogue silent) → supplier query.
- Soft-close + cantilever **load tables** (Häfele/Blum/supplier).
- Local **edge-banding gauge**, Thai **TIS/มอก. panel standard**, E0/E1 formaldehyde class.
- **Sellable-palette proof** — our *local* benchmark (designer-labelled anchors), not a corpus.

---

## 4. DECISION MENU — choices + reasons (⭐ = my grounded recommendation; owner/client picks)

### D1 · Anti-monopoly strategy — *the load-bearing call*
- **⭐ A. Oak as the 30 % secondary.** Non-oak walls + ceiling in **matte cool off-white
  limewash/plaster**; a **large soft rug** demotes the oak floor; brass = 10 % accent; a subtle
  contrast on the drawer fronts (see D3). → textbook 60-30-10, Albers-grounded, escapes the proven
  monopoly.
- B. All-oak monolith (mood #3 literal) — rely only on glass + textiles. → highest monopoly risk;
  the exact failure the critique DR caught. *Not recommended.*
- C. Heavy two-tone (oak slats + off-black joinery). → strong contrast but risks "busy" against D2.

### D2 · Slat headboard rhythm (BF14, 2540 mm long × 2800 high)
- **⭐ A. 40 mm face × 20 mm gap (2:1, ~66 % solid), 20–25 mm deep**, oak veneer on matte-black ply
  backing, 10–15 mm shadow-gap top+bottom, terminating into a solid oak corner post at BF09-3. →
  calm continuous field (Albers stripes), resolved terminations, robust; ≈42 slats over 2540 mm.
- B. Fine 20×20 (1:1, 50 % solid) → more delicate, busier, ~63 slats.
- C. Wide 60 mm reveal → reads "panelled," heavier.

### D3 · BF09-3 composition — 4 functions → 3 masses (3300 mm run)
- **⭐ A. Asymmetric 3-mass:** [1] open **hang-rail bay** (brass rail, ≥914 clear) · [2] unified
  **floating drawer + open-shelf tower** (the vertical divider that also solves the ≤900 mm span) ·
  [3] the slat field / a display niche turning the corner. Odd-rule, legible.
- B. Symmetric (drawers centred, rails flanking) → formal, calmer, less dynamic.
- *Depth note:* shelves usable ≤450 mm front (daily), back 150 mm for seasonal (reach 457).

### D4 · Hang-rail + hardware finish
- **⭐ Satin/brushed brass**, Ø25–28 mm round rail; short-hang 1000–1150 + full-hang 1600–1750
  zones; +102 mm to shelf above. → satin hides humidity marks (Ask3); AELLA SB line exists.
  *(Solid-vs-plated + load rating = supplier query, D-open.)*
- Alt: polished brass — mirror-bright but shows every fingerprint/water-spot in a humid bedroom.

### D5 · Material build + finish (humidity)
- **⭐ Oak veneer over MR-engineered core**, satin **film-forming** finish, edge-banded, acclimatised
  72 h–1 wk. Closed drawers for dust-sensitive items. → engineered > solid in tropics; film finish
  resists delamination; open airing offset by closed dust zones.
- Alt: solid-oak slats — warmer/authentic but real warp/cup risk in AC humidity swings.

### D6 · Contrast tone (pairs with D1)
- **⭐ A. Cool matte plaster/microcement** on drawer fronts or the tower back — adds depth, reads
  intentional against oak + black-alu.
- B. Honed stone accent (one shelf/counter) — richer, higher cost, supplier-gated.
- C. None — oak-only, lean entirely on glass+rug+textiles for contrast.

---

## 5. Owner numbers still needed (blocks geometry, not this DR)
- **BF14 south end** — trimmed to `y110` `[est]` to meet the track "แถว ๆ south-of-bed". Confirm.
- Sliding pocket door — width **1600 (2×800)** and **y≈6250** `[est]`; panels+pocket confirmed, numbers not.

## 6. After owner sign-off
1. Fold D1–D6 picks into `../master-suite.CANONICAL.spec.json` (BF14 slat params; BF09-3
   sub-mass layout + rail/shelf/drawer geometry; wall-finish + contrast material).
2. Re-build + **eye-verify** (owner lesson: LOOK, don't trust numbers).
3. Distil the reusable rules (slat rhythm, tropical veneer finish, open-wardrobe ergonomics,
   anti-monopoly palette) into `knowledge/` as the studio's element-1 library entry.

## Provenance
- NLM notebook `a5a43395` (Design Systems), asks 1–4 this session; raw JSON in session scratchpad
  (`nlm-e1-ask{1..4}-*.json`). Ask 1 (ergonomics) + Ask 4 (composition) grounded+cited; Ask 2
  (detailing) + Ask 3 (material) honestly outside-sources → convention tier.
- Vault recon: 6 knowledge-manager agents, cited have/gap maps (workflow `wf_921373d1-f0f`).
- Base geometry: `../master-suite.CANONICAL.spec.json`; corrections `v4/OWNER-CORRECTIONS-2026-07-16.md`.

---

## 7. BUILD-LAYER LOG — the render that SHOWS the design (2026-07-16, after sign-off)

The proof render (`pipeline/output/room_bedroom_suite_eye_e1palette.png`) proved the *palette* lever
(de-wood), but `build_room` still drew BF09-3 as a **closed box** and could not show the slat rhythm,
the open joinery, the brass, or the microcement. This session taught the materializer to render the
signed design. **Deliverable render: `pipeline/output/room_bedroom_suite_eye_e1build.png`.** All by
LOOKING (owner's law), not by trusting a score.

**What the build layer added (design-visualization, NOT a new instrument):**
- `millwork.millwork_parts` gained an **open dressing-wall branch** (opt-in `open:true`): a 3-mass
  asymmetric composition (D3-A) — a brass hang-rail bay · a floating-drawer + open-shelf **tower**
  (the divider that keeps every display-shelf span ≤ 900, Ask1) · a corner display niche. NO leaves.
  Same CAD invariant as the door run (a part may never leave the plan bbox; unit-tested).
- The headboard slat branch now reads the **design block** → BF14's signed **40 face / 20 gap / 22
  deep** (D2-A, 66 % solid, 42 battens over 2540). Absent a design block it keeps the old defaults.
- Four **material presets** carry the signed palette: `oak_veneer` (light oak, D5-A) · `cool_plaster`
  (D1-A cool ground) · `microcement_cool` (D6-A drawer fronts / tower back) · `satin_brass` (D4-A
  rail). `_suite_materials` routes the open-wall sub-parts by name (rail→brass, front/towerback→
  microcement, else oak).
- An `eye_camera` block frames the NE corner (BF14 meets BF09-3); a `light_warm` spec override cools
  the ceiling CCT (defaults untouched → every other render is byte-identical).

**What LOOKING caught that numbers didn't (3 render passes):**
1. **Pass 1 → the room rendered ORANGE.** The signed cool plaster read as saturated amber. Cause was
   NOT the wall albedo — it was the default **2400 K amber downlights** (1.0,0.82,0.60) flooding an
   enclosed, saturated-oak room, plus warm oak bounce. The mono-timber failure returned in *light*
   form. Fix: a 3000 K warm-**white** `light_warm` for this shot + a **desaturated** oak preset.
2. **Pass 2 → oak now reads light honey; slats, open joinery, brass, cool drawers all show.** But the
   plaster still read warm-beige (oak floor-bounce).
3. **Pass 3 → added the D1-A rug** (the signed floor-demotion lever). The neutral herringbone grounds
   the foreground and cuts floor-bounce; palette now clearly **oak + cool grey + white + brass** —
   the monopoly is broken. **Honest residual:** the upper plaster still reads warm-neutral, not
   cold-cool (enclosed bounce; the only cached HDRI is a warm brown studio — a cool daylight HDRI or
   a cool garden key through the south glass is the next lever, deferred, owner-directable).

**Review-hardening (pass 4).** A 5-lens / 22-agent adversarial review (workflow `wf_ebee49f7-b43`)
returned 14 confirmed findings; ALL fixed — and two were design-fidelity fixes that materially
improved the render, not just bugs:
- **The slat BACKER was rendering oak**, silently contradicting the signed **matte-black ply** (D2-A).
  Added a `matte_black_ply` preset + routed the backer to it. The black ground behind the battens is
  what makes the 40/20 rhythm *read as slats* — pass 4's wall is crisp where pass 3's was soft.
- **The hang bay had ONE rail at 2.37 m**; the signed **two-zone** arrangement (double short-hang +
  single full-hang, D4-A) was dropped. Added a mid-gable splitting the bay into a double short-hang
  zone + a full-hang zone — which ALSO fixed a real 1.46 m unsupported bay-shelf span (the span test
  had *hidden* it by excluding that shelf; the exclusion is now gone).
- Robustness: slat-design typos (metre/mm slip, sign-flip, extra zero) now **RAISE** instead of
  emitting 42 k slivers or a silent box; `light_warm` is shape/range-validated (fail loud); the
  material router is a pure `mill_object_role()` that no longer mis-paints a fallback box whose spec
  NAME contains 'front'/'rail'; the microcement tower back is drawn side-by-side with the oak backs
  (no cross-material z-fight).

**Coverage / status:** tests 167 in millwork+presets (open branch, slat override + validation, two-zone
rails, span rule, routing incl. fallback-safety, presets exact-pinned, light_warm); full pipeline suite
**1581 green**. Opt-in throughout — no existing render changes (proven by the light_warm/open/design
default-preservation pins). Deliverable render regenerated: `room_bedroom_suite_eye_e1build.png`.
Owner numbers still open (do NOT block this render): BF14 south end `y110`; sliding pocket door
`1600 (2×800)` @ `y≈6250`. Residual (owner-directable): the cool-plaster ground still reads
warm-neutral in the enclosed oak room — a cool daylight HDRI / cool garden key through the south glass
is the next lever (deferred; the only cached HDRI is a warm brown studio).
