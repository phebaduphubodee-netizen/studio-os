"""STUDY-D18 (2026-09-02) lighting-fixture study — the reproduction recipe for every number in
knowledge/_inbox/model-study/2026-09-02-lighting-fixtures.md. Pure Python, no bpy: reads the
probe dumps in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-lighting.json.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D18-lighting-fixtures): how a professional
file builds the CORD, the BULB and the SOCKET — separate objects or not, how many verts, and what
CURVE bevel radius — to feed the lane's open sense-item "the lamps have no cord".

THE EXAM PRESUMED CURVES, AND THE CORPUS HAS NONE. Every rung in this repo reads MESH objects
only, and that has already cost the lane once: the 37 clothes hangers in the frame are CURVE
objects, so no placement, carry or census rung could see them. So `study_probe_read.curves` was
written for this unit expecting to find bevelled curves used as flex. There are ZERO CURVE objects
across all six lamps. That is a real answer rather than a failed search — but it is only knowable
because the reader was built and pointed at them.

  slenderness     max(dims) / middle(dims), per mesh. A cord, a stem and a pole are slender; a
                  shade, a bulb and a canopy are not. It is a ratio and not a list of names, so
                  the next asset cannot escape it by calling its cord something else — the rule
                  R9b names ("a rule that names the objects it applies to will always exempt the
                  next one"). Every mesh is reported with its number so the reading is disputable.
  emitting        a material is EMITTING when it carries an EMISSION/BSDF_EMISSION node, OR a
                  Principled with a non-black Emission Color AND a positive Emission Strength.
                  THE SECOND HALF WAS MISSING AND IT MATTERED: two of the six emit through a
                  Principled, so a detector that looked only for EMISSION nodes reported them as
                  having no emitter at all. And Emission Strength ALONE is not enough either —
                  1.0 is Blender's default, so strength-only would have called every Principled
                  material in every file a light. `Emission Color` was added to the probe for
                  this unit; a dump probed before 2026-09-02 does not carry it.
  BLACK_EPS       an emission colour whose channels are all below this is treated as not
                  emitting, and any material that lands within 10x of it is FLAGGED rather than
                  silently dropped (a8348982's `Steel.001` reads 0.016 and is the case).

WHAT IS COMPARED ON OUR SIDE: the two table lamps in the p2r91 frame and the two hand-built
sconces. Their object counts are the answer to the sense-item, and they are counted the same way.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import (REPO, load, meshes, curves, lights,  # noqa: E402
                              bevel_mm, edge_proxy_mm)

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-lighting.json")

BLACK_EPS = 0.002

ASSETS = {
    "a2ff3a79": ("APOLLO Pendant Light", "full_plan", "pendant_lamp",
                 "the tallest pendant on the shelf (1502 mm) — the longest drop, so the best "
                 "chance of a modelled cord"),
    "a6068c83": ("MARKSLOJD-style pendant lamps", "full_plan", "pendant_lamp",
                 "five pendants in one asset: five drops, and the only file here with LIGHT "
                 "datablocks"),
    "dafcda42": ("Jefferson Pendant large", "full_plan", "pendant_lamp",
                 "150 x 150 x 659 — narrow, and it asserted at EXACTLY the band floor of 150.0"),
    "85f6c3d5": ("Rattan Floor Lamp", "full_plan", "floor_lamp", "a floor lamp's cord run"),
    "a6313486": ("Wicker Wall Lamp", "full_plan", "wall_lamp",
                 "hard-wired by construction — the control for 'no cord is correct here'"),
    "a8348982": ("IKEA Alang Floor Lamp", "free", "floor_lamp",
                 "the free-tier comparison inside the class"),
}

OURS_LAMP = ("nightstand__lampacq-367__acq0", "nightstand__lampacq-367__acq1",
             "nightstand__lampacq2188__acq0", "nightstand__lampacq2188__acq1")
OURS_SCONCE_PREFIX = "bf14_sconce"

# knowledge/ rows found 2026-09-02. PLACEMENT only — the vault has no fixture-SIZE row for any
# of the three classes, which is why asset_scale's three lamp bands are declared assumptions.
VAULT = {
    "pendant_bottom_above_table_mm": [762, 914,
                                      "knowledge/lighting/lumen-method-and-fixture-placement.md:127-128"],
    "sconce_centre_affl_mm": [1397, 1524,
                              "docs/research/2026-08-08-upgrade-dr/ANSWER_gemini_q5-hero-light-practice_grounded.md:86-87"],
    "sconce_shade_above_mattress_mm": [305, 508, "same source"],
    "floor_lamp": [None, None, "NO ROW IN knowledge/ (searched 2026-09-02)"],
    "cord_grammar": [None, None,
                     "knowledge/_inbox/video-study/2026-08-28-designer-redesigns-four-real-"
                     "bedrooms-kmCHv3PG2XM.md:55-73 — a cord is either hidden behind its own "
                     "furniture or deliberately exposed as a line on the wall. There is no third "
                     "state; a dangling cord is a defect."],
}


def _slender(o):
    d = sorted(o["dims_mm"])
    return round(d[2] / max(d[1], 1e-9), 2)


def _emitters(d):
    """returns (emitting, borderline). See the docstring for why both halves are needed."""
    emitting, borderline = [], []
    for m in d.get("materials", []):
        h = m.get("node_hist") or {}
        pr = m.get("principled") or {}
        ec = pr.get("Emission Color")
        es = pr.get("Emission Strength")
        if h.get("EMISSION") or h.get("BSDF_EMISSION"):
            emitting.append({"material": m["name"], "how": "EMISSION node"})
            continue
        if isinstance(ec, str):
            # a LINKED socket, recorded by the probe as e.g. "HUE_SAT<IMG:2_BaseColor.jpg>".
            # It is driven by a node tree, so its value is not in the dump — undecidable, and
            # said so rather than compared. `max("HUE"[:3])` returns a CHARACTER, which either
            # raises against a float or silently orders as text.
            borderline.append({"material": m["name"], "emission_color": ec,
                               "emission_strength": es,
                               "why": "Emission Color is a LINKED socket — value not in the dump"})
            continue
        if ec and isinstance(ec, (list, tuple)) and es and es > 0:
            peak = max(float(v) for v in ec[:3])
            if peak > BLACK_EPS * 10:
                emitting.append({"material": m["name"], "how": "principled",
                                 "emission_color": [round(v, 3) for v in ec[:3]],
                                 "emission_strength": es})
            elif peak > BLACK_EPS:
                borderline.append({"material": m["name"],
                                   "emission_color": [round(v, 3) for v in ec[:3]],
                                   "emission_strength": es,
                                   "why": "within 10x of black — reported, not counted"})
    return emitting, borderline


def _degenerate(o):
    """R10's identity question as a measurement: is this object's SURFACE consistent with the
    box it occupies? a2ff3a79's `Emmiter` is 456 x 456 x 203 mm and its whole mesh totals
    120 mm2 of area across 31,696 faces — an average face of 0.004 mm2. It was filed as the
    corpus's densest "bulb" on the strength of its NAME, which is the exact move this study
    refuses one section earlier for an object called `Wire`. Returns the ratio of real surface
    to the bbox's own surface; anything under 1% cannot be the solid its name implies."""
    d = o["dims_mm"]
    box = 2 * (d[0] * d[1] + d[1] * d[2] + d[0] * d[2]) / 1e6      # m2
    area = o["mesh"].get("area_m2") or 0.0
    return round(area / box, 5) if box else None


