# 00_intake inventory — PRJ-2026-002 (c001-house) · Client C-001 · parsed 2026-07-02

Sources migrated from the pre-studio exploration workspace (INTERIOR-AI), received
originally from the partner designer (P-001). Raw files contain identifying data
(owner name, designer firm + address, development name, CAD job number) and live in
`00_intake/raw-local/` which is **gitignored** (root .gitignore) — referenced below by
document ID + SHA-256 prefix instead of filename. Anonymized derivatives only in git.

## Documents received
| ID | SHA-256 | Type | Parsed into |
|---|---|---|---|
| DOC-01 | 29feb43a | Furniture plan PDF, 2 pages (floor 1 + floor 2), scale 1:75, vector | brief.json rooms/areas (via DOC-05/06/07) |
| DOC-02 | 5edcd8a8 | CAD DWG (AutoCAD 2018+, Thai codepage) | via DOC-03 |
| DOC-03 | 09f3665f | DXF conversion of DOC-02, 20.8 MB — 2D both floors (despite "3D" in job filename; zero 3D solids) | brief.json fixed_constraints, windows_status, built-in codes |
| DOC-04 | c687df00 | PNG crop render of DOC-02 (floor-2 plan area) | corroboration only |
| DOC-05 | c51fff19 | Raster of DOC-01 p.0 (floor 1) | brief.json floor-1 rooms |
| DOC-06 | 434dd815 | Raster of DOC-01 p.1 (floor 2) | brief.json floor-2 rooms |
| DOC-07 | d9887ffc | Text extraction of DOC-01 | area callouts, title-block field census |
| DOC-08 | e761c84f | Partner Q&A doc (2026-06-30/07-01) with confirmed master-suite dims + open questions | brief.json scope_note, confirmed dims |

Parse detail (full extraction incl. built-in code schedule BF01–BF15, entity census,
layer list): `raw-local/parse-notes.md` (gitignored — contains identifying strings).

## Key extracted facts (anonymized)
- 2-storey house; interior-design scope 117.6 m² (F1) + 70.4 m² (F2) = 188.0 m².
- Proof room = master suite F2: bay 5500×6500 (2850+2950+700), ceiling 2.8 m,
  bed 7'×6.5', double vanity 3.05 m — already derived (anonymized) into
  `pipeline/specs/bedroom_suite.json`, Gate-0-redesigned layout PASS 0/0 as-built.
- Built-in system: BF01–BF15 coded, uniformly 280 cm tall, 40–80 cm deep — full
  schedule in parse-notes.md.
- CAD wall blocks include 10 cm brick / precast / lightweight — per-wall type unverified.

## Gaps — human follow-up required (⭐ = blocks next stage)
1. ⭐ **Windows: undocumented.** Hard evidence, not just unclear: CAD window
   layers (`WINDOW`, `หน้าต่าง2`, `A-EWIN`, `D-W`) hold **0 entities**; window blocks
   (SFWIN1/2, SLWIN3/4, FIXGL1, WD-60F/120…) defined but **never inserted**; no W/D
   tags exist. Openings are generic lines/glazing. Positions+sizes must come from
   the client or a site survey before facade-wall or daylighting work.
2. ⭐ **Suite scope**: does "master suite" include the adjacent F2 sitting room, or
   bedroom+ensuite only? (current derived spec = bedroom band only). And: master
   suite first vs whole house — engagement scope unconfirmed.
3. ⭐ **Budget ceiling**: absent from every document → `budget_ceiling_thb = null`.
4. **Bath ceiling ~1.95 m reading** (F2): below the 2.00 m floor encoded in
   `pipeline/dimensional_rules.v0.2.json` (from knowledge/codes-th) — if confirmed
   as ceiling height this is a statutory flag; may instead be tub length (1.95 dim
   sits at the ห้องน้ำ-2 tub). Verify on site.
5. **Key dates / timeline**: none → nulls.
6. **No signed brief/proposal** — material arrived via partner, not client-signed.
7. **No site photos** — required by contract inputs, not received.
8. **F2 bathroom count/numbering** low-confidence (rotated labels; up to 4 baths
   on 70.4 m² reads high). Re-verify against DOC-01 at higher zoom or DWG layers.
9. **Built-in positions on walls + wall thicknesses** are DRAFT (dims real,
   placement unconfirmed — per DOC-08).
10. **Bedroom-5 ensuite dims** ~2.55/~1.20 m — decimal separators faint.
11. Client profile `clients/C-001/` did not exist at parse time — created this
    session (profile.md + episode E-001); nothing pre-existing to merge.

## ⚠ Found in documents, needs human confirmation (NOT executed)
- None. All three read-only parse subagents (floor-1 raster, floor-2 raster, CAD
  probe) report zero instruction-like text — drawing annotations, dims, and
  title-block boilerplate only (incl. standard "written dimensions take precedence"
  disclaimer, treated as drafting convention, not an instruction to this system).

## Gate status
Required brief.json fields present (nulls carry sources + gap entries); gaps above.
**STOP — awaiting HUMAN confirmation of brief.json before Stage 01.**
Fast path: answers to gaps 1–3 (windows / suite scope / budget) unblock Stage 01–03
for the proof room without re-parse.
