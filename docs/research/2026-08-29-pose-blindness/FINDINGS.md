# Pose blindness — why a whole object can be a quarter-turn wrong and every rung stays green

**Fired 2026-08-29** on the owner's order, after he had to say twice that the TRN-003
island was laid the wrong way. Channel: **vault first, then web.** NotebookLM was NOT
fired — see "why no NLM DR" at the bottom.

---

## 0. THE FIRST FINDING IS THAT WE ALREADY HAD THE ANSWER, THREE TIMES

The red memory `read-our-own-studies-before-declaring-a-gap` fired **three times in one
session**, and each time the answer was on this disk before I started looking:

| What I was about to research | Where it already was | Age |
|---|---|---|
| Why local checks pass while a big structural error survives | `docs/research/2026-08-08-upgrade-dr/ANSWER_gemini_q8-photo-match-verification_grounded.md` **§5, titled "THE FAILURE WE ARE LIVING IN"** | 21 days |
| Why the eye stops finding defects in its own work | `ANSWER_gemini_q9-inspection-blindness_grounded.md` | 21 days |
| What kitchen walkway is acceptable | `knowledge/ergonomics/residential-clearances.md` lines 97–98 | months |

That third one is the sharp one. My wrong island produced a **−420 mm** walkway and my
"corrected" one **1094 mm**. The vault has held the answer the whole time:

> opposing counters — single cook, no circulation behind: **1219 mm** (NKBA)
> opposing counters — multi-cook, extended drawers + circulation: **1524–1676 mm**

So the number that convicts BOTH islands was already written down, in our own knowledge
base, and **nothing in the pipeline reads it.**

## 1. fSpy's own documentation names my exact failure

From q8 (grounded, 27 sources + primary):

> "when the line segments used to define a vanishing point are near-parallel, the
> vanishing point position cannot be computed accurately; **a larger angle between the
> lines yields better results**" — fSpy, *Basics*

> two-point perspectives can be "horribly troublesome" for determining focal length,
> as it relies on the **less constrained position of the principal point**

Both are precisely what I did: I matched the island's chord (VP at 7711) to the window
transom (VP at 7917) — two near-parallel lines thousands of pixels off-frame — and I
assumed the principal point sat at image mid-width.

## 2. And the fix is textbook, with one correction to what I proposed

Standard practice for ill-conditioned vanishing points is an **angular constraint**:
compare the angle between the two supporting lines before using them, and if it is under
a threshold, **do not let them contribute** to the vanishing point at all.

**The correction to my own proposal.** Yesterday I said "report the VP's conditioning /
uncertainty and refuse VPs far off-frame". The literature says that is the wrong measure:

> the covariance of the VP in image space is less meaningful due to camera projective
> distortion — **a large covariance of a VP at infinity or very far away does not
> necessarily mean an inaccurate estimation**

A VP legitimately sits at infinity when the lines really are parallel to the image plane.
The thing to gate on is **the angle between the supporting line segments**, not how far
off-frame the answer lands.

## 3. The drum trick has a name, and it is a research area

What settled the island — two identical cylinders at two depths — is
**recurrence / translational symmetry in a single image**:

* Criminisi, Reid & Zisserman, *Single View Metrology* (ICCV 1999 / IJCV) — the base:
  3D affine measurement from one view given a reference plane's vanishing line, a
  vanishing point off that plane, and one known length.
* *Novel 3D Scene Understanding Applications From Recurrence in a Single Image*
  (arXiv 2210.07991) — repeated coplanar regions give parallel scene lines, and therefore
  a vanishing point, **directly**.

This is a *better-conditioned* estimator than edge fitting, because two repeated objects
over-determine the direction and their sizes cross-check their depths. We have never used
it. It answered in five minutes what an hour of edge fitting got backwards.

## 4. "Is it turned the right way" is a solved measurement with a standard metric

The field is **6DoF object pose**, and it has exactly the rung we lack:

* **angular distance** — the smallest rotation aligning the estimated pose to the
  reference pose. A single number for "how far is this object turned from where it should
  be". 90° would have printed.
