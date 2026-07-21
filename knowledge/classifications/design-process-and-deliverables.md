# กระบวนการออกแบบภายในระดับวิชาชีพ — 6 เฟส + ส่งมอบ / The Professional Interior-Design Process — 6 phases + deliverables (REFERENCE)

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §2 ("The professional process — 6 phases + deliverables"). That KB was built
> 2026-06-30 by cross-checking two independent Deep-Research runs; tier
> **REFERENCE — strong-but-unaudited**, NOT Authority. This file gives the
> canonical phase/deliverable vocabulary the pipeline organizes work against; it
> carries no statutory values and cannot gate a deliverable.
> Companion: `knowledge/classifications/cd-set-anatomy.md` (§3 — what the phase-4
> CD set must contain).
>
> PROVENANCE (§§3–8, appended 2026-07-13):
> - `knowledge/_inbox/nlm-design-systems/process.md` — NotebookLM answer (notebook
>   a5a43395, 118 sources), asked 2026-07-02. **REFERENCE tier**, secondary summary.
>   Source of §3 (effort split), §4 (sign-off gates), and the phase-4 dual-set rule.
> - `knowledge/_inbox/interior-ai/2026-06-30-gemini-DR-design-components.md` — Gemini
>   Deep-Research run, 2026-06-30. **REFERENCE tier**, single-model. Source of §5
>   (room-record schema), §6 (pipeline checks), §7 (canonical-sources bibliography).
>
> Both appended sources are **entirely North-American convention**, but by
> different framings: `process.md` is framed NCIDQ / Piotrowski (`process.md:1`);
> the DR's code frame is IBC / ADA (`DR:64`, `DR:133`). Neither asserts a Thai
> statutory value and neither may be used to supply one — §8 records what was
> dropped for that reason.

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

## 3. สัดส่วนแรงงานต่อเฟส / Effort split per phase (REFERENCE)

From `knowledge/_inbox/nlm-design-systems/process.md:12-51`. That source frames the
work as **five primary phases, "typically preceded by an essential
Pre-Design/Programming stage"** (`process.md:13-14`) — so Programming carries **no
percentage** there, and the five quoted shares sum to 100%. The tildes are the
source's own; treat these as indicative planning ratios, not a billing rule.

| Phase (this file §1) | Share of effort | Source line |
|---|---|---|
| 1 Programming / Pre-Design | *(un-percentaged in the source)* | `process.md:16-21` |
| 2 Schematic design (SD) | **~15%** | `process.md:22` |
| 3 Design development (DD) | **~20%** | `process.md:28` |
| 4 Construction documents (CD) | **~40%** — "the most extensive phase" | `process.md:34` |
| 5 Bidding | **~5%** | `process.md:41` |
| 6 Construction administration (CA) | **~20%** | `process.md:46` |

Deliverables this source names that §1 above does not (same REFERENCE tier):

- **Pre-Design / Programming** — site analysis; existing-condition **"as-built"
  models**; bubble diagrams; a summarized list of required spaces (the **building
  program**); a preliminary project budget. (`process.md:19-21`)
- **SD** — a **rough-order-of-magnitude (ROM) preliminary cost estimate**, to check
  the project still aligns with the budget. (`process.md:25-27`)
- **DD** — **daylighting / solar studies *(if applicable)*** alongside the final
  material/finish/fixture/appliance selections. (`process.md:31-33`)
- **CD — the dual set.** "Typically, two sets are produced: a **'Permit set'** for
  the local jurisdiction and an **'Issue for Construction'** set for the
  contractors." (`process.md:38-40`) *US instrument. The source is North-American
  throughout and says nothing about Thai submission practice (แบบยื่นขออนุญาต vs
  แบบก่อสร้าง) — do not adopt the two-set split as studio standard without checking
  it against Thai practice.*
- **Bidding** — clarifications to the CDs, responses to contractor questions, and
  the final contractor proposal / construction agreement. (`process.md:43-45`)
- **CA** — approved contractor **submittals** (shop drawings, product data,
  samples), **RFI** responses, **change orders**, and **periodic site-observation
  reports**. (`process.md:49-51`)

## 4. ประตูอนุมัติ 4 จุด / The four client sign-off gates

`process.md:88-105`. The source's own stated rationale: formal client sign-offs
exist "to prevent wasted effort, costly redesigns, and scope creep"
(`process.md:89-90`).

| # | Gate | What the client signs |
|---|---|---|
| 1 | **End of Programming** | the summarized program, budget expectations, defined scope of work — **before any actual design drafting begins** (`process.md:92-94`) |
| 2 | **End of Schematic Design** | the selected floor-plan layout + overall design concept (`process.md:95-97`) |
| 3 | **End of Design Development** | final selection of materials, finishes, fixtures + the finalized layout — **before the heavy CD hours are invested** (`process.md:98-101`) |
| 4 | **Project Closeout** | after the final walk-through: the client agrees the **punch list**; once those items are done, the client signs the **Certificate of Substantial Completion**, "officially concluding the project" (`process.md:102-105`) |

