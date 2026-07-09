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


def test_kinded_rot90_emits_local_rect_so_footprint_rebuilds_true_aabb():
    """THE DOUBLE-ROTATION FIX (rot_reconcile ADJACENT FINDING, 2026-07-09). A rot-carrying
    element is scored through placement_gate.footprint(), which RE-ROTATES x/y/w/d by rot about
    the centre. Emitting the already-rotated WORLD AABB + rot therefore rebuilds a box rotated
    TWICE -> transposed at 90/270 (IoU 0.25 vs truth) -> a DETECTION MISS on the most common
    furniture facings. The kinded lane must instead emit the LOCAL un-yawed rect (2*coeffs on
    basis[0]/basis[1], centred on the centroid) so footprint(local, native_yaw) reconstructs the
    TRUE world AABB. Invisible to gt-vs-gt (both sides re-rotate identically), so pinned here
    against the ground-truth AABB + a real footprint round-trip."""
    import placement_gate as PG
    # a box facing +Y (native yaw 90): basis row0 (local x / forward) = +Y. Half-extents 500 along
    # local-x(+Y) and 200 along local-y(-X) -> a 400mm-wide (X) x 1000mm-deep (Y) world footprint.
    rot90 = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
    box = {"ID": 0, "basis": rot90, "centroid": [1000, 1000, 400], "coeffs": [500, 200, 300]}
    gx, gy, gw, gd, gr = A._box_footprint_xy(rot90, [1000, 1000, 400], [500, 200, 300])
    assert (round(gw), round(gd), round(gr)) == (400, 1000, 90)   # ground-truth AABB + native yaw
    with tempfile.TemporaryDirectory() as td:
        anno_p, bbox_p = _write_scene(td, _two_room_scene(), [box])
        blind = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s")
        kinded = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s", labels={0: "bed"})
    # BLIND lane is unchanged: it stores the world AABB (no rot -> footprint reads it as-is)
    be = blind["elements"][0]
    assert (be["w"], be["d"]) == (400.0, 1000.0) and "rot" not in be
    # KINDED lane stores the LOCAL un-yawed rect (2*coeffs), NOT the world AABB, + native rot
    ke = kinded["elements"][0]
    assert ke["kind"] == "bed" and ke["rot"] == 90.0
    assert (ke["w"], ke["d"]) == (1000.0, 400.0)                  # 2*500 x 2*200, un-yawed
    # footprint() re-rotates the local rect by rot=90 -> reconstructs the TRUE world AABB (== blind)
    fx0, fy0, fx1, fy1 = PG.footprint(ke)
    assert (round(fx1 - fx0), round(fy1 - fy0)) == (400, 1000)
    assert (round((fx0 + fx1) / 2), round((fy0 + fy1) / 2)) == (1000, 1000)   # centre preserved
    # it IoU-matches a reader that emits the true AABB (rot 0) -> NO detection miss ...
    reader = {"x": gx, "y": gy, "w": gw, "d": gd}
    assert PG.iou(PG.footprint(ke), PG.footprint(reader)) > 0.99
    # ... whereas the OLD buggy emission (world AABB + rot) transposes and misses (IoU 0.25)
    buggy = {"x": gx, "y": gy, "w": gw, "d": gd, "rot": 90.0}
    assert PG.iou(PG.footprint(buggy), PG.footprint(reader)) < 0.3


def test_kinded_tipped_box_keeps_aabb_drops_rot_and_is_counted():
    """A TIPPED labeled box (basis[2] tilts into XY, so its 8-corner world AABB carries a coeffs[2]
    contribution the local face drops) cannot be represented by any (w,d,rot) rect: the local-face
    emission would score a sub-visible footprint that never IoU-matches a real reader -- a SILENT,
    UNCOUNTED detection miss (adversarial verification 2026-07-09). The kinded lane must instead keep
    the WORLD AABB (detection + F1 correct), emit NO rot (F2 honestly unreported, never a fabricated
    facing), and COUNT it in meta.kinded_tipped_blinded. Clean-yaw furniture is unaffected."""
    import placement_gate as PG
    # local-y axis = world Z; the long 4000mm (coeffs[2]) axis lies in the XY plane -> world AABB
    # ~2400x3200, but the basis[0]/basis[1] face is only 0.8x0.8mm.
    basis = [[0.8, -0.6, 0], [0, 0, 1], [0.6, 0.8, 0]]
    box = {"ID": 0, "basis": basis, "centroid": [5000, 5000, 400], "coeffs": [0.4, 0.4, 2000]}
    gx, gy, gw, gd, _r = A._box_footprint_xy(basis, [5000, 5000, 400], [0.4, 0.4, 2000])
    with tempfile.TemporaryDirectory() as td:
        # bigger room so the centroid lands indoors (reuse the synthetic 2-room scene's coords is
        # too small; a standalone floor plane keeps the element emitted regardless of indoor).
        anno = _build_anno([(0, 0, 0), (10000, 0, 0), (10000, 10000, 0), (0, 10000, 0)],
                           [(0, 1), (1, 2), (2, 3), (3, 0)],
                           [("floor", [0, 1, 2, 3])],
                           [{"ID": 0, "planeID": [0], "type": "bedroom"}])
        anno_p, bbox_p = _write_scene(td, anno, [box])
        doc = A.convert(anno_path=anno_p, bbox_path=bbox_p, scene_id="s", labels={0: "bed"})
    e = doc["elements"][0]
    assert e["kind"] == "bed"                          # F1 still scores
    assert "rot" not in e                              # F2 honestly unreported (no faithful rot)
    assert (e["w"], e["d"]) == (round(gw, 1), round(gd, 1))   # kept the WORLD AABB, not the 0.8 face
    assert doc["meta"]["kinded_tipped_blinded"] == 1 and doc["meta"]["n_kinded"] == 1
    # detection: the world AABB matches a real reader seeing the true ~2400x3200 region
    reader = {"x": gx, "y": gy, "w": gw, "d": gd}
    assert PG.iou(PG.footprint(e), PG.footprint(reader)) > 0.99


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
