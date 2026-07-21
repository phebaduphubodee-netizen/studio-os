# พฤติกรรมวัสดุ PBR / PBR Material Behavior — authoring compliance for the render lane

> PROVENANCE: distilled from the id-project-corpus DR reports staged in
> `knowledge/_inbox/id-project-corpus/` — primary pages:
> `knowledge/_inbox/id-project-corpus/Automated Production QA Scoring Systems.pdf`
> pp.5–6 (glTF channel bounds, histogram-check rationale) and
> `knowledge/_inbox/id-project-corpus/Automated Vision QA for Interiors.pdf`
> pp.7–8 (map classification, family light response, emissive / texture-scale /
> tiling cues). Date 2026-07-03; citations re-verified 2026-07-13. Tier: **REFERENCE**.
> Role: corroborates the studio's PBR rules used by the `material-lint` skill
> and the critique gate. Any lint/gate **value** change still goes via PR —
> values are never adopted directly from these PDFs.

## ลำดับอำนาจ / Authority order

This file carries **no statutory values** / ไม่มีค่าตามกฎหมายในไฟล์นี้.
Anything dimensional or legally binding comes from `knowledge/codes-th/`
(Authority tier), which outranks everything here. Studio gate evidence
(own-pipeline A/B) also outranks this reference for the studio's own outputs
(precedent: `knowledge/brand-standards/render-quality.md` §4).

## 1. การจำแนก PBR maps / PBR map classification

Standard 3D workflows separate surface behavior into four texture channels
(Automated Vision QA for Interiors.pdf p.7):

| Map | บทบาท / Role |
|---|---|
| Diffuse / Albedo | innate surface color สีเนื้อวัสดุ (diffuse for non-metals, specular color for metals — Production QA p.5) |
| Normal | bump / relief ความนูน-ผิวสัมผัส |
| Roughness | gloss ↔ matte เงา-ด้าน (specular-lobe shape — Production QA p.6) |
| Specular | reflectance behavior การสะท้อน |

- Production compliance is evaluated on the **metallic-roughness workflow**
  standardized by the Khronos Group glTF specification — core channels
  **Albedo, Metalness, Roughness**
  (Automated Production QA Scoring Systems.pdf p.5).
- Generative image models output flat 2D pixels: all of these physical
  properties must read as convincingly **baked into the final image**
  (Automated Vision QA for Interiors.pdf p.7) — hence, studio inference (not
  in the source): the render gate judges light response in-image, not
  texture files.

## 2. ขอบเขตการ author ที่ถูกฟิสิกส์ / Authoring-compliance bounds (reference corroboration)

PBR's contract: a material reacts predictably from ~100,000-lux outdoor
daylight down to ~10-lux interiors (illustrative range from the source — an
invariance claim, NOT an illuminance target; lux targets are out of scope
here) because reflected light energy never exceeds incoming radiant energy —
**energy conservation**
(Automated Production QA Scoring Systems.pdf p.5).

| Channel | ขอบเขต / Bound | Rationale (source) |
|---|---|---|
| Albedo (non-metal) | **30–240 sRGB** — source wording: non-metals "should strictly fall between 30 and 240 sRGB" | below 30 (absolute black) or above 240 (approaching absolute white) absorb/reflect light unnaturally, "violating physical rendering laws"; the source's automated systems "trigger a failure state if pixel values exceed these bounds" (Production QA p.5) |
| Albedo (content) | **no baked directional lighting or AO** | albedo represents innate surface color only; shadows/highlights are stripped at authoring (Production QA p.5) |
| Metalness | effectively **binary 0.0 / 1.0** (0 / 255) | conductors = 1.0, insulators = 0.0; histogram check penalizes widespread mid-gray = physically impossible Fresnel reflectance. Transitional values only for rare edge cases: accumulated dust, oxidation (Production QA p.6) |
| Roughness | avoid absolute **0.0 / 1.0** | Cook-Torrance microfacet model: 0.0 = mirror-sharp lobe, 1.0 = broad diffuse; perfectly smooth or perfectly matte surfaces virtually never exist (Production QA p.6) — already studio rule, see `knowledge/brand-standards/render-quality.md` §3 |

