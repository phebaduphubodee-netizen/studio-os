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
import re
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


MM_PER_IN = 25.4


class Room:
    def __init__(self, width_in, depth_in, ceiling_in, door=None, rtype=None,
                 floor_to_floor_mm=None):
        self.W, self.D, self.H = float(width_in), float(depth_in), float(ceiling_in)
        self.door = door
        self.rtype = rtype                      # spec room.type — gates typed statutory checks
        self.f2f_mm = float(floor_to_floor_mm) if floor_to_floor_mm is not None else None

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


def _thai(key):
    """(value, cite) from RULES['thai_code_minimums'][key]; (None, '') if absent."""
    node = _r("thai_code_minimums", key, default=None)
    if isinstance(node, dict):
        return node.get("value"), node.get("cite", "")
    return None, ""


# Wet-room vocabulary — SUBSTRING match, same tokens as suite_clearance._WET
# (exact-match on 4 strings let 'ensuite'/'powder'/Thai names hit the habitable
# ladder = the round-1 false-FAIL BLOCKER back through the vocab door).
_WET = ("bath", "ensuite", "toilet", "wc", "shower", "powder", "ห้องน้ำ", "ส้วม", "อาบน้ำ")


def _is_wet(rtype_l):
    return any(t in rtype_l for t in _WET)


# ข้อ 20 typing — doctrine regex (suite_clearance): 'bedroom', 'master_bedroom',
# 'bedroom2', 'bed' all count; 'bath' does not.
_BED_RE = re.compile(r"(^|[^a-z])bed(room)?($|[^a-z])")


def _fixture_evidence(items):
    """(has_wc, has_wash) from item KINDS (substring: 'shower_stall', 'walk_in_tub')
    + THAI-ONLY name markers, mirroring suite_clearance._bath_checks. English names
    deliberately do NOT count — a kind='accessory' named "shower curtain" must not
    upgrade the tier and drop the 900 mm separated-width floor (verified defect)."""
    has_wc = has_wash = False
    for it in items:
        k = (it.kind or "").lower()
        n = it.name or ""
        if k in ("wc", "toilet") or "ชักโครก" in n or "ส้วม" in n:
            has_wc = True
        if "shower" in k or "tub" in k or "ฝักบัว" in n or "อ่างอาบ" in n or "อาบน้ำ" in n:
            has_wash = True
    return has_wc, has_wash


