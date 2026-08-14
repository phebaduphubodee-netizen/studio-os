# สภาพผ้าบนเตียง / Bed-cloth state mechanisms — corner splay, hem resonance, loft, tucks, stack-on-cushion dent

> PROVENANCE: promoted 2026-08-13 from three staged DR units, all from NotebookLM
> notebook `ae3dd665` (blender-cloth-corner-drape corpus):
> - `knowledge/_inbox/dr-cloth-corner-drape-2026-08-11.md` (turn 1 — corner
>   held open; already CONSUMED into code at p2r22/p3r2 before this promotion)
> - `knowledge/_inbox/dr-cloth-hem-serration-2026-08-12.md` (p2r25 R1 stop —
>   periodic sine-hem)
> - `knowledge/_inbox/dr-cloth-state-loft-tuck-cushion-2026-08-13.md` (owner
>   verdict #2 p2r26 + C2-r27#1 + the bench folded-stack site)
> Raw turns: `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json`.
> **Tier REFERENCE — practice-report grounding, not domain truth, not statute.**
> No parameter below may gate a deliverable by itself; a value becomes live only
> when a named file consumes it and a LOOK/critic round judges the result.

## ลำดับอำนาจ / Authority + precedence

1. What a run of the actual solver MEASURES outranks every parameter below —
   starting points and a diagnostic map, not settings of record.
2. `pipeline/CLAUDE.md` §Blender build law binds: geometry via the DATA API, no
   `bpy.ops` on geometry, headless one-process-per-job. Modifiers (Soft Body,
   Hook, Displace, Smooth) and keyframes are data-API; the effector-weight
   keyframe path must be verified headless before first use.
3. This file.

## 1. Corner splay (มุมผ้ากางค้าง) — CONSUMED, kept here as the map

Diagnosis (2026-08-11 DR): a free corner must bend in two directions at once;
the default ANGULAR bending model resists that double curvature like a shell,
premature self-collision repulsion inflates an air bubble between folds, and a
55-frame bake freezes the corner mid-splay.

Ranked fixes and their consumption state (of record in
`pipeline/scripts/drape.py` + `pipeline/scripts/build_room.py`, gate-DELIV001-P2r22):

- `bending_model = 'LINEAR'` + bending 0.15-0.35, mass ~0.12 — CONSUMED
  PER-PIECE (throw + coverlet; the duvet keeps ANGULAR for its standing-fold
  preset). Failure mode: corner shard collapse if bending falls too low.
- self-collision distance 1-3 mm + self_friction 5→~12-15 — CONSUMED.
- frames 55 → 120-150, quality 12, collision_quality 8 — CONSUMED.
- Sewing-spring corner darts (`use_sewing_springs`, `sewing_force_max` 10-25) —
  recorded NEXT mechanism, needs dart cuts in `softgoods.flat_sheet`.

## 2. Hem serration (คลื่นคาบสม่ำเสมอเหมือน sine) — NOT yet consumed

Diagnosis (2026-08-12 DR): a UNIFORM quad grid draping under gravity is a
physical-numerical RESONATOR with a **single dominant buckling eigenmode** —
compressive stress along the free hem resolves at one wavelength. The LINEAR
bending model on a regular grid is *more* susceptible (grid-aligned virtual
cross-springs), and uniform shrink expands every structural spring identically
— exactly the symmetry the eigenmode needs. Bending stiffness only scales the
wavelength (~(B/K)^(1/4)) — which matches our p2r25 measurement (same lag,
softer teeth: autocorr 0.434→0.489, not reduced).

Levers, ranked; the two already-spent mechanisms (slack field, hem bending)
never broke the symmetry, so these are NEW mechanisms, not re-turns:

1. **Hem MASS** — a weighted hem strip: body ~0.12 → hem 0.25-0.5 kg (2-4×)
   via the mass vertex group. Never touched in our lane.
2. **Symmetry-breaking vertex SPACING at the hem** — irregular in-plane station
   spacing (or triangulated hem topology) removes the single eigenmode. The
   sheet stays FLAT — the enter-smooth law is untouched; this is the
   "irregular cell" half of the r23 triage suggestion, now with a mechanism.
3. **shrink_max ≤ ~5% along the hem** — over-contracting the edge is its own
   pucker source (throw currently ≈3%, inside the band; check per piece).
4. **Post-sim Smooth modifier on the hem vertex group** (factor ~0.5, 5-15
   iterations, after Cloth, before Subdivision) — render-side kill switch,
   damps serration, keeps aperiodic primary folds.
5. Simulate coarse, render fine (SurfaceDeform) — industry frame; heavier.

What this does NOT license: pre-wrinkled feedstock (z-noise). Spacing jitter is
in-plane and flat; the solver stays the only wrinkle author.

## 3. Stack-on-cushion dent (กองผ้าพับบนเบาะ) — CONSUMED p2r28

Diagnosis (2026-08-13 DR): the folded stack sits on a RIGID cushion, so contact
reads as plastic-on-plastic; C2 filed "ผ้าพับวางบนเบาะนุ่มต้องยุบ" four rounds
running and every knob available was a forbidden re-turn.

Mechanism: convert the cushion to a deformable target with **Soft Body** —
**goal stiffness ~0.5** via a painted vertex group (core holds, surface
yields), edges pull/push ~0.8 — so the stack DENTS the cushion. First
mechanism for this site that is not a knob re-turn.

CONSUMED 2026-08-14 (`drape.dent_soft_body`, gate-DELIV001-P2r28, D-046) with
three measured corrections the DR could not know: (1) a static presser has no
weight — the press must be a MOTION (keyframed travel; probe first measured
the cushion RISING off the collision field); (2) the soft body's own gravity
must be ZERO — the seat's rest shape is already its settled shape, and leaving
gravity on double-applies it; (3) the dent is measured on the yield band's own
verts — a z-window filter returned its own constant (36.0 mm twice) because
the overhanging stack puts seat-side verts in the presser's footprint.
Result: 23 mm dent from a 16 mm press; the four-round critic item was absent
from the next blind C2 read.

## 4. Batting loft (duvet/coverlet all-over undulation) — CONSUMED p2r28

The full frame is sim-coarse-render-fine (SurfaceDeform + post-sim Solidify
~10 mm) — heavier pipeline change. The REACHABLE half first: **procedural
quilting/loft via displacement driven by a distance-function thickness** on the
render mesh, no re-sim. Displacement on a subdivided cage is already
R8b-lawful.

CONSUMED 2026-08-14 (`softgoods.boundary_dist_weights` → `drape._freeze`
vertex-group solidify, gate-DELIV001-P2r28, D-047): 18→36 mm graded by
edge-distance, with two additions the DR did not carry — the CREASE is an
extra distance source (a 180° fold compresses batting; also the two layers'
solidify normals point OPPOSITE ways on a folded lattice, so an untapered roll
grazes its own visible surface), and the thickness biases UPWARD
(solid_offset 0.4) because batting squashes flat against what it lies on and
the lofted inner shell must clear the collider stack. duvet_fold octave
energy moved 1.91x → 1.80x toward the anchor.

## 5. Tucked-sheet fold irregularity (รอยเหน็บมือ) — R1-STOPPED p2r28, successor staged

Three techniques for the ruler-straight tucked fold:

- **Hook modifiers on hem vertex groups parented to animated empties** = the
  hand that tucks — localized asymmetric folds.
- **Gravity ramp keyframed 0.0→1.0 over ~40 of 120-150 frames** — tucks slide
  and settle instead of bouncing rigid.
- Asymmetric initial state (rotate the sheet before the drape): the 45-70°
  figure smells like a loose-drape number — verify before using on a MADE bed.

MEASURED DEAD END 2026-08-14 (2 mechanism cycles, R1 stop — gate-DELIV001-
P2r28): hook + pin weight 1.0 is an infinite-mass CLAMP, not a hand — the
settling roll lofts ~27 mm around press points frozen at feedstock height, so
every dip bottoms at one plane (35.8/33.4/33.3 mm, then 28.5/26.9/26.9 after
halving travel — cv 0.03 both, uniform by construction). The ramp lever is
also COUPLED to pins: on an unpinned sheet the weightless first third slides
laterally (52-64 mm proud, invariant to slack). Ramp CONSUMED per-piece where
pins exist (bench throw); duvet ramp waits for the tuck pins. The successor
mechanism set (spring pinning first: gradient weights + pin_stiffness
1.5-4.0) is staged in `knowledge/_inbox/dr-cloth-tuck-hands-2026-08-13.md` —
distill before the p2r29 re-entry.

## 6. Empirical chaos bands — what a believability test may cut against

Real re-draped fabric varies **±15% drape coefficient**,
**±25% fold/node dimensions**, **±3 fold count** between identical trials. A frame whose repeated
features vary LESS than this band reads as machine-made; a symmetry test can be
written against it — same family as the aperiodicity test that closed the
sine-hem's measurement side.

## 7. ช่องว่าง / Gaps — do not fill from model knowledge

- The corpus has **no physical constants for fold crease radius or stack-edge
  bulge** (stated explicitly in the 08-13 turn) — the folded-stack GEOMETRY
  question stays partly open; the dent mechanism (§3) does not depend on it.
- All numeric bands are model-cited REFERENCE values; `[n]` markers in the raw
  turns could not be resolved to source titles from the CLI (same caveat class
  as DRW-4). Original-source verification still owed; until then no band above
  is a threshold of record — bands parameterise TESTS, tests are judged by
  LOOK + critics.
- §2-§6 are UNTESTED against our solver as of promotion; §1 is the only tested
  section. Consumption state must be updated here when a round consumes a row.
- Nothing on knits, sheers, leather; settling drape only, no motion.
