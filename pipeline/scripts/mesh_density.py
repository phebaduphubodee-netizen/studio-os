"""mesh_density.py — how fine is the cloth in this .glb, WITHOUT opening Blender.

PURE PYTHON, NO `bpy` (pipeline/CLAUDE.md layer law). It reads the glTF JSON chunk
only: every primitive's index accessor carries a triangle count and every POSITION
accessor carries min/max.

WHY IT EXISTS, and it is a cost measured on 2026-08-17. The fineness cut
(`bedcloth_rules.fineness`) is the only rung that can see what a bought cover is MADE
of, and the only way to apply it was `bedcloth_bench` — which imports each candidate
into Blender. Measured that day: 68 small models took ~4 minutes, and ONE 88 MB model
took over 20 minutes on its own, at 30-40 s per mesh node. That cost is why this lane
had auditioned TEN bed covers in its whole history and then reported the free tier
"exhausted". A screen that costs milliseconds is not a convenience here; it is the
difference between considering ten candidates and considering a hundred.

    python pipeline/scripts/mesh_density.py <cache_dir> [--cover 1820x1969]

IT ESTIMATES AND IT NEVER DECIDES. `bedcloth_fit.edge_mm` — median edge in WORLD
space on the STAGED mesh — stays the authority, and this file must never grow a
threshold of its own. A second definition of a rule that drifts from the first is
this repo's most repeated defect (the bench's own deleted runners, the fineness
control that lived inline in the build). Everything here ORDERS a queue so the
expensive rung is spent on the right candidates first.

THE ESTIMATE IS UNIT-FREE, WHICH IS THE WHOLE TRICK. A SketchUp export's units are
the one thing that cannot be trusted (`pipeline/CLAUDE.md`: "SketchUp exports
IMPERIAL even when the model was authored in metres"), and this shelf proves it —
`0227d2c9`'s sheets read 90 x 79 in the file and import as 0.9 m objects. So the
estimate never uses the file's own extents. For a cloth sheet quadrangulated at
roughly uniform pitch, the number of quads across it is

    n_across = sqrt(tris / 2)

which is a pure count, immune to the file's units. Staging always scales a cover so
it COVERS this bed's mattress, so its world size is known from the BED rather than
from the file, and

    world edge ~ cover_span / n_across

CALIBRATION, on the only candidate whose world edge was measured before this file
existed: `0afd4c6f` carries 4,175 triangles on its field sheet -> estimate 43.8 mm
against a MEASURED 43.5 mm. A second point, `13525bfb` (33,632 tris), estimates 15.4
against a measured 25.6 — optimistic by 1.7x, because the largest primitive in a file
is not always the part that ends up being the field. Treat the estimate as a floor on
coarseness: a candidate this screen calls coarse will not come back fine.

WHAT IT SAYS ABOUT THE ASK, in one line the bench cannot afford to compute: to clear
a 10.3 mm control on a ~2 m cover a candidate needs about 2 * (2000/10.3)^2 = 75,000
triangles IN ONE SHEET. Nothing on this shelf of 84 models has that in a part that is
also a bed cover.
"""
import argparse
import json
import os
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

GLB_MAGIC = 0x46546C67


