#!/usr/bin/env python3
"""build_kitchen.py - the 3D Shaker workflow, stages 2-5, run for real.

    blender -b --factory-startup -P build_kitchen.py -- --stage mood --quick

STAGES, in the tutorial's own order, and the ORDER IS THE LESSON:
  blockout : geometry only, flat clay, no light decisions yet
  mood     : ONE override material + an overcast HDRI + a sun, and NOTHING else.
             Colour, exposure and shadow contrast are settled here, on grey, before a
             single texture exists.
  split    : the override divides into a handful of tonal families (lighter / white /
             black / wood / metal / plants) - still no textures.
  texture  : real maps. Reflections before colour, always.

Everything dimensional comes from ../03_blockout/room_spec.py, which is derived from the
plate through the solved camera. Nothing here types a position a contact could give.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03_blockout"))
sys.path.insert(0, HERE)
import room_spec as RS                                                  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HDRI = os.path.join(REPO, "assets", "shared", "cc0", "hdris",
                    "kloofendal_overcast_puresky_4k.hdr")

MM = 0.001
AVG_LINEAR = (0.3657, 0.2993, 0.2254)     # plate average-blur #A39583, as linear
SUN_AZIMUTH_PLAN = 21.58                  # MEASURED from the plate's floor shadows
SKIP = {}
LENS_OVERRIDE = 0.0


def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
              bpy.data.worlds, bpy.data.images, bpy.data.curves):
        for d in list(c):
            c.remove(d)


def coll(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def box(name, lo, hi, collection):
    lo = Vector([v * MM for v in lo])
    hi = Vector([v * MM for v in hi])
    me = bpy.data.meshes.new(name)
    vs = [(x, y, z) for z in (lo.z, hi.z) for y in (lo.y, hi.y) for x in (lo.x, hi.x)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def cyl(name, cx, cy, z0, z1, r, collection, verts=48):
    me = bpy.data.meshes.new(name)
    vs, fs = [], []
    for z in (z0, z1):
        for i in range(verts):
            a = 2 * math.pi * i / verts
            vs.append(((cx + r * math.cos(a)) * MM, (cy + r * math.sin(a)) * MM, z * MM))
    for i in range(verts):
        j = (i + 1) % verts
        fs.append((i, j, verts + j, verts + i))
    fs.append(tuple(range(verts)))
    fs.append(tuple(range(2 * verts - 1, verts - 1, -1)))
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def stadium(name, x0, x1, y0, y1, z0, z1, collection, seg=48, arris=0.0, na=4):
    """A prism whose PLAN is a stadium - straight sides, semicircular ends on the LONG
    axis - with the arris rounded IN THE MESH rather than by a modifier.

    The plate's island is a stadium and we were building a bevelled BOX, which is why its
    near end read as a corner in every frame this lane has produced. A bevel rounds an
    EDGE; it cannot turn a rectangle into a racetrack.

    WHY THE ARRIS IS BUILT IN. A BEVEL modifier on this shape GROWS it: measured, the AABB
    went from 1693..2943 to 1683..2953, exactly one bevel width outwards on both sides in
    plan, with Z untouched, and identically for either face winding. On a plain box the
    same modifier leaves the AABB alone, so it is the near-tangent facet junctions that do
    it. Rather than tune a modifier until a check passes, the profile is generated: rings
    of the same stadium, inset by rb*(1-sin a) at height rb*(1-cos a). The extreme ring is
    the declared box, so the AABB is exact by construction and spec_agreement keeps its
    teeth.
    """
    cx = (x0 + x1) / 2.0
    r = (x1 - x0) / 2.0
    ya, yb = y0 + r, y1 - r

    def ring(d, z):
        """the stadium inset by d, at height z. An inset stadium is another stadium."""
        rr = max(r - d, 1e-6)
        p = [(cx + rr, ya), (cx + rr, yb)]
        for i in range(1, seg // 2):
            a = math.pi * i / (seg // 2)
            p.append((cx + rr * math.cos(a), yb + rr * math.sin(a)))
        p += [(cx - rr, yb), (cx - rr, ya)]
        for i in range(1, seg // 2):
            a = math.pi + math.pi * i / (seg // 2)
            p.append((cx + rr * math.cos(a), ya + rr * math.sin(a)))
        return [(px * MM, py * MM, z * MM) for px, py in p]

    rb = min(arris, r * 0.5, (z1 - z0) * 0.45)
    levels = []
    if rb > 1e-6:
        for i in range(na + 1):                      # bottom arris
            a = math.pi / 2 * i / na
            levels.append((rb * (1 - math.sin(a)), z0 + rb * (1 - math.cos(a))))
        for i in range(na, -1, -1):                  # top arris
            a = math.pi / 2 * i / na
            levels.append((rb * (1 - math.sin(a)), z1 - rb * (1 - math.cos(a))))
    else:
        levels = [(0.0, z0), (0.0, z1)]
    rings = [ring(d, z) for d, z in levels]
    n = len(rings[0])
    vs = [v for rg in rings for v in rg]
    fs = []
    for k in range(len(rings) - 1):
        b0, b1 = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            fs.append((b0 + i, b0 + j, b1 + j, b1 + i))
    fs.append(tuple(range(n)))
    fs.append(tuple(range(len(vs) - 1, len(vs) - n - 1, -1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def tube(name, pts, r, collection, bevel_res=5):
    """A swept circle along a polyline - R8 calls this BUILD, not ACQUIRE."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r * MM
    cu.bevel_resolution = bevel_res
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1.0)
    ob = bpy.data.objects.new(name, cu)
    collection.objects.link(ob)
    return ob


