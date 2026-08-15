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
    """The live numbers this module was derived from, pinned as a regression:
    acquired hem 95.0% vs our coverlet 2.8% against a 93.7% control."""
    sites = [
        {"name": "bed base meets floor", "pct": 93.7, "med": 39.3, "n": 395, "control": True},
        {"name": "pillow flange", "pct": 95.0, "med": 23.0, "n": 200},
        {"name": "coverlet boundary", "pct": 2.8, "med": 2.9, "n": 142},
    ]
    rows, _ = ES.verdict(sites)
    calls = {s["name"]: call for s, call, _ in rows}
    assert calls["pillow flange"] == "READS AS AN EDGE"
    assert calls["coverlet boundary"].startswith("NO LINE")
