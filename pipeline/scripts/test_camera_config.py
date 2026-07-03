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


TESTS = [test_default_height_in_designer_band, test_ray_threshold_is_coupled_to_eye_height,
         test_env_override_enables_render_ab, test_bad_env_value_falls_back_to_default,
         test_height_change_is_solve_neutral_for_production_specs,
         test_eye_aim_unset_returns_none, test_eye_aim_exact_kind_beats_substring,
         test_eye_aim_substring_when_no_exact, test_eye_aim_no_match_raises,
         test_eye_aim_missing_bbox_raises, test_eye_aim_null_kind_not_matched_as_none_string]


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
