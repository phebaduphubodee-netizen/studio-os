# What a sold render actually does — measured from one delivered Thai bedroom

- Source: TRN-002 reproduction lane, measurements taken 2026-08-04/05 off the
  reference frame through a solved camera (landmarks reproject at 0.09 px mean).
- Tier: REFERENCE. Distilled from OUR OWN measurement, not from a document.
- **n = 1.** Everything below is a hypothesis with a number attached, not a law.
  This repo has already been caught generalising "3 projects" from n=1; the
  honest use of this file is as a CHECKLIST OF QUESTIONS to ask the next
  delivered render, and every entry says what would confirm or kill it.
- Owner order that produced it (2026-08-05): *"ที่ผมให้ศึกษางานเพื่อนผม คุณก็ควร
  ตั้งคำถามงานเพื่อนผมด้วย แล้วก็ทำ DR หรืออะไรก็ได้เพื่อเก็บความรู้จากงาน"* —
  the reproduction curriculum had been executed as pure imitation for five
  rounds. Measuring is not learning.

---

## 1. LIGHT — and every finding here contradicts what the room looks like it does

**1.1 The visible window is not the key light.** The reference's left wall
carries a blind, and it is dressed nearly closed. Evidence: the wardrobe face
directly across from it shows no peak opposite the window's band (monotone
−0.028 Ylin/m *away* from it); the floor nearest the window is the DARKEST
floor in frame (0.172 against 0.253 a metre further in); the ceiling corner
nearest it is the darkest ceiling (0.236 vs 0.454); and the one cast shadow in
the frame points 22° away from where a window key would put it.
→ **Transferable question:** in a sold interior, is the visible daylight source
usually a subject rather than an illuminant? A window rendered as a bright
portal blows the frame's own exposure; dressing it closed lets the interior
carry the value range. *Killed by:* a delivered render whose brightest surfaces
are the ones facing the window.

**1.2 The room is lit by a large, soft, off-frame source in FRONT.** Bounce, not
throw: the back wall measures FLAT in x and −7.7 %/m *upward*, i.e. brightest
at the floor — it is lit by what the rug and bed return, not directly.
→ **Practical consequence we paid to learn:** aim the key at the floor and the
bedding and let the back wall be paid for out of bounce. Lighting the back wall
directly put every object in our room at 0.4–0.65 of its reference ratio while
the overall exposure looked correct — an error invisible to a LOOK and obvious
to a per-object ladder.

**1.3 Ceiling downlights are GRAPHIC, not functional.** Four of them, and their
entire contribution is four blown lens cores (273 px, 0.03 % of frame) plus one
−8 % handle shadow. Measured negative twice: the ceiling glow is back to
background within 120–200 mm, and the parquet directly under a fixture reads
0.184 and RISES to 0.220 a metre away.
→ **Transferable question:** are recessed downlights in sold work primarily
CEILING COMPOSITION — a rhythm of bright points — rather than a light source?
*Killed by:* a delivered render with measurable pools under its downlights.
→ **Corollary that cost us four rounds:** our own flat form-light made bright
ceiling pools, and four separate blind critics counted those pools as extra
downlights and filed it as a defect four times. An artifact of our lighting was
repeatedly diagnosed as an error in our geometry.

**1.4 Shelf strips sell by FALLOFF, never by fill.** On one continuous panel:
strip line 0.726, lit compartment 0.283, unlit compartment 0.099 — a 7.6 : 2.9 : 1
ladder, with a 250 mm wash under each strip (0.73 at 20 mm → 0.40 at 90 →
0.28 at 250 → flat).
→ **The unlit compartments stay dark.** Our clay read them as solid blocks and
the instinct was to lift them; lifting moves *away* from the reference. The
read comes from the gradient, not from the level.

**1.5 The bedside lamp is OFF.** A black cone at Ylin 0.008–0.020, no rim, no
pool. A styling object, not a light.
→ **Transferable question:** how often is a practical in a sold render switched
off and used purely as a dark accent? This frame's dark tail is entirely the
TV screen and one arch void — the lamp joins them.

**1.6 The illumination range on any ONE material is small: 1.2–1.9 : 1**, except
the lit etagere at 7.6 : 1. The frame's p99/p1 of 182 : 1 is NOT a lighting
range — both tails are MATERIAL (a black screen and a void at one end, clipped
lens cores at the other).
→ **Discipline this forces:** judge light with same-material ratios. A whole-
frame histogram ratio conflates the palette with the lighting, and we quoted it
once as if it were a dynamic range before catching it.

## 2. MATERIAL — the palette is a narrow band with two deliberate holes

Measured as ratios to the white back wall (n = 65,014 px), which is the
declared reference surface:

| surface | ×wall |
|---|---|
| bed platform side / white bedding | 1.51 / 1.29 |
| rug (lit) | 1.15 |
| ceiling / wardrobe lacquer | 0.81 / 0.82 |
| travertine run (spans 4× by LIGHT, one material) | 0.26–1.05 |
| herringbone floor | 0.44 |
| partition frame (warm dark grey-brown, not black) | 0.11–0.19 |
| TV screen | ≤0.05 |

