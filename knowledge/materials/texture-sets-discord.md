# ชุดเท็กซ์เจอร์/แผนที่พื้นผิว (Discord) / Texture & material-map set index (Discord)

> PROVENANCE: distilled from Discord "MY DATA PEAT". Forum channel **#maps** — threads
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/002_Terrazzo/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/003_View/thread.md`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/004_Fabic/thread.md` (+ images in each thread's files/).
> Per-image pixel dimensions in §1–§3 are transcribed from the attachment metadata in
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/raw.json`,
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/002_Terrazzo/raw.json` and
> `knowledge/_inbox/discord/MY-DATA-PEAT/maps/003_View/raw.json` (`width` / `height` fields).
> Forum channel **#3dmax-tip** — thread `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/002_3D-EAZY/thread.md`
> (+ 26 card images in `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/002_3D-EAZY/files/`,
> dimensions from `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/002_3D-EAZY/raw.json`) → §5.
> The other eight #3dmax-tip threads (`001_ตั้งค่าเริ่มต้นหน้ากระดาษงาน`, `003_เทคนิคภายนอก`,
> `004_เปลี่ยนตำแหน่ง-Autoback-3DMAX`, `005_เทคนิคการเซฟแมทไว้ใช้และแมทสำเร็จรูป`,
> `006_วิธีวางชุด-model-หลาย-ๆ-ชุด`, `007_การทดแทน-Model-หรือการเปลี่ยน-โมเดลตามตำแหน่งเดิม`,
> `008_Lighting-Master-Interior-Krupipe`, `009_วิธีจับ-snap-frozen-line`) were read → DROPPED, see §6.
> Pulled 2026-07-03, tier REFERENCE. Sources = a studio practitioner's dumps ("Peat") + third-party
> course material, not a published standard.
> AUTHORITY: statutory Thai minimums in `knowledge/codes-th/` OUTRANK every value here; where a value
> overlaps a legal floor, the law wins and this file defers to it.

**สิ่งที่ไฟล์นี้เป็น / What this file is.** An INDEX of downloaded reference texture/material-map
image sets captured in the studio's Discord — surface type, image count, pixel size, and files/ paths.
§1–§4 are the #maps image dumps (tile, terrazzo, a 360° panorama link, a fabric bookmark); §5 is the
#3dmax-tip **3D-EAZY "INSIGHT MATERIAL" card set**, which despite living in a folder of .png files is
NOT texture data — it is 26 pages of annotated Corona material-editor screenshots, and it is the only
part of this file that carries shading VALUES.

