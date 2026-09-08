"""STUDY-D17 (2026-09-02) cushion/throw study — the reproduction recipe for every number in
knowledge/_inbox/model-study/2026-09-02-cushions.md. Pure Python, no bpy: reads the probe dumps
in assets/shared/blenderkit/_study/ and writes qa/blenderkit-study-cushions.json.

THE QUESTION THIS UNIT WAS SET (curriculum exam, STUDY-D17-cushions): knife-edge vs box-edge
construction, and the stacking/rotation numbers of pro cushions against the ones in our frame.

IT TOOK TWO CORPORA, AND THE SECOND ONE IS THE POINT. The six assets fetched for this unit are
PRODUCT SHOTS: every one sits at the origin with rot (0,0,0), so not one of them can answer a
question about POSE. Arrangement is not a property of a product; it is a property of a STAGED
SCENE. So the pose half is measured on the made-bed corpus already on disk from STUDY-D11
(free, already probed), and the construction half on today's fetch. Reading pose off a product
shot would have produced "every pro cushion is axis-aligned", which is a fact about catalogue
photography and nothing about how anybody styles a bed.

  CONSTRUCTION (today's six)
    edge_proxy_mm   sqrt(area / faces) * 1000, from study_probe_read — NOT bedcloth_fit.edge_mm.
    body            the mesh with the COARSEST edge_proxy. A plain fabric shell is the coarse
                    part of a cushion; piping, fringe, lace and tufting are the fine parts. The
                    rule is stated on the physics rather than on a threshold picked to fit.
                    `body_is_a_tie` flags an EXACT tie of the 2-dp edge proxies, and it does NOT
                    fire on c4450c29 (7.71 vs 7.69) — an earlier version of this docstring and the
                    note both said it did. What actually protects that asset is the edge_spread
                    rule below: it is two whole pillows, not a pillow and its trim.
    edge_spread     coarsest edge_proxy / finest, across the asset's meshes. 1.0 = the asset is
                    modelled at one resolution.
    face_area_mm2   p10/p50/p90 of the face areas INSIDE one mesh, plus p90_over_p10 and cv.
                    Added in round 2 because the note concluded "we spread polygons evenly
                    and the pros concentrate theirs" from a single MEAN face size, and a
                    mean cannot see a distribution. It is now measured rather than inferred:
                    the bought cushion mass reads p90/p10 = 1.0 (cv 0.088) and the three pro
                    shells read 24.3, 870.8 and 28,339.6. Absent on any dump probed before
                    2026-09-02 — absent means NOT MEASURED.
    per_slot        faces and WORLD area per material slot, from the probe. Added to the probe
                    during this unit: the dump used to record which materials an object
                    DECLARES and never which faces WEAR them, and those are different claims.
                    A dump probed before 2026-09-02 has no `per_slot` key at all — absent
                    means NOT MEASURED, never zero faces.
    detail_vert_share   verts NOT in the body / total verts. REPORTED ONLY when edge_spread
                    >= 2.0, because below that the asset is modelled at one resolution and
                    "everything but the body" is not trim — c4450c29 is two whole pillows at
                    7.69 and 7.71 mm, and calling the second one 63.2% detail was wrong.

  ARRANGEMENT (the STUDY-D11 made-bed corpus)
    lean_deg        the angle between the object's own +Z and world +Z, from rot_deg via a real
                    rotation matrix — not "the x euler", which is only the same number while the
                    other two axes are zero (Bed-Pillow.001 is (45,0,-9) and they are not).
                    IT IS BLIND IN ONE DIRECTION, AND THE CORPUS CONTAINS THAT CASE: it reads
                    the OBJECT TRANSFORM, so a pillow stood upright by rotating its MESH DATA
                    scores lean 0.0 while standing on edge. The three Francesca pillows in
                    62253e5c are exactly that — local dims 244x595x512, lean 0.0, upright.
    z_rank          which of the three WORLD extents the vertical one is: 1 = z is the largest,
                    3 = z is the smallest. Transform-free, so it catches the baked pose that
                    lean_deg cannot. A cushion lying flat ranks 3; one on edge ranks 1 or 2.
    presents_mm     the world-space z extent, i.e. what the pillow is actually tall in the scene
                    after being posed. This is the number a builder has to reproduce; dims_mm is
                    the LOCAL box and stays put when an object is rotated.
    overlap_mm      pairwise overlap of world bboxes, reported on BOTH plan axes and named for
                    what each one is. THE FIRST VERSION CALLED THE LONGER PLAN AXIS THE "WIDTH",
                    which is the D16 fill bug repeating one unit later: on a wardrobe the longer
                    plan axis IS the width, but on a BED it is the LENGTH (ba112721 is 1529 wide
                    x 2063 long), so "overlap across the width" was measuring front-to-back
                    overlap. A rule carried from another object class is a guess about this one.
                      overlap_long_mm   along the bed's long axis = one pillow in FRONT of another
                      overlap_short_mm  across the bed = pillows SIDE BY SIDE
                    AND THE LABELS ARE ONLY WORTH HAVING WHEN THE PLAN SAYS WHICH IS WHICH. The
                    axes come from the union of the whole set's world boxes, which on a staged
                    scene includes rugs, throws and side tables, so it is often nearly square:
                    62253e5c is 2434x2245 (1.08) and afcfd29e 2287x2191 (1.04). Below
                    PLAN_DECISIVE the assignment is a coin-flip and `plan_is_near_tie` is set —
                    the same failure as D16's tied rotation base, caught here before it was
                    written into prose rather than after.
                    The vault says in its own words there is no row for lean angle or overlap
                    (knowledge/ searched 2026-09-02), so these are new.

WHAT dims_mm IS, because two objects here disagree while sharing a mesh: `ob.dimensions` is the
LOCAL bounding box times scale — rotation never touches it. The Francesca pillow is 661x658x178
as a product and 244x595x512 inside 62253e5c at 89,262 verts BOTH TIMES, scale 1.0 both times.
Identical topology with a different local box means the bed's author rotated the MESH DATA and
then rotated the OBJECT as well. So the two rows are the same asset, and neither dims_mm is
wrong; they are answers to different questions. Comparisons here use world_bbox_mm.
"""
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_probe_read import REPO, load, meshes, edge_proxy_mm  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(REPO, "qa", "blenderkit-study-cushions.json")

