# 2026-08-08 — the whole DR queue, fired

**Owner order:** *"งานคุณห่วยมาก ๆ ในตอนนี้ / ใช้ nlm DR, gemini DR ให้หมดเพื่อ upgrade ซะ"*

The repo already held a triaged DR agenda — `docs/research/2026-08-04-dr-queue-triage.md`,
six topics with sharpened question sets and fire conditions. TRN-002 is past the
blockout→materials→light transition, which is the fire condition on topics 1–4.
This run fires those, plus three the queue did not have and this lane's own
unpaid triage debt names in its own words.

## What fired

| # | Question | Channel | Grounded? |
|---|---|---|---|
| q1 | CG-tells: edges, shading, silhouette, contact, surface variation | Gemini ×2 + **NLM DR** | Gemini refused to search **twice**; NLM DR answered from AWI standards |
| q2 | Glass / transmission / mirrors in Cycles | Gemini | 33 sources |
| q3 | Palette anchors — Thai paint LRV, oak, powder coat, brass | Gemini + **NLM DR** | 21 sources |
| q4 | Bedding mass / drape feedstock | Gemini + **NLM DR** | 13 sources |
| q5 | Hero-shot lighting practice | Gemini + **NLM ask** `79476082` | 8 sources |
| q6 | Camera language of interior photography | Gemini | 33 sources |
| q7 | Junctions and joinery setting-out | Gemini | 22 sources |
| q8 | Photo-match + how a match is scored | Gemini + **direct paper fetch** | 27 sources + primary |
| q9 | Inspection blindness / habituation | Gemini | 31 sources |
| q10 | Asset acquisition and ingest pipeline | Gemini | 32 sources |
| — | Photographer / light-story / camera | **NLM ask** `a5a43395` | corpus |

Every prompt is archived in `prompts/`. Every answer is archived beside it with
its vendor grounding metadata in a `.grounding.json` sidecar.

## The finding that changes how this repo does research at all

**A 32k thinking budget silences the search tool.** Measured, same prompt, same
system instruction, back to back:

| mode | construction | searches issued | sources returned |
|---|---|---|---|
| `pro` | `google_search` | **58** | **21** |
| `deep` | `google_search` + `thinking_budget=32768` | **0** | **0** |

Nine of the first ten calls this session came back that way. They are not empty —
they are long, confident, and cite manufacturers and standards **by name**, which
makes them read as *more* authoritative than the grounded answers that say
"NO SOURCED VALUE FOUND". A mode named `deep` was the shallowest thing here.

This is not local to one script. `BRAINDEAD/scripts/gemini_query.py --deep` is
built the same way — search tool plus a 32k thinking budget — so every call
labelled Deep Research through that path is suspect for the same reason. **That
is a cross-repo finding and the sibling repo's research record should be
re-read with it in hand.**

Fixed structurally, not by memory: `pipeline/scripts/research_call.py` carries no
thinking budget at all, states why in the code, and stamps **UNGROUNDED — the
vendor reported ZERO retrieved sources** at the top of any answer whose grounding
came back empty. The warning lands where a reader lands.

## Two more ways an answer can look sourced without being sourced

Both were found the same morning, in the other channel, and neither is visible
from reading the answer — only from asking the vendor what the source IS.
`pipeline/scripts/nlm_provenance.py <notebook>` now does that in one command.

**(2) Every NotebookLM Deep Research adds its OWN report as a citable source.**
Typed `MARKDOWN`, `url: null`, titled like a paper. All three DRs fired today did
it, and in all three it became the **most-cited source in the answer**:

| notebook | synthesised source | what cited it |
|---|---|---|
| craft | *"Computational Aesthetics and Perceptual Mechanics…"* | the whole segment table, the shading mechanics |
| bedding | *"Physical and Computational Modeling of Bedding Systems…"* | the settled-loft-in-millimetres column |
| palette | *"Quantitative Modeling of Cream, White Oak, and Black…"* | every LRV/sRGB pair |

It cites in exactly the format it cites a manufacturer datasheet in. The craft
answer put an AWI citation and a synthesis citation **in the same sentence**, and
the two numbers I trusted most from the whole run — a 3.2 mm eased radius and a
1.6 mm square edge — turned out to be in the synthesis and **not in AWI**. Caught
only by pulling the AWI text and grepping it.

