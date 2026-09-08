# training/ — TRN reproduction curriculum, ชั้น TEXT (tracked)

เกิด 2026-08-04 จาก outside-review ข้อ 2 + คำตัดสิน owner (คิว A): ประวัติ TRN
(สเปก / probe / metric / gate / critique / triage — งานที่กลั่นมาเป็น R7b/R8/R9)
เคยอยู่ใต้ `_private/` ทั้งเลน = diff ไม่ได้ bisect ไม่ได้ หายทั้งก้อนได้
ย้ายมาที่นี่ **เฉพาะชั้น text** — 272 ไฟล์ (TRN-001: 233, TRN-002: 39)
leak-scan ก่อน add: C-001 = 0, คำ address ไทย = 0

## กฎของ dir นี้

- **TEXT เท่านั้น** ชั้น pixel ทุกชิ้นอยู่ `_private/benchmark/reproduction/`
  ตามเดิม: render PNG/blend ของเรา, และเหนืออื่นใด **target/anchor ของเพื่อนสตูดิโอ
  ที่ห้ามออกจากเครื่องนี้** (R7b; `.gitignore` มี rule กันรูป/blend ใน training/ ไว้แล้ว)
- **`target.json` (pick mapping) ไม่ย้ายมาที่นี่เด็ดขาด** — มันผูกชื่อไฟล์ anchor pool
  กับชื่อโฟลเดอร์โปรเจกต์ของเพื่อนสตูดิโอ charter กำหนดให้อยู่ `_private` เท่านั้น
  (`qa/reproduction-curriculum.md`; ตัวเขียนคือ `pick_reproduction_target.py`)
- โครง dir สะท้อน `_private/benchmark/reproduction/<TRN-id>/` หนึ่งต่อหนึ่ง —
  ไฟล์ text ของ bundle ใดหาคู่ pixel ได้ที่ path เดียวกันฝั่ง `_private`
- **procedure ปัจจุบัน (จนกว่าเลน B/C จะ rewire ตอน TRN-002 ปิด):** เครื่องมือ
  (`critique_bundle.py`, `trn002_*.py`) ยังเขียนลง `_private` เหมือนเดิม —
  ปิดรอบแล้วย้ายชั้น text ของรอบนั้นมาที่นี่ (robocopy ตาม extension, /XF target.json)

## ที่มา

- triage: `docs/outside-review-2026-08-04-structure.md` (ข้อ 2 + คิว A)
- charter/ledger ของเลน: `qa/reproduction-curriculum.md`
