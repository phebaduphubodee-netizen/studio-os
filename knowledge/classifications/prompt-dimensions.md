# มิติของพรอมต์ / Prompt-Dimension Taxonomy — seven-dimension completeness checklist + vocabulary (Gemini render lane)

> PROVENANCE: distilled from two REFERENCE-tier DR reports staged in
> `knowledge/_inbox/id-project-corpus/`:
> `knowledge/_inbox/id-project-corpus/AI Image Prompt Engineering.pdf`
> (pp. 4–8, 14) and
> `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`
> (pp. 2–4).
> Date 2026-07-03, tier REFERENCE. This file is **prompt vocabulary only** —
> prompt mechanics (slot templates, registry, dispatch) live in `pipeline/`.
>
> INDEPENDENT VERIFICATION 2026-07-13: re-read against the source PDFs by a
> second reader. One OVERSTATED merge claim fixed: the original merge-provenance
> table paired IPE's "Lighting Physics" row with CW's "Atmospherics" row as though
> the two source tables corresponded there. They do not — CW's table contains NO
> lighting row (CW's lighting content is prose, p.4), and its Atmospherics row is
> a mood / emotional-register row (CW p.3), not a lighting one. Splitting that
> false pair moves the checklist from six dimensions to SEVEN (the two tables
> overlap on three rows, not four) and restores the mood vocabulary the false
> merge had silently dropped (now §2.3). Two citations tightened: the aperture
> setting is a discrete pair, "f/8 or f/11", not a range (IPE p.5); the Gemini
> prompting-philosophy cell straddles a page break (IPE pp.7–8, not p.8).
>
> SECOND PASS 2026-07-13 (adversarial): the verification note above itself
> overstated the merge. The two tables' ROW TITLES are disjoint where claimed, but
> their row FUNCTIONS are not: IPE's Lighting Physics row names "mood" (IPE p.5)
> and CW's Atmospherics row names "environmental conditions" (CW p.3). The
> seven-dimension split stands as the studio's declared synthesis; the "only X
> backs Y" and "clean absence" phrasings did not, and are removed. Also fixed: the
> tele band inherits the source's hedge ("typically 85mm or higher", CW p.3), and
> the textile cross-ref repointed from `knowledge/styles/color-composition.md` §8
> (bed-linen layering) to that file's §9 item C.9 (tactile-weave vocabulary).
> The §2 lexicon is now ordered to match the checklist's dimension order.

## ลำดับอำนาจ / Authority order — กฎหมายชนะ / law wins

- **No statutory values here.** Any dimensional, ventilation, daylight-opening
  or ceiling-height requirement comes from `knowledge/codes-th/` (Authority
  tier), which outranks everything in this file. Never cite this file for law.
- **Studio CAMERA POLICY outranks the optics vocabulary below** for the
  studio's own outputs: the gate-evidenced **26 / 28 / 35 / 50 mm** snap set is
  governed by `knowledge/brand-standards/render-quality.md` §4. §2.4 here is
  lexicon, not policy.

## 1. เช็คลิสต์ 7 มิติ / The seven-dimension prompt-completeness checklist

Both source reports independently propose a five-row prompt-component table for
architectural/interior generation: the "Architectural Prompting Variables"
table (AI Image Prompt Engineering.pdf pp. 5–6) and the "lexical architecture"
Prompt Component table (AI Interior Design Commercial Workflow.pdf pp. 2–3).
The two tables correspond on **three** rows *by row title* (typology,
materiality, optics), and each carries **two** rows the other's table does not
name — IPE adds Lighting Physics and Environment; CW adds Aesthetic Paradigm and
Atmospherics. Merged here into ONE seven-dimension checklist. The merge is the
studio's own synthesis: neither source asserts a correspondence with the other,
and the split is by row TITLE — the row *functions* are not disjoint (CW's
Atmospherics function text covers "environmental conditions", CW p.3; IPE's
Lighting Physics function text names "mood", IPE p.5). A render prompt is
**complete** when every dimension is either filled or deliberately waived.

| # | Unified dimension | หน้าที่ / Function | Example tokens (from sources) |
|---|---|---|---|
| 1 | Spatial Typology & Scale | volume, massing, primary function of the room | "double-height industrial loft", "minimalist studio kitchen" (AI Interior Design Commercial Workflow.pdf p.2); "cantilevered cliffside residence" (AI Image Prompt Engineering.pdf p.5) |
| 2 | Aesthetic Paradigm | historical / stylistic design language | "Japandi minimalism", "Bauhaus geometric abstraction", "French Country elegance" (AI Interior Design Commercial Workflow.pdf p.2) |
| 3 | Materiality | surface physics, texturing, light absorption / micro-reflections | see §2.1 |
| 4 | Lighting Physics | "volume, mood, color temperature, and shadow depth" (AI Image Prompt Engineering.pdf p.5) | see §2.2 |
| 5 | Atmospherics / Mood | "the emotional resonance and environmental conditions" (AI Interior Design Commercial Workflow.pdf p.3) | see §2.3 |
| 6 | Environment / Context | contextual background + seasonal atmosphere | "urban rooftop", "dense pine forest", "blue-hour twilight" (AI Image Prompt Engineering.pdf p.5) |
| 7 | Optical Parameters | perspective distortion, depth of field, spatial hierarchy (AI Image Prompt Engineering.pdf p.6); film-stock processing (AI Interior Design Commercial Workflow.pdf p.3) | see §2.4 |

### ตารางที่มาการรวม / Merge-provenance table

Absence cells below describe each source's **table row titles** only. Two
qualifications, both load-bearing: (a) a concept absent from one table may still
appear in that report's prose (CW's lighting is exactly this case); (b) a concept
with no row of its own may still be named inside another row's *function* text —
CW's Atmospherics row covers "environmental conditions" (CW p.3) and IPE's
Lighting Physics row names "mood" (IPE p.5). The absence cells are NOT claims of
clean conceptual disjointness.

