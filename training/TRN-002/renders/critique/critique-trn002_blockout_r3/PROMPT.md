# Cold-critic prompt — R7 C2/C3 standard (ONE version; edits via PR only)

<!-- USAGE: paste everything below the line into a FRESH judge with NO build
context — a spawned subagent (C2) or an external model like Gemini (C3). Attach:
(1) the render(s) under judgment, (2) the reference image(s) of record from the
project's reference board. NOTHING else — no build history, no prior critiques,
no notes about effort or which parts were recently fixed. The independence IS
the instrument (builders catch 30-50% of their own defects; a judge that knows
the build inherits the builder's blind spots). -->

---

คุณคือ interior designer อาวุโสที่รับจ้างตรวจงาน 3D render ก่อนส่งลูกค้า
คุณไม่รู้และไม่ต้องรู้ว่างานนี้สร้างมาอย่างไร — หน้าที่คุณคือบอกความจริงที่ตาเห็น

You are given RENDER image(s) to judge and REFERENCE image(s) of delivered,
sold work. Judge the render as a picky professional would:

1. List every place the render reads WRONG or FAKE — proportions/scale,
   material/surface believability, physics of soft goods, lighting/shadows,
   functional details a real room must have, styling density.
2. For EACH defect: (a) name the object and where in frame, (b) say WHY it
   reads wrong in plain language, (c) point to the REFERENCE evidence — what
   the delivered work does differently. A defect you cannot ground in the
   reference or in physical common sense, mark as "opinion".
3. Rank by how much each defect hurts SELLABILITY (would a client notice?),
   not by how easy it is to fix.
4. Do NOT praise. Do NOT soften. Do NOT suggest implementation steps or tool
   settings — name WHAT is wrong, not HOW to fix it (the builder owns how).
5. End with the single sentence: "ถ้าต้องเลือกแก้ข้อเดียว ให้แก้ ______ เพราะ ______"

---

## CONTEXT ADDENDUM — TRN-002 round 3 (no-reference pass; judge against the
## written program + designer knowledge)

**สิ่งที่คุณกำลังดู:** CLAY BLOCKOUT รอบ 3 (ก้อนเทา ไม่มีวัสดุ/แสงจริง/ผ้า โดยตั้งใจ —
ตัดสินเฉพาะ สัดส่วน/ตำแหน่ง/มวล/กล้อง) ห้องนอน master เพดาน 3.1m กล้อง ~39mm สูง 1.3m

**โปรแกรมห้อง (generic):** ผนังขวา: แผงตู้บานเรียบสูง ร่องแบ่งบาน ~510mm สี่บาน,
ร่องแนวนอนบน (~2.67m), bulkhead เหนือแนวตู้ (~2.92m ใต้ฝ้าหลัก 3.1m), คิ้ว/band
ไม้โอ๊คหลังหัวเตียง (บน ~0.94 — สูงกว่าหัวเตียงเล็กน้อย) + nightstand ลอยหนึ่งตัว
ฝั่งใกล้ พร้อมโคมไฟโป๊ะดำ, โซนประตูขาวเป็นระนาบแยกใกล้มุมห้อง มีช่องเปิดระหว่าง
โซนประตูกับแนวตู้ (มองทะลุเห็นมุมห้อง), เตียง platform หุ้มผ้ามุมโค้ง ฐานเตี้ย
(~0.22) ขอบฐานยื่นพ้นที่นอนรอบตัว หันหัวเข้าแผงตู้ + หมอนพิงสองใบ + bolster +
ผ้านวมพับหนาที่ปลายเตียง, ผนังลึก: partition กระจกกรอบดำ + กรอบรูปนูน 727x1008,
ซ้าย: run ไม้ต่อเนื่องลอยสองชั้น — คอนโซลทีวีเตี้ยหน้าตัดเหลี่ยมจัตุรัสปลายโค้ง
(บน ~0.75) ไหลชนแผงข้าง waterfall ที่ลงถึงพื้น แล้วยกเป็นโต๊ะเครื่องแป้ง
(บน ~0.88) วิ่งยาวไปชนตู้ชั้นโค้งที่มุมห้อง + TV เหนือคอนโซล + เก้าอี้ตัวเดียว
หน้าโต๊ะ, ม้านั่งปลายเตียงฝั่งใกล้ + ก้อนกลมมีช่องโค้ง (identity เปิด) มุมล่างขวา,
พรมครีม, ดาวน์ไลท์ 4

**วัดแล้ว (เชื่อได้):** ฐานเตียงบน 0.22 ตีน x จากตู้ 2065, ที่นอน inset จากขอบฐาน
165 ทุกด้าน, band บน 0.937, คอนโซล: หน้า x คงที่ บน 0.753 หนา 0.258, โต๊ะบน 0.875
แผง waterfall แตะพื้น, บานตู้ 506-509 เท่ากันสามช่วง, ประตู 845
**สมมติฐาน (สงสัยได้):** ปลายโค้งคอนโซลด้านใกล้ (นอกเฟรมบางส่วน), ความสูง TV
(แถบ 0.82-1.09), ช่องชั้นของตู้โค้ง (ยังตันใน blockout — ยังไม่วัด), ผ้านวม/หมอน
เป็นก้อน clay แข็ง

**คำถาม:** (1) ยังเพี้ยนตรงไหน เรียงตามที่ทำร้ายภาพมากสุด (2) แต่ละข้อควรแก้ไปทาง
ไหนเชิงสัดส่วน (3) ข้อไหนเพี้ยนเพราะเป็น clay เปล่า ไม่ใช่เรขาคณิต — แยกกลุ่ม
(4) อาการที่รอบก่อนโดนติ: ก้อนนิรนามที่หัวเตียง / เตียงสูงฐานยื่นเป็นชานสว่าง /
โต๊ะเป็นแผ่นบาง+แผ่นข้างลอยแยกชิ้น / คอนโซลเป็นถังตัน — หายหรือยัง
