"""blend_append.py — the route a hero asset takes from its native .blend into
a build: bpy.data.libraries.load(link=False), never an operator, never a GLB.

WHY (STUDY-D11b, 2026-09-02 — the day-10 study's TOP-10 rules 3 and 4):
  * `blenderkit.export_glb` bakes every modifier through the VIEWPORT depsgraph,
    so a SUBSURF at viewport 1 / render 2 lands in the GLB with a quarter of the
    faces the vendor renders (97 of 142 SUBSURF rows on the shelf carry
    levels < render_levels). export_glb is fixed to raise the level first, but a
    bake is still a bake: the frame gets a frozen mesh at ONE level.
  * The GLB round-trip drops what glTF cannot carry: procedural chains, ColorRamp
    tone curves, Bump-from-height, displacement wiring, sheen — 19 of 39 organic
    materials on the shelf lose their tree entirely (day-10 INDEX §TOP-10 rule 4).
  * `mesh_import.py` already REFUSES `.blend` by name and points here
    (REFUSED_BY_NAME['.blend']: "append its objects with bpy.data.libraries.load").
    Until today that route existed as a sentence in a refusal message and nowhere
    as code — the queue-with-no-consumer shape, one level down.

WHAT IT KEEPS that the GLB path loses, and the probe can prove with numbers
(model_study_probe.py --append vs --glb on the same asset, `source` field):
the vendor's modifier stack alive (subsurf evaluated at render_levels by Cycles
itself), the full node tree, packed images, shape keys, vertex groups, the
vendor's rotation mode. What it COSTS: the .blend must stay on disk (the
disk-retention law already says never delete a .orig.blend for this reason),
and third-party datablocks enter our file by name — name collisions are
Blender's `.001` suffixing, reported here, never silently merged.

LAYER LAW SPLIT (pipeline/CLAUDE.md): `pick_blend`, `select_names`, `SKIP_TYPES`
and the report shape are pure python (test_blend_append.py, no Blender). Only
`append_objects` touches bpy, importing it inside the function.

FAIL CLOSED: an asset dir with no .blend raises BlendAppendError naming the dir
(the GLB path is a different decision, not a fallback this module makes); a
requested object name the library does not hold is reported in `missing`, and
`require_all=True` raises on it.

NOT YET WIRED INTO build_room.py: that file is owned by a render lane on
2026-09-02 (P2r-34, parallel session). The integration point is the glTF asset
import at build_room.py:12007 (`bpy.ops.import_scene.gltf(filepath=path)`); a
spec row would name `"blend": "<asset>.orig.blend"` and land here. Recorded as
the restart_by of STUDY-D11b, not as done.
"""
import glob
import os
import re

# object types that are the vendor's staging, never the asset: a bought bed
# arriving with its own key light would re-light our room from inside a prop
SKIP_TYPES = ("CAMERA", "LIGHT", "SPEAKER", "LIGHT_PROBE")

_RES = re.compile(r"\.(\d+(?:_\d+)?)K\.blend$", re.IGNORECASE)


class BlendAppendError(ValueError):
    """A refusal, never a guess."""


def pick_blend(asset_dir):
    """PURE. The vendor file to append from, by preference: `.orig.blend`
    (full-resolution textures) > the highest `.<N>K.blend` > any other .blend.
    `.blend1` backups never count. Raises when the dir holds none."""
    if not os.path.isdir(asset_dir):
        raise BlendAppendError(f"{asset_dir}: not a directory")
    cands = [p for p in sorted(glob.glob(os.path.join(asset_dir, "*.blend")))
             if not p.endswith(".blend1")]
    if not cands:
        raise BlendAppendError(
            f"{os.path.basename(os.path.normpath(asset_dir))}: no .blend on the "
            f"shelf — the append route needs the vendor file; a GLB-only entry "
            f"is a different decision (GLB import), not a fallback taken here")
    orig = [p for p in cands if p.lower().endswith(".orig.blend")]
    if orig:
        return orig[0]

    def _res(p):
        m = _RES.search(p)
        return float(m.group(1).replace("_", ".")) if m else -1.0
    cands.sort(key=_res, reverse=True)
    return cands[0]


def select_names(available, names=None, require_all=False):
    """PURE. Which library object names to append: all of `available` when
    `names` is None, else the intersection in library order; `missing` lists
    requested names the library lacks. Raises on missing when require_all."""
    available = list(available)
    if names is None:
        return available, []
    want = set(names)
    chosen = [n for n in available if n in want]
    missing = [n for n in names if n not in set(available)]
    if missing and require_all:
        raise BlendAppendError(f"library lacks {missing}")
    return chosen, missing


def append_objects(blend_path, into=None, names=None, require_all=False,
                   skip_types=SKIP_TYPES):
    """bpy: append objects from `blend_path` (link=False = a local copy) and
    link them into `into` (a Collection; default the scene's root collection).
    Returns the report dict:
      {"blend", "appended": [names], "skipped": [[name, type]], "missing",
       "materials": n (use_nodes only), "images": n, "renamed": [[wanted, got]]}
    Never saves. Never touches the source file (link=False reads it once).
    """
    import bpy
    # absolute, always: Blender resolves a relative library path against ITS
    # notion of the current dir, not Python's — the first live run passed
    # os.path.isfile on "assets/shared/…" and libraries.load then tried to open
    # "C:\assets\shared\…" and failed
    blend_path = os.path.abspath(blend_path)
    if not os.path.isfile(blend_path):
        raise BlendAppendError(f"{blend_path}: no such file")
    before_mats = {m.name for m in bpy.data.materials}
    before_imgs = {i.name for i in bpy.data.images}
    with bpy.data.libraries.load(blend_path, link=False) as (src, dst):
        chosen, missing = select_names(src.objects, names, require_all)
        # a COPY: Blender replaces the assigned list's items IN PLACE with the
        # loaded datablocks on exit, so assigning `chosen` itself turned every
        # `wanted` name below into an Object (first live run: the dump died in
        # json.dump on "Object is not JSON serializable")
        dst.objects = list(chosen)
    coll = into or bpy.context.scene.collection
    appended, skipped, renamed = [], [], []
    for wanted, ob in zip(chosen, dst.objects):
        if ob is None:
            missing.append(wanted)
            continue
        if ob.type in skip_types:
            skipped.append([ob.name, ob.type])
            bpy.data.objects.remove(ob, do_unlink=True)
            continue
        if ob.name != wanted:
            renamed.append([wanted, ob.name])
        coll.objects.link(ob)
        appended.append(ob.name)
    new_mats = [m for m in bpy.data.materials
                if m.name not in before_mats and m.use_nodes]
    new_imgs = [i for i in bpy.data.images if i.name not in before_imgs]
    return {"blend": blend_path, "appended": appended, "skipped": skipped,
            "missing": missing, "materials": len(new_mats),
            "images": len(new_imgs), "renamed": renamed}
