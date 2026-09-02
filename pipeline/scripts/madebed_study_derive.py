"""STUDY-D11 (2026-09-02) made-bed study — the reproduction recipe for every number in
knowledge/_inbox/model-study/2026-09-02-madebed.md. Pure Python, no bpy: reads the probe
dumps in assets/shared/blenderkit/_study/*.probe.json (written by model_study_probe.py)
and writes qa/blenderkit-study-madebed.json. A verifier reruns this and diffs; a number
that is not in the output did not come from a dump.

Definitions (all mm, world space, from each object's `world_bbox_mm`):
  loft = layer top z - mattress top z            (how proud the cloth stands of the sleeping plane)
  hem  = layer min z - lowest mesh z of the set  (0 = the cloth reaches the floor; "the floor" is
                                                  the set's own lowest mesh, which can sit below z=0)
  pillow top / bottom = pillow bbox z - mattress top z
  edge_proxy = sqrt(area_m2 / (quads + tris/2 + ngons)) * 1000
  surplus = area_m2 / (dims_x * dims_y)          (drape surplus vs plan bbox; a closed flat slab ~2.0)

EDGE_PROXY IS NOT `bedcloth_fit.edge_mm`, AND THE TWO MUST NEVER BE COMPARED AS ONE NUMBER.
`bedcloth_fit.edge_mm` is the TRUE median edge length, read off the mesh's edge list in world
space (bedcloth_fit.py:45) — it is what `bedcloth_rules.fineness` consumes and what produced the
4.5 / 10.3 / 43.2 mm figures in that rule's docstring. A probe dump carries no edge list at all
(mesh keys: verts, polys, quads, tris, ngons, area_m2, ...), so offline the closest available
quantity is the area-per-face square root above. On a regular quad grid the two nearly agree; on
elongated or irregular faces they diverge, and the divergence is unmeasured here. Any ratio taken
between a `fineness` number and an `edge_proxy` number is instrument-mixed and approximate.

SURPLUS ASSUMES THE OBJECT IS AXIS-ALIGNED IN PLAN: dims_mm x/y are the object's own bbox axes, so
a set authored on rotated axes (bk_phoenix) yields a denominator that is not the plan footprint and
a surplus that is an artifact — bk_phoenix 'sheet 02' reads 9.36 for this reason and is excluded
from every statistic in the note.

Object roles (mattress / cloth layers / pillows) are assigned BY HAND per set in SETS —
that assignment is the one judgement in this file, and it is printed so a reader can
dispute it against the dump's own object list. Two assignments WERE disputed and lost
(2026-09-02 opposing verifiers); the rows stay so their numbers keep reproducing, and
ROLE_DISPUTES carries what the reader must know before using them. It is written into
the output so the note and the artifact cannot drift apart.
"""
import glob, json, math, os, sys
sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDY = os.path.join(REPO, "assets", "shared", "blenderkit", "_study")
OUT = os.path.join(REPO, "qa", "blenderkit-study-madebed.json")

