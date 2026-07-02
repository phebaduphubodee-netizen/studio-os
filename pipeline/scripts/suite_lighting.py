"""
suite_lighting.py — INTERIOR-AI v0.2 lighting layer: METRIC + POLYGON (pure Python).

The v0.1 lighting.py sizes downlights in footcandles over a rectangular W x D room in
inches. Real work (the master-bedroom SUITE from the friend's 1:75 furniture plan) is an
L-shaped METRIC room with an ensuite sub-room, so this module derives the DRAFT lighting
plan on the polygon, in millimetres, against a LUX target band:

  * ambient recessed downlights — COUNT sized by the lumen method (KB §6.6) to hit the
    room's target illuminance E (lux) — N = E*A / (phi*CU*LLF) — laid on a grid that is
    CLIPPED to the outline polygon (point-in-polygon), so no fixture ever lands outside
    the room or in the L-notch. Each sub-room (ensuite) gets its own wet-room band.
  * an adjustable ACCENT over the headboard/TV built-in feature wall (if present)
  * a decorative PENDANT over a round coffee/centre table in the lounge (if present)

Illuminance is LUX here (metric), not footcandles: bedrooms ~150 lx general, baths ~200 lx
(CIE/IES residential midpoints — DRAFT; a designer sets real fixture photometrics + local
code). Fixtures come out in the SAME dict shape as lighting.py, and TYPE tags are assigned
by lighting.type_table(), so the RCP and the lighting schedule agree by construction (the
relational rule, KB §3). A spec may OVERRIDE via spec["lighting"]["fixtures"] (verbatim).

    python pipeline/suite_lighting.py [spec.json]      # inspect the derived layer
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lighting          # reuse DOWNLIGHT/PENDANT/ACCENT defaults + type_table (unit-agnostic)
import suite_clearance   # reuse _shoelace + _point_in_poly (the polygon IP)

# Target maintained illuminance by room class (lux). DRAFT midpoints from CIE/IES
# residential guidance — a designer confirms per real fixture + local code.
TARGET_LUX = {"habitable": 150, "bedroom": 150, "bedroom_suite": 150,
              "living": 150, "wet": 200, "bath": 200, "default": 150}
_WET = ("bath", "ensuite", "toilet", "wc", "ห้องน้ำ")


def _lux_target(name):
    n = (name or "").lower()
    if any(k in n for k in _WET):
        return TARGET_LUX["wet"]
    return TARGET_LUX.get(n, TARGET_LUX["default"])


def _cu_llf():
    cu = (lighting._LIGHTING_RULES.get("cu_default", 0.65))
    llf = (lighting._LIGHTING_RULES.get("llf_default", 0.80))
    return float(cu), float(llf)


def _grid_in_poly(outline, spacing_mm):
    """Centred grid over the outline's bbox at ~spacing_mm, KEPT only where the point
    is inside the outline polygon. Because a grid over the bbox at spacing s yields one
    point per s^2, the in-polygon count ~= poly_area / s^2, so choosing s = sqrt(A/N)
    lands ~N fixtures inside the real (clipped) shape. Returns (points, actual_spacing)."""
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    W = x1 - x0; H = y1 - y0
    if W <= 0 or H <= 0 or spacing_mm <= 0:
        return [], spacing_mm
    nx = max(1, round(W / spacing_mm)); ny = max(1, round(H / spacing_mm))
    sx = W / nx; sy = H / ny
    pts = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + (i + 0.5) * sx
            y = y0 + (j + 0.5) * sy
            if suite_clearance._point_in_poly(x, y, outline):
                pts.append((round(x, 1), round(y, 1)))
    return pts, round((sx + sy) / 2.0, 1)


def _ambient_for(outline, name, cu, llf, phi):
    """Lumen-method ambient downlights clipped to `outline`. Returns (fixtures, meta)."""
    area_m2 = suite_clearance._shoelace(outline) / 1e6
    target = _lux_target(name)
    if area_m2 <= 0:
        return [], {"area_m2": 0, "target_lux": target, "n": 0}
    n_target = max(1, round(target * area_m2 / (phi * cu * llf)))
    spacing = math.sqrt(area_m2 * 1e6 / n_target)          # mm
    pts, actual = _grid_in_poly(outline, spacing)
    if not pts:                                            # tiny/degenerate -> centroid
        cx = sum(p[0] for p in outline) / len(outline)
        cy = sum(p[1] for p in outline) / len(outline)
        pts = [(round(cx, 1), round(cy, 1))]
        actual = spacing
    achieved = len(pts) * phi * cu * llf / area_m2
    fixtures = []
    for (x, y) in pts:
        f = dict(lighting.DOWNLIGHT)
        f.update({"x": x, "y": y,
                  "note": f"ambient lumen-method {name}: {len(pts)} dl @ {phi:.0f}lm "
                          f"~{actual:.0f}mm o.c. -> ~{achieved:.0f}lx (target {target}lx)"})
        fixtures.append(f)
    return fixtures, {"area_m2": round(area_m2, 1), "target_lux": target,
                      "achieved_lux": round(achieved), "n": len(pts),
                      "spacing_mm": actual}


def plan_lighting(spec):
    """Return (fixtures, meta) for a room-spec@0.2 (metric polygon)."""
    r = spec["room"]
    outline = [tuple(p) for p in r["outline_mm"]]
    H = float(r.get("ceiling_mm", 2800))
    cu, llf = _cu_llf()
    phi = float(lighting.DOWNLIGHT["lumens"])

    override = (spec.get("lighting") or {}).get("fixtures")
    if override:
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        cx = (min(xs) + max(xs)) / 2.0; cy = (min(ys) + max(ys)) / 2.0
        fixtures = []
        for f in override:
            base = dict(lighting.DOWNLIGHT); base.update(f)
            base.setdefault("note", "from spec")
            base.setdefault("x", round(cx, 1)); base.setdefault("y", round(cy, 1))
            fixtures.append(base)
        return fixtures, {"source": "spec-override", "ceiling_mm": H}

    fixtures, meta = [], {"source": "auto", "ceiling_mm": H, "zones": []}

    # 1) ambient for the main room outline
    main_fx, main_meta = _ambient_for(outline, r.get("type", "habitable"), cu, llf, phi)
    fixtures += main_fx
    meta["zones"].append(dict(main_meta, zone=r.get("type", "room")))

    # 2) ambient for each sub-room (ensuite gets the wet-room band + its own ceiling)
    for sr in spec.get("subrooms", []):
        so = [tuple(p) for p in sr["outline_mm"]]
        nm = sr.get("name", "sub")
        sub_fx, sub_meta = _ambient_for(so, nm, cu, llf, phi)
        fixtures += sub_fx
        meta["zones"].append(dict(sub_meta, zone=nm))

    # 3) ACCENT over the headboard/TV built-in feature wall (the focal millwork).
    focal = next((b for b in spec.get("builtins", [])
                  if b.get("kind") in ("headboard_tv", "feature", "tv")), None)
    if focal:
        cx = float(focal["x"]) + float(focal["w"]) / 2.0
        cy = float(focal["y"]) + float(focal["d"]) / 2.0
        cy = cy + 400.0 if cy < max(p[1] for p in outline) / 2.0 else cy - 400.0
        f = dict(lighting.ACCENT)
        f.update({"x": round(cx, 1), "y": round(cy, 1),
                  "note": f"accent wall-wash on {focal.get('name', focal['kind'])}"})
        fixtures.append(f)

    # 4) decorative PENDANT over a round coffee/centre table in the lounge.
    table = next((it for it in spec.get("items", [])
                  if it.get("kind") in ("coffee_table", "round_table", "dining_table")), None)
    if table:
        cx = float(table["x"]) + float(table["w"]) / 2.0
        cy = float(table["y"]) + float(table["d"]) / 2.0
        f = dict(lighting.PENDANT)
        f.update({"x": round(cx, 1), "y": round(cy, 1),
                  "note": f"decorative pendant over {table.get('name', table['kind'])}"})
        fixtures.append(f)

    return fixtures, meta


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "bedroom_suite.json")
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    fixtures, meta = plan_lighting(spec)
    rows, _ = lighting.type_table(fixtures)
    print(f"=== metric lighting layer for {os.path.basename(path)} ({meta['source']}) ===")
    for z in meta.get("zones", []):
        print(f"  zone {z['zone']}: {z['n']} downlights over {z['area_m2']} m² "
              f"~{z.get('spacing_mm','?')}mm o.c. -> ~{z.get('achieved_lux','?')}lx (target {z['target_lux']}lx)")
    print(f"  total {len(fixtures)} fixtures, {len(rows)} types:")
    for row in rows:
        print(f"    [{row['tag']}] {row['type']}: {row['lumens']}lm {row['cct_k']}K CRI{row['cri']} "
              f"({row['layer']}) x{row['count']}")
    print("  (LUX target is a DRAFT residential midpoint — verify vs real fixtures + local code)")
