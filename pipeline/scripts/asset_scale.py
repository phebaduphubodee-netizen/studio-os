"""asset_scale.py — ASSERT the unit of an ingested glTF/GLB, never assume it.

CLI-ONLY: run by `warehouse.py fetch --assert-class <cls>` on every ingest (it
writes a `<asset>.scale.json` sidecar there whether or not a class is named),
and by hand as `python pipeline/scripts/asset_scale.py <file.glb> <class>` when
checking an asset already in the cache. `warehouse` is itself hand-run, so this
module is not reachable from a scheduled entry point and says so rather than
looking wired.

WHY THIS FILE EXISTS, IN THE REPO'S OWN WORDS
---------------------------------------------
`pipeline/CLAUDE.md` carries the rule as a MUST — "no external geometry reaches a
spec or a gate until its unit is RESOLVED and asserted — never assumed" — and in
the same section admits the assertion half was never built: `dwg_ingest.py`
resolves a unit and then falls through to `1.0, "assumed mm"` and keeps going,
and `warehouse.py` prints "SCALE IS NOT ASSERTED HERE — the caller must check"
and has never had a caller that did. The trap it guards is specific and this
repo has already named it: a SketchUp export can carry imperial numbers even
when the model was authored in metres, a 0.0254x error, and "a plausible-but-
wrong-scale model = the exact failure we sell against".

WHAT IT DOES AND WHAT IT REFUSES TO DO
--------------------------------------
It reads the bounds of a GLB in PURE PYTHON — no bpy, per the layer law — by
walking the node tree and transforming every mesh accessor's own min/max. Then
it compares the result against a per-class band that comes from a CITED source,
and it FAILS CLOSED: an unknown class raises rather than passing, because the
whole point is that "no band for this" and "within band" must not look alike.

WHAT IT CANNOT DO, SAID PLAINLY
-------------------------------
A bounds check catches a factor-of-25 unit error and a factor-of-1000 one. It
CANNOT catch a model that is simply the wrong size for its name — a child's
shirt and an adult's are both inside any band wide enough to be useful — and it
cannot see proportion at all: a 1100 mm object is in band whether it is a shirt
or a plank. It answers "is the UNIT right", which is the question the DR asked,
and nothing more. Do not let a green line here stand in for looking at the mesh.
"""
import json
import math
import os
import struct
import sys

# --------------------------------------------------------------------- bands --
# Each band is (min_mm, max_mm, axis, source). The axis is named because the
# useful dimension differs by class: a garment is diagnosed by its HEIGHT, a rug
# by its longest plan dimension. A band with no cited source does not belong
# here — this table is the difference between an assertion and a preference.
_GARMENT_SRC = ("knowledge/ergonomics/casework-fixture-clearances-th-practice.md:47 "
                "(PAPERROOM garment chart: shirt-blouse hung 1100 mm tall, "
                "550 mm width-depth; coat 1600; long skirt 1200)")
BANDS = {
    # A hung shirt is charted at 1100. The band spans a folded-trouser hanger
    # (500) to a coat (1600) with margin, because the class is "a garment on a
    # hanger" and the chart's own spread across that class is 3.2x.
    "garment_hung": (400.0, 1900.0, "z", _GARMENT_SRC),
    "hanger": (300.0, 600.0, "x", _GARMENT_SRC + "; a hanger spans a shoulder"),
    "vase": (80.0, 900.0, "z", "styling props, this lane's own lathe range"),
    "branch_dried": (200.0, 1500.0, "z", "a cut stem in a floor or table vessel"),
    "chair": (600.0, 1300.0, "z", _GARMENT_SRC.split("(")[0]
              + "knowledge/ergonomics/residential-clearances.md (seat 406-432, "
                "back to ~1100)"),
}

