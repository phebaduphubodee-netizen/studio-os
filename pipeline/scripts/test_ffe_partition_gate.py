"""
test_ffe_partition_gate.py — the scoping gate: split FF&E into MADE (workshop) vs BOUGHT (sourcing).

Pure-logic tests (no files) for division / classify_role / partition, plus one end-to-end check()
over the committed PRJ-2026-002 ffe-candidates.json (a regression anchor so the csi partition can't
silently rot). Mirrors the 2026-07-11 furniture-sourcing DR finding (d): built-ins (csi 06/09) are
fabricated, loose + fixtures (csi 12/22/26) are sourceable, and a csi that DIVERGES from the
built-in/retailer signals must surface as REVIEW, never be silently trusted.
"""
import json
import os
import unittest

import ffe_partition_gate as PG


def _role(tag="FFE-M01", role="Bed frame", csi="12 58 00", selected=True,
          source_th="Index Living Mall", link="https://www.indexlivingmall.com/110047607",
          price=8990, extra=None, n=1):
    cand = {"manufacturer": "Index", "model": "Serine", "csi": csi, "unit_price_thb": price,
            "source_th": source_th, "link": link, "dimensions_mm": {"w": 2000, "d": 2088, "h": 1100},
            "selected": selected}
    cands = [cand] + (extra or [])
    if n == 0:
        cands = []
    return {"tag": tag, "room": "Master Bedroom", "role": role, "candidates": cands}


def _builtin(tag="FFE-BM01", role="Built-in wardrobe — west wall (BF11)", csi="06 41 00"):
    cand = {"manufacturer": "Formica (via TH supplier)", "model": "laminate on carcass", "csi": csi,
            "unit_price_thb": None, "source_th": "studio vault (finish/hardware draft)",
            "link": "projects/PRJ-2026-002_c001-house/03_layout/ffe-finish-hardware-draft.md",
            "dimensions_mm": {"w": 2300, "d": 600, "h": 2800}, "selected": True}
    return {"tag": tag, "room": "Master Bedroom", "role": role, "candidates": [cand]}


class TestDivision(unittest.TestCase):
    def test_space_separated(self):
        self.assertEqual(PG._division("06 41 00"), "06")
        self.assertEqual(PG._division("12 58 00"), "12")

    def test_dash_and_concatenated(self):
        self.assertEqual(PG._division("22-41-13"), "22")
        self.assertEqual(PG._division("064100"), "06")

    def test_garbage_is_none(self):
        for v in (None, "", "  ", "abc", 12):
            self.assertIsNone(PG._division(v), v)


class TestClassifyRoute(unittest.TestCase):
    def test_casework_06_is_fabricated(self):
        self.assertEqual(PG.classify_role(_builtin(csi="06 41 00"))["route"], "fabricated")

    def test_finish_09_is_fabricated(self):
        r = _builtin(tag="FFE-BM03", role="Headboard feature wall (built-in)", csi="09 77 00")
        self.assertEqual(PG.classify_role(r)["route"], "fabricated")

    def test_furnishings_12_is_sourceable(self):
        self.assertEqual(PG.classify_role(_role(csi="12 52 00"))["route"], "sourceable")
        self.assertEqual(PG.classify_role(_role(csi="12 58 00"))["route"], "sourceable")

    def test_plumbing_22_and_lighting_26_and_av_11_are_sourceable(self):
        for csi in ("22 41 00", "22 41 13", "22 41 39", "26 51 00", "11 52 13"):
            self.assertEqual(PG.classify_role(_role(csi=csi))["route"], "sourceable", csi)

    def test_selected_pick_drives_csi(self):
        # first candidate is a fabricated one, but the SELECTED pick is sourceable
        fab = {"csi": "06 41 00", "selected": False, "link": "projects/x.md", "source_th": "vault"}
        r = _role(csi="12 58 00", selected=True, extra=None)
        r["candidates"] = [fab, r["candidates"][0]]
        self.assertEqual(PG.classify_role(r)["route"], "sourceable")


