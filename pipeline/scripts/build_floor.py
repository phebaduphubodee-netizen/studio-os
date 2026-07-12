"""
build_floor.py — extrude a whole FLOOR into ONE .blend, FAITHFULLY, from the wall segments
read out of the vector floor-plan PDF (pdf_extract_walls.py). For owner inspection.

    blender -b --factory-startup --python build_floor.py -- <floor-manifest.json> [--render] [--out DIR]

This does NOT estimate or trace-by-eye: every wall is the actual thick-black stroke from the
dimensioned sheet, mapped to real mm (scale verified against the written dims). Walls are
extruded to ceiling height; the two designed rooms (master + sitting) can drop their trusted
furniture on top; a groundplane + top/3-4 cameras make it a clean white inspection model.

Self-contained (does NOT import build_room.py — that module auto-runs on import). Data API
only (never bpy.ops for geometry — dies in --background). Reuses furniture.py for massing.
"""
import hashlib
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import furniture   # pure-python massing (INCHES)
import placement_gate  # bpy-free pure logic: scene_zone_decision (owner-signed below_grade -> excluded)
import floor_openings  # bpy-free pure logic: doors/windows/glass wall-cuts + boxes

MM = 0.001
IN = 0.0254
_FURN_KINDS = {"sofa", "loveseat", "coffee_table", "dining_table", "desk", "side_table",
               "nightstand", "chair", "dining_chair", "armchair", "bed"}
_MATS = {}


# --------------------------------------------------------------------------- materials
def _mat(name, rgba, rough=0.85):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Roughness"].default_value = rough
        if rgba[3] < 1.0:                     # translucent (glass panes)
            b.inputs["Alpha"].default_value = rgba[3]
            for attr, val in (("blend_method", "BLEND"),
                              ("surface_render_method", "BLENDED")):
                try:                          # EEVEE legacy vs Next: set whichever exists
                    setattr(m, attr, val)
                except (AttributeError, TypeError):
                    pass
    m.diffuse_color = rgba
    _MATS[name] = m
    return m


PALETTE = {
    "wall":  ((0.88, 0.86, 0.82, 1.0), 0.9),    # walls – warm off-white plaster
    "glass": ((0.60, 0.76, 0.80, 0.30), 0.05),  # window/facade panes – translucent
    "floor": ((0.72, 0.69, 0.64, 1.0), 0.9),    # groundplane
    "wood":  ((0.74, 0.65, 0.53, 1.0), 0.7),    # furniture
    "seat":  ((0.80, 0.75, 0.67, 1.0), 0.75),   # upholstery
    "white": ((0.85, 0.86, 0.88, 1.0), 0.45),   # bath fixtures
    "terrace": ((0.62, 0.59, 0.54, 1.0), 0.8),  # terrace deck
    "plant": ((0.34, 0.48, 0.30, 1.0), 0.85),   # planter greenery
    "lbl":   ((0.10, 0.36, 0.40, 1.0), 0.5),    # labels
}


def matp(key):
    rgba, rough = PALETTE[key]
    return _mat(key, rgba, rough)


# --------------------------------------------------------------------------- primitives
_BOX_FACES = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _link(obj, coll):
    (coll or bpy.context.scene.collection).objects.link(obj)


