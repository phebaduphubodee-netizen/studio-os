"""drape.py — REAL cloth, baked headless. LAYER 2 (Blender materializer).

WHY THIS EXISTS (2026-07-22, owner correction)
----------------------------------------------
Element 8 shipped 785 lines of hand-written cloth mathematics (`softgoods.py` +
its tests): golden-ratio crease sequences, multi-wavelength fold pitch, hem
wander, a sag term. It produced garments that read as "curved cards", a duvet
that stayed a box, and — most tellingly — a foot throw that was WRITTEN, TESTED,
CONTAINED and then DISABLED, with a comment in `build_room.py` stating:

    "a throw laid on a bed whose flank is ALSO compliant is a cloth-on-cloth
     interaction, and this vocabulary has no collision term"

The owner's reply was that the missing thing was never a vocabulary. It was
knowing Blender. He was right, and the probe settles it — every claim behind
that comment is false in this exact build (Blender 5.1.2, `-b`, factory startup):

    CLOTH modifier via data API .... OK          COLLISION via data API ... OK
    sim advances headless ......... YES          collision deflects ....... YES
    bake, 625 verts x 40 frames ... 0.48 s       determinism (2 runs) ..... 0.000000000 m
    SUBSURF n-gons ................ 0            freeze -> plain mesh ..... OK

The "collision term this vocabulary has no ..." is one line: `COLLISION`.

WHY THE LAYER LAW NEVER FORBADE THIS
------------------------------------
`pipeline/CLAUDE.md` bans `bpy.ops` FOR GEOMETRY (it dies `poll() failed` in
`--background`) and requires `bpy.data` + `from_pydata`. Modifiers are the DATA
API — `obj.modifiers.new(...)` — and the repo has used one since day one
(`build_room.py:292`, BEVEL). Nothing here touches `bpy.ops`. What actually
happened is that layer 1 (pure python, unit-testable under plain `python`) was so
comfortable that soft-goods GEOMETRY got written there too, and paid for its
testability by re-implementing physics badly. The correct split, restored here:

    layer 1 (pure)   decides WHERE cloth goes and WHAT MAY NOT BE VIOLATED
                     — rects, drop budgets, signed reveals, containment bounds
    layer 2 (this)   SHAPES it with the solver, then PROVES layer 1's bounds
                     held, in Blender, on the baked result

So the constraints stay testable under plain python; only the shaping moves.

DETERMINISM
-----------
Repo law is that a build is reproducible. Measured bit-exact across two bakes in
one process (drift 0.000000000 m). The solver is stepped explicitly here — never
via `bpy.ops.ptcache.bake`, which is both an op and cache-state dependent — and
every sheet is FROZEN to a plain mesh the moment its bake ends, so no simulation
state survives into the render and later bakes see a static collider.

FAIL-LOUD
---------
Two guards, both RAISE, because the studio's recurring wound is decided data that
silently stops being built:
  * `min_motion` — a sim that did not advance (bad collider, gravity off, zero
    frames) yields a FLAT SHEET that looks like a deliberate plane. It raises.
  * `bounds`     — the CAD invariant ("the plan-measured footprint never moves").
    Cloth is the first thing in this pipeline that can leave its own rect by
    swinging, so containment is asserted on the BAKED verts, not on the input.
"""

import bpy

import clothcheck
import softgoods as sg


class DrapeError(RuntimeError):
    """A drape that did not simulate, or left its measured footprint."""


def world_bbox(obj):
    """(xmin, ymin, zmin, xmax, ymax, zmax) of a built object, in world metres.

    Exists so a second drape can be sized against the FIRST one's settled result
    instead of against the nominal rect both were cut from. Where a simulated
    surface actually came to rest is not predictable from its cut — that is the
    whole reason it is being simulated — so anything laid on top of it must
    measure it. The throw's every containment failure came from being sized to the
    bed rect while physically hanging off whatever happened to be widest."""
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    if not pts:
        raise DrapeError(f"{obj.name}: no geometry to measure")
    return (min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts),
            max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))


def violations(bb, bounds=None, hem_min=None):
    """(bulge, hem_deficit, worst_axis) for a baked bbox — both in metres, 0 = clean.

    Split out from the raising guards so a caller can SEARCH against the same two
    constraints the guards enforce, rather than a caller's private idea of them."""
    bulge, axis = 0.0, ""
    if bounds:
        xn, yn, zn, xx, yx, zx = bounds
        for got, lo, hi, nm in ((bb[0], xn, xx, "x"), (bb[3], xn, xx, "x"),
                                (bb[1], yn, yx, "y"), (bb[4], yn, yx, "y"),
                                (bb[2], zn, zx, "z"), (bb[5], zn, zx, "z")):
            over = max(lo - got, got - hi)
            if over > bulge:
                bulge, axis = over, nm
    deficit = max(0.0, (hem_min - bb[2]) if hem_min is not None else 0.0)
    return bulge, deficit, axis