**เกณฑ์ tileable / Tileability, measured — read before using §1–§2.** The threads themselves say
nothing about the maps (the Tile and Terrazzo message bodies are empty; the word "seamless" does not
appear anywhere in the staged source). An earlier version of this file nevertheless called these sets
"seamless / tileable"; the attachment metadata contradicts that for most of them, so the claim is
WITHDRAWN and replaced by the measured pixel sizes below. Working rule used here (ours, not the
source's): only a **square, power-of-two** image is a *candidate* seamless tile — in these sets that
means 2048×2048, plus the single 1024×1024 file in Terrazzo: **15 of 26** Tile files and **6 of 35**
Terrazzo files (1 × 1024² + 5 × 2048²). The rest (860×700 crops, non-power-of-two squares, 1:2 portrait
captures) are reference PHOTOS. Even for the candidates, seamlessness is unverified — nobody has tiled
them.

## 1. กระเบื้อง / Tile — tile-surface reference images (thread `001_Tile`)
Tile-surface reference images for floor/wall 3D texturing (e.g. herringbone-laid tile, verified in
`files/625060_01-1.jpg` — a dark charcoal herringbone tile field). 26 image files, grouped by a
trailing `SS-N` numbering in each filename (SS = design set, N = image index in that set). Pixel sizes
per file from `001_Tile/raw.json` (`width`/`height`).

| ชุด / Set | จำนวนภาพ / Images | ไฟล์ / files/ (pixel size) |
|---|---|---|
| 01 | 6 | `625060_01-1.jpg` 2048×2048, `038921_01-2.jpg` 2048×2048, `955852_01-3.jpg` 2048×2048, `510034_01-4.jpg` 2048×2048, `610950_01-5.jpg` 2048×2048, `915536_01-6.jpg` **860×700** |
| 02 | 3 | `195257_02-1.jpg` 2048×2048, `036050_02-2.jpg` 2048×2048, `028604_02-3.jpg` **860×700** |
| 03 | 4 | `330580_03-1.jpg` **860×700**, `587391_03-2.jpg` 2048×2048, `708659_03-3.jpg` 2048×2048, `790798_03-4.jpg` 2048×2048 |
| 04 | 2 | `869036_04-1.jpg` **2048×2041**, `590451_04-2.jpg` **860×700** |
| 06 | 3 | `258956_06-2.jpg` **860×700**, `562772_06-3.jpg` **860×700**, `667687_06-4.jpg` **1878×982** (no `06-1` captured) |
| 07 | 2 | `116951_07-1.jpg` **860×700**, `431215_07-2.jpg` **2048×2041** |
| 08 | 5 | `741115_08-1.jpg` 2048×2048, `107998_08-2.jpg` 2048×2048, `825630_08-3.jpg` 2048×2048, `415666_08-4.jpg` **860×700**, `990211_08-5.jpg` 2048×2048 |
| 09 | 1 | `792170_09.jpg` 2048×2048 |

- Total 26 files under `knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/files/`.
- Resolution tally: **15 × 2048×2048** (tile candidates) · 8 × 860×700 · 2 × 2048×2041 · 1 × 1878×982.
  The 11 bold rows are non-square and/or non-power-of-two — treat them as catalogue crops, not maps.
- Set `05` is absent from the capture; set `06` is missing its `-1`. Gaps are in the source, not
  transcription loss.
- No source URL / embed — images were posted as direct Discord attachments only.

## 2. เทอร์ราซโซ / Terrazzo — aggregate-stone reference images (thread `002_Terrazzo`)
Terrazzo / aggregate-stone surface images (grey stone chips in a fine matrix, verified in
`files/148288_490329241_2805120696337686_3197247629696598224_n.jpg` — light-grey terrazzo with
mixed white/grey/dark aggregate). 35 image files. Filenames are the original social-media asset IDs
(pattern `NNNNNN_<fb-asset-id>_n.jpg`); there is no studio set-index numbering on this set.

- **Resolution roster (from `002_Terrazzo/raw.json`): 35 files across 26 DISTINCT pixel sizes.**
  Only **5 are 2048×2048**; 15 are square at some size (1000², 1024², 1417²×2, 1600², 1653², 1766²,
  1800², 1984², 2000², 2048²×5) and 15 are portrait (h > w), including 4 × 1448×2896 and singletons at
  1112×2224, 1280×2560, 850×1639, 768×1655 — i.e. 1:2 phone/social captures. Remaining singletons:
  1547×2048, 1065×2048, 2017×2048, 2048×1536, 1835×1484, 1550×2048, 2048×1025, 1542×2048, 2896×1448,
  2048×1040, 1040×2048 ×2. Range 1.00 MP (1000×1000) → 4.19 MP (2048×2048 / 1448×2896 / 2896×1448).
- Consequence: this set is a terrazzo **look-and-colour library**, not a tile-map library. Only 6 of 35
  are even candidates for tiling under the working rule at the top (the one 1024×1024 + the five
  2048×2048); the rest are re-hosted photographs.

- 35 files under `knowledge/_inbox/discord/MY-DATA-PEAT/maps/002_Terrazzo/files/`:
  `148288_…_n.jpg`, `192396_…_n.jpg`, `142396_…_n.jpg`, `605453_…_n.jpg`, `729825_…_n.jpg`,
  `559130_…_n.jpg`, `791161_…_n.jpg`, `328229_…_n.jpg`, `404823_…_n.jpg`, `471038_…_n.jpg`,
  `325060_…_n.jpg`, `155026_…_n.jpg`, `319815_…_n.jpg`, `089491_…_n.jpg`, `840261_…_n.jpg`,
  `723008_…_n.jpg`, `040814_…_n.jpg`, `768140_…_n.jpg`, `597448_…_n.jpg`, `623924_…_n.jpg`,
  `251843_…_n.jpg`, `353639_…_n.jpg`, `434181_…_n.jpg`, `208342_…_n.jpg`, `779451_…_n.jpg`,
  `895403_…_n.jpg`, `186303_…_n.jpg`, `796010_…_n.jpg`, `386082_…_n.jpg`, `117364_…_n.jpg`,
  `250388_…_n.jpg`, `309930_…_n.jpg`, `831474_…_n.jpg`, `045332_…_n.jpg`, `457620_…_n.jpg`.
  (Full untruncated filenames are in `002_Terrazzo/thread.md` Attachments list.)
- No source URL / embed — direct Discord attachments only. Filename `_n.jpg` asset-ID form indicates
  they were re-hosted from a social-media source, but no origin link was captured in the thread.

## 3. วิว / View — 360° panorama BOOKMARK (thread `003_View`)
A backdrop reference **pointing at** a 360° equirectangular panorama (beach, clear shallow water, blue
sky). The thread contains one PNG and one link embed — **no usable equirect/HDRI is present locally**
(see the two measurements below).

| รายการ / Item | ค่า / Value |
|---|---|
| ไฟล์ / file | `knowledge/_inbox/discord/MY-DATA-PEAT/maps/003_View/files/674265_image.png` (2.0 MB, **1920×1080**) |
| แหล่งที่มา / source URL | https://www.360cities.net/image/ao-pra-beach-thailand-2 |
| ชื่อ / title (embed) | "Ao Pra Beach 360 Panorama \| 360Cities" |
| สถานที่/ช่างภาพ / location & author | Ao Pra Beach, Koh Mak, Thailand — by Jan Koehn (per 360Cities embed) |
| ภาพย่อ embed / embed thumbnail | https://cloudflare1.360gigapixels.com/pano/jan-koehn/02032713_Koh-Mak-Beach-01-tif/equirect_crop_3_1/6.jpg — **1024×346** (`003_View/raw.json` embed `thumbnail.width` / `.height`) |

- The captured PNG is a **1920×1080 framegrab of the 360Cities viewer** (it still shows the
  "www.360cities.net" fullscreen-viewer overlay), not an equirectangular image.
- The equirect URL in the embed is the **1024×346 thumbnail strip**, not a full-res panorama. (An
  earlier version of this file called it "full-res" and truncated the URL with an ellipsis — both
  wrong; corrected above.)
- **Operational conclusion:** this thread yields no HDRI/equirect the render lane can use. Do not wire
  `674265_image.png` in as a world background. Environment lighting keeps coming from the Poly Haven
  HDRI fetch in `pipeline/scripts/assets.py`. To actually use this panorama, the 360Cities page must be
  opened and licensed.

## 4. ผ้า / Fabric ("Fabic") — external fabric reference, no images captured (thread `004_Fabic`)
A fabric-texture reference bookmark. NO image files were downloaded into this thread — only a message
`"Farbicผ้า"` (Thai ผ้า = "fabric") and an external link embed.

| รายการ / Item | ค่า / Value |
|---|---|
| ไฟล์ในเครื่อง / local files | none (no `files/` directory in this thread) |
| แหล่งที่มา / source URL | https://www.pinterest.com/pin/21955116929586306/ |
| ชื่อ / title (embed) | "Yandex Images: search for images in 2025 \| Printing on fabric, Geom…" (Pinterest pin) |

- To use this reference the Pinterest link must be opened and the map downloaded — it is a pointer,
  not a captured asset.

## 5. 3D-EAZY "INSIGHT MATERIAL" — 26 material cards with SHADING VALUES (thread `3dmax-tip/002_3D-EAZY`)

**What these files actually are.** The 26 `.png` in
`knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/002_3D-EAZY/files/` are **not** texture maps. Every one
is a single **1810×2560 portrait page** (uniform across all 26, per `002_3D-EAZY/raw.json`; the
`-scaled` suffix suggests a CMS resize — the thread does not say) titled `INSIGHT MATERIAL`
(`thread.md:16`, "INSIGHT MATERIAL VOL.1") and footed `WWW.3DEASYSTUDIO.COM` — an annotated screenshot
of a **3ds Max + Corona `CoronaPhysicalMtl`** material.

The 26 cards were posted across the **19 lessons 21–39** of the thread's numbered course
(`thread.md:96-214`: Floor 1-4 → Brick 1-2 → Cement 1-2 → Fabric 1-8 → Wall 1-3). It is **not** one card
per lesson: several lessons carry more than one card (in `002_3D-EAZY/raw.json` the message `27. Cement 1`
alone carries cement-1…4, and `28. Cement 2` carries cement-5…6), and the card numbering runs past the
lesson numbering (fabric-9, wall-4 and wall-5 have no correspondingly-numbered lesson — the last fabric
lesson is `36. Fabric 8` and the last wall lesson is `39.Wall 3`). The **47** lesson `.mp4`s were never
downloaded (`thread.md:219-291`, every one marked `SKIPPED (video, use --videos)`), so the cards are the
only surviving payload — and they carry numbers.

**Tier + engine.** REFERENCE, third-party course material (3D EASY STUDIO), **Corona for 3ds Max — not
our engine.** Read the caveats in §5.3 before copying any number into Blender.

### 5.1 ค่าที่อ่านได้จากการ์ด / Values transcribed from the cards
Base-layer values as printed in each card's material editor. "(M)" = the channel is driven by a map,
not the flat number. Every card without exception: **Metalness = Non-metal**, **Base Layer Level = 1.0**,
Anisotropy 0.0.

| การ์ด / Card (file) | Mtl name | Roughness | IOR | Bump | Selected layers / extras printed on the card (not an exhaustive transcription of the page) |
|---|---|---|---|---|---|
| WOOD FLOOR 1 `198056_wood-1-scaled.png` | `wood floor 1-2` | 0.25 (M) | 2.0 | 0.2 (M) | base colour map; map Output: Invert ✓, Output Amount 1.0, RGB Offset 0.0, **RGB Level 1.5** |
| WOOD FLOOR 2 `058148_wood-2-scaled.png` | `wood floor 1-2` | 0.25 (M) | 2.0 | 0.2 (M) | **Clearcoat**: Amount 1.0, IOR 1.5, Roughness 0.0 (M), Bump 10.0 (M = scratch map); Displacement Max 0.001 m; scratch-map Output: RGB Offset 0.1, RGB Level 1.0 |
| WOOD FLOOR 3 `430854_wood-3-scaled.png` | `wood floor 2` | 0.0 (M) | 2.0 | 1.0 (M) | map Output: Output Amount 1.5, RGB Level 1.0 |
| WOOD FLOOR 4 `043192_wood-4-scaled.png` | `wood floor 2-2` | 0.0 (M) | 2.0 | 10.0 (M) | **Clearcoat**: Amount 1.0, IOR 2.0, Roughness 0.0 (M), Bump 0.5 (M); Displacement Max 0.001 m; Output Amount 1.5 |
| BRICK 1 `117531_Brick-1-scaled.png` | `brick 1` | 0.65 (M) | 1.6 | 1.0 | dark base colour (painted brick); **Displacement Max 0.03 m** (Texture = M); Output: Invert ✓, **Output Amount 0.6** |
| BRICK 2 `380595_Brick-2-scaled.png` | `brick-2` | 0.05 (M) | 1.5 | 1.0 (M) | **Displacement Max 0.05 m**, Texture = normal map; Output: Enable Color Map ✓ (Mono curve), **Output Amount 3.0** |
| Cement 1 `101854_cement-1-scaled.png` | `cement 1` | 0.3 | 1.8 | 0.2 (M) | — |
| Cement 2 `028075_cement-2-scaled.png` | `cement 2` | 0.3 (M) | 1.8 | 0.2 (M) | Output: Output Amount 1.5, RGB Level 1.5 |
| Cement 3 `057547_cement-3-scaled.png` | `cement 3` | 0.3 (M) | 1.8 | 0.2 (M) | Output: Enable Color Map ✓ (Mono curve) |
| Cement 4 `560384_cement-4-scaled.png` | `cement 4` | 0.3 (M) | 1.8 | 0.2 (M) | Output: **RGB Offset 0.3**, RGB Level 1.5, Enable Color Map ✓ |
| Cement 5 `709269_cement-5-scaled.png` | `cement 5` | 0.2 (M) | 1.8 | 0.2 (M) | Output: **RGB Offset 0.2**, RGB Level 1.5, Enable Color Map ✓ |
| Cement 6 `747210_cement-6-scaled.png` | `cement 6` | 0.2 (M) | 1.8 | 0.2 (M) | **Clearcoat**: Amount 1.0, IOR 1.5, Roughness 0.0 (M), **Bump 85.0** (M); Displacement Max 0.001 m; Output: **RGB Offset 0.2**, RGB Level 1.5; second Output: Enable Color Map ✓ (Mono curve) |
| Fabric 1 `100798_fabric-1-scaled.png` | `fa-1` | 0.75 | 1.5 | 1.0 (M) | base colour = **Falloff** (Front dark blue / Side lighter blue, both 100.0; Type Perpendicular/Parallel; Direction Viewing (Camera Z-Axis)) + Mix Curve |
| Fabric 2 `157842_fabric-2-scaled.png` | `fa-2` | 0.75 (M) | 1.5 | 1.0 (M) | same Falloff base; roughness-map Output: Invert ✓, Output Amount 1.5 |
| Fabric 3 `931420_fabric-3-scaled.png` | `fa-3` | 0.75 | 1.5 | 1.0 (M) | Falloff with **two bitmaps** in Front/Side (`fabric 1-1.jpg` dark / `fabric1-2.jpg` light) + **CoronaColorCorrect**: Brightness −0.14, Contrast 8.035, Hue 180.0, Saturation 0.0, Gamma 1.0, Temperature 6500.0 |
| Fabric 4 `629319_fabric-4-scaled.png` | `fa-4` | 0.75 | 1.5 | 1.0 (M) | **Sheen**: Amount 1.0, **Roughness 0.45**, pale-cream colour; Falloff base + CoronaColorCorrect as fa-3 |
| Fabric 5 `668776_fabric-5-scaled.png` | `fa-5` | 0.75 | 1.5 | 1.0 (M) | base colour = **Composite, 2 layers**, each a Falloff (darker / lighter red), Layer 2 opacity 100.0 masked by a greyscale grunge map (labelled *สำหรับกันสี* = for colour break-up) |
| Fabric 6 `833845_fabric-6-scaled.png` | `fa-6` | 0.75 | 1.5 | 1.0 (M) | **Sheen**: Amount 1.0, **Roughness 0.6**, pink colour; Composite/Falloff base as fa-5 |
| Fabric 7 `803596_fabric-7-scaled.png` | `fa-7` | 0.75 | 1.5 | 1.0 (M) | flat green base colour (no map); **Sheen**: Amount 1.0, **Roughness 0.4**, light-green colour; Clearcoat Amount 0.0 |
| Fabric 8 `693195_fabric-8-scaled.png` | `fa-8` | 0.75 | 1.5 | 1.0 (M) | flat green base; **Sheen**: Amount 1.0, **Roughness 0.4 (M)** — driven by a grunge map (Output RGB Offset 0.6) — light-green colour |
| Fabric 9 `183113_fabric-9-scaled.png` | `fa-9` | 0.75 | 1.5 | **3.0 (M)** | chenille/velvet look; **Displacement Min level 0.01 m** (Texture = normal map); **Sheen**: Amount 1.0, Roughness 0.5 (M), pale-pink colour; Output Amount 1.5 |
| Wall 1 `007815_wall-1-scaled.png` | `wall-1-1` | 0.75 (M) | 1.5 | 0.5 (M) | flat off-white base; roughness-map Output: Enable Color Map ✓ (Mono S-curve) |
| Wall 2 `367612_wall-2-scaled.png` | `wall-1-2` | 0.75 (M) | 1.5 | 0.5 (M) | **Displacement Max 0.1 m**, Texture = normal map |
| Wall 3 `952943_wall-3-scaled.png` | `wall-1-3` | 0.75 (M) | 1.5 | 0.5 (M) | **Displacement Max 0.1 m**, Texture = **Gradient** (Color #1 black / #2 grey / #3 white with `Map #264 nor-1.jpg`; **Color 2 Position 0.35**; Gradient Type Linear); roughness-map Output: Enable Color Map ✓ (Mono S-curve) |
| Wall 4 `355611_wall-4-scaled.png` | `wall-1-4` | 0.75 (M) | 1.5 | 0.5 (M) | base colour = **Gradient** (Color #1 white / #2 grey / #3 black with `wall-1.jpg`; **Color 2 Position 0.35**; Linear) **and** the same Gradient in Displacement (Max 0.1 m) |
| Wall 5 `743178_wall-5-scaled.png` | `wall1-5` | 0.75 | 1.5 | 0.5 (M) | base colour = **Composite**: L1 plaster grunge, L2 = CoronaColor solid **sRGB 8-bit R:99 G:130 B:184** (`#6382B8`) at opacity 100.0, masked by a scratch grunge |

### 5.2 รูปแบบที่ซ้ำทั้งชุด / Patterns that hold across the whole set (as printed, not inferred)
- **Dielectric only.** Metalness = Non-metal on all 26 cards; no metal card exists in this set.
- **IOR is constant per surface class**: wood **2.0** (4/4) · brick 1.5–1.6 · cement **1.8** (6/6) ·
  fabric **1.5** (9/9) · wall **1.5** (5/5).
- **Roughness by class**: wood 0.0–0.25 (glossy, always map-driven) · brick 0.05 or 0.65 · cement
  0.2–0.3 · fabric **0.75** (9/9) · wall **0.75** (5/5).
- **Fabric = Sheen + Falloff.** Every fabric card that is not a plain diffuse uses the same two moves:
  a **Sheen layer** (Amount 1.0, Roughness 0.4–0.6, tinted a lighter shade of the base) and a base
  colour built from a **Falloff (front/side)** — a darker colour facing the camera, a lighter one at
  grazing angles. Fabric 5/6 stack two Falloffs in a **Composite** with a grunge mask for colour
  break-up.
- **Wall = one plaster map, four different re-uses.** Same 0.75 / 1.5 / 0.5 base every time; the
  variation comes from where the greyscale map is wired (roughness → colour-mapped curve; displacement
  → normal map; displacement or base colour → 3-colour **Gradient** with Color-2 Position 0.35, Gradient
  Type Linear). The cards print the Gradient's colours and Color-2 Position only — no orientation and no
  stated purpose.
- **The card's own greyscale rules of thumb** (printed in Thai beside each map thumbnail, repeated on
  most cards): a bump/roughness map is *ขาว เทา ดำ — **ยิ่งเข้มยิ่งชัด*** ("white, grey, black — the
  darker, the more pronounced"), and on the reflection map *สียิ่งเข้มดำจะยิ่งเห็นความใสความสะท้อน*
  ("the darker the colour, the more gloss/reflection shows"). **Many — not all — cards** add that the
  input can be pushed further with **CoronaColorCorrect** (*ใช้CoronaColorCorect ปรับเพิ่มได้*): it is
  printed on wood-1, brick-2, cement-6, fabric-3 and fabric-4, and is absent from brick-1, wall-3 and
  wall-5 (which print only *สามารถปรับแต่งเพิ่มเติมภาพที่ Output* and/or the greyscale note). Cards
  spot-checked, not all 26 counted.

### 5.3 ข้อควรระวังก่อนย้ายค่ามาที่ Blender / Caveats before porting a number
These are Corona UI values. Ported blind they will be wrong:
- **Bump is NOT 0–1 here.** Corona's bump is a multiplier that the cards drive to **10.0** (wood-4),
  **85.0** (cement-6 clearcoat) and 3.0 (fabric-9). Do not paste those into a Blender bump *Strength*
  (0–1). Only the *relative* intent transfers (clearcoat scratches want a very strong bump).
- **IOR wood = 2.0 is an artistic reflection boost, not measured wood.** The studio's own
  Principled-BSDF starting values give wood IOR **1.52** (`knowledge/materials/bsdf-material-presets.md`
  §1); on conflict our own table and the bounds it defers to win. Treat the card's 2.0 as "Corona look",
  not as physics.
- **Output / RGB Level / Enable Color Map curves are Corona texmap controls**, not BSDF inputs; their
  Blender equivalents are a ColorRamp / Map Range on the map, and the numbers do not carry over 1:1.
- **Displacement is in metres and is real geometry** (0.001 m wood, 0.03 m brick 1, 0.05 m brick 2,
  0.1 m walls). These are usable as *scale intent* for a Blender displacement/bump-height, and they are
  the one class of number in this set already in our unit system (mm/m).
- What DOES transfer cleanly: the **roughness bands per surface class**, **Sheen for fabric**, the
  **Falloff front/side colour trick**, the **map-wiring recipes**, and the greyscale rules of thumb.

## 6. อ่านแล้วไม่รับเข้า / Read and deliberately NOT promoted (#3dmax-tip threads 001, 003–009)

`002_3D-EAZY` is the only #3dmax-tip thread promoted above. The other eight were opened and judged, not
overlooked. Recorded so the next reader can tell "dropped" from "never read".

| ต้นทาง / Source | เนื้อหา / What it is | เหตุผลที่ตัดออก / Why dropped |
|---|---|---|
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/001_ตั้งค่าเริ่มต้นหน้ากระดาษงาน/thread.md` | 5 `.png` UI screenshots and one line of text, *ตั้งค่ากล้อง* ("camera setup", `:18`); no values in the thread body | 3ds Max page/camera **UI setup**. Images opened 2026-07-13 (ledger pass): viewport-layout + Corona 9 Render Setup panels — operator settings only, still no dimension, rule or supplier fact. Not executable in a Blender + generative-image pipeline. PRIVACY: one screenshot's title bar shows a client/project name — images stay local (gitignored), never quote into an external call |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/003_เทคนิคภายนอก/thread.md` | One YouTube link + embed title *สอน Corona render ห้องนอน* (`:16-17`) | **Bare pointer** — no transcribed content in the thread; nothing citable |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/004_เปลี่ยนตำแหน่ง-Autoback-3DMAX/thread.md` | Two `.mp4` attachments, both `SKIPPED (video, use --videos)` (`:20-21`); no text | Moving 3ds Max's **Autoback** folder — a 3ds Max preference; and the videos were never downloaded, so there is no content to read |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/005_เทคนิคการเซฟแมทไว้ใช้และแมทสำเร็จรูป/thread.md` | One YouTube link + embed (`:16-18`), "3dsMax Tips Ep.1" on saving/reusing materials | **Bare pointer**, no transcribed content; 3ds Max material-library UI operation |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/006_วิธีวางชุด-model-หลาย-ๆ-ชุด/thread.md` | One YouTube link + embed (`:16-20`) on replacing many instanced models in one click | **Bare pointer**, no transcribed content; 3ds Max UI operation |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/007_การทดแทน-Model-หรือการเปลี่ยน-โมเดลตามตำแหน่งเดิม/thread.md` | YouTube link + embed with three steps for the 3ds Max **Substitute modifier** (`:16-25`) | 3ds Max **UI operation**, no Blender equivalent wired here; no dimension, rule or supplier fact |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/008_Lighting-Master-Interior-Krupipe/thread.md` | Seven YouTube links, EP.01–EP7 of a lighting course (`:18-50`), + one `.png` | **Bare pointers** — the lighting content is in the videos, none of it transcribed in the thread. Our lighting values come from `knowledge/lighting/` |
| `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/009_วิธีจับ-snap-frozen-line/thread.md` | One tip: tick **Snap to frozen objects** and Snap will catch frozen objects (`:19-20`), + one `.jpg` | 3ds Max **snap-setting trivia**; not executable in our pipeline, no design payload |

## หมายเหตุ / Notes
- The four #maps threads are single-author reference dumps by "Peat" (2025-04-20 → 2025-10-22); the Tile
  and Terrazzo message bodies are empty (images only), so surface identity comes from the images
  themselves and the thread names. The #3dmax-tip 3D-EAZY thread (2024-05-17 → 2024-05-20) is likewise
  posted by "Peat" but the content is third-party course material.
- Nothing here is a statutory or dimensional claim; §1–§4 are a downloaded-asset catalogue and §5 is a
  shading-value reference. Before any of these maps or values feed a client deliverable, confirm
  licensing/origin — the Terrazzo and Fabric sources are third-party re-hosts, and the 3D-EAZY cards are
  someone else's paid course pages (index them, do not republish them).
- The gitignored binaries in these threads are only manifested by each thread's `thread.md` / `raw.json`;
  those two files are the sole record of the filenames and pixel sizes quoted above.
