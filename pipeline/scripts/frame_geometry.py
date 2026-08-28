#!/usr/bin/env python3
"""frame_geometry.py — WHAT THE LENS ACTUALLY CONTAINS, as numbers, before a render.

WHY THIS EXISTS (2026-08-26, sighted panel on p2r77 beside two delivered anchors).
Three independent readings said the same thing about the eye frame and none of the
repo's 34 rungs could see any of it, because every one of them measures the SCENE or
the FRAME'S PIXELS and none measures THE MAPPING BETWEEN THEM:

  * "No ceiling exists anywhere in the frame — the slat wall runs off the top edge, so
    the wall has no height and the image reads as a backdrop."
  * "The bench's front face and its floor contact are cropped out by the bottom edge;
    floor survives only as rug slivers in the corners."
  * "The nearest 30% of frame height is a defocus mush" — measured: p99 laplacian 7-9
    on the ottoman rows against 68-81 in the pillow plane, while the delivered anchors
    run their FOREGROUND props SHARPER than their back walls (anchor bench book 1090
    vs far panel wall 215).

All three are properties of camera + lens + shift + aperture against the room's own
geometry. Every one is decidable WITHOUT rendering, and every one was invisible to a
lane that renders first and judges the pixels afterwards. This module is the missing
half: it projects the spec's own masses through the spec's own camera and reports what
lands inside the frame, what falls outside it, and what is inside the depth of field.

THE LAW IT SERVES: R9 says a position that can be DERIVED from a contact must never be
typed. A camera is the same shape of object — `shift_y: -0.14` is a typed RESULT whose
relationship ("include the wall-ceiling junction, include the nearest mass's floor
contact") was never written down, so when the bench moved the framing silently broke
and nothing failed. `solve_framing` writes the relationship instead and hands back the
numbers; `dof_from_geometry` does the same for the aperture, which was a literal 2.8
carried from a study of other people's .blend files while the delivered frames we are
judged against are deep-focus.

PURE + IMPORTABLE (layer law, pipeline/CLAUDE.md): no bpy, no PIL. build_room.py
consumes it inside Blender; tests and gates consume it under plain python.

CONVENTIONS, verified against build_room.add_suite_eye_camera:
  * camera is LEVEL (two-point: verticals stay vertical), eye height from camera_config
  * sensor_fit = 'HORIZONTAL', sensor 36 mm, so the HORIZONTAL fov is pinned by the
    lens and the aspect ratio is a VERTICAL framing parameter (camera_config's own note)
  * shift_y is in units of the sensor's fitted (horizontal) dimension, and POSITIVE
    shift_y tilts the frustum axis UP -> more ceiling in frame. build_room's
    RENDER_SHIFT_Y = -0.10 and the spec's -0.14 therefore frame DOWN, which is what
    amputated the wall.
"""
from __future__ import annotations

import json
import math
import os
import sys

MM = 0.001
SENSOR_MM = 36.0                 # build_room sensor_fit='HORIZONTAL', 36 mm back

# The circle of confusion is DERIVED from the frame we actually deliver, not chosen:
# a feature is "sharp" when its blur disc is under CoC_PX pixels at the delivered
# resolution. Two pixels is the standard just-resolvable criterion and it is the one
# the sighted panel's laplacian probe effectively applied.
COC_PX = 2.0


# --------------------------------------------------------------------- projection --
def _basis(ex, ey, tx, ty):
    """Level camera basis. forward = aim direction in plan; image right = forward
    rotated -90 deg (build_room's to_track_quat('-Z','Y') with world up +Z)."""
    fx, fy = tx - ex, ty - ey
    n = math.hypot(fx, fy)
    if n < 1e-9:
        raise ValueError("camera aim coincides with the stand — no view direction")
    fx, fy = fx / n, fy / n
    return (fx, fy), (fy, -fx)


