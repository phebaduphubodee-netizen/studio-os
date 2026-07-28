"""look_bench.py — R4 benchmark-anchored LOOK: put OUR frame next to DELIVERED work.

THE RULE (knowledge/brand-standards/iteration-control-and-review-gates.md, R4,
adopted 2026-07-28): every LOOK judgment answers "does this survive next to a
sold render?", never "is this better than my previous attempt?" — judging one's
own output against one's own prior output is the documented self-preference
bias, and it is exactly how mediocrity got approved for hours on 2026-07-28.

PRIVACY (inherits the sellability lane's LOCAL-ONLY law, qa/benchmark-sellability.md
+ commit fa2c0df): the anchors are the friend's delivered client renders under
`_private/` (gitignored, I-coded). This tool reads them for a LOCAL side-by-side
only. The sheet it writes goes UNDER `_private/` by default, never into a commit,
never into any external call; sheets carry NO project names, NO slugs, NO I-codes
— cells are labeled only OURS / DELIVERED. Anchors JUDGE; they never DICTATE
(copying an anchor is benchmark leakage — R4's own recorded failure mode).

Selection reuses benchmark_precut's audited pure classifiers (dim_class, sector)
so the panel draws from the same residential-render pool the sellability lane
froze — no second, drifting definition of "anchor". Dedup tags are NOT applied
(a near-dup in a LOOK panel is harmless; re-running phash on 800 files is not).

Usage (plain python, no bpy):
  python pipeline/scripts/look_bench.py pipeline/output/room_..._ql.png
         [--n 5] [--room bedroom] [--salt 0] [--out <dir under _private/>]
Re-runs with the same inputs give the SAME panel (seeded by filename+salt), so a
before/after pair of ours is judged against an IDENTICAL delivered panel.
"""
import argparse
import hashlib
import json
import os
import random
import sys

import benchmark_precut as bp

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATES = os.path.join(REPO, "_private", "benchmark", "candidates.json")
OUT_DEFAULT = os.path.join(REPO, "_private", "benchmark", "look-bench")
CELL_H = 480          # uniform cell height; widths follow each image's aspect
PAD = 8
LABEL_H = 26


def orientation(wh):
    """'portrait' | 'landscape' | 'squarish' — the cheap apples-to-apples cut."""
    w, h = wh
    r = w / max(1, h)
    if r > 1.15:
        return "landscape"
    if r < 0.87:
        return "portrait"
    return "squarish"


def anchor_pool(candidates, want_orient=None, room=None):
    """The sellability lane's residential-render pool, optionally narrowed by
    orientation / room hint. PURE (no I/O) — testable on synthetic records."""
    pool = []
    for c in candidates:
        eng = bp.render_engine(os.path.basename(c["path"]))
        if bp.dim_class(c["wh"], eng) != "render":
            continue
        if bp.sector(c["project"])[0] == "commercial":
            continue
        if want_orient and orientation(c["wh"]) != want_orient:
            continue
        if room and bp.room_hint(c["project"]) != room:
            continue
        pool.append(c)
    return pool


def select_pool(candidates, orient, room):
    """Fallback chain, honest about what it dropped: (orient+room) -> (room only)
    -> (bare pool). Returns (pool, effective_orient, effective_room) so the
    summary line never claims a filter the panel did not actually wear (review
    2026-07-28: a mixed-orientation panel labeled apples-to-apples is exactly
    the mis-judgment R4 exists to prevent). PURE — testable on synthetic records."""
    pool = anchor_pool(candidates, want_orient=orient, room=room)
    if pool:
        return pool, orient, room
    pool = anchor_pool(candidates, want_orient=None, room=room)
    if pool:
        return pool, None, room
    pool = anchor_pool(candidates, want_orient=orient, room=None)
    if pool:
        return pool, orient, None
    return anchor_pool(candidates), None, None


