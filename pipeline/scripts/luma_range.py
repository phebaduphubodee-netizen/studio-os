"""luma_range — the value RANGE of a frame as p95/p5 of gamma-encoded luminance.

The number the sighted panel of 2026-09-01 measured at 3.3x on ours against 5.0-5.4x
on every delivered peer (audit-2026-09-01-project-overview.md §A). Flatness is a
range, not a brightness (lighting-design skill), so the gate reads a RATIO of two
percentiles and never a mean.

Method, fixed so the number is comparable across rounds and with the peers:
  - PIL open, RGB, resized to LONG EDGE 1600 with LANCZOS (the peers were measured
    at 1600 — a percentile at a different pixel count is a different measurement;
    R11's "could not look" rule applies to a mismatched size, so a frame SMALLER
    than the long edge is refused with exit 2 unless --allow-upscale names the
    playblast use)
  - L = 0.2126 R + 0.7152 G + 0.0722 B on the encoded values / 255 (no
    linearisation — the panel's number is on the encoded image, i.e. what the eye
    was shown)
  - p5, p95 = numpy percentiles over all pixels; ratio = p95 / max(p5, 1e-3)

Exit codes (a contract, R11): 0 = ratio >= --min, 1 = under, 2 = COULD NOT RUN.
"""
from __future__ import annotations

import argparse
import json
import sys

LONG_EDGE = 1600
DEFAULT_MIN = 5.0


def measure(path, long_edge=LONG_EDGE, allow_upscale=False):
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("RGB")
    w, h = im.size
    le = max(w, h)
    native = False
    if le < long_edge:
        if not allow_upscale:
            raise RuntimeError(f"{path}: long edge {le} px is under {long_edge} — a "
                               f"percentile at another pixel count is another "
                               f"measurement (pass --allow-upscale for a playblast "
                               f"reading that is NOT a gate reading)")
        native = True
    elif le > long_edge:
        sc = long_edge / float(le)
        im = im.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float64) / 255.0
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    p5, p50, p95 = (float(v) for v in np.percentile(L, [5, 50, 95]))
    return {"path": str(path), "measured_at": list(im.size), "native_size": [w, h],
            "upscale_refused": False, "measured_native": native,
            "p5": p5, "p50": p50, "p95": p95, "ratio": p95 / max(p5, 1e-3),
            "dark_share_lt_0_08": float((L < 0.08).mean()),
            "bright_share_gt_0_90": float((L > 0.90).mean())}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("images", nargs="+")
    ap.add_argument("--min", type=float, default=DEFAULT_MIN,
                    help=f"pass floor for p95/p5 (default {DEFAULT_MIN}, the peers' floor)")
    ap.add_argument("--long-edge", type=int, default=LONG_EDGE)
    ap.add_argument("--allow-upscale", action="store_true",
                    help="measure a smaller frame at native size (playblast bisect only)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rc = 0
    rows = []
    for p in a.images:
        try:
            r = measure(p, a.long_edge, a.allow_upscale)
        except Exception as e:                       # noqa: BLE001
            print(f"luma_range: COULD NOT RUN on {p}: {e}")
            rc = max(rc, 2)
            continue
        ok = r["ratio"] >= a.min
        r["min"] = a.min
        r["pass"] = ok
        rows.append(r)
        tag = "PASS" if ok else "UNDER"
        note = (" [NATIVE SIZE — playblast reading, not a gate reading]"
                if r["measured_native"] else "")
        print(f"luma_range {tag}: p95/p5 = {r['ratio']:.2f}x (p5 {r['p5']:.3f}, p50 "
              f"{r['p50']:.3f}, p95 {r['p95']:.3f}; <0.08: {100 * r['dark_share_lt_0_08']:.1f}%, "
              f">0.90: {100 * r['bright_share_gt_0_90']:.1f}%) floor {a.min:.1f}x — {p}{note}")
        if not ok:
            rc = max(rc, 1)
    if a.json:
        print(json.dumps(rows, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main())
