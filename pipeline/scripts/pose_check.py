"""pose_check.py — IS IT TURNED THE RIGHT WAY. PURE (no bpy, no PIL).

    python pipeline/scripts/pose_check.py --poses <poses.json> [--spec <spec.json>]

WHY THIS FILE EXISTS
--------------------
2026-08-29, TRN-003. The owner said the kitchen island looked laid the wrong way.
The builder checked, **confirmed its own model with a number** ("the axis measures
89.6 deg, it is the HEIGHT that is wrong"), and moved the island 1.65 m on an
asserted slab height. He had to say it a second time — *"คุณตาบอดจริง ๆ ด้วย ผมเห็นว่า
ไอแลนมันชี้ประมาณเข้าหากล้อง"* — before the island turned out to be **a full quarter
turn out**: measured 87.3 deg, i.e. parallel to the kitchen wall, where the build
had it perpendicular.

Every rung in this repo was green the whole time, and none of them was broken.
They were all asking a different question:

  - `coverage_check` asks PRESENCE. The island was present: named, built, in the
    manifest, non-degenerate. A 90-degree error is not a missing object.
  - `placement_check` asks FLOATING / OVERHANG / OFF-AXIS on world axes. A box
    that is square to the world is on-axis whichever of its two horizontal
    dimensions is the long one.
  - `pixel_check` asks about the features somebody CLAIMED. Nobody claims the
    orientation of a mass, because until this file there was no field to claim it in.
  - `carry_check` asks what holds a mass up. A rotated island rests on its own
    drums exactly as well as a correct one.

Turning an object a quarter turn changes NO extent, NO contact, NO inventory, and
NO justification. It is invisible to every instrument here by construction, which
is why it survived until a person looked at the picture twice.

THE MEASUREMENT THIS RUNG USES is standard and old: **angular distance**, the
smallest rotation carrying our axis onto the reference axis. It is the headline
metric of the 6DoF object-pose literature (alongside ADD/ADD-S for symmetric
objects), and it prints "90" for what happened here.

THE THREE WAYS A POSE ROW CAN LIE, all three paid for on 2026-08-29
-------------------------------------------------------------------
1. **A DIRECTION READ OFF A CURVED EDGE IS NOT A DIRECTION.** The wrong axis came
   from fitting a straight line to the slab's front edge — which is an OVAL. A
   straight fit across a curve returns a CHORD, and a chord's slope depends on
   which span you fit. Two spans gave -0.031 and -0.049; both numbers were in
   front of the builder and it walked past them. So `line_fit` is accepted ONLY
   with two independent spans recorded, and it is REFUSED when they disagree —
   refused, never averaged. Averaging two chords of an oval yields a third chord.
2. **A VANISHING POINT FAR OFF-FRAME CANNOT SORT LINES INTO FAMILIES.** The chord
   was assigned to an axis family by PROXIMITY of vanishing points: 7711 against
   the transom's 7917, both thousands of pixels outside a 1440-wide image, where
   a 0.02 slope error moves the VP by kilometres. The true answer was -1546.
   fSpy's own documentation says it in one line: *"when the line segments used to
   define a vanishing point are near-parallel, the vanishing point position
   cannot be computed accurately; a larger angle between the lines yields better
   results."* So `vp_intersection` must carry the ANGLE BETWEEN ITS SUPPORTING
   SEGMENTS, and is refused below a threshold. Note what is NOT the gate: how far
   off-frame the VP lands. A VP at infinity is the correct answer for lines truly
   parallel to the image plane, and the pose literature is explicit that a large
   covariance there does not mean a bad estimate. The angle is the gate.
3. **DECLARING SYMMETRY IS THE CHEAPEST WAY TO MAKE AN ERROR VANISH.** Fold n
   means the object maps onto itself every 360/n degrees, so a fold-4 declaration
   erases exactly the 90-degree error this file exists to catch. Therefore: fold
   defaults to 1 (nothing is assumed symmetric), a fold above 2 must carry
   `fold_reason`, and **fold 0 — full rotational symmetry — is REFUSED rather
   than passed**, because a drum has no orientation to check and a row claiming
   to have checked one is a row reporting a measurement it did not make.

WHAT SETTLED IT IN THE END, and it is the estimator this repo had never used:
**two identical objects at two depths.** The island's two bronze drums are the
same cylinder; each one's base height gives its depth and its silhouette width
confirms that depth, so the line through their centres is a scene direction with
no curve to fit and no family to guess. That is `recurrence` below, and it is the
best-conditioned method in the list — five minutes against an hour of edge fitting
that came out backwards.

EXIT CODES ARE A CONTRACT (same as pixel_check)
    0 = every claimed pose is within tolerance
    1 = a pose is out of tolerance, or a row is malformed
    2 = COULD NOT RUN — no rows, or a row whose reference was never measured.
        "Could not look" must never print like "looked and it was fine".

WHAT IT DOES NOT DO, said plainly so nobody reads it as compliance: it checks the
masses somebody wrote a row for. `--spec` prints how many masses carry no pose
row at all, and that number is the remaining work, not a score.
"""
import argparse
import json
import math
import os
import sys


