#!/usr/bin/env python3
"""test_camera_config.py — pin the eye-camera height + its coupled LOS threshold.

The height change (1.5 -> 1.15 m, M3.2 designer GS-15) is designer-specified, not an
aesthetic guess — so these tests assert (a) it sits in the designer's stated band,
(b) the ray-block threshold stays COUPLED to it (the latent-bug fix), and (c) the
change is SOLVE-NEUTRAL for the production specs: no built-in height sits in the band
between the old and new thresholds, so the eye camera's standing-spot solve is
byte-for-byte identical — only the eye Z drops. That is the deterministic guarantee I
can make WITHOUT rendering; the aesthetic win itself is a designer render A/B, never
the (decalibrated) LLM judge.

Run: python pipeline/scripts/test_camera_config.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera_config as C  # noqa: E402

_OLD_EYE = 1.5    # the literal this change replaced (build_room add_suite_eye_camera)
_OLD_RAY = 1.55   # the literal ray-block threshold it was independently coupled to


def test_default_height_in_designer_band():
    lo, hi = C.DESIGNER_BAND_M
    assert lo <= C.DEFAULT_EYE_CAM_HEIGHT_M <= hi, C.DEFAULT_EYE_CAM_HEIGHT_M


def test_ray_threshold_is_coupled_to_eye_height():
    # the whole point: threshold tracks the height (was two independent literals)
    assert C.RAY_BLOCK_MIN_H_M == C.eye_cam_height_m() + C.RAY_BLOCK_MARGIN_M
    assert abs(C.ray_block_min_h_m(1.15) - 1.20) < 1e-9
    # the OLD pairing is reproducible from the same coupling (1.5 -> 1.55)
    assert abs(C.ray_block_min_h_m(_OLD_EYE) - _OLD_RAY) < 1e-9


def test_env_override_enables_render_ab():
    os.environ["EYE_CAM_HEIGHT_M"] = "1.5"
    try:
        assert abs(C.eye_cam_height_m() - 1.5) < 1e-9
        assert abs(C.ray_block_min_h_m() - _OLD_RAY) < 1e-9   # A/B reproduces old exactly
    finally:
        del os.environ["EYE_CAM_HEIGHT_M"]


def test_bad_env_value_falls_back_to_default():
    os.environ["EYE_CAM_HEIGHT_M"] = "tall-please"
    try:
        assert C.eye_cam_height_m() == C.DEFAULT_EYE_CAM_HEIGHT_M
    finally:
        del os.environ["EYE_CAM_HEIGHT_M"]


def test_height_change_is_solve_neutral_for_production_specs():
    # PROOF the 1.5->1.15 change does not move the eye camera's standing-spot for our
    # real rooms: the only solve input that depends on height is which BUILT-IN blocks
    # the level ray (items never ray-block — build_room add_suite_eye_camera). Old
    # threshold 1.55, new ~1.20. If no built-in height lands in [new, old), the blocker
    # set is identical -> same spot, same lens, only eye Z drops. Also GUARDS a future
    # spec that adds a mid-height built-in: that WOULD alter the frame and must be
    # re-gated on a designer render, so this test would (correctly) fail and force it.
    new = C.ray_block_min_h_m(C.DEFAULT_EYE_CAM_HEIGHT_M)     # ~1.20
    specs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs")
    checked = 0
    for f in ("bedroom_suite.json", "living_condo.json"):
        p = os.path.join(specs, f)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        for b in d.get("builtins", []):
            h_m = float(b.get("h", 0)) * 0.001
            assert not (new <= h_m < _OLD_RAY), (
                f"{f}: built-in {b.get('kind')} h={h_m:.2f}m is in the disturbed band "
                f"[{new:.2f},{_OLD_RAY})  -> the height change moves the LOS solve; "
                f"re-gate with a designer render before shipping")
            checked += 1
    assert checked > 0, "no production specs found to prove solve-neutrality"


def _elems():
    # a pool exercising the EYE_AIM priority: a wall 'tv' AND a 'tv_console', two wardrobes
    return [{"kind": "tv_console", "name": "media console", "x": 6, "y": 6, "w": 1400, "d": 400},
            {"kind": "sofa", "name": "big sofa", "x": 100, "y": 100, "w": 2000, "d": 900},
            {"kind": "tv", "name": "wall tv", "x": 200, "y": 0, "w": 1200, "d": 60},
            {"kind": "wardrobe", "name": "closet A", "x": 0, "y": 0, "w": 600, "d": 2000},
            {"kind": "wardrobe", "name": "closet B", "x": 0, "y": 2100, "w": 600, "d": 2000}]


def test_eye_aim_unset_returns_none():
    assert C.select_aim_element(_elems(), None) is None
    assert C.select_aim_element(_elems(), "") is None
    assert C.select_aim_element(_elems(), "   ") is None


def test_eye_aim_exact_kind_beats_substring():
    # EYE_AIM=tv must pick the wall 'tv' (exact kind), NOT the 'tv_console' that appears first
    el = C.select_aim_element(_elems(), "tv")
    assert el["kind"] == "tv" and el["name"] == "wall tv"


def test_eye_aim_substring_when_no_exact():
    el = C.select_aim_element(_elems(), "console")     # substring only
    assert el["kind"] == "tv_console"


def test_eye_aim_no_match_raises():
    try:
        C.select_aim_element(_elems(), "fireplace")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_eye_aim_missing_bbox_raises():
    try:
        C.select_aim_element([{"kind": "tv", "name": "screen"}], "tv")   # no x/y/w/d
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_eye_aim_null_kind_not_matched_as_none_string():
    # a null kind must not become the string "none" and match EYE_AIM=one/non
    pool = [{"kind": None, "name": None, "x": 0, "y": 0, "w": 100, "d": 100}]
    try:
        C.select_aim_element(pool, "one")
        assert False, "expected ValueError (no spurious 'none' match)"
    except ValueError:
        pass


# ---------- solve_eye_camera (the extracted pure solve, shared with build_room) ----------

def _load(name):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", name)
    return json.load(open(p, encoding="utf-8"))


def test_solve_production_specs_pinned():
    # REGRESSION PINS on the render-affecting outputs (aim, standing spot, lens). These are
    # the exact values the inline build_room solve produced before extraction — the guarantee
    # the refactor is behaviour-identical. A change here means the camera MOVED and must be
    # re-gated on a designer render, not silently accepted.
    b = C.solve_eye_camera(_load("bedroom_suite.json"))
    assert abs(b["ex"] - 1.2) < 1e-6 and abs(b["ey"] - 3.2) < 1e-6, (b["ex"], b["ey"])
    assert abs(b["tx"] - 4.2) < 1e-9 and abs(b["ty"] - 2.096) < 1e-9, (b["tx"], b["ty"])
    assert b["lens_mm"] == 26.0 and abs(b["standoff_m"] - 3.1967) < 1e-3, b
    assert b["hero"]["kind"] == "platform"

    l = C.solve_eye_camera(_load("living_condo.json"))
    assert abs(l["ex"] - 0.8) < 1e-6 and abs(l["ey"] - 0.4) < 1e-6, (l["ex"], l["ey"])
    assert abs(l["tx"] - 2.6) < 1e-9 and abs(l["ty"] - 4.8) < 1e-9, (l["tx"], l["ty"])
    assert l["lens_mm"] == 35.0 and abs(l["standoff_m"] - 4.7539) < 1e-3, l
    # largest overall = the lounge rug the sofa sits on -> aim = rug centre, hero = the sofa
    assert l["hero"]["kind"] == "sofa" and l["main"]["kind"] == "rug"


def test_solve_no_loose_item_raises():
    spec = {"room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}, "items": []}
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (no loose item to aim at)"
    except C.EyeCameraError as e:
        assert "loose item" in str(e)


def test_solve_packed_room_raises_no_clear_spot():
    # a full-height built-in fills the room -> every grid candidate is within 0.3 m of it,
    # so NO clear standing spot exists. build_room would SystemExit here; the gate FAILs.
    spec = {"room": {"outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "builtins": [{"kind": "wall", "x": 200, "y": 200, "w": 1600, "d": 1600, "h": 2800}],
            "items": [{"kind": "bed", "x": 600, "y": 600, "w": 800, "d": 800, "h": 600}]}
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (no clear standing spot)"
    except C.EyeCameraError as e:
        assert "no clear standing spot" in str(e)


def test_solve_bad_eye_aim_raises():
    spec = _load("bedroom_suite.json")
    os.environ["EYE_AIM"] = "fireplace"
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (EYE_AIM matches nothing)"
    except C.EyeCameraError as e:
        assert "matched no" in str(e)
    finally:
        del os.environ["EYE_AIM"]


def test_subject_share_high_for_a_real_hero_shot():
    # both production eye shots frame the furniture group, not a wall -> high subject share
    for name, floor in (("bedroom_suite.json", 0.9), ("living_condo.json", 0.5)):
        spec = _load(name)
        sol = C.solve_eye_camera(spec)
        share = C.frame_subject_share(spec, sol)
        assert share >= floor, f"{name}: subject share {share:.3f} < {floor}"


def test_frame_fov_matches_36mm_horizontal_sensor():
    # PIN the sensor half-width (scrutiny 2026-07-04): _H_SENSOR_HALF_MM must be 18 mm (half of
    # a 36 mm horizontal sensor). The classic mistake is using 36 (the full width) as the half,
    # which DOUBLES the FOV (~108° at 26 mm) yet leaves the loose one-directional share floors
    # green. Pin the actual FOV angle so that doubling is caught.
    import math
    for lens, expect_deg in ((26.0, 69.4), (35.0, 54.4), (50.0, 39.6)):
        hfov = math.degrees(2 * math.atan2(C._H_SENSOR_HALF_MM, lens))
        assert abs(hfov - expect_deg) < 0.6, (lens, hfov)


def test_ray_block_is_mount_aware():
    # PROVE the ray-block reads mount_mm, not just h (scrutiny 2026-07-04: build_room now floats
    # built-ins from z=mount_mm, so a wall panel h=800 mount=900 spans 900–1700 mm and DOES cross
    # a 1.15 m lens). A/B on a room split by a full-width mid partition, subject in the thin north
    # strip: a FLOATED partition (spans the lens) occludes every south sightline -> no shot; the
    # SAME partition on the FLOOR (0–800 mm, below the lens) does not -> a shot exists.
    def room(mount):
        return {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 2500], [0, 2500]]},
                "builtins": [{"kind": "partition", "name": "panel", "x": 0, "y": 2000,
                              "w": 4000, "d": 50, "h": 800, "mount_mm": mount}],
                "items": [{"kind": "stool", "name": "target", "x": 1800, "y": 2250,
                           "w": 400, "d": 200, "h": 450}]}
    try:
        C.solve_eye_camera(room(900))       # floated across the lens -> occludes the only sightline
        assert False, "expected EyeCameraError (floated panel spans eye level and blocks the ray)"
    except C.EyeCameraError:
        pass
    sol = C.solve_eye_camera(room(0))       # on the floor, below the lens -> transparent to the ray
    assert sol["standoff_m"] > 0.5, sol


def test_subject_share_low_for_a_dead_wall_frame():
    # a big empty room with a lone tiny stool in a corner: the far standing spot frames
    # almost all bare wall -> low subject share (the dead-wall signal the WARN path uses)
    spec = {"room": {"outline_mm": [[0, 0], [8000, 0], [8000, 8000], [0, 8000]]},
            "items": [{"kind": "stool", "x": 200, "y": 200, "w": 400, "d": 400, "h": 450}]}
    sol = C.solve_eye_camera(spec)
    share = C.frame_subject_share(spec, sol)
    assert share < 0.15, f"expected a dead-wall (low) share, got {share:.3f}"


# ---------- manual eye_camera override (spec["eye_camera"], for L-shaped suites) ----------

def _manual_room():
    """A 5x5 m room, a low bed in the east half, a full-height wardrobe on the north wall —
    an open floor with one tall ray-blocker, enough to exercise place + validate."""
    return {"room": {"outline_mm": [[0, 0], [5000, 0], [5000, 5000], [0, 5000]]},
            "builtins": [{"kind": "wardrobe", "name": "wd", "x": 0, "y": 0, "w": 5000, "d": 600, "h": 2800}],
            "items": [{"kind": "bed", "name": "bed", "x": 3000, "y": 2000, "w": 1800, "d": 2000, "h": 600}]}


def test_manual_override_places_exact_camera():
    # stand_mm + aim_mm + lens_mm are honoured verbatim (mm -> m); manual flag set; auto grid skipped
    spec = _manual_room()
    spec["eye_camera"] = {"stand_mm": [1000, 3000], "aim_mm": [3900, 3000], "lens_mm": 28}
    sol = C.solve_eye_camera(spec)
    assert sol["manual"] is True
    assert abs(sol["ex"] - 1.0) < 1e-9 and abs(sol["ey"] - 3.0) < 1e-9, (sol["ex"], sol["ey"])
    assert abs(sol["tx"] - 3.9) < 1e-9 and abs(sol["ty"] - 3.0) < 1e-9, (sol["tx"], sol["ty"])
    assert sol["lens_mm"] == 28 and abs(sol["standoff_m"] - 2.9) < 1e-9, sol


def test_manual_override_shift_y_passthrough():
    # shift_y is carried on the solve for build_room to apply; absent -> None (build_room's default)
    spec = _manual_room()
    spec["eye_camera"] = {"stand_mm": [1000, 3000], "aim_mm": [3900, 3000], "shift_y": -0.20}
    assert abs(C.solve_eye_camera(spec)["shift_y"] + 0.20) < 1e-9
    spec["eye_camera"] = {"stand_mm": [1000, 3000], "aim_mm": [3900, 3000]}
    assert C.solve_eye_camera(spec)["shift_y"] is None


def test_manual_override_aim_by_substring():
    # "aim" names the subject by kind/name; tx,ty become its centre and hero follows
    spec = _manual_room()
    spec["eye_camera"] = {"stand_mm": [1000, 3000], "aim": "bed"}
    sol = C.solve_eye_camera(spec)
    assert sol["hero"]["kind"] == "bed"
    assert abs(sol["tx"] - 3.9) < 1e-9 and abs(sol["ty"] - 3.0) < 1e-9, (sol["tx"], sol["ty"])
    # no lens_mm given -> hero-sized snap from _LENS_SNAP
    assert sol["lens_mm"] in C._LENS_SNAP


def test_manual_override_inert_without_key():
    # no eye_camera key -> the auto grid solve runs unchanged, manual flag False
    b = C.solve_eye_camera(_load("bedroom_suite.json"))
    assert b.get("manual") is False
    assert abs(b["ex"] - 1.2) < 1e-6 and abs(b["ey"] - 3.2) < 1e-6   # same pin as the auto test


def test_manual_override_rejects_no_line_of_sight():
    # a full-height partition splits the room; stand on the far side of the subject -> the level
    # ray crosses the partition (a ray-block) -> the SAME safety net the auto solve uses fires
    spec = {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]},
            "builtins": [{"kind": "partition", "name": "p", "x": 2000, "y": 0, "w": 100, "d": 3000, "h": 2800}],
            "items": [{"kind": "stool", "name": "s", "x": 3000, "y": 1400, "w": 400, "d": 200, "h": 450}]}
    spec["eye_camera"] = {"stand_mm": [1000, 1500], "aim": "stool"}   # west of the wall, subject east
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (manual spot has no line of sight past the partition)"
    except C.EyeCameraError as e:
        assert "line of sight" in str(e)


def test_manual_override_rejects_too_close():
    spec = {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": [{"kind": "stool", "name": "s", "x": 100, "y": 100, "w": 300, "d": 300, "h": 450}]}
    spec["eye_camera"] = {"stand_mm": [2000, 2000], "aim_mm": [2300, 2000]}   # 0.3 m standoff
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (standoff < 0.5 m)"
    except C.EyeCameraError as e:
        assert "standoff" in str(e)


def test_manual_override_rejects_bad_lens():
    spec = _manual_room()
    spec["eye_camera"] = {"stand_mm": [1000, 3000], "aim_mm": [3900, 3000], "lens_mm": 0}
    try:
        C.solve_eye_camera(spec)
        assert False, "expected EyeCameraError (lens_mm must be > 0)"
    except C.EyeCameraError as e:
        assert "lens_mm" in str(e)


TESTS = [test_default_height_in_designer_band, test_ray_threshold_is_coupled_to_eye_height,
         test_env_override_enables_render_ab, test_bad_env_value_falls_back_to_default,
         test_height_change_is_solve_neutral_for_production_specs,
         test_eye_aim_unset_returns_none, test_eye_aim_exact_kind_beats_substring,
         test_eye_aim_substring_when_no_exact, test_eye_aim_no_match_raises,
         test_eye_aim_missing_bbox_raises, test_eye_aim_null_kind_not_matched_as_none_string,
         test_solve_production_specs_pinned, test_solve_no_loose_item_raises,
         test_solve_packed_room_raises_no_clear_spot, test_solve_bad_eye_aim_raises,
         test_frame_fov_matches_36mm_horizontal_sensor, test_ray_block_is_mount_aware,
         test_subject_share_high_for_a_real_hero_shot, test_subject_share_low_for_a_dead_wall_frame,
         test_manual_override_places_exact_camera, test_manual_override_shift_y_passthrough,
         test_manual_override_aim_by_substring,
         test_manual_override_inert_without_key, test_manual_override_rejects_no_line_of_sight,
         test_manual_override_rejects_too_close, test_manual_override_rejects_bad_lens]


def main():
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
