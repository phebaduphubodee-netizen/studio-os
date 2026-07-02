# pipeline/scripts — geometry + CD-set engine (ported from INTERIOR-AI, 2026-07-03)

Provenance: `Desktop/INTERIOR-AI/pipeline` (predecessor project). Its rendered
OUTPUTS were poor; this infrastructure is the salvage — the owner-validated
"correct by construction" layer. **Status: smoke-tested in place (2026-07-03):
`make_all.py` on `specs/living_demo.json` ran hands-off — clearance PASS → full
CD set (plan/RCP/elevations/schedules) → Blender 5.1 render → packaged
deliverable + SHEETSET.pdf. Gemini legs live-tested same day (`.env` key in
place): critique gate scored the clay control 1/5 NOT_CLIENT_READY (correct)
and the hybrid pass 4/5 REWORK — photoreal/proportion/furniture 5/5, remaining
gap = human art-direction (styling/composition), as DECISIONS-render-assets.md
predicted.**

## What's here
- `clearance_check.py` + `dimensional_rules.v0.2.json` — pure-Python clearance/
  lighting rule engine. Seed of Gate 0 (blueprint §9.2, M3.1). v0.2 merges Thai
  statutory floors from `knowledge/codes-th/` (Authority, per-value citations in
  `thai_code_minimums`); ergonomic values remain Panero-derived DRAFT.
  v0.1 kept for diff/rollback per the pipeline versioning convention.
- `plan_2d.py`, `elevations.py`, `rcp.py`, `schedules.py` (+ `suite_*` variants),
  `layout_gen.py`, `furniture.py`, `lighting.py` — ezdxf CD-set generators:
  plans, elevations, reflected ceiling plans, schedules from a validated spec.
- `dwg_ingest.py` — license-tiered DWG→DXF reader (avoids the ODA
  non-commercial-EULA landmine; see docs/LICENSING.md).
- `critique.py` — independent Gemini-vision critique gate (reads GEMINI_API_KEY
  from `.env`; no hardcoded secrets).
- `hybrid_render.py` — the HYBRID beauty pass (render direction of record):
  clay control render + "keep exact layout" instruction → Gemini image model →
  photoreal repaint at ~$0.04/img. Ported from INTERIOR-AI tools/gemini_image.py.
  Client work must run on the PAID tier (free tier = no commercial rights).
- `assets.py` — Poly Haven CC0 fetcher (populates `assets/shared/cc0/`).
- `package.py`, `qa_checklist.py`, `make_all.py` — deliverable assembly.
- `build_room.py` (Blender materializer) / `build_room.rb` (native SketchUp
  Ruby) — REFERENCE tier: build_room.rb was never smoke-tested in a real
  SketchUp; keep for the hybrid-render path (docs/DECISIONS-render-assets.md).
- `specs/` — example spec schemas (bedroom_suite, living_demo).

## Deps (not yet in a requirements file here)
`ezdxf`, `python-dotenv`, `google-genai` (critique), `bpy` only inside Blender
for build_room.py. Install per-need; keep tools/requirements.txt separate.

## Law of the layer (carried from the predecessor's hard lesson)
The LLM emits a validated SPEC only — it never writes geometry code. One fixed,
tested generator turns spec → geometry → drawings. Dimensional correctness is
the studio's actual edge.
