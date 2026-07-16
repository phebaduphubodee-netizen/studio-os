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

## 0. The two pieces — ⚠️ GEOMETRY CORRECTED 2026-07-16b, THIS DD WAS DESIGNED ON WRONG NUMBERS

> **Read this before trusting any dimension below.** The owner's 2026-07-16b markup sent me back
> to the sheet ink, and the `[est]` numbers this DD was built on were not merely loose — they were
> wrong. Scale first proven against the designer's OWN printed dim (sheet prints "3.05" for the
> ensuite counter; the ink measures **3047.0**, 0.1%). Then 6 independent readers + adversarial
> refuters (94 claims, 50 refuted) re-read the band. What changed:
>
> | | this DD designed against | drawn ink | impact |
> |---|---|---|---|
> | **BF14 length** | 2540 (`y110→2650`) | **3250.2** (`y-450.2→2800.0`) | **+710 mm = +28%** — the signature wall is over a quarter longer than designed |
> | BF14 x (west face) | 5150 | **5203.2** | +53 |
> | **BF09-3 position** | `y2650` | **`y2800.0→3399.9`** | +150 north (rigid pair with BF14's N end) |
> | BF09-3 run | `x2300→5600` = 3300 | **`x2353.0→5654.0` = 3301.0** | closes on the party wall |
> | BF09-3 internal | "3-mass **asymmetric**" (D3-A) | drawn in **3 EQUAL bays**, dividers at x3454.4 / x4552.6 (1101.4 / 1098.2 / 1101.4) | ~~contradicts the signed layout~~ **RETRACTED** — carcass/module lines, not a design instruction (see §0b) |
>
> `3250.2` and `3301.0` reproduce the pieces' OWN printed labels (`BF14.325x10x280CM`,
> `BF09-3.330x60x280CM`) to 0.2 mm and 1 mm — the strongest evidence class this project has.
> The `y110` trim was MY conflation, not the owner's error: y110 carries **zero horizontal strokes
> anywhere on the floor**; the owner's "~y110" is the **curtain slot's** north cap (`y=149.7`,
> x5301.6→5552.4) in the 250.8 mm void east of BF14, where the sheet draws a real **2-layer curtain
> symbol** (serpentine + south-pointing draw arrows at x5406.4/x5473.0). Owner right, me wrong.
> Spec + this table are now ink-true. **Slat arithmetic: RE-RUN and CLOSED — see D2-A-MODULE
> (AKUWALL 27/13, 77 slats, Σ 3250.2 exact).** The "3-bay conflict" was **RETRACTED** — those are
> carcass/module lines, not a design instruction (§0b). **§2–§4 below are the ORIGINAL reasoning trail
> and still quote the dead 2540/40-20 numbers; D2-A-MODULE supersedes them.**

- **BF14 — vertical-slat headboard.** East side, `x5203→5303`, `y-450→2800` (**length 3250 mm**),
  `h2800` full-height, 100 mm thick (drawn 98.4 = a 100 nominal on the sheet's ~3.174 mm grid —
  do NOT "correct" it). Stands IN FRONT of the black-alu glass return (`glz-east`); the bed head
  pins to this SOLID wall. N end meets BF09-3 @ y2800 (**rigid pair**). S end = a drawn cap at
  y-450.2, flush with the south nightstand — it does **not** stop at the curtain track.
- **BF09-3 — open dressing wall.** Runs along `y2800→3400`, `x2353→5654` (**length 3301 mm**),
  **600 mm deep**, `h2800`, `open:true` — oak carcass, brass hang-rails, floating drawers,
  open shelves, **NO doors**. The signature piece. Its north face `y3399.9` is the sliding
  door's south jamb.

### §0b · WHAT THIS SHEET CAN AND CANNOT BE ASKED — the law that produced the errors above

