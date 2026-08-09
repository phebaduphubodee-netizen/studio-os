# Rebelway "AI For Interior Design" (Fadi H. Kacem) — what their workflow is, and what of it is ours

Date: 2026-08-09 · Trigger: owner watched the course trailer (youtu.be/31PU7v4J-Ys) and asked
what is useful. **He is not enrolling.** This is a reconstruction of the method from the public
syllabus + the underlying open tooling, not course material.

Course facts of record: 7 weeks, 13+ training hours, $498 (or 3×$166), skill level *beginner*,
hardware "mid to high-end GPU". Source: <https://www.rebelway.net/ai-for-interior-design>.

---

## 1. The syllabus, verbatim, and what each week actually is mechanically

| Wk | Title (verbatim) | The mechanism underneath |
|----|------------------|--------------------------|
| 1 | Setup ComfyUI locally · node basics · **integrating Qwen Image Edit** | Local instruction-edit model, 20B MMDiT, **Apache-2.0** |
| 2 | **Sketch to render** · hand-sketch + prompt structure · translating **CAD and 3d art** to different mood/style/lighting · watercolour and **SketchUp model** | img2img/instruct-edit with the input image carrying the structure; no ControlNet strictly required — Qwen-Edit is instruction-conditioned on the source image |
| 3 | Custom **furniture integration** · multi-input / mood-board · **"Using a 3d Model to Control placement, scale and orientation"** | Qwen-Image-Edit-2511 multi-image: 1–3 reference images (product + scene) composited by the model; the 3D model is a *proxy that owns the geometry* |
| 4 | Camera control over a flat image · multi-angle by prompting · by **3D reference** · by **LoRA + custom nodes** | `Qwen-Image-Edit-2511-Multiple-Angles` LoRA — 96 canned positions (4 elevation × 8 azimuth × 3 distance), trained on ~3000 Gaussian-splat renders |
| 5 | **Relighting** by prompt + LoRA · **people integration** from reference · pose/placement control | `dx8152/Qwen-Image-Edit-2509-Relight` and `Multi-Angle-Lighting` LoRAs (light direction as a prompt token / luminance map) |
| 6 | **Nano Banana** inside ComfyUI — the whole course again through the API | Google `gemini-3-pro-image-preview` ("Nano Banana Pro") via ComfyUI partner/API nodes |
| 7 | Bonus: **the ultimate upscaler** (Flux model), 10K–11K | Tiled diffusion upscale (Ultimate SD Upscale / SUPIR class) — resolution by *tiles*, so VRAM is bounded |

**Read the shape, not the chapters.** The whole course is one move repeated: *the geometry is
supplied by something cheap and dumb (a sketch, a SketchUp box, a clay proxy), and everything
expensive — surface, light, people, resolution — is produced by an image model that is
forbidden from moving the geometry.* Weeks 3–5 are three instances of that one move.

**What the syllabus does not contain, and this is the finding:** no measurement, no
specification, no sourcing, no code compliance, no dimension that survives to a drawing. It is a
7-week course on producing an *image*. We are not in that business — our north star is that a
render **visualises a sourceable spec**. So the correct posture is extraction, not conversion.

---

## 2. The licence/VRAM gate — **we cleared it ourselves five weeks ago and never read it back**

The first draft of this section presented Qwen's Apache-2.0 licence and Nunchaku's ~3 GB
footprint as news from outside. They are not.
`docs/research/2026-07-02-comfyui-flux-feasibility.md:78-83` already says it, in our own words:

> **Stronger 2026 local alternatives to FLUX (all Apache 2.0, if a local lane ever matters)**
> — **Z-Image Turbo** (6B): ~6 GB GGUF/FP8, official Fun Union ControlNet incl. depth …
> — **Qwen-Image-Edit 2509/2511**: union control LoRA incl. depth, a dedicated interior-design
>   ComfyUI toolkit exists, Nunchaku 4-bit + async offload → **~3 GiB VRAM**.

