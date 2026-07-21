# Render Quality Standard — มาตรฐานคุณภาพภาพเรนเดอร์ (photoreal, lived-in vs sterile)

> PROVENANCE — three streams, distinguish them when citing:
> 1. **NLM stream (§1–§6, 2026-07-02).** Distilled from
>    `knowledge/_inbox/nlm-design-systems/render-photoreal-rules.md`, NLM notebook
>    `a5a43395` turn 7 (primary) + turns 2, 6, 12, 13, 14 (supplementary) — see
>    `knowledge/_inbox/nlm-design-systems/qa-history.json` +
>    `knowledge/_inbox/nlm-design-systems/sources-manifest.md`.
>    Tier: REFERENCE (studio standard, not law).
> 2. **PDF stream (§4 adjacent evidence, appended 2026-07-03).**
>    `knowledge/_inbox/id-project-corpus/Automated Vision QA for Interiors.pdf` p.5.
>    Tier: REFERENCE (DR-style write-up, single source).
> 3. **INTERNAL stream (§4 RESOLVED block, §7).** The studio's own critique-gate
>    A/B evidence — not a reference source. Studio gate evidence outranks reference
>    sources for the studio's own outputs.
>
> VERIFY HISTORY — process record, NOT a clean bill of health:
> - **2026-07-03** (PDF append): its independent verify pass was killed by a spend
>   limit and never ran.
> - **2026-07-13, author self-check** (source PDF re-read): §4 PDF block and the
>   Gaps list rewritten (the block had been over-read as "corroboration" of our
>   lens choice; two Gaps had gone stale).
> - **2026-07-13, independent verify**: found further defects *in that self-check*
>   — the §4 PDF block, the rule table's registry citations, and two provenance
>   path tokens. Those findings were applied the same day by the authoring lane.
>   No pass has certified the file since that edit.

**Authority cross-ref:** any statutory room geometry depicted in renders
(ceiling height, minimum room dimensions) is governed by
`knowledge/codes-th/mr55-residential-dimensions.md` — codes-th outranks this
file; on conflict the law wins.

## Scope — ขอบเขต / what this standard binds

The studio definition of a professional, lived-in interior image vs a sterile
"AI-generated" one: six rules. This is the checklist that the critique gate
(`pipeline/scripts/critique.py` — axes `lighting_quality`, `styling_and_life`)
and the prompt registry (`pipeline/prompts/registry/render-hybrid/`, v003+)
encode. Registry v003 fixed lighting by prompt; these rules are the target for
v004+ prompts and for the clay controls themselves
(source: `knowledge/_inbox/nlm-design-systems/render-photoreal-rules.md` header,
notebook a5a43395 turn 7).

## The six rules — กฎ 6 ข้อ (summary / สรุป)

| # | Rule (EN / ไทย) | Key values | Pipeline status |
|---|---|---|---|
| 1 | Lighting hierarchy / ลำดับชั้นแสง | no 4000 K vs 2700 K clash in one zone | fixed by prompt in registry v003 |
| 2 | Foreground layering / ฉากหน้า | — | prompt-level: clause shipped in registry **v004** (evidence note ↓) |
| 3 | Material imperfection / วัสดุไม่สมบูรณ์แบบ | roughness never 0.0 or 1.0 (clay/BSDF side — **not** in the v004 prompt) | prompt-level: only the *qualitative* imperfection clause shipped in **v004** (evidence note ↓) |
| 4 | Physical camera optics / เลนส์กล้องจริง | 35–50 mm, ~f/2.8 | RESOLVED 2026-07-02: subject-size snap 26 / 28 / 35 / 50 mm; 26 mm = gate-evidenced small-room deviation (see §4) |
| 5 | Environmental light + contact shadows / แสงบรรยากาศ + เงาสัมผัส | — | prompt-level: clause shipped in registry **v004** (evidence note ↓) |
| 6 | Parallel verticals / เส้นดิ่งขนาน | — | encoded: `build_room` level-camera + shift_y rule |

