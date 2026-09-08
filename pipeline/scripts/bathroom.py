"""bathroom.py -- ensuite sanitaryware + wet-zone geometry as PURE data (no bpy).

LAYER LAW (pipeline/CLAUDE.md): "dimensional correctness is a CONSTRAINT problem, not
a Blender problem" -- this module emits box PARTS (plan-mm) that build_room._add_ensuite
materializes; it never imports bpy and stays runnable under plain python (unit-tested).

Each part is a dict {name,x,y,z,dx,dy,dz,mat}; `mat` is a ROLE the consumer maps to the
DD's 60-30-10 palette (element4-ensuite_DD-2026-07-18.md):
  porcelain  cool white sanitaryware (the ~60% cool ground reads through it)
  stone      cool-grey Caesarstone counter / tub deck  (suite-consistent)
  oak        the ONE warm light-oak vanity body        (the lone ~30% gesture, D1-A)
  brass      satin-brass tapware/fittings              (the ~10% accent)
  glass      frameless clear glass                      (shower screen + wet/dry partition)
  tray       shower tray/tile                           (cool ground, slip-rated [GAP])
  blackalu   black-alu luminaire body (element-5 task bar, coheres w/ window frames)
  opal       luminous opal diffuser face (element-5; consumer renders it EMISSIVE)
  towel      element-6 greige-oatmeal terry — ONE shared token for towels AND the
             bath mat (D-E6-3: two tokens double the router work; decided)

Footprints are the OWNER-AUTHORED ink (element4-ensuite_ink-read-2026-07-18.json); this
module only MASSES them for a structural decision-instrument render (the Gemini beauty
pass refines the rounded sanitaryware forms). Fixture origin convention matches
build_room.add_box: (x,y) = the SW/min corner, dx=E-W, dy=N-S, dz from z upward, all mm.
"""

# --- massing constants (mm) — render-tier proportions, not construction dims -----------
COUNTER_THK = 40.0      # stone counter slab
TOE_KICK_H  = 90.0      # recess under the vanity cabinet
BASIN_W     = 480.0     # vessel basin footprint (E-W)
BASIN_D     = 360.0     # vessel basin footprint (N-S)
BASIN_RIM_H = 120.0     # vessel basin above the counter
FAUCET      = 45.0      # brass tap post section
FAUCET_H    = 240.0
TUB_WALL    = 110.0     # tub apron / shell wall thickness
TUB_FLOOR   = 110.0
CURB_H      = 110.0     # low shower curb
CURB_T      = 90.0
GLASS_T     = 12.0      # frameless panel thickness
GLASS_H     = 2000.0    # shower screen / partition height (below the 2800 ceiling)
TRAY_H      = 40.0
HEAD_Z      = 2150.0    # showerhead mounting height


def _box(name, x, y, z, dx, dy, dz, mat):
    assert dx > 0 and dy > 0 and dz > 0, f"{name}: zero/negative box {dx}x{dy}x{dz}"
    return {"name": name, "x": float(x), "y": float(y), "z": float(z),
            "dx": float(dx), "dy": float(dy), "dz": float(dz), "mat": mat}


def _f(fx, k, default=None):
    v = fx.get(k, default)
    if v is None:
        raise ValueError(f"bathroom: fixture {fx.get('name','?')} missing '{k}'")
    return float(v)


LEDGE_D = 260.0     # shallow stone ledge where the counter runs over the WC (west)
MIRROR_SILL = 1100.0   # mirror bottom AFF (above the 850 counter + backsplash) [est]
MIRROR_H    = 1000.0   # mirror field height [est]
MIRROR_T    = 25.0
# ELEMENT 5 (D-E5-5, element5-lighting_DD-2026-07-20.md §5): the task BAR above the
# mirror — black-alu body + opal luminous face, NO brass (keeps mass off the mirror
# plane, D-E4-2). Lives HERE beside the mirror constants so one nudge of
# MIRROR_SILL/MIRROR_H moves mirror AND bar together (derive-not-entrench).
BAR_REVEAL = 10.0   # gap above the mirror top [est]
BAR_H      = 40.0   # bar profile height [est]
BAR_D      = 50.0   # bar projection off the wall [est]; the north ~40% is the opal face