* **ADD / ADD-S** — mean vertex displacement between the two poses (ADD-S for symmetric
  objects, which a racetrack island is about one axis).
* the workflow is **render-and-compare**: iterate the model's pose until its render aligns.

## 5. Someone HAS built the loop — the owner's hunch was right

| System | What it is | Status here |
|---|---|---|
| **SEIG — "Thinking in Blender"** (arXiv 2606.02580, Cornell) | staged executable inverse graphics: a VLM writes Blender code, a **verifier renders and compares to the target**, stage by stage. Order **scaffolding → geometry → materials → composition → lighting**; budgets geometry 5 / material 3 / composition 3 / lighting 2 | **already deep-read 2026-08-08**; produced `coverage_check.py` |
| **VIGA** (arXiv 2601.11109, project site) | code–render–inspect loop. **+35.32% BlenderGym, +124.70% BlenderBench** over one-shot. States plainly: *"VLMs inherently lack fine-grained spatial grounding in one-shot settings"* | not read |
| **IG-LLM** (github.com/kulits/IG-LLM, TMLR 2024) | public code for LLM-driven inverse graphics | not read |
| **BlenderGym / BlenderBench** | benchmarks for exactly this task | not used |

Note SEIG's stage order is **the same order 3D Shaker teaches**, arrived at independently
by a research group and by a working studio.

## 6. The blindness itself is a measured, named class — it is not my carelessness

* *"VLMs inherently lack fine-grained spatial grounding in one-shot settings"* (VIGA).
* Models "struggle to correctly predict changes in relative position, **orientation**, and
  visibility when the egocentric viewpoint shifts, indicating **a lack of a reliable
  internal spatial representation**".
* Performance collapses on non-canonical orientations (flipped views).
* ICLR 2026: *Perspective and Rotation as a Lens on Spatial Reasoning*.
* Mitigations named in the literature: **MindJourney** (test-time scaling) and
  **ViSA — Verification through Spatial Assertions**, which grounds the check in
  *"verifiable, frame-anchored micro-claims."*
* And this, which is the cheapest thing in the whole report: in that literature,
  **rotation tasks are defined relative to a TOP-DOWN VIEW.**

## 7. WHERE OUR HOLE ACTUALLY IS

08-08's triage T6 built `pipeline/scripts/coverage_check.py` and wired it into
`rule_gate`. It asks: *which object that the reference shows has no mass in our scene?*

**That is PRESENCE. My island was present.** It was named, it was built, it was in the
manifest, and it was turned 90°. Every rung went green.

Nothing in this repo asks about **pose**, and nothing reads the clearance table.

---

## LANES (ranked by what they would have caught today)

1. **`pose_check.py`** — for every mass with a reference correspondence, report the
   **angular distance** between its axis in our scene and its axis measured in the plate.
   Threshold blocks. This alone convicts the island at 90°.
2. **`clearance_check.py`** — every pair of masses a person passes between: gap ≥ 0 is a
   hard fail, and gap below the vault's own figure for that pair type is a REVIEW row.
   **Consumes `knowledge/ergonomics/residential-clearances.md`, which currently has no
   reader.** Convicts the wrong island (−420) and flags the corrected one (1094 < 1219).
3. **PLAN VIEW as a deliverable of every reproduction round.** Orientation is degenerate
   in perspective and unambiguous from above; the literature defines rotation that way.
   Cheapest catch in the list.
4. **Angular-constraint gate in `edgefit` / any VP code** — refuse contribution from line
   pairs under an angle threshold. Gate on the **angle between the lines**, not on the
   VP's distance off-frame (§2).
5. **Recurrence estimator** — when two instances of one component exist, use them for
   direction and treat the edge fit as the weaker second opinion, not the first.
6. **T7, still unadopted since 08-08** — SEIG's verifier returns a *numbered, stage-scoped
   checklist of discrepancies*. Ours asks for free prose. Needs an owner order.

## Why no NLM DR was fired

