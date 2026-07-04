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
import camera_config             # the SHARED eye-camera solve (also used by build_room)

PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"

TV_STANDALONE_KINDS = {"tv", "tv_console", "tv_panel"}   # a real, positioned TV
TV_FUSED_KINDS = {"headboard_tv", "tv_feature"}          # TV fused into a wall/headboard
TV_WALL_MOUNT_KINDS = {"tv_panel"}                       # explicitly wall-hung (needs a mount height). A generic
                                                         # "tv" is ambiguous (could be a console) and a "tv_console"
                                                         # sits on a unit — neither is faulted for a missing mount.
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

# kitchen work-triangle vertices (NKBA). NOTE: "sink" is ALSO a bath basin kind, but the
# kitchen rule scans the MAIN room (items/builtins) while bathroom_logic scans SUBROOM
# fixtures — location disambiguates them, so a bath basin never counts as a kitchen sink.
KITCHEN_SINK_KINDS = {"sink", "kitchen_sink"}
KITCHEN_COOK_KINDS = {"cooktop", "stove", "hob", "range", "hotplate", "range_cooker"}
KITCHEN_FRIDGE_KINDS = {"refrigerator", "fridge"}
K_LEG_MIN, K_LEG_MAX = ergo.KITCHEN_TRIANGLE_LEG_MM   # 1219–2743 mm per leg
K_PERIM_MAX = ergo.KITCHEN_TRIANGLE_PERIM_MAX_MM      # ≤ 7925 mm total


