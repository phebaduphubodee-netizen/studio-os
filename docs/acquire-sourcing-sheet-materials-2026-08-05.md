# ACQUIRE sourcing sheet — วัสดุ/ผ้า/พรม (R8 lane) — 2026-08-05

จัดทำโดย Claude-Cowork ตาม R7c/R8 หลัง C2 verdict `trn002_mat_r15`
(defect อันดับ 1 = กลุ่มเตียงทั้งกลุ่มอ่านเป็นปูนปั้น)

**ขอบเขต:** เฉพาะแหล่งที่ใช้กับ Blender ได้จริง + ตรวจ licence text จากหน้าเจ้าของ
เอง ไม่ใช่จากบล็อกสรุป · ไม่แตะกฎ DELIVERY ใน `docs/LICENSING.md` — sheet นี้คือ
ชั้น SOURCING เท่านั้น ทุกอย่างยังต้องผ่านกฎ Combined-Work / no-standalone เดิม

---

## สิ่งที่พบก่อนเริ่มค้น — และมันเปลี่ยนคำถามทั้งหมด

`pipeline/scripts/assets.py` **มี fetcher ของ Poly Haven อยู่แล้ว และรองรับ
`textures` เป็น type หนึ่งในสามอยู่แล้ว** (models / hdris / textures) แต่
`material_presets.py` ทั้ง 1,254 บรรทัด **ไม่มีการอ้าง texture ไฟล์ใดเลย** —
grep เจอคำว่า fabric 18 ครั้ง ทั้งหมดเป็น procedural shader ไม่มี image texture
สักตัว

แปลว่า 15 รอบของเฟสวัสดุถูกเล่นด้วย procedural ล้วน ในขณะที่ท่อ acquire ของ
CC0 texture นั่งรออยู่ในโค้ดตัวเอง ตั้งแต่ก่อนเฟสวัสดุจะเริ่ม — นี่คือ R8 ซ้ำรอย
เดิมเป๊ะ ("everything FREE FORM ที่ปั้นเองเพี้ยนเสมอ") แค่ย้ายจากเรขาคณิตมาเป็นผิว

**ข้อเสนอที่ตามมา: รอบ 16 ไม่ควรเป็นการปรับ shader อีกรอบ แต่คือการต่อ
`assets.py --type textures` เข้ากับ material_presets แล้ววัดว่าภาพขยับไหม**

---

## Tier 1 — CC0 จริง: commit ได้ ใช้เชิงพาณิชย์ได้ ไม่มีเงื่อนไขซ่อน

