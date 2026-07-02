#!/usr/bin/env python3
"""inbox_audit.py — make the _inbox -> knowledge/ distillation debt VISIBLE.

The ingestion flow's failure mode is silence: REFERENCE-tier files sit in
knowledge/_inbox forever while the promoted dirs stay empty, and the vault's
retrieval surface (which mounts all of knowledge/) serves staging content as
truth (integrity red-team, 2026-07-02). This prints the debt; a human decides.

    python scripts/inbox_audit.py        # run alongside test_guards.sh / lfs_audit.sh
"""
import datetime
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, "knowledge", "_inbox")
# promoted dirs the staged content is destined for
TARGETS = ["ergonomics", "lighting", "materials", "styles", "codes-th",
           "classifications", "brand-standards"]
NOW = datetime.datetime.now()


def md_count(d):
    if not os.path.isdir(d):
        return -1
    return sum(1 for _, _, fs in os.walk(d) for f in fs if f.endswith(".md"))


print("=== knowledge/_inbox distillation debt ===")
total, oldest = 0, 0
for dirpath, _, files in os.walk(INBOX):
    for f in sorted(files):
        p = os.path.join(dirpath, f)
        age = (NOW - datetime.datetime.fromtimestamp(os.path.getmtime(p))).days
        rel = os.path.relpath(p, INBOX).replace("\\", "/")
        total += 1
        oldest = max(oldest, age)
        flag = "  <-- aging" if age >= 14 else ""
        print(f"  {age:4d}d  {rel}{flag}")

print("\n=== promoted dirs (the distillation destination) ===")
empties = []
for t in TARGETS:
    n = md_count(os.path.join(ROOT, "knowledge", t))
    state = "MISSING" if n < 0 else (f"{n} file(s)" if n else "EMPTY")
    if n == 0:
        empties.append(t)
    print(f"  knowledge/{t}: {state}")

print(f"\n  {total} file(s) staged, oldest {oldest}d; "
      f"{len(empties)} promoted dir(s) still empty: {', '.join(empties) or '-'}")
print("  (staging is not knowledge: distill or consciously drop — don't let it ride)")
