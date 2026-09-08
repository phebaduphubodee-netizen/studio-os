# Master suite — owner ground-truth corrections (2026-07-16)

> **STATUS: DRAFT / STREAMING** — owner is enumerating what is still wrong in the
> master suite. Recorded live so it survives a context reset. Base model being
> corrected = `v4/scene-graph.master_bedroom.json` (owner-authoritative takeoff).
> Owner supplied 3 images in-session (client's own house photo + plan crop + a
> style reference). Privacy: refer to pieces by BF code / geometry only; this
> file stays in the project dir, never `knowledge/`, never an external call.
> Cross-check against `../floor2-owner-decision-queue.md`.
> `[?]` = still needs an owner number before I hand-edit the canonical spec.

Method (owner-agreed this session): **owner gives ground truth → Claude hand-edits
ONE canonical spec → then design.** No new automated reader.

| # | Owner correction | v4 current state | Corrected state | Type |
|---|---|---|---|---|
| 1 | The linear element I called an **AC duct** is a **curtain track (รางผ้าม่าน)** | read as a duct / dismissed as riser linework | curtain track = there IS glazing under it; model a recessed pelmet + track, not a duct | opening evidence |
| 2 | Bedroom↔sitting-room door is a **sliding pocket door that hides behind BF09-1** | `id2` read as a swing door (894×948), dismissed | 2-panel(?) pocket slider; pocket void behind BF09-1; NOT a swing, NOT a wall gap | opening |
| 3 | **South corner of the bed = big floor-to-ceiling L-shaped corner glass** (like the attached photo) | master south = niche at y-450; "no terrace, grass below the glass" (07-06); L not modelled | L corner window wrapping the SE corner, sill 0 → head 2800; garden at grade outside | opening / glazing |
| 4 | **BF09-3 = OPEN wardrobe, no doors** (like the reference photo) | `wardrobe` 3300×600×2800, closed implied | open dressing joinery: oak veneer carcass, brass hang rails, floating drawers, open shelves | identity + design |
| 5 | **Blender 3D walls don't seal/close cleanly** | build leaves gaps at corners | build-layer fix: watertight corners (esp. the L-jog x5500→5650 @ y2650) + opening face-loops | 3D build bug |
| 6 | Foot-of-bed **"TV console" is NOT for a TV** (client barely watches) → **display/book shelving** | `tv_console` (west wall, x306, 600×2046, h1800) | re-type → open bookcase/display; bed foot faces a shelf wall, not a screen | identity + design |
| 7 | **BF11 = makeup/dressing table (โต๊ะเครื่องแป้ง)**, not a work desk | `cabinet` "โต๊ะทำงาน built-in" (west wall, x0,y2650, 600×3200, h750) | dressing vanity: mirror + drawers; the "desk chair" = vanity stool | identity + design |

## Reference images (owner-supplied, in-session)
- **Photo #1** — the real L-shaped floor-to-ceiling corner glazing (black alu frame,
  garden/grass below, adjacent walnut door). = the look + reality of correction #3.
- **Photo #3** — style reference for #4: light-oak open wardrobe, brass hang rails,
  floating drawers, open shelving, floating oak nightstand + mushroom lamp, and a
  **slatted oak headboard (= BF14)** at frame right. Seeds the headboard/dressing wall design.

