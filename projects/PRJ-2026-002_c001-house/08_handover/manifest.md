# Handover manifest · PRJ-2026-002 (c001-house) · closed 2026-07-02
Status: **SHOWCASE COMPLETE** (best-case override A1–A5; not a client release).
Owner approvals: brief override (Stage 00), image "go" (Stage 05, extends to
showcase release at Stage 07). All work commits: e8b4d16 (intake), e919329
(Stage 00→05 run), this commit (approval + 06→08). Local only — NOT pushed
(client-derived project; privacy decision of record).

## Delivered artifacts (versions + sources)
| Artifact | Path | Version/provenance |
|---|---|---|
| Hero render (APPROVED) | assets/projects/PRJ-2026-002/renders/R_PRJ002_MasterSuite_Cam01_v01.png | registry v004@production, gemini-3-pro-image-preview, sha 2c5b209a…, judge 4.5+5.0 SHIP |
| Final copy (native res) | assets/projects/PRJ-2026-002/upscales/R_PRJ002_MasterSuite_Cam01_v01_final-nativeres.png | upscaler not wired — disclosed in presentation.md |
| Control clay + overlay | assets/projects/PRJ-2026-002/maps/ (same stem) | Blender 5.1.2 Cycles GPU 256; overlay eyeball PASS |
| CD set v01 | 04_visualization/cd-set_v01/ (SHEETSET.pdf + 6 DXF + schedules) | suite_* engines on scene-graph sha f34c999f… |
| Scene graph | 03_layout/scene-graph.json | = pipeline/scripts/specs/bedroom_suite.json (Gate-0 revised) |
| Clearance proof | 03_layout/clearance-report.md | suite_clearance v0.4.2, PASS 22/22 |
| Concept + review | 02_concept/{concept.md, critique-log.md} | MARS wf_b4ed14a0-154, r1 |
| Requirements | 01_brief/{requirements.md, success-criteria.md} | 13 rows cited |
| Intake | 00_intake/{brief.json, inventory.md, gate-override.md} | 8 docs, SHA-mapped; raw-local gitignored |
| QA trail | 05_qa/{qa-report.md, approved_*.md, scorecards ×2} + qa/reports/PRJ-2026-002/ | thresholds v1 |
| Client memory | clients/C-001/{profile.md, episodes/E-001, E-002} | E-002 = approved settings |

## Sources
Client plan PDF + DWG (identifying) — LOCAL ONLY in 00_intake/raw-local/ (SHA map
in inventory.md); identity map in raw-local/parse-notes.md. Nothing identifying in
any committed artifact (scans clean at e8b4d16, e919329, and this commit).

## Profile-update PR (contract requirement — deferred, recorded)
Profile edits ship via the weekly memory-consolidation PR flow. This repo's client
data is NOT pushed to the remote this run, so no PR opened; the consolidation
inputs are staged in episodes E-001/E-002. When the owner next syncs: fold "approved
showcase configuration" + household observations into profile.md via that flow.

## Tracker
No external tracker exists; this manifest + phase-status memory = the tracker.
**Project marked CLOSED (showcase).** Reopen path: real client answers → re-run
Stage 00 merge → invalidated stages re-run (gate-override.md rule).
