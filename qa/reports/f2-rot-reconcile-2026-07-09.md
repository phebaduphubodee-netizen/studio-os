# F2 rotation-convention reconciliation — native yaw ↔ build_floor

**2026-07-09 · branch `tier1-self-doubt-suite` · parallel session (track A, download-free slice)**

## Why this exists

`structured3d_adapter.py` and `render_mask_labels.py` both carry the **same** load-bearing
caveat on F2_facing, deferred to a future "reconcile before trusting the angular buckets":

> The adapter emits GT `rot` as **native yaw** (`atan2(basis[0].y, basis[0].x)`, CCW from
> world +X, forward = `basis[0]`). `benchmark_reader` scores `rot` in **build_floor**'s
> `F(rot) = (sin rot, −cos rot)` convention — *"a CONSTANT ~270° offset from native yaw …
> y-handedness UNVALIDATED … reconcile (offset AND y-handedness) against a real reader before
> trusting F2 angular buckets."* (`structured3d_adapter.py:137-149`)

Track A's real-label lane is owner-gated on a render-zip download (agent Bash has no network
egress). This is the **slice of the F2 lane that needs no download** and touches no file another
pane holds: it resolves the coordinate-convention half of the caveat outright, and names exactly
what genuinely remains gated.

## What is now proven (coordinate layer → SOLVED)

**`build_floor_rot = (native_yaw + 90) mod 360`** — a **pure rotation, not a mirror.**

Delivered as `pipeline/scripts/rot_reconcile.py` (+ `test_rot_reconcile.py`, 10 tests). Proven
three independent ways, all executable (`python rot_reconcile.py --prove`):

