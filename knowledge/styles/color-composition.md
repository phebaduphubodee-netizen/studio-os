# ทฤษฎีสี องค์ประกอบภาพ และการจัดฉาก / Color Theory, Composition & Staging (Interior)

> PROVENANCE: distilled from `knowledge/_inbox/nlm-design-systems/color-composition.md`,
> NLM notebook a5a43395 turns 6, 12, 13, 14 (supporting values from turn 7)
> (see `_inbox/nlm-design-systems/qa-history.json` + `sources-manifest.md`),
> date 2026-07-02, tier REFERENCE.
> The inbox file's `[n]` markers have no exported marker→source map; where the
> notebook answer names the work, the manifest title is cited; otherwise the
> citation is "notebook a5a43395 turn N".
>
> ADDED 2026-07-13 (second staging pass, tier REFERENCE):
> §11 (colour & mood) is distilled from
> `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` §7 (lines 128–130).
> §2's corroboration note and §2.1 come from
> `knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf` p.3.
> Both are AI deep-research outputs; INTERIOR-DESIGN-KB.md:7 states its own
> posture — "AI DR fabricates citations/numbers; treat everything here as
> strong-but-unaudited until it matters for a client". That caveat is inherited
> by everything promoted from it here.

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

> Corroboration (NOT independent verification): a second REFERENCE-tier DR
> report carries the rule with identical carriers — "sixty percent of a room
> operates as the dominant color (walls, large rugs), thirty percent as the
> secondary color (furniture, window treatments), and ten percent as the accent
> color (accessories, artwork)"; values unchanged
> (`knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf`
> p.3, staged 2026-07-03). Source-independence is NOT established: both carriers
> are LLM deep-research outputs, and the PDF footnotes this rule to its own web
> marker [26] = *Interior Design Rules — Ideal Organizing + Design* (a design
> blog; not held in-repo). Treat as a second REFERENCE-tier witness, not as
> confirmation from an authority.
>
> Oversized-treatment exception: when a floor-to-ceiling curtain is too large
> for the 30 % role, see **§12** — Albers' ground-subtraction lets it join the
> 60 % ground instead of displacing another secondary element.

### 2.1 กฎเลขคี่ / Odd Rule (การจัดกลุ่มของตกแต่ง / object groupings)

> PROVENANCE (this subsection + the corroboration note above only): distilled
> from `knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf`
> p.3 (DR report, REFERENCE tier, staged 2026-07-03) — separate from this file's
> NLM provenance block at the top.

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

> ⚠️ **SUPERSEDED FOR STUDIO RENDERS** by `knowledge/rendering/render-defaults.md`
> **§3 — Camera & composition**, which holds the camera values the pipeline
> actually runs: focal length **24–50 mm** for interiors; and under that section's
> **"Studio deviations (gate evidence wins)"** block, the **26 mm** small-room lens
> as an A/B-proven deviation from that band, and eye-camera height **~1.15 m**
> rather than the general **1.35–1.65 m**, on M3.2 designer evidence.
> (Anchored by section + value, deliberately not by line number.) The table below is
> the **photographic-reference tier** (Adams / Shulman via the notebook); where it
> conflicts with a gate-proven studio value, render-defaults wins. Do not quote
> "28 mm or 35 mm" from here as the studio lens rule.

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
- The notebook gave no numeric camera height (only "eye-level") and no
  TV-viewing-distance data. Both are answered elsewhere in the vault — use those,
  not this file (anchored by section + value, deliberately not by line number):
  camera height → `knowledge/rendering/render-defaults.md` **§3 — Camera &
  composition** (general **1.35–1.65 m**) and that section's **"Studio deviations"**
  block (studio, gate-proven **~1.15 m** eye camera, which outranks the general
  value); TV viewing distance →
  `knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md`
  **§TV / flat-screen viewing (SMPTE, THX)** — viewing distance = diagonal
  **× 1.6** (SMPTE 30°) / **× 1.4** (THX 36°) / **× 1.2** (THX 40°), and that
  section's **1.5–3.0 m** comfort band. Scope: the gaps listed in this section are
  the NOTEBOOK's, not the vault's.
- No Thai statutory values anywhere in the notebook (turns 8–10 answered from
  model memory, explicitly flagged ungrounded) — use `knowledge/codes-th/`.
- No paint-system values (LRV, NCS/Munsell notation) in the color sources.

## 11. สีกับอารมณ์ และปฏิสัมพันธ์แสง×สี / Colour & mood; the light × colour interaction

