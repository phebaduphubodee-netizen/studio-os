"""
clearance_check.py — INTERIOR-AI core IP (Layer 1: engine-agnostic, NO Blender).

The differentiator lives HERE, not in Blender: dimensional correctness is a
CONSTRAINT problem. This module takes a room + a furniture layout (axis-aligned
boxes, inches) and verifies every clearance against dimensional_rules.json, then
emits a PASS / WARN / FAIL report. It runs on plain `python` — no Blender, no GUI —
so it is unit-testable and is the automated first-pass guard before a human QA.

The Blender layer (build_room.py) is just the MATERIALIZER that renders a spec
this layer has already validated.

Run a built-in demo:  python pipeline/clearance_check.py
"""
import json
import math
import os
import sys

try:  # keep output legible on a cp1252 Windows console (and allow Thai notes)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dimensional_rules.v0.2.json")
with open(RULES_PATH, encoding="utf-8") as _f:
    RULES = json.load(_f)


class Item:
    """Footprint box on the floor. x,y = SW corner; w,d = size (inches)."""
    def __init__(self, name, kind, x, y, w, d):
        self.name, self.kind = name, kind
        self.x, self.y, self.w, self.d = float(x), float(y), float(w), float(d)

    @property
    def aabb(self):
        return (self.x, self.y, self.x + self.w, self.y + self.d)

    def gap_to(self, other):
        """Orthogonal gap (in) between two AABBs; 0.0 if they overlap/touch."""
        ax0, ay0, ax1, ay1 = self.aabb
        bx0, by0, bx1, by1 = other.aabb
        dx = max(0.0, max(bx0 - ax1, ax0 - bx1))
        dy = max(0.0, max(by0 - ay1, ay0 - by1))
        return math.hypot(dx, dy)

    def overlaps(self, other):
        ax0, ay0, ax1, ay1 = self.aabb
        bx0, by0, bx1, by1 = other.aabb
        return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


class Room:
    def __init__(self, width_in, depth_in, ceiling_in, door=None):
        self.W, self.D, self.H = float(width_in), float(depth_in), float(ceiling_in)
        self.door = door

    def wall_gaps(self, it):
        """Clearance from an item to each wall: (west, east, south, north)."""
        return (it.x, self.W - (it.x + it.w), it.y, self.D - (it.y + it.d))


def _r(*keys, default=None):
    """Safe nested lookup into RULES."""
    node = RULES
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return default
        node = node[k]
    return node


def check(room, items):
    out = []

    def add(status, name, detail):
        out.append({"status": status, "check": name, "detail": detail})

    # 1) ceiling
    cmin = _r("ceilings_and_heights", "ceiling_min_habitable", "in", default=90)
    add("PASS" if room.H >= cmin else "FAIL", "ceiling height",
        f"{room.H:.0f}\" vs {cmin}\" min")

    # 1b) door fits the wall + under the ceiling. A door wider than the wall or
    #     taller than the ceiling makes the materializers build inverted piers /
    #     a negative-height header (silently-wrong geometry) — catch it HERE.
    if getattr(room, "door", None):
        dwin = float(room.door.get("w_in", 32) or 32)
        dhin = float(room.door.get("h_in", 80) or 80)
        add("PASS" if dwin < room.W else "FAIL", "door fits wall width",
            f"door {dwin:.0f}\" vs wall {room.W:.0f}\"")
        add("PASS" if dhin < room.H else "FAIL", "door under ceiling",
            f"door {dhin:.0f}\" vs ceiling {room.H:.0f}\"")

    # 2) every item inside the room
    for it in items:
        x0, y0, x1, y1 = it.aabb
        inside = x0 >= -0.01 and y0 >= -0.01 and x1 <= room.W + 0.01 and y1 <= room.D + 0.01
        add("PASS" if inside else "FAIL", f"in-bounds: {it.name}",
            "inside room" if inside else f"extends past room ({room.W:.0f}x{room.D:.0f}\")")

    # 3) no overlaps (rug-under-furniture excluded — that is the intent;
    #    rug-on-rug still flags: two rugs overlapping is an authoring error)
    for a, b in _pairs(items):
        if "rug" in (a.kind, b.kind) and a.kind != b.kind:
            continue
        if a.overlaps(b):
            add("FAIL", f"overlap: {a.name} / {b.name}", "footprints intersect")

    # 4) circulation: coarse proxy — non-paired items shouldn't be tighter than
    #    the secondary-walkway min (a real path-search comes in a later phase).
    sec = _r("circulation", "secondary_walkway_min", "in", default=30)
    for a, b in _pairs(items):
        if {a.kind, b.kind} & {"rug"}:
            continue
        if frozenset({a.kind, b.kind}) in ADJACENT:
            continue
        if a.overlaps(b):
            continue
        g = a.gap_to(b)
        if 0 < g < sec:
            add("WARN", f"tight gap: {a.name}/{b.name}",
                f"{g:.0f}\" < {sec}\" secondary-walkway (ok if not a path)")

    # 4b) door swing: nothing should sit in the door's swing quarter-arc (the door
    #     is centered on the south wall in the materializers). WARN — could be a
    #     pocket/sliding door or low furniture, but usually a real conflict.
    if getattr(room, "door", None):
        dwn = float(room.door.get("w_in", 32) or 32)
        dl = (room.W - dwn) / 2.0
        sx0, sy0, sx1, sy1 = dl, 0.0, dl + dwn, dwn      # conservative swing bbox
        for it in items:
            if it.kind == "rug":
                continue
            ix0, iy0, ix1, iy1 = it.aabb
            if ix0 < sx1 and sx0 < ix1 and iy0 < sy1 and sy0 < iy1:
                add("WARN", f"door swing: {it.name}",
                    f"sits in the door swing zone (~{dwn:.0f}\" arc)")

    # 5) typed relationship rules
    out += _living(room, items)
    out += _bedroom(room, items)
    out += _dining(room, items)
    return out


