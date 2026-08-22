# Owner advice session — 2026-08-22 (บันทึกคำต่อคำ; recorded_at ของ ORD-2026-08-22-front-door-dims)

Four owner messages in one sitting, ending in an order. His words verbatim:

1. **"ทำไมคุณประเมิณวิธีแก้ปัญที่เป็นสมเหตุสมผลเองไม่ได้ เช่นตอนได้ model เตียงมา
   คุณบอกไม่ได้ด้วยซ้ำว่ามันเล็กไป ต้องรอให้ผมสั่งแก้ว่าให้ไปหาขนาดมาตรฐานมาใส่
   แล้วขยับของรอบ ๆ"** — answered with a 9-agent evidence sweep: 28 gate rungs,
   3 world-standard, 1 blocking; `ergonomics_ref.nearest_bed_size(1243,1569)`
   would have failed the p2r52 mattress by 336 mm and no path fed built numbers
   to it; the owner's eye preceded green instruments 15 times in 33 days.

2. **"และผมไม่ชอบที่ต้องรอให้ render ออกมาก่อนถึงจะเห็นว่ามันผิด"** — measured:
   the 1243 number existed at three pre-render stages (bench arithmetic, scene
   dump, then pixels); ~10 of the 15 eye-catches were determinable from data
   before a full frame.

3. **"คุยก่อน ถามตรง ๆ ตอนนี้ project ใหญ่เกินกว่าที่ตรวจเช็คได้ว่าขั้นไหนผิดอะไร
   แล้วใช่ไหม?"** — answered: post-hoc tracing still works and terminates; the
   LIVE map ("which stage asks what / what nobody asks") no longer fits any
   head — producing the first full census took a 5-agent fan-out; defects have
   moved from inside mechanisms to the seams between them.

4. **"ทำตัวฉลาด ๆ แล้วแนะนำผมหน่อยสิ"** — the advice given, in order:
   (1) close P2 with the remaining craft work, do not stall the lane for meta
   (the 2026-07-16 factory-of-referees lesson);
   (2) BEFORE P4, build ONE thing: the front-door rung — built dimensions vs
   world standards, no allowlist, at bench arithmetic + scene dump, not at
   render — because P4 styling walks many new objects through the same door
   the bed slipped through;
   (3) the "too big to hold" answer is a PRINTED MAP (dimension x stage,
   qa/coverage-map.json at session open) + D-112's existing admission quota,
   NOT a 29th enforcement rung;
   (4) the structural debt (rung consolidation, R9 relationships for the NEXT
   project's spec, full earliest-stage migration) is paid in one batch after
   DELIV-001, before the real client run (D-113);
   (5) his three highest-value personal actions: ASK-006 RANK sheet, the two
   SC-3 practitioner questions, one paid-library trial decision.

5. **"ลุย"** — the order. It covers items (2) and (3) — the two the builder said
   were waiting on his word. Item (1) continues as the standing plan, item (4)
   is scheduled at the DELIV-001 boundary, item (5) is his side.

## What was built the same day under this order

- `pipeline/scripts/dim_check.py` — scene-dump dims vs world standards, no
  allowlist, three-state (ok / signed-interim / fail), exit 0/1/2, spawned by
  `build_room._score_deliverable` on every render including R5 quick (the
  defect is arithmetic before it is pixels). Admission per D-112 printed in its
  own header: owner-ordered; the defect class (built size vs the real thing)
  had no instrument — his eye filed it three times (bed 08-18, garments 08-12,
  nightstand datum 08-22); extends asset_scale's self-declared blind spot.
- `wholebed_bench.py` + `wholebed_rules.verdict` — the bench now projects the
  anchor mattress through the fit scale and refuses a candidate whose projected
  mattress is no standard bed's size (`anchor_std`), before any build round.
- `pipeline/scripts/ergonomics_ref.py` `BED_SIZES_TH_MM` + knowledge distillation
  (knowledge/_inbox/web-thai-mattress-sizes-2026-08-22.md → ergonomics md §Thai)
  — D-114's declared assumption 1800x2000 upgrades to a sourced value.
- `qa/dim-deficits.json` — signed-deficit register (the R13 third state for this
  rung); first row: garment rails 614-715 vs the 700 shirt floor, citing
  ORD-2026-08-12-garment-scale-is-wrong, floor 600.
- `qa/coverage-map.json` + `plan_status.coverage_lines()` — the map, printed at
  every session open; admission stays D-112's discipline, no new checker.
