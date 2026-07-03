# ComfyUI + FLUX feasibility — full research record (2026-07-02)

**Question:** can the studio run the blueprint's ComfyUI + FLUX + Depth ControlNet + IP-Adapter
lane, given the RTX 3060 Laptop 6 GB machine and mandatory commercial rights for client work?
**Method:** 10-agent workflow (`wf_34372431-e1a`) — 5 research angles, each adversarially
verified by an independent fact-checker against primary sources (license texts, pricing pages,
model cards). Raw claim-by-claim output with all source URLs:
[`2026-07-02-comfyui-flux-feasibility-raw.json`](2026-07-02-comfyui-flux-feasibility-raw.json).
**Outcome:** FOUNDER DECIDED same day — stay on Gemini hybrid; FLUX lane deferred
(decision + re-open triggers in [`../DECISIONS-render-assets.md`](../DECISIONS-render-assets.md)).

> **DO NOT RE-RESEARCH this topic from scratch.** Facts below were verified 2026-07-02.
> On re-open, only refresh: current prices, license versions, and whatever the specific
> trigger is (e.g. new GPU specs). Everything else here stands until proven stale.

---

## Headline findings

1. **The gate is LICENSING, not VRAM.** FLUX [dev] Non-Commercial License v2.0 (2025-11-25;
   covers FLUX.1-dev, Depth/Canny/Fill/Redux [dev], Kontext [dev], Krea [dev], FLUX.2 [dev]):
   *outputs* are commercially usable ("You may use Output for any purpose (including for
   commercial purposes)") BUT *using the model* is restricted to non-commercial purposes —
   "revenue-generating activity" is explicitly excluded, and BFL sells a Professional tier
   aimed at "agencies producing images on behalf of named clients" (first 3 clients included;
   pricing behind sales). Running dev weights in a paid client pipeline — locally OR on a
   rented GPU — requires that paid license. Local for-profit *testing* in a non-production
   environment is expressly permitted.
