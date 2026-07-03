#!/usr/bin/env python3
"""placement_logic.py — deterministic HUMAN-USAGE placement checks (design correctness).

M3.2 (2026-07-03) proved the LLM judge gates on PHOTOREALISM, not design correctness:
a practicing designer REWORKed all 26 golden renders, repeatedly on PLACEMENT logic
the judge can't see — the TV ("TV ไม่ควรอยู่ข้างเตียง" GS-11; "TV อยู่หัวเตียง ให้ใคร
ดู? เงยคอดูหรอ?" GS-24), the entry door on the headboard wall (GS-01), armchairs that
face nothing (GS-03/26). See docs/functional-correctness-layer.md.

ROOT CAUSE for the TV: it has NO position in the spec — fused into `headboard_tv` /
a `tv_feature` wall — so Gemini paints the screen wherever, often behind the head. Fix
= (1) give it real coordinates so build_room materialises a control mass on the RIGHT
wall, and (2) THIS module — check placements against human-usage rules BEFORE the paid
render, deterministically: no model, no render, no (decalibrated) judge, unit-testable.

Extensible rule set. v1 = TV vs the primary viewer (a bed OR the main sofa) + the entry
door vs the bed's head. Pure stdlib. PASS/WARN/FAIL/UNWIRED mirror the gate vocabulary;
a MISSING / fused position (an element the render would otherwise invent) is a FAIL,
never a silent pass.

Coordinate model = room-spec@0.2: x,y = SW corner (mm), w along X, d along Y, y-up,
origin SW. A piece's FRONT faces -Y at rot 0 (furniture.py convention); `rot` (deg,
CCW about +Z) turns it. A bed's FOOT and a sofa's SEAT both = the front.
"""
import math
import re

import ergonomics_ref as ergo   # cited ergonomic constants (NLM DR 5de4bb36)

PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"

TV_STANDALONE_KINDS = {"tv", "tv_console", "tv_panel"}   # a real, positioned TV
TV_FUSED_KINDS = {"headboard_tv", "tv_feature"}          # TV fused into a wall/headboard
_TV_NAME_RE = re.compile(r"\b(tv|television)\b|ทีวี", re.IGNORECASE)

BED_KINDS = {"bed"}
SEAT_KINDS = {"sofa", "loveseat"}            # primary lounge seat (a living room's "viewer")
SEATING_KINDS = {"sofa", "loveseat", "armchair", "chair", "lounge_chair", "accent_chair"}
CONVERSATION_FOCAL_KINDS = {"coffee_table", "round_table"}   # what lounge seating orients toward
VIEW_MIN_MM, VIEW_MAX_MM = ergo.TV_VIEW_DIST_MM   # SMPTE/THX comfort band (ergonomics_ref)

# bathroom fixture families for the GS-05 use-frequency + wet/dry rule
BATH_BASIN_KINDS = {"vanity", "vanity_double", "basin", "lavatory", "washbasin", "sink"}
BATH_WC_KINDS = {"wc", "toilet"}
BATH_WET_KINDS = {"shower", "tub", "bathtub"}


# ---------- geometry ----------
def _footprint(el):
    """Axis-aligned (x0,y0,x1,y1) mm, honoring a 90/270 w/d swap (matches
    suite_clearance; other angles use the unrotated rect)."""
    x, y = float(el["x"]), float(el["y"])
    w, d = float(el["w"]), float(el["d"])
    if int(round(float(el.get("rot", 0) or 0))) % 180 == 90:
        w, d = d, w
    return x, y, x + w, y + d


def _center(el):
    x0, y0, x1, y1 = _footprint(el)
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def _front_vec(rot_deg):
    """Unit FRONT direction: base -Y at rot 0, rotated CCW by rot_deg about +Z."""
    r = math.radians(float(rot_deg or 0))
    return math.sin(r), -math.cos(r)          # (0,-1) rotated


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _wall_in_dir(dx, dy):
    """Which perimeter wall a cardinal-ish direction points at."""
    return ("east" if dx > 0 else "west") if abs(dx) >= abs(dy) else ("north" if dy > 0 else "south")


# ---------- units ----------
IN_TO_MM = 25.4


def _is_inch(spec):
    """A room-spec@0.1 (inch, rect) — clearance_check's own discriminant."""
    return "width_in" in (spec.get("room") or {})