# fetched for this unit, 2026-09-02. tier and the class asserted at fetch time.
PRODUCTS = {
    "e5fc6314": ("3 cushion set", "free", "pillow_set_standing",
                 "the free tier's own panel-passing piece from STUDY-D13 — the free/paid "
                 "comparison inside the class, not a filler"),
    "c4450c29": ("Fabric Cushions", "full_plan", "pillow_set_lying", "a pair, two sizes"),
    "aac13b32": ("Throw Pillow", "full_plan", "pillow_set_lying",
                 "the densest single cushion on the shelf at 396k faces"),
    "402c662f": ("Francesca Hand Embroidered Throw Pillow", "full_plan", "pillow_set_lying",
                 "square, embroidered — and the SAME asset that appears posed inside the "
                 "made-bed set 62253e5c, so product and pose can be read off one mesh"),
    "da65b0fa": ("Corindi Pillow", "full_plan", "pillow_set_lying",
                 "310x303x292 — nearly cubic, the box-edge end of the class"),
    "7ca290af": ("The Needle Lace Handcraft Pillow", "full_plan", "pillow_set_lying",
                 "lace trim as its own mesh"),
}

# the STUDY-D11 made-bed corpus, re-read here for POSE. No new download.
STAGED = ["ee42aa0e", "62253e5c", "afcfd29e", "1f83314d", "ba112721", "a682383b",
          "e2418055", "81d895fd"]
# NAME IS THE ONLY IDENTIFIER AVAILABLE AND IT IS NOT RELIABLE. e2418055 — the bed in our
# own frame — ships its cushions as an object called "Cusions", and ee42aa0e's headboard
# cushions are called Bed.008 / Bed.009 (STUDY-D11 ROLE_DISPUTES). "cusion" is in the list
# because that misspelling was FOUND, not guessed; Bed.008 is unreachable by any word rule.
# So every count here is a FLOOR, never a census, and each set reports what it could not
# match so the reader can see the size of the hole.
PILLOW_WORDS = ("pillow", "cushion", "cusion", "sham", "bolster")

