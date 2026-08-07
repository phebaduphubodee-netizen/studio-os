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


# --------------------------------------------------------------- mesh tables --
# The vertex/face tables for the two shapes the builder makes live HERE, in the
# pure layer, and the builder only hands them to bpy. They were inside the
# Blender module until a probe found that every _box face was wound INWARD and
# every axis="y" prism too — invisible to Cycles (its diffuse BSDF flips a
# backfacing normal) and fatal to a cloth COLLISION modifier, which pushes cloth
# along the normal and so pushed the duvet straight into the mattress. A defect
# that survives five rounds of LOOKing needs a test, and a test needs the table
# out of bpy. LAYER LAW, applied to the one thing that had escaped it.

def box_mesh(c, s):
    """(verts, faces) of an axis-aligned box in METRES from mm centre+size."""
    x, y, z = (v * MM for v in c)
    sx, sy, sz = (v * MM / 2 for v in s)
    vs = [(x + dx * sx, y + dy * sy, z + dz * sz)
          for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    fs = [(2, 3, 1, 0), (5, 7, 6, 4), (4, 6, 2, 0), (3, 7, 5, 1),
          (1, 5, 4, 0), (6, 7, 3, 2)]
    return vs, fs


def oct_mesh(c, s, cut, axis="z", tilt_deg=0.0, seg=6):
    """(verts, faces) of a rounded prism: four true ARC corners of radius `cut`.

    axis  — the extrusion axis: "z" rounds the PLAN, "y" rounds the x-z SECTION
            (a lying cylinder when cut is ~half the section).
    tilt_deg — rotation about y through the bottom-back edge, so a leaning
            pillow is a declared posture rather than a typed position.
    """
    x, y, z = (v * MM for v in c)
    z0, z1 = z - s[2] * MM / 2, z + s[2] * MM / 2
    if axis == "y":
        sa, sb = s[0] * MM / 2, s[2] * MM / 2
        e0, e1 = y - s[1] * MM / 2, y + s[1] * MM / 2
        ca, cb = x, z
    else:
        sa, sb = s[0] * MM / 2, s[1] * MM / 2
        e0, e1 = z0, z1
        ca, cb = x, y
    r = min(cut * MM, sa * 0.95, sb * 0.95)
    ring = []
    for cca, ccb, a0 in ((ca + sa - r, cb - sb + r, -90.0), (ca + sa - r, cb + sb - r, 0.0),
                         (ca - sa + r, cb + sb - r, 90.0), (ca - sa + r, cb - sb + r, 180.0)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            ring.append((cca + r * math.cos(a), ccb + r * math.sin(a)))
    n = len(ring)
    if axis == "y":
        vs = [(pa, e0, pb) for pa, pb in ring] + [(pa, e1, pb) for pa, pb in ring]
    else:
        vs = [(pa, pb, e0) for pa, pb in ring] + [(pa, pb, e1) for pa, pb in ring]
    fs = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    fs += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    if axis == "y":
        # (a, b) -> (x, z) extruded along +y is an ODD permutation of (x, y, z),
        # so the ring order that gives outward normals for axis="z" gives
        # inward ones here — all 30 faces.
        fs = [tuple(reversed(f)) for f in fs]
    if tilt_deg:
        th = math.radians(tilt_deg)
        px, pz = x + s[0] * MM / 2, z0          # pivot: bottom-back edge
        vs = [((vx - px) * math.cos(th) + (vz - pz) * math.sin(th) + px,
               vy,
               -(vx - px) * math.sin(th) + (vz - pz) * math.cos(th) + pz)
              for vx, vy, vz in vs]
    return vs, fs


def herringbone(w=132.1, length=619.6, anchor=(-5321.0, 422.2), joint=2.0,
                x_range=(-4750.0, 60.0), y_range=(-6600.0, 60.0)):
    """Plank rectangles of a herringbone floor, as [(x,y) x4] in mm on z=0.

    MEASURED, not styled: w and length come from 20 independently fitted joint
    lines (per-family answers agree to 0.05 mm), the 45 deg orientation from
    refitting each line FREELY and finding the bisector at 89.97 deg, and the
    anchor from phase-fitting against joint darkness (joints 4.12 vs floor 2.25).

    Construction is done in the rotated frame a=(x+y)/r2, b=(y-x)/r2, where the
    A planks lie along +a and the B planks along +b. In that frame the pattern
    is two rectangles and two lattice vectors:
        A at (a, b) spanning [a, a+L] x [b, b+w]
        B at (a+L, b+w-L) spanning [.., ..+w] x [.., ..+L]
        repeats  t1 = (L+w, w-L)   (along the staircase)
                 t2 = (w, w)       (across it)
    `joint` shrinks each plank so the dark base below shows as the groove — the
    target's joints are a measurable 1.83x darker than the field, which is what
    made the phase fit possible in the first place.
    """
    r2 = math.sqrt(2.0)
    half = joint / 2.0
    t1 = (length + w, w - length)
    t2 = (w, w)
    out = []
    # generous index window, clipped by the world-space bounds below
    span = int((abs(x_range[1] - x_range[0]) + abs(y_range[1] - y_range[0]))
               / min(w, length)) + 4
    for i in range(-span, span + 1):
        for j in range(-span, span + 1):
            a0 = anchor[0] + i * t1[0] + j * t2[0]
            b0 = anchor[1] + i * t1[1] + j * t2[1]
            for (aa, bb, da, db) in ((a0, b0, length, w),
                                     (a0 + length, b0 + w - length, w, length)):
                corners = [(aa + half, bb + half), (aa + da - half, bb + half),
                           (aa + da - half, bb + db - half), (aa + half, bb + db - half)]
                xy = [((a - b) / r2, (a + b) / r2) for a, b in corners]
                if all(x_range[0] - length <= x <= x_range[1] + length
                       and y_range[0] - length <= y <= y_range[1] + length
                       for x, y in xy) and any(
                        x_range[0] <= x <= x_range[1] and y_range[0] <= y <= y_range[1]
                        for x, y in xy):
                    out.append(xy)
    return out


def face_normal(vs, f):
    """Newell normal of a polygon — robust for non-planar quads."""
    nx = ny = nz = 0.0
    for i in range(len(f)):
        a, b = vs[f[i]], vs[f[(i + 1) % len(f)]]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def inward_faces(vs, fs):
    """Indices of faces whose normal points at the mesh centroid. A closed
    convex solid must return [] — anything else is a collider that repels
    inward."""
    cen = [sum(v[k] for v in vs) / len(vs) for k in range(3)]
    bad = []
    for j, f in enumerate(fs):
        n = face_normal(vs, f)
        fc = [sum(vs[i][k] for i in f) / len(f) for k in range(3)]
        if sum(n[k] * (fc[k] - cen[k]) for k in range(3)) <= 0:
            bad.append(j)
    return bad


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


def ripple_seed(verts, axis="x", wavelength_mm=75.0, amp_mm=6.0, jitter=0.35,
                salt=3, scale=0.001):
    """Seed a flat cloth sheet with ORGANISED fold starts. PURE.

    WHY THIS EXISTS, and why the two cheaper rungs could not do its job. The
    target's white duvet carries folds of ~75 mm wavelength (15.6 px at a
    measured 4.7-5.0 mm/px on the bed top). A cloth grid at 42 mm cells has a
    Nyquist wavelength of 84 mm — IT CANNOT REPRESENT A 75 MM FOLD AT ALL, at
    any slack, for any number of frames. That is why raising the solver's slack
    bought 1.4x of a needed 13x, and why a noise bump could reach the amplitude
    only by inventing an isotropic crumple that renders as tree bark. Fold
    depth was never the free variable; MESH RESOLUTION was, and under it the
    direction was.

    So: a finer cell gives the folds somewhere to exist, and this gives them a
    direction. Real bedding folds run in FAMILIES along the drape's tension
    lines, not as isotropic noise — which is the structural reason the noise
    rung failed. The seed is a jittered sinusoid whose ridges run ACROSS the
    bed (varying along `axis`), and it is deliberately irregular: a perfect
    sine reads as corrugated metal.

    The ripple moves z ONLY, so the plan footprint is unchanged while the ARC
    LENGTH grows by about pi^2*A^2/L^2 (6.3% at A=6, L=75). That excess IS the
    fabric a made bed has spare, delivered in the one form the solver can keep:
    already buckled, in a direction, at a wavelength the mesh can hold.

    verts are in world METRES (softgoods' contract); wavelength/amp are mm.
    """
    i = "xyz".index(axis)
    j = 1 if i == 0 else 0            # the ACROSS axis, for the envelope
    L = wavelength_mm * scale
    A = amp_mm * scale
    out = []
    for n, v in enumerate(verts):
        u = v[i]
        # ENVELOPE — REFUTED BY LOOK 2026-08-05 and kept at 1.0 deliberately.
        # The intent was to leave some bands flat and others deeply folded, so
        # the ridges would stop reading as corduroy. It did the opposite: a
        # periodic envelope adds a SECOND regular period (its own), and the
        # render came back more banded than before. The eye caught it; the fold
        # metric could not, because a regular field and an irregular one carry
        # the same high-passed rms. Irregularity has to come from the jitter
        # term, which is aperiodic, not from another sine. Left in place at 1.0
        # rather than deleted so the next person does not re-derive it.
        env = 1.0
        # THREE INCOMMENSURATE PERIODS, and the reason is what both the eye and
        # the cross-vendor critic caught on the first build of this seed: the
        # cloth read as CORDUROY / "a repeating pattern with no depth". The
        # first version added irregularity as a PER-VERTEX random term, which
        # is the wrong kind — per-vertex noise is high-frequency grain and
        # leaves the RIDGE SPACING perfectly even, and it is spacing the eye
        # reads. Real folds are unevenly spaced, so the irregularity has to
        # live in the phase field itself: three sines whose wavelengths share
        # no common multiple never repeat over the sheet.
        phase = 2.0 * math.pi * u / L
        h = (math.sin(phase)
             + 0.62 * math.sin(phase * 0.611 + 0.9)      # a longer swell
             + 0.31 * math.sin(phase * 1.703 + 2.3))     # a shorter break-up
        if jitter:
            # a slow ACROSS-sheet phase drift, so a ridge is not a straight
            # line either. Deterministic and salt-keyed: the same spec must
            # bake the same cloth, bit for bit.
            drift = math.sin(v[j] / (L * 3.1) + salt * 0.7)
            h += jitter * math.sin(phase + 1.9 * drift)
        out.append((v[0], v[1], v[2] + A * env * h))
    return out


def slat_stack(c, s, pitch_mm, chord_mm, tilt_deg, thick_mm=2.0, scale=0.001):
    """A venetian blind: horizontal slats filling the box (centre `c`, size `s`).

    Slats run along y (the window's width), each a thin plate of `chord_mm`
    tilted `tilt_deg` about that axis, repeated every `pitch_mm` up z. Returns
    (verts, faces) for ONE mesh — 8 verts and 6 quads per slat, no n-gons.

    R8 BUILD class by its own test: this is an extrusion of a measured outline
    repeated on a measured pitch, not a free-form shape. Every number here is
    measured or declared:
      pitch   6.50 px between 89 peaks in the target's own column, constant up
              the whole band, backprojecting to 29.4 mm on the wall plane.
      extent  the light rig's blind measurement (y -2630..-910, z 730..2550),
              confirmed independently here at the near edge (u=50 -> y -2631,
              1 mm) and at the top (v=125 -> z 2582 against 2550, 32 mm). The
              BOTTOM is the one number of that pass this view could not confirm
              — the periodic column runs on past the blind into the console
              below it — so it is inherited, not re-measured.
      chord/tilt  DECLARED. A 1080-px frame gives ~6.5 px per slat, which
              cannot resolve a slat's width or its angle; what it fixes is the
              pitch and the fact that the gaps are narrow. Chord and tilt are
              chosen to satisfy the one thing the pixels DO say — chord*cos(tilt)
              just under the pitch, so the blind reads nearly closed.
    """
    n = max(1, int(round(s[2] / pitch_mm)))
    t = math.radians(tilt_deg)
    ct, st = math.cos(t), math.sin(t)
    y0, y1 = (c[1] - s[1] / 2.0) * scale, (c[1] + s[1] / 2.0) * scale
    verts, faces = [], []
    for i in range(n):
        z0 = c[2] - s[2] / 2.0 + (i + 0.5) * s[2] / n
        base = len(verts)
        for ex in (-chord_mm / 2.0, chord_mm / 2.0):
            for ez in (-thick_mm / 2.0, thick_mm / 2.0):
                x = (c[0] + ex * ct - ez * st) * scale
                z = (z0 + ex * st + ez * ct) * scale
                for y in (y0, y1):
                    verts.append((x, y, z))
        # 8 verts, ordered (ex, ez, y). Quads over the box's six faces.
        a, b, cc, d, e, f, g, h = (base + k for k in range(8))
        faces += [(a, b, d, cc), (e, g, h, f),      # the two ends in ex
                  (a, cc, g, e), (b, f, h, d),      # the two faces in ez
                  (a, e, f, b), (cc, d, h, g)]      # the two ends in y
    return verts, faces
