# kind-priors wiring — the corpus prior-band tier goes from UNWIRED to READ (2026-07-13)

**One sentence:** the FloorPlanCAD kind-priors artifact (derived 2026-07-07, never landed) now
lives at `qa/priors/kind-priors-floorplancad-train.json` and is wired into all three
doubt-instrument consumers — anomaly's corpus size/aspect band, confidence's `prior_kind`
corroboration, and a new F7 mutation class that MEASURES the band's added catching power —
with a probe-derived vocabulary policy that keeps the flagship no-false-positive guarantee.

## 1. The wound

`self_audit` on PRJ-2026-002 v4 reported `prior_band: UNWIRED (no corpus priors)` and 16 of its
18 MEDIUM doubts read *"hand-typed identity, no owner sign + no prior-band corroboration"*. The
wiring for a corpus tier existed on every consumer (`anomaly_flags.check_room(priors=)`,
`confidence` context `prior_kind`, `self_audit._load_priors` globbing `qa/**`) — but the artifact
itself had never been landed, so the machine could not corroborate ANY kind read without an owner
signature, and its size doubts ran on the deliberately-generous built-in bounds only.

The artifact existed all along at
`C:/Users/teza_/studio-datasets/floorplancad/priors/` (17,973 elements, 3,525 mm-calibrated
train sheets, 19 kinds). Reproducibility re-verified before landing: a fresh
`kind_priors.py --derive` over the same on-disk `gt-train-00 + gt-train-01` gives **0 field
mismatches** against the 2026-07-07 file.

## 2. The probe BEFORE wiring (why a vocabulary policy exists)

Bands were run against the KNOWN-CORRECT v4 reads (both rooms verified against the sheet) before
any code changed. Result:

- **5 false MEDIUM flags — every one a built-in `cabinet`** (โต๊ะทำงาน built-in BF11 600×3200,
  ตู้/ชั้น BF10 2500×600, ชั้นวางทีวี BF13 300×4100): repo `cabinet` includes custom millwork
  runs; the corpus `cabinet` class is freestanding symbols ≤ ~1.3 m. Same population error
  `BUILTIN_BOUNDS` already dodged by omitting cabinet/headboard.
- **Zero false flags on every other kind.** The Thai 7'×6.5' bed (2134×1981) sits just outside
  the corpus bed band but inside the `PRIOR_FAR` 40 % margin — the margin is doing its job.
- Strict unique-membership corroboration hits **2/30 pieces** (sofa 2202×1008, wardrobe run
  2500×600). Membership-based corroboration was CONSIDERED AND REFUSED: a toilet 400×700
  mutated to kind `sink` still fits the sink band, so membership would corroborate a WRONG kind
  — the strict rule keeps the instrument conservative.

Policy (frozen by `test_vocabulary_policy_frozen`; changing it is a re-probe, not a tweak):

- `PRIOR_EXEMPT_KINDS = {cabinet, headboard}` — skipped and DISCLOSED in coverage, never a
  silent pass. Also preserves F7's `_NO_BOUND_TARGETS` invariant (kind-change mutations re-kind
  into these so that probe stays single-collector).
- `PRIOR_KIND_ALIASES = {armchair: chair}` — corpus class is a true superset population.
  **`tv_console → tv_cabinet` REFUSED**: the corpus tv_cabinet band is a thin wall-strip symbol
  (short 27–450 mm, aspect 2.98–17.1); a real deep TV console would false-flag on aspect.
- Exempt kinds are also never CORROBORATED (`build_prior_context` injects nothing for them) —
  corroborating repo `cabinet` off the freestanding band is the same population error as
  false-flagging it.

## 3. What changed

- `qa/priors/kind-priors-floorplancad-train.json` + `README.md` — the artifact, auto-discovered
  by `self_audit._load_priors` (filename must contain `kind-priors`; schema-checked).
