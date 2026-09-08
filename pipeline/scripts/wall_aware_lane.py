"""
wall_aware_lane.py -- WRAPPER lane: wall-aware cluster splitting, measured before/after.

WHY: the full-corpus F2 run (qa/reports/structured3d-synth-f2-2026-07-09.md, commit 4c4bf42)
measured the reader's ceiling as FUSION -- 10/12 forensically-inspected wrong-facing cases
were fused-neighbour strips, detection recall sits at ~10.7% (47,437/444,405), and every
fused cluster that spans a wall drags every GT element inside it below IoU 0.5. This lane
asks ONE question: how much of that ceiling is CROSS-WALL fusion? It splits exactly there
and re-scores, so the delta is causally attributable to walls and nothing else.

MECHANISM (wrapper -- svg_plan_reader.py is NOT edited; it is owned by a parallel session):
the reader's own morphology is rasterize -> binary CLOSE -> connected components -> size
screen (plan_cluster.cluster_segments). Fusion happens at the CLOSE step: two symbols
closer than ~2*CLOSE_MM bridge into one component. A wall between them cannot be un-bridged
by masking ink (walls carry no ink in the oriented synth SVG, and cluster_segments applies
masks BEFORE closing), so this lane re-runs the SAME morphology with the closing DECOMPOSED
into its two halves (scipy's binary_closing IS erosion(dilation(x)) with these defaults)
and the wall barrier applied in between:

    dil    = binary_dilation(ink, r)          # the reader's own bridge step, first half
    cut    = dilate(rasterize(walls)) & ~ink  # wall pixels that carry NO real ink
    dil   &= ~cut                             # phantom mass is severed AT the wall...
    closed = binary_erosion(dil, r) | ink     # ...so erosion eats the stranded far-side
                                              #    mass back, and real ink is restored

The barrier cuts BRIDGES, never ink: a pixel the pen actually drew is never removed, so
an element genuinely inked across a wall (curtains, windows, a wardrobe bbox overlapping
the wall band -- common in S3D) stays whole, while the closing's phantom bridge between
two rooms' separate symbols is severed. Two pinned lessons live in this exact shape:
  - cutting real ink (first probe) shredded wall-hugging elements below the size screen
    and whole scenes LOST matches;
  - cutting AFTER the closing (second iteration) left the bridge mass beyond the ~3px
    band alive, so ink poking a few mm past the wall centreline reconnected the rooms
    through the hole in the band (adversarial review, reproduced) -- severing mid-closing
    lets the erosion half eat the stranded mass back at any overlap depth.
KNOWN, COUNTED residuals: a bridge legitimately ROUTES AROUND a wall trace that does not
span it (door gaps, junction-broken/adapter-skipped traces) -- no wall there, no cut; and
fusion carried by REAL ink continuity across a wall is kept by design and counted per
scene as residual_cross_region (components spanning >=2 wall-partitioned regions).

Everything else (raster res, zone padding, close radius, size screen, sort order, curve/
fill flags) mirrors read_sheet/cluster_segments exactly, pinned by a zero-walls
equivalence test: with wall_lines=[] this lane's elements are GEOMETRY-IDENTICAL to the
unedited reader's (x/y/w/d/curve/fill and order; ids are intentionally w### vs the
reader's c### so a lane pred can never be mistaken for a reader pred). The primitives
(_rasterize, _screen_component) are IMPORTED from plan_cluster,
never re-implemented; only the ~20-line orchestration is mirrored (drift breaks the pin
test loudly).

A second, previously invisible recovery: cluster_segments DROPS components larger than
3.6 m on both axes as 'merged_blob' -- whole-room fusions where every GT element inside
scored as a miss. The barrier cuts those at walls; per-room parts re-enter the size screen
and many become scoreable elements again.

TIER -- ORACLE-WALLS (disclose wherever quoted): wall geometry comes from gt['wall_lines']
(the answer-key side), same tier as the reader's own `walls oracle` lane and the F2
wall-prior (precedents qa/reports/floorplancad-oracle-walls-2026-07-07.md,
f2-facing-convention-validated-2026-07-09.md). The number is the CEILING a real
wall-detector (pdf_extract_walls on production sheets) can unlock -- NEVER the blind
headline. Walls carry no kind/rot/indoor: identity and facing stay unleaked; the only
information consumed is WHERE walls are.

WHAT IS MEASURED (before vs after, same scene, same ink, same enrichment):
  detection   recall/precision/matched -- the 10.7% headline under test
  F2 facing   f2_facing_lane's own visual post-pass (oriented back-strips ->
              enrich_pred_with_facing) run UNCHANGED on both preds; beds-excluded
              headline via the same _facing_nobed; the aggregate delta is COMPOSITION-
              DRIVEN (new pairs are strip-carrying by construction), so a per-pair
              transition decomposition of the before-matched subset is always printed
              beside it; the blind baseline is MEASURED per run on the un-enriched
              preds, never asserted
  F3 indoor   score_pair's F3 on the matched set (pred stays indoor-silent; the delta
              is composition: WHICH pairs exist)
  secondary   the wall-prior ORACLE rot band (double-oracle: split + prior), disclosed

    python wall_aware_lane.py --score <gt-dir> <out-dir> [limit N] [--no-oracle]
"""
import copy
import glob
import json
import os
import sys
import time

