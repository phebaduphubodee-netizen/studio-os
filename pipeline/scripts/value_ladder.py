#!/usr/bin/env python3
"""value_ladder.py — the suite's soft goods as a TONAL LADDER (pure; no bpy, no numpy).

WHY THIS EXISTS (2026-07-23). `docs/strategy.md` has carried the same unfixed line since
element 3: *"the bed is two near-white values and reads pale"*. Three passes softened the
bed's SHAPE (bevels, a floating base, a solver-draped coverlet, a real foot throw) and not
one of them touched its VALUE, because nothing in this build ever owned value. Each builder
typed its own colour tuple next to a comment arguing for it, and the ladder those tuples
produce in the render was never measured.

Measured, on the hero frame at HEAD (per-OBJECT, via an object-id mask — not eyeballed
region boxes), median sRGB luma:

    bed__duvet_fold 204.7 · pillowsoft0 200.6 · sham0 199.6 · duvet 199.4 ·
    pillowsoft1 198.8 · sham1 197.6 · lumbar 188.6 · bench__seat 178.2 ·
    coverlet 164.8 · throw 155.1 · mattress 126.2 · base 121.1

Three defects that only a measurement can see, and each kills a different claim:

  1. THE HEAD IS ONE VALUE. duvet_fold / pillowsoft0 / sham0 / duvet / pillowsoft1 /
     sham1 span 197.6-204.7 — six pieces inside 7.1 codes, at the focal point of the
     frame. Element 8 built a THREE-RANK head ladder because "three heights is the single
     most recognisable signal of a styled bed"; the heights are there and the eye cannot
     use them, because all three ranks are the same tone. And the brightest object in the
     whole bed is `bed__duvet_fold` — a turned-back fold of the duvet that was wearing the
     PILLOW material, so the duvet's own hem out-valued the pillows it lies below.

  2. ALBEDO WAS NEVER THE LEVER ANYONE THOUGHT IT WAS. `bed__base`, `bed__throw` and
     `bench__seat` carry the IDENTICAL authored albedo (0.46, 0.43, 0.39) and render at
     121.1 / 155.1 / 178.2 — 57 codes apart from orientation and local light alone. Over
     the same frame `bed__coverlet`, authored 74% brighter (0.80), renders DARKER (164.8)
     than `bench__seat` (178.2). Whatever ladder the render shows, nobody authored it.
     Which is why this module's targets are stated in RENDERED value and its albedos are
     SOLVED against a measurement, instead of typed and hoped for.

  3. THE STUDIO'S OWN ALBEDO BAND WAS NEVER APPLIED HERE. The band is 30-240 sRGB
     (knowledge/materials/pbr-material-behavior.md:55; threshold key
     `material_qa.albedo_srgb`). material_presets clamps every PRESET-driven colour into
     it at resolve time — but `_build_bed`/`_build_bench` author LINEAR tuples straight
     into the BSDF and never touch `factory_args`, so the pillows shipped at 0.90 linear
     = sRGB 243.5, PAST the ceiling. (Corrected in review: the first draft of this
     paragraph also indicted the mattress at "0.87 = 240.5". 0.87 linear is 239.83 — just
     INSIDE the band. One material was out of bounds, not two, and a defect statement that
     overcounts its own evidence is the same disease as prose that outlives it.)
     build_room's `albedo_plausible()` could not see even the real one: it flags floats
     outside 0.04-0.94, a band in a DIFFERENT UNIT that 0.90 passes — the "two albedo bands are live in the studio"
     OPEN item the vault records against itself (pbr-material-behavior.md:177-186). The
     same hole was already found and plugged for ROUGHNESS inside `_woven` ("the bespoke
     _build_bed / _build_bench calls pass their roughness straight in and never touch
     factory_args, so the bound has to be applied HERE or it is not applied at all");
     albedo is the other half of that sentence, and this module is it.

WHAT IS SIGNED, WHAT IS AMENDED, AND THE ONE THING THAT IS SUPERSEDED. The suite's
textile IDENTITIES stand unchanged and unreopened:
  D3-1  bed base = upholstered greige stonewashed LINEN, not oak (anti-monopoly D1-A)
  D3-2  bedding = greige-oatmeal stonewashed linen
  D3-4  the foot bench matches the bed base
Every tone below is the SAME greige, one hue in several values —
`color-composition.md` §1's monochromatic harmony (สีเดียวหลายน้ำหนัก), the one harmony
type that adds contrast without adding a colour. The palette stays closed, no new material
enters, and no piece changes what it is made of.

SUPERSEDED — D3-1's RATIONALE, not its material (owner loop OPEN, 2026-07-23). The first
draft of this header said "this module does not reopen any of them" and then listed two
small amendments while omitting the largest change in the file. That was false, and the
pre-commit review called it. D3-1 was signed with a specific reason: *"A LIGHT greige linen
joins the ~60% plaster ground (Albers: a light element on a light ground recedes), so the
warm oak slat headboard wall + the crisp bedding carry the eye."* The upholstery rung takes
that base from linear 0.46 (sRGB 181) to 0.20 (sRGB 124) — it no longer joins the ground and
no longer recedes; it grounds. The evidence for overturning it is the render the rationale
was written to produce: the base, the bench and the throw wear that one cloth and measured
121.1 / 155.1 / 178.2, with the BENCH sitting 13 codes ABOVE the coverlet it stands in front
of. Albers' ground-subtraction is real, and it was being applied to the wrong element — the
sheer (element 1, D8) joins the light ground correctly; the piece the eye lands on first
should not. Recorded, not smuggled: see
`projects/PRJ-2026-002_c001-house/03_layout/element3-bed_TONAL-LADDER-2026-07-23.md`, and
the spec's own owner-signed `items[1].design.decision` carries an amendment note flagged
for the owner rather than being quietly rewritten.

AMENDED in the open (no owner loop needed — neither was owner-signed):
  - the euro shams leave the pillowcase and join the DUVET SET, one rung under the sleeping
    pillows. Two pieces of a bedding set at two values is how bedding is sold; two pieces at
    ONE value with a 100 mm height difference between them is what defect 1 is.
  - the duvet's turned-back FOLD leaves the pillowcase for the duvet's own cloth, because
    it is the duvet.

HOW INDEPENDENT "CLEAN" ACTUALLY IS. Five cloths drive seven rungs, so a clean
`check_render` is not seven independent successes: `upholstery` alone carries three rungs
(73 / 90 / 131) and `duvet_set` carries two (154 / 181). A tone was solved from ONE object
per cloth and the sibling rungs are what the frame's light does to the same cloth on other
faces — the per-object spreads (58 codes across the three upholstery pieces, 26 between
the standing shams and the lying duvet) are LIGHT, not authoring, and that is the whole
finding of defect 2.

THE HONEST LIMITATION. These albedos are SOLVED against the hero frame's lighting: they
are the fabrics a stylist would choose knowing where this room's light falls. Under a
different key the same cloths render a different ladder — so `check_render()` is not a
build-time gate, it is a LOOK-time instrument, and it must be re-run on any camera whose
verdict is being claimed. The build-time half (`validate()`) checks only what is true
independent of light: the band, the hue, and that every ladder rung has a tone.
"""

