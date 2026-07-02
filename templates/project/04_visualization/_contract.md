# Stage 04 — Visualization · {{PROJECT_ID}}   [Gates 1–2]
## Inputs
Approved scene graph; SketchUp/CAD clay + line exports per approved cameras; concept palette.
## Process
1. vision-reviewer validates depth (D_*) and segmentation (S_*) maps against the plan.
2. prompt-engineer compiles dual-track payloads (see .claude/rules/render-payloads.md) from the registry.
3. Dispatch to ComfyUI (FLUX + Depth ControlNet + IP-Adapter); poll; fetch.
4. Gate 1 (Image+Prompt QA) then Gate 2 (Camera/Lighting/Material QA) per qa/thresholds.yaml.
## Outputs (required)
- batch-manifest.md (payload version, seeds, ControlNet weights) · renders in assets/projects/{{PROJECT_ID}}/renders/ · scorecards → ../05_qa/
## Gate
Only Gate-1+2 passes proceed; hard failures reseed automatically (≤3 repair iterations).
