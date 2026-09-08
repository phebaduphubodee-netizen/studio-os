# Blendkit — the money-and-licence questions, from PRIMARY SOURCES (2026-08-23)

**TIER: REFERENCE, but a stronger grade than the DR beside it.** Every claim below was
filed with a URL and a verbatim quote, then handed to a SEPARATE agent whose instruction
was to REFUTE it by opening the cited page itself. 25 claims checked, **20 held, 5
refuted**. A claim that could not be re-opened was scored refuted, not confirmed.

WHY THIS FILE EXISTS SEPARATELY FROM THE DR: this repo's distillation ledger records the
DR lane fabricating prices and licences, and the 2026-08-23 run did it again in its
search-operator section. Licence terms decide whether a 30-day payment buys a permanent
library or a rental, so they are read from the contract, never from a summary.

## THE ANSWER TO THE LAPSE QUESTION: the licence is not the subscription

Four clauses, all from the live user Terms, settle it — and they settle it in our favour.
The decisive structural fact is that TWO SEPARATE CONTRACTS exist: the subscription
contract with the operator, which expires, and the licence contract with the CREATOR,
which is minted at the moment of download and runs for the author's copyright term.

### (c) The licence is a contract between the USER and the CREATOR, concluded at the moment of download — BlenderKit/Blendkit itself is expressly not a party to it. Therefore lapsing the vendor subscription cannot, by itself, withdraw a licence the vendor never granted.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > By pressing the "Download" button, a licence contract is concluded between you and the creator. […] Please note that we are not a contracting party of the licence contract.
- **What it changes:** This is the structural reason download-now-keep-forever works. The thing that expires (the subscription contract, Art. 3, with the operator) is a DIFFERENT contract from the thing that grants use (the licence contract, Art. 5, with the creator). A 29-day plan should therefore be treated as buying ACCESS-WINDOW, not buying rental rights: every download executed inside the window mints its own independent, separately-durable contract. Strategy: download broadly.

### (c) DECISIVE CLAUSE. The licence duration is tied to the author's copyright term, not to the subscription term. Art. 5.3.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > The licence granted by the creator under the Terms is gratuitous, non-exclusive, worldwide and unlimited in quantitative terms unless specified otherwise. The licence under the Terms is granted for the duration of the author’s property rights to the product.
- **What it changes:** This is the single sentence that answers (c). 'Duration of the author's property rights' = the copyright term (decades), explicitly NOT 'duration of your subscription'. It also says 'gratuitous' — the licence is free of charge, i.e. the subscription fee is not consideration for the licence, which is why non-payment later cannot be a breach of the licence. A 29-day plan can build a permanent library.

### (d) THE EXPLICIT STATEMENT EXISTS, and this is exactly where it is: Terms and Conditions for users, Article 2.4. Licence rights (Art. 5) are declared unchanged by subscriber status.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > You can use the interface partially (e.g. download certain products) without becoming a subscriber. These cases are always stated in the interface. Your rights and obligations arising from the Terms (in particular Articles 5 and 7 of the Terms) shall remain unchanged whether you are a subscriber or not.
- **What it changes:** This is the closest thing to a published post-lapse statement, and it is stronger than an FAQ line because it is contract text. Article 5 IS the licence article. The sentence decouples the entire licence article from subscriber status in both directions. Note the exact wording though: it is drafted about non-subscribers generally, not about ex-subscribers specifically — so cite it as 'the Terms make licence rights subscription-independent', never as 'BlenderKit says you keep assets after cancelling'. That sentence does not exist anywhere (see silences).

### (c) The ONLY published trigger that terminates the licence is the user's own violation of it. Lapse, cancellation and non-payment are not among the stated termination triggers. Art. 5.5.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > If you violate the terms of this licence, you are required to pay us and the creator in full for any damage we or the creator incur as a result, even if the product was separated from your licence without your consent or knowledge. In that case, the licence granted to you under the Terms shall terminate.
- **What it changes:** An absence test needs a positive control: the Terms DO contain a licence-termination clause, they know how to write one, and the one they wrote fires on violation only. So the silence about lapse is meaningful silence, not an oversight of drafting. The real termination risk to manage is redistribution (handing a client the model file), not the calendar.

### (c) The subscription is defined as purchasing time-boxed ACCESS AND DOWNLOAD, not time-boxed usage rights. Art. 1 definitions, and Art. 3.2/3.4.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > subscription means our service which enables you to access and download all products available in the interface for a specified time period after you purchase it
- **What it changes:** Confirms what the 29 days actually buy. Paired with Art. 3.4 — 'The number of product downloads per your subscription period is unlimited' — the plan is explicitly an unlimited-download window. There is no per-asset seat, no download quota, and no published clause converting downloaded items back to locked at expiry. The correct 29-day strategy is volume acquisition inside the window.

## THE REST OF WHAT HELD

### [limits-and-fair-use] The current user Terms (2026, the version live on the post-rebrand domain) promise UNLIMITED downloads for the subscription period. This is the contractual baseline that every technical cap below contradicts.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > The number of product downloads per your subscription period is unlimited.
- **What it changes:** If a 29-day plan gets throttled or 403'd, the studio has a contractual hook (Art. 3) to demand it be lifted or to claim under Art. 6 warranty — but only if they DOCUMENT the refusal (status code + body + timestamp). Build the fetcher to log every non-200 body verbatim from day 1; that log is the leverage.

### [limits-and-fair-use] The Terms carry an anti-script / anti-burden clause. It is written around EFFECT (burden, negatively affect operation, inconsistent with function or purpose), NOT around channel — it never says 'you may not script' outright.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > When using the interface, you may not use mechanisms, software, scripts or any other process that could negatively affect its operation, i.e. in particular, interfere with the interface or impose a disproportionate burden for the interface, or to allow third parties to tamper with or use the software or other components constituting the interface without authorization and to use the interface or its parts or software in a manner inconsistent with its function or purpose.
- **What it changes:** A 29-day plan should be designed to stay demonstrably under 'disproportionate burden': serialize the fetcher (1 concurrent request), keep a fixed inter-request delay, never run it unattended overnight. The clause is effect-based, so a slow script is defensible and a fast one is not — the rate IS the compliance argument, not the tooling.