def _normalize(spec):
    """Return an mm spec the rules can consume in ONE unit. @0.2 (outline_mm) passes
    through untouched. @0.1 (inch, width_in): scale every element ×25.4 and synthesize
    the mm outline + the materializer's south-wall entry door (build_room/clearance_check
    centre the entry door on the south wall), so the SAME rules — and the mm ergonomic
    bands — apply. No mutation of the caller's spec (inch path deep-copies fields)."""
    if not _is_inch(spec):
        return spec
    r = spec.get("room") or {}
    W = float(r.get("width_in", 0) or 0) * IN_TO_MM
    D = float(r.get("depth_in", 0) or 0) * IN_TO_MM

    def scale(el):
        e = dict(el)
        for k in ("x", "y", "w", "d", "h"):
            if e.get(k) is not None:
                try:
                    e[k] = float(e[k]) * IN_TO_MM
                except (TypeError, ValueError):
                    pass
        return e

    out = {"room": {"outline_mm": [[0, 0], [W, 0], [W, D], [0, D]], "type": r.get("type")},
           "items": [scale(it) for it in spec.get("items", [])],
           "builtins": [scale(b) for b in spec.get("builtins", [])],
           "subrooms": spec.get("subrooms", [])}   # @0.1 has none -> bathroom rule no-ops
    dw = float((r.get("door") or {}).get("w_in", 32) or 32) * IN_TO_MM
    out["door"] = {"wall": "south", "x": max(0.0, (W - dw) / 2.0), "y": 0.0, "w": dw}
    return out


# ---------- element finders ----------
def _iter_elements(spec):
    for grp in ("items", "builtins"):
        for el in spec.get(grp, []):
            yield el


def find_bed(spec):
    beds = [el for el in _iter_elements(spec) if el.get("kind") in BED_KINDS]
    return max(beds, key=lambda b: float(b["w"]) * float(b["d"]), default=None)


def find_primary_viewer(spec):
    """The element a TV should face: the bed (bedroom) else the largest sofa (living).
    Returns (element, front_vec, kind) or (None, None, None)."""
    bed = find_bed(spec)
    if bed is not None:
        return bed, _front_vec(bed.get("rot", 0)), "bed"
    seats = [el for el in _iter_elements(spec) if el.get("kind") in SEAT_KINDS]
    if seats:
        s = max(seats, key=lambda e: float(e["w"]) * float(e["d"]))
        return s, _front_vec(s.get("rot", 0)), "sofa"
    return None, None, None


def find_tv(spec):
    """Return (element, status) where status in {'positioned','fused','absent'}."""
    standalone = [el for el in _iter_elements(spec) if el.get("kind") in TV_STANDALONE_KINDS]
    if standalone:
        return standalone[0], "positioned"
    for el in _iter_elements(spec):
        if el.get("kind") in TV_FUSED_KINDS or _TV_NAME_RE.search(str(el.get("name", ""))):
            return el, "fused"
    return None, "absent"


def _door_wall(spec):
    d = spec.get("door")
    if not d:
        return None
    if d.get("wall"):
        return str(d["wall"]).lower()
    # infer from the door's position against the room bbox
    out = (spec.get("room") or {}).get("outline_mm")
    if not out:
        return None
    xs = [p[0] for p in out]; ys = [p[1] for p in out]
    dx = float(d.get("x", 0)); dy = float(d.get("y", 0))
    near = {"south": abs(dy - min(ys)), "north": abs(dy - max(ys)),
            "west": abs(dx - min(xs)), "east": abs(dx - max(xs))}
    return min(near, key=near.get)


# ---------- rules: each takes (spec, ctx) -> (rule_id, status, detail) or None ----------
def _rule_tv_positioned(spec, ctx):
    tv, st = ctx["tv"], ctx["tv_status"]
    if st == "positioned":
        return ("tv_positioned", PASS, "TV has its own coordinates (build_room can place the control mass)")
    if st == "fused":
        return ("tv_positioned", FAIL,
                f"TV is FUSED into '{tv.get('kind') or tv.get('name')}' — no independent position, so "
                f"the render pass decides where the screen lands (GS-24: TV behind/above the head). "
                f"Split it into a standalone 'tv' facing the {ctx['viewer_kind'] or 'seat'}.")
    return None  # absent -> nothing named a TV -> N/A (not a silent pass)


