# Engineered oak flooring — real plank widths (staged 2026-08-24)

REFERENCE tier. Retrieved 2026-08-24 by web search (generic question about a
product category; no client data, no project details, no dimensions of the
owner's unit left this machine). Why it exists: STY-7 convicted the room floor of
rendering its boards 266.67 mm wide, and the evidence FIRST reached for was
`build_room.PLANK_PITCH_MM = 180.0`, whose trailing comment says "150-250 mm is
the real range" — an uncited bare literal that this repo chose for its own
procedural veneer. Convicting a render with a number we invented is the
self-consistency shape R7b warns about by name. This unit replaces that yardstick
with sourced values.

## Values

**189 mm is an ordinary stocked width for engineered oak**, not an unusual one.
It is the metric rendering of a ~7.5 in board and multiple independent UK
retailers carry it as a named filter or category:

| width | status | seen at |
|---|---|---|
| 150-189 mm | a retailer's own "Wide" band | FlooringSupplies filter |
| 189 mm | dedicated category page; multiple SKUs | Wood and Beyond; flooring365; Builder Depot; Ambience |
| 220 / 260 / 300 mm | "extra-wide", sold as a distinct premium class | Chaunceys |
| up to 385 mm | "Giant Oak", the top of the ladder | Chaunceys |

**~267 mm was NOT found on sale.** Extra-wide oak is marketed at 220, 260 and
300; a search at 265 / 267 / 270 returned no supplier. State this as "no supplier
found", never as "does not exist" — one search pass is weaker than a citation,
and the honest half of the finding is the positive ladder above.

## What this settles for the repo

- The `wood_floor` CC0 artefact carries **9 boards across its declared
  1699.99969 mm tile = 188.889 mm per board** (measured from the AO and
  Displacement maps: 9 joints, confirmed by FFT top harmonic k=9 and by circular
  autocorrelation; 9 x 189 = 1701 mm, so the publisher's own metadata confirms
  itself to 0.06%). Used at its declared scale the texture depicts an ordinary,
  purchasable product.
- Mapped at the pre-STY-7 `tile_m = 2.4` it drew **266.67 mm** boards — a width
  in a real class (extra-wide) but at a size nobody was found selling.
- `PLANK_PITCH_MM = 180.0`'s comment is roughly right and its centre is not 180:
  the sourced ordinary band runs 150-189 with a separate extra-wide class above.
  Treat the constant as what it is — a chosen feature size for OUR procedural
  veneer — and cite this file when a real product width is the question.

## Sources (retrieved 2026-08-24)

- https://www.woodandbeyond.com/engineered-wood-flooring/shopby/189mm.html (189 mm category)
- https://www.flooringsupplies.co.uk/engineered-wood-flooring?wood-species=oak&plank-width=wide-(150mm-189mm) ("Wide (150mm - 189mm)")
- https://chauncey.co.uk/wide-plank-engineered-wood-flooring/ ("standard engineered oak board widths up to 300mm ... Giant Oak boards up to 385mm"; "220mm, 260mm, and 300mm-wide planks")
- flooring365 (Milano Engineered Natural Oak Lacquered 189mm x 15/4mm; Richmond Engineered Stone Grey Oak 189mm x 14/3mm)
- Builder Depot ("18 x 189mm Nutmeg Oak Oiled T&G Engineered Wood Flooring")
- Ambience ("189mm Rustic Brushed & Oiled Engineered Oak 20mm")

## Distillation target

`knowledge/materials/residential-materials.md` (flooring section) — a widths row
for engineered oak, citing this unit. NOT yet distilled: staged only, and the
gate field that names it says so rather than claiming knowledge/ gained a line it
did not gain.

AUTHORITY NOTE: these are UK retail ranges. They answer "is this a width somebody
manufactures", which is what STY-7 needed. They are NOT a Thai-market supply
statement — for what is actually stocked in Thailand, ask the owner to ask a
practitioner (the practitioner-rung law), and never let this file stand in for
`knowledge/codes-th/`.