def _rows(ms):
    out = []
    for o in ms:
        a = o["mesh"].get("area_m2") or 0.0
        out.append({"name": o["name"], "dims_mm": [round(x) for x in o["dims_mm"]],
                    "verts": o["mesh"]["verts"], "faces": o["mesh"]["polys"],
                    "area_m2": round(a, 6),
                    # verts per m2 of real surface. The raw COUNT is not a density and the two
                    # do not rank the same way: a 37 mm bulb at 18,999 v and a 537 mm lamp at
                    # 3,778 v are 5x apart by count and 224x apart by density.
                    "verts_per_m2": (round(o["mesh"]["verts"] / a) if a > 0 else None),
                    "slenderness": _slender(o),
                    "surface_vs_bbox": _degenerate(o),
                    "edge_proxy_mm": round(edge_proxy_mm(o), 2),
                    "materials": o.get("materials")})
    return sorted(out, key=lambda r: -r["slenderness"])


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0], "_black_eps": BLACK_EPS,
           "_vault": VAULT, "assets": {}}
    for pre, (label, tier, cls, why) in ASSETS.items():
        fn, d = load(pre)
        ms, cs, ls = meshes(d), curves(d), lights(d)
        em, bl = _emitters(d)
        rows = _rows(ms)
        out["assets"][pre] = {
            "file": fn, "label": label, "tier": tier, "asserted_class": cls,
            "why_in_corpus": why,
            "n_mesh": len(ms), "n_curve": len(cs), "n_light_objects": len(ls),
            "n_materials": len(d["materials"]), "n_images": len(d.get("images", [])),
            "curves": [{"name": o["name"], "bevel_mm": bevel_mm(o),
                        "splines": o["curve"]["splines"],
                        "points": o["curve"]["points"]} for o in cs],
            "emitting_materials": em, "borderline_emitters": bl,
            "most_slender": rows[0] if rows else None,
            "objects": rows,
        }

    _, do = load("_ours_p2r91")
    oms = meshes(do)
    lamp = [o for o in oms if o["name"] in OURS_LAMP]
    sconce = [o for o in oms if o["name"].startswith(OURS_SCONCE_PREFIX)]
    o_em, o_bl = _emitters(do)
    em_names = {e["material"] for e in o_em}
    wearing = [x["name"] for x in oms if set(x.get("materials") or []) & em_names]
    hang = [x for x in do["objects"] if "hanger" in x["name"].lower()]
    out["ours"] = {
        "table_lamp_objects": _rows(lamp),
        "table_lamp_is_acquired": ("nightstand__lampacq* carries the __acq tag: it is a BOUGHT "
                                   "asset, not something this lane built. Any 'pro vs ours' "
                                   "line drawn against it is pro against pro."),
        "sconce_objects": _rows(sconce),
        # THE TEST THAT WAS ASSERTED IN PROSE AND NEVER RUN. It runs now, and it refutes the
        # sentence it was supposed to support: our scene HAS emitting materials, and four of
        # the objects wearing one are the hand-built sconce lenses this unit dissects.
        "emitting_materials": o_em,
        "borderline_emitters": o_bl,
        "objects_wearing_an_emitting_material": len(wearing),
        "emitting_object_names_sample": sorted(wearing)[:8],
        "n_curve_in_whole_scene": len(curves(do)),
        "n_light_objects_in_whole_scene": len(lights(do)),
        "hanger_named_objects": {"total": len(hang),
                                 "CURVE": sum(1 for x in hang if x.get("type") == "CURVE"),
                                 "EMPTY": sum(1 for x in hang if x.get("type") == "EMPTY")},
        "note": ("the hangers are 37 NAMED objects but only 23 are CURVE — the other 14 are "
                 "EMPTY parents. The table lamp is base + shade, and it is acquired."),
    }

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    for pre, s in out["assets"].items():
        print(f"\n== {pre} {s['label'][:34]:34} [{s['tier']:9}] mesh={s['n_mesh']} "
              f"CURVE={s['n_curve']} LIGHT_obj={s['n_light_objects']} mat={s['n_materials']}")
        print(f"   emitting: {[e['material'] for e in s['emitting_materials']]}"
              + (f"  borderline: {[b['material'] for b in s['borderline_emitters']]}"
                 if s["borderline_emitters"] else ""))
        for r in s["objects"][:4]:
            print(f"     slender={r['slenderness']:6.2f} {r['name'][:26]:26} "
                  f"{str(r['dims_mm']):20} v={r['verts']:>7}")
    o = out["ours"]
    print(f"\n== OURS  table-lamp objects={len(o['table_lamp_objects'])} "
          f"sconce objects={len(o['sconce_objects'])} "
          f"CURVE in scene={o['n_curve_in_whole_scene']} "
          f"LIGHT objects={o['n_light_objects_in_whole_scene']}")
    print(f"   OUR emitting materials: {[e['material'] for e in o['emitting_materials']]}"
          f"  on {o['objects_wearing_an_emitting_material']} object(s)")
    print(f"   hangers: {o['hanger_named_objects']}")
    for r in o["table_lamp_objects"] + o["sconce_objects"]:
        print(f"     slender={r['slenderness']:6.2f} {r['name'][:30]:30} "
              f"{str(r['dims_mm']):20} v={r['verts']:>7} mats={r['materials']}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
