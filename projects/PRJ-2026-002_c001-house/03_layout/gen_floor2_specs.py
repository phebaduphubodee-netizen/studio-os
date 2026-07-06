"""
gen_floor2_specs.py — CLUSTER-DRIVEN scene-graph generator (master + sitting).

The old version claimed to read the drawing but HAND-TYPED every coordinate, so the
placed furniture drifted off the plan and one real piece was deleted as a "dimension
label". This version actually reads it: loose-furniture POSITIONS and SIZES are SNAPPED
to the deterministic drawn clusters (plan_cluster.extract_clusters — the same clusters the
placement GATE checks against), so a placed footprint reproduces the drawn bbox by
construction. The ONLY hand-authored inputs per loose piece are:
    kind      — what it is (a bbox has no identity)
    facing    — rotation (a bbox has no front; read from the symbol / owner). An owner-signed facing
                in placement-review.json `confirmed[]` (keyed by the manifest furnish id —
                "master_bedroom"/"sitting_room") OVERRIDES this hand-typed default via
                placement_gate.resolve_rot, the gate's OWN confirmed_rot matcher (single-source, so
                generator and gate never disagree). A signature may be a CARDINAL letter
                ({"facing":"W"}) OR an explicit numeric {"rot": 12} — the latter covers the NON-cardinal
                case (v4's angled terrace chairs at 12/335) that a cardinal facing cannot express. On
                the ENFORCED build path (manifest -> generator + gate) a regeneration re-applies a
                facing the owner already adjudicated instead of re-rolling it. The SAME wiring is now
                in the LIVE v4 generator (v4/gen_floor2_v4_specs.py — its snap() for cardinal pieces
                and angled() for the non-cardinal chairs). CAVEAT: a standalone diagnostic gate run on
                the raw master scene-graph keys off room.type ("bedroom_suite"), not the furnish id, so
                it will not see a "master_bedroom"-keyed signature (a known mode-2 quirk shared with
                dismissed[] — the enforced manifest invocation is the authoritative one).
    anchor    — a ROUGH (cx,cy) used only to pick WHICH cluster is this piece
No precise coordinates are typed, so there is nothing left to mistype.

Built-ins keep their BF-label size at a wall-anchored position (they live on the excluded
thick-line wall layer and have no furniture-ink cluster — the gate treats them leniently).
Wet fixtures (ensuite) are massing boxes the human confirms. The bed merges with the
over-bed casework into one blob, so it is the one MEASURED loose piece (gate = ON_INK).

WHAT THE GATE DOES AND DOES NOT VERIFY (be honest — this is the whole point of the studio):
because snap() sets a piece's footprint EQUAL to its drawn cluster, the gate's per-piece
IoU is ~1.00 BY CONSTRUCTION. That proves the coordinate was copied from the drawing exactly
(0-4mm) — it does NOT prove the machine read the blob's IDENTITY right. The gate's genuinely
independent guarantees are (1) COMPLETENESS — every drawn cluster is either claimed or listed
UNPLACED for a human, so nothing drawn is silently dropped; and (2) NO-FLOATING — a hand-placed
piece on empty floor hard-FAILs. Cluster IDENTITY (is this blob a bench, a door-swing, or two
merged pieces?) remains a HUMAN call, surfaced in the REVIEW checklist. FACING is an owner-SIGNED
call (placement-review.json confirmed[]), applied here (and in the live v4 generator) so a
regeneration through the manifest path survives it — cardinal or non-cardinal (see the facing note
above). This generator adds a curve/shape sanity check + snap-distance guard so an anchor cannot
quietly grab the wrong cluster, but it does not replace the human identity sign-off.

    python gen_floor2_specs.py <plan.pdf> <out_overlay.png> <layout_dir>

Emits both scene-graphs (absolute mm, offset 0,0), a MATCH REPORT (piece -> cluster id +
snap distance + any curve/shape mismatch, and any drawn cluster no piece claimed), and a
self-verify overlay.

Pure logic (to_spec / match / snap / bf_spec / room_zone; facing via placement_gate.resolve_rot) is import-testable
without a PDF (fitz/matplotlib/plan_cluster load inside main); only main() reads the plan.
"""
import json
import math
import os
import sys

