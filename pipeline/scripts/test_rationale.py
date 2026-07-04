#!/usr/bin/env python3
"""test_rationale.py — pin the per-element rationale (explainability) layer.

The layer's whole value is HONESTY, so the tests assert the honest properties, not
pretty output: (a) every material is labelled a hardcoded default (never a design
reason) and that caps every element below 'true'; (b) the material description does not
DRIFT from what build_room actually renders (shared material_defaults + a slug-presence
guard against build_room's source); (c) cite-or-drop — an uncited spec material stays
'default', a cite-resolving one grounds to 'concept'; (d) real placement/dimension
sources ground the axes they should; (e) it degrades, never throws.

Run: python pipeline/scripts/test_rationale.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rationale as R          # noqa: E402
import material_defaults as M  # noqa: E402


def _spec(fn):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", fn)
    assert os.path.exists(p), f"fixture spec missing: {p}"
    return json.load(open(p, encoding="utf-8"))


# ---- shape + the honest headline ----
def test_report_shape_and_summary_counts():
    rep = R.report(_spec("bedroom_suite.json"))
    assert set(rep) == {"elements", "room", "summary"}
    assert len(rep["elements"]) == 12                       # 5 builtins + 2 items + 5 fixtures
    s = rep["summary"]
    assert s["true"] + s["partial"] + s["default"] == 12
    for rec in rep["elements"]:
        assert set(rec["presence_why"]) == {"text", "cite", "grounded"}


def test_every_material_is_an_honest_default():
    # the honesty keystone: NO material is dressed as a design reason today
    for fn in ("bedroom_suite.json", "living_condo.json"):
        for rec in R.report(_spec(fn))["elements"]:
            m = rec["material_why"]
            assert m["grounded"] == "default", (fn, rec["tag"], m)
            assert "STUDIO RENDER DEFAULT" in m["text"] and "material_defaults" in m["cite"]


def test_material_caps_every_element_below_true():
    # while materials are all default, no element can roll up to 'true'
    for fn in ("bedroom_suite.json", "living_condo.json"):
        rep = R.report(_spec(fn))
        assert rep["summary"]["true"] == 0, fn


def test_bedroom_grounding_is_zero_nine_three():
    s = R.report(_spec("bedroom_suite.json"))["summary"]
    assert (s["true"], s["partial"], s["default"]) == (0, 9, 3), s


# ---- drift guard: rationale must describe what build_room actually renders ----
def test_material_slugs_still_exist_in_build_room_source():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_room.py"),
               encoding="utf-8").read()
    missing = [slug for slug in M.ALL_SLUGS if slug not in src]
    assert not missing, f"material_defaults slugs no longer in build_room.py (drift!): {missing}"


def test_build_room_shares_the_kind_sets():
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_room.py"),
               encoding="utf-8").read()
    assert "import material_defaults" in src
    assert "FABRIC_KINDS" in src and "WOODEN_KINDS" in src   # sourced from the shared module


# ---- real sources ground the axes they should ----
def _rec(rep, kind):
    return next(r for r in rep["elements"] if r["kind"] == kind)


def test_tv_placement_is_function_grounded():
    rep = R.report(_spec("bedroom_suite.json"))
    tv = _rec(rep, "tv_panel")
    assert tv["placement_why"]["grounded"] == "function"
    assert "GS-xx" in tv["placement_why"]["cite"]


def test_bed_dimension_is_ergonomic_grounded():
    bed = _rec(R.report(_spec("bedroom_suite.json")), "bed")
    assert bed["dimension_why"]["grounded"] == "ergonomic"
    assert "mattress" in bed["dimension_why"]["text"]


def test_wc_presence_is_code_grounded():
    wc = _rec(R.report(_spec("bedroom_suite.json")), "wc")
    assert wc["presence_why"]["grounded"] == "code"
    assert "mr39" in wc["presence_why"]["cite"]


# ---- cite-or-drop on a future spec material field ----
def _one(kind="cabinet", rationale=None):
    el = {"name": "x", "kind": kind, "x": 0, "y": 0, "w": 600, "d": 400, "h": 800}
    if rationale is not None:
        el["rationale"] = rationale
    return {"room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]], "type": "study"},
            "builtins": [el], "items": [], "subrooms": []}


def test_uncited_spec_material_stays_default():
    spec = _one(rationale={"material": "engineered rift-oak"})   # no cite
    m = _rec(R.report(spec), "cabinet")["material_why"]
    assert m["grounded"] == "default" and "cite-or-drop" in m["text"]


def test_unresolved_cite_stays_default():
    spec = _one(rationale={"material": "oak", "cite": {"material": "knowledge/nope/missing.md"}})
    assert _rec(R.report(spec), "cabinet")["material_why"]["grounded"] == "default"


def test_resolving_cite_grounds_to_concept():
    # a cite that points at a REAL repo file grounds the material to 'concept'
    spec = _one(rationale={"material": "engineered rift-oak veneer",
                           "why": {"material": "humidity-stable core for a Thai condo"},
                           "cite": {"material": "docs/functional-correctness-layer.md"}})
    m = _rec(R.report(spec), "cabinet")["material_why"]
    assert m["grounded"] == "concept", m
    assert "humidity-stable" in m["text"]


# ---- robustness ----
def test_degrades_never_throws_on_malformed():
    spec = {"room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "builtins": [{"kind": "bed", "x": 0, "y": 0, "d": 2000}],   # missing w/name
            "items": [], "subrooms": []}
    rep = R.report(spec)                    # must not raise
    assert len(rep["elements"]) == 1


def test_markdown_carries_the_honest_headline():
    md = R.to_markdown(_spec("bedroom_suite.json"), "bedroom_suite.json")
    assert "DESIGN RATIONALE" in md
    assert "0 fully-grounded" in md and "chromatically a placeholder" in md


TESTS = [test_report_shape_and_summary_counts, test_every_material_is_an_honest_default,
         test_material_caps_every_element_below_true, test_bedroom_grounding_is_zero_nine_three,
         test_material_slugs_still_exist_in_build_room_source, test_build_room_shares_the_kind_sets,
         test_tv_placement_is_function_grounded, test_bed_dimension_is_ergonomic_grounded,
         test_wc_presence_is_code_grounded, test_uncited_spec_material_stays_default,
         test_unresolved_cite_stays_default, test_resolving_cite_grounds_to_concept,
         test_degrades_never_throws_on_malformed, test_markdown_carries_the_honest_headline]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
