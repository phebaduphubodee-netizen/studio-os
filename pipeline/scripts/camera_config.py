#!/usr/bin/env python3
"""camera_config.py — interior eye-camera height as a cited, testable constant.

The suite eye-camera height was a bare literal `1.5` m inside build_room.py
(add_suite_eye_camera), COUPLED to a second bare literal `1.55` m — the height at/
above which a built-in blocks the LEVEL line-of-sight ray used to pick a standing
spot. Those two must move together: an object blocks a level ray at eye height H iff
it is taller than ~H. Hardcoding them independently is a latent bug — change one and
the LOS solve silently mismatches the actual camera height.

M3.2 designer calibration (2026-07-03, golden-set GS-15 note): a practicing designer
rejected the renders' camera as "too high — ฝ้าเพดานดูเตี้ย; ผมใช้ความสูงมุมกล้อง
ประมาณ 1.0–1.2 ม." So the default drops 1.5 -> 1.15 m (band midpoint) and the ray
threshold follows it (1.55 -> ~1.20).

stdlib-only + importable ON PURPOSE: build_room.py imports bpy at module top and is
NOT importable for a unit test; this tiny module is, so the height + its coupling are
pinned by test_camera_config.py.

A/B for a paid batch:
    EYE_CAM_HEIGHT_M=1.5 blender -b --python build_room.py -- spec.json   # old height
AESTHETIC confirmation is a DESIGNER render A/B, NOT the LLM judge — M3.2 proved the
judge decalibrated (too lenient vs a designer's eye); see qa/reports/
judge-calibration-2026-07-03-designer-notes.md. This module only encodes the
designer's stated value + guarantees the LOS threshold stays coupled.
"""
import os

DEFAULT_EYE_CAM_HEIGHT_M = 1.15        # designer 1.0–1.2 m (M3.2 GS-15); was 1.5
DESIGNER_BAND_M = (1.0, 1.2)
RAY_BLOCK_MARGIN_M = 0.05              # a built-in blocks the level ray if taller than
                                       # eye + margin (the old 1.55 = 1.5 eye + 0.05)

# --------------------------------------------------------------- DELIVERABLE RES --
# DELIV-001 P1a. It lives beside the eye camera and not in the renderer because with
# sensor_fit='HORIZONTAL' the ASPECT RATIO IS A FRAMING PARAMETER: horizontal FOV is
# pinned by the lens, so changing h/w changes how much ceiling and floor the eye
# camera sees. A resolution edited in the render call is a silent recompose.
#
# BOTH NUMBERS ARE READ OFF THE 658 DELIVERED FRAMES, not chosen (census
# 2026-08-09, re-read 2026-08-10 for size because the census stores mp only):
#     median mp                4.194      -> 2400x1800 = 4.320 MP
#     median aspect            1.250      -> 1.333 is inside the delivered spread
#                                            (p25 0.750 / p75 1.500; 60.3% landscape)
# The eye path rendered 2000x1400 = 2.800 MP, which cleared the D1 floor of 2.796 by
# 0.004 MP — a margin nobody chose and nothing was protecting. Hence the floor
# argument below: this constant is now COUPLED to the row it exists to satisfy, so a
# re-cut census that raises D1 fails the build instead of quietly producing a frame
# that cannot qualify.
DELIVERABLE_RES = (2400, 1800)


def deliverable_res(d1_floor_mp=None):
    """Full-fidelity resolution for the client-facing EYE frame.

    Pass the standard's D1 threshold and this REFUSES to hand back a resolution
    below it. Fail-closed on purpose: the failure mode it is built against is the
    quiet one — a frame rendered under the floor scores NOT-qualified for a reason
    that has nothing to do with the room.
    """
    w, h = DELIVERABLE_RES
    if d1_floor_mp is not None:
        mp = (w * h) / 1e6
        if mp < float(d1_floor_mp):
            raise ValueError(
                f"DELIVERABLE_RES {w}x{h} = {mp:.3f} MP is below the standard's D1 "
                f"floor of {float(d1_floor_mp):.3f} MP — raise the constant (and "
                f"re-look at the framing: the aspect is a camera parameter here)")
    return DELIVERABLE_RES


