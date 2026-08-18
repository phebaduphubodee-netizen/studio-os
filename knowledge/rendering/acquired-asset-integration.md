# Acquired-asset integration — keep/strip, re-tint, normalise, whole-piece swap

**Tier: REFERENCE (distilled from two staged DR units).** Not domain truth, not
statute. Nothing here outranks `knowledge/codes-th/`, the client contract, or an
owner-signed decision. A value becomes live only when a named file consumes it.

PROVENANCE — distilled 2026-08-17 from:
- `knowledge/_inbox/dr-acquired-mesh-integration-2026-08-10.md` (notebook
  1277ca41, 86 sources imported; every citation marker resolved to a source
  title — titles are quoted below where a number depends on them)
- `knowledge/_inbox/dr-whole-bed-swap-2026-08-17.md` (notebook 1036d123;
  **citation markers UNRESOLVED** — every §5–§7 number below is "a DR said so",
  one tier weaker than this file's other sections, and stays that way until
  someone resolves the markers in the NLM UI. Stated here so nobody upgrades it
  by forgetting.)
Consumers of record at distillation time: `pipeline/scripts/build_room.py`
(`_normalise_acquired`, keep-vs-replace branch), `pipeline/scripts/asset_scale.py`
(`pbr_map_roles`, `carries_a_pbr_surface`), `pipeline/scripts/wholebed_bench.py` +
`wholebed_rules.py` (headboard deletion + contact placement).

## 1. Keep vs strip — the decision, not a preference

KEEP the incoming texture set when: the asset is background/far-from-camera; or
its maps are already PBR-calibrated — albedo whites strictly below **240 sRGB**,
darks above **30–50 sRGB** [Learn Substance 3D Designer The PBR Guide – Part 2,
Adobe; Corona forum "Confusion about albedo in color and textures"].

STRIP and rebuild with studio shaders when: the asset is a foreground **hero**
prop (close-ups need SSS on stone, anisotropy on metals, micro-roughness);
textures violate energy conservation (pure 255 whites, baked-in lighting in the
diffuse); or the material graph arrives broken from a CAD export.

Already true in our code before the DR arrived (recorded so the DR is not
credited): Poly Haven assets carry normal + metallic-roughness, 3D Warehouse
assets carry base colour only (`asset_scale.pbr_map_roles`) — the DR added the
hero/background criterion, not the shelf split.

## 2. Re-tint law — colour moves, data maps never do

Albedo loads sRGB; **Roughness and Normal maps load Linear (Non-Color) and are
never routed through the colour correction** [An Idiot's Guide to ACES,
Toadstorm; Adobe PBR Guide Part 2]. The tint is a correction node (HSV or
equivalent) inserted between the albedo file and Base Color only; final
brightness stays inside the same 30–240 sRGB authoring band. Our retint already
does exactly this (Base Color link swapped, Roughness/Normal links untouched).

## 3. Tells of a disconnected import (inspection list)

- Glowing / uncalibrated albedo (≥255 whites → flattened shadows).
- **Flat specular response** — every surface answers the key light identically;
  no roughness variation [8 Key Architectural Visualization Tips, VirtualT].
- "Plastic" metals — metallic mask not 1.0, or no roughness variation.
- Fresnel violation — smooth dielectrics should sit near **2% to 5%** facing
  the camera and approach 100% at grazing angles [Mastering PBR Materials,
  Babylon.js docs]; imports that miss this read as toys.
- Texel-density mismatch against neighbours (blurry beside sharp).
- Obvious tiling repetition on large surfaces.
- Shading gradients / corner faceting from recomputed vertex normals.
- Edge halos between metal and dielectric regions from low-res masks.

## 4. Normalisation checklist (what `_normalise_acquired` implements or refuses)

- **Weld split vertices at 0.001 mm to 0.01 mm**, keeping genuine hard edges
  sharp [Standardized Asset Integration and Pipeline Calibration]. First real
  mesh through this path welded 4,652 split vertices — the mesh was split at
  every face, which is why its curved rim rendered faceted.
