# Render Defaults — PBR · Lighting · Camera · Realism (REFERENCE)
# ค่าตั้งต้นการเรนเดอร์ — วัสดุ PBR · แสง · กล้อง · ความสมจริง

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §8 (Rendering — photoreal pipeline). That KB was built 2026-06-30 by cross-checking
> **two independent Deep-Research runs** (Gemini 2.5 Pro + Google Search; NotebookLM
> DR over ~290 sources; raw audit trail
> `knowledge/_inbox/interior-ai/2026-06-30-gemini-DR-rendering.md`).
> Tier: **REFERENCE — strong-but-unaudited**, NOT Authority. Per the KB §9 ledger,
> the PBR parameter set + two-point-perspective + ~5 ft eye level + 24–50 mm are
> **cross-vendor-confirmed**; exact preset values are single-source.
>
> This renders OUR dimensionally-correct model — the OPPOSITE of text-to-image
> tools (RoomGPT/Imagen) that invent a new room. **Scale accuracy is the
> foundation realism factor and the studio's one real differentiator.**
>
> PROMOTION PASS 2026-07-13 — §1 albedo typical values, §3 focal-length taxonomy, §6
> lens effects, §8 render-spec fields and §9 encoding rules were read straight
> out of that same raw DR,
> `knowledge/_inbox/interior-ai/2026-06-30-gemini-DR-rendering.md`
> (the DR→KB hop had dropped them). Below, **`DR:NN` = that file, line NN**.
> Everything carrying a `DR:` cite is REFERENCE tier, single-source, and is a
> *proposal* — none of it is a gate until a PR makes it one.

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
| **Albedo / base color** | dielectrics *generally* **30–240 sRGB**; avoid pure 0/255 (rare in the physical world). Typical values (the source's own examples): **charcoal ≈ 50**, **fresh white snow ≈ 240** (DR:21) | full authoring bounds + rationale → `materials/pbr-material-behavior.md §2` |
| **Metalness** | effectively binary **0.0** (dielectric) / **1.0** (metal) | mid only for rust/dust; raw metal → albedo near-black, colour from specular |
| **Roughness** | 0.0 mirror → 1.0 fully diffuse (§8.1). Studio rule: **avoid absolute 0.0/1.0** — from `pbr-material-behavior.md §2` + `render-quality.md §3`, not §8.1 | "Glossiness" = 1 − roughness — know which the engine uses |
| **Normal map** | RGB → per-pixel detail without geometry | DirectX vs OpenGL green-channel convention is a GAP (see pbr file) |
| **Specular / IOR** | dielectric default **IOR ≈ 1.5** (plastic); **water 1.33**, **glass ~1.52** | these IOR values are new here — single-source |

- **The band and its examples.** DR:21 lists these under "Typical Values": for
  dielectric (non-metal) materials albedo values *generally* fall within
  **30–240**; "very dark materials like charcoal are around **50**, while fresh
  white snow is around **240**". The source gives them as illustrations of the
  band, and attaches no procedure to them.
- **DR Rule 2 (validate material inputs):** flag albedo **< 30 or > 240** —
  "physically implausible for *most common* dielectric materials" (DR:166). The
  source says *flag*, not fail; keep it a WARN unless a PR promotes it.
- **OPEN — unit reconciliation, do not resolve in this file.** `build_room.py`'s
  `albedo_plausible()` runs **0.04–0.94** (§7) while DR Rule 2's bounds normalise
  to ≈ **0.118–0.941** (30/255, 240/255). These are not the same number and may
  not even be the same space (sRGB-encoded 0–255 vs linear float). Unreconciled;
  the code bound is a gate value → change by PR only, never from this reference.

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
  = natural. *Cross-vendor-confirmed band.* Full lens taxonomy behind that band
  (DR:46–48):

| Band | Range (the source gives these as **e.g.** ranges, not hard boundaries) | Behaviour (as the source states it) |
|---|---|---|
| **Wide-angle** | e.g. **18–24 mm** | used to capture *small* interior spaces, **but can cause perspective distortion if too wide — objects appear stretched near the edges of the frame** (DR:46) |
| **Normal** | e.g. **35–50 mm** | approximates the human field of view; generally natural-looking perspective (DR:47) |
| **Telephoto** | e.g. **85 mm +** | exterior shots, or to flatten perspective — *often* creating a more controlled, "almost orthographic" look (DR:48) |

> For interior design, focal lengths are **typically kept between 24 mm and 50 mm**,
> balancing showing the space against significant distortion (DR:48). The studio's
> A/B-proven **26 mm** small-room lens sits at the **wide end of that 24–50 mm
> interior band**.

- **Eye level** camera Z ≈ **4'6"–5'6" (1.35–1.65 m)**. *Cross-vendor-confirmed
  as the general architectural value.* Placing the camera too high or too low
  **can create** an unnatural or unsettling feeling (DR:49).
- **Two-point perspective is the architectural standard** — sensor plane parallel
  to verticals so all vertical lines stay vertical (camera roll 0, no up/down
  tilt). Most render engines expose an **"automatic vertical tilt" / "architectural"
  camera** feature to enforce this (DR:51).
  Three-point (camera tilted, verticals converge to a third vanishing point) only
  for deliberate drama — it is *generally avoided for standard documentation shots*
  because it distorts the perception of the space (DR:52).
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
- **Junction & termination plausibility** (archviz convention — REFERENCE,
  never a gate; distilled 2026-07-21 from
  `knowledge/_inbox/interior-render-critique-DR-2026-07-15.md`, notebook
  639575c3 turn 1): floor-flush volumes get a recessed plinth base (zocallo)
  **10–15 mm**, a mitered base detail, or a shadow line; bridge material
  changes with baseboards/coving or **10–20 mm** aluminium shadow-gap
  Z-reveals — a razor 0 mm junction is the CG tell and produces artificial
  "light leaks"; heavy cladding (slats/stone/acoustic panels) terminates by
  wrapping the corner, a mitered return, or an L-bead trim — never a texture
  ending on a raw corner; recesses/cavities must receive GI bounce (no
  absolute-black 0,0,0 "black holes"; shadows soft, transparent, colour-bled).
  Full critique protocol + red flags:
  `knowledge/classifications/qa-dimensions.md` §8.

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
balance, sharpening, subtle lens effects — the source names these last as
**chromatic aberration, vignetting, lens flare**, added to mimic the
imperfections of a real camera lens (DR:84). The pro workflow renders **AOV passes**
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
- **Stated here, not encoded here:** DR encoding-rules **5 (link IES profiles)**,
  **6 (texture-scale sanity)** and **7 (complete-deliverable check)** are written
  out in full in §9. This file *states* them; it does not encode them as checks and
  makes no claim that any gate runs them — read the code before relying on one.

---

## 8. Render-spec — the fields a "complete" spec carries (DR:121–161)

The DR's proposed data contract for an AI drafting pipeline. **REFERENCE tier,
single-source, a proposal — not the studio's spec format and not a gate.** It is
recorded here because it is the vocabulary a render spec needs before §9's
completeness rule can even be evaluated. Types and enum members below are the
source's own.

**Geometry**

| Field | Type | Note (source) |
|---|---|---|
| `model_file` | path | link to the dimensionally-correct 3D model (DR:124) |
| `scale_check` | Boolean | flag confirming all objects are at **1:1 real-world scale** (DR:125) |

**Materials** — one set per surface / object

| Field | Type | Note (source) |
|---|---|---|
| `material_name` | string | e.g. "White Oak Flooring" (DR:127) |
| `pbr_albedo` | RGB value or texture path | **must be free of baked-in shadows** (DR:128) |
| `pbr_roughness` | Float **0.0–1.0** or texture path | (DR:129) |
| `pbr_metalness` | Float **0.0 or 1.0** (texture path only for mixed materials) | (DR:130) |
| `pbr_normal` | texture path | surface detail (DR:131) |
| `texture_scale` | physical dimension the map covers | source's example: "map covers 48×96 inches" (DR:132) |
| `edge_bevel_radius_mm` | mm | source's schema example **1.5 mm**; its Rule 3 default is **1 mm** (DR:133, DR:167) |

**Lighting** — `lighting_strategy` is an Enum: **`HDRI`** or **`Sun and Sky`** (DR:135)

| Branch | Field | Type / value (source) |
|---|---|---|
| HDRI | `hdri_file` | path to a high-resolution **`.hdr` / `.exr`** (DR:137) |
| HDRI | `hdri_rotation_degrees` | Float **0–360** (DR:138) |
| HDRI | `hdri_intensity` | Float (e.g. 1.0) (DR:139) |
| Sun & Sky | `geo_location` | latitude + longitude (DR:141) |
| Sun & Sky | `date_time` | **ISO 8601** date-time (DR:142) |
| Sun & Sky | `sun_intensity` | Float (DR:143) |
| Sun & Sky | `sky_turbidity` | Float (DR:144) |

Artificial lights — a **list** of objects, each:

| Field | Type / value (source) |
|---|---|
| `light_type` | Enum: `Area` / `Spot` / `Point` (DR:146) |
| `light_shape` | Enum: `Rectangle` / `Disc` (DR:147) |
| `light_dimensions_mm` | width × height (DR:148) — the physical size that sets shadow softness, §2 |
| `light_intensity_lumens` | Integer, **taken from the fixture spec sheet** (DR:149) |
| `light_color_temp_kelvin` | Integer, e.g. **2700 K**, **4000 K** (DR:150) |
| `ies_profile` | path to an **`.ies`** file for accurate light distribution (DR:151) |

**Camera**

| Field | Type / value (source) |
|---|---|
| `camera_position` / `camera_target` | XYZ coordinates (DR:153–154) |
| `focal_length_mm` | Integer (source's example: **28 mm**) (DR:155) |
| `perspective_type` | Enum: `Two-Point` / `Three-Point` — **defaults to `Two-Point`** (DR:156) |
| `output_resolution` | width × height px (source's example: **4000×3000**) (DR:157) |

**Render settings**

| Field | Type / value (source) |
|---|---|
| `render_engine` | Enum: `Cycles` / `V-Ray` / `Corona` (DR:159) |
| `quality_preset` | Enum: `Draft` / `Production` / `High` (DR:160) |
| `output_passes` | list of required AOVs, e.g. Denoise / Reflections / Ambient Occlusion (DR:161) |

> Dropped from this schema on purpose: the DR's `model_file` DCC-extension enum
> (`.3dm` / `.max` / `.skp` / `.blend`, DR:124) — operator trivia for software we
> do not run; we author `.blend`.

---

## 9. The DR's seven encoding rules (DR:163–171)

REFERENCE tier. Rules 1–4 already have a home in this file (column 3); rules 5–7
are recorded here as rules and nothing more.

| # | Rule, as the source states it | Where it sits here |
|---|---|---|
| **1** | **Enforce two-point perspective** — camera roll **0**, pitch corrected so all vertical lines are parallel to the frame's y-axis (DR:165) | §3 (and the level-camera / negative `shift_y` encoding, §7) |
| **2** | **Validate material inputs** — *flag* albedo **< 30** or **> 240** as physically implausible for most common dielectrics (DR:166) | §1 + the open unit reconciliation there |
| **3** | **Auto-bevel edges** — if `edge_bevel_radius_mm` is not specified, apply a **default 1 mm bevel to all geometric edges** (DR:167) | §4 (`BEVEL_WIDTH_M = 0.001`) |
| **4** | **Anthropometric camera height** — default camera Z at a standard eye level (source: "e.g. 1.6 m or 5'3″") (DR:168) | §3 — **but the studio's gate-proven ~1.15 m eye shot outranks it for our own outputs** (§3 deviations) |
| **5** | **Link IES profiles** — for any specified fixture, the pipeline *should attempt to* find and link the corresponding **manufacturer's `.ies` file** so light distribution is physically accurate (DR:169) | stated only — see §7 |
| **6** | **Texture-scale sanity check** — validate `texture_scale` against the object's real dimensions; the source's example is flagging a **10-foot (~3 m) wood-grain texture applied to a 6-inch (~150 mm) picture frame** (DR:170) | stated only — the realism principle is at §4, the *check* is not here |
| **7** | **Complete-deliverable check** (below) (DR:171) | stated only — see §7 |

> **Rule 7 — definition-of-done for a render spec (DR:171).** A render specification
> is "complete" **only if** it defines: **geometry** + **a material for every visible
> surface** + **at least one lighting source** (HDRI *or* Sun/Sky) + **a defined
> camera view**. Four conditions, all required.

---

## 10. Canonical sources the DR names (rendering-relevant)

Reference list only — **none of these is Authority tier**; Thai statutory geometry
still comes from `knowledge/codes-th/` (see Authority, above).

| Source | What the DR says it is |
|---|---|
| **Pharr, Matt; Jakob, Wenzel; Humphreys, Greg — *Physically Based Rendering: From Theory to Implementation*** | the **definitive technical reference** for PBR / "the 'bible' of rendering"; the underlying CS + physics, *not* a user guide for a specific program (DR:18, DR:101) |
| **Adobe Substance 3D (formerly Allegorithmic) + Marmoset documentation** | *de facto* industry standards for **explaining PBR concepts** to practitioners (DR:18) |
| **IES — *The IES Lighting Handbook*** | the authoritative professional standard for lighting design in the built environment; supplies the physical data (illuminance levels, light-distribution patterns) that render engines aim to simulate (DR:34, DR:95) |
| **Gordon, Gary — *Interior Lighting for Designers*** | accessible, design-focused; translates the IES technical standards into practical interior application (DR:34, DR:96) |
| **Steffy, Gary — *Architectural Lighting Design*** | art + science of lighting: how light shapes perception and defines space (DR:34, DR:97) |
| **Panero, Julius & Zelnik, Martin — *Human Dimension & Interior Space*** | the anthropometric authority the DR ties directly to **scale accuracy** — the ground-truth values that make furniture/fixtures dimensionally correct (DR:59) |
| **Binggeli, Corky — *Materials for Interior Environments*** | interior materials + their properties — the DR's material grounding for realistic PBR (DR:99) |

Ching (*Interior Design Illustrated*) and Karlen & Fleming (*Space Planning Basics*)
are also named by the DR (DR:92–93) but are general space-planning texts, out of
this file's scope; not carried here.

## Cross-refs
- `knowledge/classifications/qa-dimensions.md` §8 — render-critique protocol (plausibility · palette · sellability rubric; §4's junction/termination conventions come from the same DR).
- `knowledge/materials/pbr-material-behavior.md` — PBR authoring/QA bounds (§8.1 companion).
- `knowledge/brand-standards/render-quality.md` — the studio 6-rule photoreal standard + gate evidence.
- `knowledge/lighting/residential-lighting.md`, `knowledge/lighting/lumen-method-and-fixture-placement.md` — lighting companions.
- `pipeline/scripts/build_room.py`, `camera_config.py` — the code that consumes this.
