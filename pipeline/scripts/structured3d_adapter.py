"""
structured3d_adapter.py -- Structured3D annotation_3d.json (+ bbox_3d.json) -> the
backwards-benchmark gt.json that benchmark_reader.py scores (the SECOND corpus adapter,
after floorplancad_adapter.py; research record docs/research/2026-07-06-paired-2d3d-
backlearn.md SS3 "3D-native tier" -- Structured3D landed in the plan-extraction memory
2026-07-07 as the F2/F3 ground-truth source).

    python structured3d_adapter.py <scene_dir> <out.json>
    python structured3d_adapter.py --batch <N|first:last> <out-dir>   # + manifest + summary
    python structured3d_adapter.py --selftest <out-dir>              # score gt-vs-gt

WHY THIS CORPUS UNLOCKS F3: FloorPlanCAD, the first adapter, carries NO indoor / floor /
rotation ground truth, so F2/F3/F5 scored UNWIRED on every prior corpus -- the indoor/
outdoor read (terrace-vs-lounge, balcony-vs-bedroom: the exact class of error the v4
self-audit review flagged live) had no answer key anywhere. Structured3D's per-room floor
polygons plus its balcony/garden OUTDOOR semantics give a machine-checkable indoor bool
per element (point-in-room-polygon of the bbox centroid). This adapter WIRES F3 for the
first time, and F4 (openings) + F6 (glazing) alongside it.

WHAT THE RAW ANNOTATION LOOKS LIKE (verified on scene_00000 + a 500/50-scene corpus scan,
not from the paper -- see the data-recipe in docs; all coordinates are mm, confirmed vs
junction magnitudes in the thousands and SOURCE.txt):
  - planes[]      {ID, normal, offset, type in {floor,ceiling,wall}}
  - junctions[]   {ID, coordinate:[x,y,z]} in mm; floor-boundary junctions have z=0
  - lines[]       {ID, direction, point}; an infinite line, its real segment endpoints are
                  the two junctions incident to it
  - lineJunctionMatrix  n_lines x n_junctions 0/1 incidence (a floor edge has exactly 2)
  - planeLineMatrix     n_planes x n_lines 0/1 incidence
  - semantics[]   {ID, planeID:[...], type}; type is a ROOM (bedroom/living room/kitchen/
                  bathroom/study/corridor/store room/studio/dining room), an OUTDOOR space
                  (balcony/garden), the ambiguous 'undefined', or a BOUNDARY (door/window/
                  outwall). A room semantic bundles exactly one floor + one ceiling + its
                  wall planes.
  - bbox_3d.json  [{ID, basis 3x3, centroid[x,y,z], coeffs[3 half-extents]}] -- oriented
                  boxes. NO class label lives here (kinds are only in the un-downloaded
                  render zips), so F1/F2 stay HONESTLY BLOCKED (see the honesty contract).

ROOM FLOOR-POLYGON RECIPE (verified closed on 264/264 rooms over 50 scenes, 0 failures):
take the room semantic's one floor plane fp; its edges are lines li with
planeLineMatrix[fp][li]==1; each edge's endpoints are junctions j with
lineJunctionMatrix[li][j]==1 (use coordinate[:2]); walk the edge set into an ordered loop.

UNITS VERDICT -- coeffs ARE mm half-extents; NO rescale is applied. A 50-scene / 7,947-
object corpus scan put the MEDIAN object max-horizontal-dim at 447 mm (furniture-plausible)
with 20% of objects <100 mm (genuine decor: cups, books, picture frames) and 61% in the
300-3000 mm furniture band. Object 0's coeffs ~[19,13,19] = a real ~38 mm table-top prop
(z-centroid 1040 mm), NOT a unit error. Large >10 m boxes exist (whole-wall/floor-spanning
annotations) -- a plausibility band should tolerate/flag them, never rescale the corpus.
meta.units='mm', so benchmark_reader's default 300 mm opening tol + 250 mm glaze-perp tol
apply directly with no caller-supplied open_tol.

F2 UNBLOCK (the code-side blocker is removed; F2 is now DATA-limited, not code-limited):
  Structured3D bbox_3d.json carries no class label, but the GT rot IS derivable (basis yaw).
  convert(labels={obj_id: kind}) accepts an OPTIONAL caller-supplied sidecar of REAL labels
  (from 3D-FRONT layout JSON, or render-mask pairing of the downloaded instance masks with the
  semantic masks in the render zips) -> a labeled element emits kind + rot and F2_facing scores.
  A labeled element ALSO re-emits x/y/w/d as the LOCAL un-yawed rect (2*coeffs along basis[0]/
  basis[1], centred on the centroid) so placement_gate.footprint() rebuilds the true oriented box
  from (rect, rot): the blind lane's already-yawed AABB would otherwise be re-rotated a SECOND time
  by footprint() and detection-miss at 90/270 (the double-rotation fix, 2026-07-09; blind lane
  keeps the AABB and stays byte-identical).
  No sidecar (the state on disk today) -> byte-identical blocked default, F2 UNWIRED. The kind
  is never guessed here (kind_priors-style suggestion is a PRED-side lane, never GT). The two
  real label recipes + the (now VALIDATED, no-conversion) rot convention are documented at
  ROT_CONVENTION.

wall_lines: every WALL plane's floor-level trace is emitted as gt['wall_lines'] ([{x1,y1,x2,y2}]
  mm) -- the plan skeleton synth_plan_2d.py draws so OUR reader can be RUN on a synthesized 2D
  plan and scored for real (F3 pred!=gt), and the input svg_plan_reader's oracle-walls lane reads.

HONESTY CONTRACT (matches benchmark_reader + floorplancad_adapter):
  - KIND IS BLOCKED BY DEFAULT (no labels sidecar). Emitted elements then carry NO `kind` key
    and NO `rot` key (rot is informational-only without a kind to face). This makes F2_facing
    score UNWIRED (score_facing skips every kind-less element) -- NEVER a fabricated kind.
    meta.kind_blocked states the reason loudly (and is null once a sidecar supplies real kinds).
    F1_identity is a SPECIAL
    case: score_identity has no empty-kind guard, so kind-less matched pairs score as a
    single '' bucket and verdict PASS on gt-vs-gt. It is IDENTITY-BLIND, not UNWIRED; the
    selftest asserts F1's per_kind keys are a subset of {''} (no real class fabricated),
    which is the honest claim here.
  - NO `floor` key. The corpus is single-storey; every element would be floor=True, making
    F5 uninformative. Omitting it lets F5 score UNWIRED (house doctrine: no silent pass).
  - indoor is emitted ONLY when the centroid lands in a room whose type is in INDOOR; a
    centroid in an OUTDOOR room (balcony/garden) gets indoor=False; a centroid in an
    'undefined' room or in NO room gets NO indoor key (skipped by score, counted+reported).
  - EVERY skip is counted and reported in meta: objects projecting to zero footprint area
    (dropped), centroids in no room, rooms whose polygon failed to close, scenes with no
    bbox file (elements n=0). n=0 / UNWIRED where a whole channel has no eligible data.

SCENES WITH NO BBOX FILE (exactly 4, enumerated NO_BBOX_SCENES): rooms/openings/glazing
still emit; elements report n=0 (no bbox file). 4 scenes over the 3,496 with bbox.

SELFTEST vs UNIT TESTS -- they are a PAIR, neither alone suffices. The gt-vs-gt selftest is a
SCHEMA / HONESTY-CONTRACT check: it catches parse-breaking drift (per-file guard), total OR
partial channel death (the coverage floor, not just n==0), and accidental kind/rot/floor
emission (F2/F5 UNWIRED + F1 subset-{''} asserts). It CANNOT catch drift that is symmetric
across gt==pred -- a coordinate-convention flip, a units-magnitude error, or an over-emitted
indoor flag all self-match with distance 0 and PASS. The correctness anchor is the synthetic
unit file test_structured3d_adapter.py: the exact-pinned bbox->footprint projection math and
the indoor True/False/no-key pins. Run BOTH -- the selftest proves the output is
benchmark_reader-clean, the unit tests prove the geometry + semantics are right.
"""
import glob
import json
import math
import os
import sys
from collections import Counter

