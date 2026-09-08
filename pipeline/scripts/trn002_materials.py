"""trn002_materials.py — TRN-002 phase 2: material identity for the reproduction.

Same two-layer split as trn001_materials (LAYER LAW): a PURE half — which
material each mass wears (`material_for`) and what that material IS (`PALETTE`)
— importable and testable under plain python, and a bpy half that turns the
table into Principled node graphs.

WHAT THIS MODULE INHERITS RATHER THAN RE-LEARNS (all from trn001_materials,
each earned by a failed round there — read that file before changing any of it):
  * MAP_MEAN / ROUGH_MEAN normalisation. A map already carries a mid tone, so
    multiplying it by an albedo lands at albedo x mean. Normalising by the map's
    own mean makes the MAP carry variation and the SAMPLED value carry identity.
    TRN-001 shipped four rounds with the roughness half of this missing and the
    hero object's polish never reached a frame.
  * TONE_NOISE. Board-to-board drift. TRN-001 measured its floor at 1.9%
    plank-to-plank variation against a reference's 30.4% — identical tone on
    every plank is what makes wood read as printed laminate.
  * NORMAL_STRENGTH is per-MATERIAL, never per-map-slug: a floor plank carries a
    1-2 mm V-groove at every joint and a cabinet panel is spliced flush. Keying
    it by slug is one parameter carrying two things.
  * The albedo METHOD: sample the target patch and divide by a reference surface
    read under the SAME illumination, so the light cancels. Never read a value
    off a lit pixel and call it an albedo. And where a value error belongs to
    the LIGHT lane, correct HUE ONLY and leave luminance alone — otherwise the
    light's error is baked into the material table permanently.

WHAT IS DIFFERENT HERE: TRN-002's palette is dominated by an OAK veneer run
(console/desk/etagere/band/nightstand), lacquered greige wardrobe fronts, white
paint, and a herringbone floor — and every mass in the frame is measured
geometry, so a material can be assigned by NAME with no guessing about which
surface is which.

AND ONE CORRECTION WORTH MORE THAN ITS ROW: that run was called TRAVERTINE from
r6 to r12 on the strength of an 8x crop, and it is oak. A crop shows texture;
texture does not identify a material, because rift oak and vein-cut travertine
carry the same tight parallel lines. What identifies it is what the material is
asked to DO — the console wraps those fibre lines continuously around a
half-round end, and stone does not bend. The measurement that catches it is
ANISOTROPY, never hue: on the target these surfaces vary 6x more along the grain
than across it, and our marble-mapped frame came back isotropic while its
corrected B/R sat within 0.1 of the target's the whole time. A hue check was
never going to find this, and we ran one.

PALETTE VALUES ARE FILLED FROM THE PHASE-2 MEASUREMENT PASS. Any row still
carrying `prov="A"` in PALETTE_PROV is a declared assumption, not a measurement,
and must say so at every gate.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CC0 = os.path.join(REPO, "assets", "shared", "cc0", "textures")

# --------------------------------------------------------------- assignment --
# Mass name (or prefix) -> palette key. PURE: no bpy, no image, no I/O.
# Exact names win over prefixes; a mass with no rule raises rather than falling
# back to a default, because a silent default is a decision nobody made
# (the class this repo names "a default nobody set = a decision nobody made").
EXACT = {
    # The floor slab is now the JOINT plane: the planks ride 2 mm proud of it,
    # so what shows between them is this. The target's joints measure 1.83x
    # darker than the field, which is the number this row carries.
    "floor": "floor_joint",
    "floor_planks": "floor_herringbone",
    "back_wall": "paint_white", "left_wall": "paint_white",
    # r30 split `back_wall` into the three pieces that stop at the partition
    # frame, because the single slab was standing IN the opening — 53.4% of the
    # partition zone by id mask, which thirty rounds of critics read as frosted
    # glass. Same paint; the reference-surface measurement (n=65,014 px) lives
    # in back_wall_R, since that is where those pixels are.
    "back_wall_L": "paint_white", "back_wall_R": "paint_white",
    "back_wall_head": "paint_white",
    "right_wall": "paint_white", "door_wall": "paint_white",
    "ceil_main": "paint_ceiling",
    "ward_bulkhead": "lacquer_wardrobe", "ward_body": "lacquer_wardrobe",
    "ward_groove": "reveal_shadow",
    "door_leaf": "lacquer_white",
    # The artwork mass IS the frame. Its own `seen` line measured a 21 mm black
    # bar at luma 28-33 against a 175-187 wall — a 6:1 contrast, the strongest
    # edge on that wall — and the mass wore a 0.78-albedo white from r2 to r13,
    # so the target's most legible wall object rendered as a blank slab. MEASURED
    # AND NEVER BUILT: the pass that identifies an object by a feature is not the
    # pass that builds it, and nothing checked that the feature survived.
    "artwork": "frame_black",
    "art_mat": "art_relief",
    "door_handle": "frame_black",
    "door_rev_near": "reveal_shadow", "door_rev_far": "reveal_shadow",
    "door_rev_head": "reveal_shadow",
    "part_head": "frame_black", "part_jamb_L": "frame_black",
    "part_jamb_R": "frame_black", "part_stile_M": "frame_black",
    "part_rail_B": "frame_black", "part_rail_top": "frame_black",
    "closet_floor": "floor_herringbone", "closet_back": "paint_white",
    # the wardrobe niche behind the partition — same oak as the whole left run.
    # Grain VERTICAL, which is what a tall lining panel shows and what the
    # target's own niche shows at 4x.
    "closet_oak": "veneer_oak",
    # r34 splits that one panel into the unit it actually is, on the plane the
    # floor contact puts it (y=1130, not the declared 2330). Listed one by one
    # rather than as a `closet_` PREFIX on purpose: `closet_floor` and
    # `closet_back` are NOT oak, so a prefix here would be a rule that has to
    # carry two exceptions on the day it is written. `material_for` raises on an
    # unmapped mass, so the next closet part fails loudly instead of defaulting.
    "closet_body": "veneer_oak", "closet_head": "veneer_oak",
    "closet_stile_R": "veneer_oak", "closet_niche_back": "veneer_oak",
    "closet_shelf": "veneer_oak", "closet_plinth": "veneer_oak",
    "led_strip": "strip_led",
    "desk": "veneer_oak", "console": "veneer_oak",
    # `desk_pier` STAYS although r37 deleted the mass, and the reason is worth reading
    # before tidying it: `test_every_mass_in_the_spec_has_a_material` walks EVERY spec in
    # the lane, not the newest, because re-rendering a past round is how this lane catches
    # regressions. Thirty-six specs still carry the mass, so dropping this rule breaks
    # r1..r36 rather than cleaning up r37. It was removed at r37 and the suite refuted it
    # in one run. The guard against a deleted object walking back in is `declared_gaps` +
    # the coverage manifest, which is a check about the SPEC — not this table.
    "desk_pier": "veneer_oak",
    "shelf_col_base": "veneer_oak", "shelf_col_back": "veneer_oak",
    "tv": "screen_black",
    "blind": "blind_slat",
    "rug": "rug_cream",
    "bed_platform": "upholstery_bed", "bed_headboard": "upholstery_bed",
    "bed_mattress": "linen_white",
    "duvet": "linen_white",
    "duvet_top": "linen_white", "duvet_drape": "linen_white",
    "pillow_L": "linen_white", "pillow_R": "linen_white", "bolster": "linen_white",
    "cushion_taupe": "fabric_taupe",
    "throw_velvet": "velvet_taupe", "throw_woven": "woven_oat",
    # It IS oak, and the r6 pass that renamed it travertine was wrong — see the
    # PALETTE row. Grain runs VERTICALLY here (fine dense staves, top to bottom).
    "ward_band": "veneer_oak",
    # ...and HORIZONTALLY on the nightstand: at 8x the drawer front carries
    # continuous long-grain lines running the full width, with a soft cathedral
    # figure. Grain direction is a per-OBJECT fact, not a per-material one, so it
    # gets its own key rather than a knob on the shared one.
    "nightstand": "veneer_oak_h",
    "bench": "upholstery_bed",
    "petcave": "upholstery_bed",
    # THE CAVITY WORE THE CAVE'S OWN MATERIAL FIRST, and that was a test, not
    # a default: if a 0.86-albedo lining 300 mm wide and 450 mm deep had
    # rendered anywhere near the target's 0.0003, the black would have been
    # OCCLUSION and geometry the whole answer. IT RENDERED 0.1884, with 0.0% of
    # the mouth below Ylin 0.02 against the target's 85.1% — the cavity fills by
    # interreflection like an integrating sphere. So the lining is DARK, and
    # this row is derived from a number instead of chosen.
    # THE FIRST RUN OF THIS TEST WAS VOID AND IS NOT WHAT IS QUOTED: it was
    # measured while the cavity was still 2 mm proud of a solid face, where the
    # lining was barely hit and a 40x albedo change moved the region 1%. A
    # conclusion refuted OR confirmed by a broken instrument is not a
    # conclusion, so it was re-run on the corrected opening before this row was
    # believed. See PALETTE cave_liner.
    "petcave_mouth": "cave_liner",
    # ONE lamp. The two-mass version invented a post to hold a measured shade
    # up, and the owner spotted it in the first frame that had light on it.
    # The two old names are KEPT so every historical spec still builds — a
    # rename that silently breaks a past round destroys the ability to
    # reproduce it, and reproducing past rounds is how regressions are found.
    # r35: `lamp` was a fabricated 640.7 mm body standing where the reference
    # shows lit oak wall. Deleted, not renamed — the shade it claimed to carry
    # is now measured on its own (`pendant_shade`), and the post that carried
    # nothing is simply gone. `lamp`/`lamp_shade`/`lamp_stem` stay listed so a
    # spec that still names them keeps rendering black rather than defaulting.
    "lamp": "shade_black",
    "pendant_shade": "shade_black",
    "pendant_cord": "shade_black",
    "lamp_shade": "shade_black", "lamp_stem": "shade_black",
    "duvet_top": "linen_white", "duvet_drape": "linen_white",
    "shelf_col_base": "veneer_oak",
    "chair_seat": "upholstery_chair", "chair_back": "upholstery_chair",
}
PREFIX = (
    ("rev_", "reveal_shadow"),
    ("dl_", "lens_warm"),
    # every etagere part, under any of the names it has carried across eleven
    # specs (shelf_col, shelf_col_mid/top/cap/board3..., shelf_board2...)
    ("shelf_", "veneer_oak"),
    # historical names from earlier rounds, kept so every past spec still
    # renders — reproducing an old round is how a regression is caught
    ("ceil_", "paint_ceiling"),
    ("slot_fascia", "paint_white"),
    # the alcove wall, split into near/far/head around its opening
    ("door_wall", "paint_white"),
    ("door_jamb", "reveal_shadow"),
    # the partition's members are PAIRS in the target: a fixed jamb/mullion and
    # the sliding leaf's own stile beside it. All the same powder-coated metal.
    ("leaf_stile", "frame_black"),
    ("mullion", "frame_black"),
    ("chair_leg", "leg_dark"),
)
# Retired names, mapped once so the eleven specs in this lane all build.
EXACT.update({
    "wardrobe": "lacquer_wardrobe",
    "fin_wall": "paint_white",
    "chair": "upholstery_chair",
    "desk_panel": "veneer_oak",
})


def material_for(name):
    """Palette key for a mass. Raises on an unmapped mass — see module docstring."""
    if name in EXACT:
        return EXACT[name]
    for pre, key in PREFIX:
        if name.startswith(pre):
            return key
    raise KeyError(f"no material rule for mass '{name}' — assign one, never default")


# ------------------------------------------------------------------ palette --
# key -> (linear albedo RGB, roughness, metallic, map-set slug or None, map scale m)
# Every row's basis is in PALETTE_PROV below. Values measured relative to the
# white wall taken at 0.80 albedo (the trn001 method), which assumes the two
# surfaces see comparable illumination — TRUE for vertical surfaces at similar
# height, FALSE for the floor under ceiling fixtures (trn001 paid for that once:
# a sampled 0.72 floor albedo became a second ceiling and flattened the frame).
_M = "M(phase-2 pass, ratio to the back wall taken at 0.80 albedo)"
_A = "A(assumed — not measured from the target)"

# MAPPED ONLY WHERE THE TARGET SHOWS TEXTURE, and the measurement decides which.
# trn001's rule is "every material that has a real map set gets one", written
# after a study found this studio at 95% image-free against 50-66% in pro files.
# Applied blind here it was WRONG: the phase-2 pass measured each surface's own
# texture index, and the walls/ceiling come in at 0.03 — flat — against the
# floor's 0.29 and the travertine's 0.49. Carrying plastered_wall_03 on the
# paint turned smooth walls into raw stucco in the first frame. The rule is
# real; what it needs is the per-surface number, not the studio average.
PALETTE = {
    "paint_white":       ((0.799, 0.799, 0.799), 0.75, 0.0, None, 0.0),
    "paint_ceiling":     ((0.680, 0.638, 0.597), 0.80, 0.0, None, 0.0),
    "lacquer_wardrobe":  ((0.665, 0.651, 0.617), 0.52, 0.0, None, 0.0),
    "lacquer_white":     ((0.760, 0.755, 0.740), 0.45, 0.0, None, 0.0),
    # ONE oak for the whole left run AND the headboard band. The four objects
    # sample 0.26x-1.05x of the wall, a 4x range — and that range is LIGHTING,
    # proven on a single continuous etagere panel where one spot under the LED
    # strip reads 2.24x another 0.6 m away on the SAME surface, same material,
    # same orientation. Giving each object its own albedo would bake the light's
    # job into the material table, the exact error trn001 recorded when it
    # corrected a floor's VALUE instead of its hue. The ALBEDO below is
    # unchanged by the identity correction — it is a measurement of those
    # pixels, and the pixels did not move.
    #
    # THE IDENTITY WAS WRONG FROM r6 TO r12 and the correction is the console.
    # r6 examined the band at 8x, found "fine vertical fibrous striations and
    # irregular linear porosity", and wrote vein-cut travertine — a reading a
    # crop genuinely supports, because rift oak and vein-cut travertine both
    # give tight parallel lines. What the crop could not answer, and nobody
    # asked, is whether the material WRAPS A RADIUS: at 4x the console and the
    # desk pier carry those same fibre lines continuously around a full
    # half-round end, and stone does not bend. The nightstand settles it a second
    # way, with long-grain cathedral figure running the width of the drawer.
    # The lesson is the one this lane keeps paying for: a texture crop answers
    # "what does this surface look like", and identity needs "what could have
    # been MADE this way" — different questions, and only the second one has an
    # answer a measurement can refute.
    # MAP SCALE 1.10 -> 3.2 m (r22). At 1.10 the wood_floor map laid a plank
    # joint every ~120 mm across a veneer panel and repeated its whole tile 2.6
    # times up the column, so the etagere came back with plank joints a veneer
    # does not have and visible horizontal tile seams — which is what the owner
    # meant by "ลายไม้ยังไม่สวย" and what C2 filed as texture tiling. THE MAP IS A
    # FLOOR: it carries board joints, and cabinetwork does not. At 3.2 m one of
    # the map's boards spans a whole panel, so the grain runs unbroken top to
    # bottom and the tile no longer repeats within the object — one leaf per
    # panel, which is exactly what the reference shows. Bracketed 1.10 / 2.2 /
    # 3.2 on the quick rung and judged by eye: 2.2 still showed seams at a third
    # and two thirds of the column's height.
    "veneer_oak":        ((0.578, 0.485, 0.361), 0.60, 0.0, "wood_floor", 3.2),
    # Same oak, grain turned 90 deg. Split by OBJECT because grain direction is
    # a fact about the panel, not about the species.
    "veneer_oak_h":      ((0.578, 0.485, 0.361), 0.60, 0.0, "wood_floor", 3.2),
    # RETIRED NAME, kept so the twelve specs in this lane all still build and any
    # past round can be re-rendered — reproducing an old round is how a
    # regression is caught. Points at the same values as veneer_oak.
    "veneer_travertine": ((0.578, 0.485, 0.361), 0.60, 0.0, "wood_floor", 3.2),
    # HUE CORRECTED r22 against the target's own floor, illuminant-cancelled
    # through the wall in BOTH frames: corrected G/R 0.634 target vs 0.722 ours,
    # B/R 0.357 vs 0.513. Ours was ashy where the target is honey — G x0.877,
    # B x0.695. The previous row's warmth was measured through the joint plane,
    # not the plank field, so it carried the joint's own lift.
    "floor_herringbone": ((0.503, 0.275, 0.117), 0.42, 0.0, "wood_floor", 0.66),
    "floor_joint":       ((0.275, 0.150, 0.064), 0.55, 0.0, None, 0.0),
    # The 2026-07-30 ground-truth study measured this studio at 95% image-free
    # materials against 50-66% in every photoreal reference file, with fabric
    # compensating by flat sheen. Every fabric here therefore carries a real
    # map, and the maps are what supply weave — not a roughness number.
    # Fabrics keep their maps for WEAVE (normal), but the rug's diffuse is
    # dropped: wool_boucle's colour variation rendered as a plaid on a rug the
    # target measures as plain. The bed platform's side face measures texture
    # 0.05 — "extraordinarily uniform", plausibly a matte leatherette rather
    # than a weave — so it loses its diffuse map too.
    "rug_cream":         ((0.828, 0.837, 0.823), 0.92, 0.0, "wool_boucle", 0.45),
    # the taupe lumbar cushion. Lit-face swatch (720,525)=(161,145,129) sRGB ->
    # lin (0.357,0.285,0.222); over the wall reference at 0.80 that is albedo
    # (0.64,0.59,0.52) - a warm pale taupe, darker in B the way linen mixes are.
    "fabric_taupe":      ((0.638, 0.588, 0.519), 0.92, 0.0, "rough_linen", 0.5),
    # The two throws — the ONLY non-neutral things on the target's bed, and the
    # trained fingerprint says that is exactly what our frame lacks: coloured
    # share 0.128 against the target's 0.320, while the chroma of the colour we
    # DO have already matches (16.30 vs 16.02). Not more saturation; more AREA.
    # Velvet swatch (520,640)=(173,155,135) sRGB, tail (540,700)=(147,129,110);
    # woven top (610,640)=(187,170,151), tail (620,740)=(173,152,131).
    # RELIEF TURNED ON r33. Both this row and `upholstery_bed` below carried a
    # NORMAL_STRENGTH that no code path could reach — `build_materials` returns
    # early for a row with no map, so the relief was written and never built.
    # Same class as the dead PALETTE rows r30 deleted, in a different table.
    # Measured before turning it on (`texture_check.py`, σ=2, r32 frame): the
    # throw reads 0.0162 against the target's 0.0749, and the four bed-upholstery
    # objects 0.0073-0.0165 against 0.0291-0.0581. The map is `rough_linen`
    # and it is DIFFUSE_OFF — normal only — so r32's freshly re-derived albedos
    # are not moved by a texture round. Scale 0.30 for velvet (a finer pile than
    # the woven bed cloth at 0.50), the same band the other linen rows use.
    "velvet_taupe":      ((0.560, 0.470, 0.375), 0.42, 0.0, "rough_linen", 0.30),
    "woven_oat":         ((0.640, 0.548, 0.443), 0.88, 0.0,
                          "poly_wool_herringbone", 0.30),
    "upholstery_bed":    ((0.855, 0.871, 0.863), 0.90, 0.0, "rough_linen", 0.50),
    "linen_white":       ((0.860, 0.855, 0.840), 0.95, 0.0, "rough_linen", 0.7),
    "upholstery_chair":  ((0.791, 0.768, 0.708), 0.90, 0.0, "rough_linen", 0.5),
    "frame_black":       ((0.117, 0.095, 0.078), 0.45, 0.0, None, 0.0),
    # ROUGHNESS 0.12 -> 0.90, and the albedo is UNTOUCHED because it was never
    # the lever: at 86.3 degrees off this panel's normal, Fresnel returns 0.69
    # whatever the base colour is. Bracketed at quick price on the ONE metric
    # that decides it, our p50 over the TV's own 8,989 px against the target's
    # 0.0409:  r=0.12 (r28) 0.2756 = 6.75x | specular level 0.15 -> 0.2512 =
    # 6.15x, the knob that cannot reach | IOR 1.0 -> 0.0129 = 0.32x, a physical
    # lie that overshoots | r=0.45 -> 0.1221 = 2.99x | **r=0.90 -> 0.0409 =
    # 1.00x**. It also moves the character the right way: the target's TV runs
    # p99/p50 = 11.4, ours was 2.3 at r=0.12 and is 7.2 here.
    "screen_black":      ((0.051, 0.040, 0.028), 0.90, 0.0, None, 0.0),
    "shade_black":       ((0.045, 0.040, 0.035), 0.55, 0.0, None, 0.0),
    # THE PET CAVE'S LINING — measured by INVERSION, not by sampling, because
    # the pixels it has to match read 0.0000 and a saturated pixel carries no
    # value. What was sampled is OUR OWN cavity: built at the cave's 0.863
    # upholstery, through a REAL opening, it rendered 0.1884 with 0.0% of the
    # mouth below Ylin 0.02 against the target's 85.1% — so occlusion is NOT
    # the mechanism, and the round measured that rather than assuming it.
    # 0.020 is the darkest a real textile goes (soot sits near 0.02); anything
    # lower would be typed to hit a number. See PALETTE_PROV for what the
    # residual then belongs to.
    "cave_liner":        ((0.020, 0.019, 0.018), 0.95, 0.0, None, 0.0),
    "art_relief":        ((0.780, 0.770, 0.750), 0.80, 0.0, None, 0.0),
    "reveal_shadow":     ((0.300, 0.290, 0.275), 0.85, 0.0, None, 0.0),
    "lens_warm":         ((1.000, 0.955, 0.900), 0.50, 0.0, None, 0.0),
    # the chair legs: near-black tapered timber in the reference, the darkest
    # furniture element in the frame after the TV.
    "leg_dark":          ((0.055, 0.048, 0.042), 0.40, 0.0, None, 0.0),
    # the venetian slats. Their room-facing side is what the camera sees and
    # it is lit by the aperture, so this is a plain matte white — the bright
    # bar / dark gap reading has to come from the GEOMETRY, not from a value.
    "blind_slat":        ((0.780, 0.775, 0.760), 0.62, 0.0, None, 0.0),
    # THE ROW r30 DELETED, RE-DECLARED IN THE ROUND THAT BUILDS THE OBJECT.
    # r30 was right to delete it: `strip_led` sat in EMISSIVE naming a material
    # that had never existed here, so no code path could reach it. What it could
    # not do was build the strip, and the manifest has carried `led_strip` as
    # UNCOVERED ever since. The order matters and is the whole lesson: the mass
    # exists first (spec_r34 `led_strip`, a line fitted to rms 0.124 px over 65
    # columns), and the material is declared for it, not ahead of it.
    "strip_led":         ((1.000, 0.905, 0.790), 0.50, 0.0, None, 0.0),
}

PALETTE_PROV = {
    "paint_white": _M + "; the declared REFERENCE surface (back wall -y face, "
                        "n=65,014 px). Its own illumination spread p05..p95 is "
                        "1.36x, which is the floor on every ratio below.",
    "paint_ceiling": _M + "; 0.811x wall, n=88,286. Warmer than the wall "
                          "(chroma 0.853/0.801/0.748) and NOT uniform: near "
                          "third 0.926x vs far third 0.723x = 1.28x within one "
                          "plane, which the LIGHT must produce, not this row.",
    "lacquer_wardrobe": _M + "; 0.816x wall, n=111,816, IQR very tight. "
                             "Illuminant-corrected B/R 0.926 = a slightly warm "
                             "off-white greige, ~7% warmer than the wall paint.",
    "lacquer_white": _A + " — the entry door leaf is never cleanly sampled "
                          "(it sits in the slot's shadow); taken as the wall "
                          "paint slightly warmed and smoother.",
    "veneer_oak": _M + "; ONE material for console/desk/pier/etagere/band, and "
                       "veneer_oak_h is the same row with the grain turned. "
                       "Value from the etagere panel (the middle of the run's "
                       "4x lighting spread). IDENTITY corrected at r13 from "
                       "travertine back to oak — the console wraps its fibre "
                       "lines around a half-round end and stone does not bend; "
                       "the nightstand shows long-grain cathedral figure across "
                       "the drawer width. Measured against our own r12 frame, "
                       "the tell is ANISOTROPY, not hue: on the target's "
                       "nightstand the along-grain/across-grain variation ratio "
                       "is 6.3:1 (row 0.169 / col 0.027) and on the band 5.8:1, "
                       "while our marble-mapped r12 returned 2.1:1 and 0.42:1 — "
                       "isotropic blotch where the target has direction. "
                       "Corrected B/R agreed all along (0.59-0.69 target vs "
                       "0.66-0.77 ours), which is exactly why a hue check never "
                       "caught it.",
    "veneer_oak_h": "see veneer_oak — same measured row, grain rotated 90 deg "
                    "for panels whose long axis is horizontal.",
    "veneer_travertine": "RETIRED NAME (r6-r12). Kept pointing at veneer_oak's "
                         "values so every past spec still renders.",
    "floor_herringbone": _M + "; 0.436x wall, n=30,694, the warmest and most "
                              "saturated surface in the room (corrected B/R "
                              "0.327). Map scale 0.66 m = the measured 132 mm "
                              "plank width x the map's ~5-plank tile.",
    "floor_joint": _M + "; the plank field divided by the measured joint "
                        "contrast (joints read 1.83x darker than the field — "
                        "the same signal the herringbone phase was fitted on).",
    "fabric_taupe": _M + "; cushion lit face (720,525)=(161,145,129) sRGB over "
                          "the wall-at-0.80 method; piping (770,550)=(62,55,47) "
                          "is geometry the oct does not carry - declared.",
    "velvet_taupe": _M + "; the runner's lit face over the wall-at-0.80 method. "
                         "Roughness 0.42 because velvet is the one sheened "
                         "fabric in the frame - its tail reads 0.85x its top "
                         "where a matte weave reads ~0.95x.",
    "woven_oat": _M + "; the coarse throw's lit face; it keeps a REAL "
                      "herringbone map because its weave is the one fabric "
                      "texture the target resolves at this camera.",
    "rug_cream": _M + "; sampled in BOTH conditions (lit front 1.154x wall, "
                      "shadowed band 0.938x = 1.23x apart) and the row carries "
                      "their midpoint — the spread is the light's to produce. "
                      "Corrected B/R 1.025 = essentially neutral.",
    "upholstery_bed": _M + "; the side face reads 1.512x wall and CLIPS when "
                           "converted (albedo 1.16-1.22), so the row is capped "
                           "at the foot face's honest 1.091x-derived value. A "
                           "measurement that returns an impossible albedo is "
                           "reporting the light, not the surface.",
    "linen_white": _M + "; four bedding samples spanning 1.35x (sheet at foot "
                        "1.292x wall to shaded duvet 0.954x); neutral warm-"
                        "white, same hue as the wall at higher value.",
    "upholstery_chair": _A + " — the chair is small and half-occluded; taken "
                             "as the headboard fabric (0.966x wall) which is "
                             "the nearest measured fabric in the frame.",
    "frame_black": _M + "; BRACKETED not single-valued: full strips read "
                        "0.150-0.191x wall, darkest-30% cores 0.113-0.125x. "
                        "Row uses the core. Corrected B/R 0.675 = a warm dark "
                        "grey-brown, NOT neutral black. Roughness matte: the "
                        "apparent specular tail (p99/med 4.6-6.9) collapses to "
                        "1.1-1.4 once JPEG ringing off the glass is excluded.",
    "screen_black": _M + " (upper bound); dark core 0.053x wall -> albedo ~0.04."
                         " The TV is the ONLY specular class in the frame "
                         "(p99/med 11.97, two broad soft bands). ROUGHNESS "
                         "CORRECTED r29, 0.12 -> 0.90, and the old reasoning is "
                         "left standing because its ERROR is the useful part: "
                         "it read high specular CONTRAST off the target and "
                         "inferred a POLISHED screen. At 86.3 degrees the "
                         "contrast comes from the environment being reflected, "
                         "not from the lobe being tight — a mirror at grazing "
                         "shows a bright wall as a bright panel, and that is "
                         "what ours did for 29 rounds at 6.75x the target. "
                         "Bracketed on the quick rung: r=0.45 -> 2.99x, "
                         "r=0.90 -> 1.00x, and p99/p50 moved 2.3 -> 7.2 against "
                         "the target's 11.4. Same mechanism as FRESNEL's note: "
                         "a value method with a diffuse model inside it cannot "
                         "measure a grazing specular surface.",
    "shade_black": _M + "; the lamp shade sits at Ylin 0.008-0.020 with no rim "
                        "and no pool — it is a dark cone, and the lamp is OFF.",
    "cave_liner": "M-by-inversion(upper bound) — the target's mouth reads Ylin "
                  "0.0000 over thousands of px and a saturated pixel has no "
                  "value in it, so nothing here was sampled FROM the target. "
                  "What was measured is our own: the same cavity built at the "
                  "cave's own 0.863 upholstery rendered 0.1884 with 0.0% of "
                  "the mouth below Ylin 0.02 against the target's 85.1%, which "
                  "settles the question the geometry was built to ask — a 300 mm mouth "
                  "on a 450 mm cavity does NOT go dark by occlusion, it fills "
                  "by interreflection like an integrating sphere. 0.020 is the "
                  "darkest a real textile reaches. THE RESIDUAL IS DECLARED, "
                  "NOT TUNED AWAY: if 0.020 still lands above the target, the "
                  "MEASURED SPLIT (both legs re-run on the corrected "
                  "opening, because the first pair was taken while the cavity "
                  "was still a 2 mm groove and said nothing about linings): "
                  "the OPENING is worth 1.8x, 0.344 -> 0.1884 at the same white "
                  "lining, and the LINING is worth 38x. The material dominates, "
                  "which is the opposite of what the round set out to show. "
                  "gap belongs to DEPTH — which this camera cannot see and the "
                  "spec declares — or to the target's mouth not being a lit "
                  "surface at all. Driving the albedo below a real material to "
                  "close it would be typing a number to hit a pixel.",
    "art_relief": _A + " — the mount board reads near the wall value; the "
                       "artwork's relief is geometry the spec does not yet "
                       "carry (frame 20.9 mm, relief block ~450x650 in a "
                       "705x978 mat) and is a styling-round ticket.",
    "reveal_shadow": _M + " (upper bound); the wardrobe grooves read 0.710x "
                          "wall but are truly darker — they are UNRESOLVED at "
                          "this camera (equivalent width 1.05 mm, sigma does "
                          "not grow with scale), so they must be matched "
                          "photometrically, never tuned by eye.",
    "leg_dark": _A + " — read off the target's chair legs as a near-black stained timber; not sampled cleanly (they are 4-6 px wide), so the value is bracketed by the partition frame core (0.11) above and the TV core (0.05) below.",
    "blind_slat": _A + " — the slats are ~6.5 px apart at this camera, far too fine to sample a value from; taken as the wall paint slightly warmed. What IS measured is their pitch (29.4 mm) and that the gaps are narrow.",
    "lens_warm": _M + "; the four lens cores are the frame's only legitimately "
                      "clipped pixels (273 px, 0.03%).",
    "strip_led": _A + " (COLOUR) — carried verbatim from trn002_light.STRIP's "
                      "measured warm white (1.000/0.905/0.790), the etagere "
                      "strips in this same room. The target's own strip pixels "
                      "read RGB 0.98/0.95/0.90, which is NOT usable as a hue: "
                      "at Ylin 0.94-0.96 a JPEG is compressing what little "
                      "chroma survives, and every near-clipped source in any "
                      "frame reads near-white whatever its colour. What IS "
                      "measurable is the WASH one pixel below the line — "
                      "0.82/0.71/0.56 at v 330 — and that is oak reflectance "
                      "times the strip, so it constrains the pair, not the "
                      "row. The line's LEVEL (0.94-0.96, not clipping) is the "
                      "bracket target; see EMISSIVE for the seed's derivation.",
}

# ------------------------------------------------------------- bpy builders --
# Linear MEAN of each map set's diffuse, measured once outside Blender. The
# first four are trn001's constants (its canon); the fabrics were measured for
# this lane and the method cross-checks — recomputing trn001's three at 512px
# returns 0.4429/0.2168/0.2482 against its 0.4493/0.2189/0.2495.
MAP_MEAN = {
    "wood_floor": (0.2189, 0.1185, 0.0557),
    "plastered_wall_03": (0.2495, 0.2061, 0.1679),
    "marble_01": (0.4493, 0.3397, 0.1936),
    "grey_cartago_03": (0.2664, 0.2489, 0.2317),
    "rough_linen": (0.2842, 0.4077, 0.6136),
    "wool_boucle": (0.2415, 0.2034, 0.1634),
    "poly_wool_herringbone": (0.1925, 0.1801, 0.1654),
}
ROUGH_MEAN = {
    "wood_floor": 0.471, "plastered_wall_03": 0.911, "marble_01": 0.506,
    "wool_boucle": 0.657, "poly_wool_herringbone": 0.861,
    # rough_linen ships no roughness map in this pack — only AO. Left out
    # deliberately: keying it to the AO mean would be a different quantity
    # wearing the right variable's name.
}
# Materials that keep a map set for its NORMAL (weave, grain relief) but must
# NOT take its colour variation — measured texture near zero on that surface.
DIFFUSE_OFF = {"rug_cream", "upholstery_bed", "velvet_taupe"}
# Materials whose mesh carries REAL UVs and must use them instead of box
# projection. Only the herringbone floor: its planks each carry their own UV
# frame so the grain turns with the chevron, which is what a box projection —
# one orientation for the whole floor — structurally cannot do.
UV_MAPPED = {"floor_herringbone"}
# Emission strength per material. The four downlight lenses are the frame's
# only legitimately clipped pixels (273 px, 0.03%), so the LENS is supposed to
# blow — what must not appear is a ceiling pool, and the measurement killed
# that twice (glow back to background within 120-200 mm; the floor directly
# under a fixture is DARKER than a metre away). Making the lens an emissive
# SURFACE rather than a bright point is what separates the two: a surface that
# small blows its own pixels and lights almost nothing.
# `strip_led: 26.0` was DELETED here at r30, not documented. It named a
# material that has never existed in PALETTE, and build_materials iterates
# PALETTE — so the entry could not have been reached by any code path in any
# round. The etagere strips are AREA lights (trn002_light.STRIP), which is the
# approach that actually shipped; this was the abandoned other one, left behind
# looking like a setting. A dead declaration is worse than no declaration:
# it reads as a decision that was made.
EMISSIVE = {"lens_warm": 34.0, "strip_led": 23.0}
# strip_led 23.0 is DERIVED FROM THIS LANE'S OWN SHIPPED STRIP, not chosen. The
# etagere strips are AREA lights at 0.85 W over 452 x 26 mm, and that power was
# itself set against a measured falloff (0.73 at 20 mm -> 0.40 at 90 -> 0.28 at
# 250) rather than by eye. A Lambertian emitter of power P over area A has
# radiance P/(pi*A) = 0.85 / (pi * 0.011752) = 23.0, which is what an emissive
# SURFACE has to carry to be the same light. It is a SEED, and it is bracketed
# on the quick rung like every other emitter here, because a box emits from six
# faces where an area light emits from one -- the equivalence above is exact for
# radiance and not for total power.
# CROSS-CHECK from outside this repo, which is the point of paying for research:
# 23.0 over the strip's 500 x 26 mm front face is ~0.94 W radiant, ~280 lm at a
# warm-white 300 lm/W radiant, i.e. ~560 lm/m. Diode LED's VALENT cove tape runs
# 436-2050 lm/m and Lutron's Lumaris 820-1640 lm/m
# (docs/research/2026-08-08-upgrade-dr/ANSWER_gemini_q5-hero-light-practice.md:26,
# both [MEASURED] against manufacturer spec sheets). So the seed sits at the dim
# end of one range and below the other -- consistent, and the direction to
# bracket in is UP.
# WHY AN EMISSIVE MESH AND NOT A FOURTH AREA LIGHT: the etagere strips are
# CONCEALED and only their wash is in frame. This one IS in frame -- a 1-2 px
# line at Ylin 0.94-0.96, the brightest thing in that quarter of the target and
# it does not clip. An area light with camera_visible off cannot produce a line;
# a light that IS visible has to be a surface.

# ------------------------------------------------------------------ fresnel --
# {key: (ior, specular_ior_level)}. A SEPARATE table from PALETTE, and the
# reason it is separate is the whole finding: it answers a question an albedo
# row structurally cannot.
#
# MEASURED 2026-08-07. The TV renders at Ylin p50 0.281 against the target's
# 0.037 — 7.6x, on 8,989 px, the largest single wrong-value object in the frame
# — and NOT ONE PART of that value comes from its albedo. The camera sits
# 86.3 degrees off that panel's normal (computed from the solved camera and the
# mass's own +x face), and a dielectric at 86.3 degrees returns Fresnel
# R = 0.689 whatever its base colour is. `screen_black`'s 0.040 contributes
# about 0.02 of the 0.281; the rest is the room, mirrored.
#
# WHY EVERY INSTRUMENT IN THIS LANE MISSED IT: every value in PALETTE was
# measured by the trn001 ratio method — sample the patch, divide by a reference
# surface under the same illumination, so the light cancels. That method has a
# DIFFUSE model inside it. Pointed at a grazing specular surface it returns a
# number that is not an albedo and cannot be made into one, and the four rounds
# r23-r26 that bracketed this lane's WATTAGE could not have moved this pixel by
# construction: the panel is showing a reflection, and a reflection scales with
# the thing reflected, so brightening or dimming the room moves the TV and the
# wall together. Same family as this repo's recorded A KNOB THAT CANNOT REACH.
#
# WHAT THE BRACKET THEN DID TO THE SECOND HALF OF THAT PARAGRAPH (r29, quick
# rung, and it is left in because being wrong on the record is the point of
# writing a falsifiable claim). This block first said: "specular_ior_level
# scales what remains, and roughness is not the lever." BOTH HALVES WERE WRONG,
# and the same arithmetic kills them:
#
#   Blender's Principled takes a Schlick form, F = F0 + (1-F0)(1-cos0)^5. At
#   86.3 degrees (1-cos0)^5 = 0.716, so F = 0.716 + 0.283*F0 and F0 is worth 2%
#   of the answer. MEASURED: dropping the level to 0.15 moved the TV's p50 from
#   0.2756 to 0.2512 — 9%, against 21x for IOR 1.0. The level knob does not
#   reach, for the same structural reason the wattage bracket did not.
#
#   And roughness DOES reach, because the two claims are about different
#   quantities. Total reflectance at 86 degrees is pinned near 0.72 by geometry
#   and nothing changes it. But what lands in the frame is the RADIANCE from the
#   mirror direction, and a rough lobe replaces one bright wall with the average
#   of a whole hemisphere. "Reflectance" and "the pixel" are not the same
#   number, and the first version of this comment used one to rule out the other.
#
# So the honest control is ROUGHNESS at a physical IOR — an anti-glare screen is
# a rough dielectric, not a dielectric with an impossible IOR. IOR 1.0 stays in
# the table as the bracket's dark end, never as a shipped value: it is a
# physical lie that happens to land near the right number.
FRESNEL = {}


# Names kept alive ONLY so past specs still render — see the rows themselves.
# A retired name is a deliberate orphan; every other orphan is a defect.
RETIRED = {"veneer_travertine"}

# Rows the CURRENT spec does not wear. This is a RATCHET, not a permission
# slip: the pin below lets it shrink and never grow, and each entry has to say
# what the target shows that we are not building.
#
# WHY IT EXISTS. r30 went looking for orphan rows on a hunch and found the most
# expensive instance of this lane's own recorded class, MEASURED AND NEVER
# BUILT:
#   blind_slat  — the venetian blind. There is a mesh generator (G.slat_stack)
#     with a MEASURED docstring (pitch 29.4 mm, extent back-projected from the
#     target's own sliver), a builder path (_slats), a palette row, THREE tests
#     in test_trn002_geom, and an area light in trn002_light whose comment says
#     its job is "to light ITS OWN SLATS ... and until r25 there were no slats".
#     Across all thirty specs THERE HAS NEVER BEEN A `blind` MASS. Every part of
#     the machine exists except the one line that puts it in the room, and the
#     target shows the blind plainly on the left wall.
#   leg_dark    — the chair's black tapered legs, among the darkest elements in
#     the target's frame. chair_leg_1..4 existed in spec_r12 and were dropped by
#     r14. Nothing noticed for eighteen rounds, because nothing counted.
#
# The check is four lines and it would have caught both the day they happened.
# EMPTIED at r31: both were built. The blind became a mass (it had had a
# generator, a builder, a palette row, three tests and a light aimed at it for
# thirty specs), and the chair's measured legs and seat were restored from
# spec_r12 — where a sighted audit had put them, and from which r14 silently
# reverted. `leg_dark` sitting unworn for eighteen rounds was the ONLY trace
# left that the chair had ever been measured, which is the argument for this
# whole check: the orphan outlived every gate, every critic and every report.
ORPHAN_ROWS = set()


def unworn_rows(mass_names, palette=None):
    """PALETTE rows that no mass in `mass_names` wears, minus retired names.

    PURE. An unworn row is a decision that never reached a render — the same
    shape as a FRESNEL row naming no material, or `strip_led` sitting in
    EMISSIVE with no PALETTE row to attach to.
    """
    pal = palette if palette is not None else PALETTE
    worn = set()
    for n in mass_names:
        try:
            worn.add(material_for(n))
        except KeyError:
            pass
    return set(pal) - worn - RETIRED


def resolve_fresnel(palette, override=None):
    """FRESNEL merged with a spec override, or raise. PURE — the layer law.

    It lives out here rather than inside `build_materials` for a reason this
    session already paid for once: a pure check written inside a bpy-only
    function cannot be tested under plain python, and the bug it was guarding
    against then ships. A fresnel row naming a material that does not exist is
    exactly the silent no-op this table was created to end.
    """
    out = dict(FRESNEL)
    out.update(override or {})
    unknown = sorted(set(out) - set(palette))
    if unknown:
        raise KeyError(f"FRESNEL names no such material: {unknown} — "
                       f"a row that matches nothing is a setting nobody applied")
    for k, row in out.items():
        if len(row) != 2:
            raise ValueError(f"FRESNEL[{k}] must be (ior, specular_level), got {row!r}")
    return out


MAP_FILE = {          # slug -> (diffuse, roughness or None, normal or None)
    "wood_floor": ("wood_floor_Diffuse_2k.jpg", "wood_floor_Rough_2k.jpg",
                   "wood_floor_nor_gl_2k.jpg"),
    "plastered_wall_03": ("plastered_wall_03_Diffuse_2k.jpg",
                          "plastered_wall_03_Rough_2k.jpg",
                          "plastered_wall_03_nor_gl_2k.jpg"),
    "marble_01": ("marble_01_Diffuse_2k.jpg", "marble_01_Rough_2k.jpg",
                  "marble_01_nor_gl_2k.jpg"),
    "rough_linen": ("rough_linen_Diffuse_2k.jpg", None,
                    "rough_linen_nor_gl_2k.jpg"),
    "wool_boucle": ("wool_boucle_Diffuse_2k.jpg", "wool_boucle_Rough_2k.jpg",
                    "wool_boucle_nor_gl_2k.jpg"),
    "poly_wool_herringbone": ("poly_wool_herringbone_Diffuse_2k.jpg",
                              "poly_wool_herringbone_Rough_2k.jpg",
                              "poly_wool_herringbone_nor_gl_2k.jpg"),
}
# Grain direction, as a rotation of the OBJECT coordinates fed to the box
# projection. wood_floor lays its boards along the map's V axis, and a box
# projection takes a face's UV from the two axes that are NOT its normal — so on
# any wall panel, X-facing or Y-facing, V comes from world Z and the unrotated
# default already runs the grain up the panel. That is what the etagere column,
# the console and the band want, and what they show.
#
# TO TURN THE GRAIN, ROTATE ABOUT THE AXIS THE PANEL FACES. That is the whole
# rule, and the first version of this table got it wrong by keying the rotation
# to the MATERIAL: (0,90,0) turns a Y-facing drawer front and is a silent no-op
# on an X-facing one, because rotating about Y leaves an X-face's (Y,Z) pair
# untouched. The nightstand faces -X, the rotation did nothing, and the frame
# came back with vertical grain on a drawer that shows long grain across its
# width in the target. Same shape as this repo's recorded ONE PARAMETER CARRYING
# TWO THINGS: one Euler was standing for both "which way does the grain run" and
# "which way does the panel face". The KEY NAME now carries the facing, so a
# panel with a different one gets its own row instead of quietly not turning.
MAP_ROT = {
    "veneer_oak_h": (90.0, 0.0, 0.0),   # horizontal grain on an X-FACING panel
}
NORMAL_STRENGTH = {
    "floor_herringbone": 1.6,          # planks DO carry a joint micro-bevel
    "veneer_oak": 0.10,                # spliced flush and sanded — not a floor
    "veneer_oak_h": 0.10,
    "veneer_travertine": 0.10,
    "lacquer_wardrobe": 0.06,
    "paint_white": 0.12, "paint_ceiling": 0.12,
    "linen_white": 0.6, "upholstery_bed": 0.6, "rug_cream": 0.9,
    "woven_oat": 1.1, "velvet_taupe": 0.2,
    "upholstery_chair": 0.5,
}
# CRUMPLE — sub-mesh fold relief, carried by the MATERIAL rather than by the
# solver. A categorically different rung, reached only after the solver's own
# knob was shown not to reach: the target's white bedding measures a high-passed
# rms of 0.01133 on its fold field; our baked cloth returns 0.00168 at slack 2%
# and 0.00234 at 6%, and slack is the ONLY fold-amplitude knob the drape ladder
# has — which it then halves on every billow, by its own design, because slack
# and footprint are antagonistic. A knob that cannot reach its target value is
# not a tuning problem (this repo's own recorded class).
#
# So the finest crumple moves to where sub-mesh detail belongs. At this camera a
# 14 px fold period is ~50 mm of world, which a 42 mm cloth cell cannot resolve
# and a normal can. {material: (noise scale, bump strength, stretch)}
# R1 STOP FILED 2026-08-05 — this rung is REFUTED as the answer, and kept only
# as a hint. The bracket, all at quick price, on a strip that is white duvet in
# BOTH frames (see below — the first strip was not):
#   scale 7.0 str 2.0 d0.12 -> rms 0.00788 vs target 0.00983 (1.25x short) and
#                              fold PERIOD 15.6 px, the target's exactly.
#                              AND IT RENDERS AS TREE BARK.
#   scale 3.2 str 0.7 d0.05 -> reads as cloth again, and measures ~14x short.
# There is no setting between them that is both. WHY, structurally: a noise
# field is ISOTROPIC and organised cloth folds are not — real folds run in
# FAMILIES along the drape's tension lines, which is why the target's crumple
# reads as fabric at the same amplitude that makes ours read as bark. A knob
# whose two ends are "invisible" and "wrong material" is not under-tuned.
#
# THE MEASUREMENT THAT ENDORSED THE BARK IS DISQUALIFIED, by this lane's own
# rule about a metric that cannot separate two things: a 1-D high-passed rms
# rewards ANY high-frequency variation and cannot tell a soft fold from a
# crumpled foil. It said 1.25x while the eye said catastrophe, and the eye wins.
# (It had already lied once: the strip I first quoted, u430-700, overlaps the
# TARGET'S THROWS — so "6.7x too smooth" was comparing their woven herringbone
# against our bare duvet. The honest white-on-white gap was 12.8x.)
CRUMPLE = {
    # a hint only, verified BY EYE to read as cloth. It is not the fix.
    "linen_white": (3.2, 0.7, (1.0, 1.0, 1.0)),
}
TONE_NOISE = {
    "floor_herringbone": (0.30, 2.2, (0.35, 1.0, 6.0)),
    # leaf-to-leaf drift on a spliced veneer. The stretch is ALONG the grain
    # (6x in z) so the drift reads as neighbouring leaves at slightly different
    # tone, never as a stain blotch crossing the grain.
    "veneer_oak": (0.16, 1.6, (1.0, 1.0, 6.0)),
    "veneer_oak_h": (0.16, 1.6, (6.0, 1.0, 1.0)),
    "veneer_travertine": (0.16, 1.6, (1.0, 1.0, 6.0)),
}


def _set_fresnel(bsdf, ior, level):
    """Apply a FRESNEL row, tolerating socket renames across Blender versions.

    Reports what it could NOT set rather than failing silently: a specular
    control that quietly no-ops is exactly how this lane spent four rounds
    bracketing a number that was never reaching the render.
    """
    missed = []
    for names, value in ((("IOR",), ior),
                         (("Specular IOR Level", "Specular"), level)):
        if value is None:
            continue
        for n in names:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = float(value)
                break
        else:
            missed.append(names[0])
    return missed


def build_materials(palette_override=None, fresnel_override=None):
    """{palette key: bpy Material}. bpy-only — imported from the builder.

    Every mapped material is BOX-PROJECTED on object coordinates because these
    meshes carry no UVs by construction (authored quads, never unwrapped), and
    normalised by its map's own mean so the MAP carries variation while the
    MEASURED value carries identity. Both halves of that normalisation are
    applied — base colour AND roughness — because trn001 shipped four rounds
    with only the first, and its hero material's polish never reached a frame.
    """
    import bpy
    pal = dict(PALETTE)
    pal.update(palette_override or {})
    fres = resolve_fresnel(pal, fresnel_override)
    out = {}
    for key, (alb, rough, metal, slug, scale) in pal.items():
        m = bpy.data.materials.new(f"M_TRN002_{key}")
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*alb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if key in fres:
            missed = _set_fresnel(bsdf, *fres[key])
            print(f"  fresnel {key}: ior={fres[key][0]} level={fres[key][1]}"
                  + (f"  !! SOCKET NOT FOUND: {missed}" if missed else ""))
        if key in EMISSIVE:
            bsdf.inputs["Emission Color"].default_value = (*alb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = EMISSIVE[key]
        if not slug or slug not in MAP_FILE:
            out[key] = m
            continue
        diff_f, rough_f, nor_f = MAP_FILE[slug]
        coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        uv = key in UV_MAPPED
        s = 1.0 if uv else 1.0 / max(scale, 1e-6)
        mapping.inputs["Scale"].default_value = (s, s, s)
        if key in MAP_ROT:
            import math as _math
            mapping.inputs["Rotation"].default_value = tuple(
                _math.radians(a) for a in MAP_ROT[key])
        nt.links.new(coord.outputs["UV" if uv else "Object"], mapping.inputs["Vector"])

        def _tex(fname, non_color):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(os.path.join(CC0, slug, fname),
                                           check_existing=True)
            if not uv:
                t.projection = "BOX"
                t.projection_blend = 0.3
            t.extension = "REPEAT"
            if non_color:
                t.image.colorspace_settings.name = "Non-Color"
            nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
            return t

        # DIFFUSE-OFF materials still get their weave/relief from the normal
        # map — the target's fabrics carry texture the eye reads as cloth while
        # measuring near-zero COLOUR variation, and those are different maps.
        if key in DIFFUSE_OFF:
            if nor_f:
                nt_tex = _tex(nor_f, True)
                nmapn = nt.nodes.new("ShaderNodeNormalMap")
                nmapn.inputs["Strength"].default_value = NORMAL_STRENGTH.get(key, 0.3)
                nt.links.new(nt_tex.outputs["Color"], nmapn.inputs["Color"])
                nt.links.new(nmapn.outputs["Normal"], bsdf.inputs["Normal"])
            out[key] = m
            continue
        # base colour: (map / map_mean) * albedo
        tex = _tex(diff_f, False)
        mean = MAP_MEAN[slug]
        div = nt.nodes.new("ShaderNodeVectorMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = mean
        nt.links.new(tex.outputs["Color"], div.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.inputs[6].default_value = (*alb, 1.0)
        nt.links.new(div.outputs["Vector"], mul.inputs[7])
        base_out = mul.outputs[2]

        if key in TONE_NOISE:
            amp, nscale, stretch = TONE_NOISE[key]
            nmap = nt.nodes.new("ShaderNodeMapping")
            nmap.inputs["Scale"].default_value = stretch
            nt.links.new(coord.outputs["Object"], nmap.inputs["Vector"])
            noise = nt.nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = nscale
            nt.links.new(nmap.outputs["Vector"], noise.inputs["Vector"])
            tone = nt.nodes.new("ShaderNodeMix")
            tone.data_type = "RGBA"
            tone.blend_type = "MULTIPLY"
            tone.inputs["Factor"].default_value = amp
            nt.links.new(base_out, tone.inputs[6])
            nt.links.new(noise.outputs["Fac"], tone.inputs[7])
            base_out = tone.outputs[2]
        nt.links.new(base_out, bsdf.inputs["Base Color"])

        if rough_f and slug in ROUGH_MEAN:
            rt = _tex(rough_f, True)
            rdiv = nt.nodes.new("ShaderNodeMath")
            rdiv.operation = "DIVIDE"
            nt.links.new(rt.outputs["Color"], rdiv.inputs[0])
            rdiv.inputs[1].default_value = ROUGH_MEAN[slug]
            rmul = nt.nodes.new("ShaderNodeMath")
            rmul.operation = "MULTIPLY"
            nt.links.new(rdiv.outputs["Value"], rmul.inputs[0])
            rmul.inputs[1].default_value = rough
            nt.links.new(rmul.outputs["Value"], bsdf.inputs["Roughness"])

        if nor_f:
            nt_tex = _tex(nor_f, True)
            nmapn = nt.nodes.new("ShaderNodeNormalMap")
            nmapn.inputs["Strength"].default_value = NORMAL_STRENGTH.get(key, 0.3)
            nt.links.new(nt_tex.outputs["Color"], nmapn.inputs["Color"])
            nrm_out = nmapn.outputs["Normal"]
            if key in CRUMPLE:
                # CHAINED, not replacing: the weave map feeds the bump's own
                # Normal input, so the material carries both the thread and the
                # fold instead of one overwriting the other.
                cs, cstr, cstretch = CRUMPLE[key]
                cmap = nt.nodes.new("ShaderNodeMapping")
                cmap.inputs["Scale"].default_value = cstretch
                nt.links.new(coord.outputs["Object"], cmap.inputs["Vector"])
                cn = nt.nodes.new("ShaderNodeTexNoise")
                cn.inputs["Scale"].default_value = cs
                cn.inputs["Detail"].default_value = 6.0
                cn.inputs["Roughness"].default_value = 0.6
                nt.links.new(cmap.outputs["Vector"], cn.inputs["Vector"])
                bump = nt.nodes.new("ShaderNodeBump")
                bump.inputs["Strength"].default_value = cstr
                bump.inputs["Distance"].default_value = 0.05
                nt.links.new(cn.outputs["Fac"], bump.inputs["Height"])
                nt.links.new(nrm_out, bump.inputs["Normal"])
                nrm_out = bump.outputs["Normal"]
            nt.links.new(nrm_out, bsdf.inputs["Normal"])
        out[key] = m
    return out


def palette_report():
    """One line per material with its provenance — printed at every build so a
    gate artifact can never quote a measured-looking number that was assumed."""
    out = []
    for k in sorted(PALETTE):
        alb, rough, metal, slug, scale = PALETTE[k]
        out.append(f"  {k:20s} alb=({alb[0]:.3f},{alb[1]:.3f},{alb[2]:.3f}) "
                   f"r={rough:.2f} m={metal:.1f} map={slug or '-':18s} "
                   f"{PALETTE_PROV.get(k, 'PROV MISSING')}")
    return "\n".join(out)
