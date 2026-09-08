"""exit_panel — the plan's exit test as one command (audit 2026-09-01).

What these tests pin: the key decodes a judge's letters back to OURS/F*; the
counter fires on a full frame newer than the last panel and stays quiet on a
quick leg; packs are refused anywhere git can see them; a pool of two is a
coin. No Blender, no PIL beyond a 2-px PNG."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import exit_panel as EP  # noqa: E402


def _key(out, render="pipeline/output/room_x_p2r99.png"):
    key = {"render": render, "render_sha1": "abc", "seed": 1,
           "judges": {"j1": {"A": {"tag": "OURS"}, "B": {"tag": "F2"},
                             "C": {"tag": "F3"}, "D": {"tag": "F1"}}}}
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "panel_key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f)
    return key


def _repo(tmp_path, monkeypatch):
    monkeypatch.setattr(EP, "REPO", str(tmp_path))
    os.makedirs(tmp_path / "qa", exist_ok=True)
    os.makedirs(tmp_path / "pipeline" / "output", exist_ok=True)
    return tmp_path


def test_record_decodes_through_the_key(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch)
    out = str(tmp_path / "_private" / "panel")
    _key(out)
    row = EP.record(out, "j1", '{"A": 61, "B": 55, "C": 80, "D": 50}',
                    '["C", "A", "B", "D"]', "v.md", "sendable-after-minor-fixes",
                    "D", "")
    assert row["ours_letter"] == "A"
    assert row["ours_score"] == 61 and row["ours_rank"] == 2 and row["field"] == 4
    assert row["order"] == ["F3", "OURS", "F2", "F1"]
    assert row["scores"]["F3"] == 80
    assert row["odd_one_out"] == "F1"
    log = json.load(open(tmp_path / "qa" / "exit-panel-log.json", encoding="utf-8"))
    assert log["runs"][-1]["ours_score"] == 61


def test_status_owes_a_panel_for_a_full_frame_but_not_a_quick_leg(tmp_path, monkeypatch):
    _repo(tmp_path, monkeypatch)
    out = str(tmp_path / "_private" / "panel")
    _key(out)
    EP.record(out, "j1", '{"A": 61, "B": 55, "C": 80, "D": 50}',
              '["C", "A", "B", "D"]', "v.md", "sendable", "D", "")
    lines = EP.status()
    assert lines[0].startswith("EXIT PANEL: last on")
    assert "OURS 61" in lines[0] and "rank 2/4" in lines[0]
    assert not any("OWED" in ln for ln in lines)
    # a full frame lands after the panel: > 1 MB, room_*.png, newer mtime
    time.sleep(1.1)
    full = tmp_path / "pipeline" / "output" / "room_x_p2r100.png"
    full.write_bytes(b"\0" * 1_000_001)
    quick = tmp_path / "pipeline" / "output" / "room_x_p2r100_ql.png"
    quick.write_bytes(b"\0" * 1_000_001)
    lines = EP.status()
    owed = [ln for ln in lines if "OWED" in ln]
    assert owed and "room_x_p2r100.png" in owed[0] and "_ql" not in owed[0]
    assert "1 full frame" in owed[0]


def test_status_never_recorded_says_zero_runs(tmp_path, monkeypatch):
    _repo(tmp_path, monkeypatch)
    lines = EP.status()
    assert "never recorded" in lines[0] and "0 runs" in lines[0]


def test_packs_are_refused_inside_the_repo_outside_private(tmp_path, monkeypatch):
    _repo(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        EP._out_is_safe(str(tmp_path / "pipeline" / "output" / "panel"))
    EP._out_is_safe(str(tmp_path / "projects" / "x" / "_private" / "panel"))
    EP._out_is_safe(str(tmp_path.parent / "elsewhere"))


def test_pool_of_two_is_a_coin(tmp_path, monkeypatch):
    _repo(tmp_path, monkeypatch)
    for n in ("a.png", "b.png"):
        (tmp_path / n).write_bytes(b"x")
    pool = tmp_path / "pool.json"
    pool.write_text(json.dumps({"frames": [{"tag": "F1", "path": "a.png"},
                                            {"tag": "F2", "path": "b.png"}]}))
    with pytest.raises(SystemExit) as e:
        EP._pool(str(pool))
    assert "at least 3" in str(e.value)
    with pytest.raises(SystemExit) as e:
        EP._pool(str(tmp_path / "missing.json"))
    assert "no pool" in str(e.value)
