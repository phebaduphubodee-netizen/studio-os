# TRN-001 / element 1: camera + blockout — 2026-07-31 — gate #1

**ภาพ:** ก่อน `_private/benchmark/reproduction/TRN-001/renders/trn001_blockout_smoke_ql.png` (สภาพก่อน solve) | หลัง `_private/benchmark/reproduction/TRN-001/look/trn001_blend_v003f.png` (50/50 blend บน target) + คู่เต็ม `look/trn001_pair_v003f.png` + edge `look/trn001_edges_v003f.png` + full frame `renders/trn001_blockout_v003f.png`
(look_bench ไม่ใช้ใน lane นี้ — target คือกรรมการโดยตรงตาม charter; quarantine 91 siblings wired แล้วกันรั่วไป lane อื่น)

1. **แก้อะไร:** ตรึงกล้อง + โครง massing ของห้องพระให้นั่งใต้กระดูกของงานส่งจริง — ด้วย VP solve (focal 38.9mm / horizon กลางเฟรม / yaw −20.55°) + least-squares หา station จาก landmark ที่ probe ด้วยเครื่อง 20 จุด แล้วอ่าน residual pattern กลับเป็น mm จนได้ spec ที่ไม่สมมาตรตามของจริง (plinth วิ่งใต้ tower ซ้ายถึงขอบนอก unit / tower ขวายืนพื้น)
2. **ผมตัดสินว่า:** ผ่านระดับ rung — **mean 10.6px / median 7.9px / max 25.4px บนเฟรม 2048** (0.5% ของเฟรม; ตัว max คือปลายโค้ง plinth ที่ probe เองก็ flag ว่าอ่านยากสุด) และ C2 ตัวที่สองยืนยันเป็นลายลักษณ์ว่า "ปัญหาไม่ได้อยู่ที่กล้อง" — ทางที่ทิ้ง: ไม่ solve dims ใน optimizer (คน adjust จาก residual ทีละชิ้นแทน กัน solver แต่งตัวเลข mm มั่ว)
3. **ไม่แน่ใจ:** (a) สัดส่วน**แท่นประธาน vs กล่องข้าง** ตอนนี้ตั้งจากเสียงข้างมาก 2:1 (measurer B + critic ค้าน measurer A) — องค์พระจริงจะเป็นตัวชี้ขาดในรอบ styling ถ้าตาคุณเห็นว่ากล่องกลางยังกว้าง/แคบไป บอกได้เลย; (b) สเกลสัมบูรณ์ทั้งฉากพิงสมมติฐานฝ้า 2700 (ภาพเดี่ยวหาสเกลจริงไม่ได้) — ทุกสัดส่วนภายในตรง target แต่ถ้าบ้านจริงฝ้า 2.6 ทุก mm หด ~4%

**C2 cold critic (R7):** รอบแรก (เฟรม v001f): critic จับ "ก้อนตันแปลกปลอมบังแท่น" ที่ builder อธิบายแทนมันไปแล้วสองรอบ → instrument ID-mask ชี้ตัว = **default cube ของ --factory-startup** ที่หลุดเข้าฉากทุกเฟรม (บทเรียนใหม่ทั้งคลาส: วัตถุแปลกปลอมมองไม่เห็นด้วยเครื่องมือฝั่ง spec เพราะ projection เช็คเฉพาะจุดที่ spec รู้จัก) → ล้าง scene ก่อน build เสมอ + idmask เป็น rung ถาวร
รอบสอง (เฟรม v002f สะอาด): 7 ข้อ → ✓รับ 4: หินอ่อนห้ามโชว์ขอบล่าง (จม bot_z→150), กล่องกลางแคบลง 980→780, pedestal +40, header ลึก 400→360 ให้ตระกูลระนาบแบนตาม reference → แก้แล้วใน v003f · ✓รับเข้า**เลนรอบ 2 (joinery)**: ช่องชั้น 5 ช่องของ towers + toe base ตู้ขวา + รอยต่อ 3 แผง header + เส้นทองเหลือง + ร่องลิ้นชัก/toe recess ของ plinth · ✗หักล้าง 2 ด้วยการวัด: "จังหวะชั้นเพี้ยน" (machine probe ปัก plinth-top 190 / step-top 420 ที่ residual ≤10px — probe ชนะการกะด้วยตาบน crop คนละสเกล) และ "เฟรมบนขวาตึงไป" (มุม header วัดจริง v130 / model ฉาย 125 — ตรง target ใน 5px)
**C3:** not fired — minor gate (rung แรกของ curriculum lane; C3 เก็บไว้ gate ปิด work ทั้งชิ้น)

**Spend:** full 2048 จำนวน 3 เฟรม (v001f เสีย 1 เฟรมให้ default cube — จ่ายค่าเรียน, v002f, v003f) + quick 4 (smoke/v001/v002/idmask) / สะสม lane = เท่ากัน · solve 5 รอบฟรี (pure math) · fan-out 5 agents ~604k tokens + critic 2 ตัว ~168k
**Reversible:** yes — spec JSON + solved camera ทั้งหมดเป็นไฟล์ versioned; ลบ trn001_* ก็กลับสภาพเดิม

**ขอ verdict:** ไปต่อ (รอบ 2 joinery) / แก้ตามนี้ / ฆ่าทิ้ง — พร้อมให้ตัดสิน
