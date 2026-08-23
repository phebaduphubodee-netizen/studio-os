#!/usr/bin/env python3
"""Tests for style_check.py.

The NEGATIVE CONTROLS are the point, and each one is a real thing this repo
did:

  * `test_a_style_read_off_our_own_render_is_refused` — "Japandi" entered on
    2026-08-11 as a blind critic's DESCRIPTION OF OUR OWN FRAME and became the
    rule selecting what we buy. The register must refuse that provenance by
    name, not by taste.
  * `test_signed_where_that_points_nowhere` — the first run of this checker
    against the first draft of the register caught exactly this: the DD
    document was cited at 04_visualization/ and lives at 03_layout/.
  * `test_the_floor_missing_entirely_is_a_violation` — the floor had no spec
    key for 40 days. The register must not be able to be silent about it.
  * `test_client_description_contradiction` — walls/feature_wall/millwork are
    signed to cool plaster and oak while material_defaults still tells the
    CLIENT warm-white paint and walnut, and test_rationale stays green because
    it drift-guards against build_room's source rather than the signature.
  * `test_a_widened_palette_gap_fails` — the one rule that reads pixels. It
    may only ever ratchet down.
  * `test_could_not_run_is_not_a_pass` — R11's own sentence: "could not look"
    must never print like "looked and it was fine".
  * `test_the_live_register_is_honest` — the register in this repo, checked
    against the real canonical spec, must return []. If a later commit signs a
    slot and forgets material_defaults, this is the test that goes red.
"""

import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import style_check as SC

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC_REL = ("projects/PRJ-2026-002_c001-house/03_layout/"
            "master-suite.CANONICAL.spec.json")


def _slot(slot, kind, **kw):
    row = {"slot": slot, "kind": kind}
    row.update(kw)
    return row


def _signed(slot, kind, preset):
    return _slot(slot, kind, status="signed", preset=preset,
                 signed_where="qa/style-of-record.json")


def _unsigned(slot, kind):
    return _slot(slot, kind, status="legacy-unsigned", since="2026-07-14",
                 renders_as="a legacy hardcode", restart_by="sign it")


def _register(**over):
    d = {
        "_slot_floor": 9,
        "_unsigned_ceiling": 6,
        "style": {"name": "Test Style", "decided_by": "builder",
                  "decision_row": "D-122", "date": "2026-08-23",
                  "derived_from": "qa/style-of-record.json",
                  "retired_names": []},
        "slots": [_signed("walls", "surface", "cool_plaster"),
                  _signed("feature_wall", "surface", "oak_veneer"),
                  _signed("millwork", "surface", "oak_veneer_photo"),
                  _unsigned("floor", "surface"),
                  _unsigned("glazing", "surface"),
                  _unsigned("fixtures", "surface"),
                  _unsigned("fabric", "family"),
                  _unsigned("wood", "family"),
                  _unsigned("neutral", "family")],
        "edges": [],
        "client_description_debt": {
            "walls": {"since": "2026-07-16", "restart_by": "fix rationale"},
            "feature_wall": {"since": "2026-07-16", "restart_by": "fix rationale"},
            "millwork": {"since": "2026-07-16", "restart_by": "fix rationale"}},
        "palette_measured": {
            "frame": "qa/style-of-record.json",   # any real path; not read as an image
            "measured_at": "2026-08-23",
            "declared": {"dominant": 0.60, "secondary": 0.30, "accent": 0.10},
            "dominant_share": 0.30, "secondary_share": 0.19, "accent_share": 0.18,
            "gap_worst": 0.30, "gap_ceiling": 0.32, "gap_since": "2026-08-23",
            "close_by": "sign the floor"},
    }
    d.update(over)
    return d


def _v(data, **kw):
    kw.setdefault("repo_root", REPO)
    return SC.check(copy.deepcopy(data), **kw)


