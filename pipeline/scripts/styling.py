"""
styling.py — ELEMENT 8 (PRJ-2026-002): the styling layer, derived from BUILT geometry.
Pure Python (NO bpy), metres in/out, deterministic, unit-tested.

WHY THIS MODULE EXISTS (2026-07-22)
-----------------------------------
Six rendered frames were put in front of the owner and the verdict was "ยังดูไม่มี style".
The DD's ground phase read the pixels and found two things:

  1. NOTHING IN THE ROOM DEFORMS — soft goods were modelled with joinery's primitive.
     That is softgoods.py's problem, and this module is its first consumer.
  2. NOTHING IS ON ANYTHING. Zero objects sit on any horizontal surface in the entire
     hero frame. Three satin-brass hang rails carry no garment; ~25 open shelf cavities
     across three wardrobe frames are empty; a 3.2 m makeup-vanity counter is bare.

(2) is not a taste gap, it is a WIRING gap with a name: build_room._dress_scene only
fires for a `coffee_table`/`round_table` item, and this suite has neither, so the master
suite has always received exactly ZERO decor pieces. And the garments are worse than
missing — element 7's DD promised "satin-brass hang rails with garments" in writing, and
wardrobe_bay_story_bits still tells the beauty pass they are there. That is the studio's
recurring revert-by-omission wound in its purest form: decided data that the build never
made, with prose still asserting it.

THE DERIVATION LAW (the thing that makes this module different from a prop list)
-------------------------------------------------------------------------------
Every styled object hangs off an ANCHOR: a part that the build actually emitted, passed
in by name with its real coordinates. A garment is positioned from the rail it hangs on,
not from a number in this file. So if a rail moves, its garments move; if a shelf is
re-pitched, its stack re-sits; and if an anchor DISAPPEARS, this module RAISES instead of
quietly shipping an empty rail again. Hardcoding a coordinate here would re-create the
exact defect the module exists to fix — it would let the render and the decision drift
apart silently, which is how the bay shipped empty in the first place.

ANCHOR CONTRACT
---------------
`anchors` is a list of dicts as emitted by the build:
    {"name": "mill__BF09-3__rail_short0", "x":, "y":, "z":, "dx":, "dy":, "dz":}
in absolute metres. This module never invents one.

PART CONTRACT
-------------
Returns a list of dicts the consumer materialises:
    {"name":  object name (carries the material token — see material_presets),
     "shape": "box" | "mesh",
     # shape == "box":
     "x","y","z","dx","dy","dz", "bevel": float,
     # shape == "mesh":
     "verts": [(x,y,z), ...] ABSOLUTE metres, "faces": [(i,j,k,l), ...]}
"""

import math

import softgoods as sg

MM = 0.001

# --- material tokens ------------------------------------------------------------------
# ELEMENT 8 INTRODUCES NO NEW MATERIAL FAMILY (D1-A anti-monopoly + the closed palette).
# Every styled object wears an identity the suite already owns, and it reaches it through
# the EXISTING router: a part named `mill__<piece>__<token>` is painted by
# material_presets.mill_object_role, which already has branches for brass / cool /
# backer / towel / counter / mirror. Only ONE new row is added (`linen`), because the
# greige stonewashed linen was signed in element 3 but was re-hardcoded inside each
# builder instead of being reachable BY NAME — this element is what makes it a token.
#
# Bed-family soft goods deliberately do NOT use this router: they keep the `bed__` prefix
# and are handed _build_bed's own bespoke bedding materials, which is the channel
# bed__coverlet already uses. That keeps them out of the mill__ vocabulary entirely, so
# there is no silent-walnut exposure on the hero object.
TOK_LINEN = "linen"        # greige stonewashed linen (NEW row; the element-3 identity)
TOK_INK = "backer"         # matte-black ply — the EXISTING backer* branch, the dark anchor
TOK_MINERAL = "cool"       # cool microcement — the EXISTING `cool` branch
TOK_BRASS = "brass"        # satin brass — the EXISTING branch
TOK_TERRY = "towel"        # greige-oatmeal terry — the EXISTING element-6 branch
TOK_OAK = "oakboard"       # no special token -> the router's oak default (book boards)
# A vessel is sanitaryware-white porcelain. It does NOT go through the mill__ router:
# material_presets.FIXTURE_MAT_OBJECT already maps the `porcelain` role to `fix__{b}`,
# so a vessel is named with the fix__ prefix and inherits that identity unchanged.
TOK_PORCELAIN = "porcelain"

# Bed-family part prefixes (materials assigned inline by build_room._build_bed).
BED_COVER = "bed__coverlet"
BED_PILLOW = "bed__pillow"

