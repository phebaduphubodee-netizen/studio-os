# Outside Review — โครงสร้าง repo STUDIO-OS (2026-08-04)

- ผู้วิจารณ์: Claude (Cowork session — คนละ context กับ builder, มุมมองคนนอก)
- ขอบเขต: โครงสร้างไฟล์/git/การไหลของ state เท่านั้น ไม่ตัดสินคุณภาพงานออกแบบ
- วิธีอ่าน: ทุกข้อมีหลักฐานเป็น path/ตัวเลขที่วัดจริงวันนี้ ข้อไหนเป็นความเห็นเชิงรสนิยมติดป้าย **[opinion]**
- สิ่งที่ไม่ได้เปิด: เนื้อหาใน `clients/`, ภาพ target/anchor ทั้งหมด, เนื้อไฟล์ความรู้เชิงลึก

---

## สิ่งที่แข็งแรง (ไม่ต้องแตะ)

ระบบ contract ต่อ stage + gate ต่อการตัดสิน, hooks ที่เป็น fail-closed จริง
(`.claude/hooks/`: guard_bash / guard_egress / guard_paths / leak_patterns +
`logs/write-audit.log`), `.gitignore` ที่เขียนเหตุผลกำกับทุกก้อน (raw-local intake,
warehouse ตาม licence text, embed-bank), กฎทุกข้อมี provenance เป็น owner order
พร้อมวันที่และ quote, commit message เล่าเหตุและบทเรียน (สิบสอง commit ล่าสุดอ่านเป็น
case log ได้), vault + `_inbox` + DISTILLATION-LEDGER แยกชั้นความเชื่อถือของความรู้
ชัดเจน นี่คือโครงกระดูกที่ดีกว่าสตูดิโอจริงจำนวนมาก

---

## ข้อวิจารณ์ เรียงตามความเสียหาย

### 1. State machine ที่ประกาศไว้ กับ state จริง อยู่คนละที่กัน

กฎบอกว่า "stage outputs are files in the stage directory" และ render ต้องชื่อ
`R_PRJ###_Room_CamNN_vNN` วัดจริง: `pipeline/output/` มี PNG **154 ไฟล์ ตรง
convention 0 ไฟล์** (684 MB) ขณะที่ `projects/.../04_visualization/` เก็บแต่เอกสาร
LOOK ส่วน render ตัวจริงอยู่ใน dir ที่ **gitignore ทั้งก้อน** (`pipeline/output/`)
และ `output/` ที่ root ว่างเปล่า ผลคือ "ไฟล์ของ record" ของแต่ละ round ไม่มีอยู่ใน
โครงสร้างที่ประกาศ — clone ใหม่ตอบไม่ได้ว่าเฟรมไหนปิด round ไหน นี่คือ defect
ตระกูลเดียวกับที่ R9b เขียนเอง: *"the file that renders is not automatically the
file of record"* — คราวนี้เกิดกับทั้ง pipeline ไม่ใช่แค่ Blender scene

### 2. เลนที่ active ที่สุดของสตูดิโอ อยู่นอก version control ทั้งเลน

`_private/` ถูก ignore ทั้งก้อน — ถูกต้องสำหรับ pixel ของ target/anchor/ลูกค้า
แต่วันนี้มันกลายเป็นบ้านของ TRN-001/TRN-002 ซึ่งคืองานหลักของสตูดิโอ: วัดได้
**683 ไฟล์ text** (md/json/py) ปนกับ 2,333 binaries ใน `_private/` ประวัติ 20 รอบ
ของ TRN-001 — สเปก, critique, triage, บทเรียนที่กลั่นเป็น R7b/R8/R9 — **diff
ไม่ได้ bisect ไม่ได้ และหายทั้งก้อนถ้าดิสก์/OneDrive มีปัญหา** ที่ย้อนแย้งที่สุด:
commit ล่าสุดสิบสอง commit เล่าเรื่อง TRN ทั้งนั้น แต่ artifact ที่มันเล่าถึง git
มองไม่เห็นสักไฟล์ — ประวัติศาสตร์ถูกเขียนไว้ในหัว commit ของไฟล์ที่ไม่มีอยู่ใน repo

