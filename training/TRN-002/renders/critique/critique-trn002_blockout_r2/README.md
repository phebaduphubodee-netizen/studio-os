# ส่งให้ Gemini ตัดสินในฐานะ designer — R7b

**ทำทุกครั้งหลัง render ออก** (คำสั่งเจ้าของ 2026-08-02)

## วิธีใช้ (2 นาที)

1. เปิด Gemini
2. แนบไฟล์ **`trn002_blockout_r2.png`** — ไฟล์เดียวเท่านั้น
3. วาง **ทุกบรรทัดใน `PROMPT.md`** (ใต้เส้นคั่น) เป็นข้อความ
4. เอาคำตอบกลับมาวางในแชท

## สิ่งที่ห้ามส่งเด็ดขาด

**ภาพ target และคลัง anchor ห้ามออกจากเครื่องนี้** — มันคืองานลูกค้าที่สตูดิโออื่น
ส่งมอบจริง การส่งออกไปคือทั้งการรั่วข้อมูลลูกค้า *และ* การทำให้กรรมการเห็นเฉลย
สคริปต์นี้ปฏิเสธไฟล์พวกนั้นให้อัตโนมัติแล้ว แต่อย่าแนบเองด้วยมือ

ห้ามพิมพ์ชื่อลูกค้า ที่อยู่ ขนาดห้อง หรือ path ของไฟล์ไปกับภาพ

## สิ่งที่จะเกิดขึ้นกับคำตอบ

ทุกข้อที่ Gemini ตอบมาจะได้ **triage เป็นลายลักษณ์อักษร** ตาม R7 —
รับแล้วเข้าเลนไหน หรือตีตกพร้อม **ตัวเลขที่วัดได้** ไม่มีการตีตกด้วยรสนิยม

และเกณฑ์การชั่งน้ำหนัก (R7b): **ตาบอกว่า "อะไร" ผิด เครื่องมือบอกว่า "เท่าไร"
และ "ปุ่มไหน"** — ถ้าสองอย่างขัดกันเรื่อง *มีปัญหาหรือไม่* ให้ตาชนะ

## หมายเหตุรอบนี้

TRN-002 round 2 CLAY BLOCKOUT - right-wall assembly re-solved (ward x=-1290, bulkhead 2920, door plane -976, bed anchored); judge proportions/placement
## PENDING ASK — C2 Claude-Cowork (R7c)
Round-2 render awaits the Cowork cold-critic pass: attach trn002_blockout_r2.png
+ PROMPT.md in the Cowork chat (judge must not open target/anchors/history).
Archive the answer here as ANSWER_claude-cowork.md. Recorded 2026-08-04; C3 ran
without waiting per R7c fallback rule.