def search_bake(build, *, name, bounds=None, hem_min=None, top_z=None, slack=0.0,
                steps=6):
    """Bake `build(length_scale, slack)` repeatedly and return the FIRST result that
    satisfies every constraint; raise with the full history if none does.

    Cloth cannot be cut to a prediction. It stretches under its own weight, and the
    `slack` that makes it fold at all also makes it billow outward — so the two things
    that must hold (clear a signed reveal below, stay inside the plan-measured footprint
    outward) are pulled in opposite directions by the same two dials. Worse, it is not
    monotonic in either: shortening a cut by 17 mm moved a skirt FURTHER out, because a
    different cut lands on a different station count and the whole fold pattern re-forms.

    So this is a LADDER, not a solver: correct the length by the measured shortfall,
    halve the slack on a billow, and once the slack is spent shorten the lever instead.
    Every rung is a real bake and a real measurement. Nothing here is allowed to ship
    the least-bad attempt — both constraints are signed decisions, not preferences.

    Six hand-picked constants were tried across the coverlet and the throw before this
    existed, and every one of them satisfied one constraint by breaking the other.
    """
    sl, scale, history = slack, 1.0, []
    for k in range(steps):
        obj = build(scale, sl)
        bb = world_bbox(obj)
        bulge, deficit, axis = violations(bb, bounds, hem_min)
        history.append("len x%.3f slack %.2f%% -> hem %.3f (%s), edge %s"
                       % (scale, sl * 100, bb[2],
                          "clear" if not deficit else "%.0f mm LOW" % (deficit * 1000),
                          "clear" if not bulge else "%.0f mm proud on %s" % (bulge * 1000, axis)))
        if not bulge and not deficit:
            print("  drape: %s solved in %d bake(s) — %s" % (name, k + 1, history[-1]))
            return obj
        bpy.data.objects.remove(obj, do_unlink=True)
        if deficit and top_z is not None:
            hung = top_z - bb[2]
            if hung <= 1e-6:
                raise DrapeError(f"{name}: sheet did not hang at all (hem z={bb[2]:.3f})")
            scale *= (top_z - hem_min) / hung
        if bulge:
            sl *= 0.5           # the billow IS the slack; spend it before spending length
            if sl < 0.01:       # ...but a near-slackless edge that STILL sits proud is
                scale *= 0.92   # too long a lever, not too much fabric. Shorten it.
    raise DrapeError("%s: no cut satisfied every constraint in %d bakes:\n    %s\n"
                     "Raise the plinth, widen the inset, or accept less fabric slack — "
                     "do not widen the bbox." % (name, len(history), "\n    ".join(history)))


# Fabric presets — Blender's own cloth families, retuned for interior soft goods.
# tension/compression resist stretch; shear resists in-plane skew; bending is the
# one that decides whether cloth reads as LINEN (holds a crease, larger folds) or
# as SILK (collapses into many fine folds). Values are the modifier's units.
FABRIC = {
    #          mass  tension compress shear  bending  air
    "linen":  (0.30, 15.0,   15.0,    5.0,   1.2,     1.0),   # coverlets, throws
    "cotton": (0.30, 15.0,   15.0,    5.0,   0.5,     1.0),
    "wool":   (0.40, 20.0,   20.0,    8.0,   3.0,     1.0),   # heavier, fewer folds
    "knit":   (0.35, 12.0,   12.0,    4.0,   0.35,    1.0),   # a throw: heavy but LIMP
    "silk":   (0.15,  5.0,    5.0,    5.0,   0.05,    1.0),   # sheers, fine drape
    # A LOFTED DUVET, added for TRN-002 r21 (owner's route-c call). It is not a
    # sheet and the difference is COMPRESSION: linen at 15 pulls itself flat
    # against a mattress, and a quilted duvet - batting between two skins -
    # buckles at almost no load, which is why a made bed carries standing folds
    # that a bedsheet does not. Compression 1.0 lets it buckle; bending 2.6
    # (above wool) makes the buckles LARGE and standing rather than fine and
    # collapsed, which is the fold family the reference shows at ~75 mm.
    "duvet":  (0.30, 15.0,    1.0,    3.0,   2.6,     1.0),
}


def _collider(obj, thickness=0.004, friction=40.0, damping=0.6):
    """Make `obj` deflect cloth. Idempotent — a mattress collides for every sheet
    dropped on it, and adding a second COLLISION modifier would double its field."""
    for m in obj.modifiers:
        if m.type == 'COLLISION':
            return m
    m = obj.modifiers.new("drape_collide", 'COLLISION')
    s = m.settings
    s.thickness_outer = thickness
    s.thickness_inner = thickness
    s.cloth_friction = friction      # high: bedding does not slide off a mattress
    s.damping = damping
    return m


