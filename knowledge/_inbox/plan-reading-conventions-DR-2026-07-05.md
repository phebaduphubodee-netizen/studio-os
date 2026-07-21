---
title: Reading furniture/interior floor-plan symbols (how to interpret a 1:75 Thai furniture plan)
tier: REFERENCE
source: deep-research web DR (2026-07-05), 20 sources fetched, 25 claims 3-vote adversarially verified (22 confirmed / 3 refuted)
primary_refs:
  - Francis D.K. Ching, "Architectural Graphics" 6th ed. — line weight, dashed lines, door swing, scale (NOT furniture facing)
  - Francis D.K. Ching, "Interior Design Illustrated" — the correct ref for furniture plan symbols/facing
  - NKBA "Universal Drawing Standards" ch.3 — line-type hierarchy, dimensioning, overhead vs hidden dash lengths
  - Thai practice: dsignsomething.com, miraidesignstudio.com (door/window symbols), iwadesignthailand.com
status: PROMOTED 2026-07-06 -> knowledge/classifications/plan-reading-conventions.md (distilled into the classifications house style; this raw DR is retained as the audit trail per the _inbox convention). Filled the vault gap knowledge-manager confirmed: no furniture-plan symbol / orientation / BF-code guide existed.
provenance_note: raw DR output at (session task) w1q6hmuzj; furniture/fixture symbol claims are blog-tier (RoomSketcher/Cedreo/PlanSnapper) multi-source unanimous; line/door/dash/scale claims have PRIMARY backing (Ching, NKBA). Imperial dash dimensions transfer as conventions; defer to the sheet's own legend/line-type key.
---

# How to READ a furniture plan (stop guessing — apply two independent systems)

Two reading systems, used together. **FACING** comes from each piece's own symbol geometry.
**STRUCTURE / completeness** comes from line weight + line pattern.

## A. FACING — read the piece's own geometry, NEVER the sheet orientation
- **Bed** — the HEAD is the short end that carries the extra thinner rectangle (the **headboard
  strip**) and/or the pillows; the pillows always sit at the head. FACING/orientation = that end.
  (Size is read from scaled **width** — king is wider than queen/twin, all ~2.0 m long — NOT
  from pillow count, which is only a soft cue.)
- **Sofa / loveseat / armchair** — a rectangle with a thinner **backrest strip** along ONE long
  edge (armrest shapes at the ends). The occupant faces **AWAY** from the backrest strip → the
  OPEN side is the direction the seat faces. Reliable cue = *presence* of the backrest strip on
  one side (not that it's "thinner").
- **Door** — a gap in the wall + a straight leaf line perpendicular to the wall + a quarter-circle
  **swing arc**; the arc gives swing direction, hinge side, clearance; leaf width = opening width.
  This is the most airtight facing cue on the whole sheet.

## B. STRUCTURE / completeness — read line WEIGHT and line PATTERN
- **Line weight (what is CUT vs beyond):** heaviest CONTINUOUS line = elements the plan cut
  passes through (**walls, columns**). Intermediate weight = horizontal surfaces below the cut
  but above the floor (**furniture, fixtures**), lighter the farther below. Thinnest = dimension
  lines, leaders, door swings, break lines. → **A faint element is furniture/annotation, NOT a
  wall.** (Line weight degrades in bad PDF/scans — don't rely on it alone.)
- **Dashed lines — long vs short mean OPPOSITE things (top cause of "missing furniture"):**
  - **LONG dashes** (¼–⅜in) = **OVERHEAD**, above the cut plane at the ceiling: upper cabinets,
    soffits, beams, skylights, roof overhang.
  - **SHORT dashes** (⅛in) = **HIDDEN below** a visible surface: base cabinets under a counter,
    a pony/half wall under a countertop.
  - **dash-DOT** = centerline / alignment reference, not an object.
  → resolve above-vs-below by dash LENGTH + the sheet legend. Don't conflate.
- **Scale:** 1:75 metric sits between 1/8in=1ft and 1/4in=1ft. Read every size off the scale.

## C. Thai-sheet specifics (medium confidence — one Thai blog + 3 corroborators)
- Swing/pivot door (บานเปิด): opening arc + pivot จุดหมุน, **often drawn DASHED** — so on a Thai
  sheet a **dashed arc at a door = the swing path, not a hidden element.**
- Sliding (บานเลื่อน): panels move along the **arrow** direction. Fixed panel: marked **"FIX"**
  (or unmarked). Louver (บานเกล็ด): tilt points toward where the slats angle down.
- Bathroom fixtures (blog-tier, representative not exclusive): **bathtub** = rectangle/oval;
  **shower** = square with a **triangle** at the showerhead (a wet-zone orientation cue);
  **WC/toilet** = oval with a flat top, or oval + tank rectangle; **basin/vanity** = the basin
  ovals — count them for single vs double.

## D. ⚠️ THREE assumptions I (Claude) had WRONG — refuted by verification
1. **"North arrow = north is up" → FALSE.** Do NOT infer facing from sheet orientation. Read the
   actual north arrow; read furniture facing from the symbol geometry (§A).
2. **"Built-in vs loose furniture = lighter line/other colour" → FALSE.** The fixed/loose split
   is NOT reliably encoded by line weight or colour. Use **labels / the legend / built-in codes /
   hatching** instead. (For this project: the **BF** codes ARE the built-in tag — a BF label =
   built-in millwork.)
3. **Window symbol specifics (sliding=3 lines, casement=arc) → UNCONFIRMED.** Only the DOOR swing
   arc is airtight; don't over-read window type without the sheet legend.

## E. Open gaps (still unsourced — flag, don't fabricate)
- The **BF (built-in furniture) code scheme** used by Thai design-build firms — no public source
  documents it, and each drawing office runs its own. Treat `BF##` as *that firm's built-in
  millwork tag*, read the size off the label (form: `BF<nn>.<W>x<D>x<H>CM`), and where the meaning
  matters, **ASK the designer** rather than guess.
  <!-- REDACTED 2026-07-13 (client-privacy): the originating firm's name and the worked BF example
       lifted from that client's sheet were removed from this staged copy AND from the promoted
       successor. A client's drawing office and a client's furniture dimensions are project data
       (`projects/<PRJ>/`), not shared knowledge — see .claude/rules/client-privacy.md. -->
- **Owner check owed:** this DR was a WEB deep-research run (see `source:` above) and its framing
  named the client's sheet. Whether the firm name / sheet title actually left the machine in a
  search query cannot be recovered from this artifact. Flagged for the owner; no leak asserted.
- Single-vs-double vanity symbol, window type symbols, and material HATCH patterns (tile/wood/
  concrete/glass fills) were not authoritatively covered — get a graphic-standards hatch key.

## F. Checklist to apply to THIS project's `PLAN FURNITURE FLOOR 2`
1. For every bed/sofa/chair: find the headboard/backrest strip → set facing from it (not the sheet).
2. Before declaring furniture "complete": scan for LONG-dash rectangles (overhead built-ins you'd
   otherwise miss) and SHORT-dash rectangles (things under counters). Count them in.
3. Every **BF** label = a built-in; read its cm size from the label; don't infer built-in from line.
4. Read all room sizes off the 1:75 scale / written dims — never estimate proportionally.
5. Doors: use the swing arc for entry side + clearance; a dashed arc on this Thai sheet = swing path.