- `anomaly_flags.py` — `prior_band_kind()` vocabulary gate on the size/aspect prior lanes;
  alias disclosed inside the record text; coverage note lists exemptions/aliases.
- `kind_priors.py` — `build_prior_context(pieces, priors)`: the injector that feeds confidence's
  documented-but-never-fed `prior_kind` corroboration (agreement judged through the alias map;
  claimed string injected on agreement so the equality check reads corroboration; disagreeing
  suggestions injected raw — visible, never a downgrade; ambiguity injects nothing).
- `self_audit.py` — `collect_confidence(..., priors=None)` builds the context per spec
  (degrades to context-less WITH a coverage note on failure); coverage gains
  `prior_corroboration: WIRED/UNWIRED`.
- `flag_localization.py` — `priors` threaded through the collectors exactly as self_audit wires
  them (F7 measures the live-suite configuration); new should-flag class
  **`size_off_prior_band`**: re-dimension a piece FAR outside its corpus band (band-hi × 1.4 ×
  1.1) while INSIDE every built-in bound, short side kept inside the band so exactly one axis
  carries the planted error. No window (built-in already at the corpus far-edge — bed, toilet,
  bathtub, wardrobe) → skip, counted. `--priors auto|none|PATH` (default auto = self_audit's
  discovery); priors-none keeps the frozen `flag-localization-2026-07-08` stem, priors-wired
  writes `flag-localization-priors-2026-07-13` so the baseline record is never silently
  overwritten.

## 4. Measurements (all deterministic, re-runnable)

| instrument | before | after (priors wired) |
|---|---|---|
| self_audit PRJ-2026-002 doubt-score | 291 (30 open) | **281 (29 open)** — the sofa kind say-unsure corroborated away (0.30→0.70); nothing else moved |
| self_audit anomaly false flags on v4 | 0 (band unwired) | **0 (band READ)** — exemption holds live |
| self_audit coverage | `prior_band=UNWIRED`, no corroboration lane | `prior_band=READ`, `prior_corroboration=WIRED` |
| F7 `--priors none` | recall 1.0 · prec 0.949 · overfire 0 (6 lanes) | identical numbers; new class honestly `unwired` (0 mut / 26 skip) |
| F7 `--priors auto` | n/a | **7/7 lanes · macro-recall 1.0 · size_off_prior_band 4/4 recall, precision 1.0, severity-match 1.0 · overfire 0** |
| pytest (pipeline/scripts) | 1344 | **1368** (+24 pins) |

The 4 `size_off_prior_band` mutations are the sofa + 3 armchairs — the only v4 pieces with a
"corpus catches / built-in silent" window (computed, not assumed: bed's corpus far-edge 3023 mm
exceeds its built-in max 3000, so no window exists; same for toilet/bathtub/wardrobe). Without
priors these 4 planted errors are INVISIBLE to the whole suite — that is the band's measured
added value, and the class reports `unwired` (never a silent pass) when the artifact is absent.

## 5. Honesty / limits

- **Pooled precision 0.949 → 0.952 is mechanical**: a new 4-mutation perfect-precision class
  raises the pooled ratio; no pre-existing lane improved. Do not quote the delta as a
  detection improvement. (`kind_change_unsigned` 0.929→0.931 is likewise a pooling artifact of
  prior-context records under mutated kinds.)
- Corroboration yield is intentionally TINY (strict unique membership): 1 live doubt removed
  on v4. The instrument got *calibrated*, not lenient — 15 kind doubts correctly REMAIN open
  (corpus has no side_table/bench/console/vanity/shower classes; the Thai king bed sits outside
  the Chinese-corpus bed band, honestly uncorroborated).
- Bands are REFERENCE-tier drawn-symbol statistics from a Chinese CAD corpus (FloorPlanCAD,
  CC BY-NC — artifact holds derived aggregate quantiles only, no corpus files). They may only
  raise doubt or corroborate at 0.70 (below owner 1.0); they never gate a deliverable and never
  re-label a piece. `knowledge/codes-th/` outranks.
