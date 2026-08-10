"""trn002_build.py — TRN-002 materializer (Blender headless).

  blender -b --factory-startup --python pipeline/scripts/trn002_build.py -- \
      <spec.json> --out <render.png> [--quick] [--materials]

  --quick      R5 playblast rung (half res per axis, 64 samples)
  --materials  dress the masses from trn002_materials instead of clay values,
               and light the set from the spec's `light` block instead of the
               neutral form light. Phase 2 (blockout closed 2026-08-04); a
               blockout spec with no `light` block still renders exactly as it
               did, because the form light is kept as the fallback.

Round-1 scope: every mass is a clay box straight from the spec (the spec's
numbers are MEASURED through the solved camera — see trn002_station.py), a
neutral form light, and two verification rungs before any pixel is trusted:
  1. PROJECTION DUMP — pure-math projection vs Blender's world_to_camera_view
     for every landmark (>1.5 px disagreement prints LOUDLY), plus the pixel
     error against the MEASURED landmark table (the round metric of record).
  2. R9b PLACEMENT GATE — placement_dump + placement_check on the built scene,
     FAIL-loud (floating / overhang / off-axis; no allowlist).
"""
import glob
import json
import math
import os
import re
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_geom as G  # noqa: E402

MM = 0.001
FULL_SAMPLES = 128
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE_DIR = os.path.join(REPO, "training", "TRN-002")
BUNDLE_ROOT = os.path.join(REPO, "_private", "benchmark", "reproduction",
                           "TRN-002", "renders", "critique")
WAIVERS = os.path.join(LANE_DIR, "r7-triage-waivers.md")