ADAPTER_VERSION = "structured3d_adapter v1.0"

# dataset lives OUTSIDE the repo — override via STRUCTURED3D_ROOT env var
# (.env / shell); the literal below is only this machine's default
DATASET_ROOT = os.environ.get("STRUCTURED3D_ROOT", "C:/Users/teza_/studio-datasets/structured3d")
ANNO_ROOT = os.path.join(DATASET_ROOT, "annotation_3d", "Structured3D")
BBOX_ROOT = os.path.join(DATASET_ROOT, "bbox", "Structured3D")
DEFAULT_OUT = os.path.join(DATASET_ROOT, "gt-sample")

# room-type -> indoor bool (verified vocab over a 500-scene scan). 'undefined' is
# deliberately ABSENT -> emit no indoor key (benchmark_reader skips scoring it).
INDOOR = {
    "living room": True, "bedroom": True, "kitchen": True, "bathroom": True,
    "study": True, "corridor": True, "store room": True, "studio": True,
    "dining room": True,
    "balcony": False, "garden": False,
}
ROOM_TYPES = set(INDOOR) | {"undefined"}          # everything that owns a floor polygon
OPENING_TYPES = {"door": "door", "window": "window"}   # boundary semantics -> F4 vocab
OUTWALL_TYPE = "outwall"

# 4 scenes ship an annotation but no bbox_3d.json (verified enumeration). Wired live in
# run_batch (warns if the corpus grows an unlisted no-bbox scene) so it can't go stale silently.
NO_BBOX_SCENES = {"scene_01155", "scene_01714", "scene_01816", "scene_03398"}

# a footprint whose ROWS vs COLS (transpose) interpretation diverges by more than this (mm) on
# any of x/y/w/d is counted transpose-divergent -- the honest audit that replaced the retracted
# 'interpretation-invariant' claim in _box_footprint_xy.
TRANSPOSE_DIVERGENCE_MM = 50.0

KIND_BLOCKED_REASON = ("bbox_3d.json carries no per-object class label (labels live in the "
                       "un-downloaded render zips); kind + rot omitted -> F1 identity-blind, "
                       "F2 UNWIRED, never fabricated. Supply a --labels sidecar (caller's REAL "
                       "{obj_id: kind} from 3D-FRONT or render-mask pairing) to unblock F2")

# ROT CONVENTION -- VALIDATED (geometric oracle 2026-07-09, 4 independent methods unanimous; see
# qa/reports/f2-facing-convention-validated-2026-07-09.md). The emitted rot is the adapter's NATIVE
# yaw (see _box_footprint_xy): degrees CCW from world +X = the yaw of basis[0]. The PRIOR note here
# asserted "forward = basis[0]" and warned a ~+90 conversion was needed before a real reader could
# be scored -- BOTH are now REFUTED:
#   - basis[0] is the object's SIDE axis, not its front. It runs PARALLEL to the backing wall, and
#     basis[0]_xy is perpendicular to the true front to 0.00deg on 117/117 sampled objects (an EXACT
#     identity: (sin R,-cos R) is by construction basis[0] rotated -90deg, so basis[0] can NEVER be
#     the front). basis[0] is the longer/width axis in ~87%.
#   - the object's real (into-room) FRONT = (sin R, -cos R) = EXACTLY benchmark_reader's build_floor
#     front(R) applied to the SAME emitted R. So the emitted native-yaw VALUE is ALREADY in
#     build_floor convention: a perfect build_floor reader inverts front=(sin,-cos) to recover rot=R
#     and scores EXACT. There is NO offset to apply. Into-room agreement 94.5% (median 0deg) over 73
#     wall-backed strong-front objects; 100% for cabinets and tv_panels.
#   - the old "~+90 / native{0,90,180,270} vs build_floor{90,180,270,0}" arithmetic is real but it
#     re-encodes basis[0]-AS-front (the SIDE axis). Applying it to FACING would drive a correct
#     reader to angle_diff=90 -> the 'wrong' bucket: it CORRUPTS F2 -- the inverse of the old fear.
# RESIDUALS (documented; do NOT "fix" blindly): a ~5% left-handed (det(basis)<0) tail has
# front=+basis[1] and reads 180-flipped, but it sits in non-wall-backed / bed objects (0 in the
# scored wall-backed set) -> an empirical det<0 rot+180 flip gave 0 measured gain, so it is NOT
# applied. BEDS encode length in basis[0]-yaw, not facing -> exclude from strong-front facing.
# Near-square objects have an ambiguous side/front axis. STILL render-gated: that basis[1] is the
# SEMANTIC front (vs a mirror-symmetric side) -- wall geometry proves (sin,-cos) points INTO the room
# but cannot rule out a further fixed 90 for a symmetric symbol. LEAVE rot NATIVE; do NOT apply +90.
ROT_CONVENTION = ("native_yaw_deg_ccw_from_+x__==__build_floor_front=(sin,-cos)_rot__VALIDATED_"
                  "2026-07-09__basis[0]=SIDE(parallel_wall,perp_front_exact)__front=(sin,-cos)__"
                  "NO_offset_apply__~5pct_det<0_tail_180flip__beds_excluded")


