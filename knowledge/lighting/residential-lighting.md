# แสงสว่างที่พักอาศัย / Residential Lighting — CCT · Layering · TM-30 (REFERENCE)

> PROVENANCE: distilled from `knowledge/_inbox/nlm-design-systems/lighting.md`,
> NLM notebook a5a43395 turns 2, 6, 7, 12, 14 (see
> `knowledge/_inbox/nlm-design-systems/qa-history.json` +
> `knowledge/_inbox/nlm-design-systems/sources-manifest.md`), date 2026-07-02,
> tier REFERENCE — NOT Authority.
> `[n]` markers are notebook-internal citations; the export has no exact
> [n]→title map, so cite "notebook a5a43395 turn N". The notebook's manifest
> contains IES standards listings (IES Standards / IES Lighting Handbook 10th
> ed. / IES Lighting Library) and Jeremy Birn, *Digital Lighting & Rendering*
> (see sources-manifest.md); the render/camera turns also draw on the
> notebook's photography sources — per-turn attribution is not recoverable.

## อำนาจกฎหมาย / Authority cross-ref — กฎหมายชนะ / law wins

ค่าความสว่างขั้นต่ำตามกฎหมาย (lux floors, 50–300 lux ตามประเภทพื้นที่) คือ
`knowledge/codes-th/mr39-fire-sanitation-ventilation.md` ตาราง 3 — ค่านั้นเป็น LAW:
ค่าออกแบบเพื่อความสบายตาในไฟล์นี้ห้ามต่ำกว่า floor ตามกฎหมาย และเมื่อขัดกัน codes-th ชนะเสมอ
/ statutory lux floors outrank everything in this file; design comfort values never go below them.

## อุณหภูมิสีต่อโซน / CCT per zone (สี Kelvin, อุณหภูมิสี)

| โซน / zone | CCT | source |
|---|---|---|
| ที่พักอาศัยทุกโซน / residential warm atmosphere | **2200–3000 K** | notebook a5a43395 turn 2 [2]; turn 12 [2] |
| baseline หลอดไส้อบอุ่นบ้านพัก / typical warm residential incandescent | **2700 K** | notebook a5a43395 turn 2 [3] |
| เชิงพาณิชย์ / commercial (ไม่ใช่ค่าพักอาศัย — reserved for commercial) | **4000–5700 K** | notebook a5a43395 turn 12 [2] |

- CCT รายห้อง (living / dining / kitchen / bedroom / bath / corridor) — **GAP**: source
  ระบุเพียงช่วงอบอุ่นรวม ไม่แยกค่าเป็นรายห้อง (turn 2, stated explicitly).
- CCT ของ task lighting (reading / vanity / counter) — **GAP**: not specified in source.

## กฎการผสมอุณหภูมิสี / CCT mixing rules (ห้ามผสม 4000K กับ 2700K ในโซนเดียว)

- อุณหภูมิสีต้องสอดคล้องกันทั้งพื้นที่ / color temperatures must remain logically
  consistent across the space — notebook a5a43395 turn 12 [1].
- **ห้าม**วางแหล่งแสงอุณหภูมิสีขัดแย้งกันใน "โซนเฉพาะที่เดียวกัน" (same localized zone) —
  ถือเป็น severe compositional error — turn 12 [1]; turn 7 [1]; turn 14 [7].
- ตัวอย่างต้องห้าม: หลอด daylight 4000 K (clinical) ชนกับหลอดไส้อบอุ่น 2700 K
  ในโซนเดียวกัน / never mix a clinical 4000K source directly against a warm 2700K
  residential incandescent source — turn 12 [1].

## การจัดแสงสามชั้น / Lighting layers: ambient · task · accent (แสงสามระดับ)

| ชั้น / layer | หน้าที่ / role | source |
|---|---|---|
| Ambient / แสงพื้นฐาน | overall fill illumination ของห้อง | inbox lighting.md [3]; turn 7 [1] |
| Task / แสงใช้งาน | directed lighting สำหรับกิจกรรมเฉพาะจุด (เช่น โคมตั้งโต๊ะ, LED ใต้ตู้) | inbox lighting.md [3]; turn 7 [1] |
| Accent / แสงเน้น | เน้น architectural features หรือ artwork | inbox lighting.md [3]; turn 7 [1] |

- ห้ามพึ่งแหล่งแสงเพดานดวงเดียวแบบสม่ำเสมอ — ลบเงาทิศทาง ทำภาพแบน ดู sterile /
  "AI-generated" — notebook a5a43395 turn 7 [1].
- อัตราส่วนเชิงตัวเลขระหว่างชั้น (layering ratios) — **GAP**: source ไม่ให้ค่า
  (stated explicitly, turn 2 / inbox lighting.md).

## ความถูกต้องของสี / Color rendition — CRI · R9 · TM-30 (Rf / Rg)

