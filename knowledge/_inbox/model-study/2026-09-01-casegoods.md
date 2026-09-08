# Model study — CASEGOODS (nightstand ×5 + headboard ×1) · 2026-09-01

กลุ่มที่ R8 บอกให้ปั้นเอง (box+radius = millwork) จึงเป็นกลุ่มที่แปลงเป็น `millwork.py` ได้ตรงสุด.
แหล่ง: `assets/shared/blenderkit/_study/<id>.probe.json` · สถิติรวม `qa/blenderkit-study-stats.json` · ซีนเรา `_ours_p2r91.probe.json`.
ข้อควรระวังการอ่าน: `loc_mm` คือ object origin ไม่ใช่ bbox center — ทุกตัวเลข reveal ด้านล่างระบุสมมติฐาน pivot ที่ใช้ และตัวที่ pivot กำกวมถูกตัดทิ้ง ไม่เดา.

## ตารางต่อ asset

| asset | objects | verts รวม | ชิ้นส่วน (dims_mm) | bevel modifier | material |
|---|---|---|---|---|---|
| 11ec5eeb XF Bedside 47×37×50 [free] | 4 | 637 | carcass 470×370×485 (264v) · Drawer1/2 390×345×160 (191/174v) · Top 470×370×15 (8v) | BEVEL w=0.002 seg=2 ANGLE ทุกชิ้น | 2 mat, baked trio 2048 ต่อ mat |
| 24c65eb4 Asta Bedside 45×43×48 [free] | 3 | 400 | legs-root 479×400×440 (136v, MIRROR) · Body 450×430×260 (40v) · Door 410×30×220 (224v, 2 slots: Wood+Handle) | legs w=0.005 seg=4 · body/door w=0.001 seg=4 | 2 mat, baked trio 2048 |
| 6d4ccb0c Night Stand 40×40×55 [full_plan] | 2 | 336 | carcass 400×400×550 (228v) · Drawers 320×375×80 (108v) | BEVEL w=0.002 seg=1 | 1 mat, baked trio 2048 |
| bc74535c Teak & Oak 44×30×55 [full_plan] | 2 | 820 | carcass 440×300×550 (552v, 52 ngons) · Drawers 400×288×65 (268v) | BEVEL w=0.002 seg=2 | 1 mat, baked trio **4096** |
| d7e2a7bc Padded Headboard [free] | 1 | **78,353** | 2059×144×1666, 100% quads, modifier NODES (geometry nodes), 9,776 v/m² | — | 1 mat `fabric`: trio 2048, mapping_scale 2.0, NORMALMAP+BUMP ซ้อน, CURVE_RGB คุม roughness |
| fbb98c0b Nightstand [free] | 8 | 19,818 | จริง ๆ คือ vignette ทั้งชุด: ตู้ Cube.001 500×390×556 (6,756v, ไม่มี BEVEL mod — ขอบอยู่ใน geometry) + โคม (EMISSION+BLACKBODY) + หนังสือ 2 + แจกัน | หนังสือ w=0.001 seg=3 + WEIGHTED_NORMAL | 7 mat, ตู้ = baked trio ชื่อ `Cube.001_Bake1_PBR_*` |

สถิติคลาส nightstand (`qa/blenderkit-study-stats.json`): median 637 verts/asset (336–19,818) · subsurf_share = 0.0 ทุกตัว · quad_share median 0.938 · verts/m² median 704 · images median 6 (2048px) · displacement share = 0.0 · sheen = 0.0.

## idiom ที่พบ (ตัวเลข)