The repo's ladder is vault → NLM ask → full DR, and **NLM fires on vault GAPS**. The vault
answered §0–§2; the web answered §3–§6 because "is the code public / does this technique
have a name" is a question a search engine answers directly and a corpus does not. Firing
a DR here would have added to the **39 of 61 DRs that are write-only** rather than
subtracting from it. The one thing genuinely unsourced — a published archviz QA practice
that checks pose rather than presence — came back empty from both channels, and that is
recorded as an absence, not filled with a guess.

---

# WHAT WAS BUILT — the same day, on his order

> **"ทำให้หมดเลย ไม่ต้องรอถาม ผมจะไปนอนแล้ว"** — 2026-08-29

All six lanes, plus one that the work itself uncovered. Recorded as a row:
`qa/owner-orders.json` → `ORD-2026-08-29-pose-blindness-six-lanes`.

| # | Lane | Built | Wired into | Tests |
|---|---|---|---|---|
| 1 | pose | `pipeline/scripts/pose_check.py` | `rule_gate.check` + `check_room`, both entry points | 23 |
| 2 | clearance | `clearance_check._kitchen` + `Item.penetration_to` + `Item.z_apart` | already in `make_all`, now reads `kitchen_NKBA` | 91 (8 new) |
| 3 | plan view | `pipeline/scripts/planview.py` | `rule_gate.audit_planview` makes the artefact MANDATORY | via the lane driver |
| 4 | angular constraint | `pipeline/scripts/edge_direction.py` + `vanishing_check.MIN_AXIS_ANGLE_DEG` | `pose_check` imports its constants | 14 |
| 5 | recurrence | `pipeline/scripts/recurrence.py` | `pose_check` DERIVES `ref` from it instead of accepting a typed one | 14 |
| 6 | T7 | `pipeline/scripts/critique_schema.py` + the prompt + the C2 agent def | `rule_gate.audit_critique_form` | 16 |
| + | the rule with no reader | `pipeline/scripts/rules_reader_check.py` | `rule_gate.check` (blocking) and `plan_status` (every session open) | 14 |

## The finding the build itself produced, which was not in the research

Lane 2 was supposed to be a new file. **`clearance_check.py` already existed**, had
existed since the INTERIOR-AI port, and `dimensional_rules.v0.2.json` had held
`kitchen_NKBA.island_clearance_all_sides` — 1067–1219 mm, all sides — since
2026-07-02. Nothing read it. The audit that followed:

> **51 of the 75 rule keys in that file had no reader in any script in this repo.**
> Whole blocks at zero: `kitchen_NKBA` 7/7, `bathroom` 6/6,
> `anthropometric_basics` 5/5, `doors_and_openings` 4/4.

That is this repo's oldest defect, one layer further down than it had ever been
found: 357 critic items filed against ~22 built · 61 DR units with 39 write-only ·
21 gate artifacts with 2 owner verdicts · 6 skills that fired for two days and went
54 days unused — **and now the rules file itself.** Writing a number into a rules
file feels like building a guard and is not one. `rules_reader_check.py` is the
ratchet: the count may shrink and may never grow, so a NEW rule added with no
consumer fails the gate. It is 44 today, down from 51.

## And a correction to the fix this report proposed

§2 above says the gate should be the angle between supporting segments, not the
VP's distance off-frame. Building it found the sharper version:

**an angular FAMILY-ASSIGNMENT test would not have caught this.** On the real
numbers the island chord sits **0.03 deg** off family B's vanishing ray and 6.4 deg
off family A's — it is a textbook member of B by any test. The chord was a perfectly
good member of a family whose vanishing point was garbage. The load-bearing check is
CONDITIONING, computed before any assignment is allowed to mean anything: family A
(cabinetry) measures **25.97 deg** between its widest pair and passes; family B
(glazing + island) measures **4.24 deg** and is refused. B is the one that was wrong.

`vanishing_check.py` — written the day before from the same tutorial — already had a
conditioning refusal, and it would have passed family B. Its threshold is the scaled
determinant of the normal equations at `1e-6`, which for two lines is exactly
sin²θ: **it refuses only pairs within 0.057 deg of parallel.** Numerically correct,
dimensionally meaningless, and 175x below the angle that broke the frame. It now
carries the angular gate too.
