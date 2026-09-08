# DR RESULT — sourcing buyable Thai furniture/fixtures for a client BOM (2026-07-11)

**Method:** `deep-research` harness — 6 angles → 22 sources fetched → 91 claims → 25 verified by
3-vote adversarial panel → 17 confirmed / 8 refuted. 105 agents. Retargeted from the (proxy)
auto-read topic per the 2026-07-10 self-critique. **Privacy:** generic Thai-market queries only, no
client/project data.

## Headline — the DR empirically validated OUR owner-signed law, for sourcing too

No matching method is accurate enough to auto-pick a product: the best domain-tuned vision model gets
**~58% top-1 / 74% top-5** (furniture slice 65.8 / 83.8 — still wrong ~1/3 at top-1). And reliable
match SELECTION requires a **trained/calibrated human (89.5% accuracy)** vs a naive crowd
(**32.5%**, Pinterest Shop-The-Look KDD 2020). → the correct design is **machine proposes a ranked
top-5 buyable shortlist → the owner (trained reviewer) signs**. This is the SAME two-layer pattern as
walls→glazing→furniture, now confirmed for sourcing. Sourcing is NOT a full-auto problem; it is
candidate-generation + owner-signature.

## (a) Ranked Thai sources — what each exposes (VERIFIED)

| source | dimensions | price | stock | how queryable | verdict |
|---|---|---|---|---|---|
| **Index Living Mall** | **W×D×H on product page** (e.g. Miley sofa 288×117×82 ซม.) | THB, same page (promo) | — | scrape PRODUCT-DETAIL page (NOT category cards — those show only name/price) | **BEST primary source** |
| **HomePro** | inconsistent, embedded in product NAME (`120 ซม.`) | per tile (sale + original) | per tile (สินค้าหมด) | scrape tiles for price/stock; product-page spec table for dims; no feed | good price/stock, weak dims |
| **Lazada / Shopee** | **none** (scraper/affiliate schemas carry no dimension field) | yes | partial | Shopee affiliate actor is **Brazil-region**; official API partner-gated + seller-OAuth | price/availability cross-check ONLY, not a dimension source |

Caveat: only these 4 were verified. **SB Design Square, Koncept, IKEA Thailand, Boonthavorn,
Modernform, Winner were NOT checked — IKEA TH likely exposes structured dims + article numbers and
should be verified before finalizing** (open question).

## (b) Matching method (VERIFIED)

- **Architecture:** two-stage multimodal (image+text) embedding — embed the query (render look-image
  + spec text) → vector NN retrieve candidates → finer rerank. Maps directly onto "propose candidates".
- **Current default = CLIP-style vision-language embeddings** (the 2018 ResNet-50+word2vec "DeepStyle"
  is illustrative, dated — do NOT build on it).
- **Accuracy → shortlist, never auto-pick:** ~58% top-1 / 74% top-5 general; ~66/84 furniture. Human
  reviewer must be TRAINED (89.5% vs 32.5% naive). **REFUTED:** the "+21%/+32% multimodal beats
  visual", the 4-stage CLIP+LLM-reranker pipeline, and a furniture-specific 65.8-vs-57.4 figure did
  NOT survive — don't cite them.

## (c) Freshness (VERIFIED)

Anchor each BOM item to a **canonical manufacturer/retailer key** (GTIN/MPN/Brand per Google Merchant
Center), not a rot-prone URL. Two hard limits: Thai furniture **GTIN coverage is likely LOW** → use a
composite fallback key (retailer SKU + brand + model + captured dims); and **cross-retailer ID
portability was REFUTED** — a GTIN does NOT re-find an item at a different retailer → freshness must be
**per-source re-validation cadence + owner-approved alternates**, not assumed portability. Prices are
promotional snapshots (Index runs frequent promos; a HomePro SKU already rotated mid-research) → capture
is never one-time.

## (d) Scoping — CONFIRMED, and it shrinks the sourcing target

**Built-in joinery = custom-FABRICATED (MADE, excluded from FF&E); only loose furniture + fixtures are
externally sourced.** So the studio's `BF##` built-ins (wardrobes, headboards, media walls) are NOT
sourced — they are fabricated by the workshop. Sourcing targets ONLY: loose (bed, mattress, sofa,
chairs, lighting, rugs) + fixtures (tub, toilet, vanity, faucets). Nuance: MOVABLE cabinetry IS FF&E;
only FIXED joinery is excluded. **Open:** no quantitative loose-vs-built-in fraction was established.

## Integration plan → `ffe-research` pipeline (ffe-candidates catalog)

1. **Scope filter first:** partition the spec — `BF##`/fixed joinery → `fabricated` (skip sourcing,
   route to workshop BOM); loose + fixtures → `sourceable` queue. (Cashes the scoping finding + the
   built-in reality we already saw in v5.)