import material_presets as _mp

# --------------------------------------------------------------------------- the band
# knowledge/materials/pbr-material-behavior.md:55 — non-metals "should strictly fall
# between 30 and 240 sRGB". Re-exported from material_presets rather than re-typed: two
# copies of a bound is how one of them goes stale.
SRGB_BAND_LO, SRGB_BAND_HI = _mp._SRGB_BAND_LO, _mp._SRGB_BAND_HI

# --------------------------------------------------------------------------- the hue
# The signed greige linen's LINEAR channel ratios, taken from element 3's own base colour
# (0.46, 0.43, 0.39) — D3-1's tone, kept exactly. Every tone below is this hue at a
# different value, so the family cannot drift by construction: there is no per-piece
# colour to mistype. (The old bedding tuples drifted anyway — the pillows were authored
# at ratios 1 : 0.978 : 0.933 against the base's 1 : 0.935 : 0.848, i.e. markedly LESS
# chromatic: nearer neutral, which is why signed "greige-oatmeal" D3-2 rendered as a
# near-WHITE rather than as the warm greige it names. Unifying the family on the base's
# ratios raised measured chroma on every bed piece — 12-18 codes at HEAD, 13-20 now — so
# this is the opposite move from desaturating. Element 6 carries the same rule for its
# sibling textile: "greige must not read cream".)
HUE = (1.0, 0.43 / 0.46, 0.39 / 0.46)

