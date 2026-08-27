"""Tests for skill_usage.py — the counter that answers "did anything ever CALL the
skills this repo builds".

Pinned hardest, because each one is a way this rung could quietly become theatre:
(1) a hook NEVER blocks and NEVER raises, whatever it is fed; (2) zero rows with zero
sessions prints as UNKNOWN-WIRING, never as "nothing was invoked"; (3) the roster is
DISCOVERED from disk, so a new skill is counted the day it lands; (4) the selftest row
is excluded from the call count — an instrument must not count its own heartbeat as work.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_usage as SU  # noqa: E402


class Store(unittest.TestCase):
    def setUp(self):
        self.log = os.path.join(tempfile.mkdtemp(), "usage.jsonl")

    def test_a_skill_call_is_stamped(self):
        row = SU.hook({"tool_name": "Skill", "tool_input": {"skill": "styling-narrative"},
                       "session_id": "deadbeefcafe"}, self.log)
        self.assertEqual(row["kind"], "skill")
        self.assertEqual(row["name"], "styling-narrative")
        self.assertEqual(row["session"], "deadbeef")
        self.assertEqual(len(SU.read_rows(self.log)), 1)

    def test_an_agent_call_is_stamped_under_its_type(self):
        row = SU.hook({"tool_name": "Agent",
                       "tool_input": {"subagent_type": "cold-critic-c2",
                                      "prompt": "judge this bundle"}}, self.log)
        self.assertEqual((row["kind"], row["name"]), ("agent", "cold-critic-c2"))

    def test_other_tools_are_not_our_business(self):
        self.assertIsNone(SU.hook({"tool_name": "Bash",
                                   "tool_input": {"command": "ls"}}, self.log))
        self.assertEqual(SU.read_rows(self.log), [])

    def test_a_malformed_payload_never_raises(self):
        """A hook that can throw is a hook that can stop the lane. It counts work; it
        does not police it."""
        for bad in ({}, {"tool_name": "Skill"}, {"tool_name": "Skill", "tool_input": None},
                    {"tool_name": None}):
            SU.hook(bad, self.log)          # must not raise
        rows = SU.read_rows(self.log)
        self.assertTrue(all(r["kind"] == "skill" for r in rows))

    def test_a_corrupt_line_is_skipped_not_fatal(self):
        with open(self.log, "w", encoding="utf-8") as fh:
            fh.write('{"kind": "skill", "name": "a", "ts": "2026-08-27T10:00:00"}\n')
            fh.write("half a line, no json\n")
        self.assertEqual(len(SU.read_rows(self.log)), 1)

    def test_a_missing_log_reads_empty_and_not_an_error(self):
        self.assertEqual(SU.read_rows(os.path.join(tempfile.mkdtemp(), "nope.jsonl")), [])


class Roster(unittest.TestCase):
    def _tree(self, skills=(), agents=()):
        d = tempfile.mkdtemp()
        sd, ad = os.path.join(d, "skills"), os.path.join(d, "agents")
        for s in skills:
            os.makedirs(os.path.join(sd, s))
            with open(os.path.join(sd, s, "SKILL.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: %s\n---\n" % s)
        os.makedirs(ad, exist_ok=True)
        for a in agents:
            with open(os.path.join(ad, a + ".md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: %s\n---\n" % a)
        with open(os.path.join(ad, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("not an agent\n")
        return sd, ad

    def test_it_is_discovered_from_disk(self):
        """NEVER a typed list: the next skill added would be the one nobody counts, and
        it would be missing from the very report built to catch that."""
        sd, ad = self._tree(("camera-composition", "lighting-design"), ("cold-critic-c2",))
        self.assertEqual(SU.roster(sd, ad),
                         [("skill", "camera-composition"), ("skill", "lighting-design"),
                          ("agent", "cold-critic-c2")])

    def test_a_dir_without_a_skill_md_is_not_a_skill(self):
        sd, ad = self._tree(("real",), ())
        os.makedirs(os.path.join(sd, "_retired"))
        self.assertEqual([n for _, n in SU.roster(sd, ad)], ["real"])

    def test_the_agents_readme_is_not_an_agent(self):
        sd, ad = self._tree((), ("knowledge-manager",))
        self.assertEqual(SU.roster(sd, ad), [("agent", "knowledge-manager")])

    def test_the_live_repo_roster_is_not_empty(self):
        """Cheap wiring check: if the real dirs stop resolving, every number below
        becomes a confident zero."""
        self.assertTrue(SU.roster())


class Reporting(unittest.TestCase):
    ROS = [("skill", "camera-composition"), ("agent", "cold-critic-c2")]

    def test_zero_rows_and_zero_sessions_is_UNKNOWN_not_ZERO(self):
        """The whole reason the session stamp exists. 'The hook is not firing' and
        'nothing was invoked' are different facts, and a rung that cannot separate them
        is the instrument this file was built to replace."""
        out = SU.report_lines([], self.ROS, {"wired_at": "2026-08-27"})
        text = "\n".join(out)
        self.assertIn("hook ยังไม่เคยยิงเลย", text)
        self.assertNotIn("ยังไม่เคยถูกเรียกเลย", text)

    def test_a_call_with_no_session_stamp_still_proves_the_hook_fires(self):
        """CAUGHT ON THE FIRST LIVE READING. A hook wired mid-session writes Skill rows
        before any SessionStart can exist, and the first version of this report printed
        'the hook has never fired' immediately under the row that hook had just written.
        Any row, by either route, is proof the hook is alive."""
        rows = [{"kind": "skill", "name": "camera-composition", "ts": "2026-08-27T11:38:28"}]
        text = "\n".join(SU.report_lines(rows, self.ROS, {"wired_at": "2026-08-27"}))
        self.assertNotIn("hook ยังไม่เคยยิงเลย", text)
        self.assertIn("SessionStart stamp", text)          # says WHY there is no stamp
        self.assertIn("agent:cold-critic-c2", text)        # and still names the unused

    def test_sessions_but_no_calls_names_every_unused_entry(self):
        rows = [{"kind": "session", "ts": "2026-08-27T09:00:00"}]
        text = "\n".join(SU.report_lines(rows, self.ROS, {"wired_at": "2026-08-27"}))
        self.assertIn("ยังไม่เคยถูกเรียกเลย", text)
        self.assertIn("skill:camera-composition", text)
        self.assertIn("agent:cold-critic-c2", text)

    def test_the_selftest_row_is_not_counted_as_work(self):
        rows = [{"kind": "session", "ts": "2026-08-27T09:00:00"},
                {"kind": "skill", "name": "__selftest__", "ts": "2026-08-27T09:01:00"}]
        sessions, calls, last, never, stale = SU.summarise(rows, self.ROS)
        self.assertEqual((sessions, calls), (1, 0))
        self.assertEqual(len(never), 2)

    def test_a_stale_entry_prints_its_age(self):
        rows = [{"kind": "session", "ts": "2026-08-27T09:00:00"},
                {"kind": "skill", "name": "camera-composition", "ts": "2026-08-01T09:00:00"},
                {"kind": "agent", "name": "cold-critic-c2", "ts": "2026-08-27T09:00:00"}]
        text = "\n".join(SU.report_lines(rows, self.ROS, {"wired_at": "2026-07-01"},
                                         today=date(2026, 8, 27)))
        self.assertIn("camera-composition (26d)", text)
        self.assertNotIn("cold-critic-c2 (", text)

    def test_the_last_use_is_the_newest_not_the_first(self):
        rows = [{"kind": "skill", "name": "x", "ts": "2026-08-01T09:00:00"},
                {"kind": "skill", "name": "x", "ts": "2026-08-27T09:00:00"},
                {"kind": "skill", "name": "x", "ts": "2026-08-10T09:00:00"}]
        _, calls, last, _, _ = SU.summarise(rows, [("skill", "x")])
        self.assertEqual(calls, 3)
        self.assertEqual(last["x"], ("2026-08-27", 3))

    def test_report_survives_an_unreadable_state_file(self):
        text = "\n".join(SU.report_lines([{"kind": "session", "ts": "2026-08-27T09:00:00"}],
                                         self.ROS, {}))
        self.assertIn("?", text)


class ExitContract(unittest.TestCase):
    def test_hook_mode_exits_0_on_garbage_stdin(self):
        import io
        real = sys.stdin
        sys.stdin = io.StringIO("not json at all")
        try:
            self.assertEqual(SU.main(["hook"]), 0)
            self.assertEqual(SU.main(["session"]), 0)
        finally:
            sys.stdin = real

    def test_an_unknown_mode_exits_2(self):
        self.assertEqual(SU.main(["wat"]), 2)


if __name__ == "__main__":
    unittest.main()
