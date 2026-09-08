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
TRAINED = os.path.join(REPO, "_private", "benchmark", "trained-anchors.json")
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


def load_trained(path=TRAINED):
    """Project keys quarantined by the reproduction curriculum (R4 leakage law,
    qa/reproduction-curriculum.md rule 2). FAIL-LOUD: since 2026-07-30 at least
    one training target exists, so a missing/empty file means the exclusion
    list was gutted — refusing beats silently judging against trained anchors
    (wired gates never silent-pass)."""
    try:
        data = json.load(open(path, encoding="utf-8"))
        keys = frozenset(p["project_key"] for p in data["projects"])
    except (OSError, KeyError, ValueError) as e:
        raise SystemExit(f"look_bench: cannot load trained-anchors quarantine {path!r} ({e}) — "
                         f"reproduction training targets exist (qa/reproduction-curriculum.md); "
                         f"restore the file before running any panel")
    if not keys:
        raise SystemExit(f"look_bench: {path!r} lists no projects but the reproduction ledger "
                         f"has ACTIVE training targets — restore it before running any panel")
    return keys


def anchor_pool(candidates, want_orient=None, room=None, trained=frozenset()):
    """The sellability lane's residential-render pool, optionally narrowed by
    orientation / room hint, minus reproduction-quarantined projects.
    PURE (no I/O) — testable on synthetic records."""
    pool = []
    for c in candidates:
        if c["project"] in trained:
            continue
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


def select_pool(candidates, orient, room, trained=frozenset()):
    """Fallback chain, honest about what it dropped: (orient+room) -> (room only)
    -> (bare pool). Returns (pool, effective_orient, effective_room) so the
    summary line never claims a filter the panel did not actually wear (review
    2026-07-28: a mixed-orientation panel labeled apples-to-apples is exactly
    the mis-judgment R4 exists to prevent). The trained quarantine is NEVER
    dropped by the fallback chain. PURE — testable on synthetic records."""
    pool = anchor_pool(candidates, want_orient=orient, room=room, trained=trained)
    if pool:
        return pool, orient, room
    pool = anchor_pool(candidates, want_orient=None, room=room, trained=trained)
    if pool:
        return pool, None, room
    pool = anchor_pool(candidates, want_orient=orient, room=None, trained=trained)
    if pool:
        return pool, orient, None
    return anchor_pool(candidates, trained=trained), None, None


