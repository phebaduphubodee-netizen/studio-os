# PLAN-f1-size-prior-identity — deterministic size/shape identity priors (first honest nonzero F1)

> **สถานะ (2026-08-04): EXECUTED** — สร้างครบตามแผน: `kind_priors.py` + tests
> (`6508701`), wired เข้า `svg_plan_reader.py`, รายงาน
> `qa/reports/floorplancad-f1-priors-2026-07-07.md`; ต่อยอดเข้า doubt suite ภายหลัง
> (`63271bf`, `474dc11`) (ย้ายจาก root มา docs/plans/ 2026-08-04 ตาม outside-review ข้อ 7)

Rank: 3/5

## Goal (incl. the measured number this moves)

The FloorPlanCAD baseline reader emits **no `kind` on any element** — F1 identity is
structurally 0.0. Verified this session from the real run artifacts:

- Aggregate F1 across `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00\cards.jsonl`:
  **hits 0 / n 1,014 → accuracy 0.0** (n = IoU-matched GT↔pred element pairs across the
  2,245 scored sheets; detection: n_gt 10,347, n_pred 7,097, matched 1,014).
- GT-kind distribution of those 1,014 matched pairs (computed from the cards' `per_kind`
  integer counts): chair 334, squat_toilet 172, table 166, elevator 163, air_conditioner 82,
  refrigerator 40, sink 29, bed 11, toilet 6, sofa 4, stairs 4, gas_stove 1, wardrobe 1,
  cabinet 1.

**This plan moves aggregate F1 accuracy from 0.0 to > 0.0** by adding a deterministic,
cited, size/aspect prior table derived from the TRAIN split GT (legitimate train/test
separation), wired into the benchmark reader lane behind an **off-by-default** parameter.
A kind is emitted ONLY when the element's footprint falls inside exactly ONE kind's band —
ambiguity emits nothing (stays unreported). The production/owner lane is untouched.

Honest expectation-setting (verified engine semantics): `norm_kind(None) → ""` in
`benchmark_reader.py:65-67`, so a matched pair with NO pred kind scores as **WRONG** in F1
accuracy (confusion `"table->"`), not skipped — F1 has no unreported-skip semantics (only
F2/F3/F5 do). Therefore F1 accuracy = emission-coverage × prior-precision on 1,014 matched
pairs. With chair/squat_toilet/sink size overlap forcing much of the mass to unreported,
expect accuracy in the low tens of percent at best; ANY value > 0 with a reported
emitted-precision is the win. **No tuning against the test split, ever** (see Do NOT).

## Why now (leverage)

- F1 = 0.0 is the one benchmark axis where zero is structural, not a tuning problem; identity
  is also the owner's most-corrected fault class in the production lane.
- All inputs exist tonight: train-00 (3,760 SVGs) + train-01 (6,401 SVGs) are extracted at
  `C:\Users\teza_\studio-datasets\floorplancad\` (verified by directory count this session);
  the adapter converts at ~11 ms/file (measured on 30 train-00 files), so train GT generation
  is minutes, not hours.
- The 300-file survey medians ("wardrobe 2.1 m × 0.56 m") are NOT persisted machine-readably
  anywhere — only prose fragments survive (`floorplancad_adapter.py:28-29`,
  `docs/research/2026-07-06-paired-2d3d-backlearn.md:191-192`). Recomputing distributions
  from train gt.json is the only reproducible source, and it is strictly better data.
- The scorer needs zero changes: `benchmark_reader.score_identity` already scores kinds on
  matched pairs only (`benchmark_reader.py:140-162`), so detection weakness (recall 9.8%)
  cannot pollute F1 — it only caps n at 1,014.

## Files to touch

| Path (repo-relative, repo root = `c:\Users\teza_\OneDrive\Desktop\PlingPeat`) | Status | What |
|---|---|---|
| `pipeline/scripts/kind_priors.py` | **[NEW]** | Prior derivation + suggestion logic (pure python, no corpus data inside) |
| `pipeline/scripts/test_kind_priors.py` | **[NEW]** | Unit + mutation-pin tests, synthetic fixtures only |
| `pipeline/scripts/svg_plan_reader.py` | [EXISTS] | Wire optional `kind_priors` into `read_sheet` / `run_baseline` / CLI / report |
| `pipeline/scripts/test_svg_plan_reader.py` | [EXISTS] | 4 new tests (priors emission, ambiguity, blindness-with-priors, baseline wiring) |
| `qa/reports/floorplancad-f1-priors-2026-07-07.md` | **[NEW]** | Committed aggregate summary (numbers only, no corpus data) |
| `docs/strategy.md` | [EXISTS] | Append dated session entry at file tail |

Outside-repo artifacts created (NEVER committed — CC BY-NC corpus derivatives stay in
`C:\Users\teza_\studio-datasets\`):

- `C:\Users\teza_\studio-datasets\floorplancad\gt-train-00\` (*.gt.json + manifest.jsonl + summary.md)
- `C:\Users\teza_\studio-datasets\floorplancad\gt-train-01\` (same)
- `C:\Users\teza_\studio-datasets\floorplancad\priors\kind-priors-train.json`
- `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors\` (cards.jsonl, preds/, overlays/, report.md)

Files that must NOT change: `pipeline/scripts/benchmark_reader.py`,
`pipeline/scripts/floorplancad_adapter.py`, `pipeline/scripts/plan_cluster.py`,
`pipeline/scripts/glazing_candidates.py`, `pipeline/scripts/placement_gate.py`,
`projects/PRJ-2026-002_c001-house/03_layout/v4/gen_floor2_v4_specs.py`,
`pipeline/scripts/raster_overlay.py`,
`pipeline/scripts/build_floor.py`, and the four hook-protected paths (see Do NOT).

## Implementation order

All python commands run with cwd = `c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts`
(imports are flat top-level modules — `svg_plan_reader.py:56-59`). Test invocations use the
verified repo canon: `python3 -m pytest pipeline/scripts/ -q` from repo root (green in ~5 s
as of this plan's writing — re-verified this session; the absolute total is NOT stable
tonight, see Step 1).

### Step 1 — Preflight

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat
python3 -m pytest pipeline/scripts/ -q
```
Require 0 failures / 0 errors; RECORD the green count as N (other slices land in the same
tree tonight — the absolute total is not stable, failures are what STOP you). If anything
fails or errors, STOP — the tree has drifted from this plan's anchors; re-verify every line
number cited below before proceeding.

