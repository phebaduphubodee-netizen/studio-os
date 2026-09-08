# Blendkit Full — หนึ่งเดือนที่ต้องตอบด้วยตัวเลขและด้วยภาพ (2026-08-22)

คำสั่งพี่ verbatim (บันทึกใน `docs/owner-advice-2026-08-22.md` ข้อ 6):
**"สมัคร blenderkit 1 เดือนเลย ผมอยากจะรู้ว่ามันจะทำให้งานดีขึ้นยังไง"**
→ แถว `ORD-2026-08-22-blenderkit-one-month` ใน `qa/owner-orders.json` · ASK-029 ("เอาทางไหน") ปิดด้วยประโยคนี้
· การจ่าย/วาง key = `ASK-031` · เกณฑ์ที่ล็อกก่อนโหลดตัวแรก = `D-119` (+ `qa/blenderkit-month-classes.json`
+ `docs/blenderkit-month/style-panel-prompt.md`; hash ของสามไฟล์นี้ถูกเขียนลง log ตอนโหลดเสียเงินตัวแรก).

ประโยคหลังของคำสั่งคือคำถาม และคำถามนี้ repo ต้องตอบด้วย**การวัด** ไม่ใช่ความรู้สึกว่า "มีของเยอะขึ้น" —
และเพราะพี่อ่าน render ไม่ใช่เอกสาร (R3/R11) ข้อที่ตัดสินจริงต้องมี**ภาพ**อยู่ในนั้น ไม่ใช่ bench อย่างเดียว.
เกณฑ์จึงถูกเขียน**ก่อน**ดาวน์โหลดตัวแรก (บทเรียน flattering-scorer) และถูกรีวิวโดยกรรมการ fresh-context 5 lens
ก่อนล็อก (ร่างแรกผิด 4 จุดจริง — ดู D-119.because).

---

## 1. เงินซื้ออะไร และไม่ซื้ออะไร — สำรวจจริง 2026-08-22 (public API, ไม่มี account)

**ราคาจริง** (อ่านจาก markup หน้า `blendkit.com/plans/pricing`, แท็บทั้งสามของการ์ด Full):
**"30 day glimpse" $19.90 ไม่ต่ออัตโนมัติ** · Monthly $17.90 · Yearly $9.90/เดือน = $118.80/ปี.
หน้าเปิดที่แท็บ Yearly — เลข "$9.90/เดือน" ที่ทะเบียนจำไว้ตอนเช้า 08-22 คือแท็บนั้น. "1 เดือน" ตามคำสั่ง = glimpse.

| ชนิด | query (name-hit, ไม่ใช่ category) | ทั้งหมด | free | **ต้องจ่าย** |
|---|---|---:|---:|---:|
| model | shirt / clothes hanger / coat | 726 / 1,429 / 269 | 39 / 242 / 81 | **95% / 83% / 70%** |
| model | curtain | 595 | 64 | 89% (ไม่อยู่ใน frustum กล้อง record — ไม่ใช่คลาสของเดือนนี้) |
| model | bed (category_subtree:bed) | 1,244 (611) | 282 (106) | **77% (83%)** |
| model | floor lamp · vase · plant | 1,762 · 2,606 · 4,652 | 392 · 609 · 1,087 | 78% · 77% · 77% |
| model | armchair · pillow · rug · bench · wardrobe | 7,166 · 1,543 · 1,543 · 920 · 722 | 1,752 · 363 · 409 · 250 · 194 | 76% · 76% · 73% · 73% · 73% |
| model | nightstand · books · table lamp · candle · mirror · tray | 646 · 1,069 · 5,267 · 451 · 523 · 258 | 198 · 347 · 1,816 · 157 · 197 · 101 | 69% · 68% · 66% · 65% · 62% · 61% |
| **material** | wood / oak / walnut / veneer / fabric / linen / boucle / velvet / marble / plaster / concrete / carpet | ทุก query | **= ทั้งหมด** | **0%** |
| hdr | interior | 1,444 | 550 | 62% |

**ทำไมเลข 0 ของ material เชื่อได้** (เพราะ API ตอบ 0 กับ filter ที่สะกดผิดเหมือนกัน): หน้าราคาเองให้
material **Free = Full = 37,912** ชิ้น ขณะ model Free 23,383 vs Full 80,839 (71% หลังกำแพง) · filter `is_free`
แยกครึ่งได้จริงใน type อื่น: scene 1,055 + 3,420 = 4,475 · brush 1,256 + 5,428 = 6,684 เท่าค่าไม่กรอง ·
hdr 4,952 + 9,581 = 14,533 เท่าเลข HDRI บนหน้าราคา · `count` ตันที่ 10,000 จึงรวม type ทั้งก้อนไม่ได้ — ต้องบวกสองครึ่ง.

