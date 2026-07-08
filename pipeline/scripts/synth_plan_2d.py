"""
synth_plan_2d.py -- Structured3D gt.json -> an annotation-blind 2D SVG floor plan, so OUR
reader (svg_plan_reader) can be RUN on a synthesized plan and scored for REAL. This closes the
gap the plan-extraction memory named ("reader-scores need a 2D synthesizer"): until now the
Structured3D lane could only run benchmark_reader gt-vs-gt, a SYMMETRIC selftest that cannot
catch an error (a convention flip, an over-emitted flag, all self-match with distance 0). The
3D corpus is the indoor/outdoor ANSWER KEY; this module draws the 2D a reader would see and
runs the reader on it, so F3_indoor becomes a pred!=gt number for the FIRST time on any corpus.

    python synth_plan_2d.py <scene.gt.json> <out.svg> [--walls]
    python synth_plan_2d.py --score <gt-dir> <out-dir> [limit N] [--walls]

THE HONESTY CORE (mirrors svg_plan_reader.read_ink's annotation-blindness): the indoor label is
NEVER drawn. synth_svg reads x/y/w/d geometry ONLY; two gt docs that differ solely in `indoor`
produce a BYTE-IDENTICAL SVG (pinned by test_synth_plan_2d). So F3 measures whether GEOMETRY
alone recovers the room semantics -- it cannot leak the answer key into the reader's input.

WHAT THE F3 NUMBER MEANS (read this before quoting it): svg_plan_reader has NO indoor
classifier -- it emits no `indoor` key, so benchmark_reader scores every matched pred element
as indoor=True (silence = ordinary this-floor-indoor). The resulting F3 accuracy is therefore
the ALWAYS-INDOOR BASELINE: it equals the indoor fraction among matched pairs, and its
`wrong_ids` are exactly the OUTDOOR (balcony/garden) pieces the reader would misclassify. The
value of this module is NOT that baseline number (which the adapter's meta already implies) --
it is that the loop is now WIRED end-to-end: an indoor-inference upgrade to the reader (e.g.
generalising zone_flag beyond the south-facade case) becomes an immediately SCOREABLE pred!=gt
delta over this baseline, on real balcony/garden ground truth.

DETECTION RECALL IS LOW ON THIS CORPUS -- AND THAT IS NOT A SOUNDNESS PASS (adversarially
verified 2026-07-08). F3 scores only on MATCHED pairs, and plan_cluster recovers roughly a
TENTH of the synthesized footprints (~10% recall over the 200-scene sample), because: (a) ~54-
63% of Structured3D 'objects' are sub-150mm decor (cups, books, picture frames) that the reader
screens as thin ink BY DESIGN; (b) boxes >~3.6m on both axes drop as merged_blob; and (c)
furniture drawn within CLOSE_MM (40mm) -- a bed with a flush nightstand, stacked cushions --
MERGES into one cluster whose AABB matches neither GT box, so BOTH pieces leave the F3 set. So
F3 is measured on the DETECTED SUBSET (~1.7k of ~20k indoor-carrying GT). Read render_report's
representativeness line before quoting F3: the matched subset's OUTDOOR fraction is reported
next to the corpus outdoor rate -- on the 200-scene run they are close (~5.6% vs ~4.7%), so the
baseline is NOT optimistically biased against outdoor, but the sample is SMALL and clustered
furniture is under-represented. Raising the scoreable slice (a realistic size-filtered draw +
instance separation) is the clear next slice; the hard detection test remains FloorPlanCAD's
real symbol ink, not these clean rectangles.

WALLS (opt-in, --walls): the synthesized plan can also draw gt['wall_lines'] + glazing as thin
structure lines (a realistic plan). It is OFF by default for the headline F3 lane because a
furniture rect drawn hard against a wall merges into the wall network under plan_cluster's CLOSE
and is then not recovered as its own element -- which would drop detection recall and conflate
'reader can't separate furniture from walls' (a real but SEPARATE morphology problem) with the
F3 measurement. Furniture-only isolates the F3 variable; walls are there for the geometric-indoor
follow-up lane (which needs the enclosure geometry to infer indoor without the label).
"""
import glob
import json
import os
import sys
import time

import benchmark_reader as B
import svg_plan_reader as R

SYNTH_VERSION = "synth_plan_2d v1.0"
PAD_MM = 100.0


