---
paths: ["pipeline/comfyui/**", "**/*.workflow.json", "projects/**/04_visualization/**"]
---
# Render Payload Rule (fires on ComfyUI workflow files)
- Payloads are compiled dual-track (blueprint §8.2): T5 = narrative prose
  (structure, space, camera, lighting story); CLIP = short comma tags
  (materials, style, finishes). NEVER duplicate the same long text into both.
- FLUX graphs: no negative prompts (no standard CFG) — convert exclusions to
  aggressive positive framing. SD-class graphs: negatives go in the dedicated
  conditioning node only.
- Token weights are un-normalized in ComfyUI: max 2 weighted terms per prompt,
  weight ceiling 1.3. Prefer restructuring over stacking weights.
- Every payload must reference its ControlNet map files (D_*/S_*) and record
  seed + weights in the batch manifest for memory write-back.
