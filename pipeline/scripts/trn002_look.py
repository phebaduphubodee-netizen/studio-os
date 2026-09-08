"""trn002_look.py — the R4 LOOK sheets for TRN-002. PURE (no bpy).

    python pipeline/scripts/trn002_look.py <ours.png> [--tag r6] \
        [--zone bed_platform,pillow_L] [--zone shelf_col_back] [--scale 3]

Writes, under the lane's `look/` dir:
    trn002_pair_<tag>.png     target | ours, side by side at full size
    trn002_blend_<tag>.png    50/50 blend — the exhibit that shows whether our
                              edges ride the target's own lines
    trn002_zone_<name>_<tag>.png   target | ours, cropped to a named zone

WHY ZONES ARE NAMED BY OBJECT AND NOT TYPED AS PIXEL BOXES. Every crop in this
lane's first five rounds was a hand-typed box, and two column rebuilds came out
of reading edges inside one (a 3x crop reads to about +-30 mm per edge, and
worse, THE CROP'S OWN BOUNDARY became the design's boundary — the r4 shelf
measurement never asked what was above its window). The blockout closed with
every mass measured, so a zone can be derived: name the masses, project their
corners through the solved camera, take the union, pad it. The frame decides
where to look, not my hand.

TARGET IMAGERY IS LOCAL-ONLY (R7b). Every sheet this writes contains the
target and therefore lives under `_private/`; the writer refuses any other
destination rather than trusting the caller to remember.
"""
import argparse
import json
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import trn002_geom as G  # noqa: E402

REPO = os.path.dirname(os.path.dirname(_HERE))
LANE = os.path.join(REPO, "_private", "benchmark", "reproduction", "TRN-002")
TARGET = os.path.join(LANE, "target.jpg")
LOOK = os.path.join(LANE, "look")


def _assert_private(path):
    """A sheet holding target pixels may only be written inside _private/."""
    p = os.path.abspath(path)
    if os.path.join(os.sep, "_private", "") not in p + os.sep:
        raise SystemExit(f"refusing to write target imagery outside _private/: {p}")
    return p


def zone_box(spec, names, pad=40):
    """Union of the named masses' projected corners, padded, clipped to frame."""
    cam = spec["camera"]
    wh = (spec["image"]["w"], spec["image"]["h"])
    by = {m["name"]: m for m in spec["masses"]}
    us, vs = [], []
    for n in names:
        if n not in by:
            raise SystemExit(f"no mass named '{n}' in the spec")
        c, s = by[n]["c"], by[n]["s"]
        for dx in (-1, 1):
            for dy in (-1, 1):
                for dz in (-1, 1):
                    uv = G.project(cam, (c[0] + dx * s[0] / 2, c[1] + dy * s[1] / 2,
                                         c[2] + dz * s[2] / 2), wh)
                    if uv:
                        us.append(uv[0])
                        vs.append(uv[1])
    if not us:
        raise SystemExit(f"zone {names} projects entirely behind the camera")
    return (max(0, int(min(us)) - pad), max(0, int(min(vs)) - pad),
            min(wh[0], int(max(us)) + pad), min(wh[1], int(max(vs)) + pad))


def _side_by_side(a, b, gap=8, bg=(200, 60, 60)):
    """Target LEFT, ours RIGHT, with a hard divider — the divider is deliberate:
    a seamless join invites reading the pair as one image and comparing our
    frame against itself, which is the habit R4 exists to break."""
    w, h = a.size
    sheet = Image.new("RGB", (w * 2 + gap, h), bg)
    sheet.paste(a, (0, 0))
    sheet.paste(b, (w + gap, 0))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours")
    ap.add_argument("--tag", default=None, help="defaults to the render's stem")
    ap.add_argument("--spec", default=os.path.join(REPO, "training", "TRN-002",
                                                   "spec_r7.json"))
    ap.add_argument("--zone", action="append", default=[],
                    help="comma-separated mass names; repeatable")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--pad", type=int, default=40)
    a = ap.parse_args()

    tag = a.tag or os.path.splitext(os.path.basename(a.ours))[0].replace(
        "trn002_blockout_", "").replace("trn002_", "")
    ours = Image.open(a.ours).convert("RGB")
    tgt = Image.open(TARGET).convert("RGB")
    if ours.size != tgt.size:
        ours = ours.resize(tgt.size, Image.LANCZOS)
        print(f"note: render upscaled to the target's {tgt.size} for the sheets "
              f"— zone crops are therefore NOT a resolution comparison")
    os.makedirs(LOOK, exist_ok=True)

    p = _assert_private(os.path.join(LOOK, f"trn002_pair_{tag}.png"))
    _side_by_side(tgt, ours).save(p)
    print(f"wrote {p}")
    b = _assert_private(os.path.join(LOOK, f"trn002_blend_{tag}.png"))
    Image.blend(tgt, ours, 0.5).save(b)
    print(f"wrote {b}")

    if a.zone:
        with open(a.spec, encoding="utf-8") as f:
            spec = json.load(f)
        for group in a.zone:
            names = [n.strip() for n in group.split(",") if n.strip()]
            box = zone_box(spec, names, a.pad)
            ct, co = tgt.crop(box), ours.crop(box)
            if a.scale != 1:
                sz = (ct.width * a.scale, ct.height * a.scale)
                ct, co = ct.resize(sz, Image.LANCZOS), co.resize(sz, Image.LANCZOS)
            label = "_".join(names)[:40]
            z = _assert_private(os.path.join(LOOK, f"trn002_zone_{label}_{tag}.png"))
            _side_by_side(ct, co).save(z)
            print(f"wrote {z}  (box {box} from {len(names)} mass(es))")


if __name__ == "__main__":
    main()
