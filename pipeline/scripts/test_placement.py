"""Tests for placement.py — R9's contact resolver.

Most of these assert a RAISE. That is the point of the module: a position that
cannot be derived must stop the build, because the alternative is a default, and a
default is a typed coordinate with the typing hidden. This lane has already
shipped an asset that landed at the world origin while the build log reported it
placed, so "refuses to guess" is the load-bearing behaviour, not the happy path.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "specs", "trn001_blockout.json")


def m(name, cx, cy, cz, w=100.0, d=100.0, h=100.0):
    return {"name": name, "c": [cx, cy, cz], "s": [w, d, h]}


TABLE = PL.support_table([m("box", 0, 0, 50), m("ped", -800, -140, 300, 277, 285, 600)])


# ------------------------------------------------------------------- derives ---

def test_rest_on_gives_the_top_face_not_the_centre():
    x, y, z = PL.resolve({"rest_on": "box", "centre_on": "box"}, TABLE)
    assert (x, y, z) == (0, 0, 100)                     # centre 50 + half-height 50


def test_centre_on_gives_the_plan_centre():
    x, y, _ = PL.resolve({"rest_on": "ped", "centre_on": "ped"}, TABLE)
    assert (x, y) == (-800, -140)


def test_z_gap_is_explicit_and_additive():
    _, _, z = PL.resolve({"rest_on": "box", "centre_on": "box", "z_gap_mm": 3.0}, TABLE)
    assert z == 103.0


def test_mirror_about_puts_one_offset_on_two_sides():
    """ONE offset, two objects. Two independent x values is what let a symmetric
    pair drift apart one edit at a time."""
    base = {"rest_on": "box", "mirror_about": "box", "offset_x_mm": 920.9,
            "y_from": "box", "dy_mm": 10.5}
    l = PL.resolve(dict(base, side="L"), TABLE)
    r = PL.resolve(dict(base, side="R"), TABLE)
    assert l[0] == -920.9 and r[0] == 920.9
    assert l[1] == r[1] == 10.5                          # same y, by construction


def test_measured_offsets_are_relative_to_a_named_datum():
    x, y, _ = PL.resolve({"rest_on": "ped", "x_from": "ped", "dx_mm": 12.0,
                          "y_from": "ped", "dy_mm": -7.0}, TABLE)
    assert (x, y) == (-788.0, -147.0)


# --------------------------------------------------------------- fails closed ---

def test_an_unknown_support_raises_instead_of_defaulting():
    with pytest.raises(PL.PlacementError, match="not a mass"):
        PL.resolve({"rest_on": "nope", "centre_on": "box"}, TABLE, "vase_L")


def test_a_missing_rest_on_raises():
    with pytest.raises(PL.PlacementError, match="hold it up"):
        PL.resolve({"centre_on": "box"}, TABLE)


def test_an_undetermined_axis_raises():
    """The whole defect in one assertion: a silently defaulted axis IS a typed
    coordinate."""
    with pytest.raises(PL.PlacementError, match="undetermined"):
        PL.resolve({"rest_on": "box"}, TABLE, "fig")


def test_an_empty_or_absent_place_block_raises():
    for bad in ({}, None, "centre_box"):
        with pytest.raises(PL.PlacementError):
            PL.resolve(bad, TABLE)


def test_two_sources_for_one_axis_raise():
    """R9's own shape: one number asked to satisfy two relationships."""
    with pytest.raises(PL.PlacementError, match="claim x"):
        PL.resolve({"rest_on": "box", "centre_on": "box", "mirror_about": "box",
                    "side": "L", "offset_x_mm": 10}, TABLE)
    with pytest.raises(PL.PlacementError, match="claim x"):
        PL.resolve({"rest_on": "box", "centre_on": "box", "x_from": "box",
                    "dx_mm": 5}, TABLE)


def test_mirror_without_a_side_or_an_offset_raises():
    with pytest.raises(PL.PlacementError, match="side"):
        PL.resolve({"rest_on": "box", "mirror_about": "box", "offset_x_mm": 1,
                    "y_from": "box"}, TABLE)
    with pytest.raises(PL.PlacementError, match="offset_x_mm"):
        PL.resolve({"rest_on": "box", "mirror_about": "box", "side": "L",
                    "y_from": "box"}, TABLE)


