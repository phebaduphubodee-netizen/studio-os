"""Tests for model_study_probe.py — the PURE half only (no Blender): what the
batch plans to probe, the refusal of a shelf entry with nothing to probe, the
--force semantics, the bpy-side argument contract, the spawn lines per source,
and the wait-for-idle-Blender loop with a fake process table.

Pinned hardest (STUDY-D11b exam, judged by instrument):
  (1) a dir with neither .blend nor .glb is REFUSED and never yields a probe
      item — an empty dump would be a measurement of nothing;
  (2) a .blend wins over a .glb in the same dir (the vendor's file is the
      construction; the GLB is our bake of it);
  (3) the wait loop never spawns while another blender.exe is in the table,
      prints while it waits, and refuses past its ceiling instead of starting
      a second Blender.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_study_probe as P  # noqa: E402


def _touch(path, mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x")
    if mtime is not None:
        os.utime(path, (mtime, mtime))


class TestPlan(unittest.TestCase):
    def test_blend_wins_glb_only_is_glb_neither_is_refused_underscore_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(os.path.join(d, "aaaa", "aaaa.orig.blend"))
            _touch(os.path.join(d, "aaaa", "aaaa.glb"))
            _touch(os.path.join(d, "bbbb", "bbbb.glb"))
            _touch(os.path.join(d, "cccc", "SOURCE.json"))
            _touch(os.path.join(d, "dddd", "dddd.orig.blend1"))   # backup only
            _touch(os.path.join(d, "_study", "aaaa.probe.json"))
            items, refused = P.plan(d)
            self.assertEqual([(b, k) for b, k, _ in items],
                             [("aaaa", "blend"), ("bbbb", "glb")])
            self.assertTrue(items[0][2].endswith(".orig.blend"))
            self.assertEqual([r["asset"] for r in refused], ["cccc", "dddd"])
            self.assertIn("no .blend and no .glb", refused[0]["reason"])

    def test_only_filters_by_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(os.path.join(d, "bk_daxing", "bk_daxing.glb"))
            _touch(os.path.join(d, "81d895fd-1", "x.glb"))
            _touch(os.path.join(d, "zzzz", "z.blend"))
            items, refused = P.plan(d, only=["bk_", "81d895fd"])
            self.assertEqual([b for b, _, _ in items], ["81d895fd-1", "bk_daxing"])
            self.assertEqual(refused, [])


class TestNeedsProbe(unittest.TestCase):
    def test_force_missing_and_stale_dump(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "a.blend")
            out = os.path.join(d, "a.probe.json")
            _touch(src, mtime=1000)
            self.assertTrue(P.needs_probe(out, src))            # no dump
            _touch(out, mtime=2000)
            self.assertFalse(P.needs_probe(out, src))           # fresh
            self.assertTrue(P.needs_probe(out, src, force=True))
            _touch(src, mtime=3000)
            self.assertTrue(P.needs_probe(out, src))            # source newer


class TestBpyArgs(unittest.TestCase):
    def test_contract(self):
        self.assertTrue(P.parse_bpy_args([]).startswith("REFUSED"))
        self.assertEqual(P.parse_bpy_args(["o.json"]), ("o.json", None, None))
        with tempfile.TemporaryDirectory() as d:
            g = os.path.join(d, "a.glb")
            _touch(g)
            self.assertEqual(P.parse_bpy_args(["o.json", "--glb", g]), ("o.json", g, None))
            self.assertEqual(P.parse_bpy_args(["o.json", "--append", g]), ("o.json", None, g))
            self.assertIn("does not exist",
                          P.parse_bpy_args(["o.json", "--glb", os.path.join(d, "no.glb")]))
            self.assertIn("pick one", P.parse_bpy_args(["o.json", "--glb", g, "--append", g]))
        self.assertIn("unknown", P.parse_bpy_args(["o.json", "--what"]))


class TestSpawnLines(unittest.TestCase):
    def test_three_kinds_share_the_factory_autoexec_off_contract(self):
        for kind in ("blend", "glb", "append"):
            cmd = P.probe_cmd("blender.exe", "probe.py", kind, "p", "o.json")
            self.assertEqual(cmd[:6], ["blender.exe", "-b", "--factory-startup", "-Y",
                                       "--python-exit-code", "1"])
            self.assertIn("--python", cmd)
            # the exit-code flag must precede --python or Blender ignores it
            self.assertLess(cmd.index("--python-exit-code"), cmd.index("--python"))
        self.assertEqual(P.probe_cmd("b", "m", "blend", "p.blend", "o")[6], "p.blend")
        self.assertEqual(P.probe_cmd("b", "m", "glb", "p.glb", "o")[-2:], ["--glb", "p.glb"])
        self.assertEqual(P.probe_cmd("b", "m", "append", "p.blend", "o")[-2:],
                         ["--append", "p.blend"])
        with self.assertRaises(ValueError):
            P.probe_cmd("b", "m", "obj", "p", "o")


class TestWait(unittest.TestCase):
    def test_tasklist_parse(self):
        txt = ('"blender.exe","19244","Console","1","871,000 K"\n'
               '"blender.exe","2852","Console","1","10 K"\n'
               '"python.exe","1","Console","1","1 K"\n')
        self.assertEqual(P.blender_pids(txt), [19244, 2852])
        self.assertEqual(P.blender_pids("INFO: No tasks are running which match "
                                        "the specified criteria.\n"), [])

    def test_waits_while_busy_prints_and_returns_seconds(self):
        table = [[1], [1], [], []]
        slept, logged = [], []
        waited = P.wait_for_idle_blender(max_wait_s=600, poll_s=15,
                                         pids_fn=lambda: table.pop(0),
                                         sleep_fn=slept.append, log=logged.append)
        self.assertEqual(waited, 30)
        self.assertEqual(slept, [15, 15])
        self.assertTrue(logged and logged[0].startswith("WAIT blender busy"))

    def test_refuses_past_ceiling_never_starts_a_second_blender(self):
        with self.assertRaises(RuntimeError) as cm:
            P.wait_for_idle_blender(max_wait_s=30, poll_s=15, pids_fn=lambda: [7],
                                    sleep_fn=lambda s: None, log=lambda m: None)
        self.assertIn("refusing", str(cm.exception))

    def test_idle_returns_zero_without_sleeping(self):
        self.assertEqual(P.wait_for_idle_blender(pids_fn=lambda: [],
                                                 sleep_fn=lambda s: 1 / 0), 0)


class TestDumpOk(unittest.TestCase):
    def test_truncated_or_shapeless_dump_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.json")
            self.assertFalse(P.dump_ok(out))                       # absent
            with open(out, "w") as f:
                f.write('{"source": "append", "objects": [], "append": {"renamed": [[')
            self.assertFalse(P.dump_ok(out))                       # truncated
            with open(out, "w") as f:
                json.dump({"objects": []}, f)
            self.assertFalse(P.dump_ok(out))                       # no totals
            with open(out, "w") as f:
                json.dump({"objects": [], "totals": {"objects": 0}}, f)
            self.assertTrue(P.dump_ok(out))

    def test_probe_one_treats_a_truncated_dump_as_failure(self):
        # a fake "blender" that exits 0 and leaves a half-written file behind:
        # the caller must still say FAIL (Blender's real default is exit 0 on
        # a script traceback; the flag fixes the code, this fixes the reading)
        class Done:
            returncode, stdout, stderr = 0, "Traceback …", ""

        def fake_run(cmd, **kw):
            with open(cmd[cmd.index("--") + 1], "w") as f:
                f.write('{"objects": [')
            return Done()
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.json")
            src = os.path.join(d, "a.glb")
            _touch(src)
            rc = P.probe_one(src, out, blender="blender.exe", wait=False,
                             _run=fake_run)
            self.assertEqual(rc, 1)


class TestProbeOneRefusals(unittest.TestCase):
    def test_missing_or_wrong_kind_refuses_with_2_and_no_dump(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.json")
            self.assertEqual(P.probe_one(os.path.join(d, "nope.blend"), out,
                                         blender="blender.exe", wait=False), 2)
            self.assertFalse(os.path.exists(out))
            obj = os.path.join(d, "a.obj")
            _touch(obj)
            self.assertEqual(P.probe_one(obj, out, blender="blender.exe", wait=False), 2)
            self.assertFalse(os.path.exists(out))
            g = os.path.join(d, "a.glb")
            _touch(g)
            self.assertEqual(P.probe_one(g, out, kind="append", blender="blender.exe",
                                         wait=False), 2)
            self.assertFalse(os.path.exists(out))


class TestStatsSeparatesSources(unittest.TestCase):
    def test_glb_import_dumps_do_not_enter_the_construction_table(self):
        with tempfile.TemporaryDirectory() as d:
            cache = os.path.join(d, "cache")
            study = os.path.join(cache, "_study")
            os.makedirs(study)
            for aid, src, sub in (("aaaa1111", "blend", [{"type": "SUBSURF", "levels": 1,
                                                          "render_levels": 2}]),
                                  ("bbbb2222", "glb-import", [])):
                os.makedirs(os.path.join(cache, aid))
                with open(os.path.join(cache, aid, aid + ".scale.json"), "w") as f:
                    json.dump({"class": "whole_bed"}, f)
                doc = {"source": src, "objects": [{
                    "name": "bed", "type": "MESH", "modifiers": sub,
                    "mesh": {"verts": 1000, "polys": 900, "quads": 900, "tris": 0,
                             "ngons": 0, "area_m2": 2.0, "verts_per_m2": 500.0}}],
                    "materials": [{"name": "m", "node_hist": {"BSDF_PRINCIPLED": 1},
                                   "principled": {"Sheen Weight": 0.2}}],
                    "images": [], "totals": {"objects": 1, "meshes": 1, "curves": 0,
                                             "verts": 1000, "materials": 1, "images": 0}}
                with open(os.path.join(study, aid + ".probe.json"), "w") as f:
                    json.dump(doc, f)
            out = os.path.join(d, "stats.json")
            P.stats(cache, out=out)
            with open(out, encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["dumps_by_source"], {"blend": 1, "glb-import": 1})
            self.assertEqual(s["classes"]["whole_bed"]["assets"], ["aaaa1111"])
            self.assertEqual(s["classes"]["whole_bed"]["subsurf_share"]["median"], 1.0)
            self.assertEqual(s["classes_glb_import"]["whole_bed"]["assets"], ["bbbb2222"])
            self.assertNotIn("subsurf_share", s["classes_glb_import"]["whole_bed"])
            self.assertNotIn("mat_sheen_set_share", s["classes_glb_import"]["whole_bed"])


if __name__ == "__main__":
    unittest.main()