2. **Candidate generation:** for each sourceable item, scrape **Index Living Mall product-detail pages**
   (primary, dim+price) + HomePro product pages (fixtures/price); build a small dim-bearing catalog.
   Match render-look + spec (type/dims/style/budget) via a CLIP-style embedding → **top-5 ranked
   candidates** by dim/style/budget fit.
3. **Owner-signature gate (the load-bearing step):** present the top-5 to the owner to SELECT — mirror
   `placement_gate` / the thin-glass `OWNER-CONFIRM-PENDING` pattern; an unsigned candidate is
   machine-inert (never enters the client BOM). Wire into the existing `sourceability_gate` +
   `ffe_tag` ([[sourceability-first]]).
4. **Freshness:** store the composite canonical key (SKU+brand+model+dims) + captured price/date;
   re-validate on a cadence; flag rot → owner-approved alternate.

## What's NOT settled (open questions for a follow-up, do not assume)

IKEA TH + SB/Modernform/Koncept/Boonthavorn/Winner catalog structure; the quantitative
sourceable-vs-fabricated fraction (sizes the pipeline); the right re-validation cadence + composite-key
stability; and how a 2026 CLIP model matches OUR render look-images to Thai catalog products
specifically (only general-domain vendor benchmarks survived).

**Sources (primary):** Index product page, HomePro category, Lazada/Shopee API docs, arXiv 2006.10866
/ nyris benchmark / Pinterest KDD 2020, Google Merchant Center docs, BAREO (built-in vs loose). Full
verified/refuted list + votes in the workflow journal.

---

## TRACER RESULT (de-risk before build, 2026-07-11) — the matcher is already built; freshness is the gap

Ran a bounded de-risking tracer on the EXISTING `ffe-candidates.json` (24 items, ffe-research skill,
researched 2026-07-04) instead of building blind. Two findings changed the integration plan:

1. **Matching is already solved — do NOT build a CLIP matcher.** `ffe-candidates.json` already
   implements the DR's recommended pattern: each role has `target_dims_mm` → multiple real Thai-market
   candidates ranked by dimensional fit (±15% tolerance) → a `selected` pick with `verified:false`
   (designer signs off). It even already tags built-ins (`csi 06 41 00`, "fabrication") vs loose
   (`csi 12 5x 00`). So the DR's "candidate generation" is done via dimension retrieval — the reliable
   channel — and the visual-CLIP step (the ~58% unreliable one) is not needed for the plan-derived spec.

2. **Freshness re-fetch (07-04 → 07-11, one week) confirms the DR's freshness thesis empirically:**

   | item | dims then→now | price then→now | canonical key |
   |---|---|---|---|
   | IKEA BRIMNES | 39×41×53 → **same** | 1,990 → **1,990** | article 003.540.63 |
   | IKEA MALM | 196×209 → **same** | 8,090 → **8,090** | article 302.494.76 |
   | Index Serine | 220×208.8×110 → **same** | 19,800 → **19,850** (promo moved) | SKU 110047607 |

   → **dimensions are STABLE (the reliable match anchor); prices DRIFT** (Index +50 THB in a week,
   IKEA stable — IKEA is less promo-driven). **Canonical keys exist** (IKEA article #, Index SKU) =
   the DR's recommended freshness anchor is implementable. **Stock caveat:** IKEA renders stock via JS
   ("Checking availability…" not in static HTML) → not statically scrapable; Index exposes stock text
   ("มีสินค้าพร้อมส่ง"). So a freshness pass can re-validate price by canonical key but stock only where
   the source serves it statically.

### Reframed integration (evidence-based) — build these, NOT a matcher

- **(a) Partition gate:** formally split `fabricated` (BF##/built-ins, csi 06/09 → workshop BOM, skip
  external sourcing) vs `sourceable` (loose + fixtures) — the ffe already tags it; make it a gate.
- **(b) Freshness re-validation:** re-fetch each SELECTED candidate by canonical key (article#/SKU),
  update price + stock, FLAG drift (price moved / out-of-stock / dims changed = wrong SKU). Dims stable
  → a dim mismatch on re-fetch means the link rotted to a different product.
- **(c) Owner-sign gate:** `verified:false` → owner confirms live price+SKU → `verified:true`; wire to
  the existing `sourceability_gate` + `ffe_tag` (the machine-proposes / owner-signs pattern the DR and
  every other layer share).

Load-bearing caveat: this tracer used WebFetch (agent tool). A standalone re-validation script needs
its own HTTP fetch (curl/urllib per [[machine-constraints]]); IKEA JS-stock will need the product API
endpoint, not the HTML — a build detail to resolve.
