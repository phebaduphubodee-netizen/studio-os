# DR-queue triage — six proposed topics, dedup'd against the repo (2026-08-04)

Provenance: 10-agent workflow (6 read-only dedup auditors + 4 literature lenses),
run 2026-08-04 from the builder session, on the six-topic proposal set from the
C2 (Cowork) landscape scan of the same date. Standing law applied: search our
own vault first; never re-research what the repo owns.

Queue verdict summary:

| # | Topic | Verdict | Queue as |
|---|-------|---------|----------|
| 1 | Inspection blindness / habituation | PARTIAL_COVERED | DR entry — bundle with the queued SEIG deep-read (same consumer, same proposal set) |
| 2 | Bedding mass / drape feedstock | PARTIAL_COVERED | DR entry — NEW unit `nlm-bedding-mass/` (extend-closedtube premise REFUTED) |
| 3 | Palette color/reflectance anchors | PARTIAL_COVERED | DR entry — URL-mandatory quarantine in the prompt |
| 4 | Bedroom lighting of sellable photos | PARTIAL_COVERED | NOT a new DR — asks to existing notebooks 79476082 + a5a43395 |
| 5 | Camera language of interior sales photography | PARTIAL_COVERED | Measurement-first (anchor sweep with existing tools); DR deferred to first no-target camera |
| 6 | Asset source map / Thai furniture brands | REROUTE | Do NOT queue as DR — practitioner ask + direct per-brand web verification |

Quarantine rule (all entries): a number with no section/URL attribution does not
enter `knowledge/` — it stays quarantined in `_inbox/` until the verification
rung (Cowork opens the page/DOI per R7c) clears it.

---

## Topic 1 — Inspection blindness / habituation in visual QA

**Verdict: PARTIAL_COVERED.** The repo already owns the phenomenon at
practice-report tier and has the countermeasures WIRED as procedure:

- `knowledge/_inbox/nlm-process-rules/process-control-rules.md` — "familiarity
  blindness", builders catch 30-50% of own defects vs 70-90% independent.
- `knowledge/brand-standards/iteration-control-and-review-gates.md` R3/R4/R7 —
  the critic ladder is itself the fresh-eyes countermeasure, adopted + wired.
- `templates/cold-critic-prompt.md` + gate-artifact C2 slot — fresh-eyes
  rotation is structural, every render.
- `qa/reproduction-curriculum.md` ~1096-1185 — habituation NAMED and twice
  measured in TRN-002; STRANGER SWEEP adopted (N unset, no cadence, no pin).
- `qa/benchmark-sellability.md` + `look_bench.py --blind` — forced-choice and
  blind-rank instruments already built.
- r4b in-house data point: a ~1-hour gap does NOT restore the builder's eye.

**Real gaps (what the research is FOR):** literature mechanism names + effect
sizes (change blindness, satisfaction of search, low-prevalence effect — repo
vocabulary is home-grown); image inversion/mirror-flip/blur as detection
restorers (ZERO repo mentions — the one countermeasure with no in-repo
analogue); STRANGER SWEEP parameterisation (N, cadence, zone ordering);
time-away decay curve; 2AFC-vs-rating psychophysics; double-read incremental
catch rates; label-withholding as countermeasure.

**Sharpened questions (queue payload):**
1. What does the visual-perception literature name and quantify for a maker repeatedly inspecting their own image over many rounds — change blindness under repeated exposure, expertise/schema-driven viewing, semantic satiation — and after roughly how many exposures does defect-detection measurably drop?
2. Satisfaction of search: by how much does finding one defect suppress detection of remaining defects in the same image (radiology numbers), and which interventions (checklist-driven second read, forced re-scan of already-cleared zones, structured reporting) measurably restore second-defect detection?
3. What controlled evidence exists that viewing an image inverted, mirror-flipped, blurred, or at changed scale restores error detection for a habituated viewer — and which transformation shows the largest measured effect?
4. How much time away, or how much context change, does a creator need before their defect-detection recovers toward fresh-viewer levels — and is there evidence that breaks on the order of an hour do NOT restore it?
5. In psychophysics, how much more sensitive is two-alternative forced choice (or paired ranking) than single-stimulus absolute rating for small quality differences, and does side-by-side vs sequential presentation change detection rates?
6. In high-volume visual inspection QA, do enforced systematic scan patterns or per-zone checklists measurably reduce misses in frequently-viewed regions versus free viewing, and at what false-alarm and time cost?
7. What is the measured incremental defect-catch rate of a second independent reader (radiology double-reading, print proofing, VFX dailies), and what reviewer-rotation cadence or independence structure does the evidence support?
8. Does naming/labelling an object before inspection ("this is a pillow") measurably reduce detection of its FORM errors, and is withholding the label from the inspector a validated countermeasure?

