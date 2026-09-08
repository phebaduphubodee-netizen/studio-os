"""trn001_overlay.py — TRN-001 LOOK instruments: overlay + numeric track. PURE.

Round metric of record (charter rule 6: at least one numeric track per round):
mean landmark reprojection error in px @2048, from the builder's projections
dump vs the measured target landmarks. Plus the LOOK sheets a human judges:
50/50 blend, side-by-side pair, and a red/green edge overlay (target RED,
ours GREEN, aligned YELLOW — same grammar as overlay_fidelity.py).

  python pipeline/scripts/trn001_overlay.py <render.png> <target.png> \
      --proj <projections.json> --targets <landmarks.json> --out <dir> [--tag v001]

All outputs land under the private TRN dir (side-by-sides of the target are
client imagery — never committed, never egressed).
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw


def _load(p, size=2048):
    im = Image.open(p).convert("RGB")
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    return im


def _edges(im):
    g = np.asarray(im.convert("L"), dtype=np.float32)
    gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    gy = np.abs(np.diff(g, axis=0, prepend=g[:1]))
    e = gx + gy
    thr = np.percentile(e, 97.5)
    return e > thr


def sheets(render, target, out_dir, tag):
    r, t = _load(render), _load(target)
    Image.blend(t, r, 0.5).save(os.path.join(out_dir, f"trn001_blend_{tag}.png"))
    pair = Image.new("RGB", (2048 + 8, 1024), (24, 24, 24))
    pair.paste(t.resize((1024, 1024)), (0, 0))
    pair.paste(r.resize((1024, 1024)), (1024 + 8, 0))
    pair.save(os.path.join(out_dir, f"trn001_pair_{tag}.png"))
    et, er = _edges(t), _edges(r)
    ov = np.zeros((2048, 2048, 3), dtype=np.uint8)
    ov[..., 0] = np.where(et, 255, 0)
    ov[..., 1] = np.where(er, 255, 0)
    Image.fromarray(ov).save(os.path.join(out_dir, f"trn001_edges_{tag}.png"))


def metric(proj_path, targets_path, out_dir, tag):
    proj = json.load(open(proj_path, encoding="utf-8"))
    tgts = {t["name"]: t for t in json.load(open(targets_path, encoding="utf-8"))["landmarks"]}
    rows, errs = [], []
    for name, p in sorted(proj.items()):
        if name not in tgts or p.get("blender") is None:
            continue
        u, v = p["blender"]
        du, dv = u - tgts[name]["u"], v - tgts[name]["v"]
        d = math.hypot(du, dv)
        errs.append(d)
        rows.append({"name": name, "du": round(du, 1), "dv": round(dv, 1), "err": round(d, 1)})
        print(f"  {name:18s} du={du:+7.1f} dv={dv:+7.1f}  |{d:6.1f}|")
    summary = {"tag": tag, "n": len(errs),
               "mean_px": round(float(np.mean(errs)), 1) if errs else None,
               "median_px": round(float(np.median(errs)), 1) if errs else None,
               "max_px": round(float(np.max(errs)), 1) if errs else None,
               "rows": rows}
    print(f"mean={summary['mean_px']}px median={summary['median_px']}px max={summary['max_px']}px @2048")
    with open(os.path.join(out_dir, f"trn001_metric_{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("target")
    ap.add_argument("--proj", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="v001")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sheets(a.render, a.target, a.out, a.tag)
    metric(a.proj, a.targets, a.out, a.tag)


if __name__ == "__main__":
    main()
