#!/usr/bin/env python3
"""detail.py — A CAMERA AIMED AT ONE OBJECT, SOLVED FROM THE OBJECT.

    python detail.py <scene.json> --object <name> [--res 2400x1800] [--spec <spec.json>]

Owner order 2026-08-27 ("ลุยยาว ๆ", item B), answering his third question directly:
*"เวลามอง คุณมองแค่รูปภาพรวมที่มุมกล้อง fixed ทั้ง ๆ ที่คุณมีอำนาจเปลี่ยนมุมกล้องเพื่อมอง
สิ่งที่อยากจะแก้ไข ... จะได้แก้ได้อย่างตรงจุด"*

WHAT THE MEASUREMENT SAID BEFORE THIS FILE EXISTED. Of 213 measurable in-frustum
objects on the delivered frame, 109 (51.2%) have a short side under 24 px — the line
this repo set at p2r87b, below which a faceted edge and a smooth gradient are the same
picture. The median object in the frame is 20.7 px. The lane holds 16 named camera
variants and rendered 13 of them, ALL between 2026-07-17 and 2026-07-28; in the 58 days
since it has produced 350 frames from one camera and zero diagnostic views of the room.
And the 16 named views do not answer it: they rescue 8 of the 109, because they are
alternative ROOM cameras, not detail cameras.

THE AIM IS DERIVED, NEVER TYPED — R9 applied to the lens, and this is the whole design.
The builder does not get to choose where to look:
  * the AIM is the named object's own AABB centre, read from the built scene's dump;
  * the DIRECTION is the ray from that object toward the hero camera, so the detail view
    shows the same FACE the delivered frame shows — not a flattering other side;
  * the DISTANCE is solved: the closest stand at which the whole object still fits the
    frame with margin;
  * the vertical framing is solved shift, because the room's cameras are LEVEL
    (two-point) and a tilted detail view would not match the geometry it is diagnosing.
There is no `--x`, no `--offset` and no `--nudge`, and there will not be one: a typed
crop box is exactly what `p2_exit.CROPS` is, and those boxes went stale the moment D-152
moved the camera under them — `rug_edge` spent rounds measuring a box holding 0.8% rug.

WHAT A DETAIL VIEW MAY AND MAY NOT DO. It may DIAGNOSE — name the knob, show the defect
at a size where shape is decidable. It may never CLOSE a work item: closure is judged on
the delivered frame and on his eye (R3). The reason is measured rather than principled:
p2r84 argued for a whole round about a bowl rendering 413 px² — 20x20 px, 0.0096% of the
frame. At 1000x1000 that bowl looks fine, and closing on it would have hidden the actual
defect, which is that nothing in that cell reads at all. The cruelty of the hero frame is
information, so the verdict stays there.

PURE + IMPORTABLE (layer law): no bpy, no PIL. build_room consumes the solved camera
inside Blender; tests and gates consume it under plain python.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame_geometry as FG                                   # noqa: E402

# The closest a camera may stand to what it is looking at. Not a taste number: nearer
# than this and a room camera's near clip and its own body start intersecting joinery,
# and the view stops being a view of the room.
MIN_STAND_M = 0.35
# Margin kept around the object inside the frame, in frame units. A detail view whose
# subject touches the edge is a crop, and a crop is what this file exists to replace.
FIT_MARGIN = 0.06
# The most shift a detail view may carry. A real lens shifts by a fraction of the sensor;
# the room's own hero camera runs -0.088. THE FIRST VERSION HAD NO CAP AND EARNED THIS
# ONE: it pinned the camera to the hero's eye height and let shift absorb everything, so
# aiming at a sconce 0.5 m above the lens from 0.35 m away solved shift_y = 0.854 — eight
# times the hero's — and rendered a sheared off-axis frame that was not a view of
# anything. The height is now derived instead (see solve_detail_camera), and this cap is
# what makes a residual failure LOUD rather than silently absurd.
MAX_SHIFT = 0.30


class CannotAim(Exception):
    """Raised instead of guessing. Every refusal names what could not be derived."""


def _corners(aabb):
    (x0, y0, z0), (x1, y1, z1) = aabb
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def _centre(aabb):
    (x0, y0, z0), (x1, y1, z1) = aabb
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)


def _cam_at(stand, aim, hero, res, shift_y=0.0, eye_h=None):
    return {"ex": stand[0], "ey": stand[1], "tx": aim[0], "ty": aim[1],
            "eye_h": hero["eye_h"] if eye_h is None else eye_h,
            "lens_mm": hero["lens_mm"],
            "shift_y": shift_y, "res_w": res[0], "res_h": res[1]}


def _solve_shift(cam, aabb):
    """Centre the object vertically by SHIFT, because the camera is level.

    v = vz/depth * k - shift_y, so the shift that centres the object is the midpoint of
    its unshifted angular extent. Solved, not searched.
    """
    flat = dict(cam, shift_y=0.0)
    vs = []
    for p in _corners(aabb):
        u, v, d = FG.project(p, flat)
        if v is not None:
            vs.append(v)
    if not vs:
        raise CannotAim("every corner of the object is behind the lens")
    return (min(vs) + max(vs)) / 2.0


def _fits(cam, aabb, margin=FIT_MARGIN):
    ah = FG.aspect_h(cam)
    for p in _corners(aabb):
        u, v, d = FG.project(p, cam)
        if u is None:
            return False
        if abs(u) > 0.5 - margin or abs(v) > ah - margin:
            return False
    return True


def short_side_px(cam, aabb):
    """Projected short side of the object's silhouette box, in pixels."""
    pts = [FG.to_px(p, cam) for p in _corners(aabb)]
    pts = [p for p in pts if p is not None]
    if len(pts) < 2:
        return 0.0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(max(xs) - min(xs), max(ys) - min(ys))


