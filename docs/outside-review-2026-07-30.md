# Outside review 2026-07-30 — ทำไมงานเพี้ยน และทางแก้ที่ยั่งยืน

> PROVENANCE: owner ask 2026-07-30 "สวมบทบาทเป็นคนนอกแล้ววิเคราะห์ว่าทำไมงานใน
> project นี้เพี้ยน และแนวทางแก้ไขที่ยั่งยืน (พิจารณาใช้ DR ได้)".
> Method: 14-agent workflow (3 repo auditors → 4 independent outsider lenses:
> stills-production veteran / lean-constraint theorist / business economist /
> agent-systems designer → semantic dedup → adversarial verify per claim, every
> citation re-checked against the live repo) + NLM DR notebook fd94d3c8 turns
> 6-9 (staged: `knowledge/_inbox/nlm-process-rules/drift-review-asks-2026-07-30.md`).
> Tier REFERENCE — this is decision context; no value here gates a deliverable.

## §0 คำตัดสินรวม (สามย่อหน้า)

งานนี้ไม่ได้เพี้ยนเพราะคนทำหละหลวม — วินัยรายรอบ (stop-loss ที่ fire จริง,
quick rung, งบที่รายงาน, budget ที่เหลือไม่ใช้) อยู่ในระดับที่ supervisor
จริงเรียกว่า exemplary. มันเพี้ยนเพราะ **กฎทั้งหมดคุมว่า "ทำยังไงใน lane"
แต่ไม่มีอะไรคุมว่า "lane ไหนควรได้แรง"**: เครื่องวัดของ studio เอง (bench
sheet แรก, `98edc17`) ตัดสินแล้วว่าเราแพ้งานส่งจริงที่ **light story ไม่ใช่
geometry** — แต่คำตัดสินนั้นไม่มีผลบังคับใดๆ ในขณะที่ prop พื้นหลังชิ้นเดียว
(ราวเสื้อ) ดูดไป ≥7 full-fidelity cycles ใน 3 วัน และ lane ที่ถูกจัดอันดับ
#1 (Gemini top-up, block ตั้งแต่ 07-11) ไม่ถูกแตะเลย 19 วัน.

ความเพี้ยนนี้ **co-authored** — ไม่ใช่ agent drift ล้วน: gate round-5
เสนอทางออก "จอด wardrobe ไปทำ light-story" เป็นคำแนะนำที่บันทึกไว้ (ข)+(ค)
แต่ owner เลือก (ก) — และ loop ปิดสองด้าน: owner ตัดสินเฉพาะ crop ที่ gate
โชว์ → gate โชว์เสื้อ → owner สั่งแก้เสื้อ → gate โชว์เสื้ออีก. วิศวกรที่ได้
เมนูที่มีปริศนากลไกอยู่บนนั้นจะเลือกปริศนาทุกครั้ง — และคนเขียนเมนูคือคนที่
อยู่ใน lane เสื้ออยู่แล้ว.

ความเสี่ยงที่ใหญ่ที่สุดตอนนี้ไม่ใช่คุณภาพ render แต่คือ **custody**: งาน
118 commits (07-06→07-30) อยู่บนดิสก์เดียว ใน OneDrive folder เดียว ไม่มีบน
remote ใดๆ. sync conflict หนึ่งครั้งลบเดือนกรกฎาทั้งเดือน.

## §1 Root causes (ranked, adversarially verified)

### 1. [CONFIRMED] ไม่มี regulator เหนือระดับ mechanism
R1 stop-loss ผูกกับ **mechanism** จึง reset ทุกครั้งที่ mechanism เปลี่ยนชื่อ
— และมันเปลี่ยน 6 ครั้งใน 3 วัน (procedural carve → silhouette invert →
reference law → cloth solver → shred instrument → hybrid rail; `36e8c49` →
`8889b61`) โดยไม่มีรอบไหนผิดกฎเลย. ราวเสื้อกิน g6→g10 + hybrid build ที่
timeout "อย่างถูกกติกา". Bench verdict (light story) ไม่เคยเป็นหัวข้อแรกของ
gate ใดหลัง `98edc17` — ตรวจแล้ว: ทุก commit หลังจากนั้นในทุก branch เป็นงาน
เสื้อทั้งหมด, ศูนย์ commit เป็น light story.
Evidence: `98edc17` body, `LOOK-round5-sim-stop-2026-07-30.md:31-49`,
CLAUDE.md §R1.

