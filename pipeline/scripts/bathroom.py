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


def shower_parts(fx):
    """Glass shower NW: cool tray + a low curb on the south (entry) edge + a frameless
    fixed glass screen on part of the south face (entry gap left) + a brass head/arm."""
    x0, y0 = _f(fx, "x"), _f(fx, "y")
    W, D, H = _f(fx, "w"), _f(fx, "d"), _f(fx, "h")
    nm = "shower"
    screen_w = W * 0.55                     # a fixed screen; the rest is the entry
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


DISPATCH = {
    "vanity_double": vanity_parts,
    "vanity": vanity_parts,
    "toilet": toilet_parts,
    "bathtub": bathtub_parts,
    "shower": shower_parts,
    "glass_partition": glass_partition_parts,
}


def fixture_parts(fx, taskbar=False):
    """Route a subroom fixture to its massing fn by `kind`; return [] for unmapped kinds
    (the consumer then falls back to the plain box, like _build_millwork). `taskbar`
    reaches only the vanity branch (the element-5 mirror bar opt-in)."""
    fn = DISPATCH.get(str(fx.get("kind", "")))
    if fn is vanity_parts:
        return fn(fx, taskbar=taskbar)
    return fn(fx) if fn else []


def all_fixture_parts(fixtures, taskbar=False):
    out = []
    for fx in fixtures or ():
        out.extend(fixture_parts(fx, taskbar=taskbar))
    return out
