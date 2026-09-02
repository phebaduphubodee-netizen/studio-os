"""key_sun — the eye lane's directional key, SOLVED THROUGH A NAMED OPENING.

bpy-free (layer 1). `build_room._add_key_sun` consumes it inside Blender; the tests
run it under plain python. Every number here is a derivation from the spec's own
`room.openings` and `eye_camera`, plus TWO declared assumptions that are printed as
such: the sun's azimuth OFFSET from the opening's inward normal and its ELEVATION.
Site latitude and a date/time are not in the client's brief, so neither can be
derived (R10's word for a typed number is DECLARED ASSUMPTION, and it must print).

WHY A NAMED OPENING AND NOT THE AREA-WEIGHTED PORTAL NORMAL (the derivation that
shipped from p2r35 to p2r91): `element5_lighting.daylight_portals` returns only the
glass OUTSIDE the eye frustum, so on any camera that shows a window — which the
sighted panel of 2026-09-01 measured as 4 of 4 delivered peers and 0 of ours — the
window in the picture is exactly the one the sun is forbidden to come through. The
frame's own window then reads as a bright wall while the beam arrives from behind
the lens. A key must enter through the opening the viewer can see, so the opening
is NAMED and the direction is proven against THAT pane's normal.

DIRECTION IS PROVEN BY A DIRECTION, NEVER BY AN AMOUNT (the lighting skill's law,
paid for over 43 rounds at dot 0.000): `solve()` returns the beam, its dot with the
opening's inward normal, the parallelogram the opening's rect casts on the floor
along the beam, which named masses that patch lands on, and where the patch's
centre projects in the FRAME. A caller that cannot show the patch landing inside
the picture on a named surface has not lit the picture.

Conventions (match build_room's Blender SUN):
  beam    = unit vector the light TRAVELS along (into the room, downward)
  a SUN at rotation_euler (pi/2 - elev, 0, rot) emits along
      (-sin(th) sin(rot), sin(th) cos(rot), -cos(th)),  th = pi/2 - elev
  so for a wanted horizontal heading (hx, hy): rot = atan2(-hx, hy).
  az_deg  = the heading's rotation COUNTER-CLOCKWISE (plan view, +z up) from the
            opening's inward normal. For a south-facing pane (normal +y) a positive
            az swings the heading toward -x, i.e. the sun stands to the EAST.
"""
from __future__ import annotations

import math

MM = 0.001
DOT_FLOOR = 0.30       # the same floor build_room has enforced since p2r78


class KeySunError(ValueError):
    """A key that cannot be proven to enter the room through its named opening."""


def opening_by_id(spec, oid):
    for o in (spec.get("room") or {}).get("openings") or ():
        if str(o.get("id")) == str(oid):
            return o
    known = sorted(str(o.get("id")) for o in (spec.get("room") or {}).get("openings") or ()
                   if o.get("type") == "glass")
    raise KeySunError(f"key sun: no opening {oid!r} in room.openings (glass: {known})")


def _room_centroid_m(spec):
    ol = (spec.get("room") or {}).get("outline_mm") or []
    if not ol:
        return None
    xs = [float(p[0]) * MM for p in ol]
    ys = [float(p[1]) * MM for p in ol]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def opening_frame(spec, oid, toward_mm=None):
    """The named opening as {id, x0,y0,x1,y1 (m), z0,z1 (m), nx,ny (inward unit)}.

    `toward_mm` decides which side is 'inward' (the camera stand when it is known —
    the same rule daylight_portals uses — else the room outline's centroid). A pane
    whose two sides cannot be told apart raises rather than guessing."""
    o = opening_by_id(spec, oid)
    if o.get("type") != "glass":
        raise KeySunError(f"key sun: opening {oid!r} is type {o.get('type')!r}, not glass — "
                          f"a sun through a door or a wall is not a derivation")
    x0, y0, x1, y1 = (float(v) * MM for v in o["rect"])
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 0.05:
        raise KeySunError(f"key sun: opening {oid!r} has no length")
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    ref = None
    if toward_mm:
        ref = (float(toward_mm[0]) * MM, float(toward_mm[1]) * MM)
    else:
        ref = _room_centroid_m(spec)
    if ref is None:
        raise KeySunError("key sun: no camera stand and no room outline — cannot tell "
                          "which side of the pane is the room")
    side = (ref[0] - cx) * nx + (ref[1] - cy) * ny
    if abs(side) < 1e-6:
        raise KeySunError(f"key sun: reference point lies ON the plane of {oid!r}")
    if side < 0:
        nx, ny = -nx, -ny
    z0 = float(o.get("sill_mm") or 0.0) * MM
    z1 = float(o.get("head_mm") or (spec.get("room") or {}).get("ceiling_mm", 2800)) * MM
    return {"id": str(oid), "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "z0": z0, "z1": z1, "nx": nx, "ny": ny, "len_m": length,
            "area_m2": length * (z1 - z0)}