# ------------------------------------------------------------- planar refusal --
# ADDED THE HOUR THIS FILE'S FIRST REAL INGEST WALKED PAST IT. The first asset
# fetched for TRN-002 was a shirt on a hanger: 715 mm tall, comfortably inside
# the garment band, SCALE ASSERTED — and 11.7 mm deep. A billboard cutout. The
# bounds check could not see it, and this module's own docstring said so in
# advance ("it cannot see proportion at all"), which is a confession, not a
# guard. A stated blind spot that is cheap to close and left open is the
# flattering-scorer shape this repo keeps paying for.
#
# The threshold is per class because flatness is only a defect where the class
# has depth: a rug IS 12 mm thin and a shirt on a hanger is not. `None` means
# the class is legitimately planar and the check does not apply — declared, so
# that "exempt" and "unchecked" cannot look the same.
MIN_DEPTH_RATIO = {
    "garment_hung": 0.06,   # a shirt on a hanger is >= ~90 mm front-to-back
    "hanger": 0.02,
    "vase": 0.25,           # a lathed body is near-square in plan
    "branch_dried": 0.05,
    "chair": 0.35,
}


def _chunks(path):
    with open(path, "rb") as f:
        magic, _ver, _len = struct.unpack("<4sII", f.read(12))
        if magic != b"glTF":
            raise ValueError(f"{path} is not a binary glTF (magic {magic!r})")
        out = {}
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            clen, ctype = struct.unpack("<II", head)
            out[ctype] = f.read(clen)
        return out


def _gltf_json(path):
    """The glTF document, from either container form.

    BOTH FORMS, BECAUSE ONE OF THEM WAS SILENTLY REFUSING THE ENTIRE SHELF. This
    module only ever read the BINARY form (.glb, `glTF` magic), and every Poly
    Haven asset in `assets/shared/cc0/models/` ships the OTHER one — a JSON
    `.gltf` beside an external `.bin`. So all 13 of them raised "not a binary
    glTF" on ingest, which means the scale assertion `pipeline/CLAUDE.md` calls a
    MUST was dead for the whole CC0 shelf while reading like a working guard.
    Found 2026-08-09 by a plan audit, not by the guard suite, because nothing had
    ever tried to ingest one.

    The `.bin` IS NEVER READ, and that is not a shortcut — the bounds come from
    each accessor's own declared `min`/`max`, which live in the JSON in both
    forms. `bounds_mm` already refuses when they are absent rather than decoding
    a buffer and guessing, and that refusal is unchanged here.
    """
    with open(path, "rb") as f:
        head = f.read(4)
    if head == b"glTF":
        return json.loads(_chunks(path)[0x4E4F534A].decode("utf-8"))
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"{path} is not a binary glTF (magic {head!r}) and is not "
                         f"readable as a JSON glTF either ({e})")
    if not isinstance(doc, dict) or "asset" not in doc:
        raise ValueError(f"{path} is not a binary glTF (magic {head!r}) and the JSON "
                         f"it holds has no glTF `asset` block")
    return doc


