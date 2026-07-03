# Golden-set labeling — คู่มือเจ้าของ (M3.2 judge calibration)

## ทำไม
ก่อนให้ LLM judge (critique.py) มีสิทธิ์ gate งาน production ต้องพิสูจน์ว่ามัน
ให้คะแนน "ตรงกับตาดีไซเนอร์" — blueprint §9.4: Spearman ρ ≥ 0.8 (เรียงลำดับถูก)
และ Cohen's κ ≥ 0.8 (ตัดสิน SHIP/REWORK ตรง) ข้อมูลฝั่งมนุษย์คือไฟล์ที่คุณ
กำลังจะกรอกนี่แหละ

## กติกาสำคัญ (BLIND)
- **ห้ามเปิด `machine-scores.json` ก่อนกรอกเสร็จ** — ถ้าเห็นคะแนนเครื่องก่อน
  ค่า ρ/κ จะเชื่อไม่ได้ทั้งชุด (anchoring)
- ลำดับ GS-ID สุ่มแบบ deterministic แล้ว (crc32) — ไม่เรียงตามคุณภาพ/ห้อง/เวอร์ชัน
- ให้คะแนนจาก "ตาดีไซเนอร์มืออาชีพ" ไม่ใช่จากความรู้ว่าไฟล์ไหนมาจากรอบไหน

## ขั้นตอน
1. `copy labels.template.json labels.json` (ในโฟลเดอร์นี้)
2. เปิดภาพทีละใบจาก `assets/qa/golden-set/GS-XX.png` (26 ใบ) — หรือใช้
   `qa/golden-set/labeler.html` (เปิดในเบราว์เซอร์) ที่โชว์ทุกใบ + ปุ่มให้คะแนน
   แล้ว export `labels.json` ให้เลย ไม่ต้องแก้ JSON มือ
3. กรอกใน `labels.json` ต่อภาพ (**ทั้ง overall_0_5 และ verdict บังคับ** — ถ้ากรอก
   คะแนนแต่ลืม verdict, `judge_calibrate.py` จะ **หยุดพร้อมบอกรายชื่อ ID** ไม่ยอม
   คำนวณ เพราะ verdict ว่างจะถูกนับเป็น REWORK เงียบ ๆ แล้วบิดค่า κ):
   - `overall_0_5`: 0–5 ขั้นละ 0.5 (5 = ลงนิตยสาร/ส่งลูกค้าได้ทันที,
     4 = ผ่านมาตรฐานส่งงาน, 3 = ต้องแก้, ≤2 = ใช้ไม่ได้)
   - `verdict`: `"SHIP"` หรือ `"REWORK"` (คำถามเดียว: ส่งให้ลูกค้าที่จ่ายเงินได้ไหม).
     κ วัดว่า gate อัตโนมัติ (คะแนนเฉลี่ย ≥ 4) ตรงกับการตัดสิน SHIP ของคุณไหม —
     ต้องมีทั้งคู่ทุกภาพ
   - `note`: (ไม่บังคับ) defect ที่เห็น — มีค่ามากตอนวิเคราะห์ per-dimension
4. รัน `python pipeline/scripts/judge_calibrate.py`
   → รายงานลง `qa/reports/judge-calibration-<วันที่>.md` พร้อมคำตัดสิน M3.2

## หลังกรอกเสร็จ
- commit `labels.json` (ground truth ถาวรของสตูดิโอ)
- ถ้า FAIL: judge ถือว่า "เทสต์พัง" — ห้ามใช้ gate จนกว่าจะแก้ (rubric/model/
  multi-roll policy) แล้ว calibrate ใหม่ — ดู REVALIDATION.md