# --------------------------------------------------------------------------- the tones
# TONE = the authored LINEAR value of the red channel. This is the ACTUATOR, not the
# design: see LADDER below for the design.
#
# FIVE CLOTHS, and they are the five a bed actually has — a duvet SET is sold as cover
# plus euro shams in one fabric, sheets are their own weight, pillowcases are the crisp
# white ones, a coverlet is a separate spread, and the upholstery is upholstery. Two of
# these did not exist before: the euro shams and the duvet's own turned-back fold were
# both wearing the PILLOWCASE, which is why the head rendered as one value and why a hem
# of the duvet was the brightest object in the bed.
#
# THE VALUES ARE SOLVED, NOT TYPED. Two full renders were measured per-object (HEAD, then
# a deliberately loud pass), a power-law fit taken per piece, and each tone inverted from
# the rendered target below. That is the only honest way here, because the same authored
# albedo rendered 57 codes apart on different pieces of this room at HEAD — see defect 2.
TONES = {
    # 2026-07-28 (2): the standing shams respond ~2.3x more steeply to the duvet_set tone
    # than the duvet does (wall-shadow light), so the first re-solve moved the pinch from
    # duvet->pillowcase to coverlet->sham instead of closing it. The top of the ladder is
    # boxed in — the pillowcase sits at the 240 band ceiling and the sham rides ~26 codes
    # under the duvet on the SAME cloth — so the room comes from the bottom, where the
    # gaps run 17-40 codes: upholstery and coverlet each give ~2-3.
    # 2026-08-15 (p2r35), 0.188 -> 0.150. THE FIRST MOVE ON THIS RUNG THAT IS NOT
    # CHASING A TARGET, and the distinction is D-058's: the seven absolute targets in
    # LADDER were re-anchored to our own 2026-07-28 render, so a deviation from one is
    # a distance from an old picture, not a defect. What SURVIVES that objection is
    # ORDER and MIN_STEP, because those are relationships between rungs. check_render
    # on the p2r35 frame filed exactly such a failure:
    #     upholstery (bench__seat) 162.7 and coverlet (bed__coverlet) 164.1
    #     -> 1.4 codes apart, under MIN_STEP 10.0. They read as one piece of cloth.
    # And it is the frame's loudest complaint said in numbers: every critic reads the
    # bed as ONE PALE MASS, and the bench is the largest foreground object in it (8.0%
    # by id mask) sitting at the coverlet's own value. The spec asks for the opposite in
    # its own words — the upholstery "grounds the bed and keeps the foreground BELOW the
    # bedding behind it".
    #
    # THE MOVE IS INVERTED PER OBJECT FROM THIS FRAME, not from another piece's slope.
    # One authored albedo renders 106.3 / 139.6 / 162.7 on base / throw / bench, so the
    # light — not the cloth — is what spread this rung across 57 codes. Decoding each
    # rendered code to linear and dividing by the authored 0.188 gives each object's own
    # illumination factor on this frame: base 0.77, throw 1.39, bench 1.94. At 0.150 the
    # same three predict 96 / 126 / 147, i.e. a bench->coverlet gap of ~17 codes against
    # a floor of 10, with the rung's internal order untouched.
    # PREDICTED, therefore CHECKED by check_render on the next full render, never
    # asserted (D-053). Bounce falls with albedo, so the true response is slightly
    # steeper than this and the prediction should land a little DARK — which is the
    # direction with margin.
    # DISCLOSED, unchanged from the note below: this rung also dresses the wardrobe's
    # linen garments and folded knits, and they darken with it. That is one identity and
    # one change, which is the point of the table.
    # 2026-08-16 (p2r42), 0.150 -> 0.077, AND THE SAME SOLVE ON THREE OTHER RUNGS
    # BELOW. The owner looked at the frame and said *"ผ้าบนเตียงยังเละอยู่เลย"*.
    # check_render on that frame, run by hand because nothing failed on it:
    #     base 91.3 (+18.3) · throw 127.5 (+37.5) · coverlet 162.2 (+20.2) ·
    #     duvet 208.3 (+27.3), tolerance +-8 — and three rungs unscored.
    # Every visible rung ABOVE its target, the whole cloth stack riding at the top
    # of the frame's range: measured against the delivered-work anchors, their
    # duvet planes sit at 0.51-0.67 of their own frame's 99th-percentile luma and
    # ours sat at 0.77-0.93. A bed that is the brightest mass in the room has no
    # value left to separate its own layers with, which is what "เละ" measures as.
    # (Fold structure was NOT the defect and was tested first: on a rectangle
    # wholly inside one cloth, delivered duvets run 2.30-6.36 octave energy and
    # ours 2.13-5.77 — inside the band. Ten rounds of crease/drape work had been
    # aimed at a metric that was never off.)
    # SOLVED, NOT NUDGED: for a diffuse surface under fixed light the rendered
    # linear value is albedo x an illumination factor, so each rung's own factor
    # comes from THIS frame (linear(rendered) / authored tone) and the tone that
    # lands the signed target is linear(target) / factor. Where one tone serves
    # several objects the answer is their area-weighted log mean, which is the
    # least-squares fit in the space the solve is linear in.
    # bench__seat is EXCLUDED from this rung's solve, measured not assumed: the
    # id/mat mask cross-reference shows bench__acq0 rendering in a material called
    # `Ottoman_01`, i.e. the acquired bench is retinted from element_preset and
    # never took this tone at all. That is its own open defect (acquired meshes
    # escape the value system) and pulling this rung to cover it would have put
    # base and throw 21-33 codes out.
    # PREDICTED at 0.077: base 65.7 (-7.3) · throw 93.2 (+3.2), both inside
    # tolerance. PREDICTED, therefore CHECKED by check_render on the next full
    # render, never asserted (D-053) — and from p2r42 that check FAILS THE BUILD.
    "upholstery": 0.0848,  # bed base + foot bench + foot throw + the vanity tub chair
    #                       (D3-1/D3-4), and the wardrobe's linen garments + folded knits,
    #                       which wear the same suite token (styling.TOK_LINEN). DISCLOSED:
    #                       deepening this rung deepens those too — one identity, one change.
    #                       LOOK-verified on three cameras, not asserted: `eye` (the hanging
    #                       garments, left third), `wardrobe_bay_dressing` (the folded knit
    #                       stacks, which now alternate against the terry instead of washing
    #                       into it) and `west_vanity` (the tub chair). The review was right
    #                       to challenge the first draft, which claimed verification "in the
    #                       same frame" for pieces that frame does not contain.
    # 2026-07-28, re-solved after the PEBBLE-FIX geometry pass (standing king shams, plump
    # pillows, the throw at 0.50): the taller shams shade the sleeping pillows (195.9 ->
    # 192.9 rendered), which pinched the duvet->pillowcase gap to 9.9 codes — under
    # MIN_STEP, caught by check_render on the first probe of the new geometry. The
    # pillowcase is parked at the 240 band ceiling and cannot rise, so the room is bought
    # BELOW it: duvet_set and coverlet each step down, re-inverted through the same
    # per-object power fits as the original solve.
    # 2026-08-15 (p2r31), 0.545 -> 0.435: the FIRST measurement of this ladder
    # since the light story went on (2026-08-11). check_render had not been
    # called by build or gate at all — it is a standalone tool nobody invoked —
    # so twelve rounds shipped with every visible rung 28-49 codes over target
    # and no line anywhere saying so. Run at last on the p2r31 frame: base
    # +33.6, throw +49.3, coverlet +46.3, duvet +27.7. The ORDER and the SPAN
    # (117 codes, floor 95) still hold, so the cloths are not wrong — the story
    # light lifted everything, and it lifted the deep end most, which is what
    # collapsed the design's coverlet->duvet gap from 39 codes to 20 and made
    # the owner read the bed as layers he could not tell apart ("ทำไมมันมีอะไร
    # ซ้อนข้างในเตียง"). This ONE rung moves, and it moves TOWARD its own signed
    # target (188.3 -> ~170 predicted, target 142), never away: inverted through
    # the same sRGB response the original solve used, 0.9028^2.2. The other six
    # rungs are left alone deliberately — re-anchoring all seven to whatever we
    # currently render is self-consistency, the wound this repo has already
    # paid for twice. Predicted, therefore CHECKED after the render, never
    # asserted (D-053).
    # SECOND STEP, and this one is FITTED not guessed. The 0.545 -> 0.435 move
    # predicted 170 from an sRGB power law and delivered 179.2 — the response
    # under this room's bounce-heavy story light is shallower than a diffuse
    # power law assumes, which is the same lesson the original solve recorded
    # ("the same authored albedo rendered 57 codes apart on different pieces").
    # Two MEASURED points on this frame now define the line: 0.545 -> 188.3 and
    # 0.435 -> 179.2, i.e. 82.7 codes per unit tone. The designed coverlet ->
    # duvet gap is 39 codes; at 179.2 it stands at 29.1, so the rung needs
    # -10.2 more codes = -0.123 tone. Predicted 169.0, gap 39.3 — and predicted
    # means CHECKED by the ladder rung on the next render, never asserted.
    # p2r42: the same one-step solve as `upholstery` above — each rung's own
    # illumination factor read off the frame the owner rejected, then the tone
    # that lands the SIGNED target. 0.312 -> 0.233 predicts the coverlet at 142.0
    # against a target of 142.0.
    "coverlet":   0.1820,  # the bed's main field, the solver-draped spread
    # p2r42, 0.68 -> 0.5012, AND IT WAS THE ARMOUR THAT DEMANDED IT. The sheet is
    # the one cloth with no rung in LADDER (unranked: 0.34% of frame, occluded),
    # so the solve above skipped it — and the test that pins "the pillowcase is
    # the lightest cloth" failed instantly, because dropping the other four would
    # have left the SHEET as the brightest cloth in the room. That is not a
    # hypothetical: on the acquired leg the mattress is 165k px of exposed
    # near-white at 0.94 of the frame's top value, the single loudest thing in
    # the frame.
    # There is no target to solve against, so what is preserved is the RELATION,
    # which is the design fact here — one hue at several values (color-composition
    # §1). The sheet sat 0.669 of the way in log space from duvet_set to
    # pillowcase; it still does. Predicted 153.3 -> 133.3 on the mattress.
    "sheet":      0.3401,  # the mattress/sheet edge showing under the coverlet
    # p2r42, 0.415 -> 0.289. This tone serves TWO rungs whose light has drifted
    # apart (duvet needs 0.303, sham needs 0.251) and one cloth cannot land both:
    # the area-weighted answer puts the duvet at 177.1 (-3.9, inside) and the
    # acquired sham at ~164 (+10, outside). SPLITTING the fabric would close it and
    # is refused — the signed design says a duvet SET is cover plus shams in ONE
    # cloth, and inventing `bed_sham` to make a number go green is changing the
    # design to fit the instrument. The sham is an ACQUIRED rung (ACQUIRED_AS), so
    # its point target is reported and its ORDER and SPAN enforced; 164 sits inside
    # the [152, 167] window MIN_STEP leaves between coverlet and duvet.
    "duvet_set":  0.1360,  # duvet + its turned-back fold + the two euro shams (one cloth)
    # p2r42, 0.868 -> 0.658. The old value was set to park just under the 240 sRGB
    # band ceiling, i.e. against the BAND rather than against the render, and the
    # render put the acquired pillows at 217-220 — the two brightest objects in the
    # frame. 0.658 predicts 192.0 on the pillowcase rung's own target of 192.0.
    "pillowcase": 0.5350,  # the sleeping pillows — the lightest thing in the room, by design
}

