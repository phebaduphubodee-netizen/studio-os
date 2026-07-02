# Stage 05 — QA · {{PROJECT_ID}}   [Gates 3–4 + human review]
## Inputs
Gate-2-passed renders + scorecards; brief rubric; brand palette (if any).
## Process
Gate 3: ΔE00 brand check + LLM-judge rubric vs requirements. Gate 4: set consistency (multi-view) + revision drift (post-edit/upscale LPIPS). Failures → vision feedback loop (blueprint §10), cap 3, then human triage.
## Outputs (required)
- scorecards (JSON) in qa/reports/ mirror · _inbox/ folder of pass-images awaiting HUMAN approval
## Gate
Human approval per image. Approved settings written to client episodic memory.