def eye_cam_height_m():
    """Resolved eye height: env override (for a render A/B) else the designer default."""
    try:
        return float(os.environ.get("EYE_CAM_HEIGHT_M", DEFAULT_EYE_CAM_HEIGHT_M))
    except (TypeError, ValueError):
        return DEFAULT_EYE_CAM_HEIGHT_M


def ray_block_min_h_m(eye_h=None):
    """Height at/above which a built-in blocks the LEVEL eye ray — coupled to eye
    height so the standing-spot LOS solve always matches where the lens actually is."""
    base = eye_cam_height_m() if eye_h is None else eye_h
    return base + RAY_BLOCK_MARGIN_M


# module-level resolved values build_room.py reads (per-invocation script, so
# reading env once at import is correct)
EYE_CAM_HEIGHT_M = eye_cam_height_m()
RAY_BLOCK_MIN_H_M = ray_block_min_h_m()


def select_aim_element(elements, aim):
    """Pick the element the --eye camera should frame for EYE_AIM=<substr> (see
    build_room.add_suite_eye_camera). Priority: EXACT kind, then EXACT name, then a
    substring of kind or name — so EYE_AIM=tv frames a wall 'tv' before a 'tv_console',
    not the first arbitrary match. `elements` is the search pool (items + builtins) in
    priority order. Returns the element, or None when `aim` is falsy (default camera
    behaviour). Raises ValueError when aim is set but nothing matches OR the match lacks
    a usable footprint (x/y/w/d) — build_room turns that into a loud SystemExit rather
    than a bare KeyError mid-render. Pure/importable, so it is unit-testable (build_room
    is not — it imports bpy)."""
    if not aim:
        return None
    aim = str(aim).strip().lower()
    if not aim:
        return None

    def kind(e):
        return str(e.get("kind") or "").lower()

    def name(e):
        return str(e.get("name") or "").lower()

    el = (next((e for e in elements if kind(e) == aim), None)
          or next((e for e in elements if name(e) == aim), None)
          or next((e for e in elements if aim in kind(e) or aim in name(e)), None))
    if el is None:
        raise ValueError(f"EYE_AIM={aim!r} matched no item/builtin by kind or name")
    for k in ("x", "y", "w", "d"):
        if el.get(k) is None:
            raise ValueError(f"EYE_AIM match {name(el) or kind(el) or '?'!r} lacks '{k}' "
                             f"— cannot aim the camera at it")
    return el


# ------------------------------------------------------------------------------
# eye-camera SOLVE — the pure-geometry half of build_room.add_suite_eye_camera,
# extracted so it has ONE definition shared by the materializer (which renders it)
# and placement_logic's "camera has a reason" gate (which validates it BEFORE the
# paid render). build_room is not importable (imports bpy); this is, so the solve is
# unit-testable and the gate can predict a render-time abort without launching Blender.
# Same doctrine that put select_aim_element + EYE_CAM_HEIGHT_M here — no split-brain.
# ------------------------------------------------------------------------------
MM = 0.001                    # millimetres -> metres (room-spec@0.2 is metric); == build_room.MM
_LENS_SNAP = (26.0, 28.0, 35.0, 50.0)  # build_room v0.4.1 snap set (28/35/50 per render-quality §4 + 26 on gate evidence)
_STAND_BLOCK_MIN_H_M = 0.35   # an item taller than this blocks STANDING (build_room)
_H_SENSOR_HALF_MM = 18.0      # 36 mm horizontal sensor, half-width (build_room sensor_fit='HORIZONTAL')


class EyeCameraError(Exception):
    """The --eye camera cannot produce a valid shot for this spec (no loose subject to
    aim at, no clear standing spot with line of sight, or the standoff collapses onto the
    subject). Raised by solve_eye_camera so BOTH callers own the consequence: build_room
    turns it into a loud SystemExit (its render-abort convention); placement_logic turns
    it into a FUNCTION-gate FAIL that stops the paid render BEFORE Blender launches."""


