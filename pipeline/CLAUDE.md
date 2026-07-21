# pipeline/ — generation infrastructure (loaded when working here)

Provenance: the build/ingest/export laws below (§ Blender build law → § Export
and interop law) are distilled from
`knowledge/_inbox/interior-ai/2026-06-30-blender-pipeline-DR.md` — REFERENCE
tier (a research DR, not domain truth, not statute). Cited inline as
`DR:<line>`; repo evidence as `file:line`. Thai statutory values never come
from a DR: `knowledge/codes-th/` remains the sole authority.

- scripts/ holds the ported INTERIOR-AI geometry + CD-set engine — read
  scripts/README.md first (provenance, unvalidated status, the LLM-emits-
  SPEC-only law). Render direction of record: HYBRID — 3D render as
  structural control, then a Gemini image pass (docs/DECISIONS-render-assets.md);
  this sidesteps the 6 GB-VRAM limit for FLUX local.

- comfyui/workflows/*.workflow.json are VERSIONED API-format graphs.
  Never hand-edit a deployed graph; copy → bump version suffix → edit → test.
  Schema-validate before commit (validator lands in pipeline/scripts/, Phase 2).
- prompts/registry/ holds compiled prompt payloads: immutable versions,
  labels dev|staging|production. Promote by re-pointing the label, never by
  editing a published version. Organize by intent/domain, never by model.
- Dual-track rule for diffusion payloads (blueprint §8.2): T5 track = narrative
  prose (structure, camera, lighting story); CLIP track = short comma tags
  (materials, style). Never duplicate the same paragraph into both.
- FLUX has no standard CFG: convert negatives to positive framing at compile
  time. SD-class graphs may use real negative conditioning. Token weights are
  passed un-normalized — enforce a weight budget; prefer restructuring.
- Render dispatch is ask-tier (paid/GPU work). GPU note for this machine:
  RTX 3060 Laptop 6 GB — FLUX.1-dev local is NOT feasible; Phase 2 targets a
  cloud GPU or API endpoint. Do not propose local FLUX runs here.
- Generation/render tasks never write into knowledge/ or clients/ (hook +
  rule enforced). Outputs land in assets/projects/<PRJ>/ (LFS) and the
  project's 04_visualization/ stage dir.

## Blender build law (headless materializer)

- LAYER LAW — three decoupled layers, only the MIDDLE is Blender (DR:6-17):
  (1) rules + spec + clearance = PURE PYTHON, NO `bpy` — "dimensional
  correctness is a CONSTRAINT problem, not a Blender problem" (DR:7-8);
  (2) Blender materializer; (3) render + export. Corollary: never import `bpy`
  into rule/gate/scoring code — it must stay runnable under plain `python`.
- INVOCATION — headless, one process per job (DR:12-13):
  `blender -b --factory-startup --python pipeline/scripts/build_room.py -- spec.json`
  (as wired in `make_all.py:194`; the DR writes the `-P` short form).
- GEOMETRY = DATA API ONLY: `bpy.data.meshes.new` + `from_pydata`,
  `bpy.data.libraries.load`. NEVER `bpy.ops` for geometry — it dies with
  `poll() failed` in `--background` (DR:13-14). Headless-safe `bpy.ops`
  exceptions already relied on: `wm.save_as_mainfile` and `render.render`
  (`build_room.py:133,170`), plus `preferences.addon_enable` /
  `import_scene.gltf` on the glTF asset-import path (`build_room.py:1554,1624`).
  `bpy.ops` creep breaks headless — a named top risk (DR:44). This repo scopes
  the ban to GEOMETRY ops; the four ops actually used are headless-safe
  (`build_room.py:170` comment: "'render' op is headless-safe (unlike geometry
  ops)").
- OPENINGS are authored quad face-loops, NOT booleans — booleans produce n-gons
  that a SketchUp recipient will see (DR:14-15).
- RENDER ENGINE = CYCLES. EEVEE needs EGL/Xvfb — avoid headless; the DR names
  an EEVEE-on-headless crash as a top risk (DR:16, DR:45). The script (not the
  CLI) owns engine/device/output — CLI flag-ordering trap — and MUST log the
  active device + samples so a silent CPU fallback is caught (DR:16-17).
  `build_room.py:169` prints `cycles device=… samples=…`; keep that line.

## Scale assertion — every ingest of external geometry

- THE TRAP: SketchUp exports IMPERIAL even when the model was authored in metres
  (~0.0254× error) — "a plausible-but-wrong-scale model = the exact failure we
  sell against". The DR's instruction is a MUST: add a scale assertion on every
  ingest (DR:25-26); a silently mis-scaled model corrupting the differentiator
  is named among the DR's top risks (DR:43 — an unranked list).
- RULE: no external geometry (.skp, DWG/DXF, glTF/OBJ, mesh drops) reaches a
  spec or a gate until its unit is RESOLVED and asserted — never assumed.
- Fail-loud precedent to copy for the ASSERT half of that rule:
  `clearance_check.py` handles the inch spec@0.1 only and hard-exits on a metric
  @0.2 spec instead of mis-reading it (`clearance_check.py:519-537`).
- Unit-RESOLUTION precedent only: `dwg_ingest.py` resolves the drawing unit from
  the `$INSUNITS` header → mm-per-unit, falls back to inferring from dimension
  sizes, and REPORTS the provenance of that decision
  (`dwg_ingest.py:17,48,164-180`). Note its terminal branch returns
  `1.0, "assumed mm (no $INSUNITS, no dimensions)"` and processing continues
  (`dwg_ingest.py:180`) — it assumes and does NOT fail, so a real assertion still
  has to be added. Do not copy that path believing it satisfies the rule above.
- Conversion constant in the Blender layer is `IN = 0.0254` (`build_room.py:25`,
  `build_floor.py:31`).

## Engine of record

- The DR names "maintaining TWO generators (.py + .rb)" as a top risk and
  prescribes the mitigation: pick an engine-of-record (DR:43-44).
- PROPOSED (2026-07-13, from repo state — NOT yet owner-confirmed, so do not
  cite it as settled): make `build_room.py` the engine of record. The DR does not
  pick one, and no owner signature exists for this; carry it to
  `docs/strategy.md` for confirmation before treating it as law.
- The evidence behind the proposal: `build_room.rb` (native SketchUp Ruby) sits
  at REFERENCE tier and "was never smoke-tested in a real SketchUp"
  (`scripts/README.md:66-68` — this is what supports the blanket claim). The
  `.rb`'s own header scopes its untested status more narrowly: the v0.1
  rectangular path is unchanged, "the v0.2 polygon path is NEW and NOT yet
  smoke-tested in real SketchUp (no SketchUp on the build machine)"
  (`build_room.rb:19-22`).
- Either way: if the `.rb` is worked on or revived, it needs its own validation
  against the live SketchUp Ruby API before any client deliverable
  (`build_room.rb:22`).

## Export and interop law (SketchUp-using collaborator)

- ONE-WAY ONLY. No native .skp exchange, no clean round-trip. Never promise an
  editable SketchUp file back from exported geometry — Blender→SketchUp arrives
  as triangle soup (non-solid, multi-material), destroying the recipient's
  component/section workflow (DR:19-21). Over-promising an editable .skp is a
  named top risk (DR:44).
- FINE / Blender superior (DR:22-23): final Cycles renders, walkthroughs,
  view-only GLB/USDZ; and one-way INGEST of the collaborator's `.skp` via the open-source
  SketchUp Importer (Windows/Mac only) to run the clearance check on it —
  subject to the scale assertion above.
- 3D exchange DROPS dimensions/text/sections → construction documents ship FLAT
  2D (PDF/DWG/DXF/annotated), never a 3D round-trip (DR:24, DR:32).
- HANDOFF FORMAT — the DR RECOMMENDS, founder to confirm (that is the heading of
  the block this line sits in, "Deliverable decision (RECOMMENDED — founder to
  confirm)", DR:28): "Standardize handoff on glTF if friend on SketchUp 2025+,
  else DAE/COLLADA" (DR:33). Not law here until confirmed; the rest of that
  block's commercial decision is routed to docs/strategy.md, not distilled here.
- Live tension to know before you read `build_room.rb`: its stated route is to
  ship a generated Ruby SCRIPT that the collaborator runs inside a licensed
  desktop SketchUp — i.e. NOT the geometry export the DR rules out
  (`build_room.rb:1-9`). That channel is untested (see Engine of record); do not
  cite it as a validated editable deliverable.

## Automation ceiling (REFERENCE tier — shapes what a gate may claim)

- The DR's honest estimate: ~70-85% of the LABOR for a still is automatable
  (spec→geometry, units, asset import, camera rig, lighting, render, denoise,
  batch, and the clearance/scale check); the un-automatable ~15-30% =
  LAYOUT GENERATION, composition/lighting taste, and final scale/dimensional QA
  (DR:35-39).
- Operational form of that line: "automation CHECKS a layout, a human GENERATES
  it" (DR:38-39). Gates in this dir verify a layout; they do not authorize one.
  Also stays MANUAL per the DR (DR:47-50): aesthetic/client judgment, hero
  camera + lighting final tuning, dimensional APPROPRIATENESS (code proves two
  things are 800 mm apart; a human knows whether 800 mm is right here),
  local-code compliance, and the final QA sign-off that scale and clearances are
  right on every deliverable.
- The DR also flags: a DRAFT rules JSON is not the recipient's local code —
  verify before client use (DR:45). Statutory floors come from
  `knowledge/codes-th/` (carried into `dimensional_rules.v0.2.json`), never from
  a DR.