**Vehicle:** literature evidence (scite once quota restores 2026-08-17 / PAYG;
Crossref REST worked as fallback TODAY — see
`docs/research/2026-08-04-inspection-blindness-evidence.md`, 7 DOI-backed
findings already in hand with effect sizes QUARANTINED pending full-text) +
one practitioner ask via owner (how real archviz/print studios run fresh-eyes
rotation). NLM DR only as fallback. **Coordinate with the queued SEIG
deep-read** — the t1 dedup confirmed the queue entry cites the same 2026-08-04
proposal set and the same consumer (the C1-pattern question); share a firing
decision, don't fire separately.

**Fire condition:** at the TRN-002 blockout→materials/cloth/light transition,
bundled with the SEIG read. Already past a DR self-initiation trigger
(C1-blind-at-gate is on its third occurrence-class round). Mandatory at latest
BEFORE the STRANGER SWEEP gets parameterised into a test-pinned rule.

**Scope discipline:** research the evidence base and parameters ONLY — do not
let it re-derive the ladder (rotation, forced-choice, zone-sweep all exist).
The genuinely novel element with zero repo presence is image inversion/flip.
Check any answer against the in-house data: 1-hour gap insufficient; missed
zones are the MOST-looked-at ones; "knowing-what-it-is" and a pre-excusing
prompt sentence are documented blinders.

---

## Topic 2 — Measured bedding mass / drape feedstock

**Verdict: PARTIAL_COVERED — and the proposal's extend-premise is REFUTED.**
`knowledge/_inbox/nlm-cloth-closedtube/` contains ZERO bedding content (grep
duvet|tog|fill|loft|bedding|pillow: no matches — it is purely closed-tube
garment-sim mechanics) and is already DISTILLED (ledger row 172) into
`knowledge/rendering/cloth-sim-closed-tube-garments.md`, whose own Gaps section
says "nothing on materials other than cotton-like wovens". Correct shape:
**NEW inbox unit `nlm-bedding-mass/`**, cross-linking the closed-tube unit for
solver mechanics only.

**What the repo already owns:** the GEOMETRIC half — target-measured duvet
envelope (spec_r5: crest 710 in band 626..734, extent 540, hem-to-ledge);
anchor-derived cues (reference board: slump 30-45°, loft→cell 42mm/solidify
18mm); mesh-density floors (ground-truth study: pillow ≥3.1k polys); working
overhang machinery (`drape.py` derives drop from `hang_to`); the R1 halt that
makes this the named consumer (r5: duvet reclassified free-form drapery, R8;
"reads as folded fabric" transferred to the CLOTH phase). Discord thread
(MY-DATA-PEAT …/001_Sketchup-แบ่ง-Model/thread.md ~121) already points at a 3D
Warehouse pillow collection — the research must serve ACQUIRE sizing/scale
assertion, not only sim parameterisation.

**Real gaps:** tog↔fill-weight↔fill-power→settled loft (mm) by fill class;
duvet areal density/total mass by construction; fold compression factor
(stack height vs naive layer sum); industry overhang/drop conventions
(`hang_to` is an untraced prior); pillow ILD/compression under head-weight
load; fabric g/m² + bending rigidity/Cusick drape coefficient → Blender
mass/bending mapping (the FABRIC table in `drape.py:153-164` self-describes as
retuned Blender defaults — the exact prior to replace); quilted/baffle-box
composite representation.

**Sharpened questions (queue payload):**
1. What published mappings exist from duvet tog rating to fill weight (g/m²) and to settled loft thickness in mm, per fill class (down, feather, microfiber, wool), across the common 4.5 / 10.5 / 13.5 tog bands?
2. How does down fill power translate to loft height and areal density — what crest loft in mm does an all-season double/queen duvet typically present, and how much does the loft compress at the hem roll and under a resting hand?
3. When a duvet is folded at the foot of a bed (half-fold, third-fold, turned-back fold), what stack heights result as a multiple of single-layer loft — how much does self-weight compress the stack below the naive layer sum?
4. What drop/overhang length conventions do bedding manufacturers and styling guides use at bed edges — comforter vs coverlet vs bedspread drop bands in mm, relative to mattress thickness bands (roughly 200-350 mm)?
5. What indentation depth and slump behaviour do the major pillow fill classes show under a head-weight load band of roughly 3-5 kg, and what lean-back angle bands do styled/propped pillows settle at against a vertical support?
6. What are published areal weights (g/m²) and bending rigidity / Cusick drape coefficient values for common bedding fabrics, and what accepted procedure maps these onto cloth-solver mass and bending stiffness parameters?
7. How do production cloth-simulation practitioners represent a quilted, batting-filled duvet — loft via pressure or internal springs, shell thickness, quilting-seam constraints, edge-roll formation — and what parameter bands do they publish?
8. What turned-back fold depth and visible-sheet-reveal proportions do hotel/staging bedding standards specify for a made bed?

