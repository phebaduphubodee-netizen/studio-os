"""Tests for mesh_import — the one extension -> importer dispatch.

No Blender: the pure half (`candidates`, `resolve`, `model_files`) is tested
directly, and the bpy edge (`import_file`) against a mock `bpy` injected into
sys.modules. The property pinned hardest is FAIL CLOSED: an unknown extension
or a missing operator must RAISE, because a dispatch that guesses is how a
model silently fails to arrive and prints like an empty import.
"""
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesh_import as MI  # noqa: E402


class _Op:
    """A bpy.ops-like operator: get_rna_type() exists = registered."""

    def __init__(self, log=None, name=""):
        self._log = log if log is not None else []
        self._name = name

    def get_rna_type(self):
        return object()

    def __call__(self, **kw):
        self._log.append((self._name, kw))


class _MissingOp:
    """Registered-looking attribute whose RNA probe raises (unknown op)."""

    def get_rna_type(self):
        raise KeyError("unknown operator")


def _ns(**submods):
    ns = types.SimpleNamespace()
    for name, ops in submods.items():
        setattr(ns, name, types.SimpleNamespace(**ops))
    return ns


class TestRouting(unittest.TestCase):
    def test_glb_and_gltf_route_to_the_gltf_importer(self):
        for p in ("bed.glb", "bed.gltf", "BED.GLB"):
            self.assertEqual(MI.candidates(p)[0][0], "import_scene.gltf")

    def test_obj_prefers_the_core_importer_then_legacy(self):
        self.assertEqual([op for op, _ in MI.candidates("chair.obj")],
                         ["wm.obj_import", "import_scene.obj"])

    def test_fbx_stl_dae(self):
        self.assertEqual(MI.candidates("a.fbx")[0][0], "import_scene.fbx")
        self.assertEqual([op for op, _ in MI.candidates("a.stl")],
                         ["wm.stl_import", "import_mesh.stl"])
        self.assertEqual(MI.candidates("a.dae")[0][0], "wm.collada_import")

    def test_kwargs_carry_the_filepath(self):
        _op, kw = MI.candidates("dir/lamp.glb")[0]
        self.assertEqual(kw, {"filepath": "dir/lamp.glb"})


class TestFailClosed(unittest.TestCase):
    def test_unknown_extension_raises_and_names_it(self):
        with self.assertRaises(MI.MeshImportError) as cm:
            MI.candidates("model.xyz")
        self.assertIn(".xyz", str(cm.exception))
        self.assertIn("refused", str(cm.exception))

    def test_no_extension_raises(self):
        with self.assertRaises(MI.MeshImportError):
            MI.candidates("model")

    def test_skp_is_refused_by_name_with_its_route(self):
        with self.assertRaises(MI.MeshImportError) as cm:
            MI.candidates("house.skp")
        self.assertIn("SketchUp", str(cm.exception))

    def test_blend_is_refused_by_name_with_libraries_load(self):
        with self.assertRaises(MI.MeshImportError) as cm:
            MI.candidates("scene.blend")
        self.assertIn("libraries.load", str(cm.exception))


class TestResolve(unittest.TestCase):
    def test_first_available_candidate_wins(self):
        ns = _ns(wm={"obj_import": _Op()}, import_scene={"obj": _Op()})
        op_path, _op, kw = MI.resolve("a.obj", ns)
        self.assertEqual(op_path, "wm.obj_import")
        self.assertEqual(kw["filepath"], "a.obj")

    def test_falls_through_to_the_legacy_op(self):
        ns = _ns(import_scene={"obj": _Op()})     # no wm.obj_import at all
        op_path, _op, _kw = MI.resolve("a.obj", ns)
        self.assertEqual(op_path, "import_scene.obj")

    def test_an_op_whose_rna_probe_raises_is_not_available(self):
        ns = _ns(wm={"obj_import": _MissingOp()}, import_scene={"obj": _Op()})
        op_path, _op, _kw = MI.resolve("a.obj", ns)
        self.assertEqual(op_path, "import_scene.obj")

    def test_no_candidate_available_raises_naming_all_tried(self):
        ns = _ns()
        with self.assertRaises(MI.MeshImportError) as cm:
            MI.resolve("a.obj", ns)
        msg = str(cm.exception)
        self.assertIn("wm.obj_import", msg)
        self.assertIn("import_scene.obj", msg)
        self.assertIn("NOT imported", msg)

    def test_unknown_extension_raises_before_touching_the_namespace(self):
        with self.assertRaises(MI.MeshImportError):
            MI.resolve("a.xyz", None)


class TestModelFiles(unittest.TestCase):
    def test_lists_supported_best_format_first_and_skips_sidecars(self):
        with tempfile.TemporaryDirectory() as tmp:
            for n in ("b.obj", "a.glb", "a.scale.json", "SOURCE.json",
                      "note.txt", "c.fbx", "z.gltf"):
                open(os.path.join(tmp, n), "w").close()
            got = MI.model_files(tmp)
        self.assertEqual(got, ["a.glb", "z.gltf", "b.obj", "c.fbx"])

    def test_missing_dir_is_an_empty_list(self):
        self.assertEqual(MI.model_files(os.path.join("no", "such", "dir")), [])


class TestImportFileMockBpy(unittest.TestCase):
    def _bpy(self, log, objects, ops):
        bpy = types.ModuleType("bpy")
        bpy.data = types.SimpleNamespace(objects=objects)
        bpy.ops = ops
        return bpy

    def test_returns_only_the_new_objects(self):
        log, objects = [], ["old_obj"]
        op = _Op(log, "import_scene.gltf")

        def call_and_add(**kw):
            log.append(("import_scene.gltf", kw))
            objects.append("new_obj")
        op.__class__ = type("X", (_Op,), {"__call__": staticmethod(call_and_add)})
        ops = _ns(import_scene={"gltf": op})
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "m.glb")
            open(p, "w").close()
            sys.modules["bpy"] = self._bpy(log, objects, ops)
            try:
                new = MI.import_file(p)
            finally:
                del sys.modules["bpy"]
        self.assertEqual(new, ["new_obj"])
        self.assertEqual(log[0][1]["filepath"], p)

    def test_missing_file_raises_before_any_operator_runs(self):
        log = []
        ops = _ns(import_scene={"gltf": _Op(log, "gltf")})
        sys.modules["bpy"] = self._bpy(log, [], ops)
        try:
            with self.assertRaises(MI.MeshImportError):
                MI.import_file(os.path.join("no", "such", "m.glb"))
        finally:
            del sys.modules["bpy"]
        self.assertEqual(log, [])

    def test_unknown_extension_raises_even_with_bpy_present(self):
        log = []
        ops = _ns(import_scene={"gltf": _Op(log, "gltf")})
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "m.skp")
            open(p, "w").close()
            sys.modules["bpy"] = self._bpy(log, [], ops)
            try:
                with self.assertRaises(MI.MeshImportError):
                    MI.import_file(p)
            finally:
                del sys.modules["bpy"]
        self.assertEqual(log, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
