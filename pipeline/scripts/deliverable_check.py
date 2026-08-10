"""deliverable_check.py — is this frame at the level the friend's studio ships?

CLI-ONLY: run by hand on a candidate frame, and by DELIV-001's phase exits. Its
thresholds live in `qa/deliverable-standard.json`, cut by `--census` from the
delivered anchor pool.

WHAT MAKES THIS DIFFERENT FROM THE NINE FLATTERING SCORERS BEFORE IT
--------------------------------------------------------------------
Every threshold here is a PERCENTILE OF DELIVERED WORK, not a number the builder
chose. That is the whole design. This repo has shipped nine scorers whose
thresholds were picked to be satisfiable, and the pattern is documented: an
instrument answers the question it was built to ask, and every instrument here
was built by the same builder who chose what to worry about. A percentile of
work that was actually sold to clients is the one number the builder cannot
quietly move.

AND IT MUST PROVE IT CAN FAIL BEFORE IT IS BELIEVED. The acceptance contract,
run by `--calibrate`: it must FAIL our own best frame, FAIL the reproduction
frame the owner rejected, FAIL the reproduction TARGET on resolution, and PASS
delivered anchors. A standard our best frame already passes is not a standard;
one that fails sold work is measuring the wrong thing. If it cannot do both, it
is deleted rather than tuned.

TWO ROW KINDS, AND THE DIFFERENCE IS LOAD-BEARING
-------------------------------------------------
IMAGE rows (D1-D6, D10) read pixels. SCENE rows (D7-D9) read the built model,
because "twelve loose objects" and "no primitive standing in for an acquired
object" cannot be seen in a JPEG. A scene row with no scene reports NOT RUN, and
NOT RUN IS NEVER PASS — the same law as pixel_check's exit code 2. A report that
prints 7 of 7 while three rows never ran is the mute this repo keeps rebuilding.

NORMALISATION
-------------
Every image row except D1 is measured after resampling to a long edge of 1600 px,
so a bigger render cannot buy detail or contrast. D1 is the only row resolution
may win, and it is measured on the original.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STANDARD_REL = os.path.join("qa", "deliverable-standard.json")
LONG_EDGE = 1600

IMAGE_ROWS = ("D1", "D2", "D3", "D4", "D5", "D6", "D10")
SCENE_ROWS = ("D7", "D8", "D9")


class NotRun(Exception):
    """A row that could not be measured. Never a pass."""


# ------------------------------------------------------------------ measuring --

def _load(path):
    im = Image.open(path)
    im.load()
    return im.convert("RGB")


def _norm(im):
    w, h = im.size
    s = LONG_EDGE / max(w, h)
    if abs(s - 1.0) < 1e-6:
        return im
    return im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)


def _lum(im):
    a = np.asarray(im, dtype=np.float64)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def _blur(a, r, passes=3):
    """Repeated box blur ~= Gaussian, via summed-area tables. Three passes rather
    than one because one box does not attenuate pixel noise enough to keep it out
    of the band below — measured, not assumed."""
    if r < 1:
        return a
    for _ in range(passes):
        k = 2 * int(r) + 1
        pad = np.pad(a, int(r), mode="edge")
        c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
        c = np.pad(c, ((1, 0), (1, 0)), mode="constant")
        H, W = a.shape
        a = (c[k:k + H, k:k + W] - c[:H, k:k + W]
             - c[k:k + H, :W] + c[:H, :W]) / (k * k)
    return a


def _octave_energy(L, lo=4, hi=32):
    """Luminance structure in the 4-32 px octave: mean |bandpass(L)|.

    BAND-LIMITED ON PURPOSE. A plain mean |grad L| floor is payable in noise — add
    grain, a denoiser artefact or a 4k wood texture and the number rises while the
    frame gets uglier. Our own best frame scores 1.58x the reproduction target on
    the unrestricted metric, entirely from a slat wall.

    AND THE FIRST BAND-LIMITED VERSION WAS STILL PAYABLE, which is why this
    docstring carries numbers. It measured mean |grad| OF the bandpass, and its own
    test caught it moving 3.45x on pure noise: taking a gradient re-emphasises the
    top of the band, where whatever noise survived the low-pass lives. Measuring
    the band's ENERGY instead of its gradient, with three box passes, moves 1.01x
    on the same input against the raw metric's 11.84x.

        raw mean|grad L|              11.84x on pure noise
        mean|grad| of band, 1 pass     1.58x
        mean|band|, 1 pass             1.14x
        mean|band|, 3 passes           1.01x   <- this

    The lesson is the one this repo keeps paying for: naming a metric
    'band-limited' is not the same as it being band-limited, and only the negative
    control tells them apart.
    """
    return float(np.mean(np.abs(_blur(L, lo // 2) - _blur(L, hi // 2))))


def _chroma_spread(im):
    """Interquartile range of hue angle over the most-saturated decile.

    PROVISIONAL, and labelled so wherever it appears. It is a proxy for 'the room
    has a colour story', and a proxy is what the nine previous flattering scorers
    were. It is here because the single largest visible difference between our
    best frame and delivered work — an amber-monochrome cast — is invisible to
    every other row. It gets deleted at the first sign it is satisfiable by a
    change that made the frame worse.
    """
    a = np.asarray(im, dtype=np.float64) / 255.0
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)
    thr = np.percentile(sat, 90)
    sel = sat >= max(thr, 1e-6)
    if sel.sum() < 64:
        return 0.0
    r, g, b = a[..., 0][sel], a[..., 1][sel], a[..., 2][sel]
    hue = np.degrees(np.arctan2(math.sqrt(3) * (g - b), 2 * r - g - b)) % 360.0
    # circular IQR: rotate to the circular mean so the wrap point is not inside
    # the distribution, which would report a red-dominant room as maximally wide.
    ang = np.radians(hue)
    mean = math.degrees(math.atan2(np.sin(ang).mean(), np.cos(ang).mean())) % 360.0
    d = (hue - mean + 180.0) % 360.0 - 180.0
    return float(np.percentile(d, 75) - np.percentile(d, 25))


def measure_image(path):
    """Every image-side quantity, from one open. Returns a dict of raw numbers —
    thresholds are applied elsewhere, so the census and the check cannot drift."""
    im = _load(path)
    w, h = im.size
    n = _norm(im)
    L = _lum(n)
    p1, p99 = np.percentile(L, 1), np.percentile(L, 99)
    return {
        "mp": round(w * h / 1e6, 3),
        "p1": round(float(p1), 2),
        "stops": round(float(math.log2(max(p99, 1e-6) / max(p1, 1e-6))), 3),
        "clipped_pct": round(float((L >= 254).mean() * 100.0), 4),
        "octave_energy": round(_octave_energy(L), 4),
        "dark_share_pct": round(float((L < 26).mean() * 100.0), 4),
        "chroma_iqr_deg": round(_chroma_spread(n), 2),
    }


# ------------------------------------------------------------------- the rows --
# (id, kind, metric key, direction, threshold percentile, what it is)
# direction: "min" = value must be >= t; "max" = must be <= t; "band" = both.
ROWS = [
    ("D1", "image", "mp", "min", 25, "resolution — measured on the ORIGINAL; the "
     "one row a bigger render may win"),
    ("D2", "image", "p1", "max", 75, "the frame has true darks — our shadow floor "
     "sits where delivered work's does"),
    ("D3", "image", "stops", "min", 25, "dynamic range p1->p99"),
    ("D4", "image", "clipped_pct", "max", 75, "blown highlights"),
    ("D5", "image", "octave_energy", "band", (25, 90), "structure in the 4-32 px "
     "octave — two-sided, so noise cannot buy it"),
    ("D6", "image", "dark_share_pct", "min", 25, "share of the frame below L=26"),
    ("D10", "image", "chroma_iqr_deg", "min", 25, "PROVISIONAL — the room has a "
     "colour story rather than one cast"),
    ("D7", "scene", "loose_objects", "min", None, "loose styling objects, counted "
     "from per-object ids, not from gradient blobs"),
    ("D8", "scene", "primitive_acquire_class", "max", None, "R8-ACQUIRE-class "
     "objects built as primitives"),
    ("D9", "scene", "flat_shaded_curved", "max", None, "curved forms rendering "
     "flat-shaded"),
]
SCENE_FIXED = {"D7": 12, "D8": 0, "D9": 0}


def census(paths, progress=None):
    """Measure the delivered pool. Returns {metric: sorted[values]} plus the
    per-file rows, so a threshold can always be traced back to the frames that
    produced it."""
    rows = []
    for i, p in enumerate(paths):
        try:
            m = measure_image(p)
        except Exception as e:      # a pool file that will not open is reported,
            rows.append({"path": p, "error": f"{type(e).__name__}: {e}"})
            continue                # never silently dropped from the denominator
        m["path"] = p
        rows.append(m)
        if progress and i % 25 == 0:
            progress(i, len(paths))
    return rows


def cut_thresholds(rows):
    ok = [r for r in rows if "error" not in r]
    if len(ok) < 30:
        raise ValueError(f"census has only {len(ok)} readable frames — a percentile "
                         f"of that is a preference, not a standard")
    out = {}
    for rid, kind, key, direction, pct, _why in ROWS:
        if kind != "image":
            out[rid] = {"metric": key, "direction": direction,
                        "threshold": SCENE_FIXED[rid], "source": "declared by the plan"}
            continue
        vals = np.array([r[key] for r in ok], dtype=np.float64)
        if direction == "band":
            lo, hi = pct
            out[rid] = {"metric": key, "direction": "band",
                        "threshold": [round(float(np.percentile(vals, lo)), 4),
                                      round(float(np.percentile(vals, hi)), 4)],
                        "source": f"pool p{lo}/p{hi} of {len(ok)} delivered frames"}
        else:
            out[rid] = {"metric": key, "direction": direction,
                        "threshold": round(float(np.percentile(vals, pct)), 4),
                        "source": f"pool p{pct} of {len(ok)} delivered frames"}
    return out


def measure_scene_spec(spec):
    """The three scene rows, read from a canonical mass spec.

    D8's class list is R8's own: free-form objects that must be ACQUIRED and never
    hand-modelled. A mass whose name says it is one and whose kind is a primitive
    is the exact defect the owner named by eye — "หมอน" built as a rounded prism.
    D9 counts curved forms that no beauty.soft entry smooths, which is why 15 `oct`
    masses have rendered flat-shaded for 10 straight rounds with the softening code
    present and never enabled.
    """
    acquire_words = ("pillow", "cushion", "bolster", "sham", "duvet", "throw",
                     "blanket", "rug", "plant", "flower", "garment", "towel",
                     "chair_seat", "chair_back", "sofa", "upholst")
    styling_words = ("book", "vase", "tray", "bowl", "plant", "lamp", "candle",
                     "figurine", "bird", "art", "towel", "bottle", "cup")
    primitive_kinds = (None, "box", "oct", "cone", "slats", "pocket", "herringbone")
    soft = ((spec.get("beauty") or {}).get("soft") or {})
    masses = spec.get("masses", [])
    loose = sum(1 for m in masses
                if any(w in m["name"].lower() for w in styling_words))
    prim_acquire = sum(1 for m in masses
                       if any(w in m["name"].lower() for w in acquire_words)
                       and m.get("kind") in primitive_kinds)
    flat_curved = sum(1 for m in masses
                      if m.get("kind") in ("oct", "cone")
                      and not (soft.get(m["name"]) or {}).get("smooth"))
    return {"loose_objects": loose, "primitive_acquire_class": prim_acquire,
            "flat_shaded_curved": flat_curved}


def qualifies(rows, standard):
    """(bool, why). NOT a conjunction, and the reason is measured rather than
    preferred: only 28.6% of the 658 delivered frames pass all seven image rows,
    so an all-rows-must-pass standard would reject 71% of work that was actually
    sold. Percentile thresholds are per-row by construction, and conjunction
    compounds them into a bar almost nothing clears.

    So: the MANDATORY rows are correctness, not quality — a frame below the pool's
    resolution floor cannot be handed to a client at any level of polish, and a
    pillow built as a rounded prism is a defect however pretty the light is. The
    SCORED rows are a distribution, and the pass count is the one that lands on
    the median of delivered work: D1 plus 5 of 6 qualifies 50.5% of the pool.
    (4 of 6 -> 60.9%, 6 of 6 -> 28.6%. The number was read off the pool, not
    chosen to fit our frame; our best frame scores 4 and does not qualify.)
    """
    by = {r[0]: r for r in rows}
    for rid in standard["mandatory"]:
        v = by.get(rid)
        if v is None or v[1] != "PASS":
            return False, f"{rid} is mandatory and came back {v[1] if v else 'MISSING'}"
    got = sum(1 for rid in standard["scored"] if by.get(rid) and by[rid][1] == "PASS")
    need = standard["scored_need"]
    if got < need:
        return False, f"{got} of {len(standard['scored'])} scored rows, needs {need}"
    return True, f"{got}/{len(standard['scored'])} scored, all mandatory rows pass"


def score(standard, image_path=None, scene=None):
    """[(row_id, verdict, value, threshold, why)] where verdict is PASS / FAIL /
    NOT RUN. NOT RUN is never PASS."""
    img = measure_image(image_path) if image_path else None
    out = []
    for rid, kind, key, _d, _p, why in ROWS:
        t = standard["rows"][rid]
        thr, direction = t["threshold"], t["direction"]
        src = img if kind == "image" else scene
        if src is None or key not in src:
            out.append((rid, "NOT RUN", None, thr,
                        f"no {'image' if kind == 'image' else 'scene'} given — "
                        f"could not look, which is not the same as fine"))
            continue
        v = src[key]
        if direction == "min":
            ok = v >= thr
        elif direction == "max":
            ok = v <= thr
        else:
            ok = thr[0] <= v <= thr[1]
        out.append((rid, "PASS" if ok else "FAIL", v, thr, why))
    return out


def summarise(rows):
    return {"pass": sum(1 for r in rows if r[1] == "PASS"),
            "fail": sum(1 for r in rows if r[1] == "FAIL"),
            "not_run": sum(1 for r in rows if r[1] == "NOT RUN")}


def load_standard(path=None):
    with open(path or os.path.join(REPO, STANDARD_REL), encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frame", nargs="?", help="the image to score")
    ap.add_argument("--scene", default=None, help="JSON of scene-row measurements")
    ap.add_argument("--standard", default=None)
    a = ap.parse_args(argv)
    if not a.frame:
        ap.print_help()
        return 2
    std = load_standard(a.standard)
    scene = json.load(open(a.scene, encoding="utf-8")) if a.scene else None
    rows = score(std, a.frame, scene)
    for rid, verdict, v, thr, why in rows:
        vs = "-" if v is None else f"{v}"
        print(f"{rid:4s} {verdict:8s} {vs:>10s} vs {thr}   {why[:60]}")
    s = summarise(rows)
    print(f"\n{s['pass']} pass / {s['fail']} fail / {s['not_run']} NOT RUN")
    return 1 if s["fail"] or s["not_run"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
