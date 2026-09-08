"""Tests for export_bake_control.py — the PURE half (no Blender).

Pinned hardest: the export verdict is EXACT per object (legacy == viewport
prediction AND current == render prediction) — a control that only asked
"did the count rise" would pass a fix that raised to the wrong level; and the
legacy script is the current script minus the raise, nothing else."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blenderkit as BK  # noqa: E402
import export_bake_control as C  # noqa: E402


def _native(objs):
    return {"objects": [{"name": n, "type": "MESH", "modifiers": mods,
                         "mesh": {"polys": q + t + g, "quads": q, "tris": t,
                                  "ngons": g}} for n, mods, q, t, g in objs],
            "materials": [], "totals": {}}


def _glb(tris):
    return {"objects": [{"name": n, "type": "MESH",
                         "mesh": {"polys": v, "tris": v, "quads": 0, "ngons": 0}}
                        for n, v in tris.items()], "materials": [], "totals": {}}


SUB = [{"type": "SUBSURF", "levels": 1, "render_levels": 2}]


class TestLegacyScript(unittest.TestCase):
    def test_legacy_is_current_minus_the_raise(self):
        for line in C.LEGACY_EXPORT_SCRIPT.splitlines():
            self.assertIn(line, BK.EXPORT_SCRIPT.splitlines())
        self.assertNotIn("render_levels", C.LEGACY_EXPORT_SCRIPT)
        self.assertIn("m.levels = m.render_levels", BK.EXPORT_SCRIPT)


class TestPredict(unittest.TestCase):
    def test_catmull_clark_counts_and_refusals(self):
        n = _native([("q", SUB, 368, 0, 0),          # pure quads, 1 -> 2
                     ("qt", SUB, 1088, 128, 0),      # quads + tris
                     ("ng", SUB, 768, 0, 4),         # n-gons: n not dumped
                     ("flat", [], 12, 3, 0),         # no subsurf, level 0
                     ("flatng", [], 12, 0, 1),
                     ("nodes", [{"type": "NODES"}], 40, 0, 0),
                     ("stack", SUB + SUB, 4, 0, 0)])
        p = C.predict_tris(n)
        self.assertEqual(p["predictable"]["q"],
                         {"levels": 1, "render_levels": 2, "base_polys": 368,
                          "viewport_tris": 2 * 368 * 4, "render_tris": 2 * 368 * 16})
        self.assertEqual(p["predictable"]["qt"]["viewport_tris"],
                         2 * (4 * 1088 + 3 * 128))
        self.assertEqual(p["predictable"]["qt"]["render_tris"],
                         2 * (4 * 1088 + 3 * 128) * 4)
        self.assertEqual(p["predictable"]["flat"],
                         {"levels": 0, "render_levels": 0, "base_polys": 15,
                          "viewport_tris": 27, "render_tris": 27})
        self.assertIn("n-gons", p["unpredictable"]["ng"])
        self.assertIn("n-gons", p["unpredictable"]["flatng"])
        self.assertIn("NODES", p["unpredictable"]["nodes"])
        self.assertIn("stacked", p["unpredictable"]["stack"])


class TestExportVerdict(unittest.TestCase):
    def test_exact_match_passes_and_wrong_level_fails(self):
        n = _native([("q", SUB, 100, 0, 0), ("flat", [], 10, 0, 0)])
        legacy = _glb({"q": 800, "flat": 20})
        current = _glb({"q": 3200, "flat": 20})
        v = C.export_verdict(n, legacy, current)
        self.assertTrue(v["pass"])
        self.assertEqual(v["objects_checked"], 2)
        self.assertEqual(v["objects_raised"], 1)
        self.assertEqual(v["total_polys"]["ratio_current_over_legacy"],
                         round(3220 / 820, 3))
        # "rose" but only doubled: level raised to the wrong number -> FAIL
        wrong = _glb({"q": 1600, "flat": 20})
        v2 = C.export_verdict(n, legacy, wrong)
        self.assertFalse(v2["pass"])
        self.assertEqual(v2["failed_objects"], ["q"])
        # importer renamed the object -> unmatched, never guessed -> FAIL
        v3 = C.export_verdict(n, legacy, _glb({"q.001": 3200, "flat": 20}))
        self.assertFalse(v3["pass"])
        self.assertEqual(v3["unmatched_objects"], ["q"])
        # nothing had a level to raise -> the control proves nothing -> FAIL
        v4 = C.export_verdict(_native([("flat", [], 10, 0, 0)]),
                              _glb({"flat": 20}), _glb({"flat": 20}))
        self.assertFalse(v4["pass"])


class TestAppendVerdict(unittest.TestCase):
    def _dump(self, mods, node_types, images, mats, append=None):
        d = {"objects": [{"name": "a", "type": "MESH",
                          "modifiers": [{"type": t} for t in mods]}],
             "materials": [{"name": "m", "node_hist": {t: 1 for t in node_types}}],
             "totals": {"images": images, "materials": mats}}
        if append is not None:
            d["append"] = append
        return d

    def test_append_keeps_glb_loses(self):
        nat = self._dump(["SUBSURF"], ["BSDF_PRINCIPLED", "VALTORGB", "BUMP"], 13, 7)
        app = self._dump(["SUBSURF"], ["BSDF_PRINCIPLED", "VALTORGB", "BUMP"], 13, 7,
                         append={"appended": ["a"], "skipped": [], "missing": [],
                                 "renamed": []})
        glb = self._dump([], ["BSDF_PRINCIPLED", "TEX_IMAGE", "NORMAL_MAP"], 13, 7)
        v = C.append_verdict(nat, app, glb)
        self.assertTrue(v["pass"])
        self.assertEqual(v["node_types"]["lost_by_glb"], ["BUMP", "VALTORGB"])
        self.assertEqual(v["node_types"]["added_by_glb_importer"],
                         ["NORMAL_MAP", "TEX_IMAGE"])
        # append that dropped the modifier -> FAIL
        app2 = self._dump([], ["BSDF_PRINCIPLED", "VALTORGB", "BUMP"], 13, 7)
        self.assertFalse(C.append_verdict(nat, app2, glb)["pass"])
        # GLB that lost nothing -> the route buys nothing -> FAIL (honest)
        self.assertFalse(C.append_verdict(nat, app, nat)["pass"])


class TestNegativeVerdict(unittest.TestCase):
    def test_refused_and_no_dump(self):
        ref = [{"asset": "zzzz-empty", "reason": "no .blend and no .glb"}]
        self.assertTrue(C.negative_verdict(ref, 2, False, 2, False)["pass"])
        self.assertFalse(C.negative_verdict([], 2, False, 2, False)["pass"])
        self.assertFalse(C.negative_verdict(ref, 0, True, 2, False)["pass"])
        self.assertFalse(C.negative_verdict(ref, 2, False, 0, True)["pass"])


if __name__ == "__main__":
    unittest.main()
