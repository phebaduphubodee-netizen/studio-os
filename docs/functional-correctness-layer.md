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
- [x] **TV vs sofa** (living) — same facing logic against the primary seat. Closed 2026-07-04:
      `living_condo` split its fused `tv_feature` into a `cabinet` media wall + a standalone
      `tv_panel` facing the sofa (both real specs now PASS; a fused TV is still CAUGHT).
- [x] **Door vs bed head** (GS-01) — door not on the headboard wall / clear of the head.
- [x] **Seating faces focal** (GS-03/26) — sofa/armchairs oriented to the coffee-table/TV group.
- [x] **Bathroom fixture logic** (GS-05) — basin near entry (frequent use), WC/shower
      deeper; wet/dry zoning. (`suite_clearance` already knows the fixtures.)
- [x] **Furniture scale vs ergonomics/room** (GS-02/06) — seat height, piece size within
      norms and proportionate to the room. (Uses `knowledge/ergonomics/`.)
- [x] **Kitchen work-triangle** (NKBA; beyond the 26 notes, the kitchen extension) — sink /
      cooktop / fridge legs 1219–2743 mm, perimeter ≤ 7925 mm. Added 2026-07-04 with a
      `kitchen_demo.json` anchor; grounded in `knowledge/ergonomics/bathroom-kitchen-planning.md`.
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

## Status (2026-07-04)
- `placement_logic.py` + `test_placement_logic.py` (**55/55**) now hold EIGHT rules:
  tv_positioned / tv_faces_viewer / tv_not_over_viewer / tv_viewing_distance / door_vs_bed_head /
  furniture_dimensions / bathroom_logic / seating_faces_focal / kitchen_work_triangle. Wired as a
  PRE-RENDER gate at all three spec→render points (make_all clearance gate, repair_loop Gate 0
  ESCALATE-only, suite_package QA-CHECKLIST) — a FUNCTION FAIL aborts before the paid Gemini pass.
- Both production specs are now FUNCTION-clean: `bedroom_suite` (TV split onto the foot wall,
  2026-07-03) and `living_condo` (TV split onto the north media wall, 2026-07-04) — each verified
  by clearance PASS + placement PASS + a Blender clay smoke render (the TV materialises as a
  discrete control mass). A fused TV is still CAUGHT (synthetic specs + the escalation branch,
  both mutation-pinned).
- Scrutiny (2026-07-04, 4-lens adversarial workflow) confirmed the slice; the two findings were
  test-coverage holes (leg-max clause + Gate-0 escalation both passing for the wrong reason) —
  fixed and proven by mutation testing, not just re-asserted.
- NEXT: kitchen aisle / leg-obstruction rules (need run/opposing-counter grouping the @0.2 spec
  lacks); "camera has a reason" (no-dead-wall framing); more room types as specs arrive.
