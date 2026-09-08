"""Tests for edge_shadow.py — the shadow-line (undershoot) instrument.

The synthetic controls are the point: this module exists because two OTHER rungs in
this repo passed for rounds while being structurally unable to see the case they were
named for. Every claim edge_shadow makes is pinned here against geometry we authored,
so a future edit that breaks the discrimination fails a test instead of shipping green.
"""
import json

import numpy as np
import pytest

import edge_shadow as ES


def _ramp(h=60, w=120, lo=140.0, hi=200.0):
    """A pure tonal ramp: two plateaus joined by a monotonic gradient. No occlusion.
    This is what a material change with no thickness looks like."""
    col = np.concatenate([
        np.full(20, lo),
        np.linspace(lo, hi, 20),
        np.full(h - 40, hi),
    ])
    return np.tile(col[:, None], (1, w))


def _edge(h=60, w=120, lo=140.0, hi=200.0, dip=25.0):
    """A finite-thickness edge lying on a surface: the same two plateaus, but the light
    reaching the surface just past the edge is occluded, leaving a dark line."""
    col = np.concatenate([
        np.full(20, lo),
        np.array([lo - dip, lo - dip]),      # the cast line
        np.linspace(lo, hi, 6),
        np.full(h - 28, hi),
    ])
    return np.tile(col[:, None], (1, w))


def test_a_tonal_ramp_casts_no_line():
    pct, med, n = ES.shadow_line(_ramp())
    assert n > 100, "the ramp should present real columns to judge"
    assert pct < 5.0, f"a monotonic ramp must not read as an edge (got {pct:.1f}%)"


def test_a_real_edge_casts_a_line():
    pct, med, n = ES.shadow_line(_edge())
    assert pct > 90.0, f"an occluding edge must line nearly every column (got {pct:.1f}%)"
    assert med > 15.0, f"and the line must have depth (got {med:.1f} codes)"


def test_the_two_are_separated_by_an_order_of_magnitude():
    """The failure mode this module was written to avoid: a metric that scores two
    visibly different things the same. p2_exit.edge_rise_width read 5 px for both."""
    ramp_pct = ES.shadow_line(_ramp())[0]
    edge_pct = ES.shadow_line(_edge())[0]
    assert edge_pct > 10 * max(ramp_pct, 1.0)


def test_flat_field_offers_no_columns_rather_than_scoring_zero():
    """A featureless crop must report n=0, not a confident 0% — a 0 from a reader that
    cannot see is not a 0 (this repo's vacuous-zero class)."""
    pct, med, n = ES.shadow_line(np.full((60, 120), 170.0))
    assert n == 0 and pct == 0.0


def test_verdict_refuses_without_a_control():
    sites = [{"name": "ours", "pct": 2.8, "med": 2.9, "n": 142}]
    with pytest.raises(ES.NoControl):
        ES.verdict(sites)


def test_verdict_refuses_when_the_control_did_not_fire():
    """The load-bearing case: if the control is silent the test could not see, so an
    absence elsewhere is unread — never clean."""
    sites = [
        {"name": "ctrl", "pct": 11.0, "med": 3.0, "n": 300, "control": True},
        {"name": "ours", "pct": 2.8, "med": 2.9, "n": 142},
    ]
    with pytest.raises(ES.NoControl):
        ES.verdict(sites)


def test_verdict_calls_paint_when_the_control_fired():
    sites = [
        {"name": "ctrl", "pct": 93.7, "med": 39.3, "n": 395, "control": True},
        {"name": "ours", "pct": 2.8, "med": 2.9, "n": 142},
        {"name": "hem", "pct": 95.0, "med": 23.0, "n": 200},
    ]
    rows, ref = ES.verdict(sites)
    calls = {s["name"]: call for s, call, _ in rows}
    assert ref["name"] == "ctrl"
    assert calls["ours"].startswith("NO LINE")
    assert calls["hem"] == "READS AS AN EDGE"


