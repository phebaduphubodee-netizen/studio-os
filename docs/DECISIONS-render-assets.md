# INTERIOR-AI — Render asset decision log

## 2026-07-02 — ComfyUI+FLUX feasibility research → DECIDED: stay on Gemini hybrid
Founder asked whether the blueprint's ComfyUI+FLUX lane is achievable. 10-agent web research,
claims adversarially verified against primary sources (license texts, pricing pages). Findings:

**The real gate is LICENSING, not VRAM.** FLUX [dev] Non-Commercial License v2.0 (2025-11-25,
covers dev + Depth/Canny/Fill/Redux + Kontext + FLUX.2-dev): outputs are commercially usable,
but *using the model* in revenue-generating work requires a paid BFL license (Professional tier
targets exactly "agencies producing images for named clients"; price = contact sales). So
self-hosting dev weights (local OR rented GPU) for client deliverables = no, without that license.
Paid APIs are clean: the host carries the weights license.

| Path | Cost | Commercial rights | Verdict |
|---|---|---|---|
| Replicate `flux-depth-dev` (hosted API) | ~$0.025/img (verify w/ test run) | explicit yes | best pilot candidate |
| fal.ai `flux-general` (depth+IP-Adapter one call) | $0.075/MP | yes | if enforced style-lock needed |
| fal.ai depth-only | $0.04/MP | yes | parity with Gemini |
| Replicate `any-comfyui-workflow` (runs our workflow JSON) | ~$0.014/run (L40S/s) | inherits Replicate FLUX terms | keeps blueprint's ComfyUI plan alive, zero GPU ops |
| RunPod 4090 pod/serverless + ComfyUI | ~$5–15/mo at 50–300 img | dev weights = BFL license needed | only with Apache models or paid license |
| Local 6GB (Nunchaku svdq-int4 flux.1-depth-dev + Redux, ~30s–2min/img est.) | $0 | testing-only is legal; client work = no | 1-day spike as offline dev lane only |
| BFL's own API | ~$0.01–0.05/img | yes, BUT terms grant BFL training rights on inputs/outputs | REJECT on client-privacy grounds |

**Stack drift:** blueprint's FLUX.1+Depth-ControlNet+IP-Adapter is 2024-era. FLUX IP-Adapters
never got good (use Redux / FLUX.2 multi-reference); BFL deprecated Depth/Canny in its API;
2026 Apache-2.0 low-VRAM alternatives if a local lane ever matters: Z-Image Turbo (+Fun Union
depth ControlNet, ~6GB) and Qwen-Image-Edit (+Nunchaku, ~3GiB, has an interior-design toolkit).
FLUX.2 klein 4B (Apache) wants 13GB native — not this laptop; relevant only with a 16GB desktop.

**Recommendation:** production stays on Gemini hybrid ($0.039/img, clean rights, data isolation,
already 4.5/5 SHIP). FLUX-via-API is a *control* upgrade (enforced depth lock, seeds, ControlNet
weights), not a cost or quality one — pilot Replicate flux-depth-dev on the demo rooms (never
client data until its data-handling terms are vetted against client-privacy rules) only if the
overlay-fidelity gate starts failing Gemini too often. Full research record (do NOT redo):
`docs/research/2026-07-02-comfyui-flux-feasibility.md` (+ raw claim-by-claim JSON alongside).

