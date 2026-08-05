"""trn002_light.py — TRN-002 phase 2: THE LIGHT STORY. Two layers (LAYER LAW).

`plan()` is PURE — which emitter sits where, how big, how strong, what colour —
importable and testable under plain python. `build_world`/`build_lights` are the
bpy half.

THIS RIG IS BUILT FROM A MEASUREMENT PASS, AND THE PASS REFUTED MOST OF WHAT
A DESIGNER WOULD ASSUME FROM LOOKING AT THE ROOM:

  * THE LEFT-WALL WINDOW IS NOT THE KEY. It is a filtered, near-closed blind.
    The wardrobe face directly across from it shows no peak opposite the
    window's band; the floor NEAREST it is the darkest floor in frame (0.172
    against 0.253 a metre further in); the ceiling corner nearest it is the
    darkest ceiling (0.236 vs 0.454). The one cast shadow in the frame points
    at -69 deg where a window key predicts -47 deg. Build it as an aperture
    that lights its own slats and the desk zone, and nothing else.
  * THE DOWNLIGHTS MAKE NO POOLS. Measured negative twice, independently: on
    the ceiling the reflector glow is back to background within 120-200 mm
    world radius, and on the floor the parquet directly beneath dl_1 reads
    0.184 and RISES to 0.220 further away. Four blown lens cores and one -8%
    handle shadow is their entire contribution. Do NOT model beams — and note
    that our own flat form light was making exactly the pools four blind
    critics kept counting as extra downlights.
  * THE NIGHTSTAND LAMP IS OFF. A black cone at Ylin 0.008-0.020, no rim, no
    pool. The wall brightening beside it is the wall's own fitted gradient.
  * THE ETAGERE'S DARK LEVELS STAY DARK. The named debt ("our clay reads the
    unlit levels as solid") is real, but the target does NOT lift them: on ONE
    continuous panel the unlit compartment sits at 0.099 while the lit one
    sits at 0.283 and the strip line at 0.726. What sells it is the 250 mm
    falloff GRADIENT under each strip, not fill. Adding fill moves us away.

So the room is driven by a LARGE DIFFUSE SOURCE off-frame past the camera,
front-left. It must cast almost nothing: a frame standing 30 mm proud of the
back wall casts no measurable shadow (its two sides agree within 0.6%), and the
deepest cast shadow anywhere in the frame is -8%.

THE RIG IS AIMED AT RATIOS, NOT AT WATTS. Every target below is a same-material
ratio, because those are the only readings that survive not knowing the target's
tonemap (it is an 8-bit display-referred JPEG; absolute cd/m2 is unrecoverable):

    bed-base -Y face / -X face            1.38
    white bedding, head / foot            1.57
    ceiling, brightest / darkest corner   1.92   (dark at the BACK-LEFT)
    rug, lit / shaded                     1.23
    wardrobe face gradient                -0.028 Ylin per metre toward -y
    back wall                             FLAT in x, -7.7% per metre upward
    etagere: strip / lit shelf / unlit     7.6 / 2.9 / 1
"""
import math

# key light: a big soft card in front-left, off frame, past the camera.
# Its position is INFERRED, not measured — the frame shows the gradient it
# produces and cannot show the emitter. Declared as A everywhere it is quoted.
KEY = {
    "name": "KEY_front_left", "kind": "AREA", "shape": "RECTANGLE",
    "loc_mm": (-3300, -8700, 2400), "size_mm": (3000, 2000),
    # Aimed DOWN into the room, not across it. The first rig at 78 deg threw
    # the key flat down the room and lit the back wall directly, and the ladder
    # caught it: every object in the room came back at 0.4-0.65 of its target
    # value RELATIVE TO that wall. The target's back wall is not directly lit
    # at all — it measures FLAT in x and -7.7% per metre UPWARD, i.e. brightest
    # at the floor, which is the signature of bounce off the rug and the bed.
    # So the key has to light the floor and the bedding, and the wall has to be
    # paid for out of what they return.
    "rot_deg": (58.0, 0.0, -14.0),
    # 165 W, bracketed on the quick rung against the target's own histogram
    # (three-point sweep after the strip/world clipping was fixed): p50 0.363
    # vs 0.372, p95 0.617 vs 0.636. It is an EXPOSURE match, not a physical
    # wattage — the target is display-referred with an unknown tonemap, so no
    # absolute power is recoverable and none is claimed.
    "power_w": 98.0, "color": (1.000, 0.958, 0.912),
    "prov": "A(inferred: the frame shows the gradient, never the emitter; a "
            "glazed wall, an HDRI portal and a fill card all predict it)",
}

