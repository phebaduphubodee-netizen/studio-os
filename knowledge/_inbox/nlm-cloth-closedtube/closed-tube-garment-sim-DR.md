---
title: "Closed-tube garment sim instability — mechanism + parameter-level remedies (Blender cloth solver)"
source: notebooklm-deep-research
notebook: 66d719d4-5d78-4dcb-9881-9773cebbb916  # fresh DR notebook, 77 sources ready / 17 error
turns: 1 (of 3)  # turns 2-3 are NOISE: --iterate auto-followed NLM's suggested topic, which drifted to vine-robot robotics (the web sweep caught soft-robotics "closed tube" sources) — recorded as an iterate-loop pitfall; ignore those turns
date: 2026-07-30
tier: REFERENCE — practice-report grounding; no number below may gate a deliverable by itself
status: staged — distill into knowledge/ before the (ก3) open-form build session fires
privacy: generic physics/tooling question only; nothing project- or client-identifying left the machine
context: fired under the DR-PULL rule (CLAUDE.md §External research lane, adopted 2026-07-30) on the R1-stopped mechanism mystery from 5391929/48bc1cf — the first DR in this repo to arrive BEFORE its build session
---

# Closed-tube garment sim — what the DR says, mapped to our recorded failures

**[n]-marker posture** (same as nlm-process-rules): marker→source map not
exportable; citations read "turn 1"; notebook 66d719d4 is the audit trail —
do NOT prune until distilled into knowledge/. Full verbatim answer in sibling
`qa-history.json`.

## The mechanism (why clothcheck saw instability "no knob reaches")

Two named physical causes, both specific to CLOSED tubes (turn 1):

1. **Self-collision margin conflict.** A draped sleeve folds flat, bringing
   interior walls into contact. If tube cross-section D_s < 2 × collision
   margin d_col, the solver registers PERPETUAL interpenetration; in a closed
   cylinder the repulsive impulses cannot dissipate — they push vertices across
   the central axis → numerical feedback loop → high-frequency jitter,
   crumpling, or explosive shredding.
2. **Poisson's-ratio lateral contraction.** Longitudinal tension from hanging
   contracts the material laterally; harmless on flat sheets, but in a closed
   tube it pulls opposing walls inward past the self-collision threshold.

Mapping to our three quick-rung failures (5391929): 45-frame freeze/jitter ↔
sharp collider + Angular bending overshoot; 85-frame wad collapse ↔ Poisson
contraction with no structural resistance; shredded-rag ↔ the margin-conflict
feedback loop. The 27-34% DNA that never converged (48bc1cf) is consistent
with a geometry whose D_s sits below 2·d_col somewhere along the tube — a
property no solver-quality knob changes, which is what our 6-hypothesis sweep
measured.

## Remedies (parameter-level, turn 1)

- **Open-form panel feedstock + virtual sewing** — confirms (ก3) as the
  industry-standard route: flat 2D pattern panels arranged around the hanger,
  joined by sewing springs (Blender tools named: *Garment Tool*, *Seams to
  Sewing Pattern*). Panels triangulated with isotropic Delaunay — quads carry
  H/V bias that resists diagonal shear and buckles blocky. Ramp gravity
  0→9.8 m/s² over the first frames so sewing forces don't tear the panels.
- **Pressure / volume preservation** — turn the tube into a soft pneumatic
  chamber. CRITICAL detail for shirts (open cuffs/neck): vertex group with
  weight 1.0 on body faces, 0.0 on open-boundary vertices, selected in the
  Pressure settings — otherwise the holes leak pressure and generate
  propulsion. Alternative: **Internal Springs** with Max Spring Creation
  Length slightly > tube diameter + **Check Surface Normals** on, so springs
  only bridge opposing interior walls.
- **Bending model: Linear, not Angular** — Angular overshoots explosively in
  compressed zones (shoulder seam on hanger); Linear distributes via face-
  diagonal springs. Likely relevant: our stable-vs-unstable DNA split.
- **Single-shell zero-thickness** — pre-modeled thickness guarantees self-
  collision failure; Solidify AND Subdivision go BELOW the Cloth modifier.
  (Independently matches our earned [[cloth-stack-contact-law]].)
- **Collision proxy** — never the visible high-res hanger; hidden smooth
  low-poly capsule, shade-smooth, normals outward. (Matches our hidden torso
  blocker discovery — we found the what, the DR adds the why.)
- **Pinning** — weight 0.7-0.9 at shoulders (not 1.0) blends tracking with
  wrinkling; Hook-modifier-on-empty for hanger transport; **Rest Shape Key**
  to start pre-draped.

## Failure→remedy diagnostic table (turn 1, condensed)

| Symptom | Cause | Remedy |
|---|---|---|
| Explodes frame 1 | unapplied scale; self-col distance > interior clearance | apply transforms; normals outward; Self-Collision Distance 0.001-0.002 m; Impulse Clamping 0.1 |
| Jitter at hanger zone | sharp collider; Angular bending overshoot | Linear bending; smooth proxy; obj-collision distance + collider Thickness Outer 0.002 m |
| Sleeves collapse flat | Poisson contraction unresisted | Pressure (hole-masked vertex group) or Internal Springs + Check Surface Normals |
| Penetrates hanger arms | substeps too low for collider speed | Quality Steps 20-30; Collision Quality 8-12; cloth density ≥ collider density |
| Droops/over-stretches | mass:stiffness too high; frame-1 gravity shock | Vertex Mass 0.1-0.3 kg; gravity ramp over 30 frames or Rest Shape Key; Tension/Compression 50-100 (cotton) |

## Ops notes for the record

- DR budget: 1/20 in 24h (wrapper-reported). 94 sources imported, 77 ready /
  17 errored — grounding valid per the wrapper's settle gate.
- NEW PITFALL: `--iterate` follows NLM's own suggested topics, which come from
  the whole imported corpus, not our question — a "closed tube" web sweep
  captured vine-robot robotics and both iterate turns chased it. For scoped
  DRs, prefer explicit `--ask` follow-ups over `--iterate`, or vet the
  suggestion before spending the turn.
