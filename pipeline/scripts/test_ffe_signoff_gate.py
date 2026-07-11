"""
test_ffe_signoff_gate.py — the owner-sign gate: a sourced pick enters the client BOM only once a
trained human confirms its live SKU.

Pure-logic tests (no files) for canonical_key / sign_status / resolve_signoff / resolve_verified /
report, plus the sourceability_gate wiring (a ledger sign flips its verified-tier REVIEW to PASS
with no ffe edit; no ledger = inline behaviour unchanged). Mirrors placement_gate's confirmed[]
ledger discipline: canonical-key join, last-usable-wins append, OWNER-CONFIRM-PENDING inert,
orphan = detached signature surfaced.
"""
import unittest

import ffe_signoff_gate as SO


def _cand(sku_link="https://www.indexlivingmall.com/110047607", source_th="Index Living Mall",
          mfr="Index", model="Serine", verified=False, selected=True, w=2000, d=2088, h=1100,
          csi="12 58 00", **kw):
    c = {"manufacturer": mfr, "model": model, "source_th": source_th, "link": sku_link, "csi": csi,
         "dimensions_mm": {"w": w, "d": d, "h": h}, "verified": verified, "selected": selected}
    c.update(kw)
    return c


def _sign(key=None, sku="110047607", source="Index Living Mall", by="designer-a",
          date="2026-07-11", price=19850, **kw):
    e = {"by": by, "date": date}
    if key is not None:
        e["key"] = key
    if sku is not None:
        e["sku"] = sku
    if source is not None:
        e["source"] = source
    if price is not None:
        e["price_thb"] = price
    e.update(kw)
    return e


class TestCanonicalKey(unittest.TestCase):
    def test_index_sku_from_link(self):
        k = SO.canonical_key(_cand())
        self.assertEqual(k, "index-living-mall:110047607")

    def test_ikea_dotted_article(self):
        c = _cand(sku_link="https://www.ikea.com/th/en/p/brimnes-bedside-table-white-00354063/",
                  source_th="IKEA Thailand")
        # dotted article preferred; here the link carries an 8-digit run -> longest run wins
        self.assertEqual(SO.canonical_key(c), "ikea-thailand:00354063")

    def test_ikea_dotted_article_normalised(self):
        # dotted '003.540.63' collapses to the undotted URL form '00354063' — the whole point of the fix
        c = _cand(sku_link="https://www.ikea.com/th/en/p/malm-003.540.63/", source_th="IKEA")
        self.assertEqual(SO.canonical_key(c), "ikea:00354063")

    def test_explicit_sku_field_wins(self):
        c = _cand(sku="ABC-999", sku_link="https://x.com/1234567")
        self.assertEqual(SO.canonical_key(c), "index-living-mall:abc999")   # separators normalised out

    def test_query_string_stripped(self):
        c = _cand(sku_link="https://www.indexlivingmall.com/110047607?utm=track&id=999")
        self.assertEqual(SO.canonical_key(c), "index-living-mall:110047607")

    def test_composite_fallback_when_no_id(self):
        c = _cand(sku_link="projects/PRJ/03_layout/finish.md", source_th="studio vault",
                  mfr="Formica", model="laminate")
        k = SO.canonical_key(c)
        self.assertTrue(k.startswith("studio-vault|formica|laminate|"))

    def test_stable_across_reexport(self):
        self.assertEqual(SO.canonical_key(_cand()), SO.canonical_key(_cand()))