try:                                      # Windows stdout is cp1252 — the Thai names crash it
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# The deterministic clusterer + the gate's owner-signed-facing matcher both live in
# pipeline/scripts. Put it on the path robustly (works run from the repo root OR the layout dir)
# BEFORE importing the pure gate helper. plan_cluster + fitz + matplotlib load inside main().
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (_HERE, os.path.join(_REPO, "pipeline", "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# SINGLE SOURCE OF TRUTH for 'what facing did the owner sign': resolve_rot IS the gate's own
# matcher (placement_gate.confirmed_rot) wrapped for the generator, so the two can never disagree
# about an owner-signed facing — cardinal OR non-cardinal. Importing it (not re-implementing) is what
# keeps them in lock-step. (placement_gate's top level is stdlib-only — plan_cluster loads lazily
# inside run() — so this import needs no PDF.)
from placement_gate import resolve_rot, load_confirmed

SCALE, OX, OY = 26.45, 171.2, 596.5       # this sheet's calibration (mirrors plan_cluster)
CLOSE_MM = 18.0                            # same close as the gate default
PAGE = 1

# facing -> rotation for build_floor furniture (front = -Y at rot0; front vector after rot:
#   rot0->S, 90->E, 180->N, 270->W). CARDINAL ONLY: a cardinal rot keeps the rendered
#   footprint axis-aligned == the drawn cluster bbox (a diagonal rot inflates the bbox and
#   would no longer match its cluster — the old 30/330 tub-chair splay was exactly that).
FACE_ROT = {"S": 0, "E": 90, "N": 180, "W": 270}


def to_spec(name, kind, cx, cy, wx, hy, rot, h, **extra):
    """drawn bbox (centre cx,cy; extents wx=EW, hy=NS) + cardinal rot -> spec item.
    build_floor renders (w,d) rotated by rot about the centre; for rot in {90,270} the
    axis-aligned footprint swaps, so we pre-swap here to keep the footprint == (wx,hy)."""
    if rot in (90, 270):
        w, d = hy, wx
    else:
        w, d = wx, hy
    it = {"name": name, "kind": kind, "x": round(cx - w / 2), "y": round(cy - d / 2),
          "w": round(w), "d": round(d), "h": h}
    if rot:
        it["rot"] = rot
    it.update(extra)
    return it


# --------------------------------------------------------------- cluster matching
_REPORT = []            # (room, name, kind, cluster_id, dist_mm, snapped_bbox, curve_mismatch)

# Curve/shape sanity is TRI-STATE. Only CLEAR cases carry an expectation: seating + round tables
# are ORGANIC (curved); wall casework (cabinet/console/tv/desk) is RECTILINEAR. Ambiguous kinds
# (bench, side_table, table, bed, stool, ottoman) are drawn either way — no expectation, no flag.
# The expectation prevents an armchair from silently claiming a cabinet's blob (a swap the gate
# CANNOT catch — it only checks footprint-vs-any-cluster).
_CURVED_KINDS = {"armchair", "sofa", "loveseat", "chair"}
_RECT_KINDS = {"tv_console", "cabinet", "console", "desk", "wardrobe", "headboard", "media"}


def _wants_curve(kind, shape):
    """True = expect organic, False = expect rectilinear, None = no expectation (don't penalise)."""
    if shape == "round" or kind in _CURVED_KINDS:
        return True
    if kind in _RECT_KINDS:
        return False
    return None


def _mism(cluster, want):
    return want is not None and bool(cluster.get("curve")) != want


def match(anchor, kind, shape, clusters, claimed, max_dist=1100, mismatch_penalty=350):
    """Nearest UNCLAIMED drawn cluster to the anchor, with a SOFT penalty for a CLEAR curve/shape
    mismatch (a mismatched cluster wins only if it is clearly the nearest). Returns
    (cluster|None, true_distance_mm, curve_mismatch_bool)."""
    ax, ay = anchor
    want = _wants_curve(kind, shape)
    best, bestscore = None, 1e18
    for i, c in enumerate(clusters):
        if i in claimed:
            continue
        cx, cy = c["x"] + c["w"] / 2.0, c["y"] + c["d"] / 2.0
        dd = math.hypot(cx - ax, cy - ay)
        score = dd + (mismatch_penalty if _mism(c, want) else 0.0)
        if score < bestscore:
            bestscore, best = score, i
    if best is None:
        return None, 1e18, False
    c = clusters[best]
    true_d = math.hypot(c["x"] + c["w"] / 2.0 - ax, c["y"] + c["d"] / 2.0 - ay)
    if true_d > max_dist:
        return None, true_d, False
    claimed.add(best)
    return c, true_d, _mism(c, want)


def snap(room, name, kind, clusters, claimed, anchor, face, h, confirmed=None, **extra):
    """Emit a loose piece AT the exact bbox of the best drawn cluster for its anchor+kind.
    face = 'S'/'E'/'N'/'W' cardinal. Records the source cluster id + snap distance in the spec
    (honest provenance). If no cluster is within reach we fall back to a 500x500 box at the
    anchor: for a strict furniture kind the gate then HARD-FAILs it (an honest miss that blocks
    the build until the anchor/plan is fixed — NOT a silent guess).

    `confirmed` = the room's owner-signed facing ledger (placement-review.json confirmed[]). A
    signed facing OVERRIDES the hand-typed `face` via placement_gate.resolve_rot (single-source with
    the gate — the SAME confirmed_rot matcher facing_flags checks); absent a signature the hand-typed
    face is used unchanged (byte-identical to the old generator). The facing is resolved AFTER the
    cluster match so the signature's size guard sees the piece's real footprint. The owner's signature
    is AUTHORITATIVE: the gate suppresses its facing flag once the built rot matches the sign. A
    180-deg correction (the common facing error) leaves the axis-aligned footprint bbox unchanged
    (to_spec's (w,d)-preswap cancels the gate's rotation), so placement IoU is unaffected. NOTE: snap
    is for CARDINAL pieces — signing a non-cardinal rot here re-orients an axis-aligned snapped
    footprint and the gate will honestly flag the drift; non-cardinal facings belong on angled pieces
    (v4's angled(), which reads a true drawn angle)."""
    cl, dist, mismatch = match(anchor, kind, extra.get("shape"), clusters, claimed)
    if cl is None:
        rot, fsrc = resolve_rot(name, FACE_ROT[face], 500, 500, confirmed)
        it = to_spec(name, kind, anchor[0], anchor[1], 500, 500, rot, h,
                     note="NO drawn cluster within reach of the anchor — hard-FAILs the gate "
                          "until the anchor/plan is fixed (honest miss, not a guess)", **extra)
        if fsrc:
            it["facing_source"] = fsrc
        _REPORT.append((room, name, kind, None, dist, (it["x"], it["y"], it["w"], it["d"]), False))
        return it
    cx, cy = cl["x"] + cl["w"] / 2.0, cl["y"] + cl["d"] / 2.0
    rot, fsrc = resolve_rot(name, FACE_ROT[face], cl["w"], cl["d"], confirmed)
    it = to_spec(name, kind, cx, cy, cl["w"], cl["d"], rot, h,
                 cluster=cl["id"], snap_mm=round(dist), **extra)
    if fsrc:
        it["facing_source"] = fsrc
    _REPORT.append((room, name, kind, cl["id"], dist, (it["x"], it["y"], it["w"], it["d"]), mismatch))
    return it


# Built-in sizes are LOCKED to the sheet's BF labels (W run-length, D depth, H — mm).
# For a wall-run cabinet, W is ALONG the wall, D is into the room. bf_spec() applies that.
BF = {"BF09-3": (3300, 600, 2800), "BF10": (2500, 600, 2800), "BF11": (3200, 600, 2800),
      "BF12-1": (1575, 400, 2800), "BF12-2": (700, 400, 2800), "BF13": (4100, 300, 500),
      "BF14": (3250, 100, 2800)}


def bf_spec(name, code, kind, cx, cy, run, h=None, **extra):
    """Built-in placed at a wall centre (cx,cy) with size taken from the BF label.
    run='NS' -> length runs north-south (wall on E/W); run='EW' -> length runs east-west.
    Built-ins are NOT snapped to clusters: they are label-authoritative wall casework the
    gate checks leniently (they may be drawn on the excluded thick-line layer)."""
    W, D, H = BF[code]
    wx, hy = (D, W) if run == "NS" else (W, D)
    return to_spec(name, kind, cx, cy, wx, hy, 0, h or H, **extra)


def room_zone(outline, subrooms, pad=150.0):
    """Cluster zone = bbox of the room outline ∪ subroom outlines, padded — IDENTICAL to
    placement_gate._room_zone, so the generator and the gate extract the SAME clusters."""
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    for sr in subrooms:
        for p in sr:
            xs.append(p[0]); ys.append(p[1])
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ============================================================ ROOM OUTLINES (wall-snapped)
# East master/sitting party wall measured at x~5550 (master interior) / x~5750 (sitting
# interior); sitting east interior wall x~10650; ensuite/closet partition x~3200; the
# ensuite/closet wing north exterior wall y~8600. South wall at y~-450: the bed head has a
# nightstand NICHE (thick walls y~0..-450) on BOTH sides (owner-confirmed: identical lamp
# symbols), so the room extends to -450 (my y=0 origin was an interior line, not the glazing).
# These feed BOTH the cluster zone and the rendered floor zones so colours sit inside the walls.
MASTER_OUTLINE = [[0, -450], [5550, -450], [5550, 6250], [5650, 6250], [5650, 8600], [0, 8600]]
# 2026-07-05 owner option (ก): NO separate walk-in closet ROOM. The north wing = ensuite (left,
# extracted walls: W x77, S y5923, up to the N wall y8574) + an open WARDROBE BAY (right of the
# ensuite) that is part of the dressing. BF09-1 is a ~5.2m L-shaped wardrobe wrapping that bay's
# north + east walls (read from the drawn wardrobe outline, not a small closet box).
MASTER_SUB = [
    [[0, 2650], [5550, 2650], [5550, 5850], [0, 5850]],                                  # dressing
    [[0, 5850], [3150, 5850], [3150, 8600], [0, 8600]],                                  # ensuite (full height to N wall)
    [[3150, 5850], [5550, 5850], [5550, 6250], [5650, 6250], [5650, 8600], [3150, 8600]],  # wardrobe bay (was 'closet')
]
SITTING_OUTLINE = [[5750, 0], [10650, 0], [10650, 6250], [5750, 6250]]


def main():
    import fitz
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.patches import FancyArrow, Polygon
    from plan_cluster import extract_clusters

    PDF = sys.argv[1]
    OUT_OVERLAY = sys.argv[2]
    LAYOUT_DIR = sys.argv[3]

    # Owner-signed facings (placement-review.json, same dir as the scene-graphs). A signed facing is
    # applied OVER the hand-typed default so a regeneration cannot silently re-roll an adjudicated
    # facing. Read defensively — a missing/malformed ledger -> no signatures (hand-typed faces),
    # never a crash. Filter by room exactly as the gate does (room match or '*').
    led_path = os.path.join(LAYOUT_DIR, "placement-review.json")
    confirmed_all = []
    if os.path.exists(led_path):
        try:
            confirmed_all = load_confirmed(json.load(open(led_path, encoding="utf-8")))
        except (ValueError, OSError, TypeError):
            confirmed_all = []
    confirmed_master = [e for e in confirmed_all if e.get("room") in ("master_bedroom", "*")]
    confirmed_sitting = [e for e in confirmed_all if e.get("room") in ("sitting_room", "*")]
    print(f"placement-review.json: {len(confirmed_all)} owner-signed facing(s) "
          f"({len(confirmed_master)} master, {len(confirmed_sitting)} sitting)")

    master_zone = room_zone(MASTER_OUTLINE, MASTER_SUB)
    sitting_zone = room_zone(SITTING_OUTLINE, [])
    mc = extract_clusters(PDF, PAGE, master_zone, CLOSE_MM, calib=(SCALE, OX, OY))["items"]
    sc = extract_clusters(PDF, PAGE, sitting_zone, CLOSE_MM, calib=(SCALE, OX, OY))["items"]
    m_claimed, s_claimed = set(), set()

    # ---------------------------------------------------------------- MASTER pieces
    master_items, master_builtins, master_fix = [], [], []

    # BED — MEASURED (head EAST against the BF14 slat, foot faces the west TV). It merges with
    # the over-bed BF09-3 casework into one blob, so it has no clean cluster: gate = ON_INK,
    # flagged for the human. 7'x6.5' -> E-W(head-foot) 1981, N-S(width) 2134. Facing "W" (rot 270,
    # foot faces the west TV) is the hand-typed default; an owner-signed facing overrides it too
    # (the bed is the one facing piece placed by direct to_spec rather than snap()).
    _bed_rot, _bed_src = resolve_rot("เตียง 7'x6.5' หัวตะวันออก", FACE_ROT["W"], 1981, 2134, confirmed_master)
    _bed = to_spec("เตียง 7'x6.5' หัวตะวันออก", "bed", 4115, 1090, 1981, 2134,
                   _bed_rot, 600,
                   note="head EAST vs BF14 slat; foot faces the west TV; "
                        "measured (bed merges with built-ins = no clean cluster)")
    if _bed_src:
        _bed["facing_source"] = _bed_src
    master_items.append(_bed)
    # FOOT BENCH — the drawn 504x1008 ORGANIC piece at the bed foot the old gen DELETED as a
    # 'dimension label'. It is a real drawn piece (the '7'x6.5' TEXT is a separate item inside
    # the bed). Recovered by snapping to its cluster; identity (bench/ottoman) = owner-confirm.
    master_items.append(snap("master_bedroom", "ม้านั่งปลายเตียง (bench)", "bench", mc, m_claimed,
                             (2898, 1130), "N", 450, confirmed=confirmed_master,
                             note="recovered organic cluster at the bed foot; confirm identity"))
    # NIGHTSTANDS flank the bed head (east): NE corner + SE wall niche. Owner-confirmed BOTH are
    # identical bedside tables (same table-lamp symbol); both are clean 300x300 organic clusters now
    # that the zone reaches the south niche (y-450) -> both SNAPPED, no hand-typing.
    master_items.append(snap("master_bedroom", "โต๊ะข้างเตียง เหนือ", "side_table", mc, m_claimed,
                             (4944, 2456), "S", 520, confirmed=confirmed_master, note="NE corner of the bed head"))
    master_items.append(snap("master_bedroom", "โต๊ะข้างเตียง ใต้", "side_table", mc, m_claimed,
                             (4944, -196), "N", 520, confirmed=confirmed_master, note="SE wall niche south of the bed head"))
    # DESK CHAIR — pulled up to the BF11 work desk on the west wall; faces W into the desk.
    master_items.append(snap("master_bedroom", "เก้าอี้ทำงาน (หันเข้าโต๊ะ W)", "armchair", mc, m_claimed,
                             (1125, 4253), "W", 750, confirmed=confirmed_master, note="pulled up to the BF11 work desk; faces W"))
    # TV CONSOLE on the WEST wall — the bed foot faces it (owner point B).
    master_items.append(snap("master_bedroom", "ตู้/ชั้นวางทีวี ผนังตะวันตก", "tv_console", mc, m_claimed,
                             (606, 1151), "S", 700, confirmed=confirmed_master, note="TV shelf on the west wall the bed foot faces"))

    # BUILT-INS from BF labels (size WxDxH mm; label-authoritative, position on the wall)
    # BF14 length = 3250 (owner-confirmed the label 325x10x280CM is authoritative, 2026-07-05; the
    # earlier 2700 was a drawn-slat mis-measure). Slat runs N-S on the east wall; centre keeps the
    # head aligned, 3250 spans y~-275..2975 inside the 6700mm east wall.
    master_builtins.append(to_spec("ผนังระแนงหัวเตียง BF14.325x10x280", "headboard",
                                   5250, 1350, 100, 3250, 0, 2800))
    # kind='cabinet' (NOT 'desk'): a built-in worktop is lenient wall casework. 'desk' is a STRICT
    # furniture kind in the gate, which would hard-FAIL this correctly-placed built-in if the plan
    # ever drew it on the excluded thick-line layer (no furniture-ink under it). Renders as a box.
    master_builtins.append(bf_spec("โต๊ะทำงาน built-in BF11.320x60x280", "BF11", "cabinet",
                                   300, 4500, "NS", h=750))
    master_builtins.append(bf_spec("ตู้เสื้อผ้าเหนือเตียง BF09-3.330x60x280", "BF09-3", "wardrobe",
                                   3450, 3250, "EW"))
    # ---- ENSUITE BATHROOM (owner point B) — wet fixtures render as massing boxes, human confirms
    ensuite_fix = []
    ensuite_fix.append(bf_spec("อ่างล้างหน้าคู่ BF10.250x60x280", "BF10", "vanity_double",
                               1900, 6350, "EW", h=850, note="south wall; two basins"))
    ensuite_fix.append(to_spec("โถสุขภัณฑ์ WC", "toilet", 380, 6340, 380, 690, 0, 400,
                               note="SW corner, against the west wall"))
    ensuite_fix.append(to_spec("อ่างอาบน้ำ (bathtub)", "bathtub", 2240, 7995, 1360, 870, 0, 550,
                               note="against the north wall"))
    ensuite_fix.append(to_spec("ที่อาบน้ำฝักบัว (shower)", "shower", 510, 8025, 780, 950, 0, 2200,
                               note="NW corner glass enclosure"))
    # ---- WARDROBE BAY (owner 2026-07-05 option ก) — BF09-1 = a ~5.2m L-shaped wardrobe read from
    # the DRAWN wardrobe outline (front at y7974 x3254..5654, turning down the east wall x5054 to
    # y6250). Modelled as its two drawn legs. The '520'=5.2m label is the L total incl. the corner
    # return (the two visible legs measure ~4.1m; the balance is the internal corner unit/returns).
    # BF09-2 (1.5m) IS labelled on the sheet but its wall is not yet unambiguous from the vector —
    # OMITTED here on purpose (honest miss, flagged for owner to point the wall; not guessed).
    wardrobe_fix = []
    wardrobe_fix.append(to_spec("ตู้เสื้อผ้า BF09-1 ผนังเหนือ (ขา L ของ 5.2m)", "wardrobe",
                                4454, 8274, 2400, 600, 0, 2800,
                                note="BF09-1 north leg 2.4m, along the wardrobe-bay north wall (faces S)"))
    wardrobe_fix.append(to_spec("ตู้เสื้อผ้า BF09-1 ผนังตะวันออก (ขา L ของ 5.2m)", "wardrobe",
                                5350, 7112, 600, 1724, 0, 2800,
                                note="BF09-1 east leg ~1.7m, along the east wall x5650 down to y6250 (faces W)"))

    # ---------------------------------------------------------------- SITTING pieces
    sit_items, sit_builtins = [], []
    # SOFA — faces EAST toward the round accent table.
    sit_items.append(snap("sitting_room", "โซฟา 3 ที่นั่ง", "sofa", sc, s_claimed,
                          (8164, 4652), "E", 800, confirmed=confirmed_sitting, note="faces EAST toward the round accent table"))
    # TUB CHAIRS — owner: face OUT toward the terrace TREES (south). STRAIGHTENED to face south
    # (was a drawn 30/330 splay = the 'เบี้ยว' tilt the owner flagged; a cardinal facing also
    # keeps each chair's footprint == its drawn cluster).
    sit_items.append(snap("sitting_room", "เก้าอี้ tub ซ้าย (หันออกสู่ระเบียง)", "armchair", sc, s_claimed,
                          (6331, 950), "S", 750, confirmed=confirmed_sitting, note="faces the terrace planters (south)"))
    sit_items.append(snap("sitting_room", "เก้าอี้ tub ขวา (หันออกสู่ระเบียง)", "armchair", sc, s_claimed,
                          (7633, 1403), "S", 750, confirmed=confirmed_sitting, note="faces the terrace planters (south)"))
    # ROUND accent tables (snapped to their drawn circles; render round).
    sit_items.append(snap("sitting_room", "โต๊ะกลม (ระหว่างเก้าอี้)", "side_table", sc, s_claimed,
                          (6916, 1412), "S", 450, confirmed=confirmed_sitting, shape="round"))
    sit_items.append(snap("sitting_room", "โต๊ะกลม (ข้างโซฟา)", "side_table", sc, s_claimed,
                          (9466, 4664), "S", 450, confirmed=confirmed_sitting, shape="round"))
    # (NO storage cabinet at x~6250..7150 — owner point A: the plan draws a DOOR there. The
    #  clusterer reads the door-swing as furniture ink (unplaced 894x948 rect); a DOOR is not a
    #  piece. Left unmatched on purpose; the gate lists it for the human to dismiss.)
    # BUILT-INS (BF labels; wall-positioned; lenient in the gate)
    sit_builtins.append(bf_spec("ตู้โชว์/มีเดีย BF12-1.157.5x40x280", "BF12-1", "cabinet",
                                5920, 5408, "NS"))
    sit_builtins.append(bf_spec("คอนโซล+กล้วยไม้ BF12-2.70x40x280", "BF12-2", "cabinet",
                                6440, 2410, "EW", h=800))
    sit_builtins.append(bf_spec("ชั้นวางเตี้ย ผนังตะวันออก BF13.410x30x50", "BF13", "cabinet",
                                10530, 4100, "NS", h=500))

    # ---------------------------------------------------------------- write scene-graphs
    master = {
        "schema": "interior-ai/room-spec@0.2", "units": "metric",
        "note": "2026-07-05 CLUSTER-DRIVEN by gen_floor2_specs.py: loose-furniture POSITIONS+SIZES "
                "are SNAPPED to the deterministic drawn clusters (plan_cluster), 0-4mm from the "
                "drawing, EXCEPT the bed (merges with over-bed casework -> measured, flagged). Both "
                "nightstands snap to their drawn 300x300 clusters (NE corner + SE wall niche). "
                "Built-ins = BF-label size on the wall. Absolute floor coords (offset 0,0). L-shaped "
                "suite: bedroom+dressing + ensuite (WC/double-vanity/tub/shower, owner point B) + "
                "walk-in closet. The placement gate independently checks COMPLETENESS (no drawn "
                "cluster silently dropped) and NO-FLOATING; per-piece IoU=1.00 confirms the coords "
                "are drawing-exact but NOT which piece a blob is — cluster IDENTITY stays a human "
                "REVIEW call.",
        "room": {"type": "bedroom_suite", "outline_mm": MASTER_OUTLINE,
                 "ceiling_mm": 2800, "wall_thk_mm": 100},
        "builtins": master_builtins, "items": master_items,
        "subrooms": [{"name": "โซนแต่งตัว (dressing)", "type": "dressing",
                      "outline_mm": MASTER_SUB[0], "ceiling_mm": 2800, "fixtures": master_fix},
                     {"name": "ห้องน้ำในตัว (ensuite)", "type": "bathroom",
                      "outline_mm": MASTER_SUB[1], "ceiling_mm": 2800, "fixtures": ensuite_fix},
                     {"name": "โซนตู้เสื้อผ้า (wardrobe bay)", "type": "wardrobe",
                      "outline_mm": MASTER_SUB[2], "ceiling_mm": 2800, "fixtures": wardrobe_fix}],
    }
    sitting = {
        "schema": "interior-ai/room-spec@0.2", "units": "metric",
        "note": "2026-07-05 CLUSTER-DRIVEN by gen_floor2_specs.py (loose furniture SNAPPED to drawn "
                "clusters 0-4mm; built-ins = BF labels). Absolute floor coords (offset 0,0). Sofa "
                "faces EAST; tub chairs face the terrace (south); round tables snapped to their "
                "circles. Gate checks COMPLETENESS + NO-FLOATING; snapped IoU=1.00 = drawing-exact "
                "coords, NOT cluster identity (the NW door-swing blob is a human dismiss, not a piece).",
        "room": {"type": "sitting_room", "outline_mm": SITTING_OUTLINE,
                 "ceiling_mm": 2800, "wall_thk_mm": 100},
        "builtins": sit_builtins, "items": sit_items,
    }
    json.dump(master, open(f"{LAYOUT_DIR}/scene-graph.master_bedroom.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(sitting, open(f"{LAYOUT_DIR}/scene-graph.sitting_room.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("wrote scene-graphs:",
          len(master_items) + len(master_builtins) + len(master_fix) + len(ensuite_fix) + len(wardrobe_fix),
          "master pieces (incl. ensuite+closet),", len(sit_items) + len(sit_builtins), "sitting pieces")

    # ---------------------------------------------------------------- match report
    print("\nCLUSTER MATCH REPORT (loose furniture — every coord came from the drawing, not typed):")
    for room, name, kind, cid, dist, bbox, mism in _REPORT:
        tag = f"cluster #{cid}" if cid is not None else "NO CLUSTER (flagged)"
        flag = "  <-- CURVE MISMATCH" if mism else ""
        print(f"  [{room[:7]:7}] {kind:12} <- {tag:22} d={dist:5.0f}mm  bbox={bbox}  {name[:26]}{flag}")
    for label, clusters, claimed in [("master", mc, m_claimed), ("sitting", sc, s_claimed)]:
        left = [c for i, c in enumerate(clusters) if i not in claimed
                and min(c["w"], c["d"]) >= 250 and c.get("area_m2", 0) >= 0.03]
        if left:
            print(f"  UNMATCHED drawn clusters in {label} (a human dismisses these — door/label/missing):")
            for c in left:
                print(f"      {c['w']}x{c['d']}mm at ({c['x']},{c['y']})  "
                      f"{'organic' if c['curve'] else 'rect'}  area {c['area_m2']}m2")

    # generation-time guard: a large snap distance or a curve/shape mismatch means an anchor grabbed
    # the WRONG drawn cluster — a swap the gate cannot see (it checks footprint-vs-any-cluster). The
    # 3D would then render e.g. an armchair where a table is drawn, certified PASS. Surface it loudly.
    anomalies = [(r, n, cid, d, mm) for (r, n, k, cid, d, bbox, mm) in _REPORT
                 if cid is not None and (d > 200 or mm)]
    if anomalies:
        print("\n[!] SNAP ANOMALIES — an anchor may have grabbed the WRONG cluster; CHECK before build:")
        for r, n, cid, d, mm in anomalies:
            print(f"      {r[:7]} '{n[:30]}' -> cluster #{cid}  dist={d:.0f}mm"
                  + ("  CURVE-MISMATCH" if mm else ""))
    else:
        print("  (all snaps <=200mm and curve-consistent — no anchor grabbed a wrong-shaped cluster)")

    # ---------------------------------------------------------------- self-verify overlay
    p = fitz.open(PDF)[PAGE]
    m = p.rotation_matrix

    def mm(P):
        Q = fitz.Point(P) * m
        return ((Q.x - OX) * SCALE, (OY - Q.y) * SCALE)

    def bez(pts, n=6):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
        return [((1-t)**3*x0+3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3*x3,
                 (1-t)**3*y0+3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3*y3) for t in (i/n for i in range(n+1))]

    strokes = []
    for d in p.get_drawings():
        if (d.get("width") or 0) >= 0.6:
            continue
        for it in d["items"]:
            if it[0] == "l":
                strokes.append([mm(it[1]), mm(it[2])])
            elif it[0] == "re":
                r = it[1]
                cs = [mm((r.x0, r.y0)), mm((r.x1, r.y0)), mm((r.x1, r.y1)), mm((r.x0, r.y1)), mm((r.x0, r.y0))]
                strokes += [[a, b] for a, b in zip(cs, cs[1:])]
            elif it[0] == "c":
                poly = [mm(z) for z in bez([(pt.x, pt.y) for pt in it[1:5]])]
                strokes += [[a, b] for a, b in zip(poly, poly[1:])]

    fig, ax = plt.subplots(figsize=(22, 14), dpi=130)
    ax.add_collection(LineCollection(strokes, colors="#aab8cc", linewidths=0.5))

    def draw_item(it, color):
        w, d, rot = it["w"], it["d"], it.get("rot", 0)
        cx, cy = it["x"] + w / 2, it["y"] + d / 2
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in corners]
        ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=color, lw=1.7))
        if it["kind"] in ("sofa", "armchair", "chair", "bed"):
            fx, fy = math.sin(a), -math.cos(a)
            L = 0.3 * min(w, d) + 150
            ax.add_patch(FancyArrow(cx, cy, fx * L, fy * L, width=25,
                         head_width=170, head_length=150, color="#e07000", length_includes_head=True))
        ax.text(cx, cy, it["name"].split()[0][:10], ha="center", va="center", fontsize=6, color=color)

    for it in master_items:
        draw_item(it, "#c02020")
    for it in master_builtins:
        draw_item(it, "#106010")
    for it in master_fix + ensuite_fix:
        draw_item(it, "#1080b0")
    for it in wardrobe_fix:
        draw_item(it, "#106010")
    for it in sit_items:
        draw_item(it, "#c02020")
    for it in sit_builtins:
        draw_item(it, "#106010")

    ax.set_xlim(-500, 10900)
    ax.set_ylim(-1100, 8700)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.25)
    ax.set_title("SELF-VERIFY: placed footprints (red=loose green=built-in blue=fixture, "
                 "orange=facing) over the plan. Every box must land on a drawn piece.", fontsize=10)
    plt.tight_layout()
    plt.savefig(OUT_OVERLAY, dpi=130)
    print("wrote", OUT_OVERLAY)


if __name__ == "__main__":
    main()