# asset prefix -> (label, mattress object name, cloth-layer object names, pillow object names)
SETS = {
    "ee42aa0e": ("Cozy bed", "Mattress", ["Base.001", "Bed.003", "Bed.002", "Bed.001", "Bed"], ["Bed.004", "Bed.005", "Bed.006", "Bed.007", "Bed.008", "Bed.009"]),
    "62253e5c": ("Wyller Bed", "mattres", ["blanket", "bed shawl"], ["PillowIvory Left", "PillowIvory Right", "Fur Pillow", "Francesca Hand Embroidered Throw Pillow Left", "Francesca Hand Embroidered Throw Pillow Middle", "Francesca Hand Embroidered Throw Pillow Right"]),
    "afcfd29e": ("Dream Bed", "Mattress", ["Mattress_cover", "Bed_main_cover", "Secondary_cover"], ["Main_pillows", "Support_pillows", "Decoration_pillows"]),
    "1f83314d": ("Messy bed (unmade control)", "Cube", ["BED EXPORT.004", "BED EXPORT.003", "BED EXPORT.005"], ["BED EXPORT.001", "BED EXPORT.002"]),
    "ba112721": ("Rattan headboard bed", "Bed-Sheet", ["Bed-Cover-Bottom", "Bed-Cover-Top"], ["Bed-Pillow", "Bed-Pillow.001", "Bed-Pillow.002", "Bed-Pillow.003"]),
    "a682383b": ("Ikea double bed", "Mattress", ["blanket"], ["Pillow"]),
    "e2418055": ("Metropol — IN FRAME (D-121)", "Matress", ["Blanket", "Sheet"], ["Cusions"]),
    "81d895fd": ("previous frame (D-109/110)", "Cube.015", ["Plane.029", "Plane.030", "Plane.038"], ["Plane.031", "Plane.032", "Plane.033", "Plane.035"]),
    "bk_daxing": ("Keywest Daxing", "sheet", ["sheet 02", "blanquet"], ["cuishon 1", "chuishion 2"]),
    "bk_phoenix": ("Keywest Phoenix", "sheet", ["sheet 02", "blanquet"], ["cuishon 1", "chuishion 2"]),
    "bk_stansted": ("Keywest Stansted", "sheet", ["sheet 02", "blanquet"], ["cuishon 1", "chuishion 2"]),
}
PILLOW_SETS = {"45daf5df": "Pillow Set A", "2767f3fa": "Cylinder pillow (bolster)"}

# hand assignments that opposing verifiers overturned on 2026-09-02. The rows above are
# UNCHANGED (their loft/hem still reproduce, and the mattress top plane is the same
# surface either way) — what changes is which claims may be built on them.
ROLE_DISPUTES = {
    "afcfd29e/Mattress": "The object named 'Mattress' (1857x830) is only the strip of the "
        "sleeping surface left exposed by the covers; the bed itself is a double whose deck "
        "is 'Bed_Base' 2069x2270. TOP Z, and therefore every loft and hem, is unaffected. "
        "Its dims_mm must NOT be used as a mattress size, and this set is excluded from any "
        "coverage-of-length or overhang-per-side statistic.",
    "ee42aa0e/Bed.008+Bed.009": "Listed as pillows; they sit in the gap behind the mattress "
        "head (bottom 253 mm BELOW the mattress top, Velvet, not the pillow fabric) and are "
        "headboard cushions, not pillows on the bed. Excluded from every pillow range.",
}
OURS = ["bed__cloth__acq0", "bed__headset0__acq1", "bed__frame__acq1", "bed__frame__acq0", "bed__base__acq0",
        "bed__headboard", "bed__head_shim", "deco_bedthrow__acq0", "Sheet"]


def load(prefix):
    fs = glob.glob(os.path.join(STUDY, prefix + "*.probe.json"))
    assert len(fs) == 1, (prefix, fs)
    return os.path.basename(fs[0]), json.load(open(fs[0], encoding="utf-8"))


def find(d, name):
    for o in d["objects"]:
        if o["name"] == name and o["type"] == "MESH":
            return o
    hits = [o for o in d["objects"] if o["type"] == "MESH" and o["name"].startswith(name)]
    if len(hits) == 1:      # Keywest sets suffix the same mesh names differently (.001 etc.)
        return hits[0]
    raise KeyError((name, [h["name"] for h in hits]))


def edge_proxy_mm(o):
    """Square root of area per QUAD-EQUIVALENT face, in mm. See the module docstring:
    this is not the repo's `bedcloth_fit.edge_mm` (true median edge) and cannot be —
    a probe dump carries no edge list. Two tris make one quad-equivalent, so a mesh
    that is half quads and half tris is scored on the same footing as either."""
    m = o["mesh"]
    faces = m["quads"] + m["tris"] / 2.0 + m.get("ngons", 0)
    if not faces:                          # a dump that lost its face counts
        faces = m["polys"]
    return math.sqrt(m["area_m2"] / faces) * 1000.0 if faces else float("nan")