- Lock/respect explicit vertex normals on CAD-origin imports; unify normals;
  check backfaces.
- One UV set, non-overlapping shells, seams on hard edges.
- Texel-density targets by camera zone:
  hero foreground **2048 px/m to 4096 px/m**,
  midground 512–1024 px/m, props 200–512 px/m [Standardized Asset
  Integration and Pipeline Calibration]. RECORDED, NOT ENFORCED — this repo has
  no texel-density instrument yet, and adopting a number we cannot measure is
  how a threshold becomes decoration.
- Polygon budgets (background props 500–5,000 tris etc.) are GAMES-pipeline
  numbers; recorded, never enforced on stills.
- The 3ds Max/Revit unit-ritual sections of the source are NOT adopted — we
  ingest glTF and assert scale on every import (R8, fail-closed).

## 5. Whole-piece swap into built millwork (bed frame vs drawn headboard band)
### markers unresolved — see PROVENANCE

- Purchased whole beds arrive with their own headboard: ungroup and delete it
  (or delete its faces at element level), keep frame + mattress + bedding. Our
  `wholebed_bench.py` converged on this independently the same hour.
- **Mattress-to-headboard clearance 0.5 to 1.5 inches (12.7–38.1 mm)** — the
  frame butts the drawn band with a real gap, never 0.
- **Micro-gap 0.5 mm to 1.0 mm between touching solids** so occlusion shadows
  form instead of coplanar intersections.
- Sanity bands for judging a candidate's proportions: metal frames run
  **1 to 3 inches shorter** than the mattress; headboards run
  **6 to 8 inches wider** than the mattress per side.
- An excessive frame-to-band gap is closed with a modelled **pillowstop** /
  board shim — a real joinery solution, not a transform fudge.
- The source's cloth-sim recipe (friction 1.0, collision offset 0.05–0.1) is
  INAPPLICABLE while the bed-cloth class order is ACQUIRED (D-104); staged for
  a future lane that simulates.

## 6. Case-goods material policy (nightstands, dressers, shelving)
### markers unresolved — see PROVENANCE

- **Trial-by-Zoom**: place the asset under target lighting, render at final
  camera/resolution, inspect a 100% crop. Blurry grain, plastic highlights, or
  visible tiling fails the asset's materials → rebuild them.
- Normal maps load **Linear (gamma 1.0)**; concave-looking pores/bevels that
  should be convex mean the green channel is inverted — **Flip Y / Invert
  Green Channel** in the shader.
- Wood on jointed case goods: triplanar projection kills UV seams at corners
  and keeps veneer scale uniform on stretched imports.
- UV audit before a hero slot: apply a high-frequency checkerboard; skewing,
  stretching (the "taffy stretch"), or mismatched check sizes mean fabric
  weaves and grain will distort — reject or re-unwrap.

## 7. Texel density — the audit this repo does not yet have
### markers unresolved — see PROVENANCE

density = texture px / bounding size (m). 4K over a 2 m headboard = 2048 px/m.
Camera-zone targets: background 512 px/m · midground 1024 px/m · hero
2048–4096 px/m · macro 8192+ px/m. Blender-side measuring tool named by the
source: **Texel Density Checker** add-on. Coarse-density mitigation ladder:
UDIM split per component → seamless tiling multipliers → triplanar → macro +
micro normal blending. If adopted, the instrument comes FIRST (see §4's
recorded-not-enforced rule).

## 8. Honest gaps

- No numeric re-tint LIMIT exists here (acceptable ΔE/ΔL band before an
  acquired albedo's story breaks) — that question stays open; the 2026-08-17 DR
  slate carries it.
- The albedo authoring band (30–240 sRGB) vs `albedo_plausible()`'s 0.04–0.94
  float band remains UNRECONCILED by design — moving a threshold is its own
  decision with its own A/B (PR-only), never a side effect of distillation.
- Materials-by-role mapping (legs keep leg tone when a signed textile lands on
  an acquired mesh) is a build lane (P2h), not covered by either source unit.