def _clay(value):
    name = f"M_clay_{value:.2f}"
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (value, value, value, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    return m


def _surface(value, mat):
    """The one place a mass's shading is decided: a dressed material when the
    materials pass is on, the clay value otherwise. Kept as a single function so
    the two paths can never diverge per shape-kind (a box dressed and an oct
    left clay is exactly the kind of split nobody sees in a thumbnail)."""
    return mat if mat is not None else _clay(value)


def _box(name, c, s, value, mat=None):
    vs, fs = G.box_mesh(c, s)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _slats(name, c, s, value, mat=None, pitch_mm=29.4, chord_mm=34.0,
           tilt_deg=25.0, thick_mm=2.0):
    """A venetian blind as ONE mesh of 62 slats — see G.slat_stack for which of
    its numbers are measured and which are declared."""
    vs, fs = G.slat_stack(c, s, pitch_mm, chord_mm, tilt_deg, thick_mm)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _oct(name, c, s, cut, value, axis="z", tilt_deg=0.0, mat=None,
         open_face=None, seg=6):
    """Rounded prism: four true ARC corners of radius `cut` mm, `seg` per quarter.
    Round 2 shipped this as a single 45-degree chamfer and the C3 critic read it
    as a faceted octagon, not a curve — a chamfer is not a radius. Name kept so
    specs don't churn.

    axis: which axis the prism is EXTRUDED along — "z" (default: rounding in
    plan) or "y" (rounding in the x-z SECTION: a lying cylinder when cut is
    ~half the section). Earned in r3b: the bolster was built plan-rounded and
    three blind critics could not read a lying cylinder in it, because the
    roundness was in the wrong plane.

    tilt_deg: rotation about the y-axis through the bottom-BACK edge
    (x_max, z_min) — tips the top toward +x while the back edge keeps its
    mattress contact. Earned in r3b: a "lying" pillow that still stands at 90
    degrees reads as a capsule, whatever its dimensions say.
    """
    # `seg` MUST be forwarded. It was not, for every round this lane has run:
    # `craft_check` read `m["seg"]` off the spec and the builder hard-coded 6,
    # so the silhouette advisory named three masses every round and there was
    # no edit to the spec that could have silenced it. Same shape as TRN-001's
    # roughness column, which the table set and the material path overrode.
    # A CHECKER THAT READS A FIELD THE BUILDER IGNORES MEASURES A FICTION.
    vs, fs = G.oct_mesh(c, s, cut, axis=axis, tilt_deg=tilt_deg,
                        open_face=open_face, seg=seg)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cone(name, c, s, value, mat=None, seg=24):
    """A cone described by its own AABB, so every existing guard still sees it.

    Deliberately NOT a new pair of spec fields. `placement_check` reads the
    built scene's boxes, `craft_check` reads `c`/`s`, R10's justification gate
    reads `prov`/`why` — a cone carrying `apex`/`radius_mm` instead would have
    been invisible to the first two, and the lane's own history says an object
    invisible to a guard is the one that goes wrong (8 of 13 placements were
    exempt from the two guards that preceded R9b, and every figure was among
    them).

    So: apex on top of the box, rim on its floor, radius from the plan half.
    """
    if abs(s[0] - s[1]) > 1e-6:
        raise SystemExit(f"{name}: a right cone needs a circular plan, "
                         f"got {s[0]} x {s[1]} — an ellipse is a different object")
    apex = (c[0], c[1], c[2] + s[2] / 2.0)
    vs, fs = G.cone_mesh(apex, s[0] / 2.0, s[2], seg=seg)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _pocket(name, value, mat=None, host_mat=None, host_value=None, **kw):
    """An arched CAVITY cut THROUGH its host's face — see G.arch_pocket.

    Two materials on one mesh, and the split is DERIVED, never indexed: a quad
    whose four vertices all sit on the opening's plane is the host's own face
    (it wears the host's material); everything else is the cavity's lining. An
    index into a face list would go stale the first time the generator gains a
    quad, and a lining that silently spread onto the host's face is precisely
    the kind of error that reads as a shadow and gets tuned instead of fixed.
    """
    vs, fs = G.arch_pocket(**kw)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(host_value if host_value is not None else value,
                                 host_mat))
    me.materials.append(_surface(value, mat))
    plane = float(kw["face_x_mm"]) * 0.001
    for poly, f in zip(me.polygons, fs):
        poly.material_index = 0 if all(
            abs(vs[i][0] - plane) < 1e-9 for i in f) else 1
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _herringbone(name, z_mm, thick_mm, value, mat=None, **kw):
    """The measured herringbone as REAL planks, one mesh, sitting a hair proud
    of a darker base so the gaps read as joints. The floor map alone cannot do
    this: it lays parallel planks, and the target's floor is a 45-degree
    chevron whose w, L and phase were all fitted from its own joint lines."""
    kw = dict(kw)
    # 1.192 m puts exactly ONE of the map's own boards across one 132.1 mm
    # plank: the wood_floor map lays its boards at 227/2048 = 0.11084 of a tile,
    # and 132.1 / 0.11084 = 1191.8. At the previous 0.9 each plank carried ~1.3
    # of the map's boards, so a "plank" was a plank and a bit — the grain
    # crossed its own joint, which is what a real parquet never does.
    uv_scale = kw.pop("uv_scale", 1.192)
    quads = G.herringbone(**kw)
    z0, z1 = z_mm * MM, (z_mm + thick_mm) * MM
    vs, fs, uvs = [], [], []
    for q in quads:
        b = len(vs)
        vs += [(x * MM, y * MM, z1) for x, y in q]
        vs += [(x * MM, y * MM, z0) for x, y in q]
        fs.append((b, b + 1, b + 2, b + 3))                       # top
        # PER-PLANK UVs, and they are the whole point. The joints themselves are
        # SUB-PIXEL at this camera (2 mm at ~4 m through f_px 1165 is 0.58 px),
        # exactly like the wardrobe reveal the pattern pass declared
        # geometrically unresolved — so a herringbone cannot be sold by its
        # grooves here. What IS resolvable is each plank's 132 mm width (~38 px)
        # and the direction of its grain, and that only changes per plank if
        # each plank carries its own UV frame. One box projection over the whole
        # floor gives every plank identical grain, which is a parquet-printed-
        # on-lino look no amount of joint tuning can fix.
        # THE LONG AXIS IS MEASURED, NOT ASSUMED. The previous version took
        # q0->q1 as the plank's length; on a herringbone the two arms wind in
        # opposite senses, so for HALF the planks that edge is the 132 mm WIDTH
        # and their grain came out running across. Comparing the two edges is
        # the whole fix, and it costs one hypot.
        e1 = ((q[1][0] - q[0][0]), (q[1][1] - q[0][1]))
        e3 = ((q[3][0] - q[0][0]), (q[3][1] - q[0][1]))
        l1 = (e1[0] ** 2 + e1[1] ** 2) ** 0.5
        l3 = (e3[0] ** 2 + e3[1] ** 2) ** 0.5
        ex, ln = (e1, l1) if l1 >= l3 else (e3, l3)
        ux, uy = ex[0] / (ln or 1.0), ex[1] / (ln or 1.0)
        # AND EVERY PLANK NOW SAMPLES A DIFFERENT PART OF THE MAP. Each plank's
        # UV frame started at (0,0) at its own first vertex, so all 458 of them
        # read the SAME rectangle — one board's figure, printed 458 times. That
        # is trn001's recorded "printed laminate" defect (it measured its floor
        # at 1.9% plank-to-plank variation against a reference's 30.4%),
        # reintroduced here by the per-plank frame that was added to fix a
        # different defect. A fix that solves one thing can restore another.
        # The offset is derived from the plank's own world position, so it is
        # deterministic and a rebuild is bit-identical; the flip doubles the
        # library of figures for free.
        h = int(abs(q[0][0]) * 7.13 + abs(q[0][1]) * 3.71) % 997
        off_v = (h % 31) / 31.0
        off_u = ((h // 31) % 17) / 17.0
        flip = (h // 527) % 2
        for (px, py) in q:
            dx, dy = (px - q[0][0]) * MM, (py - q[0][1]) * MM
            along = (dx * ux + dy * uy) / uv_scale      # along the plank's length
            across = (-dx * uy + dy * ux) / uv_scale    # across its width
            if flip:
                along = -along
            # U <- ACROSS, V <- ALONG. The map's boards run along its V axis, so
            # feeding the plank's length into U laid the grain ACROSS every
            # plank — the one orientation a parquet floor never has.
            uvs.append((across + off_u, along + off_v))
        for k in range(4):
            k2 = (k + 1) % 4
            fs.append((b + k, b + 4 + k, b + 4 + k2, b + k2))     # side
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        if len(poly.vertices) == 4 and poly.vertices[0] % 8 == 0 and \
                poly.vertices[0] // 8 * 4 + 3 < len(uvs) and \
                all(v - poly.vertices[0] < 4 for v in poly.vertices):
            base_uv = poly.vertices[0] // 8 * 4
            for j, li in enumerate(poly.loop_indices):
                uvl.data[li].uv = uvs[base_uv + j]
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    print(f"herringbone: {len(quads)} planks, {len(vs)} verts")
    return ob


def _cloth_duvet(m, built, mat):
    """The duvet as SIMULATED cloth — the recipe is PRJ-2026-002's shipped
    folded_sheet hotel roll, inherited whole rather than re-learned (every
    simulated bed cloth in that lane passed the owner's eye; every analytic one
    failed). What TRN-002 adds is only that the feedstock footprint, the hem
    target and the bounds are MEASURED from the reference through the solved
    camera instead of derived from styling constants.

    Units: the spec speaks mm (this lane's convention); drape/softgoods speak
    world METRES (their contract) — converted here, in one place.

    The class licence, spelled out because R8 forbids hand-modelling free form:
    what never converged in TRN-001 was closed-tube pinned garments (piece 0_1
    at 27-34% shred under every configuration). A duvet is an open flat sheet
    settling on rigid outward-wound colliders — the solver's proven topology.
    No pins: bed cloth is supported by its colliders (pins are the coverlet's
    mechanism, for a band trapped under pillows)."""
    import drape
    import softgoods
    p = m["cloth"]
    x1 = (p["x0"] + p["w"]) * MM          # head edge — measured, stays fixed
    y1 = (p["y0"] + p["d"]) * MM          # far edge — declared, stays fixed
    w0, d0 = p["w"] * MM, p["d"] * MM
    colliders = []
    for n in p["colliders"]:
        ob = built.get(n)
        if ob is None:
            # a sim-surface proxy from an earlier cloth in the stack. The proxy
            # is named after its cloth, which now carries the SM_TRN002_ prefix
            # (see search_bake below) — both spellings are tried so a stack
            # baked before that change still resolves.
            import bpy as _b
            ob = (_b.data.objects.get(f"SM_TRN002_{n}__simsrf")
                  or _b.data.objects.get(f"{n}__simsrf"))
            if ob is None:
                raise KeyError(f"{m['name']}: collider '{n}' not built and no "
                               f"'{n}__simsrf' proxy — bake order wrong?")
        colliders.append(ob)
    bounds = tuple(v * MM for v in p["bounds"])

    def build(scale, sl):
        # the ladder lengthens the FALL sides: head and far edges hold their
        # measured/declared lines while the foot and near cascade gain fabric
        w, d = w0 * scale, d0 * scale
        if p.get("band"):
            vs, fs = softgoods.folded_sheet(
                x1 - w, y1 - d, w, d, p["z"] * MM,
                band=p["band"] * MM, head=p["head"], cell=p["cell"] * MM,
                salt=p.get("salt", 0))
        else:
            # a THROW has no turned-back head fold — it is a plain rectangle
            # laid across the bed. Same rig otherwise, so the two cloths cannot
            # drift into two recipes.
            vs, fs = softgoods.flat_sheet(
                x1 - w, y1 - d, w, d, p["z"] * MM,
                cell=p["cell"] * MM, salt=p.get("salt", 0))
        # FOLD SEED (route ค, owner's call 2026-08-05). The cell must be fine
        # enough to hold the target's ~75 mm fold FIRST — at 42 mm the mesh's
        # Nyquist wavelength is 84 mm and no amount of slack or frames can put
        # a 75 mm fold in it. With the resolution there, this gives the folds a
        # DIRECTION: ridges across the bed, jittered, carrying their own arc
        # excess so the fabric arrives already buckled instead of arriving flat
        # and being asked to buckle.
        r = p.get("ripple")
        if r:
            vs = G.ripple_seed(vs, axis=r.get("axis", "x"),
                               wavelength_mm=r["wavelength_mm"],
                               amp_mm=r["amp_mm"] * scale,
                               jitter=r.get("jitter", 0.35),
                               salt=r.get("salt", 3), scale=MM)
        # bounds go to search_bake ONLY (the PRJ-002 pattern): bake_sheet with
        # bounds RAISES on first violation, which kills the ladder before it
        # can halve slack or rescale — the first integration did exactly that.
        # THE OBJECT'S NAME IS BORN HERE, not at search_bake — search_bake's
        # `name` only labels its progress lines. Changing the outer one alone
        # renamed nothing, which is worth leaving on the record: the first fix
        # for the missing-cloth defect was applied to the wrong call and the
        # mask came back with the same 68 objects.
        return drape.bake_sheet(
            f"SM_TRN002_{m['name']}", vs, fs, colliders,
            frames=p.get("frames", 55), fabric=p.get("fabric", "linen"),
            mat=mat if mat is not None else _clay(m["value"]),
            thickness=p["thickness"] * MM, slack=sl,
            collide_dist=p["collide_dist"] * MM,
            # sim_surface leaves a hidden SINGLE-SHELL proxy for the next cloth
            # in the stack. Cloth-on-cloth law (drape.py:209-215): a sheet baked
            # against a SOLIDIFIED sheet tunnels between its two shells and
            # renders as mottled cloth-through-cloth at ANY collide distance.
            sim_surface=p.get("sim_surface", False))

    # hem_min is DELIBERATELY OFF for this sheet, and that is a correction of
    # mechanism rather than of a number. search_bake's hem constraint exists for
    # a coverlet hanging FREE below a plinth, where the hem's z really is the
    # design variable the cut controls. This duvet's hem lands ON THE DECK — a
    # supporting surface — so its z is set by the platform, not by the cut, and
    # feeding it to the ladder asks the length to solve for something that is
    # not free. It showed as a bounce: hem 35 -> rescale -> 264, hem 133 ->
    # rescale -> 347, each correction overshooting because the measured
    # "shortfall" was really a strip slipping over the platform edge. Three
    # rounds of retyping the same three numbers is R1's repeat signal, so the
    # numbers stopped and the rung changed. BOUNDS alone now govern, which is
    # what keeps the slack — and SLACK IS THE FOLD AMPLITUDE the target has 6.7x
    # more of than we do.
    hem = p.get("hem_min")
    # THE PREFIX IS NOT COSMETIC. Every other mass here is emitted as
    # `SM_TRN002_<name>`; these three came out of drape under their BARE names,
    # so `id_mask.py … SM_TRN002_` — the filter every ladder measurement in this
    # lane is taken through — never saw the duvet or either throw. Thirty-one
    # rounds of per-object value measurement silently excluded the three largest
    # soft-goods objects in the frame, including the one the C2 critics named as
    # the target's brightest. A selector that keys on a naming convention is only
    # as good as the convention's WEAKEST caller, and this was it. (The guard
    # that makes it impossible to happen again is in trn002_lightcheck.ladder:
    # a spec mass with no mask row is now reported, not skipped.)
    return drape.search_bake(
        build, name=f"SM_TRN002_{m['name']}", bounds=bounds,
        hem_min=None if hem is None else hem * MM, top_z=p["z"] * MM,
        slack=p.get("slack", 0.04))


def build_camera(cam, beauty=None):
    data = bpy.data.cameras.new("CAM_TRN002")
    data.lens = cam["focal_mm"]
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = G.SENSOR_MM
    data.shift_x = cam.get("shift_x", 0.0)
    data.shift_y = cam.get("shift_y", 0.0)
    # DEPTH OF FIELD — off unless the spec asks, so every reproduction frame
    # renders exactly as it did. The 2026-07-30 ground-truth study measured
    # every camera in five professional interior .blend files at f/1.4-2.4 and
    # ranked "f/2.0-2.8 detail camera" as one of eight wire items; this lane
    # set lens, sensor and shift and never touched aperture, i.e. it renders a
    # pinhole. Nothing in the ladder can see this: DOF moves no per-surface
    # mean, which is why 27 rounds of per-surface metrics never asked for it.
    cd = (beauty or {}).get("camera") or {}
    if cd.get("fstop"):
        data.dof.use_dof = True
        data.dof.aperture_fstop = float(cd["fstop"])
        data.dof.focus_distance = float(cd["focus_mm"]) * MM
        data.dof.aperture_blades = int(cd.get("blades", 7))
    ob = bpy.data.objects.new("CAM_TRN002", data)
    ob.location = (cam["x_mm"] * MM, cam["y_mm"] * MM, cam["z_mm"] * MM)
    ob.rotation_euler = (math.pi / 2, 0.0, -math.radians(cam["yaw_deg"]))
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def build_light(spec=None):
    """Blockout rounds 1-5: a neutral FORM light — bright world + one soft sun —
    whose only job was to let geometry read. Phase 2 replaces it with the
    measured story (trn002_light) the moment the spec carries a `light` block,
    so every blockout spec still renders exactly as it did.

    The form light is also the reason four blind critics counted 6-7 downlights
    in a 4-downlight room: a flat world washes bright pools that read as
    fixtures. Killing those is a named phase-2 ticket, and it is killed HERE."""
    if spec and spec.get("light"):
        import trn002_light as LIGHT
        LIGHT.build_world(spec)
        LIGHT.build_lights(spec)
        return
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 0.55
    sun = bpy.data.lights.new("SUN_TRN002", type="SUN")
    sun.energy = 2.0
    sun.angle = math.radians(8)
    ob = bpy.data.objects.new("SUN_TRN002", sun)
    ob.rotation_euler = (math.radians(55), 0.0, math.radians(-35))
    bpy.context.scene.collection.objects.link(ob)


def setup_render(spec, out_png, quick):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    W, H = spec["image"]["w"], spec["image"]["h"]
    samples = FULL_SAMPLES
    if quick:
        W, H, samples = W // 2, H // 2, 64
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    rn = spec.get("render") or {}
    for k, dflt in (("diffuse_bounces", 4), ("max_bounces", 12),
                    ("glossy_bounces", 4), ("sample_clamp_indirect", 10.0)):
        setattr(sc.cycles, k, type(dflt)(rn.get(k, dflt)))
    prefs = bpy.context.preferences.addons.get("cycles")
    device = "CPU"
    if prefs:
        cp = prefs.preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                cp.compute_device_type = kind
                cp.get_devices()
                for d in cp.devices:
                    d.use = True
                if any(d.use and d.type != "CPU" for d in cp.devices):
                    sc.cycles.device = "GPU"
                    device = kind
                    break
            except Exception:
                continue
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_png
    # FILM. Default stays Standard so every reproduction frame is unchanged,
    # but it is no longer a hardcoded literal — it is a declared, bracketable
    # setting, which is the whole complaint against the line it replaces.
    #
    # WHY THIS MATTERS MORE THAN IT LOOKS: TRN-001 measured this exact lever and
    # wrote the finding into trn001_light.py:273-280 — "ours clipped 2.15% under
    # Standard, which is a straight-line transform with no shoulder to hold a
    # highlight. AgX has one — this is a measured lever, not a preference" — and
    # defaulted that lane to AgX. TRN-002 opened four days later with `Standard`
    # typed in, no film hook, no comment, and the string appears in none of
    # gates 06-15. Rounds r23→r26 (four rounds, four gates) were then spent
    # closing a blown highlight tail by bracketing WATTAGE: clipped pixels
    # 2.804% → 0.731% → 0.093% → 0.124%, p99 1.0000 (clipped solid) → 0.7232.
    # That is the symptom the shoulder exists to remove, rediscovered one
    # project later at the price of four build+render cycles.
    #
    # It is NOT automatically correct to switch: the target is display-referred
    # and we do not know its transform, so AgX has to be measured against the
    # same ratios like anything else. The defect was never "wrong transform" —
    # it was an uncalibrated free variable at the last stage of every
    # measurement, set by a literal nobody bracketed.
    film = ((spec or {}).get("beauty") or {}).get("film") or {}
    vt = film.get("view_transform", "Standard")
    for cand in (vt, "Standard"):
        try:
            sc.view_settings.view_transform = cand
            break
        except TypeError:
            print(f"!! view_transform {cand!r} not available in this Blender")
    if film.get("look"):
        try:
            sc.view_settings.look = film["look"]
        except TypeError:
            print(f"!! look {film['look']!r} not available")
    sc.view_settings.exposure = float(film.get("exposure", 0.0))
    print(f"film view={sc.view_settings.view_transform} "
          f"look={sc.view_settings.look} exposure={sc.view_settings.exposure:+.3f}")
    print(f"cycles device={device} samples={samples} res={W}x{H} "
          f"diff_bounce={sc.cycles.diffuse_bounces}")  # keep: silent-CPU catch


def dump_projections(spec, cam_ob, path):
    from bpy_extras.object_utils import world_to_camera_view as w2cv
    import mathutils
    sc = bpy.context.scene
    W, H = spec["image"]["w"], spec["image"]["h"]
    cam = spec["camera"]
    measured = spec.get("landmarks_px", {})
    out, bad, errs = {}, [], []
    print("\nlandmark             pure(u,v)        w2cv(u,v)        vs measured px")
    for name, p in spec["landmarks_3d"].items():
        pure = G.project(cam, p, (W, H))
        co = w2cv(sc, cam_ob, mathutils.Vector((p[0] * MM, p[1] * MM, p[2] * MM)))
        blend = (co.x * W, (1.0 - co.y) * H)
        row = {"pure": pure, "blender": blend}
        d_pb = math.hypot(pure[0] - blend[0], pure[1] - blend[1]) if pure else 1e9
        if d_pb > 1.5:
            bad.append(f"{name}: pure {pure} vs blender {blend} ({d_pb:.2f}px)")
        msg = ""
        if name in measured and pure:
            mu, mv = measured[name]
            e = math.hypot(pure[0] - mu, pure[1] - mv)
            errs.append(e)
            row["err_px"] = round(e, 2)
            msg = f"err={e:6.2f}"
        out[name] = row
        print(f"  {name:18s} ({pure[0]:7.1f},{pure[1]:7.1f}) "
              f"({blend[0]:7.1f},{blend[1]:7.1f})  {msg}")
    if errs:
        errs.sort()
        print(f"\nmetric of record: n={len(errs)} mean={sum(errs)/len(errs):.2f}px "
              f"median={errs[len(errs)//2]:.2f}px max={max(errs):.2f}px @1080")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    if bad:
        raise SystemExit("PROJECTION MODEL DISAGREES WITH BLENDER:\n  " + "\n  ".join(bad))


def placement_gate(out_json):
    import placement_check as PC
    import placement_dump as PD
    bpy.context.view_layer.update()
    objs = PD.dump()
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"unit": "mm", "objects": objs}, f, indent=1, ensure_ascii=False)
    found = [f for f in PC.check(objs) if f["sev"] == "FAIL"]
    n_adv = len(PC.check(objs)) - len(found)
    print(f"PLACEMENT: {len(objs)} objects, {len(found)} FAIL, {n_adv} advisory")
    if found:
        for f in found:
            print(f"  !! {f['kind']} {f['object']}: {f['detail']}")
        raise SystemExit("PLACEMENT GATE FAILED (R9b)")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec_path = argv[0]
    # ABSOLUTE, ONCE, FOR EVERY WRITER. Blender resolves a drive-less relative
    # path against the DRIVE ROOT while Python resolves against the CWD — the
    # exact split that let TRN-001's id_mask write client pixels to C:\_private
    # outside the repo. One resolution here, all writers inherit it.
    out_png = os.path.abspath(argv[argv.index("--out") + 1])
    quick = "--quick" in argv
    spec = G.load_spec(spec_path)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials):
        for ob in list(coll):
            coll.remove(ob)

    # R10 RULE GATE, before a single vertex is made. It sits here rather than in
    # a checklist because the only rules this repo has ever actually kept are
    # the ones that are programs in a path someone already runs — the placement
    # gate below has never been skipped, while "write the triage" and "distil
    # the learning" drifted the moment nobody was watching. `--no-rule-gate`
    # exists for bisecting an old spec, and prints loudly that it was used.
    import rule_gate as RULES
    if "--no-rule-gate" in argv:
        # Was an unconditional bypass. A bypass whose only cost is typing the
        # flag is not a bypass, it is the default with extra steps — so it now
        # costs an env var AND writes a line into the lane's own record, where
        # the next gate has to look at it.
        if os.environ.get("TRN002_ALLOW_RULE_GATE_BYPASS") != "1":
            raise SystemExit(
                "--no-rule-gate requires TRN002_ALLOW_RULE_GATE_BYPASS=1. It "
                "exists for bisecting an OLD spec, not for getting past a gate "
                "that is telling you something.")
        print("!! RULE GATE BYPASSED by --no-rule-gate")
        with open(os.path.join(LANE_DIR, "rule-gate-bypasses.log"), "a",
                  encoding="utf-8") as f:
            f.write(f"{os.path.basename(spec_path)} -> {out_png}\n")
    else:
        # require_seen is ON: after the object-justification audit every mass
        # can point at itself in the reference, so the strict form is now the
        # cheap one. It is the only check that catches an invented object whose
        # derivation is impeccable — lamp_stem's prov ("rest_on nightstand top
        # 481, carries shade") was a perfectly well-formed contact for a thing
        # that is not in the room.
        # R7's half of this gate had NEVER executed: `check()` runs
        # audit_bundle only `if bundle_dir:` and this call site passed none, so
        # every render printed "all justified" while the triage rule was mute.
        # A mute is indistinguishable from compliance, which is why it survived
        # 27 rounds. Now the debt is resolved here and passed in.
        debt = RULES.bundle_debt(BUNDLE_ROOT, spec_path, WAIVERS)
        older = []
        for d in debt[:-1]:
            older += [f"[{os.path.basename(d)}] {s}"
                      for s in RULES.audit_bundle(d, LANE_DIR)]
        if older:
            print(f"\nRULE GATE: {len(older)} standing violation(s) in "
                  f"{len(debt) - 1} older bundle(s)")
            for s in older:
                print(f"  !! {s}")
        # `hard` is handed to enforce only when there is nothing else to add, so
        # enforce prints its own list and no violation is ever printed twice.
        # spec_path feeds the CONTINUITY diff (a mass that left the scene
        # asserts nothing, so only a spec-to-spec comparison can see it) and
        # LANE_DIR feeds the coverage manifest, which is derived rather than
        # passed so that no call site can leave that half mute the way this one
        # left R7 mute for 27 rounds.
        # render_dir feeds R1's full-frame count. It is passed rather than
        # derived inside the gate for the same reason `--out` is absolute here:
        # this module is the only place that knows where this lane's frames
        # land. Passing it is also what makes the cap bite — `check` treats a
        # missing render dir as a violation when a frame cap is declared,
        # because 0 frames would otherwise pass any cap and read as compliance.
        v = RULES.enforce(
            spec, bundle_dir=debt[-1] if debt else None,
            inbox_root=os.path.join(REPO, "knowledge", "_inbox"),
            require_seen=True, lane_dir=LANE_DIR, hard=not older,
            spec_path=spec_path,
            # BUNDLE_ROOT already ends in `renders/critique`, so joining
            # "renders" onto it named `renders/critique/renders`, which has
            # never existed. `count_full_frames` returned 0 for it and 0 passes
            # a cap of 55 — R1, the first rule the owner adopted, has been
            # counting nothing on the render path while the CLI (which resolves
            # this dir itself) reported 44. Measured both ways 2026-08-09.
            render_dir=os.path.dirname(BUNDLE_ROOT))
        if older or v:
            raise SystemExit("RULE GATE FAILED (R10 / R7 / charter)")

    # The seam between a pocket and the host face it fills. Checked HERE and not
    # only in the tests because the defect it catches was written straight into
    # the JSON with no generator behind it — `_mk_r29.py` emits the pocket but
    # never its `face`, so no maker script was ever in the path to be wrong.
    # A hand-editable field needs a check on the build path, not a check that
    # only runs when someone remembers to run the makers. It sits OUTSIDE the
    # `--no-rule-gate` branch on purpose: this one is not a judgement about the
    # round, it is whether two halves of a seam were authored from one number.
    seams = G.pocket_face_violations(spec)
    if seams:
        raise SystemExit("POCKET/HOST SEAM (r36):\n  " + "\n  ".join(seams))

    materials = None
    if "--materials" in argv:
        import trn002_materials as MAT
        materials = MAT.build_materials(palette_override=spec.get("materials"),
                                        fresnel_override=spec.get("fresnel"))
        print("materials ON\n" + MAT.palette_report())

    def mat_of(name):
        if materials is None:
            return None
        import trn002_materials as MAT
        return materials[MAT.material_for(name)]

    # C3-r14 item 5, accepted: "ขอบ...คมกริบเกินไป ... แม้วัตถุจะมีดีไซน์เหลี่ยม แต่ขอบจะมี
    # การลบมุมเล็กน้อยเสมอ เพื่อให้เกิดไฮไลท์ของแสงที่ขอบวัตถุ". A manufactured object has an
    # eased arris because it is cut, sanded and edge-banded; the highlight that
    # runs along it is a large part of why a real object reads as one and a
    # primitive does not. Every mass in this lane is a perfectly sharp box.
    #
    # Blender generates this (R8b: do not hand-write what the tool already does)
    # and a MODIFIER is headless-safe — it is not a geometry `bpy.ops`.
    #
    # SCOPE COMES FROM THE RULE'S OWN PREMISE, not from what looks better. The
    # premise is "a manufactured object has an eased edge". Plaster does not:
    # a wall/ceiling/floor junction is a sharp arris, and those arrises are the
    # features this lane MEASURES AGAINST — the room corner and the wardrobe
    # corner are confirmed at 0.5 px, and rounding them would move the very
    # lines the camera solve stands on. R9b's warning is the other half: a rule
    # that NAMES the objects it applies to will exempt the next one, so this
    # names the exempt CLASS and beveals everything else, including masses that
    # do not exist yet.
    ARCHITECTURE = {"back_wall", "left_wall", "right_wall", "ceil_main",
                    "floor", "floor_planks", "closet_back", "closet_floor"}

    def _ease(ob, name):
        if name in ARCHITECTURE or name.startswith(("ceil_", "door_wall")):
            return
        b = ob.modifiers.new("EASE", "BEVEL")
        # 1.5 mm — a cabinetmaker's arris ease. This lane's own rule is to
        # bracket an amplitude LOUD and then take ~70% of it, because trn001
        # once shipped a physically-honest bump that rendered as nothing. The
        # loud pass here was 5 mm and the R9b PLACEMENT GATE REFUSED IT: both
        # pillows came back FLOATING by 1.7 mm, because a bevel that size eats
        # the measured contact between two objects. So the bracket was closed by
        # a guard rather than by an opinion, which is the better outcome — and
        # it names a real constraint: an edge ease may never exceed the
        # tolerance of the contacts around it.
        b.width = 0.0015
        b.segments = 2
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(30)
        b.harden_normals = False
        # clamp is what keeps this safe on the 6 mm reveal strips: a 1.5 mm
        # bevel on a 6 mm member would eat a quarter of it, so the modifier
        # shrinks itself rather than deforming the part.
        b.use_clamp_overlap = True

    # SOFT FORMS — off unless the spec asks. `oct` masses (pillows, bolster,
    # the throw stand-ins) are built by oct_mesh(seg=6): 56 verts, 30 faces,
    # two 28-gon end caps, FLAT shaded, no subdivision. The 2026-07-30
    # ground-truth study measured pro pillows at 3,124-88,374 polys and named
    # SUBSURF on soft forms as a wire item; this lane never ran either, so
    # every arc in the frame renders as visible facets.
    #
    # R8b's corollary is the reason this is opt-in per mass and not global:
    # subdivision SMOOTHS WHAT EXISTS AND CANNOT ADD WHAT WAS NEVER THERE. On
    # trn001 it erased the deliberate ledges of a stepped base while changing
    # nothing visible on the smooth-shaded body. A probe proves reachability;
    # only a look proves value — so this ships as a bracket, not as a default.
    soft = ((spec.get("beauty") or {}).get("soft") or {})

    def _soften(ob, name, kind):
        cfg = soft.get(name) or soft.get(kind or "") or {}
        if not cfg:
            return
        if cfg.get("smooth"):
            for p in ob.data.polygons:
                p.use_smooth = True
        lv = int(cfg.get("subsurf", 0))
        if lv:
            # Appended AFTER the EASE bevel, which is the order we want and the
            # order `modifiers.new` already gives: bevel cuts the arris, then
            # subdivision rounds the result. (There is no `move_to_index` on
            # this collection in 5.1 — reordering is an operator, and geometry
            # operators are banned headless. The append order is the contract.)
            s = ob.modifiers.new("SOFT", "SUBSURF")
            s.levels = s.render_levels = lv

    built = {}
    cloth_queue = []
    for m in spec["masses"]:
        if m.get("kind") == "cloth_duvet":
            # cloth builds AFTER every rigid mass exists (its colliders are
            # looked up in `built`), and never enters _ease — a bevel modifier
            # on a cloth object would evaluate into the frozen drape.
            cloth_queue.append(m)
            continue
        if m.get("kind") == "herringbone":
            built[m["name"]] = _herringbone(
                m["name"], m["c"][2], m["s"][2], m["value"],
                mat=mat_of(m["name"]), **(m.get("lattice") or {}))
        elif m.get("kind") == "slats":
            built[m["name"]] = _slats(m["name"], m["c"], m["s"], m["value"],
                                      mat=mat_of(m["name"]),
                                      **(m.get("slat") or {}))
        elif m.get("kind") == "pocket":
            built[m["name"]] = _pocket(m["name"], m["value"],
                                       mat=mat_of(m["name"]),
                                       host_mat=mat_of(m["host"]),
                                       host_value=m.get("host_value"),
                                       **m["pocket"])
        elif m.get("kind") == "cone":
            built[m["name"]] = _cone(m["name"], m["c"], m["s"], m["value"],
                                     mat=mat_of(m["name"]),
                                     seg=int(m.get("seg", 24)))
        elif m.get("kind") == "oct":
            built[m["name"]] = _oct(m["name"], m["c"], m["s"], m.get("cut", 200),
                                    m["value"], axis=m.get("axis", "z"),
                                    tilt_deg=m.get("tilt_deg", 0.0),
                                    mat=mat_of(m["name"]),
                                    open_face=m.get("open_face"),
                                    seg=int(m.get("seg", 6)))
        else:
            built[m["name"]] = _box(m["name"], m["c"], m["s"], m["value"],
                                    mat=mat_of(m["name"]))
        _ease(built[m["name"]], m["name"])
        _soften(built[m["name"]], m["name"], m.get("kind"))
    # "parent": <mass> declares an assembly IN the scene — placement_check groups
    # by Blender hierarchy ("the scene's own declaration of what moves together"),
    # so a shade over its stem is judged as one lamp, not as a slab teetering on a
    # post. Meshes carry world coords with identity transforms, so no inverse
    # matrix is needed.
    for m in spec["masses"]:
        if m.get("parent"):
            built[m["name"]].parent = built[m["parent"]]
    for m in cloth_queue:
        built[m["name"]] = _cloth_duvet(m, built, mat_of(m["name"]))
    cam_ob = build_camera(spec["camera"], spec.get("beauty"))
    build_light(spec)
    setup_render(spec, out_png, quick)

    base = os.path.splitext(out_png)[0]
    bpy.context.view_layer.update()
    dump_projections(spec, cam_ob, base + ".projections.json")
    placement_gate(base + ".placement.json")

    bpy.ops.wm.save_as_mainfile(filepath=base + ".blend")
    bpy.ops.render.render(write_still=True)
    print(f"wrote {out_png}")

    # R11 — THE GATE OPENS THE PICTURE. Owner order 2026-08-09: "ผมขอบังคับให้ทุก
    # กลไก ทุกขั้นตอนต้องมองรูปจริง". Every other rung in this build runs BEFORE a
    # pixel exists, which is precisely why none of them could ever look at one:
    # measured that day, 0 of the 8 modules the gate calls opened an image, and 0
    # of the 21 instruments that do were called by any of them.
    #
    # It has to be HERE and not in the pre-render gate, and it FAILS THE BUILD
    # rather than printing a note, because the whole finding is that a gate made
    # of declarations goes green while the frame gets worse. Proven on a real
    # negative control before it shipped: run against trn002_mat_r32.png — a full
    # frame built with the invented 176 mm headboard — it fails with "the feature
    # this claim names is not in our frame" (1.8 L of contrast against the
    # target's 39.6), i.e. it would have caught at r32 the defect that in fact
    # survived to r38.
    #
    # A spec with no `pixel_claims` passes silently, and that is not a loophole
    # being left open: `pixel_check.unclaimed()` prints how many masses carry no
    # claim on every gate run, so the hole is a number in the render path rather
    # than a silence.
    # IT RUNS OUT OF PROCESS, and that is the layer law rather than a workaround:
    # Blender's bundled Python has no PIL (`ModuleNotFoundError` on the first
    # attempt), and the fix is NOT to teach the checker to read pixels through
    # `bpy.data.images` — that would drag a gate module into layer 2, which
    # pipeline/CLAUDE.md forbids for exactly this kind of code. `pixel_check` is
    # layer-1 rule code operating on layer-3 output, so it belongs in a plain
    # python process. The build spawns it and dies on its exit code.
    #
    # AND IT IS SPAWNED, NOT PRINTED. This repo has already shipped the other
    # version once ("the guard was declared mandatory and then printed as a
    # suggestion for a human to copy"). An interpreter that cannot be found is a
    # HARD STOP, not a note: a gate that cannot run must never read as a gate
    # that passed.
    import shutil
    import subprocess
    target = os.path.join(REPO, "_private", "benchmark", "reproduction",
                          "TRN-002", "target.jpg")
    if not os.path.isfile(target):
        raise SystemExit(f"R11: the reference {target} is not readable, so this "
                         f"run cannot compare the frame to anything. A gate that "
                         f"cannot look must not report that it looked.")
    py = next((p for p in (shutil.which("python3"), shutil.which("python"))
               if p), None)
    if py is None:
        raise SystemExit("R11: no plain python interpreter on PATH to run "
                         "pixel_check (Blender's has no PIL). Refusing to finish "
                         "a render whose only rung that opens the picture could "
                         "not be started.")
    r = subprocess.run([py, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "pixel_check.py"),
                        "--spec", os.path.abspath(spec_path),
                        "--render", out_png, "--target", target],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    for ln in (r.stdout or "").splitlines():
        print(f"PIXEL {ln}")
    # 2 = COULD NOT RUN (an R5 playblast is not the reference's size, and a
    # sub-pixel comparison at half resolution is a different measurement). It is
    # a distinct code from 0 on purpose: the line above says NOT RUN in the
    # render path, and only full fidelity was ever allowed to close a gate.
    #
    # P0f — THE MUTE THAT WAS HERE. This branch was a bare `pass`, for BOTH
    # kinds of run. The reasoning written above it is sound and the code never
    # implemented it: `quick` was in scope and never tested, so a FULL-FIDELITY
    # frame whose pixel rung could not run for any reason at all — an unreadable
    # claim, a size mismatch, a broken estimator — finished, printed, and closed
    # exactly like a frame that had passed the rung. That is R11's own sentence
    # ("could not look must never print like looked and it was fine") failing
    # inside R11's own implementation, three lines under a comment asserting the
    # opposite. On a full frame this is the same event as the missing target and
    # the missing interpreter above, and it gets the same answer: a hard stop.
    import rule_gate as _RG
    action, msg = _RG.pixel_exit_policy(r.returncode, quick)
    if action == "note":
        print("PIXEL -- " + msg)
    elif action == "stop":
        for ln in (r.stderr or "").splitlines()[-4:]:
            print(f"PIXEL !! {ln}")
        raise SystemExit(msg)


if __name__ == "__main__":
    main()
