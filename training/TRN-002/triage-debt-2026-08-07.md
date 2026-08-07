# TRN-002 — R7 triage debt, paid 2026-08-07

The R7 half of `rule_gate` had never executed: `check()` runs `audit_bundle`
only `if bundle_dir:` and the one call site in `trn002_build.py` passed none.
Every render therefore printed **"RULE GATE: N masses, all justified"** while
the triage rule was mute, and a mute is indistinguishable from compliance.

Wired 2026-08-07 at ITEM level. Run across all 21 bundles of this lane it
cleared **18** and named **3** — the debt below. The 18 matter as much as the 3:
a file-level version of this check reported eleven correctly-triaged rounds as
violations, and a gate that fails on correct work is the one that gets muted.

**And the first thing the check found is the argument for it.** r26's
`C2#14` read:

> *"The panel widths in the wardrobe run are **arbitrarily unequal** and their
> joints do not align with the bulkhead above, with the wood ledge that runs at
> headboard height, or with each other. Joinery is set out; unequal bays with
> no reason read as a mistake, not a rhythm."*

Nobody triaged it. **One round later the owner looked at r26 and asked why
there are two doors at the head of the bed** — and r27 found that same wardrobe
built 259 mm short. The blind critic named the defect a round before the eye
had to, and the item was dropped because nothing counted the items. The loss
was in the accounting, not in the rung.

---

## `critique-trn002_mat_r26` — C2#14

| ข้อ | triage |
|---|---|
| **C2#14 "จังหวะบานตู้ไม่เท่ากัน — panel widths arbitrarily unequal, joints do not align with the bulkhead, the headboard-height ledge, or each other"** | **✗ หักล้างด้วยการวัด — และผมรับมันไปก่อนหน้านี้โดยไม่ได้วัด** เจ้าของเปิดสิทธิ์ให้ดูภาพเป้าได้ 2026-08-07 วัดตำแหน่งรอยต่อจากภาพเป้าเทียบของเรา: **u = 810 / 874 / 950 / 1043 (เป้า) เทียบ 810 / 873 / 949 / 1042 (เรา) — ตรงกันภายใน 1 px ทั้งสี่เส้น** และ **ช่วงบานของภาพเป้าเองไม่เท่ากันจริง ๆ**: กว้าง 23/11/6/23/15/64/76/93/28 px = สเปรด **231% ของค่าเฉลี่ย** critic เอาหลัก *"joinery is set out"* ซึ่งเป็น prior ทั่วไป มาทาบผนังที่ของจริงมันไม่เท่ากัน — คลาสเดียวกับที่ R10b ตั้งชื่อไว้: critic ตาบอดตอบคำถาม *"น่าเชื่อมั้ย"* ไม่ใช่ *"ตรงกับเป้ามั้ย"* |
| **บทเรียนของผมเองในรอบนี้** | **การ "รับ" ก็ต้องมีหลักฐานเหมือนกัน** R7 เขียนว่าการหักล้างต้องพกการวัด และผมอ่านมันเป็น "การรับไม่ต้อง" จึงรับข้อนี้เข้า queue ทั้งที่มันผิด — **ข้อที่รับผิดคือการเอางานผิดเข้าคิว ซึ่งแพงกว่าการหักล้างผิด** เพราะไม่มีใครมาตรวจซ้ำ |

## `critique-trn002_mat_r27` — C2#15

| ข้อ | triage |
|---|---|
| **C2#15 "No skirting, shadow gap, or any wall-to-floor junction detail"** — ผนังชนพื้นเป็นเส้นคมที่ (140–200, 590–625) และ (415–430, 600–620) กรอบประตูก็วิ่งชนปาร์เกต์เฉย ๆ | **✓ รับ เข้าเลน craft (ยังไม่มีตัวเลข)** ห้องที่สร้างจริงมีอย่างใดอย่างหนึ่งเสมอ: บัวเชิงผนัง / ร่อง shadow gap / รอยสกrib **ยังไม่หักล้างและยังไม่รับด้วยตัวเลข** เพราะยังไม่มีใครวัดรอยต่อผนัง–พื้นของภาพเป้า — และตามกฎ R7 การหักล้างต้องพกการวัด ส่วนการรับไม่ต้อง จึงรับไว้ก่อน **เงื่อนไขก่อนสร้าง:** วัดว่าภาพเป้ามีบัว มีร่อง หรือไม่มีอะไรเลย ถ้าไม่มีอะไรเลย ข้อนี้กลายเป็น "ของเราขาดเงาที่รอยต่อ" ไม่ใช่ "ขาดบัว" — คนละยา |