**ข้อสรุป:** เงินก้อนนี้ซื้อ **โมเดล** (เตียง, ของลอยทุกคลาสที่ P4 ต้องใช้, เสื้อผ้าแขวนที่ C3 ชี้เป็นอันดับ 1 บน p2r57)
และ HDRI บางส่วน — **ไม่ได้ซื้อ material**. ดังนั้น P2r-2 (ลายไม้ซ้ำ) ไม่ใช่สิ่งที่เงินแก้ — วีเนียร์สแกน 4,864 ตัว
หยิบได้วันนี้ที่ ฿0. ส่วน P2r-5 (ผิวผ้า 'พลาสติก') มีคำถามที่ต้องวัด ไม่ใช่ห้ามถาม: shader ของเตียงที่ซื้อช่วยไหม
เมื่อ render จาก .blend ต้นฉบับแทน GLB ที่ท่อเราแบนมัน (บรรทัด R4 ใน §3).

## 2. หลักฐานที่มีอยู่แล้วว่าชั้นฟรี "ไม่พอ" ตรงไหน (วัดแล้ว ไม่ใช่คิดเอา)

- **เตียงทั้งหลัง** — ชั้นฟรี Blendkit 12/12 ที่ panel ผ่าน ถูก stage ในห้องจริงแล้ว ด้วยเครื่องมือที่แก้แล้ว (D-109);
  ผ้านวมชั้นฟรีทุกแหล่ง 0/22 ผ่าน duvet-share 0.80 (p2r49, cut จากงานส่งจริง 7 ใบ); FurniMesh เตียงเป็น dry-only ·
  ตัวที่อยู่ในเฟรม (81d895fd) ผ่าน field ที่ขนาดมาตรฐานแล้ว (D-114: 1.00×1.00) แต่ duvet share 43.2% · คลังที่ยังไม่เคยวัด
  = **full-plan 135 ตัว** ที่ panel 12 คนคัดจาก 2,147 (`_private/deliv-001/bed-size-2026-08-18/blenderkit-shortlist/`).
- **ของลอยชิ้นง่าย** (โต๊ะข้าง ม้านั่ง) — ชั้นฟรีให้ได้แล้ว (p2r57: 341b04e0 + 5b8e98d7, กรรมการเงียบสองรอบ) → เป็น
  **control class** ของเดือนนี้: ถ้า paid ไม่ชนะฟรีแม้ในคลาสที่ฟรีชนะ ก็รู้ว่ากรรมการไม่ได้เข้าข้างของแพง.
- **คลาสที่ชั้นฟรียังไม่เคยถูกวัดเลย** (wall art, plant, cushion/throw, ของบนโต๊ะข้าง, เสื้อผ้าแขวน) — ไม่มีใครพูดได้ว่า
  "ฟรีไม่มี" จนกว่า 20 thumbnail แรกของชั้นฟรีจะผ่าน panel เดียวกัน **ก่อน** ตัว paid — ลำดับนี้บังคับใน classes.json.

## 3. เกณฑ์ที่ล็อก (D-119) — คำตอบของ "ดีขึ้นยังไง" ต้องผ่าน **C3 และ (C1 หรือ C2)**