def check(room, items):
    out = []

    def add(status, name, detail):
        out.append({"status": status, "check": name, "detail": detail})

    # 1) ceiling + typed statutory floors — same doctrine as suite_clearance v0.4.x.
    #    WET rooms are the statute's own exception: ฉ.39 ข้อ 9 and ข้อ 22's ห้องน้ำ row
    #    are both พื้นถึงเพดาน (clear height IS the basis, decisive) — the IRC line and
    #    the 2600 habitable ladder must NOT fire there. Non-wet rooms: (a) ergonomic
    #    IRC clear-height reference; (b) ข้อ 22 on its OWN basis (ระยะดิ่ง พื้นถึงพื้น) —
    #    a floor_to_floor field proves/refutes; clear height proves a fortiori, never
    #    a breach; tier per rtype (ระเบียง 2200; office/dining 3000 = WARN-only).
    rtype_l = (room.rtype or "").lower()
    wet = _is_wet(rtype_l)
    balcony = ("balcony" in rtype_l) or ("ระเบียง" in rtype_l)   # terrace = 2600 per doctrine
    clear_mm = room.H * MM_PER_IN
    area_m2 = (room.W * MM_PER_IN / 1000.0) * (room.D * MM_PER_IN / 1000.0)
    narrow_mm = min(room.W, room.D) * MM_PER_IN

    if wet:
        bc_min, bc_cite = _thai("bathroom_floor_to_ceiling_min_mm")
        if bc_min:
            add("PASS" if clear_mm >= bc_min else "FAIL", "bath ceiling (Thai ฉ.39)",
                f"clear {clear_mm:.0f} mm vs {bc_min:.0f} min, basis พื้นถึงเพดานจริง — "
                f"decisive; ข้อ 22 wet row agrees ({bc_cite})")
        # ฉ.39 area tiers: combined 1.5 m² vs separated 0.9 m² + 900 mm width.
        # AUTHORED wc+wash fixtures always take the combined tier — a type label
        # can neither upgrade NOR downgrade real fixture evidence (both directions
        # verified as defects); typed wc/toilet gates only the inference path.
        # Unknown -> dual-tier honesty incl. the every-reading FAIL.
        has_wc, has_wash = _fixture_evidence(items)
        typed_sep = rtype_l in ("wc", "toilet") or "ส้วม" in rtype_l
        comb_min, comb_cite = _thai("bathroom_combined_area_min_m2")
        sep_a_min, sep_cite = _thai("bathroom_separated_area_min_m2")
        sep_w_min, _ = _thai("bathroom_separated_width_min_mm")
        if comb_min and sep_a_min and sep_w_min:
            if has_wc and has_wash:
                add("PASS" if area_m2 >= comb_min else "FAIL", "bath area (Thai ฉ.39)",
                    f"{area_m2:.2f} m² vs {comb_min} m² min ({area_m2 - comb_min:+.2f}), "
                    f"combined tier (wc+wash fixtures authored) ({comb_cite})")
            elif typed_sep or has_wc or has_wash:
                ok = area_m2 >= sep_a_min and narrow_mm >= sep_w_min
                add("PASS" if ok else "FAIL", "bath area (Thai ฉ.39)",
                    f"{area_m2:.2f} m² vs {sep_a_min} m² + width {narrow_mm:.0f} mm vs "
                    f"{sep_w_min:.0f} min, separated tier ({sep_cite})")
            else:
                if area_m2 < sep_a_min or (area_m2 < comb_min and narrow_mm < sep_w_min):
                    add("FAIL", "bath area (Thai ฉ.39)",
                        f"{area_m2:.2f} m² / width {narrow_mm:.0f} mm — breach under EVERY tier "
                        f"reading (combined needs {comb_min} m²; separated needs {sep_a_min} m² "
                        f"+ {sep_w_min:.0f} mm) ({comb_cite})")
                elif area_m2 >= comb_min and narrow_mm >= sep_w_min:
                    add("PASS", "bath area (Thai ฉ.39)",
                        f"{area_m2:.2f} m² >= {comb_min} m² and width {narrow_mm:.0f} >= "
                        f"{sep_w_min:.0f} mm — compliant under either tier ({comb_cite})")
                else:
                    add("WARN", "bath area (Thai ฉ.39)",
                        f"{area_m2:.2f} m² / width {narrow_mm:.0f} mm — combined-vs-separated "
                        f"tier unresolved (no wc/wash fixtures in spec); one reading passes, "
                        f"one fails ({comb_cite})")
    else:
        # IRC ergonomic reference is a HABITABLE-room tier — a balcony's legal
        # ceiling regime (2200 f2f) sits below it; doctrine emits no IRC row there.
        if not balcony:
            cmin = _r("ceilings_and_heights", "ceiling_min_habitable", "in", default=90)
            add("PASS" if room.H >= cmin else "FAIL", "ceiling height (ergonomic)",
                f"{room.H:.0f}\" vs {cmin}\" min (IRC clear-height reference tier)")
        tier_key = ("balcony_floor_to_floor_min_mm" if balcony
                    else "floor_to_floor_habitable_min_mm")
        f2f_min, f2f_cite = _thai(tier_key)
        if f2f_min:
            if room.f2f_mm is not None:
                add("PASS" if room.f2f_mm >= f2f_min else "FAIL",
                    "ceiling height (Thai ข้อ 22)",
                    f"floor-to-floor {room.f2f_mm:.0f} mm vs {f2f_min:.0f} min ({f2f_cite})")
            elif clear_mm >= f2f_min:
                add("PASS", "ceiling height (Thai ข้อ 22)",
                    f"clear {clear_mm:.0f} mm >= {f2f_min:.0f} floor-to-floor min -> compliant a fortiori ({f2f_cite})")
            else:
                add("WARN", "ceiling height (Thai ข้อ 22)",
                    f"clear {clear_mm:.0f} mm < {f2f_min:.0f} but basis is ระยะดิ่ง พื้นถึงพื้น — cannot prove or refute "
                    f"from clear height; add room.floor_to_floor_mm to the spec ({f2f_cite})")
        # ข้อ 22 office/dining 3000 tier — in-unit interpretation unresolved: WARN
        # only, never FAIL (the rule's own note). Basis = the f2f field, or the
        # PROVEN LOWER BOUND from an a-fortiori clear height (clear >= 2600 proved
        # the 2600 row, but 2600 <= bound < 3000 still cannot prove this tier —
        # the silent [2600,3000) window was a verified round-2 defect).
        if ("office" in rtype_l or "dining" in rtype_l) and f2f_min:
            od_min, od_cite = _thai("office_dining_floor_to_floor_min_mm")
            if od_min:
                basis = room.f2f_mm if room.f2f_mm is not None else (
                    clear_mm if clear_mm >= f2f_min else None)
                if basis is not None and basis >= od_min:
                    add("PASS", "ceiling height (Thai ข้อ 22, office/dining tier)",
                        f"{basis:.0f} mm >= {od_min:.0f} ({od_cite})")
                elif basis is not None:
                    add("WARN", "ceiling height (Thai ข้อ 22, office/dining tier)",
                        f"proven basis {basis:.3f} mm < {od_min:.0f} — 3000 tier's in-unit scope "
                        f"unresolved (vault gap): WARN only, never FAIL ({od_cite})")

    # 1c) bedroom statutory floors — ฉ.55 ข้อ 20 (typed via doctrine regex: catches
    #     master_bedroom/bedroom2/bed). Runs INDEPENDENT of the wet gate — doctrine
    #     order: a 'bedroom_ensuite'-named sleeping room gets wet rows AND bedroom
    #     rows (the wet gate swallowing ข้อ 20 flipped a statutory FAIL to PASS —
    #     verified defect). Valid for @0.1 ONLY on a plain bedroom: the rect schema
    #     has no sub-rooms, and build_room extrudes walls OUTWARD, so net = W x D
    #     as-built. Suite-typed rooms CANNOT get a statutory area verdict here
    #     (ensuite/WIC would be carved) — route to @0.2.
    bed_typed = bool(_BED_RE.search(rtype_l))
    # 'suite' routing fires for bed-typed or non-wet suite names ONLY — plain
    # 'ensuite' (a wet room; "suite" is a substring accident) already got its
    # correct ฉ.39 basis above and must not collect a false routing WARN.
    if "suite" in rtype_l and (bed_typed or not wet):
        add("WARN", "bedroom area (Thai ข้อ 20)",
            f"suite-typed room in @0.1: sub-rooms not representable, gross {area_m2:.2f} m² "
            f"is NOT the statutory net basis — author @0.2 and run suite_clearance.py")
    elif bed_typed:
        area_min, a_cite = _thai("bedroom_area_min_m2")
        narrow_min, n_cite = _thai("bedroom_narrow_side_min_mm")
        if area_min:
            add("PASS" if area_m2 >= area_min else "FAIL", "bedroom area (Thai ข้อ 20)",
                f"{area_m2:.2f} m² vs {area_min} m² min ({area_m2 - area_min:+.2f}), "
                f"net = gross (rect @0.1, no sub-rooms, walls extrude outward) ({a_cite})")
        if narrow_min:
            add("PASS" if narrow_mm >= narrow_min else "FAIL", "bedroom narrow side (Thai ข้อ 20)",
                f"{narrow_mm:.0f} mm vs {narrow_min:.0f} min ({n_cite})")
    elif any((it.kind or "").lower() == "bed" for it in items):
        add("WARN", "bedroom area (Thai ข้อ 20)",
            f"room contains a bed but type {room.rtype!r} is not bedroom-typed — "
            f"ข้อ 20 not evaluated; type the room or confirm it is not a sleeping room")

    # 1b) door fits the wall + under the ceiling. A door wider than the wall or
    #     taller than the ceiling makes the materializers build inverted piers /
    #     a negative-height header (silently-wrong geometry) — catch it HERE.
    if getattr(room, "door", None):
        dwin_raw, dhin_raw = room.door.get("w_in"), room.door.get("h_in")
        dwin = float(dwin_raw or 32)
        dhin = float(dhin_raw or 80)
        add("PASS" if dwin < room.W else "FAIL", "door fits wall width",
            f"door {dwin:.0f}\" vs wall {room.W:.0f}\"")
        add("PASS" if dhin < room.H else "FAIL", "door under ceiling",
            f"door {dhin:.0f}\" vs ceiling {room.H:.0f}\"")
        # STUDIO floor 800/1900 mm — same tier as suite_clearance (no general
        # statutory interior-door minimum: ฉ.55 ข้อ 31 covers fire doors only).
        # A defaulted dimension is NOT verified data — never assert PASS on it.
        if dwin_raw:
            dw_mm = dwin * MM_PER_IN
            add("PASS" if dw_mm >= 800 else "FAIL", "door width (studio floor)",
                f"{dw_mm:.0f} mm vs 800 min (studio floor — not statutory; ฉ.55 ข้อ 31 = fire doors)")
        else:
            add("WARN", "door width (studio floor)",
                "door.w_in not in spec — 32\" assumed for geometry only; floor unverified")
        if dhin_raw:
            dh_mm = dhin * MM_PER_IN
            add("PASS" if dh_mm >= 1900 else "FAIL", "door height (studio floor)",
                f"{dh_mm:.0f} mm vs 1900 min (studio floor — not statutory)")
        else:
            add("WARN", "door height (studio floor)",
                "door.h_in not in spec — 80\" assumed for geometry only; floor unverified")

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

    # 2b) legal lux floor — ฉ.39 ตาราง 3 via thai_code_minimums.legal_lux_floors.
    #     Statutory row for bathrooms; for house habitable rooms residential_unit=100
    #     is a studio-ADOPTED floor (see the key's scope_note — MARS PRJ-2026-002).
    #     WARN tier: the lighting layer is a DRAFT the designer refines.
    lux_tbl = _r("thai_code_minimums", "legal_lux_floors", default={}) or {}
    rtype_l = (rtype or "").lower()
    lux_key = "bathroom" if _is_wet(rtype_l) else "residential_unit"
    lux_floor = lux_tbl.get(lux_key)
    if area > 0 and amb > 0 and isinstance(lux_floor, (int, float)):
        lux = (amb * cu * llf / area) / (0.3048 ** 2)  # fc -> lux, exact (1 fc = 1 lm/ft²)
        tier = "statutory" if lux_key == "bathroom" else "studio-adopted (scope_note)"
        out.append({"status": "PASS" if lux >= lux_floor else "WARN",
                    "check": f"legal lux floor ({rtype})",
                    "detail": f"{lux:.0f} lux avg vs {lux_floor} floor [{tier}; {lux_tbl.get('cite', 'ฉ.39 ตาราง 3')}]"})

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
    print("  (rule source: dimensional_rules.v0.2.json — Thai statutory floors cited to knowledge/codes-th"
          " (ข้อ 20/22, ฉ.39, lux floors) + ergonomic DRAFT tier (Panero — verify before client use);"
          " door 800/1900 = studio floor. Metric @0.2 specs -> suite_clearance.py.)")
    return verdict


