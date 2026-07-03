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

## โปรโตคอลหรี่ไฟและระบบควบคุม / Dimming & control protocol taxonomy

> PROVENANCE (this section only): distilled from
> `knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf`
> p.8 (DR report, REFERENCE tier, staged 2026-07-03) — separate from this
> file's NLM provenance block at the top. NOT Authority; no statutory content.

| โปรโตคอล / protocol | ชนิดสัญญาณ / signal | ความละเอียดการควบคุม / control granularity | การใช้งาน / typical use | source |
|---|---|---|---|---|
| **0-10V** | analog | หรี่แบบ logarithmic ทั้งวงจร / logarithmic dimming | งานหรี่ไฟทั่วไป / general dimming | Interior Design Knowledge Structuring.pdf p.8 |
| **DALI / DALI-DT8** | digital addressable (Digital Addressable Lighting Interface) | ควบคุมรายโคมแม่นยำ / precise individual (per-fixture) control | ระบบที่ต้อง address โคมแยกดวง / addressable systems | Interior Design Knowledge Structuring.pdf p.8 |
| **DMX512** | digital multiplexing | ควบคุมไดนามิกความเร็วสูง / dynamic control | แสงเชิง entertainment / dynamic, entertainment-style lighting | Interior Design Knowledge Structuring.pdf p.8 |

- **กฎการจับคู่ / matching rule:** control และ dimming protocol ของโคม **ต้อง**
  match กับ electrical/dimming infrastructure ที่มีอยู่ของอาคาร — โคมที่ระบุสเปกต้อง
  interface กับ architectural dimming system ได้โดยไม่เกิด **voltage drops หรือ
  flickering** / fixture control gear must match the building's existing dimming
  infrastructure (Interior Design Knowledge Structuring.pdf p.8).
