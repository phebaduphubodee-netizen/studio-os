# DR: elevation/section conventions · hatch semantics · ASA cut-plane (DRW-4)

**Tier: REFERENCE** (research DR, ไม่ใช่ domain truth; ค่า statutory ไทยยังคงมาจาก
`knowledge/codes-th/` เท่านั้น) · Notebook `e1d577ea-f421-45cb-96ee-c59e7f5f027e`,
conversation `66e5cca2` turns 1+3 (turn 2 = BIM/Revit follow-up หลงประเด็น — ทิ้ง)
· fired 2026-08-11 by DRW-4's own trigger (DRW-2 opened) · raw Q&A:
`drw4-elevation-section-conventions-DR-2026-08-11.qa-history.json` (คู่กันใน commit เดียว)

**คุณภาพ source pool (ตรวจแล้ว, 25 sources):** ของจริงที่เกี่ยว = คู่มือ ASA
มาตรฐานการเขียนแบบก่อสร้าง พ.ศ. 2554 (โยธาไทย #18, TumCivil #19, PubHTML5 #22,
asa.or.th #15), รายการประกอบแบบ ASA 2552 (#24), hatch references (#5 #8 #12 #13)
· **ปนขยะ keyword-match "chapter 8": NASA, HHS, ICC, California math และ paper
ยา atrial fibrillation (#10)** — เพราะฉะนั้น claim ที่อ้างเลขบทต้องตรวจกับต้นฉบับ
ก่อนใช้เป็น authority เสมอ

## ชั้น 1 — ใช้ได้เลย (conventions ทั่วไป, หลาย source อิสระตรงกัน)

### สิ่งที่ ELEVATION ตรึงได้ที่ plan ตรึงไม่ได้ (ตรงกับ charter DRW-2)
- ทิศลายวีเนียร์ + ชนิด match (slip/book/running) + ตำแหน่ง grain break ข้าม joint
- แนว reveal/joint แนวนอน (หิน/ไม้/กระเบื้อง) ให้ตรงกับช่องเปิดและ datum millwork
- ระยะ drop ของ bulkhead / lighting valance / drapery pocket เทียบยอดตู้
- พิกัด z ของ switch/outlet/thermostat/HVAC grille เทียบ trim
→ ใช้เป็น checklist ว่า "ข้อมูลชั้นไหนที่เราไม่มีทางได้จากแผ่น plan" — ทุกตัวในลิสต์นี้
ที่งานเราต้องใช้ = declared assumption จนกว่าจะมี elevation จริง (ซึ่ง owner ยืนยันว่าไม่มี
— D-036 บริบท) หรือ owner เคาะจากภาพ

### Datum แนวตั้ง (วิธีคิดที่ DD/fabricator tier ควรใช้)
- FFL = ±0.00 ฐานทุกมิติแนวตั้ง · SSL แยกต่างหาก + tolerance ดูดซับความเพี้ยนหน้าแปลน
- Cumulative height callout (จาก FFL, สัญลักษณ์สามเหลี่ยม datum) สำหรับแนวจัดตำแหน่งวิกฤต ·
  chain dimension เฉพาะชิ้นส่วนต่อเนื่องใน carcass เดียว (กัน tolerance สะสม)
- h_clear = H_nominal − (t_finish + Δ_deflection + δ_scribe) · scribe zone ที่ฐานตู้
- ergonomic datums ที่หลาย source ให้ตรงกัน: base cabinet 850-900 / toe-kick 100-150
  ลึกเว้า 50-75 / splashback clearance 600 / wall cabinet ฐาน 1500 ลึก 300-350 /
  **bathroom vanity 800-850 ลึก 500-550** / bar 1050-1100
  → cross-check บันได DRW-2: vanity คู่ ensuite ของเรา 850 ✓ ใน band ·
  BF11 750 คือ makeup vanity นั่ง (คนละคลาส, owner-signed อยู่แล้ว) ✓ ·
  ความลึก vanity 500-550 ยัง**หนุนคำตอบ "ตามเส้นวาด ~500"** ของ Q1 ใน eye-pack ด้วย

### Hatch semantics (อุด gap ที่ vault ประกาศไว้ตรง ๆ)
- ANSI31/เส้นโค้ง = ลายไม้หน้าไม้ (section = โครง/แผ่นไม้; plan/elev = ทิศลายวีเนียร์)
- วงแหวนซ้อน/เฉียงถี่ = end grain · เฉียงสลับชั้น = plywood/blockboard (section เท่านั้น)
- NET/grid = กระเบื้อง/หิน (plan/elev = layout+grout+origin arrow) · AR-CONC = คอนกรีต
- คลื่น/ห่วงต่อเนื่อง = ฉนวน · เส้นคู่+fill = glass poche
- MDF/HMR = stipple ละเอียดหรือเฉียงคู่ถี่ แยกจากไม้จริง (กันสับ substrate โซนเปียก)

## ชั้น 2 — ต้องตรวจกับต้นฉบับ ASA 2554 ก่อนใช้เป็น authority (มี source จริงใน pool
## แต่ pool ปนขยะ "บท 8" และ vault เราจดไว้เองว่าบท 8 ยังไม่เคยสกัด)
- เส้นแนวตัด (เส้นแสดงแนวระนาบตัด): ต่อเนื่องบาง 0.18-0.25 + ปลายหนา 0.5-0.7 ชี้ทิศมอง
  หรือเส้นโซ่ 0.5 · แยกจาก grid โครงสร้าง (โซ่บาง 0.18)
- section bubble วงกลมผ่าครึ่ง Ø12-15: บน = ชื่อ section, ล่าง = แผ่นอ้างอิง
- ตาราง line weight ตาม scale (cut โครงสร้าง 0.5-0.6 @≥1:50 → 0.35-0.5 @≤1:100,
  millwork cut 0.35→0.25, background 0.18-0.25→0.13-0.18, hidden 0.25→0.18)
- ข้อบังคับเขตร้อน: air gap ≥15mm + vapor barrier ระหว่างคอนกรีตกับ MDF/HMR ·
  expansion joint ที่รอยต่อ millwork/ท้องพื้น
**คำเตือนชื่อ layer:** ตารางในคำตอบ DR แปะชื่อ layer สไตล์ AIA (`I-MILL-CUT` ฯลฯ)
ซึ่งไม่ใช่ vocabulary ของ ASA 2554 (vault: `thai-cad-layers-asa2554.md` ใช้ระบบ
pen/color ของ ASA เอง) — ส่วนนี้อ่านเป็น cross-mapping ที่ DR แต่งเอง ห้ามอ้างต่อ

## การใช้งานที่ผูกไว้แล้ว
- DRW-2 ladder (qa/sheet-recon.json `heights`): ชั้น 1 ยืนยัน vanity 850 ✓ และเพิ่มน้ำหนัก
  ให้คำตอบ "เส้นวาด ~500" ของ Q1 · เลขใน band เหล่านี้เป็น REFERENCE — ตัวตัดสินจริง
  ยังเป็น ladder (label > owner > band > declared assumption)
- DRW-5 (กฎ sheet-first): checklist "สิ่งที่ elevation ตรึง" = นิยามขอบเขตความรู้ที่แผ่น
  plan ให้ไม่ได้ → ใช้ตอนเขียนกฎ
- ปลายทาง distill ถาวร: `knowledge/classifications/plan-reading-conventions.md`
  (ส่วน elevation/section ที่มันประกาศเป็น gap) — ทำเมื่อ ASA ต้นฉบับถูกตรวจ (ชั้น 2)
- Notebook `e1d577ea` เก็บไว้ถาม follow-up ได้ · เข้าคิว prune เมื่อ distill ถาวรเสร็จ