ทางแก้ที่ privacy ไม่แตก: เปลี่ยน ignore จากทั้ง dir เป็น **ignore เฉพาะชั้น
binary/pixel** (`_private/**/*.png|jpg|blend|npz` + target/anchor path) แล้ว track
text — โดยให้ `leak_patterns.py` เป็นด่านตามเดิม หรือย้าย text ของ TRN ออกมาเป็น
`training/TRN-00N/` แบบ tracked ไปเลย (ชื่อ generic แล้ว: "TRN-002 blockout" ไม่มี
ตัวระบุลูกค้า)

### 3. Version-soup ใน pipeline/output — กับดัก R4 ที่สร้างเอง

154 render ตั้งชื่อแบบ ad-hoc ไล่ suffix: `fx1..fx9`, `g2..g10`, `lb/lc/ld`,
`weaveLOUD/weaveFINAL/weaveREVIEWED`, `doorfix/doorfix2`, บวก `.blend` คู่ทุกไฟล์
และ `.blend1` backup อัตโนมัติปนอยู่ ไม่มี manifest บอกว่าไฟล์ไหนเป็น frame of
record ของ round ไหน (batch-manifest.md อยู่ใน 04_visualization แต่ไม่ align กับ
ไฟล์จริง) โครงแบบนี้เชิญชวนให้ทำสิ่งที่ R4 ห้ามพอดี — เทียบกับเฟรมตัวเองรุ่นก่อน
เพราะมันวางเรียงอยู่ตรงหน้า ขณะที่ anchor pool ต้องเปิดอีก dir เสมอ
**[opinion ส่วนทางแก้]**: subdir ต่อ round + rename ผ่าน script ตาม convention
เดิมที่ประกาศแล้วแต่ไม่เคยถูกใช้ และเพิ่ม `*.blend1` เข้า gitignore/สคริปต์กวาด

### 4. pipeline/scripts — 199 ไฟล์ / 81,000 บรรทัด ใน namespace เดียวแบน ๆ

โมดูล build กลาง (millwork, softgoods, curtains), กติกา/guard (placement,
look_bench), เลนเฉพาะกิจ (trn001_* สิบไฟล์, trn002_* สี่ไฟล์), และ test ~90 ไฟล์
อยู่ปนกันหมด ยิ่งกว่านั้น code เฉพาะโปรเจกต์มีสองบ้าน (gen_floor2*.py อยู่ใน
`03_layout/` ของโปรเจกต์ ขณะ trn* อยู่ใน pipeline/scripts) — เส้นแบ่ง "ของกลาง vs
ของเลน" ไม่มีนิยาม R8b เคยวัดแล้วว่ามี 2,177 บรรทัดที่ซ้ำกับของที่ Blender มีให้
**[opinion]**: แตกเป็น `core/ lanes/ trn/ tests/` — แต่อย่าทำกลางรอบ ทำตอน
TRN-002 ปิด เพราะ import path จะขยับทั้งกระดาน

### 5. สอง copy ของความจริงเดียว — และมัน diverge แล้วจริง ๆ

`floor2-walls-mm.json` มีสามชุด: root กับ v5 md5 ตรงกัน (`6899e281`) แต่ **v4 เป็น
คนละเนื้อหา** (`550225f7`) โดยไม่มีอะไรบอกว่าอันไหนคือความจริงปัจจุบัน นี่คือกฎ
R9 ฉบับ generalize: **ไฟล์ที่ถูก copy คือ coordinate ที่ถูก type** — มันจะถูกต้อง
ณ วันที่ copy แล้วเงียบ ๆ ผิดตั้งแต่การแก้ครั้งแรกที่ตามไปไม่ครบ ทางแก้: ชุดเดียว
เป็น source + ชุด generate ต้องมี provenance header ว่ามาจากไหน generate เมื่อไร

### 6. CLAUDE.md โตแบบ append-only — 23.5KB และยังไม่มีเพดาน

