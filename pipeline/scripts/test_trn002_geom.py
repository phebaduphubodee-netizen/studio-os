"""Pins for the TRN-002 instruments: landscape camera math + line fitter.

What these protect (each was a live failure this round, not a hypothetical):
  - the landscape shift convention (Blender ties focal AND shift_y to sensor
    WIDTH; a square-frame habit silently misplaces the horizon),
  - project/backproject inversion on all three plane families,
  - the closed-form station anchor,
  - the straightness guard (a rounded console end fit as a straight line is
    how a VP no room axis owns got invented),
  - dark-stroke mode (an edge detector sees a thin frame bar as TWO edges and
    drops every station as ambiguous — art_L starved at n=1 until this mode).
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_geom as G  # noqa: E402


# --- mesh winding -----------------------------------------------------------
# Cycles' diffuse BSDF flips a backfacing normal, so an inward-wound solid
# renders correctly and no LOOK can catch it. A cloth COLLISION modifier does
# not flip — it pushes cloth ALONG the normal, i.e. into the box. Five rounds
# of blockout shipped with every box and every axis="y" prism inverted, and it
# only surfaced when a duvet fell through the mattress. These tests are the
# reason it cannot come back.

def _shapes():
    yield "box", G.box_mesh([100, 200, 300], [1000, 800, 600])
    yield "oct z", G.oct_mesh([0, 0, 500], [800, 600, 400], 120, axis="z")
    yield "oct y", G.oct_mesh([0, 0, 500], [400, 900, 400], 150, axis="y")
    yield "oct z tilt", G.oct_mesh([0, 0, 500], [800, 600, 400], 120,
                                   axis="z", tilt_deg=22.0)


def test_every_generated_face_is_wound_outward():
    for label, (vs, fs) in _shapes():
        assert G.inward_faces(vs, fs) == [], f"{label} has inward faces"


def test_the_winding_check_can_actually_fail():
    """A guard that cannot fail is not a guard — reverse one face and it must
    be caught (the negative control this repo asks every new guard to carry)."""
    vs, fs = G.box_mesh([0, 0, 0], [100, 100, 100])
    fs[2] = tuple(reversed(fs[2]))
    assert G.inward_faces(vs, fs) == [2]


def test_box_dimensions_and_centre_survive_the_table():
    vs, _ = G.box_mesh([100, 200, 300], [1000, 800, 600])
    xs, ys, zs = zip(*vs)
    assert abs((max(xs) - min(xs)) - 1.0) < 1e-9
    assert abs((max(ys) - min(ys)) - 0.8) < 1e-9
    assert abs((max(zs) + min(zs)) / 2 - 0.3) < 1e-9


def test_oct_y_rounds_the_section_not_the_plan():
    """The r3b lesson in a test: axis='y' must make the x-z SECTION round and
    leave the y extent flat-ended, which is what a lying bolster is."""
    vs, _ = G.oct_mesh([0, 0, 0], [400, 900, 400], 200, axis="y")
    ys = sorted({round(v[1], 6) for v in vs})
    assert len(ys) == 2, "a y-extruded prism has exactly two end planes"
    xs = {round(v[0], 6) for v in vs}
    zs = {round(v[2], 6) for v in vs}
    assert len(xs) > 4 and len(zs) > 4, "the x-z section must be a rounded ring"


def test_tilt_pivots_about_the_bottom_back_edge():
    """A leaning pillow must keep its mattress contact: the pivot edge cannot
    move, or the tilt silently becomes a translation too."""
    c, s = [0, 0, 500], [400, 600, 400]
    flat, _ = G.oct_mesh(c, s, 60, axis="z")
    lean, _ = G.oct_mesh(c, s, 60, axis="z", tilt_deg=20.0)
    pivot = (max(v[0] for v in flat), min(v[2] for v in flat))
    still = [v for v in lean
             if abs(v[0] - pivot[0]) < 1e-6 and abs(v[2] - pivot[1]) < 1e-6]
    assert still, "no vertex stayed on the pivot edge"
import trn002_lines as L  # noqa: E402

WH = (1080, 821)
CAM = {"x_mm": -4491.0, "y_mm": -7992.0, "z_mm": 1305.0,
       "yaw_deg": 20.0417, "focal_mm": 38.841,
       "shift_x": 0.0, "shift_y": -0.002961}


def test_horizon_uses_width_for_shift():
    # a point at camera height, dead ahead, lands on the horizon row:
    # H/2 + W*shift_y — the WIDTH scales the shift, not the height.
    fwd, _, _ = G.cam_basis(CAM["yaw_deg"])
    pt = (CAM["x_mm"] + 5000 * fwd[0], CAM["y_mm"] + 5000 * fwd[1], CAM["z_mm"])
    u, v = G.project(CAM, pt, WH)
    assert v == pytest.approx(821 / 2 + 1080 * CAM["shift_y"], abs=1e-6)
    assert u == pytest.approx(1080 / 2, abs=1e-6)


@pytest.mark.parametrize("plane,pt", [
    (("y", 0.0), (-2137.0, 0.0, 1970.0)),
    (("x", 0.0), (0.0, -750.0, 3217.0)),
    (("z", 0.0), (-3787.0, -1843.0, 0.0)),
])
def test_project_backproject_roundtrip(plane, pt):
    uv = G.project(CAM, pt, WH)
    back = G.backproject(CAM, uv, plane, WH)
    assert back is not None
    for a, b in zip(back, pt):
        assert a == pytest.approx(b, abs=1e-6)


def test_backproject_refuses_behind_camera():
    # a ray pointed away from the plane must return None, never a number
    assert G.backproject(CAM, (540.0, 410.0), ("y", -20000.0), WH) is None


def test_station_from_anchor_recovers_camera():
    anchor = (0.0, 0.0, 3102.0)
    uv = G.project(CAM, anchor, WH)
    pins = {k: CAM[k] for k in ("yaw_deg", "focal_mm", "shift_x", "shift_y")}
    cam = G.station_from_anchor(pins, uv, anchor, CAM["z_mm"], WH)
    assert cam["x_mm"] == pytest.approx(CAM["x_mm"], abs=1e-6)
    assert cam["y_mm"] == pytest.approx(CAM["y_mm"], abs=1e-6)


def _canvas(w=200, h=200, base=180.0):
    return np.full((h, w), base, dtype=np.float64)


def test_fitter_straight_edge_subpixel():
    g = _canvas()
    for y in range(200):
        edge = 60.3 + 0.10 * y
        xi = int(edge)
        g[y, :xi] = 120.0
        g[y, xi] = 120.0 + (180.0 - 120.0) * (edge - xi)
    f = L.fit_seed(g, {"name": "e", "p0": [62, 10], "p1": [80, 190]})
    assert f["ok"] and L.usable(f)
    # recovered angle: dx/dy = 0.10 -> atan2 in image terms
    want = math.degrees(math.atan2(1.0, 0.10)) % 180
    assert f["angle_deg"] == pytest.approx(want, abs=0.15)


def test_straightness_guard_rejects_curve():
    g = _canvas()
    for y in range(200):
        edge = 60.0 + 0.0012 * y * y  # gentle parabola, rms-small but bent
        xi = int(edge)
        g[y, :xi] = 120.0
        g[y, xi] = 120.0 + 60.0 * (edge - xi)
    f = L.fit_seed(g, {"name": "c", "p0": [62, 10], "p1": [105, 190]})
    assert f["ok"]
    assert not L.usable(f)          # bend guard, not a human eyeball
    assert f["bend_deg"] > L.BEND_MAX


def test_dark_stroke_mode_finds_thin_line():
    g = _canvas()
    g[:, 99:102] = 40.0  # 3px dark bar on light ground
    edge = L.fit_seed(g, {"name": "edge", "p0": [100, 10], "p1": [100, 190]})
    dark = L.fit_seed(g, {"name": "dark", "p0": [100, 10], "p1": [100, 190],
                          "mode": "dark", "half": 5})
    # edge mode is ambiguous on a stroke (two opposing edges); dark mode locks
    assert dark["ok"] and L.usable(dark)
    assert dark["ambig_frac"] < 0.1
    assert abs(dark["e0"][0] - 100.5) < 0.6
    assert (not edge.get("ok")) or edge["ambig_frac"] > 0.5 or not L.usable(edge)


def test_vp_residual_is_angular():
    # same angular error, 10x the VP distance -> same residual (not 10x)
    line = {"n": [0.0, 1.0], "c": -100.0, "e0": [0, 100], "e1": [100, 100]}
    near = L.vp_residual(line, (1000.0, 110.0))
    far = L.vp_residual(line, (10000.0, 200.0))
    ang_near = math.degrees(math.asin(10.0 / math.hypot(950.0, 10.0)))
    assert near == pytest.approx(ang_near, abs=0.02)
    assert far == pytest.approx(math.degrees(math.asin(100.0 / math.hypot(9950.0, 100.0))), abs=0.02)


def test_ripple_seed_moves_only_z_and_is_deterministic():
    """The plan footprint is MEASURED (it is the platform's own edges), so a
    fold seed that moved x or y would silently re-cut a solved dimension."""
    vs = [(x * 0.001, y * 0.001, 0.5)
          for x in range(0, 400, 20) for y in range(0, 200, 20)]
    a = G.ripple_seed(vs)
    b = G.ripple_seed(vs)
    assert a == b, "same input must bake the same cloth"
    assert [(v[0], v[1]) for v in a] == [(v[0], v[1]) for v in vs]
    assert any(abs(p[2] - q[2]) > 1e-6 for p, q in zip(a, vs))


def test_ripple_seed_adds_arc_length_without_widening_the_plan():
    """The excess IS the point: a made bed's spare fabric, delivered already
    buckled at a wavelength the mesh can hold."""
    import math
    vs = [(x * 0.001, 0.0, 0.5) for x in range(0, 600, 5)]
    r = G.ripple_seed(vs, "x", 75.0, 6.0, jitter=0.0)
    flat = sum(math.dist(vs[i], vs[i + 1]) for i in range(len(vs) - 1))
    arc = sum(math.dist(r[i], r[i + 1]) for i in range(len(r) - 1))
    assert arc > flat * 1.02, f"seed adds no fabric: {arc/flat:.4f}"
    assert arc < flat * 1.20, f"seed adds absurd fabric: {arc/flat:.4f}"


def test_ripple_seed_wavelength_is_the_one_asked_for():
    """A 42 mm cell cannot hold a 75 mm fold (Nyquist 84) — the whole reason
    this exists — so the seed's own period must be trustworthy."""
    vs = [(x * 0.0005, 0.0, 0.0) for x in range(0, 1200)]
    r = G.ripple_seed(vs, "x", 75.0, 6.0, jitter=0.0)
    zs = [v[2] for v in r]
    crossings = sum(1 for i in range(len(zs) - 1)
                    if (zs[i] <= 0) != (zs[i + 1] <= 0))
    span_mm = (vs[-1][0] - vs[0][0]) * 1000.0
    period = 2 * span_mm / max(crossings, 1)
    assert 60 < period < 95, f"asked 75 mm, seed delivers {period:.1f} mm"


# ---- slat_stack (r25 venetian blind) ----------------------------------------

def test_slat_stack_fills_the_box_at_the_measured_pitch():
    v, f = G.slat_stack((-4700, -1770, 1640), (40, 1720, 1820), 29.4, 34.0, 25.0)
    assert len(f) // 6 == 62, len(f) // 6          # 1820 / 29.4
    zs = [p[2] * 1000 for p in v]
    assert 730 <= min(zs) and max(zs) <= 2550, (min(zs), max(zs))
    ys = [p[1] * 1000 for p in v]
    assert abs(min(ys) + 2630) < 1e-6 and abs(max(ys) + 910) < 1e-6


def test_every_slat_face_is_a_quad_and_no_vertex_is_shared_between_slats():
    """8 verts and 6 quads per slat. Shared verts would weld two slats into one
    surface and the gaps — the whole point of a blind — would close."""
    v, f = G.slat_stack((0, 0, 1000), (40, 1000, 300), 30.0, 34.0, 25.0)
    assert all(len(q) == 4 for q in f)
    assert len(v) == 8 * (len(f) // 6)
    assert len(set(v)) == len(v)


def test_a_shallower_tilt_opens_the_gaps():
    """chord*cos(tilt) against the pitch is what decides open vs closed, and it
    is the one thing a 6.5-px-per-slat image actually constrains."""
    import math
    for tilt, closed in ((25.0, True), (70.0, False)):
        assert (34.0 * math.cos(math.radians(tilt)) > 29.4) is closed


def test_pitch_larger_than_the_box_still_makes_one_slat():
    v, f = G.slat_stack((0, 0, 100), (40, 500, 20), 999.0, 34.0, 25.0)
    assert len(f) // 6 == 1


# ------------------------------------------------------- arch_pocket (r29) --
# The cavity that puts true black in the frame. These pins exist because this
# lane's recorded failure is MEASURED AND NEVER BUILT — the artwork's 21 mm
# black bar was measured at r2 and the mass wore a 0.78 white until r13, and
# nothing checked that the measured feature survived into geometry.

MOUTH = dict(face_x_mm=-2100.0, y_centre_mm=-5464.8, spring_z_mm=199.6,
             radius_mm=149.9, base_z_mm=0.0, depth_mm=450.0)


def test_the_pocket_outline_carries_the_measured_arch():
    """Crown, springing and both extremes, in mm, straight off the fit."""
    v, f = G.arch_pocket(**MOUTH)
    ys = [p[1] * 1000 for p in v]
    zs = [p[2] * 1000 for p in v]
    assert abs(max(zs) - (199.6 + 149.9)) < 0.05, max(zs)      # crown 349.5
    assert abs(min(zs)) < 1e-6                                  # base at floor
    assert abs(max(ys) - (-5464.8 + 149.9)) < 0.05, max(ys)     # left springing
    assert abs(min(ys) - (-5464.8 - 149.9)) < 0.05, min(ys)     # right springing


def test_the_near_end_is_open_and_the_far_end_is_capped():
    """The opening IS the object. A cap on the near face makes it a lump of
    upholstery with a decorative groove, which is what a boolean-free build
    accidentally produces if the face loop is closed at the wrong end."""
    v, f = G.arch_pocket(**MOUTH)
    n = len(v) // 2
    near, far = set(range(n)), set(range(n, 2 * n))
    caps = [q for q in f if len(q) == n]
    assert len(caps) == 1 and set(caps[0]) == far, caps
    assert not any(set(q) <= near for q in f)


def test_the_arc_is_an_arc_and_not_a_chamfer():
    """A straight line fit the measured top edge 9.7x worse than a circle. If
    the generator ever flattens the head, this catches it: every head vertex
    must sit on the fitted radius."""
    v, _ = G.arch_pocket(**MOUTH)
    n = len(v) // 2
    head = [(p[1] * 1000, p[2] * 1000) for p in v[:n]
            if p[2] * 1000 > MOUTH["spring_z_mm"] + 1e-9]
    assert len(head) >= 20, len(head)
    for y, z in head:
        r = math.hypot(y - MOUTH["y_centre_mm"], z - MOUTH["spring_z_mm"])
        assert abs(r - MOUTH["radius_mm"]) < 1e-6, (y, z, r)


def test_the_built_mouth_reprojects_onto_the_pixels_it_was_measured_from():
    """END TO END, and the only test here that could have caught the artwork:
    push the built rim back through the SOLVED camera and land on the target's
    own measured arch — crown (1034, 754) and left jamb u=1004.00."""
    spec = G.load_spec(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "training", "TRN-002",
                                    "spec_r29.json"))
    cam, wh = spec["camera"], (spec["image"]["w"], spec["image"]["h"])
    v, _ = G.arch_pocket(**MOUTH)
    n = len(v) // 2
    uv = [G.project(cam, tuple(t * 1000 for t in p), wh) for p in v[:n]]
    crown = min(uv, key=lambda t: t[1])
    assert abs(crown[0] - 1034.0) < 2.0, crown      # measured apex column
    assert abs(crown[1] - 754.0) < 2.0, crown       # measured apex row
    jamb = max(uv, key=lambda t: -t[0])             # left springing / jamb
    assert abs(jamb[0] - 1004.0) < 2.0, jamb


@pytest.mark.parametrize("bad", [dict(radius_mm=0.0), dict(depth_mm=-1.0),
                                 dict(spring_z_mm=-10.0)])
def test_a_pocket_that_cannot_be_a_cavity_raises(bad):
    """Fail closed. A zero radius or a negative depth silently yields a
    degenerate sliver that renders as nothing, and 'nothing' is exactly what
    this object is here to stop being."""
    with pytest.raises(ValueError):
        G.arch_pocket(**{**MOUTH, **bad})


def test_open_face_drops_exactly_the_minus_x_quad():
    """DERIVED from the ring order, not typed as an index — and pinned, because
    dropping the wrong quad opens a hole in a wall nobody is looking at while
    the mouth stays shut."""
    c, s, cut = (-1750, -5464.8, 275), (700, 900, 550), 200
    v0, f0 = G.oct_mesh(c, s, cut)
    v1, f1 = G.oct_mesh(c, s, cut, open_face="x_min")
    assert len(f1) == len(f0) - 1
    gone = [f for f in f0 if f not in f1]
    assert len(gone) == 1, gone
    xs = [v0[i][0] * 1000 for i in gone[0]]
    assert all(abs(x - (-2100.0)) < 1e-6 for x in xs), xs


def test_open_face_is_refused_where_the_ring_order_does_not_hold():
    with pytest.raises(ValueError):
        G.oct_mesh((0, 0, 0), (100, 100, 100), 20, axis="y", open_face="x_min")


def test_the_host_face_is_authored_around_the_opening_not_over_it():
    """The quads that replace the dropped face must all lie ON the opening's
    plane, and none of them may cover the mouth: a face that spans the arch is
    the 2 mm groove defect again, wearing a different shape."""
    face = (-5714.8, -5214.8, 550.0)
    v, f = G.arch_pocket(**MOUTH, face=face)
    plane = MOUTH["face_x_mm"] / 1000.0
    host = [q for q in f if all(abs(v[i][0] - plane) < 1e-9 for i in q)]
    assert host, "no host face emitted"
    yc, r, sp = MOUTH["y_centre_mm"], MOUTH["radius_mm"], MOUTH["spring_z_mm"]
    for q in host:
        pts = [(v[i][1] * 1000, v[i][2] * 1000) for i in q]
        mid = (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)
        inside = (abs(mid[0] - yc) < r and
                  (mid[1] <= sp or math.hypot(mid[0] - yc, mid[1] - sp) < r))
        assert not inside, f"host quad centred inside the mouth: {mid}"


def test_a_mouth_too_wide_for_its_host_face_raises():
    with pytest.raises(ValueError):
        G.arch_pocket(**MOUTH, face=(-5500.0, -5400.0, 550.0))


def test_a_crown_that_reaches_the_top_of_the_host_face_raises():
    with pytest.raises(ValueError):
        G.arch_pocket(**MOUTH, face=(-5714.8, -5214.8, 300.0))
