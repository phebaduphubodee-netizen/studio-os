"""Tests for softgoods.py — the ELEMENT 8 compliant-surface vocabulary.

These pin the PHYSICS, not the numbers. The module exists because three previous
"make it softer" passes shipped bevelled boxes, so the tests must be able to tell drape
from a rounded slab: crease amplitude must GROW downward, hems must NOT be level, fold
pitch must NOT be uniform, and the same spec must build the same room every run.

Pure python — no bpy, no Blender.
"""
import math

import pytest

import softgoods as sg


# --------------------------------------------------------------------------- dev()

def test_dev_is_deterministic_across_calls():
    """A render that differs run-to-run cannot be a structural control for the beauty
    pass. Irregularity here is derived, never random."""
    a = [sg.dev(i, 0.02) for i in range(40)]
    b = [sg.dev(i, 0.02) for i in range(40)]
    assert a == b


def test_dev_respects_its_bound():
    for i in range(200):
        assert abs(sg.dev(i, 0.017)) <= 0.017 + 1e-12


def test_dev_streams_are_independent():
    """A piece's x-deviation must not correlate with its z-deviation, or a rail of
    garments steps diagonally like a staircase."""
    xs = [sg.dev(i, 1.0, salt=0) for i in range(60)]
    zs = [sg.dev(i, 1.0, salt=1) for i in range(60)]
    mx, mz = sum(xs) / len(xs), sum(zs) / len(zs)
    cov = sum((x - mx) * (z - mz) for x, z in zip(xs, zs)) / len(xs)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / len(xs))
    szz = math.sqrt(sum((z - mz) ** 2 for z in zs) / len(zs))
    assert abs(cov / (sx * szz)) < 0.35

# Every generator this module still ships. `drape_skirt` and `throw` were removed on
# 2026-07-22: their job is done by Blender's cloth solver (pipeline/scripts/drape.py) and
# leaving them here would have left ~130 lines of superseded physics under 22 green tests
# that certify what no render uses — the studio's own prose-vs-build wound, in test form.
ALL_MESHES = [
    ("garment", lambda: sg.garment(0.46, 0.95)),
    ("hanger", lambda: sg.hanger(0.40)),
    ("cushion", lambda: sg.cushion(0.70, 0.70, 0.19, dent=0.02)),
    ("folded_knit", lambda: sg.folded_knit(0.17, 0.25, 0.042, salt=3)),
]


@pytest.mark.parametrize("name,make", ALL_MESHES, ids=[n for n, _ in ALL_MESHES])
def test_mesh_is_wellformed(name, make):
    verts, faces = make()
    assert verts and faces
    n = len(verts)
    for f in faces:
        assert len(f) == 4, f"{name}: n-gon/tri {f} — the export law wants quads"
        assert len(set(f)) == 4, f"{name}: degenerate face {f}"
        for idx in f:
            assert 0 <= idx < n, f"{name}: face index {idx} out of range"


@pytest.mark.parametrize("name,make", ALL_MESHES, ids=[n for n, _ in ALL_MESHES])
def test_mesh_is_deterministic(name, make):
    assert make()[0] == make()[0]


@pytest.mark.parametrize("name,make", ALL_MESHES, ids=[n for n, _ in ALL_MESHES])
def test_mesh_has_no_nan(name, make):
    for v in make()[0]:
        for c in v:
            assert c == c and abs(c) < 1e4


# ------------------------------------------------------------------- drape physics

def _skirt_rings(verts, nv):
    """Regroup a skirt's flat vert list into per-station rings of (nv+1) samples."""
    return [verts[i:i + nv + 1] for i in range(0, len(verts), nv + 1)]


