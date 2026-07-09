# F2 facing convention — VALIDATED (basis[0] is the SIDE, native yaw is already build_floor-correct)

**2026-07-09 · branch `tier1-self-doubt-suite` · geometric oracle + 4-method adversarial verification**

## Why this exists

Every prior F2 artifact carried the same load-bearing caveat: *F2 is WIRED but NOT
angle-validated.* `structured3d_adapter.py` emitted GT `rot` as **native yaw**
(`atan2(basis[0].y, basis[0].x)`), **asserted `forward = basis[0]`**, and warned that a
`~+90°` reconcile to `benchmark_reader`'s build_floor `front(rot)=(sin,−cos)` schema was
needed "before a real reader is scored, or F2 is corrupted." `rot_reconcile.py` then *proved*
`build_floor_rot = native+90` and shipped `convert_gt_doc` to apply it — but explicitly flagged
(lines 45–52) that whether **basis[0] actually is the object's semantic front** was *unproven,
"download-gated."*

This report **answers that deferred question with geometry, no render download** — and the
answer overturns the prior recommendation.

## Method

The oracle: for a **wall-backed, canonical-front** object (bed foot / sofa seat / tv screen /
cabinet doors / fridge door), the real front faces **into the room**, i.e. *away from the wall
it backs onto*. So the inward normal of its nearest wall is an independent estimate of its
front. Run over the **14-scene labelled slice** (real render-mask kinds + rot), restricted to
strong-front kinds with centroid ≤450 mm from a wall (**n = 73**). For each object, find which
cardinal offset of the emitted rot `R` (`R+{0,90,180,270}`) best aligns with the inward normal.
`R+270 ≡ (sin R, −cos R) ≡ build_floor front(R)`; `R+0 ≡ (cos R, sin R) ≡ native basis[0]`.

## Result — build_floor `(sin,−cos)` is the front; basis[0] is the side

| Offset of emitted rot | = which axis | into-room agreement |
|---|---|---|
| `R+270` = `(sin R,−cos R)` | build_floor front / basis[1] | **69/73 = 94.5%**, median error **0.0°** |
| `R+0` = `(cos R, sin R)` | native basis[0] | **0/73** |
| `R+90` / `R+180` | (LH flip / near-square) | 2 + 2 |

Per kind (offset R+0, emitted basis[0], vs inward normal): cabinet **46/46**, tv_panel
**13/13**, sofa, dresser, fridge — **97.3% SIDE** (perpendicular to the front), i.e. basis[0]
runs *parallel to the backing wall*.

### Adversarial verification — 4 independent methods, unanimous CONFIRM

A workflow ran four methods, each attacking the claim a different way:

1. **Room-polygon oracle** (annotation_3d floor loops, point-in-polygon, object→room-centroid):
   reproduces oracle A exactly (270 = 94.5%, median 0°); binary-sign use 95.9%. The naïve
   4-way centroid superficially sides with the *wrong* answer (57.5%) **only** because 30/31 of
   its 0/180 verdicts sit on basis[0]∥wall objects where a 0/180 front is geometrically
   impossible — a caught confound, not evidence.
2. **Raw-basis first-principles** (raw 3D basis in the native XY frame): **exact identities on
   117/117 objects** — `basis[0]_xy ⟂ (sin R,−cos R)` to **0.00°** (basis[0] can *never* be the
   front), and `(sin R,−cos R) = −basis[1]` for the 111 right-handed bases (`+basis[1]` for 6
   left-handed). basis[0] is the longer/width axis in 87%. Well-posed subset 59/61 = 96.7%.
3. **Oracle-B adjudication**: the open-space raycast oracle (which agreed only 53.7%) points
   *along the backing wall* in **51/51** disagreements — it measures room shape, never a
   coherent alternative front (0/51). B is discredited for this question, not the claim.
4. **Convention algebra + score_facing code trace**: `rot_bf = R` is a **general trig identity**
   (not just the four cardinals). `score_facing` compares rot *values* via `angle_diff`; a
   correct build_floor reader emits `R` → `angle_diff(R,R)=0` → **exact**. Applying the +90 to GT
   drives that same correct reader to `angle_diff=90` → **wrong** (0%).

## What this changes

**The emitted GT rot is already in build_floor convention. No conversion is needed. The prior
`forward=basis[0]` / `+90` / "will corrupt F2" narrative is itself the defect** — applying the
+90 rotates the declared front onto the side axis and *is* the F2 corruption.

Applied fixes (this commit):
- `structured3d_adapter.py` — `ROT_CONVENTION` + the FOOTGUN block + `_box_footprint_xy`
  docstring rewritten: emitted native yaw **==** build_floor front rot; basis[0] = side; do NOT
  apply +90. New regression `test_emitted_rot_is_native_yaw_not_plus90_...` fails if the +90 is
  ever reintroduced.
- `rot_reconcile.py` — **`convert_gt_doc` WITHDRAWN (raises)**; premise-refuted banner; `_prove`
  step 4 corrected to demonstrate the +90 *corrupts* (1.0 → 0.0), not fixes. The pure +90 algebra
  is retained as the conditional record (it computes build_floor rot *of basis[0]* = the side).
- `render_mask_labels.py` — the mirrored "reconcile before trusting F2" caveat corrected.
- `f2-rot-reconcile-2026-07-09.md` — resolution-update banner.

## Honest residuals (NOT closed)

- **~5% left-handed (det<0) tail** flips 180° (`front=+basis[1]`). It sits in
  **non-wall-backed / bed** objects — **0 in the scored wall-backed set** — so an empirical
  `det<0 → rot+180` flip gave **0 measured gain** and was **not** applied. The scored-set
  residual (4/73) is 2 near-square corner fridges (ambiguous axis) + ~2 noisy render-mask rot
  labels, not a systematic convention bug.
- **Beds** — a bed's `basis[0]`-yaw encodes its *length*, not a room-facing (wall-backed confirm
  only 4/8). Exclude beds from strong-front facing scoring; the S3D bed rot label is unreliable
  for facing.
- **Semantic front vs mirror-symmetric side** — wall geometry proves `(sin,−cos)` points *into
  the room*; it cannot rule out a further fixed 90° for a symbol whose front/side is
  visually symmetric. That last check stays render / 3D-FRONT gated.
- **No rot-emitting reader exists** — `svg_plan_reader` is facing-blind, so F2's angular buckets
  remain un-exercised end-to-end until an oriented-symbol reader emits rot. This validation makes
  the GT *trustworthy* for that day; it does not itself produce a cardinal_correct number against
  a real reader.

## Reproduce

The method is fully specified above; it runs off the local licensed slice
(`studio-datasets/structured3d/{gt-slice-labeled, bbox}`, not redistributable — S3D ToU). The
**durable** guard is in-repo: `test_structured3d_adapter.test_emitted_rot_is_native_yaw_not_plus90_
and_build_floor_front_is_perp_to_basis0` pins the convention (emitted rot == native yaw, and
build_floor `front(rot) ⟂ basis[0]`), and `rot_reconcile.test_convert_gt_doc_withdrawn_raises_by_
default` pins the withdrawal — either fails the moment the +90 is reintroduced. The one-off
oracle scripts ran in the session scratchpad; the 4-method adversarial workflow independently
re-derived every number.
