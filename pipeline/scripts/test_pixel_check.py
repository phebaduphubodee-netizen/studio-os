"""Tests for pixel_check — the first gate rung in this repo that opens the picture.

Owner order 2026-08-09: "ผมขอบังคับให้ทุกกลไก ทุกขั้นตอนต้องมองรูปจริง". Measured
that day: of the 8 modules the render gate calls, 0 ever opened an image; of the
21 instruments that do, 0 were called by any of them.

The negative controls here are the ways a pixel check can lie, and each one has a
name in this lane's history:
  * the feature is NOT in our frame and the fit returns a confident number anyway
    (r38's absence argument, which had no positive control)
  * the stored target numbers came from a DIFFERENT estimator than the checker's
    (the first cut of this lane's own pixel_claims block failed exactly here)
  * the search window is wide enough to lock onto the neighbouring feature
    (20 px away on the headboard's near end)

The last test is the one that matters: a REAL frame from before the defect was
fixed must fail.
"""
import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_check as PC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "_private", "benchmark", "reproduction", "TRN-002")
TARGET = os.path.join(LANE, "target.jpg")


def _frame(path, edge_u, contrast=80, w=200, h=120, second=None):
    """A bright field with a vertical step at `edge_u` (and optionally a second)."""
    a = np.full((h, w), 180.0)
    a[:, int(edge_u):] -= contrast
    if second is not None:
        a[:, int(second):int(second) + 2] -= 45
    Image.fromarray(np.dstack([a, a, a]).astype("uint8")).save(path)
    return str(path)


def _claim(**kw):
    c = {"name": "edge", "mass": "m", "kind": "v_edge", "along": [20, 100],
         "step": 1, "search_px": 8, "tol_px": 2.0,
         "target": {"slope": 0.0, "intercept": 100.0}}
    c.update(kw)
    return c


def _spec(claims, masses=1):
    return {"masses": [{"name": f"m{i}"} for i in range(masses)],
            "pixel_claims": claims}


# --- it measures, and it agrees with itself -----------------------------------

def test_a_frame_that_matches_the_target_passes(tmp_path):
    t = _frame(tmp_path / "t.png", 100)
    o = _frame(tmp_path / "o.png", 100)
    assert PC.check(_spec([_claim()]), o, t) == []


def test_the_report_gives_numbers_even_when_it_passes(tmp_path):
    t = _frame(tmp_path / "t.png", 100)
    o = _frame(tmp_path / "o.png", 100)
    rows = PC.report(_spec([_claim()]), o, t)
    assert len(rows) == 1
    name, ours, tgt, d, cr, rms = rows[0]
    assert abs(d) < 0.5 and cr == pytest.approx(1.0, abs=0.05)


# --- the ways it must fail -----------------------------------------------------

def test_a_feature_in_the_wrong_place_fails(tmp_path):
    t = _frame(tmp_path / "t.png", 100)
    o = _frame(tmp_path / "o.png", 105)          # 5 px away, tolerance 2
    v = PC.check(_spec([_claim()]), o, t)
    assert len(v) == 1 and "tolerance" in v[0]


def test_a_feature_ABSENT_from_our_frame_fails_as_absent_not_as_a_number(tmp_path):
    """The positive control r38's absence argument did not have: our contrast is
    judged against the TARGET's own contrast at the same feature."""
    t = _frame(tmp_path / "t.png", 100, contrast=80)
    o = _frame(tmp_path / "o.png", 100, contrast=2)   # the edge is barely there
    v = PC.check(_spec([_claim()]), o, t)
    assert len(v) == 1
    assert "not in our frame" in v[0] and "0.0" in v[0].replace("0.02x", "0.0")


def test_stored_numbers_from_a_different_estimator_fail_the_self_check(tmp_path):
    """The first cut of this lane's own claims failed here: the target block had
    been copied from a round's probe, which used a different sub-pixel rule."""
    t = _frame(tmp_path / "t.png", 100)
    o = _frame(tmp_path / "o.png", 100)
    v = PC.check(_spec([_claim(target={"slope": 0.0, "intercept": 103.0})]), o, t)
    assert len(v) == 1 and "SELF-CHECK FAILED" in v[0]


