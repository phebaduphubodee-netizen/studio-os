# pipeline/ — generation infrastructure (loaded when working here)

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
