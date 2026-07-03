# INTERIOR-AI deliverable — BEDROOM SUITE  5.5 x 6.5 m  (~36 m²) (metric, v0.2)

Assembled 2026-07-02. **DRAFT** — positions read from the friend's 1:75 furniture plan where legible, else approximated; overall footprint / ceilings / windows still to confirm vs the DWG. Sign `QA-CHECKLIST.md` before any client use.

- `bedroom_suite_SHEETSET.pdf` — the CD set: cover · floor plan (1:50) · RCP · 4 wall elevations · schedules
- `suiteplan_bedroom_suite.dxf`, `suitercp_bedroom_suite.dxf`, `suiteelev_bedroom_suite_*.dxf` — editable metric CAD masters (1:1 mm; open in any DXF app)
- `bedroom_suite.spec.json` — the room-spec@0.2 everything derives from
- `build_room.rb` — builds the **native, editable** 3D model inside SketchUp Pro (Window ▸ Ruby Console → `$INTERIOR_SPEC='.../bedroom_suite.spec.json'; load '.../build_room.rb'`)
