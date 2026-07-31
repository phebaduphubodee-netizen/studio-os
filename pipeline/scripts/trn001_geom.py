"""trn001_geom.py — TRN-001 reproduction blockout: PURE geometry model, no bpy.

LAYER LAW (pipeline/CLAUDE.md): rules/spec/solve = pure python; only the
materializer (trn001_build.py, run inside Blender) imports bpy. This module is
the ONE source of truth for the blockout's masses and named landmark points —
the camera solver (plain python) and the Blender builder both import it, so the
solve and the render can never disagree about where a corner is.

Scene: generic prayer-room feature wall (reproduction study TRN-001,
qa/reproduction-curriculum.md — committed files carry the TRN-id and generic
descriptions only; the target mapping lives under _private/).

World frame: mm. Feature-wall FACE is the plane y=0 with the ROOM at y<0, so a
camera at negative y with Blender euler (90°, 0, -yaw) looks +Y at the wall and
world +x = frame right (checked against Blender's own world_to_camera_view by
the builder, which dumps its projections for the solver to cross-verify).
z up, floor z=0. yaw_deg positive = camera panned toward the RIGHT side of the
wall. Verticals stay vertical (pitch 0); framing height comes from shift_y.
"""
import json
import math

MM = 0.001  # mm -> Blender metres


# ---------------------------------------------------------------- masses ----

def _box(name, cx, cy, cz, sx, sy, sz, value, radii=None):
    """Axis-aligned mass. cx/cy/cz = CENTER (mm); sx/sy/sz = full size (mm).
    radii = optional plan-view corner radii (front-left, front-right, back-left,
    back-right; 'front' = room side, y<0) for an extruded rounded-rect.
    value = clay grey so masses separate in the LOOK overlay."""
    return {"name": name, "c": (cx, cy, cz), "s": (sx, sy, sz),
            "value": value, "radii": radii or (0.0, 0.0, 0.0, 0.0)}


def masses(spec):
    """Spec dict -> list of mass dicts. Every dimension read here is mm.
    Room sits at y<0; positive spec depths are applied toward the room."""
    u = spec["unit"]
    room = spec["room"]
    out = []

    ceil = room["ceiling_mm"]
    wall_len = room["back_wall_len_mm"]
    wall_off = room.get("unit_center_offset_mm", 0.0)  # unit centre vs wall centre
    depth = room["room_depth_mm"]

    # room shell (floor, back wall, ceiling, left side wall at frame-left = -x)
    out.append(_box("floor", -wall_off, -depth / 2, -50, wall_len, depth, 100, 0.65))
    out.append(_box("back_wall", -wall_off, +50, ceil / 2, wall_len, 100, ceil, 0.80))
    out.append(_box("ceiling", -wall_off, -depth / 2, ceil + 50, wall_len, depth, 100, 0.82))
    lx = -wall_off - wall_len / 2
    out.append(_box("side_wall_L", lx - 50, -depth / 2, ceil / 2, 100, depth, ceil, 0.80))

    # header band across the top; its brass trim lines are a later round
    h = u["header"]
    hcx = h.get("cx_mm", 0.0)
    out.append(_box("header", hcx, -h["depth_mm"] / 2, h["top_z_mm"] - h["band_h_mm"] / 2,
                    h["len_mm"], h["depth_mm"], h["band_h_mm"], 0.45))

    # towers (-> header underside); the LEFT tower stands on the plinth when
    # the spec says so (target reads asymmetric), the right on the floor
    t = u["tower"]
    tz = h["top_z_mm"] - h["band_h_mm"]
    for side, sgn in (("L", -1), ("R", 1)):
        z0t = u["plinth"]["h_mm"] if (side == "L" and t.get("left_on_plinth")) else 0.0
        cx = hcx + sgn * (h["len_mm"] / 2 - t["w_mm"] / 2)
        out.append(_box(f"tower_{side}", cx, -t["d_mm"] / 2, (tz + z0t) / 2,
                        t["w_mm"], t["d_mm"], tz - z0t, 0.28))

    # backlit slab, proud of the wall
    m = u["marble"]
    out.append(_box("marble", m.get("cx_mm", 0.0), -m["proud_mm"] / 2,
                    m["bot_z_mm"] + m["h_mm"] / 2,
                    m["w_mm"], m["proud_mm"], m["h_mm"], 0.75))

    # white drawer plinth with rounded front corners; cx_mm because the target
    # reads ASYMMETRIC (plinth runs on under the left tower to the unit's outer
    # edge; the left tower stands ON it while the right tower stands on floor)
    p = u["plinth"]
    out.append(_box("plinth", p.get("cx_mm", 0.0), -p["d_mm"] / 2, p["h_mm"] / 2,
                    p["len_mm"], p["d_mm"], p["h_mm"], 0.85,
                    radii=(p["r_mm"], p["r_mm"], 0, 0)))

    # altar stack: wide step -> centre box -> side pedestals (all on plinth top)
    s = u["step"]
    out.append(_box("step", s.get("cx_mm", 0.0), -s["d_mm"] / 2,
                    p["h_mm"] + s["h_mm"] / 2,
                    s["len_mm"], s["d_mm"], s["h_mm"], 0.58,
                    radii=(s["r_mm"], s["r_mm"], 0, 0)))
    b = u["box"]
    z0 = p["h_mm"] + s["h_mm"]
    out.append(_box("centre_box", b.get("cx_mm", 0.0), -b["d_mm"] / 2,
                    z0 + b["h_mm"] / 2,
                    b["w_mm"], b["d_mm"], b["h_mm"], 0.40,
                    radii=(b["r_mm"], b["r_mm"], 0, 0)))
    q = u["pedestal"]
    for side, sgn in (("L", -1), ("R", 1)):
        out.append(_box(f"pedestal_{side}", sgn * q["cx_mm"], -q["d_mm"] / 2,
                        z0 + q["h_mm"] / 2, q["w_mm"], q["d_mm"], q["h_mm"], 0.48,
                        radii=(q["r_mm"], q["r_mm"], 0, 0)))
    return out


