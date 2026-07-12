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
import camera_config   # eye-camera height + its coupled LOS threshold (M3.2 designer-cited, testable)
import placement_gate  # bpy-free pure logic: scene_zone_decision (owner-signed below_grade -> excluded)

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


def save(name):
    path = os.path.join(_outdir(), f"room_{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"  saved: {path}")


def render(name, samples=128, res=(1600, 1000)):
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'   # EEVEE needs EGL/Xvfb headless; Cycles is the safe choice
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
    scn.render.resolution_x, scn.render.resolution_y = res
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


def _bevel_edges(width_m=BEVEL_WIDTH_M, segments=2):
    """KB §8.4: no real edge is perfectly sharp — a ~1mm bevel lets every edge catch a
    highlight, which is one of the biggest 'CG vs photoreal' tells. Non-destructive
    Bevel modifier, so the geometry stays editable."""
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or obj.get("ph_model"):   # don't bevel imported detailed models
            continue
        mod = obj.modifiers.new(name="edge_bevel", type='BEVEL')
        mod.width = width_m
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


def poly_walls_bpy(prefix, outline_m, thk, h, door):
    """Build every wall of a polygon (outward normals from the winding), door gap+header."""
    import math
    ccw = _signed_area(outline_m) > 0
    n = len(outline_m)
    for i in range(n):
        p1 = outline_m[i]; p2 = outline_m[(i + 1) % n]
        dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        a = (dx / L, dy / L)
        out = (a[1], -a[0]) if ccw else (-a[1], a[0])
        gap = _door_on_edge_m(door, p1, a, L)
        if gap:
            u0, u1, dh = gap
            s = lambda u: (p1[0] + a[0] * u, p1[1] + a[1] * u)
            if u0 > 1e-4:
                add_wall(f"wall_{prefix}{i}a", p1, s(u0), out, thk, h)
            if L - u1 > 1e-4:
                add_wall(f"wall_{prefix}{i}b", s(u1), p2, out, thk, h)
            if h - dh > 1e-4:
                add_wall(f"wall_{prefix}{i}h", s(u0), s(u1), out, thk, h - dh, z0=dh)
        else:
            add_wall(f"wall_{prefix}{i}", p1, p2, out, thk, h)


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
        cam_data.dof.aperture_fstop = 9.0    # gentle DoF, subject stays crisp
    except Exception:
        pass
    bpy.context.scene.camera = cam
    # soft cool fill from behind the lens: the eye shot runs ENCLOSED (ceiling on), so
    # without it the room is downlights-only and the gate dings 'flat lighting' again.
    fill_data = bpy.data.lights.new("Fill", type='AREA')
    fill_data.energy = 60; fill_data.size = 2.0
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


def _solid(name, rgba, rough, metallic=0.0, sheen=0.0, coat=0.0, ior=1.45, spec=0.5):
    """Clean physically-plausible Principled material (no texture). sheen -> fabric,
    coat -> lacquer/marble sheen, metallic+low rough -> brass/chrome."""
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
            _set(bsdf, "Sheen Roughness", 0.3)
        if coat:
            _set(bsdf, "Coat Weight", coat)
            _set(bsdf, "Coat Roughness", 0.1)
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
    mr.inputs["To Min"].default_value = 0.94
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
    bump.inputs["Strength"].default_value = 0.08
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
    mr2.inputs["To Min"].default_value = max(0.0, rough - 0.08)
    mr2.inputs["To Max"].default_value = min(1.0, rough + 0.04)
    nt.links.new(gz.outputs["Fac"], mr2.inputs["Value"])
    nt.links.new(mr2.outputs["Result"], bsdf.inputs["Roughness"])
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


def _add_rug(name, x, y, w, d, thick=0.014):
    """A thin textured rug slab under a seating group (own planar UV + wool/herringbone
    PBR). Sits just above the floor to avoid z-fighting. Anchors the furniture group so the
    floor doesn't read as an empty plane (KB scene-dressing)."""
    obj = add_box(name, x, y, 0.004, w, d, thick)
    _planar_uv(obj, tile_m=1.3)
    obj.data.materials.append(_pbr_material("rug_" + name, RUG_SLUG))
    return obj


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
    plant beside the seating group. Positions derived from the spec so it generalises."""
    placed = 0
    items = spec.get("items", [])
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
                             0.13, 0.13, 0.30, z0=top):
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
    # a small potted plant on the centre table for a touch of green
    if tbl:
        p = _model_path("calathea_orbifolia_01")
        if p and place_model(p, tx + 0.15 * tw, ty + 0.12 * td, 0.22, 0.22, 0.3,
                             z0=max(float(tbl.get("h", 350)) * MM, 0.05)):
            placed += 1
    if placed:
        print(f"  dressed scene with {placed} decor pieces")
    return placed


# floor/millwork texture choices (swap FLOOR_SLUG to 'marble_01' or 'grey_cartago_01'
# for a marble scheme). Kept as constants so the iteration loop can retune in one place.
FLOOR_SLUG = "wood_floor"
WALL_RGBA = (0.83, 0.80, 0.75, 1.0)    # matte warm-white paint
RUG_SLUG = "poly_wool_herringbone"


def _suite_materials():
    """Warm luxury interior palette using REAL CC0 PBR textures where they help
    (floor grain/reflection), clean physically-based solids elsewhere. Assigned by
    object-name PREFIX (tag__...). Imported furniture models keep their own PBR."""
    floor = _pbr_material("floor_pbr", FLOOR_SLUG)                                   # warm oak grain
    wall = _painted("wall_paint", WALL_RGBA, 0.88)                                   # matte warm-white
    feature = _pbr_material("feature_walnut", FLOOR_SLUG, base_tint=(0.40, 0.28, 0.20, 1.0),
                            variation=0.06)  # walnut backdrop, drift breaks tile repeats
    # LINEAR-space walnut (sRGB ~#5F4430): Blender default_value is linear — a
    # 'looks right in sRGB' triple renders as pale pink-beige (round-2 lesson).
    mill = _veneer("mill_walnut", (0.105, 0.052, 0.026, 1.0), 0.45)  # rift-walnut veneer, matte lacquer
    fab = _solid("fabric_boucle", (0.84, 0.79, 0.71, 1.0), 0.92, sheen=0.8)         # cream boucle (sheen)
    wood = _pbr_material("wood_oak", FLOOR_SLUG)                                     # oak on wood items
    fix = _solid("sanitary_white", (0.90, 0.91, 0.92, 1.0), 0.15, spec=0.6, coat=0.2)  # glossy sanitaryware
    furn = _solid("furn_neutral", (0.52, 0.50, 0.48, 1.0), 0.55)
    M = {"wall": wall, "mill": mill, "fab": fab, "wood": wood, "fix": fix, "furn": furn}
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
            obj.data.materials.append(wall)
            continue
        if n.startswith("mill__"):
            # millwork previously had NO UV -> flat featureless slabs (the 'flat
            # panel' judge datapoint). Round-1 lesson: do NOT map the floor plank
            # texture here (reads as flooring-on-walls, tanked the bedroom A/B) —
            # _veneer is procedural (world-space), no UV needed.
            obj.data.materials.append(mill)
            continue
        if n.startswith("rug__"):                        # rug already carries its own PBR
            continue
        key = n.split("__", 1)[0] if "__" in n else "furn"
        obj.data.materials.append(M.get(key, furn))


def add_interior_lights(spec, h_m):
    """Place warm ceiling lights at the SAME positions as the RCP lighting layout
    (suite_lighting), so the render is lit like the room's real fixture plan — the
    single biggest lift from 'grey massing' to 'a lit room'."""
    try:
        import suite_lighting
        fixtures, _ = suite_lighting.plan_lighting(spec)
    except Exception as e:
        print(f"  (interior lights skipped: {e})")
        return 0
    warm = (1.0, 0.82, 0.60)
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
    "bench": "Ottoman_01",
}

# Native facing of each model AFTER glTF import: the compass azimuth (deg; +X=0, +Y=90)
# the piece's FRONT points at rot=0. Calibrated by inspecting a render. Auto-face rotates
# a seating item so its front points at the conversation focal point (the centre table).
MODEL_FRONT_DEG = {
    "modern_arm_chair_01": -90.0,     # faces -Y (south) as imported
    "mid_century_lounge_chair": -90.0,
    "sofa_02": -90.0,                 # faces -Y as imported -> auto-face flips it to the room
}


def _rbox(name, x0, y0, z0, w, d, hgt, mat, bevw=0.02, seg=3):
    """A rounded (bevel-modifier) box with a material — the primitive for procedural
    modern furniture. Soft edges are what separate a modern-luxury cushion from a CG cube."""
    o = add_box(name, x0, y0, z0, w, d, hgt)
    o.data.materials.append(mat)
    o["ph_model"] = 1                       # skip the global 1mm _bevel_edges (we bevel here)
    m = o.modifiers.new("bev", 'BEVEL')
    m.width = bevw; m.segments = seg; m.limit_method = 'ANGLE'; m.angle_limit = 0.5236
    return o


def _build_modern_sofa(x0, y0, W, D):
    """Build a clean low-profile MODERN sofa from beveled primitives, back to the SOUTH wall,
    facing +Y (the room). All three CC0 sofas are vintage Victorian/baroque — they fight the
    modern slat wall + mid-century chairs. Modern-luxury seating is geometrically simple (a low
    plinth + boxy bouclé cushions + low arms), so we model it to MATCH instead of retinting a
    Chesterfield. Colours = the same cream bouclé as the retint (#DCD0BD-ish), honed matte."""
    boucle = _solid("sofa_boucle", (0.86, 0.81, 0.72, 1.0), rough=0.9, sheen=1.0, spec=0.4)
    base   = _solid("sofa_base",   (0.70, 0.66, 0.60, 1.0), rough=0.75, sheen=0.25, spec=0.4)
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
    terra = _solid("cush_terra", (0.58, 0.32, 0.23, 1.0), rough=0.75, sheen=0.6, spec=0.4)
    sage  = _solid("cush_sage",  (0.44, 0.46, 0.37, 1.0), rough=0.75, sheen=0.6, spec=0.4)
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
            return
        if from_head < -1e-9 or from_head + a_size > along + 1e-9:
            return
        if across_off < -1e-9 or across_off + c_size > across + 1e-9:
            return
        bx, by, bdx, bdy = box(from_head, across_off, a_size, c_size)
        _rbox(name, bx, by, z, bdx, bdy, dz, mat, bevw=bevw, seg=seg)

    base_m = _solid("bed_base",     (0.40, 0.36, 0.32, 1.0), rough=0.70, sheen=0.15, spec=0.4)
    matt_m = _solid("bed_mattress", (0.87, 0.85, 0.81, 1.0), rough=0.92, sheen=0.5, spec=0.35)
    duvt_m = _solid("bed_duvet",    (0.80, 0.77, 0.71, 1.0), rough=0.95, sheen=0.7, spec=0.35)
    pill_m = _solid("bed_pillow",   (0.90, 0.88, 0.84, 1.0), rough=0.95, sheen=0.8, spec=0.35)

    # Proportions matter as much as parts: a 50/50 base-to-mattress split reads as a platform
    # bed. (First pass used a 0.34 base + a 0.40 m mattress + a 0.10 m duvet — three fat slabs
    # stacked, which still cued "cube tool". Thin the cloth, thicken nothing.)
    base_h = H * 0.50                                   # platform plinth: grounds the piece
    _rbox("bed__base", x0, y0, 0.0, W, D, base_h, base_m, bevw=0.012)
    ins = 0.035                                         # mattress sits proud of the base
    _rbox("bed__mattress", x0 + ins, y0 + ins, base_h, W - 2 * ins, D - 2 * ins,
          H - base_h, matt_m, bevw=0.03)

    # duvet: a THIN cloth layer over the foot ~2/3, inset so the mattress edge still shows, and
    # dipping slightly INTO the mattress top so it reads as cloth lying on it, not a second slab.
    # NOTE: sizes below are computed, never floor-clamped — `emit` drops any part that would not
    # fit, so the footprint invariant holds for any bed size (see emit's docstring).
    pz = min(0.42, along * 0.26)                        # pillow zone, measured from the head
    dv_from = pz + 0.14
    ci = 0.015
    emit("bed__duvet", dv_from, ci, along - dv_from - 0.02, across - 2 * ci,
         H - 0.02, 0.07, duvt_m, 0.032, seg=4)
    # turned-back fold at the duvet's head edge — the single most legible "this is a made bed"
    # cue, and it gives the repaint an edge to hang linen folds on.
    emit("bed__duvet_fold", dv_from - 0.13, ci, 0.15, across - 2 * ci,
         H - 0.01, 0.09, pill_m, 0.04, seg=4)

    # two plump pillows at the HEAD, gapped (a plausible bed silhouette is what the beauty pass
    # needs in order to paint linen; a bare slab is what made the critic reach for "cube tool").
    gap = min(0.07, across * 0.06)
    pw = (across - 3 * gap) / 2.0
    for i in range(2):
        emit(f"bed__pillow{i}", 0.08, gap + i * (pw + gap), pz - 0.08, pw,
             H - 0.005, 0.16, pill_m, 0.07, seg=5)
    return True


def _build_bench(x0, y0, W, D, H, rot=0.0):
    """A formed upholstered bench: a beveled cushion on four slim tapered legs, inside the spec
    footprint. Replaces the CC0 `Ottoman_01` fallback, which — stretched to a 0.5 x 1.0 m bench
    footprint — renders as a dark leather blob the pro critic called "a simple box shape on
    legs". A real seat-on-legs silhouette (with air under it) is what reads as furniture."""
    seat_m = _solid("bench_seat", (0.84, 0.80, 0.74, 1.0), rough=0.92, sheen=0.9, spec=0.4)
    leg_m  = _solid("bench_leg",  (0.26, 0.21, 0.16, 1.0), rough=0.45, sheen=0.1, spec=0.5)
    leg_h = H * 0.62                                    # tall legs + a SLIM cushion = a bench;
    seat_h = H - leg_h                                  # a fat pad on stubs is just a box again
    lt = min(0.05, W * 0.12, D * 0.12)                  # leg thickness
    inset = 0.035
    for i, (ox, oy) in enumerate(((inset, inset), (W - inset - lt, inset),
                                  (inset, D - inset - lt), (W - inset - lt, D - inset - lt))):
        _rbox(f"bench__leg{i}", x0 + ox, y0 + oy, 0.0, lt, lt, leg_h, leg_m, bevw=0.006)
    _rbox("bench__seat", x0, y0, leg_h, W, D, seat_h, seat_m, bevw=0.045, seg=4)
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
    """Local cached .gltf for a slug, or None (no network inside Blender — assets.py
    pre-downloads; here we only read the cache)."""
    import glob
    here = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
    root = os.path.join(os.path.dirname(os.path.dirname(here)), "assets", "shared", "cc0", "models", slug)
    hits = glob.glob(os.path.join(root, "*.gltf")) + glob.glob(os.path.join(root, "*.glb"))
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


def _retint_upholstery(mats, rgba=(0.84, 0.79, 0.71, 1.0), sheen=0.85, force_all=False):
    """Recolour a model's UPHOLSTERY to cream boucle (DR: #F5F0E9, rough 0.8-0.9, Sheen 0.7-1.0)
    while leaving wood frames and metal legs alone. Because CC0 models drive Base Color from a
    DIFFUSE TEXTURE, we DISCONNECT that texture and set a flat cream, KEEPING the roughness +
    normal maps so the tufting/weave relief survives. Targets materials by name; force_all
    retints every non-metal material (for single-material models like sofa_02)."""
    for m in mats:
        if not m or not getattr(m, "use_nodes", False):
            continue
        nt, b = _principled(m)
        if not b:
            continue
        met = b.inputs.get("Metallic")
        if met is not None and not met.is_linked and met.default_value > 0.5:
            continue                                       # solid metal — keep
        name = m.name.lower()
        if not (force_all or any(k in name for k in _UPHOLSTERY_KW)):
            continue                                       # e.g. '..._legs' (wood) — keep
        bc = b.inputs.get("Base Color")
        if bc is None:
            continue
        for l in list(bc.links):                           # drop the dark diffuse texture
            nt.links.remove(l)
        bc.default_value = rgba
        _set(b, "Sheen Weight", sheen)
        _set(b, "Sheen Roughness", 0.35)
        rg = b.inputs.get("Roughness")
        if rg is not None and not rg.is_linked:
            rg.default_value = 0.9


def place_model(path, x, y, w, d, h, rot=0.0, z0=0.0, retint_fabric=False):
    """Import a gltf, UNIFORMLY scale it to fit the item footprint (undistorted), set it
    footprint-centred at (x,y) with its base at height z0 (0 = on the floor; >0 = on a
    table for decor), then rotate it `rot` degrees about world Z (so a chair can face the
    conversation group — fixes the 'all chairs face the wrong way' bug). Keeps the model's
    own PBR materials (retint_fabric recolours dark upholstery to cream boucle). Coords
    metres. Returns True on success."""
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
    if mw <= 1e-6 or md <= 1e-6:
        return False
    s = min(w / mw, d / md)                      # uniform footprint fit (no distortion)
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
    if retint_fabric:
        mats = {slot.material for o in meshes for slot in o.material_slots if slot.material}
        _retint_upholstery(mats, force_all=(len(mats) == 1))   # single-mat model = all cream
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
    # bright slit) + a ceiling below; the overview keeps the real door opening.
    poly_walls_bpy("", outline_m, thk, h, None if spec.get("_hero") else spec.get("door"))

    for si, sr in enumerate(spec.get("subrooms", [])):
        so = [(float(x) * MM, float(y) * MM) for x, y in sr["outline_mm"]]
        sh = float(sr.get("ceiling_mm", 2000)) * MM
        poly_walls_bpy(f"s{si}_", so, thk, sh, sr.get("door"))
        for fx in sr.get("fixtures", []):
            add_box("fix__" + str(fx.get("name", "fixture")).replace(" ", "_"),
                    float(fx["x"]) * MM, float(fx["y"]) * MM, 0,
                    float(fx["w"]) * MM, float(fx["d"]) * MM, max(float(fx.get("h", 400)) * MM, 0.02))

    for b in spec.get("builtins", []):
        bh = float(b["h"]) * MM if b.get("h") else h
        # mount_mm = height above the floor the element's BASE sits (AFF). Default 0 =
        # floor-standing (wardrobes/cabinets/full-height millwork). A WALL-MOUNTED element
        # (TV panel, floating shelf) sets it so the control mass FLOATS on the wall instead
        # of a floor block — the designer's "ทำไมเอา TV ไปติดไว้ที่พื้น?" fix (built-ins used to
        # always extrude from z=0, so a wall TV rendered as a slab on the floor).
        bz = float(b.get("mount_mm", 0) or 0) * MM
        add_box("mill__" + str(b.get("name", "builtin")).replace(" ", "_"),
                float(b["x"]) * MM, float(b["y"]) * MM, bz,
                float(b["w"]) * MM, float(b["d"]) * MM, bh)

    # loose furniture: a REAL CC0 model (Poly Haven) when the kind is mapped + cached,
    # else furniture.py primitives (which work in INCHES). Models are fit to the footprint.
    MM_IN = 1.0 / 25.4
    n_model = 0
    # conversation focal point = the lounge centre table; lounge seating auto-faces it.
    _ct = next((it for it in spec.get("items", [])
                if it.get("kind") in ("coffee_table", "round_table")
                and float(it["x"]) > 4000 and float(it["y"]) < 3000), None)
    _focal = ((float(_ct["x"]) + float(_ct["w"]) / 2.0, float(_ct["y"]) + float(_ct["d"]) / 2.0)
              if _ct else None)
    for it in spec.get("items", []):
        kind = it.get("kind", "block")
        nm = it.get("name") or kind
        xm, ym = float(it["x"]) * MM, float(it["y"]) * MM
        wm, dm = float(it["w"]) * MM, float(it["d"]) * MM
        hm = max(float(it.get("h", 400)) * MM, 0.05)
        rot = float(it.get("rot", 0.0))
        if kind == "rug":
            _add_rug("rug__" + str(nm).replace(" ", "_"), xm, ym, wm, dm)
            continue
        # HERO: build a MODERN sofa from primitives (every CC0 sofa is vintage Victorian, which
        # clashes with the modern room). Back to the south wall, facing +Y (the room).
        if kind == "sofa" and spec.get("_hero"):
            _build_modern_sofa(xm, ym, wm, dm)
            n_model += 1
            continue
        # ROT-AWARE procedural massing (2026-07-11). These MUST come before MODEL_MAP /
        # furniture.parts: that fallback is called without `rot`, so it massed the bed's head
        # on the wrong side (see _build_bed) — and the clay is the beauty pass's structural
        # control, so a wrong-way bed mis-teaches the repaint which wall is the feature wall.
        if kind == "bed":
            _build_bed(xm, ym, wm, dm, hm, rot)
            continue
        if kind == "bench":
            _build_bench(xm, ym, wm, dm, hm, rot)
            continue
        slug = MODEL_MAP.get(kind)
        # auto-face lounge seating toward the centre table (fixes 'all chairs face the wrong way')
        if (slug in MODEL_FRONT_DEG and _focal and "rot" not in it
                and kind in ("armchair", "chair", "lounge_chair", "sofa", "loveseat")
                and float(it["x"]) > 4000 and float(it["y"]) < 3000):
            icx = float(it["x"]) + float(it["w"]) / 2.0
            icy = float(it["y"]) + float(it["d"]) / 2.0
            rot = math.degrees(math.atan2(_focal[1] - icy, _focal[0] - icx)) - MODEL_FRONT_DEG[slug]
        mpath = _model_path(slug) if slug else None
        retint = kind in ("sofa", "loveseat", "armchair", "chair", "lounge_chair")
        if mpath and place_model(mpath, xm, ym, wm, dm, hm, rot=rot, retint_fabric=retint):
            n_model += 1
            continue
        tag = _mat_tag(kind)
        xi, yi = float(it["x"]) * MM_IN, float(it["y"]) * MM_IN
        wi, di = float(it["w"]) * MM_IN, float(it["d"]) * MM_IN
        hi = max(float(it.get("h", 400)) * MM_IN, 0.5)
        for (pname, px, py, pz, pdx, pdy, pdz) in furniture.parts(kind, nm, xi, yi, wi, di, hi):
            add_box(f"{tag}__{pname}".replace(" ", "_"),
                    px * IN, py * IN, pz * IN, pdx * IN, pdy * IN, pdz * IN)
    if n_model:
        print(f"  placed {n_model} real CC0 furniture models (Poly Haven)")

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

    _suite_materials()
    _dress_scene(spec)                         # vases on the centre table + a floor plant
    _bevel_edges(width_m=0.005, segments=3)   # softer edges read as real furniture/millwork

    xs = [p[0] for p in outline_m]; ys = [p[1] for p in outline_m]
    hero = bool(spec.get("_hero") and seats)
    if hero:
        cx = (gx0 + gx1) / 2.0; cy = (gy0 + gy1) / 2.0
        _hero_camera(gx0, gy0, gx1, gy1, h, min(xs), min(ys), max(xs), max(ys))
        _add_ceiling(outline_m, h)                    # enclose -> no HDRI leak over the walls
        _add_feature_slats(min(xs), max(xs), min(ys), h)  # fluted slat wall (kills the 'dumb blank wood wall')
        _hero_lighting(min(xs), min(ys), max(xs), max(ys), h, cx, cy, gx0, gx1)  # layered luxury light
        _hdri_world("brown_photostudio_07", strength=0.2, rot_deg=30.0, exposure=0.0,
                    look="AgX - Medium High Contrast")
    elif spec.get("_eye") and spec.get("items"):
        add_interior_lights(spec, h)
        _add_ceiling(outline_m, h)                    # enclose -> no HDRI leak over the walls
        add_suite_eye_camera(spec, outline_m, h)
        _hdri_world("brown_photostudio_02", strength=0.3, rot_deg=30.0, exposure=-0.1,
                    look="AgX - Medium High Contrast")
    else:
        add_interior_lights(spec, h)
        add_suite_camera(min(xs), max(xs), min(ys), max(ys), h)
        _hdri_world("brown_photostudio_02", strength=1.0, rot_deg=30.0, exposure=-0.1)
    name = r.get("type", "suite") + ("_hero" if spec.get("_hero") else
                                     ("_eye" if spec.get("_eye") else ""))
    save(name)
    if spec.get("render"):
        render(name, samples=(400 if hero else 256), res=((2400, 1500) if hero else (2000, 1400)))
    print(f"  built SUITE '{name}' {(max(xs)-min(xs)):.1f}x{(max(ys)-min(ys)):.1f}m + "
          f"{len(spec.get('builtins',[]))} built-ins + {len(spec.get('items',[]))} items")
    return f"OK: {label}"


def build(spec, label="default"):
    """Dispatch: room-spec@0.2 (outline_mm) -> build_suite; else the rectangular builder."""
    if spec.get("room", {}).get("outline_mm"):
        return build_suite(spec, label=label)
    return build_rect(spec, label=label)


def build_rect(spec, label="default"):
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
    save(name)
    if spec.get("render"):
        render(name)

    print(f"  built '{name}' {r['width_in']}x{r['depth_in']}in, ceiling {r['ceiling_in']}\" + {len(items)} items")
    print("  -> run  python pipeline/clearance_check.py <spec.json>  for the dimensional PASS/WARN/FAIL report")
    return f"OK: {label}"


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


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


if __name__ == "__main__" or True:
    _p = _spec_path_from_argv()
    _spec = load_spec(_p) if _p else DEFAULT_SPEC
    if _force_render_from_argv():
        _spec["render"] = True
    if "--hero" in _post_dashdash():      # close magazine shot of the lounge seating group
        _spec["_hero"] = True
    if "--eye" in _post_dashdash():       # eye-level interior shot aimed at the main piece
        _spec["_eye"] = True
    print(build(_spec, label=os.path.basename(_p) if _p else "DEFAULT_SPEC"))