> The source attaches its wasted-effort / cost rationale to the **whole gate list**
> (`process.md:89-90`), not to any one gate — Gate 1 carries an effort argument of
> its own ("before any actual design drafting begins", `process.md:92-94`). What
> the source says of Gate 3 is that it precedes "the heavy hours required to draft
> the technical Construction Documents" (`process.md:100`) — *heavy hours*, with no
> percentage attached.
>
> **STUDIO INFERENCE** (ours, not the source's): joining `process.md:100` with the
> ~40% CD effort share at `process.md:34` (§3) makes DD approval the last cheap
> place to change one's mind. The source states those two facts in separate
> sections and never links them.
>
> Gate 4's **Certificate of Substantial Completion** is a North-American closeout
> instrument; recorded as vocabulary, not as a Thai contractual requirement.

STUDIO-OS note: these are *client* gates, distinct from the repo's *machine* gates
(a stage's `_contract.md` gate). A stage may pass its contract gate and still be
awaiting the client sign-off above.

## 5. โครงสร้างข้อมูลห้อง / The Programming room-record schema

From `2026-06-30-gemini-DR-design-components.md:131-143` ("Input Data Model (Based
on Programming)"). REFERENCE tier — this is a **data model** and it carries no
statutory content.

**STUDIO-OS integration decision** (ours, not the DR's — the DR describes a generic
pipeline and names no repo artifact): this is the shape a `brief.json` room record
should converge on.

Project level (`DR:132-133`):

| Field | Contents |
|---|---|
| `Project Info` | client, address, project type, scope |
| `Code Data` | the DR says "applicable IBC version, local amendments, ADA requirements". **In Thailand this field is filled ONLY from `knowledge/codes-th/`** — see §8. |

Per room (`DR:134-143`):

| Field | Type / example (DR's own examples) |
|---|---|
| `Room_Name` | e.g. "Primary Bedroom" |
| `Room_ID` | e.g. "101" |
| `Required_SF/M2` | net area (DR example is imperial, "250 sq. ft."; **record m² in this repo**) |
| `Adjacency_Requirements` | list of `Room_ID`s, each with a `Proximity` flag ∈ **{Immediate, Near, Separate}** |
| `Functional_Requirements` | text or tags, e.g. "Sleep", "Reading", "Dressing" |
| `Key_Furniture_Items` | list, e.g. "King Bed", "2x Nightstand", "Dresser" |
| `Lighting_Requirements` | task (e.g. "Reading") / ambient / accent + a lux target. **The DR's flat `IES_Lux_Target: 500 lux` is NOT promoted** — take the value from the banded per-room/per-task table in `knowledge/lighting/lumen-method-and-fixture-placement.md` §6.2 (§8 below). |
| `Acoustic_Requirements` | **STC** rating for partitions |
| `Power_Data_Reqs` | number of outlets, data-port locations |

The three-level `Proximity` flag {Immediate, Near, Separate} is the machine-readable
form of the **adjacency matrix** already named in §1 phase 1.

## 6. เช็คอัตโนมัติของสายงานร่างแบบ / Checks + annotation the DR asks of an AI drafting pipeline

`DR:157-169`. The DR's framing: the generator "isn't just 'drawing pictures' but is
building a **relational database** of the project" (`DR:155`). Completeness checks
it lists (`DR:157-162`) include, beyond the per-element schedule pairings:

- **"Are all plans dimensioned?" — check for DANGLING DIMENSION STRINGS.** (`DR:162`)
- Are all custom millwork elements detailed in an elevation and/or section view? (`DR:161`)

Automated annotation (`DR:163-165`):

- **Keynote bubbles** generated automatically and **linked to a keynote database**.
- **Door, window and room tags placed automatically**, pulling data from the
  underlying project model.

Schedule generation (`DR:166-167`): query the internal project database to emit all
schedules (Finish, Lighting, Door) — so drawings and schedules "are never out of
sync".

**Specifications link — the numbered-section crosswalk** (`DR:168-169`): a material
tag on a drawing must link to its CSI MasterFormat spec section. The DR's worked
example, and the only numbered section it gives:

| Drawing tag | CSI MasterFormat section |
|---|---|
| `PT-1` (paint tag on a wall in an elevation) | **09 91 00 — Painting** |

Do not extrapolate further section numbers from this one example; the DR supplies
no others.

## 7. ตำราอ้างอิงหลัก / Canonical sources — what each is the authority FOR

`DR:94-102`. Verbatim scope claims, condensed. REFERENCE tier: this is the DR's
opinion of each book's authority, not the studio's audit of it. None of these
outranks `knowledge/codes-th/` inside Thailand.

The DR uses the "THE authority" construction for only **five of the seven**; for
Nielson & Taylor and for Gordon its prose is deliberately softer, and this table
keeps that distinction.

| Author — Title | What the DR says it covers |
|---|---|
| **Francis D.K. Ching**, *Interior Design Illustrated* | "**THE authority for graphic standards**" — how to draw and *read* plans, elevations, sections, details. The "visual dictionary" for design documentation. (`DR:96`) |
| **Mark Karlen & Christina Fleming**, *Space Planning Basics* | "**THE authority for the programming and schematic design process**" — step-by-step method from client needs to a functional floor plan. (`DR:97`) |
| **Julius Panero & Martin Zelnik**, *Human Dimension & Interior Space* | "**THE authority for anthropometrics and ergonomics**" — human body sizes and spatial requirements; the basis for dimensioning clearances, circulation paths and workstations. (`DR:98`) |
| **Karla J. Nielson & David A. Taylor**, *Interiors: An Introduction* | *Not claimed as an authority by the DR.* "A comprehensive **textbook-grade overview of the entire profession**" — principles/elements, materials, FF&E, professional practice. (`DR:99`) |
| **Binggeli**, *Materials for Interior Environments* | "**THE authority for the technical specifications of materials**" — performance characteristics, sustainability, installation methods. (`DR:100`) *(the DR gives the given name as "Cindy"; verify the author's name before ordering.)* |
| **IES**, *The IES Lighting Handbook* (most recent edition) | Illuminance data (lux / footcandles) per space and task, plus qualitative practice. The DR calls it "THE definitive **legal** and professional standard" — **that word does not transfer to Thailand**: here IES is REFERENCE, and statutory floors come from `codes-th/`. (`DR:101`) |
| **Gary Gordon**, *Interior Lighting for Designers* | *Not claimed as an authority by the DR.* "A more **accessible, design-focused guide to lighting**" that translates the IES Handbook's engineering principles into practice — "how to achieve lighting effects". (`DR:102`) |

Phase attribution the DR makes, per its "Authoritative Source" lines: **Karlen &
Fleming govern phases 1–2** (`DR:19, 36`); **Panero & Zelnik govern phase 1**
(`DR:19`) — the DR's phase-2 line names only Ching and Karlen & Fleming, so the
anthropometric text is *not* extended to schematic design here; **Nielson & Taylor,
Binggeli, IES + Gordon govern phase 3** (`DR:49`); **Ching governs phases 2 and 4**
— the drawing conventions (`DR:36, 64`).

## 8. ที่จงใจไม่รับเข้ามา / Deliberately NOT promoted — drop rationale

Recorded so a future audit sees these were *considered and refused*, not missed.

| Dropped from the DR | Why |
|---|---|
| `MIN_CLEARANCE_HALLWAY = 36 in` (914 mm), **44 in commercial** (1118 mm); `MIN_CLEARANCE_DOORWAY = 32 in` (813 mm) — offered as "non-violable constraints" (`DR:147`) | US/ADA values from a **REFERENCE-tier DR**. A DR may never supply a statutory value. Thai corridor minima are Authority: `knowledge/codes-th/mr55-residential-dimensions.md` (ข้อ 21) — **1.00 m** inside a dwelling, **1.50 m** for อาคารอยู่อาศัยรวม / สำนักงาน / อาคารสาธารณะ. **Both DR hallway figures fall below the corresponding Thai floor** (914 < 1000; 1118 < 1500), so promoting them would have been actively unsafe. The 32 in doorway figure is a foreign (ADA) accessibility reference only — not applicable-in-Thailand. |
| `IES_Lux_Target = 500 lux at task plane` (`DR:141`) | A single flat constant. Superseded by the **banded per-room / per-task table** in `knowledge/lighting/lumen-method-and-fixture-placement.md` §6.2 (e.g. bedroom bedside reading 30–50 fc ≈ 323–538 lux). The schema **field** survives (§5); the DR's value does not. |
| `Code Data`: "applicable IBC version, local amendments, ADA requirements" (`DR:133`) | Keep the field, drop the content. In Thailand it is filled from `knowledge/codes-th/` only. IBC/ADA are foreign reference. |

## Cross-refs
- `knowledge/classifications/cd-set-anatomy.md` — the phase-4 completeness target (KB §3 companion).
- `knowledge/classifications/design-domain-taxonomies.md` — NCIDQ IDFX/IDPX/PRAC routing (which phase a request belongs to); CSI MasterFormat vocabulary behind §6.
- `knowledge/lighting/lumen-method-and-fixture-placement.md` §6.2 — the lux table that replaces the DR's 500-lux constant (§8).
- `knowledge/codes-th/mr55-residential-dimensions.md` ข้อ 21 — Authority for corridor widths (§8).
- `projects/CLAUDE.md`, per-stage `_contract.md` — how these phases are enforced as the stage-gate protocol.
- `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` §2 — source of §§1–2.
- `knowledge/_inbox/nlm-design-systems/process.md` — source of §§3–4.
- `knowledge/_inbox/interior-ai/2026-06-30-gemini-DR-design-components.md` — source of §§5–8.
