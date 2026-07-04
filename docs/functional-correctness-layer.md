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
- [~] **Seating faces focal** (GS-03/26) — PARTIAL. `seating_faces_focal` checks only a seat's
      *orientation* (does its front half-plane contain a focal), WARN-only, and skips any seat
      with no `rot`. So it encodes the GS-26 principle (a seat angled to receive the sofa =
      correct) but CANNOT decide GS-03 "armchair ไม่ควรตั้งตรงนั้น" (no position/circulation
      model) or GS-20 "armchair เอาออก" (no existence/redundancy logic). NB: the real
      `living_condo` armchair carries no `rot`, so it is not evaluated at all — its PASS comes
      from the sofa alone.
- [x] **Bathroom fixture logic** (GS-05) — basin near entry (frequent use), WC/shower
      deeper; wet/dry zoning. (`suite_clearance` already knows the fixtures.) NB: the basin-at-
      entry ordering is a hard FAIL, but wet/dry zoning is WARN-only, and in-bath per-fixture
      approach clearance is not checked (only aggregate ฉ.39 area/width + path-to-door).
- [~] **Furniture scale vs ergonomics/room** (GS-02/06) — PARTIAL. `furniture_dimensions`
      (WARN-only) checks table height, wardrobe depth and gross bed-footprint mis-scale — NOT
      seat height (GS-02 "ที่นั่งสูงเกิน" is explicitly excluded: the spec has no `seat_h`
      field). Material real-scale — laminate 2.40×1.20 seams (GS-03), SPC plank scale (GS-06) —
      is checkable-in-principle but NOT built (needs a `texture_scale`/material field the spec
      lacks); polygon/repetition (GS-02/25) is genuinely render-domain.
- [x] **Kitchen work-triangle** (NKBA; beyond the 26 notes, the kitchen extension) — sink /
      cooktop / fridge legs 1219–2743 mm, perimeter ≤ 7925 mm. Added 2026-07-04 with a
      `kitchen_demo.json` anchor; grounded in `knowledge/ergonomics/bathroom-kitchen-planning.md`.
- [x] **Camera has a reason** (GS-04/05/22) — the framed view must contain the subject,
      not aim at a blank wall. Closed 2026-07-04: `camera_has_a_reason` (rule 10). The whole
      eye-camera SOLVE was extracted out of `build_room` (bpy, not importable) into
      `camera_config.solve_eye_camera` so ONE definition is shared by the materializer (renders
      it) and the gate (validates it) — no split-brain. The rule FAILs when no valid shot exists
      (the `--eye` render would `SystemExit` — caught pre-render, before the paid pass), and WARNs
      when `frame_subject_share` (level rays vs furniture footprints, a floor-plan proxy) shows the
      FOV is mostly bare wall. Camera height 1.0–1.2 m already landed (`camera_config.py`, M3.2 GS-15).

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

