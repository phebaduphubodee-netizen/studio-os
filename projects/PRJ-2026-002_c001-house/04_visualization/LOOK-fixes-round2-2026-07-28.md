# LOOK round-2 fixes — 2026-07-28

Owner order: fix the round-2 verdict's confirmed defects in rank order 1→5
(`LOOK-verdict-round2-2026-07-28.md`). Standing law applied: LOOK-and-judge ran
IN the loop — every fix was rendered and judged in pixels before the next began,
and two of the five needed a second cut that only the render could have asked for.

Final frames: `pipeline/output/room_bedroom_suite_eye_g6.png` (hero 3/4) and
`room_bedroom_suite_eye_g6_bedhero.png` (frontal) — the round-3 baseline pair.
Full pipeline suite green: 2090 passed.

## 1. `_rbox` terracing — FIXED (one line, whole fleet)

`build_room._rbox` now sets `use_smooth` like every other curved path (curtains
:1279, sheers :1330, `_smooth_mesh_obj`, drape). LOOK fx1 vs g5: the bench seat's
stair-step bands (142→84 in ~18 px plateaus) are gone — luma profile down the
bench face is now monotonic; mattress rolls and bed base smooth in both frames.
Nightstands/sofa inherit the fix (same primitive).

## 2. Throw's fold-less drop face — FIXED (fall weight 0.30)

Mechanism confirmed: the fall carried shrink weight 0 (dead taut) — the
containment fix had rebuilt the painted-slab class. `drape.bake_sheet` now takes
weighted slack groups; the fall gets 0.30.
- First cut at 0.45 FAILED the bake ladder: the coverlet's foot skirt already
  spends the 90 mm inset, so the stack sat 10 mm proud of the plan line at every
  slack — there is no room outboard for deep folds on this bed. 0.30 makes the
  fall CONFORM into the coverlet's troughs instead of bridging their crests.
- Solved in 1 bake at full 10% slack. LOOK g6_bedhero: hem undulates, the
  fold-over rolls, the face carries soft draped relief; corner falls curve.

## 3. Skirt corner 90° Z-step — FIXED (tangent mitre curve, dip 0.45)

The constant-radius corner cut ended the corner cloth at 0.6×overhang against
strips at 1.0 — the as-draped hem stepped drop→shelf→drop, squared, at face-drop
staircase precision. `softgoods._mitre_radius` replaces it: full radius at both
strip junctions, dipping between, cos⁶(2θ) so the free hem leaves each strip
tangent; kept verts past the curve are arc-snapped onto it.
- cos² with dip 0.6 FAILED: it nearly doubled corner cloth, the cowl bulged past
  the plan line, and the search ladder paid by ironing the whole coverlet
  (slack 2.5%→0.62%, hem 62 mm short) and starving the throw. The deeper dip
  (0.45) buys the tangent rise back — total corner cloth lands under the old
  mitre's and the ladder solves like before (3 bakes, slack 1.25%).
- LOOK g6_bedhero: left corner now hangs as a draped cowl with real creases;
  right corner's stiff flap is a soft rolled fall. No step on either side.

## 4. Sheer sawtooth hem — FIXED (hanging lattice, two-scale wander)

`curtains.ribbon_mesh` replaces the 2-ring prism: the top ring is the
owner-signed track wave byte-for-byte; downward the primary decays (modulated
per station), an incommensurate secondary crease grows in, everything clamps to
the layer's ±amp pocket envelope, and all law terms taper to zero at the run
ends so the L-corner mitres still meet. Consumed by `_add_curtains` for all six
ribbons (opaque + sheer, three legs).
- First cut FAILED the LOOK: hem wander carried only slow waves, so adjacent
  pleats still ended at matched heights — a slowly-breathing spike row. A third
  wander wave at ~0.47×n_folds (incommensurate with the pleat pitch) plus a
  32 mm ceiling de-synchronised neighbouring tips.
- LOOK final g6_bedhero: the detached-triangle row is gone; pleat tips end at
  scattered heights with softened, merging terminations, and the pitch no longer
  reads metronomic. (Casement sheers keep their own micro-wave path — not
  flagged by the verdict, not touched.)

## 5. Garment-rack clones — FIXED (pose DNA per piece)

`softgoods.garment` now derives a POSE from its salt, inside the published
bounds: knee height (bend opens 0.28–0.42 of drop), below-waist flare ≤0.06
(GARMENT_FLARE stays the true span bound), shoulder-tip slope (hanger arms angle
down from the hook — a level top ring is a coat on a shelf), a C-or-S lateral
bow spent out of the sway budget and zero at the hook, and per-piece crease
amplitude. Signature unchanged; styling's containment math untouched.
LOOK fx5 vs g5, both rails: knees at different heights, bows in both directions,
sloped shoulders, hems kicking at varied heights — the rack reads as clothes.

## Pre-commit review round (6-agent adversarial) — two majors, both fixed

1. **The first slope cut hung cloth below its own hanger.** Slope ran to 53 mm
   while the recorded cover budget (SHOULDER_DROP 0.020 above a straight bar at
   0.030) is 10 mm — probed 40/40 salts, cloth 13–43 mm below the rigid wire
   that suspends it, invisible to every per-module test because the two meshes
   only compose in `garments_on_rail`. Fix: `softgoods.garment_slope` is now ONE
   published stream — clamped to [0.017, 0.038], the band the ^1.6 cloth profile
   provably covers — and `hanger` grew angled ARMS (sheared boxes) that wear the
   same slope the caller's garment does. New composition test in test_styling.py
   asserts cloth covers the arm at every top-ring station across salts.
2. **Fix 3 had zero armour** — revertible with all tests green, the standing
   revert-by-omission class. The dip constant moved into softgoods
   (`COVERLET_MITRE_KEEP`) where pure tests reach it; new tests pin the tangent
   curve's shape (full at strips, `keep` on the diagonal), the arc-snap (no kept
   vert beyond the curve — red on revert), and the deep-dip value with its why.

## Residuals (disclosed, not in the 1→5 order)

- Charcoal garments still render very dark in the bay's shadow (verdict noted
  "detail-free black cores"). The silhouettes now vary so they read as garments,
  but the value floor is a MATERIAL question (backer ply albedo under the 30
  floor in shadow) — amplitude-bisect class, owner's lane, same family as the
  BF09-3 towerback texture gain (verdict #10) and the lamp-shade emission (#11).
- Verdict #6–#9 (pillow contact compression, dead-black holes, folded-stack
  edges, soffit ripple) were not ordered and are untouched.
- Throw hem rides ~100 mm higher than the taut version at the flanks (slack
  spends length); reveal law held by the bake guards (hem 0.409 > reveal line).

## Test/armour deltas

- `test_curtains.py`: +6 tests pinning the lattice law (top ring identity,
  envelope containment, hem never level/never low, ends fixed for mitres,
  metronome broken, determinism).
- `test_softgoods.py`: +3 tests pinning pose DNA (shoulder slopes, poses differ
  by salt, pose stays inside published span/drop bounds).
- `test_drape_feedstock.py`: +3 tests pinning the tangent mitre (curve shape,
  arc-snap boundary law, the deep-dip constant).
- `test_styling.py`: +2 composition tests (cloth covers the hanger arm at every
  salt; hanger arms wear the garment's own slope stream).
- Full `pipeline/scripts` suite green (re-run after the review fixes: 2095).