def vanity_parts(fx, taskbar=False):
    """Double-basin vanity. fx (x,y,w,d,h) = the DEEP oak cabinet footprint (the east
    ~2047 mm of the ink run, x1077->3124), NOT the whole 3.05 m counter — the west ~1000
    mm is a SHALLOW stone ledge over the WC cistern (critique 2026-07-18: a solid cabinet
    the full 3047 would build straight through the SW WC). Emits: oak cabinet (the lone
    warm-oak gesture, held to the 850 mm-low body) + a stone counter spanning the full
    `design.counter_x0_mm..+counter_len_mm` run + a shallow west ledge over the WC + 2
    vessel basins + 2 brass taps. Basin centres from design.basin_ctr_x_mm (ink)."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D, H = _f(fx, "w"), _f(fx, "d"), _f(fx, "h")
    dz = fx.get("design", {}) or {}
    cx0 = float(dz.get("counter_x0_mm", x0))            # counter west start (may run over WC)
    clen = float(dz.get("counter_len_mm", W))           # full counter run (the '3.05')
    nm = "vanity"
    parts = [
        # oak cabinet body (toe-kick recessed) — the single warm-oak gesture, LOW (850)
        _box(f"{nm}_cabinet", x0 + 30, y0, TOE_KICK_H, W - 60, D - 40, H - COUNTER_THK - TOE_KICK_H, "oak"),
        # cool-grey Caesarstone counter slab over the cabinet, slight front overhang
        _box(f"{nm}_counter", x0, y0 - 20, H - COUNTER_THK, W, D + 20, COUNTER_THK, "stone"),
    ]
    # the counter continues WEST as a shallow ledge over the WC (no cabinet below it)
    if cx0 < x0 - 1.0:
        parts.append(_box(f"{nm}_ledge", cx0, y0, H - COUNTER_THK, x0 - cx0, LEDGE_D, COUNTER_THK, "stone"))
    ctrs = dz.get("basin_ctr_x_mm") or [x0 + W * 0.25, x0 + W * 0.75]
    ymid = y0 + D * 0.5
    for i, cx in enumerate(ctrs):
        parts.append(_box(f"{nm}_basin{i}", cx - BASIN_W / 2, ymid - BASIN_D / 2, H,
                          BASIN_W, BASIN_D, BASIN_RIM_H, "porcelain"))
        parts.append(_box(f"{nm}_tap{i}", cx - FAUCET / 2, y0 + 60, H,
                          FAUCET, FAUCET, FAUCET_H, "brass"))
    # full-width frameless mirror on the wall above the counter, over the basins (D-E4-2). A
    # DECIDED element, so it is BUILT here with a consumer — never left to a note that a render
    # or the Gemini polish silently drops (the revert-by-omission trap that has recurred 5x).
    parts.append(_box(f"{nm}_mirror", x0, y0 - MIRROR_T, MIRROR_SILL, W, MIRROR_T, MIRROR_H, "mirror"))
    # ELEMENT 5 (D-E5-5): the task BAR above the mirror — mirror-width, black-alu body
    # against the wall + the opal luminous face on the room side. The wash LIGHT itself is
    # emitted by element5_lighting.ensuite_bar_wash from these same constants. GATED on
    # `taskbar` (the consumer passes element5_lighting.applies(spec)) — scrutiny
    # 2026-07-21: un-gated, every future NON-e5 bathroom spec grew an emissive bar,
    # bypassing the schema opt-in the whole element rides on.
    if taskbar:
        bar_z = MIRROR_SILL + MIRROR_H + BAR_REVEAL
        body_d = BAR_D * 0.6
        parts.append(_box(f"{nm}_taskbar_body", x0, y0 - MIRROR_T, bar_z, W, body_d, BAR_H, "blackalu"))
        parts.append(_box(f"{nm}_taskbar_opal", x0, y0 - MIRROR_T + body_d, bar_z,
                          W, BAR_D - body_d, BAR_H, "opal"))
    return parts


def toilet_parts(fx):
    """WC in the SW: cistern against the west wall (x0), bowl projecting EAST, seat on top.
    fx.w = E-W projection, fx.d = N-S width."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D, H = _f(fx, "w"), _f(fx, "d"), _f(fx, "h")
    nm = "wc"
    tank_w = 200.0
    bowl_x = x0 + tank_w - 10
    bowl_w = W - tank_w + 10
    return [
        _box(f"{nm}_tank", x0, y0 + D * 0.08, 0, tank_w, D * 0.84, max(H, 760), "porcelain"),
        _box(f"{nm}_bowl", bowl_x, y0 + D * 0.12, 0, bowl_w, D * 0.76, 400, "porcelain"),
        _box(f"{nm}_seat", bowl_x, y0 + D * 0.12, 400, bowl_w, D * 0.76, 40, "porcelain"),
    ]