- **How the studio expresses this band — and its wiring status (checked 2026-07-13).**
  The threshold key exists: `qa/thresholds.yaml` → `material_qa.albedo_srgb`, carrying
  `min` / `max` **30 / 240** plus a `pass_pct` / `warn_pct` pair. Its *shape* is therefore
  a percentile rule, not an absolute per-pixel clamp: the source states a failure state
  when "pixel values exceed these bounds" (Production QA p.5) and gives no tolerance
  percentage, so the source's framing is the stricter one. **But no scorer is wired to
  `material_qa.*` yet** — the key is a declared intent, not a running gate
  (`projects/PRJ-2026-002_c001-house/05_qa/qa-report.md`: "no scorer wired (Phase 3) —
  not scored"). The only consumer today is the `material-lint` skill, which checks
  `.mtlx` **authoring defaults** against that key, not rendered pixels. Read the live
  values from the key; it is a PR-only file and this file must not become a second copy
  of it.

- GAP — **corpus scope**: these PDFs give channel bounds only. They carry no numeric
  roughness **bands per material family** (e.g. honed vs polished marble), no
  dielectric F0 / specular values, and no normal-map convention (DirectX vs OpenGL
  green channel). Do not read any of those three out of this corpus.

- STUDIO scope — what exists elsewhere in the vault (checked 2026-07-13). None of it is
  gating; none of it comes from this corpus:
  - **Per-family roughness bands, incl. honed vs polished marble — these exist**:
    `knowledge/materials/bsdf-material-presets.md` §1 (honed marble 0.4–0.7, polished
    marble 0.0–0.15). **REFERENCE tier, single-source DR.** They are *starting values
    that must sit inside this section's bounds* — that file states "on conflict, the
    bounds win", and that a preset "must not gate a client deliverable" until confirmed
    by lint or promoted via PR.
  - **Dielectric F0 — no studio value exists, anywhere.** The vault carries no F0 number
    and no F0 table; do not read one out of any file. What *does* exist is **IOR**, a
    different parameterization of the same physics:
    `knowledge/rendering/render-defaults.md` §1 (dielectric default IOR ≈ 1.5; water
    1.33; glass ~1.52 — that file marks these values as single-source) and the
    per-material IOR / specular-level column in `bsdf-material-presets.md` §1. An IOR is
    **not** an F0 value: quote IOR as IOR, and treat "dielectric F0 table" as still open.
  - **Normal-map green-channel convention (DirectX vs OpenGL) — no studio value exists.**
    The corpus carries none and none is adopted here. Take it from lint rules via PR.

## 3. การตอบสนองแสงตามตระกูลวัสดุ / Expected light response by material family

The QA question is always: does the material interact correctly with the
established lighting environment?
(Automated Vision QA for Interiors.pdf p.7)

| ตระกูล / Family | พฤติกรรมแสงที่ถูกต้อง / Correct light response |
|---|---|
| Matte absorbers — raw concrete ปูนเปลือย, Belgian linen ลินิน | absorb light: high roughness, low specularity (Vision QA p.7) |
| Polished — marble หินอ่อนขัดเงา, glass กระจก, brass ทองเหลือง | crisp, **localized** specular highlights + environmental reflections (depth/luxury cue) (Vision QA pp.7–8) |
| Scattering identity — e.g. cognac leather หนัง vs velvet กำมะหยี่ | each material's scatter signature is distinct: leather rendered with velvet's fuzzy diffuse scattering = material mismatch → regeneration (Vision QA p.7) |

- Reference protocol (Hi3DEval-style): assess albedo, saturation, metallicness
  by extracting **reflectance cues under the image's implied illumination**
  (Vision QA p.7) — i.e. judge the response in-image, matching how the
  studio's critique gate scores renders rather than source maps.
- Textile vocabulary that drives correct scatter (weave named explicitly:
  stonewashed linen, crushed velvet, bouclé, handwoven rattan) is already a
  studio standard — `knowledge/brand-standards/render-quality.md` §3,
  `knowledge/styles/color-composition.md` §8.

## 4. วัสดุเปล่งแสงและสัญญาณความสมจริง / Emissives & realism cues

**Emissives** (Automated Vision QA for Interiors.pdf p.8):

- LED strips, neon signs, TV/screens must not only glow — they must **cast
  localized, color-accurate light onto adjacent surfaces**.
- Generative models frequently fail the decomposition between emissive and
  non-emissive components; QA verifies luminous-area statistics and rejects
  **excessive glare disturbance** / แสงฟุ้งเกินจริง.
- GAP: no numeric emissive-intensity bounds (cd/m²) in the corpus.
- Internal corroboration: "perfectly even LED strips" is a recorded flash-tier
  micro-texture tell in the studio's own gate evidence
  (`knowledge/brand-standards/render-quality.md` §7).

**Texture scale ต้องตรงสเกลจริงของวัตถุ** (Vision QA p.8):

- Pattern frequency must match the object's **metric scale** (checked against
  the estimated 3D bounding box). Source example: a brick pattern implying
  ~600 mm (60 cm) bricks next to a chair = severe pattern-scaling error;
  oversized wood grain makes furniture read as a miniature toy.

