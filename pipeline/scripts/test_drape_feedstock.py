"""Tests for the PURE half of the cloth lane (2026-07-22).

The previous element shipped 1985 green tests that could not see a build-breaking
regression, because the two functions its consumer actually called had zero coverage.
These are those functions this time: what layer 1 hands the solver, and the predicate
the anti-repaint armour and the build must both answer the same way.

Nothing here simulates cloth â€” that is layer 2's job and Blender's. What is pinned is
the CONTRACT: quads only, no orphan vertices, corners that leave no free edge, a pin
region that is a region and not a grid row, and one predicate with one answer.
"""
import math

import pytest

import softgoods as sg
import styling as st


# ---------------------------------------------------------------- flat_sheet

def test_sheet_is_all_quads_never_ngons():
    v, f = sg.flat_sheet(0.0, 0.0, 1.0, 2.0, 0.5, cell=0.05)
    assert f and all(len(q) == 4 for q in f), "a SketchUp recipient sees n-gons"


def test_sheet_stations_derive_from_extent_not_a_fixed_count():
    """`cell` is an edge LENGTH. A coverlet and a napkin must not share a station
    count or the napkin folds like a tarpaulin."""
    small = sg.flat_sheet(0, 0, 0.4, 0.4, 0, cell=0.02)[0]
    large = sg.flat_sheet(0, 0, 4.0, 4.0, 0, cell=0.02)[0]
    assert len(large) > len(small) * 50


def test_sheet_edge_length_tracks_the_requested_cell():
    v, f = sg.flat_sheet(0, 0, 1.0, 1.0, 0, cell=0.05)
    a, b = v[f[0][0]], v[f[0][1]]
    assert math.isclose(abs(b[0] - a[0]), 0.05, abs_tol=1e-9)


def test_sheet_refuses_a_degenerate_extent():
    with pytest.raises(ValueError):
        sg.flat_sheet(0, 0, 0.0, 1.0, 0.0)


def test_every_vertex_is_used_by_a_face():
    """A vertex no face references is a FREE PARTICLE: the solver drops it to the
    floor and it lands outside every bound the build asserts."""
    cut = [(0.0, 0.0, 0.3, 0.3)]
    v, f = sg.flat_sheet(0, 0, 1.0, 1.0, 0, cell=0.05, cut=cut)
    used = {i for q in f for i in q}
    assert used == set(range(len(v))), "orphan vertices survived the cut"


def test_a_square_cut_actually_removes_that_corner():
    v, _ = sg.flat_sheet(0, 0, 1.0, 1.0, 0, cell=0.05, cut=[(0.0, 0.0, 0.3, 0.3)])
    assert not [p for p in v if p[0] < 0.24 and p[1] < 0.24]


def test_cutting_everything_raises_rather_than_returning_an_empty_sheet():
    with pytest.raises(ValueError):
        sg.flat_sheet(0, 0, 1.0, 1.0, 0, cell=0.05, cut=[(-1, -1, 2, 2)])


# ---------------------------------------------------------------- the corner

def _corner_profile(keep):
    """Distance from the inner corner to the nearest kept vertex, per angle."""
    v, _ = sg.flat_sheet(0, 0, 1.0, 1.0, 0, cell=0.02,
                         mitre=[(0.0, 0.0, 0.4, 0.4, 0.4, 0.4)], mitre_keep=keep)
    return [p for p in v if p[0] < 0.4 - 1e-9 and p[1] < 0.4 - 1e-9]


def test_the_rounded_corner_leaves_no_free_edge_running_to_a_point():
    """The defect this replaced: a squared-off or mitred corner leaves the two
    adjacent panels with free edges meeting at a point, and they splay into sharp
    tabs sticking out of the bed's silhouette. A rounded boundary has no such pair â€”
    every kept corner vertex sits within the radius, so the outline is one curve."""
    r = 0.4
    for p in _corner_profile(1.0):
        d = math.hypot(0.4 - p[0], 0.4 - p[1])
        assert d <= r + 0.03, f"vertex at radius {d:.3f} escaped a {r:.3f} round"


def test_a_rounded_corner_keeps_more_cloth_than_a_diagonal_mitre():
    """Sanity on the geometry itself: quarter disc (pi/4) beats triangle (1/2)."""
    assert len(_corner_profile(1.0)) > len(_corner_profile(0.7))


def test_mitre_keep_below_one_tucks_more_of_the_corner_away():
    assert len(_corner_profile(0.6)) < len(_corner_profile(1.0))


# ------------------------------------------------------------- verts_in_rect

