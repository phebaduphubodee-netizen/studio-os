"""Tests for floor_openings -- doors/windows/glass as real build geometry.

Pins: a window CUTS the wall segment it sits in (both faces, wall may split in two);
a segment away from every opening is untouched; window contributes sill+glass+lintel,
door contributes lintel only, glass runs sill-to-ceiling when head is None, bare
opening contributes nothing; heights fall back to DISCLOSED render defaults."""
import floor_openings as FO


def test_window_cuts_wall_and_splits_it():
    segs = [[[0, -698], [5000, -698]], [[0, -799], [5000, -799]]]
    ops = [{"type": "window", "rect": [2000, -799, 2600, -698]}]
    kept, n_cuts = FO.clip_wall_segments(segs, ops)
    assert n_cuts == 2                       # both faces cut
    assert len(kept) == 4                    # each face split in two
    spans = sorted((min(a[0], b[0]), max(a[0], b[0])) for a, b in kept)
    assert (0.0, 2000.0) in spans and (2600.0, 5000.0) in spans


def test_far_segment_untouched_and_diagonal_passthrough():
    segs = [[[0, 5000], [3000, 5000]], [[0, 0], [1000, 1000]]]
    ops = [{"type": "door", "rect": [1000, -100, 1900, 100]}]
    kept, n_cuts = FO.clip_wall_segments(segs, ops)
    assert n_cuts == 0 and len(kept) == 2


def test_vertical_wall_cut():
    segs = [[[10650, 0], [10650, 3000]]]
    ops = [{"type": "window", "rect": [10550, 800, 10750, 1600]}]
    kept, n_cuts = FO.clip_wall_segments(segs, ops)
    assert n_cuts == 1 and len(kept) == 2
    spans = sorted((min(a[1], b[1]), max(a[1], b[1])) for a, b in kept)
    assert spans == [(0.0, 800.0), (1600.0, 3000.0)]


def test_window_boxes_sill_glass_lintel():
    boxes = FO.opening_boxes({"type": "window", "rect": [0, 0, 600, 100]}, 2800)
    kinds = [(b["kind"], b["z0_mm"], b["z1_mm"]) for b in boxes]
    assert kinds == [("wall", 0.0, 900.0), ("glass", 900.0, 2200.0),
                     ("wall", 2200.0, 2800.0)]        # render DEFAULTS, disclosed


def test_door_lintel_only_and_opening_nothing():
    door = FO.opening_boxes({"type": "door", "rect": [0, 0, 900, 100]}, 2800)
    assert [(b["kind"], b["z0_mm"], b["z1_mm"]) for b in door] == [("wall", 2000.0, 2800.0)]
    assert FO.opening_boxes({"type": "opening", "rect": [0, 0, 2000, 100]}, 2800) == []


def test_glass_full_height_when_head_none():
    g = FO.opening_boxes({"type": "glass", "rect": [0, 0, 4898, 100]}, 2800)
    assert [(b["kind"], b["z0_mm"], b["z1_mm"]) for b in g] == [("glass", 0.0, 2800.0)]


def test_sliding_is_two_offset_panels_not_a_monolith():
    """Owner 2026-07-10: 'ประตูเลื่อน ไม่ใช่แผ่นกระจก' -- a sliding door renders as TWO
    overlapping panels on two tracks, never one fixed pane."""
    b = FO.opening_boxes({"type": "sliding", "rect": [7150, 2000, 9900, 2100]}, 2800)
    assert len(b) == 2 and all(x["kind"] == "glass" for x in b)
    (r1, r2) = (b[0]["rect"], b[1]["rect"])
    assert r1[3] - r1[1] < 100 and r2[3] - r2[1] < 100        # each on its own track
    assert r1[2] > r2[0]                                       # panels overlap mid-run
    assert b[0]["z1_mm"] == 2400.0                             # door height, not ceiling


def test_railing_is_a_low_parapet_band():
    b = FO.opening_boxes({"type": "railing", "rect": [5752, 99, 10650, 200]}, 2800)
    assert [(x["kind"], x["z0_mm"], x["z1_mm"]) for x in b] == [("wall", 0.0, 1000.0)]


def test_explicit_heights_override_defaults():
    b = FO.opening_boxes({"type": "window", "rect": [0, 0, 600, 100],
                          "sill_mm": 1200, "head_mm": 2400}, 2800)
    assert [(x["z0_mm"], x["z1_mm"]) for x in b] == [(0.0, 1200.0), (1200.0, 2400.0),
                                                     (2400.0, 2800.0)]
