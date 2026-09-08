"""STUDY-D15 (2026-09-02) upholstered-seating study — the reproduction recipe for every
number in knowledge/_inbox/model-study/2026-09-02-seating.md. Pure Python, no bpy: reads the
probe dumps in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-seating.json.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D15-seating): say IN NUMBERS where a
pro upholstered seat differs from ours — density, seams, piping — against the _ours dump.

So the script splits every asset's meshes into three bands by density, because that split is
the finding: upholstery, structure, and a third band 3.6x-319x above the cushions that turns
out to be the STITCHING modelled as its own object.

  SHELL      < 25,000 v/m2   — frame, legs, plinth: structure, cheap on purpose
  UPHOLSTERY 25,000 - 1,000,000 v/m2 — the cushions and their folds
  DETAIL     >= 1,000,000 v/m2 — seams, piping, cord, small metal fittings. The threshold is
             one order above the densest cushion measured here (471,211) and one order below
             the sparsest detail (1,717,229), so nothing in this corpus sits near the line.

The bands are DENSITY ONLY and are named after what they turned out to hold; the script does
not read object names to decide, so a vendor who calls nothing "Sewing" is classified the
same way. Where a name does confirm the reading it is printed (33c5f315 ships an object
literally named `Sewing`, material `Linha_Costura`), but the name is evidence, never input.

edge_proxy_mm and the readers come from study_probe_read — same definitions as the bed,
curtain and rug studies, so the four notes compare without a second implementation.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import (REPO, edge_proxy_mm, img_sizes, load, meshes,  # noqa: E402
                              mods)

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-seating.json")

SHELL_MAX = 25_000.0
DETAIL_MIN = 1_000_000.0

SETS = {
    "a34e3cdf": ("Sheriff Armchair", "full_plan", "the density extreme: 3.19 M faces"),
    "62520f38": ("Upholstered Accent Chair", "free",
                 "the SECOND-densest free single seat, 1.07 M faces — the free extreme is "
                 "6c4752d5 Leather lounge chair at 1.31 M, which was not fetched"),
    "e0095b9b": ("Apex Linen Lounge Chair", "full_plan", "linen rather than leather"),
    "33c5f315": ("Otio Welsh Taupe Lounge Chair", "full_plan",
                 "ships an object named `Sewing` — the seam question answered by the vendor"),
    "10542494": ("Ottoman", "full_plan",
                 "the ottoman class, and a ONE-object asset. NOTE it is not from the "
                 "504-row single-seat pool: its plan is 1978 x 922 mm, so the <=1.20 m "
                 "single-seat cut excludes it and it was taken from the 631-row band pool "
                 "as a deliberate class exception"),
    "6429a852": ("Lc3", "full_plan", "a classic frame-and-cushion chair"),
}
# ours, from the p2r91 scene dump: every mesh wearing an upholstery material
OURS = ["bench__acq0", "bench__acq1", "stool__acq0", "stool__acq1", "stool__acq2"]


def _band(vpm):
    if vpm >= DETAIL_MIN:
        return "detail"
    if vpm >= SHELL_MAX:
        return "upholstery"
    return "shell"


def _row(o):
    m = o["mesh"]
    return {"name": o["name"], "dims": [round(x) for x in o["dims_mm"]],
            "verts": m["verts"], "area_m2": round(m["area_m2"], 4),
            "v_per_m2": round(m["verts_per_m2"]),
            "edge_proxy_mm": round(edge_proxy_mm(o), 1),
            "band": _band(m["verts_per_m2"]), "mods": mods(o),
            "materials": list(o["materials"])}


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0],
           "_bands": {"shell_max_v_per_m2": SHELL_MAX, "detail_min_v_per_m2": DETAIL_MIN},
           "seats": {}}
    for pre, (label, tier, why) in SETS.items():
        fn, d = load(pre)
        ms = meshes(d)
        rows = sorted((_row(o) for o in ms), key=lambda r: -r["v_per_m2"])
        by = {"shell": [], "upholstery": [], "detail": []}
        for r in rows:
            by[r["band"]].append(r)
        out["seats"][pre] = {
            "file": fn, "label": label, "tier": tier, "why_in_corpus": why,
            "source": d["source"], "n_objects": len(d["objects"]), "n_mesh": len(ms),
            "n_materials": len(d["materials"]), "n_images": len(d.get("images", [])),
            "image_sizes": img_sizes(d),
            "total_verts": sum(o["mesh"]["verts"] for o in ms),
            "counts": {k: len(v) for k, v in by.items()},
            "upholstery_v_per_m2": [r["v_per_m2"] for r in by["upholstery"]],
            "detail_v_per_m2": [r["v_per_m2"] for r in by["detail"]],
            "meshes": rows,
        }

    _, do = load("_ours_p2r91")
    ours = {}
    for n in OURS:
        o = [x for x in meshes(do) if x["name"] == n]
        if o:
            ours[n] = _row(o[0])
    out["ours"] = ours
    out["ours_note"] = ("every upholstered mesh in the p2r91 scene. There is no hand-built "
                        "tub chair in this frame: `_build_tub_chair` exists in build_room.py "
                        "but nothing it makes is in the dump, so the comparison the exam asks "
                        "for is against the ACQUIRED bench and stools that are actually there.")

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"{'asset':10s} {'tier':9s} {'mesh':>4s} {'totV':>9s} {'shell':>5s} {'uph':>4s} "
          f"{'det':>4s}  upholstery v/m2 (each)")
    for pre, s in out["seats"].items():
        c = s["counts"]
        print(f"{pre:10s} {s['tier']:9s} {s['n_mesh']:>4d} {s['total_verts']:>9d} "
              f"{c['shell']:>5d} {c['upholstery']:>4d} {c['detail']:>4d}  "
              f"{s['upholstery_v_per_m2']}")
        for r in s["meshes"]:
            if r["band"] == "detail":
                print(f"           DETAIL {r['name'][:28]:28s} v={r['verts']:>7} "
                      f"v/m2={r['v_per_m2']:>9} edge~{r['edge_proxy_mm']:.1f} {r['materials'][:2]}")
    print()
    print("OURS (p2r91):")
    for n, r in out["ours"].items():
        print(f"  {n:14s} v={r['verts']:>6} v/m2={r['v_per_m2']:>7} edge~{r['edge_proxy_mm']:>5.1f} "
              f"band={r['band']:10s} mats={r['materials'][:2]}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
