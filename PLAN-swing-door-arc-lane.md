# PLAN-swing-door-arc-lane
Rank: 2/5

## Goal (incl. the measured number this moves)

Build a quarter-arc + radial-leaf **swing-door detector** for the annotation-blind SVG
reader lane, so hinged doors — **6,124 of 10,235 GT openings (60%), today at 14.6%
recall (895/6,124)** per `qa/reports/floorplancad-baseline-2026-07-06.md:42` — become
findable. The pair-run lane (`glazing_candidates.promote`) structurally cannot find
them: an arc-and-leaf symbol has no parallel pair.

The number that must move: **F4 per-type door recall on the FloorPlanCAD test corpus**,
from 895/6,124 matched (baseline-test-00) to strictly more (realistic band 2,000–4,500;
some GT doors are line-only symbols and stay unfindable by an arc lane — verified below).
Secondary first: **corpus subtype hits > 0 for the first time**, earned by a real
classifier (arc+leaf evidence → `type="door"`), never by sentinel collision.

Numbers that must NOT move (or must be explained): sliding recall 733/835, window
2,850/3,160 (this slice only ADDS pred openings; greedy matching keeps prior matches).
Detection recall 9.8% will NOT move — this slice never touches `plan_cluster`.
F4 precision (2.9%) is item A's number (wall-aware promote), not this slice's; expect it
to wiggle slightly in either direction as both `matched` and `n_pred` grow.

## Why now (leverage)

- No other single detector can move F4 recall this much: doors are the majority class.
- All machinery already exists and was verified in code this session:
  - W3C SVG 1.1 F.6.5 arc sweep sampling: `floorplancad_adapter.py:108-150`
    (`_arc_extent_points`, `_ARC_SAMPLES=16` at :105) — REUSE via a small refactor,
    never rewrite (the two-half-arc-circle zero-area lesson is documented in its
    docstring :111-114).
  - The reader already imports the adapter's path walker
    (`svg_plan_reader.py:57: from floorplancad_adapter import walk_path, shape_points, SVG_NS`)
    and feeds arc sweep samples into curve segs (`_path_ink`, :72-89).
  - The scorer already handles typed openings honestly: subtype accuracy is
    case-insensitive string equality on matched pairs (`benchmark_reader.py:268`),
    F4 verdict = min(recall, precision, subtype_accuracy) (`benchmark_reader.py:343-345`).
- Corpus evidence verified on-machine 2026-07-07:
  - Swing-door drawing pattern (test-00/0001-0023.svg, semantic-id=3 instance-id=5):
    four line paths form a thin leaf rect (0.5u × 9.75u) + ONE quarter arc
    `M 75.318,85.502 A 9.75,9.75 0.0 0,0 65.818,95.249` — radius == leaf length,
    arc center (hinge) sits at the leaf base, arc start at the leaf tip.
  - Same sheet also shows **line-only doors** (instance-id 6 and 8, semantic-id 3 =
    plain 8-unit line segments, NO arc) → an arc lane cannot reach 100% door recall.
    Do not chase it.
  - Smoke sheet found and verified: `0001-0024` is mm-calibrated (scale 100.0,
    7 GT `single_door`, arcs present at r = 7.3125/8.775/9.75 units = 731–975 mm).
    (`0001-0023` is units=`svg-unit` — NOT usable for mm scoring; verified.)

## Files to touch

All paths repo-relative to `c:/Users/teza_/OneDrive/Desktop/PlingPeat`.

| File | Status | What |
|---|---|---|
| `pipeline/scripts/floorplancad_adapter.py` | [EXISTS] | Extract `arc_center_params()` out of `_arc_extent_points` (:108-150); add optional `arcs` accumulator to `walk_path` (:153-217). Behavior-identical for all existing callers. |
| `pipeline/scripts/swing_door_candidates.py` | [NEW] | Pure-geometry detector: gates (circular, quarter-sweep, door-size band), leaf evidence, overprint dedupe, mirrored-double-arc merge. No file IO, no XML. |
| `pipeline/scripts/test_swing_door_candidates.py` | [NEW] | 13 unit tests on hand-built mm fixtures (self-authored — never corpus bytes). |
| `pipeline/scripts/svg_plan_reader.py` | [EXISTS] | Collect arcs in `read_ink` (:92-139) via `_path_ink` (:72-89); scale + call detector in `read_sheet` (:143-192) after the `promote()` block (:167-174); meta stats; report honesty-note update (:311-351); `READER_VERSION` bump (:61). |
| `pipeline/scripts/test_svg_plan_reader.py` | [EXISTS] | +2 tests: synthetic swing-door sheet emits exactly one `type=="door"` opening with no `rot`; annotated-vs-stripped arc twin stays blind. Touch NOTHING existing. |
| `qa/reports/floorplancad-swing-door-2026-07-07.md` | [NEW] | Distilled before/after report (the only corpus-derived artifact that enters the repo). |
| `docs/strategy.md` | [EXISTS] | APPEND a dated session entry at the tail. Never rewrite history. |

Outside the repo (never committed):
`C:/Users/teza_/studio-datasets/floorplancad/baseline-test-01/` [NEW dir, created by the
run] — cards.jsonl + preds/ + overlays/ + report.md. `baseline-test-00/` is the committed
reference: NEVER overwrite it.

## Implementation order

