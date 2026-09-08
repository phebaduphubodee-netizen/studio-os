"""Tests for glb_flatten.py — the per-triangle-export merge.

Fixtured on the facts of p2r47, the way this repo tests a rule that has already
decided something: `d4698c95` is a 360 MB file holding 299,307 triangles in 297,631
primitives and **297,632 material entries that are 27 distinct definitions**. Both
numbers are load-bearing — grouping on the raw material index merges nothing, and a
merge that loses one triangle is worse than no merge at all.
"""
import json
import struct

import pytest

import glb_flatten as F


def _bin_glb(doc, blob):
    js = json.dumps(doc).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    bl = blob + b"\x00" * ((4 - len(blob) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bl)
    return (struct.pack("<III", F.GLB_MAGIC, 2, total)
            + struct.pack("<II", len(js), F.CHUNK_JSON) + js
            + struct.pack("<II", len(bl), F.CHUNK_BIN) + bl)


def _per_triangle_doc(tris, materials):
    """A SketchUp-shaped export: one primitive AND one material entry per triangle.

    `materials[i]` is the material VALUE for triangle i — repeat a value to make two
    entries that must dedupe to one.
    """
    blob = bytearray()
    views, accs, prims = [], [], []
    for i, (a, b, c) in enumerate(tris):
        off = len(blob)
        for v in (a, b, c):
            blob.extend(struct.pack("<fff", *v))
        views.append({"buffer": 0, "byteOffset": off, "byteLength": 36})
        accs.append({"bufferView": len(views) - 1, "componentType": 5126,
                     "count": 3, "type": "VEC3",
                     "min": [min(p[k] for p in (a, b, c)) for k in range(3)],
                     "max": [max(p[k] for p in (a, b, c)) for k in range(3)]})
        pos = len(accs) - 1
        off = len(blob)
        blob.extend(struct.pack("<HHH", 0, 1, 2))
        blob.extend(b"\x00\x00")                       # keep 4-byte alignment
        views.append({"buffer": 0, "byteOffset": off, "byteLength": 6})
        accs.append({"bufferView": len(views) - 1, "componentType": 5123,
                     "count": 3, "type": "SCALAR"})
        prims.append({"attributes": {"POSITION": pos}, "indices": len(accs) - 1,
                      "material": i, "mode": 4})
    doc = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
           "nodes": [{"mesh": 0, "scale": [0.1, 0.1, 0.1]}],
           "meshes": [{"primitives": prims}], "materials": list(materials),
           "accessors": accs, "bufferViews": views,
           "buffers": [{"byteLength": len(blob)}]}
    return doc, bytes(blob)


def _tri(n):
    return [((i, 0, 0), (i + 1, 0, 0), (i, 1, 0)) for i in range(n)]


def _positions(g, blob):
    bufs = F.buffers_of(g, blob)
    out = []
    for m in g["meshes"]:
        for p in m["primitives"]:
            pos = F.accessor(g, bufs, p["attributes"]["POSITION"])
            idx = [int(v[0]) for v in F.accessor(g, bufs, p["indices"])]
            out.extend(pos[i] for i in idx)
    return out


def test_a_per_triangle_export_merges_to_one_primitive_per_distinct_material():
    """The shape of d4698c95: many primitives, many material ENTRIES, few material
    VALUES. 27 definitions is what 297,632 entries are worth."""
    mats = [{"name": "cloth"} if i % 3 else {"name": "wood"} for i in range(9)]
    doc, blob = _per_triangle_doc(_tri(9), mats)
    out, ob, rep = F.flatten(doc, blob)
    assert rep["prims_in"] == 9
    assert rep["materials_in"] == 9 and rep["materials_out"] == 2
    assert rep["prims_out"] == 2, "one primitive per DISTINCT material, not per entry"
    assert len(out["meshes"]) == 1 and len(out["meshes"][0]["primitives"]) == 2


def test_grouping_on_the_raw_material_index_would_merge_nothing():
    """The reason dedupe_materials exists, pinned: with a unique VALUE per triangle
    there is nothing to merge, and the tool must not pretend otherwise."""
    mats = [{"name": f"m{i}"} for i in range(6)]
    doc, blob = _per_triangle_doc(_tri(6), mats)
    _out, _ob, rep = F.flatten(doc, blob)
    assert rep["materials_out"] == 6 and rep["prims_out"] == 6


def test_two_materials_differing_only_in_name_stay_two():
    """Identity is the whole JSON value. The conservative direction: nothing that
    renders differently is ever merged, and a name is a difference we did not author."""
    remap, mats = F.dedupe_materials(
        {"materials": [{"name": "a", "doubleSided": True},
                       {"name": "b", "doubleSided": True},
                       {"name": "a", "doubleSided": True}]})
    assert len(mats) == 2 and remap == {0: 0, 1: 1, 2: 0}


def test_no_triangle_is_lost_and_none_is_invented():
    doc, blob = _per_triangle_doc(_tri(12), [{"name": "cloth"}] * 12)
    _out, _ob, rep = F.flatten(doc, blob)
    assert rep["tris_in"] == rep["tris_out"] == 12


