#!/usr/bin/env python3
"""edgefit.py - sub-pixel line fit along a near-horizontal image edge.

WHY THIS EXISTS. fSpy asks you to place vanishing-point lines by eye. On a 1440x1920
photo a 2 px error at one end of a 400 px baseline moves the vanishing point by
thousands of pixels, and three of my own eyeball reads disagreed about which side the
horizon was on. The eye names WHICH edge to fit; this names WHERE it is.

Method: walk x across the segment, at each x take a column window around the current
line estimate, convolve with a 1-D derivative, take the extremum of the |gradient|
with parabolic sub-pixel refinement, then robust (Huber/IRLS) least-squares fit.
Re-run twice so the window recentres on the fitted line.
"""
import json
import sys

import numpy as np
from PIL import Image


def luma(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float64)
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def _subpix_extremum(v, i):
    """Parabolic peak of |v| around index i. Returns fractional offset in [-1,1]."""
    if i <= 0 or i >= len(v) - 1:
        return 0.0
    a, b, c = v[i - 1], v[i], v[i + 1]
    den = a - 2 * b + c
    if abs(den) < 1e-12:
        return 0.0
    return float(np.clip(0.5 * (a - c) / den, -1.0, 1.0))


def fit(img, p0, p1, half=9, nsamp=None, sign=0, passes=3):
    """p0,p1: (x,y) endpoints bracketing a near-horizontal edge.

    sign: +1 keep only dark->bright downward gradients, -1 only bright->dark, 0 = |grad|.
    Returns dict with slope m, intercept b (y = m*x + b), rms residual, n points.
    """
    L = luma(img) if isinstance(img, str) else img
    H, W = L.shape
    x0, y0 = p0
    x1, y1 = p1
    if x1 < x0:
        x0, y0, x1, y1 = x1, y1, x0, y0
    n = nsamp or max(24, int((x1 - x0) / 4))
    xs = np.linspace(x0, x1, n)
    m = (y1 - y0) / max(1e-9, (x1 - x0))
    b = y0 - m * x0
    kernel = np.array([-1.0, -2.0, 0.0, 2.0, 1.0]) / 8.0
    res = None
    for _ in range(passes):
        pts = []
        for x in xs:
            xi = int(round(x))
            if xi < 1 or xi >= W - 1:
                continue
            yc = m * x + b
            lo = int(round(yc)) - half
            hi = int(round(yc)) + half + 1
            if lo < 2 or hi > H - 2:
                continue
            col = L[lo - 2:hi + 2, xi - 1:xi + 2].mean(axis=1)
            g = np.convolve(col, kernel, mode="valid")     # len = hi-lo
            if sign > 0:
                score = np.where(g > 0, g, 0.0)
            elif sign < 0:
                score = np.where(g < 0, -g, 0.0)
            else:
                score = np.abs(g)
            i = int(np.argmax(score))
            if score[i] <= 0:
                continue
            y = lo + i + _subpix_extremum(score, i)
            pts.append((x, y, score[i]))
        if len(pts) < 6:
            return None
        P = np.array(pts)
        X, Y = P[:, 0], P[:, 1]
        w = np.ones_like(X)
        for _ in range(12):                                  # IRLS, Huber
            A = np.vstack([X, np.ones_like(X)]).T
            Aw = A * w[:, None]
            sol, *_ = np.linalg.lstsq(Aw, Y * w, rcond=None)
            m, b = float(sol[0]), float(sol[1])
            r = Y - (m * X + b)
            s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-6
            k = 1.5 * s
            w = np.where(np.abs(r) <= k, 1.0, k / np.abs(r))
        r = Y - (m * X + b)
        keep = np.abs(r) < 3 * (1.4826 * np.median(np.abs(r - np.median(r))) + 1e-6)
        res = dict(m=m, b=b, n=int(keep.sum()), n_raw=len(X),
                   rms=float(np.sqrt(np.mean(r[keep] ** 2))),
                   x0=float(X.min()), x1=float(X.max()),
                   y_at_x0=float(m * X.min() + b), y_at_x1=float(m * X.max() + b))
    return res


if __name__ == "__main__":
    spec = json.loads(sys.argv[2])
    out = {}
    L = luma(sys.argv[1])
    for name, s in spec.items():
        r = fit(L, s["p0"], s["p1"], half=s.get("half", 9), sign=s.get("sign", 0))
        out[name] = r
        if r:
            print(f"{name:18s} m={r['m']:+.5f} b={r['b']:8.2f} rms={r['rms']:.2f} "
                  f"n={r['n']}/{r['n_raw']}  y({r['x0']:.0f})={r['y_at_x0']:.1f} "
                  f"y({r['x1']:.0f})={r['y_at_x1']:.1f}")
        else:
            print(f"{name:18s} FAILED")
    json.dump(out, open("edges.json", "w"), indent=1)
