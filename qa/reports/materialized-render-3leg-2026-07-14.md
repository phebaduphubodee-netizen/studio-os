# Materialized-render 3-leg experiment — sitting room (PRJ-2026-002), 2026-07-14

**Owner direction under test:** move ALL design authority (materials + lighting) into the
spec — deterministic, ownable, FF&E-groundable — and narrow Gemini from "repaint the
render" to "close the shot" (micro-realism only). This experiment measures what that
costs and buys TODAY, on the one room that is fully gate-clean.

## What was built (all landed, reviewed, tested)

- `pipeline/scripts/material_presets.py` — spec-selectable material presets (pure
  stdlib): 19 presets in 3 tiers (REFERENCE = knowledge/materials/bsdf-material-presets.md;
  STUDIO = the live gate-proven palette verbatim; DESIGN-INTENT = derived for the real
  FF&E picks). Authoring bounds enforced at resolve time (30–240 albedo band, roughness
  [0.03, 0.97], binary metalness, sRGB→linear once).
- `build_room.py` — `materials` block in room-spec@0.2 (optional; absence = legacy
  palette EXACTLY): surfaces (floor/walls/feature_wall/millwork/glazing/fixtures),
  families (fabric/wood/neutral), per-element presets (imported-model retint keeping
  rough/normal maps + `em-` primitive routing); `--suffix=` output isolation; headless
  failure now exits 1 (was: Blender swallowed errors and exited 0).
- `pipeline/prompts/registry/render-polish/` v001 — NEW intent: layout-lock (verbatim
  strength) + materials-lock + no-add/no-remove; licence = photographic finishing only.
  `{material_story}` is COMPUTED from the spec (material_presets.material_story), so the
  prompt cannot describe materials the render does not show.
- `pipeline/scripts/experiment_3leg.py` — the driver (paid calls only behind explicit
  flags; thresholds at call sites, `qa/thresholds.yaml` untouched).
- Review: 26-agent adversarial pass, 19 confirmed findings → 6 defect families, ALL
  fixed + test-pinned before any paid call. The two HIGH: (1) element presets could
  silently not-bind while `material_story` still asserted them to Gemini — now a
  reconciliation gate that aborts the build (`reconcile_elements`); (2) headless exit-0
  on invalid spec — now `os._exit(1)`, proven live (`blender_exit=1`).
- Tests: full suite **1419 passed** (was 1393; +26 this lane, incl. U7-style pins on
  every preset value).

## Material truth (the part that is PROVEN, not judged)

`.blend` probe of leg C — every per-element preset landed EXACTLY (linear values):
armchair cushions (0.552, 0.397, 0.275) = #C4A98F velvet_sand, sheen 1.0, wood legs
untouched; sofa (0.807, 0.761, 0.672) = #E8E2D6 polyester weave; coffee table
(0.694, 0.539, 0.347) = #D9C29F birch. The render now tells the FF&E truth: **Lamona =
polyester (not bouclé), Teddy pair = velvet (not bouclé), BORGEBY = birch (not dark
oak)** — three material lies of the hardcoded palette, corrected at the source.

## The three legs (same room, same auto eye camera)

| leg | what | judge mean (3× gemini-2.5-pro) | key dims |
|---|---|---|---|
| A | old clay + render-hybrid@v004 FULL repaint (existing baseline) | **3.7** (SHIP/REWORK/REWORK) | lighting 4.7, styling 3.0, furniture_realism 3.3 |
| B | spec-materialized Cycles + render-polish@v001 (pro) | **2.5** (REWORK ×2, PLACEHOLDER) | **furniture_realism 4.0**, palette 4.0, styling **0.0**, room_context 1.7, lighting 2.0 |
| C | spec-materialized Cycles, no Gemini | **1.5** (NOT_CLIENT_READY ×3) | proportion 4.0, lighting 1.0, photoreal 1.0 |

Instruments: overlay B-vs-C recall 84.2 % / precision 74.4 % (layout held; the RED
channel of `leg_b_vs_c.overlay.png` is the real verdict); ΔE00 dominant-colour B-vs-C
worst 10.4 — the polish pass did shift large-area TONE (a strong warm relight of the
walls). Per-piece materials survived (see furniture_realism 4.0), but 10.4 says the
"keep lighting exactly" clause is not yet fully honoured — v002 material for the
polish intent. Artifacts: `assets/projects/PRJ-2026-002/experiments/3leg-2026-07-14/`.

## Honest verdict

**The headline number goes AGAINST the polish leg today (3.7 vs 2.5)** — but the dims
say the gap is NOT materials:

1. Leg B **beats** the baseline on furniture_realism (4.0 vs 3.3) — spec-true materials
   + finishing pass render *better furniture* than the full repaint.
2. What kills B/C is everything the room does not CONTAIN: styling_and_life 0.0 (no
   rug/curtains/pillows/art/plants — we forbade Gemini from inventing them), room_context
   (no baseboards/trim/ceiling in frame), flat lighting (the room's real south glazing to
   the terrace is not modelled as an opening, so there is no daylight key).
3. Leg A's advantage is largely **hallucinated decor** — and the judge itself dockets it
   as "sterile and cliché … default assets", "plastic plant", "art practically a blank
   texture". That decor is unsourceable fiction; it scores points while being exactly
   what the sourceability north star exists to eliminate.

Caveats: judge is UNCALIBRATED (M3.2; designer 26/26 REWORK history) — direction of the
gap is meaningful, magnitudes advisory; one room; leg-A mean drifted 3.5→3.7 across
batches (within known variance).

## What this buys the direction

The deficit list of leg B is **finite and deterministic** — each item is spec-buildable
and sourceable-compatible:
- **Scene dressing**: rug under the conversation group (generalize `_add_rug` beyond the
  hard-coded lounge zone), curtains at glazing, wall art slot, plant — the UNWIRED
  rug/curtain WARN rules in `knowledge/rendering/cycles-lighting-camera-presets.md:262-282`
  name exactly this list. Dressing items can carry ffe_tag like any other item.
- **Architectural finish**: baseboard/trim runs are millwork-generator work.
- **Daylight**: model the room's REAL south glazing as an opening (it exists on the
  plan — the spec estimates it away) + the deferred daylight key (values already staged
  in cycles-lighting-camera-presets.md §2, scoped Warm Luxury/Daylight).
- **Polish v002**: tighten the relight licence (the ΔE00-10.4 lesson) once the scene
  carries its own lighting story.

Recommended sequence: dressing + opening/daylight first (they move styling_and_life and
lighting_quality, the two 0-and-2 dims), then re-run this same 3-leg harness — the
experiment is now a one-command re-measure.

## Files

- Experiment bundle: `assets/projects/PRJ-2026-002/experiments/3leg-2026-07-14/`
  (leg_b_polish.png, leg_b_vs_c.overlay.png, experiment_3leg.{json,md}); leg C also at
  `pipeline/output/room_sitting_room_eye_mat.{png,blend}`; leg A unchanged at
  `assets/projects/PRJ-2026-002/renders/R_PRJ002_SittingRoom_Cam01_v01.png`.
- Spec variant (geometry byte-identical, re-gated clearance PASS 0/0 + FUNCTION PASS):
  `projects/PRJ-2026-002_c001-house/04_visualization/experiments/3leg-2026-07-14/sitting_room.materialized.spec.json`
- Review evidence: workflow wf_44cb0317-dda (26 agents, 19 confirmed → all fixed).
