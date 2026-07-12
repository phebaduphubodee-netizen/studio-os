# INTERIOR-AI — Render asset decision log

## 2026-07-12 — OWNER DECISION: NO ASSET SPEND. The asset lever was measured and it is not the lever.
Closes the 2026-07-01 "furniture pack (DEFERRED)" entry below. 31-agent workflow: repo forensics +
live-catalog CC0 hunt + adversarial license verification (21 claims survived, 3 refuted).

**The premise "furniture_realism=2 is what caps us at 3.5" is REFUTED by our own scorecards.**

| render | furn | ctx | styl | mean | overall |
|---|---|---|---|---|---|
| LivingRoom_Cam01_v01 | **4** | 1 | 2 | 3.0 | **2.5** |
| MasterSuite_Cam02_v01 | 2 | 5 | 3 | **4.0** | **3.5** |
| MasterSuite_Cam02_v03 | 2 | 5 | 3 | 3.75 | 3.5 |
| MasterSuite_Cam02_v04 | 2 | 4 | 3 | 3.625 | 3.5 |
| SittingRoom_Cam01_v01 | **3** | 4 | 3 | 3.625 | **3.5** |

Three independent kills: (a) the top furniture score in the corpus (4) belongs to the *worst*
image (2.5) — sunk by `room_context: 1`; (b) **`overall_0_5` is HOLISTIC, not a mean** —
`critique.py:112` literally says `"your honest overall, NOT just the mean"`, and v01 already
scored a 4.0 sub-mean (= `thresholds.yaml` `pass_min: 4`) yet still got 3.5/REWORK, so **no
arithmetic carries furniture 2→4 to overall ≥4**; (c) **SittingRoom already renders real CC0
meshes** (`sofa_02`, `modern_arm_chair_01`) → furniture 3, overall **still 3.5**. That is the A/B,
already run. `batch-manifest.md:197-220` says it in the repo's own voice: *"I predicted this lever
would lift that axis. **It did not.** The critic simply moved its aim to..."* — as did the
2026-07-03 clay round (Δoverall = 0.0). **Measured price of an asset library: furn 2→3, overall +0.**

**The plumbing bugs cost more than the models, and they are free to fix:**
- `build_room.py:1418` — `s = min(w/mw, d/md)` **discards the `h` param**. This, not mesh quality,
  is why the real scanned `Ottoman_01` renders as a "dark leather blob". **Buying assets before
  fixing this pays for beautiful geometry and then squashes it.**
- `build_room.py:1563-1568` — `kind=="bed"`/`"bench"` `continue` *before* `MODEL_MAP` (:1569).
  **Any bed asset purchased today is inert — it cannot load.**
- The wardrobe is not furniture at all: it is a `builtins` → single `add_box` (:1521-1531).
  The judge's *"the wardrobe is a texture-mapped box"* is a literal description of that code.
  **No purchase can fix built-in millwork; it must be generated at project mm.**

**CC0 reality (live catalogs, not memory).** Poly Haven API: 521 models, **3 beds (all period),
0 wardrobes**. Sketchfab `cc0 + downloadable`: **0 wardrobes, 0 nightstands, 0 ottomans**.
**There is no modern CC0 bed and no CC0 wardrobe in existence.** Usable CC0 (verified commercial,
redistribution-into-git OK): `side_table_01`, `modern_wooden_cabinet`, `drawer_cabinet`,
`throw_pillows_01`.

**CORRECTIONS to the 2026-07-01 entry below — do not act on its table:**
- **Chocofur's "free CC0 tier" DOES NOT EXIST in 2026.** `/free-3d-models` → 404; the store now
  sells one bundle at **$349**, and its license **prohibits redistributing meshes in any form** →
  incompatible with a repo that commits assets to git. The "~€25/pack, free CC0 tier" row is stale.
- CC-BY (Sketchfab) is the only free tier with contemporary bedroom furniture, and it is game art
  (7k–36k tris, 2K atlases) with an attribution obligation that propagates into git *and* into every
  downstream reuse of the render — into a directory literally named `cc0/`, whose loader reads no
  license field (`build_room.py:1325-1332`). The good-looking ones (Michael Amini "Malibu Crest",
  "IKEA-Style Wardrobe") carry **trade-dress exposure that CC-BY explicitly does not clear**.
- Retailer geometry cannot close the sourceability north star: IKEA's ToU bars commercial use *and*
  redistribution outright; no Thai retailer publishes downloadable 3D at any terms.

**OWNER DECISIONS (2026-07-12):**
1. **Tier = design-intent (DD grade), not client-facing marketing.** 3.5 is acceptable; `thresholds.yaml`
   asks for 4, not 5, and 3.5 is WARN not FAIL. (Independently corroborated by commit `03ee737`:
   "v04 is the deliverable of record at 3.5/5 REWORK (DD grade, NOT client-ready)".)
2. **Budget = ฿0.** No Evermotion (~$115–160), no commission ($450–900). Fix the bugs first, then
   re-measure on a **3-roll mean** (judge variance is ±0.5/roll; every critique in the table is n=1).
3. **CC-BY = NOT accepted** on client deliverables. Therefore: **no free bed, no free bench, no free
   wardrobe. Period.** CC0-only in `assets/shared/cc0/`.
4. **Wardrobe = build, don't buy** — a procedural millwork generator (door leaves, 2–3 mm reveals,
   shadow gaps, handles, plinth, chamfer). ฿0, 1–2 days, and it then serves every future project's
   built-ins. Buying a one-off wardrobe buys geometry for one room; the generator buys a capability.

**Why this is the right call even if money were free:** the ledger architecture shipped 2026-07-11
(`ffe_signoff_gate` — owner-signed canonical-key ledger mapping a mesh to the real SKU) means **the
mesh does not have to *be* the product.** So choose meshes for silhouette plausibility and license
hygiene, not for likeness — which removes most of the reason to spend at all. And the judge that
would score the purchase was measured at **ρ=0.428 vs a practising designer** (26/26 REWORK, incl.
images it scored 5.00), with **`room_context` (+0.628), not `furniture_realism`,** as the best
predictor of human opinion. Paying to move `furniture_realism` is paying to move a proxy.

**Re-open triggers:** (a) tier changes to client-facing marketing; (b) after the ฿0 work + a 3-roll
mean, `furniture_realism` is *still* the low axis AND `overall` moved; (c) a client needs a specific
real SKU shown accurately (the 2026-07-01 caveat, still valid).

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

## 2026-07-01 — Modern-luxury furniture pack (~~PENDING founder decision, DEFERRED~~ → **CLOSED 2026-07-12: DECLINED, see top entry. Its premise was refuted by measurement and its Chocofur row is factually stale. Do not act on this table.**)
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