| # | คำถาม | เครื่องมือ | baseline | ผ่านเมื่อ |
|---|---|---|---|---|
| C1 | **เตียง** — เตียง full-plan ที่ผ่าน bench ทุกข้อ **และดีกว่าตัวที่มี** | `wholebed_bench` + `wholebed_rules.verdict` ใน rect ที่ **derive จาก spec item kind=bed** (วันนี้ 3204,226,2000,1800; ไม่ใช่ 3204,51,2000,2149 ที่ D-114 retire — `blenderkit.py` พิมพ์ให้ ห้ามพิมพ์เอง) + `anchor_std` + style panel (prompt ที่ล็อก) · **differential** บน paired frames (สลับเฉพาะเตียง): ชนะ 81d895fd ≥2 ใน 3 ของ duvet share / bare-flank / จำนวน item ผ้าเตียง C2+C3 | 81d895fd: field 1.00×1.00, duvet 43.2% | ≥1 ตัว |
| C2 | **ของลอย P4** — paid ให้ชิ้นที่ผ่านในคลาสที่ฟรี**วัดแล้ว**ให้ไม่ได้ | `qa/blenderkit-month-classes.json` (5 คลาส non-control + 2 control) · dim_check ในคลาส asset_scale ของมัน + panel `inside` (≥2/3) · free_baseline (20 thumbnail แรกของฟรี) **ก่อน** paid ในคลาสนั้น ไม่งั้นไม่นับ | ต่อคลาส (ยังไม่มี) | ≥3 คลาส non-control ที่ฟรี = 0 |
| **C3** | **ภาพ** — เฟรมที่มีของซื้อ "ส่งลูกค้าได้มากกว่า" เฟรมเดิมไหม | คู่ A/B ล็อกจากกล้อง record สลับ**เฉพาะ**ของที่ซื้อ → sighted-reader panel (R4B 08-17: 3 reader fresh-context, anchor + เฟรมแทรกไม่ติดป้าย, คำถามเดียว + เหตุผลต่อช่อง) **และ** ตาพี่บนคู่ภาพ (R3) | p2r57 (s57) | panel 2/3 เลือก paid **และ** พี่ไม่ปฏิเสธ |
| R1 | บรรทัดรายงาน: item surface-realism top-3 ของ C2+C3 บน paired frames เดิม (critic เดิม prompt เดิม) | R7/R7b/R7c | p2r57 | รายงาน |
| R2 | บรรทัดรายงาน: blind RANK A-F — **เฉพาะเมื่อ P5r-1 กรอง anchor แล้ว** (3/5 anchor ครั้งก่อนมี watermark/ห้องเปล่า) ไม่งั้นไม่อ้าง | `look_bench --blind` | — | รายงาน |
| R3 | บรรทัดรายงาน: wall-clock ต่อชิ้นซื้อ vs ปั้น (ไม้บรรทัด 4 วัน/เฟรม, ASK-030) | `at` ใน `qa/blenderkit-fetch-log.json` | — | รายงาน |
| R4 | บรรทัดรายงาน P2r-5: เตียง paid ตัวเดียวกัน render ผ่าน GLB vs append จาก .blend ต้นฉบับ → highlight-histogram บนผ้านวม | cloth_highlights + คู่ภาพ | — | บอกว่าขีดจำกัดอยู่ที่คลังหรือท่อเรา |

**การต่ออายุไม่ได้ตัดสินที่นี่** — เงินเป็นของพี่ต่อการซื้อ (R8). วัน 30: `blenderkit.py status` พิมพ์ C1/C2/C3 และผมเปิด
procurement ask ใหม่ (ราคา Monthly $17.90 / Yearly $118.80, spec = ตัวเลขที่วัดได้ + คู่ภาพ) — พี่ตัดสินจากภาพ.
พี่ไม่ต่อ → tier `paid-subscription` ใน `qa/sourcing-tiers.json` กลายเป็น `searched` พร้อมตัวเลข = ครั้งแรกในประวัติ repo
ที่ชั้นเสียเงินถูก "วัด" จริง (R13: unbought ≠ unavailable). glimpse ไม่ต่ออัตโนมัติ — ไม่มี "ลืมยกเลิก".

**แช่แข็ง:** เปลี่ยนเกณฑ์ได้เฉพาะ**ก่อน** `status` พิมพ์ "MONTH CLOCK: first paid download …". หลังจากนั้น `status`
พิมพ์ `criteria freeze: CHANGED` ทุกรอบ และ gate ต้องเขียนว่าทำไม — การแก้เกณฑ์หลังเห็นผลคือ flattering-scorer.

## 4. ขั้นตอนของพี่ — 3 นาที ไม่มีอย่างอื่น (ASK-031)

1. `https://www.blendkit.com/plans/pricing` → การ์ด **Full** → เลือกแท็บ **"30 day glimpse"** (หน้าเปิดที่แท็บ Yearly
   $9.90/เดือน ซึ่งคือ $118.80/ปี — **ไม่ใช่อันนั้น**) → **$19.90 ครั้งเดียว** จ่ายด้วยบัตรพี่
