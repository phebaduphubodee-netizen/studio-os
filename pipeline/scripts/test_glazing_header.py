"""test_glazing_header.py — the pelmet's geometry, under plain `python -m pytest`.

The tests that matter here are the ones that would have caught the two defects this
module actually had while it was being written: a return that ran 18 mm INSIDE the
blackout's swept envelope, and a run derived from the track path instead of from the
leg the fabric hangs on.
"""
import copy
import json
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curtains
import glazing_header as gh

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house", "03_layout",
                    "master-suite.CANONICAL.spec.json")


@pytest.fixture(scope="module")
def spec():
    with io.open(SPEC, encoding="utf-8") as fh:
        return json.load(fh)


def test_no_curtains_block_builds_nothing():
    parts, meta = gh.header_parts({"room": {"ceiling_mm": 2800}})
    assert parts == [] and meta["legs"] == 0


def test_one_board_per_leg(spec):
    parts, meta = gh.header_parts(spec)
    assert meta["legs"] == 3
    assert {p["name"] for p in parts} == {
        "pelmet__west_fascia", "pelmet__south_fascia", "pelmet__east_fascia"}


def test_hangs_from_the_ceiling_never_floats(spec):
    parts, meta = gh.header_parts(spec)
    ceil = spec["room"]["ceiling_mm"] * gh.MM
    for p in parts:
        assert p["z"] + p["dz"] == pytest.approx(ceil, abs=1e-9), p["name"]


def test_drop_is_the_declared_drop(spec):
    for drop in (100.0, 150.0, 300.0):
        parts, meta = gh.header_parts(spec, drop_mm=drop)
        assert meta["drop_mm"] == drop
        for p in parts:
            assert p["dz"] == pytest.approx(drop * gh.MM, abs=1e-9)


def test_ceiling_missing_raises_rather_than_floating(spec):
    s = copy.deepcopy(spec)
    s["room"].pop("ceiling_mm", None)
    with pytest.raises(gh.HeaderError, match="ceiling_mm"):
        gh.header_parts(s)


def test_bad_section_raises(spec):
    with pytest.raises(gh.HeaderError):
        gh.header_parts(spec, drop_mm=0)
    with pytest.raises(gh.HeaderError):
        gh.header_parts(spec, thick_mm=-1)


# ------------------------------------------------------------------ THE COLLISION --
def _front_face_from_glass(spec):
    """Where the frontmost fabric layer's swept envelope ends, measured from the glass
    — the authority is curtains._layer_offsets, not a number retyped here."""
    g = curtains.curtain_legs(spec)
    offs, _scale = curtains._layer_offsets(g["layers"], g["pocket"])
    _l, centre, amp = offs[-1]
    return centre + amp, g["pocket"]


def test_return_is_capped_by_the_fabric_not_by_its_constant(spec):
    """The bug this test exists for: RETURN_MM = 30 with only 10 mm of pocket air left
    room-side of the blackout put 18 mm of solid board through the cloth."""
    front, pocket = _front_face_from_glass(spec)
    free = pocket - front
    parts, meta = gh.header_parts(spec, return_mm=30.0)
    assert meta["pocket_free_room_side_mm"] == pytest.approx(free)
    assert meta["return_cap_mm"] == pytest.approx(max(0.0, free - gh.RETURN_CLEAR_MM))
    assert meta["return_mm"] <= meta["return_cap_mm"] + 1e-9
    # on THIS spec the cap (6 mm) is under RETURN_MIN_MM, so the return is dropped and
    # the dropping is disclosed rather than silent
    assert meta["return_mm"] == 0.0 and meta["return_dropped"] is True
    assert not any(p["name"].endswith("_return") for p in parts)


