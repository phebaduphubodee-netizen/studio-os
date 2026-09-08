# Element 3 amendment — the bed's TONAL LADDER (2026-07-23)

Amends D3-1 / D3-2 / D3-4 in VALUE only. No colour, no material identity and no geometry
decision is reopened: the hue is element 3's own signed base colour and every cloth below is
that hue at a different value — `knowledge/styles/color-composition.md` §1's monochromatic
harmony (*สีเดียวหลายน้ำหนัก*), the one harmony type that adds contrast without adding a
colour. The palette stays closed.

Live data: `pipeline/scripts/value_ladder.py`. This file is the RECORD, not the source —
every number here is printed by that module and by `pipeline/scripts/value_probe.py`.

## Why

`docs/strategy.md` carried "the bed is two near-white values and reads pale" from element 3
onward. Three passes fixed the bed's SHAPE and none touched its VALUE, because no module
owned value: each builder typed its own colour tuple.

## The measurement (hero eye camera, median sRGB luma, per OBJECT)

Instrument: `id_mask.py` re-renders the same camera with every object flat-emitting a
palette colour (1 sample, 0 bounces, Standard view transform); `value_probe.py` decodes it.
Hand-drawn region boxes were tried first and were WRONG — they straddled silhouettes and
reported four different objects as one value.