def solve_detail_camera(aabb, hero, res=(2400, 1800), margin=FIT_MARGIN,
                        min_stand_m=MIN_STAND_M, room_bounds=None):
    """The closest LEVEL camera, on the hero's own side, that still holds the whole object.

    Returns (cam, info). Raises CannotAim rather than returning a view that crops its
    subject or stands inside it — "could not aim" must never render like "aimed and it
    was fine" (R11's sentence, applied to a camera).
    """
    cx, cy, cz = _centre(aabb)
    hx, hy = hero["ex"], hero["ey"]
    dx, dy = hx - cx, hy - cy
    n = math.hypot(dx, dy)
    if n < 1e-6:
        raise CannotAim("the hero camera stands on top of this object in plan, so "
                        "'the side the delivered frame sees' has no direction")
    ux, uy = dx / n, dy / n

    # THE LENS HEIGHT IS DERIVED TOO, and this is the correction that made the rung real.
    # Pinning the camera to the hero's eye height and letting SHIFT absorb the difference
    # is arithmetically valid and physically nonsense: a sconce 0.5 m above the lens seen
    # from 0.35 m solved shift_y = 0.854 against a hero camera that runs -0.088, and what
    # rendered was a sheared frame that was a view of nothing. A detail camera stands at
    # its SUBJECT's height; it stays LEVEL, so verticals are still vertical and the view
    # is still comparable to the delivered frame.
    def cam_for(dist):
        stand = (cx + ux * dist, cy + uy * dist)
        c = _cam_at(stand, (cx, cy), hero, res, eye_h=cz)
        c["shift_y"] = _solve_shift(c, aabb)
        return c

    # The far end must fit; grow until it does or give up honestly.
    hi = max(n, 1.0)
    for _ in range(24):
        if _fits(cam_for(hi), aabb, margin):
            break
        hi *= 1.5
    else:
        raise CannotAim("no stand on this ray frames the whole object — it is longer "
                        "than the lens can hold from any distance on the hero's side")
    lo = min_stand_m
    if _fits(cam_for(lo), aabb, margin):
        hi = lo                                   # already fits at the closest legal stand
    else:
        for _ in range(48):                       # bisect for the CLOSEST fitting stand
            mid = (lo + hi) / 2.0
            if _fits(cam_for(mid), aabb, margin):
                hi = mid
            else:
                lo = mid
    cam = cam_for(hi)
    if hi < min_stand_m - 1e-9:
        raise CannotAim(f"the solved stand is {hi:.3f} m from the subject, inside the "
                        f"{min_stand_m} m floor")
    if abs(cam["shift_y"]) > MAX_SHIFT:
        raise CannotAim(
            f"the framing needs shift_y {cam['shift_y']:+.3f}, past the {MAX_SHIFT} cap "
            f"(the room's hero camera runs -0.088). A shift this large is not a lens, it "
            f"is a shear — the subject cannot be centred from a level stand on this ray")
    if room_bounds is not None:
        (rx0, ry0), (rx1, ry1) = room_bounds
        if not (rx0 <= cam["ex"] <= rx1 and ry0 <= cam["ey"] <= ry1):
            raise CannotAim(
                f"the solved stand ({cam['ex']:.2f}, {cam['ey']:.2f}) is outside the "
                f"room — this object can only be framed from inside a wall, which is a "
                f"fact about the object's placement, not a camera to render")
    return cam, {"stand_m": hi, "short_px": short_side_px(cam, aabb),
                 "hero_short_px": short_side_px(hero, aabb)}


