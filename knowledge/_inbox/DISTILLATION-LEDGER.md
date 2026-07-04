# _inbox distillation ledger — 2026-07-03

Produced by the `inbox-distill-corpus` workflow (11 corpus readers + route +
author + verify) plus a whole-`_inbox` audit agent. Honest status of every
staged stash. **Rule reminder: staging is NOT knowledge** — a file in `_inbox/`
is REFERENCE tier; distil it into a promoted dir or consciously drop it, never
let it ride (`scripts/inbox_audit.py`).

## ⚠️ Verification status of THIS run (read before trusting the new files)
The workflow's independent **adversarial-verify phase did not complete** — the
Fable-5 monthly spend limit aborted 10 of 11 verifiers + the ledger writer
mid-run. Consequence:
- `classifications/design-domain-taxonomies.md` — **fully verified** (verdict
  FIXED: the verifier caught a real cross-file contradiction — the file claimed
  the Odd Rule was undistilled when `styles/color-composition.md §2.1` already
  had it — fixed in place; 8/8 citation spot-checks passed; statutory/client/
  tier checks PASS).
- The other 10 authored files carry **author self-verification only** (each
  author re-read its source PDF pages before asserting). They are REFERENCE
  tier and must be re-checked before any value gates a deliverable.
- Post-hoc safety sweep (this session, grep): no Thai statutory value asserted
  as fact, no client identifiers, REFERENCE framing + page citations present in
  all 11. The gap is citation-accuracy spot-checking, not a safety leak.
- **Follow-up owed:** re-run the verify phase on the 10 self-verified files
  (resume `wf_de661c7b-269`, or a fresh `/code-review`-style pass) — watch
  specifically for the same parallel-authoring artifact the one live verifier
  found (stale "not yet distilled" cross-references between the new files).

## 1. id-project-corpus (11 PDFs) — distilled + dropped this run

### Authored (11 files)
| file | source PDFs |
|---|---|
| `classifications/qa-dimensions.md` (new) | Automated Production QA Scoring Systems; Automated Vision QA for Interiors; AI Image Prompt Engineering; AI Interior Design Commercial Workflow |
| `classifications/render-defects.md` (new) | Automated Vision QA for Interiors; Automated Production QA Scoring Systems |
| `classifications/prompt-dimensions.md` (new) | AI Image Prompt Engineering; AI Interior Design Commercial Workflow |
| `classifications/design-domain-taxonomies.md` (new, VERIFIED) | Interior Design Knowledge Structuring |
| `materials/millwork-casework.md` (new) | Interior Design Knowledge Structuring |
| `materials/pbr-material-behavior.md` (new) | Automated Vision QA for Interiors; Automated Production QA Scoring Systems |
| `brand-standards/brand-color-verification.md` (new) | Automated Production QA Scoring Systems |
| `lighting/residential-lighting.md` (append) | Interior Design Knowledge Structuring; QA Scoring; Vision QA |
| `materials/residential-materials.md` (append) | Interior Design Knowledge Structuring |
| `styles/color-composition.md` (append §2.1 Odd Rule) | Interior Design Knowledge Structuring |
| `brand-standards/render-quality.md` (append §4 FOV corroboration) | Automated Vision QA for Interiors |

**The empty `classifications/` dir is now populated** (4 files) — the one
promoted dir the audit repeatedly flagged as the pipeline's biggest knowledge
gap.

### Consciously dropped (with rationale)
- **6 PDFs whole** — AI-orchestration / repo-architecture / Claude-Code meta
  already embodied in `CLAUDE.md`, hooks, stage contracts, skills, LFS scripts:
  *AI Context Engineering Architecture*, *AI Design Knowledge Systems*, *AI
  Design Studio Architecture*, *AI Studio Workflow Automation*, *Claude Code
  Architecture Design*, *Large Scale Project Organization*. Filing their
  AI-systems taxonomies under `classifications/` would pollute a
  design-domain dir.
