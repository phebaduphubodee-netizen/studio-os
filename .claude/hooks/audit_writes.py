#!/usr/bin/env python3
"""PostToolUse audit trail: appends every successful file mutation to logs/.

Never blocks (always exit 0). Log is append-only by convention.
"""
import datetime
import json
import os
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR", data.get("cwd", "."))
    tool = data.get("tool_name", "?")
    path = (data.get("tool_input") or {}).get("file_path", "?")
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{tool}\t{path}\n"
    try:
        os.makedirs(os.path.join(root, "logs"), exist_ok=True)
        with open(os.path.join(root, "logs", "write-audit.log"), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
