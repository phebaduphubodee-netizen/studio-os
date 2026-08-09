"""texture_check.py — how much PER-PIXEL surface detail the target has that we do not.

    python pipeline/scripts/texture_check.py --ours <r.png> --target <t.jpg> \
        --mask <r.idmask.png> --mask-json <r.idmask.json> [--spec <spec.json>] \
        [--sigmas 1,2,4] [--min-px 2000]

WHY THIS IS NOT THE LADDER'S `spread_ratio`
-------------------------------------------
`trn002_lightcheck.ladder` already reports IQR/median per object for both frames,
and its comment is right that a ratio above 1 means "content we do not model".
But that number sums TWO different things:

    a LIGHTING GRADIENT across a surface   (low spatial frequency)
    SURFACE TEXTURE                        (high spatial frequency)

and they have different fixes. r32 measured the first one and settled it: our
light modulates each material at ~0.92 of the target's within-material range, so
the light is not what flattens this room. The second one had never been measured
here at all — which matters, because the one controlled experiment in the
literature on why images read as CG (Rademacher, Lengyel, Cutrell & Whitted,
EGRW 2001, n=18) found surface roughness the STRONGEST cue it tested, ahead of
shadow softness, at ℜ .71 rough vs .39 smooth, χ²=13.04, p=.0003.

So: high-pass, then compare.

    hf(σ) = std(L − blur(L, σ)) / median(L)      per object, per frame
    ratio = hf_target / hf_ours

Dimensionless, so a dark surface and a bright one are comparable — the same
reasoning `_spread` gives for normalising by the median.

THE TWO CONFOUNDS BOTH PUSH AGAINST A POSITIVE RESULT, which is what makes one
worth acting on:
  - our render carries sampling noise, which INFLATES our hf
  - the target is a JPEG, and compression erodes fine detail, deflating its hf
One exception, stated so nobody has to rediscover it: JPEG blocking is on an
8×8 grid, so at σ≳4 some of the target's residual IS the codec. Fine-scale
readings (σ=1–2) are the trustworthy ones; treat a coarse-scale finding as a
hypothesis, not a measurement.

READ THE SCALES SEPARATELY. They answer different questions, and on this lane's
r32 frame they gave opposite answers:

    σ=1   unmapped materials 5.38×, mapped 2.95×   → no map means no fine grain
    σ=4   unmapped materials 1.91×, mapped 2.42×   → our maps deliver fine grain
                                                     and NOT the coarse variation

A single averaged number would have hidden that, and "add more texture" would
have been the wrong prescription for half the frame.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter


def hf_field(im, sigma):
    """High-pass residual of a PIL 'L' image, as float32."""
    a = np.asarray(im, dtype=np.float32)
    lo = np.asarray(im.filter(ImageFilter.GaussianBlur(sigma)), dtype=np.float32)
    return a - lo


def hf(values_hf, values, eps=4.0):
    """std of the residual over the median of the signal. None on a near-black
    surface, where the normalisation would divide by noise."""
    med = float(np.median(values))
    if med < eps:
        return None
    return float(np.std(values_hf) / med)


def load_luma(path, wh=None):
    im = Image.open(path).convert("L")
    if wh and im.size != wh:
        im = im.resize(wh, Image.LANCZOS)
    return im


def audit(ours_png, target_png, mask_png, mask_json, sigmas=(1.0, 2.0, 4.0),
          min_px=2000, erode_px=3, material_of=None, flat_keys=frozenset()):
    """Return rows, one per measurable object. Needs the lane's mask codec."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import trn002_lightcheck as LC

    ours_im = load_luma(ours_png)
    tgt_im = load_luma(target_png, wh=ours_im.size)
    ours = np.asarray(ours_im, dtype=np.float32)
    tgt = np.asarray(tgt_im, dtype=np.float32)
    o_hf = {s: hf_field(ours_im, s) for s in sigmas}
    t_hf = {s: hf_field(tgt_im, s) for s in sigmas}

    ids, names = LC.decode_mask(mask_png, mask_json)
    if ids.shape != ours.shape:
        raise SystemExit(f"mask {ids.shape} vs frame {ours.shape} — refusing")

    rows = []
    for i, name in names.items():
        if i == 0:
            continue
        m = LC.erode(ids == i, erode_px)
        n = int(m.sum())
        if n < min_px:
            continue
        short = name.replace("SM_TRN002_", "")
        key = (material_of or {}).get(short)
        row = {"object": short, "n_px": n, "material": key,
               "mapped": (key not in flat_keys) if key else None, "sigma": {}}
        skip = False
        for s in sigmas:
            a, b = hf(o_hf[s][m], ours[m]), hf(t_hf[s][m], tgt[m])
            if a is None or b is None or a < 1e-6:
                skip = True
                break
            row["sigma"][s] = {"ours": round(a, 4), "target": round(b, 4),
                               "ratio": round(b / a, 2),
                               # THE RATIO ALONE PICKS THE WRONG ROUND.
                               # `ward_body` is the largest object in the frame
                               # and reads 10.66x at sigma 1 — but both numbers
                               # are tiny (0.0038 vs 0.0092 at sigma 2): a
                               # lacquered door IS smooth in the target, and a
                               # ratio between two near-zeros explodes. What a
                               # build round should chase is texture that is
                               # ABSENT AND ACTUALLY THERE, weighted by how much
                               # of the frame it covers.
                               "missing": round((b - a) * n / 1e6, 3)}
        if not skip:
            rows.append(row)
    rows.sort(key=lambda r: -r["n_px"])
    return rows