- งานพักอาศัยต้องการ **R9 สูง** (rendering reds) — notebook a5a43395 turn 2 [2].
  ค่าตัวเลขขั้นต่ำของ R9 — **GAP**: not given.
- TM-30 metrics — Color Fidelity (**Rf**) + Color Gamut (**Rg**) — ได้แทนที่ระบบ CRI
  เดิมเป็นส่วนใหญ่ เพื่อให้สีดูธรรมชาติและอิ่มตัวพอเหมาะ — turn 2 [2].
  ค่าเป้าหมาย Rf / Rg — **GAP**: not given.
- CRI ขั้นต่ำรายห้อง — **GAP**: not specified in source.

## ความสว่างออกแบบ / Design illuminance (lux) — GAP + law floor

- Source ยืนยันว่า IES ตีพิมพ์ตาราง recommended illuminance criteria แต่ excerpts
  **ไม่มีค่า lux รายห้อง/รายงาน** (living, dining, kitchen counter vs general, bedroom,
  bathroom vanity vs general, corridor, reading) — notebook a5a43395 turn 2 [1]
  (gap stated explicitly). ห้ามเติมค่าเองจนกว่าจะ ingest ตาราง IES จริง.
- ระหว่างรอ: ใช้ floor ตามกฎหมายจาก `knowledge/codes-th/mr39-fire-sanitation-ventilation.md`
  ตาราง 3 เป็นขั้นต่ำ (law wins — ดูหัวข้อ Authority ด้านบน).

## หลักแสงเรนเดอร์ / Render lighting principles (Birn-derived, photoreal)

จาก inbox lighting.md [4–7] (Birn *Digital Lighting & Rendering* listings per manifest)
และ turns 6, 7, 14:

- **Photographic mimicry:** จำลอง optics กล้องจริง — natural color temperatures (K),
  f-stops, exposure times, lens breathing, bokeh — inbox lighting.md [4, 5].
- **Three-point adaptation:** key / fill / backlight ปรับเข้าสภาพแวดล้อม 3D —
  inbox lighting.md [6].
- **Exposure & shadow management:** คุม post-processing exposure, shadow softness —
  inbox lighting.md [5, 7].
- **Linear workflow & compositing:** แยก passes/layers (เช่น highlight pass), linear
  workflow ก่อน composite — inbox lighting.md [5, 6].
- **Advanced techniques:** physically based lighting, subsurface scattering, caustics,
  HDRI — inbox lighting.md [5].
- **Lens / เลนส์:** 35–50 mm สำหรับ natural eye-level perspective — turn 7 [6],
  turn 14 [5]; 28 mm หรือ 35 mm prime (แหล่งระบุสองค่า discrete ไม่ใช่ช่วง)
  สำหรับบริบทกว้างโดยเลี่ยง edge distortion — turn 6 [17].
- **Depth of field:** shallow DoF เช่น **f/2.8** เพื่อ isolate รายละเอียด lived-in,
  ห้าม blur แบบ non-physical — turn 7 [6, 7, 8].
- **Roughness:** ผิว 0.0 (perfectly smooth) หรือ 1.0 (perfectly matte)
  แทบไม่มีจริง — ใส่ micro-imperfections เสมอ — turn 7 [3, 4].
- **Temporal mood:** "golden hour" (เงาอุ่นดราม่า) · "blue hour" (interior อุ่นตัด
  exterior เย็น) · "overcast" (soft neutral) — turn 7 [10], turn 14 [8].
- **Grounding:** บังคับ ambient occlusion + soft contact shadows กันเฟอร์นิเจอร์
  "ลอย" — turn 7 [9, 11].
- **Balance natural vs artificial** (Shulman method): สมดุลแสงประดิษฐ์ภายในกับ
  daylight จากหน้าต่างเพื่อขับ architectural volumes — turn 14 [6].
- **Verticals:** camera back ตั้งฉากจริง / tilt-shift correction กันเส้นดิ่งลู่ —
  turn 7 [12, 7], turn 14 [1].

## ช่องว่างข้อมูล / Gaps in source (ห้ามเติมเอง — ingest เพิ่มเท่านั้น)

1. ค่า lux ออกแบบรายห้อง/รายงานจากตาราง IES — ไม่มีใน excerpts (turn 2).
2. อัตราส่วน ambient:task:accent เชิงตัวเลข — ไม่มี (turn 2).
3. ค่าตัวเลข CRI / R9 / Rf / Rg ขั้นต่ำหรือเป้าหมาย — ไม่มี (turn 2).
4. CCT รายห้องและ CCT ของ task lighting — ไม่มี (turn 2).
5. นิยามละเอียดของ Birn "motivation" และ "exposure discipline" — excerpts มีเพียง
   high-level summaries (turn 2 / inbox lighting.md).
