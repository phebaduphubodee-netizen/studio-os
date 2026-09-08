"""Tests for wall_detect -- the blind double-line wall detector.

The load-bearing pins:
  - DRAW: two face lines per wall at exactly +/-T/2 along the normal; degenerate walls
    skipped AND counted (a zero-length line would shift read_ink's tail slice and break
    the lane's identity pin);
  - DETECT: a drawn wall pair is found and its centerline lands on the gt centerline;
  - the RING exclusion is load-bearing: a bare rect's opposite edges ARE a legal parallel
    pair in the gap window (proven here), and only the ring index keeps furniture out;
  - the CO-TERMINOUS screen is what keeps F2 back-strips alive: a strip near a wall face
    is parallel and in-window but never end-aligned (the wardrobe scenario, pinned);
  - collinear strokes never pair (GAP_MIN); double walls (two rooms' parallel
    centerlines) classify all four faces with every centerline inside the band;
  - collinear centerline halves MERGE to one; coverage_vs_gt reads 100% on a perfect
    detection and 0% + walls_zero on an empty one.
"""
import math

import wall_detect as WD


def _wall(x1, y1, x2, y2):
    return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def _rect_segs(x, y, w, d):
    ring = [(x, y), (x + w, y), (x + w, y + d), (x, y + d), (x, y)]
    return [[a, b] for a, b in zip(ring, ring[1:])]


def _wall_ink(walls, t=WD.WALL_T_MM):
    """The exact segments read_ink would see for the drawn walls (both faces, in order)."""
    faces, _ = WD.wall_face_lines(walls, t)
    out = []
    for fa, fb in faces:
        out.append([fa[0], fa[1]])
        out.append([fb[0], fb[1]])
    return out


# ---- drawing --------------------------------------------------------------------------------
def test_face_lines_offsets_and_degenerate():
    faces, skipped = WD.wall_face_lines([_wall(0, 0, 1000, 0), _wall(5, 5, 5, 5)])
    assert skipped == 1 and len(faces) == 1
    (a1, a2), (b1, b2) = faces[0]
    ys = sorted([a1[1], b1[1]])
    assert ys == [-50.0, 50.0]                    # +/- T/2 along the normal
    assert a1[0] == 0.0 and a2[0] == 1000.0


def test_append_wall_ink_lines_and_identity():
    svg = "<svg></svg>"
    out, expected, skipped = WD.append_wall_ink(svg, [_wall(0, 0, 1000, 0)])
    assert out.count("<line") == 2 and len(expected) == 2 and skipped == 0
    assert out.rstrip().endswith("</svg>")
    for (a, b) in expected:                        # endpoints as %.1f-formatted floats
        assert a != b
    out2, expected2, _ = WD.append_wall_ink(svg, [])
    assert out2 == svg and expected2 == []


# ---- detection ------------------------------------------------------------------------------
def test_single_wall_detected_with_centerline_on_gt():
    gt = _wall(0, 0, 2000, 0)
    segs = _wall_ink([gt])
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == {0, 1}
    assert len(det["centerlines"]) == 1
    c = det["centerlines"][0]
    assert abs(c["y1"]) <= 1.0 and abs(c["y2"]) <= 1.0
    assert abs(min(c["x1"], c["x2"]) - 0) <= 1.0
    assert abs(max(c["x1"], c["x2"]) - 2000) <= 1.0


def test_ring_pair_veto_is_load_bearing():
    """A 900x200 rect's horizontal edges ARE a co-terminous parallel pair at gap 200 --
    with the veto disabled the detector eats furniture (proven), with the default
    ring-pair veto nothing fires. The rejected designs (all-members exclusion,
    furniture-size screen, same-ring-only veto) are pinned in the module comment."""
    segs = _rect_segs(0, 0, 900, 200)
    naked = WD.detect_walls(segs, ring_sets=[])
    assert naked["wall_idx"], "calibration drift: the rect-edge hazard vanished -- " \
                              "re-derive the ring-pair-veto rationale"
    vetoed = WD.detect_walls(segs)                 # default = ring_groups
    assert vetoed["wall_idx"] == set() and vetoed["centerlines"] == []
    assert vetoed["stats"]["pairs_ring_vetoed"] >= 1