### 2. [CONFIRMED] งานที่ owner เท่านั้นทำได้ ไม่มีคิว ไม่มี aging ไม่มีการทวงซ้ำ
ทุกกฎที่ adopt มา bind ฝั่ง agent — ไม่มีข้อไหน bind owner. Gemini top-up ถูก
จัดอันดับ "the single highest-leverage unblock" ที่ director review 07-21
(`strategy.md:1907`) แล้ว**หายจาก strategy.md หลัง 07-22** (grep ยืนยัน: การ
กล่าวถึงสุดท้ายคือบรรทัด 2029; ที่โผล่หลังจากนั้นเป็น passive prose ใน LOOK
files ไม่ใช่การทวง action). Push decision ถูก flag 07-21 ว่า "an owner
decision" แล้วไม่เคยถูกถามซ้ำ ระหว่างที่ exposure โตจาก 92 → 118 commits.
Repo มีคิวสำหรับหนี้ฝั่ง agent (inbox_audit, nlm-queue) — ไม่มีคิวสำหรับ
action ฝั่ง owner แม้แต่ไฟล์เดียว.

### 3. [PLAUSIBLE — core จริง, specifics บางส่วนถูกหักล้าง] เกณฑ์รับงานไม่มีขอบเขต
"เหมือนของจริง" ไม่มีนิยาม falsifiable เขียนไว้ที่ไหนใน repo; รอบ 2-4 ไม่มี
รอบไหนที่ pass condition ถูกเขียน**ก่อน** build (รอบ 5d มีที่ระดับ instrument
— clothcheck threshold — แต่นั่น certify "ไม่ขาด" ไม่ใช่ "ขายได้"). แต่ละรอบ
รู้นิยาม done ของตัวเองจาก one-liner ของรอบ**ถัดไป**. ข้อแก้จาก verifier:
10-pair pilot **วิ่งแล้วจริง 07-15** — designer ตัดสินให้เราแพ้ทุกคู่ พร้อม
เหตุผล (แสงได้คำชม!) — สิ่งที่ค้างคือ hardened blind re-run ซึ่ง block อยู่บน
owner decision "WHO judges" (`qa/benchmark-sellability.md:141-143`) — กลับไป
เข้า cause #2 อีกดอก.

### 4. [CONFIRMED] Instrument factory คือ attractor state และระบบแก้ไขป้อนมัน
ทุก failure ถูกตอบด้วยกฎ/instrument ใหม่ที่สร้าง**หลัง** failure โดย
component เดียวกับที่สร้าง failure — ตรวจ adoption dates ครบ: R1-R6, R4b,
LOOK-law, clothcheck ทุกตัวเกิดหลังเหตุของตัวเอง ไม่มีตัวไหนเกิดก่อน. Test
count ratchet 2095→2125 ข้ามยุค polish โดย light lane ได้ศูนย์. แม้งบ owner
funded 2 full cycles ก็ถูกแปลงเป็น instrument โดย cycles ไม่ถูกใช้
(`48bc1cf`: "the two funded full-price cycles UNSPENT"). Project เอง
บันทึกไว้แล้วว่า "the class MUTATES — hunt the shape" — กรงโตขึ้นหนึ่งชั้น
ใต้จุดที่ failure ตัวถัดไปจะเกิดเสมอ.

### 5. [CONFIRMED — เลขแก้แล้ว] Ledger กับ safety net ผุใต้เท้างาน
**118 commits ไม่มีบน remote ใดๆ** (main..HEAD = 90, origin/main..main = 28;
tier1-self-doubt-suite ไม่มี upstream; backup ref ล่าสุด 07-03) ทั้งหมดอยู่ใน
OneDrive folder ที่การย้ายออกเป็น decision ค้างของ owner เอง. strategy.md
จบที่ 07-28 — rounds 4→5d (5 commits) ไม่ถูกบันทึกทั้งที่ CLAUDE.md สั่ง
"append learnings" ไว้เอง. Red tests โต 2→4 (`test_inbox_audit.py`, วัดสด).

### 6. [PLAUSIBLE] แรงงาน agent ราคา ฿0 ขณะที่คันโยกเงินจริงถูก freeze ทั้งคู่
ไม่มีกฎไหนตีราคา detail ต่อสัดส่วน pixel ในเฟรม หรือคำนวณ make-vs-buy —
ระบบจึงเท cycles "ฟรี" ไม่จำกัดเข้า background prop โดยผลรวมสุดท้ายคือ
"3 of 12 shirts sim-certified" — metric ที่ผู้ซื้อภาพ interior มองไม่เห็น.
Verifier ค้าน mechanism ครึ่งหนึ่ง: การ route เป็นการตัดสินใจของ owner ที่
gate โดยมีทางเลือกวางอยู่ตรงหน้าแล้ว — สอดคล้อง cause #1/#2 มากกว่าจะเป็น
เหตุอิสระ. (R6 grounding พูดถึงราคาเงินของ agent ไว้แล้ว แต่ไม่มีกฎ
operationalize.)