# Which build material wears which tone. The build asks BY NAME; a builder that invents
# its own tuple is the defect this table replaces.
MATERIAL_TONE = {
    "m_mill_linen": "upholstery",
    "bed_base":     "upholstery",     # also the foot THROW: same cloth, and the render
    #                                   already separates them by 23 codes (see LADDER) —
    #                                   a second tone would be a decision the light already
    #                                   made for free
    "bench_seat":   "upholstery",
    "stool_uph":    "upholstery",     # the BF11 vanity tub chair. Added after the pre-commit
    #                                   review found it holding a FIFTH private copy of this
    #                                   colour under a comment insisting it was "NOT A NEW
    #                                   TONE" — and found that this module's own test claimed
    #                                   the chair shared the rung while checking a material
    #                                   the chair does not wear
    "bed_coverlet": "coverlet",
    "bed_mattress": "sheet",
    "bed_duvet":    "duvet_set",      # + bed__duvet_fold + bed__sham0/1 (see HEAD_CLOTH)
    "bed_pillow":   "pillowcase",
}

# WHICH MATERIAL EACH HEAD PIECE WEARS — data, not a dict typed inside the builder.
# `styling.pillow_bank` emits pieces named `bed__<stem><n>`; this maps the stem to the
# material. It is here rather than in build_room because THIS mapping IS defect 1: the
# shams and the duvet's fold wore `bed_pillow`, and the line that said so was a literal
# inside `_build_bed` that no test could see. Reverting it there now goes red twice — the
# builder reads this table, and the builder has no default to fall back to.
HEAD_CLOTH = {
    "sham":       "bed_duvet",        # a duvet cover and its euro shams are one fabric
    "pillowsoft": "bed_pillow",       # the crisp sleeping pillows
}

# --------------------------------------------------------------------------- the design
# LADDER = what the EYE must be able to rank, darkest first, stated in RENDERED median
# sRGB luma on the hero frame, with the object each rung is measured on and the cloth that
# drives it. THIS is the design decision; TONES above is only how it is reached.
#
# Rungs are OBJECTS, not cloths, and several rungs share a cloth on purpose: the frame
# separates `bed__base` (73), `bed__throw` (90) and `bench__seat` (131) by 58 codes while
# all three wear the identical upholstery linen, because they face different ways in
# different light. Ranking cloths would have missed that entirely — and chasing it with
# per-object albedos would have been three lies about one fabric.
#
# Steps are >= MIN_STEP because that is what "reads as two things" costs. The span is what
# "reads as a bed and not a blob" costs: at HEAD the bed spanned 83.6 codes with six of
# its ten pieces inside 7.1 of each other.
MIN_STEP = 10.0            # codes between ADJACENT rungs, on the frame the tones are
#                            solved against — the styling margin the design paid for
MIN_STEP_OFF = 6.0         # the same check on any OTHER camera. Two-tier ON PURPOSE
#                            (2026-07-28): between the two verified cameras this room's
#                            light moves the coverlet +9.7 codes and the sham +5.8 — in
#                            OPPOSITE directions relative to each other — so demanding the
#                            full 10 under every light forces tone fits with ~1-code
#                            margins that go red on any future geometry edit, and a check
#                            that is red for reasons nobody can act on gets explained away
#                            (the muted-instrument failure). Off-frame the check is a
#                            COLLAPSE ALARM: the defect it exists to catch measured 0.2-7.1
#                            codes between piled-up pieces, and 6 still catches that with
#                            room, while an 8-code cross-light squeeze between two pieces
#                            the eye separates by geometry is not a defect.
MIN_SPAN = 95.0            # codes from the darkest rung to the lightest

# THE FRAME THE TARGETS WERE SOLVED ON. The per-rung numbers below are only meaningful
# here: they were inverted from measurements of THIS camera's light, and the same cloth
# renders 59 codes apart on this camera alone. On any other view the targets are noise —
# but the ORDER and the SPAN are not, because "the bed must not read as one mass" is a
# claim about every frame that shows the bed. check_render() therefore splits the two and
# refuses to score targets it cannot honestly score, instead of quietly crying wolf.
FRAME = "eye"              # the canonical hero eye camera (spec.eye_camera)

# THE FRAME NAME IS A CLOSED VOCABULARY. `check_render` turns the target checks OFF for any
# frame that is not FRAME, so a TYPO would silently disable all seven of them and still
# print CLEAN — the flattering-instrument shape, and the exact reason build_room hard-exits
# on an unknown `--eyecam` name instead of falling back. These are the canonical spec's
# `eye_camera_variants` keys plus the bare eye camera; `test_value_ladder` re-derives them
# from that file, so this list cannot drift from the cameras that exist.
KNOWN_FRAMES = frozenset((
    FRAME, "bed_hero", "corner_ne_legacy", "curtains_semouth",
    "curtains_south", "ensuite_hooks_east",
    "ensuite_mirror", "ensuite_towels_west", "ensuite_vanity", "ensuite_wet",
    "wardrobe_bay_doorlane", "wardrobe_bay_dressing", "wardrobe_bay_entry",
    "west_bookshelf", "west_vanity",
))

# Targets re-anchored 2026-07-28 to the measured pebble-fix geometry (standing king
# shams, plump pillows, the throw at 0.50 band): a standing sham lives in wall-shadow
# light and legitimately renders ~26 codes under its own cloth's duvet, so the old squat
# targets (sham 164) stopped describing any object that exists. Tightest adjacent gap in
# this set: 11.1 codes.
LADDER = (
    ("upholstery", "bed__base",         73.0),
    ("upholstery", "bed__throw",        90.0),
    ("upholstery", "bench__seat",      131.0),
    ("coverlet",   "bed__coverlet",    142.0),
    ("duvet_set",  "bed__sham0",       154.0),
    ("duvet_set",  "bed__duvet",       181.0),
    ("pillowcase", "bed__pillowsoft0", 192.0),
)
# NOT in the ladder, on purpose (each would be a lie to rank):
#   bed__mattress   — 0.34% of the frame and almost entirely occluded by the coverlet it
#                     lies under. It still gets a TONE (a sheet is a real cloth) but
#                     ranking a sliver of shadow would pin noise, not design.
#   the duvet's turned-back fold — the duvet's own hem: same cloth, adjacent, and it
#                     lands between the shams and the duvet by itself. Ranking a piece
#                     against its own parent passes forever and means nothing. (Since
#                     2026-07-28 round 3 it is not even a separate OBJECT: the duvet is
#                     simulated cloth — softgoods.folded_sheet — and the fold is part of
#                     bed__duvet's own lattice, duvt_m by construction.)
#   the second sham / second pillow — mirrored twins of the ranked ones.
TOLERANCE = 8.0            # codes a rung may miss its target by before the LOOK fails


