#!/usr/bin/env python3
"""BM25 keyword search over knowledge/ with path citations (M1.1 first pass).

Pure stdlib. Corpus is small (~60 markdown files), so the index is built per
query; no persistence, no staleness. Thai text is matched via character
bigrams (no word segmentation dependency).

Usage:
    python3 scripts/vault_search.py "query text" [-k 5] [--root knowledge]

Output: rank, score, path#heading citation, snippet — one block per hit.
Dense/rerank hybrid is a later Phase 1 upgrade; keep the CLI contract stable.
"""
import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

K1 = 1.5
B = 0.75
THAI = re.compile(r"[฀-๿]+")
WORD = re.compile(r"[a-z0-9]+")


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
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    roots = [repo / r for r in (args.root or ["knowledge", "docs"])]

    docs = []  # (citation, text, tokens)
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if p.name == "_vault-CLAUDE-v2.2.md":  # parked historical file — noise
                continue
            rel = p.relative_to(repo).as_posix()
            secs = sections(p)
            for head, line, text in secs:
                toks = tokenize(text)
                if toks:
                    docs.append((f"{rel}#L{line} ({head})", text, toks))
            if secs:
                # whole-file doc too: catches queries whose terms scatter
                # across sections, and carries the path tokens (filenames
                # often hold the only occurrence of words like "template")
                whole = "\n".join(t for _, _, t in secs)
                docs.append((f"{rel}#L1 ((file))", whole,
                             tokenize(whole) + tokenize(rel) * 3))
    if not docs:
        print("no indexable documents found", file=sys.stderr)
        return 1

    n = len(docs)
    avgdl = sum(len(t) for _, _, t in docs) / n
    df = Counter()
    for _, _, toks in docs:
        df.update(set(toks))

    q = tokenize(args.query)
    scores = []
    for cit, text, toks in docs:
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
            scores.append((s, cit, text))
    scores.sort(key=lambda x: -x[0])

    if not scores:
        print("no hits — try different terms; corpus roots: "
              + ", ".join(str(r) for r in roots))
        return 0
    qset = set(q)
    for rank, (s, cit, text) in enumerate(scores[: args.k], 1):
        print(f"{rank}. [{s:.2f}] {cit}\n   {snippet(text, qset)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