def make_mesh(name, verts, faces, mat, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    if mat:
        ob.data.materials.append(mat)
    _link(ob, coll)
    return ob


def add_box(name, x0, y0, z0, dx, dy, dz, mat, coll):
    z1 = z0 + dz
    v = [(x0, y0, z0), (x0 + dx, y0, z0), (x0 + dx, y0 + dy, z0), (x0, y0 + dy, z0),
         (x0, y0, z1), (x0 + dx, y0, z1), (x0 + dx, y0 + dy, z1), (x0, y0 + dy, z1)]
    return make_mesh(name, v, _BOX_FACES, mat, coll)


def add_oriented_box(name, x0, y0, z0, dx, dy, dz, rot_deg, pivot, mat, coll):
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    px, py = pivot

    def R(x, y):
        xr, yr = x - px, y - py
        return (px + xr * ca - yr * sa, py + xr * sa + yr * ca)

    base = [R(x0, y0), R(x0 + dx, y0), R(x0 + dx, y0 + dy), R(x0, y0 + dy)]
    z1 = z0 + dz
    v = [(x, y, z0) for x, y in base] + [(x, y, z1) for x, y in base]
    return make_mesh(name, v, _BOX_FACES, mat, coll)


# ------------------------------------------------------------------ FAITHFUL wall extrude
def _in_zones(mx, my, zones):
    if not zones:
        return True
    for z in zones:
        if z[0] <= mx <= z[2] and z[1] <= my <= z[3]:
            return True
    return False


def build_walls(segments, h_m, thick_m, coll, zones=None):
    """Each PDF wall segment (mm) -> a thin vertical wall box of height h_m. The drawing's
    double-lined walls become two parallel faces (reads as a real wall); single-line
    partitions become one thin wall. `zones` (list of [x0,y0,x1,y1] mm) clips to a scope."""
    mat = matp("wall")
    ht = thick_m / 2.0
    n = 0
    for (a, b) in segments:
        if not _in_zones((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, zones):
            continue
        x1, y1 = a[0] * MM, a[1] * MM
        x2, y2 = b[0] * MM, b[1] * MM
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-4:
            continue
        nx, ny = -dy / L * ht, dx / L * ht          # perpendicular offset
        base = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
        v = [(x, y, 0.0) for x, y in base] + [(x, y, h_m) for x, y in base]
        make_mesh(f"wall_{n}", v, _BOX_FACES, mat, coll)
        n += 1
    print(f"  walls: extruded {n} segments to {h_m:.2f} m")
    return n


def build_openings(openings, ceiling_mm, coll):
    """Windows/doors/glass as REAL geometry. floor_openings.opening_boxes computes the
    boxes (glass pane, sill wall, lintel); this only extrudes them -- no decision logic
    in the bpy layer. Bare 'opening' type contributes nothing (an honest passage)."""
    n = 0
    for o in openings:
        for b in floor_openings.opening_boxes(o, ceiling_mm):
            r = b["rect"]
            add_box(f"open_{o.get('id', '?')}_{b['kind']}_{n}",
                    r[0] * MM, r[1] * MM, b["z0_mm"] * MM,
                    (r[2] - r[0]) * MM, (r[3] - r[1]) * MM,
                    (b["z1_mm"] - b["z0_mm"]) * MM,
                    matp("glass" if b["kind"] == "glass" else "wall"), coll)
            n += 1
    print(f"  openings: {n} boxes (glass/sill/lintel)")


# --------------------------------------------------------------------- furniture overlay
def place_massing(kind, name, sw_x, sw_y, w, d, h, rot, base_z, mat_furn, mat_box, coll):
    pivot = (sw_x + w / 2.0, sw_y + d / 2.0)
    if kind in _FURN_KINDS:
        wi, di, hi = max(w / IN, 1.0), max(d / IN, 1.0), max(h / IN, 1.0)
        for (pn, px, py, pz, pdx, pdy, pdz) in furniture.parts(kind, name, 0.0, 0.0, wi, di, hi):
            add_oriented_box(pn.replace(" ", "_"),
                             sw_x + px * IN, sw_y + py * IN, base_z + pz * IN,
                             pdx * IN, pdy * IN, max(pdz * IN, 0.01),
                             rot, pivot, mat_furn, coll)
    else:
        add_oriented_box(("m__" + name).replace(" ", "_"),
                         sw_x, sw_y, base_z, w, d, max(h, 0.02), rot, pivot, mat_box, coll)


def add_cylinder(name, cx, cy, z0, r, h, mat, coll, seg=40):
    import math as _m
    verts = [(cx + r * _m.cos(2 * _m.pi * i / seg), cy + r * _m.sin(2 * _m.pi * i / seg), z0) for i in range(seg)]
    verts += [(cx + r * _m.cos(2 * _m.pi * i / seg), cy + r * _m.sin(2 * _m.pi * i / seg), z0 + h) for i in range(seg)]
    faces = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    faces.append(tuple(range(seg)))                          # bottom cap
    faces.append(tuple(range(2 * seg - 1, seg - 1, -1)))     # top cap
    return make_mesh(name, verts, faces, mat, coll)


def place_round_table(name, cx, cy, base_z, r, h, mat, coll):
    """A ROUND pedestal table (circular top + slim stem + foot disk) — reads round, not boxy."""
    t = min(0.045, max(h * 0.12, 0.02))
    add_cylinder(name + "_top", cx, cy, base_z + h - t, r, t, mat, coll)
    add_cylinder(name + "_stem", cx, cy, base_z + 0.02, max(r * 0.14, 0.03), max(h - t - 0.02, 0.02), mat, coll)
    add_cylinder(name + "_foot", cx, cy, base_z, max(r * 0.42, 0.05), 0.025, mat, coll)


def build_floor_zones(zones, coll):
    """A thin colour-coded floor slab per room so the top view reads at a glance."""
    for i, z in enumerate(zones):
        outline = [(x * MM, y * MM) for x, y in z["outline_mm"]]
        rgba = tuple(z.get("color", [0.8, 0.8, 0.8])) + (1.0,)
        m = _mat(f"zone_{z.get('id', i)}", rgba, 0.92)
        add_poly_floor(f"floorzone_{z.get('id', i)}", outline, 0.03, m, coll)


def build_terrace(t, coll):
    outline = [(x * MM, y * MM) for x, y in t["outline_mm"]]
    fth = t.get("slab_thk_mm", 120) * MM
    add_poly_floor("terrace_slab", outline, fth, matp("terrace"), coll)
    pm = matp("plant")
    for p in t.get("planters", []):
        add_box(("planter_" + p.get("name", "p")).replace(" ", "_"),
                p["x"] * MM, p["y"] * MM, 0.0, p["w"] * MM, p["d"] * MM, p["h"] * MM, pm, coll)


def add_poly_floor(name, outline_m, fth, mat, coll):
    n = len(outline_m)
    verts = [(x, y, -fth) for x, y in outline_m] + [(x, y, 0.0) for x, y in outline_m]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return make_mesh(name, verts, faces, mat, coll)


def build_furniture(spec, dx_mm, dy_mm, coll):
    """Drop the trusted furniture (builtins + items + ensuite fixtures) of a room-spec@0.2
    into the floor frame. Walls come from the PDF, so the spec's shell is skipped."""
    furn, seat, white = matp("wood"), matp("seat"), matp("white")

    def place(lst, base_default=0.0, seat_ok=False):
        for it in lst or []:
            if placement_gate.scene_zone_decision(it)["action"] == "skip":
                continue                               # owner-signed below_grade: ground-below, not a floor-2 object
            kind = it.get("kind", "block")
            bz = (it.get("mount_mm", 0) or 0) * MM
            mat = seat if (seat_ok and kind in ("sofa", "loveseat", "armchair", "chair", "bench")) else furn
            if it.get("shape") == "round":                 # round tables render as a cylinder, not a box
                place_round_table(it.get("name", kind).replace(" ", "_"),
                                  (it["x"] + dx_mm + it["w"] / 2.0) * MM, (it["y"] + dy_mm + it["d"] / 2.0) * MM,
                                  bz, min(it["w"], it["d"]) / 2.0 * MM, max(it.get("h", 400) * MM, 0.02), mat, coll)
                continue
            place_massing(kind, it.get("name", kind),
                          (it["x"] + dx_mm) * MM, (it["y"] + dy_mm) * MM,
                          it["w"] * MM, it["d"] * MM, max(it.get("h", 400) * MM, 0.02),
                          it.get("rot", 0), bz, mat, mat, coll)

    place(spec.get("builtins"))
    place(spec.get("items"), seat_ok=True)
    for sr in spec.get("subrooms", []):
        for fx in sr.get("fixtures", []):
            place_massing(fx.get("kind", "block"), fx.get("name", "fix"),
                          (fx["x"] + dx_mm) * MM, (fx["y"] + dy_mm) * MM,
                          fx["w"] * MM, fx["d"] * MM, max(fx.get("h", 400) * MM, 0.02),
                          fx.get("rot", 0), 0.0, white, white, coll)


# --------------------------------------------------------------------------------- labels
_FONT = None


def _font():
    global _FONT
    if _FONT is not None:
        return _FONT or None
    for p in (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try:
                _FONT = bpy.data.fonts.load(p)
                return _FONT
            except Exception:
                pass
    _FONT = False
    return None


def add_label(text, x_m, y_m, coll, size=0.5, z=0.05):
    cu = bpy.data.curves.new(text[:40], type='FONT')
    cu.body = text
    cu.size = size
    cu.extrude = 0.012
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    f = _font()
    if f:
        cu.font = f
    ob = bpy.data.objects.new(f"label__{text[:24]}", cu)
    ob.location = (x_m, y_m, z)
    ob.data.materials.append(matp("lbl"))
    _link(ob, coll)
    return ob


# ------------------------------------------------------------------------------- scene
def new_collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def scene_bbox():
    import mathutils
    xs, ys, zs = [], [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for c in ob.bound_box:
            wc = ob.matrix_world @ mathutils.Vector(c)
            xs.append(wc.x)
            ys.append(wc.y)
            zs.append(wc.z)
    if not xs:
        return (0, 0, 0, 10, 6, 3)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def add_cameras(bb):
    import mathutils
    x0, y0, z0, x1, y1, z1 = bb
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    span = max(x1 - x0, y1 - y0)
    persp = bpy.data.cameras.new("Overview3q")
    persp.lens = 38
    co = bpy.data.objects.new("Overview_3q", persp)
    loc = mathutils.Vector((cx - span * 0.05, y0 - span * 0.38, z1 + span * 1.1))
    co.location = loc
    co.rotation_euler = (mathutils.Vector((cx, cy, z0)) - loc).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(co)

    top = bpy.data.cameras.new("TopPlan")
    top.type = 'ORTHO'
    # ortho_scale maps to the render's LONGER (horizontal) axis, so a plan taller than
    # width*aspect gets cropped top/bottom (was clipping the ensuite tub). Fit BOTH dims.
    aspect = 2600.0 / 1700.0                       # matches scn.render resolution in set_engine
    top.ortho_scale = max(x1 - x0, (y1 - y0) * aspect) * 1.06
    to = bpy.data.objects.new("Top_Plan", top)
    to.location = (cx, cy, z1 + span)
    to.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.scene.collection.objects.link(to)
    bpy.context.scene.camera = co


def add_lighting():
    scn = bpy.context.scene
    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.80, 0.83, 0.87, 1.0)
        bg.inputs[1].default_value = 0.5             # softer ambient (was blowing out)
    sun = bpy.data.lights.new("Sun", type='SUN')
    sun.energy = 1.7
    sun.angle = 0.3                                  # soft shadows
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(22), math.radians(6), math.radians(35))  # near-overhead, short shadows
    bpy.context.scene.collection.objects.link(so)


def set_engine():
    scn = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scn.render.engine = eng
            break
        except Exception:
            continue
    try:
        scn.eevee.taa_render_samples = 24
    except Exception:
        pass
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.exposure = -0.7           # keep whites off the clip point so colours read
    scn.render.resolution_x = 2600
    scn.render.resolution_y = 1700
    return scn.render.engine


# --------------------------------------------------------------------------------- main
def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def require_placement_gate(manifest_path, man, man_dir, repo_root, accept_review=False):
    """Enforce the 2D->3D reading gate BEFORE any geometry is built. The gate runs in system
    python (needs fitz/scipy, absent from Blender's python) and leaves placement-gate.json.
    This refuses to build unless the marker was produced from EXACTLY the files about to be
    built (manifest + each furnished scene-graph, matched by content hash) AND the verdict is
    acceptable. FAIL always blocks; REVIEW blocks until a human passes --accept-review; any
    other/missing verdict fails CLOSED. All messages are ASCII (Blender stdout is cp1252 on
    Windows — a non-ASCII glyph would crash the build). This makes the machine, not the
    owner's eyeball, the first verifier."""
    marker = os.path.join(man_dir, "placement-gate.json")
    cmd = ("    python pipeline/scripts/placement_gate.py <plan.pdf> "
           + os.path.basename(manifest_path))
    if not os.path.exists(marker):
        raise SystemExit("REFUSED: 2D->3D reading was never verified (no placement-gate.json "
                         "next to the manifest).\n  Run the gate first:\n" + cmd)
    try:
        with open(marker, encoding="utf-8") as f:
            gate = json.load(f)
    except (ValueError, OSError):
        raise SystemExit("REFUSED: placement-gate.json is unreadable/corrupt (partial write?).\n"
                         "  Re-run the gate:\n" + cmd)

    # Bind the marker to THIS build's inputs by CONTENT HASH: the manifest (offsets/furnish list
    # are gate inputs) + every furnished scene-graph must appear in the marker with a matching
    # sha1. Kills the stale-edit, manifest-edit, and 'marker from a different target in this dir'
    # holes in one check; hash beats mtime (immune to OneDrive re-sync touching timestamps).
    marker_inputs = gate.get("inputs", {})
    required = {os.path.basename(manifest_path): manifest_path}
    for rm in man.get("furnish", []):
        sp = os.path.join(repo_root, rm["spec"]) if not os.path.isabs(rm["spec"]) else rm["spec"]
        required[os.path.basename(sp)] = sp
    # walls_json is BOTH a direct build input (walls are extruded from it) and what the gate's
    # calibration check reads; bind it so a post-gate re-extraction with a wrong scale/origin
    # triple refuses the build instead of quietly extruding mis-calibrated walls off a stale marker.
    wj = man.get("walls_json")
    if wj:
        required[os.path.basename(wj)] = os.path.join(repo_root, wj) if not os.path.isabs(wj) else wj
    # the dismissals ledger can SUPPRESS a drawn piece from the completeness check, so a post-gate
    # edit -- especially DELETING a dismissal to re-open a question -- must force a re-gate. Require
    # it when it exists now OR the marker recorded one; a ledger that appeared/vanished/changed
    # after gating then lands in 'bad' (present-and-matching, or absent-in-both, is the only pass).
    ledger_path = os.path.join(man_dir, "placement-review.json")
    if os.path.exists(ledger_path) or "placement-review.json" in marker_inputs:
        required["placement-review.json"] = ledger_path
    # overlay freshness: the owner's REVIEW sign-off is made by SCANNING review-read-vs-sheet*;
    # a marker gated before the overlay changed (or an overlay deleted/added after gating) must
    # refuse exactly like a spec edit. Same present-and-matching-or-absent-in-both rule as the
    # ledger above. Logic lives in placement_gate (top level is stdlib-only, safe in Blender
    # python; HERE is already on sys.path) so this bpy module carries no decision logic.
    from placement_gate import overlay_required
    required.update(overlay_required(man_dir, marker_inputs))
    bad = []
    for name, path in required.items():
        have = _sha1(path) if os.path.exists(path) else None
        if marker_inputs.get(name) is None or have is None or marker_inputs.get(name) != have:
            bad.append(name)
    if bad:
        raise SystemExit("REFUSED: the placement gate does not match what is about to be built "
                         "(changed or never-gated: " + ", ".join(sorted(bad)) + ").\n"
                         "  Re-run the gate on THIS manifest:\n" + cmd)

    verdict = gate.get("verdict")
    if verdict not in ("PASS", "REVIEW"):     # fail-closed: FAIL / None / typo / truncated
        floats = "; ".join(f"{r.get('room','?')}: {len(r.get('floating') or [])} floating"
                           for r in gate.get("rooms", []) if r.get("floating"))
        raise SystemExit(f"REFUSED: placement gate verdict '{verdict}' (need PASS or signed REVIEW). "
                         + (floats or "a piece floats on empty floor, or the marker is invalid")
                         + ".\n  Fix the scene-graph, re-gate, then build.")
    if verdict == "REVIEW":
        if not accept_review:
            raise SystemExit("REFUSED: placement gate = REVIEW (the machine could not certify "
                             "every piece).\n  Read the checklist (run placement_gate.py), and if "
                             "the flagged items are correct, build with --accept-review.")
        print("  [!] placement gate: REVIEW accepted via --accept-review (human signed off)")
        for r in gate.get("rooms", []):
            if r.get("unplaced") or r.get("floating"):
                print(f"     [{r.get('room','?')}] {r.get('verdict','?')}  unplaced_clusters={r.get('unplaced')}")
    else:
        print("  [OK] placement gate: PASS (machine-verified reading)")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    manifest_path = next((a for a in argv if not a.startswith("-")), None)
    if not manifest_path:
        raise SystemExit("usage: build_floor.py -- <floor-manifest.json> [--render] [--out DIR] [--no-gate]")
    do_render = "--render" in argv
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else None

    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    man_dir = os.path.dirname(os.path.abspath(manifest_path))
    # Repo root is where the manifest's repo-relative spec/walls paths resolve. Do NOT assume a
    # fixed depth (a manifest can live in a stage dir OR a deeper vN subdir): walk up until a dir
    # holds the repo markers, and fall back to the historical 3-levels-up only if none is found.
    def _find_repo_root(start):
        d = start
        for _ in range(8):
            if os.path.isdir(os.path.join(d, "pipeline")) and os.path.isdir(os.path.join(d, "projects")):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
        return os.path.abspath(os.path.join(start, "..", "..", ".."))
    repo_root = _find_repo_root(man_dir)
    if not out_dir:
        out_dir = os.path.join(repo_root, "pipeline", "output", "floor2")
    # Absolute: Blender resolves a RELATIVE render.filepath against ITS cwd (often the drive
    # root), so a relative --out silently leaks renders to C:\pipeline\... instead of the repo.
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # gate: a furnished floor must pass the placement reading-check before it can be built
    if man.get("furnish") and "--no-gate" not in argv:
        require_placement_gate(manifest_path, man, man_dir, repo_root,
                               accept_review="--accept-review" in argv)
    elif "--no-gate" in argv:
        print("  [!] --no-gate: SKIPPING the placement gate (dev only - output is UNVERIFIED)")
        try:                                   # leave an audit trail so the bypass is not invisible
            with open(os.path.join(out_dir, "build-provenance.json"), "w", encoding="utf-8") as f:
                json.dump({"gate": "bypassed", "manifest": os.path.basename(manifest_path),
                           "note": "built with --no-gate; the 2D->3D reading was NOT machine-verified"},
                          f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.scene.unit_settings.system = 'METRIC'

    h_m = man.get("ceiling_mm", 2800) * MM
    thick_m = man.get("wall_render_thick_mm", 24) * MM

    # 1) faithful walls from the PDF
    walls_path = os.path.join(repo_root, man["walls_json"]) if not os.path.isabs(man["walls_json"]) else man["walls_json"]
    with open(walls_path, encoding="utf-8") as f:
        wj = json.load(f)
    segs = wj["segments"] if isinstance(wj, dict) else wj
    # 1b) doors/windows/glass (owner 2026-07-10: "ถ้าไม่ใส่เข้า model เวลา render ออกมามันก็ว่าง"):
    # cut the walls at each declared opening, then contribute glass panes / sills /
    # lintels back (floor_openings computes; heights are DISCLOSED render defaults)
    openings = []
    if man.get("openings_json"):
        op_path = man["openings_json"] if os.path.isabs(man["openings_json"]) \
            else os.path.join(repo_root, man["openings_json"])
        with open(op_path, encoding="utf-8") as f:
            openings = json.load(f).get("openings", [])
        segs, n_cut = floor_openings.clip_wall_segments(segs, openings)
        print(f"  openings: {len(openings)} declared, {n_cut} wall segments cut")
    nwall = build_walls(segs, h_m, thick_m, new_collection("WALLS_from_PDF"), man.get("clip_zones"))
    if openings:
        build_openings(openings, man.get("ceiling_mm", 2800), new_collection("OPENINGS"))

    if man.get("floor_zones"):
        build_floor_zones(man["floor_zones"], new_collection("floor_zones"))
        print(f"  floor zones: {len(man['floor_zones'])}")

    if man.get("terrace"):
        build_terrace(man["terrace"], new_collection("terrace"))
        print("  terrace + planters")

    # 2) groundplane
    if man.get("groundplane"):
        g = man["groundplane"]
        add_box("groundplane", g["x0"] * MM, g["y0"] * MM, -0.12,
                (g["x1"] - g["x0"]) * MM, (g["y1"] - g["y0"]) * MM, 0.12, matp("floor"),
                new_collection("floor"))

    # 3) trusted furniture overlay for the designed rooms
    for rm in man.get("furnish", []):
        spec_path = os.path.join(repo_root, rm["spec"]) if not os.path.isabs(rm["spec"]) else rm["spec"]
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
        coll = new_collection(f"FURN__{rm['id']}")
        build_furniture(spec, rm["offset_mm"][0], rm["offset_mm"][1], coll)
        print(f"  furnished {rm['id']:16} offset={rm['offset_mm']}")

    # 4) room labels (placed at known centres from the plan reading)
    lc = new_collection("labels")
    for lb in man.get("labels", []):
        # z from manifest (mm) — BF labels float ABOVE their cabinet so the top camera isn't
        # occluded by the box (a floor-level label under a 2.8 m box is invisible from above).
        add_label(lb["text"], lb["x"] * MM, lb["y"] * MM, lc, size=lb.get("size", 0.5),
                  z=lb.get("z_mm", 50) * MM)

    bb = scene_bbox()
    add_cameras(bb)
    add_lighting()
    eng = set_engine()

    blend = os.path.join(out_dir, "floor2.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    n_obj = len([o for o in bpy.data.objects if o.type == 'MESH'])
    print(f"\nSAVED {blend}")
    print(f"  {nwall} walls | {n_obj} mesh objects | engine {eng}")
    print(f"  bbox (m): X[{bb[0]:.2f}..{bb[3]:.2f}] Y[{bb[1]:.2f}..{bb[4]:.2f}] Z[{bb[2]:.2f}..{bb[5]:.2f}]")

    if do_render:
        scn = bpy.context.scene
        scn.camera = bpy.data.objects["Top_Plan"]
        scn.render.filepath = os.path.join(out_dir, "floor2_top.png")
        bpy.ops.render.render(write_still=True)
        scn.camera = bpy.data.objects["Overview_3q"]
        scn.render.filepath = os.path.join(out_dir, "floor2_overview.png")
        bpy.ops.render.render(write_still=True)
        print(f"  rendered floor2_top.png + floor2_overview.png")


main()
