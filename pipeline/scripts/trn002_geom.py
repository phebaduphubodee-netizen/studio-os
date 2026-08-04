"""trn002_geom.py — TRN-002 camera/space math. PURE python (no bpy).

TRN-001's geometry module carried the unit's whole parametric model; this one
is deliberately thinner: the spec carries explicit masses and landmark points,
and this module owns only the mm<->pixel math for a LANDSCAPE frame (TRN-001
was square, so its `res` scalar hid the fact that Blender ties focal AND both
shifts to the SENSOR-FIT dimension — the WIDTH here).

World frame (matches trn001 conventions so project() math carries over):
  back wall = plane y=0, room protrudes toward the camera in -y,
  wardrobe face = plane x=0, room extends in -x, z up from floor 0.
  Camera: pitch 0, +yaw pans right, fwd=(sin yaw, cos yaw, 0).

Camera dict: x_mm y_mm z_mm yaw_deg focal_mm shift_x shift_y  (+ the spec
carries "image": {"w":1080,"h":821}).

Projection (validated against Blender world_to_camera_view by the build's
dump rung before any conclusion rests on it):
  k = focal_mm / 36.0        f_px = W*k
  u = W*(0.5 + shift_x) + f_px * xc/depth
  v = H*0.5 + W*shift_y      - f_px * dz/depth
"""
import json
import math

SENSOR_MM = 36.0
MM = 0.001


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cam_basis(yaw_deg):
    yw = math.radians(yaw_deg)
    return ((math.sin(yw), math.cos(yw), 0.0),
            (math.cos(yw), -math.sin(yw), 0.0),
            (0.0, 0.0, 1.0))


def project(cam, pt, wh):
    W, H = wh
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    dx, dy, dz = pt[0] - cam["x_mm"], pt[1] - cam["y_mm"], pt[2] - cam["z_mm"]
    depth = dx * fwd[0] + dy * fwd[1]
    if depth <= 1.0:
        return None
    xc = dx * right[0] + dy * right[1]
    f_px = W * cam["focal_mm"] / SENSOR_MM
    u = W * (0.5 + cam.get("shift_x", 0.0)) + f_px * xc / depth
    v = H * 0.5 + W * cam.get("shift_y", 0.0) - f_px * dz / depth
    return (u, v)


def backproject(cam, uv, plane, wh):
    """Measured pixel + the PLANE it lies on -> world mm. plane=(axis, value).
    None when the ray is parallel or the hit is behind the camera. The plane-
    is-not-the-surface caveat carries over from TRN-001 verbatim: this answers
    where a ray meets an INFINITE plane and knows nothing about extent."""
    W, H = wh
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    f_px = W * cam["focal_mm"] / SENSOR_MM
    a = (uv[0] - W * (0.5 + cam.get("shift_x", 0.0))) / f_px
    b = (H * 0.5 + W * cam.get("shift_y", 0.0) - uv[1]) / f_px
    d = (fwd[0] + a * right[0], fwd[1] + a * right[1], b)
    c = (cam["x_mm"], cam["y_mm"], cam["z_mm"])
    i = "xyz".index(plane[0])
    if abs(d[i]) < 1e-12:
        return None
    t = (plane[1] - c[i]) / d[i]
    if t <= 0:
        return None
    return tuple(c[j] + t * d[j] for j in range(3))


def station_from_anchor(cam_pins, anchor_uv, anchor_xyz, z_mm, wh):
    """Closed-form station: with orientation+focal+shifts pinned and camera z
    DECLARED (door-hardware anchor), the ray through one measured pixel of one
    known 3D point fixes x and y exactly. Returns full camera dict.

    This is the round-1 bootstrap, not the final word: the reprojection table
    over every fitted line is what judges it, and a later LSQ polish may float
    what this pins. Raises if the anchor ray runs level (no z progress)."""
    W, H = wh
    cam = dict(cam_pins)
    cam.update({"x_mm": 0.0, "y_mm": 0.0, "z_mm": 0.0})
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    f_px = W * cam["focal_mm"] / SENSOR_MM
    a = (anchor_uv[0] - W * (0.5 + cam.get("shift_x", 0.0))) / f_px
    b = (H * 0.5 + W * cam.get("shift_y", 0.0) - anchor_uv[1]) / f_px
    d = (fwd[0] + a * right[0], fwd[1] + a * right[1], b)
    if abs(d[2]) < 1e-12:
        raise ValueError("anchor ray is level: cannot recover distance from z")
    t = (anchor_xyz[2] - z_mm) / d[2]
    if t <= 0:
        raise ValueError("anchor behind camera")
    cam["x_mm"] = anchor_xyz[0] - t * d[0]
    cam["y_mm"] = anchor_xyz[1] - t * d[1]
    cam["z_mm"] = float(z_mm)
    return cam


def project_landmarks(cam, spec):
    wh = (spec["image"]["w"], spec["image"]["h"])
    return {n: project(cam, p, wh) for n, p in spec["landmarks_3d"].items()}


def reprojection_table(spec, measured):
    """measured: {name: [u,v]}. Returns rows + summary over landmarks present
    in both the spec and the measurement file."""
    cam = spec["camera"]
    wh = (spec["image"]["w"], spec["image"]["h"])
    rows = []
    for name, uv in sorted(measured.items()):
        p = spec["landmarks_3d"].get(name)
        if p is None:
            continue
        pr = project(cam, p, wh)
        if pr is None:
            rows.append({"name": name, "err": None})
            continue
        du, dv = pr[0] - uv[0], pr[1] - uv[1]
        rows.append({"name": name, "du": round(du, 2), "dv": round(dv, 2),
                     "err": round(math.hypot(du, dv), 2)})
    errs = [r["err"] for r in rows if r["err"] is not None]
    summary = {"n": len(errs),
               "mean": round(sum(errs) / len(errs), 2) if errs else None,
               "max": round(max(errs), 2) if errs else None}
    return rows, summary