### [limits-and-fair-use] The Terms name a PURPOSE for the database, which is the nearest thing to a restriction on stockpiling: it is meant for scene creation, not for library-building.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > The Blendkit (formerly known as BlenderKit) database is meant to be used for scene creation in Blender and other 3D content creation software.
- **What it changes:** Reframes the 29-day plan: 'download everything we might ever want' is arguably against purpose; 'download what these named rooms need' is squarely inside it. Plan the month as PER-SCENE pulls driven by real spec rows, not a class-wide harvest — same outcome for the studio, much safer posture.

### [limits-and-fair-use] Enforcement clause: BlenderKit reserves the right to restrict, suspend or terminate access with no refund, on a standard of 'unlawful or unethical behaviour' — an undefined term, not a numeric threshold.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2026/
- > If you engage in any unlawful or unethical behaviour while using the interface, we may restrict, suspend or terminate your access to the interface without compensation.
- **What it changes:** The downside of an aggressive month is losing the paid window with no refund and no notice period. That asymmetry (lose 29 days vs. save a few hours) argues for conservative pacing and for front-loading the highest-value pulls (bed, nightstand, pillow, plant) into week 1 rather than a big harvest at the end.

### [paid-vs-free-quality] The free/paid split is the CREATOR's monetisation choice, not a quality grade assigned by BlenderKit. The same creator can put one asset in Free Plan and the next in Full Plan and be paid either way.

- **OFFICIAL** — https://www.blendkit.com/become-creator/
- > Whether you choose to include your assets in Free Plan or Full Plan, revenue is guaranteed.
- **What it changes:** Kills the premise that 'paid = better model'. A 29-day plan must NOT be 'prefer Full-plan results'; it must be 'filter every candidate the same way regardless of tier, and measure whether the paid pool merely has MORE candidates passing the same filter'. The A/B they owe C3 should be filter-pass-rate per tier, not tier-vs-tier eyeballing.

### [paid-vs-free-quality] All public assets — free and paid alike — go through the same single human validation pass by a BlenderKit creator. There is no published second, stricter bar for Full-plan assets.

- **OFFICIAL** — https://www.blendkit.com/become-creator/
- > All public assets go through a validation process. One of the Blendkit experienced 3D creators will open your file and check its quality.
- **What it changes:** Their instrument, not BlenderKit's validator, is the only gate that will catch the backdrop-wall class. Budget the 29 days assuming a per-asset inspection step is mandatory on every download, including paid ones.

### [paid-vs-free-quality] Real-world scale IS an official, stated requirement: 1 Blender unit = 1 metre, scale must be applied, including on child objects, and UV scale must be real-world.

- **OFFICIAL** — https://www.blendkit.com/docs/upload/
- > Always apply scale before uploading, and in child objects wherever possible. Check also the scale of your UV's to make sure everything has real-world scaling.
- **What it changes:** Scale is the one lens dimension the platform actually governs, so a wrong-scale asset is a validation MISS and worth reporting rather than an accepted norm. Their R8 'scale is ASSERTED on every ingest' rule still stands, but they can expect a high pass rate here and should spend the 29 days' inspection budget elsewhere.

### [failure-modes] The licence you get is between YOU and the CREATOR, is concluded at the moment of download, and runs for the author's copyright term — not for the subscription term. Nothing in the Terms ties the licence's life to the plan's life. Practical reading: the 29 days are a DOWNLOAD WINDOW, not a usage window.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2021/
- > By pressing the " Download " button, a licence contract is concluded between you and the creator. […] The licence under the Terms is granted for the duration of the author’s property rights to the product.
- **What it changes:** Changes the plan's shape entirely: optimise for BREADTH OF ACQUISITION inside 29 days (download every plausible candidate for the next several projects, at the highest resolution offered), not for finishing one room. A model downloaded on day 28 is licensed forever; a model not downloaded by day 30 costs another subscription.

### [failure-modes] BlenderKit explicitly disclaims the accuracy of the MEASUREMENTS of the assets it sells. Real-world size is a creator guideline, not a warranted property of the product.

- **OFFICIAL** — https://www.blendkit.com/terms-and-conditions-2021/
- > The operator and the creator make no representations, warranties, conditions, or guarantees as to the usefulness, quality, suitability, truth, suitability for a particular purpose, non-infringement, merchantability, or visual attributes of the products, and do not guarantee the accuracy or completeness of specifications associated with the products, including measurements, materials, general physical properties, regulatory compliance, other engineering or construction attributes.
- **What it changes:** A BlenderKit model may never be treated as a dimension SOURCE — only as geometry to be measured after ingest. The existing 'scale is ASSERTED on every ingest' rule must fire on every BlenderKit asset, with the vendor's own disclaimer as its grounding, and dim_check.py must run on the imported mesh, not on the listing.

### [failure-modes] BlenderKit publishes a real-world-scale requirement to creators — '1 blender unit = 1 meter', apply scale, put it on the ground facing -Y.

- **OFFICIAL** — https://www.blendkit.com/docs/upload/
- > 1 blender unit = 1 meter. Always apply scale before uploading, and in child objects wherever possible. Check also the scale of your UV's to make sure everything has real-world scaling.
- **What it changes:** Gives a defensible expected convention (metres, grounded, -Y front) so an ingest check has a stated target to test against rather than a guess. It is the RULE; the next claim is why the rule is not enforced.

### [failure-modes] The add-on's own upload validator deliberately does NOT check that scale was applied, and its dimensions check is commented out of the code. It blocks only ASYMMETRICAL scaling. So the metre convention is enforced by a human validator's eye, never by a machine.

- **OFFICIAL** — https://raw.githubusercontent.com/BlenderKit/blenderkit/main/upload.py
- > Anything scaled away from (1,1,1) is a smaller problem. We do not check for that.
- **What it changes:** Settles the scale question as a structural fact rather than a rumour: wrong-scale assets can and do pass validation. Budget an ingest gate as MANDATORY, not as paranoia — and expect the failure mode to be uniform-but-wrong scale (a whole model at 0.8x), which is exactly the class their existing 618 mm-table negative control already catches.