2. key มาได้สามทาง — ทางหลักไม่ต้อง copy อะไรเลย:
   - **(หลัก) `python pipeline/scripts/blenderkit.py key --login`** — ทำสิ่งเดียวกับ add-on (OAuth PKCE ของ Blendkit ด้วย
     client_id/port/redirect ของ add-on เอง — อ่านจาก source สาธารณะ `bkit_oauth.py` + `bk_client/login.go`): Chrome เปิด
     `blendkit.com/o/authorize` → **พี่ login Google / กด Authorize ในแท็บนั้น** → redirect กลับ `localhost:62485/consumer/exchange/`
     → แลก code เป็น token ที่ `/o/token/` → เขียน `.env` (access + refresh + หมดอายุ; refresh อัตโนมัติก่อนหมด) → `status` ทันที
   - **(ก) เว็บ:** `https://www.blendkit.com/profile` → ส่วน **API key** → รันเองใน PowerShell ที่รากรีโป
     `python pipeline/scripts/blenderkit.py key <ค่าที่คัดลอก>` — เขียนบรรทัด `BLENDERKIT_API_KEY=` ให้ถูกรูปแบบ
     (ปฏิเสธถ้ามีช่องว่าง/`#`/เครื่องหมายคำพูดติดมา) แล้วทดสอบกับ `/me` ทันที · **ห้ามวาง key ลงในแชท** (มันจะติดไปกับ transcript)
   - **(ข) ผ่าน Blender (ตามคู่มือที่พี่ส่งมา):** Blender 5.1 → Preferences → Get Extensions → ติดตั้ง **BlenderKit** →
     แผง BlenderKit → **Login** ด้วย Google — คู่มือบอกว่า key "ถูกดึงมาอัตโนมัติตอน login" และเก็บไว้ใน preferences → แล้ว
     `python pipeline/scripts/blenderkit.py key --from-blender` อ่านจาก preferences ลง `.env` ให้เอง (ไม่พิมพ์ค่าออกหน้าจอ)
3. จบ — `python pipeline/scripts/blenderkit.py status` เห็น key เอง และพิมพ์ plan จาก `/me` (บอกได้ว่าซื้อ glimpse หรือเผลอกด Yearly);
   ไม่มี key = exit 2 พิมพ์ ASK-031; key ผิด/หมดอายุ = exit 2 บอกว่า key ถูกปฏิเสธ.

หมายเหตุ 2026-08-22 คืน: พี่สมัครด้วย Google account แล้ว — เครื่องนี้ยังไม่มี extension BlenderKit (userpref ลงวันที่ 4 ก.ค.)
ดังนั้นทาง (ข) ต้องติดตั้งก่อน; ทาง (ก) ไม่ต้องติดตั้งอะไร.

## 5. สิ่งที่เกิดเองหลัง key ลง (ฝั่ง builder ไม่มีการตัดสินใจค้าง)

```
python pipeline/scripts/blenderkit.py status
    # /me ยืนยัน plan · นาฬิกาเดือนยังไม่เริ่ม · คลาส C2 ที่ยังไม่มี free baseline
python pipeline/scripts/blenderkit.py shortlist            # default --limit 10 --resolution 2K
    # 135 full-plan beds ตามลำดับ panel → .blend → GLB (Blender --factory-startup -Y) → scale sidecar → SOURCE.json
    # โหลดเสียเงินตัวแรก = นาฬิกาเริ่ม + hash เกณฑ์ถูกเขียนลง log · ไม่มี key / key ผิด / ไม่มี Blender = exit 2 หยุดทันที
    # บรรทัด NEXT พิมพ์คำสั่ง bench พร้อม rect ที่ derive จาก spec
python pipeline/scripts/blenderkit.py bench --out _private/deliv-001/bed-size-2026-08-22/bench-full-blenderkit
    # = blender -b <p2rNN.blend ล่าสุด> --python wholebed_bench.py -- assets/shared/blenderkit <out> <rect จาก spec> <ids ที่ asserted จาก log>
```
ตัวที่ผ่าน → p2r58 ด้วยกฎเดิมทุกข้อ (R5 quick ก่อน · dim_check ก่อนพิกเซล · C2 blind + C3 Gemini · R10 ทุกชิ้นที่ติดมากับไฟล์
ต้องตอบว่าอยู่ทำไม) + คู่ A/B ของ C3 · ของลอย P4: ต่อคลาสใน classes.json — free baseline ก่อน แล้ว `search` + `fetch
--assert-class <cls>` (คลาสที่ยังไม่มี band ใน `asset_scale.BANDS` ต้องเพิ่มพร้อมแหล่งอ้างอิงก่อน fetch — R8).

`--resolution 2K` เป็น default เพราะ 135 ไฟล์ × ~50-90 MB (ต้นฉบับ 4K) ≈ 7-12 GB; 2K ลดครึ่ง และ 6 GB VRAM ไม่ได้ประโยชน์จาก 4K.
`.blend` เก็บไว้ข้าง GLB เพราะถือ Cycles material ของจริง — R4 ใช้มัน. log ทุกครั้งลง `qa/blenderkit-fetch-log.json`
(dry-run/search = probe ไม่นับ; tests/reviewer ชี้ `--log` ไปที่อื่น; บันทึกมือ `qa/blenderkit-search-log.json` ไม่ถูกแตะ).

