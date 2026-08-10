"""Tests for asset_scale.py.

The synthetic GLBs are built here rather than committed as fixtures: a fixture
binary is a thing nobody reads, and the failure this module exists to catch is a
UNIT error, which is one multiply away from a passing file. Building them makes
the wrong-unit case a one-line edit instead of a new binary.
"""
import json
import math
import os
import struct
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_scale as A


def _glb(tmp, name, nodes, meshes, accessors, scene_roots=None):
    gl = {"asset": {"version": "2.0"}, "accessors": accessors,
          "meshes": meshes, "nodes": nodes,
          "scenes": [{"nodes": scene_roots if scene_roots is not None
                      else list(range(len(nodes)))}], "scene": 0}
    blob = json.dumps(gl).encode("utf-8")
    blob += b" " * ((4 - len(blob) % 4) % 4)
    body = struct.pack("<II", len(blob), 0x4E4F534A) + blob
    path = os.path.join(str(tmp), name)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    return path


def _boxglb(tmp, name, size_m, translate=None, rot=None, scale=None):
    """One box of the given size in glTF axes (x, y=up, z)."""
    hx, hy, hz = (s / 2 for s in size_m)
    acc = [{"type": "VEC3", "componentType": 5126, "count": 8,
            "min": [-hx, -hy, -hz], "max": [hx, hy, hz]}]
    node = {"mesh": 0}
    if translate:
        node["translation"] = list(translate)
    if rot:
        node["rotation"] = list(rot)
    if scale:
        node["scale"] = list(scale)
    return _glb(tmp, name, [node], [{"primitives": [{"attributes": {"POSITION": 0}}]}], acc)


# --------------------------------------------------------------- bounds --
def test_metres_become_millimetres_and_axes_are_repo_axes(tmp_path):
    # glTF is Y-up; the repo is Z-up. A 0.6 x 1.1 x 0.2 (x, up, depth) shirt
    # must come back as z=1100 (height) and y=200 (depth), not the other way.
    p = _boxglb(tmp_path, "a.glb", (0.6, 1.1, 0.2))
    b = A.bounds_mm(p)
    assert b["x_mm"] == pytest.approx(600.0)
    assert b["z_mm"] == pytest.approx(1100.0)
    assert b["y_mm"] == pytest.approx(200.0)


def test_node_scale_is_applied(tmp_path):
    p = _boxglb(tmp_path, "b.glb", (1.0, 1.0, 1.0), scale=(0.0254, 0.0254, 0.0254))
    assert A.bounds_mm(p)["z_mm"] == pytest.approx(25.4)


def test_rotation_uses_all_eight_corners(tmp_path):
    # A flat plate rotated 45 deg about x: its Z-up extent must GROW. Transform
    # only two corners and this comes back unchanged, which is the bug the
    # eight-corner loop exists to prevent.
    s = math.sin(math.pi / 8), math.cos(math.pi / 8)
    p = _boxglb(tmp_path, "c.glb", (1.0, 0.1, 1.0), rot=(s[0], 0.0, 0.0, s[1]))
    assert A.bounds_mm(p)["z_mm"] > 700.0


def test_child_inherits_parent_transform(tmp_path):
    acc = [{"type": "VEC3", "componentType": 5126, "count": 8,
            "min": [-0.05, -0.05, -0.05], "max": [0.05, 0.05, 0.05]}]
    nodes = [{"children": [1], "scale": [10.0, 10.0, 10.0]}, {"mesh": 0}]
    p = _glb(tmp_path, "d.glb", nodes,
             [{"primitives": [{"attributes": {"POSITION": 0}}]}], acc, scene_roots=[0])
    assert A.bounds_mm(p)["z_mm"] == pytest.approx(1000.0)


def test_missing_min_max_raises_rather_than_guessing(tmp_path):
    acc = [{"type": "VEC3", "componentType": 5126, "count": 8}]
    p = _glb(tmp_path, "e.glb", [{"mesh": 0}],
             [{"primitives": [{"attributes": {"POSITION": 0}}]}], acc)
    with pytest.raises(ValueError, match="min/max"):
        A.bounds_mm(p)