**FOUNDER DECISION (2026-07-02): stay on Gemini hybrid.** FLUX lane (incl. the local Nunchaku
spike) DEFERRED — a preflight on this laptop confirmed the spike is viable if ever needed
(RTX 3060 Laptop 6 GB, driver 610.62/CUDA 13.3, 174 GB free on C:, 15.7 GB RAM, Blender 5.1
at `C:\Program Files\Blender Foundation\Blender 5.1\`). Re-open triggers: (a) overlay_fidelity
starts catching Gemini layout drift too often, (b) Gemini pricing/terms change, or (c) a
16 GB+ desktop GPU arrives (then FLUX.2 klein 4B / Nunchaku-class local becomes competitive).

## 2026-07-01 — Modern-luxury furniture pack (PENDING founder decision, DEFERRED)
Founder wants renders as beautiful as his friend's studio (PORS). The free CC0 pipeline
reaches ~70–75%; the biggest remaining lever is **modern-luxury furniture/material assets**
(Poly Haven / free CC0 has only vintage furniture, so we retint dark leather → cream boucle).

Fired Gemini DR (`research/2026-07-01-asset-sourcing-DR.md`) + **web-verified real prices/licenses**
(DR fabricates these; real money at stake). Verified options:

| Option | Price (verified) | License (verified) | Pipeline fit |
|---|---|---|---|
| **BlenderKit Full** ⭐ | $118.80/yr ($17.90/mo) | RF + CC0; **client-delivered renders = allowed commercial use** (selling the image, not the model — matches our LICENSING.md); can't resell raw models | BEST: 48k assets built into Blender as an add-on → automatable download+placement |
| **Chocofur** | ~€25/pack one-time (€8.90/model); free CC0 tier | commercial renders OK | Blender-native Cycles shaders, modern; best if one-time preferred over subscription |
| 3dsky / Dimensiva | $5–15/model (3dsky); Dimensiva ~€29/mo | royalty-free commercial | huge selection incl. exact boucle/marble/brass, but manual per-model |

**Recommendation:** BlenderKit Full ($118.80/yr) — only option that plugs into Blender (automatable).
One-time alternative: Chocofur packs (~$27).
**Status: DEFERRED — founder will decide later (2026-07-01). AI cannot purchase; needs founder go-ahead.**
On approval: subscribe/buy → wire into `build_room.py` (swap MODEL_MAP vintage→modern, auto-place).

Honest caveat: assets close most of the gap; the last ~10–15% is human art-direction (styling/composition),
which no pack buys.

## 2026-07-01 — BREAKTHROUGH: HYBRID (3D render -> Gemini image model) closes the gap
Founder surfaced `banana-claude` (Claude Code skill wrapping Google's Gemini image model
"Nano Banana", `gemini-3.1-flash-image-preview` / `gemini-2.5-flash-image`). Tested the HYBRID
path directly (`tools/gemini_image.py`): fed our finished 3D hero render as the STRUCTURAL
CONTROL image + a "make photoreal luxury, keep exact layout" prompt. Result
(`output/_checkpoint_G_hybrid_gemini.png`) = ~PORS quality in ~30s for ~$0.039/image.

Why it wins where pure-3D and pure-AI each fail:
- Pure 3D (Blender+CC0): dimensionally exact + buildable, but beauty capped ~85% (CC0 assets).
- Pure AI-image: gorgeous but HALLUCINATES furniture/sizes -> not buildable, inconsistent across views.
- HYBRID: our render supplies the correct layout/placement/proportions (the thing AI invents);
  Gemini supplies photoreal fabric/wood/light/shadow (the thing 3D can't cheaply reach).
  Bouclé weave, real walnut grain, soft window light + shadows, pillows read as soft — all added
  while the composition/camera/palette stayed faithful.

Cost/licensing: free tier ~500 img/day but COMMERCIAL RIGHTS RESTRICTED on free tier; use PAID
tier ($0.039/1024px img, full commercial rights + data isolation) for client work. Trivial cost.

RECOMMENDATION UPDATE: the furniture-pack purchase is now LOWER priority — the hybrid closes most
of the beauty gap for ~$0.04/image without buying assets. Keep the 3D/spec pipeline as the
dimensional source of truth + control image; add the Gemini pass as the final BEAUTY layer.
Furniture pack only if a client needs a specific real SKU shown accurately.
Decision on adopting `banana-claude` skill vs. our own `gemini_image.py`: DEFERRED to founder
(our script already proves the capability at $0; the skill adds prompt-engineering polish).
