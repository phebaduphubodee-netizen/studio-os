# DRW-2 eye-pack — 2026-08-11

สามคำถามที่เครื่องตัดสินแทนไม่ได้ ตอบได้ด้วยการชี้/ประโยคเดียว **ไม่มีข้อไหน block เลน** —
ทุกข้อมีค่า default ที่เดินอยู่แล้ว และแก้เป็น edit แถวเดียวใน spec ทั้งหมด

| # | ภาพ | คำถาม | ค่าที่เดินอยู่ | ถ้าเปลี่ยน |
|---|-----|-------|----------------|-----------|
| Q1 | q1_depth_drawn_vs_label.png | ความลึก BF11/BF09-2 ตามเส้นวาด (~500) หรือตามป้าย (600)? | เส้นวาด (precedent element 2/7; spec จดเป็น "designer question" ไว้เอง) | แก้ `w` สองแถวใน canonical spec |
| Q2 | q2_tv_console_vs_bookshelf.png | ผนังตะวันตก: คงชั้นหนังสือ 1.8ม. หรือกลับเป็นตู้ทีวีเตี้ยตามแบบ? | ชั้นหนังสือ ("ex-TV", ตัดสินตอน element 2) | แก้ builtin แถวเดียว |
| Q3 | q3_bf10_junction_slit.png | ปิดช่อง ~152มม. ระหว่าง BF10 กับ BF09-2 ตามที่แบบวาดปิด? | ยังเปิดอยู่ (watch-item #9c ของ element 7) | ยืด BF10 ตะวันออก ~152 ใน spec |

ที่มา: โปรแกรม DRW (qa/sheet-recon.json + qa/deliverable-plan.json เฟส DRW) ·
แบบของ record = snapshot ใน 00_intake (D-036) · รหัส BF = declared guess ยกเว้นที่เคาะแล้ว (D-037)

หมายเหตุคืนนี้: recon board เต็ม **19 วาด / 19 matched / 0 UNRESOLVED** — สามตัวที่เคยถูกสงสัยว่า
build เพี้ยนจากแบบ (BF11, BF09-2, BF09-3) วัด vector แล้ว **build ตรง ink ทั้งสามตัว**;
ตัวที่เพี้ยนคือ scene-graph เก่าของเลน floor2 (วางตามป้ายแทน strokes)
