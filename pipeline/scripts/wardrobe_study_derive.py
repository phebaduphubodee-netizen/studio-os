"""STUDY-D16 (2026-09-02) wardrobe-internals study — the reproduction recipe for every
number in knowledge/_inbox/model-study/2026-09-02-wardrobe.md. Pure Python, no bpy: reads the
probe dumps in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-wardrobe.json.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D16-wardrobe): the cell-filling grammar
— COUNT, POSE and EMPTINESS — as numbers taken from the real loc/rot of loaded assets, for the
lane's contents round to use.

  POSE      rot_deg per object, censused. A set is called AXIS-ALIGNED when every content
            object shares one rotation triple. Where a set does not, its most common triple is
            treated as the set's BASE (an import-axis convention: 90 deg about X is the Z-up /
            Y-up swap, not a styling choice) and each object's RESIDUAL is reported against it,
            because the residual is the part a builder would have to reproduce deliberately.
  LEVEL     content objects clustered by world z. Two objects are on the same level when their
            bbox z-ranges overlap at all; the cluster's span is the level. Levels are what a
            shelf grammar is written in, and the dump has no shelf objects labelled as such.
  FILL      per level: the union of the objects' extents ALONG THE ASSET'S WIDTH AXIS, divided
            by the asset's extent on that axis. The width axis is the LONGER of the two plan
            axes, chosen per asset — b19781fd is a run along world Y, and measuring it on x
            silently reported DEPTH occupancy (0.79/0.70/0.75) where the width figures are
            0.21/0.22/0.20. 1.00 is a level packed edge to edge. Says nothing about headroom.
  HEADROOM  gap from the top of a level to the bottom of the level above it, in mm.

WHAT COUNTS AS CONTENT, and it is the one judgement here: an object is CONTENT unless it is
either (a) large by bbox volume (>= STRUCT_VOL_FRAC of the asset), or (b) FULL-HEIGHT — its z
extent covers >= FULL_HEIGHT_FRAC of the asset. Rule (b) exists because a back panel and a
side sheet are thin enough to pass (a) at 1.0% and 3.8% of volume, and on 748845d0 those two
sheets bridged every shelf into ONE level. The note first blamed that on "the cells overlap in
z", which was the wrong mechanism: with the sheets removed the cells are 44-370, 482-2149 and
2230-2525 — plainly disjoint. Every object's classification is written out so it can be disputed.

Readers and edge_proxy_mm come from study_probe_read — same definitions as the bed, curtain,
rug and seating studies.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import REPO, load, meshes  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-wardrobe.json")

# an object whose bbox volume exceeds this fraction of the asset's own bbox volume is
# structure (carcass / door / back), not content.
STRUCT_VOL_FRAC = 0.06
FULL_HEIGHT_FRAC = 0.80

SETS = {
    "3e38f13d": ("Polo Closet", "full_plan", "the richest staged closet: 2.32 M faces"),
    "885a71e4": ("WallCloset-Mens Classic", "full_plan", "hanging + folded in one case"),
    "748845d0": ("Large Wardrobe", "full_plan",
                 "a 5.66 m fitted RUN — and the asset whose 810 mm carcass my own new "
                 "MIN_DEPTH_RATIO refused at 0.1431 before the ratio was declared None"),
    "b19781fd": ("Closet and coffee", "full_plan", "a closet staged with non-clothing props"),
}
OURS_PREFIX = "mill__style_foldacq"


def _vol(o):
    d = o["dims_mm"]
    return d[0] * d[1] * d[2]


def _levels(objs):
    """cluster by overlapping world-z ranges; returns [{z, objects}] bottom-up."""
    items = sorted(objs, key=lambda o: o["world_bbox_mm"]["min"][2])
    out = []
    for o in items:
        lo, hi = o["world_bbox_mm"]["min"][2], o["world_bbox_mm"]["max"][2]
        if out and lo <= out[-1]["z"][1]:
            out[-1]["z"][1] = max(out[-1]["z"][1], hi)
            out[-1]["objects"].append(o)
        else:
            out.append({"z": [lo, hi], "objects": [o]})
    return out


def _union_len(spans):
    spans = sorted(spans)
    tot, cur_lo, cur_hi = 0.0, None, None
    for lo, hi in spans:
        if cur_hi is None or lo > cur_hi:
            if cur_hi is not None:
                tot += cur_hi - cur_lo
            cur_lo, cur_hi = lo, hi
        else:
            cur_hi = max(cur_hi, hi)
    if cur_hi is not None:
        tot += cur_hi - cur_lo
    return tot


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0],
           "_struct_vol_frac": STRUCT_VOL_FRAC, "sets": {}}
    for pre, (label, tier, why) in SETS.items():
        fn, d = load(pre)
        ms = [o for o in meshes(d) if "world_bbox_mm" in o]
        if not ms:
            continue
        ax = [min(o["world_bbox_mm"]["min"][i] for o in ms) for i in range(3)]
        bx = [max(o["world_bbox_mm"]["max"][i] for o in ms) for i in range(3)]
        asset_vol = max((bx[0] - ax[0]) * (bx[1] - ax[1]) * (bx[2] - ax[2]), 1e-9)
        # the width axis is the longer plan axis of the asset itself
        wi = 0 if (bx[0] - ax[0]) >= (bx[1] - ax[1]) else 1
        asset_w = max(bx[wi] - ax[wi], 1e-9)

        asset_h = max(bx[2] - ax[2], 1e-9)
        content, structure = [], []
        for o in ms:
            zspan = o["world_bbox_mm"]["max"][2] - o["world_bbox_mm"]["min"][2]
            big = _vol(o) / asset_vol >= STRUCT_VOL_FRAC
            tall = zspan / asset_h >= FULL_HEIGHT_FRAC
            (structure if (big or tall) else content).append(o)

        rots = Counter(tuple(round(x) for x in o.get("rot_deg", [0, 0, 0])) for o in content)
        base = rots.most_common(1)[0][0] if rots else (0, 0, 0)
        residuals = Counter()
        for o in content:
            r = tuple(round(x) for x in o.get("rot_deg", [0, 0, 0]))
            residuals[tuple(((a - b + 180) % 360) - 180 for a, b in zip(r, base))] += 1

        # the taxonomy the note used to assert: how far is each residual from the nearest
        # multiple of 90 on its worst axis? on_axis <= 1, tilt <= 5, else MID-ANGLE.
        pose = {"on_axis": 0, "tilt_le_5": 0, "mid_angle": 0}
        mids = []
        for o in content:
            r = tuple(round(x) for x in o.get("rot_deg", [0, 0, 0]))
            res = tuple(((a - b + 180) % 360) - 180 for a, b in zip(r, base))
            off = max(min(abs(v % 90), 90 - abs(v % 90)) for v in res)
            if off <= 1:
                pose["on_axis"] += 1
            elif off <= 5:
                pose["tilt_le_5"] += 1
            else:
                pose["mid_angle"] += 1
                mids.append([o["name"], list(res), round(off)])

        levels = []
        lv = _levels(content)
        for i, L in enumerate(lv):
            spans = [(o["world_bbox_mm"]["min"][wi], o["world_bbox_mm"]["max"][wi])
                     for o in L["objects"]]
            head = round(lv[i + 1]["z"][0] - L["z"][1]) if i + 1 < len(lv) else None
            levels.append({"z": [round(L["z"][0]), round(L["z"][1])],
                           "span_mm": round(L["z"][1] - L["z"][0]),
                           "n_objects": len(L["objects"]),
                           "fill": round(_union_len(spans) / asset_w, 2),
                           "headroom_to_next_mm": head,
                           "names": sorted(o["name"] for o in L["objects"])[:8]})

        out["sets"][pre] = {
            "file": fn, "label": label, "tier": tier, "why_in_corpus": why,
            "n_objects": len(d["objects"]), "n_mesh": len(ms),
            "n_materials": len(d["materials"]), "n_images": len(d.get("images", [])),
            "asset_bbox_mm": [round(bx[i] - ax[i]) for i in range(3)],
            "width_axis": "xy"[wi],
            "n_structure": len(structure), "n_content": len(content),
            "structure_names": sorted(o["name"] for o in structure),
            "rot_census": [[list(k), v] for k, v in rots.most_common()],
            "rot_base": list(base),
            "residual_census": [[list(k), v] for k, v in residuals.most_common()],
            "axis_aligned": len(rots) == 1,
            "pose_taxonomy": pose,
            "mid_angle_examples": sorted(mids, key=lambda m: -m[2])[:6],
            "rot_base_is_a_tie": (len(rots) > 1
                                  and rots.most_common()[0][1]
                                  == rots.most_common()[1][1]),
            "n_levels": len(levels), "levels": levels,
        }

    _, do = load("_ours_p2r91")
    ours = [o for o in meshes(do) if o["name"].startswith(OURS_PREFIX)]
    orot = Counter(tuple(round(x) for x in o.get("rot_deg", [0, 0, 0])) for o in ours)
    out["ours"] = {"prefix": OURS_PREFIX, "n": len(ours),
                   "rot_census": [[list(k), v] for k, v in orot.most_common()],
                   "axis_aligned": len(orot) == 1,
                   "verts_each": sorted({o["mesh"]["verts"] for o in ours}),
                   "dims_each": sorted({tuple(round(x) for x in o["dims_mm"]) for o in ours}),
                   "note": ("the p2r91 scene dump carries no world_bbox_mm, so levels and fill "
                            "cannot be computed for ours from this dump — only pose and size")}

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    for pre, s in out["sets"].items():
        print(f"\n== {pre} {s['label']} [{s['tier']}] bbox={s['asset_bbox_mm']} "
              f"mesh={s['n_mesh']} structure={s['n_structure']} content={s['n_content']}")
        print(f"   AXIS-ALIGNED={s['axis_aligned']} base={s['rot_base']}"
              f"{' (TIE — base picked by insertion order)' if s['rot_base_is_a_tie'] else ''} "
              f"pose={s['pose_taxonomy']}")
        if not s["axis_aligned"]:
            print(f"   residuals off base: {s['residual_census'][:5]}")
        print(f"   levels={s['n_levels']}")
        for L in s["levels"]:
            print(f"     z={L['z']} span={L['span_mm']:>4} n={L['n_objects']:>3} "
                  f"fill={L['fill']:.2f} headroom={L['headroom_to_next_mm']}")
    o = out["ours"]
    print(f"\nOURS {o['prefix']}* n={o['n']} axis_aligned={o['axis_aligned']} "
          f"rot={o['rot_census']} verts={o['verts_each']} dims={o['dims_each']}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
