# qa/priors/ — corpus prior-band artifacts (doubt-instrument inputs)

`kind-priors-floorplancad-train.json` — per-kind size/aspect quantile bands
(schema `interior-ai/kind-priors@0.2`, 19 kinds, 17,973 elements) derived from
the FloorPlanCAD TRAIN split (`gt-train-00` + `gt-train-01`, mm-calibrated
files only) by `pipeline/scripts/kind_priors.py --derive` on 2026-07-07, plus
the per-kind curve signature merged by `derive_curve_priors.py`. Byte-level
size-band reproducibility re-verified 2026-07-13 (0 field mismatches against a
fresh `--derive` over the same on-disk corpus).

Consumers (all advisory, REVIEW-never-FAIL, two-layer law):

- `self_audit.py` auto-discovers any `*kind-priors*.json` under `qa/` or
  `knowledge/` — landing this file flips the anomaly `prior_band` coverage
  lane from UNWIRED to READ and feeds `prior_kind` corroboration into
  `confidence.py`.
- `anomaly_flags.py` checks a claimed kind's footprint against its corpus band
  (MEDIUM when FAR outside; built-in gross bounds still supersede at HIGH).
  Vocabulary policy lives in `anomaly_flags.PRIOR_EXEMPT_KINDS` /
  `PRIOR_KIND_ALIASES` — see the comments there for why `cabinet`/`headboard`
  are exempt and why `tv_console → tv_cabinet` is refused.
- `flag_localization.py` (benchmark F7) measures the band's added catching
  power via the `size_off_prior_band` mutation class.

REFERENCE tier: bands are drawn-symbol statistics from a Chinese CAD corpus,
not Thai statute and not owner truth — they may only raise DOUBT, never gate a
deliverable and never re-label a piece. `knowledge/codes-th/` outranks
everything here.

LICENSE NOTE (FloorPlanCAD is CC BY-NC 4.0): this file holds only derived
aggregate quantile statistics — no corpus sheets, geometry, or annotations are
redistributed (same rule the test fixtures already pin). Use stays in the
internal benchmark/doubt-calibration lane, matching the recorded dataset
position in `studio-datasets/ACCESS-REQUESTS.md`; nothing derived from it may
enter a client deliverable. Repo is local/unpushed; revisit before any public
push.

Regenerate:

```
cd pipeline/scripts
python kind_priors.py --derive out.json \
    C:/Users/teza_/studio-datasets/floorplancad/gt-train-00 \
    C:/Users/teza_/studio-datasets/floorplancad/gt-train-01
```
