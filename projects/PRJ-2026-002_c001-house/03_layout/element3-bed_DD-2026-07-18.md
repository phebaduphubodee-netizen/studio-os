# Element 3 — The bed + its base (เตียง+ฐาน)
## Design-Development decision record — 2026-07-18

> **What this is.** Element 3 of the master-suite DD: the HERO of the room — the
> bed, its BASE, the bedding, the two lamped nightstands that flank the head, the
> foot bench, and the rug under it. The head meets the element-1 oak slat wall
> (BF14 = "ผนังระแนงหัวเตียง"); the foot faces the element-2 west wall. After owner
> sign-off this folds into `master-suite.CANONICAL.spec.json`.
> **Method.** Furniture geometry INK-READ from the designer's furniture plan
> (deterministic + visual, see Provenance — NOT the 30-agent adversarial read the
> WALLS of elements 1–2 needed; this is four clean rectangles). Composition /
> ergonomics grounded vault-first, every value traced to drawn ink, a cited datum,
> or a flagged studio default. **Privacy.** All plan reads LOCAL.

---

## 0. The pieces (INK-READ 2026-07-18, owner premise CONFIRMED)

Full record: `element3-bed_ink-read-2026-07-18.json`. Frame = room mm, x EAST from
the master west wall, y NORTH from the south glazing. Calibration re-proven this
run against BF14 (x5203.2 & x5301.6, y-450.2→2800.0, len 3250.2 = spec exact).

| piece | ink TRUTH (0.6pt furniture pen) | note |
|---|---|---|
| **bed** | x3203.6→5203.2 (**E-W head-foot 2000**) × y51.3→2200.1 (**N-S width 2149**) | head **EAST**, flush on BF14 face x5203.2 |
| **bench** | x2654.5→3152.8 (498) × y625.8→1625.6 (1000), rounded corners | at foot, 50.8 mm gap; centred on the bed |
| **nightstand NE** | x4701.8→5203.2 (501) × y2200.1→2698.4 (498) + round lamp | against BF14, flanks head N |
| **nightstand SE** | x4701.8→5203.2 (501) × y-450.2→51.3 (501) + round lamp | against BF14 S; S half in front of glz-east return |
| **platform / ยกพื้น** | **NONE drawn** (verified numerically + visually) | "ฐาน" is the bed BASE, not a built riser |

**Head = EAST, three-way confirmed:** two pillow outlines (0.12pt) against the east
end at x4520.8/x4603.4; a turned-back duvet fold at the NE head corner; the east
edge sits exactly on BF14's face. The **headboard IS the wall** — no separate
headboard drawn; the pillows lean on the oak slats.

**OWNER-CONFIRMED PREMISE (2026-07-18, the two forks that gated this DD):**
1. **"ฐาน" = the bed's own designed BASE** (a platform-bed plinth), NOT a raised
   floor (ยกพื้น). The plan draws no platform; the owner chose the base reading.
2. **Bed footprint = the INK-DRAWN 2000 (E-W head-foot) × 2149 (N-S width)**, head
   EAST — NOT the spec's transposed 2134 × 1981. This is a wide, near-square
   feature bed: the "7'" is the WIDTH (N-S), 6.5' the head-foot length (a standard
   ~2000 mattress length). Two-layer law: furniture is owner-authored; the ink is
   the designer's drawn intent and the owner adopted it.

So the room reads, foot-on: **a low upholstered platform bed whose head disappears
into the warm oak slat wall, flanked by two dark lamped nightstands, a bench at the
foot, all grounded on a soft neutral rug that pulls the oak floor back to 30%.**

---

## §0b · What this sheet can and cannot be asked

Same drawing-tier / pen-resolution law as elements 1–2. At 1:75 a 0.6pt pen covers
15.87 mm; nothing finer than ~2.5 mm is real. The furniture plan answers WHERE /
HOW BIG / WHAT IT IS (bed, bench, side tables, lamps) to ~2.5 mm. It does **not**
carry: bed/base **heights**, base **material**, bedding, lamp type/height, or any
z — those are ours to DESIGN or the owner's to answer, and their absence is not a
finding. There is **no drawing-vs-schedule conflict** on this plane (unlike BF11's
depth) — only the spec-vs-ink furniture reconciliations of §0, which the owner has
signed.

---

## §1. GROUNDED evidence (vault-cited — safe to gate a decision)

**Circulation** (`ergonomics/residential-clearances.md:46-49`, P&Z §2.3):
- **914 mm** general circulation/access around a bed; **660–762** tight (bending to
  make a high bed); **930–991** kneeling to make a low bed. → The bed's usable
  circulation is on the FOOT/WEST side: foot x3203.6 → bench → the clear standing
  band gives **~1749 mm** west of the bench (bookshelf front x905.6). The N/S sides
  are tight by the drafted room (nightstands flank the head, then wardrobe/glass) —
  a KNOWN owner-accepted reality (derivation-notes: "the REAL drafted room is that
  tight"), not a new defect.

**Composition** (`styles/color-composition.md#L47-56, L69-79, L140-157`):
- **60-30-10 LOCKED**: cool plaster **60** (ground) / light oak + **textiles/rug 30**
  (secondary) / brass **10** (accent).
- **Single-large-focal**: the bed is the solo compositional anchor; **foreground
  layering** (bench, rug edge) builds depth and kills "head-on empty frame"
  flatness.
- **Odd-groupings**: the bed's masses read as **3** distinct blocks (the oak slat
  headboard wall + the bed + the paired nightstands-as-one rhythm).