import numpy as np
import scipy.ndimage as ndi

import benchmark_reader as B
import f2_facing_lane as F2L
import plan_cluster as PC
import svg_plan_reader as R

LANE_VERSION = "wall_aware_lane v1.0"

# Dilation of the rasterized wall line before it is applied as a barrier. A 1px Agg line
# can leak 8-connected components through its diagonal steps (two off-line pixels touching
# corner-to-corner across the step); one dilation makes the line >=3px and leak-proof.
# Real ink is exempted from the cut (bridge-only barrier), so the dilation costs nothing
# on elements that touch or overlap walls.
BARRIER_DILATE_PX = 1


# ---- the wall-aware morphology -----------------------------------------------------------
def wall_barrier_elements(segs_mm, csegs_mm, wall_lines, close_mm=R.CLOSE_MM):
    """Reader-equivalent clustering with gt wall_lines as a post-close connectivity barrier.
    segs_mm/csegs_mm = read_ink output already scaled to mm (the same lists read_sheet
    clusters). Returns (elements, stats); with wall_lines empty/None the elements are
    GEOMETRY-IDENTICAL to the unedited reader's -- x/y/w/d/curve/fill and order, pinned
    by test_zero_walls_is_reader_equivalent; ids deliberately differ (w### vs c###).

    Zone padding, effective res, close radius, component screen, sort order: all mirror
    svg_plan_reader.read_sheet + plan_cluster.cluster_segments line-for-line. Primitives
    are imported, not copied."""
    stats = {"n_wall_segs": len(wall_lines or []), "wall_px": 0, "res": None,
             "kept": 0, "dropped_thin": 0, "dropped_blob": 0, "dropped_speckle": 0,
             "n_regions": 0, "residual_cross_region": 0}
    if not segs_mm:
        return [], stats
    # zone + effective res: svg_plan_reader.read_sheet verbatim
    xs = [p[0] for seg in segs_mm for p in seg]
    ys = [p[1] for seg in segs_mm for p in seg]
    zone = (min(xs) - R.ZONE_PAD_MM, min(ys) - R.ZONE_PAD_MM,
            max(xs) + R.ZONE_PAD_MM, max(ys) + R.ZONE_PAD_MM)
    extent = max(zone[2] - zone[0], zone[3] - zone[1])
    res = max(R.BASE_RES_MM, extent / R.MAX_RASTER_PX)
    stats["res"] = res
    X0, Y0, X1, Y1 = zone
    Wc = int((X1 - X0) / res)
    Hc = int((Y1 - Y0) / res)
    # raster + close: plan_cluster.cluster_segments verbatim (no masks in this lane --
    # read_sheet passes none either)
    ink = PC._rasterize(segs_mm, zone, Wc, Hc)
    curveink = PC._rasterize(csegs_mm, zone, Wc, Hc)
    r = max(1, int(round(close_mm / res)))
    st = ndi.generate_binary_structure(2, 2)
    wsegs = [[(float(w["x1"]), float(w["y1"])), (float(w["x2"]), float(w["y2"]))]
             for w in (wall_lines or [])]
    wsegs = [s for s in wsegs if s[0] != s[1]]
    regions = None
    if wsegs:
        barrier = PC._rasterize(wsegs, zone, Wc, Hc)
        if barrier.shape != ink.shape:         # same Agg args must yield the same canvas
            raise RuntimeError(f"barrier raster {barrier.shape} != ink raster "
                               f"{ink.shape} -- refusing a misaligned barrier")
        barrier = ndi.binary_dilation(barrier, structure=st,
                                      iterations=BARRIER_DILATE_PX)
        # BRIDGE-ONLY cut, applied MID-closing: sever pixels the pen never drew.
        #  - cutting real ink shredded wall-hugging elements below the size screen
        #    (probe scenes LOST up to half their matches);
        #  - cutting AFTER the closing left bridge mass beyond the ~3px band alive, and
        #    ink poking past the wall centreline reconnected the rooms through the hole
        #    (adversarial review, reproduced). Severing the DILATED mass instead lets the
        #    erosion half eat the stranded far-side bridge back at any overlap depth.
        # scipy's binary_closing(x, st, r) IS binary_erosion(binary_dilation(x, st, r),
        # st, r) at these defaults, so the no-wall pin stays geometry-identical.
        cut = barrier & ~ink
        stats["wall_px"] = int(cut.sum())
        dil = ndi.binary_dilation(ink, structure=st, iterations=r)
        dil &= ~cut
        closed = ndi.binary_erosion(dil, structure=st, iterations=r)
        # erosion eats back from the new cut faces too -- restore every real-ink pixel
        # (a no-op away from walls: closing is extensive over the padded zone)
        closed |= ink
        regions, n_regions = ndi.label(~barrier, structure=st)
        stats["n_regions"] = int(n_regions)
    else:
        closed = ndi.binary_closing(ink, structure=st, iterations=r)
    # components + screen: plan_cluster.cluster_segments lines 118-149, mirrored (the
    # loop is not importable separately; the screen itself IS imported)
    lab, n = ndi.label(closed, structure=st)

    def px2mm(col, row):
        return X0 + col * res, Y1 - row * res          # row0 = top = Y1

    comps = []
    for i in range(1, n + 1):
        ys_, xs_ = np.where(lab == i)
        area_px = len(xs_)
        if area_px < 25:
            stats["dropped_speckle"] += 1
            continue
        x_lo, _ = px2mm(xs_.min(), 0)
        x_hi, _ = px2mm(xs_.max(), 0)
        _, y_hi = px2mm(0, ys_.min())
        _, y_lo = px2mm(0, ys_.max())
        wmm, dmm = x_hi - x_lo, y_hi - y_lo
        keep, reason = PC._screen_component(wmm, dmm)
        if not keep:
            stats["dropped_thin" if reason == "thin" else "dropped_blob"] += 1
            continue
        reg = (lab == i)
        curvy = int((reg & curveink).sum())
        fill = area_px / max((xs_.max() - xs_.min() + 1) * (ys_.max() - ys_.min() + 1), 1)
        comps.append({"x": round(x_lo), "y": round(y_lo),
                      "w": round(wmm), "d": round(dmm),
                      "curve": curvy > 30, "fill": round(fill, 2), "_lab": i})
    if regions is not None and comps:
        # honest-residual counter: kept components whose pixels span >=2 wall-partitioned
        # regions = cross-wall continuity the barrier deliberately kept (real ink across
        # a wall) -- COUNTED, never asserted away. Partial/door-gap wall traces leave
        # ~barrier connected, so route-around fusions are structurally invisible to this
        # counter (disclosed in the report prose).
        kept_labs = {c["_lab"] for c in comps}
        m = closed & (regions > 0)
        codes = (lab[m].astype(np.int64) * (int(stats["n_regions"]) + 1)
                 + regions[m].astype(np.int64))
        labs_of_pairs = np.unique(codes) // (int(stats["n_regions"]) + 1)
        labs, counts = np.unique(labs_of_pairs, return_counts=True)
        multi = {int(l) for l, c in zip(labs, counts) if c >= 2}
        stats["residual_cross_region"] = len(kept_labs & multi)
    for c in comps:
        c.pop("_lab")
    comps.sort(key=lambda c: (-c["w"] * c["d"]))
    stats["kept"] = len(comps)
    elements = [{"id": f"w{k:03d}", **c} for k, c in enumerate(comps)]
    return elements, stats