**(3) The `a5a43395` "Design Systems" corpus contains our own documents.**
Asked about the light story of an interior photograph, it answered by citing
`Automated Vision QA for Interiors.pdf` and `Knowledge Base Architecture for a
World-Class AI Interior Design Studio Powered by Claude Code`. The audit:
**103 retrievable / 1 synthesised / 11 uploaded**, and all eleven uploads are our
own AI-studio material.

CLAUDE.md's research doctrine — *vault first, NLM fires on vault GAPS* — assumes
the notebook is EXTERNAL to the vault. For this corpus it partly is not, so it
can return our own beliefs to us as grounding. That is the flattering-scorer
failure this repo has already pinned nine shapes of, arriving in the research
lane. **Every value previously staged out of `a5a43395` needs re-checking against
which sources it cited** — that is a separate audit, not done here.

## The fabrication, caught in the act

The un-searched q8 answer described the SEIG paper's staged verifier with
specific numbers: *"a fixed budget of 3 rounds of correction"*, *"3D IoU of 0.42
versus 0.28, a 50% improvement"*, authors *"K. Ling, K. Rempe"*.

The paper was then fetched directly (arXiv 2606.02580):

| claim | fetched from the paper |
|---|---|
| 3 rounds per phase | **geometry 5, material 3, composition 3, lighting 2** |
| 3D IoU 0.42 vs 0.28 | no 3D IoU anywhere — **PSNR/SSIM/LPIPS/DreamSim/DINO/CLIP**; PSNR 13.58 vs 12.33 |
| "K. Ling, K. Rempe" | **Guangzhao He, Rundong Luo, Wei-Chiu Ma, Hadar Averbuch-Elor** (Cornell) |

Every one of those numbers was plausible. That is the whole problem with the
class, and it is why the URL-or-quarantine rule is written the way it is.

## Claims refuted here by local measurement, not by taste (R7)

1. **"Set Transmission Roughness for frosted glass"** (q2, grounded, sourced) —
   REFUTED. The Principled BSDF in the Blender this repo actually runs (**5.1.2**)
   has no such socket; probed live, the full socket list is in the triage notes.
   The frosted lobe comes off `Roughness` itself. A grounded answer can still be
   wrong for THIS machine, and the version it was written for is the tell: most
   returned advice says "Blender 4.x" and this lane is two majors past it.
2. **"Round budget of 3 per phase"** (q8, ungrounded) — REFUTED by the paper.

## What was built, because research that changes nothing is a reading list

| file | what it does | tests |
|---|---|---|
| `pipeline/scripts/coverage_check.py` | the MISSING-object half of R10 — which object the reference shows has no mass in our scene. Ratcheted allowed-absence list. | 15 |
| `pipeline/scripts/craft_check.py` | silhouette segment floor from the 1-arcmin acuity limit — the first craft property in this lane that is a number | 13 |
| `pipeline/scripts/nlm_provenance.py` | splits a notebook's sources into retrievable / synthesised / uploaded — findings (2) and (3) above become one command | — |
| `pipeline/scripts/research_call.py` | grounded Gemini research with RULE ZERO, no thinking budget, and an UNGROUNDED stamp | — |
| `training/TRN-002/coverage-manifest.json` | v1 manifest assembled from this lane's own gates | — |

First runs against `spec_r31`, both finding real things:
**coverage** — 5 ABSENT, 5 BUILT, **7 UNCOVERED** (mirror, wall-floor junction,
garments, closet shelf, LED strip, far room, etagere objects — every one already
written down in a gate, none of them counted by anything until now).
**silhouette** — 13 of 16 rounded masses pass, **3 fail** (`petcave` 6 vs 9,
`bed_platform` 6 vs 8, `bench` 6 vs 8). That also corrects a claim in our own
source code, which says every arc in the frame renders as visible facets.

## Spend

- Gemini: 10 ungrounded first-pass + 12 grounded (10 re-fires + 2 probes) + 1 retry + 1 verification = **24 text calls**, `gemini-2.5-pro`
- NotebookLM: **3 fresh-notebook Deep Researches** (104 / 139 / 113 sources) **+ 2 asks against existing corpora** — 5 of the ≤10 ask budget
- Direct fetch: 2 (arXiv SEIG) + 2 source-fulltext pulls (Rademacher EGRW 2001, AWI 3.4)
- Blender probe: 1 (`--factory-startup`, socket enumeration)

## Where the answers go

Nothing here is domain truth. This directory is REFERENCE tier and un-distilled.
Values enter `knowledge/` only through `_inbox/` staging with attribution, and a
number whose source is a name rather than a retrievable page stays quarantined —
the two entries in the table above are why.
