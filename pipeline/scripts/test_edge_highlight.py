#!/usr/bin/env python3
"""Tests for edge_highlight.py — the rung that asks whether an edge in this frame
is wide enough to catch a highlight at all.

THE PROPERTY THESE TESTS PIN, and it is the one worth pinning: this rung must stay
a REPORTING LINE. Every case that would tempt a future round to promote it into a
cut is written down here as an assertion that it did NOT change the exit code.
A frame that is 100% invisible edges still exits 0, because the pixel width a
highlight needs has never been measured off delivered work — and a threshold
invented in this file would carry this file's authority instead of the anchor
pool's. If someone measures that band, they change these tests deliberately.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edge_highlight as EH                                  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "edge_highlight.py")


def _dump(tmp_path, objs, name="d.scene.json", res=(2400, 1800)):
    p = tmp_path / name
    doc = {"schema": "scene-dump@2", "objects": objs}
    if res is not None:
        doc["render_res"] = list(res)
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


def _run(path):
    r = subprocess.run([sys.executable, SCRIPT, path], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _obj(name, mm, mm_per_px, area=1.0, **kw):
    d = {"name": name, "hidden_render": False, "in_frustum": True,
         "bevel_m": mm / 1000.0, "bevel_segments": 2, "area_m2": area,
         "mm_per_px": mm_per_px}
    d.update(kw)
    return d


# ------------------------------------------------------------- the arithmetic

def test_the_millwork_arris_at_the_wall_is_a_third_of_a_pixel():
    """The measured case that produced this file. 1.2 mm at the eye camera's
    ~3.2 mm/px on the wardrobe wall. Written as a number here, not derived from
    the module, so a change to the formula fails rather than agrees with itself."""
    px = EH.bevel_px(_obj("mill", 1.2, 3.2))
    assert abs(px - 0.375) < 0.001


def test_the_same_bevel_is_visible_in_the_foreground():
    """The identical millimetre value passes and fails depending only on where the
    object stands — which is the entire finding, and the reason a mm-domain rule
    could never have caught it."""
    assert EH.bevel_px(_obj("near", 1.2, 0.833)) > 1.4
    assert EH.bevel_px(_obj("far", 1.2, 3.2)) < 0.4


def test_an_object_with_no_camera_behind_it_is_None_not_zero():
    """The third state. An unmeasured object counted as fine is the vacuous zero
    this repo has now filed under four names."""
    o = _obj("x", 1.2, 3.2)
    del o["mm_per_px"]
    assert EH.bevel_px(o) is None


def test_a_zero_mm_per_px_is_None_rather_than_a_division():
    o = _obj("x", 1.2, 0.0)
    assert EH.bevel_px(o) is None


def test_bands_are_buckets_and_one_pixel_is_the_only_meaningful_edge():
    assert EH.band(0.3) == "invisible"
    assert EH.band(0.9) == "sub-pixel"
    assert EH.band(1.5) == "one-pixel"
    assert EH.band(3.0) == "readable"
    assert EH.band(99.0) == "wide"


# ------------------------------------------------------------- what it measures

def test_out_of_frame_masses_are_excluded_but_unknown_frustum_is_kept():
    """`in_frustum: False` is a real "not in the picture". A MISSING key is
    unknown, and unknown must be measured rather than dropped — dropping it would
    let a dump with no camera report a clean, empty result."""
    objs = [_obj("in", 5.0, 1.0, area=2.0),
            _obj("out", 5.0, 1.0, area=9.0, in_frustum=False),
            _obj("unknown", 5.0, 1.0, area=3.0)]
    objs[2].pop("in_frustum")
    rows, _n, _u, _nb, _anb = EH.measure(objs)
    assert [r["name"] for r in rows] == ["unknown", "in"]


def test_hidden_masses_are_excluded():
    objs = [_obj("shown", 5.0, 1.0), _obj("hidden", 5.0, 1.0, hidden_render=True)]
    rows, _n, _u, _nb, _anb = EH.measure(objs)
    assert [r["name"] for r in rows] == ["shown"]


def test_rows_come_back_largest_area_first():
    """The report is read by an eye looking for what dominates the frame, so the
    order is part of the deliverable, not a formatting choice."""
    objs = [_obj("small", 5.0, 1.0, area=0.2),
            _obj("huge", 5.0, 1.0, area=18.4),
            _obj("mid", 5.0, 1.0, area=3.0)]
    rows, _n, _u, _nb, _anb = EH.measure(objs)
    assert [r["name"] for r in rows] == ["huge", "mid", "small"]


def test_unmeasurable_objects_are_counted_separately_not_silently_dropped():
    o = _obj("nocam", 1.2, 3.2)
    del o["mm_per_px"]
    rows, n_bev, unmeasurable, _nb, _anb = EH.measure([_obj("ok", 5.0, 1.0), o])
    assert len(rows) == 1 and n_bev == 2 and unmeasurable == 1


# --------------------------------------------------------- it stays a REPORT

def test_a_frame_where_every_edge_is_invisible_still_exits_0(tmp_path):
    """THE LOAD-BEARING TEST. This is the worst case the rung can see, and it is
    still a report. Promoting it to a cut needs an anchor-pool measurement, not a
    strong feeling about this number."""
    objs = [_obj(f"m{i}", 1.2, 3.2, area=10.0 - i) for i in range(6)]
    code, out = _run(_dump(tmp_path, objs))
    assert code == 0, out
    assert "6/6 (100%) OF THE MEASURED subtend LESS THAN ONE PIXEL" in out
    assert "REPORTING LINE, NOT A CUT" in out


def test_the_report_names_the_biggest_masses_with_all_three_numbers(tmp_path):
    """mm, mm/px and px must all print. A report that gave only the px would hide
    which half moved — the bevel or the camera — and the camera moves often."""
    code, out = _run(_dump(tmp_path, [_obj("mill__carcass", 1.2, 3.2, area=18.4)]))
    assert code == 0, out
    assert "1.20 mm" in out and "3.20 mm/px" in out and "0.37 px" in out


# ------------------------------------------------------- the could-not-run gate

def test_a_dump_with_no_bevel_key_exits_2(tmp_path):
    p = _dump(tmp_path, [{"name": "a", "in_frustum": True, "mm_per_px": 2.0}])
    code, out = _run(p)
    assert code == 2 and "bevel_m" in out


def test_a_dump_with_bevels_but_no_camera_exits_2(tmp_path):
    p = _dump(tmp_path, [{"name": "a", "in_frustum": True, "bevel_m": 0.005}])
    code, out = _run(p)
    assert code == 2 and "mm_per_px" in out


def test_bevels_that_are_all_out_of_frame_exit_2_rather_than_report_nothing(
        tmp_path):
    """"Nothing to measure" is not "nothing wrong". An empty report that exited 0
    would read exactly like a clean frame."""
    p = _dump(tmp_path, [_obj("out", 5.0, 1.0, in_frustum=False)])
    code, out = _run(p)
    assert code == 2, out


def test_an_unreadable_dump_exits_2(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    code, out = _run(str(p))
    assert code == 2, out


def test_a_dump_with_no_render_res_exits_2(tmp_path):
    """FOUND BY RUNNING IT, not by thinking about it. The first live artefact was a
    `_ql` playblast at 1200x900 against a delivered 2400x1800, so every pixel
    figure in that report was half. A px count with no resolution attached is not
    a measurement, and this rung refuses rather than guessing which one it got —
    the same choice R11's pixel rung already made in its own words."""
    p = _dump(tmp_path, [_obj("m", 1.2, 3.2)], res=None)
    code, out = _run(p)
    assert code == 2, out
    assert "render_res" in out


