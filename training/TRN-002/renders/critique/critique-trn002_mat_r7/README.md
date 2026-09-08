# Bundle — trn002_mat_r7 (PHASE 2 round 1: first frame with real materials and light)

Render: `_private/…/renders/critique/critique-trn002_mat_r7/trn002_mat_r7.png`
Spec: `training/TRN-002/spec_r9.json` (54 masses — the herringbone floor is new).

## What this round built

- **Materials** measured per surface as ratios to a declared reference (back
  wall at 0.80 albedo), one row per material with its basis recorded in
  `trn002_materials.PALETTE_PROV`. The "oak band" is corrected to travertine.
- **Light** built from the measured story, whose findings refuted the obvious
  reading four ways (window is not the key; downlights make no pools; the lamp
  is off; unlit shelves stay dark).
- **Herringbone floor** as real geometry: 458 planks at the measured 132.1 ×
  619.6 mm, 45°, phase-anchored on the target's own joint darkness, each plank
  carrying its own UV frame so the grain turns with the chevron.
- **trn002_lightcheck** — the numeric track, sampling both frames through an
  object-ID mask and reporting a per-object ladder, with an alignment check
  that voids any row whose object is not where the target's is.

## Numeric state (lightcheck vs target)

| | ours | target |
|---|---|---|
| p50 | 0.412 | 0.372 |
| p95 | 0.633 | 0.636 |
| p1 | 0.074 | 0.004 |

The ladder tightened from the clay baseline's 0.1–6.5 spread to mostly
0.5–1.7 once the key was moved from "far and flat" to "close and aimed down" —
a change the ladder found and a LOOK could not: the far key lit the back wall
directly, where the target's back wall is bounce-lit (flat in x, −7.7%/m
upward). Bed, bench and mattress now sit within 6% of their target ratios.

## C3 triage (R7)

1. **"แสงแบน ไม่มี contact shadow, contrast ต่ำ"** → **ACCEPTED as an
   observation, REFUTED as a mechanism.** The observation is confirmed by our
   own numbers: p1 0.074 against the target's 0.004, and range 12.8:1 against
   its 182:1. But C3's stated evidence — "the room's main light is downlights,
   which should make bright pools and hard shadows" — is exactly what the
   measurement pass killed twice: on the ceiling the glow dies within
   120–200 mm, and the parquet directly under dl_1 is DARKER than a metre
   away. Making the downlights the key would move us away from the target, not
   toward it. **Lane:** contact shadows and shadow depth are real work
   (higher AO/bounce fidelity, and the foot-of-bed and nightstand contacts) —
   but the flatness is to be paid for by *deepening the darks*, not by
   introducing a directional key the target does not have.
2. **"ดาวน์ไลท์ยังมีวงเรืองบนฝ้า"** → **ACCEPTED.** Ours still glows despite
   dropping the fixtures to 1.6 W and moving the brightness into an emissive
   lens. Next: the lens plane sits 5 mm below the ceiling and spills upward —
   it needs to be recessed into its own housing so nothing lights the ceiling
   plane. Measurable: the target's ceiling returns to background within
   120–200 mm of each lens.
3. **"ช่องชั้นที่ไม่มีไฟสว่างเกือบเท่าช่องที่มีไฟ"** → **ACCEPTED, and it is
   a measured miss.** The target holds unlit 0.099 vs lit 0.283 vs strip
   0.726 — a 2.9:1 step our world light is filling in. The world is already
   down to 0.018; the remaining lift is bounce off the very bright travertine.
   Next: check the etagere back panel's own value against the 0.099 floor.
4. **"วัสดุเรียบเหมือนพลาสติก"** → PARTIALLY ACCEPTED. Travertine and floor
   carry maps; the fabrics currently carry only a normal map and the walls
   none at all — the last by measurement (target texture 0.03). The honest
   next step is per-surface: the travertine's porosity is real and missing.
5. **"พื้นไม้ไม่มีรอยต่อระหว่างแผ่น"** → REFUTED as buildable-at-this-camera:
   the joints are 2 mm, which is 0.58 px at this focal length and distance —
   geometrically unresolvable, the same verdict the pattern pass reached
   independently for the wardrobe reveals. It must be matched photometrically
   (a darker joint value), never modelled as a groove.

## Ladder state

- C1: pair/blend `trn002_pair_r7.png`, and the numeric ladder above.
- **C2 (Cowork, R7c): PENDING** — attach `trn002_mat_r7.png` + this bundle's
  `PROMPT.md`.
- C3 (Gemini): `ANSWER_gemini25pro.md`, triaged above.