def outline_m_of(spec):
    """Metric outline [(x_m, y_m), ...] from a room-spec@0.2, or None if absent."""
    ol = (spec.get("room") or {}).get("outline_mm")
    if not ol:
        return None
    return [(float(x) * MM, float(y) * MM) for x, y in ol]


def _box_m(e):
    """Axis-aligned furniture footprint (x0,y0,x1,y1) in metres from an mm element."""
    return (float(e["x"]) * MM, float(e["y"]) * MM,
            (float(e["x"]) + float(e["w"])) * MM, (float(e["y"]) + float(e["d"])) * MM)


def _inside_poly(px, py, outline_m):
    """Ray-cast point-in-polygon (handles L-shaped outlines). build_room parity."""
    n = len(outline_m)
    hit = False
    for i in range(n):
        x1, y1 = outline_m[i]
        x2, y2 = outline_m[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (x2 - x1) * (py - y1) / (y2 - y1):
            hit = not hit
    return hit


def _seg_hits_box(x0, y0, x1, y1, bb):
    """Liang-Barsky: does segment (x0,y0)->(x1,y1) intersect AABB bb? build_room parity."""
    bx0, by0, bx1, by1 = bb
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - bx0), (dx, bx1 - x0), (-dy, y0 - by0), (dy, by1 - y0)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            if t > t1:
                return False
            if t > t0:
                t0 = t
        else:
            if t < t0:
                return False
            if t < t1:
                t1 = t
    return True


def _build_obstacles(spec, outline_m, exclude_subroom=None):
    """The stand-vs-ray obstacle split, factored out so the AUTO grid solve and the MANUAL
    eye_camera override validate against the SAME geometry (no split-brain). Returns
    (stand_blocks, ray_blocks) as lists of (x0,y0,x1,y1) AABBs in metres.

    stand_blocks — a person cannot stand here: every sub-room, every built-in, and any loose
      item taller than _STAND_BLOCK_MIN_H_M (a bed blocks standing but, being low, NOT the
      level eye ray).
    ray_blocks — occludes the LEVEL eye ray at lens height: sub-rooms + only those built-ins
      whose rendered box actually SPANS the lens. build_room floats a built-in from z=mount_mm
      to mount_mm+h, so the box crosses the lens iff base <= EYE_CAM_HEIGHT_M <= top (coupled to
      RAY_BLOCK_MIN_H_M): a wall TV floated at 900 mm blocks a 1.15 m lens though h<threshold; a
      built-in floated wholly above eye level does not. Reduces to `h >= threshold` at mount 0.

    exclude_subroom (name substring, case-insensitive) — the ONE subroom the camera is standing
      INSIDE for an interior shot (eye_camera.in_subroom). A subroom is an opaque box to the MAIN
      room, so it is normally both a stand- and ray-block; to shoot a subroom's own interior the
      camera must be allowed to stand within it (element 4 ensuite). Only the focused subroom is
      dropped — every OTHER subroom + all built-ins still occlude, so the shot cannot see through
      a wall into a different zone."""
    stand_blocks, ray_blocks = [], []
    for sr in spec.get("subrooms", []):
        if exclude_subroom and str(exclude_subroom).lower() in str(sr.get("name", "")).lower():
            continue
        sx = [p[0] for p in sr["outline_mm"]]
        sy = [p[1] for p in sr["outline_mm"]]
        bb = (min(sx) * MM, min(sy) * MM, max(sx) * MM, max(sy) * MM)
        stand_blocks.append(bb)
        ray_blocks.append(bb)
    for b in spec.get("builtins", []):
        stand_blocks.append(_box_m(b))
        base = float(b.get("mount_mm", 0) or 0) * MM
        top = base + float(b.get("h", 0) or 0) * MM
        if base <= EYE_CAM_HEIGHT_M and top >= RAY_BLOCK_MIN_H_M:
            ray_blocks.append(_box_m(b))
    for it in spec.get("items", []):
        if it.get("kind") != "rug" and float(it.get("h", 400)) * MM >= _STAND_BLOCK_MIN_H_M:
            stand_blocks.append(_box_m(it))
    return stand_blocks, ray_blocks