def test_garment_shoulder_is_the_widest_point():
    """INVERTED at round 4 (owner: "เสื้อผ้าในตู้ ดูไม่เหมือนเสื้อผ้าจริง"): the old pin
    demanded a narrow top opening to a fuller body — which is the silhouette of a
    GARMENT BAG. A real hanging piece is widest across the hanger tips and the body
    falls slightly narrower below."""
    nu, nv = 11, 7
    for salt in range(6):
        verts, _ = sg.garment(0.46, 0.95, nu=nu, nv=nv, sway=0.0, salt=salt)
        rings = [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(nv + 1)]
        widths = [max(v[0] for v in r) - min(v[0] for v in r) for r in rings]
        assert widths[0] == max(widths), f"salt {salt}: shoulder is not the widest ring"
        assert widths[nv // 2] < widths[0] * 0.97, f"salt {salt}: no body taper — a slab"


def test_garment_hem_wanders():
    nu, nv = 11, 7
    verts, _ = sg.garment(0.46, 0.95, nu=nu, nv=nv, hem_wander=0.02)
    hem = verts[nv * (nu + 1):]
    zs = [v[2] for v in hem]
    assert abs(min(zs) - (-0.95)) < 0.03
    # the hem ring sits at ONE wandered z per garment; across garments they must differ
    z_by_salt = {round(sg.garment(0.46, 0.95, salt=s)[0][-1][2], 6) for s in range(6)}
    assert len(z_by_salt) > 1, "every garment hem lands at the same z"


def test_garments_on_a_rail_are_not_identical():
    """The vault's amateur red flag is literally 'placing identical, repeating 3D assets
    across a scene'. Instancing one garment 30 times ADDS the CAD tell."""
    sils = [tuple(round(c, 5) for c in sg.bbox(sg.garment(0.46, 0.95, salt=s)[0]))
            for s in range(8)]
    assert len(set(sils)) == len(sils)


def test_garment_sleeves_hang_beside_the_body_inside_every_bound():
    """Round-4 identity cue: sleeves. Two tubes must appear BELOW the shoulder tips,
    stay INSIDE the shoulder span (the published GARMENT_FLARE bound must survive
    sleeves), stay inside the body's own thickness envelope (the rail pitch budget
    is spent on the body, so sleeves may not widen it), and end above the hem."""
    w, d, dep = 0.40, 1.00, 0.045
    nu, nv = 11, 7
    body_n = (nv + 1) * (nu + 1)
    for salt in range(8):
        verts, faces = sg.garment(w, d, depth=dep, sway=0.010, salt=salt, sleeves=True)
        assert len(verts) > body_n, "sleeves=True added no geometry"
        sleeve = verts[body_n:]
        # two tubes, one per side
        assert any(v[0] > 0 for v in sleeve) and any(v[0] < 0 for v in sleeve)
        # span bound survives sleeves; thickness stays inside the half-depth budget
        # (outside-birth was tried and LOOK-refuted at round 5c: detached sticks)
        xs = [v[0] for v in verts]
        assert max(xs) - min(xs) <= w * sg.GARMENT_FLARE + 2 * 0.010 + 1e-9
        assert max(abs(v[1]) for v in sleeve) <= 0.5 * dep + 1e-9
        # the SILHOUETTE NOTCH: the tube must reach wider than the narrowed body at
        # its own band — a sleeve buried inside the body's width is invisible, which
        # is exactly what the first cut rendered (quick-look, round 4)
        assert max(abs(v[0]) for v in sleeve) > 0.5 * w * 0.80
        # hangs from under the shoulder; cuffs may fall PAST the body hem (reference
        # I-24-062 #125386: sleeves are the lowest part) but never past the
        # published budget the caller solves against
        assert max(v[2] for v in sleeve) < 0.0
        assert min(v[2] for v in sleeve) >= -(d * sg.SLEEVE_OVER + sg.SLEEVE_PAD) - 1e-9
    # across salts, LONG sleeves exist and actually drop below the body hem —
    # the cue the reference shows and the whole rework exists to add
    lows = [min(v[2] for v in sg.garment(w, d, depth=dep, salt=s, sleeves=True)[0][body_n:])
            for s in range(8)]
    assert any(lo < -d for lo in lows), "no sleeve ever falls past the hem"
    # the tubes are wired into the SAME mesh: faces must index into sleeve verts
    assert max(i for f in faces for i in f) >= body_n


# ---------------------------------------------------------------- cushion physics

def test_cushion_is_plump_not_a_slab():
    """A slab's horizontal cross-section is constant with height; a stuffed cushion's
    peaks in the middle and shrinks toward both poles."""
    nu, nv = 13, 9
    verts, _ = sg.cushion(0.7, 0.7, 0.19, nu=nu, nv=nv)
    rings = [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(nv + 1)]
    spans = [max(v[0] for v in r) - min(v[0] for v in r) for r in rings]
    mid = spans[len(spans) // 2]
    assert mid > spans[0] * 3, "no waist swell — this is a slab"
    assert mid > spans[-1] * 3


def test_cushion_stays_inside_its_footprint():
    verts, _ = sg.cushion(0.7, 0.5, 0.19)
    x0, y0, z0, x1, y1, z1 = sg.bbox(verts)
    assert x0 >= -1e-9 and x1 <= 0.7 + 1e-9
    assert y0 >= -1e-9 and y1 <= 0.5 + 1e-9
    assert z0 >= -1e-9 and z1 <= 0.19 + 1e-9


def test_cushion_dent_lowers_the_top_centre():
    plain = sg.bbox(sg.cushion(0.7, 0.7, 0.19, dent=0.0)[0])[5]
    dented = sg.bbox(sg.cushion(0.7, 0.7, 0.19, dent=0.03)[0])[5]
    assert dented < plain


def test_cushion_rejects_bad_pinch():
    with pytest.raises(ValueError):
        sg.cushion(0.7, 0.7, 0.19, pinch=1.8)


# ------------------------------------------------------------- folded knit physics

def _fk_rings(w=0.17, d=0.25, h=0.042, nu=17, salt=3):
    verts, _ = sg.folded_knit(w, d, h, nu=nu, salt=salt)
    n_rows = len(verts) // (nu + 1)
    return [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(n_rows)]


def test_folded_knit_is_a_slab_not_a_pancake():
    """The defect this generator replaces: cushion's sin**edge profile reaches full
    width only at mid-height, so a stack of them reads as pancakes. A folded knit's
    side must hold near-full width from just above the fold-roll to just below it —
    the quarter-height span must be >= 92% of the mid-height span (cushion at the
    old stack settings measures ~83% at the same station, and an ellipse-plan
    cushion never passes the 45-degree test below)."""
    w, d, h = 0.17, 0.25, 0.042
    rings = _fk_rings(w, d, h)
    spans = [max(v[0] for v in r) - min(v[0] for v in r) for r in rings]
    mid = max(spans)
    zs = [r[0][2] for r in rings]
    # ring nearest quarter height
    jq = min(range(len(zs)), key=lambda j: abs(zs[j] - h * 0.25))
    assert spans[jq] >= 0.92 * mid, (
        f"quarter-height span {spans[jq]:.4f} < 92% of mid {mid:.4f} — profile domes")


def test_folded_knit_plan_is_rectangular_not_elliptical():
    """An ellipse's 45-degree radius is 71% of its axis radius — the oval-pill plan
    that read as pebbles. A soft-cornered rectangle holds >= 85%."""
    w = d = 0.20
    rings = _fk_rings(w, d, 0.042)
    # widest ring (the side row at mid height)
    ring = max(rings, key=lambda r: max(v[0] for v in r) - min(v[0] for v in r))
    cx = cy = 0.10
    r_axis = max(abs(v[0] - cx) for v in ring)
    r_diag = max(min(abs(v[0] - cx), abs(v[1] - cy)) * math.sqrt(2.0) for v in ring)
    assert r_diag >= 0.85 * r_axis, (
        f"45-degree radius {r_diag:.4f} vs axis {r_axis:.4f} — plan is an oval")


def test_folded_knit_top_is_a_flat_face_not_a_pole():
    """cushion ends in a point pole; a folded item ends in a FLAT top face. The
    verts at exactly z=h must span a real area, not collapse to a point."""
    w, d, h = 0.17, 0.25, 0.042
    verts, _ = sg.folded_knit(w, d, h)
    top = [v for v in verts if abs(v[2] - h) < 1e-12]
    assert len(top) > 1
    span_x = max(v[0] for v in top) - min(v[0] for v in top)
    assert span_x >= 0.5 * w, f"top face spans {span_x:.4f} of {w} — still a dome"


def test_folded_knit_stays_inside_footprint_and_fills_height():
    w, d, h = 0.17, 0.25, 0.042
    verts, _ = sg.folded_knit(w, d, h, salt=9)
    x0, y0, z0, x1, y1, z1 = sg.bbox(verts)
    assert x0 >= -1e-9 and x1 <= w + 1e-9
    assert y0 >= -1e-9 and y1 <= d + 1e-9
    assert abs(z0) < 1e-12 and abs(z1 - h) < 1e-12, "z must fill 0..h exactly"


def test_folded_knit_salt_de_twins_the_silhouette():
    a, _ = sg.folded_knit(0.17, 0.25, 0.042, salt=1)
    b, _ = sg.folded_knit(0.17, 0.25, 0.042, salt=2)
    assert a != b


def test_folded_knit_edges_waver_not_ruler_straight():
    """The reference's silhouette lines waver ~a millimetre; a laser-straight edge is
    the CAD tell. Along the widest ring, the outline radius must vary, but never by
    more than ~4% (more reads as damage, not a fold)."""
    rings = _fk_rings(0.30, 0.25, 0.042, salt=5)
    ring = max(rings, key=lambda r: max(v[0] for v in r) - min(v[0] for v in r))
    cx, cy = 0.15, 0.125
    # sample only the flat middle of the long sides (reach > 97% of max), where the
    # superellipse's own curvature contributes ~0, so spread ~= waver alone
    reach = [abs(v[1] - cy) for v in ring]
    side = [r for r in reach if r > 0.97 * max(reach)]
    assert len(side) >= 3, "no side verts sampled"
    spread = max(side) - min(side)
    assert 1e-4 < spread < 0.02 * 0.25, f"side spread {spread:.5f} out of band"


def test_folded_knit_rejects_degenerate_and_bad_roll():
    with pytest.raises(ValueError):
        sg.folded_knit(0.0, 0.25, 0.042)
    with pytest.raises(ValueError):
        sg.folded_knit(0.17, 0.25, 0.042, roll=0.7)


# ------------------------------------------------------------------ stack + throw

def test_folded_stack_is_not_perfectly_aligned():
    """A folded towel really is a rectangle — what it must not be is perfectly stacked."""
    items = sg.folded_stack(0.32, 0.30, 5, 0.045)
    xs = {round(i[0], 6) for i in items}
    assert len(xs) == 5, "every item shares an x — that is one extruded block"


def test_folded_stack_tapers_upward():
    items = sg.folded_stack(0.32, 0.30, 5, 0.045)
    assert items[-1][3] < items[0][3]


def test_folded_stack_heights_are_exact():
    """The stack must sit ON its shelf: cumulative height stays exactly n*item_h so the
    caller can check headroom against the shelf above."""
    items = sg.folded_stack(0.32, 0.30, 4, 0.05)
    assert abs(items[-1][2] + items[-1][5] - 0.20) < 1e-9


def test_folded_stack_rejects_zero_items():
    with pytest.raises(ValueError):
        sg.folded_stack(0.32, 0.30, 0, 0.045)


def test_folded_stack_items_vary_in_height_but_the_pile_does_not():
    """Round-6 lane C (C2#9 'perfect boxes'): equal slices are the one thing a pile of
    folded knits never has — but the headroom contract (cumulative == n*item_h) stays."""
    items = sg.folded_stack(0.32, 0.30, 5, 0.045)
    hs = {round(i[5], 6) for i in items}
    assert len(hs) > 1, "every item shares one thickness — an extruded block, sliced"
    assert abs(items[-1][2] + items[-1][5] - 5 * 0.045) < 1e-9
    for a, b in zip(items, items[1:]):                 # slices still tile: no air, no overlap
        assert abs((a[2] + a[5]) - b[2]) < 1e-9


def test_folded_sheet_salt_breaks_mirror_symmetry_boundedly():
    """Round-6 lane C (C2#4): the duvet's L/R corners baked as mirror images because the
    feedstock was mirror-symmetric. salt must (a) change the main panel, (b) leave the
    fold band untouched, (c) stay bounded, (d) leave salt=0 as the exact old grid."""
    plain, _ = sg.folded_sheet(0.0, 0.0, 1.8, 2.0, 0.6, band=0.28, head="x+", cell=0.05)
    salted, _ = sg.folded_sheet(0.0, 0.0, 1.8, 2.0, 0.6, band=0.28, head="x+", cell=0.05, salt=7)
    again, _ = sg.folded_sheet(0.0, 0.0, 1.8, 2.0, 0.6, band=0.28, head="x+", cell=0.05, salt=7)
    assert salted == again, "salt must be deterministic"
    assert salted != plain, "salt=7 must actually move the panel"
    moved = 0
    for p, s in zip(plain, salted):
        d = max(abs(p[0] - s[0]), abs(p[1] - s[1]))
        assert d <= 0.006 + 1e-9, "deviation must stay inside its declared 6mm bound"
        assert abs(p[2] - s[2]) < 1e-12, "salt is in-plane only — the lift ramp is sacred"
        if d > 1e-12:
            moved += 1
    assert moved > len(plain) * 0.3, "most of the main panel should carry its own bias"


@pytest.mark.parametrize("call", [
    lambda: sg.garment(0.0, 0.9),
    lambda: sg.garment(0.4, 0.0),
    lambda: sg.cushion(0.0, 0.5, 0.2),
    lambda: sg.hanger(0.0),
    lambda: sg.bbox([]),
    lambda: sg.flat_sheet(0, 0, 0.0, 1.0, 0.0),          # the simulation feedstock must
    lambda: sg.flat_sheet(0, 0, 1.0, 1.0, 0.0,           # refuse a degenerate cut too
                          cut=[(-1, -1, 2, 2)]),
])
def test_degenerate_input_raises(call):
    """Silent-drop is this codebase's recurring wound: a botched drape must not look like
    a drape nobody asked for."""
    with pytest.raises(ValueError):
        call()



def test_cushion_edge_fullness_kills_the_pebble_silhouette():
    """2026-07-28, the pebble fix: r = sin(phi) raw made every cushion's silhouette a
    pointed lens — six of them at the bed head read as pebbles/UFOs (owner LOOK on the
    tonal-ladder renders). With the edge-fullness profile the first ring off the pole
    must already carry most of the width; the old lens must stay reproducible at
    edge=1.0 so the comparison itself is pinned."""
    nu, nv = 13, 9
    def ring1_frac(edge):
        verts, _ = sg.cushion(0.62, 0.115, 0.44, nu=nu, nv=nv, edge=edge)
        rings = [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(nv + 1)]
        spans = [max(v[0] for v in r) - min(v[0] for v in r) for r in rings]
        return spans[1] / spans[len(spans) // 2]
    assert ring1_frac(0.30) > 0.65, "first ring collapsed — the pebble is back"
    assert ring1_frac(1.0) < 0.45, "edge=1.0 no longer reproduces the old lens"


def test_cushion_rejects_a_bad_edge():
    with pytest.raises(ValueError):
        sg.cushion(0.6, 0.1, 0.4, edge=0.0)
    with pytest.raises(ValueError):
        sg.cushion(0.6, 0.1, 0.4, edge=1.4)


# ---- per-garment pose DNA (LOOK round-2 #5) ------------------------------------------
# The rail read as cloned boards because dev() varied widths only. These pin that two
# salts now produce two POSES -- and that the pose never breaks the published bounds.

def _cols(verts, nu=11, nv=7):
    return [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(nv + 1)]


def test_garment_shoulder_slopes_down_from_the_hook():
    verts, _ = sg.garment(0.40, 1.10, depth=0.045, salt=5)
    top = _cols(verts)[0]
    tip = min(v[2] for v in top)            # a shoulder END (|cos a| = 1)
    mid = max(v[2] for v in top)            # the hook point (cos a = 0)
    assert mid - tip > 0.012, "top ring is still a level ellipse -- a coat on a shelf"


def test_garment_poses_differ_by_salt():
    a, _ = sg.garment(0.40, 1.10, depth=0.045, salt=5)
    b, _ = sg.garment(0.40, 1.10, depth=0.045, salt=6)
    ca, cb = _cols(a), _cols(b)
    # bend: the mid-height lateral drift must not match piece-to-piece
    bow_a = sum(v[0] for v in ca[4]) / len(ca[4])
    bow_b = sum(v[0] for v in cb[4]) / len(cb[4])
    assert abs(bow_a - bow_b) > 0.001
    # shoulder slope differs too
    sa = max(v[2] for v in ca[0]) - min(v[2] for v in ca[0])
    sb = max(v[2] for v in cb[0]) - min(v[2] for v in cb[0])
    assert abs(sa - sb) > 0.002


def test_garment_pose_stays_inside_published_bounds():
    # the containment law styling solves against: span <= width*FLARE + 2*sway, and
    # nothing hangs below -drop - hem_wander
    for salt in range(12):
        w, d, sway, hw = 0.40, 1.10, 0.010, 0.016
        verts, _ = sg.garment(w, d, depth=0.045, sway=sway, hem_wander=hw, salt=salt)
        xs = [v[0] for v in verts]
        assert max(xs) - min(xs) <= w * sg.GARMENT_FLARE + 2 * sway + 1e-9, salt
        assert min(v[2] for v in verts) >= -d - hw - 1e-9, salt


# ---- round-3 identity cues (owner: four named examples) ------------------------------
# The round-2 review's lasting lesson: a fix without armour is revertible with every
# test green. Each round-3 construction cue gets its pin.

def test_cushion_seam_raises_a_ridge_but_never_leaves_the_footprint():
    # the whole seamed form is PRE-SHRUNK to buy the ridge room, so the pin compares
    # WITHIN each form: how far the equator ring stands proud of the ring a third of
    # the way up (where the seam gaussian is ~zero). The seamed form's equator must
    # stand proud by more than the plain form's own profile difference.
    w, d, h, nu, nv = 0.60, 0.34, 0.15, 13, 12

    def proud(verts):
        eq = max(p[0] for p in verts[6 * (nu + 1):7 * (nu + 1)])
        third = max(p[0] for p in verts[4 * (nu + 1):5 * (nu + 1)])
        return eq - third

    plain, _ = sg.cushion(w, d, h, nu=nu, nv=nv, salt=3)
    seamed, _ = sg.cushion(w, d, h, nu=nu, nv=nv, salt=3, seam=0.008)
    assert proud(seamed) > proud(plain) + 0.004      # the ridge exists
    bb = sg.bbox(seamed)                             # and the case stays contained
    assert bb[0] >= -1e-9 and bb[1] >= -1e-9
    assert bb[3] <= w + 1e-9 and bb[4] <= d + 1e-9


def test_cushion_refuses_a_seam_that_eats_the_footprint():
    with pytest.raises(ValueError):
        sg.cushion(0.05, 0.05, 0.05, seam=0.03)


def test_trouser_fold_is_a_different_species():
    tv, tf = sg.trouser_fold(0.14, 0.50, salt=2)
    gv, _ = sg.garment(0.40, 1.10, salt=2)
    assert all(len(f) == 4 for f in tf)
    # half the drop, a fraction of the span — the silhouette differs in KIND
    assert min(p[2] for p in tv) > min(p[2] for p in gv)
    assert max(p[0] for p in tv) - min(p[0] for p in tv) \
        < 0.5 * (max(p[0] for p in gv) - min(p[0] for p in gv))


def test_garment_collar_rises_at_the_neck_only():
    nu = 11
    bare, _ = sg.garment(0.40, 1.10, salt=4)
    col, _ = sg.garment(0.40, 1.10, salt=4, collar=0.016)
    top_b, top_c = bare[:nu + 1], col[:nu + 1]
    # the neck zone rises...
    assert max(p[2] for p in top_c) > max(p[2] for p in top_b) + 0.008
    # ...the shoulder TIPS (|x| max) stay where the hanger law put them
    tip_b = min(top_b, key=lambda p: -abs(p[0]))
    tip_c = min(top_c, key=lambda p: -abs(p[0]))
    assert abs(tip_b[2] - tip_c[2]) < 0.001          # gaussian tail = float dust, not lift


# --------------------------------------------------------------------------- dart
# P2r-1 mechanism 3 (p2r13): the DR rank-4 sewing dart as pure feedstock.

def test_corner_dart_cuts_a_wedge_and_pairs_the_banks():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    v2, f2, sew = sg.corner_dart(v, f, (0.0, 0.0), length=0.3)
    assert len(f2) < len(f)                          # the wedge is really gone
    assert all(len(q) == 4 for q in f2)              # quads survive (no n-gons)
    assert sew and all(a != b for a, b in sew)
    n = len(v2)
    assert all(0 <= k < n for q in f2 for k in q)
    assert all(0 <= a < n and 0 <= b < n for a, b in sew)


def test_corner_dart_sew_edges_are_loose_and_span_the_gap():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    v2, f2, sew = sg.corner_dart(v, f, (1.0, 0.0), length=0.25)
    face_edges = {frozenset((q[i], q[(i + 1) % 4])) for q in f2 for i in range(4)}
    assert all(frozenset(e) not in face_edges for e in sew)   # loose by construction
    # every pair spans the wedge: the two ends sit apart, not coincident
    assert all((v2[a][0] - v2[b][0]) ** 2 + (v2[a][1] - v2[b][1]) ** 2 > 1e-8
               for a, b in sew)


def test_corner_dart_refuses_a_silent_noop():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    with pytest.raises(ValueError):
        sg.corner_dart(v, f, (5.0, 5.0), length=0.1)   # fan never touches the sheet


def test_corner_dart_keeps_untouched_geometry_verbatim():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    v2, f2, sew = sg.corner_dart(v, f, (0.0, 1.0), length=0.3)
    orig = {tuple(p) for p in v}
    assert all(tuple(p) in orig for p in v2)          # a dart cuts, it never moves cloth


def test_corner_dart_is_deterministic():
    v, f = sg.flat_sheet(0.0, 0.0, 1.2, 0.8, 0.5, cell=0.04)
    a = sg.corner_dart(v, f, (1.2, 0.8), length=0.2)
    b = sg.corner_dart(v, f, (1.2, 0.8), length=0.2)
    assert a == b


def test_corner_dart_chains_two_corners_without_detaching_the_first_seam():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    v1, f1, s1 = sg.corner_dart(v, f, (0.0, 0.0), length=0.25)
    v2, f2, s2 = sg.corner_dart(v1, f1, (1.0, 0.0), length=0.25, sew=s1)
    assert len(s2) >= len(s1) + 3          # first seam survived + second added
    n = len(v2)
    assert all(0 <= a < n and 0 <= b < n and a != b for a, b in s2)
    # first seam's pairs still span a real gap after the second remap
    import math
    assert all(math.hypot(v2[a][0] - v2[b][0], v2[a][1] - v2[b][1]) > 1e-4
               for a, b in s2)


# ---------------------------------------------------------------- dart sites + hem
# P2r-1, the coverlet half (p2r19): the round-cut corner's dart is DERIVED from
# the mitre's own arc, and the hem cue names the sheet's free boundary.

def _foot_mitre(over=0.30, x0=1.0, y0=1.0, dx=2.0, dy=1.6):
    """Two free foot-corner blocks the way bake_bed_cover builds them
    (head on x+ so the x0 side carries the overhang)."""
    return [(x0 - over, y0 - over, x0, y0, x0, y0),
            (x0 - over, y0 + dy, x0, y0 + dy + over, x0, y0 + dy)]


def test_corner_dart_sites_apex_lands_on_the_mattress_corner():
    import math
    inv = 1.0 / math.sqrt(2.0)
    sites, skipped = sg.corner_dart_sites(_foot_mitre(), sg.COVERLET_MITRE_KEEP, 0.028)
    assert len(sites) == 2 and not skipped
    for (dipx, dipy), length, (ix, iy) in [
            (*s, c) for s, c in zip(sites, [(1.0, 1.0), (1.0, 2.6)])]:
        # reproduce corner_dart's own apex arithmetic: bisector toward the
        # sheet interior is +x for both (overhang west), +/-y by corner
        bx = 1.0
        by = 1.0 if dipy <= iy else -1.0
        ax = dipx + bx * length * inv
        ay = dipy + by * length * inv
        assert abs(ax - ix) < 1e-9 and abs(ay - iy) < 1e-9


def test_corner_dart_sites_skip_subresolution_loudly():
    sites, skipped = sg.corner_dart_sites(_foot_mitre(over=0.05),
                                          sg.COVERLET_MITRE_KEEP, 0.028)
    assert not sites and len(skipped) == 2
    assert all("SKIPPED" in m for m in skipped)


def test_corner_dart_sites_feed_a_real_cut():
    over = 0.30
    mit = _foot_mitre(over)
    v, f = sg.flat_sheet(1.0 - over, 1.0 - over, over + 2.0, 1.6 + 2 * over, 0.5,
                         cell=0.028, mitre=mit,
                         mitre_keep=sg.COVERLET_MITRE_KEEP)
    sites, skipped = sg.corner_dart_sites(mit, sg.COVERLET_MITRE_KEEP, 0.028)
    assert sites and not skipped
    sew = []
    for dip, length in sites:
        v, f, sew = sg.corner_dart(v, f, dip, length, sew=sew)
    assert sew                                  # both cuts paired banks on arc cloth


def test_boundary_verts_names_the_rim_and_only_the_rim():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.1)
    rim = sg.boundary_verts(f)
    for k in rim:
        x, y, _ = v[k]
        assert min(x, y) < 1e-9 or max(x, y) > 1.0 - 1e-9
    inner = [k for k in range(len(v)) if k not in rim]
    assert inner                                # a sheet has an interior
    for k in inner:
        x, y, _ = v[k]
        assert 0.0 < x < 1.0 and 0.0 < y < 1.0


def test_boundary_verts_includes_dart_banks_after_the_cut():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.05)
    rim0 = sg.boundary_verts(f)
    v2, f2, sew = sg.corner_dart(v, f, (0.0, 0.0), length=0.3)
    rim2 = sg.boundary_verts(f2)
    # every sewn bank vert is boundary now — the seam inherits the hem read
    assert all(a in rim2 and b in rim2 for a, b in sew)
    assert len(rim2) > 0 and len(rim0) > 0
