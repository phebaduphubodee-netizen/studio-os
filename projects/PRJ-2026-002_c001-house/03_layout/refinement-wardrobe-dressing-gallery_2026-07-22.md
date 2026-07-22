# Redesign — the wardrobe bay becomes THE DRESSING GALLERY (owner feedback 2026-07-22)

**Trigger:** after the fluting refinement the owner said *"wardrobe ดูไม่มี design เลย
แข็งมาก"* (no design at all, very stiff/rigid). This is the THIRD verdict on the bay
(flat grey → "not pretty"; fluted grey → "no design, stiff"). His render verdict is
the one design instrument he operates and it OUTRANKS design theory
([[owner-is-an-engineer-not-a-designer]]).

## Diagnosis
Surface texture was never the fix. Two rounds proved it: the bay was a CLOSED grey
monolith with no composition, no hierarchy, no warmth, nothing to see — the fluting
just made it a *ribbed* monolith ("stiff"). The DEFECT is the e7-DD premise itself:
"recede to quiet cool mineral" (anti-monopoly — protect BF09-3 as the only oak
dressing signature). Receding all the way to a blank enclosure is exactly what reads
as undesigned. And the owner's own strongest signal contradicts it: he CHOSE BF09-3
as an OPEN dressing wall because he likes seeing a composed dressing arrangement.

## Method
I had guessed wrong twice, so I stopped guessing: a design-panel workflow
(`wf_4ba074d9`, 6 distinct directions → 3 judges → synthesis). Winner: **THE
DRESSING GALLERY** (avg 41/50) — flip the closed box into the enclosed twin of the
BF09-3 dressing wall the owner already loves.

## Decision (D-E7-4 AMENDED by owner evidence — the recede-to-grey premise rejected)
An OPEN oak-and-brass walk-in DRESSING ROOM with a clear figure/ground: two open
composed masses you see INTO, one calm cool closed anchor, and a mirror-backed lit
niche as the focal jewel. Composition + hierarchy + a focal point + warmth + things
to see — all as REAL geometry the 3D builds and the Gemini pass enhances.

- **BF09-1 north leg (entry money-shot, fronts SOUTH) — OPEN.** The first wall seen
  through the throat: satin-brass hang rails with garments, a floating cool-microcement
  drawer tower, open light-oak shelves. `open: true`. The 73mm west sliver stays a
  leafless OAK scribe.
- **BF09-1 east leg (the HERO, fronts WEST) — OPEN + the JEWEL.** The longest mass:
  a long brass hang bay + floating microcement drawer tower + a TERMINAL open-oak
  niche whose back is a MIRROR (`niche_mirror: true`) — it doubles the niche depth and
  sparkles the lit shelves, terminating the hero wall before the blind L-corner
  (which stays blind oak carcass at the drawn front-stop).
- **BF09-2 (the cool ANCHOR, fronts EAST) — CLOSED.** Flat handleless microcement
  leaves (fluting deleted) with ONE horizontal ~720 counter-datum reveal so the calm
  face reads composed. It is the deliberate figure/ground GROUND against the two open
  masses, suits the shallow 501.5 depth + the slide-lane cover, and now carries the
  suite's cool microcement note by surface area.
- **Floor** stays BARE (bedroom oak continues) — the clear floor is ~1800×1300 crossed
  by both door lanes, so no island/bench fits (the feature lives in the joinery, off
  the floor).

## Materials + anti-monopoly (reconsidered, honored by MIX not hiding)
The owner-signed BF09-3 recipe, reused by NAME: `oak_veneer` = carcass/gables/tops/
backs/shelves/niche/scribe; `microcement_cool` = the floating drawer fronts + tower
backs + the whole BF09-2 anchor; `satin_brass` = the hang rails; `mirror` = the niche
back. Oak masses 4→5, BUT an open walk-in reads as its CONTENTS (garments/folds/
objects dominate the visual field), so **net visible oak SURFACE drops** versus the
wall-to-wall grey monopoly it replaces; the cool microcement is retained as the drawer
ribbons + the closed anchor; the bay is its own subroom behind the throat, never
co-framed with the four bedroom oak masses. The owner's render verdict authorizes the
amendment (recorded as owner-evidence, not a silent overwrite).

