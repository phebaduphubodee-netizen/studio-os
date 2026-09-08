#!/usr/bin/env python3
"""BM25 keyword search over knowledge/ with path citations (M1.1 first pass).

Pure stdlib. The corpus is ~276 markdown files (knowledge 215 + docs 61), so
the index is built per query; no persistence, no staleness. Thai text is
matched via character bigrams (no word segmentation dependency).

Usage:
    python3 scripts/vault_search.py "query text" [-k 5] [--root knowledge]
                                    [--tier distilled] [--json]

Output: rank, score, TIER, path#heading citation, snippet — one block per hit.
Dense/rerank hybrid is a later Phase 1 upgrade; keep the CLI contract stable.

WHY EVERY HIT CARRIES A TIER (added 2026-08-08, from a measurement)
-------------------------------------------------------------------
The 2026-08-08 research run put ~50 files of raw DR prose into `docs/research/`.
Asked "skirting shadow gap wall floor junction plinth mm" the DEFAULT corpus
then returns those DR files at ranks 1-4 and buries
`knowledge/rendering/render-defaults.md` — the distilled file that actually
holds `10-15 mm` plinth and `10-20 mm` shadow-gap and says a razor 0 mm
junction is the CG tell — below them. Raw research outranking distilled truth
ON ITS OWN TOPIC is how a settled number gets re-researched, which is exactly
what happened to that junction: held since 2026-07-04, flagged NOT APPLIED on
07-22, re-found by a critic on 08-07, sent to a fresh DR on 08-08.

So the ranking is NOT silently changed — existing callers keep the corpus they
had — but every hit now says which tier it came from, and `--tier` filters:

    distilled  knowledge/, minus _inbox and minus studio-vault. Domain truth.
    staged     knowledge/_inbox/. Research that has NOT been distilled: real
               content, unaudited, cite it and you are citing an inbox.
    vault      knowledge/studio-vault/. The migrated v2.2 studio vault —
               templates, commands, and the studio's own operating documents.
    research   docs/. DR output, audits, decisions-of-record. Never truth.

Tier is derived from the path, not from a list of files, so a document added
tomorrow lands in the right tier without anyone remembering to register it.

MEASURED WARNING — `--tier distilled` IS NOT A BETTER SEARCH
------------------------------------------------------------
An adversarial pass ran it against the repo's own golden set the hour it landed:

    default corpus      23/25 = 92% hit@3   (unchanged by this feature)
    --tier distilled     5/25 = 20% hit@3   worse on 18 questions, better on 0

That is NOT a defect in the flag. It is a MEASUREMENT OF THE DISTILLATION DEBT: only
~46 of 276 corpus files are in the distilled tier, and most of the golden answers still
live in `_inbox/` or `docs/`. The morning's audit said the same thing from the other
side — 669 of 766 knowledge files are staging.

So use each mode for what it answers:
  DEFAULT     "where is the best answer we have anywhere" — keep this for real lookups.
  --tier distilled  "can our DOMAIN TRUTH answer this on its own?" A hit means the value
              is settled and citable; a MISS is a real finding — it means the answer, if
              we have one, is unaudited staging. That is the question the wall/floor
              junction needed, and the one the default corpus could not answer because
              four raw DR files outranked the distilled page.
Never quote a `--tier distilled` miss as "the vault has nothing on X" without also
running the default corpus. The tier is a claim about STATUS, not about coverage.
"""
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

K1 = 1.5
B = 0.75
THAI = re.compile(r"[฀-๿]+")
WORD = re.compile(r"[a-z0-9]+")

TIERS = ("distilled", "staged", "vault", "research")


def tier_of(rel_path: str) -> str:
    """Path -> tier. Derived, never enumerated: a rule that lists the files it
    applies to will always miss the next one (R9b, paid for in this repo)."""
    if rel_path.startswith("knowledge/_inbox/"):
        return "staged"
    if rel_path.startswith("knowledge/studio-vault/"):
        return "vault"
    if rel_path.startswith("knowledge/"):
        return "distilled"
    return "research"


def tokenize(text: str) -> list:
    text = text.lower()
    toks = WORD.findall(text)
    for run in THAI.findall(text):
        toks.extend(run[i : i + 2] for i in range(len(run) - 1))
    return toks


