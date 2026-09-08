"""test_rules_reader_check.py — seeded suite for rules_reader_check.py.

The load-bearing test is the LAST one: adding a rule to the rules file without a
consumer must FAIL. Without it this is a report, and this repo has had four
reports of this same defect already.

Pure Python, no test framework:  python pipeline/scripts/test_rules_reader_check.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules_reader_check as rr

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


RULES = {
    "_meta": {"name": "ignored"},
    "kitchen_NKBA": {"_note": "not a rule", "work_aisle_one_cook": {"in": 42},
                     "never_read_by_anything": {"in": 99}},
    "circulation": {"tested_only_key": {"in": 30}},
}
SRC = {
    "/x/clearance_check.py": 'lo = _r("kitchen_NKBA", "work_aisle_one_cook", "in")',
    "/x/test_clearance_check.py": 'assert "tested_only_key" in RULES',
}


def state(rows, key):
    return next(r["state"] for r in rows if r["id"].endswith("." + key))


rows = rr.audit(RULES, SRC)
check("a key quoted by a production script is READ",
      state(rows, "work_aisle_one_cook") == "READ")
check("a key nothing quotes is UNREAD", state(rows, "never_read_by_anything") == "UNREAD")
check("a key only a test quotes is TEST-ONLY, which counts as unread",
      state(rows, "tested_only_key") == "TEST-ONLY")
check("`_meta` and `_note` are not rules",
      not any(r["id"].startswith("_") or r["id"].endswith("._note") for r in rows)
      and len(rows) == 3, [r["id"] for r in rows])


def run(rules, baseline, extra=()):
    d = tempfile.mkdtemp()
    rp, bp = os.path.join(d, "rules.json"), os.path.join(d, "base.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(rules, f)
    if baseline is not None:
        with open(bp, "w", encoding="utf-8") as f:
            json.dump({"unread": baseline}, f)
    cp = subprocess.run([sys.executable, os.path.join(HERE, "rules_reader_check.py"),
                         "--rules", rp, "--baseline", bp, *extra],
                        capture_output=True, text=True, cwd=HERE)
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


# Against the REAL repo sources, so these exercise the actual scan.
REAL_OK = {"kitchen_NKBA": {"work_aisle_one_cook": {"in": 42}}}
REAL_NEW = {"kitchen_NKBA": {"work_aisle_one_cook": {"in": 42}},
            "brand_new_block": {"a_number_nobody_reads": {"mm": 1219}}}

rc, out = run(REAL_OK, [])
check("a fully-wired rules file exits 0 with an empty baseline", rc == 0, str(rc) + out)

rc, out = run(REAL_NEW, [])
check("THE RATCHET: a NEW rule with no reader FAILS", rc == 1, str(rc) + out)
check("...and the message says a rule nothing reads is a number, not a guard",
      "not a guard" in out, out)

rc, out = run(REAL_NEW, ["brand_new_block.a_number_nobody_reads"])
check("an unread key already in the baseline is tolerated", rc == 0, str(rc) + out)

rc, out = run(REAL_OK, ["kitchen_NKBA.work_aisle_one_cook"])
check("a key that GAINED a reader is reported so the baseline can shrink",
      rc == 0 and "[CLOSED]" in out, out)

rc, out = run(REAL_NEW, ["brand_new_block.a_number_nobody_reads"],
              extra=("--update-baseline",))
check("--update-baseline writes when it does not grow", rc == 0, str(rc) + out)
rc, out = run(REAL_NEW, [], extra=("--update-baseline",))
check("--update-baseline REFUSES to grow the baseline", rc == 1 and "REFUSING" in out, out)
check("...naming the ratchet law", "not a ratchet" in out, out)

rc, out = run(REAL_OK, None)
check("no baseline at all is exit 2 — could-not-run, not a pass", rc == 2, str(rc) + out)

# The live repo state, as a regression: kitchen must stay wired.
live = rr.audit(json.load(open(rr.RULES, encoding="utf-8")), rr.sources())
kit = [r for r in live if r["id"].startswith("kitchen_NKBA.")]
check("LIVE: all 7 kitchen_NKBA keys now have a production reader",
      len(kit) == 7 and all(r["state"] == "READ" for r in kit),
      [(r["id"], r["state"]) for r in kit])

bad = [r for r in RESULTS if not r[1]]
for name, ok, detail in RESULTS:
    print(f"  [{'ok' if ok else 'XX'}] {name}")
    if not ok and detail:
        print(f"        got: {detail}")
print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
sys.exit(1 if bad else 0)
