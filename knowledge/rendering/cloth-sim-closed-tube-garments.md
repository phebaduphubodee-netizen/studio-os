# ผ้าจำลองบนทรงท่อปิด / Cloth sim on CLOSED-TUBE garments — the instability no quality knob reaches

> PROVENANCE: promoted 2026-08-02 from
> `knowledge/_inbox/nlm-cloth-closedtube/closed-tube-garment-sim-DR.md`
> (NotebookLM Deep Research, notebook `66d719d4-5d78-4dcb-9881-9773cebbb916`,
> 77 sources ready / 17 errored, **turn 1 only**).
> **Tier REFERENCE — practice-report grounding, not domain truth and not statute.**
> No parameter below may gate a deliverable by itself.
>
> **Turns 2–3 of that DR are NOISE and are excluded here.** `--iterate` auto-followed
> NotebookLM's own suggested topic, which drifted into vine-robot soft robotics
> because the web sweep read "closed tube" that way. Recorded as a lane pitfall, not
> as findings.

**Why this file exists.** A garment lane was stopped under R1 after a simulator ran
but would not stabilise: pieces froze, wadded or shredded across six hypotheses at
quick-rung cost, and one piece held a 27–34% defect rate through **every**
configuration tried — solver quality, mesh density, blocker shape, birth position.
A metric no knob in the lane can move is the tell that the cause is not in the lane.
This file names the mechanism that was missing.

## ลำดับอำนาจ / Authority + precedence

1. What a run of the actual solver MEASURES outranks every parameter below. These
   are starting points and a diagnostic map, not settings of record.
2. `pipeline/CLAUDE.md` §Blender build law still binds — geometry via the DATA API,
   no `bpy.ops` on geometry, headless one-process-per-job.
3. This file.

## 1. The mechanism — two causes, both specific to CLOSED tubes

A flat sheet and a closed tube are not the same problem, and this is why:

1. **Self-collision margin conflict.** A draped sleeve folds flat and brings its own
   interior walls into contact. If the tube's cross-section `D_s` is smaller than
   **2 × the collision margin `d_col`**, the solver registers *perpetual*
   interpenetration. In a closed cylinder the repulsive impulses have nowhere to
   dissipate — they push vertices across the central axis, and the result is a
   numerical feedback loop: high-frequency jitter, crumpling, or explosive shredding.
2. **Poisson lateral contraction.** Longitudinal tension from hanging contracts the
   material laterally. Harmless on a flat sheet; in a closed tube it pulls opposing
   walls **inward past the self-collision threshold** — i.e. it *creates* cause 1
   over time, out of a geometry that started legal.

**The consequence worth carrying:** if `D_s < 2·d_col` anywhere along the tube, no
solver-quality setting fixes it, because quality does not change the geometry that
violates the condition. Check the condition before spending another sweep.

## 2. Remedies, in the order that changes the most

- **Open-form panel feedstock + virtual sewing.** The industry route: flat 2D
  pattern panels arranged around the support and joined by sewing springs. Panels
  triangulated with isotropic Delaunay — quads carry an H/V bias that resists
  diagonal shear and buckles blocky. Ramp gravity 0 → 9.8 m/s² over the first frames
  so sewing forces do not tear the panels.
- **Pressure / volume preservation** — treat the tube as a soft pneumatic chamber.
  **Critical for anything with openings** (cuffs, neck): a vertex group weighted 1.0
  on body faces and **0.0 on open-boundary vertices**, selected in the Pressure
  settings. Without the mask the holes leak pressure and generate propulsion.
- **Internal Springs**, as the alternative to pressure: Max Spring Creation Length
  slightly greater than the tube diameter, with **Check Surface Normals** ON so
  springs only bridge opposing interior walls rather than stitching a fold shut.
- **Bending model: Linear, not Angular.** Angular overshoots explosively in
  compressed zones (a shoulder seam over a hanger); Linear distributes the load
  through face-diagonal springs.
- **Single-shell, zero thickness.** Pre-modelled thickness guarantees self-collision
  failure. Solidify AND Subdivision go **below** the Cloth modifier in the stack.
- **Collision proxy, never the visible mesh.** A hidden smooth low-poly capsule,
  shade-smooth, normals outward — not the high-resolution support geometry.
- **Pinning at 0.7–0.9, not 1.0.** Full pinning tracks perfectly and never wrinkles;
  the band blends tracking with drape.

## 3. Symptom → cause → remedy

| symptom | cause | remedy |
|---|---|---|
| explodes on frame 1 | unapplied scale; self-collision distance exceeds interior clearance | apply transforms; normals outward; Self-Collision Distance 0.001–0.002 m; **Impulse Clamping** 0.1 |
| jitter at the support | sharp collider; Angular bending overshoot | Linear bending; smooth proxy; collider Thickness Outer 0.002 m |
| sleeves collapse flat | **Poisson** contraction unresisted | Pressure with a hole-masked vertex group, or Internal Springs + Check Surface Normals |
| penetrates the support | substeps too low for collider speed | Quality Steps 20–30; Collision Quality 8–12; cloth density ≥ collider density |
| droops / over-stretches | mass:stiffness ratio too high; frame-1 gravity shock | Vertex Mass 0.1–0.3 kg; gravity ramp over 30 frames or a Rest Shape Key; Tension/Compression 50–100 (cotton) |

## 4. What this repo had already earned, independently

Two of the remedies above were already discovered here by failure, before the
research arrived, and that agreement is the strongest thing in this file:

- **single-shell, no pre-modelled thickness** — reached by three failed bakes and
  written down as the cloth-stack contact law;
- **hidden low-poly collision proxy** — found empirically as a torso blocker.

We had the *what*; the source supplies the *why*. Nothing else here has been tested
against our solver.

## 5. ช่องว่าง / Gaps — do not fill from model knowledge

- **Untested.** No parameter in §2 or §3 has been run against the stopped lane. The
  `D_s < 2·d_col` condition is a HYPOTHESIS that explains the recorded 27–34%
  residual; it has not been checked by measuring the geometry.
- Turn 1 only. Turns 2–3 are contaminated (see the provenance block) and no claim
  may be drawn from them.
- Nothing on materials other than cotton-like wovens; no knits, leather or sheers.
- No guidance on animation — everything here concerns a settling drape, not motion.
