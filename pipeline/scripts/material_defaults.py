#!/usr/bin/env python3
"""material_defaults.py — the pipeline's HARDCODED render palette, as SHARED DATA.

build_room.py assigns every material by kind -> name-prefix -> a hardcoded constant
(there is no material field in room-spec@0.2, and build_room reads none). rationale.py
must DESCRIBE those same defaults truthfully or it lies about what the render shows.
This module is the single source of truth for the kind->family mapping + the slug each
family renders as, so the two can never silently drift. Pure stdlib ON PURPOSE:
build_room imports bpy and is NOT importable for a test; this is (and rationale +
test_rationale import it).

Honesty: these are STUDIO RENDER DEFAULTS, tuned by past A/B render gates and keyed to
KIND — not chosen for any client, brief, concept, or spec. Every project renders this
same "warm modern-luxury" palette. The description strings + slugs MUST match
build_room.py _suite_materials / _mat_tag (test_rationale.py drift-guards the slugs).
"""

# kind families (mirrored INTO build_room via import so _mat_tag stays in lockstep)
FABRIC_KINDS = {"sofa", "loveseat", "armchair", "chair", "dining_chair", "bed", "bench"}
WOODEN_KINDS = {"coffee_table", "dining_table", "side_table", "nightstand", "desk", "table",
                "vanity", "platform", "tv_console", "cabinet"}

# (human-readable material, build_room slug) per render-default family.
BUILTIN_MATERIAL = ("rift-walnut veneer, matte lacquer (linear ~#5F4430)", "mill_walnut")
FIXTURE_MATERIAL = ("glossy white sanitaryware solid", "sanitary_white")
FABRIC_MATERIAL = ("cream bouclé solid (sheen)", "fabric_boucle")
WOODEN_MATERIAL = ("oak PBR (wood_floor slug)", "wood_oak")
NEUTRAL_MATERIAL = ("neutral solid", "furn_neutral")
# whole-room surfaces (build_room constants FLOOR_SLUG / WALL_RGBA / feature_walnut)
FLOOR_MATERIAL = ("oak plank PBR", "wood_floor")
WALL_MATERIAL = ("matte warm-white paint", "wall_paint")
FEATURE_WALL_MATERIAL = ("walnut feature wall (the hardcoded south/hero backdrop)", "feature_walnut")

# every slug rationale.py names — test_rationale asserts each still appears in
# build_room.py's source, so a rename there fails the test instead of silently lying.
ALL_SLUGS = ("mill_walnut", "sanitary_white", "fabric_boucle", "wood_oak", "furn_neutral",
             "wood_floor", "wall_paint", "feature_walnut")


def default_material(kind, group):
    """(description, slug) that build_room renders for an element, by its ARRAY then
    kind. build_room prefixes ALL builtins 'mill__' (walnut) and ALL fixtures 'fix__'
    regardless of kind, so `group` decides first; loose items dispatch on kind."""
    if group == "builtins":
        return BUILTIN_MATERIAL
    if group == "fixtures":
        return FIXTURE_MATERIAL
    if kind in FABRIC_KINDS:
        return FABRIC_MATERIAL
    if kind in WOODEN_KINDS:
        return WOODEN_MATERIAL
    return NEUTRAL_MATERIAL