2. **Paid APIs are license-clean** — the host carries the weights license: fal.ai
   ("commercial usage rights included"), Replicate ("images generated on Replicate with
   FLUX.1 models can be used commercially"), BFL API (outputs commercial, but see privacy).
3. **Apache-2.0 (fully clean) weights exist but have no clean depth stack:** FLUX.1-schnell
   and FLUX.2 klein 4B are Apache 2.0, yet every good FLUX depth-control weight (official
   Depth [dev], Shakker/InstantX Union Pro, XLabs) inherits the dev non-commercial license.
4. **The blueprint's stack (FLUX.1 + Depth ControlNet + IP-Adapter) is 2024-era.** FLUX
   IP-Adapters never got good — practitioners use Redux, SDXL-stage IP-Adapter, or FLUX.2
   multi-reference editing (up to 10 reference images). BFL deprecated Depth/Canny in its own
   API (sunset 2025-10-31). Real 2026 archviz workflows (e.g. PH's Archviz x AI v0.43,
   Feb 2026) stage SDXL ControlNets for structure and use FLUX only as a quality pass.

## Per-path verdicts (verified numbers)

| Path | Cost | Commercial rights | Verdict |
|---|---|---|---|
| **Replicate `flux-depth-dev`** | ~$0.025/img @1024² (price not on static page — confirm with a $1 test run) | explicit yes | **best pilot candidate**; only option clearly cheaper than Gemini $0.039 |
| **Replicate `any-comfyui-workflow`** (fofr) | L40S $0.000975/s ≈ $0.014/run | inherits Replicate FLUX terms | keeps the blueprint's "dispatch workflow JSON" plan alive with zero GPU ops; supported weights already include flux1-depth-dev, redux, XLabs IP-adapter |
| **fal.ai `flux-general`** (depth + IP-Adapter in one call) | $0.075/MP | yes | if an *enforced* style lock is needed; ~2× Gemini |
| **fal.ai depth-only** (`flux-control-lora-depth`) | $0.04/MP | yes | price parity with Gemini |
| **fal.ai `flux/dev`** | $0.025/MP (endpoint page; another fal page says $0.055 — endpoint page is authoritative, check at checkout) | yes | no depth control on this endpoint |
| **BFL's own API** | ~$0.01–0.05/img (FLUX.2 flex "from $0.05") | outputs yes — but Developer ToS / API Service Terms §2(b) grant BFL a perpetual right to **train on your inputs/outputs** | **REJECT on client-privacy grounds** (clay renders derive from client floor plans); also Depth/Canny deprecated, FLUX.2 has no depth conditioning |
| **RunPod pod** (4090 $0.34/hr community, $0.69 secure; Vast ~$0.29–0.50/hr) | ~$5–15/mo at 50–300 img/mo incl. ~60–100 GB network volume ($0.07/GB/mo, billed hourly; stopped-pod volume $0.20/GB/mo) | dev weights = BFL paid license needed | technically mature (templates + API port 8188 pattern documented; first boot 15–30 min) but license-blocked for client work |
| **RunPod serverless / Modal** | 4090 flex $1.10/hr; Modal L40S $0.000542/s → ~$0.01–0.03/img | same dev-license problem | cheapest raw compute, ops burden, license-blocked |
| **Comfy Cloud (official)** | $20–100/mo credit plans, RTX 6000 Pro Blackwell 96 GB, ~0.266 credits/s | n/a | curated custom-node/model support — cannot upload arbitrary ControlNet/IP-Adapter weights today → poor fit |
| **Local 6 GB — Nunchaku SVDQuant INT4** | $0 | **testing-only legal**; client deliverables = no (int4 quants are Derivatives of dev) | the one viable local stack — see below |
| **Local 6 GB — GGUF Q4/Q5** | $0 | same dev license | Q4_0 file 6.79 GB + t5xxl-fp8 4.89 GB → RAM offload only; ~2–5 min/img expected; Q4 = quality floor for client work |
| **Local — FLUX.2 klein 4B** (Apache 2.0!) | $0 | yes (cleanest FLUX license) | BFL card says ~13 GB VRAM (ComfyUI blog says 8.4 — sources conflict, plan on 13); only touches 6 GB at Q3/Q2 quality already ruled out → **relevant only with a 16 GB+ desktop GPU** |
| **ComfyDeploy** | — | — | stopped taking new managed-cloud customers after open-sourcing (Sept 2025) |
| **Together AI** | — | — | FLUX depth page 404s; Tools models gone from pricing — lane dead |

## The local Nunchaku stack (if ever needed)

- `nunchaku-flux.1-depth-dev` svdq-int4_r32 = 6.77 GB single file; depth is **baked into the
  base model** (BFL Depth-dev is a finetune, not an add-on ControlNet) → no extra ControlNet
  VRAM. Redux (style ref) ships as official ComfyUI-nunchaku workflows since v0.2.0.
- Ampere sm_86 (this laptop) fully supported (W4A4 kernels). Per-layer CPU offload floor for
  FLUX ≈ 4 GiB transformer (the "3 GiB" figure applies to Qwen-Image, not FLUX).
- Quality: SVDQuant int4 ≈ FP16-comparable, clearly better than NF4/GGUF-Q4.
- Throughput on THIS card: **no published benchmark exists** — nearest anchors: Tesla T4
  16 GB = 26 s @1024²/28 steps (17 s w/ Turbo LoRA); RTX 3080 10 GB <10 s. With forced
  offload (file > 6 GB VRAM) estimate ~30 s–2 min/img — must be measured in a 1-day spike
  before believing (16 GB system RAM is also tight; GGUF users report ~19 GB peak RAM).
- Blender exports a TRUE depth map from the clay scene → no depth-preprocessor model in VRAM.
- Classic separate-ControlNet + IP-Adapter stacks reliably OOM/crawl under 8 GB — don't try.
- Nunchaku v1.2.1 (Jan 2026) had NO FLUX.2 support.
- Preflight of this laptop passed 2026-07-02: driver 610.62 / CUDA 13.3, 174 GB free C:,
  15.7 GB RAM, Blender 5.1 installed.

## Stronger 2026 local alternatives to FLUX (all Apache 2.0, if a local lane ever matters)

- **Z-Image Turbo** (6B): ~6 GB GGUF/FP8, official Fun Union ControlNet incl. depth,
  ComfyUI template — the current best license-clean depth-locked low-VRAM option.
- **Qwen-Image-Edit 2509/2511**: union control LoRA incl. depth, a dedicated interior-design
  ComfyUI toolkit exists, Nunchaku 4-bit + async offload → ~3 GiB VRAM.
- FLUX.2 klein 4B for its editing/multi-reference mode — 16 GB+ desktop only.

## Why Gemini hybrid won (decision context)

Gemini paid tier: $0.039/img, contractual commercial rights, data isolation (privacy rules
compliant), already shipping 4.5–5/5 on the studio's own critique gate. FLUX-via-API adds
*control* (enforced depth conditioning, reproducible seeds, tunable weights) — not cost or
quality. Re-open triggers (recorded in DECISIONS-render-assets.md): overlay_fidelity catching
Gemini layout drift too often · Gemini price/terms change · 16 GB+ desktop GPU arrives.
First move on re-open: pilot Replicate `flux-depth-dev` on DEMO rooms only — vet Replicate's
data-handling terms against `.claude/rules/client-privacy.md` before any client-derived pixel
leaves the machine.