## 6. สิ่งที่เงินก้อนนี้ไม่แก้ — พูดไว้ก่อนจะได้ไม่อ่านผิดตอนสิ้นเดือน

- **ลายไม้ซ้ำ (P2r-2)** — material ฟรีทั้งคลัง; เป็นงาน mapping ของเรา
- **ความละเอียดผ้า** — 08-17 วัดแล้ว: faceCount ของ asset อยู่ที่หัวเตียงบุนวม ไม่ใช่ผ้า; ผ้าเป็น mesh ชุดเดียวกันใน 3 ไฟล์ —
  full-plan ต่างไหม **ยังไม่รู้** และเดือนนี้คือการวัดนั้น (C1 differential + R4)
- **ขนาดที่ประกาศ** = ทั้ง asset รวมฉากที่ติดมา (D-109: "เตียงผ่าน" ครั้งก่อนเป็นแผงผนัง 2,759 มม.) — bench วัดเอง
- **10-15% สุดท้ายคือ art direction** (บันทึก 07-01) — ไม่มี pack ไหนซื้อให้; ผู้ชนะ C3 ยังต้องผ่านตาพี่
- **ใบอนุญาต**: royalty-free = render/งานลูกค้าได้ ห้ามขายต่อเป็นโมเดล; AI/ML เงียบ (`docs/LICENSING.md`) — ถือว่า
  "ยังไม่ตอบ"; asset ที่ API ไม่ระบุ licence บันทึกเป็น `unknown` ไม่ใช่อนุญาต; cache gitignored ไม่มีอะไรขึ้น git

## 7. ท่อพิสูจน์แล้วก่อนพี่จ่าย

- `pipeline/scripts/blenderkit.py` + `test_blenderkit.py`: pure half + **exit contract** (network/Blender stub, log ชั่วคราว):
  ไม่มี key → `status` 2, `shortlist` 2, `fetch` full-plan 2 ชื่อ ASK-031 ไม่ทิ้ง dir เปล่า · network ล่ม → 2 ไม่ใช่ traceback ·
  key ผิด → `status` 2, `shortlist` หยุดหลังเรียก API ครั้งเดียว · regex ของ ORD อ่านจากทะเบียนจริง จับเฉพาะ paid fetch ที่ไม่ใช่ probe
- live: `search` สาธารณะพิมพ์ tier ต่อแถว · **negative control** เตียง full-plan ไม่มี key → 401 → REFUSED exit 2 ·
  **positive control** โต๊ะข้างฟรี fbb98c0b `--resolution 2K` → 9.6 MB → Blender 5.1 export → GLB 13.8 MB → sidecar **8.3 วิ**
  · scale **REFUSED 940 มม. vs 300-800** = คำตอบจริง (ท่อปฏิเสธเอง)
- รีวิว fresh-context 5 lens + refuter ต่อข้อ (23 agents): ราคา, exit ของ `shortlist`, transport error, rect ที่ retire,
  เกณฑ์ที่ไม่เปิดภาพ, "≥3" ไม่มี baseline, กฎต่ออายุแทนพี่, field ใน ASK ที่ไม่มีคนอ่าน, `--factory-startup -Y`, cache สองชื่อ,
  log ไม่ atomic, SOURCE.json ทับ provenance — ทั้งหมดแก้แล้วในร่างนี้

## 7b. ความคืบหน้า — คืนแรก (2026-08-22 23:40 → 08-23 01:30, นาฬิกาเดือนวัน 0)

**Key:** พี่ "จ่ายตังแล้ว" + กดในแท็บที่ `key --login` เปิด (OAuth ของ add-on เอง) → `/me` Full · ASK-031 answered · ORD เหลือ restart_by ของผม.

**โหลด:** `shortlist --limit 10 --resolution 2K` → 10/10 เตียง full-plan ลง shelf, scale ASSERTED ทุกตัว (GLB 49–211 MB, 0.7–3.9 ล้านหน้า) ·
digest เกณฑ์ถูกเขียนลง log (status: MATCH).

**Bench ในห้อง p2r57, rect 3204,226,2000,1800 (derive จาก spec):** **1/10 ผ่าน hard filter ทุกข้อ** — ชั้นฟรี 0/12