| Unified dimension | AI Image Prompt Engineering.pdf pp.5–6 ("Architectural Prompting Variable") | AI Interior Design Commercial Workflow.pdf pp.2–3 ("Prompt Component") |
|---|---|---|
| 1 Spatial Typology & Scale | Typology & Scale | Spatial Typology |
| 2 Aesthetic Paradigm | — no style/aesthetic row in this table | Aesthetic Paradigm |
| 3 Materiality | Materiality | Materiality |
| 4 Lighting Physics | Lighting Physics | — no lighting row in this table; CW's lighting content is prose (CW p.4) |
| 5 Atmospherics / Mood | — no row TITLED Atmospherics; IPE folds emotional register into lighting — its Lighting Physics row function names "mood" (IPE p.5) and its prose says "Lighting dictates the emotional register" (IPE p.4) | Atmospherics |
| 6 Environment / Context | Environment | — no row TITLED Environment; CW's Atmospherics row function includes "environmental conditions" (CW p.3), but its examples are mood tokens, not context tokens |
| 7 Optical Parameters | Optical Parameters | Photographic Specs |

- **Why 4 and 5 are separate dimensions** (correcting a 2026-07-03 error in this
  file, which paired them as if the two source tables agreed): CW's Atmospherics
  row is not a lighting row. Its function is "Controls the emotional resonance
  and environmental conditions" and its examples are "Hygge vibes," "serene hotel
  aesthetic," "cinematic indoor mood" (AI Interior Design Commercial Workflow.pdf
  p.3) — mood, not light. IPE's Lighting Physics row "Establishes volume, mood,
  color temperature, and shadow depth", examples "Volumetric morning rays, hard
  midday sun, high-contrast shadows, global illumination" (AI Image Prompt
  Engineering.pdf p.5) — light, whose own function text also names mood, as does
  IPE's prose ("Lighting dictates the emotional register, volume, and perceived
  realism of an image", p.4). So the two rows are not a correspondence, but they
  are not disjoint either: only IPE's table has a lighting row, and only CW's
  table has a row DEDICATED to mood (its examples are mood tokens). Fill BOTH.
- GAP: both sources illustrate dimension 1 with commercial/architectural
  typologies (loft, tower, pavilion) — no Thai-residential typology tokens
  (condo 1BR, townhome, บ้านเดี่ยว). Studio typology wording comes from the
  project brief, not this corpus.
- GAP: dimension 2 examples are Western/global styles only; Thai-residential
  style language lives in `knowledge/styles/` — this corpus adds no Thai style
  vocabulary.
- GAP: dimension 6 examples are exterior-architecture contexts (hillside,
  forest, rooftop) — thin for interior renders beyond window-view /
  time-of-day context.

## 2. คลังคำศัพท์ต่อมิติ / Per-dimension vocabulary

### 2.1 วัสดุ / MATERIALITY lexicon