Work from repo root `c:/Users/teza_/OneDrive/Desktop/PlingPeat` unless a step says
otherwise. The repo's working pytest invocation (~5 s):
`python3 -m pytest pipeline/scripts/ -q`. Always `python3` (a user-local shim;
the bare MS-Store stub once made hooks fail open).

**ANCHOR LAW: svg_plan_reader.py line numbers in this plan are advisory only (another
slice — PLAN-f4-wall-aware-precision, item A — landed first and shifted everything
below :143); the quoted code strings are binding.** Locate every edit by its quoted
content, never by line number. Item A also means `read_sheet`'s signature is now
`read_sheet(svg_path, scale_mm_per_unit, close_mm=CLOSE_MM, wall_segs=None,
wall_source=None)` — any new parameter this plan adds must go AFTER those, keyword-only
in spirit, default None/off.

### Step 0 — baseline check + record N (nothing edited yet)

```
python3 -m pytest pipeline/scripts/ -q
```
Require **0 failures / 0 errors**, and RECORD the green count as **N**. (As of
2026-07-07, after item A landed, N = 471 — but do not hard-require that value.) Every
later suite-count expectation in this plan is expressed relative to N.

Hard precondition before Step 1:

```
git status --short pipeline/scripts/
```
Must show NO modifications (item A committed or absent). If it is dirty with wall-lane
work (`wall_lines` / `wall_source` strings in the diff), STOP and wait for that work to
be committed first — otherwise Step 10's explicit-path `git add` would smuggle item A's
changes into the swing-door commit.

STOP only on test failures/errors or a dirty `git status --short pipeline/scripts/`.

### Step 1 — adapter refactor: expose the F.6.5 centre conversion

File: `pipeline/scripts/floorplancad_adapter.py`.
Current `_arc_extent_points` (lines 108-150) does endpoint→centre conversion AND
sampling in one body. Split it. Insert ABOVE `_arc_extent_points` a new public function
containing lines 115-144 verbatim, returning params instead of sampling:

```python
def arc_center_params(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2):
    """W3C SVG 1.1 F.6.5 endpoint->centre conversion (shared by the bbox sampler below
    and the swing-door lane). Returns (cx, cy, rx, ry, phi_rad, th1_rad, dth_rad) with
    the LAMBDA-SCALED radii (spec: radii too small are scaled up), or None when the arc
    is degenerate (zero radius / coincident endpoints / numerically flat)."""
    rx, ry = abs(rx), abs(ry)
    if rx < 1e-12 or ry < 1e-12 or (x1 == x2 and y1 == y2):
        return None
    phi = math.radians(phi_deg % 360.0)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1.0:                      # radii too small: scale up per spec
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    if den < 1e-12:
        return None
    coef = math.sqrt(max(0.0, num / den))
    if bool(large) == bool(sweep):
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2.0
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2.0
    th1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    th2 = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx)
    dth = th2 - th1
    if sweep and dth < 0:
        dth += 2 * math.pi
    elif not sweep and dth > 0:
        dth -= 2 * math.pi
    return (cx, cy, rx, ry, phi, th1, dth)
```

Then reduce `_arc_extent_points` to (keep its existing docstring VERBATIM):

```python
def _arc_extent_points(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2):
    """<existing docstring lines 109-114, unchanged>"""
    prm = arc_center_params(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2)
    if prm is None:
        return []
    cx, cy, rx, ry, phi, th1, dth = prm
    cp, sp = math.cos(phi), math.sin(phi)
    pts = []
    for k in range(1, _ARC_SAMPLES):
        t = th1 + dth * k / _ARC_SAMPLES
        pts.append((cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp,
                    cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp))
    return pts
```

Note the ONE behavior difference to preserve exactly: the old body returned `[]` on
degenerate; `None`→`[]` mapping keeps that. The `den < 1e-12` branch previously
returned `[]` directly — now returns `None` from the helper; same net effect.

Check before moving on:
```
python3 -m pytest pipeline/scripts/test_floorplancad_adapter.py -q
```
Expected: all pass (same count as before this step; the file has named mutant pins
M3b/M4b/M6b/M7b and arc pins at :65-70 — none may fail). Do NOT re-run `--batch` or
regenerate gt-test-00: emission is unchanged by construction.

### Step 2 — adapter: optional arc accumulator on `walk_path`

Same file. Change the signature at line 153 from `def walk_path(d):` to
`def walk_path(d, arcs=None):` and extend its docstring with one sentence:
`"If arcs is a list, one record per A-command is appended: {cx, cy, rx, ry, phi_deg,
sweep_deg, x1, y1, x2, y2, pts} (pts = start + sweep samples + end, raw path units)."`

Replace the `elif C == "A":` branch (currently lines 209-216) with:

```python
        elif C == "A":
            ex = args[5] + (cx if rel else 0)
            ey = args[6] + (cy if rel else 0)
            apts = _arc_extent_points(cx, cy, args[0], args[1], args[2],
                                      args[3], args[4], ex, ey)
            for p in apts:
                out.append((p, "ctrl"))    # true swept extent; segments still get chord
            if arcs is not None:
                prm = arc_center_params(cx, cy, args[0], args[1], args[2],
                                        args[3], args[4], ex, ey)
                if prm is not None:
                    acx, acy, arx, ary, aphi, ath1, adth = prm
                    arcs.append({"cx": acx, "cy": acy, "rx": arx, "ry": ary,
                                 "phi_deg": math.degrees(aphi),
                                 "sweep_deg": math.degrees(adth),
                                 "x1": cx, "y1": cy, "x2": ex, "y2": ey,
                                 "pts": [(cx, cy)] + apts + [(ex, ey)]})
            cx, cy = ex, ey
            out.append(((cx, cy), "draw"))
```

