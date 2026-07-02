# Render Quality Standard — มาตรฐานคุณภาพภาพเรนเดอร์ (photoreal, lived-in vs sterile)

> Distilled from `knowledge/_inbox/nlm-design-systems/render-photoreal-rules.md`,
> NLM notebook `a5a43395` turn 7 (primary) + turns 2, 6, 12, 13, 14 (supplementary)
> — see `knowledge/_inbox/nlm-design-systems/qa-history.json` +
> `sources-manifest.md`. Date 2026-07-02. Tier: REFERENCE (studio standard, not law).

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
(source: `render-photoreal-rules.md` header, notebook a5a43395 turn 7).

## The six rules — กฎ 6 ข้อ (summary / สรุป)

| # | Rule (EN / ไทย) | Key values | Pipeline status |
|---|---|---|---|
| 1 | Lighting hierarchy / ลำดับชั้นแสง | no 4000 K vs 2700 K clash in one zone | fixed by prompt in registry v003 |
| 2 | Foreground layering / ฉากหน้า | — | prompt-level, v004 candidate |
| 3 | Material imperfection / วัสดุไม่สมบูรณ์แบบ | roughness never 0.0 or 1.0 | prompt-level, v004 candidate |
| 4 | Physical camera optics / เลนส์กล้องจริง | 35–50 mm, ~f/2.8 | DEVIATION: `--eye` camera is 26 mm (open item) |
| 5 | Environmental light + contact shadows / แสงบรรยากาศ + เงาสัมผัส | — | prompt-level, v004 candidate |
| 6 | Parallel verticals / เส้นดิ่งขนาน | — | encoded: `build_room` level-camera + shift_y rule |

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
- **OPEN ITEM / รายการค้าง:** current pipeline `--eye` suite camera is
  **26 mm** — a wide-angle CG tell vs the 35–50 mm standard. Candidate v0.4
  change; do not silently fix (source: `render-photoreal-rules.md` pipeline
  note).

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
  (source: `render-photoreal-rules.md`).

## Gaps — ช่องว่างที่แหล่งข้อมูลไม่ตอบ (source could not answer)

- No lux illuminance targets per room/task; no numeric
  ambient:task:accent layering ratios (turn 2 states sources lack them).
- No numeric CRI / R9 / Rf / Rg thresholds — only "high R9" qualitatively
  (turn 2).
- Physical bed-styling technique (asymmetric throw, relaxed pillows, exposed
  layers) was flagged by the notebook as OUTSIDE its sources (turn 13) —
  excluded here; verify independently before adopting as standard.
- The `[n]` markers in staged answers resolve only inside the notebook;
  `sources-manifest.md` pins the 118-source inventory but not per-marker
  mapping — named attributions above (Shulman, Adams, Birn, Block) come from
  the answer text itself.
