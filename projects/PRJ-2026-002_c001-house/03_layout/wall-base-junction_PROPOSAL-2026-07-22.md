# Wall-to-floor junction — a design to approve, not a menu

**PRJ-2026-002 master suite · 2026-07-22 · status: OWNER DECISION OPEN · nothing built**

Raised by the vault audit (`docs/strategy.md:2171-2176`). Not built unilaterally because
it touches the wall geometry every spec shares and the deciding question is
constructability and tolerance — an engineering call, not a taste call.

---

## 1. The defect

Our renderer builds the room shell as "floor + 4 walls" (`pipeline/scripts/build_room.py:5`)
and the junction between them is **exactly zero**, by construction, not by oversight:
`add_wall` starts every wall prism at `z0=0.0` (`build_room.py:339`) and the floor slab's
top face is exactly `z=0` (`build_room.py:2729`). Wall and floor meet on a razor line.

The studio's own reference calls that line the tell:

> floor-flush volumes get a recessed plinth base (zocallo) **10–15 mm**, a mitered base
> detail, or a shadow line; bridge material changes with baseboards/coving or **10–20 mm**
> aluminium shadow-gap Z-reveals — **a razor 0 mm junction is the CG tell** and produces
> artificial "light leaks"
> — `knowledge/rendering/render-defaults.md:149-152`

**Tier, stated honestly:** REFERENCE, archviz convention, *"never a gate"*, distilled
2026-07-21 from `knowledge/_inbox/interior-render-critique-DR-2026-07-15.md` (notebook
`639575c3`). The full protocol is `knowledge/classifications/qa-dimensions.md:240`, whose
own provenance block says REFERENCE band only and that `knowledge/codes-th/` outranks it.
**`knowledge/codes-th/` contains nothing at all on skirting, wall base or floor
termination** — I checked; there is no statutory pressure here in either direction.

Two facts make this more than a render-polish nicety:

1. **Our own construction deliverable already specifies a base that our render does not
   build.** `pipeline/scripts/schedules.py:33` emits a finish schedule with a **"Base"**
   column whose room defaults are `Painted MDF, 4"` / `Tile / coved vinyl` / `Tile`, and
   the studio drawing standard carries the tag **SK = บัวเชิงผนังอลูมิเนียม**
   (`knowledge/brand-standards/drawing-symbols-abbreviations-th.md:45`). The schedule says
   there is a skirting. The geometry says there is none. That is prose-vs-build drift
   inside a client deliverable.
2. **The Gemini polish pass already invents one.** In the shipped v04 hero
   (`assets/projects/PRJ-2026-002/renders/R_PRJ002_MasterSuite_Cam02_v04.png`) a white
   skirting is clearly visible at the left wall. It is not in our model. So the question is
   not *whether* this suite has a wall base — it is whether **we** decide it or the
   repaint keeps guessing it for us.

---

## 2. The recommendation

**A 12 mm recessed shadow gap at the base of every DRY wall — ร่องเงาเชิงผนัง — dark-backed,
with the floor finish running under it. No skirting anywhere in the dry rooms.**

```
      wall plaster face (= the plan outline; add_wall extrudes OUTWARD from it)
      │
      │                              ← full-height plaster, unbroken, to ceiling
      ├──────────  FFL + 12          ← underside of the plaster nib, 1.5 mm arris
      │▓▓▓▓▓▓│                        12 mm high × 15 mm deep slot, DARK-BACKED
      │▓▓▓▓▓▓│                        (matte near-black, the BF14 backer identity)
   ═══╧══════╧═══  FFL ± 0           ← engineered-oak floor runs UNDER the nib and
      floor finish continues 15 mm      terminates behind the plaster face; its ~10 mm
      behind the wall face              perimeter expansion gap is INSIDE the slot
```

- **Opening 12 mm, depth 15 mm, dry rooms only** (bedroom ring + wardrobe-bay ring).
- **Depth is 15, not 12, and the 3 mm is bought for one specific reason:** a 12 mm nib
  cannot reliably lap a 10 mm floating-floor expansion gap. The extra 3 mm is floor-lap
  tolerance — it is not a second reveal language, and it appears nowhere else.
