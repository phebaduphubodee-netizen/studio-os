# Placement audit — 2026-08-02

**Why this exists.** The owner: *"ผมสังเกตว่าที่ผ่านมาทั้งหมดคุณชอบวาง model เบี้ยว ลอย
ไม่ตรงแกน ไม่สมจริง มีแผนหรือแนวทางแก้แบบยั่งยืนมั้ย?"* — an observation across every
project, not one lane, and the second one he has made in that shape. The first
produced R8. This is the measured half of the answer to the second; the rules it
produced are **R9 and R9b** in `CLAUDE.md`.

## 1. The measurement

### Guard coverage: 5 of 13 placed objects

Two placement guards existed, both written after a burn, both scoped by class name:

```python
if p["cls"] not in ("vase", "candlestick"): continue
```

The scene places five classes: `figure`×3, `candlestick`×3, `candle`×3, `vase`×2,
`floral`×2. **Eight of thirteen objects were exempt, including every figure.** And
rounds 15, 16, 17 and 18 were *all* figure-placement defects.

### Support coverage: 14 of 78 masses

The "does it rest on a real surface" guard accepts a support only if its name
starts with `("step", "plinth", "pedestal_", "centre_box")`. **64 masses are
invisible to it as supports** — including the `base_*` that round 16's defect was
about.

### The four rounds, and what each one actually was

| round | defect | what the position was doing |
|---|---|---|
| 15 | *"the principal image was off its own altar, and I had already fixed that class twice in the same edit"* | two of three instances corrected, the third left on a contaminated mask read |
| 16 | *"the image was overhanging its own base, because the base was sized from a constant drawn for a different figure"* | the base moved; the typed coordinate did not |
| 17 | *"the nudge I added to centre the figure on the BOX is what pushed it off its own BASE"* | one coordinate asked to satisfy two relationships |
| 18 | *"two bounding boxes shared a centre to 0.5 mm and the figure still sat wrong on its base"* | centring the boxes is not seating the object |

## 2. The mechanism — the spec confesses it in its own words

> *"the base is built at the unnudged position, so every millimetre of that
> correction also moved the figure across its own pedestal. **I optimised one
> relationship and broke another in the same edit, and did not look at the
> second.**"*

Positions are stored as `pos_mm`, an absolute triple, plus `x_nudge_mm`, a manual
fudge. **A coordinate encodes a RESULT, not a RELATIONSHIP.** When the supporting
object is resized, the stored number stays perfectly legal and the contact breaks
in silence — nothing fails, because a coordinate is always a legal coordinate.
And with no declared parent, *"centre on the box"* and *"stand on the pedestal"*
are two edits to the same three numbers, so every fix to one is a break to the
other.

**Contrast, from the same lane:** the one placement that was SOLVED rather than
typed — a symmetric pair on one surface has exactly one unknown, so two measured
pixels over-determine it — landed at **1.6 mm in a single cut.** That is the whole
edge, and it is the same edge R8 drew for geometry: what is recoverable from
measurement lands in one round; what is invented drifts for five.

## 3. The instrument, and the three corrections that scoped it

`placement_dump.py` (inside Blender, reads the EVALUATED depsgraph so modifiers
count) → `placement_check.py` (pure, no bpy, testable under plain python).

It was run against the live TRN-001 scene, 99 rendered meshes, at every stage:

| version | FAIL on the correct scene | what it proved |
|---|---|---|
| 1. containment for every object | **27** (all architecture, 0 props) | a metric that cannot separate a plinth overhanging its own toe-kick from a figure overhanging its base |
| 2. + freestanding = touches only its support | 1 | it would have **passed round 16**: a figure is several meshes touching each other, so no part was ever "freestanding" |
| 3. + group by parent tree, count only LATERAL contact | 1 | correct on figures; the ceiling still convicted |
| 4. + one support only; contents don't brace | **0** | a ceiling rests on ten walls — containment is the wrong question for a SPANNING element |

**The lesson that outlives the tool:** three of those four corrections were found
by the check convicting correct construction, and the tempting fix each time was
to narrow the scope until the noise stopped. Version 2 did exactly that and
silenced the true positive along with the false ones. **Scope must be derived from
the rule's own premise** — "its footprint must sit inside its support" is only
true when ONE thing holds it up — not chosen to make the output quiet.

## 4. Proof it catches the real thing

A guard that has never blocked anything is a rumour. Each defect was reintroduced
into the REAL dumped geometry and the check re-run:

| reintroduced on the live scene | caught as |
|---|---|
| figure moved +60 mm off its base (round 16) | **OVERHANG** — *hangs 59.0 mm past `figure_centre_base`* |
| figure lifted 40 mm | **FLOATING** — *nearest surface below is 40.0 mm away* |
| figure tipped 2° | **OFF-AXIS** |
| candlestick moved −170 mm off the plinth | **OVERHANG** — *hangs 21.6 mm* |
| vase moved −140 mm (margin is 125.9 mm) | **OVERHANG** — *hangs 14.1 mm past `step`* |
| **vase moved −100 mm (still on the step)** | **nothing — the negative control** |

The last row is the one that matters: a guard that fires at both −100 and −140 is
not measuring the margin.

## 5. Declared blind spots — stated, not discovered later

- **AABB is not geometry.** Interpenetration is ADVISORY and never fails a run,
  because two boxes overlapping may be interlocking legally. Promoting it would
  train the reader to mute the instrument, which is how the previous debt
  instrument died.
- **A spanning element unsupported at one end is not caught.** That needs the
  footprint covered by the UNION of supports, which an AABB cannot express.
- **"Attached to" and "adjacent to" are indistinguishable.** Anything touching
  anything escapes FLOATING — a petal on a stem is exempt, and so would be a prop
  merely brushing a wall.
- **This is a check, not a solver.** It catches a typed coordinate that went
  wrong; it does not derive the right one. That is R9's other half and it is
  **not built**: `pos_mm` and `x_nudge_mm` are still what the spec stores.

## 6. What is done, and what is next

DONE: the audit, R9 + R9b in `CLAUDE.md`, `placement_dump.py`,
`placement_check.py`, 19 pure tests with a negative control for every scope rule.

NEXT, and it is the half that actually removes the defect class rather than
reporting it: **contacts in the spec.** `rest_on` / `centre_on` / `align` resolved
at build time, `pos_mm` derived and never typed, `x_nudge_mm` deleted rather than
zeroed. The check then stops being a net and becomes a regression test on a
mechanism that cannot produce the defect.