ทุก session จ่ายต้นทุนอ่านทั้งไฟล์ก่อนเริ่มงาน และกฎใหม่ทุกข้อมาพร้อมเรียงความ
เต็มรูป ผมเข้าใจ trade-off นี้ดี — R4b พิสูจน์มาแล้วว่ากฎที่อยู่นอกสายตาไม่ถูกตาม
ดังนั้น **ข้อเสนอไม่ใช่ "ย้ายกฎออก"** แต่คือแยกชั้น: คงไว้ใน CLAUDE.md เฉพาะ
ตัวบังคับ (กฎ + test + stop-loss, 3-5 บรรทัดต่อข้อ) แล้วย้ายคดีตัวอย่าง/หลักฐาน
ไป `docs/case-law.md` อ้างด้วยหมายเลข — ผลบังคับอยู่หน้า เหตุผลอยู่หลัง pointer
**[opinion — owner ตัดสิน เพราะขัดกับสัญชาตญาณที่พิสูจน์แล้วว่า rules-in-face
ได้ผล]**

### 7. PLAN-*.md ห้าไฟล์ 223KB ค้างที่ root ตั้งแต่ ~7 ก.ค.

`PLAN-confirmed-kind-identity-ledger` / `f1-size-prior` / `f4-wall-aware` /
`gate-hardening` / `swing-door-arc` — ไม่มี disposition ว่า adopted / superseded /
rejected root ของ repo คือหน้าบ้านที่ทุก session เห็นก่อน ควรย้ายเข้า
`docs/plans/` พร้อมสถานะบรรทัดแรกของแต่ละไฟล์

### 8. ทั้ง repo อยู่ใต้ OneDrive — และวันนี้มันกัดจริงต่อหน้าผม

git + LFS + render 684MB ที่ถูก rewrite ทุกคืน + `.blend` 10MB ต่อไฟล์ อยู่ใน
โฟลเดอร์ที่ OneDrive sync ทุก write = churn มหาศาล และ semantics การลบ/lock บน
mount ทำให้เกิดเหตุจริงวันนี้: `git status` ทิ้ง `.git/index.lock` ค้าง (ผมย้ายไป
`_to_delete/` แล้ว — **ลบโฟลเดอร์นั้นทิ้งได้เลย**) ทางเลือกเรียงตามแรง:
(ก) ย้าย repo ออกจาก OneDrive แล้วให้ git+GitHub เป็น backup — ซึ่งจะเป็น backup
จริงก็ต่อเมื่อข้อ 2 ถูกแก้ (ข) อย่างน้อยที่สุด exclude `pipeline/output/` และ
`_private/**/renders/` จากการ sync

### 9. เส้นเลือดข้าม repo เป็น absolute path

CLAUDE.md ชี้ `C:/Users/teza_/OneDrive/Desktop/BRAINDEAD/scripts/notebooklm_dr.py`
— เครื่องอื่น, clone อื่น, หรือวันที่ BRAINDEAD ย้ายบ้าน = เลน DR ตายเงียบ
ทางแก้: vendor สคริปต์เข้า `tools/` หรือประกาศเป็น env var ใน `.env.example`

### 10. โปรเจกต์และโฟลเดอร์ที่จบหน้าที่แล้วแต่ยังนั่งอยู่

- `projects/PRJ-2026-001_test-run/` — มีแต่ `_contract.md` เปล่าใน 01-04:
  ถ้าจบหน้าที่ test แล้ว archive หรือยกเป็น golden example ของ scaffold
- `run_altcwd/` ที่ root — ชื่อสารภาพว่าเกิดจากรัน cwd ผิด (pilot-blind, 14 ก.ค.)
  ของจริงควรอยู่ `qa/` หรือ `_private/` แล้วลบทิ้ง
- `output/` root ว่างเปล่า — ไม่มีใครใช้ ลบหรือประกาศเจ้าของ
- usage counters สามไฟล์ (`.gemini/.openai/.perplexity_usage.json`) — ignored
  แล้วก็จริง แต่ root ไม่ใช่ที่ของ state ไฟล์ **[opinion]**: ย้ายเข้า `logs/`

### 11. Inbox ค้างนานสุด ~1 เดือน

เก่าสุด `nlm-ergonomics-2026-07-03.md` (3 ก.ค.) — มี DISTILLATION-LEDGER และ
`scripts/inbox_audit.py` อยู่แล้ว แค่ต้องมีจังหวะรันตามรอบ (นี่คืองานที่เหมาะกับ
scheduled task ฝั่ง Cowork ถ้าต้องการ)

### สิ่งที่ตรวจแล้ว "ผ่าน" (บันทึกไว้กันเข้าใจผิด)

