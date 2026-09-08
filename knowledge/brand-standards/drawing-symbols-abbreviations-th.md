# รายการสัญลักษณ์ประกอบแบบ & มาตรฐานถอดแบบ / Drawing symbols, material abbreviations & QS take-off conventions

> PROVENANCE: distilled from Discord "MY DATA PEAT" (forum channel #ข้อมูลแบ่งปัน), threads:
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/008_รายการสัญลักษณ์ประกอบแบบ-(ตัวย่อ-List-)/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/013_รายการถอดแบบ/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/003_Vocabulary-คำศัพท์ภาษาอังกฤษเกี่ยวกับชนิดของเก้าอี้/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/012_รวมสูตรคำนวล-Excel-ต่าง-ๆ/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/014_Handle/thread.md` (drop note, §6),
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/015_View/thread.md` (drop note, §6).
> §5 is distilled from the text channel #autocad-tip of the same server:
> `knowledge/_inbox/discord/MY-DATA-PEAT/autocad-tip/005_httpsoubeebwithprogram.blogspot.com201804cad.html/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/autocad-tip/003_DIMDISASSOCIATE/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/autocad-tip/004_วิธีแก้เส้นประ-LAYOUT-ไม่เปลี่ยน/thread.md`.
>
> LOCAL-ONLY inputs — read during distillation but **gitignored, NOT resolvable in a clean clone**; do not
> treat these as repo-resolvable provenance paths. Re-pull with `scripts/discord_ingest.py`:
> the Excel pack `files/688576_Excel_-20240902T085725Z-001.rar` (`.gitignore:34`) and the thread screenshot
> `files/575425_image.png` (`.gitignore:31`), both in thread 012's files/; and the hinge chart
> `files/383192_07-E0B89AE0B8B2E0B899E0B89EE0B8B1E0B89AE0B896E0B989E0B8A7E0B8A2-02-new-950x1024`
> (`.gitignore:37`) in thread 013's files/. Every value promoted from them is transcribed into this file
> with its sheet/row or table cell, so the evidence travels with the text, not with the binaries.
>
> Pulled 2026-07-03, tier REFERENCE. Source = studio practitioner notes ("Peat"), not a published standard;
> thread 005 is itself the practitioner's crib copy of a blogspot command list ("คำสั่งและโค้ดที่'เรา'ใช้บ่อย
> รวมไว้เพื่อให้กลับมาหาง่ายๆหากลืม" — 005/thread.md:16).
> AUTHORITY: statutory Thai minimums in `knowledge/codes-th/` OUTRANK every value here; where a value
> overlaps a legal floor, the law wins and this file defers to it.

Scope: the studio's own shop-drawing (แบบ Shop Drawing) material-finish tag legend, its
take-off / hardware-quantity conventions, an English chair-type vocabulary for FF&E labelling,
what the shared Excel estimating pack does and does not contain, and (§5) the CAD text-escape /
drawing-hygiene conventions our DWG→DXF reader has to survive. Codes here are **studio-internal
drafting tags**, not an industry-standard finish schedule — treat them as this studio's house convention.

---

## 1. ตัวย่อวัสดุ–ผิวสำเร็จบนแบบ / Material & finish abbreviation legend
Source thread: `008_รายการสัญลักษณ์ประกอบแบบ-(ตัวย่อ-List-)/thread.md` (Peat, 2023-10-12).
These are the finish tags written against surfaces on the studio's shop drawings.
Spelling is transcribed **exactly as the source wrote it**; a "corrected reading" column
resolves the obvious typos so the tag is unambiguous.

| ตัวย่อ / Code | ความหมาย (ตามต้นฉบับ) / Meaning as written | Corrected reading / วัสดุ |
|---|---|---|
| **SK** | บัวเชิงผนังอลูมิเนียม | Aluminium skirting / บัวเชิงผนัง อลูมิเนียม |
| **PT** | Paint Finnish (ผนังทาสี) | Paint finish — painted wall / ผนังทาสี |
| **MR** | Clear mirror, mirror (ผนังกระจก) | Mirror — clear mirror / กระจกเงา |
| **LA** | Lamineted panel (ลามิเนต) | Laminated panel / แผ่นลามิเนต |
| **CT** | Ceramic tiles (กระเบื้องเซรามิก) | Ceramic tiles / กระเบื้องเซรามิก |
| **ST** | (หิน) | Stone / หิน |
| **FB** | Wall Fabric (ผ้า–หนัง) | Wall fabric — fabric/leather wall / ผนังบุผ้า–หนัง |
| **WC** | Wall Paper Wall covenng | Wallpaper / wall covering / วอลเปเปอร์ |
| **ML** | Melamine panel | Melamine panel / แผ่นเมลามีน |
| **WD** | Wood | Wood / ไม้ |
| **GC** | Laminated Glass, Color Glass | Laminated / coloured glass / กระจกลามิเนต–กระจกสี |
| **GF** | ผนังกราฟฟิก | Graphic wall / ผนังกราฟิก |
| **SP** | Spray paint | Spray paint / สีสเปรย์ (สีพ่น) |
| **WV** | Woodvenneer, wall veneer | Wood veneer / wall veneer / ไม้วีเนียร์ |
| **MT** | กระเบื้องลอนคู่ | Twin-corrugated roof tile / กระเบื้องลอนคู่ |
| **SS** | stainless steel | Stainless steel / สแตนเลส |

Notes:
- The source list is the complete legend as posted; thread 008 has no attached image (text only).
- Typos in the raw ("Finnish"→finish, "Lamineted"→laminated, "covenng"→covering,
  "Venneer"→veneer) are the studio's own; kept in the middle column for fidelity.
- **MT** is unusual — it reads กระเบื้องลอนคู่ (a corrugated *roofing* tile), not a wall finish;
  carry it forward with care and confirm intent against the specific drawing before quoting.

---

## 2. การถอดแบบ – จำนวนบานพับต่อประตู/บานตู้ / Take-off convention — hinge count per door
Source thread: `013_รายการถอดแบบ/thread.md` (Peat, 2024-11-06, note "วิธีดูจำนวนบานพับ" = how to
read the required number of hinges) — image
`files/383192_07-E0B89AE0B8B2E0B899E0B89EE0B8B1E0B89AE0B896E0B989E0B8A7E0B8A2-02-new-950x1024`
(the Thai CDN filename lost its extension — the file on disk carries **no** suffix; LOCAL-ONLY,
`.gitignore:37`). Chart credit in image: **Häfele** ("ภาพและข้อมูลจาก hafele").

**Number of concealed hinges per door / จำนวนบานพับต่อหน้าบานประตู.** Pick the hinge count from
the door's height band; the door-weight band (at width 600 mm) cross-checks it.

| จำนวนบานพับ / No. of hinges | ความสูงบานสูงสุด / Max door height (mm) | น้ำหนักบาน / Door weight band (kg) | ความกว้างบานอ้างอิง / Ref. door width (mm) |
|---|---|---|---|
| 2 | up to **1000** | **4–9** | **600** |
| 3 | up to **1500** | **9–12** | **600** |
| 4 | up to **2000** | **12–18** | **600** |
| 5 | up to **2400** | **17–22** | **600** |

Right-hand nomograph in the same image: door weight is read on a **0–30 kg** axis; heavier doors
push into **"+1" and "+2"** zones (add one or two extra hinges beyond the table for very heavy
leaves). Weight-band boundaries visible on that axis fall around **~10 / ~20 / ~30 kg**.

Use: when doing a hardware take-off (ถอดแบบ) count hinges from door height first, then confirm the
leaf weight sits inside the band for that count; if the leaf is heavier than the band, apply the
+1/+2 rule. Weight bands assume a 600 mm-wide leaf — widen/heavier leaves shift the count up.

---

## 3. คำศัพท์ชนิดเก้าอี้ (อังกฤษ) / English chair-type vocabulary (FF&E labelling)
Source thread: `003_Vocabulary-คำศัพท์ภาษาอังกฤษเกี่ยวกับชนิดของเก้าอี้/thread.md`
(Peat, 2023-07-01 / 2023-10-10). Purpose: consistent English seating terms for schedules,
FF&E lists and model/asset naming. (The two images in the thread are a decorative banner and a
`chaise` 3D-model preview card — no data to transcribe.)

| English term | คำอธิบาย / Thai gloss |
|---|---|
| Chair | เก้าอี้ทั่วไป มักไม่มีพนักแขน มีขาสูงสี่ขา |
| Desk chair | เก้าอี้นั่งโต๊ะ; ใช้ในสำนักงานเรียก **Office chair** |
| Sofa | โซฟา ตั้งในห้องรับแขก บุนิ่ม นั่งได้หลายคน มีพนักพิง; เรียกได้ว่า **couch / settee** |
| Armchair | คล้ายโซฟาแต่นั่งคนเดียว มีพนักแขน |
| Rocking chair | เก้าอี้โยก โยกไปมาได้ |
| Wheelchair | เก้าอี้รถเข็นสำหรับผู้ป่วย/เดินลำบาก |
| Swivel chair | เก้าอี้หมุนได้รอบตัว (swivel = หมุน) |
| Folding chair | เก้าอี้พับได้ |
| Recliner | เก้าอี้เอนหลังได้ บางรุ่นนวดได้ (recline = เอนกาย) |
| Stool | เก้าอี้สตูล/บาร์ ที่นั่งกลม หมุนได้ |
| High chair | เก้าอี้สูงสำหรับเด็กเล็กนั่ง |
| Barber chair | เก้าอี้ร้านตัดผม; เรียกได้ว่า **Salon chair** |
| Dentist chair | เก้าอี้ร้านหมอฟัน |
| Director's chair | เก้าอี้ผู้กำกับ ที่นั่งผ้าขึงกับไม้ พับได้ |
| Deck chair | เก้าอี้ผ้าใบชายหาด |
| Lounge chair | เก้าอี้ไม้ยาวเอนนอนริมสระ |
| Waiting chair | เก้าอี้นั่งรอ แนวยาวหลายตัวต่อกัน (โรงพยาบาล/ธนาคาร) |
| Egg chair | เก้าอี้ไข่ ทรงคล้ายรูปไข่ |
| Ball chair | เก้าอี้ทรงกลม เปิดช่องให้เข้าไปนั่ง |
| Bench | ม้านั่งยาว (สวนสาธารณะ) |
| Baby chair | เก้าอี้ให้เด็กหัดเดิน |
| Pushchair | รถเข็นเด็ก; นิยมเรียก **stroller** |
| Car seat | เก้าอี้เด็กสำหรับใช้ในรถ เพื่อความปลอดภัย |
| Adirondack chair | (แอ๊-ดิ-รอน-แด่ก) เก้าอี้ไม้แผ่นเรียงต่อกัน มีพนักแขน ใช้นั่งชมวิวในสวน |
| Chaise | (เก้าอี้เอนนอนตัวยาว / chaise longue) — เพิ่มโดย Peat 2023-10-10 |

---

## 4. สูตร/เทมเพลต Excel ที่แชร์ / Shared Excel estimating pack — what is actually in it
Source thread: `012_รวมสูตรคำนวล-Excel-ต่าง-ๆ/thread.md` (Peat, 2024-09-02). The thread body is a
Google Drive link plus one screenshot (`files/575425_image.png`) and the pack itself as
`files/688576_Excel_-20240902T085725Z-001.rar` (thread.md:23–24).

**Correction (2026-07-13).** An earlier pass of this file dropped the pack as "general-purpose
business templates, not interior take-off/BOQ sheets" **while stating that the archive had not been
opened**. That negative was asserted, not measured, and it is wrong. The archive has now been opened
and enumerated: **139 RAR5 entries = 125 files + 14 folders** (the earlier note listed only the ~12
root-level files legible in the screenshot). Three of the files sit in the `ที่อยู่อาศัย/` (Housing)
folder that the screenshot showed as a folder name only, and they ARE interior fit-out costing sheets:

| File in `ที่อยู่อาศัย/` (inside the .rar) | Unpacked | What it is |
|---|---|---|
| `เครื่องคำนวณค่าตกแต่งห้องครัวอีกครั้ง1.xls` | 22,528 B | Kitchen fit-out cost worksheet — sheet `ค่าใช้จ่ายในการตกแต่งห้องครัว`, rows 1–45 |
| `เครื่องคำนวณค่าตกแต่งห้องน้ำอีกครั้ง1.xls` | 23,040 B | Bathroom fit-out cost worksheet — sheet `ค่าใช้จ่ายในการตกแต่งห้องน้ำ`, rows 1–41 |
| `ตารางเวลาการซ่อมบำรุงบ้าน1.xls` | 28,672 B | Home-maintenance schedule (3-monthly / autumn / spring inspection checklist), rows 1–79 |

**What is worth keeping from them (structure, not rates).** Both calculators share one layout:

- Column pair **`โดยประมาณ` (estimate) vs `ที่แท้จริง` (actual)** carried on BOTH the unit cost and the
  line total (kitchen sheet row 4; bathroom sheet row 5) — i.e. every line item is budgeted and then
  reconciled against what it really cost.
- A **contingency line: `ค่าใช้จ่ายที่ไม่คาดคิด` → `เพิ่ม 30%`** applied to the subtotal, then
  `รวมทั้งสิ้น` (grand total) — kitchen rows 42–45 (the literal `เพิ่ม 30%` at kitchen row 44),
  bathroom rows 38–41 (`เพิ่ม 30%` at bathroom row 40). **+30 %** is the only ratio **these two costing
  sheets** state. (Scope check, 2026-07-13: scanning every text cell of all 123 .xls for
  `\d+\s*%|ร้อยละ|เปอร์เซ็นต์`, **15 files state an explicit ratio** — e.g. VAT `ภาษีมูลค่าเพิ่ม 7%`, a
  `ราคาขายลด 20/30/40%` discount table, income-tax `หักค่าใช้จ่าย (ร้อยละ 40 …)`, a 1 %/month late fee —
  but none of the other 13 is a **fit-out cost** ratio.)
- **Kitchen line-item categories** (kitchen sheet, category headers): ตู้ลิ้นชัก (base + wall cabinets,
  quantified in running feet) · อุปกรณ์ทำความสะอาด (dishwasher, waste disposal) · อุปกรณ์ปรุงอาหาร
  (hob/range, microwave) · เคาท์เตอร์ · ประตู · พิเศษ · ก็อกน้ำ · พื้น · อุปกรณ์ซักรีด · ไฟ (recessed
  downlights) · ตู้เย็น · ซิงค์ · ระบบระบายอากาศ (hood) · ผนัง · หน้าต่าง · อื่นๆ.
- **Bathroom line-item categories** (bathroom sheet): ห้องน้ำ/ฝักบัว (tub, shower door, shower head, tub
  surround) · ตู้มีลิ้นชัก (medicine cabinet, vanity) · พื้นที่บนเคาท์เตอร์ · ก็อกน้ำ (tub / shower /
  basin) · พื้น · ฮาร์ดแวร์ (towel rail, paper holder) · ไฟ · ซิงค์ · ห้องน้ำ/ที่ฉีดน้ำล้างชำระ ·
  การระบายอากาศ · ผนัง · หน้าต่าง · อื่นๆ.

**Do NOT take rates or units from these sheets.** They read as translated office-suite templates
rather than Thai QS sheets: quantities are in **imperial units** (`จำนวนเป็นฟุต` / `ตารางฟุต`, cabinet
sizes in `นิ้ว` — kitchen rows 6, 15, 24; bathroom rows 11, 14, 20), the unit costs are round demo
numbers merely formatted with a ฿ symbol (dishwasher 250, refrigerator 1,200, recessed light 35 —
kitchen rows 9, 31, 29), and the companion maintenance sheet is organised by ฤดูใบไม้ร่วง / ฤดูใบไม้ผลิ
(autumn / spring — rows 30, 58), seasons Thailand does not have. This repo is metric-first (mm/m/m²)
and Thai-market-priced, so only the **category checklist, the estimate-vs-actual pairing and the
+30 % contingency** carry over; the numbers do not.

Notes:
- The other 122 files in the pack are general-purpose business/office templates (finance, HR,
  invoicing, education, health, calendars) — no drafting, symbol or take-off content. They are
  dropped; see §6.
- The Google Drive folder link in thread.md:20 was NOT followed (external link, unversioned). What is
  distilled above was read out of the `.rar` on disk — but that archive is **LOCAL-ONLY** (gitignored,
  `.gitignore:34`) and absent from a clean clone, so it is **not** itself a citable artefact either.
  The evidence a consumer can check is the transcribed rows and sheet/row references above; re-pull the
  archive with `scripts/discord_ingest.py` to re-derive them.

---

## 5. โค้ดในตัวหนังสือ CAD & ข้อควรระวังเวลาอ่านแบบ / AutoCAD in-string escapes + drawing-hygiene caveats for the reader
Source: `autocad-tip/005_httpsoubeebwithprogram.blogspot.com201804cad.html/thread.md` (Peat,
2024-08-17), with `autocad-tip/003_DIMDISASSOCIATE/thread.md` and
`autocad-tip/004_วิธีแก้เส้นประ-LAYOUT-ไม่เปลี่ยน/thread.md`. Tier REFERENCE — a practitioner's crib
sheet, not Autodesk documentation. Kept here because these values are consumed by **our DWG/DXF
reader**, not by a human operator.

READING RULE for this section: each quoted line is the source's; the "consequence" sentences after it
are **this repo's inference** for our reader, not a claim the source makes.

### 5.1 Decode table — `%%` escapes inside TEXT / MTEXT
These are typed inline in AutoCAD text, so expect the escape to survive verbatim into any label we
extract (a diameter note comes back as the string `%%c100`). Our reader does no unescaping —
`pipeline/scripts/dwg_ingest.py:224` returns `e.dxf.text` / `e.text` with only a newline-strip — so
decode at read time:

| Escape (as typed) | Renders as | Meaning |
|---|---|---|
| `%%c` | Ø | เส้นผ่านศูนย์กลาง / diameter (005/thread.md:25) |
| `%%d` | ° | องศา / degree (005/thread.md:24) |
| `%%p` | ± | บวกลบ / plus-minus (005/thread.md:23) |
| `%%189` | ½ | one half (005/thread.md:21) |
| `%%188` | ¼ | one quarter (005/thread.md:22) |

Consequence: any string match on extracted plan text (dimension strings, notes, schedules) must
normalise these five first, or a diameter note `%%c100` is read as a non-numeric token.

### 5.2 Caveats that COULD make printed plan text unreliable as ground truth

- **`DIMDISASSOCIATE` / alias `DDA`** — "คำสั่งล็อก DImension ไม่ขยับเวลา Move งาน" (003/thread.md:16,
  one post, 2023-10-26; the bare alias `DDA` re-posted 003/thread.md:19, 2024-05-20; also listed as
  "ทำลายความสัมพันธ์ Dimension" in the crib list at 005/thread.md:34): it breaks the dimension→geometry
  association so the dim text does not follow the geometry when the work is moved. The command **appears
  in this studio's tip channel** (that one post, plus the alias in the crib list) — the source says
  nothing about how often it is used, and nothing about it having been applied to any issued drawing.
  **IF** the command has been used on a sheet, a printed dimension string on that sheet need not track
  the geometry it labels — it may have been frozen before an edit. Under that condition, a lane scoring
  a reader against the designer's *printed* dims is scoring an author's claim rather than a measurement
  of the drawn geometry; when the two disagree, the disagreement is evidence, not automatically a reader
  bug. (Frequency of use in this office is UNMEASURED — do not read the above as a standing property of
  drawings from this office.)
- **`FIELD` + `REA`** — "บอกเลขพื้นที่ในกรอบที่กำหนด Update ได้หากกรอบขยับ *แต่ต้องกด REA"
  (005/thread.md:29): an area label can be a computed field over a bounded region; it updates when the
  boundary moves **but only once a regen (`REA`) is run**. So an area printed on a plan is only as
  fresh as its last regen — treat plotted areas as claims, and re-derive area from the boundary when
  it gates anything.

### 5.3 Settings that change what becomes INK in an exported plan

- **`PSLTSCALE`** — source wording: "`PSLTSCALE` = 0 (เส้นใน Model กับ Paper Relateกัน), 1
  (ไม่Relateกัน)" (005/thread.md:36) — i.e. at 0 the model-space and paper-space linetype scales are
  related, at 1 they are not (transcribed as written; this is the practitioner's phrasing, not
  Autodesk's). Worked example from the same channel: when dashed lines do not change in a LAYOUT, set
  `PSLTSCALE` → 0 then `REGENALL` (004/thread.md:16). Bears on how dashed / hidden linework is scaled
  in the PDFs the reader ingests: dash period is a *plot* property, so a dashed-vs-solid ink class
  must not be inferred from dash length alone across sheets.
- **`XCLIPFRAME`** — "= 0,1,… = การแสดงเส้นกรอบ Xclip" (005/thread.md:31): controls whether the clip
  frame of an XCLIPped block is displayed at all. A rectangle that looks like a wall/boundary in an
  export may be an xclip frame, and the same drawing plotted with a different `XCLIPFRAME` will not
  contain it — so a boundary-ink class must tolerate its presence *and* its absence.
- **`DWGCONVERT`** — "ปรับรุ่น AutoCAD Version ต่างๆ (ได้ทั้งปรับขึ้นและลง)" (005/thread.md:37): the
  studio's stated route for up- *and* down-versioning a DWG. This is the fallback when a received file
  is a DWG version our toolchain cannot open: convert first, then ingest. (Any conversion is a
  re-write — ingest from the converted copy, never overwrite the received original.)

### 5.4 Recorded but not consumed (operator-only, from the same source)
`EDGEMODE` 0/1 (whether Extend/Trim needs a true intersection, 005:32) · `TCOUNT` (auto-number a
sequence: start, step — 005:33) · `TCASE`/`TEXTCASE` (bulk text-case change, 005:28) · `UCS` (rotate
the axis, 005:30) · `BO` = `BOUNDARY` (005:35) · installing a `.ctb` plot style via Home > Print >
Manage Plotters, or Control Panel > Autodesk Plot Style Manager (005:40–42) · View > Viewports
(005:43–45). Listed for traceability only — these are GUI actions in software the render pipeline
does not run; nothing in them changes a value we consume.

---

## 6. Conscious drops from these staged units / รายการที่ตัดสินใจไม่ distil
Recorded so the drop is a decision, not an oversight.

- **`ข้อมูลแบ่งปัน/014_Handle`** (2024-11-12, a single message: the vendor link
  `https://www.krixhardware.com/aluminum-handle` plus its embed blurb — thread.md:16–17 — and one
  attachment, `files/447481_image.png`, thread.md:20). Hardware, so in this file's domain (§2), and
  therefore checked rather than assumed: the image was opened and is a browser screen-capture of that
  vendor's product page — hero banner, Thai marketing copy and four product photos of aluminium
  furniture handles. **No dimensions, no model codes, no take-off rule** → **dropped**: nothing in it
  is promotable into the §2 hardware take-off. If a later pull yields a KRIX size chart, re-open this
  drop.
- **`ข้อมูลแบ่งปัน/015_View`** (2025-04-07, three messages with empty bodies, 16 JPG attachments;
  thread.md:15–37). Four frames were opened
  (`files/875026_220057973_194234112675903_4320203909232886255_n.jpg`,
  `files/421672_LINE_ALBUM__by_.__1.jpg`, `files/196471_LINE_ALBUM__by_.__12.jpg`,
  `files/387402_LINE_ALBUM__by_.__15.jpg`): all four are exterior / site photography of a Thai
  detached-house estate (street elevations, landscaping, developer marketing flags). No dimensions,
  no schedules, no material tags, no drawing content → **dropped**: reference/mood photography with no
  promotable value. Two of the frames show a gate plate with a house number and an estate sales sign
  → under `.claude/rules/client-privacy.md` treat this thread's images as **not-for-external-sink**
  (no web search, no external tool call, no upload); they are gitignored (`.gitignore:32`,
  `knowledge/_inbox/discord/**/*.jpg`) and stay local. If a later pass finds a dimensioned frame among
  the 12 not opened, re-open this drop.
- **`ข้อมูลแบ่งปัน/012…` — the remaining 122 files of the Excel pack.** General-purpose business/office
  templates (invoicing, payroll, grading, health, calendars). No drafting, symbol or take-off content;
  they do not define this studio's QS method. Dropped. The three housing-folder sheets are promoted in
  §4 above.
- **`autocad-tip` threads 001, 002, 006, 007, 008, 009.** Each is a title plus one screen-capture
  video (`.mp4`, skipped by the ingest — e.g. 001/thread.md:18, 006/thread.md:18) and, in 002, one
  screenshot; the message bodies are empty. They are GUI walkthroughs (selection appearance, XCLIP
  picking, hatch from a block, TEXTFILL, viewport splitting, LAYISO) for AutoCAD, which the
  Blender + generative render pipeline does not run. Dropped as operator trivia. The two of these
  whose *setting* does reach our reader (XCLIP frames, dashed-line plotting) are captured in §5.3 from
  the text thread 005, so no value is lost by dropping the videos.

---

## Related studio references
- Material tags here name finishes; product-level material knowledge lives under
  `knowledge/materials/` and style tags under `knowledge/styles/` (cross-file, not merged here).
- Clearance/ergonomic values referenced during layout: `knowledge/ergonomics/residential-clearances.md`.
- Statutory dimensions always outrank: `knowledge/codes-th/`.