# A garment hangs from a rail; these are its proportions, not its position.
#
# ORIENTATION — the blocker both DD critics caught independently, by running the numbers:
# a hanger's shoulder bar runs FRONT-TO-BACK across the carcass, NOT along the rail. So a
# garment's SHOULDER SPAN lies on the depth axis and its THICKNESS lies along the rail,
# and the pitch is the thickness of a garment on its hanger. Getting this backwards packs
# 400mm-wide shells at 52mm centres — twelve garments totalling 4.8 m of cloth stuffed
# into a 635 mm rail, every one interpenetrating its neighbours. Drops are vault-cited:
# shirt/blouse 1100, dress 1400, coat 1600, trousers-on-hanger 500
# (knowledge/.../casework-fixture-clearances-th-practice.md 2.1).
SHORT_DROP = 0.86          # a folded-over jacket / short garment — STUDIO CONVENTION,
#                            deliberately NOT presented as vault-cited: the source has no
#                            900 row (critic's minor finding; labelled, not smuggled).
FULL_DROP = 1.40           # dress (vault row); coats 1600 exceed BF09-3's full-hang clear
GARMENT_PITCH = 0.068      # centre-to-centre along the rail = a garment's own thickness
SHOULDER_MAX = 0.46        # shoulder span across the depth axis, before the clear check
MIN_GARMENTS = 3           # a rail with fewer than this does not read as a wardrobe
#                            (3, not 4: the bay's BF09-1-0 rails are a real 264mm run)
GARMENT_FOLD = 0.006       # crease amplitude — SMALL, because it is spent on the pitch
GARMENT_LEAN = 0.004       # lean along the rail — likewise
GARMENT_HEM = 0.014        # hem wander — spent on the clear drop
SHOULDER_DROP = 0.020      # shoulder sits this far below the rail. At 62mm the hanger's
#                            bar and stem stood PROUD of every garment and the rail read
#                            as a row of black sticks; a real garment's shoulder covers
#                            its hanger and only the hook shows above.


def _fail(msg):
    raise ValueError(f"styling: {msg}")


def find(anchors, prefix, required=True):
    """Every anchor whose part token STARTS WITH `prefix`, in build order.

    RAISES when a required anchor is absent — the whole point of the module. A silent []
    here is exactly how three brass rails shipped bare while the story bits claimed
    garments hung on them."""
    hits = [a for a in anchors if _token(a).startswith(prefix)]
    if required and not hits:
        have = sorted({_token(a) for a in anchors})
        _fail(f"no anchor part matching {prefix!r} — decided styling cannot be placed on "
              f"geometry that was not built. Anchors present: {have}")
    return hits


def _token(a):
    """What an anchor IS. Prefer the explicit `part` the builder recorded; fall back to
    the object name's trailing token.

    WHY THE FALLBACK IS NOT ENOUGH: the wardrobe bay routes its parts by MATERIAL
    (`mill__bayBF09-1-0_rail_short0__brass`), so its rails' trailing token is `brass` and
    a name-only match finds ZERO of the bay's six rails — the render would have dressed
    BF09-3 and left the walk-in the owner rejected twice exactly as empty as before, and
    nothing would have failed."""
    if a.get("part"):
        return a["part"]
    return a["name"].rsplit("__", 1)[-1]


def _long_axis(a):
    """('x'|'y') the anchor runs along, and its (lo, hi) extent on that axis."""
    if a["dx"] >= a["dy"]:
        return "x", (a["x"], a["x"] + a["dx"])
    return "y", (a["y"], a["y"] + a["dy"])


def piece_of(a):
    """The built piece an anchor belongs to. Explicit when the builder recorded it —
    a bay part's object name is per-PART, so string-splitting it would put every part in
    a piece of its own and the sibling search (which derives every clearance) would find
    nothing to measure against."""
    if a.get("piece"):
        return a["piece"]
    return a["name"].rsplit("__", 1)[0]


def _overlaps(a, b):
    return (a["x"] < b["x"] + b["dx"] - 1e-9 and b["x"] < a["x"] + a["dx"] - 1e-9
            and a["y"] < b["y"] + b["dy"] - 1e-9 and b["y"] < a["y"] + a["dy"] - 1e-9)