> **v004 evidence note (rules 2, 3, 5).** The clauses ship in the `template` field of
> `pipeline/prompts/registry/render-hybrid/v004.json` —
> rule 2: *"let one small physical element break the camera plane at a frame edge
> (a plant leaf, the corner of a table, the back of a chair) … softly out of focus"*;
> rule 3: *"include subtle real-world imperfection … natural wrinkles and slouch in
> fabric, slight unevenness in plaster, natural variation in wood grain"*;
> rule 5: *"believable contact shadows under every object"*. That file's `provenance`
> field names this standard as their origin ("foreground plane-break + CCT-harmony
> from knowledge/brand-standards/render-quality.md (rules 1-2)").
> **Rule 3 caveat:** only that qualitative language shipped — the numeric
> "roughness never 0.0 or 1.0" is a clay/BSDF-side value the v004 prompt does not carry.
> **Separately**, v004 is the ACTIVE label (dev / staging / production) per
> `pipeline/prompts/registry/render-hybrid/labels.json:2-4` — those three lines carry
> the version pointer only, no clause content.

> A further prompt-side push (registry **v005**, render-tell kill-list) was tried
> and **NOT promoted** — `pipeline/prompts/registry/render-hybrid/labels.json:9`
> (`_v005_evidence`). See §7: at this plateau the measured lever was the image
> model tier, not the prompt.

### 1. Lighting hierarchy — ลำดับชั้นแสง / อุณหภูมิสี (ambient task accent, color temperature)

- Never a single uniform ceiling source — it kills directional shadows,
  flattens the image, reads AI-generated (turn 7).
- Layer three tiers: **ambient** (fill) + **task** (table lamps,
  under-cabinet) + **accent** (architecture/artwork) (turns 2, 7).
- Harmonize color temperatures: never a clinical **4000 K** daylight source
  against a warm **2700 K** incandescent in the same localized zone
  (turns 7, 12).

| Zone / โซน | CCT (K) | Source |
|---|---|---|
| Residential warm atmosphere / บ้านพักอาศัย | 2200–3000 K | turns 2, 12 |
| Typical warm residential incandescent | 2700 K | turn 2 |
| Commercial (avoid in residential renders) / เชิงพาณิชย์ | 4000–5700 K | turn 12 |

- Color rendition: TM-30 metrics (Rf fidelity / Rg gamut) have largely
  replaced CRI; high R9 needed to render reds (turn 2 — no numeric R9/Rf
  targets given in source).
- Balance interior artificial light against window daylight to reveal
  architectural volumes (Julius Shulman method, turns 6, 14).

### 2. Foreground layering — ฉากหน้า / ความลึกภาพ (depth, scale anchor)

- Head-on rooms with nothing breaking the camera plane read flat and
  institutional (turn 7).
- Place a physical object — plant, chair edge, tabletop — in the immediate
  foreground: spatial hierarchy, 3D depth, realistic scale anchor
  (turns 6, 7, 14).
- Audit the frame for "mergers": foreground/background lines that visually
  intersect; shift camera slightly to separate them (Ansel Adams / Shulman
  principle, turn 14).

### 3. Material imperfection — วัสดุไม่สมบูรณ์แบบ / micro-texture (roughness, wear)

- Perfectly smooth (**0.0** roughness) or perfectly matte (**1.0** roughness)
  surfaces virtually never exist — the "plastic" tell of sterile renders
  (turn 7).
- Prescribe high-frequency detail: subtle scratches, fingerprints, wear,
  terrazzo stone chips, brushed-metal refraction (turn 7).
- Material physics must behave: matte (raw concrete, linen) absorbs light;
  polished (glass, brass) catches crisp specular highlights and reflections
  (turn 14).
- Textiles / ผ้า: name the weave — "stonewashed linen, crushed velvet, bouclé,
  handwoven rattan"; heavy drape of linen and fabric pilling read as
  authentic/lived-in (turns 13, 14).

### 4. Physical camera optics — เลนส์กล้องจริง / ระยะโฟกัส (focal length mm, DoF, f-stop)

- Focal length **35–50 mm** for natural human-eye perspective (turns 7, 14).
  Turn 6 separately cites a **28 mm or 35 mm** prime for broad environmental
  context with minimal edge distortion — internal spread in the notebook;
  studio standard follows the 35–50 mm rule until reconciled.
- Shallow depth of field ≈ **f/2.8** on a lived-in detail (cabinet pull, linen
  weave) — soft physical bokeh, never arbitrary non-physical blur (turn 7).
- Perspective is governed by camera-to-subject distance, not lens (Ansel Adams,
  turn 6).
- **RESOLVED 2026-07-02 (v0.4, gate evidence over doctrine):** the `--eye`
  camera now picks the lens by subject size (frame ≈ 2× the largest non-rug
  piece), snapped to **26 / 28 / 35 / 50 mm**. A/B through the critique gate:
  living_condo at 35 mm scored 4/5 (natural perspective ✓ the source rule
  works in normal rooms); but the tight bedroom_suite at 28 mm dropped
  room_context 5/5 → 3/5 vs 5/5 at 26 mm — in small rooms the wider frame is
  what carries room-context, so 26 mm stays in the snap set ON EVIDENCE,
  documented as a deviation from the 35–50 mm source standard (studio gate
  outranks general reference for the studio's own outputs).

#### §4 adjacent evidence — a described generative fisheye failure mode, from a Vision-QA source (REFERENCE, appended 2026-07-03, corrected 2026-07-13)

Source: `knowledge/_inbox/id-project-corpus/Automated Vision QA for Interiors.pdf`
p.5, opening paragraph of §"Recurrence-based Vanishing Point Detection". Verbatim:

> "Generative models often warp these lines, particularly at the periphery of an
> image, simulating an unnatural fisheye distortion if the implied field of view
> exceeds the standard 24–35mm equivalent"

**What the source does with it.** The sentence is *descriptive*, sitting in the
section's motivation paragraph: it states a failure mode of generative models. The
section's subject is an anomaly detector (R-VPD — vanishing points recovered from
explicit + implicit lines, grouped by weighted RANSAC) run over the **2D output of
a generative model**. The flag conditions that source actually names are **not**
FOV-based; two paragraphs later, p.5: *"If vertical lines fail to remain parallel
(violating the two-point architectural perspective rules essential for interior
renders), or if horizontal depth lines converge at wildly conflicting horizon
points, the system flags a severe structural anomaly"*. Nowhere in the 14 pages
does the source say the system thresholds on implied focal length.

**This file's reading — the source does not say so either way.** We treat the
24–35 mm figure as *adjacent* evidence about generated 2D images and **do not**
take it as corroboration of the studio's authored lens choice: the source makes no
claim about a 26 mm **authored** camera. Whether the band doubles as an authoring
reference is not settled by the source (its own wording, "the **standard**
24–35mm equivalent", is compatible with one). An earlier version of this file
inverted the implication — "inside the band → reads natural" — and applied it to
the Blender clay camera's focal length; that inference was the file's, not the
source's, and is retracted (2026-07-13).

**Lens bands now in promoted knowledge** — do not read these as one band:

| Band | Where | What the cited source says it is |
|---|---|---|
| **24–50 mm** | `knowledge/rendering/render-defaults.md:92`, restated :102–104 | interior authoring band ("typically kept between 24 mm and 50 mm"); *cross-vendor-confirmed* per that file's ledger. This is the band our pipeline default sits in — `pipeline/scripts/build_room.py:30` `RENDER_FOCAL_MM = 28` |
| **35–50 mm** | notebook a5a43395 turns 7, 14 (§4 above) | authoring guidance — turn 7 verbatim: "Use a 35mm to 50mm focal length to establish a natural, human-eye-level perspective"; turn 14 restates it ("a natural, eye-level human perspective") |
| **24–35 mm equivalent** | `knowledge/_inbox/id-project-corpus/Automated Vision QA for Interiors.pdf` p.5 | the *implied* FOV above which generative models are described as simulating fisheye warp. Stated descriptively; the source does not say how, or whether, its detector uses the figure |

The 24–50 mm authoring band subsumes both narrower authoring figures, and
`knowledge/rendering/render-defaults.md:102–104` already places the studio's **26 mm** small-room
lens at the wide end of that band. None of this changes the evidence-based
**26 / 28 / 35 / 50 mm** snap set — studio gate evidence outranks reference
sources for the studio's own outputs.

GAP: no source cited above gives a room-size → mm mapping.
`knowledge/rendering/render-defaults.md:98` gives only the direction — wide-angle
"e.g. **18–24 mm**" is "used to capture *small* interior spaces, **but can cause
perspective distortion if too wide**" (DR:46). The **26 / 28 / 35 / 50 mm** snap
set is studio gate evidence (§4 RESOLVED), not reference-sourced.

### 5. Environmental light + contact shadows — แสงบรรยากาศ / เงาสัมผัส (golden hour, ambient occlusion)

- Without contact shadows furniture appears to float — illusion destroyed
  (turn 7).
- Dictate a temporal quality / เวลาแสง: **golden hour** (warm dramatic
  shadows), **blue hour** (warm interior vs cool exterior contrast), or
  **overcast** (soft neutral color) (turns 7, 14).
- Force "ambient occlusion" and "soft contact shadows" so objects ground to
  the surfaces they rest on (turn 7).

### 6. Parallel verticals — เส้นดิ่งขนาน / geometric accuracy (tilt-shift, camera back)

- Camera back perfectly vertical, or tilt-shift perspective correction:
  vertical structural lines stay parallel to the frame edges, never converging
  (turns 6, 7; Ansel Adams camera source per turn 6).
- Leaning/warping walls = spatial disorientation (turn 7).
- One-point (head-on) shots: camera back parallel to the subject's horizontal
  AND vertical lines (turn 6).
- Already encoded in pipeline: `build_room` level-camera + shift_y rule
  (source: `knowledge/_inbox/nlm-design-systems/render-photoreal-rules.md`).

## Gaps — ช่องว่างที่แหล่งข้อมูลไม่ตอบ (source could not answer)

- The **turn-2 NLM source** gives no lux illuminance targets per room/task and no
  numeric ambient:task:accent layering ratios. This is a limit of *that* source,
  not of the vault: both values exist in promoted knowledge — the per-room IES
  illuminance table (`knowledge/lighting/lumen-method-and-fixture-placement.md:64–76`,
  e.g. Living general 10–20 fc / 108–215 lux; Kitchen counters 50–80 fc /
  538–861 lux; Home office desk 50–75 fc / 538–807 lux) and the numeric layering
  ratios (same file `:48–49` — accent : ambient **~3 : 1**; task surface : surround
  within **3 : 1**). Both are REFERENCE, single-source (Gemini DR) per that file.
- Colour-rendition thresholds, split:
  - **CRI floor — CLOSED.** **CRI ≥ 90** = residential professional floor
    (`knowledge/lighting/lumen-method-and-fixture-placement.md:94`, single-source),
    encoded at `pipeline/scripts/dimensional_rules.v0.2.json:128` →
    `lighting.cri_min = 90` (also v0.1.json:92).
  - **R9 / Rf / Rg — still open.** Turn 2 gives only "high R9" qualitatively; no
    numeric R9, Rf or Rg target is carried in this file.
- Physical bed-styling technique (asymmetric throw, relaxed pillows, exposed
  layers) was flagged by the notebook as OUTSIDE its sources (turn 13) —
  excluded here; verify independently before adopting as standard.
- The `[n]` markers in staged answers resolve only inside the notebook;
  `knowledge/_inbox/nlm-design-systems/sources-manifest.md` pins the 118-source
  inventory but not per-marker mapping — named attributions above (Shulman,
  Adams) come from the answer text itself.

### 7. Image-model tier — gate evidence (INTERNAL provenance, own pipeline)

- 2026-07-02 A/B (same clays, same v004 production prompt, critique.py flash
  judge): flash image tier plateaus at 4/5 REWORK with recurring micro-texture
  tells (uniform wood grain, perfectly even LED strips, "too clean");
  `gemini-3-pro-image-preview` -> 4.5/5 SHIP on BOTH proven room types with
  photoreal_believability 5/5 — the believability gap is the image model, not
  the prompt (a prompt-side kill-list, registry v005, gained nothing
  reproducible; see labels.json `_v005_evidence`).
- Rule of thumb: client-facing hero shots dispatch on the pro tier
  (`GEMINI_IMAGE_MODEL` env, hybrid_render.py); drafts and iteration stay on
  flash. Single-roll critique variance is ±0.5 — compare versions on means,
  never one roll.
