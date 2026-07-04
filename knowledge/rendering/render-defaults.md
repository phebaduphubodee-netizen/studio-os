# Render Defaults — PBR · Lighting · Camera · Realism (REFERENCE)
# ค่าตั้งต้นการเรนเดอร์ — วัสดุ PBR · แสง · กล้อง · ความสมจริง

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §8 (Rendering — photoreal pipeline). That KB was built 2026-06-30 by cross-checking
> **two independent Deep-Research runs** (Gemini 2.5 Pro + Google Search; NotebookLM
> DR over ~290 sources; raw audit trail
> `knowledge/_inbox/interior-ai/research/2026-06-30-gemini-DR-rendering.md`).
> Tier: **REFERENCE — strong-but-unaudited**, NOT Authority. Per the KB §9 ledger,
> the PBR parameter set + two-point-perspective + ~5 ft eye level + 24–50 mm are
> **cross-vendor-confirmed**; exact preset values are single-source.
>
> This renders OUR dimensionally-correct model — the OPPOSITE of text-to-image
> tools (RoomGPT/Imagen) that invent a new room. **Scale accuracy is the
> foundation realism factor and the studio's one real differentiator.**

## อำนาจ / Authority + precedence

- Any statutory geometry a render depicts (ceiling height, min room dims) is
  governed by `knowledge/codes-th/mr55-residential-dimensions.md` (LAW) — a
  render must never depict a non-compliant room.
- **Studio gate evidence outranks this reference for the studio's own outputs**
  (precedent: `knowledge/brand-standards/render-quality.md` §4). Where an A/B
  through the critique gate has decided a value (e.g. the small-room 26 mm lens,
  the M3.2 eye-camera height), the gate-proven value wins over the general
  number below — noted inline.
- PBR **authoring bounds** (albedo/metalness/roughness channel limits) are the
  domain of `knowledge/materials/pbr-material-behavior.md`; this file references
  them, does not restate them as new law.

---

## 1. PBR materials + typical values (§8.1)

Energy-conserving, physically-based. Per surface:

| Channel | Value | Note |
|---|---|---|
| **Albedo / base color** | dielectrics ~**30–240 sRGB**; avoid pure 0/255 | full authoring bounds + rationale → `materials/pbr-material-behavior.md §2` |
| **Metalness** | effectively binary **0.0** (dielectric) / **1.0** (metal) | mid only for rust/dust; raw metal → albedo near-black, colour from specular |
| **Roughness** | 0.0 mirror → 1.0 fully diffuse (§8.1). Studio rule: **avoid absolute 0.0/1.0** — from `pbr-material-behavior.md §2` + `render-quality.md §3`, not §8.1 | "Glossiness" = 1 − roughness — know which the engine uses |
| **Normal map** | RGB → per-pixel detail without geometry | DirectX vs OpenGL green-channel convention is a GAP (see pbr file) |
| **Specular / IOR** | dielectric default **IOR ≈ 1.5** (plastic); **water 1.33**, **glass ~1.52** | these IOR values are new here — single-source |

---

## 2. Lighting for render (§8.2)

- **HDRI / Image-Based Lighting** — a 360° high-range image = realistic ambient
  + reflections in one map.
- **Sun & Sky** (Cycles **Nishita**, V-Ray Sun/Sky) — physical daylight by
  lat/long + date/time → correct shadow direction + colour temperature.
- **Area lights** — give a physical size → soft shadows (bigger source = softer);
  drive with real lumens + Kelvin + **`.ies` photometric profiles** where the
  fixture sheet provides them.
- **Global Illumination** — indirect bounce; without it shadows go pure-black.
  The realism workhorse.

> Render-side lighting *principles* (three-point adaptation, exposure/shadow
> discipline, golden/blue/overcast mood, forced contact shadows to stop
> "floating" furniture, Shulman natural-vs-artificial balance) live in
> `knowledge/lighting/residential-lighting.md` and
> `knowledge/brand-standards/render-quality.md §1,5`. Design-side illuminance
> targets + the lumen method: `knowledge/lighting/lumen-method-and-fixture-placement.md`.

---

## 3. Camera & composition (§8.3)

- **Focal length** interiors **24–50 mm** (wide enough, low distortion); ~35–50 mm
  = natural. *Cross-vendor-confirmed band.*