"Modern materials" is computationally useless — explicit material naming
dictates how the model simulates specularity, surface roughness and index of
refraction (AI Image Prompt Engineering.pdf p.4). An interior scene is
"effectively a material physics stress test" (AI Interior Design Commercial
Workflow.pdf p.4).

| กลุ่ม / Group | Tokens |
|---|---|
| Textiles / soft furnishing (specify weave + tactile quality) | bouclé, stonewashed linen, crushed velvet, handwoven rattan (AI Image Prompt Engineering.pdf p.4); textured linen, heavy drape of linen (AI Interior Design Commercial Workflow.pdf p.4) |
| Hard surfaces (geological / industrial specificity) | honed Carrara marble, filled travertine, brushed concrete, Corten steel, oxidized copper (AI Image Prompt Engineering.pdf p.4); warm teak wood (p.5); limewashed walls, white terrazzo flooring with stone chips, brushed brass (AI Interior Design Commercial Workflow.pdf p.3); matte aluminum finish, high-gloss enamel polymer (p.4) |
| Glazing / translucency | reeded glass, fluted glass, frosted polycarbonate (AI Image Prompt Engineering.pdf p.4); "glazed curtain wall" or "floor-to-ceiling fenestration" — never "big window" (AI Interior Design Commercial Workflow.pdf p.2) |
| Realism triggers | "physically accurate marble with natural veining", "micro surface imperfections" — triggers the model's latent high-end-CGI representations, away from sterile digital painting (AI Image Prompt Engineering.pdf p.4) |

- **Micro-texture directive / กันภาพพลาสติก:** always force micro-textures;
  omission yields the overly smooth "plastic" aesthetic of poorly prompted
  generation (AI Interior Design Commercial Workflow.pdf p.4).
- **Worked macro-prompt example (terrazzo):** "white terrazzo flooring with
  mixed stone chips, subtle reflections from overhead daylight" — makes the
  model prioritize surface imperfection + realistic light interaction over a
  flat synthetic color (AI Interior Design Commercial Workflow.pdf p.4).