class Shape(unittest.TestCase):
    def test_a_clean_fixture_is_clean(self):
        self.assertEqual(_v(_register()), [])

    def test_unreadable_register_is_exactly_one_violation(self):
        v = SC.check(None)
        self.assertEqual(len(v), 1)
        self.assertIn("style-of-record.json", v[0])

    def test_a_slot_may_not_leave_the_file(self):
        d = _register()
        d["slots"] = d["slots"][:-1]
        v = _v(d)
        self.assertTrue(any("floor of 9" in x for x in v))
        self.assertTrue(any("neutral" in x and "no row for it" in x for x in v))

    def test_the_floor_missing_entirely_is_a_violation(self):
        """40 days of a floor with no key must not be expressible as silence."""
        d = _register()
        d["slots"] = [s for s in d["slots"] if s["slot"] != "floor"]
        d["_slot_floor"] = 8
        v = _v(d)
        self.assertTrue(any(x.startswith("floor:") for x in v), v)

    def test_a_slot_the_build_cannot_address_is_refused(self):
        d = _register()
        d["slots"].append(_unsigned("ceiling_paint", "surface"))
        v = _v(d)
        self.assertTrue(any("ceiling_paint" in x and "cannot address" in x
                            for x in v))

    def test_no_third_slot_state(self):
        d = _register()
        d["slots"][3]["status"] = "pending"
        self.assertTrue(any("not one of" in x for x in _v(d)))


class Ratchets(unittest.TestCase):
    def test_unsigned_ceiling_only_ever_falls(self):
        d = _register()
        d["slots"][0] = _unsigned("walls", "surface")     # un-signing a slot
        v = _v(d)
        self.assertTrue(any("ceiling of 6" in x for x in v), v)

    def test_signing_a_slot_never_trips_the_ceiling(self):
        d = _register()
        d["slots"][3] = _signed("floor", "surface", "oak_wood_floor")
        d["client_description_debt"]["floor"] = {"since": "2026-08-23",
                                                 "restart_by": "x"}
        self.assertFalse(any("ceiling" in x for x in _v(d)))


class Provenance(unittest.TestCase):
    def test_a_style_read_off_our_own_render_is_refused(self):
        for bad in ("our_own_render", "critic_description", "OUR OWN RENDER"):
            d = _register()
            d["style"]["derived_from"] = bad
            v = _v(d)
            self.assertTrue(any("REFUSED BY NAME" in x for x in v), bad)

    def test_owner_override_locks_the_row_to_him(self):
        d = _register()
        d["style"]["owner_override"] = "ชอบอันขวา"
        v = _v(d)
        self.assertTrue(any("locked" in x or "his" in x for x in v), v)
        d["style"]["decided_by"] = "owner"
        self.assertFalse(any("owner_override" in x for x in _v(d)))

    def test_decider_has_no_pending_state(self):
        d = _register()
        d["style"]["decided_by"] = "pending"
        self.assertTrue(any("pending" in x for x in _v(d)))


class Signatures(unittest.TestCase):
    def test_signed_where_that_points_nowhere(self):
        """The real first-run catch: the DD cited at 04_visualization/."""
        d = _register()
        d["slots"][0]["signed_where"] = ("projects/PRJ-2026-002_c001-house/"
                                         "04_visualization/element1-oak.md")
        v = _v(d)
        self.assertTrue(any("does not exist" in x for x in v), v)

    def test_a_preset_that_cannot_be_built_is_not_a_signature(self):
        d = _register()
        d["slots"][0]["preset"] = "burled_unobtainium"
        self.assertTrue(any("not in the live preset library" in x for x in _v(d)))

    def test_unsigned_must_state_its_age_its_value_and_its_way_out(self):
        d = _register()
        d["slots"][3] = _slot("floor", "surface", status="legacy-unsigned")
        v = [x for x in _v(d) if x.startswith("floor ")]
        self.assertEqual(len(v), 3, v)