> PROVENANCE (this section only): distilled from
> `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` §7, lines 128–130
> (staged 2026-07-01, promoted 2026-07-13). Tier **REFERENCE**.
> **Single-source:** the KB tags the light×colour bullet *(NLM)* — i.e. one of its
> two deep-research vendors — and its own cross-vendor ledger (§9, lines 170–171)
> does **not** list colour/mood among the both-vendor-confirmed items. The KB
> heads this section "brief — design element, **human-kept**" (:128): these are
> design-judgement heuristics for palette + mood language, **not** measurable
> values and **not** QA-gate material. Numbered §11 to keep §1–§10 stable for the
> files that cite them.

### 11.1 Hue → mood (palette language)

| Hue family | Effect (as stated by the source) | Design consequence given |
|---|---|---|
| Warm — red / orange / yellow | stimulate | red **raises appetite → dining rooms** |
| Cool — blue / green | calm / focus | — |
| Neutral — white | airy | supporting role |
| Neutral — brown | grounding | supporting role |
| Neutral — black | drama | supporting role |
| Neutral — gray | balance | supporting role |

- Light **value** governs perceived spaciousness: **light = airy,
  dark = intimate** (`INTERIOR-DESIGN-KB.md`:129).
- The source gives no mechanism, no magnitudes, and no exceptions for any of the
  above — it is an associative list. Do not manufacture a rationale for it, and
  do not turn "red → dining" into a rule that a dining palette must be red.

### 11.2 Light × colour interaction (the one operational rule here)

From `INTERIOR-DESIGN-KB.md`:130, verbatim in substance:

- **Warm light** enriches reds / oranges **but dulls blues**, and **can make skin
  sallow**.
- **Cool light** pops blues / greens.
- **Brightness sets saturation.**
- → **Rule: never judge a finish colour independent of its light source.**