def project(pt_m, cam):
    """World point (x,y,z in METRES) -> (u, v, depth_m) in FRAME UNITS.

    u spans [-0.5, +0.5] across the image width; v spans [-aspect_h, +aspect_h] where
    aspect_h = 0.5 * height/width. depth is metres along the view axis (<=0 = behind
    the lens). Reproduces Blender's shift convention: a point's image coordinate is its
    angular term MINUS the shift, so positive shift_y puts more ceiling in frame.
    """
    ex, ey, eh = cam["ex"], cam["ey"], cam["eye_h"]
    (fx, fy), (rx, ry) = _basis(ex, ey, cam["tx"], cam["ty"])
    vx, vy, vz = pt_m[0] - ex, pt_m[1] - ey, pt_m[2] - eh
    depth = vx * fx + vy * fy
    if depth <= 1e-6:
        return None, None, depth
    k = cam["lens_mm"] / SENSOR_MM
    u = (vx * rx + vy * ry) / depth * k - cam.get("shift_x", 0.0)
    v = vz / depth * k - cam.get("shift_y", 0.0)
    return u, v, depth


def aspect_h(cam):
    """Half-height of the frame in the same units u is measured in."""
    return 0.5 * float(cam["res_h"]) / float(cam["res_w"])


def in_frame(pt_m, cam, margin=0.0):
    """Is the world point inside the rendered rectangle (margin in frame units)?"""
    u, v, d = project(pt_m, cam)
    if u is None:
        return False
    ah = aspect_h(cam)
    return (abs(u) <= 0.5 - margin) and (abs(v) <= ah - margin)


def to_px(pt_m, cam):
    """World point -> (px, py) in the delivered image, origin top-left. None if behind."""
    u, v, d = project(pt_m, cam)
    if u is None:
        return None
    W, H = float(cam["res_w"]), float(cam["res_h"])
    return ((u + 0.5) * W, (aspect_h(cam) - v) * W)


# --------------------------------------------------------------- depth of field ----
def dof_limits(lens_mm, fstop, focus_m, coc_mm):
    """(near_m, far_m) sharp limits. far = inf is returned as math.inf."""
    f = float(lens_mm)
    H = (f * f) / (float(fstop) * float(coc_mm)) + f          # hyperfocal, mm
    s = float(focus_m) * 1000.0
    near = s * (H - f) / (H + s - 2 * f)
    denom = H - s
    far = math.inf if denom <= 0 else s * (H - f) / denom
    return near / 1000.0, (far / 1000.0 if far != math.inf else math.inf)


def dof_from_geometry(lens_mm, near_subject_m, res_w, fstop_floor=2.8,
                      fstop_ceiling=22.0, margin=0.90):
    """Derive focus distance + aperture from WHAT IS IN THE ROOM, never typed.

    The relationship, written down: *the nearest mass a viewer can see must be sharp,
    and so must everything behind it.* Focus at the hyperfocal distance H = 2 * near
    puts the sharp zone at [near, infinity]; the aperture that produces that H is then
    a consequence of the lens and the delivered resolution, not a taste setting.

    Returns (fstop, focus_m, coc_mm, near_m, far_m, ok). ok=False means the required
    aperture is past `fstop_ceiling` — at which point the honest move is to turn DoF
    OFF rather than pretend, because a lens that cannot hold the room is a lie about
    the room, not a look.

    WHAT THIS OVERRULES, with the measurement (R7 refutation rules): the eye lane ran
    f/2.8 from `_e5.STORY_FSTOP`, adopted 2026-07-30 from a ground-truth study of pro
    scene files ("every pro scene camera measured f/1.4-2.4"). That study measured
    CAMERA DATABLOCKS IN OTHER PEOPLE'S FILES. The pool this studio is judged against
    (R4, the delivered anchors) is deep-focus in its PIXELS: an anchor's foreground
    bench book measures laplacian variance 1090 against 215 on its own far wall, while
    p2r77's nearest styled objects measure 5.7-18.9 against 104 in the pillow plane.
    A measurement of the delivered work outranks a measurement of the tools.
    """
    coc_mm = SENSOR_MM / float(res_w) * COC_PX
    near = float(near_subject_m) * float(margin)
    f = float(lens_mm)
    H = 2.0 * near * 1000.0
    denom = coc_mm * (H - f)
    if denom <= 0:
        return fstop_ceiling, near * 2.0, coc_mm, near, math.inf, False
    n = (f * f) / denom
    ok = True
    if n < fstop_floor:
        n = fstop_floor
    if n > fstop_ceiling:
        n, ok = fstop_ceiling, False
    focus_m = H / 1000.0
    nr, fr = dof_limits(f, n, focus_m, coc_mm)
    return n, focus_m, coc_mm, nr, fr, ok


