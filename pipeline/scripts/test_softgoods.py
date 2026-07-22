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


def test_dev_does_not_clump():
    """Golden-ratio low discrepancy: no two of the first 30 samples land on top of each
    other (a naive sin(i) sequence beats and clumps — the vault's 'identical repeating
    assets' amateur red flag)."""
    vals = sorted(sg.dev(i, 1.0) for i in range(30))
    gaps = [b - a for a, b in zip(vals, vals[1:])]
    assert min(gaps) > 0.005


# --------------------------------------------------------------------- mesh sanity

ALL_MESHES = [
    ("drape_skirt", lambda: sg.drape_skirt(2.0, 2.149, 0.28)),
    ("garment", lambda: sg.garment(0.46, 0.95)),
    ("hanger", lambda: sg.hanger(0.40)),
    ("cushion", lambda: sg.cushion(0.70, 0.70, 0.19, dent=0.02)),
    ("throw", lambda: sg.throw(1.40, 0.90, 0.60, tail_drop=0.42)),
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


def test_drape_crease_grows_downward():
    """THE signature of hanging cloth: constrained at the top, free at the bottom. If the
    amplitude were uniform the surface is a corrugation (which is exactly why the existing
    sheers read as fluted acrylic panel)."""
    nv = 6
    verts, _ = sg.drape_skirt(2.0, 2.0, 0.30, nv=nv, fold=0.03)
    rings = _skirt_rings(verts, nv)
    # sample the south edge only (normal -y): spread in y at each height level
    south = [r for r in rings[: len(rings) // 4]]
    spreads = []
    for j in range(nv + 1):
        ys = [r[j][1] for r in south]
        spreads.append(max(ys) - min(ys))
    assert spreads[0] < spreads[nv] * 0.25, f"crease does not grow downward: {spreads}"
    assert spreads[nv] > 0.008, "hem has no fold at all — this is a slab"


def test_drape_hem_is_not_level():
    """A level hem is a machine cut. Real cloth wanders."""
    nv = 6
    verts, _ = sg.drape_skirt(2.0, 2.0, 0.30, nv=nv, hem_wander=0.020)
    rings = _skirt_rings(verts, nv)
    hem_z = [r[nv][2] for r in rings]
    assert max(hem_z) - min(hem_z) > 0.004, "hem is level — that is a box, not a drape"


def test_drape_hem_wanders_SMOOTHLY_not_as_a_sawtooth():
    """CAUGHT IN PIXELS, 2026-07-22. The first cut drove the hem with dev(i), whose whole
    purpose is to make adjacent samples maximally DIFFERENT — correct for choosing garment
    widths, catastrophic for a continuous edge. The render showed torn cardboard. A hem is
    a curve along its run: neighbouring stations must differ by a small fraction of the
    total wander, not by all of it."""
    nv = 8
    verts, _ = sg.drape_skirt(1.95, 2.10, 0.37, nv=nv, hem_wander=0.018)
    rings = _skirt_rings(verts, nv)
    hem = [r[nv][2] for r in rings]
    jumps = [abs(b - a) for a, b in zip(hem, hem[1:])]
    total = max(hem) - min(hem)
    assert max(jumps) < total * 0.12, (
        f"hem jumps {max(jumps) * 1000:.1f}mm between adjacent stations out of a "
        f"{total * 1000:.1f}mm range — that is a sawtooth, not drape")


def test_drape_folds_land_in_a_physical_pitch_band():
    """Fold pitch must be a LENGTH, not a cycle count. Specifying '13 cycles per
    perimeter' put the folds 615mm apart on this bed and rendered as flat panels with a
    wavy edge; hanging cloth folds every ~60-160mm regardless of how big the bed is."""
    nv = 8
    verts, _ = sg.drape_skirt(1.95, 2.10, 0.37, nv=nv, fold=0.02)
    rings = _skirt_rings(verts, nv)
    quarter = len(rings) // 4
    ys = [r[nv][1] for r in rings[:quarter]]
    peaks = [i for i in range(1, len(ys) - 1) if ys[i] < ys[i - 1] and ys[i] < ys[i + 1]]
    pitch = 1.95 / max(len(peaks), 1)
    assert 0.05 <= pitch <= 0.20, f"fold pitch {pitch * 1000:.0f}mm is not cloth-like"


def test_drape_fold_pitch_is_independent_of_bed_size():
    """The same fabric on a bigger bed folds at the same pitch — more folds, not wider
    ones. A cycles-per-perimeter spec gets this exactly backwards."""
    def pitch(w, d):
        nv = 8
        rings = _skirt_rings(sg.drape_skirt(w, d, 0.37, nv=nv, fold=0.02)[0], nv)
        q = len(rings) // 4
        ys = [r[nv][1] for r in rings[:q]]
        pk = [i for i in range(1, len(ys) - 1) if ys[i] < ys[i - 1] and ys[i] < ys[i + 1]]
        return w / max(len(pk), 1)
    small, big = pitch(1.4, 1.9), pitch(2.6, 2.9)
    assert abs(small - big) < 0.045, f"pitch drifts with size: {small:.3f} vs {big:.3f}"


def test_drape_top_edge_is_clean():
    """The suspension line must stay put: it is where the cloth meets built joinery, and
    a wandering top edge would show a gap against the mattress."""
    nv = 6
    verts, _ = sg.drape_skirt(2.0, 2.0, 0.30, nv=nv, top_z=0.55)
    rings = _skirt_rings(verts, nv)
    tops = [r[0][2] for r in rings]
    assert max(tops) - min(tops) < 1e-9
    assert abs(tops[0] - 0.55) < 1e-9


def test_drape_fold_pitch_is_irregular():
    """Multi-wavelength on purpose: one frequency is a corrugation, several incommensurate
    ones read as cloth. Measured as: the gaps between successive outward peaks vary."""
    nv = 6
    verts, _ = sg.drape_skirt(3.0, 3.0, 0.30, nv=nv, fold=0.03)
    rings = _skirt_rings(verts, nv)
    quarter = len(rings) // 4
    ys = [r[nv][1] for r in rings[:quarter]]           # south hem, outward = -y
    peaks = [i for i in range(1, len(ys) - 1) if ys[i] < ys[i - 1] and ys[i] < ys[i + 1]]
    assert len(peaks) >= 3, f"too few folds to judge pitch: {peaks}"
    gaps = [b - a for a, b in zip(peaks, peaks[1:])]
    assert len(set(gaps)) > 1, f"fold pitch is uniform ({gaps}) — that is a corrugation"


def test_drape_bulge_is_bounded_by_fold():
    """The caller owes its host part the CAD invariant, so it must be able to size an
    inset. The skirt may bulge outward, but never by more than `fold`."""
    fold = 0.02
    verts, _ = sg.drape_skirt(2.0, 2.149, 0.28, fold=fold, hem_wander=0.01)
    x0, y0, _, x1, y1, _ = sg.bbox(verts)
    assert -fold - 1e-9 <= x0 and x1 <= 2.0 + fold + 1e-9
    assert -fold - 1e-9 <= y0 and y1 <= 2.149 + fold + 1e-9


def test_drape_hangs_the_full_drop():
    verts, _ = sg.drape_skirt(2.0, 2.0, 0.28, top_z=0.6)
    _, _, z0, _, _, z1 = sg.bbox(verts)
    assert abs(z1 - 0.6) < 1e-9
    assert z0 < 0.6 - 0.28 + 1e-9


# ----------------------------------------------------------------- garment physics

def test_garment_shoulder_is_narrower_than_body():
    """A garment on a hanger is a shoulder line opening to a body. A constant width is a
    sheet pegged on a line."""
    nu, nv = 11, 7
    verts, _ = sg.garment(0.46, 0.95, nu=nu, nv=nv, shoulder=0.6, sway=0.0)
    rings = [verts[j * (nu + 1):(j + 1) * (nu + 1)] for j in range(nv + 1)]
    top_w = max(v[0] for v in rings[0]) - min(v[0] for v in rings[0])
    bot_w = max(v[0] for v in rings[-1]) - min(v[0] for v in rings[-1])
    assert top_w < bot_w * 0.75, f"shoulder {top_w:.3f} not narrower than body {bot_w:.3f}"


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


def test_garment_rejects_bad_shoulder():
    with pytest.raises(ValueError):
        sg.garment(0.46, 0.95, shoulder=1.4)


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


def test_throw_hem_is_not_parallel_to_the_host_edge():
    """A fold parallel to the bed edge is the machine's signature."""
    nu, nv = 17, 7
    verts, _ = sg.throw(1.4, 0.9, 0.6, nu=nu, nv=nv, skew=0.06)
    far = [verts[i * (nv + 1)] for i in range(nu + 1)]     # j=0 == the far edge
    ys = [v[1] for v in far]
    assert max(ys) - min(ys) > 0.01, "throw hem runs parallel to the host edge"


def test_throw_tail_falls_below_the_lay_plane():
    verts, _ = sg.throw(1.4, 0.9, 0.6, tail_drop=0.42)
    _, _, z0, _, _, z1 = sg.bbox(verts)
    assert z0 < 0.6 - 0.35, "the tail does not hang"
    assert z1 <= 0.6 + 0.05


def test_throw_without_tail_stays_on_the_plane():
    verts, _ = sg.throw(1.4, 0.9, 0.6, tail_drop=0.0)
    _, _, z0, _, _, z1 = sg.bbox(verts)
    assert z0 > 0.6 - 0.05 and z1 < 0.6 + 0.05


# --------------------------------------------------------------------- fail loud

@pytest.mark.parametrize("call", [
    lambda: sg.drape_skirt(0.0, 2.0, 0.3),
    lambda: sg.drape_skirt(2.0, 2.0, 0.0),
    lambda: sg.garment(0.0, 0.9),
    lambda: sg.garment(0.4, 0.0),
    lambda: sg.cushion(0.0, 0.5, 0.2),
    lambda: sg.throw(0.0, 0.9, 0.6),
    lambda: sg.throw(1.4, 0.9, 0.6, tail_drop=-0.1),
    lambda: sg.hanger(0.0),
    lambda: sg.bbox([]),
])
def test_degenerate_input_raises(call):
    """Silent-drop is this codebase's recurring wound: a botched drape must not look like
    a drape nobody asked for."""
    with pytest.raises(ValueError):
        call()


def test_hem_wander_beyond_the_cap_raises():
    """Past a bound, 'drape' becomes damage — and a mistyped value must not quietly ship
    a shredded hem."""
    with pytest.raises(ValueError):
        sg.drape_skirt(2.0, 2.0, 0.3, hem_wander=sg.MAX_HEM_WANDER + 0.001)