## Designer critique round 2 (2026-07-04, owner acting as the designer eye)
The GS-27..30 re-renders were reviewed directly (not via labeler) and REWORKed again. Root causes,
triaged: (1) **TV rendered on the FLOOR** (GS: "ทำไมเอา TV ไปติดไว้ที่พื้น?") — build_room extruded
built-ins from z=0; FIXED with a `mount_mm` (AFF) field so wall elements FLOAT, + `tv_mount_height`
rule (WARN if a wall TV lacks a mount). (2) **armchair under / in front of the TV** (GS-03, "TV อยู่หลัง
คนนั่ง") — `seating_faces_focal` only judged orientation and skipped no-rot seats; ADDED
`seating_clear_of_screen` (position rule: flags a secondary lounge seat in the viewer→TV corridor).
(3) monotonous wood walls + Gemini hallucinations (a phantom handle, a stray mass) = render/prompt
domain. (4) **ROOT CAUSE the owner named:** `bedroom_suite` is a LOOSE approximation of the real
Floor-2 master (its own note says "positions approximated from a plan image"; terrace not modelled),
and `living_condo` is FICTIONAL — neither is a faithful client unit. DECISION: re-derive the REAL
rooms (master + Floor-1 living + Floor-2 sitting) precisely from the DXF (`raw-local`, ezdxf), retire
`living_condo`.

### Re-derivation status (2026-07-04)
Done: three dimension-authoritative specs — `master_bedroom.json`, `sitting_room.json`,
`living_room.json` — replace the loose/fictional pair (`living_condo.json` marked DEPRECATED, kept
only as a test fixture). KEY FINDING from the CAD dig (`ezdxf`): the DXF is usable for DIMENSIONS
(walls flatten to mm; the drafter's written dims are authoritative — bay 5500 × [2850+2950+700],
right bay 5100, coffee-table F03 1000×1000 as a raster scale) but NOT for furniture POSITIONS —
the interior-furniture layer sits in a mirrored, mixed-scale, SQUASHED, anonymized-block frame, and
freehand raster tracing is exactly the drift the owner flagged. So each spec's DIMENSIONS + ZONES are
authoritative; FURNITURE XY is ergonomic design judgement placed to pass the gates, documented per
file. master_bedroom fixes the real dimensional error (interior 5500×5800 + 700 terrace, was 6500
all-interior; bed 7'×6.5' was 6ft) and passes FUNCTION (clearance is tight — a 2134 mm N-S bed can't
meet 610/910 in a 2950 mm zone, which the real drafted room also can't). sitting_room = FUNCTION+
clearance clean; living_room = FUNCTION clean (all TV rules pass: wall-mounted mount_mm 900, faces the
sofa, seating clear of sightline — the round-2 TV critique enforced), clearance REVIEW (advisory).
OPEN: furniture XY + entry doors need designer confirmation or a cleaner CAD/DWG export before a
render gates a deliverable.

## Status (2026-07-04)
- `placement_logic.py` + `test_placement_logic.py` (**75/75**) now hold TWELVE rules:
  tv_positioned / tv_faces_viewer / tv_not_over_viewer / tv_viewing_distance / door_vs_bed_head /
  furniture_dimensions / bathroom_logic / seating_faces_focal / **seating_clear_of_screen** /
  kitchen_work_triangle / **tv_mount_height** / camera_has_a_reason. The two new rules answer the
  designer's round-2 TV-on-floor + armchair-under-TV comments; both are advisory WARN. build_room now
  floats built-ins by `mount_mm` (AFF), and `camera_config.solve_eye_camera`'s ray-block was made
  z-aware to stay coupled to where a floated mass actually sits (scrutiny-caught regression, fixed). (The prior revision of this doc said "eight"; the code shipped nine at that
  point — that stale prose is corrected here, and camera_has_a_reason is the tenth, added
  2026-07-04.) Wired as a PRE-RENDER gate at all three spec→render points (make_all clearance gate,
  repair_loop Gate 0 ESCALATE-only, suite_package QA-CHECKLIST) — a FUNCTION FAIL aborts before the
  paid Gemini pass. The eye-camera solve now lives in `camera_config.solve_eye_camera`
  (`test_camera_config.py` **17/17**), imported by both build_room and camera_has_a_reason.
- Both production specs are now FUNCTION-clean: `bedroom_suite` (TV split onto the foot wall,
  2026-07-03) and `living_condo` (TV split onto the north media wall, 2026-07-04) — each verified
  by clearance PASS + placement PASS + a Blender clay smoke render (the TV materialises as a
  discrete control mass). A fused TV is still CAUGHT (synthetic specs + the escalation branch,
  both mutation-pinned).
- Scrutiny (2026-07-04, 4-lens adversarial workflow) confirmed the slice; the two findings were
  test-coverage holes (leg-max clause + Gate-0 escalation both passing for the wrong reason) —
  fixed and proven by mutation testing, not just re-asserted.
- HONESTY CAVEAT — the load-bearing open item: everything above is the FUNCTION layer gating the
  *spec* against rules WE derived from Peat's 26 notes. **The loop is NOT closed until Peat labels.**
  As of 2026-07-04 the causal test is STAGED but the verdict has NOT moved: `bedroom_suite` +
  `living_condo` were re-rendered through the full pipeline (clay eye camera → Gemini pro-tier
  hybrid → critique) at BOTH camera heights (1.15 default + 1.5 A/B, item N), curated as GS-27+,
  and staged for a blind re-label — but `labels.json` is STILL the original one round, 26/26 REWORK,
  0 SHIP. "Passes the FUNCTION gate" ≠ "Peat's REWORK flipped to SHIP"; only Peat's new labels +
  `judge_calibrate.py` prove that. The render/material notes (GS-01 black blob, GS-21 black beam,
  GS-02 polygon, GS-25 repetition, GS-19 frame) are legitimately render/Gemini + designer domain,
  not this layer.
- NEXT (real): **Peat blind-labels GS-27+ in `qa/golden-set/labeler.html`** → re-run
  `judge_calibrate.py`; a moved verdict (some GS-27+ = SHIP) is the only proof the comments are
  addressed. Then: kitchen aisle / leg-obstruction rules (need run/opposing-counter grouping the
  @0.2 spec lacks); seat_h / texture_scale schema fields for the remaining GS-02/06 furniture-scale
  checks; more room types as specs arrive.