- **Eye level** camera Z ≈ **4'6"–5'6" (1.35–1.65 m)**. *Cross-vendor-confirmed
  as the general architectural value.*
- **Two-point perspective is the architectural standard** — sensor plane parallel
  to verticals so all vertical lines stay vertical (camera roll 0, no up/down
  tilt). Three-point only for deliberate drama.
- Apply rule-of-thirds / leading lines.

> ⚠️ **Studio deviations (gate evidence wins):**
> - **Lens snap 26 / 28 / 35 / 50 mm** — the small-room **26 mm** is an
>   A/B-proven deviation from the 24–50 mm reference (`render-quality.md §4`);
>   `camera_config.py` picks by subject size.
> - **Eye-camera height ~1.15 m**, NOT 1.35–1.65 m — the M3.2 designer labelled
>   the 1.5 m eye level "too high"; the studio `--eye` camera was lowered to
>   ~1.0–1.2 m on that evidence (`pipeline/scripts/camera_config.py`,
>   `docs/functional-correctness-layer.md`; see `qa/reports/judge-calibration-*`).
>   `build_room.py`'s `EYE_LEVEL_M = 1.6` constant is the general/overview value;
>   the client-facing eye shot uses `camera_config`.
> - **Parallel verticals** are encoded as `build_room.py`'s level camera +
>   negative `shift_y` (no tilt) — see `render-quality.md §6`.

---

## 4. Realism factors — good → photoreal (§8.4)

- **Scale accuracy** — non-negotiable; the differentiator. (Enforced upstream by
  the dimensional gate, not the renderer.)
- **Correct UV / texture scale** — grain matches plank width; a brick pattern
  implying ~600 mm bricks or oversized wood grain reads as a toy
  (`materials/pbr-material-behavior.md §4`).
- **Bevel every edge** ~**1–2 mm** so edges catch light. `build_room.py` encodes
  a `BEVEL_WIDTH_M = 0.001` (1 mm) edge-bevel modifier.
- **Imperfection** — micro-scratches, dust, smudges, slight asymmetry via
  roughness/grunge maps (corroborated: `render-quality.md §3`,
  `pbr-material-behavior.md §4`).

---

## 5. Engines (§8.5)

- **Offline path-tracers** (hero stills): **Cycles** (our Blender engine),
  **V-Ray** (studio standard elsewhere), **Corona** (archviz-loved).
- **Real-time:** **Enscape** (CAD/BIM walkthroughs), **Lumion** (animations /
  entourage).

> Pipeline direction of record is HYBRID — the Blender/Cycles clay render is the
> **structural control**, then a Gemini image pass beautifies it
> (`docs/DECISIONS-render-assets.md`; RTX 3060 6 GB rules out local FLUX).

---

## 6. Post-processing (§8.6)

Never ship straight out of the engine: exposure/contrast, colour grade / white
balance, sharpening, subtle lens effects. The pro workflow renders **AOV passes**
(reflection / shadow / AO / denoise) for control without re-rendering.
`build_room.py` pins an AgX/Filmic view transform + a mild exposure correction
as the baseline of this.

---

## 7. What the pipeline already encodes + GAPs

- **Encoded in `pipeline/scripts/build_room.py`** (cites this file, §3–§4): level
  two-point camera, ~1.6 m overview eye level / 28 mm, negative vertical
  lens-shift (no tilt), 1 mm edge bevel, `albedo_plausible()` flag (0.04–0.94),
  per-material roughness, soft world ambient fill, AgX view transform.
  Doc-verified vs Blender 3.6/4.x (wf_b76afaf9) and render-verified on Blender 5.1.
- **GAPs / do-not-invent:** no per-material-family roughness bands, no dielectric
  F0 tables, no numeric emissive bounds (cd/m²) — those come from lint rules via
  PR, never from this reference (`pbr-material-behavior.md §2,4`). Preset values
  here are single-source; verify before a value gates a client deliverable.

## Cross-refs
- `knowledge/materials/pbr-material-behavior.md` — PBR authoring/QA bounds (§8.1 companion).
- `knowledge/brand-standards/render-quality.md` — the studio 6-rule photoreal standard + gate evidence.
- `knowledge/lighting/residential-lighting.md`, `knowledge/lighting/lumen-method-and-fixture-placement.md` — lighting companions.
- `pipeline/scripts/build_room.py`, `camera_config.py` — the code that consumes this.