Confirm corpus present:
```powershell
(Get-ChildItem C:\Users\teza_\studio-datasets\floorplancad\train-00 -Filter *.svg | Measure-Object).Count   # expect 3760
(Get-ChildItem C:\Users\teza_\studio-datasets\floorplancad\train-01 -Filter *.svg | Measure-Object).Count   # expect 6401
```

### Step 2 — Generate TRAIN GT (prerequisite: no gt-train dirs exist yet — verified)

Adapter CLI (`floorplancad_adapter.py:672-674`): `--batch <svg-dir> <out-dir>`; the out-dir
default is `<svg-dir>-gt` (`:674`), so pass the explicit out dir to match the `gt-test-00`
naming precedent. Measured 11 ms/file → ~45 s and ~75 s respectively; run foreground with a
generous timeout (600000 ms). `summary.md` is written LAST (`floorplancad_adapter.py:624-626`)
— its existence means the run finished.

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
python floorplancad_adapter.py --batch C:\Users\teza_\studio-datasets\floorplancad\train-00 C:\Users\teza_\studio-datasets\floorplancad\gt-train-00
python floorplancad_adapter.py --batch C:\Users\teza_\studio-datasets\floorplancad\train-01 C:\Users\teza_\studio-datasets\floorplancad\gt-train-01
```

Check each `summary.md`: `parse-failed: 0` (a handful is tolerable — one broken file costs
one manifest row, never the run, `floorplancad_adapter.py:574-578`) and "calibrated to mm"
in the 35–46% band (test-00 was 40.8%; expect ≈ 1,500 + ≈ 2,600 mm files ≈ 4,100 total).

Then run the standing gt-vs-gt schema gate on both:
```powershell
python floorplancad_adapter.py --selftest C:\Users\teza_\studio-datasets\floorplancad\gt-train-00
python floorplancad_adapter.py --selftest C:\Users\teza_\studio-datasets\floorplancad\gt-train-01
```
Expected final line each: `selftest PASS: adapter output is benchmark_reader-clean`.

### Step 3 — Write `pipeline/scripts/kind_priors.py` [NEW]

Pure logic module, no fitz, no matplotlib, no corpus constants baked in. Contents:

```
"""kind_priors.py -- deterministic per-kind size/aspect bands for the benchmark lane.

    python kind_priors.py --derive <out.json> <gt-dir> [<gt-dir> ...]

Bands are derived from TRAIN-split gt.json only (units=='mm' files), scored on the test
split -- legitimate train/test separation. suggest_kind emits a kind ONLY when the
footprint falls inside exactly ONE kind's band (unique membership); any ambiguity
(0 or >=2 candidates) returns None and the element stays kind-less. The benchmark
scores a kind-less matched pair as WRONG (norm_kind(None)->'' in benchmark_reader),
never skipped -- unreported is the honest failure mode, a guess is a false-accept.

BENCHMARK / SUGGESTION LANE ONLY: identity in owner projects is owner-signed semantic
truth. This module must never be imported by placement_gate, gen_floor2_v4_specs,
raster_overlay, or build_floor.
"""
```

Constants (module level):
- `SCHEMA = "interior-ai/kind-priors@0.1"`
- `Q_LO, Q_HI = 0.10, 0.90`
- `PAD_MM = 50.0`          # covers cluster-AABB dilation: pred dims are morphology bboxes
                            # rounded to int mm, ±2·res ≈ ±12 mm typical (plan_cluster.py:145-147;
                            # test_svg_plan_reader.py:185 allows ±12 on a 600 mm rect)
- `ASPECT_PAD = 1.15`
- `MIN_SUPPORT = 50`

Functions:

1. `_quantile(sorted_vals, q)` → `sorted_vals[int(round(q * (len(sorted_vals) - 1)))]`.

2. `derive(gt_dirs, min_support=MIN_SUPPORT)` → priors dict.
   - For each dir, `glob.glob(os.path.join(d, "*.gt.json"))`, `json.load`.
   - **Skip AND COUNT files where `doc["meta"]["units"] != "mm"`** (mirror the runner's
     skip at `svg_plan_reader.py:252-255`). This is load-bearing: 59.2% of gt files carry
     raw svg-unit dims ~100× off; including one poisons every band.
   - Sample only `doc["elements"]` (NEVER `doc["openings"]` — door widths ≈ 999 mm would
     collide with furniture bands). Per element: `w, d = float(e["w"]), float(e["d"])`;
     skip+count if either ≤ 0 or non-numeric; `lo, hi = sorted((w, d))`;
     `aspect = hi / lo`. Append `(lo, hi, aspect)` to `samples[e["kind"]]`.
   - Per kind, split the samples into THREE separate lists (lo, hi, aspect) and sort
     each ascending with `sorted()` BEFORE any `_quantile` call. `_quantile` indexes
     positionally and assumes pre-sorted input (its `sorted_vals` name is the contract,
     not a hint); quantiling an unsorted list silently yields garbage bands that can
     still pass loose containment asserts.
   - Kinds with `n >= min_support` get a band row; others land in
     `excluded_low_support: {kind: n}`.
   - Band row per kind:
     ```json
     {"n": 812,
      "lo_mm": [<q10(lo)-PAD_MM>, <q90(lo)+PAD_MM>],
      "hi_mm": [<q10(hi)-PAD_MM>, <q90(hi)+PAD_MM>],
      "aspect": [<max(1.0, q10(aspect)/ASPECT_PAD)>, <q90(aspect)*ASPECT_PAD>],
      "raw": {"lo_q10":..., "lo_q90":..., "hi_q10":..., "hi_q90":...,
              "aspect_q10":..., "aspect_q90":...},
      "provenance": "<built at runtime -- see next bullet>"}
     ```
   - `provenance` is CONSTRUCTED AT RUNTIME from derive()'s actual inputs, never a
     hardcoded literal (step 4's tests run derive() on `tmp_path` fixture dirs — a
     baked-in "gt-train-00+gt-train-01" string would emit FALSE provenance there):
     ```python
     "floorplancad " + "+".join(os.path.basename(os.path.normpath(d)) for d in gt_dirs) + f", units=mm gt.json, n={n} instances, adapter floorplancad_adapter v1, derived {date.today()}"
     ```
     where `n` is that kind's sample count and `date.today()` is the same value written
     to `meta["date"]`. On the real step-7 run this yields the
     "floorplancad gt-train-00+gt-train-01, ..." form.
   - Top-level doc:
     ```json
     {"schema": "interior-ai/kind-priors@0.1",
      "meta": {"derived_from": [<abs gt dirs>], "date": "YYYY-MM-DD",
               "n_files_total":.., "n_files_mm":.., "n_files_skipped_units":..,
               "n_elements_sampled":.., "n_elements_malformed":..,
               "params": {"q_lo":0.10,"q_hi":0.90,"pad_mm":50.0,"aspect_pad":1.15,"min_support":50}},
      "kinds": {...}, "excluded_low_support": {...}}
     ```
   - Vocabulary note: emit kinds under the EXACT GT names (`RAW_CLASSES` values,
     `floorplancad_adapter.py:64-74`, e.g. `tv_cabinet` not `tv_console`). The scorer
     normalizes both sides through `KIND_SYNONYMS` (`benchmark_reader.py:61-62,65-67`), so
     exact-GT-name emission always compares equal.

3. `suggest_kind(w_mm, d_mm, priors)` → `str | None`.
   - Guard: any of w/d non-positive or non-numeric → `None`.
   - `lo, hi = sorted((float(w_mm), float(d_mm)))`; `aspect = hi / lo`.
   - `cands = [k for k, b in sorted(priors["kinds"].items()) if b["lo_mm"][0] <= lo <= b["lo_mm"][1] and b["hi_mm"][0] <= hi <= b["hi_mm"][1] and b["aspect"][0] <= aspect <= b["aspect"][1]]`
   - `return cands[0] if len(cands) == 1 else None`  ← the confidence rule IS unique
     membership. Both interval ends inclusive.

4. `load(path)` → dict; `raise SystemExit(f"not a kind-priors file: {path}")` if
   `doc.get("schema") != SCHEMA`. Loud failure at startup, never a per-sheet error row.

5. `main(argv)`: `--derive <out.json> <gt-dir> [...]` — `os.makedirs(dirname, exist_ok=True)`
   on the out path's parent, atomic write (`out + ".tmp"` then `os.replace` — precedent
   `glazing_candidates.py:488-490`), then print a per-kind table (kind, n, lo band, hi band,
   aspect band) plus the excluded_low_support dict. Anything else → `raise SystemExit(__doc__)`.

Deliberate scope-down (record in the module docstring): v1 bands are size/aspect only. The
item spec mentions curve-signature bands, but gt.json elements carry NO curve field (only
`id/x/y/w/d/layer/n_prims/kind` — `floorplancad_adapter.py` element schema), so a grounded
curve prior needs a train-side reader run to pair pred `curve` flags with GT kinds — a
follow-up slice, not fabricated here. The pred-side `curve`/`fill` fields
(`plan_cluster.py:145-147`) stay unused by v1 suggestion.

### Step 4 — Write `pipeline/scripts/test_kind_priors.py` [NEW]

Pytest-style + the repo's `__main__` self-runner convention
(`if __name__ == "__main__": import pytest; raise SystemExit(pytest.main([__file__, "-q"]))`
— same as `test_svg_plan_reader.py:333-335`). ALL fixtures are self-authored synthetic
gt.json dicts written into `tmp_path` — never corpus files (CC BY-NC, never redistributed;
same rule as `test_floorplancad_adapter.py`).

Helper: `_gt(tmp_path, name, units, elements)` writes
`{"meta": {"units": units, "scale_mm_per_unit": 100.0 if units == "mm" else None}, "elements": elements, "openings": []}`
to `<tmp_path>/<name>.gt.json`.

Tests (9 — each name below is load-bearing for the acceptance count):

1. `test_derive_bands_from_synthetic_gt` — one mm gt file with 60 `table` elements around
   1600×800 (spread ±100); `derive([dir], min_support=50)`; assert `"table"` in kinds,
   `n == 60`, `lo_mm[0] <= 800 <= lo_mm[1]`, `hi_mm[0] <= 1600 <= hi_mm[1]`, and params
   echoed in meta.
2. `test_svg_unit_files_are_excluded` — **mutation pin**: add a `units="svg-unit"` gt file
   with 60 `table` elements at 16×8 (raw units). Bands must be identical to test 1's
   (compare the kinds dict) and `meta["n_files_skipped_units"] == 1`. A mutant that drops
   the units filter shifts `lo_mm[0]` below 0 — this test must fail it.
3. `test_openings_never_enter_element_bands` — one mm gt file containing BOTH 60
   door-sized rows in `"openings"` (w≈999, d≈100) AND 60 `table` elements (1600×800);
   (extend the `_gt` helper with an `openings=[]` kwarg for this test).
   `derive([dir], min_support=50)`; assert `meta["n_elements_sampled"] == 60` and that
   `"table"` is the ONLY kind in the result — proving the opening rows never entered
   the samples.
4. `test_min_support_excludes_thin_kinds` — kind with 3 samples at `min_support=5` →
   absent from `kinds`, present in `excluded_low_support` with value 3.
5. `test_suggest_unique_band_emits` — hand-built priors dict with a single `table` band
   containing (1600, 800) → `suggest_kind(1600, 800, p) == "table"`.
6. `test_suggest_ambiguity_stays_unreported` — **THE mutation pin**: two kinds
   (`table`, `cabinet`) with identical bands → `suggest_kind(1600, 800, p) is None`.
   Comment in the test: the mutant `return cands[0] if cands else None` (dropping the
   `len == 1` check) must fail here — a guess on ambiguity is a false-accept, the exact
   flattering failure the scorer-honesty doctrine bans.
7. `test_suggest_orientation_agnostic` — `suggest_kind(800, 1600, p)` equals
   `suggest_kind(1600, 800, p)` (sorted-dims join, same convention as the ledger's
   `_size_consistent`).
8. `test_suggest_outside_all_bands_is_none` — (10000, 10000) → `None`; also (0, 500) → `None`
   (non-positive guard).
9. `test_provenance_recorded_per_band` — every row in `kinds` carries a non-empty
   `provenance` string and integer `n`; doc carries `schema == "interior-ai/kind-priors@0.1"`.

Verify: `python3 -m pytest pipeline/scripts/test_kind_priors.py -q` → `9 passed`.

### Step 5 — Wire into `pipeline/scripts/svg_plan_reader.py` [EXISTS]

Current anchors verified this session (module is 381 lines, commit 34c1a08 tree):

5a. **Docstring** (lines 3-4): change the baseline usage line to
    `python svg_plan_reader.py --baseline <svg-dir> <gt-dir> <out-dir> [limit N] [overlays K] [priors P]`
    and add one sentence: "priors P = kind-priors JSON (kind_priors.py); off by default —
    without it elements never carry kind." The module docstring is the ONLY string literal
    whitelisted by the static tripwire (see Edge case 1).

5b. **Import** (after line 59 `from plan_cluster import cluster_segments`): add
    `import kind_priors`.

5c. **`read_sheet`** (def at line 143): new signature
    `def read_sheet(svg_path, scale_mm_per_unit, close_mm=CLOSE_MM, kind_priors_doc=None):`
    (name the param `kind_priors_doc` to avoid shadowing the module). The element loop
    (lines 159-162) currently appends an inline dict literal with no local name —
    restructure it to bind the dict first, run the priors check, then append (field names
    verified against the current code: `id/x/y/w/d/curve/fill`):
    ```python
    for k, it in enumerate(clu["items"]):
        el = {"id": f"c{k:03d}", "x": it["x"], "y": it["y"],
              "w": it["w"], "d": it["d"],
              "curve": it["curve"], "fill": it["fill"]}
        if kind_priors_doc:
            ks = kind_priors.suggest_kind(el["w"], el["d"], kind_priors_doc)
            if ks:
                el["kind"] = ks
        elements.append(el)
    ```
    In the meta dict (lines 176-189): add — ONLY when `kind_priors_doc` is truthy — a key
    ```python
    "kind_priors": {"schema": kind_priors_doc["schema"],
                    "derived_from": [os.path.basename(os.path.normpath(d)) for d in kind_priors_doc["meta"]["derived_from"]],
                    "n_kinds": len(kind_priors_doc["kinds"]),
                    "kinds_emitted": sum(1 for e in elements if "kind" in e)},
    ```
    When `kind_priors_doc is None` the meta dict must be byte-for-byte what it is today
    (no new key, not even a null one) — pinned in step 6.

5d. **`run_baseline`** (def at line 227): new signature
    `def run_baseline(svg_dir, gt_dir, out_dir, limit=None, overlays=0, priors=None):`
    where `priors` is a PATH string. Before the gt loop (right after the makedirs at
    lines 228-230): `pdoc = kind_priors.load(priors) if priors else None` — a bad path
    fails the whole run loudly at startup, never per-sheet error rows. At the read call
    (line 261): `pred = read_sheet(sfp, gt["meta"]["scale_mm_per_unit"], kind_priors_doc=pdoc)`.
    At the report call (line 288): pass
    `priors_note=(f"{os.path.basename(priors)} ({len(pdoc['kinds'])} kinds)" if priors else None)`.

5e. **`render_baseline_report`** (def at line 297): new signature
    `def render_baseline_report(cards, skipped, n_total, secs, overlay_failed=0, priors_note=None):`
    In the F1 section (currently lines 325-328): when `priors_note is None`, keep the two
    existing lines VERBATIM (report stability for the no-priors lane). When set, replace the
    "NO symbol classifier" prose with:
    ```python
    per, unrep = {}, 0
    for c in cards:
        for k, r in c["F1_identity"]["per_kind"].items():
            if k == "":
                unrep += r["pred"]; continue
            row = per.setdefault(k, {"gt": 0, "pred": 0, "hit": 0})
            row["gt"] += r["gt"]; row["pred"] += r["pred"]; row["hit"] += r["hit"]
    emitted = sum(r["pred"] for r in per.values())
    hits = sum(r["hit"] for r in per.values())
    ```
    and emit lines:
    - `- kind priors: {priors_note} -- deterministic size/aspect bands from TRAIN gt; unique-band membership only, ambiguity stays unreported`
    - `- accuracy {pct(f1['accuracy'])} on {f1['n']} matched pairs`
    - `- emitted kind on {emitted}/{f1['n']} matched pairs; emitted-correct {hits} -> emitted precision {pct(hits/emitted) if emitted else 'n/a'}`
    - `- unreported (no kind emitted) on {unrep} matched pairs -- counted as WRONG in accuracy (F1 has no skip semantics)`
    - one line per kind, sorted by gt desc, skipping rows where gt+pred == 0:
      `    - {kind}: gt {gt}, pred {pred}, hit {hit}, precision {pct(hit/pred) if pred else 'n/a'}, recall {pct(hit/gt) if gt else 'n/a'}`
    Integer sums only — NEVER average per-card accuracies (`aggregate()` drops `per_kind`
    entirely, `benchmark_reader.py:363-366`; this table is the only corpus-level per-kind view).

5f. **`main` option parser** (lines 364-374): the current loop rejects any option whose
    value fails `.isdigit()` — a path can never pass it. Replace the while-loop body with:
    ```python
    while rest:
        if len(rest) >= 2 and rest[0] in ("limit", "overlays") and rest[1].isdigit():
            kw[rest[0]] = int(rest[1]); rest = rest[2:]
        elif len(rest) >= 2 and rest[0] == "priors":
            kw["priors"] = rest[1]; rest = rest[2:]
        else:
            raise SystemExit(f"bad option {rest[0]!r} -- expected: "
                             f"[limit N] [overlays K] [priors P]\n\n{__doc__}")
    ```
    Do NOT touch the `--sheet` branch.

Verify step 5 before moving on:
`python3 -m pytest pipeline/scripts/test_svg_plan_reader.py -q` → all existing tests still
pass (especially `test_read_sheet_clusters_and_openings` with its `"kind" not in e` pin at
line 189, `test_run_baseline_skips_and_scores` with its `F1 accuracy == 0.0` pin at line 257,
and `test_reader_source_never_names_annotation_attrs`).

### Step 6 — Add 4 tests to `pipeline/scripts/test_svg_plan_reader.py` [EXISTS]

Insert before the `if __name__ == "__main__":` block (currently line 333). Reuse the
existing helpers `_write`, `_sheet_svg`, `ANNOTATED`, `STRIPPED`. A minimal in-test priors
dict (no file needed for read_sheet tests):

```python
_PRIORS = {"schema": "interior-ai/kind-priors@0.1",
           "meta": {"derived_from": ["gt-train-00"], "params": {}},
           "kinds": {"table": {"lo_mm": [500.0, 700.0], "hi_mm": [500.0, 700.0],
                               "aspect": [1.0, 1.4]}}}