def synth_svg(gt_doc, include_walls=False):
    """gt.json document -> an SVG string in mm (scale 1.0), ANNOTATION-BLIND. Furniture elements
    become <rect> footprints (the reader's morphology recovers each AABB); with include_walls,
    gt['wall_lines'] + gt['glazing_lines'] are drawn as thin <line> structure. The indoor/kind
    fields are NEVER read -- only x/y/w/d and wall endpoints reach the drawing."""
    elements = gt_doc.get("elements", []) or []
    walls = (gt_doc.get("wall_lines", []) or []) if include_walls else []
    glaz = (gt_doc.get("glazing_lines", []) or []) if include_walls else []

    xs, ys = [], []
    for e in elements:
        xs += [float(e["x"]), float(e["x"]) + float(e["w"])]
        ys += [float(e["y"]), float(e["y"]) + float(e["d"])]
    for w in walls + glaz:
        xs += [float(w["x1"]), float(w["x2"])]
        ys += [float(w["y1"]), float(w["y2"])]
    if not xs:                                  # an empty plan still emits a valid (empty) SVG
        xs, ys = [0.0, 1.0], [0.0, 1.0]
    minx, miny = min(xs) - PAD_MM, min(ys) - PAD_MM
    vw, vh = (max(xs) - min(xs)) + 2 * PAD_MM, (max(ys) - min(ys)) + 2 * PAD_MM

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="{minx:.1f} {miny:.1f} {vw:.1f} {vh:.1f}">']
    # structure first (drawn under the furniture), then furniture footprints. Order is geometry
    # only -- it never depends on indoor/kind, so the blindness invariant holds.
    for w in walls:
        parts.append(f'<line x1="{float(w["x1"]):.1f}" y1="{float(w["y1"]):.1f}" '
                     f'x2="{float(w["x2"]):.1f}" y2="{float(w["y2"]):.1f}"/>')
    for g in glaz:
        parts.append(f'<line x1="{float(g["x1"]):.1f}" y1="{float(g["y1"]):.1f}" '
                     f'x2="{float(g["x2"]):.1f}" y2="{float(g["y2"]):.1f}"/>')
    for e in elements:
        parts.append(f'<rect x="{float(e["x"]):.1f}" y="{float(e["y"]):.1f}" '
                     f'width="{float(e["w"]):.1f}" height="{float(e["d"]):.1f}"/>')
    parts.append('</svg>')
    return "\n".join(parts)


def score_gt(gt_doc, include_walls=False, tmp_dir=None):
    """Synthesize gt_doc -> SVG -> run svg_plan_reader -> benchmark_reader card. Returns
    (card, pred). The reader needs a file path, so the SVG is written to tmp_dir (a caller-owned
    scratch dir) or a fresh temp file."""
    import tempfile
    svg = synth_svg(gt_doc, include_walls=include_walls)
    if tmp_dir is not None:
        p = os.path.join(tmp_dir, "synth.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg)
        pred = R.read_sheet(p, 1.0)
    else:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "synth.svg")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(svg)
            pred = R.read_sheet(p, 1.0)
    card = B.score_pair(gt_doc, pred)
    return card, pred


