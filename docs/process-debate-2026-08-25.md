# PROCESS DEBATE — 2026-08-25 (three chairs, owner-triggered)

**TRIGGER (owner, verbatim):** *"ส่วนตัวผมมองว่า project นี้ทำงานได้ไม่มีประสิทธิภาพเลย มีของที่ผิดแบบโง่ ๆ หลายอย่าง เช่น โต๊ะหัวเตียงปัจจุบันก็ยังหันหน้าผิดทั้งที่ผมสั่งแก้แล้ว (ตอนนี้มันหันหน้าเข้ากำแพง), เสื้อผ้าที่แขวนในตู้ก็ยังซ้อน, ของที่วางในตู้ก็วางไม่เป็นธรรมชาติ — มีอีกเยอะ แต่ผมคนเดียวจะให้ชี้ข้อผิดพลาดมากขนาดนั้นก็ไม่ไหว"* — และคำสั่งให้ตั้งวง 3 ฝ่าย (interior designer / systems programmer / project director) debate กฎ เครื่องมือ และอนาคตของ project. เขาย้ำภายหลัง: **มุ่งแก้เชิงระบบระยะยาว ไม่ใช่เฉพาะหน้า**

**METHOD:** 3 position agents (ทุกตัวถูกบังคับเปิด `room_bedroom_suite_eye_p2r76.png`, `..._p2r75w.png` และ crop โต๊ะหัวเตียง 100% ก่อนออกความเห็น — R11 ใช้กับกรรมการด้วย) → cross-exam ไขว้ 3 → synthesis 1 → adversarial verify ข้อเสนอ top-3 อีก 3. รวม 10 agents / ~942K tokens / ~15 นาที / full render 0 รอบ. Read-only ตลอด (มี session คู่ขนานถือ uncommitted changes อยู่)

## สิ่งที่วงยืนยันจากพิกเซล (เอกฉันท์ ตรวจอิสระต่อคน)