def gltf_json(path):
    """The JSON chunk of a binary glTF. Raises on anything that is not a .glb."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12:
            raise ValueError(f"{os.path.basename(path)}: too short to be a glb")
        magic, _ver, _total = struct.unpack("<III", head)
        if magic != GLB_MAGIC:
            raise ValueError(f"{os.path.basename(path)}: not a binary glTF")
        clen, _ctype = struct.unpack("<II", f.read(8))
        return json.loads(f.read(clen).decode("utf-8"))


def primitives(g):
    """[{tris, ext}] for every primitive, largest plan area first.

    `ext` is in the FILE's own units and is reported for orientation only — never
    used by the estimate, for the reason in the module docstring.
    """
    acc = g.get("accessors") or []
    out = []
    for m in (g.get("meshes") or []):
        for p in (m.get("primitives") or []):
            pos = (p.get("attributes") or {}).get("POSITION")
            if pos is None or pos >= len(acc):
                continue
            a = acc[pos]
            mn, mx = a.get("min"), a.get("max")
            if not mn or not mx or len(mn) < 3 or len(mx) < 3:
                continue
            ext = sorted((abs(mx[i] - mn[i]) for i in range(3)), reverse=True)
            idx = p.get("indices")
            n = acc[idx].get("count", 0) if (idx is not None and idx < len(acc)) \
                else a.get("count", 0)
            tris = max(0, int(n) // 3)
            if tris <= 0:
                continue
            out.append({"tris": tris, "ext": ext, "plan": ext[0] * ext[1]})
    out.sort(key=lambda r: -r["plan"])
    return out


def est_edge_mm(tris, cover_mm):
    """Estimated world edge (mm) of a sheet of `tris` triangles staged to span
    `cover_mm`. None when there is nothing to estimate from."""
    if not tris or tris <= 0 or not cover_mm or cover_mm <= 0:
        return None
    n_across = (tris / 2.0) ** 0.5
    return float(cover_mm) / n_across if n_across else None


def tris_needed(control_mm, cover_mm):
    """How many triangles ONE sheet needs to reach `control_mm` at this bed's span.
    The number that turns 'nothing is fine enough' into a spec a search can use."""
    if not control_mm or control_mm <= 0:
        return None
    return int(round(2.0 * (float(cover_mm) / float(control_mm)) ** 2))


def screen(path, cover_mm):
    """{slug-agnostic} density screen for one .glb — the densest sheet it holds."""
    prims = primitives(gltf_json(path))
    if not prims:
        return {"tris": 0, "est_edge_mm": None, "prims": 0}
    finest = max(prims, key=lambda r: r["tris"])
    return {"prims": len(prims), "tris": finest["tris"],
            "total_tris": sum(r["tris"] for r in prims),
            "ext": finest["ext"],
            "est_edge_mm": est_edge_mm(finest["tris"], cover_mm)}


def screen_dir(cache, cover_mm):
    """[(est_edge_mm, slug, tris, bytes)] over a cache of <slug>/<slug>.glb dirs."""
    rows = []
    for slug in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        d = os.path.join(cache, slug)
        if not os.path.isdir(d):
            continue
        glbs = [f for f in os.listdir(d) if f.endswith(".glb")]
        if not glbs:
            continue
        p = os.path.join(d, glbs[0])
        try:
            s = screen(p, cover_mm)
        except (OSError, ValueError, KeyError, struct.error) as e:
            rows.append((None, slug, 0, os.path.getsize(p), str(e)[:60]))
            continue
        rows.append((s["est_edge_mm"], slug, s["tris"], os.path.getsize(p), None))
    rows.sort(key=lambda r: (r[0] is None, r[0] if r[0] is not None else 0.0))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cache")
    ap.add_argument("--cover-mm", type=float, default=2000.0,
                    help="the span the cover must reach (this bed: 1820 x 1969)")
    ap.add_argument("--control-mm", type=float, default=None,
                    help="the fineness control to report against, if known")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args(argv)
    rows = screen_dir(a.cache, a.cover_mm)
    need = tris_needed(a.control_mm, a.cover_mm) if a.control_mm else None
    print(f"SCREEN {len(rows)} model(s) — ESTIMATE ONLY, orders the queue, decides "
          f"nothing (authority: bedcloth_fit.edge_mm on the staged mesh)")
    if need:
        print(f"SCREEN to reach {a.control_mm:.1f} mm over a {a.cover_mm:.0f} mm "
              f"cover, ONE sheet needs ~{need:,} triangles")
    print(f"{'slug':44s} {'est edge':>9} {'sheet tris':>11} {'MB':>7}")
    for est, slug, tris, nbytes, err in rows[:a.top]:
        if err:
            print(f"{slug:44s} {'—':>9} {'—':>11} {nbytes/1e6:7.1f}  {err}")
            continue
        mark = ""
        if a.control_mm and est is not None:
            mark = "  <= control" if est <= a.control_mm else ""
        print(f"{slug:44s} {est:8.1f}mm {tris:11,d} {nbytes/1e6:7.1f}{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
