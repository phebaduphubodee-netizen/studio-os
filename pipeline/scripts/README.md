# pipeline/scripts — geometry + CD-set engine (ported from INTERIOR-AI, 2026-07-03)

Provenance: `Desktop/INTERIOR-AI/pipeline` (predecessor project). Its rendered
OUTPUTS were poor; this infrastructure is the salvage — the owner-validated
"correct by construction" layer. **Status: ported, NOT yet smoke-tested inside
STUDIO-OS. Run a spec through `make_all.py` before trusting any of it here.**

## What's here
- `clearance_check.py` + `dimensional_rules.v0.1.json` — pure-Python clearance/
  lighting rule engine (Panero-derived values). Seed of Gate 0 (blueprint §9.2,
  M3.1). NOTE: rules JSON predates `knowledge/codes-th/` — reconcile values
  against the Authority tier before Gate-0 duty (codes-th outranks it).
- `plan_2d.py`, `elevations.py`, `rcp.py`, `schedules.py` (+ `suite_*` variants),
  `layout_gen.py`, `furniture.py`, `lighting.py` — ezdxf CD-set generators:
  plans, elevations, reflected ceiling plans, schedules from a validated spec.
- `dwg_ingest.py` — license-tiered DWG→DXF reader (avoids the ODA
  non-commercial-EULA landmine; see docs/LICENSING.md).
- `critique.py` — independent Gemini-vision critique gate (reads GEMINI_API_KEY
  from `.env`; no hardcoded secrets).
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
