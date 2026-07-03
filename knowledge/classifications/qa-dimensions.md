# อนุกรมวิธานมิติ QA / Canonical QA-Dimension Taxonomy (render + image QA)

> PROVENANCE: distilled from `knowledge/_inbox/id-project-corpus/` DR reports
> (REFERENCE tier). Every claim re-verified against the source PDF pages on
> 2026-07-03 (text-layer extraction). Sources: Automated Production QA Scoring
> Systems.pdf; Automated Vision QA for Interiors.pdf; AI Image Prompt
> Engineering.pdf; AI Interior Design Commercial Workflow.pdf.
> Live-pipeline axis names verified against `pipeline/scripts/critique.py`
> (render rubric) on the same date.

## กฎเหล็ก / HARD RULE — vocabulary only, no gates

This file defines **vocabulary and axes only**. Every numeric gate/threshold
lives in `qa/thresholds.yaml` (change via PR only) and NOWHERE else. The
source threshold matrix ("Matrix 1", Automated Production QA Scoring
Systems.pdf p.12) is partly **unrecoverable** — its right-hand operands are
embedded as images and come out blank in text extraction — so no number
"from the corpus" may be reconstructed or inferred. Thai statutory values
never appear here: `knowledge/codes-th/` is the only Authority source.

## 1. เก้าเสาหลัก QA / Nine-pillar QA taxonomy

Source: Automated Production QA Scoring Systems.pdf p.1 (pillar list) +
per-pillar section headings pp.1–11.

| Pillar | Source definition (section heading) | Canonical check |
|---|---|---|
| 1. Prompt QA | Semantic & intent alignment — degree of alignment between output and the semantic constraints of the input prompt (p.1) | decompose prompt into verifiable atomic elements; VQA against them (p.1) |
| 2. Image QA | Perceptual & statistical fidelity — artifacts, compression degradation, structural noise (p.3) | FR/NR/NAR-IQA statistics vs natural-scene regularities (pp.3–4) |
| 3. Lighting QA | Illumination & shadow consistency — adherence to geometric optics; light attenuation/occlusion vs visible scene architecture (p.4) | shadow probability map; specular lobe vs normal-map correlation (pp.4–5) |
| 4. Material QA | PBR compliance — energy conservation across texture channels (p.5) | Albedo/Metalness/Roughness channel scans; geometry topology checks (pp.5–6) |
| 5. Camera QA | Geometric & projection validity — perspective, lens properties, projective geometry adhere to mathematical reality (p.6) | homography factorization; vanishing-point + radial-distortion consistency (pp.6–7) |
| 6. Consistency QA | Temporal & structural stability — identities/colors/textures must not flicker or morph across frames (p.7) | optical-flow warping error (FloLPIPS-class); frame-by-frame entity/attribute VQA (pp.7–8) |
| 7. Brand QA | Colorimetric & identity adherence — brand color/logo conforms to colorimetric + geometric spec, not "looks similar" (p.8) | CIELAB ΔE00 distance vs master guideline; keypoint match vs reference vector (pp.8–9) |
| 8. Client Requirement QA | Operational & semantic compliance — output fulfills the specific constraints of the production brief (p.9) | LLM-as-a-Judge rubric with explicit criteria + structured output (pp.9–10) |
| 9. Revision QA | Reconstruction fidelity & regression prevention — targeted edits must not alter unedited background/identity (p.11) | SSIM/LPIPS delta OUTSIDE the edit mask; preservation tracked across model updates (p.11) |

**Consistency re-scoped for this studio:** the source's Consistency QA is
temporal (video frames). This studio generates stills, so Consistency QA here
= **cross-view identity of one room across its CamNN renders**
(`R_PRJ###_Room_CamNN_vNN`): same furniture, materials, palette and layout
from every camera. Closest source evaluator: MET3R multi-view consistency —
dense 3D reconstruction warps content from one view to another and computes a
view-invariant feature similarity (Automated Vision QA for Interiors.pdf p.9).

### แกนวิจารณ์ที่ใช้จริง / Mapping to live critique axes

Live render rubric = 8 axes in `pipeline/scripts/critique.py` (verified
2026-07-03). Mapping is many-to-one; pillar coverage is partial by design.

