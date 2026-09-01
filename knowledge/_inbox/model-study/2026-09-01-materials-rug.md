# Model study — MATERIALS cross-cut + RUG (2026-09-01)

กลุ่ม: MATERIALS (rug `0fd746ae`, misc `18261a8a`) + cross-cut 216 material rows จากทั้ง corpus 71 dump.
แหล่ง: `assets/shared/blenderkit/_study/*.probe.json`, สถิติรวม `qa/blenderkit-study-stats.json`, ซีนเรา `_ours_p2r91.probe.json`.
ตารางดิบทั้ง 216 แถว: `assets/shared/blenderkit/_study/_mat_table.txt` (สร้างจาก probe, ชี้กลับ dump ได้ทุกแถว).

## ตารางต่อ asset

| asset | คืออะไร | objects | verts | mesh | material สรุป |
|---|---|---|---|---|---|
| `0fd746ae` Carpet (rug) | พรม 2427×3024×26.3 mm | 1 | 1,585 (210.9 v/m²) | quad 100%, slab หนา 26.3 mm, UV 1 ชั้น, ไม่มี modifier | mat `Texture`: Base=`AMBIENT_OCCLUSION<HUE_SAT<IMG:Carpet Set-001>>`, Rough=const 0.5528, Normal=`BUMP<IMG:Carpet Set-003>` (BUMP×2 ใน tree), `DISPLACEMENT` node scale **0.5**, ภาพ 3 ใบ **671×996 px** (001 sRGB / 002,003 Non-Color) |
| `18261a8a` = **Carafe Bottle 1l + Cork** (ระบุจาก dump: ชื่อ object ตรงตัว, ขวดแก้ว ⌀87.6×270.2 mm + จุก ⌀55.1×26.8 mm) | ขวดแก้ว procedural ล้วน (0 images) | 2 | 1,220 | cage 898+322 verts, quad 100%; ขวดมี `BEVEL(w=0.007, seg=2, angle)` + `SUBSURF(render=2)` (จุกไม่มี modifier) | แก้ว: Transmission 1.0, **Rough 0.0274 (ไม่ใช่ 0)**, Base 0.8 เทา, Normal=`BUMP<PROC:NOISE>` (แก้วจริงผิวไม่เนียนสนิท) · จุก: Base=`VALTORGB<VALTORGB<PROC:NOISE>>`, Rough 0.8435, Coat 0.0638, Normal=`BUMP<VALTORGB<PROC:NOISE>>` |

### Cross-cut 15 แถวตัวแทน (จาก 216)

| cls / asset | material | Base | Rough | Normal | sheen | disp scale | mapping |
|---|---|---|---|---|---|---|---|
| rug `0fd746ae` | Texture | AO<HUE_SAT<IMG>> | 0.5528 | BUMP<IMG> | 0 | **0.5** | 1,1,1 |
| whole_bed `8968de2e` | waffle_pique_cotton | HUE_SAT<IMG> | IMG | NORMALMAP<IMG> | **0.3** | 0.0015 | 3,3,3 |
| whole_bed `8968de2e` | ribbed_corduroy | IMG | IMG | NORMALMAP<IMG> | 0.2 | 0.0006 | 5,5,5 |
| whole_bed `b4915f0a` | scuba_suede | MIX<HUE_SAT<IMG>> | IMG | NORMALMAP<IMG> | 0.0744 | 0.0001 | ~1 |
| whole_bed `b8359da9` | Velvet | MIX<PROC:NOISE> 2 โทน | IMG | NORMALMAP<IMG> | **0.08** | – | 5,5,5 |
| whole_bed `17aff0ff` | body | MIX<BRIGHTCONTRAST<MIX<IMG>>> + LAYER_WEIGHT | VALTORGB<IMG> | BUMP<INVERT<VALTORGB<IMG>>> | 0.0015 | – | 6,6,1 |
| garment `03ede500` | Procedural Fabric | VALTORGB<MIX×3<NOISE>> | VALTORGB<MIX×3> | BUMP<MIX×4> | 0.2 | – | **2,11,2** |
| throw `b89bc1af` | Procedural gray Fabric 01 | MIX<NOISE> (MAGIC อยู่ใน tree, จุดเสียบ trace ไม่เห็น) | **0.9455 const** | BUMP×2 (trace เห็น BUMP<NOISE>) | 0.2 | – | 2,2,2 |
| handbag `8f19d91a` | Begie_leather | RGB | INVERT<IMG gloss> | NORMALMAP<IMG> | 0.2 | – | 10,10,10 |
| nightstand `bc74535c` | Teak & Oak (baked 4K/object) | IMG | IMG | NORMALMAP<IMG> | 0 | – | 1,1,1 |
| table_lamp `18d17256` | WoodKendra | CURVE_RGB<HUE_SAT<IMG diffuse>> | INVERT<IMG glossiness> | NORMALMAP<IMG> | 0 | 0.003 | 2,2,2 |
| table_lamp `18d17256` | NaturalLinen (โป๊ะ) | HUE_SAT<IMG> | IMG | NORMALMAP<IMG> | 0, Transmission 0.333 | 0.01 | 5,5,5 |
| table_lamp `dcebfd80` | Brass (Metal035 2K) | IMG | IMG | NORMALMAP<IMG> + Metalness IMG | 0 | – | 1,1,1 |
| table_lamp `dcebfd80` | White Marble (Marble005 2K) | IMG | IMG | NORMALMAP<IMG>, Transmission 0.4 | 0 | 0.005 | 1,1,1 |
| table_lamp `01bb0e45` | metall (procedural) | RGB 0.6422 | 0.2318, Metallic 1.0 | NORMALMAP<VALTORGB<NOISE>> | 0 | – | **30,30,30** |