def beam(nx, ny, az_deg, elev_rad):
    """Unit 3D direction the light travels: the inward normal rotated CCW by az in
    plan, tilted down by the elevation."""
    a = math.radians(float(az_deg))
    hx = nx * math.cos(a) - ny * math.sin(a)
    hy = nx * math.sin(a) + ny * math.cos(a)
    ce, se = math.cos(float(elev_rad)), math.sin(float(elev_rad))
    return (hx * ce, hy * ce, -se)


def sun_euler(beam_vec):
    """(rx, ry, rz) for a Blender SUN whose local -Z is `beam_vec`."""
    bx, by, bz = beam_vec
    h = math.hypot(bx, by)
    elev = math.atan2(-bz, h)
    th = math.pi / 2.0 - elev
    rot = math.atan2(-bx, by) if h > 1e-12 else 0.0
    return (th, 0.0, rot)


def emitted_beam(euler):
    """Re-derive the emission vector from a SUN's own euler — the fail-closed half.
    Must reproduce `beam()` for the euler `sun_euler()` returns."""
    th, _ry, rot = euler
    return (-math.sin(th) * math.sin(rot), math.sin(th) * math.cos(rot), -math.cos(th))


def compass_of(beam_vec):
    """Where the SUN stands, as a plan bearing in degrees (0 = +y 'north' of the plan,
    90 = +x 'east'), i.e. the direction OPPOSITE the travel — for the log line."""
    bx, by, _ = beam_vec
    return (math.degrees(math.atan2(-bx, -by)) + 360.0) % 360.0


def floor_patch(frame, beam_vec, z_floor=0.0):
    """The opening's rect swept along the beam to z = z_floor: four (x, y) corners.
    A beam with no downward component never reaches the floor → raises."""
    bx, by, bz = beam_vec
    if bz >= -1e-9:
        raise KeySunError("key sun: beam does not descend — a sun below the horizon")
    pts = []
    for (px, py) in ((frame["x0"], frame["y0"]), (frame["x1"], frame["y1"])):
        for pz in (frame["z0"], frame["z1"]):
            t = (pz - z_floor) / (-bz)
            pts.append((px + bx * t, py + by * t))
    # order: sill-x0, sill-x1, head-x1, head-x0 → a simple parallelogram
    return [pts[0], pts[2], pts[3], pts[1]]


def _poly_aabb_overlap(poly, x0, y0, x1, y1, samples=24):
    """Parallelogram vs AABB overlap in plan, by sampling — good enough to NAME what a
    sun patch lands on (a listed mass either has sun on its footprint or it does not).
    Both corner-inclusion directions are tested so a patch entirely inside a big mass
    (a rug) and a small mass entirely inside the patch are both caught."""
    def inside(px, py):
        # convex polygon, consistent winding
        s = None
        n = len(poly)
        for i in range(n):
            ax, ay = poly[i]
            bx_, by_ = poly[(i + 1) % n]
            cr = (bx_ - ax) * (py - ay) - (by_ - ay) * (px - ax)
            if abs(cr) < 1e-12:
                continue
            if s is None:
                s = cr > 0
            elif (cr > 0) != s:
                return False
        return True
    for (px, py) in poly:
        if x0 <= px <= x1 and y0 <= py <= y1:
            return True
    for i in range(samples + 1):
        for j in range(samples + 1):
            px = x0 + (x1 - x0) * i / samples
            py = y0 + (y1 - y0) * j / samples
            if inside(px, py):
                return True
    return False


def patch_hits(spec, poly, kinds=None):
    """Names of spec masses (builtins + items) whose plan footprint the patch overlaps."""
    hits = []
    for b in spec.get("builtins", []) or []:
        x0, y0 = float(b["x"]) * MM, float(b["y"]) * MM
        x1, y1 = x0 + float(b["w"]) * MM, y0 + float(b["d"]) * MM
        if _poly_aabb_overlap(poly, x0, y0, x1, y1):
            hits.append((b.get("name") or "?", b.get("kind") or "builtin"))
    for it in spec.get("items", []) or []:
        x0, y0 = float(it["x"]) * MM, float(it["y"]) * MM
        x1, y1 = x0 + float(it["w"]) * MM, y0 + float(it["d"]) * MM
        k = it.get("kind") or "item"
        if kinds and k not in kinds:
            continue
        if _poly_aabb_overlap(poly, x0, y0, x1, y1):
            hits.append((it.get("name") or "?", k))
    return hits