# A tolerance is a measurement's noise floor, not a licence. The camera solve that
# produced these axes reproduces its own orthogonality to 0.02 deg and lands 2.7 deg
# off parallel on a hand-picked drum pair; anything past 15 deg is no longer
# absorbing measurement error, it is absorbing a different orientation.
TOL_CAP_DEG = 15.0

# ONE PLACE FOR THE TWO ANGLES, and it is not this file. `edge_direction` refuses a
# bad direction AT THE MEASUREMENT; this file refuses it AT THE GATE. Two copies of
# a threshold is two thresholds the moment one of them is tuned, and this repo has
# already shipped a constant copied into a build (a comment saying one thing while
# the code did another for a month).
from edge_direction import (MIN_FAMILY_ANGLE_DEG as MIN_SEGMENT_ANGLE_DEG,
                            MAX_SPAN_DISAGREE_DEG)

METHODS = {
    # method            needs
    "recurrence":       (),                      # two instances of one component
    "datum_pair":       (),                      # two named points on the object
    "sheet":            (),                      # read off the drawing of record (R12)
    "owner":            (),                      # he said so; outranks everything
    "line_fit":         ("spans",),
    "vp_intersection":  ("segment_angle_deg",),
}


def _as_angle_deg(v, field):
    """A plan heading in degrees, or a direction vector, -> degrees in [0, 360).

    Accepts a scalar (already a heading) or a 2-/3-vector. A 3-vector is projected
    to the plan: this rung answers "which way is it laid", which is a question about
    the floor. A mass tipped in Z is a different defect with a different instrument
    (placement_check's OFF-AXIS), and one row must never carry two questions.
    """
    if isinstance(v, (int, float)):
        return float(v) % 360.0
    if isinstance(v, (list, tuple)) and len(v) in (2, 3):
        x, y = float(v[0]), float(v[1])
        if math.hypot(x, y) < 1e-9:
            raise ValueError(f"{field} is a vector with no length in plan {v!r} — "
                             f"a vertical axis has no heading to compare")
        return math.degrees(math.atan2(y, x)) % 360.0
    raise ValueError(f"{field} must be a heading in degrees or a 2-/3-vector, got {v!r}")


def angular_distance(a_deg, b_deg, fold=1):
    """Smallest rotation taking heading a onto heading b, given n-fold symmetry.

    fold n -> the object is unchanged by a rotation of 360/n, so the error is
    measured modulo that period. fold 1 is the strict case and the default.
    fold 2 (a rectangle, a bed, a racetrack island) folds 180 and NOT 90 — which
    is exactly why the TRN-003 island still prints 90 under its honest fold.
    """
    p = 360.0 / float(fold)
    d = (float(a_deg) - float(b_deg)) % p
    return min(d, p - d)