## Build (high reuse — the open engine already existed)
`millwork.millwork_parts(open_front=True)` already builds BF09-3's hang bay + drawer
tower + niche and names parts so the material router paints rail→brass, front/
towerback→microcement, rest→oak. NEW/CHANGED:
- `wardrobe_bay.py`: a per-mass OPEN route — `open:true` → one open_front composition
  across the fronted run (filler/blind stay oak slabs), parts routed BY TOKEN
  (`_open_part_mat`); `niche_mirror:true` → a mirror at the terminal niche back
  (RAISES if the flag is set but no mirror part emits); the closed path drops the
  fluting and adds the optional `counter_reveal_mm` leaf split. The e7-era open:true
  RAISE is retired (the flag is now HONORED — the correct resolution of that swallow).
- `millwork.py`: `open_front` gains an optional `niche_mirror` (default off →
  byte-identical for BF09-3); emits a `niche_mirror` part at the niche back.
- `material_presets.wardrobe_bay_story_bits`: rewritten from the dead grey-fluted
  armour to the open dressing inventory, DERIVED per-mass (open count, closed anchor,
  mirror jewel) so the polish keeps the open composition and can never re-flatten it.
- Spec: `open:true` on the two BF09-1 masses, `niche_mirror:true` on the east,
  `counter_reveal_mm:720` on BF09-2; every ink pin intact (rects, ink_faces, junction/
  lane pins, zone-open-south, baycut, front_stop, slide lane).
- 63 bay parts: 40 oak / 6 brass / 16 microcement / 1 mirror.

## Behavior change disclosed (review E7-STATION-3): the drawn stations now BOUND the
fronted span (the filler/blind boundaries) rather than splitting closed leaves at every
interior station — the open composition fills the span with its OWN divisions (gables
near, not exactly on, the interior stations). The stations still VALIDATE (in-run,
ascending, junction/ink pins intact) and the composition follows the BOUNDARY station
(move it → composition shifts). The DD's original "reveals land on every station" held
for the closed scheme; the open scheme's rhythm is the dressing composition, which is
the point.

## Verify
Tests rewritten in lockstep (mineral-only → material-mix + open-composition + mirror-
jewel-fails-loud + closed-anchor-reveal + open/closed split pins; fluting test deleted;
story fragments updated; the derivation pin now proves the open composition follows the
boundary station). Pure suites green.

## LOOK (256-sample renders — verified, a decisive transformation)
- `wardrobe_bay_entry` (money shot): the grey box is GONE — an OPEN oak-and-brass
  dressing composition fills the frame: satin-brass hang rails in open oak bays, a
  floating cool-microcement drawer tower with open oak shelves above, more open oak
  shelving, the warm oak carcass glowing, the oak floor grounding it. Reads as a real
  boutique walk-in with hierarchy + things to see. PASS (the "no design, stiff"
  verdict is answered).
- `wardrobe_bay_dressing` (hero + jewel): open oak shelves + the microcement drawer
  bank + the MIRROR-BACKED niche working — the mirror doubles the niche depth and
  reflects the lit room (no GI black-hole / coplanar artifact — the design-panel's
  probe cleared). PASS.
- `wardrobe_bay_doorlane`: the ensuite doorway still reads OPEN (e4/e6 intact — no
  regression); the BF09-2 CLOSED cool anchor is at frame-left with its horizontal
  counter-datum reveal reading composed (not a blank locker); a warm oak dressing
  sliver at frame-right. PASS.

## Open (owner to judge / confirm)
Confirm the D-E7-4 amendment (closed grey → open warm) is authorized by your verdict;
whether BF09-2 stays the one cool CLOSED mass or should also open; whether you want a
slim full-height dressing mirror in addition to the mirror-backed niche; an optional
built-in perch (seat recessed into the east run, zero floor clearance); under-shelf warm
LED (optional, [est] — closet lux is a vault gap, so the e5 ceiling cans carry it).
