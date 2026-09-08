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

---

## RANK — คำตอบแรกของเจ้าของมาถึงแล้ว (2026-08-22, ผ่านช่องแชท — วันแรกที่ช่องถูกซ่อม)

Verbatim: **"คำตอบของผมคือสัดส่วนตู้ built-in ที่ fix ไว้ ทำให้ เตียงดูเล็กมาก ๆ ทำยังไงดี?"**
— เหตุผลรูป "ข้อบกพร่อง" ไม่ใช่รสนิยม ตรงเกณฑ์ของแผ่น; การเรียง A-F เต็มยังเปิดรออยู่
(ASK-006 คงสถานะ open)

### การวัดที่ตามคำตัดสิน (ตา = อะไร, เครื่อง = เท่าไหร่)

เฟรมเรา (นับจาก idmask, แม่น): เตียง soft กว้าง 0.49 ของเฟรม, พื้นที่ 12.3%
(รวมแถบหัวเตียง 17.1%), ผิวนอนอยู่ที่ y 0.49-0.95 จากบนลงล่าง — ขอบบนของเตียง
สูงราว 0.4 ของเฟรมจากล่าง. กล้อง canonical: 24mm, z 1.15 m, aim มุม NE.

งานส่งจริง 7 ใบ (วัดตาเห็นโปรโตคอลเดียวกัน, reader_A panel p2r54): แตกเป็นสองโหมด
เสมอ — (ก) **เตียงเป็นพระเอก**: กล้องลดลง ~1.1-1.2 m, เตียงกว้าง 0.5-0.7, พื้นที่
15-35%, ผิวนอนอยู่ต่ำ ~0.3, และเตียงถูกขอบเฟรมตัดเสมอ (ดันเข้ากล้อง) — (ข)
**ตู้/ผนังเป็นพระเอก**: เตียงเป็นเสี้ยวมุมล่าง 7-13%. ใบที่ตู้กิน 0.5-0.6 ของเฟรม
(เท่าเรา) ล้วนเลือกโหมด (ข). เฟรมเราตัวเลขอยู่ "ในแบนด์" แต่ไม่เข้าโหมดไหนเลย:
กล้องสูงกว่าทุกใบ, เตียงลอยกลางระยะ มีพื้น/พรมคั่นหน้า, แบ่งเฟรมครึ่ง-ครึ่งกับตู้
— นี่คือกลไกที่ทำให้ "ตู้ fix ไว้แล้วเตียงดูเล็ก": ไม่ใช่ขนาดตู้ แต่คือเฟรมที่ไม่เลือกข้าง

### คิวที่ตามมา (D-117): commit โหมด (ก) — กล้อง ไม่ใช่เรขาคณิต; ตู้เป็น ink ไม่แตะ

---

## 6. BlenderKit — คำสั่งเย็นวันเดียวกัน (2026-08-22; recorded_at ของ ORD-2026-08-22-blenderkit-one-month)

Verbatim: **"สมัคร blenderkit 1 เดือนเลย ผมอยากจะรู้ว่ามันจะทำให้งานดีขึ้นยังไง"**

การอ่าน (ของ builder — พี่แก้ได้จากแถวนี้): ประโยคแรกคือคำตอบของ ASK-029 ("เอาทางไหน" = หนึ่งเดือน,
ตามที่พี่เลือกไว้เช้าวันเดียวกัน "สมัครเดือนเดียวก่อนไม่ได้หรอ") — ASK-029 ปิดเป็น answered ด้วยประโยคนี้;
ขั้นจ่าย + วาง key เป็น ASK-031 (มือพี่เท่านั้น). **ราคา:** หนึ่งเดือนจริงคือแท็บ "30 day glimpse" $19.90
ไม่ต่ออัตโนมัติ (Monthly $17.90 · Yearly $9.90/เดือน = $118.80/ปี) — เลข $9.90 ที่ทะเบียนจำไว้ตอนเช้าคือ
แท็บ Yearly ที่หน้าเปิดเป็นค่าเริ่มต้น (reviewer fresh-context จับได้เย็นเดียวกัน). ประโยคหลังคือ**คำถามที่เดือนนั้นต้องตอบ
ด้วยตัวเลข** — เกณฑ์ล็อกไว้ก่อนโหลดตัวแรก (D-119) และแผนทั้งเดือนอยู่ที่
`docs/blenderkit-month-2026-08-22.md`. สิ่งที่สร้างทันที: `pipeline/scripts/blenderkit.py`
(fetch ด้วย key → GLB → scale sidecar; `shortlist` เดิน 135 เตียง full-plan เข้า bench เอง;
`status` พิมพ์นาฬิกาเดือน) พิสูจน์ด้วย control ทั้งสองทางบนชั้นฟรีก่อนพี่จ่าย.
