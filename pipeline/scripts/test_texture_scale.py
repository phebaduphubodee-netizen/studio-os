#!/usr/bin/env python3
"""Tests for texture_scale.py.

THE NEGATIVE CONTROLS ARE THE POINT, and every one of them is a real thing this
repo did or nearly did:

  * `test_the_typed_floor_is_refused` — the defect itself. `wood_floor` declares
    1699.9997 mm and the room floor mapped it at 2.4 m for seven weeks. The rung
    must name the ratio, not merely disagree.
  * `test_reverting_the_floor_line_goes_red` — the strongest control available:
    a temp tree carrying the OLD source line, checked by the LIVE registry. If
    somebody puts `tile_m=2.4` back, this is what catches it. Written against a
    patched root, because a control that reads the real repo would be marking
    its own homework.
  * `test_no_sidecar_is_not_a_pass` and `test_could_not_run_is_not_a_pass` —
    R11's sentence: "could not look" must never print like "looked and it was
    fine".
  * `test_sidecar_self_check_catches_a_hand_edit` — an assertion somebody edited
    by hand is not an assertion. Same shape as pixel_check's SELF-CHECK.
  * `test_anisotropic_set_mapped_uniformly_is_refused` — four of the sixteen
    cached sets are not square (wood_cabinet_worn_long is 1000 x 500 mm). One
    number standing for two axes is this repo's own recurring defect.
  * `test_sweep_sees_the_positional_tuple_shape` — the first version of the
    sweep looked only for `tile_m=`-shaped literals and missed the TRN lanes
    entirely, because they carry the tile as the fifth element of a tuple.
    Anchoring on a keyword IS an allowlist one level down.
  * `test_sweep_baseline_may_not_rise` — the backlog is a ratchet.
  * `test_the_live_registry_is_honest` — the registry in this repo, against the
    real code, must return []. If a later commit retunes a tile and forgets the
    row, this is the test that goes red.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import texture_scale as TS

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _root(slugs=None):
    """A throwaway repo root holding only what the rung reads."""
    d = tempfile.mkdtemp(prefix="texscale_")
    for slug, dims in (slugs or {"demo": [1700.0, 1700.0]}).items():
        TS.write_sidecar(slug, dims, "test://" + slug, root=d)
    return d


def _site(**over):
    s = {
        "id": "TS-T1",
        "slug": "demo",
        "surface": "a test surface",
        "tile_m": 1.7,
        "departure": None,
        "why": "the publisher's own number",
    }
    s.update(over)
    return s


def _registry(sites, baseline=0, debt_baseline=None):
    n = debt_baseline if debt_baseline is not None else len(
        [s for s in sites if s.get("debt")])
    return {"sites": sites, "sweep_baseline": baseline, "debt_baseline": n}


class TypedTiles(unittest.TestCase):

    def test_the_typed_floor_is_refused(self):
        root = _root()
        v = TS.check(_registry([_site(tile_m=2.4)]), root)
        self.assertTrue(v, "a 2.4 m tile on a 1.7 m texture must not pass")
        self.assertIn("1.4118", " ".join(v))

    def test_the_asserted_floor_passes(self):
        root = _root()
        self.assertEqual(TS.check(_registry([_site(tile_m=1.7)]), root), [])

    def test_rounding_to_the_published_millimetre_is_not_a_departure(self):
        # 1.7 against 1.6999997 is a rounding, not a decision.
        root = _root()
        self.assertEqual(
            TS.check(_registry([_site(tile_m=1.6999996900558472)]), root), [])


class Departures(unittest.TestCase):

    def test_a_departure_needs_a_real_reason(self):
        root = _root()
        v = TS.check(_registry([_site(
            tile_m=2.4,
            departure={"axis": "u", "ratio": 1.4118, "why": "looks better"})]),
            root)
        self.assertTrue(any("why" in x for x in v))

    def test_a_departure_ratio_must_reproduce(self):
        root = _root()
        v = TS.check(_registry([_site(
            tile_m=2.4,
            departure={"axis": "u", "ratio": 1.10,
                       "why": "a stated ratio that does not match the numbers"})]),
            root)
        self.assertTrue(any("claims" in x for x in v))

    def test_a_signed_departure_passes(self):
        root = _root()
        self.assertEqual(TS.check(_registry([_site(
            tile_m=2.4,
            departure={"axis": "both", "ratio": 1.4118,
                       "why": "deliberately oversize on both axes, and here is "
                              "the reason it is wanted on this surface"})]), root), [])

    def test_a_v_departure_does_not_exempt_u(self):
        """The millwork's along-grain stretch must not silently license a wrong
        across-grain scale — the axis a departure names is the only axis it
        covers."""
        root = _root()
        v = TS.check(_registry([_site(
            tile_m=2.4, tile_v_m=2.8,
            departure={"axis": "v", "ratio": 1.6471,
                       "why": "leaves run continuous to the full panel height"})]),
            root)
        self.assertTrue(any("maps U" in x for x in v), v)


class Anisotropy(unittest.TestCase):

    def test_anisotropic_set_mapped_uniformly_is_refused(self):
        root = _root({"oblong": [1000.0, 500.0]})
        v = TS.check(_registry([_site(slug="oblong", tile_m=1.0)]), root)
        self.assertTrue(any("maps V" in x for x in v), v)

    def test_anisotropic_set_mapped_per_axis_passes(self):
        root = _root({"oblong": [1000.0, 500.0]})
        self.assertEqual(
            TS.check(_registry([_site(slug="oblong", tile_m=1.0,
                                      tile_v_m=0.5)]), root), [])


class CouldNotRun(unittest.TestCase):

    def test_no_sidecar_is_not_a_pass(self):
        root = _root()
        v = TS.check(_registry([_site(slug="never_ingested")]), root)
        self.assertTrue(any("NO SIDECAR" in x for x in v), v)

    def test_could_not_run_is_not_a_pass(self):
        self.assertTrue(TS.check(None, _root()))

    def test_an_empty_registry_proves_nothing(self):
        v = TS.check(_registry([]), _root())
        self.assertTrue(any("proves nothing" in x for x in v), v)

    def test_sidecar_self_check_catches_a_hand_edit(self):
        root = _root()
        p = TS.sidecar_path("demo", root)
        d = json.load(open(p, encoding="utf-8"))
        d["tile_m"] = 2.4                      # somebody "fixed" it by hand
        json.dump(d, open(p, "w", encoding="utf-8"))
        v = TS.check(_registry([_site(tile_m=1.7)]), root)
        self.assertTrue(any("SELF-CHECK" in x for x in v), v)


class Assertions(unittest.TestCase):

    def test_an_assertion_that_cannot_run_is_not_a_pass(self):
        root = _root()
        v = TS.check(_registry([_site(assert_=None, **{"assert": [
            {"file": "pipeline/scripts/nothing_here.py", "pattern": "x",
             "why": "a file that does not exist in this tree at all"}]})]), root)
        self.assertTrue(any("cannot be read" in x for x in v), v)

    def test_an_assertion_needs_a_why(self):
        root = _root()
        os.makedirs(os.path.join(root, "pipeline/scripts"), exist_ok=True)
        with open(os.path.join(root, "pipeline/scripts/x.py"), "w") as f:
            f.write("tile\n")
        v = TS.check(_registry([_site(**{"assert": [
            {"file": "pipeline/scripts/x.py", "pattern": "tile", "why": "no"}]})]),
            root)
        self.assertTrue(any("`why`" in x for x in v), v)

    def test_reverting_the_floor_line_goes_red(self):
        """THE REAL NEGATIVE CONTROL. The LIVE registry, run against a tree whose
        build_room.py still carries the pre-STY-7 line."""
        live = TS.load(REPO)
        self.assertIsNotNone(live, "the live registry must be readable")
        root = _root({"wood_floor": [1699.9996900558472, 1699.9996900558472]})
        os.makedirs(os.path.join(root, "pipeline/scripts"), exist_ok=True)
        with open(os.path.join(root, "pipeline/scripts/build_room.py"),
                  "w", encoding="utf-8") as f:
            f.write("def _planar_uv(obj, tile_m=2.0):\n    pass\n"
                    "# the pre-2026-08-24 mapping\n"
                    "_planar_uv(obj, tile_m=2.4)\n")
        ts001 = [s for s in live["sites"] if s["id"] == "TS-001"][0]
        v = TS.site_violations(ts001, root)
        self.assertTrue(any("no longer matches" in x for x in v), v)


class Sweep(unittest.TestCase):

    def test_sweep_sees_the_positional_tuple_shape(self):
        """The shape the first version of this sweep could not see."""
        root = _root({"wood_floor": [1700.0, 1700.0]})
        os.makedirs(os.path.join(root, "pipeline/scripts"), exist_ok=True)
        with open(os.path.join(root, "pipeline/scripts/trn.py"),
                  "w", encoding="utf-8") as f:
            f.write('M = {"veneer_oak": ((0.5, 0.4, 0.3), 0.6, 0.0, '
                    '"wood_floor", 3.2)}\n')
        hits = TS.sweep(root)
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("trn.py", hits[0][0])

    def test_sweep_skips_comments(self):
        root = _root()
        os.makedirs(os.path.join(root, "pipeline/scripts"), exist_ok=True)
        with open(os.path.join(root, "pipeline/scripts/c.py"),
                  "w", encoding="utf-8") as f:
            f.write("# it used to say tile_m=2.4 here\n")
        self.assertEqual(TS.sweep(root), [])

    def test_sweep_baseline_may_not_rise(self):
        root = _root()
        os.makedirs(os.path.join(root, "pipeline/scripts"), exist_ok=True)
        with open(os.path.join(root, "pipeline/scripts/new.py"),
                  "w", encoding="utf-8") as f:
            f.write("_planar_uv(obj, tile_m=3.1)\n")
        _hits, v = TS.sweep_violations({"sweep_baseline": 0}, root)
        self.assertTrue(any("ratchet" in x for x in v), v)

    def test_a_missing_baseline_is_refused(self):
        _hits, v = TS.sweep_violations({}, _root())
        self.assertTrue(v)


class Debt(unittest.TestCase):
    """R13's third state. It is the state that lets this rung be honest on day
    one instead of being switched off in its first week — so it needs sharper
    controls than the states that block, not looser ones."""

    DEBT = {"since": "2026-08-24", "measured_ratio": "u 4.81",
            "restart_by": "measure the on-screen pitch, then decide"}

    def test_a_debt_row_does_not_block(self):
        root = _root()
        self.assertEqual(
            TS.check(_registry([_site(tile_m=99.0, departure=None,
                                      debt=dict(self.DEBT))]), root), [])

    def test_a_debt_row_still_prints_its_ratio(self):
        root = _root()
        reg = _registry([_site(tile_m=99.0, departure=None, debt=dict(self.DEBT))])
        txt = " ".join(TS.lines(reg, root))
        self.assertIn("SCALE DEBT", txt)
        self.assertIn("u 4.81", txt)

    def test_debt_needs_an_age_and_a_named_action(self):
        root = _root()
        for drop in ("since", "restart_by", "measured_ratio"):
            d = dict(self.DEBT)
            del d[drop]
            v = TS.check(_registry([_site(tile_m=99.0, departure=None, debt=d)]),
                         root)
            self.assertTrue(any(drop in x for x in v), (drop, v))

    def test_debt_and_departure_together_is_refused(self):
        root = _root()
        v = TS.check(_registry([_site(
            tile_m=99.0, debt=dict(self.DEBT),
            departure={"axis": "u", "ratio": 58.2,
                       "why": "a ratio cannot be both decided and undecided"})]),
            root)
        self.assertTrue(any("BOTH" in x for x in v), v)

    def test_the_debt_class_may_not_grow(self):
        root = _root()
        v = TS.check(_registry([_site(tile_m=99.0, departure=None,
                                      debt=dict(self.DEBT))],
                               debt_baseline=0), root)
        self.assertTrue(any("may only fall" in x for x in v), v)

    def test_a_missing_debt_baseline_is_refused(self):
        root = _root()
        v = TS.check({"sites": [_site()], "sweep_baseline": 0}, root)
        self.assertTrue(any("debt_baseline" in x for x in v), v)


class TheDoor(unittest.TestCase):

    def test_declared_tile_m_returns_none_for_an_unasserted_slug(self):
        """The door must not invent a plausible default — a plausible default is
        exactly what 2.4 was."""
        self.assertIsNone(TS.declared_tile_m("no_such_texture", _root()))

    def test_the_repo_floor_texture_is_asserted(self):
        self.assertAlmostEqual(TS.declared_tile_m("wood_floor", REPO), 1.7, 5)


class Live(unittest.TestCase):

    def test_the_live_registry_is_honest(self):
        data = TS.load(REPO)
        self.assertIsNotNone(data)
        self.assertEqual(TS.check(data, REPO), [])

    def test_every_cached_set_carries_an_asserted_size(self):
        missing = [s for s in TS.cached_slugs(REPO)
                   if TS.declared_tile_m(s, REPO) is None]
        self.assertEqual(missing, [], f"unasserted texture sets: {missing}")


if __name__ == "__main__":
    unittest.main()
