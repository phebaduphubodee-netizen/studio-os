"""Tests for mesh_density.py — the pre-bench density SCREEN.

The estimate is pinned against the two candidates whose world edge was measured by
the authority (`bedcloth_fit.edge_mm`, in Blender, on the staged mesh) BEFORE this
file existed. A screen that cannot reproduce a measurement it was calibrated on is
not a screen, it is a second opinion.
"""
import json
import struct

import pytest

import mesh_density as MD

# the bed this lane is dressing: mattress 1820 x 1969 mm
COVER = 2000.0
CONTROL = 10.3          # coarsest BOUGHT cloth accepted in the same frame


def _glb(doc):
    """Minimal in-memory .glb: 12-byte header + JSON chunk."""
    raw = json.dumps(doc).encode("utf-8")
    raw += b" " * ((4 - len(raw) % 4) % 4)
    head = struct.pack("<III", MD.GLB_MAGIC, 2, 12 + 8 + len(raw))
    return head + struct.pack("<II", len(raw), 0x4E4F534A) + raw


def _doc(prims):
    """prims: [(tris, (x, y, z))] -> a glTF doc with one mesh per primitive."""
    acc, meshes = [], []
    for tris, ext in prims:
        pos = len(acc)
        acc.append({"count": tris * 3, "min": [0, 0, 0], "max": list(ext)})
        idx = len(acc)
        acc.append({"count": tris * 3})
        meshes.append({"primitives": [{"attributes": {"POSITION": pos},
                                       "indices": idx}]})
    return {"accessors": acc, "meshes": meshes}


def test_calibration_0afd4c6f_reproduces_its_measured_world_edge():
    """THE CALIBRATION CASE. 0afd4c6f's field sheet carries 4,175 triangles and
    `bedcloth_fit.edge_mm` measured it at 43.5 mm in world on the staged mesh."""
    est = MD.est_edge_mm(4175, COVER)
    assert est == pytest.approx(43.5, abs=1.0), (
        "the screen must land on the one number that was measured independently")


def test_the_second_calibration_point_is_optimistic_and_that_is_recorded():
    """13525bfb: 33,632 triangles on its largest primitive, MEASURED at 25.6 mm.
    The screen says 15.4 — optimistic by 1.7x, because the largest primitive in a
    file is not always the part staging ends up calling the field. So the screen is
    a FLOOR on coarseness: what it calls coarse never comes back fine."""
    est = MD.est_edge_mm(33632, COVER)
    assert est == pytest.approx(15.4, abs=0.5)
    assert est < 25.6, "documented direction of the error: optimistic, never harsh"


def test_the_estimate_ignores_the_files_own_units_by_construction():
    """The SketchUp inch trap is the one thing that cannot be trusted, and this
    shelf carries it: 0227d2c9's sheets read 90 x 79 in the file and import as
    0.9 m objects. Two files with the SAME triangle count and wildly different
    declared extents must screen identically."""
    a = _glb(_doc([(4175, (90.0, 79.0, 29.0))]))
    b = _glb(_doc([(4175, (2286.0, 2007.0, 737.0))]))
    open_a, open_b = "a.glb", "b.glb"
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        pa, pb = os.path.join(td, open_a), os.path.join(td, open_b)
        with open(pa, "wb") as f:
            f.write(a)
        with open(pb, "wb") as f:
            f.write(b)
        assert MD.screen(pa, COVER)["est_edge_mm"] == \
               MD.screen(pb, COVER)["est_edge_mm"]


def test_the_screen_reports_the_densest_sheet_not_the_biggest_one():
    """0227d2c9 holds a 16,291-triangle part with a LARGER declared plan than its
    159,923-triangle one. Density is the question being asked."""
    import os
    import tempfile
    doc = _doc([(16291, (90.0, 79.0, 29.0)), (159923, (9.0, 8.0, 3.0))])
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "m.glb")
        with open(p, "wb") as f:
            f.write(_glb(doc))
        s = MD.screen(p, COVER)
    assert s["tris"] == 159923
    assert s["prims"] == 2 and s["total_tris"] == 16291 + 159923


def test_tris_needed_states_the_bar_a_search_has_to_clear():
    """The line the bench cannot afford to compute: what a candidate must carry to
    clear the control at all. ~75,000 triangles in ONE sheet."""
    need = MD.tris_needed(CONTROL, COVER)
    assert 74_000 <= need <= 76_000
    assert MD.est_edge_mm(need, COVER) == pytest.approx(CONTROL, abs=0.05)


def test_a_finer_mesh_always_screens_finer():
    seq = [MD.est_edge_mm(t, COVER) for t in (1000, 10_000, 100_000)]
    assert seq == sorted(seq, reverse=True)


def test_nothing_to_measure_returns_none_rather_than_a_flattering_zero():
    assert MD.est_edge_mm(0, COVER) is None
    assert MD.est_edge_mm(None, COVER) is None
    assert MD.est_edge_mm(4175, 0) is None
    assert MD.tris_needed(0, COVER) is None
    assert MD.tris_needed(None, COVER) is None


def test_a_file_that_is_not_a_glb_raises_rather_than_screening_as_empty(tmp_path):
    p = tmp_path / "not.glb"
    p.write_bytes(b"this is not a glb at all, not even close")
    with pytest.raises(ValueError):
        MD.gltf_json(str(p))


def test_a_truncated_file_raises(tmp_path):
    p = tmp_path / "short.glb"
    p.write_bytes(b"\x67\x6c\x54\x46")
    with pytest.raises(ValueError):
        MD.gltf_json(str(p))


def test_primitives_skips_what_it_cannot_measure_without_failing_the_file():
    doc = {"accessors": [{"count": 300, "min": [0, 0, 0], "max": [1, 1, 1]},
                         {"count": 300},
                         {"count": 30}],                       # no min/max
           "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1},
                                      {"attributes": {"POSITION": 2}},
                                      {"attributes": {}}]}]}
    rows = MD.primitives(doc)
    assert len(rows) == 1 and rows[0]["tris"] == 100


def test_a_screen_dir_over_a_missing_cache_is_empty(tmp_path):
    assert MD.screen_dir(str(tmp_path / "nope"), COVER) == []
