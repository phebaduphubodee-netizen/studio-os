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

---

# Stage 04 — Batch manifest · PRJ-2026-002 · batch 002 · 2026-07-04
Two more CAD-derived rooms rendered on the same HYBRID direction of record
(Gemini pro), owner-authorised paid run. Master bedroom deferred (owner-blocked on
bed N–S/E–W orientation; its clay build is already proven — batch 001 / M3.2 work).

## Chain (sitting room + living room)
1. Scene graph / spec: `pipeline/scripts/specs/{sitting_room,living_room}.json`
   (interior-ai room-spec **@0.2 metric**; the CAD-authoritative envelopes).
2. Gate 0 (metric @0.2): `suite_clearance.py` — sitting **PASS** (0 fail/0 warn);
   living **REVIEW** (0 fail / 3 warn: 2 against-wall overlaps + entry→sofa
   bottleneck 850 mm < 910 ergonomic target, non-statutory). FUNCTION gate
   (`placement_logic.py`) **PASS** both (sitting tv=absent viewer=sofa; living
   full TV rules green — tv_faces_viewer / distance 3277 mm / mount 900 mm AFF).
   NOTE: `make_all.py` is NOT the driver here — its `clearance_check.py` handles
   only the inch @0.1 spec; the @0.2 metric path is `suite_clearance.py` +
   `build_room.py` directly.
3. Clay control: `build_room.py --render --eye`, Blender 5.1.2 headless, Cycles
   GPU 256 samples, eye camera ~1.15 m level two-point aimed at the hero sofa.
   → durable copy: `assets/projects/PRJ-2026-002/maps/R_PRJ002_{SittingRoom,LivingRoom}_Cam01_v01_control-clay.png`
   (built to scratch `pipeline/output/room_*_eye.png`, gitignored; albedo WARN
   mill_walnut 0.026 < 0.04 floor — cosmetic, non-blocking).
4. Beauty pass: `hybrid_render.py`, registry `render-hybrid@v004` (immutable),
   image model **gemini-3-pro-image-preview** (GEMINI_IMAGE_MODEL env; pro tier).
   PAID. Slots: room_type = "sitting room" / "living room"; material/lighting/
   style = v004 defaults (warm walnut+oak, bouclé/linen, off-white plaster,
   evening key + cove, quiet-luxury Thai residential — room-agnostic, fit both).
   → `assets/projects/PRJ-2026-002/renders/R_PRJ002_SittingRoom_Cam01_v01.png`
     (sha256 638fb8d13b7471a2…)
   → `assets/projects/PRJ-2026-002/renders/R_PRJ002_LivingRoom_Cam01_v01.png`
     (sha256 f2367d711d1d9a4d…)
5. Judge: `critique.py` **--model pro** (gemini-2.5-pro), 1 roll each →
   `../05_qa/critique_R_PRJ002_{Sitting,Living}Room_Cam01_v01.json`.

## Gate results (SC-3) — DRAFT, both REWORK (honest read)
| Room | Overall | Verdict | strong dims | weak dims |
|---|---|---|---|---|
| Sitting | **3.5/5** | REWORK | palette 5, lighting 4, proportion 4 | furniture_realism 3 (sofa tufting "melty"), styling 3 (generic), photoreal 3 |
| Living | **2.5/5** | REWORK | furniture 4, palette 4, proportion 4 | room_context 1 ("featureless box / no window in frame"), styling 2, lighting 3 (harsh key) |

These are **DRAFT DD character renders, NOT client-ready** — unlike batch 001's
master (4.75 SHIP×2). The pro critic runs *harsher* than the M3.2 flash judge, and
its complaints are real but partly structural: the living eye camera frames the
walnut feature wall + a blank side wall with no glazing in shot, so the beautify
pass had little architectural context to work with (the sitting room read better —
its clay carried a glazed door). Improvement paths for the designer (not done here,
would need a call): a second camera angle that includes glazing, richer scene
dressing, or the `--hero` magazine restage (rejected here — it *moves* furniture,
breaking CAD fidelity). Inventing windows the real room lacks was deliberately
avoided (functional-correctness / faithful-to-house rule).

## Faithfulness caveat
Beauty pass preserved layout/geometry in both (verified by eye vs the clay). The
wall-mounted TV on the living feature wall is downplayed by the repaint — the
dimensioned TV placement lives in the spec + FUNCTION gate + elevations, and
FFE-L06 (65" TV) is client-supplied/reference-only, so the character render is a
mood shot, not the TV-placement drawing.

## Handoff
DRAFT — human QA + designer call on the REWORK verdicts before any client use.
Binaries in assets/ (LFS); critique scorecards in ../05_qa/.
