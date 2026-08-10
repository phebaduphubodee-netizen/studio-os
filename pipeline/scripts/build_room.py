"""
build_room.py — INTERIOR-AI materializer (Layer 2: BLENDER, headless bpy).

Reads a validated room SPEC (the SAME JSON that clearance_check.py validates) and
materializes it as an editable Blender scene: room shell (floor + 4 walls + a real
door opening) + furniture boxes, all dimensionally correct, then frames a draft
camera + sun and (optionally) renders a Cycles still. Runs with NO human at the GUI:

    blender -b --factory-startup --python pipeline/build_room.py -- pipeline/specs/living_demo.json
    blender -b --factory-startup --python pipeline/build_room.py          # uses DEFAULT_SPEC

Geometry is built with the DATA API only (bpy.data.*, mesh.from_pydata) — never
bpy.ops for geometry, which dies with "poll() failed" in --background. (bpy.ops is
fine for save + render; those work headless.) Saves output/room_<type>.blend
(+ .png if the spec sets "render": true).

This is the MATERIALIZER. The differentiator (dimensional correctness) lives in the
engine-agnostic clearance_check.py — run that on the spec for the PASS/WARN/FAIL report.
"""
import bpy
import math
import os
import sys
import json

IN = 0.0254   # inches -> metres

# Render realism defaults (knowledge/rendering/render-defaults.md §8.3-§8.4). Encoded so the draft
# render obeys the architectural conventions instead of looking like generic CG.
EYE_LEVEL_M = 1.6        # §8.3 camera eye level ~5'3"
RENDER_FOCAL_MM = 28     # §8.3 interior focal length 24-50mm (low distortion)
RENDER_SHIFT_Y = -0.10   # NEGATIVE vertical lens shift: frame DOWN toward the floor/furniture
                         # (positive would frame up into the open void above the ceiling), WITHOUT
                         # tilting the camera so two-point is preserved. Verified vs Blender docs.
BEVEL_WIDTH_M = 0.001    # §8.4 ~1mm edge bevel so every edge catches a highlight

# furniture.py is pure-python (no bpy) and lives next to this script.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import furniture
import millwork       # bpy-free pure logic: built-in joinery layout (METRES) + the model-fit gate
import casement_sheers as _csheers   # bpy-free pure logic: sill-length sheers inside the two
                                     # west casement reveals (element 6 D-E6-1) — layout derives
                                     # from each opening's OWN sill/head, alpha pinned cross-block
                                     # to curtains.render_state (ONE sheer identity)
import curtains       # bpy-free pure logic: fabric ribbons from curtain_track/curtains spec data —
#   data the canonical spec carried since 2026-07-16 with NO consumer, so every render showed bare
#   glass where the owner decided fabric (3ce5f5e measured that omission as a "pale band" finding)
import exterior       # bpy-free pure logic: the view OUT of the glass — spec-declared garden HDRI
#   + the Juliet rail the owner's photo shows outside the slider (option B, 2026-07-17b). Same law:
#   the studio-HDRI default must not be able to silently override a decided exterior.
import element5_lighting as _e5   # bpy-free pure logic: the 3 real light layers (element 5) —
                       # ambient grids clipped out of full-height masses + mirror task strips/bar
                       # + BF14/tub accent spots + lamp glow, all DERIVED from spec.lighting
                       # (schema e5-layers@0.1); malformed/missing referents RAISE (831fc1b law).
import styling       # bpy-free pure logic: ELEMENT 8 styling derived from built parts
import softgoods     # bpy-free pure logic: ELEMENT 8 compliant-surface vocabulary
import drape         # LAYER 2 (uses bpy): Blender's own cloth solver, baked headless and
#                      frozen to static meshes. Element 8 hand-wrote cloth mathematics and
#                      then DISABLED the foot throw for want of "a collision term"; the
#                      solver has had one all along (see drape.py's header for the probe).
import wardrobe_bay   # bpy-free pure logic: the wardrobe-bay dressing gallery (open oak+brass
                      # dressing masses + a mirror niche + one closed cool anchor; element 7).
                      # Routed BY SUBROOM TYPE in build_suite so no bay fixture can fall through
                      # to the bathroom lane's silent [] -> fix__ white slab (D-E7-3 merge
                      # ruling; bathroom.py byte-untouched).
import bathroom       # bpy-free pure logic: ensuite sanitaryware massing (element 4). Subroom
#   fixtures used to render as ONE plain box each (the crude v4); this emits per-part boxes with
#   material ROLES that route to the SAME suite materials (oak/caesarstone/brass/glass) by name.
import quicklook      # bpy-free pure logic: R5 playblast-ladder rung (--quick) — cheap
                      # first LOOK before any full-fidelity frame; kills bad work
                      # early, never certifies good work
import asset_scale as _ascale   # bpy-free: glTF bounds, scale assertion, PBR map roles
import camera_config   # eye-camera height + its coupled LOS threshold (M3.2 designer-cited, testable)
import placement_gate  # bpy-free pure logic: scene_zone_decision (owner-signed below_grade -> excluded)
import floor_openings  # bpy-free pure logic: opening TYPE -> sill/head render defaults + the
#   sliding two-leaf rule. ONE schema for openings across build_floor (plan slabs) and build_room
#   (polygon edges); build_room used to know only a single `door` key and rendered a sealed box.

# Fallback if no spec is passed on the CLI. Mirrors pipeline/specs/living_demo.json.
DEFAULT_SPEC = {
    "room": {"type": "living", "width_in": 168, "depth_in": 192, "ceiling_in": 96,
             "wall_thk_in": 4.5, "floor_thk_in": 4.0,
             "door": {"w_in": 32, "h_in": 80, "wall": "south"}},
    "render": False,
    "items": [
        {"name": "sofa", "kind": "sofa", "x": 24, "y": 12, "w": 84, "d": 36, "h": 34},
        {"name": "coffee table", "kind": "coffee_table", "x": 45, "y": 64, "w": 42, "d": 22, "h": 18},
    ],
}