| แหล่ง | ของที่มี | licence (ตรวจจากหน้าเจ้าของ) | สถานะในระบบเรา |
|---|---|---|---|
| **Poly Haven** | textures / models / HDRI | CC0 — "use for any purpose including commercial", redistribute ได้, ไม่ต้องเครดิต, **อนุญาต AI/ML ชัดเจน** ([polyhaven.com/license](https://polyhaven.com/license)) | ✅ มี fetcher แล้ว (`assets.py`) — ยังไม่ถูกใช้กับ texture |
| **ambientCG** | PBR สูงสุด 8K + displacement, HDRI, ไฟล์ Substance | CC0 — "may be used for commercial purposes, **even if that means redistributing them as files**" ([ambientcg.com](https://ambientcg.com/)) | ❌ ยังไม่มี fetcher — คุ้มค่าเขียนเพิ่ม |

**ทำไม ambientCG สำคัญกับ defect ของเรา:** มีหมวด `Fabric0xx` และ `Carpet0xx`
เป็นชุด พร้อม **displacement map** ซึ่งคือสิ่งที่ทำให้พรมมี pile จริงและผ้ามี
weave นูน — ตรงกับ defect #1 (ผ้าไม่มี weave) และ #6 (พรมเป็นกระดาษ) โดยตรง
ตัวอย่างที่ยืนยันแล้วว่ามีอยู่: [Fabric022](https://ambientcg.com/view?id=Fabric022),
[Fabric019](https://ambientcg.com/view?id=Fabric019),
[Carpet001](https://ambientcg.com/view?id=Carpet001),
[Carpet008](https://ambientcg.com/view?id=Carpet008),
[Carpet011](https://ambientcg.com/view?id=Carpet011),
[Carpet012](https://ambientcg.com/view?id=Carpet012),
[หมวด Fabric ทั้งหมด](https://ambientcg.com/list?sort=Popular&category=Fabric)

**หมายเหตุการวัด (ตรงไปตรงมา):** หน้ารายละเอียดของ ambientCG ทั้งสองหน้าที่ผมลอง
เปิด **ถูก robots.txt บล็อกไม่ให้ผมอ่าน** — ผมจึงยืนยัน "CC0 + 8K + displacement"
ได้จากหน้าแรกของเว็บ แต่**ยังไม่ได้ยืนยันรายละเอียด map ต่อไฟล์ด้วยตาตัวเอง**
ก่อน ingest ให้เปิดหน้า asset จริงหนึ่งใบแล้วบันทึกลง provenance ตามวินัย R8

## Tier 2 — ใช้ได้แต่มีเงื่อนไข ต้องอ่านก่อนจ่าย

**Poliigon** (มี Blender addon ทางการ) — [terms](https://www.poliigon.com/terms)
- ห้าม redistribute asset เดี่ยว ๆ ไม่ว่าจะแก้แล้วหรือไม่ → **ห้าม commit ลง git**
  (ใช้กติกาเดียวกับ `assets/shared/warehouse/` ที่ gitignore ไว้)
- **ห้ามใช้กับ AI/ML โดยเด็ดขาดหากไม่ได้ licence แยก** — ข้อนี้ต้องให้ owner
  ตัดสินก่อนแตะ เพราะ repo นี้มี `style_embed.py` / CLIP embed bank / เลนชื่อ
  TRN (training) อยู่จริง ต่อให้เจตนาเราเป็น benchmark ไม่ใช่การเทรนโมเดล
  ความเสี่ยงในการตีความก็ไม่เป็นศูนย์
- ชุมชนรายงานว่า**เคยแก้เงื่อนไขเงียบ ๆ** (ห้ามฝัง texture ในโมเดลที่ขาย, ห้าม
  cloud render, ห้าม bake ลง UV เพื่อขาย) — [เธรด Blender Artists](https://blenderartists.org/t/warning-poliigon-changed-their-conditions-to-the-worse/1415347)
- คำตัดสินของผม: **ไม่แนะนำสำหรับระบบนี้** — ข้อ AI/ML ชนกับสถาปัตยกรรม repo ตรง ๆ

**BlendKit / BlenderKit** — [licences](https://www.blendkit.com/docs/licenses)
- มีสองแบบ: CC0 (อิสระเต็ม) และ Royalty-Free (ใช้เชิงพาณิชย์ได้ ห้ามขายต่อเป็น
  asset) → **ต้องกรองเอาเฉพาะ CC0 เท่านั้นถ้าจะ commit** ส่วน RF ใช้ได้แต่ต้อง
  gitignore · เอกสารไม่พูดเรื่อง AI/ML → ถือว่ายังไม่ตอบ

**Sketchfab / Fab** — [คู่มือ licence](https://www.licenseorg.com/guide/3d-assets/sketchfab)
- ปนกันทั้ง CC0 / CC-BY / CC-BY-NC / CC-BY-ND ต่อโมเดล → **ต้องอ่านทีละชิ้น**
  CC-BY-NC ใช้กับงานลูกค้าไม่ได้เลย
- ฝั่ง Fab (Epic รวม Quixel Megascans + Sketchfab Store): licence "ยังเปลี่ยนอยู่"
  และห้าม redistribute ทุกชั้น ([Fab guide](https://www.licenseorg.com/guide/3d-assets/fab)) ·
  หน้า licence ของ Quixel เองตอบ 403 กับผม — **ยังไม่ยืนยัน** ว่าสถานะ "ฟรี"
  หลังปี 2024 เป็นอย่างไรในปี 2026 ([ที่มาของความไม่แน่นอน](https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/))

## Tier 3 — ห้าม / ไม่คุ้มกับระบบนี้

- **3DSky / 3DDD** — คลัง interior ที่ใหญ่และตรงรสงานที่สุดในตลาด แต่เป็น
  ecosystem ของ 3ds Max + V-Ray/Corona และผลค้นเต็มไปด้วยไซต์ mirror เถื่อน
  (`3dskyfree`, `gfx-hub`, `visualstorms`) → **แหล่ง mirror = ห้ามแตะ** ทั้ง
  licence และความปลอดภัยไฟล์
- **แหล่ง mirror/nulled ทุกชนิด** — ไม่มีข้อยกเว้น

---

## ข้อเสนอเชิงปฏิบัติ (owner ตัดสิน)

1. **เขียน `ambientcg.py` คู่กับ `assets.py`** — CC0 เหมือน Poly Haven จึง
   commit ได้ ใช้ cache dir เดียวกับ CC0 ที่มีอยู่ ไม่ต้องแยกเหมือน warehouse
2. **ต่อ texture เข้า `material_presets`** สามคลาสก่อน ตามลำดับ defect ของ
   mat_r15: ผ้าเครื่องนอน → พรม (displacement คือหัวใจ) → วีเนียร์ millwork
   (defect #5: ลายพื้นถูกใช้กับทุกชิ้น สเกลใหญ่เกิน)
3. **ห้ามเรียก Poliigon จนกว่า owner จะตัดสินข้อ AI/ML** — เขียนเป็น pin ใน
   LICENSING.md ไม่ใช่ความจำของ session
4. **ผ้านวม/หมอนที่เป็น geometry** ยังไม่มีคำตอบจาก sheet นี้ — แหล่งฟรีที่
   ค้นเจอ (Sketchfab/Free3D/CGTrader ฟรีทีเออร์) licence ปนกันหมดและคุณภาพ
   ไม่ garantee สำหรับงานขาย ทางที่สะอาดกว่าคือ **cloth sim ในบ้านตัวเอง** ซึ่ง
   repo มีของอยู่แล้ว (`drape.py`, `test_drape_feedstock.py`, cloth-stack contact
   law) — ข้อนี้จึงเป็น BUILD ที่ชอบธรรมตาม R8 เพราะ input มันคือตัวเลขที่วัดได้
   (fill weight/loft) ไม่ใช่รูปทรงอิสระ

## ช่องที่ sheet นี้ยังไม่ปิด (ห้ามอ้างว่าปิดแล้ว)

- รายละเอียด map/ความละเอียดต่อไฟล์ของ ambientCG — robots บล็อก ต้องเปิดด้วยมือ
- สถานะ Megascans/Fab ปี 2026 — หน้า licence ต้นทาง 403
- ตัวเลขราคาทุกแหล่ง — **ไม่ได้ตรวจ** และ ledger เคยจับ DR กุราคามาแล้ว จึงไม่ใส่

Sources หลัก: [Poly Haven licence](https://polyhaven.com/license) ·
[ambientCG](https://ambientcg.com/) · [Poliigon terms](https://www.poliigon.com/terms) ·
[Poliigon Blender addon](https://www.poliigon.com/blender) ·
[BlendKit licences](https://www.blendkit.com/docs/licenses) ·
[Sketchfab licence guide](https://www.licenseorg.com/guide/3d-assets/sketchfab) ·
[Fab licence guide](https://www.licenseorg.com/guide/3d-assets/fab)

---

# ภาคผนวก 2026-08-08 (r34) — ตรวจข้ออ้างกลางของ sheet กับ tree ปัจจุบัน

*(เพิ่มโดย session อื่น หลัง owner ส่ง sheet นี้กลับเข้ามาพร้อมคำถาม "ไม่รู้เกี่ยวกับ lane นี้มั้ย" — เนื้อหาเดิมด้านบนไม่ถูกแก้)*

sheet ระบุว่า *"material_presets.py ทั้ง 1,254 บรรทัด ไม่มีการอ้าง texture ไฟล์ใดเลย …
แปลว่า 15 รอบของเฟสวัสดุถูกเล่นด้วย procedural ล้วน"*

| ข้ออ้าง | ผลตรวจ |
|---|---|
| `material_presets.py` ไม่มี image texture เลย | **จริง** — `grep -c "TexImage\|\.jpg\|\.png\|texture_file"` = **0** |
| ⇒ "15 รอบของเฟสวัสดุเล่นด้วย procedural ล้วน" | **ไม่จริงสำหรับเลนที่ sheet เขียนถึง** |

`mat_r15` คือเลน **TRN-002** ซึ่งใช้ `pipeline/scripts/trn002_materials.py` ไม่ใช่
`material_presets.py` (ตัวหลังเป็นของเลน PRJ-2026-002) และเลน TRN-002 **มี image map
มาตั้งแต่เฟรมวัสดุแรก**:

- `trn002_materials.py:51` `CC0 = assets/shared/cc0/textures`
- `MAP_FILE` (`:616`) มี 6 ชุด: `wood_floor`, `plastered_wall_03`, `marble_01`,
  `rough_linen`, `wool_boucle`, `poly_wool_herringbone`
- บนดิสก์มี 9 slug ที่ดึงผ่าน fetcher ของ Poly Haven แล้ว
- commit `b5fa066` (2026-08-04, "the first materials+light frame") เป็น **บรรพบุรุษ**
  ของ `459137e` (r15, 2026-08-05) — ยืนยันด้วย `git merge-base --is-ancestor`

**ข้อสรุปเชิงปฏิบัติของ sheet ("รอบ 16 ไม่ควรเป็นการปรับ shader อีกรอบ แต่คือการต่อ
`assets.py --type textures` เข้ากับ material_presets") จึงใช้กับเลน PRJ ไม่ใช่ TRN-002**
สำหรับ PRJ มันยังเป็นข้อเสนอที่ถูกต้องและยังไม่ได้ทำ

### และสิ่งที่ sheet ชี้ กลับ**เกี่ยวข้องมากขึ้น**หลัง r33 ไม่ใช่น้อยลง

r33 (2026-08-08) เปิด normal-map relief ให้ผ้าสองตัวและ **วัดไม่ขึ้นเลย แม้ที่ strength 5.0**
— ข้อสรุปคือ **แอมพลิจูดไม่ใช่ตัวจำกัด แสงนุ่มของเราต่างหากที่ล้างมันทิ้ง** (R1 STOP รอบ 2)
`rug_cream` เดินเส้นทาง DIFFUSE_OFF + normal ที่ strength 0.9 มาหลายรอบ และวัดได้
**0.0045 เทียบเป้า 0.0493 — ขาด 11 เท่า**

**ทางยกระดับที่ sheet ชี้ไว้พอดีคือ DISPLACEMENT ไม่ใช่ normal** — และจุดขายที่ sheet
ให้กับ ambientCG คือหมวด `Fabric0xx` / `Carpet0xx` **พร้อม displacement map**
displacement ขยับเรขาคณิตจริง จึงไม่ถูกล้างด้วยความนุ่มของแหล่งกำเนิดแบบที่ normal ถูก

---

## สิ่งที่ทำไปแล้วจาก sheet นี้ (2026-08-08, r34)

- **เขียน `pipeline/scripts/asset_scale.py`** — ปิดครึ่ง ASSERT ของกฎ scale ที่
  `pipeline/CLAUDE.md` ยอมรับเองว่ายังไม่มี · ต่อเข้า `warehouse.py fetch --assert-class`
  จึงรันใน path ที่รันอยู่แล้ว · 13 tests
- **พบว่าตัวขวางจริงของเลน ACQUIRE ไม่ใช่แหล่ง แต่คือ CONSUMER**:
  `trn002_build.py` **ไม่มีเส้นทาง import glTF เลย** (`build_room.py` มี) — นี่คือเหตุผลที่
  asset 26 ชิ้นใน `assets/shared/` ไม่เคยถูกใช้ **ไม่ว่าจะเพิ่มแหล่งอีกกี่แหล่งก็ไม่ช่วย
  จนกว่าจะมีทางเข้า** เขียนไว้ใน `spec_r34.declared_gaps.garments`

## สิ่งที่ยังต้องใช้ owner

1. **ข้อ AI/ML ของ Poliigon** — ตาม sheet: ห้ามแตะจนกว่าจะตัดสิน และปักเป็น pin ใน
   `docs/LICENSING.md` ไม่ใช่ความจำของ session · **ยังไม่แตะ**
2. **เขียน `ambientcg.py` หรือไม่** — CC0 เหมือน Poly Haven จึง commit ได้และใช้ cache เดียวกัน
   **ผมเสนอให้รอ** จนกว่าเส้นทาง glTF/texture ingest ของ trn002 จะมี มิฉะนั้นได้ fetcher
   ตัวที่สองที่ไม่มีใครบริโภคได้ ซึ่งเป็นข้อผิดพลาดเดียวกับที่ sheet นี้ชี้
3. **ผ้านวม/หมอน** — sheet เสนอ cloth sim ในบ้าน (`drape.py` มีอยู่แล้ว) เป็น BUILD ที่ชอบธรรม
   ตาม R8 เพราะ input เป็นตัวเลขวัดได้ (fill weight/loft) **ยังไม่ได้ประเมิน**