class TestMatchingRobustness(unittest.TestCase):
    """The load-bearing fixes: a valid signature must BIND despite id-format / source-spelling drift."""
    def test_dotted_signature_binds_undotted_url_article(self):
        # candidate keyed from the undotted URL run; owner signs with the dotted article -> must bind
        cand = _cand(sku_link="https://www.ikea.com/th/en/p/brimnes-00354063/", source_th="IKEA Thailand")
        sign = _sign(sku="003.540.63", source="IKEA Thailand", key=None)
        self.assertIsNotNone(SO.resolve_signoff(cand, [sign]))
        self.assertTrue(SO.resolve_verified(cand, [sign])[0])

    def test_abbreviated_source_still_binds(self):
        # candidate source_th 'IKEA Thailand'; owner writes source 'IKEA' (or omits) -> id is unique, binds
        cand = _cand(sku_link="https://www.ikea.com/th/en/p/brimnes-00354063/", source_th="IKEA Thailand")
        self.assertIsNotNone(SO.resolve_signoff(cand, [_sign(sku="00354063", source="IKEA")]))
        self.assertIsNotNone(SO.resolve_signoff(cand, [_sign(sku="00354063", source=None)]))

    def test_composite_pick_signable_via_key(self):
        # a SKU-less pick (composite key) is signed by copying its canonical key into `key`
        cand = _cand(sku_link="https://kulthong.com/product/bed-slug/", source_th="KulThong Design",
                     mfr="KulThong Design", model="NBT01 platform", w=1950, d=2080, h=300)
        key = SO.canonical_key(cand)
        self.assertIn("|", key)                                   # confirm it is a composite
        self.assertIsNotNone(SO.resolve_signoff(cand, [_sign(sku=None, key=key)]))

    def test_cross_retailer_same_id_does_not_bind(self):
        # an IKEA pick must NOT be bound by a sign that carries the same digits but a DIFFERENT
        # retailer source (the one fail-toward-PASS vector the cross-source match could open)
        cand = _cand(sku_link="https://www.ikea.com/th/en/p/x-12345/", source_th="IKEA Thailand")
        self.assertIsNone(SO.resolve_signoff(cand, [_sign(sku="12345", source="Index Living Mall")]))
        # but the same id with a compatible (abbreviated) source DOES bind
        self.assertIsNotNone(SO.resolve_signoff(cand, [_sign(sku="12345", source="IKEA")]))

    def test_degenerate_composite_binds_nothing(self):
        # no id, no model, no dims -> unbindable bucket: a stray key must NOT sign it
        cand = {"manufacturer": "", "model": "", "source_th": "Index Living Mall",
                "link": "https://www.indexlivingmall.com/category/sofas", "dimensions_mm": {},
                "verified": False, "selected": True, "csi": "12 52 00"}
        self.assertIsNone(SO.cand_composite(cand))
        self.assertIsNone(SO.resolve_signoff(cand, [_sign(key="index-living-mall|||", sku=None)]))