class LadderError(ValueError):
    """A tone/ladder violation. Raised, never warned: a silently-repainted signed textile
    is this studio's recurring wound (six elements running)."""


def _fail(msg):
    raise LadderError(msg)


def linear_to_srgb_code(v):
    """LINEAR 0..1 -> the 0..255 sRGB texel code the studio band is stated in."""
    return _mp.linear_to_srgb(v) * 255.0


def rgba(material):
    """The LINEAR (r, g, b, a) a build material wears. RAISES on an unknown name — a
    typo must not silently fall back to a default tone (that default is exactly how the
    bed became one value)."""
    tone = MATERIAL_TONE.get(material)
    if tone is None:
        _fail(f"value_ladder: no tone for material {material!r} "
              f"(known: {sorted(MATERIAL_TONE)})")
    v = TONES[tone]
    return (v * HUE[0], v * HUE[1], v * HUE[2], 1.0)


def codes(material):
    """The same tone as sRGB texel codes — what a human reads off a swatch, and the unit
    the 30-240 band is stated in."""
    return tuple(round(linear_to_srgb_code(c), 1) for c in rgba(material)[:3])


def validate():
    """Everything checkable WITHOUT a render. Called at build time so a bad tone cannot
    reach a deliverable, and by the tests so it cannot reach a commit."""
    # (1) every tone inside the studio's dielectric albedo band, in the band's own unit.
    #     The ceiling is the tone's BRIGHTEST channel and the floor its DARKEST, taken from
    #     HUE rather than assumed to be red and blue: a future re-hue that is not warm
    #     descending (say a cool greige with b > g) would otherwise be checked on the wrong
    #     two channels and could ship a tone outside the band with validate() green.
    #     THE AUTHORED VALUE IS THE CEILING, WHICH IS WHY CHECKING IT IS ENOUGH: `_woven`
    #     drives Base Color through a MULTIPLY whose factor runs [1 - albedo_var, 1.0]
    #     (build_room.py, "MULTIPLY so the SIGNED colour is the CEILING"), so the texture
    #     can only ever darken. The band's UPPER bound therefore binds exactly here; its
    #     lower bound is checked conservatively — the true floor is another albedo_var
    #     below (8.5% on linen), and at the shipped tones that is sRGB 110 against a floor
    #     of 30, so there is no case where the drift alone could cross it.
    for name, v in sorted(TONES.items()):
        hi = linear_to_srgb_code(v * max(HUE))
        lo = linear_to_srgb_code(v * min(HUE))
        if hi > SRGB_BAND_HI + 1e-6:
            _fail(f"value_ladder: tone {name!r} = {v} linear = sRGB {hi:.1f}, over the "
                  f"studio dielectric ceiling {SRGB_BAND_HI} "
                  f"(pbr-material-behavior.md:55). This is the check the pillows "
                  f"(0.90 = 243.5) shipped past for four elements")
        if lo < SRGB_BAND_LO - 1e-6:
            _fail(f"value_ladder: tone {name!r} = {v} linear -> blue channel sRGB "
                  f"{lo:.1f}, under the studio floor {SRGB_BAND_LO}")
    # (2) every material maps to a tone that exists, and every tone is worn by something.
    #     An orphan tone is a decision nothing renders — the revert-by-omission shape.
    for mat, tone in sorted(MATERIAL_TONE.items()):
        if tone not in TONES:
            _fail(f"value_ladder: material {mat!r} wants tone {tone!r} which does not exist")
    unworn = sorted(set(TONES) - set(MATERIAL_TONE.values()))
    if unworn:
        _fail(f"value_ladder: tones {unworn} are authored but no material wears them — "
              f"a tone nothing renders is a decision the render reverted")
    # (3) the ladder is a ladder: strictly increasing, every step legible.
    ranked = sorted(LADDER, key=lambda r: r[2])
    for (an, ao, av), (bn, bo, bv) in zip(ranked, ranked[1:]):
        if bv - av < MIN_STEP - 1e-9:
            _fail(f"value_ladder: rungs {an!r} ({av}) and {bn!r} ({bv}) are "
                  f"{bv - av:.1f} codes apart — under MIN_STEP {MIN_STEP}. Two rungs the "
                  f"eye cannot separate are one rung, which is the defect this file exists "
                  f"to remove")
    span = ranked[-1][2] - ranked[0][2]
    if span < MIN_SPAN - 1e-9:
        _fail(f"value_ladder: the ladder spans {span:.1f} codes, under MIN_SPAN "
              f"{MIN_SPAN} — at HEAD the bed spanned 83.6 and read as one mass")
    # (4) every rung names a tone that exists (so a renamed tone cannot orphan the design).
    for name, obj, _v in LADDER:
        if name not in TONES:
            _fail(f"value_ladder: ladder rung {name!r} (on {obj!r}) has no tone")
    # (5) no two cloths at the same value. "FIVE cloths" is a claim the armour makes and
    #     the polish pass is told; two of them authored identically would make it four
    #     wearing five names, and nothing else here would notice.
    dupes = sorted(n for n, v in TONES.items()
                   if sum(1 for w in TONES.values() if abs(w - v) < 1e-9) > 1)
    if dupes:
        _fail(f"value_ladder: cloths {dupes} are authored at the same value — they are one "
              f"cloth wearing several names, and the armour would still say {len(TONES)}")
    # (6) no object ranked twice. A duplicated rung passes every other check here, inflates
    #     story_line()'s piece count, and lets one measurement satisfy two rungs.
    objs = [obj for _n, obj, _v in LADDER]
    if len(set(objs)) != len(objs):
        twice = sorted({o for o in objs if objs.count(o) > 1})
        _fail(f"value_ladder: {twice} appear(s) more than once in the ladder — one "
              f"measurement cannot honestly satisfy two rungs")
    # (7) every ladder rung names an object the BUILD actually emits. The ladder is the
    #     design and the build is the render; a rung naming a piece that no longer exists
    #     would go quietly unmeasured for the rest of the project (check_render reports it,
    #     but only if somebody runs a probe). Checked as data, from the two sources that own
    #     the names: build_room's own literals and styling.pillow_bank's stems.
    _emitted_or_fail(objs)
    return True


