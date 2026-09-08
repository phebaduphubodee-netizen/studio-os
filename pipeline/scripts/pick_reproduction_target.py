#!/usr/bin/env python3
"""pick_reproduction_target.py — draw the next unit of the reproduction curriculum.

TRN-001 was picked by hand from a seed typed into a shell, and the only record
of how is a `seed` string in a private JSON. That is fine once and unreproducible
twice, and this curriculum is a standing order that runs "ทุก session จนกว่าจะ
สร้างงานของเพื่อนออกมาได้ทั้งหมด" — so the draw is a script.

WHAT IT ENFORCES, beyond convenience:

* THE POOL IS look_bench's, not a fresh one. The charter's rule 1 says picks come
  from `anchor_pool` — delivered residential RENDERS, commercial excluded — so a
  unit can never be a site photo or a shop drawing. TRN-001's first draw had to
  be re-rolled by hand for exactly that.
* ALREADY-TRAINED PROJECTS ARE EXCLUDED. `load_trained` is the same quarantine
  that keeps a reproduced project out of the judging pool, and it fails loud;
  reusing it here means a unit cannot be drawn twice, and cannot be drawn from a
  project whose siblings have already taught us the answer.
* THE MAPPING STAYS PRIVATE. The pick's path, project and filename are written
  ONLY under `_private/benchmark/reproduction/<TRN-id>/target.json`. What goes to
  stdout for the committed ledger is the TRN id, the seed, the pool size and the
  image's shape — never a name. The charter says so in its own header and this
  is the enforcement.

    python pipeline/scripts/pick_reproduction_target.py TRN-002 [--salt 0]
"""
import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import look_bench as LB  # noqa: E402

PRIV = os.path.join(LB.REPO, "_private", "benchmark", "reproduction")


def draw(candidates, trn_id, trained, salt=0):
    """Deterministic pick from the anchor pool. PURE — no I/O, seeded by the
    TRN id so the same unit always draws the same target."""
    pool = LB.anchor_pool(candidates, trained=trained)
    if not pool:
        raise SystemExit("pick: the anchor pool is empty after quarantine — nothing to draw")
    seed = int(hashlib.sha1(f"TRN-curriculum|{trn_id}|{salt}".encode()).hexdigest()[:8], 16)
    return random.Random(seed).choice(pool), len(pool)


def main(argv=None):
    ap = argparse.ArgumentParser(description="draw the next reproduction-curriculum unit")
    ap.add_argument("trn_id", help="e.g. TRN-002")
    ap.add_argument("--salt", type=int, default=0, help="bump to re-roll; record why in the ledger")
    a = ap.parse_args(argv)

    trained = LB.load_trained()
    # the SAME census look_bench reads — one pool, not a second one that could
    # drift away from the one the finish-line panel is drawn from
    with open(LB.CANDIDATES, encoding="utf-8") as fh:
        candidates = json.load(fh)["images"]
    hit, n = draw(candidates, a.trn_id, trained, a.salt)

    d = os.path.join(PRIV, a.trn_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "target.json"), "w", encoding="utf-8") as fh:
        json.dump({"seed": f"TRN-curriculum|{a.trn_id}|{a.salt}",
                   "pool_rule": "look_bench.anchor_pool (delivered residential renders, "
                                "commercial excluded, trained projects quarantined)",
                   "pool_n": n, "pick": hit}, fh, indent=1, ensure_ascii=False)

    # stdout is what a human pastes into the COMMITTED ledger: no name, no path
    print(f"{a.trn_id}: drawn from {n} candidates, seed TRN-curriculum|{a.trn_id}|{a.salt}")
    print(f"  shape {hit['wh'][0]}x{hit['wh'][1]} ({LB.orientation(hit['wh'])})")
    print(f"  mapping written to _private/benchmark/reproduction/{a.trn_id}/target.json "
          f"(gitignored — the charter forbids a corpus name in a committed file)")
    print(f"  NEXT: add {a.trn_id}'s project key to the quarantine before any look_bench run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