| piece | HEAD | now | cloth |
|---|---|---|---|
| `bed__base` | 121.1 | **74.7** | upholstery |
| `bed__throw` | 155.1 | **98.3** | upholstery |
| `bed__mattress` | 126.2 | 105.2 | sheet (unranked — 0.34 % of frame, occluded) |
| `bench__seat` | 178.2 | **134.3** | upholstery |
| `bed__coverlet` | 164.8 | **146.1** | coverlet |
| `bed__sham0` / `sham1` | 199.6 / 197.6 | **164.3** / 162.3 | duvet set |
| `bed__duvet_fold` | 204.7 | 176.1 | duvet set (unranked — the duvet's own hem) |
| `bed__duvet` | 199.4 | **182.0** | duvet set |
| `mill__style_lumbar__towel` | 188.6 | 184.9 | element-6 terry — deliberately unchanged |
| `bed__pillowsoft0` / `soft1` | 200.6 / 198.8 | **195.9** / 194.9 | pillowcase |

**Span 83.6 → 121.2 codes.** At HEAD six of the bed's ten pieces sat inside 7.1 codes of
each other, at the focal point of the frame.

## The three defects

1. **The head was one value.** The euro shams and the duvet's turned-back fold both wore
   the PILLOW material. Element 8's three-rank head ladder had its heights and the eye could
   not use them; a hem of the duvet was the brightest object in the bed.
2. **Albedo was not the lever.** `bed__base`, `bed__throw` and `bench__seat` carry the
   identical authored albedo and rendered 57 codes apart; `bed__coverlet`, authored 74 %
   brighter, rendered darker than `bench__seat`. So the tones are SOLVED from measurement,
   and the ladder is stated in rendered value — see the honest limitation below.
3. **The studio's 30–240 sRGB albedo band was never applied here**
   (`knowledge/materials/pbr-material-behavior.md:55`). `material_presets` clamps
   preset-driven colours at resolve time; `_build_bed`/`_build_bench` bypass `factory_args`
   entirely, so the pillows shipped at **243.5** — past the ceiling. (The mattress at 0.87
   = 239.8 was inside it; a first draft of this file indicted both and was corrected in
   review. One material out of bounds, not two.)
   `albedo_plausible()` guards 0.04–0.94 floats — a different band in a different unit, the
   OPEN item the vault records against itself at `pbr-material-behavior.md:177-186`.

## The five cloths (authored sRGB swatch codes)

| cloth | linear | sRGB | worn by |
|---|---|---|---|
| upholstery | 0.200 | 124 / 120 / 114 | bed base, foot bench, foot throw, vanity tub chair, wardrobe linen garments + folded knits |
| duvet set | 0.450 | 179 / 174 / 166 | duvet, its turned-back fold, both euro shams |
| coverlet | 0.600 | 203 / 197 / 189 | the solver-draped spread |
| sheet | 0.680 | 215 / 209 / 200 | mattress / sheet edge |
| pillowcase | 0.868 | 240 / 233 / 223 | the two sleeping pillows |

Five is what a bed actually has: a duvet SET is sold as cover plus euro shams in one
fabric, sheets are their own weight, pillowcases are the crisp ones, a coverlet is a
separate spread, upholstery is upholstery.

## Disclosed

- **Frame-scoped.** The per-rung targets were solved against ONE camera's light.
  `value_ladder.check_render()` scores them only on that frame and enforces ORDER and SPAN
  everywhere else — an instrument that cried wolf off-frame would get muted. The
  `bed_hero` camera holds the same order unprompted (84.2 · 107.0 · 144.5 · 157.0 · 169.2 ·
  185.8 · 199.8).
- **The upholstery rung reaches outside the bed.** `m_mill_linen` is worn by the wardrobe's
  linen garments and folded knits (via `styling.TOK_LINEN`), and `stool_uph` by the vanity
  tub chair, so those deepened too. One identity, one change — LOOK-verified on three
  cameras: `eye` (hanging garments), `wardrobe_bay_dressing` (folded knit stacks, which now
  alternate against the terry instead of washing into it) and `west_vanity` (the tub chair,
  which still renders 179 there under the west-casement daylight flood).
- **The tub chair was a fifth private copy of the "same" colour**, found by the pre-commit
  review: `_build_tub_chair` typed `(0.40, 0.37, 0.33)` under a comment insisting it was
  "NOT A NEW TONE", while the spec, the docstring and the armour all say it matches the bed
  base EXACTLY — and the test written to guard that checked a material the chair does not
  wear. It now takes the rung. The owner's 2026-07-22 LOOK ("the pale flat wrap read as
  ceramic") is honoured, not reverted: it asked for deeper than the then-0.46 family.
- **The room is deliberately less bright.** Whole-frame mean 121.1 → 107.3.
- **Not fixed here (geometry, not value):** the foot throw covers ~42 % of the bed top and
  is the largest single object in the frame at 8.7 % — a value pass cannot make it a
  narrower band, and `styling.foot_throw`'s 0.72 m band of a 2.0 m bed is a separate call.

---

## Amendment 2026-07-28 — the PEBBLE-FIX geometry pass, and the ladder re-anchored

The owner's LOOK on the ladder renders named three geometry defects the value work had
exposed: the cushions read as **pebbles/lenses** (a `sin(phi)` hemisphere profile collapsed
every silhouette to a pointed lens), the euro shams were **squat bands lying down** (235 mm
tall against the DD's own word "upright/standing"), and the throw at its 0.72 m band was
**the largest single object in both frames** — a second coverlet, not a styling accent.
Fixed: `softgoods.cushion` gained an edge-fullness profile (`edge=0.30`; at 10 % of height
the plan is at ~86 % width instead of 60 %), the shams became standing **king shams**
(0.80 × 0.44, `SHAM_W`/`SHAM_H`), the lumbar rose to 0.19 so the duvet fold stops occluding
it, and the throw band went to **0.50 m (25 %)** with the 2.2× band:hang floor retired in
the open (it was measured on an unpinned sheet; the tucked-edge pin now holds the throw,
and the bake still fails loudly if that stops being true — the resize attempt that misread
`hang` as visible fall was CAUGHT by the containment ladder, exactly as designed).

**Tones re-solved** for the new light distribution (standing shams shade the pillows;
the sham responds ~2.3× more steeply to the duvet_set tone than the duvet — wall-shadow
light): upholstery 0.188, coverlet 0.545, duvet_set 0.415; sheet/pillowcase unchanged.
**Targets re-anchored** to the measured accepted look (eye frame):

    base 73 · throw 90 · bench 131 · coverlet 142 · sham0 154 · duvet 181 · pillow 192
    span 119 codes; tightest adjacent gap 11.1; CLEAN on eye AND bed_hero

**Two-tier ORDER law** (`MIN_STEP_OFF = 6`): cross-camera light moves the coverlet
+9.7 codes and the sham +5.8 between the two verified views, so demanding the full
10-code styling step under every light forces ~1-code tone margins that flake on any
future edit. Off the solved frame the check is a **collapse alarm** (the original defect
measured 0.2–7.1 codes); on it, the styling margin stands.

**The all-grey question, measured and RECORDED FOR THE OWNER, not acted on:** after the
geometry pass every textile measures warm (r>g>b throughout, chroma 12–22 codes) and
57 % of the frame is warm pixels — the "one grey mass" read was the throw's AREA, which
is fixed. If the owner still wants more colour after seeing the frame, that is a palette
decision (new accent, or chroma-preserving deepening of the greige family) and reopens
signed identities — his call, not a sleep-shift's.
