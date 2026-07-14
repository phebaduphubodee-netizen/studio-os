"""Corpus census + gate answer-key. Reads every page of every Bluehouse PDF and records:
  - the DRAWING TITLE field (the DESIGNER'S OWN label = the answer key)
  - whether the reader's gate accepts it, and if not, WHICH check ids failed
  - the raw signals the gate uses, so a fix can be evaluated without re-parsing 898 pages

Run this EVERY time the gate is touched; closure_run.py consumes its output.
Writes _private/plan-gate/census.json -- client filenames stay under _private/ (gitignored);
NOTHING here leaves the machine.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline", "scripts"))
os.chdir(REPO)

import fitz  # noqa: E402
import bluehouse_plan_reader as R  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Thai paths under piped cp1252

# PIN THE INSTRUMENT. A background agent silently edited this reader DURING the first census run,
# so half the corpus was scored against HEAD and half against a patched file, and `accept` moved
# 10 -> 16 with no run in between. Never again: the census records the exact bytes it measured.
READER = os.path.join("pipeline", "scripts", "bluehouse_plan_reader.py")
READER_MD5 = hashlib.md5(open(READER, "rb").read()).hexdigest()
_gs = subprocess.run(["git", "status", "--porcelain", READER], capture_output=True, text=True)
DIRTY = f"git status FAILED rc={_gs.returncode}" if _gs.returncode else _gs.stdout.strip()
print(f"reader md5={READER_MD5}  working-tree={'DIRTY: ' + DIRTY if DIRTY else 'clean (== HEAD)'}")

ROOT = os.path.join("_private", "discord", "MY-DATA-PEAT")
OUT_DIR = os.path.join(REPO, "_private", "plan-gate")
os.makedirs(OUT_DIR, exist_ok=True)

pdfs = []
for dirpath, _dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if fn.lower().endswith(".pdf"):
            pdfs.append(os.path.join(dirpath, fn))
pdfs.sort()
if not pdfs:
    sys.exit(f"no PDFs under {ROOT} -- the corpus is gitignored and absent on this machine. "
             "Refusing to write a 0-page census over a real one; a census of nothing is not "
             "a measurement.")

FAIL_RE = re.compile(r"\[FAIL\] (\w+\*?)")

rows = []
for pdf in pdfs:
    try:
        doc = fitz.open(pdf)
    except Exception as e:
        # the artifact claims EVERY page of EVERY PDF -- an unopenable file must appear in it,
        # or the answer-key denominator silently shrinks
        print("OPEN-FAIL", pdf, e)
        rows.append({"pdf": pdf, "page": -1, "accept": False, "fails": ["OPEN-FAIL"],
                     "open_fail": f"{type(e).__name__}: {e}"})
        continue
    n = len(doc)
    doc.close()
    for pg in range(n):
        row = {"pdf": pdf, "page": pg}
        # --- raw signals, read independently of the gate so a refusal never hides them
        try:
            d = fitz.open(pdf)
            page = d[pg]
            spans = R.page_spans(page)
            page_text = page.get_text()
            row["title"] = R.titleblock_field(spans, "DRAWING TITLE")
            tb, tb_why = R.titleblock_scale_denom(spans, page_text)
            row["tb_denom"] = tb
            drawings = page.get_drawings()
            row["has_border"] = any(
                round(dd.get("width") or 0, 2) == R.BORDER_PEN_PT for dd in drawings)
            # every black lone-quad, by pen weight -> is the 0.84 pen universal?
            pens = {}
            for dd in drawings:
                items = dd.get("items") or []
                if dd.get("type") != "s" or len(items) != 1 or items[0][0] != "qu":
                    continue
                c = dd.get("color")
                if c is None or sum(c) > R.MAX_COLOR_SUM:
                    continue
                w = round(dd.get("width") or 0, 2)
                pens[w] = pens.get(w, 0) + 1
            row["black_quad_pens"] = pens
            row["n_wall_pen"] = pens.get(R.WALL_PEN_PT, 0)
            d.close()
        except Exception as e:
            row["signal_error"] = f"{type(e).__name__}: {e}"

        # --- the gate's verdict
        try:
            R.read_bands(pdf, pg)
            row["accept"] = True
            row["fails"] = []
        except R.RefuseSheet as e:
            row["accept"] = False
            msg = str(e)
            row["fails"] = FAIL_RE.findall(msg)
            if not row["fails"]:
                row["fails"] = ["EARLY:" + msg.split("(")[0].strip()[:60]]
        except Exception as e:
            row["accept"] = False
            row["fails"] = ["CRASH:" + type(e).__name__]
            row["crash"] = traceback.format_exc(limit=2)
        rows.append(row)
    print(f"{pdf}  {n}pp", flush=True)

# --- ANSWER KEY, from the designer's own DRAWING TITLE. Two axes, not one:
#   TYPE   : is this a plan at all?           (แปลน / PLAN, vetoed by แบบขยาย = enlarged detail)
#   EXTENT : a plan OF WHAT?                  (a storey, or ONE ROOM blown up?)
# The extent axis is not cosmetic. This reader emits a FLOOR for build_floor. A sheet titled
# 'แปลนเฟอร์นิเจอร์ ห้องนอน 3,4' is a 12.0 x 4.8 m strip = two bedrooms; it has walls, a stated
# 1:50, a habitable footprint and ink on four sides, so EVERY geometric gate check passes on it.
# Only the title can tell a room from a storey. Scoring a title-based gate against a TYPE-only
# answer key cannot see this class at all -- that is the flattering-scorer shape, again.
PUA = range(0xF700, 0xF720)
def skel(t):
    return R.thai_skeleton("".join(c for c in (t or "") if ord(c) not in PUA))
DETAIL_SK, PLAN_SK, ROOM_SK = skel("แบบขยาย"), skel("แปลน"), skel("ห้อง")

for r in rows:
    s = skel(r.get("title"))
    if not s:
        r["k"], r["extent"] = "no-title", None
    elif DETAIL_SK in s:
        r["k"], r["extent"] = "DETAIL", "room"
    elif PLAN_SK in s or re.search(r"\bPLAN\b", r.get("title") or "", re.I):
        r["k"] = "PLAN"
        r["extent"] = "room" if ROOM_SK in s else "storey"
    else:
        r["k"], r["extent"] = "other", None

out = os.path.join(OUT_DIR, "census.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"reader_md5": READER_MD5, "reader_dirty": DIRTY, "pages": rows},
              f, ensure_ascii=False, indent=1)
print("WROTE", out, len(rows), "pages")
