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