# Objects `_build_bed`/`_build_bench` emit directly (build_room owns these literals; this
# list is pinned against its SOURCE by test_value_ladder, so it cannot drift silently).
BUILT_OBJECTS = ("bed__base", "bed__mattress", "bed__coverlet", "bed__duvet",
                 "bed__throw", "bench__seat")


def _emitted_or_fail(objs):
    """RAISE if a ladder rung names an object nothing builds. Head pieces come from
    `styling.pillow_bank` as `bed__<stem><n>`, so they are checked against HEAD_CLOTH's
    stems rather than against a second copy of their names."""
    stems = tuple(HEAD_CLOTH)
    for obj in objs:
        if obj in BUILT_OBJECTS:
            continue
        if obj.startswith("bed__") and any(
                obj[len("bed__"):].rstrip("0123456789") == s for s in stems):
            continue
        _fail(f"value_ladder: ladder rung on {obj!r} — nothing in the build emits that "
              f"object (built: {sorted(BUILT_OBJECTS)}; head stems: {sorted(stems)})")


# WHEN A RUNG'S OBJECT IS BOUGHT INSTEAD OF BUILT (p2r42, 2026-08-16).
#
# THE EVENT. p2r38 acquired the foot bench and the head cushions. `place_model`
# names an acquired mesh `<tag>__acq<N>`, so `bench__seat` became `bench__acq0`
# and `bed__sham0` / `bed__pillowsoft0` became `bed__headset0__acq0` and
# `__acq1`. The CLOTH was still right — the head set is handed `HEAD_CLOTH`'s own
# materials at placement, so both meshes render in `bed_duvet` and `bed_pillow`
# and take those tones. Only the ladder's NAMES went stale, and `check_render`
# has one bucket for a stale name and a missing object: "no measurement — the
# probe did not see it (occluded, renamed, or not built)". Three of seven rungs
# said that on every build from p2r38 to p2r41, and the build shipped anyway,
# because the caller treated exit 1 as a note. The owner found the result by eye:
# *"ผ้าบนเตียงยังเละอยู่เลย"*.
#
# WHAT IS DECLARED HERE AND WHAT IS DERIVED. The pairing — "the bench that fills
# the bench slot is the thing the bench rung ranks" — is a DESIGN fact and cannot
# be computed, so it is written down once, in the module that owns value. Which
# actual mesh it is, is DERIVED: the prefix comes from `place_model`'s own naming
# contract, the material comes from the id-mask sidecar's `wears` block, and the
# pair has to resolve to EXACTLY ONE object. Zero is the old violation, and more
# than one is a violation too — an ambiguous resolution that quietly picks a
# member is how a rung starts measuring whichever mesh sorted first.
#
# WHAT AN ACQUIRED RUNG IS SCORED ON, AND WHY IT IS LESS. The per-rung target is
# a POINT solved against the SOLVER object's own geometry under one light: 154
# was measured on a built 0.80 x 0.44 standing king sham. A bought cushion is a
# different shape with a different normal distribution, so scoring it against
# that number is this repo's own defect of measuring one thing with another
# thing's figure. So an acquired rung is scored on ORDER and SPAN — which are
# claims about the BED, not about a mesh — and its distance from the point target
# is REPORTED as a note naming the replacement. That is a real loss of grip and
# it is written in the report rather than hidden: re-deriving the point target
# from what the acquisition happens to render would be scoring the frame against
# itself.
ACQUIRED_AS = {
    "bench__seat":      ("bench__acq", "bench_seat"),
    "bed__sham0":       ("bed__headset0__acq", "bed_duvet"),
    "bed__pillowsoft0": ("bed__headset0__acq", "bed_pillow"),
    # p2r44 — THE BED CLOTH ITSELF, now that his 2026-08-14 / 2026-08-15 orders
    # are carried out and the coverlet and duvet are bought rather than solved.
    # `_place_bed_cloth` names every kept part `bed__cloth__acq<N>` and hands the
    # FIELD parts `cov_mat` and the parts LYING ON IT `duv_mat` — the same split
    # the part cut already made, so the pairing below is that decision read back
    # rather than a second guess. Same loss of grip as every acquired rung: the
    # point target was solved on the SOLVER's own geometry, so it is reported and
    # ORDER/SPAN are what bind.
    "bed__coverlet":    ("bed__cloth__acq", "bed_coverlet"),
    "bed__duvet":       ("bed__cloth__acq", "bed_duvet"),
    # p2r52 — THE WHOLE BED (D-106/D-107): the base rung's own object leaves the
    # scene with the hand-built bed and the acquired frame takes its rung. The
    # frame hook names the platform `bed__frame__acq0` and dresses it in the
    # base linen; `bed__frame__acq1` is the mattress (bed_mattress — not a rung,
    # same reason bed__mattress never was). Duvet/sham/pillow resolve through
    # the rows above unchanged, because the hook names its parts into the same
    # register (`bed__cloth__acq0`, `bed__headset0__acq0/1`).
    "bed__base":        ("bed__frame__acq", "bed_base"),
}

# A RUNG WHOSE OBJECT IS ABSENT ON PURPOSE, AND THE DECISION THAT SAYS SO.
#
# p2r44. This is the third time in one day that the same distinction turned out
# to be the fix, so it gets a name: "I could not measure it" and "it is not there
# and we said so" are DIFFERENT SENTENCES, and a rung that reports them as one
# either blocks a lane over a signed decision or lets a real absence pass as a
# shrug. `sourcing_check` needed it between `not-attempted` and `n/a`; the p2-exit
# rungs need it for a mask half whose material is gone; the ladder needs it here.
#
# The bar is deliberately high: the object must be absent by a DECISION ROW with
# an id, and the reason has to be the measurement that produced it. Adding a row
# here to quiet a rung is the defect; the row is only honest when the absence was
# already decided somewhere a reader can check.
DECLARED_ABSENT = {
    "bed__throw": ("D-083", "the acquired cloth set falls to the bed line itself "
                            "— 0 mm of line left for a runner to hang in "
                            "(measured 85-95 mm proud at every rung, and the "
                            "length levers did not move it). The deepest-value "
                            "job it did is open as ASK-020, not as a licence to "
                            "hand-build it again."),
    "bed__duvet": ("D-086", "the acquired set 0afd4c6f is ONE field cloth — the "
                            "part cut keeps 1 field part and 0 parts lying on "
                            "it — so there is no separate duvet layer to "
                            "measure. The duvet_set RUNG is still measured, on "
                            "the euro shams that wear the same cloth "
                            "(bed__sham0 -> bed__headset0__acq0). A set that "
                            "does carry a turned band resolves through "
                            "ACQUIRED_AS and is measured instead of this: the "
                            "declaration is asked only after that lookup "
                            "fails."),
    # p2r52 — the whole-bed winner's construction is duvet-over-fitted-mattress:
    # the file holds NO spread layer between mattress and duvet, and the blind
    # panel read that construction inside the delivered none-or-sliver band
    # (gate-DELIV001-P2r51). A future asset that does carry a spread resolves
    # through ACQUIRED_AS first, same safety as the duvet row above.
    "bed__coverlet": ("D-107", "the acquired whole bed f52472c1 has no spread: "
                               "its bedding is one duvet field over a "
                               "fitted-sheet mattress (id-coloured part census "
                               "2026-08-18, 12 meshes, none between mattress "
                               "top and duvet). The coverlet rung has no "
                               "object to rank and the panel accepted the "
                               "construction blind."),
}