def test_pin_region_is_a_region_not_a_grid_row():
    """THE bug that made the first coverlet bake fail: pinning a whole grid row held
    the overhanging wings rigidly in mid-air, so the flanks never fell at all while
    the unpinned foot draped correctly. A pin names cloth that is physically trapped."""
    v, _ = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.0, cell=0.05)
    band = sg.verts_in_rect(v, 0.2, 0.2, 0.3, 0.8)
    assert band, "the band found nothing"
    for i in band:
        assert 0.2 - 1e-6 <= v[i][0] <= 0.3 + 1e-6
        assert 0.2 - 1e-6 <= v[i][1] <= 0.8 + 1e-6
    assert len(band) < len(v) / 4


def test_pin_region_outside_the_sheet_is_empty_not_an_error():
    """bake_bed_cover turns an empty pin into a RAISE with a sentence about creeping
    off the bed; it must be allowed to see the emptiness first."""
    v, _ = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.0, cell=0.05)
    assert sg.verts_in_rect(v, 5.0, 5.0, 6.0, 6.0) == []


# ----------------------------------------------------------------- the throw

def test_foot_throw_agrees_with_the_canonical_bed_the_build_ships():
    """2026-07-28: band re-solved 0.72 -> 0.50 (owner LOOK: at 36% of the bed the throw
    was the LARGEST object in both judged frames â€” a second coverlet, not an accent).
    The envelope here is the one the bake ladder actually verified on this bed."""
    band, hang = st.foot_throw(2.0, 2.149, 0.60, 0.204)
    assert 0.45 <= band <= 0.55 and 0.20 <= hang <= 0.30


def test_the_laid_band_is_never_shorter_than_the_cantilever():
    """THE 2.2x FLOOR IS RETIRED, and this test records why instead of vanishing: the
    5.1 m fall it encoded was measured on an UNPINNED sheet. The build has since pinned
    the throw's innermost strip (a tucked edge), so the pin â€” not the band's weight â€”
    holds the sheet, and the bake still fails the build loudly (hem_min, containment,
    frozen-sheet) if that ever stops being true; the 2026-07-28 resize attempt that
    misread `hang` proved that ladder fires. What pure logic still owns: a LAID throw
    has at least as much cloth on the bed as hanging off it â€” band >= hang â€” which is
    also the envelope the bake has actually been verified in (0.50 vs 0.28)."""
    for along in (1.6, 1.9, 2.0, 2.2, 2.6):
        for h in (0.40, 0.50, 0.60, 0.75):
            plan = st.foot_throw(along, 2.0, h, h * 0.34)
            if plan:
                band, hang = plan
                assert band >= hang - 1e-9


def test_the_throw_never_reaches_into_the_pillow_ladder():
    for along in (1.6, 1.8, 2.0, 2.4):
        plan = st.foot_throw(along, 2.0, 0.60, 0.204)
        if plan:
            _ranks, pz = st.head_ranks(along)
            assert along - plan[0] > pz + 0.14


def test_the_throw_hem_can_never_bury_the_signed_plinth_reveal():
    """Element 3 signed a recessed-plinth shadow gap. The fall is bounded by it."""
    for h in (0.40, 0.55, 0.60, 0.80):
        plan = st.foot_throw(2.0, 2.0, h, h * 0.34)
        if plan:
            assert h - h * 0.34 - plan[1] >= st.DRAPE_REVEAL


def test_a_bed_too_narrow_for_a_coverlet_shoulder_gets_no_throw():
    assert st.foot_throw(2.0, 2 * st.THROW_INSET + 0.2, 0.60, 0.204) is None


def test_a_bed_too_low_to_fall_past_gets_no_throw_instead_of_a_negative_one():
    assert st.foot_throw(2.0, 2.0, 0.30, 0.28) is None


def test_the_predicate_is_deterministic():
    """The armour and the build call this separately; they must never disagree."""
    a = st.foot_throw(2.0, 2.149, 0.60, 0.204)
    b = st.foot_throw(2.0, 2.149, 0.60, 0.204)
    assert a == b


# ------------------------------------------------- the deliverable .blend engine

def _build_room_src():
    import io as _io
    import os as _os
    here = _os.path.dirname(_os.path.abspath(__file__))
    return _io.open(_os.path.join(here, "build_room.py"), encoding="utf-8").read()


def test_the_saved_blend_is_pinned_to_cycles_before_it_is_written():
    """Every .blend this studio shipped up to 2026-07-22 recorded BLENDER_EEVEE at 4096
    samples, because render() set the engine AFTER save() ran. The deliverable therefore
    did not reproduce the PNG beside it, and opened headless it takes the EGL/Xvfb path
    pipeline/CLAUDE.md forbids â€” a rule broken by the ordering at its own call site.

    This pins the ORDER, not just the presence: a configure_cycles() call that drifts
    below save_as_mainfile() restores the bug while still looking correct in a diff.
    (Element 7 shipped exactly that shape â€” a routing pin that never pinned order.)"""
    src = _build_room_src()
    i_def = src.index("def save(")
    i_cfg = src.index("configure_cycles(", i_def)
    i_write = src.index("save_as_mainfile", i_def)
    assert i_cfg < i_write, "save() writes the .blend before pinning the engine"


