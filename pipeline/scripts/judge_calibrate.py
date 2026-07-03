#!/usr/bin/env python3
"""judge_calibrate.py — M3.2 judge governance (blueprint §9.4).

Compares the LLM judge (critique.py, gemini-2.5-flash rubric) against the
designer-labeled golden set and reports the two acceptance statistics:

    Spearman rho >= 0.8   correct RELATIVE ranking (tie-aware average ranks)
    Cohen's kappa >= 0.8  correct ABSOLUTE pass/fail (pass = overall >= 4.0,
                          the qa/thresholds.yaml client_qa.judge_score bound)

plus per-image residuals so miscalibrated regions are visible. Pure stdlib —
no scipy (rho on average ranks == Pearson on ranks, exact for ties).

Machine side = the mean over ALL stored rolls per image (machine-scores.json,
judge-variance rule ±0.5: single rolls never decide). Add fresh rolls with
critique.py first if an image has only one roll and the decision is close.

Human side = qa/golden-set/labels.json (owner copies labels.template.json,
fills overall_0_5 in 0.5 steps + verdict SHIP|REWORK per image, BLIND — do not
open machine-scores.json first; see LABELING.md).

Usage:
    python pipeline/scripts/judge_calibrate.py            # full report
    python pipeline/scripts/judge_calibrate.py --selftest # math check only
Exit 0 = calibration ran (report says PASS/FAIL); exit 2 = labels missing.
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GS = os.path.join(ROOT, "qa", "golden-set")
PASS_BOUND = 4.0          # qa/thresholds.yaml client_qa.judge_score (pass >= 4/5)
RHO_MIN = KAPPA_MIN = 0.8  # blueprint §9.4


def _avg_ranks(vals):
    """Tie-aware average ranks (1-based)."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def spearman(a, b):
    ra, rb = _avg_ranks(a), _avg_ranks(b)
    n = len(ra)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra)
    vb = sum((y - mb) ** 2 for y in rb)
    return cov / (va * vb) ** 0.5 if va and vb else 0.0


def cohen_kappa(a, b):
    """a, b: parallel lists of booleans (pass/fail)."""
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa = sum(a) / n
    pb = sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1.0 else 1.0


def selftest():
    assert abs(spearman([1, 2, 3, 4], [1, 2, 3, 4]) - 1.0) < 1e-9
    assert abs(spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-9
    assert abs(spearman([1, 1, 2, 2], [1, 1, 2, 2]) - 1.0) < 1e-9
    # kappa hand-check: po=0.6, pa=0.5, pb=0.6 -> pe=0.5, kappa=0.2
    a = [True] * 10 + [False] * 10
    b = [True] * 7 + [False] * 3 + [True] * 5 + [False] * 5
    assert abs(cohen_kappa(a, b) - 0.2) < 1e-9
    assert cohen_kappa([True, False] * 5, [True, False] * 5) == 1.0
    print("selftest OK (rho identity/reversal/ties, kappa bounds/identity)")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    machine = json.load(open(os.path.join(GS, "machine-scores.json"), encoding="utf-8"))["images"]
    lab_path = os.path.join(GS, "labels.json")
    if not os.path.exists(lab_path):
        print("labels.json missing — owner fills labels.template.json first (LABELING.md)")
        sys.exit(2)
    labels = json.load(open(lab_path, encoding="utf-8"))["labels"]

    ids, m_means, h_scores, m_pass, h_pass, rows = [], [], [], [], [], []
    for gid, lab in sorted(labels.items()):
        if lab.get("overall_0_5") is None or gid not in machine:
            continue
        rolls = [r["overall_0_5"] for r in machine[gid]["rolls"] if r.get("overall_0_5") is not None]
        if not rolls:
            continue
        mm = sum(rolls) / len(rolls)
        hh = float(lab["overall_0_5"])
        ids.append(gid)
        m_means.append(mm)
        h_scores.append(hh)
        m_pass.append(mm >= PASS_BOUND)
        h_pass.append(str(lab.get("verdict", "")).upper() == "SHIP")
        rows.append((gid, machine[gid]["source_stem"], mm, len(rolls), hh,
                     lab.get("verdict"), abs(mm - hh)))

    n = len(ids)
    if n < 10:
        print(f"only {n} labeled images — need >=10 for a meaningful rho; label more first")
        sys.exit(2)
    rho = spearman(m_means, h_scores)
    kap = cohen_kappa(m_pass, h_pass)
    ok = rho >= RHO_MIN and kap >= KAPPA_MIN

    rep = [f"# Judge calibration — {date.today()} (M3.2, blueprint §9.4)",
           f"Golden set: {n} designer-labeled images. Machine = mean over stored rolls "
           f"(gemini-2.5-flash rubric). Pass bound {PASS_BOUND} (thresholds client_qa).",
           "",
           f"| metric | value | bound | status |",
           f"|---|---|---|---|",
           f"| Spearman rho (ranking) | {rho:.3f} | >= {RHO_MIN} | {'PASS' if rho >= RHO_MIN else 'FAIL'} |",
           f"| Cohen's kappa (SHIP/REWORK) | {kap:.3f} | >= {KAPPA_MIN} | {'PASS' if kap >= KAPPA_MIN else 'FAIL'} |",
           "",
           f"**M3.2 acceptance: {'PASS' if ok else 'FAIL'}** "
           f"{'' if ok else '(an uncalibrated judge is a broken test, not a lenient one — do not gate production on it)'}",
           "",
           "| id | source | judge mean (n) | designer | Δ |",
           "|---|---|---|---|---|"]
    for gid, stem, mm, nr, hh, v, d in sorted(rows, key=lambda r: -r[6]):
        rep.append(f"| {gid} | {stem} | {mm:.2f} ({nr}) | {hh:.1f} {v} | {d:.2f} |")
    out = os.path.join(ROOT, "qa", "reports", f"judge-calibration-{date.today()}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep[:12]))
    print(f"\nfull report -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
