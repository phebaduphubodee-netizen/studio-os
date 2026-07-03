# ค่าแสง IES และโน้ตการจัดแสงภายใน / IES profiles & interior lighting notes (Discord)

> PROVENANCE: distilled from Discord "MY DATA PEAT" (forum channels #ข้อมูลแบ่งปัน and #3dmax-tip), threads:
> `knowledge/_inbox/discord/MY-DATA-PEAT/ข้อมูลแบ่งปัน/002_ค่าแสง-IES/thread.md` (+ images in that thread's files/),
> `knowledge/_inbox/discord/MY-DATA-PEAT/3dmax-tip/008_Lighting-Master-Interior-Krupipe/thread.md` (+ image in that thread's files/).
> Pulled 2026-07-03, tier REFERENCE. Source = studio practitioner notes ("Peat"), not a published standard.
> AUTHORITY: statutory Thai minimums in `knowledge/codes-th/` OUTRANK every value here; where a value
> overlaps a legal floor, the law wins and this file defers to it.

**อำนาจโฟโตเมตริก / Photometric authority cross-ref:** ค่ามาตรฐาน lux สำหรับที่พักอาศัย และ authority
สำหรับ CCT / layering / IES อยู่ที่ `knowledge/lighting/residential-lighting.md` (ซึ่ง cross-ref
กฎหมาย lux floors ใน `knowledge/codes-th/mr39-fire-sanitation-ventilation.md` ตาราง 3).
ไฟล์นี้เป็นโน้ตปฏิบัติของสตูดิโอ (สี Kelvin→RGB ที่ใช้ตั้งค่าไฟใน Enscape + แคตตาล็อกรูปทรงลำแสง IES)
— ไม่ใช่ค่ากำหนด lux. / For residential lux design values and IES/CCT authority use
`knowledge/lighting/residential-lighting.md`; this file is studio working practice for setting light
colour in the renderer and choosing an IES beam shape, not a lux specification.

---

## 1. ค่าสีของแสงไฟ (Kelvin → RGB) / Light colour temperature to RGB
Source thread: `ข้อมูลแบ่งปัน/002_ค่าแสง-IES/`.
ค่าเหล่านี้คือค่า RGB/HEX ที่ใช้ตั้งสีหลอดไฟตามอุณหภูมิสี (CCT) เวลาเรนเดอร์ด้วย Enscape.
ทดสอบโดย "Enscape NDWORK / อ.แชมป์". / RGB/HEX values for tinting a light source to a given
colour temperature when rendering in Enscape; tested by "Enscape NDWORK / อ.แชมป์".

Transcribed from image `ข้อมูลแบ่งปัน/002_ค่าแสง-IES/files/043358_image.png`:

| อุณหภูมิสี / CCT | ชื่อเรียก / label | HEX | R | G | B |
|---|---|---|---|---|---|
| 1800 K | กันยุง / Anti Mosquito | #FF7700 | 255 | 119 | 0 |
| 2700 K | วอร์มไวท์ / Warm White | #FF8222 | 255 | 130 | 34 |
| 3000 K | วอร์มไวท์ / Warm White | #FF933E | 255 | 174 | 62 |
| 4000 K | คูลไวท์ / Cool White | #FFC382 | 255 | 195 | 130 |
| 6000 K | คูลเดย์ไลท์ / Cool Day Light | #FFFFFF | 255 | 255 | 255 |
| 6500 K | เดย์ไลท์ / Day Light | #C9E2FF | 201 | 226 | 255 |

Additional CCT points typed in the thread body (post [7], text — NOT from an image):

| อุณหภูมิสี / CCT | HEX (as given) | R | G | B |
|---|---|---|---|---|
| 3500 K | ffc68a | 255 | 149 | 65 |
| 4500 K | — | 255 | 192 | 127 |

- Note: for 3500 K the source lists HEX `ffc68a` alongside R255/G149/B65; these disagree
  (`#ffc68a` = R255/G198/B138). Transcribed verbatim as the source gave them — verify against
  intended CCT before use.
- Note: the Enscape image has the same self-contradiction at 3000 K — HEX `#FF933E` decodes to
  R255/G147/B62, but the printed RGB is R255/G174/B62 (G disagrees). Both values are transcribed
  exactly as printed on the image; use the RGB triplet as authoritative for renderer tinting.
- These are renderer light-tint values, not lux/illuminance. For lux and CCT-per-zone design
  authority see `knowledge/lighting/residential-lighting.md` (residential warm 2200–3000 K;
  2700 K typical warm baseline).

## 2. แคตตาล็อกรูปทรงลำแสง IES / IES beam-shape catalogue
Source thread: `ข้อมูลแบ่งปัน/002_ค่าแสง-IES/` — image `files/633297_iesguide.jpg`, plus an IES file
pack on Google Drive (`https://drive.google.com/drive/folders/1OdKvl2v4U5ha4b36HRKOCxVIQP2Oof39`)
and a SketchUp scene `files/616168_c866775c3c7fc5f9.skp`.

- `iesguide.jpg` is a **visual preview grid of 30 IES beam profiles** (numbered 1–30), each shown
  as a wall-wash light cone against a wall/floor — a picking index for the downloadable .ies pack.
- **The image contains NO numeric data** — no lux, no beam-angle degrees, no candela figures are
  printed on it. It is a beam-shape reference only. Numbers 1–30 are just profile indices.
- Practical use (studio practice): browse the grid, note the profile number whose cone shape
  (tight spot vs wide wash, symmetric vs grazing) matches the fixture, then load the matching .ies
  from the Drive pack. For actual photometric magnitudes (lumens/lux/beam angle) rely on the real
  .ies file header and `knowledge/lighting/residential-lighting.md`, not this preview.

## 3. เวิร์กโฟลว์จัดแสงภายใน — Lighting Master Interior (Krupipe) / Interior lighting workflow
Source thread: `3dmax-tip/008_Lighting-Master-Interior-Krupipe/`.

A 7-part video course "Lighting Master Interior" by Krupipe (พี่ปิ๊ป / "3D EASY BY KRUPIPE"),
shared as YouTube links only. The thread carries **no written setup values** — it is a pointer to
the course. Episodes:

| EP | หัวข้อ / topic | link |
|---|---|---|
| EP.01 | ความรู้เรื่องแสงอย่างละเอียด / light fundamentals in depth | https://youtu.be/5UEl7Wminms |
| EP.02 | set up light | https://youtu.be/H8QlrtyRg-U |
| EP.03 | (—) | https://youtu.be/MjramtC-6IQ |
| EP.04 | (—) | https://youtu.be/quKuZNJGr70 |
| EP.05 | (—) | https://youtu.be/apA6PPFFFz4 |
| EP.06 | (—) | https://youtu.be/V4GGtet7-vM |
| EP.07 | (—) | https://youtu.be/T0ngud5Es2s |

- The lone attachment (`files/539924_...n.png`) is just the "3D EASY BY KRUPIPE" logo — no data.
- Kept as a reference-video pointer; distil concrete setup values into
  `knowledge/lighting/residential-lighting.md` only after watching, if any survive review.

## ช่องว่าง / Gaps in source (do not fill from memory)
- No lux / illuminance targets, no beam-angle degrees, no candela values anywhere in either thread
  or their images. Do NOT infer them here — use `knowledge/lighting/residential-lighting.md` and
  `knowledge/codes-th/mr39-fire-sanitation-ventilation.md` (statutory lux floors).
- CCT↔RGB table is Enscape-specific renderer tinting; it is not a spectral or CRI/TM-30 spec.
- The 30 IES profiles are unlabelled by beam type — matching a profile to a real fixture is by eye.