```
(The `_sheet_svg` fixture's rect clusters to ~600×600 mm at scale 100 — verified by the
existing assertion at lines 183-185.)

1. `test_read_sheet_priors_emit_and_ambiguity` — `read_sheet(_sheet_svg(tmp_path), 100.0,
   kind_priors_doc=_PRIORS)` → the 600×600 element carries `kind == "table"` and meta
   carries `kind_priors` with `kinds_emitted == 1`. Then deep-copy `_PRIORS`, add a second
   kind `"cabinet"` with identical bands → re-read → NO element carries `"kind"` (ambiguity
   mutation pin at the reader level) and `kinds_emitted == 0`.
2. `test_read_sheet_no_priors_meta_and_elements_unchanged` — `read_sheet(fixture, 100.0)`
   (no priors): assert `"kind_priors" not in pred["meta"]` and
   `all("kind" not in e for e in pred["elements"])`. This pins default-lane byte-identity
   alongside the existing line-189 pin.
3. `test_read_sheet_priors_stays_annotation_blind` — the ANNOTATED vs STRIPPED twins
   (fixtures at lines 29-41) read with `kind_priors_doc=_PRIORS`; pop `meta["file"]` from
   both; assert equal. Blindness must hold on the priors path too: suggestion reads only
   w/d, which derive from geometry attributes.
4. `test_run_baseline_with_priors` — clone the `test_run_baseline_skips_and_scores` fixture
   pattern (lines 225-252) but with only the s1 mm sheet; write `_PRIORS` to
   `<tmp_path>/priors.json`; `run_baseline(svg_dir, gt_dir, out_dir, priors=<path>)`;
   assert `cards[0]["F1_identity"]["accuracy"] == 1.0` (gt kind is `table`, fixture line
   234), the written `preds/s1.pred.json` element carries `"kind": "table"`, and report.md
   contains `emitted precision` and the `table:` per-kind row.

Verify: `python3 -m pytest pipeline/scripts/test_svg_plan_reader.py pipeline/scripts/test_kind_priors.py -q`
from repo root → 13 new tests green, 0 failures. Then the full suite:
`python3 -m pytest pipeline/scripts/ -q` → **N + 13 passed** (N = Step 1's recorded green
baseline), 0 failed.

### Step 7 — Derive the real priors from TRAIN

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts
python kind_priors.py --derive C:\Users\teza_\studio-datasets\floorplancad\priors\kind-priors-train.json C:\Users\teza_\studio-datasets\floorplancad\gt-train-00 C:\Users\teza_\studio-datasets\floorplancad\gt-train-01
```
Runtime: seconds-to-a-minute (reads ~10k small JSON files). Checks before proceeding:
- File exists, `schema == "interior-ai/kind-priors@0.1"`, `meta.n_files_mm` ≈ 4,100
  (35–46% of 10,161).