So the accurate statement is narrower, and worse. The 2026-07-02 decision parked the local lane
because **FLUX.1-dev's licence** was non-commercial — and the same file, twenty lines further
down, recorded that the licence-clean substitute existed, fitted this GPU, carried depth control,
and even had an interior-design toolkit waiting. That lane was never gated on licence *or* on
VRAM. It was gated on nobody re-reading page 2 of our own report.

**So what is missing is not knowledge. It is a measurement — and the file says so in its own
words:** throughput on this card has *"no published benchmark"* and *"must be measured in a
1-day spike before believing"* (16 GB system RAM is called out as tight; GGUF users report
~19 GB peak). That sentence is five weeks old and is still the open item.

The three re-open triggers that file actually lists — overlay_fidelity catching Gemini layout
drift · Gemini price/terms change · a 16 GB+ desktop GPU — have **not** fired. So the decision
log owes an entry, but not the one I first wrote. Not *"the gate is gone"*; the sharper one:
**the local lane's blocker was never licence, it is an unrun spike.**

Fourth time an outside answer has landed on something already sitting on our disk (3D Warehouse
from three directions, the empty `pipeline/comfyui/workflows/`, now this). The pattern is not
that our research is bad — it is that **a research file with no consumer is storage, not
knowledge**, which is the same defect the DR subscription is currently being cancelled over.

---

## 3. What is worth taking, ranked, with the rule of ours it serves

### 3.1 — Week 3 is the missing third branch of **R8**, and it does not violate R9

R8 today has exactly two outcomes for a free-form object: **ACQUIRE**, or, when acquisition
fails, a **declared gap handed to the owner**. The declared gaps are literally the holes in our
frames — drapery, plants, cut flowers, figures, food. Five rounds and 785 lines of hand-written
cloth physics is what the first branch costs when it is taken anyway.