| ตัว | หน้า | ผล | ตัวเลข/เหตุผล |
|---|---:|---|---|
| **Bolzan Letti 17aff0ff** | 0.92M | **PASS** | scale 0.91 · field 1929×1785 (0.99×0.97) · ที่นอน fit 1676×1951 = คิงไทย 6 ฟุต (±124) · plane 536 · ผ้า 4.3 มม./edge · หัวเตียงแยก · โต๊ะข้าง showroom ถูก strip |
| Ikea Nordli | 0.69M | fail | field 0.73 · ที่นอน 1340 ไม่ตรงไซซ์ — ตาเห็นเล็กจริง |
| Bed Loca Loft b43e2f5c | 0.73M | fail | field 0.71×0.81 · ที่นอน 1366×1478 |
| Metropol Sofa | 1.17M | fail | ที่นอน 1550×1710 ห่าง full 195 (ขนาดเดียวที่ตก) |
| Bed Loca loft 93862856 | 1.21M | fail | field 0.66×0.68 |
| Tierra | 1.29M | fail | หัวเตียงไม่ resolve · field 0 (ผ้ารกไม่มีโครง) |
| Bed 004 | 1.57M | fail | หัวเตียงไม่ resolve · field 0.60×0.25 (ผ้าลายม้าลายรก) |
| Slate Platform | 1.59M | fail | field 0.79×0.70 · ที่นอน 1140 เล็กจริง |
| Cloudrest | 2.66M | fail | เครื่องเลือก Quilt 1882×1979 เป็น anchor เพราะฐานจริง 1223×1655 — ผ้านวมยักษ์คลุมเตียงเล็ก ตาโดนหลอก เครื่องถูก |
| Obsidian Lounge | 3.86M | fail | ฐาน 2023×2179 ใหญ่เกินช่อง ต้องย่อ 0.85 → ที่นอน 1711×1843 ไม่ใช่ไซซ์จริง (front-door rule ปฏิเสธถูก) |

**Style panel (C1 ครึ่งหลัง):** 3 กรรมการ fresh-context, anchor 5 ใบจาก pool งานส่งจริง (tag "contemporary-neutral" ก่อนรัน — pool ไม่มี Japandi ตรง ๆ),
candidate A–E สุ่มไม่ติดป้าย (Bolzan + ฟรี 3 + Ikea paid) → **Bolzan inside 3/3** (profile: หัวเตียงผ้าเตี้ยมุมมน ฐานหุ้มผ้า) ·
เตียงฟรีที่อยู่ในเฟรมตอนนี้ (81d895fd) **edge 3/3** (หนังดำ + โต๊ะข้างติดมา — ข้อที่กรรมการ p2r56 เคยยื่น ยืนยันแบบ blind) ·
9ea98a45 (ฟรี) inside 3/3 แต่ตกขนาดตั้งแต่ 08-18 · บันทึก `_private/deliv-001/bed-size-2026-08-22/style-panel-bolzan/verdicts.json`.

**→ C1 ผ่านแล้วครึ่ง "bench + panel"; ที่เหลือคือ DIFFERENTIAL (paired frames ชนะ 81d895fd บน duvet share / bare-flank / item ผ้าเตียง) และ C3 (คู่ A/B + ตาพี่) ที่ p2r58.**

**ข้อค้นพบที่สำคัญกว่าตัวผ่าน (บรรทัด R4):** thumbnail ของ Bolzan เป็นกำมะหยี่เทาซีด ผ้าน้ำตาล/เทา — แต่ render ของเราขึ้น**ลายพิมพ์ขาว-ดำดัง ๆ** บนหัวเตียง/ฐาน และผ้ากลายเป็นขาว:
GLB ผูก texture `velvet` เป็น base color ของ material `body` (ใน .blend มันน่าจะเป็น map bump/roughness ผ่าน node) — ท่อ export ของเราแบน material ของ asset ที่ซื้อ
ซึ่งเป็นสิ่งที่เงินซื้อมา. ทางแก้ที่ถูก = append จาก .blend ต้นฉบับด้วย `bpy.data.libraries.load` (อยู่ใน DATA API ที่ layer law อนุญาต) — วัดเป็นคู่ GLB vs native ที่ p2r58 ตาม R4 ไม่ใช่แก้ลายด้วยมือ.

