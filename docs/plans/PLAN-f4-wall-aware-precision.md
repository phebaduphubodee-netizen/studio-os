# PLAN-f4-wall-aware-precision

> **สถานะ (2026-08-04): EXECUTED** — ทำครบตั้งแต่ 2026-07-07 (commits
> `1c6a13f`/`46f95c5`/`1d1721a`); ผลที่ `qa/reports/floorplancad-oracle-walls-2026-07-07.md`
> (F4 precision 2.9%→3.4%, candidates −23,651 โดย recall คงเดิมตามเงื่อนไขแผน);
> เลนต่อยอดเป็น `wall_detect.py`/`wall_aware_lane.py` แล้ว (ย้ายจาก root มา
> docs/plans/ 2026-08-04 ตาม outside-review ข้อ 7)

Rank: 1/5

## Goal

**The measured number this moves: F4 opening-candidate precision on the FloorPlanCAD
test-00 mm lane — currently 2.9 % (4,569 matched / 159,582 candidates) — must go UP,
via the candidate flood (159,582) going DOWN.**
(Blind baseline of record: `qa/reports/floorplancad-baseline-2026-07-06.md:38-43`.)

Build the ORACLE wall lane: the FloorPlanCAD adapter exports per-sheet wall geometry
(raw semantic class 1 = wall) as a `wall_lines` channel in gt.json; the reader's
baseline runner feeds it into `glazing_candidates.promote()` at its single injection
point (`svg_plan_reader.py:168`), labeled `wall_source="oracle"` in every cards.jsonl
row, every pred meta, and the report title. The oracle lane uses GT-side information —
it measures the CEILING of wall-aware precision and is NEVER the honest headline. The
annotation-blind headline stays the 2026-07-06 empty-wall run, unchanged.

Explicitly NOT a goal (critic-corrected from the session spec): detection recall
(9.8 %) will NOT move. Wall-merge deaths happen inside `plan_cluster.cluster_segments`
(`svg_plan_reader.py:158`), which never sees the wall set in this slice. Expect the
detection line in the oracle report to be numerically IDENTICAL to the blind run
(matched 1,014 / GT 10,347 / pred 7,097). If it moves, walls leaked into the element
lane — that is a bug, not a win.

## Why now (leverage)

- The blind baseline names this "the single number that moves" and the cheapest lever
  (`qa/reports/floorplancad-baseline-2026-07-06.md:60-63,88-92`): with an empty wall
  set, every double-line wall face pairs with itself at 40–250 mm and scores >= 2
  (`glazing_candidates.py:306-307`) — the flood IS the corpus's own wall ink.
- Inside `promote()` a wall set does exactly two things, both already built and
  mutation-pinned: coverage suppression of wall-covered thin runs
  (`glazing_candidates.py:288,295`) and 0–2 endpoint wall-contact score (`:305`).
  **Zero changes to `glazing_candidates.py` are needed or allowed.**
- The adapter change is a mirror of the existing GLAZING branch
  (`floorplancad_adapter.py:322-328`) — wall geometry is currently thrown away at
  `:329-333` (count-only).
- `benchmark_reader.score_pair` provably ignores extra top-level gt keys — it reads
  only `meta.units`, `elements`, `openings` (`benchmark_reader.py:309-328`), so
  `wall_lines` needs no engine change; the adapter `--selftest` re-proves it corpus-wide.

## Files to touch