OURS = ("bed__headset0__acq1", "deco_bedthrow__acq0")

# long/short axis is only a real distinction when the set's plan is this much longer than
# it is wide. 1.15 is a declared assumption, and every set records its own ratio so the
# reader can move it and see which rows survive.
PLAN_DECISIVE = 1.15

# knowledge/ rows found 2026-09-02 (the vault search that also reported the two gaps this
# unit fills). Face sizes only — the vault has no scatter-cushion face row, these are the
# sham/pillow chart it does have.
VAULT_FACES_MM = {
    "euro_sham": (686, 686, "knowledge/_inbox/dr-made-bed-grammar-2026-08-17.md L90,L102 (27x27 in)"),
    "standard_sham": (533, 686, "knowledge/_inbox/dr-made-bed-grammar-2026-08-17.md L92 (21x27 in)"),
    "boudoir": (305, 406, "knowledge/_inbox/dr-made-bed-grammar-2026-08-17.md L93,L104 (12x16 in)"),
    "king_pillow": (500, 900, "knowledge/_inbox/dr-made-bed-grammar-2026-08-17.md L103,L166"),
    "bolster": (230, 800, "knowledge/_inbox/dr-made-bed-grammar-2026-08-17.md L163"),
}


def _is_pillow(name):
    n = name.lower()
    return any(w in n for w in PILLOW_WORDS)


