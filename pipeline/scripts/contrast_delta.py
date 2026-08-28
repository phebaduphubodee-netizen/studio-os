#!/usr/bin/env python3
"""contrast_delta.py — LIT-minus-SHADOW on ONE material, the way a working studio checks it.

    python pipeline/scripts/contrast_delta.py --beauty <ours.png> --mask <idmask.png>
                                              --names <idmask.json>
                                              [--reference <ref.jpg> --samples <pairs.json>]
                                              [--expect-delta LO:HI] [--json <out.json>]

WHERE THIS CAME FROM, AND WHY IT IS NOT ANOTHER RATIO
-----------------------------------------------------
2026-08-28, from a 3D Shaker tutorial in which a studio reproduces a published interior
(Est Living / Garden House, McCluskey Studio) in Blender. At 15:00-15:45 they check
whether their light matches the reference, and the method is the whole point:

    desaturate both images -> eyedropper a LIT patch and a SHADOW patch ON THE SAME
    MATERIAL -> the DIFFERENCE of the two 0..255 greys must match between reference and
    render.

    reference:  170/80   250/150   210/110     -> delta ~ 90-100 every time
    their render: 150/50   210/100              -> delta ~ 100  -> match

They say out loud why the material must be held constant: *"I can't do it on this shelf
here which is white and this black oven, but I can check it for example on this marble
table."* Verified against the video's own pixels at 1152 px: the eyedropper on the
reference's shadowed marble reads 89,89,89 (#595959), which is the "80" they quote.

THE CLASS THIS RUNG CATCHES THAT OUR EXISTING ONES DO NOT. This lane already measures
DYNAMIC RANGE as a whole-frame ratio (ours ~10:1 against delivered work at 191-2500:1).
That number mixes ALBEDO into a claim about LIGHT: a white shelf beside a black oven
produces a large ratio in a totally flat room, and a monochrome room produces a small one
under beautiful light. Holding the material constant removes albedo BY CONSTRUCTION and
leaves the lighting alone.

This repo already measured the same phenomenon from the other side and built the other
half of the instrument. `value_ladder.py` records that `bed__base`, `bed__throw` and
`bench__seat` carry the IDENTICAL authored albedo (0.46, 0.43, 0.39) and render at
121.1 / 155.1 / 178.2 — "57 codes apart from orientation and local light alone". That is
this rung's premise, stated as a finding 36 days before the rung existed: within one
albedo, the spread IS the light. `value_probe` ranks objects by their median; nothing
looked INSIDE an object at the spread between its lit and its shadowed pixels.

HOW THE SPLIT IS MADE, AND WHEN IT REFUSES
------------------------------------------
Per object (an object is one material by construction — that is what the id mask buys us):

  1. Otsu's threshold on that object's own luma histogram splits its pixels in two.
  2. SEPARABILITY (between-class variance / total variance) must clear `SEP_FLOOR`.
     A unimodal object has no shadow on it; forcing a threshold through the middle of one
     mode yields a number, and the number is noise wearing arithmetic.
  3. Each side must hold at least `MIN_CLASS_SHARE` of the object's pixels, or the "shadow"
     is an anti-aliased rim rather than a lighting state.
  4. delta = median(lit) - median(shadow), on the 0..255 sRGB-encoded scale — the same
     space `value_probe.luma` uses and the same space a Photoshop eyedropper reports, which
     is the space the eye ranks. Linear luminance would report a ladder no viewer sees.

Any object failing 1-3 is reported as UNSPLIT with the reason. It is never reported as
delta 0. "Could not measure" must never print like "measured and it was fine" (R11).

THE POSITIVE CONTROL, BECAUSE A PASS HERE IS AN ABSENCE (exit-test clause 2b)
----------------------------------------------------------------------------
"No object in this frame carries a lit/shadow split" is exactly the shape of claim that
needs proof the instrument can fire at all. So `positive_control()` takes the SAME pixels
of the SAME object, darkens a deterministic half of them by a known K, and re-runs the
splitter. If the recovered delta is not within tolerance of K, the splitter could not have
found a real one either, and the run exits 2 rather than reporting a clean sheet.

WHAT IT CANNOT SEE, FOUND ON ITS OWN FIRST LIVE FRAME (trn002_mat_r32)
----------------------------------------------------------------------
An object that CONTAINS AN OPENING reads the opening as its shadow. `petcave_mouth` came
back at 143.8 codes against a frame median of 26.0 — the "shadow" class is the unlit cave
interior, not a lighting state on one surface. The premise "one id = one material = one
albedo" holds for the id mask, but not for what is VISIBLE THROUGH that id. Rows far above
the frame median should be read as candidates for this, not as good news; the fix is
either to exclude apertures by name in the spec or to accept the row as unusable. It is
named here rather than silenced because a rung that quietly drops its outliers is choosing
its own evidence.

The frame's own reading, for whoever calibrates the cuts later: 26 of 73 objects split, 47
refused (37 unimodal, 6 sliver, 4 rim), valley ratios on the measured rows spanning
0.00-0.59 against a cut of 0.60 — so the cut is doing work at the top of its range and
wants re-deriving once a second real frame exists.

EXIT CODES ARE A CONTRACT
    0  measured (and, if --expect-delta was given, the frame's delta sits in the band)
    1  a band was given and the frame's delta is outside it
    2  COULD NOT RUN — no object could be split, the positive control did not fire, the
       images disagree in size, or a sample point lies outside the reference
"""
import json
import os
import sys

