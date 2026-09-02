"""test_panel_diff.py — the differential, and the one claim it is allowed to make."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel_diff as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANELS = [os.path.join(REPO, "_private", "deliv-001", p)
          for p in ("exit-panel-p2r95", "exit-panel-p2r96")]
HAVE = all(os.path.isfile(os.path.join(p, "panel_key.json")) for p in PANELS)


def test_a_theme_only_ours_gets_scores_positive():
    rows = [(True, ["the bench is enormous"]), (True, ["shrink the bench"]),
            (False, ["recompose"]), (False, ["lift the exposure"])]
    table, no, np_ = pd.differential(rows)
    bench = next(r for r in table if r["theme"] == "bench/ottoman")
    assert bench["ours_pct"] == 100.0 and bench["peers_pct"] == 0.0
    assert bench["diff"] == 100.0
    assert (no, np_) == (2, 2)


def test_a_theme_everyone_gets_scores_near_zero():
    """THE POINT OF THE MODULE. A complaint the delivered work attracts too is not what
    separates us from it, and must not read as our defect."""
    rows = [(True, ["the window is blown"]), (False, ["the window is blown"]),
            (False, ["recover the window"]), (False, ["the glazing is hot"])]
    table, _, _ = pd.differential(rows)
    win = next(r for r in table if r["theme"] == "window/glare")
    assert win["ours_pct"] == 100.0 and win["peers_pct"] == 100.0
    assert win["diff"] == 0.0


def test_it_refuses_a_one_sided_panel():
    with pytest.raises(RuntimeError, match="need both"):
        pd.differential([(True, ["only ours"])])


def test_missing_panel_is_exit_2(tmp_path):
    assert pd.main([str(tmp_path)]) == 2


@pytest.mark.skipif(not HAVE, reason="panels not on disk")
def test_the_real_panels_rank_bench_and_headboard_above_the_window():
    """Regression on the finding that redirected P2r-38/39: two items nobody had worked
    on separate us further than the one two rounds were spent on."""
    rows = []
    for p in PANELS:
        rows += pd.read_panel(p)
    table, n_ours, n_peers = pd.differential(rows)
    assert n_ours >= 6 and n_peers >= 24
    order = [r["theme"] for r in table]
    assert order.index("bench/ottoman") < order.index("window/glare")
    assert order.index("headboard") < order.index("window/glare")
    win = next(r for r in table if r["theme"] == "window/glare")
    assert win["peers_pct"] >= 50.0, (
        "the window bar was dropped because the DELIVERED field fails it too; if this "
        "ever drops below half, that reasoning needs re-checking")
    cam = next(r for r in table if r["theme"] == "camera/crop")
    assert cam["diff"] < 0, "the camera is supposed to be our advantage over the field"
