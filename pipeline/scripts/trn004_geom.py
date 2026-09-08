#!/usr/bin/env python3
"""trn004_geom.py — TRN-004 penthouse bathroom: the PURE half of the reproduction.

WHAT IS BEING REPRODUCED. A public 23:51 Blender tutorial ("Blender Interior Design
Tutorial - Luxury Penthouse Bathroom", Aryan, watched 2026-08-29, id _7_HiynmdOc).
It is picked because five of its moves are mechanisms this repo does not have, and
one of them lands directly on a defect the plan of record is carrying (the wall
texture that repeats).

WHY A PURE MODULE AND NOT A bpy SCRIPT. Layer law (pipeline/CLAUDE.md): rules + spec
are pure python, `trn004_build.py` only materialises. That is what makes the numbers
below TESTABLE without launching Blender — see test_trn004_geom.py.

THE NUMBERS THAT CAME FROM THE VIDEO ARE MARKED `# VID`. They were READ OFF THE
BLENDER UI IN THE FRAME, not inferred from what he said, and each carries its
timestamp so the claim can be re-checked against the frame. Everything NOT marked
`# VID` is ours and must cite a knowledge/ source or be a declared assumption —
the tutorial is a source for TECHNIQUE, never for a Thai residential dimension.

THE ONE THING THE VIDEO IS NOT A SOURCE FOR. Its reference image is AI-GENERATED
(Canva Dream Lab, prompt visible at 00:54). A synthesised image is a PRIOR, not a
measurement: it cannot be cited for a dimension, a clearance or a code. It is used
here only as the tutorial's own starting point, and our reproduction target is his
FINISHED RENDER, which is a real artefact.
"""
import math

SCHEMA = "trn004-geom@0.1"

# ---------------------------------------------------------------------------
# ROOM. Ours, not his — he never states a dimension in the video, so copying a
# room from a frame would be inventing a measurement (R10: an object invented to
# satisfy a structure is a declared assumption). These are DECLARED ASSUMPTIONS
# sized from our own ergonomics so the props below have something real to sit on.
# ---------------------------------------------------------------------------
ROOM_W_MM = 2600.0      # assumption: a long narrow ensuite, one vanity wall + one tub wall
ROOM_L_MM = 5200.0      # assumption
ROOM_H_MM = 3000.0      # assumption: penthouse floor-to-ceiling
WALL_T_MM = 150.0       # assumption

# Vanity. knowledge/ergonomics/casework-fixture-clearances-th-practice.md is the
# repo's own source for counter heights; 850 is the value this lane already uses.
COUNTER_H_MM = 850.0
COUNTER_D_MM = 600.0
COUNTER_T_MM = 40.0     # slab thickness (assumption, joinery-plausible)

# Basin. Built the way the video builds it: inset the counter top face, then
# SHRINK/FATTEN the inset face downward. The wall thickness of the resulting
# vessel IS the shrink offset — that is the whole trick, and it is why the basin
# never needs a separate "thickness" number typed anywhere.
BASIN_W_MM = 500.0      # assumption
BASIN_D_MM = 360.0      # assumption
BASIN_DEPTH_MM = 130.0  # assumption
BASIN_SHRINK_MM = 10.1  # VID 15:52 — "Shrink/Fatten Offset -0.0101 m", read off the operator panel

# Mirror. VID 18:09 — "Extrude Region and Move ... Z -0.004898 m" on the mirror plane.
MIRROR_T_MM = 4.898     # VID 18:09
MIRROR_SILL_MM = 1050.0  # assumption: 200 above the counter
MIRROR_H_MM = 1400.0     # assumption

# Towels. VID 17:48-17:58: a folded towel is a rounded box; a stack is 2-3 of them;
# the roll on top is a CYLINDER lying down. No cloth sim, no sculpt — this is the
# R8 BUILD side of the build/acquire test (boxes with radii; a swept profile).
TOWEL_W_MM = 300.0      # assumption
TOWEL_D_MM = 220.0      # assumption
TOWEL_T_MM = 55.0       # assumption: one folded bath towel
TOWEL_STACK_N = 3       # VID 17:50 — three in the stack in his frame
TOWEL_ROLL_D_MM = 110.0  # assumption
TOWEL_FOLD_LIP_MM = 12.0  # the lip loop that reads as the fold (assumption)

