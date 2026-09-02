"""Tests for blend_append.py — the PURE half (no Blender): which vendor file
is appended from, which object names are selected, and the refusals.

Pinned hardest: a shelf dir with no .blend RAISES naming the dir and the GLB
route as a different decision — it never falls back to the GLB silently
(the whole point of the module is what the GLB path loses)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blend_append as BA  # noqa: E402


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x")


class TestPickBlend(unittest.TestCase):
    def test_orig_beats_resolution_beats_other_and_blend1_never_counts(self):
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, "a")
            _touch(os.path.join(a, "a.2K.blend"))
            _touch(os.path.join(a, "a.4K.blend"))
            self.assertTrue(BA.pick_blend(a).endswith("a.4K.blend"))
            _touch(os.path.join(a, "a.orig.blend"))
            self.assertTrue(BA.pick_blend(a).endswith("a.orig.blend"))
            b = os.path.join(d, "b")
            _touch(os.path.join(b, "model.blend"))
            _touch(os.path.join(b, "model.blend1"))
            self.assertTrue(BA.pick_blend(b).endswith("model.blend"))
            c = os.path.join(d, "c")
            _touch(os.path.join(c, "c.0_5K.blend"))
            _touch(os.path.join(c, "c.1K.blend"))
            self.assertTrue(BA.pick_blend(c).endswith("c.1K.blend"))

    def test_glb_only_dir_refuses_by_name_and_names_the_other_route(self):
        with tempfile.TemporaryDirectory() as d:
            g = os.path.join(d, "bk_daxing")
            _touch(os.path.join(g, "bk_daxing.glb"))
            _touch(os.path.join(g, "x.blend1"))
            with self.assertRaises(BA.BlendAppendError) as cm:
                BA.pick_blend(g)
            self.assertIn("bk_daxing", str(cm.exception))
            self.assertIn("GLB", str(cm.exception))
            with self.assertRaises(BA.BlendAppendError):
                BA.pick_blend(os.path.join(d, "missing"))


class TestSelectNames(unittest.TestCase):
    def test_all_subset_missing_and_require_all(self):
        lib = ["mattress", "pillow", "Camera"]
        self.assertEqual(BA.select_names(lib), (lib, []))
        self.assertEqual(BA.select_names(lib, ["pillow", "duvet"]), (["pillow"], ["duvet"]))
        with self.assertRaises(BA.BlendAppendError):
            BA.select_names(lib, ["duvet"], require_all=True)

    def test_skip_types_are_staging_not_asset(self):
        for t in ("CAMERA", "LIGHT"):
            self.assertIn(t, BA.SKIP_TYPES)
        self.assertNotIn("MESH", BA.SKIP_TYPES)
        self.assertNotIn("CURVE", BA.SKIP_TYPES)   # hangers on the shelf are curves


if __name__ == "__main__":
    unittest.main()
