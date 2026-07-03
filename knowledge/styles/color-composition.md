# ทฤษฎีสี องค์ประกอบภาพ และการจัดฉาก / Color Theory, Composition & Staging (Interior)

> PROVENANCE: distilled from `knowledge/_inbox/nlm-design-systems/color-composition.md`,
> NLM notebook a5a43395 turns 6, 12, 13, 14 (supporting values from turn 7)
> (see `_inbox/nlm-design-systems/qa-history.json` + `sources-manifest.md`),
> date 2026-07-02, tier REFERENCE.
> The inbox file's `[n]` markers have no exported marker→source map; where the
> notebook answer names the work, the manifest title is cited; otherwise the
> citation is "notebook a5a43395 turn N".

## ลำดับอำนาจ / Authority order

กฎหมายชนะเสมอ / Thai law wins: this file carries **no statutory values**. Any
dimensional, ventilation, or daylight-opening requirement comes from
`knowledge/codes-th/mr55-residential-dimensions.md` and
`knowledge/codes-th/mr39-fire-sanitation-ventilation.md`, which outrank
everything here. (Notebook turns 8–10 could NOT ground Thai regulations —
never cite this file for law.)

## 1. ชนิดความกลมกลืนของสี / Color harmony types (วงจรสี, Albers)

Six primary harmony types for organizing an interior palette
(notebook a5a43395 turn 6, single unmapped marker [1]; the ask was scoped to
the COLOR THEORY PDF `f6354b19-6bf` + Albers *Interaction of Color*
`28fa10cb-2bd` — a wheel-based harmony taxonomy is consistent with the COLOR
THEORY source; do not attribute this list to Albers specifically):

| Harmony type | โครงสี |
|---|---|
| Complementary | สีคู่ตรงข้าม |
| Split-complementary | สีตรงข้ามแบบแยก |
| Double complementary (Tetrad) | สีตรงข้ามคู่ (สี่สี) |
| Analogous | สีข้างเคียงในวงจรสี |
| Triadic | สามสีระยะห่างเท่ากัน |
| Monochromatic | สีเดียวหลายน้ำหนัก |

## 2. กฎ 60/30/10 การกระจายสีในห้อง / 60-30-10 color distribution rule

"Golden ratio" of spatial color distribution (notebook a5a43395 turn 6):

| สัดส่วน / Share | Role | ตัวอย่างพื้นผิว / Typical carriers |
|---|---|---|
| 60% | Dominant color สีหลัก | walls, large rugs / ผนัง พรมผืนใหญ่ |
| 30% | Secondary color สีรอง | furniture, window treatments / เฟอร์นิเจอร์ ผ้าม่าน |
| 10% | Accent color สีเน้น | artwork, small accessories / งานศิลปะ ของตกแต่งชิ้นเล็ก |

> Corroboration: independently confirmed by a second DR source with identical
> carriers — 60% dominant (walls, large rugs), 30% secondary (furniture, window
> treatments), 10% accent (accessories, artwork); values unchanged
> (Interior Design Knowledge Structuring.pdf p.3, tier REFERENCE, 2026-07-03).

### 2.1 กฎเลขคี่ / Odd Rule (การจัดกลุ่มของตกแต่ง / object groupings)

> PROVENANCE (this subsection + the corroboration note above only): distilled
> from `knowledge/_inbox/id-project-corpus/Interior Design Knowledge
> Structuring.pdf` p.3 (DR report, REFERENCE tier, staged 2026-07-03) —
> separate from this file's NLM provenance block at the top.

- Grouping objects in **odd numbers** creates visual asymmetry, forcing the
  eye to move across the composition and generating rhythm / จัดของตกแต่ง
  เป็นกลุ่ม**จำนวนคี่** เกิดความไม่สมมาตรตามธรรมชาติ สายตาเคลื่อนผ่าน
  องค์ประกอบ เกิดจังหวะ (Interior Design Knowledge Structuring.pdf p.3).
- Machine-checkable: **odd-count validation on decorative arrays** (styling
  slots) — the source describes JSON-schema furniture layouts whose decorative
  arrays must populate with odd-numbered entity counts
  (Interior Design Knowledge Structuring.pdf p.3).
