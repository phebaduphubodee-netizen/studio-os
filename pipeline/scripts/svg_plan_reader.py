"""svg_plan_reader.py -- OUR reader's SVG lane + the first FloorPlanCAD baseline run.

    python svg_plan_reader.py --sheet <in.svg> <scale_mm_per_unit> <out.pred.json>
    python svg_plan_reader.py --baseline <svg-dir> <gt-dir> <out-dir> [limit N] [overlays K] [walls oracle] [priors P]

priors P = kind-priors JSON (kind_priors.py); off by default -- without it elements never
carry kind. It is a BENCHMARK/SUGGESTION lane only (unique-band membership, ambiguity stays
unreported); production identity remains owner-signed and this path is never auto-applied.

WHY: gt-test-00 (5,502 machine-checkable answer keys) exists but no reader has ever been
scored against it -- the owner has still only ever seen our reads verified by eye. This
module runs the pipeline's OWN deterministic reading stack on the raw FloorPlanCAD SVGs
and scores it with benchmark_reader, producing the first real detection/F1/F4 numbers
(docs/research/2026-07-06-paired-2d3d-backlearn.md SS3).

WHAT "OUR READER" MEANS HERE (no new intelligence invented for the benchmark):
  elements  the SAME morphology engine the placement gate trusts --
            plan_cluster.cluster_segments (rasterize -> CLOSE -> connected components ->
            size screen) -- fed with SVG stroke polylines instead of PDF strokes.
  openings  the SAME thin-run candidate lane that flags glazing on the real sheets --
            glazing_candidates.promote -- with an EMPTY wall set, because this corpus
            draws every stroke at width 0.1 (verified: the PDF lane's 0.6 pt wall gate
            has NO signal here), so only PAIR + length evidence can fire. Candidates are
            emitted with type="candidate" -- deliberately OUTSIDE the F4 subtype
            vocabulary (door|sliding|window|opening): the lane has no door/window
            classifier, and scrutiny proved the earlier type="opening" sentinel silently
            collected subtype credit against GT bare-opening symbols (5/15 smoke sheets
            scored nonzero subtype accuracy with zero classifiers -- a verdict flip).
  identity  the production reader HAS NO symbol classifier (identity is owner-signed
            semantic truth) -> elements carry NO kind and F1 scores ~0. That zero is
            the honest baseline the next slices must beat, not a bug.

ANNOTATION BLINDNESS (the honesty core): the corpus SVGs carry the ANSWER KEY inline
(semantic-id / instance-id / layer labels). read_ink() parses geometry attributes only
and never reads those -- enforced by test_svg_plan_reader's strip-equivalence test
(reading an SVG with all annotation attributes deleted yields identical ink).

SCALE (calib-from-manifest, same pattern as placement_gate): mm-per-unit comes from the
gt.json meta, which the adapter derived from UNANNOTATED dimension ink -- sheet scale is
project metadata in our production lane too, never re-guessed per read. Sheets the
adapter could not calibrate (units='svg-unit') are SKIPPED AND COUNTED: mm-threshold
morphology on unknown-scale ink would be noise wearing numbers.

Coordinates stay in the RAW SVG FRAME x scale (y grows down), exactly like the gt.json
files -- IoU and centre-distance matching are handedness-blind, so no flip is applied.
"""
import glob
import json
import math
import os
import sys
import time
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import benchmark_reader as B
from floorplancad_adapter import walk_path, shape_points, SVG_NS
from glazing_candidates import axis_run, promote, run_endpoints
from swing_door_candidates import detect as detect_swing
from plan_cluster import cluster_segments
import kind_priors

READER_VERSION = "svg_plan_reader v2"
CLOSE_MM = 40.0          # bridge a symbol's internal stroke gaps; keep neighbours apart
BASE_RES_MM = 6.0        # the PDF lane's raster resolution (plan_cluster.RES)
MAX_RASTER_PX = 3000     # cap the longest raster axis; res coarsens on huge sheets and
                         # the res actually used is recorded in the pred meta
ZONE_PAD_MM = 100.0      # pad the ink bbox so closing near the border cannot clip