def _lookup_label(labels, obj_id):
    """Caller-supplied per-object kind (str) for this scene, or None. Tries the int and str key
    (JSON object keys are strings); the kind is lowercased so benchmark_reader.norm_kind's
    synonym/casing rules apply. NEVER fabricates -- an absent id returns None and the element
    stays kind-less (F2 UNWIRED for it). A blank/whitespace label is treated as absent."""
    if not labels:
        return None
    v = labels.get(obj_id)
    if v is None:
        v = labels.get(str(obj_id))
    if v is None or not str(v).strip():
        return None
    return str(v).strip().lower()


# ---- geometry ----------------------------------------------------------------------------
def _room_polygon(fp, planes, lines, junc, plm, ljm):
    """Ordered (x,y) loop of a room's floor plane fp, or (None, reason). Edges are the lines
    incident to fp in planeLineMatrix; each edge's endpoints are its two incident junctions
    (lineJunctionMatrix); the edge set is walked into a single closed loop. Every failure
    mode is NAMED (no-edges / open-loop / no-close / degenerate) and COUNTED by the caller,
    never silently dropped -- 0/264 rooms failed on the 50-scene scan, but the guard stays."""
    edges = [li for li in range(len(lines)) if plm[fp][li]]
    if not edges:
        return None, "no-edges"
    adj = {}
    for li in edges:
        js = [jj for jj in range(len(junc)) if ljm[li][jj]]
        if len(js) != 2:
            continue                       # not a clean 2-endpoint floor edge: skip it
        a, b = js
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if not adj:
        return None, "no-edges"
    start = min(adj)                        # deterministic start (lowest junction ID index)
    loop, prev, cur = [start], None, start
    while True:
        nbrs = [n for n in adj[cur] if n != prev]
        if not nbrs:
            return None, "open-loop"
        nxt = nbrs[0]
        if nxt == start:
            break
        if nxt in loop:
            return None, "no-close"        # re-entered mid-loop without closing on start
        loop.append(nxt)
        prev, cur = cur, nxt
        if len(loop) > len(junc):
            return None, "no-close"
    if len(loop) < 3:
        return None, "degenerate"
    return [(junc[j]["coordinate"][0], junc[j]["coordinate"][1]) for j in loop], None


