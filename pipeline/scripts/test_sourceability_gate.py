"""
test_sourceability_gate.py — the moat gate: a render must visualize a SOURCEABLE spec.

Pure-logic tests (no files) for classify / resolve / the four machine checks / aggregate,
plus a couple of end-to-end check() tests over temp spec + ffe-candidates files. Mirrors
the strategy.md SOURCEABILITY GATE spec (2026-07-06): SOURCED vs FABRICATED split, five
checks, UNWIRED-honest when a project has no FF&E file (never silent-pass).
"""
import json
import os
import tempfile
import unittest

import sourceability_gate as SG


def _sofa(ffe_tag="FFE-101", w=2100, d=950, **kw):
    it = {"name": "sofa_01", "kind": "sofa", "x": 0, "y": 0, "w": w, "d": d, "rot": 0}
    if ffe_tag is not None:
        it["ffe_tag"] = ffe_tag
    it.update(kw)
    return it


def _ffe(tag="FFE-101", selected=True, verified=True, w=2100, d=950, h=850,
         source_th="Index Living Mall", link="https://www.indexlivingmall.com/",
         extra_candidates=None):
    cand = {"manufacturer": "Index", "model": "VERONA", "qty": 1,
            "dimensions_mm": {"w": w, "d": d, "h": h}, "unit_price_thb": 24900,
            "source_th": source_th, "link": link, "verified": verified, "selected": selected}
    cands = [cand] + (extra_candidates or [])
    return {"project_id": "PRJ-TEST", "currency": "THB", "unit_system": "mm",
            "items": [{"tag": tag, "room": "Living", "role": "Sofa", "candidates": cands}]}


class TestClassify(unittest.TestCase):
    def test_items_are_sourced(self):
        self.assertEqual(SG.classify_element({"kind": "sofa"}, "items"), "sourced")
        self.assertEqual(SG.classify_element({"kind": "bed"}, "items"), "sourced")

    def test_builtins_are_fabricated(self):
        self.assertEqual(SG.classify_element({"kind": "wardrobe"}, "builtins"), "fabricated")
        self.assertEqual(SG.classify_element({"kind": "headboard"}, "builtins"), "fabricated")

    def test_sanitary_appliance_fixtures_are_sourced(self):
        for k in ("toilet", "wc", "basin", "tub", "bathtub", "shower", "fridge"):
            self.assertEqual(SG.classify_element({"kind": k}, "fixtures"), "sourced", k)

    def test_millwork_fixtures_are_fabricated(self):
        for k in ("vanity", "cabinet", "wardrobe", "counter"):
            self.assertEqual(SG.classify_element({"kind": k}, "fixtures"), "fabricated", k)


class TestResolve(unittest.TestCase):
    def test_resolves_selected_candidate(self):
        doc = _ffe(tag="FFE-101")
        cand = SG.resolve_candidate("FFE-101", doc)
        self.assertIsNotNone(cand)
        self.assertTrue(cand["selected"])

    def test_missing_tag_returns_none(self):
        self.assertIsNone(SG.resolve_candidate("FFE-999", _ffe(tag="FFE-101")))

    def test_no_selected_candidate_returns_none(self):
        self.assertIsNone(SG.resolve_candidate("FFE-101", _ffe(selected=False)))

    def test_empty_candidates_returns_none(self):
        doc = {"items": [{"tag": "FFE-202", "role": "Wardrobe", "candidates": []}]}
        self.assertIsNone(SG.resolve_candidate("FFE-202", doc))


