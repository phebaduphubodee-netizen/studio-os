# Process review 2026-08-22 — วิธีทำงานของเรา vs interior designer ตัวจริง

**ที่มา:** เจ้าของสั่ง review ว่ากระบวนการของ repo นี้เหมือน/ต่างกับ designer ตัวจริงอย่างไร
และต้องปรับอะไร เพราะ "เราช้ามากและผิดเยอะมากเมื่อเทียบกับตัวจริง"
หลักฐานรวบรวมโดย 6 fresh-context agents อ่าน repo เท่านั้น (pace จาก git log 567 commits,
practitioner knowledge ที่กลั่นไว้แล้ว, time-sink audits, asset economics, task framing, counter-case)

## ข้อค้นพบหลัก (ตัวเลขทั้งหมดมี path ใน repo)

- เฟรมห้องนอนหลังเดียวกิน ~96 รอบ / 90+ full frames ใน 16 วัน (TRN-002 38 + P2 55 + P1 1 + P3 2);
  ทั้ง repo >=116 รอบ ภายใต้ R1 ที่เขียนว่า cap = 2 รอบ/กลไก (qa/curriculum-caps.json)
- สตูดิโอเพื่อน: SketchUp + Enscape (228/230 ภาพส่งจริงที่ระบุ renderer = Enscape, เรียลไทม์) ·
  ซื้อ/โหลดโมเดลทั้งหมด (96/96 โฟลเดอร์ cache เป็น 3D Warehouse; วงการ 80-90% โหลดเตียงแล้ว re-shade) ·
  ตัดสินด้วยตาต่อเนื่อง (qa/owner-asks.json ASK-025, knowledge/styles/style-and-asset-references-discord.md)
- เรา: quick look 68 วิ / full ~15 นาที ตาบอดระหว่างรอบ · ณ 08-15 ปั้นเอง 467/569 masses (82%),
  ของซื้อ = 3.78% ของพิกเซล · pipeline/scripts 284 ไฟล์ / ~105k บรรทัด ซึ่ง ~3/4 เป็นเครื่องตรวจ
  (docs/orders-vs-frame-audit-2026-08-15.md)
- Sink อันดับ 1 ไม่มีคู่แข่ง: ปั้นของที่มืออาชีพซื้อ — ผ้าเตียง 10 decision rows,
  soft-goods-read-rigid ถูกยื่น 49/49 รอบ, garments 5 รอบ + 785 บรรทัด cloth physics เขียนเอง;
  audit 08-15 หักล้างคำแก้ตัว "รอบหายไปกับเครื่องมือ" แล้ว — 26/32 รอบแก้ geometry จริง
  รอบหายไปกับการปั้นซ้ำ/ตัดสินซ้ำ object ประเภทเดิม
- ชั้นเสียเงิน priced + licence-verified ตั้งแต่ 07-01, ไม่ถูกลองเลย 48 วัน จน "ลุย BlenderKit" (08-18)
  คืนเดียวได้ shelf 2,147 ตัว และเตียง interim ที่ตัด bare-flank 99.4% (panel most -> none 3/3)
- ส่วนที่การเทียบไม่แฟร์ (บันทึกไว้กันอ่านผิด): โจทย์ reproduction-ห้าม-copy-เคยห้ามดู target ไม่ใช่โจทย์ designer ·
  เฟรมที่แพ้ 25/30/40 เป็นเฟรม objects-phase ที่แสงยังไม่ทำ (ลำดับ objects->light เป็นคำสั่งเจ้าของ) ·
  นับรอบรวมการสร้างโรงงาน 284 เครื่องมือที่ designer ใช้ SketchUp+Enscape ไม่ต้องสร้าง

## ข้อเสนอ 6 ข้อที่ยื่นให้เจ้าของ

1. ปิด ASK-029 — จ่าย BlenderKit แล้ววาง API key (การกระทำของเจ้าของล้วน ๆ)
2. ถามเพื่อน designer 3 คำถาม: ปั้นเองชิ้นไหน/ซื้อชิ้นไหน · ลูกค้าไทยส่งกลับแก้อะไรบ่อยสุด ·
   1 เฟรมห้องนอนใช้เวลาเท่าไร