- Cross-ref: studio material-imperfection RULE (binding, gate side) is
  `knowledge/brand-standards/render-quality.md` §3; the tactile-weave staging
  vocabulary is `knowledge/styles/color-composition.md` §9 item C.9 (bed-linen
  layering is a different topic, that file's §8).

### 2.2 แสง / LIGHTING lexicon

If lighting parameters are omitted, models default to flat, neutral,
uninspiring ambient illumination (AI Image Prompt Engineering.pdf p.4). Always
state source, temporal quality, and shadow behavior.

| กลุ่ม / Group | Tokens |
|---|---|
| Natural-temporal | golden hour ("golden hour afternoon light" — warm dramatic shadows), blue-hour twilight (warm interior vs cool exterior), soft overcast diffusion / "overcast daylight" (flat neutral color), dappled sunlight streaming through foliage (AI Image Prompt Engineering.pdf p.4; AI Interior Design Commercial Workflow.pdf p.4) |
| Artificial-cinematic | volumetric rays, global illumination, rim lighting, bounce light (AI Image Prompt Engineering.pdf p.4); warm ambient lighting, recessed LED strips, pendant fixtures, cinematic rim lighting, diffused light (AI Interior Design Commercial Workflow.pdf p.4) |
| Shadow dynamics | "high-contrast chiaroscuro", "soft contact shadows", "ambient occlusion" — forces complex light-decay / occlusion calculation, mimicking a professional V-Ray setup (AI Image Prompt Engineering.pdf p.4) |

- Cross-ref (do not restate here): temporal moods + staging order are already
  canonical in `knowledge/styles/color-composition.md` §9; lighting layers
  (ambient/task/accent), CCT zones and mixing rules in
  `knowledge/lighting/residential-lighting.md`. Design-illuminance floors are
  a codes-th matter — see `knowledge/codes-th/`.

### 2.3 อารมณ์ / ATMOSPHERICS–MOOD lexicon

CW's Prompt Component table is the only one of the two whose row is DEDICATED to
mood: "Atmospherics", function "Controls the emotional resonance and
environmental conditions" (AI Interior Design Commercial Workflow.pdf p.3), and
its three examples are all mood tokens. IPE has no such row — but its Lighting
Physics row function does name mood among the four things lighting establishes
(AI Image Prompt Engineering.pdf p.5), so the mood concept is not absent from
IPE's table, only undedicated.

| กลุ่ม / Group | Tokens |
|---|---|
| Emotional register / mood | "Hygge vibes", "serene hotel aesthetic", "cinematic indoor mood" (AI Interior Design Commercial Workflow.pdf p.3) |

- Mood tokens do **not** substitute for the §2.2 lighting tokens: IPE states that
  if lighting parameters are omitted, models default to "a flat, neutral, and
  uninspiring ambient illumination" (AI Image Prompt Engineering.pdf p.4). Fill
  dimension 4 *and* dimension 5.
- GAP: those three tokens are the entire mood vocabulary in this corpus, and the
  register is Western/Nordic ("Hygge") — no Thai mood/emotional-register tokens
  appear anywhere in either source.

### 2.4 ออปติกส์ / OPTICS lexicon (vocabulary only — policy is render-quality.md §4)

| Shot class | เลนส์ / Focal length | Use + required discipline |
|---|---|---|
| Wide / open-plan context | 14–24 mm | expansive layouts, open-plan living, sweeping architectural context; MUST pair with explicit compositional rules — "rule of thirds composition", "symmetrical architectural framing" — to manage spatial distortion (AI Interior Design Commercial Workflow.pdf p.3) |
| Standard / eye-level | 35–50 mm | natural eye-level perspective mimicking human sight, realistic sense of scale (AI Interior Design Commercial Workflow.pdf p.3); a 28 mm or 35 mm prime cited for broad context with minimal edge distortion (AI Image Prompt Engineering.pdf p.5) — same 28/35-vs-35/50 spread already logged in render-quality.md §4 |
| Macro / tele detail | typically 85 mm+ / macro lens (the source hedges: "typically specified as 85mm or higher") | intricate material close-ups + furniture detailing with "shallow depth of field" isolating the element (cabinet pull, marble veining) against soft bokeh (AI Interior Design Commercial Workflow.pdf pp.3–4; AI Image Prompt Engineering.pdf p.5) |

- **Aperture pair:** f/2.8 → shallow depth of field, subject sharp, background
  bokeh; **f/8 or f/11** (the source names a discrete pair, not a range) →
  infinite depth of field, keeping "the entire architectural massing and
  background landscape in sharp, rigorous focus"
  (AI Image Prompt Engineering.pdf p.5).
- **Tilt-shift:** essential architectural modifier — simulates perspective
  correction so vertical lines stay parallel instead of converging
  (AI Image Prompt Engineering.pdf p.5).
- **Compositional frameworks:** Rule of Thirds, Golden Ratio, symmetrical
  balance, leading lines — state explicitly or the model defaults to
  center-weighted framing (AI Image Prompt Engineering.pdf p.5).
- Film/gear tokens seen in the corpus: "Shot on Kodak Portra 400",
  "Hasselblad H6D-100c", "85mm f/1.4 GM lens"
  (AI Interior Design Commercial Workflow.pdf p.3). GAP: no evidence in the
  corpus that film-stock tokens help the Gemini lane specifically — treat as
  untested until gate-evidenced.

## 3. ลำดับความสำคัญและลิงก์ / Precedence + cross-refs

1. **Camera policy:** governed by `knowledge/brand-standards/render-quality.md`
   §4 — gate-evidenced 26 / 28 / 35 / 50 mm snap set, chosen by subject size.
   Studio gate evidence outranks the reference bands in §2.4 for studio
   outputs; this file supplies wording, never the lens decision.
2. **Temporal moods / staging:** canonical in
   `knowledge/styles/color-composition.md` §9 (staging checklist) and
   `knowledge/lighting/residential-lighting.md` (layers, CCT) — cite those,
   do not duplicate values here.
3. **Statutory anything:** `knowledge/codes-th/` only. This corpus is
   REFERENCE tier and must never source a legal value.
4. **Pipeline pointer (one line):** the corpus reports of Gemini (Imagen 3) that
   "Scenario-based descriptions significantly outperform technical
   specifications. Responds deeply to mood and atmosphere described in natural
   language" (AI Image Prompt Engineering.pdf pp.7–8 — the model-comparison table
   cell straddles the page break). CAVEAT: the source's own backing for that cell
   is its footnote 44, a vendor blog post (GMI Cloud, works-cited p.14) —
   REFERENCE tier with no studio gate evidence, which reinforces the
   "untested until gate-evidenced" stance in §2.4. Phrasing mechanics belong in
   the `pipeline/` prompt-registry guidance, not here.