# ---------------------------------------------------------------------------
# GLAZING. VID 10:18-11:20 — the glass wall is divided into vertical bays by
# near-black mullion posts, and the glass itself is a Glass BSDF.
# ---------------------------------------------------------------------------
MULLION_W_MM = 60.0     # assumption
MULLION_D_MM = 80.0     # assumption
GLASS_T_MM = 12.0       # assumption
GLASS_ROUGHNESS = 0.500  # VID 12:04 — Material.022 Glass BSDF, Multiscatter GGX
GLASS_IOR = 1.500        # VID 12:04
MULLION_METALLIC = 1.000  # VID 01:30 — "Window Bar" material
MULLION_ROUGHNESS = 0.206  # VID 01:30

# ---------------------------------------------------------------------------
# BACKDROP. The single most transferable idea in the video and the one this repo
# does not have: the city outside is a PLANE with a photo, placed far away, and
# its material EMITS. It is not scenery you look at, it is the light source that
# makes a night interior read as a night interior.
# ---------------------------------------------------------------------------
BACKDROP_Y_M = 106.02    # VID 08:43 — Move Y, read off the operator panel
BACKDROP_Z_M = 40.043    # VID 08:43 — Move Z
BACKDROP_X_M = -0.96274  # VID 08:43 — Move X
BACKDROP_EMISSION = 55.0  # VID 11:10 — Material.020 Emission Strength

# THE TRAP THAT COMES WITH IT, and it is silent: a plane 106 m away is beyond the
# viewport's default far clip, so it vanishes from the VIEWPORT while still
# rendering. He raises the clip end (VID 03:53: End 1415 m). A number that only
# affects what you can SEE while working is exactly the kind that gets left wrong.
CLIP_END_M = 1415.0      # VID 03:53
FOCAL_MM = 25.4          # VID 03:53 — his viewport focal length

# ---------------------------------------------------------------------------
# LIGHTS. VID 08:29 and 22:35 — read off the light data panel in two frames.
# The shape of the spec is the lesson: (kelvin, watts, shape, size, spread).
# Every one of the five is a PHYSICAL quantity. None of them is "brightness".
# ---------------------------------------------------------------------------
LIGHTS_VID = (
    # (name,        kelvin, watts,  shape,    size_m, spread_deg, source)
    ("wall_wash",   4248.0, 326.800, "SQUARE", 1.0, 126.0, "VID 08:29 Area.005"),
    ("ceiling_key",   None, 451.600, "DISK",   1.0,  75.3, "VID 22:35 Area.003/005 (colour swatch warm, K not shown)"),
)

# The sconce is not a light object at all — it is an EMISSIVE PLANE behind a
# frosted panel. VID 12:26: Emission colour #FFD389 (H 0.083 / S 0.512 / V 1.000),
# Strength 34.7, then dialled to 15.0 at 12:30 once he looked at it.
SCONCE_HEX = "FFD389"      # VID 12:26
SCONCE_HSV = (0.083, 0.512, 1.000)  # VID 12:26 — the panel's own readout
SCONCE_EMISSION_FIRST = 34.700  # VID 12:26
SCONCE_EMISSION_FINAL = 15.000  # VID 12:30 — halved after one look. R5 in his hands.

# ---------------------------------------------------------------------------
# THE SLAB LAYOUT. VID 19:29-20:30. A Brick Texture node is used NOT to make
# bricks but as a SLAB GRID: Color1 = the stone photo, Color2 = a dark joint,
# and the node's own per-brick offset means each slab samples the photo at a
# different place. That is what stops one photo reading as one smeared repeat.
# ---------------------------------------------------------------------------
BRICK_VID = {
    "offset": 0.500,        # VID 19:29 — running-bond half offset
    "offset_frequency": 2,  # VID 19:29
    "squash": 1.000,        # VID 19:29
    "squash_frequency": 2,  # VID 19:29
    "scale": 5.000,         # VID 19:29
    "mortar_size": 0.020,   # VID 19:29
    "mortar_smooth": 0.100,  # VID 19:29
    "bias": 0.000,          # VID 19:29
    "brick_width": 0.500,   # VID 19:29
    "row_height": 0.250,    # VID 19:29
}

# VID 21:44 — the SAME travertine map, retinted into a second material by
# Brightness/Contrast (-0.300 / -0.300) -> Hue/Saturation/Value (Sat 0.800,
# Value 0.300). One download, two stones. This is why his "marble" and his
# "porcelain" slots share a texture and still read as different materials.
RETINT_VID = {
    "bright": -0.300,     # VID 21:44
    "contrast": -0.300,   # VID 21:44
    "hue": 1.000,         # VID 21:44
    "saturation": 0.800,  # VID 21:44
    "value": 0.300,       # VID 21:44
    "fac": 1.000,         # VID 21:44
}