def _node_matrix(node):
    """glTF node -> 4x4 row-major list. `matrix` is COLUMN-major in the file."""
    if "matrix" in node:
        m = node["matrix"]
        return [[m[0], m[4], m[8], m[12]],
                [m[1], m[5], m[9], m[13]],
                [m[2], m[6], m[10], m[14]],
                [m[3], m[7], m[11], m[15]]]
    t = node.get("translation", [0.0, 0.0, 0.0])
    r = node.get("rotation", [0.0, 0.0, 0.0, 1.0])   # x, y, z, w
    s = node.get("scale", [1.0, 1.0, 1.0])
    x, y, z, w = r
    rot = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
           [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
           [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[rot[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)] + \
           [[0.0, 0.0, 0.0, 1.0]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def _apply(m, p):
    return tuple(m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3]
                 for i in range(3))


def bounds_mm(path):
    """World-space AABB of a GLB, in MILLIMETRES.

    glTF declares metres (spec 3.3), so the x1000 below is the file format's own
    statement of unit — which is exactly why the check is worth running: a model
    exported through a chain that ignored that lands 25.4x or 1000x out, and the
    declaration keeps saying metres.
    """
    gl = _gltf_json(path)
    acc, meshes, nodes = (gl.get("accessors", []), gl.get("meshes", []),
                          gl.get("nodes", []))
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    seen = 0

    def walk(idx, parent):
        nonlocal seen
        node = nodes[idx]
        m = _mul(parent, _node_matrix(node))
        if "mesh" in node:
            for prim in meshes[node["mesh"]].get("primitives", []):
                a = prim.get("attributes", {}).get("POSITION")
                if a is None:
                    continue
                amin, amax = acc[a].get("min"), acc[a].get("max")
                if not amin or not amax:
                    continue
                seen += 1
                # All EIGHT corners: an AABB under a rotation is not the
                # transform of two corners, and a hanger arrives rotated.
                for bx in (amin[0], amax[0]):
                    for by in (amin[1], amax[1]):
                        for bz in (amin[2], amax[2]):
                            p = _apply(m, (bx, by, bz))
                            for i in range(3):
                                lo[i] = min(lo[i], p[i])
                                hi[i] = max(hi[i], p[i])
        for c in node.get("children", []):
            walk(c, m)

    ident = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    scenes = gl.get("scenes") or [{"nodes": list(range(len(nodes)))}]
    roots = scenes[gl.get("scene", 0)].get("nodes", [])
    for r in roots:
        walk(r, ident)
    if not seen:
        raise ValueError(f"{path}: no POSITION accessor carried min/max — "
                         f"bounds cannot be read without decoding the buffer, "
                         f"and a guess is the thing this file exists to refuse")
    # glTF is Y-up; this repo is Z-up. Report in the REPO's axes so the band
    # names ("z" for a garment's height) mean what they say.
    return {"x_mm": (hi[0] - lo[0]) * 1000.0,
            "y_mm": (hi[2] - lo[2]) * 1000.0,
            "z_mm": (hi[1] - lo[1]) * 1000.0,
            "prims": seen}


def assert_scale(path, cls, bands=None):
    """Returns (ok, report). FAILS CLOSED on an unknown class."""
    bands = BANDS if bands is None else bands
    if cls not in bands:
        raise KeyError(
            f"no scale band for class '{cls}'. Add one WITH A CITED SOURCE — an "
            f"unknown class must not pass, because 'no band' and 'in band' "
            f"reading the same is how an unasserted ingest gets called asserted")
    lo, hi, axis, src = bands[cls]
    b = bounds_mm(path)
    v = b[f"{axis}_mm"]
    in_band = lo <= v <= hi
    ratios = {f"x{f:g}": round(v * f, 1) for f in (0.0254, 1.0, 25.4, 1000.0)
              if lo <= v * f <= hi}
    dims = (b["x_mm"], b["y_mm"], b["z_mm"])
    ratio = min(dims) / max(max(dims), 1e-9)
    floor_ = MIN_DEPTH_RATIO.get(cls)
    planar = floor_ is not None and ratio < floor_
    ok = in_band and not planar
    return ok, {
        "file": os.path.basename(path), "class": cls, "axis": axis,
        "measured_mm": round(v, 1), "band_mm": [lo, hi], "ok": ok,
        "in_band": in_band,
        "thinnest_over_longest": round(ratio, 4),
        "min_ratio_for_class": floor_,
        "planar_refusal": (
            f"thinnest axis is {min(dims):.1f} mm against a longest of "
            f"{max(dims):.1f} — ratio {ratio:.4f} below the class floor "
            f"{floor_}. This is a CUTOUT, not a {cls}. A bounds check cannot "
            f"see it, which is why this line exists" if planar else None),
        "bbox_mm": {k: round(x, 1) for k, x in b.items() if k != "prims"},
        "prims": b["prims"], "source": src,
        # If it FAILS, say which unit interpretation WOULD have landed in band.
        # That turns "wrong" into "the exporter wrote inches", which is the
        # actionable half — and if nothing lands, the model is the wrong object,
        # not the wrong unit.
        "in_band_under": ratios if not in_band else None,
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print("usage: asset_scale.py <file.glb> <class>\n  classes: "
              + ", ".join(sorted(BANDS)))
        return 2
    try:
        ok, rep = assert_scale(argv[0], argv[1])
    except (KeyError, ValueError) as e:
        print(f"SCALE ASSERTION FAILED: {e}")
        return 1
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    print("SCALE ASSERTED" if ok else "SCALE REFUSED — do not let this reach a spec")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