def wall_aware_pred(pred, segs_mm, csegs_mm, wall_lines):
    """A COPY of the reader's pred whose elements are re-derived with the wall barrier.
    Openings/meta are inherited (F4 is identical on both sides by construction); the meta
    gains a wall_aware block so the pred can never be mistaken for a blind read."""
    elements, stats = wall_barrier_elements(segs_mm, csegs_mm, wall_lines)
    out = copy.deepcopy(pred)
    out["elements"] = elements
    out["meta"]["wall_aware"] = {"tier": "ORACLE-WALLS", "lane": LANE_VERSION, **stats}
    return out, stats


# ---- per-pair transition decomposition -----------------------------------------------------
def facing_transitions(before_f, after_f):
    """Join two score_facing views by GT element id: what happened to each BEFORE-matched
    facing pair after the barrier? The aggregate pp-delta compares two different
    populations (new pairs on this closed-loop corpus are strip-carrying by construction,
    i.e. near-guaranteed hits), so a regression on the common subset can hide under a
    positive delta unless this decomposition is printed next to it (adversarial review
    finding, 2026-07-10 -- the flattering-scorer hole recurring in per-lane form)."""
    b = {gid: bucket for gid, _d, bucket in (before_f.get("per_element") or [])}
    a = {gid: bucket for gid, _d, bucket in (after_f.get("per_element") or [])}
    changed = {}
    unchanged = left = 0
    for gid, bb in b.items():
        ab = a.get(gid)
        if ab is None:
            left += 1
            changed[f"{bb}->left_matched_set"] = changed.get(f"{bb}->left_matched_set", 0) + 1
        elif ab == bb:
            unchanged += 1
        else:
            changed[f"{bb}->{ab}"] = changed.get(f"{bb}->{ab}", 0) + 1
    new_buckets = {}
    for gid, ab in a.items():
        if gid not in b:
            new_buckets[ab] = new_buckets.get(ab, 0) + 1
    return {"before_n": len(b), "unchanged": unchanged, "left_matched_set": left,
            "changed": changed, "new": new_buckets}


