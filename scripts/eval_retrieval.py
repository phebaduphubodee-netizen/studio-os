#!/usr/bin/env python3
"""M1.1 retrieval eval: run qa/golden-set/retrieval-questions.json through
vault_search and score hit@3 (expected source cited in top-3).

Usage: python3 scripts/eval_retrieval.py [-k 3]
Exit 0 if pass-rate >= 0.90 (M1.1 gate), else 1.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HIT_LINE = re.compile(r"^\d+\. \[[\d.]+\] (.+?)#L\d")


def top_paths(query: str, k: int) -> list:
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "vault_search.py"), query, "-k", str(k)],
        capture_output=True, text=True, encoding="utf-8",
    )
    return [m.group(1) for line in r.stdout.splitlines()
            if (m := HIT_LINE.match(line))]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=3)
    args = ap.parse_args()

    spec = json.loads((REPO / "qa" / "golden-set" / "retrieval-questions.json")
                      .read_text(encoding="utf-8"))
    passed = 0
    rows = []
    for item in spec["questions"]:
        paths = top_paths(item["q"], args.k)
        hit = any(exp in p for exp in item["any_of"] for p in paths)
        passed += hit
        rows.append((hit, item["q"], paths[0] if paths else "(no hits)"))
        print(("PASS " if hit else "MISS ") + item["q"][:55]
              + "  ->  " + (paths[0] if paths else "(no hits)"))

    rate = passed / len(spec["questions"])
    print(f"\nRESULT: {passed}/{len(spec['questions'])} = {rate:.0%}"
          f"  (M1.1 gate: >=90%)")
    return 0 if rate >= 0.90 else 1


if __name__ == "__main__":
    sys.exit(main())
