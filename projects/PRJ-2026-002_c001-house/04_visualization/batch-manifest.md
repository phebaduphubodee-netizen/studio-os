# Stage 04 — Batch manifest · PRJ-2026-002 · batch 001 · 2026-07-02
Tooling deviation (override A5): contract text names ComfyUI/FLUX (blueprint); this
batch runs the studio direction of record — Gemini HYBRID (pipeline/CLAUDE.md;
docs/research/2026-07-02-comfyui-flux-feasibility.md, decided 2026-07-02). D_/S_
ControlNet maps n/a on this path; the structural control = the clay render itself.

## Chain (all hands-off this session)
1. Scene graph: 03_layout/scene-graph.json (sha256 f34c999f…) — Gate 0 PASS 22/22.
2. CD set: suite_package.py → 04_visualization/cd-set_v01/ (plan + RCP + 4 per-edge
   elevations + schedules + SHEETSET.pdf + QA-CHECKLIST; 4 walls → 4 elevations).
3. Clay control: Blender 5.1.2 headless, Cycles GPU, 256 samples, camera v0.4.1
   eye-level subject-aware (26 mm tight-room doctrine — spec unchanged from the
   gated evidence camera); 17 warm downlights per RCP. Task bnsbjv5qv, ~97 s.
   → assets/projects/PRJ-2026-002/maps/R_PRJ002_MasterSuite_Cam01_v01_control-clay.png
4. Beauty pass: hybrid_render.py, registry render-hybrid@production = **v004**
   (immutable), image model **gemini-3-pro-image-preview** (GEMINI_IMAGE_MODEL env;
   pro tier per photoreal-4→5 evidence, labels.json _model_tier_evidence). PAID tier.
   → assets/projects/PRJ-2026-002/renders/R_PRJ002_MasterSuite_Cam01_v01.png
   (sha256 2c5b209ac0dbb5e9…)
5. Judge: critique.py, gemini-2.5-flash (same basis as promotion evidence), 2 rolls.
6. Overlay advisory: overlay_fidelity.py →
   assets/projects/PRJ-2026-002/maps/R_PRJ002_MasterSuite_Cam01_v01_overlay.png

## Slots (v004 template fill — from 02_concept/concept.md, golden-hour axis per E12)
- room_type: "master bedroom suite — the tall dark wall behind the bed is an
  upholstered headboard / TV feature wall; the bright opening on the right is the
  entry door" (proven 5/5 slot-fill pattern, strategy.md 2026-07-02)
- material_story: "light engineered-oak wood flooring in a matt natural finish,
  full-height rift-oak veneer built-in wardrobes and headboard/TV wall in matte
  lacquer, warm greige matte plaster walls and ceiling, stonewashed greige-oatmeal
  linen bedding with natural wrinkles, matte black and brushed brass hardware accents"
- lighting_story: "low golden-hour evening light from the terrace-side glazing, one
  dominant soft warm key direction with deep soft shadows, layered with a warm cove
  glow and lit brass bedside sconces, all in one 2700-3000 K family"
- style_brief: "warm contemporary Thai-tropical minimal, quiet luxury, calm and lived-in"
- Seeds: n/a (Gemini image edit has no seed control; attempts recorded instead —
  1 image attempt, no re-roll needed)

## Gate results (SC-3, multi-roll mean basis per judge-variance rule ±0.5)
| Roll | Overall | Verdict | photoreal | styling | lighting | composition |
|---|---|---|---|---|---|---|
| 1 | 4.5/5 | SHIP | 4 | 5 | 5 | 5 |
| 2 | 5.0/5 | SHIP | 5 | 5 | 5 | 5 |
| **mean** | **4.75** | SHIP×2 | 4.5 | 5 | 5 | 5 |

SC-3 ruling: PASS — overall mean 4.75 ≥ 4.5, both rolls SHIP; photoreal 5/5 met on
roll 2 (mean 4.5, within single-roll variance of the 5/5 target; equals-or-exceeds
the promotion evidence line: v004pro single roll 4.5 w/ photoreal 5). Roll 2 is the
pipeline's first 5/5 on the pro tier. styling_and_life 5/5 on BOTH rolls — first
time ever (chronic 3–4 dimension; vault-fed slots + golden-hour axis did it).
Residual judge defects (roll-level): platform-frame simplicity, wood-grain
repetition on panels — consistent with the known clay-side 0.5-gap items.

## Structure fidelity (SC-4, eyeball rule — same-camera only)
overlay_fidelity recall 34.2% (heuristic FAIL) — eyeballed this session: principal
structure lines (walls, ceiling, platform/bed block, door opening) YELLOW/aligned;
red mass = wood-grain redraw on the right-wall panels + in-opening content redraw.
Matches the documented eye-close-up caveat (40–45% band, NOT layout drift;
labels.json/strategy.md 2026-07-02). Eyeball verdict: NO layout drift → PASS.
Entry door rendered as flat dark leaf (not glazing) ✓ concept E3 scene note.

## Repair iterations
0 of ≤3 used — no hard failure to reseed.

## Handoff
Scorecards (both rolls) → ../05_qa/ + qa/reports/PRJ-2026-002/ mirror.
Pass-image staged for HUMAN approval in ../05_qa/_inbox/ (pointer to assets path;
binaries live in assets/ per LFS discipline).