| # | Check | Result |
|---|---|---|
| 1 | Closed form `native+90` vs independent vector inverse `atan2(fx,−fy)`, every degree 0–359 | max diff **5.7e-14°** |
| 2 | Rotation vs reflection fit over the sweep | rotation residual **5.7e-14°** (fits); reflection `K−native` residual **180°** (**rejected**) |
| 3 | Four cardinals vs `facing_reader._FACING` (the repo's own convention: 0→S, 90→E, 180→N, 270→W) | exact |

Why "no mirror" is safe (the exact worry the adapter hedged on):
- **Algebra:** the relation is a *constant additive offset in native* (+90). A handedness flip
  would instead read `build = K − native` (a sign-flip on native) — check #2 decisively rejects it.
- **Data path:** nothing flips Y in the *scored* path. `synth_plan_2d` draws x/y/w/d at mm scale
  1.0 (its only `invert_yaxis()` is a cosmetic debug-plot label); `svg_plan_reader` is
  *"handedness-blind, so no flip is applied"* (`svg_plan_reader.py:45`) and emits mm footprints in
  the **same** world frame as GT — which is precisely why detection IoU-matches at all. GT and any
  future rot-emitting reader share one mm XY frame; the only difference is the +90 convention.

The convention `F(rot) = (sin rot, −cos rot)` is corroborated in **three** places
(`facing_reader.py:14`, `cross_signal.py:96`, `benchmark_reader._CARDINAL_ROT`), so the +90 is
checked against the repo's own facing code, not a re-transcription.

## The F2 consequence — reproduced, then fixed

Against the real scorer (`benchmark_reader.score_pair`), a facing element whose GT is native-yaw
and whose (correct) reader emits build_floor rot:

- **native GT vs build_floor reader → `cardinal_correct = 0.0`** (the read is physically perfect;
  the score is silently wrong — exactly the corruption the adapter warned would appear "the moment
  a real reader emitting build_floor rot is scored").
- **after `convert_gt_doc()` → `cardinal_correct = 1.0`.**

`rot_reconcile.convert_gt_doc(doc)` rewrites each element's `rot` native→build_floor (pure, stamps
`meta.rot_reconciled`, leaves rot-less elements untouched — honesty contract preserved), so a future
rot-emitting reader can be scored against reconciled GT correctly. CLI: `--convert-gt in out`.

## What still stays download-gated (the honest residual)

This proves an **angle-convention** offset. It does **not** prove Structured3D's `basis[0]` **is**
the object's semantic **front**. If S3D's local-x is (say) the object's right/back axis, every GT
facing is a further fixed offset from *true* facing, and no coordinate algebra recovers it — it
needs the render masks / 3D-FRONT layout (the same owner download). So after this module, F2 is
**data-limited on two remaining axes, both download-gated, neither a code bug:**

1. **`basis[0] == front` semantic check** — needs render / 3D-FRONT.
2. **A reader that actually emits `rot`** — `svg_plan_reader` emits **none** today (facing-blind),
   so F2 against it buckets every pair `unreported` regardless of convention; and a bare synth
   rectangle carries no facing cue for any reader to recover. F2's angular buckets stay
   un-exercisable end-to-end until oriented symbols **and** a rot-emitting reader both land.

**Net correction to the two docstrings' caveat:** the "~270°/handedness" worry is **resolved**
(pure +90, no mirror); the residual F2 caveat is the semantic front-axis + the missing rot-reader,
named precisely instead of the vague "reconcile before real reader." This narrows — not closes —
the F2 lane, and says so plainly.

## Adjacent finding (reproduced → **NOW FIXED** 2026-07-09, adapter/main session)

`placement_gate.footprint(x/y/w/d, rot)` **re-rotates** `x/y/w/d` by `rot` (it treats them as the
*un-rotated* placed rect — the benchmark generator's schema). But `structured3d_adapter` emits
`x/y/w/d` as the **already-rotated tight world AABB** plus a separate `rot`. So in the **kinded
lane** (labels supplied → `rot` emitted), any object at `rot ≠ 0/180` gets a **wrong scored
footprint**, silently degrading **detection IoU** against a true-AABB reader — and **invisible to
gt-vs-gt** (symmetric), exactly the drift the adapter docstring says its selftest cannot catch.

Reproduced on a 1000×400 box (adversarial verification **corrected the severity UP** — my first
pass wrongly called cardinals safe):

| rot | true AABB | scored (re-rotated) | IoU | effect |
|---|---|---|---|---|
| 0, 180 | 1000×400 | 1000×400 | **1.0** | safe |
| **90, 270** | 400×1000 | 1000×400 | **0.25** | **transposed → DETECTION MISS** |
| 45, 135 | 990×990 | 1400×1400 | 0.5 | inflated ~2× area |

**90°/270° are among the most common furniture facings** (a piece square-on to a side wall), so
this is **broad, not a rare diagonal tail**. Only 0°/180° survive untouched.

**Recommended fix (upstream, adapter owner):** when emitting `rot`, emit `x/y/w/d` as the object's
**local (un-yawed) `w×d`** so `footprint()` rebuilds the true oriented box — instead of the pre-baked
world AABB. Scope: kinded lane only, non-cardinal objects only.

**RESOLUTION (2026-07-09).** Fixed in two paired places so the scored footprint is correct AND stays
invariant through the rot conversion:
1. `structured3d_adapter.convert()` kinded branch now overrides `x/y/w/d` with the local un-yawed rect
   (`x=cx−coeffs[0]`, `y=cy−coeffs[1]`, `w=2·coeffs[0]`, `d=2·coeffs[1]`) alongside `rot=native yaw`.
   The blind lane still emits the 8-corner world AABB and is **byte-identical**.
2. `rot_reconcile.convert_gt_doc()` now **swaps `w↔d`** (centre held) when it adds +90, because that
   convention rotation transposes `footprint()`'s AABB — so a non-square box no longer detection-misses
   itself after reconcile.
3. `synth_plan_2d` (`_as_footprint`) bakes each element's `rot` into the drawn/grouped `footprint()` AABB,
   so a labelled corpus is not silently drawn un-rotated.

Verified: over **208 clean-yaw boxes** (0–360° × 4 aspect ratios) `footprint(kinded)` reproduces the
8-corner AABB to **0.0000 mm** and detection IoU vs a true-AABB reader is **1.0000**; the three failure
rows above are pinned as regression tests (`test_structured3d_adapter`, `test_rot_reconcile`,
`test_synth_plan_2d`); full suite **811 pass**.

## Deliverables

- `pipeline/scripts/rot_reconcile.py` — converter (`native_yaw_to_build_floor`,
  `build_floor_to_native_yaw`, `forward_to_build_floor_rot`, `convert_gt_doc`), executable proof
  (`--prove`), CLI `--convert-gt`.
- `pipeline/scripts/test_rot_reconcile.py` — 10 pinned unit tests (**all pass**).
- **No edits** to any file a parallel pane holds (`kind_priors.py` / `svg_plan_reader.py` /
  `derive_curve_priors.py` = track B; `synth_plan_2d.py` = track C). New files only; the two held
  files were **read-only**.

## Verdict

- **F2 coordinate-convention layer: SOLVED** (proven pure +90, no mirror; converter tested; the
  silent-corruption consequence reproduced and fixed).
- **F2 end-to-end trustworthiness: still NOT reached** — for two precisely-named, download-gated
  reasons (semantic front-axis; no rot-emitting reader), neither a code defect.
- **One adjacent adapter bug found + reproduced** (kinded-lane footprint double-rotation), scoped
  and handed off, not fixed here.

## Independent adversarial verification (6 agents, 0 errors)

- **3 blind replicators** (each forbidden to read `rot_reconcile.py`) independently derived the
  offset from the convention code alone. **All three: `offset = +90°`, `relation = rotation`,
  `agrees_with_plus90 = true`.** Each ran its own degree-by-degree sweep; `build − native` collapsed
  to the single value `{90.0}` while the reflection form `build + native` (or `K − native`) took
  180+ distinct values → mirror ruled out. One noted the honest scope limit verbatim: this
  reconciles the two *formulas*; whether S3D's physical y-axis matches build_floor's is the
  semantic question this report also flags as download-gated.
- **3 refuters** (try-to-break, high effort): **none refuted.**
  - *+90 holds every heading* — not refuted; independent brute force over 3.8M+ headings, worst
    circular error 5.7e-14°; wraparound + near-zero guards checked; **direction** `+90` (not −90/+270)
    confirmed against the four cardinals.
  - *no hidden mirror* — not refuted; confirmed the scored GT→SVG→reader path is an **identity map**
    (raw mm coords verbatim; the only `invert_yaxis` is a cosmetic overlay), and a reflection
    **reverses cyclic order** whereas this map preserves it, so a mirror cannot hide as a ±90 offset.
  - *footprint double-rotation* — not refuted; **reproduced and refined the severity upward**
    (90/270 transposed → IoU 0.25, not just diagonal inflation). That correction is folded into the
    finding above.

**Consensus: the coordinate reconciliation is confirmed by independent replication and survived
adversarial refutation; the one correction it produced (cardinal severity) is incorporated.**