class SpecAgreement(unittest.TestCase):
    def _spec(self, surfaces=None, families=None):
        return {"materials": {"surfaces": surfaces or {},
                              "families": families or {}}}

    def test_spec_and_register_must_name_the_same_preset(self):
        d = _register()
        v = _v(d, spec=self._spec({"walls": "warm_white_paint"}))
        self.assertTrue(any("reopen the register, never the frame" in x
                            for x in v), v)

    def test_a_signature_the_renderer_never_reads_is_prose(self):
        d = _register()
        v = _v(d, spec=self._spec({}))
        self.assertTrue(any("never reads is prose" in x for x in v), v)

    def test_spec_selecting_a_slot_the_register_calls_unsigned(self):
        d = _register()
        v = _v(d, spec=self._spec({"walls": "cool_plaster",
                                   "feature_wall": "oak_veneer",
                                   "millwork": "oak_veneer_photo",
                                   "floor": "oak_wood_floor"}))
        self.assertTrue(any("floor" in x and "legacy-unsigned" in x
                            for x in v), v)


class Edges(unittest.TestCase):
    def test_a_prohibition_with_no_test_is_prose(self):
        d = _register()
        d["edges"] = [{"id": "E1", "rule": "no velvet", "source": "concept",
                       "test": "none"}]
        v = _v(d)
        self.assertTrue(any("no way to be wrong is prose" in x for x in v), v)

    def test_untestable_today_is_allowed_but_must_name_a_way_out(self):
        d = _register()
        d["edges"] = [{"id": "E3", "rule": "lined drapery", "source": "concept",
                       "test": "none-yet"}]
        self.assertTrue(any("none-yet with no restart_by" in x for x in _v(d)))
        d["edges"][0]["restart_by"] = "add a lining key in P4"
        self.assertEqual([x for x in _v(d) if x.startswith("E3")], [])

    def test_an_edge_source_must_exist(self):
        d = _register()
        d["edges"] = [{"id": "E9", "rule": "x", "test": "panel",
                       "source": "projects/nowhere/concept.md:1"}]
        self.assertTrue(any("does not exist" in x for x in _v(d)))


class OpensThePicture(unittest.TestCase):
    """R11 applied to style. These are the only rules here that read pixels —
    indirectly, through a measurement style_measure.py takes out of process."""

    def test_a_register_that_never_looked_fails(self):
        d = _register()
        del d["palette_measured"]
        v = _v(d)
        self.assertTrue(any("never opens the picture" in x for x in v), v)

    def test_could_not_run_is_not_a_pass(self):
        d = _register()
        d["palette_measured"]["could_not_run"] = "PIL missing"
        v = _v(d)
        self.assertTrue(any("COULD NOT RUN" in x for x in v), v)
        self.assertTrue(any("looked and it was fine" in x for x in v), v)

    def test_a_widened_palette_gap_fails(self):
        d = _register()
        d["palette_measured"]["dominant_share"] = 0.10   # gap 0.50 vs ceiling 0.32
        v = _v(d)
        self.assertTrue(any("THE CEILING ONLY EVER FALLS" in x for x in v), v)

    def test_a_narrowed_gap_passes(self):
        d = _register()
        d["palette_measured"].update({"dominant_share": 0.55,
                                      "secondary_share": 0.28,
                                      "accent_share": 0.12})
        self.assertEqual([x for x in _v(d) if "palette" in x.lower()
                          or "CEILING" in x], [])

    def test_an_unbounded_gap_is_refused(self):
        d = _register()
        del d["palette_measured"]["gap_ceiling"]
        self.assertTrue(any("no `gap_ceiling`" in x for x in _v(d)))

    def test_a_gap_must_print_its_age_and_name_its_closer(self):
        d = _register()
        del d["palette_measured"]["gap_since"]
        del d["palette_measured"]["close_by"]
        v = _v(d)
        self.assertTrue(any("gap_since" in x for x in v))
        self.assertTrue(any("close_by" in x for x in v))

    def test_a_measurement_of_a_frame_nobody_can_open(self):
        d = _register()
        d["palette_measured"]["frame"] = "pipeline/output/never_rendered.png"
        self.assertTrue(any("does not exist" in x for x in _v(d)))


