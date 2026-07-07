"""
glazing_candidates.py -- F4: promote THIN dark strokes to glazing / thin-wall CANDIDATES
for owner review, instead of silently dropping them like the thick-stroke wall gate does.

    python glazing_candidates.py <plan.pdf> <walls.json> <out.json> [manifest.json]

(passing the build manifest suppresses thin ink inside placed-furniture footprints --
the gate-certified rects -- which is most of the interior noise on a furnished sheet)

WHY: real boundaries are drawn THIN on purpose. The SW-corner wall faces of the real
floor-2 sheet are 0.48 pt (below is_wall_stroke's 0.6 pt gate) and the sliding-glass
facade is thinner still. ASA CAD standard 2554 (verified: knowledge/classifications/
thai-cad-layers-asa2554.md) makes width USELESS as an identifier: glazing 0.25 =
interior walls 0.25 = furniture 0.25 (only exterior walls 0.35 are thicker, and a
grade-level tree is 0.5) -- and this one sheet draws ~4.5k furniture/dimension strokes
with the same 0.48 pt dark pen. So lowering the wall gate globally is NOT the fix;
what separates a boundary from furniture ink is STRUCTURE, and a thin run is promoted
only on structural evidence:

  PAIR          two long parallel thin runs 40..250 mm apart = a drawn face pair
                (the real SW patch is exactly this: verticals 101.6 mm apart).
  WALL-CONTACT  a run endpoint lands within end_tol of the extracted thick-wall
                geometry (continuation of a wall line, or spanning a wall gap --
                the classic sliding-door-in-gap).
  LENGTH        strengthens a candidate that already has pair or contact evidence
                (worth 1 point -- it can never promote a run on its own).

HONESTY CONTRACT (matches the two-layer crystallization): this tool only FLAGS
candidates -- it never injects walls. Whether a candidate is a wall face, a glass
facade, or furniture ink is a SEMANTIC call that stays with the owner. The output's
manual_additions_stub is a TEMPLATE with an EMPTY segments list: the owner copies the
specific candidates they confirm (each candidate carries its own `segments`) into
their own signed record -- and pdf_extract_walls.merge_carried REFUSES to re-inject
any record whose `by` still carries the OWNER-CONFIRM-PENDING marker, so an unsigned
paste is machine-inert, not just discouraged by prose. Candidates that re-derive an
existing owner patch are labelled confirms_manual_patch (machine agrees with a past
sign: evidence the patch is recoverable from ink, not eyeballed).

Calibration is read FROM the walls JSON (calib-from-manifest, same pattern as
placement_gate) -- never re-typed. The wall set used for scoring EXCLUDES the
manual_additions segments so the tool honestly re-derives them from raw ink.

KNOWN NOISE (documented, measured on the real sheet): furniture drawn as nested
double lines ~40..250 mm apart WILL reach strong when an end also touches a wall
(pair 2 + contact 1 >= 3; a bed pushed against its head wall does this). The real
cut is the manifest footprint suppression (pass the manifest!), which strips the
inner strip and thereby starves the outline of its pair mate; without a manifest
the list is a REVIEW artifact and the overlay is the scan surface -- that is why
the stub ships empty rather than pre-filled with strong candidates. Runs are also
NOT chained across corners in v1 -- an L-shaped glass return scores per leg.
"""
import json
import math
import os
import sys
import time

from pdf_extract_walls import is_wall_stroke, keep_segment, map_pt, _valid_seg

# thin-stroke gate: everything BELOW the wall gate but still a real drawn pen.
# 0.05 floor drops width-0 hairline artifacts (411 on the real sheet) whose weight
# the PDF leaves to the viewer -- they are not a drafting pen choice we can read.
THIN_MIN_PT = 0.05
DEFAULTS = dict(
    off_tol=6.0,       # mm; c-band when clustering collinear pieces into one run
    gap_tol=160.0,     # mm; max along-axis break still merged (door-frame breaks)
    min_len=400.0,     # mm; shortest run worth reporting (a glass panel / wall face)
    pair_gap=(40.0, 250.0),   # mm; face-pair separation (real SW pair: 101.6)
    pair_overlap=0.5,  # fraction of the shorter run the pair must overlap on-axis
    end_tol=250.0,     # mm; run endpoint counts as touching wall within this
    covered_tol=12.0,  # mm; collinear offset at which a wall already covers a run
    covered_frac=0.8,  # runs >=80% under an existing collinear wall are not news
)


