# Element 4 — Ensuite (ห้องน้ำในตัว) Design Development · 2026-07-18

**Provenance.** Grounded in the `ensuite-dd-research` workflow (6-dimension vault
sweep → per-dimension adversarial verify → synthesis → critique; run
`wf_0fd0028a-160`) AND a firsthand cross-read of the cited files by the author, to
guard against the "a big workflow can be confidently wrong" lesson (correction #11b).
Every value below traces to a `knowledge/` path, or is tagged `[est]` (render-tier,
owner-vetoable) or `[GAP]` (needs owner / designer / RCP / supplier / an NLM ask).
Authority order: `knowledge/codes-th/` (statutory) > client contract > studio
standards > references. Geometry this DD designs onto = the ink-read
[element4-ensuite_ink-read-2026-07-18.json](element4-ensuite_ink-read-2026-07-18.json)
(deterministic + visual; the `3.05` counter re-proved calibration).

Room (ink-true clear): **3.10 m (E-W) × 2.70 m (N-S), 8.36 m², ceiling 2800.**

---

## §1 Zoning — keep the drawn split (it already obeys studio doctrine)
Enter the door mid the **east/party wall** into a **~680 mm central circulation
strip**; **DRY south** = the double vanity on the full 3047 south wall + the WC in the
SW corner (tank on the west wall); **WET north** behind the glass partition at x1125 =
shower NW (1070×1276) + deck tub NE (2000 deck / 1700 inner, long axis E-W on the
north wall). This conforms to the studio GS-05 function rule — *basin nearest the
door, WC shielded deeper, shower/tub deepest, wet-zone centroid deeper than dry*
(`knowledge/ergonomics/bathroom-kitchen-planning.md` §L9-20).

**Envelope (STATUTORY, all PASS):** area 8.36 m² vs combined WC+bath ≥1.50 m² =
PASS ~5.6× (`knowledge/codes-th/mr39-fire-sanitation-ventilation.md` L19); ceiling
2800 vs ≥2.00 m floor-to-ceiling = PASS +800 (mr39 L21; `mr55-residential-dimensions.md` L22).

**The one binding constraint — the 680 strip.** Thai code sets **no** fixture-to-
fixture spacing (confirmed absent across mr39 + mr55); all spacing is ergonomic
REFERENCE (NKBA/Neufert/P&Z, `bathroom-kitchen-planning.md` L5-7). The 680 strip
**clears every floor** (code basin 533 / WC P&Z 610 / tub P&Z 600 / shower code 610;
Neufert walkway 600, `tv-viewing-and-furniture-dimensions.md` L63-65) but **WARNs
against comfort** (NKBA 762 / Neufert 700). It is *not* a statutory breach (the mr55
1.00 m corridor is a building corridor, not an in-room value). → **Owner render call:**
accept 680 on a rendered sightline, or steal depth from the vanity. Double basins fit
at **1050 c/c** (ink) vs the 914 c/c min (L27) — PASS.

## §2 The signature move — ONE warm-oak vanity, reverse-Albers
**A single warm light-oak floating double-vanity is the ensuite's ONLY oak gesture,
set as the lone ~30% focal against a fully COOL ~60% ground.** This runs the suite's
Albers lever *in reverse* from the bedroom: a cool ground *subtracts its own hue and
lightness* and thereby **amplifies the oak's warmth**
(`knowledge/styles/color-composition.md` §3). Crucially it **protects D1-A anti-
monopoly**: the bedroom already carries **four** oak masses (BF14 slat wall, BF09-3
wardrobe, west bookshelf, BF11 vanity), so the ensuite deliberately adds **zero** new
dominant oak block — oak stays the 30% secondary, one controlled accent, never a fifth
mass (color-composition §2 L47-55). **Wet-side coherence carrier:** the garden
(`rainforest_trail` HDRI — the *same* Element-1 exterior asset) read through **two
black-alu west casements** ties the wet zone back to the suite's garden view. Net: the
ensuite is unmistakably the same suite — cool ground, one warm-oak accent, satin
brass, garden beyond glass — without repeating the bedroom's oak density. **This is a
Claude design call (D-E4-1), owned as one; owner-vetoable on the render.**

## §3 Materials — the 60-30-10 roles
| role | material | source / status |
|---|---|---|
| **~60% cool GROUND** | Large-format **porcelain** to wet floor + wet walls (impervious to steam/humidity, ideal wet+tropical); cool grey. | `knowledge/materials/residential-materials.md` L46/L57 |
| ↑ dry walls/ceiling | **Microcement** (cool grey), **DRY-ZONE ONLY** | see GAP — microcement is **not** vault-rated for wet; no promoted file rates it for a shower pan. Kept off the wet zone. |
| **~30% warm OAK** | The **floating vanity cabinet body** — oak veneer over MR core, film finish (dry-zone, moisture-resistant). The single oak gesture. | color-composition §2; residential-materials (veneer over engineered core) |
| **~10% BRASS accent** | Satin-brass tapware / mixers / shower valve / towel rail | finish `[est]`; **SKU `[GAP]`** — `aella-hardware-th.md` is door+furniture hardware only, carries **no** tapware/sanitaryware |
| counter | cool-grey **Caesarstone** quartz (durable, non-porous — consistent with the element-2 vanity) | `residential-materials.md` L64; `caesarstone-engineered-stone-th.md` §5 |
| mirror | one **full-width frameless** mirror over the vanity (keeps brass off a large reflective plane so it never out-reads the west daylight) | design call (D-E4-2); render preset = polished-chrome proxy, roughness 0.02-0.05 floor (`bsdf-material-presets.md` §2) |
| shower glass | **frameless clear glass** enclosure + fixed partition at x1125, minimal **black-alu** hardware (cohere with the suite's black-alu windows) | design call (D-E4-3); PBR: Transmission 1.0, IOR 1.52, roughness ~0.02-0.05 (never 0.0 = the CG tell) + light smudge (`bsdf-material-presets.md` §2) |

`[GAP]` wet-floor **DCOF slip target + a floor-tile SKU/PEI** — `residential-materials.md`
names DCOF as a metric-to-check with no numeric value (its own gaps L188/L195); no
floor-tile product exists in the vault. Anti-mold กันเชื้อรา paint on the dry
ceiling/walls; **avoid vinyl wallcovering** (traps moisture → hidden mold,
`residential-materials.md` L55).

## §4 Lighting — 3 layers, one warm electric family + cool daylight
| layer | target | source |
|---|---|---|
| **ambient** | 20-30 fc = **215-323 lux** general, recessed downlights | `knowledge/lighting/lumen-method-and-fixture-placement.md` §2 L74 |
| **task (mirror)** | 50-80 fc = **538-861 lux VERTICAL on the face**, **CRI ≥ 90**, flanking the mirror | lumen-method §2 L75, §3 L94 |
| **accent** | niche / cove / tub wash, **~3:1** to ambient (overall contrast ≤20:1) | lumen-method §1 L46-49 |

**CCT law.** All electrics = a single warm **3000K** family (coheres with the suite's
3000K ceiling / 2850K bedside lamps; 3000-4000K is the vault bath band, lumen-method
§3 — the *use 3000K* pick is a coherence derivation, not a vault value). The **only**
second CCT is **cool daylight** through the west casements — which is exactly how the
≥2-CCT check is legitimately satisfied: **across KINDS (daylight vs electric), never by
two electric CCTs** in one zone (`knowledge/rendering/cycles-lighting-camera-presets.md`
§3; PH-03, `render-defects.md` L52). Statutory floor: bathroom ≥ **100 lux**
(mr39 ตาราง 3, L45) — our targets clear it.

`[GAP — STATUTORY, NOT INGESTED]` **wet-location luminaire IP rating** (IP44/IP65 over
shower/tub), IEC 60364-7-701 bathroom zones 0/1/2, and RCD protection live in the
วสท./EIT wiring code, **absent from `knowledge/`** — do **not** invent an IP value; this
is an M&E/electrical-designer statutory call. (The vault *does* carry the GFCI-within-
914mm-of-basin rule, `bathroom-kitchen-planning.md` L34.) Exact task-light Kelvin
within 3000-3500K and flanking-vs-bar placement = `[GAP]` (`residential-lighting.md`
own gap L43/L239).

## §5 Waterproofing & drainage
- **STATUTORY (mr39 ข้อ 9, verbatim):** whole finished floor graded **≥1:100** (~10 mm/m)
  to a low-point drain (L23); soil pipe **Ø≥100 mm at ≥1:10**, vent **Ø≥25 mm** (L24);
  septic/soakaway ≥10 m from public water (L25). The code mandates **only** slope +
  drain + pipe sizing — it is **silent on any membrane obligation**.
- **Best-practice (REFERENCE, does not override the 1:100 floor):** shower pan a
  separate **~2% fall** (`bathroom-kitchen-planning.md` L32); tanking/waterproofing
  **≥1829 mm AFF** or ≥76 mm above the head, whichever is higher (L33) — the shower
  niche **and** the west-window sill both fall inside this band.
- **Decisions (D-E4-4):** whole floor to 1:100; shower pan its own 2% zone; a **linear
  channel drain** along the glass/curb line at x1125 `[est` — drain type is not
  statutorily fixed]; a **low curb** retained (the brief draws one). Sequence: "floor
  leveling + waterproof" = a discrete phase before finishes
  (`studio-vault/.../07-construction-brief.md`).
- `[GAP]` membrane **type / coats / coving extent**; **curb height + numeric wet-area
  floor-drop (mm)** (the construction-brief leaves it "drop X mm"); the **glass-to-
  floor/curb junction** and the **west-window-sill** waterproofing detail — all designer/
  RCP tier.

## §6 Ventilation
STATUTORY: natural air-opening **≥10% of floor = 0.836 m²** OR a sufficient exhaust
fan (the *หรือ* makes these true alternatives, mr39 L22); mechanical exhaust for a
house bathroom **ACH ≥2 = 46.8 m³/h** (8.36×2.80×2, ตาราง 4 L54). **Decision (D-E4-5):
default to the exhaust-fan path (≥46.8 m³/h)** — do **not** rest compliance on natural
vent because the operable openable-glazing area of the two casements is undrawn
(`[GAP]`, owner). The windows remain a light + cross-vent bonus. Anti-mold paint on
the dry ceiling/walls. Fan CMH/SKU = `[GAP]` (no fan product in the vault).

## §7 Fixtures (owner-authored footprints from the ink; this DD dresses them)
- **Vanity (standing):** counter **~850 mm AFF** (standing grooming station — *not* the
  seated 750 of the element-2 makeup vanity; standing lavatory band 850-904,
  `residential-clearances.md` L72 / casework §4.1). Two basins 1050 c/c, oak veneer
  cabinet below (the single oak gesture), Caesarstone top, full-width frameless mirror.
- **WC:** SW, tank on the west wall, ~685 projection; front clear 680 = PASS P&Z 610,
  WARN NKBA 762. Wall-hung vs floor + exact side offset = owner/designer.
- **Tub:** deck 2000 / inner 1700, long axis E-W on the north wall; deck access 680 =
  PASS P&Z 600.
- **Shower:** 1070×1276 clears 900×900 (L30) but interior 1372 not met → **no built-in
  seat**. Frameless glass + partition at x1125.
- **Niche/storage:** recessed shower niche + a towel shelf sized to folded goods
  (towels 450 wide, ~200-250/stack; casework §2.1/§2.2) in the easy-reach 800-850 band
  (§2.4); the niche must sit **inside** the ≥1829 waterproofed band. Exact niche geometry
  + towel-bar AFF = `[GAP]` (only bounding datums exist).
- **Door: SLIDING / pocket** — an 800-900 swing arc fouls the 680 strip
  (`tv-viewing.md` L66; mr55 ข้อ 31 800×1900 is a **fire** door, no general interior
  min). Confirm the party wall can host a pocket (owner).

## §8 Open owner / designer questions
1. **Door:** confirm slide/pocket (vs a surface slider) — the swing fouls the 680 strip.
2. **680 central strip** is below NKBA 762 / Neufert 700 comfort (above code 533): accept
   on a render, or steal depth from the vanity? A "does 680 feel right" judgment.
3. **West casement sill/head z** (`[est]` sill ~1000, head ~2200-2400): drives both the
   garden framing and the wet-side sill waterproofing.
4. **Curb height + wet-area floor drop (mm)** — a constructability/tolerance call.
5. **Drain type** — linear channel at x1125 (my `[est]`) vs a point drain.
6. **Brass wet-room fittings** — approve a sanitaryware/brassware supplier (AELLA has
   none) and confirm satin brass is acceptable for spotting/tarnish under constant water.
7. **Frameless vs slim black-alu-framed shower glass** — a look call, best judged on the
   deferred Gemini beauty pass.
8. **Accessibility** — is a grab-bar / wheelchair provision required? The Thai
   accessibility กฎกระทรวง is **not ingested** — if required this is an owner/architect
   statutory call (see GAP).

## §9 Vault GAPS (honest — do not invent)
1. **STATUTORY, not ingested:** wet-location luminaire **IP rating**, IEC 60364-7-701
   bathroom zones, RCD protection (วสท./EIT code — zero hits in `knowledge/`).
2. Waterproofing **membrane type / coats / coving**, and whether Thai statute even
   mandates a membrane (mr39 ข้อ 9 is silent).
3. **Point vs linear drain** selection/sizing/placement; numeric wet-area floor drop.
4. **Microcement wet-area durability** — no promoted vault file rates it for wet; kept
   DRY-only here. Needs a durability source before it could ever touch the wet zone.
5. Wet-floor **slip DCOF** numeric + a floor-tile SKU/PEI.
6. **Brass bathroom tapware / mixer / shower-valve / towel-rail SKUs** (AELLA is
   door+furniture only).
7. Lighting sub-values: exact task Kelvin, mirror-flank vs bar placement, wet-zone
   illuminance/accent lux, R9/Rf/Rg targets.
8. **Thai accessibility statute** (กฎกระทรวงสิ่งอำนวยความสะดวก) — not ingested; the
   only wheelchair values in the vault are flagged FOREIGN/non-applicable.

## §10 Claude design decisions I own (D-E4-*, owner-vetoable, NOT menus)
- **D-E4-1** the reverse-Albers signature (one warm-oak vanity on a cool ground; garden
  as the wet-side coherence carrier).
- **D-E4-2** full-width frameless mirror, no brass frame.
- **D-E4-3** frameless clear glass enclosure + partition, minimal black-alu hardware.
- **D-E4-4** whole-floor 1:100 + shower-pan 2% + low curb + linear drain at x1125.
- **D-E4-5** exhaust-fan ventilation path (don't rest on undrawn window area).

## §11 Critique fold-in (DD-research critique + build review, 2026-07-18)
The workflow's completeness/coherence critic + the build review raised these; each is
addressed or recorded honestly:
1. **Anti-monopoly quantification (the sharpest risk).** The oak vanity is a **LOW 850 mm
   cabinet body**, never a wall-height block: its oak surface ≈ the ~2.05 m-wide front +
   two ends ≈ **~3 m²** against ~47 m² of cool wall/ceiling/floor/porcelain ground = **~6%**
   — well under the 30% accent ceiling. Held low + on one wall + backed by a cool counter +
   cool wall + mirror above, so the vanity WALL itself reads mostly cool. The signature is a
   controlled accent, not a 5th dominant mass. (Verified on the `ensuite_vanity` render:
   oak-on-cool reads; the room is cool-dominant.)
2. **Grooming light vs suite CCT.** Resolved: vanity task light **3000K with CRI ≥ 90** —
   high CRI (not cooler CCT) is what renders skin faithfully, so 3000K/CRI≥90 both coheres
   with the suite AND serves grooming; the *primary* makeup station is anyway the daylit
   element-2 seated vanity, this is a standing grooming station. Owner option to go **3500K**
   if makeup acuity is prioritized (an NLM design-theory ask; R9/skin target is a vault
   `[GAP]`). Added to open Q.
3. **Whole-floor drainage.** mr39 needs the WHOLE floor to fall 1:100 to a low point, not
   just the wet line. → the room low point is the **linear channel at x1125**; the dry zone
   (WC/vanity) floor also falls 1:100 toward it, plus a **secondary point drain** near the
   WC. (Curb height + numeric drop = `[GAP]`.)
4. **Ventilation ข้อ9 vs ข้อ13.** ข้อ13 wants every room to have ≥10% opening to OUTSIDE air;
   ข้อ9 allows a fan alternative. We satisfy BOTH honestly: the 2 west casements open to the
   garden (outside air) AND we add the exhaust fan (≥46.8 m³/h). Whether the casements'
   operable area alone clears 0.836 m² is undrawn — a code/architect confirmation, added to
   open Q (do not rest compliance on the undrawn area).
5. **Wet-zone E-W fit (constructability).** Ink closes to the drawn faces (shower 1069.7 +
   partition + tub 1999.6 + reveal 28.1 ≈ x55→3152.8), so it fits AS DRAWN — but once wall
   tile buildout + the partition panel are counted there is only ~a stroke of slack. A
   tolerance/constructability call for the owner/engineer (which fixture shaves a few mm if
   finishes eat it). Added to open Q.
6. **SW-corner vanity/WC overlap — FIXED in the build.** The "3.05" counter is a full 3047
   run but the DEEP oak 2-basin cabinet is only the east ~2047 (x1077→3124); the west ~1000
   is a shallow stone ledge over the WC (no cabinet through the toilet). Encoded in
   `bathroom.py` + the spec fixture (`counter_x0_mm`) + a `test_bathroom` non-overlap
   invariant.
7. **Mirror — BUILT (was about to be revert-by-omission #6).** D-E4-2 decided a full-width
   frameless mirror; the first build did NOT emit it. Now built as a `mill__…__mirror` part
   in `bathroom.py` (routes to the suite `mirror_silver`), with a `test_bathroom` invariant
   that it exists above the counter. The decided element can no longer silently drop.
8. **Ceiling/RCP** = a follow-on scope: moisture-resistant board + anti-mold paint (dry),
   a service bulkhead/access panel over the wet zone, the exhaust fan location, and the
   downlight/cove layout — RCP tier, not drawn here.

**Build status (2026-07-18).** `bathroom.py` (pure massing, 12 tests) + `build_room`
per-part material routing (reuses the suite oak/Caesarstone/brass/glass/mirror by name) +
a reusable `eye_camera.in_subroom` camera feature (lets the eye stand inside a subroom — a
subroom was otherwise an opaque mass). Renders (Cycles): `ensuite_vanity` shows the oak-on-
cool + brass signature; `ensuite_wet` shows the glass shower with the **garden through the
west casements** (the coherence carrier) + the deck tub. Full suite: 1730 tests green.
Known render artifact: a thin black band at the frame top (eye-render ceiling-edge, not
element-4-specific). Fixture footprints are OWNER-AUTHORED (two-layer law) — adopted from
the ink per the ink-read reco, presented for the owner's veto on the render.

*Refs: `element4-ensuite_ink-read-2026-07-18.json`; workflow `wf_0fd0028a-160`;
`knowledge/` paths cited inline; the suite palette in `master-suite.CANONICAL.spec.json`
(D1-A, 3000K/2850K, black-alu, Caesarstone).*