CRITICAL ordering facts (verified): the record reads `cx, cy` BEFORE the
`cx, cy = ex, ey` update (they are the arc START); `_arc_extent_points`' loop is
`range(1, _ARC_SAMPLES)` — it EXCLUDES both endpoints (:146), which is why the record's
`pts` must prepend `(cx, cy)` and append `(ex, ey)` or the bbox under-covers.

Check: `python3 -m pytest pipeline/scripts/test_floorplancad_adapter.py -q` still all
pass (all existing callers pass no `arcs`; default `None` is inert).

### Step 3 — new module `pipeline/scripts/swing_door_candidates.py` [NEW]

Pure geometry, no imports beyond `math`. NO file IO, NO xml — it must never see the
SVG (blindness by construction: it consumes only mm arcs + mm segments handed to it).

```python
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
```

(Chord-endpoint wall contact is item A's evidence channel — this lane runs wall-free
today; do NOT add a wall parameter speculatively.)

Check: `python3 -c "import sys; sys.path.insert(0,'pipeline/scripts'); import swing_door_candidates; print(swing_door_candidates.detect([], []))"`
prints `([], {'arcs_seen': 0, ...})`.

### Step 4 — new test file `pipeline/scripts/test_swing_door_candidates.py` [NEW]

13 pytest-style tests, self-authored fixtures (all mm), plus the repo's usual
`__main__` runner. Fixture helper (put at top):

```python
"""test_swing_door_candidates.py -- pins for the swing-door arc lane.

Honesty contract pinned here: type='door' must be EARNED (leaf or mirrored double);
arc-only stays type='candidate'; openings never carry rot; every rejection is counted.
Fixtures are self-authored synthetic geometry (the corpus is CC BY-NC, never copied).

    python3 -m pytest test_swing_door_candidates.py -q
"""
import math

import swing_door_candidates as S


def _arc(hx, hy, r, a0_deg, a1_deg, n=17):
    ts = [math.radians(a0_deg + (a1_deg - a0_deg) * k / (n - 1)) for k in range(n)]
    pts = [(hx + r * math.cos(t), hy + r * math.sin(t)) for t in ts]
    return {"cx": hx, "cy": hy, "rx": r, "ry": r,
            "sweep_deg": a1_deg - a0_deg,
            "x1": pts[0][0], "y1": pts[0][1], "x2": pts[-1][0], "y2": pts[-1][1],
            "pts": pts}
```

The 13 tests (names + the assertion that matters):

1. `test_arc_plus_leaf_is_typed_door` — `detect([_arc(0,0,1000,0,90)], [[(0,0),(1000,0)]])`
   → 1 cand, `type=="door"`, `tier=="strong"`, `evidence["leaf"] is True`,
   bbox ≈ x 0 y 0 w 1000 d 1000 (±1).
2. `test_arc_only_stays_untyped_candidate` — same arc, `segs=[]` → `type=="candidate"`,
   `tier=="weak"`. (THE mutation pin: deleting the leaf gate and typing everything
   "door" must fail here.)
