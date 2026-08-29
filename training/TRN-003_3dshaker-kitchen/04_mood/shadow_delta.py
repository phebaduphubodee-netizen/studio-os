#!/usr/bin/env python3
"""shadow_delta.py - the tutorial's shadow-contrast check, as an instrument.

WHAT HE DOES (14:31-15:45). Put the reference and the render in Photoshop, DESATURATE
both, then eyedropper a LIT patch and a SHADOW patch **on the same material** and read
the two 0-255 levels. On the reference marble he gets 170/80, 250/150, 210/110 - a
difference of about 100 every time. On his render: 150/50, 210/100. Same difference,
so the shadow contrast matches, and he moves on.

He is careful about the one thing that makes it a measurement rather than a vibe: *the
two samples must be the same material*. "I can't do it on this shelf here which is
white and this black oven."

WHY IT IS WORTH TURNING INTO CODE. It answers a question no other instrument in this
studio's pipeline asks. Every existing rung reads an ABSOLUTE level - is the duvet
0.80 of p99, is the ratio in band - and an absolute level moves when the exposure
moves, so it can be satisfied by turning the exposure knob without the light changing
at all. The lit-minus-shadow difference on one material is a property of the LIGHTING
RATIO between the key and the fill, and exposure cannot fake it: raising exposure
raises both samples together.

WHAT IT IS NOT. It cannot tell you the light is coming from the wrong place - a lamp
in the wrong corner reproduces the same delta. Direction stays a separate question
(sun_solve.py measures that off the shadows). This rung answers only "is the key doing
as much work here as it does there".

    python shadow_delta.py ref.png render.png --patch floor 600 1620 1440 1900
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image


def desaturate(path):
    """Photoshop's Image > Adjustments > Desaturate is HSL lightness, (max+min)/2, on
    the DISPLAY-space pixels. Not a luma weighting - matching his numbers means
    matching his operator."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    return (a.max(axis=2) + a.min(axis=2)) * 0.5


def two_modes(v, bins=64, min_share=0.10, min_sep=25.0):
    """The lit level and the shadow level of one material, without clicking anything.

    A patch of ONE material under a key plus a fill is bimodal: a shadow lobe and a lit
    lobe. Split it with Otsu (the standard between-class-variance threshold) and take
    the MEDIAN of each side - medians, so a few specular pixels or a dark object that
    strayed into the box cannot drag a lobe.

    Returns None when the patch is not really bimodal: either side under min_share of
    the pixels, or the two medians closer together than min_sep levels. That is a
    finding - "this box has no lit and shadow to compare" - and must never be papered
    over by returning a mean, because a mean always returns a number and so always
    looks like it worked.

    (First version of this function picked the two tallest histogram peaks and got the
    plate's own floor wrong: the shadow lobe has two humps, so it returned 104 and 122
    and reported a delta of 18 where the true answer is 111. A peak is not a lobe.)
    """
    v = np.asarray(v, dtype=np.float64)
    if v.size < 400:
        return None
    h, edges = np.histogram(v, bins=bins, range=(0, 255))
    h = h.astype(np.float64)
    tot = h.sum()
    if tot <= 0:
        return None
    p = h / tot
    ctr = (edges[:-1] + edges[1:]) / 2.0
    w0 = np.cumsum(p)
    m0 = np.cumsum(p * ctr)
    mT = m0[-1]
    denom = w0 * (1.0 - w0)
    with np.errstate(divide="ignore", invalid="ignore"):
        between = np.where(denom > 1e-12, (mT * w0 - m0) ** 2 / denom, 0.0)
    k = int(np.argmax(between))
    thr = float(edges[k + 1])
    lo, hi = v[v <= thr], v[v > thr]
    if lo.size < min_share * v.size or hi.size < min_share * v.size:
        return None
    shadow, lit = float(np.median(lo)), float(np.median(hi))
    if lit - shadow < min_sep:
        return None
    return dict(shadow=shadow, lit=lit, threshold=thr,
                share_shadow=float(lo.size) / v.size,
                share_lit=float(hi.size) / v.size,
                separability=float(between[k] / max(1e-12, v.var())))


def measure(path, patches):
    g = desaturate(path)
    out = {}
    for name, (x0, y0, x1, y1) in patches.items():
        sub = g[y0:y1, x0:x1].ravel()
        m = two_modes(sub)
        if m is None:
            out[name] = dict(bimodal=False,
                             note="not bimodal - no separable lit and shadow lobe here")
            continue
        m["delta"] = m["lit"] - m["shadow"]
        m["bimodal"] = True
        m["n_px"] = int(sub.size)
        out[name] = m
    return out


def compare(ref, ours, patches, tol=25.0):
    a, b = measure(ref, patches), measure(ours, patches)
    rows = []
    for k in patches:
        ra, rb = a[k], b[k]
        if not (ra.get("bimodal") and rb.get("bimodal")):
            rows.append((k, ra, rb, None, "COULD NOT RUN"))
            continue
        d = rb["delta"] - ra["delta"]
        rows.append((k, ra, rb, d, "PASS" if abs(d) <= tol else "FAIL"))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("ours")
    ap.add_argument("--patch", nargs=5, action="append", metavar=("NAME", "X0", "Y0", "X1", "Y1"))
    ap.add_argument("--tol", type=float, default=25.0)
    ap.add_argument("--json", default="")
    o = ap.parse_args()
    patches = {p[0]: tuple(int(v) for v in p[1:]) for p in (o.patch or [])}
    if not patches:
        print("no --patch given", file=sys.stderr)
        return 2
    rows = compare(o.ref, o.ours, patches, o.tol)
    print(f"{'patch':14s} {'REFERENCE lit/shadow=delta':>32s}   {'OURS lit/shadow=delta':>30s}   verdict")
    worst = 0.0
    ran = 0
    for k, ra, rb, d, verdict in rows:
        if d is None:
            print(f"{k:14s} {'--':>32s}   {'--':>30s}   COULD NOT RUN (not bimodal)")
            continue
        ran += 1
        worst = max(worst, abs(d))
        print(f"{k:14s} {ra['lit']:8.0f} /{ra['shadow']:7.0f} = {ra['delta']:6.0f}      "
              f"{rb['lit']:8.0f} /{rb['shadow']:7.0f} = {rb['delta']:6.0f}      "
              f"{verdict}  ({d:+.0f})")
    if o.json:
        json.dump([dict(patch=k, ref=ra, ours=rb, delta_of_deltas=d, verdict=v)
                   for k, ra, rb, d, v in rows], open(o.json, "w"), indent=1)
    if ran == 0:
        print("\nexit 2 - COULD NOT RUN on any patch. That is not a pass.")
        return 2
    print(f"\nworst |delta of deltas| = {worst:.0f} levels   (tolerance {o.tol:.0f})")
    return 0 if worst <= o.tol else 1


if __name__ == "__main__":
    sys.exit(main())
