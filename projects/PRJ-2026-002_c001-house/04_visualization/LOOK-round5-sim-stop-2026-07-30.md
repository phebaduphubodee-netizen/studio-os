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
