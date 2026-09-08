"""trn001_measure.py — turn probed target PIXELS into world mm. PURE (no bpy).

Once round 1's camera solve converged, the target image stopped being a
proportion puzzle and became a MEASURING INSTRUMENT: any pixel a probe can
find on a face whose plane is known reads back as a real dimension. This is
the tool that does the reading, so no round after the first has to guess a
millimetre from a ratio.

  python pipeline/scripts/trn001_measure.py <spec.json> <probes.json>

probes.json: {"probes": [{"name", "u", "v", "plane": ["y", -350]}, ...]}
Planes may also be named for readability — see PLANES below, which derive from
the spec so a dimension change can never leave a stale plane behind.
"""
import argparse
import json
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import trn001_geom as G  # noqa: E402

RES = 2048


def planes(spec):
    """Named planes of the built piece, derived from the spec (never hardcoded)."""
    u = spec["unit"]
    return {
        "wall": ("y", 0.0),
        "tower_front": ("y", -u["tower"]["d_mm"]),
        "header_front": ("y", -u["header"]["depth_mm"]),
        "marble_face": ("y", -u["marble"]["proud_mm"]),
        "plinth_front": ("y", -u["plinth"]["d_mm"]),
        "step_front": ("y", -u["step"]["d_mm"]),
        "box_front": ("y", -u["box"]["d_mm"]),
        "floor": ("z", 0.0),
        "plinth_top": ("z", u["plinth"]["h_mm"]),
        "ceiling": ("z", u["header"]["top_z_mm"]),
    }


def measure(spec, probes):
    cam = spec["camera"]
    named = planes(spec)
    rows = []
    for p in probes:
        pl = p["plane"]
        plane = named[pl] if isinstance(pl, str) else (pl[0], float(pl[1]))
        world = G.backproject(cam, (p["u"], p["v"]), plane, res=RES)
        rows.append({"name": p["name"], "plane": pl,
                     "world_mm": None if world is None else [round(c, 1) for c in world]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("probes")
    ap.add_argument("--json", action="store_true", help="emit rows as JSON")
    a = ap.parse_args()
    spec = G.load_spec(a.spec)
    probes = json.load(open(a.probes, encoding="utf-8"))["probes"]
    rows = measure(spec, probes)
    if a.json:
        print(json.dumps(rows, indent=1))
        return
    print(f"{'name':28s} {'plane':14s} x_mm      y_mm      z_mm")
    for r in rows:
        w = r["world_mm"]
        pl = r["plane"] if isinstance(r["plane"], str) else f"{r['plane'][0]}={r['plane'][1]}"
        if w is None:
            print(f"{r['name']:28s} {pl:14s} RAY MISSED THE PLANE")
        else:
            print(f"{r['name']:28s} {pl:14s} {w[0]:9.1f} {w[1]:9.1f} {w[2]:9.1f}")


if __name__ == "__main__":
    main()