3. พลิก default การ sourcing ให้ครบ class (built-in ปั้น / loose ซื้อ) + ซ่อมท่อ:
   fetch FurniMesh (อนุมัติแล้ว 0 ไฟล์), เปิด import format ให้กว้างกว่า gltf ทางเดียว
4. ทำ loop การมองให้ถูกลง ~10 เท่า — glance rung ระดับวินาที (Eevee/Workbench snapshot)
   เป็น rung มาตรฐานของ LOOK-while-working; Cycles เก็บไว้ปิด gate
5. หยุดขยายโรงงานกรรมการ — เครื่องมือใหม่ต่อเมื่อ critic-debt class นั้นยังไม่มีตัวมอง
   (ตอนนี้มี 9 class ที่ไม่มีเครื่องมอง — ใช้โควตากับตรงนั้นเท่านั้น)
6. แยก "ฝึก" กับ "แข่ง" — สนามที่วัดความเร็วจริงคือโปรเจกต์ลูกค้าจริงด้วยของซื้อ
   ไม่ใช่ reproduction; ให้เจ้าของเลือกเมื่อ DELIV-001 ปิด

## คำตอบเจ้าของ (verbatim, 2026-08-22)

> 1. สมัครเดือนเดียวก่อนไม่ได้หรอ
> 2. 4 วัน
> 3 - 6 ลุย

## การอ่านและการบันทึก (การอ่านเป็นของ builder — เจ้าของแก้ได้จากแถวนี้)

- **ข้อ 1** = เลือกเส้นทางรายเดือน: ได้ — BlenderKit Full มี $17.90/เดือน ยกเลิกได้
  (ราคา verify ใน repo 2026-08-18; ASK-029 อัปเดตแล้ว) สมัคร 1 เดือน, bench คลัง full-plan 135 ตัว
  ระหว่างเดือนนั้น, ต่ออายุตัดสินจากผลที่วัดได้
  **คำเตือนความปลอดภัย:** 2026-08-22 การเรียก https://www.blenderkit.com/plans/pricing/ ตอบ
  301 redirect ไป `blendkit.com` (สะกดไม่มี "er" — โดเมนเลียนแบบ) builder ไม่ตามลิงก์นั้น
  ตอนจ่ายเงินให้เช็ค address bar ว่าเป็น `blenderkit.com` ตัวจริงเท่านั้น
- **ข้อ 2** "4 วัน" = คำตอบของคำถามข้อสุดท้าย (เวลา/เฟรมของเพื่อน): **1 เฟรมห้องนอน ~4 วัน**
  (บันทึกเป็น ASK-030 answered) นี่คือไม้บรรทัดที่ repo ไม่เคยมี: เรา 16 วันบนเฟรมเดียวและยังไม่จบ
  = ช้ากว่า ~4 เท่าโดย wall-clock — ไม่ใช่ร้อยเท่า — แต่ 4 วันของเขารวมทั้ง scene จากของซื้อ
  บนเครื่องมือเรียลไทม์ · คำถามอีกสองข้อ (ปั้นเอง/ซื้อ · ลูกค้าส่งกลับ) ยังเปิดอยู่ที่ ASK-004
- **ข้อ 3-6 "ลุย"** = คำสั่ง:
  - ข้อ 3-5 เป็น builder actions → ORD-2026-08-22-process-review-actions (ลงมือทันที session นี้)
  - ข้อ 6 เป็นทิศทางอนาคต → ORD-2026-08-22-real-client-run-next (trigger = DELIV-001 ships) ·
    ลำดับกับ standing order TRN-003 (reproduction curriculum, 2026-07-30) เป็น D-113:
    client run เป็น unit ถัดไปหลัง DELIV-001, curriculum ไม่ถูก retire — เจ้าของ overrule ได้ทุกเมื่อ
  - กลไกของข้อ 5 → D-112 (instrument quota: refuse-by-default นอก critic-debt-ไม่มีตา)

## Spend ของ review นี้ (R6)

Workflow 6 agents อ่านอย่างเดียว ~766k tokens / 193 tool calls · 0 render rounds · ไม่มีการแก้โค้ดใน review
