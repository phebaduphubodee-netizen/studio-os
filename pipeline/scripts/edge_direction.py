"""edge_direction.py — REFUSE A DIRECTION THE PICTURE CANNOT SUPPORT. PURE.

    python pipeline/scripts/edge_direction.py --lines lines.json

WHY THIS FILE EXISTS
--------------------
`pose_check.py` refuses a bad pose row at the GATE. This module refuses it at the
MEASUREMENT, which is where it was made. Both are needed and they are not the same
rung: a gate can only reject a number somebody already wrote down, and the number
that started this was written down with complete confidence.

2026-08-29, TRN-003, in the order the mistakes actually happened:

  1. A straight line was fitted to the island slab's front edge and its slope was
     called a direction. **The slab is an oval.** A straight fit across a curve
     returns a CHORD, and a chord's slope depends on which span you fit — two spans
     gave -0.031 and -0.049. Both numbers were on screen. Nothing refused.
  2. That chord was then assigned to an axis family by the PROXIMITY of vanishing
     points: 7711 against the transom's 7917, on a 1440-wide image.
  3. And the family it was assigned to was itself built from two lines only
     **4.24 degrees apart** — the window transom at +2.46 deg and the island edge at
     -1.78 deg. fSpy's own manual says what that produces: *"when the line segments
     used to define a vanishing point are near-parallel, the vanishing point position
     cannot be computed accurately; a larger angle between the lines yields better
     results."*

THE PART THAT MATTERS MOST, because it was not the obvious one. An angular
family test does NOT catch step 2: run it on the real numbers and the island chord
sits 0.03 deg off family B's vanishing ray and 6.4 deg off family A's, so it lands
in B cleanly by any test you like. **The chord was a perfectly good member of a
family whose vanishing point was garbage.** So the load-bearing check here is not
the assignment at all — it is CONDITIONING, computed before any assignment is
allowed to mean anything, and on this frame it refuses family B (4.24 deg) and
passes family A (25.97 deg, from A7 at -16.00 and A3 at +9.97). Family B is the one
that was wrong.

AND THE CORRECTION TO THE OBVIOUS FIX. The instinct is to distrust a vanishing
point that lands far off-frame. That is the wrong measure, and the pose literature
says so directly: the covariance of a VP in image space is distorted by projection,
and *"a large covariance of a VP at infinity or very far away does not necessarily
mean an inaccurate estimation"* — a VP at infinity is the CORRECT answer for lines
truly parallel to the image plane. Gate on the angle between the supporting
segments. Never on where the answer lands.

WHAT IT REFUSES, in one list
    * a direction read from spans of one edge that disagree  -> the edge is curved
    * a vanishing point whose supporting lines are near-parallel
    * a family assignment that two families fit about equally well
    * a family assignment made against an ill-conditioned family at all

Every refusal raises `Unsupported` with the reason and the number. It never returns
a degraded answer, because a degraded answer here is indistinguishable from a good
one four steps downstream — which is exactly how a quarter-turn error reached a
render, a spec, and two days of work.
"""
import argparse
import json
import math
import sys


# fSpy's guidance as a number: two segments 10 deg apart put the VP where a quarter
# degree of fit noise moves it by a kilometre.
MIN_FAMILY_ANGLE_DEG = 10.0
# Two spans of ONE straight edge must agree. The oval that caused this gave 1.03 deg.
MAX_SPAN_DISAGREE_DEG = 1.0
# A line must sit this close to a family's vanishing ray to belong to it...
MAX_FAMILY_RESIDUAL_DEG = 2.0
# ...and the runner-up must be this much worse, or the assignment is ambiguous.
MIN_FAMILY_MARGIN_DEG = 2.0


class Unsupported(Exception):
    """The picture does not support the direction that was asked for."""


def slope_deg(m):
    return math.degrees(math.atan(float(m)))


def pair_angle_deg(m1, m2):
    """Angle between two image lines given as slopes, in [0, 90]."""
    a = abs(slope_deg(m1) - slope_deg(m2)) % 180.0
    return min(a, 180.0 - a)


def straight_direction(spans, name="edge"):
    """One heading from >= 2 independent spans of the SAME edge, or refuse.

    `spans` are slopes (dv/du). REFUSES on disagreement rather than averaging: the
    mean of two chords of an oval is a third chord, which is a number with no
    referent at all. The correct response to a curved edge is a different
    instrument (recurrence.py), never a better average.
    """
    ms = [float(m) for m in spans]
    if len(ms) < 2:
        raise Unsupported(
            f"{name}: one span cannot tell a straight edge from a chord of a curve. "
            f"Fit at least two independent spans")
    worst = max(pair_angle_deg(a, b) for a in ms for b in ms)
    if worst > MAX_SPAN_DISAGREE_DEG:
        raise Unsupported(
            f"{name}: spans disagree by {worst:.2f} deg (limit {MAX_SPAN_DISAGREE_DEG}) "
            f"— this edge is CURVED and every fit across it returns a chord, not a "
            f"direction. Do not average; measure it another way")
    return sum(slope_deg(m) for m in ms) / len(ms), worst