class TestDimensionParity(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(SG.dims_ok({"w": 2100, "d": 950}, {"w": 2100, "d": 950}))

    def test_within_tolerance(self):
        # +14% still ok (tol 15%)
        self.assertTrue(SG.dims_ok({"w": 2100, "d": 950}, {"w": 2100 * 1.14, "d": 950}))

    def test_orientation_agnostic(self):
        # candidate recorded w/d swapped from the scene-graph piece = same footprint
        self.assertTrue(SG.dims_ok({"w": 2100, "d": 950}, {"w": 950, "d": 2100}))

    def test_ffe_s01_depth_mismatch_fails(self):
        # the 2026-07-04 real lesson: a 600mm-deep spec sofa vs the buyable 860mm product
        self.assertFalse(SG.dims_ok({"w": 2100, "d": 600}, {"w": 2100, "d": 860}))

    def test_missing_dims_fails(self):
        self.assertFalse(SG.dims_ok({"w": 2100, "d": 950}, {"w": 2100}))
        self.assertFalse(SG.dims_ok({"w": 2100, "d": 950}, None))


class TestCheckSourced(unittest.TestCase):
    def test_bound_verified_supplier_dims_is_pass(self):
        r = SG.check_sourced(_sofa(), _ffe())
        self.assertEqual(r["status"], "PASS")

    def test_unverified_is_review(self):
        r = SG.check_sourced(_sofa(), _ffe(verified=False))
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("verified", r["failed"])

    def test_no_ffe_tag_is_fail(self):
        r = SG.check_sourced(_sofa(ffe_tag=None), _ffe())
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("binding", r["failed"])

    def test_unresolved_tag_is_fail(self):
        r = SG.check_sourced(_sofa(ffe_tag="FFE-999"), _ffe(tag="FFE-101"))
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("binding", r["failed"])

    def test_dimension_mismatch_is_fail(self):
        r = SG.check_sourced(_sofa(d=600), _ffe(d=860))
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("dimension", r["failed"])

    def test_missing_link_is_fail(self):
        r = SG.check_sourced(_sofa(), _ffe(link=""))
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("supplier", r["failed"])

    def test_missing_source_th_is_fail(self):
        r = SG.check_sourced(_sofa(), _ffe(source_th=""))
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("supplier", r["failed"])


class TestReport(unittest.TestCase):
    def _spec(self, items=None, builtins=None, subrooms=None):
        return {"room": {"type": "living", "outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
                "items": items or [], "builtins": builtins or [], "subrooms": subrooms or []}

    def test_no_ffe_doc_is_unwired(self):
        res, verdict = SG.report(self._spec(items=[_sofa()]), None)
        self.assertEqual(verdict, "UNWIRED")

    def test_all_verified_is_pass(self):
        res, verdict = SG.report(self._spec(items=[_sofa()]), _ffe())
        self.assertEqual(verdict, "PASS")

    def test_one_unverified_is_review(self):
        res, verdict = SG.report(self._spec(items=[_sofa()]), _ffe(verified=False))
        self.assertEqual(verdict, "REVIEW")

    def test_unbound_item_is_fail(self):
        res, verdict = SG.report(self._spec(items=[_sofa(ffe_tag=None)]), _ffe())
        self.assertEqual(verdict, "FAIL")

    def test_fabricated_builtin_does_not_drive_verdict(self):
        # a built-in with no ffe_tag must NOT FAIL the gate (it is joiner-made, not sourced)
        spec = self._spec(items=[_sofa()],
                          builtins=[{"name": "wardrobe_01", "kind": "wardrobe", "x": 0, "y": 0, "w": 2400, "d": 600}])
        res, verdict = SG.report(spec, _ffe())
        self.assertEqual(verdict, "PASS")
        fab = [r for r in res if r.get("cls") == "fabricated"]
        self.assertEqual(len(fab), 1)
        self.assertEqual(fab[0]["status"], "FABRICATED")

    def test_sanitary_fixture_is_sourced_and_gated(self):
        spec = self._spec(subrooms=[{"outline_mm": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
                                     "fixtures": [{"name": "wc_01", "kind": "toilet", "x": 0, "y": 0,
                                                   "w": 380, "d": 680, "ffe_tag": "FFE-999"}]}])
        res, verdict = SG.report(spec, _ffe(tag="FFE-101"))
        self.assertEqual(verdict, "FAIL")   # toilet is sourced, unbound -> FAIL


class TestBundleRows(unittest.TestCase):
    def test_render_without_ffe_is_concept_only_warn(self):
        rows = SG.bundle_rows("UNWIRED", ffe_present=False, has_render=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "WARN")
        self.assertIn("CONCEPT ONLY", rows[0]["detail"])

    def test_no_render_no_ffe_emits_nothing(self):
        self.assertEqual(SG.bundle_rows("UNWIRED", ffe_present=False, has_render=False), [])

    def test_ffe_present_emits_no_exception_row(self):
        # with an FF&E file the standing reminder lives in the always-visible QA section,
        # so bundle_rows stays quiet (no false WARN)
        self.assertEqual(SG.bundle_rows("PASS", ffe_present=True, has_render=True), [])
        self.assertEqual(SG.bundle_rows("REVIEW", ffe_present=True, has_render=True), [])


class TestCheckIntegration(unittest.TestCase):
    def _write(self, d, name, obj):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f)
        return p

    def test_check_locates_adjacent_ffe(self):
        with tempfile.TemporaryDirectory() as d:
            spec = {"room": {"type": "living", "outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
                    "items": [_sofa()], "builtins": [], "subrooms": []}
            sp = self._write(d, "scene-graph.living.json", spec)
            self._write(d, "ffe-candidates.json", _ffe())
            verdict, res = SG.check(sp)
            self.assertEqual(verdict, "PASS")

    def test_check_no_ffe_is_unwired(self):
        with tempfile.TemporaryDirectory() as d:
            spec = {"room": {"type": "living", "outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
                    "items": [_sofa()], "builtins": [], "subrooms": []}
            sp = self._write(d, "spec_living.json", spec)
            verdict, res = SG.check(sp)
            self.assertEqual(verdict, "UNWIRED")

    def test_committed_gold_example_reviews(self):
        """The committed worked example (examples/scene-graph.example.json bound to
        ffe-candidates.example.json via spec['ffe_candidates']) must gate to REVIEW — every
        sourced item is bound + right-sized + supplied, but the example picks are DRAFT
        (verified:false). A regression anchor so the ffe_tag join can't silently rot."""
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        sp = os.path.join(root, "examples", "scene-graph.example.json")
        self.assertTrue(os.path.exists(sp), "gold-standard example scene-graph is missing")
        verdict, res = SG.check(sp)
        self.assertEqual(verdict, "REVIEW")
        # the media wall built-in is FABRICATED and must NOT be sourcing-gated
        fab = [r for r in res if r.get("cls") == "fabricated"]
        self.assertEqual(len(fab), 1)


if __name__ == "__main__":
    unittest.main()