def resolve_acquired(obj, measured, wears):
    """(object_name, why) for a ladder rung whose own object is absent, or
    (None, why). `wears` = {object: [material]} from the id-mask sidecar.

    Fails closed in three directions, because each of them has a different
    answer and reporting them as one is what let p2r38 through: no declaration,
    no sidecar, and an ambiguous match are all distinct from "not built"."""
    dec = ACQUIRED_AS.get(obj)
    if dec is None:
        return None, (f"{obj!r} is not declared as an acquirable rung, so a "
                      f"replacement for it cannot be recognised")
    prefix, material = dec
    if not wears:
        return None, (f"{obj!r} may have been replaced by an acquisition "
                      f"({prefix}*), but this mask sidecar carries no `wears` "
                      f"block — re-run id_mask.py; a rung that cannot tell a "
                      f"rename from a deletion must not guess")
    # `acq_<rung>` is what a RETINT leaves behind: the mesh keeps the uploader's
    # material object, so build_room renames it to the rung it was tinted from,
    # and Blender may suffix a duplicate (`acq_bench_seat.001`). A REPLACED
    # material is our own object and matches exactly. Both are the same claim —
    # "this mesh renders on that rung" — so both resolve.
    def _on_rung(ms):
        return any(m == material or m.startswith("acq_" + material)
                   for m in (ms or []))
    hits = sorted(o for o, ms in wears.items()
                  if o.startswith(prefix) and _on_rung(ms) and o in measured)
    if not hits:
        return None, (f"{obj!r} is absent and nothing named {prefix}* renders in "
                      f"{material!r} either")
    if len(hits) > 1:
        return None, (f"{obj!r} resolves to {len(hits)} acquired meshes "
                      f"({', '.join(hits)}) that all wear {material!r} — "
                      f"ambiguous; one rung cannot rank two objects")
    return hits[0], f"acquired: {hits[0]} wears {material}"


