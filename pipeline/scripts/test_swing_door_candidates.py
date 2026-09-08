"""test_swing_door_candidates.py -- pins for the swing-door arc lane.

Honesty contract pinned here: type='door' must be EARNED (leaf or mirrored double);
arc-only stays type='candidate'; openings never carry rot; every rejection is counted.
Fixtures are self-authored synthetic geometry (the corpus is CC BY-NC, never copied).

    python3 -m pytest test_swing_door_candidates.py -q
"""
import math

import swing_door_candidates as S


def _arc(hx, hy, r, a0_deg, a1_deg, n=17):
    ts = [math.radians(a0_deg + (a1_deg - a0_deg) * k / (n - 1)) for k in range(n)]
    pts = [(hx + r * math.cos(t), hy + r * math.sin(t)) for t in ts]
    return {"cx": hx, "cy": hy, "rx": r, "ry": r,
            "sweep_deg": a1_deg - a0_deg,
            "x1": pts[0][0], "y1": pts[0][1], "x2": pts[-1][0], "y2": pts[-1][1],
            "pts": pts}


def test_arc_plus_leaf_is_typed_door():
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 90)], [[(0, 0), (1000, 0)]])
    assert len(cands) == 1
    c = cands[0]
    assert c["type"] == "door"
    assert c["tier"] == "strong"
    assert c["evidence"]["leaf"] is True
    assert stats["leaf_confirmed"] == 1 and stats["emitted_door"] == 1
    assert abs(c["x"] - 0) <= 1 and abs(c["y"] - 0) <= 1
    assert abs(c["w"] - 1000) <= 1 and abs(c["d"] - 1000) <= 1


def test_arc_only_stays_untyped_candidate():
    # THE mutation pin: deleting the leaf gate and typing everything "door" fails here.
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 90)], [])
    assert len(cands) == 1
    assert cands[0]["type"] == "candidate"
    assert cands[0]["tier"] == "weak"
    assert stats["emitted_candidate"] == 1 and stats["emitted_door"] == 0


def test_openings_never_carry_rot():
    # mirror of the adapter's M6b pin: openings are rot-less, always.
    strong, _ = S.detect([_arc(0, 0, 1000, 0, 90)], [[(0, 0), (1000, 0)]])
    weak, _ = S.detect([_arc(0, 0, 1000, 0, 90)], [])
    for c in strong + weak:
        assert "rot" not in c


def test_negative_sweep_accepted():
    cands, stats = S.detect([_arc(0, 0, 1000, 90, 0)], [])
    assert stats["arcs_quarter"] == 1
    assert len(cands) == 1


def test_sink_scale_arc_rejected():
    # the sink-flood killer: sinks ~50% arc share, basins r<500.
    cands, stats = S.detect([_arc(0, 0, 300, 0, 90)], [])
    assert cands == []
    assert stats["arcs_quarter"] == 1
    assert stats["arcs_in_band"] == 0


def test_half_circle_rejected():
    # two-half-arc circles = furniture, not doors.
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 180)], [])
    assert cands == []
    assert stats["arcs_circular"] == 1
    assert stats["arcs_quarter"] == 0


def test_elliptical_arc_rejected():
    a = _arc(0, 0, 1000, 0, 90)
    a["ry"] = 700
    cands, stats = S.detect([a], [])
    assert stats["arcs_circular"] == 0 and cands == []


def test_bbox_covers_sweep_not_chord():
    # endpoints both at y~707 but the sweep apex is (0,1000): chord-only bbox
    # would give d~0 -- the zero-area lesson.
    cands, _ = S.detect([_arc(0, 0, 1000, 45, 135)], [])
    assert len(cands) == 1
    assert cands[0]["d"] >= 250


def test_double_door_merges_to_one():
    a = _arc(0, 0, 1000, 90, 0)        # tip (0,1000) -> closed (1000,0)
    b = _arc(2000, 0, 1000, 90, 180)   # tip (2000,1000) -> closed (1000,0)
    cands, stats = S.detect([a, b], [])
    assert len(cands) == 1
    c = cands[0]
    assert c["evidence"]["double"] is True
    assert c["type"] == "door"
    assert stats["doubles_merged"] == 1
    assert abs(c["x"] - 0) <= 1 and abs((c["x"] + c["w"]) - 2000) <= 1


def test_adjacent_singles_not_merged():
    a = _arc(0, 0, 1000, 90, 0)        # closed at (1000,0)
    c = _arc(2000, 0, 1000, 90, 0)     # closed at (3000,0): min end gap ~1414 > 300
    cands, stats = S.detect([a, c], [])
    assert len(cands) == 2
    assert stats["doubles_merged"] == 0


def test_overprint_dupe_dropped():
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 90), _arc(0, 0, 1000, 0, 90)], [])
    assert len(cands) == 1
    assert stats["dupes_dropped"] == 1


def test_leaf_wrong_length_not_confirmed():
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 90)], [[(0, 0), (500, 0)]])
    assert len(cands) == 1
    assert cands[0]["tier"] == "weak"
    assert cands[0]["evidence"]["leaf"] is False
    assert stats["leaf_confirmed"] == 0


def test_correct_length_leaf_far_from_hinge_not_confirmed():
    # THE hinge-proximity pin (scrutiny 2026-07-07): a segment of the CORRECT leaf
    # length (~r) but NOT touching the hinge must NOT confirm a door. Without this,
    # deleting the hinge-proximity gate degrades the leaf test to "any ~r-long segment
    # anywhere on the sheet earns type='door'" -- the unearned-credit flood the module
    # forbids. Leaf here is 1000 mm long (== r) but sits at (5000,0)->(6000,0), both
    # ends >> leaf_end_tol from the hinge (0,0).
    cands, stats = S.detect([_arc(0, 0, 1000, 0, 90)],
                            [[(5000.0, 0.0), (6000.0, 0.0)]])
    assert len(cands) == 1
    assert cands[0]["type"] == "candidate"
    assert cands[0]["tier"] == "weak"
    assert cands[0]["evidence"]["leaf"] is False
    assert stats["leaf_confirmed"] == 0 and stats["emitted_door"] == 0


def test_stats_shape_pinned_and_empty_input():
    cands, stats = S.detect([], [])
    assert cands == []
    assert set(stats) == {"arcs_seen", "arcs_circular", "arcs_quarter",
                          "arcs_in_band", "dupes_dropped", "leaf_confirmed",
                          "doubles_merged", "emitted_door", "emitted_candidate"}
    assert all(v == 0 for v in stats.values())


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
