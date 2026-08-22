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
    # Two pillow classes because the useful axis follows the POSTURE, not the
    # object: a sleeping pillow is diagnosed lying (z = loft thickness), a
    # styled sham group standing (z = presented height). Bands cite the lane's
    # own signed rank dimensions, which themselves derive from the delivered-bed
    # reference (I-23-023 #499473).
    "pillow_set_lying": (120.0, 420.0, "z",
                         "pipeline/scripts/styling.py PILLOW_H=0.15 (a plump "
                         "sleeping pillow lying flat) with case-loft margin"),
    "pillow_set_standing": (350.0, 800.0, "z",
                            "pipeline/scripts/styling.py SHAM_H=0.44 (a 650mm "
                            "euro sham leaning upright presents ~450) + king "
                            "sham 500x900 case note at SHAM_W"),
    # A DRESSED BED'S CLOTH SET, diagnosed on the axis a duvet cannot fake: the
    # LENGTH it must cover. This lane's own mattress is 1969 mm long (the ink-true
    # element-3 footprint) and a duvet covers a mattress and falls past its foot,
    # so a set for a bed of this class measures ~2000-2400; the band opens to
    # 1400 (a single/child duvet — a real product, and refusing it here would be
    # the band judging TASTE instead of UNIT) and 2900 (super-king with a deep
    # fall). What it is actually for is the 0.0254x trap: an imperial-exported
    # set lands at 56-92 mm and a metres-as-millimetres one at 2.0-2.9, both
    # decades outside.
    "bedding_set": (1400.0, 2900.0, "y",
                    "projects/PRJ-2026-002_c001-house/03_layout/"
                    "master-suite.CANONICAL.spec.json element 3 (mattress "
                    "1969 mm long, ink-true) + standard duvet sizes"),
    # Towels are diagnosed by PRESENTED height, like garments. The band cites the
    # lane's own signed accessory schedule (bathroom.py): a hand towel presents
    # HAND_DROP=300 on a hook, a bath towel TOWEL_DROP=350 folded over the bar
    # (i.e. a ~700-1500mm towel presenting half or less), a robe ROBE_DROP=750 —
    # so a HUNG towel-class mesh lands 200..1000 with margin either side.
    "towel_hung": (200.0, 1000.0, "z",
                   "pipeline/scripts/bathroom.py HAND_DROP=300 / TOWEL_DROP=350 "
                   "/ ROBE_DROP=750 (the e6 accessory schedule, D-E6-3)"),
    # A folded towel on a counter presents its PLY STACK: bathroom.py builds the
    # counter towel 35mm tall; a plusher fold runs to ~120.
    "towel_folded": (20.0, 160.0, "z",
                     "pipeline/scripts/bathroom.py acc_hand_towel_counter part "
                     "(300x200x35, D-E6-3) with plush-fold margin"),
    # ---------------------------------------------------------------- p2r33 --
    # THE FOUR LOOSE-FURNITURE CLASSES, added when the owner ordered every
    # hand-built non-BF piece replaced by an acquired mesh. Each band is
    # diagnosed on the axis that does NOT depend on how a stranger exported the
    # file, which is a different choice per class and the reason they are not
    # one rule:
    #   - a BED and a RUG are diagnosed by their longest HORIZONTAL extent
    #     ("maxxy"), because their height is nearly meaningless (a platform bed
    #     is 250 mm, the same bed with a headboard is 1400) while their footprint
    #     is the thing the class is named for. maxxy is invariant under the only
    #     rotation furniture gets, which a literal "x" or "y" is not.
    #   - a NIGHTSTAND and a BENCH are diagnosed by HEIGHT, because that is what
    #     ergonomics pins (a bedside surface meets the mattress; a bench meets a
    #     knee) while their plan sizes range freely.
    "bed_frame": (1800.0, 2600.0, "maxxy",
                  "projects/PRJ-2026-002_c001-house/03_layout/"
                  "master-suite.CANONICAL.spec.json element 3 (2000 x 2149 mm "
                  "ink-true footprint); band opens to a 1900 double and a 2500 "
                  "super-king with a footboard"),
    # ---------------------------------------------------------------- p2r52 --
    # A WHOLE DRESSED BED in one file (frame + mattress + bedding + pillows +
    # its own headboard), diagnosed like bed_frame on the longest horizontal
    # extent — but the band opens wider on both ends because the assembly
    # includes side ledges, wing panels and drape that a bare frame does not
    # carry (the D-106 winner measures 3159 mm across its ledged platform,
    # inside wholebed_rules.ANCHOR_LONG_M's 3.30 m ceiling). What the band is
    # for is the unit traps: an imperial-as-metres king lands at ~80 mm and a
    # cm-as-metres one at ~32 m, both decades outside.
    "whole_bed": (1900.0, 3600.0, "maxxy",
                  "pipeline/scripts/wholebed_rules.py ANCHOR_LONG_M (1.55-3.30 "
                  "m bed-anchor band) + the drawn 2000 x 2149 mm footprint "
                  "(element 3, ink-true); D-106 audition table spans "
                  "2149-3160 mm native across 11 staged candidates"),
    "nightstand": (300.0, 800.0, "z",
                   "master-suite.CANONICAL.spec.json items[3..4] h=580 + "
                   "knowledge/ergonomics/residential-clearances.md (a bedside "
                   "surface sits at or just above the mattress top)"),
    "bench_seat": (300.0, 600.0, "z",
                   "master-suite.CANONICAL.spec.json items[2] h=450 + "
                   "knowledge/ergonomics/residential-clearances.md (seat "
                   "406-432); a backless bed-end bench is seat height and no more"),
    "rug": (1000.0, 5000.0, "maxxy",
            "master-suite.CANONICAL.spec.json items[0] 3100 x 2500 mm; band "
            "spans a bedside runner to a whole-room rug"),
    # ---------------------------------------------------------------- p2r37 --
    # THE CC0 SHELF, banded so it can be asserted for the first time. Measured
    # 2026-08-16: all 13 committed Poly Haven assets carried NO sidecar, because
    # `assets.py` never wrote one — so the MUST in pipeline/CLAUDE.md was dead for
    # the entire COMMITTED shelf while `build_room._model_path` handed those files
    # to `place_model` unasserted. The gitignored warehouse cache was the half
    # anyone remembered to check.
    #
    # These three are UNIT BANDS AND SAY SO. They are deliberately wider than the
    # ergonomic range they cite, because the shelf's own `coffee_table_round_01`
    # is 491 mm tall and Ottoman_01 is 624 — both real products, both outside the
    # ergonomic table. Refusing them here would be the band judging TASTE, and
    # this module answers one question: is the UNIT right (the 0.0254x and 1000x
    # traps), nothing more. Height is the axis for all three because that is what
    # ergonomics pins; plan sizes range freely across a catalogue.
    "sofa": (500.0, 1400.0, "z",
             "knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md:36,48 "
             "(seat 400-450 mm, and a sofa's `h` is the BACKREST not the seat); "
             "band spans a bench-backed modern sofa to a high-back wing"),
    "coffee_table": (200.0, 900.0, "z",
                     "knowledge/ergonomics/tv-viewing-and-furniture-dimensions"
                     ".md:39-40 (coffee table 300-460, side/end 380-480); band "
                     "widened to admit a low plinth table and a console"),
    "ottoman": (250.0, 800.0, "z",
                "knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md:36 "
                "(seat height 400-450); band spans a low pouf to a tall storage "
                "ottoman"),
    # ---------------------------------------------------------------- 08-22 --
    # A TABLE LAMP, added for the first FurniMesh ingest (ORD-2026-08-22 item 3
    # — AI photo->3D models, so the unit trap is the expected case, not the
    # rare one). Diagnosed by HEIGHT: a table lamp is a TABLETOP luminaire —
    # the canonical spec stands it on a 580 mm nightstand whose own height was
    # owner-corrected so the lamp is usable from the 600 mm mattress datum
    # (D-045), and the studio's lighting law files it in the TASK tier of the
    # three-tier scheme (render-quality.md:79), i.e. a sub-metre object on a
    # surface, never a floor fixture. Band spans a compact accent lamp to a
    # tall buffet lamp; what it is FOR is the traps: an imperial-exported
    # 600 mm lamp lands at 15.2 and a metres-as-mm one at 0.6, both decades out.
    "table_lamp": (250.0, 1100.0, "z",
                   "projects/PRJ-2026-002_c001-house/03_layout/"
                   "master-suite.CANONICAL.spec.json items[3..4] (h=580 "
                   "nightstand + dome lamp, D-045 mattress-datum usability) + "
                   "knowledge/brand-standards/render-quality.md:79 (table "
                   "lamps = task tier, a tabletop object)"),
}