**Anti-monopoly — the bed base** (`_inbox/nlm-element1-dressing-wall-2026-07-16.md#L35`):
- "quantity = size × recurrence (Albers): the same wood on the floor (60%) AND a
  feature wall is what manufactures a mono-timber monopoly." With **four oak masses
  already** present (BF14 slat wall, BF09-3 wardrobe, west bookshelf shelves, BF11
  vanity), a fifth oak bed base violates it. **The bed base must NOT be oak.**

**Bedding + rug** (`styles/color-composition.md#L174-186`;
`materials/residential-materials.md#L149-151`):
- Bedding = **stonewashed linen**, "the heavy drape of linen is critical to
  convincing the eye" + **micro-imperfections (wrinkle/pilling)** so it reads used,
  not synthetic-smooth.
- Rug = **poly-wool blend** (solution-dyed synthetics "resist tropical mildew +
  humidity better" than natural fibre); footprint under the bed demotes the oak
  floor to the 30% layer (D1-A).

**Bedside lighting** (`lighting/lumen-method-and-fixture-placement.md#L73,89,94`;
`lighting/residential-lighting.md#L45-54`; `classifications/render-defects.md#L42-51`):
- Bedside reading **323–538 lux**, **CCT 2700–3000 K**, **CRI ≥90**.
- **CCT layering SAFE**: 3000 K ceiling (element-1 D1-A cool-ground) + 2700–3000 K
  bedside lamp are both in the warm residential band — no clash.
- **PH-02 brightness-ordering**: a secondary source (bedside lamp) must NOT out-emit
  the primary (the garden glazing) in a day scene. The rule tests INCIDENT light,
  not material albedo — a brass lamp is fine as long as it is dim vs the windows.

**Brass accent** (`styles/color-composition.md#L211-213, L55`;
`materials/aella-hardware-th.md`): brushed brass hides fingerprints; brass is the
**10% accent carrier** — appropriate at the lamp base, orthogonal to PH-02.

---

## §2. CONVENTION — studio defaults for the vault GAPS (candidate, not grounded)

The vault has NO bed/base ergonomic heights (confirmed GAP, all three lookups).
These are RENDER-TIER, several already owner-seen, carried as studio defaults:

- **Mattress-top height 600 mm** — the spec's `h600`, already in element-1's render
  ("the bed 600 mm sits below the 1.15 m lens"), owner-seen; not re-opened.
- **Base / mattress split 50/50** (base ~300 upholstered plinth, mattress ~300) —
  `_build_bed` default; reads as a platform bed. [est]
- **Bench 450 h × ~1000 × 498** — spec `h450`, ink footprint; a standard seat height. [est]
- **Nightstand ~500 sq × height ~450–500** (side/end table band 380–480 AFF,
  `tv-viewing-and-furniture-dimensions.md#L40`; ~50–100 above the mattress is the
  ergonomic reach — vault-uncited INFERENCE). [est]
- **Table-lamp overall ~450–550 tall** (dome/"mushroom") — shade centre near the
  seated-reading plane; vault-uncited. [est]

## §3. OPEN — supplier / owner / render-tier (do NOT fabricate)

- **Bed/base + bench heights, base material spec, upholstery abrasion grade**
  (Wyzenbeek/Martindale) — vault GAP; building with the §2 defaults, flagged.
- **Nightstand-to-mattress height relationship** — vault GAP; §2 inference.
- **Lamp SKU + exact height + lumen output** — stage-05 / supplier tier; the render
  places a representative dome lamp at PH-02-safe intensity.
- **Rug exact dimensions/weave SKU** — supplier tier; spec footprint stands.

## §4. DECISION MENU — DECIDED, grounded (not a taste menu; D7 discipline)

Per the element-1 D7 rule (owner is an engineer, not a designer): DECIDED, to be
built, rendered, and SHOWN — not offered as A/B/C taste picks. The governing idea:
**the bed is the soft neutral hero that lets the warm oak slat wall be its
headboard** — which is exactly how 60-30-10 is kept (oak stays 30%, the bed base
joins the plaster ground, brass is the 10% at the lamps).

**D3-1 · Bed base — upholstered greige stonewashed-linen platform plinth** (NOT oak;
§1 anti-monopoly). A low ~300 mm plinth base + ~300 mm mattress = a platform bed
(total h600). Head **flush to the BF14 slats** — the wall IS the headboard, no
separate headboard mass; pillows lean on the oak. The base's greige linen **joins
the ~60% plaster ground** (Albers: a light element on a light ground recedes — the
same grounding the curtain DR used for the opaque layer, `3ce5f5e`), so the OAK
headboard wall and the bedding carry the eye, not the base.

**D3-2 · Bedding — greige-oatmeal stonewashed linen**, heavy drape + micro-wrinkle
(§1), a turned-back duvet fold at the head (the "made-bed" cue `_build_bed` already
emits), two plump pillows against the slat wall. This is the room's **textile
layer** (element 3+'s ผ้า sub-part starts here).

**D3-3 · Nightstands + lamps — two dark low cabinets, brass dome lamps.** Match the
ink (~500 sq, not the spec's 300). **Material = matte-dark** (the established "matte
black + brushed brass accents" story, batch001) — a cool/dark small mass **pops
against the warm oak headboard wall** (a small oak nightstand would melt into BF14),
and stays out of the oak count. Each carries a **brass-based dome/"mushroom" table
lamp** (the drawing's round lamp symbol; ref image #3 mood): CCT **2700–3000 K**
(warm band, CCT-safe with the 3000 K ceiling), **CRI ≥90**, output tuned to
**323–538 lux** at the reading plane and **dim vs the garden windows** (PH-02). Brass
= the 10% accent.

**D3-4 · Bench — upholstered greige linen** (matches the base), at the foot,
~1000 × 498 × 450, the foreground-layering mass that builds depth (§1).

**D3-5 · Rug — poly-wool herringbone**, under the bed + foreground (spec item
already present), demotes the oak floor to 30% and cuts the warm floor-bounce that
kept the cool plaster reading beige (D1-A, LOOK 2026-07-16).

**D3-6 · Materials under anti-monopoly + PH-02 + the material_story rule.** The bed
base / bench (upholstered linen), nightstands (matte-dark), lamps (brass), and rug
(poly-wool) must all be **named in the render's material_story** so the Gemini
polish pass cannot repaint the base oak or drop the lamps — the exact element-2 trap
(the cool counter reverting to warm; `961bbea`). NOTE the build constraint:
`material_presets.UNAPPLIABLE_KINDS = (bed, bench, rug)` — these are bespoke builders
the preset system cannot retint, so their materials are set IN `_build_bed`/
`_build_bench`/`_add_rug` and must be surfaced to `material_story()` another way
(the `fabric`/`neutral` families, or a bed/lamp branch — build layer, §6).

## §5. Owner / designer numbers still needed (minimal)

- Bed/base/bench heights + upholstery grade (vault GAP) — building §2 defaults.
- Nightstand + lamp exact height/SKU/lumens — stage-05 / supplier.
- Rug exact size/weave — supplier; spec footprint stands.

## §6. After sign-off — fold into canonical spec

- `items` **bed**: x3092→**3203.6**, y110→**51.3**, w2134→**2000**, d1981→**2149**
  (keep rot270 head EAST); add an element-3 `design` block (base = upholstered
  linen platform; head flush to BF14).
- `items` **nightstands** (×2): w300→**501**, d→**498/501**, position to ink; add
  `lamp: true` (brass dome) + design block.
- `items` **bench**: confirm ink ~498×1000 (spec 504×1002 ✓).
- **Build**: `_build_bed` base material → greige linen (retint from the current dark
  base); NEW `_build_nightstand` (solid low cabinet, not the spindly `_table`
  primitive) + `_build_table_lamp` (base + stem + dome); route all four into
  `material_story()` (§4 D3-6).
- `eye_camera_variants`: ADD a **bed-hero** verify view (stand W of the foot, look E
  across the bed to the BF14 slat headboard wall — the old
  `eye-camera.master_bedroom.json` [1350,1500]→[5150,1000] framing).

---

## Provenance

- **Ink read**: deterministic + visual, 2026-07-18 (recovered `ink.py`, calibration
  `floor2-walls-mm.json` 26.45 mm/pt). NOT a 30-agent adversarial workflow — the bed
  zone is FF&E (four clean rectangles + a pillow pair), not the contested WALL
  geometry of elements 1–2; over-instrumenting it would be the "factory of referees"
  the project-reset warns against. Verified two ways (minlen-100 numeric sweep +
  rendered crop). Result: `element3-bed_ink-read-2026-07-18.json`.
- **Owner premise** (base-not-platform + ink footprint): confirmed 2026-07-18.
- **Base geometry**: designer furniture plan
  `00_intake/raw-local/The City …_Plan funiture 02.pdf` (page 1, vector).
- **Design grounding — vault-first, NO fresh NLM DR** (consistent with element 2's
  owner choice). Three knowledge-manager lookups (§1, cited) + element-1's distilled
  NLM files. The ergonomic HEIGHTS the vault lacks (bed/base/bench/nightstand) are
  studio defaults (§2), several already owner-seen in element-1's render — RENDER-
  tier, not gating. If the bed composition is ever contested, the a5a43395 DR
  (single-large-focal hero, textile-as-softener, cool-vs-warm balance) is the lever.
- **Carried from elements 1–2**: the locked palette (oak veneer / cool plaster /
  microcement / satin brass / matte black), the 60-30-10 anti-monopoly (D1-A), the
  PH-02 brightness rule, and the D7 decide-build-render-show discipline.
