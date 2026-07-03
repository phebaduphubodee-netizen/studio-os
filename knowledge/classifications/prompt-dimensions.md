# มิติของพรอมต์ / Prompt-Dimension Taxonomy — six-dimension completeness checklist + vocabulary (Gemini render lane)

> PROVENANCE: distilled from two REFERENCE-tier DR reports staged in
> `knowledge/_inbox/id-project-corpus/`:
> `AI Image Prompt Engineering.pdf` (pp. 4–6, 8) and
> `AI Interior Design Commercial Workflow.pdf` (pp. 2–4).
> Date 2026-07-03, tier REFERENCE. This file is **prompt vocabulary only** —
> prompt mechanics (slot templates, registry, dispatch) live in `pipeline/`.

## ลำดับอำนาจ / Authority order — กฎหมายชนะ / law wins

- **No statutory values here.** Any dimensional, ventilation, daylight-opening
  or ceiling-height requirement comes from `knowledge/codes-th/` (Authority
  tier), which outranks everything in this file. Never cite this file for law.
- **Studio CAMERA POLICY outranks the optics vocabulary below** for the
  studio's own outputs: the gate-evidenced **26 / 28 / 35 / 50 mm** snap set is
  governed by `knowledge/brand-standards/render-quality.md` §4. §2.3 here is
  lexicon, not policy.

## 1. เช็คลิสต์ 6 มิติ / The six-dimension prompt-completeness checklist

Both source reports independently propose a 5-part prompt structure for
architectural/interior generation: the "Architectural Prompting Variables"
table (AI Image Prompt Engineering.pdf pp. 5–6) and the "lexical architecture"
Prompt Component table (AI Interior Design Commercial Workflow.pdf pp. 2–3).
The two systems overlap on four parts and each contributes one dimension the
other lacks — merged here into ONE six-dimension checklist. A render prompt is
**complete** when every dimension is either filled or deliberately waived.

| # | Unified dimension | หน้าที่ / Function | Example tokens (from sources) |
|---|---|---|---|
| 1 | Spatial Typology & Scale | volume, massing, primary function of the room | "double-height industrial loft", "minimalist studio kitchen" (AI Interior Design Commercial Workflow.pdf p.2); "cantilevered cliffside residence" (AI Image Prompt Engineering.pdf p.5) |
| 2 | Aesthetic Paradigm | historical / stylistic design language | "Japandi minimalism", "Bauhaus geometric abstraction", "French Country elegance" (AI Interior Design Commercial Workflow.pdf p.2) |
| 3 | Materiality | surface physics, texturing, light absorption / micro-reflections | see §2.1 |
| 4 | Lighting Physics & Atmospherics | light source, mood, color temperature, shadow depth, emotional register | see §2.2 |
| 5 | Environment / Context | contextual background + seasonal atmosphere outside the room | "urban rooftop", "dense pine forest", "blue-hour twilight" (AI Image Prompt Engineering.pdf p.5) |
| 6 | Optical Parameters | perspective distortion, depth of field, spatial hierarchy, film-stock processing | see §2.3 |

### ตารางที่มาการรวม / Merge-provenance table

| Unified dimension | AI Image Prompt Engineering.pdf pp.5–6 ("Architectural Prompting Variable") | AI Interior Design Commercial Workflow.pdf pp.2–3 ("Prompt Component") |
|---|---|---|
| 1 Spatial Typology & Scale | Typology & Scale | Spatial Typology |
| 2 Aesthetic Paradigm | — (absent) | Aesthetic Paradigm |
| 3 Materiality | Materiality | Materiality |
| 4 Lighting Physics & Atmospherics | Lighting Physics | Atmospherics |
| 5 Environment / Context | Environment | — (absent) |
| 6 Optical Parameters | Optical Parameters | Photographic Specs |

- GAP: both sources illustrate dimension 1 with commercial/architectural
  typologies (loft, tower, pavilion) — no Thai-residential typology tokens
  (condo 1BR, townhome, บ้านเดี่ยว). Studio typology wording comes from the
  project brief, not this corpus.
- GAP: dimension 2 examples are Western/global styles only; Thai-residential
  style language lives in `knowledge/styles/` — this corpus adds no Thai style
  vocabulary.
- GAP: dimension 5 examples are exterior-architecture contexts (hillside,
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
  `knowledge/brand-standards/render-quality.md` §3; textile-weave staging notes
  in `knowledge/styles/color-composition.md` §8.

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

### 2.3 ออปติกส์ / OPTICS lexicon (vocabulary only — policy is render-quality.md §4)

| Shot class | เลนส์ / Focal length | Use + required discipline |
|---|---|---|
| Wide / open-plan context | 14–24 mm | expansive layouts, open-plan living, sweeping architectural context; MUST pair with explicit compositional rules — "rule of thirds composition", "symmetrical architectural framing" — to manage spatial distortion (AI Interior Design Commercial Workflow.pdf p.3) |
| Standard / eye-level | 35–50 mm | natural eye-level perspective mimicking human sight, realistic sense of scale (AI Interior Design Commercial Workflow.pdf p.3); a 28 mm or 35 mm prime cited for broad context with minimal edge distortion (AI Image Prompt Engineering.pdf p.5) — same 28/35-vs-35/50 spread already logged in render-quality.md §4 |
| Macro / tele detail | 85 mm+ / macro lens | intricate material close-ups + furniture detailing with "shallow depth of field" isolating the element (cabinet pull, marble veining) against soft bokeh (AI Interior Design Commercial Workflow.pdf pp.3–4; AI Image Prompt Engineering.pdf p.5) |

- **Aperture pair:** f/2.8 → shallow depth of field, subject sharp, background
  bokeh; f/8–f/11 → infinite depth of field, entire massing sharp
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
   Studio gate evidence outranks the reference bands in §2.3 for studio
   outputs; this file supplies wording, never the lens decision.
2. **Temporal moods / staging:** canonical in
   `knowledge/styles/color-composition.md` §9 (staging checklist) and
   `knowledge/lighting/residential-lighting.md` (layers, CCT) — cite those,
   do not duplicate values here.
3. **Statutory anything:** `knowledge/codes-th/` only. This corpus is
   REFERENCE tier and must never source a legal value.
4. **Pipeline pointer (one line):** Gemini responds better to scenario/mood
   natural language than to technical spec lists — "scenario-based
   descriptions significantly outperform technical specifications"
   (AI Image Prompt Engineering.pdf p.8); phrasing mechanics belong in the
   `pipeline/` prompt-registry guidance, not here.