def room_from_spec(r):
    """Build Room from a spec's room dict — the ONE place for rtype/floor-to-floor/
    door plumbing, so every validator (load_spec here, layout_gen._validate,
    qa_checklist._clearance_results, package.build) sees identical typed statutory
    checks. mm field wins when present; explicit values are never truthiness-dropped."""
    f2f = r.get("floor_to_floor_mm")
    try:
        if f2f is None and r.get("floor_to_floor_in") is not None:
            f2f = float(r["floor_to_floor_in"]) * MM_PER_IN
        elif f2f is not None:
            f2f = float(f2f)
    except (TypeError, ValueError):
        sys.exit(f"spec room.floor_to_floor value invalid: {f2f!r} / "
                 f"{r.get('floor_to_floor_in')!r} — must be a number (mm or in)")
    return Room(r["width_in"], r["depth_in"], r["ceiling_in"], door=r.get("door"),
                rtype=r.get("type"), floor_to_floor_mm=f2f)


def load_spec(path):
    """Load a room SPEC JSON (the same artifact build_room.py / .rb materialize).

    @0.1 (inch, rect) ONLY. Metric polygon specs (@0.2 family, outline_mm,
    units=metric) belong to suite_clearance.py — fail LOUDLY with routing instead
    of a KeyError. An inch spec that merely carries auxiliary metric data still
    processes: width_in presence decides."""
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if not isinstance(spec, dict):
        sys.exit(f"{os.path.basename(path)}: top-level JSON must be an object, got {type(spec).__name__}")
    r = spec.get("room", {}) or {}
    if not isinstance(r, dict):
        sys.exit(f"{os.path.basename(path)}: 'room' must be an object, got {type(r).__name__}")
    if "width_in" not in r:
        schema = str(spec.get("schema", ""))
        metricish = ("@0.2" in schema) or str(spec.get("units", "")).lower() == "metric" or "outline_mm" in r
        if metricish:
            sys.exit(f"{os.path.basename(path)} is a metric spec ({schema or 'outline_mm/units=metric'}) — "
                     f"clearance_check.py handles inch spec@0.1 only. "
                     f"Run: python pipeline/scripts/suite_clearance.py {path}")
        sys.exit(f"{os.path.basename(path)}: room.width_in missing — not a valid inch spec@0.1")
    room = room_from_spec(r)
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
