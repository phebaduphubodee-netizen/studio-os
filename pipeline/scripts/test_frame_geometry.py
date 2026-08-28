#!/usr/bin/env python3
"""test_frame_geometry.py — pin the claims frame_geometry makes about the eye frame.

These are not synthetic fixtures: every expectation below is a number the p2r78 round
measured on the CANONICAL spec and then acted on, so a future edit that quietly changes
the projection convention breaks the test that named the defect rather than the frame.
"""
import json
import math
import os
import unittest

import frame_geometry as fg

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house", "03_layout",
                    "master-suite.CANONICAL.spec.json")

# THE OUTGOING CAMERA (bed-foot hero, D-118) at the deliverable resolution — the camera
# of record from 2026-08-22 until the owner chose the room-contained leg from the A/B
# pair on 2026-08-26 (D-152). It stays pinned here BY VALUE and not by spec lookup,
# because these tests are the record of what was measurably wrong with it: three sighted
# readers said "backdrop", and this block is the geometry that made them right. A test
# that re-read the spec would have quietly started describing the new camera and the
# evidence would have evaporated with the edit.
CAM = {"ex": 1.400, "ey": 1.125, "tx": 5.180, "ty": 1.125, "eye_h": 1.15,
       "lens_mm": 26.0, "shift_y": -0.14, "res_w": 2400, "res_h": 1800}


def _record_cam():
    """The camera the spec declares TODAY, resolved the way build_room resolves it."""
    import camera_config
    s = _spec()
    ov = s["eye_camera"]
    return {"ex": ov["stand_mm"][0] / 1000.0, "ey": ov["stand_mm"][1] / 1000.0,
            "tx": ov["aim_mm"][0] / 1000.0, "ty": ov["aim_mm"][1] / 1000.0,
            "eye_h": camera_config.spec_eye_h_m(s),
            "lens_mm": float(ov["lens_mm"]), "shift_y": float(ov["shift_y"]),
            "res_w": 2400, "res_h": 1800}


def _spec():
    with open(SPEC, encoding="utf-8") as f:
        return json.load(f)


class TestProjection(unittest.TestCase):
    def test_a_point_on_the_axis_lands_at_frame_centre_in_u(self):
        s = _spec()
        u, v, d = fg.project((5.18, 1.125, CAM["eye_h"]), CAM)
        self.assertAlmostEqual(u, 0.0, places=6,
                               msg="a point on the aim axis must sit on the frame's "
                                   "vertical centre line")
        self.assertAlmostEqual(d, 3.78, places=2)

    def test_positive_shift_y_puts_more_ceiling_in_frame(self):
        """The sign convention this whole module depends on. build_room's
        RENDER_SHIFT_Y is NEGATIVE and its comment says it frames DOWN, so a point
        near the ceiling must move DOWN the image (smaller v) as shift_y rises."""
        p = (5.18, 1.125, 2.7)
        _u0, v0, _ = fg.project(p, dict(CAM, shift_y=0.0))
        _u1, v1, _ = fg.project(p, dict(CAM, shift_y=+0.10))
        self.assertLess(v1, v0)