def test_not_a_glb_raises(tmp_path):
    path = os.path.join(str(tmp_path), "f.glb")
    with open(path, "wb") as f:
        f.write(b"NOPE" + b"\x00" * 16)
    with pytest.raises(ValueError, match="not a binary glTF"):
        A.bounds_mm(path)


# ------------------------------------------------------------ assertion --
def test_in_band_passes(tmp_path):
    p = _boxglb(tmp_path, "g.glb", (0.55, 1.10, 0.20))
    ok, rep = A.assert_scale(p, "garment_hung")
    assert ok and rep["measured_mm"] == pytest.approx(1100.0)
    assert rep["in_band_under"] is None


def test_imperial_export_is_caught_AND_named(tmp_path):
    # The DR's named trap: authored in metres, exported as if inches. 1100 mm
    # of shirt arrives as 43.3. Catching it is half the job; saying WHICH
    # multiplier would land in band is what makes it actionable.
    p = _boxglb(tmp_path, "h.glb", (0.0217, 0.0433, 0.0079))
    ok, rep = A.assert_scale(p, "garment_hung")
    assert not ok
    assert "x25.4" in rep["in_band_under"]


def test_a_cutout_is_refused_even_though_its_height_is_right(tmp_path):
    # THE REAL CASE. The lane's first fetched asset: 715 mm tall, in band, and
    # 11.7 mm deep. Scale alone calls this fine.
    p = _boxglb(tmp_path, "i.glb", (0.616, 0.715, 0.0117))
    ok, rep = A.assert_scale(p, "garment_hung")
    assert rep["in_band"] is True
    assert not ok
    assert "CUTOUT" in rep["planar_refusal"]


def test_a_class_with_no_planar_floor_is_not_silently_exempt(tmp_path):
    # `None` must mean DECLARED-planar, and a class absent from the table must
    # not read as exempt by accident. Every band has an explicit entry.
    assert set(A.MIN_DEPTH_RATIO) == set(A.BANDS), (
        "every band needs an explicit planar floor (or a declared None) — an "
        "absent key makes 'exempt' and 'unchecked' look identical")


def test_unknown_class_raises_and_does_not_pass(tmp_path):
    p = _boxglb(tmp_path, "j.glb", (0.5, 0.5, 0.5))
    with pytest.raises(KeyError, match="no scale band"):
        A.assert_scale(p, "lamp_we_never_declared")


def test_every_band_carries_a_source(tmp_path):
    for cls, (lo, hi, axis, src) in A.BANDS.items():
        assert lo < hi, cls
        assert axis in ("x", "y", "z"), cls
        assert src and len(src) > 20, f"{cls}: a band with no cited source is a preference"


def test_cli_returns_nonzero_when_it_refuses(tmp_path):
    p = _boxglb(tmp_path, "k.glb", (0.616, 0.715, 0.0117))
    assert A.main([p, "garment_hung"]) == 1
    q = _boxglb(tmp_path, "l.glb", (0.55, 1.10, 0.20))
    assert A.main([q, "garment_hung"]) == 0


# ------------------------------------------------- the OTHER container form --
# Added 2026-08-09. This module read only the BINARY form, and every Poly Haven
# asset on the shelf ships the other one — a JSON .gltf beside an external .bin.
# All 13 raised "not a binary glTF" on ingest, so the scale assertion that
# pipeline/CLAUDE.md calls a MUST was dead for the whole CC0 shelf while reading
# like a working guard. Nothing caught it because nothing had ever ingested one.

CC0 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets", "shared", "cc0", "models")


def _gltf_json_file(tmp, name, nodes, meshes, accessors, scene_roots=None):
    """A JSON .gltf whose buffer URI points at a .bin that is NEVER WRITTEN —
    the point being that bounds come from the accessors' own min/max and the
    binary is not needed. If this test ever needs the .bin, the reader started
    decoding buffers and the 'refuse rather than guess' rule broke."""
    doc = {"asset": {"version": "2.0"},
           "scene": 0,
           "scenes": [{"nodes": scene_roots if scene_roots is not None
                       else list(range(len(nodes)))}],
           "nodes": nodes, "meshes": meshes, "accessors": accessors,
           "buffers": [{"byteLength": 1, "uri": "nowhere.bin"}]}
    path = os.path.join(str(tmp), name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f)
    return path