# ---- pure geometry (NO fitz -> unit-testable) -----------------------------------------
def axis_run(seg, max_off_axis=8.0):
    """Axis-aligned segment -> ('v', x, ylo, yhi) or ('h', y, xlo, xhi); None if slanted.
    'c' is the constant coordinate (the line's position), lo..hi the span along the axis."""
    if not _valid_seg(seg):
        return None
    (x1, y1), (x2, y2) = seg
    if abs(x1 - x2) <= max_off_axis and abs(y1 - y2) > abs(x1 - x2):
        return ("v", (x1 + x2) / 2.0, min(y1, y2), max(y1, y2))
    if abs(y1 - y2) <= max_off_axis and abs(x1 - x2) >= abs(y1 - y2):
        return ("h", (y1 + y2) / 2.0, min(x1, x2), max(x1, x2))
    return None


def merge_runs(segs, off_tol=DEFAULTS["off_tol"], gap_tol=DEFAULTS["gap_tol"]):
    """Merge fragmented collinear pieces into maximal runs (the real sheet draws one
    650 mm wall face as 3+ pieces). Greedy c-band clustering per axis, then interval
    union with gaps <= gap_tol bridged. Returns dicts:
      {axis, c, lo, hi, length, pieces, coverage}
    where coverage = drawn ink / span (a run bridged across big gaps scores low ink).
    A band is capped at TOTAL width off_tol from its first member -- chaining on
    consecutive gaps alone lets fine-pitch hatching (strokes every ~5 mm) drift a band
    across tens of mm and swallow two DISTINCT parallel faces into one phantom line."""
    by_axis = {"v": [], "h": []}
    for s in segs:
        r = axis_run(s)
        if r:
            by_axis[r[0]].append(r)
    runs = []
    for axis, items in by_axis.items():
        items.sort(key=lambda r: r[1])
        group = []
        for r in items:
            if group and (r[1] - group[-1][1] > off_tol or r[1] - group[0][1] > off_tol):
                runs.extend(_merge_group(axis, group, gap_tol))
                group = []
            group.append(r)
        if group:
            runs.extend(_merge_group(axis, group, gap_tol))
    return runs


def _merge_group(axis, group, gap_tol):
    """One c-band -> interval-union its spans (sorted by lo), bridging gaps <= gap_tol."""
    ivs = sorted((r[2], r[3], r[1]) for r in group)      # (lo, hi, c)
    out = []
    cur = None
    for lo, hi, c in ivs:
        if cur and lo - cur["hi"] <= gap_tol:
            cur["hi"] = max(cur["hi"], hi)
            cur["_cs"].append((c, hi - lo))
            cur["_ink"] += hi - lo
            cur["pieces"] += 1
        else:
            if cur:
                out.append(_finish_run(axis, cur))
            cur = {"hi": hi, "lo": lo, "_cs": [(c, hi - lo)], "_ink": hi - lo, "pieces": 1}
    if cur:
        out.append(_finish_run(axis, cur))
    return out


def _finish_run(axis, cur):
    wsum = sum(w for _c, w in cur["_cs"]) or 1.0
    c = sum(c * w for c, w in cur["_cs"]) / wsum         # ink-weighted line position
    span = cur["hi"] - cur["lo"]
    return {"axis": axis, "c": round(c, 1), "lo": round(cur["lo"], 1),
            "hi": round(cur["hi"], 1), "length": round(span, 1),
            "pieces": cur["pieces"],
            "coverage": round(min(1.0, cur["_ink"] / span), 2) if span > 0 else 1.0}


def dist_point_seg(px, py, seg):
    """Distance from point to a 2-point segment."""
    (x1, y1), (x2, y2) = seg
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def run_endpoints(run):
    if run["axis"] == "v":
        return ((run["c"], run["lo"]), (run["c"], run["hi"]))
    return ((run["lo"], run["c"]), (run["hi"], run["c"]))