### [failure-modes] Every model in the search API carries its real-world bounding box as machine-readable fields (dimensionX/Y/Z, boundBoxMin/Max X/Y/Z), uploaded by the add-on at publish time. The public search endpoint returns them WITHOUT authentication, and numeric range filters work server-side: 'asset_type:model bed' returns 1244 results, 'asset_type:model bed dimensionX_gte:1.5' returns 691.

- **OFFICIAL** — https://www.blenderkit.com/api/v1/search/?query=asset_type:model+nightstand&page_size=2
- > "dimensionX": 0.5, "dimensionY": 0.39, "dimensionZ": 0.9402, "boundBoxMinX": -0.25, "boundBoxMinY": -0.195, "boundBoxMinZ": 0.0, "boundBoxMaxX": 0.25, "boundBoxMaxY": 0.195, "boundBoxMaxZ": 0.9402
- **What it changes:** This is the single biggest lever in the 29 days. Scale stops being a post-download surprise and becomes a PRE-DOWNLOAD FILTER: query the API with the spec's slot dimensions, shortlist only assets whose bbox fits, and never spend a download on a mis-sized model. It also means a bulk acquisition sweep can be scripted and audited against the canonical spec rather than browsed by hand.

### [search-and-features] The search query grammar is a single `query=` string of `+`-joined tokens: bare tokens are free text, tokens containing a colon are filters. Everything else (`dict_parameters`, `page_size`, `addon_version`, `blender_version`, `scene_uuid`) is a normal URL parameter. Ordering is a token too: `+order:<field>`.

- **OFFICIAL** — https://github.com/BlenderKit/BlenderKit/blob/main/search.py
- > requeststring += f"+{q}:{urllib.parse.quote_plus(value)}"  ...  if requeststring.find("+order:") == -1: requeststring += "+order:" + ",".join(order)  ...  requeststring += "&dict_parameters=1"
- **What it changes:** Their current string "asset_type:model+wall+art" is already valid grammar — but it is one filter plus two fuzzy keywords. The lever is replacing the keywords with filter tokens, not tuning the keywords.

### [search-and-features] The filter terms the official add-on actually emits are: asset_type, category / category_subtree, author_id, verification_status, license, order, query, quality_gte, bookmarks_rating, files_size_gte/_lte, source_app_version_gte/_lt, modelStyle, style, condition, designYear_gte/_lte, faceCount_gte/_lte, textureResolutionMax_gte/_lte, animated, modifiers, sexualizedContent, trueHDR, mode (brushes), working_hours_count, quality_count.

- **OFFICIAL** — https://github.com/BlenderKit/BlenderKit/blob/main/search.py
- > query["faceCount_gte"] = props.search_polycount_min ... query["textureResolutionMax_gte"] = props.search_texture_resolution_min ... query["source_app_version_gte"] = ui_props.search_blender_version_min ... query["license"] = ui_props.search_license
- **What it changes:** This is the complete set the UI can reach. Anything beyond it (see the dimension claim) is reachable only by hand-built URLs — which is exactly the unused-feature gap the lens is asking about.

### [search-and-features] MEASURED LIVE: dimensional filters work on the public endpoint — `dimensionX_gte` / `dimensionX_lte` / `dimensionY_*` / `dimensionZ_*` (metres, float). category_subtree:bed = 611 results; adding +dimensionX_gte:1.5+dimensionX_lte:2.2 = 171; +dimensionX_gte:99 = 0; +dimensionZ_lte:1.0 = 304. The add-on's UI exposes NONE of these.