- Sanity cross-check against the CITED knowledge (this is source (b) of the item spec —
  it validates, it does not override the data):
  `knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md:30-33` gives bed mattress
  991–1930 × 1905–2032 mm → derived `bed.hi_mm` band must overlap [1905, 2032];
  `:39` gives wardrobe depth 500–600 mm → derived `wardrobe.lo_mm` band should sit near
  500–700 (survey prose said 2.1 m × 0.56 m, `floorplancad_adapter.py:28-29`).
  If `bed.hi_mm` does not overlap [1905, 2032], STOP — the derivation has a units or
  elements/openings mix-up; do not proceed to the test run.
- Record the printed per-kind table — it goes into the qa report.

### Step 8 — Rerun the test-split baseline WITH priors (detached — run exceeds the 10-min lane)

The prior run took 865 s wall-clock; expect ~15 min. Launch detached (PowerShell
Start-Process; the in-tool background lane hard-caps at 10 min):

```powershell
Start-Process -FilePath python -ArgumentList 'svg_plan_reader.py','--baseline','C:\Users\teza_\studio-datasets\floorplancad\test-00','C:\Users\teza_\studio-datasets\floorplancad\gt-test-00','C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors','overlays','6','priors','C:\Users\teza_\studio-datasets\floorplancad\priors\kind-priors-train.json' -WorkingDirectory 'c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts' -RedirectStandardOutput 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors-run.log' -RedirectStandardError 'C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors-run.err'
```