def ends_near_walls(run, wall_segs, end_tol=DEFAULTS["end_tol"],
                    covered_tol=DEFAULTS["covered_tol"]):
    """How many of the run's two endpoints STRUCTURALLY touch wall geometry (0/1/2).
    2 = spans between walls (gap-span), 1 = continues a wall line off its end.
    Counts only PERPENDICULAR walls or COLLINEAR continuations (same line within
    covered_tol) -- a wall merely running parallel alongside the run (furniture
    pushed against a wall) is sideways adjacency, not a joint, and must not score;
    that is exactly how a headboard pair would otherwise fake wall contact."""
    n = 0
    for (px, py) in run_endpoints(run):
        for s in wall_segs:
            w = axis_run(s)
            if w is None:
                continue                      # walls are axis-aligned by extraction
            if w[0] == run["axis"] and abs(w[1] - run["c"]) > covered_tol:
                continue                      # sideways-parallel: not a structural joint
            if dist_point_seg(px, py, s) <= end_tol:
                n += 1
                break
    return n


def covered_by_walls(run, wall_runs, covered_tol=DEFAULTS["covered_tol"]):
    """Fraction of the run's span already overlapped by a COLLINEAR wall run --
    a thin line redrawn on top of an extracted wall is not a discovery."""
    span = run["hi"] - run["lo"]
    if span <= 0:
        return 1.0
    ivs = []
    for w in wall_runs:
        if w["axis"] == run["axis"] and abs(w["c"] - run["c"]) <= covered_tol:
            lo, hi = max(run["lo"], w["lo"]), min(run["hi"], w["hi"])
            if hi > lo:
                ivs.append((lo, hi))
    ivs.sort()
    cov = 0.0
    cur_lo = cur_hi = None
    for lo, hi in ivs:
        if cur_hi is None or lo > cur_hi:
            if cur_hi is not None:
                cov += cur_hi - cur_lo
            cur_lo, cur_hi = lo, hi
        else:
            cur_hi = max(cur_hi, hi)
    if cur_hi is not None:
        cov += cur_hi - cur_lo
    return cov / span


def find_pair(i, runs, pair_gap=DEFAULTS["pair_gap"], pair_overlap=DEFAULTS["pair_overlap"]):
    """Index of a parallel mate run (same axis, 40..250 mm away, on-axis overlap >=
    pair_overlap of the SHORTER run), else None. Nearest-gap mate wins."""
    a = runs[i]
    best, best_gap = None, None
    for j, b in enumerate(runs):
        if j == i or b["axis"] != a["axis"]:
            continue
        gap = abs(b["c"] - a["c"])
        if not (pair_gap[0] <= gap <= pair_gap[1]):
            continue
        ov = min(a["hi"], b["hi"]) - max(a["lo"], b["lo"])
        shorter = min(a["hi"] - a["lo"], b["hi"] - b["lo"])
        if shorter <= 0 or ov < pair_overlap * shorter:
            continue
        if best_gap is None or gap < best_gap:
            best, best_gap = j, gap
    return best


def inside_footprint(run, rects, margin=30.0, span_frac=0.7):
    """True when the run's line lies STRICTLY inside a placed-furniture footprint rect
    (x0,y0,x1,y1): its c is > margin from the two parallel rect edges and >=span_frac
    of its span falls within the rect. Ink inside a certified footprint is furniture
    detail (headboard strips, drawer fronts, stair treads), not a boundary. STRICT on
    purpose: a furniture OUTLINE sits ON the rect edge, and a glass wall behind a
    wardrobe sits outside it -- both survive; suppressing interiors alone also strips
    outlines of their 40..250 mm pair mates, so outline noise decays to weak/dropped."""
    for (x0, y0, x1, y1) in rects:
        if run["axis"] == "v":
            if not (x0 + margin < run["c"] < x1 - margin):
                continue
            lo, hi = y0, y1
        else:
            if not (y0 + margin < run["c"] < y1 - margin):
                continue
            lo, hi = x0, x1
        span = run["hi"] - run["lo"]
        ov = min(run["hi"], hi) - max(run["lo"], lo)
        if span > 0 and ov >= span_frac * span:
            return True
    return False


