"""
gen_floor2_v4_specs.py — Floor-2 blue-zone scene-graph generator, v4 (CLEAN REBUILD).

Division of labor is FIXED for this project (RESTART-PROMPT-floor2-v4.md):
  * The OWNER is ground-truth for every DIMENSION / wall / built-in size. Those live in the
    BF table below with an owner citation. NO dimension is read off the raster by eye here.
  * Claude transcribes the owner's sizes and places each built-in on the owner-named wall.
  * The machine (placement_gate.py) verifies only COMPLETENESS / NO-FLOATING / ON-INK.
  * The ONE thing read from the drawing is LOOSE-furniture geometry: position + size via
    deterministic clusters (plan_cluster), and for the angled tub chairs the true ANGLE +
    tight size via an oriented (min-area) box — because the owner's feedback was explicit:
    do NOT force chairs to cardinal facings, and do NOT oversize them.

FACING is owner-signable and DURABLE (placement-review.json `confirmed[]`, same dir): a signed
facing OVERRIDES the hand-read default via placement_gate.resolve_rot — the SAME confirmed_rot
matcher the gate uses to suppress/raise its facing flag, so generator and gate never disagree.
A signature is a CARDINAL letter ({"facing":"W"}) OR an explicit numeric {"rot": 12} — the latter
is what makes the NON-cardinal terrace tub chairs (rot 12/335) signable. The mechanism is BUILT +
WIRED + TESTED but ACTIVATES PER PIECE only once the owner signs it: today `confirmed[]` is EMPTY,
so every facing below is still just a hand-read LITERAL and a clean rebuild CAN re-roll it (the exact
v3->v4 regression) UNTIL the owner signs the piece into the ledger — signing is the owner's step, not
the machine's. Absent a signature the hand-read facing is used unchanged, so a regen against the
(currently empty) ledger is byte-identical to the pre-wiring generator.

v4 corrections vs v3 (kept as the known-flawed diff baseline):
  * BF label parse fixed: `BF09-1.520x60x280` = 5200x600x2800 (was mis-read 1520), BF09-2=1500
    (was 2150), BF09-3=3300, BF11=3200 (v3 had 1320/3200 muddle) — all owner-confirmed cm.
  * BF09-1 5200 does not fit a straight wall in the 2500x2800 bay -> modelled as the drawn L
    wrapping the bay's north (2500) + east (2700) walls (flagged for owner confirm).
  * Tub chairs are INDOOR floor-2 lounge chairs (owner 2026-07-06: "the chairs ARE floor 2; there
    is no terrace — outside the wall is grass BELOW"). They sit in the south lounge of the sitting
    room, by the south GLASS facade, and FACE OUT toward the garden VIEW below (the trees are ground
    level, y<0, OUTSIDE/below the glass — NOT a floor-2 terrace). The y~2050 wall is an interior
    partition/sliding door (not the exterior facade, which is a thin-line glass wall ~y0 the wall
    extractor drops). Placed at realistic size + true facing (drawn 12/335), not cardinal.
  * Outlines anchored to the vector wall grid (floor2-walls-mm.json).

    python gen_floor2_v4_specs.py <plan.pdf> <out_overlay.png> <v4_layout_dir>

Pure logic (to_spec / match / snap / angled / bf / room_zone; facing via placement_gate.resolve_rot)
is import-testable without a PDF (fitz/matplotlib/plan_cluster load inside main); only main() reads
the plan.
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# import the SAME deterministic clusterer + the gate's OWN facing matcher (single source of truth).
# plan_cluster + fitz + matplotlib load inside main(); placement_gate's top level is stdlib-only.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
for _p in (_HERE, os.path.join(_REPO, "pipeline", "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from placement_gate import resolve_rot, load_confirmed, reconcile_confirmed

SCALE, OX, OY = 26.45, 171.2, 596.5
CLOSE_MM = 18.0
PAGE = 1
FACE_ROT = {"S": 0, "E": 90, "N": 180, "W": 270}


def to_spec(name, kind, cx, cy, wx, hy, rot, h, swap_cardinal=True, **extra):
    """drawn bbox (centre cx,cy; extents wx=EW, hy=NS) + rot -> spec item, matching how
    build_floor.place_massing renders (fills w x d at the lower-left corner, pivots at the
    centre, rotates by rot). For a CARDINAL 90/270 the axis-aligned footprint swaps, so we
    pre-swap to keep the footprint == (wx,hy). For a NON-cardinal rot (angled chair) we do
    NOT swap: build_floor + the gate both compute the true rotated bbox from (w,d,rot).

    swap_cardinal MUST be False on the angled() path: there (wx,hy) are the piece's OWN oriented
    dims, not a drawn axis-aligned cluster AABB, so the pre-swap would CANCEL an owner sign that
    happens to resolve to exactly 90/270 (storing the rot=0 footprint while claiming rot 90) — the
    gate would then suppress its own flag because gate and renderer are self-consistently wrong."""
    if swap_cardinal and rot in (90, 270):
        w, d = hy, wx
    else:
        w, d = wx, hy
    it = {"name": name, "kind": kind, "x": round(cx - w / 2), "y": round(cy - d / 2),
          "w": round(w), "d": round(d), "h": h}
    if rot:
        it["rot"] = round(rot, 1)
    it.update(extra)
    return it


# ---------------------------------------------------------- cluster matching (loose furniture)
_REPORT = []
_CURVED_KINDS = {"armchair", "sofa", "loveseat", "chair"}
_RECT_KINDS = {"tv_console", "cabinet", "console", "desk", "wardrobe", "headboard", "media"}


def _wants_curve(kind, shape):
    if shape == "round" or kind in _CURVED_KINDS:
        return True
    if kind in _RECT_KINDS:
        return False
    return None


def _mism(cluster, want):
    return want is not None and bool(cluster.get("curve")) != want


def match(anchor, kind, shape, clusters, claimed, max_dist=1100, mismatch_penalty=350):
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
    """Emit a CARDINAL loose piece AT the exact drawn-cluster bbox for its anchor+kind. An owner
    signed facing (placement-review.json confirmed[], resolved via placement_gate.resolve_rot)
    OVERRIDES the hand-typed `face`; absent one the hand-typed cardinal is used unchanged (byte-
    identical to the pre-wiring generator). Facing is resolved AFTER the match so the size guard
    sees the real footprint. snap is for CARDINAL pieces (an angled facing belongs on angled())."""
    cl, dist, mismatch = match(anchor, kind, extra.get("shape"), clusters, claimed)
    if cl is None:
        rot, fsrc = resolve_rot(name, FACE_ROT[face], 500, 500, confirmed)
        it = to_spec(name, kind, anchor[0], anchor[1], 500, 500, rot, h,
                     note="NO drawn cluster within reach — hard-FAILs the gate (honest miss)", **extra)
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


def angled(room, name, kind, cx, cy, w, d, rot, h, confirmed=None, **extra):
    """Place an ANGLED loose piece (tub chair) at an explicit centre + tight size + true angle
    read from the drawing's oriented (min-area) box. NOT snapped to a cluster AABB (an angled
    piece's AABB overstates its size). The gate checks it ON-INK against the drawn cluster.

    This is the NON-cardinal path: an owner-signed rot (placement-review.json confirmed[] with a
    numeric {"rot": ...} OR a cardinal {"facing": ...}, resolved via placement_gate.resolve_rot)
    OVERRIDES the hand-read angle, so a rebuild re-applies the owner-adjudicated chair-facing
    instead of re-rolling it. Absent a signature the drawn angle is used unchanged (byte-identical)."""
    eff_rot, fsrc = resolve_rot(name, rot, w, d, confirmed)
    # swap_cardinal=False: (w,d) are the piece's oriented dims — an owner sign landing on exactly
    # 90/270 must ROTATE the box, never trip to_spec's cluster-AABB pre-swap (which would cancel it).
    it = to_spec(name, kind, cx, cy, w, d, eff_rot, h, swap_cardinal=False, angled=True, **extra)
    if fsrc:
        it["facing_source"] = fsrc
    _REPORT.append((room, name, kind, "angled", 0, (it["x"], it["y"], it["w"], it["d"]), False))
    return it


# ---------------------------------------------------------- built-ins (OWNER-authoritative BF table, mm)
BF = {"BF09-1": (5200, 600, 2800), "BF09-2": (1500, 600, 2800), "BF09-3": (3300, 600, 2800),
      "BF10": (2500, 600, 2800), "BF11": (3200, 600, 2800), "BF12-1": (1575, 400, 2800),
      "BF12-2": (700, 400, 2800), "BF13": (4100, 300, 500), "BF14": (3250, 100, 2800)}


def bf(name, code, kind, cx, cy, run, h=None, **extra):
    """Built-in at a wall centre (cx,cy), size from the owner BF label. run='NS' -> length N-S
    (wall on E/W); run='EW' -> length E-W. Not snapped: label-authoritative wall casework the
    gate checks leniently."""
    W, D, H = BF[code]
    wx, hy = (D, W) if run == "NS" else (W, D)
    return to_spec(name, kind, cx, cy, wx, hy, 0, h or H, bf=code, **extra)


def room_zone(outline, subrooms, pad=150.0):
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    for sr in subrooms:
        for p in sr:
            xs.append(p[0]); ys.append(p[1])
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ============================================================ ROOM OUTLINES (wall-snapped, v4)
# L-shaped master: west x0, south niche y-450, sleeping east x5500, north-wing east x5650,
# north wall y8650. Ensuite (walled) x0-3150 y5850-8650; wardrobe bay (open) x3150-5650 same y.
MASTER_OUTLINE = [[0, -450], [5500, -450], [5500, 2650], [5650, 2650], [5650, 8650], [0, 8650]]
ENSUITE_OUT = [[0, 5850], [3150, 5850], [3150, 8650], [0, 8650]]
WARDROBE_OUT = [[3150, 5850], [5650, 5850], [5650, 8650], [3150, 8650]]
MASTER_SUB = [ENSUITE_OUT, WARDROBE_OUT]
SITTING_OUTLINE = [[5750, 0], [10650, 0], [10650, 6250], [5750, 6250]]

_NOTE = ("v4 CLEAN REBUILD (gen_floor2_v4_specs.py). Dimensions/built-in sizes = OWNER-authoritative "
         "(BF label = cm, owner-confirmed 2026-07-05); loose-furniture position/size = deterministic "
         "clusters (plan_cluster); tub-chair ANGLE + tight size = oriented min-area box (not cardinal). "
         "Gate verifies COMPLETENESS + NO-FLOATING + ON-INK only; identity/facing/built-in size are "
         "human calls. Absolute floor coords, offset (0,0).")


def assert_signatures_applied(pieces, confirmed, where=""):
    """Guard against a SILENTLY DETACHED signature. `pieces` MUST be exactly the loose pieces the
    generator applies signs to via resolve_rot (never built-ins/fixtures — those never consult the
    ledger, so counting a sign that merely name-matches one as 'applied' is a false pass). Every
    owner-signed facing in confirmed[] must match one of those pieces by the gate's OWN name+size
    join (reconcile_confirmed). A detached join means resolve_rot silently fell back to the hand-read
    facing — the exact re-roll the ledger exists to prevent, hidden behind a reassuring COUNT. So we
    reconcile AFTER placement and hard-FAIL on any orphan: the owner is told a sign no longer binds
    instead of shipping a facing that reverted. Import-testable (no PDF). Returns the matched entries."""
    matched, orphaned = reconcile_confirmed(pieces, confirmed)
    if orphaned:
        lines = "\n".join(
            f"    - {e.get('name')!r}  (w={e.get('w')} d={e.get('d')} "
            f"sign={e.get('rot', e.get('facing'))})" for e in orphaned)
        raise SystemExit(
            f"PLACEMENT-REVIEW ORPHAN{f' [{where}]' if where else ''}: {len(orphaned)} owner-signed "
            f"facing(s) bind to NO loose piece the generator places — the name+size join is detached "
            f"(a rename or resize, a piece not found in the drawing, or a sign aimed at a built-in/"
            f"fixture the generator does not apply facings to). The facing would re-roll to the "
            f"hand-read default. Fix the ledger name/size/room (or the generator), then regenerate:\n{lines}")
    return matched


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

    # Owner-signed facings (placement-review.json in this v4 dir). A signature is applied OVER the
    # hand-read default so a regeneration cannot silently re-roll an adjudicated facing. Read
    # defensively — a missing/malformed ledger -> no signatures (byte-identical regen), never a crash.
    led_path = os.path.join(LAYOUT_DIR, "placement-review.json")
    confirmed_all = []
    if os.path.exists(led_path):
        try:
            confirmed_all = load_confirmed(json.load(open(led_path, encoding="utf-8")))
        except (ValueError, OSError, TypeError):
            confirmed_all = []
    confirmed_master = [e for e in confirmed_all if e.get("room") in ("master_bedroom", "*")]
    confirmed_sitting = [e for e in confirmed_all if e.get("room") in ("sitting_room", "*")]
    print(f"placement-review.json: {len(confirmed_all)} owner-signed facing(s) loaded "
          f"({len(confirmed_master)} master, {len(confirmed_sitting)} sitting) — reconciled AFTER placement")

    master_zone = room_zone(MASTER_OUTLINE, MASTER_SUB)
    sitting_zone = room_zone(SITTING_OUTLINE, [])
    mc = extract_clusters(PDF, PAGE, master_zone, CLOSE_MM, calib=(SCALE, OX, OY))["items"]
    sc = extract_clusters(PDF, PAGE, sitting_zone, CLOSE_MM, calib=(SCALE, OX, OY))["items"]
    m_claimed, s_claimed = set(), set()

    # ---------------------------------------------------------------- MASTER pieces
    master_items, master_builtins = [], []

    # BED — MEASURED (merges with BF14/BF09-3 casework -> no clean cluster; gate = ON_INK). 7'x6.5':
    # head-foot (E-W) = 6.5' = 1981, width (N-S) = 7' = 2134. Head EAST flush to BF14 (east face 5150),
    # foot faces the west TV. Anchored to the east wall, NOT eyeballed. Facing hand-read W (rot 270);
    # an owner-signed facing overrides it (the bed is placed by direct to_spec, not snap/angled).
    _bed_rot, _bed_src = resolve_rot("เตียง 7'x6.5' หัวตะวันออก", 270, 1981, 2134, confirmed_master)
    _bed = to_spec("เตียง 7'x6.5' หัวตะวันออก", "bed", 4159, 1100, 1981, 2134, _bed_rot, 600,
                   note="head EAST vs BF14 slat; measured (merges with casework)")
    if _bed_src:
        _bed["facing_source"] = _bed_src
    master_items.append(_bed)
    # FOOT BENCH (organic id37) at the west foot.
    master_items.append(snap("master_bedroom", "ม้านั่งปลายเตียง (bench)", "bench", mc, m_claimed,
                             (2898, 1129), "S", 450, confirmed=confirmed_master, note="foot of bed; confirm identity"))
    # TWO lamp NIGHTSTANDS flank the head (NE + SE), owner-confirmed identical bedside tables.
    master_items.append(snap("master_bedroom", "โต๊ะข้างเตียง เหนือ (มีโคมไฟ)", "side_table", mc, m_claimed,
                             (4947, 2458), "S", 520, confirmed=confirmed_master, note="NE of the bed head"))
    master_items.append(snap("master_bedroom", "โต๊ะข้างเตียง ใต้ (มีโคมไฟ)", "side_table", mc, m_claimed,
                             (4947, -194), "N", 520, confirmed=confirmed_master, note="SE of the bed head"))
    # DESK CHAIR pulled up to BF11, faces W (near-cardinal per the oriented box 89deg).
    master_items.append(snap("master_bedroom", "เก้าอี้ทำงาน (หันเข้าโต๊ะ W)", "armchair", mc, m_claimed,
                             (1125, 4252), "W", 750, confirmed=confirmed_master, note="pulled up to BF11 work desk; faces W"))
    # WEST-WALL unit the bed foot faces (id34 600x2052). Identity = owner-confirm (TV console?).
    master_items.append(snap("master_bedroom", "ตู้ทีวีสูง ผนังตะวันตก", "tv_console", mc, m_claimed,
                             (606, 1150), "S", 1800, confirmed=confirmed_master, note="west-wall TALL TV cabinet the bed foot faces; owner-confirmed identity + TALL (2026-07-06); footprint 2046x600 from cluster, height owner-set"))

    # BUILT-INS (owner BF sizes; positioned on the owner-named wall / drawn footprint)
    # BF14 headboard slat: east wall, N-S, 3250 long x100 deep, bed head against its west face.
    master_builtins.append(to_spec("ผนังระแนงหัวเตียง BF14 (325x10x280)", "headboard",
                                   5200, 1350, 100, 3250, 0, 2800, bf="BF14"))
    # BF09-3 over-bed wardrobe: divider N of bed, E-W, 3300x600.
    master_builtins.append(to_spec("ตู้เสื้อผ้าเหนือเตียง BF09-3 (330x60x280)", "wardrobe",
                                   3950, 2950, 3300, 600, 0, 2800, bf="BF09-3"))
    # BF11 built-in work desk: master WEST wall, N-S, 3200x600, h750. 'cabinet' (lenient) not 'desk'.
    master_builtins.append(bf("โต๊ะทำงาน built-in BF11 (320x60x280)", "BF11", "cabinet",
                              300, 4250, "NS", h=750))
    # BF10 is a DRESSING cabinet (owner correction 2026-07-05: NOT the ensuite vanity). It sits in
    # the dressing BETWEEN BF11 and BF09-2, against the ensuite south wall (drawn front edge y5250),
    # E-W run 2500x600, facing south into the dressing. East end abuts BF09-2 (x3150).
    master_builtins.append(bf("ตู้/ชั้น BF10 (250x60x280)", "BF10", "cabinet", 1900, 5550, "EW",
                              note="dressing cabinet BETWEEN BF11 and BF09-2, against the ensuite south wall (NOT the vanity)"))

    # ---- ENSUITE (walled subroom): the double vanity here is SANITARYWARE (not BF10), + WC/tub/shower
    ensuite_fix = [
        to_spec("อ่างล้างหน้าคู่ (ในห้องน้ำ)", "vanity_double", 1850, 6350, 2500, 550, 0, 850,
                note="ensuite double vanity (sanitaryware, NOT BF10); two basins on the south counter, run '3.05'"),
        to_spec("โถสุขภัณฑ์ WC", "toilet", 450, 6350, 400, 700, 0, 400, note="SW, against the west wall"),
        to_spec("อ่างอาบน้ำ (bathtub)", "bathtub", 2200, 8000, 1800, 900, 0, 550, note="NE, north wall"),
        to_spec("ฝักบัว (shower)", "shower", 625, 7925, 1050, 1150, 0, 2200, note="NW glass enclosure"),
    ]
    # ---- WARDROBE BAY (open, part of dressing): BF09-1 L (5.2m) + BF09-2 (1.5m)
    wardrobe_fix = [
        # BF09-1 = 5200 total. Bay is 2500(x3150-5650) x 2800(y5850-8650): a 5200 run must wrap.
        # Modelled as the drawn L: north leg 2500 along y8650 + east leg 2700 along x5650. CONFIRM.
        to_spec("ตู้เสื้อผ้า BF09-1 ขาเหนือ (L 5.2m)", "wardrobe", 4400, 8350, 2500, 600, 0, 2800,
                bf="BF09-1", note="north leg 2.5m along the bay north wall (of the 5.2m L)"),
        to_spec("ตู้เสื้อผ้า BF09-1 ขาตะวันออก (L 5.2m)", "wardrobe", 5350, 7000, 600, 2100, 0, 2800,
                bf="BF09-1", note="east leg ~2.7m along the bay east wall x5650 (of the 5.2m L)"),
        # BF09-2 = 1500, flush to the ensuite east wall (x3150). The door GAP is y6698-7596 (from the
        # wall data); the solid wall below it is only ~850mm, too short for a 1500 run, so BF09-2 spans
        # the ensuite-south-wall line: N end just below the door (y6680), S end DOWN to MEET BF10 (~y5250)
        # (owner 2026-07-05: "BF09-2 and BF10 must meet exactly — move it north until they join").
        to_spec("ตู้เสื้อผ้า BF09-2 (150x60x280)", "wardrobe", 3450, 5930, 600, 1500, 0, 2800,
                bf="BF09-2", note="flush to ensuite east wall; S end MEETS BF10 (~y5250), N end just below the door gap (y6698)"),
    ]

    # ---------------------------------------------------------------- SITTING pieces
    sit_items, sit_builtins = [], []
    # SOFA faces EAST toward the BF13 media/TV wall (round accent table between).
    sit_items.append(snap("sitting_room", "โซฟา 3 ที่นั่ง", "sofa", sc, s_claimed,
                          (8161, 4651), "E", 800, confirmed=confirmed_sitting, note="faces EAST toward BF13/TV"))
    # TWO TUB CHAIRS — INDOOR floor-2 lounge by the south GLASS facade (owner 2026-07-06: "the chairs
    # ARE floor 2; no terrace — outside the wall is grass BELOW"). They face OUT toward the garden VIEW
    # below (trees are ground level y<0, outside the glass). Angled at realistic 680x640 (NOT the ~774
    # AABB, NOT cardinal). Drawn-read angles rot 12 (left) / rot 335 (right). OWNER REFINED the aim
    # 2026-07-06: converge JUST RIGHT OF THE LEFT garden tree below (~6550,-600, was ~6670,-650) ->
    # signed in placement-review.json confirmed[] as rot 8 / 332, which resolve_rot APPLIES over these
    # drawn-read literals (the ledger's first real signatures; regen without them = drawn 12/335).
    sit_items.append(angled("sitting_room", "เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)", "armchair",
                            6331, 949, 680, 640, 12, 750, confirmed=confirmed_sitting,
                            note="indoor floor-2 lounge by the south glass; faces the garden VIEW below"))
    sit_items.append(angled("sitting_room", "เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)", "armchair",
                            7630, 1405, 660, 640, 335, 750, confirmed=confirmed_sitting,
                            note="indoor floor-2 lounge by the south glass; faces the garden VIEW below"))
    # ROUND TABLES (snap to their drawn circles; render round).
    sit_items.append(snap("sitting_room", "โต๊ะกลม (ระหว่างเก้าอี้)", "side_table", sc, s_claimed,
                          (6916, 1414), "S", 450, confirmed=confirmed_sitting, shape="round"))
    sit_items.append(snap("sitting_room", "โต๊ะกลม (ข้างโซฟา)", "side_table", sc, s_claimed,
                          (9466, 4660), "S", 450, confirmed=confirmed_sitting, shape="round"))
    # (NW door swing = a DOOR, dismissed in placement-review.json — not a piece.)
    # BUILT-INS
    sit_builtins.append(bf("ตู้โชว์ BF12-1 (157.5x40x280)", "BF12-1", "cabinet", 5950, 5462, "NS",
                           note="party/west wall, NW, behind sofa, next to door"))
    # BF12-2 = a TALL cabinet (70x40x280) and the ORCHID TABLE are SEPARATE pieces (owner 2026-07-06):
    # the drawn ~1000x400 table (cluster id2, with the orchid squiggle) is loose furniture; BF12-2 is a
    # distinct 700x400 tall cabinet against the y2600 wall behind it. (Was wrongly merged as one console.)
    sit_builtins.append(bf("ตู้สูง BF12-2 (70x40x280)", "BF12-2", "cabinet", 5950, 3000, "NS",
                           note="tall cabinet on the WEST party wall (x5750), INNER sitting side, just NORTH of the outer orchid table — owner-pointed spot 2026-07-06 (highlighted); 400 deep x 700 N-S"))
    # ORCHID TABLE (loose, drawn 1002x402 = cluster id2) — a separate low console the owner flagged.
    # Wired through resolve_rot like every other loose piece (cardinal: drawn AABB, default swap) so an
    # owner-signed facing is APPLIED here too — else the gate could raise a sign the generator can't satisfy.
    _orchid_name = "โต๊ะวางกล้วยไม้ (console)"
    _orchid_rot, _orchid_src = resolve_rot(_orchid_name, FACE_ROT["S"], 1002, 402, confirmed_sitting)
    _orchid = to_spec(_orchid_name, "console", 6399, 2373, 1002, 402, _orchid_rot, 450,
                      note="orchid console table (drawn ~1002x402) — SEPARATE piece from BF12-2 (owner 2026-07-06)")
    if _orchid_src:
        _orchid["facing_source"] = _orchid_src
    sit_items.append(_orchid)
    sit_builtins.append(bf("ชั้นวางทีวี ผนังตะวันออก BF13 (410x30x50)", "BF13", "cabinet", 10500, 4100, "NS",
                           h=500, note="east wall; the sofa faces it"))

    # ---------------------------------------------------------------- orphan-signature gate
    # Reconcile the owner-signed ledger against the loose pieces the generator ACTUALLY applies signs
    # to (resolve_rot runs on master_items / sit_items ONLY — built-ins/fixtures never consult the
    # ledger, so they are NOT in the pool: a sign that merely name-matches one must ORPHAN, not read as
    # applied). A detached signature (renamed/resized piece, a sign aimed at a built-in) that would
    # silently re-roll its facing hard-FAILs here — the precondition that makes every signature
    # trustworthy. Each sign is checked against EXACTLY the pool it can apply to: a room-scoped sign vs
    # its room, a '*' sign vs both (so it isn't false-orphaned in the room it doesn't live in), and a
    # sign whose room this generator never produces vs nothing (a typo'd room can't be silently skipped
    # by both filters). No signature escapes the check.
    _known = {"master_bedroom", "sitting_room", "*"}
    assert_signatures_applied(master_items,
                              [e for e in confirmed_all if e.get("room") == "master_bedroom"],
                              where="master_bedroom")
    assert_signatures_applied(sit_items,
                              [e for e in confirmed_all if e.get("room") == "sitting_room"],
                              where="sitting_room")
    assert_signatures_applied(master_items + sit_items,
                              [e for e in confirmed_all if e.get("room") == "*"],
                              where="* (any room)")
    assert_signatures_applied([], [e for e in confirmed_all if e.get("room") not in _known],
                              where="unknown room (this generator produces only master_bedroom + sitting_room)")
    # Report the TRUE applied count from facing_source (what resolve_rot actually set), not the join
    # count — a sign can bind by name+size yet set no facing (a malformed/non-cardinal facing/rot
    # value); that is not an orphan (the piece exists) but it is NOT applied, and saying so is honest.
    applied = sum(1 for it in master_items + sit_items if it.get("facing_source") == "owner-signed")
    inert = len(confirmed_all) - applied     # reached here => 0 orphaned, so the remainder are inert signs
    print(f"placement-review.json: {len(confirmed_all)} loaded, {applied} APPLIED (facing set), 0 orphaned"
          + (f"; NOTE {inert} bound a piece but set NO facing — check its facing/rot value" if inert else ""))

    # ---------------------------------------------------------------- write scene-graphs
    master = {
        "schema": "interior-ai/room-spec@0.2", "units": "metric", "version": "v4", "note": _NOTE,
        "room": {"type": "bedroom_suite", "outline_mm": MASTER_OUTLINE, "ceiling_mm": 2800, "wall_thk_mm": 100},
        "builtins": master_builtins, "items": master_items,
        "subrooms": [{"name": "ห้องน้ำในตัว (ensuite)", "type": "bathroom", "outline_mm": ENSUITE_OUT,
                      "ceiling_mm": 2800, "fixtures": ensuite_fix},
                     {"name": "โซนตู้เสื้อผ้า (wardrobe bay)", "type": "wardrobe", "outline_mm": WARDROBE_OUT,
                      "ceiling_mm": 2800, "fixtures": wardrobe_fix}],
    }
    sitting = {
        "schema": "interior-ai/room-spec@0.2", "units": "metric", "version": "v4", "note": _NOTE,
        "room": {"type": "sitting_room", "outline_mm": SITTING_OUTLINE, "ceiling_mm": 2800, "wall_thk_mm": 100},
        "builtins": sit_builtins, "items": sit_items,
    }
    json.dump(master, open(f"{LAYOUT_DIR}/scene-graph.master_bedroom.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(sitting, open(f"{LAYOUT_DIR}/scene-graph.sitting_room.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("wrote v4 scene-graphs:",
          len(master_items) + len(master_builtins) + len(ensuite_fix) + len(wardrobe_fix),
          "master pieces,", len(sit_items) + len(sit_builtins), "sitting pieces")

    # ---------------------------------------------------------------- REQUIRED read-vs-sheet overlay
    # The pre-owner surfacing step (2026-07-06 diagnosis): every rebuild MUST emit the machine's
    # read painted over the TRUE sheet (numbered pieces + provenance-coloured facing arrows +
    # the checklist the numbers key into), so the owner SCANS a picture instead of HUNTING each
    # misread. No try/except: if the overlay cannot be produced, the generate fails loudly — a
    # rebuild without its overlay is a rebuild the owner cannot review.
    from raster_overlay import render_read_overlay
    overlay_rooms = [{"id": "master_bedroom", "spec": master, "offset": (0, 0)},
                     {"id": "sitting_room", "spec": sitting, "offset": (0, 0)}]
    for w in render_read_overlay(PDF, PAGE, (SCALE, OX, OY), overlay_rooms,
                                 os.path.join(LAYOUT_DIR, "review-read-vs-sheet")):
        print("wrote", w)

    # ---------------------------------------------------------------- match report
    print("\nLOOSE-FURNITURE READ (positions/angles from the drawing, not typed):")
    for room, name, kind, cid, dist, bbox, mism in _REPORT:
        tag = ("angled box" if cid == "angled" else
               (f"cluster #{cid}" if cid is not None else "NO CLUSTER"))
        flag = "  <-- CURVE MISMATCH" if mism else ""
        print(f"  [{room[:7]:7}] {kind:11} <- {tag:14} d={dist:5.0f}mm  bbox={bbox}  {name[:24]}{flag}")
    for label, clusters, claimed in [("master", mc, m_claimed), ("sitting", sc, s_claimed)]:
        left = [c for i, c in enumerate(clusters) if i not in claimed
                and min(c["w"], c["d"]) >= 250 and c.get("area_m2", 0) >= 0.03]
        if left:
            print(f"  UNCLAIMED drawn clusters in {label} (gate will list for human dismiss/add):")
            for c in left:
                print(f"      id{c['id']} {c['w']}x{c['d']}mm at ({c['x']},{c['y']})  "
                      f"{'organic' if c['curve'] else 'rect'}  {c['area_m2']}m2")

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

    fig, ax = plt.subplots(figsize=(22, 16), dpi=130)
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
            ax.add_patch(FancyArrow(cx, cy, fx * L, fy * L, width=25, head_width=170, head_length=150,
                         color="#e07000", length_includes_head=True))
        ax.text(cx, cy, it["name"].split()[0][:10], ha="center", va="center", fontsize=6, color=color)

    for it in master_items:
        draw_item(it, "#c02020")
    for it in master_builtins + wardrobe_fix:
        draw_item(it, "#106010")
    for it in ensuite_fix:
        draw_item(it, "#1080b0")
    for it in sit_items:
        draw_item(it, "#c02020")
    for it in sit_builtins:
        draw_item(it, "#106010")

    ax.set_xlim(-800, 11000)
    ax.set_ylim(-1200, 9000)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.25)
    ax.set_title("v4 SELF-VERIFY: placed footprints (red=loose green=built-in blue=fixture, "
                 "orange=facing) over the plan strokes. Every box must land on a drawn piece.", fontsize=10)
    plt.tight_layout()
    plt.savefig(OUT_OVERLAY, dpi=130)
    print("wrote", OUT_OVERLAY)


if __name__ == "__main__":
    main()