# ------------------------------------------------------------ slot roles (P2h) --
# SPLIT AN ACQUIRED MESH'S MATERIAL SLOTS BY ROLE, from the geometry each slot's
# faces actually cover — never from the uploader's names (tub_chair_c's upholstery
# is called Carpet_Plush_Charcoal and is fluorescent green; a name is not evidence).
# The signed statement the split serves: "upholstery = the textile; legs = the
# bench leg tone" — and until this landed, a FORCED retint painted every non-metal
# slot, legs included (build_room._ACQUIRE_FORCE_RETINT_NOTE, the declared gap).
#
# A LEG slot is one whose faces ALL top out in the bottom LEG_TOP_FRAC of the
# model's own height AND carry a small share of its surface area. A seat cushion
# is large and reaches high; a leg is small and stays low. Both halves together,
# because each alone is wrong: area alone tags piping and buttons; height alone
# tags a low seat pan. Slots that fail either half stay UPHOLSTERY — the split
# fails toward the signed textile, which is the pre-split behaviour, so it can
# only ever improve on the forced state, never regress it.
LEG_TOP_FRAC = 0.45     # legs top out under ~45% of a chair/bench's height
LEG_AREA_MAX = 0.30     # legs + stretchers carry <= ~30% of the surface area


def slot_roles(slots, z0, z1):
    """{name: 'leg' | 'upholstery'} for {name: {'area': m2, 'top_z': m}} against
    the MODEL'S OWN z range (never per-mesh — a leg exported as its own mesh has
    a short range of its own and would read 'tall' against itself). Degenerate
    height or empty stats -> everything upholstery (fail toward the signed
    textile, loudly upstream)."""
    h = z1 - z0
    total = sum(s.get("area", 0.0) for s in slots.values())
    if h <= 1e-9 or total <= 1e-12:
        return {n: "upholstery" for n in slots}
    out = {}
    for n, s in slots.items():
        low = (s.get("top_z", z1) - z0) <= LEG_TOP_FRAC * h
        small = s.get("area", 0.0) <= LEG_AREA_MAX * total
        out[n] = "leg" if (low and small) else "upholstery"
    return out


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
    "pillow_set_lying": 0.10,     # a lying pair is flat-ish but never a billboard
    "pillow_set_standing": 0.30,  # a leaning sham group has real plan depth
    "towel_hung": 0.04,           # two plies over a bar are thin but never zero
    "towel_folded": 0.10,         # a folded stack has real plan depth
    # a dressed bed's cloth stands ~200 mm proud of a ~2 m footprint at the very
    # least (duvet loft + the turned sheet); a set that measures thinner than
    # that is a flat bedspread decal, which is the class this lane is REPLACING
    "bedding_set": 0.08,
    # a bed frame, a nightstand and a bench are all solid objects with real plan
    # depth; none of them can legitimately arrive as a billboard
    "bed_frame": 0.10,
    "whole_bed": 0.10,      # a dressed bed is a volume for the same reason
    "nightstand": 0.20,
    "bench_seat": 0.15,
    # a rug IS a plane — this class is the reason MIN_DEPTH_RATIO carries None as
    # a DECLARED value rather than treating "absent" and "exempt" as the same
    "rug": None,
    # all three are solid volumes; none can legitimately arrive as a billboard
    "sofa": 0.20,
    "coffee_table": 0.15,       # a round top on legs is thin in z, never planar
    "ottoman": 0.30,
    # a lamp's shade and base are round-ish in plan; even a slim candlestick
    # buffet lamp keeps ~1/10 of its height in depth — a flat cutout does not
    "table_lamp": 0.10,
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