## Owner answers — RESOLVED (2026-07-16, 2nd plan crop)
- **L-glass (#3):** SOUTH wall glazed **full width x0 → 5500**, floor-to-ceiling 0–2800,
  wrapping the **SE** corner and returning up the EAST wall (x5500) from y-450 up to
  **~y110 (south edge of bed)**. Garden at grade outside (no floor-2 terrace). "ตามรูป."
- **BF14 vs glass (#3/#4):** BF14 (east slat headboard) NORTH end meets **BF09-3 exactly**
  (y2650); SOUTH end meets the **curtain track exactly** (~y110). BF14 stands IN FRONT of the
  east glass return; the bed head is against **solid BF14**, not glass.
- **Sliding door (#2):** **2 panels**, slide in sequence, both pocket behind **BF09-1 EAST
  leg** (x5050, y4674–8050) — connects dressing/wardrobe bay ↔ sitting room.
- **Curtain track (#1):** continuous ceiling pelmet — NW corner → south down the WEST wall →
  east along the SOUTH wall → up the EAST wall **behind BF14**, ending ~south-of-bed y. It
  runs onto the solid west + east returns so curtains **PARK off the glass** →
  **a 3-sided track does NOT mean 3-sided glass** (this reconciled the apparent conflict with
  the west-wall bookshelf / BF11 vanity).
- **Wall-seal bug (#5):** owner — open corners are visible in the **plan itself** (SW, SE,
  the L-jog), walls drawn not meeting. FIX = close the canonical outline watertight + clean
  subroom joins, then re-verify in Blender. (Build-layer task, sequenced AFTER the geometry spec.)

## CONFIRMED (owner traced the track on a 3rd crop, "ตามรูป")
- **Curtain track path = LOCKED:** the owner drew the red line — NW corner → down the FULL
  west wall → east across the FULL south wall → up the east wall behind BF14, ending
  ~south-of-bed. This is the TRACK (ceiling pelmet), not the glass line.
- **Glass (final):** SOUTH wall full x0 → 5500 + EAST return x5500 (y-450 → ~y110). The track
  is longer than the glass on purpose (wraps onto the solid west + east walls so the wide
  south curtain stacks/parks off the glass). Red line ≠ glass extent.
- **West wall (bookshelf x306 / BF11 vanity) + east wall (BF14) = SOLID** — the track only
  passes over them for curtain parking. (Stated; owner did not dispute.)

## DONE — owner said "ลุย" (list complete, no #8/#9)
Folded all 7 into ONE canonical spec: **`../master-suite.CANONICAL.spec.json`**
(schema `@0.2+ext`; supersedes v4 master_bedroom + the 3 stale example copies for rendering).

**Fields I had to ESTIMATE `[est]` — owner please eyeball:**
- Sliding pocket door: opening **width 1600 (2×800)** and **y≈6250** in the east wall — owner
  confirmed panels(2)+pocket(behind BF09-1 E leg) but NOT the numbers.
- BF14 south end trimmed from y-275 → **y110** to meet the track "~south-of-bed" (owner phrase "แถว ๆ").

---

## ⭐ THE `[est]` NUDGE — RESOLVED 2026-07-16b (owner: "ดูตามรูปที่แนบ")

Owner sent the plan crop with the pocket **shaded red + a north arrow**: "บานเลื่อนเข้าไปเก็บใน
ช่องที่ระบายสีแดง". That sent me to the sheet ink. **Both `[est]` numbers were WRONG — not loose.**

**Method + calibration.** Transform = the repo's committed one (26.45 mm/pt, origin 171.2/596.5,
page 1). Proven against the designer's OWN printed dimension: the sheet prints **"3.05"** for the
ensuite counter and the ink measures **3047.0** (0.1%). Then 6 independent readers, every claim
adversarially refuted (**94 claims, 50 refuted, 44 survived**). Tooling: `ink.py` (scratchpad).

| | `[est]` I recorded | drawn ink | delta |
|---|---|---|---|
| Door opening | w1600 @ y6250–7850 | **y3399.9→4621.9, w1222** in x5654.0–5752.3 | **2850 south, 378 narrower** |
| BF14 | x5150, y110→2650, d2540 | **x5203.2–5301.6, y-450.2→2800.0, d3250.2** | **+710 (+28%)** |
| BF09-3 | y2650 | **y2800.0→3399.9** | +150 (rigid pair) |

- **The door was punched through a SOLID WALL.** y6250–7850 dumps as `x5654.0/x5752.3
  y6297.7→8097.4 w=0.84` + 0.12 skins + 44 hatch diagonals = hatched masonry. There is no opening there.
- **The real opening is the gap between the two wardrobes**: BF09-3's north face (y3399.9) and
  BF09-1 E leg's south end (y4621.9), closed by full-thickness jamb caps at both ends.
- **Two leaves are drawn CLOSED**, each 612.6 long, in two lanes inside the wall (leaf-S
  x5698.4–5727.0 y3399.9–4012.5; leaf-N x5657.1–5688.9 y3999.8–4612.4; lane gap 9.5, lap 12.7).
  This **retracts the 2026-07-11 re-read** ("s2 = ช่องเปิดเปล่า ไม่มีบาน; the leaf ink is really
  cabinet frames"): the cabinets BF12-1/BF12-2 are at x5752.3–6152.3, a different x band entirely.
- **THE POCKET.** Owner-declared (the red markup) and recorded at top-level `door_sitting_pocket`.
  ⚠️ My first write-up said "the sheet REFUSES to draw a pocket" and that "the adversarial pass refuted
  it and was right" — **BOTH RETRACTED, see §RETRACTION below**. A 1:75 furniture plan never carries a
  pocket cage; the refutation was a harness bias I built. The pocket is also **corroborated by
  arithmetic**: a single leaf would need a 1222.0 pocket and only 1076.0 exists (short 146.0), so TWO
  leaves are FORCED; opening north gives leaf-N 622.1 / leaf-S 1222.0 travel = **ratio 1.964 ≈ 2.000**,
  the telescopic fast:slow signature; the stacked pair needs 612.6 of 1076.0. The owner's slot is also
  the only viable run — the south run (599.9) is 12.7 SHORTER than one leaf.
- **"~y110" — OWNER RIGHT, CLAUDE WRONG.** y110 carries **zero horizontal strokes floor-wide**
  (`ink.py -500 11000 105 120 0`). The owner was reading the **curtain**, not BF14: east of BF14 is a
  **250.8 mm void** (x5301.6–5552.4) capped at `y=149.7` (x5301.6→5552.4, len 250.7), holding a real
  **2-layer curtain symbol** — serpentine fabric + **south-pointing draw arrows** at x5406.4/x5473.0,
  y-377.2..~90. y110 sits between the symbol's top (~y89) and the cap (y149.7). I applied the track's
  end to a different object 560 mm further south and cut 710 mm off the signature wall.

**Done:** spec ink-trued (BF14, BF09-3 rigid pair, door rect), rebuilt + rendered + LOOKED
(`pipeline/output/room_bedroom_suite_doorfix_dh.png` dollhouse, `..._eye_doorfix2.png` hero —
BF14 now visibly runs past the bed foot; hero camera re-nudged because the subject moved).

**KNOWN RESIDUAL — deliberately NOT fixed** (see spec `corrections_applied` #9): the party wall is
**band-scoped** (199.9 thick, west face x5552.4 across the sleeping band, with 200×200 columns
embedded; 98.3, west face x5654.0 north of ~y2800 — a structural wall line meeting a lighter
partition, which is ordinary); the outline still reads x0..5500 / jog y2650 vs ink x55.0..5552.4 /
jog y2800 (the *width* is right — 5497.4 = the designer's printed "5500" — so it is a ~52 translation).
Per-piece offsets are NOT constant (BF14 was 53.2, BF10 ~154, BF11 ~306).
**RULE ADOPTED: the element under design gets its geometry ink-trued; the rest waits its turn** —
otherwise this becomes another takeoff re-measure instead of a design.

---

## ⛔ RETRACTION 2026-07-16c — "แบบมันไม่ได้ผิด แต่เครื่องมืออ่านแบบของเราห่วย" (owner). He was right.

**THE TEST.** Each BF piece's drawn extent vs its OWN printed label:

| piece | printed | drawn | Δ |
|---|---|---|---|
| BF14 | 3250 | 3250.2 | **+0.2** |
| BF13 | 4100 | 4100.8 | +0.8 |
| BF09-3 | 3300 | 3301.0 | +1.0 |
| BF12-2 | 700 | 701.5 | +1.5 |
| BF09-2 | 1500 | 1498.1 | −1.9 |
| BF10 | 2500 | 2497.9 | −2.1 |
| BF12-1 | 1575 | 1577.5 | +2.5 |
| ensuite counter | "3.05" | 3047.0 | −3.0 |

**The sheet agrees with itself to ≤2.5 mm (0.16 %). Our spec disagreed with the sheet by up to
2850 mm — ~1000×.** Every discrepancy this session resolved to OUR reader; not once to the drawing.

**THE RESOLUTION LIMIT I IGNORED.** At 1:75 a **0.6pt pen covers 15.87 mm of real space** (snap grid
3.17 mm). I reported the leaf lane gap (**9.5 = 0.60 pen widths**) and the leaf y-lap
(**12.7 = 0.80 pen widths**) as findings. They are *inside the ink*. I invented precision.

**WITHDRAWN — every "designer error" I raised was mine:**
1. *"BF09-1's east leg runs through the y5697.9 column with no notch = a real build clash."* A 1:75
   FURNITURE plan does not draw notches (101.6 mm = 1.3 mm on paper). Joinery drawings do. Wrong tier.
2. *"The sheet REFUSES to draw a pocket."* It never carries a pocket cage. Not a refusal — not that
   kind of document.
3. *"BF09-3's 3 equal bays contradict the signed asymmetric layout."* Carcass/module lines. I turned
   a fabrication split into a design instruction.
4. *"BF09-1 is 26.4 short of its 5200 label."* 1.7 pen widths, and dependent on a corner-counting
   convention the reader does not know.
5. *"Nothing on the sheet explains why the wall steps 199.9→98.3."* Structural wall meeting a
   partition. Only a tool with no concept of buildings calls that a mystery.

**ROOT CAUSE — and it is in the harness, not the sheet.** The reader has no notion of DRAWING TIER or
PEN RESOLUTION: it treats every stroke as a dimension and every absence as a contradiction. Worse, I
instructed the adversarial refuters to *"default to refuted unless you can reproduce it from a dump"* —
which **auto-kills every claim that is not a stroke**. The 50/94 refutation rate I presented as rigour
was that bias, and it is what "refuted" the owner's pocket. Same disease again minutes later: the
label-check tool reported BF09-3 as "not found" because it hunted for one long stroke while the
designer had drawn it, normally, as three bays.

**THE RULE (also in memory `drawing-tier-law`).** This sheet answers **where / how big / what it is
called**, to ~2.5 mm — more than enough for us. **Notches, pocket cages, head heights and joinery are
not in it, and their absence is not a gap, a conflict, or anyone's error** — they are ours to DESIGN,
or the owner's/designer's to answer. Never generate a "designer error" list from a document that was
never asked the question. The fix is NOT a better reader — that is the referee-factory trap the
direction reset exists to stop.

**Still pending (build layer, correction #5):** the L-glass + doors already render via native
`room.openings` (verified — see below); STILL TODO = build_room to render BF09-3 as OPEN
(`open:true` unconsumed) + the `curtain_track`, and confirm the L-jog corner seals on the
full-floor build.

## VERIFIED BY EYE (2026-07-16, Blender 5.1 headless GPU)
Built + rendered the canonical spec. Owner-lesson "LOOK, don't trust numbers" honoured.
- `pipeline/output/room_bedroom_suite_canon16.png` (dollhouse overview) — L-suite builds coherently.
- `pipeline/output/room_bedroom_suite_eye_canon16eye.png` (eye) — **glass-L reads floor-to-ceiling
  to greenery = owner photo#1**, **walls SEAL at the visible corner** (no light-leak), slat
  headboard BF14 + bed present. Build log: room 3 openings cut (2 glass panes) + ensuite door.
- The eye shot shows **BF09-3 as a flat brown UNDESIGNED slab** = the exact target for element 1.
- **The 'ถอดแบบไม่ตรง' loop is CLOSED for this room.** Files NOT git-committed (owner didn't ask).

## ⭐ NEXT SESSION — element 1 design (do NOT re-do takeoff, it's closed)
Fire the **NLM DR** myself (notebook a5a43395): detailing a warm-oak OPEN dressing wall + vertical
slat headboard + brass hang-rails + floating drawers beside floor-to-ceiling corner glass,
tropical-humidity veneer rules → **choices + reasons** (highlight → client choice) → owner decision
→ into `../master-suite.CANONICAL.spec.json` geometry → store to `knowledge/`. Mood = owner image#3.
First: apply the two `[est]` nudges once owner gives the numbers. Full plan lives in the memory
anchor `project-direction-reset.md` (State + NEXT).

## Downstream design consequences (my read, not owner-stated)
- #3 + #6 don't conflict: glass is SOUTH, the shelf wall the bed foot faces is WEST.
- The bed head is EAST against BF14 (slat headboard). If the L-glass wraps the SE corner,
  BF14's south end and the glass must be reconciled (Q3-b).
- #4 + #6 + #7 + BF14 together = the two signature walls (headboard/dressing wall E,
  vanity+bookshelf wall W). These become the first detailed-design elements (Photo #3 = the mood).