| critique.py axis | Primary pillar | Note |
|---|---|---|
| `palette_coherence` | Brand QA | one controlled colour/material story (no colorimetric ΔE check live — VLM judgment only) |
| `lighting_quality` | Lighting QA | layered/intentional light vs flat |
| `composition` | Camera QA | believable framing vs floating catalogue shot |
| `furniture_realism` | Material QA | primitive-box tell = geometry/PBR fidelity failure |
| `room_context` | Image QA | scene completeness — real room vs empty-void tell |
| `styling_and_life` | Client Requirement QA | lived-in staging per studio standard/brief |
| `proportion_and_scale` | Camera QA | projective/scale validity of the scene |
| `photoreal_believability` | Image QA | photograph vs CG — perceptual fidelity |

GAP: no live per-image axis covers Prompt QA (spec adherence is upstream:
build spec + `overlay_fidelity.py` draft), Consistency QA (batch-level,
cross-CamNN — no automated check yet), or Revision QA (repair re-renders are
re-critiqued whole; no outside-mask preservation delta).

## 2. รูบริกอื่นเป็นมุมมองบนเก้าเสา / Other rubrics reconciled as views onto the nine pillars

**Four critique dimensions** — interiors Vision-QA critiques across
"spatial, photometric, material, and compositional dimensions" (Automated
Vision QA for Interiors.pdf p.1): spatial → Camera + Consistency; photometric
→ Lighting; material → Material; compositional → Image (aesthetic side) +
Camera.

**Four-axis VLM evaluation harness** (AI Image Prompt Engineering.pdf p.10):

| VLM axis | Form | Pillar view |
|---|---|---|
| Instruction Following | binary pass/fail on hard constraints (counts, colors, spatial relations) | Prompt QA + Client Requirement QA |
| Text Rendering Accuracy | legibility, spelling fidelity, placement of embedded typography | Brand QA (typography side) |
| Style & Brand Fit | graded scalar (typically 0–5) vs requested aesthetic | Brand QA + Client Requirement QA |
| Spatial & Relational Logic | physics + spatial-instruction correctness (e.g. shadow direction vs light source) | Camera QA + Lighting QA |

**Aesthetic dimensions** (AESBench / Aesthetic Scorer families; Automated
Vision QA for Interiors.pdf p.9): Technical Quality (no artifacts/noise/blur)
→ Image QA; Composition (rule of thirds, offset focal points, foreground
depth) → Camera QA; Depth of Field (physical bokeh/falloff, not arbitrary
blur) → Camera + Image QA; Color Harmony (cohesive chromatic relationships)
→ Brand QA.

**หลักสองแกนอิสระ / Dual-axis principle:** prompt adherence and visual
quality are **independent axes** — the model that follows instructions best
is rarely the one producing the most beautiful image; a robust pipeline
scores BOTH, separately, and balances them (Automated Vision QA for
Interiors.pdf p.9). Never collapse them into one number.

## 3. วงจร Vision-QA ห้าเฟส / Five-phase Vision-QA loop

Names + definitions only (Automated Vision QA for Interiors.pdf pp.3–4).
Studio implementation = Stage 05 critique gate + repair queue.

| Phase | Mechanism | Objective |
|---|---|---|
| 1. Decomposition | dependency-structured question graphs | break design intent into binary verifiable constraints; prerequisites precede dependents (confirm window exists BEFORE judging its daylight) |
| 2. Visual Anchoring | baseline T2I rendering | externalize latent/textual hallucinations into an observable image as the critique baseline |
| 3. Diagnostic VQA | VLM binary YES/NO assessment | evaluate anchor against the question graph; a natural-language rationale for every NO |
| 4. Targeted Refinement | agentic prompt rewriting + adaptive negative prompting | correct only the failing elements (e.g. add dimensional anchors); never blind-rewrite the whole prompt — stylistic drift |
| 5. Verification | iterative resampling | confirm constraint satisfaction; halt early to save compute/API cost |

## 4. ตระกูลตัวประเมิน / Evaluator & metric families

### 4.1 Prompt-alignment evaluators (Automated Production QA Scoring Systems.pdf pp.1–3)

| Framework | Mechanism | Optimal use case |
|---|---|---|
| DSG | semantic tuples → directed acyclic graph; VQA against the graph; dependency filtering prevents cascading errors (no "red" penalty if "car" absent) | open-ended complex prompts needing strict logical entailment; discrete binary scores |
| Soft-TIFA | VLM token probabilities on templated atomic questions; continuous 0–1; arithmetic mean = average adherence, geometric mean = strict/penalty-driven | templated compositional enterprise pipelines |
| SGA | scene graphs built for prompt AND image; scored on node, edge, and global alignment | complex relational scenes needing explicit structural matching |
| VQAScore / PickScore | direct VQA querying / pairwise preference | model training, hyperparameter tuning, baseline comparisons; pointwise logits or pairwise win rates |

