# ค่าตั้งต้น Principled BSDF ต่อวัสดุ / Per-Material Principled-BSDF Presets — REFERENCE starting values

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/2026-07-01-photoreal-render-technique-DR.md`
> ("Physically-Based Materials (PBR) for Blender's Principled BSDF" findings
> table). **Single-source Deep-Research report — tier REFERENCE, strong-but-
> unaudited.** These are per-material STARTING points for the Cycles clay pass
> and a material-intent reference for the Gemini hybrid beauty pass — NOT
> authoring law. Per-material companion to `knowledge/rendering/render-defaults.md`
> §1 (the §8.1 PBR summary).

## ลำดับอำนาจ / Authority + precedence — READ BEFORE USING A NUMBER

- **Authoring / QA bounds are NOT set here.** The channel limits that these presets
  must sit inside — the albedo band, binary metalness, and the "avoid absolute
  0.0 / 1.0 roughness" rule — live in `knowledge/materials/pbr-material-behavior.md`
  **§2**. This file gives *plausible per-material defaults*; that file gives the
  *bounds they must sit inside*. On conflict, the bounds win.
- **Dielectric F0 is NOT one of those bounds — no studio F0 value exists anywhere.**
  `pbr-material-behavior.md` §2 declares dielectric F0 an explicit **GAP**; it carries
  no F0 number, and neither does any other vault file (checked 2026-07-13). What the
  vault does carry is **IOR**, a different parameterization:
  `knowledge/rendering/render-defaults.md` **§1** (dielectric default IOR ≈ 1.5;
  water 1.33; glass ~1.52 — single-source), and the per-material **IOR (Specular
  level)** column in §1 below. Cite IOR as IOR; do not cite it as an F0 bound.
- `render-defaults.md` §7 lists **per-material-family roughness bands** and **dielectric
  F0 tables** among its GAPs / do-not-invent — those "come from lint rules via PR, never
  from this reference" (its composite cite `pbr-material-behavior.md §2,4` points at
  where those GAPs are *declared*: the channel GAPs at §2, the numeric emissive-bounds
  GAP at §4 — not at any value). So these presets are a **convenience starting point, not
  a gate**: a value here **must not gate a client deliverable** until it is either
  confirmed by the material lint rules or promoted via PR with a named source.
- Any statutory geometry a material sits on is still governed by
  `knowledge/codes-th/`; a preset never overrides that.

## 1. ตารางค่าตั้งต้น / The per-material preset table (verbatim from the DR)

Blender Principled BSDF. "Use texture" = drive the channel from a map, not a flat
value; the value shown is the plausible range/centre. Metallic is binary (0
dielectric / 1 metal).

| Material | Base Color (sRGB hex) | Roughness | IOR (Specular level) | Metallic | Sheen | Coat | Note (source) |
|---|---|---|---|---|---|---|---|
| **Warm Oak Wood Floor** | `#A68763`→`#8B6F4E` (texture) | 0.3–0.6 (texture) | 1.52 (0.5) | 0 | 0.1–0.3 | 0.01–0.05 | roughness map for glossy↔rough grain; slight coat = polyurethane |
| **Honed Marble** | `#EBEBEB` (texture) | 0.4–0.7 | 1.5 (0.5) | 0 | 0 | 0 | matte/satin, diffuse reflections; SSS sparingly for high-end |
| **Polished Marble** | `#EBEBEB` (texture) | 0.0–0.15 † | 1.5 (0.5) | 0 | 0 | 0 | low roughness = sharp reflections; smudge/wear roughness map |
| **Cream Bouclé Upholstery** | `#F5F0E9` | 0.8–0.9 | 1.5 (0.5) | 0 | 0.7–1.0 | 0 | high roughness + high **Sheen** = fuzzy fabric; normal/displacement for loops |
| **Brushed Brass** | `#B5A642` | 0.3–0.5 | N/A (metal) | 1.0 | 0 | 0 | brushed pattern via a Normal/Bump texture; **Anisotropic** stretches reflections along the brush direction |
| **Polished Chrome** | `#F0F0F0` | 0.0–0.05 † | N/A (metal) | 1.0 | 0 | 0 | mirror finish: very low roughness + metallic 1.0 |
| **Clear Architectural Glass** | `#FFFFFF` | 0.0 † | 1.52 | 0 | 0 | 0 | set **Transmission = 1.0**; faint green tint for thick panes |
| **Matte Warm-White Wall Paint** | `#F5F3EE` | 0.7–0.9 | 1.4–1.5 (0.5) | 0 | 0 | 0 | **do not use pure white** `#FFFFFF` (energy-conservation + unnatural); warm off-white |