def test_the_search_window_cannot_reach_the_neighbouring_feature(tmp_path):
    """On the headboard's near end the two features are 20 px apart. With a wide
    window the strongest edge wins and the checker reports the WRONG feature's
    position as if it were the right one — measured on the real pair before this
    was fixed."""
    t = _frame(tmp_path / "t.png", 120, contrast=80, second=100)
    o = _frame(tmp_path / "o.png", 120, contrast=80)      # the welt is gone
    # the stored number is what THIS checker reads on the target (99.5, the dark
    # band's left flank) — deriving it any other way is the defect the self-check
    # above already covers, and mixing the two would test two things at once.
    claim = _claim(target={"slope": 0.0, "intercept": 99.5}, search_px=8)
    v = PC.check(_spec([claim]), o, t)
    assert len(v) == 1, "a vanished feature must not be answered by its neighbour"
    assert "not in our frame" in v[0] or "not one edge" in v[0]


def test_an_unreadable_frame_is_a_violation_not_a_pass(tmp_path):
    t = _frame(tmp_path / "t.png", 100)
    v = PC.check(_spec([_claim()]), str(tmp_path / "nope.png"), t)
    assert len(v) == 1 and "must not report that it looked" in v[0]


def test_no_claims_is_silence_not_a_pass_claim(tmp_path):
    t = _frame(tmp_path / "t.png", 100)
    assert PC.check({"masses": []}, t, t) == []


def test_unclaimed_counts_the_hole_it_leaves(tmp_path):
    notes = PC.unclaimed(_spec([_claim(mass="m0")], masses=4))
    assert len(notes) == 1 and "3 of 4 masses carry no pixel claim" in notes[0]


# --- and the real thing --------------------------------------------------------

@pytest.mark.skipif(not os.path.isfile(TARGET), reason="reference not on this machine")
def test_the_lane_claims_hold_on_the_frame_of_record():
    spec = json.load(open(os.path.join(REPO, "training", "TRN-002",
                                       "spec_r38.json"), encoding="utf-8"))
    frame = os.path.join(LANE, "renders", "trn002_mat_r38b.png")
    if not os.path.isfile(frame):
        pytest.skip("frame of record not on this machine")
    assert PC.check(spec, frame, TARGET) == []


@pytest.mark.skipif(not os.path.isfile(TARGET), reason="reference not on this machine")
def test_it_would_have_caught_the_defect_that_survived_to_r38():
    """THE PIN THAT JUSTIFIES THE RUNG. trn002_mat_r32.png is a full frame built
    with the invented 176 mm headboard — the number r37 measured away and r38
    applied. Run today's claims against it and the rung fails, naming the right
    reason: the feature is not in our frame at all. Six rounds of gates passed
    that frame because not one of them opened it."""
    spec = json.load(open(os.path.join(REPO, "training", "TRN-002",
                                       "spec_r38.json"), encoding="utf-8"))
    old = os.path.join(LANE, "renders", "trn002_mat_r32.png")
    if not os.path.isfile(old):
        pytest.skip("historical frame not on this machine")
    v = PC.check(spec, old, TARGET)
    assert v, "the pre-fix frame must not pass the claims written after the fix"
    assert any("not in our frame" in s for s in v)


def test_a_playblast_refuses_rather_than_passing(tmp_path):
    """'could not look' must never print like 'looked and it was fine'. The very
    first build to call this rung was an R5 quick frame at half resolution."""
    t = _frame(tmp_path / "t.png", 100, w=200, h=120)
    o = _frame(tmp_path / "o.png", 50, w=100, h=60)
    with pytest.raises(PC.NotComparable):
        PC.check(_spec([_claim()]), o, t)
    assert PC.report(_spec([_claim()]), o, t) == []