**2.1 Everything except two objects lives inside one 2× band.** The TV and the
arch void are the only true darks. A room that reads rich is doing it with a
NARROW value range plus two deliberate holes — not with contrast everywhere.

**2.2 One material can span 4× and still be one material.** Console, desk,
pier, etagere and the headboard band are a single travertine; the spread is
lighting, proven on ONE continuous panel reading 2.24× between two spots 0.6 m
apart. Giving each object its own albedo would have baked the light's job into
the material table permanently.
→ **And the corollary we got wrong first:** the "oak band" behind the headboard
is not oak. At 8× it is vein-cut travertine with a mitred return. A first-look
name written into a spec survives five rounds unexamined.

**2.3 Texture is per-surface and mostly ABSENT.** Measured texture index: walls
and ceiling 0.03 (flat), bed platform side 0.05, floor 0.29, travertine 0.49.
→ The studio's own ground-truth study says we run 95 % image-free materials
against 50–66 % in pro files, and the fix is real — but applied blind it is
wrong: mapping a plaster texture onto paint the reference measures at 0.03
turned smooth walls into raw stucco in one frame. **The rule needs the
per-surface number, not the studio average.**

**2.4 Nothing in the room is glossy except the screen.** The partition's metal
frame looks specular and is not — its p99/median of 4.6–6.9 collapses to 1.1–1.4
once JPEG ringing off the adjacent glass is excluded. Matte/satin powder coat.

## 3. DIMENSIONS worth carrying to the next Thai residential job

- **Herringbone parquet 132 × 620 mm at 45°**, chevron spine along the room's
  depth axis (L/w = 4.69, and the RATIO is scale-invariant so it survives any
  gauge uncertainty).
- **Bed: 1595 wide**, platform top 221 with the platform ledge protruding
  **165 mm past the mattress on every side**, mattress+bedding ≈ 290–330 thick.
  A low tray with a fat soft stack, ratio ≈ 1 : 1.4.
- **Joinery run:** floating media console top 753, section ≈ 255 × 258 (square),
  rounded end R ≈ 55; vanity top 875 with a 110–135 thick edge; waterfall pier
  to the floor. Band top 937 — i.e. **just above the headboard**, not level with it.
- **Etagere:** thin boards at ~530 pitch, back panel continuous to a top that
  aligns with the wardrobe bulkhead across the room (2920). Open, not a cabinet.
- **Partition members come in PAIRS** (jamb + door stile, ~45–50 mm each with a
  44 mm gap), where an inexperienced model puts one fat stile. This is a
  topology error before it is a dimension error.
- **Wardrobe doors ~508 mm modules**; the reveal between them is SUB-PIXEL at a
  normal interior camera (equivalent width ≈ 1 mm) — match it photometrically,
  never model a groove.

## 4. WHERE THE REFERENCE IS A CHOICE, NOT A LAW — questions to put to it

A reproduction lane that treats the reference as perfect cannot tell a decision
from an accident. Open questions, none of them settled:

1. **Is the near-closed blind a design decision or an exposure rescue?** It
   costs the room its daylight story. Would a practitioner defend it, or is it
   what you do when the exterior would blow out?
2. **Four downlights that light nothing** — is that honest lighting design, or
   a ceiling that would fail a real lux check? Our own vault carries the lumen
   method; the two have never been compared.
3. **The TV as a black void.** It is the darkest thing in the frame and the eye
   goes to it. Deliberate anchor, or an unsolved surface?
4. **A 1595 mm bed in a room of this size** reads modest. Is that the unit's
   real constraint, or a choice to make the room look larger?
5. **273 clipped pixels.** Clipping the lens cores is a decision about where the
   frame's white point sits. Is that standard practice or this artist's habit?
6. **One stone across the entire joinery run** — is that a Thai-market cost
   decision (one slab order), a style position, or both?

## 5. What our own measurement CANNOT answer → the research queue

These need a practitioner or a DR; the frame cannot settle them (and the
practitioner rung comes first — this studio has already proven that one
question to a working designer beat a 154-line DR):

- Do Thai residential studios light bedroom hero shots with a large off-frame
  soft source as standard practice, and what is it physically (softbox card,
  HDRI portal, glazed wall)?
- Is "downlights as ceiling rhythm, not illumination" a stated convention?
- What drives the near-universal narrow value band in sold residential work —
  print/screen delivery, client preference, or a lighting-model limitation?
- Standard Thai bedroom bed sizes and the module logic behind 508 mm wardrobe
  doors.
- Whether one-slab joinery runs are a cost decision in the Thai market.

---

## Provenance and how to reuse

Every number above traces to a scripted measurement in the TRN-002 lane
(`training/TRN-002/`, round records in `qa/reproduction-curriculum.md`,
instruments in `pipeline/scripts/trn002_*.py`). No number here was read off a
document, and none of it came from the builder's memory. Before any value in
this file gates a deliverable it must be distilled into `knowledge/` proper —
this is `_inbox` tier, and `n = 1`.
