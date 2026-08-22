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
  **คำเตือนความปลอดภัย (แก้แล้ววันเดียวกัน):** 301 ไป `blendkit.com` เป็น **rebrand จริง**
  ไม่ใช่โดเมนเลียนแบบ — BlenderKit → Blendkit 2026-06-10 ตามคำขอ trademark ของ Blender
  Foundation (ยืนยัน: redirect ออกจาก origin จริง + BlenderNation + release notes add-on
  v3.21.0 'formerly known as BlenderKit') · ราคาปัจจุบันหลัง rebrand ถูกลง: **$9.90/เดือน**
  (เดิมบันทึก $17.90) · การหยุดไม่ตาม cross-domain redirect บนเส้นทางจ่ายเงินจนกว่าจะ verify
  เป็นพฤติกรรมที่ถูก — ที่ผิดคือประกาศ 'โดเมนเลียนแบบ' ก่อน verify แทนที่จะพูดว่า 'ยังไม่รู้'
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

## Glance rung — measured (ข้อ 4, ทำแล้ว 2026-08-22)

`pipeline/scripts/glance.py` — build machinery ไม่ใช่กรรมการ (ฝั่ง D-112 ที่ถูกต้อง):
render เฟรมถูก ๆ จาก .blend ที่ lane save ไว้แล้ว (กล้อง --eye ตัวเดิมอยู่ในไฟล์)
ไม่ตัดสินอะไร ไม่แตะ .blend เดิม Cycles ยังเป็น engine ปิด gate เหมือนเดิม (R5 ไม่เปลี่ยน)

วัดจริงบนเครื่องนี้ (RTX 3060 Laptop 6GB, Blender 5.1.2, scene = room_bedroom_suite_eye_p2r55.blend 118MB, scale 50%):

| rung | wall-clock | หมายเหตุ |
|---|---|---|
| R5 quick (Cycles --quick) เดิม | ~68 วิ | ตัวเลขที่บันทึกไว้บนหน้านี้ (บรรทัด "quick look 68 วิ") |
| glance workbench one-shot | 6.61 วิ | render 3.25 วิ; ที่เหลือ = เปิด Blender + โหลด scene |
| glance eevee one-shot ครั้งแรกสุด | 26.95 วิ | 24.6 วิ เป็น shader compile ครั้งเดียว (cache ลงดิสก์) |
| glance eevee one-shot warm | 6.99 วิ | render 4.68 วิ |
| **--watch + --snap eevee (amortized)** | **2.6-2.7 วิ/เฟรม** | โหลด scene จ่ายครั้งเดียว — นี่คือ rung มาตรฐาน |
| --watch + --snap workbench | 0.71 วิ/เฟรม | เทาล้วน อ่าน material ไม่ออก — เก็บไว้เป็น flag |

Default = **eevee**: 2.7 วิ อยู่ในเป้า "ระดับวินาที" และเฟรมอ่านออกจริง (ไม้ตู้, ผนังระแนง,
sconce ติดไฟ, headboard เข้ม — ใกล้ Cycles) ขณะ workbench ให้ก้อนเทาแบน ๆ; เร็วกว่า
quick เดิม ~25 เท่า (amortized) / ~10 เท่า (one-shot) · EEVEE-headless risk ใน DR เป็นเรื่อง
EGL/Xvfb (Linux) — บนเครื่อง Windows นี้วัดแล้วทั้งสอง engine ทำงาน headless ได้จริง
(เฟรมเปิดดูยืนยันแล้ว ไม่ใช่จอดำ)

วิธีใช้ (LOOK-while-working ระหว่างรอบ):
```
python pipeline/scripts/glance.py pipeline/output/<room>.blend --watch   # เปิดค้างไว้ 1 terminal
python pipeline/scripts/glance.py pipeline/output/<room>.blend --snap   # ~2.7 วิ ได้เฟรมใหม่
python pipeline/scripts/glance.py pipeline/output/<room>.blend          # one-shot ~7 วิ ไม่ต้องมี watcher
```
(--mode=workbench, --scale=N, --cam=NAME, --stop มีครบ; test = test_glance.py, 24 ข้อ, ไม่ต้องมี Blender)

## Mock ladder ขนาดเตียง (คำถามเจ้าของ 2026-08-22: "ขยายอีกไม่ได้หรอ?")

MOCK_bedladder_{1_088cut,2_092,3_096,4_fullwidth}.png ใน pipeline/output — uniform scale
×1.054/×1.10/×1.15/×1.197 รอบ pivot หัวเตียงจริง (แก้จากคู่ A/B แรกที่ pivot คลาด 54มม.)
พร้อมเลื่อน nightstand+โคม (±dy 48/90/135/177) และ bench+หนังสือ+ผ้าพาด (dx 108/200/300/395
เข้าหากล้อง) รักษาระยะเดิมแบบที่ designer จริงทำเมื่อ upsize เตียง · ขั้น 4 = กว้างเต็มแบบ 7' พอดี
แต่ยาวเกินเส้น 6.5' ไป 395มม. — **ข้อจำกัดจริงคือสัดส่วนโมเดล ไม่ใช่สเกล**: แบบวาดเตียงกว้าง>ยาว
(2149×2000) ตัวที่ซื้อยาว>กว้าง (2000×1795 ที่ fit) uniform scale จึงตรงได้ทีละแกน · เป็น mock
ใน .blend memory เท่านั้น ไม่แตะ spec/gate; ถ้าเจ้าของชี้ขั้นไหน → ลง owner decision แล้ว
implement ผ่าน spec (fit override + placement re-derive) เป็นรอบจริง