- **Partial drops** — *AI Image Prompt Engineering* (XML/FLUX/ComfyUI craft →
  mooted by the 2026-07-02 stay-on-Gemini decision; only the "Gemini prefers
  scenario/mood NL" fragment kept as a pointer); *AI Interior Design Commercial
  Workflow* (re-litigates the closed engine decision; licensing thresholds are
  legal values never distilled from a DR); *Automated Production QA Scoring
  Systems* Matrix 1/2 threshold operands (**physically unrecoverable** — the
  numbers are truncated equation images in the export; `qa/thresholds.yaml` is
  PR-only regardless); *Automated Vision QA* fine-tuning/DPO lanes (no training
  lane on the Gemini hybrid); *Interior Design Knowledge Structuring* US ADA/
  NKBA numeric clearances (foreign statutory values — `codes-th` is sole
  Authority; only the check-type NAMES + logic were routed).
- **All bibliography lists** — provenance stays with the staged PDFs.

## 2. interior-ai stash — audit (not touched this run; findings for follow-up)
| file | status | evidence / remaining |
|---|---|---|
| 2026-06-30-blender-pipeline-DR.md | ALREADY-DISTILLED | operationalized in build_room.py / clearance_check.py / pipeline CLAUDE.md / strategy.md |
| 2026-06-30-feasibility-market-DR.md | **NOT-DISTILLED** | business verdict (NO-GO thesis / QUALIFIED-GO wedge; Trimble "SketchUp Connector for Claude"). Home = `docs/strategy.md`, not knowledge/ |
| 2026-06-30-gemini-DR-design-components.md | PARTIALLY | primary feeder for the classifications gap; process/deliverables only cross-checked into KB, still _inbox |
| 2026-06-30-gemini-DR-lighting.md | DISTILLED 2026-07-04 | lumen method + fixture spacing + daylighting promoted (via INTERIOR-DESIGN-KB §6) → `knowledge/lighting/lumen-method-and-fixture-placement.md` |
| 2026-06-30-gemini-DR-rendering.md | DISTILLED 2026-07-04 | PBR value ranges + engine comparison + post-processing promoted (via INTERIOR-DESIGN-KB §8) → `knowledge/rendering/render-defaults.md` |
| 2026-06-30-thai-building-code-DR.md | ALREADY-DISTILLED (superseded) | statutory values now in codes-th from the primary PDF; **stale-path residue**: suite_package.py:110 + PRJ-2026-002 QA-CHECKLIST cite the old research path |
| 2026-06-30-unit-economics-DR-002.md | **NOT-DISTILLED** | pricing/economics findings; home = `docs/strategy.md` |
| 2026-07-01-asset-sourcing-DR.md | ALREADY-DISTILLED | cited in docs/DECISIONS-render-assets.md + LICENSING.md |
| 2026-07-01-photoreal-render-technique-DR.md | PARTIALLY | remaining: per-material Principled BSDF presets + light watt/Kelvin tables |
| 2026-07-01-plan-read-write-tools-DR.md | ALREADY-DISTILLED | cited in dwg_ingest.py / plan_2d.py / suite_plan.py (stale `research/` paths) |
| 2026-07-01-plan-read-write-tools-gemini-DR.md | ALREADY-DISTILLED (audit trail) | raw input to the synthesis DR (which overturned 4 of its license claims); keep as provenance only, never distil directly |
| INTERIOR-DESIGN-KB.md | §6/§8 PROMOTED + PATHS FIXED 2026-07-04 | stale-path RESOLVED — the 3 code sites (build_room.py:27, lighting.py:5, dimensional_rules.v0.1.json:89) now cite the promoted knowledge/ files, not the dead `docs/` path. §6 (IES table + lumen method + fixture placement + daylighting) → `knowledge/lighting/lumen-method-and-fixture-placement.md`; §8 (PBR/IOR + render lighting + camera + realism + engines + post) → `knowledge/rendering/render-defaults.md`. STILL unpromoted: §2–3 professional process + CD-set anatomy (targets `classifications/`) |

## 3. nlm-design-systems stash — audit (essentially fully distilled)
Five of six content files have named promoted successors with provenance
blocks: `color-composition.md`, `ergonomics.md`, `lighting.md`, `materials.md`,
`render-photoreal-rules.md` → the matching `knowledge/{styles,ergonomics,
lighting,materials,brand-standards}/` files (notebook a5a43395/79476082 turns
cited). `sources-manifest.md` is the citation anchor — stays in _inbox by
design. **Remaining: `process.md`** (design-phase %-effort SD/DD/CD, CD-set
anatomy, sign-off milestones) — targets the `classifications/` gap; partly
covered now by `design-domain-taxonomies.md`, but the phase-effort split is not
yet promoted.

## 4. Highest-leverage follow-ups (surfaced by the audit — NOT done this run)
1. **Re-run the adversarial verify** on the 10 self-verified corpus files (see
   §warning).
2. **Repoint stale in-script citation paths** — ✅ **DONE 2026-07-04.**
   The `docs/INTERIOR-DESIGN-KB.md` citers (build_room.py:27, lighting.py:5,
   dimensional_rules.v0.1.json:89) now point at the promoted `knowledge/` files;
   the `research/...` DR citers (dwg_ingest.py, plan_2d.py, suite_plan.py →
   `knowledge/_inbox/interior-ai/2026-07-01-plan-read-write-tools-DR.md`, and
   suite_package.py:110 → `knowledge/codes-th/mr55-residential-dimensions.md`,
   the Authority that supersedes the thai-building-code DR) all resolve. Grep
   confirms zero dead `docs/INTERIOR-DESIGN-KB.md` or `research/2026-*` paths in
   pipeline source. Doc-links only (not imports) → low severity, now consistent.
3. **File the 2 business DRs** (feasibility-market, unit-economics) into
   `docs/strategy.md` — they have zero distillation trace and do not belong in
   `knowledge/`.
4. **Promote the remaining domain values** the audit isolated: ✅ **lumen method
   + fixture spacing → `lighting/lumen-method-and-fixture-placement.md` DONE
   2026-07-04** (+ §8 render defaults → `rendering/render-defaults.md`).
   **Remaining:** per-material BSDF presets + watt/Kelvin tables (from
   `2026-07-01-photoreal-render-technique-DR.md`) → `materials/`; `process.md`
   phase-effort → `classifications/`.

## 5. nlm-programming (2026-07-04) — DISTILLED this session
New stash from the persona-driven-design-layer work (this session, 2026-07-04):
| file | status | note |
|---|---|---|
| `nlm-programming-2026-07-04.md` + `-qa-history.json` | **DISTILLED** | NLM DR notebook `053ff5e6` (241 sources), single-shot turn 1 (no `--iterate` drift). Promoted successor: `knowledge/programming/architectural-programming-and-activity-taxonomy.md` (new `programming/` dir). |
| `nlm-persona-poe-2026-07-04.md` + `-qa-history.json` | **DISTILLED** | NLM DR notebook `e0eab101` (247 sources), single-shot turn 1. Promoted successor: `knowledge/programming/persona-ucd-two-way-coverage-and-poe.md`. Independently names the "Two-Way Coverage Check" + "Gaps"/"Orphans" — validates the built layer as established method. |

- **Consumed by:** `pipeline/scripts/activity_taxonomy.py` (`ACTIVITIES` 12-activity set +
  `KIND_ACTIVITY`) and `persona.py` (the persona-coverage layer). REFERENCE tier — the layer
  it feeds is ADVISORY (verdict REVIEW, never gates a deliverable), so REFERENCE grounding is
  sufficient by doctrine.
- **Marker note:** `[n]` unresolved (CLI exposes no answer→title map); provenance carried at
  the AUTHORITY level (NCIDQ/IDFX, Karlen & Fleming, Peña & Parshall, Neufert, NKBA, Space
  Syntax — all named in the answer).
- **Pending:** DR#2 (persona methods + POE, notebook fired 2026-07-04) → will stage as
  `nlm-persona-poe-2026-07-04.md`, strengthening the gap/orphan grounding.
