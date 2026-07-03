#!/usr/bin/env python3
"""image_sanity.py — deterministic no-reference Gate 1 image-execution check.

Gate 1 (blueprint §9.5 EXECUTION) is the cheapest failure: catch a raw render
that is obviously broken — blurred to mush, blown-out / crushed exposure, or a
near-blank frame — and route it to discard/reseed BEFORE spending the structure
gate or the paid LLM judge. This is NOT a perceptual quality score (BRISQUE); it
is a catastrophe floor. Subtle quality remains the LLM judge's job.

Deliberately NOT BRISQUE: a calibrated BRISQUE needs a trained SVR model + a
heavy dep and mis-scores clean AI renders (it is trained on natural photos). We
chose a deterministic, closed-form floor with no model — see the memory note
'brisque-deferred' for when to revisit BRISQUE (Gate 4 / post-upscaler artifacts).

Design mirrors delta_e00.py: the CORE is pure-python and operates on a flat
luminance grid, so it is fully testable with synthetic images and needs NO numpy
or Pillow. Only the real-image LOADER uses Pillow (lazy) — missing Pillow or an
unreadable file yields None, which the caller reads as UNWIRED (never a silent
pass).

BOUNDS ARE DRAFT: the Laplacian-variance / clip / std cutoffs are scale- and
content-dependent heuristics, hardcoded-with-citation here pending a real
calibration on studio renders and a PR into qa/thresholds.yaml (image_qa). The
TESTS pin the metric COMPUTATION (a blurred image scores lower than its sharp
source; an all-white frame clips high; a flat frame is blank) — robust relative
facts — not the absolute cutoffs.
"""
import math

# DRAFT bounds (pending qa/thresholds.yaml image_qa PR + calibration on real
# renders). Computed on a luminance grid downscaled to LOAD_MAX_SIDE.
BOUNDS = {
    "blur_var_fail": 8.0,     # Laplacian variance below this = mush/flat
    "blur_var_warn": 25.0,
    "clip_pct_fail": 0.45,    # >45% of pixels pinned at black or white = blown/crushed
    "clip_pct_warn": 0.25,
    "mean_dark_fail": 12.0,   # overall luminance floor/ceiling (0-255)
    "mean_bright_fail": 243.0,
    "blank_std_fail": 3.0,    # global std below this = near-uniform / empty frame
    "blank_std_warn": 8.0,
}
LOAD_MAX_SIDE = 200           # downscale before the pure-python passes (speed)
_BLACK, _WHITE = 2, 253       # clip thresholds (0-255)

PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"


def laplacian_variance(gray, w, h):
    """Variance of the 4-neighbour Laplacian over interior pixels. High = sharp
    (lots of edges), near-zero = flat/blurred. gray = flat row-major luminance."""
    if w < 3 or h < 3:
        return 0.0
    vals = []
    for y in range(1, h - 1):
        row = y * w
        for x in range(1, w - 1):
            i = row + x
            lap = 4.0 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - w] - gray[i + w]
            vals.append(lap)
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return sum((v - m) ** 2 for v in vals) / n


def exposure_stats(gray):
    """Fraction of pixels clipped at black / white, and the mean luminance."""
    n = len(gray) or 1
    low = sum(1 for v in gray if v <= _BLACK) / n
    high = sum(1 for v in gray if v >= _WHITE) / n
    return {"clipped_low": low, "clipped_high": high, "mean": sum(gray) / n}


def blankness_std(gray):
    """Population std of luminance — near-zero = a uniform / empty frame."""
    n = len(gray) or 1
    m = sum(gray) / n
    return math.sqrt(sum((v - m) ** 2 for v in gray) / n)


def _worst(statuses):
    if FAIL in statuses:
        return FAIL
    if WARN in statuses:
        return WARN
    return PASS