def pbr_map_roles(path):
    """Which PBR map roles this asset actually carries: {role: material count}.

    WHY THIS IS A MEASUREMENT AND NOT A PREFERENCE (2026-08-10). The plan's own
    re-ranking of P2 says "acquiring pays the texture bill in the same move, because
    acquired meshes ship with 3-8 maps". Measured across both shelves, that is true of
    one and false of the other:

        Poly Haven ArmChair_01        1 material   normal 1   metallicRoughness 1
        Poly Haven Nightstand_01      1 material   normal 1   metallicRoughness 1
        3D Warehouse tub_chair_c      8 materials  normal 0   metallicRoughness 0
        3D Warehouse th_d             7 materials  normal 0   metallicRoughness 0

    A CC0 Poly Haven asset arrives as a finished PBR surface. A 3D Warehouse asset
    arrives as SHAPE with flat colours on it — which is still exactly what R8 wants
    from it (a real free-form silhouette we cannot model), but it means the surface
    has to come from our own signed materials rather than be kept.

    So an integration rule can be DERIVED instead of chosen: keep an incoming surface
    that exists, replace one that does not.
    """
    gl = _gltf_json(path)
    roles = {"base": 0, "normal": 0, "metallicRoughness": 0,
             "occlusion": 0, "emissive": 0}
    mats = gl.get("materials", []) or []
    for m in mats:
        pbr = m.get("pbrMetallicRoughness", {}) or {}
        roles["base"] += bool(pbr.get("baseColorTexture"))
        roles["metallicRoughness"] += bool(pbr.get("metallicRoughnessTexture"))
        roles["normal"] += bool(m.get("normalTexture"))
        roles["occlusion"] += bool(m.get("occlusionTexture"))
        roles["emissive"] += bool(m.get("emissiveTexture"))
    roles["materials"] = len(mats)
    return roles


