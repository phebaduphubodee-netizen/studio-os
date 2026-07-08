"""
test_structured3d_adapter.py -- unit tests for the Structured3D -> gt.json adapter.

Synthetic fixtures are SELF-AUTHORED tiny annotations (the corpus lives outside the repo;
nothing here redistributes it). Pinned per the scorer-honesty doctrine: the bbox->footprint
projection math is exact-pinned; the indoor point-in-room-polygon must map an in-balcony
object to False and an in-bedroom object to True; a centroid in no room must emit NO indoor
key (counted, not guessed); a zero-area box is dropped and counted; and the emitted schema
must round-trip benchmark_reader with F3/F4/F6 WIRED, F2/F5 UNWIRED, F1 identity-blind -- a
fabricated kind/rot/indoor flag would poison the whole backwards-learning lane.

    python3 -m pytest test_structured3d_adapter.py -q
"""
import json
import os
import tempfile

import pytest

import benchmark_reader as B
import structured3d_adapter as A


# ---- synthetic annotation builder --------------------------------------------------------
def _build_anno(junctions, lines, planes, semantics):
    """junctions=[(x,y,z)], lines=[(ja,jb)], planes=[(type,[line-idx])], semantics=[dict].
    Builds the incidence matrices so plane/line/junction IDs equal their list index (the
    real corpus invariant the adapter relies on)."""
    nj, nl = len(junctions), len(lines)
    ljm = [[1 if j in lines[li] else 0 for j in range(nj)] for li in range(nl)]
    plm = [[1 if li in planes[pi][1] else 0 for li in range(nl)] for pi in range(len(planes))]
    return {
        "junctions": [{"ID": i, "coordinate": list(c)} for i, c in enumerate(junctions)],
        "lines": [{"ID": i, "direction": [0, 0, 1], "point": [0, 0, 0]}
                  for i in range(nl)],
        "planes": [{"ID": i, "normal": [0, 0, 1], "offset": 0, "type": t}
                   for i, (t, _e) in enumerate(planes)],
        "lineJunctionMatrix": ljm,
        "planeLineMatrix": plm,
        "semantics": semantics,
        "cuboids": [], "manhattan": [],
    }


# two unit squares side by side: bedroom (0,0)-(1000,1000), balcony (1000,0)-(2000,1000),
# a door boundary box near (900,0)-(1000,120), and a left-wall outwall segment.
def _two_room_scene():
    junctions = [
        (0, 0, 0),        # 0
        (1000, 0, 0),     # 1
        (1000, 1000, 0),  # 2
        (0, 1000, 0),     # 3
        (2000, 0, 0),     # 4
        (2000, 1000, 0),  # 5
        (900, 0, 0),      # 6  door
        (1000, 120, 0),   # 7  door
    ]
    lines = [
        (0, 1),  # 0 bedroom bottom
        (1, 2),  # 1 shared middle
        (2, 3),  # 2 bedroom top
        (3, 0),  # 3 bedroom left
        (1, 4),  # 4 balcony bottom
        (4, 5),  # 5 balcony right
        (5, 2),  # 6 balcony top
        (6, 7),  # 7 door
        (3, 0),  # 8 outwall (bedroom left, floor-level)
    ]
    planes = [
        ("floor", [0, 1, 2, 3]),   # 0 bedroom floor
        ("floor", [1, 4, 5, 6]),   # 1 balcony floor
        ("wall", [7]),             # 2 door wall
        ("wall", [8]),             # 3 outwall wall
    ]
    semantics = [
        {"ID": 100, "planeID": [0], "type": "bedroom"},
        {"ID": 101, "planeID": [1], "type": "balcony"},
        {"ID": 102, "planeID": [2], "type": "door"},
        {"ID": 103, "planeID": [3], "type": "outwall"},
    ]
    return _build_anno(junctions, lines, planes, semantics)


def _bbox_objs():
    ident = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return [
        {"ID": 0, "basis": ident, "centroid": [500, 500, 400],
         "coeffs": [100, 100, 100]},   # in bedroom  -> indoor True
        {"ID": 1, "basis": ident, "centroid": [1500, 500, 400],
         "coeffs": [80, 80, 100]},     # in balcony  -> indoor False
        {"ID": 2, "basis": ident, "centroid": [5000, 5000, 400],
         "coeffs": [50, 50, 100]},     # in no room  -> no indoor key
        {"ID": 3, "basis": ident, "centroid": [500, 500, 400],
         "coeffs": [0.1, 0.1, 100]},   # zero-area   -> dropped + counted
    ]


def _write_scene(td, anno, bbox=None):
    anno_p = os.path.join(td, "annotation_3d.json")
    with open(anno_p, "w", encoding="utf-8") as fh:
        json.dump(anno, fh)
    bbox_p = None
    if bbox is not None:
        bbox_p = os.path.join(td, "bbox_3d.json")
        with open(bbox_p, "w", encoding="utf-8") as fh:
            json.dump(bbox, fh)
    return anno_p, bbox_p