1. **ลิ้นชัก/ตู้เป็น object แยกจาก carcass (4/5)** — carcass 1 mesh + front/door 1–2 mesh + (บางตัว) top แยก. ตัวเดียวที่เป็น mesh เดียวทั้งใบคือ fbb98c0b ที่ sculpt แล้ว bake (Cube.001, mods=[]).
2. **ลิ้นชักเป็นกล่อง HOLLOW จริง** — พิสูจน์จาก area_m2 ÷ พท.กล่องปิดของ dims เดียวกัน:
   - XF Drawer1: 0.700/0.504 = **1.39×** (≈ กล่องเปิดฝาบน ผนังมีความหนา)
   - 6d4ccb0c Drawers: 0.415/0.351 = **1.18×** · bc74535c Drawers: 0.389/0.320 = **1.22×**
   - Asta Body (ตู้บานเปิด): 1.399/0.845 = **1.66×** = carcass เปิดหน้า มีผิวข้างใน
   - เทียบ: Asta Door = 0.98× (บานเป็น slab ตัน — ถูกแล้ว บานไม่ต้อง hollow)
   - carcass ไม่จำเป็นต้องเป็นกล่องด้วยซ้ำ: bc74535c = **0.71×** ของกล่องปิด (โครงขา/ระแนงเปิด)
3. **reveal/margin ระหว่างหน้าบานกับ carcass** (ตัวที่ pivot พิสูจน์ได้):
   - Asta (พิสูจน์ pivot=center จาก top-flush เป๊ะ 350==350): margin ข้าง **20 มม./ข้าง** (450−410)/2 · ล่าง **40 มม.** · บนชนขอบ **0** · หน้าบาน**ยื่นเลยหน้า carcass 5 มม.** (door y −220 vs body หน้า −215) — บานหนา 30 จมใน opening 25 โผล่ 5 = เส้นเงาจริงหน้าตู้
   - margin ข้างตัวอื่น (จาก dims, x=0 ทั้งคู่): XF 40/ข้าง · 6d4ccb0c 40/ข้าง · bc74535c 20/ข้าง + หน้า-หลัง 6/ข้าง (เลขนี้ = ความหนาแก้ม+ช่องไฟรวมกัน แยกจาก dump ไม่ได้)
   - XF: ลิ้นชัก 2 ชั้น c2c 320 มม. สูง 160 → **ช่องว่าง 160 มม. = ชั้นเปิดกลางตู้** — negative space เป็นดีไซน์ ไม่ใช่หน้าบานเรียงติด
4. **bevel: 1–2 มม. seg 1–4, limit ANGLE + shade smooth ทั้งใบใน 4 ตัว box + headboard (smooth_share=1.0)** — ยกเว้นชิ้น "ขา/โครงหนา" ที่ได้ w=5 มม. seg=4 (Asta legs). คือ bevel แยกตามบทบาทชิ้น ไม่ใช่ค่าเดียวทั้งซีน. ข้อยกเว้น shading: fbb98c0b ทุก mesh smooth_share=0.0 — ใช้ WEIGHTED_NORMAL modifier แทน shade smooth. ไม่มี SUBSURF เลยในคลาสนี้ (subsurf_share 0.0).
5. **มือจับไม่ใช่ object แยก — แกะอยู่ใน mesh บาน + material slot ที่สอง**: Asta Door 224 verts (slab เปล่า ~8–16v → ~200v เป็น handle+ขอบ), slot `Handle` = baked trio ของโลหะแยกจาก `Wood`. ไม่มีชิ้นไหนยื่นเกิน slab 30 มม. (จับแบบเซาะ/แนบ).
6. **วัสดุตัวตู้ = per-object UV bake เสมอ**: ทุก mesh มี uv_layers ≥1 (fbb98c0b มี 4 mesh ที่ 2 ชั้น) · mapping_scale = **1.0 ทุก baked trio** (texel density ถูก resolve ตอน bake) · สูตรตายตัว BaseColor(sRGB) + Roughness(Non-Color) + Normal(Non-Color ผ่าน NORMAL_MAP node) ที่ 2048 (bc74535c ใช้ 4096) · roughness ตัวตู้เป็น **map เสมอ ไม่ใช่ค่าคงที่** · Metallic=0, Sheen=0, Displacement=0 ทั้งคลาสตาม `_stats` (sheen/displacement share 0.0). node_hist ของ baked trio ซ้ำกันทุก asset: `TEX_IMAGE:3 + NORMAL_MAP + MAPPING + TEX_COORD` — สูตรเดียว. ขอบเขตที่ต้องพูดตรง ๆ: prop ประกอบใน fbb98c0b หลุดสูตร (plastic โคม = procedural, rough **คงที่ 0.4** · `Red Fabric` มี DISPLACEMENT node ใน graph · หนังสือใช้ BUMP ไม่มี MAPPING/TEX_COORD) — สูตรนี้คือของตัวตู้/ชิ้น bake ไม่ใช่ของทุก material ในไฟล์.
7. **detail อยู่คนละชั้นตามชนิดวัตถุ**: casegoods = mesh หยาบ (637 verts, 704 v/m²) + ผิว bake แน่น · upholstered headboard = ตรงข้าม: 78,353 verts quads ล้วน (geometry nodes) — รอยบุ๋ม/tufting เป็น geometry จริง ไม่ fake ด้วย normal map. ยืนยัน R8: ไม้=box ปั้นได้, นวม=free-form ซื้อ.
8. โบนัสจาก vignette (fbb98c0b): ไส้หลอดโคม = `EMISSION + BLACKBODY` (อุณหภูมิสีเป็นฟิสิกส์ ไม่ใช่ RGB มือ) · ตู้ที่ sculpt มา 6,756v/255 ngons ก็ **bake ลง trio เดียว** ชื่อไฟล์ `Cube.001_Bake1_PBR_*` — ขายความละเอียดผ่าน bake ไม่ใช่ผ่าน mesh.

