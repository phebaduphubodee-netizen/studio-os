"""
lighting.py — INTERIOR-AI lighting layer (pure Python, engine-agnostic, no deps).

Derives a DRAFT lighting plan (fixtures with positions + photometrics) from a
validated room spec, applying docs/INTERIOR-DESIGN-KB.md §6:
  * ambient recessed downlights — COUNT sized by the lumen method (§6.6) to hit the
    room's IES illuminance band (§6.2), laid on an aspect-matched centred grid (§6.4)
  * a pendant centered over a dining table (if present)
  * an adjustable accent over a focal piece (tv console / artwork, if present)
The ambient sizing reads the SAME targets (dimensional_rules.json["lighting"]) that
clearance_check.check_lighting verifies against, so the auto-layout passes its own check.
Like layout_gen, the output is a DRAFT a designer refines — but it is rule-grounded
and makes the RCP + lighting schedule non-empty.

DETERMINISM / the 'relational rule' (KB §3): same spec in -> same fixtures out, so the
RCP and the lighting schedule always agree without persisting anything. A spec may
OVERRIDE the auto-layout by supplying spec["lighting"]["fixtures"] (a list of dicts with
at least type/lumens/cct_k and x/y); then those are used verbatim.

    python pipeline/lighting.py [spec.json]      # demo / inspect the derived layer
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# IES targets + CU/LLF live in the rules file (single source of truth, shared with
# clearance_check.check_lighting). Load once; degrade to {} if unreadable.
_RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dimensional_rules.v0.2.json")
try:
    with open(_RULES_PATH, encoding="utf-8") as _rf:
        _LIGHTING_RULES = (json.load(_rf).get("lighting", {}) or {})
except Exception:
    _LIGHTING_RULES = {}

# DRAFT default photometrics (KB §6.3). A designer overrides per real fixture.
DOWNLIGHT = {"type": "Recessed LED downlight", "lumens": 800, "cct_k": 3000, "cri": 90, "mounting": "Recessed ceiling", "layer": "ambient"}
PENDANT   = {"type": "Pendant", "lumens": 1200, "cct_k": 2700, "cri": 90, "mounting": "Suspended", "layer": "task"}
ACCENT    = {"type": "Adjustable accent / wall-wash", "lumens": 500, "cct_k": 3000, "cri": 90, "mounting": "Recessed adjustable", "layer": "accent"}


def _centered_positions(length, target_spacing):
    """Evenly-spaced, wall-margin-balanced centers along an axis of `length` (inches).

    n = round(length / target_spacing); margin off each wall = half the actual step
    (the KB §6.4 'wall distance = spacing / 2' rule), which keeps the grid symmetric
    and avoids the 'cave effect'."""
    n = max(1, round(length / float(target_spacing)))
    step = length / n
    return [(i + 0.5) * step for i in range(n)], step


def plan_lighting(spec):
    """Return (fixtures, meta). fixtures = list of dicts:
        {tag_layer, type, lumens, cct_k, cri, mounting, layer, x, y, note}
    `tag_layer` is the design layer (ambient/task/accent); the TYPE tag (A/B/C...) is
    assigned later by type_table() so identical fixtures share one schedule row."""
    r = spec["room"]
    W, D, H = float(r["width_in"]), float(r["depth_in"]), float(r["ceiling_in"])
    items = spec.get("items", [])

    # Designer override: use spec-supplied fixtures verbatim (fill defaults).
    override = (spec.get("lighting") or {}).get("fixtures")
    if override:
        fixtures = []
        for f in override:
            base = dict(DOWNLIGHT)
            base.update(f)
            base.setdefault("note", "from spec")
            base.setdefault("x", round(W / 2.0, 1))   # guard: a malformed override
            base.setdefault("y", round(D / 2.0, 1))   # fixture without x/y must not crash the RCP
            fixtures.append(base)
        return fixtures, {"source": "spec-override", "ceiling_in": H}

    fixtures = []

    # 1) AMBIENT: size the downlight COUNT by the lumen method (KB §6.6) to hit the room's
    #    IES illuminance band midpoint — N = E*A / (phi*CU*LLF) — then lay N on an
    #    aspect-matched centred grid (KB §6.4). Replaces a fixed ceiling/2 grid that
    #    over-lit (~30fc vs a 10-20 target); now the auto-layout passes check_lighting.
    cu = _LIGHTING_RULES.get("cu_default", 0.65)
    llf = _LIGHTING_RULES.get("llf_default", 0.80)
    fc_tbl = _LIGHTING_RULES.get("general_illuminance_fc", {}) or {}
    band = fc_tbl.get(r.get("type", "default")) or fc_tbl.get("default", {"min": 10, "max": 30})
    target_fc = (band["min"] + band["max"]) / 2.0
    phi = float(DOWNLIGHT["lumens"])
    area = (W * D) / 144.0
    if area > 0 and W > 0 and D > 0:
        n_total = max(1, round(target_fc * area / (phi * cu * llf)))
        n_x = max(1, round(math.sqrt(n_total * W / D)))   # more columns when room is wider
        n_y = max(1, round(n_total / n_x))
    else:
        n_x = n_y = 1
    xs, sx = _centered_positions(W, W / n_x)
    ys, sy = _centered_positions(D, D / n_y)
    achieved_fc = (n_x * n_y * phi * cu * llf) / area if area > 0 else 0.0
    for y in ys:
        for x in xs:
            f = dict(DOWNLIGHT)
            f.update({"x": round(x, 1), "y": round(y, 1),
                      "note": f"ambient lumen-method {n_x}x{n_y}@{phi:.0f}lm -> ~{achieved_fc:.0f}fc (target {target_fc:.0f}fc)"})
            fixtures.append(f)

    # 2) TASK: pendant centered over a dining table, if any (KB §6.4: 30-36in above top).
    for it in items:
        if it.get("kind") == "dining_table":
            cx = float(it["x"]) + float(it["w"]) / 2.0
            cy = float(it["y"]) + float(it["d"]) / 2.0
            f = dict(PENDANT)
            f.update({"x": round(cx, 1), "y": round(cy, 1),
                      "note": "pendant over dining table (hang 30-36in above top)"})
            fixtures.append(f)

    # 3) ACCENT: one adjustable head over a focal piece (tv console / artwork) if present.
    focal = next((it for it in items if it.get("kind") in ("tv_console", "artwork")), None)
    if focal:
        cx = float(focal["x"]) + float(focal["w"]) / 2.0
        cy = float(focal["y"]) + float(focal["d"]) / 2.0
        # nudge the head slightly into the room off the wall-hugging focal piece
        cy = cy + 12.0 if cy < D / 2.0 else cy - 12.0
        f = dict(ACCENT)
        f.update({"x": round(cx, 1), "y": round(cy, 1),
                  "note": f"accent on {focal.get('name', focal['kind'])} (~3x ambient)"})
        fixtures.append(f)

    return fixtures, {"source": "auto", "ceiling_in": H,
                      "ambient_grid": f"{n_x}x{n_y}", "target_fc": round(target_fc, 1),
                      "achieved_fc": round(achieved_fc, 1),
                      "ambient_spacing_in": round((sx + sy) / 2.0, 1)}


def type_key(f):
    """Fixtures sharing (type, lumens, cct, cri) are the SAME schedule TYPE."""
    return (f["type"], int(f["lumens"]), int(f["cct_k"]), int(f["cri"]))


def type_table(fixtures):
    """Group instances into TYPES with stable tags A, B, C... (order of first appearance).
    Returns (rows, tag_of) where rows = list of {tag,type,lumens,cct_k,cri,mounting,layer,count}
    and tag_of maps id(fixture)->tag for labelling the RCP."""
    order, by_key = [], {}
    for f in fixtures:
        k = type_key(f)
        if k not in by_key:
            by_key[k] = {"type": f["type"], "lumens": int(f["lumens"]), "cct_k": int(f["cct_k"]),
                         "cri": int(f["cri"]), "mounting": f.get("mounting", ""),
                         "layer": f.get("layer", ""), "count": 0}
            order.append(k)
        by_key[k]["count"] += 1
    rows, tag_of_key = [], {}
    for i, k in enumerate(order):
        tag = chr(ord("A") + i) if i < 26 else f"A{i}"
        tag_of_key[k] = tag
        row = dict(by_key[k]); row["tag"] = tag
        rows.append(row)
    tag_of = {id(f): tag_of_key[type_key(f)] for f in fixtures}
    return rows, tag_of


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    fixtures, meta = plan_lighting(spec)
    rows, _ = type_table(fixtures)
    print(f"=== lighting layer for {os.path.basename(path)} ({meta['source']}) ===")
    print(f"  {len(fixtures)} fixtures, {len(rows)} types; ambient {meta.get('ambient_grid','?')} grid "
          f"~{meta.get('ambient_spacing_in','?')}in o.c. -> ~{meta.get('achieved_fc','?')}fc "
          f"(IES target {meta.get('target_fc','?')}fc)")
    for row in rows:
        print(f"  [{row['tag']}] {row['type']}: {row['lumens']}lm {row['cct_k']}K CRI{row['cri']} "
              f"({row['layer']}) x{row['count']}")
    print("  (ambient SIZED to the IES band via the lumen method; verify vs real fixture photometrics + local code)")