- GAP: single-source; corpus gives no group-size bounds (3 / 5 / 7?), no
  exception rules for deliberately symmetrical or formal/classical styling
  (even pairs), and no per-slot applicability list — re-source before
  promoting odd-count from advisory check to hard QA gate.

## 3. สีข้างเคียงและ simultaneous contrast / Adjacency & perceived color shift

Source: Albers *Interaction of Color* (manifest `28fa10cb-2bd`); notebook a5a43395 turn 6.

- Color is the most **relative** medium: one color reads as two different
  colors depending on its background / สีเดียวกันดูต่างกันตามพื้นหลัง.
- Simultaneous contrast (after-image effect): a ground color "subtracts" its
  own hue and lightness from any object placed on it.
- Practical consequence: a fabric or paint swatch visually shifts the moment
  it sits next to a new adjacent room color — re-judge every pairing in place.

## 4. การทดสอบสีในบริบทจริง / Testing colors in context (colored-paper method)

Source: Albers *Interaction of Color* (manifest `28fa10cb-2bd`); notebook a5a43395 turn 6.

- Perception changes with **quantity, area size, and lighting** — harmonious
  swatches fail when tested in isolation / ทดสอบสีแยกเดี่ยวไม่ได้.
- Albers method: test colors in physical proximity with **colored paper, not
  paint** — exact, unvarying comparison without brushstroke texture.
- Boundary effect / ขอบสี: **soft boundary** (torn paper, draped fabric)
  connects colors; **hard boundary** (cut paper, sharp architectural edges)
  separates them.

## 5. มุมกล้อง เลนส์ และเปอร์สเปคทีฟ / Camera viewpoint, lens & perspective (render/photo)

Sources: Ansel Adams *The Camera* (manifest `fd4ce41c-b78`), Shulman
*Photographing Architecture and Interiors* (manifest `52d018cd-a1c`);
notebook a5a43395 turns 6, 7, 14.

| Rule | ค่า / Value | Note |
|---|---|---|
| Viewpoint / ระดับสายตา | eye-level | natural perspective for interiors (turn 6) |
| Lens for environmental context | 28 mm or 35 mm prime | broad context, minimal edge distortion (turn 6) |
| Lens for natural human perspective | 35–50 mm | staging checklist (turn 14); wider angles only with strict compositional rules (rule of thirds / symmetry) |
| Shallow depth of field for detail shots | f/2.8 | isolates subject, physical bokeh; never arbitrary non-physical blur (turn 7) |
| Perspective control | camera-to-subject distance only | Adams: moving closer enlarges foreground vs background, changes perceived scale (turn 6) |
| Verticals / เส้นดิ่งขนาน | camera back perfectly vertical | prevents converging verticals (walls leaning); in AI render prompts enforce with "tilt-shift" modifier (turn 6) |
| One-point perspective (head-on) | camera back parallel to subject's horizontal AND vertical lines | absolute geometric accuracy (turn 6) |
| Two-point perspective | keep rules strict | essential for spatial coherence in interior rendering (turn 6) |

## 6. ฉากหน้าและโครงสร้างภาพ / Foreground layering & visual structure (Block, Shulman)

Sources: Bruce Block *The Visual Story* 3rd ed (manifest `b3e4e53d-c93`),
Shulman sources; notebook a5a43395 turns 6, 14.

- **Foreground layering / วางวัตถุฉากหน้า:** place an object (plant, chair
  edge, tabletop) in the immediate foreground — creates spatial hierarchy,
  depth, and a realistic scale anchor; head-on empty frames read flat and
  institutional.
- **Block's visual components:** deliberately organize space, line, shape,
  tone, color to structure the frame.
- **Shulman balance:** balance artificial interior lighting with natural
  daylight to show architectural volumes and realistic spatial transitions.
- **Shadow strategy:** high-contrast chiaroscuro or soft ambient occlusion
  forces realistic shadow behavior and establishes 3D geometry.
- **Merger audit / ตรวจเส้นซ้อน:** from the exact camera position, check that
  foreground and background lines do not intersect confusingly; shift camera
  to separate conflicting shapes (turn 14).

## 7. การผสมอุณหภูมิสีข้ามโซนแสง / Mixing color temperature (CCT) across lighting zones