@pytest.mark.parametrize("key", ["x_nudge_mm", "nudge", "y_fudge", "TWEAK_mm"])
def test_a_nudge_by_any_name_is_refused(key):
    """It is not the fix; it is the missing derivation wearing a knob. Banned by
    name so it cannot come back under a synonym."""
    with pytest.raises(PL.PlacementError, match="banned by R9"):
        PL.resolve({"rest_on": "box", "centre_on": "box", key: 33.4}, TABLE, "fig")


# -------------------------------------------------------------- containment ---

def test_contains_refuses_a_footprint_that_hangs_off_its_declared_support():
    place = {"rest_on": "box", "centre_on": "box"}
    pos = PL.resolve(place, TABLE)
    PL.contains(place, TABLE, (80.0, 80.0), pos, "ok")           # inside: fine
    with pytest.raises(PL.PlacementError, match="hangs"):
        PL.contains(place, TABLE, (140.0, 80.0), pos, "too wide")


# --------------------------------------------------- the live spec, converted ---

def test_the_live_spec_carries_no_typed_coordinate_and_no_nudge():
    """The conversion is only real if the old fields are GONE. Zeroing a nudge
    leaves the mechanism in place for the next round to reach for."""
    spec = json.load(open(SPEC, encoding="utf-8"))
    st = spec["styling"]
    for f in st["figures"]:
        assert "place" in f, f["name"]
        for dead in ("x_mm", "y_mm", "z_mm", "x_nudge_mm"):
            assert dead not in f, f"{f['name']} still types {dead}"
    for c in st["candlesticks"]:
        assert "place" in c
        assert not {"x_mm", "y_mm", "z_mm"} & set(c)
    assert "place" in st["vase_pair"]
    assert not {"y_mm", "z_mm"} & set(st["vase_pair"])


def test_every_declared_contact_resolves_and_lands_on_its_support():
    """End to end on the real spec: nothing raises, and every resolved prop sits
    within the plan extent of the mass it declares it stands on."""
    import trn001_geom as G
    import trn001_styling as S
    spec = json.load(open(SPEC, encoding="utf-8"))
    table = PL.support_table(G.masses(spec))
    st = spec["styling"]
    for f in st["figures"]:
        PL.resolve(f["place"], table, f["name"])
    for c in st["candlesticks"]:
        PL.resolve(c["place"], table, c["name"])
    for side in ("L", "R"):
        PL.resolve(dict(st["vase_pair"]["place"], side=side), table, f"vase_{side}")
    # and the figures really are contained by what they stand on
    got = {p["name"]: p for p in S.plan(spec)}
    for f in st["figures"]:
        sup = table[f["place"]["rest_on"]]
        x, y, _ = got[f["name"]]["pos_mm"]
        assert sup["x0"] <= x <= sup["x1"] and sup["y0"] <= y <= sup["y1"], f["name"]


def test_resizing_a_support_MOVES_what_stands_on_it():
    """THE POINT OF R9, as one assertion. Under typed coordinates, raising the
    centre box left the figure hanging in the air and nothing failed. Under a
    declared contact the figure follows, because its z was never a number."""
    import trn001_geom as G
    spec = json.load(open(SPEC, encoding="utf-8"))
    fig = next(f for f in spec["styling"]["figures"] if f["place"]["rest_on"] == "centre_box")
    before = PL.resolve(fig["place"], PL.support_table(G.masses(spec)), "fig")

    masses = [dict(m) for m in G.masses(spec)]
    for m_ in masses:
        if m_["name"] == "centre_box":
            m_["c"] = [m_["c"][0], m_["c"][1], m_["c"][2] + 50.0]
    after = PL.resolve(fig["place"], PL.support_table(masses), "fig")
    assert after[2] == before[2] + 50.0
    assert after[0] == before[0] and after[1] == before[1]
