# Structured3D real-furniture kind-priors: the corroboration tier's second corpus — landed, and its ceiling measured

**2026-07-14 · branch tier1-self-doubt-suite · answers the roadmap line of
`kind-priors-wiring-2026-07-13.md` §7** ("a Thai-market prior set, or Structured3D
real-furniture bands once labelled, would corroborate the bed/side-table reads this corpus
honestly cannot"). The labels already existed — `corpus_labels_all.json` (3,482 scenes,
73,348 instance labels from the F2 panorama-semantic lane) sat beside 3,500 labelled
`gt.json`, so "once labelled" was an unlocked door.

**Headline: doubt-score 281 → 271.** The `bed` 2134×1981 kind doubt corroborates off real
furniture (5,481 real beds; unique band hit). That is ONE of the 15 open kind doubts — and
the honest half of this report is that the other 14 CANNOT be corroborated by this corpus
under the established rule, measured, not assumed:

- **Real-furniture size populations overlap too much for unique membership.** A 500×500
  side table hits {chair, nightstand}; a 680×640 armchair hits {chair, refrigerator};
  1800×900 bathtub hits {bathtub, desk}. Unique-membership is the confidence rule and it
  stays — loosening it to "inside the claimed band" would be flattering shape #11.
- **The height lane was probed and REFUTED before a line of it was written.** Spec `h` is a
  FUNCTIONAL height (bed 600 = platform, toilet 400 = seat); Structured3D `h` is the full
  bbox z-extent (bed ≈ 840–1763 incl. headboard). 3/11 known-correct v4 pieces sit outside
  their kind's h-band — including the bed, so an h-tie-break would have KILLED the one
  corroboration this lane exists to make. No h code shipped; this paragraph is its grave
  (same doctrine as the refuted asset lever).
- **Five S3D label classes are not size populations at all** and were REFUSED at derive
  time by a pre-stated dispersion rule (10–90 quantile ratio > 3.0 on either footprint
  side): `sofa` 22.7× (≥20 % of instances are cushion/section fragments — short-side decile
  row: 52, 107, 107, 727, 831 …), `toilet` 5.4× (fragment tail), `table` 3.7×
  (coffee→dining), `cabinet` 4.0× (base units→closets), `tv_panel` 4.1× (wall-strip class).
  Disclosure: the threshold was chosen with the data visible, but any cut in [2.6, 3.5]
  yields the identical partition (kept max 2.48 = desk, refused min 3.66 = table) — the
  criterion sits in a natural gap, and the refusals are recorded WITH their ratios in the
  artifact's `excluded_degenerate` (dropped-and-counted, never silent).
- **`side_table → nightstand` alias REFUSED** by the subset/superset asymmetry: corpus
  `chair` ⊇ repo `armchair` is sound in both lanes, but `nightstand` ⊂ repo `side_table`
  would false-flag legitimate large side tables in the anomaly direction — and the
  corroboration it could buy was measured to be ZERO on v4 (300 mm tables sit below the
  band; 500/600 mm tables are chair-ambiguous).

## 1. What landed

1. **`qa/priors/kind-priors-structured3d-first3500.json`** — 8 kinds (bathtub, bed, chair,
   desk, dresser, nightstand, refrigerator, sink; 30,000+ instances behind them), size-only
   (no curve lane ran on S3D), schema @0.2, frozen-constant pinned
   (`test_committed_structured3d_artifact_frozen_constants`). License: Structured3D is
   non-commercial-research-only (agreement on file, `SOURCE.txt`); the artifact holds only
   aggregate quantile statistics, nothing redistributed.
2. **`kind_priors.derive(source=, max_dispersion=)`** — both opt-in; default output proven
   byte-identical (the committed FloorPlanCAD artifact re-derives with 0 field mismatches
   AFTER this change, re-verified live).
3. **Multi-corpus consumption** (the real wiring work): every consumer now takes one doc or
   a list, each doc keeping its OWN unique-membership structure (corpora are never pooled
   into one candidate set):
   - corroboration (`build_prior_context`): ≥1 doc uniquely agrees AND no doc uniquely
     disagrees — STRICTER than any single doc; an independent corpus actively suggesting a
     different kind is counter-evidence and can never be outvoted into a 0.70.
   - anomaly band flag: FAR-outside EVERY carrying doc — a size one corpus vouches for is
     not anomalous because another draws the symbol differently.
   - `self_audit._load_priors` now returns ALL discovered artifacts. The old
     first-match-wins return was a live landmine: this very lane's artifact would have been
     a silent no-op (sorts after `floorplancad`), and a future file sorting BEFORE it would
     have silently REPLACED the FloorPlanCAD bands. Pinned by
     `test_load_priors_returns_EVERY_artifact_never_first_match_wins`.
   - normalizer split, deliberate: `kind_priors.as_docs` is STRICT (a garbage doc raises →
     confidence coverage reports ERROR, preserving the 2026-07-13 dead-lane finding);
     `anomaly_flags._priors_docs` is TOLERANT (drops garbage → the sweep never crashes),
     matching each module's pre-existing contract.
