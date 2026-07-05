"""
placement_gate.py — the REAL 2D->3D reading gate.

For years the "self-verify overlay" was a picture a human eyeballed: nothing in code
checked that a placed piece of furniture actually lands on something drawn in the plan,
and nothing FAILED when it didn't. So the OWNER was the first (and only) verifier, which
is exactly why the 3D kept coming out wrong. This module makes the machine the first
verifier.

It re-derives the DETERMINISTIC furniture clusters straight from the plan
(plan_cluster.extract_clusters) and checks every placed LOOSE item against them:

  * MATCHED   — placed footprint aligns with a drawn cluster (IoU >= IOU_OK).           OK
  * DRIFT     — overlaps a drawn piece but size/position is off (IOU_DRIFT..IOU_OK).    REVIEW
  * ON_INK    — sits on drawn ink but not a clean cluster (e.g. a bed merged with a     REVIEW
                built-in) — plausible but the machine can't certify the exact bbox.
  * FLOATING  — placed where the plan has essentially NO furniture ink under it.        FAIL  <-- blocks
  * UNPLACED  — a drawn cluster no placed piece covers: MISSING furniture, or a         REVIEW
                dimension-label the clusterer mistook for a piece. A human must say which.

Verdict / exit code:
  FAIL   (exit 1) if any loose piece is FLOATING — an unambiguous "you built furniture the
                  plan does not have there". Nothing renders on a FAIL.
  REVIEW (exit 0, but prints a HUMAN-CONFIRM checklist) for drift / on-ink / unplaced /
                  unverified built-ins — the honest "we read this much; sign off on the rest".
  PASS   (exit 0) when every loose piece matches a drawn cluster and nothing is left unplaced.

The FAIL is deliberately narrow so the gate does not cry wolf; the REVIEW list is where the
irreducibly-human calls (identity of a cluster, wet-fixture symbols, exact facing) live —
made EXPLICIT and signed, instead of silently guessed or eyeballed.

    python placement_gate.py <plan.pdf> <manifest.json | scene-graph.json> [page] [close_mm]

Pure logic (footprint / iou / classify / gate) is import-testable without a PDF; only run()
touches fitz. Calibration triple mirrors plan_cluster / gen_floor2_specs (one source sheet).
"""
import hashlib
import json
import math
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- thresholds (tunable; documented so a reviewer can argue each) -------------------
IOU_OK = 0.45        # placed box vs drawn cluster: a clean match
IOU_DRIFT = 0.15     # below this = no real overlap with any cluster
INK_FLOAT_PX = 12    # furniture-ink pixels under a footprint below this = FLOATING (empty floor)
UNPLACED_MIN_EXT_MM = 250    # a leftover cluster smaller than this in either axis = ignore (tick/noise)
UNPLACED_MIN_AREA_M2 = 0.03  # ...or smaller area than this = ignore (a small stool IS real -> keep low)

# Free-standing furniture MUST land on a drawn piece (STRICT): a floating one is a hard FAIL.
# Strictness is decided by KIND, not by which JSON array a piece sits in — a bed dropped into
# builtins[] must still FAIL if it floats. Mirrors build_floor._FURN_KINDS (+ bench/stool/ottoman).
# Everything NOT in this set (wall casework, wet fixtures, headboards) is LENIENT: it may be drawn
# on the excluded thick-line wall layer, so 'no furniture-ink there' is UNVERIFIED (REVIEW), not a
# floor-on-empty FAIL.
FURN_KINDS = {"sofa", "loveseat", "coffee_table", "dining_table", "desk", "side_table",
              "nightstand", "chair", "dining_chair", "armchair", "bed", "bench", "stool",
              "table", "ottoman"}


def _is_strict(kind):
    return kind in FURN_KINDS


# ---- pure geometry (no PDF) ----------------------------------------------------------
def footprint(it, offset=(0, 0)):
    """AXIS-ALIGNED plan-mm bbox of a placed spec item AS build_floor ACTUALLY RENDERS IT.

    build_floor.place_massing builds the piece filling w x d with centre pivot =
    (x + w/2, y + d/2), then rotates it by `rot` degrees about that pivot. So the centre
    matches x + w/2 exactly, and the axis-aligned half-extents of a w x d rectangle rotated
    by theta are (w/2)|cos| + (d/2)|sin| and (w/2)|sin| + (d/2)|cos|. This reduces to the
    plain (w,d)/(d,w) swap at 0/90/180/270 but stays CORRECT for the 'หันเฉียง' diagonal
    chairs too (a 45-deg piece has a larger bbox than either swap). Getting this wrong
    silently offsets every check, so it is derived from the renderer's own math on purpose.
    """
    w, d, rot = it["w"], it["d"], it.get("rot", 0)
    cx = it["x"] + offset[0] + w / 2.0
    cy = it["y"] + offset[1] + d / 2.0
    th = math.radians(rot)
    c, s = abs(math.cos(th)), abs(math.sin(th))
    ew = w * c + d * s
    ns = w * s + d * c
    return (cx - ew / 2.0, cy - ns / 2.0, cx + ew / 2.0, cy + ns / 2.0)