## idiom ที่พบ (ตัวเลข)

1. **สูตรมาตรฐาน image-based = diff(sRGB) + rough + normal ครบชุด, colorspace แทบไม่พลาด.** 449 ภาพทั้ง corpus: data map (normal/rough/metal/disp/alpha/aniso) เป็น Non-Color 300 ใบ — ผิดจริงแค่ 2 ใบ (`f8573a9c` Blue Leather normal+roughness เป็น sRGB) = วินัย 300/302 ≈ 99.3%. diffuse เป็น sRGB เสมอ.
2. **sheen ของผ้า: แถบหลัก 0.02–0.3 (มี 6 แถวผ้าของ `17aff0ff` ตั้ง 0.0015 ≈ ศูนย์), ฐานนิยม 0.2, เพดานที่เห็นจริง 0.3.** 46/216 แถวตั้ง sheen>0; ผ้า: waffle_pique 0.3, Cotton 0.3, gingham 0.2448, corduroy/teddy/leather/procedural-fabric 0.2, jersey 0.1565, herringbone 0.0986, Velvet 0.08, suede 0.0744, denim 0.0213 (ตัวเดียวเกินคือแก้ว vase `b4d3ed11` 1.0). สอดคล้อง stats: whole_bed sheen_set 59.3%, throw 18.2%.
3. **displacement จริง (node DISPLACEMENT) ใช้ใน 34/216 material (16%), scale เป็นมิลลิเมตร:** ผ้าบนเตียงส่วนใหญ่ 0.0001–0.0015 m (0.1–1.5 mm: suede 0.0001, jogging 0.0002, denim 0.0003, herringbone 0.0005, corduroy 0.0006, jersey 0.0007, gingham 0.001, waffle/teddy 0.0015; หมอน `b43e2f5c` และ Brown fabric `b8359da9` ขึ้นถึง 0.003), ไม้ 0.003, marble 0.005, โป๊ะ linen 0.01. outlier ผ้า: clear pants `2751554e` 0.05; rug คือ outlier 0.5. rug class disp_share 1.0, whole_bed 0.424 (`qa/blenderkit-study-stats.json`).
4. **ผ้า procedural ล้วนมี 2 ตระกูล** (6 แถวผ้า — อีก 4 แถว procedural ในคลาสผ้าคือ hook โลหะ ×3 กับ Acrylic Paint): (A) garment 4 แถวใน 3 asset (`03ede500`, `91bbbed5`×2 สี, `ef06e40e`) ใช้ tree เดียวกัน `NOISE×2+WAVE+VORONOI×2 → MIX×9 → VALTORGB×3` แจก Base/Rough/Metallic(ผ่าน INVERT) + `BUMP<MIX×4>`, sheen 0.2, **mapping [2,11,2]** — ยืด noise 5.5 เท่าตามแกนเดียว = ทิศเส้นด้าย; (B) throw `b89bc1af` (2 แถว) มี `TEX_MAGIC` (ลายสอดประสานเป็นคาบ = โครงทอจริง) + NOISE ใน tree, trace เห็น `MIX<NOISE>` เข้า Base, Rough const 0.9455, BUMP ต่อกัน 2 ชั้น (จุดเสียบ MAGIC/NOISE ต่อชั้นไหน dump ไม่บอก — เปิด `.orig.blend` วัน port), mapping [2,2,2].
5. **velvet ไม่ได้อยู่ที่ bump แต่อยู่ที่มุมมอง:** `b8359da9` Velvet = `MIX_SHADER(BSDF_SHEEN + PRINCIPLED)` + Base 2 โทนผ่าน `MIX<NOISE>`, sheen weight แค่ 0.08; `17aff0ff` body มี `LAYER_WEIGHT` คุม MIX ของ albedo (สีเปลี่ยนตามมุมตกกระทบ). ทั้ง corpus: LAYER_WEIGHT 21 แถว + FRESNEL 15 แถว, ซ้อนกัน 12 → รวม 24/216 (11%) มี facing term.
6. **HUE_SAT เป็น stage ย้อมสีมาตรฐาน: 56/216 (26%)** คั่นระหว่าง IMG กับ Base Color (rug, waffle, WoodKendra, Terrazzo, teddy) — เปลี่ยน hue/sat โดยไม่ทับ luminance detail ของ texture.
7. **resolution ต่ำกว่าที่คิดมาก:** rug 7.3 m² ใช้ภาพ **671×996**; ชุดผ้าเชิงพาณิชย์ (8968de2e, b4915f0a) **63–75% เป็น 512 px** (27/43, 24/32 ใบ) แล้ว tile ด้วย mapping 3–5; เตียง 17aff0ff ใช้ 427×427–2048. เงินลงที่ **geometry แทน**: whole_bed 655k–1.8M verts/asset. ชุดผ้าขาย ship map ครบ 8 ชนิด (aniso_rotation/strength, spec_ior, disp) แต่ที่ถึง output จริง **5** (diff/rough/metal/nor_gl + disp เข้า node DISPLACEMENT) — aniso×2 กับ spec_ior ไม่ wire; มืออาชีพก็ไม่ wire ทุก map.
8. **แก้ว/จุก procedural (carafe `18261a8a`):** แก้ว Rough 0.0274 + `BUMP<NOISE>` (ผิวคลื่นจาง ๆ) ไม่ใช่ 0.0 เกลี้ยง; จุกคอร์ก = double `VALTORGB` บน NOISE ทั้งสีและ bump + Coat 0.0638. Cage 898 verts + BEVEL+SUBSURF — ของกลม = โมเดลเบา + modifier, ไม่ใช่ mesh หนา.
9. **AO node แทบไม่ใช้ (2/216)** แต่ตัวที่ใช้คือ**พรม** — `AMBIENT_OCCLUSION` คูณเข้า Base เพื่อกดร่องขนให้มืดโดยไม่ง้อ GI (อีกตัว: `f8573a9c` LEATHER).