- Corroboration: หน้าเดียวกันยืนยันค่า CCT bands ของไฟล์นี้อิสระอีกทาง —
  warm residential **2200–3000 K** vs cool commercial **4000–5700 K** — และ
  การใช้ TM-30 (**Rf**/**Rg**) แทน CRI พร้อม track **R9 สูง** สำหรับ reds;
  values unchanged (Interior Design Knowledge Structuring.pdf p.8).
- **GAP:** คำแนะนำเลือกโปรโตคอลรายประเภทห้อง/สเกลพักอาศัย (ห้องไหนควรใช้
  0-10V vs DALI vs DMX512) — corpus ไม่ให้ / protocol-per-room-type guidance
  absent from source.

## QA ความสอดคล้องของแสงในเรนเดอร์ / Render light-coherence QA checks (photoreal review vocabulary)

> PROVENANCE (this section only): distilled from
> `knowledge/_inbox/id-project-corpus/Automated Production QA Scoring Systems.pdf`
> pp.4–5, 12 and `knowledge/_inbox/id-project-corpus/Automated Vision QA for
> Interiors.pdf` pp.6–7 (DR reports, REFERENCE tier, staged 2026-07-03).
> Vocabulary สำหรับรีวิวภาพเรนเดอร์ photoreal — ไม่ใช่ gate; ดู threshold caveat ท้ายหัวข้อ.

Generative artifacts ด้านแสงที่พบบ่อย: แหล่งแสงขัดแย้งกัน, เงาวิ่งทิศที่เป็นไปไม่ได้
ทางฟิสิกส์, และการหาย contact shadows ทั้งหมด (Automated Production QA Scoring
Systems.pdf p.4). Checks ต่อไปนี้คือคำศัพท์รีวิวมาตรฐานของสตูดิโอ:

1. **การจำแนกเงา / Shadow classification** — **attached shadow** เกิดบนผิวส่วน
   ที่หันหนีแหล่งแสง; **cast shadow** เกิดเมื่อ occluder บังแสงจากผิวอีกผืน.
   ภายใน cast shadow: **umbra** = ถูกบังจาก direct illumination เต็มส่วน,
   **penumbra** = โซนไล่ระดับจากการมองเห็นแหล่งแสงบางส่วน โดยความนุ่มของ
   penumbra ถูกกำหนดโดย **spatial extent ของแหล่งแสง** (แหล่งใหญ่ → penumbra
   กว้าง) (Automated Production QA Scoring Systems.pdf p.4).
2. **Specular–shadow agreement / single-source convergence** — ทิศของ specular
   highlight ต้องชี้กลับไปแหล่งแสงเดียวกับที่ cast shadow บอก: ลาก vector จากปลาย
   เงาผ่านจุด anchor ของวัตถุ และจาก centroid ของ highlight ออกไป — ทุก vector
   ต้องตัดกันที่พิกัด 3D เดียว (ตำแหน่งแหล่งแสงโดยนัย). ถ้า highlight บอกแหล่งแสง
   ที่เบี่ยงจากแหล่งที่เงาบอกเกิน threshold → ภาพ **structurally incoherent** /
   composited จาก illumination priors ที่ขัดแย้งกัน (Automated Production QA
   Scoring Systems.pdf p.5; Automated Vision QA for Interiors.pdf p.7 — ค่า
   ตัวอย่างเชิงสาธิต "e.g., > 2.3°" กู้จาก embedded figure, illustrative เท่านั้น
   ไม่ใช่ gate).
3. **ลำดับความสว่างของแหล่งแสง / Source-brightness ordering** — แหล่งแสงรอง
   (โคมตั้งโต๊ะ, sconces) **ห้าม**สว่างกว่าแหล่งแสงหลัก (หน้าต่างบานใหญ่ในซีน
   กลางวัน); ตรวจด้วย localized contrast analysis (Automated Vision QA for
   Interiors.pdf p.6).
4. **Inverse-square falloff** — cast shadows, reflections, ambient-occlusion
   regions ต้องเป็นไปตาม **inverse-square laws** ของโลกจริง; area light ที่อยู่ชิด
   ผิวโดยไม่มี falloff สมจริง → highlight แข็งผิดธรรมชาติ = anomaly (Automated
   Vision QA for Interiors.pdf p.7, 3DLP benchmark).
5. **FFT separation** — ใช้ Fast Fourier Transform แยก **low-frequency
   illumination gradients** ออกจาก **high-frequency texture details** เพื่อแยกแยะ
   "เงา" (shadow instances) ออกจาก "วัสดุสีเข้มโดยกำเนิด" (intrinsic material
   darkening) โดยไม่ทำลาย semantic content (Automated Production QA Scoring
   Systems.pdf p.5).

**Threshold caveat (สำคัญ — ห้ามเติมตัวเลขเอง):** ตาราง QA gate ใน Automated
Production QA Scoring Systems.pdf p.12 export ค่าคณิตศาสตร์เป็นภาพที่ถูก clip ขอบ
เซลล์ — text extraction ได้เซลล์ว่าง. ตรวจระดับพิกเซล 2026-07-03: รอดมาเพียง
**ขอบล่างของ soft band = 15°** ("15° ≤ Δ_light_angle ≤ …" ถูกตัดหลังจากนั้น);
ค่า **hard gate** ("Δ_light_angle < …") และ **ขอบบนของ soft band**
**กู้ไม่ได้ / unrecoverable** — ห้าม invent และห้าม backfill ด้วย pattern inference.
ค่า "> 2.3°" ของ Vision QA p.7 เป็นเพียง "e.g." ประกอบการอธิบาย ไม่ใช่ production
gate. Gate จริงใดๆ ต้องเสนอผ่าน **PR ต่อ `qa/thresholds.yaml` เท่านั้น** —
ตัวเลขในหัวข้อนี้เป็น REFERENCE vocabulary.

## ช่องว่างข้อมูล / Gaps in source (ห้ามเติมเอง — ingest เพิ่มเท่านั้น)

1. ค่า lux ออกแบบรายห้อง/รายงานจากตาราง IES — ไม่มีใน excerpts (turn 2).
2. อัตราส่วน ambient:task:accent เชิงตัวเลข — ไม่มี (turn 2).
3. ค่าตัวเลข CRI / R9 / Rf / Rg ขั้นต่ำหรือเป้าหมาย — ไม่มี (turn 2).
4. CCT รายห้องและ CCT ของ task lighting — ไม่มี (turn 2).
5. นิยามละเอียดของ Birn "motivation" และ "exposure discipline" — excerpts มีเพียง
   high-level summaries (turn 2 / inbox lighting.md).
6. ค่า divergence threshold เชิงตัวเลขของ light-coherence QA — hard gate ของ
   Δ_light_angle และขอบบนของ soft band ถูก clip ใน PDF export กู้ไม่ได้
   (รอดเพียงขอบล่าง 15°; Automated Production QA Scoring Systems.pdf p.12) —
   ห้าม invent; gate จริงต้องผ่าน PR ต่อ `qa/thresholds.yaml`.
7. คำแนะนำ dimming protocol รายประเภทห้อง (0-10V vs DALI vs DMX512 ต่อ
   living / bedroom / bath ฯลฯ) — corpus ไม่ให้ (Interior Design Knowledge
   Structuring.pdf p.8 ให้เพียง taxonomy + กฎ match infrastructure).