- โต๊ะหัวเตียงทั้งสอง: หน้าที่หันหาห้องเป็นแผง framed เรียบ **ไม่มีมือจับ ไม่มีร่องลิ้นชักบนหน้าใดที่มองเห็น** — สอดคล้องกับคำพี่ว่าหน้าลิ้นชักหันเข้ากำแพง BF14. gate r74 อ้าง "มีลิ้นชัก+มือจับ" / gate r75 อ้าง "ยืนยันจาก crop" — **ทั้งคู่เท็จเทียบพิกเซล**
- ตู้: เสื้อดำเงา asset เดิม instance ซ้ำ ~10 ครั้ง แขวนทะลุกันเป็นก้อน specular เดียว; ผ้าพับ sage ตัวเดียวซ้ำหลายชั้น; ชั้นส่วนใหญ่ว่าง; shader อ่านเป็น vinyl ไม่ใช่ผ้า
- ทั้งเฟรมโทนเทา-taupe ตระกูลเดียว (เสียง #1 ของ C2 สองรอบติด — ACCEPT แล้ว route ทิ้งทั้งสองรอบ ยังไม่มี hue ลงเฟรม); เหยือกบังโคมขวา (accepted "micro-fix" ที่ r75) **ยังอยู่ใน p2r76**

## ชันสูตรกลไก (ยืนยันจาก source โดยทุกประธาน)

- `build_room.py:6631` pin convention `front=(sin rot, −cos rot)` → **rot=90 = หน้าหัน +X = เข้ากำแพง BF14 (x4803)**. spec note ของ r75 อ้างเอง "Front now faces -x" — คณิตของ convention ตัวเองบอกตรงข้าม = typed rot ผิดตั้งแต่พิมพ์
- `build_room.py:6673` `MODEL_FRONT_DEG.get(slug, -90.0)` **fail-open ทั้ง acquire path** — asset ซื้อทุกตัว (slug เป็น UUID ไม่มีทางอยู่ในตาราง) ได้ front "สมมุติ"; completeness assert คุมแค่ 9 slug CC0
- การปิดข้อ 1 ของ ORD-08-25b: builder พิมพ์ fix → เรนเดอร์ **quick** (ผิด R5 ถ้าใช้เป็นหลักฐาน) → อ่าน crop ของตัวเอง → เขียน "verified" → register พิมพ์ obeyed. ข้อเดียวจากห้าที่**ไม่มี obeyed_assert** คือข้อที่พัง
- C2 (11 ข้อ) + C3 (5 ข้อ) ดูเฟรมเดียวกันคืนเดียวกัน **เงียบทั้งคู่เรื่อง facing/ซ้อน** — ความเงียบถูกแปลงเป็น "ผ่านตากรรมการทั้งสองค่าย" (คลาส absence-as-confirmation ที่ R11 บันทึกไว้แล้วจาก r38)
- `facing_reader` มีอยู่แล้ว มี test เขียว มีตาราง `_FACING{90:E}` — **0 callers**. เครื่องที่ตอบคำถามคืนนี้ถูกสร้างเสร็จแล้วและไม่มีใครเรียก (หนึ่งใน 81/190 unreached)

## ROOT CAUSES (คลาส ไม่ใช่ instance)

1. **Self-judged closure** — คนแก้เป็นคนตรวจเป็นคนประกาศปิด ไม่มี rung คั่นระหว่าง "builder อ้างว่าปิด" กับ "พิมพ์เป็น fact"; สถิติ 30-50% ที่ R3 อ้างใช้กับการปิดงานเท่ากับที่ใช้กับการสร้าง
2. **Verification อ่าน code/spec ไม่อ่านพิกเซล** — obeyed_assert เป็น grep; ช่อง evidence ใน gate เขียนพิกเซลที่ไม่มีจริงได้โดยไม่มีใครเทียบ (บทเรียนก่อตั้ง R13 เกิดซ้ำหนึ่งชั้นบน: คราวนี้พิกเซลคือ field ที่ไม่มี checker อ่าน)
3. **Fail-open บน acquire path + orientation ถูกพิมพ์ทั้งที่ position ถูก derive** — scale มีกฎ assert ตอน ingest, orientation ไม่เคยมี; stop-loss ของ R9 ("แก้ตำแหน่งซ้ำสอง = ค่ากำลังถูกพิมพ์") ไม่เคยขยายไปถึง rot
4. **Absence อ่านเป็น confirmation** — critic ถูกถาม "เชื่อมั้ย" ไม่เคยถูกถาม "ชี้พิกเซลที่ทำให้ประโยคของพี่เป็นจริง"
5. **Queue ไร้ consumer ที่ระดับ governance** — cap ทะลุ 6.3x เป็น prose; 32 critic items/2 gates ACCEPT-then-route; asks 26 ค้าง (ตอบจริง 5/33) → **ตาพี่กลายเป็น detector เดียวที่เหลือ และล้า**
6. **ผลิตเครื่องมือเร็วกว่าบริโภค** — 190 ตัว / 81 unreached / reachability_check แดง 15 ข้ออยู่ที่จุด wire ที่ CLAUDE.md สั่งรันอยู่แล้ว; reflex ต่อ defect ใหม่คือสร้างตัวที่ 191

## VERDICT ต่อแผนของ OWNER

วินิจฉัยถูก (ทุก rung ที่ตัดสินกระบวนการคือ builder ตัดสินตัวเอง — 79/79 plan reviews self-signed, 0 catches) และ 3 บทบาทคือ shape ที่ถูก **แต่ห้ามเป็น standing ritual**: calendar-fired debate = self-review อันที่ 80 (คลาส 357/22, 21/2). มติหลังซักค้าน (director ถอน weekly floor เอง):
- **Designer seat = งานประจำใน delivery path** (sighted closure-verifier ทุกรอบ) ไม่ใช่ที่นั่งประชุม
- **วงเต็ม 3 ฝ่าย = event-triggered เท่านั้น**: พี่หักล้าง closure / มีการเสนอปิดเฟส / cap breach / R1 ซ้ำ — ไม่มีวันจุดไฟตามปฏิทิน
- เงื่อนไขผูกพัน: ทุกประธานเปิด render ก่อนพูด; designer ให้ verdict ก่อนอ่านคำอ้างของ builder (blind-to-claims, sighted-to-pixels); **ผลจบเป็น rows ใน register ที่มี checker อ่าน ไม่ใช่ไฟล์รายงาน**
- ราคา: หนึ่งวง < หนึ่งรอบ full render ที่เสียเปล่า; วงแรกนี้คุ้มแล้ว (จับ false evidence r74, จับ fail-open :6673, จับ typed-rot ที่ผิดจาก convention ตัวเอง — ไม่มี rung ไหนเคย file ทั้งสามข้อ)

## ข้อเสนอ (R13: PROPOSAL ทั้งหมด — ตาพี่คือ C4 และ final; เรียงตาม structural leverage ตามคำสั่งเขา)

| # | ข้อเสนอ | verify | amendment สำคัญจากฝ่ายค้าน |
|---|---|---|---|
| 1 | **Independent sighted closure verifier**: ข้อ visual ของพี่ flip เป็น obeyed ได้จากคำพี่ หรือจาก verdict ของ agent fresh-context ที่ได้แค่ประโยคพี่ verbatim + เฟรม full-fidelity แล้วต้องคืน annotated crop ลูกศรชี้พิกเซล หรือ NOT-VISIBLE; orders_check ปฏิเสธ obeyed ที่ไม่มี verdict file; block แค่สถานะ ไม่ block การส่งเฟรมถึงพี่ (R3 คงเดิม) | WEAKENED → adopt-amended | NOT-VISIBLE บนเรื่อง geometry/orientation ต้อง route ไป **measurement** (ตาบอก WHAT เครื่องบอก HOW MUCH — C2/C3 คืนนี้ก็พลาด); triage หักล้าง verdict ได้ด้วย measurement ที่ pass ถัดไปยืนยันในพิกเซลเท่านั้น; arrow-on-named-pixels บังคับเคร่ง (yes/no เปล่า = noise); archive prompt+verdict ใน bundle แบบ R7c |
| 2 | **Fail-closed front axis + facing เป็น relationship**: วัด MODEL_FRONT_DEG ตอน ingest ทุก asset (กฎ scale-assert ขยายไป orientation); `model_rot` RAISE เมื่อไม่มีแถว; เพิ่ม `face_away_from`/`face_toward` ใน placement.py; แปลง side_tables แล้ว **ลบ** typed rot (ไม่ zero — precedent x_nudge_mm); placement_check fail ทุก typed rot บน object ที่มี front จดทะเบียน | SURVIVES | **ทุก** asset ต้องมีแถว รวม "no meaningful front" อย่าง explicit (ห้าม allowlist "fronted kinds" — R9b); ตัวที่เปลี่ยนพิกเซลคือการแปลงเป็น face_away_from ต้องลงรอบเดียวกับ probe (probe เดี่ยว ๆ pixel-inert) |
| 3 | **Wire-or-delete 81 instruments** + กฎถาวร: instrument ใหม่ไม่ลงถ้าไม่ named consumer ใน commit เดียวกัน; reachability_check → blocking; facing_reader wire ก่อน (พิมพ์ spec-rot → world-front ต่อ object ลง render path) | (อยู่ใน dispute 2) | เริ่มด้วย triage วันเดียว default DELETE, exception ~5; wire-list ยาวกว่านั้น = priced ask |
| 4 | **Cap เป็น counter fail-closed**: เสนอ 12 รอบ / 24 full frames จาก 08-26 ใน rule_gate.check() (fail build เมื่อ breach); breach = R1 stop บังคับ + **real-client run (ORD-2026-08-22) เริ่มทันที** โดย DELIV-001 เหลือเป็น testbed ข้างใน; file เป็น decision-with-default แทน ASK-023 | — | คลาส R13 stop-loss counter; พี่ overrule ได้หนึ่งประโยค |
| 5 | **Drain queues ของพี่**: asks 26 → ≤6 (self-decide สิ่งที่ R3 มอบแล้ว + reverse_by; รวม 4 ask เงินเป็น procurement sheet เดียว 5 นาที); พิมพ์ critic-debt due-unpaid ข้างทุกเฟรมที่ส่ง | — | ตอบตรงประโยค "ผมคนเดียว...ไม่ไหว" — ลดภาระตาเขาโดยไม่ให้อ่านเอกสาร |
| 6 | **Execute ORD-2026-08-25c styling round** (narrative → vignette ref → shopping list → composition; ตู้ restyle ด้วย real closet reference, bay แต่งเต็ม varied + bay stacks/boxes/รองเท้า, ≤2 instance/id) — ปิดข้อ "ซ้อน/ไม่ธรรมชาติ" ของพี่ | WEAKENED → run-amended | อย่า bundle cloth-shader เข้ารอบนี้ (แยกไป P2r-5 — multi-item gate คือ shape ที่เพิ่งพัง); acceptance เพิ่ม pixel checks 2 ตัว: garment-overlap จาก id mask + instance-census จาก **built scene**; sourcing จริงผ่าน panel 1 asset → ถ้า catalogue ไม่พอ = **priced procurement ask** ไม่ใช่ declared gap เงียบ; gate พิมพ์ "landed" ห้าม "closed" |

**Closure grammar demotion (คร่อมทุกข้อ):** gate ห้ามพิมพ์ "ลงพิกเซลครบ"/"closed" กับ itemized visual order — พิมพ์ BUILT + evidence (refuse-by-name แบบเดียวกับ "พร้อมให้ตัดสิน"); prose evidence ไม่รับเป็นหลักฐานปิด (redline crop เท่านั้น); ทุก item ต้องมี obeyed_assert ของตัวเอง; source-grep assert refuse-by-name สำหรับ visual items; plan review ที่อ้างปิด owner-visible item ต้องมี countersignature file ที่ไม่ใช่ builder (= verdict file ของ verifier)

## DISPUTES ที่เหลือ (วิธี settle ระบุแล้ว)

1. **สี accent ลงเฟรมถัดไปเลย vs ตามลำดับ ORD-25c เคร่ง** → **owner call หนึ่งประโยค** (เขาเป็นคนสั่งลำดับ มีแต่เขาย่นได้)
2. **81 instruments: รายตัว vs triage วันเดียว default-delete** → measurement: รัน triage day ก่อน ความยาว wire-list จริงคือข้อมูลตัดสิน
3. **ระยะห่างจาก sellable (director 70% vs panel 25-40)** → measurement: รัน blind sighted-reader panel ใหม่บน p2r76/p2r75w เทียบ anchor pool เดิม; เลขใหม่แทนทั้งสองฝั่ง

## STATUS — อนุมัติแล้ว และลงมือคืนเดียวกัน

**OWNER APPROVED ทั้งหกข้อ คืน 2026-08-25: "ลุยเต็มที่ ผมอนุมัติทุกอย่าง"** พร้อมกำชับ
เป้าหมายเชิงระบบระยะยาว — บันทึกเป็นแถว `ORD-2026-08-25d-debate-proposals-approved`
(คำ verbatim ใน owner-order-2026-08-25d-debate-approved.md). สิ่งที่ลงคืนนั้น:

1. **Sighted closure verifier** — วิ่งจริงบนห้าข้อของ ORD-25b (verdict + arrowed crops ใน
   `04_visualization/closure-verdicts/ORD-2026-08-25b/`): พี่ถูก 4/5 (item5 พรม VISIBLE);
   item1 ตากรรมการอ่านแผงหลังเป็นหน้าลิ้นชัก → **front_probe หักล้างด้วยการวัด** (ตาบอก WHAT
   เครื่องบอก WHICH WAY — ยืนยัน amendment ของฝ่ายค้านคาที่). `orders_check` ตอนนี้ปฏิเสธ
   obeyed บนแถว visual ที่ไม่มี verdict file และปฏิเสธ "ลงพิกเซลครบ" ใน gate ใหม่ by name;
   negative control: แถว ORD-25b จริง flip กลับเป็น obeyed แล้วเครื่องปฏิเสธ (test พิสูจน์)
2. **Front law** — `front_probe.py` วัด Asta = −90 (หน้าเดียวที่มี pull), tub chair = **0**
   (เก้าอี้ vanity เรนเดอร์เบี้ยว 90° มาทุกเฟรมโดย fail-open เดิม — defect ตัวที่สองจากกลไกเดียว),
   bench = null; `model_rot` FAILS CLOSED; `facing_derive` + `placement.face_rot` แทน typed rot
   (ลบ ไม่ zero); rung ใหม่ใน `check_room` + FRONT lines พิมพ์ทุก build (facing_reader ได้
   consumer แรก); **p2r77 เรนเดอร์แล้ว มือจับหันออกหาห้องทั้งสองตัว** — สถานะ BUILT,
   OPEN-AWAITING-HIS-EYE
3. **Instrument triage** — 81 ตัว: **17 ALREADY-REACHED** (checker มองไม่เห็น subprocess) /
   **10 WIRE** / **55 DELETE** (docs/instrument-triage-2026-08-25.md); facing_reader wired,
   CLI-ONLY 5 ตัวประกาศแล้ว, baseline ตัด 5 แถวปิด; 4 code wires + 55 deletion = D-142 default
4. **Cap เป็นเครื่องจักร** — 89 rounds / 93 frames ใน curriculum-caps.json (spend คืนอนุมัติ
   77/69 + default +12/+24), `cap_check` BLOCK จริง; ทะลุ = R1 stop + real-client run เริ่ม;
   D-141 ล็อกด้วยคำพี่; **ORD-2026-07-28 (กฎแรกของเขา) flip เป็น obeyed หลัง 28 วัน**
5. **Queue drain** — asks 26 → **6** (ASK-023 answered ด้วยคำพี่; เงิน 4+1 ข้อรวมเป็น
   procurement-sheet-2026-08-26.md = ASK-034; 20 ข้อ withdrawn พร้อม default รายแถว; D-143)
6. **Styling round** — ยังเป็นแถว not-obeyed ของ ORD-25c; pane ที่ถืองานถูกพี่สั่ง "หยุด" ตรง ๆ
   — amendments ของฝ่ายค้านส่งถึง pane นั้นเป็นลายลักษณ์แล้ว

ผลดิบเต็มของวง: workflow `wf_69e03ae3-bfa` (ชั่วคราว — สาระสำคัญอยู่ในไฟล์นี้). Reversal:
รายข้อตาม reverse_by ในแถว D-141/D-142/D-143 + ORD-25d; หนึ่งประโยคจากภาพเสมอ