`report.md` is written LAST (`svg_plan_reader.py:288-291`) — the run is DONE exactly when
this returns True:
```powershell
Test-Path C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors\report.md
```
Poll it every few minutes (cards.jsonl streams row-by-row with flush, so a mid-run death
keeps completed rows — check the .err log if the row count stalls).

Post-run checks (python, NOT PowerShell — PS 5.1 `ConvertFrom-Json` chokes on the cards'
deep keys):
- cards.jsonl has 5,502 rows; skipped counts identical to the old run
  (`{"svg-unit": 3257, "svg-missing": 0, "error": 0}`) — priors change no skip logic.
- detection matched == 1,014 and F4 recall/precision identical to
  `qa/reports/floorplancad-baseline-2026-07-06.md` — priors touch element `kind` only.
  (Drift of ±1–2 pairs is theoretically possible via the exact-IoU-tie kind tie-break,
  `benchmark_reader.py:114-117`; more than that = wiring bug, stop and investigate.)
- **THE number: F1 accuracy in report.md > 0.0** (was 0.0, hits 0/1014). Also record:
  emitted count, emitted precision, unreported count, per-kind rows.
- Contingency if hits == 0 (all emissions ambiguous or absent): do NOT touch the bands and
  re-run against test — that is test-set fitting. Verify the mechanics via
  `test_run_baseline_with_priors` (it proves end-to-end emission works), write the qa
  report with the honest zero + the band-overlap diagnosis (which kinds' bands mutually
  contain the common footprints), and mark band refinement as a TRAIN-side follow-up.