def _rule_tv_faces_viewer(spec, ctx):
    tv, st, viewer, front = ctx["tv"], ctx["tv_status"], ctx["viewer"], ctx["viewer_front"]
    if st != "positioned" or viewer is None:
        return None
    vcx, vcy = _center(viewer)
    tcx, tcy = _center(tv)
    dot = (tcx - vcx) * front[0] + (tcy - vcy) * front[1]
    if dot <= 0:
        return ("tv_faces_viewer", FAIL,
                f"TV is BEHIND the {ctx['viewer_kind']}'s facing side (head/back) — you would look "
                f"backward to watch. Move it to the wall the {ctx['viewer_kind']} faces "
                f"(front {front[0]:+.0f},{front[1]:+.0f}).")
    return ("tv_faces_viewer", PASS, f"TV is in front of the {ctx['viewer_kind']} (in the line of sight)")


def _rule_tv_not_over_viewer(spec, ctx):
    tv, st, viewer = ctx["tv"], ctx["tv_status"], ctx["viewer"]
    if st != "positioned" or viewer is None:
        return None
    if _overlap(_footprint(tv), _footprint(viewer)):
        return ("tv_not_over_viewer", FAIL,
                f"TV footprint overlaps the {ctx['viewer_kind']} in plan — mounted over it (crane-neck).")
    return ("tv_not_over_viewer", PASS, f"TV is clear of the {ctx['viewer_kind']} footprint")


def _rule_tv_viewing_distance(spec, ctx):
    tv, st, viewer = ctx["tv"], ctx["tv_status"], ctx["viewer"]
    if st != "positioned" or viewer is None:
        return None
    vcx, vcy = _center(viewer)
    tcx, tcy = _center(tv)
    dist = math.hypot(tcx - vcx, tcy - vcy)
    if dist < VIEW_MIN_MM:
        return ("tv_viewing_distance", WARN, f"{ctx['viewer_kind']}–TV {dist:.0f} mm is very close (<{VIEW_MIN_MM:.0f})")
    if dist > VIEW_MAX_MM:
        return ("tv_viewing_distance", WARN, f"{ctx['viewer_kind']}–TV {dist:.0f} mm is far (>{VIEW_MAX_MM:.0f})")
    return ("tv_viewing_distance", PASS, f"{ctx['viewer_kind']}–TV {dist:.0f} mm within {VIEW_MIN_MM:.0f}–{VIEW_MAX_MM:.0f}")


def _rule_door_vs_bed_head(spec, ctx):
    bed, dw = ctx["bed"], ctx["door_wall"]
    if bed is None or dw is None:
        return None
    fx, fy = _front_vec(bed.get("rot", 0))       # foot dir
    head_wall = _wall_in_dir(-fx, -fy)           # head = opposite the foot
    if head_wall == dw:
        return ("door_vs_bed_head", FAIL,
                f"the entry door and the bed's HEAD share the '{dw}' wall — the door opens by the "
                f"sleeper's head (GS-01). Put the headboard on a different wall.")
    return ("door_vs_bed_head", PASS, f"bed head ('{head_wall}') is clear of the door wall ('{dw}')")


def _rule_furniture_dimensions(spec, ctx):
    # WARN (advisory, never FAIL) when a piece's size/height is outside the ergonomic
    # norm — the GS-02/06 family ("สัดส่วนไม่ได้ / เฟอร์ฯใหญ่ไป / ที่นั่งสูงเกิน").
    # Values from ergonomics_ref (NLM DR 5de4bb36). Overall chair/sofa `h` is the
    # backrest not the seat, so seat-height is intentionally NOT checked here.
    issues, checked = [], False
    for el in _iter_elements(spec):
        k = el.get("kind")
        if k in ergo.TABLE_H_MM:
            checked = True
            lo, hi = ergo.TABLE_H_MM[k]
            h = float(el.get("h", 0) or 0)
            if h and not (lo <= h <= hi):
                issues.append(f"{k} height {h:.0f}mm (norm {lo}–{hi})")
        elif k == "wardrobe":
            checked = True
            lo, hi = ergo.WARDROBE_DEPTH_MM
            dep = min(float(el.get("w", 0) or 0), float(el.get("d", 0) or 0))
            if dep and not (lo <= dep <= hi):
                issues.append(f"wardrobe depth {dep:.0f}mm (norm {lo}–{hi})")
        elif k == "bed":
            checked = True
            name, (bw, bl), ok, worst = ergo.nearest_bed_size(el.get("w", 0), el.get("d", 0))
            if not ok:
                issues.append(f"bed {float(el['w']):.0f}×{float(el['d']):.0f}mm off standard "
                              f"(nearest {name} {bw}×{bl}, off {worst:.0f}mm)")
    if issues:
        return ("furniture_dimensions", WARN, "; ".join(issues))
    if checked:
        return ("furniture_dimensions", PASS, "furniture sizes/heights within ergonomic norms")
    return None   # no dimensionable piece (table/wardrobe/bed) -> not a silent pass


