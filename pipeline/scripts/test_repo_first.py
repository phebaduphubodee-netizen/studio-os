"""Tests for repo_first — the rung that refuses to let us look outside for what
we already wrote down.

The regression at the top is the one that matters: the second version of
`used_tokens` scanned file CONTENT and the module PASSED ITS OWN CHECK, because
its docstring names FurniMesh eleven times. A checker satisfied by its own prose
is the defect it was built to catch, so that case is pinned first and by name.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_first as RF  # noqa: E402


TABLE = """
## Sources — whitelist vs blacklist
| Source | Client-deliverable? | Notes |
|---|---|---|
| **SketchUp 3D Warehouse** | ✅ ONLY as a Combined-Work scene | Manual download only. |
| **FurniMesh** | ✅ cleanest | the ONLY source legal to script-fetch. |
| **Poly Haven** | ✅ | Already fetched by `pipeline/scripts/assets.py`. |
| **ambientCG** | ✅ (not yet used) | No fetcher yet, deliberately not written yet. |
| **BIMobject** | ❌ personal-use only | EULA 4.4(b). |
| **HomePro** | facts only | Retail catalog. |
"""


def _repo(tmp, scripts=None, shelf=None, tiers=None):
    os.makedirs(os.path.join(tmp, "pipeline", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "qa"), exist_ok=True)
    for name, body in (scripts or {}).items():
        with open(os.path.join(tmp, "pipeline", "scripts", name), "w",
                  encoding="utf-8") as f:
            f.write(body)
    for slug, src in (shelf or {}).items():
        d = os.path.join(tmp, "assets", "shared", "warehouse", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SOURCE.json"), "w", encoding="utf-8") as f:
            json.dump(src, f)
    if tiers is not None:
        with open(os.path.join(tmp, "qa", "sourcing-tiers.json"), "w",
                  encoding="utf-8") as f:
            json.dump(tiers, f)
    return tmp


def _src(name):
    return [s for s in RF.parse_sources(TABLE) if s["name"] == name][0]


class TestTable(unittest.TestCase):
    def test_reads_only_approved_rows(self):
        rows = RF.parse_sources(TABLE)
        names = [r["name"] for r in rows]
        self.assertIn("FurniMesh", names)
        self.assertIn("BIMobject", names)
        approved = {r["name"] for r in rows if r["approved"]}
        self.assertEqual(approved, {"SketchUp 3D Warehouse", "FurniMesh",
                                    "Poly Haven", "ambientCG"})

    def test_header_and_rule_lines_are_not_sources(self):
        self.assertNotIn("Source", [r["name"] for r in RF.parse_sources(TABLE)])


class TestUsedTokens(unittest.TestCase):
    def test_prose_naming_a_source_is_NOT_use(self):
        """THE REGRESSION. A module whose docstring says the name over and over
        must not make that source read — this exact shape made repo_first pass
        its own check."""
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp, scripts={"talker.py": '"""furnimesh FurniMesh furnimesh.\n'
                                             'We should use furnimesh one day."""\n'})
            state, _ = RF.source_state(_src("FurniMesh"), RF.used_tokens(tmp))
            self.assertEqual(state, "SILENT")

    def test_a_host_in_code_IS_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp, scripts={"assets.py": 'API = "https://api.polyhaven.com/x"\n'})
            state, _ = RF.source_state(_src("Poly Haven"), RF.used_tokens(tmp))
            self.assertEqual(state, "used")

    def test_bytes_on_the_shelf_ARE_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp, shelf={"m1": {"source": "furnimesh.com",
                                     "license_id": "furnimesh"}})
            state, _ = RF.source_state(_src("FurniMesh"), RF.used_tokens(tmp))
            self.assertEqual(state, "used")

    def test_a_tier_row_IS_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp, tiers={"tiers": [{"id": "furnimesh"}]})
            state, _ = RF.source_state(_src("FurniMesh"), RF.used_tokens(tmp))
            self.assertEqual(state, "used")


class TestRule1(unittest.TestCase):
    def test_silent_approved_source_is_a_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            v = RF.check(TABLE, {"asks": []}, tmp)
            self.assertTrue(any("FurniMesh" in s and "DELIVERABLE" in s for s in v))

    def test_declared_unused_passes_without_a_migration(self):
        """ambientCG says so in its own Notes cell; the document must pass as
        written, or the rung gets reverted on the day it lands."""
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            v = RF.check(TABLE, {"asks": []}, tmp)
            # match the SUBJECT, not the substring: every rule-1 message ends
            # "...the way ambientCG's does", so a bare `in` matched the advice
            # instead of the accusation.
            self.assertFalse(any("'ambientCG'" in s for s in v))

    def test_a_declined_source_is_never_asked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp)
            v = RF.check(TABLE, {"asks": []}, tmp)
            self.assertFalse(any("'BIMobject'" in s or "'HomePro'" in s
                                 for s in v))

    def test_no_table_is_not_a_pass(self):
        v = RF.check(None, {"asks": []}, ".")
        self.assertEqual(len(v), 1)
        self.assertIn("unfalsifiable", v[0])