def test_return_appears_when_the_pocket_really_has_room(spec):
    """Positive control for the cap: widen the room-side air and the return comes back.
    A cap that can never be satisfied would pass the test above for the wrong reason."""
    s = copy.deepcopy(spec)
    s["curtains"]["layers"][0]["stack_depth_mm"] = 40   # was 85 (sheer)
    s["curtains"]["layers"][1]["stack_depth_mm"] = 60   # was 130 (blackout)
    parts, meta = gh.header_parts(s, return_mm=30.0)
    assert meta["return_cap_mm"] > gh.RETURN_MIN_MM
    assert meta["return_mm"] > 0.0 and meta["return_dropped"] is False
    assert any(p["name"].endswith("_return") for p in parts)


def test_no_board_intersects_the_fabric_envelope(spec):
    """Whole-module contact check: every board must stay room-side of the frontmost
    fabric face on its own leg, on whichever axis that leg runs."""
    g = curtains.curtain_legs(spec)
    front, pocket = _front_face_from_glass(spec)
    parts, _meta = gh.header_parts(spec, return_mm=30.0)
    by_leg = {leg["name"]: leg for leg in g["legs"]}
    for p in parts:
        leg = by_leg[p["name"].split("__")[1].rsplit("_", 1)[0]]
        fabric_face = leg["plane"] + leg["sign"] * front      # mm
        if leg["axis"] == "y":
            lo, hi = p["x"] / gh.MM, (p["x"] + p["dx"]) / gh.MM
        else:
            lo, hi = p["y"] / gh.MM, (p["y"] + p["dy"]) / gh.MM
        nearest = min(lo, hi) if leg["sign"] > 0 else max(lo, hi)
        gap = (nearest - fabric_face) * leg["sign"]
        assert gap >= 0.0, (f"{p['name']} crosses the fabric face by {-gap:.1f} mm "
                            f"(board at {lo:.1f}..{hi:.1f}, fabric {fabric_face:.1f})")


# ----------------------------------------------------------------- THE ONE SOURCE --
def test_run_comes_from_the_leg_not_from_the_track_path(spec):
    """The header must cover the leg — the trimmed track-vs-glass intersection — not
    the raw traced track, which overruns the glass on two legs of this very spec."""
    g = curtains.curtain_legs(spec)
    parts, _ = gh.header_parts(spec)
    for leg in g["legs"]:
        p = next(x for x in parts if x["name"] == f"pelmet__{leg['name']}_fascia")
        lo, hi = leg["drawn"]
        if leg["park"]:
            lo, hi = min(lo, leg["park"][0]), max(hi, leg["park"][1])
        run = (p["dy"] if leg["axis"] == "y" else p["dx"]) / gh.MM
        assert run == pytest.approx(hi - lo, abs=1e-6), leg["name"]


def test_header_covers_the_fabric_wherever_a_repark_can_put_it(spec):
    """A re-park must never slide the stack out from under its own board — so the run
    is the union of drawn and park, and is invariant under park_end_over_glass."""
    a, _ = gh.header_parts(spec)
    s = copy.deepcopy(spec)
    cur = s["curtains"]["render_state"]["park_end_over_glass"]["south"]
    s["curtains"]["render_state"]["park_end_over_glass"]["south"] = "lo" if cur == "hi" else "hi"
    b, _ = gh.header_parts(s)
    assert {p["name"]: (p["x"], p["dx"], p["y"], p["dy"]) for p in a} == \
           {p["name"]: (p["x"], p["dx"], p["y"], p["dy"]) for p in b}


def test_south_board_spans_the_whole_glass_wall(spec):
    """The complaint was a wall with no top. The south board must actually reach both
    ends of the south glazing, not stop where one opening does."""
    parts, _ = gh.header_parts(spec)
    p = next(x for x in parts if x["name"] == "pelmet__south_fascia")
    assert p["x"] <= 0.001 and p["x"] + p["dx"] >= 5.499


def test_units_are_metres(spec):
    parts, _ = gh.header_parts(spec)
    for p in parts:
        assert abs(p["z"]) < 10 and abs(p["dz"]) < 1, "metres, not millimetres"
