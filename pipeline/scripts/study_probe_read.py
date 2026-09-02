"""Shared readers for the BlenderKit study probe dumps (ORD-2026-09-01).

WHY THIS MODULE EXISTS. On 2026-09-02 the made-bed study grew its own `edge_mm`,
and a scrutinize pass found it was a DIFFERENT QUANTITY from `bedcloth_fit.edge_mm`
wearing the same name and the same unit — the note had divided one by the other.
The second study (curtains) would have copied the same function, so the primitives
live here once: one definition, one name, one place to fix.

Pure Python, NO `bpy` (pipeline/CLAUDE.md layer law) — everything reads the JSON that
`model_study_probe.py` wrote, and a quantity a dump does not carry is not available
here at any price. In particular a dump has no edge list, which is why `edge_proxy_mm`
below is a proxy and says so in its name.
"""
import glob
import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STUDY = os.path.join(REPO, "assets", "shared", "blenderkit", "_study")


def load(prefix, study=None):
    """The one dump whose filename starts with `prefix`. Two matches is a caller
    bug (an ambiguous prefix), not something to resolve by picking one."""
    fs = glob.glob(os.path.join(study or STUDY, prefix + "*.probe.json"))
    assert len(fs) == 1, (prefix, fs)
    return os.path.basename(fs[0]), json.load(open(fs[0], encoding="utf-8"))


def find(d, name):
    """The MESH object called `name`. Exact match wins; a unique prefix match is
    accepted because vendors suffix duplicated names (.001); anything ambiguous
    RAISES rather than guessing, because guessing here silently re-points every
    number computed from the object."""
    for o in d["objects"]:
        if o["name"] == name and o["type"] == "MESH":
            return o
    hits = [o for o in d["objects"] if o["type"] == "MESH" and o["name"].startswith(name)]
    if len(hits) == 1:
        return hits[0]
    raise KeyError((name, [h["name"] for h in hits]))


def meshes(d):
    return [o for o in d["objects"] if o["type"] == "MESH"]


def edge_proxy_mm(o):
    """Square root of area per QUAD-EQUIVALENT face, in mm.

    NOT `bedcloth_fit.edge_mm`, which is the TRUE median edge length read off the
    mesh's edge list in world space (bedcloth_fit.py:45) and is what
    `bedcloth_rules.fineness` consumes. A probe dump carries no edge list, so this
    is the closest available quantity offline. On a regular quad grid the two nearly
    agree; on elongated or irregular faces they diverge by an unmeasured amount.
    Never divide one by the other and report the ratio as a fact."""
    m = o["mesh"]
    faces = m["quads"] + m["tris"] / 2.0 + m.get("ngons", 0)
    if not faces:
        faces = m["polys"]
    return math.sqrt(m["area_m2"] / faces) * 1000.0 if faces else float("nan")


def surplus(o):
    """area / plan-bbox area — fold richness. ASSUMES the object is axis-aligned in
    plan: dims_mm x/y are its own bbox axes, so a set authored on rotated axes gives
    a denominator that is not the plan footprint and a surplus that is an artifact."""
    dx, dy = o["dims_mm"][0], o["dims_mm"][1]
    return o["mesh"]["area_m2"] / (dx * dy * 1e-6) if dx and dy else float("nan")


def mat_row(d, name):
    for mt in d["materials"]:
        if mt["name"] == name:
            p = mt.get("principled") or {}
            return {"sheen": p.get("Sheen Weight"), "rough": p.get("Roughness"),
                    "base": str(p.get("Base Color"))[:40], "normal": str(p.get("Normal"))[:40],
                    "principled": "BSDF_PRINCIPLED" in (mt.get("node_hist") or {})}
    return None


def mods(o):
    return [x["type"] + (f"({x.get('levels')},{x.get('render_levels')})" if x["type"] == "SUBSURF" else "")
            for x in o.get("modifiers", [])]


def img_sizes(d):
    """[[w, h, count], ...] largest area first — so a note's image column is
    regenerated rather than hand-read (two verifier rounds each caught a wrong
    image band in a hand-read column)."""
    hist = {}
    for i in d.get("images", []):
        k = tuple(i["size"])
        hist[k] = hist.get(k, 0) + 1
    return [[w, h, n] for (w, h), n in sorted(hist.items(), key=lambda kv: -kv[0][0] * kv[0][1])]