def _row_error(row):
    """(error_deg, note) or raise ValueError with the reason the row cannot be read."""
    if "ours" not in row:
        raise ValueError("no `ours` — nothing measured in our scene")
    # A REFERENCE HEADING THAT CAN BE DERIVED MUST NOT BE TYPED — R9's law, which
    # this repo wrote about POSITIONS, applied to orientation. When the row carries
    # the pixel readings of two identical objects, the checker computes the heading
    # itself with `recurrence.solve`, so the number in the gate and the number in
    # the measurement cannot drift apart, and recurrence's own self-check (base-row
    # depth vs silhouette-width depth) has to pass before the pose row can.
    if "ref_recurrence" in row and "ref" not in row:
        import recurrence as RC
        rr = row["ref_recurrence"]
        c = rr["camera"]
        cam = RC.Camera(c["f_px"], c["ppx"], c["ppy"], c["height_mm"], c["yaw_deg"],
                        c.get("origin", (0.0, 0.0)))
        try:
            row = dict(row, ref=RC.solve(cam, rr["instances"], rr.get("size_mm"),
                                         row.get("id", "ref_recurrence"))["heading_deg"])
        except RC.Unsupported as exc:
            raise ValueError(f"the reference heading could not be derived: {exc}")
    if "ref" not in row:
        raise ValueError("no `ref` — the reference axis was never measured. That is "
                         "COULD NOT RUN, not a pass")
    ours = _as_angle_deg(row["ours"], "ours")
    ref = _as_angle_deg(row["ref"], "ref")

    fold = row.get("fold", 1)
    if not isinstance(fold, int) or fold < 0:
        raise ValueError(f"`fold` must be a non-negative integer, got {fold!r}")
    if fold == 0:
        raise ValueError(
            "`fold: 0` declares full rotational symmetry — a drum, a round table, a "
            "column. Such an object HAS no orientation, so this row reports a "
            "measurement it did not make. Delete the row; do not pass it")
    if fold > 2 and not str(row.get("fold_reason", "")).strip():
        raise ValueError(
            f"`fold: {fold}` folds a {360.0 / fold:.0f} deg error to zero and needs "
            f"`fold_reason` naming the symmetry (a square footprint, a 4-way base). "
            f"Declaring symmetry is the cheapest way to make a real error vanish")

    method = row.get("method")
    if method not in METHODS:
        raise ValueError(
            f"`method` {method!r} is not one of {sorted(METHODS)} — a reference angle "
            f"with no recorded method cannot be audited, and every way this "
            f"measurement has lied so far was a property of the method")
    for need in METHODS[method]:
        if need not in row:
            raise ValueError(f"method `{method}` requires `{need}`")

    note = ""
    if method == "line_fit":
        spans = row["spans"]
        if not isinstance(spans, (list, tuple)) or len(spans) < 2:
            raise ValueError(
                "`line_fit` needs at least TWO independent spans of the same edge. "
                "One span cannot tell a straight edge from a chord of a curve")
        angs = [_as_angle_deg(s, "spans[]") for s in spans]
        worst = max(angular_distance(a, b, fold=2) for a in angs for b in angs)
        if worst > MAX_SPAN_DISAGREE_DEG:
            raise ValueError(
                f"the spans of this edge disagree by {worst:.2f} deg (limit "
                f"{MAX_SPAN_DISAGREE_DEG}) — the edge is CURVED and each fit returns a "
                f"chord, not a direction. REFUSE; do not average, because the mean of "
                f"two chords is a third chord. Measure it by `recurrence` instead")
        note = f"spans agree to {worst:.2f} deg"
    elif method == "vp_intersection":
        ang = float(row["segment_angle_deg"])
        if ang < MIN_SEGMENT_ANGLE_DEG:
            raise ValueError(
                f"the segments supporting this vanishing point are {ang:.1f} deg apart "
                f"(need >= {MIN_SEGMENT_ANGLE_DEG}) — near-parallel segments put the VP "
                f"where fit noise moves it by kilometres (fSpy, Basics). Note the gate "
                f"is the ANGLE, not how far off-frame the VP lands: a VP at infinity is "
                f"the correct answer for lines parallel to the image plane")
        note = f"supporting segments {ang:.1f} deg apart"

    tol = float(row.get("tol_deg", 5.0))
    if tol > TOL_CAP_DEG:
        raise ValueError(
            f"`tol_deg` {tol} is above the cap {TOL_CAP_DEG} — past that a tolerance "
            f"stops absorbing measurement noise and starts absorbing a different "
            f"orientation")
    if tol < 0:
        raise ValueError(f"`tol_deg` {tol} is negative")

    return angular_distance(ours, ref, fold), tol, method, fold, note


