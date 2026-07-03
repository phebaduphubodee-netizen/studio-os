# Functional-correctness layer — north star

> ทุกอย่าง ทุก detail ในงานต้องสมเหตุสมผลกับหลักการใช้งานจริง ลูกค้าน่าจะซื้อเพราะ
> ความล้ำ + ความสะดวกสบายของ function การใช้งานจริง **และต้องสวยด้วย** (ไม่ใช่แค่สวยอย่างเดียว)
> — owner, 2026-07-03

## Why this exists (the M3.2 lesson)
M3.2 judge calibration (2026-07-03) FAILED: a practicing designer REWORKed all 26
golden renders (ρ 0.428, κ 0.000). Root cause was not bad realism — the designer
PRAISED the light/depth-of-field/realism — it was **broken function**: the TV behind
the sleeper's head, furniture out of proportion, camera angles that show nothing,
bathroom fixtures ordered against use, doors fighting headboards. The LLM judge scores
**beauty**; it is blind to **function**. So the product's real differentiator — a home
that is genuinely usable AND beautiful — needs a layer the judge cannot provide.

## The three layers (separation of concerns)
1. **FUNCTION — deterministic, pre-render, this repo's job.** Geometry + ergonomics
   say whether a layout makes human-usage sense, BEFORE any paid render. No model, no
   render, no judge — pure code, fully unit-testable. If function fails, never render.
   - `suite_clearance.py` / `clearance_check.py` (Gate 0): circulation, clearances,
     Thai code minimums. **Already built.**
   - `placement_logic.py` (NEW, slice 1): human-usage placement — TV faces the bed,
     not behind the head, not over it, sane viewing distance. **Extensible rule set.**
2. **BEAUTY — Gemini hybrid render.** Photoreal materials, light, styling. Already
   strong (the designer's praise lands here). Its job is to make the *functionally
   correct* control look magazine-grade — never to invent geometry (that is why an
   un-positioned TV drifts: give it coordinates, Gemini paints it there).
3. **JUDGMENT — the designer (human).** M3.2 proved no auto-judge can gate production
   alone. The designer is the arbiter; the LLM judge is at most a photoreal pre-filter.

## Roadmap — the designer's 26 notes ARE the requirements
Deterministically checkable (belongs in the FUNCTION layer; build as rules):
- [x] **TV vs bed** — faces the bed, not behind/over the head (GS-11/23/24). `placement_logic` v1.
- [ ] **TV vs sofa** (living) — same facing logic against the primary seat.
- [ ] **Door vs bed head** (GS-01) — door not on the headboard wall / clear of the head.
- [ ] **Seating faces focal** (GS-03/26) — sofa/armchairs oriented to the coffee-table/TV group.
- [ ] **Bathroom fixture logic** (GS-05) — basin near entry (frequent use), WC/shower
      deeper; wet/dry zoning. (`suite_clearance` already knows the fixtures.)
- [ ] **Furniture scale vs ergonomics/room** (GS-02/06) — seat height, piece size within
      norms and proportionate to the room. (Uses `knowledge/ergonomics/`.)
- [ ] **Camera has a reason** (GS-04/05/22) — the framed view must contain the subject,
      not aim at a blank wall. (Partly geometric — the eye-camera solve already aims at
      the hero; tighten "no dead-wall framing".) Camera height 1.0–1.2 m already landed
      (`camera_config.py`, M3.2 GS-15).

Render-domain (stays with Gemini + designer, NOT this layer):
- Material realism / laminate seams / repetition (GS-03/25), polygon look (GS-02),
  styling nuance, final aesthetic. These need vision/render, not spec geometry.

## Conventions for FUNCTION rules
- Pure stdlib, operate on the room-spec@0.2 (x,y = SW corner mm, front = -Y at rot 0).
- Verdicts PASS/WARN/FAIL/UNWIRED; a MISSING position (an element the render pass would
  otherwise invent) is a FAIL, never a silent pass — that is the whole point of the TV fix.
- Every rule ships with synthetic-spec tests pinning the behavior + the real specs as
  anchors (`test_placement_logic.py`). Scrutinize per the 6-cycle law before wiring.
- Wire into the pipeline as a pre-render gate (alongside Gate 0) so a functionally
  broken spec is caught before the paid Gemini pass — cheap failure first (blueprint §9.5).

## Status (2026-07-03)
- placement_logic.py + test_placement_logic.py (9/9): slice 1 = TV-vs-bed. Runs on the
  real bedroom_suite → **FAIL (tv fused into headboard, no position)** = the real bug, caught.
- NEXT: (a) give the bedroom TV real coordinates on the foot wall (split `headboard_tv`),
  re-run clearance + placement_logic + a Blender smoke render; (b) add the next rules above.
