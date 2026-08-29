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
RATIO between the key and the fill.

CORRECTION, 2026-08-29. This paragraph used to end "and exposure cannot fake it: raising
exposure raises both samples together." That is FALSE and the file now proves it against
itself - same lights, same scene, only the knob moving: -2.0 -> 128 FAIL, -1.0 -> 99 PASS,
0.0 -> 70 PASS. Raising exposure lifts both lobes only while both CAN move; once the lit
lobe is against the top of the display range it stops and the shadow lobe keeps climbing.
Two refusals now stand where the claim did - see the clip guard and LIT_MATCH in
compare(). Leaving the sentence in place would have been the worst outcome: a docstring
arguing a rung is sound while the rung's own code refuses to act on it.

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


CLIP_HI = 248.0          # a lobe whose median is above this is against the ceiling
CLIP_LO = 6.0            # ... or against the floor
CLIP_SHARE = 0.25        # ... or this much of THAT LOBE is pinned at the extreme, which
                         # is the level at which the pinning can hold the lobe's own
                         # median. It was 0.02 OF THE WHOLE PATCH for one frame and that
                         # was wrong twice over - wrong denominator, and a threshold far
                         # below anything that can move a median.


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
    # ---- THE CLIP GUARD, added 2026-08-29, and it is why this rung is a rung ----------
    # The docstring above this function claimed, in the paragraph beginning "WHY IT IS
    # WORTH TURNING INTO CODE", that the lit-minus-shadow difference is a property of the
    # key:fill ratio and that "exposure cannot fake it: raising exposure raises both
    # samples together". MEASURED on this lane's own frames, same lights, same geometry,
    # only the exposure knob moved:
    #        exposure -2.0   lit 244 / shadow 117 -> delta 128   FAIL (+51)
    #        exposure -1.0   lit 253 / shadow 154 -> delta  99   PASS (+22)
    #        exposure  0.0   lit 255 / shadow 185 -> delta  70   PASS  (-6)
    # The knob alone walks the rung from FAIL to PASS. The claim is false for a nameable
    # reason: raising exposure lifts both lobes ONLY while both can move. Once the lit
    # lobe is against the top of the display range it stops, the shadow lobe keeps
    # climbing, and the difference collapses. So the instrument this lane built to be
    # unfakeable by a knob was fakeable by exactly that knob, and its own docstring
    # argued it could not be.
    # THE TUTORIAL NEVER HAD THIS PROBLEM because he samples marble MID-TONES by hand and
    # would never eyedropper a blown highlight. Making his discipline a refusal is what
    # ports the measurement rather than the gesture.
    # THE SHARE TEST BELONGS TO THE LOBE IT COULD CORRUPT, NOT TO THE WHOLE PATCH.
    # Corrected 2026-08-29, one frame after the guard was written, by the frame that first
    # had a MEASURED sun in it: the floor read lit 180 / shadow 92 - the closest this lane
    # has come to the plate's 176 / 100 - and the guard refused it, because 2% of the whole
    # patch sat at pure black in the deep shade under the island. Those pixels are a tail;
    # the shadow lobe's median was 92 and nothing was holding it anywhere. A guard that
    # refuses the best reading it has ever been handed is miscalibrated, and refusing for
    # the wrong reason is not the safe direction to err in - it is how a rung gets switched
    # off. The tests that stay are the ones that mean something: a lobe whose MEDIAN is
    # against the wall is not a reading, and a lobe with enough of ITSELF pinned to hold its
    # own median there is not either.
    hi_share = float((v >= 254.0).sum()) / max(hi.size, 1)
    lo_share = float((v <= 1.0).sum()) / max(lo.size, 1)
    if lit >= CLIP_HI or shadow <= CLIP_LO or hi_share > CLIP_SHARE or lo_share > CLIP_SHARE:
        return dict(clipped=True, shadow=shadow, lit=lit,
                    hi_share=hi_share, lo_share=lo_share,
                    note=("a lobe is against the end of the range, so this patch's "
                          "difference is set by the clipping and not by the light. "
                          "Change the LIGHT, not the exposure."))
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
        if m.get("clipped"):
            m["bimodal"] = False
            out[name] = m
            continue
        m["delta"] = m["lit"] - m["shadow"]
        m["bimodal"] = True
        m["n_px"] = int(sub.size)
        out[name] = m
    return out


