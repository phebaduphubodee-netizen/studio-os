"""Known-answer tests for the D11 made-bed derivations.

Why these exist: the note built on this script quotes ~400 numbers, and a study note
is judged by opposing verifiers reading the note — nobody re-derives the DEFINITIONS.
A definition that quietly computes something else than it says would pass every one of
those rounds. So each metric is checked here against a hand-computed answer on a
synthetic dump, and the two role disputes are checked to be present in the output
(they are the difference between a number and a number that may be used).
"""
import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import madebed_study_derive as M  # noqa: E402


def _obj(name, lo, hi, verts=100, quads=0, tris=0, ngons=0, area=1.0, mats=()):
    return {
        "name": name, "type": "MESH",
        "world_bbox_mm": {"min": list(lo), "max": list(hi)},
        "dims_mm": [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]],
        "loc_mm": [0.0, 0.0, 0.0], "rot_deg": [0, 0, 0], "scale": [1, 1, 1],
        "modifiers": [], "materials": list(mats),
        "mesh": {"verts": verts, "polys": quads + tris + ngons, "quads": quads,
                 "tris": tris, "ngons": ngons, "area_m2": area,
                 "verts_per_m2": verts / area if area else 0.0, "mesh_users": 1,
                 "shape_keys": 0, "smooth_share": 1.0, "uv_layers": 1,
                 "uv_layer_names": [], "vertex_groups": 0},
    }


def test_edge_proxy_counts_two_tris_as_one_quad():
    """1 m2 over 200 tris = 100 quad-equivalents -> 100 mm. The pre-2026-09-02 form
    divided total polys by two only when tris outnumbered quads, which scored a mixed
    mesh (the 2767f3fa bolster: 9,331 quads + 1,356 tris) 3.2% fine."""
    assert M.edge_proxy_mm(_obj("t", (0, 0, 0), (1, 1, 1), tris=200, area=1.0)) == pytest.approx(100.0)
    assert M.edge_proxy_mm(_obj("q", (0, 0, 0), (1, 1, 1), quads=100, area=1.0)) == pytest.approx(100.0)
    mixed = _obj("m", (0, 0, 0), (1, 1, 1), quads=50, tris=100, area=1.0)
    assert M.edge_proxy_mm(mixed) == pytest.approx(100.0)          # 50 + 100/2 = 100
    assert M.edge_proxy_mm(mixed) != pytest.approx(math.sqrt(1.0 / 150) * 1000.0)


def test_edge_proxy_survives_a_dump_with_no_face_breakdown():
    o = _obj("x", (0, 0, 0), (1, 1, 1), area=1.0)
    o["mesh"]["polys"] = 25
    assert M.edge_proxy_mm(o) == pytest.approx(200.0)


def test_edge_proxy_is_not_the_repo_median_edge():
    """Guard against the two metrics being merged. bedcloth_fit.edge_mm reads the mesh
    EDGE LIST (needs bpy, absent from a dump); this one reads area per face. If someone
    ever makes this module import that one, this test says why not."""
    src = open(M.__file__, encoding="utf-8").read()
    code = src.split('"""', 2)[2]          # everything after the module docstring
    assert "import bedcloth_fit" not in code and "from bedcloth_fit" not in code, \
        "derive must stay dump-only — importing the bpy-side metric would make it unrunnable"
    # the bare name may appear in prose explaining the difference, but never as an
    # identifier the code defines or writes into the artifact
    ident = code.replace("edge_proxy_mm", "").replace("bedcloth_fit.edge_mm", "")
    assert "edge_mm" not in ident, "the ambiguous name is back as an identifier"


