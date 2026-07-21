# STUDIO-OS — Definitive Implementation Blueprint
## A World-Class AI Interior Design Studio Powered by Claude Code

**Version 1.0 · July 2026 · Synthesized from 11 research reports (ID Project corpus)**

Source corpus: *Claude Code Architecture Design · AI Design Studio Architecture · AI Context Engineering Architecture · AI Design Knowledge Systems · Interior Design Knowledge Structuring · AI Image Prompt Engineering · AI Interior Design Commercial Workflow · AI Studio Workflow Automation · Automated Vision QA for Interiors · Automated Production QA Scoring Systems · Large Scale Project Organization*

---

## 0. Executive Summary and Governing Principles

This blueprint defines a single, coherent operating system — **STUDIO-OS** — for a production interior design studio in which Claude Code is the central orchestrator, the filesystem is the state machine, deterministic guardrails contain probabilistic generation, and every rendered pixel passes through a measurable quality gate before a client ever sees it. It is designed to be operated by a single principal designer today (Thai residential: condos, single houses, townhomes; SketchUp / AutoCAD / 3ds Max / V-Ray / Photoshop as the existing geometry and finishing stack) and to scale to a multi-seat commercial product without re-architecture. The existing `studio-vault` (v2.2) is not discarded — it becomes the seed of the Knowledge Layer, and its Source-and-Truth Hierarchy is formalized into the Authority tier of the context system.

Seven principles govern every decision in this document. They are the reconciled consensus of the eleven reports:

