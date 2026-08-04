"""trn002_lightcheck.py — the phase-2 numeric track: light + value, PURE (no bpy).

    python pipeline/scripts/trn002_lightcheck.py <ours.png> <target.jpg> \
        <idmask.png> [--json out.json] [--erode 3] [--min-px 250]

WHAT IT MEASURES AND WHY IT IS DIFFERENT FROM trn001_lightcheck.

TRN-001's version compares named patches that were TYPED as pixel boxes. That
works, but it inherits the eyeball: a typed box is a guess about where a surface
is, and this lane has now lost two rounds to exactly that class (the shelf column
was rebuilt twice from crop-edge reads). TRN-002 does not need to guess. The
blockout closed with every mass measured and the frame's landmarks reprojecting
at 0.09 px mean — so an OBJECT-ID MASK rendered from our own scene marks, per
pixel, which measured surface is there. **Because the geometry agrees with the
target to sub-pixel, the same pixel set samples the same physical surface in
BOTH frames.** That claim is the instrument's foundation and it is checkable:
it is the landmark table in every projections.json.

Three readings:

  LADDER   per-object median linear luminance in both frames, each normalised to
           a REFERENCE object, so a pure exposure difference cancels and only
           the SHAPE of the light is compared. A frame whose ladder is
           compressed is flat, and this says by how much and WHERE.
  RANGE    p1/p5/p50/p95/p99 and p99/p1 of each frame. The 2026-07-30
           ground-truth study measured photoreal references at 191:1 to 2500:1
           against our 10:1 — light range is the studio's named #1 gap, so it
           gets a number here, never an adjective.
  SPREAD   the target contains objects we do not model (vases, books, a bird
           sculpture, plants). Where they sit inside one of our masks, the
           target-side sample is not that surface at all. Every row carries the
           target-side IQR/median so a dispersed region cannot be read as a
           clean measurement.
           **AND THE FLAG NAMES WHAT IT MEASURES, NOT A CAUSE IT CANNOT SEE.**
           A first cut called this "contaminated", which asserts foreign
           content — but a wall running from window-bright to corner-dark is
           legitimately dispersed and perfectly clean. Dispersion has two
           causes and IQR alone cannot separate them, so the row reports BOTH
           frames' spread: ours shares the target's geometry and carries a
           smooth light, so `spread_ratio = target_spread / ours_spread` near
           1 means a real gradient both frames see, while a large ratio means
           the target holds something ours does not. Naming a cause the
           instrument cannot distinguish is how a metric starts flattering.

DISCIPLINE THIS FILE ENFORCES SO THE CALLER CANNOT SKIP IT:
  * Absolute values between frames are never compared — only ratios within a
    frame (different exposure, different render).
  * Masks are ERODED before sampling. An un-eroded mask includes the
    antialiased boundary, where a bright neighbour bleeds in; that is the
    "a 30 px strip is not a surface" error in its per-object form.
  * A row with too few surviving pixels is reported as UNMEASURABLE, not
    averaged from noise.
"""
import argparse
import json

import numpy as np
from PIL import Image