def _lean_deg(rot_deg):
    """angle between the object's own +Z and world +Z, from an XYZ euler in degrees."""
    rx, ry, rz = (math.radians(a) for a in rot_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    # R = Rz @ Ry @ Rx (Blender XYZ euler); the object's local +Z maps to R[:,2]
    zx = cz * sy * cx + sz * sx
    zy = sz * sy * cx - cz * sx
    zz = cy * cx
    n = math.sqrt(zx * zx + zy * zy + zz * zz) or 1.0
    return round(math.degrees(math.acos(max(-1.0, min(1.0, zz / n)))), 1)


def _slots(o):
    """per-slot faces/area with each slot's share of the object's own area. Returns None
    when the dump predates the probe change — absent is NOT MEASURED, not zero."""
    ps = o["mesh"].get("per_slot")
    if ps is None:
        return None
    tot = sum(q["area_m2"] for q in ps) or 1.0
    return [{**q, "area_share": round(q["area_m2"] / tot, 4)} for q in ps]


def _rank_of_z(ext):
    """1 = z is the largest of the three world extents, 3 = the smallest. Strict, on the
    raw floats — no rounding, so no invented ties."""
    return sorted(ext, reverse=True).index(ext[2]) + 1


def _z_near_tie(ext, tol_mm=2.0):
    """True when z is within tol of another extent, i.e. the rank is not a real signal.
    Reported beside the rank rather than folded into it, so a reader sees WHICH rows the
    metric cannot speak about instead of getting a confident number for all of them."""
    z = ext[2]
    return any(abs(z - e) <= tol_mm for i, e in enumerate(ext) if i != 2)


def _wb(o):
    return o.get("world_bbox_mm")


def _union_dims(ms):
    """the asset's own size = the union of its meshes' world boxes. Taking it from the
    densest mesh reported a 641x136x20 FRINGE STRIP as the size of aac13b32."""
    ws = [_wb(o) for o in ms if _wb(o)]
    if not ws:
        return None
    return [round(max(w["max"][i] for w in ws) - min(w["min"][i] for w in ws))
            for i in range(3)]


def _overlap(a, b, i):
    lo = max(a["min"][i], b["min"][i])
    hi = min(a["max"][i], b["max"][i])
    return round(hi - lo) if hi > lo else 0


def construction():
    out = {}
    for pre, (label, tier, cls, why) in PRODUCTS.items():
        fn, d = load(pre)
        ms = meshes(d)
        rows = []
        for o in ms:
            rows.append({"name": o["name"], "dims_mm": [round(x) for x in o["dims_mm"]],
                         "rot_deg": [round(x) for x in o.get("rot_deg", [0, 0, 0])],
                         "verts": o["mesh"]["verts"], "faces": o["mesh"]["polys"],
                         "edge_proxy_mm": round(edge_proxy_mm(o), 2),
                         "materials": o.get("materials"),
                         "per_slot": _slots(o),
                         "face_area_mm2": o["mesh"].get("face_area_mm2")})
        edges = [r["edge_proxy_mm"] for r in rows if r["edge_proxy_mm"] > 0]
        coarse = max(edges) if edges else 0.0
        fine = min(edges) if edges else 0.0
        tie = sum(1 for e in edges if e == coarse) > 1
        body = max(rows, key=lambda r: r["edge_proxy_mm"]) if rows else None
        tot_v = sum(r["verts"] for r in rows) or 1
        out[pre] = {
            "file": fn, "label": label, "tier": tier, "asserted_class": cls, "why_in_corpus": why,
            "n_mesh": len(ms), "n_materials": len(d["materials"]),
            "n_images": len(d.get("images", [])),
            "asset_dims_mm": _union_dims(ms),
            "objects": sorted(rows, key=lambda r: -r["verts"]),
            "body_name": body["name"] if body else None,
            "body_edge_proxy_mm": coarse, "finest_edge_proxy_mm": fine,
            "body_is_a_tie": tie,
            "edge_spread": round(coarse / fine, 1) if fine else None,
            "detail_vert_share": (round((tot_v - (body["verts"] if body else 0)) / tot_v, 4)
                                  if (fine and coarse / fine >= 2.0) else None),
            "total_verts": tot_v,
        }
    return out


def arrangement():
    out = {}
    for pre in STAGED:
        try:
            fn, d = load(pre)
        except Exception as e:                                    # noqa: BLE001
            out[pre] = {"error": str(e)}
            continue
        ms = meshes(d)
        pil = [o for o in ms if _is_pillow(o["name"]) and _wb(o)]
        rows = []
        for o in pil:
            w = _wb(o)
            rows.append({
                "name": o["name"],
                "dims_local_mm": [round(x) for x in o["dims_mm"]],
                "rot_deg": [round(x) for x in o.get("rot_deg", [0, 0, 0])],
                "lean_deg": _lean_deg(o.get("rot_deg", [0, 0, 0])),
                "presents_mm": round(w["max"][2] - w["min"][2]),
                "world_extents_mm": [round(w["max"][i] - w["min"][i]) for i in range(3)],
                # RANKED ON THE UNROUNDED EXTENTS. The first version rounded to whole mm
                # BEFORE sorting and then used list.index(), which returns the first of two
                # now-equal entries — so four identically-posed pillows in ba112721 came out
                # 3,3,2,2 while z is in fact the strict minimum on all four. The note then
                # explained that flip as "the two spans differ by a few mm", which its own
                # rows refute (two pillows with the SAME 0.6 mm gap landed on opposite ranks;
                # what decided it was which side of .5 each fraction fell on). An instrument
                # that rounds before it compares INVENTS ties the geometry does not have.
                "z_rank": _rank_of_z([w["max"][i] - w["min"][i] for i in range(3)]),
                "z_rank_is_near_tie": _z_near_tie([w["max"][i] - w["min"][i]
                                                   for i in range(3)]),
                "z_bottom_mm": round(w["min"][2]), "z_top_mm": round(w["max"][2]),
                "verts": o["mesh"]["verts"],
                "edge_proxy_mm": round(edge_proxy_mm(o), 2),
            })
        # a bed's LONGER plan axis is its LENGTH, not its width — see the docstring.
        allw = [_wb(o) for o in ms if _wb(o)]
        _plan = ([round(max(w["max"][i] for w in allw) - min(w["min"][i] for w in allw))
                  for i in range(2)] if allw else None)
        _ratio = (round(max(_plan) / max(min(_plan), 1), 2) if _plan else None)
        pairs = []
        li = si = None
        if allw and len(pil) > 1:
            ex = [max(w["max"][i] for w in allw) - min(w["min"][i] for w in allw)
                  for i in range(2)]
            li = 0 if ex[0] >= ex[1] else 1
            si = 1 - li
            for i in range(len(pil)):
                for j in range(i + 1, len(pil)):
                    ol = _overlap(_wb(pil[i]), _wb(pil[j]), li)
                    os_ = _overlap(_wb(pil[i]), _wb(pil[j]), si)
                    if ol or os_:
                        # each overlap as a FRACTION of the smaller pillow's own extent on
                        # that axis, so "how much of a pillow is hidden" is answerable
                        el = min(_wb(pil[k])["max"][li] - _wb(pil[k])["min"][li]
                                 for k in (i, j)) or 1
                        es = min(_wb(pil[k])["max"][si] - _wb(pil[k])["min"][si]
                                 for k in (i, j)) or 1
                        pairs.append({"a": pil[i]["name"], "b": pil[j]["name"],
                                      "overlap_long_mm": ol, "overlap_short_mm": os_,
                                      "long_frac": round(ol / el, 2),
                                      "short_frac": round(os_ / es, 2)})
        leans = sorted({r["lean_deg"] for r in rows})
        out[pre] = {
            "file": fn, "n_mesh": len(ms), "n_pillow_named": len(pil),
            "long_axis": (None if li is None else "xy"[li]),
            "short_axis": (None if si is None else "xy"[si]),
            "bed_plan_mm": _plan,
            "plan_ratio": _ratio,
            "plan_is_near_tie": (_ratio is not None and _ratio < PLAN_DECISIVE),
            "pillows": sorted(rows, key=lambda r: r["z_bottom_mm"]),
            "distinct_lean_deg": leans,
            "leaning": [r["name"] for r in rows if r["lean_deg"] > 1],
            "overlaps": sorted(pairs, key=lambda p: -(p["overlap_long_mm"]
                                                      + p["overlap_short_mm"]))[:8],
            "unmatched_mesh_names": sorted(o["name"] for o in ms if not _is_pillow(o["name"])),
            "all_mesh_names": sorted(o["name"] for o in ms),
        }
    return out


def ours():
    _, d = load("_ours_p2r91")
    ms = meshes(d)
    rows = []
    for o in ms:
        if o["name"] in OURS:
            rows.append({"name": o["name"],
                         "dims_local_mm": [round(x) for x in o["dims_mm"]],
                         "rot_deg": [round(x) for x in o.get("rot_deg", [0, 0, 0])],
                         "lean_deg": _lean_deg(o.get("rot_deg", [0, 0, 0])),
                         "verts": o["mesh"]["verts"],
                         "edge_proxy_mm": round(edge_proxy_mm(o), 2),
                         "materials": o.get("materials"),
                         "n_materials_on_this_object": len(o.get("materials") or []),
                         "per_slot": _slots(o),
                         "face_area_mm2": o["mesh"].get("face_area_mm2")})
    named = Counter()
    for o in ms:
        if _is_pillow(o["name"]):
            named[o["name"]] += 1
    src = None
    try:
        _, sd = load("e2418055")
        c = [x for x in meshes(sd) if x["name"].strip() == "Cusions"]
        if c:
            src = {"asset": "e2418055", "name": c[0]["name"],
                   "dims_mm": [round(x) for x in c[0]["dims_mm"]],
                   "verts": c[0]["mesh"]["verts"], "quads": c[0]["mesh"]["quads"],
                   "tris": c[0]["mesh"]["tris"],
                   "area_m2": c[0]["mesh"]["area_m2"],
                   "edge_proxy_mm": round(edge_proxy_mm(c[0]), 4),
                   "materials": c[0].get("materials"),
                   "per_slot": _slots(c[0]),
                   "slots_with_no_face": c[0]["mesh"].get("slots_with_no_face"),
                   "face_area_mm2": c[0]["mesh"].get("face_area_mm2"),
                   "why": ("bed__headset0__acq1 in our frame IS this object: same 137,073 verts, "
                           "same dims with axes swapped, area within 0.13%, edge_proxy 4.97 both. "
                           "Ours arrives triangulated and with every slot replaced by one "
                           "material (build_room.py:8996 replace_material=sham_mat).")}
    except Exception as e:                                            # noqa: BLE001
        src = {"error": str(e)}
    return {"objects": rows,
            "source_object": src,
            "pillow_named_objects_in_scene": sorted(named),
            "n_pillow_named": len(named),
            "note": ("the whole head-end arrangement is ONE acquired mesh with ONE material, "
                     "so it has no per-pillow pose, no per-pillow fabric and nothing to count")}


def main():
    out = {"_recipe": __doc__.strip().splitlines()[0],
           "_vault_face_sizes_mm": VAULT_FACES_MM,
           "construction": construction(),
           "arrangement": arrangement(),
           "ours": ours()}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print("== CONSTRUCTION (products fetched 2026-09-02)")
    for pre, s in out["construction"].items():
        print(f"{pre} {s['label'][:36]:36} [{s['tier']:9}] mesh={s['n_mesh']} mat={s['n_materials']} "
              f"img={s['n_images']} dims={s['asset_dims_mm']}")
        share = ("n/a — one resolution" if s["detail_vert_share"] is None
                 else f"{s['detail_vert_share']:.1%}")
        print(f"    body={s['body_name']!r} edge {s['body_edge_proxy_mm']} .. "
              f"{s['finest_edge_proxy_mm']} spread={s['edge_spread']}x "
              f"detail_verts={share} of {s['total_verts']}")
        for r in s["objects"]:
            fa = r.get("face_area_mm2") or {}
            sp = (f" p90/p10={fa['p90_over_p10']:>9.1f} cv={fa['cv']}"
                  if fa.get("p90_over_p10") is not None else "  (dispersion not measured)")
            print(f"      {r['name'][:30]:30} {str(r['dims_mm']):20} v={r['verts']:>7} "
                  f"edge={r['edge_proxy_mm']:6.2f}{sp}")

    print("\n== ARRANGEMENT (STUDY-D11 made-bed corpus, no new download)")
    for pre, s in out["arrangement"].items():
        if "error" in s:
            print(f"{pre} ERROR {s['error']}")
            continue
        print(f"{pre} mesh={s['n_mesh']} pillow-named={s['n_pillow_named']} "
              f"lean={s['distinct_lean_deg']} plan={s['bed_plan_mm']} r={s['plan_ratio']} "
              f"long={s['long_axis']} short={s['short_axis']}"
              f"{'  !! PLAN NEAR-TIE — long/short is a coin-flip' if s['plan_is_near_tie'] else ''}")
        if not s["n_pillow_named"]:
            print(f"      NO NAME MATCHED — {s['unmatched_mesh_names'][:9]}")
        for r in s["pillows"]:
            print(f"      {r['name'][:30]:30} rot={str(r['rot_deg']):16} lean={r['lean_deg']:5.1f} "
                  f"presents={r['presents_mm']:>4} zrank={r['z_rank']} "
                  f"world={str(r['world_extents_mm']):18} edge={r['edge_proxy_mm']:5.2f}")
        for q in s["overlaps"][:4]:
            print(f"      overlap {q['a'][:22]:22} x {q['b'][:22]:22} "
                  f"long={q['overlap_long_mm']:>4} ({q['long_frac']:.2f}) "
                  f"short={q['overlap_short_mm']:>4} ({q['short_frac']:.2f})")

    o = out["ours"]
    src = o.get("source_object") or {}
    if src.get("per_slot"):
        print(f"\n== SOURCE of our head set — {src['asset']} {src['name']!r} "
              f"verts={src['verts']} quads={src['quads']} area={src['area_m2']}")
        for q in src["per_slot"]:
            print(f"      slot{q['slot']} {str(q['material'])[:28]:28} faces={q['faces']:>7} "
                  f"area={q['area_m2']:.6f} ({q['area_share']:.2%})")
        print(f"      slots with no face: {src.get('slots_with_no_face')}")
        fa = src.get("face_area_mm2") or {}
        if fa.get("p90_over_p10") is not None:
            print(f"      face-area dispersion p90/p10={fa['p90_over_p10']} cv={fa['cv']} "
                  f"(p10={fa['p10']} p50={fa['p50']} p90={fa['p90']} mm2)")
    print(f"\n== OURS  pillow-named objects in the whole scene: {o['n_pillow_named']}")
    for r in o["objects"]:
        print(f"      {r['name'][:30]:30} {str(r['dims_local_mm']):20} lean={r['lean_deg']} "
              f"v={r['verts']} edge={r['edge_proxy_mm']} mats={r['materials']}")
    print("\nwrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
