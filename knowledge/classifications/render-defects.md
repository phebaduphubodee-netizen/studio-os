# อนุกรมวิธานข้อบกพร่องภาพเรนเดอร์ / Render Defect Taxonomy (defect codes for QA scorecards)

> PROVENANCE: compiled from `knowledge/_inbox/id-project-corpus/Automated Vision
> QA for Interiors.pdf` (primary) and `Automated Production QA Scoring
> Systems.pdf` pp.4–5 (shadow-geometry cross-ref), date 2026-07-03,
> tier REFERENCE. This is a **compiled list, not one verbatim source table** —
> the source PDFs describe these failure modes in prose across multiple
> sections; per-defect page citations are kept so each claim can be re-checked.
> The one verbatim table (§4.6) is reproduced as printed on pp.8–9.

## ลำดับอำนาจ / Authority order & scope

- **No thresholds here.** This file defines the defect **vocabulary** (code +
  definition + detection heuristic) for QA scorecards and repair-queue triage.
  Pass/fail numbers live in `qa/thresholds.yaml` (PR-only) — never in this file.
- **No statutory values.** Clearance, ventilation, and dimensional law come
  from `knowledge/codes-th/` (enforced by the clearance_check engine), which
  outranks everything here. A hazardous-adjacency flag (SP-06) is a plausibility
  check, not a code check.
- Defect codes: `SP-` spatial, `PH-` photometric, `MA-` material,
  `CO-` compositional/artifact. Use these codes verbatim in scorecards and
  repair queues so triage stays greppable.

## 1. SPATIAL — โครงสร้างพื้นที่และเปอร์สเปคทีฟ / Spatial coherence & perspective

Root cause per the corpus: T2I diffusion models have no internal 3D coordinate
system, so perspective distortion, collisions, and scale violations are the
default failure family (Automated Vision QA for Interiors.pdf pp.4–5).

| Code | Defect / ข้อบกพร่อง | Detection heuristic |
|---|---|---|
| SP-01 | Floating furniture / เฟอร์นิเจอร์ลอย — object not grounded on floor | Monocular metric depth (MMDE, e.g. ZoeDepth / Depth Anything V2): sharp, unexplainable **depth discontinuity between the object's base and the floor directly beneath it** (p.6) |
| SP-02 | Scale violation / สัดส่วนผิด — furniture "too tall"/"too miniature" vs neighbors | Lift objects to metric 3D bounding boxes (3DBB); compare the spatial-scale parameter of each object against adjacent objects (e.g. armchair vs sofa, seat vs table) (pp.1, 5–6) |
| SP-03 | 3DBB collision / วัตถุทะลุกัน — volumes physically intersect | Monocular 3D detection (Boxer, Cube R-CNN, OmniNOCS): flag when one object's 3D bounding box intersects another's (dining chair through dining table) (p.5) |
| SP-04 | Perspective anomaly / เส้นเปอร์สเปคทีฟผิด — non-parallel verticals, conflicting horizon points | Recurrence-based Vanishing Point Detection (R-VPD) over explicit lines (baseboards, ceiling joints) + implicit lines (tile grids); flag if verticals fail to stay parallel or horizontal depth lines converge at wildly conflicting horizon points (p.5) |
| SP-05 | Fisheye / excessive implied FOV / ภาพบิดขอบเลนส์กว้างเกิน | Peripheral line-warp analysis; source norm: unnatural fisheye distortion appears when implied FOV exceeds a standard **24–35 mm equivalent** (p.5) — source-stated norm, not a studio threshold; camera discipline: `knowledge/styles/color-composition.md` §5 |
| SP-06 | Hazardous / implausible adjacency / การวางชิดที่อันตรายหรือเป็นไปไม่ได้ | Semantic adjacency check on detected object pairs — corpus example: fireplace situated dangerously beneath wooden shelves (p.1). Statutory clearances are NOT this code — those come from `knowledge/codes-th/` |

