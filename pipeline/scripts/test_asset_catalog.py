"""Tests for asset_catalog — the shelf inventory and the procurement number.

The negative controls are the ways an inventory lies: a model it could not read
counted as stock, a known cutout listed as usable, a whole-room export offered
for an object slot, and a guessed slot class dressed up as a measurement.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_catalog as AC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _dir(tmp, name, dims=None, licence=None, ext=".gltf"):
    d = tmp / name
    d.mkdir()
    if dims is not None:
        x, y, z = dims                                    # repo axes, metres
        doc = {"asset": {"version": "2.0"}, "scene": 0,
               "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
               "meshes": [{"primitives": [{"attributes": {"POSITION": 0},
                                           "indices": 1, "mode": 4}]}],
               # glTF is Y-up: repo z is glTF y.
               "accessors": [{"min": [0, 0, 0], "max": [x, z, y], "count": 8},
                             {"count": 36}]}
        (d / (name + ext)).write_text(json.dumps(doc), encoding="utf-8")
    if licence:
        (d / "SOURCE.json").write_text(json.dumps({"license": licence}), encoding="utf-8")
    return str(d)


# --- slot classes are read, never guessed --------------------------------------

def test_slot_comes_from_the_name_and_is_none_when_unreadable():
    assert AC.slot_of("ceramic_vase_01") == "styling"
    assert AC.slot_of("ArmChair_01") == "seating"
    assert AC.slot_of("ClassicNightstand_01") == "case"
    assert AC.slot_of("bd_c") is None


def test_an_unclassified_model_is_not_usable(tmp_path):
    r = AC.row("warehouse", _dir(tmp_path, "bd_c", (0.5, 0.5, 0.5)))
    assert r["verdict"] == "unclassified"
    assert "guessed class" in r["why"]


# --- the ways it must refuse ---------------------------------------------------

def test_a_model_it_cannot_read_is_unreadable_not_usable(tmp_path):
    d = tmp_path / "broken_vase"
    d.mkdir()
    (d / "broken_vase.gltf").write_text("{not json", encoding="utf-8")
    r = AC.row("cc0", str(d))
    assert r["verdict"] == "unreadable"
    assert "usable" not in r["verdict"]
    assert r["why"]


def test_an_empty_directory_is_unreadable(tmp_path):
    r = AC.row("cc0", _dir(tmp_path, "empty_vase"))
    assert r["verdict"] == "unreadable" and "no .gltf" in r["why"]


def test_a_cutout_is_refused_even_though_its_height_is_right(tmp_path):
    """THE PIN THAT JUSTIFIES THE PLANAR RUNG. The first catalog this module ever
    produced printed `shirt_hanger_a 616x12x715 usable` — a model asset_scale had
    already refused as a billboard a round earlier. A fresh guard that drops a
    rung an older one had is the flattering-scorer shape."""
    r = AC.row("warehouse", _dir(tmp_path, "shirt_hanger_a", (0.616, 0.012, 0.715)))
    assert r["verdict"] == "planar"
    assert r["thinnest_over_longest"] < AC.MIN_DEPTH_RATIO


def test_a_whole_room_export_is_out_of_band_with_the_reason_named(tmp_path):
    r = AC.row("warehouse", _dir(tmp_path, "bd_chair", (18.0, 16.2, 25.5)))
    assert r["verdict"] == "out-of-band"
    assert "scales uniformly and" in r["why"]


def test_something_too_small_to_be_its_name_is_out_of_band(tmp_path):
    r = AC.row("cc0", _dir(tmp_path, "tiny_vase", (0.02, 0.02, 0.03)))
    assert r["verdict"] == "out-of-band"


# --- measurement ---------------------------------------------------------------

def test_bounds_and_triangles_are_read_without_the_binary(tmp_path):
    d = _dir(tmp_path, "ceramic_vase_09", (0.2, 0.2, 0.4))
    assert not os.path.exists(os.path.join(d, "ceramic_vase_09.bin"))
    r = AC.row("cc0", d)
    assert r["verdict"] == "usable"
    assert r["bounds_mm"]["z_mm"] == pytest.approx(400.0)
    assert r["tris"] == 12


def test_licence_is_read_from_source_json_and_defaults_only_for_cc0(tmp_path):
    a = AC.row("warehouse", _dir(tmp_path, "th_x", (0.5, 0.5, 0.5), licence="Trimble GML"))
    assert a["licence"] == "Trimble GML"
    b = AC.row("cc0", _dir(tmp_path, "ceramic_vase_77", (0.2, 0.2, 0.4)))
    assert "CC0" in b["licence"]
    c = AC.row("warehouse", _dir(tmp_path, "th_y", (0.5, 0.5, 0.5)))
    assert c["licence"] is None, "an unknown licence must not default to a permissive one"


# --- the procurement number ----------------------------------------------------

def test_shortfall_counts_styling_only():
    rows = [{"verdict": "usable", "slot": "styling", "slug": "v1"},
            {"verdict": "usable", "slot": "styling", "slug": "v2"},
            {"verdict": "usable", "slot": "seating", "slug": "chair"},
            {"verdict": "planar", "slot": "styling", "slug": "cutout"}]
    sf = AC.shortfall(rows, need=12)
    assert sf["usable_styling"] == 2 and sf["styling_short_by"] == 10
    assert "cutout" not in sf["usable_styling_slugs"]
    assert sf["usable_total"] == 3


# --- and the real shelf --------------------------------------------------------

@pytest.mark.skipif(not os.path.isdir(AC.SHELVES["cc0"]), reason="shelf not on this machine")
def test_the_real_shelf_reports_the_shortfall_that_goes_to_the_owner():
    rows = AC.build()
    assert len(rows) >= 29
    sf = AC.shortfall(rows)
    assert sf["styling_short_by"] > 0, ("if this ever reaches zero, D7 is satisfiable "
                                        "from stock and the procurement ask is closed")
    assert all(r["verdict"] != "usable" or r.get("bounds_mm") for r in rows)


@pytest.mark.skipif(not os.path.isdir(AC.SHELVES["warehouse"]), reason="shelf not on this machine")
def test_the_known_cutout_on_the_real_shelf_is_not_listed_as_stock():
    rows = {r["slug"]: r for r in AC.build()}
    if "shirt_hanger_a" in rows:
        assert rows["shirt_hanger_a"]["verdict"] == "planar"


# --- the field that was write-only until 2026-08-10 -------------------------------

def test_catalog_slot_reads_the_field_the_acquire_path_needs(tmp_path):
    """This module's docstring says the catalog is what "P2's acquire step reads".
    Nothing read it, and `millwork.model_fit` — the acquire path's only gate — took
    six numbers and no class at all."""
    f = tmp_path / "CATALOG.json"
    f.write_text(json.dumps({"models": [
        {"slug": "ArmChair_01", "slot": "seating"},
        {"slug": "ClassicNightstand_01", "slot": "case"}]}), encoding="utf-8")
    assert AC.catalog_slot("ArmChair_01", str(f)) == "seating"
    assert AC.catalog_slot("ClassicNightstand_01", str(f)) == "case"
    assert AC.catalog_slot("not_on_the_shelf", str(f)) is None


def test_an_unreadable_catalog_is_none_not_a_guess(tmp_path):
    """None means "the class is unknown", which model_fit reports rather than
    treating as a match. A guessed class would be worse than no class."""
    assert AC.catalog_slot("ArmChair_01", str(tmp_path / "missing.json")) is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert AC.catalog_slot("ArmChair_01", str(bad)) is None


def test_a_spec_kind_resolves_through_the_same_vocabulary():
    """No second map: a spec kind and an asset slug are both words, and SLOT_WORDS
    already answers what class a word names."""
    assert AC.kind_slot("stool") == "seating"
    assert AC.kind_slot("side_table") == "case"
    assert AC.kind_slot("bed") == "bed"
    assert AC.kind_slot("bench") == "seating"
    assert AC.kind_slot("rug") is None        # not a class this vocabulary names
    assert AC.kind_slot(None) is None