def _subroom_door_center(sr):
    d = sr.get("door")
    if not d:
        return None
    x, y, w = float(d.get("x", 0)), float(d.get("y", 0)), float(d.get("w", 0))
    wall = str(d.get("wall", "")).lower()
    if wall in ("south", "north"):
        return (x + w / 2.0, y)
    if wall in ("east", "west"):
        return (x, y + w / 2.0)
    return (x, y)


def _rule_bathroom_logic(spec, ctx):
    # GS-05 ("สลับโถ/อ่างตามการใช้บ่อย + แยกโซนเปียกแห้ง"): fixtures ordered by use
    # frequency — basin (most-used) nearest the entry, WC intermediate, shower/tub
    # deepest (the wet zone). Deterministic geometry per bathroom subroom vs its door.
    # Clearance NUMBERS stay with suite_clearance/codes-th; this checks the LOGIC.
    details, checked = [], False
    for sr in spec.get("subrooms", []):
        fixtures = sr.get("fixtures", [])
        door = _subroom_door_center(sr)
        basins = [f for f in fixtures if f.get("kind") in BATH_BASIN_KINDS]
        wcs = [f for f in fixtures if f.get("kind") in BATH_WC_KINDS]
        wets = [f for f in fixtures if f.get("kind") in BATH_WET_KINDS]
        if door is None or not basins or not (wcs or wets):
            continue
        checked = True
        name = sr.get("name", "bath")

        def _d(f):
            cx, cy = _center(f)
            return math.hypot(cx - door[0], cy - door[1])

        basin_near = min(_d(b) for b in basins)
        intruders = sorted({f.get("kind") for f in (wcs + wets) if _d(f) < basin_near - 50})
        if intruders:
            details.append((FAIL, f"{name}: {', '.join(intruders)} sits nearer the entry than the "
                                  f"basin — the basin is the most-used fixture and belongs closest (GS-05)"))
        if wets:
            dry = basins + wcs
            mw = sum(_d(f) for f in wets) / len(wets)
            md = sum(_d(f) for f in dry) / len(dry)
            if mw <= md:
                details.append((WARN, f"{name}: the wet zone (shower/tub) is not pushed to the back "
                                      f"(wet mean {mw:.0f} ≤ dry mean {md:.0f} mm) — GS-05 wet/dry zoning"))
    if not checked:
        return None
    if not details:
        return ("bathroom_logic", PASS, "bathroom fixtures follow use-frequency ordering + wet/dry zoning")
    status = FAIL if any(s == FAIL for s, _ in details) else WARN
    return ("bathroom_logic", status, "; ".join(t for _, t in details))