# VID 18:51 — the ambientCG asset page publishes the map's REAL-WORLD SIZE next
# to the download buttons ("Travertine 003 ... Dimensions ca. 1.2 m"). This repo
# already has a rung that wants exactly that number (texture_scale.py) and a
# fetcher that cannot reach that publisher (assets.py knows Poly Haven only).
AMBIENTCG_EXAMPLE = {"slug": "Travertine003", "dimensions_m": 1.2, "source": "VID 18:51"}


# ---------------------------------------------------------------------------
# DERIVATIONS. R9: a position that can be derived from a contact must never be
# typed. Everything below returns a CONTACT, not a coordinate.
# ---------------------------------------------------------------------------
def counter_top_z_mm():
    """The datum every vanity prop rests on."""
    return COUNTER_H_MM


def basin_rim_z_mm():
    """The basin is UNDERMOUNT: its rim is the underside of the slab, not the top.
    Typing the counter height here would be the classic one-number-two-meanings
    defect the placement audit named."""
    return COUNTER_H_MM - COUNTER_T_MM


def basin_floor_z_mm():
    return basin_rim_z_mm() - BASIN_DEPTH_MM


def towel_stack_layers():
    """Each folded towel RESTS on the one below. Returns bottom-z per layer, so
    a changed towel thickness moves every layer above it and nothing is typed."""
    z = counter_top_z_mm()
    out = []
    for i in range(TOWEL_STACK_N):
        out.append(round(z, 6))
        z += TOWEL_T_MM
    return out


def towel_roll_axis_z_mm():
    """The roll lies ON the stack, so its AXIS is one radius above the top face."""
    top = counter_top_z_mm() + TOWEL_STACK_N * TOWEL_T_MM
    return top + TOWEL_ROLL_D_MM / 2.0


def basin_shell_thickness_mm():
    """The shrink/fatten offset IS the vessel wall. Stated as a derivation so the
    two can never drift apart — the defect that turns up whenever one quantity is
    written down twice."""
    return BASIN_SHRINK_MM


def mullion_bay_centres_mm(run_mm, n_bays):
    """Mullion posts split a glazed run into n equal bays. Returns the post
    centres INCLUDING the two ends, derived from the run — never a typed list."""
    if n_bays < 1:
        raise ValueError("n_bays must be >= 1")
    step = run_mm / float(n_bays)
    return [round(i * step, 6) for i in range(n_bays + 1)]


def backdrop_distance_m():
    """Straight-line distance from the origin to the backdrop plane's origin."""
    return math.sqrt(BACKDROP_X_M ** 2 + BACKDROP_Y_M ** 2 + BACKDROP_Z_M ** 2)


def clip_end_is_sufficient(clip_end_m=CLIP_END_M, margin=1.5):
    """THE RUNG THIS FILE EXISTS TO CARRY. A backdrop beyond the far clip plane
    disappears from the viewport while still rendering — so the builder works
    blind on the one object that carries the scene's light. Fails CLOSED."""
    need = backdrop_distance_m() * margin
    return clip_end_m >= need, need


def brick_slab_size_m(scale=None, brick_width=None, row_height=None):
    """The Brick node's width/height are in ITS OWN scaled space, so the real slab
    size on the surface is width/scale. Stating it as a derivation is the point:
    'Brick Width 0.5' means nothing until you divide by Scale.

    Returns (slab_w_m, slab_h_m) for a mapping where 1.0 texture unit = 1 m."""
    s = BRICK_VID["scale"] if scale is None else scale
    w = BRICK_VID["brick_width"] if brick_width is None else brick_width
    h = BRICK_VID["row_height"] if row_height is None else row_height
    if s <= 0:
        raise ValueError("scale must be > 0")
    return (w / s, h / s)


def brick_mortar_width_m(scale=None, mortar_size=None):
    """The joint's real width, same reasoning as above. A 0.02 mortar at scale 5
    is a 4 mm joint — which is a REAL stone joint. At scale 1 it would be 20 mm,
    which is a brick joint. The number alone cannot tell you which you built."""
    s = BRICK_VID["scale"] if scale is None else scale
    m = BRICK_VID["mortar_size"] if mortar_size is None else mortar_size
    if s <= 0:
        raise ValueError("scale must be > 0")
    return m / s


