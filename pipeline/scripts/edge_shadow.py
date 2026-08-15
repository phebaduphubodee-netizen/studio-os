#!/usr/bin/env python3
"""edge_shadow.py — does a boundary CAST A LINE, or is it a tonal ramp? PURE (no bpy).

WHY THIS EXISTS. A cold critic looked at p2r34 and wrote the sentence that named the
defect exactly: *"the boundary between the grey band and the white below it is a TONAL
CHANGE WITH NO THICKNESS — no hem, no turn-down, no shadow under an edge. It reads as
paint, not one cloth lying on another."* The builder's eye agreed on sight. Neither is
a measurement, and this repo does not act on either alone.

The instrument already in the house could not settle it. `p2_exit.edge_rise_width`
measures how STEEP the strongest transition is, and on p2r34 it read 2-9 px at a real
acquired pillow hem, 5 px at our coverlet boundary and 5 px at a control edge — three
things a human eye separates instantly, scoring the same. A rung that cannot tell them
apart is not evidence of anything. (Same family as the wood-figure rung, whose own
docstring named "two adjacent boards" as its purpose while its search bound made the
two-board case the one thing it could not see.)

SO THE DISCRIMINATOR IS TAKEN FROM THE PHYSICS THE CRITIC NAMED, not from what was
convenient to compute. A finite-thickness edge lying on a surface OCCLUDES the light
reaching the surface just beyond it, so the luminance profile across the boundary DIPS
BELOW BOTH PLATEAUS — a dark line. A tonal ramp between two materials is monotonic and
never undershoots. That is the whole test: how often does the profile dip, and how deep.

MEASURED ON p2r34, one frame, one light, one camera — which is what makes it an
argument and not a comparison across conditions:

    acquired pillow sham flange      dip in 95.0% of columns, median 23.0 codes
    gap between the two pillows      dip in 95.6% of columns, median 14.1 codes
    CONTROL bed base meets floor     dip in 93.7% of columns, median 39.3 codes
    our coverlet -> sheet boundary   dip in  2.8% of columns, median  2.9 codes

An edge that certainly occludes lines 93-96% of its columns. Ours lines 2.8%. The
acquired cloth in the SAME frame has hems that read; the cloth we generate has none.
That isolates the cause to geometry — a lighting change cannot explain a 30x gap
between two objects lit by the same lights.

THE CONTROL IS NOT OPTIONAL AND THIS MODULE ENFORCES IT. R11 was written after a round
quoted "no step at u=989" as proof of absence until a same-class corner that certainly
existed scored the same. An absence test with no positive control measures nothing, so
`verdict()` REFUSES to return a verdict unless at least one site is declared a control
AND that control actually fires. "Could not look" must never print like "looked and it
was fine".
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

# A column with no real transition has nothing to say about edges; including it would
# dilute the percentage with flat wall. 3.0 codes is below the render's own noise-free
# gradient on a smooth cloth ramp and well under any real edge.
MIN_GRAD = 3.0
# Half-window around the strongest transition, in px. Wide enough to hold both plateaus
# of a real hem at 2400px, narrow enough not to swallow a second edge.
HALF_WIN = 14
# A dip shallower than this is quantisation, not occlusion.
MIN_DIP = 1.5
# A control that lines fewer than this fraction of its columns did not fire: the test
# could not see, so no absence elsewhere in that frame means anything.
CONTROL_MIN_PCT = 60.0


def luma(im):
    """sRGB-code luminance array from a PIL image. Kept identical in spirit to
    p2_exit._lum_arr so numbers from the two modules stay comparable."""
    return np.asarray(im.convert("L"), dtype=float)


def shadow_line(L, min_grad=MIN_GRAD, half=HALF_WIN, min_dip=MIN_DIP):
    """Per-column: find the strongest vertical transition, then ask whether the profile
    dips BELOW the lower of its two plateaus.

    Returns (pct_columns_with_dip, median_dip_codes, n_columns_considered).

    n_columns is reported because a percentage over a handful of columns is noise, and
    a caller that cannot see that is being flattered."""
    H, W = L.shape
    hits, cols = [], 0
    for x in range(W):
        col = L[:, x]
        grad = np.abs(np.diff(col))
        if grad.size == 0 or grad.max() < min_grad:
            continue                       # no edge in this column — it is not evidence
        y = int(np.argmax(grad))
        a, b = max(0, y - half), min(H - 1, y + half + 1)
        seg = col[a:b]
        if len(seg) < 6:
            continue                       # window ran off the crop; cannot judge
        cols += 1
        plateau = min(float(seg[0]), float(seg[-1]))
        dip = plateau - float(seg.min())
        if dip > min_dip:
            hits.append(dip)
    pct = 100.0 * len(hits) / cols if cols else 0.0
    med = float(np.median(hits)) if hits else 0.0
    return pct, med, cols


class NoControl(RuntimeError):
    """Raised when a verdict was asked for with no working positive control.

    This is a HARD STOP, not a warning. The whole value of the measurement is that a
    low score means "no edge"; without a control a low score equally means "the test
    could not see", and those two must never print the same way."""