# ---- projection math (exact pin) ---------------------------------------------------------
def test_footprint_identity_basis():
    ident = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    x, y, w, d, rot = A._box_footprint_xy(ident, [1000, 2000, 500], [100, 50, 200])
    assert (round(x, 6), round(y, 6)) == (900.0, 1950.0)
    assert (round(w, 6), round(d, 6)) == (200.0, 100.0)   # 2*coeff0, 2*coeff1
    assert round(rot, 6) == 0.0                            # forward = +x


def test_footprint_rotated_yaw():
    # basis row0 (local x / forward) points along world +y -> yaw 90 deg CCW from +x
    rot90 = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
    x, y, w, d, rot = A._box_footprint_xy(rot90, [0, 0, 0], [100, 50, 200])
    # footprint is axis-aligned regardless of yaw: extents swap (x-extent from coeff1)
    assert (round(w, 6), round(d, 6)) == (100.0, 200.0)
    assert round(rot, 6) == 90.0


def test_transpose_divergence_counted():
    """The footprint is NOT rows-vs-cols invariant for tipped / axis-swapped boxes (the
    retracted 'interpretation-invariant' claim). convert() must COUNT that population in meta
    (honesty), not hide it: an identity basis is invariant (transpose == self) and counts 0; a
    cyclic-permutation rotation with DISTINCT coeffs diverges (rows 600x200 mm vs cols
    400x600 mm) and counts 1."""
    ident = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    cyclic = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]   # det +1 rotation; rows/cols footprints differ
    boxes = [
        {"ID": 0, "basis": ident, "centroid": [500, 500, 400], "coeffs": [100, 100, 100]},
        {"ID": 1, "basis": cyclic, "centroid": [500, 500, 400], "coeffs": [100, 200, 300]},
    ]
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), boxes)
        doc = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="tipped")
    assert doc["meta"]["transpose_divergent"] == 1          # only the cyclic box diverges
    assert doc["meta"]["transpose_divergence_mm"] == A.TRANSPOSE_DIVERGENCE_MM


# ---- indoor / opening / drop-counting on the synthetic 2-room scene ----------------------
def test_two_room_indoor_and_openings():
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), _bbox_objs())
        doc = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="synthetic")
    m = doc["meta"]
    # rooms: bedroom + balcony (door/outwall are boundaries, not rooms)
    assert m["n_rooms"] == 2
    assert m["rooms_by_type"] == {"bedroom": 1, "balcony": 1}
    # elements: 4 objects, 1 zero-area dropped -> 3 emitted
    assert m["zero_area_dropped"] == 1
    assert len(doc["elements"]) == 3
    by_id = {e["id"]: e for e in doc["elements"]}
    assert by_id["o0"]["indoor"] is True     # bedroom
    assert by_id["o1"]["indoor"] is False    # balcony
    assert "indoor" not in by_id["o2"]       # no room -> no key
    assert m["centroid_in_no_room"] == 1
    assert m["indoor_true"] == 1 and m["indoor_false"] == 1
    assert m["transpose_divergent"] == 0     # all bbox objs use an identity basis (invariant)
    # NO kind / rot / floor keys on any element (blocked / single-storey)
    for e in doc["elements"]:
        assert "kind" not in e and "rot" not in e and "floor" not in e
    # one door opening, located at its junction bbox
    assert len(doc["openings"]) == 1
    op = doc["openings"][0]
    assert op["type"] == "door"
    assert (op["x"], op["y"], op["w"], op["d"]) == (900.0, 0.0, 100.0, 120.0)
    # one outwall glazing segment
    assert m["n_glazing"] >= 1
    assert all(g["kind"] == "outwall" for g in doc["glazing_lines"])
    assert m["units"] == "mm"
    assert m["kind_blocked"]                  # loud reason string present


