"""Tests for model_assert_check — the rung that made a model's size DATA.

The suite is built around ONE negative control, and it is not hypothetical: it
is p2r36, replayed. The spec asserted 2198.1 mm on y for `ub806591a` — the size
of `2b142a32`, the candidate this lane rejected — while that file's own sidecar
read 1599.9 mm and was correct throughout. `test_the_p2r36_defect_is_refused`
fails if that combination is ever green again.

Everything is built on SYNTHETIC glTF written into a temp repo root: the real
warehouse shelf is a gitignored cache (docs/LICENSING.md), so a suite that read
it would pass or fail depending on what somebody had fetched. A fixture that
depends on an uncommitted download is not a test.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_scale as A            # noqa: E402
import model_assert_check as MA    # noqa: E402


# --------------------------------------------------------------- the fixtures --

def _gltf(x_mm, y_mm, z_mm, prims=1, with_bounds=True):
    """A minimal glTF document whose bounds are exactly (x, y, z) mm in REPO
    axes. glTF is Y-up and this repo is Z-up, so the file's y is our z."""
    prim = {"attributes": {"POSITION": 0}}
    acc = {"componentType": 5126, "count": 2, "type": "VEC3"}
    if with_bounds:
        acc["min"] = [0.0, 0.0, 0.0]
        acc["max"] = [x_mm / 1000.0, z_mm / 1000.0, y_mm / 1000.0]
    return {"asset": {"version": "2.0"},
            "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [dict(prim) for _ in range(prims)]}],
            "accessors": [acc]}


def _shelf(root, slug, x_mm, y_mm, z_mm, cls, axis, prims=1,
           sidecar=True, with_bounds=True, **sc_over):
    d = os.path.join(root, "assets", "shared", "warehouse", slug)
    os.makedirs(d, exist_ok=True)
    mp = os.path.join(d, slug + ".gltf")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(_gltf(x_mm, y_mm, z_mm, prims, with_bounds), f)
    if sidecar:
        band = A.BANDS[cls]
        meas = {"x": x_mm, "y": y_mm, "z": z_mm,
                "maxxy": max(x_mm, y_mm)}[axis]
        sc = {"file": slug + ".gltf", "class": cls, "axis": axis,
              "measured_mm": round(meas, 1), "band_mm": [band[0], band[1]],
              "ok": True, "in_band": True,
              "thinnest_over_longest": 0.5,
              "min_ratio_for_class": A.MIN_DEPTH_RATIO.get(cls),
              "planar_refusal": None,
              "bbox_mm": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": z_mm},
              "prims": prims, "source": "test", "in_band_under": None}
        sc.update(sc_over)
        with open(os.path.join(d, slug + ".scale.json"), "w",
                  encoding="utf-8") as f:
            json.dump(sc, f)
    return mp


BED = {"kind": "bed", "name": "bed", "x": 0, "y": 0, "w": 2000, "d": 2149,
       "h": 600}


def _spec(asserted_mm=1599.9, **row_over):
    row = {"class": "bedding_set", "axis": "y", "asserted_mm": asserted_mm}
    row.update(row_over)
    return {"items": [dict(BED, bed_models={"cloth_set": "cloth"})],
            "model_assertions": {"cloth": row}}


@pytest.fixture
def repo(tmp_path):
    """A repo root holding ONE cloth asset that measures 1599.9 on y — the real
    ub806591a's numbers, which is what makes the negative control the real one."""
    _shelf(str(tmp_path), "cloth", 1505.4, 1599.9, 396.8, "bedding_set", "y",
           prims=6)
    return str(tmp_path)


# ------------------------------------------------------------------- the pass --

def test_a_matching_row_passes_and_prints_a_line(repo):
    v, lines = MA.check(_spec(), repo)
    assert v == []
    assert len(lines) == 1
    # the line has to carry all three legs, or a reader cannot audit the diff
    assert "sidecar=1599.9" in lines[0] and "live=1599.9" in lines[0]
    assert "items[0].bed_models.cloth_set" in lines[0]


def test_a_spec_with_no_models_needs_no_block(repo):
    v, lines = MA.check({"items": [dict(BED)]}, repo)
    assert v == []


# --------------------------------------------------- THE p2r36 NEGATIVE CONTROL --

def test_the_p2r36_defect_is_refused(repo):
    """The spec asserts the REJECTED candidate's size; the file says otherwise."""
    v, lines = MA.check(_spec(asserted_mm=2198.1), repo)
    assert len(v) >= 1
    joined = " ".join(v)
    assert "2198.1" in joined and "1599.9" in joined
    assert "p2r36" in joined            # the finding is named, not just the delta


