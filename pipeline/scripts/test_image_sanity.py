#!/usr/bin/env python3
"""test_image_sanity.py — deterministic proof of the Gate 1 image-sanity metrics.

Pins the metric COMPUTATION with synthetic grids (no numpy/Pillow/files): a
blurred image scores lower Laplacian variance than its sharp source; an all-white
frame clips high; a flat frame is blank; a sharp mid-exposure varied frame PASSes.
These are robust relative/extreme facts, independent of the DRAFT absolute cutoffs.

Run: python pipeline/scripts/test_image_sanity.py   (prints N/N, exit 0/1)
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import image_sanity as S  # noqa: E402


# --- synthetic luminance grids (row-major flat lists) ---
def flat(w, h, val):
    return [float(val)] * (w * h)


def checkerboard(w, h, a=100, b=160):
    return [float(a if (x + y) % 2 == 0 else b) for y in range(h) for x in range(w)]


def h_gradient(w, h):
    return [float(int(255 * x / (w - 1))) for _y in range(h) for x in range(w)]


def box_blur(g, w, h):
    out = [0.0] * (w * h)
    for y in range(h):
        for x in range(w):
            s = c = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        s += g[ny * w + nx]
                        c += 1
            out[y * w + x] = s / c
    return out


def _status_of(result, check):
    return next(c["status"] for c in result["checks"] if c["check"] == check)


# --- tests ---
def test_blur_sharp_scores_higher_than_blurred():
    w = h = 20
    sharp = checkerboard(w, h)
    blurred = box_blur(sharp, w, h)
    assert S.laplacian_variance(sharp, w, h) > S.laplacian_variance(blurred, w, h)
    assert S.laplacian_variance(flat(w, h, 128), w, h) == 0.0


def test_flat_frame_is_blank_and_blurry_fail():
    r = S.assess(flat(20, 20, 128), 20, 20)
    assert r["status"] == S.FAIL
    assert _status_of(r, "blank") == S.FAIL and _status_of(r, "blur") == S.FAIL


def test_all_white_and_all_black_fail_exposure():
    white = S.assess(flat(20, 20, 255), 20, 20)
    assert _status_of(white, "exposure") == S.FAIL and white["status"] == S.FAIL
    black = S.assess(flat(20, 20, 0), 20, 20)
    assert _status_of(black, "exposure") == S.FAIL and black["status"] == S.FAIL


def test_sharp_mid_exposure_varied_frame_passes():
    # checkerboard 100/160: high-frequency edges, mean ~130, no clipping, good std
    r = S.assess(checkerboard(20, 20), 20, 20)
    assert r["status"] == S.PASS, r["detail"]
    assert _status_of(r, "blur") == S.PASS and _status_of(r, "exposure") == S.PASS
    assert _status_of(r, "blank") == S.PASS


def test_gradient_exposure_ok_not_blank():
    r = S.assess(h_gradient(40, 10), 40, 10)
    assert _status_of(r, "exposure") == S.PASS   # full ramp: mean ~127, ends clip but < fail %
    assert _status_of(r, "blank") == S.PASS      # a ramp has real variance


def test_metrics_reported():
    r = S.assess(checkerboard(10, 10), 10, 10)
    for k in ("laplacian_var", "clipped", "mean", "std"):
        assert k in r["metrics"], f"missing metric {k}"


def test_bounds_are_ordered():
    b = S.BOUNDS
    assert b["blur_var_fail"] < b["blur_var_warn"]
    assert b["blank_std_fail"] < b["blank_std_warn"]
    assert b["clip_pct_warn"] < b["clip_pct_fail"]
    assert b["mean_dark_fail"] < b["mean_bright_fail"]


def test_low_lv_but_contrasty_is_not_fail():
    # SCRUTINY FIX: a smooth-but-contrasty frame (minimalist wall / gradient) has
    # near-zero Laplacian variance yet healthy std — it must NOT blur-FAIL (that
    # would reseed a valid render); a truly flat frame (low std too) still FAILs.
    smooth = h_gradient(40, 20)              # lv ~0 but std high
    assert _status_of(S.assess(smooth, 40, 20), "blur") != S.FAIL
    assert _status_of(S.assess(flat(20, 20, 128), 20, 20), "blur") == S.FAIL  # flat = still mush


def test_partial_bounds_override_falls_back_per_key():
    # SCRUTINY FIX: a partial bounds dict must merge over defaults, not KeyError.
    r = S.assess(checkerboard(10, 10), 10, 10, bounds={"blur_var_fail": 1.0})
    assert r["status"] in (S.PASS, S.WARN)   # ran without KeyError on the absent keys


def test_real_render_gs01_passes():
    # real-data anchor: a real furnished interior render must read sane, not
    # false-FAIL — a regression guard for the DRAFT bounds beyond synthetic grids.
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gs01 = os.path.join(root, "assets", "qa", "golden-set", "GS-01.png")
    if not os.path.exists(gs01):
        return  # golden set not materialized (LFS) — skip
    r = S.sanity_of_image(gs01)
    if r is None:
        return  # Pillow missing — loader UNWIRED, skip
    assert r["status"] == S.PASS, f"real render GS-01 must PASS, got {r['detail']}"
    m = r["metrics"]
    assert m["laplacian_var"] > 100 and 40 < m["mean"] < 220 and m["clipped"] < 0.1


def test_loader_is_crash_safe():
    # sanity_of_image must return None (UNWIRED), never raise, on a bad candidate
    assert S.sanity_of_image(os.path.join(tempfile.gettempdir(), "does_not_exist_xyz.png")) is None
    d = tempfile.mkdtemp(prefix="imgsanity_")
    p = os.path.join(d, "not_an_image.png")
    with open(p, "w", encoding="utf-8") as f:
        f.write("this is text, not a PNG")
    try:
        assert S.sanity_of_image(p) is None, "unreadable candidate must degrade to None, not raise"
    finally:
        shutil.rmtree(d, ignore_errors=True)


TESTS = [test_blur_sharp_scores_higher_than_blurred, test_flat_frame_is_blank_and_blurry_fail,
         test_all_white_and_all_black_fail_exposure, test_sharp_mid_exposure_varied_frame_passes,
         test_gradient_exposure_ok_not_blank, test_metrics_reported, test_bounds_are_ordered,
         test_low_lv_but_contrasty_is_not_fail, test_partial_bounds_override_falls_back_per_key,
         test_real_render_gs01_passes, test_loader_is_crash_safe]


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