def carries_a_pbr_surface(path):
    """True when the asset brings a surface worth keeping — any normal or
    metallic-roughness map. Base colour alone is a COLOUR, not a surface: it has no
    relief and no gloss variation, so keeping it buys nothing our own material does
    not do better."""
    try:
        r = pbr_map_roles(path)
    except Exception:                                       # noqa: BLE001
        return None                                         # unknown, never assumed
    return bool(r["normal"] or r["metallicRoughness"])


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
    # "maxxy" = the longest HORIZONTAL extent, for classes whose diagnostic
    # dimension is a footprint. A literal "x" or "y" band silently depends on
    # which way the uploader happened to lay the model out, so the same real
    # object passes or fails by an accident of export — and this module's whole
    # job is to make a wrong unit impossible to mistake for a right one.
    v = max(b["x_mm"], b["y_mm"]) if axis == "maxxy" else b[f"{axis}_mm"]
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


def sidecar_path(path):
    return os.path.splitext(path)[0] + ".scale.json"


def write_sidecar(path, cls):
    """Assert `path` as `cls`, write `<asset>.scale.json` beside it, return
    (ok, report). `cls=None` records BOUNDS ONLY and says in the file that the
    unit is not asserted — "no class named" and "in band" must never read alike.

    IT LIVES HERE, NOT IN A FETCHER, because it was in one and that is why half
    the shelf was never asserted: `warehouse.py` wrote a sidecar on every fetch
    and `assets.py` (Poly Haven, the COMMITTED shelf) had no such line, so
    thirteen assets sat unasserted for six weeks while the rule read as enforced.
    A step that only happens if each downloader remembers it is not a step.
    """
    try:
        if cls:
            ok, rep = assert_scale(path, cls)
        else:
            ok, rep = None, {
                "file": os.path.basename(path), "class": None,
                "bbox_mm": {k: round(v, 1) for k, v in bounds_mm(path).items()
                            if k != "prims"},
                "ok": None,
                "note": "NO CLASS GIVEN — bounds recorded, unit NOT asserted. "
                        "Nothing may consume this until a class is named."}
    except (KeyError, ValueError) as e:
        ok, rep = False, {"file": os.path.basename(path), "class": cls,
                          "ok": False, "error": str(e)}
    with open(sidecar_path(path), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1, ensure_ascii=False)
    return ok, rep


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    write = "--sidecar" in argv
    argv = [a for a in argv if a != "--sidecar"]
    if len(argv) < 2:
        print("usage: asset_scale.py [--sidecar] <file.glb> <class>\n"
              "  --sidecar  also write <asset>.scale.json beside the file\n"
              "  classes: " + ", ".join(sorted(BANDS)))
        return 2
    try:
        if write:
            ok, rep = write_sidecar(argv[0], argv[1])
            if ok is False and "error" in rep:
                raise ValueError(rep["error"])
        else:
            ok, rep = assert_scale(argv[0], argv[1])
    except (KeyError, ValueError) as e:
        print(f"SCALE ASSERTION FAILED: {e}")
        return 1
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if write:
        print(f"  scale sidecar -> {os.path.basename(sidecar_path(argv[0]))}")
    print("SCALE ASSERTED" if ok else "SCALE REFUSED — do not let this reach a spec")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