## delta vs โค้ดเรา (file:line)

| เรื่อง | ของเขา (เลขข้างบน) | ของเรา | ช่อง |
|---|---|---|---|
| ลิ้นชัก hollow | ratio 1.18–1.39× | `millwork.py:767` `drawer_box` = กล่อง 8 verts ตัน — วัดจากซีนจริง p2r91: `mill__bayBF09-1-0_drawer_box0` area 0.972442 vs กล่องปิดจาก dims เดียวกัน 0.972443 = **ratio 1.000 เป๊ะ** | ช่องไฟ 10 มม. (DRAWER_REV) ของเราเปิดไปเจอหน้ากล่องตัน ไม่ใช่โพรงมืด |
| หน้าบาน nightstand | margin ข้าง 20–40 มม., ยื่นหน้า carcass 5 มม. | `millwork.py:889` หน้าลิ้นชัก nightstand = slab เต็ม footprint `(0,0,·,w_m,d_m,·)` ไม่มี margin ข้าง; มีแต่ z-reveal `NS_REV=0.006` (`millwork.py:209`) | หน้าใหญ่คลุมทั้งตัว (NS_DRAWER_H=185 vs ของเขา 65–160) และไม่มีเส้นเงาแนวตั้ง |
| bevel | หน้าบาน/ตัว 1–2 มม.; ขาโครงหนา 5 มม. — แยกตามบทบาท | `build_room.py:12968` `_bevel_edges(width_m=0.005, segments=3)` เหมาทั้งซีน ×150 objects; `build_room.py:1282` `MILL_BEVEL_M=0.0012` ×90 | ค่า 0.0012 ของ mill ตรง band ของเขาอยู่แล้ว; ตัว 5 มม. global คือ 2.5–5× ของ band หน้าบาน (แต่ตรง band "ขา" พอดี — เราใช้เลขขา ทาทั้งตัว) |
| มือจับ | แกะใน mesh บาน ~200v + slot วัสดุโลหะ | `millwork.py:25,35` ประกาศ handleless-by-design (PULL_H=0.030 pull-gap); ไม่มี handle/knob object ใดในซีน (grep p2r91 พบแต่ `Handle` ของ asset ที่ซื้อ) | สำหรับ wardrobe คือ design ที่ signed; สำหรับ **loose nightstand** คือ sense-gap 'ตู้ไม่มีมือจับ' — ทางของเขาถูกกว่าที่กลัว: ~200 verts + 1 slot, ไม่ต้องยื่นพ้นบาน |
| UV + normal | uv_layers=1 ทุก mesh → NORMALMAP + normal map จริง | ซีนเรา: mill 284 objects, **188 mesh uv_layers=0 + 23 เป็น CURVE ไม่มี UV เลย (รวม 211/284 ไม่มี UV; mesh ที่มี UV = 73)** → `build_room.py:2274-2277` บังคับใช้ BUMP จาก **Diffuse luminance** (`m_millwork_oak_veneer_photo`: `Normal: BUMP<IMG:oak_veneer_01_Diffuse_2k.jpg>`) เพราะ from_pydata ไม่มี tangent basis | ประตูสู่ stack ของเขาคือ **unwrap ก่อน** (cube project ก็พอ) — nor_gl 2k อยู่ในแคชแล้ว (`build_room.py:2270` อ้างค่า 2.246° ของมันเอง) |
| roughness | เป็น map เสมอ แม้ hardware ชิ้นเล็ก | `m_mill_brass` rough=0.35 คงที่, `m_mill_blackalu` 0.45, `m_mill_caesar` 0.28 — ไม่มี map (probe p2r91) | โลหะ/หินเราแบนสนิทระดับ specular |
| mapping_scale | 1.0 (bake แก้ปัญหา texel density ให้จบตั้งแต่ต้น) | box-projection + `tile_m` ต้อง assert ต่อ ingest (`material_presets.py:207` tile_m=1.83) — เคยพลาด 1.41×/4.81× มาแล้ว (memory: texture-scale) | คนละ paradigm; bake ต่อชิ้นคือทางที่ตัดคลาสบั๊ก tile_m ทิ้งทั้งคลาส |
| โครงสร้าง asset | 2–4 objects: carcass-root + front(s) + top | nightstand เรา 3 parts (toe/body/drawer `millwork.py:884-890`) — จำนวนชิ้นเท่ากัน แต่ split คนละแบบ: เขา split ตาม "ประตู/ลิ้นชักที่ขยับได้", เรา split ตามแนวนอน | split ของเขาให้เส้นเงาแนวตั้ง + เปิดทางมือจับ/hollow |

