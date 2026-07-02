"""
suite_clearance.py — INTERIOR-AI v0.3 clearance engine: METRIC + POLYGON + Thai code.

v0.2 embedded its own DR-derived Thai rules; v0.3 (M3.1 unification slice, 2026-07-02)
loads the statutory floors from dimensional_rules.v0.2.json `thai_code_minimums` —
ONE cited rule source for every engine. The unification also fixed three
miscitations the embedded copy carried:
  * ระยะดิ่ง 2600 is ข้อ 22 (was cited §21) and is FLOOR-TO-FLOOR, not clear ceiling;
  * bathroom 2000 is ฉ.39 ข้อ 9 (was attributed to กฎกระทรวง 55);
  * the 800/1900 door minimums are NOT a general statutory interior-door rule —
    ฉ.55 ข้อ 31 covers FIRE-ESCAPE doors; kept as a STUDIO floor (ergonomic std
    81 cm per dimensional_rules doors_and_openings), honestly labeled.
Engine stays engine-agnostic IP: pure Python, PASS / WARN / FAIL, no CAD/3D needed.

    python pipeline/scripts/suite_clearance.py [spec.json]
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_RULES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "dimensional_rules.v0.2.json")


def _load_rules():
    """Thai statutory floors from the ONE cited source (dimensional_rules v0.2,
    section thai_code_minimums). Values in mm; each carries its legal cite.
    Door minimums are a STUDIO floor (no general statutory interior-door min —
    ฉ.55 ข้อ 31 is fire doors), kept at the v0.2 thresholds for gate stability."""
    with open(_RULES_JSON, encoding="utf-8") as fh:
        tcm = json.load(fh)["thai_code_minimums"]

    def v(key):
        return tcm[key]["value"]

    def cite(key):
        return tcm[key]["cite"].split(" — ")[0]

    return {
        "ceiling_min_habitable": v("floor_to_floor_habitable_min_mm"),
        "ceiling_min_habitable_cite": cite("floor_to_floor_habitable_min_mm") + " (ระยะดิ่ง พื้นถึงพื้น)",
        "ceiling_min_bath": v("bathroom_floor_to_ceiling_min_mm"),
        "ceiling_min_bath_cite": cite("bathroom_floor_to_ceiling_min_mm"),
        "bedroom_area_min_mm2": v("bedroom_area_min_m2") * 1e6,
        "bedroom_area_cite": cite("bedroom_area_min_m2"),
        "bedroom_width_min": v("bedroom_narrow_side_min_mm"),
        "bedroom_width_cite": cite("bedroom_narrow_side_min_mm"),
        "corridor_min": v("corridor_in_house_min_mm"),
        "corridor_cite": cite("corridor_in_house_min_mm"),
        "door_w_min": 800,
        "door_h_min": 1900,
        "door_cite": "studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors)",
        "circulation_min": 900,          # ergonomic design walkway (DRAFT, not code)
    }


RULES_TH = _load_rules()
_WET = ("bath", "ensuite", "toilet", "wc", "ห้องน้ำ")


def _shoelace(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _point_in_poly(x, y, poly):
    """Ray-casting point-in-polygon (poly = list of (x,y), any winding)."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _corners(it):
    x, y, w, d = float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"])
    return [(x, y), (x + w, y), (x + w, y + d), (x, y + d)]