def bathtub_parts(fx):
    """Deck bathtub on the north wall: a porcelain shell (4 apron walls + floor = an open
    recess) + a thin cool-stone deck cap on the rim + a brass deck filler at the back."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D, H = _f(fx, "w"), _f(fx, "d"), _f(fx, "h")
    nm = "tub"
    t = TUB_WALL
    parts = [
        _box(f"{nm}_apron_s", x0, y0, 0, W, t, H, "porcelain"),
        _box(f"{nm}_apron_n", x0, y0 + D - t, 0, W, t, H, "porcelain"),
        _box(f"{nm}_apron_w", x0, y0, 0, t, D, H, "porcelain"),
        _box(f"{nm}_apron_e", x0 + W - t, y0, 0, t, D, H, "porcelain"),
        _box(f"{nm}_floor", x0 + t, y0 + t, 0, W - 2 * t, D - 2 * t, TUB_FLOOR, "porcelain"),
        # cool-stone deck rim cap on the apron tops (the "deck" of a deck tub)
        _box(f"{nm}_deck_s", x0 - 10, y0 - 10, H, W + 20, t + 20, 25, "stone"),
        _box(f"{nm}_deck_n", x0 - 10, y0 + D - t - 10, H, W + 20, t + 30, 25, "stone"),
        # brass deck filler at the north (back) edge, mid-run
        _box(f"{nm}_filler", x0 + W * 0.5 - 30, y0 + D - 70, H, 60, 60, 220, "brass"),
    ]
    return parts


SCREEN_FRAC = 0.55   # fixed-screen fraction of the shower's south face — CONVENTION tier.
                     # Shared by shower_parts AND shower_entry_gap so the element-6 mat
                     # centre DERIVES from the same constant the screen builds from: a
                     # screen nudge moves the mat with it, never strands it (D-E6-4).


def shower_entry_gap(fx):
    """The shower's south-face entry gap (screen east end -> shower east edge), mm.
    ELEMENT 6 (D-E6-4): the bath-mat centre must derive from the BUILT screen geometry,
    never a hardcoded x — the decided-data-through-swallows class."""
    x0, W = _f(fx, "x"), _f(fx, "w")
    return x0 + W * SCREEN_FRAC, x0 + W


def shower_parts(fx):
    """Glass shower NW: cool tray + a low curb on the south (entry) edge + a frameless
    fixed glass screen on part of the south face (entry gap left) + a brass head/arm."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D, H = _f(fx, "w"), _f(fx, "d"), _f(fx, "h")
    nm = "shower"
    screen_w = W * SCREEN_FRAC              # a fixed screen; the rest is the entry
    return [
        _box(f"{nm}_tray", x0, y0, 0, W, D, TRAY_H, "tray"),
        _box(f"{nm}_curb", x0, y0, 0, W, CURB_T, CURB_H, "tray"),
        _box(f"{nm}_screen", x0, y0, TRAY_H, screen_w, GLASS_T, GLASS_H, "glass"),
        # showerhead arm + head on the west/back wall, high
        _box(f"{nm}_head", x0 + 120, y0 + D - 140, HEAD_Z, 140, 140, 60, "brass"),
    ]


