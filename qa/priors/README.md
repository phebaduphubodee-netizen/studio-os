# qa/priors/ — corpus prior-band artifacts (doubt-instrument inputs)

TWO artifacts are live. Consumers discover BOTH and consult them under the
multi-corpus rules (2026-07-14, `kind_priors.py` module docstring): each doc
keeps its own unique-membership structure; corroboration needs >=1 doc uniquely
agreeing AND no doc uniquely disagreeing; an anomaly band flag needs FAR-outside
on EVERY doc that carries the kind.

## kind-priors-floorplancad-train.json (drawn-symbol bands)

Per-kind size/aspect quantile bands
(schema `interior-ai/kind-priors@0.2`, 19 kinds, 17,973 elements) derived from
the FloorPlanCAD TRAIN split (`gt-train-00` + `gt-train-01`, mm-calibrated
files only) by `pipeline/scripts/kind_priors.py --derive` on 2026-07-07, plus
the per-kind curve signature merged by `derive_curve_priors.py`. Byte-level
size-band reproducibility re-verified 2026-07-14 (0 field mismatches against a
fresh `--derive` over the same on-disk corpus, AFTER the multi-corpus derive
flags landed — the new flags are opt-in and change nothing by default).

## kind-priors-structured3d-first3500.json (real-furniture bands)

Per-kind size bands (size-only — no curve lane ran) from the Structured3D
first-3500 labelled corpus (`gt-corpus-labeled`, 3,500 mm gt.json, 73,346
labelled objects out of 444k — labels come from the panorama-semantic sidecar
`corpus_labels_all.json`), derived 2026-07-14 with `--source structured3d
--max-dispersion 3.0`. Eight kinds kept: bathtub, bed, chair, desk, dresser,
nightstand, refrigerator, sink. Five REFUSED as degenerate (recorded with
measured ratios in `excluded_degenerate`): `sofa` (10–90 short-side ratio
22.7× — instance labels include cushion/section fragments), `cabinet` (base
units → full-height closets, 4.0×), `table` (coffee → dining, 3.7×), `toilet`
(fragment tail, 5.4×), `tv_panel` (wall-strip class, 4.1×). Any threshold in
[2.6, 3.5] yields the same partition (kept max 2.48, refused min 3.66) — the
cut sits in a natural gap, not on a knife edge. Frozen-constant pin:
`test_kind_priors.py::test_committed_structured3d_artifact_frozen_constants`.

What it buys (measured on PRJ-2026-002 v4, the known-correct probe):
`bed` 2134×1981 corroborates (doubt 281→271); the other kind doubts stay
honestly open — real-furniture size populations overlap too much for unique
membership (chair≈nightstand≈refrigerator), and the HEIGHT lane was probed and
REFUTED (spec `h` is a functional height, Structured3D `h` is a full bbox —
3/11 known-correct pieces sit outside their kind's h-band, including the bed).
See `qa/reports/structured3d-kind-priors-2026-07-14.md`.

## Consumers (all advisory, REVIEW-never-FAIL, two-layer law)

- `self_audit.py` auto-discovers any `*kind-priors*.json` under `qa/` or
  `knowledge/` and returns ALL of them (sorted-path order; the pre-2026-07-14
  first-match-wins return made a second artifact a silent no-op) — landing a
  file flips the anomaly `prior_band` coverage lane from UNWIRED to READ and
  feeds `prior_kind` corroboration into `confidence.py`. The LIVE doc set is
  a frozen tripwire: `test_live_repo_priors_doc_set_is_pinned` asserts exactly
  {floorplancad, structured3d} — a stray artifact (e.g. a re-derive without
  `--max-dispersion` parked here) turns the suite red instead of silently
  joining the outside-ALL veto; adopting a third corpus means updating that
  pin deliberately. Coverage lines name doc SOURCES, never just a count.
- `anomaly_flags.py` checks a claimed kind's footprint against its corpus band
  (MEDIUM when FAR outside EVERY carrying doc; built-in gross bounds still
  supersede at HIGH). Vocabulary policy lives in
  `anomaly_flags.PRIOR_EXEMPT_KINDS` / `PRIOR_KIND_ALIASES` — see the comments
  there for why `cabinet`/`headboard` are exempt and why
  `tv_console → tv_cabinet` is refused. `side_table → nightstand` was
  considered for the Structured3D doc and REFUSED: nightstand is a SUBSET of
  side_table (sofa-side tables are not nightstands), and a subset band is
  unsound in the anomaly direction (it would false-flag legit large side
  tables); the corroboration it could add was measured to be zero on v4.
- `flag_localization.py` (benchmark F7) measures the bands' added catching
  power via the `size_off_prior_band` mutation class; with both docs live the
  mutation must clear EVERY carrying doc's far-edge (see the multi-corpus F7
  record `flag-localization-priors-multi-2026-07-14.md`). The chair-family
  corpus-only window CLOSES, and part of it closes into deliberate
  un-flagging, stated plainly: an armchair long side in 963–1300 mm was
  MEDIUM-flagged under FloorPlanCAD alone and is now unflagged, because real
  chairs reach 989 mm (S3D q90) and the outside-ALL rule reads such sizes as
  corpus-plausible — the old flag there was drawn-symbol narrowness, i.e. a
  false doubt on real furniture. Above 1300 mm the built-in armchair bound
  still fires HIGH. F7 mutations for this class drop 4 → 1 accordingly
  (skips counted, never hidden).

REFERENCE tier: bands are corpus statistics (Chinese CAD drawn symbols;
synthetic-home real furniture), not Thai statute and not owner truth — they may
only raise DOUBT, never gate a deliverable and never re-label a piece.
`knowledge/codes-th/` outranks everything here.

LICENSE NOTE — FloorPlanCAD is CC BY-NC 4.0; Structured3D is free for
non-commercial research only (agreement on file, `studio-datasets/
structured3d/SOURCE.txt`; position recorded in
`studio-datasets/ACCESS-REQUESTS.md`). Both files hold only derived aggregate
quantile statistics — no corpus sheets, geometry, renders, or annotations are
redistributed (same rule the test fixtures already pin). Use stays in the
internal benchmark/doubt-calibration lane; nothing derived from either corpus
may enter a client deliverable. Repo is local/unpushed; revisit before any
public push.

Regenerate:

```
cd pipeline/scripts
python kind_priors.py --derive out.json \
    C:/Users/teza_/studio-datasets/floorplancad/gt-train-00 \
    C:/Users/teza_/studio-datasets/floorplancad/gt-train-01
python kind_priors.py --derive s3d.json \
    C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled \
    --source structured3d --max-dispersion 3.0
```
