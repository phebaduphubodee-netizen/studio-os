#!/usr/bin/env python3
"""trn004_build.py — TRN-004: materialise the penthouse-bathroom reproduction.

    blender -b --factory-startup --python pipeline/scripts/trn004_build.py -- \
        --out pipeline/output/trn004_r1.png [--quick] [--stage shell|light|full]

LAYER LAW: every number comes from trn004_geom (pure, tested). This file only
turns them into datablocks. bmesh, never bpy.ops on geometry (bpy.ops dies with
"poll() failed" in --background; the repo has paid for that twice).

WHAT IS BEING LEARNED HERE, stage by stage, in the tutorial's own order:
  1 shell     an open-fronted box; walls are planes given thickness by SOLIDIFY
  2 backdrop  ONE plane, far outside, its material EMITTING — the night light
  3 glazing   mullion bays + Glass BSDF (multiscatter GGX)
  4 light     area lights specified as (K, W, shape, size, spread), plus an
              EMISSIVE PLANE sconce rather than a light object
  5 objects   basin by inset+shrink/fatten; folded-towel stack; rolled towel;
              4.9 mm mirror — all of them R8-BUILD shapes (boxes, radii, sweeps)
  6 material  the Brick node as a SLAB GRID over one stone map, and the same map
              retinted into a second stone
"""
import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trn004_geom as G

MM = 0.001