**Pipeline consequence (studio application — an inference from the two rules
above, NOT a statement in the source):** a palette is only meaningful together
with the CCT of the zone it sits in. §7 of this file records residential zones at
**2200–3000 K (warm)** (REFERENCE tier, notebook a5a43395 turn 12); §11.2 says warm
light *dulls* blues — and the source never defines "dull". **If** that means
desaturation, a blue/green scheme specified for a warm residential zone **may** read
less saturated in the render than it does on the swatch — so re-judge it under the
zone's actual CCT before sign-off. This is the same failure §3 (simultaneous
contrast) and §4 (Albers' colored-paper test: perception changes with "quantity,
area size, and lighting") describe for adjacency — light is the third context that
moves a colour.
Second, non-reconciled witness: the same staged KB gives a **different** warm band —
"**2700–3000K** warm (living/bed/dining = cozy)" (`INTERIOR-DESIGN-KB.md`:105).
Neither band is gate-proven; do not treat either as fixed.

**Not carried:** **§7 of the KB** — the section distilled here — gives no LRV, no
NCS/Munsell notation, no CRI/TM-30 figure and no per-hue Kelvin recommendation (it
is the associative list above plus the light×colour bullet). Lighting-quality
metrics and surface reflectances are subject matter for `knowledge/lighting/` and
`knowledge/materials/`, not for this file; §7 above holds the only CCT values this
file carries.

## 12. เมื่อผ้าม่านใหญ่จนล้นบทบาท 30% / When a window treatment outgrows its 30 % role (Albers ground-subtraction)

> PROVENANCE (this section only): distilled 2026-07-21 from
> `knowledge/_inbox/nlm-element1-curtain-2026-07-16.md` (NLM notebook a5a43395
> turns 19–20 of 20; snapshot in the sibling `-qa-history.json`), staged
> 2026-07-16, tier **REFERENCE**. Albers citations = *Interaction of Color*
> (manifest `28fa10cb-2bd`), the same source behind §3–§4. First consumer:
> PRJ-2026-002 element 1 (decision D8 — the curtain joins the ground); see the
> unit for the full A/B record. Numbered §12 to keep §1–§11 stable for the
> files that cite them.

§2 assigns window treatments to the **30 % secondary** — but the sources
contain **no rule** for the case where a floor-to-ceiling treatment is so
large it would displace another 30 % element, and **no rule** for choosing a
textile value relative to the wall it hangs against. Both refusals are
recorded in the unit; the refusal is the useful half — do not cite this file
as if the 60-30-10 literature resolved the conflict. What Albers grounds
instead:

- น้ำหนักสายตาของสีถูกกำหนดโดยปริมาณพื้นที่ / a colour's visual weight is set
  by its **"extension in area"**; increasing the quantity of a colour
  "visually reduces distance" — the mass advances, producing "nearness".
- **The lever / คานงัด:** *"any ground subtracts its own hue from colors which
  it carries"*, and *"the light of a ground subtracts in the same way that its
  hue does"* — so a light-valued textile hung against a light-valued ground
  has the visual diversion between them **"reduced if not obliterated
  visually"**.
- Consequence: ผ้าม่านผืนใหญ่ไม่จำเป็นต้องนับเป็นสีรอง 30 % — **it can be
  assigned to the 60 % ground** by choosing its value at (near) the wall's
  value, leaving the 30 % free for the element the scheme actually wants
  there.
- A complete boundary-vanish requires exact **"equal light intensity"** — the
  sources call this rare and difficult, and for fabric it is deliberately NOT
  the goal: keep a hair of value difference so the textile still reads as
  fabric, with separation carried by texture and the fold's self-shading.
  (That last move is a **studio inference** recorded in the unit's decision
  rationale, not an Albers statement.)

**Fold geometry: refused in full.** The notebook answered verbatim that none
of it is covered (fullness ratio, carrier spacing, wave depth, hem height,
track-to-glass offset) — every such number is **CONVENTION tier**, never
citable as grounded. The vault-held hard numbers are the stack/pocket depths
in `knowledge/ergonomics/casework-fixture-clearances-th-practice.md`
(single-layer S-fold stack **130 mm**; pocket ≥ 150 mm single-layer / ≥ 250 mm
two-layer — from the owner's NITAS TESSILE sheets). "Stack depth ≈ drawn wave
depth" is a studio inference, convention not citation.

Still GAP after this DR (do not fabricate): fullness ratio · carrier spacing ·
hem-to-floor gap · track-to-glass offset · sheer transmission values for a
BSDF · curtain drawing-symbol convention (ASA 2554 carries no curtain / track /
pelmet layer at all — `knowledge/classifications/thai-cad-layers-asa2554.md`).

## 13. ทางออกจากกับดักไม้โทนเดียว / Escaping the mono-material (mono-timber) trap (Albers, Postell)

> PROVENANCE (this section only): distilled 2026-07-21 from
> `knowledge/_inbox/nlm-element1-dressing-wall-2026-07-16.md` (Ask 4, the
> unit's GROUNDED-CITED half — Albers *Interaction of Color* `28fa10cb`,
> Postell *Furniture Design* `109b32e1`, Interior-Design-Knowledge-Structuring
> `56678948`; NLM notebook a5a43395), tier **REFERENCE**. Same Albers source
> as §3–§4 and §12. First consumer: PRJ-2026-002 element 1 (oak signature
> wall). Numbered §13 to keep §1–§12 stable for the files that cite them.

- **Quantity is not just area — "quantity = size × recurrence" (Albers).** The
  same wood on the *floor* (60 %) *and* a feature wall (30 %) is what
  manufactures a mono-timber monopoly: the material recurs, so its visual
  quantity exceeds either surface alone. **Escape move:** demote the floor's
  visual weight (a large soft rug) so the wood reads as the **30 % secondary**;
  keep metal as the **10 % accent**. This extends §2's 60-30-10 with a concrete
  de-monopoly lever.
- **Offset a light-wood field (the §12 ground-subtraction lever, applied in
  reverse):** warm-painted walls *wash the wood out* — the ground subtracts its
  own hue from the timber. Put the 60 % in **matte, cool-toned off-white
  plaster / limewash / textured linen**: low-frequency texture rests the eye
  and lets the grain read.
- **Wood vs black-framed glass = intentional separation, not a clash.** Albers'
  hard-boundary rule (§4): a black-alu frame *frames* the wood; the extreme
  tonal contrast reads as a structural statement, not bleeding.
- **Many functions → few masses.** Slats read as a calm continuous field
  ("stripes are overlooked as almost shapeless"); group N functional
  sub-elements into an **odd number of masses** (3) for a legible, un-busy wall
  (the §2.1 Odd Rule applied at wall scale).

Scope note: the unit's CONVENTION halves (slat rhythm/section, shadow-gap and
floating-joinery detailing, tropical veneer/finish behaviour) are **not**
carried here — they are outside-corpus rules-of-thumb held REFERENCE-in-unit
until verified vs AWI / supplier / Thai practice. The ergonomics half is
distilled separately at `knowledge/ergonomics/residential-clearances.md`
(dressing-wall section).


## 14. วัสดุเป็นสเปกตรัม ไม่ใช่แค่สัดส่วน / A material palette is a SPECTRUM, and colour is chosen against its backdrop

> PROVENANCE: promoted 2026-08-28 from
> `knowledge/_inbox/video-study/2026-08-28-material-spectrum-and-the-32mm-system-5gfcLreD2ZM.md`
> `knowledge/_inbox/video-study/2026-08-28-what-a-real-project-hands-over-w2Gw5rzFKjA.md`
> and, for §14.3, `knowledge/_inbox/video-study/2026-08-28-why-a-room-feels-off-Sz4TC-VJ2PQ.md`.
> Source video ids: `5gfcLreD2ZM` (a materials primer — **that video carries a sponsor read,
> disclosed**) · `w2Gw5rzFKjA` (a studio preparing a client sign-off) · `Sz4TC-VJ2PQ`.
> Tier REFERENCE. §2's 60/30/10 rule is unchanged; this section adds the axis that decides
> whether a correct ratio can still fail.


> **RELATIONSHIP TO §13, READ IT FIRST.** §13 already answers the mono-timber trap with
> Albers' *quantity = size × recurrence* and gives the escape moves: demote the floor with a
> large soft rug so the wood reads as the 30 % secondary, and **keep metal as the 10 % accent**.
> This section does not repeat that. It adds the AXIS that explains why §13's metal accent is
> the right instrument rather than one option among many, and it names a failure §2's ratio
> arithmetic cannot detect.

### 14.1 THE SPECTRUM
> *"I think the **key to a successful material palette is to focus on CONTRAST**, and to think
> about your materials **on a spectrum**."*

Soft/natural to harsh/manmade, as he orders it:

**woven textiles · wood → brick · natural stone · textured ceramics · leather · some
concrete → linoleum · painted elements · fibreglass · acrylic · laminate → glass · glossy
tiles → METALS**

He corrects his own word mid-explanation, and the correction is the useful part: *"maybe a
better word for it is like **sharper** or like **harsher**… we can all agree that metal feels
harsher than fabric."*

**Position is set by FINISH, not by material class:** *"a highly reflective polished marble
floor is going to feel way harsher than a more raw matte limestone floor tile. So it's not as
simple as saying stone is in one place."* A satin oak and a gloss-lacquered oak are different
palette entries.

### 14.2 WHY A CORRECT RATIO CAN STILL FAIL
> *"the tried and true easiest way of doing this is to bring in some nice **wood furniture
> with some fabric upholstery**, and then **sort of CUT IT with a much harsher material** —
> like a metallic table for example — because when you bring in materials from the **further
> ends of that spectrum** you get this interesting **tension and contrast** that just makes a
> space feel more deep and ultimately more balanced."*

> **A room can satisfy 60/30/10 by area and still read wrong if all three tiers sit at the
> same end of the spectrum** — which is the same failure §13 describes as a monopoly, seen
> along a different axis: §13 counts RECURRENCE of one material, this counts DISTANCE between
> the materials chosen. Before adjusting any ratio, ask whether the palette contains
> anything from the harsh end AT ALL, and whether it is large enough to read at the frame's
> scale. That is a different measurement from a pixel share against a target ratio, and §2
> cannot detect it.

### 14.3 A COLD ROOM IS A TEXTILE PROBLEM — three independent sources
| Source | Wording |
|---|---|
| studio principal, on a TV room | *"it's got **quite a cold feel**… **there's no soft furnishings, it's got a lot of glass, a lot of wood**"* — the fix is linen wallpaper and heavily textured bouclé |
| designer, on a bedroom | *"there's **no colour** in this room, that's why it **feels cold**"*, and *"**anything wood, any natural material is immediately going to bring warmth**"* |
| designer, on a bedroom | *"**Everything is very hard**… it just feels very rigid"* — the prescription is an upholstered frame and curtains |

The three do not agree on the CAUSE (absent colour vs absent soft goods vs hard materials),
and they do agree on the REMEDY: **add textile mass.** Not more wood, and not a hue change.

### 14.4 A COLOUR IS CHOSEN AGAINST WHAT IT SITS IN FRONT OF
> *"when you're picking the leather fabrics you have to be quite careful… **you always have to
> think what it's going to be in front of**. It's quite an insipid sort of taupe — sometimes it
> looks pink, sometimes it looks grey — so **if you don't get a really clear contrast**, the
> bar stool could **clash** with that. So by going white, you know it's going to have a
> **definite contrast** there."*

This is §3's simultaneous-contrast principle applied as a SELECTION rule rather than a
warning: an object's colour is specified for its separation from its own backdrop. Every
object standing against a single dominant wall material is subject to it.

### 14.5 COUNTS CAN BE LOW, AND A SCHEME CAN LOOK POOR AS A FLAT-LAY
*"just keeping it very minimal on the cushions — **we've only got three cushions in this
entire room**"*, and on a deliberately restrained bedroom scheme: *"it's more about the
**form**… very serene and simple. **In a tray, like you say, that doesn't look that
impressive.**"*

Two correctives for anyone judging a scheme by its board: a delivered room can be sparse in
decorative objects, and a flat-lay is not the room. Weigh against the opposite finding
recorded in `knowledge/rendering/practitioner-consensus-eye-light-camera.md` — an archviz
reviewer asking for a rendered closet to be **fuller** — **the sparse/full answer differs by
object class, and neither is a general rule.**