class TestDivergence(unittest.TestCase):
    def test_fabricated_csi_but_retailer_link_is_review(self):
        # csi says 06 (made) yet it is a real retailer product with no built-in signal -> REVIEW
        r = _role(tag="FFE-X", role="Cabinet", csi="06 41 00",
                  source_th="HomePro", link="https://www.homepro.co.th/p/123")
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "review")
        self.assertTrue(out["divergent"])

    def test_sourceable_csi_but_builtin_tag_is_review(self):
        # csi says 12 (bought) yet the tag/role/source read built-in -> REVIEW
        r = _builtin(tag="FFE-BM09", role="Built-in wardrobe", csi="12 58 00")
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "review")
        self.assertTrue(out["divergent"])

    def test_custom_fabrication_on_plumbing_csi_is_review(self):
        # the real FFE-M05 shape: csi 22 (plumbing/bought) but the SELECTED pick is a custom-
        # fabricated built-in vanity (mfr 'Custom fabrication', 'carcass', null price at quote,
        # a BF10.250 code). It has no live SKU to sign -> must surface as REVIEW, not sourceable.
        r = {"tag": "FFE-M05", "room": "Ensuite", "role": "Double-basin vanity (twin washbasin + cabinet)",
             "candidates": [{"manufacturer": "Custom fabrication (COTTO countertop basins)",
                             "model": "Built-in 2400 stone-top double vanity + 2x basin (BF10.250)",
                             "material_finish": "quartz top on moisture-resistant carcass",
                             "csi": "22 41 00", "unit_price_thb": None,
                             "lead_time": "3-5 weeks (fabricated to order)",
                             "source_th": "Boonthavorn / local stone fabricator",
                             "link": "https://www.cotto.com/th/product/basins", "selected": True}]}
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "review")
        self.assertTrue(out["divergent"])
        self.assertTrue(out["fabrication_signal"])

    def test_bf_code_in_best_pick_prose_does_not_false_flag(self):
        # a genuinely-bought sofa (csi 12, retailer link, priced, in stock) whose best_pick_reason
        # merely REFERENCES another role's built-in code must NOT be pulled out of the sourcing queue.
        r = {"tag": "FFE-S05", "room": "Sitting", "role": "3-seat sofa",
             "best_pick_reason": "Chosen over the built-in BF12 bench option for flexibility",
             "candidates": [{"manufacturer": "Index", "model": "VERONA 3-seat", "csi": "12 52 00",
                             "unit_price_thb": 18900, "lead_time": "in stock", "source_th": "Index Living Mall",
                             "link": "https://www.indexlivingmall.com/verona-123456", "selected": True}]}
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "sourceable")
        self.assertFalse(out["fabrication_signal"])

    def test_bought_product_model_without_bf_code_stays_sourceable(self):
        # a bought lamp whose model is a bare token 'F60' must not trip the BF-code regex on prose;
        # only a real BF##/F## in the STRUCTURED id (tag/model) counts, and 'F60' is a 2-digit model
        # id -> it DOES match by design, so use a non-matching model to prove the prose exclusion.
        r = {"tag": "FFE-L07", "room": "Living", "role": "Floor lamp",
             "best_pick_reason": "compared against BF20 sconce", "candidates": [
                 {"manufacturer": "IKEA", "model": "NYMANE arc lamp", "csi": "26 51 00",
                  "unit_price_thb": 2990, "source_th": "IKEA Thailand",
                  "link": "https://www.ikea.com/th/en/p/nymane-123456/", "selected": True}]}
        self.assertEqual(PG.classify_role(r)["route"], "sourceable")

    def test_drop_in_bathtub_is_not_false_flagged(self):
        # regression: the bathtub role literally says 'built-in/drop-in' (an INSTALL type) but the
        # pick is a real SKU (COTTO BT216D) with a price -> the weak word must NOT flip it to review.
        r = {"tag": "FFE-M08", "room": "Ensuite",
             "role": "Bathtub ~1.6m (freestanding or built-in/drop-in)",
             "candidates": [{"manufacturer": "COTTO", "model": "BT216D(H) Santa 1.6m drop-in, chain waste",
                             "material_finish": "acrylic", "csi": "22 41 00", "unit_price_thb": 8000,
                             "lead_time": "in stock", "source_th": "Boonthavorn / COTTO",
                             "link": "https://www.cotto.com/th/product/bathtubs", "selected": True}]}
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "sourceable")
        self.assertFalse(out["fabrication_signal"])

    def test_builtin_tag_with_fabricated_csi_is_not_divergent(self):
        # the normal built-in: FFE-B* tag AND csi 06 agree -> fabricated, no divergence
        out = PG.classify_role(_builtin())
        self.assertEqual(out["route"], "fabricated")
        self.assertFalse(out["divergent"])

    def test_retailer_sourceable_is_not_divergent(self):
        out = PG.classify_role(_role())  # FFE-M tag, retailer link, csi 12
        self.assertEqual(out["route"], "sourceable")
        self.assertFalse(out["divergent"])