def assess(gray, w, h, bounds=None):
    """Run the three deterministic checks over a luminance grid. Returns
    {status, checks[], detail, metrics}."""
    b = {**BOUNDS, **(bounds or {})}   # partial overrides fall back per-key (no KeyError)
    lv = laplacian_variance(gray, w, h)
    exp = exposure_stats(gray)
    std = blankness_std(gray)
    clip = max(exp["clipped_low"], exp["clipped_high"])

    checks = []
    # blur — a low Laplacian FAILs only when the frame is ALSO flat (low global std):
    # true blur-to-mush is edgeless AND low-contrast. A low-lv but contrasty frame is
    # "smooth content" (a minimalist plaster wall, soft gradient) — that is the LLM
    # judge's aesthetic call, so it WARNs, never a reseed-forcing FAIL. This also keeps
    # the blur and blank checks non-redundant.
    if lv < b["blur_var_fail"] and std < b["blank_std_warn"]:
        blur_status = FAIL
    elif lv < b["blur_var_warn"]:
        blur_status = WARN
    else:
        blur_status = PASS
    checks.append({"check": "blur", "status": blur_status,
                   "detail": f"laplacian_var {lv:.1f} std {std:.1f} "
                             f"(fail = lv<{b['blur_var_fail']} AND std<{b['blank_std_warn']}; warn lv<{b['blur_var_warn']})"})
    # exposure (clip % and mean floor/ceiling)
    if clip > b["clip_pct_fail"] or exp["mean"] < b["mean_dark_fail"] or exp["mean"] > b["mean_bright_fail"]:
        exp_status = FAIL
    elif clip > b["clip_pct_warn"]:
        exp_status = WARN
    else:
        exp_status = PASS
    checks.append({"check": "exposure", "status": exp_status,
                   "detail": f"clip {clip*100:.0f}% mean {exp['mean']:.0f} "
                             f"(fail clip>{b['clip_pct_fail']*100:.0f}% or mean<{b['mean_dark_fail']}/>{b['mean_bright_fail']})"})
    # blank
    blank_status = FAIL if std < b["blank_std_fail"] else (WARN if std < b["blank_std_warn"] else PASS)
    checks.append({"check": "blank", "status": blank_status,
                   "detail": f"std {std:.1f} (fail<{b['blank_std_fail']}, warn<{b['blank_std_warn']})"})

    status = _worst([c["status"] for c in checks])
    failed = [c["check"] for c in checks if c["status"] == FAIL]
    warned = [c["check"] for c in checks if c["status"] == WARN]
    detail = (f"image sanity {status}"
              + (f" — FAIL: {', '.join(failed)}" if failed else "")
              + (f" — WARN: {', '.join(warned)}" if warned else ""))
    return {"status": status, "checks": checks, "detail": detail,
            "metrics": {"laplacian_var": round(lv, 2), "clipped": round(clip, 3),
                        "mean": round(exp["mean"], 1), "std": round(std, 2)}}


def luma_from_image(path, max_side=LOAD_MAX_SIDE):
    """Load a render as a downscaled flat luminance grid (Pillow, lazy). Returns
    (gray, w, h) or None if Pillow is missing / the file is unreadable — the
    caller must read None as UNWIRED, never a silent pass."""
    try:
        from PIL import Image
        im = Image.open(path).convert("L")
        w, h = im.size
        if max(w, h) > max_side:
            scale = max_side / float(max(w, h))
            w, h = max(1, int(w * scale)), max(1, int(h * scale))
            im = im.resize((w, h))
        # get_flattened_data() on new Pillow (>=12), getdata() on older — both give
        # a flat row-major luminance sequence for an "L" image
        data = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
        return list(data), w, h
    except Exception:  # noqa: BLE001 — missing dep OR unreadable candidate -> UNWIRED
        return None


def sanity_of_image(path, bounds=None):
    """Real-image entry: load + assess, or None (UNWIRED) on any failure."""
    loaded = luma_from_image(path)
    if loaded is None:
        return None
    gray, w, h = loaded
    return assess(gray, w, h, bounds)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("usage: python image_sanity.py IMAGE.png")
    r = sanity_of_image(sys.argv[1])
    if r is None:
        print("UNWIRED (Pillow missing or unreadable image)")
        sys.exit(2)
    print(r["detail"])
    print("  metrics:", r["metrics"])
    sys.exit(0 if r["status"] != FAIL else 1)