- **Dark backer**, exactly as BF14 does it (the signed #2A2C2E–#3A3C3E matte backer), so
  the slot reads as a shadow line and never as an absolute-black cavity —
  `qa-dimensions.md:258` red-flags `(0,0,0)` cavities explicitly.
- **Closed with backer rod + neutral-cure silicone tinted to the backer colour.** This is
  the movement joint a 0 mm junction cannot have — and it is what makes a ±5 mm floor-cut
  error invisible, because the eye reads the dark line either way (see §5).
- **Top arris is a uPVC render stop bead**, laser-fixed before rendering — never a
  hand-struck groove. Internal corners run through; mitred return at the external corner;
  stopped ends returned into the back face at each jamb. The reveal stops at every joinery
  end panel, where millwork's own toe-kick (`PLINTH_H 80 / PLINTH_R 18`,
  `pipeline/scripts/millwork.py:33`) already takes over.
- **Run, derived and re-checked against the spec, not guessed:** main ring 29,995.6
  − 8,420 (7,198 of sill-0 glazing + the 1,222 door threshold, both of which have no wall
  base) − 5,950 (the two edges coincident with the wet ensuite: 2,800 on x=0 + 3,150 on
  y=8,650) = 15,625.6; bay ring 10,600 − 2,500 (open south edge) − 898 (ensuite passage)
  = 7,202. **≈ 22.8 m.** Every term recomputed from `master-suite.CANONICAL.spec.json`.
- **The ensuite is deliberately a different detail**: wall tile onto floor tile over the
  tanking with a 5 mm dark neutral-cure silicone joint — the same dark-line family, with no
  rebate cut through a waterproofed base. That asymmetry is a decision, not an omission —
  and it must be enforced in **code**, not prose, or a bathroom subroom silently inherits
  the slot.
- **Drawing note:** no horizontal conduit or outlet box below +150 AFF on any wall carrying
  this detail.

### Why 12 and not 10, 15 or 20

**Because it is your number, and you already gave the reason.** BF14 carries
`schedule.reveal_mm = 12.0` in the canonical spec, with your own `reveal_note` recording
that 15 sat at the top of the tolerance band and 12 was taken instead for floor/ceiling
tolerance (owner, 2026-07-16c). This proposal spends no new design authority: it extends
one signed number to the thirty-odd walls it was never applied to.

That is also the non-taste answer to *"งานคุณยังดูไม่มี style"* — **the room has one
detailed wall and thirty-three untrimmed ones.** The suite's signed language is already
reveals and shadow lines: BF14's 12 mm floor and ceiling reveals, element 3's recessed bed
plinth, element 7's counter-datum reveal, handleless millwork throughout.

And the style rule is already signed at Stage 02:

> Built-in-first, flat-panel, full-height (2800) joinery; **shadow-gap reveals.
> EDGE: no ornamental moulding / cornice / classic profile anywhere**
> — `projects/PRJ-2026-002_c001-house/02_concept/concept.md:29`

Stated fairly: the skirting direction was deliberately drawn **flat and square-edged**, so
it is not literally the "ornamental moulding" that edge excludes. But it is still a proud
applied trim in a room whose signed DNA is recessed lines, and choosing it means overturning
a Stage-02 rule on appearance — which is the one kind of question I should not be putting
to you.

**One more engineering point in the reveal's favour:** our clearance gate carves statutory
keep-outs from the wall band, because `build_room` extrudes every wall outward
(`pipeline/scripts/suite_clearance.py:22`). A 15 mm proud skirting projects *into* the room
on both faces and quietly over-claims every ข้อ 20/21 clear leg by ~30 mm. **A recess can
only add clear floor.**

---

## 3. What it beats, and the one argument against it

The panel ran three directions and split 2–1 for a reveal. **The skirting case is real and
you should hear it**, because it makes one point the reveal must answer:

> An engineered-oak plank floor in Bangkok's humidity swing needs a free perimeter of
> ~10 mm. Something has to cover that gap, and it has to be fixed to the **wall**, so the
> floor can move under it. A skirting does that by definition. A reveal must not trap it.

The recommended detail answers it by **running the floor finish under the plaster nib** and
terminating it 15 mm behind the wall face — the expansion gap lives inside the slot, hidden,
and the floor stays free to move. That is the graft from the skirting direction, and it is
why the slot is 15 mm deep and not 12.

The skirting also wins on two honest points: it is the more forgiving detail on site, and
it is what our own finish schedule already says. If the answer to §5 is "no", it is the
right detail and I will build that instead.

---

## 4. What it costs