def unreachable_normal_rows(materials):
    """PALETTE side-table entries no code path can reach.

    `build_materials` returns EARLY for a row with no map — so a NORMAL_STRENGTH
    written for an unmapped material is a surface-relief intention that cannot
    be delivered, and reads in the source as a decision someone made. Same class
    as the dead PALETTE rows r30 found, in a different table.

    EMISSIVE is deliberately NOT checked: it is applied BEFORE that early return,
    so an unmapped emissive row is legal. The first version of this audit flagged
    `lens_warm` and was wrong — which table sits on which side of the return is
    the whole question, and it is not visible from the table itself.
    """
    mapped = {k for k, v in materials.PALETTE.items()
              if v[3] and v[3] in materials.MAP_FILE}
    dead = {}
    for tname in ("NORMAL_STRENGTH", "DIFFUSE_OFF", "MAP_ROT", "UV_MAPPED"):
        t = getattr(materials, tname, None)
        if not t:
            continue
        bad = sorted(set(t) - mapped)
        if bad:
            dead[tname] = bad
    return dead


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--mask", required=True)
    ap.add_argument("--mask-json", required=True)
    ap.add_argument("--spec")
    ap.add_argument("--sigmas", default="1,2,4")
    ap.add_argument("--min-px", type=int, default=2000)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import trn002_materials as M
    flat = {k for k, v in M.PALETTE.items() if not v[3]}
    mat_of = {}
    if a.spec:
        spec = json.loads(open(a.spec, encoding="utf-8").read())
        mat_of = {m["name"]: M.material_for(m["name"]) for m in spec["masses"]}

    sigmas = tuple(float(s) for s in a.sigmas.split(","))
    rows = audit(a.ours, a.target, a.mask, a.mask_json, sigmas,
                 a.min_px, material_of=mat_of, flat_keys=flat)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if a.json:
        print(json.dumps({"rows": rows, "dead_declarations": unreachable_normal_rows(M)},
                         indent=2, ensure_ascii=False))
        return

    head = f"{'n_px':>7} {'object':<16} {'material':<19} {'map':<5}"
    for s in sigmas:
        head += f" {('σ' + str(s)):>7}"
    print(head)
    for r in rows:
        line = (f"{r['n_px']:7d} {r['object']:<16} {str(r['material']):<19} "
                f"{'map' if r['mapped'] else 'FLAT':<5}")
        for s in sigmas:
            line += f" {r['sigma'][s]['ratio']:7.2f}"
        print(line)

    lead = sigmas[0]
    ranked = sorted(rows, key=lambda r: -r["sigma"][lead]["missing"])[:10]
    print(f"\nMISSING TEXTURE, frame-weighted at σ={lead} — (target_hf − ours_hf) × px:")
    print(f"{'score':>7} {'object':<16} {'material':<19} {'ours':>7} {'target':>7}")
    for r in ranked:
        d = r["sigma"][lead]
        print(f"{d['missing']:7.3f} {r['object']:<16} {str(r['material']):<19} "
              f"{d['ours']:7.4f} {d['target']:7.4f}")

    print("\nmedian target/ours high-frequency ratio:")
    for s in sigmas:
        f = [r["sigma"][s]["ratio"] for r in rows if not r["mapped"]]
        m = [r["sigma"][s]["ratio"] for r in rows if r["mapped"]]
        print(f"  σ={s:<4} unmapped {np.median(f):5.2f} (n={len(f):2d})   "
              f"mapped {np.median(m):5.2f} (n={len(m):2d})")
    print("  (σ≥4 is partly the target's JPEG blocking — read the fine scales)")

    dead = unreachable_normal_rows(M)
    if dead:
        print("\nDEAD DECLARATIONS — written, unreachable, and readable as a decision:")
        for tname, keys in dead.items():
            print(f"  {tname}: {', '.join(keys)}")


if __name__ == "__main__":
    main()