def test_labels_sidecar_wires_kind_rot_and_f2():
    """F2 UNBLOCK. An OPTIONAL per-object labels sidecar (caller-supplied REAL kinds -- never
    fabricated) makes the adapter emit kind + rot, lighting up F2_facing (UNWIRED -> scored)
    for the first time. WITHOUT the sidecar the element stays kind-less and F2 stays UNWIRED:
    the blocked default is byte-identical, so the honesty contract is unchanged when no data."""
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), _bbox_objs())
        blind = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s")
        kinded = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s",
                           labels={0: "bed", 1: "sofa"})
    # blind default unchanged: no kind/rot on any element, F2 UNWIRED, n_kinded 0
    assert all("kind" not in e and "rot" not in e for e in blind["elements"])
    assert B.score_pair(blind, blind)["F2_facing"]["verdict"] == "UNWIRED"
    assert blind["meta"]["n_kinded"] == 0 and blind["meta"]["labels_supplied"] is False
    # kinded: labeled objects carry kind + rot; an UNLABELED object stays kind-less (never guessed)
    by = {e["id"]: e for e in kinded["elements"]}
    assert by["o0"]["kind"] == "bed" and by["o0"]["rot"] == 0.0
    assert by["o1"]["kind"] == "sofa" and by["o1"]["rot"] == 0.0
    assert "kind" not in by["o2"] and "rot" not in by["o2"]   # o2 unlabeled
    assert kinded["meta"]["n_kinded"] == 2 and kinded["meta"]["labels_supplied"] is True
    # F2 now SCORES (both facing-kinds carry rot; gt-vs-gt => exact match => PASS)
    card = B.score_pair(kinded, kinded)
    assert card["F2_facing"]["verdict"] == "PASS" and card["F2_facing"]["n"] == 2


def test_wall_lines_emitted_for_synthesizer_and_oracle_lane():
    """The adapter emits every WALL plane's floor-level trace as gt['wall_lines'] -- the plan
    skeleton the 2D synthesizer draws AND the input svg_plan_reader's oracle-walls lane consumes.
    Schema mirrors floorplancad_adapter: [{x1,y1,x2,y2}] in mm."""
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), _bbox_objs())
        doc = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s")
    wl = doc["wall_lines"]
    assert doc["meta"]["n_wall_lines"] == len(wl) and len(wl) >= 1
    for w in wl:
        assert {"x1", "y1", "x2", "y2"} <= set(w)
        assert all(isinstance(w[k], (int, float)) for k in ("x1", "y1", "x2", "y2"))


def test_no_bbox_file_reports_zero_elements():
    with tempfile.TemporaryDirectory() as td:
        anno_p, _ = _write_scene(td, _two_room_scene(), bbox=None)
        doc = A.convert(anno_path=anno_p, bbox_path=None, scene_id="nobbox")
    assert doc["meta"]["no_bbox_file"] is True
    assert doc["meta"]["n_elements"] == 0
    assert len(doc["elements"]) == 0
    # rooms/openings/glazing still emit without a bbox file
    assert doc["meta"]["n_rooms"] == 2
    assert len(doc["openings"]) == 1
    assert doc["meta"]["n_glazing"] >= 1


def test_selftest_contract_on_synthetic():
    """gt-vs-gt on the synthetic scene must meet the benchmark_reader contract:
    detection/F3/F4/F6 score, F2/F5 UNWIRED, F1 identity-blind (only the '' bucket)."""
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), _bbox_objs())
        doc = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="synthetic")
    card = B.score_pair(doc, doc)          # mm -> default tol, no open_tol needed
    assert card["detection"]["verdict"] == "PASS"
    assert card["F3_indoor"]["n"] > 0 and card["F3_indoor"]["verdict"] == "PASS"
    assert card["F4_openings"]["verdict"] == "PASS"
    assert card["F6_glazing"]["n_gt"] > 0 and card["F6_glazing"]["verdict"] == "PASS"
    assert card["F2_facing"]["verdict"] == "UNWIRED"
    assert card["F5_floor"]["verdict"] == "UNWIRED"
    assert set(card["F1_identity"]["per_kind"].keys()) <= {""}   # identity-blind
    assert not any(card["malformed"].values())


# ---- real-data test (skips cleanly when the dataset is absent) ---------------------------
_SCENE0 = os.path.join(A.ANNO_ROOT, "scene_00000")


@pytest.mark.skipif(not os.path.isdir(_SCENE0),
                    reason="Structured3D dataset not present")
def test_real_scene_00000():
    doc = A.convert(scene_dir=_SCENE0)
    m = doc["meta"]
    assert m["n_elements"] > 0
    assert m["n_openings"] > 0
    assert m["n_glazing"] >= 1
    assert m["n_rooms"] > 0
    assert m["units"] == "mm"
    # living-room polygon anchor from the verified recipe (x extent ~ -3507..-489)
    # -> at least one element carries a real indoor bool
    assert m["indoor_true"] + m["indoor_false"] > 0
    card = B.score_pair(doc, doc)
    assert card["detection"]["verdict"] == "PASS"
    assert card["F3_indoor"]["n"] > 0 and card["F3_indoor"]["verdict"] == "PASS"
    assert card["F4_openings"]["verdict"] == "PASS"
    assert card["F6_glazing"]["n_gt"] > 0 and card["F6_glazing"]["verdict"] == "PASS"
    assert card["F2_facing"]["verdict"] == "UNWIRED"
    assert card["F5_floor"]["verdict"] == "UNWIRED"
    assert set(card["F1_identity"]["per_kind"].keys()) <= {""}
