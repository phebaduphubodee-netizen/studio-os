"""THE REAL METRIC. The gate count is not the goal -- a gate that accepts more pages has proved
nothing about whether the reader can READ them.

Memory's own warning from the round-1 post-mortem: "Never score this lane on a bbox; score it on
closure + the image." A bbox of a sparse cloud of corner stubs matched the printed overalls to the
mm and was still wall fins on a slab. So: does the ink CLOSE a room?

Seeds are swept on a grid IN BUILD'S OWN FRAME (origin = the wall bbox's SW corner, y NORTH -- the
first version of this script seeded in the page frame and every one of 27 pages "REFUSED"; that was
the harness lying, not the reader). For each page we report the LARGEST room the ink closes, so a
failure means the ink closes nothing ANYWHERE on the sheet, not that we guessed a bad seed.

Consumes _private/plan-gate/census.json (run census.py first) and REFUSES a stale one: the
census's reader_md5 must match the reader on disk, or the sweep would score one reader's gate
verdicts with another reader's builder -- the mixed-instrument incident, again.
Writes closure.json next to it, stamped with the same provenance.
Nothing here writes into the repo; client geometry stays under _private/ (gitignored).
"""
import hashlib
import json
import os
import subprocess
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline", "scripts"))
os.chdir(REPO)

import bluehouse_plan_reader as R  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Thai titles under piped cp1252

READER = os.path.join("pipeline", "scripts", "bluehouse_plan_reader.py")
READER_MD5 = hashlib.md5(open(READER, "rb").read()).hexdigest()
_gs = subprocess.run(["git", "status", "--porcelain", READER], capture_output=True, text=True)
DIRTY = f"git status FAILED rc={_gs.returncode}" if _gs.returncode else _gs.stdout.strip()
print(f"reader md5={READER_MD5}  working-tree={'DIRTY: ' + DIRTY if DIRTY else 'clean (== HEAD)'}")

DATA = os.path.join(REPO, "_private", "plan-gate")
census = json.load(open(os.path.join(DATA, "census.json"), encoding="utf-8"))
if census.get("reader_md5") != READER_MD5:
    sys.exit(f"census.json was measured against reader md5 {census.get('reader_md5')} but the "
             f"reader on disk is {READER_MD5}. Re-run census.py first -- sweeping another "
             "reader's gate verdicts with this builder is the mixed-instrument incident.")
rows = census["pages"]
accepted = [r for r in rows if r["accept"]]
print(f"{len(accepted)} pages accepted by the gate. Sweeping seeds on each.\n")

N = 7          # 7x7 seed grid over the footprint
out = []
for r in accepted:
    rec = {"pdf": os.path.basename(r["pdf"]), "page": r["page"], "title": r.get("title")}
    try:
        bands_pt, _st, scale, denom, _m, _tb, _c, _n = R.read_bands(r["pdf"], r["page"])
        px0 = min(b[0] for b in bands_pt)
        py1 = max(b[3] for b in bands_pt)                      # page y DOWN -> build's y NORTH
        bands = R.to_mm_bands(bands_pt, scale, px0, py1)       # build's own frame
        W = max(b[2] for b in bands)
        H = max(b[3] for b in bands)
        rec.update(scale=round(scale, 4), denom=denom, bands=len(bands),
                   extent_mm=[round(W), round(H)])

        best = None
        whys = set()
        seeds = {"built": 0, "refused": 0, "crashed": 0}
        for i in range(1, N + 1):
            for j in range(1, N + 1):
                seed = (W * i / (N + 1), H * j / (N + 1))
                try:
                    meta, _notes = R.build(r["pdf"], r["page"], seed=seed)
                except R.RefuseSheet:
                    seeds["refused"] += 1      # designed: seed in wall ink / outside envelope
                    continue
                except Exception as e:
                    # NOT designed. Recorded, or a builder regression that crashes all 49 seeds
                    # reads as 'no-closure' -- 'harness broken' must never wear 'the ink closes
                    # nothing' as a costume (the lying-harness shape from this file's docstring).
                    seeds["crashed"] += 1
                    whys.add("CRASH:" + type(e).__name__)
                    continue
                seeds["built"] += 1
                rc = meta.get("room_closure") or {}
                whys.add(rc.get("why", "?"))
                # `closed` is the reader's OWN honest verdict: false when the flood escaped to the
                # envelope border (= the boundary has a hole and the "room" is the outdoors).
                if not rc.get("closed"):
                    continue
                a = rc.get("area_m2") or 0.0
                if best is None or a > best[0]:
                    best = (a, rc.get("n_vertices"), rc.get("ink_backed"), seed)
        rec["seeds"] = seeds
        if best:
            rec.update(build="CLOSED", room_m2=round(best[0], 1), poly_pts=best[1],
                       ink_backed=best[2])
        else:
            rec["build"] = "no-closure"
            rec["why"] = "; ".join(sorted(whys))[:150]
    except R.RefuseSheet as e:
        rec["build"] = "REFUSE"
        rec["why"] = str(e).split("\n")[0][:120]
    except Exception as e:
        rec["build"] = "CRASH:" + type(e).__name__
        rec["why"] = str(e)[:120]
        rec["tb"] = traceback.format_exc(limit=3)
    out.append(rec)
    print(f"  {rec['build']:<12} {str(rec.get('extent_mm', '')):<16} "
          f"{str(rec.get('room_m2', '-')) + ' m2':<10} {rec['pdf'][:26]:<26} p{rec['page']:<3} "
          f"{rec['title']}")

json.dump({"reader_md5": READER_MD5, "reader_dirty": DIRTY,
           "census_reader_md5": census.get("reader_md5"), "pages": out},
          open(os.path.join(DATA, "closure.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
closed = [r for r in out if r["build"] == "CLOSED"]
print(f"\n  CLOSED a room : {len(closed)}/{len(out)}   <- THE REAL NUMBER (the gate count is not)")
print(f"  distinct PDFs closing : "
      f"{len({r['pdf'] for r in closed})} of {len({r['pdf'] for r in out})}")