def _spot_is_clear(ex, ey, tx, ty, outline_m, stand_blocks, ray_blocks):
    """True if a person may stand at (ex,ey) [metres] and see the aim point (tx,ty): the spot
    plus a 0.3 m cross around it is inside the room outline, it is >=0.3 m clear of every
    stand-block, and the level ray to 0.95x the target hits no ray-block. ONE definition shared
    by the auto grid search and the manual override, so a hand-set camera gets the exact same
    wall-clip / line-of-sight safety net as the solved one."""
    for ox, oy in ((0, 0), (0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)):
        if not _inside_poly(ex + ox, ey + oy, outline_m):
            return False
    if any(bx0 - 0.3 <= ex <= bx1 + 0.3 and by0 - 0.3 <= ey <= by1 + 0.3
           for bx0, by0, bx1, by1 in stand_blocks):
        return False
    gx, gy = ex + (tx - ex) * 0.95, ey + (ty - ey) * 0.95
    if any(_seg_hits_box(ex, ey, gx, gy, bb) for bb in ray_blocks):
        return False
    return True


def solve_eye_camera(spec, outline_m=None):
    """Solve the v0.3 eye-level suite camera from spec GEOMETRY ALONE (no bpy). Returns a
    dict {ex, ey, tx, ty, lens_mm, standoff_m, hero, main, n_clear, manual} in METRES; the
    caller builds the Blender camera/fill from it.

    A spec["eye_camera"] block (stand_mm required; aim_mm/aim + lens_mm optional) HAND-PLACES
    the camera and short-circuits the grid search — for L-shaped / multi-zone suites where the
    farthest-clear-spot heuristic frames a corner or a wall. The manual spot is still validated
    against the same obstacles (returns manual=True). See the MANUAL OVERRIDE block below.

    Reproduces build_room.add_suite_eye_camera EXACTLY: aim = EYE_AIM override else the
    largest NON-RUG loose item (the group-rug centre when the largest overall is a rug the
    hero touches); the stand-vs-ray obstacle split (a bed blocks standing but not the level
    eye ray, tall millwork/sub-rooms block both, coupled to RAY_BLOCK_MIN_H_M); a 0.4 m
    free-floor grid kept to spots with 0.3 m of air and a clear line of sight to 0.95x the
    target; the FARTHEST such spot; and the hero-sized lens snapped to {26,28,35,50} mm.

    Raises EyeCameraError for the three degenerate cases build_room already aborts on:
    no loose item, no clear standing spot with LOS, standoff < 0.5 m. Also surfaces
    select_aim_element's ValueError (bad EYE_AIM) as EyeCameraError."""
    loose = spec.get("items") or []
    if not loose:
        raise EyeCameraError("camera needs at least one loose item to aim at")
    if outline_m is None:
        outline_m = outline_m_of(spec)
    if not outline_m:
        raise EyeCameraError("camera needs a room.outline_mm to solve a standing spot")

    _area = lambda it: float(it["w"]) * float(it["d"])
    try:
        aim_el = select_aim_element(list(loose) + list(spec.get("builtins", [])),
                                    os.environ.get("EYE_AIM"))
    except ValueError as e:                     # bad EYE_AIM -> same abort as build_room
        raise EyeCameraError(str(e))

    def _touches(a, b):
        ax0, ay0 = float(a["x"]), float(a["y"])
        ax1, ay1 = ax0 + float(a["w"]), ay0 + float(a["d"])
        bx0, by0 = float(b["x"]), float(b["y"])
        bx1, by1 = bx0 + float(b["w"]), by0 + float(b["d"])
        return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1

    if aim_el is not None:
        hero = main = aim_el
    else:
        hero = max((it for it in loose if it.get("kind") != "rug"), key=_area,
                   default=max(loose, key=_area))
        main_all = max(loose, key=_area)
        main = main_all if (main_all.get("kind") == "rug" and _touches(main_all, hero)) else hero
    tx = (float(main["x"]) + float(main["w"]) / 2.0) * MM
    ty = (float(main["y"]) + float(main["d"]) / 2.0) * MM

    stand_blocks, ray_blocks = _build_obstacles(
        spec, outline_m, (spec.get("eye_camera") or {}).get("in_subroom"))

    # ---- MANUAL OVERRIDE: spec["eye_camera"] places the standing spot by hand -----------
    # The auto solve below takes the FARTHEST clear grid spot — great for a plain box, but for
    # an L-shaped / multi-zone suite that heuristic can back the lens into a far corner behind
    # a full-height feature wall or wardrobe bay (bedroom_suite v4: auto stands SW, grazing the
    # wardrobe that spans the room, and reads the bed small & cluttered). A designer sets the
    # shot by hand:
    #   "eye_camera": {"stand_mm": [x, y],            # REQUIRED — activates the override
    #                  "aim_mm": [x, y] | "aim": "<kind/name substr>",   # default = auto subject centre
    #                  "lens_mm": <focal length>,     # default = auto hero-sized snap
    #                  "shift_y": <vertical lens shift>}  # default = build_room RENDER_SHIFT_Y (-0.10);
    #                                                     # more negative frames DOWN (kills empty upper wall)
    # The hand-set spot is validated by the SAME _spot_is_clear (outline + wall-clip + line of
    # sight) as the auto grid, so a bad manual camera aborts as loudly as a packed auto solve —
    # "manual" means you PLACE the camera, not that you skip the safety net. hero/main (for lens
    # sizing, DoF focus and the gate's "camera has a reason") stay the auto subject unless "aim"
    # names a different element.
    ov = spec.get("eye_camera") or {}
    manual = ov.get("stand_mm")
    if manual:
        ex, ey = float(manual[0]) * MM, float(manual[1]) * MM
        if ov.get("aim_mm"):
            tx, ty = float(ov["aim_mm"][0]) * MM, float(ov["aim_mm"][1]) * MM
        elif ov.get("aim"):
            try:
                ae = select_aim_element(list(loose) + list(spec.get("builtins", [])), ov["aim"])
            except ValueError as e:
                raise EyeCameraError(str(e))
            hero = main = ae
            tx = (float(ae["x"]) + float(ae["w"]) / 2.0) * MM
            ty = (float(ae["y"]) + float(ae["d"]) / 2.0) * MM
        if not _spot_is_clear(ex, ey, tx, ty, outline_m, stand_blocks, ray_blocks):
            raise EyeCameraError(
                f"manual eye_camera.stand_mm {list(manual)} is not a clear standing spot with a "
                f"line of sight to the aim — it lands outside the outline / within 0.3 m of a "
                f"built-in, or a mass blocks the view; move the spot or re-aim")
        standoff = ((ex - tx) ** 2 + (ey - ty) ** 2) ** 0.5
        if standoff < 0.5:
            raise EyeCameraError(f"manual eye_camera: standoff {standoff:.2f} m < 0.5 m — camera on top of the subject")
        if ov.get("lens_mm") is not None:
            lens = float(ov["lens_mm"])
            if lens <= 0:
                raise EyeCameraError(f"manual eye_camera.lens_mm {lens} must be > 0")
        else:
            subj_dim = max(float(hero["w"]), float(hero["d"])) * MM
            lens = min(_LENS_SNAP, key=lambda f: abs(f - 36.0 * standoff / max(2.0 * subj_dim, 3.5)))
        shift_y = float(ov["shift_y"]) if ov.get("shift_y") is not None else None
        return {"ex": ex, "ey": ey, "tx": tx, "ty": ty, "lens_mm": lens, "shift_y": shift_y,
                "standoff_m": standoff, "hero": hero, "main": main, "n_clear": 1, "manual": True}

    # ---- AUTO: farthest clear grid spot with a line of sight ----------------------------
    xs = [p[0] for p in outline_m]
    ys = [p[1] for p in outline_m]
    cands = [(gx, gy)
             for gx in [min(xs) + 0.4 + i * 0.4 for i in range(int((max(xs) - min(xs)) / 0.4))]
             for gy in [min(ys) + 0.4 + j * 0.4 for j in range(int((max(ys) - min(ys)) / 0.4))]
             if _spot_is_clear(gx, gy, tx, ty, outline_m, stand_blocks, ray_blocks)]
    if not cands:
        raise EyeCameraError("camera: no clear standing spot with line of sight to the "
                             "subject — room too packed for an eye shot; adjust the spec")
    ex, ey = max(cands, key=lambda c: (c[0] - tx) ** 2 + (c[1] - ty) ** 2)

    standoff = ((ex - tx) ** 2 + (ey - ty) ** 2) ** 0.5
    if standoff < 0.5:
        raise EyeCameraError(f"camera: no standing spot with line of sight "
                             f"(standoff {standoff:.2f} m) — room too packed for an eye shot")

    subj_dim = max(float(hero["w"]), float(hero["d"])) * MM
    req_w = max(2.0 * subj_dim, 3.5)            # frame width wanted at the subject (m)
    raw = 36.0 * standoff / req_w               # 36 mm-sensor pinhole approximation
    lens = min(_LENS_SNAP, key=lambda f: abs(f - raw))
    return {"ex": ex, "ey": ey, "tx": tx, "ty": ty, "lens_mm": lens,
            "standoff_m": standoff, "hero": hero, "main": main, "n_clear": len(cands), "manual": False}


