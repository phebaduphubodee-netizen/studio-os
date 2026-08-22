"""mesh_import.py — ONE import dispatch for external geometry, chosen by
extension, failing closed on anything it does not know.

WHY IT EXISTS (docs/strategy.md 2026-08-15, re-ordered by
ORD-2026-08-22-process-review-actions item 3): the repo's own audit found every
importer call in the tree was `bpy.ops.import_scene.gltf` — glTF-only out of all
the formats Blender ships importers for — so every non-glTF mesh a source offered
(FurniMesh ships GLB *and* OBJ; Dimensiva ships .blend; XOIO ships OBJ) was
unreachable not because of licences or money but because of us. This module is
the one place the extension -> importer choice lives, so widening the pipe is an
edit here and not an edit per caller (the same one-rule-many-callers law as
`bedcloth_fit`).

LAYER LAW SPLIT (pipeline/CLAUDE.md): the CHOICE is pure python — `candidates()`
and `resolve()` import no bpy and are tested without Blender
(test_mesh_import.py). Only `import_file()` touches `bpy`, and it imports it
inside the function so this module stays loadable under plain `python`.

FAIL CLOSED, in both places it can fail:
  * an UNKNOWN EXTENSION raises `MeshImportError` — never guesses an importer.
    "could not run" must never print like "looked and it was fine" (R11's exit-2
    law, applied to ingest). `.skp` and `.blend` raise with their actual route
    named, because both are real formats on our sources and each has a real
    answer that is not this module.
  * a KNOWN extension whose operator this Blender build does not have raises,
    naming every candidate op it tried — an importer that silently does nothing
    would surface three rungs later as "import produced no meshes".

`bpy.ops` NOTE: these are the headless-safe IMPORT ops (the same class as the
`import_scene.gltf` calls this module replaces — pipeline/CLAUDE.md scopes the
ops ban to GEOMETRY ops). Candidate order per extension is newest-first: Blender
4.x moved OBJ/STL to core C++ ops (`wm.obj_import`, `wm.stl_import`) and kept
the legacy add-on ops in older builds, so both are listed and `resolve()` takes
the first one that exists in the running Blender.
"""
import os

# ------------------------------------------------------------------ pure part --

class MeshImportError(ValueError):
    """A refusal, never a guess: unknown extension, or no importer available."""


# extension -> ordered candidate operator paths (dotted, under bpy.ops).
# First entry that exists in the running Blender wins (resolve()).
OPS_BY_EXT = {
    ".glb":  ("import_scene.gltf",),
    ".gltf": ("import_scene.gltf",),
    ".obj":  ("wm.obj_import", "import_scene.obj"),
    ".fbx":  ("import_scene.fbx",),
    ".stl":  ("wm.stl_import", "import_mesh.stl"),
    ".dae":  ("wm.collada_import",),
}

# add-on module behind an op, for the enable-then-retry fallback build_room.py
# already relies on for glTF under --factory-startup (pipeline/CLAUDE.md names
# `preferences.addon_enable` among the headless-safe ops in use).
ADDON_FOR_OP = {
    "import_scene.gltf": "io_scene_gltf2",
    "import_scene.fbx": "io_scene_fbx",
    "import_scene.obj": "io_scene_obj",
    "import_mesh.stl": "io_mesh_stl",
}

# formats we KNOW and refuse BY NAME, with the actual route stated — a named
# refusal is actionable, "unknown extension" is not.
REFUSED_BY_NAME = {
    ".skp": "SketchUp .skp has no stock Blender importer — the one-way ingest "
            "route is the open-source SketchUp Importer add-on or a GLB/DAE "
            "export from SketchUp itself (pipeline/CLAUDE.md, interop law)",
    ".blend": "a .blend is not imported through an operator — append its "
              "objects with bpy.data.libraries.load (pipeline/CLAUDE.md, "
              "Blender build law)",
}

# listing preference for a cache dir that may hold several formats of the same
# model: glb first (the shelf's native format, and the one every existing bench
# measured), then the descending order of how faithfully each carries materials.
EXT_PREFERENCE = (".glb", ".gltf", ".obj", ".fbx", ".dae", ".stl")