DRAW_TAGS = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}


# ---- annotation-blind ink extraction ----------------------------------------------------
def _path_ink(d, arcs=None):
    """Path -> (segments, curve_segments) as drawn polylines. Chains pen->point through
    walk_path output; 'ctrl' points are INCLUDED in the chain (arc sweep samples lie on
    the curve; Bezier control polygons over-ink slightly inside their hull -- the same
    fidelity class as the PDF lane's 8-step _bez sampling). Segments that touch a ctrl
    point are also returned as curve segments (feeds the cosmetic organic/curve flag)."""
    segs, csegs = [], []
    pen, pen_ctrl = None, False
    for (pt, flag) in walk_path(d, arcs):
        if flag == "move":
            pen, pen_ctrl = pt, False
            continue
        if pen is not None and pt != pen:
            segs.append([pen, pt])
            if flag == "ctrl" or pen_ctrl:
                csegs.append([pen, pt])
        pen, pen_ctrl = pt, (flag == "ctrl")
    return segs, csegs


def read_ink(svg_path):
    """Whole-sheet ink in raw svg units, ANNOTATION-BLIND: only tag names + geometry
    attributes are read (d/points/x/y/r/...); the corpus answer-key attributes and layer
    names are never queried (enforced by test_svg_plan_reader: behavioral strip-equivalence
    on read_sheet + a static string scan of this module).
    Returns {"segs", "curve_segs", counts...}; every skip is counted."""
    root = ET.parse(svg_path).getroot()
    segs, csegs = [], []
    arcs = []
    counts = {"n_prims": 0, "transforms_skipped": 0, "text_skipped": 0}
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag == "text":
            counts["text_skipped"] += 1     # <text> is not drawn geometry in this corpus
            continue
        if tag not in DRAW_TAGS:
            continue
        counts["n_prims"] += 1
        if el.get("transform"):
            counts["transforms_skipped"] += 1   # same rule as the adapter: skip, count
            continue
        if tag == "path":
            s, c = _path_ink(el.get("d"), arcs)
            segs += s
            csegs += c
        elif tag in ("circle", "ellipse"):
            pts = shape_points(el, tag)         # extent corners -> sample the ellipse
            if len(pts) == 2:
                (x0, y0), (x1, y1) = pts
                cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                rx, ry = (x1 - x0) / 2.0, (y1 - y0) / 2.0
                ring = [(cx + rx * math.cos(2 * math.pi * k / 16),
                         cy + ry * math.sin(2 * math.pi * k / 16)) for k in range(17)]
                arc = [[a, b] for a, b in zip(ring, ring[1:])]
                segs += arc
                csegs += arc
        else:
            pts = shape_points(el, tag)
            if tag == "rect" and len(pts) == 2:
                (x0, y0), (x1, y1) = pts
                ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
                segs += [[a, b] for a, b in zip(ring, ring[1:])]
            elif tag == "line" and len(pts) == 2:
                segs.append([pts[0], pts[1]])
            elif tag in ("polyline", "polygon") and len(pts) >= 2:
                chain = pts + ([pts[0]] if tag == "polygon" else [])
                segs += [[a, b] for a, b in zip(chain, chain[1:])]
    segs = [s for s in segs if s[0] != s[1]]
    return {"segs": segs, "curve_segs": csegs, "arcs": arcs, **counts}