def cluster_bbox(c):
    return (c["x"], c["y"], c["x"] + c["w"], c["y"] + c["d"])


def iou(a, b):
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = ix1 - ix0, iy1 - iy0
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _best_cluster(fp, clusters):
    best_i, best_iou = None, 0.0
    for i, c in enumerate(clusters):
        v = iou(fp, cluster_bbox(c))
        if v > best_iou:
            best_i, best_iou = i, v
    return best_i, best_iou


def _centre(fp):
    return ((fp[0] + fp[2]) / 2.0, (fp[1] + fp[3]) / 2.0)


def _in_zone(pt, zone):
    return zone[0] <= pt[0] <= zone[2] and zone[1] <= pt[1] <= zone[3]


def classify_item(it, clusters, ink_count, zone, offset=(0, 0), strict=True):
    """Classify one placed item against the drawn clusters + furniture ink:
      matched  IoU >= IOU_OK
      drift    IOU_DRIFT <= IoU < IOU_OK
      else (no real cluster overlap):
        - centroid OUTSIDE the rasterised zone -> 'unverified'. The ink raster only covers the
          room zone, so a piece placed largely outside it has no ink to see; a FAIL must never
          fire there (false-block guard for furniture that laps past the outline).
        - ink under footprint >= INK_FLOAT_PX -> 'on_ink': sits on SOME drawing but not its own
          clean cluster (a displaced piece dumped onto other furniture lands here) -> REVIEW,
          which now BLOCKS the build until a human signs off.
        - else 'floating' if strict (free-standing furniture on empty floor = hard FAIL),
          else 'unverified' (wall/wet casework may be on the excluded thick-line layer).
    """
    fp = footprint(it, offset)
    bi, biou = _best_cluster(fp, clusters)
    if biou >= IOU_OK:
        status = "matched"
    elif biou >= IOU_DRIFT:
        status = "drift"
    elif not _in_zone(_centre(fp), zone):
        status = "unverified"
    elif ink_count(fp) >= INK_FLOAT_PX:
        status = "on_ink"
    else:
        status = "floating" if strict else "unverified"
    return {"name": it.get("name", it.get("kind", "?")), "kind": it.get("kind", "?"),
            "status": status, "iou": round(biou, 3), "cluster": bi, "fp": fp}


def unplaced_clusters(clusters, all_fps):
    """Clusters no placed footprint covers (best IoU to ANY placed piece < IOU_DRIFT) and
    big enough to be furniture rather than a dim-tick. These are MISSING pieces or
    label-text phantoms — a human decides which."""
    out = []
    for i, c in enumerate(clusters):
        cb = cluster_bbox(c)
        best = max((iou(fp, cb) for fp in all_fps), default=0.0)
        if best >= IOU_DRIFT:
            continue
        if min(c["w"], c["d"]) < UNPLACED_MIN_EXT_MM or c.get("area_m2", 0) < UNPLACED_MIN_AREA_M2:
            continue
        out.append({"id": c.get("id"), "x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"],
                    "area_m2": c.get("area_m2"), "curve": c.get("curve"),
                    "best_iou": round(best, 3)})
    return out


def gate(loose, fixed, clusters, ink_count, zone, offset=(0, 0)):
    """Check one room. loose = spec items[]; fixed = built-ins + subroom fixtures (kept
    separate only for the report). STRICTNESS is decided per piece by KIND (see _is_strict),
    so free-standing furniture is checked strictly wherever it is listed. FAIL if ANY piece
    (loose or fixed) whose kind is free-standing floats on empty floor."""
    loose_r = [classify_item(it, clusters, ink_count, zone, offset, _is_strict(it.get("kind"))) for it in loose]
    fixed_r = [classify_item(it, clusters, ink_count, zone, offset, _is_strict(it.get("kind"))) for it in fixed]
    every = loose_r + fixed_r
    unplaced = unplaced_clusters(clusters, [r["fp"] for r in every])

    floating = [r for r in every if r["status"] == "floating"]
    review = [r for r in every if r["status"] in ("drift", "on_ink", "unverified")]
    if floating:
        verdict = "FAIL"
    elif review or unplaced:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "loose": loose_r, "fixed": fixed_r,
            "unplaced": unplaced, "n_clusters": len(clusters)}