def test_a_reference_with_no_row_fails(repo):
    s = _spec()
    del s["model_assertions"]["cloth"]
    v, _ = MA.check(s, repo)
    assert any("no row" in x for x in v)


def test_an_orphan_row_fails_by_name(repo):
    """A row nothing points at is how a rejected candidate's numbers survive."""
    s = _spec()
    s["model_assertions"]["ghost"] = {"class": "bedding_set", "axis": "y",
                                      "asserted_mm": 2198.1}
    v, _ = MA.check(s, repo)
    assert any("ORPHAN" in x.upper() or "no reference" in x for x in v)


def test_a_spec_with_models_and_no_block_fails(repo):
    s = _spec()
    del s["model_assertions"]
    v, _ = MA.check(s, repo)
    assert v and "model_assertions" in v[0]


# ------------------------------------------------------- the file's own honesty --

def test_missing_sidecar_fails_closed(tmp_path):
    _shelf(str(tmp_path), "cloth", 1505.4, 1599.9, 396.8, "bedding_set", "y",
           sidecar=False)
    v, lines = MA.check(_spec(), str(tmp_path))
    assert any("sidecar" in x for x in v)
    assert "NO SIDECAR" in lines[0]


def test_a_sidecar_about_another_file_fails(repo):
    d = os.path.join(repo, "assets", "shared", "warehouse", "cloth")
    p = os.path.join(d, "cloth.scale.json")
    sc = json.load(open(p, encoding="utf-8"))
    sc["file"] = "2b142a32.glb"
    json.dump(sc, open(p, "w", encoding="utf-8"))
    v, _ = MA.check(_spec(), repo)
    assert any("2b142a32" in x for x in v)


def test_a_refused_ingest_may_not_be_referenced(repo):
    p = os.path.join(repo, "assets", "shared", "warehouse", "cloth",
                     "cloth.scale.json")
    sc = json.load(open(p, encoding="utf-8"))
    sc["ok"] = False
    json.dump(sc, open(p, "w", encoding="utf-8"))
    v, _ = MA.check(_spec(), repo)
    assert any("REFUSED at ingest" in x for x in v)


def test_a_narrowed_band_reopens_the_ingest(repo):
    p = os.path.join(repo, "assets", "shared", "warehouse", "cloth",
                     "cloth.scale.json")
    sc = json.load(open(p, encoding="utf-8"))
    sc["band_mm"] = [1000.0, 4000.0]          # the band this ingest passed under
    json.dump(sc, open(p, "w", encoding="utf-8"))
    v, _ = MA.check(_spec(), repo)
    assert any("band" in x and "in force" in x for x in v)


def test_swapping_the_file_under_the_slug_is_caught_live(repo):
    """The sidecar and the spec agree with each other and BOTH are stale."""
    d = os.path.join(repo, "assets", "shared", "warehouse", "cloth")
    with open(os.path.join(d, "cloth.gltf"), "w", encoding="utf-8") as f:
        json.dump(_gltf(1505.4, 2198.1, 396.8, prims=6), f)
    v, _ = MA.check(_spec(), repo)
    assert any("RIGHT NOW" in x for x in v)


def test_a_changed_primitive_count_is_caught(repo):
    d = os.path.join(repo, "assets", "shared", "warehouse", "cloth")
    with open(os.path.join(d, "cloth.gltf"), "w", encoding="utf-8") as f:
        json.dump(_gltf(1505.4, 1599.9, 396.8, prims=68), f)
    v, _ = MA.check(_spec(), repo)
    assert any("primitive" in x for x in v)


def test_could_not_measure_is_not_a_pass(tmp_path):
    """R11's law: 'could not look' must never print like 'looked and it was
    fine'. A glTF whose accessors carry no min/max cannot be measured at all."""
    _shelf(str(tmp_path), "cloth", 1505.4, 1599.9, 396.8, "bedding_set", "y",
           prims=6, with_bounds=False)
    v, lines = MA.check(_spec(), str(tmp_path))
    assert any("COULD NOT MEASURE" in x for x in v)
    assert "COULD-NOT-MEASURE" in lines[0]


def test_an_unknown_class_fails_closed(repo):
    v, _ = MA.check(_spec(**{"class": "chaise_we_never_declared"}), repo)
    assert any("no band" in x for x in v)


def test_a_missing_file_is_a_violation_not_a_skip(tmp_path):
    v, lines = MA.check(_spec(), str(tmp_path))
    assert any("neither shelf" in x for x in v)
    assert "NO FILE" in lines[0]


# ---------------------------------------------------------------- discovery --

def test_discovery_finds_a_slug_under_a_key_not_called_model(repo):
    """R9b: a rule that names the objects it applies to exempts the next one.
    The VALUE detector does not care what the key is called."""
    found = dict((s, g) for s, g in
                 MA.discover({"soft_goods": {"whatever": "cloth"}}, repo))
    assert found == {"soft_goods.whatever": "cloth"}