# the blind: a filtered aperture, NOT a portal
BLIND = {
    "name": "BLIND_left_wall", "kind": "AREA", "shape": "RECTANGLE",
    "loc_mm": (-4735, -1770, 1640), "size_mm": (1720, 1820),
    "rot_deg": (90.0, 0.0, 90.0),
    "power_w": 38.0, "color": (0.960, 0.975, 1.000),
    "prov": "M(extent y -2630..-910, z 730..2550 backprojected from the blind "
            "sliver) / A(power: it lights its own slats at 0.43-0.49 and the "
            "desk zone, and the floor beside it is the frame's darkest)",
}

# four recessed lenses: blown cores, glow dead by ~200 mm, no beam
DOWNLIGHT_XY = ((-4129, -2465), (-3851, -717), (-1778, -706), (-1788, -2456))
DOWNLIGHT = {
    # z 3102 = AT the ceiling plane, not 92 mm below it. A source hanging below
    # the plane delivers light to it at a grazing angle and washes a halo; a
    # source ON the plane delivers cos(theta)=0 and cannot light it at all.
    # That is the whole mechanism behind the ceiling glow the owner saw, Gemini
    # filed twice, and four blind critics kept counting as extra fixtures —
    # and it was 92 mm of z, not a power setting.
    "kind": "POINT", "z_mm": 3102, "radius_mm": 40.0,
    # 9 W washed a visible pool across the ceiling in the first materials
    # frame — the exact artifact the measurement refuted twice, and the exact
    # artifact four blind critics kept counting as extra downlights in the clay
    # rounds. The lens BRIGHTNESS is carried by the dl_ masses' emissive
    # material (trn002_materials.EMISSIVE), not by these; what is left here is
    # only enough to buy the one -8% handle shadow the target actually shows.
    "power_w": 1.6, "color": (1.000, 0.945, 0.885),
    "prov": "M(positions from the target's blob grid, all four prov M in spec) "
            "/ A(power: bounded ABOVE by 'no ceiling pool beyond 200 mm and no "
            "floor pool at all' — the parquet under dl_1 reads 0.184 and RISES "
            "to 0.220 a metre away, so a pool is not a tuning error here, it "
            "is the wrong sign)",
}

# concealed LED strips under the etagere boards
STRIP_Z = (2382, 1855, 1319)
STRIP = {
    "x_mm": -4470, "y_mm": -200, "len_mm": 452, "depth_mm": 26,
    # 5.2 W sat 26 mm off the back panel and blew 11,000 px of wall and panel
    # to pure white — 40x the target's ENTIRE clipped budget (273 px, and all
    # of those are lens cores, not strips). The target's strip line itself
    # reads 0.726 and does not clip; what sells the etagere is its 250 mm
    # falloff (0.73 at 20 mm -> 0.40 at 90 -> 0.28 at 250), so the strip is
    # powered to that GRADIENT, not to "looks like a lit shelf".
    "power_w": 0.85, "color": (1.000, 0.905, 0.790),
    "prov": "M(z levels from the board fits: 2382/1855/1319, pitch ~530; wash "
            "0.73 at 20 mm -> 0.40 at 90 -> 0.28 at 250 -> flat) / A(power)",
}

WORLD = {
    # 0.06 lifted our p1 to 0.067 against the target's 0.004 — a world floods
    # every shadow in the room at once, which is the same defect trn001's light
    # round was written to kill ("rounds 1-3 lit the set with a WORLD ... and a
    # world lights a ceiling exactly as hard as it lights a floor").
    "strength": 0.018, "color": (0.760, 0.820, 0.900),
    "prov": "A(a small cool ambient standing for the rest of the flat arriving "
            "through the room's openings — NOT the room's light source; a "
            "world lights a ceiling as hard as a floor, which is precisely the "
            "defect the blockout's form light had)",
}


