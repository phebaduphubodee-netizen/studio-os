"""Tests for style_measure.write() — the palette ratchet's write side.

THIS FILE EXISTS BECAUSE THE RATCHET HAD NO TESTS AT ALL. style_check's
`test_unsigned_ceiling_only_ever_falls` covers the SLOT ceiling, which is a
read-side comparison; the gap ceiling's `min()` — the only place the words "only
ever falls" are actually implemented — had zero coverage, and a live bug sat in
the branch beside it: a could-not-run replaced the whole palette_measured block
and dropped gap_ceiling, so "I could not look at the picture" silently deleted
the record of the last time something could.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_measure as SM  # noqa: E402


def _register(tmp_path, **palette):
    qa = tmp_path / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    reg = {"palette_measured": dict(palette)} if palette else {}
    (qa / "style-of-record.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return tmp_path


def _read(tmp_path):
    return json.loads((tmp_path / "qa" / "style-of-record.json").read_text(
        encoding="utf-8"))["palette_measured"]


PREV = {"dominant_share": 0.3, "secondary_share": 0.19, "accent_share": 0.18,
        "gap_worst": 0.3002, "gap_ceiling": 0.3202, "gap_since": "2026-08-23",
        "close_by": "sign the floor slot", "_honest_note": "the gap is WIDE",
        "declared": {"dominant": 0.60, "secondary": 0.30, "accent": 0.10}}


def _result(dom, sec, acc):
    return {"palette": {"dominant_share": dom, "secondary_share": sec,
                        "accent_share": acc, "entropy": 0.9, "k": 6}}


def test_a_could_not_run_does_not_erase_the_ratchet(tmp_path):
    """THE BUG, pinned: before 2026-08-24 this dropped gap_ceiling entirely."""
    _register(tmp_path, **PREV)
    SM.write("f.png", None, "no PIL", repo_root=str(tmp_path), today="2026-08-24")
    b = _read(tmp_path)
    assert b["could_not_run"] == "no PIL"
    assert b["gap_ceiling"] == 0.3202
    assert b["gap_worst"] == 0.3002
    assert b["gap_since"] == "2026-08-23"


def test_a_could_not_run_then_a_worse_frame_still_cannot_raise_the_ceiling(tmp_path):
    """The bug's actual consequence, end to end: could-not-run, then a frame
    measuring 0.55. Without the carry-forward the ceiling re-seeds at 0.57 and
    the worse frame PASSES. With it, the ceiling stays 0.3202 and the gate bites."""
    _register(tmp_path, **PREV)
    SM.write("f.png", None, "no PIL", repo_root=str(tmp_path), today="2026-08-24")
    SM.write("g.png", _result(0.05, 0.30, 0.10), None,
             repo_root=str(tmp_path), today="2026-08-24")
    b = _read(tmp_path)
    assert b["gap_worst"] == 0.55
    assert b["gap_ceiling"] == 0.3202, "a could-not-run laundered the ratchet"


def test_the_ceiling_falls_on_a_better_frame_and_never_rises(tmp_path):
    _register(tmp_path, **PREV)
    SM.write("g.png", _result(0.55, 0.30, 0.10), None,      # worst 0.05
             repo_root=str(tmp_path), today="2026-08-24")
    assert _read(tmp_path)["gap_ceiling"] == 0.07            # 0.05 + 0.02
    SM.write("h.png", _result(0.20, 0.30, 0.10), None,      # worst 0.40, worse
             repo_root=str(tmp_path), today="2026-08-25")
    b = _read(tmp_path)
    assert b["gap_worst"] == 0.40 and b["gap_ceiling"] == 0.07


def test_the_first_honest_measurement_seeds_the_ceiling(tmp_path):
    _register(tmp_path, declared={"dominant": 0.60, "secondary": 0.30,
                                  "accent": 0.10})
    SM.write("f.png", _result(0.30, 0.19, 0.18), None,
             repo_root=str(tmp_path), today="2026-08-24")
    b = _read(tmp_path)
    assert b["gap_worst"] == 0.3 and b["gap_ceiling"] == 0.32
    assert b["gap_since"] == "2026-08-24"


def test_gap_since_is_kept_across_measurements(tmp_path):
    _register(tmp_path, **PREV)
    SM.write("g.png", _result(0.31, 0.30, 0.10), None,
             repo_root=str(tmp_path), today="2026-08-30")
    assert _read(tmp_path)["gap_since"] == "2026-08-23"


def test_a_playblast_is_refused_by_name():
    for n in ("room_x_ql.png", "room_x_quick.png", "room-ql.png",
              "playblast_3.png"):
        assert SM._is_quick(n) if hasattr(SM, "_is_quick") else any(
            m in n for m in SM.QUICK_MARKERS)