# ---- PDF-backed orchestration --------------------------------------------------------
def _ink_counter(res):
    """Closure: furniture-ink pixel count inside a plan-mm footprint, on the cluster raster."""
    ink = res["ink"]
    X0, Y0, X1, Y1 = res["zone"]
    RES = res["res"]
    W, H = res["W"], res["H"]

    def count(fp):
        x0, y0, x1, y1 = fp
        c0 = max(0, int((x0 - X0) / RES)); c1 = min(W, int((x1 - X0) / RES))
        r0 = max(0, int((Y1 - y1) / RES)); r1 = min(H, int((Y1 - y0) / RES))
        if c1 <= c0 or r1 <= r0:
            return 0
        return int(ink[r0:r1, c0:c1].sum())

    return count


def _room_zone(spec, offset, pad=150.0):
    """Cluster zone = the ROOM outline bbox (∪ subroom outlines), padded ~150mm.

    Deliberately NOT expanded to stray footprints: connected-component clustering is
    zone-sensitive — pulling a neighbouring room's ink into the frame can bridge/merge
    or drop a piece's cluster (the dressing chair vanished into a >3600mm blob when the
    zone reached into the adjacent room), and even a modest pad drags wall hatching just
    outside the outline in as spurious 'unplaced' noise. The pad is kept SMALL for a clean
    frame; the false-FAIL of furniture that laps past the outline is prevented instead by
    classify_item's centroid-in-zone guard (a piece whose centroid lands beyond the zone is
    UNVERIFIED, never FLOATING), so a tight zone cannot hard-fail a correctly-read piece."""
    xs, ys = [], []
    for p in spec["room"]["outline_mm"]:
        xs.append(p[0] + offset[0]); ys.append(p[1] + offset[1])
    for sr in spec.get("subrooms", []):
        for p in sr.get("outline_mm", []):
            xs.append(p[0] + offset[0]); ys.append(p[1] + offset[1])
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _pieces(spec):
    loose = list(spec.get("items", []))
    fixed = list(spec.get("builtins", []))
    for sr in spec.get("subrooms", []):
        fixed += sr.get("fixtures", [])
    return loose, fixed


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(pdf, target, page=None, close_mm=None, calib=None):
    """Load a manifest (multi-room) or a single scene-graph, extract clusters per room,
    gate each, print a report, and return overall verdict + per-room results.

    page/close_mm/calib default from the manifest ('page','close_mm','calibration' fields)
    then to this sheet's values — so a different project can carry its own calibration and is
    NOT silently read in the wrong coordinate frame. The calibration used is logged."""
    from plan_cluster import extract_clusters, SCALE, OX, OY

    base = os.path.dirname(os.path.abspath(target))
    doc = json.load(open(target, encoding="utf-8"))
    page = doc.get("page", 1) if page is None else page
    close_mm = doc.get("close_mm", 18.0) if close_mm is None else close_mm
    if calib is None:
        calib = tuple(doc["calibration"]) if "calibration" in doc else (SCALE, OX, OY)
    print(f"gate calibration: scale={calib[0]} ox={calib[1]} oy={calib[2]}  page={page}  "
          f"close_mm={close_mm}  (verify this matches {os.path.basename(pdf)})")

    input_paths = [os.path.abspath(target)]
    rooms = []          # (room_id, spec, offset_mm, spec_path)
    if "furnish" in doc:                      # a floor manifest
        for f in doc["furnish"]:
            spec_path = f["spec"]
            if not os.path.isabs(spec_path) and not os.path.exists(spec_path):
                spec_path = os.path.join(base, os.path.basename(spec_path))
            spec = json.load(open(spec_path, encoding="utf-8"))
            rooms.append((f.get("id", spec["room"].get("type", "room")),
                          spec, tuple(f.get("offset_mm", [0, 0])), os.path.abspath(spec_path)))
            input_paths.append(os.path.abspath(spec_path))
    else:                                     # a single scene-graph
        rooms.append((doc["room"].get("type", "room"), doc, (0, 0), os.path.abspath(target)))

    results, worst = [], "PASS"
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    for room_id, spec, offset, _sp in rooms:
        loose, fixed = _pieces(spec)
        zone = _room_zone(spec, offset)
        res = extract_clusters(pdf, page, zone, close_mm, calib=calib)
        r = gate(loose, fixed, res["items"], _ink_counter(res), zone, offset)
        r["room"] = room_id
        results.append(r)
        if order[r["verdict"]] > order[worst]:
            worst = r["verdict"]

    _report(results, worst)
    marker = _write_marker(target, worst, results, input_paths)
    print(f"wrote gate marker: {marker}  (build refuses on FAIL, on un-signed REVIEW, or when an "
          f"input hash no longer matches)")
    return worst, results