# ---------- geometry ----------
def _footprint(el):
    """Axis-aligned (x0,y0,x1,y1) mm, honoring a 90/270 w/d swap (matches
    suite_clearance; other angles use the unrotated rect). Missing coords read as 0 —
    a malformed element must not crash a pre-render gate (it degrades, never throws)."""
    x, y = float(el.get("x", 0) or 0), float(el.get("y", 0) or 0)
    w, d = float(el.get("w", 0) or 0), float(el.get("d", 0) or 0)
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
           "subrooms": []}   # @0.1 has no sub-rooms; never run the mm bathroom rule on inch coords
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
    return max(beds, key=lambda b: float(b.get("w", 0) or 0) * float(b.get("d", 0) or 0), default=None)


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
    """(element, status). 'positioned' = its own coords; 'fused' = a KIND that melds the
    TV into a wall/headboard (the GS-24 defect — a hard FAIL); 'named_only' = an element
    merely NAMED like a TV (a hint, not a discrete screen — WARN, so a 'ตู้ทีวี' console
    can't hard-block a deliverable over a naming coincidence); 'absent'. Kind is decisive;
    a name is only ever a soft signal."""
    standalone = [el for el in _iter_elements(spec) if el.get("kind") in TV_STANDALONE_KINDS]
    if standalone:
        return standalone[0], "positioned"
    for el in _iter_elements(spec):
        if el.get("kind") in TV_FUSED_KINDS:
            return el, "fused"
    for el in _iter_elements(spec):
        if _TV_NAME_RE.search(str(el.get("name", "") or "")):
            return el, "named_only"
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
    if st == "named_only":
        return ("tv_positioned", WARN,
                f"an element named like a TV ('{tv.get('name')}', kind '{tv.get('kind')}') is not a "
                f"discrete positioned screen — confirm the TV has a controlled position, or model it "
                f"as a standalone 'tv' facing the {ctx['viewer_kind'] or 'seat'}")
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
            bw_, bd_ = float(el.get("w", 0) or 0), float(el.get("d", 0) or 0)
            name, (bw, bl), ok, worst = ergo.nearest_bed_size(bw_, bd_)
            if bw_ and bd_ and not ok:
                issues.append(f"bed {bw_:.0f}×{bd_:.0f}mm off standard "
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
    # GS-03/26 ("เก้าอี้หันหน้าเข้าไหน? ไม่มีอะไรให้มอง"): a lounge seat should orient toward
    # a focal — a coffee/round table, a positioned TV, or another seat (a conversation
    # group). We judge ONLY a seat that (a) carries an EXPLICIT rot and (b) has a focal to
    # face: build_room's auto-face is narrow (hero lounge-zone, no-rot only — build_room.py
    # ~1542) so a no-rot seat's orientation isn't knowable here, and we cannot model a
    # window/view, so a seat with no focal could legitimately face one. Leaving those
    # UNJUDGED (None) beats a false WARN. WARN when an explicitly-rotated seat faces AWAY
    # from every focal (a focal in the front half-plane, dot>0, counts as facing it).
    seats = [el for el in _iter_elements(spec) if el.get("kind") in SEATING_KINDS]
    if not seats:
        return None
    base = [_center(t) for t in _iter_elements(spec) if t.get("kind") in CONVERSATION_FOCAL_KINDS]
    if ctx["tv_status"] == "positioned":
        base.append(_center(ctx["tv"]))
    issues, judged = [], 0
    for s in seats:
        if s.get("rot") is None:
            continue                        # orientation not knowable (auto-face / unset)
        focals = base + [_center(o) for o in seats if o is not s]
        if not focals:
            continue                        # nothing to face -> can't judge (may be a window)
        judged += 1
        scx, scy = _center(s)
        fx, fy = _front_vec(s.get("rot", 0))
        if not any((cx - scx) * fx + (cy - scy) * fy > 0 for cx, cy in focals):
            issues.append(f"{s.get('kind')} (rot {float(s.get('rot', 0)):.0f}) faces away from every "
                          f"focal (table/TV/other seat) — orient it toward the group")
    if issues:
        return ("seating_faces_focal", WARN, "; ".join(issues))
    if judged:
        return ("seating_faces_focal", PASS, "lounge seating is oriented toward a focal (table/TV/other seat)")
    return None


def _rule_kitchen_work_triangle(spec, ctx):
    # NKBA kitchen work-triangle: the sink, cooktop and refrigerator form a triangle whose
    # three legs each measure 1219–2743 mm and whose perimeter is ≤ 7925 mm — a cramped
    # triangle crowds the cook, a stretched one wastes steps. Grounded in
    # knowledge/ergonomics/bathroom-kitchen-planning.md (NLM DR f61fded1; NKBA/Neufert/P&Z),
    # constants in ergonomics_ref. Scans the MAIN room (an open-plan condo kitchen); a
    # bathroom "sink" lives in a subroom (bathroom_logic's scope) so the two never collide.
    # Checkable ONLY when all three vertices exist — else None (a kitchenette / wet-bar is
    # not faulted for a missing vertex, and a non-kitchen room never triggers). The aisle
    # and leg-obstruction checks (bathroom-kitchen-planning.md) need run/opposing-counter
    # grouping the @0.2 spec lacks, so they are out of scope here. Advisory WARN, never FAIL.
    def _biggest(kinds):
        c = [el for el in _iter_elements(spec) if el.get("kind") in kinds]
        return max(c, key=lambda e: float(e.get("w", 0) or 0) * float(e.get("d", 0) or 0), default=None)

    sink, cook, fridge = _biggest(KITCHEN_SINK_KINDS), _biggest(KITCHEN_COOK_KINDS), _biggest(KITCHEN_FRIDGE_KINDS)
    if not (sink and cook and fridge):
        return None
    s, c, f = _center(sink), _center(cook), _center(fridge)
    legs = {"sink–cooktop": math.hypot(s[0] - c[0], s[1] - c[1]),
            "cooktop–fridge": math.hypot(c[0] - f[0], c[1] - f[1]),
            "fridge–sink": math.hypot(f[0] - s[0], f[1] - s[1])}
    perim = sum(legs.values())
    issues = []
    for nm, d in legs.items():
        if d < K_LEG_MIN:
            issues.append(f"{nm} leg {d:.0f} mm < {K_LEG_MIN} (cramped)")
        elif d > K_LEG_MAX:
            issues.append(f"{nm} leg {d:.0f} mm > {K_LEG_MAX} (too far apart)")
    if perim > K_PERIM_MAX:
        issues.append(f"perimeter {perim:.0f} mm > {K_PERIM_MAX} (inefficient — extra steps)")
    if issues:
        return ("kitchen_work_triangle", WARN, "; ".join(issues))
    legs_str = "/".join(f"{d:.0f}" for d in legs.values())
    return ("kitchen_work_triangle", PASS,
            f"work triangle within norm (legs {legs_str} mm, perimeter {perim:.0f} ≤ {K_PERIM_MAX})")


def _rule_seating_clear_of_screen(spec, ctx):
    # Designer 2026-07-04 (GS-03): an armchair placed BETWEEN the main seat and the TV, or
    # under the screen — "เก้าอี้ยังตั้งอยู่ใต้ทีวี", "TV มันอยู่ข้างหลังคนนั่ง เค้าจะดูยังไง?".
    # `seating_faces_focal` only judges a seat's ORIENTATION (and skips no-rot seats); this is
    # the missing POSITION check. Deterministic + orientation-free: flag a SECONDARY lounge
    # seat whose centre falls in the primary-viewer→TV corridor (past the viewer, before the
    # TV, within ~the screen's width of the sightline). Advisory WARN — a seat angled toward
    # the sofa CAN legitimately sit near the TV wall (GS-26), so this flags for the human eye,
    # it does not hard-decide. None when there is no viewer/TV or no secondary seat to judge.
    viewer, tv = ctx.get("viewer"), ctx.get("tv")
    if viewer is None or tv is None:
        return None
    seats = [s for s in (spec.get("items") or [])
             if s.get("kind") in SEATING_KINDS and s is not viewer]
    if not seats:
        return None
    vc, tc = _center(viewer), _center(tv)
    ax, ay = tc[0] - vc[0], tc[1] - vc[1]
    axlen = math.hypot(ax, ay)
    if axlen < 1e-6:
        return None
    ux, uy = ax / axlen, ay / axlen
    screen_half = max(float(tv.get("w", 0) or 0), float(tv.get("d", 0) or 0)) / 2.0
    flagged = []
    for s in seats:
        sc = _center(s)
        t = (sc[0] - vc[0]) * ux + (sc[1] - vc[1]) * uy          # along viewer→TV
        lat = abs(-(sc[0] - vc[0]) * uy + (sc[1] - vc[1]) * ux)  # perpendicular offset
        seat_half = max(float(s.get("w", 0) or 0), float(s.get("d", 0) or 0)) / 2.0
        # in the sightline iff the seat is past the viewer, before the TV, AND its footprint
        # laterally OVERLAPS the screen (screen_half + seat_half) — a seat well to the side
        # provably can't sit under/in front of the screen (GS-26 angled chair, no false WARN).
        # The 0.05*axlen near bound only excludes a seat coincident with the viewer itself.
        if 0.05 * axlen < t < 0.98 * axlen and lat < screen_half + seat_half:
            flagged.append(s.get("name") or s.get("kind"))
    if flagged:
        return ("seating_clear_of_screen", WARN,
                f"{', '.join(flagged)} sit(s) between the main seat and the TV / in front of the screen "
                f"— verify the sightline (the TV must not end up behind whoever sits there; GS-03)")
    return ("seating_clear_of_screen", PASS, "no lounge seat sits in the viewer→TV sightline")


def _rule_tv_mount_height(spec, ctx):
    # Designer 2026-07-04: "ทำไมเอา TV ไปติดไว้ที่พื้น?" — a WALL TV rendered as a floor block.
    # build_room extrudes built-ins from the floor (z=0) unless the spec gives a mount height
    # (mount_mm = base AFF); a wall-hung TV (tv_panel/tv) therefore needs mount_mm so the
    # control mass floats on the wall and the paid render paints a mounted screen (not a slab
    # on the floor). A tv_console (TV on a media unit) is floor-adjacent by design → exempt.
    # WARN, never FAIL: it's a render-fidelity fix, and mount_mm is a young field many specs
    # won't carry yet (a missing mount is a flag to set it, not a reason to block deliverables).
    tv = ctx.get("tv")
    if tv is None:
        return None
    kind = tv.get("kind")
    # a wall-hung panel (tv_panel) always needs a mount; a generic 'tv' only when authored as
    # a BUILT-IN — build_room floats built-ins from z=mount_mm, and a builtin TV is architectural
    # millwork (never a loose console), so an un-mounted one renders as a floor slab. A LOOSE
    # 'tv' (ambiguous) and any 'tv_console' (sits on a unit) stay exempt. (scrutiny 2026-07-04)
    is_wall = (kind in TV_WALL_MOUNT_KINDS
               or (kind == "tv" and any(tv is b for b in (spec.get("builtins") or []))))
    if not is_wall:
        return None
    nm = tv.get("name") or tv.get("kind")
    mount = float(tv.get("mount_mm", 0) or 0)
    h = float(tv.get("h", 0) or 0)
    if mount < 300:
        return ("tv_mount_height", WARN,
                f"wall TV '{nm}' has no mount height (mount_mm={mount:.0f}) — it renders as a "
                f"floor-standing block; set mount_mm (AFF base, ~600–1100 mm for a screen)")
    ceil = float((spec.get("room") or {}).get("ceiling_mm", 2800) or 2800)
    if mount + h > ceil:
        return ("tv_mount_height", WARN,
                f"wall TV '{nm}' top {mount + h:.0f} mm exceeds ceiling {ceil:.0f} mm — lower mount_mm")
    return ("tv_mount_height", PASS,
            f"wall TV mounted at {mount:.0f} mm AFF (base), top {mount + h:.0f} mm — floats on the wall")


CAMERA_MIN_SUBJECT_SHARE = 0.15   # WARN when the framed FOV is >85% bare wall / void


def _rule_camera_has_a_reason(spec, ctx):
    # GS-04/05/22: the eye-camera's framed view must SHOW the room — a real subject, not a
    # blank wall ("camera angles that show nothing"). The --eye camera (build_room) aims at
    # the hero from the farthest clear standing spot; this rule runs the SAME solve
    # (camera_config.solve_eye_camera — one definition, shared with the materializer) and:
    #   (1) WARNs if no valid shot exists (no loose subject to aim at / no clear line of
    #       sight) — build_room --eye would SystemExit at render time; flag it here early;
    #   (2) WARNs if the horizontal FOV is mostly furniture-free (a dead-wall frame).
    # ADVISORY ONLY — this rule returns WARN/PASS/None, NEVER FAIL. The eye camera is OPT-IN
    # (build_room --eye); the automated pipeline (make_all / suite_package / repair_loop)
    # renders the OVERVIEW camera by default, and @0.1 inch specs render via build_rect which
    # has NO eye path at all. So a "no eye shot" must never hard-abort the shared FUNCTION gate
    # (that false-blocked non-eye deliverables — scrutiny 2026-07-04). The HARD guard against a
    # dead-wall eye render stays build_room's own loud SystemExit at actual --eye render time;
    # here we only surface it as a REVIEW so a human eye-shot batch is warned before spending.
    if ctx.get("is_inch"):                     # @0.1 -> build_rect (add_camera_and_light), no eye camera
        return None
    outline_m = camera_config.outline_m_of(spec)
    # not applicable unless there is a metric room AND a non-rug LOOSE item to aim at — the
    # --eye camera aims at the largest loose item, so a builtins-only spec (e.g. a kitchen of
    # counters) or a rug-only room is NOT eye-camera-eligible and returns None here (same
    # "no subject -> None" discipline as the kitchen/bathroom rules).
    aim_items = [e for e in (spec.get("items") or []) if e.get("kind") != "rug"]
    if not outline_m or not aim_items:
        return None
    try:
        sol = camera_config.solve_eye_camera(spec, outline_m)
    except camera_config.EyeCameraError as e:
        return ("camera_has_a_reason", WARN,
                f"eye camera has no valid shot: {e} — a --eye (client-facing) render would abort; "
                f"the default overview render is unaffected")
    except Exception:                          # malformed element (missing dims, bad outline):
        return None                            # degrade, never throw — geometry/other rules own it
    hero = sol.get("hero") or {}
    hero_nm = hero.get("name") or hero.get("kind") or "subject"
    try:
        share = camera_config.frame_subject_share(spec, sol, outline_m)
    except Exception:
        return None
    # `share` = fraction of the FOV's view directions (bearings) that land on a furniture
    # footprint — a bearing-coverage proxy, NOT framed image area, and it ignores occlusion.
    if share < CAMERA_MIN_SUBJECT_SHARE:
        return ("camera_has_a_reason", WARN,
                f"only {share * 100:.0f}% of the view directions hit furniture (mostly bare wall) — aims at "
                f"{hero_nm} from {sol['standoff_m']:.1f} m at {sol['lens_mm']:.0f} mm; verify it shows the room")
    return ("camera_has_a_reason", PASS,
            f"eye camera frames {hero_nm} from {sol['standoff_m']:.1f} m "
            f"({sol['lens_mm']:.0f} mm; {share * 100:.0f}% of view directions on a subject)")


RULES = [_rule_tv_positioned, _rule_tv_faces_viewer, _rule_tv_not_over_viewer,
         _rule_tv_viewing_distance, _rule_door_vs_bed_head, _rule_furniture_dimensions,
         _rule_bathroom_logic, _rule_seating_faces_focal, _rule_seating_clear_of_screen,
         _rule_kitchen_work_triangle, _rule_tv_mount_height, _rule_camera_has_a_reason]


def _worst(statuses):
    for s in (FAIL, WARN, PASS):
        if s in statuses:
            return s
    return UNWIRED


def check(spec):
    """Run the human-usage placement rules over a room spec. Returns
    {status, findings:[{rule,status,detail}], applicable, tv_status, viewer_kind}.
    @0.1 inch specs are normalized to mm first, so one rule set serves both schemas."""
    is_inch = _is_inch(spec)            # capture BEFORE _normalize erases width_in (camera rule needs it)
    spec = _normalize(spec)
    bed = find_bed(spec)
    viewer, viewer_front, viewer_kind = find_primary_viewer(spec)
    tv, tv_status = find_tv(spec)
    ctx = {"bed": bed, "viewer": viewer, "viewer_front": viewer_front,
           "viewer_kind": viewer_kind, "tv": tv, "tv_status": tv_status,
           "door_wall": _door_wall(spec), "is_inch": is_inch}
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
