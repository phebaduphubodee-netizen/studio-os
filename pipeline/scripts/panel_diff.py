#!/usr/bin/env python3
"""panel_diff.py — WHAT DO THE JUDGES SAY ABOUT OURS THAT THEY DO NOT SAY ABOUT THE FIELD?

The exit panel already shows every judge four DELIVERED frames beside ours and asks all
five the same question. Until now the lane read only ours' rank and score and threw the
other four verdicts away — which is the panel's most valuable half, because a complaint
that lands on the delivered work too is not what separates us from it.

WHY THIS EXISTS (2026-09-02, after P2r-38 and P2r-39 both aimed at the window)
------------------------------------------------------------------------------
Two consecutive rounds were spent on the window wall because six judges, C2 and C3 all
named it. Both rounds moved their instruments and neither moved the panel. Then the same
verdicts, read across ALL FIVE frames instead of ours alone, said why:

    theme            OURS   PEERS   differential
    bench/ottoman     83%     29%      +54
    headboard        100%     50%      +50
    window/glare     100%     54%      +46
    camera/crop       17%    100%      -83

A blown, viewless window is named in the top-3 of HALF TO TWO-THIRDS of the delivered
frames that outrank us. It is close to a genre convention, not our defect — and the
round's close condition ("no judge names the window in their top-3") is a bar the
benchmark itself fails, so it could never have been met by improving the frame. Two
items we had never touched, the bench and the headboard, separate us further than the
one we spent two rounds on. And the camera — the thing the previous rounds fixed — is
now our largest ADVANTAGE over the field.

THE RULE THIS ENCODES: before adopting a bar of the form "no judge may say X", measure
how often judges say X about the delivered work. A bar the reference cannot clear
measures the genre, not the frame.

NOT A RANKING RUNG. `exit_panel` owns rank, score and gap (D-189). This owns only the
DIFFERENTIAL, and it is advisory: small n (one panel = 3 judge-views of ours against 12
of the field) means it points, it does not convict.
"""
import argparse
import json
import os
import re
import sys

# Themes are deliberately coarse and overlapping — this is a POINTER, and a finer
# taxonomy on n=6 would be false precision. Add a theme when a judge keeps naming
# something these miss; never tune one to make a number come out.
THEMES = {
    "window/glare":  r"window|glaz|blown|pure white|white void|light box|louvre|blind|exterior|glare",
    "headboard":     r"headboard",
    "bed dressing":  r"bedding|duvet|pillow|make the bed|dress the bed|throw|sheet|quilt|coverlet",
    "rug/floor":     r"\brug\b|floor",
    "bench/ottoman": r"bench|ottoman",
    "camera/crop":   r"camera|crop|recompose|reframe|sliced|amputat|re-aim|frame edge|wider|pull back",
    "value/palette": r"value|monochrome|beige|palette|contrast|dark anchor|accent|mono",
    "light story":   r"light story|no source|artifact|smear|downlight|lit from|shadow",
    "styling/empty": r"styl|empty|bare|\bart\b|mirror|plant|prop|dress",
}


def read_panel(panel_dir):
    """-> [(is_ours, [top3 strings]), ...] for every judge-view in one panel."""
    key_path = os.path.join(panel_dir, "panel_key.json")
    if not os.path.isfile(key_path):
        raise RuntimeError(f"no panel_key.json in {panel_dir}")
    with open(key_path, encoding="utf-8") as fh:
        key = json.load(fh)
    rows = []
    for j, mapping in (key.get("judges") or {}).items():
        ans = os.path.join(panel_dir, j, "ANSWER.md")
        if not os.path.isfile(ans):
            continue
        text = open(ans, encoding="utf-8").read()
        if "{" not in text:
            continue
        try:
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except ValueError:
            continue
        for v in data.get("verdicts", []):
            img = str(v.get("image", "")).replace(".png", "")
            tag = (mapping.get(img) or {}).get("tag")
            rows.append((tag == "OURS", list(v.get("top3_changes") or [])))
    if not rows:
        raise RuntimeError(f"{panel_dir} holds no readable judge answers")
    return rows


def differential(rows):
    ours = [items for is_ours, items in rows if is_ours]
    peers = [items for is_ours, items in rows if not is_ours]
    if not ours or not peers:
        raise RuntimeError(f"need both ours ({len(ours)}) and peers ({len(peers)})")
    out = []
    for name, pat in THEMES.items():
        rx = re.compile(pat, re.I)
        o = 100.0 * sum(any(rx.search(c) for c in it) for it in ours) / len(ours)
        p = 100.0 * sum(any(rx.search(c) for c in it) for it in peers) / len(peers)
        out.append({"theme": name, "ours_pct": o, "peers_pct": p, "diff": o - p})
    out.sort(key=lambda r: -r["diff"])
    return out, len(ours), len(peers)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("panel_dir", nargs="+", help="one or more exit-panel-* directories")
    a = ap.parse_args(argv)
    rows = []
    for d in a.panel_dir:
        try:
            rows += read_panel(d)
        except RuntimeError as e:
            print(f"PANEL-DIFF  COULD NOT READ {d} — {e}", file=sys.stderr)
    if not rows:
        return 2
    table, n_ours, n_peers = differential(rows)
    print(f"PANEL-DIFF  {n_ours} judge-view(s) of ours vs {n_peers} of the delivered field")
    print(f"PANEL-DIFF  {'theme':16s} {'OURS':>7s} {'PEERS':>7s} {'diff':>7s}")
    for r in table:
        print(f"PANEL-DIFF  {r['theme']:16s} {r['ours_pct']:6.0f}% {r['peers_pct']:6.0f}% "
              f"{r['diff']:+6.0f}")
    worst = table[0]
    print(f"PANEL-DIFF  largest differential: {worst['theme']} "
          f"({worst['diff']:+.0f} points) — this is what separates us from the field, "
          f"which is not the same question as what judges complain about most")
    universal = [r for r in table if r["peers_pct"] >= 50.0 and r["ours_pct"] >= 50.0]
    if universal:
        print("PANEL-DIFF  named on the DELIVERED work too (a bar of the form 'no judge "
              "may say X' would fail the benchmark itself): "
              + ", ".join(f"{r['theme']} {r['peers_pct']:.0f}%" for r in universal))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