class TestSignStatus(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(SO.sign_status(_sign()), "valid")

    def test_pending_template_is_inert(self):
        self.assertEqual(SO.sign_status(_sign(by="OWNER-CONFIRM-PENDING")), "pending")

    def test_no_signer_is_pending(self):
        self.assertEqual(SO.sign_status(_sign(by="")), "pending")

    def test_no_sku_or_key_is_incomplete(self):
        e = _sign(sku=None, key=None)  # real signer + date + price, but no id anchor
        self.assertEqual(SO.sign_status(e), "incomplete")

    def test_no_date_is_incomplete(self):
        self.assertEqual(SO.sign_status(_sign(date="")), "incomplete")

    def test_no_id_anchor_is_incomplete(self):
        # a real signer + date but no sku/article/key: a real attempt missing the anti-rot anchor
        self.assertEqual(SO.sign_status({"by": "x", "date": "2026-07-11"}), "incomplete")

    def test_non_dict_is_inert(self):
        self.assertEqual(SO.sign_status("nope"), "inert")
        self.assertEqual(SO.sign_status(None), "inert")

    def test_price_absent_still_valid(self):
        # the SKU is the anti-rot anchor; price is the drift-prone snapshot -> absence is advisory
        self.assertEqual(SO.sign_status(_sign(price=None)), "valid")


class TestResolveSignoff(unittest.TestCase):
    def test_matches_by_key(self):
        cand = _cand()
        self.assertIsNotNone(SO.resolve_signoff(cand, [_sign()]))

    def test_no_match_returns_none(self):
        self.assertIsNone(SO.resolve_signoff(_cand(), [_sign(sku="999", source="Index Living Mall")]))

    def test_only_valid_entries_bind(self):
        self.assertIsNone(SO.resolve_signoff(_cand(), [_sign(by="OWNER-CONFIRM-PENDING")]))

    def test_last_usable_wins_append_a_correction(self):
        cand = _cand()
        good1 = _sign(by="designer-a", date="2026-07-01")
        typo = _sign(by="OWNER-CONFIRM-PENDING")            # a later inert paste
        good2 = _sign(by="designer-b", date="2026-07-11")   # the appended correction
        e = SO.resolve_signoff(cand, [good1, typo, good2])
        self.assertEqual(e["by"], "designer-b")             # last VALID wins; the typo can't erase it

    def test_trailing_typo_does_not_erase_earlier_valid(self):
        cand = _cand()
        good = _sign(by="designer-a")
        typo = _sign(by="")                                 # trailing pending -> not usable
        e = SO.resolve_signoff(cand, [good, typo])
        self.assertIsNotNone(e)
        self.assertEqual(e["by"], "designer-a")


class TestResolveVerified(unittest.TestCase):
    def test_ledger_sign_makes_verified(self):
        ok, prov = SO.resolve_verified(_cand(verified=False), [_sign()])
        self.assertTrue(ok)
        self.assertEqual(prov["source"], "ledger")

    def test_inline_verified_honoured_with_no_ledger(self):
        ok, prov = SO.resolve_verified(_cand(verified=True), None)
        self.assertTrue(ok)
        self.assertEqual(prov["source"], "inline")

    def test_unsigned_unverified_is_false(self):
        ok, prov = SO.resolve_verified(_cand(verified=False), [])
        self.assertFalse(ok)
        self.assertIsNone(prov)

    def test_backward_compatible_none_ledger_equals_inline(self):
        self.assertEqual(SO.resolve_verified(_cand(verified=True), None)[0], True)
        self.assertEqual(SO.resolve_verified(_cand(verified=False), None)[0], False)


class TestReport(unittest.TestCase):
    def _doc(self, cands):
        return {"items": [{"tag": "FFE-M01", "room": "MBR", "role": "Bed",
                           "candidates": [c]} for c in cands]}

    def test_signed_pick_passes(self):
        rows, verdict = SO.report(self._doc([_cand(verified=False)]), [_sign()])
        self.assertEqual(verdict, "PASS")
        self.assertEqual(rows[0]["status"], "signed")

    def test_pending_pick_reviews(self):
        rows, verdict = SO.report(self._doc([_cand(verified=False)]), [])
        self.assertEqual(verdict, "REVIEW")
        self.assertEqual(rows[0]["status"], "pending")

    def test_inline_verified_passes_flagged(self):
        rows, verdict = SO.report(self._doc([_cand(verified=True)]), [])
        self.assertEqual(verdict, "PASS")
        self.assertEqual(rows[0]["status"], "verified_inline")

    def test_orphan_signature_reviews(self):
        # a valid sign whose key binds no current pick -> orphan -> REVIEW
        doc = self._doc([_cand(verified=True)])          # pick passes inline...
        rows, verdict = SO.report(doc, [_sign(sku="000-gone", source="Nowhere")])
        self.assertEqual(verdict, "REVIEW")              # ...but the detached sign forces REVIEW
        self.assertTrue(any(r["status"] == "orphan" for r in rows))

    def test_fabricated_role_not_gated(self):
        # a csi 06 built-in is not sourceable -> it must not appear as a sourcing pick
        doc = {"items": [{"tag": "FFE-BM01", "room": "MBR", "role": "Built-in wardrobe (BF11)",
                          "candidates": [_cand(verified=False, source_th="studio vault",
                                               sku_link="projects/x.md", csi="06 41 00")]}]}
        # tag the candidate csi so the partition routes it fabricated
        doc["items"][0]["candidates"][0]["csi"] = "06 41 00"
        rows, verdict = SO.report(doc, [])
        self.assertEqual(rows, [])                        # nothing sourceable to sign
        self.assertEqual(verdict, "UNWIRED")              # zero sourceable -> never a vacuous green PASS

    def test_no_pick_reviews(self):
        doc = {"items": [{"tag": "FFE-M01", "room": "MBR", "role": "Bed",
                          "candidates": [_cand(verified=False, selected=False)]}]}
        # give it a sourceable csi but no selected pick
        doc["items"][0]["candidates"][0]["csi"] = "12 58 00"
        rows, verdict = SO.report(doc, [])
        self.assertEqual(verdict, "REVIEW")
        self.assertTrue(any(r["status"] == "no_pick" for r in rows))


class TestLedgerSurfaces(unittest.TestCase):
    """A signature must never silently drop: incomplete + orphan signs must SURFACE as REVIEW rows."""
    def _doc(self, cand):
        return {"items": [{"tag": "FFE-M03", "room": "MBR", "role": "Nightstand", "candidates": [cand]}]}

    def test_incomplete_signature_surfaces_as_malformed(self):
        # owner fills by+sku but forgets date -> 'incomplete' -> must appear as a malformed REVIEW row,
        # not vanish silently (the docstring promises 'surfaced, cannot bind')
        cand = _cand(verified=False)
        rows, verdict = SO.report(self._doc(cand), [{"by": "peat", "sku": "somethingelse"}])
        self.assertEqual(verdict, "REVIEW")
        self.assertTrue(any(r["status"] == "malformed" for r in rows))

    def test_zero_sourceable_with_no_ledger_is_unwired(self):
        rows, verdict = SO.report({"items": []}, [])
        self.assertEqual(verdict, "UNWIRED")

    def test_client_supplied_pick_labelled_not_bare_pending(self):
        # FFE-L06 TV shape: sourceable but client-supplied -> distinct 'client_ref' row (still REVIEW,
        # not auto-excused), labelled so no one hunts a SKU the studio isn't buying
        doc = {"items": [{"tag": "FFE-L06", "room": "Living",
                          "role": "Wall-mounted TV — electronics, normally CLIENT-SUPPLIED reference only",
                          "candidates": [_cand(verified=False, csi="11 52 13", source_th="Power Buy",
                                               sku_link="https://www.samsung.com/th/ua65du8100/")]}]}
        rows, verdict = SO.report(doc, [])
        self.assertEqual(verdict, "REVIEW")
        self.assertTrue(any(r["status"] == "client_ref" for r in rows))


class TestSourceabilityWiring(unittest.TestCase):
    """The DR's 'wire to the existing sourceability_gate': a ledger sign satisfies its verified tier."""
    def test_ledger_sign_flips_review_to_pass(self):
        import sourceability_gate as SG
        el = {"name": "bed", "kind": "bed", "x": 0, "y": 0, "w": 2000, "d": 2088, "ffe_tag": "FFE-M01"}
        cand = _cand(verified=False, w=2000, d=2088)
        cand["csi"] = "12 58 00"
        ffe = {"items": [{"tag": "FFE-M01", "role": "Bed", "candidates": [cand]}]}
        # no ledger -> REVIEW (verified:false)
        self.assertEqual(SG.check_sourced(el, ffe, None)["status"], "REVIEW")
        # with a matching sign -> PASS
        self.assertEqual(SG.check_sourced(el, ffe, [_sign()])["status"], "PASS")

    def test_no_ledger_is_backward_compatible(self):
        import sourceability_gate as SG
        el = {"name": "bed", "kind": "bed", "x": 0, "y": 0, "w": 2000, "d": 2088, "ffe_tag": "FFE-M01"}
        cand = _cand(verified=True, w=2000, d=2088)
        ffe = {"items": [{"tag": "FFE-M01", "role": "Bed", "candidates": [cand]}]}
        self.assertEqual(SG.check_sourced(el, ffe)["status"], "PASS")   # inline verified, no ledger

    def test_ledger_pass_surfaces_provenance_in_detail(self):
        # a ledger-driven PASS must be visibly distinct from an inline PASS in the moat's own report
        import sourceability_gate as SG
        el = {"name": "bed", "kind": "bed", "x": 0, "y": 0, "w": 2000, "d": 2088, "ffe_tag": "FFE-M01"}
        cand = _cand(verified=False, w=2000, d=2088)
        ffe = {"items": [{"tag": "FFE-M01", "role": "Bed", "candidates": [cand]}]}
        r = SG.check_sourced(el, ffe, [_sign()])
        self.assertEqual(r["status"], "PASS")
        self.assertIn("owner-signed by designer-a", r["detail"])

    def test_truthy_non_true_verified_is_backward_compatible_with_ledger_present(self):
        # verified:1 (legacy truthy) must stay PASS even when a NON-binding ledger is auto-loaded
        import sourceability_gate as SG
        el = {"name": "bed", "kind": "bed", "x": 0, "y": 0, "w": 2000, "d": 2088, "ffe_tag": "FFE-M01"}
        cand = _cand(verified=1, w=2000, d=2088)   # non-canonical truthy
        ffe = {"items": [{"tag": "FFE-M01", "role": "Bed", "candidates": [cand]}]}
        other = _sign(sku="999-unrelated", source="Nowhere")   # valid but binds a different product
        self.assertEqual(SG.check_sourced(el, ffe, [other])["status"], "PASS")


class TestLoadSignoff(unittest.TestCase):
    def test_bare_list(self):
        self.assertEqual(len(SO.load_signoff([_sign(), _sign()])), 2)

    def test_signed_key(self):
        self.assertEqual(len(SO.load_signoff({"signed": [_sign()]})), 1)

    def test_drops_non_dicts(self):
        self.assertEqual(SO.load_signoff({"signed": [_sign(), "junk", None, 5]}), [SO.load_signoff({"signed": [_sign()]})[0]])

    def test_garbage_is_empty(self):
        self.assertEqual(SO.load_signoff("nope"), [])
        self.assertEqual(SO.load_signoff({"signed": "nope"}), [])


if __name__ == "__main__":
    unittest.main()