def _point_in_poly(x, y, poly):
    """Even-odd ray-cast point-in-polygon (poly = list of (x,y), implicitly closed)."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def _transpose(m):
    """3x3 transpose -- used ONLY by convert()'s transpose-sensitivity audit (the alternative
    basis[:,i]=local-axis-i reading), never by the committed footprint math below."""
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]


def _box_footprint_xy(basis, centroid, coeffs):
    """(x, y, w, d, rot) of an oriented bbox's axis-aligned XY footprint, mm.

    8 world corners = centroid + sum_i s_i * coeffs[i] * basis[i,:] over s in {+-1}^3, using
    basis ROWS as the local axes (basis[i,:] = local axis i). This is the SUN RGB-D /
    Structured3D corner convention -- the authoritative corner formula treats each ROW as an
    oriented axis scaled by its half-extent coeffs[i] -- and the code deliberately COMMITS to
    it. x/y = min corner, w/d = extent (min-corner + extent schema).

    NOT transpose-invariant -- the earlier claim that rows-vs-columns is 'immaterial' was
    wrong at corpus scale and is retracted. The footprint IS invariant to rows-vs-cols for
    properly-yawed / freely-rotated boxes (all 833 such objects over the first 200 scenes gave
    a rows-vs-cols diff of 0.0, and their AABB is exact). It is NOT invariant for 'tipped' /
    axis-swapped boxes where a horizontal local axis maps to vertical: over the first 200
    scenes (26,949 objects) 470 diverge by >50 mm, 11 of them furniture-scale (400-1731 mm;
    worst scene_00160 obj52 coeffs [208,33,898] -> ROWS 1796x416 mm vs COLS 65x1796 mm, a
    1731 mm swing). The choice materially fixes ~1.7% of footprints, so it is a real
    convention decision, not a negligible one -- convert() COUNTS the transpose-divergent
    population per scene into meta.transpose_divergent (threshold TRANSPOSE_DIVERGENCE_MM)
    rather than claiming invariance.

    rot (yaw, deg, CCW from world +X) = atan2(basis[0].y, basis[0].x), the yaw of local-x = basis[0].
    In the kind-less lane it is provenance only (score_facing skips kind-less elements). With a label
    it IS the facing GT -- and it is emitted AS-IS: this native yaw already equals the build_floor
    front rot (front(rot)=(sin,-cos) = the into-room front), VALIDATED 2026-07-09 (see ROT_CONVENTION
    above). basis[0] is the SIDE axis (parallel to the backing wall), NOT the front -- do NOT apply a
    +90 'reconcile' to make basis[0] the front; that would corrupt F2."""
    cx, cy, cz = centroid
    xs, ys = [], []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                wx = cx + sx * coeffs[0] * basis[0][0] + sy * coeffs[1] * basis[1][0] + sz * coeffs[2] * basis[2][0]
                wy = cy + sx * coeffs[0] * basis[0][1] + sy * coeffs[1] * basis[1][1] + sz * coeffs[2] * basis[2][1]
                xs.append(wx)
                ys.append(wy)
    x, y = min(xs), min(ys)
    w, d = max(xs) - x, max(ys) - y
    rot = math.degrees(math.atan2(basis[0][1], basis[0][0]))
    return x, y, w, d, rot


# ---- per-scene parse ---------------------------------------------------------------------
def _resolve_paths(scene_dir):
    """(annotation_path, bbox_path_or_None, scene_id) from a scene directory."""
    scene_id = os.path.basename(os.path.normpath(scene_dir))
    anno = os.path.join(scene_dir, "annotation_3d.json")
    bbox = os.path.join(BBOX_ROOT, scene_id, "bbox_3d.json")
    if not os.path.exists(bbox):
        bbox = None
    return anno, bbox, scene_id


def convert(scene_dir=None, anno_path=None, bbox_path=None, scene_id=None, split=None,
            labels=None):
    """Scene -> gt document (dict), coordinates in mm. Either pass scene_dir (paths are
    resolved against the dataset roots) or anno_path/bbox_path/scene_id directly (the unit
    tests feed synthetic dicts through the file path). A missing bbox file is NOT an error:
    rooms/openings/glazing still emit and elements report n=0 (no bbox file).

    labels (default None) is the OPTIONAL per-object kind sidecar for THIS scene: a dict
    {obj_id: raw_kind} of caller-supplied REAL labels (from 3D-FRONT or render-mask pairing --
    NEVER guessed here). When an object is labeled, its element gains `kind` (lowercased) AND
    `rot` (the native yaw, ROT_CONVENTION), which unblocks F2_facing. When labels is None (the
    default, and the state on disk today), output is byte-identical to the blocked baseline:
    no kind, no rot, F2 UNWIRED. This makes F2 data-limited, not code-limited."""
    if scene_dir is not None:
        anno_path, bbox_path, scene_id = _resolve_paths(scene_dir)
    scene_id = scene_id or "?"
    a = json.load(open(anno_path, encoding="utf-8"))
    planes = {p["ID"]: p for p in a["planes"]}
    junc = {j["ID"]: j for j in a["junctions"]}
    lines = a["lines"]
    plm, ljm = a["planeLineMatrix"], a["lineJunctionMatrix"]
    semantics = a["semantics"]

    # -- rooms -> polygons + indoor map -----------------------------------------------------
    rooms = []                 # (type, polygon, indoor-or-None)
    rooms_by_type = Counter()
    poly_failed = Counter()    # reason -> count
    for s in semantics:
        st = s["type"]
        if st not in ROOM_TYPES:
            continue
        floor_planes = [pid for pid in s["planeID"]
                        if pid in planes and planes[pid]["type"] == "floor"]
        if not floor_planes:
            poly_failed["no-floor"] += 1
            continue
        poly, reason = _room_polygon(floor_planes[0], planes, lines, junc, plm, ljm)
        if poly is None:
            poly_failed[reason] += 1
            continue
        rooms.append((st, poly, INDOOR.get(st)))   # 'undefined' -> None (no indoor key)
        rooms_by_type[st] += 1

    # -- openings (door / window) -----------------------------------------------------------
    openings = []
    open_counts = Counter()
    for s in semantics:
        st = s["type"]
        if st not in OPENING_TYPES:
            continue
        pts = []
        for pid in s["planeID"]:
            for li in range(len(lines)):
                if not plm[pid][li]:
                    continue
                for jj in range(len(junc)):
                    if ljm[li][jj]:
                        c = junc[jj]["coordinate"]
                        pts.append((c[0], c[1]))
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x, y = min(xs), min(ys)
        openings.append({"type": OPENING_TYPES[st], "x": round(x, 1), "y": round(y, 1),
                         "w": round(max(xs) - x, 1), "d": round(max(ys) - y, 1),
                         "id": f"op{s['ID']}"})
        open_counts[OPENING_TYPES[st]] += 1

    # -- glazing_lines: the single outwall boundary's floor-level wall segments -------------
    glazing = []
    for s in semantics:
        if s["type"] != OUTWALL_TYPE:
            continue
        for pid in s["planeID"]:
            if planes.get(pid, {}).get("type") != "wall":
                continue
            for li in range(len(lines)):
                if not plm[pid][li]:
                    continue
                js = [jj for jj in range(len(junc)) if ljm[li][jj]]
                if len(js) != 2:
                    continue
                c0, c1 = junc[js[0]]["coordinate"], junc[js[1]]["coordinate"]
                if abs(c0[2]) > 1e-6 or abs(c1[2]) > 1e-6:
                    continue               # floor-level segments only (both junctions z~=0)
                glazing.append({"x1": round(c0[0], 1), "y1": round(c0[1], 1),
                                "x2": round(c1[0], 1), "y2": round(c1[1], 1),
                                "kind": "outwall"})

    # -- wall_lines: every WALL plane's floor-level trace (both junctions z~=0), deduped by
    #    rounded endpoints. This is the plan SKELETON the 2D synthesizer (synth_plan_2d.py)
    #    draws so OUR reader can be run on it, AND the input svg_plan_reader's oracle-walls lane
    #    consumes (schema mirrors floorplancad_adapter: [{x1,y1,x2,y2}], mm). Distinct from
    #    glazing_lines (the outwall F6 GT): an outwall's own trace appears in both, by design --
    #    a real plan draws the envelope too. A shared party wall belongs to two rooms -> dedup.
    wall_lines = []
    seen_walls = set()
    for pid, pl in planes.items():
        if pl.get("type") != "wall":
            continue
        for li in range(len(lines)):
            if not plm[pid][li]:
                continue
            js = [jj for jj in range(len(junc)) if ljm[li][jj]]
            if len(js) != 2:
                continue
            c0, c1 = junc[js[0]]["coordinate"], junc[js[1]]["coordinate"]
            if abs(c0[2]) > 1e-6 or abs(c1[2]) > 1e-6:
                continue                   # floor-level segments only (both junctions z~=0)
            key = tuple(sorted(((round(c0[0], 1), round(c0[1], 1)),
                                (round(c1[0], 1), round(c1[1], 1)))))
            if key in seen_walls:
                continue
            seen_walls.add(key)
            wall_lines.append({"x1": round(c0[0], 1), "y1": round(c0[1], 1),
                               "x2": round(c1[0], 1), "y2": round(c1[1], 1)})

    # -- elements from bbox -----------------------------------------------------------------
    elements = []
    no_bbox = bbox_path is None
    zero_area_dropped = 0
    n_kinded = 0
    kinded_tipped_blinded = 0  # kinded boxes too TIPPED for a (w,d,rot) rect to carry -> AABB, rot dropped
    centroid_no_room = 0
    transpose_divergent = 0    # objects whose rows-vs-cols footprint diverges > threshold
    indoor_split = Counter()   # True / False / None
    if not no_bbox:
        boxes = json.load(open(bbox_path, encoding="utf-8"))
        for obj in sorted(boxes, key=lambda o: o["ID"]):   # deterministic order by ID
            x, y, w, d, rot = _box_footprint_xy(obj["basis"], obj["centroid"], obj["coeffs"])
            # honesty audit: the footprint is NOT rows-vs-cols invariant for tipped/axis-
            # swapped boxes (see _box_footprint_xy). Count -- never hide -- the divergent
            # population; counted over ALL objects (before the zero-area drop).
            tx, ty, tw, td, _tr = _box_footprint_xy(_transpose(obj["basis"]),
                                                    obj["centroid"], obj["coeffs"])
            if max(abs(tx - x), abs(ty - y), abs(tw - w), abs(td - d)) > TRANSPOSE_DIVERGENCE_MM:
                transpose_divergent += 1
            if w < 1.0 or d < 1.0:
                zero_area_dropped += 1
                continue                   # a zero-area box can never IoU-match, even itself
            rec = {"id": f"o{obj['ID']}", "x": round(x, 1), "y": round(y, 1),
                   "w": round(w, 1), "d": round(d, 1)}
            # indoor: point-in-room-polygon of centroid XY -> INDOOR map
            cx, cy = obj["centroid"][0], obj["centroid"][1]
            hit = None
            for (rt, poly, ind) in rooms:
                if _point_in_poly(cx, cy, poly):
                    hit = ind              # None for 'undefined' rooms
                    break
            if hit is None and not any(_point_in_poly(cx, cy, poly) for _rt, poly, _i in rooms):
                centroid_no_room += 1
            if hit is not None:            # only emit a real True/False, never a guess
                rec["indoor"] = hit
            indoor_split[hit] += 1
            # kind + rot ONLY when the caller supplied a REAL label for this object (F2 unblock).
            # Without a label: no kind, no rot (blocked default). rot is emitted ONLY with a kind
            # -- a rot without a kind has no facing to score and the honesty contract forbids it.
            lab = _lookup_label(labels, obj["ID"])
            if lab:
                rec["kind"] = lab
                # DOUBLE-ROTATION FIX (rot_reconcile ADJACENT FINDING, 2026-07-09). x/y/w/d above are
                # the already-yawed WORLD AABB. But a rot-carrying element is scored through
                # placement_gate.footprint(), which RE-ROTATES x/y/w/d by rot about the centre -- so
                # emitting the AABB + rot rebuilds a box rotated TWICE (transposed at 90/270 -> IoU
                # 0.25 -> DETECTION MISS on the commonest furniture facings; inflated at 45). It is
                # invisible to gt-vs-gt (both sides re-rotate identically), which is why the selftest
                # cannot catch it. Emit instead the LOCAL un-yawed rect -- 2*coeffs[0] along basis[0]
                # (forward, the rot axis) x 2*coeffs[1] along basis[1], centred on the centroid -- so
                # footprint(local, native_yaw) reconstructs the TRUE world AABB. Proven: footprint's
                # extents w|cos|+d|sin| / w|sin|+d|cos| with (w,d,rot)=(2c0,2c1,theta_n) equal
                # _box_footprint_xy's 8-corner AABB for a clean-yaw box.
                a, b = obj["coeffs"][0], obj["coeffs"][1]
                th = math.radians(rot)
                lw = 2 * a * abs(math.cos(th)) + 2 * b * abs(math.sin(th))
                ld = 2 * a * abs(math.sin(th)) + 2 * b * abs(math.cos(th))
                if abs(lw - w) <= 1.0 and abs(ld - d) <= 1.0:
                    # clean-yaw box: the local rect + rot faithfully rebuilds the world AABB.
                    rec["rot"] = round(rot, 1)
                    rec["x"], rec["y"] = round(cx - a, 1), round(cy - b, 1)
                    rec["w"], rec["d"] = round(2 * a, 1), round(2 * b, 1)
                else:
                    # TIPPED box (basis[2] tilts into XY, so the 8-corner AABB carries a coeffs[2]
                    # contribution the local face drops): NO (w,d,rot) rect can represent it, and the
                    # tiny local face would score a sub-visible footprint that never IoU-matches a real
                    # reader -- a SILENT, UNCOUNTED detection miss. Keep the WORLD AABB (x/y/w/d above)
                    # so detection + F1 stay correct, emit NO rot (F2 honestly unreported for it, never
                    # a fabricated facing), and COUNT it (house doctrine: every skip is tallied). Real
                    # labelled furniture is upright (basis[2]~=Z) so this is the rare degenerate tail.
                    kinded_tipped_blinded += 1
                n_kinded += 1
            # NO floor key (single-storey)
            elements.append(rec)

    meta = {
        "source": "structured3d", "adapter": ADAPTER_VERSION, "scene": scene_id,
        "split": split, "units": "mm",
        "n_elements": len(elements), "n_rooms": len(rooms),
        "rooms_by_type": dict(rooms_by_type),
        "n_openings": len(openings), "openings_by_type": dict(open_counts),
        "n_glazing": len(glazing), "n_wall_lines": len(wall_lines),
        "indoor_true": indoor_split[True], "indoor_false": indoor_split[False],
        "indoor_unknown": indoor_split[None],
        "zero_area_dropped": zero_area_dropped,
        "centroid_in_no_room": centroid_no_room,
        "transpose_divergent": transpose_divergent,
        "transpose_divergence_mm": TRANSPOSE_DIVERGENCE_MM,
        "rooms_polygon_failed": dict(poly_failed),
        "no_bbox_file": no_bbox,
        "labels_supplied": labels is not None,
        "n_kinded": n_kinded,
        "kinded_tipped_blinded": kinded_tipped_blinded,
        "rot_convention": ROT_CONVENTION if n_kinded else None,
        # kind is BLOCKED only in the default (no-labels) lane; with a labels sidecar the emitted
        # kinds are the caller's real data (F1/F2 wired for those objects), never fabricated here.
        "kind_blocked": KIND_BLOCKED_REASON if not n_kinded else None,
    }
    return {"meta": meta, "elements": elements, "openings": openings,
            "glazing_lines": glazing, "wall_lines": wall_lines}


# ---- batch -------------------------------------------------------------------------------
def _parse_slice(spec):
    """'200' -> (0, 200); 'first:last' (inclusive first, exclusive last) -> (first, last)."""
    if ":" in spec:
        lo, hi = spec.split(":", 1)
        return int(lo), int(hi)
    return 0, int(spec)


def run_batch(slice_spec, out_dir, labels_path=None):
    """Convert a slice of scenes (default first 200 readable) -> one <scene>.gt.json each +
    manifest.jsonl + summary.md. Deterministic sorted scene order; NO silent cap -- the log
    states converted-vs-skipped. A scene that raises costs ONE manifest row (ok:False),
    never the rest of the run (mirrors floorplancad_adapter.run_batch).

    labels_path (optional) is a corpus labels sidecar {scene_id: {obj_id: kind}} of caller
    REAL labels; each scene gets its own slice passed to convert() -> kind + rot emitted ->
    F2 unblocked. A scene absent from the file is simply blind (no kinds), never guessed."""
    os.makedirs(out_dir, exist_ok=True)
    corpus_labels = None
    if labels_path:
        corpus_labels = json.load(open(labels_path, encoding="utf-8"))
        if not isinstance(corpus_labels, dict):
            raise SystemExit(f"labels file {labels_path} must be a JSON object "
                             "{scene_id: {obj_id: kind}}")
    lo, hi = _parse_slice(slice_spec) if slice_spec else (0, 200)
    scenes = sorted(glob.glob(os.path.join(ANNO_ROOT, "scene_*")))
    if not scenes:
        raise SystemExit(f"no scene_* under {ANNO_ROOT}")
    sel = scenes[lo:hi]
    split = f"first{hi}" if lo == 0 else f"{lo}-{hi}"
    man_path = os.path.join(out_dir, "manifest.jsonl")
    n_ok = n_fail = n_nobbox = 0
    el_total = op_total = gl_total = wl_total = kinded_total = tipped_blinded_total = 0
    open_by_type, rooms_by_type = Counter(), Counter()
    indoor_true = indoor_false = indoor_unknown = 0
    zero_dropped = no_room = transpose_div_total = 0
    poly_fail_total = Counter()
    nobbox_seen = set()        # discovered no-bbox scenes -> checked against NO_BBOX_SCENES
    with open(man_path, "w", encoding="utf-8") as man:
        for k, sd in enumerate(sel):
            base = os.path.basename(os.path.normpath(sd))
            try:
                scene_labels = corpus_labels.get(base) if corpus_labels else None
                doc = convert(scene_dir=sd, split=split, labels=scene_labels)
            except Exception as e:         # one broken scene = ONE manifest row, never the run
                n_fail += 1
                man.write(json.dumps({"scene": base, "ok": False,
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
                continue
            with open(os.path.join(out_dir, base + ".gt.json"), "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False)
            m = doc["meta"]
            n_ok += 1
            if m["no_bbox_file"]:
                n_nobbox += 1
                nobbox_seen.add(base)
            el_total += m["n_elements"]
            op_total += m["n_openings"]
            gl_total += m["n_glazing"]
            wl_total += m["n_wall_lines"]
            kinded_total += m["n_kinded"]
            tipped_blinded_total += m.get("kinded_tipped_blinded", 0)
            open_by_type.update(m["openings_by_type"])
            rooms_by_type.update(m["rooms_by_type"])
            indoor_true += m["indoor_true"]
            indoor_false += m["indoor_false"]
            indoor_unknown += m["indoor_unknown"]
            zero_dropped += m["zero_area_dropped"]
            no_room += m["centroid_in_no_room"]
            transpose_div_total += m["transpose_divergent"]
            poly_fail_total.update(m["rooms_polygon_failed"])
            man.write(json.dumps({
                "scene": base, "ok": True, "units": m["units"],
                "n_elements": m["n_elements"], "n_openings": m["n_openings"],
                "n_glazing": m["n_glazing"], "n_wall_lines": m["n_wall_lines"],
                "n_kinded": m["n_kinded"],
                "kinded_tipped_blinded": m.get("kinded_tipped_blinded", 0),
                "n_rooms": m["n_rooms"],
                "indoor_true": m["indoor_true"], "indoor_false": m["indoor_false"],
                "indoor_unknown": m["indoor_unknown"],
                "zero_area_dropped": m["zero_area_dropped"],
                "centroid_in_no_room": m["centroid_in_no_room"],
                "no_bbox_file": m["no_bbox_file"]}) + "\n")
            if (k + 1) % 100 == 0:
                print(f"  {k + 1}/{len(sel)}")
    # keep the enumerated NO_BBOX_SCENES honest: a no-bbox scene this slice discovered that the
    # constant doesn't list means the enumeration went stale (behavior stays correct via the
    # os.path.exists check in _resolve_paths, but the constant must not silently drift).
    unlisted_nobbox = nobbox_seen - NO_BBOX_SCENES
    if unlisted_nobbox:
        print(f"WARNING: no-bbox scene(s) not in NO_BBOX_SCENES enumeration (constant is "
              f"stale): {sorted(unlisted_nobbox)}")
    summary = [
        "# Structured3D -> gt.json batch summary", "",
        f"- annotation root: `{ANNO_ROOT}`",
        f"- scene slice: [{lo}:{hi}]  selected: {len(sel)}  converted: {n_ok}  "
        f"parse-failed: {n_fail}  (no silent cap -- every selected scene is accounted for)",
        f"- scenes with no bbox file (elements n=0): {n_nobbox}",
        "",
        f"- elements (bbox footprints): {el_total}"
        + (f"  (kinded via labels sidecar: {kinded_total} -> F2 wired"
           + (f"; of those {tipped_blinded_total} TIPPED -> AABB+kind, rot dropped (F2 unreported, "
              f"detection kept)" if tipped_blinded_total else "") + ")" if corpus_labels
           else "  (no labels sidecar -> kind-less, F2 UNWIRED)"),
        f"- openings: {op_total}  by type: {dict(open_by_type.most_common())}",
        f"- glazing (outwall) segments: {gl_total}",
        f"- wall_lines (plan skeleton for the 2D synthesizer + oracle lane): {wl_total}",
        f"- rooms by type: {dict(rooms_by_type.most_common())}",
        f"- element indoor split: True={indoor_true}  False={indoor_false}  "
        f"unknown/no-key={indoor_unknown} (undefined-room or centroid-in-no-room)",
        "",
        f"- zero-area footprints dropped + reported: {zero_dropped}",
        f"- centroids in no room (indoor omitted): {no_room}",
        f"- transpose-divergent footprints (rows-vs-cols differ > {TRANSPOSE_DIVERGENCE_MM:.0f} "
        f"mm; committed to ROWS/SUN RGB-D convention): {transpose_div_total}",
        f"- room polygons failed to close: {dict(poly_fail_total) or 'none'}",
        "",
        "WIRED by this corpus: F3_indoor (first time on any corpus), F4_openings, "
        "F6_glazing" + (", F2_facing (labels sidecar supplied)" if corpus_labels else "")
        + ". " + ("F1/F2 use the caller's real labels for kinded objects; "
                  if corpus_labels else
                  "BLOCKED without a labels sidecar: F1 identity-blind + F2 UNWIRED (no bbox "
                  "class label -- supply --labels from render-mask pairing or 3D-FRONT); ")
        + "F5 UNWIRED (single-storey, floor key omitted).",
        "", f"adapter: {ADAPTER_VERSION}",
    ]
    sum_path = os.path.join(out_dir, "summary.md")
    with open(sum_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")
    print("\n".join(summary))
    print(f"\nwrote {man_path}\nwrote {sum_path}")


# ---- selftest ----------------------------------------------------------------------------
def run_selftest(out_dir):
    """Score every gt against ITSELF and assert the kind-less-but-indoor-carrying contract:
    detection PASS, F3_indoor PASS with n>0, F4_openings PASS, F6_glazing PASS (all WIRED),
    F2_facing + F5_floor UNWIRED, and F1_identity IDENTITY-BLIND (per_kind keys subset of
    {''} -- kind-less pairs score the empty bucket; there is no way to make F1 UNWIRED while
    geometry matches, so the honest assertion is that no REAL class was fabricated). The WIRED
    channels are held to a COVERAGE FLOOR (carry on a healthy majority of eligible files), not
    merely n>0, so a regression that silently collapses emission to a handful of scenes is
    caught, not passed as UNWIRED (house doctrine). One corrupt/foreign *.gt.json costs ONE
    row (per-file try/except), never the whole gate. NOTE the scope limit: gt-vs-gt is a
    SCHEMA / honesty-contract check and cannot catch drift symmetric across gt==pred (a
    coordinate-convention flip, a units-magnitude error, or an over-emitted indoor flag all
    self-match with distance 0); correctness rests on the synthetic unit file -- see the
    module docstring's SELFTEST vs UNIT TESTS note. F1's aggregate is printed with an explicit
    identity-blind caveat (B.aggregate strips per_kind, so the rolled-up number is meaningless)."""
    import benchmark_reader as B
    files = sorted(glob.glob(os.path.join(out_dir, "*.gt.json")))
    if not files:
        raise SystemExit(f"no *.gt.json under {out_dir}")
    bad = 0
    cards = []
    n_f3 = n_f4 = n_f6 = 0     # how many files CARRIED each WIRED channel (corpus-level proof)
    n_kinded_files = 0         # files carrying real labels -> F2 SCORED (not UNWIRED) for the headline
    elig_f3 = elig_f4 = elig_f6 = 0   # how many files were ELIGIBLE to carry it (upstream
                                      # signal present) -> denominator for the coverage floor
    for fp in files:
        try:
            doc = json.load(open(fp, encoding="utf-8"))
            card = B.score_pair(doc, doc)  # mm units -> default 300 mm tol, no open_tol needed
        except Exception as e:             # one corrupt/foreign gt.json costs ONE row, never
            bad += 1                       # the whole regression gate (mirrors run_batch)
            print(f"SELFTEST-FAIL {os.path.basename(fp)}: {type(e).__name__}: {e}")
            continue
        cards.append(card)
        # eligibility is read from meta -- UPSTREAM of each channel's own emission code, so a
        # bug that collapses that emission still leaves the file counted eligible and is caught
        # by the coverage floor below (not masked as a legitimately-empty channel).
        dm = doc.get("meta", {})
        if dm.get("n_elements", 0) > 0 and dm.get("n_rooms", 0) > 0:
            elig_f3 += 1                   # an indoor determination is possible
        if dm.get("n_rooms", 0) > 0:
            elig_f4 += 1                   # walls present -> door/window openings possible
            elig_f6 += 1                   # walls present -> an outwall boundary is possible
        problems = []
        if card["detection"]["n_gt"] and card["detection"]["verdict"] != "PASS":
            problems.append(f"detection={card['detection']['verdict']}")
        # WIRED channels: MUST carry data (n>0) AND pass on gt-vs-gt. A no-data channel is a
        # regression (silent UNWIRED), asserted against -- unless this scene legitimately has
        # none of that channel, tracked corpus-wide below.
        f3 = card["F3_indoor"]
        if f3["n"]:
            n_f3 += 1
            if f3["verdict"] != "PASS":
                problems.append(f"F3_indoor={f3['verdict']} (n={f3['n']})")
        f4 = card["F4_openings"]
        if f4["n_gt"]:
            n_f4 += 1
            if f4["verdict"] != "PASS":
                problems.append(f"F4_openings={f4['verdict']}")
        f6 = card["F6_glazing"]
        if f6["n_gt"]:
            n_f6 += 1
            if f6["verdict"] != "PASS":
                problems.append(f"F6_glazing={f6['verdict']}")
        # F5 is ALWAYS UNWIRED (single-storey, no floor key). F2 is UNWIRED only in the BLIND
        # lane; a gt built WITH a labels sidecar (kinds present) must SCORE F2 on gt-vs-gt (a
        # perfect self-match), so assert per the mode this file was built in.
        kinded = any("kind" in e for e in doc.get("elements", []))
        if kinded:
            n_kinded_files += 1
        if card["F5_floor"]["verdict"] != "UNWIRED":
            problems.append(f"F5_floor={card['F5_floor']['verdict']} (expected UNWIRED)")
        f2 = card["F2_facing"]
        if kinded:
            if f2["n"] and f2["verdict"] != "PASS":
                problems.append(f"F2_facing={f2['verdict']} (labels present -> expected PASS gt-vs-gt)")
        elif f2["verdict"] != "UNWIRED":
            problems.append(f"F2_facing={f2['verdict']} (expected UNWIRED, no labels)")
        # F1 identity-blind ONLY in the blind lane: no REAL class fabricated (per_kind subset of
        # {''}). With real caller labels, real kinds are expected and score 1.0 on gt-vs-gt.
        if not kinded:
            f1_kinds = set(card["F1_identity"]["per_kind"].keys())
            if not (f1_kinds <= {""}):
                problems.append(f"F1_identity fabricated classes {f1_kinds} (expected only '')")
        if any(card["malformed"].values()):
            problems.append(f"malformed={card['malformed']}")
        if problems:
            bad += 1
            print(f"SELFTEST-FAIL {os.path.basename(fp)}: {'; '.join(problems)}")
    # COVERAGE FLOOR (not a >0 total-death check): a WIRED channel must carry on a healthy
    # MAJORITY of ELIGIBLE files. This catches a regression that silently collapses emission to
    # a handful of scenes (e.g. indoor only when a room is first in semantics order) -- the
    # exact 'silent partial UNWIRED' the house doctrine forbids -- which the old n==0 check let
    # pass green. It is a BAND, not an exact baseline: legitimate tails sit above it (e.g. the
    # ~21/200 F3 scenes with only 'undefined' rooms or all-centroids-in-no-room; live healthy
    # numbers F3 179/~200, F4/F6 200/200 clear a 0.5 floor comfortably, a collapse to ~1 fails).
    COVERAGE_FLOOR = 0.5
    for name, carrying, elig in (("F3_indoor", n_f3, elig_f3),
                                 ("F4_openings", n_f4, elig_f4),
                                 ("F6_glazing", n_f6, elig_f6)):
        if elig == 0:                      # nothing upstream could carry it: report, don't
            print(f"SELFTEST-NOTE: {name} had 0 eligible files in this dir "
                  f"(no upstream data -- coverage floor N/A)")
            continue
        floor = math.ceil(COVERAGE_FLOOR * elig)
        if carrying < floor:
            bad += 1
            print(f"SELFTEST-FAIL: {name} carried on {carrying}/{elig} eligible files "
                  f"(< coverage floor {floor}) -- channel silently collapsed on most scenes")
    agg = B.aggregate(cards)
    print(f"selftest: {len(files)} files, {bad} failures; "
          f"F3-carrying={n_f3}/{elig_f3} F4-carrying={n_f4}/{elig_f4} "
          f"F6-carrying={n_f6}/{elig_f6}; aggregate: "
          f"det recall={agg['detection']['recall']}, F3 acc={agg['F3_indoor']['accuracy']}, "
          f"F4 recall={agg['F4_openings']['recall']}, F6 recall={agg['F6_glazing']['recall']}")
    # F1 is DELIBERATELY absent from the headline aggregate above: B.aggregate() strips
    # per_kind, so agg['F1_identity'] reads {n=<big>, accuracy=1.0} with NO signal that it is
    # the kind-less '' bucket -- a downstream rollup could mistake it for a solved, high-n
    # identity score (the silent-pass surface the house doctrine forbids). Surface the
    # blindness loudly instead of printing the flattering number as if it were real.
    f1 = agg["F1_identity"]
    if n_kinded_files:
        # real caller labels present -> F1 carries real classes, NOT the '' bucket. But keep the
        # house honesty: gt-vs-gt acc is a SELF-match (labels fed in come back out) -- it proves the
        # adapter preserves labels, it is NOT a blind-reader-vs-truth identity score.
        print(f"F1 identity: {n_kinded_files}/{len(files)} files carry REAL caller labels "
              f"(aggregate n={f1['n']} acc={f1['accuracy']} is a gt-vs-gt self-match -- proves labels "
              f"survive the adapter, NOT a blind-reader identity score; do not roll up as solved)")
    else:
        print(f"F1 identity-blind: aggregate would read n={f1['n']} acc={f1['accuracy']}, but that "
              f"is the kind-less '' bucket ONLY -- NOT a real identity score; do not roll up as solved")
    if bad:
        raise SystemExit(f"{bad} selftest failures")
    f2_state = (f"F2_facing WIRED on {n_kinded_files}/{len(files)} labelled files, F5 UNWIRED, "
                f"F1 labels real" if n_kinded_files else "F2/F5 UNWIRED, F1 identity-blind")
    print("selftest PASS: adapter output is benchmark_reader-clean "
          f"(F3/F4/F6 WIRED, {f2_state})")


def main(argv):
    if len(argv) >= 3 and argv[1] == "--batch":
        # python structured3d_adapter.py --batch <slice> <out-dir> [labels.json]
        run_batch(argv[2], argv[3] if len(argv) > 3 else DEFAULT_OUT,
                  labels_path=argv[4] if len(argv) > 4 else None)
    elif len(argv) >= 2 and argv[1] == "--selftest":
        run_selftest(argv[2] if len(argv) > 2 else DEFAULT_OUT)
    elif len(argv) >= 3:
        # python structured3d_adapter.py <scene_dir> <out.json> [labels.json]  (labels = {obj_id: kind})
        scene_labels = json.load(open(argv[3], encoding="utf-8")) if len(argv) > 3 else None
        doc = convert(scene_dir=argv[1], labels=scene_labels)
        with open(argv[2], "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        m = doc["meta"]
        print(f"{m['scene']}: {len(doc['elements'])} elements, {len(doc['openings'])} "
              f"openings, {len(doc['glazing_lines'])} glazing segs, "
              f"{m['n_rooms']} rooms, units={m['units']}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