def same_size_or_refuse(ref, ours):
    """A PATCH IS A PIXEL BOX, so the two images must be the same size or the box is not
    on the same thing in both. Added 2026-08-29 after the mood loop spent a round comparing
    720x960 --quick renders against the 1440x1920 plate with one shared --patch: every box
    read the TOP-LEFT QUARTER of the render against the whole region of the plate, and
    printed a number for it. This is R11's exit-code law on a different instrument - a
    playblast is not the reference's size, and 'could not look' must never print like
    'looked and it was fine'. It REFUSES rather than rescaling, because a rescale is a
    different measurement and would hide which one was made.
    """
    wa, ha = Image.open(ref).size
    wb, hb = Image.open(ours).size
    if (wa, ha) != (wb, hb):
        print(f"exit 2 - COULD NOT RUN. The reference is {wa}x{ha} and the render is "
              f"{wb}x{hb}. A --patch is a pixel box; on two different sizes it is two "
              f"different boxes. Re-render at the plate's resolution "
              f"(--res-pct 100), or crop, but do not compare these.", file=sys.stderr)
        return False
    return True


LIT_MATCH = 30.0   # levels; beyond this the two frames are not on the same part of the curve


def compare(ref, ours, patches, tol=25.0, lit_match=LIT_MATCH):
    """MATCH THE LIT LEVEL FIRST, THEN COMPARE THE SHADOW.

    Added 2026-08-29 alongside the clip guard, and for the same reason. A difference of
    display code values is only a property of the key:fill ratio while both frames sit on
    the SAME part of the tone curve. AgX is steep in the mid-tones and flat near white, so
    a frame whose lit floor reads 232 and one whose lit floor reads 176 cannot have their
    lit-minus-shadow numbers put side by side - the second frame's difference is measured
    on a steeper part of the curve than the first's.

    This is also what takes the exposure knob away. Exposure is now SPENT matching the lit
    level; it is no longer free to move the delta. What is left to move the delta is the
    light, which is the thing the rung claims to measure.

    The tutorial does this without saying so: every pair he reads is a mid-tone (170/80,
    250/150, 210/110 on the reference; 150/50, 210/100 on his render), because he
    eyedroppers marble by hand and would never sample a blown highlight.
    """
    a, b = measure(ref, patches), measure(ours, patches)
    rows = []
    for k in patches:
        ra, rb = a[k], b[k]
        if not (ra.get("bimodal") and rb.get("bimodal")):
            rows.append((k, ra, rb, None, "COULD NOT RUN"))
            continue
        lit_off = rb["lit"] - ra["lit"]
        ra["lit_offset"] = rb["lit_offset"] = lit_off
        if abs(lit_off) > lit_match:
            rb["off_curve"] = True
            rows.append((k, ra, rb, None, "COULD NOT COMPARE"))
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
    if not same_size_or_refuse(o.ref, o.ours):
        return 2
    rows = compare(o.ref, o.ours, patches, o.tol)
    print(f"{'patch':14s} {'REFERENCE lit/shadow=delta':>32s}   {'OURS lit/shadow=delta':>30s}   verdict")
    worst = 0.0
    ran = 0
    for k, ra, rb, d, verdict in rows:
        if d is None:
            why = "not bimodal"
            for side, r in (("reference", ra), ("ours", rb)):
                if r.get("clipped"):
                    why = (f"{side} lobe CLIPPED (lit {r['lit']:.0f} shadow "
                           f"{r['shadow']:.0f}, {100*r['hi_share']:.1f}% at 255) - "
                           f"change the LIGHT, not the exposure")
            if rb.get("off_curve"):
                print(f"{k:14s} {ra['lit']:8.0f} /{ra['shadow']:7.0f} = {ra['delta']:6.0f}"
                      f"      {rb['lit']:8.0f} /{rb['shadow']:7.0f} = {rb['delta']:6.0f}"
                      f"      COULD NOT COMPARE  (lit {rb['lit_offset']:+.0f} off the "
                      f"reference; match the lit level with exposure first)")
                continue
            print(f"{k:14s} {'--':>32s}   {'--':>30s}   COULD NOT RUN ({why})")
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