# Pairs that are SUPPOSED to sit close together — excluded from the generic
# "tight gap = circulation problem" proxy.
ADJACENT = {
    frozenset({"sofa", "coffee_table"}), frozenset({"sofa", "side_table"}),
    frozenset({"armchair", "side_table"}), frozenset({"bed", "nightstand"}),
    frozenset({"dining_table", "dining_chair"}), frozenset({"desk", "chair"}),
}


def _pairs(items):
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            yield items[i], items[j]


def _by(items, *kinds):
    return [it for it in items if it.kind in kinds]


def _living(room, items):
    res = []
    sofas = _by(items, "sofa")
    tables = _by(items, "coffee_table")
    lo = _r("living_room", "sofa_to_coffee_table", "in_min", default=14)
    hi = _r("living_room", "sofa_to_coffee_table", "in_max", default=18)
    for s in sofas:
        for t in tables:
            g = s.gap_to(t)
            ok = lo <= g <= hi
            res.append({"status": "PASS" if ok else "WARN",
                        "check": f"sofa<->coffee_table ({s.name}/{t.name})",
                        "detail": f"{g:.0f}\" (target {lo}-{hi}\")"})
    return res


def _bedroom(room, items):
    res = []
    need = _r("bedroom", "clearance_around_bed", "in_min", default=24)
    one_side = 30
    for bed in _by(items, "bed"):
        gaps = room.wall_gaps(bed)
        names = ("west", "east", "south", "north")
        passable = [g for g in gaps if g >= need]
        has_make_side = any(g >= one_side for g in gaps)
        ok = len(passable) >= 1 and has_make_side
        detail = ", ".join(f"{n}={g:.0f}\"" for n, g in zip(names, gaps))
        res.append({"status": "PASS" if ok else "WARN",
                    "check": f"clearance around bed ({bed.name})",
                    "detail": f"{detail}  (need >=1 side {one_side}\" to make it)"})
    return res


def _dining(room, items):
    res = []
    need = _r("dining", "table_edge_to_wall_min", "in", default=36)
    for tbl in _by(items, "dining_table"):
        gmin = min(room.wall_gaps(tbl))
        ok = gmin >= need
        res.append({"status": "PASS" if ok else "FAIL",
                    "check": f"dining pull-out ({tbl.name})",
                    "detail": f"nearest wall {gmin:.0f}\" (need {need}\")"})
    return res


