# Stage 03 — Layout · PRJ-2026-001   [Geometry gate = Gate 0]
## Inputs
02_concept/concept.md, floor plan, furniture candidates with real dimensions (catalog).
## Process
Commit placement to scene-graph JSON; run geometry engine: clearances (passage ≥ code value, turning circles, door-swing arcs, knee/toe), 3D bounding-box collisions, odd-rule groupings.
## Outputs (required)
- scene-graph.json · clearance-report.md (every check: value vs threshold, pass/fail)
## Gate
HARD: zero collisions, zero clearance violations vs knowledge/codes-th. Unbuildable layouts never reach rendering.