## 2. PHOTOMETRIC — แสงและเงา / Lighting & shadow realism

Root cause: no light-transport physics — models default to sterile uniform
illumination or conflicting light sources (Automated Vision QA for
Interiors.pdf p.6).

| Code | Defect / ข้อบกพร่อง | Detection heuristic |
|---|---|---|
| PH-01 | Flat single-uniform-source lighting / แสงแบนแหล่งเดียว | Localized contrast analysis: a single uniform ceiling source without directional shadows flattens the image ("immediately revealing its AI origins"); expect an ambient / task / accent hierarchy (p.6; staging rule: `knowledge/styles/color-composition.md` §9 B6) |
| PH-02 | Brightness-ordering violation / ลำดับความสว่างผิด | Localized contrast comparison across sources: secondary sources (table lamps, sconces) must not emit brighter illumination than primary sources (large windows in a daytime scene) (p.6) |
| PH-03 | CCT clash within one zone / อุณหภูมิสีตีกันในโซนเดียว | RGB sampling in highlighted regions: a clinical 4000 K daylight source fighting a warm residential 2700 K incandescent source within the same localized zone (p.6; zone-consistency rule: `knowledge/lighting/residential-lighting.md`, `color-composition.md` §7) |
| PH-04 | Shadow/highlight source disagreement / เงากับไฮไลต์ชี้คนละแหล่งแสง | Forensic light-transport check: vectors drawn from cast-shadow tips through object anchor points and from specular-highlight centroids must intersect at one implied 3D light position; angular deviation past an acceptable threshold = composited conflicting illumination priors (p.7). Cross-ref: normal-map-vs-specular-lobe correlation — highlight implying a source that diverges from the shadow-implied source ⇒ structurally incoherent (Automated Production QA Scoring Systems.pdf p.5) |
| PH-05 | Missing inverse-square falloff / ไม่มีการตกของแสงตามระยะ | Area-light neighborhoods must show realistic falloff (inverse-square behavior, per the 3DLP-style probes); an area light close to a surface with no falloff produces a harsh unnatural highlight (p.7) |
| PH-06 | Inconsistent shadow trajectories / เงาทิศทางขัดแย้ง, contact shadow หาย | Shadow-geometry audit: contradictory light sources, physically impossible shadow trajectories, or omitted contact shadows; use attached-vs-cast shadow logic (umbra/penumbra grading vs light-source extent) and differentiable shadow prediction from depth + light localization (Automated Vision QA for Interiors.pdf p.1; Automated Production QA Scoring Systems.pdf p.4) |

## 3. MATERIAL — วัสดุและพื้นผิว / Material authenticity & texture fidelity

Root cause: PBR properties (albedo, normal, roughness, specular) must be
convincingly "baked" into flat 2D pixels (Automated Vision QA for
Interiors.pdf p.7).

| Code | Defect / ข้อบกพร่อง | Detection heuristic |
|---|---|---|
| MA-01 | Material-response mismatch / วัสดุสะท้อนแสงผิดชนิด | Reflectance-cue extraction under implied illumination (Hi3DEval-style: albedo, saturation, metallicness): e.g. "cognac leather" exhibiting the fuzzy diffuse scattering of velvet ⇒ material prompt mismatch, force regeneration (p.7) |
| MA-02 | Texture/pattern scale error / ลายวัสดุผิดสเกล | Correlate texture spatial frequency with the object's 3DBB metric scale: wallpaper motifs, wood grain, floor tiles out of proportion to room geometry — e.g. implied brick length ~600 mm next to a chair (p.8) |
| MA-03 | Tiling / repeating-grid artifact / ลายซ้ำเป็นตาราง | High-frequency artifact detection isolating hallucinated repetitive grid-like structures in continuous patterns; natural variation should survive (p.8) |
| MA-04 | Emissive without localized light (or excessive glare) / วัตถุเรืองแสงไม่ส่องสว่างรอบข้าง | Luminous-area statistics: neon signs, LED strips, TV screens must both glow **and** cast localized, color-accurate light onto adjacent surfaces, without excessive glare disturbance (p.8) |
| MA-05 | Plastic look — missing micro-imperfections / ผิววัสดุเนียนปลอม | Detail audit: absence of subtle scratches, fingerprints, signs of wear that make materials tangible (p.8); "plastic-looking fabrics" is the corpus's canonical late-denoising-stage textural error (p.10); styling counter-moves: `color-composition.md` §8–9 |