# ---- one scene, before + after -----------------------------------------------------------
def score_scene(gt_doc, tmp_dir, oracle=True):
    """One scene through the f2 lane twice: the unedited reader (before) and the
    wall-barrier re-cluster (after), sharing the same oriented SVG, ink and enrichment.
    Returns a row with card_before/card_after (full score_pair cards) + the beds-excluded
    F2 views + split stats."""
    svg, sstats = F2L.oriented_svg(gt_doc)
    p = os.path.join(tmp_dir, "oriented.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    pred_b = R.read_sheet(p, 1.0)
    ink = R.read_ink(p)                       # scale 1.0 -> svg units ARE mm
    segs, csegs = ink["segs"], ink["curve_segs"]
    pred_a, wstats = wall_aware_pred(pred_b, segs, csegs, gt_doc.get("wall_lines"))

    pred_vb, emit_b = F2L.enrich_pred_with_facing(pred_b, segs)
    pred_va, emit_a = F2L.enrich_pred_with_facing(pred_a, segs)
    nobed_b = F2L._facing_nobed(gt_doc, pred_vb)
    nobed_a = F2L._facing_nobed(gt_doc, pred_va)
    row = {"card_before": B.score_pair(gt_doc, pred_vb),
           "card_after": B.score_pair(gt_doc, pred_va),
           "f2_nobed_before": nobed_b,
           "f2_nobed_after": nobed_a,
           "f2_transitions": facing_transitions(nobed_b, nobed_a),
           # MEASURED blind baseline (never asserted): the un-enriched preds through the
           # same scorer -- any rot here means rot without ink evidence, a lane defect
           "f2_blind_before": B.score_pair(gt_doc, pred_b)["F2_facing"],
           "f2_blind_after": B.score_pair(gt_doc, pred_a)["F2_facing"],
           "strips": sstats, "emit_before": emit_b, "emit_after": emit_a,
           "wall_aware": wstats}
    if oracle:
        wl = gt_doc.get("wall_lines")
        pred_ob, _ = F2L.wall_prior_pred(pred_b, wl)
        pred_oa, _ = F2L.wall_prior_pred(pred_a, wl)
        row["f2_oracle_nobed_before"] = F2L._facing_nobed(gt_doc, pred_ob)
        row["f2_oracle_nobed_after"] = F2L._facing_nobed(gt_doc, pred_oa)
    return row


# ---- corpus run ---------------------------------------------------------------------------
def score_corpus(gt_dir, out_dir, limit=None, oracle=True):
    """Every *.gt.json through score_scene; cards.jsonl streamed, report.md at the end.
    One bad scene costs one row, never the run (mirrors f2_facing_lane.score_corpus)."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    rows, skipped = [], {"error": 0, "units": 0, "no_walls": 0}
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as out, \
            tempfile.TemporaryDirectory() as td:
        for k, gfp in enumerate(gt_files):
            base = os.path.basename(gfp)[:-len(".gt.json")]
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    out.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                if not gt.get("wall_lines"):
                    # scored anyway (delta is 0 by construction) but COUNTED: a corpus
                    # where many scenes carry no walls must not quietly read as "no gain"
                    skipped["no_walls"] += 1
                row = {"scene": base, **score_scene(gt, td, oracle=oracle)}
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as e:
                skipped["error"] += 1
                out.write(json.dumps({"scene": base, "skipped": "error",
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                out.flush()
                if (k + 1) % 100 == 0:
                    print(f"  {k + 1}/{len(gt_files)}  scored={len(rows)}  "
                          f"({time.time() - t0:.0f}s)", flush=True)
    report = render_report(rows, skipped, len(gt_files), time.time() - t0, oracle=oracle)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return rows, skipped


def _pct(v):
    return "n/a" if v is None else f"{100.0 * v:.1f}%"


def _delta_pp(a, b):
    if a is None or b is None:
        return "n/a"
    return f"{100.0 * (b - a):+.1f}pp"


def render_report(rows, skipped, n_total, secs, oracle=True):
    if not rows:
        return "# wall_aware_lane\n\nno gt scored -- " + json.dumps(skipped)
    agg_b = B.aggregate([r["card_before"] for r in rows])
    agg_a = B.aggregate([r["card_after"] for r in rows])
    det_b, det_a = agg_b["detection"], agg_a["detection"]
    f3_b, f3_a = agg_b["F3_indoor"], agg_a["F3_indoor"]
    nb_b = F2L._sum_facing([r["f2_nobed_before"] for r in rows])
    nb_a = F2L._sum_facing([r["f2_nobed_after"] for r in rows])
    bed_b = F2L._sum_facing([r["card_before"]["F2_facing"] for r in rows])
    bed_a = F2L._sum_facing([r["card_after"]["F2_facing"] for r in rows])
    blind_b = F2L._sum_facing([r.get("f2_blind_before") for r in rows])
    blind_a = F2L._sum_facing([r.get("f2_blind_after") for r in rows])
    trans = {"before_n": 0, "unchanged": 0, "left_matched_set": 0, "changed": {}, "new": {}}
    for r in rows:
        t = r.get("f2_transitions") or {}
        trans["before_n"] += t.get("before_n", 0)
        trans["unchanged"] += t.get("unchanged", 0)
        trans["left_matched_set"] += t.get("left_matched_set", 0)
        for k, v in (t.get("changed") or {}).items():
            trans["changed"][k] = trans["changed"].get(k, 0) + v
        for k, v in (t.get("new") or {}).items():
            trans["new"][k] = trans["new"].get(k, 0) + v
    common_changed = trans["before_n"] - trans["unchanged"]
    # a DOWNGRADE is a transition whose destination ranks worse than its source (leaving
    # the matched set is always a downgrade); upgrades (e.g. unreported->exact de-spoofs)
    # must not trip the banner -- a false "REGRESSIONS PRESENT" is still a false claim
    _RANK = {"exact": 3, "cardinal": 2, "unreported": 1, "wrong": 0, "flipped": 0,
             "left_matched_set": -1}
    downgrades = sum(v for k, v in trans["changed"].items()
                     if _RANK.get(k.split("->")[1], -1) < _RANK.get(k.split("->")[0], 3))
    n_split_up = sum(1 for r in rows if r["card_after"]["detection"]["n_pred"]
                     > r["card_before"]["detection"]["n_pred"])
    n_split_down = sum(1 for r in rows if r["card_after"]["detection"]["n_pred"]
                       < r["card_before"]["detection"]["n_pred"])
    blobs_after = sum(r["wall_aware"]["dropped_blob"] for r in rows)
    walls_fed = sum(r["wall_aware"]["n_wall_segs"] for r in rows)
    residual = sum(r["wall_aware"].get("residual_cross_region", 0) for r in rows)
    L = [
        "# wall_aware_lane -- cross-wall fusion split, before/after on the SAME ink", "",
        "**TIER: ORACLE-WALLS** -- the barrier consumes gt['wall_lines'] (answer-key side).",
        "This is the CEILING a real wall-detector can unlock, NEVER the blind headline",
        "(precedents: floorplancad-oracle-walls-2026-07-07.md, svg_plan_reader `walls "
        "oracle`, f2 wall-prior). Walls leak position only: no kind/rot/indoor.", "",
        f"- {LANE_VERSION}; f2 lane {F2L.LANE_VERSION} (unedited); reader {R.READER_VERSION} "
        f"(UNEDITED, wrapper only); synthesizer {F2L.S.SYNTH_VERSION}",
        f"- scenes: {len(rows)} scored / {n_total} (skipped {json.dumps(skipped)}); "
        f"wall-clock {secs:.0f}s; wall segs fed {walls_fed}",
        f"- scenes where the barrier changed the cluster count: +{n_split_up} / "
        f"-{n_split_down} (down = split parts fell under the size screen)", "",
        "## detection (the fusion-ceiling headline)",
        "| metric | before (unedited reader) | after (wall barrier) | delta |",
        "|---|---|---|---|",
        f"| recall | {_pct(det_b['recall'])} | {_pct(det_a['recall'])} | "
        f"{_delta_pp(det_b['recall'], det_a['recall'])} |",
        f"| precision | {_pct(det_b['precision'])} | {_pct(det_a['precision'])} | "
        f"{_delta_pp(det_b['precision'], det_a['precision'])} |",
        f"| matched | {det_b['matched']} | {det_a['matched']} | "
        f"{det_a['matched'] - det_b['matched']:+d} |",
        f"| n_pred | {det_b['n_pred']} | {det_a['n_pred']} | "
        f"{det_a['n_pred'] - det_b['n_pred']:+d} |",
        f"| merged_blob still dropped (after) | | {blobs_after} | |",
        f"| kept components still spanning >=2 wall-partitioned regions "
        f"(real-ink crossers, honest residual) | | {residual} | |", "",
        "## F2 facing -- visual lane, beds excluded (closed-loop ink recovery)",
        "| metric | before | after | delta |",
        "|---|---|---|---|",
        f"| cardinal_correct | {_pct(nb_b['cardinal_correct'])} | "
        f"{_pct(nb_a['cardinal_correct'])} | "
        f"{_delta_pp(nb_b['cardinal_correct'], nb_a['cardinal_correct'])} "
        f"(COMPOSITION-DRIVEN -- see decomposition) |",
        f"| n (matched facing pairs) | {nb_b['n']} | {nb_a['n']} | "
        f"{nb_a['n'] - nb_b['n']:+d} |",
        f"| hits | {nb_b['hits']} | {nb_a['hits']} | {nb_a['hits'] - nb_b['hits']:+d} |",
        f"| buckets before | {json.dumps(nb_b['buckets'])} | | |",
        f"| buckets after | | {json.dumps(nb_a['buckets'])} | |",
        "",
        "### per-pair decomposition (the delta above compares two POPULATIONS; new pairs "
        "on this closed-loop corpus are strip-carrying by construction, so the honest "
        "question is what happened to the pairs matched BEFORE)",
        f"- of {trans['before_n']} before-matched facing pairs: {trans['unchanged']} "
        f"unchanged-bucket, {common_changed} changed or left "
        f"({json.dumps(trans['changed']) if trans['changed'] else 'none'})"
        + (f" -- **{downgrades} COMMON-SUBSET DOWNGRADE(S) PRESENT, inspect before "
           f"quoting the delta**" if downgrades else
           " -- zero common-subset downgrades"
           + (" (all churn is upgrades)" if common_changed else "")),
        f"- newly matched after the barrier: {sum(trans['new'].values())} pairs, buckets "
        f"{json.dumps(trans['new'])}",
        "",
        f"- beds included (contaminated -- S3D bed rot = length axis): "
        f"{_pct(bed_b['cardinal_correct'])} (n={bed_b['n']}) -> "
        f"{_pct(bed_a['cardinal_correct'])} (n={bed_a['n']})",
        f"- blind baseline (MEASURED on the un-enriched preds, never asserted): "
        f"cardinal_correct {_pct(blind_b['cardinal_correct'])} on n={blind_b['n']} -> "
        f"{_pct(blind_a['cardinal_correct'])} on n={blind_a['n']}; buckets after "
        f"{json.dumps(blind_a['buckets'])} (anything but unreported = rot without ink "
        f"evidence = lane defect)",
        "",
        "## F3 indoor (matched-set composition; pred stays indoor-silent)",
        f"- accuracy {_pct(f3_b['accuracy'])} (n={f3_b['n']}) -> "
        f"{_pct(f3_a['accuracy'])} (n={f3_a['n']}) "
        f"[{_delta_pp(f3_b['accuracy'], f3_a['accuracy'])}]",
    ]
    if oracle and any("f2_oracle_nobed_before" in r for r in rows):
        ob = F2L._sum_facing([r.get("f2_oracle_nobed_before") for r in rows])
        oa = F2L._sum_facing([r.get("f2_oracle_nobed_after") for r in rows])
        L += [
            "",
            "## secondary -- wall-prior rot band (DOUBLE ORACLE: split + prior, disclosed)",
            f"- beds excluded: {_pct(ob['cardinal_correct'])} (n={ob['n']}) -> "
            f"{_pct(oa['cardinal_correct'])} (n={oa['n']}) "
            f"[{_delta_pp(ob['cardinal_correct'], oa['cardinal_correct'])}]",
        ]
    L += [
        "", "## what this number IS (and is not)",
        "- ORACLE-WALLS: gt wall geometry, disclosed above. The blind headline remains "
        "the committed f2 lane report; this lane bounds what a wall-DETECTOR is worth.",
        "- CLOSED LOOP: same oriented back-strip synth as f2_facing_lane -- ink-recovery "
        "fidelity, not generalization to real-world symbol ink.",
        "- BRIDGE-ONLY: the barrier severs pixels the closing added (mid-closing, so a "
        "stranded far-side bridge erodes back), never pixels the pen drew -- an element "
        "genuinely inked across a wall stays whole (pinned) and is COUNTED in the "
        "residual row, not asserted away.",
        "- RESIDUAL CROSS-WALL FUSION EXISTS where the wall trace does not span the "
        "bridge: door gaps and junction-broken/adapter-skipped traces let the bridge "
        "route AROUND the trace end (pinned, documented) -- those are structurally "
        "invisible to the residual counter, so the recall gap after this lane is "
        "'not cross-wall fusion' only up to partial-trace route-arounds.",
        "- within-room fusion (flush neighbours, sub-object granularity) is UNTOUCHED by "
        "design.",
        f"", f"engines: {LANE_VERSION} / {F2L.LANE_VERSION} / {R.READER_VERSION}",
    ]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--score":
        limit, oracle = None, "--no-oracle" not in argv
        rest = [a for a in argv[4:] if a != "--no-oracle"]
        i = 0
        while i < len(rest):
            if rest[i] == "limit" and i + 1 < len(rest) and rest[i + 1].isdigit():
                limit = int(rest[i + 1]); i += 2
            else:
                i += 1
        score_corpus(argv[2], argv[3], limit=limit, oracle=oracle)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