def test_configure_cycles_pins_the_engine_the_layer_law_requires():
    src = _build_room_src()
    body = src[src.index("def configure_cycles("):src.index("def save(")]
    assert "scn.render.engine = 'CYCLES'" in body
    assert "EEVEE" in body, "the reason CYCLES is mandatory must travel with the code"


def test_the_blend_and_the_png_are_given_the_same_settings():
    """save() and render() must be handed ONE samples/res value. They were literally
    adjacent lines with different numbers, which is how a deliverable drifts from its
    own render without any diff ever looking wrong."""
    src = _build_room_src()
    seg = src[src.index("_samples = 400 if hero"):]
    seg = seg[:seg.index("built SUITE")]
    assert "save(name, samples=_samples, res=_res)" in seg
    assert "render(name, samples=_samples, res=_res)" in seg


def test_the_armour_never_goes_silent_on_a_throw_the_build_actually_made():
    """`_build_bed` knows the head axis; the anti-repaint armour does not, and resolves it
    by taking the LONGER footprint run as head-to-foot. That guess can disagree â€” and the
    build/armour cross-check in _build_bed only pins build-against-build, so nothing else
    catches it. What makes the guess safe is its DIRECTION, and a direction asserted in a
    docstring is not a direction.

    A false YES (armour describes a throw that is not there) tells the beauty pass not to
    remove something absent: free. A false NO drops armour off a piece the build really
    made â€” the revert-by-omission this whole lane exists to prevent. Sweep says: 547 false
    YES, ZERO false NO."""
    import material_presets as mp        # noqa: F401  (import proves the pair ship together)
    false_no = []
    for w in [1.2 + 0.05 * i for i in range(30)]:
        for d in [1.2 + 0.05 * i for i in range(30)]:
            for h in (0.45, 0.55, 0.60, 0.70):
                try:
                    built = bool(st.foot_throw(w, d, h, h * 0.34))
                    said = bool(st.foot_throw(max(w, d), min(w, d), h, h * 0.34))
                except ValueError:
                    continue            # head_ranks refuses the bed; the build would too
                if built and not said:
                    false_no.append((round(w, 2), round(d, 2), h))
    assert not false_no, f"armour goes silent on {len(false_no)} built throws: {false_no[:5]}"


# ---- the tangent mitre curve (LOOK round-2 #3) ---------------------------------------
# The corner Z-step fix shipped once with ZERO armour (pre-commit review 2026-07-28):
# reverting _mitre_radius to `return keep`, deleting the arc-snap and dropping the
# coverlet's deep dip left all tests green. These make that revert red.

def test_mitre_radius_is_full_at_the_strips_and_dips_on_the_diagonal():
    for keep in (0.45, 0.6, 0.8):
        assert sg._mitre_radius(1.0, 0.0, keep) == pytest.approx(1.0)
        assert sg._mitre_radius(0.0, 1.0, keep) == pytest.approx(1.0)
        assert sg._mitre_radius(0.7, 0.7, keep) == pytest.approx(keep)   # 45 deg
        # everywhere between the two: inside [keep, 1], never outside
        for k in range(1, 20):
            u = k / 20.0
            f = sg._mitre_radius(u, 1.0 - u, keep)
            assert keep - 1e-9 <= f <= 1.0 + 1e-9


def test_mitre_boundary_verts_are_snapped_onto_the_curve():
    # every kept vert inside the corner rect must lie ON or INSIDE the tangent curve;
    # face-drop precision alone leaves a staircase of verts beyond it (the squared
    # drop->shelf->drop the render caught), so this fails if the arc-snap reverts
    keep = 0.45
    mit = (0.0, 0.0, 0.3, 0.3, 0.3, 0.3)      # corner rect, inner corner at (0.3, 0.3)
    verts, faces = sg.flat_sheet(0.0, 0.0, 1.0, 1.0, 0.5, cell=0.028,
                                 mitre=[mit], mitre_keep=keep)
    a, b, c, e, ix, iy = mit
    for vx, vy, _ in verts:
        if a - 1e-9 <= vx <= c + 1e-9 and b - 1e-9 <= vy <= e + 1e-9:
            u = abs(vx - ix) / (c - a)
            v = abs(vy - iy) / (e - b)
            r = (u * u + v * v) ** 0.5
            assert r <= sg._mitre_radius(u, v, keep) + 1e-6


def test_coverlet_mitre_keep_is_the_deep_dip():
    # 0.45, deliberately UNDER the 0.6 default: the tangent rise adds corner cloth,
    # and at 0.6 that surplus cowled past the plan line and made the search ladder
    # iron the whole coverlet (slack 2.5%->0.62%). The deep dip pays for the rise.
    assert sg.COVERLET_MITRE_KEEP == pytest.approx(0.45)
    assert sg.COVERLET_MITRE_KEEP < 0.6
