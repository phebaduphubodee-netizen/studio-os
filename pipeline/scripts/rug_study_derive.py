"""STUDY-D14 (2026-09-02) rug study — the reproduction recipe for every number in
knowledge/_inbox/model-study/2026-09-02-rug.md. Pure Python, no bpy: reads the probe dumps
in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-rugs.json.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D14-rug): Recipe D and TOP-10 rule 4
were both built from ONE rug, 0fd746ae — "slab ~26 mm + Base=AO<HUE_SAT<diffuse>> + BUMP
height + DISPLACEMENT, pile 100% in the shader, geometry 210 v/m2 is enough". A corpus of
seven more must say whether that is a rule or a coincidence. So this script measures exactly
the quantities that claim is made of, on every rug INCLUDING the original, and prints them
side by side. It is built to be able to REFUTE the note that produced it.

Definitions (mm, world space, from world_bbox_mm / dims_mm):
  thickness   = the rug mesh z extent (Recipe D's "slab ~26 mm")
  v_per_m2    = the dump's own verts_per_m2 on the largest-area mesh (Recipe D's "210 is enough")
  pile_route  = where the pile lives, decided by evidence and NOT by taste:
                  "geometry:particles"          - a PARTICLE_SYSTEM modifier (real hair)
                  "geometry:displace-modifier"  - a DISPLACE modifier (real displaced verts)
                  "mesh:dense-relief"           - no such modifier but >= 25,000 v/m2. A THRESHOLD,
                                  not a sighting: the dump cannot tell modelled yarn
                                  from a dense sheet carrying a normal map, and on
                                  d326591b the area is BELOW a flat slab of the same
                                  footprint, so there is no room for strand bodies.
                  "shader:displacement-node"    - a DISPLACEMENT node in a material
                  "flat:none-of-the-above"      - nothing anywhere carries pile
                A rug may match SEVERAL routes; the field lists all that apply, because the
                whole finding of this unit is that the routes are not exclusive and Recipe D
                named only one of them.
  disp_nodes  = materials carrying a DISPLACEMENT node (Recipe D's shader half)

The readers and edge_proxy_mm come from study_probe_read — the same definitions the bed and
curtain studies use, so the three notes compare without a second implementation of anything.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import (REPO, edge_proxy_mm, img_sizes, load, meshes,  # noqa: E402
                              mods, surplus)

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-rugs.json")

# prefix -> (label, tier, why this one is in the corpus)
SETS = {
    "0fd746ae": ("Carpet (THE n=1 RECIPE D WAS BUILT FROM)", "full_plan",
                 "the single rug behind Recipe D and TOP-10 rule 4; it is IN the corpus so the "
                 "rule is tested against its own source rather than around it"),
    "d326591b": ("Athena Reversible Persian Rug", "free", "the density extreme: 913k faces"),
    "217e01bc": ("Rug Classic", "full_plan", "the paid density extreme: 634k faces"),
    "f48cece3": ("Soft Shaggy Rug", "full_plan", "SHAG - the pile question at its sharpest"),
    "a8f4c331": ("Modern Carpet", "full_plan", "the catalogue simulation flag was set on it"),
    "3efaabe9": ("Rough Beige Rug", "full_plan", "low-poly paid"),
    "9287710c": ("Contemporary carpet", "free", "mid-poly free"),
    "021601af": ("Carpet geometric pattern", "full_plan",
                 "representative of the 7-asset 76,386-face vendor family that dominates the "
                 "band, so the corpus is not silently one studio"),
}
OURS = "rug__acq0"
RECIPE_D_CLAIMS = {
    "slab_mm": 26,
    "v_per_m2_is_enough": 210,
    "base_chain": "AO<HUE_SAT<diffuse>>",
    "pile_route": "shader (BUMP height + DISPLACEMENT), 100%",
    "source": ("knowledge/_inbox/model-study/2026-09-01-materials-rug.md Recipe D and the "
               "INDEX TOP-10 rule 4, both from n=1 (0fd746ae)"),
}


def _mat_row(mt):
    nh = mt.get("node_hist") or {}
    p = mt.get("principled") or {}
    return {"name": mt["name"], "nodes": sum(nh.values()), "kinds": len(nh),
            "disp_nodes": sorted(k for k in nh if "DISPLAC" in k.upper()),
            "roughness": str(p.get("Roughness"))[:60],
            "normal": str(p.get("Normal"))[:60],
            "base": str(p.get("Base Color"))[:60],
            "has_AO": any("AMBIENT_OCCLUSION" in k or k == "AO" for k in nh),
            "has_HUE_SAT": any("HUE_SAT" in k for k in nh)}


def _pile_route(o, mats):
    mm = mods(o)
    routes = []
    if any(x.startswith("PARTICLE_SYSTEM") for x in mm):
        routes.append("geometry:particles")
    if any(x.startswith("DISPLACE") for x in mm):
        routes.append("geometry:displace-modifier")
    if o["mesh"]["verts_per_m2"] >= 25000:
        routes.append("mesh:dense-relief")
    if any(m["disp_nodes"] for m in mats):
        routes.append("shader:displacement-node")
    return routes or ["flat:none-of-the-above"]


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0], "_recipe_d_claims": RECIPE_D_CLAIMS,
           "rugs": {}}
    for pre, (label, tier, why) in SETS.items():
        fn, d = load(pre)
        ms = meshes(d)
        big = max(ms, key=lambda o: o["mesh"]["area_m2"])
        m = big["mesh"]
        mats = [_mat_row(mt) for mt in d["materials"]]
        out["rugs"][pre] = {
            "file": fn, "label": label, "tier": tier, "why_in_corpus": why,
            "source": d["source"], "n_objects": len(d["objects"]), "n_mesh": len(ms),
            "n_images": len(d.get("images", [])), "image_sizes": img_sizes(d),
            "mesh": {"name": big["name"], "dims": [round(x) for x in big["dims_mm"]],
                     "thickness_mm": round(big["dims_mm"][2]),
                     "verts": m["verts"], "polys": m["polys"], "quads": m["quads"],
                     "tris": m["tris"], "area_m2": round(m["area_m2"], 3),
                     "v_per_m2": round(m["verts_per_m2"]),
                     "edge_proxy_mm": round(edge_proxy_mm(big), 1),
                     "surplus": round(surplus(big), 2), "mods": mods(big)},
            "materials": mats,
            "pile_route": _pile_route(big, mats),
            "all_mesh_names": sorted(o["name"] for o in ms),
        }

    _, do = load("_ours_p2r91")
    o = [x for x in meshes(do) if x["name"] == OURS][0]
    m = o["mesh"]
    omats = [_mat_row(mt) for mt in do["materials"] if mt["name"] in o["materials"]]
    out["ours"] = {"name": OURS, "dims": [round(x) for x in o["dims_mm"]],
                   "thickness_mm": round(o["dims_mm"][2]), "verts": m["verts"],
                   "area_m2": round(m["area_m2"], 3), "v_per_m2": round(m["verts_per_m2"]),
                   "edge_proxy_mm": round(edge_proxy_mm(o), 1), "mods": mods(o),
                   "materials": omats, "pile_route": _pile_route(o, omats)}

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    hdr = (f"{'asset':10s} {'tier':9s} {'thick':>5s} {'v/m2':>8s} {'edge':>6s} "
           f"{'dispN':>5s} {'AO':>3s} {'HueSat':>6s}  pile route / mods")
    print(hdr)
    for pre, r in out["rugs"].items():
        me = r["mesh"]
        nd = sum(1 for x in r["materials"] if x["disp_nodes"])
        ao = sum(1 for x in r["materials"] if x["has_AO"])
        hs = sum(1 for x in r["materials"] if x["has_HUE_SAT"])
        print(f"{pre:10s} {r['tier']:9s} {me['thickness_mm']:>5d} {me['v_per_m2']:>8d} "
              f"{me['edge_proxy_mm']:>6.1f} {nd:>5d} {ao:>3d} {hs:>6d}  "
              f"{'+'.join(r['pile_route'])} {me['mods']}")
    o2 = out["ours"]
    nd = sum(1 for x in o2["materials"] if x["disp_nodes"])
    ao = sum(1 for x in o2["materials"] if x["has_AO"])
    hs = sum(1 for x in o2["materials"] if x["has_HUE_SAT"])
    print(f"{'OURS':10s} {'-':9s} {o2['thickness_mm']:>5d} {o2['v_per_m2']:>8d} "
          f"{o2['edge_proxy_mm']:>6.1f} {nd:>5d} {ao:>3d} {hs:>6d}  "
          f"{'+'.join(o2['pile_route'])} {o2['mods']}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