def test_a_json_gltf_with_an_external_bin_reads_without_the_bin(tmp_path):
    acc = [{"min": [0.0, 0.0, 0.0], "max": [0.55, 1.10, 0.20]}]
    p = _gltf_json_file(tmp_path, "shirt.gltf", [{"mesh": 0}],
                        [{"primitives": [{"attributes": {"POSITION": 0}}]}], acc)
    assert not os.path.exists(os.path.join(str(tmp_path), "nowhere.bin"))
    b = A.bounds_mm(p)
    assert b["x_mm"] == pytest.approx(550.0)
    assert b["z_mm"] == pytest.approx(1100.0)


def test_a_json_gltf_goes_through_the_band_assertion_too(tmp_path):
    acc = [{"min": [0.0, 0.0, 0.0], "max": [0.55, 1.10, 0.20]}]
    p = _gltf_json_file(tmp_path, "shirt.gltf", [{"mesh": 0}],
                        [{"primitives": [{"attributes": {"POSITION": 0}}]}], acc)
    ok, rep = A.assert_scale(p, "garment_hung")
    assert ok and rep["measured_mm"] == pytest.approx(1100.0)


def test_json_that_is_not_a_gltf_is_refused_not_read(tmp_path):
    path = os.path.join(str(tmp_path), "notes.gltf")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"hello": "world"}, f)
    with pytest.raises(ValueError, match="no glTF `asset` block"):
        A.bounds_mm(path)


def test_binary_garbage_still_raises_and_names_both_forms(tmp_path):
    path = os.path.join(str(tmp_path), "f.glb")
    with open(path, "wb") as f:
        f.write(b"NOPE" + b"\x00" * 16)
    with pytest.raises(ValueError, match="not readable as a JSON glTF either"):
        A.bounds_mm(path)


@pytest.mark.skipif(not os.path.isdir(CC0), reason="CC0 shelf not on this machine")
def test_the_whole_cc0_shelf_now_ingests_and_none_of_it_raises():
    """THE PIN THAT JUSTIFIES THE CHANGE. Before it, this loop raised 13 times."""
    import glob as _glob
    dirs = sorted(d for d in os.listdir(CC0) if os.path.isdir(os.path.join(CC0, d)))
    assert len(dirs) >= 13
    for d in dirs:
        hits = (_glob.glob(os.path.join(CC0, d, "*.gltf"))
                + _glob.glob(os.path.join(CC0, d, "*.glb")))
        assert hits, f"{d} holds no model file"
        b = A.bounds_mm(hits[0])
        assert b["prims"] >= 1
        assert max(b["x_mm"], b["y_mm"], b["z_mm"]) > 1.0, f"{d} measured as nothing"


@pytest.mark.skipif(not os.path.isdir(CC0), reason="CC0 shelf not on this machine")
def test_a_known_asset_measures_like_the_object_it_is_named_after():
    """A bounds reader that returns numbers is not a bounds reader that returns
    the RIGHT numbers. ArmChair_01 is an armchair, so it is roughly 850 wide and
    roughly 1065 tall — if the Y-up to Z-up mapping were dropped, height and
    depth would swap and this would read 766."""
    import glob as _glob
    hits = _glob.glob(os.path.join(CC0, "ArmChair_01", "*.gltf"))
    b = A.bounds_mm(hits[0])
    assert b["z_mm"] == pytest.approx(1065.0, abs=5.0), "height is not the tall axis"
    assert b["x_mm"] == pytest.approx(848.0, abs=5.0)
    ok, _ = A.assert_scale(hits[0], "chair")
    assert ok