def test_the_merged_positions_are_the_same_points_in_the_same_order():
    """THE CORRECTNESS TEST. Merging rebases every primitive's indices onto the
    concatenated vertex array; an off-by-one there scrambles a duvet into noise and
    nothing downstream could trace it back to a byte reader."""
    doc, blob = _per_triangle_doc(_tri(7), [{"name": "cloth"}] * 7)
    before = _positions(doc, blob)
    out, ob, _rep = F.flatten(doc, blob)
    assert _positions(out, ob) == before


def test_node_scales_survive_because_a_sketchup_export_carries_its_units_there():
    """0227d2c9's four copies of one duvet sit under node scales of 0.1 and 0.01 and
    that is the only thing making them ~900 mm objects. Losing it silently rescales
    the model — the exact failure pipeline/CLAUDE.md calls a MUST."""
    doc, blob = _per_triangle_doc(_tri(3), [{"name": "cloth"}] * 3)
    out, _ob, _rep = F.flatten(doc, blob)
    assert out["nodes"][0]["scale"] == [0.1, 0.1, 0.1]
    assert out["scenes"] == [{"nodes": [0]}] and out["scene"] == 0


def test_a_non_triangle_primitive_is_reported_by_mode_never_silently_dropped():
    doc, blob = _per_triangle_doc(_tri(4), [{"name": "cloth"}] * 4)
    doc["meshes"][0]["primitives"][0]["mode"] = 1          # LINES
    _out, _ob, rep = F.flatten(doc, blob)
    assert rep["skipped_modes"] == {1: 1}
    assert rep["tris_out"] == 3


def test_an_attribute_this_tool_does_not_carry_is_named_in_the_report():
    doc, blob = _per_triangle_doc(_tri(2), [{"name": "cloth"}] * 2)
    doc["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"] = 0
    _out, _ob, rep = F.flatten(doc, blob)
    assert rep["dropped_attrs"] == ["COLOR_0"]


def test_a_sparse_accessor_is_refused_rather_than_read_wrong():
    doc, blob = _per_triangle_doc(_tri(2), [{"name": "cloth"}] * 2)
    doc["accessors"][0]["sparse"] = {"count": 1}
    with pytest.raises(ValueError, match="sparse"):
        F.flatten(doc, blob)


def test_a_buffer_pointing_at_an_external_file_is_refused():
    doc, blob = _per_triangle_doc(_tri(2), [{"name": "cloth"}] * 2)
    doc["buffers"] = [{"uri": "geometry.bin", "byteLength": 10}]
    with pytest.raises(ValueError, match="external file"):
        F.flatten(doc, blob)


def test_a_mesh_left_with_no_primitives_does_not_leave_a_node_pointing_at_it():
    doc, blob = _per_triangle_doc(_tri(2), [{"name": "cloth"}] * 2)
    for p in doc["meshes"][0]["primitives"]:
        p["mode"] = 1
    out, _ob, rep = F.flatten(doc, blob)
    assert rep["meshes_out"] == 0 and out["meshes"] == []
    assert "mesh" not in out["nodes"][0], "a dangling mesh index is an invalid glTF"


def test_write_then_read_round_trips(tmp_path):
    doc, blob = _per_triangle_doc(_tri(5), [{"name": "cloth"}] * 5)
    out, ob, _rep = F.flatten(doc, blob)
    p = tmp_path / "flat.glb"
    F.write_glb(str(p), out, ob)
    g2, b2 = F.read_glb(str(p))
    assert _positions(g2, b2) == _positions(doc, blob)
    assert g2["nodes"][0]["scale"] == [0.1, 0.1, 0.1]


def test_a_file_that_is_not_a_glb_raises(tmp_path):
    p = tmp_path / "no.glb"
    p.write_bytes(b"nope, not a glb")
    with pytest.raises(ValueError):
        F.read_glb(str(p))


def test_byte_stride_and_normalized_integers_are_honoured():
    """An accessor may be interleaved and may store UVs as normalized shorts. Reading
    either one wrongly puts the geometry somewhere else entirely."""
    blob = bytearray()
    for x in (1.0, 2.0, 3.0):
        blob.extend(struct.pack("<fff", x, 0.0, 0.0))
        blob.extend(struct.pack("<ff", 0.0, 0.0))          # 8 bytes of padding
    g = {"buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(blob),
                          "byteStride": 20}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3,
                        "type": "VEC3"}]}
    assert F.accessor(g, [bytes(blob)], 0) == [(1.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                                               (3.0, 0.0, 0.0)]
    g2 = {"buffers": [{"byteLength": 4}],
          "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 4}],
          "accessors": [{"bufferView": 0, "componentType": 5123, "count": 1,
                         "type": "VEC2", "normalized": True}]}
    got = F.accessor(g2, [struct.pack("<HH", 65535, 0)], 0)
    assert got[0][0] == pytest.approx(1.0) and got[0][1] == pytest.approx(0.0)
