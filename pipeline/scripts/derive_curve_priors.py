"""
derive_curve_priors.py -- TRAIN-side derivation of the per-kind CURVE signature that
kind_priors.suggest_kind uses to break size ties (v2). Runs svg_plan_reader ANNOTATION-BLIND
on train sheets, IoU-matches each pred element to its GT element (the same benchmark_reader
matcher the scorer uses), pairs the pred `curve` bool with the GT `kind`, and folds the
per-kind curve fraction into an existing size-priors doc via kind_priors.merge_curve_signatures.

    python derive_curve_priors.py <size_priors.json> <out_augmented.json> \
           <svg_dir> <gt_dir> [<svg_dir2> <gt_dir2> ...] [--limit N]

LEGITIMATE TRAIN/TEST SEPARATION: pass TRAIN svg/gt dirs only; the curve fractions are then
scored on the TEST split, exactly as the size bands are. mm-calibrated sheets only (svg-unit
dims are ~100x off and never scored). A sheet that fails to read costs one counted line, never
the run. Curve is a pred-side geometry flag (plan_cluster: >30 curve segments) -- never an
annotation read.
"""
import glob
import json
import os
import sys
import time

import benchmark_reader as B
import kind_priors
import svg_plan_reader as R


def _iter_pairs(dir_pairs, limit=None):
    """Yield (gt_kind, pred_curve_bool) for every IoU-matched element over the train dirs.
    Prints progress + a running mm-sheet count for the detached-run monitor."""
    n_sheets = n_mm = n_read = n_readfail = n_pairs = 0
    t0 = time.time()
    for svg_dir, gt_dir in dir_pairs:
        for gfp in sorted(glob.glob(os.path.join(gt_dir, "*.gt.json"))):
            if limit and n_mm >= limit:
                return
            n_sheets += 1
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
            except Exception:
                continue
            if (gt.get("meta") or {}).get("units") != "mm":
                continue
            base = os.path.basename(gfp)[:-len(".gt.json")]
            sfp = os.path.join(svg_dir, base + ".svg")
            if not os.path.exists(sfp):
                continue
            n_mm += 1
            try:
                pred = R.read_sheet(sfp, gt["meta"]["scale_mm_per_unit"])
            except Exception as e:
                n_readfail += 1
                if n_readfail <= 20:
                    print(f"  read-fail {base}: {type(e).__name__}: {e}", flush=True)
                continue
            n_read += 1
            g_el, _ = B.sanitize_elements(gt.get("elements", []))
            p_el, _ = B.sanitize_elements(pred.get("elements", []))
            pairs, _, _ = B.match_elements(g_el, p_el)
            for g, p, _v in pairs:
                n_pairs += 1
                yield g.get("kind"), bool(p.get("curve"))
            if n_mm % 500 == 0:
                print(f"  ...{n_mm} mm sheets read, {n_pairs} matched pairs, "
                      f"{time.time()-t0:.0f}s", flush=True)
    print(f"train run done: {n_sheets} sheets seen, {n_mm} mm, {n_read} read "
          f"({n_readfail} read-fail), {n_pairs} matched pairs, {time.time()-t0:.0f}s", flush=True)


def main(argv):
    limit = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 5 or (len(argv) - 3) % 2 != 0:
        raise SystemExit(__doc__)
    size_path, out_path = argv[1], argv[2]
    rest = argv[3:]
    dir_pairs = [(rest[i], rest[i + 1]) for i in range(0, len(rest), 2)]
    for sd, gd in dir_pairs:
        if not os.path.isdir(sd) or not os.path.isdir(gd):
            raise SystemExit(f"missing dir: {sd} or {gd}")

    size_doc = kind_priors.load(size_path)            # loud fail if not a kind-priors artifact
    stats = kind_priors.accumulate_curve(_iter_pairs(dir_pairs, limit))
    source = "+".join(os.path.basename(os.path.normpath(gd)) for _s, gd in dir_pairs)
    aug = kind_priors.merge_curve_signatures(size_doc, stats, source=source)

    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(aug, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)

    cm = aug["meta"]["curve"]
    print(f"\nwrote {out_path}")
    print(f"curve signatures: {cm['kinds_with_signature']} kinds >= {cm['min_support']} pairs "
          f"(of {len(aug['kinds'])} size kinds); {cm['n_pairs']} total matched pairs")
    print(f"{'kind':<16}{'pairs':>7}{'curve%':>9}  class")
    for k in sorted(aug["kinds"], key=lambda z: -(aug['kinds'][z].get('curve') or {}).get('n', 0)):
        c = aug["kinds"][k].get("curve")
        if not c:
            continue
        cls = kind_priors._curve_class(aug["kinds"][k]) or "ambiguous"
        print(f"{k:<16}{c['n']:>7}{c['frac']*100:>8.0f}%  {cls}")


if __name__ == "__main__":
    main(sys.argv)