# ------------------------------------------------------------------- room reading --
def _room_masses(spec):
    """Every mass the frame can contain, as (name, kind, x0,y0,x1,y1, z0,z1) in metres."""
    out = []
    for b in spec.get("builtins", []) or []:
        z0 = float(b.get("mount_mm", 0) or 0) * MM
        out.append((b.get("name") or "?", b.get("kind") or "builtin",
                    float(b["x"]) * MM, float(b["y"]) * MM,
                    (float(b["x"]) + float(b["w"])) * MM,
                    (float(b["y"]) + float(b["d"])) * MM,
                    z0, z0 + float(b.get("h", 0) or 0) * MM))
    for it in spec.get("items", []) or []:
        h = float(it.get("h") or 0) * MM
        out.append((it.get("name") or "?", it.get("kind") or "item",
                    float(it["x"]) * MM, float(it["y"]) * MM,
                    (float(it["x"]) + float(it["w"])) * MM,
                    (float(it["y"]) + float(it["d"])) * MM,
                    0.0, h))
    return out


def _ceiling_m(spec):
    return float((spec.get("room") or {}).get("ceiling_mm") or 2800) * MM


def _u_span(cam, x0, y0, x1, y1, z0, z1):
    """Horizontal frame-unit span [umin, umax] of a mass's AABB, or None if wholly
    behind the lens. Used to keep every question about the frame restricted to what
    the frame CONTAINS — the first version of nearest_mass forgot this and answered
    with a wardrobe standing 1.7 m off to the side at u = 1.27, i.e. a mass no viewer
    of this frame will ever see. A reading taken outside the picture is not a reading
    about the picture."""
    us = []
    for X in (x0, x1):
        for Y in (y0, y1):
            for Z in (z0, z1):
                u, v, d = project((X, Y, Z), cam)
                if u is not None:
                    us.append(u)
    if not us:
        return None
    return min(us), max(us)


def in_frustum(cam, box):
    """Does this AABB overlap the rendered rectangle horizontally?"""
    sp = _u_span(cam, *box)
    return bool(sp and sp[1] >= -0.5 and sp[0] <= 0.5)


def nearest_mass(spec, cam, exclude_kinds=("rug",)):
    """The nearest IN-FRAME mass, with its distance along the view axis.

    This is the object whose FLOOR CONTACT must be in frame (or the room has no floor)
    and which must be inside the depth of field (or the nearest thing to the viewer is
    the blurriest thing in the picture — p2r77's exact defect)."""
    best = None
    (fx, fy), _ = _basis(cam["ex"], cam["ey"], cam["tx"], cam["ty"])
    for nm, kind, x0, y0, x1, y1, z0, z1 in _room_masses(spec):
        if kind in exclude_kinds:
            continue
        if not in_frustum(cam, (x0, y0, x1, y1, z0, z1)):
            continue
        cand = []
        for px in (x0, x1):
            for py in (y0, y1):
                d = (px - cam["ex"]) * fx + (py - cam["ey"]) * fy
                # only corners that are themselves inside the frame's width
                u, _v, _d = project((px, py, 0.0), cam)
                if u is not None and abs(u) <= 0.5:
                    cand.append((d, px, py))
        cand = [c for c in cand if c[0] > 0.05]
        if not cand:
            continue
        d, px, py = min(cand)
        if best is None or d < best[0]:
            best = (d, nm, kind, px, py)
    return best


