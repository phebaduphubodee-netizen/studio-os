"""recurrence.py — DIRECTION FROM TWO OF THE SAME THING. PURE (stdlib only).

    python pipeline/scripts/recurrence.py --scene scene.json

WHY THIS FILE EXISTS
--------------------
2026-08-29. An hour of sub-pixel edge fitting put a kitchen island a quarter turn
out of true. Five minutes with the two bronze drums on its base got it right. The
drums are the same cylinder photographed at two depths, and that is enough:

    each base row gives a depth       D = f * h / (v_base - v_horizon)
    each silhouette width gives it too   w = 2R f / D
    the two centres then give the DIRECTION — no curve to fit, no family to guess

The technique is old and has a name this repo did not know: **recurrence, or
translational symmetry, in a single image** — repeated identical elements give
parallel scene lines and therefore a vanishing point directly (Criminisi, Reid &
Zisserman, *Single View Metrology*; *Novel 3D Scene Understanding Applications From
Recurrence in a Single Image*, arXiv 2210.07991). It is BETTER CONDITIONED than
fitting an edge, for a reason worth stating plainly: an edge fit's accuracy comes
from a lever arm inside one object, a few hundred pixels long, while two instances
put the lever arm across the whole scene. And a repeated object over-determines
itself — the same physical size read at two depths cross-checks both depths — so
this estimator can tell you it is WRONG, which an edge fit never can.

THE ORDER OF THE LADDER, which is the actual lesson (R7d, one layer down):
    1. two instances of one component  -> use them
    2. a measured datum pair on a straight, verifiably straight edge
    3. an edge fit, as a SECOND OPINION only, and never on a curved edge
`edge_direction.py` enforces rung 3's preconditions. This module is rung 1, and it
should be reached for first.

THE SELF-CHECK IS NOT OPTIONAL and it is what makes this a measurement rather than
another confident number. Every instance carrying both a base row and a silhouette
width yields two independent depths. If they disagree past tolerance the answer is
REFUSED, because the disagreement means one of three things and all three are
fatal: the two objects are not actually the same object, a base is occluded so the
contact row is not the contact, or the camera solve is wrong. Returning a heading
anyway would be the exact failure this file was written after — an estimate that
cannot fail is not an estimate.
"""
import argparse
import json
import math
import sys


DEPTH_AGREE_TOL = 0.05          # 5% between the base-row depth and the width depth
COLLINEAR_TOL_MM = 25.0         # residual of >2 instances about their own line


class Unsupported(Exception):
    """The instances do not support a direction."""


class Camera:
    """A level camera: verticals vertical, principal point on the horizon.

    `yaw_deg` is measured off the datum wall, and `origin` is where the camera
    stands in the world frame, so the module can hand back WORLD positions rather
    than camera-frame ones. Everything here is the arithmetic of a pinhole; there
    is no solver and no fitting.
    """

    def __init__(self, f_px, ppx, ppy, height_mm, yaw_deg, origin=(0.0, 0.0)):
        self.f = float(f_px)
        self.ppx, self.ppy = float(ppx), float(ppy)
        self.h = float(height_mm)
        yaw = math.radians(float(yaw_deg))
        self.fwd = (-math.sin(yaw), -math.cos(yaw))
        self.rgt = (self.fwd[1], -self.fwd[0])
        self.origin = (float(origin[0]), float(origin[1]))

    def depth_from_base(self, v_base):
        """Ground-contact row -> depth along the view axis."""
        dv = float(v_base) - self.ppy
        if dv <= 0:
            raise Unsupported(
                f"a ground contact at v={v_base} is at or above the horizon "
                f"({self.ppy}) — that point is not on the floor in front of the "
                f"camera, so no depth exists to compute")
        return self.f * self.h / dv

    def depth_from_width(self, w_px, size_mm):
        if w_px <= 0:
            raise Unsupported("a silhouette width of zero has no depth")
        return float(size_mm) * self.f / float(w_px)

    def world(self, u_centre, depth):
        lat = (float(u_centre) - self.ppx) / self.f * depth
        return (self.origin[0] + depth * self.fwd[0] + lat * self.rgt[0],
                self.origin[1] + depth * self.fwd[1] + lat * self.rgt[1])