class TestUnknownAndEmpty(unittest.TestCase):
    def test_missing_csi_is_review(self):
        r = _role(csi=None)
        self.assertEqual(PG.classify_role(r)["route"], "review")

    def test_unknown_division_is_review(self):
        r = _role(csi="99 99 00")
        self.assertEqual(PG.classify_role(r)["route"], "review")

    def test_zero_candidates_is_review(self):
        r = _role(n=0)
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "review")
        self.assertIn("no candidates", out["reason"])


class TestClientSupplied(unittest.TestCase):
    def test_tv_flagged_client_supplied_advisory(self):
        r = _role(tag="FFE-L06", role="Wall-mounted TV — electronics, normally CLIENT-SUPPLIED",
                  csi="11 52 13", source_th="Power Buy", link="https://www.samsung.com/th/...")
        out = PG.classify_role(r)
        self.assertEqual(out["route"], "sourceable")   # still bought, just advised client-supplied
        self.assertTrue(out["client_supplied"])


class TestPartition(unittest.TestCase):
    def test_buckets_and_verdict(self):
        doc = {"items": [_builtin(), _role(tag="FFE-M01", csi="12 58 00"),
                         _role(tag="FFE-M09", csi="26 51 00"), _role(tag="FFE-Z", csi=None)]}
        rows, summary, verdict = PG.partition(doc)
        self.assertIn("FFE-BM01", summary["fabricated"])
        self.assertEqual(set(summary["sourceable"]), {"FFE-M01", "FFE-M09"})
        self.assertIn("FFE-Z", summary["review"])
        self.assertEqual(verdict, "REVIEW")

    def test_all_clean_is_pass(self):
        doc = {"items": [_builtin(), _role(tag="FFE-M01", csi="12 58 00")]}
        _rows, _summary, verdict = PG.partition(doc)
        self.assertEqual(verdict, "PASS")

    def test_empty_doc_is_not_vacuous_pass(self):
        # a stub / wrong file with no roles must NOT read a reassuring green PASS (flattering-scorer
        # guard, mirrors sourceability_gate's zero-input discipline)
        for doc in ({"items": []}, {}, None):
            _rows, _summary, verdict = PG.partition(doc)
            self.assertEqual(verdict, "EMPTY", repr(doc))

    def test_sourceable_tags_helper(self):
        doc = {"items": [_builtin(), _role(tag="FFE-M01", csi="12 58 00")]}
        self.assertEqual(PG.sourceable_tags(doc), ["FFE-M01"])


class TestRealProjectFile(unittest.TestCase):
    """Regression anchor over the committed PRJ-2026-002 ffe-candidates.json: the built-ins
    (FFE-BM/BS, csi 06/09) must route fabricated and the loose/fixtures (csi 12/22/26/11) sourceable.
    A silent csi retag or a routing-logic mutation trips this."""
    def _doc(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        p = os.path.join(root, "projects", "PRJ-2026-002_c001-house", "03_layout", "ffe-candidates.json")
        if not os.path.exists(p):
            self.skipTest("PRJ-2026-002 ffe-candidates.json not present")
        return json.load(open(p, encoding="utf-8"))

    def test_builtins_route_fabricated(self):
        rows, summary, _v = PG.partition(self._doc())
        by_tag = {r["tag"]: r for r in rows}
        for tag in ("FFE-BM01", "FFE-BM02", "FFE-BM03", "FFE-BS01"):
            if tag in by_tag:
                self.assertEqual(by_tag[tag]["route"], "fabricated", tag)

    def test_loose_and_fixtures_route_sourceable(self):
        rows, _s, _v = PG.partition(self._doc())
        by_tag = {r["tag"]: r for r in rows}
        for tag in ("FFE-M01", "FFE-M03", "FFE-S01", "FFE-M08"):
            if tag in by_tag:
                self.assertEqual(by_tag[tag]["route"], "sourceable", tag)

    def test_custom_fabricated_vanity_surfaces_as_review(self):
        # FFE-M05's selected pick is a custom-fabricated built-in vanity on a plumbing csi -> the
        # gate must NOT silently route it sourceable (asking for a SKU that doesn't exist).
        rows, _s, verdict = PG.partition(self._doc())
        by_tag = {r["tag"]: r for r in rows}
        if "FFE-M05" in by_tag:
            self.assertEqual(by_tag["FFE-M05"]["route"], "review")
            self.assertEqual(verdict, "REVIEW")   # so the whole file honestly reads REVIEW

    def test_every_role_routes_without_crash(self):
        rows, summary, verdict = PG.partition(self._doc())
        self.assertGreater(len(rows), 0)
        total = len(summary["fabricated"]) + len(summary["sourceable"]) + len(summary["review"])
        self.assertEqual(total, len(rows))


if __name__ == "__main__":
    unittest.main()