def rail_clearances(rail, siblings):
    """(clear_depth, clear_drop) for one rail, DERIVED from its own piece's other parts.

    clear_depth = the cross-axis span of the shelf that caps this bay (a shelf runs the
    full carcass depth, so it IS the honest measure of how wide a shoulder may be).
    clear_drop  = from the rail down to the top of the nearest thing under it — the rail
    below on a double-hang, a shelf, or the plinth — never a guessed floor.

    Both are derivations, and both RAISE when the geometry cannot supply them. A guessed
    clearance is how a 1400mm dress ends up passing through the shelf beneath it."""
    axis, (lo, hi) = _long_axis(rail)
    cross = "y" if axis == "x" else "x"
    below = [s for s in siblings
             if s is not rail and _overlaps(rail, s) and s["z"] + s["dz"] <= rail["z"] + 1e-9]
    if not below:
        _fail(f"rail {rail['name']!r}: nothing built beneath it — the clear drop cannot be "
              f"derived, and a guessed floor is how garments end up through a shelf")
    floor_z = max(s["z"] + s["dz"] for s in below)
    clear_drop = (rail["z"] + rail["dz"] * 0.5) - floor_z

    caps = [s for s in siblings
            if s is not rail and "shelf" in s["name"].rsplit("__", 1)[-1]
            and _overlaps(rail, s)]
    if caps:
        clear_depth = min(c["d" + cross] for c in caps)
    else:
        # no shelf caps this bay: fall back to the deepest sibling that overlaps in the
        # RUN axis (a gable or the carcass back), which still measures real built joinery.
        runners = [s for s in siblings
                   if s is not rail and s["z"] < rail["z"] < s["z"] + s["dz"] + 1e-9]
        if not runners:
            _fail(f"rail {rail['name']!r}: no shelf or gable to measure the bay depth from")
        clear_depth = max(s["d" + cross] for s in runners)
    if clear_drop <= 0.05 or clear_depth <= 0.05:
        _fail(f"rail {rail['name']!r}: derived clearances are degenerate "
              f"(depth {clear_depth * 1000:.0f}mm, drop {clear_drop * 1000:.0f}mm)")
    return clear_depth, clear_drop


def dress_rails(anchors, min_rails=1):
    """Every rail in `anchors`, filled with garments derived from its own piece.

    RAISES if no rail is found at all: element 7's DD promised "satin-brass hang rails
    with garments" and material_presets still tells the beauty pass they are there, so a
    silent zero here is the exact revert-by-omission this element was written to end."""
    rails = find(anchors, "rail", required=False)
    if len(rails) < min_rails:
        _fail(f"expected at least {min_rails} hang rail(s) among {len(anchors)} built "
              f"parts, found {len(rails)} — the decided garments have nothing to hang on")
    by_piece = {}
    for a in anchors:
        by_piece.setdefault(piece_of(a), []).append(a)
    out = []
    for i, r in enumerate(rails):
        depth, drop_clear = rail_clearances(r, by_piece[piece_of(r)])
        # a rail with over ~1.2m of air below it is a FULL hang (dresses/coats); a rail
        # sitting over another rail or a shelf is a short hang. Derived, not declared.
        drop = FULL_DROP if drop_clear > 1.25 else SHORT_DROP
        out.extend(garments_on_rail(r, drop, depth, drop_clear, salt=i))
    return out


KNIT_KINDS = frozenset({"wardrobe", "closet"})


def dress_shelves(anchors, every=2, n_items=4, kinds=KNIT_KINDS):
    """Folded knit stacks on open WARDROBE shelves — one dressed shelf in every `every`,
    so the joinery still reads as joinery and one bay per mass is left bare.

    KIND-GATED. The first cut matched every anchor whose part token began with "shelf",
    and the pre-commit review caught what that put in the hero frame: the west display
    bookshelf — element 2's signed open oak-on-cool shelf with no back, whose whole job is
    that the garden reads THROUGH it — received 4 stacks of folded knits. Folded clothes on
    a living-room display shelf is not a styling density question, it is the wrong object
    in the wrong room. A shelf's HOST tells you what belongs on it, so the host kind rides
    the anchor and this lane refuses anything that is not wardrobe-family.

    `every=2` is a DENSITY choice, not a measurement: the vault has no objects-per-shelf
    row (a named GAP), so it is declared here rather than dressed up as derived."""
    shelves = [a for a in find(anchors, "shelf", required=False)
               if str(a.get("kind", "")) in kinds]
    out = []
    for i, sh in enumerate(shelves):
        if i % every:
            continue
        if sh["dx"] < 0.20 or sh["dy"] < 0.20:
            continue                                  # too small to hold a folded stack
        out.extend(stack_on_shelf(sh, n=n_items, salt=i))
    return out


# ---------------------------------------------------------------------------
# GARMENTS — the largest gap between decided design and rendered pixels.
# ---------------------------------------------------------------------------