def solve(cam, instances, size_mm=None, name="instances"):
    """Positions, and the direction through them, from >= 2 identical objects.

    instances: [{u_centre, v_base, [w_px]}]. `size_mm` is the object's real width
    when it is known; when it is not, the FIRST instance's width defines the size
    and the rest are checked against it — which is exactly what the drums did.
    """
    if len(instances) < 2:
        raise Unsupported(f"{name}: recurrence needs at least two instances of the "
                          f"same object; one instance is a position, not a direction")
    rows, ref_size = [], size_mm
    for i, inst in enumerate(instances):
        d_base = cam.depth_from_base(inst["v_base"])
        w = inst.get("w_px")
        if w and ref_size is None:
            # the first instance CALIBRATES the size; it cannot also check it
            ref_size = 2.0 * (w * d_base / (2.0 * cam.f))
        agree = None
        if w and ref_size:
            d_w = cam.depth_from_width(w, ref_size)
            agree = abs(d_w - d_base) / d_base
            if i > 0 and agree > DEPTH_AGREE_TOL:
                raise Unsupported(
                    f"{name}[{i}]: the base row says depth {d_base:.0f} mm and the "
                    f"silhouette width says {d_w:.0f} mm — {agree * 100:.1f}% apart "
                    f"(limit {DEPTH_AGREE_TOL * 100:.0f}%). These are not two views of "
                    f"the same object, or one base is occluded and the row measured is "
                    f"not the contact. REFUSED: an estimator that cannot fail is not an "
                    f"estimator")
        x, y = cam.world(inst["u_centre"], d_base)
        rows.append({"depth_mm": d_base, "x": x, "y": y,
                     "width_agreement": agree, "u": float(inst["u_centre"])})

    (x0, y0), (x1, y1) = (rows[0]["x"], rows[0]["y"]), (rows[-1]["x"], rows[-1]["y"])
    dx, dy = x1 - x0, y1 - y0
    span = math.hypot(dx, dy)
    if span < 1.0:
        raise Unsupported(f"{name}: the instances land in the same place; no direction")
    heading = math.degrees(math.atan2(dy, dx)) % 180.0

    resid = 0.0
    for r in rows[1:-1]:
        resid = max(resid, abs((dx * (r["y"] - y0) - dy * (r["x"] - x0)) / span))
    if len(rows) > 2 and resid > COLLINEAR_TOL_MM:
        raise Unsupported(
            f"{name}: the instances are {resid:.0f} mm off their own straight line "
            f"(limit {COLLINEAR_TOL_MM:.0f}) — they are not a repeated row, so the line "
            f"through them is not a scene direction")

    # the direction's vanishing column, for cross-checking against a solved axis
    fx = dx * cam.fwd[0] + dy * cam.fwd[1]
    rx = dx * cam.rgt[0] + dy * cam.rgt[1]
    vp_u = cam.ppx + cam.f * (rx / fx) if abs(fx) > 1e-9 else float("inf")

    return {"instances": rows, "heading_deg": heading, "spacing_mm": span,
            "size_mm": ref_size, "vp_u": vp_u, "collinearity_mm": resid}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True,
                    help='JSON: {"camera":{f_px,ppx,ppy,height_mm,yaw_deg,origin},'
                         ' "size_mm":null, "instances":[{u_centre,v_base,w_px}]}')
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    s = json.loads(open(a.scene, encoding="utf-8").read())
    c = s["camera"]
    cam = Camera(c["f_px"], c["ppx"], c["ppy"], c["height_mm"], c["yaw_deg"],
                 c.get("origin", (0.0, 0.0)))
    try:
        r = solve(cam, s["instances"], s.get("size_mm"), s.get("name", "instances"))
    except Unsupported as e:
        print(f"RECURRENCE REFUSED: {e}")
        return 1
    for i, inst in enumerate(r["instances"]):
        ag = inst["width_agreement"]
        print(f"  instance {i}: depth {inst['depth_mm']:8.0f} mm   world "
              f"({inst['x']:.0f}, {inst['y']:.0f})"
              + (f"   width agrees to {ag * 100:.1f}%" if ag is not None else ""))
    print(f"  object size    {r['size_mm']:.0f} mm" if r["size_mm"] else "")
    print(f"  spacing        {r['spacing_mm']:.0f} mm")
    print(f"  HEADING        {r['heading_deg']:.1f} deg")
    print(f"  vanishing col  u = {r['vp_u']:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
