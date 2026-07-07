"""swing_door_candidates.py -- F4 swing-door lane: quarter-arc (+ radial leaf) detector.

Hinged doors are 60% of FloorPlanCAD GT openings and the pair-run lane cannot see them
(an arc-and-leaf symbol has no parallel pair). This module classifies mm-scaled arc
records (produced by floorplancad_adapter.walk_path's accumulator -- W3C F.6.5 sweep
sampling, never chords) into swing-door candidates:

  gates    circular (rx~ry) -> quarter sweep (60..120 deg) -> radius in the door band
           (500..2500 mm -- same physical anchor as the adapter's door-band calibration
           revoker, floorplancad_adapter.py DOOR_MM_MIN/MAX).
  leaf     a radial segment: one endpoint within leaf_end_tol of the hinge (arc centre)
           and length within +-20% of r. Verified corpus pattern: leaf rect long side
           runs hinge -> arc start, length == r.
  doubles  mirrored arc pairs (radii within 25%, hinge distance ~2r, non-hinge
           endpoints meeting mid-opening) merge into ONE candidate: GT draws a double
           door as ONE instance, and an unmerged half sits ~r/2 (>OPEN_TOL=300mm) from
           the GT centre -- merging is required for recall, not cosmetics.

HONESTY: type="door" is emitted ONLY on earned evidence (leaf confirmed, or a mirrored
double). Arc-only survivors stay type="candidate" (outside the GT vocabulary
door|sliding|window|opening -- findability credit only, zero subtype credit). Openings
NEVER carry "rot": the benchmark scores rot on elements only, so a fabricated opening
rot would be an invisible (untestable) lie. Every rejection is counted in stats.
"""
import math

SWING_DEFAULTS = dict(
    circular_tol=0.10,        # |rx-ry| <= 10% of max: door swings are circular arcs
    sweep_deg=(60.0, 120.0),  # quarter-circle band (corpus symbol sweeps ~90 deg)
    r_min=500.0,              # mm; leaf-length band == adapter door band [500, 2500]
    r_max=2500.0,
    leaf_end_tol=150.0,       # mm; leaf endpoint-to-hinge proximity
    leaf_len_tol=0.20,        # leaf length within +-20% of r
    dupe_hinge_tol=50.0,      # mm; overprinted identical arcs -> keep first
    dupe_r_tol=0.05,
    double_r_tol=0.25,        # mirrored pair: radii within 25%
    double_hinge_band=(1.4, 2.6),   # hinge distance in [1.4, 2.6] * max(r)
    double_meet_tol=300.0,    # mm; the two arcs' endpoints meet mid-opening
)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def detect(arcs, segs, params=None):
    """arcs: mm-scaled arc records {cx, cy, rx, ry, sweep_deg, x1, y1, x2, y2, pts}.
    segs: ALL mm 2-point segments on the sheet (leaf-evidence pool).
    -> (cands, stats). cand: {x, y, w, d, type, tier, evidence} -- bbox over the SWEEP
    SAMPLES (+ leaf endpoints), 0.1-rounded; never the chord alone; never a "rot" key."""
    p = dict(SWING_DEFAULTS)
    p.update(params or {})
    stats = {"arcs_seen": len(arcs), "arcs_circular": 0, "arcs_quarter": 0,
             "arcs_in_band": 0, "dupes_dropped": 0, "leaf_confirmed": 0,
             "doubles_merged": 0, "emitted_door": 0, "emitted_candidate": 0}
    # leaf pool built ONCE per sheet: only segments of plausible leaf length
    # (arc sweep-sample chains are ~2*pi*r/4/16 < 250 mm even at r_max -> self-excluded)
    lo = p["r_min"] * (1.0 - p["leaf_len_tol"])
    hi = p["r_max"] * (1.0 + p["leaf_len_tol"])
    pool = [s for s in segs if lo <= _dist(s[0], s[1]) <= hi]

    acc = []
    for a in arcs:
        mx = max(a["rx"], a["ry"])
        if mx <= 0 or abs(a["rx"] - a["ry"]) > p["circular_tol"] * mx:
            continue
        stats["arcs_circular"] += 1
        if not (p["sweep_deg"][0] <= abs(a["sweep_deg"]) <= p["sweep_deg"][1]):
            continue
        stats["arcs_quarter"] += 1
        r = (a["rx"] + a["ry"]) / 2.0
        if not (p["r_min"] <= r <= p["r_max"]):
            continue
        stats["arcs_in_band"] += 1
        hinge = (a["cx"], a["cy"])
        if any(_dist(hinge, b["hinge"]) <= p["dupe_hinge_tol"]
               and abs(r - b["r"]) <= p["dupe_r_tol"] * max(r, b["r"]) for b in acc):
            stats["dupes_dropped"] += 1          # overprinted duplicate arc
            continue
        leaf = None
        for s in pool:
            if abs(_dist(s[0], s[1]) - r) > p["leaf_len_tol"] * r:
                continue
            if (_dist(s[0], hinge) <= p["leaf_end_tol"]
                    or _dist(s[1], hinge) <= p["leaf_end_tol"]):
                leaf = s
                break
        if leaf is not None:
            stats["leaf_confirmed"] += 1
        acc.append({"hinge": hinge, "r": r, "pts": list(a["pts"]),
                    "ends": [(a["x1"], a["y1"]), (a["x2"], a["y2"])],
                    "leaf": leaf, "double": False})

    # mirrored double doors -> merge greedily by meet distance, each arc merges once
    cand_pairs = []
    for i in range(len(acc)):
        for j in range(i + 1, len(acc)):
            A, B = acc[i], acc[j]
            mr = max(A["r"], B["r"])
            if abs(A["r"] - B["r"]) > p["double_r_tol"] * mr:
                continue
            hd = _dist(A["hinge"], B["hinge"])
            if not (p["double_hinge_band"][0] * mr <= hd
                    <= p["double_hinge_band"][1] * mr):
                continue
            meet = min(_dist(ea, eb) for ea in A["ends"] for eb in B["ends"])
            if meet <= p["double_meet_tol"]:
                cand_pairs.append((meet, i, j))
    cand_pairs.sort()
    used = set()
    for meet, i, j in cand_pairs:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        acc[i]["pts"] += acc[j]["pts"]
        if acc[i]["leaf"] is None and acc[j]["leaf"] is not None:
            acc[i]["leaf"] = acc[j]["leaf"]
        acc[i]["double"] = True
        acc[j]["dropped_into_merge"] = True
        stats["doubles_merged"] += 1

    cands = []
    for a in acc:
        if a.get("dropped_into_merge"):
            continue
        pts = a["pts"] + (list(a["leaf"]) if a["leaf"] is not None else [])
        x0, y0, x1, y1 = _bbox(pts)
        strong = (a["leaf"] is not None) or a["double"]
        typ = "door" if strong else "candidate"
        stats["emitted_door" if typ == "door" else "emitted_candidate"] += 1
        cands.append({"x": round(x0, 1), "y": round(y0, 1),
                      "w": round(x1 - x0, 1), "d": round(y1 - y0, 1),
                      "type": typ, "tier": "strong" if strong else "weak",
                      "evidence": {"r_mm": round(a["r"], 1),
                                   "leaf": a["leaf"] is not None,
                                   "double": a["double"]}})
    return cands, stats