def verdict(sites, control_min_pct=CONTROL_MIN_PCT):
    """sites: list of dicts {name, pct, med, n, control: bool}.

    Returns (rows, control_row). Raises NoControl if no site is marked control, or if
    every control site failed to fire — because then this frame's absences are unread,
    not clean."""
    controls = [s for s in sites if s.get("control")]
    if not controls:
        raise NoControl(
            "no site was declared a control — an absence test with no positive control "
            "measures nothing (R11). Declare a site that certainly occludes.")
    fired = [c for c in controls if c["pct"] >= control_min_pct]
    if not fired:
        best = max(controls, key=lambda c: c["pct"])
        raise NoControl(
            f"control {best['name']!r} lined only {best['pct']:.1f}% of its columns "
            f"(needs >= {control_min_pct:.0f}%) — the test did not fire on this frame, "
            f"so nothing here can be called clean")
    ref = max(fired, key=lambda c: c["pct"])
    rows = []
    for s in sites:
        if s.get("control"):
            rows.append((s, "CONTROL", f"fired at {s['pct']:.1f}%"))
            continue
        ratio = s["pct"] / ref["pct"] if ref["pct"] else 0.0
        if ratio >= 0.5:
            rows.append((s, "READS AS AN EDGE", f"{ratio:.2f}x the control"))
        elif ratio >= 0.15:
            rows.append((s, "WEAK", f"{ratio:.2f}x the control"))
        else:
            rows.append((s, "NO LINE — reads as paint", f"{ratio:.2f}x the control"))
    return rows, ref


def measure_sites(image_path, sites):
    """sites: list of {name, box:[x0,y0,x1,y1], control?:bool}. Returns enriched dicts."""
    from PIL import Image
    im = Image.open(image_path)
    out = []
    for s in sites:
        x0, y0, x1, y1 = s["box"]
        pct, med, n = shadow_line(luma(im.crop((x0, y0, x1, y1))))
        out.append({**s, "pct": pct, "med": med, "n": n})
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Does a boundary cast a shadow line, or is it a tonal ramp? "
                    "At least one site must be declared a positive control.")
    ap.add_argument("render")
    ap.add_argument("--sites", required=True,
                    help='JSON list: [{"name":..., "box":[x0,y0,x1,y1], "control":true?}, ...] '
                         'or a path to a .json file holding it')
    a = ap.parse_args()

    raw = a.sites
    if not raw.lstrip().startswith("["):
        with open(raw, encoding="utf-8") as fh:
            raw = fh.read()
    sites = measure_sites(a.render, json.loads(raw))

    for s in sites:
        tag = " [CONTROL]" if s.get("control") else ""
        print(f"  {s['name']:<44}{tag:<11} dip {s['pct']:5.1f}% of columns   "
              f"median {s['med']:5.1f} codes   (n={s['n']})")
    print()
    try:
        rows, ref = verdict(sites)
    except NoControl as e:
        print(f"COULD NOT RUN — {e}")
        return 2
    print(f"control of record: {ref['name']} ({ref['pct']:.1f}% of columns, "
          f"median {ref['med']:.1f} codes)")
    for s, call, why in rows:
        if s.get("control"):
            continue
        print(f"  {s['name']:<44} {call:<26} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