def mat_row(d, name):
    for mt in d["materials"]:
        if mt["name"] == name:
            p = mt.get("principled") or {}
            return {"sheen": p.get("Sheen Weight"), "rough": p.get("Roughness"),
                    "base": str(p.get("Base Color"))[:40], "normal": str(p.get("Normal"))[:40],
                    "principled": "BSDF_PRINCIPLED" in (mt.get("node_hist") or {})}
    return None


def _img_sizes(d):
    """Packed-image size census for a set, as [[w, h, count], ...] largest area first.
    The note's per-asset table quotes these; without them here the annotation is
    hand-read prose that nothing regenerates, which is how two verifier rounds each
    found a wrong image band in that column."""
    hist = {}
    for i in d.get("images", []):
        k = tuple(i["size"])
        hist[k] = hist.get(k, 0) + 1
    return [[w, h, n] for (w, h), n in sorted(hist.items(), key=lambda kv: -kv[0][0] * kv[0][1])]


def _mods(o):
    return [x["type"] + (f"({x.get('levels')},{x.get('render_levels')})" if x["type"] == "SUBSURF" else "")
            for x in o.get("modifiers", [])]


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0], "_role_disputes": ROLE_DISPUTES,
           "sets": {}, "pillow_sets": {}}
    for pre, (label, matt, layers, pillows) in SETS.items():
        fn, d = load(pre)
        zmin_all = min(o["world_bbox_mm"]["min"][2] for o in d["objects"] if o["type"] == "MESH")
        mo = find(d, matt)
        mtop = mo["world_bbox_mm"]["max"][2]; mbot = mo["world_bbox_mm"]["min"][2]
        row = {"file": fn, "label": label, "source": d["source"], "bed_min_z": round(zmin_all, 1),
               "n_images": len(d.get("images", [])),
               "image_sizes": _img_sizes(d),
               "mattress": {"name": matt, "dims": [round(x) for x in mo["dims_mm"]], "z": [round(mbot), round(mtop)],
                            "thick": round(mtop - mbot), "verts": mo["mesh"]["verts"], "mods": _mods(mo)},
               "layers": [], "pillows": []}
        for n in layers:
            o = find(d, n); bb = o["world_bbox_mm"]; m = o["mesh"]
            row["layers"].append({"name": n, "dims": [round(x) for x in o["dims_mm"]],
                "z": [round(bb["min"][2]), round(bb["max"][2])],
                "loft_over_mattress_top": round(bb["max"][2] - mtop),
                "hem_above_floor": round(bb["min"][2] - zmin_all),
                "verts": m["verts"], "polys": m["polys"], "quads": m["quads"], "tris": m["tris"],
                "area_m2": round(m["area_m2"], 3), "v_per_m2": round(m["verts_per_m2"]),
                "surplus": round(m["area_m2"] / (o["dims_mm"][0] * o["dims_mm"][1] * 1e-6), 2),
                "edge_proxy_mm": round(edge_proxy_mm(o), 1), "mods": _mods(o),
                "mats": {mn: mat_row(d, mn) for mn in o["materials"]}})
        for n in pillows:
            o = find(d, n); bb = o["world_bbox_mm"]; m = o["mesh"]
            row["pillows"].append({"name": n, "dims": [round(x) for x in o["dims_mm"]],
                "z": [round(bb["min"][2]), round(bb["max"][2])],
                "top_over_mattress_top": round(bb["max"][2] - mtop),
                "bottom_over_mattress_top": round(bb["min"][2] - mtop),
                "verts": m["verts"], "v_per_m2": round(m["verts_per_m2"]), "edge_proxy_mm": round(edge_proxy_mm(o), 1),
                "mods": _mods(o), "mats": {mn: mat_row(d, mn) for mn in o["materials"]}})
        out["sets"][pre] = row

    for pre, label in PILLOW_SETS.items():
        fn, d = load(pre)
        row = {"file": fn, "label": label, "objects": []}
        for o in d["objects"]:
            if o["type"] != "MESH":
                continue
            m = o["mesh"]
            row["objects"].append({"name": o["name"], "dims": [round(x) for x in o["dims_mm"]], "verts": m["verts"],
                "polys": m["polys"], "quads": m["quads"], "tris": m["tris"], "v_per_m2": round(m["verts_per_m2"]),
                "edge_proxy_mm": round(edge_proxy_mm(o), 1), "mods": _mods(o),
                "mats": {mn: mat_row(d, mn) for mn in o["materials"]}})
        row["images"] = [(i["name"], i["size"]) for i in d["images"]]
        out["pillow_sets"][pre] = row

    fo = os.path.join(STUDY, "_ours_p2r91.probe.json")
    do = json.load(open(fo, encoding="utf-8"))
    ours = {}
    for n in OURS:
        o = find(do, n); m = o["mesh"]
        ours[n] = {"dims": [round(x) for x in o["dims_mm"]], "loc_z": round(o["loc_mm"][2]), "verts": m["verts"],
                   "polys": m["polys"], "quads": m["quads"], "tris": m["tris"], "area_m2": round(m["area_m2"], 3),
                   "v_per_m2": round(m["verts_per_m2"]), "edge_proxy_mm": round(edge_proxy_mm(o), 1), "mods": _mods(o),
                   "mats": {mn: mat_row(do, mn) for mn in o["materials"]}}
    out["ours"] = ours

    census = []
    for pre, row in out["sets"].items():
        for L in row["layers"] + row["pillows"]:
            for mn, mr in L["mats"].items():
                census.append((pre, L["name"], mn, mr and mr["sheen"], mr and mr["rough"], mr and mr["principled"]))
    for pre, row in out["pillow_sets"].items():
        for L in row["objects"]:
            for mn, mr in L["mats"].items():
                census.append((pre, L["name"], mn, mr and mr["sheen"], mr and mr["rough"], mr and mr["principled"]))
    out["sheen_census"] = census

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    for pre, row in out["sets"].items():
        print(f"\n== {pre} {row['label']} [{row['source']}] bed_min_z={row['bed_min_z']} imgs={row['n_images']} mattress {row['mattress']}")
        for L in row["layers"]:
            print(f"  L {L['name'][:22]:22s} dims={L['dims']} z={L['z']} loft={L['loft_over_mattress_top']:+d} hem={L['hem_above_floor']} v={L['verts']} q/t={L['quads']}/{L['tris']} area={L['area_m2']} surplus={L['surplus']} v/m2={L['v_per_m2']} edge~{L['edge_proxy_mm']} mods={L['mods']} mats={ {k:(v['sheen'],v['rough']) if v else None for k,v in L['mats'].items()} }")
        for P in row["pillows"]:
            print(f"  P {P['name'][:22]:22s} dims={P['dims']} z={P['z']} top+{P['top_over_mattress_top']} bot{P['bottom_over_mattress_top']:+d} v={P['verts']} v/m2={P['v_per_m2']} edge~{P['edge_proxy_mm']} mats={ {k:(v['sheen'],v['rough']) if v else None for k,v in P['mats'].items()} }")
    for pre, row in out["pillow_sets"].items():
        print(f"\n== {pre} {row['label']} imgs={row['images']}")
        for o in row["objects"]:
            print(f"  {o['name'][:22]:22s} dims={o['dims']} v={o['verts']} q/t={o['quads']}/{o['tris']} v/m2={o['v_per_m2']} edge~{o['edge_proxy_mm']} mods={o['mods']} mats={ {k:(v['sheen'],v['rough']) if v else None for k,v in o['mats'].items()} }")
    print("\n== OURS p2r91")
    for n, o in ours.items():
        print(f"  {n:22s} dims={o['dims']} locz={o['loc_z']} v={o['verts']} q/t={o['quads']}/{o['tris']} area={o['area_m2']} v/m2={o['v_per_m2']} edge~{o['edge_proxy_mm']} mods={o['mods']} mats={ {k:(v['sheen'],v['rough']) if v else None for k,v in o['mats'].items()} }")
    print("\n== SHEEN census (asset, obj, mat, sheen, rough, principled)")
    for c in census:
        print("  ", c)
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
