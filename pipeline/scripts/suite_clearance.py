"""
suite_clearance.py — INTERIOR-AI v0.3.1 clearance engine: METRIC + POLYGON + Thai code.

v0.2 embedded its own DR-derived Thai rules; v0.3 (M3.1 unification slice, 2026-07-02)
loads the statutory floors from dimensional_rules.v0.2.json `thai_code_minimums` —
ONE cited rule source for every engine. The unification also fixed three
miscitations the embedded copy carried:
  * ระยะดิ่ง 2600 is ข้อ 22 (was cited §21) and is FLOOR-TO-FLOOR, not clear ceiling;
  * bathroom 2000 is ฉ.39 ข้อ 9 (was attributed to กฎกระทรวง 55);
  * the 800/1900 door minimums are NOT a general statutory interior-door rule —
    ฉ.55 ข้อ 31 covers FIRE-ESCAPE doors; kept as a STUDIO floor (ergonomic std
    81 cm per dimensional_rules doors_and_openings), honestly labeled.
v0.3.1 (scrutiny fixes, qa/reports/2026-07-02-scrutiny-019a67f.md):
  * ข้อ 22 is checked on its OWN basis: clear >= 2600 passes a fortiori; clear < 2600
    is a WARN (clear height cannot prove a floor-to-floor breach) — pass
    room.floor_to_floor_mm for a statute-basis PASS/FAIL;
  * ข้อ 20 fully enforced for bedrooms: NET area (outline minus sub-rooms) + narrow
    side (bbox approximation); non-bedroom rooms get an informational line, not the
    bedroom statute;
  * in-bounds treats on-boundary corners as inside (flush-to-wall east/north = legal);
  * rug overlap whitelist scoped to loose furniture only (rug under builtin millwork
    and rug-on-rug still warn).
Engine stays engine-agnostic IP: pure Python, PASS / WARN / FAIL, no CAD/3D needed.

    python pipeline/scripts/suite_clearance.py [spec.json]
"""
import json
import os
import re
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
        # loaded for cross-engine reuse; NOT enforced in this engine (no corridor
        # geometry in room-spec@0.2) — enforcement lands with Gate 0 / clearance_check
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


def _on_edge(x, y, poly, eps=0.5):
    """Point lies ON a polygon edge (within eps mm). Ray-casting counts max-x/max-y
    boundaries as outside; flush-to-wall furniture is legal, so boundary = inside."""
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        seg2 = dx * dx + dy * dy
        if seg2 == 0:
            continue
        t = ((x - x1) * dx + (y - y1) * dy) / seg2
        if t < -1e-9 or t > 1 + 1e-9:
            continue
        px, py = x1 + t * dx, y1 + t * dy
        if (x - px) ** 2 + (y - py) ** 2 <= eps * eps:
            return True
    return False