try:  # keep output legible on a cp1252 Windows console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import value_probe as VP  # noqa: E402  — one decoder, one luma, one palette


class ContrastError(Exception):
    """Raised when the measurement cannot be made. Callers turn this into exit 2."""


# --------------------------------------------------------------------------- the cuts

MIN_PIXELS = 400          # below this an object cannot support two classes at all
MIN_CLASS_SHARE = 0.12    # each side must hold this fraction of the object's pixels
SEP_FLOOR = 0.35          # Otsu separability below this is noise, not a split
VALLEY_MAX = 0.60         # the valley at the threshold, as a fraction of the shallower peak
CONTROL_K = 40.0          # the known step the positive control plants, in 0..255 codes
CONTROL_TOL = 6.0         # how close the splitter must come to recovering it
SMOOTH_W = 5              # histogram box-smooth width, to keep quantisation off the valley

# WHY SEPARABILITY IS NOT ENOUGH, found by this module's own test before it ever ran on a
# frame. Otsu separability answers "does a split explain the variance", and ANY spread
# distribution answers yes: a UNIFORM histogram cut at its middle scores 0.75, well past any
# floor worth setting, while having exactly one mode. A ramp scores the same. So a rung
# gated on separability alone would have read every smoothly-shaded object in the frame as
# an object with a shadow across it, and reported a delta for each — the flattering-scorer
# shape this repo has caught in a dozen lanes.
#
# What actually distinguishes "one surface lit from one side" from "one surface with a
# shadow edge crossing it" is a VALLEY: at a real shadow boundary few pixels sit at the
# threshold, because the penumbra is narrow compared with the two lit states. So the cut is
# on the histogram's depth at the threshold relative to the shallower of its two peaks.
# The ratio is PRINTED on every row so the cut can be re-derived from real frames rather
# than defended as a round number.


# --------------------------------------------------------------------------- pure core

def otsu(values, bins=256):
    """Threshold that maximises between-class variance, plus the separability ratio.

    Returns (threshold, separability). PURE — takes any sequence of 0..255 floats and
    needs no numpy, so the tests exercise the same code the CLI runs.
    """
    vals = [float(v) for v in values]
    n = len(vals)
    if n < 2:
        raise ContrastError("otsu needs at least two samples")
    hist = [0] * bins
    for v in vals:
        i = int(v)
        hist[0 if i < 0 else (bins - 1 if i >= bins else i)] += 1

    total = float(n)
    sum_all = sum(i * h for i, h in enumerate(hist))
    mean_all = sum_all / total
    var_all = sum(h * (i - mean_all) ** 2 for i, h in enumerate(hist)) / total

    w0 = 0.0
    sum0 = 0.0
    best_t, best_between = 0, -1.0
    for t in range(bins - 1):
        w0 += hist[t]
        sum0 += t * hist[t]
        w1 = total - w0
        if w0 == 0 or w1 == 0:
            continue
        m0 = sum0 / w0
        m1 = (sum_all - sum0) / w1
        between = (w0 / total) * (w1 / total) * (m0 - m1) ** 2
        if between > best_between:
            best_between, best_t = between, t
    if best_between < 0:
        raise ContrastError("otsu found no admissible threshold")
    sep = (best_between / var_all) if var_all > 0 else 0.0
    return best_t, sep