def solve(spec, opening_id, az_deg, elev_rad, cam=None, stand_mm=None):
    """Everything build_room needs, and everything a reader needs to refuse.

    cam: a frame_geometry camera dict (ex, ey, tx, ty, eye_h, lens_mm, shift_y,
    res_w, res_h) — when given, the patch centre is projected into the frame.
    Raises KeySunError when the beam does not enter through the named pane
    (dot < DOT_FLOOR) — the same refusal build_room has made since p2r78, now
    against the pane the viewer can see instead of a weighted average."""
    fr = opening_frame(spec, opening_id, toward_mm=stand_mm)
    b = beam(fr["nx"], fr["ny"], az_deg, elev_rad)
    eul = sun_euler(b)
    b2 = emitted_beam(eul)
    if max(abs(b[i] - b2[i]) for i in range(3)) > 1e-6:
        raise KeySunError("key sun: euler round-trip disagrees with the wanted beam — "
                          "the rotation convention has drifted")
    dot = b[0] * fr["nx"] + b[1] * fr["ny"]
    if dot < DOT_FLOOR:
        raise KeySunError(
            f"key sun REFUSED: beam ({b[0]:+.3f},{b[1]:+.3f}) does not enter through "
            f"{opening_id!r} — dot with its inward normal ({fr['nx']:+.3f},{fr['ny']:+.3f}) "
            f"is {dot:+.3f}, under the {DOT_FLOOR} floor (az {az_deg:+.1f} deg is past "
            f"grazing for this pane; name a different pane or a smaller offset)")
    patch = floor_patch(fr, b)
    hits = patch_hits(spec, patch)
    cx = sum(p[0] for p in patch) / 4.0
    cy = sum(p[1] for p in patch) / 4.0
    out = {"opening": fr, "beam": b, "euler": eul, "dot": dot,
           "az_deg": float(az_deg), "elev_deg": math.degrees(float(elev_rad)),
           "sun_bearing_deg": compass_of(b), "floor_patch_m": patch,
           "patch_centre_m": (cx, cy), "lands_on": hits,
           "patch_in_frame": None, "patch_uv": None}
    if cam is not None:
        try:
            import frame_geometry as _fg
            u, v, d = _fg.project((cx, cy, 0.0), cam)
            if u is not None:
                ah = _fg.aspect_h(cam)
                out["patch_uv"] = (u, v)
                out["patch_in_frame"] = bool(abs(u) <= 0.5 and abs(v) <= ah)
            else:
                out["patch_in_frame"] = False
        except Exception as e:                       # noqa: BLE001
            out["patch_in_frame"] = None
            out["patch_uv_error"] = str(e)
    return out


def describe(sol):
    fr = sol["opening"]
    b = sol["beam"]
    lands = ", ".join(f"{n} [{k}]" for n, k in sol["lands_on"]) or "NOTHING LISTED"
    pf = sol["patch_in_frame"]
    pf_s = ("in frame" if pf else ("OUT OF FRAME" if pf is False else "frame unknown"))
    uv = sol.get("patch_uv")
    uv_s = f" at u={uv[0]:+.3f} v={uv[1]:+.3f}" if uv else ""
    return (f"KEY SUN through {fr['id']}: beam ({b[0]:+.3f},{b[1]:+.3f},{b[2]:+.3f}), "
            f"sun bearing {sol['sun_bearing_deg']:.0f} deg (plan; 0=+y, 90=+x), "
            f"az {sol['az_deg']:+.1f} deg off the pane normal [DECLARED], "
            f"elevation {sol['elev_deg']:.1f} deg [DECLARED], dot {sol['dot']:+.3f}; "
            f"floor patch centre ({sol['patch_centre_m'][0]:.2f},{sol['patch_centre_m'][1]:.2f}) m "
            f"{pf_s}{uv_s}; lands on: {lands}")


def cam_for(spec, variant=None, res=(2400, 1800)):
    """frame_geometry camera for the spec's eye_camera, or a named variant — the
    same selection `build_room --eyecam=` makes, so the pure check and the build
    read one camera."""
    import copy
    import frame_geometry as _fg
    s = spec
    if variant:
        vs = spec.get("eye_camera_variants") or {}
        if variant not in vs:
            raise KeySunError(f"key sun: no eye_camera_variants[{variant!r}] "
                              f"(have {sorted(vs)})")
        s = copy.deepcopy(spec)
        v = dict(vs[variant])
        v.pop("note", None)
        s["eye_camera"] = {**(spec.get("eye_camera") or {}), **v}
    return _fg.cam_from_spec(s, res=res)


def main(argv=None):
    import argparse
    import json
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("spec")
    ap.add_argument("--through", required=True, help="opening id the key enters by")
    ap.add_argument("--az", type=float, default=0.0,
                    help="deg CCW (plan) from the pane's inward normal [DECLARED]")
    ap.add_argument("--elev", type=float, default=0.55,
                    help="sun elevation, RADIANS (build_room's KEY_SUN_ELEVATION) [DECLARED]")
    ap.add_argument("--camera", default=None, help="eye_camera_variants key")
    a = ap.parse_args(argv)
    spec = json.load(open(a.spec, encoding="utf-8"))
    try:
        cam = cam_for(spec, a.camera)
    except SystemExit as e:
        print(f"key_sun: camera unreadable ({e}) — COULD NOT RUN")
        return 2
    stand = (cam["ex"] / MM, cam["ey"] / MM)
    try:
        sol = solve(spec, a.through, a.az, a.elev, cam=cam, stand_mm=stand)
    except KeySunError as e:
        print(str(e))
        return 1
    print(describe(sol))
    for i, (x, y) in enumerate(sol["floor_patch_m"]):
        print(f"  patch corner {i}: ({x:.2f}, {y:.2f}) m")
    return 0 if sol["patch_in_frame"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