def garments_on_rail(rail, drop, clear_depth, clear_drop, salt=0, pitch=GARMENT_PITCH):
    """Fill one brass hang rail with hanging garments + their hangers.

    Position, count, shoulder span and length ALL derive from the rail anchor and the
    host carcass: the run gives the count, the rail's own cross-centreline gives where the
    shoulders sit, the rail top gives the shoulder height, `clear_depth` (the host shelf's
    own span) bounds the shoulder, and `clear_drop` (rail z minus whatever obstructs
    below) bounds the hem. Nothing here is a coordinate.

    `clear_drop` is a hard bound, not a hint: a 1400mm dress on a rail with 1100mm of air
    below it does not "look a bit long", it passes through the shelf under it. RAISE.

    Garments vary in span, drop and lean by a bounded deterministic deviation, because the
    vault's own amateur red flag is "placing identical, repeating 3D assets across a
    scene" — instancing one garment 30 times would ADD the CAD tell this element removes.
    """
    axis, (lo, hi) = _long_axis(rail)
    run = hi - lo
    n = int(run // pitch)
    if n < MIN_GARMENTS:
        _fail(f"rail {rail['name']!r}: run {run * 1000:.0f}mm fits only {n} garments at "
              f"{pitch * 1000:.0f}mm pitch — below MIN_GARMENTS ({MIN_GARMENTS}) a rail "
              f"reads as a bare towel bar, which is the defect being fixed")
    # The DROP BUDGET is not just the garment body: the shoulder hangs SHOULDER_DROP below
    # the rail and the hem wanders another GARMENT_HEM below its nominal. A budget that
    # ignores what the generator adds is not a budget — this is the second of the two
    # containment bugs this module's own tests caught.
    drop_budget = clear_drop - SHOULDER_DROP - GARMENT_HEM
    if drop > drop_budget + 1e-9:
        _fail(f"rail {rail['name']!r}: declared drop {drop * 1000:.0f}mm exceeds the "
              f"derived budget {drop_budget * 1000:.0f}mm (clear "
              f"{clear_drop * 1000:.0f}mm less the {SHOULDER_DROP * 1000:.0f}mm shoulder "
              f"hang and {GARMENT_HEM * 1000:.0f}mm hem wander) — the garments would pass "
              f"through the obstruction below. Re-choose the census, never clamp it")
    # A garment's real span is wider than its nominal `width` (the body flares and the
    # piece leans), so the containment bound is solved on the ACTUAL span, using the
    # factor softgoods publishes — not on the nominal, which would overhang the carcass
    # by ~34mm per side and read as clothes growing through a gable.
    SWAY = 0.010
    max_span = clear_depth * 0.92
    shoulder = min(SHOULDER_MAX, (max_span - 2 * SWAY) / sg.GARMENT_FLARE)
    if shoulder < 0.24:
        _fail(f"rail {rail['name']!r}: host clear depth {clear_depth * 1000:.0f}mm leaves "
              f"only a {shoulder * 1000:.0f}mm shoulder — not a hangable bay")
    # centre the file of garments on the rail, and hang them from just under it
    span = (n - 1) * pitch
    start = lo + (run - span) * 0.5
    cross = ("y" if axis == "x" else "x")
    c_ctr = rail[cross] + rail["d" + cross] * 0.5
    z_top = rail["z"] + rail["dz"] * 0.5

    parts = []
    for i in range(n):
        s = salt * 97 + i
        along = start + i * pitch
        # bounded per-garment variation: shoulder span, drop, and a small lean along the
        # rail. THICKNESS (the rail-axis extent) stays strictly under the pitch so no two
        # neighbours can interpenetrate — the blocker this signature exists to prevent.
        # variation SUBTRACTS only: `shoulder` is a containment bound derived from the
        # host's clear depth, so a +10% swing would put the widest garment outside the
        # carcass it hangs in. A bound that the variation can exceed is not a bound.
        wid = shoulder * (1.0 - 0.16 * abs(sg.dev(i, 1.0, s)))
        # THICKNESS BUDGET: the pitch has to hold the shell, its crease on BOTH sides, and
        # the lean. Sizing thickness against the raw pitch is what let neighbours overlap
        # by 0.6mm — small, but it is cloth growing through cloth.
        thk_max = pitch - 2 * GARMENT_FOLD - 2 * GARMENT_LEAN
        if thk_max <= 0.012:
            _fail(f"rail {rail['name']!r}: pitch {pitch * 1000:.0f}mm cannot hold a "
                  f"garment plus its crease and lean")
        thk = thk_max * (0.72 + 0.28 * abs(sg.dev(i, 1.0, s + 7)))
        drp = min(drop * (1.0 + sg.dev(i, 0.13, s + 11)), drop_budget)   # raggeder hem
        lean = sg.dev(i, GARMENT_LEAN, s + 23)
        # A THREE-VALUE LADDER from three ALREADY-SIGNED identities: mostly greige linen,
        # the element-6 terry for the occasional robe, and every third mass in matte-black
        # ply. Across six frames there is essentially nothing below 35% luminance, and a
        # wardrobe is the one place dark clothes legitimately live — D1-A governs OAK
        # share, not value, so this adds the missing dark anchor without touching it.
        tok = (TOK_INK if i % 3 == 1 else TOK_TERRY if i % 5 == 2 else TOK_LINEN)

        gv, gf = sg.garment(wid, drp, depth=thk, fold=GARMENT_FOLD,
                            hem_wander=GARMENT_HEM, sway=SWAY, salt=s)
        # the hanger's arms angle down by the SAME slope this garment's shoulders
        # wear (one published stream) — a straight bar under sloped cloth hangs the
        # cloth below the wire that suspends it (pre-commit review, 40/40 salts)
        hv, hf = sg.hanger(wid * 0.82, salt=s, arm_drop=sg.garment_slope(drp, s))
        # THE ORIENTATION: the generator authors its shoulder span along local +x, so the
        # piece is rotated whenever that span would land ALONG the rail. Shoulder must lie
        # on the CROSS axis; thickness on the rail axis.
        cross_is_y = (axis == "x")
        if axis == "x":
            ox, oy = along + lean, c_ctr
        else:
            ox, oy = c_ctr, along + lean
        # garment local origin is its top-centre; hanger local origin is the rail centre
        gs = SHOULDER_DROP                          # shoulder sits below the hanger bar
        parts.append({
            "name": f"mill__style_garment{salt}_{i}__{tok}", "shape": "mesh",
            "verts": _xlate(gv, ox, oy, z_top - gs, swap=cross_is_y), "faces": gf,
        })
        parts.append({
            # hangers are METAL, and matte_black_ply is a joinery BACKER identity carrying
            # too much already — route them to element 5's black-anodised aluminium, which
            # is a metal, is already routed, and needs no new row (critic's amendment).
            "name": f"mill__style_hanger{salt}_{i}__blackalu", "shape": "mesh",
            "verts": _xlate(hv, ox, oy, z_top, swap=cross_is_y), "faces": hf,
        })
    return parts


def _xlate(verts, ox, oy, oz, swap=False):
    """Translate local verts to absolute. `swap` rotates the piece 90 deg about z so a
    generator authored along +x serves a rail whose CROSS axis is y."""
    if swap:
        return [(ox - v[1], oy + v[0], oz + v[2]) for v in verts]
    return [(ox + v[0], oy + v[1], oz + v[2]) for v in verts]


# ---------------------------------------------------------------------------
# FOLDED STACKS — what fills an open shelf.
# ---------------------------------------------------------------------------

def stack_on_shelf(shelf, n=4, item_h=0.042, salt=0, frac_w=0.46, frac_d=0.62):
    """A stack of folded knits sitting ON a shelf, sized as a FRACTION of the shelf's own
    clear span so it can never overhang, and pushed toward the shelf's front half where a
    real folded pile sits (and where the camera can see it)."""
    if not 0.0 < frac_w <= 1.0 or not 0.0 < frac_d <= 1.0:
        _fail(f"stack_on_shelf: fractions must be in (0,1] — got {frac_w}, {frac_d}")
    w = shelf["dx"] * frac_w
    d = shelf["dy"] * frac_d
    x0 = shelf["x"] + (shelf["dx"] - w) * 0.5 + sg.dev(salt, shelf["dx"] * 0.10, salt)
    y0 = shelf["y"] + (shelf["dy"] - d) * 0.5
    z0 = shelf["z"] + shelf["dz"]                   # ON the shelf, never inside it
    parts = []
    for k, (ox, oy, oz, dx, dy, dz) in enumerate(
            sg.folded_stack(w, d, n, item_h, salt=salt)):
        tok = TOK_TERRY if k % 2 == 0 else TOK_LINEN
        parts.append({
            "name": f"mill__style_fold{salt}_{k}__{tok}", "shape": "box",
            "x": x0 + ox, "y": y0 + oy, "z": z0 + oz,
            "dx": dx, "dy": dy, "dz": dz, "bevel": 0.008,
        })
    return parts


# ---------------------------------------------------------------------------
# BED — the biggest single area in both frames the owner judges from.
# ---------------------------------------------------------------------------

DRAPE_FOLD = 0.030         # crease amplitude at the free hem. 18mm was TOO SHALLOW to
#                            read: at a 108mm fold pitch that is a depth/pitch ratio of
#                            0.17, and head-on under this suite's broad soft sources it
#                            rendered as a flat plane with a wavy bottom edge. Real
#                            drapery gathers at ~0.3-0.5; 30mm/108mm = 0.28.
DRAPE_REVEAL = 0.020       # air left under the hem, above whatever it falls toward
DRAPE_HEM = 0.016          # hem wander, spent out of the reveal budget
DRAPE_SAG = 0.010          # mid-run sag, ALSO spent out of it (missed on the first cut:
#                            a budget that omits one of the generator's own terms is not a
#                            budget, and the reveal came out at 11mm instead of 20mm)


RANK_GAP = 0.020           # air between pillow ranks — a stack, not a wedge
SHAM_D = 0.115             # a euro sham standing upright is THIN in plan
PILLOW_D = 0.340           # a sleeping pillow lying flat
LUMBAR_D = 0.200

# Rank HEIGHTS (2026-07-28, the pebble fix's other half). The heights used to be inline
# literals — sham 0.235, pillow 0.135, lumbar 0.155 — and two of the three contradicted
# the design they were built from. The DD's own words are "upright euro shams STANDING
# against the slat wall": a 235mm-tall band on a 700mm width is a sham lying down, and it
# is why the back rank rendered as low domes instead of the hotel-style standing squares
# that anchor a styled bed. A real euro sham is a 650mm square; leaning upright it
# presents ~0.45m. And the LUMBAR sat taller than the sleeping pillows (155 vs 135), so
# the "three heights" ladder was really tall-short-mid — the accent outgrew the rank
# behind it. Now: shams clearly TALLEST (the DD's word made true), pillows plump middle,
# lumbar the SMALLEST — an accent, not a third pillow.
SHAM_H = 0.44              # standing height. Width rides SHAM_W: the first standing cut
#                            used 0.62 and the pair read as two AIRPLANE HEADRESTS — tall,
#                            narrow, floating with 0.42 m of bare bed on each flank. A KING
#                            sham is a 500x900 case; 0.80 x 0.44 upright IS that object,
#                            and two of them span 1.66 of the 2.15 m width the way styled
#                            bedding actually does.
SHAM_W = 0.80              # cap; the across-fraction still governs on a narrow bed
PILLOW_H = 0.15            # a plump sleeping pillow lying flat
LUMBAR_H = 0.19            # tall enough to CLEAR the duvet's turned-back fold. At 0.13 the
#                            accent vanished: the fold band (top ~0.75 above plan) fully
#                            occluded it from the foot camera, so the "breaks the mirror
#                            symmetry" piece was breaking nothing. 0.19 peeks ~90 mm above
#                            the fold's ridge in silhouette.
LUMBAR_T = 0.16            # the cushion's own thickness — less than its 0.20 rank, so it
#                            sits tight against the pillow row like a propped lumbar does


def head_ranks(along):
    """The bed head as THREE ranks, returned as [(from_head, depth), ...] plus the total.

    THIS IS A RE-DERIVATION, NOT AN ADDITION. Both DD critics ran the real numbers and
    found the same blocker: the bed's head edge lands at x5204 and BF14's slat face at
    x5203, so the head is FLUSH with the wall — there is no space BEHIND the existing
    pillows to stand shams in. The ranks therefore replace the old two-slab pillow zone
    rather than sitting behind it, and the zone's total depth is returned so the duvet
    start re-derives from it (build_room's `dv_from = pz + 0.14`). Element 3's pillow zone
    is amended in the same commit — a derivation that lives in two places drifts."""
    ranks = []
    at = 0.020                                     # a hair off the headboard wall
    for d in (SHAM_D, PILLOW_D, LUMBAR_D):
        ranks.append((at, d))
        at += d + RANK_GAP
    total = at - RANK_GAP
    if total > along * 0.60:
        _fail(f"head_ranks: the three ranks need {total * 1000:.0f}mm of a "
              f"{along * 1000:.0f}mm bed — over 60% of the mattress would be pillow. "
              f"Re-choose the census, never silently drop a rank")
    return ranks, total


def pillow_bank(coverlet, head_axis, head_sign, salt=0):
    """Three pillow HEIGHTS at the bed head — upright euro shams against the slat wall,
    flat sleeping pillows in front of them, one accent lumbar in a contrasting TEXTURE.

    (2026-07-23: this line used to end "one accent lumbar in the deepest value". Measured,
    the lumbar was the seventh lightest of the twelve pieces the bed group measures as.
    See the [3] block.)

    Three heights is the single most recognisable signal of a styled bed versus a made
    one; the build currently emits two identical flat slabs at identical height, which the
    ground phase named as the loudest CAD tell in the hero frame. Every dimension derives
    from the coverlet's own span, and the ranks never overlap (head_ranks owns that)."""
    if head_axis not in ("x", "y"):
        _fail(f"pillow_bank: head_axis {head_axis!r} must be 'x' or 'y'")
    if head_sign not in (1, -1):
        _fail(f"pillow_bank: head_sign {head_sign!r} must be +1 or -1")
    along = coverlet["dx"] if head_axis == "x" else coverlet["dy"]
    across = coverlet["dy"] if head_axis == "x" else coverlet["dx"]
    z_top = coverlet["z"] + coverlet["dz"]
    ranks, _total = head_ranks(along)

    def place(from_head, across_off, a_size, c_size):
        """(x, y, dx, dy) for a piece `from_head` back from the head edge."""
        if head_axis == "x":
            x = (coverlet["x"] + coverlet["dx"] - from_head - a_size) if head_sign > 0 \
                else (coverlet["x"] + from_head)
            return x, coverlet["y"] + across_off, a_size, c_size
        y = (coverlet["y"] + coverlet["dy"] - from_head - a_size) if head_sign > 0 \
            else (coverlet["y"] + from_head)
        return coverlet["x"] + across_off, y, c_size, a_size

    parts = []
    gap = across * 0.030
    # [1] two KING SHAMS standing upright against the headboard wall — the tallest rank.
    # pinch 0.30 (was 0.42): a king sham's case is sewn square-cornered; the heavier pinch
    # rounded the tops into the headrest read.
    (sh_from, sh_d), (pl_from, pl_d), (lb_from, lb_d) = ranks
    sham = min(across * 0.40, SHAM_W)
    for i in range(2):
        off = (across - 2 * sham - gap) * 0.5 + i * (sham + gap)
        x, y, dx, dy = place(sh_from, off, sh_d, sham)
        v, f = sg.cushion(dx, dy, SHAM_H, pinch=0.30, salt=salt + i)
        parts.append({"name": f"bed__sham{i}", "shape": "mesh",
                      "verts": [(x + p[0], y + p[1], z_top + p[2]) for p in v], "faces": f})
    # [2] two flat SLEEPING pillows in front of them. NO dent: this owner's two prior
    # rejections were both of things he read as BROKEN rather than ugly, and a pressed
    # pillow is exactly the cue an engineer reads as a modelling error (DD kill list).
    pw = min(across * 0.40, 0.66)
    for i in range(2):
        off = (across - 2 * pw - gap) * 0.5 + i * (pw + gap)
        x, y, dx, dy = place(pl_from, off, pl_d, pw)
        v, f = sg.cushion(dx, dy, PILLOW_H, pinch=0.30, salt=salt + 5 + i)
        parts.append({"name": f"bed__pillowsoft{i}", "shape": "mesh",
                      "verts": [(x + p[0], y + p[1], z_top + p[2]) for p in v], "faces": f})
    # [3] ONE accent lumbar, off-centre, in the greige-oatmeal TERRY identity — a real
    # signed textile with character, not a joinery ply pretending to be a cushion (the
    # critic's amendment to the `ink` overload). It breaks the mirror symmetry, and its
    # accent is TEXTURE and POSITION, not value.
    # 2026-07-23 — this comment used to claim it was "the hero frame's darkest object above
    # the plinth". Measured: 188.6, the SEVENTH lightest of the twelve pieces the bed group
    # measures as (the ten bed__ parts + the bench seat + this cushion), with
    # the throw (155.1), the coverlet (164.8) and the bench (178.2) all below it. Terry is
    # element 6's signed cloth and is shared with the ensuite towels, robes and mat, so it
    # is deliberately NOT re-valued here — re-tinting it to make an old sentence true would
    # repaint four other pieces in another room. The sentence goes instead.
    lw = min(across * 0.34, 0.52)
    loff = (across - lw) * 0.5 + sg.dev(salt, across * 0.06, salt + 3)
    # LUMBAR_T < the rank depth: placed at the rank's head-side edge, so it sits tight
    # against the pillow row (a lumbar is propped against what is behind it, it does not
    # float mid-bed).
    x, y, dx, dy = place(lb_from, loff, min(lb_d, LUMBAR_T), lw)
    v, f = sg.cushion(dx, dy, LUMBAR_H, pinch=0.55, salt=salt + 9)
    parts.append({"name": f"mill__style_lumbar__{TOK_TERRY}", "shape": "mesh",
                  "verts": [(x + p[0], y + p[1], z_top + p[2]) for p in v], "faces": f})
    return parts


THROW_SKEW = 0.05          # how far the throw's hem line departs from parallel
THROW_SWING = 0.14         # how far the falling tail swings outward per metre of fall
THROW_RIPPLE = 0.016       # softgoods.throw's own default crease amplitude
THROW_FOLD_K = 1.9         # its out-of-plane gain at the free hem (softgoods.throw tail)


THROW_INSET = 0.18         # coverlet shoulder left showing on each side of the throw


def foot_throw(along, across, height, base_top):
    """(band, hang) for the simulated foot throw, or None if this bed cannot carry one.

    PURE, and it is the SAME predicate `_build_bed` uses, for one reason: the anti-repaint
    armour has to state whether a throw exists, and the first cut of that gate consulted
    the BAKED coverlet's measured width — which no pure re-run can see. A story bit that
    cannot re-derive its own subject either goes silent (dropping armour off a piece that
    was built) or asserts blind. The positioning still measures the baked coverlet; only
    the EXISTENCE question was moved back to something both sides can compute.

    band  what lies ON the bed.
    hang  the CANTILEVER CUT past the bed's plan foot line — NOT the visible fall. The
          throw folds over at the mattress edge, ~0.09 m inboard of the plan line, so
          roughly the first 0.10 m of `hang` is spent crossing that inset horizontally
          and only the remainder becomes vertical drop. Discovered the hard way
          (2026-07-28): a resize that read `hang` as "visible fall" and cut it to 0.18
          left ~0.08 of true drop — a stubby flap with no weight, which BOWED outward
          and failed the containment ladder at every slack (edge 1-28 mm proud on x).
          The bake caught it, loudly, exactly as designed.

    2026-07-28 RESIZE (owner LOOK on the tonal-ladder renders): the visible defect was
    the BAND, not the hang. At the old formula the band bottomed out at 0.72 m — 36% of a
    2.0 m bed, and measured in pixels the throw was 8.7% of the hero frame and 15.3% of
    bed_hero, the LARGEST single object in both. A throw that outweighs the coverlet it
    decorates is a second coverlet, and its long straight hem read as a defect. Now
    0.50 m on this bed (25%) with the hang kept at the value whose physics is proven.

    THE 2.2x BAND:HANG FLOOR IS RETIRED, and the reason is recorded rather than deleted:
    it was measured on an UNPINNED sheet ("0.30 m of cloth in mid-air against a 0.50 m
    band ... fell 5.1 m through the floor"). The build has since pinned the throw's
    innermost strip the way a tucked edge really is, so the pin — not the band's weight —
    is what holds the sheet, and the bake still fails the build loudly (hem_min,
    containment, frozen-sheet) if that ever stops being true. Keeping the floor would
    force band back to 0.62+ and reinstate the defect this resize removes.
    """
    hang = min(0.28, (height - base_top) - DRAPE_REVEAL - 0.06)
    band = min(0.50, along * 0.25)
    _ranks, pz = head_ranks(along)
    if hang <= 0.05 or (along - band) <= pz + 0.14:
        return None                      # the throw would reach into the pillow ladder
    if across <= 2 * THROW_INSET + 0.3:
        return None                      # too narrow to leave a coverlet shoulder showing
    return band, hang


def book_stack(x, y, z, n=3, w=0.215, d=0.155, salt=0):
    """A leaning stack of books. Boards are oak-family, so a stack reads as a warm dark
    block — the cheapest value anchor available inside the closed palette."""
    if n <= 0:
        _fail(f"book_stack: n must be >= 1 (got {n})")
    parts = []
    zz = z
    for k in range(n):
        h = 0.030 - k * 0.002
        sw = w - k * 0.011
        sd = d - k * 0.008
        parts.append({
            "name": f"mill__style_book{salt}_{k}__{TOK_INK if k % 2 else TOK_OAK}",
            "shape": "box",
            "x": x + sg.dev(k, 0.011, salt), "y": y + sg.dev(k, 0.009, salt + 4),
            "z": zz, "dx": sw, "dy": sd, "dz": h, "bevel": 0.004,
        })
        zz += h
    return parts


def vessel(x, y, z, r=0.055, h=0.185, tok=TOK_PORCELAIN, salt=0, name="vessel"):
    """A turned vessel (vase / carafe / tumbler) as a tapered profile of revolution — a
    curved silhouette among orthogonal boxes, which is what the ground phase asked for
    when it said every object in every frame is axis-aligned."""
    if r <= 0 or h <= 0:
        _fail(f"vessel: degenerate r={r} h={h}")
    nu, nv = 14, 8
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)
        # a soft shoulder: full at 1/3 height, drawing in toward the lip
        rr = r * (0.62 + 0.38 * math.sin(math.pi * min(v * 1.35, 1.0)) ** 0.7)
        for i in range(nu + 1):
            a = 2.0 * math.pi * i / float(nu)
            verts.append((x + rr * math.cos(a), y + rr * math.sin(a), z + h * v))
    # `porcelain` is a FIXTURE role, not a mill token: mill_object_role has no branch
    # for it and the name would fall through to the oak default. Sanitaryware goes
    # through fix__, which is the channel FIXTURE_MAT_OBJECT already documents.
    return [{"name": f"fix__style_{name}{salt}", "shape": "mesh",
             "verts": verts, "faces": sg._loft_faces(nv, nu)}]


def tray(x, y, z, w=0.32, d=0.22, tok=TOK_BRASS, salt=0):
    """A shallow tray: the styling device that turns loose objects into a composed group,
    and (in brass) the suite's accent metal at eye level."""
    t = 0.010
    return [
        {"name": f"mill__style_tray{salt}__{tok}", "shape": "box",
         "x": x, "y": y, "z": z, "dx": w, "dy": d, "dz": t, "bevel": 0.004},
        {"name": f"mill__style_trayrim{salt}a__{tok}", "shape": "box",
         "x": x, "y": y, "z": z, "dx": w, "dy": 0.008, "dz": 0.022, "bevel": 0.003},
        {"name": f"mill__style_trayrim{salt}b__{tok}", "shape": "box",
         "x": x, "y": y + d - 0.008, "z": z, "dx": w, "dy": 0.008, "dz": 0.022,
         "bevel": 0.003},
    ]