def _freeze(obj, solid_thickness, hem=None):
    """Evaluated cloth -> plain static mesh. Everything downstream (materials,
    the suite material router, glTF export, Cycles) then treats it as ordinary
    geometry, and no solver state can re-run at render time.

    SOLIDIFY rides along so a zero-thickness sheet gains a real edge — a bare
    simulated plane renders as an infinitely thin blade wherever the hem is seen
    against the light, which is its own CAD tell. Solidify on quads yields quads
    (the SketchUp n-gon law holds; asserted by the caller's face check).

    `hem` = (vertex_group_name, factor): the named group rides the solidify at
    factor x thickness while everything else keeps the plain thickness — a
    turned-under stitched hem IS two-to-three layers of cloth, so the cue is the
    physics, not a decal (bed_base welts precedent: cue derived from what
    exists). Solidify semantics: weight 1 gets full modifier thickness, weight 0
    gets thickness x thickness_vertex_group — so the modifier carries
    factor x base and the zero-weight factor carries 1/factor, which lands body
    verts exactly on the plain thickness. Fails LOUD if the API surface moved
    (a swallowed miss would be a hem that silently never thickened)."""
    if solid_thickness:
        sm = obj.modifiers.new("drape_solid", 'SOLIDIFY')
        if hem:
            gname, factor = hem
            if not hasattr(sm, "vertex_group") or \
                    not hasattr(sm, "thickness_vertex_group"):
                raise DrapeError(f"{obj.name}: Solidify has no vertex-group "
                                 f"thickness on this Blender — the hem cue "
                                 f"cannot run; do not freeze as if it did")
            sm.vertex_group = gname
            sm.thickness = solid_thickness * float(factor)
            sm.thickness_vertex_group = 1.0 / float(factor)
        else:
            sm.thickness = solid_thickness
        sm.offset = 0.0
        sm.use_quality_normals = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    baked = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    old = obj.data
    obj.data = baked
    obj.modifiers.clear()
    if old.users == 0:
        bpy.data.meshes.remove(old)
    for p in baked.polygons:
        p.use_smooth = True
    return baked


def sim_surface_of(name):
    """The hidden single-shell proxy a `sim_surface=True` bake left behind, or None.
    Colliding a LATER sheet against this — instead of against the frozen render mesh —
    is what makes cloth-on-cloth stacks stable: the render mesh is SOLIDIFIED (two
    shells), and a sheet that tunnels between them gets trapped and renders as
    mottled cloth-through-cloth patches whatever the collision distance (fx6/fx7/fx8,
    2026-07-28: graze at 0.004, shard-crumple at 0.012, still patched at 0.008)."""
    return bpy.data.objects.get(name + "__simsrf")


def drop_sim_surfaces(*names):
    """Delete the hidden proxies once every sheet that needed them has baked — they
    must never reach the render or an export."""
    for n in names:
        p = sim_surface_of(n)
        if p is not None:
            bpy.data.objects.remove(p, do_unlink=True)