def ext_of(path):
    return os.path.splitext(str(path))[1].lower()


def candidates(path):
    """[(op_path, kwargs)] for this file, or raise MeshImportError. PURE.

    Every importer listed takes `filepath=`; kwargs stay per-candidate so a
    future op that needs more can carry it without touching callers."""
    ext = ext_of(path)
    if ext in REFUSED_BY_NAME:
        raise MeshImportError(f"{os.path.basename(str(path))}: {REFUSED_BY_NAME[ext]}")
    ops = OPS_BY_EXT.get(ext)
    if not ops:
        raise MeshImportError(
            f"{os.path.basename(str(path))}: no importer for '{ext or '(no extension)'}'"
            f" — refused rather than guessed. Known: {', '.join(sorted(OPS_BY_EXT))}")
    return [(op, {"filepath": str(path)}) for op in ops]


def _walk(ns, op_path):
    """The op object at a dotted path under a bpy.ops-like namespace, or None."""
    cur = ns
    for part in op_path.split("."):
        cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


def op_exists(op):
    """Whether an op wrapper is a REAL registered operator.

    `bpy.ops.x.y` attribute access never fails — the wrapper is built lazily and
    only errors on call — so existence is asked of the RNA type, which raises
    for an op no build registered. A mock namespace in tests satisfies the same
    contract (get_rna_type present = exists, raising or absent = not)."""
    if op is None:
        return False
    probe = getattr(op, "get_rna_type", None)
    if probe is None:
        return False
    try:
        probe()
    except Exception:                                   # noqa: BLE001
        return False
    return True


def resolve(path, ops_ns, exists=op_exists):
    """(op_path, op_callable, kwargs) — first candidate that exists, or raise.

    PURE against the namespace it is handed: production passes `bpy.ops`,
    tests pass a mock. Raises MeshImportError naming every candidate tried,
    because 'no importer in this build' must be a loud stop, never a no-op."""
    tried = []
    for op_path, kwargs in candidates(path):
        op = _walk(ops_ns, op_path)
        if exists(op):
            return op_path, op, kwargs
        tried.append(op_path)
    raise MeshImportError(
        f"{os.path.basename(str(path))}: none of the candidate importers exist in "
        f"this Blender build ({', '.join(tried)}) — the file was NOT imported")


def model_files(dirpath, exts=EXT_PREFERENCE):
    """Importable model files in `dirpath`, best format first. PURE-ish (one
    os.listdir). Preference is by EXT_PREFERENCE then name, so a folder holding
    the same model as .glb and .obj keeps auditioning the .glb the benches have
    always measured."""
    try:
        names = sorted(os.listdir(dirpath))
    except OSError:
        return []
    rank = {e: i for i, e in enumerate(exts)}
    hits = [n for n in names if ext_of(n) in rank]
    return sorted(hits, key=lambda n: (rank[ext_of(n)], n))


# ------------------------------------------------------------------ bpy edge --

def import_file(path):
    """Import one model file into the open scene; return the NEW objects.

    The only function here that touches bpy. On a missing glTF/FBX add-on it
    tries the enable-then-retry fallback build_room already uses, then imports.
    Raises MeshImportError (unknown ext / no importer) or whatever the operator
    itself raises — callers that tolerate a bad candidate already catch."""
    import bpy

    if not os.path.exists(path):
        raise MeshImportError(f"{path}: file does not exist — nothing was imported")
    try:
        op_path, op, kwargs = resolve(path, bpy.ops)
    except MeshImportError:
        # enable-then-retry for add-on-backed importers (headless-safe; the
        # same call build_room.py makes before its own glTF ingest)
        enabled = False
        for cand, _kw in candidates(path):
            mod = ADDON_FOR_OP.get(cand)
            if mod:
                try:
                    bpy.ops.preferences.addon_enable(module=mod)
                    enabled = True
                except Exception:                       # noqa: BLE001
                    pass
        if not enabled:
            raise
        op_path, op, kwargs = resolve(path, bpy.ops)
    before = set(bpy.data.objects)
    op(**kwargs)
    return [o for o in bpy.data.objects if o not in before]