Source: notebook a5a43395 turn 12. (Statutory or IES illuminance values are
NOT in this file — the notebook could not ground residential lux/CRI tables.)

| Zone / บริบท | CCT |
|---|---|
| Residential atmosphere / บ้านพักอาศัย (บรรยากาศอบอุ่น) | 2200–3000 K (warm) |
| Commercial environments / เชิงพาณิชย์ | 4000–5700 K (cool) |

- Rule: CCT must stay **logically consistent within a localized zone** —
  never mix a clinical 4000 K daylight source directly against a warm
  2700 K residential incandescent source in the same zone
  (ห้ามผสมแสงขาว 4000 K กับแสงวอร์ม 2700 K ในโซนเดียวกัน).

## 8. การจัดผ้าบนเตียง / Bed textile layering (styling ผ้าปูเตียง หมอน ผ้าห่ม)

Source: notebook a5a43395 turn 13 — **grounded portions only**.

Grounded (material representation for lived-in look):

- Specify weave + tactile quality explicitly so render engines compute light
  interaction (specularity, subsurface scattering) correctly — e.g.
  **"stonewashed linen, crushed velvet, bouclé, handwoven rattan"**.
- Capturing the **heavy drape of linen** is critical to convincing the eye of
  authenticity / น้ำหนักการทิ้งตัวของผ้าลินิน.
- Add micro-imperfections such as **fabric pilling** so textiles read used,
  not synthetic-smooth.

NOT grounded — dropped (notebook flagged these as outside its sources; do not
cite from here): physical layering techniques — texture mixing across layers,
asymmetrical throw draping, relaxed/non-"karate-chopped" pillows, folding the
duvet back to expose layers. Re-source before use.

## 9. เช็คลิสต์จัดฉากก่อนถ่ายภาพ/เรนเดอร์ / Staging checklist before photography (stylist checklist)

Source: notebook a5a43395 turn 14 (fully grounded, markers [1]–[14]).
Closes the vault's staging/textile gap found in the A/B benchmark.

**A. Camera & geometry / กล้องและเรขาคณิต (Adams, Shulman)**
1. Camera back parallel to walls — verticals stay parallel, architecture reads stable.
2. Audit the frame for mergers; shift camera slightly to separate conflicting shapes, remove intruding elements.
3. Anchor with a foreground object (plant, table edge, chair) for scale and depth.
4. Lens 35–50 mm at eye level; wider only with strict compositional discipline (rule of thirds, symmetrical framing).

**B. Lighting & atmosphere / แสงและบรรยากาศ (Shulman, Birn)**
5. Balance natural daylight with artificial interior light to show architectural volumes.
6. Never a single uniform source — stage three layers: ambient (fill), task (table lamps), accent (features/artwork).
7. Harmonize CCT: no 4000 K daylight clashing with 2700 K incandescent in one zone (see §7).
8. Dictate temporal mood: "golden hour" (warm dramatic shadows) or "blue hour" (warm interior vs cool exterior sky).

**C. Material & textile styling / วัสดุและผ้า**
9. Maximize tactile vocabulary: stonewashed linen, crushed velvet, bouclé, handwoven rattan, honed marble, brushed brass.
10. Introduce human imperfection — "sense of humanity" without a figure: fabric pilling, casual draping, mixed stone chips in terrazzo.
11. Material physics must behave naturally: matte (raw concrete, linen) absorbs light; polished (glass, brass) positioned to catch crisp specular highlights and reflections. Supporting value (turn 7): perfectly smooth (roughness 0.0) or perfectly matte (roughness 1.0) surfaces virtually never exist.

## 10. ช่องว่างข้อมูล / Gaps — what the notebook could NOT answer

- No residential illuminance (lux) or CRI tables per room — turn 2 excerpts
  named IES tables but contained no values; CCT ranges above are all it gave.
- No physical bed-layering technique was grounded (turn 13) — dropped, see §8.
- No numeric camera height (only "eye-level"); no TV-viewing-distance data.
- No Thai statutory values anywhere in the notebook (turns 8–10 answered from
  model memory, explicitly flagged ungrounded) — use `knowledge/codes-th/`.
- No paint-system values (LRV, NCS/Munsell notation) in the color sources.
