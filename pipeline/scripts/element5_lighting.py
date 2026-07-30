"""element5_lighting.py — ELEMENT 5: the 3 real light layers as PURE derivation (no bpy).

LAYER LAW (pipeline/CLAUDE.md): rules + spec = pure python; build_room only
materializes. This module turns spec["lighting"] (schema e5-layers@0.1 — DERIVATION
PARAMETERS, never baked fixture arrays) into the suite's electric-light plan:

  ambient   lumen-method downlight grids per zone (bedroom NET polygon / ensuite /
            wardrobe-bay row), CLIPPED out of full-height masses (h >= ceiling) —
            the auto plan's envelope-grid defect resolved one tier further down
            (D-E5-1/-2/-3; every dropped point is DISCLOSED in meta, no silent caps)
  task      BF11 mirror-edge opal strips (E2 D2-3 built, D-E5-4) + the ensuite
            mirror-bar WASH light (D-E5-5; the bar's geometry itself is emitted by
            bathroom.vanity_parts so mirror and bar move from one source)
  accent    BF14 slat-wall wash spots (D-E5-7 — DATA kills the dead kind-sniff) +
            the ensuite tub wash from the drawn dry strip (D-E5-8)
  practicals the E3 dome lamps' glow config (D-E5-6; consumed by _build_nightstand)

FAIL-LOUD LAW (the 831fc1b swallow lesson): a malformed block, an unknown key, a
renamed BF, a missing mirror/window referent, or !=1 bathtub RAISES — a decided
layer must never be revertible by an omission or a typo. CCT FAMILY LAW (PH-03 by
construction): every electric CCT must sit in the residential warm family
2200-3000K (knowledge/lighting/residential-lighting.md); the module RAISES on any
electric outside it. The scene's second CCT is DAYLIGHT, by KIND only.

Ref: element5-lighting_DD-2026-07-20.md (workflow wf_0280f6a3-7e7).
    python pipeline/scripts/element5_lighting.py [spec.json]   # inspect the plan
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
import bathroom          # MIRROR_SILL / MIRROR_H / MIRROR_T — the bar derives from the mirror
import lighting          # DOWNLIGHT photometrics + wired CU/LLF rules
import millwork          # nightstand_lamp_parts — the lamp emitter z derives from the built shade
import suite_clearance   # _shoelace + _point_in_poly
import suite_lighting    # _grid_in_poly + _cu_llf (the same wired lumen method)

SCHEMA = "e5-layers@0.1"

# The repo's own CCT->RGB anchors (build_room light lore): 2400K amber and the
# element-1 3000K warm-white. A practical's RGB interpolates between them — no
# third colour convention is invented (D-E5-6).
_CCT_ANCHORS = ((2400.0, (1.0, 0.82, 0.60)), (3000.0, (1.0, 0.90, 0.80)))
CCT_FAMILY = (2200.0, 3000.0)   # residential warm family (residential-lighting.md)
NOMINAL_ELECTRIC_CCT = 3000.0   # every light_warm-tinted fixture's schedule CCT

_TOP_KEYS = {"schema", "_provenance", "note", "ambient", "task", "accent", "practicals"}
_AMBIENT_KEYS = {"bedroom_target_lux", "wet_target_lux", "bay_target_lux",
                 "downlight_watts", "note"}
_TASK_KEYS = {"bf11_mirror_strips", "ensuite_mirror_bar", "note"}
_STRIP_KEYS = {"strip_w_mm", "depth_mm", "watts", "note"}
# bar PROFILE (reveal/height/depth) deliberately NOT spec keys: bathroom.BAR_REVEAL/BAR_H/
# BAR_D are the ONE source (the solid bar builds from them; scrutiny 2026-07-21 caught the
# spec copy as a second unchecked source of truth — a spec carrying them now RAISES as
# unknown keys, which is the correct fail-loud for the stale shape).
_BAR_KEYS = {"watts", "note"}
_ACCENT_KEYS = {"target_bf", "n", "setback", "axis_ref", "aim_z_mm", "cone_deg",
                "blend", "watts", "tub_wash", "note"}
_TUB_KEYS = {"n", "spacing_mm", "cone_deg", "watts", "note"}
_PRACT_KEYS = {"lamp_glow", "lamp_watts", "note"}


def applies(spec):
    """True when the spec carries the element-5 lighting block (schema-gated: every
    other spec keeps the legacy light path — unchanged except the disclosed
    TARGET_LUX wet 200->270 recalibration, which re-sizes legacy wet grids too;
    scrutiny 2026-07-21 corrected the earlier 'byte-identical' overclaim)."""
    return ((spec or {}).get("lighting") or {}).get("schema") == SCHEMA


def _fail(msg):
    raise ValueError(f"element5_lighting: {msg}")


def _check_keys(d, allowed, where):
    bad = set(d) - allowed
    if bad:
        _fail(f"{where} has unknown key(s) {sorted(bad)} — a typo must RAISE, "
              f"never silently drop a decided layer (allowed: {sorted(allowed)})")


def _pos(d, k, where):
    try:
        v = float(d[k])
    except (KeyError, TypeError, ValueError):
        _fail(f"{where}.{k} missing or not a number: {d.get(k)!r}")
    if v <= 0:
        _fail(f"{where}.{k} must be > 0, got {v}")
    return v


def validate_block(spec):
    """spec['lighting'] -> the validated block. RAISES on any malformed shape."""
    blk = (spec or {}).get("lighting")
    if not isinstance(blk, dict) or blk.get("schema") != SCHEMA:
        _fail(f"spec.lighting missing or schema != {SCHEMA!r}")
    _check_keys(blk, _TOP_KEYS, "lighting")
    for sect, keys in (("ambient", _AMBIENT_KEYS), ("task", _TASK_KEYS),
                       ("accent", _ACCENT_KEYS), ("practicals", _PRACT_KEYS)):
        if not isinstance(blk.get(sect), dict):
            _fail(f"lighting.{sect} missing (all four layers are DECIDED — an absent "
                  f"section is a revert-by-omission, not a default)")
        _check_keys(blk[sect], keys, f"lighting.{sect}")
    amb = blk["ambient"]
    for k in ("bedroom_target_lux", "wet_target_lux", "bay_target_lux", "downlight_watts"):
        _pos(amb, k, "ambient")
    task = blk["task"]
    for sub, keys in (("bf11_mirror_strips", _STRIP_KEYS), ("ensuite_mirror_bar", _BAR_KEYS)):
        if not isinstance(task.get(sub), dict):
            _fail(f"lighting.task.{sub} missing")
        _check_keys(task[sub], keys, f"lighting.task.{sub}")
    for k in ("strip_w_mm", "depth_mm", "watts"):
        _pos(task["bf11_mirror_strips"], k, "task.bf11_mirror_strips")
    _pos(task["ensuite_mirror_bar"], "watts", "task.ensuite_mirror_bar")
    acc = blk["accent"]
    if not isinstance(acc.get("target_bf"), str) or not acc["target_bf"]:
        _fail("accent.target_bf must be a non-empty BF name string")
    if acc.get("axis_ref") != "bed":
        _fail(f"accent.axis_ref: only 'bed' is implemented, got {acc.get('axis_ref')!r}")
    sb = acc.get("setback")
    if sb != "H/3" and not (isinstance(sb, (int, float)) and sb > 0):
        _fail(f"accent.setback must be 'H/3' or a positive mm number, got {sb!r}")
    n = acc.get("n")
    if not isinstance(n, int) or n < 1:
        _fail(f"accent.n must be an int >= 1, got {n!r}")
    for k in ("aim_z_mm", "cone_deg", "watts"):
        _pos(acc, k, "accent")
    bl = acc.get("blend")
    if not isinstance(bl, (int, float)) or not (0.0 <= float(bl) <= 1.0):
        _fail(f"accent.blend must be in [0,1], got {bl!r}")
    if not isinstance(acc.get("tub_wash"), dict):
        _fail("accent.tub_wash missing (E4 layer-3 is DECIDED — see D-E5-8)")
    _check_keys(acc["tub_wash"], _TUB_KEYS, "accent.tub_wash")
    tn = acc["tub_wash"].get("n")
    if not isinstance(tn, int) or tn < 1:
        _fail(f"accent.tub_wash.n must be an int >= 1, got {tn!r}")
    for k in ("spacing_mm", "cone_deg", "watts"):
        _pos(acc["tub_wash"], k, "accent.tub_wash")
    pr = blk["practicals"]
    if pr.get("lamp_glow") is not True:
        _fail("practicals.lamp_glow must be true (D-E5-6 decided the lamps EMIT; "
              "turning them off is an owner decision recorded in the spec, not a default)")
    _pos(pr, "lamp_watts", "practicals")
    return blk


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def _clip_poly_y(poly, c, keep_below):
    """Sutherland-Hodgman clip of a polygon against the halfplane y<=c (or y>=c)."""
    out = []
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        a_in = (ay <= c) if keep_below else (ay >= c)
        b_in = (by <= c) if keep_below else (by >= c)
        if a_in:
            out.append((ax, ay))
        if a_in != b_in:
            t = (c - ay) / (by - ay)
            out.append((ax + t * (bx - ax), c))
    return out


def _bbox(outline):
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def bedroom_net_outline(spec):
    """Room outline MINUS the subroom band. The two subrooms must exactly tile the
    band (their shared y-band spans full envelope width) — verified, RAISES if a
    spec edit breaks the tiling (deriving a wrong polygon silently would move every
    ambient fixture: the swallow class again)."""
    outline = [tuple(map(float, p)) for p in spec["room"]["outline_mm"]]
    subs = spec.get("subrooms") or []
    if not subs:
        return outline
    boxes = [_bbox([tuple(map(float, p)) for p in sr["outline_mm"]]) for sr in subs]
    band_y0 = min(b[1] for b in boxes)
    band_y1 = max(b[3] for b in boxes)
    for sr, b in zip(subs, boxes):
        if abs(b[1] - band_y0) > 1.0 or abs(b[3] - band_y1) > 1.0:
            _fail(f"subroom '{sr.get('name')}' y-range {b[1]}..{b[3]} does not match the "
                  f"shared band {band_y0}..{band_y1} — bedroom net polygon underivable")
    band_poly = _clip_poly_y(outline, band_y0, keep_below=False)
    band_area = suite_clearance._shoelace(band_poly)
    sub_area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in boxes)
    if abs(band_area - sub_area) > 1e4:      # 0.01 m2 in mm2
        _fail(f"subrooms do not tile the y>={band_y0} band: band {band_area/1e6:.2f} m2 "
              f"vs subrooms {sub_area/1e6:.2f} m2")
    return _clip_poly_y(outline, band_y0, keep_below=True)


def full_height_rects(spec, zone):
    """Plan rects (x0,y0,x1,y1,name) of masses that reach the ceiling in `zone`
    ('bedroom' -> builtins PLUS every subroom fixture, since a full-height subroom
    fixture may PROTRUDE into the bedroom band — BF09-2 spans y5180..6680 across the
    y5850 line; a subroom name -> its fixtures). A recessed can inside a to-ceiling
    carcass is not a light (verify-lens catch D-E5-1/-3; protrusion seam caught by
    the 2026-07-21 scrutiny — no live hit on the canonical grid, closed anyway)."""
    ceil = float(spec["room"].get("ceiling_mm", 2800))
    if zone == "bedroom":
        rows = list(spec.get("builtins") or [])
        for sr in spec.get("subrooms") or []:
            rows += sr.get("fixtures") or []
    else:
        sr = next((s for s in spec.get("subrooms") or [] if s.get("name") == zone), None)
        rows = (sr or {}).get("fixtures") or []
    out = []
    for b in rows:
        if float(b.get("h") or 0) >= ceil - 1.0:
            x, y = float(b["x"]), float(b["y"])
            out.append((x, y, x + float(b["w"]), y + float(b["d"]),
                        b.get("bf") or b.get("name") or b.get("kind", "?")))
    return out


def _clip_masses(pts, rects):
    kept, dropped = [], []
    for (x, y) in pts:
        hit = next((r for r in rects if r[0] < x < r[2] and r[1] < y < r[3]), None)
        (dropped if hit else kept).append((x, y) if not hit else (x, y, hit[4]))
    return kept, dropped


def _lumen_n(target_lux, area_m2):
    cu, llf = suite_lighting._cu_llf()
    phi = float(lighting.DOWNLIGHT["lumens"])
    return max(1, round(target_lux * area_m2 / (phi * cu * llf))), phi * cu * llf


def _ambient_zone(outline, target_lux, masses, zone_name):
    area_m2 = suite_clearance._shoelace(outline) / 1e6
    n_target, eff = _lumen_n(target_lux, area_m2)
    spacing = math.sqrt(area_m2 * 1e6 / n_target)
    pts, actual = suite_lighting._grid_in_poly(outline, spacing)
    kept, dropped = _clip_masses(pts, masses)
    achieved = len(kept) * eff / area_m2 if area_m2 > 0 else 0.0
    meta = {"zone": zone_name, "area_m2": round(area_m2, 2), "target_lux": target_lux,
            "n_grid": len(pts), "n": len(kept), "achieved_lux": round(achieved, 1),
            "spacing_mm": actual,
            "dropped_in_masses": [{"x": d[0], "y": d[1], "mass": d[2]} for d in dropped]}
    return kept, meta


# ---------------------------------------------------------------------------
# layer derivations
# ---------------------------------------------------------------------------

def _find_one(rows, pred, what):
    hits = [r for r in rows if pred(r)]
    if len(hits) != 1:
        _fail(f"expected exactly 1 {what}, found {len(hits)} — a rename/duplicate must "
              f"RAISE, never revert the decision")
    return hits[0]


def _opening_yspan(spec, oid):
    op = _find_one(spec["room"].get("openings") or [],
                   lambda o: o.get("id") == oid, f"room opening id={oid!r}")
    r = [float(v) for v in op["rect"]]
    return min(r[1], r[3]), max(r[1], r[3])


def ambient_plan(spec, blk):
    amb = blk["ambient"]
    ceil = float(spec["room"].get("ceiling_mm", 2800))
    z = ceil - 60.0
    watts = float(amb["downlight_watts"])
    fixtures, metas = [], []
    # bedroom: NET polygon, builtin clip
    net = bedroom_net_outline(spec)
    kept, meta = _ambient_zone(net, float(amb["bedroom_target_lux"]),
                               full_height_rects(spec, "bedroom"), "bedroom")
    fixtures += [{"layer": "ambient", "zone": "bedroom", "x": x, "y": y, "z": z,
                  "watts": watts} for (x, y) in kept]
    metas.append(meta)
    # subrooms: ensuite grid (wet target) / wardrobe bay row (bay target)
    for sr in spec.get("subrooms") or []:
        so = [tuple(map(float, p)) for p in sr["outline_mm"]]
        nm = sr.get("name", "sub")
        masses = full_height_rects(spec, nm)
        if sr.get("type") == "bathroom":
            kept, meta = _ambient_zone(so, float(amb["wet_target_lux"]), masses, nm)
        else:
            x0, y0, x1, y1 = _bbox(so)
            area_m2 = suite_clearance._shoelace(so) / 1e6
            n_target, eff = _lumen_n(float(amb["bay_target_lux"]), area_m2)
            pts = [((x0 + x1) / 2.0, y0 + (i + 0.5) * (y1 - y0) / n_target)
                   for i in range(n_target)]     # centred aisle ROW (D-E5-3 [est] call)
            kept, dropped = _clip_masses([(round(x, 1), round(y, 1)) for x, y in pts], masses)
            meta = {"zone": nm, "area_m2": round(area_m2, 2),
                    "target_lux": float(amb["bay_target_lux"]), "n_grid": n_target,
                    "n": len(kept), "achieved_lux": round(len(kept) * eff / area_m2, 1),
                    "spacing_mm": round((y1 - y0) / n_target, 1),
                    "dropped_in_masses": [{"x": d[0], "y": d[1], "mass": d[2]} for d in dropped],
                    "rcp_placeholder": True}
        fixtures += [{"layer": "ambient", "zone": nm, "x": x, "y": y, "z": z,
                      "watts": watts} for (x, y) in kept]
        metas.append(meta)
    return fixtures, metas


def bf11_strips(spec, blk):
    """D-E5-4: the two mirror-edge opal strips, derived from the BF11 mirror block +
    the two casement rects. Returns [{name, box(x,y,z,dx,dy,dz), light{...}}]."""
    cfg = blk["task"]["bf11_mirror_strips"]
    van = _find_one(spec.get("builtins") or [],
                    lambda b: b.get("kind") == "vanity" and (b.get("design") or {}).get("mirror"),
                    "builtin kind='vanity' carrying design.mirror")
    m = van["design"]["mirror"]
    for k in ("x_mm", "y_mm", "d_mm", "sill_mm", "h_mm"):
        if k not in m:
            _fail(f"BF11 design.mirror missing {k!r} — strips underivable")
    my0, md = float(m["y_mm"]), float(m["d_mm"])
    sill, mh = float(m["sill_mm"]), float(m["h_mm"])
    _, win1_hi = _opening_yspan(spec, "glz-west-win1")
    win2_lo, _ = _opening_yspan(spec, "glz-west-win2")
    w = float(cfg["strip_w_mm"]); depth = float(cfg["depth_mm"])
    strips = []
    for name, lo, hi in (("s", win1_hi, my0), ("n", my0 + md, win2_lo)):
        gap = hi - lo
        if gap < w:
            _fail(f"BF11 {name}-strip margin {gap:.1f} < strip_w {w} — the pier margin "
                  f"the strips live in has collapsed (spec move?); re-decide, don't squeeze")
        c = (lo + hi) / 2.0
        mx = float(m["x_mm"])
        strips.append({
            "name": f"bf11_strip_{name}",
            "box": (mx, c - w / 2.0, sill, depth, w, mh),
            # light x/aim derive from the SAME mirror referent as the box (scrutiny
            # 2026-07-21: an absolute x entrenched wall-at-x0 — the paired-geometry
            # divergence class this module raises for everywhere else)
            "light": {"x": mx + depth + 20.0, "y": c, "z": sill + mh / 2.0,
                      "size": (w, mh),
                      "aim": (mx + 1000.0, my0 + md / 2.0, sill + mh / 2.0),
                      "watts": float(cfg["watts"])},
        })
    return strips


def _ensuite(spec):
    return _find_one(spec.get("subrooms") or [],
                     lambda s: s.get("type") == "bathroom", "subroom type='bathroom'")


def ensuite_bar_wash(spec, blk):
    """D-E5-5: the wash light of the mirror task bar. The bar's SOLID geometry comes
    from bathroom.vanity_parts (same source as the mirror — one nudge moves both);
    this returns only the light, derived from the same constants."""
    cfg = blk["task"]["ensuite_mirror_bar"]
    sr = _ensuite(spec)
    fx = _find_one(sr.get("fixtures") or [],
                   lambda f: str(f.get("kind", "")).startswith("vanity"),
                   "ensuite vanity fixture")
    x0, y0 = float(fx["x"]), float(fx["y"])
    W, D = float(fx["w"]), float(fx["d"])
    # profile from bathroom.BAR_* — the ONE source the solid bar also builds from
    z_under = bathroom.MIRROR_SILL + bathroom.MIRROR_H + bathroom.BAR_REVEAL
    return {"name": "ensuite_bar_wash",
            "x": x0 + W / 2.0,
            "y": y0 - bathroom.MIRROR_T + bathroom.BAR_D + 10.0,
            "z": z_under + bathroom.BAR_H / 2.0,
            "size": (W, bathroom.BAR_H),
            "aim": (x0 + W / 2.0, y0 + D / 2.0, 900.0),
            "watts": float(cfg["watts"])}


def accent_plan(spec, blk):
    """D-E5-7 (BF14 wash) + D-E5-8 (tub wash) as aimed SPOT entries."""
    acc = blk["accent"]
    ceil = float(spec["room"].get("ceiling_mm", 2800))
    z = ceil - 60.0
    spots = []
    # BF14 wash — target resolved by bf NAME; a rename RAISES (kills the kind-sniff)
    tgt = _find_one(spec.get("builtins") or [],
                    lambda b: b.get("bf") == acc["target_bf"],
                    f"builtin bf={acc['target_bf']!r}")
    face_x = float(tgt["x"])                       # west (room-side) face of the slat wall
    run_y0, run_len = float(tgt["y"]), float(tgt["d"])
    setback = ceil / 3.0 if acc["setback"] == "H/3" else float(acc["setback"])
    fx_x = face_x - setback
    bed = _find_one(spec.get("items") or [], lambda i: i.get("kind") == "bed", "item kind='bed'")
    bed_cy = float(bed["y"]) + float(bed["d"]) / 2.0
    n = int(acc["n"])
    spacing = run_len / n
    for i in range(n):
        y = bed_cy + (i - (n - 1) / 2.0) * spacing
        if not (run_y0 < y < run_y0 + run_len):
            _fail(f"accent pool {i} at y={y:.1f} falls off the {acc['target_bf']} run "
                  f"{run_y0}..{run_y0 + run_len} — axis_ref geometry moved; re-derive the DD")
        spots.append({"layer": "accent", "name": f"bf14_wash_{i}", "x": fx_x, "y": y, "z": z,
                      "aim": (face_x, y, float(acc["aim_z_mm"])),
                      "cone_deg": float(acc["cone_deg"]), "blend": float(acc["blend"]),
                      "watts": float(acc["watts"])})
    # tub wash — dry strip derived from DRAWN geometry (vanity front .. shower/partition/tub),
    # NOT from a statutory zone dimension (the retracted 600 — DD §8)
    tw = acc["tub_wash"]
    sr = _ensuite(spec)
    fxs = sr.get("fixtures") or []
    tub = _find_one(fxs, lambda f: f.get("kind") == "bathtub", "ensuite bathtub")
    van = _find_one(fxs, lambda f: str(f.get("kind", "")).startswith("vanity"),
                    "ensuite vanity fixture")
    y_lo = float(van["y"]) + float(van["d"])
    y_hi = min([float(tub["y"])] +
               [float(f["y"]) for f in fxs if f.get("kind") in ("shower", "glass_partition")])
    if y_hi - y_lo < 200.0:
        _fail(f"ensuite dry strip collapsed ({y_lo:.0f}..{y_hi:.0f}) — tub-wash fixtures "
              f"have nowhere dry to stand; re-decide, don't overlap the wet zone")
    row_y = (y_lo + y_hi) / 2.0
    tcx = float(tub["x"]) + float(tub["w"]) / 2.0
    aim_y = float(tub["y"]) + float(tub["d"]) / 2.0
    aim_z = float(tub.get("h") or 560)
    tn = int(tw["n"])
    for i in range(tn):
        x = tcx + (i - (tn - 1) / 2.0) * 2.0 * float(tw["spacing_mm"]) / max(1, tn - 1) \
            if tn > 1 else tcx
        spots.append({"layer": "accent", "name": f"tub_wash_{i}", "x": x, "y": row_y, "z": z,
                      "aim": (x, aim_y, aim_z), "cone_deg": float(tw["cone_deg"]),
                      "blend": 0.5, "watts": float(tw["watts"])})
    return spots


def coplanar_backer_skins(spec):
    """PURE (mm): the coplanar-backer skin rects — where a full-height builtin's face
    lies EXACTLY (<=2mm) on a subroom edge, Cycles' coplanar tie can render the
    builtin's material as the subroom's wall (BF10's oak carcass wearing the ensuite's
    plaster — the element-5 LOOK catch the task-bar wash exposed). Returns
    [{x,y,z,dx,dy,dz,edge,backer}] 4mm plaster skins 2mm inside the subroom, floor to
    the ROOM ceiling (the subroom ring stops at its own sh, the backer shows above it).
    Extracted pure from build_suite (LAYER LAW — dimensional logic never lives in the
    bpy layer; scrutiny 2026-07-21). Data-driven and surgical: fires ONLY on a proven
    backer; the consumer discloses each one in the build log."""
    ceil = float(spec.get("room", {}).get("ceiling_mm", 2800))
    out = []
    for sr in spec.get("subrooms") or []:
        so = [tuple(map(float, p)) for p in sr["outline_mm"]]
        scx = sum(p[0] for p in so) / len(so)
        scy = sum(p[1] for p in so) / len(so)
        for bi, b in enumerate(spec.get("builtins") or []):
            if float(b.get("h") or 0) < ceil - 1.0:
                continue
            bx0, by0 = float(b["x"]), float(b["y"])
            bx1, by1 = bx0 + float(b["w"]), by0 + float(b["d"])
            name = b.get("bf") or b.get("name") or b.get("kind", "?")
            for ei in range(len(so)):
                (ex0, ey0), (ex1, ey1) = so[ei], so[(ei + 1) % len(so)]
                if abs(ey0 - ey1) < 1e-6:                     # horizontal edge y=const
                    lo, hi = min(ex0, ex1), max(ex0, ex1)
                    ov0, ov1 = max(lo, bx0), min(hi, bx1)
                    if ov1 - ov0 < 100.0:
                        continue
                    inw = 1.0 if scy > ey0 else -1.0          # subroom side of the edge
                    face = by1 if inw > 0 else by0            # builtin face toward the subroom
                    if abs(face - ey0) <= 2.0:
                        out.append({"x": ov0, "y": ey0 + (2.0 if inw > 0 else -6.0),
                                    "z": 0.0, "dx": ov1 - ov0, "dy": 4.0, "dz": ceil,
                                    "edge": f"y={ey0:.0f}", "backer": name})
                elif abs(ex0 - ex1) < 1e-6:                   # vertical edge x=const
                    lo, hi = min(ey0, ey1), max(ey0, ey1)
                    ov0, ov1 = max(lo, by0), min(hi, by1)
                    if ov1 - ov0 < 100.0:
                        continue
                    inw = 1.0 if scx > ex0 else -1.0
                    face = bx1 if inw > 0 else bx0
                    if abs(face - ex0) <= 2.0:
                        out.append({"x": ex0 + (2.0 if inw > 0 else -6.0), "y": ov0,
                                    "z": 0.0, "dx": 4.0, "dy": ov1 - ov0, "dz": ceil,
                                    "edge": f"x={ex0:.0f}", "backer": name})
    return out


def lamp_rgb(cct_k):
    """CCT -> the repo's RGB stand-in, linear between its own 2400K/3000K anchors.
    RAISES outside the residential warm family (PH-03 by construction)."""
    c = float(cct_k)
    if not (CCT_FAMILY[0] <= c <= CCT_FAMILY[1]):
        _fail(f"electric CCT {c:.0f}K outside the residential warm family "
              f"{CCT_FAMILY[0]:.0f}-{CCT_FAMILY[1]:.0f}K (PH-03 / one-family law)")
    (c0, a), (c1, b) = _CCT_ANCHORS
    t = (c - c0) / (c1 - c0)
    return tuple(round(a[i] + t * (b[i] - a[i]), 3) for i in range(3))


def lamp_glow(spec):
    """The practicals config for _build_nightstand: {watts, rgb, z_off_m} or None.
    z derives from millwork.nightstand_lamp_parts' own shade stack (h + base_h +
    stem_h + shade_h/2 - 0.02 = h + 0.26): the retracted 870 [est] cannot recur."""
    if not applies(spec):
        return None
    blk = validate_block(spec)
    parts = millwork.nightstand_lamp_parts(0.5, 0.5, 0.52, lamp=True)
    shade = next(p for p in parts if p[0] == "lamp_shade")
    z_centre_off = shade[3] + shade[6] / 2.0 - 0.52      # oz + dz/2 - h  ->  +0.26 m
    return {"watts": float(blk["practicals"]["lamp_watts"]), "z_off_m": z_centre_off}


def plan(spec):
    """The whole electric plan. RAISES on any malformed block / missing referent."""
    blk = validate_block(spec)
    downlights, metas = ambient_plan(spec, blk)
    strips = bf11_strips(spec, blk)
    bar = ensuite_bar_wash(spec, blk)
    spots = accent_plan(spec, blk)
    lamps = [{"name": it.get("name", "lamp"), "cct_k": float(it["lamp"].get("cct_k", 2850)),
              "rgb": lamp_rgb(it["lamp"].get("cct_k", 2850))}
             for it in spec.get("items") or []
             if it.get("kind") == "side_table" and it.get("lamp")]
    dropped = [d for m in metas for d in m["dropped_in_masses"]]
    return {"downlights": downlights, "strips": strips, "bar": bar, "spots": spots,
            "lamps": lamps,
            "meta": {"zones": metas, "dropped": dropped,
                     "counts": {"downlights": len(downlights), "strips": len(strips),
                                "bar": 1, "spots": len(spots), "lamps": len(lamps)},
                     "nominal_cct": {"family": CCT_FAMILY,
                                     "electric": sorted({NOMINAL_ELECTRIC_CCT}
                                                        | {l["cct_k"] for l in lamps})}}}


def schedule_fixtures(spec):
    """The plan mapped to suite_lighting's fixture-dict shape, so the CLIENT lane
    (suite_package -> suite_rcp / schedules) documents THE SAME lighting the render
    shows — scrutiny 2026-07-21: the auto grid would silently contradict the render
    (18 unclipped envelope cans vs the designed 29 sources), the exact silent-revert
    channel the fail-loud law exists for. Returns (fixtures, meta) like plan_lighting.
    Strip/bar/lamp lumens are [est] schedule-tier stand-ins (SKU = stage-05)."""
    p = plan(spec)
    fixtures = []
    for f in p["downlights"]:
        fixtures.append(dict(lighting.DOWNLIGHT, x=f["x"], y=f["y"],
                             note=f"e5 ambient ({f['zone']})"))
    for s in p["strips"]:
        bx, by, _, bdx, bdy, _ = s["box"]
        fixtures.append({"type": "Task strip (opal mirror-edge)", "lumens": 1000,
                         "cct_k": 3000, "cri": 90, "mounting": "Wall, mirror edge",
                         "layer": "task", "x": bx + bdx / 2.0, "y": by + bdy / 2.0,
                         "note": f"{s['name']} — lumens [est], SKU stage-05 (D-E5-4)"})
    b = p["bar"]
    fixtures.append({"type": "Task bar (opal, mirror width)", "lumens": 2000,
                     "cct_k": 3000, "cri": 90, "mounting": "Wall above mirror",
                     "layer": "task", "x": b["x"], "y": b["y"],
                     "note": "ensuite mirror bar — lumens [est], SKU stage-05 (D-E5-5)"})
    for s in p["spots"]:
        fixtures.append(dict(lighting.ACCENT, x=s["x"], y=s["y"],
                             note=f"e5 {s['name']} (aimed wash)"))
    for it in spec.get("items") or []:
        if it.get("kind") == "side_table" and it.get("lamp"):
            fixtures.append({"type": "Table lamp (brass dome)", "lumens": 450,
                             "cct_k": float(it["lamp"].get("cct_k", 2850)), "cri": 90,
                             "mounting": "Table", "layer": "decorative",
                             "x": float(it["x"]) + float(it["w"]) / 2.0,
                             "y": float(it["y"]) + float(it["d"]) / 2.0,
                             "note": "e5 practical — lumens [est], SKU stage-05 (D-E5-6)"})
    meta = {"source": SCHEMA, "ceiling_mm": float(spec["room"].get("ceiling_mm", 2800)),
            "zones": p["meta"]["zones"]}
    return fixtures, meta


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout",
        "master-suite.CANONICAL.spec.json")
    with open(path, encoding="utf-8") as fh:
        sp = json.load(fh)
    p = plan(sp)
    print(f"=== element-5 lighting plan for {os.path.basename(path)} ===")
    for m in p["meta"]["zones"]:
        drop = f" (dropped {len(m['dropped_in_masses'])} in masses)" if m["dropped_in_masses"] else ""
        print(f"  ambient {m['zone']}: {m['n']}/{m['n_grid']} @ ~{m['achieved_lux']}lx "
              f"(target {m['target_lux']}){drop}")
    print(f"  strips: {[s['name'] for s in p['strips']]}")
    print(f"  bar wash: x{p['bar']['x']:.0f} z{p['bar']['z']:.0f} aim {p['bar']['aim']}")
    print(f"  spots: {[s['name'] for s in p['spots']]}")
    print(f"  lamps: {[(l['name'], l['cct_k'], l['rgb']) for l in p['lamps']]}")
    print(f"  counts: {p['meta']['counts']}  electric CCTs {p['meta']['nominal_cct']['electric']}")


# ---------------------------------------------------------------------------
# HERO LIGHT-STORY dimmer state (lane A, verdict-round6-2026-07-30 — four
# independent judges unanimous that the flat wash is the #1 sellability gap).
# The SAME signed fixture plan, operated like a photoshoot: the lumen-method
# ambient grid is EVEN by design (correct for the CD, fatal for a hero frame),
# and an accent must read ~3x ambient to register as a focal point
# (knowledge/lighting/lumen-method-and-fixture-placement.md:48, Kelly "Focal
# Glow"). Dimming is standard operating practice, not a fixture change
# (residential-lighting.md dimming protocols) — element 5's PLAN is untouched;
# only the dimmer levels differ, and only when the build asks for the story.
# ambient 0.28 -> 0.40 + exposure trim relaxed at the first quick pair: the
# delivered references are BRIGHT-warm rooms with accents on top, not moody
# dusk scenes — 1.50/0.40 keeps the focal ratio at 3.75:1, still past the 3:1
# ambient_wardrobe: the first full eye frame sank the dressing zone into
# silhouette — its 2 cans have no accent layer to carry them, and a real
# dressing area is lit BRIGHTER than the room it serves (task + display).
# Per-zone dimming is exactly what real scene controllers do.
# 0.40 -> 0.48 at the C2 re-critic ("ยังจมมืดหม่นเหมือน draft"): the story keeps
# its 3:1 focal floor (1.50/0.48 = 3.1) while the room reads finished-bright.
STORY_SCALES = {"ambient": 0.48, "ambient_wardrobe": 0.70,
                "strips": 0.95, "bar": 0.95, "spots": 1.50, "lamps": 1.50,
                # LANE B (ground-truth study 2026-07-30): the measured flat-light
                # mechanism was NO KEY — our energy range was 10:1 with a 60W COOL
                # FILL on top, vs 191-2500:1 with a warm key on top in every pro
                # scene, and the same-genre archviz feeds its HDRI at 2.0 vs our
                # 0.3. The story demotes the fill to a whisper and lets the env +
                # practicals carry the frame (the study's key-ratio lever, not a
                # new fixture — the signed e5 plan is untouched).
                # hdri 3.3 -> 2.3 at the b1 quick (amplitude-bisect law: the LOUD
                # rung proved the key reaches the frame but blew the white cloths
                # toward clip; ~70% keeps the direction, returns the highlights)
                "fill": 0.25, "hdri": 2.3}

# Story-mode aperture (ground-truth study: every pro scene camera sits at
# f/1.4-2.4 — even asset turnarounds stop at f/8 — while our deliverable ran
# f/9). The CD/documentation wide keeps f/9; the story pair opens up.
STORY_FSTOP = 2.8


def ambient_scale(scales, zone):
    """The ambient dimmer for one downlight, by its plan zone."""
    if "wardrobe" in str(zone):
        return scales.get("ambient_wardrobe", scales["ambient"])
    return scales["ambient"]


def story_scales(enabled):
    """Per-layer dimmer multipliers. Disabled -> exact unity (the signed CD
    state must be byte-identical when the story is off)."""
    if not enabled:
        return {k: 1.0 for k in STORY_SCALES}
    return dict(STORY_SCALES)
