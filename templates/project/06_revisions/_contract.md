# Stage 06 — Revisions · {{PROJECT_ID}}
## Inputs
Client/designer change requests (annotated images or notes).
## Process
Convert each request into a structured repair ticket (region mask + minimal prompt delta). Prefer localized inpainting over full regeneration. Re-run Gate 4 revision-drift check outside the mask.
## Outputs (required)
- tickets.md (request → action → result) · revised renders (v+1 naming)
## Gate
Background LPIPS delta within threshold; client-visible change matches the ticket. Human confirms.