หมายเหตุความซื่อสัตย์: กลุ่มนี้ **สองตัวอยู่ในซีนเราแล้ว** ในฐานะของซื้อ — `bed__headboard` (78,353 verts = d7e2a7bc ตัวเดียวกันเป๊ะ) และ `side_table__acq0/1/2` (dims 431×451×261 + Door 30×411×220 + slot Wood/Handle = Asta 24c65eb4 หมุน 90°). โน้ตนี้จึงเป็นคู่มือ "ปั้นแทนของที่เช่ามา" ตรงตัว.

## กฎ transferable จัดอันดับ

1. **หน้าบาน/ลิ้นชักต้องเป็นชิ้นที่เล็กกว่า carcass และยื่นหน้า**: margin ข้าง 20–40 มม., ยื่นพ้นหน้า carcass ~5 มม. (Asta: 20/40/0/5). แก้ `millwork.py:889` — หน้า nightstand จาก slab เต็ม footprint → front ที่หด 20 มม./ข้าง + proud 5 มม.
2. **เจาะลิ้นชัก/ตู้ให้ hollow** (open-top box ผนัง ~15 มม.; เป้า area-ratio 1.2–1.4× ของกล่องปิด) — ช่องไฟถึงจะมีโพรงมืดหลังมัน. แก้ `millwork.py:767`.
3. **bevel สองอัตราตามบทบาท**: หน้าบาน/carcass 1–2 มม. seg 2–4 · ขา/โครงหนา 5 มม. seg 4 · ANGLE-limit + shade smooth เสมอ · ไม่ใช้ SUBSURF กับ casegoods. เรามีเลขถูกอยู่แล้วที่ `build_room.py:1282` (0.0012) — เลิกทาหน้าบานด้วยเลขขา (`build_room.py:12968`).
4. **มือจับ = geometry ในบาน ~200 verts + material slot โลหะ** ไม่ใช่ object แยก ไม่ต้องยื่นพ้นระนาบบาน — ปิด sense item 'ตู้ไม่มีมือจับ' ได้ในงบ verts จิ๋ว.
5. **สูตรวัสดุ casegoods มีสูตรเดียว**: BaseColor(sRGB)+Rough(map,Non-Color)+Normal(NORMAL_MAP,Non-Color) @2048 · Metallic/Sheen/Displacement = 0 · roughness ห้ามเป็นค่าคงที่. ขั้นแรกของเรา: unwrap mill parts (188 mesh uv_layers=0; อีก 23 เป็น CURVE ต้องแปลงเป็น mesh ก่อนถึงจะ unwrap ได้) แล้วต่อ nor_gl ที่แคชไว้แทน BUMP-from-Diffuse.
6. **งบ verts ของ nightstand ทั้งใบ = 336–820** (ช่วงจริงของ 4 ตัว box: 336/400/637/820 · median คลาส 637 · 704 v/m²) — ความจริงของผิวอยู่ที่ texture ไม่ใช่ mesh; เกินพันแปลว่ากำลังปั้นผิดชั้น.
7. **negative space เป็นชิ้นส่วน**: ชั้นเปิด 160 มม. ระหว่างลิ้นชัก (XF), โครงระแนง 0.71× ของกล่องปิด (bc74535c) — ตู้ข้างเตียงไม่ใช่กล่องเต็มเสมอ.
8. **upholstery ห้ามลอกวิธีนี้**: headboard = 78k quads จาก geometry nodes — คนละ regime; ยืนยันเส้นแบ่ง R8 (ไม้ปั้น/นวมซื้อ) ด้วยเลขจาก vendor เอง.

