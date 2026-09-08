#!/usr/bin/env python3
"""camera_solve.py - the fSpy step, done as arithmetic instead of a GUI.

fSpy (2 vanishing points) does exactly this:
  * two image lines per horizontal axis -> two vanishing points Fu, Fv
  * principal point P (default: image midpoint)
  * f = sqrt(-(Fu-P).(Fv-P))            [orthogonality of the two axes]
  * camera basis from the two vanishing directions
  * position from ONE known real length on a segment in the image

This photo is a magazine architectural frame: its verticals are vertical, which is the
signature of a shift lens or a perspective correction, so the camera is LEVEL and the
horizon is a horizontal line. That constraint is used here instead of a third vanishing
point - it lets both vanishing points be fitted on a shared horizon, which is far better
conditioned than intersecting two nearly-parallel lines (my first eyeball pass put the
horizon on the wrong side of the frame twice, by exactly that route).

The principal point of a shifted/corrected frame is NOT the image midpoint vertically:
it sits ON the horizon. Horizontally it is taken as the midpoint (no horizontal shift).
"""
import json
import math

import numpy as np


def horizon_and_vps(fam_a, fam_b):
    """fam_a, fam_b: lists of (m, b) image lines, y = m*x + b, for two perpendicular
    horizontal world axes. Returns (h, ua, ub) minimising squared vertical distance
    from each line to its family's vanishing point, with both VPs on the horizon y=h.

    Unknowns h, ua, ub. Each line i in family A gives residual  m_i*ua + b_i - h = 0.
    Linear least squares.
    """
    rows, rhs = [], []
    for m, b in fam_a:
        rows.append([m, 0.0, -1.0]); rhs.append(-b)
    for m, b in fam_b:
        rows.append([0.0, m, -1.0]); rhs.append(-b)
    A = np.array(rows); y = np.array(rhs)
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    ua, ub, h = [float(v) for v in sol]
    resid = A @ sol - y
    return h, ua, ub, float(np.sqrt(np.mean(resid ** 2)))


def focal(ua, ub, px):
    """f in pixels. Requires px strictly between the two vanishing points."""
    d = -(ua - px) * (ub - px)
    if d <= 0:
        raise ValueError(f"principal point {px} is not between vanishing points "
                         f"{ua:.0f} and {ub:.0f}: the two axes cannot be perpendicular")
    return math.sqrt(d)


def axis_dirs(ua, ub, px, py, f):
    """World axis directions expressed in CAMERA coordinates (x right, y up, -z fwd)."""
    def d(u):
        v = np.array([u - px, 0.0, -f])       # level camera: vanishing point on horizon
        return v / np.linalg.norm(v)
    return d(ua), d(ub)


def solve(W, H, fam_a, fam_b, px=None):
    h, ua, ub, rms = horizon_and_vps(fam_a, fam_b)
    px = W / 2.0 if px is None else px
    f = focal(ua, ub, px)
    ea, eb = axis_dirs(ua, ub, px, h, f)
    up = np.array([0.0, 1.0, 0.0])
    # World->camera rotation R has rows = camera axes in world frame. We know the images
    # of the world axes in camera coords, so the columns of R are ea, eb (sign chosen so
    # both point away from the camera) and their cross product for Z-up.
    ez = np.cross(ea, eb)
    if ez[1] < 0:
        ez = -ez
    Rc = np.column_stack([ea, eb, ez])        # camera_vec = Rc @ world_vec
    return dict(
        horizon_y=h, vp_a=[ua, h], vp_b=[ub, h], fit_rms_px=rms,
        principal=[px, h], f_px=f,
        f_mm_ff=f / W * 36.0,
        hfov_deg=math.degrees(2 * math.atan(W / (2 * f))),
        vfov_deg=math.degrees(2 * math.atan(H / (2 * f))),
        Rc=Rc.tolist(), up_check=float(abs(np.dot(ez, up))),
        orthogonality_deg=math.degrees(math.acos(abs(float(np.dot(ea, eb))))),
    )


def project(cam, Pw):
    """World point (m or mm, consistent) -> image pixel. cam needs Rc, cam_pos, f, pp."""
    Rc = np.array(cam["Rc"]); C = np.array(cam["cam_pos"])
    px, py = cam["principal"]; f = cam["f_px"]
    v = Rc @ (np.asarray(Pw, float) - C)
    if v[2] >= -1e-9:
        return None
    return (px + f * v[0] / (-v[2]), py - f * v[1] / (-v[2]))


def place_from_segment(cam, Pw0, Pw1, uv0, uv1):
    """Position the camera so that the world segment Pw0->Pw1 lands on uv0->uv1.

    With rotation and focal already known, the camera centre C is the point whose
    projections of Pw0 and Pw1 hit uv0 and uv1. Two back-projected rays; solve for C by
    least squares (the segment's known LENGTH is what fixes the scale).
    """
    Rc = np.array(cam["Rc"]); px, py = cam["principal"]; f = cam["f_px"]
    rows, rhs = [], []
    for Pw, (u, v) in ((Pw0, uv0), (Pw1, uv1)):
        d_cam = np.array([(u - px), -(v - py), -f])
        d_world = Rc.T @ d_cam
        d_world = d_world / np.linalg.norm(d_world)
        # (Pw - C) parallel to d_world  ->  two independent linear constraints
        for e in _perp_basis(d_world):
            rows.append(e); rhs.append(float(np.dot(e, Pw)))
    A = np.array(rows); y = np.array(rhs)
    C, *_ = np.linalg.lstsq(A, y, rcond=None)
    return C


def _perp_basis(d):
    a = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(d, a); e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1); e2 /= np.linalg.norm(e2)
    return [e1, e2]


def blender_camera(cam, sensor_mm=36.0, W=None):
    """Blender needs: lens mm (36 mm sensor fit HORIZONTAL), location, XYZ-euler."""
    Rc = np.array(cam["Rc"])
    # Blender camera looks down its local -Z with +Y up, same convention as here, so the
    # world->camera rotation matrix is the transpose of the camera's world matrix basis.
    Rw = Rc.T
    # Blender camera object rotation: columns are camera x,y,z axes in world coords.
    sy = math.sqrt(Rw[0, 0] ** 2 + Rw[1, 0] ** 2)
    if sy > 1e-8:
        rx = math.atan2(Rw[2, 1], Rw[2, 2]); ry = math.atan2(-Rw[2, 0], sy)
        rz = math.atan2(Rw[1, 0], Rw[0, 0])
    else:
        rx = math.atan2(-Rw[1, 2], Rw[1, 1]); ry = math.atan2(-Rw[2, 0], sy); rz = 0.0
    return dict(lens_mm=cam["f_px"] / (W or cam["W"]) * sensor_mm,
                sensor_mm=sensor_mm, sensor_fit="HORIZONTAL",
                location=list(cam["cam_pos"]),
                rotation_euler_deg=[math.degrees(rx), math.degrees(ry), math.degrees(rz)],
                shift_y=(cam["principal"][1] - (cam["H"] / 2.0)) / cam["W"] * -1.0)


if __name__ == "__main__":
    import sys
    print(json.dumps(solve(*json.load(open(sys.argv[1]))), indent=1))
