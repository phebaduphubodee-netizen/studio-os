#!/usr/bin/env python3
"""Tests for experiment_3leg.py (pure parts only — no paid calls, no Pillow required).

Run: python -m pytest test_experiment_3leg.py -q   (cwd = pipeline/scripts)
"""
import json

import pytest

import experiment_3leg as ex


def test_summarize_rolls_means_and_error_exclusion():
    """ERROR rolls must be excluded from the MEAN but counted in the tally — an API
    failure scored as 0 would fake a REWORK (the flattering-scorer's evil twin)."""
    rolls = [
        {"overall_0_5": 4.0, "verdict": "SHIP", "scores": {"lighting_quality": 5, "styling_and_life": 3}},
        {"overall_0_5": 3.0, "verdict": "REWORK", "scores": {"lighting_quality": 4, "styling_and_life": 4}},
        {"verdict": "ERROR", "one_line": "boom"},
    ]
    s = ex.summarize_rolls(rolls)
    assert (s["n_rolls"], s["n_scored"]) == (3, 2)
    assert s["mean_overall"] == 3.5
    assert s["mean_scores"]["lighting_quality"] == 4.5
    assert s["verdicts"] == {"SHIP": 1, "REWORK": 1, "ERROR": 1}


def test_summarize_rolls_all_errors_has_no_mean():
    s = ex.summarize_rolls([{"verdict": "ERROR"}])
    assert s["mean_overall"] is None
    assert s["n_scored"] == 0


def test_de_verdict_note_bands():
    """Bands quote brand_qa 1.0/2.0 as reference points; boundary semantics follow
    delta_e00.brand_compliance (exactly 1.0 = warn band, not pass). The pass-band note
    must NOT overclaim: k=6 whole-image sampling cannot see per-piece swaps, so it says
    'not proof of preservation' (review finding 2026-07-14 — flattering wording)."""
    assert "not proof of preservation" in ex.de_verdict_note(0.4)
    assert "warn band" in ex.de_verdict_note(1.0)
    assert "inspect" in ex.de_verdict_note(2.5)
    assert ex.de_verdict_note(None) == "not scored"


def test_markdown_report_names_all_legs_and_missing_stays_loud(tmp_path):
    """A missing leg must render as MISSING in the report, never silently dropped."""
    res = {
        "date": "2026-07-14", "spec": "spec.json", "room_type": "sitting_room",
        "material_story": "floor: light birch",
        "legs": {
            "A": {"image": "a.png", "sanity": {"verdict": "PASS"},
                  "baseline_critique": {"overall_0_5": 3.5, "verdict": "REWORK"}},
            "B": {"image": None},
            "C": {"image": "c.png", "sanity": {"verdict": "PASS"},
                  "critique_summary": {"n_rolls": 3, "n_scored": 3, "mean_overall": 3.8,
                                       "verdicts": {"REWORK": 3},
                                       "mean_scores": {"lighting_quality": 4.3}}},
        },
        "overlay_b_vs_c": None, "de_b_vs_c": None,
        "de_c_vs_a": {"worst_both": 3.1, "note": ex.de_verdict_note(3.1)},
    }
    md = ex.to_markdown(res)
    assert "MISSING" in md
    assert "3.5" in md and "3.8" in md
    assert "UNCALIBRATED" in md          # the judge-advisory caveat is part of the report
    assert "lighting_quality 4.3" in md


def test_main_free_path_writes_reports_without_paid_deps(tmp_path):
    """End-to-end on the FREE path: no rolls, no leg B, fake tiny images — main() must
    write both report files and never import critique (which sys.exits without a key)."""
    spec = {"schema": "interior-ai/room-spec@0.2", "room": {"type": "sitting_room"},
            "materials": {"surfaces": {"floor": "birch_veneer"}}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec), encoding="utf-8")
    a = tmp_path / "a.png"
    c = tmp_path / "c.png"
    a.write_bytes(b"not-a-real-png")     # sanity/ΔE00 must degrade to UNWIRED, not crash
    c.write_bytes(b"not-a-real-png")
    out = tmp_path / "out"
    rc = ex.main(["--spec", str(sp), "--leg-a", str(a), "--leg-c", str(c),
                  "--out", str(out)])
    assert rc == 0
    data = json.loads((out / "experiment_3leg.json").read_text(encoding="utf-8"))
    assert data["room_type"] == "sitting_room"
    assert "birch" in data["material_story"]
    assert data["legs"]["B"]["image"] is None
    assert (out / "experiment_3leg.md").exists()


def test_baseline_critique_bad_path_fails_loud(tmp_path):
    """--baseline-critique pointing at a missing file must raise, not silently report
    'no baseline' (review finding 2026-07-14)."""
    spec = {"room": {"type": "x"}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec), encoding="utf-8")
    a = tmp_path / "a.png"
    c = tmp_path / "c.png"
    a.write_bytes(b"x")
    c.write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        ex.main(["--spec", str(sp), "--leg-a", str(a), "--leg-c", str(c),
                 "--baseline-critique", str(tmp_path / "missing.json"),
                 "--out", str(tmp_path / "o")])


def test_baseline_critique_identity_mismatch_flagged(tmp_path):
    """A baseline scorecard whose _artifact is a DIFFERENT render must be flagged —
    reusing another render's score as the baseline is the flattering-scorer shape."""
    spec = {"room": {"type": "x"}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec), encoding="utf-8")
    a = tmp_path / "a.png"
    c = tmp_path / "c.png"
    a.write_bytes(b"x")
    c.write_bytes(b"x")
    bc = tmp_path / "crit.json"
    bc.write_text(json.dumps({"_artifact": "some_other_render.png",
                              "overall_0_5": 4.75, "verdict": "SHIP"}), encoding="utf-8")
    out = tmp_path / "o"
    assert ex.main(["--spec", str(sp), "--leg-a", str(a), "--leg-c", str(c),
                    "--baseline-critique", str(bc), "--out", str(out)]) == 0
    data = json.loads((out / "experiment_3leg.json").read_text(encoding="utf-8"))
    assert data["legs"]["A"]["baseline_critique"]["_identity_mismatch"] is True


def test_bad_materials_block_fails_loud(tmp_path):
    """A typo'd preset in the spec must abort the EXPERIMENT too (ValueError), not score
    legs against a story describing materials that never rendered."""
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps({"room": {"type": "x"},
                              "materials": {"surfaces": {"floor": "oak_wood_flor"}}}),
                  encoding="utf-8")
    with pytest.raises(ValueError):
        ex.main(["--spec", str(sp), "--leg-a", "a.png", "--leg-c", "c.png",
                 "--out", str(tmp_path / "o")])


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
