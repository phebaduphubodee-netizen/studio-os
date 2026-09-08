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


class _FakeObj:
    """A stand-in Blender Object. It exists because the mock used to model objects
    as bare STRINGS, so a test could not have caught `rotation_mode` being read or
    written at all -- and every real bpy Object has that property, so the code is
    right to assume it and the mock was wrong to omit it."""

    def __init__(self, name, mode="QUATERNION"):
        self.name = name
        self._mode = mode
        self.writes = 0

    @property
    def rotation_mode(self):
        return self._mode

    @rotation_mode.setter
    def rotation_mode(self, v):
        self._mode = v
        self.writes += 1

    def __repr__(self):
        return f"_FakeObj({self.name!r}, {self._mode})"


class TestImportFileMockBpy(unittest.TestCase):
    def _bpy(self, log, objects, ops):
        bpy = types.ModuleType("bpy")
        bpy.data = types.SimpleNamespace(objects=objects)
        bpy.ops = ops
        return bpy

    def _import(self, existing, added):
        """Run import_file against the mock, with `added` appearing on the call."""
        log, objects = [], list(existing)
        op = _Op(log, "import_scene.gltf")

        def call_and_add(**kw):
            log.append(("import_scene.gltf", kw))
            objects.extend(added)
        op.__class__ = type("X", (_Op,), {"__call__": staticmethod(call_and_add)})
        ops = _ns(import_scene={"gltf": op})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "m.glb")
            open(path, "w").close()
            sys.modules["bpy"] = self._bpy(log, objects, ops)
            try:
                return MI.import_file(path), log, path
            finally:
                del sys.modules["bpy"]

    def test_returns_only_the_new_objects(self):
        old, fresh = _FakeObj("old_obj"), _FakeObj("new_obj")
        new, log, path = self._import([old], [fresh])
        self.assertEqual([o.name for o in new], ["new_obj"])
        self.assertEqual(log[0][1]["filepath"], path)

    def test_every_imported_object_is_converted_to_xyz_rotation_mode(self):
        """`import_scene.gltf` leaves objects at QUATERNION, on which
        `rotation_euler` is a dead attribute: it reads (0,0,0) however the object
        is turned, and writing it moves nothing. Both halves were live -- the
        OFF-AXIS rung read it, and trn001_styling wrote its plan yaw into it --
        so acquired assets were never turned and never convicted of not being."""
        old = _FakeObj("old_obj", mode="QUATERNION")
        a, b = _FakeObj("a", mode="QUATERNION"), _FakeObj("b", mode="AXIS_ANGLE")
        new, _, _ = self._import([old], [a, b])
        self.assertEqual([o.rotation_mode for o in new], ["XYZ", "XYZ"])
        self.assertEqual(old.rotation_mode, "QUATERNION",
                         "objects already in the scene must not be touched")

    def test_an_object_already_in_xyz_is_not_reassigned(self):
        """Assigning the mode converts the rotation; a needless write is a needless
        chance to be wrong, and it would also hide a mock that never modelled it."""
        obj = _FakeObj("a", mode="XYZ")
        self._import([], [obj])
        self.assertEqual(obj.writes, 0)

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
