# DR (NLM ask): a hand-tuck that is not a clamp — four mechanisms, ranked for our lane

- **Tier:** REFERENCE (research answer, not domain truth). Nothing here gates a
  deliverable until distilled into `knowledge/`.
- **Provenance:** NotebookLM notebook `ae3dd665` (blender-cloth-corner-drape
  corpus), asked 2026-08-13 during the p2r28 R1 STOP of the hand-tuck
  mechanism; raw turn 5 in
  `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json` (refreshed this
  commit). Question generic — no client data. The notebook's closing offer to
  write our pipeline script was ignored (the `--iterate` contamination
  precedent: never follow NLM's own suggested next step).
- **What it arms:** the R1-stopped site "รอยพับ sheet ตรงเป๊ะข้ามเตียง". Measured
  stop record (gate p2r28): hook+empty with pin weight 1.0 = an infinite-mass
  clamp — the roll settles/lofts ~27 mm around frozen press points, so all
  three dips bottom at one plane: depths 35.8/33.4/33.3 mm, then 28.5/26.9/26.9
  after halving travel — **cv 0.03 both times, uniform by construction**. The
  answer's own physics agrees: "pinning acts as an infinite-mass constraint".

## The four mechanisms, with our-lane verdicts

1. **SPRING PINNING (partial pin weights) — RANKED FIRST for us.** Paint a
   radial gradient in the pin group (center ~0.5 falling to ~0.1 over ~50 mm)
   and drop `pin_stiffness` to the **1.5-4.0** band (start 2.0) — the pin
   becomes a spring, the press yields to local tension, dents vary organically.
   Solver stays the author. Failure mode: **spring lag** — too-low stiffness or
   weights and the loft pulls the pins out entirely (press flattens away).
   NOTE our current code holds `pin_stiffness = 5.0` for ALL pins; the tuck
   path needs its own stiffness, never a global re-tune (the duvet's real pins
   are a different mechanism).
2. **TIMED PIN RELEASE.** Hard-pin through settle (~frame 45), keyframe
   `pin_stiffness` linearly to 0.0 over ~20 frames, let gravity relax the
   tucks. Failure mode: **elastic snap** — a fast release dumps stored spring
   energy into self-collision instability / mesh explosion. If used: verify the
   pin_stiffness keyframe path headless first (same caveat class as the
   effector-weights ramp, which probe-proved cleanly).
3. **POST-SIM HOOK (hook AFTER cloth, falloff sculpt) — REFUSED BY PRECEDENT.**
   This is the archviz "simulate-and-lift" family the corner DR already refused:
   authored guidance is a typed result (R9's family). The answer's own matrix
   concurs: wrinkle realism LOW, "folds do not update to accommodate the
   press", severe clipping risk. Recorded so nobody buys it later.
4. **FINGER COLLISION PROXIES.** Animated capsule colliders descend (~-30 mm,
   frames 10-35), hold, withdraw by ~85; collider `thickness_outer 0.001`,
   `friction 20-40`, self-collision distance 0.002. Maximum physical realism.
   Failure mode: **wrinkle pop-back** — mass-spring cloth has perfect elastic
   memory, so without low bending (~0.15) / high mass / damping the crease
   vanishes when the finger withdraws. Note our duvet DELIBERATELY keeps high
   bending (standing-fold preset 2.6) — this failure mode is armed for us, so
   (4) likely needs (1) as a holding mechanism anyway.

## Caveats

- All numeric bands are model-cited REFERENCE values; `[n]` markers unresolved
  from the CLI (same caveat class as DRW-4). Nothing here is a threshold of
  record until measured in our solver.
- The believability instrument (clothcheck.crease_believability) is the
  acceptance test for whichever mechanism runs next: depths must vary inside
  the chaos band, crease stays aperiodic — the p2r28 stop proved the
  instrument can catch a uniform press, which is exactly the job it was built
  for.