def sconce_rgb_linear():
    """#FFD389 -> linear RGB, so the emissive plane can be built from the hex the
    video shows rather than from a guess at 'warm'."""
    srgb = [int(SCONCE_HEX[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    out = []
    for c in srgb:
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(round(v, 6) for v in out)


def light_rows():
    """The five-field light spec, as rows. The lesson is the SHAPE: every field is
    a physical quantity with a unit. `None` where the video did not show it —
    an unknown that prints as unknown, never as a default."""
    rows = []
    for name, k, w, shape, size, spread, src in LIGHTS_VID:
        rows.append({
            "name": name, "kelvin": k, "watts": w, "shape": shape,
            "size_m": size, "spread_deg": spread, "source": src,
        })
    return rows


def unknown_light_fields():
    """Which of the five the video did NOT show. Printed rather than filled in."""
    out = []
    for r in light_rows():
        miss = [k for k in ("kelvin", "watts", "shape", "size_m", "spread_deg")
                if r[k] is None]
        if miss:
            out.append((r["name"], miss))
    return out


def brick_settings_for_slab(slab_w_m, slab_h_m, joint_m, uv_m_per_unit=1.0):
    """SOLVE the Brick node's settings from the slab you actually want.

    WHY THIS FUNCTION AND NOT THE VIDEO'S NUMBERS. Reproducing his values
    (scale 5.0, brick width 0.5, row height 0.25) and rendering them gives
    100 x 50 mm units with a 4 mm joint. That is SUBWAY TILE. It is a fine
    ceiling and it is not a marble slab, and no amount of looking at the node
    panel says so — the panel shows 0.5, and 0.5 of WHAT is only answerable
    after dividing by Scale and multiplying by the mapping.

    That is the same defect this repo has already paid for twice under another
    name: a texture whose real-world size was never asserted. `Brick Width 0.5`
    is a number with no unit until the mapping is fixed, exactly as a colour map
    has no scale until the publisher's dimensions are read.

    So: name the slab in millimetres, get the node values. Fails closed on a
    joint that cannot fit."""
    if slab_w_m <= 0 or slab_h_m <= 0:
        raise ValueError("slab dimensions must be > 0")
    if joint_m <= 0 or joint_m >= min(slab_w_m, slab_h_m) / 2.0:
        raise ValueError(f"joint {joint_m} m does not fit a {slab_w_m}x{slab_h_m} m slab")
    scale = 1.0 / float(uv_m_per_unit)
    return {
        "scale": scale,
        "brick_width": slab_w_m * scale,
        "row_height": slab_h_m * scale,
        "mortar_size": joint_m * scale,
        "mortar_smooth": 0.10,
        "bias": 0.0,
        "offset": 0.5,
        "offset_frequency": 2,
        "squash": 1.0,
        "squash_frequency": 2,
    }


# Real stone slab sizes, for the derivation above to be aimed at something.
# 1200x600 is the commodity porcelain/marble-look slab; a genuine book-matched
# marble slab is larger. Sourced as a DECLARED ASSUMPTION until a catalogue
# row backs it — the video is not a source for a product dimension.
SLAB_STONE_M = (1.2, 0.6)
SLAB_JOINT_M = 0.004


def main():
    ok, need = clip_end_is_sufficient()
    sw, sh = brick_slab_size_m()
    print(f"TRN-004 {SCHEMA}")
    print(f"  backdrop distance      {backdrop_distance_m():.2f} m")
    print(f"  clip end {CLIP_END_M:.0f} m needs >= {need:.0f} m -> {'OK' if ok else 'FAILS'}")
    print(f"  brick slab (VID values) {sw * 1000:.0f} x {sh * 1000:.0f} mm"
          f"  <- SUBWAY TILE, not slab")
    d = brick_settings_for_slab(SLAB_STONE_M[0], SLAB_STONE_M[1], SLAB_JOINT_M)
    dw, dh = brick_slab_size_m(d["scale"], d["brick_width"], d["row_height"])
    dj = brick_mortar_width_m(d["scale"], d["mortar_size"])
    print(f"  brick slab (derived)    {dw * 1000:.0f} x {dh * 1000:.0f} mm, joint {dj * 1000:.1f} mm")
    print(f"  brick joint            {brick_mortar_width_m() * 1000:.1f} mm")
    print(f"  basin rim z            {basin_rim_z_mm():.1f} mm (undermount)")
    print(f"  basin shell            {basin_shell_thickness_mm():.1f} mm")
    print(f"  towel layers           {towel_stack_layers()}")
    print(f"  towel roll axis z      {towel_roll_axis_z_mm():.1f} mm")
    print(f"  sconce linear rgb      {sconce_rgb_linear()}")
    for name, miss in unknown_light_fields():
        print(f"  UNKNOWN {name}: {', '.join(miss)} — not shown in the video, not invented")


if __name__ == "__main__":
    main()