def frame_subject_share(spec, solve, outline_m=None, n_rays=41):
    """Fraction of the eye-camera's HORIZONTAL field-of-view DIRECTIONS (bearings) that land
    on a real subject (loose non-rug furniture + built-ins) rather than bare outline wall /
    void — a deterministic "does this shot actually show the room" proxy for the dead-wall
    check (GS-04/05/22). Casts n_rays level rays evenly across the FOV from the solved standing
    spot and counts how many strike a furniture footprint.

    HONEST SCOPE (advisory WARN only, never a statutory measure): this is bearing-coverage,
    NOT framed image AREA (evenly-spaced angles, not pixel share), it has no vertical extent
    (level rays, ignores shift_y framing), and it does NOT model occlusion — a subject behind
    a wall or another mass on the same bearing is still counted. Good enough to separate a
    furniture-filled hero shot from a frame aimed at a bare wall; not a photometric metric.
    0.0 = every bearing misses all furniture (a dead frame)."""
    import math
    ex, ey = solve["ex"], solve["ey"]
    tx, ty = solve["tx"], solve["ty"]
    vdx, vdy = tx - ex, ty - ey
    if math.hypot(vdx, vdy) < 1e-9:
        return 0.0
    va = math.atan2(vdy, vdx)
    hfov = 2.0 * math.atan2(_H_SENSOR_HALF_MM, float(solve["lens_mm"]))
    subs = [_box_m(e) for e in spec.get("items", []) if e.get("kind") != "rug"]
    subs += [_box_m(e) for e in spec.get("builtins", [])]
    if not subs:
        return 0.0
    if outline_m is None:
        outline_m = outline_m_of(spec) or [(ex, ey)]
    xs = [p[0] for p in outline_m]
    ys = [p[1] for p in outline_m]
    reach = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) + 1.0   # room diagonal; subjects are inside
    hit = 0
    for i in range(n_rays):
        frac = 0.0 if n_rays == 1 else (i / (n_rays - 1) - 0.5)
        a = va + frac * hfov
        gx, gy = ex + reach * math.cos(a), ey + reach * math.sin(a)
        if any(_seg_hits_box(ex, ey, gx, gy, bb) for bb in subs):
            hit += 1
    return hit / n_rays