class TestTheOutgoingCameraCroppedTheRoom(unittest.TestCase):
    """The three findings a sighted panel measured from p2r77's pixels, reproduced
    here from geometry alone — which is the point of the module. This camera is no
    longer the record (D-152); these tests keep WHY it was replaced."""

    def setUp(self):
        self.spec = _spec()
        self.rep = fg.framing_report(self.spec, dict(CAM, fstop=2.8, focus_m=3.78))

    def test_the_slat_walls_own_top_is_outside_the_frame(self):
        top = self.rep["top_edge"]
        self.assertIn("BF14", top["what"])
        self.assertFalse(top["in_frame"])
        self.assertAlmostEqual(top["v"], 0.4533, places=3)
        self.assertAlmostEqual(top["v_max"], 0.375, places=3)

    def test_the_nearest_mass_is_the_bench_and_its_floor_contact_is_cropped(self):
        nm = self.rep["nearest_mass"]
        self.assertEqual(nm["kind"], "bench")
        self.assertAlmostEqual(nm["depth_m"], 1.254, places=2)
        self.assertFalse(nm["floor_contact_in_frame"])

    def test_the_nearest_mass_sits_outside_the_shipped_depth_of_field(self):
        cur = self.rep["dof_current"]
        self.assertEqual(cur["fstop"], 2.8)
        self.assertGreater(cur["near_m"], self.rep["nearest_mass"]["depth_m"],
                           "f/2.8 focused at the subject starts its sharp zone BEYOND "
                           "the bench — the nearest object to the viewer was the "
                           "blurriest thing in the picture")
        self.assertFalse(cur["nearest_mass_sharp"])

    def test_the_derived_aperture_holds_the_nearest_mass_sharp(self):
        d = self.rep["dof"]
        self.assertTrue(d["reachable"])
        self.assertTrue(d["nearest_mass_sharp"])
        self.assertLessEqual(d["near_m"], self.rep["nearest_mass"]["depth_m"])
        self.assertIsNone(d["far_m"], "focusing at hyperfocal must reach infinity")
        self.assertTrue(8.0 < d["fstop"] < 12.0)

    def test_a_mass_outside_the_frustum_is_not_the_nearest_mass(self):
        """The first cut answered with the wardrobe standing 1.7 m off to the side at
        u = 1.27 — a reading taken outside the picture is not a reading about it."""
        nm = fg.nearest_mass(self.spec, CAM)
        u, _v, _d = fg.project((nm[3], nm[4], 0.0), CAM)
        self.assertLessEqual(abs(u), 0.5)


class TestDofMath(unittest.TestCase):
    def test_circle_of_confusion_follows_the_delivered_resolution(self):
        _n, _f, coc_hi, _a, _b, _ok = fg.dof_from_geometry(26.0, 1.25, 2400)
        _n2, _f2, coc_lo, _a2, _b2, _ok2 = fg.dof_from_geometry(26.0, 1.25, 1200)
        self.assertAlmostEqual(coc_hi, 0.03, places=4)
        self.assertAlmostEqual(coc_lo, 0.06, places=4)

    def test_focusing_at_hyperfocal_makes_the_near_limit_half_of_it(self):
        n, focus, coc, near, far, ok = fg.dof_from_geometry(26.0, 2.0, 2400, margin=1.0)
        self.assertAlmostEqual(near, 2.0, places=1)
        self.assertEqual(far, math.inf)

    def test_an_unreachable_aperture_is_reported_not_clamped_silently(self):
        # a very long lens with a very near subject cannot hold both
        n, focus, coc, near, far, ok = fg.dof_from_geometry(200.0, 0.5, 2400)
        self.assertFalse(ok)


