# Licensing gate · PRJ-2026-002 deliverables · 2026-07-02
Register: docs/LICENSING.md (ported from INTERIOR-AI salvage).

| Asset in deliverable | Source | License status |
|---|---|---|
| Clay geometry (room, built-ins, bed, fixtures) | build_room.py procedural output from scene-graph.json | studio-generated — clear |
| Hybrid render R_PRJ002_MasterSuite_Cam01_v01 | Gemini image edit over studio clay, **PAID tier** (pro image model) | commercial rights per paid-tier terms — clear (free tier would NOT be; docs/DECISIONS-render-assets.md) |
| CD set (plan/RCP/elevations/schedules/SHEETSET) | suite_* engines, procedural | studio-generated — clear |
| CC0 asset library (raw/assets/cc0) | — | NOT USED in this batch (no external mesh/texture/HDRI in the clay) |
| Client plan PDF/DWG content | raw-local (gitignored) | NOT reproduced in any deliverable — layout re-derived into anonymized spec; drawing itself never shipped |

**Gate: PASS** — every shipped artifact is studio-generated or paid-tier licensed;
no third-party asset entered the batch. Caveat: SynthID watermark presumed present
in Gemini output (disclosure, not a restriction).