def pick(pool, ours_name, n, salt=0):
    """Deterministic panel: same (ours_name, salt, pool) -> same anchors, so a
    before/after of OUR frame is judged against an identical delivered panel."""
    seed = int(hashlib.sha1(f"{ours_name}|{salt}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))


def _guard_out(out_dir):
    """LOCAL-ONLY: a sheet IS client imagery, so it may land ONLY under
    REPO/_private/ (gitignored). ALLOWLIST, resolved + normcased — a substring
    denylist was refuted at review (2026-07-28): case-insensitive NTFS accepts
    Projects\\ / KNOWLEDGE\\ spellings, and qa/, docs/, assets/ were all open."""
    allowed = os.path.normcase(os.path.realpath(os.path.join(REPO, "_private")))
    got = os.path.normcase(os.path.realpath(out_dir))
    if got != allowed and not got.startswith(allowed + os.sep):
        raise SystemExit(f"look_bench: refusing {out_dir!r} — sheets are LOCAL-ONLY client "
                         f"imagery and may only be written under _private/")
    return out_dir


def compose(ours_path, anchor_paths, out_path):
    """One row: OURS first (red border), then the delivered anchors. No names."""
    from PIL import Image, ImageDraw
    cells = []
    for i, p in enumerate([ours_path] + list(anchor_paths)):
        im = Image.open(p).convert("RGB")
        w = max(1, round(im.width * CELL_H / im.height))
        cells.append(im.resize((w, CELL_H)))
    total_w = sum(c.width for c in cells) + PAD * (len(cells) + 1)
    sheet = Image.new("RGB", (total_w, CELL_H + LABEL_H + 2 * PAD), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    x = PAD
    for i, c in enumerate(cells):
        sheet.paste(c, (x, LABEL_H + PAD))
        label = "OURS" if i == 0 else f"DELIVERED {i}"
        colour = (255, 80, 80) if i == 0 else (200, 200, 200)
        d.text((x + 4, 6), label, fill=colour)
        if i == 0:
            d.rectangle([x - 2, LABEL_H + PAD - 2, x + c.width + 1, LABEL_H + PAD + CELL_H + 1],
                        outline=(255, 80, 80), width=2)
        x += c.width + PAD
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="R4 side-by-side vs delivered anchors (LOCAL-ONLY)")
    ap.add_argument("ours", help="our render (png)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--room", default=None, help="room_hint filter, e.g. bedroom")
    ap.add_argument("--salt", type=int, default=0, help="new salt = new panel, same salt = same panel")
    ap.add_argument("--out", default=OUT_DEFAULT)
    a = ap.parse_args(argv)

    from PIL import Image
    with Image.open(a.ours) as im:
        ours_orient = orientation((im.width, im.height))

    data = json.load(open(CANDIDATES, encoding="utf-8"))
    root_fix = lambda p: p if os.path.exists(p) else os.path.join(REPO, p)
    pool, eff_orient, eff_room = select_pool(data["images"], ours_orient, a.room)
    if not pool:
        raise SystemExit("look_bench: anchor pool is empty even unfiltered — "
                         "_private/benchmark/candidates.json is missing or gutted")
    for want, got, what in ((ours_orient, eff_orient, "orientation"), (a.room, eff_room, "room")):
        if want and got is None:
            print(f"note: {what} filter '{want}' starved the pool — dropped (panel is looser "
                  f"than asked; judge accordingly)")
    chosen = pick(pool, os.path.basename(a.ours), a.n, a.salt)

    out = os.path.join(_guard_out(a.out),
                       f"bench_{os.path.splitext(os.path.basename(a.ours))[0]}_s{a.salt}.png")
    compose(a.ours, [root_fix(c["path"]) for c in chosen], out)
    print(f"panel: {len(chosen)} delivered anchors (orient={eff_orient or 'any'}, "
          f"room={eff_room or 'any'}, pool={len(pool)})")
    print(f"sheet: {out}   [LOCAL-ONLY — never commit, never egress]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