# --- what an incoming asset actually BRINGS (2026-08-10) --------------------------
# The plan's own re-ranking of P2 says acquiring "pays the texture bill in the same
# move, because acquired meshes ship with 3-8 maps". Measured across the two shelves
# that is true of one and false of the other, and the integration rule is derived from
# the file rather than chosen: keep a surface that exists, replace one that does not.

def _matglb(tmp, name, materials):
    """A minimal glTF whose only interesting content is its material list."""
    gl = {"asset": {"version": "2.0"}, "accessors": [], "meshes": [], "nodes": [],
          "scenes": [{"nodes": []}], "scene": 0, "materials": materials}
    blob = json.dumps(gl).encode("utf-8")
    blob += b" " * ((4 - len(blob) % 4) % 4)
    body = struct.pack("<II", len(blob), 0x4E4F534A) + blob
    path = os.path.join(str(tmp), name)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    return path


def test_base_colour_alone_is_a_colour_not_a_surface(tmp_path):
    """The 3D Warehouse shape: flat colours, sometimes a diffuse image, and no relief
    at all. Retinting that produces the moulded-plastic look the first acquired chair
    rendered as."""
    p = _matglb(tmp_path, "warehouse_like.glb", [
        {"name": "Carpet_Plush_Charcoal",
         "pbrMetallicRoughness": {"baseColorFactor": [0.471, 0.667, 0.204],
                                  "baseColorTexture": {"index": 0}}},
        {"name": "Color_006", "pbrMetallicRoughness": {"baseColorFactor": [.3, .3, .3]}},
    ])
    r = A.pbr_map_roles(p)
    assert r["materials"] == 2 and r["base"] == 1
    assert r["normal"] == 0 and r["metallicRoughness"] == 0
    assert A.carries_a_pbr_surface(p) is False


def test_normal_or_roughness_maps_mean_there_is_a_surface_worth_keeping(tmp_path):
    """The Poly Haven shape: one material carrying base + normal + metallicRoughness."""
    p = _matglb(tmp_path, "polyhaven_like.glb", [
        {"name": "ArmChair_01",
         "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
                                  "metallicRoughnessTexture": {"index": 1}},
         "normalTexture": {"index": 2}},
    ])
    r = A.pbr_map_roles(p)
    assert r["normal"] == 1 and r["metallicRoughness"] == 1
    assert A.carries_a_pbr_surface(p) is True


def test_either_map_alone_is_enough_to_count_as_a_surface(tmp_path):
    for mat in ({"normalTexture": {"index": 0}},
                {"pbrMetallicRoughness": {"metallicRoughnessTexture": {"index": 0}}}):
        p = _matglb(tmp_path, f"one{list(mat)[0]}.glb", [dict(mat, name="m")])
        assert A.carries_a_pbr_surface(p) is True


def test_an_unreadable_asset_is_unknown_not_assumed_bare(tmp_path):
    """None means "could not look", and the caller must not treat it as "no surface" —
    that would strip a real PBR set on a read error."""
    bad = tmp_path / "nope.glb"
    bad.write_bytes(b"not a gltf at all")
    assert A.carries_a_pbr_surface(str(bad)) is None
    assert A.carries_a_pbr_surface(str(tmp_path / "missing.glb")) is None


def test_a_gltf_with_no_materials_block_is_bare_not_a_crash(tmp_path):
    p = _matglb(tmp_path, "nomats.glb", [])
    assert A.pbr_map_roles(p)["materials"] == 0
    assert A.carries_a_pbr_surface(p) is False


@pytest.mark.skipif(
    not os.path.isfile(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets", "shared", "cc0", "models", "ArmChair_01", "ArmChair_01_1k.gltf")),
    reason="CC0 shelf not on this machine")
def test_the_real_shelves_differ_the_way_the_rule_assumes():
    """The measurement the rule rests on, run against the actual files. If a future
    Poly Haven asset ever ships bare, this fails and the rule gets re-cut rather than
    quietly mis-firing."""
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cc0 = os.path.join(repo, "assets", "shared", "cc0", "models",
                       "ArmChair_01", "ArmChair_01_1k.gltf")
    assert A.carries_a_pbr_surface(cc0) is True, "the CC0 shelf ships real PBR"