def check_render(measured, frame=FRAME, wears=None):
    """LOOK-time. `measured` = {object_name: median sRGB luma} from an object-id probe.

    Returns a list of human-readable violations — EMPTY means the ladder the design
    decided is the ladder the render actually shows. This is deliberately not a build
    gate: it needs pixels, and a gate that cannot run without a 2-minute Cycles render
    would either be skipped or would make the build lie about having checked.

    `frame` names the camera the measurement came from. On FRAME everything is scored.
    On any OTHER camera the per-rung targets are skipped — they were solved against this
    room's light on one view and mean nothing elsewhere — while ORDER and SPAN are still
    enforced, because "the bed must not read as one mass" is a claim about every frame
    that shows the bed. A probe that scored frame-specific targets everywhere would
    report defects that are not defects, and an instrument that cries wolf gets muted.
    """
    if frame not in KNOWN_FRAMES:
        _fail(f"value_ladder: unknown frame {frame!r}. A frame name that is not recognised "
              f"would silently switch every per-rung target OFF and still report CLEAN, so "
              f"it RAISES instead (known: {sorted(KNOWN_FRAMES)})")
    out = []
    seen = []
    acquired = set()          # rung objects resolved through ACQUIRED_AS
    on_frame = (frame == FRAME)
    if not on_frame:
        out.append(f"NOTE: frame {frame!r} is not {FRAME!r} — per-rung targets NOT scored "
                   f"(they were solved against {FRAME!r}'s light); ORDER and SPAN still are")
    for name, obj, target in LADDER:
        use, bought = obj, False
        if obj not in measured:
            # A RENAME BY ACQUISITION IS NOT A MISSING OBJECT. See ACQUIRED_AS.
            alt, why = resolve_acquired(obj, measured, wears)
            # ABSENT ON PURPOSE IS NOT ABSENT BY ACCIDENT — but this is asked
            # AFTER the acquisition lookup, never before, and the order is the
            # whole safety of the mechanism: if a later purchase DOES carry this
            # piece, it resolves and gets measured, and the declaration cannot
            # hide it. Declaring first would have turned a signed absence into a
            # blindfold the moment the shopping changed.
            if alt is None and obj in DECLARED_ABSENT:
                _dec, _why = DECLARED_ABSENT[obj]
                out.append(f"NOTE: {name} ({obj}) is ABSENT BY DECLARATION "
                           f"{_dec} — {_why} Not measured, and not a defect in "
                           f"this frame's tone.")
                continue
            if alt is None:
                # On FRAME this is a real finding: every rung is chosen because the hero
                # view shows it, so an absent one means occluded, renamed or not built.
                # On another camera it usually just means "not in this shot".
                out.append(f"{name}: object {obj!r} has no measurement — the probe did "
                           f"not see it ({why})"
                           if on_frame else
                           f"NOTE: {name} ({obj}) is not visible in {frame!r} — not scored")
                continue
            use, bought = alt, True
            acquired.add(use)
            out.append(f"NOTE: {name} ({obj}) is scored on {use} — {why}. Its point "
                       f"target {target:.1f} was solved on the BUILT object and is "
                       f"reported, not enforced; ORDER and SPAN still are")
        got = float(measured[use])
        seen.append((name, use, target, got))
        if on_frame and abs(got - target) > TOLERANCE:
            out.append(f"{'NOTE: ' if bought else ''}{name} ({use}): rendered {got:.1f}, "
                       f"target {target:.1f} (off by {got - target:+.1f}, tolerance "
                       f"+-{TOLERANCE})"
                       + (" — acquired rung, reported not enforced" if bought else ""))
    # ONE CHECK WAS CARRYING TWO CLAIMS (split p2r42). Sorting by TARGET and then
    # measuring adjacent RENDERED gaps fires for two different defects at once:
    # two pieces that read as one cloth (COLLAPSE), and a piece that has crossed
    # another in the designed order (INVERSION). Naming one of them "ORDER" and
    # reporting both through it is this repo's own "one parameter carrying two
    # things", and it mattered the moment acquisitions arrived: an INVERSION
    # against a target ordering is a claim about the object that was REPLACED —
    # the acquired ottoman renders below the throw only because the built bench
    # it stands in for sat in different light — while COLLAPSE is a claim about
    # the bed in front of us and survives any swap. So collapse is measured over
    # every rung by RENDERED value, and inversion only over the rungs whose own
    # object is actually in the frame.
    # COLLAPSE IS A CLAIM ABOUT THE PALETTE, so it compares rungs on DIFFERENT
    # tones (narrowed p2r42). MIN_STEP's own sentence is "they read as one piece
    # of cloth" — and `upholstery` drives the bed base, the foot throw AND the
    # foot bench, which D3-4 signs as ONE cloth on purpose. Demanding ten codes
    # between two objects cut from the same fabric asks the build to break the
    # design it is checking; the built bench cleared the throw by 41 codes
    # through LIGHT and position, and when p2r38 replaced it with a bought
    # ottoman that relationship went with it. Same-tone pairs still PRINT their
    # gap, because "the ottoman and the throw are nine codes apart" is worth
    # knowing — it is just a composition finding, not a palette one.
    #
    # THE TEST THAT MAKES THIS A CORRECTION AND NOT A LOOPHOLE, and it is the
    # only reason to accept it: the narrowed check still catches every defect
    # this instrument was built for. The founding one — six pieces inside 7.1
    # codes at the head — spans `duvet_set` and `pillowcase`, two tones. The one
    # the owner rejected by eye at p2r41 — duvet 208.3 against pillow 217.2 —
    # is also cross-tone. A narrowing that would have let either through would
    # be a loophole; this one fires on both.
    step_floor = MIN_STEP if on_frame else MIN_STEP_OFF
    by_value = sorted(seen, key=lambda r: r[3])
    for (an, ao, _at, ag), (bn, bo, _bt, bg) in zip(by_value, by_value[1:]):
        if bg - ag >= step_floor - 1e-9:
            continue
        if an == bn:
            out.append(f"NOTE: {ao} rendered {ag:.1f} and {bo} rendered {bg:.1f} "
                       f"— {bg - ag:+.1f} codes apart. They are the SAME cloth "
                       f"({an}), so this is a composition finding, not a palette "
                       f"one: no tone can separate them")
            continue
        out.append(f"COLLAPSE: {an} ({ao}) rendered {ag:.1f} and {bn} ({bo}) "
                   f"rendered {bg:.1f} — {bg - ag:+.1f} codes apart, under "
                   f"{'MIN_STEP' if on_frame else 'MIN_STEP_OFF'} {step_floor}. "
                   f"They read as one piece of cloth")
    built = sorted((r for r in seen if r[1] not in acquired), key=lambda r: r[2])
    for (an, ao, _at, ag), (bn, bo, _bt, bg) in zip(built, built[1:]):
        if bg < ag:
            out.append(f"ORDER: {an} ({ao}) is designed below {bn} ({bo}) and renders "
                       f"ABOVE it — {ag:.1f} against {bg:.1f}. The ladder the design "
                       f"decided is not the ladder the render shows")
    # SPAN IS ONLY MEANINGFUL OVER THE WHOLE LADDER. A first cut measured it across
    # "whatever rungs happened to be visible", so a camera that legitimately sees three of
    # the seven pieces would FAIL the span it had just been told was unscorable — the
    # instrument contradicting itself in the same report, which is how a check gets muted.
    # The rungs it is defined over are the ones that are missing in exactly that case, so
    # the honest answer is to say so rather than to score a smaller ladder.
    if len(seen) == len(LADDER):
        span = max(g for *_x, g in seen) - min(g for *_x, g in seen)
        if span < MIN_SPAN - 1e-9:
            out.append(f"SPAN: the bed renders across {span:.1f} codes, under MIN_SPAN "
                       f"{MIN_SPAN} — that is what 'reads pale' measures as")
    elif len(seen) >= 2:
        out.append(f"NOTE: SPAN not scored — {len(seen)} of {len(LADDER)} rungs visible in "
                   f"{frame!r}; the span is defined over the whole ladder")
    return out


def cloths_by_tone():
    """Every cloth, deepest first. Ordered by TONE and not by the ladder, because the
    ladder ranks OBJECTS: three of its rungs share one cloth and one cloth (the sheet) is
    deliberately unranked, so walking the ladder would both repeat a name and drop one.
    A first cut of the armour did exactly that — it said "5 cloths" and then listed 4."""
    return [n for n, _v in sorted(TONES.items(), key=lambda kv: kv[1])]


def story_line():
    """One sentence for the anti-repaint armour, DERIVED from the data above so it cannot
    describe a ladder the build does not have. No number is typed here."""
    ranked = sorted(LADDER, key=lambda r: r[2])
    span = ranked[-1][2] - ranked[0][2]
    # NAME NO FURNITURE. A first cut ended "the foot bench and the foot throw sitting BELOW
    # the coverlet" — but this sentence rides on any spec with a bed, and a bed without a
    # bench or a throw would have had the prose promise the polish pass two pieces the
    # build never made. That is the armour-describes-what-isn't-there shape, and the review
    # caught it here. The claim is now about the CLOTHS, which are this module's own data.
    # "AS SWATCHES", said out loud. The cloths are listed by AUTHORED depth, and the render
    # does not preserve that order: duvet_set is a deeper swatch than coverlet yet renders
    # 18-36 codes above it, because the duvet is lit and the coverlet is largely in its own
    # shade. Calling the swatch order "the frame's order" in a prompt sent to an image model
    # would instruct it to invert two of the biggest cloths in the picture.
    deepest, lightest = cloths_by_tone()[0], cloths_by_tone()[-1]
    return (f"bed tonal ladder: ONE greige linen in {len(TONES)} cloths — "
            f"{' -> '.join(cloths_by_tone())}, deepest to lightest AS SWATCHES (the frame's "
            f"own order differs, because light does that) — carrying "
            f"{len(ranked)} pieces the eye can rank across ~{span:.0f} sRGB codes of the "
            f"hero frame. The layers are told apart by VALUE, not only by height: do NOT "
            f"flatten them toward a single cream, do NOT lift the {deepest} toward the "
            f"bedding, and do NOT dull the {lightest} — whatever wears the deepest cloth "
            f"sitting BELOW the bedding behind it is what gives the frame its depth")


validate()