### Step 9 — Default-lane identity proof (no-priors output unchanged)

Write this throwaway to `$env:TEMP\f1_identity_check.py` (PowerShell — e.g.
`Set-Content -Path "$env:TEMP\f1_identity_check.py" -Encoding utf8`; `%TEMP%` is cmd.exe
syntax and is NOT expanded by PowerShell) and run `python "$env:TEMP\f1_identity_check.py"`:

```python
import glob, json, os, sys
os.chdir(r"c:\Users\teza_\OneDrive\Desktop\PlingPeat\pipeline\scripts")
sys.path.insert(0, os.getcwd())
import svg_plan_reader as R
base = r"C:\Users\teza_\studio-datasets\floorplancad"
old_fp = sorted(glob.glob(base + r"\baseline-test-00\preds\*.pred.json"))[0]  # 0000-0009.pred.json
name = os.path.basename(old_fp)[:-len(".pred.json")]
gt = json.load(open(base + rf"\gt-test-00\{name}.gt.json", encoding="utf-8"))
old = json.load(open(old_fp, encoding="utf-8"))
new = R.read_sheet(base + rf"\test-00\{name}.svg", gt["meta"]["scale_mm_per_unit"])
print("NO-PRIORS PRED IDENTICAL:", old == new)
```
Expected output: `NO-PRIORS PRED IDENTICAL: True` (parsed-JSON equality; read_sheet is
deterministic and the default path added zero keys). If False, diff the two dicts — the
default lane regressed; fix before anything else.

### Step 10 — Committed artifacts

10a. `qa/reports/floorplancad-f1-priors-2026-07-07.md` [NEW] — aggregate numbers ONLY
(precedent: `qa/reports/floorplancad-baseline-2026-07-06.md` quotes corpus medians; the
priors JSON itself and all gt.json stay outside the repo). Must contain:
- before/after: F1 accuracy 0.0 (hits 0/1014) → <new value> (hits <h>/1014); emitted
  count + emitted precision + unreported count.
- the per-kind table from the new report.md.
- priors provenance: file path under studio-datasets, derivation params
  (q10/q90, pad 50 mm, aspect_pad 1.15, min_support 50), train dirs + n_files_mm,
  date, adapter version.
- the ergonomics cross-check rows with citations
  (`knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md:30-39`) and a note that
  `knowledge/classifications/thai-cad-layers-asa2554.md` was consulted for layer/pen
  priors but contributes no size bands (its finding: pen width does NOT identify class).
- honesty caveats, verbatim ideas: F1 n = 1,014 matched pairs only (detection recall 9.8%
  caps eligibility — detection misses are reported separately and do not pollute F1);
  unreported counts as WRONG (no skip semantics in F1); bands fixed a priori from TRAIN,
  zero tuning iterations against test; benchmark/suggestion lane only — production identity
  stays owner-signed.

10b. Append a dated entry at the tail of `docs/strategy.md`
(`## Session 2026-07-07<letter> — F1 size-prior identity: first honest nonzero F1`),
3–8 bullets: what moved, the ambiguity-→-unreported rule, the train/test discipline, the
production-lane guard, what stays open (curve signatures need a train-side reader run;
chair/squat_toilet/sink overlap is the coverage ceiling).

### Step 11 — Final gates + commit

```powershell
cd c:\Users\teza_\OneDrive\Desktop\PlingPeat
python3 -m pytest pipeline/scripts/ -q     # expect: N + 13 passed (N = Step 1 baseline), 0 failed
git status                                  # confirm ONLY the six repo files changed/added
```
Commit ritual (repo law): separate logical commits, explicit paths, NEVER `git add -A`,
never push:
```powershell
git add pipeline/scripts/kind_priors.py pipeline/scripts/test_kind_priors.py pipeline/scripts/svg_plan_reader.py pipeline/scripts/test_svg_plan_reader.py
git commit -m "F1 size-prior identity lane: train-derived kind bands, unique-membership emission, off-by-default"
git add qa/reports/floorplancad-f1-priors-2026-07-07.md docs/strategy.md
git commit -m "session 2026-07-07 wrap: first nonzero F1 (priors report + strategy entry)"
```

## Edge cases a weaker model would miss (all personally verified in code this session)

1. **The static tripwire bans identifier substrings, not just attribute reads.**
   `test_svg_plan_reader.py:134-135` asserts the needles `"semantic"`, `"inkscape"`,
   `"INK_NS"`, `"instance_id"` never appear in `svg_plan_reader.py` CODE tokens, and
   `"semantic-id"`/`"instance-id"`/`"inkscape"` in no string literal except the module
   docstring (`:136-140`). Naming a variable `semantic_kinds` or writing a comment string
   "maps semantic ids" inside svg_plan_reader.py fails the suite. The new usage text goes
   in the module docstring ONLY.
