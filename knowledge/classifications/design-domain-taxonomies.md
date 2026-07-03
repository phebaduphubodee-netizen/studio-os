# อนุกรมวิธานความรู้งานออกแบบภายใน / Industry & Professional Design-Domain Taxonomies

> PROVENANCE: distilled from `knowledge/_inbox/id-project-corpus/Interior Design
> Knowledge Structuring.pdf` (deep-research report, 17 pp., staged in the
> id-project-corpus that informed the STUDIO-OS blueprint), date 2026-07-03,
> tier REFERENCE. Page citations refer to that PDF. DR reports are NOT
> Authority sources — see boxed warning in §4.

## ลำดับอำนาจ / Authority order

กฎหมายชนะเสมอ / Thai law wins: this file carries **no statutory values**.
It provides organizing vocabulary and routing/check taxonomies only. Any
dimensional, clearance, ventilation, or egress requirement comes from
`knowledge/codes-th/` (Authority tier), which outranks everything here.
Nothing in this file may gate a deliverable.

## 1. อนุกรมวิธานสามโดเมนของ NCIDQ / NCIDQ three-domain knowledge taxonomy

NCIDQ (National Council for Interior Design Qualification) divides
professional interior-design knowledge into three operational domains — a
pre-validated schema for organizing a design knowledge base
(Interior Design Knowledge Structuring.pdf p.2). NCIDQ is a **North American
certification**: use its structure, never its jurisdictional content.

| Domain | Core competencies | Algorithmic role (per source) |
|---|---|---|
| **IDFX** (Fundamentals) | design concepts, programming, human factors, history, drawing conventions | generative constraints for initial spatial layouts and stylistic parameters |
| **IDPX** (Professional) | project management, building systems, construction documentation, code requirements | validation engine — cross-references generated layouts against life-safety and structural rules |
| **PRAC** (Practicum) | synthesis of programming, planning, spatial analysis, contract administration | governs multi-agent orchestration, end-to-end from prompt to specification package |

Source example of routing: an egress / fire-resistive-materials request maps
to IDPX (triggers code validation); a programmatic adjacency request maps to
IDFX (Interior Design Knowledge Structuring.pdf p.2).

**STUDIO-OS query-routing mapping / การจัดเส้นทางคำถาม:**

| Question class | NCIDQ analogue | Route to |
|---|---|---|
| Statutory / code / clearance | IDPX | `knowledge/codes-th/` + vault (`vault_search.py`) — never NLM |
| Concept, style, theory, composition | IDFX | `knowledge/styles/` + vault first; NLM lane on vault gaps |
| End-to-end stage synthesis, contracts, handover | PRAC | project stage `_contract.md`s + pipeline skills (intake-parse → concept-brief → qa-report) |

## 2. องค์ประกอบ 7 + หลักการ 6 / Elements-and-principles scaffold (variables vs evaluation functions)

Core scaffold (Interior Design Knowledge Structuring.pdf pp.2–3): the
**7 elements** act as *variables in a generative design equation*; the
**6 principles** act as *evaluation functions* that judge whether the
variables integrate into a cohesive environment.

| 7 elements (generative variables) | 6 principles (evaluation functions) |
|---|---|
| space / ที่ว่าง | unity / เอกภาพ |
| line / เส้น | balance / สมดุล |
| form / รูปทรง | rhythm / จังหวะ |
| light / แสง | emphasis / จุดเน้น |
| color / สี | contrast / ความต่าง |
| texture / พื้นผิว | scale / สัดส่วนขนาด |
| pattern / ลวดลาย | — |

Studio use: vocabulary scaffold for concept-brief authoring (elements =
what the prompt varies) and render scoring (principles = what the evaluator
names when judging a frame).

Quantified heuristics from the same source (p.3):

- **60/30/10 color distribution** — dominant / secondary / accent; the source
  proposes pixel-color analysis of renders to verify the ratio. Canonical
  studio table already lives in `knowledge/styles/color-composition.md` §2 —
  cite that file, not this one, for the rule itself.
- **Odd Rule** — grouping objects in odd numbers creates visual asymmetry,
  moves the eye, generates rhythm; source suggests enforcing odd-numbered
  entity counts in decorative-array schemas
  (Interior Design Knowledge Structuring.pdf p.3). Canonical studio record:
  `knowledge/styles/color-composition.md` §2.1 (distilled from the same PDF
  page) — cite that file, not this one, for the rule.
- **Style ontology as restrictive edges** — a style node (e.g. Minimalist)
  carries restrictive edges (clean lines, neutral colors, unornamented
  surfaces); contradicting specs get flagged via the associative links
  (p.3). Aligns with how `knowledge/styles/` files constrain prompt slots.

## 3. ผังจำแนก CSI / CSI classification crosswalk (MasterFormat · UniFormat · OmniClass)