> **Owner, 2026-07-16c: "แบบมันไม่ได้ผิด แต่เครื่องมืออ่านแบบของเราห่วย." He was right.**
>
> **The test.** Every BF piece's drawn extent vs its OWN printed label: BF14 3250.2/3250 (+0.2) ·
> BF13 4100.8/4100 (+0.8) · BF09-3 3301.0/3300 (+1.0) · BF12-2 701.5/700 (+1.5) ·
> BF09-2 1498.1/1500 (−1.9) · BF10 2497.9/2500 (−2.1) · BF12-1 1577.5/1575 (+2.5) ·
> ensuite counter 3047.0 vs printed "3.05" (−3.0).
> **The sheet agrees with itself to ≤2.5 mm (0.16 %). Our spec disagreed with it by up to 2850 mm.**
> ~1000×. Every discrepancy this session resolved to OUR reader — never once to the drawing.
>
> **The resolution limit.** At 1:75 a **0.6pt pen covers 15.87 mm of real space**; the coordinate
> snap is 3.17 mm. So the leaf lane gap (9.5 = **0.60 pen widths**) and the leaf y-lap
> (12.7 = **0.80 pen widths**) are *inside the ink* — I reported them as findings. That precision
> does not exist. A 101.6 mm notch is 1.3 mm on paper; a pocket cage is not on a furniture plan at all.
>
> **WITHDRAWN as "designer errors"** (all mine, not the drawing's): the BF09-1/column "build clash"
> (furniture plans don't draw notches — wrong tier); "the sheet REFUSES to draw a pocket" (it never
> carries one); "3 equal bays contradict the signed layout" (module lines); "BF09-1 is 26.4 short of
> its label" (1.7 pen widths + an unknown corner convention); "nothing explains the wall step"
> (structural wall meeting a partition — only a tool with no concept of buildings calls that a mystery).
> Also: I instructed the adversarial refuters to *"default to refuted unless reproducible from a dump"*,
> which auto-kills every non-stroke claim — the 50/94 refutation rate was **that bias, not rigour**,
> and it is what "refuted" the owner's pocket.
>
> **THE RULE.** This sheet answers **where / how big / what it is called**, to ~2.5 mm — more than
> enough for us. **Notches, pocket cages, head heights and joinery are not in it, and their absence is
> not a gap, a conflict, or anyone's error** — they are ours to DESIGN, or the owner's/designer's to
> answer. Never generate a "designer error" list from a document that was never asked the question.
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

### ⚠️ AUTHORITY NOTE — 2026-07-16c, read before citing any "owner-signed" decision below

The owner stated, unprompted: **"ผมไม่ใช่ interior designer ตัวจริง ไม่มีความรู้เรื่องนี้เลย แต่จบวิศวกรเลย
พอจะอ่านแบบออกอยู่บ้าง."** I had been running on the opposite premise (a workflow prompt this session
literally read *"He is a working interior designer; he signs, we build"*).