2. **Two existing pins assert the kindless default and must stay green untouched:**
   `test_svg_plan_reader.py:189` (`assert "kind" not in e` — read_sheet called with NO
   priors at :179) and `:257` (`card["F1_identity"]["accuracy"] == 0.0` — run_baseline
   called with NO priors at :252). Both pass automatically iff the new parameter defaults
   to None and gates every new behavior. Do not edit either assertion.
3. **Unreported ≠ skipped in F1.** `norm_kind(None) → ""` (`benchmark_reader.py:65-67`) and
   `score_identity` counts a `gk != pk` pair as a miss with confusion key `"table->"`
   (`:146-154`). Only F2 has 'unreported' semantics and only F3/F5 default pred silence to
   True. Consequence: the per-kind table gets a `""` row whose `pred` count IS the
   unreported counter (verified in the real cards: `'': {gt: 0, ...}` appears) — the report
   code must exclude it from the kinds table and surface it as the unreported line.
4. **Emit GT's exact vocabulary.** `KIND_SYNONYMS` (`benchmark_reader.py:61-62`) normalizes
   `tv_cabinet → tv_console` on BOTH gt and pred sides, so emitting the raw GT name
   (`RAW_CLASSES` values, `floorplancad_adapter.py:64-74`) always compares equal. Inventing
   "nicer" names (e.g. `fridge`) scores as wrong even when the object is right.
5. **The baseline CLI option parser rejects non-digit values.** `svg_plan_reader.py:367-372`
   exits with usage unless `rest[1].isdigit()` — simply adding `"priors"` to the accepted
   tuple breaks because a path is not a digit. The elif branch in step 5f is required.
6. **`aggregate()` silently drops `per_kind`.** `benchmark_reader.py:363-366` sums only
   `n`/`hits` for F1 — a corpus per-kind table MUST be summed from the cards' integer
   `per_kind` counts (gt/pred/hit), never recomputed from per-card accuracies and never
   read off `aggregate()`.
7. **svg-unit gt files poison bands by ~100×.** 3,257/5,502 test gt files (59.2%) carry
   raw svg-unit dims; the runner pre-skips them (`svg_plan_reader.py:252-255`) and the
   derivation must too (`meta.units != "mm"` → skip + count). Test 2 in step 4 mutation-pins
   this.
8. **Openings would collide with furniture bands.** Corpus median door ≈ 999 mm
   (`gt-test-00/summary.md:5`); if `derive()` iterates `doc["openings"]` a phantom ~1 m
   band lands inside table/cabinet territory. Elements only (step 3, test 3).
9. **Pred dims are dilated, rounded ints.** Cluster bboxes come out of rasterize→CLOSE→label
   at `round(wmm)` (`plan_cluster.py:145-147`) with ±2·res ≈ ±12 mm typical error (the
   existing test tolerance at `test_svg_plan_reader.py:185`). Bands derived from exact GT
   dims match nothing without PAD_MM. Conversely on huge sheets `res_eff` coarsens up to
   `extent/3000` (`svg_plan_reader.py:157`) and dims quantize >100 mm — those elements
   naturally go unreported. Do NOT add per-sheet dynamic slack: widening intervals can
   flip a zero-candidate case into a one-candidate emission on coarse data (a new
   false-accept channel).
10. **Kind emission can re-pair exact-IoU ties.** `match_elements` sorts candidates by
    `(-iou, kind_mismatch, i, j)` (`benchmark_reader.py:114-117`) — once preds carry kinds,
    equal-IoU ties prefer same-kind partners. Matched COUNT stays 1,014; if per-pair
    assignments shift on a tie that is by-design, not a bug. Do not "fix".
11. **Adapter batch default out dir is `<svg-dir>-gt`.** `floorplancad_adapter.py:674` —
    omitting the out-dir arg creates `train-00-gt`, breaking the `gt-train-00` naming
    precedent this plan (and the follow-up lanes) depend on. Always pass it explicitly.
12. **Completion markers: summary.md / report.md are written LAST.**
    `floorplancad_adapter.py:624-626` and `svg_plan_reader.py:288-291`. Poll those files,
    not process lists. manifest.jsonl / cards.jsonl stream row-by-row, so partial files
    exist DURING a healthy run.
13. **The full baseline run cannot use the in-tool background lane** (865 s + overhead >
    10-min cap) — detached `Start-Process` with log redirect is the repo canon; the two
    adapter batch runs, measured at 11 ms/file this session, CAN run foreground with
    `timeout 600000`.
14. **Analyze cards.jsonl with python only** — PowerShell 5.1 `ConvertFrom-Json` fails on
    the cards' deep keys (standing repo note, re-confirmed by using python for all
    this session's card analysis).
15. **`load()` must fail before the loop, not inside it.** `run_baseline`'s per-sheet
    try/except converts exceptions into `skipped["error"]` rows (`svg_plan_reader.py:250,
    278-281`) — lazily loading priors per sheet would turn a typo'd path into 2,245 error
    rows that LOOK like corpus problems. Load once, before iterating (step 5d).
16. **`render_baseline_report` is called positionally in tests** —
    `test_report_without_cards_is_honest` (`test_svg_plan_reader.py:272-274`) passes 4
    positional args; `priors_note` must be keyword-with-default and the `priors_note=None`
    branch must leave the existing report text unchanged.
17. **Aspect lower bound can dip below 1.0 after padding.** lo/hi are sorted so every real
    aspect ≥ 1.0; `q10(aspect)/1.15 < 1.0` for near-square kinds — clamp with
    `max(1.0, ...)` (step 3) or square elements fall out of their own kind's band.
18. **Zero-division guards in the report table:** `score_identity` creates pred-only rows
    (`per.setdefault(pk, ...)["pred"] += 1`, `benchmark_reader.py:149`) so a kind row can
    have `gt == 0` (and the `""` row always does) — recall must be `'n/a'`-guarded, not
    divided.

## Acceptance criteria

Each is a command + observable result:

1. `python3 -m pytest pipeline/scripts/ -q` (repo root) → **`N + 13 passed`, 0 failed**
   (N = Step 1's recorded green baseline; +13 = 9 in test_kind_priors.py + 4 new in
   test_svg_plan_reader.py). Count must never drop below N.