- **OFFICIAL** — https://www.blendkit.com/api/v1/search/?query=asset_type:model+category_subtree:bed+dimensionX_gte:1.5+dimensionX_lte:2.2&page_size=1
- > {"count":171,"next":"https://www.blendkit.com/api/v1/search/?dict_parameters=1&page=2&page_size=3&query=asset_type%3Amodel+category_subtree%3Abed+dimensionX_gte%3A1.5+dimensionX_lte%3A2.2"
- **What it changes:** This is the single biggest hit-rate lever for a studio that fails assets on SIZE. A bed frame that must sit in a 2134x1981 slot can be filtered server-side before a single download, instead of downloading, importing, measuring and rejecting. It converts their whole pick_mattress/dim_check loop from post-hoc measurement to pre-fetch selection.

## WHAT WAS REFUTED, and by what

Kept because a refutation is a finding: each of these looked like a source-backed answer
and was not. Note that most were refuted for OVERREACH rather than for a bad quote — the
page was real and the sentence was real, and the claim said more than the sentence did.

- **The Terms explicitly list APIs as a sanctioned access route to the service, alongside the add-on. There is NO clause anywhere distinguishing the official add-on from another client using the same API **
  - https://www.blendkit.com/terms-and-conditions-2026/
  - REFUTED: PARTIALLY VERIFIED, BUT REFUTED AS FILED. The quote is real, verbatim, and on the correct canonical OFFICIAL page — the claim's first half stands. Its second half does not: "There is NO clause anywhere distinguishing the official add-on from another client using the same API with a Bearer key" is a universal negative that Article 7 of the same document contradicts, and the cited sentence itself carries a qualifier the claim drops. (a) The quoted sentence sits in Article 1 DEFINITIONS AND GENERAL PROVISIONS, describing what "the interface" is — it is definitional, not a grant of access rights, and it says "APIs and other SUPPORTED integrations", immediately followed by "Additional information regarding supported platforms and integrations is available on the BlendKit website." Sanction is conditional on being supported; the Terms delegate that list off-page and are silent there on whether a self-written Bearer-key client is one. (b) Article 7 LIABILITY does constrain non-add-on clients, without ever naming them: "When using the interface, you may not use mechanisms, software, scripts or any other process that could negatively affect its operation … or to allow third parties to tamper with or use the software or other components constituting the interface without authorization and to use the interface or its parts or software in a manner inconsistent with its function or purpose." It adds a purpose limitation — "The Blendkit (formerly known as BlenderKit) database is meant to be used for scene creation in Blender and other 3D content creation software" — and an explicit enforcement notice: "To protect the integrity and proper operation of the services, the operator employs various security measures and verification mechanisms intended to prevent misuse and unauthorized activity." So "no clause anywhere" is false; what is true is the narrower, weaker finding that no clause NAMES the official add-on as the sole permitted client. This is the named failure mode: a permission conclusion inferred from a sentence about something else. The defensible replacement claim: OFFICIAL — the Terms list APIs among supported access routes (Art. 1) and never single out the official add-on, but Art. 7 forbids software/scripts used "in a manner inconsistent with its function or purpose" or "without authorization", and the Terms are SILENT on whether a self-built API client with a Bearer key counts as a "supported integration".

- **Validation is defined as subjective human inspection, with no published rubric, no numeric thresholds and no checklist. Rejection means 'serious quality issues'; on-hold means smaller fixes.**
  - https://www.blendkit.com/docs/validation-status/
  - REFUTED: REFUTED as filed, on overreach — not on the quote. The URL is genuine and official (blendkit.com is the renamed BlenderKit: footer "© 2026 Blendkit (formerly known as BlenderKit)", links to github.com/BlenderKit), I opened it, and it does contain the quoted sentence verbatim, plus "the asset has serious quality issues" for Rejected and "needs some (usually smaller) fixes" for On Hold. Those three sub-claims are confirmed. But the claim's load-bearing generalisation — "no published rubric, no numeric thresholds and no checklist" — is an absence observed on one short status-definition page and then asserted about the whole service. Two sibling OFFICIAL pages linked from that same page's nav contradict it: /docs/upload/ is literally introduced as "a list of things to check and do before uploading your model" and states a numeric threshold ("The thumbnail size should be at least 1024x1024 pixels"), and /docs/tutorials/most-common-upload-problems/ says "The validation comments that appear below your assets link to the tutorials or short explanations of these issues on this page", tying a published, named criteria index directly to validator decisions. A studio acting on this claim would conclude nothing is written down about what passes validation, when a checklist of what validators cite is published. Correct restatement: the validation-status page defines the STATUSES qualitatively and human-judged, with no score or numeric bar; published upload criteria and a common-rejection index exist elsewhere in the same docs; and on a numeric quality threshold specifically, the official sources I could reach are silent (the linked PBR specifications page 404s).

- **The rejection threshold is effort-based, not spec-based: an asset is rejected when fixing it would cost the platform too much time or exceeds the uploader's skill, not when it violates a named specifi**
  - https://www.blendkit.com/docs/tutorials/most-common-upload-problems/insufficient-quality-asset/
  - REFUTED: The page is real, OFFICIAL, and the quoted sentence is verbatim — but the claim overreaches what the text supports, on two counts.

(1) WRONG SENTENCE, WRONG SUBJECT. The time/skill language does not govern REJECTION; it governs the advice given AFTER a rejection. The full passage is: "If your asset is rejected, we may recommend you to start working on a new model. We do this when we think that fixing the asset will take too much time, or that it is (currently) beyond your skill level." The antecedent of "We do this" is "recommend you to start working on a new model", not "reject". So the time/skill test is a start-over-vs-repair recommendation, not the rejection threshold. The page never states WHY an asset gets rejected beyond its own title ("Insufficient quality of uploaded asset") and "we can't allow ourselves to accept all uploads". The claim also relocates the cost onto "the platform" ("would cost the platform too much time"); the page's context ("beyond YOUR skill level", "recommend YOU to start working on a new model") points at the uploader's time, and it is in any case unstated. Official sources are silent on a stated rejection threshold on this page.

(2) THE "NOT SPEC-BASED" HALF IS CONTRADICTED BY THE SAME DOC SET. This page is one leaf of the "Most common upload mistakes" series, whose index says: "If you upload your assets to Blendkit (formerly BlenderKit), you get focused feedback on your assets from our team. The validation comments that appear below your assets link to the tutorials or short explanations of these issues on this page." The listed issues are named specifications — "Incorrect category or style", "Incorrect UV mapping", "Put the model on the ground", "No AI Assets", "Not printable", "Authorship verification", "Texel density". A validation system whose comments deep-link to named issue articles is precisely spec-based feedback, so "not when it violates a named specification" is refuted by the platform's own docs rather than merely unsupported.

The verbatim quote checks out and the tier label OFFICIAL is correct (blendkit.com is the rebranded official domain — footer: "© 2026 Blendkit (formerly known as BlenderKit)"). What fails is the inference built on top of it.

- **There is no public BlenderKit/Blendkit API documentation: https://www.blendkit.com/api/v1/docs/ 301-redirects to a login wall, so the ONLY authoritative description of the search contract is the add-o**
  - https://www.blendkit.com/api/v1/docs/
  - REFUTED: Refuted on three independent grounds, though one component of the claim survives.

WHAT SURVIVES: /api/v1/docs/ does land on a login form. That much is true. And blendkit.com is NOT a typosquat — it is the legitimate rebranded domain (footer: "© 2026 Blendkit (formerly known as BlenderKit)").

GROUND 1 — THE QUOTE IS NOT ON THE PAGE. The cited QUOTE ("Original URL: ... — Status: 301 Moved Permanently") is a WebFetch redirect-notice string, i.e. the previous researcher's own tool plumbing, reformatted to read as a source sentence. No BlenderKit/Blendkit page contains it. Rule 4 (quote the decisive sentence verbatim) is unmet: the "evidence" is the harness talking about the fetch, not the publisher talking about the API.

GROUND 2 — THE STATUS CODE IS WRONG FOR THE CITED URL. The claim says the cited URL "301-redirects". It does not: it 302s. The 301 exists only if you start from the LEGACY domain, and it is the rebrand hop blenderkit.com -> blendkit.com — a domain move, not a docs-to-login wall. The claim welds the status code of one hop onto the semantics of a different hop. This is the exact "inferred from a sentence about something else" failure the rules of evidence name.

GROUND 3 — THE OVERREACH. "There is no public API documentation" converts "I did not log in" into "none exists". The docs are account-GATED, not absent — and this studio holds an active paid BlenderKit Full account, so the gate is one they can already pass. More decisively, "the ONLY authoritative description of the search contract is the add-on's source" is false: /api/v1/search/ answers UNAUTHENTICATED with a self-describing first-party JSON envelope. That is an official description of the search contract which is neither the walled docs page nor the GPL source.

FAIRNESS NOTE, so the refutation does not itself overreach: I checked two candidate official doc sources and neither rescues the claim's second half in the direction the claimant wanted. blendkit.com/docs/ (200, no login) covers licensing/uploading/troubleshooting but NOT the REST API; github.com/BlenderKit/blenderkit/wiki (200, named "Documentation" by the official repo) has no API or search-parameter content either. So the practical instinct behind the claim — that the add-on source is the best prose description of the search contract — is defensible. What is refuted is the stated form: the cited status code, the fabricated-looking quote, and the word "ONLY".

PRACTICAL CONSEQUENCE: the studio should not record "no API docs exist". They should record that the docs are behind an account wall their existing subscription opens, and that the live unauthenticated search endpoint is a first-party contract they can read today without credentials.

- **MEASURED LIVE: `manufacturer:` and `designer:` are filterable. category_subtree:bed + manufacturer:ikea = 23; + designer:ikea = 2. These are uploader-declared fields, and the server also stores an AI **
  - https://www.blendkit.com/api/v1/search/?query=asset_type:model+category_subtree:bed+manufacturer:ikea&page_size=1
  - REFUTED: The cited URL is reachable and OFFICIAL, and the claim's structural half is true — but the VERBATIM QUOTE is not on the cited page. The cited URL (page_size=1) returns exactly one asset, "IKEA Tarva Bed", whose validation fields read the opposite of the quote: "validatedManufacturer":true, "validatedManufacturerOutput":"Heuristics approved metadata", "validatedManufacturerActor":"heuristic". The string "Bubble" appears zero times anywhere in that query's result set (I pulled all 23 with page_size=25 and checked). The quoted sentence belongs to a different asset, "Bubble Round Soft Bed", which is not in category_subtree:bed + manufacturer:ikea at all — I found it only under a separate free-text query. So the decisive evidence was lifted from one URL and filed against another, which is the exact failure mode (quote-to-URL misattribution) these rules of evidence exist to catch; a human auditing the cited URL would not find the quote.

Two secondary overreaches: (a) the quote as filed is also edited — the real field order is validatedManufacturer, validatedManufacturerDate, validatedManufacturerOutput, validatedManufacturerActor, and the real output string continues "\nmanufacturer: Unknown|designer: Unknown", which the claim silently drops; (b) "uploader-declared fields" is an inference — the API payload says nothing about who supplies manufacturer/designer, so official sources are silent on provenance. Calling the verdict "an AI validation verdict" also generalises one actor value: observed actors are "heuristic" (22 of the 23 beds), "no_data", and "ai" — AI is one of at least three, not the mechanism.

What SURVIVES and can be re-filed with correct citations: `manufacturer:` and `designer:` are genuinely filterable and discriminate (bed+manufacturer:ikea = 23; bed+designer:ikea = 2), and the three validation fields do exist, nested under `dictParameters` (and mirrored in `parameters` as parameterType/value pairs) — the claim omits that nesting too.

## WHERE THE OFFICIAL SOURCES ARE SILENT

51 questions the finders could not answer from any official page. A silence is a
finding: it is the list of things that can only be settled by asking Blendkit support, and
it is the reason nothing here should be paraphrased into a reassurance.

- Whether a paid asset already downloaded can be RE-DOWNLOADED after the plan lapses (e.g. after a disk loss, or on a new machine). Nothing published addresses this. The server-side can_download flag decides it and the Terms only promise access 'for a specified time period', so the safe planning assumption is NO — which makes an off-machine backup of the download directory on day 29 a hard requirement, not a nicety.
- Whether the account's download HISTORY / 'my assets' listing remains visible after the plan ends. Not stated anywhere. If the studio needs a per-asset licence record (royalty_free vs cc_zero, author, asset id) for its own provenance ledger, it must capture that itself during the 29 days rather than assume the web account will still show it.
- What happens to a downloaded asset if the CREATOR later removes it from the library, or if a creator's upload is retrospectively found to infringe. Art. 5.3 ties the licence to the author's copyright term, and Art. 6 says defect claims go to the creator directly, but no clause addresses withdrawal. The local file is unaffected mechanically; the licence position is unaddressed.
- Whether the non-recurring '30 day glimpse' plan carries any terms different from the monthly/yearly Full plan. The pricing page presents it as a tab alongside Monthly and Yearly with no separate fine print, and the Terms make no distinction. Official sources are silent on any difference.
- Whether renders ALREADY DELIVERED to clients must be withdrawn on lapse. The Terms contain no express survival clause and no express withdrawal clause; the answer is derived from Art. 5.3's duration language plus the absence of any lapse-based termination trigger, not from a stated rule.
- Whether the add-on continues to function in a degraded/free mode for locally cached PAID assets after lapse — i.e. whether the asset bar will still show and re-append them. The source code shows the reuse path bypasses the server, but no documentation states the intended post-lapse behaviour, and the add-on's search UI is server-driven. Verify by testing an offline append on day 28, while the plan is still live and a failure is still fixable.
- Whether BlenderKit archives, per download, WHICH of the two licences applied at that moment. The Terms say the licence type 'is always stated in the description of the product in the interface' (a live server field), not that it is recorded to the user. Since royalty_free and cc_zero carry materially different redistribution rights, the studio must record the licence field per asset at download time or lose the ability to prove it later.
- Any published statement on what happens if the operator (Blender Kit s.r.o.) ceases trading. The licence being with the creator rather than the operator (Art. 5.1) suggests it survives, but this is inference; the Terms do not address it.
- What is the rate limit for AUTHENTICATED traffic? The official client source states only that the backend 'caps anonymous traffic at 100 requests/minute'. No official source states the ceiling for a request carrying a Bearer key, and it may be higher or lower.
- What is the exact size of the per-IP 10-second window limit? Issue #372 says a limit exists in a 10-second window and returns 429, but never gives the request count for that window.
- Does the 10,000-per-asset-type download cap reset, and on what clock? Staff said 'over 50k downloads available per month', implying monthly, but no official source states whether the counter is per calendar month, per subscription period, per rolling 30 days, or lifetime-per-plan.
- Why did Full-plan users hit 'limit of models exceeded' far below 10,000 on a one-month plan? Both issues (platform#28, #29) were closed with no public explanation, and no official source states whether short-duration plans carry a lower cap, whether resolution variants count as separate downloads, or whether it was simply a bug.
- Do the resolution variants of one asset (1K/2K/4K/blend) each consume a download against the cap? The 403 in platform#17 was triggered on a resolution_4K request, but no official source states the accounting rule.
- Are the identifying headers (Platform-Version, System-ID, Addon-Version, Client-Version, Origin-Name) required, validated, or used for rate-limit tiering by the server? The client sends them; no official source says what happens if a request carries only Authorization.
- Is there any published Acceptable Use Policy, API Terms of Service, or developer agreement separate from the user Terms and Conditions? None was found; /api/v1/docs/ is behind login and may or may not contain one.
- What conditions actually trigger account restriction under the 'unlawful or unethical behaviour' clause? The term is undefined in the Terms and no official guidance, threshold, or warning procedure is published.
- Does contacting admin@blenderkit.com for scripted/business use result in a raised cap, a written permission, a different plan, or a refusal? Staff offered the channel; no official source describes the outcome or terms of such an arrangement.
- Is there any API field, header, or endpoint that reports remaining download budget before the 403? None was found in the official add-on, the Go client, or the server-side utils — the plan cap appears to be discoverable only by hitting it.
- What happens to already-downloaded Full-plan assets when the 30-day plan lapses? The Terms grant the licence 'for the duration of the author's property rights to the product', which reads as perpetual, but no official source addresses re-download access or continued use after expiry — worth confirming in writing before the 29 days elapse.
- Does BlenderKit apply any per-day (as opposed to per-window or per-period) download ceiling? No official source mentions a daily cap in either direction.
- What happens to already-downloaded FILES after the plan ends. No official page states whether the add-on continues to serve locally cached PAID assets, whether the local cache is invalidated, or whether a previously-downloaded paid asset can be re-downloaded after expiry. The Terms' licence-duration clause strongly implies perpetual USE rights, but the Terms speak about the licence, never about the files or the add-on's behaviour. This is the single most load-bearing silence for a 29-day plan and it is why the file-level mitigations (pack resources, project subdirectory, backed-up global_dir) must be treated as mandatory rather than prudent.
- Whether the non-recurring '30 day glimpse' plan differs from the recurring Full plan in any post-expiry respect. The pricing page names the tier and lists storage quotas but says nothing about what changes at day 30. Private storage in particular (2 GiB on Full) has no stated fate — assets uploaded as private during the trial may or may not remain accessible.
- Any published technical quality standard. Official sources state no requirement or threshold for n-gons, topology, manifoldness, poly budget, shader construction, PBR compliance, or render engine on model uploads. The 'insufficient quality' page names no criteria at all.
- Any official Eevee/Cycles requirement in the model upload documentation. The only official statement on the subject is a general FAQ line about materials, not a rule creators must meet — so the 97.1%-Cycles / 0%-Eevee figure is a property of what happens to be uploaded, not of an enforced policy, and could drift.
- Any official guidance for STUDIOS on archiving, packing, or handing off scenes containing BlenderKit assets. There is no page on making a project self-contained, on what to back up, or on what a subscriber should do before a plan ends. The directory_behaviour and unpack_files preferences are documented only as tooltip strings inside the add-on source.
- Any official trade-dress or brand guidance, despite BlenderKit explicitly encouraging creators to model real branded furniture and to record the manufacturer. The Terms disclaim non-infringement and stop there; no page tells a licensee what their exposure is when a branded replica appears in a delivered client render.
- Any figure — official or community — for how often downloaded furniture must have its materials rebuilt. No source states a percentage for furniture, and no source corroborates the studio's prior 80-90% bedding figure either. The correct answer is that no source states a figure; the nearest measurable substitute is the API's own purePbr / textureResolutionMax / procedural fields, measured here at 39.2% purePbr and 35.8% sub-1K over n=800.
- Whether meshPolyType, manifold, purePbr or dimension fields can be filtered SERVER-SIDE beyond simple numeric ranges. dimensionX_gte works; meshPolyType:quad_dominant returned zero results, so the query grammar for non-numeric parameter fields is undocumented and would have to be probed. The fields are all present in the response, so client-side filtering is always available as the fallback.
- How canDownloadError is typed for a LAPSED subscriber specifically. Anonymous access returns type 'anonymous_user'; there is no documentation of the string returned when an authenticated user's plan has expired, which is the exact value a day-29 audit script would need to test for.
- Whether the engines field is reliable. It is returned inconsistently in the live data (both ['cycles'] and ['[cycles]'] appear, and 2.9% of sampled models return nothing), and nothing official describes how it is populated or validated — so it should be treated as a hint, not a guarantee.
- Whether higher texture-resolution tiers (4K / 8K) are gated behind the Full plan at all — the pricing page, the FAQ, the resolutions article, and the add-on's entire download path are all silent, and the add-on contains no plan check on resolution. The only plan gate that is visible anywhere is per-asset (access: "full").
- Any published API rate limit, requests-per-minute figure, or concurrency guidance. The Terms give only a qualitative 'disproportionate burden' test, and mention unspecified 'security measures and verification mechanisms'.
- Whether accessing assets through /api/v1/ from outside the Blender add-on is permitted, tolerated, or grounds for key revocation. The Terms acknowledge 'APIs and other supported integrations' exist but set no rules for them, and there is no public API documentation to define supported use.
- How many people or machines one subscription covers. There is no seat, team, or studio clause anywhere in the Terms, pricing page, or FAQ.
- Whether the non-recurring 30-day 'Full' plan differs in any feature from the recurring monthly or yearly Full plan. Every official page describes 'Full plan' as one thing; the duration is treated purely as a billing period.
- Whether any download quota exists. The Terms say 'unlimited'; a user-reported server error on BlenderKit's own tracker says 10,000 models; no official page mentions a limit and no staff member has replied.
- Whether 'following an author' exists as a feature. The add-on has no follow mechanism in its source — only author profiles, author_id filtering, and an asset_type:author search. Nothing official describes following.
- Whether private uploaded assets are searchable or retrievable through /api/v1/search with a key, and what happens to private assets exceeding 200 MiB when a Full subscription lapses. The FAQ gives only the storage figures.
- What the manifold, purePbr, uv, objectCount, meshPolyType and engines parameters are FOR, given they are uploaded, stored and returned but are not searchable. No official page explains the asymmetry.
- Any definition of the 'score' field used by order:-score, or of how the 1-10 quality rating is produced and moderated. Both are usable as filters/sorts with no documented semantics.
- Whether the cart / per-asset purchase path (/api/v1/cart/request-price-bulk/, isForSale, basePrice, userPrice) is a live user-facing product, what it costs, or whether such a purchase survives subscription expiry. It exists only in the add-on source.
- Official sources are SILENT on whether Full-plan models are technically better than free ones. No BlenderKit page claims higher polycount, better topology, better UVs, more complete PBR maps, or better scale accuracy for paid assets. The only stated differences are asset counts, private storage and 'extra add-ons'.
- Official sources are SILENT on extraneous geometry inside a MODEL asset. The 'most common upload problems' index lists 12 items (not printable, category/style, UV mapping, thumbnail behaviour, no AI, leaf translucency, texel density, original designs, tags, put on the ground, authorship, brush preview) and NOT ONE covers backdrop walls, studio floors, ground planes or staging props. The nearest clause is 'Models should not be libraries or collections of objects', which is about collections, not scene furniture. The 2,759 mm backdrop-wall case has no rule that plainly forbids it.
- Official sources are SILENT on whether an asset must arrive as separated parts or may be one fused mesh. No upload rule, no validation criterion, no API field addresses part separation.
- Official sources are SILENT on any numeric quality standard: no polygon-count limit or floor, no required PBR map set (base colour / roughness / normal / etc.), no texture-resolution minimum for models, no n-gon or quad requirement, no UV-overlap or texel-density number. The texel-density page teaches consistency without giving a single figure.
- No published validator rubric or checklist exists. Validation is described only as 'somebody looks at your upload'. There is no way to know what a validator actually checked on any given asset.
- Official sources are SILENT on what happens to already-downloaded assets when a subscription expires. The FAQ does not address it and the Terms only say the licence is 'granted for the duration of the author's property rights to the product'. Perpetuity is implied, never stated. This is the single most decisive unknown for a 29-day non-recurring plan and should be asked of support in writing.
- Official sources are SILENT on whether the free and paid pools are validated by the same people, at the same time, or with the same throughput — only that 'all public assets' go through 'a' validation process.
- Official sources are SILENT on whether the faceCount / 'Polygon count' metadata is verified at validation. An observed Full-plan scene asset of 357 MiB reports 'Polygon count 1', so the field the API filter reads can be wrong, and nothing documents how or when it is populated.
- Official sources are SILENT on whether lower-resolution texture variants are generated for ALL assets or only some, and on the exact resolution ladder (only '1k' is given as an example).
- COMMUNITY sources are SILENT too: no side-by-side technical comparison of free-tier versus Full-plan BlenderKit models — polycount, UV, map completeness, part separation — appears to exist anywhere public. Every 'is it worth it' source argues from asset COUNT. If the studio wants that comparison it will have to run and publish it itself; there is no prior art to lean on, and any claim that 'people report paid models are cleaner' would be fabrication.

## THE SYNTHESIS — what to do with 29 days

Written from the survivors only; inference is marked as inference in the text.

## A. THE LAPSE ANSWER

**The lapse question is not silent — it is answered, and answered in the studio's favour.** Four clauses, all OFFICIAL, all on https://www.blendkit.com/terms-and-conditions-2026/ (mirrored in the 2021 version):

- The licence is between **you and the creator**, concluded at download: *"By pressing the \"Download\" button, a licence contract is concluded between you and the creator. […] Please note that we are not a contracting party of the licence contract."*
- Its term is the **author's copyright term**, not the plan's: *"The licence under the Terms is granted for the duration of the author's property rights to the product."* (Art. 5.3)
- Subscriber status is explicitly irrelevant to it: *"Your rights and obligations arising from the Terms (in particular Articles 5 and 7 of the Terms) shall remain unchanged whether you are a subscriber or not."* (Art. 2.4)
- The **only published termination trigger is your own violation**: *"If you violate the terms of this licence […] the licence granted to you under the Terms shall terminate."* (Art. 5.5) Lapse, cancellation and non-payment are not among them.
- And the subscription is defined as time-boxed access: *"subscription means our service which enables you to access and download all products available in the interface for a specified time period after you purchase it."*

**Therefore the strategy assumes: 29 days is a DOWNLOAD window, not a usage window.** Anything on local disk before day 30 is licensed for the author's copyright term and ships in client work after lapse.

**Where the silence actually is** — and it bears on *how* you download, not *whether* you keep:
1. Art. 1 lists APIs among supported integrations but delegates the list of supported integrations off-page; official sources are **silent** on whether a self-built Bearer-key client is one.
2. Art. 7 constrains by **effect, not channel**: *"you may not use mechanisms, software, scripts or any other process that could negatively affect its operation […] or to use the interface or its parts or software in a manner inconsistent with its function or purpose."* No numeric rate or volume threshold is published anywhere.
3. The nearest published anti-stockpiling rule is a purpose statement: *"The Blendkit (formerly known as BlenderKit) database is meant to be used for scene creation in Blender and other 3D content creation software."*
4. Enforcement runs on an undefined standard: *"If you engage in any unlawful or unethical behaviour while using the interface, we may restrict, suspend or terminate your access to the interface without compensation."*
5. The Terms promise *"The number of product downloads per your subscription period is unlimited."* — a contractual baseline that any technical cap contradicts.

**Cost of the conservative reading** (inference): if you instead assumed licences die at lapse, you would owe rent on every delivered scene containing a BlenderKit asset, forever. The Terms do not support that reading; adopting it would be paying to avoid a risk the publisher has already disclaimed in writing.

## B. THE ACQUISITION ORDER

**Skip materials entirely.** Free = Full (37,912). They need no month, no urgency, no slot in this plan.

**1. Enumerate before you download — days 1–2, costs nothing, needs no subscription.** The public search endpoint answers **unauthenticated** and carries every model's real-world bounding box as machine-readable fields (`dimensionX/Y/Z`, `boundBoxMin/MaxX/Y/Z`), with **server-side numeric range filters**: `category_subtree:bed` = 611; `+dimensionX_gte:1.5+dimensionX_lte:2.2` = 171; `+dimensionZ_lte:1.0` = 304. Grammar: one `query=` string of `+`-joined tokens, colon = filter, plus `&dict_parameters=1`. The add-on's UI exposes **none** of these dimension filters. Shortlist by the dimension your slot actually requires, never by thumbnail.
`manufacturer:` and `designer:` also discriminate (bed+`manufacturer:ikea` = 23) — this survives only as the re-verified remnant of a refuted claim; treat as usable, lightly held.

**2. Download in blocked-lane order, not category order.** Priority by (paid-share × current frame need): bed 77%, pillow 76%, nightstand 69% first — the classes the lane is stopped on — then books 68%, mirror 62%, plant 77%, then clothes hanger 83% / shirt 95% only if a frame calls for them. A download can only be judged in a frame, and you have 29 days of judging.

**3. Take 3–5 candidates per slot, not one** (inference from two survivors): paid is **not** a quality grade — *"Whether you choose to include your assets in Free Plan or Full Plan, revenue is guaranteed"* — and all public assets pass **one** human validation pass with no published stricter bar for Full. A wrong pick discovered on day 40 cannot be replaced. Redundancy is the thing the window actually buys.

**4. Assert scale on every ingest, locally.** BlenderKit publishes *"1 blender unit = 1 meter. Always apply scale before uploading"*, but its own uploader deliberately does not enforce it — *"Anything scaled away from (1,1,1) is a smaller problem. We do not check for that."* — the dimensions check is commented out, and the Terms disclaim measurement accuracy outright: *"[we] do not guarantee the accuracy or completeness of specifications associated with the products, including measurements."* Metadata is a search key, never a spec.

**5. Channel discipline** (inference from the Art. 1 silence + Art. 7 effect test): enumerate over the unauthenticated public endpoint freely; run the **authenticated downloads through the official add-on** where practical, serial and throttled. Download against **named slots in named scenes**, which is both what the purpose clause describes and what makes the haul useful.

**6. Record at download time**: asset id, fileId, creator, licence field (`royalty_free` vs `cc_zero`), date. The contract is with the creator and is formed at download — the date and creator identity *are* the evidence.

**7. HDRI last**, and only the specific ones a planned shot needs (partial paywall, low count relative to models).

## C. WASTED EFFORT

- **Downloading materials.** Free = Full. Any minute spent here is a minute the month did not need.
- **Mirroring a whole category because it is paid.** Contradicts the stated database purpose, and puts you under an undefined *"unlawful or unethical"* standard with no published numeric safe harbour and no compensation on termination.
- **Skipping free assets in a paid-heavy class.** The split is the creator's monetisation choice; the validation pass is the same one. Free/paid predicts nothing about whether it renders.
- **Trusting `dimensionX` as a dimension.** Disclaimed contractually, unenforced technically.
- **Building tooling on the search API during the month.** That endpoint is unauthenticated and permanent — it is any-time work. Doing it inside the window burns the window.
- **Hunting for "the missing API docs."** They are account-gated, not absent; the active paid account already opens `/api/v1/docs/` (this is the correct remnant of a refuted claim — mark as such).
- **Chasing a numeric validation/quality threshold.** Official sources are silent; the linked PBR specification page 404s.

## D. OPEN QUESTIONS

**(i) Ask a practitioner** — cheaper and more accurate than any further reading:
- Do working archviz studios ship BlenderKit models in delivered client scenes, or use them as blockout only?
- Real hit rate: candidates downloaded per slot before one ships?
- For residential interiors, does BlenderKit actually displace 3D Warehouse, or sit beside it?
- Is re-topology / re-material standard practice on a bought model, and what does it cost per asset?
- Has anyone renewed a second month, and what did the second month buy that the first did not?

**(ii) Only BlenderKit support can answer:**
- Is a self-built client using the documented API with a Bearer key a "supported integration" under Art. 1? (Terms are silent; Art. 7 constrains by effect.)
- Is there a rate or volume limit, and what is the number? The Terms say unlimited; get any technical cap named in writing.
- Does downloading against a planned slot library, rather than an open Blender scene, fall outside *"meant to be used for scene creation"*?
- After lapse: does download history persist, and can a previously downloaded file/resolution variant be re-fetched?
- Confirm Art. 2.4 / 5.3 in writing for a lapsed account — one support reply makes the whole plan auditable.

## E. THE COUNTER-CASE (stated so it can be tested)

**The strongest honest argument that this month will not pay for itself:** the paywall is a monetisation boundary, not a quality boundary — BlenderKit says so itself — so the month bought *convenience of selection*, not *access to better geometry*, and most of the selection machinery was never behind the wall.

Four tests, each capable of refuting the spend:

1. **Paid-vs-free blind test.** For each blocked class, run the same dimension filters restricted to free assets, render the best free candidate beside the best paid one, unlabelled, and let the owner's eye pick. If free wins or ties in a class, the month is refuted **for that class**.
2. **Time-to-accepted.** Log wall-clock from download to in-frame-accepted for the first five paid assets. If the median exceeds the studio's own build time for the same class, acquisition saved nothing — the disclaimed measurements and unenforced scale are the mechanism.
3. **Renewal test at day 29.** Count slots filled by paid downloads vs slots still open. If the stock covers the lane, renewal is refuted; if it does not, this month under-bought and the plan (not the vendor) is at fault.
4. **Paywall-attribution test.** Measure what fraction of the month's usable output came from the unauthenticated search/shortlist work vs from files that required the Bearer key. If the former dominates, the money bought a capability the studio already had for free.

Any one of these coming back negative is a finding, not a failure — and test 1 is the one to run first, because it is cheap and it decides the other three.