def glass_partition_parts(fx):
    """The wet/dry glass partition at x1125 (ink) dividing shower (W) from tub (E)."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D = _f(fx, "w"), _f(fx, "d")
    H = float(fx.get("h") or GLASS_H)
    return [_box("wet_partition", x0, y0, 0, max(W, GLASS_T), D, H, "glass")]


# --- ELEMENT 6 accessory constants (D-E6-3/-4, element6-textiles_DD-2026-07-21.md) -----
# Every AFF/size here is [est] RENDER-TIER: the vault carries NO towel-hardware mounting
# heights (e4 DD §7 [GAP]) and NO bath-linen data (the linen->terry family extension is
# an owned un-cited call). POSITIONS always DERIVE from the sibling fixtures/door —
# these constants only shape the massing (the MIRROR_SILL pattern: beside what they serve).
# The same [est] massing tier covers EVERY raw mm literal inside accessory_parts below
# (holder box dims, counter-towel folds, robe layering offsets, the fold-over 40) —
# none is a measured or vaulted value (scope review 2026-07-21).
BAR_AFF      = 1100.0   # towel bar rail centre AFF [est]
BAR_LEN      = 610.0    # K-14436-2MB 24in — the LOCKED Purist row; 457 (18in) fallback = spec data
BAR_STANDOFF = 65.0     # rail centreline off the wall [est] (no cut-sheet)
BAR_SECT     = 20.0     # post/rail square section [est]
HOOK_AFF     = 1650.0   # robe hook AFF [est]
HOOK_SECT    = 40.0
HOOK_JAMB_SETBACK = 350.0   # hook centre from its door jamb [est]
HOLDER_AFF   = 650.0    # paper holder (roll centre) AFF [est] — seated reach, below the bar line
HOLDER_N_OF_WC = 130.0  # holder centre north of the WC's north edge (the re-sited y~6640-6900 band)
TOWEL_DROP   = 350.0    # folded-over drop below the bar rail (clears the holder's top)
TOWEL_W      = 280.0    # bath towel width on the bar
TOWEL_THK    = 60.0     # draped thickness (both plies over the rail)
HAND_W       = 200.0
HAND_DROP    = 300.0
ROBE_W       = 300.0
ROBE_DROP    = 750.0    # bottom z900 — clears the tub deck cap (~585)
ROBE_THK     = 60.0
MAT_W        = 800.0    # E-W at the curb (D-E6-4 [est])
MAT_D        = 500.0    # N-S — lives inside the ~743 drawn dry strip
MAT_THK      = 20.0
MAT_CURB_GAP = 50.0     # mat north edge off the curb face

ACCESSORY_CENSUS_KEYS = ("bath_on_bar", "hand_on_south_hook", "hand_on_counter",
                         "robes_on_north_hook", "bath_mat")


def accessory_parts(fx, subroom):
    """ELEMENT 6 (D-E6-3/-4/-5): the LOCKED Purist -2MB accessory set + its textiles.

    Hardware (mat='brass', the existing brass row — no new brass material): the 24in
    towel bar on the WEST wall in the WC->curb segment, robe hooks x2 on the east
    door jambs, the paper holder re-sited NORTH of the WC cistern (the drafted band
    landed ON the built wc_tank massing — DD collision fix). Textiles (mat='towel',
    ONE shared token): draped bath towels on the bar, a hand towel on the south hook
    + one folded on the counter between the basins, robes double-hung on the north
    hook, and the flat bath mat centred on the BUILT shower entry gap.

    Everything DERIVES from the sibling fixtures + the door opening — `subroom` is
    therefore required. The towel inventory is CENSUS data (D-E6-3: census, not
    implication), and every census entry must materialize a soft mass — hardware
    succeeding with zero textiles is the revert-by-omission channel. Fail-loud
    everywhere (D-E6 build-consequence 8): missing subroom/census/fixture/door,
    unknown census key, a bar that does not fit its segment, all RAISE."""
    if subroom is None:
        raise ValueError("bath_accessories: needs the enclosing subroom (fixtures + "
                         "openings) — positions DERIVE from the WC/shower/vanity/door, "
                         "never from this entry")
    dz = fx.get("design") or {}
    census = dz.get("census")
    if not isinstance(census, dict) or not census:
        raise ValueError("bath_accessories: design.census missing — the towel "
                         "inventory is CENSUS data (D-E6-3), not an implication")
    unknown = set(census) - set(ACCESSORY_CENSUS_KEYS)
    if unknown:
        raise ValueError(f"bath_accessories: unknown census key(s) {sorted(unknown)} "
                         f"(known: {ACCESSORY_CENSUS_KEYS})")
    counts = {}
    for k in ACCESSORY_CENSUS_KEYS:
        v = census.get(k, 0)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError(f"bath_accessories: census.{k} must be a non-negative "
                             f"int, got {v!r}")
        counts[k] = v
    if sum(counts.values()) == 0:
        raise ValueError("bath_accessories: census is all-zero — accessory data that "
                         "routes to no soft parts must RAISE (the white-box fallback "
                         "swallow, build_room.py:2367-2370)")

    fxs = subroom.get("fixtures") or []

    def _one(pred, what):
        hits = [f for f in fxs if pred(f)]
        if len(hits) != 1:
            raise ValueError(f"bath_accessories: expected exactly 1 {what} in the "
                             f"subroom, found {len(hits)} — positions derive from it")
        return hits[0]

    wc = _one(lambda f: f.get("kind") == "toilet", "toilet")
    shower = _one(lambda f: f.get("kind") == "shower", "shower")
    van = _one(lambda f: str(f.get("kind", "")).startswith("vanity"), "vanity")
    doors = [o for o in subroom.get("openings") or [] if o.get("type") == "door"]
    if len(doors) != 1:
        raise ValueError(f"bath_accessories: expected exactly 1 door opening, found "
                         f"{len(doors)} — the jamb hooks derive from its rect")
    dr = [float(v) for v in doors[0]["rect"]]
    if abs(dr[0] - dr[2]) > 1e-6:
        raise ValueError("bath_accessories: door rect is not on an x-plane wall — "
                         "the jamb-hook derivation reads an east/party-wall door")
    door_x, door_y0, door_y1 = dr[0], min(dr[1], dr[3]), max(dr[1], dr[3])

    parts = []
    # -- towel bar: WEST wall (the WC-cistern plane), centred in the WC->curb segment --
    wall_x = _f(wc, "x")
    wc_n = _f(wc, "y") + _f(wc, "d")
    curb_s = _f(shower, "y")                     # the curb sits on the shower's south edge
    seg = curb_s - wc_n
    bar_len = float(dz.get("bar_len_mm", BAR_LEN))
    if bar_len <= 0 or bar_len >= seg:
        raise ValueError(f"bath_accessories: bar_len {bar_len:.0f} does not fit the "
                         f"WC->curb segment ({seg:.0f}) — take the 18in fallback "
                         f"(spec data bar_len_mm; the schedule FILE stays untouched)")
    bar_y0 = wc_n + (seg - bar_len) / 2.0
    rail_x = wall_x + BAR_STANDOFF - BAR_SECT / 2.0
    rail_z = BAR_AFF - BAR_SECT / 2.0
    parts.append(_box("acc_towelbar_rail", rail_x, bar_y0, rail_z,
                      BAR_SECT, bar_len, BAR_SECT, "brass"))
    for i, py in enumerate((bar_y0, bar_y0 + bar_len - BAR_SECT)):
        parts.append(_box(f"acc_towelbar_post{i}", wall_x, py, rail_z,
                          BAR_STANDOFF, BAR_SECT, BAR_SECT, "brass"))
    n = counts["bath_on_bar"]
    if n and bar_len / n < TOWEL_W:
        raise ValueError(f"bath_accessories: census asks {n} bath towel(s) on a "
                         f"{bar_len:.0f} bar but each needs {TOWEL_W:.0f} — the towels "
                         f"would interpenetrate; shrink the census or lengthen the bar")
    for i in range(n):                       # side-by-side slots, centred in each
        ctr = bar_y0 + (i + 0.5) * bar_len / n
        parts.append(_box(f"acc_bath_towel{i}",
                          wall_x + BAR_STANDOFF - TOWEL_THK / 2.0, ctr - TOWEL_W / 2.0,
                          BAR_AFF - TOWEL_DROP, TOWEL_THK, TOWEL_W,
                          TOWEL_DROP + 40.0, "towel"))
    # -- robe hooks x2 on the east door jambs (south = hand towel, north = robes) ------
    hook_y = {"s": door_y0 - HOOK_JAMB_SETBACK, "n": door_y1 + HOOK_JAMB_SETBACK}
    for side, hy in hook_y.items():
        parts.append(_box(f"acc_robe_hook_{side}", door_x - HOOK_SECT, hy - HOOK_SECT / 2.0,
                          HOOK_AFF, HOOK_SECT, HOOK_SECT, HOOK_SECT, "brass"))
    for i in range(counts["hand_on_south_hook"]):
        parts.append(_box(f"acc_hand_towel_hook{i}", door_x - 45.0,
                          hook_y["s"] - HAND_W / 2.0, HOOK_AFF - HAND_DROP,
                          45.0, HAND_W, HAND_DROP, "towel"))
    for i in range(counts["robes_on_north_hook"]):     # double-hung: layered outward
        parts.append(_box(f"acc_robe{i}", door_x - (i + 1) * ROBE_THK - 10.0,
                          hook_y["n"] - ROBE_W / 2.0 + i * 30.0, HOOK_AFF - ROBE_DROP,
                          ROBE_THK, ROBE_W, ROBE_DROP, "towel"))
    # -- paper holder: WEST wall, immediately NORTH of the WC cistern (re-sited) -------
    holder_y = wc_n + HOLDER_N_OF_WC
    parts.append(_box("acc_paper_holder", wall_x, holder_y - 70.0, HOLDER_AFF - 60.0,
                      90.0, 140.0, 120.0, "brass"))
    # -- folded hand towel on the counter between the basins (soft goods, no hardware) --
    if counts["hand_on_counter"]:
        ctrs = (van.get("design") or {}).get("basin_ctr_x_mm") or []
        cx = (float(ctrs[0]) + float(ctrs[1])) / 2.0 if len(ctrs) >= 2 \
            else _f(van, "x") + _f(van, "w") / 2.0
        cy = _f(van, "y") + _f(van, "d") / 2.0
        for i in range(counts["hand_on_counter"]):
            parts.append(_box(f"acc_hand_towel_counter{i}", cx - 150.0,
                              cy - 100.0 + i * 40.0, _f(van, "h") + i * 35.0,
                              300.0, 200.0, 35.0, "towel"))
    # -- bath mat: centred on the BUILT shower entry gap, in the drawn dry strip -------
    if counts["bath_mat"]:
        g0, g1 = shower_entry_gap(shower)
        mat_cx = (g0 + g1) / 2.0
        for i in range(counts["bath_mat"]):
            parts.append(_box(f"acc_bath_mat{i}", mat_cx - MAT_W / 2.0,
                              curb_s - MAT_CURB_GAP - MAT_D, 0.0,
                              MAT_W, MAT_D, MAT_THK, "towel"))
    soft = [p for p in parts if p["mat"] == "towel"]
    if len(soft) != sum(counts.values()):
        raise ValueError(f"bath_accessories: census promises {sum(counts.values())} "
                         f"soft masses but {len(soft)} were built — hardware without "
                         f"its textiles is the revert-by-omission channel")
    return parts


DISPATCH = {
    "vanity_double": vanity_parts,
    "vanity": vanity_parts,
    "toilet": toilet_parts,
    "bathtub": bathtub_parts,
    "shower": shower_parts,
    "glass_partition": glass_partition_parts,
    "bath_accessories": accessory_parts,   # ELEMENT 6 (needs the enclosing subroom)
}


def fixture_parts(fx, taskbar=False, subroom=None):
    """Route a subroom fixture to its massing fn by `kind`; return [] for unmapped kinds
    (the consumer then falls back to the plain box, like _build_millwork). `taskbar`
    reaches only the vanity branch (the element-5 mirror bar opt-in); `subroom` reaches
    only the accessories branch (element-6 positions derive from the sibling fixtures
    + door — accessory_parts RAISES without it, and RAISES rather than returning [] so
    the consumer's white-box fallback can never swallow a decided accessory set)."""
    fn = DISPATCH.get(str(fx.get("kind", "")))
    if fn is vanity_parts:
        return fn(fx, taskbar=taskbar)
    if fn is accessory_parts:
        return fn(fx, subroom)
    return fn(fx) if fn else []


def all_fixture_parts(fixtures, taskbar=False, subroom=None):
    out = []
    for fx in fixtures or ():
        out.extend(fixture_parts(fx, taskbar=taskbar, subroom=subroom))
    return out