Organizing vocabulary for BOM / FF&E / specification artifacts
(Interior Design Knowledge Structuring.pdf p.9; Div 06-vs-12 distinction p.5).
Thailand does not procure by CSI — treat as artifact-structuring vocabulary,
not a procurement standard.

| System | Organizational logic | Interiors-relevant slices |
|---|---|---|
| **MasterFormat** | work results (materials + trades), 50 divisions; detailed construction specs | Div 06 Wood/Plastics/Composites · Div 08 Openings · Div 09 Finishes · Div 12 Furnishings |
| **UniFormat** | functional assemblies / physical building systems; early schematic cost models and scope narratives | Category C — Interiors |
| **OmniClass** | 15 hierarchical tables for full facility life cycle + BIM | Table 13 Spaces-by-Function · Table 23 Products |

- **Div 06 vs Div 12 boundary** (p.5): Div 06 = custom, site-specific
  architectural woodwork / millwork / casework (AWI-governed fabrication);
  Div 12 = Furnishings (the "loose / manufactured" gloss is studio
  interpretation — the source names the division without elaborating).
  Useful split for our
  built-in-vs-loose line in FF&E schedules and BOMs.
- **Crosswalk concept** (p.9): as a design matures from schematic to CDs,
  a UniFormat assembly is *unpacked* into its component MasterFormat
  sections so estimating and procurement stay aligned with design intent.
  Studio analogue: Stage 02 concept (assembly-level) → Stage 06+ BOM/spec
  (work-result-level) should keep a traceable mapping per item.
- Suggested artifact tagging: FF&E rows carry a MasterFormat division tag
  (06/08/09/12); room records carry an OmniClass Table-13 function tag.

GAP: corpus contains no Thai classification equivalent (no TIS/Thai
procurement taxonomy); crosswalk depth (numbered section-level mapping) is
not in the corpus — only the concept.

## 4. อนุกรมวิธานประเภทการตรวจระยะ / Spatial-clearance CHECK-TYPE taxonomy (logic only)

> **BOXED WARNING / คำเตือน — NO NUMBERS BY DESIGN**
> All US ADA / NKBA numeric values in the source have been **deliberately
> excluded**. Thai statutory floors live in `knowledge/codes-th/` and are
> enforced by the `clearance_check` engine (suite v0.4.3). This section
> defines *check categories and their algorithmic logic only*. Nothing here
> may gate a deliverable; if a number is needed, it comes from codes-th.

Six check types, each with its geometric test
(Interior Design Knowledge Structuring.pdf pp.4–5, values stripped):

| # | Check type | Algorithmic logic |
|---|---|---|
| 1 | **Circular turning space** / พื้นที่หมุนวงกลม | project a clear vertical cylinder (clear up to a set height) into the room; must not intersect any fixed asset |
| 2 | **T-shaped turning space** / พื้นที่หมุนรูปตัว T | alternative bounding-box geometry (square body + arms) used when the circle fails collision detection due to room constraints |
| 3 | **Passageway clearance** / ทางเดิน | pathfinding (e.g. A* search) must maintain a continuous minimum-width navigation mesh through the whole plan |
| 4 | **Knee / toe clearance** / ระยะเข่า-ปลายเท้า | extrusion parameters under casework / sink elevations guaranteeing the forward-approach volume (toe depth-height + knee height) |
| 5 | **Door-swing interference sweep** / รัศมีบานเปิดประตู | sweep an arc from every hinge point; require zero intersection with fixture clear spaces and stationary-activity zones |
| 6 | **Activity-center clearance** / พื้นที่หน้าจุดใช้งาน | rectangular clear floor space generated at every functional node, strictly centered on the fixture or equipment |

Studio mapping (verified against `pipeline/scripts/clearance_check.py`,
suite v0.4.3): category 3 exists as a coarse walkway-gap proxy (real
path-search deferred to a later phase) and category 5 as a conservative
swing-bbox proxy; the engine's statutory floors (areas, widths, heights)
come from codes-th. Categories 1, 2, 4, 6 (turning spaces, knee/toe,
activity-center) are NOT yet implemented — this taxonomy is the
forward-looking check vocabulary. GAP: no Thai statutory source ingested
for turning-space or approach volumes; do not improvise values — queue a
codes-th PR if a project needs them.

## 5. ช่องว่างข้อมูล / Gaps

- Corpus is US-centric throughout (NCIDQ, CSI, ADA/NKBA, AWI); no Thai
  professional-qualification taxonomy (e.g. TIDA) and no Thai classification
  standard appears anywhere in the corpus.
- Elements/principles scaffold exists here only as REFERENCE — not yet
  distilled into a scoring rubric under `knowledge/styles/`. (The Odd Rule
  IS already distilled: `knowledge/styles/color-composition.md` §2.1.)
- No numbered MasterFormat section-level crosswalk table in the corpus —
  only division-level mapping and the crosswalk concept.
- Turning-space, knee/toe, and activity-center checks: not in suite v0.4.3
  and no Thai statutory floors ingested for them (see §4).