## `critique-trn002_mat_r23` — C3#5, C3#6, C3#11, C3#12

Gemini flash ยื่น 12 ข้อ gate #10 triage ไป 8 · สี่ข้อนี้หล่นเงียบ

| ข้อ | triage |
|---|---|
| **C3#5 "ฐานเตียงเป็นทรงเรขาคณิตเรียบง่ายเกินไป ขอบมนแบบโมเดลพื้นฐาน"** | **✓ รับ ซ้ำกับคลาสที่รู้อยู่แล้ว** = C2#3 ของ gate #15 (แถบดิ่งแข็งบนฐานเตียง) และเป็นอาการของ `oct_mesh(seg=6)` = 56 verts / 30 faces ไม่มี `shade_smooth` ไม่มี SUBSURF → **เลน craft ข้อ 1** ไม่ใช่เลนวัด |
| **C3#6 "บานเลื่อนตู้เป็นแผ่นระนาบขาวเรียบ ไม่มีมือจับ ไม่มีรายละเอียดวัสดุ"** | **⧗ ครึ่งรับ** ครึ่ง "ไม่มีมือจับ" **หักล้างด้วยการวัดที่มีอยู่แล้ว**: ภาพเป้าเป็นตู้ handleless จริง ร่อง 1.05 มม. = unresolved ที่กล้องนี้ (gate #7, C2#6) · ครึ่ง "แผ่นขาวเรียบไม่มีวัสดุ" **✓ รับ** = C2#11 ของ gate #15 ที่ยังเท่าเดิมเป๊ะ → เลนวัสดุ |
| **C3#11 "กระจกโต๊ะเครื่องแป้งสว่างขาวโพลนจนไม่เห็นสิ่งที่สะท้อน"** | **✓ รับ** และเป็นข้อเดียวในสี่ข้อที่ **ไม่มีใครหยิบเลยตั้งแต่ r23** — กระจกของเราไม่ใช่กระจก มันคือผิว emissive/ขาวที่ไม่สะท้อนอะไร (shader ทั้งเลนมีแค่ base color / roughness / metallic / emission ไม่มี transmission ไม่มี coat) → **เลน craft พร้อม C3#11 เป็นตัวอย่างที่วัดได้**: ค่าที่วัดของกระจกเทียบเป้า |
| **C3#12 "มือจับประตูเล็กเป็นรูปทรงพื้นฐานเกินไป"** | **✓ รับ เป็น declared gap** — ฮาร์ดแวร์ทั้งห้องอยู่ในเลน ACQUIRE (R8: มือจับไม่ใช่ free-form ปั้นได้ แต่มันคือของที่ซื้อถูกกว่าปั้น) ยังไม่มีชิ้นไหนถูกซื้อจริงในเลนนี้เลย ซึ่งเป็นข้อค้างของ R8 ไม่ใช่ของ C3#12 |

---

**สิ่งที่หนี้ก้อนนี้เปิดเผย:** สามในสี่ข้อของ r23 และทั้งสองข้อของ r26/r27 เป็น
**ข้อ craft** — ขอบ, ผิว, กระจก, รอยต่อ, ฮาร์ดแวร์ — ไม่ใช่ข้อวัด และไม่มีข้อไหนที่
ladder (LEVEL / SHAPE / p50 / p99) ให้คะแนนได้ นี่ไม่ใช่เรื่องบังเอิญ: ข้อที่เครื่องมือ
ของเลนนี้ให้คะแนนได้ จะถูกหยิบเสมอเพราะมันแปลเป็นรอบถัดไปได้ทันที ส่วนข้อที่ให้คะแนน
ไม่ได้ ต้องอาศัยคนจำมันไว้ — **และการหล่นหายทั้งหมดเกิดในกลุ่มหลัง**
