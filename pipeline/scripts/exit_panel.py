#!/usr/bin/env python3
"""THE EXIT TEST, AS ONE COMMAND — `qa/deliverable-plan.json`'s own finish line
("three sighted judges, our frame shuffled blind among delivered frames"),
which the 2026-09-01 audit measured at ZERO runs in that shape across 91 rounds.

Why a script and not a paragraph: the audit found the plan had been reviewed
94 times and its exit test rewritten 5 times, while the test itself was never
assembled — because assembling it meant, every time, resizing five images by
hand, inventing neutral names, shuffling per judge, writing the key somewhere
the judge cannot see, and typing the question again. A test that costs twenty
manual steps is run zero times; a test that costs one command is run after
every full frame. This file makes it the second kind. (R13's sentence, applied
to a test instead of an order: a rung carried out by hand is a rung that was
not carried out.)

WHAT IT DOES
  build   <render.png>  → <out>/j1..jN/{A..E}.png + PROMPT.md   (one pack per
                          judge, distinct shuffle, long edge 1600, LANCZOS)
                          and <out>/panel_key.json (the mapping — OUTSIDE the
                          packs, so the judge's directory holds no answer).
  record  <out> --judge j1 --scores '{"A":61,...}' --rank '["C","A",...]'
                --verdict "..."  → appends one row to qa/exit-panel-log.json
                          decoded through the key (which letter was OURS).
  status                → the lines plan_status prints: last panel, its scores,
                          and how many full frames have been rendered since a
                          panel last ran — THE COUNTER that makes "after every
                          full frame" checkable instead of remembered.

WHAT IT REFUSES
  - a pool file that does not exist (fails closed — never a panel of one)
  - fewer than 3 delivered frames in the pool (a field of two is not a field)
  - a key written inside a pack directory (never; the judge reads the pack)
  - the delivered frames are under `_private/` and STAY THERE: this script
    reads them, never copies them anywhere git can see. The packs live under
    the scratchpad or `_private/` — refuse any --out inside the repo that is
    not under `_private/`.

LAYER LAW: pure Python + PIL, no bpy, no network. Nothing leaves the machine.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POOL_REL = os.path.join("projects", "PRJ-2026-002_c001-house", "04_visualization",
                        "_private", "exit-panel-pool.json")
LOG_REL = os.path.join("qa", "exit-panel-log.json")
OUTPUT_REL = os.path.join("pipeline", "output")
LONG_EDGE = 1600
LETTERS = "ABCDEFGH"

# The one question, fixed — so a judge cannot be steered round by round.
# It names no frame as ours, carries no build history, and asks for the three
# things the panel is for: rank, sendability, and what a designer would change.
QUESTION = """You are a senior interior designer reviewing FIVE bedroom renders (A-E) for a
client presentation. You do not know who made any of them. Judge each frame
exactly as a client would see it: composition, light, styling, material,
believability — the whole picture, not a checklist.

For EACH image return:
  - sendable: "sendable-as-is" | "sendable-after-minor-fixes" | "not-sendable"
  - score_0_100 (100 = the best delivered bedroom render you have seen)
  - top3_changes: the three changes a designer would make first, concrete
  - one_line_read: what the room is, in one line

Then: rank all five best to worst, and name the ONE frame that most looks like
it did not come from a delivering studio, with one sentence why.