class ClientFacing(unittest.TestCase):
    def test_client_description_contradiction(self):
        """A signed slot the client is told is something else."""
        d = _register()
        d["client_description_debt"] = {}
        v = SC.client_description(d)
        got = {x.split(":")[0] for x in v}
        self.assertEqual(got, {"walls", "feature_wall", "millwork"}, v)
        self.assertTrue(any("rationale.py ships that string" in x for x in v))

    def test_acknowledging_it_with_a_date_and_a_way_out_clears_it(self):
        self.assertEqual(SC.client_description(_register()), [])

    def test_a_bare_acknowledgement_does_not_clear_it(self):
        d = _register()
        d["client_description_debt"]["walls"] = {"since": "2026-07-16"}
        v = SC.client_description(d)
        self.assertTrue(any(x.startswith("walls:") for x in v), v)


class RetiredNames(unittest.TestCase):
    """R9b: no allowlist. The walk covers the trees the machine reads, and every
    hit must be acknowledged — exempting a file is not available."""

    def _tree(self, tmp, name, files):
        for rel, body in files.items():
            fp = os.path.join(tmp, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(body)
        d = _register()
        d["style"]["retired_names"] = [name]
        return d

    def test_an_unacknowledged_retired_name_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, "Japandi",
                           {"qa/selector.json": '{"rule": "inside Japandi"}'})
            v = SC.retired_name_hits(d, repo_root=tmp)
            self.assertTrue(any("not acknowledged" in x for x in v), v)

    def test_an_acknowledged_name_in_a_known_file_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, "Japandi",
                           {"qa/selector.json": '{"rule": "inside Japandi"}'})
            d["name_debt"] = {"Japandi": {"since": "2026-08-11",
                                          "restart_by": "at the month review",
                                          "where_seen": "qa/selector.json"}}
            self.assertEqual(SC.retired_name_hits(d, repo_root=tmp), [])

    def test_the_debt_may_exist_but_may_not_spread(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, "Japandi",
                           {"qa/selector.json": '{"rule": "inside Japandi"}',
                            "qa/new_file.json": '{"style": "Japandi"}'})
            d["name_debt"] = {"Japandi": {"since": "2026-08-11",
                                          "restart_by": "at the month review",
                                          "where_seen": "qa/selector.json"}}
            v = SC.retired_name_hits(d, repo_root=tmp)
            self.assertTrue(any("NEW file" in x for x in v), v)
            self.assertTrue(any("not allowed to SPREAD" in x for x in v), v)

    def test_the_walk_is_not_an_allowlist(self):
        """A name typed into a file nobody thought of must still be caught."""
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, "Japandi",
                           {"pipeline/scripts/some_new_selector.py":
                            '# pick anything inside the Japandi envelope\n'})
            v = SC.retired_name_hits(d, repo_root=tmp)
            self.assertTrue(any("some_new_selector.py" in x for x in v), v)


class TheLiveRegister(unittest.TestCase):
    def test_the_live_register_is_honest(self):
        data = SC.load(repo_root=REPO)
        self.assertIsNotNone(data, "qa/style-of-record.json is unreadable")
        with open(os.path.join(REPO, SPEC_REL), encoding="utf-8") as f:
            spec = json.load(f)
        self.assertEqual(SC.check(data, repo_root=REPO, spec=spec), [])

    def test_the_live_register_covers_every_addressable_role(self):
        import material_presets as MP
        data = SC.load(repo_root=REPO)
        named = {s["slot"] for s in SC.slots(data)}
        self.assertEqual(named,
                         set(MP.ALLOWED_SURFACES) | set(MP.ALLOWED_FAMILIES))

    def test_the_live_register_actually_looked(self):
        data = SC.load(repo_root=REPO)
        m = data.get("palette_measured") or {}
        self.assertTrue(m.get("frame", "").endswith(".png"))
        self.assertNotIn("could_not_run", m)
        self.assertGreater(m.get("gap_worst", 0), 0.0,
                           "a gap of exactly zero would mean the instrument "
                           "was not run against a real frame")

    def test_one_line_and_style_lines_never_raise(self):
        for d in (None, {}, {"slots": []}, SC.load(repo_root=REPO)):
            SC.style_lines(d if d is not None else {})
        self.assertIn("STYLE:", SC.one_line(SC.load(repo_root=REPO)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