def build_room():
    shell = coll("Shell")
    mill = coll("Millwork")
    loose = coll("Loose")
    ext = coll("Exterior")
    G = RS.GLASS_Y
    # the camera stands ~7.0 m off the kitchen wall and ~11.8 m down the room, so the room
    # has to be that big. The walls BEHIND the camera are modelled on purpose: the tutorial
    # says so at 06:45 - "although they are not visible in your image they still impact the
    # lighting in your scene because they reflect a lot of light".
    X1, Y1, T = RS.SHELL_X1, RS.SHELL_Y1, RS.WALL_T
    HEAD = RS.CEILING - RS.GLAZE_HEAD_T
    box("floor", (-400, G - 400, -60), (X1, Y1, 0), shell)
    box("ceiling", (-400, G - 400, RS.CEILING), (X1, Y1, RS.CEILING + 200), shell)
    box("wall_kitchen", (-T, G - 400, 0), (0, Y1, RS.CEILING), shell)
    box("wall_behind", (-T, Y1, 0), (X1, Y1 + T, RS.CEILING), shell)
    box("wall_right", (X1, G, 0), (X1 + T, Y1 + T, RS.CEILING), shell)
    # THE GLAZING SITS IN THE WALL, IT DOES NOT STRADDLE THE DATUM. Until 2026-08-29 the
    # head, the transom, the mullions and the glass were all built CENTRED on y = GLASS_Y,
    # so every one of them stood 45-60 mm proud of the wall line into the room, and the
    # glass pane's inner face was 12 mm inboard of the plane the whole room is measured
    # from. Nothing rendered wrong enough to notice; spec_agreement caught it as 12.00 mm.
    # The frame members now occupy the outboard 90 mm of the 150 mm reveal with their inner
    # faces ON the datum, and the sealed unit sits inside them.
    FD = RS.FRAME_D
    box("glazing_head", (-T, G - FD, HEAD), (X1, G, RS.CEILING), shell)
    box("glazing_transom", (-T, G - FD, RS.TRANSOM_Z - RS.TRANSOM_T / 2),
        (X1, G, RS.TRANSOM_Z + RS.TRANSOM_T / 2), shell)
    glass = box("glass", (-T, G - FD + RS.GLASS_SET, 0),
                (X1, G - FD + RS.GLASS_SET + RS.GLASS_T, HEAD), shell)
    # VERTICAL MULLIONS. Without them a 12.6 m opening throws one undifferentiated wash and
    # the floor has no pattern at all - which is exactly what the first sun renders showed.
    x = -T
    while x < X1:
        box("mullion_%d" % x, (x, G - FD, 0), (x + RS.MULLION_W, G, HEAD), shell)
        x += RS.MULLION_PITCH

    PI = RS.PLINTH_INSET
    box("bench", (0, RS.BENCH_Y0, RS.PLINTH), (RS.BENCH_DEPTH, RS.BENCH_Y1, RS.BENCH_H), mill)
    box("bench_plinth", (PI, RS.BENCH_Y0, 0),
        (RS.BENCH_DEPTH - PI, RS.BENCH_Y1, RS.PLINTH), mill)
    box("splashback", (0, RS.BENCH_Y0, RS.BENCH_H),
        (RS.SPLASH_T, RS.BENCH_Y1, RS.UPPERS_BOTTOM), mill)
    box("uppers", (0, RS.BENCH_Y0, RS.UPPERS_BOTTOM),
        (RS.UPPERS_DEPTH, RS.BENCH_Y1, RS.CEILING), mill)
    box("tall_bank", (0, RS.TALL_Y0, RS.PLINTH), (RS.TALL_DEPTH, RS.TALL_Y1, RS.CEILING), mill)
    box("tall_plinth", (PI, RS.TALL_Y0, 0),
        (RS.TALL_DEPTH - PI, RS.TALL_Y1, RS.PLINTH), mill)
    box("oven_stack", (RS.TALL_DEPTH - RS.OVEN_RECESS, RS.OVEN_Y0 + RS.OVEN_SIDE_INSET,
                       RS.OVEN_Z0),
        (RS.TALL_DEPTH + RS.OVEN_PROUD, RS.OVEN_Y1 - RS.OVEN_SIDE_INSET, RS.OVEN_Z1), mill)

    # THE ISLAND IS TWO THINGS, not one block: a travertine volume at the FAR end and a
    # cantilevered oval slab carried on two bronze drums at the NEAR end. Building it as one
    # long box is what made it read as a wall.
    #
    # REBUILT 2026-08-29. Until this edit these four statements read RS.ISL_STONE_X0 and
    # RS.DRUM_X, which room_spec.py stopped defining when the island was turned a quarter
    # turn onto its true axis. So THE BUILD SCRIPT HAD NOT IMPORTED SINCE THE FIX, and every
    # image in out/ was made by the wrong island. Nothing said so: the spec was corrected in
    # one file and the builder was a SECOND TRANSCRIPTION of the same numbers in another.
    # spec_agreement() at the bottom of this file is the answer to that - the built scene is
    # now measured against room_spec.boxes() and the render is refused when they disagree.
    box("island_stone", (RS.ISL_X0 + 140, RS.ISL_Y0, RS.PLINTH),
        (RS.ISL_X1 - 140, RS.ISL_STONE_Y1, RS.ISL_H - RS.ISL_SLAB_T), mill)
    slab = stadium("island_slab", RS.ISL_X0, RS.ISL_X1, RS.ISL_Y0, RS.ISL_Y1,
                   RS.ISL_H - RS.ISL_SLAB_T, RS.ISL_H, mill,
                   arris=RS.SLAB_BULLNOSE_R)
    for i, y in enumerate(RS.DRUM_Y):
        cyl("island_drum%d" % i, RS.ISL_CENTRE_X, y, 0, RS.ISL_H - RS.ISL_SLAB_T,
            RS.DRUM_R, mill)

    # STOOLS. Width runs along Y (the island's long axis), depth along X, and the sitter
    # faces the island - which is at a SMALLER X than the stools - so the backrest hoop is
    # the +X plane and the front legs are the -X one. The old code had width along X, which
    # was correct only while the island itself was a quarter turn out.
    for i, y in enumerate(RS.STOOL_Y):
        cx = RS.STOOL_X
        w = RS.STOOL_W / 2.0          # half width,  along Y
        d = RS.STOOL_D / 2.0          # half depth,  along X
        h = RS.STOOL_H
        s = RS.STOOL_SEAT
        back, front = cx + d * .8, cx - d * .8
        # A TUBE'S CENTRELINE IS NOT ITS SURFACE. SP01 Michelle low is 815 mm OVERALL, so
        # the hoop's apex centreline belongs at 815 - r, not at 815 - the version that put
        # it at 815 built the stool 10.72 mm too tall and spec_agreement said so on its
        # first run. Same reasoning at the seat rail; the legs are vertical, so their end
        # caps are already flat on the floor.
        r, rr = RS.STOOL_TUBE_R, RS.STOOL_RAIL_R
        apex = h - r
        hoop = [(back, y - w * .78, 0), (back, y - w * .78, s + 40),
                (back, y - w * .52, apex - 24), (back, y, apex),
                (back, y + w * .52, apex - 24), (back, y + w * .78, s + 40),
                (back, y + w * .78, 0)]
        tube("stool%d_hoop" % i, hoop, r, loose)
        for sy in (-1, 1):
            tube("stool%d_leg%d" % (i, sy), [(front, y + sy * w * .78, 0),
                                             (front, y + sy * w * .72, s)], r, loose)
            tube("stool%d_rail%d" % (i, sy), [(front, y + sy * w * .78, RS.STOOL_RAIL_Z),
                                              (back, y + sy * w * .78, RS.STOOL_RAIL_Z)],
                 rr, loose)
        box("stool%d_seat" % i, (cx - d * .84, y - w * .82, s - 14),
            (cx + d * .84, y + w * .82, s), loose)

    if not SKIP.get("sheer"):
        build_curtain(shell)
    if not SKIP.get("canopy"):
        build_canopy(ext)
    return glass