# ---- one sheet -> pred document ----------------------------------------------------------
def read_sheet(svg_path, scale_mm_per_unit, close_mm=CLOSE_MM,
               wall_segs=None, wall_source=None, kind_priors_doc=None,
               emit_glazing_lines=False):
    """Raw SVG -> pred.json document (benchmark_reader schema, units=mm).

    kind_priors_doc (default None) is OFF for the blind headline lane: when None the pred
    is byte-identical to the classifier-less baseline (no kind on any element, no
    kind_priors meta key). When a priors doc is passed (benchmark/suggestion lane only),
    each element gets a kind ONLY on unique-band membership (kind_priors.suggest_kind);
    ambiguity stays unreported. Suggestion reads w/d only -- geometry, never annotations.

    emit_glazing_lines (default False) is OFF for the same byte-identity reason: only when
    True does the pred gain a top-level `glazing_lines` channel (the promote() candidates as
    {x1,y1,x2,y2,tier,score} segments) so benchmark_reader's F6 can score glazing FLAG
    recall/precision vs the GT curtain_wall/railing channel. Default-off keeps the committed
    blind baseline (and its pred byte-identity tests) unchanged."""
    s = float(scale_mm_per_unit)
    ink = read_ink(svg_path)
    segs = [[(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)] for a, b in ink["segs"]]
    csegs = [[(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)] for a, b in ink["curve_segs"]]
    arcs = [{"cx": a["cx"] * s, "cy": a["cy"] * s, "rx": a["rx"] * s, "ry": a["ry"] * s,
             "phi_deg": a["phi_deg"], "sweep_deg": a["sweep_deg"],
             "x1": a["x1"] * s, "y1": a["y1"] * s, "x2": a["x2"] * s, "y2": a["y2"] * s,
             "pts": [(px * s, py * s) for px, py in a["pts"]]}
            for a in ink["arcs"]]

    elements, res_eff, zone = [], None, None
    if segs:
        xs = [p[0] for seg in segs for p in seg]
        ys = [p[1] for seg in segs for p in seg]
        zone = (min(xs) - ZONE_PAD_MM, min(ys) - ZONE_PAD_MM,
                max(xs) + ZONE_PAD_MM, max(ys) + ZONE_PAD_MM)
        extent = max(zone[2] - zone[0], zone[3] - zone[1])
        res_eff = max(BASE_RES_MM, extent / MAX_RASTER_PX)
        clu = cluster_segments(segs, csegs, zone, close_mm, res=res_eff)
        for k, it in enumerate(clu["items"]):
            el = {"id": f"c{k:03d}", "x": it["x"], "y": it["y"],
                  "w": it["w"], "d": it["d"],
                  "curve": it["curve"], "fill": it["fill"]}
            if kind_priors_doc:
                ks = kind_priors.suggest_kind(el["w"], el["d"], kind_priors_doc,
                                              curve=el["curve"])
                if ks:
                    el["kind"] = ks
            elements.append(el)
        n_dropped = len(clu["dropped"])
    else:
        n_dropped = 0

    openings = []
    w_segs, n_diag = [], 0
    if wall_source is not None and wall_source != "oracle":
        raise ValueError(f"unknown wall_source {wall_source!r} -- only 'oracle' exists; "
                         "an unknown label must never wrap a blind run")
    if wall_segs and wall_source is None:
        raise ValueError("wall_segs given without wall_source -- refusing an UNLABELED "
                         "wall-aware read")
    if wall_source == "oracle":
        # GT-side wall geometry, ALREADY in mm (adapter scales at emission) -- never
        # rescale here. Raw 2-point segments [[x1,y1],[x2,y2]], exactly what promote
        # expects; diagonal segs are counted (axis_run=None -> they contribute nothing
        # to suppression or contact) rather than silently vanishing.
        w_segs = list(wall_segs or [])
        n_diag = sum(1 for s2 in w_segs if axis_run(s2) is None)
    cands, stats = promote(segs, wall_segs=w_segs)
    for k, c in enumerate(cands):
        (ax, ay), (bx, by) = c["segments"][0][0], c["segments"][0][1]
        openings.append({"id": f"g{k:03d}", "type": "candidate",
                         "x": round(min(ax, bx), 1), "y": round(min(ay, by), 1),
                         "w": round(abs(bx - ax), 1), "d": round(abs(by - ay), 1),
                         "tier": c["tier"], "score": c["score"]})
    swing, sw_stats = detect_swing(arcs, segs)
    for k, c in enumerate(swing):
        openings.append({"id": f"a{k:03d}", "type": c["type"],
                         "x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"],
                         "tier": c["tier"]})

    pred = {
        "meta": {
            "source": "svg-ink", "reader": READER_VERSION,
            "file": os.path.basename(svg_path), "units": "mm",
            "scale_mm_per_unit": s,
            "scale_provenance": "gt-manifest (calib-from-manifest; adapter derived it "
                                "from unannotated dimension ink)",
            "close_mm": close_mm, "res_mm_per_px": res_eff,
            "n_segs": len(segs), "n_prims": ink["n_prims"],
            "transforms_skipped": ink["transforms_skipped"],
            "text_skipped": ink["text_skipped"],
            "clusters_dropped": n_dropped,
            "opening_candidate_stats": stats,
            "swing_door_stats": sw_stats,
        },
        "elements": elements,
        "openings": openings,
    }
    if wall_source is not None:
        # wall keys appear ONLY in wall mode: the blind headline lane's meta must not
        # change by one key (corpus pred byte-identity vs the committed baseline)
        pred["meta"]["wall_source"] = wall_source
        pred["meta"]["wall_segs_n"] = len(w_segs)
        pred["meta"]["wall_diag_unusable"] = n_diag
    if kind_priors_doc:
        # priors meta appears ONLY in the suggestion lane: the blind lane's meta stays
        # byte-for-byte identical to the committed baseline (pinned in the reader tests)
        pred["meta"]["kind_priors"] = {
            "schema": kind_priors_doc["schema"],
            "derived_from": [os.path.basename(os.path.normpath(d))
                             for d in kind_priors_doc["meta"]["derived_from"]],
            "n_kinds": len(kind_priors_doc["kinds"]),
            "kinds_emitted": sum(1 for e in elements if "kind" in e),
        }
    if emit_glazing_lines:
        # glazing channel appears ONLY when opted in: the blind lane's pred stays
        # byte-identical to the committed baseline. promote() candidates as raw segments
        # (no glass-subtype kind -- curtain-wall-vs-railing is an owner call the reader
        # cannot make, so F6 scores DETECTION recall/precision, not subtype).
        gl = []
        for c in cands:
            (ax0, ay0), (bx0, by0) = c["segments"][0][0], c["segments"][0][1]
            gl.append({"x1": round(ax0, 1), "y1": round(ay0, 1),
                       "x2": round(bx0, 1), "y2": round(by0, 1),
                       "tier": c["tier"], "score": c["score"]})
        pred["glazing_lines"] = gl
    return pred