2. `python3 -m pytest pipeline/scripts/test_svg_plan_reader.py -q` → all pass, including
   the UNCHANGED pins: `test_read_sheet_clusters_and_openings`,
   `test_run_baseline_skips_and_scores`, `test_reader_source_never_names_annotation_attrs`,
   `test_read_sheet_is_annotation_blind`, `test_read_sheet_blind_at_corpus_density`,
   `test_read_sheet_blind_on_real_corpus_sheet`, `test_candidate_type_never_earns_subtype_credit`.
3. `Test-Path C:\Users\teza_\studio-datasets\floorplancad\gt-train-00\summary.md` and
   `...gt-train-01\summary.md` → True; each summary shows parse-failed 0 (≤5 tolerable)
   and calibrated-to-mm in 35–46%; both `--selftest` runs print
   `selftest PASS: adapter output is benchmark_reader-clean`.
4. `C:\Users\teza_\studio-datasets\floorplancad\priors\kind-priors-train.json` exists with
   `schema == "interior-ai/kind-priors@0.1"`; every `kinds` row has `n >= 50` and a
   non-empty `provenance`; `bed.hi_mm` band overlaps [1905, 2032]
   (cross-check source: `knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md:30-33`).
5. `C:\Users\teza_\studio-datasets\floorplancad\baseline-test-00-f1priors\report.md` exists;
   cards.jsonl has exactly 5,502 rows; skipped == `{"svg-unit": 3257, "svg-missing": 0,
   "error": 0}`; 2,245 sheets scored.
6. **THE number moves up:** aggregate F1 accuracy in the new report.md **> 0.0**
   (baseline: 0.0 = hits 0/1014, verified this session). The report also states emitted
   count, emitted precision, unreported count, and a per-kind table whose counts satisfy
   `sum(pred over kinds) + unreported == 1014`.
7. **Nothing else moves:** detection matched == 1,014 (±2 max, tie-break note) and F4
   recall/precision/per-type recall identical to
   `qa/reports/floorplancad-baseline-2026-07-06.md`.
8. Step 9's identity script prints `NO-PRIORS PRED IDENTICAL: True` — the default lane's
   pred for an already-scored corpus sheet is unchanged.
9. `git diff --name-only HEAD~2` (after the two commits) lists EXACTLY:
   `pipeline/scripts/kind_priors.py`, `pipeline/scripts/test_kind_priors.py`,
   `pipeline/scripts/svg_plan_reader.py`, `pipeline/scripts/test_svg_plan_reader.py`,
   `qa/reports/floorplancad-f1-priors-2026-07-07.md`, `docs/strategy.md` — no priors JSON,
   no gt.json, no cards, no PNGs, and none of: `benchmark_reader.py`,
   `floorplancad_adapter.py`, `plan_cluster.py`, `glazing_candidates.py`,
   `placement_gate.py`, `gen_floor2_v4_specs.py`, `raster_overlay.py`, `build_floor.py`.
10. Each of the three patterns must hit individually (a single alternation cannot prove
    all three are present):
    ```powershell
    foreach ($p in 'provenance','unreported','owner-signed') { if (-not (Select-String -Path qa\reports\floorplancad-f1-priors-2026-07-07.md -Pattern $p -Quiet)) { "MISSING: $p" } }
    ```
    → empty output (the report carries provenance, the honest-unreported statement, and
    the production-lane guard).

## Do NOT

- **Do NOT tune bands against the test split.** Parameters are fixed a priori (q10/q90,
  PAD_MM 50, ASPECT_PAD 1.15, MIN_SUPPORT 50). If test-side precision disappoints, record
  it; refinement happens on a TRAIN-side split in a future slice. One derive → one scored
  run.
- **Do NOT emit a kind on ambiguity, low support, or "best guess".** Unique band membership
  or nothing. `return cands[0] if cands else None` is the named enemy mutant. Never write
  `"kind": None` either — omit the key.
- **Do NOT default anything in the scorer or touch `benchmark_reader.py` at all.** The
  engine's honesty semantics (unreported-counts-wrong for F1) are the measuring stick; a
  reader-side change may never be compensated scorer-side in the same change.
- **Do NOT wire priors into the production/owner lane.** No imports of `kind_priors` in
  `placement_gate.py`, `gen_floor2_v4_specs.py`, `raster_overlay.py`, `build_floor.py`.
  Identity in owner projects is owner-signed semantic truth (two-layer law); at most a
  future overlay SUGGESTION column — explicitly out of scope here.
- **Do NOT break annotation blindness.** svg_plan_reader.py reads geometry attributes only;
  no code token may contain `semantic`, `inkscape`, `INK_NS`, or `instance_id`
  (`test_svg_plan_reader.py:134`), and priors decisions use only w/d derived from ink.
- **Do NOT commit corpus derivatives.** gt-train dirs, the priors JSON, cards.jsonl, preds,
  overlays all stay under `C:\Users\teza_\studio-datasets\` (CC BY-NC, no redistribution;
  the repo lives in OneDrive = cloud sync). Only the aggregate qa report + strategy entry
  enter git.
- **Do NOT touch** `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.claude/settings.json`,
  `.gitattributes` (hook-enforced, PR-only). No `git add -A`, no push, no destructive shell.
- **Do NOT overwrite or re-run into `baseline-test-00\`** — it is the frozen 34c1a08
  baseline the before/after comparison depends on. The priors run gets its own out dir.
- **Do NOT type openings.** This item touches element `kind` only; pred openings keep
  `type="candidate"` (pinned: `test_candidate_type_never_earns_subtype_credit`,
  `test_svg_plan_reader.py:195-206`) — a door/window classifier is a different plan.
- **Do NOT derive from `gt-test-00`** or let any test-split file into `derive()` inputs —
  train/test separation is the legitimacy of the whole exercise.
- **Do NOT guess scale for svg-unit sheets** anywhere in the lane (derivation skips them;
  the runner already skips them at `svg_plan_reader.py:252-255`).