def score_corpus(gt_dir, out_dir, limit=None, include_walls=False):
    """Synthesize + read + score every gt.json in gt_dir. Writes cards.jsonl (streamed, so a
    mid-run death keeps finished work) + report.md, and returns (cards, skipped). One bad file
    costs ONE row, never the run (mirrors svg_plan_reader.run_baseline)."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    cards, skipped = [], {"error": 0, "units": 0}
    gt_el_total = corpus_indoor_true = corpus_indoor_false = 0   # corpus-wide totals for the
    #                                     recall + representativeness lines in render_report
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as rows, \
            tempfile.TemporaryDirectory() as td:
        for k, gfp in enumerate(gt_files):
            base = os.path.basename(gfp)[:-len(".gt.json")]
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    rows.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                gm = gt.get("meta") or {}
                gt_el_total += gm.get("n_elements", len(gt.get("elements", [])))
                corpus_indoor_true += gm.get("indoor_true", 0)
                corpus_indoor_false += gm.get("indoor_false", 0)
                card, _pred = score_gt(gt, include_walls=include_walls, tmp_dir=td)
                cards.append(card)
                rows.write(json.dumps({"scene": base, "card": card}, ensure_ascii=False) + "\n")
            except Exception as e:              # one bad sheet costs one row, never the run
                skipped["error"] += 1
                rows.write(json.dumps({"scene": base, "skipped": "error",
                                       "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                rows.flush()
                if (k + 1) % 50 == 0:
                    print(f"  {k + 1}/{len(gt_files)}  scored={len(cards)} ({time.time()-t0:.0f}s)")
    report = render_report(cards, skipped, len(gt_files), time.time() - t0, include_walls,
                           gt_el_total=gt_el_total,
                           corpus_indoor=(corpus_indoor_true, corpus_indoor_false))
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return cards, skipped


def render_report(cards, skipped, n_total, secs, include_walls,
                  gt_el_total=None, corpus_indoor=None):
    if not cards:
        return "# synth_plan_2d F3 lane\n\nno gt scored -- " + json.dumps(skipped)
    agg = B.aggregate(cards)
    det, f3 = agg["detection"], agg["F3_indoor"]
    # Because the reader is always-indoor, EVERY F3 wrong call is an OUTDOOR piece it missed, so
    # f3_wrong = matched OUTDOOR pairs. That lets us report the matched subset's outdoor fraction
    # next to the corpus outdoor rate -- the representativeness check the adversarial review asked
    # for (is the small detected subsample biased against outdoor? measure it, don't assume).
    f3_wrong = sum(len(c["F3_indoor"].get("wrong_ids") or []) for c in cards)
    matched_out_frac = (f3_wrong / f3["n"]) if f3["n"] else None
    corpus_out_frac = None
    if corpus_indoor and (corpus_indoor[0] + corpus_indoor[1]):
        corpus_out_frac = corpus_indoor[1] / (corpus_indoor[0] + corpus_indoor[1])
    f3_of_gt = (f3["n"] / gt_el_total) if gt_el_total else None

    def pct(v):
        return "n/a" if v is None else f"{100.0 * v:.1f}%"

    verdict_counts = {}
    for c in cards:
        v = c["F3_indoor"]["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    L = [
        f"# synth_plan_2d -- REAL F3 reader score on Structured3D (pred != gt)", "",
        f"- synthesizer: {SYNTH_VERSION}  (walls drawn: {include_walls})",
        f"- reader: {R.READER_VERSION} (annotation-blind ink -> plan_cluster morphology; "
        f"NO indoor classifier -> the F3 number below is the ALWAYS-INDOOR BASELINE)",
        f"- scenes: {len(cards)} scored / {n_total} gt "
        f"(skipped {json.dumps(skipped)}); wall-clock {secs:.0f}s", "",
        f"## detection -- LOW RECALL BY EXPECTATION, not a soundness pass",
        f"- GT {det['n_gt']} vs pred {det['n_pred']} -> matched {det['matched']}: "
        f"recall {pct(det['recall'])}, precision {pct(det['precision'])}",
        f"- recall is low because ~54-63% of GT is sub-150mm decor the reader screens as thin, "
        f"plus furniture-vs-furniture merges under CLOSE_MM=40 -> F3 is scored on the DETECTED "
        f"SUBSET, not all GT (see honesty notes; NOT an easy round-trip).", "",
        f"## F3 indoor (THE deliverable -- first pred!=gt indoor score on any corpus)",
        f"- accuracy {pct(f3['accuracy'])} on {f3['n']} matched pairs carrying GT indoor"
        + (f" ({pct(f3_of_gt)} of all {gt_el_total} GT elements)" if f3_of_gt is not None else ""),
        f"- {f3_wrong} wrong calls = OUTDOOR (balcony/garden) pieces the always-indoor reader "
        f"misclassifies -- these wrong_ids are exactly where an indoor-inference upgrade must win",
        f"- REPRESENTATIVENESS: matched-subset outdoor fraction {pct(matched_out_frac)}"
        + (f" vs corpus outdoor rate {pct(corpus_out_frac)}" if corpus_out_frac is not None else "")
        + " -- close => the baseline is NOT optimistically biased against outdoor (measured).",
        f"- per-scene F3 verdicts: {verdict_counts}", "",
        "## honesty notes",
        "- F3 accuracy == indoor fraction among matched pairs BY CONSTRUCTION (the reader is "
        "silent=indoor). The number is the BASELINE TO BEAT; the win is the wired pred!=gt loop.",
        "- annotation-blind: the indoor label is never drawn (test_synth_plan_2d pins byte-"
        "identity across an indoor flip). No answer key leaks into the reader's input.",
        "- DETECTION-LIMITED SAMPLE: F3 n is ~a tenth of GT. plan_cluster screens sub-150mm decor "
        "and MERGES furniture drawn within CLOSE_MM=40 (bed+flush nightstand -> one blob matching "
        "neither, both leave F3). test_synth_plan_2d pins this merge limit. Clustered furniture is "
        "under-sampled; raising the slice (size-filtered realistic draw + instance separation) is "
        "the next slice.",
        "- furniture-only by default; --walls adds structure but ALSO merges wall-adjacent "
        "furniture -- quote the furniture-only lane as the F3 headline.",
        "", f"synthesizer: {SYNTH_VERSION}",
    ]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 2 and argv[1] == "--score":
        if len(argv) < 4:
            raise SystemExit("usage: synth_plan_2d.py --score <gt-dir> <out-dir> [limit N] [--walls]")
        walls = "--walls" in argv
        rest = [a for a in argv[4:] if a != "--walls"]
        limit = None
        if len(rest) >= 2 and rest[0] == "limit" and rest[1].isdigit():
            limit = int(rest[1])
        score_corpus(argv[2], argv[3], limit=limit, include_walls=walls)
    elif len(argv) >= 3:
        walls = "--walls" in argv
        gt = json.load(open(argv[1], encoding="utf-8"))
        svg = synth_svg(gt, include_walls=walls)
        with open(argv[2], "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {argv[2]} ({len(gt.get('elements', []))} elements, walls={walls})")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