# ---------------------------------------------------------------------------------------
# THE RUNG THIS LANE DID NOT HAVE, added 2026-08-29.
#
# room_spec.py is the spec of record and this file is the builder, and for one day they
# were two independent transcriptions of the same numbers. When the island was turned onto
# its measured axis, room_spec changed and this file did not: it still asked for DRUM_X and
# ISL_STONE_X0. That is the loud version - an ImportError - and it still went a whole day
# unnoticed because nobody re-ran the build. The quiet version is worse and this repo has
# shipped it before: a builder that keeps importing while its numbers drift, so a frame is
# rendered from geometry the spec does not describe and NOTHING SAYS SO.
#
# So the check reads the BUILT SCENE, not the spec (R9b's law: a spec-side check cannot see
# an object the spec does not know about, and the file that renders is not automatically the
# file of record). Every mass room_spec.boxes() declares is located in the scene Blender is
# about to render, its world AABB measured off the evaluated mesh, and compared. It FAILS
# CLOSED - there is no flag to skip it, because an order carried out as an opt-in is an
# order that was not carried out.
#
# Two modes, and the difference is honest rather than convenient:
#   equal  - the two must be the same mass to TOL_MM. Millwork, the island, the drums.
#   inside - the built assembly must fit INSIDE the spec's envelope. A stool is seven tubes
#            and a seat; its spec box is the product's overall envelope, so equality would
#            be the wrong test and asserting it would only teach the next reader to relax
#            the tolerance until it passed.
#   plane  - only one coordinate is compared. The shell boxes are deliberately BIGGER than
#            the guide boxes (the room has to enclose a camera 11.8 m down it, and the walls
#            behind the camera are modelled on purpose), so the only thing that must agree
#            is where the surface the room is measured from actually sits.
TOL_MM = 1.0
AGREEMENT = {
    "bench":         ("bench",        "equal"),
    "splashback":    ("splashback",   "equal"),
    "uppers":        ("uppers",       "equal"),
    "tall_bank":     ("tall_bank",    "equal"),
    "island_stone":  ("island_stone", "equal"),
    "island_slab":   ("island_slab",  "equal"),
    "island_drum0":  ("drum0",        "equal"),
    "island_drum1":  ("drum1",        "equal"),
    "stool0_*":      ("stool0",       "inside"),
    "stool1_*":      ("stool1",       "inside"),
    "floor":         ("floor",        "plane:z:max"),
    "ceiling":       ("ceiling",      "plane:z:min"),
    "wall_kitchen":  ("kitchen_wall", "plane:x:max"),
    "glazing_head":  ("glazing_wall", "plane:y:max"),
    "glass":         ("glazing_wall", "inside:y"),
}