4. **F7 generator** targets beyond the UNION of hi edges with the short side in the
   INTERSECTION of lo bands (no intersection → counted skip); report stems are
   frozen-per-config (none → 2026-07-08, one doc → 2026-07-13 — regenerates
   byte-identically, verified — ≥2 docs → `flag-localization-priors-multi-2026-07-14`).

## 2. Measurements (all run live on PRJ-2026-002)

| measurement | before | after |
|---|---|---|
| self_audit doubt-score | 281 (29 open: 1 H / 17 M / 11 L) | **271 (28 open: 1 H / 16 M / 11 L)** |
| what moved | — | ONLY the bed kind doubt (corroborated by S3D); nothing else shifted |
| new anomaly flags on known-correct v4 | 0 | **0** (probed pre-change, confirmed post) |
| F7 macro-recall / precision / overfires | 1.0 / 0.952 / 0 (single-doc) | **1.0 / 0.951 / 0** (multi) |
| size_off_prior_band mutations | 4/4 caught | **1/1 caught** (3 windows closed, skips counted) |
| tests | 1368 | **1385** (+17, all green) |
| FPC artifact reproducibility | byte-verified 07-13 | **re-verified post-change, 0 mismatches** |

**The 4 → 1 window closure, stated without varnish:** the three lost mutations are the
armchair→chair pieces. Real chairs reach 989 mm long (S3D q90), so the outside-ALL far-edge
moves 963 → 1385 mm while the built-in armchair HIGH bound sits at 1300 mm: an armchair long
side in **963–1300 mm was MEDIUM-flagged under FloorPlanCAD alone and is now unflagged** —
that range is corpus-plausible real furniture (lounge chairs live there), so the old flag is
judged drawn-symbol narrowness, i.e. a false doubt. The same un-flagging applies to every
kind BOTH docs carry where the real-furniture band extends past the drawn-symbol band — the
review panel reproduced armchair 530×1059, **refrigerator 1000×1150 and sink 550×1600 going
MEDIUM → nothing** (bed and bathtub move far less). This is the deliberate loosening
direction of the multi-corpus rule, it is measured (F7 skips counted, precision 0.952 →
0.951), and it is the price of admission for the corroboration tier being honest about what
real furniture looks like. Above the built-in bounds (armchair 1300 mm) the HIGH tier still
fires. If the owner ever wants the old tighter doubts back for a specific kind, the lever is
a BETTER band (Thai-market SKU dims), not re-narrowing to drawn symbols.

## 3. Probe discipline (repo ritual: probed on KNOWN-CORRECT reads before a line changed)

Three scratch probes ran before any repo edit: (1) raw S3D bands vs all 26 v4 pieces →
exposed the degenerate `sofa` band killing every uniqueness and ZERO naive corroborations;
(2) height bands from `bbox_3d.json` (73,346 labelled objects) → refuted the h-lane on
known-correct heights; (3) the final refused-set simulation → predicted exactly one
corroboration (bed), zero new flags, FPC corroborations (sofa, wardrobe) preserved. The live
after-measurements match the probe's predictions 1:1.

## 4. Review (5 lenses + per-finding refutation panel, 21 agents)

**16 findings raised → 14 confirmed by refuters → deduplicated to 8 distinct defects, ALL
fixed + pinned before this commit** (three lenses independently converged on the stem defect,
two on the alias defect — convergence, not inflation):

1. **Live doc-set unpinned (MEDIUM, THE flattering channel):** `_load_priors` admits any
   schema-matching `*kind-priors*.json` under `qa/**`/`knowledge/**`, and under outside-ALL
   an added doc can only SUPPRESS flags for kinds already carried — a re-derive without
   `--max-dispersion` parked in `qa/priors/` would have silently vetoed every sofa doubt
   with coverage still READ. Fixed as a declared TRIPWIRE: the live repo doc set is now a
   frozen pin (`test_live_repo_priors_doc_set_is_pinned` — adopting corpus #3 means updating
   the pin deliberately), and every coverage line names its doc SOURCES, not just a count.