## delta vs โค้ดเรา (file:line)

1. **พรมใน p2r91 คือ asset `0fd746ae` ตัวเดียวกันเป๊ะ — แต่ node tree หายระหว่าง ingest.**
   `_ours_p2r91.probe.json`: `rug__acq0` dims [3023.9, 2426.8, 26.3] (หมุน 90°), 1,585 verts, mat `Texture` เหลือ node_hist `{TEX_IMAGE:2, NORMAL_MAP:1}` — เทียบต้นทาง `{TEX_IMAGE:3, AO:1, MAPPING:3, BUMP:2, DISPLACEMENT:1, HUE_SAT:1}`. สิ่งที่หาย: (ก) AO+HUE_SAT บน Base, (ข) BUMP ทั้งสองชั้น, (ค) `DISPLACEMENT` scale 0.5, (ง) ภาพ `Carpet Set-002` ทั้งใบ. ที่แย่กว่าหาย: **`Carpet Set-003` เป็น height map (ต้นทางเสียบเข้า BUMP.Height) แต่ของเราเสียบผ่าน `NORMALMAP`** — grayscale อ่านเป็น tangent normal ≈ ผิวแบน+เอียงเพี้ยน. เส้นทาง: `build_room.py:12790-12814` rug ACQUIRED → `place_model` (`build_room.py:11888` `import_scene.gltf`) — glTF แบก node tree ของ Blender ไม่ได้ จึงเหลือ baseColor+normal slot. บรรทัด 12814 พิมพ์ "vendor weave kept" — จริงครึ่งเดียว: เก็บได้แค่ diffuse. **นี่คือกลไกของ "พรมแบน" (ORD-2026-08-25b) — ไม่ใช่ vendor ทำมาแบน.** ทางแก้: append material จาก `.orig.blend` โดยตรง (memory note disk-retention ระบุอยู่แล้วว่า .orig.blend = "Cycles material ของจริง") หรือ rebuild 4 ชิ้นที่หายหลัง import.