**Consequence for this document: D1–D6 are NOT design authority.** They were authored by Claude
(vault + NLM, CONVENTION tier) and countersigned by someone who has now said he cannot evaluate them.
Do not wield them as constraints against new evidence — this session did exactly that ("D5-A already
signed NOT solid oak") and it was a circular argument.

**What the owner IS authority on, and has been right about every single time:** reading the sheet ·
what the client and the partner-designer meant · engineering, tolerance, constructability · money ·
and **"does this look right"** on a RENDER. See memory `owner-is-an-engineer-not-a-designer`.

**Method change:** stop issuing A/B/C menus of taste for signature. Decide, build it, render it, and
put the picture in front of him — the render is the decision instrument, not the decision memo.

#### Owner answers 2026-07-16c (engineering + client + money only)

| # | Question | Answer | Consequence |
|---|---|---|---|
| 1 | Can a 100 mm wall carry the 2-leaf telescopic pocket (69.9 of leaf in 98.3, ~14/skin)? | **"น่าจะไหว"** | Engineering call taken. Pocket proceeds; flag to the fabricator, do not re-open. |
| 2 | Reveal 15 (zero tolerance) or 12 (mid-window, ±3)? | **12 / posts 63** | Reveal **12.0**; terminal posts grow **60.0→63.0 / 60.2→63.2**. Field stays 3100.0 / 52 slats at 40-20. Close: 63.0+12+3100+12+63.2 = 3250.2 ✓ |
| 3 | North corner post solid oak (D2-A's word) or veneer (D5-A's word)? | **"ไม่น่าใช่เสาไม้"** → **VENEER** | The D2-A/D5-A contradiction is resolved on the owner's own materials judgement, not by citing a soft signature. Post = oak veneer over MR core. |
| 4 | Call AKUWALL re a 40/20 run on their acoustic base? Budget ~฿43–48k? | **"ลุยเลย แบบไม่ต้องโทร"** | No supplier call. **Claude decides the module** — see D2-A-MODULE below. |
| 5 | Does the client actually need 2 curtain layers? | **ชั้นเดียว / single layer** | ⭐ **THE POCKET LOCK IS DEAD.** Single S-fold needs ≥150, single 3-pleat ≥100; the slot clears ~220–240. Both make-ups fit with room to spare. Q4's "3-pleat + 3-pleat, no S-fold ever" is WITHDRAWN — S-fold is available. |
| 6 | Acoustic requirement for this room? | **yes** | Bespoke 40/20's signed **matte-black PLY backer is a REFLECTOR** — slats + gaps absorb nothing against solid ply. "Yes" therefore forces either a porous backer we have no data for, or the stock acoustic panel. Drives D2-A-MODULE. |

---

### D2-A · **ISSUED SLAT SCHEDULE** — 2026-07-16c, on the ink-proven 3250.2 × 2800

> **"≈42 slats over 2540" is DEAD.** 2540 was a wrong *input*, not a wrong rhythm — the old
> arithmetic was self-consistent (42×40 + 41×20 = 2500 in 2540). **D2-A's 40/20 survives untouched
> and is delivered pure.** Only the count changes.

> ⛔ **THIS SCHEDULE IS SUPERSEDED — see D2-A-MODULE below.** The owner (a) chose reveal **12**, not 15,
> and (b) then chose the **AKUWALL 27/13 product** over the bespoke 40/20 by LOOKING at an A/B render
> pair. Both the module and the reveal below are dead. The reasoning is kept because the *method* —
> sink the remainder into timber, make the end members whole beats of the field's rhythm — carried
> straight over to the AKUWALL schedule and is the reason it closes.

Setting out from the **SOUTH datum** (y-450.2), running south → north:

| # | Part | Width (y) | From → to |
|---|---|---|---|
| 1 | ~~South mouth-jamb~~ | ~~60.0~~ | ~~y-450.2 → y-390.2~~ |
| 2 | ~~Shadow reveal (15.0)~~ | ~~15.0~~ | ~~owner chose 12~~ |
| 3 | ~~FIELD — 52 slats · 40/20 · pitch 60 · depth 22~~ | ~~3100.0~~ | ~~owner chose AKUWALL 27/13~~ |
| 4 | ~~Shadow reveal (15.0)~~ | ~~15.0~~ | |
| 5 | ~~North corner post~~ | ~~60.2~~ | |

~~Σ = 60.0 + 15.0 + 3100.0 + 15.0 + 60.2 = 3250.2~~ — arithmetically correct, **but on inputs the owner
has since replaced.**

**How the remainder is absorbed — into TIMBER, not into air.** Pure 40/20 cannot close: n=54 → 3220.0
(rem +30.2); n=55 overshoots 29.8; the wall lands almost exactly half a module out
((3250.2+20)/60 = 54.5033). So the two end members are made **exactly one pitch each** (60.0 / 60.2)
and the terminus reads as a member of the rhythm rather than as leftover.
*Rejected, for the record:* tuning the face to 40.56 (silently un-signs D2-A's 40 and poisons every
future studio slat wall) · tuning the gap to 20.19–20.57 (free to machine, but 51–53 spacer-stacks
compound ±0.5 into ~26 mm of creep that lands **at the curtain mouth**) · two 15.1 end reveals with no
posts (a "reveal" at a free end is just the wall stopping short — and 15.1 misses D2-A's signed 10–15
window by 0.1).

**Datum south, scribe north.** The south is the functional end — the curtain must clear the mouth
dead-on beside a hairline black-alu frame in daylight. The **+0.2 asymmetry and all accumulated build
error die in the north scribe** against BF09-3, an already-built face.

**Solid %** — D2-A's "~66%" delivered, not drifted: repeat ratio 40/60 = **66.67 %** (this is what
D2-A names) · field 2080/3100 = 67.10 % · whole wall, oak members only = 65.85 %.
**Cut length** = 2800 − 15 (floor) − 15 (ceiling) = **2770**.

⚠️ **BUILD-LAYER GAP:** `millwork.py` currently does `n = int(run // pitch)` then `pitch = run/n` over
the WHOLE run → it renders **54 slats @ gap 20.19, end margins 10.09**. That is a *defensible* auto-fit
but it is **not this schedule** (52 + two terminal members). The current render
`room_bedroom_suite_eye_doorfix2.png` shows 54. The terminal members must become real parts before the
render matches the issue.

---

### D2-A-MODULE · ⭐ **AKUWALL 27/13 — DECIDED 2026-07-16c, BY LOOKING**