def back_wall_junction(spec, cam):
    """The (x,y,z) of the wall/ceiling junction ON THE AIM AXIS behind the subject —
    the architectural closure whose absence made the panel read the frame as a backdrop.
    Derived from the aim direction and the room outline, never typed."""
    (fx, fy), _ = _basis(cam["ex"], cam["ey"], cam["tx"], cam["ty"])
    ol = [(float(x) * MM, float(y) * MM)
          for x, y in ((spec.get("room") or {}).get("outline_mm") or [])]
    if not ol:
        return None
    # march along the aim ray to the outline boundary
    t, step = 0.0, 0.01
    ex, ey = cam["ex"], cam["ey"]
    last = (ex, ey)
    while t < 60.0:
        t += step
        px, py = ex + fx * t, ey + fy * t
        if not _inside_poly(px, py, ol):
            break
        last = (px, py)
    return (last[0], last[1], _ceiling_m(spec))


def top_edge_constraint(spec, cam):
    """The HIGHEST thing the frame must contain, as (v, label, point).

    Not only the wall/ceiling junction: a full-height feature wall standing PROUD of
    that wall projects higher than it does, and on this plan it is the one the sighted
    panel named ("the backlit top edge of the slats is this wall's best moment and it
    is currently amputated"). Taking the max over the junction and every in-frame
    full-height mass's top means the constraint follows whatever the room actually
    puts up there, instead of a number chosen once for one layout."""
    best = None
    j = back_wall_junction(spec, cam)
    if j:
        _u, v, _d = project(j, cam)
        if v is not None:
            best = (v, "wall/ceiling junction on the aim axis", j)
    ceil = _ceiling_m(spec)
    for nm, kind, x0, y0, x1, y1, z0, z1 in _room_masses(spec):
        if z1 < ceil - 0.15:            # not a full-height element
            continue
        if not in_frustum(cam, (x0, y0, x1, y1, z0, z1)):
            continue
        for X in (x0, x1):
            for Y in (y0, y1):
                u, v, d = project((X, Y, z1), cam)
                if u is None or abs(u) > 0.5 or v is None:
                    continue
                if best is None or v > best[0]:
                    best = (v, f"top of {nm}", (X, Y, z1))
    return best


def _inside_poly(px, py, poly):
    hit = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (x2 - x1) * (py - y1) / (y2 - y1):
            hit = not hit
    return hit


def mass_frame_share(spec, cam, kinds, samples=160):
    """Fraction of the RENDERED RECTANGLE covered by the given kinds' bounding boxes.

    Deterministic and honest about its scope: it rasterises each mass's AABB (8 corners
    -> convex hull in frame units) with a uniform sample grid over the image, so it
    OVER-counts an L-shaped or open-framed object and does not model occlusion. It is
    the frame-share proxy the camera-of-record note already needed and never had:
    D-118 adopted the bed-hero camera citing a two-mode reading of delivered work
    ("bed-as-subject: sleep surface <= 0.3 of frame"), and then nothing in this repo
    could measure that number on our own frame."""
    boxes = []
    for nm, kind, x0, y0, x1, y1, z0, z1 in _room_masses(spec):
        if kind not in kinds:
            continue
        pts = []
        for X in (x0, x1):
            for Y in (y0, y1):
                for Z in (z0, z1):
                    u, v, d = project((X, Y, Z), cam)
                    if u is None:
                        continue
                    pts.append((u, v))
        if len(pts) >= 3:
            boxes.append((min(p[0] for p in pts), min(p[1] for p in pts),
                          max(p[0] for p in pts), max(p[1] for p in pts)))
    if not boxes:
        return 0.0
    ah = aspect_h(cam)
    hit = 0
    total = 0
    for i in range(samples):
        u = -0.5 + (i + 0.5) / samples
        for j in range(int(samples * 2 * ah)):
            v = -ah + (j + 0.5) / samples
            total += 1
            if any(b[0] <= u <= b[2] and b[1] <= v <= b[3] for b in boxes):
                hit += 1
    return hit / total if total else 0.0