def _bbox(it):
    x, y, w, d = float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"])
    return (x, y, x + w, y + d)


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _bbox(a); bx0, by0, bx1, by1 = _bbox(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


# furniture pairs that are SUPPOSED to sit on/next to each other -> not a conflict
_OK_OVERLAP = {frozenset({"bed", "platform"}), frozenset({"bed", "nightstand"}),
               frozenset({"platform", "nightstand"}), frozenset({"platform", "bench"}),
               frozenset({"sofa", "coffee_table"}), frozenset({"sofa", "armchair"})}


def check(spec):
    out = []
    def add(status, name, detail): out.append({"status": status, "check": name, "detail": detail})

    r = spec["room"]
    outline = [tuple(p) for p in r["outline_mm"]]
    ceiling = float(r.get("ceiling_mm", 0))
    area = _shoelace(outline)

    # 1) ceiling height (room + each sub-room, wet rooms get the lower min)
    cmin = RULES_TH["ceiling_min_habitable"]
    add("PASS" if ceiling >= cmin else "FAIL", "ceiling height (room)",
        f"{ceiling:.0f} mm vs {cmin} min ({RULES_TH['ceiling_min_habitable_cite']})")
    for sr in spec.get("subrooms", []):
        wet = any(k in (sr.get("name", "") + sr.get("th", "")).lower() for k in _WET)
        smin = RULES_TH["ceiling_min_bath"] if wet else cmin
        sc = float(sr.get("ceiling_mm", 0))
        add("PASS" if sc >= smin else "FAIL", f"ceiling ({sr.get('name','sub')})",
            f"{sc:.0f} mm vs {smin} min")

    # 2) entry door size
    door = spec.get("door")
    if door:
        dw, dh = float(door.get("w", 0)), float(door.get("h", 0))
        add("PASS" if dw >= RULES_TH["door_w_min"] else "FAIL", "door width",
            f"{dw:.0f} mm vs {RULES_TH['door_w_min']} min ({RULES_TH['door_cite']})")
        add("PASS" if dh >= RULES_TH["door_h_min"] else "FAIL", "door height",
            f"{dh:.0f} mm vs {RULES_TH['door_h_min']} min ({RULES_TH['door_cite']})")

    # 3) overall area vs the bedroom floor min (informational for a big suite)
    add("PASS" if area >= RULES_TH["bedroom_area_min_mm2"] else "WARN", "floor area (Thai bedroom min)",
        f"{area/1e6:.1f} m² vs {RULES_TH['bedroom_area_min_mm2']/1e6:.0f} m² min ({RULES_TH['bedroom_area_cite']})")

    # 4) furniture + built-ins inside the outline polygon (all corners in)
    placed = [dict(it, _grp="item") for it in spec.get("items", [])] + \
             [dict(b, _grp="builtin") for b in spec.get("builtins", [])]
    for it in placed:
        outc = [c for c in _corners(it) if not _point_in_poly(c[0], c[1], outline)]
        nm = it.get("name") or it.get("kind", "item")
        add("PASS" if not outc else "FAIL", f"in-bounds: {nm}",
            "inside outline" if not outc else f"{len(outc)} corner(s) outside the room polygon")

    # 5) overlaps between placed pieces (excluding designed adjacencies)
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i], placed[j]
            if frozenset({a.get("kind"), b.get("kind")}) in _OK_OVERLAP:
                continue
            if "rug" in (a.get("kind"), b.get("kind")):
                continue          # furniture ON a rug is the intent, not a conflict
            if _overlap(a, b):
                add("WARN", f"overlap: {a.get('name', a.get('kind'))} / {b.get('name', b.get('kind'))}",
                    "footprints intersect (ok if stacked/against a wall)")

    # 6) sub-room fixtures inside their sub-room
    for sr in spec.get("subrooms", []):
        so = [tuple(p) for p in sr["outline_mm"]]
        for fx in sr.get("fixtures", []):
            outc = [c for c in _corners(fx) if not _point_in_poly(c[0], c[1], so)]
            add("PASS" if not outc else "WARN", f"fixture in {sr.get('name','sub')}: {fx.get('name', fx.get('kind'))}",
                "inside" if not outc else "extends past the sub-room wall")

    return out


def report(spec, label=""):
    res = check(spec)
    icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX"}
    print(f"\n=== suite clearance {label} (metric, Thai code) ===")
    for r in res:
        print(f"  [{icon[r['status']]}] {r['check']}: {r['detail']}")
    fails = sum(x["status"] == "FAIL" for x in res)
    warns = sum(x["status"] == "WARN" for x in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")
    print(f"  -> {verdict}  ({fails} fail, {warns} warn)")
    print("  (statutory floors loaded from dimensional_rules.v0.2.json thai_code_minimums —")
    print("   cited to knowledge/codes-th; door minimums are a STUDIO floor, see docstring)")
    return res, verdict


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    report(spec, os.path.basename(spec_path))