def bake_sheet(name, verts, faces, colliders, *, frames=55, fabric="linen",
               bounds=None, mat=None, pin=(), thickness=0.006, self_collide=True,
               quality=8, collide_dist=0.004, min_motion=0.010, tol=1e-4,
               hem_min=None, slack=0.0, slack_verts=None, sim_surface=False,
               shred_guard=False, collision_quality=4, bend_scale=1.0,
               self_friction=None, bend_verts=None, bend_floor=0.15,
               sew_edges=None, sewing_force=15.0,
               hem_verts=None, hem_factor=2.0, bending_model=None,
               hem_bend=None, hem_smooth=None):
    """Simulate a cloth sheet falling onto `colliders`; return the frozen object.

    verts/faces  a QUAD grid from layer 1 (`softgoods.flat_sheet`) — the solver
                 preserves topology, so the repo's no-n-gon law is decided here.
    colliders    Blender objects already in the scene. Each gets a COLLISION
                 modifier. Pass a previously-baked sheet to get CLOTH ON CLOTH.
    pin          vertex indices held in place (an edge tucked under a mattress).
    bounds       (xmin, ymin, zmin, xmax, ymax, zmax) in WORLD space. The baked
                 result is asserted against it — this is the CAD invariant, and
                 it is checked AFTER the physics, which is the only moment it
                 can actually be known.
    """
    if not colliders and not pin:
        # a PINNED sheet is supported by its pins (a garment on its hanger zone,
        # round 5) — only cloth with neither pins nor surfaces would fall forever
        raise DrapeError(f"{name}: cloth with no collider AND no pins would fall "
                         f"through the world — pass surfaces or a pin group")
    me = bpy.data.meshes.new(name)
    # sew_edges are LOOSE edges (no face) — Blender's cloth solver treats a
    # faceless edge as a SEWING SPRING when use_sewing_springs is on. They are
    # feedstock only: loose edges do not render and Solidify ignores them.
    me.from_pydata(list(verts), list(sew_edges or []), list(faces))
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)

    before = [v.co.copy() for v in me.vertices]

    md = obj.modifiers.new("drape", 'CLOTH')
    s = md.settings
    mass, ten, com, shr, ben, air = FABRIC[fabric]
    s.quality = quality
    s.mass = mass
    s.tension_stiffness = ten
    s.compression_stiffness = com
    s.shear_stiffness = shr
    s.bending_stiffness = ben * bend_scale     # ladders may stiffen a wad-prone piece
    s.air_damping = air
    if bending_model:
        # DR blender-cloth-corner-drape rank 1, consumed PER-CALL only (p2r22):
        # the ANGULAR default resists double curvature at ANY stiffness, so a
        # loose sheet ends as one smooth curve — the exact critic read on the
        # throw/coverlet three rounds running. LINEAR lets a plane buckle in two
        # directions and form secondary folds. Global consumption was refused
        # twice in this file's own comments (it would soften the duvet's
        # standing-fold preset), which is why this is an opt-in parameter and
        # never a default. Fails LOUD on an unknown value (API enum).
        s.bending_model = bending_model
    # LOCAL bending relief — DR blender-cloth-corner-drape rank 3 (the half whose
    # slot is still free: vertex_group_shrink is spent on slack, the BENDING group
    # is not). A standing corner ear is double curvature refused: the ANGULAR
    # model resists bending in two directions at once, so the flank tip holds its
    # crease in mid-air instead of falling. Dropping stiffness GLOBALLY (DR rank
    # 1, LINEAR) would also soften the large standing folds the duvet preset
    # exists to buy — so the relief is painted: weight 1 (body) = the preset
    # stiffness via bending_stiffness_max, weight 0 (corner tip) = bend_floor of
    # it. Blender semantics: with vertex_group_bending set, weight lerps base ->
    # max, so the BASE carries the floor and the MAX carries the preset. Pieces
    # that do not pass bend_verts keep the scalar path byte-identical.
    # Named failure mode (DR): corner shard collapse if the floor is too low for
    # the vertex mass — judged by LOOK on the quick rung before any full frame.
    # SEWING DART (P2r-1 mechanism 3, p2r13 — DR rank 4 "solver corner
    # constraint", dr-cloth-corner-drape-2026-08-11: use_sewing_springs +
    # sewing_force_max 10-25; dart cuts come from softgoods.corner_dart).
    # Fails LOUD if the API surface moved — a swallowed miss here would be a
    # mechanism that silently never ran (the --factory-startup default-cube
    # family of lie).
    if sew_edges:
        if not hasattr(s, "use_sewing_springs") or \
                not hasattr(s, "sewing_force_max"):
            raise DrapeError(f"{name}: cloth API has no sewing springs on this "
                             f"Blender — the dart mechanism cannot run; do not "
                             f"bake as if it did")
        s.use_sewing_springs = True
        s.sewing_force_max = float(sewing_force)
    # p2r25 — HEM BENDING (the sim half of the sewn-hem cue; the solidify half
    # below is render-only and "the sim never sees it" by its own comment).
    # WHY: the throw's free hem buckles at CELL wavelength under LINEAR bending
    # (p2r24 measured the sawtooth: autocorr 0.591 -> 0.434 after the slack
    # field — reduced, still periodic; the tooth pitch IS the cell). A real
    # throw is hemmed: a turned-under hem is 2-3 layers, and plate bending
    # stiffness scales with t^3, so the boundary is ~8-27x stiffer than the
    # body — it physically cannot buckle at cell scale. Painted through the
    # ONE bending group Blender gives us: base carries 0, max carries
    # factor x preset, body weight 1/factor lands exactly on the preset, hem
    # weight 1.0 carries the doubled cloth. Refuses to share the slot with
    # bend_verts (one group, two owners = a silent half-mechanism).
    if hem_bend:
        if bend_verts:
            raise DrapeError(f"{name}: hem_bend and bend_verts both paint the "
                             f"one bending vertex group — a piece gets corner "
                             f"relief or a stiff hem, not both silently")
        hverts, hfac = hem_bend
        if hfac <= 1.0:
            raise DrapeError(f"{name}: hem_bend factor {hfac} <= 1 — a hem "
                             f"softer than the body is not a sewn hem")
        if not hverts:
            raise DrapeError(f"{name}: hem_bend with no hem verts would be a "
                             f"mechanism that silently never ran")
        vgh = obj.vertex_groups.new(name="drape_hembend")
        vgh.add(list(range(len(me.vertices))), 1.0 / float(hfac), 'REPLACE')
        vgh.add(list(hverts), 1.0, 'REPLACE')
        s.vertex_group_bending = vgh.name
        s.bending_stiffness_max = ben * bend_scale * float(hfac)
        s.bending_stiffness = 0.0
    if bend_verts:
        vgb = obj.vertex_groups.new(name="drape_bend")
        vgb.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
        if isinstance(bend_verts, dict):
            by_w = {}
            for i, w in bend_verts.items():
                by_w.setdefault(float(w), []).append(i)
            for w, idxs in sorted(by_w.items()):
                vgb.add(idxs, w, 'REPLACE')
        else:
            vgb.add(list(bend_verts), 0.0, 'REPLACE')
        s.vertex_group_bending = vgb.name
        s.bending_stiffness_max = ben * bend_scale
        s.bending_stiffness = ben * bend_scale * float(bend_floor)
    # SLACK — the single thing that separates simulated cloth from a simulated PANEL.
    # A sheet cut to exactly fit its bed hangs perfectly flat: physically correct, and
    # still a box. That was the first three bakes here, and it is the same wrong answer
    # the hand-written vocabulary gave, arrived at by a better road. Real bedding always
    # carries more material than the space it covers; a negative shrink factor grows the
    # solver's rest lengths so the excess has to buckle, and where it buckles is solved.
    #
    # `slack_verts` spends it WHERE IT IS SAFE. Slack folds cloth and it also billows it
    # outward, and containment is decided almost entirely at the hanging edge — so a
    # search that trades slack for containment strips the folds off the whole sheet to
    # buy a few millimetres at one hem. The throw lost 0.06 -> 0.0075 that way and went
    # back to being a flat plate. Naming the region lets the part lying ON the bed carry
    # the fabric it should while the falling part stays taut enough to stay inside.
    # `slack_verts` may be a list (weight 1.0 everywhere named) or a {index: weight}
    # dict. The dict exists for LOOK round-2 #2: the throw's FALL carried weight 0 =
    # dead taut, and a taut cantilever is a fold-less slab with a level hem — the
    # literal e8 defect, rebuilt by the very mechanism that fixed containment. A
    # PARTIAL weight on the fall buys it enough excess to buckle into vertical folds
    # (constrained at the fold-over line, so excess width MUST wave) while still
    # spending most of the slack where containment is cheap, on the bed.
    if slack_verts:
        vg = obj.vertex_groups.new(name="drape_slack")
        if isinstance(slack_verts, dict):
            by_w = {}
            for i, w in slack_verts.items():
                by_w.setdefault(float(w), []).append(i)
            for w, idxs in sorted(by_w.items()):
                vg.add(idxs, w, 'REPLACE')
        else:
            vg.add(list(slack_verts), 1.0, 'REPLACE')
        s.vertex_group_shrink = vg.name
        s.shrink_min = 0.0                  # weight 0: taut
        s.shrink_max = -abs(slack)          # weight 1: full slack
    else:
        s.shrink_min = -abs(slack)
    if pin:
        vg = obj.vertex_groups.new(name="drape_pin")
        vg.add(list(pin), 1.0, 'REPLACE')
        s.vertex_group_mass = vg.name
        s.pin_stiffness = 5.0
    # HEM/SEAM CUE (P2r-1 residual "no hem/seam cue on sewn goods"; r18 C2 #1 /
    # C3 #1 filed the missing cue from both sides). The group is created BEFORE
    # the bake but consumed only by _freeze's solidify AFTER it — thickness is
    # not a solver input, so the sim is byte-identical with or without it. The
    # indices are the CALLER's (softgoods.boundary_verts on the post-dart
    # faces); computing them here from pre-dart topology would be the exact
    # index-shift trap corner_dart documents.
    hem = None
    if hem_verts:
        vgh = obj.vertex_groups.new(name="drape_hem")
        vgh.add(list(hem_verts), 1.0, 'REPLACE')
        hem = (vgh.name, float(hem_factor))
    c = md.collision_settings
    c.collision_quality = collision_quality
    c.distance_min = collide_dist
    c.use_self_collision = self_collide
    c.self_distance_min = max(0.002, thickness * 0.5)
    # p3r2 (DR blender-cloth-corner-drape, notebook ae3dd665 — REFERENCE tier,
    # staged in knowledge/_inbox/): folds that have gathered SLIDE APART again
    # under the default self-friction (5.0), which is half of why a settled
    # corner re-opens by the last frame. Callers that fight the held-open
    # corner raise it toward the DR's linen band (~12); None = Blender default,
    # so every lane that does not opt in is byte-identical.
    if self_friction is not None:
        c.self_friction = float(self_friction)

    for ob in colliders:
        _collider(ob, thickness=collide_dist)

    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()

    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    tmp = ev.to_mesh()
    after = [v.co.copy() for v in tmp.vertices]
    ev.to_mesh_clear()

    # GUARD 1 — did the solver actually run? A frozen sheet is a flat plane, and a
    # flat plane is exactly what element 8 shipped by hand; it must never pass silently.
    moved = max((a - b).length for a, b in zip(after, before)) if after else 0.0
    if moved < min_motion:
        raise DrapeError(
            f"{name}: cloth never moved ({moved * 1000:.1f} mm < {min_motion * 1000:.0f} mm). "
            f"The sheet would render as a rigid plane. Check gravity, frames={frames}, "
            f"and that the colliders are below it.")

    # GUARD 2 — the SHRED DETECTOR (round-5 gate, owner order "ก": instrument
    # before any more sim spend). A wad or a shred passes bbox/hem/min-motion —
    # only the normal field says it. `shred_guard`: False = off (bed cloths keep
    # their own LOOK-verified recipes), "report" = print the profile for
    # calibration, True = enforce clothcheck's published thresholds.
    if shred_guard:
        # the solver preserves topology, so the INPUT faces index the settled verts
        _bad, _prof, _msg = clothcheck.shredded([tuple(a) for a in after], list(faces))
        if shred_guard == "report":
            print(f"  shred-report {name}: {_msg}")
        elif _bad:
            raise DrapeError(f"{name}: SHREDDED/WADDED — {_msg}")

    if sim_surface:
        # capture the settled SINGLE-SHELL surface before solidify, as a hidden
        # collision proxy for the next sheet in the stack (see sim_surface_of).
        # Idempotent per attempt: a search ladder re-bakes under the same name.
        stale = bpy.data.objects.get(name + "__simsrf")
        if stale is not None:
            bpy.data.objects.remove(stale, do_unlink=True)
        dgp = bpy.context.evaluated_depsgraph_get()
        mep = bpy.data.meshes.new_from_object(obj.evaluated_get(dgp), depsgraph=dgp)
        prx = bpy.data.objects.new(name + "__simsrf", mep)
        bpy.context.collection.objects.link(prx)
        prx.hide_render = True
        prx["ph_model"] = True                    # no material pass, no bevel pass

    # p2r26 — HEM-SCOPED SMOOTH (DR dr-cloth-hem-serration-2026-08-12 lever 4):
    # damp the residual high-frequency serration on the hem ring AFTER the
    # physics and BEFORE the solidify — the DR's prescribed stack order
    # (Cloth -> Smooth -> Solidify/Subdiv). Scoped by vertex group so the
    # primary aperiodic folds in the body are untouched; post-sim, so the
    # solver stays the only wrinkle AUTHOR and this only removes what the
    # discretisation invented. None = byte-identical.
    if hem_smooth:
        _sv, _sf, _si = hem_smooth
        if not _sv:
            raise DrapeError(f"{name}: hem_smooth with no hem verts would be "
                             f"a mechanism that silently never ran")
        vgs = obj.vertex_groups.new(name="drape_hemsmooth")
        vgs.add(list(_sv), 1.0, 'REPLACE')
        smm = obj.modifiers.new("drape_smooth", 'SMOOTH')
        if not hasattr(smm, "vertex_group") or not hasattr(smm, "iterations"):
            raise DrapeError(f"{name}: Smooth modifier API surface moved — "
                             f"the hem de-serration cannot run; do not freeze "
                             f"as if it did")
        smm.vertex_group = vgs.name
        smm.factor = float(_sf)
        smm.iterations = int(_si)

    _freeze(obj, thickness, hem=hem)
    sc.frame_set(1)          # the render must not inherit the bake's frame

    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    bx = (min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts),
          max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    print("  drape: %s %d verts x %d frames, fell %.0f mm, bbox "
          "x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]"
          % (name, len(before), frames, moved * 1000, bx[0], bx[3], bx[1], bx[4], bx[2], bx[5]))

    # GUARD 2 — the CAD invariant, on the BAKED result.
    if bounds:
        xn, yn, zn, xx, yx, zx = bounds
        worst, axis = 0.0, ""
        for p in pts:
            for got, lo, hi, nm in ((p.x, xn, xx, "x"), (p.y, yn, yx, "y"), (p.z, zn, zx, "z")):
                over = max(lo - got, got - hi)
                if over > worst:
                    worst, axis = over, nm
        if worst > tol:
            raise DrapeError(
                f"{name}: baked cloth leaves its measured footprint by "
                f"{worst * 1000:.1f} mm on {axis}. baked x[{bx[0]:.3f} {bx[3]:.3f}] "
                f"y[{bx[1]:.3f} {bx[4]:.3f}] z[{bx[2]:.3f} {bx[5]:.3f}] vs allowed "
                f"x[{xn:.3f} {xx:.3f}] y[{yn:.3f} {yx:.3f}] z[{zn:.3f} {zx:.3f}]. "
                f"The plan-measured footprint never moves — shrink the sheet or raise its "
                f"hem, do not widen the bbox.")

    # GUARD 3 — a SIGNED reveal upstream is not a soft target. Element 3 signed a
    # recessed-plinth shadow gap; a coverlet whose hem falls past the plinth top
    # DELETES it, and the deletion is invisible in the story bits (the drape is still
    # "there"). Simulated cloth stretches under its own weight, so the hem cannot be
    # predicted from the cut length — it is measured here and must clear the line.
    if hem_min is not None and bx[2] < hem_min - tol:
        raise DrapeError(
            f"{name}: hem settled at z={bx[2]:.3f}, {(hem_min - bx[2]) * 1000:.0f} mm below "
            f"the reveal line z={hem_min:.3f} — it would bury a signed shadow gap. "
            f"Shorten the cut (cloth stretches, so cut length != drop).")

    ngons = sum(1 for p in obj.data.polygons if len(p.vertices) > 4)
    if ngons:
        raise DrapeError(f"{name}: {ngons} n-gon(s) — a SketchUp recipient sees these")
    return obj