2. **sheen เราเรียกเกินแถบมืออาชีพทั้งกอง แล้วพึ่ง clamp:** `_SHEEN_CAP = 0.4` (`build_room.py:2988`) ขณะที่ caller ส่ง 0.5–1.0 — `bed_mattress` 0.5, `bed_duvet` 0.7, `bed_pillow` 0.8 (`build_room.py:9778-9781`), cushion boucle 1.0 (`build_room.py:8413`), towel 0.7 (`:7266`). แถบจริงจาก 46 แถว: **0.02–0.3, ฐานนิยม 0.2** — เพดาน clamp ของเรา (0.4) ยังสูงกว่า max ที่มืออาชีพตั้งบนผ้าเตียง (0.3). ค่าที่ผ่าน clamp แล้วทุกตัว = 0.4 = ทุก textile หลักแบนเท่ากันหมดที่เพดาน แทนที่จะไล่ระดับ 0.07–0.3 ตามชนิดผ้าแบบ corpus.
3. **เราไม่มี true displacement เลยทั้ง repo:** grep `ShaderNodeDisplacement` = 0 ตัวสร้างจริง; ที่ใกล้สุดคือเอา Displacement map มาเป็น bump height dist 0.0004 (`build_room.py:2305-2308`). มืออาชีพใช้ node DISPLACEMENT 16% ของ material โดย scale 0.1–3 mm บนผ้า / 3–10 mm บนไม้·หิน·โป๊ะ (idiom #3) — และ mesh ฝั่งเขาหนาแน่นพอรับ (28,651 v/m² median ของ whole_bed vs เตียงเรา). พรมต้นทางตั้ง 0.5 ทั้งที่ mesh มี 210 v/m² — น่าจะพึ่ง displacement_method โหมด bump (dump ไม่บันทึก → คำถามพิกเซล #1).
4. **weave เราเป็น noise isotropic — ไม่มีทิศเส้นด้าย:** `_woven` slub/weave (`build_room.py:3049-3058`) scale เท่ากันทุกแกน; ตัว anisotropic เดียวคือ crease field (`:3112-3125`). Corpus: fabric procedural ใช้ mapping **[2,11,2]** (ยืด 5.5×) หรือ `TEX_MAGIC` เป็นลายทอตรง ๆ; และแม้ image-based ก็มี mapping ไม่สมมาตร ([12,12,1], [6,6,1], [4.5,4.5,1] ที่ `17aff0ff` — z=1 เพราะ UV). ของเรา `_FABRIC_TILE_M = 0.85` (`build_room.py:2675`) คูณ BOX projection เท่ากันสามแกน (`:3216-3217`).
5. **velvet เราไม่มี facing term:** row `velvet` = bump 0.30 + sheen_rough 0.40 (`material_presets.py:451-455`); ทั้ง `_woven`/`_solid` ไม่เคยสร้าง LAYER_WEIGHT/FRESNEL/BSDF_SHEEN (grep ไม่พบใน build_room.py) ขณะที่ corpus มี facing term ~17% และ velvet ระดับดีทำสองโทนตามมุม (idiom #5). MA-01 scatter-identity ของ studio เองบอกว่า signature ต้องต่างชนิด — ตอนนี้ velvet เรากับ linen ต่างกันแค่ตัวเลข ไม่ต่างโครง.
6. **ย้อมสี: เราคูณ (MULTIPLY, darken-only ceiling law) — เขา HUE_SAT:** `_pbr_material` base_tint (`build_room.py:2578-2583`) และ `_woven` (`:3084-3090`) เป็น multiply; ข้อดีเราคือสีที่ sign ไว้เป็นเพดานแน่นอน — เก็บไว้ — แต่ตอน "แปลงโทนของซื้อ" (retint) HUE_SAT ของ corpus รักษา contrast ของ texture ได้ดีกว่า multiply ที่กดทั้ง histogram.
7. **สิ่งที่เราทำถูกแล้ว (ยืนยันด้วยเลข, อย่าแตะ):** (ก) colorspace — `_img_node` (`build_room.py:2546-2551`) ตั้ง Non-Color/sRGB ตรงตามวินัย 99.6% ของ corpus; (ข) VRAM cap 1–2K (`build_room.py:11899`) ไม่ได้ต่ำเกิน — มืออาชีพใช้ 512–2048 เป็นหลัก; (ค) rough map เต็ม amplitude บน mapped cloth (`_CLOTH_ROUGH_LINKED`, `build_room.py:2692`, D-035) ตรง pole ของ corpus ที่ Rough=IMG แทบทุกผ้า image-based.

## กฎ transferable จัดอันดับ

1. **Ingest ที่ทิ้ง node tree = ทิ้งของที่จ่ายเงินซื้อ.** พรมแบนเพราะ glTF round-trip เหลือ 2 node จาก 15: AO, BUMP×2, DISPLACEMENT(0.5), HUE_SAT, และ map 1 ใน 3 หาย — แถม height map ถูกเสียบเป็น normal map. ของซื้อจาก BlenderKit ต้อง append จาก `.orig.blend` หรือมี checker เทียบ node_hist ก่อน/หลัง ingest (`0fd746ae` vs `_ours_p2r91` คือ negative control สำเร็จรูป).
2. **sheen ผ้า = 0.02–0.3, ฐาน 0.2 — ไล่ตามชนิดผ้า ไม่ใช่ชนเพดานเท่ากันหมด** (46 แถวจริง: denim 0.021 < suede 0.074 < velvet 0.08 < herringbone 0.099 < jersey 0.157 < corduroy/teddy 0.2 < gingham 0.245 < waffle/cotton 0.3). ลด `_SHEEN_CAP` → 0.3 และแก้ caller ที่ส่ง 0.5–1.0 ให้ส่งค่าที่ตั้งใจจริง.
3. **displacement จริงหลักไมโคร-มิลลิเมตร:** ผ้า 0.1–1.5 mm (หมอนบางแถว 3 mm), ไม้ 3 mm, หิน 5 mm — บน mesh ระดับ 10k+ v/m². เพิ่ม material displacement ใน `_woven`/`_pbr_material` ด้วย scale แถบนี้ (เตียงเรา sim mesh หนาแน่นพอแล้ว).
4. **ทิศเส้นด้ายมาก่อนความละเอียด:** ยืด noise แกนเดียว ~5× (mapping [2,11,2]) หรือใช้ TEX_MAGIC เป็นโครงทอ — 512 px + mapping 3–5 ของ corpus ชนะ texture ใหญ่ที่ไม่มีทิศ.
5. **velvet = facing-dependent albedo (LAYER_WEIGHT→MIX สองโทน) + BSDF_SHEEN mix, sheen weight ต่ำ (0.08)** — ไม่ใช่ bump และไม่ใช่ sheen สูง.
6. **ของกลมเล็ก = cage เบา + BEVEL(2 seg)+SUBSURF(2):** carafe 898 verts อ่านเป็นแก้วเป่าได้; แก้วต้อง Rough ~0.03 + noise bump จาง ไม่ใช่ 0.0.
7. **จุก/วัสดุเม็ดละเอียด procedural = VALTORGB ซ้อนสองชั้นบน NOISE เดียว** (สี+bump จาก field เดียวกัน — law เดียวกับ _woven ของเรา, ยืนยันอิสระ).
8. **โลหะ procedural: NORMALMAP<VALTORGB<NOISE>> ที่ mapping 30 + rough ~0.23** — micro-dent บนโลหะเรียบ ราคา 6 node (`01bb0e45` metall).

## สูตร port ลง material_presets (วัน 26)

- **Recipe A — "Procedural Fabric" (garment, ใช้ซ้ำ 4 แถวใน 3 asset):** Mapping scale (2,11,2) → NOISE×2 + WAVE + VORONOI×2 → สาย MIX 9 ตัวรวม field → VALTORGB แยก 3 เส้น: Base, Rough, Metallic(ผ่าน INVERT — ค่าต่ำมาก), + BUMP<field> → Normal; Sheen 0.2. ค่า stop ของ ramp อ่านจาก dump ไม่ได้ — **เปิด `.orig.blend` ของ `03ede500` วัน port** (ห้ามเดา).
- **Recipe B — throw ผ้าถัก (`b89bc1af`):** MAGIC(โครงทอ) + NOISE(slub) ใน tree เดียว (trace เห็น MIX<NOISE> เข้า Base); Rough const 0.9455; BUMP สองชั้นต่อ chain — ชั้นไหนรับ MAGIC/NOISE dump ไม่บอก, เปิด `.orig.blend` วัน port; Sheen 0.2; mapping (2,2,2).
- **Recipe C — velvet (`b8359da9` + `17aff0ff`):** LAYER_WEIGHT(facing) → MIX(albedo โทนลึก/โทนสว่าง); MIX_SHADER(BSDF_SHEEN, PRINCIPLED); Rough จาก map ผ้า generic 2K; Sheen weight 0.08.
- **Recipe D — พรม (แก้ ingest ก่อน แล้วถ้าจะปั้นเอง):** slab หนาจริง ~26 mm (ขอบพรมจบด้วยความหนา geometry ไม่ใช่ระนาบ) + Base=AO<HUE_SAT<diffuse>> + BUMP height + DISPLACEMENT — ขน 100% อยู่ในชั้น shader, geometry 210 v/m² พอ.

## คำถามที่ต้องพิสูจน์ด้วยพิกเซล

1. **rug ds=0.5:** vendor ตั้ง displacement_method โหมดไหน (dump ไม่บันทึก)? ถ้า 'BUMP' โหมด — displacement 0.5 ทำหน้าที่เป็น bump แรง; ถ้า true — 1,536 quad จะเป็นลูกคลื่น. ต้อง render A/B จาก `.orig.blend` (นอกเหนือ scope วันนี้ — ห้ามเปิด Blender ในงานศึกษานี้).
2. **พรมหลังซ่อม ingest จะหาย "แบน" จริงไหม** — AO+bump+displacement คืนแล้วขนอ่านออกที่ระยะ hero camera หรือยังต้องเพิ่ม particle/fiber? เลขบอกไม่ได้ว่า 671×996 px พอสำหรับ close-up.
3. **sheen 0.2 vs 0.4 ของเรา** เห็นต่างจริงบนแสง soft ของห้องเราแค่ไหน (ห้องนี้เคยกลืน bump honest มาแล้ว — `material_presets.py:404-410`).
4. **Recipe A/B อ่านเป็นผ้าจริงที่ระยะเตียงหรือไม่** — corpus ใช้กับ garment แขวน/throw ระยะกลาง; ยังไม่มีหลักฐานพิกเซลว่า scale ไหนของ MAGIC ใช้ที่ระยะ 1.5 m.
5. **Metallic บนผ้า (Recipe A ต่อ INVERT เข้า Metallic)** — ตั้งใจหรือความสกปรกของ tree? ต้องเปิดไฟล์ดูค่าจริงก่อน port.
6. **HUE_SAT vs MULTIPLY retint** — บนของซื้อสีเข้ม (เคส retint_fabric) อันไหนรักษา weave contrast ดีกว่า: ต้อง A/B ครอปเดียว.

---
VERIFIED 2026-09-01: ตรวจ 49 ข้อ ผิด 18 แก้แล้ว 18 (verifier ฝ่ายค้าน, เทียบกับ probe dump ทุกค่า — ผิดหนักสุด: corpus คือ 71 dump ไม่ใช่ 43 · facing term 11% ไม่ใช่ ~17% (LAYER_WEIGHT∩FRESNEL ซ้อน 12 แถว) · recipe-A คือ 4 แถวใน 3 asset ไม่ใช่ 4 asset · ผ้า procedural 6 แถวไม่ใช่ 9 (อีก 4 คือ hook/สี) · fabric pack ต่อ output จริง 5 map ไม่ใช่ 4 (disp ต่ออยู่ — ขัดกับ idiom #3 ของโน้ตเอง) · rug 7.3 ตร.ม. ไม่ใช่ 3 · displacement 34/216 ไม่ใช่ 35 · แถบ sheen/disp มีแถวนอกกรอบที่โน้ตไม่ได้บอก · b89bc1af Base/BUMP layer เกินหลักฐาน trace — ย้ายเป็นเงื่อนไขเปิด .orig.blend)