def audit(poses):
    """Return (rows, violations, could_not_run). Pure; no I/O, no exit."""
    rows, violations, cnr = [], [], []
    entries = poses.get("poses") or []
    seen = set()
    for e in entries:
        pid = e.get("id", "")
        if not pid:
            violations.append("pose entry with no `id`")
            continue
        if pid in seen:
            violations.append(f"poses lists `{pid}` twice")
        seen.add(pid)
        try:
            err, tol, method, fold, note = _row_error(e)
        except ValueError as exc:
            msg = f"`{pid}`: {exc}"
            # A row that names no reference is a rung that could not run. A row that
            # is malformed is a rung that was written wrong. Only the first may leave
            # the gate uninformed; the second is the builder's own defect.
            (cnr if "COULD NOT RUN" in str(exc) else violations).append(msg)
            rows.append({"id": pid, "state": "COULD NOT RUN" if "COULD NOT RUN" in str(exc)
                         else "MALFORMED", "detail": str(exc)})
            continue
        ok = err <= tol
        rows.append({"id": pid, "state": "PASS" if ok else "FAIL", "error_deg": err,
                     "tol_deg": tol, "method": method, "fold": fold, "detail": note})
        if not ok:
            violations.append(
                f"POSE `{pid}` is {err:.1f} deg from the reference (tolerance "
                f"{tol:.1f}, method {method}, fold {fold}){' — ' + note if note else ''}")
    return rows, violations, cnr


def unclaimed(spec, poses):
    """Masses in the spec that no pose row mentions. Printed, never a pass/fail.

    Same honesty as pixel_check's "78 of 79 masses carried no claim": a rung that
    checks what somebody claimed must say out loud how much was never claimed,
    or its silence reads as coverage.
    """
    claimed = set()
    for e in poses.get("poses") or []:
        if e.get("id"):
            claimed.add(e["id"])
        for m in e.get("built_as") or []:
            claimed.add(m)
    names = [m.get("name") for m in spec.get("masses", []) if m.get("name")]
    return [n for n in names if n not in claimed], len(names)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poses", required=True)
    ap.add_argument("--spec", default="", help="print how many masses carry no pose row")
    ap.add_argument("--soft", action="store_true", help="report, exit 0")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        poses = json.loads(open(a.poses, encoding="utf-8").read())
    except FileNotFoundError:
        print(f"POSE: no pose file at {a.poses} — nothing claims an orientation")
        return 0 if a.soft else 2

    rows, violations, cnr = audit(poses)
    if not rows:
        print("POSE: the pose file carries no rows — a pose claim with no entries is "
              "the mute that this check exists to prevent")
        return 0 if a.soft else 2

    print(f"POSE: {len(rows)} claimed orientations")
    for r in rows:
        if "error_deg" in r:
            print(f"  [{r['state']:4s}] {r['id']}: {r['error_deg']:6.1f} deg off "
                  f"(tol {r['tol_deg']:.1f}, {r['method']}, fold {r['fold']})"
                  + (f" — {r['detail']}" if r["detail"] else ""))
        else:
            print(f"  [{r['state']}] {r['id']}: {r['detail']}")

    if a.spec and os.path.exists(a.spec):
        spec = json.loads(open(a.spec, encoding="utf-8").read())
        miss, total = unclaimed(spec, poses)
        print(f"POSE COVERAGE: {len(miss)} of {total} masses carry no pose row"
              + (f" — {', '.join(miss[:8])}{' …' if len(miss) > 8 else ''}" if miss else ""))

    if cnr:
        print(f"POSE COULD NOT RUN ({len(cnr)}):")
        for c in cnr:
            print("  - " + c)
    if violations:
        print(f"POSE VIOLATIONS ({len(violations)}):")
        for v in violations:
            print("  - " + v)
    if a.soft:
        return 0
    if violations:
        return 1
    if cnr:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