**On site** — trade: **ช่างปูน only.** No carpenter, no trim SKU, no import, no new
supplier. The plasterer fixes a 12 × 15 mm PVC stop bead around the base, set off the
standard **+1.000 m datum line**, never measured up from the screed; plasters down to it;
leaves the bead in permanently. One extra operation for a trade already at that wall. The
skirting alternative pulls in a carpenter, a filler/sander and a painter — the vault's own
TIP-TOP install note describes exactly that four-step chain
(`knowledge/materials/wall-cladding-and-decorative-mouldings-th.md:139`).

**Money — `[est]` only, and I want to be blunt about how weak the basis is.** Order of
magnitude **฿175–320/m all-in, so ≈ ฿4,000–7,300** over the 22.8 m run. That is a
labour-and-bead estimate, **not a quote**: the vault holds **no THB price for any skirting,
bead, trim or profile in any material**. TIP-TOP is a spec book with no prices
(`wall-cladding-and-decorative-mouldings-th.md:110`), Pan Union's price sheet has never been
obtained, and there is no Thai supplier recorded for aluminium shadow-gap extrusion at all —
despite our own drawing tag defaulting to aluminium skirting. If money is the deciding axis,
that is a supplier query I should run before you decide, not a number I should invent.

**In code** — this is the most invasive geometry change since the wall builder was written:

- A new **pure** `wall_base.py` (bpy-free), following the `element5_lighting.coplanar_backer_skins`
  / `wardrobe_bay.py` precedent — because **no test anywhere imports `build_room.py` or
  `build_floor.py`** (both `import bpy` at module top), so `poly_walls_bpy` has *zero*
  regression coverage on prism geometry, wall counts or names. The logic has to live where
  it can be tested.
- **20** room-spec JSONs carry `room.outline_mm`, **11** of them live; plus **13** subroom
  rings, each of which multiplies the detail.
- **A second implementation is unavoidable**: 2 whole-floor manifests build walls through
  `build_floor.build_walls` (`build_floor.py:130`), a different code path with no continuous
  slab. Either it gets the detail too, or the razor junction survives there and we say so.
- Two known traps: the name-prefix material router would send a `wall_base__*` object to the
  wrong material silently (`build_room.py:1622`), and the global `_bevel_edges(0.005)`
  (`build_room.py:3008`) would round a 12 mm slot into mush — 5 mm of bevel on a 12 mm
  feature. Both must be handled or the detail ships broken-looking.

---

## 5. Your call — one question

Everything above is settled except one thing, and it is yours:

> **Can the master-suite finished-floor build-up (screed + underlay + 15 mm engineered
> board) be frozen in writing before the walls are finished, so the stop bead can be
> laser-set at FFL+12 weeks before the floor exists?**

All three judges arrived at this question independently, and it is the same tolerance
argument you made yourself when you took 12 over 15 at BF14 — *"15 sat at the very top of
the 10–15 window with zero site tolerance; 12 is mid-window with ±3"*. The bead goes on
before the floor exists: if the finished floor lands high the slot closes toward 7 mm; if
it lands low, the floor stops short of the nib.

**How much risk is actually left, honestly:** less than the panel first thought. Because the
joint is closed with backer rod and silicone tinted to the backer colour, a ±5 mm error in
the *floor cut* is invisible — the eye reads a dark line either way. What the bead position
still controls is the **visible slot height**, and at 12 mm nominal a ±3 mm site error lands
between 9 and 15 mm, which is inside the vault's own 10–15 zocallo band at the top and one
millimetre under it at the bottom. So this is a detail that degrades gracefully rather than
failing — but it does need the floor level frozen in writing, which is a project-management
commitment, not a drawing note.

- **YES** → I build the 12 mm dark-backed reveal above.
- **NO** → I build the skirting instead: **100 × 15 mm square-edge, painted the wall colour,
  satin** — inside the only sourceable family we have (TIP-TOP PU, h 91–201, thk 11–20).
  It is the forgiving detail and it is what our own finish schedule already claims.
- **Third option, if the programme can't freeze:** set the bead *after* the floor is laid.
  That removes the tolerance risk entirely and costs a second visit from the plasterer.

**If you do not answer, I build nothing here** — the razor junction stays, and stays
recorded as a known defect. I am not going to guess a tolerance on your behalf.

---

## Provenance

Panel: 5 grounding sweeps (read-only) → 3 independent directions → 3 judges (coherence /
constructability / pixels) → this document. Judges split 2–1 for a reveal; the skirting's
floor-expansion argument is grafted in, and its direction is the recorded fallback.
Every dimension above traces to `knowledge/` or to the canonical spec; every price is a
declared gap.