3. `test_openings_never_carry_rot` — both cands above: `assert "rot" not in c`
   (mirror of the adapter's M6b pin, `test_floorplancad_adapter.py:314-317`).
4. `test_negative_sweep_accepted` — `_arc(0,0,1000,90,0)` (sweep −90) still passes the
   quarter gate (`abs()` on sweep).
5. `test_sink_scale_arc_rejected` — r=300 → 0 cands; `stats["arcs_quarter"]==1`,
   `stats["arcs_in_band"]==0` (the sink-flood killer: sinks ≈50% arc share, basins
   r<500).
6. `test_half_circle_rejected` — `_arc(0,0,1000,0,180)` → `stats["arcs_circular"]==1`,
   `stats["arcs_quarter"]==0` (two-half-arc circles = furniture, not doors).
7. `test_elliptical_arc_rejected` — the `_arc` helper can only produce circular
   records, so build the elliptical record by mutating one (every key stays present):
   `a = _arc(0, 0, 1000, 0, 90); a["ry"] = 700; cands, stats = S.detect([a], []);
   assert stats["arcs_circular"] == 0 and cands == []`.
8. `test_bbox_covers_sweep_not_chord` — `_arc(0,0,1000,45,135)`: both endpoints at
   y≈707 but the sweep apex is (0,1000); assert cand `d >= 250` (chord-only bbox
   would give d≈0 — the zero-area lesson).
9. `test_double_door_merges_to_one` — arc A `_arc(0,0,1000,90,0)` (tip (0,1000)→closed
   (1000,0)) + arc B `_arc(2000,0,1000,90,180)` (tip (2000,1000)→closed (1000,0)):
   ends meet at (1000,0) → exactly 1 cand, `evidence["double"] is True`,
   `type=="door"`, `stats["doubles_merged"]==1`, bbox spans x 0..2000.
10. `test_adjacent_singles_not_merged` — arc A as above + arc C
    `_arc(2000,0,1000,90,0)` (closed at (3000,0)): min endpoint distance ≈1414 > 300
    → 2 cands, `stats["doubles_merged"]==0`.
11. `test_overprint_dupe_dropped` — same arc twice → 1 cand,
    `stats["dupes_dropped"]==1`.
12. `test_leaf_wrong_length_not_confirmed` — arc r=1000 + radial seg of length 500
    `[[(0,0),(500,0)]]` → `tier=="weak"`, `evidence["leaf"] is False`.
13. `test_stats_shape_pinned_and_empty_input` — `detect([], [])` → `([],
    stats)` with EXACTLY the key set `{arcs_seen, arcs_circular, arcs_quarter,
    arcs_in_band, dupes_dropped, leaf_confirmed, doubles_merged, emitted_door,
    emitted_candidate}` all == 0.

End the file with:
```python
if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
```

Check: `python3 -m pytest pipeline/scripts/test_swing_door_candidates.py -q` → 13 passed.

### Step 5 — wire the reader (`pipeline/scripts/svg_plan_reader.py`)

Five edits, in file order (ANCHOR LAW applies: locate each by the quoted strings,
not by line number):

5a. The line reading `READER_VERSION = "svg_plan_reader v1"` → `"svg_plan_reader v2"`.
    (No test pins the value; meta.reader and the report header both pick it up.)

5b. After the import line that now reads
    `from glazing_candidates import axis_run, promote, run_endpoints` add:
    `from swing_door_candidates import detect as detect_swing`.

5c. `_path_ink`: signature `def _path_ink(d):` → `def _path_ink(d, arcs=None):` and
    its loop `for (pt, flag) in walk_path(d):` → `for (pt, flag) in walk_path(d, arcs):`.
    Nothing else changes. (`test_path_ink_polylines_and_curves` calls it with ONE arg —
    the default keeps it green.)

5d. `read_ink`: initialize `arcs = []` next to its `segs, csegs = [], []` line; in the
    path branch, change `s, c = _path_ink(el.get("d"))` to
    `s, c = _path_ink(el.get("d"), arcs)`; add `"arcs": arcs` to the return dict:
    `return {"segs": segs, "curve_segs": csegs, "arcs": arcs, **counts}`.
    IMPORTANT: the arc collection now lives INSIDE the existing per-prim flow, i.e.
    AFTER the `el.get("transform")` skip-and-count branch — transform-bearing prims must
    not contribute arcs (same rule as segs; pooling their coords would misplace doors).

5e. `read_sheet` (signature now `read_sheet(svg_path, scale_mm_per_unit,
    close_mm=CLOSE_MM, wall_segs=None, wall_source=None)` after item A — do not add
    parameters before the item-A ones): two insertions.
    After the `csegs = [...]` scaling line, scale the arcs:
    ```python
    arcs = [{"cx": a["cx"] * s, "cy": a["cy"] * s, "rx": a["rx"] * s, "ry": a["ry"] * s,
             "phi_deg": a["phi_deg"], "sweep_deg": a["sweep_deg"],
             "x1": a["x1"] * s, "y1": a["y1"] * s, "x2": a["x2"] * s, "y2": a["y2"] * s,
             "pts": [(px * s, py * s) for px, py in a["pts"]]}
            for a in ink["arcs"]]
    ```
    (Angles are scale-invariant — only coordinates and radii multiply by `s`. Forgetting
    `rx`/`ry` silently breaks the 500–2500 mm door band.)
    Insert after the pair-lane loop that appends
    `{"id": f"g{k:03d}", "type": "candidate", ...}` (item A's oracle-wall block now
    sits between `openings = []` and that loop — the swing insertion goes AFTER the
    loop, not after `openings = []`):
    ```python
    swing, sw_stats = detect_swing(arcs, segs)
    for k, c in enumerate(swing):
        openings.append({"id": f"a{k:03d}", "type": c["type"],
                         "x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"],
                         "tier": c["tier"]})
    ```
    And in the meta dict, after the `"opening_candidate_stats": stats,` line, add:
    `"swing_door_stats": sw_stats,`.

5f. Report honesty text (`render_baseline_report`). Two string edits:
    - The reader-description string containing `"openings = glazing_candidates
      pair-runs, untyped)"`: change that fragment to
      `"openings = glazing_candidates pair-runs (untyped) + "
      "swing-door arc lane (typed 'door' on arc+leaf / mirrored-double evidence))"`.
    - The honesty bullet beginning `"- pred openings carry type='candidate'"`: replace
      the sentence claiming ALL pred openings are `type='candidate'` with:
      `"- pair-lane openings stay type='candidate' (outside the GT vocabulary: zero "
      "unearned subtype credit); swing-lane openings claim type='door' ONLY on earned "
      "arc+leaf / mirrored-double evidence, so nonzero subtype accuracy is real signal. "
      "A per-sheet F4 PASS additionally needs recall AND precision >= 0.9 -- the "
      "empty-wall candidate flood keeps that out of reach until the wall-aware pass."`
    Static-tripwire caution: no new string may contain `semantic-id`, `instance-id`,
    or `inkscape`, and no code token may contain `semantic`/`inkscape`/`INK_NS`/
    `instance_id` (test:120-140).

Check: `python3 -m pytest pipeline/scripts/test_svg_plan_reader.py -q` → all existing
tests still pass (the blindness twins now flow arcs through `read_sheet` and must stay
byte-equal; `test_read_sheet_clusters_and_openings` still passes because its fixture
has no arcs and pair-lane rows still say `candidate`).

### Step 6 — extend `pipeline/scripts/test_svg_plan_reader.py` (+2 tests, append only)

6a. `test_read_sheet_swing_door_typed(tmp_path)` — synthetic sheet replicating the
verified corpus symbol geometry (self-authored numbers, scale 100 mm/unit → r=975 mm):
```python
def test_read_sheet_swing_door_typed(tmp_path):
    """A quarter arc (r=9.75u) + radial leaf at scale 100 -> exactly one earned
    type='door' opening; pair-lane rows stay 'candidate'; openings never carry rot."""
    body = ('<path d="M 75.3,85.5 L 75.8,85.5"/>\n'
            '<path d="M 75.8,95.25 L 75.3,95.25"/>\n'
            '<path d="M 75.8,95.25 L 75.8,85.5"/>\n'
            '<path d="M 75.3,95.25 L 75.3,85.5"/>\n'
            '<path d="M 75.3,85.5 A 9.75,9.75 0.0 0,0 65.8,95.25"/>\n')
    pred = R.read_sheet(_write(tmp_path, "door.svg", body), 100.0)
    doors = [o for o in pred["openings"] if o["type"] == "door"]
    assert len(doors) == 1, pred["openings"]
    assert all("rot" not in o for o in pred["openings"])
    assert all(o["type"] in ("candidate", "door") for o in pred["openings"])
    d = doors[0]
    # bbox over sweep+leaf: x ~ 6580..7580, y ~ 8550..9525 (mm)
    assert abs((d["x"] + d["w"] / 2) - 7080) < 300
    assert abs((d["y"] + d["d"] / 2) - 9037) < 300
    assert pred["meta"]["swing_door_stats"]["emitted_door"] == 1
```
(Heads-up: the leaf rect's long sides are 50 mm apart at this scale — inside
`pair_gap=(40,250)` — so the PAIR lane will also emit a `candidate` row here. That is
expected; assert on the door subset, never on `len(openings)==1`.)

6b. `test_read_sheet_blind_with_arcs(tmp_path)` — annotated-vs-stripped twin whose
body is the SAME five paths as 6a but with `semantic-id="3" instance-id="5"` on each
path in the annotated variant (and a `<g inkscape:label="D">` wrapper), bare in the
stripped variant. Assert `read_sheet` equality after `meta.pop("file")` on both —
the swing lane must be annotation-blind end-to-end.

Check:
```
python3 -m pytest pipeline/scripts/ -q
```
Expected: **N + 15 passed** (N from Step 0, + 13 swing tests + 2 reader tests),
zero failures.

### Step 7 — smoke on one real mm sheet (verified suitable: 0001-0024)

cwd MUST be `pipeline/scripts` (flat sibling imports at the top of svg_plan_reader.py):

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
python3 svg_plan_reader.py --sheet C:\Users\teza_\studio-datasets\floorplancad\test-00\0001-0024.svg 100.0 C:\Users\teza_\studio-datasets\floorplancad\smoke-0001-0024.pred.json
python3 benchmark_reader.py C:\Users\teza_\studio-datasets\floorplancad\gt-test-00\0001-0024.gt.json C:\Users\teza_\studio-datasets\floorplancad\smoke-0001-0024.pred.json
```

Then compare door matches against the stored baseline row AND re-score in-process —
the benchmark CLI's `render_report` omits `per_type_gt` (dict values are filtered out
of the printed nums), so the door row is only observable via `score_pair`. Python,
NEVER PowerShell ConvertFrom-Json — PS 5.1 chokes on the cards' deep keys. cwd is
already `pipeline/scripts`, so `benchmark_reader` imports flat:

```powershell
python3 -c "import json
for line in open(r'C:/Users/teza_/studio-datasets/floorplancad/baseline-test-00/cards.jsonl', encoding='utf-8'):
    r = json.loads(line)
    if r.get('file') == '0001-0024' and 'card' in r:
        print('baseline door row:', r['card']['F4_openings']['per_type_gt'].get('door')); break
p = json.load(open(r'C:/Users/teza_/studio-datasets/floorplancad/smoke-0001-0024.pred.json', encoding='utf-8'))
doors = [o for o in p['openings'] if o['type'] == 'door']
print('new pred doors:', len(doors), 'stats:', p['meta']['swing_door_stats'])
assert len(doors) >= 3 and not any('rot' in o for o in p['openings'])
import benchmark_reader as B
g = json.load(open(r'C:/Users/teza_/studio-datasets/floorplancad/gt-test-00/0001-0024.gt.json', encoding='utf-8'))
row = B.score_pair(g, p)['F4_openings']['per_type_gt']['door']
print('new door row:', row)
assert row['matched'] > 0"
```

Gate: ≥3 `door`-typed openings on this sheet (7 GT single_doors, arcs verified at
r 731–975 mm); the re-scored `per_type_gt.door.matched` must be strictly greater than
the baseline row's — baseline matched is 0 on this sheet, so strictly-greater == the
block's `assert row['matched'] > 0`. If 0 doors emit, dump `swing_door_stats` and check
which gate zeroed out (`arcs_seen` → scaling bug; `arcs_in_band` → forgot to scale
rx/ry).

### Step 8 — full corpus rerun → `baseline-test-01` (detached; NEVER foreground)

Baseline run was 865 s wall-clock; the swing lane adds per-sheet leaf-pool scans —
budget **15–35 min**. The in-tool background lane caps at 10 min, so launch detached
from PowerShell (canon pattern; `run_baseline` writes report.md LAST — its final
`report.md` write — so its existence == run finished; cards.jsonl streams row-by-row,
a mid-run death keeps finished rows):

```powershell
Start-Process -FilePath python3 -ArgumentList 'svg_plan_reader.py','--baseline','C:\Users\teza_\studio-datasets\floorplancad\test-00','C:\Users\teza_\studio-datasets\floorplancad\gt-test-00','C:\Users\teza_\studio-datasets\floorplancad\baseline-test-01','overlays','6' -WorkingDirectory 'c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts' -RedirectStandardOutput 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-01-run.log' -RedirectStandardError 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-01-run.err'
```

CLI syntax law (the `__main__` usage block at the bottom of svg_plan_reader.py, which
item A extended with `walls oracle`): options are bare word-value pairs
(`overlays 6`, `limit 200`) — flags with dashes exit with usage. Poll for completion:
`Test-Path C:\Users\teza_\studio-datasets\floorplancad\baseline-test-01\report.md`;
progress prints every 100 sheets into the .log. Optional pre-flight: run once with
`limit 200` into a scratch out-dir first (~1-3 min, foreground is fine).

Expected in report.md: `2245 scored / 5502 gt files (skipped: {"svg-unit": 3257,
"svg-missing": 0, "error": 0})` — identical skip census to baseline-test-00; any
`error > 0` means the swing lane crashed on real geometry: read the error rows in
cards.jsonl (`r['skipped']=='error'`) before proceeding.

### Step 9 — analysis + delta report

Python (not PowerShell) over the new cards; hardcoded baseline reference numbers come
from `qa/reports/floorplancad-baseline-2026-07-06.md:35-44` (verified):
door 895/6,124 · sliding 733/835 · window 2,850/3,160 · opening 91/116 ·
F4 matched 4,569 / n_pred 159,582.

```powershell
python3 -c "import json
tot = {}; n_pred = 0; matched = 0; sub_hits = 0
for line in open(r'C:/Users/teza_/studio-datasets/floorplancad/baseline-test-01/cards.jsonl', encoding='utf-8'):
    r = json.loads(line)
    if 'card' not in r: continue
    f4 = r['card']['F4_openings']
    n_pred += f4['n_pred']; matched += f4['matched']
    sub_hits += f4['matched'] - sum(f4['subtype_confusion'].values())
    for t, row in (f4.get('per_type_gt') or {}).items():
        a = tot.setdefault(t, [0, 0]); a[0] += row['n_gt']; a[1] += row['matched']
for t, (n, m) in sorted(tot.items()):
    print(f'{t}: {m}/{n} = {100.0*m/n:.1f}%')
print('F4 matched', matched, 'n_pred', n_pred, 'precision', f'{100.0*matched/n_pred:.2f}%')
print('subtype hits (earned):', sub_hits)"
```

(`aggregate()` drops subtype data — benchmark_reader.py:352-385 — which is why subtype
hits are recomputed per card as `matched - sum(confusion.values())`; confusion holds
only MISmatches, benchmark_reader.py:269-273.)

Write `qa/reports/floorplancad-swing-door-2026-07-07.md` [NEW]: before/after table
(door/sliding/window/opening recall, F4 matched, n_pred, precision, subtype hits),
swing stats totals (sum `swing_door_stats` across preds or quote per-smoke-sheet),
honesty notes: (a) typed `door` is earned by arc+leaf/mirrored-double evidence;
(b) line-only door symbols remain unfindable by this lane (cite the 0001-0023
instance-6/8 pattern in prose, no corpus bytes); (c) precision still flooded pending
the wall-aware pass (item A); (d) detection recall untouched by design.

### Step 10 — strategy entry + commits

Append a dated entry to `docs/strategy.md` (tail, `## Session 2026-07-07<letter> —
swing-door arc lane` style). Commit ritual (standing law): scrutinize first, separate
logical commits, **NEVER `git add -A`**, never push:

```
git add pipeline/scripts/floorplancad_adapter.py pipeline/scripts/swing_door_candidates.py pipeline/scripts/test_swing_door_candidates.py pipeline/scripts/svg_plan_reader.py pipeline/scripts/test_svg_plan_reader.py
git commit -m "swing-door arc+leaf lane: first typed F4 detector (door recall X%->Y%)"
git add qa/reports/floorplancad-swing-door-2026-07-07.md docs/strategy.md
git commit -m "session 2026-07-07x wrap: swing-door lane corpus numbers + strategy entry"
```

## Edge cases a weaker model would miss

All personally verified in code this session:

1. **Sample the sweep, never the chord.** `_arc_extent_points` exists precisely because
   chord-only bboxes under-covered arc symbols by up to 66% and collapsed two-half-arc
   circles to zero area (`floorplancad_adapter.py:108-114` docstring). AND its sampling
   loop is `range(1, _ARC_SAMPLES)` (`:146`) — endpoints are EXCLUDED, so the arc
   record's `pts` must explicitly prepend the start and append the end (Step 2 does).
2. **F.6.5 lambda radius scaling** (`floorplancad_adapter.py:124-126`): when declared
   radii are too small for the endpoints, the spec scales them up. `arc_center_params`
   must return the SCALED radii — using the raw `d`-attribute radii mis-sizes `r`
   against the 500–2500 mm door band.
3. **Never regex-parse `d` yourself.** Arc flags/radii are consumed positionally via
   `_ARITY["A"]=7` (`floorplancad_adapter.py:104`; pinned by
   `test_walk_path_arc_consumes_flags_not_as_coords`, test_floorplancad_adapter.py:65-70);
   relative arcs add the current pen to endpoint args (`:210-211`); `M` implies lineto
   after the first pair (`:191`); malformed tails break-and-keep-prefix (`:181-182`).
   The accumulator inside `walk_path` inherits ALL of this for free — a parallel parser
   would diverge on every one of these.
4. **Arc collection must sit AFTER the transform skip.** `read_ink` skips-and-counts
   transform-bearing prims (its `if el.get("transform"):` branch incrementing
   `transforms_skipped`); arcs from a transformed path
   would be misplaced. Step 5d threads `arcs` through `_path_ink` inside the existing
   branch, so the skip applies automatically — do not "optimize" by collecting arcs in a
   separate pre-pass over the tree.
5. **`_path_ink` is called with ONE argument in an existing test**
   (`test_svg_plan_reader.py:145`) — the new `arcs` parameter must default to `None`.
6. **The sentinel pin.** Pair-lane emission (the loop appending
   `{"id": f"g{k:03d}", "type": "candidate", ...}` in `read_sheet`) must stay
   `type="candidate"`; `test_candidate_type_never_earns_subtype_credit`
   (test_svg_plan_reader.py:195-206) pins that history: an earlier `type='opening'`
   sentinel silently earned subtype credit against GT bare-opening symbols and flipped
   verdicts. ONLY the swing lane's evidence-backed candidates may say `door`; its
   arc-only survivors stay `candidate`.
7. **Never emit `rot` on openings** — mirror of mutant M6b
   (`test_floorplancad_adapter.py:314-317`): F2 reads elements only
   (`benchmark_reader.py` facing path), so an opening `rot` is scoring-invisible — a lie
   no metric can catch. The arc genuinely knows the hinge side; keep it OUT of the
   emission (evidence dict carries `r_mm/leaf/double` only).
8. **F4 verdict = min(recall, precision, subtype_accuracy)** when matched>0
   (`benchmark_reader.py:343-345`), subtype = case-insensitive string equality on
   matched pairs (`:268`). Typed doors make per-sheet PASS *theoretically* reachable —
   that is earned and fine, but the empty-wall flood (~71 candidates/sheet avg) keeps
   per-sheet precision tiny; do NOT chase verdict flips.
9. **Greedy one-to-one centre matching within OPEN_TOL=300 mm**
   (`benchmark_reader.py:252-267`, `:54`): GT draws a double door as ONE instance
   (class 4 → `"door"`), so an unmerged half-arc sits ~r/2 (≈400–500 mm for corpus
   median r≈1000) from the GT centre and BOTH halves miss. The mirrored-arc merge is a
   recall requirement, not cosmetics. Conversely: two adjacent single doors can have
   hinges ~2r apart too — the merge additionally requires non-hinge endpoints meeting
   within 300 mm (test 10 pins the non-merge case).
10. **Line-only door symbols exist** — verified in
    `test-00/0001-0023.svg`: instance-id 6 and 8 carry semantic-id 3 (single_door) yet
    are plain 8-unit line segments with no arc. Door recall cannot reach 100% here; do
    not loosen gates or type pair-runs as doors to chase it.
11. **Sink/fixture arc flood**: sinks (class 23) have ~50% arc share; basins are
    r<500 mm and full/half sweeps — the circular+quarter+band gate stack is the defense.
    Test 5 pins the band rejection. If corpus `emitted_candidate` dwarfs `emitted_door`
    with no recall gain, that is a REPORTED finding for a later tier-tuning slice, not a
    reason to silently drop weak emissions now.
12. **`sanitize_openings` semantics** (`benchmark_reader.py:223-241`): openings without
    numeric x/y are counted malformed and dropped; null w/d degrade to 0. Always emit
    numeric 0.1-rounded bbox fields.
13. **Blindness is behavioral + static.** The strip-equivalence twins
    (test_svg_plan_reader.py:69-117) bind EVERYTHING `read_sheet` calls — the new lane
    is automatically covered, which is why `swing_door_candidates.py` must never touch
    the SVG/XML itself. The static tripwire (test:120-140) scans ONLY
    `svg_plan_reader.py`: no code token containing `semantic`/`inkscape`/`INK_NS`/
    `instance_id`, no non-docstring string containing `semantic-id`/`instance-id`/
    `inkscape` — e.g. a variable named `semantic_arcs` fails the suite.
14. **`0001-0023` is a trap smoke sheet**: its gt.json is `units="svg-unit"`,
    `scale=None` (verified) — `run_baseline` would skip it and `--sheet` scoring would
    raise the units guard (`benchmark_reader.py:309-318`). Use `0001-0024` (mm,
    scale 100.0, 7 GT doors). Never guess scale for svg-unit sheets — 3,257 of 5,502
    skip by design (`run_baseline`'s svg-unit skip branch in svg_plan_reader.py).
15. **`render_overlay` draws pred openings as diagonal LINES** from (x,y) to
    (x+w,y+d) — door bboxes will render as diagonals in the 6 overlay PNGs. Cosmetic;
    leave it alone (the overlay try/except inside `run_baseline` must not error-count
    a scored sheet — don't touch that block).
16. **Baseline CLI options are bare word-value pairs** (the `__main__` usage block at
    the bottom of svg_plan_reader.py): `overlays 6`, `limit 200`; both values
    digits-only; anything else exits with usage.
17. **cards.jsonl analysis in python only** — PowerShell 5.1 `ConvertFrom-Json` chokes
    on the cards' deep keys (standing project note).
18. **`aggregate()` drops subtype data** (`benchmark_reader.py:352-385`) — corpus
    subtype hits must be recomputed per card as `matched - sum(subtype_confusion
    .values())` (confusion records mismatches only, `:269-273`).

## Acceptance criteria

1. `python3 -m pytest pipeline/scripts/ -q` from repo root → **N + 15 passed, 0 failed**
   (N pre-existing, recorded green in Step 0, + 13 new swing tests + 2 new reader
   tests). The count never dips below N at any step.
2. `python3 -m pytest pipeline/scripts/test_floorplancad_adapter.py -q` passes with
   ZERO modified tests — the Step 1/2 refactor is behavior-identical for existing
   callers (no gt regeneration, no `--batch`, gt-test-00 bytes untouched).
3. Blindness holds: `python3 -m pytest pipeline/scripts/test_svg_plan_reader.py -q`
   all green, including the two new tests and the pre-existing three-density
   strip-equivalence suite + static tripwire.
4. Smoke (Step 7): pred for `0001-0024` contains ≥3 openings with `type=="door"`, none
   of its openings carries a `rot` key, and the scorecard `per_type_gt.door.matched`
   strictly exceeds the baseline-test-00 row for the same file.
5. Full run (Step 8): `baseline-test-01/report.md` exists; census line reads
   `2245 scored / 5502` with `{"svg-unit": 3257, "svg-missing": 0, "error": 0}`.
6. The number moves: corpus `per_type_gt` **door matched > 895** (direction: UP; if
   below 1,200, dump summed `swing_door_stats` and diagnose gate attrition before
   writing the report — do not ship a report that cannot explain its own number).
7. No collateral recall damage: sliding matched ≥ 726 (≥99% of 733) and window
   matched ≥ 2,822 (≥99% of 2,850). Any larger drop = investigate before shipping.
8. Corpus subtype hits (`Σ matched − Σ confusion`) **> 0** for the first time.
9. `qa/reports/floorplancad-swing-door-2026-07-07.md` committed with the before/after
   table; `git status` shows NO corpus artifacts (no cards/preds/gt/pngs from
   studio-datasets) staged in either commit; `docs/strategy.md` gained exactly one
   appended dated entry.
10. Detection metrics identical to baseline-test-00 aggregate (recall 9.8% / precision
    14.3%) — this slice never touches `plan_cluster`; any detection movement is a bug.

## Do NOT

- Do NOT touch `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.claude/settings.json`,
  `.gitattributes` (hook-enforced, PR-only). No destructive shell, no push, no
  `git add -A`.
- Do NOT modify `pipeline/scripts/glazing_candidates.py`. The swing lane is a separate
  evidence channel by design (arc candidates have no parallel pair by construction —
  they must not inherit promote()'s pair requirement, and promote's 36-test suite pins
  every constant, including the gap_tol=0 wall-merge that a "unifying" refactor would
  break).
- Do NOT emit `type="opening"` from anything, ever (the historical verdict-flip bug);
  do NOT change pair-lane candidates' `type="candidate"`; do NOT invent new subtype
  strings inside the GT vocabulary (`door|sliding|window|opening`) without evidence
  that EARNS them — this slice earns exactly one: `door`.
- Do NOT emit `rot`, `indoor`, `floor`, or `kind` anywhere in the reader's output.
  Elements stay kind-less (pinned test:189); openings stay rot-less (M6b mirror).
  Missing data is missing — the scorer's honesty contract (unreported ≠ defaulted) is
  the whole point of this benchmark.
- Do NOT read annotation attributes anywhere in the lane: `swing_door_candidates.py`
  must never parse SVG/XML at all; `svg_plan_reader.py` must keep passing the
  behavioral strip-equivalence twins AND the static string scan.
- Do NOT guess scale for `svg-unit` sheets, pass a made-up `open_tol`, or "fix" the
  units guard (`benchmark_reader.py:309-318` raising is correct behavior).
- Do NOT overwrite or write into `baseline-test-00/` — it is the committed baseline
  reference. New run artifacts go to `baseline-test-01/` only, and stay OUTSIDE the
  repo (`C:/Users/teza_/studio-datasets/` — CC BY-NC corpus derivatives are never
  committed; only the distilled `qa/reports/*.md` enters git).
- Do NOT copy corpus SVG bytes into test fixtures — fixtures are self-authored
  synthetic geometry (replicating the symbol's numeric pattern is fine; file content
  is not).
- Do NOT run the full 5,502-sheet baseline in a foreground tool call (10-min cap kills
  it mid-run) — detached `Start-Process` + poll on `report.md` only.
- Do NOT loosen the radius band / sweep band / leaf tolerance to chase door recall
  without reporting the precision cost in the same table — false-accepts-to-zero
  outranks coverage in this repo.
- Do NOT regenerate gt-test-00 or run `floorplancad_adapter --batch` — the adapter
  edits in Steps 1-2 must not change emission (that is itself an acceptance check).