def test_discovery_ignores_prose_notes(repo):
    """The note is where the wrong number used to live; it must never be read
    as data again — even when it quotes a slug."""
    spec = {"bed_models_note": "we rejected cloth and 2b142a32 before that"}
    assert MA.discover(spec, repo) == []


def test_a_model_key_pointing_at_nothing_is_still_discovered(tmp_path):
    """Key shape alone is enough: a deleted asset must be REPORTED absent, not
    silently dropped from the scope by the detector that resolves paths."""
    found = MA.discover({"items": [{"model": "gone"}]}, str(tmp_path))
    assert found == [("items[0].model", "gone")]


def test_caller_supplied_refs_are_checked_like_spec_refs(repo):
    """build_room hard-codes two decor slugs; they import through the same door.
    An extra with a row passes; the same extra with no row fails exactly as a
    spec reference would."""
    row = {"class": "bedding_set", "axis": "y", "asserted_mm": 1599.9}
    ok = {"model_assertions": {"cloth": row}}
    v, lines = MA.check(ok, repo, extra=[("build_room._DECOR", "cloth")])
    assert v == [] and len(lines) == 1
    v2, _ = MA.check({"model_assertions": {}}, repo,
                     extra=[("build_room._DECOR", "cloth")])
    assert any("no row" in x for x in v2)


# ------------------------------------------------------------------- covers --

def test_a_duvet_too_small_for_its_bed_is_refused(repo):
    """The half a band structurally cannot answer. 1599.9 mm is the right UNIT
    and the wrong SIZE: 1505 x 1600 cannot cover a 1820 x 1969 mattress."""
    v, _ = MA.check(_spec(covers={"item": 0, "inset_mm": 90}, max_scale=1.0),
                    repo)
    assert any("1.231x" in x for x in v)


def test_a_big_enough_set_passes_the_same_clause(tmp_path):
    _shelf(str(tmp_path), "cloth", 2184.0, 2331.1, 625.8, "bedding_set", "y",
           prims=14)
    s = _spec(asserted_mm=2331.1, covers={"item": 0, "inset_mm": 90},
              max_scale=1.0)
    v, _ = MA.check(s, str(tmp_path))
    assert v == []


def test_covers_aimed_at_the_wrong_item_is_refused(repo):
    s = _spec(covers={"item": 1, "inset_mm": 90}, max_scale=1.0)
    s["items"].append({"kind": "stool", "name": "s", "x": 0, "y": 0,
                       "w": 510, "d": 546, "h": 750})
    v, _ = MA.check(s, repo)
    assert any("aimed at" in x for x in v)


def test_a_site_requirement_binds_a_row_that_omits_it(repo):
    """A row may not opt out of the site's rule by not mentioning it."""
    s = _spec()                                    # no covers on the row itself
    s["model_requirements"] = {
        "items[0].bed_models.cloth_set": {"class": "bedding_set",
                                          "covers": {"item": 0, "inset_mm": 90},
                                          "max_scale": 1.0}}
    v, _ = MA.check(s, repo)
    assert any("1.231x" in x for x in v)


def test_a_row_contradicting_its_site_is_refused(repo):
    s = _spec()
    s["model_requirements"] = {"items[0].bed_models.cloth_set":
                               {"class": "rug"}}
    v, _ = MA.check(s, repo)
    assert any("REQUIRES class='rug'" in x for x in v)


def test_an_unfilled_site_prints_and_does_not_block(repo):
    """The requirement outlives the asset. ub806591a was removed for being too
    small; a rule that lived on its row would have gone with it, and the next
    audition would have inherited nothing."""
    s = {"items": [dict(BED)],
         "model_requirements": {"items[0].bed_models.cloth_set":
                                {"class": "bedding_set",
                                 "covers": {"item": 0, "inset_mm": 90},
                                 "max_scale": 1.0}}}
    v, lines = MA.check(s, repo)
    assert v == []
    assert len(lines) == 1 and "NO MODEL YET" in lines[0]
    assert "bedding_set" in lines[0]


def test_covers_tracks_the_bed_instead_of_copying_it(repo):
    """R9: the requirement is DERIVED, so re-drawing the bed re-aims it. Shrink
    the bed to something the same asset CAN cover and the violation goes away
    with no second number to edit."""
    s = _spec(covers={"item": 0, "inset_mm": 90}, max_scale=1.0)
    assert MA.check(s, repo)[0]
    s["items"][0]["w"], s["items"][0]["d"] = 1600, 1700
    assert MA.check(s, repo)[0] == []