def check_lighting(spec, fixtures=None):
    """IES completeness checks on the lighting layer (KB §6), reading targets from
    dimensional_rules.json["lighting"]. Returns result dicts in the same shape as
    check(). These are WARN-level — the lighting layer is a DRAFT a designer refines,
    so they flag issues without hard-blocking the build (only a geometry FAIL blocks).

    Checks: (1) ambient general illuminance via the lumen method (avg fc = ambient
    lumens x CU x LLF / area) vs the room's IES band; (2) per fixture-type CCT comfort
    band + CRI floor; (3) layering (a primary room wants ambient + task/accent)."""
    import lighting  # local import: lighting has no clearance dependency (no import cycle)

    r = spec.get("room", {}) or {}
    W, D = float(r.get("width_in", 0) or 0), float(r.get("depth_in", 0) or 0)
    rtype = r.get("type", "default")
    if fixtures is None:
        fixtures, _ = lighting.plan_lighting(spec)

    L = _r("lighting", default={}) or {}
    out = []

    # 1) ambient general illuminance (lumen method)
    area = (W * D) / 144.0
    amb = sum(float(f.get("lumens", 0) or 0) for f in fixtures if f.get("layer") == "ambient")
    cu = L.get("cu_default", 0.65)
    llf = L.get("llf_default", 0.80)
    fc_tbl = L.get("general_illuminance_fc", {}) or {}
    tgt = fc_tbl.get(rtype) or fc_tbl.get("default", {"min": 10, "max": 30})
    if area > 0 and amb > 0:
        fc = amb * cu * llf / area
        lo, hi = tgt["min"], tgt["max"]
        if fc < lo:
            st, d = "WARN", f"{fc:.0f}fc avg < target {lo}-{hi}fc (UNDER-lit — add/raise ambient)"
        elif fc > hi:
            st, d = "WARN", f"{fc:.0f}fc avg > target {lo}-{hi}fc (OVER-lit — fewer/dimmer ambient or add dimming)"
        else:
            st, d = "PASS", f"{fc:.0f}fc avg within target {lo}-{hi}fc"
        out.append({"status": st, "check": f"ambient illuminance ({rtype})",
                    "detail": f"{d}  [lumen method, CU {cu}, LLF {llf}]"})
    else:
        out.append({"status": "WARN", "check": f"ambient illuminance ({rtype})",
                    "detail": "no ambient fixtures or zero area — cannot verify IES level"})

    # 2) CCT comfort band + CRI floor, per fixture TYPE
    type_rows, _ = lighting.type_table(fixtures)
    cct_tbl = L.get("cct_recommended_k", {}) or {}
    band = cct_tbl.get(rtype) or cct_tbl.get("default", {"min": 2700, "max": 4000})
    cri_min = L.get("cri_min", 90)
    for t in type_rows:
        if t["cct_k"] > band["max"]:
            out.append({"status": "WARN", "check": f"CCT type {t['tag']}",
                        "detail": f"{t['cct_k']}K cooler than {band['min']}-{band['max']}K for a {rtype}"})
        elif t["cct_k"] < band["min"]:
            out.append({"status": "WARN", "check": f"CCT type {t['tag']}",
                        "detail": f"{t['cct_k']}K warmer than {band['min']}-{band['max']}K for a {rtype}"})
        if t["cri"] < cri_min:
            out.append({"status": "WARN", "check": f"CRI type {t['tag']}",
                        "detail": f"CRI {t['cri']} < {cri_min} (colours/finishes render poorly)"})

    # 3) layering — a primary room wants ambient + at least one of task/accent (KB §6.1)
    layers = {f.get("layer") for f in fixtures}
    if rtype in {"living", "bedroom", "kitchen", "dining", "office"}:
        ok = ("ambient" in layers) and bool(layers & {"task", "accent"})
        present = sorted(l for l in layers if l)
        out.append({"status": "PASS" if ok else "WARN", "check": f"lighting layers ({rtype})",
                    "detail": f"layers={present} (want ambient + task/accent)"})
    return out


def report(room, items, label="", extra=None):
    res = check(room, items)
    if extra:
        res = res + list(extra)
    icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX"}  # ASCII: survives any console
    print(f"\n=== clearance report {label} — room {room.W:.0f}x{room.D:.0f}\", ceiling {room.H:.0f}\" ===")
    for r in res:
        print(f"  [{icon[r['status']]}] {r['check']}: {r['detail']}")
    fails = sum(r["status"] == "FAIL" for r in res)
    warns = sum(r["status"] == "WARN" for r in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")
    print(f"  -> {verdict}  ({fails} fail, {warns} warn)")
    print("  (v0.1 rules are DRAFT — verify vs Panero & Zelnik + local code before client use)")
    return verdict


def load_spec(path):
    """Load a room SPEC JSON (the same artifact build_room.py / .rb materialize)."""
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    r = spec["room"]
    room = Room(r["width_in"], r["depth_in"], r["ceiling_in"], door=r.get("door"))
    items = [Item(it.get("name", it.get("kind", "item")), it.get("kind", "item"),
                  it["x"], it["y"], it["w"], it["d"])
             for it in spec.get("items", [])]
    return room, items, spec


if __name__ == "__main__":
    # A spec path validates that spec; otherwise run the built-in demos.
    arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    if arg:
        room, items, _spec = load_spec(arg)
        report(room, items, os.path.basename(arg), extra=check_lighting(_spec))
    else:
        # Demo A: a sensible 14x16' living room — should PASS.
        room = Room(14 * 12, 16 * 12, 96)
        good = [
            Item("sofa", "sofa", 24, 12, 84, 36),
            Item("coffee table", "coffee_table", 45, 64, 42, 22),   # ~16" off sofa front
            Item("rug", "rug", 18, 6, 96, 84),
        ]
        report(room, good, "A (good living room)")

        # Demo B: same room, coffee table shoved too far + a chair outside bounds.
        bad = [
            Item("sofa", "sofa", 24, 12, 84, 36),
            Item("coffee table", "coffee_table", 45, 96, 42, 22),   # too far from sofa
            Item("armchair", "armchair", 150, 150, 30, 30),         # pokes past 168x192
        ]
        report(room, bad, "B (problem layout)")