class TestRule2(unittest.TestCase):
    def _asks(self, **kw):
        row = {"id": "ASK-999", "money": "yes — $10", "status": "open"}
        row.update(kw)
        return {"asks": [row]}

    def _clean(self, tmp):
        """A temp repo where RULE 1 is satisfied for every approved source, so
        these tests measure RULE 2 alone. Two rules in one violation list is how
        a test starts asserting the wrong thing."""
        _repo(tmp,
              scripts={"assets.py": 'A = "https://api.polyhaven.com/x"',
                       "warehouse.py": 'B = "https://3dwarehouse.sketchup.com/v"'},
              shelf={"m": {"license_id": "furnimesh"}})
        return tmp

    def test_money_ask_with_no_read_first_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            v = RF.check(TABLE, self._asks(), self._clean(tmp))
            self.assertTrue(any("ASK-999" in s and "read_first" in s for s in v))

    def test_read_first_naming_a_missing_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            v = RF.check(TABLE, self._asks(read_first="docs/NOPE.md"),
                         self._clean(tmp))
            self.assertTrue(any("does not exist" in s for s in v))

    def test_read_first_must_include_a_source_of_truth_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._clean(tmp)
            os.makedirs(os.path.join(tmp, "projects"), exist_ok=True)
            open(os.path.join(tmp, "projects", "gate.md"), "w").close()
            v = RF.check(TABLE, self._asks(read_first="projects/gate.md"), tmp)
            self.assertTrue(any("citing itself" in s for s in v))

    def test_a_good_row_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._clean(tmp)
            os.makedirs(os.path.join(tmp, "docs"), exist_ok=True)
            open(os.path.join(tmp, "docs", "LICENSING.md"), "w").close()
            v = RF.check(TABLE, self._asks(read_first="docs/LICENSING.md"), tmp)
            self.assertEqual(v, [])

    def test_a_list_is_accepted_as_well_as_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._clean(tmp)
            os.makedirs(os.path.join(tmp, "docs"), exist_ok=True)
            open(os.path.join(tmp, "docs", "LICENSING.md"), "w").close()
            v = RF.check(TABLE, self._asks(read_first=["docs/LICENSING.md"]), tmp)
            self.assertEqual(v, [])

    def test_a_free_ask_is_not_asked_for_read_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            v = RF.check(TABLE, {"asks": [{"id": "A", "money": "no",
                                           "status": "open"}]}, self._clean(tmp))
            self.assertEqual(v, [])

    def test_an_answered_ask_is_not_reopened(self):
        with tempfile.TemporaryDirectory() as tmp:
            v = RF.check(TABLE, self._asks(status="answered"), self._clean(tmp))
            self.assertEqual(v, [])


class TestRegisterLine(unittest.TestCase):
    def test_a_register_nothing_names_is_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo(tmp, scripts={"a.py": "open('qa/read-me.json')\n"})
            for n in ("read-me.json", "nobody-reads-me.json"):
                open(os.path.join(tmp, "qa", n), "w").close()
            got = {r for r, _ in RF.unread_registers(tmp)}
            self.assertIn("qa/nobody-reads-me.json", got)
            self.assertNotIn("qa/read-me.json", got)


class TestLive(unittest.TestCase):
    def test_the_real_repo_reproduces_the_finding_it_was_written_from(self):
        """This test used to pin 'FurniMesh is SILENT' and said: if this ever
        changes, either the fetcher landed (good) or the rung stopped seeing
        it. It was the good case: `furnimesh.py` landed 2026-08-22
        (ORD-2026-08-22-process-review-actions item 3) carrying the host
        literal, so the source the table ranked first is finally USED."""
        root = RF._repo_root()
        text = RF.load_text(RF.LICENSING_REL, root)
        self.assertIsNotNone(text)
        states = {n: s for n, s, _ in RF.report(text, root)}
        self.assertEqual(states.get("FurniMesh"), "used")
        self.assertEqual(states.get("Poly Haven"), "used")

    def test_this_module_does_not_make_itself_pass(self):
        """The live half of this test flipped 2026-08-22: 'furnimesh' is now a
        used token because `furnimesh.py` carries the real host — a FETCHER,
        which is exactly what the rung demands. The spirit it originally
        pinned — prose alone must never register a source as consumed — stays
        pinned by test_prose_naming_a_source_is_NOT_use on a synthetic repo,
        and by this module itself still carrying no host."""
        self.assertIn("furnimesh", RF.used_tokens(RF._repo_root()))
        with open(RF.__file__, encoding="utf-8") as fh:
            self.assertNotIn("://furnimesh", fh.read().lower(),
                             "repo_first.py must never carry the host itself")


if __name__ == "__main__":
    unittest.main(verbosity=2)