def plan(spec=None):
    """Every emitter as a plain dict. PURE — no bpy, no I/O.

    The spec's `light` block may override any emitter's power by name, e.g.
    {"power_w": {"KEY_front_left": 210}}. That exists so exposure is bracketed
    on the QUICK rung (R5) instead of guessed: the first full materials frame
    came back with p95 AND p99 both pinned at 1.000, and a clipped frame cannot
    be measured at all — every ladder row above the clip reads the same number
    whatever the light is doing.

    `rot_deg`, `loc_mm` and `size_mm` take the same by-name form. AIM is
    bracketed for the same reason POWER is: r13 measured our back wall's
    vertical gradient at +6% per metre UPWARD where the target's is -7.7%, i.e.
    the SIGN is wrong — ours is lit from above by the key, the target's from
    below by bounce off the floor and the bed. A sign error in a gradient is an
    aim question, and aiming by eye is what put it there."""
    lb = (spec or {}).get("light") or {}
    over = lb.get("power_w") or {}
    rot_over, loc_over, size_over = (lb.get("rot_deg") or {},
                                     lb.get("loc_mm") or {},
                                     lb.get("size_mm") or {})
    out = [dict(KEY), dict(BLIND)]
    for i, (x, y) in enumerate(DOWNLIGHT_XY, start=1):
        out.append({**DOWNLIGHT, "name": f"DL_{i}", "loc_mm": (x, y, DOWNLIGHT["z_mm"])})
    for i, z in enumerate(STRIP_Z, start=1):
        out.append({**STRIP, "name": f"STRIP_{i}", "kind": "AREA",
                    "shape": "RECTANGLE",
                    "loc_mm": (STRIP["x_mm"], STRIP["y_mm"], z),
                    "size_mm": (STRIP["len_mm"], STRIP["depth_mm"]),
                    "rot_deg": (0.0, 0.0, 0.0)})
    for f in out:
        n = f["name"]
        if n in over:
            f["power_w"] = float(over[n])
        if n in rot_over:
            f["rot_deg"] = tuple(float(a) for a in rot_over[n])
        if n in loc_over:
            f["loc_mm"] = tuple(float(a) for a in loc_over[n])
        if n in size_over:
            f["size_mm"] = tuple(float(a) for a in size_over[n])
    return out


def report():
    lines = []
    for f in plan():
        loc = f.get("loc_mm")
        lines.append(f"  {f['name']:16s} {f['kind']:5s} {f['power_w']:6.1f} W  "
                     f"at ({loc[0]:6.0f},{loc[1]:6.0f},{loc[2]:5.0f})  "
                     f"{f['prov'].split('(')[0]}")
    return "\n".join(lines)


# ------------------------------------------------------------- bpy builders --

def build_world(spec=None):
    import bpy
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*WORLD["color"], 1.0)
    s = ((spec or {}).get("light") or {}).get("world_strength")
    bg.inputs[1].default_value = WORLD["strength"] if s is None else float(s)


def build_lights(spec=None):
    import bpy
    MM = 0.001
    for f in plan(spec):
        data = bpy.data.lights.new(f["name"], type=f["kind"])
        data.energy = f["power_w"]
        data.color = f["color"]
        if f["kind"] == "AREA":
            data.shape = f.get("shape", "RECTANGLE")
            sx, sy = f["size_mm"]
            data.size, data.size_y = sx * MM, sy * MM
        else:
            data.shadow_soft_size = f.get("radius_mm", 50.0) * MM
        ob = bpy.data.objects.new(f["name"], data)
        ob.location = tuple(v * MM for v in f["loc_mm"])
        ob.rotation_euler = tuple(math.radians(a) for a in f.get("rot_deg", (0, 0, 0)))
        bpy.context.scene.collection.objects.link(ob)