**ความผิดของผมคืนนี้ (บันทึกไว้ไม่ให้ซ้ำ):** bench run แรก "ดูค้าง 29 นาที" แล้วผมฆ่าทิ้ง — จริง ๆ มันเรนเดอร์ไป 9/10 แล้ว แต่ out dir ที่ผมส่งเป็น relative → Blender เขียน PNG ลง `C:\_private\…`
ขณะผมดูโฟลเดอร์ในรีโปที่ว่าง + stdout ที่ถูก capture จนจบ. ราคา: GPU 27 นาที + verdict ของ 9 ตัวหาย (เขียนตอนจบ). แก้แล้ว: `run_bench` ใช้ absolute path + stream `bench.log` ทีละบรรทัด;
ภาพ 9 ใบกู้ไว้ที่ `bench-full-blenderkit/run1-killed-renders/` (README อธิบาย).

**ถัดไป (p2r58):** Bolzan เข้า spec (model assertion + sheet_ref SR-18 headboard band เดิม; โต๊ะข้าง showroom ไม่เอา) → R5 quick → dim_check → คู่ A/B สลับเฉพาะเตียง (C3 + differential) →
C2 blind + C3 Gemini → R4 pair GLB vs native append บนเตียงตัวเดียวกัน · C2 ของลอย: free baseline ต่อคลาสก่อน paid · เตียง full-plan อีก 125 ตัวใน shortlist ยังไม่ได้ bench — ตอนนี้ไม่จำเป็น มีตัวผ่านแล้ว; ถ้า Bolzan ตก differential/C3 ค่อยเดินต่อ.

## 7c. คำตัดสินของ §7b ถูกกลับด้วยเครื่องมือที่แก้แล้ว (2026-08-23 เช้า, D-120)

**ตารางใน §7b ไม่ถูกลบ — มันคือบันทึกว่าเราเชื่ออะไรคืนนั้น. สิ่งที่เปลี่ยนคือเครื่องวัด และมันกลับคำตัดสินสองทาง.**

พี่ถามเช้า 08-23 ว่าทำไม Metropol ถึง "ไม่ตรงมาตรฐาน" ทั้งที่ที่นอนในไฟล์คือ 1786x1980 = คิงไทยห่าง 14/20 มม.
คำตอบ: bench เอา **โครง** (ชิ้นแปลนใหญ่สุด) ไป fit **ช่องที่นอน** แล้วถามว่าโครงที่หดแล้วเป็นไซซ์ที่นอนมาตรฐานไหม —
ผิดตั้งแต่คำถาม. พี่สั่ง "ลุย" → D-120.

| ตัว | §7b (คืน 08-22) | หลังแก้เครื่องมือ (08-23) | เหตุผลของเลขใหม่ |
|---|---|---|---|
| **Bolzan 17aff0ff** | **PASS** (ตัวเดียวที่ผ่าน) | **FAIL** ข้อเดียว | ที่นอนจริง 1800x2114 = EU 180x210 Überlänge; ย่อลงช่อง 0.946 → 1702x2000 ห่างคิงไทย **98** (เส้น ±50) · เดิมวัด "โครง" 1676x1951 ที่ ±150 จึงผ่าน |
| **Metropol e2418055** | fail ("ที่นอน 1550x1710 ห่าง full 195") | **PASS ทุกข้อ** | เลข 1550x1710 เดิมคือ**โครงที่ถูกย่อ 0.84**; ที่นอนจริง **1786x1980 = คิงไทย ห่าง 20 ที่ scale 1.0** ไม่ต้องย่อเลย |
| **Obsidian b4915f0a** | fail (ฐานใหญ่เกิน) | FAIL สองข้อ | ที่นอน 1671x2012 (EU160+ผ้าห่อ) → 1661x2000 ห่าง 139 · **และโครงจริง 2011x2175 ล้ำหมึก SR-07 20/31** ซึ่งกฎเก่ามองไม่เห็นเพราะ cluster-fit ย่อทุกอย่างลงช่องเสมอ |
| **81d895fd — เตียงที่อยู่ในเฟรมตอนนี้** | ไม่เคยถูก bench ด้วยกฎขนาด | **FAIL** | ที่นอนจริงคือ Cube.015 **1400x1900 = US full (เตียงคู่) ห่าง 28** ไม่ใช่คิงไทย · เต็มช่องแค่ **0.78**x0.95 · เครื่องเก่ามองไม่เห็นเพราะมันจับ Plane.029 (ผ้าปู 1578x2047) เป็น anchor |
| Ikea / LocaLoft / Slate / Bed004 / Cloudrest / Tierra | fail (field/ขนาด) | fail (เหตุผลคมขึ้น) | Slate = ที่นอน 1336x1895 "full" ใต้ผ้านวม 1641 (fill 0.74) · Cloudrest ฐานจริง 2311 ล้ำหมึก 167 ที่เดิมอ่านว่า "อยู่ใน" เพราะวัดผ้านวม · Tierra/LocaLoft-938 = **UNMEASURABLE** (mesh เดียว / ที่นอนแยกสอง mesh) ไม่ใช่เดาเลขจากโครง |