`.env` ไม่ถูก track (มีแต่ `.env.example`), remote เป็น GitHub ปกติ, raw client
intake ถูก ignore ตาม pattern, warehouse ถูก ignore ด้วยเหตุผล licence ที่เขียน
กำกับไว้, commit cadence สม่ำเสมอ (ล่าสุด 3 ส.ค. — งาน 4 ส.ค. ยังไม่ commit เป็น
เรื่องปกติกลางรอบ)

---

## คิวการตัดสินของ owner

| # | เรื่อง | ข้อเสนอ | จังหวะ |
|---|--------|---------|--------|
| A | TRN text เข้า git (split ignore ชั้น binary) | ทำ — มันคือ asset ที่แพงที่สุดของระบบ | ก่อน TRN-002 round 2 |
| B | Frame-of-record: subdir ต่อ round + manifest + rename script | ทำ | ตอน TRN-002 ปิด |
| C | แตก pipeline/scripts เป็น package | ทำ | ตอน TRN-002 ปิด |
| D | ย้าย repo ออก OneDrive / exclude output จาก sync | owner call — กระทบ ritual อื่น | เมื่อสะดวก |
| E | CLAUDE.md แยกชั้นกฎ/คดีตัวอย่าง | owner call | เมื่อสะดวก |
| F | เก็บกวาด: PLAN→docs/plans, run_altcwd, output/, usage counters, ลบ `_to_delete/`, ตัดสิน v4 walls divergence (ข้อ 5) | ทำ | สั้น ทำได้เลย |

พร้อมให้ตัดสิน

---

## TRIAGE (builder, 2026-08-04) — R7: ทุกข้อ accept+lane หรือ refute ด้วยการวัด

วัดทวนทุก claim ด้วย workflow 6 agents / 35 checks หลังรับรายงาน (เลขบางตัว
ขยับจาก snapshot ของ reviewer เพราะเลนเดินต่อระหว่างวัน — ทิศไม่เปลี่ยน)
housekeeping ที่ reviewer ฝาก: `_to_delete/` ลบแล้ว git ปกติ

