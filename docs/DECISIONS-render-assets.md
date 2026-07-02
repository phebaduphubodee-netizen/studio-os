# INTERIOR-AI — Render asset decision log

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