# ------------------------------------------------------------------ scene access

def object_aabb(dump_path, name):
    d = json.load(open(dump_path, encoding="utf-8"))
    for o in d.get("objects", []):
        if o.get("name") == name:
            if not o.get("aabb"):
                raise CannotAim(f"{name!r} has no aabb in the dump")
            return [tuple(v) for v in o["aabb"]]
    near = [o["name"] for o in d.get("objects", [])
            if name.lower() in o.get("name", "").lower()][:8]
    raise CannotAim(f"no object named {name!r} in {os.path.basename(dump_path)}"
                    + (f" — did you mean {near}?" if near else ""))


def room_bounds_from(dump_path):
    """The floor's own plan extent — the region a camera may legally stand in."""
    d = json.load(open(dump_path, encoding="utf-8"))
    for o in d.get("objects", []):
        if o.get("name") == "floor" and o.get("aabb"):
            (x0, y0, _), (x1, y1, _) = o["aabb"]
            return ((x0, y0), (x1, y1))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dump", help="a scene-dump@2 json written by a build")
    ap.add_argument("--object", required=True)
    ap.add_argument("--spec", default=None, help="spec holding the hero eye_camera")
    ap.add_argument("--res", default="2400x1800")
    a = ap.parse_args(argv)
    W, H = (int(v) for v in a.res.lower().split("x"))
    try:
        aabb = object_aabb(a.dump, a.object)
        if a.spec:
            hero = FG.cam_from_spec(json.load(open(a.spec, encoding="utf-8")), res=(W, H))
        else:
            src = (json.load(open(a.dump.replace(".scene.json", ".idmask.json"),
                                  encoding="utf-8")).get("source") or {})
            if not src.get("matrix"):
                raise CannotAim("no --spec given and no idmask sidecar to read the hero "
                                "camera from")
            m = src["matrix"]
            # THE MATRIX ALREADY HOLDS THE LOOK DIRECTION — it was being thrown
            # away and replaced with an assumption, one line below the check that
            # correctly refuses when the matrix is missing. A Blender camera looks
            # along its local -Z, i.e. the negated third column of the rotation
            # part; the old `tx = m[0][3] + 1.0, ty = m[1][3]` hard-aimed every
            # reconstructed hero along world +X. Surveyed over all 49 real
            # `.idmask.json` sidecars on this machine: 26 of them (53%) point at
            # 38 deg, not 0. `hero_short_px` is computed by projecting the
            # subject's AABB through this camera, so a wrong bearing silently
            # rescales the very ratio the detail view reports.
            look = (-m[0][2], -m[1][2])
            if (look[0] * look[0] + look[1] * look[1]) ** 0.5 < 1e-6:
                raise CannotAim("the hero camera in this sidecar looks straight up "
                                "or down; its plan bearing is undefined, and a "
                                "detail view aimed from a guessed bearing reports "
                                "a ratio about a camera nobody used")
            # SHIFT IS READ, NOT ZEROED. The sidecar carries it beside `lens`, and
            # all 49 on this machine carry a NON-ZERO shift_y (-0.02 to -0.14);
            # every one was being replaced with a literal 0.0. Missing is refused
            # rather than defaulted, on this file's own standard: it raises
            # CannotAim rather than returning a view it cannot stand behind.
            shift = src.get("shift")
            if not shift or len(shift) < 2:
                raise CannotAim("the idmask sidecar carries no `shift` — the hero "
                                "camera cannot be reconstructed, and a detail view "
                                "built on a guessed shift measures a different lens")
            hero = {"ex": m[0][3], "ey": m[1][3], "eye_h": m[2][3],
                    "tx": m[0][3] + look[0], "ty": m[1][3] + look[1],
                    "lens_mm": src.get("lens") or 21.0,
                    "shift_y": float(shift[1]),
                    "res_w": W, "res_h": H}
        cam, info = solve_detail_camera(aabb, hero, res=(W, H),
                                        room_bounds=room_bounds_from(a.dump))
    except CannotAim as e:
        print(f"DETAIL COULD NOT AIM: {e}")
        return 2
    print(json.dumps({"object": a.object, "camera": cam, **info}, indent=1))
    print(f"\nDETAIL {a.object}: {info['hero_short_px']:.1f} px on the hero camera -> "
          f"{info['short_px']:.1f} px from {info['stand_m']:.2f} m "
          f"({info['short_px'] / max(1e-6, info['hero_short_px']):.1f}x)")
    print("DIAGNOSES ONLY — a detail view may name the knob; it may never close a work "
          "item. Closure is the delivered frame and his eye (R3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