## คำถามที่ต้องพิสูจน์ด้วยพิกเซล

1. bevel 1–2 มม. vs 5 มม. ที่ระยะกล้อง deliverable — `build_room.py:565` เคยคำนวณว่า 1.2 มม. subtend ต่ำกว่า 1 px ที่ 3.9 ม.; ต้อง A/B crop จริงว่า 5 มม. "อ้วน" ให้เห็นไหม หรือมองไม่ออกทั้งคู่.
2. hollow drawer หลังช่องไฟ 10 มม. อ่านเป็นโพรงมืดต่างจากหน้ากล่องตันที่ recess 20 มม. จริงไหม (เรนเดอร์คู่เดียวตัดสิน).
3. front proud 5 มม. สร้างเส้นเงาที่เห็นได้ที่กล้องเราหรือไม่ (Asta อยู่ในซีนแล้ว — crop เทียบกับ nightstand ที่เราปั้นได้ทันที).
4. per-object bake 2048 vs box-projected 2k tiling ที่ระยะ ~1–2 ม. — อะไรทำให้ "ไม้ดูจริง" กว่า: ตัวเลขบอกแค่ต่าง paradigm บอกไม่ได้ว่าตาเห็นต่าง.
5. XF drawers ที่ y=−165 อาจเป็นลิ้นชัก "posed เปิด" หรือ pivot ที่หน้าบาน — dump ตัดสินไม่ได้ ต้องเปิดภาพ preview ของ asset (ห้ามเดา).

VERIFIED 2026-09-01 (รอบสอง หลัง critic): ตรวจ 32 ข้อ ผิด 7 แก้แล้ว 7 — (1) แยกชิ้น 5/5→4/5 · (2) smooth_share=1.0 ไม่คลุม fbb98c0b (0.0, WEIGHTED_NORMAL) · (3) uv_layers=1 ทุก mesh → ≥1 (fbb 4 mesh มี 2 ชั้น) · (4) สูตรวัสดุ/mapping 1.0 scope เฉพาะ baked trio ไม่ใช่ทุก material · (5) กล่องปิด drawer_box 0.9734→0.972443 (ratio 1.000 คงเดิม) · (6) mill ไม่มี UV: 211 "uv_layers=0" → 188 mesh uv=0 + 23 CURVE (สองที่) · (7) งบ verts 300–800→336–820 (bc74535c=820 หลุด band เดิม). file:line ทั้ง 12 จุด (millwork.py 25/35/169/209/767/884-890 · build_room.py 565/1282/2270/2274-2277/12968 · material_presets.py 207) ตรงไฟล์จริงทุกจุด; ratio hollow ทั้ง 6 ค่า, margin/reveal Asta-XF ทุกค่า, สถิติคลาส nightstand ทั้ง 7 ค่า, roughness คงที่ 3 ค่า p2r91, bevel ×150/×90 — ตรง dump ทั้งหมด.
