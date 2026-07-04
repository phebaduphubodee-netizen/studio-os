# กระบวนการออกแบบภายในระดับวิชาชีพ — 6 เฟส + ส่งมอบ / The Professional Interior-Design Process — 6 phases + deliverables (REFERENCE)

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §2 ("The professional process — 6 phases + deliverables"). That KB was built
> 2026-06-30 by cross-checking two independent Deep-Research runs; tier
> **REFERENCE — strong-but-unaudited**, NOT Authority. This file gives the
> canonical phase/deliverable vocabulary the pipeline organizes work against; it
> carries no statutory values and cannot gate a deliverable.
> Companion: `knowledge/classifications/cd-set-anatomy.md` (§3 — what the phase-4
> CD set must contain).

## ลำดับอำนาจ / Authority order

Thai law wins: this file holds **no statutory values**. Any dimensional, egress,
ventilation, or clearance requirement referenced inside a phase comes from
`knowledge/codes-th/` (Authority tier), which outranks everything here. This is
organizing vocabulary — a map of *what work happens when and what it produces* —
not a rulebook. Nothing here may gate a deliverable.

## 1. เฟส / The six phases + their deliverables

Standard professional workflow (North-American RIBA/AIA-analogue phasing; use the
structure, take statutory content from `codes-th/`).

1. **Programming / brief** *(analytical, not creative)* — interviews, site
   survey, FF&E inventory, budget, **code review** (against `codes-th/`; the
   KB's US analogue is IBC/ADA). Karlen's **8-step method**:
   interview → observe → set architectural parameters → organize → research
   unknowns → analyze affinities → diagram (bubble/block) → summarize into the
   **Program**.
   *Deliverables:* written Program, goals, user profiles, spatial + **adjacency
   matrix**, functional/technical requirements, code synopsis.
2. **Schematic design** — translate program → big-idea layout.
   *Deliverables:* bubble/adjacency diagrams, **schematic (single-line) floor
   plans**, concept sketches, **mood/concept boards**.
3. **Design development (DD)** — resolve everything to specifics.
   *Deliverables:* developed dimensioned plans, **Reflected Ceiling Plan (RCP)**,
   key elevations, character renderings, **Material & Finish schedule**, FF&E
   selections + preliminary budget.
4. **Construction documentation (CDs)** — the legally-binding build instructions.
   The completeness target for this set is `cd-set-anatomy.md` (§3).
5. **Bidding / tendering** — addenda, RFIs, bid analysis, contract.
6. **Contract administration** — site visits, submittal / shop-drawing review,
   RFIs, **punch list**, closeout.

## 2. เส้นแบ่งมนุษย์ ↔ ระบบ / Where the STUDIO-OS wedge sits

> The sellable wedge lives in **phases 3–4 (DD + CDs)** — the dimensioned,
> scheduled, spec'd output. Phases 1–2 (programming + the "big idea") stay human.

| Phase | Owner | STUDIO-OS mapping |
|---|---|---|
| 1 Programming | human | Stage 00 intake (`intake-parse` → `brief.json`), client profile |
| 2 Schematic | human (+ concept skill) | Stage 02 (`concept-brief`): zoning / style direction / mood |
| **3 Design development** | **pipeline** | Stage 03 layout (scene-graph + FF&E), dimensioned plans, RCP, DD renders, Material & Finish + FF&E schedules |
| **4 Construction documents** | **pipeline** | Stage 04 CD-set (`plan_2d`, `rcp`, `elevations`, `schedules`, `suite_package`) → `cd-set-anatomy.md` |
| 5 Bidding | human | Stage 07 BOM (`bom-generate`, **planned skill**), tender support |
| 6 Contract admin | human | Stage 08 handover, punch list |

The FF&E research lane (`ffe-research` skill) feeds phase-3 selections; the
client-facing BOM (`bom-generate`, a planned Stage-07 skill — not yet built) is a
phase-5 artifact, kept separate from the back-office FF&E candidates by design.

## Cross-refs
- `knowledge/classifications/cd-set-anatomy.md` — the phase-4 completeness target (KB §3 companion).
- `knowledge/classifications/design-domain-taxonomies.md` — NCIDQ IDFX/IDPX/PRAC routing (which phase a request belongs to).
- `projects/CLAUDE.md`, per-stage `_contract.md` — how these phases are enforced as the stage-gate protocol.
- `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` §2 — source.