**Vehicle:** (1) measure own anchor corpus FIRST — drop/stack/slump/turn-back
are measurable locally with the live backprojection sweep, free, and R4b wants
the anchors open anyway; (2) NLM full DR, NEW notebook, for the industry-physics
half only; (3) optional practitioner ask on styling conventions ("แต่งเตียง
ปล่อยชายยาวแค่ไหน"). Caution from the old unit: NLM `--iterate` drifts — use
explicit follow-up asks.

**Fire condition:** at TRN-002 cloth/materials phase OPENING, before the first
duvet bake (DR-PULL triggers 2 and 4 already on file via the r5 R1 halt). The
anchor-measurement leg can fire earlier in any budgeted session.

---

## Topic 3 — Real-world color/reflectance anchors (cream–oak–black palette)

**Verdict: PARTIAL_COVERED — queue-worthy; the repo declares this exact gap
three times in its own voice** (`color-composition.md:238` "no paint-system
values (LRV/NCS/Munsell) in the color sources"; `residential-materials.md:187`
no numeric LRV targets; `render-defaults.md §7` roughness bands + F0 tables are
do-not-invent GAPs). The veneer-figure distinctness claim VERIFIED (that unit
is leaf-geometry only, zero color content).

**Key facts:** every class already has a LIVE preset (`material_presets.py`)
but the values are design-intent/LOOK-chosen, unsourced;
`bsdf-material-presets.md` is REFERENCE tier whose own header forbids gating a
deliverable until promoted via PR with a named source — **this research IS the
promotion path**; and the **delta-E gate (`brand_delta_e00`) is built, proven
against Sharma 2005, and has NEVER scored** because no `--brand-palette` file
exists — the research output is literally that missing input file. TOA
Supershield is already the studio's named default paint brand (template only,
no values). The ground-truth study caveat rides along: pros drive roughness
per-pixel via maps, so researched flat ranges anchor map MEANS, not endpoints.

**Sharpened questions (queue payload):**
1. For Thai-market interior emulsion lines (TOA, Beger, Jotun Thailand), which published cream/off-white color codes carry manufacturer LRV values in the ~75-90 band, and what are the exact LRV and hex/sRGB (or NCS) values per code — each value with the manufacturer page URL it came from (no URL = quarantine)?
2. What is the published relationship between paint LRV and CIE luminance Y / linear reflectance, and the accepted procedure to derive an sRGB base-color triple from an LRV plus hue description — with a citable source for the formula?
3. What base-color ranges (sRGB or L*a*b*) and roughness ranges do scan-based PBR libraries and published references report for white/European oak veneer under clear lacquer vs oil finish, with a source URL per value?
4. What 60-degree gloss-unit bands do powder-coat suppliers publish for matte, satin, and gloss black architectural powder coat, and is there a sourced conversion from gloss units to microfacet/Principled roughness?
5. What measured complex-IOR or F0 values exist for brass (polished vs brushed/satin), and what base-color, roughness, and anisotropy ranges do measured material libraries publish for satin brass hardware — with source URLs?
6. What L* / sRGB band do measured references give for powder-coat black and near-black factory finishes, and does any published source support a reflectance floor above pure black consistent with the ~30-sRGB texel floor already enforced in the pipeline?
7. What batch-to-batch and inter-sheen color tolerance (ΔE00 or ΔE*ab band) do interior-paint manufacturers publish, to calibrate whether a pass≤1.0 / warn≤2.0 gate against a swatch-derived anchor is achievable in practice?

**Vehicle:** (1) NLM full DR, NEW notebook, URL-mandatory quarantine stated IN
the prompt (the ledger records a prior DR fabricating exactly this class of
fact); (2) local anchor-corpus measurement of as-rendered cream/oak/black sRGB
ranges in delivered work; (3) practitioner ask: which TOA/Beger cream codes
Thai studios actually spec (the fan-deck question). Do NOT route to a5a43395 —
it has answered this class as "not covered in the sources".