## 2. การปรับให้เข้ากับกฎสตูดิโอ / Studio reconciliations (apply on top of the table)

- **† Absolute 0.0 roughness → nudge up.** The studio rule (`pbr-material-
  behavior.md §2`, `brand-standards/render-quality.md §3`, echoed in
  `render-defaults.md` §1) is **avoid absolute 0.0 / 1.0 roughness** — perfectly
  sharp mirrors read as CG. Where the DR gives `0.0` (clear glass, polished
  chrome low end, polished marble low end), floor it at a small epsilon
  (~**0.02–0.05**) and add a subtle smudge/roughness map. The mirror *look* still
  comes through; the CG tell does not.
- **Metalness stays binary** — 0 for every dielectric row, 1.0 only for the
  metals (brushed brass, polished chrome); no mid values except deliberate
  rust/dust (`render-defaults.md` §1).
- **Glass is Transmission, not a dark low-roughness surface** — Base Color is the
  tint, Transmission = 1.0, IOR 1.52; without transmission you get a grey pane.
- **Albedo bounds still apply — but mind which band you are quoting.** Two live in the
  studio, in different units, and they are *not* a conversion of each other:
  `pbr-material-behavior.md` §2 gives **30–240 sRGB** (0–255 encoded texel values), while
  `build_room.py`'s `albedo_plausible()` flags base-color **floats** outside
  **~0.04–0.94**. Both say the same thing about *these* presets — never pure 0 / 255 —
  so the DR's own paint row already obeys them (`#F5F3EE`, not `#FFFFFF`). The
  reconciliation between the two bands is OPEN (`pbr-material-behavior.md` §5,
  `render-defaults.md` §1); do not convert one into the other here.
- **Texture scale is a realism factor** — the "(texture)" rows only read right at
  correct real-world UV scale (grain matches plank width; `render-defaults.md` §4,
  `pbr-material-behavior.md §4`). A preset value on a mis-scaled map still looks
  like a toy.

## 3. ที่ใช้ค่าเหล่านี้ / Where these are consumed

- `pipeline/scripts/build_room.py` sets a **per-material roughness** + the
  `albedo_plausible()` flag on the Cycles clay (the structural control image);
  these presets are the reference for those per-material values.
- The **Gemini hybrid** beauty pass (`hybrid_render.py`, direction of record per
  `docs/DECISIONS-render-assets.md`) does not read numeric BSDF channels, but the
  material *intent* here (warm oak, honed vs polished marble, bouclé sheen,
  chrome, clear glass, warm-white paint) is the finish language a render prompt
  should carry so the beauty pass matches the clay's material story.

## Cross-refs
- `knowledge/materials/pbr-material-behavior.md` §2 — the authoring/QA **bounds** these defaults must obey (owner of the channel limits + the do-not-invent GAPs; it declares dielectric F0 a GAP rather than carrying a value).
- `knowledge/rendering/render-defaults.md` §1 — the §8.1 PBR summary this file details per-material.
- `knowledge/brand-standards/render-quality.md` — the 6-rule studio photoreal standard + gate evidence.
- `knowledge/materials/residential-materials.md`, `millwork-casework.md` — the physical materials these render presets depict.
- `knowledge/_inbox/interior-ai/2026-07-01-photoreal-render-technique-DR.md` — source.