The owner was shown two renders on the same camera, same light, same materials — **A** bespoke 40/20
(54 slats, depth 22) vs **B** the stock AKUWALL 27/13 (81 slats, depth 12) — and answered
**"ผมชอบ akuwall"**. That is the whole decision, and it is the right *kind* of decision: he cannot read
a slat rhythm off a table, he can read it off a picture. **The render is the decision instrument.**

**What won and why it was mine to put in front of him.** His answer (6) = *yes, acoustics*. The bespoke
40/20's signed **matte-black PLY backer is a REFLECTOR** — slats and gaps absorb nothing against solid
ply — so "yes" forced a choice between inventing a felt spec the vault has **zero** data for, or a
product with real numbers. AKUWALL carries: **NRC 0.8** · fire **EN13501 Class B / ASTM E84 Class A**
(the only fire data anywhere in `knowledge/` for a 9 m² full-height combustible wall in a bedroom) ·
**black backing** (D2-A's backer, as a product) · imported natural-oak veneer over its own engineered
build (D5-A's intent, as a product) · **21 mm total** (thinner than our 22 + backer) · **~฿43–48k** ·
~15-day lead — which serves the sourceability north-star.
Source: `knowledge/materials/wall-cladding-and-decorative-mouldings-th.md:65-77` (VERIFIED by coverage
math). **Price caveat: catalogue 2023, VAT unstated, the vault flags its pricing stale — not a quote.**

**What it cost, stated honestly:** 27/13 is the ubiquitous acoustic-panel look; 40/20 was more
distinctive. And at depth 12 vs 22 the reveals are shallower, so the field reads as *texture* rather
than as *battens*. The owner saw exactly that in the render and picked it anyway.
**Solid % survives: 67.5 % vs 40/20's 66.7 %** — the *weight* D2-A actually argued for is intact; only
the grain is finer. And the rhythm it replaced was a Claude+NLM CONVENTION-tier proposal countersigned
under a premise the owner has since denied — **it had no authority to defend.**

#### ISSUED SCHEDULE — AKUWALL, on the ink-proven 3250.2 × 2800

| # | Part | Width (y) | From → to |
|---|---|---|---|
| 1 | **South mouth-jamb** (D7 — the curtain mouth's west shoulder) | **79.6** | y-450.2 → y-370.6 |
| 2 | Shadow reveal | **12.0** | y-370.6 → y-358.6 |
| 3 | **FIELD — 77 slats · face 27 · gap 13 · pitch 40 · depth 12** | **3067.0** | y-358.6 → y2708.4 |
| 4 | Shadow reveal | **12.0** | y2708.4 → y2720.4 |
| 5 | **North terminus**, SCRIBED to BF09-3 | **79.6** | y2720.4 → y2800.0 |

**Σ = 79.6 + 12.0 + 3067.0 + 12.0 + 79.6 = 3250.2 EXACT.** Field = 77×27 + 76×13 = 3067.0 exact.
**No part-slat, no cut module.** Each end member is **79.6 = 1.99 × the 40 pitch** → the terminus reads
as *two beats of the field's own rhythm*, not as leftover. Cut length **2776** (2800 − 12 − 12); panel
height 2900 covers it ✓. Solid: repeat **67.5 %**, field 67.8 %.

**Reveal 12 is the OWNER'S engineering call** ("12 / เสา 63"): 15 sat at the very top of the 10–15
window with zero site tolerance, so a wavy plastered ceiling pushes it out of window; 12 is mid-window
with ±3. He answered the *post* number against the 40/20 field; the module change recomputes it to 79.6.
**His decision was the reveal — the post is its consequence.**

**Dead schedules, for the record:** 42 @2540 (wrong input) → 54 @40/20 (millwork.py auto-fit) →
52 @40/20 + 15 reveals → 52 @40/20 + 12 reveals + 63 posts → **77 @27/13 + 12 reveals + 79.6 posts**.

⚠️ **BUILD-LAYER GAP (unchanged, now sharper).** `millwork.py` auto-fits `n = int(run // (face+gap))`
then `pitch = run/n` over the WHOLE run → at 27/13 it renders **81 slats @ pitch 40.12, 10.06 end
margins**. **The render the owner chose from is that 81-slat auto-fit, not this 77 + 2 × 79.6 issue.**
The terminal members must become real parts before any render matches the schedule. Nobody has been
misled — the *module* is what he judged, and the module is right — but do not claim the render shows
the issued wall.

---

### D7 · **BF14's SOUTH TERMINATION** — the free end at y-450.2 · ⏳ open (see the note below)

> **⚠️ THIS MENU'S PREMISE IS HALF DEAD — 2026-07-16c.** It was written for "a working interior designer
> who signs" (false — see the AUTHORITY NOTE) and it was built on a pocket clearance crisis that the
> owner's answer (5) **dissolved**: the client needs only a **SINGLE curtain layer**. Single 3-pleat
> needs ≥100, single S-fold ≥150, and the slot clears ~220–240 — **both fit with room to spare**. The
> "3-pleat + 3-pleat, no S-fold ever, no cove light" lock is **WITHDRAWN**; S-fold is back on the table
> and probably suits an oak-and-glass room better. **The clearance argument that made B's "adds 0.0 to
> the pocket" decisive is therefore much weaker than written below.** Do not sign this as-is; it is
> kept as the reasoning trail. Next pass: re-decide it as a design (mine), and put it in front of the
> owner as a RENDER, not as an A/B/C menu.

**The framing.** The north end is oak into oak — a **joint**, correct there because BF09-3 receives it.
The south end has nothing to receive it: 248 of air, then black alu, then garden. It does not need to be
*received*; it needs to be **released**. And it is one member with two jobs: BF14's terminus **and the
west jamb of the curtain stack pocket**. *(As written, the pocket governed:* raw slot 250.8, clear inside
~220–240 after finishes, 2-layer 3-pleat needing ≥200 per
`knowledge/ergonomics/casework-fixture-clearances-th-practice.md:186-195` — REFERENCE tier, one
practitioner's notes, not a standard — leaving only ~20–40 spare. **Answer (5) removed that squeeze.**)

- **A. Solid oak post 60.0 — mirror the north.** The symmetric answer everyone expects. *Against:* the
  vault rates ไม้จริง **Poor — severe dimensional movement under humidity/temperature swings**
  (`knowledge/materials/residential-materials.md:43-44`), and **D5-A already signed "NOT solid oak"**.
  This is the room's sunniest, wettest, most thermally cycled point. It also stands 0.27 m² of warm oak
  in the room's only cool aperture, bouncing warm GI into the 60 % plaster ground exactly where D1-A
  must prove itself. *Not recommended — but it is the honest fallback; arithmetic identical.*
- **B. ★ MINERAL RELEASE — a 60.0 × 98.4 × 2770 cool-microcement jamb, shop-finished, zero proud.**
  ★ **RECOMMENDED.** The oak field dies at a 12.0 shadow reveal (owner 2026-07-16c; written as 15.0) into a mineral shaft that reads from
  the garden as a **98.4-wide pale vertical stroke** — the last thing between the wood and the glass —
  and is simultaneously the smooth hard cheek the curtain slides past. **No oak in it. It adds 0.0 to
  the pocket.** Serves D1-A (the cool ground releases the oak) and D6-A (mineral contrast) at once.
- **C. Black-anodised aluminium jamb — join the window-frame family.** Clever: the terminus takes the
  material of what it *meets* rather than what it *ends*, and as a metal it cannot be a 0,0,0 black hole.
  *Fatal:* the jamb would be folded sheet (5005/5052) while the frames are extruded 6063 — **black
  anodic film does not match across alloy families and no anodiser warrants it**. A near-miss black
  standing 292 from the frames it was built to join = a *third* black, i.e. **D1-C, which the DD marks
  not-recommended and the owner did not sign**, smuggled in through a detail. *Not recommended.*

**★ B as issued (runners-up grafted in):**
1. **The element.** 60.0 (y) × 98.4 (x = BF14's full thickness) × 2770 (z); x5203.2→5301.6,
   y-450.2→-390.2. Its south face **IS** the mouth plane y-450.2 — **0.0 projection south**, flush with
   the south nightstand's own south line. Its east face is **FLUSH at x5301.6, zero proud** — the 2–3 mm
   mineral build is taken **out of the carcass, never added to the face**. Hardest rule in the detail.
2. **The east face is the pocket's cheek, and it keeps going.** The same mineral continues north as the
   slot's entire west lining, flush at x5301.6, y-450.2→149.7 (599.9), full height. One hard smooth cheek
   from the parked stack right out of the mouth: **52 open 20 mm gaps at a curtain mouth is a fabric
   hazard**, and this is also the answer to the black hole (`interior-render-critique-DR-2026-07-15.md:38`
   — a 0,0,0 recess = GI misconfigured; **this is the same cavity class as the "รู" the designer circled
   on our own render**).
3. **"Seamless" is killed — the graft that makes B buildable.** You cannot hand-trowel and burnish a
   jointless 3-coat mineral system inside a 250.8 × 599.9 × 2800 blind letterbox — a float will not turn
   in a 250 slot. **Every mineral surface is a SHOP-PRE-FINISHED PANEL, face-up on trestles, installed
   with BF14.** A **deliberate 12 reveal is declared at the jamb/lining junction** (owner's number; written as 15) instead of pretending
   to a joint that will not happen. **Nothing wet happens inside the slot** — put that in bold on the
   drawing, or site will try it, the throat will ship as raw ply, and we will have rebuilt our own scored
   defect in the brightest corner of the room.
4. **Arrises.** Solid hardwood lipping at each external arris, **R6–R10**, mesh carried round, mineral
   over — *not* R3 (a 2–3 mm build cannot form a 3 mm radius; it thins to zero at the tangents and the
   substrate telegraphs). The 52 slats get a hard **1.5–2.0 chamfer**: 52 crisp lines against one soft
   one; matte mineral absorbing against satin timber taking a directional sheen.
5. **One reveal number — 12, all round** (owner 2026-07-16c; this item was written as 15). Floor, ceiling, both ends, running continuously up the field's
   south edge, around the jamb's base, up its west face, across its south cap, down its east face. BF14
   becomes one 2770 shaft floating on a single dark line. **Formed as a rebate in the millwork, never
   bought** — no shadow-gap/Z-reveal/L-bead SKU exists in our Thai catalogue of record. Reveal interiors
   get the dark backer, **not** trowelled mineral (a 15 × 22 slot will not take a burnished coat).
6. **The backer gets a number: #2A2C2E–#3A3C3E** (42–58 sRGB, slightly cool, B>G>R, roughness 0.75–0.85)
   — clears both live bands (>30 sRGB per `pbr-material-behavior.md:55`, and >0.04 linear per
   build_room's `albedo_plausible`), so "matte black" ships **without a thresholds PR**. It reads black
   against oak; the darkening is done by GI/AO, which is the point.
7. **Curtain lock, issued as DATA not prose: 3-pinch-pleat + 3-pinch-pleat ONLY. No S-fold in this
   pocket. No cove light** (+50–100 — the budget is already spent). Clear inside ~220–240 passes ≥200 with
   ~20–40 spare; S-fold + 3-pleat needs ≥250 = **FAIL**; both S-fold = **FAIL outright**. Must live in the
   spec JSON *and* on the mouth elevation — the blade is built months before any soft-furnishing supplier
   measures the most S-fold-inviting opening in the house.
8. **Track centres are NOT pinned from the arrows.** x5406.4 / x5473.0 are **draw-direction arrows, not
   track centrelines**; their 66.6 separation cannot carry two 85-deep bundles. Centre the pair on the
   **as-built** slot after surveying the east cheek → ~28 residual both sides, costs nothing.
9. **Brass is refused here.** D1-A's 10 % stays at BF09-3's rails and the mushroom lamp — the room's dim
   half, where an accent can be an accent. A specular pier at the room's highest-luminance point would
   out-read the south glazing and trip **PH-02** (`knowledge/classifications/render-defects.md:51`).

**⛔ ONE CLAIM FROM THE PANEL REJECTED (2026-07-16c).** A proposal argued *"this end is NOT raked, it is
BACKLIT — the south wall is solid from x3901.9 to x5301.6, so a west-facing plane needs an east-facing
aperture"*, and made a grazing accent a *required* element-6 item. **Rejected on three grounds:**
(1) it **re-litigates owner correction #3**, signed 2026-07-16 and eye-verified on the render
(south glazed full width x0–5500, floor-to-ceiling) — the tier law forbids going back to the ink for
what the owner has settled; (2) its ink read is **wrong on its own terms** — the 0.48 band it called
solid has 0.24pt **window-symbol modules inside it** (x4638.3→5225.5, triple line y-793.0/-773.9/-758.1),
which v4 itself declared as w1/w2; (3) the ray geometry is **simply wrong** — afternoon sun from the
**south-WEST** enters south glazing and rakes a west-facing plane; no east aperture is needed. The
grazing-accent question stays OPEN as a design option, not a forced consequence.

---

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