## §2 สิ่งที่ไม่ใช่ drift (เพื่อความยุติธรรมกับ record)

- รอบเสื้อ 4→5d เป็น**คำสั่ง owner ที่ถูก execute ตามสั่ง** — ทุกครั้งที่
  gate เสนอทางหยุด owner เลือกไปต่อ. นี่คือ command execution.
- R1 fire ถูกต้องที่ `5391929`; งบ 5b/5c ปิดโดยไม่แตะ full cycles; quick
  rungs ฆ่างานเสียก่อนจ่ายแพงจริงตามที่ R5 ออกแบบ.
- Instruments ที่สร้างมา refute สมมติฐานได้จริง 6 ข้อในราคา quick — เครื่องมือ
  ไม่ใช่ปัญหา; การที่เครื่องมือกลายเป็น deliverable แทน render คือปัญหา.

## §3 DR grounding (notebook fd94d3c8 turns 6-9, tier REFERENCE)

- **Turn 6 — Surrogation/Goodhart**: การป้องกันล่วงหน้า = sequential locks,
  capped revision budgets พร้อม disposition log, Definition of Done, WIP
  limits, Stage-Gate Go/Kill โดย gatekeeper อิสระ ("zombie projects survive
  on momentum"), multi-metric regularization.
- **Turn 7 — Blocked critical path**: ทุกสำนักสั่งตรงกัน **swarm the blocker
  + hold WIP** — ห้ามเติมเวลารอด้วยงานรองที่น่าสนใจ; อันตรายที่บันทึกไว้:
  งาน polish ระหว่างรอจะถูก **invalidate ทั้งก้อน**เมื่อ decision ต้นน้ำมาถึง
  — ตรงกับเราเป๊ะ: hybrid design กำหนดไว้เองแล้วว่า cloth micro-realism เป็น
  ของ lane Gemini (`5391929`) — วันที่ top-up จ่าย งานเสื้อส่วนหนึ่งจะถูกทับ.
- **Turn 8 — LOD hero-vs-background**: over-build sim rig ให้ background
  asset คือ named costly failure mode; "don't re-daily tiny changes";
  **diagnose the root note** — "make it feel heavier" คืออาการของ timing
  ไม่ใช่คำสั่งเพิ่มมวล. แปลตรงตัวกับเรา: "ยังไม่เหมือนของจริง" ×3 บนเสื้อ
  อาจเป็น**อาการของแสงแบน**ที่ bench ชี้อยู่แล้ว — เรา execute โน้ตแบบตรงตัว
  (geometry) แทนที่จะวินิจฉัยราก (light) = burn รอบบน layer ที่ผิดของ shot.
- **Turn 9 — Bounding "ไม่เหมือนจริง"**: references/styleframes ตกลง**ก่อน**
  ลงมือ; ข้อพิพาทตัดสินโดยเปิด reference ไม่ใช่เถียงกันด้วย prose; โน้ตที่ขัด
  stage ที่ approve แล้ว = formal **reopen พร้อมราคา cascading** ยื่นให้
  director ตัดสิน Go/Kill บนตัว revision เอง.

## §4 Fix design — 5 โครงสร้าง (แต่ละอันตอบ R6: ชื่อ class ที่ guard เดิมมองไม่เห็น)

**F1 — Custody วันนี้ (ทำก่อนทุกอย่าง; class: existential loss).**
`git push -u origin tier1-self-doubt-suite` — push คือ backup ไม่ใช่ merge;
topology decision ยังเป็นของ owner เหมือนเดิม. ตามด้วย check ถาวร: เตือนแดง
ตอนเปิด session เมื่อ HEAD นำหน้า remote ทุก ref >20 commits หรือ >48 ชม.
3/12 shirts คือสถานะที่กู้ได้ — เดือนกรกฎาที่หายไปกู้ไม่ได้.

**F2 — Owner-action queue + aging (class: owner-side deferral ที่กฎปัจจุบัน
แตะไม่ถึง).** ไฟล์ `docs/owner-actions.md` หนึ่งแถวต่อ action ที่ owner
เท่านั้นทำได้ (top-up 19 วัน · push · pilot "WHO judges" 15 วัน · OneDrive)
พร้อมวันเปิด, ราคา ฿, สิ่งที่มัน block. SessionStart hook พิมพ์แถวที่แก่กว่า
7 วันทุก session; gate artifact ต้องมี block "OWNER-OWED OUTSTANDING" เหนือ
เมนูตัวเลือก; item เกิน threshold แปลงร่างเป็น gate เดี่ยว: ตอบ หรือ defer
พร้อมวันที่ — ไม่มีการหายเงียบอีก. (Gemini top-up ตายเพราะ DECAY ไม่ใช่การ
ปฏิเสธ — grep พิสูจน์แล้ว.)

**F3 — Lane-allocation เหนือ mechanism (class: cross-lane misallocation ที่
R1-R6 พิสูจน์แล้วว่าไม่ cover).** สามชิ้นประกอบ:
(a) *Machine-written gate header* — script อ่าน bench sheet ล่าสุด + ledger
แล้ว stamp ทุก gate: "MEASURED GAP: <dimension> / รอบนี้ตอบมัน: YES-NO" และ
option (ก) ของทุกเมนูต้องเป็น measured-gap lane เสมอ (กลับหัว round-5 ที่
light เป็นแค่ fallback ของเสื้อ) — ตัดปัญหา "คนเขียนเมนูอยู่ใน lane เดิม"
เพราะเครื่องเขียนไม่ใช่คน;
(b) *Portfolio andon* — spend ledger คีย์ด้วย **SUBJECT** (wardrobe_rail,
light_story) ไม่ใช่ mechanism — เปลี่ยนชื่อกลไกแล้วตัวนับไม่ reset; subject
สะสม ≥4 full cycles → pre-build hook ปฏิเสธ full-fidelity จนกว่า gate มี
บรรทัด opportunity-cost ที่ owner acknowledge;
(c) *LOD ตาม pixel* — `id_mask.py` (มีแล้ว, 2.5s) วัดสัดส่วนเฟรมก่อนเปิดรอบ;
object <8% ของเฟรม hero ได้ cap 1 full cycle ต่อ owner verdict. ราวเสื้อจะ
ชน cap นี้ตั้งแต่รอบ 2 จาก 5.

**F4 — Acceptance contract ก่อน build (class: unbounded taste loop).** รอบ
ที่เกิดจาก taste verdict เปิดไม่ได้จนกว่า gate จะมี pass condition ที่
instrument ที่มีอยู่ execute ได้ เขียน**ก่อน** build: anchor-crop ID จาก pool
+ ≤3 properties ที่เช็คได้ + ระยะ crop ที่จะตัดสิน. ถึงเส้น = รอบ**ปิด**แม้
taste ยังคาใจ; ข้อติแกนใหม่ = formal reopen คิดราคาเข้า andon (DR turn 9).
R3 ไม่เสีย — owner ยังเป็นคนปิด แค่ปิดกับเส้นที่ตัวเอง pre-commit.

**F5 — ตีราคาเวลา agent เป็นบาท (class: ฿0 labor illusion).** SPEND block
ใน gate เพิ่มหน่วยเงิน: sessions×shadow-wage (owner ตั้งเลขครั้งเดียว) พิมพ์
ข้างราคาทางเลือกที่กำลังเลี่ยง (top-up ฿XXX, CC0 mesh ฿0). ไม่ re-propose
การซื้อ (คำสั่งเดิมคงอยู่) — แค่ให้ standing decision พกบิลปัจจุบันของมัน.
ตัวอย่างที่จะ fire ทันที: "garment lane ≈6 sessions ≈ ฿X,XXX vs top-up ฿XXX".

ลำดับ: F1 วันนี้ (keystroke เดียว) → F2+F3a (script เล็ก + template edit,
หนึ่ง session) → F3b/c + F4 + F5 (หนึ่ง session ต่อชิ้น, มี test pin ตามแบบ
guard เดิม). ทั้งชุดคือ ~5 กลไก ไม่ใช่กฎใหม่ 14 ข้อ — และไม่มีข้อไหน pin
รูปร่างของ failure ปัจจุบัน: ทุกตัวคีย์ด้วย instrument output / clock /
filesystem subject ซึ่ง mutate ตามไม่ได้.

## §5 Spend (R6)

- Workflow: 14 agents, 0 error, ~871k subagent tokens, ~17 นาที wall.
- NLM: 5 asks server-side (1 stranded duplicate — broken-pipe pitfall,
  บันทึกใน staging doc) + 1 history export; งบ ≤10 เคารพแล้ว.
- Renders/build cycles: 0. ไฟล์ที่เขียน: รายงานนี้ + staging 2 ไฟล์ใน
  `_inbox/nlm-process-rules/` (ทั้งหมดยังไม่ commit — ritual ของ owner).

---
พร้อมให้ตัดสิน — ยังไม่ verify: เลข shadow-wage ใน F5 (owner ตั้ง),
threshold 7 วัน/8%/4 cycles เป็น studio choice ไม่ใช่ค่าจาก DR,
และ F1 ต้องการ keystroke ของ owner ก่อนใคร.
