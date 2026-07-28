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


def _freeze(obj, solid_thickness):
    """Evaluated cloth -> plain static mesh. Everything downstream (materials,
    the suite material router, glTF export, Cycles) then treats it as ordinary
    geometry, and no solver state can re-run at render time.

    SOLIDIFY rides along so a zero-thickness sheet gains a real edge — a bare
    simulated plane renders as an infinitely thin blade wherever the hem is seen
    against the light, which is its own CAD tell. Solidify on quads yields quads
    (the SketchUp n-gon law holds; asserted by the caller's face check)."""
    if solid_thickness:
        sm = obj.modifiers.new("drape_solid", 'SOLIDIFY')
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
               hem_min=None, slack=0.0, slack_verts=None, sim_surface=False):
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
    if not colliders:
        raise DrapeError(f"{name}: cloth with no collider would fall through the "
                         f"world — pass the surfaces it must land on")
    me = bpy.data.meshes.new(name)
    me.from_pydata(list(verts), [], list(faces))
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
    s.bending_stiffness = ben
    s.air_damping = air
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
    c = md.collision_settings
    c.collision_quality = 4
    c.distance_min = collide_dist
    c.use_self_collision = self_collide
    c.self_distance_min = max(0.002, thickness * 0.5)

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

    _freeze(obj, thickness)
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
                   sim_surface=False):
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
                                     mitre_keep=sg.COVERLET_MITRE_KEEP)
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
        # No bounds/hem_min here: search_bake owns those constraints and needs the bake
        # to RETURN so it can measure and re-cut. bake_sheet's own guards still cover the
        # things a search cannot fix — a sim that never advanced, and n-gons.
        return bake_sheet(name, verts, faces, colliders, frames=frames, fabric=fabric,
                          mat=mat, pin=pin, thickness=thickness, slack=sl,
                          sim_surface=sim_surface)

    # The ladder that solves the cut lives in search_bake — the throw needs the very
    # same one, and a second copy of it would be the next thing to drift.
    return search_bake(lambda scale, sl: attempt((drop - 0.03) * scale, sl),
                       name=name, bounds=bounds, hem_min=hang_to, top_z=top_z,
                       slack=slack)