**ทำไมนี่ไม่ใช่การแก้เกณฑ์หลังเห็นผล (D-119 ข้อ D) — ตอบตรง ๆ ไม่เลี่ยง:**
- **ข้อความเกณฑ์ C1 ไม่ถูกแตะ**: ยังคือ "เตียง full-plan ≥1 ตัวผ่าน `wholebed_bench` hard filters ทั้งหมด + anchor_std + style panel".
  สิ่งที่เปลี่ยนคือ **เครื่องมือ** ภายใต้คำสั่ง standing `ORD-2026-08-22-front-door-dims` และ "ลุย" ของพี่วันนี้.
- **ทิศทางตรวจสอบได้และสวนทางกับ flattering-scorer**: ตัวที่เครื่องเคยเชียร์ (Bolzan, ตัวเดียวที่ผ่านคืนนั้น) **ตกลง**;
  ตัวที่เคยปฏิเสธ (Metropol) ผ่านที่ scale **1.0** — ไม่ต้องย่อ ไม่ต้องยืด. เกณฑ์ที่ถูกขยับเพื่อให้ของที่อยากได้ผ่าน จะไม่มีวันให้ผลแบบนี้.
- **เกณฑ์ใหม่เข้มขึ้นสามข้อ ไม่ใช่หลวมลง**: tolerance 150→**50** (ที่นอนเปลือย, knowledge:45,124), เพิ่ม **mattress_fill ≥0.88**
  (ที่นอนเองต้องเต็มช่อง — Slate เคยจะผ่านด้วยที่นอน 1336 "full" ใต้ผ้านวม 1641), และเพดานหมึกอ่าน **โครงจริง** แทน anchor ที่เป็นผ้า 4 ใน 11 ไฟล์.
- **จุดบอดที่บันทึกไว้ ไม่ใช่ปล่อยผ่าน**: `criteria_digest` แฮช D-119 in_effect + classes + prompt — **ไม่แฮชโค้ดของ rung**
  จึงยังพิมพ์ MATCH ทั้งที่ instrument เปลี่ยน. รอบหน้าที่แตะ rung ระหว่างเดือน ต้องเขียนแบบนี้อีก (D-120 ข้อ 9).

**สิ่งที่ยังไม่รู้และไม่แกล้งรู้:** `_place_bed_frame` ของ build ยัง fit frame cluster เข้าช่อง — bench PASS **ยังไม่ใช่คำทำนายของภาพจริง**.
แถว bench จึงพิมพ์ `hook_scale_today` + `hook_agrees` ข้าง scale ของตัวเอง; hook จะกิน `pick_mattress` ในรอบ build แรกที่ integrate เตียงซื้อ.

**ผลต่อ C1:** ตัวที่ผ่าน bench ตอนนี้คือ **Metropol Sofa (e2418055)** ไม่ใช่ Bolzan — และ Metropol **ยังไม่เคยผ่าน style panel**
(คืนนั้น panel รัน Bolzan). C1 จึงกลับไปเป็น "ครึ่งเดียว" อีกครั้ง: bench ผ่าน, panel + differential + C3 ยังไม่รัน.
Bolzan ยังเป็นทางเลือกของพี่ได้ — มันตกที่ **98 มม.** จากคิงไทยด้วยเหตุผลที่ตรวจสอบได้ (ที่นอน 1800x2114 = EU 180x210 Überlänge
ที่ตารางเราไม่มี; ตัวโครง 2144 ยาวเท่าหมึก 2134 พอดี) — ระยะ 50-150 คือดุลยพินิจของพี่จากภาพ (D-110) ไม่ใช่ตัวเลขที่ผมขยายเอง.

## 8. คำตอบของเดือน — ยังไม่มี

เริ่มเมื่อ key ลงและ `status` พิมพ์ MONTH CLOCK. หัวข้อนี้จะถูกเขียนเป็น "## 8. คำตอบของเดือน — ตอบแล้ว …" พร้อมตัวเลข C1/C2/C3,
คู่ภาพ A/B, และ ask ต่ออายุ — ORD อ่านหัวข้อนี้ด้วย regex และไม่พลิกเป็น obeyed จนกว่ามันจะมี.
