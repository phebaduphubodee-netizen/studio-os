# กายวิภาคของชุดแบบก่อสร้างที่สมบูรณ์ / Anatomy of a Complete CD Set — the completeness target (REFERENCE)

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §3 ("Anatomy of a complete CD set"). KB built 2026-06-30 from two cross-checked
> Deep-Research runs; tier **REFERENCE — strong-but-unaudited**, NOT Authority.
> This is the *completeness checklist* the phase-4 construction-document set is
> measured against (see `design-process-and-deliverables.md` §1 phase 4).
> It defines structure, not statutory content.

## ลำดับอำนาจ / Authority order + precedence

- This file holds **no statutory values**; any code data that appears *on* a CD
  sheet (cover-sheet code synopsis, egress, fire-rated assemblies) comes from
  `knowledge/codes-th/` (Authority tier).
- **On a real project, the written Specifications volume legally takes
  precedence over the drawings** where the two conflict (see §1). That is a
  documentation-hierarchy rule, recorded here; the values inside still defer to
  `codes-th/`.
- Nothing in this file gates a deliverable by itself — it is the target a QA
  checklist scores completeness against (`pipeline/scripts/qa_checklist.py`,
  `suite_package.py`).

## 1. องค์ประกอบของชุด CD / What a "complete" CD set contains

A complete construction-document set is a **cross-referenced relational whole**,
not a pile of loose drawings:

- **Cover sheet** — project info, drawing index, code data.
- **Construction / floor plans** — dimensioned; partitions, doors, power/data,
  keynotes.
- **RCP (Reflected Ceiling Plan)** — all ceiling elements: fixtures, diffusers,
  sprinklers, smoke detectors, height / material changes, **switching**.
- **Interior elevations** — vertical dims, millwork, outlet / switch placement.
- **Sections** — cuts showing assembly / material layers.
- **Details** — large-scale junctions (counter-to-wall, railing, etc.).
- **Schedules (tables):**
  - **Door schedule** — no., type, size, material, finish, hardware set.
  - **Finish schedule** — floor / base / wall / ceiling per room.
  - **Lighting-fixture schedule** — tag, symbol, mfr, model, lamping, voltage.
- **Specifications** — the written volume, organized by **CSI MasterFormat**;
  *legally takes precedence over the drawings on conflict.*

## 2. กฎเชิงสัมพันธ์ / The relational rule (the key law for an AI generator)

Every element on one sheet must have its partner rows/views, generated **from the
model** so they cannot drift out of sync:

| On the model / plan | Must produce |
|---|---|
| every **door** on a plan | a **Door-schedule** row |
| every **fixture symbol** (RCP) | a **Lighting-schedule** row |
| every **room** | a **Finish-schedule** row |
| every **millwork item** | an **elevation / section** |

> Generate schedules *from the model, never by hand* — hand-kept tables drift.
> This is exactly why `make_all.py` derives the lighting layer once and feeds the
> identical fixture list to the RCP, the schedule, and the IES check (the
> relational rule in code).

## 3. ที่เข้ารหัสไว้แล้ว / What the STUDIO-OS pipeline already encodes

| CD component | Encoded by |
|---|---|
| Floor / construction plan | `pipeline/scripts/plan_2d.py` → `plan_<type>.dxf` (+ PNG) |
| RCP | `pipeline/scripts/rcp.py` (fixtures from `lighting.plan_lighting`) |
| Interior elevations (per wall) | `pipeline/scripts/elevations.py`, `suite_elevations.py` |
| Door / Finish / Lighting schedules | `pipeline/scripts/schedules.py` (from the model) |
| Specifications — **partial (FF&E tags only)** | FF&E `csi` division tags (Div 12 furnishings, 09 finishes, 22 plumbing, 26 electrical) on `ffe-schedule.md`. The full **written CSI MasterFormat specifications volume** — the book that legally outranks the drawings — is NOT generated (see gaps). |
| Assembled sheet-set + QA gate | `pipeline/scripts/suite_package.py`, `qa_checklist.py` (`QA-CHECKLIST.md` sign-off) |

Gaps vs the full target (do-not-invent): **Sections** and large-scale **Details**
are not yet auto-generated; the **written CSI specifications volume** is not
generated (only the FF&E CSI division tags on the schedule exist — not the
book that outranks the drawings); the cover-sheet **code synopsis** is
human-authored from `codes-th/`. A CD set is not "complete" until those are
present — flag, do not silently ship a partial set as complete.

## Cross-refs
- `knowledge/classifications/design-process-and-deliverables.md` — phase 4 that produces this set.
- `pipeline/scripts/{plan_2d,rcp,elevations,schedules,suite_package,qa_checklist}.py` — the code that emits it.
- `knowledge/classifications/design-domain-taxonomies.md` — CSI MasterFormat / documentation vocabulary.
- `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` §3 — source.