def _write_marker(target, worst, results, input_paths):
    """Persist the verdict next to the target so the Blender build (which lacks fitz/scipy) can
    enforce the gate. The marker is bound to the exact files it gated by CONTENT HASH: build
    refuses unless every input it needs (manifest + each furnished scene-graph) is present in
    'inputs' with a matching sha1. This kills three holes at once — a stale edit, a manifest
    offset/furnish change (specs untouched), and a marker written by gating a DIFFERENT target
    in the same directory. Hash beats mtime: immune to OneDrive re-sync touching mtimes."""
    marker = os.path.join(os.path.dirname(os.path.abspath(target)), "placement-gate.json")
    inputs = {}
    for p in input_paths:
        try:
            inputs[os.path.basename(p)] = _sha1(p)
        except OSError:
            pass
    payload = {
        "verdict": worst,
        "gated_target": os.path.basename(os.path.abspath(target)),
        "inputs": inputs,          # basename -> sha1 of every file the gate consumed
        "generated_epoch": time.time(),   # informational only; correctness uses hashes
        "rooms": [{"room": r["room"], "verdict": r["verdict"],
                   "floating": [x["name"] for x in (r["loose"] + r["fixed"]) if x["status"] == "floating"],
                   "unplaced": len(r["unplaced"])} for r in results],
        "note": "Auto-written by placement_gate.py. Do not hand-edit; re-run the gate to refresh.",
    }
    json.dump(payload, open(marker, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return marker


# ---- reporting -----------------------------------------------------------------------
_MARK = {"matched": "OK   ", "drift": "DRIFT", "on_ink": "ON-INK",
         "floating": "FLOAT", "unverified": "UNVER"}


def _report(results, worst):
    print("=" * 74)
    print("PLACEMENT GATE — does every placed piece land on something drawn in the plan?")
    print("=" * 74)
    for r in results:
        print(f"\n### room: {r['room']}   ({r['n_clusters']} drawn clusters)   -> {r['verdict']}")
        print("  LOOSE furniture (checked strictly against clusters):")
        for it in r["loose"]:
            print(f"    [{_MARK.get(it['status'],it['status']):6}] IoU {it['iou']:.2f}  {it['name']}")
        if r["fixed"]:
            print("  BUILT-INS / fixtures (label-derived, lenient):")
            for it in r["fixed"]:
                print(f"    [{_MARK.get(it['status'],it['status']):6}] IoU {it['iou']:.2f}  {it['name']}")
        if r["unplaced"]:
            print("  UNPLACED drawn clusters (missing furniture OR a label — CONFIRM each):")
            for c in r["unplaced"]:
                print(f"    [?]     {c['w']}x{c['d']}mm at ({c['x']},{c['y']})  "
                      f"area {c['area_m2']}m2  {'organic' if c['curve'] else 'rectilinear'}")

    # human-confirm checklist (the honest 'we read this much; sign the rest')
    todo = []
    for r in results:
        for it in r["loose"]:
            if it["status"] == "floating":
                todo.append(f"FIX  [{r['room']}] '{it['name']}' floats on empty floor (IoU {it['iou']:.2f}) — reposition or remove")
            elif it["status"] in ("drift", "on_ink"):
                todo.append(f"SIGN [{r['room']}] '{it['name']}' {it['status']} (IoU {it['iou']:.2f}) — confirm size/position")
        for it in r["fixed"]:
            if it["status"] in ("drift", "unverified"):
                todo.append(f"SIGN [{r['room']}] built-in '{it['name']}' unverified — confirm against BF label/wall")
        for c in r["unplaced"]:
            todo.append(f"SIGN [{r['room']}] drawn {c['w']}x{c['d']}mm at ({c['x']},{c['y']}) has NO piece — is it furniture (add) or a label (ignore)?")
    print("\n" + "-" * 74)
    if todo:
        print("HUMAN-CONFIRM CHECKLIST (nothing below was certified by the machine):")
        for t in todo:
            print("  - " + t)
    else:
        print("No open items — every placed piece matched a drawn cluster.")
    print("-" * 74)
    print(f"OVERALL: {worst}   " + {"FAIL": "(blocks the build — a piece floats on empty floor)",
                                    "REVIEW": "(build BLOCKED until a human signs off: build with --accept-review)",
                                    "PASS": "(machine-certified)"}[worst])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    _pdf, _target = sys.argv[1], sys.argv[2]
    _page = int(sys.argv[3]) if len(sys.argv) > 3 else None       # else from manifest / default
    _close = float(sys.argv[4]) if len(sys.argv) > 4 else None
    _verdict, _ = run(_pdf, _target, _page, _close)
    sys.exit(1 if _verdict == "FAIL" else 0)