# ---------------------------------------------------------------------- the solve --
def framing_report(spec, cam, margin=0.02):
    """Everything the panel measured in pixels, decided from geometry before a render."""
    ah = aspect_h(cam)
    rep = {"cam": dict(cam), "aspect_h": ah}

    top = top_edge_constraint(spec, cam)
    if top:
        v, label, pt = top
        rep["top_edge"] = {
            "what": label, "point_m": [round(c, 3) for c in pt], "v": round(v, 4),
            "v_max": round(ah, 4),
            "in_frame": bool(v <= ah - margin),
            "shortfall_v": round(v - (ah - margin), 4)}

    nm = nearest_mass(spec, cam)
    if nm:
        d, name, kind, px, py = nm
        u, v, _ = project((px, py, 0.0), cam)
        rep["nearest_mass"] = {
            "name": name, "kind": kind, "depth_m": round(d, 3),
            "floor_contact_v": None if v is None else round(v, 4),
            "v_min": round(-ah, 4),
            "floor_contact_in_frame": bool(v is not None and v >= -ah + margin),
            "shortfall_v": None if v is None else round((-ah + margin) - v, 4)}
        n, focus, coc, near, far, ok = dof_from_geometry(
            cam["lens_mm"], d, cam["res_w"])
        rep["dof"] = {"fstop": round(n, 2), "focus_m": round(focus, 3),
                      "coc_mm": round(coc, 4), "near_m": round(near, 3),
                      "far_m": (None if far == math.inf else round(far, 3)),
                      "nearest_mass_sharp": bool(near <= d), "reachable": ok}
        cur_f = cam.get("fstop")
        if cur_f:
            cn, cf = dof_limits(cam["lens_mm"], cur_f, cam.get("focus_m") or 3.78,
                                SENSOR_MM / float(cam["res_w"]) * COC_PX)
            rep["dof_current"] = {"fstop": cur_f, "near_m": round(cn, 3),
                                  "far_m": (None if cf == math.inf else round(cf, 3)),
                                  "nearest_mass_sharp": bool(cn <= d)}

    rep["share"] = {
        "bed_zone": round(mass_frame_share(spec, cam, {"bed", "bench"}), 4),
        "bed_only": round(mass_frame_share(spec, cam, {"bed"}), 4)}
    return rep


def solve_framing(spec, cam, stand_candidates_m=None, lens_candidates=None,
                  margin=0.02, eye_candidates_m=None):
    """Find (stand, lens, shift_y) that CONTAINS the two architectural facts.

    Constraints, in the language of the room rather than of the lens:
      (1) the wall/ceiling junction behind the subject is inside the frame
      (2) the nearest mass's floor contact is inside the frame
    Both are one-sided in v, so for a given stand+lens the admissible shift_y is an
    interval; the solve takes its midpoint (equal headroom top and bottom) and prefers
    the LONGEST lens that admits a solution — long lens = least foreshortening, which
    is the third thing the panel measured (a 2:1 convergence over the bed's own length).
    Returns the best candidate dict or None.
    """
    ah = aspect_h(cam)
    stands = stand_candidates_m or [cam["ex"]]
    lenses = lens_candidates or [cam["lens_mm"]]
    eyes = eye_candidates_m or [cam["eye_h"]]
    ranked = []
    for eh in eyes:
        for ex in stands:
            c0 = dict(cam, ex=ex, eye_h=eh)
            for L in sorted(lenses, reverse=True):
                c = dict(c0, lens_mm=L, shift_y=0.0)
                top = top_edge_constraint(spec, c)
                nmz = nearest_mass(spec, c)
                if not (top and nmz):
                    continue
                d_near, nname, nkind, npx, npy = nmz
                v_ceil = top[0]
                _, v_floor, _ = project((npx, npy, 0.0), c)
                if v_ceil is None or v_floor is None:
                    continue
                # v_ceil - shift <= ah - margin   ->  shift >= v_ceil - ah + margin
                # v_floor - shift >= -ah + margin ->  shift <= v_floor + ah - margin
                lo = v_ceil - ah + margin
                hi = v_floor + ah - margin
                if lo > hi:
                    continue
                shift = round((lo + hi) / 2.0, 4)
                cand = dict(c0, lens_mm=L, shift_y=shift)
                rep = framing_report(spec, cand, margin=margin)
                ranked.append({"ex": round(ex, 3), "eye_h": round(eh, 3),
                               "lens_mm": L, "shift_y": shift,
                               "headroom": round(hi - lo, 4),
                               "bed_share": rep["share"]["bed_only"],
                               "report": rep})
    if not ranked:
        return None
    # PREFERENCE ORDER, and each rank is a thing the panel measured rather than a
    # taste: (1) the LONGEST lens that admits a solution, because the frame's third
    # measured defect is a 2:1 convergence over the bed's own length and focal length
    # is the only knob that touches it; (2) the largest bed share, because the owner's
    # standing complaint about the earlier camera was that the bed read small
    # (D-118); (3) the eye height closest to the camera of record, because a camera he
    # approved should move as little as the constraints allow.
    eh0 = cam["eye_h"]
    ranked.sort(key=lambda r: (-r["lens_mm"], -r["bed_share"], abs(r["eye_h"] - eh0)))
    return ranked[0]


