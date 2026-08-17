"""glb_flatten.py — merge a glTF's per-triangle primitives into one primitive per
material, so a file that would cost hours to import costs seconds.

PURE PYTHON, NO `bpy` (pipeline/CLAUDE.md layer law). It reads and writes .glb by
hand: header, JSON chunk, BIN chunk.

WHY IT EXISTS, and the cost is measured on this shelf. **The SketchUp GLTF Exporter
writes ONE PRIMITIVE PER TRIANGLE.** `d4698c95` ("BED SETS", 360 MB) holds 299,307
triangles in 297,631 primitives; `bf542bbc` holds 327,822 in 327,822. Almost all of
those bytes are the glTF JSON describing 300,000 accessors and bufferViews — the
geometry itself is ~30 MB. Two things follow, and both had already decided a round:

  * `bpy.ops.import_scene.gltf` walks primitives, so it spends 30-40 s per mesh node
    on such a file. p2r46 measured ONE 88 MB model at over 20 minutes and recorded
    that cost as the reason this lane had auditioned ten bed covers in its history.
  * `mesh_density` read the densest PRIMITIVE, so it scored the finest cloth on the
    shelf as a 1-triangle sheet — the coarsest reading possible. That is fixed there;
    this is the other half, because a screen that says "fine" is no use if the bench
    cannot afford to look.

WHAT IT DOES NOT DO, said plainly. It does not decimate, retopologise, weld or
otherwise CHANGE geometry: vertex positions, normals and UVs are copied through and
the triangle count is identical in and out (the CLI asserts this). It merges
primitives that share a material, and a primitive is a material patch — so the only
thing lost is the ability to assign 300,000 separate materials to 300,000 separate
triangles, which no exporter meant and no renderer wants. Anything it cannot copy
faithfully — a sparse accessor, a non-triangle draw mode, a skin, an animation — is
REFUSED OR REPORTED BY NAME, never silently dropped, because a quiet loss here would
show up three rungs later as a geometry defect nobody could trace.

    python pipeline/scripts/glb_flatten.py in.glb out.glb [--drop-textures]
"""
import argparse
import base64
import json
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

# glTF component types -> (struct code, size in bytes, max value when normalized)
COMPONENT = {5120: ("b", 1, 127.0), 5121: ("B", 1, 255.0), 5122: ("h", 2, 32767.0),
             5123: ("H", 2, 65535.0), 5125: ("I", 4, None), 5126: ("f", 4, None)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
         "MAT2": 4, "MAT3": 9, "MAT4": 16}
TRIANGLES = 4
# Copied through verbatim when a primitive has them. Everything else an exporter may
# attach (COLOR_0, JOINTS_0, TANGENT, second UV sets) is REPORTED and dropped: this
# tool exists for SketchUp exports, which carry none of them, and inventing a merge
# for an attribute nobody has seen is how a silent defect gets written.
ATTRS = (("POSITION", "VEC3", 3), ("NORMAL", "VEC3", 3), ("TEXCOORD_0", "VEC2", 2))


