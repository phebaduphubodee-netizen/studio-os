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
    "upholstery": 0.188,  # bed base + foot bench + foot throw + the vanity tub chair
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
    "coverlet":   0.545,  # the bed's main field, the solver-draped spread
    "sheet":      0.68,   # the mattress/sheet edge showing under the coverlet
    "duvet_set":  0.415,  # duvet + its turned-back fold + the two euro shams (one cloth)
    "pillowcase": 0.868,  # the sleeping pillows — the lightest thing in the room, by design,
    #                       and parked just under the 240 band ceiling rather than past it
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
    FRAME, "bed_hero", "curtains_semouth", "curtains_south", "ensuite_hooks_east",
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


def check_render(measured, frame=FRAME):
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
    on_frame = (frame == FRAME)
    if not on_frame:
        out.append(f"NOTE: frame {frame!r} is not {FRAME!r} — per-rung targets NOT scored "
                   f"(they were solved against {FRAME!r}'s light); ORDER and SPAN still are")
    for name, obj, target in LADDER:
        if obj not in measured:
            # On FRAME this is a real finding: every rung is chosen because the hero view
            # shows it, so an absent one means occluded, renamed or not built. On another
            # camera it usually just means "not in this shot", which is not a defect.
            out.append(f"{name}: object {obj!r} has no measurement — the probe did not "
                       f"see it (occluded, renamed, or not built)"
                       if on_frame else
                       f"NOTE: {name} ({obj}) is not visible in {frame!r} — not scored")
            continue
        got = float(measured[obj])
        seen.append((name, obj, target, got))
        if on_frame and abs(got - target) > TOLERANCE:
            out.append(f"{name} ({obj}): rendered {got:.1f}, target {target:.1f} "
                       f"(off by {got - target:+.1f}, tolerance +-{TOLERANCE})")
    ranked = sorted(seen, key=lambda r: r[2])
    step_floor = MIN_STEP if on_frame else MIN_STEP_OFF
    for (an, ao, _at, ag), (bn, bo, _bt, bg) in zip(ranked, ranked[1:]):
        if bg - ag < step_floor - 1e-9:
            out.append(f"ORDER: {an} ({ao}) rendered {ag:.1f} and {bn} ({bo}) rendered "
                       f"{bg:.1f} — {bg - ag:+.1f} codes apart, under "
                       f"{'MIN_STEP' if on_frame else 'MIN_STEP_OFF'} {step_floor}. "
                       f"They read as one piece of cloth")
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