# ------------------------------------------------------------------------- CLI -----
def cam_from_spec(spec, res=(2400, 1800), eye_h=None):
    ov = spec.get("eye_camera") or {}
    if not ov.get("stand_mm"):
        raise SystemExit("frame_geometry: spec has no eye_camera.stand_mm "
                         "(auto-solve lives in camera_config.solve_eye_camera)")
    if eye_h is None:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import camera_config
            # the SPEC's height first — this reader must see the same lens the
            # renderer will build, or its containment answers are about a camera
            # nobody is going to use
            eye_h = camera_config.spec_eye_h_m(spec)
        except Exception:                                    # noqa: BLE001
            eye_h = 1.15
    aim = ov.get("aim_mm")
    if not aim:
        raise SystemExit("frame_geometry: this reader needs eye_camera.aim_mm")
    return {"ex": float(ov["stand_mm"][0]) * MM, "ey": float(ov["stand_mm"][1]) * MM,
            "tx": float(aim[0]) * MM, "ty": float(aim[1]) * MM,
            "eye_h": float(eye_h), "lens_mm": float(ov.get("lens_mm") or 26.0),
            "shift_y": float(ov.get("shift_y") if ov.get("shift_y") is not None
                             else -0.10),
            "res_w": res[0], "res_h": res[1]}


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec")
    ap.add_argument("--camera", default=None,
                    help="a name from the spec's eye_camera_variants, measured "
                         "instead of eye_camera. Same variant dict build_room's "
                         "--eyecam= uses, so there is ONE definition of a view.")
    ap.add_argument("--res", default="2400x1800")
    ap.add_argument("--fstop", type=float, default=None,
                    help="report the CURRENT aperture's limits beside the derived one")
    ap.add_argument("--solve", action="store_true",
                    help="search stand/lens/shift for a framing that contains the "
                         "ceiling junction and the nearest mass's floor contact")
    ap.add_argument("--stand-min-x", type=float, default=None,
                    help="metres; westmost legal standing x (clearance-checked outside)")
    ap.add_argument("--lenses", default="20,22,24,26,28")
    ap.add_argument("--eye-band", default="1.15,1.15",
                    help="lo,hi metres to search for the lens height "
                         "(camera_config.DESIGNER_BAND_M is 1.0,1.2)")
    a = ap.parse_args(argv)
    W, H = (int(v) for v in a.res.lower().split("x"))
    spec = json.load(open(a.spec, encoding="utf-8"))
    if a.camera:
        # FAIL LOUD ON AN UNKNOWN NAME, exactly as build_room's --eyecam= does
        # (build_room.py:12629): a typo'd view must never silently measure the hero
        # one and report it as the variant's numbers.
        _vars = spec.get("eye_camera_variants") or {}
        if a.camera not in _vars:
            print(f"frame_geometry: --camera={a.camera!r}: spec has no "
                  f"eye_camera_variants[{a.camera!r}] "
                  f"(known: {sorted(k for k in _vars if not k.startswith('_'))})",
                  file=sys.stderr)
            return 2
        spec = dict(spec, eye_camera=_vars[a.camera])
    cam = cam_from_spec(spec, res=(W, H))
    if a.fstop:
        cam["fstop"] = a.fstop
        cam["focus_m"] = math.hypot(cam["tx"] - cam["ex"], cam["ty"] - cam["ey"])
    print(json.dumps(framing_report(spec, cam), ensure_ascii=False, indent=1))
    if a.solve:
        lo = a.stand_min_x if a.stand_min_x is not None else cam["ex"]
        stands = [round(lo + i * 0.02, 3) for i in range(int((cam["ex"] - lo) / 0.02) + 1)]
        lenses = [float(x) for x in a.lenses.split(",")]
        eyes = [round(v, 3) for v in _frange(a.eye_band)]
        best = solve_framing(spec, cam, stands, lenses, eye_candidates_m=eyes)
        print("\nSOLVE:")
        print(json.dumps(best, ensure_ascii=False, indent=1))
    return 0