def _histogram(values, bins=256):
    h = [0] * bins
    for v in values:
        i = int(v)
        h[0 if i < 0 else (bins - 1 if i >= bins else i)] += 1
    return h


def _smooth(hist, w=SMOOTH_W):
    """Box-smooth, so a quantisation comb cannot pass for a valley (or fill one in)."""
    n = len(hist)
    half = max(1, w // 2)
    out = []
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        out.append(sum(hist[lo:hi]) / float(hi - lo))
    return out


def valley_ratio(values, t, w=SMOOTH_W):
    """Depth of the histogram at threshold `t`, over the SHALLOWER of the two class peaks.

    0.0 = the two classes do not touch (a hard shadow edge). 1.0 = the density at the
    threshold is as high as a peak, i.e. there is no valley and therefore no second
    lighting state — just one surface with a gradient across it.
    """
    sm = _smooth(_histogram(values), w)
    t = max(0, min(len(sm) - 2, int(t)))
    lo_peak = max(sm[:t + 1]) if t + 1 > 0 else 0.0
    hi_peak = max(sm[t + 1:]) if t + 1 < len(sm) else 0.0
    if lo_peak <= 0 or hi_peak <= 0:
        return 1.0
    lo, hi = max(0, t - w), min(len(sm), t + w + 1)
    floor_at_t = min(sm[lo:hi])
    return floor_at_t / min(lo_peak, hi_peak)


def split_object(values, min_px=MIN_PIXELS, min_share=MIN_CLASS_SHARE, sep_floor=SEP_FLOOR,
                 valley_max=VALLEY_MAX):
    """One object's luma values -> its lit/shadow reading, or a refusal with a REASON.

    Returns a dict that always carries `ok`. When ok is False the row still carries the
    numbers that were available, because a refusal that hides its own evidence is how a
    guard becomes unfalsifiable.
    """
    px = len(values)
    if px < min_px:
        return {"ok": False, "reason": "sliver", "px": px,
                "detail": f"{px} px < {min_px}"}
    t, sep = otsu(values)
    lo = [v for v in values if v <= t]
    hi = [v for v in values if v > t]
    share = min(len(lo), len(hi)) / float(px)
    valley = valley_ratio(values, t)
    if sep < sep_floor:
        return {"ok": False, "reason": "noise", "px": px, "sep": sep, "valley": valley,
                "detail": f"separability {sep:.3f} < {sep_floor} — the split explains "
                          f"nothing"}
    if valley > valley_max:
        return {"ok": False, "reason": "unimodal", "px": px, "sep": sep, "valley": valley,
                "detail": f"valley {valley:.2f} > {valley_max} — a gradient across one "
                          f"lighting state, not a shadow edge"}
    if share < min_share:
        return {"ok": False, "reason": "rim", "px": px, "sep": sep, "valley": valley,
                "share": share,
                "detail": f"smaller class holds {share:.1%} < {min_share:.0%} — an edge, "
                          f"not a shadow"}
    shadow = VP.median(lo)
    lit = VP.median(hi)
    return {"ok": True, "px": px, "sep": sep, "valley": valley, "share": share,
            "threshold": float(t), "shadow": shadow, "lit": lit, "delta": lit - shadow,
            "shadow_px": len(lo), "lit_px": len(hi)}


def positive_control(values, k=CONTROL_K, tol=CONTROL_TOL):
    """Plant a known step of `k` codes in HALF of an object's own pixels and check that
    `split_object` recovers it. Returns (fired, recovered_delta, detail).

    THIS IS THE RUNG'S OWN TRIPWIRE (exit-test clause 2b, owed since D-056). A sheet that
    says "no object in this frame has a lit/shadow split" is an ABSENCE claim, and an
    absence claim from an instrument that was never shown to fire is worth nothing. The
    control uses the SAME pixels, so it cannot pass on a frame where the real reading
    could not have worked.

    The planted half is chosen by SORTED ORDER, not at random: the brighter half keeps its
    value and the darker half drops by k, which manufactures exactly the two-mode
    histogram a lit object with a shadow across it produces.
    """
    vals = sorted(float(v) for v in values)
    if len(vals) < MIN_PIXELS:
        return False, None, f"control needs {MIN_PIXELS} px, had {len(vals)}"
    half = len(vals) // 2
    planted = [max(0.0, v - k) for v in vals[:half]] + vals[half:]
    row = split_object(planted)
    if not row.get("ok"):
        return False, None, f"control could not be split: {row.get('detail')}"
    got = row["delta"]
    # The recovered delta is the gap between the two medians AFTER the step, which is the
    # planted k plus whatever spread the object already had between its own two halves.
    base = VP.median(vals[half:]) - VP.median(vals[:half])
    recovered = got - base
    fired = abs(recovered - k) <= tol
    return fired, recovered, (f"planted {k:.0f}, recovered {recovered:.1f} "
                              f"(tol {tol:.0f})")


def summarise(rows, ref_deltas=None):
    """(measured rows, unsplit rows, frame delta, reference delta) from per-object rows."""
    ok = [r for r in rows if r.get("ok")]
    bad = [r for r in rows if not r.get("ok")]
    frame = VP.median([r["delta"] for r in ok]) if ok else None
    ref = VP.median(list(ref_deltas)) if ref_deltas else None
    return ok, bad, frame, ref


def report(ok, bad, frame, ref):
    """Human-readable, and it prints what it COULD NOT read as loudly as what it could."""
    out = [f"{'object':26s} {'px':>8s} {'shadow':>7s} {'lit':>7s} {'delta':>7s} "
           f"{'sep':>6s} {'valley':>6s}"]
    for r in sorted(ok, key=lambda r: -r["delta"]):
        out.append(f"{r['name']:26s} {r['px']:8d} {r['shadow']:7.1f} {r['lit']:7.1f} "
                   f"{r['delta']:7.1f} {r['sep']:6.3f} {r['valley']:6.2f}")
    out.append("")
    out.append(f"MEASURED {len(ok)} object(s) · UNSPLIT {len(bad)}")
    for r in sorted(bad, key=lambda r: r.get("name", "")):
        out.append(f"    - {r.get('name','?'):24s} {r['reason']:9s} {r.get('detail','')}")
    out.append("")
    if frame is None:
        out.append("FRAME DELTA  (none — no object in this frame carries a lit/shadow split)")
    else:
        out.append(f"FRAME DELTA  {frame:.1f} codes (median over measured objects)")
    if ref is not None:
        out.append(f"REFERENCE    {ref:.1f} codes (median over signed sample pairs)")
        if frame is not None:
            out.append(f"GAP          {frame - ref:+.1f} codes")
    else:
        out.append("REFERENCE    none supplied — this run measures OUR frame only and "
                   "compares it to nothing")
    return "\n".join(out)


# --------------------------------------------------------------------------- reference side

def reference_deltas(pixels, pairs):
    """Signed eyedropper pairs -> one delta each. `pixels` is a callable (x, y) -> rgb.

    The reference has no id mask, so "the same material" is a HUMAN claim here, exactly as
    it is in the video. Each pair names its material and carries two points; the name is
    recorded so a wrong pair can be argued with. Identity is signed, never derived — the
    same law R12 applies to BF codes.
    """
    out = []
    for p in pairs:
        for key in ("material", "lit", "shadow"):
            if key not in p:
                raise ContrastError(f"sample pair {p!r} has no {key!r}")
        lit_xy, sh_xy = tuple(p["lit"]), tuple(p["shadow"])
        lit = VP.luma(pixels(*lit_xy))
        shadow = VP.luma(pixels(*sh_xy))
        if lit <= shadow:
            # A PAIR WHOSE "LIT" POINT IS DARKER THAN ITS "SHADOW" POINT IS MISLABELLED,
            # and it must not become a negative delta on the sheet. Found by running the
            # CLI on arbitrary sample coordinates: the run printed a REFERENCE of -4.1
            # codes, a number that cannot describe any lighting and that would have
            # dragged the median of a real sample set toward zero without ever looking
            # wrong. The points are a human's claim about the image (like the material
            # name beside them), so the refusal names the pair and the caller re-picks.
            raise ContrastError(
                f"sample pair {p['material']!r}: the 'lit' point at {list(lit_xy)} reads "
                f"{lit:.1f} and the 'shadow' point at {list(sh_xy)} reads {shadow:.1f}. "
                f"The lit point is not the brighter one — the pair is swapped or one of "
                f"the points is off the material.")
        out.append({"material": str(p["material"]), "lit": lit, "shadow": shadow,
                    "delta": lit - shadow, "lit_xy": list(lit_xy),
                    "shadow_xy": list(sh_xy)})
    if not out:
        raise ContrastError("the samples file carries no pairs")
    return out


def average_color(rgb_rows):
    """Mean R, G, B over an image — the tutorial's `Filter > Blur > Average` check (12:15).

    He collapses the whole reference to ONE colour and makes his base shader that colour.
    It is a crude statistic and that is its virtue: it cannot be satisfied by a local fix,
    so it catches a frame whose overall cast is wrong while every local material is right.
    `rgb_rows` is any iterable of (r, g, b).
    """
    n = 0
    acc = [0.0, 0.0, 0.0]
    for r, g, b in rgb_rows:
        acc[0] += r
        acc[1] += g
        acc[2] += b
        n += 1
    if not n:
        raise ContrastError("average_color over an empty image")
    return tuple(c / n for c in acc)


def color_gap(a, b):
    """Euclidean distance between two mean colours, in 0..255 sRGB. Reported, never a cut:
    the right cut is a question for the anchor pool (R4), not a number invented here."""
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) ** 0.5