def test_the_resolution_is_printed_on_every_report(tmp_path):
    """Half of the fix is refusing without it; the other half is SAYING which one
    it used, so a reader comparing two rounds can see whether the camera moved or
    the bevel did."""
    code, out = _run(_dump(tmp_path, [_obj("m", 1.2, 3.2)], res=(2400, 1800)))
    assert code == 0, out
    assert "measured at 2400x1800" in out


def test_a_malformed_render_res_is_refused_rather_than_coerced(tmp_path):
    for bad in ([0, 1800], ["2400", "1800"], [2400], "2400x1800"):
        p = _dump(tmp_path, [_obj("m", 1.2, 3.2)], res=bad,
                  name=f"d{abs(hash(str(bad)))}.json")
        code, out = _run(p)
        assert code == 2, (bad, out)


def test_masses_with_no_bevel_at_all_are_counted_and_named(tmp_path):
    """THE WORST ANSWER TO THIS RUNG'S OWN QUESTION, which the first version dropped.
    A mass with no bevel modifier is a knife edge — 0 px by construction — and
    `_bevel_edges` skips every ph_model/acquired mass, so the set is large, not rare."""
    objs = [_obj("bevelled", 5.0, 1.0, area=1.0),
            {"name": "acq_sofa", "hidden_render": False, "in_frustum": True,
             "area_m2": 9.0},
            {"name": "acq_rug", "hidden_render": False, "in_frustum": True,
             "area_m2": 4.0}]
    rows, _n, _u, n_no_bev, area_no_bev = EH.measure(objs)
    assert len(rows) == 1
    assert n_no_bev == 2 and abs(area_no_bev - 13.0) < 1e-9
    code, out = _run(_dump(tmp_path, objs))
    assert code == 0, out
    assert "carry NO bevel modifier at all" in out
    assert "13.0 m" in out


def test_the_headline_ratio_names_the_population_it_is_over(tmp_path):
    """The ratio is computed over the MEASURABLE subset, so it must say so whenever
    that is not the whole in-frame bevelled population — otherwise a reader carries
    away a percentage of a denominator nobody stated."""
    o = _obj("nocam", 1.2, 3.2, area=20.0)
    del o["mm_per_px"]
    code, out = _run(_dump(tmp_path, [_obj("m", 1.2, 3.2, area=1.0), o]))
    assert code == 0, out
    assert "OF THE MEASURED" in out
    assert "NOT measured (no camera behind them)" in out