| ข้อ | คำตัดสิน | การวัด | เลน |
|-----|----------|--------|-----|
| 1 frame-of-record | **ACCEPT** | ตอนนี้ **183** PNG (โตจาก 154 ระหว่างวัน — ยิ่งย้ำประเด็น), 0 ตรง convention, 684 MB, ignore ที่ `.gitignore:13` — ครบตามอ้าง แก้หนึ่งจุด: `batch-manifest.md` ชี้ `assets/projects/PRJ-2026-002/` และ 5/5 รายการที่สุ่มมีไฟล์จริงชื่อตรง convention — gap เป็นของเลน experiment/TRN หลัง manifest ไม่ใช่ deliverable batch-001 | B |
| 2 `_private` ทั้งเลนนอก git | **ACCEPT ปัญหา / แก้รูปทางแก้** | 703 text + 2,395 binary (โตจาก 683/2,333) ignore ทั้ง dir จริง (`.gitignore:26-27`) แต่ text ไม่ใช่ TRN ล้วน: `discord/` 93 + `_manifest-2026-07-12/` 299 ไฟล์คือ business pulls (names/tax/pricing — เหตุผลที่ ignore ถูกเขียนขึ้น) ดังนั้น "un-ignore text ทั้ง `_private`" ไม่ผ่าน — ใช้ทางที่สองของ reviewer เอง: **ย้าย TRN text → `training/TRN-00N/` tracked** หลักฐานหนุนว่าปลอดภัย: `C-001` ใน `_private` text = **0 ไฟล์**; address-word hits ทุกไฟล์อยู่ใต้ `_manifest-.../lookingfor-work/` กับ `_takeoff-012/` — ไม่มีในกอง TRN | A |
| 3 version-soup | **ACCEPT** | families ตรงตามอ้าง (g* 61, fx* 8, lb/lc/ld 10, weave 5, doorfix 3) + .blend 109 / .blend1 34; `*.blend1` ไม่มี rule global (วันนี้รอดเพราะอยู่ใน dir ที่ ignore) → เพิ่มหนึ่งบรรทัดใน F ได้เลย | B |
| 4 scripts แบน | **ACCEPT (เลขแก้) / refute หนึ่งประโยค** | 201 ไฟล์ (2 ไฟล์ใหม่วันนี้), 81,260 บรรทัด, trn001 10 / trn002 5 / test_* **75** (ไม่ใช่ ~90); top-10 = 21% ของบรรทัด (`build_room.py` 4,055 = 5% คนเดียว) REFUTED เฉพาะ "เส้นแบ่ง core/lane ไม่มี": ระดับ import วัดแล้ว**สะอาด** — trn001↔trn002↔build_room ไม่ import ข้ามกันเลย เส้นแบ่งหายแค่ระดับ layout → แตก package เสี่ยงต่ำกว่าที่รายงานกลัว | C |
| 5 walls diverge | **REFUTE เฟรม / ACCEPT residual ที่แคบกว่า** | md5 ตรงทุกตัวตามอ้าง แต่ "ไม่มีอะไรบอกว่าอันไหนถูก" ไม่จริง: v4 = root + 22 segments พร้อม `manual_additions` provenance block (owner-confirmed SW-corner, เส้น 0.48pt ต่ำกว่า gate 0.6pt ของ extractor) และ consumer ที่ active **ทุกตัว**อ่าน v4 อยู่แล้ว (test ทั้งสาม + v4 manifest + gate pin สดตรง bytes ปัจจุบัน) root/v5 เหมือนกัน**โดยเจตนา** (v5 = blind re-derivation control ที่ extractor deterministic ทำซ้ำ root ได้ bit-exact) — วันนี้ไม่มีใครอ่านของ stale **Residual จริงที่การวัดเจอ:** (a) ไฟล์ที่ path canonical `03_layout/floor2-walls-mm.json` คือฉบับ v3 ที่ขาด 4 ผนัง SW — consumer อนาคตที่ resolve path ตรง ๆ ได้ของขาดเงียบ ๆ และ root manifest ยังชี้มันพร้อม pin ที่ self-consistent (รัน build_floor ด้วย root manifest = ผนังผิดโดยไม่มี alarm) (b) `v5/floor2_v5-blind-read.md:14` + v5 manifest บรรยาย root ผิด (อ้างว่ามี manual_additions — md5 หักล้าง) → ทางแก้ที่ reviewer เสนอถูกอยู่ดี: provenance/pointer ที่ path canonical + แก้ doc สองจุด | F (โจทย์แคบลง) |
| 6 CLAUDE.md | ยืนยันเลข | 23,455 B / 314 บรรทัด | E (owner) |
| 7 PLAN ค้าง root | **ACCEPT** | 5 ไฟล์ **228 KB** (ไม่ใช่ 223) ทั้งหมด commit ล่าสุด 2026-07-07 หมายเหตุ: `PLAN-gate-hardening-freshness.md` ยังเป็นบันทึก verification ของ v4 gate — **ย้ายได้ ห้ามลบ** | F |
| 8 OneDrive | **ACCEPT** | incident จริง (index.lock วันนี้ — เก็บแล้ว); churn จริง: 684 MB + 2,395 binaries ใต้ sync | D (owner) |
| 9 absolute paths | **NUANCED → จุดแก้เดียวในโค้ด** | 38 ไฟล์ hit แต่เกือบหมดคือ doc/report/PLAN ที่ quote log + test fixtures ของ guard เอง (`test_guards.sh` = negative-control payload) โค้ดจริงจุดเดียว: `pipeline/scripts/structured3d_adapter.py:112` DATASET_ROOT hardcode → ย้ายเข้า env/`.env.example` ส่วน BRAINDEAD pointer ใน CLAUDE.md: ประเด็น "เลน DR ตายเงียบถ้า BRAINDEAD ย้าย" รับ — ทางแก้ env var เช่นกัน | F |
| 10 โฟลเดอร์จบหน้าที่ | **ACCEPT + สองเงื่อน** | `run_altcwd/` = pilot-blind 3 ไฟล์ 28 KB ไม่มี code reference → ย้าย (`qa/`) แล้วลบได้; root `output/` ว่างจริง แต่สาเหตุคือ ~15 สคริปต์ใช้ relative `output/` ผูก cwd — ลบ dir ได้ แต่ยากันเกิดใหม่คือ anchor path กับ script location; **usage counters ไม่ใช่ pure move** — hardcode ใน 6 สคริปต์ + 2 docs และ `.gemini_usage.json` ถูกใช้สดโดยเลน C3 วันนี้ → เลื่อนไปทำพร้อม C; PRJ-2026-001: จริงกว่าที่อ้าง — 01–08 **ทุก** stage มีแค่ `_contract.md` | F (counters→C) |
| 11 inbox ค้าง | **REFUTE ข้อเท็จจริง / ACCEPT ประเด็น** | เก่าสุดจริง = `knowledge/_inbox/interior-ai/` 7 ไฟล์ ลง 2026-06-30 (แก่กว่าที่อ้าง 3 วัน) — staleness ยิ่งหนักขึ้น เจ้าของงาน = `scripts/inbox_audit.py` ตามรอบ | F/รอบ audit |