def _linear(path, wh=None):
    im = Image.open(path).convert("RGB")
    if wh and im.size != wh:
        raise SystemExit(f"{path} is {im.size}, expected {wh} — a mask from a "
                         f"different frame size measures nothing")
    a = np.asarray(im, dtype=np.float32) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _lum(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def decode_mask(mask_png, mask_json):
    """id-image (H,W) of integer ids + {id: name}.

    The palette codec is value_probe's and is IMPORTED, never re-implemented
    here. value_probe's own header states the rule ("ONE definition, both
    halves") and id_mask.py already obeys it; a second copy of a codec is how
    a mask decodes to plausible-looking garbage after the original changes.
    Decoding is nearest-level per channel, which is what makes an antialiased
    silhouette land on one of its two neighbours rather than nowhere — the
    erosion below is what removes those pixels from the sample."""
    import value_probe as VP
    with open(mask_json, encoding="utf-8") as f:
        doc = json.load(f)
    # id_mask's sidecar is {"source": {...provenance...}, "ids": {id: name}}.
    # The provenance block is not optional decoration: it records the camera and
    # matrix the mask was rendered from, which is the claim that the mask and
    # the beauty frame are the same view.
    raw = doc.get("ids", doc)
    rgb = np.asarray(Image.open(mask_png).convert("RGB"), dtype=np.int16)
    n = len(VP.LEVELS)
    lv = np.abs(rgb[..., None, :3]
                - np.array(VP.LEVELS, dtype=np.int16)[None, None, :, None]
                ).argmin(axis=2)
    ids = (lv[..., 0] * n * n + lv[..., 1] * n + lv[..., 2]).astype(np.int32)
    names = {}
    for sid, entry in raw.items():
        name = entry if isinstance(entry, str) else entry.get("name", str(entry))
        names[int(sid)] = name
    return ids, names


def _spread(sample, med):
    """IQR normalised by the median — dimensionless, so a dark surface and a
    bright one are comparable. Returns a large sentinel for a near-black median
    rather than dividing by it."""
    q1, q3 = np.percentile(sample, [25, 75])
    return float((q3 - q1) / med) if med > 1e-6 else 9.99


def erode(mask_bool, k):
    """Shrink a boolean region by k pixels (4-neighbour). Pure numpy — no scipy
    dependency, and k is small."""
    m = mask_bool
    for _ in range(k):
        m = (m
             & np.roll(m, 1, 0) & np.roll(m, -1, 0)
             & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    return m


def ladder(ours_png, target_png, mask_png, mask_json, erode_px=3, min_px=250,
           dirty=0.55, ref=None):
    ours = _lum(_linear(ours_png))
    tgt = _lum(_linear(target_png, wh=Image.open(ours_png).size))
    ids, names = decode_mask(mask_png, mask_json)
    if ids.shape != ours.shape:
        raise SystemExit(f"mask {ids.shape} vs frame {ours.shape} — refusing")

    rows = {}
    for i, name in names.items():
        if i == 0:
            continue
        m = erode(ids == i, erode_px)
        n = int(m.sum())
        short = name.replace("SM_TRN002_", "")
        if n < min_px:
            rows[short] = {"n_px": n, "status": "UNMEASURABLE (too few pixels "
                                                "after erosion — occluded or tiny)"}
            continue
        o, t = ours[m], tgt[m]
        o_med, t_med = float(np.median(o)), float(np.median(t))
        t_spread = _spread(t, t_med)
        o_spread = _spread(o, o_med)
        rows[short] = {
            "n_px": n,
            "ours": o_med,
            "target": t_med,
            "target_spread": round(t_spread, 3),
            "ours_spread": round(o_spread, 3),
            # >1 means the target is more varied here than our same-geometry,
            # smoothly-lit frame is — the signature of content we do not model.
            # ~1 with both high means a gradient BOTH frames see: clean.
            "spread_ratio": round(t_spread / o_spread, 2) if o_spread > 1e-3 else None,
            "dispersed": bool(t_spread > dirty),
        }

    # The ladder reference must be a surface whose median is a clean sample:
    # low dispersion in BOTH frames, so neither a foreign object nor a strong
    # gradient is setting the number every other row is divided by.
    clean = {k: v for k, v in rows.items()
             if "ours" in v and not v["dispersed"] and v["ours_spread"] <= dirty}
    if ref is None:
        # the reference must be a LARGE, CLEAN, singly-lit surface; pick the
        # biggest clean row rather than typing a name, so the choice is derived
        ref = max(clean, key=lambda k: clean[k]["n_px"]) if clean else None
    out = {"reference": ref, "rows": rows}
    if ref and ref in clean:
        ro, rt = clean[ref]["ours"], clean[ref]["target"]
        for k, v in rows.items():
            if "ours" not in v:
                continue
            v["ours_rel"] = round(v["ours"] / ro, 4) if ro > 1e-9 else None
            v["target_rel"] = round(v["target"] / rt, 4) if rt > 1e-9 else None
            if v["ours_rel"] and v["target_rel"]:
                v["ladder_error"] = round(v["ours_rel"] / v["target_rel"], 3)
    return out


def frame_range(path):
    l = _lum(_linear(path)).ravel()
    p = np.percentile(l, [1, 5, 50, 95, 99])
    return {"p1": float(p[0]), "p5": float(p[1]), "p50": float(p[2]),
            "p95": float(p[3]), "p99": float(p[4]),
            "range_99_1": float(p[4] / p[0]) if p[0] > 1e-9 else float("inf")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours")
    ap.add_argument("target")
    ap.add_argument("mask")
    ap.add_argument("--mask-json", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--erode", type=int, default=3)
    ap.add_argument("--min-px", type=int, default=250)
    ap.add_argument("--ref", default=None)
    a = ap.parse_args()
    mj = a.mask_json or (a.mask.rsplit(".", 1)[0] + ".json")

    lad = ladder(a.ours, a.target, a.mask, mj, a.erode, a.min_px, ref=a.ref)
    ro, rt = frame_range(a.ours), frame_range(a.target)

    print(f"RANGE          {'ours':>12s} {'target':>12s}")
    for k in ("p1", "p5", "p50", "p95", "p99", "range_99_1"):
        print(f"  {k:11s} {ro[k]:12.4f} {rt[k]:12.4f}")
    print(f"\nLADDER (relative to {lad['reference']}; ladder_error 1.00 = our "
          f"light puts this surface at the target's own relative brightness)")
    print(f"  {'object':22s} {'n_px':>7s} {'ours_rel':>9s} {'tgt_rel':>9s} "
          f"{'err':>6s} {'spr':>5s}  note")
    meas = [(k, v) for k, v in lad["rows"].items() if v.get("ladder_error")]
    for k, v in sorted(meas, key=lambda kv: -abs(np.log(kv[1]["ladder_error"]))):
        sr = v.get("spread_ratio")
        if v["dispersed"]:
            note = ("target holds content we do not model" if sr and sr > 1.6
                    else "gradient both frames see")
        else:
            note = ""
        print(f"  {k:22s} {v['n_px']:7d} {v['ours_rel']:9.3f} "
              f"{v['target_rel']:9.3f} {v['ladder_error']:6.2f} "
              f"{(f'{sr:5.2f}' if sr else '    -')}  {note}")
    skipped = [k for k, v in lad["rows"].items() if "ours" not in v]
    if skipped:
        print(f"\n  UNMEASURABLE ({len(skipped)}): {', '.join(sorted(skipped))}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"ladder": lad, "range_ours": ro, "range_target": rt},
                      f, indent=1)
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
