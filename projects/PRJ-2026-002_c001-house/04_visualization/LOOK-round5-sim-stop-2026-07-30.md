# LOOK round-5 — 2026-07-30 — garments into the solver, R1 STOP called

Owner verdict on the g9 reference round: "ยังไม่เหมือนของจริง". Third consecutive
fail of the procedural garment lattice = the R1 halt signal (same fix-shape
repeated). The mechanism evidence in this room: every simulated cloth (coverlet,
duvet, throw) has passed the owner's eye; every analytic one has failed. So round
5 put the shirts through the cloth solver — pinned at the hanger zone, settling
under gravity (`styling` declares a `cloth` block; `_emit_style_part` routes it
to `drape.bake_sheet`; trousers exempt, measured 2.2 mm of settle).

## The three quick-rung states (each ~3 min wall, no full-price spend)

1. **45 frames, pins only** — real cloth character appears for the first time
   (the grey shirt's body reads as fabric), but sleeves freeze MID-SWING.
2. **85 frames, pins only** — the pendulum dies, and the unsupported tube
   SELF-COLLAPSES: the grey shirt crumples into a wad.
3. **85 frames + hidden torso blocker** (a slimmer copy of the body as a passive
   collider — the bed's sim-surface pattern inverted; hide_render, dropped after
   bake) — the dark shirt is the closest-to-real garment this project has ever
   rendered, BUT the grey shirt SHREDS on the faceted blocker.

## R1 stop

Three attempts, three distinct failures, parameter space deep (collision
quality, blocker resolution, stiffness, damping…) — the exact shape of the
round-3 cloth thrash. Per R1 the fourth knob does not get turned without a
verdict. `styling.SIM_GARMENTS = False` gates the lane: the default build
reproduces the committed g9 procedural read; flipping the flag reproduces the
experiments exactly (2119 tests pin both states of the contract).

## The decision the gate asks for

- (ก) fund the sim lane properly: one focused session, 2-full-cycle budget, a
  shred-detector instrument first (face-normal-variance — already named as the
  candidate in the cloth-stack law), then a per-piece stability ladder, the way
  the bed stack earned its pass.
- (ข) accept g9 geometry as structurally correct (sparse, sleeves, construction
  cues all reference-grounded) and hand cloth MICRO-realism to the lane the
  pipeline always assigned it to: material/light pass + the Gemini image leg
  (hybrid design; billing gate — never yet fired on this room).
- (ค) park the wardrobe; run the light-story pass (the standing queue) first.

Recommendation recorded at the gate: (ข)+(ค) — the last 10% of cloth realism is
image-space work by the pipeline's own design, and the Gemini leg has never once
been exercised on this room.

---

# Round 5b/5c addendum — the funded session (owner verdict "ก"), 2026-07-30

## Deliverable 1 — THE INSTRUMENT (built first, as ordered)

`clothcheck.py` (pure, 6 synthetic-mesh tests): adjacent-face normal-variance
profile — frac_over(60°), p95, mean, degenerate count. Wired into
`drape.bake_sheet(shred_guard=)` with three modes (off / "report" / enforce), a
3-rung stability ladder in `_emit_style_part` (solver quality 12→16, +frames,
bending ×1→×5) that uses the guard as pass/fail, and calibration tooling:
`--sim-garments`, `--shred-report`, `--shred-max=`. The instrument measured the
entire session below; it is permanent equipment (extendable to the bed stack).

## The measurements (all quick-rung, ZERO full-price renders spent)

Six mechanism hypotheses, each ~3 min, each measured by the instrument and/or
refuted by LOOK:

| # | hypothesis | result |
|---|---|---|
| 1 | finer torso blocker (nu 18) + collision_quality 6 | band 6.2–25.6%, torn piece visible |
| 2 | stability ladder (quality/frames/bend) | best piece 3.4%; 0_0 improved 12.7→8.5%; 0_1 unmoved |
| 3 | finer sim mesh (24×18) | facet-crumple softened; band unchanged |
| 4 | self-collision distance theory | REFUTED by reading the code (already 2 mm) |
| 5 | sleeves born outside the shell | LOOK-refuted: detached sticks; reverted |
| 6 | SMOOTH feedstock (carve/jitter off for sim) | band unchanged; 0_1 constant 27.2% |

The invariant: piece 0_1 sits at 27–34% under EVERY configuration — the
instability lives in something none of the six touched, most plausibly the
closed-tube topology + pinned-shoulder interaction itself (the bed has never
simmed a closed tube). Pieces at 3–5% exist in every run and their LOOK is the
best cloth this project has produced.

## State at close

`SIM_GARMENTS = False` (default build = g9 procedural read, verified); the whole
lane reproducible via flags; 2125 tests green pinning both states. The 2-full-
cycle budget was NOT spent — every hypothesis died at quick price.

## Next-decision options (for the gate)

- (ก2) HYBRID RAIL: ladder passes → simmed piece; ladder fails → analytic
  fallback (no piece ever ships shredded; rails mix best-of-both). One session.
- (ก3) OPEN-FORM feedstock: sim garments as open draped sheets over the hanger
  (the topology the solver has actually mastered here), not closed tubes.
- (ข) as before: g9 + material/light + Gemini leg.

---

# Round 5d — HYBRID RAIL shipped (owner: "(ก2) ก่อน"), 2026-07-30

The ladder's fail path now emits the piece's ANALYTIC TWIN (same salt, same
silhouette DNA, carve on) instead of raising — declared by styling in the same
cloth block (`analytic`), emitted loudly by `_emit_style_part`. Consequences,
both guaranteed by construction: no piece can ever ship shredded, and no build
can die for one unstable piece.

The multi-rung ladder is CUT to one recipe on the 5b/5c data (rungs 2-3 rescued
zero pieces while tripling worst-case time — the first hybrid build timed out on
exactly that). Quick builds attempt a playblast-grade sim (quality 8, short
settle); only the full recipe closes a gate (R5).

Full-fidelity g10 pair: 3 of 12 shirts sim-passed at the 6% line (2_0/3_1/8_1 —
the same stable DNAs every session run predicted), 9 analytic fallbacks, all
LOUD in the log. LOOK vs the reference: the rail is coherent for the first time
— solver drape on the passed pieces, carved folds on the twins, no wads, no
sticks, no tears. `SIM_GARMENTS=True` is the default; False reproduces g9
exactly. 2125 green pinning contract + fallback both ways.

Residuals (disclosed): analytic twins still read pressed-felt next to the
simmed piece (raising sim-share = the (ก3) open-form session); palette
monochrome + flat light remain the material/light lane.
