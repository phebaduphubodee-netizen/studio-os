# 3-leg materialized-render experiment — sitting_room

date: 2026-07-14 13:29  |  spec: `../../projects/PRJ-2026-002_c001-house/04_visualization/experiments/3leg-2026-07-14/sitting_room.materialized.spec.json`

| leg | what | image |
|---|---|---|
| A | baseline: hardcoded-palette control + render-hybrid@v004 full repaint | `../../assets/projects/PRJ-2026-002/renders/R_PRJ002_SittingRoom_Cam01_v01.png` |
| B | spec-materialized Cycles + render-polish@v001 finishing pass | `../../assets/projects/PRJ-2026-002/experiments/3leg-2026-07-14\leg_b_polish.png` |
| C | spec-materialized Cycles, no Gemini | `../output/room_sitting_room_eye_mat.png` |

## Material story (the spec's truth)

floor: warm oak plank PBR (CC0 texture set), polyurethane sheen; walls: matte warm-white interior wall paint (never pure white); feature wall: walnut feature wall (tinted oak PBR, drift breaks repeats); millwork: woodgrain laminate door face, slight sheen (FFE-BS01 console; Formica-class); glazing: the live glass__ glazing (Transmission 0.95); upholstery: warm off-white polyester weave (FFE-S01 Index Lamona sofa; colorway unconfirmed); wood furniture: warm oak plank PBR (CC0 texture set), polyurethane sheen; other furniture: neutral grey-beige solid (furn__ default); เก้าอี้อาร์มแชร์ 1: warm sand velvet, directional sheen (FFE-S03 Index Teddy pair; colorway unconfirmed); เก้าอี้อาร์มแชร์ 2: warm sand velvet, directional sheen (FFE-S03 Index Teddy pair; colorway unconfirmed); โซฟา 3 ที่นั่ง: warm off-white polyester weave (FFE-S01 Index Lamona sofa; colorway unconfirmed); โต๊ะกลาง (round coffee table): light birch veneer, clear acrylic lacquer (FFE-S02 IKEA BORGEBY)

## Leg A

- image_sanity: None
- critique mean overall (n=3/3 rolls): **3.7** verdicts={'SHIP': 1, 'REWORK': 2}
- critique per-dim means: composition 4.0, furniture_realism 3.333, lighting_quality 4.667, palette_coherence 4.667, photoreal_believability 3.333, proportion_and_scale 4.333, room_context 4.333, styling_and_life 3.0

## Leg B

- image_sanity: None
- critique mean overall (n=3/3 rolls): **2.5** verdicts={'REWORK': 2, 'PLACEHOLDER_ONLY': 1}
- critique per-dim means: composition 2.333, furniture_realism 4.0, lighting_quality 2.0, palette_coherence 4.0, photoreal_believability 2.667, proportion_and_scale 4.0, room_context 1.667, styling_and_life 0.0

## Leg C

- image_sanity: None
- critique mean overall (n=3/3 rolls): **1.5** verdicts={'NOT_CLIENT_READY': 3}
- critique per-dim means: composition 2.0, furniture_realism 2.667, lighting_quality 1.0, palette_coherence 3.667, photoreal_believability 1.0, proportion_and_scale 4.0, room_context 1.333, styling_and_life 0.0

## Structure: leg B vs its control (leg C)

- recall 0.842, precision 0.744 (informational) — REPORT-ONLY (no bound set — recall is scene-dependent; eyeball the RED overlay channel)
- the deciding artifact is the overlay (RED = structure lost, GREEN = invented): `../../assets/projects/PRJ-2026-002/experiments/3leg-2026-07-14\leg_b_vs_c.overlay.png`

## Materials preserved: ΔE00 dominant colours

- leg B vs leg C (did the polish repaint?): worst 10.402 — dominant-colour shift >2.0 — a large-area material/colour changed; inspect
- leg C vs leg A (how far the FF&E-true palette moved): worst 20.42 — dominant-colour shift >2.0 — a large-area material/colour changed; inspect

## Verdict

The judge is UNCALIBRATED (M3.2) — numbers above are advisory. The deciding eye is the owner's: compare the three images side by side.