**Fire condition:** when TRN-002 blockout closes and its MATERIALS phase opens
(DR trigger 4 + R4b: today no sourced color reference of these finishes exists
to open beside a crop). Must complete BEFORE the first material build round.
Independent second trigger: the moment any preset value is about to gate a
deliverable via `brand_delta_e00`.

**Scope discipline:** fetch sourced values + conversion methods ONLY — preset
structure, the 30-240 band, ΔE00 math, and the two-albedo-band mismatch are all
owned in-repo. Output lands as sourced anchors that PROMOTE/correct existing
preset rows (per bsdf-material-presets.md's own authority header), plus the
palette file the gate ingests.

---

## Topic 4 — Bedroom lighting scheme of sellable photographs

**Verdict: PARTIAL_COVERED — do NOT commission a new DR.** The lumen/CCT half
is already answered at REFERENCE tier (`residential-lighting.md`,
`lumen-method-and-fixture-placement.md`: bedroom 108-215 lux general / 323-538
bedside, 2700-3000K, Kelly 4-layer incl. cove, accent:ambient ~3:1, downlight
spacing rules — plus 30 real IES files local). The four downlight-count rounds
RESOLVED in r5 as our own clay-light artifacts (spec masses = exactly 4) — a
counting/render problem, not a norms gap; new research would not have prevented
it. element5 already built an owner-approved cove+sconce scheme — the consumer
needs verification, not first design. The ground-truth study already measured
the quantitative half of practicals-vs-ambient (our 10:1 vs 191-2500:1
delivered-grade; target ≥100:1).

**Real gaps:** photographer PRACTICE (which layers on/off/dimmed for a hero
frame, dusk vs daylight conventions, single-exposure vs flambient/HDR); cove
photometric norms (lumens-per-metre bands — e5's 10 W/m was derived, not
researched); which layer dominates marketing images; second-source verification
of the single-source numbers every file flags; bedside practical output/shade
luminance and sconce mounting-height norms; measured practical:ambient ratio in
delivered frames (answerable LOCALLY from the anchor pool).

**Sharpened questions (queue payload):** the 7 questions cover exactly those
gaps — layer on/off practice for hero shots; exposure approach + practical-glow
luminance ratio; cove lumens-per-metre + fascia geometry vs gradient length;
which layer dominates marketing bedrooms / when downlights are omitted;
corroborate-or-amend the flagged single-source values (3:1, 3:1, 20:1,
108-215, 323-538, CRI≥90); bedside practical lumen + sconce mounting band;
Kelly classification of cove + cove-with-downlights pairing guidance.

**Vehicle:** (1) ask EXISTING notebook 79476082 (315-source lighting corpus:
Steffy, Livingston, ERCO/Kelly, IES tables) for verification + cove norms;
(2) ask EXISTING notebook a5a43395 (holds Shulman + Birn) for the
photographer-balance questions; (3) measure anchor pool locally for the
practical:ambient ratio; (4) practitioner ask "ถ่ายรูปเปิดไฟดวงไหน". Asks are
~44s single-flight vs a full DR cycle, and the corpora already hold the
authorities a DR would re-scrape. Statutory floors: mr39 is LAW, outranks all.

**Fire condition:** at TRN-002 light-phase opening (owner of the named
LIGHT-phase debt in spec `downlight_table`), before the first light build. Not
during blockout r5. The anchor-ratio measurement can run earlier as instrument
work; the two notebook asks fit one session's ≤10-ask budget. Landing spot for
answers: `residential-lighting.md`'s own GAP list (extend files, not a new
inbox unit — both prior lighting units are fully audited).

---

## Topic 5 — Camera language of interior sales photography

**Verdict: PARTIAL_COVERED — measurement rung comes FIRST, DR deferred.** The
repo's camera knowledge is deliberately ledgered (`render-quality.md §4` keeps
four lens bands SEPARATE and records one retraction for over-reading
corroboration — any new numbers must enter that ledger, never merge). The gap
half is validated: `cycles-lighting-camera-presets.md §8` itself declares "no
values for the non-hero camera angles … do not interpolate".

**The load-bearing reframe:** the anchor pool's own camera language has never
been measured, and the toolchain already exists — `trn002_lines.py` (VP fit) +
`trn002_station.py` (recovers focal/horizon/shift/height from a single image,
proven twice). Sweeping the 704 anchors is engineering, not research: local-only,
no DR budget, and 704 delivered frames beat any document corpus. It would also
be the first instrument-grade check of the studio's two constants (eye 1.15 m
rests on n=1; `RENDER_SHIFT_Y=-0.10` on no recorded evidence at all).
Constraint: per-room-type stratification is BLOCKED until the designer fills
the `room_type` worksheet columns (machine refuses to assign; first sweep
reports whole-pool distributions).