# --------------------------------------------------------------------------- the real path

def measure_frame(beauty_rgb, mask_rgb, names, min_px=MIN_PIXELS):
    """HxWx3 beauty + HxWx3 id mask + {id: name} -> per-object rows. numpy path."""
    import numpy as np
    if beauty_rgb.shape[:2] != mask_rgb.shape[:2]:
        raise ContrastError(f"beauty {beauty_rgb.shape[:2]} and mask {mask_rgb.shape[:2]} "
                            f"are not the same size — a mask that is not pixel-aligned "
                            f"with its frame measures another picture")
    lum = (0.2126 * beauty_rgb[..., 0] + 0.7152 * beauty_rgb[..., 1]
           + 0.0722 * beauty_rgb[..., 2])
    ids = VP.decode_ids(mask_rgb)
    rows = []
    for k, name in names.items():
        sel = ids == int(k)
        vals = lum[sel]
        row = split_object(vals.tolist(), min_px=min_px)
        row["name"] = name
        row["id"] = int(k)
        rows.append(row)
    return rows


def _main(argv):
    import argparse
    import numpy as np
    from PIL import Image

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--beauty", required=True)
    ap.add_argument("--mask", required=True)
    ap.add_argument("--names", required=True, help="the id mask's sidecar json")
    ap.add_argument("--reference", default=None)
    ap.add_argument("--samples", default=None,
                    help="json: {pairs:[{material, lit:[x,y], shadow:[x,y]}]}")
    ap.add_argument("--expect-delta", default=None, metavar="LO:HI",
                    help="fail (exit 1) when the frame delta falls outside this band")
    ap.add_argument("--json", default=None, help="write the full reading here")
    a = ap.parse_args(argv[1:])

    side = json.load(open(a.names, encoding="utf-8"))
    names = {int(k): v for k, v in (side.get("ids") or {}).items()}
    if not names:
        print(f"contrast_delta: {a.names} has no `ids` block — re-run id_mask.py",
              file=sys.stderr)
        return 2

    b = np.asarray(Image.open(a.beauty).convert("RGB")).astype(np.float32)
    m = np.asarray(Image.open(a.mask).convert("RGB")).astype(np.int16)
    try:
        rows = measure_frame(b, m, names)
    except ContrastError as e:
        print(f"contrast_delta: COULD NOT RUN — {e}", file=sys.stderr)
        return 2

    ok = [r for r in rows if r.get("ok")]

    # ---- the positive control, on the same pixels, before any absence is reported ----
    lum = (0.2126 * b[..., 0] + 0.7152 * b[..., 1] + 0.0722 * b[..., 2])
    ids = VP.decode_ids(m)
    biggest = max(names, key=lambda k: int((ids == int(k)).sum()))
    control_vals = lum[ids == int(biggest)].tolist()
    fired, recovered, detail = positive_control(control_vals)
    print(f"POSITIVE CONTROL on `{names[biggest]}` ({len(control_vals)} px): "
          f"{'FIRED' if fired else 'DID NOT FIRE'} — {detail}")
    if not fired:
        print("contrast_delta: COULD NOT RUN — the splitter did not recover a step it "
              "planted in this frame's own pixels, so neither a reading nor a clean "
              "sheet from it means anything.", file=sys.stderr)
        return 2

    # ---- the reference side, when one was signed ----
    ref_rows = None
    if a.samples:
        if not a.reference:
            print("contrast_delta: --samples without --reference", file=sys.stderr)
            return 2
        ref_img = Image.open(a.reference).convert("RGB")
        rw, rh = ref_img.size
        px = ref_img.load()

        def at(x, y):
            if not (0 <= x < rw and 0 <= y < rh):
                raise ContrastError(f"sample point ({x},{y}) is outside the reference "
                                    f"({rw}x{rh})")
            return px[x, y]

        pairs = (json.load(open(a.samples, encoding="utf-8")) or {}).get("pairs") or []
        try:
            ref_rows = reference_deltas(at, pairs)
        except ContrastError as e:
            print(f"contrast_delta: COULD NOT RUN — {e}", file=sys.stderr)
            return 2

    _ok, bad, frame, ref = summarise(rows, [r["delta"] for r in ref_rows] if ref_rows else None)
    print()
    print(report(_ok, bad, frame, ref))

    # ---- the average-colour check, when a reference is present ----
    if a.reference:
        ours = average_color(np.asarray(Image.open(a.beauty).convert("RGB"))
                             .reshape(-1, 3).tolist())
        theirs = average_color(np.asarray(Image.open(a.reference).convert("RGB"))
                               .reshape(-1, 3).tolist())
        print()
        print(f"AVERAGE COLOUR  ours ({ours[0]:.0f},{ours[1]:.0f},{ours[2]:.0f})  "
              f"reference ({theirs[0]:.0f},{theirs[1]:.0f},{theirs[2]:.0f})  "
              f"gap {color_gap(ours, theirs):.1f}  [reported, not a cut]")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"objects": rows, "reference": ref_rows, "frame_delta": frame,
                       "reference_delta": ref,
                       "control": {"fired": fired, "recovered": recovered,
                                   "object": names[biggest]}},
                      fh, indent=2, ensure_ascii=False)

    if frame is None:
        print("\ncontrast_delta: COULD NOT RUN — the control fired but no real object "
              "split. Nothing in this frame carries a measurable lit/shadow pair.",
              file=sys.stderr)
        return 2

    if a.expect_delta:
        lo, _, hi = a.expect_delta.partition(":")
        lo, hi = float(lo), float(hi)
        if not (lo <= frame <= hi):
            print(f"\ncontrast_delta: FRAME DELTA {frame:.1f} is outside [{lo}, {hi}]",
                  file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