PASS list ของ reviewer ตรวจซ้ำผ่านครบ: `.env` untracked (มีแต่ `.env.example`),
remote GitHub, warehouse ignore `.gitignore:50` ตรงกับ citation ใน R8 พอดี

### สิ่งที่การวัดทวนเจอเพิ่ม (ไม่อยู่ในรายงาน reviewer)

1. **Canonical-path stale walls + pin self-consistent** (ข้อ 5a) — defect เงียบ
   ตระกูล "ไฟล์ที่ถูก copy คือ coordinate ที่ถูก type" ตัวจริงของเรื่องนี้:
   ไม่ใช่ v4 ที่ผิด แต่คือ path หน้าบ้านที่ถือของ retired โดยไม่ประกาศ
2. **v5 blind-read doc บรรยายเนื้อ root ผิด** (ข้อ 5b) — protocol ถูก แต่เหตุผล
   ที่จดไว้ผิดจากเนื้อไฟล์จริง
3. **`structured3d_adapter.py:112`** hardcoded escape path จุดเดียวในโค้ด live
4. inbox เก่าสุดคือ 06-30 ไม่ใช่ 07-03

### ปรับคิว A–F ตาม triage

- **A**: ทำ แต่รูปคือ **ย้าย TRN text → `training/`** ไม่ใช่ un-ignore `_private`
  text (discord/manifest text คือของที่ ignore เกิดมากัน)
- **B, C**: ตามเดิม จังหวะ TRN-002 ปิด (C เสี่ยงต่ำกว่าที่รายงานประเมิน —
  import graph สะอาดแล้ว)
- **D, E**: owner call ตามเดิม — เลขยืนยันแล้วทั้งคู่
- **F**: ทำได้เลย ยกเว้น (i) usage counters ผูกโค้ด 6 จุด → ไปกับ C และ
  (ii) ข้อ 5 เปลี่ยนโจทย์จาก "เลือกอันถูก" เป็น "ประกาศ v4 ที่ canonical path
  หรือ stamp root เป็น retired-baseline + แก้ v5 doc สองจุด"

### Spend (R6)

- Workflow วัดทวน: 6 agents / 35 checks / ~299k subagent tokens / 62 tool
  calls / ~4 นาที wall
- Renders: 0 · NLM: 0 · housekeeping: `_to_delete/` ลบแล้ว

พร้อมให้ตัดสิน — triage ครบทุกข้อตาม R7 ไม่มีข้อไหนตอบด้วย taste

---

## คำตัดสิน owner + บันทึกการปฏิบัติ (2026-08-04, session เดียวกัน)

Owner ตัดสิน: **A ทำ · F ทำทั้งชุด · D exclude output จาก sync · E ยังไม่ทำ**
(B, C คงคิวเดิม = ตอน TRN-002 ปิด)

ปฏิบัติแล้ว:

- **A** — text TRN 272 ไฟล์ (TRN-001: 233, TRN-002: 39) ย้ายจาก
  `_private/benchmark/reproduction/` → `training/TRN-001|002/` โครง dir หนึ่งต่อหนึ่ง,
  staged 273 ไฟล์ (รวม README) · `target.json` สองไฟล์**ไม่ย้าย**ตาม charter
  (pick mapping ระบุตัว anchor/โปรเจกต์เพื่อนสตูดิโอ) · leak-scan อิสระหลังย้าย:
  C-001 = 0, คำ address ไทย = 0, stray pixel = 0 · `.gitignore` เพิ่ม rule กัน
  image/blend ใน training/ · procedure จนกว่า B/C จะ rewire: เครื่องมือเขียนลง
  `_private` เหมือนเดิม ปิดรอบแล้วย้ายชั้น text (ดู `training/README.md` +
  `_private/benchmark/reproduction/TEXT-MOVED-2026-08-04.md`)