def family_conditioning(lines, name="family"):
    """Widest angle between any two supporting lines of one vanishing point.

    THIS IS THE GATE. Not the VP's distance off-frame — a VP at infinity is the
    right answer for lines parallel to the image plane.
    """
    ms = [float(l["m"]) for l in lines]
    if len(ms) < 2:
        raise Unsupported(f"{name}: a vanishing point needs at least two lines")
    widest = max(pair_angle_deg(a, b) for a in ms for b in ms)
    return widest


def require_conditioning(lines, name="family"):
    w = family_conditioning(lines, name)
    if w < MIN_FAMILY_ANGLE_DEG:
        raise Unsupported(
            f"{name}: its widest supporting pair is {w:.2f} deg apart (need "
            f"{MIN_FAMILY_ANGLE_DEG}). Near-parallel segments put the vanishing point "
            f"where fit noise moves it by kilometres (fSpy, Basics). Nothing derived "
            f"from this family may be trusted, including which lines belong to it")
    return w


def vanishing_point(lines, name="family"):
    """Least-squares VP of >= 2 lines v = m u + b, after the conditioning gate.

    Each line contributes  m*u - v + b = 0 ; solve the 2x2 normal equations.
    """
    w = require_conditioning(lines, name)
    saa = sab = sbb = sa = sb = n = 0.0
    for l in lines:
        m, b = float(l["m"]), float(l["b"])
        # residual (m*u - v + b) with unit-ish weighting
        saa += m * m
        sab += -m
        sbb += 1.0
        sa += -m * b
        sb += b
        n += 1
    det = saa * sbb - sab * sab
    if abs(det) < 1e-12:
        raise Unsupported(f"{name}: the normal equations are singular")
    u = (sa * sbb - sab * sb) / det
    v = (saa * sb - sab * sa) / det
    return (u, v), w


def assign_family(line, families, name="line"):
    """Which axis family this line belongs to, by ANGLE at the line, or refuse.

    `line` = {m, b, u} where u is a point ON the line (its midpoint column).
    `families` = {label: {"vp": (u, v), "lines": [...]}}.

    NEVER by proximity of vanishing points. The residual is the angle between the
    line and the ray from its own midpoint to the candidate vanishing point, which
    is a quantity the image can actually support. Refuses when two families fit
    about equally, and refuses outright against a family that failed conditioning —
    membership in an unreliable family is an unreliable fact.
    """
    m, b, u = float(line["m"]), float(line["b"]), float(line["u"])
    v = m * u + b
    scored = []
    for label, fam in families.items():
        require_conditioning(fam["lines"], f"family {label}")
        fu, fv = fam["vp"]
        du, dv = fu - u, fv - v
        if abs(du) < 1e-9:
            ray = 90.0
        else:
            ray = slope_deg(dv / du)
        scored.append((abs(((slope_deg(m) - ray + 90.0) % 180.0) - 90.0), label))
    scored.sort()
    best, runner = scored[0], (scored[1] if len(scored) > 1 else (1e9, None))
    if best[0] > MAX_FAMILY_RESIDUAL_DEG:
        raise Unsupported(
            f"{name}: nearest family {best[1]} is {best[0]:.2f} deg off (limit "
            f"{MAX_FAMILY_RESIDUAL_DEG}) — this line belongs to no measured axis")
    if runner[0] - best[0] < MIN_FAMILY_MARGIN_DEG:
        raise Unsupported(
            f"{name}: families {best[1]} ({best[0]:.2f} deg) and {runner[1]} "
            f"({runner[0]:.2f} deg) fit about equally — the assignment is a coin toss, "
            f"and a coin toss between two axes is a 90 degree error waiting to happen")
    return best[1], best[0]


def report(spec):
    """Run the gate over a lines file and print. Returns violations."""
    viol = []
    fams = {}
    for label, fam in (spec.get("families") or {}).items():
        try:
            vp, w = vanishing_point(fam["lines"], f"family {label}")
            fams[label] = {"vp": vp, "lines": fam["lines"]}
            print(f"  family {label}: vp=({vp[0]:.0f}, {vp[1]:.0f})  widest supporting "
                  f"pair {w:.2f} deg  OK")
        except Unsupported as e:
            print(f"  family {label}: REFUSED — {e}")
            viol.append(str(e))
    for c in spec.get("candidates") or []:
        nm = c.get("name", "line")
        try:
            if c.get("spans"):
                h, worst = straight_direction(c["spans"], nm)
                print(f"  {nm}: straight, spans agree to {worst:.2f} deg, heading "
                      f"{h:.2f} deg")
            lab, res = assign_family(c, fams, nm)
            print(f"  {nm}: family {lab} ({res:.2f} deg residual)")
        except Unsupported as e:
            print(f"  {nm}: REFUSED — {e}")
            viol.append(str(e))
    return viol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True,
                    help='JSON: {"families":{"A":{"lines":[{"m":..,"b":..},..]}},'
                         ' "candidates":[{"name":..,"m":..,"b":..,"u":..,"spans":[..]}]}')
    ap.add_argument("--soft", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    spec = json.loads(open(a.lines, encoding="utf-8").read())
    print("EDGE DIRECTION:")
    viol = report(spec)
    if viol and not a.soft:
        print(f"\n{len(viol)} refusal(s) — nothing downstream may use these directions")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