def _frange(band):
    lo, hi = (float(v) for v in str(band).split(","))
    n = max(1, int(round((hi - lo) / 0.05)))
    return [lo + i * 0.05 for i in range(n + 1)]

def behind_camera(spec, cam, min_area_m2=0.5):
    """Masses standing BEHIND the eye, and the wall area they present to the room.

    WHY THIS IS A READING AND NOT A CURIOSITY (2026-08-28, from a studio's own workflow at
    06:45-07:00 of the 3D Shaker interior tutorial): *"when modelling walls don't overlook
    the walls behind the camera — although they are not visible in your image they still
    impact the lighting in your scene because they reflect a lot of light."*

    Every rung in this lane restricts itself to what the frame CONTAINS — `_u_span` says so
    in its own docstring, and it is right about geometry. But the light in the frame comes
    from surfaces the frame does not contain, so a room that is open behind the eye renders
    a picture whose fill has nowhere to come from. That is the R10 question ("every bright
    thing needs a source") asked about the half of the room no rung has ever looked at.

    Returns {'behind': [...], 'area_m2': float, 'open': bool}. `open` is True when the
    total facing area behind the eye is under `min_area_m2` — i.e. there is effectively
    nothing back there to bounce off. It is REPORTED, never a cut: a camera standing in a
    doorway legitimately has little behind it, and this rung cannot tell that from a
    missing wall. It says what is there; the eye says whether that is right.

    WHAT IT DOES NOT SEE, AND THE NAME WOULD OTHERWISE HIDE IT. `_room_masses` reads
    `spec["builtins"]` and `spec["items"]` — the room SHELL is not among them, because the
    walls come from `room.outline` and are materialised in the Blender layer. So this
    function measures the FURNITURE AND JOINERY behind the eye, never the wall the quote
    above is actually about. Run on the canonical master-suite spec it returns 5.6 m2 from
    two pieces (the west bookshelf at 0.33 m and the BF11 dressing table at 0.44 m) and
    `open=False` — a "the room is closed behind you" answer carried entirely by cabinets.
    Read it that way: a LOW number here means the fill light has little near-field furniture
    to bounce off, and it says nothing at all about whether a wall was built. Whether the
    shell behind the camera exists and carries a material is a question for the built
    scene, not for a pure spec reader, and it is not answered anywhere yet.
    """
    (fx, fy), _right = _basis(cam["ex"], cam["ey"], cam["tx"], cam["ty"])
    ex, ey = cam["ex"], cam["ey"]
    out = []
    for name, kind, x0, y0, x1, y1, z0, z1 in _room_masses(spec):
        # A mass is behind the eye when EVERY corner of its footprint has a negative
        # forward coordinate. Straddling masses (the side walls) are not behind.
        corners = ((x0, y0), (x1, y0), (x0, y1), (x1, y1))
        fwd = [((cx - ex) * fx + (cy - ey) * fy) for cx, cy in corners]
        if max(fwd) >= 0:
            continue
        # The area it presents back into the room: its footprint's extent across the view
        # axis times its height. An AABB is coarse and that is acknowledged — this is a
        # presence check, not a radiosity solve.
        across = [(-(cx - ex) * fy + (cy - ey) * fx) for cx, cy in corners]
        width = max(across) - min(across)
        height = max(0.0, z1 - z0)
        out.append({"name": name, "kind": kind, "distance_m": -max(fwd),
                    "facing_area_m2": width * height})
    area = sum(r["facing_area_m2"] for r in out)
    return {"behind": sorted(out, key=lambda r: -r["facing_area_m2"]),
            "area_m2": area, "open": area < min_area_m2}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