- **F** — PLAN×5 → `docs/plans/` พร้อมบรรทัดสถานะที่วัดจริง (**ทั้งห้า EXECUTED**
  — ทุกแผนสร้างเสร็จ+wired ตั้งแต่ 07-07 มี commit+รายงานยืนยัน ไม่มีแผนค้างจริง
  แม้แต่แผนเดียว) · `run_altcwd/` →
  `_private/benchmark/pilot-blind/_superseded/run_altcwd-2026-07-15/` —
  **DEVIATION จากข้อเสนอ "qa/" ของ review และของ triage เอง**: ตรวจเนื้อไฟล์แล้ว
  `pilot-blind-key.json` คือเฉลย blind test (ระบุเอง "SPOILER") + anchor refs
  ของงานส่งจริงเพื่อนสตูดิโอ และ `pilot-blind.md` มีตาราง ref→image ที่ฉบับ
  canonical ลบทิ้งเพราะเป็น blindness leak → LOCAL-ONLY ตามคำสั่งยืน owner
  2026-07-12 (`qa/benchmark-sellability.md:49-59`) ห้าม track ที่ไหนก็ตาม;
  ฉบับ canonical ที่ใหม่กว่าอยู่ `_private/benchmark/pilot-blind/` อยู่แล้ว
  ฉบับนี้ park เป็น superseded (owner ลบได้เมื่อไม่ต้องการ provenance แล้ว) ·
  root `output/` ว่าง ลบแล้ว · `*.blend1` rule เข้า `.gitignore` ·
  `03_layout/README-walls.md` ประกาศ v4 = truth ณ จุดใช้งาน (bytes เลน v3 ไม่แตะ
  — pin แตก) · v5 doc correction 2 จุด (blind-read.md + manifest) ·
  `structured3d_adapter.py` อ่าน `STRUCTURED3D_ROOT` จาก env แล้ว —
  `.env.example` builder แก้ไม่ได้ (permission-blocked): **owner เพิ่มเองหนึ่งบรรทัด**
  `STRUCTURED3D_ROOT=C:/Users/teza_/studio-datasets/structured3d` ·
  usage counters เลื่อนไปทำพร้อม C ตาม triage (ผูกโค้ด 6 จุด + ไฟล์ Gemini ใช้สดอยู่)
- **D** — `pipeline/output` (684MB, 183 PNG + 109 blend) ย้ายจริงไป
  `C:\Users\teza_\PlingPeat-local\pipeline-output` แล้วแทนที่ path เดิมด้วย
  **junction** → สคริปต์ทุกตัวใช้ path เดิมได้ ไม่ต้องแก้ (verified: LinkType
  Junction, write-through จริง, 183 PNG อ่านผ่าน junction ครบ) OneDrive ไม่ sync
  เนื้อใน junction ตามพฤติกรรมมาตรฐาน — เฝ้าดู 1–2 วัน ถ้า client เริ่ม upload ซ้ำ
  fallback = ชี้ output path ตรงในสคริปต์แทน junction · หมายเหตุ: cloud จะเห็นการ
  "ลบ" 684MB — ถูกต้องตามเจตนา (ของออกจากขอบเขต sync)
- **E** — ไม่ทำตามคำตัดสิน (rules-in-face คงเดิม)

Observation ค้างให้ owner (นอก scope รอบนี้): `v5/floor2_v5-manifest.json`
บรรทัดท้ายมีชื่อเจ้าของบ้าน (K.NUT) + บริษัทออกแบบต้นทาง ใน tracked file —
ตัดสินว่าจะ anonymize ย้อนหลังหรือไม่

**ทั้งหมดยังไม่ commit** — commit เป็น ritual ของ owner (git mv ของ PLAN และ
training/ ถูก stage ไว้แล้ว; แก้ไฟล์อื่นอยู่ใน working tree)