def test_aligned_twin_rects_not_paired():
    """Two identical rects whose facing edges sit at a wall-like 60mm gap, exactly
    aligned: both edges are outline ink, so the ring-pair veto must reject them (a
    same-ring-only veto let this pair through -- fixture forensic)."""
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == set() and det["centerlines"] == []


def test_wall_flush_furniture_edge_not_eaten():
    """The 513-fp pilot class: a wardrobe filling a niche, its edge parallel to a wall
    face at an in-window gap, same length, exactly aligned. The edge passes phase 1
    against the wall's near face, but that face's MUTUAL best is its own partner -- the
    furniture edge must stay unclassified and the wall must still be detected."""
    gt = _wall(0, 0, 2000, 0)
    segs = _wall_ink([gt])                          # faces at y=-50, +50
    # wardrobe outline 2000x600 whose top edge runs at y=-200 (150mm from the -50 face)
    segs += _rect_segs(0, -800, 2000, 600)
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == {0, 1}, f"flush furniture eaten: {det['wall_idx']}"
    cov = WD.coverage_vs_gt(det["centerlines"], [gt])
    assert cov["walls_zero"] == 0 and cov["recall_len"] > 0.99


def test_thin_decor_rect_not_stripped():
    """A 2000x80 curtain: its long edges are a perfect co-terminous pair at gap 80
    (inside the wall window). The same-ring veto must reject it -- classifying decor
    edges as wall ink turned the blind arm into an accidental decor stripper and made
    blind beat oracle (pilot paradox, pinned)."""
    det = WD.detect_walls(_rect_segs(0, 0, 2000, 80))
    assert det["wall_idx"] == set() and det["centerlines"] == []


def test_wall_cavity_ring_stays_detectable():
    """The scene_00023 forensic: a double wall (two co-terminous centerlines 240mm
    apart) whose 140mm cavity is capped by stubs closes an EXACT rectangle of face ink.
    The old all-rings exclusion ate those faces and both walls read zero coverage; the
    size-screened exclusion must keep them pairable and detect both walls."""
    w1 = _wall(0, 0, 1500, 0)
    w2 = _wall(0, 240, 1500, 240)
    cap1 = _wall(0, 50, 0, 190)                    # stubs whose faces cap the cavity
    cap2 = _wall(1500, 50, 1500, 190)
    segs = _wall_ink([w1, w2, cap1, cap2])
    det = WD.detect_walls(segs)
    cov = WD.coverage_vs_gt(det["centerlines"], [w1, w2])
    assert cov["walls_zero"] == 0
    assert cov["recall_len"] > 0.99


def test_neighbour_strips_at_wall_gap_not_paired():
    """The scene_00002 forensic: two neighbours' back-strips, parallel at a wall-like
    144mm gap but offset 12.7mm longitudinally -- real double lines are drawn by offset
    and align exactly, so the CO-TERMINOUS screen must reject this pair."""
    segs = [[(0.0, 0.0), (600.0, 0.0)], [(12.7, 144.3), (612.7, 144.3)]]
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == set()


def test_strip_near_wall_face_not_eaten():
    """The wardrobe scenario: a back-strip 122mm from a wall centerline is parallel and
    inside the gap window, but its ends never align with the wall line's ends -- the
    co-terminous screen must reject the pair (a classified strip = lost F2 emission)."""
    gt = _wall(0, 0, 2000, 0)
    segs = _wall_ink([gt]) + [[(400.0, 122.0), (1480.0, 122.0)]]     # 1080mm strip
    det = WD.detect_walls(segs)
    assert 2 not in det["wall_idx"], "strip misclassified as wall ink"
    assert det["wall_idx"] == {0, 1}


