#!/usr/bin/env python3
"""Scaffold a new project from templates/project (blueprint §6.1, M0.2).

Usage:
    python3 scripts/scaffold_project.py PRJ-2026-001 sukhumvit-condo [--client C-001]
"""
import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "project"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_id", help="e.g. PRJ-2026-001")
    ap.add_argument("slug", help="short kebab-case name, e.g. sukhumvit-condo")
    ap.add_argument("--client", default="C-XXX", help="client ID, e.g. C-001")
    args = ap.parse_args()

    if not re.fullmatch(r"PRJ-\d{4}-\d{3}", args.project_id):
        print("project_id must match PRJ-YYYY-NNN", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        print("slug must be kebab-case [a-z0-9-]", file=sys.stderr)
        return 1

    dest = ROOT / "projects" / f"{args.project_id}_{args.slug}"
    if dest.exists():
        print(f"already exists: {dest}", file=sys.stderr)
        return 1

    shutil.copytree(TEMPLATE, dest)
    subs = {
        "{{PROJECT_ID}}": args.project_id,
        "{{SLUG}}": args.slug,
        "{{CLIENT_ID}}": args.client,
        "{{DATE}}": datetime.date.today().isoformat(),
    }
    for f in dest.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        f.write_text(text, encoding="utf-8")

    (ROOT / "assets" / "projects" / args.project_id).mkdir(parents=True, exist_ok=True)
    for sub in ("renders", "maps", "upscales"):
        (ROOT / "assets" / "projects" / args.project_id / sub).mkdir(exist_ok=True)

    print(f"Scaffolded {dest.relative_to(ROOT)}")
    print(f"Asset dirs at assets/projects/{args.project_id}/")
    print("Next: drop intake documents into 00_intake/ and read its _contract.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