- The committed `flag-localization-2026-07-08` report was regenerated by the priors-none run:
  every measured number is byte-identical; the diff only ADDS the new class row (`unwired`) and
  the `prior_band` coverage entry. Historical bytes remain in git history.
- `curve` signatures in the artifact are currently unused by these consumers (project pieces
  carry no `curve` flag); they ride along for the reader lane.

## 5b. Pre-commit adversarial review (47-agent workflow, 5 lenses, 2-skeptic refutation per finding)

21 findings raised → 11 survived refutation → **5 real defects, all fixed + pinned before this
commit** (the other 6 survivors were independent verification records — every measured claim
above reproduced live — plus one procedural note):

1. **Case-sensitivity exempt bypass (MEDIUM, the flattering direction):** `build_prior_context`
   decided exemption/agreement case-sensitively while `confidence` compares LOWERCASED — a
   hand-typed `'Cabinet'` slipped past the exemption as a "disagreement" injection and still
   read as corroborated 0.70 downstream. Decisions now made on the lowercased claim
   (`test_context_exemption_is_case_insensitive_like_confidence`).
2. **Hostile band edges crashed the whole F7 run (MEDIUM):** the generator runs outside the
   guarded collectors; string/None band values now SKIP the item
   (`test_hostile_band_edges_skip_the_item_never_crash_the_run`).
3. **F7 coverage claimed prior_band READ off `priors is not None` (MEDIUM):** a garbage doc
   read as READ while every mutation skipped. READ now requires the usable-artifact shape
   (`test_garbage_priors_doc_reports_prior_band_unwired_not_read`).
4. **`prior_corroboration=WIRED` over a dead context lane (LOW):** context failing on every
   spec now reports ERROR, never WIRED
   (`test_collect_confidence_dead_context_lane_reports_error_not_wired`).
5. **Fake MISS on base-builtin-violating pieces (LOW):** the mutation's MEDIUM record shares a
   `_flag_key` with a pre-existing base HIGH record (severity excluded from the key), scoring a
   harness artifact as a suite blind spot; such pieces now skip
   (`test_base_builtin_violation_skips_instead_of_faking_a_miss`).
   `--priors PATH` also now schema-checks via `kind_priors.load` (fails loudly).

Notable REFUTED findings (kept for the record): duplicate piece names corrupting the context
(names are unique in practice + last-wins is documented); the 0.929→0.931 / 0.949→0.952 deltas
hiding a regression (traced to +1/+1 pooling, disclosed in §5); ambient-false-flag blindness in
F7's delta methodology (v4 base anomaly flags = 0, verified live).

## 6. Repro

```
cd pipeline/scripts
python3 -m pytest test_anomaly_flags.py test_kind_priors.py test_self_audit.py \
    test_flag_localization.py test_confidence.py -q          # 142
python3 -m pytest -q                                          # 1368
PYTHONIOENCODING=utf-8 python3 self_audit.py ../../projects/PRJ-2026-002_c001-house
PYTHONIOENCODING=utf-8 python3 flag_localization.py ../../projects/PRJ-2026-002_c001-house              # priors auto
PYTHONIOENCODING=utf-8 python3 flag_localization.py ../../projects/PRJ-2026-002_c001-house --priors none # frozen baseline
```

## 7. Roadmap consequence

- The tier-1 suite's last always-UNWIRED machine lane is now READ; remaining UNWIRED coverage
  on PRJ-2026-002 is sourceability (needs `ffe_tag` population) and persona (needs
  persona.json) — both owner-gated inputs, not missing machine wiring.
- The corroboration tier is extensible by LANDING BETTER BANDS, not by loosening the rule:
  a Thai-market prior set (or Structured3D real-furniture bands once labelled) would corroborate
  the bed/side-table reads this corpus honestly cannot.
