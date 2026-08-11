# DR — why a simulated coverlet corner ends its bake HELD OPEN

**Tier: REFERENCE.** A NotebookLM Deep Research answer: not domain truth, not
statute. Nothing here outranks `knowledge/codes-th/`, the client contract, or an
owner-signed decision. A value becomes live only when a named file consumes it.

| field | value |
|---|---|
| notebook | `ae3dd665-b540-47ed-b277-0b19f11e4d4c` "blender-cloth-corner-drape" |
| turn | 1 (conversation `919224b9-9566-401c-9384-2d952d0bc90e`) |
| fired | 2026-08-11, by the builder (DR-is-PULL law) |
| trigger | defect class on its THIRD judged round (มุมผ้ากางค้าง — C2/C3 at r5-class, r7, p3r1), past the 2nd-round trigger; vault sweep found no cloth-solver coverage |
| full answer | `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json` (same commit) |
| consumed by | `pipeline/scripts/drape.py` (`self_friction` param + collision block), `pipeline/scripts/build_room.py` (coverlet / duvet / bed-throw corner settle package, p3r2) |

## The diagnosis, in one paragraph

The splayed corner is a physical-numerical conflict in the mass-spring solver:
at a free corner the cloth must bend in TWO directions at once, and (1) the
default ANGULAR bending model resists that double curvature like a shell;
(2) premature self-collision repulsion inflates an air bubble between folds
that pushes them apart; (3) 55 frames is too short for the corner's kinetic
energy to dissipate, so the bake freezes it mid-splay; (4) low quality /
collision steps make the solver separate compressed corner folds with harsh
repulsion. Our bakes had all four: ANGULAR (default), default self-friction
5.0, frames 55, quality 8 / collision 4. The mitre cut and per-corner salt we
kept iterating were never the mechanism.

## Ranked fixes (exact properties; linen bedding values)

1. **`settings.bending_model = 'LINEAR'`** + bending 0.15-0.35 with mass
   ~0.12 — the biggest lever; failure mode: corner shard collapse if bending
   falls too low for the vertex mass. **NOT consumed yet** — it re-tunes the
   whole fold family mid-phase; recorded as the NEXT mechanism.
2. **Self-collision distance 1-3 mm + `self_friction` 5→~12-15** — we already
   had the distance (0.003); the friction half was never set. CONSUMED.
   Failure mode: tunnelling if distance shrinks further.
3. **Vertex-group positive-shrink "corner gather" map** — conflicts with our
   slack mechanism (one `vertex_group_shrink` slot already spent on negative
   shrink). Not consumable as-is.
4. **Sewing-spring corner darts** (`use_sewing_springs`, `sewing_force_max`
   10-25) — the literal "solver corner constraint" the gate named; needs dart
   cuts in `softgoods.flat_sheet`. Recorded NEXT mechanism beside (1).
   Failure mode: seam fails low / mesh explodes high.
5. Archviz tricks (simulate-and-lift, hooked empties, gravity over-ramp) —
   refused: authored guidance is a typed result (R9's family).
6. **Frames 55 → 120-150** (+ optional gravity ramp 0→1 over 40) — CONSUMED
   at 120, no ramp. Failure mode: stagnation if over-damped.
7. **`quality` 8→12-16, `collision_quality` 4→8-10** — CONSUMED at 12/8.
   Failure mode named by the DR: headless wall-time blowup — WATCHED at the
   R5 quick.

## Verification notes (the DR is not believed, it is tested)

- Property-name check against our own working code: the DR wrote
  `collision_settings.self_distance`; the real attribute (already in
  `drape.py`) is `self_distance_min`. One fabricated-name class caught —
  every other property named exists in `drape.py`'s API surface.
- The consumed package (2+6+7) is one A/B against p3r1's cloth: judged at the
  R5 quick by LOOK on the three corner sites, then by the p3r2 critics.
- `[n]` source markers in the raw answer are NotebookLM source indices; the
  notebook holds the resolved list (account cap note: prune this notebook
  after distillation).
