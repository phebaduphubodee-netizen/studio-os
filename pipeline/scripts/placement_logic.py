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

PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"

TV_STANDALONE_KINDS = {"tv", "tv_console", "tv_panel"}   # a real, positioned TV
TV_FUSED_KINDS = {"headboard_tv", "tv_feature"}          # TV fused into a wall/headboard
_TV_NAME_RE = re.compile(r"\b(tv|television)\b|ทีวี", re.IGNORECASE)

BED_KINDS = {"bed"}
SEAT_KINDS = {"sofa", "loveseat"}            # primary lounge seat (a living room's "viewer")
VIEW_MIN_MM, VIEW_MAX_MM = 1200.0, 5000.0    # sane TV viewing distance (heuristic)


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


RULES = [_rule_tv_positioned, _rule_tv_faces_viewer, _rule_tv_not_over_viewer,
         _rule_tv_viewing_distance, _rule_door_vs_bed_head]


def _worst(statuses):
    for s in (FAIL, WARN, PASS):
        if s in statuses:
            return s
    return UNWIRED


def check(spec):
    """Run the human-usage placement rules over a room spec. Returns
    {status, findings:[{rule,status,detail}], applicable, tv_status, viewer_kind}."""
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
