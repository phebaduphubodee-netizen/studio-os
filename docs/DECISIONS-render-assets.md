# INTERIOR-AI — Render asset decision log

## 2026-08-01 — OWNER ORDER: the "฿0 + CC0/public-domain only" clause is CANCELLED.
Owner, verbatim: *"฿0 + CC0/public-domain เท่านั้น ยกเลิกข้อนี้"*. This **amends** the
2026-07-12 entry below (decisions 2 and 3 of it). That entry's *analysis* stands and is not
retracted — the asset lever really was measured and really was not the lever. What is cancelled
is the **sourcing fence** it left behind.

**Why it had to go, and it is not the reason it was written.** The clause was authored to close a
question about **paid libraries** (Evermotion, a commission, BlenderKit). By 2026-08-01 its live
effect was to fence out the best **free** source available — SketchUp 3D Warehouse, which a working
designer named in one sentence when the owner asked, and which our 2026-07-01 asset-sourcing DR does
not mention at all. It had also become the **narrowest rule in this repo about its own subject**:
`docs/LICENSING.md` (the load-bearing, adversarially-researched licensing law) already whitelists 3D
Warehouse as a Combined-Work source, `pipeline/scripts/warehouse.py` already fetches it into its own
cache with a `LICENSE.txt` and per-model `SOURCE.json`, and `.gitignore:50` already keeps that cache
out of git. Every other artifact in the repo had already accepted the source. This clause was the
only thing still saying no.

**THE SOURCING RULE, as of now:** *any source whose licence permits commercial use of the RENDER.*
That admits CC0/public domain, **Trimble General Model License (3D Warehouse)**, CC-BY with the
attribution recorded, and paid royalty-free libraries.

**Five things this order does NOT touch**, because they are licence text and client-liability law
rather than studio preference — `docs/LICENSING.md` is UNCHANGED and still binding:
1. **Non-redistributable models never enter version control.** They live in a gitignored cache with
   provenance; the fetch is reproducible from the entity id. Already wired, already correct.
2. **The client receives the assembled ROOM SCENE only** — never a standalone model, never the asset
   bundle (GML §2.4 no standalone resale, §2.6 no aggregation). This is the one rule that protects
   the founder's real liability exposure and it predates and outranks this entry.
3. **Scale is ASSERTED on every ingest, never assumed** (`pipeline/CLAUDE.md`). Warehouse content is
   user-uploaded with no scale guarantee, and the SketchUp imperial trap turns a metre-authored model
   into a 0.0254× one that still looks like a model. Also: the content is unfiltered — the "Thai
   Buddha altar" hit is somebody's entire 13.9 × 17.3 m project at 2.1 M faces, so a model has to be
   MINED for the part wanted, and the scale assertion is what tells you which one you got.
4. **Trade dress is not a licence question.** A permissive licence on a model that copies a named
   product's design clears the model, not the design (the 2026-07-12 note on the CC-BY "Michael
   Amini / IKEA-style" assets was right about this and is carried forward untouched).
5. **Money is the owner's call, per purchase.** ฿0 is no longer a RULE, but a spend is an
   irreversible outward-facing action and is never made without an explicit go-ahead. What the
   cancellation buys *immediately* is the free sources the clause excluded — those need no decision.

**Status on disk when this was written:** 13 warehouse models already fetched and rendered
(TRN-001 rounds 13–17, 2026-08-01) under R8's build-vs-acquire order. The code was already right;
only the written rule was stale. That is the repo's standing *"the file of record is not
automatically the file that runs"* defect wearing a licensing shape — logged, not excused.

