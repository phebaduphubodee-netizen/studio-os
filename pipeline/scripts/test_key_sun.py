"""key_sun — the derivation must reproduce build_room's SUN convention, refuse a
beam that misses its pane, and find the floor patch inside the frame on the camera
of record. Pure python, no bpy."""
import json
import math
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import key_sun as ks  # noqa: E402

SPEC = os.path.join(HERE, "..", "..", "projects", "PRJ-2026-002_c001-house",
                    "03_layout", "master-suite.CANONICAL.spec.json")


def _toy():
    return {
        "room": {"outline_mm": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]],
                 "ceiling_mm": 2800,
                 "openings": [
                     {"id": "S", "type": "glass", "rect": [1000, 0, 3000, 0],
                      "sill_mm": 0, "head_mm": 2800},
                     {"id": "W", "type": "glass", "rect": [0, 1000, 0, 2000],
                      "sill_mm": 1000, "head_mm": 2200},
                     {"id": "D", "type": "door", "rect": [5000, 1000, 5000, 2000],
                      "head_mm": 2400}]},
        "builtins": [{"name": "bench", "kind": "millwork", "x": 1500, "y": 1500,
                      "w": 1000, "d": 500, "h": 450}],
        "items": [{"name": "rug", "kind": "rug", "x": 500, "y": 500, "w": 4000,
                   "d": 3000, "h": 10}],
    }


def test_inward_normal_points_into_the_room():
    fr = ks.opening_frame(_toy(), "S")
    assert (fr["nx"], fr["ny"]) == pytest.approx((0.0, 1.0))
    fr = ks.opening_frame(_toy(), "W")
    assert (fr["nx"], fr["ny"]) == pytest.approx((1.0, 0.0))
    # the camera stand decides the side when given — a stand OUTSIDE flips it
    fr = ks.opening_frame(_toy(), "S", toward_mm=(2000, -5000))
    assert fr["ny"] == pytest.approx(-1.0)


def test_door_is_not_a_sun_source():
    with pytest.raises(ks.KeySunError):
        ks.opening_frame(_toy(), "D")
    with pytest.raises(ks.KeySunError):
        ks.opening_frame(_toy(), "nope")


def test_beam_and_euler_round_trip_matches_build_room_convention():
    for az in (-60, -30, 0, 30, 45, 60):
        for elev in (0.2, 0.55, 1.0):
            b = ks.beam(0.0, 1.0, az, elev)
            assert math.hypot(*b) == pytest.approx(1.0)
            e = ks.sun_euler(b)
            b2 = ks.emitted_beam(e)
            assert b2 == pytest.approx(b, abs=1e-9)
            # rz must equal build_room's atan2(-nx, ny) for az=0 (beam == normal)
            if az == 0:
                assert e[2] == pytest.approx(math.atan2(-0.0, 1.0))
                assert e[0] == pytest.approx(math.pi / 2 - elev)


def test_positive_az_puts_the_sun_east_of_a_south_pane():
    b = ks.beam(0.0, 1.0, 45, 0.55)
    assert b[0] < 0 and b[1] > 0            # travels toward -x, +y
    assert ks.compass_of(b) == pytest.approx(135.0)   # sun stands SE


def test_refuses_a_beam_that_misses_its_pane():
    with pytest.raises(ks.KeySunError, match="REFUSED"):
        ks.solve(_toy(), "S", 80, 0.55)   # cos 80 = 0.17 < 0.30
    # the dot is the 3D beam's (build_room's convention since p2r78), so the
    # elevation counts: cos70*cos0.55 = 0.29 fails, cos60*cos0.55 = 0.43 passes
    with pytest.raises(ks.KeySunError, match="REFUSED"):
        ks.solve(_toy(), "S", 70, 0.55)
    sol = ks.solve(_toy(), "S", 60, 0.55)
    assert sol["dot"] == pytest.approx(math.cos(math.radians(60)) * math.cos(0.55))


def test_floor_patch_is_the_pane_swept_along_the_beam():
    sol = ks.solve(_toy(), "S", 0, math.atan(1.0))  # 45 deg: run == rise
    xs = sorted(set(round(p[0], 6) for p in sol["floor_patch_m"]))
    ys = sorted(set(round(p[1], 6) for p in sol["floor_patch_m"]))
    assert xs == [1.0, 3.0]
    assert ys == [0.0, 2.8]                  # head 2.8 m lands 2.8 m in at 45 deg
    names = [n for n, _ in sol["lands_on"]]
    assert "rug" in names and "bench" in names


def test_below_horizon_refused():
    fr = ks.opening_frame(_toy(), "S")
    with pytest.raises(ks.KeySunError):
        ks.floor_patch(fr, (0.0, 1.0, 0.0))


@pytest.mark.skipif(not os.path.exists(SPEC), reason="spec of record not on disk")
def test_record_camera_d152_sun_through_slider_lands_in_frame():
    spec = json.load(open(SPEC, encoding="utf-8"))
    variants = spec.get("eye_camera_variants") or {}
    variant = "camera_of_record_2026-08-26_D152" if "camera_of_record_2026-08-26_D152" in variants else None
    cam = ks.cam_for(spec, variant)
    sol = ks.solve(spec, "glz-slider", 45, 0.55, cam=cam, stand_mm=(cam["ex"] / ks.MM, cam["ey"] / ks.MM))
    assert sol["opening"]["ny"] == pytest.approx(1.0)      # south wall, room is +y
    assert sol["dot"] > ks.DOT_FLOOR
    assert sol["patch_in_frame"] is True, ks.describe(sol)
    kinds = {k for _, k in sol["lands_on"]}
    assert kinds, "a key that lands on nothing named has lit nothing"