Note: the corpus expands DSG two ways — "Davidsonian Semantic Graph"
(Automated Production QA Scoring Systems.pdf p.1) vs "Dynamic Scene Graph"
(AI Image Prompt Engineering.pdf p.10). Same framework; treat the expansion
as unsettled in the corpus.

### 4.2 IQA families (Automated Production QA Scoring Systems.pdf pp.3–4)

- **FR-IQA** (full-reference): needs a pristine original (PSNR, SSIM, VMAF).
  Frequently inapplicable to generative outputs — no ground truth exists.
- **NR-IQA** (no-reference): natural-scene-statistics based. BRISQUE = MSCN
  coefficients + SVR trained on human opinion scores. NIQE = fully blind,
  compares against a pristine-corpus statistical model; it analyzes only
  patches with suprathreshold sharpness, so it does **not penalize
  intentional depth-of-field blur** — safe for our shallow-DoF interior shots.
- **NAR-IQA** (non-aligned reference): reference shares semantic content but
  not pixel alignment (novel-view synthesis, 3DGS); contrastive feature
  matching. Relevant to cross-CamNN consistency checks.

### 4.3 Named benchmark frameworks

GenEval, DSG, OneIG-Bench — rigorous multi-dimensional rubric harnesses for
VLM-as-judge image evaluation (AI Image Prompt Engineering.pdf p.10).

## 5. คำศัพท์ความน่าเชื่อถือของ LLM-judge / Judge-reliability vocabulary

Source: Automated Production QA Scoring Systems.pdf pp.9–10.

- **Spearman ρ** — rank-order correlation between LLM and human labels: does
  the judge rank relative quality correctly?
- **Cohen κ** — inter-rater agreement on absolute categorical scores: does it
  assign the right pass/fail, not just the right ordering?
- **Accuracy** — percentage of exact matches with human labels: is the rubric
  unambiguous enough for programmatic use?
- The source's target-threshold column for all three is blank in extraction
  (image-embedded operands) — **do not invent target values**; if the studio
  ever gates on judge reliability, the number enters via `qa/thresholds.yaml`
  PR with its own justification.
- **CLEAR framework** — judges are assessed on Cost, Latency, Efficacy,
  Assurance, Reliability (p.10). Validate a judge against human-labeled
  ground truth; check for self-bias (favoring its own model family).
- **Semantic vs operational metric split** — rubric criteria divide into
  semantic (correctness, groundedness) and operational (efficiency, safety)
  metrics (p.10). Keep the two families separate in scorecards.

## 6. ปรัชญาการอัปสเกล / Upscaling-philosophy classes (queued upscaler milestone)

Source: AI Interior Design Commercial Workflow.pdf pp.9, 12.

- **Creative upscaling** (Magnific-style): a secondary diffusion pass that
  invents new detail (wood grain, fabric pilling, micro-reflections). Slider
  controls: **Creativity** (how much new detail may be invented), **HDR**
  (micro-contrast + lighting intensity), **Resemblance** (how strictly the
  original geometry is followed). Interior-work reference band: Creativity
  0.3–0.5 with Resemblance 75–85% keeps architecture structurally accurate
  while enriching surfaces (p.9); the worked commercial example uses
  Creativity 0.3 / Resemblance 85% for final 4K polish (p.12).
  **REFERENCE starting band only — never a gate**; any acceptance criterion
  for upscaled output goes through `qa/thresholds.yaml`.
- **Precision upscaling** (SUPIR-style): conservative restoration only —
  sharpens/cleans without hallucinating detail or altering the design (p.9).
  Use when introducing AI-invented geometry would break established accuracy
  (e.g. dimensioned or CAD-derived imagery).
- Class choice is a per-deliverable decision: creative for marketing-grade
  photoreal enrichment, precision for anything a contractor measures against.

## 7. ช่องว่าง / GAPs — what the corpus does NOT give

- No usable numeric thresholds: Matrix 1 (p.12) and the judge-metric targets
  (p.10) have image-embedded operands, blank in extraction. Gates must be
  derived empirically (golden-set) and land in `qa/thresholds.yaml` via PR.
- No interior-specific pillar weighting or aggregation formula for a single
  batch score.
- No stills-native Consistency QA recipe — MET3R is the nearest pointer;
  cross-CamNN identity checking needs its own studio design.
- No Thai-market or Thai-regulatory QA content anywhere in these four PDFs —
  statutory floors remain exclusively `knowledge/codes-th/` +
  `clearance_check` (suite v0.4.3).