**Superseded claims — do not act on these lines in the entry below:** its decision 2 (*"Budget =
฿0"*) and decision 3 (*"CC-BY = NOT accepted … CC0-only"*), and the sentence *"no free bed, no free
bench, no free wardrobe. Period."* — that conclusion was true only over CC0, and the pool it was
measured on (Poly Haven 521 / Sketchfab CC0) is no longer the whole pool.

### Downstream debt this cancellation created — DECLARED, not silently left

**Two passages in `knowledge/` now rest on a cancelled premise, and `knowledge/` is READ + CITE only
(`knowledge/CLAUDE.md`) — corrections enter through `_inbox/`, never a hand-edit. Recorded here so
the debt is visible rather than fixed illegally:**

1. `knowledge/styles/style-and-asset-references-discord.md` **§3.8** — rules the 3D Warehouse /
   3dzip / 3df.pro collection links REFERENCE-tier-only, on the grounds of "budget = ฿0 … CC0-only …
   Geometry enters `assets/` only with a per-model licence verified CC0." **The grounds are gone.**
   3D Warehouse geometry may now enter, into the gitignored non-redistributable cache. The rest of
   §3.8 stands: *silence in a source is not a permission*, and a per-model licence check is still
   required — it just no longer has to return CC0.
2. **§4 (3DSKY bundles)** — its ⛔ DO-NOT-BUY/DO-NOT-INGEST call says explicitly that it *"rests on
   the studio's standing asset decision alone, and that is enough: budget ฿0 … CC0-only."*
   **That sole stated ground is cancelled.** The conclusion is very likely still right, but it must
   now be re-derived on the independent half the same section already records: the bundles are
   priced far below the rights-holder's own retail ⇒ licence **UNCLEAR / unverifiable**, and an
   unverifiable licence fails the new rule too, which asks for a licence that PERMITS commercial use.
   Until that re-derivation runs, treat §4 as **still ⛔** — a rule change is not a licence.

**Also repaired in this pass** (line-number citations into this newest-first log, which the new top
entry shifted by 55): `scripts/inbox_audit.py`, `docs/strategy.md` §F. Both were re-anchored to the
**date heading** instead of a line number, because a log that grows at the top guarantees this rot.
The four `knowledge/` citations (`:59`, `:61-62`, `:132`) are stale by the same amount and are part
of the `_inbox/` debt above. One canonical spec's `license` field was corrected in place
(`master-suite.CANONICAL.spec.json`) — the CC0 fact was true and is unchanged; only the rule
citation beside it was wrong.

## 2026-08-22 — OWNER ORDER: Blendkit Full, ONE MONTH, and the month must answer with numbers.
Owner, verbatim: *"สมัคร blenderkit 1 เดือนเลย ผมอยากจะรู้ว่ามันจะทำให้งานดีขึ้นยังไง"* (recorded in
`docs/owner-advice-2026-08-22.md` §6; order row `ORD-2026-08-22-blenderkit-one-month`; the payment +
API key are his alone — `ASK-029`). This closes the 2026-07-01 "DEFERRED — founder will decide later"
line below after 52 days, on the one-month route: the Full card's **'30 day glimpse' tab, $19.90, non-recurring**
(pricing-page markup verified the same evening; Monthly $17.90, Yearly $9.90/mo = the $118.80/yr below — the
'$9.90/mo' this repo recorded that morning was the Yearly tab the page opens on).

**What the money buys, measured before paying (public API census, 2026-08-22):** MODELS — 77% of
beds, 89% of curtains, 62-78% of every loose class P4 needs — and 62% of interior HDRIs. **It buys no
materials at all**: `asset_type:material+is_free:false` returns 0 (wood 4,864/4,864 free, fabric
5,730/5,730 free). So the two levers both critics rank first (wood-figure repeat, 'plastic' cloth
response) are not what this spend addresses, and no round may claim they are.

**How "ดีขึ้น" is decided — `D-119`, frozen before the first paid download:** C1 a full-plan whole bed
that passes `wholebed_bench`'s hard filters and the style panel (free tier baseline: 0/12); C2 ≥3 P4
loose objects in classes the free shelves measurably lack; reporting lines for critic counts, blind
RANK and wall-clock; and C3, a frame-level cut — a locked A/B pair from the record camera judged by the sighted-reader
panel and by his eye. Renewal is HIS call (R8: a spend is his per purchase): at day 30 a procurement ask is filed
with the measured numbers; if declined the tier is recorded as `searched` with numbers — the first paid tier ever
measured in this repo. Plan:
`docs/blenderkit-month-2026-08-22.md`. Fetcher: `pipeline/scripts/blenderkit.py` (proven on the free
tier with both controls the same evening). The 07-01 caveat stands: the last 10-15% is art direction.

## 2026-07-12 — OWNER DECISION: NO ASSET SPEND. The asset lever was measured and it is not the lever.
> **AMENDED 2026-08-01** — decisions 2 and 3 below are CANCELLED by the 2026-08-01 entry (the fence cancellation). The measurement
> and the refutation of the furniture-realism lever are NOT retracted and remain the reason not to
> chase assets as a score lever. Read the 2026-08-01 entry before acting on anything in this one; the 2026-08-22
> entry records the one-month trial that decision 2 had deferred.
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

## 2026-07-01 — Modern-luxury furniture pack (~~PENDING founder decision, DEFERRED~~ → **CLOSED 2026-07-12: DECLINED, see the 2026-08-01 entry (fence cancelled) and the 2026-08-22 entry (one month ordered). Its premise was refuted by measurement and its Chocofur row is factually stale. Do not act on this table.**)
Founder wants renders as beautiful as his friend's studio (PORS). The free CC0 pipeline
reaches ~70–75%; the biggest remaining lever is **modern-luxury furniture/material assets**
(Poly Haven / free CC0 has only vintage furniture, so we retint dark leather → cream boucle).

Fired Gemini DR (`research/2026-07-01-asset-sourcing-DR.md` — **dead path; the run is staged at
`knowledge/_inbox/interior-ai/2026-07-01-asset-sourcing-DR.md`**, verbatim citation added 2026-07-13)
+ **web-verified real prices/licenses**
(DR fabricates these; real money at stake). Verified options:

| Option | Price (verified) | License (verified) | Pipeline fit |
|---|---|---|---|
| **BlenderKit Full** ⭐ | $118.80/yr ($17.90/mo) | RF + CC0; **client-delivered renders = allowed commercial use** (selling the image, not the model — matches our LICENSING.md); can't resell raw models | BEST: 48k assets built into Blender as an add-on → automatable download+placement |
| **Chocofur** | ~€25/pack one-time (€8.90/model); free CC0 tier | commercial renders OK | Blender-native Cycles shaders, modern; best if one-time preferred over subscription |
| 3dsky / Dimensiva | $5–15/model (3dsky); Dimensiva ~€29/mo | royalty-free commercial | huge selection incl. exact boucle/marble/brass, but manual per-model |

*Provenance of the rows above (added 2026-07-13 — which fact came from which thread):* the free-CC0
line and the `3dsky / Dimensiva` row trace to the staged run
`knowledge/_inbox/interior-ai/2026-07-01-asset-sourcing-DR.md` — its §1 (free / CC0 sources) and §2
(paid marketplaces). **Chocofur appears nowhere in that DR**; it was added here. The price and
license columns are web-verified *overrides* of that DR, which fabricates both. Not carried by this
file at all: the DR's headline recommendation of a paid **PBR-material-library subscription** as the
primary investment (its §2 first entry + SYNTHESIS) — no successor anywhere in the repo carries that
lane, and this note is the first place its absence is written down.

**Recommendation:** BlenderKit Full ($118.80/yr) — only option that plugs into Blender (automatable).
One-time alternative: Chocofur packs (~$27).
**Status: DEFERRED — founder will decide later (2026-07-01). AI cannot purchase; needs founder go-ahead.** → approved in principle 2026-08-18 (ASK-002/ASK-028 'ลุย BlenderKit') → **ORDERED 2026-08-22, one month (ORD-2026-08-22-blenderkit-one-month; action ASK-031)**.
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
