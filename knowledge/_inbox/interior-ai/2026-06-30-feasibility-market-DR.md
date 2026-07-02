# DR-001 — Feasibility / Market / Monetization Scan (2026-06-30)

Source: Claude Deep Research workflow `wf_9b185755-fe3` — 5 angles, 24 sources fetched,
112 claims → 25 verified (3-vote adversarial) → 19 confirmed / 6 killed → 9 synthesized.
Full machine output archived in the session task log.

## VERDICT: NO-GO on the original thesis · QUALIFIED-GO on a narrow wedge

**NO-GO** on "build a Claude-Code→SketchUp pipeline that auto-produces sellable production-grade
deliverables, with a token-rich moat." **QUALIFIED-GO** only on a small human-in-the-loop wedge:
AI-accelerated *rough* 3D massing/concept modeling that an actual designer (the friend) reviews,
corrects, and sells — i.e. the AI amplifies an existing practitioner; it is not a machine that
earns without one.

## Why the grand thesis is dead (high-confidence, primary-sourced)

1. **The platform owner already shipped it.** Trimble launched the official **"SketchUp Connector
   for Claude"** (Apr 28 2026) — native, per-subscriber, MCP-based, produces editable `.skp`. The
   exact pipeline the founder would build now exists first-party. *(help.sketchup.com, trimble blog — 3-0)*
2. **No AI path produces production-grade output.** Every shipping tool makes either rough editable
   3D massing OR a flat 2D concept render — **NOT** dimensioned floor plans, LayOut construction
   docs, or shop drawings. The official Connector explicitly does *not* do 2D plans / dimensioning /
   LayOut / Ruby-API, and **cannot edit an existing `.skp`** (only create new). *(3-0)*
3. **Output silently fails design intent.** Generated apartments with missing doors, unusable
   kitchens, wrong proportions; a GPT-4+LangChain CAD benchmark had 5/10 "successes" silently
   deviate from the prompt with no error. → human verifies *every* deliverable. *(arXiv 2508.00843; field tests — 3-0)*
4. **Token-moat REFUTED at the foundation.** The Connector is a native per-subscriber feature, not
   token-metered — so "token-rich runs what token-poor can't" is false at the access layer; and LLM
   inference prices fall ~50–200×/yr, so any compute edge erodes fast. *(epoch.ai; trimble — 3-0)*
5. **Legal blocker on the white-label structure.** Trimble's offering terms restrict the
   subscription to the customer's *own internal business* and prohibit using it "**on behalf of, or
   to provide any product or service to, third parties**." → white-label drafting-as-a-service is
   non-compliant unless the **designer-client holds the license** and the operator works under it
   (needs a lawyer's eye). *(sketchup.com/license; trimble offering terms — 3-0)*
6. **The viable workflow is human-in-the-loop, value = the human designer.** Independent reviews +
   CAD literature converge: raw LLM CAD output needs iterative human correction; "the tool amplifies
   skill, it doesn't replace it." → the "AI does the labor, founder just directs (zero time)"
   machine-model **does not hold for this domain.** *(3-0)*

## The favorable bits (real, but don't rescue the thesis)

- **Legal (California):** unlicensed persons *may* legally design + sign **nonstructural** interior
  alterations / fixtures / cabinetwork / FF&E — no architect stamp — but the exemption voids the
  moment work touches structure, egress, occupancy, or size thresholds (>3,000 sq ft etc.). State-
  specific; founder's operating state unconfirmed. *(BPC 5538/5536.1 — 3-0)*
- **Asset rights:** 3D Warehouse furniture/fixtures *may* be embedded in commercial work-for-hire
  deliverables (as a "Combined Work" with substantial original content); may not be resold standalone. *(3-0)*
- **The services market EXISTS:** outsourced/white-label drafting for designers is already sold
  (e.g. BluEntCAD). Indicative rates (⚠️ UNVERIFIED — from fetch-phase, did not survive to the
  verified set; treat as ballpark): 2D plans ~$100–500, 3D plans ~$200–800, full 3D ~$800–2,500+;
  ~$75–200/hr; turnaround 24–48h simple / days for full sets.

## Open questions the DR could NOT close

1. A heavily-custom Claude-Code + Ruby-API pipeline (the *actual* premise) was **never directly
   benchmarked** — evidence is on the official v1 connector + general LLM-CAD literature; failure
   modes are mechanism-level and very likely to carry, but it's an inference, not a test.
2. Real **token+human-QA cost per finished deliverable** vs a freelance drafter — unquantified.
3. Does designer-holds-the-license actually cure the Trimble third-party prohibition, or does the
   non-transferable grant still bite? (lawyer question)
4. Founder's actual **state of operation** (legal exemption is California-specific).

## So what (decision input)

The durable value is the **human designer's skill + client relationship**, not the AI pipeline —
and the founder (no time, not a designer) cannot supply that half. The honest residual options:
- **(A)** Help the friend adopt the now-free native Connector workflow as a favor / small rev-share
  — low effort, but it's the *friend's* business, not a founder income engine.
- **(B)** If the goal is still "AI service → income," redirect to a domain where the AI output is
  the *final sellable product* (no licensed-human QA required, no platform owner competing). New Q.
- **(C)** Accept NO-GO; the DCA goal is better served by job income + the deposit engine.

The expensive lesson came cheap: this DR ($0) likely saved weeks of build on something Trimble
ships natively with no moat.