def sections(path: Path) -> list:
    """Split a markdown file into (heading, start_line, text) chunks."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out, head, start, buf = [], "(top)", 1, []
    for i, line in enumerate(lines, 1):
        if line.startswith("#"):
            if buf:
                out.append((head, start, "\n".join(buf)))
            head, start, buf = line.lstrip("# ").strip() or "(untitled)", i, [line]
        else:
            buf.append(line)
    if buf:
        out.append((head, start, "\n".join(buf)))
    return out


def snippet(text: str, q_tokens: set, width: int = 220) -> str:
    body = " ".join(text.split())
    best, best_hits = body[:width], -1
    for m in range(0, max(1, len(body) - width), width // 2):
        win = body[m : m + width]
        hits = sum(1 for t in q_tokens if t in win.lower())
        if hits > best_hits:
            best, best_hits = win, hits
    return best


def main() -> int:
    # Windows consoles default to cp1252; vault text is UTF-8 (Thai, arrows).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--root", default=None, action="append",
                    help="corpus root(s); default: knowledge/ and docs/")
    ap.add_argument("--tier", default=None, action="append", choices=TIERS,
                    help="keep only these tiers (repeatable). Default: all, each hit "
                         "labelled. NOTE: --tier distilled scores 20%% hit@3 against the "
                         "golden set vs 92%% for the default corpus — it asks 'can our "
                         "domain truth answer this alone', NOT 'find me the answer'")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable: one JSON object on stdout")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    roots = [repo / r for r in (args.root or ["knowledge", "docs"])]
    want = set(args.tier) if args.tier else set(TIERS)

    docs = []  # (citation, tier, text, tokens)
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if p.name == "_vault-CLAUDE-v2.2.md":  # parked historical file — noise
                continue
            rel = p.relative_to(repo).as_posix()
            tier = tier_of(rel)
            if tier not in want:
                continue
            secs = sections(p)
            for head, line, text in secs:
                toks = tokenize(text)
                if toks:
                    docs.append((f"{rel}#L{line} ({head})", tier, text, toks))
            if secs:
                # whole-file doc too: catches queries whose terms scatter
                # across sections, and carries the path tokens (filenames
                # often hold the only occurrence of words like "template")
                whole = "\n".join(t for _, _, t in secs)
                docs.append((f"{rel}#L1 ((file))", tier, whole,
                             tokenize(whole) + tokenize(rel) * 3))
    if not docs:
        msg = ("no indexable documents found for tier(s) "
               + ",".join(sorted(want)))
        if args.json:
            print(json.dumps({"query": args.query, "tiers": sorted(want),
                              "n_docs": 0, "hits": [], "error": msg}))
            return 1
        print(msg, file=sys.stderr)
        return 1

    n = len(docs)
    avgdl = sum(len(t) for _, _, _, t in docs) / n
    df = Counter()
    for _, _, _, toks in docs:
        df.update(set(toks))

    q = tokenize(args.query)
    scores = []
    for cit, tier, text, toks in docs:
        tf = Counter(toks)
        s = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * tf[term] * (K1 + 1) / (
                tf[term] + K1 * (1 - B + B * len(toks) / avgdl)
            )
        if s > 0:
            scores.append((s, cit, tier, text))
    scores.sort(key=lambda x: -x[0])
    qset = set(q)

    if args.json:
        # A machine-readable MISS is the point of this mode: a caller that
        # claims "the vault has nothing on X" can be made to prove it, and
        # `n_hits: 0` is the only form of that claim anyone can re-run.
        print(json.dumps({
            "query": args.query,
            "tiers": sorted(want),
            "n_docs": n,
            "n_hits": len(scores),
            "hits": [{"rank": i, "score": round(s, 2), "tier": tier,
                      "citation": cit, "snippet": snippet(text, qset)}
                     for i, (s, cit, tier, text) in
                     enumerate(scores[: args.k], 1)],
        }, ensure_ascii=False))
        return 0

    if not scores:
        print(f"no hits in tier(s) {','.join(sorted(want))} — try different "
              f"terms; corpus roots: " + ", ".join(str(r) for r in roots))
        return 0
    for rank, (s, cit, tier, text) in enumerate(scores[: args.k], 1):
        # The tier is printed BEFORE the path because it changes what the hit
        # means: a STAGED hit is an inbox, not domain truth, and reading the
        # path alone does not make that obvious at a glance.
        print(f"{rank}. [{s:.2f}] [{tier.upper():9s}] {cit}\n   "
              f"{snippet(text, qset)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
