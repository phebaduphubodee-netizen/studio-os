"""STUDY-D12 (2026-09-02) curtain study — the reproduction recipe for every number in
knowledge/_inbox/model-study/2026-09-02-curtains.md. Pure Python, no bpy: reads the
probe dumps in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-curtains.json.
A verifier reruns this and diffs; a number that is not in the output did not come from a dump.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D12-curtains): what does a pro
curtain's TRACK consist of, as objects and dimensions, and how does the curtain FINISH at
the top? Our own frame answers both with a coordinate: `curtains.py` TOP_EMBED_M pokes the
fabric 30 mm into the ceiling slab and models no hardware at all, and `casement_sheers.py`
ROD_OFFSET_MM is a hanging PLANE, not a rod. So the measurements below are chosen to be
the ones that can convict or acquit that: is there a hardware object, how big is it, and
where does the fabric sit relative to it.

Definitions (all mm, world space, from each object's `world_bbox_mm`):
  drop          = fabric top z - fabric bottom z
  hem           = fabric min z - lowest mesh z of the set (0 = the fabric reaches the floor)
  head_over_rod = fabric top z - hardware top z   (>0 fabric rises past the rod: tab/rings
                  over the pole; <0 it hangs below the rod's crown)
  rod_drop      = set top z - hardware bottom z   (how much of the assembly's height the
                  hardware occupies)
  rod_overhang  = (hardware x-span - total fabric x-span) / 2, per side
  fullness      = area_m2 / (drop * x-span)  — cloth area over the flat rectangle the
                  opening needs. A flat sheet is 1.0; gathered curtains are more. This is
                  the number `casement_sheers.FULLNESS = 1.8` is trying to be, and it is
                  the RIGHT fold metric for a hanging sheet.
  edge_proxy_mm : study_probe_read (area per quad-equivalent face)

SURPLUS IS RECORDED BUT IS THE WRONG INSTRUMENT FOR THIS CLASS, and the note must not use
it as it used it for beds. `surplus` = area / plan-bbox measures fold richness for cloth
lying HORIZONTALLY (a duvet on a bed, plan bbox ~ the bed). A curtain hangs VERTICALLY, so
its plan bbox is the footprint of a plane on edge (1472 x 78 mm) and the ratio measures
slenderness, not gather — which is why these read 12-405 where a duvet reads 1.3-3.5. Same
family as the 2026-08-30 lesson about an instrument blind to the axis it was not built for.

Hardware vs fabric is assigned BY HAND in SETS below — that assignment is the one judgement
in this file, and every object of every set is printed so a reader can dispute it against
the dump's own object list. A set with hardware=None is a POSITIVE CLAIM that the vendor
shipped no hardware object, not an omission.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import (REPO, edge_proxy_mm, find, img_sizes, load,  # noqa: E402
                              mat_row, meshes, mods, surplus)

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-curtains.json")

# prefix -> (label, type, hardware selectors, fabric selectors or None for "the rest")
#
# A SELECTOR is a name, or {"name": ..., "zmin": ..., "exact": True} when a vendor gives every object
# in the set the SAME name (dc081fef does) and only geometry can tell them apart. A
# selector may match several objects; that is not an error, it is a pair of rod segments
# or a row of rails. `hardware: []` is a POSITIVE CLAIM that the vendor shipped no
# hardware object — it is checked by hand against the printed all_mesh_names, not assumed.
SETS = {
    "b72cedda": ("Curtains on rod", "drape+sheer", ["rod"],
                 ["CURTAIN_right", "CURTAIN_left", "SHEER"]),
    "06fd1db1": ("Simple curtains with rod (free)", "drape", ["Rod"], ["Curtain"]),
    "16d7a3a5": ("Light linen curtains", "drape", ["rod"],
                 ["curtainleft", "curtain_right_2"]),
    # every object is named "Tulle Curtain w Decorative Edging"; the two 1177x30x30
    # segments at z 2934-2964 are the pole, and nothing but geometry says so
    "dc081fef": ("Tulle Curtain w Decorative Edging", "sheer+valance",
                 [{"name": "Tulle Curtain", "zmin": 2934}], None),
    # 3 fabric objects, materials {curtain, sheer} only — no hardware shipped
    "e30d9431": ("Curtains with sheer", "drape+sheer", [], None),
    # 5 fabric objects; the 851x15x2975 one at 1.3 M verts is the WOODEN STRING itself
    # (material Wood), i.e. fabric-class in this study, not a rail
    "caddb0d4": ("Silk and Wooden String Curtain", "drape+string", [], None),
    # 4 blinds, each carrying a `metal` material slot INSIDE its own mesh: the headrail
    # exists but is not a separate object. hardware [] is true at OBJECT level and the
    # note must say the rest.
    "ee15c366": ("Roman Curtain", "roman", [], None),
    # not one blind but FIVE, staged at different drops (rails at z 143/144/497/888/1376).
    # rails = the 1789x127x31 bars; fittings = the 5-54 mm cord/ladder parts. The fifth rail
    # is named the bare "Wooden Blinds Set", which is a PREFIX of all 39 objects, so only an
    # exact-match selector reaches it — a prefix selector silently dropped it (2026-09-02
    # verifier finding, and the reason `exact` exists).
    "89167e7c": ("Wooden Blinds Set (x5)", "venetian",
                 [{"name": "Wooden Blinds Set", "exact": True},
                  "Wooden Blinds Set 015", "Wooden Blinds Set 034",
                  "Wooden Blinds Set 038", "Wooden Blinds Set 36",
                  "Wooden Blinds Set 01", "Wooden Blinds Set 02",
                  "Wooden Blinds Set 03", "Wooden Blinds Set 04",
                  "Wooden Blinds Set 05", "Wooden Blinds Set 06",
                  "Wooden Blinds Set 07", "Wooden Blinds Set 016"], None),
}
# what our own frame does, for the delta table
OURS_CODE = {
    "curtains.py TOP_EMBED_M": 0.03,
    "curtains.py HEM_CLEAR_M": 0.015,
    "casement_sheers.py ROD_OFFSET_MM": 50.0,
    "casement_sheers.py HEM_ABOVE_SILL_MM": 15.0,
    "casement_sheers.py FULLNESS": 1.8,
}


def pick(d, sel):
    """All MESH objects matching a selector. A str is a name (exact, else unique prefix
    via study_probe_read.find); a dict adds geometry terms because some vendors name
    every object in the set identically. Zero matches RAISES — a selector that selects
    nothing would silently shrink a class."""
    if isinstance(sel, str):
        return [find(d, sel)]
    got = [o for o in meshes(d)
           if (o["name"] == sel["name"] if sel.get("exact") else o["name"].startswith(sel["name"]))
           and ("zmin" not in sel or abs(o["world_bbox_mm"]["min"][2] - sel["zmin"]) <= 1.0)]
    if not got:
        raise KeyError(("selector matched nothing", sel))
    return got


def _row(d, o):
    bb = o["world_bbox_mm"]
    m = o["mesh"]
    return {"name": o["name"], "dims": [round(x) for x in o["dims_mm"]],
            "z": [round(bb["min"][2]), round(bb["max"][2])],
            "x": [round(bb["min"][0]), round(bb["max"][0])],
            "verts": m["verts"], "polys": m["polys"], "quads": m["quads"], "tris": m["tris"],
            "area_m2": round(m["area_m2"], 3), "v_per_m2": round(m["verts_per_m2"]),
            "surplus_NOT_FOR_HANGING": round(surplus(o), 2),
            "edge_proxy_mm": round(edge_proxy_mm(o), 1),
            "mods": mods(o), "mats": {mn: mat_row(d, mn) for mn in o["materials"]}}


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0], "_ours_code": OURS_CODE, "sets": {}}
    for pre, (label, kind, hardware, fabric) in SETS.items():
        fn, d = load(pre)
        ms = meshes(d)
        zmin = min(o["world_bbox_mm"]["min"][2] for o in ms)
        ztop = max(o["world_bbox_mm"]["max"][2] for o in ms)
        hw = [o for sel in (hardware or []) for o in pick(d, sel)]
        fab = ([o for sel in fabric for o in pick(d, sel)] if fabric
               else [o for o in ms if o not in hw])
        row = {"file": fn, "label": label, "kind": kind, "source": d["source"],
               "n_objects": len(d["objects"]), "n_mesh": len(ms),
               "n_images": len(d.get("images", [])), "image_sizes": img_sizes(d),
               "set_z": [round(zmin), round(ztop)],
               "hardware_objects": len(hw),
               "hardware": [], "fabric": [],
               "all_mesh_names": sorted(o["name"] for o in ms)}
        for o in hw:
            r = _row(d, o)
            r["rod_drop_from_set_top"] = round(ztop - o["world_bbox_mm"]["min"][2])
            row["hardware"].append(r)
        for o in fab:
            bb = o["world_bbox_mm"]
            r = _row(d, o)
            drop = bb["max"][2] - bb["min"][2]
            span = bb["max"][0] - bb["min"][0]
            r["drop"] = round(drop)
            r["x_span"] = round(span)
            r["fullness"] = (round(o["mesh"]["area_m2"] / (drop * span * 1e-6), 2)
                             if drop > 0 and span > 0 else None)
            r["hem_above_floor"] = round(bb["min"][2] - zmin)
            if hw:
                r["head_over_rod"] = round(bb["max"][2] - max(
                    h["world_bbox_mm"]["max"][2] for h in hw))
            row["fabric"].append(r)
        if hw and fab:
            fx0 = min(o["world_bbox_mm"]["min"][0] for o in fab)
            fx1 = max(o["world_bbox_mm"]["max"][0] for o in fab)
            hx0 = min(o["world_bbox_mm"]["min"][0] for o in hw)
            hx1 = max(o["world_bbox_mm"]["max"][0] for o in hw)
            row["fabric_x_span"] = round(fx1 - fx0)
            row["hardware_x_span"] = round(hx1 - hx0)
            row["rod_overhang_per_side"] = round(((hx1 - hx0) - (fx1 - fx0)) / 2.0)
        out["sets"][pre] = row

    # OUR OWN SIDE, from the same kind of dump, so every delta the note states is
    # reproducible rather than read off the source by hand. Note the p2r91 scene dump
    # carries no world_bbox_mm (it predates that field), so ours is dims/area only —
    # which is why no head_over_rod or hem is claimed for our curtains anywhere.
    _, do = load("_ours_p2r91")
    ours = {}
    for o in meshes(do):
        n = o["name"].lower()
        if not any(k in n for k in ("curtain", "sheer", "drape")):
            continue
        m = o["mesh"]
        drop = o["dims_mm"][2]
        span = max(o["dims_mm"][0], o["dims_mm"][1])
        ours[o["name"]] = {
            "dims": [round(x) for x in o["dims_mm"]], "verts": m["verts"],
            "area_m2": round(m["area_m2"], 2), "v_per_m2": round(m["verts_per_m2"]),
            "fullness": round(m["area_m2"] / (drop * span * 1e-6), 2) if drop and span else None,
            "edge_proxy_mm": round(edge_proxy_mm(o), 1), "mods": mods(o),
            "mats": {mn: mat_row(do, mn) for mn in o["materials"]}}
    out["ours"] = ours
    # DERIVED, not typed: a hardware object in our scene would have to be named for what it
    # is, and nothing in the naming vocabulary matches. Typing a 0 here would be the note
    # crediting the dump with a number the script never looked for.
    _hw_words = ("rod", "track", "rail", "ring", "pole", "pelmet", "bracket", "finial", "grommet")
    _cloth_words = ("curtain", "sheer", "drape")
    _hw_any = [o["name"] for o in meshes(do)
               if any(w in o["name"].lower() for w in _hw_words)]
    _hw_curtain = [n for n in _hw_any if any(w in n.lower() for w in _cloth_words)]
    out["ours_hardware_objects"] = len(_hw_curtain)
    out["ours_hardware_scan"] = {
        "words": list(_hw_words), "meshes_scanned": len(meshes(do)),
        "matched_anywhere_in_scene": len(_hw_any),
        "of_those_named_for_a_curtain": len(_hw_curtain),
        # the scene DOES carry a pelmet — a lighting cove on element 5, an 8-vert box —
        # and no curtain object references it. Worth printing rather than collapsing to
        # a bare 0, because "we have no pelmet" would be false and "we have one" would
        # be misleading.
        "non_curtain_matches": sorted(set(_hw_any))[:40]}

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    for pre, r in out["sets"].items():
        print(f"\n== {pre} {r['label']} [{r['kind']}] objs={r['n_objects']} mesh={r['n_mesh']} "
              f"imgs={r['n_images']} set_z={r['set_z']} hardware_objs={r['hardware_objects']}")
        for h in r["hardware"]:
            print(f"  HW {h['name'][:26]:26s} {h['dims']} z={h['z']} v={h['verts']} "
                  f"edge~{h['edge_proxy_mm']} rod_drop={h['rod_drop_from_set_top']} mats={list(h['mats'])}")
        for f in r["fabric"]:
            hor = f.get("head_over_rod")
            print(f"  FB {f['name'][:26]:26s} {f['dims']} drop={f['drop']} hem={f['hem_above_floor']}"
                  f"{'' if hor is None else f' head_over_rod={hor:+d}'} v={f['verts']} "
                  f"fullness={f['fullness']} edge~{f['edge_proxy_mm']} mods={f['mods']}")
        if "rod_overhang_per_side" in r:
            print(f"  >> fabric span {r['fabric_x_span']} · hardware span {r['hardware_x_span']} "
                  f"· overhang/side {r['rod_overhang_per_side']}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