# ---- overlay (owner scans, not hunts) ----------------------------------------------------
def render_overlay(pred, gt, segs_mm, out_png):
    """Ink (grey) + GT elements (green) + pred clusters (blue) + GT openings (orange)
    + pred opening runs (red). Y axis inverted so the picture matches the corpus PNG."""
    fig, ax = plt.subplots(figsize=(14, 14), dpi=110)
    if segs_mm:
        ax.add_collection(LineCollection(segs_mm, colors="#c9c9c9", linewidths=0.4))
    for e in gt.get("elements", []):
        ax.add_patch(plt.Rectangle((e["x"], e["y"]), e["w"], e["d"], fill=False,
                                   edgecolor="#1a9641", lw=1.6))
    for e in pred.get("elements", []):
        ax.add_patch(plt.Rectangle((e["x"], e["y"]), e["w"], e["d"], fill=False,
                                   edgecolor="#2b5fc0", lw=1.1, linestyle="--"))
    for o in gt.get("openings", []):
        # sanitize_openings tolerates missing/null w,d in SCORING -- the picture must too
        ax.add_patch(plt.Rectangle((o["x"], o["y"]),
                                   max(o.get("w") or 0, 40), max(o.get("d") or 0, 40),
                                   fill=False, edgecolor="#ff8c00", lw=1.6))
    for o in pred.get("openings", []):
        ax.plot([o["x"], o["x"] + (o.get("w") or 0)], [o["y"], o["y"] + (o.get("d") or 0)],
                color="#d7191c", lw=1.4)
    ax.autoscale()
    ax.invert_yaxis()                        # svg frame draws y down
    ax.set_aspect("equal")
    ax.set_title(f"{pred['meta']['file']} -- green=GT elem, blue--=pred cluster, "
                 f"orange=GT opening, red=pred opening-run", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close(fig)


# ---- corpus baseline run -------------------------------------------------------------------
def run_baseline(svg_dir, gt_dir, out_dir, limit=None, overlays=0, walls=None, priors=None):
    os.makedirs(os.path.join(out_dir, "preds"), exist_ok=True)
    if overlays:
        os.makedirs(os.path.join(out_dir, "overlays"), exist_ok=True)
    # load ONCE, before the loop: a bad priors path must fail the whole run loudly at
    # startup, never turn into 2,245 per-sheet "error" rows that look like corpus problems
    pdoc = kind_priors.load(priors) if priors else None
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    if walls not in (None, "oracle"):
        raise SystemExit(f"unknown walls lane {walls!r} -- only 'oracle' exists")
    if walls == "oracle":
        try:
            first = json.load(open(gt_files[0], encoding="utf-8"))
        except Exception as e:                 # loud refusal beats a raw traceback
            raise SystemExit(f"walls oracle: first gt file unreadable "
                             f"({type(e).__name__}: {e}) -- regenerate the gt dir")
        if "wall_lines" not in first:
            raise SystemExit("walls oracle: first gt file has no 'wall_lines' key -- "
                             "regenerate the gt dir with floorplancad_adapter v1.1 "
                             "--batch before running the oracle lane")
    cards = []
    skipped = {"svg-unit": 0, "svg-missing": 0, "error": 0}
    overlay_failed = 0
    wall_stats = {"segs": 0, "diagonal": 0} if walls else None
    t0 = time.time()
    # rows stream to disk as they complete: a mid-run death keeps the finished work
    # (scrutiny 2026-07-06: gt-load crashes used to abort the run AND lose every row)
    rows_fh = open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8")

    def row(obj):
        if walls:
            obj = {**obj, "wall_source": walls}
        rows_fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        rows_fh.flush()

    for k, gfp in enumerate(gt_files):
        base = os.path.basename(gfp)[:-len(".gt.json")]
        try:                                 # one bad sheet costs one row, never the run
            gt = json.load(open(gfp, encoding="utf-8"))
            if gt["meta"]["units"] != "mm":
                skipped["svg-unit"] += 1
                row({"file": base, "skipped": "svg-unit"})
                continue
            sfp = os.path.join(svg_dir, base + ".svg")
            if not os.path.exists(sfp):
                skipped["svg-missing"] += 1
                row({"file": base, "skipped": "svg-missing"})
                continue
            if walls == "oracle":
                # strict indexing: in a mixed old/new gt dir a missing wall_lines key
                # must become a counted "error" row, never a silent empty-wall sheet
                # wearing the oracle label
                wsegs = [[[w["x1"], w["y1"]], [w["x2"], w["y2"]]]
                         for w in gt["wall_lines"]]
                pred = read_sheet(sfp, gt["meta"]["scale_mm_per_unit"],
                                  wall_segs=wsegs, wall_source="oracle",
                                  kind_priors_doc=pdoc)
            else:
                pred = read_sheet(sfp, gt["meta"]["scale_mm_per_unit"],
                                  kind_priors_doc=pdoc)
            card = B.score_pair(gt, pred)
            with open(os.path.join(out_dir, "preds", base + ".pred.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(pred, fh, ensure_ascii=False)
            cards.append(card)
            row({"file": base, "card": card})
            if walls:
                wall_stats["segs"] += pred["meta"]["wall_segs_n"]
                wall_stats["diagonal"] += pred["meta"]["wall_diag_unusable"]
            if overlays and len(cards) <= overlays:
                try:                # a failed PICTURE must not error-count a SCORED sheet
                    s = float(gt["meta"]["scale_mm_per_unit"])
                    segs = [[(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)]
                            for a, b in read_ink(sfp)["segs"]]
                    render_overlay(pred, gt, segs,
                                   os.path.join(out_dir, "overlays", base + ".png"))
                except Exception as e:
                    overlay_failed += 1
                    print(f"  overlay failed on {base}: {type(e).__name__}: {e}")
        except Exception as e:
            skipped["error"] += 1
            row({"file": base, "skipped": "error",
                 "error": f"{type(e).__name__}: {e}"})
            continue
        finally:
            if (k + 1) % 100 == 0:
                print(f"  {k + 1}/{len(gt_files)}  scored={len(cards)}  "
                      f"({time.time() - t0:.0f}s)")
    rows_fh.close()
    priors_note = (f"{os.path.basename(priors)} ({len(pdoc['kinds'])} kinds)"
                   if priors else None)
    report = render_baseline_report(cards, skipped, len(gt_files), time.time() - t0,
                                    overlay_failed=overlay_failed,
                                    walls=walls, wall_stats=wall_stats,
                                    priors_note=priors_note)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}\\cards.jsonl + report.md")
    return cards, skipped


def render_baseline_report(cards, skipped, n_total, secs, overlay_failed=0,
                           walls=None, wall_stats=None, priors_note=None):
    if not cards:
        return ("# FloorPlanCAD baseline"
                + (f" -- {walls.upper()}-WALL lane (wall_source={walls})" if walls else "")
                + "\n\nno sheets scored -- " + json.dumps(skipped))
    agg = B.aggregate(cards)
    det, f1, f4 = agg["detection"], agg["F1_identity"], agg["F4_openings"]

    def pct(v):
        return "n/a" if v is None else f"{100.0 * v:.1f}%"

    verdicts = {}
    for m in ("detection", "F1_identity", "F4_openings"):
        for c in cards:
            verdicts.setdefault(m, {}).setdefault(c[m]["verdict"], 0)
            verdicts[m][c[m]["verdict"]] += 1

    # F1 section: the no-priors lane keeps the exact classifier-less prose (report
    # stability); the priors lane replaces it with an aggregate per-kind table summed
    # from the cards' INTEGER per_kind counts (aggregate() drops per_kind, so this is
    # the only corpus-level per-kind view -- never averaged from per-card accuracies).
    if priors_note is None:
        f1_lines = [
            "## F1 identity",
            f"- accuracy {pct(f1['accuracy'])} on {f1['n']} matched pairs -- the reader has "
            f"NO symbol classifier (identity is owner-signed in production); this zero is "
            f"the baseline to beat, not a bug",
        ]
    else:
        per, unrep = {}, 0
        for c in cards:
            for k, r in c["F1_identity"]["per_kind"].items():
                if k == "":
                    unrep += r["pred"]           # norm_kind(None)->'' : the unreported counter
                    continue
                row = per.setdefault(k, {"gt": 0, "pred": 0, "hit": 0})
                row["gt"] += r["gt"]
                row["pred"] += r["pred"]
                row["hit"] += r["hit"]
        emitted = sum(r["pred"] for r in per.values())
        hits = sum(r["hit"] for r in per.values())
        f1_lines = [
            "## F1 identity",
            f"- kind priors: {priors_note} -- deterministic size/aspect bands from TRAIN "
            f"gt; unique-band membership only, ambiguity stays unreported",
            f"- accuracy {pct(f1['accuracy'])} on {f1['n']} matched pairs",
            f"- emitted kind on {emitted}/{f1['n']} matched pairs; emitted-correct {hits} "
            f"-> emitted precision {pct(hits / emitted) if emitted else 'n/a'}",
            f"- unreported (no kind emitted) on {unrep} matched pairs -- counted as WRONG "
            f"in accuracy (unreported is scored, never skipped in F1)",
        ]
        for k in sorted(per, key=lambda z: -per[z]["gt"]):
            r = per[k]
            if r["gt"] + r["pred"] == 0:
                continue
            f1_lines.append(
                f"    - {k}: gt {r['gt']}, pred {r['pred']}, hit {r['hit']}, "
                f"precision {pct(r['hit'] / r['pred']) if r['pred'] else 'n/a'}, "
                f"recall {pct(r['hit'] / r['gt']) if r['gt'] else 'n/a'}")
    L = [
        ("# FloorPlanCAD baseline -- OUR reader vs gt (first real numbers)"
         if not walls else
         f"# FloorPlanCAD baseline -- {walls.upper()}-WALL lane "
         f"(wall_source={walls}; NOT the blind headline)"), "",
        f"- reader: {READER_VERSION} (annotation-blind ink -> plan_cluster morphology; "
        f"openings = glazing_candidates pair-runs (untyped) + "
        f"swing-door arc lane (typed 'door' on arc+leaf / mirrored-double evidence))",
        f"- sheets: {len(cards)} scored / {n_total} gt files "
        f"(skipped: {json.dumps(skipped)}); wall-clock {secs:.0f}s"
        + (f"; OVERLAY RENDER FAILED on {overlay_failed} scored sheet(s)"
           if overlay_failed else ""),
        "",
        f"## detection (element footprints, IoU>=0.5)",
        f"- GT {det['n_gt']} vs pred {det['n_pred']} -> matched {det['matched']}: "
        f"recall {pct(det['recall'])}, precision {pct(det['precision'])}",
        f"- per-sheet verdicts: {verdicts['detection']}",
        "",
        *f1_lines,
        "",
        f"## F4 openings (centre <= 300 mm)",
        f"- GT {f4['n_gt']} vs pred {f4['n_pred']} -> matched {f4['matched']}: "
        f"recall {pct(f4['recall'])}, precision {pct(f4['precision'])}",
        f"- per-GT-type recall (the wound is `sliding`):",
    ]
    for t, row in sorted((f4.get("per_type_gt") or {}).items()):
        L.append(f"    - {t}: {row['matched']}/{row['n_gt']} = {pct(row['recall'])}")
    L += [
        "",
        "## honesty notes",
        "- F2 facing / F3 indoor / F5 floor: UNWIRED -- this corpus carries no such GT.",
        "- svg-unit sheets are skipped, never scored with guessed scale.",
        "- pair-lane openings stay type='candidate' (outside the GT vocabulary: zero "
        "unearned subtype credit); swing-lane openings claim type='door' ONLY on earned "
        "arc+leaf / mirrored-double evidence, so nonzero subtype accuracy is real signal. "
        "A per-sheet F4 PASS additionally needs recall AND precision >= 0.9 -- the "
        "empty-wall candidate flood keeps that out of reach until the wall-aware pass.",
        "- element precision counts every non-furniture ink cluster (dim blocks, "
        "annotation symbols) as a phantom -- that is the point: the number the owner's "
        "eye used to absorb is now on paper.",
    ]
    if walls == "oracle":
        L += ["- WALL SOURCE = ORACLE: promote() received the GT's own wall_lines "
              "(answer-key side). This lane measures the CEILING of wall-aware "
              "precision and must NEVER be quoted as the blind headline "
              "(that remains qa/reports/floorplancad-baseline-2026-07-06.md).",
              f"- oracle wall segs fed: {wall_stats['segs']}; diagonal/unusable "
              f"(axis_run=None -- contribute nothing to suppression or contact): "
              f"{wall_stats['diagonal']}"]
    L += ["", f"reader: {READER_VERSION}"]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--sheet":
        pred = read_sheet(argv[2], float(argv[3]))
        out = argv[4] if len(argv) > 4 else None
        if out:
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(pred, fh, ensure_ascii=False, indent=1)
        m = pred["meta"]
        print(f"{m['file']}: {len(pred['elements'])} clusters, "
              f"{len(pred['openings'])} opening candidates, res={m['res_mm_per_px']}")
    elif len(argv) >= 5 and argv[1] == "--baseline":
        kw = {}
        rest = argv[5:]
        while rest:
            if len(rest) >= 2 and rest[0] in ("limit", "overlays") and rest[1].isdigit():
                kw[rest[0]] = int(rest[1])
            elif len(rest) >= 2 and rest[0] == "walls" and rest[1] in ("oracle",):
                kw["walls"] = rest[1]
            elif len(rest) >= 2 and rest[0] == "priors":
                kw["priors"] = rest[1]           # a PATH -- never passes .isdigit()
            else:
                raise SystemExit(f"bad option {rest[0]!r} -- expected: "
                                 f"[limit N] [overlays K] [walls oracle] [priors P]\n\n{__doc__}")
            rest = rest[2:]
        run_baseline(argv[2], argv[3], argv[4], **kw)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