def test_loft_hem_and_pillow_offsets_are_measured_from_the_named_planes(tmp_path, monkeypatch):
    """mattress top 500, layer top 540 -> loft +40; set floor -10, layer min 90 -> hem 100."""
    dump = {
        "source": "blend", "images": [{"name": "a", "size": [2048, 2048]},
                                      {"name": "b", "size": [512, 256]},
                                      {"name": "c", "size": [2048, 2048]}],
        "materials": [{"name": "M1", "principled": {"Sheen Weight": 0.2, "Roughness": 1.0},
                       "node_hist": {"BSDF_PRINCIPLED": 1}}],
        "objects": [
            _obj("Matt", (0, 0, 200), (1000, 2000, 500), quads=100, area=2.0, mats=["M1"]),
            _obj("Deep", (0, 0, -10), (10, 10, 0)),          # the set's lowest mesh
            _obj("Cloth", (0, 0, 90), (1000, 2000, 540), quads=100, area=4.0, mats=["M1"]),
            _obj("Pill", (0, 0, 480), (500, 300, 800), quads=50, area=1.0, mats=["M1"]),
        ],
    }
    study = tmp_path / "_study"
    study.mkdir()
    (study / "zz111111-x.probe.json").write_text(json.dumps(dump), encoding="utf-8")
    (study / "_ours_p2r91.probe.json").write_text(json.dumps(
        {"source": "blend", "images": [], "materials": [],
         "objects": [_obj("bed__cloth__acq0", (0, 0, 0), (1, 1, 1), quads=4, area=1.0)]}), encoding="utf-8")
    out = tmp_path / "out.json"
    monkeypatch.setattr(M, "STUDY", str(study))
    monkeypatch.setattr(M, "OUT", str(out))
    monkeypatch.setattr(M, "SETS", {"zz111111": ("synthetic", "Matt", ["Cloth"], ["Pill"])})
    monkeypatch.setattr(M, "PILLOW_SETS", {})
    monkeypatch.setattr(M, "OURS", ["bed__cloth__acq0"])
    M.main()
    got = json.loads(out.read_text(encoding="utf-8"))["sets"]["zz111111"]

    assert got["mattress"]["thick"] == 300
    assert got["bed_min_z"] == -10.0
    layer = got["layers"][0]
    assert layer["loft_over_mattress_top"] == 40          # 540 - 500
    assert layer["hem_above_floor"] == 100                # 90 - (-10)
    assert layer["surplus"] == 2.0                        # 4.0 m2 over a 1.0 x 2.0 m plan
    pillow = got["pillows"][0]
    assert pillow["top_over_mattress_top"] == 300         # 800 - 500
    assert pillow["bottom_over_mattress_top"] == -20      # 480 - 500
    assert got["image_sizes"] == [[2048, 2048, 2], [512, 256, 1]]
    assert got["n_images"] == 3


def test_find_refuses_an_ambiguous_prefix_rather_than_guessing():
    d = {"objects": [_obj("sheet 01", (0, 0, 0), (1, 1, 1)), _obj("sheet 02", (0, 0, 0), (1, 1, 1))]}
    with pytest.raises(KeyError):
        M.find(d, "sheet")
    assert M.find(d, "sheet 01" if False else "sheet 01")["name"] == "sheet 01"


def test_find_prefers_an_exact_match_over_a_prefix_sibling():
    d = {"objects": [_obj("blanquet.001", (0, 0, 0), (1, 1, 1)),
                     _obj("blanquet", (0, 0, 0), (2, 2, 2))]}
    assert M.find(d, "blanquet")["dims_mm"] == [2, 2, 2]


def test_census_carries_the_whole_asset_prefix():
    """It was truncated to 8 chars, so every bk_daxing/bk_phoenix/bk_stansted row read
    'bk_daxin' and a filter written against the real prefix silently matched nothing —
    which is exactly how the first sheen census of this study came out wrong."""
    src = open(M.__file__, encoding="utf-8").read()
    assert "pre[:8]" not in src


def test_role_disputes_reach_the_artifact():
    assert set(M.ROLE_DISPUTES) == {"afcfd29e/Mattress", "ee42aa0e/Bed.008+Bed.009"}
    real = os.path.join(M.REPO, "qa", "blenderkit-study-madebed.json")
    if os.path.exists(real):
        got = json.load(open(real, encoding="utf-8"))
        assert got["_role_disputes"] == M.ROLE_DISPUTES