The Week-3 move supplies a third: **build the proxy R8 already permits** (boxes + radii, a swept
measured profile, an extruded outline — that is what a crumpled throw's bounding form is), use it
to own **placement, scale, orientation, occlusion and perspective**, and let the edit model
resolve the **surface only**.

Why this does not reopen the R9 wound: the position is still *derived from a contact in Blender*.
Nothing is typed, nothing is nudged, and the model is never asked where the object goes — it is
asked what the object's surface looks like at a place we solved. R9's law is about the
*provenance of a coordinate*, and that provenance is unchanged.

**But it needs a guard we do not have, and the guard is the price of admission.** An
instruction-edit model *can* move a mass while claiming to restyle it, and clay-vs-clay eyeballing
will not catch a 4 % drift — that is exactly the class R10 says flat grey hides. We already own
the instrument to build it: `id_mask.py` gives per-object masks in ~2.5 s. **Silhouette IoU
between the pre-edit clay and the post-edit frame, per object, with a threshold**, is a
15-line check and it converts "AI touched our geometry" from a worry into a number. Without it
this technique is not admissible under R9b, and I would not run it.

**And the strongest form of the idea inverts the usual objection.** 2511 takes 1–3 reference
images — *product + scene*. Feed it the **catalogue photo of the sofa we actually specified**
plus our clay frame, and the render shows the thing the client can buy. That serves
sourceability-first rather than breaking it. AI inventing a sofa is a spec defect; AI compositing
the sourced sofa is a rendering method.

### 3.2 — Week 6 costs us nothing and is reachable this week

"Nano Banana" is **Google `gemini-3-pro-image-preview`**. We have `GEMINI_API_KEY`, billing has
been open since 2026-08-04, and `pipeline/scripts/critique_call.py` is already the
send-one-image-with-structural-guards plumbing — a sibling script is the whole job.

- **Price:** ~**$0.134** per 1K/2K image, **$0.24** at 4K (≈ ฿4.7 / ฿8.4). For calibration: one
  full-fidelity Blender frame on this laptop costs tens of minutes of wall clock and ฿0. The two
  are not competing for the same slot — the API frame is the *cheap look*, R5's `--quick` rung
  moved to a different axis.
- **Privacy:** the reason we rejected BFL's own API was that it trains on inputs. **The paid
  Gemini API explicitly does not** — Google's paid-tier terms state prompts and responses are not
  used to improve products, retained only briefly for abuse/legal. Combined with R10b (the fence
  is now **git**, not egress), the objection that killed the FLUX API does not transfer.
- Still binding: the friend's target/anchor images do not travel — not for privacy now, but
  because a judge shown the answer stops being a judge, and `critique_call.py` already refuses
  them **by code**. Reuse that refusal, do not rewrite it.

### 3.3 — Week 5 relighting: **refused as an output, adopted as a probe**

This one conflicts with a standing owner order (2026-08-08): **light is SOLVED from geometry, not
layered on top**; doing light before the objects are complete buries geometric error in an
invisible lighting table (240 W vs 37 W). An AI relight is the extreme case — it produces
plausible light with **no luminaire, no wattage, no photometry, and nothing that can be
specified or bought**. It cannot be an output of our lighting stage. Ever.

It is, however, a very cheap **instrument**, and it attacks a hole R10 named: clay under flat
light gives every mass the same standing, so nothing looks impossible. Relight our own frame five
ways and ask whether the geometry still reads as built objects. That is R10's test with a light
switch on it, at ฿5 a pull.

### 3.4 — Week 7 upscaler: useful, with a line through the middle

Tiled upscaling bounds VRAM by tile, so 10K is reachable on 6 GB — that part is real and the
wall-clock argument (render small, upscale late) is R5's logic applied to the final frame.

The line: **tiled diffusion upscaling invents detail.** On a mood/marketing frame that is free
money. On the frame that carries the spec, invented grain on a specified material is a
fabricated reading — the same defect class as typing 60 mm for a depth the measurement pass
called UNMEASURABLE. Split the two outputs explicitly or do not ship it.

### 3.5 — Week 4 camera LoRA: **we already have the better version — do not downgrade to it**

The Multiple-Angles LoRA offers 96 canned positions (4 × 8 × 3) learned from Gaussian-splat
renders. It exists to give a camera to people who have no 3D. **We have a real camera, in a
measured room, with a real focal length** (`camera_config.py`). Adopting the LoRA would replace a
derived quantity with a picked-from-a-menu one — R9's defect in a new costume. The only thing
worth stealing from Week 4 is its own better answer: *"generate multi-camera angle using 3D
reference"*, which is what we already do.

---

## 4. The meta-finding, which is free and which we keep re-learning

Our research lane's own first rule is **the practitioner rung comes first** — a working designer
beats a 154-line Deep Research. This trailer *is* a practitioner rung, and it cost ฿0 and four
minutes. It named, in one syllabus, three things our DRs never surfaced: that the field's
furniture problem is solved with a **3D proxy** rather than a better generator, that the camera
problem is solved with **geometry we already have**, and that the production shops are running
**Apache-2.0 local + a paid API as a second lane**, not one or the other.

Also, again: our own repo was already pointing here. `pipeline/comfyui/workflows/` has existed —
empty except a `.gitkeep` — since Phase 0, and `.mcp.json.example` carries a commented `comfyui`
stub. Third time an outside answer has landed on something the repo was already implying.

---

## 4b. RUN 2026-08-09 — the ฿15 probe was taken, and it did not say what §3.1 predicted

Full record and spend: `training/TRN-002/probe/editprobe-2026-08-09/GATE.md`. Instrument
built first (`pipeline/scripts/edge_drift.py`, 43 tests), then three asks against
`trn002_mat_r32`, then the guard read on all three.

| ask | DRIFT / 73 | invented edges | verdict |
|---|---|---|---|
| A "change only the surface" | **4** | **34.3 %** | the DESTRUCTIVE one |
| B "relight, move nothing" | 4 (all false alarms) | 19.8 % | see below |
| C "add one crumpled linen throw" | **0** | 13.4 % | clean |

**The prediction in §3.1 was that a proxy-plus-restyle would hold and that adding objects
was the risky part. It is the other way round.** "Only change the surface" came back
having swapped the bench for a different armchair, stocked the shelves with books and
vases, and painted a window into the closet mirror that exists nowhere in the room. "Add
one throw" changed nothing else at all — 0 drift across every checkable object — and
produced the crumpled linen with real folds, weight and a contact shadow that previously
cost five rounds and 785 hand-written lines of cloth physics and still ended at 3/12.

**And the split inside every ask is the finding worth keeping.** What all three held to
the pixel — walls, ceiling, wardrobe, door, artwork, shelving, the bed's own mass — is
exactly what R8 says to BUILD. What they rewrote or invented — the chair, the soft goods,
the decor — is exactly what R8 says to ACQUIRE. The line this studio drew from its own
failures is the line these models already sit on.

**B's four drifts are the probe catching itself.** Nothing moved; the warm relight washed
those junctions below the edge threshold, and `edge_drift` cannot separate "the edge left
because the mass moved" from "the edge left because the contrast did". Confirmed by eye on
the pair. So the guard is sound for restyle and insert edits and ADVISORY under relight —
and it errs toward the alarm, which is the correct side to be wrong on. Recorded as D-012.

**The A-frame is also the sellability argument in one image, and that is the trap.** It
reads like delivered archviz next to our clay. It is also 34 % fabricated. Both things are
true at once, which is why D-013 splits mood frames from spec frames by name rather than
by intention.

## 5. Next step (revised by 4b — no longer the same next step)

DONE: the guard (`edge_drift.py` + 43 tests, D-011) and the probe (§4b, ฿21 against a ฿15
estimate). What §4b changed is which door is worth opening next.

1. **The narrow adoption, and it is narrow on purpose:** generative INSERT of a declared
   R8 gap — one named free-form object at a time, into a frame whose geometry is otherwise
   finished — gated by `edge_drift` exit 0. Ask C is the proof of concept and it is the
   only one of the three that earned anything. This does NOT admit restyle (D-013) and
   does NOT admit relight as an output (D-012).
2. **What it needs before it ships:** an object-inventory diff. `edge_drift` answers "did
   anything MOVE"; it does not answer "is every mass in this frame in the spec", which is
   R10's question and the one D-013 is currently holding shut by policy rather than by
   instrument. That is the next build, and it is small.
3. **Ask the practitioner** (our own first rule, still unspent here): does anyone use this
   in a paid archviz job, and what breaks? Cheaper than any further probing by us.
4. Local Qwen-Edit + Nunchaku stays a LATER step, and §2 renames its blocker: not licence,
   not VRAM — an unrun 1-day throughput spike. Do not install ComfyUI to answer a question
   a ฿4 API call answers.

**Not recommended at any price:** the course itself ($498, beginner level, 13 h). Every
mechanism above was reconstructable from the public syllabus plus the model cards in one
research pass, and the two hardest questions for *us* — does the edit move our geometry, and does
the output stay sourceable — are questions the course does not ask.

---

### Sources
- Course page + syllabus: <https://www.rebelway.net/ai-for-interior-design>
- Qwen-Image / Apache-2.0: <https://huggingface.co/Qwen/Qwen-Image-Edit> ·
  <https://github.com/QwenLM/Qwen-Image>
- Qwen-Image-Edit-2511 (multi-image, structure-aware): <https://qwen.ai/blog?id=qwen-image-edit-2511>
- Nunchaku SVDQuant INT4 + ComfyUI (~3 GB with offload):
  <https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html> ·
  <https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit>
- GGUF on 6 GB (3060 laptop report): <https://huggingface.co/QuantStack/Qwen-Image-Edit-GGUF/discussions/3>
- Multiple-Angles LoRA (96 positions): <https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA>
- Relight LoRAs: <https://huggingface.co/dx8152/Qwen-Image-Edit-2509-Relight> ·
  <https://huggingface.co/dx8152/Qwen-Edit-2509-Multi-Angle-Lighting>
- Nano Banana Pro in ComfyUI: <https://docs.comfy.org/tutorials/partner-nodes/google/nano-banana-pro>
- Gemini 3 Pro Image pricing: <https://openrouter.ai/google/gemini-3-pro-image>
- Gemini paid-tier data use / ZDR: <https://ai.google.dev/gemini-api/docs/zdr>