def test_p2r34_numbers_reproduce_the_finding():
    """The banding this module was derived from, pinned as a regression on the
    CLASSIFIER: 95.0% reads as an edge, 2.8% does not, against a 93.7% control.

    The provenance of the 2.8% is corrected at p2r41 and the correction is left
    here on purpose. That figure was measured in a box the matmask later showed to
    be 99.6% ONE material, so it was never a reading of our coverlet boundary — it
    was a reading of shading noise inside a single cloth. `verdict`'s banding of
    the three numbers is unaffected and still what this test pins; what changed is
    that a site is now DERIVED from a named contact (contact_columns), so the same
    mistake cannot be made by typing four fractions."""
    sites = [
        {"name": "bed base meets floor", "pct": 93.7, "med": 39.3, "n": 395, "control": True},
        {"name": "pillow flange", "pct": 95.0, "med": 23.0, "n": 200},
        {"name": "coverlet boundary", "pct": 2.8, "med": 2.9, "n": 142},
    ]
    rows, _ = ES.verdict(sites)
    calls = {s["name"]: call for s, call, _ in rows}
    assert calls["pillow flange"] == "READS AS AN EDGE"
    assert calls["coverlet boundary"].startswith("NO LINE")


# ------------------------------------------------------- derived contact sites

def _stack(h=60, w=200, upper=7, lower=9, row=28):
    """An id image: material `upper` above row, `lower` below it. The synthetic
    twin of a matmask where one cloth lies on another."""
    ids = np.full((h, w), lower, dtype=np.int32)
    ids[:row, :] = upper
    return ids


def test_contact_columns_finds_the_row_of_a_named_contact():
    cols = ES.contact_columns(_stack(), 7, 9)
    assert len(cols) == 200
    assert set(cols.values()) == {27}, "the contact row is the last UPPER row"


def test_contact_columns_is_ordered_and_the_other_side_is_a_different_site():
    """Reversing the pair names the other side of the fold, which on p2r39 is the
    difference between 36% and 99%. It must not quietly return the same columns."""
    ids = _stack()
    assert ES.contact_columns(ids, 7, 9)
    assert ES.contact_columns(ids, 9, 7) == {}


def test_contact_columns_drops_a_column_that_crosses_too_often():
    ids = _stack()
    # one column where the two materials interleave — a fold seen end-on
    ids[:, 5] = np.where(np.arange(60) % 2 == 0, 7, 9)
    cols = ES.contact_columns(ids, 7, 9)
    assert 5 not in cols
    assert len(cols) == 199


def test_shadow_line_at_refuses_a_site_with_too_few_columns():
    """A sliver of contact is not a measurable site, and could-not-look must never
    print like a clean absence (R11)."""
    L = _edge(h=60, w=200)
    cols = {x: 21 for x in range(10)}
    with pytest.raises(ES.NoFeature):
        ES.shadow_line_at(L, cols)


def test_shadow_line_at_refuses_when_the_contact_has_no_transition_in_pixels():
    """THE DEFECT THIS FUNCTION EXISTS FOR. A site inside ONE flat material —
    exactly what the retired cloth_edge box was measuring, at 99.6% bed_throw —
    must raise rather than return a confident 0%."""
    flat = np.full((60, 200), 170.0)
    cols = {x: 28 for x in range(200)}
    with pytest.raises(ES.NoFeature):
        ES.shadow_line_at(flat, cols)


def test_shadow_line_at_separates_a_line_from_a_ramp_at_a_known_contact():
    cols = {x: 21 for x in range(200)}
    e_pct, e_med, e_n = ES.shadow_line_at(_edge(h=60, w=200), cols)
    r_pct, _, r_n = ES.shadow_line_at(_ramp(h=60, w=200), {x: 30 for x in range(200)})
    assert e_pct > 90.0 and e_med > 15.0 and e_n == 200
    assert r_pct < 5.0 and r_n == 200
    assert e_pct > 10 * max(r_pct, 1.0)


def test_a_window_centred_on_the_contact_does_not_wander_to_another_edge():
    """`shadow_line` takes the strongest gradient anywhere in the crop, so a second,
    stronger edge elsewhere in the box captures the reading. `shadow_line_at` is
    pinned to the named contact and cannot be pulled off it — which is the whole
    reason a derived site beats a typed box."""
    h, w = 90, 200
    img = np.full((h, w), 170.0)
    img[28:, :] = 200.0                     # the contact under test: a bare step
    img[70:72, :] = 40.0                    # a much stronger dark line further down
    at_contact = ES.shadow_line_at(img, {x: 27 for x in range(w)})[0]
    in_box = ES.shadow_line(img)[0]
    assert in_box > 90.0, "the strong decoy line dominates a box reading"
    assert at_contact < 5.0, "the named contact itself casts no line"
