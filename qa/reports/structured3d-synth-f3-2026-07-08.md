# Structured3D backwards-learning — synth F3 lane (first pred≠gt indoor score) + F2 code-unblock

**Date:** 2026-07-08 · **Engines:** `pipeline/scripts/synth_plan_2d.py` v1.0 →
`svg_plan_reader.py` v2 → `benchmark_reader.py`; `structured3d_adapter.py` (labels sidecar +
`wall_lines`) · **Corpus:** Structured3D first-200 scenes
(`C:\Users\teza_\studio-datasets\structured3d\gt-sample\`, run artifacts in `synth-f3\`:
`cards.jsonl`, `report.md`) · **Adversarially verified** (5-lens workflow, 2026-07-08).

Two advances in the Structured3D backwards-learning lane, both landed with the house
no-silent-pass / never-fabricate discipline:

## 1. The 2D-plan synthesizer — F3 is now a REAL pred≠gt number, not a symmetric selftest

**The gap it closes** (plan-extraction memory: *"reader-scores need a 2D synthesizer"*): until
now the Structured3D lane could only run `benchmark_reader` **gt-vs-gt**, a symmetric selftest
that cannot catch an error (a convention flip, an over-emitted flag — all self-match with
distance 0). The 3D corpus is the indoor/outdoor **answer key**; nothing drew the **2D a reader
would see** so the reader could be RUN and scored.

`synth_plan_2d.py` turns a Structured3D `gt.json` into an **annotation-blind** 2D SVG (furniture
footprints as `<rect>`; optional walls/glazing as `<line>`), runs `svg_plan_reader` on it, and
scores against the same `gt.json`. The indoor label is **never drawn** — two gt docs differing
only in `indoor` synthesize to a **byte-identical** SVG (pinned by `test_synth_plan_2d`, and
independently re-verified by the f3-leakage adversarial lens: no leakage through order,
coordinates, count, viewBox, or `--walls`). So F3 measures whether **geometry alone** recovers
the room semantics — it cannot leak the answer key into the reader's input.

### The number (200 scenes)

| metric | value | meaning |
|---|---|---|
| **F3 indoor accuracy** | **94.4%** on **1,741** matched pairs | FIRST pred≠gt indoor score on any corpus |
| F3 wrong calls | 97 | = the OUTDOOR (balcony/garden) pieces — exactly where an indoor upgrade must win |
| detection recall | 10.6% (2,856 / 26,946) | LOW BY EXPECTATION (see below) — not a soundness pass |
| detection precision | 74.7% | |
| per-scene F3 verdicts | PASS 143 · REVIEW 33 · UNWIRED 24 | |

**What the F3 number is** — `svg_plan_reader` has **no indoor classifier**, so `benchmark_reader`
scores every matched pred element as `indoor=True` (silence = ordinary this-floor-indoor). F3
94.4% is therefore the **always-indoor baseline**: it equals the indoor fraction among matched
pairs, and its `wrong_ids` are the outdoor pieces. **The value is not the number** (the adapter's
meta already implies it) — it is that the **loop is now wired end-to-end**: an indoor-inference
upgrade (e.g. generalising `zone_flag` beyond its south-facade case) is an immediately
**scoreable pred≠gt delta** over this baseline, on real balcony/garden ground truth.

### Honest caveats (adversarially confirmed, not hidden)

- **Detection recall is ~a tenth of GT — and F3 is scored on that detected subset.** ~63% of
  Structured3D "objects" are sub-150 mm decor (cups, books, picture frames — median object
  447 mm) that `plan_cluster` screens as thin ink **by design**; boxes >~3.6 m on both axes drop
  as `merged_blob`; and furniture drawn within `CLOSE_MM` (40 mm) — a bed with a flush nightstand,
  stacked cushions — **merges into one cluster matching neither GT box**, so both leave the F3
  set. F3 n = 1,741 ≈ 8.6% of the 20,302 indoor-carrying GT elements. The merge limit is pinned
  by `test_synth_plan_2d.test_furniture_within_close_mm_merges_and_drops_from_f3`.
- **The subsample is NOT optimistically biased against outdoor (measured).** Matched-subset
  outdoor fraction **5.6%** (97/1,741) vs corpus outdoor rate **4.7%** (954/20,302) — close, and
  if anything the detected set is slightly *enriched* in outdoor. So 94.4% is representative of
  the whole, not a number that quietly dropped the hard (outdoor) cases.
- **Next slice to raise the scoreable share:** a realistic size-filtered draw (a plan shows
  furniture, not every prop) + instance separation, so clustered furniture stops merging. The
  hard *detection* test remains FloorPlanCAD's real symbol ink, not these clean rectangles.

## 2. F2 code-unblock — `structured3d_adapter` labels sidecar (data-limited, not code-limited)

**The blocker, precisely** (verified against the raw data, not assumed): every `bbox_3d.json`
object carries only `{ID, basis, centroid, coeffs}` — **no class label**. `SOURCE.txt`: the
category needs pairing the downloaded instance masks (still zipped, ~1 GB PNGs) with the
**semantic masks that live in the un-downloaded render zips**, or 3D-FRONT layout JSON. The GT
**rot IS derivable** (basis yaw); only the kind was missing. So F2 was blocked in *code*, not
just data.

`convert(labels={obj_id: kind})` now accepts an **optional** per-object sidecar of caller-supplied
**real** labels; a labeled object emits `kind` + `rot`, lighting up **F2_facing** (UNWIRED →
scored). Proven end-to-end by `test_labels_sidecar_wires_kind_rot_and_f2`
(UNWIRED→PASS on gt-vs-gt, n=2). Without a sidecar the output is **byte-identical** to the blocked
default (no kind, no rot, `kind_blocked` loud, F2 UNWIRED) — re-verified by the f2-sidecar
adversarial lens. **No kind is ever fabricated** (`kind_priors`-style suggestion is a pred-side
lane, never GT). This converts *"F2 blocked in code, no path"* → *"F2 wired, awaiting an
injectable `{ID→kind}` file"*.

**⚠ rot-convention footgun (labelled, LOW).** The emitted `rot` is the adapter's **native yaw**
(ccw from +x, forward=basis[0]) — a ~270° offset from `benchmark_reader`'s declared `build_floor`
`front=(sin,-cos)` convention. It produces **no wrong number today** (every live path is gt-vs-gt
or has no pred rot) and is emitted natively **on purpose**: the Structured3D-vs-build_floor
y-axis **handedness is unvalidated** (no rot-emitting reader exists to check against), so a
"reconciled" value could bake in a mirror/180° error that *looks* correct. Reconcile offset AND
handedness against a real reader before trusting F2 angular buckets (`ROT_CONVENTION`).

### To actually run F2 (owner-gated data — the one remaining step)

Both label sources are **owner-access-gated** (nothing on disk today):
1. **3D-FRONT** (cleaner: category + orientation in one JSON) — access via the ToU/email flow in
   `studio-datasets/ACCESS-REQUESTS.md §1`; then a small `{scene: {obj_id: kind}}` extractor →
   `python structured3d_adapter.py --batch <slice> <out> labels.json` and F2 scores.
2. **Structured3D render masks** — pair the (downloaded) instance masks with semantic masks from
   the render zips (`ACCESS-REQUESTS.md §2`, hundreds of GB, pull per-slice).

## 3. `wall_lines` (enabling infrastructure)

`structured3d_adapter` now also emits `gt['wall_lines']` (every WALL plane's floor-level trace,
deduped; schema mirrors `floorplancad_adapter`) — the plan skeleton the synthesizer draws and the
input `svg_plan_reader`'s oracle-walls lane consumes. 14,219 segments over 200 scenes; the
walllines adversarial lens confirmed it changed **no** existing channel (selftest still 0
failures, F3/F4/F6 recall 1.0). The `--selftest` now asserts F2 UNWIRED in the blind lane and
F2 PASS in the kinded lane, so the honesty contract holds in both build modes.

---

*Adversarial verification: `verify-synth-and-f2-unblock` workflow (5 diverse-lens skeptics, each
required to RUN code). 0 CRITICAL/HIGH; 2 MEDIUM (F3 subsample size/representativeness — fixed in
the report + a pinned merge-limit test) + 1 LOW (rot footgun — hardened doc). f3-leakage and
wall_lines lenses: clean. 765 tests green.*