# ------------------------------------------------------------- landmarks ----

def landmarks_3d(spec):
    """Named fixed 3D points (mm) used by the camera solve. Only true corners —
    occlusion-dependent points (marble_*_low, tower bases) are LOOK-only and
    deliberately absent. Front faces sit at negative y.

    SILHOUETTE CONVENTION for rounded-corner masses (matches what the numeric
    measurers could actually probe in the target): the left/right extreme of a
    rounded end is the arc's outermost 3D extent (x = ±L/2 at y = -(d - r)),
    NOT the rounding-onset point — from an oblique camera the silhouette
    tangent sits within ~r of that, far closer than the onset corner.
    header_bot_* is the visible JUNCTION of the tower inner-front edge with the
    header underside, which lives on the TOWER front plane (header is deeper)."""
    u = spec["unit"]
    h, t, m = u["header"], u["tower"], u["marble"]
    p, s, b = u["plinth"], u["step"], u["box"]
    zb = h["top_z_mm"] - h["band_h_mm"]
    hcx = h.get("cx_mm", 0.0)
    x_in = h["len_mm"] / 2 - t["w_mm"]          # tower inner face offset from hcx
    z0 = p["h_mm"] + s["h_mm"]
    pcx, scx = p.get("cx_mm", 0.0), s.get("cx_mm", 0.0)
    bcx, mcx = b.get("cx_mm", 0.0), m.get("cx_mm", 0.0)
    return {
        "header_top_left":  (hcx - h["len_mm"] / 2, -h["depth_mm"], h["top_z_mm"]),
        "header_top_right": (hcx + h["len_mm"] / 2, -h["depth_mm"], h["top_z_mm"]),
        "header_bot_left":  (hcx - x_in, -t["d_mm"], zb),
        "header_bot_right": (hcx + x_in, -t["d_mm"], zb),
        "marble_top_left":  (mcx - m["w_mm"] / 2, -m["proud_mm"], m["bot_z_mm"] + m["h_mm"]),
        "marble_top_right": (mcx + m["w_mm"] / 2, -m["proud_mm"], m["bot_z_mm"] + m["h_mm"]),
        "plinth_top_left":  (pcx - p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), p["h_mm"]),
        "plinth_top_right": (pcx + p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), p["h_mm"]),
        "plinth_bot_left":  (pcx - p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), 0.0),
        "plinth_bot_right": (pcx + p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), 0.0),
        "box_top_left":     (bcx - b["w_mm"] / 2, -(b["d_mm"] - b["r_mm"]), z0 + b["h_mm"]),
        "box_top_right":    (bcx + b["w_mm"] / 2, -(b["d_mm"] - b["r_mm"]), z0 + b["h_mm"]),
        "step_top_left":    (scx - s["len_mm"] / 2, -(s["d_mm"] - s["r_mm"]), p["h_mm"] + s["h_mm"]),
        "step_top_right":   (scx + s["len_mm"] / 2, -(s["d_mm"] - s["r_mm"]), p["h_mm"] + s["h_mm"]),
    }


# ------------------------------------------------------------ projection ----

SENSOR_MM = 36.0  # full-frame width, horizontal fit; square render shares it


def cam_basis(yaw_deg):
    """forward/right/up world vectors for pitch-0 camera, +yaw = pan right."""
    yw = math.radians(yaw_deg)
    fwd = (math.sin(yw), math.cos(yw), 0.0)
    right = (math.cos(yw), -math.sin(yw), 0.0)
    return fwd, right, (0.0, 0.0, 1.0)


def project(cam, pt, res=2048):
    """Pinhole projection matching the builder's Blender camera
    (euler XYZ = (90°, 0, -yaw), shift-framed). Returns (u_px, v_px), origin
    top-left, v down. Sign conventions are cross-verified against Blender's
    world_to_camera_view dump on every build (trn001_build writes both)."""
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    dx, dy, dz = (pt[0] - cam["x_mm"], pt[1] - cam["y_mm"], pt[2] - cam["z_mm"])
    depth = dx * fwd[0] + dy * fwd[1]
    if depth <= 1.0:
        return None
    xc = dx * right[0] + dy * right[1]
    k = cam["focal_mm"] / SENSOR_MM
    u = res * (0.5 + k * xc / depth + cam.get("shift_x", 0.0))
    v = res * (0.5 - k * dz / depth + cam.get("shift_y", 0.0))
    return (u, v)


def project_all(cam, spec, res=2048):
    return {n: project(cam, p, res) for n, p in landmarks_3d(spec).items()}


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