Do not average. Do not soften. Open every image at full size before writing.
Return JSON: {"verdicts":[{"image":"A.png","sendable":...,"rank":n,
"score_0_100":n,"top3_changes":[...],"one_line_read":"..."}, ...],
"order_best_to_worst":[...], "odd_one_out":{"image":"X.png","why":"..."}}
"""


def _now():
    return _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _pool(path):
    if not os.path.exists(path):
        sys.exit(f"exit_panel: no pool file at {path} — the delivered frames "
                 f"are chosen once, by hand, into that file (paths under "
                 f"_private/). No pool, no panel: this never defaults to a "
                 f"field of one.")
    with open(path, encoding="utf-8") as f:
        pool = json.load(f)
    frames = pool.get("frames") or []
    frames = [f for f in frames if isinstance(f, dict) and f.get("path")]
    missing = [f["path"] for f in frames if not os.path.exists(os.path.join(REPO, f["path"]))]
    if missing:
        sys.exit("exit_panel: pool names frames that are not on disk: "
                 + ", ".join(missing))
    if len(frames) < 3:
        sys.exit(f"exit_panel: pool holds {len(frames)} delivered frames; the "
                 f"exit test needs at least 3 — a field of two is a coin.")
    return frames


def _resize_to(src, dst):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = LONG_EDGE / float(max(w, h))
    if s < 1.0:
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    im.save(dst, "PNG")
    return im.size


def _out_is_safe(out):
    """Packs may live in the scratchpad (outside the repo) or under _private/.
    Anywhere else inside the repo is a copy of the friend's delivered work
    that git can see — refused."""
    o = os.path.abspath(out)
    r = os.path.abspath(REPO)
    try:
        inside = os.path.commonpath([o, r]) == r
    except ValueError:
        inside = False
    if inside and (os.sep + "_private" + os.sep) not in (o + os.sep):
        sys.exit(f"exit_panel: --out {out} is inside the repo and not under "
                 f"_private/ — the delivered frames must never land where git "
                 f"can see them.")


def build(render, out, judges, seed, pool_path):
    _out_is_safe(out)
    render = os.path.abspath(render)
    if not os.path.exists(render):
        sys.exit(f"exit_panel: render not found: {render}")
    frames = _pool(pool_path)
    entries = [{"tag": "OURS", "path": render}] + [
        {"tag": f.get("tag") or f"F{i+1}", "path": os.path.join(REPO, f["path"])}
        for i, f in enumerate(frames)]
    if len(entries) > len(LETTERS):
        sys.exit("exit_panel: too many frames for one panel")
    letters = LETTERS[:len(entries)]
    rng = random.Random(seed)
    key = {"render": os.path.relpath(render, REPO).replace("\\", "/"),
           "render_sha1": hashlib.sha1(open(render, "rb").read()).hexdigest()[:12],
           "built_at": _now(), "seed": seed, "long_edge": LONG_EDGE,
           "pool": os.path.relpath(pool_path, REPO).replace("\\", "/"),
           "judges": {}}
    seen = set()
    os.makedirs(out, exist_ok=True)
    for j in range(1, judges + 1):
        # distinct shuffle per judge: two judges seeing the same order would
        # make position a shared prior, and the audit's first attempt produced
        # exactly that duplicate before it was caught.
        for _ in range(1000):
            order = entries[:]
            rng.shuffle(order)
            sig = tuple(e["tag"] for e in order)
            if sig not in seen:
                seen.add(sig)
                break
        pack = os.path.join(out, f"j{j}")
        os.makedirs(pack, exist_ok=True)
        mapping = {}
        for letter, e in zip(letters, order):
            size = _resize_to(e["path"], os.path.join(pack, f"{letter}.png"))
            mapping[letter] = {"tag": e["tag"], "size": list(size)}
        with open(os.path.join(pack, "PROMPT.md"), "w", encoding="utf-8") as f:
            f.write(QUESTION)
        key["judges"][f"j{j}"] = mapping
    key_path = os.path.join(out, "panel_key.json")
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)
    print(f"exit_panel: {judges} packs under {out} ({len(entries)} frames each, "
          f"long edge {LONG_EDGE}); key at {key_path} — hand a judge ONLY its "
          f"j*/ directory.")
    return key


def _load_log(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"_what": "Every run of the plan's exit test (exit_panel.py): one "
                     "row per judge per panel. Decoded through the key, so "
                     "`ours` is the letter's content, not the letter. Read by "
                     "plan_status via exit_panel.status().",
            "runs": []}


def record(out, judge, scores, rank, verdict, sendable, odd_one_out, note):
    key_path = os.path.join(out, "panel_key.json")
    with open(key_path, encoding="utf-8") as f:
        key = json.load(f)
    mapping = key["judges"].get(judge)
    if not mapping:
        sys.exit(f"exit_panel: no judge {judge} in {key_path}")
    ours_letter = next(l for l, m in mapping.items() if m["tag"] == "OURS")
    sc = json.loads(scores) if isinstance(scores, str) else scores
    rk = json.loads(rank) if isinstance(rank, str) else rank
    rk = [r.replace(".png", "") for r in rk]
    decoded_scores = {mapping[l]["tag"]: v for l, v in sc.items() if l in mapping}
    decoded_rank = [mapping[l]["tag"] for l in rk if l in mapping]
    row = {"at": _now(), "render": key["render"], "render_sha1": key["render_sha1"],
           "panel_dir": os.path.abspath(out), "judge": judge,
           "ours_letter": ours_letter,
           "ours_score": sc.get(ours_letter),
           "ours_rank": (rk.index(ours_letter) + 1) if ours_letter in rk else None,
           "field": len(mapping), "scores": decoded_scores, "order": decoded_rank,
           "ours_sendable": sendable, "odd_one_out": (mapping.get(
               (odd_one_out or "").replace(".png", ""), {}).get("tag") or odd_one_out),
           "verdict_file": verdict, "note": note}
    log_path = os.path.join(REPO, LOG_REL)
    log = _load_log(log_path)
    log["runs"].append(row)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print(f"exit_panel: recorded {judge} on {key['render']}: OURS={ours_letter} "
          f"score {row['ours_score']} rank {row['ours_rank']}/{row['field']} "
          f"{sendable or ''}")
    return row


def _full_frames_since(since_iso):
    """Full-fidelity room frames written after `since` — the frames that owed a
    panel and did not get one. Reads mtimes under pipeline/output; quick legs
    (_ql, cct*, crops) are not full frames."""
    root = os.path.join(REPO, OUTPUT_REL)
    if not os.path.isdir(root):
        return []
    since = _dt.datetime.fromisoformat(since_iso).timestamp() if since_iso else 0
    out = []
    for name in os.listdir(root):
        if not (name.startswith("room_") and name.endswith(".png")):
            continue
        if "_ql" in name or "cct" in name or "crop" in name:
            continue
        p = os.path.join(root, name)
        try:
            st = os.stat(p)
        except OSError:
            continue
        if st.st_mtime > since and st.st_size > 1_000_000:
            out.append(name)
    return sorted(out)


def status(log_path=None):
    """Lines for plan_status. The last line is the counter."""
    log = _load_log(log_path or os.path.join(REPO, LOG_REL))
    runs = log.get("runs") or []
    lines = []
    if not runs:
        lines.append("EXIT PANEL: never recorded — the plan's exit test has 0 "
                     "runs in its own shape (audit 2026-09-01). Run "
                     "`exit_panel.py build <render>` after the next full frame.")
        return lines
    last_render = runs[-1]["render"]
    rows = [r for r in runs if r["render"] == last_render]
    scores = [r["ours_score"] for r in rows if r.get("ours_score") is not None]
    ranks = [f"{r['ours_rank']}/{r['field']}" for r in rows if r.get("ours_rank")]
    sends = [r.get("ours_sendable") or "?" for r in rows]
    mean = round(sum(scores) / len(scores), 1) if scores else None
    at = rows[-1]["at"][:10]
    lines.append(f"EXIT PANEL: last on {last_render} ({at}) — {len(rows)} judge(s), "
                 f"OURS {'/'.join(str(s) for s in scores)} (mean {mean}), rank "
                 f"{' '.join(ranks)}, {', '.join(sends)}")
    # history, one line, oldest first: the number that says whether the lane moves
    by_render = []
    for r in runs:
        if not by_render or by_render[-1][0] != r["render"]:
            by_render.append([r["render"], []])
        if r.get("ours_score") is not None:
            by_render[-1][1].append(r["ours_score"])
    hist = " → ".join(f"{os.path.basename(k).replace('room_bedroom_suite_eye_', '')}:"
                      f"{round(sum(v)/len(v)) if v else '?'}" for k, v in by_render[-6:])
    lines.append(f"  history (mean): {hist}")
    owed = _full_frames_since(rows[-1]["at"])
    if owed:
        lines.append(f"  OWED: {len(owed)} full frame(s) rendered since the last "
                     f"panel with no panel — {', '.join(owed[:4])}"
                     f"{' …' if len(owed) > 4 else ''}. Every full frame gets "
                     f"the panel (ORD-2026-09-01-direction-after-audit).")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("render")
    b.add_argument("--out", required=True)
    b.add_argument("--judges", type=int, default=3)
    b.add_argument("--seed", type=int, default=None,
                   help="default: derived from the render's bytes, so a rebuild "
                        "of the same frame gives the same packs")
    b.add_argument("--pool", default=os.path.join(REPO, POOL_REL))
    r = sub.add_parser("record")
    r.add_argument("out")
    r.add_argument("--judge", required=True)
    r.add_argument("--scores", required=True, help='{"A":61,"B":…}')
    r.add_argument("--rank", required=True, help='["C","A",…] best→worst')
    r.add_argument("--sendable", default=None, help="OURS' sendable verdict")
    r.add_argument("--odd-one-out", default=None)
    r.add_argument("--verdict", default=None, help="path of the judge's answer file")
    r.add_argument("--note", default="")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        seed = a.seed
        if seed is None:
            seed = int(hashlib.sha1(open(a.render, "rb").read()).hexdigest()[:8], 16)
        build(a.render, a.out, a.judges, seed, a.pool)
    elif a.cmd == "record":
        record(a.out, a.judge, a.scores, a.rank, a.verdict, a.sendable,
               a.odd_one_out, a.note)
    else:
        for line in status():
            print(line)


if __name__ == "__main__":
    main()