2. **Report stem keyed by doc COUNT (MEDIUM, 3 lenses):** an S3D-solo run — or a kinds-less
   doc that passes `KP.load` — would have overwritten the committed 2026-07-13 FloorPlanCAD
   F7 record. `_report_stem` is now IDENTITY-keyed (frozen stems only for the exact
   committed configs; any set containing an unusable member gets a `-degraded-adhoc` stem),
   test-pinned.
3. **Alias-source-keyed doc corroborated through the disagreement branch (MEDIUM, latent but
   armed by 3D-FRONT):** a doc whose own vocabulary carries `armchair` suggested 'armchair',
   landed in `disagrees`, and the injected string lowercase-equalled the claim → 0.70 via
   the wrong door; a genuine second-doc disagreement could even be outvoted by doc order.
   Agreement is now "suggestion ∈ {band key, lowercased claim}" — saying the claim's own
   name IS agreement — and the docstring invariant (a disagreement injection can never
   lowercase-equal the claim) is true again and pinned.
4. **`priors=[]` read `WIRED (0 corpus docs)`** → now UNWIRED (a lane that can corroborate
   nothing is not wired). 5. **An unjudgeable `{}` band in one doc vetoed the other corpus's
   real doubt** → no judgeable axis = no voice either way. 6. **CLI flags without values
   crashed with raw tracebacks** → usage exit. 7. **`collect_anomaly` claimed prior_band
   READ off bare truthiness** (a discovered-but-dead artifact) → usable-doc probe + sources
   named. 8. **`n_elements_malformed` = 371,059 actually counted UNLABELLED decor objects**
   (corpus health misstated) → counter split (`n_elements_unlabelled` 371,059 / malformed 0),
   artifact re-derived, FloorPlanCAD byte-compat re-proven after the change.

**The two REFUTED findings earned their keep anyway:** both independently reproduced the
§2 un-flagging arithmetic and were refuted ONLY because the disclosure already existed —
the first draft of this report DID carry the overclaim ("those sizes fall to the built-in
HIGH tier, not into a hole"), I caught it against the real numbers mid-review and rewrote
README + §2 before the panel returned; the refuters then judged the fixed text. Their
refrigerator/sink examples are folded into §2.

Post-fix state: **1393 tests** (+25 over the pre-lane 1368), doubt-score 271 stable, all
three F7 config records byte-stable/regenerated, FPC reproducibility re-verified.

## 5. Repro

```
cd pipeline/scripts
python -m pytest -q                                            # 1385
python kind_priors.py --derive ../../qa/priors/kind-priors-structured3d-first3500.json \
    C:/Users/teza_/studio-datasets/structured3d/gt-corpus-labeled \
    --source structured3d --max-dispersion 3.0
PYTHONIOENCODING=utf-8 python self_audit.py ../../projects/PRJ-2026-002_c001-house   # 271
PYTHONIOENCODING=utf-8 python flag_localization.py ../../projects/PRJ-2026-002_c001-house                 # multi stem
PYTHONIOENCODING=utf-8 python flag_localization.py ../../projects/PRJ-2026-002_c001-house --priors none   # 07-08 stem, byte-stable
PYTHONIOENCODING=utf-8 python flag_localization.py ../../projects/PRJ-2026-002_c001-house \
    --priors ../../qa/priors/kind-priors-floorplancad-train.json                     # 07-13 stem, byte-stable
```

## 6. Roadmap consequence

- The §7 line of the 2026-07-13 report is now ANSWERED by measurement, half-affirmed,
  half-refuted: Structured3D bands corroborate the bed (done) but CANNOT corroborate
  side_table/armchair/bathtub/toilet under the unique-membership rule — real-furniture size
  populations overlap; drawn CAD symbols were the more discriminative prior. Do not re-derive
  this hope; the numbers are in this report.
- The remaining 14 kind doubts now have exactly two honest exits: **owner signature**
  (confirmed_kind) or a **Thai-market prior set** (real SKU dimensions are tighter than
  synthetic-home bboxes and may restore uniqueness — this also aligns with the
  sourceability north star, since an ffe_tag→SKU pipeline would produce per-kind dimension
  populations as a side effect).
- The multi-corpus plumbing is the durable asset: any future prior set (Thai-market,
  3D-FRONT once owner-gated access lands) drops in as one more `*kind-priors*.json` — with
  discovery, corroboration, anomaly, F7, and coverage lines already honest about N docs.
