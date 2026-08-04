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

WHAT IS DIFFERENT HERE: TRN-002's palette is dominated by a pale travertine-look
veneer run (console/desk/etagere), smoked-oak wardrobe fronts, white paint, and
a herringbone floor — and every mass in the frame is measured geometry, so a
material can be assigned by NAME with no guessing about which surface is which.

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
    "floor": "floor_herringbone",
    "back_wall": "paint_white", "left_wall": "paint_white",
    "right_wall": "paint_white", "door_wall": "paint_white",
    "ceil_main": "paint_ceiling",
    "ward_bulkhead": "lacquer_wardrobe", "ward_body": "lacquer_wardrobe",
    "ward_groove": "reveal_shadow",
    "door_leaf": "lacquer_white",
    "artwork": "art_relief",
    "part_head": "frame_black", "part_jamb_L": "frame_black",
    "part_jamb_R": "frame_black", "part_stile_M": "frame_black",
    "part_rail_B": "frame_black",
    "closet_floor": "floor_herringbone", "closet_back": "paint_white",
    "desk": "veneer_travertine", "console": "veneer_travertine",
    "desk_pier": "veneer_travertine",
    "shelf_col_base": "veneer_travertine", "shelf_col_back": "veneer_travertine",
    "tv": "screen_black",
    "rug": "rug_cream",
    "bed_platform": "upholstery_bed", "bed_headboard": "upholstery_bed",
    "bed_mattress": "linen_white",
    "duvet_top": "linen_white", "duvet_drape": "linen_white",
    "pillow_L": "linen_white", "pillow_R": "linen_white", "bolster": "linen_white",
    "ward_band": "oak_band",
    "nightstand": "oak_band",
    "bench": "upholstery_bed",
    "petcave": "upholstery_bed",
    "lamp_shade": "shade_black", "lamp_stem": "shade_black",
    "chair_seat": "upholstery_chair", "chair_back": "upholstery_chair",
}
PREFIX = (
    ("rev_", "reveal_shadow"),
    ("dl_", "lens_warm"),
    ("shelf_board", "veneer_travertine"),
)


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
PALETTE = {}
PALETTE_PROV = {}

# ------------------------------------------------------------- bpy builders --
MAP_MEAN = {
    "wood_floor": (0.2189, 0.1185, 0.0557),
    "plastered_wall_03": (0.2495, 0.2061, 0.1679),
    "marble_01": (0.4493, 0.3397, 0.1936),
    "grey_cartago_03": (0.2664, 0.2489, 0.2317),
}
ROUGH_MEAN = {"wood_floor": 0.471, "plastered_wall_03": 0.911, "marble_01": 0.506}
NORMAL_STRENGTH = {
    "floor_herringbone": 1.6,          # planks DO carry a joint micro-bevel
    "veneer_travertine": 0.10,         # spliced flush and sanded — not a floor
    "oak_band": 0.10, "lacquer_wardrobe": 0.06,
    "paint_white": 0.12, "paint_ceiling": 0.12,
}
TONE_NOISE = {
    "floor_herringbone": (0.30, 2.2, (0.35, 1.0, 6.0)),
    "veneer_travertine": (0.16, 1.6, (0.5, 1.0, 3.0)),
    "oak_band": (0.16, 1.6, (3.0, 1.0, 0.5)),
}


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
