"""WHOLE-BED AUDITION BENCH — stage each whole-bed candidate in the REAL room and
measure it there, before any of them costs a build round.

Run:  blender -b <built>.blend --python wholebed_bench.py -- \
          <cache_dir> <out_dir> <fit_x_mm,fit_y_mm,fit_w_mm,fit_d_mm> slug[,slug...]

WHAT IT DOES per candidate, in the audition order (rules in wholebed_rules.py, pure):
reopen the built .blend -> read the fineness control (before anything is deleted)
-> DELETE our bed except the sheet-drawn headboard (R12: SR-18 stays built) -> import
the candidate -> assert a unit factor (never assumed, R8) -> pick the bed anchor and
strip scenery/neighbours geometrically (never by name, R9b) -> resolve the head end
from the candidate's own geometry and turn it EAST -> delete its separable own
headboard (fused = recorded, verdict fails it) -> uniform scale <= 1.0 against the
drawn footprint -> place by contact: head face butts the built headboard band, plan
centred on the drawn rect, rest on the floor (derived, never typed — R9) -> ray
measurements on the STAGED result -> one quick render from the room's own camera.

The render is the audition's product; the numbers stop the eye wasting time on
candidates that cannot fit (the owner's practitioner-rung split, same as
bedcloth_bench). Nothing here is a gate: rows and renders go to <out_dir> and the
verdict field says which hard filters a candidate failed.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedcloth_fit as bcf  # noqa: E402  (control_edges, edge_mm — the shared metric)
import mesh_import as MI    # noqa: E402  (one dispatch, all formats — never gltf-only)
import wholebed_rules as R  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE, OUT = argv[0], argv[1]
FIT = [float(v) / 1000.0 for v in argv[2].split(",")]  # x, y, w, d in m
SLUGS = [s for s in argv[3].split(",") if s]
os.makedirs(OUT, exist_ok=True)
BLEND = bpy.data.filepath  # the file blender opened; reopened per candidate

FX0, FY0, FW, FD = FIT
FX1, FY1 = FX0 + FW, FY0 + FD
# The head face the frame butts against: the sheet-drawn headboard band's WEST face,
# derived from the built band in the scene (never typed here).
HEAD_GAP = 0.003


def world_bbox(ob):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
    return tuple(lo), tuple(hi)


def part_dict(ob):
    lo, hi = world_bbox(ob)
    try:
        ob.data.calc_loop_triangles()
        tris = len(ob.data.loop_triangles)
    except Exception:
        tris = 0
    return {"name": ob.name, "lo": lo, "hi": hi, "tris": tris, "_ob": ob}


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def delete(objs):
    for o in objs:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass


def bvh_of(parts):
    import bmesh
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for p in parts:
        ob = p["_ob"]
        m = ob.to_mesh()
        m.transform(ob.matrix_world)
        bm.from_mesh(m)
        ob.to_mesh_clear()
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def top_samples(tree, x0, x1, y0, y1, n=24, z_from=3.0):
    out = []
    for i in range(n):
        for j in range(n):
            x = x0 + (i + 0.5) * (x1 - x0) / n
            y = y0 + (j + 0.5) * (y1 - y0) / n
            hit = tree.ray_cast(Vector((x, y, z_from)), Vector((0, 0, -1)), 6.0)
            if hit[0] is not None:
                out.append((x, y, hit[0].z))
    return out


def flank_hits(tree, plane_z, depth):
    """For each of the 3 exposed flanks (S, W-foot, N), the fraction of 9 inward
    rays at plane_z - depth that meet cloth/geometry within 0.12 m of the face."""
    z = plane_z - depth
    res = {}
    edges = {
        "S": [((FX0 + (i + 0.5) * FW / 9.0), FY0 - 0.06, (0, 1, 0)) for i in range(9)],
        "N": [((FX0 + (i + 0.5) * FW / 9.0), FY1 + 0.06, (0, -1, 0)) for i in range(9)],
        "W": [((FX0 - 0.06), FY0 + (i + 0.5) * FD / 9.0, (1, 0, 0)) for i in range(9)],
    }
    for tag, rays in edges.items():
        n = 0
        for ox, oy, d in rays:
            hit = tree.ray_cast(Vector((ox, oy, z)), Vector(d), 0.12)
            if hit[0] is not None:
                n += 1
        res[tag] = n / 9.0
    return res


def stage_one(slug):
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    row = {"slug": slug}

    # fineness control BEFORE anything is deleted (bedcloth_bench order)
    try:
        control = bcf.control_edges()
        row["control_edge_mm"] = round(max(control.values()), 2) if control else None
    except Exception as e:
        row["control_edge_mm"] = None
        row["control_error"] = f"{type(e).__name__}: {e}"

    # the built headboard band the frame butts against (derived from the scene)
    hb = bpy.data.objects.get("bed__headboard")
    if hb is None:
        row["reject"] = "built scene has no bed__headboard — wrong blend"
        return row
    hb_lo, hb_hi = world_bbox(hb)
    head_face_x = hb_lo[0] - HEAD_GAP

    # delete our bed except the sheet-drawn headboard band (R12)
    ours = [o for o in mesh_objects()
            if o.name.startswith("bed__") and not o.name.startswith("bed__headboard")]
    row["ours_removed"] = len(ours)
    delete(ours)

    # import — any format mesh_import knows, best first (never gltf-only)
    d = os.path.join(CACHE, slug)
    models = MI.model_files(d)
    if not models:
        row["reject"] = "no importable model in cache dir"
        return row
    try:
        new = MI.import_file(os.path.join(d, models[0]))
    except Exception as e:
        row["reject"] = f"import failed: {type(e).__name__}: {e}"
        return row
    for o in new:
        o["_wb_cand"] = True
    new_mesh = [o for o in new if o.type == "MESH"]
    if not new_mesh:
        row["reject"] = "import produced no meshes"
        delete(new)
        return row

    def cand_roots():
        return [o for o in bpy.data.objects if o.get("_wb_cand") and o.parent is None]

    def cand_parts():
        bpy.context.view_layer.update()
        return [part_dict(o) for o in bpy.data.objects
                if o.get("_wb_cand") and o.type == "MESH"]

    parts = cand_parts()

    # unit factor — asserted, never assumed
    f, why = R.unit_factor(parts, drawn_long_m=FD)
    row["unit_factor"] = f
    row["unit_note"] = why
    if f is None:
        row["reject"] = f"scale unresolvable: {why}"
        delete(new)
        return row
    if f != 1.0:
        for o in cand_roots():
            o.scale = tuple(s * f for s in o.scale)
        parts = cand_parts()

    anchor = R.pick_anchor(parts, drawn_plan_m2=FW * FD)
    row["anchor_found"] = anchor is not None
    if anchor is None:
        row["reject"] = "no bed-scale anchor part"
        delete(new)
        return row
    row["anchor"] = {"name": anchor["name"], "size_mm": [round((anchor["hi"][i] - anchor["lo"][i]) * 1000) for i in range(3)]}

    keep, dropped = R.strip(parts, anchor)
    row["stripped"] = [{"name": p["name"], "why": w} for p, w in dropped]
    delete([p["_ob"] for p, _ in dropped])
    keep = cand_parts()

    # head end from the candidate's own geometry, on both axes
    cand = {"x": R.head_end(keep, axis=0), "y": R.head_end(keep, axis=1)}
    lo0 = min(p["lo"][0] for p in keep); hi0 = max(p["hi"][0] for p in keep)
    lo1 = min(p["lo"][1] for p in keep); hi1 = max(p["hi"][1] for p in keep)
    span = {"x": hi0 - lo0, "y": hi1 - lo1}
    # prefer the axis that has a resolved head; ties -> longer axis
    axis = None
    if cand["x"] and not cand["y"]:
        axis = "x"
    elif cand["y"] and not cand["x"]:
        axis = "y"
    elif cand["x"] and cand["y"]:
        axis = "x" if span["x"] >= span["y"] else "y"
    if axis is None:
        row["orientation"] = "unresolved"
        rot_z = 0.0
    else:
        end = cand[axis]
        row["orientation"] = f"head at {axis}-{end}"
        # rotate so the head lands at +x (east)
        if axis == "x":
            rot_z = 0.0 if end == "hi" else math.pi
        else:
            rot_z = -math.pi / 2 if end == "hi" else math.pi / 2
    if rot_z:
        import mathutils
        piv = Vector(((lo0 + hi0) / 2, (lo1 + hi1) / 2, 0))
        rot = mathutils.Matrix.Rotation(rot_z, 4, "Z")
        for o in cand_roots():
            o.matrix_world = mathutils.Matrix.Translation(piv) @ rot @ mathutils.Matrix.Translation(-piv) @ o.matrix_world
        keep = cand_parts()

    # sleeping plane from the candidate's own top surface (central 50% plan)
    tree = bvh_of(keep)
    lo0 = min(p["lo"][0] for p in keep); hi0 = max(p["hi"][0] for p in keep)
    lo1 = min(p["lo"][1] for p in keep); hi1 = max(p["hi"][1] for p in keep)
    cx0 = lo0 + 0.25 * (hi0 - lo0); cx1 = hi0 - 0.25 * (hi0 - lo0)
    cy0 = lo1 + 0.25 * (hi1 - lo1); cy1 = hi1 - 0.25 * (hi1 - lo1)
    samples = top_samples(tree, cx0, cx1, cy0, cy1, n=16)
    plane = R.sleeping_plane([s[2] for s in samples])
    if plane is None:
        row["reject"] = "no top surface found by ray"
        delete(new)
        return row

    # separable own headboard out; fused recorded
    hb_parts, fused = R.headboard_parts(keep, plane, head_x=hi0, head="hi")
    row["own_headboard_removed"] = [p["name"] for p in hb_parts]
    row["headboard_fused"] = fused
    delete([p["_ob"] for p in hb_parts])
    keep = cand_parts()
    if not keep:
        row["reject"] = "nothing left after headboard strip"
        return row

    # scale against the drawn footprint (never stretch)
    lo0 = min(p["lo"][0] for p in keep); hi0 = max(p["hi"][0] for p in keep)
    lo1 = min(p["lo"][1] for p in keep); hi1 = max(p["hi"][1] for p in keep)
    s, fill_l, fill_w = R.plan_scale_whole(hi0 - lo0, hi1 - lo1, FW, FD)
    row["scale"] = round(s, 4) if s else None
    row["fill_len"], row["fill_w"] = round(fill_l, 3), round(fill_w, 3)
    if s and abs(s - 1.0) > 1e-9:
        import mathutils
        piv = Vector(((lo0 + hi0) / 2, (lo1 + hi1) / 2, 0))
        m = mathutils.Matrix.Translation(piv) @ mathutils.Matrix.Scale(s, 4) @ mathutils.Matrix.Translation(-piv)
        for o in cand_roots():
            o.matrix_world = m @ o.matrix_world
        keep = cand_parts()
        lo0 = min(p["lo"][0] for p in keep); hi0 = max(p["hi"][0] for p in keep)
        lo1 = min(p["lo"][1] for p in keep); hi1 = max(p["hi"][1] for p in keep)

    # place by contact: head butts the band, centre on drawn rect, rest on floor
    min_z = min(p["lo"][2] for p in keep)
    dx = head_face_x - hi0
    dy = ((FY0 + FY1) / 2) - ((lo1 + hi1) / 2)
    dz = -min_z
    for o in cand_roots():
        o.matrix_world.translation += Vector((dx, dy, dz))
    keep = cand_parts()

    # measurements on the staged result
    tree = bvh_of(keep)
    samples = top_samples(tree, FX0 + 0.25 * FW, FX1 - 0.25 * FW,
                          FY0 + 0.25 * FD, FY1 - 0.25 * FD, n=16)
    zs = sorted(s2[2] for s2 in samples)
    plane = R.sleeping_plane(zs)
    row["plane_mm"] = round(plane * 1000, 1) if plane else None
    if zs:
        p90 = zs[int(0.9 * (len(zs) - 1))]; p10 = zs[int(0.1 * (len(zs) - 1))]
        row["relief_mm"] = round((p90 - p10) * 1000, 1)
    row["flanks"] = {f"d{int(d*1000)}": flank_hits(tree, plane, d)
                     for d in (0.05, 0.15, 0.25)} if plane else None
    row["foot_over_plane_m"] = round(R.foot_over_plane(keep, plane, foot_x=FX0, head="hi"), 3) if plane else None

    # the made-bed field vs the ink (P2r-53, ORD-2026-08-18-bed-too-small): the
    # soft mass that visually IS the bed must reach the drawn rectangle. The
    # owner failed a staged winner whose mattress measured 0.58 of the drawn
    # width while every green rung measured something else; verdict() now
    # refuses a row without these keys, so an old ledger can never pass again.
    anchor_staged = next((p for p in keep
                          if p["name"] == row["anchor"]["name"]), None)
    if anchor_staged is not None:
        fparts = R.made_field(keep, anchor_staged)
        ffl, ffw = R.field_fill(fparts, fit_len=FW, fit_w=FD, axis_len=0)
        row["field_fill_len"], row["field_fill_w"] = round(ffl, 3), round(ffw, 3)
        row["field_parts"] = [p["name"] for p in fparts]
        if fparts:
            row["field_mm"] = [
                round((max(p["hi"][0] for p in fparts)
                       - min(p["lo"][0] for p in fparts)) * 1000),
                round((max(p["hi"][1] for p in fparts)
                       - min(p["lo"][1] for p in fparts)) * 1000)]

    # fineness: the part owning the most top samples is the visible bedding
    if plane and samples:
        # per-part: bbox containment of top samples as the cheap owner test
        counts = {}
        for p2 in keep:
            n = sum(1 for sx, sy, sz in samples
                    if p2["lo"][0] <= sx <= p2["hi"][0] and p2["lo"][1] <= sy <= p2["hi"][1]
                    and abs(sz - p2["hi"][2]) < 0.12)
            counts[p2["name"]] = n
        top_part = max(counts, key=counts.get) if counts else None
        if top_part:
            ob = bpy.data.objects.get(top_part)
            if ob is not None:
                row["cover_part"] = top_part
                row["cover_edge_mm"] = round(bcf.edge_mm(ob), 2)
    row["parts_kept"] = [{"name": p["name"],
                          "size_mm": [round((p["hi"][i] - p["lo"][i]) * 1000) for i in range(3)],
                          "tris": p["tris"]} for p in keep]
    row["tris_total"] = sum(p["tris"] for p in keep)

    ok, why = R.verdict(row)
    row["passes_hard_filters"] = ok
    row["filter_fails"] = why

    # the audition's product: one quick frame from the room's own camera (R5)
    scene = bpy.context.scene
    scene.render.resolution_percentage = 50
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = 48
    # pipeline law: log engine/device/samples so a silent CPU fallback is caught
    dev = getattr(scene.cycles, "device", "?") if scene.render.engine == "CYCLES" else "-"
    print(f"WHOLEBED render engine={scene.render.engine} device={dev} "
          f"samples={getattr(scene.cycles, 'samples', '-')} res%={scene.render.resolution_percentage}",
          flush=True)
    scene.render.filepath = os.path.join(OUT, f"{slug}_eye_ql.png")
    try:
        bpy.ops.render.render(write_still=True)
        row["render"] = scene.render.filepath
    except Exception as e:
        row["render_error"] = f"{type(e).__name__}: {e}"
    return row


def main():
    rows = []
    for slug in SLUGS:
        print(f"WHOLEBED staging {slug} ...", flush=True)
        try:
            row = stage_one(slug)
        except Exception as e:  # a candidate must never kill the audition
            import traceback
            row = {"slug": slug, "reject": f"CRASH {type(e).__name__}: {e}",
                   "trace": traceback.format_exc()[-2000:]}
        row.pop("_ob", None)
        rows.append(row)
        status = row.get("reject") or ("PASS" if row.get("passes_hard_filters")
                                       else "; ".join(row.get("filter_fails", [])) or "?")
        print(f"WHOLEBED {slug:16s} -> {status}", flush=True)
    with open(os.path.join(OUT, "wholebed_bench.json"), "w", encoding="utf-8") as fh:
        json.dump({"blend": BLEND, "fit_rect_mm": [v * 1000 for v in FIT], "rows": rows},
                  fh, indent=1, default=lambda o: None)
    print(f"WHOLEBED BENCH COMPLETE {sum(1 for r in rows if r.get('passes_hard_filters'))}"
          f"/{len(rows)} pass hard filters", flush=True)


main()