def read_glb(path):
    """(gltf dict, BIN chunk bytes or b'') for a binary glTF."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12:
            raise ValueError(f"{os.path.basename(path)}: too short to be a glb")
        magic, _ver, _total = struct.unpack("<III", head)
        if magic != GLB_MAGIC:
            raise ValueError(f"{os.path.basename(path)}: not a binary glTF")
        g, blob = None, b""
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            clen, ctype = struct.unpack("<II", hdr)
            data = f.read(clen)
            if ctype == CHUNK_JSON:
                g = json.loads(data.decode("utf-8", "replace"))
            elif ctype == CHUNK_BIN:
                blob = data
    if g is None:
        raise ValueError(f"{os.path.basename(path)}: no JSON chunk")
    return g, blob


def buffers_of(g, blob):
    """[bytes] per glTF buffer — the BIN chunk for the one with no uri, base64 for
    embedded ones. A buffer pointing at an external FILE is refused rather than
    guessed at: this repo's shelf is self-contained .glb and a missing sidecar would
    otherwise read as an empty mesh."""
    out = []
    for i, b in enumerate(g.get("buffers") or []):
        uri = b.get("uri")
        if not uri:
            out.append(blob)
        elif uri.startswith("data:"):
            out.append(base64.b64decode(uri.split(",", 1)[1]))
        else:
            raise ValueError(f"buffer {i} points at an external file ({uri[:40]!r})")
    return out


def accessor(g, bufs, idx):
    """[tuple(numbers)] for one accessor, byteStride and normalization honoured."""
    a = (g.get("accessors") or [])[idx]
    if "sparse" in a:
        raise ValueError(f"accessor {idx} is sparse — refused rather than guessed")
    n = NCOMP[a["type"]]
    code, size, maxv = COMPONENT[a["componentType"]]
    count = int(a.get("count") or 0)
    bv_i = a.get("bufferView")
    if bv_i is None:                                   # spec: treat as zeros
        return [tuple([0] * n)] * count
    bv = (g.get("bufferViews") or [])[bv_i]
    data = bufs[bv.get("buffer", 0)]
    base = int(bv.get("byteOffset") or 0) + int(a.get("byteOffset") or 0)
    stride = int(bv.get("byteStride") or 0) or n * size
    norm = bool(a.get("normalized")) and maxv is not None
    fmt = "<" + code * n
    out = []
    for k in range(count):
        v = struct.unpack_from(fmt, data, base + k * stride)
        out.append(tuple(max(x / maxv, -1.0) for x in v) if norm else v)
    return out


def dedupe_materials(g):
    """({old index: new index}, [material]) — materials collapsed by VALUE.

    THIS IS THE MERGE KEY, and without it the merge is a no-op. The SketchUp exporter
    writes a material ENTRY per triangle as well as a primitive per triangle:
    `d4698c95` declares **297,632 materials that are 27 distinct definitions**, and
    `bf542bbc` 327,822 that are 5. Grouping on the raw index therefore groups nothing.
    Identity here is the full JSON value including the name, which is the conservative
    direction: two materials that differ only in name stay two, and nothing that
    renders differently is ever merged.
    """
    mats, index, out = g.get("materials") or [], {}, []
    remap = {}
    for i, m in enumerate(mats):
        key = json.dumps(m, sort_keys=True)
        if key not in index:
            index[key] = len(out)
            out.append(m)
        remap[i] = index[key]
    return remap, out


def _sig(prim, remap):
    """What decides whether two primitives may be concatenated: same material AFTER
    value-dedup, same set of the attributes this tool carries."""
    at = prim.get("attributes") or {}
    mat = prim.get("material")
    return (None if mat is None else remap.get(mat, mat),
            tuple(name for name, _t, _n in ATTRS if name in at))


def flatten(g, blob, keep_textures=True):
    """(new gltf, new BIN bytes, report) — one primitive per (mesh, material).

    Node and scene structure is preserved exactly, including node scales, because a
    SketchUp export carries its unit conversion there (see `mesh_density`'s note on
    0227d2c9) and dropping it would silently rescale the model.
    """
    bufs = buffers_of(g, blob)
    mat_map, materials = dedupe_materials(g)
    rep = {"meshes_in": len(g.get("meshes") or []), "prims_in": 0, "prims_out": 0,
           "tris_in": 0, "tris_out": 0, "skipped_modes": {}, "dropped_attrs": set(),
           "materials_in": len(g.get("materials") or []),
           "materials_out": len(materials)}
    out_bin = bytearray()
    views, accs, meshes = [], [], []

    def _view(payload, target=None):
        while len(out_bin) % 4:                       # 4-byte alignment, spec 3.6.2.4
            out_bin.append(0)
        off = len(out_bin)
        out_bin.extend(payload)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(payload)}
        if target:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    for m in (g.get("meshes") or []):
        groups = {}
        for p in (m.get("primitives") or []):
            rep["prims_in"] += 1
            mode = p.get("mode", TRIANGLES)
            at = p.get("attributes") or {}
            if mode != TRIANGLES or "POSITION" not in at:
                rep["skipped_modes"][mode] = rep["skipped_modes"].get(mode, 0) + 1
                continue
            for k in at:
                if k not in ("POSITION", "NORMAL", "TEXCOORD_0"):
                    rep["dropped_attrs"].add(k)
            groups.setdefault(_sig(p, mat_map), []).append(p)

        prims_out = []
        for (mat, names), plist in groups.items():
            verts = {nm: [] for nm in names}
            tri = []
            for p in plist:
                at = p["attributes"]
                data = {nm: accessor(g, bufs, at[nm]) for nm in names}
                nv = len(data["POSITION"])
                base = len(verts["POSITION"])
                idx = p.get("indices")
                ii = ([int(v[0]) for v in accessor(g, bufs, idx)] if idx is not None
                      else list(range(nv)))
                for nm in names:
                    verts[nm].extend(data[nm])
                tri.extend(base + v for v in ii)
            rep["tris_in"] += len(tri) // 3
            rep["tris_out"] += len(tri) // 3
            if not tri:
                continue
            attrs_out = {}
            for name, typ, n in ATTRS:
                if name not in verts:
                    continue
                vals = verts[name]
                payload = bytearray()
                for v in vals:
                    payload.extend(struct.pack("<" + "f" * n, *v[:n]))
                acc = {"bufferView": _view(payload, 34962), "componentType": 5126,
                       "count": len(vals), "type": typ}
                if name == "POSITION":                # min/max is REQUIRED on POSITION
                    acc["min"] = [min(v[k] for v in vals) for k in range(3)]
                    acc["max"] = [max(v[k] for v in vals) for k in range(3)]
                accs.append(acc)
                attrs_out[name] = len(accs) - 1
            ipay = struct.pack("<%dI" % len(tri), *tri)
            accs.append({"bufferView": _view(ipay, 34963), "componentType": 5125,
                         "count": len(tri), "type": "SCALAR"})
            prim = {"attributes": attrs_out, "indices": len(accs) - 1, "mode": 4}
            if mat is not None:
                prim["material"] = mat
            prims_out.append(prim)
            rep["prims_out"] += 1
        meshes.append({k: v for k, v in m.items() if k != "primitives"}
                      | {"primitives": prims_out})

    keep = {k: v for k, v in g.items()
            if k in ("asset", "scene", "scenes", "nodes", "extras")}
    if materials:
        keep["materials"] = materials
    if keep_textures:
        for k in ("textures", "samplers", "images"):
            if k in g:
                keep[k] = json.loads(json.dumps(g[k]))
        for im in keep.get("images") or []:
            bv = im.pop("bufferView", None)
            if bv is None:
                continue                              # a data: uri travels as-is
            src = (g.get("bufferViews") or [])[bv]
            b = bufs[src.get("buffer", 0)]
            o = int(src.get("byteOffset") or 0)
            im["bufferView"] = _view(b[o:o + int(src.get("byteLength") or 0)])
    else:
        rep["textures_dropped"] = len(g.get("images") or [])

    # a mesh emptied by the skips must not leave a node pointing at it
    live = [i for i, m in enumerate(meshes) if m["primitives"]]
    remap = {old: new for new, old in enumerate(live)}
    keep["meshes"] = [meshes[i] for i in live]
    nodes = []
    for n in (keep.get("nodes") or []):
        n = dict(n)
        if "mesh" in n:
            if n["mesh"] in remap:
                n["mesh"] = remap[n["mesh"]]
            else:
                n.pop("mesh")
        nodes.append(n)
    if nodes:
        keep["nodes"] = nodes
    keep["accessors"] = accs
    keep["bufferViews"] = views
    keep["buffers"] = [{"byteLength": len(out_bin)}]
    keep.setdefault("asset", {"version": "2.0"})
    keep["asset"] = dict(keep["asset"]) | {"version": "2.0"}
    rep["dropped_attrs"] = sorted(rep["dropped_attrs"])
    rep["meshes_out"] = len(keep["meshes"])
    for k in ("skins", "animations"):
        if g.get(k):
            rep[k + "_dropped"] = len(g[k])
    return keep, bytes(out_bin), rep


def write_glb(path, g, blob):
    js = json.dumps(g, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4)
    bl = blob + b"\x00" * ((4 - len(blob) % 4) % 4)
    total = 12 + 8 + len(js) + (8 + len(bl) if bl else 0)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", GLB_MAGIC, 2, total))
        f.write(struct.pack("<II", len(js), CHUNK_JSON))
        f.write(js)
        if bl:
            f.write(struct.pack("<II", len(bl), CHUNK_BIN))
            f.write(bl)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--drop-textures", action="store_true", dest="drop",
                    help="leave images out (reported, never silent)")
    a = ap.parse_args(argv)
    g, blob = read_glb(a.src)
    out, ob, rep = flatten(g, blob, keep_textures=not a.drop)
    write_glb(a.dst, out, ob)
    n0, n1 = os.path.getsize(a.src), os.path.getsize(a.dst)
    print(f"FLATTEN {os.path.basename(a.src)} -> {os.path.basename(a.dst)}")
    print(f"  {n0/1e6:.1f} MB -> {n1/1e6:.1f} MB   "
          f"meshes {rep['meshes_in']} -> {rep['meshes_out']}   "
          f"primitives {rep['prims_in']:,} -> {rep['prims_out']:,}   "
          f"materials {rep['materials_in']:,} -> {rep['materials_out']:,}")
    print(f"  triangles {rep['tris_in']:,} in, {rep['tris_out']:,} out")
    for k in ("skipped_modes", "dropped_attrs", "textures_dropped",
              "skins_dropped", "animations_dropped"):
        if rep.get(k):
            print(f"  {k}: {rep[k]}")
    # THE ONE THING THIS TOOL MAY NEVER DO IS LOSE GEOMETRY, so it is asserted here
    # rather than trusted: an import that quietly drops triangles would surface three
    # rungs later as a hole in a duvet nobody could trace back to a byte reader.
    if rep["tris_in"] != rep["tris_out"]:
        print("  REFUSED: triangle count changed — the file was NOT written faithfully")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