def test_double_wall_all_faces_classified_centerlines_in_band():
    """Two rooms' parallel centerlines 120mm apart draw four faces; cross-pairs are
    legal ink-wise, so the pin is: all four classified, every centerline INSIDE the
    physical band (min face - tol .. max face + tol), nothing outside."""
    w1, w2 = _wall(0, 0, 3000, 0), _wall(0, 120, 3000, 120)
    segs = _wall_ink([w1, w2])
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == {0, 1, 2, 3}
    assert det["centerlines"]
    for c in det["centerlines"]:
        assert -60.0 <= c["y1"] <= 180.0 and -60.0 <= c["y2"] <= 180.0


def test_diagonal_wall_detected():
    gt = _wall(0, 0, 1500, 1500)
    det = WD.detect_walls(_wall_ink([gt]))
    assert det["wall_idx"] == {0, 1}
    c = det["centerlines"][0]
    mx = (c["x1"] + c["x2"]) / 2.0
    my = (c["y1"] + c["y2"]) / 2.0
    assert abs(mx - 750) <= 2.0 and abs(my - 750) <= 2.0


def test_collinear_strokes_never_pair():
    segs = [[(0.0, 0.0), (1000.0, 0.0)], [(1010.0, 0.0), (2000.0, 0.0)]]
    det = WD.detect_walls(segs)
    assert det["wall_idx"] == set()


def test_collinear_centerline_halves_merge():
    """One physical wall drawn as two end-to-end gt segments must come back as ONE
    merged centerline spanning both."""
    w1, w2 = _wall(0, 0, 1000, 0), _wall(1020, 0, 2000, 0)
    det = WD.detect_walls(_wall_ink([w1, w2]))
    assert len(det["centerlines"]) == 1
    c = det["centerlines"][0]
    length = math.hypot(c["x2"] - c["x1"], c["y2"] - c["y1"])
    assert abs(length - 2000) <= 5.0


def test_tilted_end_aligned_stroke_rejected():
    """Adversarial-review geometry repro: a 4.9deg-tilted stroke whose endpoints project
    to [0, L] passes a midpoint-only gap test with align_err 0 while its ends diverge
    85.7mm laterally (gap 100 -> 185.7). The both-endpoint gap test must reject it."""
    segs = [[(0.0, 0.0), (1000.0, 0.0)], [(0.0, 100.0), (1000.0, 185.73)]]
    det = WD.detect_walls(segs, ring_sets=[])
    assert det["wall_idx"] == set(), f"tilted stroke paired: {det['wall_idx']}"


def test_crossing_stroke_rejected():
    """A stroke CROSSING the reference line could average its two side-offsets into the
    gap window; same-side is required."""
    segs = [[(0.0, 0.0), (1000.0, 0.0)], [(0.0, -80.0), (1000.0, 80.0)]]
    det = WD.detect_walls(segs, ring_sets=[])
    assert det["wall_idx"] == set()


def test_double_wall_exact_tie_both_detected():
    """Adversarial-review geometry repro: two walls whose spacing makes the cross pair
    score EXACTLY (0,0,0) -- a single mutual-best pass orphans the second wall by dict
    insertion order; the round-based screen must detect BOTH walls."""
    for spacing in (200.0, 100.0):
        w1 = _wall(0, 0, 3000, 0)
        w2 = _wall(0, spacing, 3000, spacing)
        det = WD.detect_walls(_wall_ink([w1, w2]))
        cov = WD.coverage_vs_gt(det["centerlines"], [w1, w2])
        assert cov["walls_zero"] == 0, (spacing, det["centerlines"])
        assert cov["recall_len"] > 0.99, (spacing, cov)


# ---- coverage vs gt -------------------------------------------------------------------------
def test_coverage_perfect_and_empty():
    walls = [_wall(0, 0, 2000, 0), _wall(0, 0, 0, 1500)]
    det = WD.detect_walls(_wall_ink(walls))
    cov = WD.coverage_vs_gt(det["centerlines"], walls)
    assert cov["recall_len"] > 0.99 and cov["precision_len"] > 0.99
    assert cov["walls_zero"] == 0
    empty = WD.coverage_vs_gt([], walls)
    assert empty["recall_len"] == 0.0 and empty["precision_len"] is None
    assert empty["walls_zero"] == 2
