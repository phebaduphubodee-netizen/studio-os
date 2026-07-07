"""test_kind_priors.py -- unit + mutation-pin tests for the deterministic size/aspect
priors lane. ALL fixtures are self-authored synthetic gt.json dicts written into tmp_path
-- never corpus files (CC BY-NC, never redistributed; same rule as the adapter tests).

    python -m pytest test_kind_priors.py -q
"""
import json
import os

import kind_priors


def _gt(tmp_path, name, units, elements, openings=None):
    """Write a minimal gt.json and return its directory."""
    doc = {"meta": {"units": units,
                    "scale_mm_per_unit": 100.0 if units == "mm" else None},
           "elements": elements, "openings": openings or []}
    fp = os.path.join(str(tmp_path), name + ".gt.json")
    with open(fp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return os.path.dirname(fp)


def _tables(n=60, w0=1600, d0=800, spread=100.0, kind="table"):
    """n elements whose larger side ~w0, smaller side ~d0, spread evenly +-spread."""
    els = []
    for i in range(n):
        off = (i / (n - 1) * 2 - 1) * spread          # -spread .. +spread
        els.append({"id": f"{kind}{i}", "kind": kind,
                    "x": 0, "y": 0, "w": w0 + off, "d": d0 + off})
    return els


def _p(kinds):
    return {"schema": kind_priors.SCHEMA, "meta": {"params": {}}, "kinds": kinds}


# ---- derive ------------------------------------------------------------------------------
def test_derive_bands_from_synthetic_gt(tmp_path):
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50)
    assert "table" in pr["kinds"]
    b = pr["kinds"]["table"]
    assert b["n"] == 60
    assert b["lo_mm"][0] <= 800 <= b["lo_mm"][1]
    assert b["hi_mm"][0] <= 1600 <= b["hi_mm"][1]
    assert pr["meta"]["params"] == {"q_lo": 0.10, "q_hi": 0.90, "pad_mm": 50.0,
                                    "aspect_pad": 1.15, "min_support": 50}


def test_svg_unit_files_are_excluded(tmp_path):
    """Mutation pin: a mutant that drops the units filter would fold the 16x8 raw-unit
    rows into the band and shift lo_mm[0] below 0 -- deriving twice from the SAME dir
    (so provenance basenames match) before and after the svg-unit file lands must yield
    byte-identical kinds dicts, and the units skip must be counted."""
    d = _gt(tmp_path, "mm_sheet", "mm", _tables())
    before = kind_priors.derive([d], min_support=50)
    _gt(tmp_path, "raw_sheet", "svg-unit", _tables(w0=16, d0=8, spread=1.0))
    after = kind_priors.derive([d], min_support=50)
    assert before["kinds"] == after["kinds"]
    assert after["meta"]["n_files_skipped_units"] == 1
    assert after["kinds"]["table"]["lo_mm"][0] > 0


def test_openings_never_enter_element_bands(tmp_path):
    """Door-sized rows (~999 mm) live in openings; if derive() ever sampled openings a
    phantom ~1 m band would land in furniture territory. Only elements are sampled."""
    doors = [{"type": "sliding", "x": 0, "y": 0, "w": 999, "d": 100} for _ in range(60)]
    d = _gt(tmp_path, "mixed", "mm", _tables(), openings=doors)
    pr = kind_priors.derive([d], min_support=50)
    assert pr["meta"]["n_elements_sampled"] == 60
    assert list(pr["kinds"].keys()) == ["table"]


def test_min_support_excludes_thin_kinds(tmp_path):
    d = _gt(tmp_path, "thin", "mm", _tables(n=3, kind="wardrobe"))
    pr = kind_priors.derive([d], min_support=5)
    assert "wardrobe" not in pr["kinds"]
    assert pr["excluded_low_support"]["wardrobe"] == 3


# ---- suggest -----------------------------------------------------------------------------
def test_suggest_unique_band_emits():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(1600, 800, p) == "table"


def test_suggest_ambiguity_stays_unreported():
    """THE mutation pin: the mutant `return cands[0] if cands else None` (dropping the
    len == 1 check) would guess on ambiguity -- a false-accept, the exact flattering
    failure the scorer-honesty doctrine bans. Two identical bands -> None."""
    band = {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0], "aspect": [1.5, 2.5]}
    p = _p({"table": dict(band), "cabinet": dict(band)})
    assert kind_priors.suggest_kind(1600, 800, p) is None


def test_suggest_orientation_agnostic():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(800, 1600, p) == kind_priors.suggest_kind(1600, 800, p)


def test_suggest_outside_all_bands_is_none():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(10000, 10000, p) is None
    assert kind_priors.suggest_kind(0, 500, p) is None          # non-positive guard


def test_provenance_recorded_per_band(tmp_path):
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50)
    assert pr["schema"] == "interior-ai/kind-priors@0.1"
    for row in pr["kinds"].values():
        assert isinstance(row["provenance"], str) and row["provenance"]
        assert isinstance(row["n"], int)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