def _rule_seating_faces_focal(spec, ctx):
    # GS-03/26 ("เก้าอี้หันหน้าเข้าไหน? ไม่มีอะไรให้มอง"): a lounge seat should orient
    # toward a focal — a coffee/round table, a positioned TV, or another seat (a
    # conversation group). WARN (advisory): build_room AUTO-FACES a seat that carries no
    # `rot` to the focal, so this only flags (a) a seat with NO focal to face at all, and
    # (b) an EXPLICIT rot that points away from every focal (the spec fighting the intent;
    # the .rb materializer honours rot). A seat facing ANY focal passes.
    seats = [el for el in _iter_elements(spec) if el.get("kind") in SEATING_KINDS]
    if not seats:
        return None
    tables = [el for el in _iter_elements(spec) if el.get("kind") in CONVERSATION_FOCAL_KINDS]
    base_focals = [_center(t) for t in tables]
    if ctx["tv_status"] == "positioned":
        base_focals.append(_center(ctx["tv"]))
    issues = []
    for s in seats:
        scx, scy = _center(s)
        focals = base_focals + [_center(o) for o in seats if o is not s]
        if not focals:
            issues.append(f"{s.get('kind')} faces nothing — no coffee/round table, positioned "
                          f"TV, or other seat to orient toward")
            continue
        if s.get("rot") is None:
            continue   # no explicit orientation -> build_room auto-faces it to the focal
        fx, fy = _front_vec(s.get("rot", 0))
        if not any((cx - scx) * fx + (cy - scy) * fy > 0 for cx, cy in focals):
            issues.append(f"{s.get('kind')} (rot {float(s.get('rot', 0)):.0f}) faces away from every "
                          f"focal (table/TV/other seat) — orient it toward the group")
    if issues:
        return ("seating_faces_focal", WARN, "; ".join(issues))
    return ("seating_faces_focal", PASS, "lounge seating is oriented toward a focal (table/TV/other seat)")


RULES = [_rule_tv_positioned, _rule_tv_faces_viewer, _rule_tv_not_over_viewer,
         _rule_tv_viewing_distance, _rule_door_vs_bed_head, _rule_furniture_dimensions,
         _rule_bathroom_logic, _rule_seating_faces_focal]


def _worst(statuses):
    for s in (FAIL, WARN, PASS):
        if s in statuses:
            return s
    return UNWIRED


def check(spec):
    """Run the human-usage placement rules over a room spec. Returns
    {status, findings:[{rule,status,detail}], applicable, tv_status, viewer_kind}.
    @0.1 inch specs are normalized to mm first, so one rule set serves both schemas."""
    spec = _normalize(spec)
    bed = find_bed(spec)
    viewer, viewer_front, viewer_kind = find_primary_viewer(spec)
    tv, tv_status = find_tv(spec)
    ctx = {"bed": bed, "viewer": viewer, "viewer_front": viewer_front,
           "viewer_kind": viewer_kind, "tv": tv, "tv_status": tv_status,
           "door_wall": _door_wall(spec)}
    findings = []
    for rule in RULES:
        r = rule(spec, ctx)
        if r is not None:
            findings.append({"rule": r[0], "status": r[1], "detail": r[2]})
    status = _worst([f["status"] for f in findings]) if findings else UNWIRED
    return {"status": status, "findings": findings,
            "applicable": tv_status != "absent" or bed is not None,
            "tv_status": tv_status, "viewer_kind": viewer_kind, "has_bed": bed is not None}


def report(spec, label=""):
    """FUNCTION-layer gate result in the SAME (results, verdict) shape as
    suite_clearance.report / the clearance_check gate, so placement drops into the
    existing PRE-RENDER gate machinery (make_all, repair_loop Gate 0, suite_package).

    verdict: FAIL if any rule FAILs (a human-usage breach — abort before a paid
    render), REVIEW if any WARN, PASS if rules ran clean, UNWIRED if NOTHING applied
    (no TV and no bed — honest, never a silent pass). Each check id is prefixed
    'function:' so it never collides with a geometry check of the same name."""
    r = check(spec)
    results = [{"status": f["status"], "check": f"function:{f['rule']}", "detail": f["detail"]}
               for f in r["findings"]]
    if not r["findings"]:
        verdict = UNWIRED
    elif any(f["status"] == FAIL for f in r["findings"]):
        verdict = FAIL
    elif any(f["status"] == WARN for f in r["findings"]):
        verdict = "REVIEW"
    else:
        verdict = PASS
    return results, verdict


def format_report(spec, name=""):
    r = check(spec)
    lines = [f"placement_logic: {name or 'spec'} -> {r['status']}"
             f"  (tv={r['tv_status']}, viewer={r['viewer_kind'] or 'none'})"]
    for f in r["findings"]:
        mark = {PASS: "ok  ", WARN: "WARN", FAIL: "FAIL"}.get(f["status"], f["status"])
        lines.append(f"  [{mark}] {f['rule']}: {f['detail']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("usage: python placement_logic.py SPEC.json")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Thai names on a cp1252 console
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    print(format_report(spec, sys.argv[1]))
    sys.exit(1 if check(spec)["status"] == FAIL else 0)