### 3.6 ตารางเมตริก QA คุณสมบัติวัสดุ (verbatim) / Material-property QA metric table

Reproduced verbatim from Automated Vision QA for Interiors.pdf pp.8–9:

| Material Property QA | Evaluation Metric | Target Outcome for Realism |
|---|---|---|
| Roughness / Specularity | Hi3DEval Reflectance Cues | Matte surfaces absorb light; metals/glass exhibit crisp, localized highlights. |
| Texture Scale | Spatial Frequency vs. 3DBB | Pattern sizes (e.g., wood grain, tiles) match the metric scale of the object. |
| Seamlessness | High-Frequency Artifact Detection | Absence of visible tiling seams or unnatural repeating grids in large surfaces. |
| Emissivity | Luminous Area Statistics | Glowing objects cast accurate, localized light without overwhelming glare. |

## 4. COMPOSITIONAL / ARTIFACT — องค์ประกอบภาพและอาร์ติแฟกต์

| Code | Defect / ข้อบกพร่อง | Detection heuristic |
|---|---|---|
| CO-01 | Anatomical distortion / สัดส่วนกายวิภาคผิด | Universal diagnostic VQA query injected into every evaluation pass regardless of prompt (p.3) |
| CO-02 | Illegible embedded text / ตัวอักษรในภาพอ่านไม่ออก | Universal diagnostic query: is text on signage/labels legible? (p.3) |
| CO-03 | Generative artifacts / noise / structural blur / เนื้อภาพเสีย | Technical-quality dimension (AESBench / Aesthetic-Scorer style): absence of generative artifacts, noise, structural blurring, pixelation; NR-IQA statistics (BRISQUE, NIQE, NIMA) score naturalness without a reference image (p.9) |

## 5. GAP: ช่องว่างของ corpus / Where the corpus is thin

- GAP: no severity ordering or repair-priority weights per defect — the corpus
  names failure modes but does not rank them; severity mapping belongs to
  `qa/thresholds.yaml` (PR-only).
- GAP: numeric tolerances (PH-04 angular deviation, SP-05 FOV cutoff, MA-02
  scale ratio) are left symbolic or single-example in the source — the p.7
  threshold value did not survive PDF extraction. Do not invent numbers;
  propose thresholds via PR with golden-set evidence.
- GAP: no Thai-market or statutory defect classes (clearance violations,
  ventilation openings). Those are enforced from `knowledge/codes-th/` and are
  intentionally outside this taxonomy.
- GAP: cross-ref targets `knowledge/materials/pbr-material-behavior.md` and
  `knowledge/classifications/qa-dimensions.md` are not yet authored; until
  then use `knowledge/materials/residential-materials.md` for material truth.

## Cross-references

- `knowledge/lighting/residential-lighting.md` — light-coherence checks behind
  PH-01…PH-06 (layering, CCT zones).
- `knowledge/materials/residential-materials.md` (current) →
  `knowledge/materials/pbr-material-behavior.md` (pending) — expected material
  light response behind MA-01/MA-05.
- `knowledge/classifications/qa-dimensions.md` (pending) — dimension
  definitions these codes group under.
- `knowledge/styles/color-composition.md` §5, §7–9 — camera/perspective and
  CCT staging rules that prevent SP-04/SP-05/PH-03 upstream.
- `qa/thresholds.yaml` — the only place numeric gates live (PR-only).