def pick(pool, ours_name, n, salt=0, panel_key=None):
    """Deterministic panel: same (panel_key, salt, pool) -> same anchors.

    THE KEY DEFAULTS TO THE FILENAME AND THAT DEFEATED THE STATED PURPOSE.
    The line this docstring used to carry — "so a before/after of OUR frame is
    judged against an identical delivered panel" — was false for the only case
    it named: a before/after has, by definition, two different filenames, so it
    drew two different panels and the two ranks were never comparable. Measured
    2026-08-15 on the p2r35/p2r36 acquire-vs-simulate A/B: same --salt 236, and
    an independent blind ranker reported unprompted that the two sheets shared
    exactly ONE view. Our frame placed 6/6 on one sheet and 4/6 on the other
    against a DIFFERENT and weaker set of anchors — a jump that says nothing.

    So the panel key is now explicit. `panel_key` pins the anchor draw to a name
    the caller chooses, which is what makes two sheets a comparison rather than
    two unrelated exams. Omit it and the old filename behaviour stands, so every
    existing single-frame sheet reproduces byte for byte.

    NOT changed, deliberately: `blind_slot` still seeds off the real filename,
    so our frame is UNLIKELY to land in the same cell in two sheets (5/6 for a
    6-cell sheet, not a guarantee). A judge who saw both sheets should not be
    able to read our tile off a constant position; if two sheets do collide on
    a cell, re-run one with a different salt.

    THE KEY IS NOT SUFFICIENT ON ITS OWN, and saying so is the whole point.
    `rng.sample` draws from POOL, so an identical seed over a different pool
    returns different anchors. The pool depends on our own image's ORIENTATION,
    on --room, on select_pool's starve-fallback chain, on candidates.json, and
    on the trained quarantine. So the key pins the DRAW and `panel_fingerprint`
    pins the BOX drawn from — two sheets are comparable only when BOTH match,
    and both are printed. This module has just been burned by a claim asserted
    in prose instead of checked (a scale 'ASSERTED' in a spec note that belonged
    to a different file); a line reading 'comparable' that cannot be verified
    would be the same defect in new clothes."""
    seed = int(hashlib.sha1(f"{panel_key or ours_name}|{salt}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))


def panel_fingerprint(pool, n):
    """Short digest of the exact BOX the panel was drawn from: pool identity,
    pool order and n. Two sheets carrying the same panel key, the same salt AND
    the same fingerprint drew the same anchors; if the fingerprints differ, the
    ranks are not comparable no matter what the key says. PURE."""
    h = hashlib.sha1()
    h.update(f"n={n}|len={len(pool)}|".encode())
    for c in pool:
        h.update(str(c.get("path", "")).encode())
        h.update(b"\x00")
    return h.hexdigest()[:10]


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


def blind_slot(ours_name, salt, n_cells):
    """Which cell OURS occupies in a blind panel. PURE and deterministic, so a
    sheet can be regenerated and still mean the same thing — and separated from
    compose_blind so a test can assert the distribution is not always cell 0."""
    seed = int(hashlib.sha1(f"blind|{ours_name}|{salt}".encode()).hexdigest()[:8], 16)
    return seed % n_cells


def compose_blind(ours_path, anchor_paths, out_path, slot):
    """THE FINISH-LINE SHEET, and the reason it had to be written.

    `compose` puts OURS first, draws a red border round it and labels it "OURS".
    That is right for R4's day-to-day question — how does this frame compare with
    delivered work — and it makes R4's instrument structurally incapable of
    asking the CLOSING question, which is whether the owner can still pick ours
    out at all. A judge who is told the answer cannot fail the test.

    So this mode shuffles our frame into the panel at a deterministic slot,
    draws no border, writes no labels, and puts the answer in a SEPARATE file
    that the judge does not open until after choosing. Everything still lands
    under _private/ — a blind sheet is client imagery like any other."""
    from PIL import Image, ImageDraw
    paths = list(anchor_paths)
    paths.insert(slot, ours_path)
    cells = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        cells.append(im.resize((max(1, round(im.width * CELL_H / im.height)), CELL_H)))
    total_w = sum(c.width for c in cells) + PAD * (len(cells) + 1)
    sheet = Image.new("RGB", (total_w, CELL_H + LABEL_H + 2 * PAD), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    x = PAD
    for i, c in enumerate(cells):
        sheet.paste(c, (x, LABEL_H + PAD))
        d.text((x + 4, 6), chr(ord("A") + i), fill=(200, 200, 200))
        x += c.width + PAD
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    key = os.path.splitext(out_path)[0] + ".ANSWER.txt"
    with open(key, "w", encoding="utf-8") as f:
        f.write(f"ours is panel {chr(ord('A') + slot)}\n")
    return out_path, key


def main(argv=None):
    ap = argparse.ArgumentParser(description="R4 side-by-side vs delivered anchors (LOCAL-ONLY)")
    ap.add_argument("ours", help="our render (png)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--room", default=None, help="room_hint filter, e.g. bedroom")
    ap.add_argument("--salt", type=int, default=0, help="new salt = new panel, same salt = same panel")
    ap.add_argument("--panel-from", dest="panel_from", default=None,
                    help="draw the anchor panel as if our frame were named this "
                         "(any string). REQUIRED to compare two of our own frames: "
                         "without it the panel is seeded by FILENAME, so an A/B "
                         "draws two different panels and the ranks are not comparable")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--blind", action="store_true",
                    help="reproduction FINISH TEST: shuffle ours in unlabelled, "
                         "answer key written beside the sheet")
    a = ap.parse_args(argv)

    from PIL import Image
    with Image.open(a.ours) as im:
        ours_orient = orientation((im.width, im.height))

    data = json.load(open(CANDIDATES, encoding="utf-8"))
    trained = load_trained()
    root_fix = lambda p: p if os.path.exists(p) else os.path.join(REPO, p)
    pool, eff_orient, eff_room = select_pool(data["images"], ours_orient, a.room, trained=trained)
    if not pool:
        raise SystemExit("look_bench: anchor pool is empty even unfiltered — "
                         "_private/benchmark/candidates.json is missing or gutted")
    for want, got, what in ((ours_orient, eff_orient, "orientation"), (a.room, eff_room, "room")):
        if want and got is None:
            print(f"note: {what} filter '{want}' starved the pool — dropped (panel is looser "
                  f"than asked; judge accordingly)")
    chosen = pick(pool, os.path.basename(a.ours), a.n, a.salt, panel_key=a.panel_from)
    fp = panel_fingerprint(pool, a.n)
    if a.panel_from:
        print(f"panel key: '{a.panel_from}' · panel fingerprint: {fp} — comparable ONLY to a "
              f"sheet printing this SAME key, salt and fingerprint. The key pins the draw; the "
              f"fingerprint pins the pool it was drawn from, and the pool moves with our own "
              f"image's orientation, --room, the starve-fallback and candidates.json.")

    stem = os.path.splitext(os.path.basename(a.ours))[0]
    kind = "blind" if a.blind else "bench"
    # The panel key belongs in the NAME: without it, two sheets of the same frame
    # at the same salt but different keys resolve to one path and the second
    # silently clobbers the first — and its .ANSWER.txt with it, which is the one
    # file that must never be quietly replaced.
    key_tag = f"_k{hashlib.sha1(a.panel_from.encode()).hexdigest()[:6]}" if a.panel_from else ""
    out = os.path.join(_guard_out(a.out), f"{kind}_{stem}_s{a.salt}{key_tag}.png")
    anchors = [root_fix(c["path"]) for c in chosen]
    key = None
    if a.blind:
        out, key = compose_blind(a.ours, anchors, out,
                                 blind_slot(os.path.basename(a.ours), a.salt,
                                            len(anchors) + 1))
    else:
        compose(a.ours, anchors, out)
    print(f"panel: {len(chosen)} delivered anchors (orient={eff_orient or 'any'}, "
          f"room={eff_room or 'any'}, pool={len(pool)}, quarantined_projects={len(trained)})")
    print(f"sheet: {out}   [LOCAL-ONLY — never commit, never egress]")
    if key:
        print(f"answer: {key}   — DO NOT OPEN until the pick is made; opening it "
              f"first is the only way to fail this test by accident")
    return 0


if __name__ == "__main__":
    sys.exit(main())