def clear_scene():
    """Start clean so re-runs are deterministic (removes the default cube too)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def add_box(name, x, y, z, dx, dy, dz):
    """Editable cuboid object (corner at x,y,z; size dx,dy,dz, metres). Built from
    mesh data (not bpy.ops) so it is reliable in --background mode."""
    v = [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
    ]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(v, [], f)
    mesh.validate()
    mesh.update()
    # from_pydata gives inconsistent winding (bottom face normal points UP, etc.); recalc
    # OUTWARD so the Bevel modifier offsets correctly (bad normals flare the bevel into thin
    # self-intersecting skirts that read as translucent under high-contrast lighting).
    import bmesh
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def add_camera_and_light(w, d, h):
    """Draft camera + sun following the KB §8.3 architectural-render rules: a
    TWO-POINT-perspective camera (kept LEVEL so verticals stay vertical) at ~1.6m eye
    level, 28mm lens, framed with a vertical lens SHIFT instead of tilting up/down.
    Final framing/lighting taste stays human; this yields a correct, non-distorted preview."""
    from mathutils import Vector
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = RENDER_FOCAL_MM                      # §8.3 24-50mm
    cam_data.sensor_fit = 'HORIZONTAL'                   # make the 28mm h-FOV explicit / size-stable
    eye = max(0.4, min(EYE_LEVEL_M, h - 0.3))            # ~5'3", clamped under ceiling + above floor
    setback = min(0.6, 0.15 * min(w, d))                # scale corner setback so tiny rooms don't clip
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    loc = Vector((w - setback, setback, eye))           # a corner, at eye level, inside the room
    # Look HORIZONTALLY across the room — target at the SAME height as the camera, so the
    # view direction has no vertical component => the camera is level => verticals stay
    # vertical (two-point). Tilting the camera up/down is what creates three-point distortion.
    look = Vector((w * 0.35, d * 0.7, eye))
    cam.location = loc
    cam.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler()
    cam_data.shift_y = RENDER_SHIFT_Y                    # frame the room vertically without tilting
    bpy.context.scene.camera = cam

    # Key light: a Sun is a DIRECTIONAL light — only its rotation matters (Blender ignores a
    # Sun's location), so we set rotation only. Soft fill comes from the world ambient (_environment).
    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (0.6, 0.1, 0.4)
    bpy.context.scene.collection.objects.link(sun)


def _outdir():
    here = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
    out = os.path.join(os.path.dirname(here), "output")
    os.makedirs(out, exist_ok=True)
    return out


def _d1_floor_mp():
    """The standard's D1 resolution floor, in megapixels.

    Read from `qa/deliverable-standard.json` — the file whose thresholds are
    percentiles of 658 delivered frames — and NOT copied into this file, so a
    re-cut census cannot leave the renderer pointing at a stale number. Missing or
    unreadable is a HARD failure on the deliverable path: 'I could not find the
    floor' must never render like 'the floor is fine' (R11's exit-code contract).
    """
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(repo, "qa", "deliverable-standard.json"), encoding="utf-8") as f:
        return float(json.load(f)["rows"]["D1"]["threshold"])


def _score_deliverable(name, quick=False, frame=True):
    """R11 applied to the rows that carry the weight: the render path DUMPS the
    built scene and SCORES it, instead of asserting things about it.

    WHY IT IS HERE AND NOT LEFT TO A HUMAN. `deliverable_check`'s scene rows are
    MANDATORY, and until this call existed nothing on this lane produced a scene for
    them. The reader that did exist read a TRN-002 SPEC, scored the DELIV-001 lane
    0/0/0, and passed both mandatory rows — on which 63 of the 96 eye frames on disk
    qualified as delivered-level, rounds the owner called nowhere near done among
    them. An instrument nothing calls is how that survives.

    OUT OF PROCESS FOR THE SCORER, IN PROCESS FOR THE DUMP, and that split is the
    layer law rather than a convenience: `scene_dump` needs bpy and we are already
    inside Blender; `deliverable_check` needs numpy and PIL, which Blender's bundled
    Python does not have, and teaching it to read pixels through `bpy` would drag a
    layer-1 gate into layer 2. Spawned, not printed — an interpreter that cannot be
    found is a hard stop, because a gate that could not run must never read like one
    that passed (the same contract as R11's pixel rung).

    IT DOES NOT FAIL THE BUILD ON A LOW SCORE, and that is deliberate. The standard
    is an OUTCOME bar, not a pre-render rule: P2 through P4 exist precisely to climb
    it, so failing the render while the frame is below it would stop the work that
    raises it. Exit 2 — could not run — IS a hard stop.
    """
    import shutil
    import subprocess
    import scene_dump
    out = _outdir()
    dump_path = os.path.join(out, f"room_{name}.scene.json")
    objs = scene_dump.dump()
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump({"blend": bpy.data.filepath, "schema": "scene-dump@1",
                   "objects": objs}, f, indent=1, ensure_ascii=False)
    print(f"  scene dump: {len(objs)} mesh objects -> {dump_path}")
    py = next((p for p in (shutil.which("python3"), shutil.which("python")) if p), None)
    if py is None:
        print("BUILD FAILED: no plain python interpreter on PATH to run "
              "deliverable_check (Blender's has no PIL/numpy). Refusing to finish a "
              "deliverable render whose scene rows could not be started.")
        sys.stdout.flush()
        os._exit(1)
    cmd = [py, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "deliverable_check.py"), "--scene-dump", dump_path]
    if frame and not quick:
        cmd.insert(2, os.path.join(out, f"room_{name}.png"))
    elif quick:
        # The image rows are measured after a resample to a 1600 px long edge, so a
        # half-size playblast is UPSAMPLED into the measurement while a deliverable
        # is DOWNSAMPLED into it — a different operation on the octave D5 reads. And
        # D1 is measured on the original, where a quick frame fails for a reason
        # that says nothing about the room. The SCENE rows are geometry and hold at
        # either rung, so those are what the quick run scores.
        print("  SCORE -- quick rung: image rows NOT RUN (a playblast is not the "
              "deliverable's size); scene rows below are valid at this rung")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    out = r.stdout or ""
    for ln in out.splitlines():
        print(f"SCORE {ln}")
    # The policy is layer-1 and lives in rule_gate beside pixel_exit_policy, for the
    # reason that one records: a policy a plain python process cannot import is a
    # policy nobody tests, and the last untested one inverted its own meaning.
    import rule_gate as _RG
    action, msg = _RG.score_exit_policy(r.returncode, out)
    if action == "note":
        print("SCORE -- " + msg)
    elif action == "stop":
        for ln in (r.stderr or "").splitlines()[-6:]:
            print(f"SCORE !! {ln}")
        print("BUILD FAILED: " + msg)
        sys.stdout.flush()
        os._exit(1)


def configure_cycles(samples=128, res=None):
    """Pin the engine of record + device + sampling. CYCLES because EEVEE needs EGL/Xvfb
    and is unsafe headless (pipeline/CLAUDE.md).

    2026-07-22: extracted from render(), because it used to run AFTER save() — so every
    .blend this studio has ever shipped recorded Blender 5.1's factory default,
    BLENDER_EEVEE at 4096 samples. Two consequences, both real: the deliverable did not
    reproduce the PNG lying beside it, and anyone opening it headless takes exactly the
    EGL/Xvfb path the law above forbids. The rule was written at this call site and
    broken by its own ordering. Now whatever writes a file pins it first."""
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for dt in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
            try:
                prefs.compute_device_type = dt
                prefs.get_devices()
                if any(getattr(dev, "type", "CPU") != 'CPU' for dev in prefs.devices):
                    break
            except Exception:
                continue
        for dev in prefs.devices:
            dev.use = True
        scn.cycles.device = 'GPU'
    except Exception as e:
        scn.cycles.device = 'CPU'
        print(f"  (GPU setup failed, CPU fallback: {e})")
    scn.cycles.samples = samples
    try:
        scn.cycles.use_adaptive_sampling = True          # spend samples where noise remains
        scn.cycles.adaptive_threshold = 0.01
    except Exception:
        pass
    try:
        scn.cycles.use_denoising = True                  # clean up noise at modest samples
        scn.cycles.denoiser = 'OPENIMAGEDENOISE'         # CPU/GPU, always available headless
    except Exception:
        pass
    if res:
        scn.render.resolution_x, scn.render.resolution_y = res
    return scn


def save(name, samples=128, res=None):
    """Write the .blend deliverable. Takes the render settings so the saved file
    REPRODUCES the PNG rendered next to it — pass what render() will be given."""
    configure_cycles(samples, res)
    path = os.path.join(_outdir(), f"room_{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"  saved: {path} (engine={bpy.context.scene.render.engine} "
          f"samples={bpy.context.scene.cycles.samples})")


def render(name, samples=128, res=(1600, 1000)):
    scn = configure_cycles(samples, res)
    scn.render.filepath = os.path.join(_outdir(), f"room_{name}.png")
    print(f"  cycles device={scn.cycles.device} samples={scn.cycles.samples} -> rendering ...")
    bpy.ops.render.render(write_still=True)   # 'render' op is headless-safe (unlike geometry ops)
    print(f"  rendered: {scn.render.filepath}")


def albedo_plausible(rgb):
    """KB §8.1: a physically-plausible dielectric albedo sits ~0.04-0.94 (avoid pure
    black/white, which don't occur in real materials). Returns (ok, message). PURE
    function (no bpy) so it is unit-testable without Blender."""
    lo, hi = 0.04, 0.94
    bad = [round(float(c), 3) for c in tuple(rgb)[:3] if c < lo or c > hi]
    return (not bad, None if not bad else f"albedo channels outside {lo}-{hi}: {bad}")


def _basic_materials():
    """Neutral PBR materials so a Cycles render reads as a room (KB §8.1: base color +
    ROUGHNESS, with an albedo plausibility flag). Assigned by object-name prefix."""
    def mat(name, rgba, rough):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        # Prefer a TYPE lookup over the English node name (robust to a localized UI / rename).
        bsdf = m.node_tree.nodes.get("Principled BSDF") or next(
            (n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            ok, msg = albedo_plausible(rgba)
            if not ok:
                print(f"  !! albedo WARN [{name}]: {msg} (KB §8.1 — implausible base color)")
            bsdf.inputs["Base Color"].default_value = rgba
            bsdf.inputs["Roughness"].default_value = rough
        return m
    floor_m = mat("floor_mat", (0.80, 0.78, 0.74, 1.0), 0.35)   # semi-matte wood/LVT
    wall_m = mat("wall_mat", (0.92, 0.92, 0.90, 1.0), 0.85)     # matte paint
    furn_m = mat("furniture_mat", (0.45, 0.50, 0.62, 1.0), 0.55)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        n = obj.name
        m = floor_m if n == "floor" else (wall_m if n.startswith("wall") else furn_m)
        obj.data.materials.append(m)


def _environment(warm=False):
    """KB §8.2 + §8.6: a lone hard Sun reads flat/harsh, so add a soft neutral WORLD
    ambient (basic image-based fill that lifts shadowed walls beyond GI bounce), and PIN
    the view transform so the tone-mapped look is deterministic across Blender versions
    (AgX in 4.x, Filmic in 3.6) instead of shipping a raw/un-tonemapped image. DRAFT levels
    — final lighting taste stays human. `warm=True` (the metric suite) warms the fill and
    lifts exposure because interior lights carry the scene (not a bare open-top sun)."""
    scn = bpy.context.scene
    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        if warm:
            bg.inputs["Color"].default_value = (0.86, 0.83, 0.78, 1.0)   # soft warm fill
            bg.inputs["Strength"].default_value = 0.30
        else:
            bg.inputs["Color"].default_value = (0.82, 0.86, 0.92, 1.0)   # faint cool-sky fill
            # Keep the fill LOW relative to the sun key: a strong fill flattens the image
            # (no shadow contrast) = the classic "sterile CG" tell. This is a soft lift only.
            bg.inputs["Strength"].default_value = 0.12                    # soft ambient (DRAFT)
    for vt in ("AgX", "Filmic"):                                      # first that exists wins
        try:
            scn.view_settings.view_transform = vt
            break
        except Exception:
            continue
    # Open-top room: trim exposure so light materials don't blow out. The warm/interior-lit
    # suite needs far less trim than the bare-sun rectangular preview.
    try:
        scn.view_settings.exposure = -0.4 if warm else -1.2
    except Exception:
        pass


MILL_BEVEL_M = 0.0012   # joinery arris: a cabinet edge is nearly sharp, not a 5mm round-over

# ELEMENT 8: the styling layer's anchor registry — every millwork part the build actually
# emitted, in absolute metres. Filled by _build_millwork and by the wardrobe-bay routes;
# consumed by _add_styling. Cleared per build in build_suite (a module-level list that is
# never reset would carry one room's rails into the next room's render).
_STYLE_ANCHORS = []
# What the cloth solver actually FROZE this run. The anti-repaint armour keys the bed's
# fabric bits off this rather than off the spec, because whether a piece of simulated
# cloth exists is decided by a search over real bakes, not by anything a pure re-run can
# predict. A name in here is a promise the render can be held to.
_SOFT_BAKED = []


def _bevel_edges(width_m=BEVEL_WIDTH_M, segments=2):
    """KB §8.4: no real edge is perfectly sharp — a ~1mm bevel lets every edge catch a
    highlight, which is one of the biggest 'CG vs photoreal' tells. Non-destructive
    Bevel modifier, so the geometry stays editable.

    PER-OBJECT OVERRIDE (`mill_bevel`): the suite pass runs this at 5 mm, which is *wider than the
    3 mm joinery reveal* millwork.py exists to cast. The reveals do survive it (verified in a
    render crop) but come out mushy, and a 5 mm round-over on a cabinet door is not a thing that
    exists. Millwork parts therefore carry their own arris. NOTE: we deliberately do NOT tag them
    `ph_model` to escape the wide bevel — that key ALSO makes paint_materials skip the object, so
    the wardrobe would lose its walnut and render as bare grey."""
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or obj.get("ph_model"):   # don't bevel imported detailed models
            continue
        mod = obj.modifiers.new(name="edge_bevel", type='BEVEL')
        mod.width = obj.get("mill_bevel", width_m)
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = 0.5236   # ~30deg: only bevel sharp-ish edges


MM = 0.001   # millimetres -> metres (room-spec@0.2 is metric)


def _signed_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def add_wall(name, p1, p2, outward, thk, h, z0=0.0):
    """A wall prism along edge p1->p2 (metres), extruded OUTWARD by thk and UP by h from z0."""
    ax, ay = p1; bx, by = p2
    cx, cy = bx + outward[0] * thk, by + outward[1] * thk
    dx2, dy2 = ax + outward[0] * thk, ay + outward[1] * thk
    z1 = z0 + h
    v = [(ax, ay, z0), (bx, by, z0), (cx, cy, z0), (dx2, dy2, z0),
         (ax, ay, z1), (bx, by, z1), (cx, cy, z1), (dx2, dy2, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(v, [], f); mesh.validate(); mesh.update()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    return obj


def add_poly_floor(name, outline_m, fth):
    """Floor slab: the outline polygon from z=-fth to z=0 (n-gon top/bottom + side quads)."""
    n = len(outline_m)
    verts = [(x, y, -fth) for x, y in outline_m] + [(x, y, 0.0) for x, y in outline_m]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(verts, [], faces); mesh.validate(); mesh.update()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    return obj


def _door_on_edge_m(door, p1, adir, L):
    """If `door` (mm) lands on this edge, return (u0,u1,door_h_m) to leave a gap; else None."""
    if not door:
        return None
    dx = float(door["x"]) * MM; dy = float(door["y"]) * MM
    dw = float(door.get("w", 900)) * MM; dh = float(door.get("h", 2000)) * MM
    wall = door.get("wall", "south")
    horiz = abs(adir[1]) < 1e-6; vert = abs(adir[0]) < 1e-6
    on = ((wall in ("south", "north") and horiz and abs(dy - p1[1]) < 0.05) or
          (wall in ("east", "west") and vert and abs(dx - p1[0]) < 0.05))
    if not on:
        return None
    u = (dx - p1[0]) * adir[0] + (dy - p1[1]) * adir[1]
    u0 = max(min(u, u + dw), 0.0); u1 = min(max(u, u + dw), L)
    return (u0, u1, dh) if (u1 - u0) > 1e-4 else None


def _openings_on_edge_m(openings, p1, adir, L, h, tol=0.06):
    """The room-spec@0.2 `room.openings` that lie ON this polygon edge.

    WHY THIS EXISTS (2026-07-12, adversarial review). build_room only ever honoured a single
    `door` key, so a room-spec carrying the openings its plan actually draws rendered as a
    SEALED SHOEBOX -- floor + 4 blank walls. bluehouse_plan_reader found the living zone's
    3200 mm south slider and 2900 mm east slider from the ink and then DROPPED them on the way
    into the spec. A room you cannot see out of is not the room the plan draws.

    An opening is `{"id","type","rect":[x0,y0,x1,y1] mm, "sill_mm"?, "head_mm"?}` -- the same
    record floor_openings.py consumes, so ONE schema drives both the whole-floor build
    (build_floor, plan-rect slabs) and this polygon-edge build. sill/head come from
    floor_openings.DEFAULTS: they are DISCLOSED RENDER DEFAULTS, not measurements (no plan
    sheet carries a sill height).

    Returns [(u0, u1, sill_m, head_m, type, id)] in edge-parameter metres, sorted by u0."""
    out = []
    for o in openings or ():
        r = [float(v) * MM for v in o["rect"]]
        x0, y0 = min(r[0], r[2]), min(r[1], r[3])
        x1, y1 = max(r[0], r[2]), max(r[1], r[3])
        horiz = abs(adir[1]) < 1e-6
        if horiz:                                  # edge runs along x, at y = p1[1]
            if not (y0 - tol <= p1[1] <= y1 + tol):
                continue
            ua = (x0 - p1[0]) * adir[0]
            ub = (x1 - p1[0]) * adir[0]
        else:                                      # edge runs along y, at x = p1[0]
            if not (x0 - tol <= p1[0] <= x1 + tol):
                continue
            ua = (y0 - p1[1]) * adir[1]
            ub = (y1 - p1[1]) * adir[1]
        u0, u1 = max(0.0, min(ua, ub)), min(L, max(ua, ub))
        if u1 - u0 <= 1e-4:
            continue
        t = o.get("type", "opening")
        d = floor_openings.DEFAULTS.get(t, floor_openings.DEFAULTS["opening"])
        sill = float(o.get("sill_mm", d["sill_mm"]) or 0.0) * MM
        head = o.get("head_mm", d["head_mm"])
        head = float(head) * MM if head is not None else h
        out.append((u0, u1, sill, min(head, h), t, o.get("id", t)))
    return sorted(out)


def _glaze_edge(name, p1, a, out, thk, u0, u1, z0, z1):
    """The pane that fills an opening: a slab across the WHOLE wall thickness, sill..head."""
    s = lambda u: (p1[0] + a[0] * u, p1[1] + a[1] * u)
    return add_wall(name, s(u0), s(u1), out, thk, z1 - z0, z0=z0)


def poly_walls_bpy(prefix, outline_m, thk, h, door, openings=None):
    """Build every wall of a polygon (outward normals from the winding), with the door gap +
    header AND every declared opening CUT into the wall and GLAZED.

    Per edge: the openings on it are cut out; the wall is built as the pieces BETWEEN them,
    plus a sill band (0..sill) and a lintel (head..ceiling) per opening, plus the pane itself.
    `sliding` gets two overlapping panes on two tracks (owner 2026-07-10: a monolithic sheet of
    glass reads as a fixed wall, not an operable door) -- the same rule floor_openings applies.
    `door` / `opening` contribute no pane: an honest hole."""
    import math
    ccw = _signed_area(outline_m) > 0
    n = len(outline_m)
    n_cut = n_pane = 0
    for i in range(n):
        p1 = outline_m[i]; p2 = outline_m[(i + 1) % n]
        dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        a = (dx / L, dy / L)
        out = (a[1], -a[0]) if ccw else (-a[1], a[0])
        s = lambda u: (p1[0] + a[0] * u, p1[1] + a[1] * u)
        gaps = _openings_on_edge_m(openings, p1, a, L, h)
        d = _door_on_edge_m(door, p1, a, L)
        if d:                                       # the legacy `door` key: a full-height hole
            gaps = sorted(gaps + [(d[0], d[1], 0.0, min(d[2], h), "door", "door")])
        if not gaps:
            add_wall(f"wall_{prefix}{i}", p1, p2, out, thk, h)
            continue
        cursor = 0.0
        for k, (u0, u1, sill, head, typ, oid) in enumerate(gaps):
            u0, u1 = max(u0, cursor), max(u1, cursor)
            if u1 - u0 <= 1e-4:
                continue
            if u0 - cursor > 1e-4:                                    # solid pier before it
                add_wall(f"wall_{prefix}{i}p{k}", s(cursor), s(u0), out, thk, h)
            if sill > 1e-4:                                           # sill band under it
                add_wall(f"wall_{prefix}{i}s{k}", s(u0), s(u1), out, thk, sill)
            if h - head > 1e-4:                                       # lintel over it
                add_wall(f"wall_{prefix}{i}l{k}", s(u0), s(u1), out, thk, h - head, z0=head)
            if typ in ("window", "glass", "sliding"):
                if typ == "sliding":                                  # two leaves, two tracks
                    ov = floor_openings.SLIDING_OVERLAP_MM * MM
                    mid = (u0 + u1) / 2.0
                    _glaze_edge(f"glass__{prefix}{i}_{k}a", p1, a, out, thk / 2.0,
                                u0, min(u1, mid + ov), sill, head)
                    b1 = (p1[0] + out[0] * thk / 2.0, p1[1] + out[1] * thk / 2.0)
                    _glaze_edge(f"glass__{prefix}{i}_{k}b", b1, a, out, thk / 2.0,
                                max(u0, mid - ov), u1, sill, head)
                    n_pane += 2
                else:
                    _glaze_edge(f"glass__{prefix}{i}_{k}", p1, a, out, thk, u0, u1, sill, head)
                    n_pane += 1
            elif typ == "railing":
                add_wall(f"wall_{prefix}{i}r{k}", s(u0), s(u1), out, thk, head - sill, z0=sill)
            n_cut += 1
            cursor = u1
        if L - cursor > 1e-4:
            add_wall(f"wall_{prefix}{i}z", s(cursor), p2, out, thk, h)
    if n_cut:
        print(f"  openings: {n_cut} cut into the walls, {n_pane} glass pane(s) glazed back in")
    return n_cut, n_pane


def add_suite_camera(x0, x1, y0, y1, h):
    """3/4 elevated 'dollhouse' view looking down into the open-top room (best for showing
    an L-shaped multi-zone layout). Sun + world fill reuse the same realism defaults."""
    from mathutils import Vector
    W = x1 - x0; D = y1 - y0
    cam_data = bpy.data.cameras.new("Camera"); cam_data.lens = 42   # a touch long -> furniture reads bigger
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    # High 3/4 dollhouse: with a full-height feature wall dividing an open-top L, a steep
    # overview is the only angle that reads the WHOLE furnished room without the wall
    # broadsiding the lens (a magazine hero of one zone is a separate, closer shot).
    eye = Vector((x0 - 0.30 * W, y0 - 0.35 * D, h + 0.80 * max(W, D)))
    tgt = Vector((x0 + 0.50 * W, y0 + 0.50 * D, 0.2))
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    # Softer daylight fill through the open top; the warm interior lights carry the room.
    sun_data = bpy.data.lights.new("Sun", type='SUN'); sun_data.energy = 1.4
    try:
        sun_data.angle = 0.15                    # a soft sun disc -> softer shadows
    except Exception:
        pass
    sun = bpy.data.objects.new("Sun", sun_data); sun.rotation_euler = (0.65, 0.15, 0.5)
    bpy.context.scene.collection.objects.link(sun)


def add_suite_eye_camera(spec, outline_m, h):
    """v0.3 EYE-LEVEL interior camera for suites (--eye). The dollhouse overview reads
    as a 'modular unit' to the critique gate (bedroom_suite 2026-07-02: room_context 3/5,
    dinged exactly for that) — this is the client-facing angle instead. Generic: aim at
    the LARGEST loose item (the bed, in a bedroom) from the farthest inset room corner
    that has a clear eye-level line of sight past sub-room walls / full-height millwork.
    Camera kept LEVEL (§8.3 two-point: verticals stay vertical); shift_y frames down."""
    from mathutils import Vector
    # The pure-geometry solve — aim (EYE_AIM override / largest non-rug / group-rug),
    # the stand-vs-ray obstacle split, the free-floor grid + line-of-sight, the farthest
    # clear spot and the hero-sized lens — lives in camera_config.solve_eye_camera so it
    # has ONE definition shared with placement_logic's "camera has a reason" gate (which
    # predicts a render-time abort BEFORE Blender launches — no split-brain). This
    # function now only turns the solved numbers into Blender camera + fill objects.
    try:
        sol = camera_config.solve_eye_camera(spec, outline_m)
    except camera_config.EyeCameraError as e:
        raise SystemExit(f"--eye {e}")
    ex, ey, tx, ty = sol["ex"], sol["ey"], sol["tx"], sol["ty"]
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = sol["lens_mm"]
    cam_data.sensor_fit = 'HORIZONTAL'
    _eye_h = camera_config.EYE_CAM_HEIGHT_M  # designer 1.0–1.2 m (M3.2 GS-15; was 1.5); env EYE_CAM_HEIGHT_M for A/B
    eye = Vector((ex, ey, _eye_h))
    tgt = Vector((tx, ty, _eye_h))           # LEVEL look -> two-point preserved
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    _sv = sol.get("shift_y")                 # manual eye_camera.shift_y override (camera_config)
    cam_data.shift_y = RENDER_SHIFT_Y if _sv is None else float(_sv)  # frame down without tilting (two-point kept)
    try:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = (tgt - eye).length
        # lane B (ground-truth study): every pro scene camera measured f/1.4-2.4;
        # our f/9 was past even asset-turnaround aperture. The story pair opens to
        # STORY_FSTOP; the CD/documentation state keeps its crisp f/9.
        cam_data.dof.aperture_fstop = _e5.STORY_FSTOP if _LIGHT_STORY else 9.0
    except Exception:
        pass
    bpy.context.scene.camera = cam
    # soft cool fill from behind the lens: the eye shot runs ENCLOSED (ceiling on), so
    # without it the room is downlights-only and the gate dings 'flat lighting' again.
    # lane B: in the story state this fill DEMOTES (study: our strongest source was
    # this cool fill = the measured no-key signature; a fill must never out-power keys)
    fill_data = bpy.data.lights.new("Fill", type='AREA')
    fill_data.energy = 60 * _e5.story_scales(_LIGHT_STORY)["fill"]
    fill_data.size = 2.0
    try:
        fill_data.color = (0.85, 0.90, 1.0)
    except Exception:
        pass
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (ex, ey, h - 0.25)
    fill.rotation_euler = (Vector((tx, ty, 0.8)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(fill)


# material family per furniture KIND, so a sofa reads as fabric and a table as wood.
# Sourced from material_defaults (shared with rationale.py) so the "what renders as
# what" mapping has ONE definition and the explainability layer can never drift from it.
import material_defaults as _matdef
# spec-selectable presets (owner's hand on materials; pure stdlib, testable outside bpy).
# NO materials block in the spec == every legacy hardcoded default below, unchanged.
import material_presets as _matpre
# the suite's soft goods as a TONAL LADDER (pure; validates itself on import). Every
# textile colour the bespoke builders used to type by hand now comes from here BY NAME —
# see value_ladder.py for the measurement that made it necessary.
import value_ladder as _vl
# The dark furniture-leg tone, ONE definition. _build_bench and _build_tub_chair each held
# their own copy (0.26/0.21/0.16 vs 0.24/0.19/0.14) under docstrings that each said the
# other's was theirs. Not a soft good, so it is not a value_ladder rung — but it is the same
# drift, and one name is the same cure.
_DARK_LEG = (0.26, 0.21, 0.16, 1.0)
_FABRIC = _matdef.FABRIC_KINDS
_WOODEN = _matdef.WOODEN_KINDS


def _mat_tag(kind):
    if kind in _FABRIC:
        return "fab"
    if kind in _WOODEN:
        return "wood"
    return "furn"


def _proc_wood(name, base=(0.34, 0.22, 0.13, 1.0), dark=(0.20, 0.12, 0.06, 1.0), rough=0.4):
    """A procedural wood material (plank BANDS + noise grain + micro bump). No texture
    files (no network here). Guarded: any node/socket mismatch falls back to a flat base."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF") or next(
        (n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        return m
    try:
        coord = nt.nodes.new("ShaderNodeTexCoord")
        mapp = nt.nodes.new("ShaderNodeMapping")
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = 'BANDS'
        wave.inputs["Scale"].default_value = 1.6
        wave.inputs["Distortion"].default_value = 2.2
        wave.inputs["Detail"].default_value = 3.0
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 14.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = dark
        ramp.color_ramp.elements[1].color = base
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.10
        nt.links.new(coord.outputs["Object"], mapp.inputs["Vector"])
        nt.links.new(mapp.outputs["Vector"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        bsdf.inputs["Roughness"].default_value = rough
    except Exception as e:
        bsdf.inputs["Base Color"].default_value = base
        bsdf.inputs["Roughness"].default_value = rough
        print(f"  (proc wood '{name}' fallback: {e})")
    return m


def _sky_environment(strength=0.55, exposure=-0.9):
    """Realistic image-based light from Blender's built-in NISHITA physical sky (no HDRI
    file needed) -> soft directional sun + colored sky bounce + real reflections. Guarded."""
    scn = bpy.context.scene
    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
        # Nishita physical sky. Blender renamed the enum across versions -> try the modern
        # 5.x names first, fall back to older ones.
        for st in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
            try:
                sky.sky_type = st
                break
            except Exception:
                continue
        for attr, val in (("sun_elevation", 0.55), ("sun_rotation", 2.3),
                          ("air_density", 1.3), ("dust_density", 1.6)):
            try:
                setattr(sky, attr, val)
            except Exception:
                pass
        nt.links.new(sky.outputs[0], bg.inputs[0])
    except Exception as e:
        bg.inputs["Color"].default_value = (0.86, 0.83, 0.78, 1.0)
        print(f"  (sky fallback: {e})")
    nt.links.new(bg.outputs[0], out.inputs[0])
    for vt in ("AgX", "Filmic"):
        try:
            scn.view_settings.view_transform = vt
            break
        except Exception:
            continue
    try:
        scn.view_settings.exposure = exposure
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PHOTOREAL helpers (2026-07-01, founder-directed "upgrade the 3D render"):
# real CC0 PBR textures (Poly Haven) + HDRI image-based light + planar UVs +
# physically-plausible Principled params. Replaces the flat/striped procedural
# look that made renders read as generic CG instead of a designed room.
# ---------------------------------------------------------------------------

def _cc0_root():
    here = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
    return os.path.join(os.path.dirname(os.path.dirname(here)), "assets", "shared", "cc0")


def _texset(slug):
    """{logical_map: local_path} for a cached Poly Haven texture set, or {} if absent."""
    import glob
    d = os.path.join(_cc0_root(), "textures", slug)
    out = {}
    for m in ("Diffuse", "nor_gl", "Rough", "Metal", "arm", "AO"):
        hits = glob.glob(os.path.join(d, f"*_{m}_*"))
        if hits:
            out[m] = hits[0]
    return out


def _hdri_file(slug):
    import glob
    for ext in ("hdr", "exr"):
        hits = glob.glob(os.path.join(_cc0_root(), "hdris", f"{slug}_*.{ext}"))
        if hits:
            return hits[0]
    return None


def _set(bsdf, key, val):
    """Version-robust Principled socket setter (socket names moved in Blender 4.x)."""
    s = bsdf.inputs.get(key)
    if s is not None:
        try:
            s.default_value = val
        except Exception:
            pass


def _principled(m):
    nt = m.node_tree
    return nt, (nt.nodes.get("Principled BSDF") or
                next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None))


def _det01(tag):
    """Deterministic pseudo-random 0..1 from a string. zlib.crc32 is stable across
    runs and processes (unlike hash(), which Python salts per process) — drives
    per-object grain offsets and per-fixture light variation so the SCENE is
    reproducible run-to-run (the camera/evidence rule). NB the rendered PNG is not
    bit-identical — Cycles GPU + adaptive sampling + OpenImageDenoise introduce
    sub-pixel noise; determinism is at the scene-graph level, which is what the
    gate evidence relies on."""
    import zlib
    return (zlib.crc32(tag.encode("utf-8")) % 10000) / 10000.0


def _planar_uv(obj, tile_m=2.0, u_off=0.0, v_off=0.0):
    """Top-down planar UV from local XY so tiled PBR maps land at real-world scale
    (repeat every tile_m). from_pydata meshes carry no UV, so image nodes would
    otherwise sample a flat colour and normal maps would have no tangent.
    u_off/v_off shift the sampling window (in tiles) so two objects sharing a
    texture don't show the SAME grain."""
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co.x / tile_m + u_off, co.y / tile_m + v_off)


def _wall_uv(obj, tile_m=2.0, u_off=0.0, v_off=0.0):
    """Vertical planar UV for a wall: (horizontal-run, Z) so a wood/stone texture reads
    upright with real-world tiling. Picks the wall's long horizontal axis (X or Y).
    u_off/v_off shift the sampling window per object (see _planar_uv)."""
    me = obj.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    along_x = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        u = co.x if along_x else co.y
        uv.data[loop.index].uv = (u / tile_m + u_off, co.z / tile_m + v_off)


def _img_node(nt, path, non_color):
    n = nt.nodes.new("ShaderNodeTexImage")
    try:
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    except Exception as e:
        print(f"  (img load fail {os.path.basename(path)}: {e})")
    return n


def _pbr_material(name, slug, base_tint=None, variation=0.0):
    """Principled material from a cached PBR set (Diffuse/nor_gl/Rough[/Metal]) on the
    object's UV. base_tint MULTIPLIES the albedo (e.g. warm a floor / darken to walnut).
    Falls back to a flat colour when the set is missing.
    variation > 0 overlays a large-scale (~2.5 m) low-contrast luminance drift in
    WORLD space so a tiled grain never repeats identically — the judge dockets
    'subtle uniformity in the wood grain across the wall panels' (PRJ-2026-002
    rolls 1+2, v004pro) trace to exact texture repeats. Keep <= ~0.08."""
    ts = _texset(slug)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, bsdf = _principled(m)
    if not bsdf:
        return m
    if not ts:
        _set(bsdf, "Base Color", base_tint or (0.6, 0.55, 0.5, 1.0))
        _set(bsdf, "Roughness", 0.5)
        return m
    if "Diffuse" in ts:
        di = _img_node(nt, ts["Diffuse"], non_color=False)
        col_out = di.outputs["Color"]
        if base_tint:
            mix = nt.nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs["Fac"].default_value = 1.0
            mix.inputs["Color2"].default_value = base_tint
            nt.links.new(col_out, mix.inputs["Color1"])
            col_out = mix.outputs["Color"]
        if variation:
            # Object coords: these from_pydata meshes keep origin (0,0,0) so local
            # == world -> the drift field is CONTINUOUS across adjacent panels.
            tc = nt.nodes.new("ShaderNodeTexCoord")
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 0.4
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = 1.0 - variation
            mr.inputs["To Max"].default_value = 1.0
            vmix = nt.nodes.new("ShaderNodeMixRGB")
            vmix.blend_type = "MULTIPLY"
            vmix.inputs["Fac"].default_value = 1.0
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            nt.links.new(mr.outputs["Result"], vmix.inputs["Color2"])
            nt.links.new(col_out, vmix.inputs["Color1"])
            col_out = vmix.outputs["Color"]
        nt.links.new(col_out, bsdf.inputs["Base Color"])
    if "Rough" in ts:
        ri = _img_node(nt, ts["Rough"], non_color=True)
        nt.links.new(ri.outputs["Color"], bsdf.inputs["Roughness"])
    if "Metal" in ts:
        mi = _img_node(nt, ts["Metal"], non_color=True)
        nt.links.new(mi.outputs["Color"], bsdf.inputs["Metallic"])
    if "nor_gl" in ts:
        ni = _img_node(nt, ts["nor_gl"], non_color=True)
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(ni.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def _solid(name, rgba, rough, metallic=0.0, sheen=0.0, coat=0.0, ior=1.5, spec=0.5,
           aniso=0.0, sheen_rough=0.3):
    """Clean physically-plausible Principled material (no texture). sheen -> fabric,
    coat -> lacquer/marble sheen, metallic+low rough -> brass/chrome, aniso -> BRUSHED
    metal (stretches the highlight along the grain instead of a round dot).

    2026-07-22 (vault audit): default IOR was 1.45, a guess. The studio's own BSDF table
    (knowledge/materials/bsdf-material-presets.md) carries 1.5 on every dielectric row and
    1.52 for glass. Distilled 2026-07-01, never wired."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, bsdf = _principled(m)
    if bsdf:
        ok, msg = albedo_plausible(rgba)
        if not ok:
            print(f"  !! albedo WARN [{name}]: {msg}")
        _set(bsdf, "Base Color", rgba)
        _set(bsdf, "Roughness", rough)
        _set(bsdf, "Metallic", metallic)
        _set(bsdf, "IOR", ior)
        _set(bsdf, "Specular IOR Level", spec)
        if sheen:
            _set(bsdf, "Sheen Weight", sheen)
            # 2026-07-22 (vault audit): this was a hardcoded 0.3 on EVERY sheen material,
            # carrying no citation and unable to tell linen from velvet — while the studio's
            # own scatter-identity rule (pbr-material-behavior.md:102-106, MA-01) says those
            # signatures must differ. Now per-fabric, defaulting to the old 0.3 so every
            # non-cloth caller renders exactly as before.
            _set(bsdf, "Sheen Roughness", sheen_rough)
        if coat:
            _set(bsdf, "Coat Weight", coat)
            _set(bsdf, "Coat Roughness", 0.1)
        if aniso:
            _set(bsdf, "Anisotropic", aniso)
            _set(bsdf, "Anisotropic Rotation", 0.0)
    return m


_FABRIC_MAPS = True        # DEFAULT ON, D-022 2026-08-10. The A/B that decided it is
#                            re-runnable with --no-fabric-maps; the flag stays so the
#                            comparison never needs a source edit (R6). Lane B wrote
#                            `maps=` on seven soft-good materials on 2026-07-30 and left
#                            the flag False, so the bed, shams, coverlet, duvet, throw,
#                            bench seat and stool carried texture code no lane ever ran —
#                            2 of 498 built objects had an image map, against 50-66% in
#                            delivered .blend files. THE INSTRUMENTS COULD NOT DECIDE IT:
#                            octave energy moved 10.1222 -> 10.1223. The LOOK could — at
#                            2x on the bed head the shams read as woven cloth instead of
#                            matte slabs, which is Gemini's C3 item 2 ("หมอนดูเหมือน
#                            ลูกโป่ง...แข็งและไร้น้ำหนัก") answered on its surface half.
#                            The geometry half (no seams, too round) is NOT fixed by this.
_FABRIC_TILE_M = 0.85      # physical metres one 2k fabric tile spans — cm-scale features,
#                            NOT thread pitch (the 2026-07-22 probe killed thread-pitch maps
#                            and stays honoured: nothing here is authored below the meso band)
_SHEEN_CAP = 0.4           # ground-truth ceiling: max sheen measured in ANY pro file = 0.4
#                            (Italian Flat, 7 fabric mats; Poly Haven cloth runs 0.0 with the
#                            maps doing the work). Ours ran 0.7-1.0 — we were buying fabric
#                            realism in a channel the pros barely spend in, and the flat fuzz
#                            highlight it bought is half the "clay" verdict.


def _woven(name, rgba, rough, cloth, sheen=0.0, spec=0.5, coat=0.0, ior=1.5, maps=None):
    """TEXTILE: _solid's signed colour + the surface signature that makes cloth read as
    cloth instead of painted vinyl. `cloth` is material_presets.cloth_args(kind).

    WHY THIS EXISTS. Every textile in this build was `_solid` — documented "no texture" —
    so fabric was the ONLY surface class here with a perfectly uniform albedo, while the
    floor got variation=, the walls _painted's three non-uniformities and the millwork
    _veneer's grain. That is MA-05 "Plastic look — missing micro-imperfections", named in
    the studio's own taxonomy as "the corpus's canonical late-denoising-stage textural
    error" (knowledge/classifications/render-defects.md:69), and it is why three prior
    softening passes and a real cloth SOLVER still produced bedding that reads as latex:
    drape.py fixed the 100 mm+ fold band, Sheen covers the sub-mm fuzz band, and NOTHING
    was modelling the 10-40 mm slub/crease/pill band in between. Element 3's signed D3-2
    asked for exactly that band — "micro-imperfections (wrinkle/pilling) so it reads used,
    not synthetic-smooth" — and it was the half of D3-2 the build never made.

    PROCEDURAL, NOT A PHOTO — and that is the researched answer, not the lazy one. A weave
    map at a real thread pitch is minified to tens of texels per pixel at room distance and
    Cycles averages it to a flat colour (probe 2026-07-22: an image at fabric pitch returned
    an identical constant across Object/Generated/FLAT/BOX). It would also trip MA-02
    (scale) and MA-03 (tiling), and these objects carry no UV at all (see the WARN at
    _suite_materials) — drape.py's baked sheets are from_pydata meshes with no uv_layers.
    _veneer already settled this trade for millwork on gate evidence: keep the grain, drop
    the photo.

    THREE CHANNELS, ONE FIELD. The same two-scale field drives albedo, relief and roughness,
    because on real cloth they are the same slubs seen three ways — driving them from
    independent noise is what makes procedural fabric look like static.
    Object coords (origins are all at 0,0,0) keep the field CONTINUOUS across parts, so a
    coverlet and the base it falls onto share one weave instead of two unrelated ones."""
    # coat/ior are forwarded rather than dropped: _material_from_preset's cloth branch now
    # routes textile presets HERE instead of to _solid, and any channel this signature does
    # not carry would be SILENTLY LOST — the same trap factory_args' own whitelist comment
    # warns about ("A key absent from this tuple is SILENTLY DROPPED"). metallic and aniso
    # are deliberately absent: factory_args only marks NON-METAL solids as cloth, so a
    # textile cannot legally carry them.
    m = _solid(name, rgba, rough, sheen=min(sheen, _SHEEN_CAP), spec=spec, coat=coat,
               ior=ior, sheen_rough=cloth["sheen_rough"])
    nt, bsdf = _principled(m)
    if not bsdf:
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # (1) the MESO band: slubs / creases / pilling — the only band that RESOLVES at the
    #     hero camera's distance, so it carries most of the read.
    slub = nt.nodes.new("ShaderNodeTexNoise")
    slub.inputs["Scale"].default_value = 1.0 / cloth["slub_m"]
    slub.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], slub.inputs["Vector"])
    # (2) the THREAD band: sub-pixel at room distance by construction — it is not there to
    #     be seen as threads, it is there to stop the specular being a single clean lobe.
    weave = nt.nodes.new("ShaderNodeTexNoise")
    weave.inputs["Scale"].default_value = 1.0 / cloth["weave_m"]
    weave.inputs["Detail"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], weave.inputs["Vector"])
    fld = nt.nodes.new("ShaderNodeMixRGB")            # meso-dominant, thread as a dither
    fld.blend_type = "MIX"
    fld.inputs["Fac"].default_value = 0.35
    nt.links.new(slub.outputs["Fac"], fld.inputs["Color1"])
    nt.links.new(weave.outputs["Fac"], fld.inputs["Color2"])
    field = fld.outputs["Color"]
    # (3) ALBEDO drift — the MA-03/MA-05 cure, the same keyword that fixed the floor.
    #     MULTIPLY so the SIGNED colour is the CEILING and nothing ever brightens past it:
    #     every one of these tones (greige linen D3-1, greige-oatmeal terry D-E6-3, cream
    #     boucle) is an owner-signed decision, several of them LOOK-tuned by hand, and a
    #     texture that repaints one would be this studio's recurring wound wearing a new
    #     hat. DISCLOSED COST of choosing the ceiling over a centred drift: the MEAN tone
    #     darkens by about albedo_var/2 — with the shipped vocabulary that is ~4.3% on
    #     linen, ~5% on terry and ~5.5% on boucle. That is the same trade _painted
    #     (0.97-1.0) and the floor's variation= already make, but at these amplitudes it is
    #     NO LONGER negligible: it is at or just past the ~4% an eye resolves on a matte
    #     surface. It is spent knowingly — a signed tone reads as ITS OWN colour slightly
    #     deepened, which is what cloth does, whereas the flat slab it replaces did not read
    #     as cloth at all. If a future retune pushes albedo_var higher, this trade must be
    #     re-argued, not inherited. (The first draft of this comment said "~2.8%" and was
    #     left behind by the retune that doubled the amplitude — prose-vs-build drift caught
    #     in pre-commit review, in the very block warning about repainting signed data.)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 1.0 - cloth["albedo_var"]
    mr.inputs["To Max"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    mix.inputs["Color1"].default_value = rgba
    nt.links.new(field, mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    # (4) RELIEF via Bump — not a NormalMap node: tangent-space normals need a UV map for
    #     their tangents and these meshes have none, while Bump works from screen-space
    #     derivatives on any mesh. Distance is a real height in metres (cloth.relief_m).
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = cloth["bump"]
    # NOT wrapped in try/except like _veneer's: Bump.Distance defaults to 1.0, so a
    # swallowed failure here does not degrade the weave — it claims a ONE METRE relief on a
    # bedsheet. A missing socket means the API moved and the build must say so.
    bump.inputs["Distance"].default_value = cloth["relief_m"]
    nt.links.new(field, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # (5) ROUGHNESS break-up on the SAME field: a slub that stands proud also catches light
    #     differently. SYMMETRIC about the preset's own value, unlike _painted's
    #     (-0.05,+0.03): roughness is SIGNED data here too (linen 0.94, coverlet 0.96,
    #     boucle 0.92, terry 0.9, every one LOOK-tuned), and an asymmetric band shifts the
    #     MEAN toward gloss rather than only adding variance — which is the one direction a
    #     textile must never move.
    #     CLAMPED TO THE STUDIO BAND, not to 0..1: the coverlet is authored at 0.96 and the
    #     pillows/duvet at 0.95, so a naive min(1.0, rough+var) would drive the top of the
    #     band to an ABSOLUTE 1.0 — which `ROUGH_FLOOR, ROUGH_CEIL = 0.03, 0.97  # never
    #     absolute 0.0/1.0` (material_presets.py:43, from bsdf-material-presets.md:54-60)
    #     exists to forbid. factory_args enforces that ceiling for PRESET-driven materials,
    #     but the bespoke _build_bed / _build_bench calls pass their roughness straight in
    #     and never touch factory_args, so the bound has to be applied HERE or it is not
    #     applied at all on exactly the largest textile in the hero frame.
    #     The band SHRINKS rather than clipping: clamping the two ends independently would
    #     leave the coverlet (0.96) at [0.915, 0.97] — asymmetric again, mean toward gloss,
    #     the exact defect this paragraph forbids, re-introduced by the clamp that fixed the
    #     absolute-1.0 one. So the half-width is the largest that stays symmetric AND inside
    #     the studio band; near the ceiling the roughest cloths simply get less variance,
    #     which is honest — there is no headroom there.
    _rvar = max(0.0, min(0.045, _matpre.ROUGH_CEIL - rough, rough - _matpre.ROUGH_FLOOR))
    mr2 = nt.nodes.new("ShaderNodeMapRange")
    mr2.inputs["To Min"].default_value = rough - _rvar
    mr2.inputs["To Max"].default_value = rough + _rvar
    nt.links.new(field, mr2.inputs["Value"])
    nt.links.new(mr2.outputs["Result"], bsdf.inputs["Roughness"])
    # (6) GROUND-TRUTH MAPS (lane B 2026-07-30, --fabric-maps A/B): the file study
    #     measured pro cloth as image maps + sheen <= 0.4 while every textile here was
    #     procedural-only (2/41 of our materials carried any image vs 50-66% in every
    #     pro scene). This block COMPOSES a real 2k photographed weave onto the
    #     signature above — it never replaces it, and every law of this function
    #     survives: the SIGNED colour stays the albedo ceiling (multiply, band [1-v,1]),
    #     roughness keeps the symmetric studio band (the map only co-drives mr2's
    #     Value), relief chains through the same Bump. BOX projection on Object coords
    #     because drape's baked meshes carry no UVs (the same reason relief is Bump,
    #     not NormalMap) — and the map's features live at cm scale, the band the
    #     2026-07-22 thread-pitch probe never tested.
    if maps and _FABRIC_MAPS:
        ts = _texset(maps)
        if ts.get("Diffuse"):
            mp = nt.nodes.new("ShaderNodeMapping")
            _ms = 1.0 / _FABRIC_TILE_M
            mp.inputs["Scale"].default_value = (_ms, _ms, _ms)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

            def _img(path, non_color):
                n = _img_node(nt, path, non_color=non_color)
                n.projection = 'BOX'
                n.projection_blend = 0.3
                nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
                return n

            di = _img(ts["Diffuse"], False)
            bw = nt.nodes.new("ShaderNodeRGBToBW")
            nt.links.new(di.outputs["Color"], bw.inputs["Color"])
            mr3 = nt.nodes.new("ShaderNodeMapRange")
            mr3.inputs["To Min"].default_value = 1.0 - 0.12
            mr3.inputs["To Max"].default_value = 1.0
            m2 = nt.nodes.new("ShaderNodeMixRGB")
            m2.blend_type = "MULTIPLY"
            m2.inputs["Fac"].default_value = 1.0
            nt.links.new(bw.outputs["Val"], mr3.inputs["Value"])
            nt.links.new(mix.outputs["Color"], m2.inputs["Color1"])
            nt.links.new(mr3.outputs["Result"], m2.inputs["Color2"])
            nt.links.new(m2.outputs["Color"], bsdf.inputs["Base Color"])
            # the photographed weave also stands proud: chain its height UNDER the
            # slub bump so both reliefs compose (Bump.Normal input = the chain)
            bmp2 = nt.nodes.new("ShaderNodeBump")
            # 0.6 -> 0.35 at the lb1 LOOK + C2 ("แผ่นสักหลาด"): the photographed nap at
            # full weight read as FELT, not linen — bisect down, keep the breakup
            bmp2.inputs["Strength"].default_value = cloth["bump"] * 0.35
            bmp2.inputs["Distance"].default_value = cloth["relief_m"] * 0.5
            nt.links.new(bw.outputs["Val"], bmp2.inputs["Height"])
            nt.links.new(bmp2.outputs["Normal"], bump.inputs["Normal"])
            if ts.get("Rough"):
                ri = _img(ts["Rough"], True)
                rmx = nt.nodes.new("ShaderNodeMixRGB")
                rmx.inputs["Fac"].default_value = 0.5
                nt.links.new(field, rmx.inputs["Color1"])
                nt.links.new(ri.outputs["Color"], rmx.inputs["Color2"])
                nt.links.new(rmx.outputs["Color"], mr2.inputs["Value"])
    return m


def _veneer(name, rgba, rough):
    """Rift-cut veneer millwork: solid base + FINE vertical grain as bump only +
    large tonal drift. Round-1 gate evidence (2026-07-03): mapping the FLOOR
    plank texture onto millwork tanked the bedroom A/B 4.75->4.0 — plank gaps
    read as 'flooring on the walls' and three planked walls fought the
    material_story ('greige plaster walls'); the paired living A/B (+0.5) shows
    grain direction cues DO help. So: grain per se stays, plank texture goes.
    Anisotropic noise (high XY freq, low Z) = vertical striations on any wall
    orientation, colourless (bump+roughness only) like lacquered rift oak."""
    m = _solid(name, rgba, rough)
    nt, bsdf = _principled(m)
    if not bsdf:
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # tonal drift (~2 m patches) — same recipe as _painted
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")
    # 0.94 -> 0.88 (round-6 B2, C2 on lb1: the carcass read as RAW MDF, one flat
    # colour every face — the drift existed but sat under the ~4% an eye resolves;
    # amplitude-bisect: loud enough to read as figured veneer, colour still the
    # signed ceiling)
    mr.inputs["To Min"].default_value = 0.88
    mr.inputs["To Max"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    mix.inputs["Color1"].default_value = rgba
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    # fine vertical striation: compress noise in Z only
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (40.0, 40.0, 2.0)
    gz = nt.nodes.new("ShaderNodeTexNoise")
    gz.inputs["Scale"].default_value = 1.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16          # 0.08 doubled (B2, same verdict)
    try:
        bump.inputs["Distance"].default_value = 0.0003
    except Exception:
        pass
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], gz.inputs["Vector"])
    nt.links.new(gz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # sheen-of-lacquer roughness breakup along the same striations
    mr2 = nt.nodes.new("ShaderNodeMapRange")
    mr2.inputs["To Min"].default_value = max(0.0, rough - 0.12)
    mr2.inputs["To Max"].default_value = min(1.0, rough + 0.06)
    nt.links.new(gz.outputs["Fac"], mr2.inputs["Value"])
    nt.links.new(mr2.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def _burnish(m, band=(0.10, 0.05), bump=0.06, scale=1.6):
    """Trowel-burnish breakup for cement/plaster finishes (round-6 B2 — C2 on lb1
    read the white drawer stack as untreated board: SIGNED microcement must read
    as microcement, which is a TROWELLED surface — burnish patches where the
    float pressed harder). Signed colour untouched: roughness band + faint bump
    only, same discipline as _painted's three non-uniformities."""
    nt, bsdf = _principled(m)
    if not bsdf:
        return m
    r = float(bsdf.inputs["Roughness"].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 3.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.03, r - band[0])
    mr.inputs["To Max"].default_value = min(0.97, r + band[1])
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    try:
        bp.inputs["Distance"].default_value = 0.0004
    except Exception:
        pass
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def _painted(name, rgba, rough):
    """Painted plaster/paint: _solid plus the three subtle non-uniformities real
    paint always has — large-scale tonal drift (<= 3% multiply), hand-finish
    roughness breakup, and a sub-mm roller/plaster bump. Both v004pro judges
    docked EXACTLY this ('left wall is quite stark', 'ceiling entirely devoid of
    any architectural detail or subtle texture') and the repaint pass preserves a
    flat clay surface as a flat photo surface. World-space Object coords keep the
    field continuous across wall pieces (origins all at 0,0,0)."""
    m = _solid(name, rgba, rough)
    nt, bsdf = _principled(m)
    if not bsdf:
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # (1) tonal drift, ~2 m patches
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.97
    mr.inputs["To Max"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    mix.inputs["Color1"].default_value = rgba
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    # (2) roughness breakup around the base value
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 3.0
    mr2 = nt.nodes.new("ShaderNodeMapRange")
    mr2.inputs["To Min"].default_value = max(0.0, rough - 0.05)
    mr2.inputs["To Max"].default_value = min(1.0, rough + 0.03)
    nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
    nt.links.new(nz2.outputs["Fac"], mr2.inputs["Value"])
    nt.links.new(mr2.outputs["Result"], bsdf.inputs["Roughness"])
    # (3) fine roller-coat bump (sub-mm — texture, not lumps)
    nz3 = nt.nodes.new("ShaderNodeTexNoise")
    nz3.inputs["Scale"].default_value = 80.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    try:
        bump.inputs["Distance"].default_value = 0.0005
    except Exception:
        pass
    nt.links.new(tc.outputs["Object"], nz3.inputs["Vector"])
    nt.links.new(nz3.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def _hdri_world(slug, strength=1.0, rot_deg=0.0, exposure=0.0, look=""):
    """Image-based lighting from a cached interior HDRI -> soft realistic light +
    real reflections (the single biggest lift out of 'sterile CG'). Falls back to a
    warm flat fill if the HDRI is missing. Pins AgX/Filmic for a deterministic look."""
    import math
    scn = bpy.context.scene
    world = scn.world or bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    if _LIGHT_STORY:
        # DUAL BACKGROUND (round-6 B2 — the Italian Flat file's own LightPath
        # pattern, and C2 on lb1: "แสงนอกหน้าต่างขาวอมเขียวจ้าจนไหม้ ... เหมือนแปะ
        # ฉากหลังคนละภาพ"): the story pumps the env as the interior KEY (x2.3),
        # but what the CAMERA sees through the glass must not ride that gain —
        # camera rays get ~45% of the light strength, so the garden reads as a
        # view again while the room keeps its key. Story-only by construction.
        lp = nt.nodes.new("ShaderNodeLightPath")
        cmr = nt.nodes.new("ShaderNodeMapRange")
        cmr.inputs["From Max"].default_value = 1.0
        cmr.inputs["To Min"].default_value = strength
        cmr.inputs["To Max"].default_value = strength * 0.45
        nt.links.new(lp.outputs["Is Camera Ray"], cmr.inputs["Value"])
        nt.links.new(cmr.outputs["Result"], bg.inputs["Strength"])
    path = _hdri_file(slug)
    if path:
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        try:
            env.image = bpy.data.images.load(path, check_existing=True)
        except Exception as e:
            print(f"  (hdri load fail: {e})")
        mp = nt.nodes.new("ShaderNodeMapping")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rot_deg))
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    else:
        bg.inputs["Color"].default_value = (0.85, 0.82, 0.78, 1.0)
        print(f"  (hdri '{slug}' not found -> flat fill)")
    nt.links.new(bg.outputs[0], out.inputs[0])
    for vt in ("AgX", "Filmic"):
        try:
            scn.view_settings.view_transform = vt
            break
        except Exception:
            continue
    try:
        scn.view_settings.exposure = exposure
    except Exception:
        pass
    if look:                                           # DR: a medium-high contrast look adds punch
        try:
            scn.view_settings.look = look
        except Exception:
            pass


def _exterior_world_args(spec, slug, strength, rot_deg, exposure, look=""):
    """The studio-default HDRI args (call-site defaults) — unless spec.exterior.hdri
    declares the view (owner-vetoable DATA, validated fail-loud in
    exterior.resolve_hdri). Called ONLY from the eye path (the client-facing window
    view); hero/overview keep their tuned studio env by design.

    A DECLARED environment RAISES rather than silently falling back to the studio
    default over a decided view (revert-by-omission, the exterior block's charter).
    Two failure modes both raise: (a) no cached file globs the slug; (b) the file
    globs but does NOT load — a truncated download or an unhydrated OneDrive
    Files-On-Demand placeholder (this repo lives in OneDrive) reads as a magenta
    void world at exit 0 otherwise (review 2026-07-17b). check_existing=True means
    _hdri_world reuses this same datablock — no double I/O. The build() try in
    __main__ turns either raise into os._exit(1). (Fetch a slug with:
    python pipeline/scripts/assets.py <slug> --type hdris --res 4k)"""
    env = exterior.resolve_hdri(spec)
    if not env:
        return slug, strength, rot_deg, exposure, look
    path = _hdri_file(env["slug"])
    if not path:
        raise ValueError(f"spec.exterior.hdri declares '{env['slug']}' but no cached "
                         f"hdris/{env['slug']}_*.hdr exists in assets/shared/cc0 — "
                         "fetch it or fix the slug; refusing to silently render the "
                         "studio default over a decided view")
    try:
        img = bpy.data.images.load(path, check_existing=True)
        loaded = bool(img.has_data) or tuple(img.size) != (0, 0)
    except Exception as e:
        raise ValueError(f"spec.exterior.hdri '{env['slug']}' file {path} failed to "
                         f"load ({e}) — refusing a magenta-void world over a decided "
                         "view (truncated file or an unhydrated OneDrive placeholder? "
                         "re-fetch the HDRI)")
    if not loaded:
        raise ValueError(f"spec.exterior.hdri '{env['slug']}' file {path} loaded with "
                         "no pixels (0x0 / dehydrated) — refusing a magenta-void world "
                         "over a decided view; re-fetch the HDRI")
    return (env["slug"], env["strength"], env["rot_deg"], env["exposure"],
            env["look"] or look)


def _add_rug(name, x, y, w, d, thick=0.014):
    """A thin textured rug slab under a seating group (own planar UV + wool/herringbone
    PBR). Sits just above the floor to avoid z-fighting. Anchors the furniture group so the
    floor doesn't read as an empty plane (KB scene-dressing)."""
    obj = add_box(name, x, y, 0.004, w, d, thick)
    _planar_uv(obj, tile_m=1.3)
    obj.data.materials.append(_pbr_material("rug_" + name, RUG_SLUG))
    # EDGE BINDING (round-6 B2, C2 on lb1: "พรมเป็น noise เนื้อเดียวทั้งผืน ไม่มีขอบ
    # เก็บริม"): a real area rug is finished with a sewn tape band around its
    # perimeter — the one manufactured line that says 'rug', not 'carpet patch'.
    # Four slim boxes, a shade darker than the pile, sitting 2mm proud.
    bind_m = _solid(name + "_binding", (0.42, 0.40, 0.37, 1.0), rough=0.85, sheen=0.15)
    bw, bt = 0.032, thick + 0.002
    for tag, bx, by, bdx, bdy in (("s", x, y, w, bw), ("n", x, y + d - bw, w, bw),
                                  ("w", x, y + bw, bw, d - 2 * bw),
                                  ("e", x + w - bw, y + bw, bw, d - 2 * bw)):
        bo = add_box(f"{name}__bind_{tag}", bx, by, 0.004, bdx, bdy, bt)
        bo.data.materials.append(bind_m)
        bo["ph_model"] = True                     # keeps its own material, no router
    return obj


def _curtain_sheer(name, rgba, alpha):
    """Sheer voile: Principled with partial Alpha (Cycles renders it as stochastic
    transparency — headless-safe). Full sheen so the fabric edge catches light."""
    # WOVEN with the 'plain' signature: a voile IS a fine tight plain weave, and its whole
    # job is to be a fabric the light passes THROUGH — a perfectly uniform one reads as
    # tinted glass. 'plain' is the LEAST TACTILE row in the vocabulary ("flat, tight"), so
    # the sheer never reads as a textured blind. Velvet's relief_mm is lower still (1.0 vs
    # 1.8) — an earlier draft of this comment called plain "the smallest in the vocabulary",
    # which is simply false — but velvet is a PILE whose identity is directional sheen, and
    # putting that scatter on a voile is MA-01 material mismatch.
    m = _woven(name, rgba, 0.6, _matpre.cloth_args("plain"), sheen=1.0)
    _nt, bsdf = _principled(m)
    if bsdf:
        _set(bsdf, "Alpha", alpha)
    return m


def _add_curtains(spec, h):
    """Materialize the spec's curtain_track + curtains blocks. ALL layout (leg matching,
    pocket containment, drawn/parked states, wave polylines) is pure and unit-tested in
    curtains.py; here each ribbon is only extruded floor-to-ceiling and given fabric.

    Colour: the opaque layer JOINS the plaster ground (Albers grounding, DR 3ce5f5e —
    a light curtain on a light ground stops fighting the oak for its 30%). That is a
    COMPOSITION decision recorded in the spec's render_state; the fabric SKU stays
    owner/supplier tier (curtains.still_owner)."""
    ribbons = curtains.curtain_ribbons(spec)
    if not ribbons:
        return 0
    rs = (spec.get("curtains") or {}).get("render_state") or {}
    # every render_state field fails LOUD (review 2026-07-17: a mistyped tint key or a
    # percent-valued alpha silently rendered default colours / an invisible sheer)
    tint = rs.get("fabric_rgba_linear") or {}
    bad = set(tint) - {"opaque", "sheer"} - {k for k in tint if k.startswith("_")}
    if bad:
        raise ValueError(f"curtains.render_state.fabric_rgba_linear: unknown key(s) "
                         f"{sorted(bad)} — expected 'opaque'/'sheer'")
    def _rgba(key, default):
        v = tint.get(key, default)
        if len(tuple(v)) != 4 or not all(0.0 <= float(cch) <= 1.0 for cch in v):
            raise ValueError(f"curtains fabric_rgba_linear.{key}: need 4 floats in "
                             f"0..1 (LINEAR + alpha), got {v!r}")
        return tuple(float(cch) for cch in v)
    opaque_rgba = _rgba("opaque", (0.48, 0.44, 0.38, 1.0))
    sheer_rgba = _rgba("sheer", (0.85, 0.84, 0.82, 1.0))
    alpha = float(rs.get("sheer_alpha", 0.38))
    if not 0.05 <= alpha <= 0.9:
        raise ValueError(f"curtains.render_state.sheer_alpha={alpha}: outside 0.05-0.9 "
                         "— below is an invisible sheer, above is a solid (a percent "
                         "value like 38 belongs here as 0.38)")
    mats = {"sheer": _curtain_sheer("curtain_sheer", sheer_rgba, alpha),
            "opaque": _woven("curtain_opaque", opaque_rgba, 0.9,
                             _matpre.cloth_args("linen"), sheen=0.9)}
    # top edge: hide inside the ceiling slab when one exists (--eye builds it at
    # h..h+0.05); the plain overview has NO ceiling, so stop just under the wall top —
    # a top 30mm proud of the walls reads as a fence in the dollhouse view
    z_top = h + 0.03 if spec.get("_eye") else h - 0.002
    for rb in ribbons:
        # LOOK round-2 #4: the 2-ring prism this loop used to extrude (track wave at
        # constant amplitude down to a dead-level hem) is what made the east sheer's
        # hem a row of detached triangular spikes — the sawtooth class e8 killed
        # elsewhere. The lattice (rings, decaying primary, irregular secondary,
        # wandering hem, end-tapered so mitre corners still meet) is pure and
        # unit-tested in curtains.ribbon_mesh; here it is only materialised.
        verts, faces = curtains.ribbon_mesh(dict(rb, z1=min(rb["z1"], z_top)))
        me = bpy.data.meshes.new(rb["name"])
        me.from_pydata(verts, [], faces)
        me.validate()
        me.update()
        for poly in me.polygons:
            poly.use_smooth = True   # a faceted wave reads as a polygonal zigzag fan
        obj = bpy.data.objects.new(rb["name"], me)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(mats[rb["type"]])   # type validated in curtains.py
        # an open ribbon surface: the wide suite bevel would shred its border edges, and
        # its fabric is assigned right here — ph_model opts out of both passes (same
        # escape imported models use; unlike millwork it LOSES nothing by skipping)
        obj["ph_model"] = True
        if rb.get("over_glass_park"):
            print(f"  curtains: {rb['name']} parks OVER glass — its leg's track has no "
                  f"off-glass run (corner-to-corner glazing); disclosed, owner may re-park")
        if rb.get("squeezed_by"):
            print(f"  curtains: {rb['name']} envelope compressed to "
                  f"{rb['pocket_used_mm']:.0f} mm (x{rb['depth_scale']:.2f}) by "
                  f"'{rb['squeezed_by']}' standing in the pocket band — a known spec "
                  f"residual, the INK pocket stays the build truth")
    legs = len({r['leg'] for r in ribbons})
    print(f"  curtains: {len(ribbons)} fabric ribbon(s) hung on {legs} leg(s) "
          f"(curtain_track+curtains spec data -> curtains.py layout)")
    return len(ribbons)


def _add_casement_sheers(spec):
    """ELEMENT 6 (D-E6-1): sill-length flat sheers inside the two west casement
    reveals. ALL layout (window matching, drawn-only state law, room side, the
    micro-wave, z from each opening's OWN sill/head — NEVER floor-to-ceiling) is pure
    and unit-tested in casement_sheers.py; here each ribbon is only extruded between
    its own z0/z1 and given the EXISTING `curtain_sheer` material BY NAME — the suite
    keeps ONE sheer identity (same rgba + alpha as the glass-L sheer). Must run AFTER
    _add_curtains: that pass creates `curtain_sheer` (after its empty-ribbons early
    return), and a get-or-create here would fork a second sheer identity — so an
    absent material RAISES instead."""
    ribbons = _csheers.sheer_ribbons(spec)
    if not ribbons:
        return 0
    mat = bpy.data.materials.get("curtain_sheer")
    if mat is None:
        raise ValueError(
            "casement_sheers present but material 'curtain_sheer' does not exist — "
            "_add_curtains must have run first (it owns the sheer identity); a "
            "get-or-create here would fork a second sheer")
    for rb in ribbons:
        pts, z0, z1 = rb["pts"], rb["z0"], rb["z1"]
        n = len(pts)
        verts = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
        faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        me = bpy.data.meshes.new(rb["name"])
        me.from_pydata(verts, [], faces)
        me.validate()
        me.update()
        for poly in me.polygons:
            poly.use_smooth = True   # a faceted micro-wave reads as a zigzag fan
        obj = bpy.data.objects.new(rb["name"], me)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(mat)
        # open ribbon surface: the wide suite bevel would shred its border edges, and
        # its fabric is assigned right here — ph_model opts out of both passes (the
        # same escape _add_curtains uses)
        obj["ph_model"] = True
    print(f"  casement sheers: {len(ribbons)} sill-length ribbon(s) drawn inside the "
          f"west casement reveals (z from sill/head; alpha = the east system's "
          f"curtain_sheer, ONE identity)")
    return len(ribbons)


def _add_juliet_rail(spec):
    """Materialize exterior.juliet_rail (ALL layout pure + unit-tested in exterior.py;
    here each member is only a box + black metal). The rail is DEPICTED from the
    owner's photo — an existing element outside the slider — never designed here;
    dims are [est] spec data. ph_model opts out of the wide suite bevel (it would
    swallow a 14 mm bar) and of the prefix material pass (assigned right here,
    same escape the curtain fabric uses)."""
    parts, meta = exterior.juliet_rail_parts(spec)
    if not parts:
        return 0
    # black POWDER-COAT: a dielectric paint film over steel, not bare metal —
    # metallic 0 + near-black albedo (>=0.04, the PBR albedo floor; 0.03 tripped
    # the albedo WARN on first build) + a light coat for the sprayed-satin sheen
    mat = _solid("juliet_black_steel", (0.045, 0.045, 0.048, 1.0), 0.5, coat=0.2)
    for (name, x, y, z, dx, dy, dz) in parts:
        o = add_box(name, x, y, z, dx, dy, dz)
        o.data.materials.append(mat)
        o["ph_model"] = True
    print(f"  juliet rail: {meta['n_bars']} bars @ gap {meta['gap_mm']:.0f} mm outside "
          f"'{meta['opening']}' (span {meta['span_mm']:.0f} mm, centreline "
          f"{meta['centreline_mm']:.0f} mm) — depicted from the owner's photo, dims [est]")
    return len(parts)


def _add_vanity_mirror(spec):
    """Materialize the frameless makeup mirror (ELEMENT 2 D2-3) on the wall between the two west
    casement windows, behind the BF11 kneehole. DATA from the vanity builtin's `design.mirror` — a
    DECIDED element, so it lives in the spec and cannot revert by an omission of build code (the D7
    lesson). Named `mill__..__mirror` so _suite_materials routes it to the silver mirror material;
    a malformed block RAISES rather than silently skipping (fail loud). Opt-in like curtains: no
    mirror block -> nothing built."""
    box = millwork.vanity_mirror_box(spec)   # PURE + unit-tested; raises on a malformed block
    if not box:
        return 0
    name, x_mm, y_mm, sill_mm, w_mm, d_mm, h_mm = box
    add_box(name, x_mm * MM, y_mm * MM, sill_mm * MM, w_mm * MM, d_mm * MM, h_mm * MM)
    print(f"  vanity mirror: frameless {d_mm:.0f}x{h_mm:.0f} mm on the wall between the west "
          f"windows (sill {sill_mm:.0f} mm) -> silver mirror")
    return 1


def _add_ceiling(outline_m, h, margin=0.18):
    """Close the top so an eye-level hero reads as an enclosed room (the open top otherwise
    shows the HDRI/void). Built as the outline's BOUNDING BOX grown by `margin` so it always
    overlaps every wall top and seals corner hairlines — a rectangle covers ANY outline,
    including the concave L-shapes the schema supports (a centroid-expand would misbehave at
    a concave vertex)."""
    x0 = min(p[0] for p in outline_m) - margin; x1 = max(p[0] for p in outline_m) + margin
    y0 = min(p[1] for p in outline_m) - margin; y1 = max(p[1] for p in outline_m) + margin
    obj = add_poly_floor("ceiling", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.05)
    for v in obj.data.vertices:
        v.co.z += h + 0.05
    obj.data.update()
    obj.data.materials.append(_painted("ceiling_paint", (0.90, 0.89, 0.87, 1.0), 0.9))
    return obj


def _add_emissive(name, verts, color=(1.0, 0.93, 0.82), strength=12.0):
    """A glowing quad (mesh light) that is BOTH visible in-frame and lights the scene — used
    as a bright 'window' so the hero reads as a photographed room with daylight streaming in,
    not a flatly-lit box. verts = 4 corners (metres)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    o.data.materials.append(m)
    o["ph_model"] = True                                   # don't bevel / reassign
    return o


def _hero_lighting(rx0, ry0, rx1, ry1, h, cx, cy, gx0, gx1):
    """Layered 'luxury' hero light (DR: layers + contrast beats flat fill). (1) a bright warm
    WINDOW key on the west wall that rakes light across the group; (2) warm pools washing the
    walnut feature wall for a rich vertical gradient; (3) a low cool fill from behind camera so
    shadows lift without going flat; (4) a warm practical pool over the table for cosiness."""
    _add_emissive("window_east",       # side window near the lounge -> raking cross-light + a bright focal element
                  [(rx1 - 0.05, cy - 1.7, 0.5), (rx1 - 0.05, cy + 1.7, 0.5),
                   (rx1 - 0.05, cy + 1.7, 2.3), (rx1 - 0.05, cy - 1.7, 2.3)],
                  color=(1.0, 0.92, 0.80), strength=14.0)
    n = 4
    for i in range(n):
        wx = gx0 + (gx1 - gx0) * (i + 0.5) / n
        _add_window_light(wx, 0.5, h - 0.12, wx, 0.0, 0.15,
                          size=(1.2, 0.5), energy=42.0, color=(1.0, 0.80, 0.55))
    _add_window_light(cx, ry1 - 0.4, h - 0.5, cx, cy, 0.6,
                      size=(4.0, 2.0), energy=110.0, color=(0.95, 0.96, 1.0))
    _add_window_light(cx, cy, 1.35, cx, cy, 0.0,
                      size=(0.9, 0.9), energy=28.0, color=(1.0, 0.78, 0.52))


def _add_feature_slats(x0, x1, y, h):
    """Vertical wood battens proud of the (south) feature wall = a fluted SLAT wall — the
    signature modern-luxury wood-wall treatment (rhythm + shadow lines under the wall-wash),
    instead of a flat 'dumb' wood panel. Slats get their own walnut solid; the shadow gaps do
    the work. Returns the count."""
    slat_w, proud, gap = 0.05, 0.03, 0.10
    step = slat_w + gap
    mat = _solid("slat_walnut", (0.34, 0.22, 0.14, 1.0), 0.45, spec=0.5, coat=0.05)
    x = x0 + 0.12
    n = 0
    while x < x1 - 0.12:
        o = add_box(f"slat__{n}", x, y, 0.0, slat_w, proud, h)
        o.data.materials.append(mat)
        x += step
        n += 1
    return n


def _add_window_light(x, y, z, tx, ty, tz, size=(4.0, 2.4), energy=400.0, color=(1.0, 0.95, 0.88)):
    """A large soft RECTANGLE area light standing in for a window/soft key — the enclosed
    hero's main daylight. Aimed from (x,y,z) at (tx,ty,tz). Big + low-intensity = soft shadows
    (the DR's countermeasure to flat 'sterile CG')."""
    from mathutils import Vector
    ld = bpy.data.lights.new("window", type='AREA')
    ld.shape = 'RECTANGLE'; ld.size = size[0]; ld.size_y = size[1]
    ld.energy = energy; ld.color = color
    lo = bpy.data.objects.new("window", ld)
    lo.location = (x, y, z)
    lo.rotation_euler = Vector((tx - x, ty - y, tz - z)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(lo)
    return lo


# decor slugs for scene dressing (own PBR). Placed on tables / floor to kill the 'empty
# room' read. Skipped gracefully if an asset isn't cached.
def _dress_scene(spec):
    """Place a few CC0 decor pieces: a vase cluster on the round centre table + a floor
    plant beside the seating group. Positions derived from the spec so it generalises.

    LANE D (round-6, approved order; C2 ×2: "ห้องอ่านเป็นยังไม่มีใครย้ายเข้า" while the
    reference styles its bench with a magazine): the SUITE branch dresses the foot
    bench — a leaning book pair + a REAL simulated throw over the far end. Restraint
    kept deliberately (the reference's own density); everything here is procedural;
    no-defect-object law: nothing torn, nothing worn. The throw wears the DUVET's
    material handle — no new colour enters the signed palette.

    "Everything procedural" was a ฿0/CC0 CONSTRAINT when this was written; the owner
    cancelled that clause 2026-08-01, so it is now a CHOICE — and one worth re-testing
    against R8, which says a book and a folded throw are free-form and belong on the
    acquire side. Not changed here: this lane is PRJ-2026-002 and closed."""
    placed = 0
    items = spec.get("items", [])
    bench = next((it for it in items if it.get("kind") == "bench"), None)
    if bench and not spec.get("_hero"):
        bx, by = float(bench["x"]) * MM, float(bench["y"]) * MM
        bw, bd = float(bench["w"]) * MM, float(bench["d"]) * MM
        bh = float(bench.get("h", 450)) * MM
        # [1] two leaning books at the south end — the bedroom's own muted boards
        # dark board ON TOP (d1 quick: the cream book uppermost read as a tissue
        # box — an ink cover over a cream base reads "books" at one glance)
        for bi, bc in enumerate(((0.78, 0.74, 0.68, 1.0), (0.20, 0.18, 0.16, 1.0))):
            bm = _solid(f"bench_book{bi}", bc, rough=0.55, spec=0.4)
            _rbox(f"deco__bench_book{bi}", bx + (bw - 0.215) * 0.5 + bi * 0.010,
                  by + 0.085 + bi * 0.007, bh + bi * 0.030,
                  0.215 - bi * 0.013, 0.155 - bi * 0.010, 0.030, bm, bevw=0.004, seg=2)
            placed += 1
        # [2] the throw: a sheet lying on the north half, overhanging the end,
        # dropped by the solver onto the seat it must fall past — pinned on its
        # on-bench strip the way a tucked throw really is (the unpinned-sheet
        # slide-off is a recorded failure shape)
        _seat = bpy.data.objects.get("bench__seat")
        if _seat is not None:
            tv, tf = softgoods.folded_sheet(bx + 0.045, by + bd - 0.46, bw - 0.09,
                                            0.66, bh + 0.02, band=0.18, head="y-",
                                            cell=0.035, salt=11)
            _pin = [k for k, p in enumerate(tv) if p[1] < by + bd - 0.28]
            try:
                _to = drape.bake_sheet("deco__bench_throw", tv, tf, [_seat],
                                       frames=45, fabric="linen",
                                       mat=bpy.data.materials.get("bed_duvet"),
                                       pin=_pin, thickness=0.010, collide_dist=0.012,
                                       shred_guard=True)
                _to["ph_model"] = 1
                placed += 1
            except drape.DrapeError as _te:
                # lane D is styling, never structure: a throw that cannot settle is
                # DROPPED LOUDLY, the build survives (no analytic twin needed here —
                # absence of a throw is not a defect object)
                print(f"  lane D: bench throw dropped ({_te})")
    tbl = next((it for it in items if it.get("kind") in ("coffee_table", "round_table")
                and float(it["x"]) > 4000), None)
    if tbl:
        tx = float(tbl["x"]) * MM; ty = float(tbl["y"]) * MM
        tw = float(tbl["w"]) * MM; td = float(tbl["d"]) * MM
        top = max(float(tbl.get("h", 350)) * MM, 0.05)
        # ceramic_vase_01 = clean round white (good); ceramic_vase_03 (leaning slab monolith)
        # and brass_vase_02 (ornate genie-lamp ewer) both dropped — they read as odd shapes.
        p = _model_path("ceramic_vase_01")
        if p and place_model(p, tx + 0.40 * tw - 0.065, ty + 0.54 * td - 0.065,
                             0.13, 0.13, 0.30, z0=top,
                             model_slot=_slot_pair("ceramic_vase_01", None)[0],
                             item_slot="styling"):
            placed += 1
        # a low stack of coffee-table books (procedural) — classic styling, adds muted colour
        book_cols = ((0.32, 0.30, 0.26, 1.0), (0.52, 0.30, 0.22, 1.0), (0.86, 0.83, 0.76, 1.0))
        bz = top
        for bi, bc in enumerate(book_cols):
            bm = _solid(f"book{bi}", bc, rough=0.55, spec=0.4)
            _rbox(f"deco__book{bi}", tx + 0.55 * tw - 0.11 + bi * 0.012, ty + 0.34 * td - 0.085,
                  bz, 0.23 - bi * 0.015, 0.17, 0.033, bm, bevw=0.006, seg=2)
            bz += 0.036
            placed += 1
    # (dropped the foreground pouf — it read as a clumsy white box overlapping the table)
    # a small potted plant on the centre table for a touch of green.
    #
    # `calathea_orbifolia_01` is a 2492 x 1194 mm FLOOR plant. Squeezed into this 220 mm tabletop
    # slot it used to render as a 37 mm-tall green smear — the same pancake bug as the side tables,
    # just in the decor lane. model_fit now REFUSES it (aspect 48%), and this call site had no
    # fallback, so the styling cue vanished silently. Styling is a SCORED axis; a decor piece must
    # never disappear because a gate said no. Procedural pot + foliage carries it instead.
    if tbl:
        pz = max(float(tbl.get("h", 350)) * MM, 0.05)
        px, py = tx + 0.15 * tw, ty + 0.12 * td
        p = _model_path("calathea_orbifolia_01")
        if p and place_model(p, px, py, 0.22, 0.22, 0.3, z0=pz,
                             model_slot=_slot_pair("calathea_orbifolia_01", None)[0],
                             item_slot="styling"):
            placed += 1
        else:
            pot_m = _solid("deco_pot", (0.78, 0.75, 0.70, 1.0), rough=0.85, spec=0.35)
            lef_m = _solid("deco_leaf", (0.24, 0.36, 0.22, 1.0), rough=0.75, sheen=0.3, spec=0.4)
            _rbox("deco__pot", px + 0.045, py + 0.045, pz, 0.13, 0.13, 0.11, pot_m, bevw=0.02, seg=3)
            for li, (lx, ly, lw, ld, lh) in enumerate((
                    (0.075, 0.085, 0.05, 0.03, 0.20), (0.100, 0.070, 0.03, 0.05, 0.16),
                    (0.055, 0.062, 0.04, 0.04, 0.13))):
                _rbox(f"deco__leaf{li}", px + lx, py + ly, pz + 0.09, lw, ld, lh, lef_m,
                      bevw=0.014, seg=3)
            placed += 1
            print("  (decor plant: procedural pot+foliage — the CC0 calathea is a FLOOR plant "
                  "and does not fit a 220mm tabletop slot)")
    if placed:
        print(f"  dressed scene with {placed} decor pieces")
    return placed


# floor/millwork texture choices (swap FLOOR_SLUG to 'marble_01' or 'grey_cartago_01'
# for a marble scheme). Kept as constants so the iteration loop can retune in one place.
FLOOR_SLUG = "wood_floor"
WALL_RGBA = (0.83, 0.80, 0.75, 1.0)    # matte warm-white paint
RUG_SLUG = "poly_wool_herringbone"


# lane-A light story (verdict-round6): set from --light-story before the build
# so every consumer (e5 layers + nightstand practicals + exposure) agrees
_LIGHT_STORY = False

# calibration switch for the shred detector: "" = enforce (cloth block default),
# "report" = print profiles instead of raising (--shred-report; used to measure
# the healthy-vs-shredded gap the thresholds are calibrated on)
_SHRED_MODE = ""


def _emit_style_part(p, quick=False):
    """Materialise ONE styling part record (styling.py's contract) — box or mesh.

    Both branches deliberately leave the material to `_suite_materials`, which routes on
    the part's NAME token. That is why `own_mat=False` exists on _smooth_mesh_obj: without
    it every soft mass would keep whatever handle it was handed and the token would be
    decorative. A shape this function does not recognise RAISES rather than being skipped —
    a silently dropped styling part is indistinguishable from one that was never decided."""
    if p["shape"] == "box":
        o = add_box(p["name"], p["x"], p["y"], p["z"], p["dx"], p["dy"], p["dz"])
        o["mill_bevel"] = p.get("bevel", MILL_BEVEL_M)
        return o
    if p["shape"] == "mesh":
        cl = p.get("cloth")
        if cl:
            # ROUND 5: a styling part that declares `cloth` goes through the SOLVER —
            # pinned at its declared support (the hanger zone), settling under
            # gravity with self-collision into real drape. Same law as the bed
            # stack: the pure layer authors construction, the solver authors cloth.
            # Material stays with the name-token router (mat=None).
            # The declared torso BLOCKER (if any) is a passive collider that is
            # never rendered and never survives the bake — the sim-surface
            # pattern inverted: support during physics, absent from the frame.
            _sup = None
            if cl.get("support"):
                _sup = _smooth_mesh_obj(p["name"] + "__torso", cl["support"]["verts"],
                                        cl["support"]["faces"], own_mat=False)
                _sup.hide_render = True
            # THE GARMENT ATTEMPT (owner "(ก2)"): ONE recipe, then the analytic
            # fallback. The 5b/5c measurements are the reason there is no longer a
            # multi-rung climb here: across the whole session rungs 2-3 rescued
            # ZERO pieces (0_0 moved 12.7->8.5% and still failed) while tripling
            # the worst-case build time — the first hybrid build timed out on
            # exactly that arithmetic. A QUICK build attempts a playblast-grade
            # sim (cheaper solver, shorter settle): quick kills bad work; only the
            # full build's recipe closes a gate (R5).
            _fr = cl.get("frames", 45)
            _recipes = (((8, max(35, _fr - 40), 1.0),) if quick
                        else ((12, _fr, 1.0),))
            o, _err = None, None
            for _q, _f, _b in _recipes:
                try:
                    o = drape.bake_sheet(p["name"], p["verts"], p["faces"],
                                         [_sup] if _sup else [],
                                         frames=_f, fabric=cl.get("fabric", "linen"),
                                         pin=cl["pin"],
                                         thickness=cl.get("thickness", 0.004),
                                         self_collide=True, quality=_q,
                                         collision_quality=6, bend_scale=_b,
                                         shred_guard=_SHRED_MODE
                                         or cl.get("shred_guard", True))
                    break
                except drape.DrapeError as e:
                    _err = e
                    stale = bpy.data.objects.get(p["name"])
                    if stale is not None:
                        bpy.data.objects.remove(stale, do_unlink=True)
                if _SHRED_MODE == "report":
                    break                       # report mode measures rung 1 only
            if _sup is not None:
                bpy.data.objects.remove(_sup, do_unlink=True)
            if o is None:
                # HYBRID RAIL (owner "(ก2)"): a piece no rung can stabilise falls
                # back to its analytic twin — same DNA, carve on — so a build can
                # never ship a shredded piece and never dies for one either. The
                # fallback is LOUD in the log; a silent swap would hide the
                # sim-share the gate reports.
                an = cl.get("analytic")
                if an is None:
                    raise drape.DrapeError(f"{p['name']}: no ladder rung stabilised "
                                           f"the cloth and no analytic twin was "
                                           f"declared — last: {_err}")
                print(f"  hybrid rail: {p['name']} -> ANALYTIC fallback ({_err})")
                o = _smooth_mesh_obj(p["name"], an["verts"], an["faces"], own_mat=False)
            if p.get("subsurf") and o.modifiers.get("softform_subsurf") is None:
                # lane B: the baked/fallback cloth gets the same render-time
                # subdivision as every declared soft form — a sim result at vertex
                # scale is exactly the faceting the study measured us under on
                md = o.modifiers.new("softform_subsurf", 'SUBSURF')
                md.levels = 1
                md.render_levels = int(p["subsurf"])
            return o
        return _smooth_mesh_obj(p["name"], p["verts"], p["faces"], own_mat=False,
                                bevel=p.get("bevel"), subsurf=p.get("subsurf", 0))
    raise ValueError(f"_emit_style_part: unknown shape {p['shape']!r} on {p['name']!r}")


def _add_styling(spec):
    """ELEMENT 8: hang the garments and dress the open shelves, DERIVED from the parts the
    build actually emitted (`_STYLE_ANCHORS`).

    Runs BEFORE _suite_materials so every token-named part is painted by the router.

    WHAT IT RAISES ON, AND WHY THAT IS NOT "ZERO RAILS": element 7's DD promised
    "satin-brass hang rails with garments", material_presets' wardrobe story bit still
    tells the beauty pass they are there, and the render showed nine bare rails. That gap
    — decided data the build never made, with prose still asserting it — is this studio's
    recurring wound, and the cure is failing loudly the moment the decision stops being
    built. But the FIRST cut of that guard demanded a rail from any room that merely had
    millwork, and the pre-commit review reproduced the consequence under real headless
    Blender: four room specs that built fine at HEAD (specs/master_bedroom.json,
    living_room.json, sitting_room.json, living_condo.json) now hard-exit, because a
    bedroom whose wardrobe is CLOSED has millwork and no rail, and that is not an omission
    — it is a design with no open dressing piece in it.
    So the demand is DERIVED FROM THE SPEC'S OWN DECISIONS: one rail-bearing piece per
    builtin/mass that DECLARES `open`. On the canonical suite that is 3 (BF09-3 + two open
    bay masses) against 9 built rails — strictly STRONGER than the old min_rails=1 — and on
    a closed-wardrobe bedroom it is 0, which dresses nothing and raises nothing."""
    if not _STYLE_ANCHORS:
        return 0
    _declared_open = (
        sum(1 for b in spec.get("builtins") or () if b.get("open"))
        + sum(1 for sr in spec.get("subrooms") or ()
              if sr.get("type") == "wardrobe"
              for f in (sr.get("fixtures") or ()) if f.get("open")))
    parts = (styling.dress_rails(_STYLE_ANCHORS, min_rails=_declared_open)
             + styling.dress_shelves(_STYLE_ANCHORS))
    for p in parts:
        _emit_style_part(p, quick=bool(spec.get("_quick")))
    n_g = sum(1 for p in parts if "garment" in p["name"])
    n_s = sum(1 for p in parts if "fold" in p["name"])
    print(f"  styling: {n_g} garment(s) on "
          f"{len(styling.find(_STYLE_ANCHORS, 'rail', required=False))} rail(s) + "
          f"{n_s} folded item(s) on open shelves (element 8)")
    return len(parts)


def _material_from_preset(mat_name, preset_key):
    """Build ONE material from a spec-selected preset via the SAME factories the legacy
    palette uses. All authoring bounds (albedo band clamp, roughness floor/ceil, binary
    metalness, sRGB->linear) are enforced inside material_presets.factory_args — nothing
    implausible can arrive here."""
    a = _matpre.factory_args(preset_key)
    f = a["factory"]
    if f == "pbr":
        return _pbr_material(mat_name, a.get("slug") or FLOOR_SLUG,
                             base_tint=a.get("tint"), variation=a.get("variation", 0.0))
    if f == "painted":
        return _painted(mat_name, a["rgba"], a["rough"])
    if f == "veneer":
        return _veneer(mat_name, a["rgba"], a["rough"])
    if f == "proc_wood":
        return _proc_wood(mat_name, base=a["rgba"], dark=a.get("dark", a["rgba"]),
                          rough=a["rough"])
    if f == "glass":
        # built WITHOUT _solid: a glass Base Color is a TRANSMISSION TINT, not a
        # dielectric albedo — routing it through _solid fires a false '!! albedo WARN'
        # on every build for legal presets like clear_glass (review finding 2026-07-14).
        g = bpy.data.materials.new(mat_name)
        g.use_nodes = True
        _gb = _principled(g)[1]
        if _gb:
            _set(_gb, "Base Color", a.get("trans_tint", a["rgba"]))
            _set(_gb, "Roughness", a["rough"])
            _set(_gb, "IOR", a.get("ior", 1.5))
            _set(_gb, "Specular IOR Level", a.get("spec", 0.5))
            _set(_gb, "Transmission Weight", a.get("transmission", 0.95))
        return g
    if a.get("cloth"):
        # a TEXTILE preset (factory_args marks any sheen-bearing solid as one and RAISES if
        # it has no cloth row) — it must not fall through to the untextured slab below.
        return _woven(mat_name, a["rgba"], a["rough"], a["cloth"],
                      sheen=a.get("sheen", 0.0), spec=a.get("spec", 0.5),
                      coat=a.get("coat", 0.0), ior=a.get("ior", 1.5))
    return _solid(mat_name, a["rgba"], a["rough"], metallic=a.get("metallic", 0.0),
                  sheen=a.get("sheen", 0.0), coat=a.get("coat", 0.0),
                  ior=a.get("ior", 1.5), spec=a.get("spec", 0.5),
                  aniso=a.get("aniso", 0.0))


def _suite_materials(spec=None):
    """Warm luxury interior palette using REAL CC0 PBR textures where they help
    (floor grain/reflection), clean physically-based solids elsewhere. Assigned by
    object-name PREFIX (tag__...). Imported furniture models keep their own PBR.

    2026-07-14 (owner direction — materials into the spec's hands): each role first
    consults the spec's optional `materials` block (material_presets.resolve_materials);
    a selected preset builds through the same factories, a missing one falls back to the
    EXACT legacy hardcode below, so a spec without the block renders today's palette
    unchanged. An invalid block raises (fail LOUD — a typo must never silently render
    the default palette)."""
    sel = _matpre.resolve_materials(spec)
    _sur = (sel or {}).get("surfaces", {})
    _fam = (sel or {}).get("families", {})

    def _pick(preset_key, role, legacy):
        if preset_key:
            return _material_from_preset(f"m_{role}_{preset_key}", preset_key)
        return legacy()

    floor = _pick(_sur.get("floor"), "floor",
                  # MA-03 (knowledge/classifications/render-defects.md): a large continuous
                  # surface must not show a repeating grid. The floor is the largest surface
                  # in every frame and was the ONE that passed no drift, while the feature
                  # wall below - same texture slug, same function - has carried variation=0.06
                  # since it shipped. The knob was one keyword away for three weeks.
                  lambda: _pbr_material("floor_pbr", FLOOR_SLUG, variation=0.05))
    wall = _pick(_sur.get("walls"), "walls",
                 lambda: _painted("wall_paint", WALL_RGBA, 0.88))                    # matte warm-white
    feature = _pick(_sur.get("feature_wall"), "feature",
                    lambda: _pbr_material("feature_walnut", FLOOR_SLUG,
                                          base_tint=(0.40, 0.28, 0.20, 1.0),
                                          variation=0.06))  # walnut backdrop, drift breaks tile repeats
    # LINEAR-space walnut (sRGB ~#5F4430): Blender default_value is linear — a
    # 'looks right in sRGB' triple renders as pale pink-beige (round-2 lesson).
    mill = _pick(_sur.get("millwork"), "millwork",
                 lambda: _veneer("mill_walnut", (0.105, 0.052, 0.026, 1.0), 0.45))  # rift-walnut veneer
    fab = _pick(_fam.get("fabric"), "fabric",
                # cream boucle — now WOVEN (looped nubs), not a painted slab. The colour,
                # roughness and sheen weight are the gate-proven values, untouched.
                lambda: _woven("fabric_boucle", (0.84, 0.79, 0.71, 1.0), 0.92,
                               _matpre.cloth_args("boucle"), sheen=0.8))
    wood = _pick(_fam.get("wood"), "wood",
                 lambda: _pbr_material("wood_oak", FLOOR_SLUG))                      # oak on wood items
    fix = _pick(_sur.get("fixtures"), "fixtures",
                lambda: _solid("sanitary_white", (0.90, 0.91, 0.92, 1.0), 0.15,
                               spec=0.6, coat=0.2))  # glossy sanitaryware
    furn = _pick(_fam.get("neutral"), "neutral",
                 lambda: _solid("furn_neutral", (0.52, 0.50, 0.48, 1.0), 0.55))
    # Sub-part materials for the slat/open-wall millwork (element-1 D2-A/D4-A/D6-A, owner-signed):
    # the matte-black ply BACKER behind the slats, the satin-brass hang-rail, and the cool
    # microcement drawer fronts / tower back. Routed to mill__ parts by role below (see
    # material_presets.mill_object_role); a closed door run references none of them. Built from the
    # signed presets so the render's material story stays true to the decision record.
    brass = _material_from_preset("m_mill_brass", "satin_brass")
    cement = _burnish(_material_from_preset("m_mill_cement", "microcement_cool"))
    backing = _material_from_preset("m_mill_backing", "matte_black_ply")
    # ELEMENT 2 (west wall): the Caesarstone vanity counter + the frameless makeup mirror.
    # Routed to mill__ parts by 'counter*' -> caesarstone, 'mirror*' -> mirror (material_presets
    # .mill_object_role). Built from the signed presets like the element-1 sub-part materials.
    caesar = _material_from_preset("m_mill_caesar", "caesarstone_quartz")
    mirror = _material_from_preset("m_mill_mirror", "mirror_silver")
    # ELEMENT 5 (D-E5-4/-5): luminaire surfaces. The opal diffuser face EMITS (a lit
    # task bar/strip is a light, not a white slab — MA-04's glow half); black-alu
    # bodies cohere with the suite's black-alu window frames. Strength [est] LOOK-tier.
    blackalu = _solid("m_mill_blackalu", (0.045, 0.045, 0.05, 1.0), rough=0.45,
                      metallic=0.9, spec=0.5)
    opal = _solid("m_mill_opal", (0.90, 0.90, 0.88, 1.0), rough=0.4)
    # ELEMENT 6 (D-E6-3/-4): greige-oatmeal TERRY for the ensuite towels + bath mat —
    # ONE textile token 'towel' (material_presets.mill_object_role) so towels and mat
    # share one identity. Lives here like blackalu/opal (bathroom.py is PURE; its part
    # dicts carry no rgba). LIGHT neutral greige JOINS the cool 60% ground, clearly
    # cooler/greyer than the cream boucle (NOT-cream is the family rule; LOOK checks it
    # holds under the warm lamps); rgba [est] composition-not-SKU, high rough + sheen
    # for the terry-pile read.
    towel = _woven("m_mill_towel", (0.60, 0.575, 0.52, 1.0), rough=0.9,
                   cloth=_matpre.cloth_args("terry"), sheen=0.7, spec=0.3)
    # ELEMENT 8: the greige stonewashed LINEN. It used to say "at the exact element-3
    # bed_base values" and hold its own copy of them; since 2026-07-23 it holds none —
    # the value comes from value_ladder, which is what makes 'the same' checkable.
    # It was signed in element 3 but re-hardcoded inside each builder (_build_bed's base,
    # _build_bench's seat) instead of being reachable BY NAME — so nothing outside those
    # two functions could wear the suite's own signed textile. This row is what makes it a
    # material identity rather than a number repeated in three places.
    # 2026-07-23: the colour now comes from value_ladder BY NAME. This row and the two
    # bespoke builders each held their own copy of the same tuple — the comment above
    # claims this row made the linen "a material identity rather than a number repeated in
    # three places", and it did not: it made a FOURTH copy. One tone, one source.
    linen = _woven("m_mill_linen", _vl.rgba("m_mill_linen"), rough=0.94,
                   cloth=_matpre.cloth_args("linen"), sheen=0.2, spec=0.25)
    _opb = _principled(opal)[1]
    if _opb:
        _set(_opb, "Emission Color", (1.0, 0.97, 0.92, 1.0))
        _set(_opb, "Emission Strength", 3.0)

    def _legacy_glass():
        # glazing (2026-07-12): the panes poly_walls_bpy glazes back into the openings it cut. Named
        # glass__* so they route here and NOT to the opaque wall paint -- a sliding glass door that
        # renders as a painted wall is the exact bug the openings work exists to kill.
        g = _solid("glazing", (0.60, 0.76, 0.80, 1.0), 0.05, ior=1.52, spec=0.5)  # vault: glass 1.52
        _gb = _principled(g)[1]
        if _gb:
            _set(_gb, "Transmission Weight", 0.95)
            _set(_gb, "Base Color", (0.86, 0.92, 0.93, 1.0))
        return g

    glass = _pick(_sur.get("glazing"), "glazing", _legacy_glass)

    # pbr (texture-set) presets need UV. Walls get one on the fly (same recipe as the
    # feature wall); roles whose objects have no UV and whose LEGACY factory was not
    # already pbr warn LOUDLY — a texture sampling one flat texel must not pass silently
    # (review finding 2026-07-14). (The legacy wood family is pbr-on-UV-less already —
    # long-standing behaviour, not a new lie, so it does not warn.)
    def _fac(k):
        return _matpre.factory_args(k)["factory"] if k else None

    _wall_pbr = _fac(_sur.get("walls")) == "pbr"
    for _role, _key in (("millwork", _sur.get("millwork")), ("fixtures", _sur.get("fixtures")),
                        ("fabric", _fam.get("fabric")), ("neutral", _fam.get("neutral"))):
        if _fac(_key) == "pbr":
            print(f"  !! materials WARN: pbr preset '{_key}' on '{_role}' — these objects "
                  f"carry no UV, the texture samples ONE flat texel; pick a solid/painted/"
                  f"veneer/proc_wood preset unless the flat read is intended")

    M = {"wall": wall, "mill": mill, "fab": fab, "wood": wood, "fix": fix, "furn": furn,
         "glass": glass}
    # per-ELEMENT presets: the item loop tags primitive-fallback parts `em-<preset>__part`;
    # build one material per preset used and route the prefix here (imported models are
    # handled by the retint path in place_model instead — they keep their own maps).
    for _ep in sorted(set(((sel or {}).get("elements") or {}).values())):
        M[f"em-{_ep}"] = _material_from_preset(f"m_el_{_ep}", _ep)
    if sel:
        print(f"  materials: spec-selected presets -> {_matpre.material_story(sel, spec, _SOFT_BAKED)}")
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or obj.get("ph_model"):   # imported models keep their own PBR
            continue
        n = obj.name
        if n == "floor":
            _planar_uv(obj, tile_m=2.4)
            obj.data.materials.append(floor)
            continue
        if n.startswith("wall_0"):                       # south edge = the hero backdrop
            # per-object sampling offset: neighbouring wall pieces stop showing
            # the SAME plank sequence (judge: grain 'subtle uniformity' family)
            _wall_uv(obj, tile_m=2.2, u_off=_det01(n) * 3.0)  # -> walnut feature wall (PORS-style)
            obj.data.materials.append(feature)
            continue
        if n.startswith("wall") and "__" not in n:
            if _wall_pbr:   # texture preset on walls: give them the feature-wall UV recipe
                _wall_uv(obj, tile_m=2.2, u_off=_det01(n) * 3.0)
            obj.data.materials.append(wall)
            continue
        if n.startswith("mill__"):
            # millwork previously had NO UV -> flat featureless slabs (the 'flat
            # panel' judge datapoint). Round-1 lesson: do NOT map the floor plank
            # texture here (reads as flooring-on-walls, tanked the bedroom A/B) —
            # _veneer is procedural (world-space), no UV needed.
            # OPEN dressing wall + slat backer: the PART TOKEN carries the material (brass rail,
            # cool microcement fronts/tower back, matte-black slat backer); everything else is the
            # oak carcass. mill_object_role is pure (material_presets) so a plain-box fallback whose
            # spec name happens to contain 'front' is NOT mis-painted (it has no part token).
            _role = _matpre.mill_object_role(n)
            obj.data.materials.append(
                {"brass": brass, "microcement": cement, "backing": backing,
                 "caesarstone": caesar, "mirror": mirror,
                 "opal": opal, "blackalu": blackalu,
                 "towel": towel,                     # ELEMENT 6: the terry token's 3rd branch
                 "linen": linen}.get(_role, mill))   # ELEMENT 8: the signed greige linen
            continue
        if n.startswith("rug__"):                        # rug already carries its own PBR
            continue
        key = n.split("__", 1)[0] if "__" in n else "furn"
        obj.data.materials.append(M.get(key, furn))


def _aimed_light(name, ld, pos_m, aim_m):
    """Link a light datablock at pos_m aimed at aim_m (data-API, headless-safe —
    the _add_window_light track-quat pattern)."""
    from mathutils import Vector
    o = bpy.data.objects.new(name, ld)
    o.location = pos_m
    d = Vector(aim_m) - Vector(pos_m)
    if d.length > 1e-9:
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(o)
    return o


def _add_emissive_box(name, x, y, z, dx, dy, dz, color=(1.0, 0.97, 0.92), strength=3.0):
    """A small glowing BOX (visible luminaire body that also lights) — the 6-face
    sibling of _add_emissive's quad, for the element-5 opal task strips."""
    v = [(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
         (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    o.data.materials.append(m)
    o["ph_model"] = True
    return o


def _ies_path(fname):
    """A real LM-63 file from the fetched 30-profile pack (knowledge/lighting/
    ies-and-lighting-notes-discord.md:68-93 maps indices to named luminaires)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(here)), "knowledge", "_inbox",
                        "discord", "MY-DATA-PEAT", "_external-fetched", "sharing",
                        "002_IES", fname)


def _ies_beam(ld, fname, norm=1.0):
    """LANE B (ground-truth study 2026-07-30): attach a real photometric profile to a
    light. The study measured IES 0/30 for us while 30 LM-63 files sat fetched in our
    own knowledge dir — and the one same-genre pro file uses IES on 4/13 lights. The
    beam scallop a real distribution throws on a wall is the visible signature that
    light comes from a FIXTURE; a bare disk can only wash. Story-mode only: the CD
    state's lumen-method compliance math never sees this."""
    p = _ies_path(fname)
    if not os.path.exists(p):
        print(f"  e5 IES: {fname} missing at {p} — light keeps its bare emitter")
        return
    ld.use_nodes = True
    nt = ld.node_tree
    em = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeEmission"), None)
    if em is None:
        em = nt.nodes.new("ShaderNodeEmission")
        out = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputLight"), None)
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputLight")
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    ies = nt.nodes.new("ShaderNodeTexIES")
    ies.mode = 'EXTERNAL'
    ies.filepath = p
    # NORMALIZED, measured, never raw: the b1 quick pair proved raw Fac re-scales the
    # whole rig (room mean 84 -> 166, whites clipping — the profile was supposed to
    # SHAPE the beam, not re-power it; e5's lumen-method watts stay the power
    # authority). `norm` brings this profile's contribution back to plan scale
    # (5.ies candela mean 629 / 7.IES 1947 — per-profile constants, bracketed by
    # frame measurement like every amplitude in this room).
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = float(norm)
    nt.links.new(ies.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], em.inputs["Strength"])


def _add_e5_lights(spec, h_m):
    """ELEMENT 5 (element5-lighting_DD-2026-07-20.md): materialize the pure plan —
    ambient disks (mass-clipped grids), BF11 opal task strips (emissive mesh + aimed
    area), the ensuite bar wash, BF14/tub accent SPOTs, all in the one warm family.
    plan() RAISES on a malformed block -> build()'s top-level guard fails the process
    (never a silent revert). The dome-lamp emitters live in _build_nightstand."""
    from math import radians
    plan = _e5.plan(spec)
    warm = _matpre.parse_light_warm(spec)
    # lane-A light story: photoshoot dimmer state over the SAME signed plan
    # (accent must read ~3x ambient to go focal — the vault row e5 cites)
    _sc = _e5.story_scales(bool(spec.get("_light_story")))
    n = 0
    # VISIBLE LUMINAIRES (lane A, C2 re-critic verdict: "แสงไม่มีที่มา" — the
    # ceiling was bare, so every pool read as light from nowhere; the reference
    # sells because every lux points back at a fixture the eye can find). Each
    # plan position gets a recessed TRIM: a dark ring flush with the ceiling and
    # a warm emissive micro-disk inset — geometry only, the AREA lights still do
    # the actual lighting work at the same signed positions.
    _trim_m = bpy.data.materials.get("e5_trim_dark")
    if _trim_m is None:
        _trim_m = bpy.data.materials.new("e5_trim_dark")
        _trim_m.use_nodes = True
        _b = _trim_m.node_tree.nodes.get("Principled BSDF")
        _b.inputs["Base Color"].default_value = (0.05, 0.045, 0.04, 1.0)
        _b.inputs["Roughness"].default_value = 0.45
    _lens_m = bpy.data.materials.get("e5_trim_lens")
    if _lens_m is None:
        _lens_m = bpy.data.materials.new("e5_trim_lens")
        _lens_m.use_nodes = True
        _nt = _lens_m.node_tree
        _em = _nt.nodes.new("ShaderNodeEmission")
        _em.inputs["Color"].default_value = (1.0, 0.86, 0.70, 1.0)
        _em.inputs["Strength"].default_value = 30.0
        _out = _nt.nodes.get("Material Output")
        _nt.links.new(_em.outputs[0], _out.inputs["Surface"])

    def _recessed_trim(tag, cx, cy, cz):
        _cyl_frustum(f"e5_trim_{tag}", cx, cy, 0.048, 0.048, cz - 0.006, cz - 0.0005,
                     _trim_m, seg=20)
        _cyl_frustum(f"e5_lens_{tag}", cx, cy, 0.032, 0.032, cz - 0.010, cz - 0.007,
                     _lens_m, seg=20)

    for i, f in enumerate(plan["downlights"]):
        _recessed_trim(f"dl{i}", f["x"] * MM, f["y"] * MM, f["z"] * MM)
        # the proven downlight style: AREA disk facing down, deterministic ±12%
        # output spread + a hint of CCT drift (a real ceiling never fires every
        # can at one exact output/colour); positions come mass-clipped from the plan
        ld = bpy.data.lights.new(f"e5_dl_{i}", type='AREA')
        ld.shape = 'DISK'
        ld.size = 0.22
        ld.energy = f["watts"] * (0.88 + 0.24 * _det01(f"e5a{i}")) * _e5.ambient_scale(_sc, f["zone"])
        if spec.get("_light_story"):
            _ies_beam(ld, "5.ies", norm=0.20)    # Halo H7t-301 recessed open trim —
            #                                      the pack's one true recessed-can profile
        drift = 0.985 + 0.03 * _det01(f"e5c{i}")
        ld.color = (warm[0], min(1.0, warm[1] * drift), min(1.0, warm[2] * drift * drift))
        lo = bpy.data.objects.new(f"e5_dl_{i}", ld)
        lo.location = (f["x"] * MM, f["y"] * MM, f["z"] * MM)
        bpy.context.scene.collection.objects.link(lo)
        n += 1
    for s in plan["strips"]:
        bx, by, bz, dx, dy, dz = s["box"]
        _add_emissive_box(s["name"], bx * MM, by * MM, bz * MM, dx * MM, dy * MM, dz * MM)
        L = s["light"]
        ld = bpy.data.lights.new(f"{s['name']}_L", type='AREA')
        ld.shape = 'RECTANGLE'
        ld.size = L["size"][0] * MM          # strip width
        ld.size_y = L["size"][1] * MM        # luminous length (the mirror field)
        ld.energy = L["watts"] * _sc["strips"]
        ld.color = warm
        _aimed_light(f"{s['name']}_L", ld,
                     (L["x"] * MM, L["y"] * MM, L["z"] * MM),
                     (L["aim"][0] * MM, L["aim"][1] * MM, L["aim"][2] * MM))
        n += 1
    b = plan["bar"]
    ld = bpy.data.lights.new("e5_bar_wash", type='AREA')
    ld.shape = 'RECTANGLE'
    ld.size = b["size"][0] * MM              # the 2m bar length IS the softness (PH-05)
    ld.size_y = b["size"][1] * MM
    ld.energy = b["watts"] * _sc["bar"]
    ld.color = warm
    _aimed_light("e5_bar_wash", ld, (b["x"] * MM, b["y"] * MM, b["z"] * MM),
                 (b["aim"][0] * MM, b["aim"][1] * MM, b["aim"][2] * MM))
    n += 1
    for s in plan["spots"]:
        _recessed_trim(s["name"], s["x"] * MM, s["y"] * MM, s["z"] * MM)
        ld = bpy.data.lights.new(s["name"], type='SPOT')
        ld.energy = s["watts"] * _sc["spots"]
        ld.color = warm
        ld.spot_size = radians(s["cone_deg"])
        ld.spot_blend = s["blend"]
        ld.shadow_soft_size = 0.03           # physical emitter radius -> real penumbra (PH-05)
        if spec.get("_light_story"):
            _ies_beam(ld, "7.IES", norm=0.065)   # Kurt Versen B7424 directional — the
            #                                      wall-wash scallop the references show
        _aimed_light(s["name"], ld, (s["x"] * MM, s["y"] * MM, s["z"] * MM),
                     (s["aim"][0] * MM, s["aim"][1] * MM, s["aim"][2] * MM))
        n += 1
    # E5 AMENDMENT (round-6 gate #8 — the same ask stood at three gates with four
    # judges unanimous: pools need a FINDABLE fixture). Geometry + light for the
    # cove and the sconce pair; positions all derive from the plan's own numbers.
    cv = plan["cove"]
    _pel_m = _solid("e5_pelmet", (0.32, 0.21, 0.13, 1.0), rough=0.5, spec=0.4)
    _rbox("e5_cove_pelmet", (cv["face_x"] - cv["off"] - 20.0) * MM, cv["y0"] * MM,
          cv["z"] * MM, 0.020, cv["len"] * MM, 0.140, _pel_m, bevw=0.003)
    #      20mm board from the cove line up to a 10mm ceiling shadow gap (COVE_DROP
    #      is 150 by construction) — the fascia the eye finds when it asks where
    #      the wall graze comes from
    cld = bpy.data.lights.new("e5_cove", type='AREA')
    cld.shape = 'RECTANGLE'
    cld.size = 0.04
    cld.size_y = cv["len"] * MM * 0.96
    cld.energy = cv["watts"] * _sc.get("cove", 1.0)
    cld.color = warm
    _aimed_light("e5_cove", cld,
                 (cv["face_x"] * MM - cv["off"] * MM, (cv["y0"] + cv["len"] / 2.0) * MM,
                  cv["z"] * MM),
                 (cv["face_x"] * MM, (cv["y0"] + cv["len"] / 2.0) * MM,
                  cv["z"] * MM - 1.2))          # graze DOWN the slat face
    n += 1
    _sc_body = _solid("e5_sconce_body", (0.60, 0.44, 0.20, 1.0), rough=0.32,
                      metallic=1.0, spec=0.6, aniso=0.65)
    for s in plan["sconces"]:
        sx, sy, sz = s["x"] * MM, s["y"] * MM, s["z"] * MM
        # body: a brass cylinder standing 70mm off the slat face
        _cyl_frustum(s["name"], sx - 0.045, sy, 0.030, 0.030, sz - 0.070, sz + 0.070,
                     _sc_body, seg=16)
        for tag, aim_dz in (("up", 1.0), ("dn", -1.0)):
            ld = bpy.data.lights.new(f"{s['name']}_{tag}", type='SPOT')
            ld.energy = s["watts"] * _sc.get("sconces", 1.0) * 0.5
            ld.color = warm
            ld.spot_size = radians(85.0)
            ld.spot_blend = 0.9
            ld.shadow_soft_size = 0.02
            if spec.get("_light_story"):
                _ies_beam(ld, "1.IES", norm=0.10)    # BEGA 6339 surface wall luminaire
            _aimed_light(f"{s['name']}_{tag}", ld, (sx - 0.045, sy, sz + aim_dz * 0.075),
                         (sx, sy, sz + aim_dz * 1.0))
            n += 1
    c = plan["meta"]["counts"]
    drops = plan["meta"]["dropped"]
    print(f"  e5 lights: {c['downlights']} ambient + {c['strips']} strips + bar + "
          f"{c['spots']} spots + cove + {c['sconces']} sconces placed ({n} sources; "
          f"lamps glow via _build_nightstand); "
          f"clipped {len(drops)} grid can(s) inside full-height masses: "
          f"{sorted({d['mass'] for d in drops})}")
    return n


def add_interior_lights(spec, h_m):
    """Place warm ceiling lights at the SAME positions as the RCP lighting layout
    (suite_lighting), so the render is lit like the room's real fixture plan — the
    single biggest lift from 'grey massing' to 'a lit room'.
    ELEMENT 5: a spec carrying lighting schema e5-layers@0.1 gets the DESIGNED
    3-layer plan instead (_add_e5_lights). Every other spec keeps this legacy path
    UNCHANGED except one disclosed delta: suite_lighting.TARGET_LUX['wet'] 200->270
    (D-E5-2, the wired-band fix) re-sizes legacy wet-zone grids too — scrutiny
    2026-07-21 corrected the earlier 'byte-identical' overclaim."""
    if _e5.applies(spec):
        return _add_e5_lights(spec, h_m)
    try:
        import suite_lighting
        fixtures, _ = suite_lighting.plan_lighting(spec)
    except Exception as e:
        print(f"  (interior lights skipped: {e})")
        return 0
    # ceiling-fixture CCT. Default = the gate-proven 2400 K amber. A spec MAY cool it
    # (`light_warm`: [r,g,b]) when a warm cast fights the design — element-1's cool-ground
    # palette (D1-A) needs a 3000 K warm-white, not amber, or the oak-bounce drowns the cool
    # plaster (proven by LOOK, 2026-07-16). No block -> the amber, byte-identical. A malformed
    # block RAISES (parse_light_warm) -> fail loud via build()'s top-level guard, not a silent lie.
    warm = _matpre.parse_light_warm(spec)
    watt = {"ambient": 16.0, "task": 40.0, "accent": 26.0}
    # the ACCENT wall-wash renders as ONE perfect pool -> the hybrid pass paints a
    # 'perfectly uniform glow of the linear accent lighting' (v004pro judge, the
    # strip-light 0.5-gap datapoint). Real wall-washers SCALLOP: split the accent
    # into a graded 3-pool run along the feature builtin's long axis. Energy
    # fractions sum to 1.0 so total accent output (and scene exposure) is unchanged.
    focal = next((b for b in spec.get("builtins", [])
                  if b.get("kind") in ("headboard_tv", "feature", "tv")), None)
    acc_axis = None
    if focal:
        acc_axis = ((1.0, 0.0) if float(focal.get("w", 0)) >= float(focal.get("d", 0))
                    else (0.0, 1.0))
    n_placed = 0
    for i, f in enumerate(fixtures):
        # AREA (disk) facing straight DOWN (an area light emits along its local -Z, and a
        # zero-rotation light already points down) -> a real downlight POOL on the floor/
        # furniture, instead of a point light that wastes half its output up the open top.
        base_e = watt.get(f.get("layer", "ambient"), 16.0)
        pools = [(0.0, 1.0)]
        if f.get("layer") == "accent" and acc_axis:
            pools = [(-0.45, 0.28), (0.0, 0.42), (0.45, 0.30)]   # graded scallops
        for k, (off, frac) in enumerate(pools):
            ld = bpy.data.lights.new(f"light_{i}_{k}", type='AREA')
            ld.shape = 'DISK'
            ld.size = 0.22 if len(pools) == 1 else 0.17
            # deterministic ±12% per-fixture spread + a hint of CCT drift: a real
            # ceiling never fires every can at one exact output/colour. RCP
            # POSITIONS stay exact — only output varies (mean multiplier = 1.0).
            ld.energy = base_e * frac * (0.88 + 0.24 * _det01(f"e{i}_{k}"))
            drift = 0.985 + 0.03 * _det01(f"c{i}_{k}")
            ld.color = (warm[0], min(1.0, warm[1] * drift), min(1.0, warm[2] * drift * drift))
            lo = bpy.data.objects.new(f"light_{i}_{k}", ld)
            ox = acc_axis[0] * off if (acc_axis and len(pools) > 1) else 0.0
            oy = acc_axis[1] * off if (acc_axis and len(pools) > 1) else 0.0
            lo.location = (float(f["x"]) * MM + ox, float(f["y"]) * MM + oy, h_m - 0.06)
            bpy.context.scene.collection.objects.link(lo)
            n_placed += 1
    print(f"  placed {n_placed} warm interior lights (area, RCP positions, "
          f"deterministic output spread{', accent scalloped' if acc_axis else ''})")
    return n_placed


# CC0 Poly Haven models per furniture KIND (downloaded by pipeline/assets.py, cached in
# raw/assets/cc0/models/<slug>/). A real sofa/chair/table beats a primitive box. Kinds not
# mapped (bed/platform/vanity) fall back to furniture.py primitives.
# MODERN CC0 models (Poly Haven) per kind. Swapped 2026-07-01 off the vintage/gothic
# Sofa_01/ArmChair_01 (which made the render read as antique) to modern seating that
# matches the luxury-modern reference. Kinds not mapped fall back to furniture.py primitives.
# Kinds whose material is upholstery: an acquired mesh of one of these gets the
# signed textile retint so it joins the room's palette instead of arriving in whatever
# colour a stranger's model was uploaded in.
_UPHOLSTERED = ("sofa", "loveseat", "armchair", "chair", "lounge_chair", "stool",
                "bench", "ottoman")

MODEL_MAP = {
    # Poly Haven's CC0 sofas are dark leather / carved wood (traditional). We use the real
    # detailed sofa_02 (tufted) but RETINT its dark upholstery to cream boucle (retint_fabric
    # below) so it reads modern-luxury instead of a vintage leather Chesterfield.
    "sofa": "sofa_02",
    "loveseat": "sofa_02",
    "armchair": "modern_arm_chair_01",
    "lounge_chair": "mid_century_lounge_chair",
    "coffee_table": "coffee_table_round_01",
    "round_table": "coffee_table_round_01",
    "side_table": "coffee_table_round_01",
    "nightstand": "ClassicNightstand_01",
    # NO "bench" entry. It used to map to Ottoman_01 and was DEAD CODE: the item loop intercepts
    # kind=="bench" into _build_bench BEFORE MODEL_MAP is consulted, so the ottoman has not been
    # placed since 2026-07-11. Leaving the mapping in was a lie about what the renderer does — and
    # it let me tell that lie in a commit message (the "model_fit refuses the Ottoman blob" story:
    # true of the ALGEBRA and of the v01/v03 renders, but the gate is not what stops it today).
}

# THE ONE FACING CONVENTION (2026-07-12: measured, then pinned — see test_facing_convention.py).
#
#   spec `rot`  ->  the piece's FRONT points  (sin rot, -cos rot)   [rot 0 = -Y = SOUTH, CCW]
#   front azimuth (deg, +X=0, +Y=90)  =  rot - 90
#
# Stated identically in facing_reader._FACING {0:S, 90:E, 180:N, 270:W}, placement_logic._front_vec,
# cross_signal, build_floor.add_oriented_box and _head_dir below (which spells the same thing on the
# BACK vector: head = -front, so the v4 bed at rot 270 has its head EAST and faces WEST). There is
# only ONE convention; an earlier note in millwork.py claiming two contradictory ones was wrong and
# is retracted.
#
# MODEL_FRONT_DEG = the azimuth each imported glTF's FRONT points at when place_model is passed 0.
# It was "calibrated by inspecting a render" and half the table was MISSING, which made the plain
# path fail-OPEN (an un-listed model got raw rot with no declared front at all). Now MEASURED, not
# asserted: every mesh was imported headless and shot in orthographic elevation from the SOUTH —
# all nine present their FRONT to that camera, so every native front is -Y = -90 deg.
#
# THE LAW (one line, used by BOTH the plain and the auto-face paths below):
#       place_model.rot  =  (desired world FRONT azimuth)  -  MODEL_FRONT_DEG[slug]
#                        =  spec_rot - 90 - MODEL_FRONT_DEG[slug]
# It collapses to the raw spec `rot` only BECAUSE every entry here is -90. Written out explicitly so
# that adding a model whose front is not -Y cannot silently rotate a room's furniture.
MODEL_FRONT_DEG = {
    # measured: FRONT faced the south camera in the ortho probe
    "modern_arm_chair_01": -90.0,
    "mid_century_lounge_chair": -90.0,
    "sofa_02": -90.0,
    "sofa_03": -90.0,
    "Sofa_01": -90.0,
    "ArmChair_01": -90.0,
    "ClassicNightstand_01": -90.0,     # open-front cabinet; its opening faced the south camera
    # no meaningful front (rotation-invariant); listed so the completeness check cannot fail open
    "Ottoman_01": -90.0,               # upholstered box
    "coffee_table_round_01": -90.0,    # round
}
# Every MODEL_MAP slug MUST have an entry (test_facing_convention pins this). A missing entry used
# to mean "raw rot, native front unknown" — a silent, unbounded rotation error.
assert set(MODEL_MAP.values()) <= set(MODEL_FRONT_DEG), \
    f"MODEL_MAP slugs missing a measured native front: {set(MODEL_MAP.values()) - set(MODEL_FRONT_DEG)}"


def model_rot(spec_rot, slug):
    """The Z-rotation place_model must apply, from the spec's facing and the mesh's native front.
    PURE. See THE LAW above. Returns spec_rot unchanged while every native front is -90."""
    return float(spec_rot) - 90.0 - MODEL_FRONT_DEG.get(slug, -90.0)


def _rotate_about_z(objs, cx, cy, deg):
    """Rotate objects CCW by `deg` about the world-Z axis through (cx, cy) — the SAME sense and the
    SAME pivot as build_floor.add_oriented_box and place_model. Metres. No-op at deg 0."""
    if not objs or not deg:
        return
    import math
    from mathutils import Matrix, Vector
    piv = Vector((cx, cy, 0.0))
    T = (Matrix.Translation(piv) @ Matrix.Rotation(math.radians(float(deg)), 4, 'Z')
         @ Matrix.Translation(-piv))
    bpy.context.view_layer.update()
    for o in objs:
        o.matrix_world = T @ o.matrix_world
    bpy.context.view_layer.update()


def _rbox(name, x0, y0, z0, w, d, hgt, mat, bevw=0.02, seg=3):
    """A rounded (bevel-modifier) box with a material — the primitive for procedural
    modern furniture. Soft edges are what separate a modern-luxury cushion from a CG cube."""
    o = add_box(name, x0, y0, z0, w, d, hgt)
    o.data.materials.append(mat)
    o["ph_model"] = 1                       # skip the global 1mm _bevel_edges (we bevel here)
    m = o.modifiers.new("bev", 'BEVEL')
    m.width = bevw; m.segments = seg; m.limit_method = 'ANGLE'; m.angle_limit = 0.5236
    # use_smooth, like every other curved surface in this file (curtains, sheers,
    # _smooth_mesh_obj) — the unapplied bevel inherits face smoothness. Without it the
    # 3–5 flat segments render as stair-step value plateaus (LOOK round-2 #1: bench
    # seat banded 142→84 in ~18 px steps; same terracing on mattress rolls, bed base,
    # nightstands). The faces are planar, so smoothing costs the flats nothing.
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def _build_modern_sofa(x0, y0, W, D):
    """Build a clean low-profile MODERN sofa from beveled primitives, back to the SOUTH wall,
    facing +Y (the room). All three CC0 sofas are vintage Victorian/baroque — they fight the
    modern slat wall + mid-century chairs. Modern-luxury seating is geometrically simple (a low
    plinth + boxy bouclé cushions + low arms), so we model it to MATCH instead of retinting a
    Chesterfield. Colours = the same cream bouclé as the retint (#DCD0BD-ish), honed matte."""
    boucle = _woven("sofa_boucle", (0.86, 0.81, 0.72, 1.0), 0.9,
                    _matpre.cloth_args("boucle"), sheen=1.0, spec=0.4)
    base   = _woven("sofa_base",   (0.70, 0.66, 0.60, 1.0), 0.75,
                    _matpre.cloth_args("plain"), sheen=0.25, spec=0.4)
    arm_w, back_d, plinth_h = 0.24, 0.22, 0.14
    # 1) plinth (grounds the piece, slightly darker greige)
    _rbox("sofa__plinth", x0, y0, 0.0, W, D, plinth_h, base, bevw=0.01)
    # 2) low arms (left + right)
    _rbox("sofa__armL", x0, y0, plinth_h, arm_w, D, 0.44, boucle, bevw=0.03)
    _rbox("sofa__armR", x0 + W - arm_w, y0, plinth_h, arm_w, D, 0.44, boucle, bevw=0.03)
    # 3) upholstered back slab (between the arms, at the wall side)
    inner = W - 2 * arm_w
    _rbox("sofa__back", x0 + arm_w, y0, plinth_h, inner, back_d, 0.58, boucle, bevw=0.03)
    # 4) single BENCH seat cushion (cleaner/more modern than a split — no stark centre seam)
    seat_y = y0 + back_d; seat_d = D - back_d - 0.02
    _rbox("sofa__seat", x0 + arm_w, seat_y, plinth_h, inner, seat_d, 0.22, boucle, bevw=0.04)
    # 5) back cushions (2) — plump, leaning against the back slab, proud of the seat
    gap = 0.03; cw = (inner - gap) / 2.0
    for i in range(2):
        cx = x0 + arm_w + i * (cw + gap)
        _rbox(f"sofa__bk{i}", cx, y0 + back_d - 0.03, plinth_h + 0.22, cw, 0.18, 0.34,
              boucle, bevw=0.05)
    # 6) accent scatter cushions — the ONE hit of colour a stylist adds so the group isn't a
    # monochrome cream blob (muted terracotta + sage, the classic warm-neutral accent pair).
    # Placement rules learned the hard way: (a) keep bevw < half the smallest dimension or the
    # bevel collapses the mesh; (b) sit them ON the seat and clearly IN FRONT of the backrest —
    # if they interpenetrate the back cushion, coincident faces z-fight into a translucent ghost.
    _pln = _matpre.cloth_args("plain")
    terra = _woven("cush_terra", (0.58, 0.32, 0.23, 1.0), 0.75, _pln, sheen=0.6, spec=0.4)
    sage  = _woven("cush_sage",  (0.44, 0.46, 0.37, 1.0), 0.75, _pln, sheen=0.6, spec=0.4)
    pw, pd, ph = 0.46, 0.22, 0.44
    # tuck the pillows into the arm+back corners (where a stylist puts them). With normals now
    # recalculated the bevel is clean, so they can nestle against the backrest without ghosting.
    scat_y = y0 + back_d + 0.02
    for cx, mat in ((x0 + arm_w + 0.03, terra),
                    (x0 + W - arm_w - 0.03 - pw, sage)):
        _rbox(f"sofa__scatter_{'L' if mat is terra else 'R'}", cx, scat_y,
              plinth_h + 0.20, pw, pd, ph, mat, bevw=0.06, seg=4)
    return True


def _head_dir(rot):
    """Unit vector the bed's HEAD points along, snapped to the dominant cardinal.

    furniture.py's convention (its module docstring): at rot=0 a headboard sits on the +Y
    (far) side. `rot` rotates the piece CCW, so the head direction is R(rot)·(0,1) =
    (-sin rot, cos rot) — rot 270 -> (+1, 0) = head EAST, which is exactly the v4 master bed
    ("head EAST vs the BF14 slat wall", rot 270). Returns ('x'|'y', +1|-1)."""
    import math                      # module-local, matching this file's import style
    a = math.radians(float(rot or 0.0))
    hx, hy = -math.sin(a), math.cos(a)
    if abs(hx) >= abs(hy):
        return "x", (1 if hx > 0 else -1)
    return "y", (1 if hy > 0 else -1)


def _build_bed(x0, y0, W, D, H, rot=0.0):
    """A real platform bed massed from beveled primitives, ROT-AWARE — base + inset mattress +
    draped duvet + two pillows at the HEAD.

    WHY THIS EXISTS (2026-07-11): the primitive fallback path (`furniture.parts`) is called
    WITHOUT `rot` — build_room only ever passed rot to `place_model`. furniture._bed hardcodes
    the headboard/pillows on the +Y side, so the v4 master bed (rot 270 = head EAST, against the
    BF14 slat wall) was massed with its HEAD ON THE WRONG SIDE. That is not just cosmetic: the
    clay is the STRUCTURAL CONTROL for the Gemini pass, so a head-on-the-wrong-side bed told the
    beauty pass the feature wall was on the left — which is exactly what it painted (v01
    rendered the left-hand wardrobe BF09-3 as the headboard wall and lost BF14). Fixing the
    massing fixes the render's millwork identity at the source.

    CAD-SAFE: every part is built INSIDE the spec's authoritative footprint (x, y, w, d) — the
    plan-measured bbox never moves. Only pillows rise a few cm above the declared massing height
    (they sit ON the mattress, as real pillows do). NO separate tall headboard is modelled: in
    this suite the headboard IS the wall (BF14 = "ผนังระแนงหัวเตียง", the bed-head slat wall), so
    adding one would duplicate owner-confirmed millwork."""
    axis, sign = _head_dir(rot)
    along = W if axis == "x" else D          # head->foot length
    across = D if axis == "x" else W

    def box(from_head, across_off, a_size, c_size):
        """Place a part `from_head` metres back from the HEAD edge, `across_off` from the
        near side — in bbox coords, whichever way the bed faces. Returns (x, y, dx, dy)."""
        if axis == "x":
            x = (x0 + W - from_head - a_size) if sign > 0 else (x0 + from_head)
            return x, y0 + across_off, a_size, c_size
        y = (y0 + D - from_head - a_size) if sign > 0 else (y0 + from_head)
        return x0 + across_off, y, c_size, a_size

    def emit(name, from_head, across_off, a_size, c_size, z, dz, mat, bevw, seg=3):
        """Emit a bedding part ONLY if it lies wholly inside the bbox.

        The CAD-safety invariant ("the plan-measured footprint never moves") is enforced HERE,
        by construction — not assumed. An earlier cut sized these parts with `max(..., floor)`
        clamps; on a small bed those floors pushed a pillow OUTSIDE the footprint (a 0.35 m-wide
        bed put pillow1 clear of the bbox). Unreachable on today's specs, but a clamp that can
        silently break the one invariant this whole builder rests on is not something to ship.
        A degenerate/tiny bed now simply gets FEWER parts (base + mattress always survive)."""
        if a_size <= 0.01 or c_size <= 0.01:
            return None
        if from_head < -1e-9 or from_head + a_size > along + 1e-9:
            return None
        if across_off < -1e-9 or across_off + c_size > across + 1e-9:
            return None
        bx, by, bdx, bdy = box(from_head, across_off, a_size, c_size)
        # returns the object so a later cloth bake can COLLIDE with it (the throw
        # must drape over the duvet, not through it). None on the reject paths above
        # keeps that honest: a caller cannot collide with a part that was not built.
        return _rbox(name, bx, by, z, bdx, bdy, dz, mat, bevw=bevw, seg=seg)

    # ELEMENT 3 D3-1 (2026-07-18): the base is UPHOLSTERED GREIGE STONEWASHED LINEN, not the old
    # dark (0.40,0.36,0.32) that read wood-brown — and deliberately NOT oak (D1-A anti-monopoly:
    # four oak masses already; a fifth on the hero bed breaks 60-30-10). High roughness + LOW
    # sheen = matte linen weave. That identity is unchanged and not reopened.
    # D3-1's RATIONALE IS SUPERSEDED (2026-07-23, owner loop OPEN — value_ladder.py header).
    # It used to read: "A LIGHT greige linen joins the ~60% plaster ground (Albers: a light
    # element on a light ground recedes — the curtain-DR grounding, 3ce5f5e), so the warm oak
    # slat headboard wall + the crisp bedding carry the eye", and it noted the base had already
    # been "darkened + de-sheened so the platform plinth grounds the bed" after v1 at 0.58
    # "washed to the same white as the mattress ... the bed read as one pale blob; LOOK
    # 2026-07-18". Those two sentences were pulling in opposite directions and the second one
    # was right: measured, this cloth rendered 121.1 on the plinth, 155.1 on the throw and
    # 178.2 on the BENCH — 13 codes ABOVE the coverlet the bench stands in front of. A light
    # element on a light ground does recede; the piece the eye lands on first should not be
    # asked to. So the base joins the ladder's DEEPEST rung and grounds the bed, which is what
    # the 07-18 LOOK asked for and what the 07-18 Albers sentence prevented.
    # WOVEN, not _solid (2026-07-22): these five are the largest textile area in the hero
    # frame and every one of them was an untextured slab — the MA-05 "plastic look" the
    # owner has been describing since element 3. Bedding is stonewashed LINEN by D3-2, so
    # base, mattress, duvet, pillow and coverlet all wear the linen signature; the colours,
    # roughness and sheen weights below are the LOOK-tuned values and are untouched.
    # 2026-07-23 — THE COLOURS LEAVE THIS FUNCTION. Every tuple below used to be typed
    # here beside a paragraph arguing for it, and the ladder those tuples actually produced
    # in the render had never been measured. It has now (object-id probe, hero frame):
    # six of the bed's ten pieces rendered inside 7.1 sRGB codes of each other, the
    # duvet's own turned-back FOLD was the brightest object in the bed because it wore the
    # PILLOW material, and the pillows shipped at sRGB 243.5 — past the studio's own 30-240
    # dielectric ceiling, which the bespoke path never applied. (The mattress at 0.87 =
    # 239.8 was inside it; the review corrected a first draft that indicted both.) value_ladder.py owns all of
    # it now: ONE greige hue in five cloths, each checked against the band, the ladder
    # stated in RENDERED value and the albedos solved against the measurement. The count
    # is not repeated here on purpose — value_ladder.cloths_by_tone() is the one source,
    # and a "seven" in this sentence survived a revision that made it five.
    # Roughness/sheen/spec below are element 3's LOOK-tuned values and are untouched.
    _lin = _matpre.cloth_args("linen")
    # maps="rough_linen" (lane B): the CC0 2k linen set fetched 2026-07-2x and never
    # consumed — the study found the store itself was distilled-but-never-wired
    base_m = _woven("bed_base",     _vl.rgba("bed_base"),     0.94, _lin, sheen=0.2, spec=0.25, maps="rough_linen")
    matt_m = _woven("bed_mattress", _vl.rgba("bed_mattress"), 0.92, _lin, sheen=0.5, spec=0.35, maps="rough_linen")
    duvt_m = _woven("bed_duvet",    _vl.rgba("bed_duvet"),    0.95, _lin, sheen=0.7, spec=0.35, maps="rough_linen")
    pill_m = _woven("bed_pillow",   _vl.rgba("bed_pillow"),   0.95, _lin, sheen=0.8, spec=0.35, maps="rough_linen")
    # THE EURO SHAMS JOIN THE DUVET SET. They were sharing pill_m, so the head's three-rank
    # ladder — built in element 8 because "three heights is the single most recognisable
    # signal of a styled bed" — rendered as three heights of ONE value: sham0 199.6 against
    # pillowsoft0 200.6, one code apart, at the focal point of the frame. Height without
    # value is not a ladder. A duvet cover and its euro shams are one fabric in every
    # bedding set ever sold, so this is not a new cloth — it is the cloth they were always
    # supposed to be, and it puts them 33 codes under the pillowcases in front.

    # SOFT, LOW-DRAPED MASSING (owner LOOK 2026-07-18 "ยังเหลี่ยม" ×2 — bevels alone did NOT break the
    # box; a bed reads as a bed when CLOTH DRAPES over the edges, not when a slab has round corners).
    # (1) a LOW recessed plinth (pulled in 100 mm, a hidden toe) minimises the solid mass; (2) the
    # mattress insets UNDER (3) a full-width COVERLET that overhangs the mattress and FALLS down its
    # sides to just above the plinth — breaking the hard vertical faces into draped fabric and leaving
    # a shadow reveal beneath. That silhouette reads "a made bed", not "a foam cube".
    cov_m = _woven("bed_coverlet", _vl.rgba("bed_coverlet"), 0.96, _lin, sheen=0.3, spec=0.3,
                   maps="rough_linen")
    base_h = H * 0.34                                   # a LOW recessed plinth (a hidden toe)
    binset = 0.10                                       # pulled well IN — the coverlet drapes PAST it
    _base_o = _rbox("bed__base", x0 + binset, y0 + binset, 0.0, W - 2 * binset, D - 2 * binset,
                    base_h, base_m, bevw=0.03, seg=4)
    mins = 0.09                                         # mattress inset — hides UNDER the coverlet
    # bevw 0.05 -> 0.075, seg 5 (round-6 lane C, Gemini: "ฟูกหนาและขอบคมเป็นกล่อง") — the
    # visible sliver of mattress between coverlet and duvet is all EDGE, so its radius
    # is the whole read; 75mm on a ~400mm side is a real mattress roll, not a box arris
    _matt_o = _rbox("bed__mattress", x0 + mins, y0 + mins, base_h, W - 2 * mins, D - 2 * mins,
                    H - base_h, matt_m, bevw=0.075, seg=5)
    # ELEMENT 8 (2026-07-22) — THE COVERLET STOPS BEING A SOLID.
    # The DD's ground phase looked at the render and named one mechanism behind "แข็ง",
    # "เหลี่ยม" and "ไม่มี style": nothing in this room DEFORMS, because every soft good was
    # modelled with joinery's primitive — a bevelled box with a level hem. This block was
    # the largest instance: a single rigid plane occupying ~1/3 of the hero frame, whose
    # own comment claimed it was "the fabric FALL that kills the box". A 70mm bevel is not
    # drape. So the coverlet becomes what a coverlet physically is — a THIN layer lying on
    # the mattress — and its FALL becomes real simulated cloth (drape.bake_bed_cover):
    # creases that grow from nothing at the suspension line to full at the free hem, a
    # multi-wavelength fold pitch that never corrugates, and a hem that is never level.
    # The layer's inset is the drape's own fold amplitude, DERIVED: the skirt's top ring
    # sits exactly at that inset (crease amplitude is zero at the suspension line), so the
    # two meet with no gap. A smaller inset would let this plate's flat face poke through
    # the skirt's inward swings — which is part of why the first render still read flat.
    # 2026-07-22 — SIMULATED. This was a flat plate plus `styling.bed_drape`, a hand-written
    # skirt (golden-ratio creases, a multi-wavelength fold pitch, a wandering hem). It is now
    # ONE sheet of cloth laid over the mattress, overhanging on three sides, dropped under
    # gravity onto the mattress and plinth it must fall past. The fold at the mattress edge,
    # the fold pitch, the way the corners gather and the fact that the hem is not level are
    # all SOLVED — none of them is authored any more, which is why they read as cloth.
    # The decided constraints did NOT move to Blender: the hem still lands DRAPE_REVEAL above
    # bed__base's top so element 3's signed recessed-plinth shadow gap survives, and the
    # baked result is asserted back inside the plan-measured footprint (drape.bake_sheet
    # RAISES on both, and on a sim that failed to advance — a frozen sheet is a flat plane,
    # which is exactly the defect this replaces and must never pass silently).
    cov_top = H + 0.006
    _head_side = "%s%s" % (axis, "+" if sign > 0 else "-")
    _cov_o = drape.bake_bed_cover(
        "bed__coverlet",
        rect=(x0 + mins, y0 + mins, W - 2 * mins, D - 2 * mins),
        top_z=H, hang_to=base_h + styling.DRAPE_REVEAL,
        colliders=[o for o in (_matt_o, _base_o) if o],
        mat=cov_m, head=_head_side, fabric="linen",
        bounds=(x0, y0, 0.0, x0 + W, y0 + D, H + 0.30),
        sim_surface=True, salt=5)     # B2: per-corner bias — the owed lane-C debt
        #                               (C2 twice: corner gathers mirrored L/R)                       # the duvet + throw collide with the
    #                                             SINGLE-SHELL surface, not the
    #                                             solidified render mesh (see drape)
    _cov_o["ph_model"] = 1                              # keep the global 1 mm bevel off cloth
    _SOFT_BAKED.append(_cov_o.name)                     # the armour keys off what BAKED
    cov_t = 0.045                                       # kept: the pure layer's layer-thickness
    cins = styling.DRAPE_FOLD                           # kept: pillow/duvet insets derive from it

    # duvet: a THIN cloth layer over the foot ~2/3, inset so the mattress edge still shows, and
    # dipping slightly INTO the mattress top so it reads as cloth lying on it, not a second slab.
    # NOTE: sizes below are computed, never floor-clamped — `emit` drops any part that would not
    # fit, so the footprint invariant holds for any bed size (see emit's docstring).
    # ELEMENT 8: the pillow zone is now the THREE-RANK head ladder, RE-DERIVED rather than
    # added behind. Both DD critics independently ran the numbers and found the same
    # blocker: the bed's head edge lands at x5204 and BF14's slat face at x5203, so the
    # head is FLUSH with the wall — there is no space BEHIND the old two pillows to stand
    # euro shams in. `pz` therefore comes from styling.head_ranks (one source, so the
    # duvet start cannot drift from the ladder that sets it) and is an element-3 amendment
    # made in the same commit as the element-8 build.
    _ranks, pz = styling.head_ranks(along)
    dv_from = pz + 0.14
    # ELEMENT 3 AMENDED (owner LOOK 2026-07-28 round 3): "เตียงยังดูแปลก ๆ เหมือนก้อนอะไร
    # ซักอย่างอยู่บนผ้าปู" — and the ก้อน was THIS part. The duvet was the last bevelled
    # box on the bed: a 90 mm slab pulled 110 mm in from every edge, an island lump ON
    # the bedding, with a SECOND box lying in front of it playing the turned-back fold.
    # The coverlet and the throw earned their cloth read from the solver; the duvet now
    # gets the same physics: softgoods.folded_sheet pre-bends the head band 180° over
    # the main panel (ONE connected lattice) and the solver settles the crease into the
    # soft roll a hotel fold actually is. It spans the mattress and FALLS PAST its
    # flanks — a duvet covers a bed, it does not sit on one. bed__duvet_fold the OBJECT
    # is gone: the fold is cloth of bed__duvet itself, same duvt_m by construction
    # (value_ladder.BUILT_OBJECTS and the armour test moved with it). The throw still
    # bakes AFTER this with the duvet as a collider, so the foot stack orders itself
    # physically instead of by authored z.
    _dv_w = min(across - 0.06, (across - 2 * mins) + 0.16)   # mattress span + ~80 mm
    #                                                          fall per flank, never the plan edge
    _dv_len = along - dv_from - 0.10                # the throw band owns the foot edge
    _dv_x, _dv_y, _dv_dx, _dv_dy = box(dv_from, (across - _dv_w) * 0.5, _dv_len, _dv_w)

    def _duvet(scale, sl):
        # cell 0.028 -> 0.042 and thickness 0.008 -> 0.018 at round 4-ref: the
        # delivered-bed reference (I-23-023 #499473) shows a comforter with LOFT —
        # large soft billows and a thick rounded hem roll; our 8 mm sheet at 28 mm
        # cells read as a thin blanket pulled tight.
        # salt=7 (round-6 lane C, C2#4): a mirror-symmetric lattice over mirror-
        # symmetric colliders bakes mirror-image corners — the feedstock now enters
        # with per-corner bias so each corner settles its own way
        vs, fs = softgoods.folded_sheet(_dv_x, _dv_y, _dv_dx, _dv_dy, H + 0.03,
                                        band=0.28, head=_head_side, cell=0.042, salt=7)
        # THE CLOTH-STACK CONTACT LAW (earned across fx6→fx8, three failed reads):
        # collide against the coverlet's SINGLE-SHELL sim surface, never its
        # solidified render mesh — a sheet that tunnels between a frozen collider's
        # two shells is trapped and renders as mottled cloth-through-cloth whatever
        # the distance (graze at 0.004, shard-crumple at 0.012, still patched at
        # 0.008). collide_dist then only has to clear the RENDER shells: 0.016 rests
        # this sheet's −9 mm inner half above the coverlet's +3 mm outer half with
        # 4 mm to spare.
        _cprx = drape.sim_surface_of("bed__coverlet")
        return drape.bake_sheet("bed__duvet", vs, fs,
                                [o for o in (_cprx or _cov_o, _matt_o, _base_o) if o],
                                frames=55, fabric="linen", mat=duvt_m,
                                thickness=0.018, slack=sl, collide_dist=0.016,
                                sim_surface=True)
    _duv_o = drape.search_bake(_duvet, name="bed__duvet", slack=0.04,
                               top_z=H + 0.03, hem_min=base_h + styling.DRAPE_REVEAL,
                               bounds=(x0, y0, 0.0, x0 + W, y0 + D, H + 0.35))
    _duv_o["ph_model"] = 1
    _SOFT_BAKED.append(_duv_o.name)

    # ELEMENT 8: THE HEAD LADDER replaces the two identical flat slabs the DD's ground
    # phase named as the loudest CAD tell in the hero frame ("same width, same thickness,
    # same cream value, both lying FLAT with their tops level, mirrored across the
    # centreline"). Three heights — upright euro shams against the slat wall, flat
    # sleeping pillows in front, one accent lumbar — is the single most recognisable
    # signal of a styled bed. Every piece is a softgoods.cushion (a waisted, corner-pinched
    # form) rather than a bevelled slab, and NONE is dented: this owner's two prior
    # rejections were both of things he read as BROKEN rather than ugly, so the DD deletes
    # the slept-in cues on purpose.
    _cov_full = {"x": x0, "y": y0, "z": cov_top - cov_t,
                 "dx": W, "dy": D, "dz": cov_t}
    # DERIVED from value_ladder.HEAD_CLOTH, not typed here. The line this replaces —
    # `{"sham": pill_m, "pillowsoft": pill_m}` — WAS defect 1, and it was a literal inside
    # this function that no test could reach. Now the mapping is data, so reverting it is a
    # visible change to a table the tests read.
    _by_name = {"bed_base": base_m, "bed_mattress": matt_m, "bed_duvet": duvt_m,
                "bed_pillow": pill_m, "bed_coverlet": cov_m}
    _mats = {}
    for _stem, _matname in _vl.HEAD_CLOTH.items():
        if _matname not in _by_name:
            raise RuntimeError(
                f"bed head: value_ladder.HEAD_CLOTH maps {_stem!r} to material "
                f"{_matname!r}, which _build_bed does not weave (has: {sorted(_by_name)})")
        _mats[_stem] = _by_name[_matname]
    for _p in styling.pillow_bank(_cov_full, axis, sign):
        _stem = _p["name"].split("__")[1].rstrip("01")
        if _p["name"].startswith("bed__"):
            # RAISE, never default. This was `_mats.get(_stem, pill_m)`: a new head piece
            # added to pillow_bank would silently have been dressed in the PILLOWCASE — the
            # lightest cloth in the room — which is the precise mechanism that put the euro
            # shams and the duvet's fold at the top of the value ladder in the first place.
            # A silent default is how this defect was built; it does not get to survive the
            # fix for it.
            if _stem not in _mats:
                raise RuntimeError(
                    f"bed head: pillow_bank emitted {_p['name']!r} but no cloth is mapped "
                    f"for stem {_stem!r} (known: {sorted(_mats)}). Add it to value_ladder "
                    f"and to _mats — do not let it inherit a tone")
            _smooth_mesh_obj(_p["name"], _p["verts"], _p["faces"],
                             _mats[_stem], own_mat=True, subsurf=_p.get("subsurf", 0))
        else:                                            # the lumbar wears a suite TOKEN
            _smooth_mesh_obj(_p["name"], _p["verts"], _p["faces"], own_mat=False,
                             subsurf=_p.get("subsurf", 0))
    # THE FOOT THROW — RESTORED 2026-07-22. It shipped DISABLED, and the comment that
    # disabled it said a throw on a compliant flank "is a cloth-on-cloth interaction, and
    # this vocabulary has no collision term". That was true of the hand-written vocabulary
    # and false of the room: the throw is now simulated ONTO the already-baked coverlet and
    # duvet, which are passed as colliders. Cloth-on-cloth is the ordinary case for a solver.
    # It is the only vertical drape a flat-on hero frame would otherwise contain, and the
    # three LOOK failures it accumulated (zigzag silhouette, then tail flaps punching through
    # the coverlet's skirt) were both interpenetration — the thing collision is for.
    # The throw is sized against the COVERLET AS BAKED, not against the bed rect. Three
    # containment failures in a row (20.6 / 16.6 / 6.6 mm) all had the same cause: the
    # throw was cut to the nominal rect, then physically hung off whichever surface under
    # it happened to be widest — first the coverlet's settled fold, then the duvet slab.
    # Where simulated cloth comes to rest is not predictable from its cut, so it is
    # measured. The tail is what remains of the gap to the bed line after the coverlet
    # has taken its share, which makes the invariant hold BY CONSTRUCTION rather than by
    # a tuned constant — and a wider coverlet automatically yields a shorter tail.
    _cbb = drape.world_bbox(_cov_o)
    # the throw is born above the HIGHEST cloth beneath it — the simulated duvet's
    # fold roll now stands ~40 mm proud of the coverlet where the band lies, and a
    # sheet cut below that would be born intersecting its own collider
    _z_top = max(_cbb[5], drape.world_bbox(_duv_o)[5]) if _duv_o else _cbb[5]
    _c_lo, _c_hi = (_cbb[1], _cbb[4]) if axis == "x" else (_cbb[0], _cbb[3])
    _b_lo, _b_hi = (y0, y0 + D) if axis == "x" else (x0, x0 + W)
    # THE THROW FALLS OVER THE FOOT, NOT THE FLANKS. The first four cuts ran it across the
    # bed with tails down both flanks — the classic styling — and every one of them failed
    # containment, because the coverlet's own skirt already spends the 90 mm between the
    # mattress and the plan line and leaves ~30 mm for anything hanging outside it.
    # Measuring that is also what exposed the design error: this hero camera looks straight
    # down the bed from the foot, so flank tails are seen edge-on and read as nothing, while
    # the foot face — the single largest surface in the frame — had no vertical fabric on it
    # at all. Turning the throw through 90 degrees puts its fall where the camera is looking
    # AND where the room actually exists. The cross span is inset from the coverlet's BAKED
    # flanks, so it cannot reach the flank margin the coverlet has already spent.
    _thr_plan = styling.foot_throw(along, across, H, base_h)
    # The band lying ON the bed must outweigh the part cantilevered past the foot, or the
    # throw simply slides off — the first cut put 0.30 m of cloth in mid-air against a
    # 0.50 m band and the whole sheet dragged itself over the foot edge and fell 5.1 m
    # through the floor. Correct physics, wrong instruction. A laid throw is also not
    # DROPPED: it starts a few mm above the coverlet's measured top rather than 100 mm up,
    # so it has no falling momentum to carry it over, and its innermost strip — the one
    # buried under the duvet, invisible — is pinned the way a tucked edge really is.
    if _thr_plan:
        _thr_band, _thr_hang = _thr_plan
        _thr_from = along - _thr_band
        _t_in = styling.THROW_INSET                     # coverlet shoulder left showing
        def _throw(scale, sl):
            hang = _thr_hang * scale
            tx, ty, tdx, tdy = box(_thr_from, (_c_lo + _t_in) - _b_lo,
                                   _thr_band + hang, (_c_hi - _c_lo) - 2 * _t_in)
            # born ABOVE the collision field, not at its boundary: a sheet cut at
            # exactly collide_dist from the duvet's roll starts inside the repulsion
            # zone and the ejection impulse crumples the whole band into shards
            # (fx7's torn-cloth read — the bbox guards cannot see a contained crumple)
            vs, fs = softgoods.flat_sheet(tx, ty, tdx, tdy, _z_top + 0.020, cell=0.022)
            # FULL slack only on the part lying on the bed; the FALL gets a PARTIAL
            # weight, not zero. Zero was the first cut, and LOOK round-2 #2 read the
            # result off the render: the largest cloth face in both frames (~1.4 m of
            # drop face) was a fold-less slab with a near-level hem — a taut cantilever
            # is the e8 "painted slab" rebuilt by the containment fix itself. The
            # weight is 0.30, and the reason it is not higher is measured, not taste:
            # the coverlet's own foot skirt already spends the 90 mm inset (its face
            # settles ~3-15 mm inside the plan line), so there is NO room outboard for
            # deep folds of the throw's own — at 0.45 the stack sat 10 mm proud of the
            # plan line at every slack the ladder tried. What the fall CAN do in that
            # space is stop BRIDGING the coverlet's fold crests: with modest excess it
            # conforms into the troughs beneath (collision does the shaping), which is
            # what makes cloth-over-cloth read, and the inherited undulation un-levels
            # the hem.
            _on = softgoods.verts_in_rect(vs, max(tx, x0), max(ty, y0),
                                          min(tx + tdx, x0 + W), min(ty + tdy, y0 + D))
            _wts = {i: 0.30 for i in range(len(vs))}
            _wts.update({i: 1.0 for i in _on})
            pw = 0.05
            if axis == "x":
                px = (tx + tdx - pw) if sign > 0 else tx
                tpin = softgoods.verts_in_rect(vs, px, ty, px + pw, ty + tdy)
            else:
                py = (ty + tdy - pw) if sign > 0 else ty
                tpin = softgoods.verts_in_rect(vs, tx, py, tx + tdx, py + pw)
            return drape.bake_sheet(
                "bed__throw", vs, fs,
                # single-shell sim surfaces of both cloths beneath (the contact law
                # in _duvet's comment); the render meshes stay out of the collider
                # list or their solidified shells would fight the proxies
                [o for o in (drape.sim_surface_of("bed__duvet") or _duv_o,
                             drape.sim_surface_of("bed__coverlet") or _cov_o,
                             _matt_o, _base_o) if o], pin=tpin,
                # "wool" (bending 3.0) was wrong twice over: at 75 frames the tails went
                # FURTHER out than at 48, so they were not still swinging — a stiff cloth
                # draped over the coverlet's soft rounded flank BOWS instead of hanging,
                # the same "curved card" failure the hand-written vocabulary had,
                # reproduced in the solver by asking for the wrong fabric. Linen hangs.
                # The throw wears the SUITE'S GREIGE LINEN — base_m, the identity already
                # carried by the bed base and the foot bench (element 3 bundles them), not a
                # new colour: the palette is closed. The first bake gave it cov_m and it was
                # INVISIBLE, cream cloth on a cream bed. That is the whole job of this piece
                # — it is the one deep mass that breaks a hero frame otherwise filled by a
                # single value of near-white — and under the old tone it was NOT doing it:
                # it rendered 155.1 against a coverlet at 164.8, 9.7 codes from the thing it
                # was there to break. The fix is the tone, not a second material: the same
                # base_m now renders 98 here and 134 on the bench, because this surface lies
                # flat in the bed's own shadow and that one is not. The light was always
                # going to separate them; the cloth just had to be deep enough to let it.
                # 0.015 above the single-shell proxy = this sheet's −3 mm render
                # half + the duvet's +9 mm (thickness 0.018 at round 4-ref), with
                # 3 mm to spare (the contact law)
                frames=70, fabric="knit", mat=base_m, thickness=0.006, slack=sl,
                slack_verts=_wts, collide_dist=0.015)
        # Same ladder as the coverlet, for the same reason: this piece also failed on a
        # hand-picked length (2.7 mm past the plan line at the foot) and the number that
        # would have fixed it is only correct for this one bed.
        _thr_o = drape.search_bake(_throw, name="bed__throw", slack=0.10,
                          top_z=_z_top, hem_min=base_h + styling.DRAPE_REVEAL,
                          bounds=(x0, y0, 0.0, x0 + W, y0 + D, H + 0.35))
        _thr_o["ph_model"] = 1
        _SOFT_BAKED.append(_thr_o.name)
    # SWAP-AND-DEMAND-RED: the anti-repaint armour states whether a throw exists by
    # re-running styling.foot_throw. If this build ever stops honouring that same answer,
    # the prose would promise a throw the render does not have (or go silent on one it
    # does) and 1995 green tests would not notice. So the two are pinned to each other.
    if bool(_thr_plan) != ("bed__throw" in _SOFT_BAKED):
        raise RuntimeError(
            "bed: styling.foot_throw says %s but the build baked %s — the story bits "
            "derive from that predicate, so they would describe the wrong bed"
            % ("a throw" if _thr_plan else "no throw",
               "one" if "bed__throw" in _SOFT_BAKED else "none"))
    # the hidden single-shell proxies have served every sheet in the stack — they
    # must never reach a render or an export
    drape.drop_sim_surfaces("bed__coverlet", "bed__duvet")
    return True


def _build_bench(x0, y0, W, D, H, rot=0.0):
    """A formed upholstered bench: a beveled cushion on four slim tapered legs, inside the spec
    footprint. Replaces the CC0 `Ottoman_01` fallback, which — stretched to a 0.5 x 1.0 m bench
    footprint — renders as a dark leather blob the pro critic called "a simple box shape on
    legs". A real seat-on-legs silhouette (with air under it) is what reads as furniture."""
    # ELEMENT 3 D3-4 (2026-07-18): the foot bench is UPHOLSTERED GREIGE LINEN that MATCHES the bed
    # base — the spec's bench note and material_story both bundle them ("bed base + foot bench"), so
    # the render must not show a pale cream satin bench under that stated truth (the element-2
    # revert-by-omission the story bits exist to kill; review 2026-07-18). Same values as bed_base.
    # 2026-07-23: the tone comes from value_ladder ("upholstery"), the SAME rung the bed
    # base and the tub chair wear — which is what D3-4 actually decided. Three copies of
    # one tuple in three functions is not "the same linen", it is three chances to drift.
    seat_m = _woven("bench_seat", _vl.rgba("bench_seat"), 0.94,
                    _matpre.cloth_args("linen"), sheen=0.25, spec=0.3,
                    maps="rough_linen")                                  # D3-4: same linen
    leg_m  = _solid("bench_leg",  _DARK_LEG, rough=0.45, sheen=0.1, spec=0.5)
    leg_h = H * 0.62                                    # tall legs + a SLIM cushion = a bench;
    seat_h = H - leg_h                                  # a fat pad on stubs is just a box again
    lt = min(0.05, W * 0.12, D * 0.12)                  # leg thickness
    inset = 0.035
    for i, (ox, oy) in enumerate(((inset, inset), (W - inset - lt, inset),
                                  (inset, D - inset - lt), (W - inset - lt, D - inset - lt))):
        _rbox(f"bench__leg{i}", x0 + ox, y0 + oy, 0.0, lt, lt, leg_h, leg_m, bevw=0.006)
    _rbox("bench__seat", x0, y0, leg_h, W, D, seat_h, seat_m, bevw=0.065, seg=5)  # rounder cushion (07-18)
    return True


def _smooth_mesh_obj(name, verts, faces, mat=None, own_mat=True, bevel=None, subsurf=0):
    """from_pydata + smooth shading (data API, headless-safe) — curved furniture pieces.

    `own_mat=False` (ELEMENT 8) is the opt-out a DD critic proved was required: this helper
    unconditionally tagged `ph_model`, and `_suite_materials` SKIPS every ph_model object
    (:1533-ish), so a mesh part named with a material TOKEN could never be painted by the
    router — it would silently keep whatever handle it was handed. Soft goods that carry a
    token must therefore opt out of both the tag and the inline material.

    NORMALS: from_pydata gives inconsistent winding, exactly as add_box documents at :101.
    add_box recalcs; this helper never did — so every loft shipped here would flare its
    bevel into "thin self-intersecting skirts that read as translucent under high-contrast
    lighting", which is add_box's own words for the bug. Recalc here too."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if own_mat:
        if mat is None:
            raise ValueError(f"_smooth_mesh_obj({name!r}): own_mat=True needs a material")
        o.data.materials.append(mat)
        o["ph_model"] = True                              # keep its own material + no bevel pass
    else:
        # painted later BY NAME through _suite_materials; keep it out of the global 5mm
        # round-over, which would eat a prop's silhouette.
        o["mill_bevel"] = MILL_BEVEL_M if bevel is None else bevel
    if subsurf:
        # LANE B (ground-truth study 2026-07-30): our soft forms were 20-566x under
        # the measured pro poly floor (pillow 156 vs 3,124+) and we used SUBSURF on
        # exactly 0 meshes vs their 33/726/56 — the pros smooth soft forms with
        # subdivision, we were smoothing with shading alone. Render-time only; the
        # pure layer's authored lattice (and every containment proof on it) is
        # untouched — the modifier rounds BETWEEN its verts, never past its hull.
        md = o.modifiers.new("softform_subsurf", 'SUBSURF')
        md.levels = 1
        md.render_levels = int(subsurf)
    return o


def _cyl_frustum(name, cx, cy, r_bot, r_top, z0, z1, mat, seg=24, cap=True):
    """A (tapered) cylinder via from_pydata — legs / round cushions."""
    from math import cos, sin, tau
    verts, faces = [], []
    for j, (r, z) in enumerate(((r_bot, z0), (r_top, z1))):
        for i in range(seg):
            a = tau * i / seg
            verts.append((cx + r * cos(a), cy + r * sin(a), z))
    for i in range(seg):
        k = (i + 1) % seg
        faces.append((i, k, seg + k, seg + i))
    if cap:
        verts.append((cx, cy, z1))                        # top fan centre
        top = len(verts) - 1
        for i in range(seg):
            faces.append((seg + i, seg + (i + 1) % seg, top))
    return _smooth_mesh_obj(name, verts, faces, mat)


def _arc_shell(name, cx, cy, r_out, r_in, z0, z1, th0, th1, mat, seg=48, z1_arm=None):
    """An annular ARC WALL (the tub-chair wrap): outer + inner skins, rim cap, end caps.

    `z1` is the top height at the arc MIDPOINT (the back). If `z1_arm` is given, the rim
    SWEEPS as z1_arm + (z1 - z1_arm)*sin(pi*t) along the arc (t in [0,1]) — low arms at the
    opening ends rising to the tall back (the tub-chair silhouette, owner 2026-07-22);
    None keeps the flat rim (byte-identical to the pinned pre-refinement mesh)."""
    from math import cos, sin, pi
    verts, faces = [], []
    n = seg + 1

    def top_z(i):
        if z1_arm is None:
            return z1
        return z1_arm + (z1 - z1_arm) * sin(pi * i / seg)

    for r in (r_out, r_in):                              # z0 row then the swept z1 row
        for zc in (z0, "top"):
            for i in range(n):
                a = th0 + (th1 - th0) * i / seg
                z = top_z(i) if zc == "top" else z0
                verts.append((cx + r * cos(a), cy + r * sin(a), z))
    O0, O1, I0, I1 = 0, n, 2 * n, 3 * n                  # outer z0/z1, inner z0/z1 rows
    for i in range(seg):
        faces.append((O0 + i, O0 + i + 1, O1 + i + 1, O1 + i))          # outer skin
        faces.append((I1 + i, I1 + i + 1, I0 + i + 1, I0 + i))          # inner skin
        faces.append((O1 + i, O1 + i + 1, I1 + i + 1, I1 + i))          # rim cap
        faces.append((I0 + i, I0 + i + 1, O0 + i + 1, O0 + i))          # bottom cap
    # end caps at the opening — WOUND OPPOSITELY (scrutiny 2026-07-21: the identical
    # tuple made the th1 cap inside-out; with use_smooth the inverted normal smears
    # the shared vertex normals into an asymmetric dark band at one rim end)
    for a, flip in ((0, False), (seg, True)):
        quad = (O0 + a, O1 + a, I1 + a, I0 + a)
        faces.append(quad[::-1] if flip else quad)
    return _smooth_mesh_obj(name, verts, faces, mat)


def _build_tub_chair(x0, y0, W, D, H, rot=0.0):
    """The BF11 vanity seat as a CURVED tub chair (spec kind='stool' style='tub_chair'):
    a continuous annular wrap at ONE rim height opening toward the spec front (any rot —
    THE ONE FACING CONVENTION, front azimuth = rot−90°), a round linen cushion inside,
    4 tapered round legs. Upholstery = the bed-base/bench greige linen EXACTLY (one
    textile family, D1-A); legs = the bench leg tone. Geometry DATA from the PURE
    millwork.tub_chair_curved (containment/opening/rim invariants unit-tested); meshes
    are real curves via from_pydata (the curtain-wave law — the first boxy pass read as
    a box because the primitive was wrong, owner 2026-07-20)."""
    lay = millwork.tub_chair_curved(W, D, H, rot_deg=rot)
    # 2026-07-23 — THE FIFTH COPY, found by the pre-commit review. This line read
    # `(0.40, 0.37, 0.33)` under a comment saying "still the ONE bed-base textile family
    # (D1-A), NOT A NEW TONE" — and it was a new tone, a fifth private copy of a colour the
    # docstring above, the spec's own tub-chair decision ("upholstery = greige stonewashed
    # LINEN matching the bed base + foot bench EXACTLY") and material_presets' story bit all
    # swear is shared. Worse, the pass that introduced value_ladder shipped a TEST asserting
    # the chair shares the rung — while the chair wore `stool_uph` and the test checked
    # `m_mill_linen`. False armour, written inside the change built to kill false armour.
    # The owner's 2026-07-22 LOOK ("the pale flat wrap read as ceramic") is honoured, not
    # reverted: it asked for DEEPER than the then-0.46 family, and the family is now 0.20.
    # The extra sheen he was given stays — sheen is a finish, not a tone.
    uph_m = _woven("stool_uph", _vl.rgba("stool_uph"), 0.92,
                   _matpre.cloth_args("linen"), sheen=0.45, spec=0.35)  # SAME textile family
    # ONE leg tone, from one place. This was `(0.24, 0.19, 0.14)` beside a docstring saying
    # "legs = the bench leg tone", while _build_bench used `(0.26, 0.21, 0.16)`. Same drift,
    # smaller stakes — and the same fix.
    leg_m = _solid("stool_leg", _DARK_LEG, rough=0.42, sheen=0.1, spec=0.5)
    cx, cy = x0 + lay["cx"], y0 + lay["cy"]
    sh = lay["shell"]
    # swept rim: low arms at the opening rising to the tall back = the tub-chair silhouette
    _arc_shell("stool__shell", cx, cy, sh["r_out"], sh["r_in"], sh["z0"], sh["z1_back"],
               sh["th0"], sh["th1"], uph_m, z1_arm=sh["z1_arm"])
    st = lay["seat"]
    # proud DOMED cushion (gentle top taper) so it reads as a pad nested in the wrap, not a
    # flush disc — sits below the arm rim, above the seat plane
    _cyl_frustum("stool__seat", cx, cy, st["r"], st["dome_r"] - 0.03, st["z0"], st["dome_z"],
                 uph_m, seg=40)
    for i, lg in enumerate(lay["legs"]):
        _cyl_frustum(f"stool__leg{i}", cx + lg["x"], cy + lg["y"], lg["r_bot"], lg["r_top"],
                     0.0, lg["h"], leg_m, seg=12, cap=False)
    return True


def _build_nightstand(x0, y0, W, D, H, rot=0.0, lamp=None, glow=None):
    """A solid low bedside cabinet + a brass dome lamp (ELEMENT 3 D3-3). Replaces the spindly
    `_table` primitive (a top on four thin legs) the side tables used to fall through to — which
    read as a flimsy console, not the ~500 mm-square bedside cabinet with a lamp the plan draws.
    A matte-DARK cabinet pops against the warm oak slat headboard wall and is NOT a fifth oak mass
    (D1-A); the brass base carries the room's 10% accent (PH-02: the lamp is dim vs the garden
    windows, so its warm metal never out-reads the daylight). Geometry from the PURE, unit-tested
    `millwork.nightstand_lamp_parts` (footprint invariant proven there). `rot` is accepted but not
    applied — the piece is symmetric about both axes (same honesty as _build_bench).

    ELEMENT 5 (D-E5-6): `glow` = {watts, z_off_m, rgb} makes the lamp EMIT — a warm
    emission graded down the shade (mouth-bright, top-dim) and a small POINT light
    inside pools DOWN through the open mouth onto the nightstand top (MA-04 needs glow
    AND a cast pool; PH-05 real falloff). Since round 3 (owner: "โคมไฟเป็นเหลี่ยม ดูไม่มี
    จริง") every lamp part is a turned surface of revolution inscribed in the pure
    layer's box envelope — glow or not; without glow the same round lamp simply stays
    dark (specs that have not decided lighting)."""
    body_m  = _solid("nightstand_body", (0.13, 0.12, 0.11, 1.0), rough=0.55, sheen=0.1, spec=0.4)
    brass_m = _solid("lamp_brass",      (0.60, 0.44, 0.20, 1.0), rough=0.32, metallic=1.0, spec=0.6,
                     aniso=0.65)   # BRUSHED, not cast: satin brass is drawn in one direction, so
                     #              its highlight is a STREAK. A round dot is the polished-ball
                     #              look and it is why the only metal in the frame reads as
                     #              plastic (vault audit 2026-07-22; the 10% accent layer is
                     #              supposed to be what catches the light).
    shade_m = _solid("lamp_shade",      (0.93, 0.86, 0.72, 1.0), rough=0.85, sheen=0.4, spec=0.3)
    if glow:
        _sb = _principled(shade_m)[1]
        if _sb:
            _set(_sb, "Emission Color", (*glow["rgb"], 1.0))
            _set(_sb, "Emission Strength", 1.0)
            # LOOK round-3 (owner: "โคมไฟเป็นเหลี่ยม ดูไม่มีจริง") — half of the unreal
            # read was a SINGLE flat emission value edge-to-edge (measured 221±1, no
            # bulb hotspot, no falloff; verdict #11). A shade lit from a bulb inside
            # its mouth is brightest at the mouth and dies toward the closed top, so
            # the strength is driven by shade-height: z → [0,1] → 1.5 at the mouth
            # down to ~0.4 at the top. One MapRange + one Math node, added ONCE (the
            # material is shared by both nightstands; their lamps sit at one height).
            nt = shade_m.node_tree
            if "lamp_grad" not in nt.nodes:
                # shade mouth/top from millwork's OWN published stack — the hand-copied
                # 0.035/0.17/0.15 here went stale the day the lamp rescaled (lane C)
                _z0 = H + millwork.LAMP_BASE_H + millwork.LAMP_STEM_H - 0.02
                _z1 = _z0 + millwork.LAMP_SHADE_H
                tc = nt.nodes.new("ShaderNodeTexCoord")
                sx = nt.nodes.new("ShaderNodeSeparateXYZ")
                mr = nt.nodes.new("ShaderNodeMapRange")
                mr.name = "lamp_grad"
                mr.inputs["From Min"].default_value = _z0
                mr.inputs["From Max"].default_value = _z1
                mm = nt.nodes.new("ShaderNodeMath")
                mm.operation = 'MULTIPLY_ADD'
                mm.inputs[1].default_value = -1.1        # t*-1.1 + 1.5: mouth 1.5 -> top 0.4
                mm.inputs[2].default_value = 1.5
                nt.links.new(tc.outputs["Object"], sx.inputs["Vector"])
                nt.links.new(sx.outputs["Z"], mr.inputs["Value"])
                nt.links.new(mr.outputs["Result"], mm.inputs[0])
                nt.links.new(mm.outputs["Value"], _sb.inputs["Emission Strength"])
    # LOOK round-3: the lamp was a stack of BOXES wearing a "dome/mushroom" docstring —
    # the literal ก้อนเหลี่ยม the owner named. The pure part list (envelopes + the
    # containment proof) is untouched; each lamp part is now materialised as a turned
    # surface of revolution INSCRIBED in its own box: a tapering brass base, a round
    # stem, and a drum shade whose mouth stays OPEN downward so the point light still
    # pools onto the cabinet (same reason the old glow-shell had no bottom face —
    # _cyl_frustum caps only the top).
    # toe wears a NEAR-BLACK: its whole job is to be the shadow line under the mass
    # (lane C, C2#7 — a cabinet with no plinth shadow reads as a box glued to the rug)
    toe_m = _solid("nightstand_toe", (0.045, 0.042, 0.040, 1.0), rough=0.7, spec=0.2)
    for name, ox, oy, oz, dx, dy, dz in millwork.nightstand_lamp_parts(W, D, H, lamp=bool(lamp)):
        if name == "toe":
            _rbox("nightstand__toe", x0 + ox, y0 + oy, oz, dx, dy, dz, toe_m, bevw=0.004)
            continue
        if name in ("body", "drawer"):
            _rbox(f"nightstand__{name}", x0 + ox, y0 + oy, oz, dx, dy, dz, body_m, bevw=0.008)
            continue
        ccx, ccy, r = x0 + ox + dx * 0.5, y0 + oy + dy * 0.5, dx * 0.5
        if name == "lamp_base":
            _cyl_frustum("nightstand__lamp_base", ccx, ccy, r, r * 0.72, oz, oz + dz,
                         brass_m, seg=24)
        elif name == "lamp_stem":
            _cyl_frustum("nightstand__lamp_stem", ccx, ccy, r, r * 0.90, oz, oz + dz,
                         brass_m, seg=16)
        else:
            _cyl_frustum("nightstand__lamp_shade", ccx, ccy, r, r * 0.80, oz, oz + dz,
                         shade_m, seg=32)
    if glow and lamp:
        ld = bpy.data.lights.new("lamp_glow", type='POINT')
        # lane-A story: practicals CARRY the hero frame (Kelly focal glow)
        ld.energy = glow["watts"] * _e5.story_scales(_LIGHT_STORY)["lamps"]
        ld.color = tuple(glow["rgb"])
        ld.shadow_soft_size = 0.025                      # a real bulb, not a point singularity
        lo = bpy.data.objects.new("lamp_glow", ld)
        lo.location = (x0 + W / 2.0, y0 + D / 2.0, H + glow["z_off_m"])
        bpy.context.scene.collection.objects.link(lo)
    return True


def _build_millwork(name, kind, x0, y0, z0, W, D, H, room_ctr, item_ctrs=(), face=None,
                    open_front=False, design=None):
    """Emit a DETAILED built-in (door leaves + reveals + toe-kick + pull-gap, or slat battens for
    a headboard wall, or an OPEN dressing wall: brass rail + floating drawers + open shelves)
    instead of the single `add_box` that made the pro critic write "the wardrobe is a
    texture-mapped box with basic hardware". Layout is millwork.py — pure, metres, and its
    CAD invariant (parts never leave the plan bbox) is unit-tested without Blender.

    `open_front` (builtin `open`) picks the open dressing wall; `design` (builtin `design`) sets
    the slat rhythm. Returns True if it built one; False -> the caller keeps the plain box.
    Parts are named `mill__*` so _suite_materials paints them (oak, with 'rail*' -> brass and
    '*front*'/'towerback' -> cool microcement for an open wall)."""
    axis, sign, src = millwork.mill_axis(x0, y0, W, D, room_ctr, item_ctrs, face)
    if axis is None:
        return False
    parts = millwork.millwork_parts(kind, W, D, H, axis, sign, floor_standing=(z0 <= 1e-6),
                                    open_front=bool(open_front), design=design)
    if not parts:
        return False                                 # panel / wall-hung low piece -> flush box
    for pn, px, py, pz, dx, dy, dz in parts:
        o = add_box(f"mill__{name}__{pn}", x0 + px, y0 + py, z0 + pz, dx, dy, dz)
        o["mill_bevel"] = MILL_BEVEL_M               # a near-sharp arris, not the suite's 5mm round
        # ELEMENT 8 ANCHOR REGISTRY: record what was ACTUALLY built, so the styling layer
        # derives from it instead of from a number in a file. A garment must hang off the
        # rail that exists; if the rail stops being built, styling RAISES rather than
        # shipping a bare bar under prose that says otherwise (the e7 wound).
        _STYLE_ANCHORS.append({"name": o.name, "piece": name, "part": pn, "kind": kind,
                               "x": x0 + px, "y": y0 + py, "z": z0 + pz,
                               "dx": dx, "dy": dy, "dz": dz})
    faces = {("x", 1): "E", ("x", -1): "W", ("y", 1): "N", ("y", -1): "S"}
    if src == "declared-cross-run":
        # The owner still WINS (we never override a signature) — but a wardrobe opened along its
        # long axis is worth saying out loud, not building silently.
        print(f"  REVIEW millwork '{name}': owner-declared face {faces[(axis, sign)]} opens this "
              f"{max(W, D) * 1000:.0f}mm run from its {min(W, D) * 1000:.0f}mm END. Confirm.")
    elif src != "declared":
        # TWO-LAYER LAW: facing is the owner's to declare. An inferred facing is a STANDING REVIEW,
        # never a silent pass — a wardrobe that opens into the wall mis-teaches the repaint.
        print(f"  REVIEW millwork facing INFERRED ({src}) for '{name}': front = "
              f"{faces[(axis, sign)]}. Declare `face` in the spec to make it owner-signed.")
    return True


def _stage_lounge(spec):
    """Restage the lounge into a photogenic U-grouping against the SOUTH feature wall for the
    HERO beauty shot: the sofa's back to the walnut wall FACING THE ROOM (so it's the hero with
    the wood behind it), two armchairs flanking the round table. The founder's insight was
    right — the original plan floats the sofa mid-room facing a wall, forcing the camera onto
    its back. This is the human 'staging' step; the dimensioned plan/overview keeps the real
    positions. Returns a new items list (non-lounge items untouched)."""
    lounge = {"sofa", "loveseat", "armchair", "chair", "lounge_chair",
              "coffee_table", "round_table", "side_table", "ottoman"}
    keep = [it for it in spec.get("items", []) if it.get("kind") not in lounge]
    gcx = 7700   # centre of the lounge zone (east half, clear of the bed at x3100-5300)
    staged = [
        {"name": "sofa", "kind": "sofa", "x": gcx - 1030, "y": 180, "w": 2060, "d": 950, "h": 800},
        {"name": "coffee table", "kind": "coffee_table", "x": gcx - 450, "y": 1650, "w": 900, "d": 900, "h": 350},
        {"name": "armchair L", "kind": "armchair", "x": gcx - 1780, "y": 1700, "w": 780, "d": 800, "h": 750},
        {"name": "armchair R", "kind": "armchair", "x": gcx + 900, "y": 1700, "w": 780, "d": 800, "h": 750},
    ]
    return keep + staged


def _model_path(slug):
    """Local cached .gltf/.glb for a slug, or None (no network inside Blender — assets.py
    and warehouse.py pre-download; here we only read the cache).

    TWO SHELVES, searched in order (P0e, 2026-08-10). The CC0 shelf is committed;
    the Trimble/3D-Warehouse shelf is a gitignored cache (`.gitignore:50`) under
    the licence rule in docs/LICENSING.md — the client gets the assembled SCENE,
    never the asset bundle. Adding it here is what makes R8's ACQUIRE half
    reachable from a build: `place_model` and `millwork.model_fit` already exist
    and were only ever pointed at one directory.

    WHY OPENING THIS DOOR IS SAFE DESPITE A SHELF WITH MIXED UNITS, and the
    measurement rather than the assumption: the catalog verdicts call 10 of the 16
    warehouse models "out-of-band", and dividing each by 25.4 lands ALL TEN inside
    a plausible furniture band — bd_a becomes 320 x 540 x 654 mm (a nightstand),
    bd_c 710 x 640 x 1005 (a chair). They are inch-authored, which is precisely the
    trap pipeline/CLAUDE.md calls a MUST ("SketchUp exports IMPERIAL even when the
    model was authored in metres"). It does not corrupt a render THROUGH THIS PATH
    because `place_model` rescales UNIFORMLY to the slot's own w/d/h and
    `model_fit` judges ASPECT, which is scale-invariant. What it does corrupt is
    the CATALOG, which is why that is filed rather than silently worked around:
    the shelf's usable count reads 1 of 16 when it should read 11.
    """
    import glob
    here = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
    shared = os.path.join(os.path.dirname(os.path.dirname(here)), "assets", "shared")
    hits = []
    for root in (os.path.join(shared, "cc0", "models", slug),
                 os.path.join(shared, "warehouse", slug)):
        hits += glob.glob(os.path.join(root, "*.gltf"))
        hits += glob.glob(os.path.join(root, "*.glb"))
    return hits[0] if hits else None


def _enable_gltf():
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    except Exception:
        pass


def _world_bbox(objs):
    import mathutils
    mn = [1e18, 1e18, 1e18]
    mx = [-1e18, -1e18, -1e18]
    for o in objs:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx


# upholstery material-name hints (glTF preserves names like '..._pillow', 'leather', 'fabric')
_UPHOLSTERY_KW = ("pillow", "cushion", "fabric", "upholst", "leather", "seat",
                  "sofa", "couch", "boucle", "textile")


def _retint_upholstery(mats, rgba=(0.84, 0.79, 0.71, 1.0), sheen=0.85, force_all=False,
                       rough=0.9, ignore_metal=False):
    """Recolour a model's UPHOLSTERY to cream boucle (DR: #F5F0E9, rough 0.8-0.9, Sheen 0.7-1.0)
    while leaving wood frames and metal legs alone. Because CC0 models drive Base Color from a
    DIFFUSE TEXTURE, we DISCONNECT that texture and set a flat cream, KEEPING the roughness +
    normal maps so the tufting/weave relief survives. Targets materials by name; force_all
    retints every non-metal material (for single-material models like sofa_02). rgba/sheen/
    rough are overridable so a spec-selected fabric preset (material_presets) can recolour
    per piece — defaults reproduce the legacy cream boucle exactly."""
    n = 0
    skipped_metal = []
    for m in mats:
        if not m or not getattr(m, "use_nodes", False):
            continue
        nt, b = _principled(m)
        if not b:
            continue
        met = b.inputs.get("Metallic")
        if met is not None and not met.is_linked and met.default_value > 0.5:
            # SOLID METAL — KEEP, unless the caller has asserted the whole mesh is
            # upholstery. THE TRAP THIS GUARD WALKED INTO (2026-08-10): glTF's
            # `metallicFactor` DEFAULTS TO 1.0 when the exporter omits it, and
            # SketchUp exports omit it. So an acquired fabric chair imports with
            # Metallic 1.0 on its upholstery, this guard reads "solid metal", and the
            # retint skips the one material it was called to change. The chair
            # rendered fluorescent green through a retint that ran and matched
            # nothing.
            if not ignore_metal:
                skipped_metal.append(m.name)
                continue
        name = m.name.lower()
        if not (force_all or any(k in name for k in _UPHOLSTERY_KW)):
            continue                                       # e.g. '..._legs' (wood) — keep
        bc = b.inputs.get("Base Color")
        if bc is None:
            continue
        if ignore_metal and met is not None and not met.is_linked:
            met.default_value = 0.0        # a textile is not a metal; binary metalness
        n += 1
        for l in list(bc.links):                           # drop the dark diffuse texture
            nt.links.remove(l)
        bc.default_value = rgba
        _set(b, "Sheen Weight", sheen)
        _set(b, "Sheen Roughness", 0.35)
        rg = b.inputs.get("Roughness")
        if rg is not None and not rg.is_linked:
            rg.default_value = rough
    return n, skipped_metal


# The signed textile an ACQUIRED upholstered piece wears. Keys are the value-ladder
# rungs the hand builders already use (`stool_uph` in _build_tub_chair, `bench_seat` in
# _build_bench), so an acquired chair and a built bench stay in ONE textile family —
# which is the spec's own words ("upholstery = greige stonewashed LINEN matching the bed
# base + foot bench EXACTLY"), and the drift this repo has already found five copies of.
_ACQUIRED_TEXTILE_RUNG = {"stool": "stool_uph", "bench": "bench_seat",
                          "chair": "stool_uph", "armchair": "stool_uph",
                          "lounge_chair": "stool_uph", "ottoman": "bench_seat",
                          "sofa": "bench_seat", "loveseat": "bench_seat"}


def _acquired_textile(kind):
    """The room's own woven material for an acquired upholstered mesh."""
    rung = _ACQUIRED_TEXTILE_RUNG.get(kind, "stool_uph")
    return _woven(f"acq_{rung}", _vl.rgba(rung), 0.92,
                  _matpre.cloth_args("linen"), sheen=0.45, spec=0.35)


def _retint_kwargs(mat_sel, nm, kind, has_mesh):
    """How an ACQUIRED mesh joins this room's decided palette — one definition.

    THE DEFECT THAT PRODUCED IT (2026-08-10, P2f's first LOOK): the acquire-first
    branch passed `retint_fabric` and nothing else, so the first mesh ever placed on
    this lane rendered BRIGHT GREEN — the colour a stranger uploaded it in. The
    MODEL_MAP path had resolved the element preset for weeks; the new path did not,
    because the resolution was written inline at one call site instead of once.

    Returns (kwargs, retint_fabric). A texture-set preset cannot be applied to a mesh
    that keeps its own PBR, and that is REPORTED rather than silently dropped."""
    retint = kind in _UPHOLSTERED
    ep = _matpre.element_preset(mat_sel, nm, kind)
    kw = {}
    if ep:
        ea = _matpre.factory_args(ep)
        if "rgba" in ea:
            kw = {"retint_rgba": ea["rgba"], "retint_sheen": ea.get("sheen", 0.0),
                  "retint_rough": ea["rough"],
                  # non-upholstery kinds carry no fabric name keywords — recolour all
                  "retint_force": True if not retint else None}
        elif has_mesh:
            print(f"  (element preset '{ep}' on '{nm}': texture-set preset — the "
                  f"imported model keeps its own PBR; noted, not applied)")
    return kw, bool(retint or kw)


# A NAME FROM A STRANGER IS NOT EVIDENCE ABOUT A COLOUR, and this is the measurement
# that says so. tub_chair_c carries EIGHT materials and its upholstery is called
# `Carpet_Plush_Charcoal` while its baseColorFactor is [0.471, 0.667, 0.204] —
# fluorescent green. `_retint_upholstery` targets by NAME (_UPHOLSTERY_KW), and
# "carpet"/"plush"/"charcoal" are in none of our keywords, so the first mesh this lane
# ever acquired rendered green through a retint that ran and matched nothing.
#
# Widening the keyword list is the wrong fix twice over: it would have to grow for
# every uploader's vocabulary (the rule-that-names-its-objects defect, R9b), and it
# would still be trusting a field that has just been shown to lie.
#
# So for a DECLARED acquisition of an upholstered class the retint is FORCED: the
# signed palette outranks whatever colour a stranger uploaded, and that is not a
# preference — it is the same source-of-truth order the repo already runs on.
#
# WHAT IT COSTS, stated because it is visible the moment a leg shows: forcing paints
# every non-metal material, legs included, and this chair's spec wants its legs in the
# bench-leg tone rather than in linen. Splitting one mesh's materials by ROLE is
# beyond this API, it is the question the 2026-08-10 DR was fired on, and until that
# answer lands the split is a declared gap rather than a guess.
_ACQUIRE_FORCE_RETINT_NOTE = ("forced: the model's material names cannot be trusted "
                              "(tub_chair_c's upholstery is called Charcoal and is "
                              "green); legs share the textile tint until the "
                              "role-split lands")


def _slot_pair(slug, kind):
    """(model slot, slot for this kind) — the two classes model_fit compares.

    The mesh's class comes from `assets/shared/CATALOG.json`, which recorded it for
    all 29 models at P0b and which nothing has read since; the item's comes from the
    same word vocabulary applied to the spec `kind`. Either may be None, and None is
    reported by model_fit rather than treated as a match."""
    try:
        import asset_catalog as _AC
    except Exception:                                   # noqa: BLE001
        return None, None
    return (_AC.catalog_slot(slug) if slug else None,
            _AC.kind_slot(kind) if kind else None)


def _normalise_acquired(meshes, weld_mm=0.01, sharp_deg=30.0):
    """The shading half of a studio's incoming-mesh checklist, applied to an acquired
    model: WELD split vertices at a tight threshold, then shade SMOOTH while keeping
    genuine hard edges sharp.

    GROUNDED, not invented (DR 2026-08-10, notebook 1277ca41, turn 1, §"Shading
    Normals and Smoothing"): *"Weld split vertex boundaries along smooth regions using
    a tight threshold (0.001 mm to 0.01 mm), keeping sharp edges unwelded to preserve
    clean corners"* and *"run normal unification"*. Staged at
    knowledge/_inbox/dr-acquired-mesh-integration-2026-08-10.md.

    WHY IT IS NEEDED HERE AND NOT A NICETY. A SketchUp-origin mesh arrives with every
    face split and every polygon flat, so a curved shell renders as visible facets —
    the acquired tub chair's rim showed them at 2x. That is D9's row ("curved forms
    rendering flat-shaded") arriving through the acquire path, so the row this lane is
    trying to clear would have been fed by the fix for the row above it.

    DATA API ONLY — bmesh, never a geometry `bpy.ops` (pipeline/CLAUDE.md layer law).
    Returns (welded, sharp_edges, smoothed_polys) so the build says what it changed."""
    import bmesh
    welded = sharp = smoothed = 0
    for ob in meshes:
        me = ob.data
        if not me or not me.polygons:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        before = len(bm.verts)
        try:
            bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=weld_mm / 1000.0)
        except Exception:                                   # noqa: BLE001
            pass
        welded += before - len(bm.verts)
        ct = math.cos(math.radians(sharp_deg))
        for e in bm.edges:
            if len(e.link_faces) == 2:
                a, b = (f.normal for f in e.link_faces)
                e.smooth = (a.dot(b) >= ct)                 # below the angle -> smooth
                sharp += not e.smooth
            else:
                e.smooth = False                            # a boundary is an edge
        for f in bm.faces:
            f.smooth = True
            smoothed += 1
        bm.to_mesh(me)
        bm.free()
        me.update()
    return welded, sharp, smoothed


def place_model(path, x, y, w, d, h, rot=0.0, z0=0.0, retint_fabric=False,
                retint_rgba=None, retint_sheen=None, retint_rough=None,
                retint_force=None, model_slot=None, item_slot=None,
                retint_ignore_metal=False, replace_material=None):
    """Import a gltf, UNIFORMLY scale it to fit the item footprint (undistorted), set it
    footprint-centred at (x,y) with its base at height z0 (0 = on the floor; >0 = on a
    table for decor), then rotate it `rot` degrees about world Z (so a chair can face the
    conversation group — fixes the 'all chairs face the wrong way' bug). Keeps the model's
    own PBR materials (retint_fabric recolours dark upholstery to cream boucle; the
    retint_* overrides let a spec-selected element preset recolour THIS piece — None
    means the legacy behaviour, exactly). Coords metres.

    Returns True on success; False if the import failed OR the mesh does not FIT the slot
    (see model_fit) — in which case the caller falls back to a procedural primitive, which is
    the right answer: a squashed real mesh looks worse than an honest box."""
    import math
    from mathutils import Matrix, Vector
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=path)
    except Exception as e:
        print(f"  (gltf import failed {os.path.basename(path)}: {e})")
        return False
    news = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in news if o.type == 'MESH']
    if not meshes:
        for o in news:
            bpy.data.objects.remove(o, do_unlink=True)
        return False
    roots = [o for o in news if o.parent is None] or news
    mn, mx = _world_bbox(meshes)
    mw, md = mx[0] - mn[0], mx[1] - mn[1]
    s, ok, why = millwork.model_fit(mw, md, mx[2] - mn[2], w, d, h,
                                    model_slot=model_slot, item_slot=item_slot)
    if ok:
        # The scale is PRINTED on every acquisition, not only on a reject. A uniform
        # rescale of an ingest-asserted mesh is a second scaling that nothing asserts
        # (pipeline/CLAUDE.md: "scale is ASSERTED on every ingest, never assumed"),
        # and the band it should sit in is a declared gap — see model_fit's docstring.
        print(f"  MODEL-FIT {os.path.basename(path)}: {why}")
    if not ok:
        # LOUD, not silent: this is the failure mode that produced a judged 2/5 and was read as a
        # mesh-quality problem for a week. It is a SOURCING signal — the slot wants a different mesh.
        print(f"  MODEL-FIT REJECT {os.path.basename(path)}: {why} -> procedural fallback")
        # Free the DATA too, not just the objects. Removing an object orphans its mesh, materials
        # and — for a Poly Haven asset — its whole 1k/2k PBR image set, which then rides along in
        # the saved .blend forever. A gate that rejects models must not fatten the file each time.
        meshes_d = {o.data for o in news if o.type == 'MESH' and o.data}
        mats = {sl.material for o in news for sl in getattr(o, "material_slots", []) if sl.material}
        imgs = {n.image for m in mats if m.use_nodes for n in m.node_tree.nodes
                if n.type == 'TEX_IMAGE' and n.image}
        for o in news:
            bpy.data.objects.remove(o, do_unlink=True)
        for coll, items in ((bpy.data.meshes, meshes_d), (bpy.data.materials, mats),
                            (bpy.data.images, imgs)):
            for it in items:
                if it.users == 0:
                    coll.remove(it)
        return False
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
    bpy.context.view_layer.update()
    mn, mx = _world_bbox(meshes)                 # bbox after scaling
    cx = x + w / 2.0
    cy = y + d / 2.0
    dx = cx - (mn[0] + mx[0]) / 2.0
    dy = cy - (mn[1] + mx[1]) / 2.0
    dz = z0 - mn[2]
    for o in roots:
        o.location = (o.location.x + dx, o.location.y + dy, o.location.z + dz)
    if rot:
        # rotate about world Z around the footprint centre (models import with a +90deg X
        # root, so a pivot-matrix rotation is correct where poking rotation_euler.z is not).
        piv = Vector((cx, cy, 0.0))
        T = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(rot), 4, 'Z') @ Matrix.Translation(-piv)
        bpy.context.view_layer.update()
        for o in roots:
            o.matrix_world = T @ o.matrix_world
    bpy.context.view_layer.update()
    for o in news:
        o["ph_model"] = True                     # keep its own materials / skip bevel
    _wl, _sh, _sm = _normalise_acquired(meshes)
    print(f"  mesh normalise: welded {_wl} split vert(s), {_sh} edge(s) kept sharp, "
          f"{_sm} polygon(s) shaded smooth")
    if replace_material is not None:
        # THE INCOMING SURFACE DOES NOT EXIST, SO IT IS REPLACED RATHER THAN TINTED.
        # Decided by measurement, not preference — see asset_scale.carries_a_pbr_surface:
        # a Poly Haven asset arrives with normal + metallic-roughness maps and is a
        # finished surface; a 3D Warehouse asset arrives with flat base colours and no
        # relief at all. Tinting the second one produces a moulded-plastic look, which
        # is what the first acquired chair on this lane rendered as.
        n_slots = 0
        for o in meshes:
            o.data.materials.clear()
            o.data.materials.append(replace_material)
            n_slots += 1
        print(f"  material REPLACED on {n_slots} mesh(es) with "
              f"'{replace_material.name}': the mesh carried no normal or "
              f"metallic-roughness map, so it brought a colour and not a surface")
    elif retint_fabric:
        mats = {slot.material for o in meshes for slot in o.material_slots if slot.material}
        kw = {k: v for k, v in (("rgba", retint_rgba), ("sheen", retint_sheen),
                                ("rough", retint_rough)) if v is not None}
        force = retint_force if retint_force is not None else (len(mats) == 1)
        n_re, skipped = _retint_upholstery(mats, force_all=force,
                                           ignore_metal=bool(retint_ignore_metal), **kw)
        # A MECHANISM THAT RAN AND CHANGED NOTHING MUST SAY SO. This is the whole
        # lesson of the green chair: the retint fired, matched zero materials, and was
        # silent about it, so the render was the first thing that could tell anyone.
        print(f"  retint: {n_re} of {len(mats)} material(s) taken to the signed palette"
              + (f"; {len(skipped)} kept as metal ({', '.join(sorted(skipped)[:3])})"
                 if skipped else ""))
        if n_re == 0:
            print("  !! retint MATCHED NOTHING — the mesh keeps the colour it was "
                  "uploaded in. Name-matching cannot see this model's upholstery.")
    return True


def _hero_camera(gx0, gy0, gx1, gy1, h, rx0, ry0, rx1, ry1):
    """A low, seated-eye-level 'magazine' 3/4 on the lounge seating group (KB §8.3): ~1.45m
    eye height, 35mm, standing NORTH of the group (but CLAMPED inside the room walls) looking
    back SOUTH so the south/east walls are a clean backdrop, with real depth of field on the
    group. Lighting is the HDRI + interior downlights (no competing key sun). Coords metres."""
    from mathutils import Vector
    gw = gx1 - gx0; gd = gy1 - gy0
    cx = (gx0 + gx1) / 2.0; cy = (gy0 + gy1) / 2.0
    clamp = lambda v, lo, hi: max(lo, min(hi, v))
    cam_data = bpy.data.cameras.new("Camera"); cam_data.lens = 30   # wide enough to hold the group
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    # stand back from the group but STAY INSIDE the four walls (0.6m margin). This was the
    # bug: an un-clamped offset put the lens outside the north wall -> a blank wall filled frame.
    ex = clamp(cx, rx0 + 0.6, rx1 - 0.6)
    ey = clamp(gy1 + 2.6, cy + 1.4, ry1 - 0.55)
    eye = Vector((ex, ey, 1.55))                                 # eye-level (DR ~1.1-1.5m), less floor
    tgt = Vector((cx, cy - 0.05 * gd, 0.70))                     # group centre, seat height
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    try:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = (tgt - eye).length
        cam_data.dof.aperture_fstop = 9.0                        # gentle DoF, sofa stays crisp
    except Exception:
        pass
    bpy.context.scene.camera = cam


def build_suite(spec, label="suite"):
    """Materialize a room-spec@0.2 (metric L-polygon + ensuite sub-room + built-ins)."""
    import math
    clear_scene()
    del _STYLE_ANCHORS[:]                  # ELEMENT 8: per-build, never across rooms
    del _SOFT_BAKED[:]                     # ...and so must the baked-cloth record
    _enable_gltf()
    bpy.context.scene.unit_settings.system = "METRIC"
    # ZONE render-apply (owner-signed only): drop any piece the owner signed below_grade — the trees are
    # ground BELOW, not floor-2 objects. ONE filter reassigning spec['items'], run FIRST — before the _hero
    # restage AND before every consumer (the item loop, the _ct/_focal lookup, the seats bbox/rug,
    # _dress_scene, the eye/hero camera and lighting all read spec['items'] independently); filtering inside
    # the loop alone would leave a mis-aimed camera, an oversized rug and floating vases. scene_zone_decision
    # gates on zone_source=='owner-signed', so with no zone signature every item returns 'place' and this is a
    # no-op (byte-identical render). CAVEAT: the _hero beauty shot's _stage_lounge substitutes IDEALISED
    # lounge furniture (zone-blind by design — it already discards real positions), so a below_grade LOUNGE
    # piece is removed here yet the hero shot may still stage a generic seat in that spot. The faithful --eye
    # and whole-floor (build_floor) renders — the plan-faithful deliverables — honor the drop exactly.
    _kept, _dropped = [], []
    for it in spec.get("items", []):
        (_dropped if placement_gate.scene_zone_decision(it)["action"] == "skip" else _kept).append(it)
    if _dropped:
        print(f"  zone: excluded {len(_dropped)} owner-signed below_grade piece(s) "
              f"(ground-below, NOT floor-2 objects): {[it.get('name') for it in _dropped]}")
        spec = {**spec, "items": _kept}
    if spec.get("_hero"):                          # restage the lounge for the beauty shot
        spec = {**spec, "items": _stage_lounge(spec)}
    r = spec["room"]
    outline_m = [(float(x) * MM, float(y) * MM) for x, y in r["outline_mm"]]
    h = float(r.get("ceiling_mm", 2800)) * MM
    thk = float(r.get("wall_thk_mm", 100)) * MM
    fth = 0.1

    add_poly_floor("floor", outline_m, fth)
    # the hero is an enclosed beauty shot -> solid walls (a doorway gap leaks the HDRI in as a
    # bright slit) + a ceiling below; the overview keeps the real door opening AND the plan's
    # real openings (glazed, so they are windows, not raw holes -- no HDRI slit).
    poly_walls_bpy("", outline_m, thk, h,
                   None if spec.get("_hero") else spec.get("door"),
                   None if spec.get("_hero") else r.get("openings"))

    n_fix = 0
    for si, sr in enumerate(spec.get("subrooms", [])):
        so = [(float(x) * MM, float(y) * MM) for x, y in sr["outline_mm"]]
        sh = float(sr.get("ceiling_mm", 2000)) * MM
        poly_walls_bpy(f"s{si}_", so, thk, sh, sr.get("door"), sr.get("openings"))
        # ELEMENT 7 (THE DRESSING GALLERY, 2026-07-22): a type='wardrobe' subroom routes
        # BY TYPE to the pure wardrobe_bay lane — per-mass OPEN oak-and-brass dressing
        # (rails/drawers/shelves/mirror niche) or a closed cool-microcement anchor,
        # RAISING on anything it does not own — so no bay fixture can ever reach the
        # bathroom dispatch below and fall through its silent [] to the fix__ white slab
        # (D-E7-3 merge ruling; the source-text pin in test_wardrobe_bay.py walks this).
        if sr.get("type") == "wardrobe":
            _wparts = wardrobe_bay.bay_parts(sr)
            for _p in _wparts:
                _bo = add_box(_matpre.fixture_part_name(_p["mat"], _p["name"]),
                              _p["x"] * MM, _p["y"] * MM, _p["z"] * MM,
                              _p["dx"] * MM, _p["dy"] * MM, _p["dz"] * MM)
                # ELEMENT 8: the bay's rails and shelves are anchors too — this is the
                # dressing room the owner rejected twice for looking undesigned, and it is
                # the mass with the most empty joinery in the suite.
                # piece/part come from wardrobe_bay itself: a bay object's NAME is
                # routed by material (…__brass), so its function is not readable from
                # the name and a name-only match finds none of the bay's six rails.
                _STYLE_ANCHORS.append({
                    "name": _bo.name, "piece": _p.get("piece"), "part": _p.get("part"),
                    "kind": "wardrobe",
                    "x": _p["x"] * MM, "y": _p["y"] * MM,
                    "z": _p["z"] * MM, "dx": _p["dx"] * MM, "dy": _p["dy"] * MM,
                    "dz": _p["dz"] * MM})
            _wopen = sum(1 for f in sr.get("fixtures") or () if f.get("open"))
            print(f"  wardrobe bay: {len(sr.get('fixtures') or ())} mass(es) "
                  f"({_wopen} open dressing / {len(sr.get('fixtures') or ()) - _wopen} "
                  f"closed) -> {len(_wparts)} joinery part(s) (element 7 dressing gallery)")
            # NOT counted into n_fix: that tally prints as "ensuite fixture(s) ...
            # (oak vanity / ... / brass)" — the ENSUITE label; the bay owns its own
            # distinct print line above (review catch E7-CODE-4 / WB-2).
            continue
        for fx in sr.get("fixtures", []):
            # ELEMENT 4: ensuite fixtures get real per-part massing (bathroom.py, PURE) whose
            # material ROLE routes to the SAME suite materials by NAME (oak vanity, caesarstone
            # counter, porcelain sanitaryware, brass fittings, clear glass). Unmapped kinds fall
            # back to the plain sanitary box — same escape _build_millwork uses. The mat->name
            # router is a CLOSED vocabulary in the pure layer (material_presets.fixture_part_name)
            # and RAISES on a mat it doesn't know — the silent oak default it replaced is how the
            # e5 task bar rendered oak (LOOK 2026-07-20).
            # ELEMENT 6: `subroom` reaches only the bath_accessories branch — its
            # positions derive from the sibling fixtures + door, and the pure layer
            # RAISES rather than returning [] so the white-box fallback below can
            # never swallow a decided accessory set (DD build-consequence 8).
            _parts = bathroom.fixture_parts(fx, taskbar=_e5.applies(spec), subroom=sr)
            if _parts:
                for _p in _parts:
                    add_box(_matpre.fixture_part_name(_p["mat"], _p["name"]),
                            _p["x"] * MM, _p["y"] * MM, _p["z"] * MM,
                            _p["dx"] * MM, _p["dy"] * MM, _p["dz"] * MM)
                n_fix += 1
            else:
                add_box("fix__" + str(fx.get("name", "fixture")).replace(" ", "_"),
                        float(fx["x"]) * MM, float(fx["y"]) * MM, 0,
                        float(fx["w"]) * MM, float(fx["d"]) * MM, max(float(fx.get("h", 400)) * MM, 0.02))
    if n_fix:
        print(f"  fixtures: {n_fix} ensuite fixture(s) materialized with per-part roles "
              f"(oak vanity / caesarstone / porcelain / brass / clear glass)")
    # COPLANAR-BACKER SKINS (element-5 LOOK catch 2026-07-20): where a full-height
    # builtin's face lies EXACTLY on a subroom edge (BF10's north face on the ensuite's
    # y5850), Cycles' coplanar tie renders the builtin's material as the subroom's wall
    # — the ensuite plaster wore BF10's wavy oak until the task-bar wash lit it. The
    # PREDICATE is pure (element5_lighting.coplanar_backer_skins, LAYER LAW — scrutiny
    # 2026-07-21 moved it out of this layer); this loop only materializes + discloses.
    for _sk in _e5.coplanar_backer_skins(spec):
        _nm = f"wall_skin_{_sk['edge'].replace('=', '')}_{str(_sk['backer']).replace(' ', '-').replace('__', '-')}"
        add_box(_nm, _sk["x"] * MM, _sk["y"] * MM, _sk["z"] * MM,
                _sk["dx"] * MM, _sk["dy"] * MM, _sk["dz"] * MM)
        print(f"  wall skin: subroom edge {_sk['edge']} backed coplanar by '{_sk['backer']}' "
              f"(h>=ceiling) -> 4mm plaster skin ({max(_sk['dx'], _sk['dy']) * MM:.2f}m run) "
              f"hides the tie-win")

    # A built-in faces the side of the room it SERVES — read that off the furniture, not off the
    # outline's centroid (in an L-shaped SUITE the centroid lands in the wrong zone: see
    # millwork.mill_axis). Item centres in metres; the centroid is only the no-items fallback.
    _rc = (sum(p[0] for p in outline_m) / len(outline_m),
           sum(p[1] for p in outline_m) / len(outline_m))
    _ic = [((float(it["x"]) + float(it["w"]) / 2.0) * MM,
            (float(it["y"]) + float(it["d"]) / 2.0) * MM) for it in spec.get("items", [])]
    n_mill = 0
    for b in spec.get("builtins", []):
        bh = float(b["h"]) * MM if b.get("h") else h
        # mount_mm = height above the floor the element's BASE sits (AFF). Default 0 =
        # floor-standing (wardrobes/cabinets/full-height millwork). A WALL-MOUNTED element
        # (TV panel, floating shelf) sets it so the control mass FLOATS on the wall instead
        # of a floor block — the designer's "ทำไมเอา TV ไปติดไว้ที่พื้น?" fix (built-ins used to
        # always extrude from z=0, so a wall TV rendered as a slab on the floor).
        bz = float(b.get("mount_mm", 0) or 0) * MM
        nm = str(b.get("name", "builtin")).replace(" ", "_")
        bx, by = float(b["x"]) * MM, float(b["y"]) * MM
        bw, bd = float(b["w"]) * MM, float(b["d"]) * MM
        # PROCEDURAL MILLWORK (2026-07-12): door leaves + reveals + toe-kick + pull-gap (or slat
        # battens for a headboard wall). Falls back to the plain box for shapes that are not runs.
        if _build_millwork(nm, str(b.get("kind", "")), bx, by, bz, bw, bd, bh, _rc, _ic,
                           b.get("face"), open_front=b.get("open"), design=b.get("design")):
            n_mill += 1
            continue
        add_box("mill__" + nm, bx, by, bz, bw, bd, bh)
    if n_mill:
        print(f"  millwork: {n_mill} built-in(s) generated with real joinery "
              f"(leaves/reveals/toe-kick/pull-gap or slats)")

    # CURTAINS — skipped only for --hero (it restages the lounge behind SOLID walls: no
    # glazing exists there to dress, and fabric floating on a blank wall would be a lie).
    if not spec.get("_hero"):
        _add_curtains(spec, h)
        _add_casement_sheers(spec)  # ELEMENT 6: AFTER _add_curtains (it owns curtain_sheer)
        _add_juliet_rail(spec)   # outside the glass — same solid-wall reason for the skip
        _add_vanity_mirror(spec)  # ELEMENT 2: frameless mirror on the wall between the west windows

    # loose furniture: a REAL CC0 model (Poly Haven) when the kind is mapped + cached,
    # else furniture.py primitives (which work in INCHES). Models are fit to the footprint.
    MM_IN = 1.0 / 25.4
    n_model = 0
    # spec-selected per-element material presets (owner's hand on THIS piece): resolved
    # once for the retint/primitive paths below; _suite_materials(spec) re-resolves for
    # the surface/family roles. An invalid block raises here, before any geometry lies.
    _mat_sel = _matpre.resolve_materials(spec)
    if _mat_sel and _mat_sel.get("elements"):
        # anti-silent-drop gate (review 2026-07-14): every element key must provably bind
        # and be appliable BEFORE building — material_story() reports each selection as
        # the render's truth, so a selection that cannot land aborts instead of lying.
        if spec.get("_hero"):
            raise ValueError("materials.elements is not supported with --hero: the hero "
                             "shot restages/renames the lounge furniture (_stage_lounge) "
                             "so element keys cannot bind — drop --hero or the elements")
        _bound = _matpre.reconcile_elements(_mat_sel, spec)
        print(f"  materials: element presets bound -> "
              f"{ {k: v for k, v in sorted(_bound.items())} }")
    # conversation focal point = the lounge centre table; lounge seating auto-faces it.
    _ct = next((it for it in spec.get("items", [])
                if it.get("kind") in ("coffee_table", "round_table")
                and float(it["x"]) > 4000 and float(it["y"]) < 3000), None)
    _focal = ((float(_ct["x"]) + float(_ct["w"]) / 2.0, float(_ct["y"]) + float(_ct["d"]) / 2.0)
              if _ct else None)
    n_reached = n_intercepted = n_acquired = n_acq_fallback = 0
    for it in spec.get("items", []):
        kind = it.get("kind", "block")
        nm = it.get("name") or kind
        xm, ym = float(it["x"]) * MM, float(it["y"]) * MM
        wm, dm = float(it["w"]) * MM, float(it["d"]) * MM
        hm = max(float(it.get("h", 400)) * MM, 0.05)
        rot = float(it.get("rot", 0.0))
        # ---------------------------------------------------------- R8 ACQUIRE FIRST
        # P2f. An item that DECLARES `model` is an acquisition decision, and it is
        # tried BEFORE any bespoke builder — which is the whole change, because the
        # order was the blocker rather than the capability. Measured before this
        # existed: 0 of 6 items in the canonical suite reached `place_model`, since
        # every kind in it is intercepted by a builder that `continue`s first. Both
        # shelves, `model_fit`, the class gate and `place_model` all worked and were
        # never asked.
        #
        # THE DECISION LIVES IN THE SPEC, NOT IN A MAP IN THIS FILE, and that is
        # deliberate: R8 makes acquisition a recorded choice per object, MODEL_MAP is
        # a global default by kind that has already gone dead twice without anyone
        # noticing (bench 2026-07-11, side_table since), and a slug hard-coded here
        # would be a third. No spec on disk carries `model` today, so nothing changes
        # for anything already shipped.
        #
        # THE FALLBACK IS LOUD. R8 says a failed acquisition becomes a DECLARED GAP,
        # not a modelling task — but removing the object mid-lane trades a wrong
        # object for a hole, so the builder still runs and the fall-back is COUNTED
        # and printed. D8 then catches whatever it produced: an R8-ACQUIRE class
        # rendered as a primitive is exactly the row's definition.
        _mdl = None if spec.get("_no_acquire") else it.get("model")
        if _mdl:
            _mp = _model_path(str(_mdl))
            if not _mp:
                print(f"  ACQUIRE MISS '{nm}': spec declares model {_mdl!r} and no "
                      f"cached .gltf/.glb exists on either shelf -> builder")
                n_acq_fallback += 1
            else:
                _ms, _is = _slot_pair(str(_mdl), kind)
                _akw, _arf = _retint_kwargs(_mat_sel, nm, kind, True)
                _has_surface = _ascale.carries_a_pbr_surface(_mp)
                if kind in _UPHOLSTERED and _has_surface is False:
                    # No relief, no gloss variation: our own signed textile is strictly
                    # better than anything that can be done to a flat colour.
                    _akw = {}
                    _arf = False
                    _akw["replace_material"] = _acquired_textile(kind)
                elif kind in _UPHOLSTERED:
                    _akw["retint_force"] = True          # see _ACQUIRE_FORCE_RETINT_NOTE
                    _akw["retint_ignore_metal"] = True   # glTF metallicFactor defaults to 1.0
                    print(f"  retint {_ACQUIRE_FORCE_RETINT_NOTE}")
                    if _has_surface is None:
                        print("  !! could not read the asset's map roles — retinting "
                              "rather than replacing, which is the reversible half")
                if place_model(_mp, xm, ym, wm, dm, hm,
                               rot=model_rot(rot, str(_mdl)),
                               retint_fabric=_arf,
                               model_slot=_ms, item_slot=_is, **_akw):
                    n_model += 1
                    n_acquired += 1
                    print(f"  ACQUIRED '{nm}' <- {_mdl}")
                    continue
                n_acq_fallback += 1
                print(f"  ACQUIRE FELL BACK for '{nm}' ({kind}): the declared mesh "
                      f"did not pass the gate; a hand-built free-form object is what "
                      f"R8 forbids and D8 counts")
        if kind == "rug":
            _add_rug("rug__" + str(nm).replace(" ", "_"), xm, ym, wm, dm)
            continue
        # HERO: build a MODERN sofa from primitives (every CC0 sofa is vintage Victorian, which
        # clashes with the modern room). Back to the south wall, facing +Y (the room).
        if kind == "sofa" and spec.get("_hero"):
            _build_modern_sofa(xm, ym, wm, dm)
            n_model += 1
            continue
        # Procedural massing (2026-07-11), intercepted BEFORE MODEL_MAP / furniture.parts.
        # _build_bed IS rot-aware (via _head_dir, so the pillows land at the head).
        # _build_bench IS NOT: it accepts `rot` and never reads it (its body is a symmetric
        # seat-on-four-legs, so today that is invisible — but the parameter is a promise the
        # function does not keep, and the moment the bench gains a back or an asymmetric arm it
        # becomes the same wrong-way bug _build_bed exists to fix). Named, not silently "fixed":
        # rotating it now would change a shipped render for no verified gain.
        if kind == "bed":
            _build_bed(xm, ym, wm, dm, hm, rot)
            continue
        if kind == "bench":
            n_intercepted += kind in MODEL_MAP
            _build_bench(xm, ym, wm, dm, hm, rot)   # rot accepted, NOT applied — see above
            continue
        # ELEMENT 3: a side_table carrying a `lamp` block IS a bedside nightstand — a solid cabinet
        # + a brass dome lamp, not the spindly `_table` primitive. Opt-in on the flag so the sitting
        # room's plain side tables keep the model/primitive path.
        # The vanity seat: a stool that DECLARES style='tub_chair' gets the real curved
        # chair (spec DATA opt-in — a bar stool in another spec keeps its primitive).
        # An UNKNOWN non-empty style RAISES (scrutiny 2026-07-21: a typo'd style would
        # silently revert the owner-decided chair to the primitive box AND drop its
        # anti-repaint story bit — the 831fc1b swallow class); style-absent stays legal.
        if kind == "stool":
            _style = it.get("style")
            if _style == "tub_chair":
                _build_tub_chair(xm, ym, wm, dm, hm, rot)
                continue
            if _style:
                raise ValueError(f"stool style {_style!r} unknown (known: 'tub_chair'); "
                                 f"a typo must fail loud, not render the primitive box")
        if kind == "side_table" and it.get("lamp"):
            # ELEMENT 5 (D-E5-6): a spec that decided lighting makes the lamp EMIT —
            # glow config derives from the validated block + this item's own cct_k
            # (out-of-family CCT RAISES: PH-03 by construction). No block -> dark, E3-identical.
            _g5 = _e5.lamp_glow(spec)
            _glow = (dict(_g5, rgb=_e5.lamp_rgb((it.get("lamp") or {}).get("cct_k", 2850)))
                     if _g5 else None)
            n_intercepted += kind in MODEL_MAP
            _build_nightstand(xm, ym, wm, dm, hm, rot, it.get("lamp"), glow=_glow)
            continue
        slug = MODEL_MAP.get(kind)
        n_reached += 1
        # BOTH rotation paths now go through THE LAW (see MODEL_FRONT_DEG): place_model is handed
        # (desired FRONT azimuth - the mesh's native front), never a raw angle. The auto-face branch
        # already did this and is the render-calibrated anchor; the plain path used to pass the spec
        # rot straight through, which is right ONLY while every native front is -90 (it is, measured
        # — but that was luck, not construction, and a new model would have silently broken it).
        mrot = model_rot(rot, slug)                      # == rot today; explicit so it stays true
        # auto-face lounge seating toward the centre table (fixes 'all chairs face the wrong way')
        if (slug in MODEL_FRONT_DEG and _focal and "rot" not in it
                and kind in ("armchair", "chair", "lounge_chair", "sofa", "loveseat")
                and float(it["x"]) > 4000 and float(it["y"]) < 3000):
            icx = float(it["x"]) + float(it["w"]) / 2.0
            icy = float(it["y"]) + float(it["d"]) / 2.0
            front_az = math.degrees(math.atan2(_focal[1] - icy, _focal[0] - icx))
            mrot = front_az - MODEL_FRONT_DEG[slug]      # same law, front azimuth read off the table
            rot = front_az + 90.0                        # keep the SPEC-convention angle in sync
        mpath = _model_path(slug) if slug else None
        retint = kind in ("sofa", "loveseat", "armchair", "chair", "lounge_chair")
        # per-element preset (materials block): flat-colour presets recolour the imported
        # mesh via the retint path (keeping its rough/normal maps); texture-set presets
        # cannot be applied to a model that keeps its own PBR — say so, never silently.
        ekw, _rf = _retint_kwargs(_mat_sel, nm, kind, bool(mpath))
        _ms, _is = _slot_pair(slug, kind)
        if mpath and place_model(mpath, xm, ym, wm, dm, hm, rot=mrot,
                                 retint_fabric=_rf,
                                 model_slot=_ms, item_slot=_is, **ekw):
            n_model += 1
            continue
        # PRIMITIVE FALLBACK. It used to be built AXIS-ALIGNED and rot was DROPPED on the floor —
        # while build_floor rotates the very same parts (add_oriented_box, centre pivot). That
        # split-brain is what massed the v4 bed's head on the wrong side (see _build_bed); bed and
        # bench got bespoke rot-aware builders, and everything else stayed broken. It matters more
        # now: model_fit (2026-07-12) deliberately routes a badly-fitting mesh HERE, so this path is
        # no longer the rare one. Rotate the parts about the footprint centre, exactly as build_floor
        # does — one convention, one pivot, both renderers.
        tag = f"em-{ep}" if ep else _mat_tag(kind)   # element preset routes the primitive too
        xi, yi = float(it["x"]) * MM_IN, float(it["y"]) * MM_IN
        wi, di = float(it["w"]) * MM_IN, float(it["d"]) * MM_IN
        hi = max(float(it.get("h", 400)) * MM_IN, 0.5)
        prims = [add_box(f"{tag}__{pname}".replace(" ", "_"),
                         px * IN, py * IN, pz * IN, pdx * IN, pdy * IN, pdz * IN)
                 for (pname, px, py, pz, pdx, pdy, pdz)
                 in furniture.parts(kind, nm, xi, yi, wi, di, hi)]
        _rotate_about_z(prims, xm + wm / 2.0, ym + dm / 2.0, rot)
    if n_model:
        print(f"  placed {n_model} real CC0 furniture models (Poly Haven)")
    # R8'S ACQUIRE HALF, AS A NUMBER IN THE RENDER PATH. Measured 2026-08-10: on the
    # canonical suite this reads 0 of 6, because every kind in it is intercepted by a
    # bespoke procedural builder that `continue`s before MODEL_MAP is consulted — so
    # `place_model` and `model_fit` never see an item and the acquire path is
    # unreachable from the lane whose plan calls acquisition its strongest lever.
    #
    # The second half is a lie this file has already told once and told again. The
    # MODEL_MAP comment records the bench mapping going dead in 2026-07-11 and calls
    # leaving it in "a lie about what the renderer does" — and `side_table ->
    # coffee_table_round_01` is dead in exactly the same way for any spec whose side
    # table carries a lamp, which is both of this room's. It is NOT deleted, because
    # two experiment specs still reach it; it is COUNTED, so the lie cannot be silent.
    _n_items = len(spec.get("items", []))
    _n_decl = sum(1 for it in spec.get("items", []) if it.get("model"))
    print(f"  acquire path (R8): {_n_decl} of {_n_items} item(s) DECLARE a model, "
          f"{n_acquired} acquired, {n_acq_fallback} fell back to a builder; "
          f"{n_reached} reached place_model via MODEL_MAP and {n_intercepted} "
          f"carried a MODEL_MAP entry a bespoke builder intercepted first")

    # seating group bbox (the lounge, east half) — drives the rug + the hero camera.
    # the lounge conversation group = the big pieces in the SOUTH-EAST (x>4m, y<3m). Exclude
    # small side/corner tables so the group bbox (rug + hero camera target) frames tight and
    # the sofa isn't shoved to the frame edge by a far corner accent table.
    seat = {"sofa", "loveseat", "armchair", "chair", "lounge_chair", "coffee_table", "round_table"}
    seats = [it for it in spec.get("items", [])
             if it.get("kind") in seat and float(it["x"]) > 4000 and float(it["y"]) < 3000]
    gx0 = gx1 = gy0 = gy1 = None
    if seats:
        gx0 = min(float(it["x"]) for it in seats) * MM
        gx1 = max(float(it["x"]) + float(it["w"]) for it in seats) * MM
        gy0 = min(float(it["y"]) for it in seats) * MM
        gy1 = max(float(it["y"]) + float(it["d"]) for it in seats) * MM
        _add_rug("rug__lounge", gx0 - 0.55, gy0 - 0.35, (gx1 - gx0) + 1.1, (gy1 - gy0) + 0.7)

    _add_styling(spec)                     # ELEMENT 8: BEFORE _suite_materials — the
    #                                        router paints these parts by their name token
    _suite_materials(spec)
    _dress_scene(spec)                         # vases on the centre table + a floor plant
    _bevel_edges(width_m=0.005, segments=3)   # softer edges read as real furniture/millwork

    xs = [p[0] for p in outline_m]; ys = [p[1] for p in outline_m]
    hero = bool(spec.get("_hero") and seats)
    # The eye branch's own condition, named once: `_eye` alone is not the eye path
    # (a spec with no items falls through to the dollhouse overview), and the
    # resolution below must follow the branch that actually ran, not the flag.
    _eye_path = bool(not hero and spec.get("_eye") and spec.get("items"))
    if hero:
        cx = (gx0 + gx1) / 2.0; cy = (gy0 + gy1) / 2.0
        _hero_camera(gx0, gy0, gx1, gy1, h, min(xs), min(ys), max(xs), max(ys))
        _add_ceiling(outline_m, h)                    # enclose -> no HDRI leak over the walls
        _add_feature_slats(min(xs), max(xs), min(ys), h)  # fluted slat wall (kills the 'dumb blank wood wall')
        _hero_lighting(min(xs), min(ys), max(xs), max(ys), h, cx, cy, gx0, gx1)  # layered luxury light
        # HERO keeps its tuned STUDIO env — like curtains, the exterior garden is
        # skipped here: the hero restages behind SOLID walls (no glazing to see the
        # garden through) and its whole light is tuned for brown_photostudio_07 @ 0.2
        # (review 2026-07-17b: routing the override through hero swaps a glassless
        # studio composition onto a garden it cannot show).
        _hdri_world("brown_photostudio_07", strength=0.2, rot_deg=30.0, exposure=0.0,
                    look="AgX - Medium High Contrast")
    elif spec.get("_eye") and spec.get("items"):
        add_interior_lights(spec, h)
        _add_ceiling(outline_m, h)                    # enclose -> no HDRI leak over the walls
        add_suite_eye_camera(spec, outline_m, h)
        # EYE is the client-facing window view — the ONLY path a spec.exterior garden
        # + Juliet rail belongs on (an eye-level look OUT through the glass-L).
        # lane B: the story state scales whatever env strength actually WON — the
        # b1 quick caught the first cut multiplying the call-site default that
        # spec.exterior's declared strength then discards (line ~1271): a knob wired
        # to a value the resolver throws away is the revert-by-omission class with
        # extra steps. Story off = the declared/tuned strength exactly.
        _wargs = _exterior_world_args(spec, "brown_photostudio_02", 0.3, 30.0, -0.1,
                                      "AgX - Medium High Contrast")
        _hs = _e5.story_scales(bool(spec.get("_light_story")))["hdri"]
        _hdri_world(_wargs[0], _wargs[1] * _hs, *_wargs[2:])
        if spec.get("_light_story"):
            # story mode: trim exposure so the dimmed ambient lets the lamp
            # pools and slat-wash accents read as pools (the whole point of
            # the 3:1 focal ratio) instead of being lifted back to a wash
            bpy.context.scene.view_settings.exposure -= 0.10
    else:
        # OVERVIEW = the open-top dollhouse QA / hybrid CONTROL leg (make_all): kept on
        # the studio env so the exterior override never silently shifts the control
        # (review 2026-07-17b). A garden HDRI flooding the open top is a QA-view change
        # nobody asked for; the decided garden lives on the eye deliverable.
        add_interior_lights(spec, h)
        add_suite_camera(min(xs), max(xs), min(ys), max(ys), h)
        _hdri_world("brown_photostudio_02", strength=1.0, rot_deg=30.0, exposure=-0.1)
    name = r.get("type", "suite") + ("_hero" if spec.get("_hero") else
                                     ("_eye" if spec.get("_eye") else ""))
    # --suffix=<tag>: render/save under a distinct name. The repair loop and make_all
    # consume output/room_<name>.png as the hybrid CONTROL — an experimental variant
    # (e.g. spec-materialized) must never overwrite that leg silently.
    if spec.get("_suffix"):
        name += "_" + str(spec["_suffix"])
    _samples = 400 if hero else 256
    _res = (2400, 1500) if hero else (2000, 1400)
    if _eye_path:
        # DELIV-001 P1a: the client-facing frame renders at the census resolution,
        # and camera_config REFUSES a value under the standard's own D1 floor. The
        # floor is read here rather than baked in so the two files cannot drift.
        _res = camera_config.deliverable_res(_d1_floor_mp())
    if spec.get("_quick"):
        # R5 rung: distinct _ql name so the deliverable pair is never overwritten
        # by a cheap frame, and the .blend beside it records the SAME quick settings.
        _samples, _res = quicklook.quick_params(_samples, _res)
        name += "_" + quicklook.QUICK_SUFFIX
        print(f"  QUICK-LOOK rung (R5): samples={_samples} res={_res} — a pass here "
              f"kills/continues work; only the full-fidelity pair closes a gate")
    save(name, samples=_samples, res=_res)        # ONE source, so the .blend matches the PNG
    if spec.get("render"):
        render(name, samples=_samples, res=_res)
    if _eye_path:
        _score_deliverable(name, quick=bool(spec.get("_quick")),
                           frame=bool(spec.get("render")))
    print(f"  built SUITE '{name}' {(max(xs)-min(xs)):.1f}x{(max(ys)-min(ys)):.1f}m + "
          f"{len(spec.get('builtins',[]))} built-ins + {len(spec.get('items',[]))} items")
    return f"OK: {label}"


def build(spec, label="default"):
    """Dispatch: room-spec@0.2 (outline_mm) -> build_suite; else the rectangular builder."""
    if spec.get("room", {}).get("outline_mm"):
        return build_suite(spec, label=label)
    return build_rect(spec, label=label)


def build_rect(spec, label="default"):
    # the rect path knows nothing of the suite-era features: refuse rather than silently
    # overwrite the control leg (--suffix) or ignore a materials block (review 2026-07-14).
    # exterior (garden HDRI + Juliet rail) and the curtain blocks join that guard
    # (review 2026-07-17b): each is consumed only in build_suite, so a rect spec
    # carrying one would render the studio default / bare glass with the decided
    # element silently dropped — the exact revert-by-omission those blocks exist to kill.
    _suite_only = [k for k in ("_suffix", "materials", "exterior", "curtains",
                               "curtain_track", "lighting", "casement_sheers")
                   if spec.get(k)]
    if _suite_only:
        raise ValueError(f"{_suite_only} are suite-path features (room.outline_mm "
                         "specs); the rect path would silently ignore them — remove "
                         "them or use a suite spec")
    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"

    r = spec["room"]
    w = r["width_in"] * IN
    d = r["depth_in"] * IN
    h = r["ceiling_in"] * IN
    thk = r.get("wall_thk_in", 4.5) * IN
    fth = r.get("floor_thk_in", 4.0) * IN
    door = r.get("door") or {"w_in": 32, "h_in": 80}   # `or` also catches explicit JSON null
    dw = door.get("w_in", 32) * IN
    dh = door.get("h_in", 80) * IN
    # Clamp the door inside the wall so it can't invert the piers or make a
    # negative-height header (silently-wrong geometry).
    dw = max(min(dw, w - 2 * thk), 1 * IN)
    dh = max(min(dh, h), 1 * IN)

    # Shell.
    add_box("floor", 0, 0, -fth, w, d, fth)
    add_box("wall_north", -thk, d, 0, w + 2 * thk, thk, h)
    add_box("wall_west", -thk, 0, 0, thk, d, h)
    add_box("wall_east", w, 0, 0, thk, d, h)
    # South wall WITH a centered door opening: left pier | header | right pier
    # (authored as solid boxes — no boolean, which would n-gon the mesh).
    door_l = (w - dw) / 2.0
    door_r = (w + dw) / 2.0
    add_box("wall_south_pier_L", -thk, -thk, 0, door_l + thk, thk, h)
    add_box("wall_south_pier_R", door_r, -thk, 0, (w + thk) - door_r, thk, h)
    header_h = h - dh
    if header_h > 1e-6:
        add_box("wall_south_header", door_l, -thk, dh, dw, thk, header_h)

    # Furniture: each item -> recognizable primitives (furniture.py, pure-python),
    # materialized as boxes. Single box for unknown kinds. (Lazy name/kind lookup
    # avoids the eager it["kind"] KeyError.)
    items = spec.get("items", [])
    for it in items:
        if placement_gate.scene_zone_decision(it)["action"] == "skip":
            continue                                   # owner-signed below_grade: not a floor-2 object
        kind = it.get("kind", "block")
        nm = it.get("name") or kind
        ht = max(float(it.get("h", 18)), 0.5)
        for (pname, px, py, pz, pdx, pdy, pdz) in furniture.parts(
                kind, nm, float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"]), ht):
            add_box("item_" + str(pname).replace(" ", "_"),
                    px * IN, py * IN, pz * IN, pdx * IN, pdy * IN, pdz * IN)

    _basic_materials()
    _bevel_edges()
    add_camera_and_light(w, d, h)
    _environment()
    name = r.get("type", "room")
    _qs, _qr = 128, (1600, 1000)                  # the rect path's save()/render() defaults
    if spec.get("_quick"):
        _qs, _qr = quicklook.quick_params(_qs, _qr)
        name += "_" + quicklook.QUICK_SUFFIX
        print(f"  QUICK-LOOK rung (R5): samples={_qs} res={_qr}")
    save(name, samples=_qs, res=_qr)
    if spec.get("render"):
        render(name, samples=_qs, res=_qr)

    print(f"  built '{name}' {r['width_in']}x{r['depth_in']}in, ceiling {r['ceiling_in']}\" + {len(items)} items")
    print("  -> run  python pipeline/clearance_check.py <spec.json>  for the dimensional PASS/WARN/FAIL report")
    return f"OK: {label}"


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    # D2: a room-spec can now say, in a field, that the owner has NOT adopted it -- part of its
    # perimeter is agent-provisional geometry nobody signed. Rendering it is allowed (it is a
    # measurement artefact and it must stay inspectable), rendering it SILENTLY is not: that is
    # exactly how an unsigned guess becomes an "owner-approved" room one stage downstream.
    ip = spec.get("ink_provenance") or {}
    if ip.get("adopted") is False:
        print("=" * 78)
        print("  WARNING: THIS ROOM IS NOT OWNER-ADOPTED.")
        print("  %s mm of its perimeter is covered by NO signature."
              % ip.get("NOT_covered_by_any_signature_mm"))
        for v in ip.get("virtual_walls", []):
            if v.get("provenance") != "owner-signed":
                print("    UNSIGNED  %s  %s  %s mm" % (v.get("id"), v.get("spec"),
                                                       v.get("length_mm")))
        print("  The walls it extrudes for those edges are NOT on the sheet. Do not present this")
        print("  render as an approved design, and do not score anything against its geometry.")
        print("=" * 78)
    return spec


def _post_dashdash():
    """Script args after the literal `--` in `blender -b --python build_room.py -- ...`."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _spec_path_from_argv():
    """First non-flag token after `--` = the spec path (flags like --render are skipped)."""
    return next((a for a in _post_dashdash() if not a.startswith("-")), None)


def _force_render_from_argv():
    """`--render` after `--` forces a Cycles render even if the spec sets render:false
    (make_all --render uses this to embed the preview in the package)."""
    return "--render" in _post_dashdash()


# `or True` used to defeat this guard, so merely IMPORTING build_room built and rendered a scene —
# which is why the facing convention (MODEL_FRONT_DEG, model_rot, _head_dir) had no unit tests: it
# was untestable. Blender runs a `--python` script as __main__, so the guard is enough; verified by
# re-running the v4 hero render after the change (2026-07-12).
if __name__ == "__main__":
    _p = _spec_path_from_argv()
    _spec = load_spec(_p) if _p else DEFAULT_SPEC
    if _force_render_from_argv():
        _spec["render"] = True
    if "--quick" in _post_dashdash():     # R5 playblast rung: cheap first LOOK, implies render
        _spec["_quick"] = True
        _spec["render"] = True
    if "--sim-garments" in _post_dashdash():
        # round-5 lane (R1-stopped, funded by owner order "ก"): flip the styling
        # flag for this build only — the committed default stays False until the
        # lane passes its gate, and the flag means experiments never need a
        # source edit to reproduce.
        styling.SIM_GARMENTS = True
    if "--shred-report" in _post_dashdash():
        globals()["_SHRED_MODE"] = "report"
    if "--light-story" in _post_dashdash():
        # hero dimmer state over the signed e5 plan (lane A) — spec untouched
        _spec["_light_story"] = True
        globals()["_LIGHT_STORY"] = True
    if "--no-acquire" in _post_dashdash():
        # The A leg of every acquisition A/B: build every item the way the bespoke
        # builders would, ignoring `model`. Same discipline as --no-fabric-maps — an
        # A/B whose A leg needs a source edit is an A/B nobody re-runs.
        _spec["_no_acquire"] = True
    if "--no-fabric-maps" in _post_dashdash():
        # the A leg of D-022's A/B, kept runnable so the decision can be re-tested
        # without editing source (R6) — and so "revert by omission" is impossible.
        _spec["_fabric_maps"] = False
        globals()["_FABRIC_MAPS"] = False
    if "--fabric-maps" in _post_dashdash():
        # lane B A/B flag: compose the CC0 2k weave maps onto the signed textile
        # signature (_woven block 6). Off = the exact procedural-only state, so the
        # A/B pair differs by ONE mechanism.
        _spec["_fabric_maps"] = True
        globals()["_FABRIC_MAPS"] = True
    _smax = next((a.split("=", 1)[1] for a in _post_dashdash()
                  if a.startswith("--shred-max=")), None)
    if _smax:
        # CALIBRATION OVERRIDE ONLY: lets a probe render a piece that sits between
        # the synthetic bands so the EYE can rule on it — the committed threshold
        # in clothcheck.py moves only with a recorded verdict, never via this flag.
        import clothcheck as _cc
        _cc.SHRED_FRAC_MAX = float(_smax)
        print(f"  [calibration] SHRED_FRAC_MAX overridden to {_smax} for this run")
    if "--hero" in _post_dashdash():      # close magazine shot of the lounge seating group
        _spec["_hero"] = True
    if "--eye" in _post_dashdash():       # eye-level interior shot aimed at the main piece
        _spec["_eye"] = True
    _sfx = next((a.split("=", 1)[1] for a in _post_dashdash()
                 if a.startswith("--suffix=")), None)
    if _sfx:                              # distinct output name for experimental variants
        _spec["_suffix"] = _sfx
    _ecam = next((a.split("=", 1)[1] for a in _post_dashdash()
                  if a.startswith("--eyecam=")), None)
    if _ecam:
        # named eye-camera VARIANT from spec data (review 2026-07-17: the canonical
        # hero eye view is blind to the curtain decision — 0 curtain pixels — so the
        # verify views must be reproducible DATA, not ad-hoc scratch specs). Fails
        # loud on an unknown name; implies --eye (a variant IS an eye view).
        _vars = _spec.get("eye_camera_variants") or {}
        if _ecam not in _vars:
            # print + hard-exit (the try below only guards build(); headless Blender
            # swallows an exception here and would exit 0 on a typo'd variant name)
            print(f"BUILD FAILED: --eyecam={_ecam}: spec has no eye_camera_variants"
                  f"[{_ecam!r}] (known: {sorted(_vars)})")
            sys.stdout.flush()
            os._exit(1)
        _spec["eye_camera"] = _vars[_ecam]
        _spec["_eye"] = True
        _spec["_suffix"] = _spec.get("_suffix") or _ecam
    _sfx_final = _spec.get("_suffix")
    if _sfx_final and (_sfx_final == quicklook.QUICK_SUFFIX
                       or str(_sfx_final).endswith("_" + quicklook.QUICK_SUFFIX)):
        # R5 name law: '_ql' is the quick rung's reserved tail — a full-fidelity
        # variant wearing it would collide with (and silently overwrite) the cheap
        # frame of the same spec, making a deliverable mistakable for a quick-look.
        print(f"BUILD FAILED: --suffix/--eyecam {_sfx_final!r} ends in the reserved "
              f"quick-look tail '_{quicklook.QUICK_SUFFIX}' (R5); pick another name")
        sys.stdout.flush()
        os._exit(1)
    # D-021 — THE RENDER PATH THAT MAKES THE DELIVERABLE FRAME NOW CALLS A GATE.
    # Measured 2026-08-10, before this line existed: `rule_gate` was imported by
    # trn002_build.py and NOTHING ELSE, so a DELIV-001 frame rendered past no
    # contact check, no decision log, no pixel rung and no debt rung — and P1
    # would then have scored it with a standard nothing enforced.
    #
    # It is `check_room`, not `check`, and that is the decision rather than a
    # convenience: `check` returns "no coverage manifest path given" as a
    # VIOLATION, and on this lane that manifest is a READING OF A REFERENCE that
    # does not exist. Blocking client work on the absence of an artefact that
    # could never be correct to make is how a guard gets switched off. So the
    # rungs that do not transfer are DECLARED in the roster with their reason —
    # printed on every build, because the finding this whole phase rests on is
    # that a rung which did not run must never read like one that passed.
    #
    # It BLOCKS. Report-only was the other option and CLAUDE.md already names it
    # a mistake this repo has shipped once ("declared mandatory and then printed
    # as a suggestion for a human to copy").
    import room_masses as _RM
    if _RM.is_room_spec(_spec):
        if "--no-rule-gate" in _post_dashdash():
            # Same shape as trn002_build's bypass: a bypass whose only cost is
            # typing the flag is the default with extra steps.
            if os.environ.get("BUILD_ROOM_ALLOW_RULE_GATE_BYPASS") != "1":
                print("BUILD FAILED: --no-rule-gate requires "
                      "BUILD_ROOM_ALLOW_RULE_GATE_BYPASS=1. It exists for "
                      "bisecting an OLD spec, not for getting past a gate that "
                      "is telling you something.")
                sys.stdout.flush()
                os._exit(1)
            print("!! RULE GATE BYPASSED by --no-rule-gate")
        else:
            import rule_gate as _RG
            _gs = _RM.as_gate_spec(_spec, _p)
            _roster = []
            _viol = _RG.check_room(_gs, roster=_roster)
            print("RULE GATE (room lane) — what ran and what did not:")
            for _n, _ran, _why in _roster:
                print(f"  [{'x' if _ran else ' '}] {_n:26s} {_why}")
            if _viol:
                print(f"\nRULE GATE FAILED (R10): {len(_viol)} object(s) do not "
                      f"justify their own existence")
                for _s in _viol:
                    print(f"  !! {_s}")
                sys.stdout.flush()
                os._exit(1)

    try:
        print(build(_spec, label=os.path.basename(_p) if _p else "DEFAULT_SPEC"))
    except BaseException as _e:  # noqa: BLE001 — incl. SystemExit (the --eye solver)
        # Headless Blender swallows script exceptions and EXITS 0 — a caller (make_all,
        # the experiment driver, a gate) would read an invalid materials block or a
        # failed camera solve as SUCCESS (review finding 2026-07-14). os._exit sidesteps
        # Blender's handler so a failed build is a failed process.
        import traceback
        traceback.print_exc()
        print(f"BUILD FAILED: {_e}")
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
