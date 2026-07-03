# Stage 01 — Requirements · PRJ-2026-002 (c001-house) · 2026-07-02
Scope: master-suite proof room (F2 left bay 5500×6500) per 00_intake/gate-override.md
A2. Status: SHOWCASE (best-case assumptions A1–A5 apply; restated where used).
Geometry basis: `pipeline/scripts/specs/bedroom_suite.json` (Gate-0-revised, as-built PASS).

Priority: MUST = statutory floor · SHOULD = studio/ergonomic standard · TARGET = showcase polish.

| ID | Zone | Function | Requirement (value) | Pri | Source |
|---|---|---|---|---|---|
| R-01 | bedroom | habitability | area ≥ 8.0 m², narrow side ≥ 2500 mm → bay 5500×6500 net-of-ensuite complies | MUST | ฉ.55 ข้อ 20 via pipeline/dimensional_rules.v0.2.json (knowledge/codes-th/mr55-residential-dimensions.md) |
| R-02 | bedroom | vertical clearance | ระยะดิ่ง (floor-to-floor basis) ≥ 2600 mm; spec ceiling 2800 | MUST | ฉ.55 ข้อ 22 via dimensional_rules; brief.json (ceiling 2.8 m) |
| R-03 | ensuite | vertical clearance | floor-to-ceiling ≥ 2000 mm; spec ensuite ceiling = 2000 exactly (assumption A4: plan's 1.95 read as tub length) | MUST | ฉ.39 ข้อ 9 via dimensional_rules; 00_intake/gate-override.md A4 |
| R-04 | ensuite | wet-area size | combined bath+WC ≥ 1.50 m²; ensuite 2900×2600 interior ≫ floor | MUST | ฉ.39 ข้อ 9 via dimensional_rules |
| R-05 | suite | circulation | zero blocked reach: every door/fixture reachable; bottleneck ≥ 610 ergonomic pinch, main path target 910; swing arcs unobstructed | MUST (engine) | suite_clearance v0.4.2 rule set (dimensional_rules circulation.*; Gate-0 doctrine qa/reports/2026-07-02-gate0-full.md) |
| R-06 | suite | doors | entry 900 mm in-swing (south), ensuite 800 mm out-swing (south wall) — ≥ 800/1900 studio floor | SHOULD | spec door blocks; studio floor re-tiered 2026-07-02 (door 800/1900 = studio, not statutory) |
| R-07 | bedroom | sleeping | 6-ft bed (2000×2160) on 150 mm platform; ≥ 1 long side ≥ 762 mm make-bed clearance | SHOULD | brief.json rooms (bed), dimensional_rules bedroom.clearance_around_bed |
| R-08 | bedroom | client program | preserve built-in program: headboard/TV wall 3330×574 h2800, wardrobe run 2100+600 legs, double vanity 2850 | SHOULD | brief.json rooms + BF schedule (BF09-3/BF10/BF12 basis); client function, not statute |
| R-09 | suite | daylight/vent | assumption A1: glazing band on terrace (south) wall; if built for real: openable area ≥ 10% floor area | MUST-if-real / ASSUMED | ฉ.39 ข้อ 13 via dimensional_rules; gate-override A1 |
| R-10 | bedroom | lighting | ambient 10–20 fc maintained avg, CCT 2700–3000 K, CRI ≥ 90; 100-lux floor (see erratum) | SHOULD (design) / SHOULD (100 lux, studio-adopted — erratum E-r10) | dimensional_rules lighting.* (DRAFT tier) + legal_lux_floors scope_note |
| R-11 | ensuite | lighting | 20–30 fc, CCT 3000–4000 K; mech vent 2 ACH if windowless | SHOULD / MUST(vent) | dimensional_rules lighting.* + ฉ.39 ตาราง 4 |
| R-12 | suite | style envelope | warm contemporary, built-in-heavy (client-plan observation — NOT confirmed preference; Stage 02 to propose, human approves) | TARGET | clients/C-001/profile.md (observations, E-001) |
| R-13 | all artifacts | privacy | zero identifying strings in any committed/generated artifact; IDs only (C-001/P-001) | MUST | .claude/rules/client-privacy.md; 00_intake/inventory.md privacy note |

No orphan wishes: every row traces to brief.json, profile.md, gate-override.md, or a
cited code value. Human sign-off for this stage = standing best-case override
(00_intake/gate-override.md); re-verify rows R-03/R-09 if real client data arrives.

---
**Erratum E-r10 (2026-07-02, post-MARS re-tier — mirrors the R-06 door precedent):**
R-10's original "MUST (100 lux)" over-claimed statute: ฉ.39 ตาราง 3 has no 100-lux
row for a detached-house bedroom (rows = collective corridors / hotel & collective
rooms / bathrooms). Re-tiered to SHOULD (studio-adopted floor) per
`pipeline/scripts/dimensional_rules.v0.2.json` legal_lux_floors.scope_note.
The ENSUITE's 100 lux remains statutory (bathroom row) — carried by R-11.
Found by the Stage-02 MARS panel (02_concept/critique-log.md); values unchanged,
tier label corrected. Concept §5 already carries the scoped wording.
