#!/usr/bin/env python3
"""vanishing_check.py — the REFERENCE photo's own camera, solved from its vanishing points.

    python pipeline/scripts/vanishing_check.py --lines <marked.json>
                                               [--our-fov-deg D | --our-focal-px F]

WHY THIS EXISTS, AND WHAT IT REPLACES
-------------------------------------
2026-08-28, from a 3D Shaker tutorial (02:15-04:30) in which a studio reproduces a
published interior. Before modelling anything they open the reference photo in fSpy, draw
two pairs of lines along edges that are parallel in the real room, and read off the
camera's focal length, position and orientation. The scale comes from ONE measured real
dimension, which they get by reverse-image-searching the chair in the photo until they find
the product page that prints its size.

OUR CAMERA IS SOLVED FROM OUR OWN GEOMETRY. `build_room.solve_eye_camera` places the eye
from the room we built and aims it at the mass we chose. That is a SELF-CONSISTENCY check
of exactly the kind CLAUDE.md R7b already convicted once: *"rounds 12-18 asserted the built
figure matched its spec height to within 2 mm — a check against a number we chose ourselves,
which can prove the build correct and never notice the ask was wrong."* A camera solved
from our own room can be perfectly correct about our own room and still be standing
somewhere the reference's camera never stood, and nothing in the lane can tell.

This module closes that: the reference image's own pixels yield a focal length and an
orientation, independent of anything we built. Where it disagrees with our camera, the
disagreement is a number in degrees.

THE MATHEMATICS, AND WHERE IT REFUSES
-------------------------------------
Two families of lines that are parallel in the world meet at a vanishing point in the image.
For a pinhole camera with principal point P and the two vanishing points Vx, Vy of two
ORTHOGONAL world directions:

    f^2 = -( (Vx - P) . (Vy - P) )                      [Caprile & Torre; fSpy's own solve]

so the marked lines determine the focal length outright. The direction vectors
(Vx-P, f) and (Vy-P, f), normalised, are two columns of the camera's rotation; their cross
product is the third. From f the horizontal field of view is 2*atan(w / 2f).

It refuses, rather than returning a number, when:

  * an axis carries fewer than two lines (nothing to intersect);
  * the lines of an axis are too near parallel IN THE IMAGE — the vanishing point is then
    at infinity and its position is numerically meaningless. This is reported as the
    conditioning of the 2x2 normal equations, not hidden;
  * the marked lines do not agree — the RMS distance from the fitted vanishing point to the
    marked lines exceeds `MAX_RESIDUAL_PX`. A vanishing point that misses its own lines is
    a mis-marking, and reading a focal length off it produces a confident wrong camera;
  * the two vanishing points give a POSITIVE dot product, which makes f^2 negative. That
    configuration cannot come from a real pinhole camera looking at two orthogonal
    directions, so the marking is wrong. This is the check that makes the rung fail closed
    instead of returning an imaginary camera.

IDENTITY IS SIGNED, NEVER DERIVED. Which edges in the photograph are "parallel in the real
room" is a human claim about the world — the same class as a BF code (R12, D-037) — so the
lines file carries `signed_by` and `signed_at` and this module refuses a file without them.
The builder's eye MARKS the lines (R7d: C1 aims, it does not convict); the arithmetic and
the refusals are the instrument's.

EXIT CODES
    0  solved (and, if a camera of ours was given, the comparison printed)
    1  a comparison was asked for and the gap is outside --tolerance-deg
    2  COULD NOT RUN — any refusal above
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class VanishingError(Exception):
    """The camera cannot be solved from what was marked. Callers turn this into exit 2."""


MIN_LINES_PER_AXIS = 2
MAX_RESIDUAL_PX = 6.0      # RMS distance from the fitted VP to its own marked lines
MIN_CONDITION = 1e-6       # normal-equation determinant, scaled — below this: SINGULAR
# ...AND THAT NUMBER IS NOT THE GATE, which this module learned the hard way one day
# after it was written. For two unit lines the scaled determinant above is exactly
# sin^2(theta), so `1e-6` refuses only pairs within **0.057 deg** of parallel: a
# guard against dividing by zero, not against an unusable vanishing point. On
# 2026-08-29 an island was built a quarter turn out from an axis whose two
# supporting lines were **4.24 deg apart** — 175x above this threshold, and
# numerically fine. fSpy's own manual states the practical limit in words: "when
# the line segments used to define a vanishing point are near-parallel, the
# vanishing point position cannot be computed accurately; a larger angle between
# the lines yields better results." So the refusal that matters is ANGULAR and is
# stated in degrees. Note what is deliberately NOT gated: how far off-frame the
# vanishing point lands. A VP at infinity is the correct answer for lines truly
# parallel to the image plane, and the pose literature is explicit that a large
# covariance there does not imply a bad estimate.
MIN_AXIS_ANGLE_DEG = 10.0


# --------------------------------------------------------------------------- pure core

def line_from(p, q):
    """Two image points -> (a, b, c) with a*x + b*y + c = 0 and a^2 + b^2 = 1.

    Normalised so that |a*x + b*y + c| is the PIXEL distance from (x, y) to the line. That
    is what makes the residual below readable as a number of pixels instead of an
    uninterpretable algebraic quantity.
    """
    (x1, y1), (x2, y2) = (float(p[0]), float(p[1])), (float(q[0]), float(q[1]))
    a, b = y1 - y2, x2 - x1
    n = math.hypot(a, b)
    if n == 0:
        raise VanishingError(f"a segment of zero length at ({x1},{y1})")
    a, b = a / n, b / n
    c = -(a * x1 + b * y1)
    return a, b, c


def vanishing_point(segments, min_lines=MIN_LINES_PER_AXIS,
                    max_residual=MAX_RESIDUAL_PX, min_condition=MIN_CONDITION):
    """Least-squares intersection of >=2 image lines, with its own refusals.

    Returns (point, residual_px, condition). Minimises the sum of squared PIXEL distances
    from the point to every marked line, which is a 2x2 normal equation — no numpy, and the
    same code the tests drive.
    """
    if len(segments) < min_lines:
        raise VanishingError(f"an axis needs at least {min_lines} lines, got "
                             f"{len(segments)} — nothing to intersect")
    lines = [line_from(p, q) for p, q in segments]
    saa = sum(a * a for a, _b, _c in lines)
    sab = sum(a * b for a, b, _c in lines)
    sbb = sum(b * b for _a, b, _c in lines)
    sac = sum(a * c for a, _b, c in lines)
    sbc = sum(b * c for _a, b, c in lines)
    det = saa * sbb - sab * sab
    # Scale-free conditioning: for unit (a,b), saa + sbb == len(lines), so the determinant
    # of a well-spread set approaches n^2/4 and collapses to 0 as the lines become parallel.
    cond = det / (len(lines) ** 2 / 4.0)
    if abs(cond) < min_condition:
        raise VanishingError(
            f"the lines of this axis are parallel in the image (conditioning {cond:.2e}) — "
            f"its vanishing point is at infinity and has no usable position. Mark edges "
            f"that visibly converge.")
    # THE ANGULAR GATE, after the singularity check and before anything is solved.
    # Order matters: exactly-parallel lines are a SINGULARITY and keep their own
    # refusal above; what lands here is the case that reads fine numerically and is
    # unusable in practice. The axis that produced a quarter-turn error on
    # 2026-08-29 measured 4.24 deg, which is 175x above the threshold above.
    import edge_direction as ED          # the angular gate lives there, with its tests
    slopes = [((y1 - y0) / (x1 - x0) if abs(x1 - x0) > 1e-9 else 1e9)
              for (x0, y0), (x1, y1) in segments]
    widest = max(ED.pair_angle_deg(a, b) for a in slopes for b in slopes)
    if widest < ED.MIN_FAMILY_ANGLE_DEG:
        raise VanishingError(
            f"the widest pair of lines on this axis is {widest:.2f} deg apart (need "
            f"{ED.MIN_FAMILY_ANGLE_DEG}). Near-parallel segments put the vanishing "
            f"point where fit noise moves it by kilometres (fSpy, Basics). This is the "
            f"practical gate; the conditioning test above only catches an outright "
            f"singularity, at 0.057 deg.")
    x = (-sac * sbb + sbc * sab) / det
    y = (-sbc * saa + sac * sab) / det
    resid = math.sqrt(sum((a * x + b * y + c) ** 2 for a, b, c in lines) / len(lines))
    if resid > max_residual:
        raise VanishingError(
            f"the fitted vanishing point misses its own lines by {resid:.1f} px RMS "
            f"(limit {max_residual}). Those edges are not parallel in the room, or they "
            f"were marked wrong; a focal length read off them would be confidently wrong.")
    return (x, y), resid, cond


def focal_from_vps(vx, vy, principal):
    """Two orthogonal vanishing points + principal point -> focal length in pixels.

    f^2 = -((Vx - P) . (Vy - P)). A non-negative dot product means no real pinhole camera
    produces this pair, so it RAISES instead of returning a number.
    """
    ux, uy = vx[0] - principal[0], vx[1] - principal[1]
    wx, wy = vy[0] - principal[0], vy[1] - principal[1]
    dot = ux * wx + uy * wy
    if dot >= 0:
        raise VanishingError(
            f"the two vanishing points give a dot product of {dot:+.1f} about the "
            f"principal point. f^2 would be negative: no real camera looking at two "
            f"perpendicular directions produces this. The two axes are not perpendicular "
            f"in the room, or one of them is mis-marked.")
    return math.sqrt(-dot)


def fov_deg(focal_px, extent_px):
    """Field of view across `extent_px` for a pinhole of this focal length, in degrees."""
    if focal_px <= 0 or extent_px <= 0:
        raise VanishingError("focal length and extent must both be positive")
    return math.degrees(2.0 * math.atan(extent_px / (2.0 * focal_px)))


def focal_from_fov(fov_degrees, extent_px):
    """Inverse of `fov_deg` — so our own camera, which is stated as a FOV, can be compared
    in the same unit as the solve."""
    half = math.radians(float(fov_degrees)) / 2.0
    if not (0 < half < math.pi / 2):
        raise VanishingError(f"a field of view of {fov_degrees} degrees is not a camera")
    return extent_px / (2.0 * math.tan(half))


def orientation(vx, vy, principal, focal, vertical_axis=None):
    """The reference camera's rotation, as the two marked world axes in camera coordinates.

    TILT IS ONLY COMPUTED WHEN THE CALLER SAYS WHICH MARKED AXIS IS THE WORLD VERTICAL, and
    that is not a formality. The first cut of this function guessed — it took whichever
    vanishing point sat further from the principal point in y as "up". In the tutorial that
    prompted this module the two marked axes are the CEILING EDGE and the SHELVES, both
    HORIZONTAL, and the guess would have returned a confident tilt for a pair of directions
    neither of which points up. A number derived from a guess about the world is the defect
    this repo calls a typed coordinate (R9); so with no declaration, tilt is None and the
    report says the caller did not state it.
    """
    def unit(vp):
        v = (vp[0] - principal[0], vp[1] - principal[1], focal)
        n = math.sqrt(sum(c * c for c in v))
        return tuple(c / n for c in v)

    ax, ay = unit(vx), unit(vy)
    az = (ax[1] * ay[2] - ax[2] * ay[1],
          ax[2] * ay[0] - ax[0] * ay[2],
          ax[0] * ay[1] - ax[1] * ay[0])
    n = math.sqrt(sum(c * c for c in az)) or 1.0
    az = tuple(c / n for c in az)
    tilt = None
    if vertical_axis in ("x", "y"):
        up = ax if vertical_axis == "x" else ay
        # The optical axis is camera +Z; the world vertical's z-component is the sine of
        # the angle between the camera's view direction and the horizontal plane.
        tilt = math.degrees(math.asin(max(-1.0, min(1.0, up[2]))))
    return {"x_axis": ax, "y_axis": ay, "z_axis": az, "tilt_deg": tilt,
            "vertical_axis": vertical_axis}


def load_lines(doc):
    """Validate a marked-lines document. Identity is SIGNED, never derived."""
    for key in ("image_size", "axis_x", "axis_y"):
        if key not in doc:
            raise VanishingError(f"the lines file has no {key!r}")
    if not doc.get("signed_by") or not doc.get("signed_at"):
        raise VanishingError(
            "the lines file carries no `signed_by`/`signed_at`. WHICH edges are parallel "
            "in the real room is a claim about the world, not a derivation — it is signed "
            "or it is refused (R12, D-037).")
    w, h = doc["image_size"]
    if not (w > 0 and h > 0):
        raise VanishingError(f"image_size {doc['image_size']!r} is not a size")
    principal = doc.get("principal_point") or [w / 2.0, h / 2.0]
    return float(w), float(h), list(principal), doc["axis_x"], doc["axis_y"]


def solve(doc):
    """Marked-lines document -> the reference camera. Every refusal above applies."""
    w, h, principal, ax_x, ax_y = load_lines(doc)
    vx, rx, cx = vanishing_point(ax_x)
    vy, ry, cy = vanishing_point(ax_y)
    f = focal_from_vps(vx, vy, principal)
    return {
        "image_size": [w, h],
        "principal_point": principal,
        "vp_x": list(vx), "vp_y": list(vy),
        "residual_px": {"x": rx, "y": ry},
        "conditioning": {"x": cx, "y": cy},
        "focal_px": f,
        "fov_h_deg": fov_deg(f, w),
        "fov_v_deg": fov_deg(f, h),
        "orientation": orientation(vx, vy, principal, f, doc.get("vertical_axis")),
    }


def compare(sol, our_focal_px=None, our_fov_deg=None):
    """Our camera against the reference's, in one unit. Returns (gap_deg, lines)."""
    w = sol["image_size"][0]
    if our_focal_px is None and our_fov_deg is None:
        return None, ["OUR CAMERA   none given — this run solves the reference only"]
    if our_focal_px is None:
        our_focal_px = focal_from_fov(our_fov_deg, w)
    ours = fov_deg(our_focal_px, w)
    gap = ours - sol["fov_h_deg"]
    return gap, [
        f"OUR CAMERA   focal {our_focal_px:8.1f} px   h-fov {ours:6.2f} deg",
        f"GAP          {gap:+.2f} deg of horizontal field of view",
    ]


