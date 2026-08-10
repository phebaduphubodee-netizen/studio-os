"""asset_catalog.py — what is actually on the shelf, measured, with a verdict.

CLI-ONLY: run by hand when the shelf changes, and once at the top of DELIV-001's
P0b. It writes `assets/shared/CATALOG.json`, which P2's acquire step reads to
pick a mesh for a slot and which the procurement number is computed from. It is
not on a scheduled path because fetching is hand-run, and saying so is better
than looking wired.

WHY IT EXISTS
-------------
Twenty-nine model directories sit on disk — 16 from 3D Warehouse, 13 CC0 — and
zero were reachable from the lane that needed them. The audit that found this
also found the reason nobody noticed: there was no inventory. `warehouse.py`
fetches, `asset_scale.py` asserts one file at a time, and nothing ever answered
"what do we HAVE, and is any of it the right size for the slot".

The number this produces is not a nicety. R8 sends free-form objects to ACQUIRE
and hands a failure to the owner as a PROCUREMENT DECISION, never as a modelling
task — and a procurement decision needs a count, in week one, not a discovery in
week three.

WHAT IT REFUSES TO DO
---------------------
It does not guess a slot class. A model whose class cannot be read from its own
metadata is recorded as `slot: null` with `verdict: "unclassified"`, because a
guessed class would be a band assertion against a band nobody chose. It also
never writes a verdict of "usable" for a file it could not measure: an unreadable
model is `verdict: "unreadable"` carrying the exception text, so "could not look"
and "looked and it was fine" cannot be confused — the same law as pixel_check's
exit code 2.
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_scale as SCALE  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHELVES = {
    "cc0": os.path.join(REPO, "assets", "shared", "cc0", "models"),
    "warehouse": os.path.join(REPO, "assets", "shared", "warehouse"),
}
OUT_REL = os.path.join("assets", "shared", "CATALOG.json")

# An object-scale model fits in a room; a whole-room export does not fit in a
# slot. `place_model` scales UNIFORMLY to a footprint, so a 25 m scene handed to a
# 900 mm slot is not a scaling problem, it is the wrong object — and
# millwork.model_fit will reject it loudly. Recording the verdict here means the
# rejection is known before a render, not after one.
OBJECT_SCALE_MAX_MM = 3000.0
OBJECT_SCALE_MIN_MM = 40.0

# CAUGHT IN THIS FILE'S OWN FIRST OUTPUT. The run that produced the first catalog
# printed `shirt_hanger_a  616x12x715  usable` — the 11.7 mm billboard cutout that
# `asset_scale.MIN_DEPTH_RATIO` was written to refuse a round earlier. The band
# check and the planar check live in asset_scale and this module called only the
# first, so a model already known to be a cutout came back green from a new
# instrument. That is the flattering-scorer shape exactly: a fresh guard that
# quietly drops a rung an older one had.
#
# The floor here is COARSE and deliberately so — 0.02 catches a billboard and
# clears everything that has any depth at all. Per-class floors stay in
# asset_scale, which knows that a rug is legitimately 12 mm and a shirt is not;
# this is an inventory, and its job is to stop a known cutout reading as stock.
MIN_DEPTH_RATIO = 0.02

# Slot classes are read from the directory name, never inferred from geometry.
# Anything not matched is `unclassified` — see the docstring.
SLOT_WORDS = {
    "chair": "seating", "sofa": "seating", "lounge": "seating", "ottoman": "seating",
    "stool": "seating", "bench": "seating",
    "vase": "styling", "calathea": "styling", "plant": "styling", "bowl": "styling",
    "book": "styling", "tray": "styling",
    "nightstand": "case", "table": "case", "shelf": "case", "cabinet": "case",
    "bed": "bed", "garment": "garment", "shirt": "garment", "hanger": "garment",
}


def slot_of(slug):
    s = slug.lower()
    for word, cls in SLOT_WORDS.items():
        if word in s:
            return cls
    return None


def model_file(d):
    hits = sorted(glob.glob(os.path.join(d, "*.gltf")) + glob.glob(os.path.join(d, "*.glb")))
    return hits[0] if hits else None


def triangles(path):
    """Triangle count from the glTF document alone — index accessor counts, or
    POSITION counts for non-indexed primitives. Returns None if it cannot be read
    without decoding a buffer, because a guessed poly count would be worse than
    no poly count when the whole point is comparing against a 3,124-poly floor."""
    try:
        gl = SCALE._gltf_json(path)
    except Exception:
        return None
    acc = gl.get("accessors", [])
    n = 0
    for mesh in gl.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4:          # 4 = TRIANGLES
                continue
            i = prim.get("indices")
            if i is not None and i < len(acc):
                n += acc[i].get("count", 0) // 3
            else:
                p = prim.get("attributes", {}).get("POSITION")
                if p is not None and p < len(acc):
                    n += acc[p].get("count", 0) // 3
    return n or None


def licence_of(shelf, d):
    src = os.path.join(d, "SOURCE.json")
    if os.path.isfile(src):
        try:
            with open(src, encoding="utf-8") as f:
                return json.load(f).get("license")
        except Exception:
            pass
    if shelf == "cc0":
        return "CC0 (Poly Haven) — public domain, commercial use, redistributable"
    return None


def row(shelf, d):
    slug = os.path.basename(os.path.normpath(d))
    r = {"slug": slug, "shelf": shelf, "slot": slot_of(slug),
         "licence": licence_of(shelf, d)}
    path = model_file(d)
    if path is None:
        r.update(file=None, verdict="unreadable", why="no .gltf or .glb in the directory")
        return r
    r["file"] = os.path.relpath(path, REPO).replace("\\", "/")
    try:
        b = SCALE.bounds_mm(path)
    except Exception as e:
        r.update(verdict="unreadable", why=f"{type(e).__name__}: {e}")
        return r
    dims = {k: round(v, 1) for k, v in b.items() if k != "prims"}
    r["bounds_mm"] = dims
    r["prims"] = b["prims"]
    r["tris"] = triangles(path)
    longest = max(dims.values())
    thinnest = min(dims.values())
    r["longest_mm"] = longest
    r["thinnest_over_longest"] = round(thinnest / max(longest, 1e-9), 4)
    if r["thinnest_over_longest"] < MIN_DEPTH_RATIO:
        r.update(verdict="planar",
                 why=f"thinnest axis {thinnest:.0f} mm against a longest of "
                     f"{longest:.0f} — ratio {r['thinnest_over_longest']:.4f}. "
                     f"This is a cutout, not an object. asset_scale refuses it "
                     f"per class; an inventory must not list it as stock.")
    elif longest > OBJECT_SCALE_MAX_MM:
        r.update(verdict="out-of-band",
                 why=f"longest axis {longest:.0f} mm — this is a scene or a room, "
                     f"not an object for a slot; place_model scales uniformly and "
                     f"cannot subset it")
    elif longest < OBJECT_SCALE_MIN_MM:
        r.update(verdict="out-of-band", why=f"longest axis {longest:.0f} mm — too small "
                                            f"to be the object its name claims")
    elif r["slot"] is None:
        r.update(verdict="unclassified",
                 why="no slot class readable from the name; a guessed class would be "
                     "a band assertion against a band nobody chose")
    else:
        r.update(verdict="usable")
    return r


def build():
    rows = []
    for shelf, root in SHELVES.items():
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            d = os.path.join(root, name)
            if os.path.isdir(d):
                rows.append(row(shelf, d))
    return rows


def shortfall(rows, need=12):
    """The procurement number. Counts USABLE STYLING objects against D7's need —
    styling specifically, because a sofa does not dress a nightstand."""
    usable = [r for r in rows if r["verdict"] == "usable"]
    styling = [r for r in usable if r["slot"] == "styling"]
    return {
        "d7_needs": need,
        "usable_total": len(usable),
        "usable_styling": len(styling),
        "styling_short_by": max(0, need - len(styling)),
        "usable_styling_slugs": [r["slug"] for r in styling],
        "_note": "styling is what D7 counts. Seating and case goods are usable and "
                 "necessary, and they do not dress a room.",
    }


def summary(rows):
    by = {}
    for r in rows:
        by[r["verdict"]] = by.get(r["verdict"], 0) + 1
    return by


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(REPO, OUT_REL))
    ap.add_argument("--print", action="store_true", help="print the table, write nothing")
    a = ap.parse_args(argv)

    rows = build()
    sf = shortfall(rows)
    doc = {
        "_what": "Measured inventory of every model on the shelf, with a verdict. "
                 "Written by pipeline/scripts/asset_catalog.py; read by P2's acquire "
                 "step and by the procurement number handed to the owner.",
        "_law": "A verdict of 'unreadable' is never 'usable'. Could-not-look must not "
                "print like looked-and-it-was-fine.",
        "counts": summary(rows),
        "shortfall": sf,
        "models": rows,
    }
    for r in rows:
        v, dims = r["verdict"], r.get("bounds_mm")
        size = (f"{dims['x_mm']:.0f}x{dims['y_mm']:.0f}x{dims['z_mm']:.0f}"
                if dims else "-")
        print(f"{r['shelf']:10s} {r['slug']:26s} {str(r['slot'] or '-'):9s} "
              f"{size:>22s} {str(r.get('tris') or '-'):>8s}  {v}")
    print(f"\ncounts: {summary(rows)}")
    print(f"D7 needs {sf['d7_needs']} styling objects; usable styling on the shelf: "
          f"{sf['usable_styling']}  -> SHORT BY {sf['styling_short_by']}")
    if not a.__dict__["print"]:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
