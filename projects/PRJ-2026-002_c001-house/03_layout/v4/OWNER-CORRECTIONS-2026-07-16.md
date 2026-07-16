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