def report(sol):
    o = sol["orientation"]
    return "\n".join([
        f"REFERENCE CAMERA, solved from the image alone",
        f"  image        {sol['image_size'][0]:.0f} x {sol['image_size'][1]:.0f} px"
        f"   principal ({sol['principal_point'][0]:.1f}, {sol['principal_point'][1]:.1f})",
        f"  vp x         ({sol['vp_x'][0]:10.1f}, {sol['vp_x'][1]:10.1f})"
        f"   residual {sol['residual_px']['x']:.2f} px   cond {sol['conditioning']['x']:.3f}",
        f"  vp y         ({sol['vp_y'][0]:10.1f}, {sol['vp_y'][1]:10.1f})"
        f"   residual {sol['residual_px']['y']:.2f} px   cond {sol['conditioning']['y']:.3f}",
        f"  focal        {sol['focal_px']:.1f} px",
        f"  field of view {sol['fov_h_deg']:.2f} deg horizontal · "
        f"{sol['fov_v_deg']:.2f} deg vertical",
        (f"  tilt         {o['tilt_deg']:+.2f} deg from level "
         f"({'level, two-point' if abs(o['tilt_deg']) < 1.0 else 'looking up/down'})"
         if o["tilt_deg"] is not None else
         "  tilt         not computed — the lines file does not say which marked axis is "
         "the world vertical (`vertical_axis`)"),
    ])


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lines", required=True)
    ap.add_argument("--our-focal-px", type=float, default=None)
    ap.add_argument("--our-fov-deg", type=float, default=None)
    ap.add_argument("--tolerance-deg", type=float, default=None,
                    help="fail (exit 1) when the field-of-view gap exceeds this")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv[1:])

    try:
        doc = json.load(open(a.lines, encoding="utf-8"))
        sol = solve(doc)
    except (VanishingError, OSError, ValueError) as e:
        print(f"vanishing_check: COULD NOT RUN — {e}", file=sys.stderr)
        return 2

    print(report(sol))
    try:
        gap, lines = compare(sol, a.our_focal_px, a.our_fov_deg)
    except VanishingError as e:
        print(f"vanishing_check: COULD NOT RUN — {e}", file=sys.stderr)
        return 2
    print()
    print("\n".join(lines))

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"reference": sol, "gap_deg": gap}, fh, indent=2, ensure_ascii=False)

    if a.tolerance_deg is not None:
        if gap is None:
            print("vanishing_check: --tolerance-deg given with no camera of ours to "
                  "compare", file=sys.stderr)
            return 2
        if abs(gap) > a.tolerance_deg:
            print(f"\nvanishing_check: the field-of-view gap {gap:+.2f} deg exceeds "
                  f"{a.tolerance_deg}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