def matches_manual(run, manual_segs, covered_tol=DEFAULTS["covered_tol"]):
    """True when this run re-derives an owner-patched segment: same line, overlap
    >= 50% of the MANUAL seg AND >= 30% of the RUN's own span -- the second leg stops
    a long unrelated collinear run (a whole facade line that merely passes through
    the patched stretch) from wearing the green 'machine agrees with a past sign'."""
    span = run["hi"] - run["lo"]
    for s in manual_segs:
        m = axis_run(s)
        if not m or m[0] != run["axis"] or abs(m[1] - run["c"]) > covered_tol:
            continue
        ov = min(run["hi"], m[3]) - max(run["lo"], m[2])
        if (m[3] - m[2] > 0 and ov >= 0.5 * (m[3] - m[2])
                and span > 0 and ov >= 0.3 * span):
            return True
    return False


def promote(thin_segs, wall_segs, manual_segs=(), params=None, furn_rects=()):
    """(candidates, stats). Score = 2*pair + ends_near_walls(0..2) + 1 if >=1000 mm.
    tier: strong >=3, weak ==2; score <2 dropped (reported in stats, never silent).
    furn_rects (optional, from the manifest's placed pieces): runs strictly inside a
    certified furniture footprint are suppressed BEFORE pairing, so interior furniture
    detail neither surfaces itself nor lends its outline a pair mate."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    runs = merge_runs(thin_segs, p["off_tol"], p["gap_tol"])
    # coverage walls are merged with gap_tol=0: bridging wall gaps here would mark thin
    # ink INSIDE a wall gap as "already covered" -- suppressing the module's own headline
    # sliding-door-in-gap case. Only truly contiguous collinear wall ink may suppress.
    wall_runs = merge_runs([s for s in wall_segs if _valid_seg(s)], p["off_tol"], gap_tol=0.0)
    n_furn = n_short = n_cov = 0
    kept = []
    for r in runs:
        if r["length"] < p["min_len"]:
            n_short += 1
            continue
        if covered_by_walls(r, wall_runs, p["covered_tol"]) >= p["covered_frac"]:
            n_cov += 1
            continue
        if furn_rects and inside_footprint(r, furn_rects):
            n_furn += 1
            continue
        kept.append(r)
    cands = []
    for i, r in enumerate(kept):
        mate = find_pair(i, kept, p["pair_gap"], p["pair_overlap"])
        ends = ends_near_walls(r, wall_segs, p["end_tol"])
        score = (2 if mate is not None else 0) + ends + (1 if r["length"] >= 1000 else 0)
        if score < 2:
            continue
        (ax, ay), (bx, by) = run_endpoints(r)
        cands.append({
            "axis": r["axis"], "c": r["c"], "span": [r["lo"], r["hi"]],
            "length_mm": r["length"], "score": score,
            "tier": "strong" if score >= 3 else "weak",
            "evidence": {"pair_with_c": kept[mate]["c"] if mate is not None else None,
                         "ends_near_wall": ends, "pieces": r["pieces"],
                         "coverage": r["coverage"]},
            "confirms_manual_patch": matches_manual(r, manual_segs, p["covered_tol"]),
            "segments": [[[round(ax, 1), round(ay, 1)], [round(bx, 1), round(by, 1)]]],
        })
    cands.sort(key=lambda c: (-c["score"], -c["length_mm"]))
    stats = {"thin_segments": len(thin_segs), "runs": len(runs),
             "runs_kept": len(kept), "candidates": len(cands),
             "dropped_short": n_short, "dropped_wall_covered": n_cov,
             "suppressed_inside_furniture": n_furn,
             "dropped_below_score": len(kept) - len(cands)}
    return cands, stats


# ---- PDF side (mirrors pdf_extract_walls.extract, thin gate instead of thick) ---------
def extract_thin(pdf, page, scale, x0, y0, min_width=THIN_MIN_PT, max_width=0.6):
    import fitz    # lazy: pure helpers above stay importable without PyMuPDF
    doc = fitz.open(pdf)
    p = doc[page]
    m = p.rotation_matrix

    def seglist(it):
        if it[0] == "l":
            return [(it[1], it[2])]
        if it[0] == "re":
            r = it[1]
            return [((r.x0, r.y0), (r.x1, r.y0)), ((r.x1, r.y0), (r.x1, r.y1)),
                    ((r.x1, r.y1), (r.x0, r.y1)), ((r.x0, r.y1), (r.x0, r.y0))]
        if it[0] == "qu":
            q = it[1]
            return [(q.ul, q.ur), (q.ur, q.lr), (q.lr, q.ll), (q.ll, q.ul)]
        return []

    thin = []
    for d in p.get_drawings():
        col, w = d.get("color"), d.get("width") or 0
        # dark like a wall (same colour gate) but BELOW the wall width gate
        if not is_wall_stroke(col, w, min_width=min_width) or w >= max_width:
            continue
        for it in d["items"]:
            for a, b in seglist(it):
                q1, q2 = fitz.Point(a) * m, fitz.Point(b) * m
                (x1, y1) = map_pt(q1.x, q1.y, scale, x0, y0)
                (x2, y2) = map_pt(q2.x, q2.y, scale, x0, y0)
                if keep_segment(x1, y1, x2, y2, min_len=40.0):
                    thin.append([[round(x1, 1), round(y1, 1)], [round(x2, 1), round(y2, 1)]])
    return thin


def render_candidates_overlay(pdf, page, calib, cands, out_png, dpi=200):
    """Paint every PROMOTED candidate (score >= 2) over the TRUE sheet raster so the
    owner SCANS a picture instead of hunting through a 300-line list (same extent math
    as raster_overlay, so the frames can never disagree). Runs dropped below the score
    bar are NOT painted -- they are counted in stats.dropped_below_score, so their
    absence is a reported number, not a silent one. Colour = evidence class:
      GREEN   re-derives an existing owner patch (machine agrees with a past sign)
      MAGENTA strong candidate (structural evidence: pair/contact/length)
      CYAN    weak candidate (some evidence -- scan-worthy, lower priority)"""
    import fitz
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    scale, ox, oy = calib
    doc = fitz.open(pdf)
    p = doc[page]
    pix = p.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    zoom = dpi / 72.0
    wpt, hpt = pix.width / zoom, pix.height / zoom
    ext = [(0 - ox) * scale, (wpt - ox) * scale, (oy - hpt) * scale, (oy - 0) * scale]
    fig, ax = plt.subplots(figsize=(pix.width / dpi * 1.1, pix.height / dpi * 1.1))
    ax.imshow(img, extent=ext, origin="upper", aspect="equal", zorder=0)
    n = {"confirm": 0, "strong": 0, "weak": 0}
    for c in cands:
        (x1, y1), (x2, y2) = c["segments"][0]
        if c["confirms_manual_patch"]:
            col, lw, key = "#00a020", 2.2, "confirm"
        elif c["tier"] == "strong":
            col, lw, key = "#d000d0", 1.6, "strong"
        else:
            col, lw, key = "#00a0d0", 1.1, "weak"
        n[key] += 1
        ax.plot([x1, x2], [y1, y2], color=col, lw=lw, alpha=0.85, zorder=3,
                solid_capstyle="butt")
    ax.set_title(f"glazing/thin-wall CANDIDATES -- owner review, nothing auto-injected | "
                 f"GREEN confirms owner patch ({n['confirm']})  "
                 f"MAGENTA strong ({n['strong']})  CYAN weak ({n['weak']})", fontsize=9)
    ax.set_xlabel("mm east")
    ax.set_ylabel("mm north")
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png


def _furniture_rects(man_path):
    """Axis-aligned mm bboxes of every piece the manifest places (builtins, loose items,
    subroom fixtures), via the gate's own footprint math. These are the manifest's OWN
    placements -- the same rects the placement gate checks WHEN it runs, but reading them
    here asserts nothing about whether that gate passed; suppression only means 'the
    manifest claims furniture here', which is exactly the strength the docstring claims."""
    from placement_gate import footprint          # lazy: pure helpers stay standalone
    from raster_overlay import pieces, _resolve   # same manifest walk as the overlay
    man_dir = os.path.dirname(os.path.abspath(man_path))
    man = json.load(open(man_path, encoding="utf-8"))
    rects = []
    for f in man.get("furnish", []):
        spec = json.load(open(_resolve(f["spec"], man_dir), encoding="utf-8"))
        off = tuple(f.get("offset_mm", (0, 0)))
        for _group, it in pieces(spec):
            try:
                rects.append(footprint(it, off))
            except (KeyError, TypeError):
                continue                          # unplaceable rows can't suppress anything
    return rects


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    pdf, walls_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    manifest = sys.argv[4] if len(sys.argv) > 4 else None
    meta = json.load(open(walls_path, encoding="utf-8"))
    scale = meta["scale_mm_per_pt"]
    x0, y0 = meta["origin_pt"]
    page = meta["page"]
    src = os.path.basename(str(meta.get("source_pdf", ""))).replace("\\", "/").split("/")[-1]
    if src and os.path.basename(pdf) != src:
        print(f"WARNING: walls JSON was calibrated on '{src}', got '{os.path.basename(pdf)}' "
              f"-- coordinates are only valid if this is the same drawing")
    manual = (meta.get("manual_additions") or {}).get("segments") or []

    def _key(s):
        # undirected + rounded: manual segs are owner-typed ints, extracted segs are
        # 0.1-rounded floats; re-injected copies match exactly today, but a future
        # normalisation pass must not silently defeat the subtraction
        return tuple(sorted(((round(s[0][0], 1), round(s[0][1], 1)),
                             (round(s[1][0], 1), round(s[1][1], 1)))))
    manual_keys = {_key(s) for s in manual if _valid_seg(s)}
    # score against RAW extracted walls only: the tool must re-derive owner patches
    # from ink, not be handed them via the wall set
    walls = [s for s in meta.get("segments", [])
             if _valid_seg(s) and _key(s) not in manual_keys]
    thin = extract_thin(pdf, page, scale, x0, y0)
    rects = _furniture_rects(manifest) if manifest else ()
    cands, stats = promote(thin, walls, manual_segs=manual, furn_rects=rects)
    strong = [c for c in cands if c["tier"] == "strong"]
    doc_out = {
        "schema": "interior-ai/glazing-candidates@0.1",
        "source_pdf": os.path.basename(pdf), "page": page,
        "walls_json": os.path.basename(walls_path),
        "scale_mm_per_pt": scale, "origin_pt": [x0, y0],
        "params": {k: v for k, v in DEFAULTS.items()},
        "stats": stats,
        "candidates": cands,
        # a TEMPLATE, deliberately EMPTY: the owner copies the specific candidates they
        # confirm (each candidate carries its own `segments`) into their own record and
        # replaces `by` with a real signature. Shipping it pre-filled would make a bulk
        # unsigned paste one keystroke away -- and merge_carried refuses to re-inject
        # any record whose `by` still says OWNER-CONFIRM-PENDING, so even that paste is
        # machine-inert. MERGE into an existing manual_additions record; never replace
        # one (the walls JSON holds ONE record -- replacing it destroys the owner's
        # earlier signed patches).
        "manual_additions_stub": {
            "date": time.strftime("%Y-%m-%d"),
            "by": "OWNER-CONFIRM-PENDING (unsigned template; merge_carried refuses to "
                  "re-inject until this names the owner)",
            "reason": "copy the confirmed candidates' segments in here, one by one; "
                      "MERGE with any existing manual_additions -- do not replace it",
            "segments": [],
        },
    }
    tmp = out + ".tmp"
    json.dump(doc_out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, out)
    overlay = os.path.splitext(out)[0] + ".png"
    render_candidates_overlay(pdf, page, (scale, x0, y0), cands, overlay)
    n_confirm = sum(1 for c in cands if c["confirms_manual_patch"])
    print(f"wrote {overlay} (scan artifact: green=confirms-patch, magenta=strong, cyan=weak)")
    print(f"wrote {out}: {len(cands)} candidates ({len(strong)} strong) from "
          f"{stats['thin_segments']} thin segments / {stats['runs']} runs; "
          f"{n_confirm} re-derive existing owner patches; "
          f"{stats['suppressed_inside_furniture']} suppressed inside furniture footprints; "
          f"{stats['dropped_below_score']} low-score runs dropped (not silent: counted here)")
    for c in cands[:10]:
        seg = c["segments"][0]
        mark = " CONFIRMS-PATCH" if c["confirms_manual_patch"] else ""
        print(f"  [{c['tier']:6}] score {c['score']} {c['axis']}@{c['c']:>8} "
              f"span {c['span'][0]:>8}..{c['span'][1]:<8} len {c['length_mm']:>7} "
              f"seg {seg}{mark}")


if __name__ == "__main__":
    main()