1. **Deterministic guardrails for non-deterministic agents.** Security and physics are never enforced by prompts. Natural-language rules in CLAUDE.md are advisory; hooks, permission arrays, schema validation, and geometric/colorimetric math are law. Prompt-based security is an anti-pattern that fails under context pressure and injection.
2. **The context window is RAM, not a database.** The LLM is a stateless CPU; the window is scarce, volatile working memory subject to lost-in-the-middle recall decay and context rot. Everything is engineered around progressive disclosure, layered memory, compaction, and subagent isolation. [src: `knowledge/_inbox/id-project-corpus/AI Context Engineering Architecture.pdf`]
3. **The filesystem is the architecture.** Numbered stage directories with local contracts (Interpretable Context Methodology) replace framework-level orchestration for sequential design work. One stage, one job, one auditable artifact. Every intermediate output is a human-editable surface. [src: `knowledge/_inbox/id-project-corpus/AI Context Engineering Architecture.pdf`]
4. **Semantics reason, symbols verify.** The LLM handles creative intent; deterministic engines (scene-graph clearance checks, PBR range validation, homography factorization, ΔE00 colorimetry) verify physical and brand reality. AI never "guesses" whether a sofa fits — geometry answers that.
5. **Generation is cheap; evaluation is the bottleneck.** The studio's throughput is gated by QA, so QA is automated first-class infrastructure: a nine-pillar scoring system with hard/soft gates wired into the pipeline, and a closed vision-feedback loop that repairs failures before humans review anything.
6. **Match the tool to the phase.** No single image model wins. Midjourney/Gemini for emotional concept work, CAD + ComfyUI + FLUX + ControlNet for structurally faithful production, Ideogram/Recraft for typography and brand, Magnific/SUPIR for delivery-grade resolution. V-Ray remains the ground-truth renderer for construction-document-grade finals. [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`]
7. **Everything is versioned like code.** Prompts, agents, skills, QA thresholds, ComfyUI graphs, MaterialX definitions, and USD scenes live in Git (with LFS for binaries), promoted through dev → staging → production labels, and rolled back like software.

---

## 1. Overall Architecture

### 1.1 The selected paradigm: Hybrid Hierarchical Monorepo + Filesystem State Machine

Of the three deployment paradigms evaluated (decentralized CLI, centralized Agent SDK, hybrid monorepo), STUDIO-OS adopts the **Hybrid Hierarchical Monorepo**: a single repository combining Claude Code CLI operation for the designer with SDK-embedded automation for headless routines, organized so the agent discovers configuration, rules, skills, and knowledge exactly when needed rather than at session start.

Layered on top is the **Interpretable Context Methodology (ICM)**: each client project is a directory of numbered pipeline stages, each stage carrying a local `_contract.md` that defines inputs, process, and required outputs. The agent's "geographic location" in the tree determines its context. This physically eliminates cross-stage context poisoning and makes every intermediate artifact reviewable and editable by the human designer before the next stage runs. [src: `knowledge/_inbox/id-project-corpus/AI Context Engineering Architecture.pdf`]

### 1.2 System context diagram (logical)

```
┌─────────────────────────────  STUDIO-OS  ─────────────────────────────┐
│                                                                        │
│  OPERATOR SURFACE            ORCHESTRATION CORE          RENDER FARM   │
│  ┌──────────────┐            ┌──────────────────┐      ┌────────────┐ │
│  │ Claude Code   │  spawns   │ Supervisor agent │ REST │ ComfyUI    │ │
│  │ CLI / IDE     ├──────────▶│ + 12 subagents   ├─────▶│ (headless, │ │
│  │ (designer)    │           │ (MARS + Reflexion│ 8188 │ FLUX.1 dev │ │
│  └──────────────┘            │  loops, capped)  │      │ +ControlNet│ │
│         ▲                    └───┬──────────┬───┘      │ +IP-Adapter│ │
│         │                        │          │          └─────┬──────┘ │
│  ┌──────┴───────┐   MCP    ┌─────▼────┐ ┌───▼──────┐        │        │
│  │ Review inbox │◀─────────│ Knowledge │ │ Memory   │   ┌────▼──────┐ │
│  │ (approve /   │  hooks   │ Layer     │ │ Layer    │   │ Nine-pillar│ │
│  │  annotate)   │          │ (RAG+KG+  │ │ (client  │   │ QA gates   │ │
│  └──────────────┘          │  vault)   │ │ profiles)│   │ + VLM judge│ │
│                            └───────────┘ └──────────┘   └───────────┘ │
│                                                                        │
│  GEOMETRY SOURCE OF TRUTH: AutoCAD / SketchUp / 3ds Max ──▶ clay/line │
│  exports feed ControlNet · V-Ray remains final-grade offline renderer │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.3 The five architectural planes

| Plane | Responsibility | Primary technology (per corpus) |
|---|---|---|
| **Orchestration** | Task decomposition, agent routing, loop control, failure recovery | Claude Code CLI + subagents; dynamic workflows for bulk jobs; (LangGraph + Temporal reserved for scale-out, §16) |
| **Knowledge** | Domain truth: codes, materials, ergonomics, styles, catalogs, brand standards | Hybrid RAG (BM25 + dense, RRF, cross-encoder rerank) + Spatial Knowledge Graph + multimodal indices [src: `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf`] |
| **Memory** | Client continuity across months/years | Mem0-style passive extraction with conflict resolution + Ebbinghaus decay + temporal consolidation, stored as versioned markdown + vector index [src: `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf`] |
| **Generation** | Concept and production imagery | Model-routed stack: Midjourney/Gemini → ComfyUI + FLUX + Depth ControlNet + IP-Adapter → Ideogram/Recraft → Magnific/SUPIR [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`] |
| **Verification** | Physics, perception, brand, client compliance | Nine-pillar QA scoring matrix + dependency-structured VLM judging + deterministic geometry/colorimetry, wired as CI-style gates |

### 1.4 Two operating surfaces

**Surface A — Designer cockpit (now).** Claude Code CLI inside the monorepo. The designer issues stage-level commands (`/intake`, `/concept`, `/render-pass`, `/qa-report`, `/deliver`), reviews artifacts in the filesystem, and approves gate promotions. Permission mode `acceptEdits` inside project working directories; `ask` for renders that consume paid API credits; hard `deny` for destructive operations. [src: `knowledge/_inbox/id-project-corpus/Claude Code Architecture Design.pdf`]

**Surface B — Headless automation (progressive).** The Claude Agent SDK embedded in scheduled routines and webhook handlers: nightly knowledge audits, documentation-drift repair, batch render queues, QA re-scoring after threshold changes. All SDK outputs are schema-validated (structured outputs with Zod/Pydantic) so downstream code never parses free text. Surface B is also the seam where a future client-facing product attaches (§16) without touching Surface A. [src: `knowledge/_inbox/id-project-corpus/Claude Code Architecture Design.pdf`]

### 1.5 Model routing policy (token economics)

| Tier | Model | Assigned work |
|---|---|---|
| Frontier reasoning | Claude Opus-class | Spatial mathematics, multi-constraint concept synthesis, MARS meta-review, architectural refactors of the repo itself |
| Default workhorse | Claude Sonnet-class | Stage execution, prompt compilation, code for pipeline scripts, standard reviews |
| High-volume parsing | Claude Haiku-class | Subagent bulk reads (catalog parsing, spec-sheet extraction, log triage), VQA question batching |
| Vision judging | Frontier VLM (Claude vision / Gemini-class) | Nine-pillar perceptual scoring, dependency-structured VQA |

Routing is declared per-agent in `.claude/agents/*.md` frontmatter so cost discipline is structural, not habitual. Hard runtime caps (max agents, max iterations, max tokens per stage) are set in workflow configuration to prevent runaway "zombie" orchestration.

---

## 2. Agent Architecture

### 2.1 Orchestration patterns adopted

The corpus converges on four patterns, composed rather than chosen exclusively:

- **Supervisor pattern** for delegation: a project-manager agent owns global state; specialist subagents are stateless workers in isolated context windows that return dense summaries only. This preserves the master context and enables parallel fan-out.
- **Planner pattern** for long-horizon stages: a planner emits a directed acyclic graph of steps before execution, decoupling strategy from action. Plans are written to the stage directory as `_plan.md` so the human can amend before execution (mixed-initiative).
- **MARS reviewer pattern** for evaluation: independent parallel reviewers (no lateral cross-talk) plus one meta-reviewer synthesizing verdicts — matching multi-agent-debate accuracy at roughly half the token cost and latency. [src: `knowledge/_inbox/id-project-corpus/AI Design Studio Architecture.pdf`]
- **Bounded Reflexion** for self-correction: linguistic critique stored to episodic memory and injected into the retry, **capped at 3 iterations**, and **triggered only in the Green Zone** (complex tasks with low initial confidence, or when a deterministic validator flags a failure). Never invoked on tasks the base model already performs above ~75% accuracy — the self-critique paradox shows the critic will hallucinate flaws and degrade correct output. [src: `knowledge/_inbox/id-project-corpus/AI Design Studio Architecture.pdf`]

### 2.2 The twelve-agent roster

Each agent is a Claude Code subagent defined in `.claude/agents/<name>.md` with least-privilege tool grants (e.g., analyzers are denied Write; only the render-dispatcher may call the ComfyUI MCP tool).

| # | Agent | Pattern role | Model tier | Responsibilities | Tool grants (least privilege) |
|---|---|---|---|---|---|
| 1 | `project-manager` | Supervisor | Sonnet | Client interface, global state, routing, gate promotion requests | Read, Task-spawn, memory-write |
| 2 | `planner` | Planner | Opus | Decompose briefs into stage DAGs; write `_plan.md` | Read, Write (plans only) |
| 3 | `memory-manager` | Memory controller | Haiku | Post-session extraction into client profiles; conflict resolution; decay pruning | Read, memory-write |
| 4 | `knowledge-manager` | Semantic RAG operator | Haiku | Hybrid retrieval + rerank from knowledge layer; returns citations + snippets only | Read, retrieval MCP |
| 5 | `interior-designer` | Author (MARS) | Opus | Spatial concept, zoning, aesthetic direction; the creative principal's counterpart | Read, Write (concept docs) |
| 6 | `prompt-engineer` | Syntax translator | Sonnet | Compile approved concepts into dual-track diffusion prompts + ControlNet parameters from the prompt registry | Read, Write (prompt payloads) |
| 7 | `lighting-specialist` | Domain reviewer | Sonnet | CCT plan, HDRI selection, sun-direction vs. window geometry, lighting-language injection | Read only |
| 8 | `material-specialist` | Domain reviewer | Sonnet | PBR-plausible material selection; ACT durability + TM-30 conformance vs. spec sheets | Read, retrieval MCP |
| 9 | `vision-reviewer` | VLM inspector | VLM | Verify depth/segmentation maps capture floor-plan geometry before generation | Read, image tools |
| 10 | `qa-agent` | Deterministic validator | Sonnet + Python | Execute clearance math, PBR ranges, ΔE00, homography checks via code execution | Read, Bash (sandboxed) |
| 11 | `critic` | Meta-reviewer / Reflexion trigger | Opus | Synthesize independent reviews into one revision mandate; enforce iteration caps | Read, Write (critique log) |
| 12 | `render-evaluator` | Post-production auditor | VLM | Final artifact scan for diffusion artifacts, warped geometry, upscale damage; triggers re-render | Read, image tools, render MCP |

### 2.3 Canonical delegation flow

A request such as "concept a Japandi living room for the Sukhumvit condo unit" executes as: `project-manager` pulls the client profile (memory) and unit constraints (knowledge + floor plan), `planner` emits the DAG, `interior-designer` authors the concept, the concept fans out **in parallel and in isolation** to `lighting-specialist`, `material-specialist`, and `qa-agent`, `critic` merges their independent verdicts into a single revision mandate, the Reflexion loop runs at most three times, then `prompt-engineer` + `vision-reviewer` prepare generation, the render dispatch runs, and `render-evaluator` + the nine-pillar gates score the output. Every hop writes its artifact into the current stage directory; nothing lives only in conversation.

### 2.4 Subagent hygiene rules

Subagents exist to protect the master context: they perform heavy reads (thousand-line catalogs, CAD exports, spec-sheet PDFs) inside isolated windows and return summarized JSON. Rules enforced by convention and hooks: a subagent may not spawn further subagents beyond depth 2; every subagent response is capped and schema-shaped; `SubagentStop` hooks run deterministic simplifiers on any code a subagent produced; parallel subagents operate in sparse-checkout worktrees so they never collide on disk.

---

## 3. Knowledge Architecture

The knowledge layer answers a different question at every altitude — *what is true about this domain?* — and is deliberately federated because no single retrieval technology satisfies interior design's mix of prose, imagery, and geometry.

### 3.1 The five-layer cognitive stack

| Layer | Question answered | Mechanism | Failure it prevents |
|---|---|---|---|
| L1 — Core directives | "How does this studio behave?" | CLAUDE.md hierarchy + path-scoped rules (deterministic injection, progressive disclosure) | Brand-voice drift, formatting chaos |
| L2 — Client personalization | "What does *this client* want, over years?" | Hybrid memory bank (§4) | Re-asking known preferences; recommending rejected materials |
| L3 — Spatial & functional logic | "Does it physically fit and comply?" | Spatial knowledge / scene graph + deterministic solvers | Geometric hallucination: the 90-inch sofa in the 85-inch alcove |
| L4 — Action & interoperability | "Can the studio *do* it in the real toolchain?" | MCP servers (Tools / Resources / Prompts) to ComfyUI, filesystem, catalogs, Git | Brittle screen-scraping; credential leakage into context |
| L5 — Broad domain knowledge | "What do the codes, catalogs, and precedents say?" | Multimodal hybrid RAG with cross-encoder rerank | Keyword-search brittleness; caption-loss on drawings |

### 3.2 Retrieval pipeline (L5) — the reference design

1. **Ingestion.** Documents are chunked with structure awareness; drawings, mood boards, and spec sheets are indexed twice: (a) unified text–image embeddings (CLIP/SigLIP-class) for cross-modal search, and (b) a late-interaction index (ColPali-class) for visually dense pages — blueprints, dimension sheets, brand-standard tables — where OCR-and-caption pipelines silently destroy signal. Caption-and-index alone is prohibited for technical drawings: caption hallucination becomes permanent index pollution. [src: `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf`]
2. **Candidate generation.** Hybrid search — dense vectors fused with sparse BM25 via Reciprocal Rank Fusion — plus metadata filters (project, room type, standard, recency). Returns 50–100 candidates.
3. **Precision reranking.** A cross-encoder scores query+document pairs jointly, capturing multi-conditional nuance ("mid-century chair, client hates leather, bad back") that bi-encoders compress away. Only the reranked top-k enters context. [src: `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf`]
4. **Grounded synthesis.** The knowledge-manager returns snippets **with citations to vault paths**; the consuming agent may not assert a code value without a retrievable source, mirroring the studio-vault Source-and-Truth Hierarchy.

### 3.3 The Spatial Knowledge Graph (L3)

LLMs are spatially blind — trained on 1-D token streams, they guess coordinates probabilistically. STUDIO-OS therefore never lets the language model adjudicate geometry. Each project floor plan is parsed into a **scene graph**: nodes are rooms, openings, fixed elements, and furniture instances carrying dimensions, orientation, and material attributes; edges are topological and constraint relations (adjacency, clearance, swing arcs, sight lines). The neuro-symbolic split is strict — the LLM translates intent into graph queries and placement proposals; a Python geometry engine (invoked by `qa-agent`) performs collision detection, clearance verification, and path checks. The corpus reports spatial-precision improvements up to 86.7% in complex scenes when symbolic graph reasoning replaces direct visual guessing. Graph edits are versioned; incremental construction uses edge-impact scoring to localize and repair inconsistencies rather than rebuilding.

### 3.4 Domain ontology — what actually goes in the knowledge base

Structured per the NCIDQ competency pillars so queries route correctly (IDFX → generative constraints; IDPX → validation and life safety; PRAC → workflow orchestration):

- **Aesthetic codification.** Elements (space, line, form, light, color, texture, pattern) as generative variables; principles (unity, balance, rhythm, emphasis, contrast, scale) as evaluation functions. Quantified heuristics wired into QA: the 60/30/10 color-distribution rule (verifiable by pixel analysis), the odd-number grouping rule (enforced in layout JSON schemas). Style taxonomy as a graph with **restrictive edges** — a "Japandi" node forbids ornamental mouldings; contradictions are flagged at concept time, not render time.
- **Ergonomics & clearances.** Encoded as hard constraints for the geometry engine: 1525 mm (60 in) circular turning space; 915 mm (36 in) continuous passage width; T-turn geometry as fallback; knee/toe clearance extrusions; door-swing sweep arcs vs. clear floor zones; activity-center rectangles at functional nodes. **Thai localization task (M1):** ingest the Building Control Act B.E. 2522 ministerial regulations, condominium juristic rules, and Thai kitchen/bath norms as the primary Authority set, with NKBA/ADA retained as secondary reference — all values metric-first.
- **Materials & FF&E.** Relational schema (Projects–Rooms–Products–Manufacturers–Suppliers) with lead times, unit costs, dimensions; ACT durability thresholds as qualifier gates (Wyzenbeek ≥15,000 double rubs general commercial, ≥30,000 heavy duty; Martindale ≥20,000 / ≥40,000); tropical-climate suitability flags (humidity, UV, termite exposure) for the Thai residential context. AWI joinery/veneer vocabulary for bespoke millwork specs (Division 06 vs. Division 12 distinction).
- **Lighting.** CCT bands (2200–3000 K residential warm; 4000 K+ task/commercial), TM-30 Rf/Rg with R9 tracked for dining/hospitality reds, dimming-protocol compatibility (0-10V / DALI / DMX) so specified luminaires match installed control.
- **Classification crosswalks.** MasterFormat (Div 06/08/09/12) ↔ UniFormat ↔ OmniClass mappings so early scope narratives unpack automatically into specification sections; IFC (IfcSpace/IfcWall/IfcDoor) parsing for BIM interop when projects arrive as models.
- **Brand/property standards** (for hospitality or developer-standard condo lines): Room Data Sheets as machine-readable rule engines — minimum areas, clear dimensions, ceiling heights, housekeeping tolerances — powering automated deficiency logs against uploaded plans.

### 3.5 MCP integration surface (L4)

| Server | Transport | Primitives used | Purpose |
|---|---|---|---|
| `comfyui` | HTTP (localhost:8188 wrapper) | Tools (`queue_render`, `poll_status`, `fetch_output`, `free_vram`) | Headless generation; OOM auto-recovery |
| `catalog` | HTTP | Resources (live SKU, price, dimensions, stock) | Deterministic FF&E data — never RAG-guessed |
| `vault` | stdio | Resources + Prompts | studio-vault read access; firm SOPs exposed as user-triggered MCP Prompts |
| `git` (GitHub MCP) | HTTP | Tools | Issue/PR automation, doc-drift repair PRs |
| `photoshop-bridge` | WebSocket (port 3000, UXP plugin) | Tools | Layer/mask extraction and programmatic compositing |

Two MCP disciplines are mandatory: **dynamic tool loading** (a lightweight registry search injects only relevant schemas per turn — loading 50+ tool schemas costs ~55k tokens and measurably degrades selection accuracy; dynamic loading cuts tool tokens ~85% and lifts selection accuracy from ~79% to ~88%), and **zero-metadata credential design** (schemas expose only semantic parameters; an execution layer resolves secrets from a vault by connection ID so credentials never enter the context window).

---

## 4. Memory Architecture

Memory answers *what has happened between this studio and this client* — distinct from knowledge (domain truth) and context (what's loaded right now).

### 4.1 Four memory types and their physical homes

| Type | Content | Physical implementation |
|---|---|---|
| Working | Active task state | The context window itself, budgeted per §5 |
| Episodic | Time-indexed events: decisions, revisions, approvals, rejections, render settings that worked | `clients/<id>/episodes/*.md` (append-only, dated) + vector index |
| Semantic | Consolidated client truths: preferences, aversions, constraints, household facts | `clients/<id>/profile.md` (curated, conflict-resolved) |
| Procedural | How the studio executes: skills, templates, hooks, prompt registry | `.claude/skills/`, `templates/`, versioned in Git |

### 4.2 Write path: passive extraction with conflict resolution

Following the Mem0 paradigm (chosen over MemGPT-style agent-managed paging for predictability and inference-budget separation) [src: `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf`]: a post-session routine — not the live agent — extracts salient facts from the transcript, links entities, and merges into the profile. **Conflict resolution is timestamp-aware and latest-wins with provenance retained** ("client now prefers minimal; previously maximal — changed 2026-05-14, see episode E-041"). Benchmarks in the corpus justify the choice: ~66.9% recall accuracy at 0.71 s median latency and ~1.8k tokens per conversation versus a full-context baseline at 72.9% but 9.87 s and 26k+ tokens — the marginal accuracy is not worth 14× tokens on every turn.

### 4.3 Consolidation and forgetting

Two mechanisms keep the store honest over multi-year relationships. A **temporal tree** consolidates granular episodes into abstracted parent summaries as time windows close (daily notes → project-phase summaries → relationship portrait), while a parallel **semantic graph** captures entity relations independent of chronology (H-Mem dual structure) — so "what has this client rejected across all properties, and has that shifted?" is answerable by graph traversal plus temporal check. An **Ebbinghaus-style decay score** governs pruning: memories gain strength on recall or significance, unaccessed transients decay and are archived (never hard-deleted; archived episodes remain grep-able). Abandoned ideas fade; enduring preferences consolidate.

### 4.4 Read path and safety rails

Stage contracts declare which memory slices load: intake loads the full profile; a render stage loads only style/material preferences. Memory is injected as a compact **Metadata + Constraint package** (§5.3), never as raw transcript dumps. Two rails: (1) memory never overrides Authority-tier rules — a remembered "client wants the corridor at 700 mm" still fails the 900 mm code gate; (2) profile edits are diff-reviewed by the designer weekly (a scheduled routine opens a PR against `profile.md`), keeping the human the editor-in-chief of what the studio "believes" about people.

---

## 5. Context Engineering

### 5.1 The token budget: four tiers

Long windows do not repeal attention decay — recall follows a U-curve (primacy + recency), distractors rot reasoning, and models turn conservative as windows saturate. STUDIO-OS therefore enforces a tiered budget with placement discipline (static tiers first for cache hits and primacy; volatile material last for recency):

| Tier | Budget | Content | Placement |
|---|---|---|---|
| 1 — System | ~5% | Studio identity, safety rules, non-negotiables | Absolute beginning (cache-stable) |
| 2 — Project config | ~15% | CLAUDE.md chain, active path-scoped rules, stage contract | After system (cache-stable) |
| 3 — Session memory | ~20% | Compaction summaries, client profile package, plan state | Middle |
| 4 — Working | ~60% | Live conversation, tool outputs, file reads | End (recency zone) |

Prompt-caching economics reinforce the ordering: immutable prefixes (Tiers 1–2) hit provider caches (~90% input-cost savings on cached tokens with explicit breakpoints); dynamic content stays beyond the cache boundary.

### 5.2 The CLAUDE.md hierarchy

- **Root `CLAUDE.md` — hard cap 200 lines.** Repository topology map, the stage-pipeline convention, core commands, architectural boundaries (e.g., "generation agents never write to `knowledge/`; QA thresholds change only via PR"), MCP inventory. Excludes anything the model already knows (no generic style guides).
- **Directory-level `CLAUDE.md`** in `pipeline/`, `knowledge/`, `clients/`, `projects/` — loaded only when the agent works there (e.g., the projects file defines the stage-contract protocol; the pipeline file defines ComfyUI JSON conventions).
- **Path-scoped rules in `.claude/rules/*.md`** with glob frontmatter for cross-cutting concerns that fire on file match: `render-payloads.md` (triggers on `*.workflow.json`), `client-privacy.md` (triggers on `clients/**`), `materialx.md` (triggers on `*.mtlx`).
- **`CLAUDE.local.md`** (gitignored) for personal overrides.

A monolithic instruction file is a named anti-pattern: adherence drops, hallucinated APIs rise, merge conflicts multiply. The hierarchy is the remedy.

### 5.3 Modular context packages

Every stage assembles instructions from five explicitly ranked roles, preventing "context soup" and giving deterministic conflict resolution:

1. **Authority** — inviolable: Thai code values, safety clearances, client budget ceiling, privacy rules. (Sourced from the studio-vault Source-and-Truth Hierarchy.)
2. **Exemplar** — 2–3 canonical few-shot artifacts from `examples/` (a gold-standard concept doc; a perfect render payload). Dense examples align behavior better than abstract rules.
3. **Constraint** — task-local bounds: word counts, forbidden elements, target aspect ratio, SKU whitelist.
4. **Rubric** — the exact QA criteria the output will be scored against, injected *before* generation so the agent self-verifies against the same bar the gates use.
5. **Metadata** — project ID, stage, timestamps, schema versions, client-profile slice.

### 5.4 Noise control and session hygiene

- **Tool-result clearing:** oversized tool payloads (catalog dumps, DOM-scale JSON) are surgically replaced with placeholders after use; re-needed data is re-fetched, never hoarded.
- **Compaction:** at ~95% saturation, lossy summarize preserving decisions and open questions; `/compact <focus>` mid-thread when a debug tangent wanders; `/clear` on task switch — always.
- **Execution proxies:** verbose shell output (render logs, test runs) passes through summarizing wrappers returning only the failing assertion or final status (RTK-style, up to ~90% token reduction on command noise).
- **Progressive code/file retrieval:** summaries → snippets → full file, never blind `grep`-and-ingest across the repo.
- **Exclusion globs** in settings keep the agent out of `assets/` binaries (LFS pointers only), archives, and vendored code.
- **Output restraint:** agents answer tersely by default (Caveman-style), because the agent's own verbosity is tomorrow's context bloat.

---

## 6. Workflows — The Project Lifecycle as a Filesystem

### 6.1 The nine-stage pipeline (ICM applied to interior design)

Every client project instantiates from a template into numbered stage directories. Each stage has `_contract.md` (inputs/process/outputs/gate), and a stage is **done** only when its outputs exist and its gate passes.

```
projects/PRJ-2026-014_sukhumvit-condo/
├── 00_intake/        # signed brief, plans, site photos, budget → structured brief.json
├── 01_brief/         # requirements matrix, client-profile merge, success criteria
├── 02_concept/       # zoning, style direction, mood narrative  [MARS review gate]
├── 03_layout/        # scene graph, furniture placement, clearance report  [Geometry gate]
├── 04_visualization/ # prompt payloads, ControlNet maps, render batches  [Gates 1–2]
├── 05_qa/            # nine-pillar scorecards, VLM critiques, repair queue  [Gates 3–4]
├── 06_revisions/     # client feedback ingestion, targeted inpaint/regenerate cycles
├── 07_deliverables/  # upscaled finals, spec book, BOM, presentation set
└── 08_handover/      # archive manifest, memory consolidation, retrospective
```

### 6.2 The generation execution loop (stages 02→05 in detail)

**Phase A — Ingestion & planning.** `project-manager` merges brief + memory + knowledge; `planner` writes the DAG. Human may edit `_plan.md` before execution.

**Phase B — Concept under MARS.** `interior-designer` authors; three independent reviewers (lighting, material, deterministic QA) critique in parallel isolation; `critic` issues one synthesized mandate; Reflexion loop ≤3 rounds, Green-Zone-gated. Output: approved concept + layout intent.

**Phase C — Spatial translation.** The layout is committed to the scene graph; the geometry engine emits a clearance report (hard gate — unbuildable layouts never reach rendering). `vision-reviewer` validates that depth/segmentation maps extracted from the SketchUp/CAD clay export faithfully capture the plan.

**Phase D — Headless generation.** `prompt-engineer` compiles the dual-track prompt payload + sampler config + ControlNet maps into ComfyUI workflow JSON; dispatch via MCP; asynchronous poll; OOM auto-recovery (`/free` + retry).

**Phase E — Verification & consolidation.** Nine-pillar gates score outputs; failures route to the vision-feedback loop (§10); passes land in the review inbox; on approval, `memory-manager` logs the trajectory — including the exact ControlNet weights and seeds that worked — into episodic memory so procedural capability compounds.

### 6.3 Standing workflows (beyond client projects)

- **Knowledge ingestion:** drop a document into `knowledge/_inbox/` → routine chunks, embeds, cross-links, and opens a PR summarizing what changed.
- **Doc-drift repair:** on merge, a routine diffs code/config against `docs/`; drift triggers an auto-authored fix PR (§11.4).
- **Weekly memory review:** consolidation PR against client profiles.
- **Nightly audits:** catalog freshness, LFS integrity, QA-threshold regression suite against a golden image set.

---

## 7. Repository & Folder Structure

### 7.1 The monorepo tree (feature-based, agent-optimized)

```
studio-os/
├── CLAUDE.md                      # ≤200 lines: topology, boundaries, commands
├── .claude/
│   ├── settings.json              # permissions (deny→ask→allow), hooks, exclusions
│   ├── settings.local.json        # personal (gitignored)
│   ├── rules/                     # path-scoped: render-payloads.md, client-privacy.md, materialx.md, usd.md
│   ├── agents/                    # the 12 subagent definitions (§2.2)
│   ├── skills/                    # prompt system as code (§8): concept-brief/, render-pass/, qa-report/,
│   │                              #   bom-generate/ (disable-model-invocation: true), usd-validate/, material-lint/
│   └── hooks/                     # guard-destructive.sh, format-on-write.sh, verify-on-stop.sh, audit-config.sh
├── .mcp.json                      # comfyui, catalog, vault, git, photoshop-bridge
├── .gitattributes                 # LFS: *.psd *.max *.skp *.usd* *.exr assets/**/*.png …
├── knowledge/                     # L5 corpus (text + indices), seeded from studio-vault v2.2
│   ├── codes-th/                  # Building Control Act, ministerial regs, condo rules (Authority tier)
│   ├── ergonomics/  materials/  lighting/  styles/  classifications/  brand-standards/
│   └── _inbox/                    # ingestion drop zone
├── clients/
│   └── <client-id>/ profile.md · episodes/ · assets-releases/
├── projects/
│   └── PRJ-YYYY-NNN_slug/ 00_intake … 08_handover   (§6.1)
├── assets/                        # ALL heavy binaries — LFS-tracked, excluded from agent recursion
│   ├── shared/ materials-mtlx/ · lighting-usd/ · hdri/ · furniture-usd/
│   ├── references/                # mood boards, precedent imagery (vision-promptable)
│   └── projects/<PRJ>/ renders/ · maps/ · upscales/
├── pipeline/
│   ├── comfyui/workflows/*.workflow.json   # versioned graphs: flux-depth-ipadapter-v3.workflow.json …
│   ├── prompts/registry/          # §8.4: versioned, labeled dev|staging|production
│   └── scripts/                   # geometry engine, ΔE00, PBR validators, dispatchers, pollers
├── qa/
│   ├── thresholds.yaml            # the scoring matrix (§9.3) — change via PR only
│   ├── golden-set/                # reference images for regression testing judges & thresholds
│   └── reports/                   # per-batch scorecards (JSON + human summary)
├── docs/
│   ├── reference-map.md           # AUTO-GENERATED index: routes, schemas, asset deps (never hand-edit)
│   └── strategy.md                # HUMAN-CURATED: why-decisions, tech debt, audit findings
├── templates/                     # project scaffold, stage contracts, concept-doc, spec-book, RDS
├── examples/                      # gold-standard artifacts for few-shot Exemplar packages
└── scripts/                       # repo-level utilities (scaffold_project.py, lfs_audit.sh)
```

### 7.2 Asset and naming conventions

Universal `Prefix_BaseName_Variant_Suffix` scheme so type/origin/function are inferable without opening files: `SM_Sofa_Sectional_01`, `M_Oak_Fumed_02_Inst`, `T_Terrazzo_White_01_ORM`, `HDRI_BangkokDusk_01`. Renders: `R_PRJ014_Living_Cam02_v07.png`; ControlNet maps: `D_…` (depth) / `S_…` (segmentation). Prompts and skills follow the same lexical rigidity (`skill_render-pass_v04`). Renames happen only through scripts that update references — never raw file-explorer moves. [src: `knowledge/_inbox/id-project-corpus/Large Scale Project Organization.pdf`]

Materials use **MaterialX** (open, text-parseable, agent-auditable) packaged in the zipped-container convention: one root `.mtlx`, a `/textures/` subfolder, stored **uncompressed** so renderers can memory-map textures; the agent can audit or batch-adjust PBR values across the library programmatically. Scene assembly uses **USD composition arcs** with strict payload boundaries: geometry stays behind payloads (not loaded until needed); lighting rigs are sublayers; variants carry style options — so lighting edits never touch mesh files and even a studio-of-one avoids merge disasters. ASCII `.usda` is preferred where feasible so the agent can parse scene graphs directly. [src: `knowledge/_inbox/id-project-corpus/Large Scale Project Organization.pdf`]

### 7.3 Version control mechanics

Git LFS from day one for every binary class (retrofitting is disruptive); the agent sees only kilobyte pointer files, protecting the token window from binary garbage. Sparse-checkout profiles per role; subagent worktrees use precise sparse paths plus symlinked shared-asset caches to avoid disk duplication. Hosting on GitHub-class infrastructure for the 5 GB per-file ceiling, generous included LFS bandwidth, and the first-party GitHub MCP server that lets the agent read issues, open PRs, and drive CI under least-privilege OAuth scopes. [src: `knowledge/_inbox/id-project-corpus/Large Scale Project Organization.pdf`]

---

## 8. Prompt System

Prompting is treated as a compiled, versioned software layer — not artisanal text. The prompt system has four components: structured schemas, encoder-aware compilation, domain lexicons, and a governed registry.

### 8.1 Structured schemas (XML) and the elimination of the inference tax

Free-flowing "keyword soup" forces the model to spend attention guessing prompt boundaries, producing instruction drift and attribute leakage (a background modifier bleeding onto the subject). All generation prompts are compiled into tagged schemas with unambiguous attention boundaries:

```xml
<role>Architectural interior photographer; photoreal V-Ray sensibility.</role>
<context>Bangkok condominium living room, 34 m², north-facing curtain wall,
  7th floor, city haze at dusk; geometry locked by depth map D_PRJ014_Living_Cam02.</context>
<subject>Japandi lounge grouping: low-profile oak-frame sofa in stonewashed
  linen (greige), travertine plinth coffee table, single paper-cord armchair.</subject>
<instructions>60/30/10 palette (warm white / muted oak / matte black accents);
  odd-count decor groupings; maintain two-point perspective, verticals parallel.</instructions>
<output_format>Photorealistic render, 3:2, base 1024, physically accurate
  materials with micro surface imperfections.</output_format>
```

Scaffolds (R.C.T.F., 5Ws, TRACI) are embedded in skill templates so no required parameter is omitted; `{{placeholders}}` allow programmatic injection, and composability lets a master template reference the studio's locked sub-prompts (e.g., a house `StudioLighting` block) so brand aesthetics stay uniform across thousands of assets.

### 8.2 Encoder-aware compilation (the dual-track rule)

Modern diffusion stacks (FLUX, SD3-class) parse text through **two encoders with different strengths**, and feeding both the identical paragraph measurably degrades output (reported 50–75% competence loss on Flux-dev with duplicated long prompts) [src: `knowledge/_inbox/id-project-corpus/AI Image Prompt Engineering.pdf`]. The `prompt-engineer` agent therefore always emits a bifurcated payload:

- **T5 track (up to ~512 tokens):** narrative prose carrying structure — spatial relationships, scene logic, camera geometry, lighting story.
- **CLIP track (short):** comma-separated high-salience tags — materials, style tokens, finish qualities.

**Negative-prompt policy is model-conditional:** SD-class graphs route targeted negatives ("watermark, warped perspective, extra chair legs") plus adaptive untargeted negatives through a dedicated conditioning node; **FLUX lacks standard CFG, so negatives are converted to aggressive positive framing** ("impeccably clean, sparse, uncluttered") at compile time. In ComfyUI, token weights are passed **un-normalized** — stacked heavy weights blow out the latent space (color burn, artifacting) — so the compiler enforces a weight budget and prefers restructuring over weighting.

### 8.3 Domain lexicons (the vocabulary that unlocks latent physics)

The registry ships three controlled vocabularies, curated in `knowledge/` and injected by the compiler; generic words ("modern materials", "big window") are lint-flagged [src: `knowledge/_inbox/id-project-corpus/AI Image Prompt Engineering.pdf`, `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`]:

| Lexicon | Purpose | Example tokens |
|---|---|---|
| Materiality | Trigger correct specularity/roughness/refraction priors | honed Carrara marble · fumed oak, plain-sliced · bouclé · stonewashed linen · brushed brass · reeded glass · white terrazzo with mixed stone chips · limewashed plaster · "micro surface imperfections", "physically accurate veining" |
| Lighting physics | Control mood, volume, falloff | golden hour · blue-hour twilight · overcast diffusion · volumetric rays · global illumination · rim light · soft contact shadows · ambient occlusion · 2700 K warm ambient vs 4000 K task |
| Camera & composition | Control perspective, scale, focus | 24 mm wide establishing · 35–50 mm eye-level natural · 85 mm+ material close-up · tilt-shift (verticals parallel) · f/8 deep focus vs f/2.8 shallow bokeh · rule of thirds · leading lines · foreground depth element |

### 8.4 The prompt registry (governance)

Every production prompt lives in `pipeline/prompts/registry/` with **immutable versioning** (each edit = new content-hashed version), environment labels (`dev → staging → production`), and per-version observability (cost, latency, QA pass-rate, human approval rate). Regressions roll back instantly by re-pointing the label. Skills in `.claude/skills/` are the invocation layer: each skill's SKILL.md carries frontmatter (invocation rules, target globs, model tier) and can inject live system state via inline bash before the model runs. Financially or contractually sensitive workflows — `bom-generate`, `client-deliver` — set `disable-model-invocation: true` so they execute only on explicit human slash command, never autonomously. The taxonomy is organized **by intent and domain, never by model**, insulating the library against model deprecation.

### 8.5 Automatic prompt optimization (APO) — the improvement flywheel

Prompt refinement is closed-loop, not manual: a VLM critique of a failed generation becomes a **textual gradient** (ProTeGi-style) that a meta-optimizer uses to rewrite the failing schema element; a requirement checklist derived from the prompt (RAISE-style) gates completion — unmet items trigger targeted rewriting or localized resampling rather than full regeneration; and successful strategies (prompt fragments, ControlNet weights, seeds) are stored to memory (MemoGen-style) and retrieved for similar future briefs. Head-to-head comparisons (Maestro-style tournaments) settle A/B versions before promotion to `production`. [src: `knowledge/_inbox/id-project-corpus/AI Image Prompt Engineering.pdf`]

---

## 9. Quality Assurance — The Nine-Pillar Scoring System

QA is the studio's constitution: a measurable, versioned scoring matrix executed as sequential CI-style gates. Pillars combine **deterministic math** (non-negotiable) with **calibrated probabilistic judges** (validated against human ratings before being trusted).

### 9.1 The nine pillars

| # | Pillar | What it verifies | Primary mechanisms |
|---|---|---|---|
| 1 | Prompt QA | Semantic fidelity to the compiled brief | Dependency-graph decomposition (DSG) for open scenes; Soft-TIFA probabilistic scoring for templated payloads; scene-graph alignment (node/edge/global) for relational logic |
| 2 | Image QA | Perceptual/statistical integrity | BRISQUE (MSCN → GGD/AGGD features → SVR) and NIQE for no-reference scoring; NIQE's suprathreshold-patch behavior avoids penalizing intentional depth-of-field |
| 3 | Lighting QA | Physically possible illumination | Shadow-probability maps (FFT residual separation of illumination vs texture); forensic light-source triangulation — shadow-tip and specular-highlight vectors must intersect at one implied source within angular tolerance; hierarchy check (secondary sources never outshine primaries; no CCT clashes in one zone) |
| 4 | Material QA | PBR plausibility | Albedo histogram within 30–240 sRGB (energy conservation); metalness effectively binary (0/1, mid-gray penalized); roughness distribution avoids absolute 0.0/1.0; texture spatial frequency vs object scale (no giant wood grain); seam/tiling artifact scan; emissives cast plausible local light |
| 5 | Camera QA | Valid projective geometry | Vanishing-point extraction (recurrence-based R-VPD for soft-edged AI images) → homography factorization (NDLT/SVD + RANSAC); verticals parallel for interior two-point convention; consistent radial distortion across the frame |
| 6 | Consistency QA | Cross-image / temporal stability | MET3R-style multi-view consistency for camera sets of one room; FloLPIPS optical-flow-weighted warping error for video/walkthroughs; entity-count and attribute stability via MLLM frame checks |
| 7 | Brand QA | Colorimetric & identity precision | Segment brand/palette regions → CIELAB (D65) → **ΔE00**; SIFT/ORB keypoint match on logos/typography against vector masters (aspect, kerning, spacing tolerances) |
| 8 | Client Requirement QA | The brief's operational rubric | LLM-as-a-Judge with explicit criteria, chain-of-thought, JSON output; judge itself validated before trust (§9.4) |
| 9 | Revision QA | Edits don't damage the rest | Pixel mask isolates the edit zone; outside the mask, LPIPS/SSIM delta vs. pre-edit must stay under threshold (latent-drift detection); model-update regressions on the golden set block deployment |

### 9.2 Studio-specific deterministic pre-gate (Gate 0)

Before any pixel is scored, the **geometry gate** runs on the scene graph: clearance matrix satisfied (turning circles, passage widths, swing arcs, knee/toe), no 3D bounding-box collisions, style-graph contradictions absent, 60/30/10 and odd-rule heuristics satisfied in the layout JSON, budget within ceiling from live catalog Resources. An unbuildable design is rejected before it costs a render.

### 9.3 Scoring matrix (initial thresholds — `qa/thresholds.yaml`, tuned in M3 calibration)

| Pillar / metric | Hard gate (pass) | Soft gate (warn) | Fail action |
|---|---|---|---|
| Prompt QA — Soft-TIFA mean | ≥ 0.85 | 0.70–0.85 | New seed / targeted rewrite, regenerate |
| Image QA — BRISQUE | ≤ 30 | 30–45 | Discard, resample |
| Material — Albedo in 30–240 sRGB | ≥ 99.5% px | 98–99.5% | Reject; material-prompt repair |
| Material — Metalness binarity | ≥ 95% px at {0,1} | 90–95% | Reject or route to relight/repair |
| Lighting — source triangulation | ≤ 5° deviation | 5–10° | Route to relight (TokenLight/ControlLight-class) or regenerate |
| Camera — homography residual | ≤ 2 px | 2–4 px | Reject; check ControlNet map fidelity |
| Consistency — warp error (video/sets) | ≤ set baseline | +10% | Re-render offending frames/views |
| Brand — ΔE00 | < 1.0 | 1.0–2.0 | > 2.0 → non-compliant, correct palette |
| Client rubric — judge score | ≥ 4 / 5 | = 3 | Localized inpaint or regenerate per critique |
| Revision — background LPIPS delta | ≤ 0.05 | 0.05–0.10 | Re-edit with stronger background clamping |

Soft-gate passes attach warning metadata for the human reviewer; hard-gate failures never reach the review inbox. Threshold changes go through PR + golden-set regression.

### 9.4 Judge governance

Before any LLM/VLM judge gates production, it is validated against a designer-labeled ground-truth set: **Spearman ρ ≥ 0.8** (correct relative ranking), **Cohen's κ ≥ 0.8** (correct absolute pass/fail), accuracy tracked per rubric item; self-bias is checked by cross-family judging. Judges are re-validated whenever the underlying model version changes — an uncalibrated judge is treated as a broken test, not a lenient one.

### 9.5 Sequential gate logic (fail fast, spend late)

```
Gate 1 · EXECUTION   raw output → Image QA + Prompt QA
        fail → discard, reseed, regenerate (cheapest failure)
Gate 2 · PHYSICS     segmentation → Camera + Lighting + Material QA (+ Gate 0 already passed)
        fail → reject or route to targeted repair (relight / inpaint) 
Gate 3 · CLIENT      Brand ΔE00 + LLM-judge rubric
        fail → prompt augmentation + localized regeneration via §10 loop
Gate 4 · POLISH      Consistency (sets/video) + Revision drift after edits/upscale
        pass → publish scorecard → review inbox → human approval → deliverables
```

Every artifact carries its scorecard JSON; approvals write status back to the project tracker via webhook, and the approved prompt/settings pair is embedded back into memory — the QA system is also the training-data factory for §16's preference optimization.

---

## 10. Vision Feedback Loop — Closed-Loop Critique and Repair

The intent-generation gap is structural: diffusion models paint statistics, not photons, so they hallucinate impossible fireplaces, floating credenzas, and toy-scaled wood grain. Because generic LVLMs are strong at semantics but weak at low-level spatial/material features, the loop decomposes evaluation into verifiable atoms and pairs the VLM with deterministic estimators.

### 10.1 The five-step loop

1. **Visual anchoring.** Render the compiled prompt once at draft quality. This externalizes latent textual hallucinations into observable pixels — the concrete baseline for critique.
2. **Dependency-structured question generation.** Decompose the brief into a DAG of binary visual questions; prerequisites gate dependents ("window exists?" before "daylight direction correct?"), plus universal probes (glitches, legible signage, anatomical distortions). This forces localized, grounded critique instead of vague vibes.
3. **Diagnostic VQA.** The VLM answers YES/NO per node with a written rationale for every NO. In parallel, deterministic estimators run: R-VPD perspective check; monocular metric depth (Depth-Anything-V2/ZoeDepth-class) to catch floating objects via depth discontinuities at contact points; 2D→3D bounding-box lifting (Cube R-CNN/OmniNOCS-class) for proportion and collision sanity; texture-frequency vs. object-scale for pattern sizing.
4. **Targeted refinement.** Failures map to minimal edits — never wholesale prompt rewrites (which cause stylistic drift): dimensional anchors injected ("oversized 2.7 × 3.6 m rug extending beneath the sofa's front legs"), adaptive negatives accumulated (SD-class) or positive reframing (FLUX), ControlNet weights adjusted, or region-masked inpainting for locally flawed but globally sound frames. The failed rewrite is retained as a hard negative so the system doesn't learn to game the rubric with longer sentences.
5. **Verification & early exit.** Re-render, re-score only failed nodes; **loop cap = 3**; unmet-after-cap → human triage queue with full critique history attached.

### 10.2 Aesthetic balance

Adherence and beauty are different axes — the most literal model is rarely the most beautiful — so alongside the physics stack, an aesthetic scorer (AESBench-style dimensions: technical quality, composition incl. foreground depth, plausible depth-of-field, color harmony) filters images that are correct but sterile. Both axes appear on the scorecard; the human arbitrates taste, the machine guarantees truth.

### 10.3 Privacy posture

Client floor plans and site photos are proprietary. Default judging runs on local/self-hosted VLMs where feasible; when frontier cloud judges are required, images are stripped of client-identifying metadata, and the long-term path (§16) is distilled on-device rewriter/judge models (compact ~250 M-parameter class) for the routine 80% of checks.

---

## 11. Automation

### 11.1 Deterministic lifecycle hooks (the law layer)

| Hook event | Fires when | STUDIO-OS enforcement |
|---|---|---|
| `SessionStart` | Session begins/resumes | Inject active branch, open project stage, pending QA queue into context |
| `PreToolUse` | Before any tool executes | Block destructive bash (`rm -rf`, force-push), writes to `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.env`, client-privacy violations → JSON `{"permissionDecision":"deny"}` + exit 2, reason fed back to the model [src: `knowledge/_inbox/id-project-corpus/Claude Code Architecture Design.pdf`] |
| `PostToolUse` | After successful tool call | Auto-format edited files (prettier/ruff), lint MaterialX/USD on matching writes, validate workflow JSON against schema |
| `SubagentStop` | Subagent finishes | Run code-simplifier on generated code; enforce summary-size cap |
| `ConfigChange` | Settings/permissions edited | Append immutable audit-log entry |
| `Stop` | Agent ends its turn | Verification loop: run the stage's test/QA script; blocking signal forces the agent to read failures and fix before the turn may end; final memory-write step |

Permissions follow the strict `deny → ask → allow` evaluation order in `settings.json`: deny is absolute (production data, secrets, catalog mutations); ask covers paid render dispatch and anything touching `clients/`; allow silently approves reads and test runs. `acceptEdits` inside project stage dirs keeps daily friction low; CI contexts run `dontAsk` (zero-trust whitelist-only). Security is never a CLAUDE.md sentence. [src: `knowledge/_inbox/id-project-corpus/Claude Code Architecture Design.pdf`; the settings/hook rules landed in `.claude/settings.json` + `.claude/hooks/guard_bash.py`]

### 11.2 Headless render orchestration

ComfyUI runs as a backend server (REST on 8188); visual graphs are exported as API-format JSON and dispatched programmatically: POST workflow+variables → receive `prompt_id` → poll history / WebSocket-subscribe → fetch outputs. The wrapper handles the ugly parts automatically: OOM detection → `/free` to unload models → retry; prompt-cache anomalies → forced fresh execution; batch fan-out with concurrency limits sized to VRAM (FLUX.1-dev wants 16–24 GB). For multi-step chains (generate → QA → upscale → notify), an n8n-class orchestrator or plain Python pipeline scripts provide the connective tissue — webhook trigger → vector-DB style lookup → payload injection → poll loop → route artifact to storage/QA/inbox. [src: `knowledge/_inbox/id-project-corpus/AI Studio Workflow Automation.pdf`]

### 11.3 Review, approval, and delivery routing

Only artifacts that clear Gates 1–4 reach the human. The review inbox is a filesystem convention (`05_qa/_inbox/` with scorecards) surfaced through the designer's normal flow; at multi-reviewer scale it upgrades to a proofing platform (Frame.io/Ziflow-class) with sequential paths (creative → client) and audit trails [src: `knowledge/_inbox/id-project-corpus/AI Studio Workflow Automation.pdf`]. All inbound webhooks verify HMAC-SHA256 signatures and use exponential-backoff retries; an approval event triggers the delivery chain (final upscale if not yet run → watermark/manifest → `07_deliverables/` → client notification), and a change-request event routes the annotation into `06_revisions/` as a structured repair ticket for the §10 loop.

### 11.4 Scheduled routines (the studio that maintains itself)

Cloud/local scheduled Claude Code runs, each with hard token/agent caps: nightly — golden-set QA regression, LFS/pointer audit, catalog freshness diff; on-merge — documentation-drift detection (diff vs `docs/`, auto-PR the fix); weekly — memory consolidation PRs, prompt-registry performance report (pass-rates by version), knowledge `_inbox/` ingestion; monthly — judge re-validation (§9.4), threshold review, cost report by model tier. Every routine proposes via PR/branch; **no routine merges to main autonomously** — the human-in-the-loop merge is a standing security boundary, not a temporary training wheel.

### 11.5 Onboarding automation (client intake)

Intake documents (brief PDFs, plan sets, budget sheets) dropped into `00_intake/` are parsed into `brief.json` + requirement matrix + initial profile; provisioning scaffolds the project from `templates/`, opens the tracking entry, and schedules the kickoff summary. Targets carried from the corpus: ~30% faster time-to-first-value, 50–75% fewer data-entry errors, 40–60% less administrative time per client — measured, not assumed, via the milestone metrics in §14.

---

## 12. Commercial Production Pipeline

No single model is sufficient; the pipeline routes each phase to the architecture that wins it, wrapped around the studio's existing CAD/3D truth.

### 12.1 The five-phase commercial flow

**Phase 1 — Concept & client buy-in (speed + emotion).** Midjourney V7 for dramatic, art-directed concept frames and mood boards (`--sref` locks the aesthetic across a campaign; Draft Mode for cheap ideation); Gemini-class (Nano-Banana lineage) for conversational multi-reference staging — up to 14 reference images, e.g., compositing the client's existing furniture photos into candidate styles. Output: an approved direction, not construction truth. [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`]

**Phase 2 — Structural production (determinism).** Geometry authored where it already lives — SketchUp/AutoCAD (3ds Max for complex sets). Export clay render / line view per approved camera. In ComfyUI: **Depth ControlNet** (Zoe-class preprocessor) locks volumetric layout, walls, openings, vanishing points; **IP-Adapter** injects the Phase-1 approved style via decoupled cross-attention; **FLUX.1-dev, run locally**, generates — chosen for best-in-class material physics (grain directionality, marble veining continuity, glass/metal refraction), open weights (LoRA fine-tuning on the studio's portfolio later), and absolute data privacy for client plans. Canny edge maps are reserved for strict-preservation cases; segmentation maps deployed when texture bleeding appears. Semantic segmentation enables element-isolated variants (swap sofa fabric, hold the room). [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`]

**Phase 3 — Graphics & branding (when applicable).** Ideogram-class for legible in-scene typography (signage, menus, wayfinding in commercial/hospitality work); Recraft-class for art-directed presentation boards, brand-kit palette locking, and native SVG when vector deliverables are needed.

**Phase 4 — Delivery-grade polish.** Base 1024-class outputs are upscaled to 4K: **Magnific-class creative upscale at Creativity ≈ 0.3 / Resemblance ≈ 85%** enriches micro-texture (fabric pilling, grout, veining) without inventing geometry; **SUPIR-class precision restoration** for images whose geometry must not change (including V-Ray outputs being sharpened). Revision QA (Gate 4) confirms the upscale didn't drift. [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`]

**Phase 5 — Deliverables assembly.** `07_deliverables/` compiles the presentation set, spec book (auto-generated from the scene graph + catalog: dimensions, finishes, ACT/TM-30 data, MasterFormat sections), and BOM with live pricing via the catalog MCP Resource — executed only through the human-triggered `bom-generate` skill.

**V-Ray coexistence rule:** AI renders own concept, iteration, and marketing-grade visualization; V-Ray/Corona from 3ds Max remains the renderer of record wherever contractual accuracy is required (millwork shop-drawing companions, lighting-design sign-off). The AI pipeline's ControlNet maps and the V-Ray scene share the same CAD source, so the two never disagree about geometry.

### 12.2 Licensing & commercial-rights register (compliance is a gate, not a footnote)

| Platform | Commercial use | Key condition to track |
|---|---|---|
| Midjourney | Paid plans only | > $1 M gross revenue ⇒ Pro/Mega required; images public unless Stealth (Pro/Mega); no rights on free/trial [src: `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf`] |
| FLUX.1-dev | Outputs: yes, freely | Model **weights** non-commercial — never sell API access to the hosted model; outputs belong to the studio |
| Stable Diffusion 3.5 | Yes under Community License | < $1 M revenue; Enterprise license beyond |
| Adobe Firefly | Yes | Safest harbor — trained on licensed stock, enterprise IP indemnification; use for risk-averse corporate clients |
| Recraft | Paid plans only | Free-tier images owned by Recraft |
| Ideogram | Per current paid terms | Verify tier before client typography deliverables |

A `licensing.yaml` maps each pipeline stage to its platform terms; the delivery skill refuses to package an asset whose generation record violates the register. Client contracts disclose AI-assisted visualization and define which deliverables are AI-derived vs. renderer-of-record.

### 12.3 Unit economics instrumentation

Every render batch logs: model/tier, tokens, GPU-minutes, gate pass-rates, human-revision count, wall-clock brief→approved. The corpus's headline claim — visualization cycles compressed from weeks to hours — becomes a measured KPI (see M-metrics, §14) rather than a slogan.

---

## 13. Implementation Roadmap

Phased so that deterministic guardrails always precede the autonomy they contain. Durations assume the current single-operator studio at part-time build capacity alongside client work.

**Phase 0 — Foundation & boundaries (Weeks 1–2).**
Initialize monorepo + LFS (`.gitattributes` before the first binary commit); root CLAUDE.md (≤200 lines); `settings.json` permission matrix; write and *test* the destructive-command and protected-path `PreToolUse` hooks (prove a blocked `rm -rf` actually blocks); scaffold folder tree + templates; migrate studio-vault v2.2 content into `knowledge/` unmodified (indexing comes next). Exit: a session inside the repo can read everything, break nothing.

**Phase 1 — Context, knowledge & skills (Weeks 3–5).**
Directory CLAUDE.md files + path-scoped rules; context-package convention in stage contracts; hybrid retrieval up (embeddings + BM25 + rerank) over the migrated vault; Thai code corpus ingested into `codes-th/` (Authority tier); first five skills (`intake-parse`, `concept-brief`, `usd-validate`, `material-lint`, `qa-report`); `.mcp.json` with vault + catalog (read-only) servers. Exit: knowledge-manager answers a code question with a correct citation; skills run end-to-end on a dummy project.

**Phase 2 — Generation pipeline (Weeks 5–8).**
Local ComfyUI + FLUX.1-dev environment (GPU: 16–24 GB VRAM class); the canonical `flux-depth-ipadapter` workflow JSON versioned; ComfyUI MCP wrapper (queue/poll/fetch/free); prompt registry + dual-track compiler + the three lexicons; `prompt-engineer` and `vision-reviewer` agents live; SketchUp→clay→depth-map procedure documented as a skill. Exit: brief → approved concept → structurally faithful render of a real past project, hands-off from dispatch to fetched image.

**Phase 3 — QA & vision loop (Weeks 8–12).**
Geometry engine + Gate 0 on the scene graph; deterministic validators (BRISQUE/NIQE, PBR ranges, ΔE00, homography, depth-contact checks); `thresholds.yaml` + golden set (≈50 designer-labeled images spanning pass/warn/fail); VLM judge with dependency-DAG VQA; **calibration sprint** to ρ ≥ 0.8 / κ ≥ 0.8; wire Gates 1–4 + the repair loop with its 3-iteration cap. Exit: a deliberately flawed batch is auto-caught, auto-repaired or correctly escalated, with scorecards.

**Phase 4 — Automation & commercial operations (Weeks 12–16).**
Full 12-agent roster + MARS/Reflexion wiring; Stop-hook verification loops; scheduled routines (nightly regression, doc-drift, memory consolidation) via SDK; review inbox + approval webhooks; upscale + deliverables chain; licensing register enforcement; onboarding automation. Exit: one real client project runs the full 00→08 pipeline; metrics captured.

**Phase 5 — Hardening & scale prep (Weeks 16+).**
Memory decay/temporal-tree consolidation live; APO flywheel (textual gradients, tournament promotion); LoRA fine-tune of FLUX on the studio's own approved portfolio; evaluate LangGraph+Temporal for durability once batch volume warrants; begin §16 options.

---

## 14. Prioritized Milestones

Priority: **P0** = the system is unsafe or non-functional without it · **P1** = core value · **P2** = compounding advantage.

| ID | Milestone | P | Phase | Acceptance criteria |
|---|---|---|---|---|
| M0.1 | Guardrails proven | P0 | 0 | Destructive ops + protected paths blocked in live test; audit log written; permissions deny→ask→allow verified |
| M0.2 | Repo + LFS + templates | P0 | 0 | Clone < 2 min w/o assets; binaries are pointers; project scaffolds in one command |
| M1.1 | Knowledge online w/ citations | P0 | 1 | 20-question eval: ≥ 90% answered with correct vault citation; zero uncited code values |
| M1.2 | Thai Authority corpus | P0 | 1 | Clearance/egress values retrievable metric-first from codes-th with source refs |
| M1.3 | Context discipline | P1 | 1 | Root CLAUDE.md ≤ 200 lines; rules fire only on matching paths (log-verified); asset dirs excluded |
| M2.1 | Structural render loop | P0 | 2 | Depth-locked render of a real unit: walls/openings match CAD by visual overlay; dispatch→fetch hands-off |
| M2.2 | Prompt registry + compiler | P1 | 2 | Dual-track payloads; model-conditional negatives; version labels + rollback demonstrated |
| M3.1 | Gate 0 geometry | P0 | 3 | Seeded violations (blocked swing, 800 mm corridor, collision) all caught pre-render |
| M3.2 | Judge calibration | P0 | 3 | ρ ≥ 0.8, κ ≥ 0.8 on golden set; re-validation procedure documented |
| M3.3 | Gates 1–4 + repair loop | P1 | 3 | Flawed batch: ≥ 80% auto-resolved ≤ 3 iterations; rest correctly escalated with critiques |
| M4.1 | Full pipeline on live project | P1 | 4 | Real client 00→08; human touches limited to approvals + creative direction |
| M4.2 | Routines + drift repair | P1 | 4 | Nightly regression green 14 days; injected doc drift auto-PR'd within one cycle |
| M4.3 | Licensing gate | P0 | 4 | Delivery blocked for a deliberately non-compliant asset; register covers all active platforms |
| M4.4 | Baseline economics | P1 | 4 | Dashboard: brief→approved hours, cost/final, gate pass-rates, revision count — vs. pre-AI baseline |
| M5.1 | Studio LoRA | P2 | 5 | Blind test: designer prefers LoRA outputs ≥ 70% on style fidelity |
| M5.2 | APO flywheel | P2 | 5 | Registry pass-rate improves release-over-release on fixed golden briefs |
| M5.3 | Memory longevity | P2 | 5 | Cross-project preference recall demonstrated; decay archives transients (spot-audited) |

---

## 15. Risk Analysis

| Risk | L | I | Mitigation (built into the architecture) |
|---|---|---|---|
| Geometric hallucination reaches a client → real-world build/liability failure | M | **Critical** | Gate 0 scene-graph math before render; depth-locked generation; homography/depth-contact checks; V-Ray renderer-of-record rule; contract language on AI visualization scope |
| Prompt-based security illusion (rules "asking" the model not to delete) | H | High | Principle 1: hooks + permission arrays only; CLAUDE.md carries zero security load; quarterly red-team of the hook set |
| Prompt injection via untrusted inputs (client PDFs, issue text, scraped specs) | M | High | Intake parsing in sandboxed subagents with no write/tool privileges; instructions found in documents are data, surfaced for human confirmation, never executed; environment scrubbing in routines; least-privilege tokens |
| Context thrashing (unpaginated tool dumps stall the agent) | H | M | Pagination mandatory on MCP endpoints; tool-result clearing; subagent isolation for deep reads; execution proxies |
| CLAUDE.md bloat / instruction-adherence decay | H | M | 200-line cap enforced by CI check; hierarchy + path-scoping; quarterly prune |
| Runaway loops / zombie agents burn budget | M | M–H | Iteration caps (3), agent-depth caps (2), per-stage token ceilings, Haiku routing for bulk work, cost dashboard alarms |
| Self-critique degradation (critic "fixes" correct work) | M | M | Green-Zone trigger only (low-confidence/validator-flagged); Red-Zone tasks skip reflection entirely; hard cap 3 |
| VLM judge drift after model updates silently changes quality bar | M | High | Golden-set regression nightly; re-calibration (ρ/κ) on any judge version change; thresholds change only via PR |
| Licensing violation in client deliverables | L–M | High | §12.2 register enforced by delivery skill; generation records stored per asset; annual terms review |
| Client-data privacy breach via cloud models | M | High | FLUX local for all plan-conditioned generation; metadata stripping for any cloud judging; `client-privacy.md` rule + PreToolUse blocks on `clients/**` exfil paths |
| LFS misconfiguration bloats history irreversibly | M | M | `.gitattributes` committed before first binary; pre-commit size hook; nightly pointer audit; retrofit documented as prohibited |
| Documentation drift → agent acts on stale truth | H | M | Auto-generated reference-map vs. curated strategy split; on-merge drift detection with auto-PR |
| Model/platform deprecation strands the prompt library | H | M | Registry taxonomy by intent, never by model; compiler isolates model-specific syntax (negatives, encoders) in adapters |
| Single-operator bus factor | H | M | Everything-as-code in one repo; contracts + docs make the system legible; scale path (§16) adds seats without redesign |
| Memory poisoning / wrong "facts" about a client compound | L | M | Passive extraction with provenance; weekly human-reviewed profile PRs; Authority tier always outranks memory |

*(L = likelihood, I = impact.)*

---

## 16. Future Scalability

The architecture is deliberately over-specified at the seams so growth is additive:

**Client-facing product (Surface B matures).** The Agent SDK path becomes a commercial app: end-clients explore variants of *their* unit through structured-output-only interactions (Zod/Pydantic schemas for room specs, palettes, budgets — the SDK re-prompts on schema violations so the frontend never parses prose), with OpenTelemetry cost/latency observability per user. The same knowledge, QA, and licensing layers serve both surfaces.

**Durable orchestration.** When batch volume or multi-day human-approval pauses make in-memory state risky, LangGraph models the agent graphs and Temporal supplies durable execution — LLM calls wrapped as retryable Activities, `interrupt()` + signals for approval waits that survive restarts. The stage-directory contracts map 1:1 onto graph nodes, so migration is mechanical.

**True 3D spatial layer.** OpenUSD graduates from asset format to live spatial context: the orchestrator queries USD metadata (dimensions, grids, asset bounds) as declarative JSON, the LLM acts as a topological solver emitting placement graphs, engines render procedurally, and AR walkthroughs write client edits back into the same version-controlled layer — closing the loop between generated concept and inhabitable model. 3D-scene-memory techniques (snapshot-based spatial memory) extend client memory into remembered *spaces*, not just preferences.

**Learning studio (weights, not just prompts).** The QA scorecards and human approvals are already preference data: RankDPO-style synthetic-ranked preference sets align the local FLUX toward the studio's taste; step-aware preference optimization targets early-step structure errors and late-step texture errors separately; studio-portfolio LoRAs become the house style as a shippable artifact. Judges distill into compact on-device models for the routine checks.

**Knowledge deepening.** GraphRAG over the vault (multi-hop reasoning across codes ↔ materials ↔ precedents); IFC/BIM ingestion as a first-class intake path; Brick-schema hooks if smart-building/FM services enter scope.

**Team scale.** New seats = new sparse-checkout profiles + per-seat `settings.local.json`; agent-team sessions (shared task lists, direct messaging) for parallel reviews once more than one human is directing; enterprise hosting + managed policy files when compliance demands it. Because every rule, prompt, threshold, and workflow is a versioned file, onboarding a second designer is a Git clone plus a permissions grant — the studio's judgment is already written down.

---

## Appendix A — Corpus-to-Blueprint Traceability

| Blueprint section | Primary source reports |
|---|---|
| §1 Architecture | Claude Code Architecture Design · Large Scale Project Organization · AI Context Engineering Architecture |
| §2 Agents | AI Design Studio Architecture (12-agent roster, MARS, Reflexion, self-critique paradox) · Claude Code Architecture Design (subagents, teams, workflows) |
| §3 Knowledge | AI Design Knowledge Systems (5-layer stack, retrieval, MCP) · Interior Design Knowledge Structuring (ontology, codes, materials, classifications) |
| §4 Memory | AI Design Knowledge Systems (Mem0/MemGPT, Ebbinghaus, H-Mem) · AI Design Studio Architecture (memory types) |
| §5 Context | AI Context Engineering Architecture (tiers, ICM, packages, compression, caching, security) |
| §6 Workflows | AI Context Engineering Architecture (ICM/MWP) · AI Design Studio Architecture (execution pipeline) · AI Studio Workflow Automation (phases) |
| §7 Structure | Large Scale Project Organization (tree, naming, MaterialX/USD, LFS, platform) |
| §8 Prompts | AI Image Prompt Engineering (XML, dual encoders, lexicons, registry, APO) |
| §9 QA | Automated Production QA Scoring Systems (nine pillars, thresholds, gates, judge governance) |
| §10 Vision loop | Automated Vision QA for Interiors (anchoring, DAG-VQA, spatial/photometric/material estimators, DPO) |
| §11 Automation | AI Studio Workflow Automation (hooks, ComfyUI API, n8n, webhooks, onboarding) · Claude Code Architecture Design (hooks, routines) |
| §12 Commercial | AI Interior Design Commercial Workflow (phased model stack, upscaling, licensing) |
| §13–15 Roadmap/Risks | Synthesis: roadmaps and anti-pattern/failure-mode sections across all reports |
| §16 Scalability | AI Design Studio Architecture (LangGraph+Temporal) · AI Context Engineering (OpenUSD) · Vision QA (DPO/SPO) · Knowledge Systems (3D memory) |

**Staged-source key (verbatim paths of the report titles used above).** Added 2026-07-13 so the
short titles in this table resolve to a file on disk and the provenance is checkable, not merely
asserted. Only the units whose content was traced into this blueprint are keyed here; the remaining
corpus reports (Automated Vision QA for Interiors · Automated Production QA Scoring Systems) are
cited by their own distilled `knowledge/` files, not by this appendix. (AI Image Prompt Engineering
and AI Interior Design Commercial Workflow were keyed 2026-07-13: their content IS traced into
§0/§1/§8/§12, so they belong in this key like the other seven.)

| Short title used above | Staged unit (verbatim path) |
|---|---|
| AI Context Engineering Architecture | `knowledge/_inbox/id-project-corpus/AI Context Engineering Architecture.pdf` |
| AI Design Knowledge Systems | `knowledge/_inbox/id-project-corpus/AI Design Knowledge Systems.pdf` |
| AI Design Studio Architecture | `knowledge/_inbox/id-project-corpus/AI Design Studio Architecture.pdf` |
| AI Image Prompt Engineering | `knowledge/_inbox/id-project-corpus/AI Image Prompt Engineering.pdf` |
| AI Interior Design Commercial Workflow | `knowledge/_inbox/id-project-corpus/AI Interior Design Commercial Workflow.pdf` |
| AI Studio Workflow Automation | `knowledge/_inbox/id-project-corpus/AI Studio Workflow Automation.pdf` |
| Claude Code Architecture Design | `knowledge/_inbox/id-project-corpus/Claude Code Architecture Design.pdf` |
| Interior Design Knowledge Structuring | `knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf` |
| Large Scale Project Organization | `knowledge/_inbox/id-project-corpus/Large Scale Project Organization.pdf` |

*End of blueprint.*
