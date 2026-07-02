# DR-002 — Unit Economics (2026-06-30)

Method: the packaged deep-research workflow flaked (scope-agent structured-output cap), so this was
run as 3 controlled parallel research agents (marketplace prices / realistic AI hours / AI price
erosion) + my own synthesis. Sources cited inline. Context: model is now **founder = token+pipeline
sponsor; friend = existing clients + skill + QA/finishing; split the incremental** (founder picked
the lowest-his-time role; friend confirmed he ALREADY has clients → no marketplace cold-start).

## The decisive number: AI accelerates the workflow ~20–35%, NOT 80–90%

- Two independent sources state the same ~20–35% overall acceleration (Ravelin3D; Spline Dynamics).
  AI helps the FRONT END (concept 65–75%, materials 60–70%) but QA/artifact-correction eats most of it.
- **Client revisions: 0% AI savings** (4–8 hrs/round either way); AI can be **3–5× MORE expensive to
  revise** because you regenerate vs tweak a controllable 3D scene (e.g. "brick→limestone" ≈ $2–4k AI
  vs $400–800 traditional). (Ravelin3D)
- AI image→3D **model** output needs **2–4 hrs manual retopology cleanup** before production use
  (Datameister/Tripo, vendor-sourced ⇒ a floor not a ceiling).
- n≈800 architect/designer survey (Chaos/Architizer): 85% report gains but "incremental"; **48% cite
  poor output quality as the #1 obstacle**; gains concentrate in concept/ideation, not final deliverables.
- Confidence: MEDIUM (studio blogs + 1 survey; no raw freelancer time-tracking dataset). Directionally robust.

## Marketplace price context (we don't sell here, but it sets the ceiling on commoditized work)

- **Fiverr competitive floor (live listing prices): $10–40 per deliverable** (model / render / floor
  plan) — overwhelmingly South/SE-Asia sellers. HIGH confidence (first-party Fiverr listing-title prices).
- Upwork hourly (Upwork's own cost pages): 3D modeler median ~$25/hr; rendering ~$30/hr; archviz ~$25/hr.
- Studio rate-cards ($249–2,500/image) are NOT marketplace prices — ignore as the market.
- Regional spread ~2–3× freelancer-to-freelancer (Asia $15–35/hr vs West $40–90/hr); Thailand ≈ SE-Asia band (inferred).
- Platform fees to seller: **Fiverr flat 20%** (keep 80%); **Upwork 0–15%, ~10% typical** since May 2025.

## AI price erosion: real but concentrated at the bottom

- Academic (Demirci/Hannane/Zhu, SSRN 4602944, ~2M postings): image/graphic-design **+ 3D-modeling job
  posts fell ~17%** after AI image generators. Brookings (Upwork data): AI-exposed freelancers ~2% fewer
  contracts, **~5% lower monthly earnings**, declines growing.
- Virtual staging floor collapsed to ~$0.23/photo (AI) vs $25–75 human.
- Counter-evidence: established archviz rates **not** substantially cut; AI gains captured as speed/capacity,
  not price cuts; AI-adapted freelancers reportedly earn MORE. Squeeze is at the junior/low-end tier.
- "I use AI to go faster" is **already commoditized** among freelancers — not a durable edge.

## Honest economic sizing (founder's take)

Because the uplift is only ~20–35% and the founder's input (tokens ≈ $0, one-time pipeline) is the
commodity layer while the friend owns the value (clients + skill + labor), the founder's fair share of
the *incremental* is modest:

| Friend revenue/mo | +27% uplift | Founder share (~20%) |
|---|---|---|
| $2,000 | +$540 | ~$110/mo |
| $5,000 | +$1,375 | ~$275/mo |
| $10,000 | +$2,750 | ~$550/mo |

## VERDICT
A **low-cost, near-zero-founder-time OPTION worth ~$100–400/mo** (DCA boost ~5–25%) — **not a wealth
engine.** Good per-hour-of-founder-time (one-time build, then near-passive), bad in absolute $. Worth
doing because it's cheap + builds an AI-pipeline skill, NOT because it's big.

## The one swing factor left
Is the friend **capacity-constrained** (turns away / can't keep up with demand)? If yes → throughput
uplift = real incremental revenue (table above). If he's demand-constrained (idle capacity) → AI just
finishes faster with NO revenue gain. Also need: what % of his per-project time is SketchUp
modeling/drafting (the part AI accelerates) vs design/client work (it doesn't).

## Added findings (2nd wave — confirm the verdict, add 2 operating rules)

**"I use AI" is NOT a durable edge (skeptic-resistant).** 84% of freelancers already use AI (up from
41% in 2023); the freelancers whose edge WAS execution-speed got hurt MOST; clients pay for
judgment/relationships/outcomes, not tool-speed (Brookings/Hui 2024; Olpinski; multiple). → CONFIRMS:
the founder's token+pipeline contribution is the COMMODITY layer; the friend's clients + spatial
judgment + relationships are the durable value. Reinforces the friend-led shape (founder's share is fairly small).

**Demand is being siphoned, not just supplied.** 3D-modeling job posts −15.6%; AI-exposed freelancers
−5% earnings, and quality does NOT insulate (Hui 2024). Platforms shrinking: Upwork clients −47k in
2025, Fiverr buyers −13.6% YoY, as buyers go direct-to-AI. → HEADWIND only if the friend's clients are
marketplace-sourced; much weaker if they're direct relationships (which is the whole advantage of his existing book).

**Client reaction (most important new finding) → 2 operating rules:**
1. **Keep AI BACK-OFFICE; do NOT market "AI-made" to clients.** Peer-reviewed disclosure paradox: disclosing
   AI use LOWERS trust (Schilke & Reimann 2025); ~70% of consumers uncomfortable with AI media; authenticity
   premium for human-made. The friend delivers his normal finished work; AI is an invisible throughput tool.
2. **Interior viz has a heavy spatial-QA burden that CAPS the uplift.** A render is a "soft contract" of a
   REAL space; AI invents geometry + "styling drift" (sofa changes between angles) → unbuildable client
   expectations the designer "pays for at install." The friend must verify spatial truth on every deliverable
   → this is exactly his QA value, but it means throughput uplift for interior may run BELOW the generic
   20–35% (you can't speed past spatial QA). Treat the $ table as an UPPER bound for interior specifically.

**Net:** verdict UNCHANGED — a modest, low-founder-time option (~$100–400/mo, likely lower end for interior),
not a wealth engine. Run it risk-managed: AI stays back-office; friend does rigorous spatial QA; lean on the
friend's DIRECT clients (not the shrinking marketplaces).

## NEXT
2 friend questions, then (if green) build the pipeline:
1. **Capacity-constrained?** Does the friend turn away / can't keep up with demand (→ uplift = real money),
   or does he have idle time (→ AI just finishes faster, no revenue gain)?
2. **Time-split:** what % of a typical project is SketchUp modeling/drafting (the part AI speeds) vs
   design judgment + client work (it doesn't)? Sizes the real uplift.
Pipeline note: Trimble's native SketchUp Connector for Claude is now free-with-sub — the "pipeline" is
mostly setting the friend up with it + a funded token budget + prompt templates/automation around HIS
actual workflow, not a proprietary build.