def _world_aabb(names):
    """mm, from the EVALUATED mesh - so a curve's bevel and a modifier both count."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    found = False
    for ob in bpy.data.objects:
        if not any(ob.name == n or (n.endswith("*") and ob.name.startswith(n[:-1]))
                   for n in names):
            continue
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        for v in me.vertices:
            w = ev.matrix_world @ v.co
            for k in range(3):
                lo[k] = min(lo[k], w[k] / MM)
                hi[k] = max(hi[k], w[k] / MM)
            found = True
        ev.to_mesh_clear()
    return (lo, hi) if found else None


def spec_agreement(verbose=True):
    spec = {n: (lo, hi) for n, lo, hi in RS.boxes()}
    rows, bad = [], []
    for built, (specname, mode) in sorted(AGREEMENT.items()):
        if specname not in spec:
            bad.append((built, specname, mode, None, "NO SUCH BOX IN room_spec.boxes()"))
            continue
        got = _world_aabb([built])
        if got is None:
            bad.append((built, specname, mode, None, "NOT IN THE BUILT SCENE"))
            continue
        (blo, bhi), (slo, shi) = got, spec[specname]
        if mode == "equal":
            err = max(max(abs(blo[k] - slo[k]), abs(bhi[k] - shi[k])) for k in range(3))
            ok = err <= TOL_MM
        elif mode.startswith("inside:"):
            k = "xyz".index(mode.split(":")[1])
            err = max(max(slo[k] - blo[k], bhi[k] - shi[k]), 0.0)
            ok = err <= TOL_MM
        elif mode == "inside":
            err = max(max(slo[k] - blo[k], bhi[k] - shi[k]) for k in range(3))
            err = max(err, 0.0)
            ok = err <= TOL_MM
        elif mode.startswith("plane:"):
            _, ax, side = mode.split(":")
            k = "xyz".index(ax)
            err = abs((bhi[k] if side == "max" else blo[k])
                      - (shi[k] if side == "max" else slo[k]))
            ok = err <= TOL_MM
        else:
            bad.append((built, specname, mode, None, "UNKNOWN MODE")); continue
        rows.append((built, specname, mode, err, "ok" if ok else "DISAGREES"))
        if not ok:
            bad.append((built, specname, mode, err, "DISAGREES"))
    if verbose:
        print("\nSPEC AGREEMENT - built scene vs room_spec.boxes(), tolerance "
              f"{TOL_MM:.1f} mm")
        for built, specname, mode, err, verdict in sorted(rows + [r for r in bad
                                                                  if r not in rows]):
            e = "   --  " if err is None else f"{err:7.2f}"
            print(f"  {built:16s} vs {specname:14s} {mode:12s} {e} mm   {verdict}")
    if bad:
        print("\nBUILD REFUSED: the scene about to render is not the scene room_spec.py "
              "describes.")
        for built, specname, mode, err, verdict in bad:
            print(f"  {built} / {specname}: {verdict}"
                  + ("" if err is None else f" by {err:.2f} mm"))
        raise SystemExit(1)
    print(f"  {len(rows)} masses agree.\n")
    return rows


def build_curtain(collection):
    G = RS.GLASS_Y
    n, x0, x1 = 340, -100, RS.SHELL_X1 - 200
    top, bot = RS.CEILING - RS.CURTAIN_TOP_DROP, 18
    me = bpy.data.meshes.new("sheer")
    vs, fs = [], []
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        wave = 55.0 * math.sin(t * math.pi * 2 * 26) + 18.0 * math.sin(t * math.pi * 2 * 61)
        for k, z in enumerate((top, bot)):
            slack = 1.0 if k == 0 else 1.28
            vs.append((x * MM, (G + RS.CURTAIN_STANDOFF + wave * slack) * MM, z * MM))
    for i in range(n):
        a = 2 * i
        fs.append((a, a + 2, a + 3, a + 1))
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new("sheer", me)
    collection.objects.link(ob)
    ob.modifiers.new("thick", "SOLIDIFY").thickness = 0.0015
    return ob


def build_canopy(collection):
    """A tree, to the only precision this frame needs from it: chop the sun into
    leaf-sized pieces. The tutorial copies real trees in for exactly this and names the
    collection Trees/Shadows - the geometry exists to cast, not to be seen."""
    import random
    random.seed(7)
    me = bpy.data.meshes.new("canopy")
    vs, fs = [], []
    # THE FIRST CANOPY CAST NOTHING. It topped out at 5.4 m and sat 0.8-4.4 m outside;
    # a 12 deg sun reaching the window at z=3 was already at z=8.3 by the far edge of
    # that volume, so every ray came over the top. Geometry that exists to cast a shadow
    # has to be in the path, and the path is set by the sun angle, not by where a tree
    # would look right.
    for _ in range(4200):
        cx = random.uniform(-6000, 14000)
        cy = RS.GLASS_Y - random.uniform(500, 3200)
        cz = random.uniform(1400, 9500)
        r = random.uniform(45, 130)
        b = len(vs)
        vs += [(cx - r, cy - r * .3, cz), (cx + r, cy - r * .3, cz),
               (cx + r * .4, cy + r * .3, cz + r * 1.3),
               (cx - r * .4, cy + r * .3, cz + r * 1.3)]
        fs.append((b, b + 1, b + 2, b + 3))
    me.from_pydata([(v[0] * MM, v[1] * MM, v[2] * MM) for v in vs], [], fs)
    me.update()
    ob = bpy.data.objects.new("canopy", me)
    collection.objects.link(ob)
    return ob


def build_camera():
    import json
    cam = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
    S = cam["solution"]
    d = bpy.data.cameras.new("cam")
    d.sensor_fit = "HORIZONTAL"
    d.sensor_width = 36.0
    d.lens = LENS_OVERRIDE or S["lens_mm_on_36mm"]
    d.shift_y = (S["principal_point_px"][1] - cam["image"]["h"] / 2.0) / cam["image"]["w"]
    ob = bpy.data.objects.new("cam", d)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (RS.CAM_TO_KITCHEN_WALL * MM, RS.CAM_Y * MM, RS.CAM_H * MM)
    ob.rotation_euler = (math.radians(90.0), 0.0,
                         math.radians(S["blender_rotation_euler_deg"][2]))
    bpy.context.scene.camera = ob
    sc = bpy.context.scene
    sc.render.resolution_x = cam["image"]["w"]
    sc.render.resolution_y = cam["image"]["h"]
    return ob


def build_world(strength=1.0, saturation=1.0, rot_z_deg=0.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = saturation
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(HDRI)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_z_deg)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def build_sun(elevation_deg, irradiance, warm=0.06, rgb=None):
    """THE SUN'S COLOUR IS NOW A MEASUREMENT, and its AZIMUTH still is not.

    `rgb` comes from 04_mood/palette-from-plate.json's light block, where it is the inverse
    of the light chroma palette_solve measured across five families of the frame (ours was
    1.258 / 1.005 / 0.845 times the plate's after the brightness level was taken out - 49%
    warm on R/B). Correcting it HERE rather than in the albedos matters: a per-channel
    albedo divide will absorb any light error and hand you a blue kitchen that only renders
    correctly under this one light.

    The azimuth is a different story and the file says so: sun_solve returns 21.58 deg from
    four floor-shadow edges that disagree with each other by 7.75 deg, and at that azimuth
    no beam reaches the floor the camera sees. 90 deg is a knob."""
    L = bpy.data.lights.new("Sun", "SUN")
    L.energy = irradiance
    L.angle = math.radians(0.526)
    L.color = tuple(rgb) if rgb else (1.0, 1.0 - warm * 0.45, 1.0 - warm * 1.6)
    ob = bpy.data.objects.new("Sun", L)
    coll("Sun").objects.link(ob)
    az = math.radians(SUN_AZIMUTH_PLAN)
    el = math.radians(elevation_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), -math.sin(el)))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ob.location = (4.0, 2.0, 8.0)
    return ob


def override_material(color=AVG_LINEAR, rough=0.4, ior=1.5):
    m = bpy.data.materials.new("Material_Lighting")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    p.inputs["Metallic"].default_value = 0.0
    p.inputs["Roughness"].default_value = rough
    p.inputs["IOR"].default_value = ior
    return m


def glass_material():
    m = bpy.data.materials.new("Glass")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (1, 1, 1, 1)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.28
    if "Transmission Weight" in p.inputs:
        p.inputs["Transmission Weight"].default_value = 1.0
    else:
        p.inputs["Transmission"].default_value = 1.0
    return m


def sheer_material():
    m = bpy.data.materials.new("Sheer")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.66, 0.58, 0.46, 1.0)
    p.inputs["Roughness"].default_value = 0.85
    out = nt.nodes["Material Output"]
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.86, 0.75, 0.55, 1.0)
    add = nt.nodes.new("ShaderNodeAddShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.45
    nt.links.new(p.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(trans.outputs[0], mix.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def canopy_material():
    m = bpy.data.materials.new("Canopy")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.09, 0.14, 0.045, 1.0)
    p.inputs["Roughness"].default_value = 0.75
    return m


def apply(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def render_settings(quick, exposure, view="AgX", samples=0, res_pct=0):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                break
            except Exception:
                continue
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
    except Exception as e:
        print("GPU setup skipped:", e)
    sc.cycles.samples = samples or (48 if quick else 800)
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 16 if quick else 40
    sc.cycles.diffuse_bounces = 16 if quick else 40
    sc.cycles.glossy_bounces = 16 if quick else 40
    sc.cycles.transmission_bounces = 16 if quick else 40
    sc.cycles.transparent_max_bounces = 32
    if quick:
        sc.render.resolution_percentage = 50
    if res_pct:
        sc.render.resolution_percentage = res_pct
    try:
        sc.view_settings.view_transform = view
    except TypeError:
        sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "16"


def passes_for_post(out_png, denoise):
    """His 28:45-30:15: save the NOISY image, then the DENOISED one, and keep both.

    Keeping both is not belt-and-braces. He needs them because the denoiser "killed too
    much detail of the curtain", so the post step paints the denoised back over the noisy
    ONLY where the noise actually is. You cannot do that from one image.

    HOW THIS IS DONE HERE, AND WHY IT IS NOT THE COMPOSITOR. The first version built a
    compositor tree with a Denoise node and a File Output node, which is what the video
    does and what every Blender tutorial does. Blender 5.1 has moved all three pieces:
    `scene.node_tree` is gone (the tree is `scene.compositing_node_group`),
    `CompositorNodeComposite` is undefined (the group ends in a Group Output), and
    `CompositorNodeOutputFile` no longer has `base_path`. Three API errors deep, the
    honest call is that the compositor is not the point - the two IMAGES are. So the lane
    renders twice, once with Cycles' denoiser off and once on, which produces exactly the
    pair the post stage consumes and has no version surface at all.

    WHAT IS NOT PRODUCED, said plainly rather than left to look done: the CRYPTOMATTES he
    saves at 29:50. He needs them because his post is a human painting masks in Photoshop.
    Ours is deterministic - the blend between noisy and denoised is driven by a measured
    local noise estimate, not by a brush - so there is nothing for a mask to select. If a
    later round wants per-object masks, id_mask.py in pipeline/scripts already does that
    job and does not need the compositor either.
    """
    sc = bpy.context.scene
    sc.cycles.use_denoising = bool(denoise)
    print(f"PASSES: this render is the {'DENOISED' if denoise else 'NOISY'} half of the "
          f"pair -> {os.path.basename(out_png)}")
    return None

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="mood")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--samples", type=int, default=0)
    ap.add_argument("--denoise", action="store_true",
                    help="with --passes, render the DENOISED half of the pair")
    ap.add_argument("--passes", action="store_true",
                    help="write the noisy frame, a compositor-denoised frame and the "
                         "cryptomattes, which is what the post stage consumes")
    ap.add_argument("--res-pct", type=int, default=0,
                    help="force the render percentage. --quick halves it, which makes "
                         "the frame a different SIZE from the plate and silently "
                         "invalidates every pixel-box instrument aimed at it.")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "mood.png"))
    ap.add_argument("--sun-el", type=float, default=26.0)
    ap.add_argument("--sun-w", type=float, default=8.1)
    ap.add_argument("--hdri-strength", type=float, default=1.0)
    ap.add_argument("--hdri-sat", type=float, default=1.35)
    ap.add_argument("--hdri-rot", type=float, default=0.0)
    ap.add_argument("--exposure", type=float, default=2.25)
    ap.add_argument("--rough", type=float, default=0.4)
    ap.add_argument("--save-blend", default="")
    ap.add_argument("--no-canopy", action="store_true")
    ap.add_argument("--no-sheer", action="store_true")
    ap.add_argument("--no-glass", action="store_true")
    ap.add_argument("--lens", type=float, default=0.0)
    ap.add_argument("--sun-az", type=float, default=-999.0)
    ap.add_argument("--no-sun", action="store_true")
    ap.add_argument("--keep-sheer", action="store_true",
                    help="keep the sheer during the mood stage. The tutorial drops it "
                         "(13:08) to read the mood without it in the way - but HIS "
                         "reference has a curtain too, and in this plate the sheer is "
                         "not a decoration, it is the FILL LIGHT.")
    o = ap.parse_args(argv)

    # THE MOOD IS A MEASUREMENT FILE, NOT A SET OF SHELL FLAGS. Until 2026-08-29 the
    # settled values lived only in whatever the last person typed on the command line,
    # which is why RESUME.md could say "az 90 was used as a dial" and nothing on disk
    # disagreed. An explicit flag still wins - the file only supplies the DEFAULT.
    LIT = {}
    try:
        LIT = json.load(open(os.path.join(HERE, "..", "04_mood",
                                          "palette-from-plate.json"))).get("light", {})
    except Exception as e:
        print("no settled light block:", e)
    given = set()
    for a in argv:
        if a.startswith("--"):
            given.add(a[2:].split("=")[0].replace("-", "_"))
    for flag, key in (("sun_w", "sun_w"), ("sun_el", "sun_el"), ("sun_az", "sun_az"),
                      ("hdri_strength", "hdri_strength"), ("hdri_sat", "hdri_sat"),
                      ("exposure", "exposure")):
        if flag not in given and key in LIT:
            setattr(o, flag, LIT[key])
    if "keep_sheer" not in given and LIT.get("keep_sheer"):
        o.keep_sheer = True
    SUN_RGB = LIT.get("sun_rgb")
    print(f"MOOD: sun {o.sun_w:.0f} W/m2 az {o.sun_az:.1f} el {o.sun_el:.1f} rgb "
          f"{SUN_RGB}  hdri {o.hdri_strength:.2f} sat {o.hdri_sat:.2f}  exposure "
          f"{o.exposure:+.2f}  sheer {'IN (it is the fill)' if o.keep_sheer else 'hidden'}")

    global LENS_OVERRIDE
    LENS_OVERRIDE = o.lens
    SKIP["canopy"] = o.no_canopy
    SKIP["sheer"] = o.no_sheer
    wipe()
    glass = build_room()
    spec_agreement()
    if o.no_glass:
        bpy.data.objects.remove(glass, do_unlink=True)
        glass = None
    build_camera()
    build_world(o.hdri_strength, o.hdri_sat, o.hdri_rot)
    global SUN_AZIMUTH_PLAN
    if o.sun_az > -900:
        SUN_AZIMUTH_PLAN = o.sun_az
    if not o.no_sun:
        build_sun(o.sun_el, o.sun_w, rgb=SUN_RGB)

    ov = override_material(rough=o.rough)
    if o.stage in ("blockout", "mood"):
        # THE OVERRIDE IS A LIGHTING INSTRUMENT, AND IT FIGHTS TRANSMISSIVE THINGS.
        # A material override replaces EVERY material, so the window glass becomes an
        # opaque grey slab and the room goes black. That is the tutorial at 10:57 - "you
        # can see that glass in our windows block the lighting so let's disable it for
        # now" - and at 13:08 he drops the curtain too, to read the mood against the
        # reference without a sheer in the way. Both come back at the material-split
        # stage with shaders of their own.
        bpy.context.view_layer.material_override = ov
        for nm in (("glass",) if o.keep_sheer else ("glass", "sheer")):
            if nm in bpy.data.objects:
                obj = bpy.data.objects[nm]
                obj.hide_render = True
                if nm == "glass":
                    glass = None
    if o.stage in ("split", "texture"):
        # STAGE 4. The override goes; every mass gets the family the reference says it is.
        # He does this by applying the override to everything and then re-selecting groups
        # by eye (16:45-17:15). Here the grouping is a table in materials_trn003.ASSIGN, so
        # a NEW mass lands in `base` loudly instead of inheriting a neighbour's shader.
        import materials_trn003 as MAT
        made, applied = MAT.build(o.stage)
        MAT.report(applied)
    else:
        if glass is not None:
            apply(glass, glass_material())
        for ob in bpy.data.objects:
            if ob.name == "sheer":
                apply(ob, sheer_material())
            elif ob.name == "canopy":
                apply(ob, canopy_material())
    if glass is not None:
        # His 28:30, and the reason is the whole point of putting the glass back LAST:
        # "I've disabled the diffuse glossy and shadow rays to get the exact same lighting
        # as I had." A pane that starts bouncing light re-lights the room you just settled.
        glass.visible_diffuse = False
        glass.visible_glossy = False
        glass.visible_shadow = False

    render_settings(o.quick, o.exposure, samples=o.samples, res_pct=o.res_pct)
    if o.passes:
        passes_for_post(o.out, o.denoise)
    os.makedirs(os.path.dirname(o.out), exist_ok=True)
    bpy.context.scene.render.filepath = o.out
    if o.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=o.save_blend)
    bpy.ops.render.render(write_still=True)
    print("WROTE", o.out)


main()