class TestSolve(unittest.TestCase):
    def test_it_finds_a_camera_that_contains_both_facts(self):
        spec = _spec()
        best = fg.solve_framing(spec, dict(CAM),
                                stand_candidates_m=[1.24],
                                lens_candidates=[20.0, 21.0, 22.0, 26.0],
                                eye_candidates_m=[1.00, 1.05, 1.15])
        self.assertIsNotNone(best)
        r = best["report"]
        self.assertTrue(r["top_edge"]["in_frame"])
        self.assertTrue(r["nearest_mass"]["floor_contact_in_frame"])

    def test_the_camera_of_record_reproduces_its_own_claim(self):
        """THE ROW THAT MATTERS AFTER 2026-08-26. The owner's camera (D-152) says in
        its own note that it contains the slat wall's top and the nearest mass's floor
        contact. A camera whose stated reason no longer holds is a typed camera wearing
        a derivation, so the claim is re-solved from the spec on every test run — if a
        mass moves, or someone hand-retunes the lens, this fails instead of drifting."""
        spec = _spec()
        rep = fg.framing_report(spec, _record_cam())
        self.assertTrue(rep["top_edge"]["in_frame"],
                        "the camera of record no longer contains the slat wall's top")
        self.assertTrue(rep["nearest_mass"]["floor_contact_in_frame"],
                        "the camera of record no longer contains the nearest mass's "
                        "floor contact")

    def test_the_record_camera_height_comes_from_the_spec_not_a_shell(self):
        """His framing only holds at 1.05 m and it spent its A/B life as an env var.
        The height must travel with the camera (D-032 / R13), so the spec carries it
        and the resolver must prefer it over the module default."""
        import camera_config
        spec = _spec()
        self.assertIn("eye_h_m", spec["eye_camera"],
                      "the record camera's lens height is not in the spec — it is one "
                      "forgotten shell prefix away from re-cropping the room")
        self.assertAlmostEqual(camera_config.spec_eye_h_m(spec),
                               float(spec["eye_camera"]["eye_h_m"]), places=6)
        self.assertNotAlmostEqual(camera_config.spec_eye_h_m(spec),
                                  camera_config.DEFAULT_EYE_CAM_HEIGHT_M, places=6)

    def test_the_outgoing_camera_is_preserved_verbatim_as_the_reversal(self):
        """D-152's reverse_by names a key; the key must exist and must still be the
        block that shipped, or the reversal is a sentence rather than a path."""
        v = (_spec().get("eye_camera_variants") or {}).get("bed_foot_hero_2026-08-22")
        self.assertIsNotNone(v, "the outgoing camera of record left the spec")
        self.assertEqual(list(v["stand_mm"]), [1400, 1125])
        self.assertEqual(float(v["lens_mm"]), 26.0)
        self.assertAlmostEqual(float(v["shift_y"]), -0.14, places=6)


if __name__ == "__main__":
    unittest.main()


# ------------------------------------------------------------------- behind_camera

def _two_wall_spec():
    return {"room": {"ceiling_mm": 2800},
            "builtins": [
                {"name": "back_wall", "kind": "wall", "x": 0, "y": 0,
                 "w": 4000, "d": 100, "h": 2800},
                {"name": "front_wall", "kind": "wall", "x": 0, "y": 5000,
                 "w": 4000, "d": 100, "h": 2800}],
            "items": []}


def test_behind_camera_finds_the_wall_the_frame_cannot_show():
    # The camera stands at y=4 looking at y=0, so the wall at y=5 is behind it. It never
    # appears in the render and it is the surface most of the fill light comes off.
    r = fg.behind_camera(_two_wall_spec(),
                         {"ex": 2.0, "ey": 4.0, "tx": 2.0, "ty": 0.0, "eye_h": 1.6})
    assert [b["name"] for b in r["behind"]] == ["front_wall"]
    assert r["area_m2"] > 10.0
    assert r["open"] is False


def test_behind_camera_follows_the_aim_not_a_naming_convention():
    r = fg.behind_camera(_two_wall_spec(),
                         {"ex": 2.0, "ey": 0.5, "tx": 2.0, "ty": 5.0, "eye_h": 1.6})
    assert [b["name"] for b in r["behind"]] == ["back_wall"]


def test_a_mass_that_straddles_the_eye_plane_is_not_behind_it():
    # THE REFUSAL THAT KEEPS THIS HONEST. Side walls run past the camera on both sides;
    # counting them as "behind" would report a closed room in every scene ever built.
    r = fg.behind_camera(_two_wall_spec(),
                         {"ex": 2.0, "ey": 2.5, "tx": 4.0, "ty": 2.5, "eye_h": 1.6})
    assert r["behind"] == []
    assert r["open"] is True


def test_an_open_room_is_reported_not_failed():
    r = fg.behind_camera({"room": {}, "builtins": [], "items": []},
                         {"ex": 0.0, "ey": 0.0, "tx": 1.0, "ty": 0.0, "eye_h": 1.6})
    assert r["open"] is True
    assert r["area_m2"] == 0.0