**Real gaps for the eventual DR:** per-room-type/size focal + height presets
(only one data point exists: 26 mm small-room); when professionals deviate from
the 1.0-1.2 m band; vertical-shift/horizon-placement norms; one-point vs
two-point selection criteria; listing vs editorial register; orientation/aspect
per room type; quantitative pro-vs-amateur signatures usable as authoring-side
gates (8 sharpened questions on file in the triage output).

**Vehicle, in order:** (1) anchor sweep with existing tools (idle-slot work);
(2) practitioner ask in parallel (questions 1-3 are exactly what the working
designer answered better than a 154-line DR); (3) NLM full DR (new notebook)
only for the normative why/when the corpus cannot answer — its lens numbers
enter the §4 band ledger. Do NOT re-ask a5a43395 (camera turns spent, ledger
rows 81/127).

**Fire condition:** NOT during TRN-002 (that lane solves its camera FROM the
target; remaining phases consume none of this). Anchor sweep: any idle slot
after TRN-002 closes. DR + practitioner ask: the first camera that must be
AUTHORED with no target (next real project's 04_visualization, or a fresh
PRJ-2026-002 beauty pass) = DR trigger "first build of a domain class".
Designer filling `room_type` on 2-3 buckets pulls the measurement rung forward.

---

## Topic 6 — Asset source map + Thai furniture brands

**Verdict: REROUTE — do not queue as a DR.** ~70% already answered, and the
missed prior art is decisive: the proposal's check-list named `LICENSING.md`
but missed **`docs/research/2026-07-11-furniture-sourcing-DR.md`** — a second,
far closer prior DR that already ranks Thai retailers by published dimensions
(Index Living Mall best; HomePro weak; Lazada/Shopee none) and explicitly lists
the six unchecked brands (SB Design Square, Modernform, Koncept, Boonthavorn,
Winner, IKEA TH). `style-and-asset-references-discord.md` is already a
practitioner-sourced map (Cotto/Kohler/TOTO CAD portals, 17 curated 3D
Warehouse collections). The sourceability gate + warehouse.py + assets.py are
built. Fabrication precedent is structural: BOTH prior engine-run DRs on this
topic had licence/price claims overturned on verification — the reroute is the
twice-paid lesson, not preference.

**Residue (narrow, factual, web-or-human-verifiable):** per-brand verification
of the six unchecked retailers (downloadable 3D? format? terms?); IKEA TH
structured dims/article numbers; which Thai FURNITURE brands publish per-SKU
dimensioned drawings (the sanitary-brand shop-drawing pattern has no
furniture-side equivalent recorded); what Thai viz studios actually use beyond
the one practitioner sentence; Hafele TH portal EULA (flagged unverified);
the declared 3.8/4 licence re-reading debt.

**Vehicle:** practitioner ask via owner (primary — near-free, rides along
whenever he next talks to his designer friend) + direct per-brand WebFetch
verification in the 07-11 tracer pattern, recorded verbatim, staged as an
EXTENSION of the 07-11 DR's open-question list + LICENSING.md's table via
`_inbox` (the correction path at
`knowledge/_inbox/2026-08-01-sourcing-rule-change-knowledge-correction.md`
already exists). NLM DR contraindicated for licence/price facts. Note: the
07-12 claim "no Thai retailer publishes downloadable 3D" predates the
2026-08-01 rule change and was never per-brand verified — treat as hypothesis.

**Fire condition:** not now. Fire when (a) an R8 acquisition fails and becomes
a DECLARED GAP / procurement decision, or (b) the next client-facing FF&E cycle
hits a Thai SKU needing a brand model or per-SKU drawing.

---

## Literature evidence already in hand (topic 1 support)

See `docs/research/2026-08-04-inspection-blindness-evidence.md` — 7 DOI-backed
findings (satisfaction of search, invisible-gorilla in experts, expertise
INCREASING inattentional blindness, low-prevalence effect, double-reading
yield, radiology error epidemiology) retrieved live from Crossref after the
scite MCP quota exhausted (250/month; resets 2026-08-17, or PAYG at
scite.ai/users/me/subscription). Effect-size NUMBERS are quarantined pending
full-text verification — the DOIs and bibliographic records are verified real.
Three lenses (change-blindness mechanisms, countermeasures, vigilance/
prevalence) returned empty rather than fabricate; their query plans are
archived in the same file for the re-run.