def _inside_or_on(x, y, poly):
    return _point_in_poly(x, y, poly) or _on_edge(x, y, poly)


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
    # absent/zero ceiling data is MISSING, not a 0 mm measurement
    ceiling = float(r["ceiling_mm"]) if r.get("ceiling_mm") else None
    area = _shoelace(outline)

    # 1) ceiling height (room + each sub-room, wet rooms get the lower min).
    # ข้อ 22's 2600 is ระยะดิ่ง = FLOOR-TO-FLOOR; spec ceiling_mm is CLEAR height.
    # clear >= min proves compliance a fortiori (slab thickness >= 0); clear < min
    # proves NOTHING (clear + slab may still reach the floor) -> WARN, never a
    # statutory FAIL. Provide room.floor_to_floor_mm to check the statute directly.
    cmin = RULES_TH["ceiling_min_habitable"]
    f2f = r.get("floor_to_floor_mm")
    if f2f is not None:
        try:
            f2fv = float(f2f)
        except (TypeError, ValueError):
            f2fv = None
        if f2fv is None:
            add("FAIL", "ระยะดิ่ง (room, floor-to-floor)", f"floor_to_floor_mm invalid: {f2f!r}")
        else:
            add("PASS" if f2fv >= cmin else "FAIL", "ระยะดิ่ง (room, floor-to-floor)",
                f"{f2fv:.0f} mm vs {cmin} min ({RULES_TH['ceiling_min_habitable_cite']})")
        if ceiling is not None:
            add("PASS", "clear ceiling (informational)",
                f"clear {ceiling:.0f} mm recorded — statute checked on floor-to-floor above")
        else:
            add("FAIL", "ceiling height (room)", "room.ceiling_mm missing — provide the clear height")
    elif ceiling is None:
        add("FAIL", "ceiling height (room)",
            "room.ceiling_mm missing — cannot check ข้อ 22 even as a clear-height proxy")
    elif ceiling >= cmin:
        add("PASS", "ceiling height (room)",
            f"clear {ceiling:.0f} mm >= {cmin} floor-to-floor min -> compliant a fortiori "
            f"({RULES_TH['ceiling_min_habitable_cite']})")
    else:
        add("WARN", "ceiling height (room)",
            f"clear {ceiling:.0f} mm < {cmin} floor-to-floor min — clear height cannot prove "
            f"a ข้อ 22 breach; provide room.floor_to_floor_mm to verify "
            f"({RULES_TH['ceiling_min_habitable_cite']})")
    for sr in spec.get("subrooms", []):
        wet = any(k in (sr.get("name", "") + sr.get("th", "")).lower() for k in _WET)
        if not sr.get("ceiling_mm"):
            add("FAIL", f"ceiling ({sr.get('name','sub')})", "ceiling_mm missing — provide the clear height")
            continue
        sc = float(sr["ceiling_mm"])
        if wet:
            # ฉ.39 ข้อ 9 is measured floor-to-CEILING — clear height IS the statute basis
            smin = RULES_TH["ceiling_min_bath"]
            add("PASS" if sc >= smin else "FAIL", f"ceiling ({sr.get('name','sub')})",
                f"{sc:.0f} mm vs {smin} min ({RULES_TH['ceiling_min_bath_cite']} — พื้นถึงเพดาน)")
        elif sc >= cmin:
            add("PASS", f"ceiling ({sr.get('name','sub')})",
                f"clear {sc:.0f} mm >= {cmin} floor-to-floor min -> compliant a fortiori")
        else:
            add("WARN", f"ceiling ({sr.get('name','sub')})",
                f"clear {sc:.0f} mm < {cmin} floor-to-floor min — cannot prove breach from clear height")

    # 2) entry door size
    door = spec.get("door")
    if door:
        dw, dh = float(door.get("w", 0)), float(door.get("h", 0))
        add("PASS" if dw >= RULES_TH["door_w_min"] else "FAIL", "door width",
            f"{dw:.0f} mm vs {RULES_TH['door_w_min']} min ({RULES_TH['door_cite']})")
        add("PASS" if dh >= RULES_TH["door_h_min"] else "FAIL", "door height",
            f"{dh:.0f} mm vs {RULES_TH['door_h_min']} min ({RULES_TH['door_cite']})")

    # 3) ฉ.55 ข้อ 20 is a BEDROOM statute (net area >= 8 m² AND narrow side >= 2500).
    # Statutory tier (FAIL) only when the room TYPE names a bedroom; a bed item in a
    # non-bedroom-named room is a HEURISTIC (WARN — could be a daybed in a den).
    # Area is NET of sub-rooms (an ensuite is not ห้องนอน).
    rtype = str(r.get("type", "")).lower()
    typed_bedroom = bool(re.search(r"(^|[^a-z])bed(room)?($|[^a-z])", rtype)) or "นอน" in rtype
    bed_item = any(it.get("kind") == "bed" for it in spec.get("items", []))
    sub_area = sum(_shoelace([tuple(p) for p in sr["outline_mm"]])
                   for sr in spec.get("subrooms", []))
    net = area - sub_area
    if typed_bedroom or bed_item:
        viol = "FAIL" if typed_bedroom else "WARN"
        how = "" if typed_bedroom else (f" [heuristic: type '{rtype}' is not bedroom-named "
                                        f"but a bed item is present — verify the room type]")
        add("PASS" if net >= RULES_TH["bedroom_area_min_mm2"] else viol,
            "bedroom area (net of sub-rooms)",
            f"{net/1e6:.1f} m² net (outline {area/1e6:.1f} − sub-rooms {sub_area/1e6:.1f}) "
            f"vs {RULES_TH['bedroom_area_min_mm2']/1e6:.0f} m² min ({RULES_TH['bedroom_area_cite']}){how}")
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        narrow = min(bw, bh)
        wmin = RULES_TH["bedroom_width_min"]
        true_rect = len(outline) == 4 and abs(area - bw * bh) < 1.0
        carved = bool(spec.get("subrooms"))
        if narrow < wmin:
            # bbox min-dim >= every true leg width, so bbox < min PROVES the breach
            add(viol, "bedroom narrow side",
                f"{narrow:.0f} mm vs {wmin} min ({RULES_TH['bedroom_width_cite']}){how}")
        elif true_rect and not carved:
            add("PASS", "bedroom narrow side",
                f"{narrow:.0f} mm vs {wmin} min ({RULES_TH['bedroom_width_cite']}){how}")
        else:
            # bbox >= min proves NOTHING for concave/carved rooms (errs toward PASS) —
            # never stamp an unproven statutory PASS; hand it to a human instead
            add("WARN", "bedroom narrow side (unproven)",
                f"bbox {narrow:.0f} mm >= {wmin}, but the outline is concave or carved by "
                f"sub-rooms — bbox cannot prove the sleeping zone's narrow side; verify "
                f">= {wmin} on the plan ({RULES_TH['bedroom_width_cite']}){how}")
    else:
        add("PASS", "floor area (informational)",
            f"{area/1e6:.1f} m² — not detected as a bedroom (by type/items heuristic); if it IS "
            f"one, ฉ.55 ข้อ 20 applies (>= {RULES_TH['bedroom_area_min_mm2']/1e6:.0f} m² net, "
            f"narrow side >= {RULES_TH['bedroom_width_min']} mm); unit-level ฉ.55 ข้อ 19 "
            f"(20 m²) binds the whole unit, not this room")

    # 4) furniture + built-ins inside the outline polygon (all corners in)
    placed = [dict(it, _grp="item") for it in spec.get("items", [])] + \
             [dict(b, _grp="builtin") for b in spec.get("builtins", [])]
    for it in placed:
        outc = [c for c in _corners(it) if not _inside_or_on(c[0], c[1], outline)]
        nm = it.get("name") or it.get("kind", "item")
        add("PASS" if not outc else "FAIL", f"in-bounds: {nm}",
            "inside outline" if not outc else f"{len(outc)} corner(s) outside the room polygon")

    # 5) overlaps between placed pieces (excluding designed adjacencies)
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i], placed[j]
            if frozenset({a.get("kind"), b.get("kind")}) in _OK_OVERLAP:
                continue
            kinds = (a.get("kind"), b.get("kind"))
            if ("rug" in kinds and kinds[0] != kinds[1]
                    and a["_grp"] == "item" and b["_grp"] == "item"):
                continue          # loose furniture ON a rug is the intent, not a conflict
                                  # (rug under BUILTIN millwork and rug-on-rug still warn)
            if _overlap(a, b):
                add("WARN", f"overlap: {a.get('name', a.get('kind'))} / {b.get('name', b.get('kind'))}",
                    "footprints intersect (ok if stacked/against a wall)")

    # 6) sub-room fixtures inside their sub-room
    for sr in spec.get("subrooms", []):
        so = [tuple(p) for p in sr["outline_mm"]]
        for fx in sr.get("fixtures", []):
            outc = [c for c in _corners(fx) if not _inside_or_on(c[0], c[1], so)]
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
    print("  (statutory floors from dimensional_rules.v0.2.json thai_code_minimums, cited to knowledge/codes-th.")
    print("   ENFORCED here: ceiling (ข้อ 22 proxy / ฉ.39 bath direct), bedroom net-area + narrow side (ข้อ 20),")
    print("   in-bounds, overlaps. Loaded but NOT enforced in this engine: corridor/circulation (Gate 0 work).")
    print("   Door 800/1900 = STUDIO floor, not statute. Clear-height >= 2600 is a conservative proxy for ข้อ 22.)")
    return res, verdict


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    report(spec, os.path.basename(spec_path))