**Tiling / repetition** (Vision QA p.8):

- Generative models hallucinate repetitive grid-like anomalies on large
  continuous patterns; correct surfaces keep **natural variation** — no
  visible tiling seams or repeating grids.

**Micro-imperfections** (Vision QA p.8):

- Subtle scratches, fingerprints, signs of wear make materials tangible and
  authentic — corroborates studio rule 3 (material imperfection) in
  `knowledge/brand-standards/render-quality.md` §3; fabric pilling for
  textiles per `knowledge/styles/color-composition.md` §8 (NLM-sourced, not
  in these PDFs).

## 5. Cross-refs & gaps / อ้างอิงข้ามไฟล์และช่องว่าง

- `knowledge/brand-standards/render-quality.md` §3 — studio roughness /
  imperfection rules this file corroborates; §7 — image-model tier evidence.
- `knowledge/classifications/render-defects.md` — defect taxonomy (authored
  2026-07-03). This file's **in-image** failure modes map to its codes:
  scatter mismatch → MA-01, pattern-scale error → MA-02, tiling artifact →
  MA-03, emissive glare → MA-04, missing micro-imperfections → MA-05. The
  §2 **authoring-side** bounds (albedo out-of-bounds, mid-gray metalness,
  absolute 0.0/1.0 roughness) have no in-image defect code — they are
  texture-authoring checks enforced upstream by `material-lint`.
- `material-lint` skill — enforcement surface for §2 bounds on `.mtlx`
  assets; threshold/value changes via PR only (`qa/thresholds.yaml` is
  PR-only).
- `knowledge/materials/bsdf-material-presets.md` §1 — per-material Principled-BSDF
  **starting values** (REFERENCE tier, single-source DR). They are the per-material
  companion to §2 here: a preset must sit *inside* §2's channel bounds, and that file
  states "on conflict, the bounds win".
- `knowledge/rendering/render-defaults.md` §1 — the §8.1 PBR companion (albedo band,
  metalness, roughness, dielectric IOR); its §1 table points back to §2 here for the
  full authoring bounds + rationale.
- GAP: the corpus describes QA **detection** methods (histogram checks,
  luminous-area statistics, spatial-frequency vs bounding-box) but gives no
  pass/fail thresholds beyond the sRGB 30–240 albedo band — do not invent
  thresholds from this file.
- OPEN — **two albedo bands are live in the studio, in different units.** §2 here serves
  **30–240 sRGB** — 0–255 encoded texel values (threshold key `material_qa.albedo_srgb`;
  no scorer wired, see §2). Separately, `pipeline/scripts/build_room.py`'s
  `albedo_plausible()` **flags** base-color floats outside **0.04–0.94**, citing "KB §8.1"
  — and it only *prints* `!! albedo WARN`; it does not fail the build. The two are not a
  re-expression of each other: 30/255 ≈ **0.118**, not 0.04, so the code's band is not a
  unit conversion of this section's band, and neither PDF in this corpus supplies a float
  band at all. Do not convert one into the other here; quote whichever band the surface
  you are checking actually reads, and resolve the discrepancy via PR.
  `knowledge/rendering/render-defaults.md` §1 records the same reconciliation as OPEN.