def bake_bed_cover(name, *, rect, top_z, hang_to, colliders, mat, head, fabric="linen",
                   cell=0.028, frames=55, bounds=None, thickness=0.006, slack=0.05,
                   sim_surface=False, salt=0, quality=8, collision_quality=4,
                   self_friction=None, corner_darts=False, sewing_force=15.0,
                   hem_factor=None, bending_model=None, slack_waves=None):
    """A coverlet: a sheet lying on the mattress that OVERHANGS three sides and
    falls under gravity — the fold at the mattress edge is solved, not authored.

    rect     (x0, y0, dx, dy) of the surface it lies on (the mattress).
    hang_to  world z the hem should reach. The overhang is DERIVED from it, so a
             signed plinth reveal upstream survives by construction.
    head     "x-", "x+", "y-", "y+" — the side against the wall, which gets NO
             overhang (a coverlet does not drape down a headboard).
    """
    x0, y0, dx, dy = rect
    drop = top_z - hang_to
    if drop <= 0:
        raise DrapeError(f"{name}: hem ({hang_to:.3f}) is at or above the surface "
                         f"it hangs from ({top_z:.3f}) — nothing to drape")
    ax, sgn = head[0], head[1]

    def attempt(over, sl):
        ox0 = x0 - (0.0 if (ax == "x" and sgn == "-") else over)
        ox1 = x0 + dx + (0.0 if (ax == "x" and sgn == "+") else over)
        oy0 = y0 - (0.0 if (ax == "y" and sgn == "-") else over)
        oy1 = y0 + dy + (0.0 if (ax == "y" and sgn == "+") else over)
        # THE ROUNDED CORNER — wherever two overhangs meet, the corner is cut to a
        # radius about the mattress corner rather than squared or mitred, so the drape
        # turns it as one continuous edge with nothing free to splay (softgoods.flat_sheet
        # carries the full record of the two corners tried before this one). Derived from
        # the overhangs themselves, so a bed with the head on any side rounds exactly the
        # corners it actually has — the head side has no overhang, hence no corner.
        mit = []
        for cx0, cx1, ix in ((ox0, x0, x0), (x0 + dx, ox1, x0 + dx)):
            for cy0, cy1, iy in ((oy0, y0, y0), (y0 + dy, oy1, y0 + dy)):
                if cx1 - cx0 > 1e-6 and cy1 - cy0 > 1e-6:
                    mit.append((cx0, cy0, cx1, cy1, ix, iy))
        # COVERLET_MITRE_KEEP (0.45), not the 0.6 default: the tangent boundary
        # (_mitre_radius) RISES to full overhang beside each strip, which is net cloth
        # the constant-radius cut never kept — and that extra corner cloth, at 0.6,
        # cowled past the plan line and made the search ladder iron the whole sheet to
        # buy the corner back (slack 2.5%→0.62%, hem 62 mm short, and the throw
        # stacked outboard could no longer fit at ANY slack). A deeper dip pays for
        # the tangent rise: total corner cloth lands slightly UNDER the old mitre's,
        # the ladder solves like before, and the hem still turns the corner as one
        # continuous curve. The value lives in softgoods so pure tests pin it.
        verts, faces = sg.flat_sheet(ox0, oy0, ox1 - ox0, oy1 - oy0,
                                     top_z + 0.004, cell=cell, mitre=mit,
                                     mitre_keep=sg.COVERLET_MITRE_KEEP,
                                     # skirt-only per-corner bias (lane B2): the lying
                                     # rect stays exact, so the pin band + reveal
                                     # arithmetic below are untouched
                                     salt=salt, salt_rect=(x0, y0, x0 + dx, y0 + dy))
        # SEWING DART on the ROUND-CUT corners (P2r-1, the coverlet half — r18
        # C2 #1: the corner cascades read as balloons, "ไม่มีรอยหักแม้แต่รอยเดียว";
        # DR rank 4, sewing force in the DR's 10-25 band, same mechanism the
        # duvet's square corners paid for at p2r13. DR of record:
        # knowledge/_inbox/dr-cloth-corner-drape-2026-08-11.md, raw turn
        # knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json — this call
        # consumes the distillation's rank-4 row, the second of its two
        # recorded NEXT mechanisms). Sites are DERIVED from the mitre's own
        # geometry — anchor at
        # the arc's diagonal dip, length sized so the apex lands on the
        # mattress corner, so the seam closes only HANGING cloth into a cone
        # (softgoods.corner_dart_sites). Cut BEFORE the pin band is computed:
        # corner_dart remaps vertex indices, the trap its `sew` param documents.
        # A sub-resolution site (ladder shrank the overhang) prints its skip —
        # never a silent no-op.
        _sew = []
        if corner_darts:
            _sites, _skips = sg.corner_dart_sites(mit, sg.COVERLET_MITRE_KEEP,
                                                  cell)
            for _msg in _skips:
                print("  drape: %s %s" % (name, _msg))
            for _dip, _dlen in _sites:
                verts, faces, _sew = sg.corner_dart(verts, faces, _dip, _dlen,
                                                    sew=_sew)
        # HEM CUE — the free boundary of the post-dart sheet (every single-face
        # edge, dart banks included, so the sewn seam inherits the doubled
        # read). Consumed by _freeze's solidify only; the sim never sees it.
        _hem = sorted(sg.boundary_verts(faces)) if hem_factor else None
        # Pin the band trapped under the pillows at the headboard — and ONLY the part
        # of it lying ON the mattress, never the full grid row (softgoods.verts_in_rect).
        band = min(0.12, dx * 0.2 if ax == "x" else dy * 0.2)
        if ax == "x":
            px0 = (x0 + dx - band) if sgn == "+" else x0
            pin = sg.verts_in_rect(verts, px0, y0, px0 + band, y0 + dy)
        else:
            py0 = (y0 + dy - band) if sgn == "+" else y0
            pin = sg.verts_in_rect(verts, x0, py0, x0 + dx, py0 + band)
        if not pin:
            raise DrapeError(f"{name}: pin band is empty — the sheet would creep off the bed")
        # p2r24 — DE-PERIODISED SLACK (C2 + C3 at r23, independently: the
        # skirt's hem waves read as "a deliberate sine"). Uniform slack on a
        # uniform grid buckles at ONE wavelength; softgoods.slack_field
        # modulates the rest-length excess at three incommensurate envelope
        # wavelengths, so where the solver spends the fullness stops being
        # periodic. Computed on the POST-DART verts (the dart remaps indices —
        # the same trap corner_dart's `sew` param documents). Weights cap at
        # 1.0 = the scalar path's own value, the ladder still owns the total,
        # and None = the exact prior sheet, byte-identical.
        _sw = None
        if slack_waves:
            _f = sg.slack_field(verts, salt=salt + 17, depth=slack_waves)
            _sw = {i: min(1.0, m) for i, m in enumerate(_f)}
        # No bounds/hem_min here: search_bake owns those constraints and needs the bake
        # to RETURN so it can measure and re-cut. bake_sheet's own guards still cover the
        # things a search cannot fix — a sim that never advanced, and n-gons.
        return bake_sheet(name, verts, faces, colliders, frames=frames, fabric=fabric,
                          mat=mat, pin=pin, thickness=thickness, slack=sl,
                          slack_verts=_sw,
                          sim_surface=sim_surface, quality=quality,
                          collision_quality=collision_quality,
                          self_friction=self_friction,
                          sew_edges=_sew or None, sewing_force=sewing_force,
                          hem_verts=_hem, hem_factor=hem_factor or 2.0,
                          bending_model=bending_model)

    # The ladder that solves the cut lives in search_bake — the throw needs the very
    # same one, and a second copy of it would be the next thing to drift.
    return search_bake(lambda scale, sl: attempt((drop - 0.03) * scale, sl),
                       name=name, bounds=bounds, hem_min=hang_to, top_z=top_z,
                       slack=slack)
