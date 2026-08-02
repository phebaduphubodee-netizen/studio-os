"""trn001_matcheck.py — the materials round's NUMERIC TRACK. PURE (no bpy).

Charter rule 6 wants at least one measured number per round. For geometry that
was landmark reprojection error; for materials it is this: sample the SAME
patch of the same surface in our frame and in the target, in linear light, and
report the ratio per material.

What the number can and cannot say, stated up front so the gate does not
over-read it: our light rig is a neutral form light and the target was lit with
a designed rig, so a ratio is NOT expected to be 1.0 — the LIGHT round owns
that. What it does catch is a material whose ratio sits far off its neighbours,
i.e. one surface wrong relative to the rest of the palette, which is exactly
the failure a beauty render hides.

  python pipeline/scripts/trn001_matcheck.py <ours.png> <target.png> [--json out]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image

# patch = (u0, u1, v0, v1) in 2048-space, chosen on flat unoccluded areas that
# carry the SAME material in both frames (styling objects avoided by design).
#
# A patch may be ONE box (the same pixels in both frames) or a per-frame pair
# {"ours": box, "target": box}. THE PAIR IS NOT A CONVENIENCE — a narrow feature
# cannot be sampled by a shared box at all. Round 5 found the row labelled
# "veneer_dark (right stile)" sitting on the CUBBY BACK in BOTH frames: it read
# 0.0205 and 0.0186 linear where a lit stile reads above 0.05, so a cavity was
# being reported as a stile and the two cavity rows silently agreed with each
# other. The stiles are ~10 px wide and the two frames put them 6 px apart
# (target's outer band starts u1937, ours u1943), which is why the box has to be
# located per frame. Same failure class the project has already paid for twice:
# a bounding box that could not tell a vase from a plank, and a return band that
# could not tell a shallow box from a deep pocket. THE INSTRUMENT THAT SCORES
# THE WORK HAS TO BE CHECKED AGAINST THE WORK.
PATCHES = {
    # CLEARED 2026-08-01, after briefly being flagged as suspect. A first ID-mask
    # read resolved this box to brass_p1_bot, which would have meant the row was
    # comparing OUR BRASS INLAY against the target's veneer. The read was wrong,
    # not the patch: the ID pass wrote LINEAR emission and the PNG stores sRGB, so
    # a 0.2 step lands at 0.485 on disk and the decoder was matching encoded
    # values against linear ones. Re-read in linear space with unique per-mass
    # colours it resolves header_p1 95% / brass_p1_top 4% — the panel, correctly.
    # Kept as a note because the instinct to MOVE the patch on the first reading
    # would have broken a working row to satisfy a broken instrument.
    "veneer_dark (header face)": (900, 1200, 300, 360),
    # THE TWO RIGHT-TOWER STILE ROWS ARE GONE, 2026-08-02, and the reason is the
    # point of this note. They read 2.50x and 0.95x and the 2.50 had been on the
    # sheet as a material finding for rounds. An id mask says what they were
    # actually sampling: at this camera `tower_R_sA` is 20 px wide on screen and
    # `tower_R_sB` is 17 px — those panels are 18 mm thick and we are looking at
    # them EDGE ON, so the "stile" being measured is a panel's thickness, not its
    # face. The `ours` box for the outer stile ran u1946-1956 against a feature
    # ending at u1954, i.e. 2 of its 10 columns were off the object entirely.
    # No placement fixes this; the feature is a sliver from this viewpoint.
    #
    # AND THE GUARD BELOW LET THEM THROUGH, which is the part worth keeping.
    # `_check_narrow` asked "is the BOX narrow?" and a 10 px box is fine — on a
    # 400 px panel. The question is whether the FEATURE is narrow, and no box can
    # answer that about itself. Same shape as this lane's other misfires: a
    # bounding box that could not tell a vase from a plank, a return band that
    # could not tell a shallow box from a deep pocket, and a constant drawn around
    # one object reused as a constant. `audit_against_mask` now asks the renderer.
    #
    # veneer_pier keeps its coverage through the L cubby's side wall below, which
    # is 83 px of real face rather than 20 px of edge.
    "cavity (cubby interior)":   (1750, 1800, 700, 850),
    # 2026-08-01: this row USED to be "cavity (lower bay)" at (1750,1800,1150,1300),
    # on the reasoning that a second box further down would report the material
    # rather than a band. An ID-mask read showed both boxes land on the SAME mass
    # (tower_R_back), so the table carried two rows that were never independent —
    # a spread computed over them counts one surface twice. Repointed at the LEFT
    # tower's interior SIDE WALL, verified by ID mask to contain tower_L_sA and
    # nothing else, which also puts the lane's outstanding defect on the sheet:
    # that wall measures 2.05x the target's against a back panel that is exact.
    # RENAMED 2026-08-02. It was "cavity (L side wall)" and it is not cavity: the
    # mask resolves it to `tower_L_sA`, whose material is M_TRN001_veneer_pier.
    # The row was reading a VENEER and reporting it under the cavity's name, which
    # is how the palette table came to carry two rows for the lining and none for
    # the pier face. It is also the lane's only wide view of a pier: 83 px.
    "veneer_pier (L cubby side wall)": (315, 350, 990, 1020),
    "paint_white (left of bay)": (520, 600, 700, 1000),
    "paint_white (right of bay)": (1450, 1550, 700, 1000),
    "marble (clean field)":      (760, 900, 600, 750),
    "lacquer_white (plinth)":    (560, 700, 1560, 1590),
    "veneer_altar (step face)":  (500, 640, 1440, 1470),
    "floor_oak (mid)":           (700, 900, 1850, 1950),
}

# any patch narrower than this must be located per frame, never shared
NARROW_PX = 24

# how much of the dominant object must lie OUTSIDE the box, on every side, before
# the box counts as sitting ON that surface rather than straddling its edge. The
# two stile rows failed at 1 px and -2 px; the surviving rows clear it by 20-500.
FEATURE_MARGIN_PX = 8

# below this the box is sampling more than one surface and reports neither
MIN_DOMINANT_SHARE = 0.90


def _lin(img, box):
    u0, u1, v0, v1 = box
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    s = img.width / 2048.0
    blk = a[int(v0 * s):int(v1 * s), int(u0 * s):int(u1 * s)].reshape(-1, 3)
    lin = np.where(blk <= 0.04045, blk / 12.92, ((blk + 0.055) / 1.055) ** 2.4)
    return np.median(lin, axis=0)


def _boxes(spec):
    """A patch is one shared box, or a per-frame pair. Returns (ours, target)."""
    if isinstance(spec, dict):
        return spec["ours"], spec["target"]
    return spec, spec


def _check_narrow(name, spec):
    """A narrow feature sampled by a SHARED box is the round-5 defect. Refuse it
    rather than reporting a number that names the wrong surface.

    2026-08-02: this checks BOTH axes now. It only ever checked width, and round 18
    of this lane lost three rounds to a defect that hid in the axis no measurement
    looked at — a box is exactly as blind to a 10 px-TALL feature as to a 10 px-wide
    one. Note what this function still cannot do: it knows the box, not the surface
    under it. `audit_against_mask` is the half that asks."""
    if isinstance(spec, dict):
        return
    for axis, lo, hi in (("wide", spec[0], spec[1]), ("tall", spec[2], spec[3])):
        if hi - lo < NARROW_PX:
            raise ValueError(
                f"patch {name!r} is {hi - lo} px {axis} and shared between "
                f"frames; anything under {NARROW_PX} px must give a per-frame box "
                f"({{'ours': ..., 'target': ...}}) or it will sample two different "
                f"surfaces and report them as one material")


def decode_mask(mask_rgb):
    """HxWx3 uint8 id-mask -> HxW integer ids. Same palette as value_probe."""
    import numpy as np
    import value_probe as _vp
    lv = np.abs(mask_rgb[..., None, :3].astype(np.int16)
                - np.array(_vp.LEVELS, dtype=np.int16)[None, None, :, None]).argmin(axis=2)
    n = len(_vp.LEVELS)
    return lv[..., 0] * n * n + lv[..., 1] * n + lv[..., 2]


def audit_against_mask(ids, names, patches=None,
                       margin=FEATURE_MARGIN_PX, min_share=MIN_DOMINANT_SHARE):
    """For each patch: which object owns it, and does that object have ROOM around
    the box on every side?

    THE QUESTION THIS ANSWERS THAT `_check_narrow` CANNOT. A box knows its own size
    and nothing else, so it cannot distinguish a 10 px sample of a 400 px panel
    (fine) from a 10 px sample of a 20 px edge-on sliver (worthless). Only the
    renderer knows which surface a pixel belongs to, so the renderer is asked.

    `margin` is measured against the object's visible extent WITHIN the box's own
    rows/columns, not against its extent anywhere in the frame: a stile that is
    wide at the floor and a sliver at eye height must fail at eye height.

    Returns a row per patch with `ok` False when the box straddles an edge, sits on
    a sliver, or mixes surfaces. Pure — takes decoded arrays, opens nothing.
    """
    import numpy as np
    rows = []
    for name, spec in (patches or PATCHES).items():
        u0, u1, v0, v1 = _boxes(spec)[0]
        blk = ids[v0:v1, u0:u1]
        uniq, cnt = np.unique(blk, return_counts=True)
        top = int(uniq[cnt.argmax()])
        share = float(cnt.max() / blk.size)
        # the dominant object's reach through this box's own band
        band_u = ids[v0:v1, :] == top
        band_v = ids[:, u0:u1] == top
        cols = np.where(band_u.any(axis=0))[0]
        vrows = np.where(band_v.any(axis=1))[0]
        left, right = u0 - int(cols.min()), int(cols.max()) - (u1 - 1)
        above, below = v0 - int(vrows.min()), int(vrows.max()) - (v1 - 1)
        tight = min(left, right, above, below)
        ok = share >= min_share and tight >= margin
        rows.append({"patch": name, "object": names.get(top, "<void/background>"),
                     "share": round(share, 3),
                     "margins": {"left": left, "right": right,
                                 "above": above, "below": below},
                     "tightest": tight, "ok": bool(ok),
                     "why": ("" if ok else
                             ("mixed surfaces" if share < min_share else
                              "box straddles the object's edge" if tight < 0 else
                              "feature is a sliver — no placement fixes it"))})
    return rows


def compare(ours_path, target_path):
    ours, tgt = Image.open(ours_path), Image.open(target_path)
    rows = []
    for name, spec in PATCHES.items():
        _check_narrow(name, spec)
        ob, tb = _boxes(spec)
        o, t = _lin(ours, ob), _lin(tgt, tb)
        ratio = float(np.mean(o) / max(np.mean(t), 1e-6))
        # hue error is lighting-independent in a way brightness is not
        on, tn = o / max(np.mean(o), 1e-6), t / max(np.mean(t), 1e-6)
        rows.append({"patch": name,
                     "per_frame": isinstance(spec, dict),
                     "ours": [round(float(c), 4) for c in o],
                     "target": [round(float(c), 4) for c in t],
                     "value_ratio": round(ratio, 3),
                     "hue_err": round(float(np.max(np.abs(on - tn))), 3)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours")
    ap.add_argument("target")
    ap.add_argument("--json", default=None)
    ap.add_argument("--mask", default=None,
                    help="id-mask PNG from id_mask.py rendered off the SAME build as "
                         "<ours>; audits every patch against the surface it claims")
    a = ap.parse_args()

    if a.mask:
        side = json.load(open(os.path.splitext(a.mask)[0] + ".json", encoding="utf-8"))
        names = {int(k): v for k, v in (side.get("ids") or {}).items()}
        ids = decode_mask(np.asarray(Image.open(a.mask).convert("RGB")))
        bad = []
        print(f"{'patch':34s} {'object':26s} share  tightest margin")
        for r in audit_against_mask(ids, names):
            m = r["margins"]
            print(f"{r['patch']:34s} {r['object']:26s} {r['share']:.2f}   "
                  f"L{m['left']:4d} R{m['right']:4d} A{m['above']:4d} B{m['below']:4d}"
                  f"   {'ok' if r['ok'] else 'REFUSED: ' + r['why']}")
            if not r["ok"]:
                bad.append(r["patch"])
        if bad:
            raise SystemExit(f"\n{len(bad)} patch(es) do not sit on the surface they "
                             f"name: {bad}. A ratio from one of these is not a material "
                             f"reading — fix the patch table, do not read the number.")
        print()

    rows = compare(a.ours, a.target)
    print(f"{'patch':28s} {'ours(lin)':22s} {'target(lin)':22s} ratio  hue_err")
    for r in rows:
        o = "(" + ",".join(f"{c:.3f}" for c in r["ours"]) + ")"
        t = "(" + ",".join(f"{c:.3f}" for c in r["target"]) + ")"
        print(f"{r['patch']:28s} {o:22s} {t:22s} {r['value_ratio']:5.2f}  {r['hue_err']:.3f}")
    ratios = [r["value_ratio"] for r in rows]
    spread = max(ratios) / max(min(ratios), 1e-6)
    print(f"\nvalue-ratio spread across the palette = {spread:.2f}x  "
          f"(1.0 = every material sits the same distance from the target; a "
          f"large spread means one surface is wrong RELATIVE to the rest, which "
          f"is the part the light round cannot fix)")
    print(f"worst hue error = {max(r['hue_err'] for r in rows):.3f}")
    if a.json:
        json.dump({"rows": rows, "spread": round(spread, 3)},
                  open(a.json, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