# --------------------------------------------------------------------------- util
def _new_mesh(name, verts, faces, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def _box(name, size_mm, origin_mm=(0, 0, 0)):
    sx, sy, sz = (v * MM for v in size_mm)
    ox, oy, oz = (v * MM for v in origin_mm)
    v = [(ox, oy, oz), (ox + sx, oy, oz), (ox + sx, oy + sy, oz), (ox, oy + sy, oz),
         (ox, oy, oz + sz), (ox + sx, oy, oz + sz), (ox + sx, oy + sy, oz + sz),
         (ox, oy + sy, oz + sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _new_mesh(name, v, f)


def _plane(name, w_m, h_m):
    v = [(-w_m / 2, 0, -h_m / 2), (w_m / 2, 0, -h_m / 2),
         (w_m / 2, 0, h_m / 2), (-w_m / 2, 0, h_m / 2)]
    return _new_mesh(name, v, [(0, 1, 2, 3)])


def _strip_to_output(nt):
    """Remove every node but Material Output.

    THE GOTCHA THIS FUNCTION EXISTS FOR: `nodes.remove()` invalidates other
    python references into the same collection, so a variable holding the output
    node goes stale mid-loop and `out.inputs["Surface"]` then raises KeyError as
    if the socket had been renamed. Re-fetch by name AFTER the removals."""
    for n in list(nt.nodes):
        if n.bl_idname != "ShaderNodeOutputMaterial":
            nt.nodes.remove(n)


def _out(node, *names):
    """First socket that exists under any of these names (5.x renamed Brick's
    `Fac` to `Factor`; a hard-coded name silently breaks across versions)."""
    for nm in names:
        if nm in node.outputs:
            return node.outputs[nm]
    raise KeyError(f"{node.bl_idname}: none of {names} in "
                   f"{[o.name for o in node.outputs]}")


def box_uv(ob, scale_m=1.0):
    """WORLD-ALIGNED BOX PROJECTION, written into the mesh as a UV layer.

    THE DEFECT IT FIXES, found by rendering rather than by reading: Blender's
    Brick Texture consumes ONLY x and y of its input vector — z is ignored. So on
    any surface where x or y is constant (i.e. every vertical wall) the slab grid
    loses an axis and degenerates into STRIPES. Ceilings and floors tile
    correctly and walls do not, which is why the trick can look like it works
    while the wall it was aimed at is the one it breaks on.

    The fix is per-face: choose the dominant normal axis, then feed the OTHER
    two WORLD axes as u,v. An Image Texture gets this free via projection='BOX';
    a procedural has no such mode, so it has to be built. Doing it on the MESH
    rather than in the node tree keeps it one Brick node instead of a triplanar
    blend of three, and keeps it in the data layer where the repo's layer law
    wants geometry decisions to live.

    Continuity is deliberate: u,v are WORLD coordinates, so a slab grid runs
    unbroken across two walls that meet at a corner, the way a real setting-out
    does. It is also why the grid is independent of object scale."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="box")
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))     # dominant axis
        i, j = [k for k in range(3) if k != ax]
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (co[i] / scale_m, co[j] / scale_m)
    return ob


def _mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


def _assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def _smooth_by_angle(ob, angle_deg=30.0):
    """VID 18:11 — 'Shade Smooth by Angle', angle 30, Keep Sharp Edges.
    In 4.1+ this is the Smooth by Angle node-group modifier; the DATA-level
    equivalent that survives --background is per-face use_smooth plus a
    sharp-edge mark, which is what we do (a modifier that needs an operator to
    add is exactly the thing the repo's layer law forbids here)."""
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    thr = math.radians(angle_deg)
    for e in me.edges:
        e.use_edge_sharp = False
    # mark edges whose two faces meet sharper than the threshold
    face_of_edge = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            face_of_edge.setdefault(ek, []).append(p.normal.copy())
    key_to_edge = {e.key: e for e in me.edges}
    for ek, normals in face_of_edge.items():
        if len(normals) == 2:
            a = normals[0].angle(normals[1]) if normals[0].length and normals[1].length else 0.0
            if a > thr and ek in key_to_edge:
                key_to_edge[ek].use_edge_sharp = True
    return ob


# --------------------------------------------------------------------------- 1 shell
def build_shell():
    """An OPEN-FRONTED box. VID 01:30 shows his penthouse from outside: there is
    no fourth wall — the camera lives where it would be. Walls are PLANES given
    thickness by a Solidify modifier, so a wall's thickness stays one number."""
    w, l, h = G.ROOM_W_MM * MM, G.ROOM_L_MM * MM, G.ROOM_H_MM * MM
    t = G.WALL_T_MM * MM
    mat = _mat("m_trn004_wall", base=(0.62, 0.60, 0.57), rough=0.854)  # VID 02:10 rough 0.854

    parts = []
    floor = _new_mesh("shell_floor", [(0, 0, 0), (w, 0, 0), (w, l, 0), (0, l, 0)], [(0, 1, 2, 3)])
    ceil = _new_mesh("shell_ceiling", [(0, 0, h), (w, 0, h), (w, l, h), (0, l, h)], [(0, 3, 2, 1)])
    # left wall = the vanity wall; right wall = the tub wall; far wall is GLAZED
    left = _new_mesh("shell_wall_left", [(0, 0, 0), (0, l, 0), (0, l, h), (0, 0, h)], [(0, 1, 2, 3)])
    right = _new_mesh("shell_wall_right", [(w, 0, 0), (w, l, 0), (w, l, h), (w, 0, h)], [(0, 3, 2, 1)])
    for ob in (floor, ceil, left, right):
        sol = ob.modifiers.new("Solidify", "SOLIDIFY")
        sol.thickness = t
        sol.offset = -1.0
        _assign(ob, mat)
        parts.append(ob)
    return parts, mat


# --------------------------------------------------------------------------- 2 backdrop
def build_backdrop(emissive=True):
    """THE MOVE THIS REPO DOES NOT HAVE. One plane, 113 m out, EMITTING at 55.

    Two things are true at once and the video only says the first: it is the
    view, and it is the KEY LIGHT of a night interior. A night room lit by
    lamps alone has nothing to model the window reveals or the glass, so the
    glazing reads as a black hole. Emission on the backdrop is what puts light
    ON the mullions from the correct direction — a direction no lamp inside the
    room can supply."""
    plane = _plane("backdrop_city", 240.0, 135.0)   # 16:9, big enough to fill the glazing
    plane.location = (G.BACKDROP_X_M, G.BACKDROP_Y_M, G.BACKDROP_Z_M)
    plane.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    m = bpy.data.materials.new("m_trn004_backdrop")
    m.use_nodes = True
    nt = m.node_tree
    _strip_to_output(nt)
    out = nt.nodes["Material Output"]
    # a stand-in for his city photo: a cool gradient with warm point-lights.
    # THE POINT IS THE EMISSION AND THE DISTANCE, not the picture.
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 260.0
    tex.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.62
    ramp.color_ramp.elements[0].color = (0.020, 0.045, 0.070, 1.0)   # night sky/city body
    ramp.color_ramp.elements[1].position = 0.74
    ramp.color_ramp.elements[1].color = (1.000, 0.780, 0.420, 1.0)   # window lights
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = G.BACKDROP_EMISSION if emissive else 0.0
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    _assign(plane, m)
    return plane, m


# --------------------------------------------------------------------------- 3 glazing
def build_glazing(n_bays=4):
    """Far wall, floor to ceiling, split into bays by near-black posts."""
    w, l, h = G.ROOM_W_MM * MM, G.ROOM_L_MM * MM, G.ROOM_H_MM * MM
    glass = _new_mesh("glazing_pane",
                      [(0, l, 0), (w, l, 0), (w, l, h), (0, l, h)], [(0, 1, 2, 3)])
    sol = glass.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = G.GLASS_T_MM * MM

    gm = bpy.data.materials.new("m_trn004_glass")
    gm.use_nodes = True
    nt = gm.node_tree
    _strip_to_output(nt)
    out = nt.nodes["Material Output"]
    gb = nt.nodes.new("ShaderNodeBsdfGlass")
    gb.distribution = "MULTI_GGX"                      # VID 12:04
    gb.inputs["Roughness"].default_value = G.GLASS_ROUGHNESS
    gb.inputs["IOR"].default_value = G.GLASS_IOR
    nt.links.new(gb.outputs["BSDF"], out.inputs["Surface"])
    _assign(glass, gm)

    mm = _mat("m_trn004_mullion", base=(0.035, 0.035, 0.038),
              rough=G.MULLION_ROUGHNESS, metallic=G.MULLION_METALLIC)
    posts = []
    for i, cx_mm in enumerate(G.mullion_bay_centres_mm(G.ROOM_W_MM, n_bays)):
        cx = cx_mm * MM
        x0 = min(max(cx - G.MULLION_W_MM * MM / 2, 0.0), w - G.MULLION_W_MM * MM)
        p = _box(f"mullion_{i}", (G.MULLION_W_MM, G.MULLION_D_MM, G.ROOM_H_MM),
                 (x0 / MM, (l - G.MULLION_D_MM * MM / 2) / MM, 0))
        _assign(p, mm)
        posts.append(p)
    # head and sill rails, so the glass is framed rather than floating
    for nm, z in (("mullion_head", G.ROOM_H_MM - G.MULLION_W_MM),
                  ("mullion_sill", 0.0)):
        r = _box(nm, (G.ROOM_W_MM, G.MULLION_D_MM, G.MULLION_W_MM),
                 (0, (l - G.MULLION_D_MM * MM / 2) / MM, z))
        _assign(r, mm)
        posts.append(r)
    return glass, posts, gm, mm


# --------------------------------------------------------------------------- 4 light
def build_lights():
    """Area lights as (K, W, shape, size, spread). Blender's `energy` IS watts
    when the scene is in the default unit system, so a wattage is not a
    metaphor here — it is the quantity."""
    made = []
    w, l, h = G.ROOM_W_MM * MM, G.ROOM_L_MM * MM, G.ROOM_H_MM * MM
    rows = G.light_rows()

    # wall_wash: grazes the vanity wall — VID 08:29 square, 126 deg spread
    r = rows[0]
    d = bpy.data.lights.new("wall_wash", "AREA")
    d.shape = "SQUARE"
    d.size = r["size_m"]
    d.energy = r["watts"]
    d.spread = math.radians(r["spread_deg"])
    d.use_custom_distance = False
    if r["kelvin"]:
        d.color = _blackbody(r["kelvin"])
    ob = bpy.data.objects.new("wall_wash", d)
    ob.location = (0.45, l * 0.45, h - 0.35)
    ob.rotation_euler = (math.radians(70.0), 0.0, math.radians(-90.0))
    bpy.context.scene.collection.objects.link(ob)
    made.append(ob)

    # ceiling_key: VID 22:35 disk, 451.6 W, 75.3 deg. Kelvin NOT shown -> we do
    # not invent one; we take the warm swatch's hue from the sconce hex, which
    # IS shown, and say so. An unknown that gets a number silently is the defect.
    r = rows[1]
    d2 = bpy.data.lights.new("ceiling_key", "AREA")
    d2.shape = "DISK"
    d2.size = r["size_m"]
    d2.energy = r["watts"]
    d2.spread = math.radians(r["spread_deg"])
    d2.color = G.sconce_rgb_linear()      # DECLARED SUBSTITUTION, not a measurement
    ob2 = bpy.data.objects.new("ceiling_key", d2)
    ob2.location = (w * 0.5, l * 0.30, h - 0.05)
    bpy.context.scene.collection.objects.link(ob2)
    made.append(ob2)
    return made


def _blackbody(kelvin):
    """Planckian locus -> linear RGB, the same curve Blender's Blackbody node
    uses. Kept local so the light spec can carry KELVIN and the build can
    consume it without a node network per light."""
    t = kelvin / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661 if t > 0 else 0.0
        b = 0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255.0
    out = []
    for c in (r, g, b):
        c = max(0.0, min(255.0, c)) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def build_sconce():
    """VID 12:26 — a wall sconce that is NOT a light object: an emissive plane
    with a frosted panel in front of it. Why it matters beyond the trick: the
    glowing thing is VISIBLE GEOMETRY, so the frame shows a source for its own
    highlight. A light object with no fixture is the 'lit from nowhere' defect."""
    l, h = G.ROOM_L_MM * MM, G.ROOM_H_MM * MM
    emit_plane = _new_mesh("sconce_emitter",
                           [(0.02, l * 0.55 - 0.05, 1.55), (0.02, l * 0.55 + 0.05, 1.55),
                            (0.02, l * 0.55 + 0.05, 2.15), (0.02, l * 0.55 - 0.05, 2.15)],
                           [(0, 1, 2, 3)])
    m = bpy.data.materials.new("m_trn004_sconce")
    m.use_nodes = True
    nt = m.node_tree
    _strip_to_output(nt)
    out = nt.nodes["Material Output"]
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*G.sconce_rgb_linear(), 1.0)
    e.inputs["Strength"].default_value = G.SCONCE_EMISSION_FINAL   # VID 12:30, the looked-at value
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    _assign(emit_plane, m)

    diffuser = _box("sconce_diffuser", (18.0, 120.0, 640.0),
                    (25.0, (l * 0.55 - 0.06) / MM, 1530.0))
    dm = _mat("m_trn004_sconce_glass", base=(0.92, 0.90, 0.86), rough=0.42)
    dm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.85
    _assign(diffuser, dm)
    return emit_plane, diffuser


# --------------------------------------------------------------------------- 5 objects
def build_vanity():
    """The counter slab, then the basin cut INTO it the way the video does it:
    inset the top face, then push the inset face down. The vessel wall thickness
    is the shrink offset; nothing is typed twice."""
    l = G.ROOM_L_MM * MM
    run_mm = G.ROOM_L_MM - 400.0
    hole_cx = G.WALL_T_MM + G.COUNTER_D_MM * 0.52
    hole_cy = G.ROOM_L_MM * 0.42
    slab = counter_with_aperture(
        G.WALL_T_MM, 200.0, G.COUNTER_D_MM, run_mm, G.COUNTER_T_MM,
        G.COUNTER_H_MM - G.COUNTER_T_MM,
        hole_cx, hole_cy, G.BASIN_W_MM, G.BASIN_D_MM)
    basin = _make_basin("vanity_basin")
    basin.location = (hole_cx * MM, hole_cy * MM, G.basin_rim_z_mm() * MM)
    waste = build_basin_waste(hole_cx * MM, hole_cy * MM, G.basin_floor_z_mm() * MM)

    joinery = build_vanity_joinery(G.WALL_T_MM, 200.0, run_mm, G.COUNTER_D_MM)
    return slab, basin, joinery + waste


# =========================================================================== detail
# EVERY EDGE IS BROKEN. Nothing manufactured has a perfectly sharp arris: a
# machined edge is broken 0.3-0.5 mm, joinery is eased 2-3 mm, a cast fitting is
# radiused more. Without it the specular highlight that runs along a real edge
# has nowhere to live, and the frame reads as CG at a glance whatever the
# material does. The first version of this scene had 3 bevels across 35 objects.
EASE = {"joinery": 0.0025, "stone": 0.0015, "metal": 0.0008, "cloth": 0.010}


def ease(ob, kind="joinery", segments=2):
    b = ob.modifiers.new("Ease", "BEVEL")
    b.width = EASE.get(kind, 0.002)
    b.segments = segments
    b.limit_method = "ANGLE"
    b.angle_limit = math.radians(35.0)
    return ob


def counter_with_aperture(x0_mm, y0_mm, w_mm, l_mm, t_mm, z_mm,
                          hole_cx_mm, hole_cy_mm, hole_w_mm, hole_l_mm):
    """The counter slab with the basin aperture CUT, as an authored quad ring.

    THE BUG THIS FIXES, and it was mine, found by looking at the render: I built
    the basin as a separate vessel UNDER a solid slab. An undermount basin under
    an uncut slab is INVISIBLE - the frame showed a clean counter and I had
    reported the basin as built.

    Openings are authored face loops, never booleans (pipeline law: a boolean
    n-gons the mesh and a SketchUp recipient sees it)."""
    x0, y0 = x0_mm * MM, y0_mm * MM
    w, l, t, z = w_mm * MM, l_mm * MM, t_mm * MM, z_mm * MM
    hx0 = (hole_cx_mm - hole_w_mm / 2) * MM
    hx1 = (hole_cx_mm + hole_w_mm / 2) * MM
    hy0 = (hole_cy_mm - hole_l_mm / 2) * MM
    hy1 = (hole_cy_mm + hole_l_mm / 2) * MM
    xs = [x0, hx0, hx1, x0 + w]
    ys = [y0, hy0, hy1, y0 + l]
    zt = z + t

    verts, faces = [], []
    idx, bidx = {}, {}
    for i, xv in enumerate(xs):
        for j, yv in enumerate(ys):
            idx[(i, j)] = len(verts)
            verts.append((xv, yv, zt))
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            faces.append((idx[(i, j)], idx[(i + 1, j)],
                          idx[(i + 1, j + 1)], idx[(i, j + 1)]))
    for i, xv in enumerate(xs):
        for j, yv in enumerate(ys):
            bidx[(i, j)] = len(verts)
            verts.append((xv, yv, z))
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            faces.append((bidx[(i, j)], bidx[(i, j + 1)],
                          bidx[(i + 1, j + 1)], bidx[(i + 1, j)]))
    for i in range(3):
        faces.append((idx[(i, 0)], idx[(i + 1, 0)], bidx[(i + 1, 0)], bidx[(i, 0)]))
        faces.append((idx[(i, 3)], bidx[(i, 3)], bidx[(i + 1, 3)], idx[(i + 1, 3)]))
    for j in range(3):
        faces.append((idx[(0, j)], bidx[(0, j)], bidx[(0, j + 1)], idx[(0, j + 1)]))
        faces.append((idx[(3, j)], idx[(3, j + 1)], bidx[(3, j + 1)], bidx[(3, j)]))
    # the aperture reveal, so the slab shows its 40 mm thickness at the cut edge
    for (a, b) in (((1, 1), (2, 1)), ((2, 1), (2, 2)), ((2, 2), (1, 2)), ((1, 2), (1, 1))):
        faces.append((idx[a], idx[b], bidx[b], bidx[a]))
    return _new_mesh("vanity_slab", verts, faces)


def build_tub(x_mm, y_mm, w_mm, l_mm, h_mm, wall_mm=None):
    """The tub, authored the same way as the basin: rings down to a floor. A
    bath is the basin one scale up, so one method builds both."""
    wall = (G.BASIN_SHRINK_MM * 3.0 if wall_mm is None else wall_mm) * MM
    w, l, h = w_mm * MM, l_mm * MM, h_mm * MM
    x, y = x_mm * MM, y_mm * MM
    cx, cy = x + w / 2, y + l / 2
    inner_h = h - 0.06

    def rect(hw, hd, z):
        return [(cx - hw, cy - hd, z), (cx + hw, cy - hd, z),
                (cx + hw, cy + hd, z), (cx - hw, cy + hd, z)]

    rings, verts, faces = [], [], []
    for scale, z in ((1.000, h), (0.955, h - inner_h * 0.4),
                     (0.885, h - inner_h * 0.8), (0.840, h - inner_h)):
        base = len(verts)
        verts.extend(rect(w / 2 * scale - wall, l / 2 * scale - wall, z))
        rings.append(base)
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((a + k, a + k2, b + k2, b + k))
    fl = rings[-1]
    faces.append((fl + 3, fl + 2, fl + 1, fl + 0))
    ob = _new_mesh("tub_inner", verts, faces)
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = wall
    sol.offset = 1.0
    _smooth_by_angle(ob, 34.0)
    ease(ob, "stone", segments=3)

    apron = _box("tub_apron", (w_mm, l_mm, h_mm - 15.0), (x_mm, y_mm, 0.0))
    ease(apron, "joinery", segments=3)
    return [ob, apron]


def build_shower_screen(x_mm, y0_mm, l_mm, h_mm, t_mm=10.0):
    """A frameless glass screen. It gives the far half of the room an EDGE - a
    long narrow room with nothing in its depth reads as a corridor."""
    ob = _box("shower_screen", (t_mm, l_mm, h_mm), (x_mm, y0_mm, 0.0))
    return ease(ob, "metal")


def build_vanity_joinery(x0_mm, y0_mm, run_mm, depth_mm):
    """A vanity as JOINERY, not a block: a toe recess so a person can stand at
    it, drawer fronts with a reveal so there is a way in, a shadow gap under the
    counter so the top reads as a separate slab, and an end panel."""
    parts = []
    toe_h, toe_d = 110.0, 65.0
    carc_h = G.COUNTER_H_MM - G.COUNTER_T_MM - toe_h - 8.0
    plinth = _box("vanity_plinth", (depth_mm - toe_d, run_mm, toe_h),
                  (x0_mm + toe_d, y0_mm, 0.0))
    parts.append(ease(plinth, "joinery"))
    carcass = _box("vanity_carcass", (depth_mm - 18.0, run_mm, carc_h),
                   (x0_mm, y0_mm, toe_h))
    parts.append(ease(carcass, "joinery"))

    REVEAL = 4.0
    n = 3
    bank = (run_mm - REVEAL * (n + 1)) / n
    for i in range(n):
        fy = y0_mm + REVEAL + i * (bank + REVEAL)
        rows = ((toe_h + REVEAL, carc_h * 0.38 - REVEAL * 1.5),
                (toe_h + carc_h * 0.38 + REVEAL * 0.5, carc_h * 0.62 - REVEAL * 1.5))
        for k, (fz, fh) in enumerate(rows):
            f = _box("vanity_drawer_%d_%d" % (i, k), (18.0, bank, fh),
                     (x0_mm + depth_mm - 18.0, fy, fz))
            parts.append(ease(f, "joinery", segments=3))
            pull = _box("vanity_pull_%d_%d" % (i, k), (10.0, bank * 0.92, 16.0),
                        (x0_mm + depth_mm - 26.0, fy + bank * 0.04, fz + fh - 22.0))
            parts.append(ease(pull, "metal"))

    end = _box("vanity_end_panel", (depth_mm, 18.0, G.COUNTER_H_MM - toe_h),
               (x0_mm, y0_mm + run_mm - 18.0, toe_h))
    parts.append(ease(end, "joinery"))
    return parts


def build_tap(x_m, y_m):
    """A single-lever mixer with the parts a mixer has: an escutcheon on the
    deck, a body, a spout that TAPERS, an aerator ring at the tip, and a lever.
    Miss the aerator and the tip looks cut off; miss the escutcheon and the tap
    grows out of the stone."""
    parts = []
    deck = G.COUNTER_H_MM
    esc = _cylinder("tap_escutcheon", 0.028, 0.006, 32)
    esc.location = (x_m, y_m, (deck + 3) * MM)
    parts.append(ease(_smooth_by_angle(esc, 30.0), "metal"))

    body = _cylinder("tap_body", 0.021, 0.150, 32)
    body.location = (x_m, y_m, (deck + 6) * MM + 0.075)
    parts.append(ease(_smooth_by_angle(body, 30.0), "metal"))

    bm = bmesh.new()
    r0, r1, R = 0.019, 0.013, 0.070
    z0 = (deck + 6) * MM + 0.150
    prev = None
    N, SEG = 16, 20
    a88 = math.radians(88.0)
    for i in range(N + 1):
        t = i / N
        a = a88 * t
        cy = y_m + R * math.sin(a)
        cz = z0 + R * (1.0 - math.cos(a))
        rr = r0 + (r1 - r0) * t
        tang = Vector((0.0, math.cos(a), math.sin(a)))
        u = Vector((1.0, 0.0, 0.0))
        v = tang.cross(u).normalized()
        ring = []
        for k in range(SEG):
            th = 2 * math.pi * k / SEG
            off = u * (rr * math.cos(th)) + v * (rr * math.sin(th))
            ring.append(bm.verts.new((x_m + off.x, cy + off.y, cz + off.z)))
        if prev:
            for k in range(SEG):
                bm.faces.new([prev[k], prev[(k + 1) % SEG],
                              ring[(k + 1) % SEG], ring[k]])
        prev = ring
    bmesh.ops.contextual_create(bm, geom=prev)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("tap_spout")
    bm.to_mesh(me)
    bm.free()
    spout = bpy.data.objects.new("tap_spout", me)
    bpy.context.scene.collection.objects.link(spout)
    parts.append(_smooth_by_angle(spout, 40.0))

    aer = _cylinder("tap_aerator", 0.0145, 0.010, 24)
    aer.rotation_euler = (a88, 0, 0)
    aer.location = (x_m, y_m + R * math.sin(a88) + 0.004,
                    z0 + R * (1 - math.cos(a88)))
    parts.append(ease(_smooth_by_angle(aer, 30.0), "metal"))

    lever = _box("tap_lever", (16.0, 92.0, 14.0),
                 (x_m / MM - 8, y_m / MM - 100, deck + 150))
    parts.append(ease(_smooth_by_angle(lever, 30.0), "metal", segments=3))
    return parts


def build_towel_bar(x_mm, y_mm, length_mm, z_mm):
    """A towel bar with brackets - and the rail lands ON its brackets rather
    than stopping short of them, which is the exact defect the main lane is
    carrying on nine wardrobe rails right now."""
    parts = []
    for yy in (y_mm, y_mm + length_mm):
        br = _cylinder("towel_bracket", 0.011, 0.055, 20)
        br.rotation_euler = (0, math.radians(90.0), 0)
        br.location = ((x_mm + 27) * MM, yy * MM, z_mm * MM)
        parts.append(ease(_smooth_by_angle(br, 30.0), "metal"))
        pl = _cylinder("towel_bracket_plate", 0.020, 0.006, 24)
        pl.rotation_euler = (0, math.radians(90.0), 0)
        pl.location = ((x_mm + 3) * MM, yy * MM, z_mm * MM)
        parts.append(ease(_smooth_by_angle(pl, 30.0), "metal"))
    rail = _cylinder("towel_rail", 0.009, length_mm * MM, 20)
    rail.rotation_euler = (math.radians(90.0), 0, 0)
    rail.location = ((x_mm + 52) * MM, (y_mm + length_mm / 2) * MM, z_mm * MM)
    parts.append(ease(_smooth_by_angle(rail, 30.0), "metal"))
    return parts


def build_drain(x_m, y_m):
    """A linear shower drain: a channel, a grate sitting in it, a reveal between
    the two. Without it the enclosure has nowhere for water to go, which is the
    first thing the cold critic said could not be built."""
    parts = []
    ch = _box("drain_channel", (700.0, 90.0, 26.0),
              (x_m / MM - 350, y_m / MM - 45, 0.0))
    parts.append(ease(ch, "metal"))
    gr = _box("drain_grate", (676.0, 66.0, 8.0),
              (x_m / MM - 338, y_m / MM - 33, 14.0))
    parts.append(ease(gr, "metal", segments=1))
    return parts


def build_shower_fitting(x_mm, y_mm, z_mm):
    """Riser, arm, head and a mixer plate, so the enclosure is a shower and not
    a glass box."""
    parts = []
    plate = _box("shower_plate", (12.0, 120.0, 260.0),
                 (x_mm - 12.0, y_mm - 60, z_mm - 900))
    parts.append(ease(plate, "metal", segments=3))
    riser = _cylinder("shower_riser", 0.010, 0.62, 20)
    riser.location = ((x_mm - 22) * MM, y_mm * MM, (z_mm - 310) * MM)
    parts.append(ease(_smooth_by_angle(riser, 30.0), "metal"))
    arm = _cylinder("shower_arm", 0.010, 0.20, 20)
    arm.rotation_euler = (0, math.radians(90.0), 0)
    arm.location = ((x_mm - 120) * MM, y_mm * MM, z_mm * MM)
    parts.append(ease(_smooth_by_angle(arm, 30.0), "metal"))
    head = _cylinder("shower_head", 0.105, 0.016, 40)
    head.location = ((x_mm - 225) * MM, y_mm * MM, (z_mm - 12) * MM)
    parts.append(ease(_smooth_by_angle(head, 30.0), "metal", segments=3))
    return parts


def _make_basin(name):
    """An undermount basin, AUTHORED as a face loop.

    THE BUG THIS REPLACES, found by measuring the built mesh rather than by
    looking at it: the first version used `bmesh.ops.inset_region` and then
    translated "every face that is not in the returned set" downward, assuming
    the return was the new side ring. It is not. So the set I translated
    included the outer boundary, the whole vessel collapsed, and the object
    measured **z 670..680 mm — a flat 10 mm plate** where a 130 mm bowl should
    have been. In the frame it read as a black hole in the counter, and I could
    have stared at that hole for a long time without learning it was a plate.

    The lesson is not "inset_region is tricky". It is that I took a LIBRARY'S
    RETURN VALUE on faith and never asked the mesh what it had become — the same
    shape as trusting a light's wattage without asking whether the light is in
    the scene. Authored quads have no such ambiguity: every vertex here has a
    stated z, and the test can assert the depth.

    Real basins taper toward the floor and have a radiused bottom, so the walls
    draw in by TAPER on the way down."""
    w, d = G.BASIN_W_MM * MM, G.BASIN_D_MM * MM
    dep = G.BASIN_DEPTH_MM * MM
    wall = G.BASIN_SHRINK_MM * MM
    TAPER = 0.72                       # floor is 72% of the opening

    def rect(hw, hd, z):
        return [(-hw, -hd, z), (hw, -hd, z), (hw, hd, z), (-hw, hd, z)]

    # opening (tucked just under the slab), then two intermediate rings so the
    # wall can curve, then the floor
    rings, verts, faces = [], [], []
    levels = [(1.000, 0.0), (0.940, -dep * 0.35), (0.830, -dep * 0.72),
              (TAPER, -dep)]
    for scale, z in levels:
        base = len(verts)
        verts.extend(rect(w / 2 * scale, d / 2 * scale, z))
        rings.append(base)
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((a + k, a + k2, b + k2, b + k))
    fl = rings[-1]
    faces.append((fl + 3, fl + 2, fl + 1, fl + 0))          # the floor, facing up

    ob = _new_mesh(name, verts, faces)
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = wall
    sol.offset = 1.0                                        # thicken outward
    _smooth_by_angle(ob, 34.0)
    ease(ob, "stone", segments=3)
    return ob


def build_basin_waste(x_m, y_m, z_m):
    """The waste. A basin with no outlet is the same class of defect as a shower
    with no drain — the cold critic filed both."""
    ring = _cylinder("basin_waste", 0.021, 0.006, 28)
    ring.location = (x_m, y_m, z_m + 0.003)
    _smooth_by_angle(ring, 30.0)
    return [ease(ring, "metal")]


def build_towels():
    """VID 17:48-17:58. A folded towel is a box with a LIP — one thin step along
    the front edge that reads as the fold. A stack is that box repeated, each
    RESTING on the one below (R9: derived, never typed). The roll is a cylinder."""
    l = G.ROOM_L_MM * MM
    x0 = G.WALL_T_MM + 120.0
    y0 = (l * 0.66) / MM
    made = []
    # THREE IDENTICAL BOXES IS WHAT A STACK IS NOT. Real folded terry never lines
    # up: each towel sits a few mm off the one below, none is exactly the same
    # thickness, and the fold edge rolls over instead of ending in a straight
    # line. The variation is derived from the layer index so it is repeatable,
    # not random noise the next run would change.
    for i, z in enumerate(G.towel_stack_layers()):
        jx = (i * 7 % 5) - 2.0          # -2..+2 mm
        jy = (i * 11 % 7) - 3.0         # -3..+3 mm
        squash = 1.0 - 0.035 * i        # the bottom towel is compressed
        t = _box(f"towel_fold_{i}",
                 (G.TOWEL_D_MM + jx, G.TOWEL_W_MM + jy,
                  (G.TOWEL_T_MM - 4.0) * squash),
                 (x0 + jx * 0.5, y0 + jy * 0.5, z))
        bev = t.modifiers.new("Bevel", "BEVEL")
        bev.width = EASE["cloth"]       # a fold rolls over; it has no arris
        bev.segments = 4
        bev.limit_method = "ANGLE"
        _smooth_by_angle(t, 30.0)
        made.append(t)
        # the lip: a thinner slab along the front edge — this is the fold line
        lip = _box(f"towel_lip_{i}", (G.TOWEL_FOLD_LIP_MM, G.TOWEL_W_MM - 6.0,
                                      G.TOWEL_T_MM - 10.0),
                   (x0 + G.TOWEL_D_MM - G.TOWEL_FOLD_LIP_MM, y0 + 3.0, z + 3.0))
        lb = lip.modifiers.new("Bevel", "BEVEL")
        lb.width = 0.004
        lb.segments = 2
        made.append(lip)

    roll = build_rolled_towel(
        "towel_roll",
        (x0 + G.TOWEL_D_MM * 0.5) * MM,
        y0 * MM + G.TOWEL_W_MM * MM / 2,
        G.towel_roll_axis_z_mm() * MM,
        G.TOWEL_W_MM * MM * 0.85,
        r_out=G.TOWEL_ROLL_D_MM * MM / 2)
    made.append(roll)
    return made


def _cylinder(name, r, h, n):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n,
                          radius1=r, radius2=r, depth=h)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_faucet(x_m, y_m):
    """VID 17:23-17:40 — a swept profile, not a sculpt. R8's BUILD side by the
    letter: a measured 1D profile swept along a curve. Body + gooseneck arc +
    a base plate; the arc is a polyline revolved into a tube, so the only free
    number is the arc radius."""
    parts = []
    base = _box("faucet_base", (70.0, 70.0, 12.0), (x_m / MM - 35, y_m / MM - 35,
                                                    G.COUNTER_H_MM))
    parts.append(base)
    stem_h = 210.0
    stem = _cylinder("faucet_stem", 0.016, stem_h * MM, 16)
    stem.location = (x_m, y_m, (G.COUNTER_H_MM + 12 + stem_h / 2) * MM)
    _smooth_by_angle(stem, 30.0)
    parts.append(stem)
    # gooseneck: a quarter arc of tube, built from a polyline swept by hand
    bm = bmesh.new()
    r = 0.085
    z0 = (G.COUNTER_H_MM + 12 + stem_h) * MM
    ring_prev = None
    for i in range(13):
        a = math.radians(90.0) * i / 12.0
        cx = x_m
        cy = y_m + r * math.sin(a)
        cz = z0 + r * (1.0 - math.cos(a))
        tang = Vector((0.0, math.cos(a), math.sin(a)))
        u = Vector((1.0, 0.0, 0.0))
        v = tang.cross(u).normalized()
        ring = []
        for k in range(12):
            th = 2 * math.pi * k / 12
            off = u * (0.014 * math.cos(th)) + v * (0.014 * math.sin(th))
            ring.append(bm.verts.new((cx + off.x, cy + off.y, cz + off.z)))
        if ring_prev:
            for k in range(12):
                bm.faces.new([ring_prev[k], ring_prev[(k + 1) % 12],
                              ring[(k + 1) % 12], ring[k]])
        ring_prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("faucet_neck")
    bm.to_mesh(me)
    bm.free()
    neck = bpy.data.objects.new("faucet_neck", me)
    bpy.context.scene.collection.objects.link(neck)
    _smooth_by_angle(neck, 30.0)
    parts.append(neck)
    return parts


def build_rolled_towel(name, cx_m, cy_m, cz_m, length_m, r_out=0.055,
                       turns=2.6, sheet=0.006):
    """A rolled towel as a SPIRAL, so it has a free end.

    The first version was `_cylinder(...)` — a perfect extruded tube with flat
    caps. The cold critic named exactly what that costs: "no spiral, no visible
    free end of the towel, no slump where it rests, no flare at the ends". A
    cylinder is the massing of a rolled towel, not a rolled towel, and the tell
    is at the END FACE, which is where the eye goes.

    Built as an Archimedean ribbon: r grows linearly with angle, so the strip
    winds outward and terminates in an edge you can see. Two surfaces (outer and
    inner face of the terry) closed at the free end, swept along the roll axis."""
    verts, faces = [], []
    N = int(turns * 28)
    r_in = max(r_out - turns * sheet * 1.9, sheet * 1.2)
    half = length_m / 2.0
    rows = []
    for i in range(N + 1):
        th = turns * 2.0 * math.pi * (i / N)
        r = r_in + (r_out - r_in) * (i / N)
        for outer in (0, 1):
            rr = r + (sheet * 0.5 if outer else -sheet * 0.5)
            y = cy_m + rr * math.cos(th)
            z = cz_m + rr * math.sin(th)
            base = len(verts)
            verts.append((cx_m - half, y, z))
            verts.append((cx_m + half, y, z))
            rows.append(base)
    # rows is ordered [inner_i, outer_i] per step, 2 verts each
    per = 4          # inner(2) + outer(2) verts per angular step
    for i in range(N):
        a = i * per
        b = (i + 1) * per
        # outer surface
        faces.append((a + 2, a + 3, b + 3, b + 2))
        # inner surface
        faces.append((a + 1, a + 0, b + 0, b + 1))
        # the two edges of the strip
        faces.append((a + 0, a + 2, b + 2, b + 0))
        faces.append((a + 3, a + 1, b + 1, b + 3))
    # cap the free end (the visible tail) and the start
    faces.append((0, 1, 3, 2))
    e = N * per
    faces.append((e + 2, e + 3, e + 1, e + 0))
    ob = _new_mesh(name, verts, faces)
    _smooth_by_angle(ob, 42.0)
    ease(ob, "cloth", segments=2)
    return ob


def build_screen_with_door(x_mm, y0_mm, fixed_mm, door_mm, h_mm, t_mm=10.0):
    """A screen that can be ENTERED: a fixed panel, a 6 mm gap, a door leaf, and
    a handle. The critic's first cannot-be-built item was a sealed glass box —
    a continuous frame with no leaf, no hinge and no gap anywhere in its
    perimeter, so nobody could get in and no water could get out."""
    GAP = 6.0
    parts = []
    fixed = _box("shower_screen", (t_mm, fixed_mm, h_mm), (x_mm, y0_mm, 0.0))
    parts.append(ease(fixed, "metal"))
    door = _box("shower_door", (t_mm, door_mm, h_mm - 40.0),
                (x_mm, y0_mm + fixed_mm + GAP, 20.0))
    parts.append(ease(door, "metal"))
    # a pull bar on the door, standing off on two studs
    for yy in (y0_mm + fixed_mm + GAP + door_mm * 0.30,
               y0_mm + fixed_mm + GAP + door_mm * 0.70):
        st = _cylinder("shower_door_stud", 0.008, 0.040, 16)
        st.rotation_euler = (0, math.radians(90.0), 0)
        st.location = ((x_mm - 20) * MM, yy * MM, (h_mm * 0.52) * MM)
        parts.append(ease(_smooth_by_angle(st, 30.0), "metal"))
    bar = _cylinder("shower_door_pull", 0.010, door_mm * 0.46 * MM, 16)
    bar.rotation_euler = (math.radians(90.0), 0, 0)
    bar.location = ((x_mm - 40) * MM,
                    (y0_mm + fixed_mm + GAP + door_mm * 0.5) * MM,
                    (h_mm * 0.52) * MM)
    parts.append(ease(_smooth_by_angle(bar, 30.0), "metal"))
    return parts


def build_counter_props(x_m, y_m, deck_mm):
    """The counter had two towel items on it and nothing else. A penthouse
    bathroom is sold on this layer; the critic called the frame a construction
    shot taken before handover styling. These are R8-BUILD shapes only — boxes
    with radii and swept profiles, nothing free-form."""
    parts = []
    z = deck_mm * MM

    # a stone tray with a rim, so the small things sit ON something
    tray = _box("prop_tray", (150.0, 300.0, 12.0),
                (x_m / MM - 75, y_m / MM - 150, deck_mm))
    parts.append(("stone", ease(tray, "stone", segments=3)))
    for dy in (-150.0, 150.0 - 10.0):
        lip = _box("prop_tray_lip", (150.0, 10.0, 16.0),
                   (x_m / MM - 75, y_m / MM + dy, deck_mm + 10))
        parts.append(("stone", ease(lip, "stone", segments=3)))

    # soap dispenser: body + shoulder + pump + spout
    body = _cylinder("prop_soap_body", 0.030, 0.115, 32)
    body.location = (x_m, y_m - 0.075, z + 0.0125 + 0.0575)
    parts.append(("glass", ease(_smooth_by_angle(body, 30.0), "stone")))
    collar = _cylinder("prop_soap_collar", 0.019, 0.020, 28)
    collar.location = (x_m, y_m - 0.075, z + 0.0125 + 0.125)
    parts.append(("metal", ease(_smooth_by_angle(collar, 30.0), "metal")))
    stem = _cylinder("prop_soap_stem", 0.008, 0.038, 20)
    stem.location = (x_m, y_m - 0.075, z + 0.0125 + 0.153)
    parts.append(("metal", ease(_smooth_by_angle(stem, 30.0), "metal")))
    spout = _cylinder("prop_soap_spout", 0.006, 0.045, 16)
    spout.rotation_euler = (math.radians(90.0), 0, 0)
    spout.location = (x_m, y_m - 0.075 + 0.020, z + 0.0125 + 0.168)
    parts.append(("metal", ease(_smooth_by_angle(spout, 30.0), "metal")))

    # a short tumbler beside it
    cup = _cylinder("prop_tumbler", 0.034, 0.090, 32)
    cup.location = (x_m, y_m + 0.055, z + 0.0125 + 0.045)
    parts.append(("glass", ease(_smooth_by_angle(cup, 30.0), "stone")))
    return parts


def build_mirror_frame(x_mm, y0_mm, run_mm, sill_mm, h_mm, t_mm=10.0):
    """The mirror was a floating pane: no edge, no frame, no fixing, no shadow
    gap — the critic could not tell whether it was a mirror or a second window,
    and said so as the largest plane on the left of the picture. A returned
    surround plus a reveal behind the glass gives it both an edge and a reason
    to be attached to the wall."""
    parts = []
    REV = 6.0
    for nm, oy, ol, oz, oh in (
            ("mirror_head", y0_mm, run_mm, sill_mm + h_mm, t_mm),
            ("mirror_sill", y0_mm, run_mm, sill_mm - t_mm, t_mm),
            ("mirror_jamb_a", y0_mm, t_mm, sill_mm, h_mm),
            ("mirror_jamb_b", y0_mm + run_mm - t_mm, t_mm, sill_mm, h_mm)):
        f = _box(nm, (REV + G.MIRROR_T_MM, ol, oh),
                 (G.WALL_T_MM, oy, oz))
        parts.append(ease(f, "joinery", segments=3))
    return parts


def build_mirror():
    """VID 18:09 — a plane extruded 4.898 mm. Not zero: a mirror with no
    thickness has no edge, and the edge is what makes it read as glass on a wall
    rather than a hole in the wall."""
    l = G.ROOM_L_MM * MM
    run_mm = G.ROOM_L_MM - 800.0
    m = _box("vanity_mirror", (G.MIRROR_T_MM, run_mm, G.MIRROR_H_MM),
             (G.WALL_T_MM, 400.0, G.MIRROR_SILL_MM))
    mat = _mat("m_trn004_mirror", base=(0.92, 0.93, 0.94), rough=0.02, metallic=1.0)
    _assign(m, mat)
    return m


# --------------------------------------------------------------------------- 6 material
def slab_material(name, base_stone=(0.52, 0.47, 0.40), joint=(0.06, 0.055, 0.05),
                  brick=None, retint=None):
    """THE ONE THIS REPO DOES NOT HAVE.

    A Brick Texture node is wired as a SLAB GRID, not as bricks: its Color1 is
    the stone, its Color2 is the joint, and — the part that actually matters —
    the node offsets each brick along the row, so consecutive slabs sample the
    stone at DIFFERENT places. One photo therefore stops reading as one photo.

    Our lane is carrying the exact defect this fixes: a measured ~364 px wall
    repeat, and a critic item that reads 'grain runs continuously across the
    black grooves, a visible mirror axis mid-wall, the same block repeated left
    and right'. Grooves modelled, grain not broken — the joint was geometry and
    the texture underneath never learned about it.

    `retint` reproduces VID 21:44: the SAME map through Brightness/Contrast then
    Hue/Sat/Value becomes a second, darker stone. One download, two materials."""
    bk = dict(G.BRICK_VID)
    if brick:
        bk.update(brick)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])

    # the stone. A procedural stand-in for the ambientCG map, so the NODE GRAPH
    # is what is being reproduced and no download is required to run this.
    stone = nt.nodes.new("ShaderNodeTexNoise")
    stone.inputs["Scale"].default_value = 6.0
    stone.inputs["Detail"].default_value = 8.0
    stone.inputs["Roughness"].default_value = 0.62
    nt.links.new(mapping.outputs["Vector"], stone.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*base_stone, 1.0)
    ramp.color_ramp.elements[1].color = (min(1.0, base_stone[0] * 1.7),
                                         min(1.0, base_stone[1] * 1.7),
                                         min(1.0, base_stone[2] * 1.7), 1.0)
    nt.links.new(stone.outputs["Fac"], ramp.inputs["Fac"])

    src = ramp.outputs["Color"]
    if retint:                                    # VID 21:44
        bc = nt.nodes.new("ShaderNodeBrightContrast")
        bc.inputs["Bright"].default_value = retint["bright"]
        bc.inputs["Contrast"].default_value = retint["contrast"]
        nt.links.new(src, bc.inputs["Color"])
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Hue"].default_value = retint["hue"]
        hsv.inputs["Saturation"].default_value = retint["saturation"]
        hsv.inputs["Value"].default_value = retint["value"]
        hsv.inputs["Fac"].default_value = retint["fac"]
        nt.links.new(bc.outputs["Color"], hsv.inputs["Color"])
        src = hsv.outputs["Color"]

    br = nt.nodes.new("ShaderNodeTexBrick")
    nt.links.new(mapping.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(src, br.inputs["Color1"])
    br.inputs["Color2"].default_value = (*joint, 1.0)   # second stone slot
    br.inputs["Mortar"].default_value = (*joint, 1.0)
    br.inputs["Scale"].default_value = bk["scale"]
    br.inputs["Mortar Size"].default_value = bk["mortar_size"]
    br.inputs["Mortar Smooth"].default_value = bk["mortar_smooth"]
    br.inputs["Bias"].default_value = bk["bias"]
    br.inputs["Brick Width"].default_value = bk["brick_width"]
    br.inputs["Row Height"].default_value = bk["row_height"]
    br.offset = bk["offset"]
    br.offset_frequency = bk["offset_frequency"]
    br.squash = bk["squash"]
    br.squash_frequency = bk["squash_frequency"]

    nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.28
    # the joint is also a groove: Fac drives a bump, so the slab edge catches light
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(_out(br, "Factor", "Fac"), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m



_FLOOR_STANDING = ("tub_apron", "vanity_plinth", "shower_screen")


def solve_camera(cam, tries=None):
    """DERIVE the camera from THE THREE CONTAINMENT QUESTIONS, not from a nudge.

    The first version of this asked for four whole objects to be fully inside the
    frame and returned NOT SOLVED on all 48 candidates — correctly, because the
    ask was impossible: from inside a 2.6 m room no lens contains a basin on the
    left wall and a tub on the right. The failure was mine, in the ASK. The
    camera skill does not ask for whole objects; it asks three questions:

      Q1  the room's TOP EDGE is in the frame     (else it reads as a backdrop)
      Q2  the NEAREST object's FLOOR CONTACT is in the frame  (else it floats)
      Q3  every light lighting what you see is in the frustum OR its source is
          visible in frame                         (else the light comes from nowhere)

    Searching position too, because the video's room is OPEN-FRONTED for exactly
    this reason — the camera stands where the fourth wall would be."""
    import itertools
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    base_rot = tuple(cam.rotation_euler)

    def uvz(p):
        return world_to_camera_view(sc, cam, p)

    def aabb_uv(name):
        ob = sc.objects.get(name)
        if ob is None:
            return None
        dg = bpy.context.evaluated_depsgraph_get()
        obe = ob.evaluated_get(dg)
        c = [uvz(ob.matrix_world @ Vector(v)) for v in obe.bound_box]
        if max(p.z for p in c) <= 0:
            return None
        return (min(p.x for p in c), max(p.x for p in c),
                min(p.y for p in c), max(p.y for p in c))

    def score():
        q = {}
        head = aabb_uv("mullion_head")                    # Q1: the room's top
        q["Q1_top_edge"] = bool(head and head[3] <= 1.0 and head[2] >= 0.0)
        # Q2: THE FRAME MUST BE GROUNDED — at least one floor-standing object
        # shows its floor contact.
        #
        # I posed this question wrong three times, and the third failure is the
        # instructive one. The skill says "an object whose contact is cropped is
        # an object floating". I first read that as "every object" (impossible in
        # a 2.6 m room), then as "the tub" (the FARTHEST thing), then as "the
        # nearest object" — which from any camera in this room is the vanity
        # carcass the camera is standing beside. Cropping the thing you are
        # standing next to is not floating; it is normal. 0 of 875 cameras could
        # satisfy it, which is the shape of an ill-posed predicate, not of a hard
        # room. What the eye actually needs is A GROUND REFERENCE: somewhere in
        # the frame, something meets the floor where you can see it.
        grounded = False
        for _nm in _FLOOR_STANDING:
            _bb = aabb_uv(_nm)
            if _bb and _bb[2] >= 0.0 and _bb[0] < 1.0 and _bb[1] > 0.0:
                grounded = True
                break
        q["Q2_frame_is_grounded"] = grounded
        sc_d = aabb_uv("sconce_diffuser")                 # Q3: a source in frame
        q["Q3_light_source"] = bool(
            sc_d and sc_d[0] >= 0 and sc_d[1] <= 1 and sc_d[2] >= 0 and sc_d[3] <= 1)
        # and the room must still fill the frame rather than float in it
        pane = aabb_uv("glazing_pane")
        q["Q4_glazing_fills"] = bool(pane and (pane[1] - pane[0]) > 0.30)
        return q

    best, table = None, []
    W, L = G.ROOM_W_MM * MM, G.ROOM_L_MM * MM
    for x, y, z, pitch in itertools.product(
            [W * 0.20, W * 0.35, W * 0.50, W * 0.65, W * 0.80],
            # y >= 0.05: at or inside the open front. At y = -1.60 the solver
            # found a camera that answered all four questions and put the
            # UNLIT EXTERIOR of the left wall across a third of the frame
            # (trn004_r6_camera.png). The questions were right; the domain
            # was wrong. A constraint the search cannot express is a
            # constraint the search will violate.
            [0.05, 0.30, 0.60, 1.00, 1.50],
            [1.20, 1.35, 1.50, 1.65, 1.80],
            [92.0, 90.0, 88.0, 86.0, 83.0, 80.0, 76.0]):
        cam.location = (x, y, z)
        cam.rotation_euler = (math.radians(pitch), base_rot[1], base_rot[2])
        bpy.context.view_layer.update()
        q = score()
        n = sum(q.values())
        table.append((x, y, z, pitch, n, q))
        if best is None or n > best[4]:
            best = (x, y, z, pitch, n, q)
    if best is None or best[4] < 4:
        # Report, never settle. A solver that keeps its best-but-failing try
        # launders a typed camera into a derived one.
        if best:
            cam.location = (best[0], best[1], best[2])
            cam.rotation_euler = (math.radians(best[3]), base_rot[1], base_rot[2])
            bpy.context.view_layer.update()
        return False, best, table
    cam.location = (best[0], best[1], best[2])
    cam.rotation_euler = (math.radians(best[3]), base_rot[1], base_rot[2])
    bpy.context.view_layer.update()
    return True, best, table


def frame_contains(cam, names=None):
    """Project every object's world AABB through the camera and report whether it
    is IN the frame — the camera-composition skill's three containment questions,
    answered with zero render time.

    WHY IT IS HERE AND NOT IN MY EYE: I added a bathtub, looked at the render,
    could not find it, and was about to guess. A frame is not a place to look for
    an object you are not sure you built — the scene either projects inside the
    frustum or it does not, and that is arithmetic.

    Returns rows of (name, u0, u1, v0, v1, verdict) in normalised camera space
    where the frame is u,v in [0,1]."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for ob in sc.objects:
        if ob.type != "MESH":
            continue
        if names and ob.name not in names:
            continue
        obe = ob.evaluated_get(dg)
        pts = [ob.matrix_world @ Vector(c) for c in obe.bound_box]
        uv = [world_to_camera_view(sc, cam, p) for p in pts]
        us = [c.x for c in uv]; vs = [c.y for c in uv]; zs = [c.z for c in uv]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        if max(zs) <= 0:
            verdict = "BEHIND CAMERA"
        elif u1 < 0 or u0 > 1 or v1 < 0 or v0 > 1:
            verdict = "OUTSIDE FRAME"
        elif u0 < 0 or u1 > 1 or v0 < 0 or v1 > 1:
            verdict = "clipped"
        else:
            verdict = "in frame"
        rows.append((ob.name, u0, u1, v0, v1, verdict))
    return rows


def report_containment(cam):
    print("[trn004] FRAME CONTAINS (u,v normalised; frame is 0..1)")
    for name, u0, u1, v0, v1, verdict in sorted(frame_contains(cam)):
        flag = "" if verdict == "in frame" else "   <-- " + verdict
        print(f"    {name:22s} u {u0:+.3f}..{u1:+.3f}  v {v0:+.3f}..{v1:+.3f}{flag}")
    # the three questions the camera skill makes mandatory
    lights = [o for o in bpy.context.scene.objects if o.type == "LIGHT"]
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    for lo in lights:
        c = world_to_camera_view(sc, cam, lo.matrix_world.translation)
        inside = 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0
        print(f"    LIGHT {lo.name:16s} u {c.x:+.3f} v {c.y:+.3f} "
              f"-> {'source in frame' if inside else 'SOURCE NOT IN FRAME'}")


# --------------------------------------------------------------------------- camera + render
def build_camera():
    w, l, h = G.ROOM_W_MM * MM, G.ROOM_L_MM * MM, G.ROOM_H_MM * MM
    cd = bpy.data.cameras.new("cam")
    cd.lens = G.FOCAL_MM                     # VID 03:53
    cd.clip_end = G.CLIP_END_M               # VID 03:53 — the backdrop is beyond default
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("cam", cd)
    # eye height 1550, pushed to the tub side so the vanity run reads in
    # perspective rather than head-on — the tutorial's own framing at 20:30.
    cam.location = (w * 0.80, 0.65, 1.55)
    cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(12.0))
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def setup_render(out_path, quick=False):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    # DEVICE SELECTION MUST SAY WHICH DEVICE IT GOT. This block used to pin
    # "OPTIX" and fall back to CPU inside a bare except with NO print -- so a
    # render that quietly ran on CPU was indistinguishable from one that ran on
    # the GPU, and "could not use the GPU" printed exactly like "used the GPU".
    # build_room.py:987-989 already prints its fallback and trn001/trn002 print
    # `device=`; this file was the silent outlier. It also tried ONE backend,
    # where the others walk a list.
    device = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                if any(getattr(d, "type", "CPU") != "CPU" for d in prefs.devices):
                    device = kind
                    break
            except Exception:
                continue
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU" if device != "CPU" else "CPU"
    except Exception as e:
        sc.cycles.device = "CPU"
        device = "CPU"
        print(f"  (GPU setup failed, CPU fallback: {e})")
    print(f"  cycles device={device}")
    sc.cycles.samples = 48 if quick else 256
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 960 if quick else 1600
    sc.render.resolution_y = 540 if quick else 900
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_path
    sc.view_settings.view_transform = "AgX"
    return sc


def clear_scene():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                 bpy.data.lights, bpy.data.cameras):
        for item in list(coll):
            coll.remove(item)
    bpy.context.scene.world = bpy.data.worlds.new("w_trn004")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.0     # NO ambient cheat: the room is lit
    return                                        # by the backdrop and the fixtures only


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="pipeline/output/trn004_r1.png")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-backdrop-emission", action="store_true",
                    help="A/B control: the same frame with the backdrop NOT emitting.")
    ap.add_argument("--cam", default=None,
                    help="x,y,z,pitch,yaw override — a LOOK, not a hero "
                         "camera. R7d: the builder aims, it does not judge.")
    ap.add_argument("--solve-camera", action="store_true",
                    help="Derive pitch/height from what the frame must contain.")
    ap.add_argument("--contains-only", action="store_true",
                    help="Print the frame-containment table and stop. No render.")
    ap.add_argument("--vid-brick", action="store_true",
                    help="Use the video's Brick values verbatim instead of solving "
                         "them from a real slab size.")
    ap.add_argument("--flat-stone", action="store_true",
                    help="A/B control: the same stone with NO slab grid.")
    args = ap.parse_args(argv)

    clear_scene()
    shell, wallmat = build_shell()
    build_backdrop(emissive=not args.no_backdrop_emission)
    glass, posts, gm, mm = build_glazing()
    build_lights()
    build_sconce()
    slab, basin, joinery = build_vanity()
    towels = build_towels()
    mirror = build_mirror()
    faucet = build_tap((G.WALL_T_MM + G.COUNTER_D_MM * 0.80) * MM,
                       G.ROOM_L_MM * MM * 0.42 - 0.16)
    # the screen is built HERE because `fittings` below consumes its door parts.
    screen_parts = build_screen_with_door(G.ROOM_W_MM - 850.0, G.ROOM_L_MM * 0.52,
                                          900.0, 780.0, 1900.0)
    screen = screen_parts[0]
    fittings = []
    fittings += build_towel_bar(G.WALL_T_MM, G.ROOM_L_MM * 0.72, 600.0, 1150.0)
    # THE WET ZONE HAS TO BE ONE PLACE. The first arrangement put the shower head
    # on the right wall at y=2184, a linear drain on open floor at y=2184 but
    # 500 mm away in x, and the bath screen enclosing NEITHER — three fittings
    # that each made sense alone and described no room anyone could shower in.
    # This is the plan defect the cold critic reaches first: it does not ask
    # whether a part is well modelled, it asks whether the assembly could be
    # built and used. So: shower OVER the bath (the screen is its screen), and
    # the floor gully in the wet corner beyond the tub where the fall would go.
    _tub_y0 = G.ROOM_L_MM * 0.52
    _tub_len = 1700.0
    fittings += build_drain((G.ROOM_W_MM - 620.0) * MM,
                            (_tub_y0 + _tub_len + 260.0) * MM)
    fittings += build_shower_fitting(G.ROOM_W_MM - G.WALL_T_MM - 12.0,
                                     _tub_y0 + 420.0, 2050.0)
    fittings += screen_parts[1:]
    fittings += build_mirror_frame(G.WALL_T_MM, 400.0, G.ROOM_L_MM - 800.0,
                                   G.MIRROR_SILL_MM, G.MIRROR_H_MM)
    props = build_counter_props((G.WALL_T_MM + G.COUNTER_D_MM * 0.42) * MM,
                                G.ROOM_L_MM * MM * 0.60, G.COUNTER_H_MM)
    chrome = _mat("m_trn004_chrome", base=(0.045, 0.045, 0.048),
                  rough=0.16, metallic=1.0)   # VID: his taps read near-black
    for f in faucet:
        _assign(f, chrome)


    if args.vid_brick:
        brick = None                      # his numbers, verbatim -> 100x50 mm tile
        label = "VID verbatim"
    else:
        brick = G.brick_settings_for_slab(G.SLAB_STONE_M[0], G.SLAB_STONE_M[1],
                                          G.SLAB_JOINT_M)
        label = "derived slab"
    if args.flat_stone:
        brick = dict(brick or G.BRICK_VID, mortar_size=0.0)
        label += " (joints OFF - control)"
    stone = slab_material("m_trn004_stone", brick=brick)
    for ob in shell:
        box_uv(ob)
        ease(ob, "stone")
        _assign(ob, stone)
    print(f"[trn004] slab layout: {label}")
    dark = slab_material("m_trn004_stone_dark", retint=G.RETINT_VID,
                         brick={"scale": 2.0, "brick_width": 1.0, "row_height": 0.5})
    box_uv(slab); ease(slab, "stone"); _assign(slab, dark)
    joinery_mat = _mat("m_trn004_joinery", base=(0.30, 0.26, 0.22), rough=0.42)
    for j in joinery:
        _assign(j, joinery_mat)
    _assign(basin, _mat("m_trn004_basin", base=(0.86, 0.85, 0.83), rough=0.18))
    for f in fittings:
        _assign(f, chrome)
    prop_mats = {
        "stone": dark,
        "metal": chrome,
        "glass": _mat("m_trn004_prop_glass", base=(0.72, 0.74, 0.73), rough=0.08),
    }
    for kind, ob in props:
        _assign(ob, prop_mats[kind])
    towelmat = _mat("m_trn004_towel", base=(0.78, 0.76, 0.72), rough=0.92)
    for t in towels:
        _assign(t, towelmat)

    tub = build_tub(G.ROOM_W_MM - 850.0, G.ROOM_L_MM * 0.52, 800.0, 1700.0, 560.0)
    # THE SCREEN IS THE TUB'S, and it starts where the tub starts. Placed across
    # the room's middle it split the frame in two and read as a partition — an
    # object defect the camera cannot rescue.
    for t in tub:
        box_uv(t)
        _assign(t, dark if t.name == "tub_apron" else
                _mat("m_trn004_tub", base=(0.88, 0.87, 0.85), rough=0.12))
    # DELIBERATE DEVIATION from the video's 0.500: that value was read off a
    # different element. A shower screen at roughness 0.5 renders opaque milk and
    # walls the room off — visible in trn004_r4_objects.png. Clear glass here.
    sgm = bpy.data.materials.new("m_trn004_screen_glass")
    sgm.use_nodes = True
    _strip_to_output(sgm.node_tree)
    _sg = sgm.node_tree.nodes.new("ShaderNodeBsdfGlass")
    _sg.distribution = "MULTI_GGX"
    _sg.inputs["Roughness"].default_value = 0.02
    _sg.inputs["IOR"].default_value = G.GLASS_IOR
    sgm.node_tree.links.new(_sg.outputs["BSDF"],
                            sgm.node_tree.nodes["Material Output"].inputs["Surface"])
    _assign(screen, sgm)
    cam = build_camera()
    if args.cam:
        x, y, z, pitch, yaw = [float(v) for v in args.cam.split(',')]
        cam.location = (x, y, z)
        cam.rotation_euler = (math.radians(pitch), 0.0, math.radians(yaw))
        bpy.context.view_layer.update()
    if args.solve_camera and not args.cam:
        ok, best, table = solve_camera(cam)
        x, y, z, pitch, n, q = best
        verdict = "SOLVED" if ok else f"BEST EFFORT ({n}/4) — reported, not hidden"
        print(f"[trn004] CAMERA {verdict}: x {x:.2f} y {y:.2f} z {z:.2f} "
              f"pitch {pitch:.0f} deg")
        for k, v in q.items():
            print(f"    {k:20s} {'PASS' if v else 'FAIL'}")
        print(f"    {sum(1 for r in table if r[4] == 4)} of {len(table)} "
              f"candidates answered all four")
    report_containment(cam)
    if args.contains_only:
        return
    setup_render(args.out, quick=args.quick)

    ok, need = G.clip_end_is_sufficient()
    print(f"[trn004] backdrop {G.backdrop_distance_m():.1f} m; clip end "
          f"{G.CLIP_END_M:.0f} m needs >= {need:.0f} m -> {'OK' if ok else 'FAILS'}")
    sw, sh = G.brick_slab_size_m()
    print(f"[trn004] slab grid {sw * 1000:.0f}x{sh * 1000:.0f} mm, "
          f"joint {G.brick_mortar_width_m() * 1000:.1f} mm")
    print(f"[trn004] objects={len(bpy.data.objects)} rendering -> {args.out}")
    bpy.ops.render.render(write_still=True)
    print("[trn004] done")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv)