| Path | Status | What |
|---|---|---|
| `pipeline/scripts/floorplancad_adapter.py` | [EXISTS] | wall pool in `parse_svg` (:265), `wall_lines` emission in `convert` (:529-554), version bump (:59), manifest `n_wall` (:594-603) |
| `pipeline/scripts/test_floorplancad_adapter.py` | [EXISTS] | +2 tests (wall export incl. instanced; mm scaling) |
| `pipeline/scripts/svg_plan_reader.py` | [EXISTS] | `read_sheet` wall params (:143,:167-192), `run_baseline` `walls=` kwarg (:227-294), report honesty (:297-351), CLI (:364-374), docstring usage line (:4), import (:58) |
| `pipeline/scripts/test_svg_plan_reader.py` | [EXISTS] | +4 tests (blind meta unchanged; oracle suppression; in-gap survival; runner labeling + refusal) |
| `qa/reports/floorplancad-oracle-walls-2026-07-07.md` | [NEW] | committed aggregate summary, blind-vs-oracle, NOT-headline banner |
| `docs/strategy.md` | [EXISTS] | append one dated session entry at tail (never rewrite history) |
| `C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1\` | [NEW, outside repo] | regenerated gt with wall_lines (5,502 files + manifest.jsonl + summary.md) |
| `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle\` | [NEW, outside repo] | oracle run artifacts (cards.jsonl, preds/, overlays/, report.md) |

**Do-not-touch (read-only in this slice):** `pipeline/scripts/glazing_candidates.py`,
`pipeline/scripts/benchmark_reader.py`, `pipeline/scripts/plan_cluster.py`,
`C:\Users\teza_\studio-datasets\floorplancad\gt-test-00\` and `baseline-test-00\`
(the committed baseline's inputs/outputs — provenance of commits 7b86720/34c1a08),
plus the four hook-protected paths (`qa/thresholds.yaml`, `knowledge/codes-th/**`,
`.claude/settings.json`, `.gitattributes`).

All python commands below run from `c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts`
unless stated otherwise (the modules use flat imports, `svg_plan_reader.py:56-59`).
`python` and `python3` both resolve to Python 3.12.10 on this machine (`python3` is a
user-local shim copy).

## Implementation order

### Step 0 — Preflight (verify before touching anything)

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat
python3 -m pytest pipeline/scripts/ -q
```
Expected: `465 passed` (~6 s; verified green 2026-07-07). Then confirm the corpus:
```powershell
(Get-ChildItem C:\Users\teza_\studio-datasets\floorplancad\gt-test-00 -Filter *.gt.json | Measure-Object).Count
```
Expected: `5502`. If either fails, STOP — the environment is not the one this plan was
written against.

### Step 1 — Adapter: collect wall geometry in `parse_svg`

File: `pipeline/scripts/floorplancad_adapter.py`.

1a. Line 272 currently reads:
```python
    glazing, dim_texts, dim_segs = [], [], []
```
Change to:
```python
    glazing, walls, dim_texts, dim_segs = [], [], [], []
```

1b. Insert a wall branch AFTER the GLAZING branch and BEFORE the count-only branch.
The count-only branch is (currently lines 329-333):
```python
            if no_inst or kind in COUNT_ONLY_KINDS:
                counts["stuff"][kind] += 1
                if not no_inst:        # instanced wall/row_chairs/parking: never an element
                    counts["instanced_stuff"] += 1
                continue
```
Insert immediately ABOVE it:
```python
            if kind == "wall":
                # oracle wall channel: export geometry for BOTH stuff (-1) and
                # instanced wall prims (excluding instanced walls leaves oracle gaps);
                # counters preserved exactly as the count-only branch produced them
                for (a, b) in (path_segments(el.get("d")) if tag == "path"
                               else _shape_segs(el, tag)):
                    walls.append({"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1],
                                  "layer": layer})
                counts["stuff"][kind] += 1
                if not no_inst:
                    counts["instanced_stuff"] += 1
                continue
```
Leave `COUNT_ONLY_KINDS` (:83) unchanged — "wall" simply never reaches it now.
Do NOT touch the GLAZING branch: curtain_wall (class 2) stays in `glazing_lines`
(decision recorded below in Edge cases #14).

1c. Change the `parse_svg` return (line 347) from
`return inst_pool, glazing, dim_texts, dim_segs, counts` to:
```python
    return inst_pool, glazing, walls, dim_texts, dim_segs, counts
```
The ONLY caller is `convert()` at line 484 (verified by grep — no test calls
`parse_svg` directly).

### Step 2 — Adapter: emit `wall_lines` in `convert()`, bump version

2a. Line 484: change to
```python
    inst_pool, glazing, walls, dim_texts, dim_segs, counts = parse_svg(svg_path)
```

2b. In the `convert()` return dict, after the `"glazing_lines": [...]` entry
(lines 549-553), add a sibling key using the identical scaling pattern:
```python
        "wall_lines": [
            {**w, "x1": round(w["x1"] * s, 1), "y1": round(w["y1"] * s, 1),
             "x2": round(w["x2"] * s, 1), "y2": round(w["y2"] * s, 1)}
            for w in walls
        ],
```
`s` is already in scope (`s = scale if scale is not None else 1.0`, line 528). This
means wall_lines are in mm on `units=="mm"` files — the reader must NEVER rescale them.

2c. Line 59: `ADAPTER_VERSION = "floorplancad_adapter v1"` → `"floorplancad_adapter v1.1"`.
(No test pins the version string — verified by grep.)

2d. In `run_batch`'s ok-manifest row (lines 594-603), after
`"n_glazing": len(doc["glazing_lines"]),` add:
```python
                "n_wall": len(doc["wall_lines"]),
```
(The manifest test `test_json_roundtrip_and_batch_manifest` at
`test_floorplancad_adapter.py:389-406` asserts specific keys exist, never an exact key
set — adding one is safe.)

### Step 3 — Adapter tests (+2)

Append to `pipeline/scripts/test_floorplancad_adapter.py` (e.g. after
`test_curtain_wall_and_railing_go_to_glazing_channel`, line 126):

```python
def test_wall_lines_exported_including_instanced():
    # class-1 wall geometry is exported for BOTH stuff (-1) and instanced prims;
    # counters must stay exactly what the old count-only branch produced
    body = layer("WALL", prim(1, -1, "M 0,0 L 99,0") + prim(1, 7, "M 0,10 L 50,10"))
    doc = _convert(body)
    assert doc["elements"] == [] and doc["openings"] == []
    got = {(w["x1"], w["y1"], w["x2"], w["y2"]) for w in doc["wall_lines"]}
    assert got == {(0.0, 0.0, 99.0, 0.0), (0.0, 10.0, 50.0, 10.0)}
    assert doc["meta"]["stuff_counts"] == {"wall": 2}
    assert doc["meta"]["instanced_stuff"] == 1

def test_wall_lines_scaled_when_calibrated():
    doc = _convert(CAL + layer("WALL", prim(1, -1, "M 0,50 L 60,50")))
    w = doc["wall_lines"][0]
    assert (w["x1"], w["x2"], w["y1"]) == (0.0, 6000.0, 5000.0)
```

Check: `python3 -m pytest pipeline/scripts/test_floorplancad_adapter.py -q` from repo
root → all pass (44 existing + 2 new = 46). The pre-existing
`test_stuff_wall_counted_not_emitted` (:115-118) must STILL pass — it asserts
`stuff_counts == {"wall": 3}` and empty elements/openings, both preserved by Step 1b.

### Step 4 — Reader: `read_sheet` learns an optional wall set

File: `pipeline/scripts/svg_plan_reader.py`.

4a. Import line 58: `from glazing_candidates import promote, run_endpoints` →
```python
from glazing_candidates import axis_run, promote, run_endpoints
```

4b. Signature line 143:
```python
def read_sheet(svg_path, scale_mm_per_unit, close_mm=CLOSE_MM,
               wall_segs=None, wall_source=None):
```

4c. Replace lines 167-168 (`openings = []` / `cands, stats = promote(segs, wall_segs=[])`)
with:
```python
    openings = []
    w_segs, n_diag = [], 0
    if wall_source == "oracle":
        # GT-side wall geometry, ALREADY in mm (adapter scales at emission) -- never
        # rescale here. Raw 2-point segments [[x1,y1],[x2,y2]], exactly what promote
        # expects; diagonal segs are counted (axis_run=None -> they contribute nothing
        # to suppression or contact) rather than silently vanishing.
        w_segs = list(wall_segs or [])
        n_diag = sum(1 for s in w_segs if axis_run(s) is None)
    cands, stats = promote(segs, wall_segs=w_segs)
```
When `wall_source is None` this is behavior-identical to today (`w_segs == []`).

4d. The function currently ends with `return { ... }` (lines 176-192). Bind it to a
name and add the conditional meta AFTER the dict literal, keeping the existing dict
byte-identical:
```python
    pred = {
        "meta": { ... existing content unchanged ... },
        "elements": elements,
        "openings": openings,
    }
    if wall_source is not None:
        pred["meta"]["wall_source"] = wall_source
        pred["meta"]["wall_segs_n"] = len(w_segs)
        pred["meta"]["wall_diag_unusable"] = n_diag
    return pred
```
The keys are added ONLY in wall mode — the blind lane's meta must not change by one key
(that is what keeps the corpus pred byte-identity check in Acceptance #2 true).

### Step 5 — Reader: `run_baseline` grows `walls=` (keyword, LAST)

5a. Signature line 227:
```python
def run_baseline(svg_dir, gt_dir, out_dir, limit=None, overlays=0, walls=None):
```
(`walls` must be appended last with default `None` — the existing runner test calls
`R.run_baseline(svg_dir, gt_dir, out_dir)` positionally, `test_svg_plan_reader.py:252`.)

5b. Preflight, inserted after the `limit` slice (lines 234-235) and before
`cards = []`:
```python
    if walls == "oracle":
        first = json.load(open(gt_files[0], encoding="utf-8"))
        if "wall_lines" not in first:
            raise SystemExit("walls oracle: first gt file has no 'wall_lines' key -- "
                             "regenerate the gt dir with floorplancad_adapter v1.1 "
                             "--batch before running the oracle lane")
```
(Valid check: post-Step-2 `convert()` ALWAYS emits the key, even as `[]`.)

5c. Add `wall_stats = {"segs": 0, "diagonal": 0} if walls else None` next to
`overlay_failed = 0` (line 238).

5d. Label every row. The `row()` closure (lines 244-246) becomes:
```python
    def row(obj):
        if walls:
            obj = {**obj, "wall_source": walls}
        rows_fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        rows_fh.flush()
```
Blind mode: no key at all (old cards stay schema-comparable).

5e. Replace the single `pred = read_sheet(...)` call (line 261) with — INSIDE the
existing per-sheet `try` (a malformed `wall_lines` must cost one counted error row,
never the run):
```python
            if walls == "oracle":
                wsegs = [[[w["x1"], w["y1"]], [w["x2"], w["y2"]]]
                         for w in gt["wall_lines"]]
                pred = read_sheet(sfp, gt["meta"]["scale_mm_per_unit"],
                                  wall_segs=wsegs, wall_source="oracle")
            else:
                pred = read_sheet(sfp, gt["meta"]["scale_mm_per_unit"])
```
Use strict `gt["wall_lines"]` indexing, NOT `.get(...) or []` — in a mixed old/new gt
dir a missing key must become a counted `"error"` row, never a silent empty-wall sheet
wearing the oracle label.

5f. After `cards.append(card)` (line 266) add:
```python
            if walls:
                wall_stats["segs"] += pred["meta"]["wall_segs_n"]
                wall_stats["diagonal"] += pred["meta"]["wall_diag_unusable"]
```

5g. Report call (lines 288-289) becomes:
```python
    report = render_baseline_report(cards, skipped, len(gt_files), time.time() - t0,
                                    overlay_failed=overlay_failed,
                                    walls=walls, wall_stats=wall_stats)
```

### Step 6 — Reader: report honesty + CLI + docstring

6a. `render_baseline_report` (line 297) signature:
```python
def render_baseline_report(cards, skipped, n_total, secs, overlay_failed=0,
                           walls=None, wall_stats=None):
```
Leave the empty-cards early return (lines 298-299) untouched
(`test_report_without_cards_is_honest` pins "no sheets scored").

6b. Replace the fixed title line
`"# FloorPlanCAD baseline -- OUR reader vs gt (first real numbers)",` (line 312) with:
```python
        ("# FloorPlanCAD baseline -- OUR reader vs gt (first real numbers)"
         if not walls else
         f"# FloorPlanCAD baseline -- {walls.upper()}-WALL lane "
         f"(wall_source={walls}; NOT the blind headline)"), "",
```
(the `, ""` keeps the blank second element the list already has — check you did not
duplicate it).

6c. The honesty-notes block is ONE `L += [...]` list-literal statement spanning lines
337-350 — you cannot place an `if` statement inside a list literal. SPLIT it into two
statements: end the first `L += [...]` right after the element-precision bullet; then
insert the `if walls == "oracle":` block below; then close with a new final statement
`L += ["", f"reader: {READER_VERSION}"]` (the wall bullets must land BEFORE the
`reader:` footer):
```python
    if walls == "oracle":
        L += ["- WALL SOURCE = ORACLE: promote() received the GT's own wall_lines "
              "(answer-key side). This lane measures the CEILING of wall-aware "
              "precision and must NEVER be quoted as the blind headline "
              "(that remains qa/reports/floorplancad-baseline-2026-07-06.md).",
              f"- oracle wall segs fed: {wall_stats['segs']}; diagonal/unusable "
              f"(axis_run=None -- contribute nothing to suppression or contact): "
              f"{wall_stats['diagonal']}"]
```

6d. CLI: replace lines 365-374 — the option loop AND the existing `run_baseline(...)`
call at line 374 (the snippet below already ends with that call; after the edit there
must be exactly ONE `run_baseline` call in `main()`, or every `--baseline` invocation
runs the entire corpus twice) — with:
```python
        kw = {}
        rest = argv[5:]
        while rest:
            if len(rest) >= 2 and rest[0] in ("limit", "overlays") and rest[1].isdigit():
                kw[rest[0]] = int(rest[1])
            elif len(rest) >= 2 and rest[0] == "walls" and rest[1] in ("oracle",):
                kw["walls"] = rest[1]
            else:
                raise SystemExit(f"bad option {rest[0]!r} -- expected: "
                                 f"[limit N] [overlays K] [walls oracle]\n\n{__doc__}")
            rest = rest[2:]
        run_baseline(argv[2], argv[3], argv[4], **kw)
```
(The current loop rejects any non-digit value — `"oracle".isdigit()` is False — so
without this exact restructure the CLI exits `bad option 'walls'`.)

6e. Module docstring usage (line 4) becomes:
```
    python svg_plan_reader.py --baseline <svg-dir> <gt-dir> <out-dir> [limit N] [overlays K] [walls oracle]
```

### Step 7 — Reader tests (+4)

Append to `pipeline/scripts/test_svg_plan_reader.py` (after
`test_read_sheet_empty_svg`, line 222):

```python
def test_blind_lane_meta_has_no_wall_keys(tmp_path):
    # the blind headline lane must stay byte-identical: wall keys appear ONLY when a
    # wall_source is passed
    pred = R.read_sheet(_sheet_svg(tmp_path), 100.0)
    assert "wall_source" not in pred["meta"]
    assert "wall_segs_n" not in pred["meta"]


def test_oracle_walls_suppress_wall_face_pairs(tmp_path):
    # the 159,582-candidate flood: double-line wall faces pair with each other; with
    # the SAME ink handed in as oracle walls, collinear coverage (>=80%, gap_tol=0)
    # must kill exactly those runs. Also pins: wall segs are RAW 2-point mm segments
    # (merged-run dicts fail _valid_seg silently) and are NOT rescaled in read_sheet
    # (a double-scale would move them 100x away and suppress nothing).
    fp = _write(tmp_path, "w.svg", '<path d="M 20,10 L 20,40"/>\n'
                                   '<path d="M 22,10 L 22,40"/>\n')
    blind = R.read_sheet(fp, 100.0)
    assert blind["openings"], "fixture rotted: blind lane should flood here"
    walls = [[[2000.0, 1000.0], [2000.0, 4000.0]],
             [[2200.0, 1000.0], [2200.0, 4000.0]]]
    oracle = R.read_sheet(fp, 100.0, wall_segs=walls, wall_source="oracle")
    assert oracle["openings"] == []
    assert oracle["meta"]["wall_source"] == "oracle"
    assert oracle["meta"]["wall_segs_n"] == 2
    assert oracle["meta"]["opening_candidate_stats"]["dropped_wall_covered"] >= 2


def test_oracle_walls_do_not_kill_gap_candidates(tmp_path):
    # sliding-door-in-gap (the module's headline case): a thin pair INSIDE a wall gap
    # must survive coverage (promote merges coverage walls with gap_tol=0) and now
    # earn wall contact 2 -> strong
    fp = _write(tmp_path, "g.svg", '<path d="M 20,21 L 20,29"/>\n'
                                   '<path d="M 21,21 L 21,29"/>\n')
    walls = [[[2000.0, 0.0], [2000.0, 2000.0]],
             [[2000.0, 3000.0], [2000.0, 5000.0]]]
    pred = R.read_sheet(fp, 100.0, wall_segs=walls, wall_source="oracle")
    assert pred["openings"], "in-gap pair suppressed: bridged wall merging regression"
    assert pred["openings"][0]["tier"] == "strong"
    assert all(o["type"] == "candidate" for o in pred["openings"])


def test_run_baseline_oracle_labels_rows_and_requires_wall_lines(tmp_path):
    import shutil

    import pytest
    svg_dir = os.path.join(str(tmp_path), "svg")
    gt_dir = os.path.join(str(tmp_path), "gt")
    os.makedirs(svg_dir)
    os.makedirs(gt_dir)
    shutil.copy(_sheet_svg(tmp_path), os.path.join(svg_dir, "s1.svg"))
    gt = {"meta": {"units": "mm", "scale_mm_per_unit": 100.0},
          "elements": [], "openings": [], "wall_lines": []}
    with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
        json.dump(gt, fh)
    out_dir = os.path.join(str(tmp_path), "out")
    cards, skipped = R.run_baseline(svg_dir, gt_dir, out_dir, walls="oracle")
    rows = [json.loads(l) for l in open(os.path.join(out_dir, "cards.jsonl"),
                                        encoding="utf-8")]
    assert rows and all(r.get("wall_source") == "oracle" for r in rows)
    rep = open(os.path.join(out_dir, "report.md"), encoding="utf-8").read()
    assert "ORACLE-WALL" in rep and "NOT the blind headline" in rep
    # a pre-wall gt dir must be refused loudly, never silently run empty-walled
    gt2_dir = os.path.join(str(tmp_path), "gt2")
    os.makedirs(gt2_dir)
    with open(os.path.join(gt2_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": {"units": "mm", "scale_mm_per_unit": 100.0},
                   "elements": [], "openings": []}, fh)
    with pytest.raises(SystemExit):
        R.run_baseline(svg_dir, gt2_dir, os.path.join(str(tmp_path), "out2"),
                       walls="oracle")
```

Geometry sanity for the two read_sheet tests (pre-verified against
`glazing_candidates.py` DEFAULTS :64-73): scale 100 mm/unit makes the first fixture two
3,000 mm verticals 200 mm apart (pair_gap 40–250 → they pair, length >= 1000 → blind
score 3 each); as oracle walls they cover themselves 100 % >= covered_frac 0.8 →
suppressed. Second fixture: 800 mm pair 100 mm apart at c=2000/2100; wall spans end at
y=2000 / start at y=3000, so coverage overlap is zero and endpoint distances are
100 mm <= end_tol 250 → run at c=2000 scores 2(pair)+2(contacts)=4 strong (first in the
sorted candidate list); the c=2100 run's same-axis walls sit 100 mm > covered_tol 12
off its line → sideways-parallel → 0 contacts.

**Check before moving on:**
```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat
python3 -m pytest pipeline/scripts/ -q
```
Expected: `471 passed` (465 + 6), 0 failures. The blindness suite
(`test_read_sheet_is_annotation_blind`, `..._at_corpus_density`,
`..._on_real_corpus_sheet`, `test_reader_source_never_names_annotation_attrs`) must all
still pass unmodified.

### Step 8 — Regenerate GT with wall_lines (corpus, outside repo)

Do NOT write into `gt-test-00` (it is the committed baseline's input). New dir:

```powershell
Start-Process -FilePath python -ArgumentList 'floorplancad_adapter.py','--batch','C:\Users\teza_\studio-datasets\floorplancad\test-00','C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1' -WorkingDirectory 'c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts' -RedirectStandardOutput 'C:\Users\teza_\studio-datasets\floorplancad\gt-w1-batch.log' -RedirectStandardError 'C:\Users\teza_\studio-datasets\floorplancad\gt-w1-batch.err'
```
Done marker: `gt-test-00-w1\summary.md` exists (written after the loop,
`floorplancad_adapter.py:624-627`). Historical duration unrecorded — budget 5–30 min;
progress prints every 500 files to the log. Poll with:
```powershell
Test-Path C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1\summary.md; Get-Content C:\Users\teza_\studio-datasets\floorplancad\gt-w1-batch.log -Tail 2
```

Then verify (python, NOT PowerShell JSON):
```powershell
python3 -c "import glob,json
gt='C:/Users/teza_/studio-datasets/floorplancad/gt-test-00-w1'
files=glob.glob(gt+'/*.gt.json'); print('gt files:', len(files))
man=[json.loads(l) for l in open(gt+'/manifest.jsonl',encoding='utf-8')]
print('ok:false rows:', sum(1 for m in man if not m['ok']))
print('total wall segs:', sum(m.get('n_wall',0) for m in man))"
```
Expected: `gt files: 5502`, `ok:false rows: 0`, total wall segs a large positive number.

Equivalence spot-check (the adapter edit must change NOTHING except adding wall_lines
and the version string):
```powershell
python3 -c "import json
for b in ('0000-0003','0000-0009','0000-0010'):
    old=json.load(open(f'C:/Users/teza_/studio-datasets/floorplancad/gt-test-00/{b}.gt.json',encoding='utf-8'))
    new=json.load(open(f'C:/Users/teza_/studio-datasets/floorplancad/gt-test-00-w1/{b}.gt.json',encoding='utf-8'))
    new.pop('wall_lines'); new['meta']['adapter']=old['meta']['adapter']
    print(b, 'EQUAL' if new==old else 'DRIFT -- STOP AND DIAGNOSE')"
```
All three must print EQUAL. If DRIFT: your Step 1/2 edit changed element/opening/meta
emission — diff the dicts and fix before any run.

Selftest (standing gt-vs-gt schema gate):
```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
python3 floorplancad_adapter.py --selftest C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1
```
Expected final line: `selftest PASS: adapter output is benchmark_reader-clean`
(also proves score_pair ignores the new wall_lines key on all 5,502 files). Runtime:
a few minutes, foreground OK.

### Step 9 — Smoke: oracle vs blind on the same 200 gt files

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
python3 svg_plan_reader.py --baseline C:\Users\teza_\studio-datasets\floorplancad\test-00 C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1 C:\Users\teza_\studio-datasets\floorplancad\smoke-oracle limit 200 walls oracle
python3 svg_plan_reader.py --baseline C:\Users\teza_\studio-datasets\floorplancad\test-00 C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1 C:\Users\teza_\studio-datasets\floorplancad\smoke-blind limit 200
```
Each ~1–3 min foreground (historical blind pace: 200 files / ~102 scored / 56 s).
Read both `report.md` files. Required before proceeding:
- oracle F4 line's `pred` count strictly BELOW blind's, precision strictly ABOVE;
- oracle detection line numerically IDENTICAL to blind's (same matched/recall/precision);
- oracle title contains `ORACLE-WALL` + `NOT the blind headline`.
If precision did NOT rise on the smoke, stop and run the score-histogram diagnostic
(Step 11) on `smoke-oracle\preds` before any full run.

### Step 10 — Full oracle corpus run (detached — NEVER the in-tool background lane)

The blind full run took 865 s wall-clock; the oracle lane adds per-sheet
`merge_runs`+`ends_near_walls` over the wall set — budget 15–45 min. The in-tool
background Bash lane hard-caps at 10 min, so launch detached:

```powershell
Start-Process -FilePath python -ArgumentList 'svg_plan_reader.py','--baseline','C:\Users\teza_\studio-datasets\floorplancad\test-00','C:\Users\teza_\studio-datasets\floorplancad\gt-test-00-w1','C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle','overlays','6','walls','oracle' -WorkingDirectory 'c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts' -RedirectStandardOutput 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle-run.log' -RedirectStandardError 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle-run.err'
```
Done marker: `baseline-test-00-oracle\report.md` exists (report is written LAST,
`svg_plan_reader.py:288-291`; cards.jsonl streams row-by-row so a mid-run death keeps
finished rows). Poll:
```powershell
Test-Path C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle\report.md; Get-Content C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-oracle-run.log -Tail 2
```
Expected in report.md: `2245 scored / 5502 gt files (skipped: {"svg-unit": 3257,
"svg-missing": 0, "error": 0})`.

### Step 11 — Analyze + write the committed report

Row-label check + score histogram (python only — PowerShell 5.1 `ConvertFrom-Json`
chokes on the cards' deep keys):
```powershell
python3 -c "import json
rows=[json.loads(l) for l in open('C:/Users/teza_/studio-datasets/floorplancad/baseline-test-00-oracle/cards.jsonl',encoding='utf-8')]
print('rows:',len(rows),'unlabeled:',sum(1 for r in rows if r.get('wall_source')!='oracle'))"
python3 -c "import json,glob
from collections import Counter
h=Counter(); n=0
for fp in glob.glob('C:/Users/teza_/studio-datasets/floorplancad/baseline-test-00-oracle/preds/*.pred.json'):
    p=json.load(open(fp,encoding='utf-8')); n+=1
    for o in p['openings']: h[o['score']]+=1
print(n,'preds; score histogram:',dict(sorted(h.items())))"
```
Blind lane could only produce scores 2 (pair) and 3 (pair+length). Oracle adds contact
points: scores 4–5 are wall-anchored pairs; a large NEW population at score 2 that
wasn't there blind = pairless contact-only runs (dim lines spanning wall-to-wall) — if
precision disappointed, this histogram says why. Do NOT tune constants in response
(see Do NOT).

Write `qa/reports/floorplancad-oracle-walls-2026-07-07.md` [NEW] containing, in order:
1. Banner line: **"ORACLE LANE — uses GT-side wall geometry. NOT the blind headline;
   the honest baseline of record remains floorplancad-baseline-2026-07-06.md."**
2. A blind-vs-oracle table with EXACT fractions from both report.md files:
   detection recall/precision (must be identical), F4 recall, F4 precision, F4 n_pred,
   per-type recall for door/sliding/window/opening.
3. The oracle wall-seg totals + diagonal/unusable count (from the report honesty line).
4. Score-histogram note (contact-term population, from the snippet above).
5. What this ceiling licenses next: a `wall_source="self"` honest lane (own-ink wall
   hypothesis) and the swing-door arc detector (separate plan items).

Append one dated entry to `docs/strategy.md` at the tail (never rewrite existing
entries): what ran, the two precision numbers, the labeled-oracle honesty rule, path to
artifacts.

### Step 12 — OPTIONAL (do not block acceptance): first own-wall hypothesis, `walls self`

Only if Steps 0–11 are green and time remains. The honest lane derives walls from the
sheet's own ink (annotation-blind by construction):
- `svg_plan_reader.py`: add constant `SELF_WALL_MIN_MM = 2500.0` near line 66; extend
  the Step-4c branch with:
  ```python
    elif wall_source == "self":
        w_segs = [list(run_endpoints(r)) for r in merge_runs(segs)
                  if r["length"] >= SELF_WALL_MIN_MM]
  ```
  (add `merge_runs` to the import line 58); extend the CLI tuple to
  `("oracle", "self")` and the usage strings; extend Step-5e with a
  `elif walls == "self":` call passing `wall_source="self"`; report title picks up
  `SELF-WALL` automatically; add a self-lane honesty bullet ("wall hypothesis derived
  from the sheet's own ink; eligible as an honest headline lane").
- Run into `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-selfwalls`
  (same detached pattern). Report its precision honestly next to blind and oracle in
  the qa report — including if it is WORSE than blind.
- Add one test mirroring `test_oracle_walls_suppress_wall_face_pairs` but with
  `wall_source="self"` and no `wall_segs` (long parallel ink 200 mm apart >= 2,500 mm
  self-suppresses).

### Step 13 — Wrap

Per repo ritual: scrutinize the diff FIRST (run the `scrutinize` skill if available;
otherwise re-read every hunk against this plan's Edge cases), then separate logical
commits — suggested:
1. `floorplancad_adapter: export class-1 wall geometry as wall_lines (oracle wall channel)` — adapter + its 2 tests
2. `svg_plan_reader: labeled oracle-wall lane for promote() (wall_source=oracle)` — reader + its 4 tests
3. `qa: oracle-wall F4 precision report + strategy entry` — qa report + strategy.md

Stage files EXPLICITLY by path. NEVER `git add -A`. Do NOT push.

## Edge cases a weaker model would miss (all personally verified in code)

1. **Merged runs as wall_segs are SILENTLY inert.** `promote` filters coverage walls
   through `_valid_seg` (`glazing_candidates.py:288`) and `_valid_seg` is
   `len(s) == 2 and len(s[0]) == 2 and len(s[1]) == 2` (`pdf_extract_walls.py:32-36`) —
   a 7-key run dict fails it without error; `ends_near_walls` calls `axis_run(s)` which
   also returns None on dicts (`glazing_candidates.py:174-178`). Result: wall set does
   nothing, numbers look like blind, no crash. Pass RAW `[[x1,y1],[x2,y2]]` only —
   pinned by `test_oracle_walls_suppress_wall_face_pairs`.
2. **Double-scaling kills the lane silently.** gt `wall_lines` are already mm
   (`convert()` multiplies by `s` at emission — Step 2b mirrors
   `floorplancad_adapter.py:549-553`); `read_sheet` scales only SVG ink
   (`svg_plan_reader.py:147`). Rescaling walls by `s` again moves them ~100× away:
   coverage/contact never fire, zero errors. Same pin test catches it (fixture scale 100).
3. **gap_tol=0 for coverage-wall merging is sacred and lives INSIDE promote**
   (`glazing_candidates.py:285-288` comment + code). Do not pre-merge, bridge, or
   "unify" wall handling — bridged gaps mark sliding-door ink inside a wall gap as
   "already covered" (pinned `test_glazing_candidates.py:218-226`, and reader-level by
   `test_oracle_walls_do_not_kill_gap_candidates`). This slice edits
   `glazing_candidates.py` NOT AT ALL.
4. **promote()'s stats and candidate key sets are pinned EXACTLY**
   (`test_glazing_candidates.py:254-263` asserts `set(stats.keys()) == {...8 keys...}`).
   The diagonal-wall count therefore goes in the PRED META
   (`wall_diag_unusable`), never into promote's stats or candidate dicts.
5. **The static blindness tripwire scans `svg_plan_reader.py` tokens**
   (`test_svg_plan_reader.py:120-140`): needles `semantic`, `inkscape`, `INK_NS`,
   `instance_id` in any non-string/non-comment token, and `semantic-id`/`instance-id`/
   `inkscape` in any string literal outside the module docstring. Never name a reader
   identifier like `semantic_walls`. Strings `"oracle"`, `"wall_lines"`,
   `"wall_source"` are safe. The ADAPTER is exempt (it IS the GT side; tripwire only
   reads `R.__file__`).
6. **The strip-equivalence tests do NOT guard meta bloat** — both twins get any new
   meta key, so they'd still pass. Blind-lane purity is guarded by (a) adding wall meta
   keys ONLY under `wall_source is not None` (Step 4d), (b)
   `test_blind_lane_meta_has_no_wall_keys`, and (c) Acceptance #2's corpus byte-identity
   check (verified to hold pre-change on 2026-07-07: `read_sheet` on
   `test-00\0000-0009.svg` == committed `baseline-test-00\preds\0000-0009.pred.json`,
   45 openings, 339 thin segs).
7. **The CLI option loop rejects non-digit values** (`svg_plan_reader.py:368-369`):
   without the Step-6d restructure, `walls oracle` exits
   `bad option 'walls'`. Both digit options must KEEP their `.isdigit()` validation.
8. **Preflight key-presence is valid only because Step 2b makes `convert()` ALWAYS
   emit `wall_lines`** (even `[]`). Per-sheet access must be STRICT
   (`gt["wall_lines"]`), so a straggler old gt file in a mixed dir becomes a counted
   `"error"` row (the per-sheet try at `svg_plan_reader.py:250-282`), never a silently
   empty-walled sheet wearing the oracle label.
9. **Wall conversion must sit INSIDE the per-sheet try** — the runner's row-accounting
   contract is pinned: every gt file yields exactly one cards.jsonl row and exceptions
   increment `skipped["error"]` (`test_svg_plan_reader.py:225-269`); an overlay failure
   must still never error-count a scored sheet (`svg_plan_reader.py:269-277`,
   test `:277-284`).
10. **Detection recall must come out EXACTLY 9.8 % (1,014/10,347), precision 14.3 %
    (1,014/7,097)** — `cluster_segments` (`svg_plan_reader.py:158`) never sees walls.
    The session spec's "detection may also improve — measure" is WRONG for this scope
    (critic-corrected): any detection movement means walls leaked into the element
    lane. Treat drift as a bug.
11. **The contact term can ADD candidates:** with walls present, a pairless run with
    two wall contacts scores 2 = weak (`glazing_candidates.py:306-307`) — dimension
    lines spanning wall-to-wall enter the pool. The flood-kill (coverage suppression of
    wall-face pairs) is expected to dominate, but if precision does not rise, run the
    Step-11 score histogram and REPORT the finding; do not tune.
12. **Some window/sliding recall loss is possible and must be watched, not hidden:**
    a GT window whose thin runs lie collinear (<= covered_tol 12 mm) with CONTIGUOUS
    wall ink covering >= 80 % gets suppressed. Walls usually break at openings (which
    is why gap_tol=0 protects the gap cases). Guards: sliding recall >= 0.78 (blind
    0.878 = 733/835), window >= 0.80 (blind 0.902 = 2,850/3,160). Breach = inspect the
    6 overlays and the worst sheets' cards; still no constant-tuning.
13. **Instanced wall prims (class 1, instance-id != -1) are INCLUDED in wall_lines**
    (decision, per the map's open question: excluding them leaves oracle gaps), while
    `stuff_counts["wall"]` and `instanced_stuff` stay EXACTLY as v1 produced them
    (Step 1b replicates the old branch's counters; the Step-8 equivalence check
    normalizes only `wall_lines` + `meta.adapter`, so any counter drift fails it).
14. **curtain_wall (class 2) stays OUT of the wall set** (decision, flagged not
    buried): it is glazing ink already exported in `glazing_lines`
    (`floorplancad_adapter.py:82,322-328`); feeding it to promote would coverage-
    suppress true glazing candidates. Measuring a wall+curtain variant is a separate,
    labeled follow-up — not this slice.
15. **Openings keep `type="candidate"` in ALL lanes** — outside the GT vocabulary
    `door|sliding|window|opening`, so subtype accuracy stays structurally 0 and every
    per-sheet F4 verdict stays REVIEW (`benchmark_reader.py:343-346`; pin
    `test_svg_plan_reader.py:195-206`). The oracle lane's F4 verdict column will still
    read REVIEW everywhere — the signal is recall/precision/per_type_gt, and 0 F4 PASS
    verdicts is CORRECT behavior, not a failure of the slice.
16. **Analyze cards/preds with python, never PowerShell** — PS 5.1 `ConvertFrom-Json`
    fails on the cards' deep keys (recorded 2026-07-06). Also PS 5.1 has no `&&`.
17. **`walls` must be the LAST keyword param with default None** on both `read_sheet`
    (`wall_segs`/`wall_source`) and `run_baseline` — existing tests call them
    positionally (`test_svg_plan_reader.py:75-76,252`).
18. **score_pair's unit guard never fires in this lane** — non-mm sheets are pre-skipped
    as `svg-unit` (`svg_plan_reader.py:252-255`; 3,257 of 5,502). Do not "fix" skips by
    guessing scale or passing `open_tol`.

## Acceptance criteria

1. **Test suite:** `cd c:\Users\teza_\OneDrive\Desktop\PlingPeat; python3 -m pytest pipeline/scripts/ -q`
   → `471 passed` (465 baseline + 6 new; 472+ if Step 12 done), 0 failed, 0 errors.
2. **Blind byte-identity (real corpus):**
   ```powershell
   cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
   python3 -c "import json
   gt=json.load(open(r'C:\Users\teza_\studio-datasets\floorplancad\gt-test-00\0000-0009.gt.json',encoding='utf-8'))
   old=json.load(open(r'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00\preds\0000-0009.pred.json',encoding='utf-8'))
   import svg_plan_reader as R
   new=R.read_sheet(r'C:\Users\teza_\studio-datasets\floorplancad\test-00\0000-0009.svg', gt['meta']['scale_mm_per_unit'])
   print('IDENTICAL' if new==old else 'DIFFERS')"
   ```
   → prints `IDENTICAL` (this exact check printed IDENTICAL pre-change, 2026-07-07).
3. **GT regen:** `gt-test-00-w1` holds 5,502 `*.gt.json`; manifest `ok:false` count 0;
   the 3-file equivalence snippet prints `EQUAL` three times; `--selftest` on the new
   dir ends with `selftest PASS: adapter output is benchmark_reader-clean`.
4. **Smoke direction (limit 200, same gt dir):** oracle report's F4 pred count <
   blind's; oracle F4 precision % > blind's; oracle detection line == blind detection
   line.
5. **Full oracle run** (`baseline-test-00-oracle\report.md`):
   - `2245 scored / 5502` with `{"svg-unit": 3257, "svg-missing": 0, "error": 0}`;
   - detection: matched 1,014, recall 9.8 %, precision 14.3 % — identical to blind;
   - **F4 n_pred < 159,582** (down) and **F4 precision > 2.9 %** (up — the goal
     number); record the exact fraction;
   - sliding recall >= 78 % and window recall >= 80 % (floors; blind: 87.8 % / 90.2 %);
   - title contains `ORACLE-WALL` and `NOT the blind headline`; the wall-segs +
     diagonal honesty line is present.
6. **Row labeling:** the Step-11 snippet reports `unlabeled: 0` over all 5,502
   cards.jsonl rows.
7. **Committed report:** `qa/reports/floorplancad-oracle-walls-2026-07-07.md` exists
   with the NOT-headline banner, the blind-vs-oracle table (detection row identical),
   and the diagonal-wall count.
8. **Nothing rewritten:** `git status` shows NO modification to
   `qa/reports/floorplancad-baseline-2026-07-06.md`; directories
   `studio-datasets\floorplancad\gt-test-00\` and `baseline-test-00\` received no new
   writes (their file timestamps predate the session).
9. **Commits:** >= 2 logical commits with explicitly staged paths, none touching
   protected files, not pushed.

## Do NOT

- Do NOT edit `glazing_candidates.py`, `benchmark_reader.py`, `plan_cluster.py`,
  `pdf_extract_walls.py` — the entire slice is adapter + reader + tests + report.
- Do NOT tune any promote constant (`DEFAULTS` off_tol/gap_tol/min_len/pair_gap/
  pair_overlap/end_tol/covered_tol/covered_frac, or the hardcoded 1000 mm bonus at
  `glazing_candidates.py:306`) — several are boundary-pinned by tests; tuning is a
  different, owner-visible slice.
- Do NOT emit any real F4 subtype (`door|sliding|window|opening`) from the reader —
  openings stay `type="candidate"` in every lane; typing without a classifier re-opens
  the unearned-subtype-credit bug (pin `test_svg_plan_reader.py:195-206`).
- Do NOT let oracle numbers appear anywhere unlabeled — every cards row, pred meta,
  report title, and the qa report must carry `wall_source=oracle` / the NOT-headline
  banner. The honest headline remains the 2026-07-06 blind report until a `self` lane
  beats it.
- Do NOT default or guess: no scale-guessing for svg-unit sheets, no `open_tol`
  workaround, no `.get("wall_lines", [])` per-sheet fallback, no fabricated
  rot/indoor/floor/kind anywhere (scorer-honesty doctrine: missing = counted +
  reported, never defaulted).
- Do NOT write corpus-derived artifacts (gt.json, preds, cards.jsonl, overlays) into
  the repo or OneDrive — FloorPlanCAD is CC BY-NC; everything derived stays under
  `C:\Users\teza_\studio-datasets\`; only the aggregate qa report and code/tests are
  committed. Test fixtures must stay self-authored synthetic SVGs.
- Do NOT run the full corpus in the in-tool background lane (10-min hard cap vs a
  15–45 min run) — detached `Start-Process` + poll on `report.md` only.
- Do NOT regenerate into `gt-test-00` or delete/rename existing run dirs; no `rm -rf`,
  no force-push, no `git add -A`, no push at all this session.
- Do NOT touch `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.claude/settings.json`,
  `.gitattributes` (hook-enforced; propose via PR only).
- Do NOT name any identifier in `svg_plan_reader.py` containing `semantic`, `inkscape`,
  `INK_NS`, or `instance_id`, and no string literal there may contain `semantic-id`,
  `instance-id`, or `inkscape` outside the module docstring (static tripwire,
  `test_svg_plan_reader.py:120-140`).
