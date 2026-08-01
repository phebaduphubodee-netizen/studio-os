"""trn001_light.py — TRN-001 round 4: THE LIGHT STORY.

Two layers, split the same way materials were (LAYER LAW): a PURE `plan()` that
says which fixture sits where, at what power and in what colour — importable
and testable under plain python — and a bpy builder that materialises it.

WHAT OPENED THIS ROUND, in numbers rather than adjectives (trn001_lightcheck
against the target, 2026-07-31):

  our ceiling  1.21x the wall's brightness   target 0.73x   -> 1.66x too bright
  our cubbies  0.10 of the wall              target 0.06    -> 1.63x too bright
  our shadows  p1 = 0.0151                   target 0.0055  -> 2.7x lifted
  our frame    p99/p1 = 66:1                 target 141:1   -> half the range
  our halo     3.30x the wall, clips 2.15%   target 1.72x, clips 0.08%

Every one of those is the same defect wearing five faces: rounds 1-3 lit the
set with a WORLD (uniform light arriving from every direction at once) plus one
sun, and a world lights a ceiling exactly as hard as it lights a floor. Real
rooms do not do that. The 2026-07-30 ground-truth study measured this as the
studio's #1 gap across every project — pro files run 191:1 to 2500:1 energy
range with a warm key on top; we ran 10:1 with a cool fill on top.

So the rig here is made of the things the target actually shows:
  * two recessed downlights, positions MEASURED (bright disks in the ceiling,
    back-projected onto the ceiling plane, both at y = -605 mm off the wall to
    within 0.5 mm) and carrying a real LM-63 photometric profile, so the beam
    has the shape a fixture throws instead of the shape a bare disk washes;
  * their inferred continuation into the room behind the frame, which is where
    the room's ambient comes from — declared inferred, never dressed as
    measured;
  * the concealed LED behind the slab (a material, in trn001_materials), dialled
    against the measured halo profile instead of against how bright it looks;
  * a WORLD reduced to what it really is here — the light of the rest of the
    house arriving through the room's opening — not the room's light source.

IES NORMALISATION, inherited as a measured constant rather than re-derived:
build_room.py's lane-B pass proved raw IES Fac re-powers a whole rig (room mean
84 -> 166, whites clipping) because a photometric profile is meant to SHAPE a
beam, not re-spec the wattage. 5.ies (Halo H7t-301 recessed open trim, the one
profile in the fetched pack that IS this fixture type) carries norm 0.20 there;
the same constant is used here and the watts stay the one power authority.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import trn001_geom as G  # noqa: E402

REPO = os.path.dirname(os.path.dirname(_HERE))
IES_DIR = os.path.join(REPO, "knowledge", "_inbox", "discord", "MY-DATA-PEAT",
                       "_external-fetched", "sharing", "002_IES")


def ies_path(fname):
    """A real IESNA LM-63 file from the 30-profile pack fetched 2026-07-04
    (knowledge/lighting/ies-and-lighting-notes-discord.md maps index -> maker)."""
    return os.path.join(IES_DIR, fname) if fname else None


# build_room.py carries two IES norms that were each bracketed by hand against a
# rendered frame: 5.ies at 0.20 with "candela mean 629", 7.IES at 0.065 with
# "mean 1947". Multiply them out — 0.20 x 629 = 125.8, 0.065 x 1947 = 126.6 —
# and the two hand-tuned constants are one RULE with a 0.6% spread: norm =
# K / mean_candela, i.e. equalise the profiles by their own mean so swapping a
# beam shape cannot silently re-power the rig. Kept as a derivation rather than
# a third pinned number, because a per-file constant is exactly the shape of
# decision this project keeps losing to staleness.
IES_NORM_K = 126.0


def ies_mean_candela(path):
    """Arithmetic mean of an LM-63 file's candela table. PURE. Reproduces
    build_room's own measured 629 for 5.ies, which is what ties this parser to
    the constant above."""
    with open(path, "r", encoding="latin-1") as f:
        txt = f.read()
    i = txt.upper().find("TILT=")
    body = txt[txt.find("\n", i) + 1:] if i >= 0 else txt
    tok = []
    for t in body.split():
        try:
            tok.append(float(t))
        except ValueError:
            return None
    if len(tok) < 13:
        return None
    n_v, n_h = int(tok[3]), int(tok[4])
    start = 13 + n_v + n_h
    cd = tok[start:start + n_v * n_h]
    if not cd:
        return None
    return sum(cd) / len(cd)


def ies_norm_for(fname, given):
    """`given` may be a number (kept as-is) or "auto" (derived). Returns
    (norm, provenance) so the build log can say which it used."""
    if given != "auto":
        return float(given), "pinned"
    p = ies_path(fname)
    mean = ies_mean_candela(p) if p and os.path.exists(p) else None
    if not mean:
        return 1.0, "UNREAD (profile unparsed — bare emitter power)"
    return IES_NORM_K / mean, f"auto K/{mean:.0f}"


def aim_euler(pos, aim):
    """(pitch, 0, yaw) that points a light's local -Z at a world point. PURE.

    This lives here, tested, because the inline version it replaces was WRONG BY
    180 DEGREES IN YAW and had been wrong for every aimed light this lane ever
    built. `atan2(dy, dx) + pi/2` names the direction perpendicular to the run,
    turned the wrong way: rotating (0,0,-1) by X then Z gives
    (-sin@ sin!, sin@ cos!, -cos@), so the yaw that satisfies it is
    atan2(-dx, dy) -- the two differ by exactly pi, which is why the error was
    invisible in the one case where it could not show (the cove, tilted 3.4 deg
    off vertical, landed 6.8 deg from its aim and still read as "down").

    IT IS NOT INVISIBLE IN THE OTHER CASE. `_fill_refuted` and `_fill_retest`
    both describe an AREA light "standing off frame on the camera side" aimed
    INTO the room; built through the old formula it faced 180 deg away, i.e. it
    lit the back of the room and reached the frame only as bounce. A source that
    can only arrive as bounce is a diffuse fill by construction -- which is
    precisely the "raises everything at once and FLATTENS" result both
    refutations recorded. Those two verdicts now rest on a broken instrument
    (they measured a bounce card, not the wall-directed source they claim), and
    that is the owner's to re-open, not this lane's to assume.

    Verified against bpy itself rather than against this reasoning: Blender's own
    object transform returns 44.4 deg of error for the shipped formula and 0.0
    for this one on the downlight case."""
    import math

    dx, dy, dz = (a - p for a, p in zip(aim, pos))
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return (0.0 if dz < 0 else math.pi, 0.0, 0.0)
    return (math.atan2(run, -dz), 0.0, math.atan2(-dx, dy))


def plan(spec):
    """spec -> [fixture dict]. PURE. Positions come from trn001_geom so the
    emitter and the housing the camera sees are the same decision."""
    lt = spec.get("light") or {}
    dl = lt.get("downlights") or {}
    ceil = spec["room"]["ceiling_mm"]
    # emitter sits just below the lens it appears to come from, so the housing
    # never shadows its own light
    z = ceil - float(dl.get("trim_drop_mm", 12.0)) - float(dl.get("emitter_drop_mm", 6.0))
    norm, prov = ies_norm_for(dl.get("ies"), dl.get("ies_norm", "auto"))
    out = []
    for name, x, y, measured in G.downlight_positions(spec):
        # the inferred rows carry their OWN wattage. They are the part of the rig
        # that no probe can check directly, so they get the knob the frame CAN
        # check: the target's visible floor falls 37.6% end to end while ours ran
        # flat at 3.5%, and a second row sitting between the camera and the
        # measured row is exactly what would fill that ramp in.
        watt = dl.get("watt", 60.0) if measured else dl.get("fill_watt", dl.get("watt", 60.0))
        # WALL-WASH AIM, and the reason it is the measured row ONLY. That row is
        # 605 mm off the wall on a 2700 ceiling — the setback of a wall-wash, and
        # downlight_positions' own docstring already calls it "what a wall-wash
        # row is" — but every round so far has emitted it pointing at the floor,
        # which is why our floor field is explained by distance-to-nearest-lamp
        # at R2 0.965 while the target's reaches 0.104-0.449, and why
        # floor_far_left (1.0 m from the left lamp) reads 2.73x. A wall-wash
        # REDISTRIBUTES: it is the only lever tried in this lane that lowers a
        # horizontal and raises a vertical with one move, because it does not add
        # a source. The inferred rows behind the frame keep pointing down — they
        # are the room's general lighting and the only thing feeding floor_near,
        # which is already 0.79x SHORT.
        #
        # TILT IS THE KNOB, not the aim height. `aim_z_mm` cannot express a
        # gentle wash: the fixture sits 605 mm off a 2682 mm ceiling, so aiming
        # at the wall's very base is already 12.7 deg and there is no aim point
        # below it — the parameter's own floor was 12.7, which is most of the
        # useful range, and a sweep that cannot reach the small end cannot
        # bisect (the same shape as sweeping a depth from 200 mm and concluding
        # "no solution" from a range that excluded the answer).
        aim = None
        tilt = dl.get("tilt_deg")
        if measured and tilt is not None:
            r = math.radians(float(tilt))
            aim = (x, y + math.sin(r) * 1000.0, z - math.cos(r) * 1000.0)
        elif measured and dl.get("aim_z_mm") is not None:
            aim = (x + float(dl.get("aim_dx_mm", 0.0)),
                   float(dl.get("aim_y_mm", 0.0)), float(dl["aim_z_mm"]))
        out.append({
            "name": name,
            "kind": "SPOT",
            "aim": aim,
            "pos": (x, y, z),
            "watt": float(watt),
            "kelvin": float(lt.get("kelvin", 3800.0)),
            "spot_deg": float(dl.get("spot_deg", 110.0)),
            "spot_blend": float(dl.get("spot_blend", 0.5)),
            "radius_mm": float(dl.get("lens_dia_mm", 88.0)) / 2.0,
            "ies": dl.get("ies"),
            "ies_norm": norm,
            "ies_norm_from": prov,
            "measured": bool(measured),
        })

    # THE ROOM'S OTHER SOURCE, and why it has to exist. Three readings taken off
    # the target together rule out a ceiling fixture: the floor ramps 42% toward
    # frame-right (which is also toward the camera), the wall right of the bay is
    # brighter at the BOTTOM, and the ceiling shows no left-right lean at all. A
    # downlight bright enough to ramp the floor would lean the ceiling and light
    # the wall from above; something at low-to-mid height, off frame on the
    # camera side, does all three. That is an ordinary room opening — a door or a
    # window — and it is declared INFERRED, with its direction derived from the
    # frame rather than chosen.
    # WALL-DIRECTED, and that word is the whole difference from the fill this
    # lane already built and refuted. `_fill_refuted` records a big soft AREA
    # standing off-frame on the camera side: it raised everything at once and
    # FLATTENED the frame (p99/p1 50 -> 28 -> 15). The measurement that asks for
    # this one is different in both sign and direction — our verticals run 0.78x
    # of the target while our horizontals run 1.11x (ceiling) and 2.20x (far
    # floor), and our wall's own top-to-bottom ramp is 1.81 against the target's
    # 1.40, i.e. too bottom-heavy. A wash arriving from ABOVE, at the wall,
    # raises verticals and flattens that ramp without feeding the horizontals,
    # which no omnidirectional source can do.
    #
    # It hides behind the header band (the header stands 100 mm off the wall and
    # its soffit is at z=2439), so it is a cove a joiner could actually build,
    # not a light floating in the room.
    cv = lt.get("cove")
    if cv:
        out.append({
            "name": "cove_wallwash",
            "kind": "AREA",
            "pos": (float(cv["x_mm"]), float(cv["y_mm"]), float(cv["z_mm"])),
            "aim": (float(cv.get("aim_x_mm", cv["x_mm"])),
                    float(cv.get("aim_y_mm", 0.0)),
                    float(cv.get("aim_z_mm", 1200.0))),
            "size_mm": (float(cv.get("w_mm", 3400.0)), float(cv.get("h_mm", 60.0))),
            "watt": float(cv.get("watt", 40.0)),
            "kelvin": float(cv.get("kelvin", lt.get("kelvin", 3800.0))),
            "hidden": bool(cv.get("hidden", True)),
            "ies": None, "ies_norm": 1.0, "ies_norm_from": "-",
            "measured": False,
        })

    fl = lt.get("fill")
    if fl:
        out.append({
            "name": "fill_opening",
            "kind": "AREA",
            "pos": (float(fl["x_mm"]), float(fl["y_mm"]), float(fl["z_mm"])),
            "aim": (float(fl.get("aim_x_mm", 0.0)), float(fl.get("aim_y_mm", -1200.0)),
                    float(fl.get("aim_z_mm", 900.0))),
            "size_mm": (float(fl.get("w_mm", 1800.0)), float(fl.get("h_mm", 1800.0))),
            "watt": float(fl.get("watt", 60.0)),
            "kelvin": float(fl.get("kelvin", lt.get("kelvin", 3800.0))),
            "ies": None, "ies_norm": 1.0, "ies_norm_from": "-",
            "measured": False,
        })
    return out


def world(spec):
    """The world is NOT the room's light source here — it is the rest of the
    house seen through the room's opening. Rounds 1-3 had it at 0.55 doing all
    the work, which is what flattened the ceiling."""
    lt = spec.get("light") or {}
    w = lt.get("world") or {}
    return {"strength": float(w.get("strength", 0.05)),
            "kelvin": float(w.get("kelvin", lt.get("kelvin", 3800.0)))}


def film(spec):
    """View transform + exposure. The target holds its lens cores at 1.0 while
    clipping only 0.08% of the frame; ours clipped 2.15% under Standard, which
    is a straight-line transform with no shoulder to hold a highlight. AgX has
    one — this is a measured lever, not a preference."""
    lt = spec.get("light") or {}
    f = lt.get("film") or {}
    return {"view_transform": f.get("view_transform", "AgX"),
            "look": f.get("look", "None"),
            "exposure": float(f.get("exposure", 0.0))}


def halo_watt(spec):
    """Emission strength for the concealed LED, spec-owned so the LIGHT round
    can dial it without editing the materials table."""
    lt = spec.get("light") or {}
    return lt.get("halo_w")


def report(spec):
    """One line per fixture for the build log, marking which are measured."""
    rows = []
    fx = plan(spec)
    for f in fx:
        tag = "MEASURED" if f["measured"] else "inferred"
        ies = f["ies"] or "-"
        if f["kind"] == "AREA":
            rows.append(f"  {f['name']:10s} {tag:8s} "
                        f"({f['pos'][0]:8.1f},{f['pos'][1]:8.1f},{f['pos'][2]:7.1f}) "
                        f"{f['watt']:5.1f}W {f['kelvin']:.0f}K AREA "
                        f"{f['size_mm'][0]:.0f}x{f['size_mm'][1]:.0f} aim {f['aim']}")
            continue
        import math as _m
        tilt = "nadir" if f.get("aim") is None else \
            f"tilt {_m.degrees(aim_euler(f['pos'], f['aim'])[0]):.1f}d->wall"
        rows.append(f"  {f['name']:10s} {tag:8s} "
                    f"({f['pos'][0]:8.1f},{f['pos'][1]:8.1f},{f['pos'][2]:7.1f}) "
                    f"{f['watt']:5.1f}W {f['kelvin']:.0f}K {tilt:16s} "
                    f"ies={ies}x{f['ies_norm']:.4f} [{f['ies_norm_from']}]")
    w, fm = world(spec), film(spec)
    n_meas = sum(1 for f in fx if f["measured"])
    rows.append(f"  -> {len(fx)} fixtures ({n_meas} measured, {len(fx) - n_meas} inferred), "
                f"world {w['strength']:.3f}, {fm['view_transform']} "
                f"exposure {fm['exposure']:+.2f}, halo {halo_watt(spec)}")
    return "\n".join(rows)


# ------------------------------------------------------------------ bpy side --

def _blackbody(nt, kelvin):
    bb = nt.nodes.new("ShaderNodeBlackbody")
    bb.inputs["Temperature"].default_value = kelvin
    return bb


def _attach_ies(ld, path, norm):
    """Real photometric distribution on the light, NORMALISED. See the module
    docstring: raw Fac re-powers the rig; the profile shapes, the watts power."""
    import bpy  # noqa: F401  (import proves we are inside Blender)
    ld.use_nodes = True
    nt = ld.node_tree
    em = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeEmission"), None)
    if em is None:
        em = nt.nodes.new("ShaderNodeEmission")
        out = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputLight"), None) \
            or nt.nodes.new("ShaderNodeOutputLight")
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    ies = nt.nodes.new("ShaderNodeTexIES")
    ies.mode = "EXTERNAL"
    ies.filepath = path
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = float(norm)
    nt.links.new(ies.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], em.inputs["Strength"])
    return em


def build_lights(spec):
    """Materialise plan() into Blender lights. Data API only (no bpy.ops)."""
    import math

    import bpy
    col = bpy.context.scene.collection
    made = []
    for f in plan(spec):
        ld = bpy.data.lights.new(f"LGT_TRN001_{f['name']}", type=f["kind"])
        ld.energy = f["watt"]
        ld.color = (1.0, 1.0, 1.0)
        if f["kind"] == "SPOT":
            ld.shadow_soft_size = f["radius_mm"] * G.MM
            ld.spot_size = math.radians(f["spot_deg"])
            ld.spot_blend = f["spot_blend"]
        elif f["kind"] == "AREA":
            ld.shape = "RECTANGLE"
            ld.size, ld.size_y = (s * G.MM for s in f["size_mm"])
            # a concealed cove is concealed BY GEOMETRY here (it sits behind the
            # header's own soffit); the flag is a belt on top of that, so a small
            # spec change can never turn the source itself into a visible bar
            if f.get("hidden") and hasattr(ld, "visible_camera"):
                ld.visible_camera = False
        p = ies_path(f["ies"])
        em = None
        if p and os.path.exists(p):
            em = _attach_ies(ld, p, f["ies_norm"])
        elif f["ies"]:
            print(f"  LIGHT: ies {f['ies']} missing at {p} — bare emitter kept")
        # colour via blackbody so the temperature is the knob, not an RGB guess
        if em is not None:
            bb = _blackbody(ld.node_tree, f["kelvin"])
            ld.node_tree.links.new(bb.outputs["Color"], em.inputs["Color"])
        else:
            ld.use_nodes = True
            nt = ld.node_tree
            e = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeEmission"), None)
            if e is not None:
                nt.links.new(_blackbody(nt, f["kelvin"]).outputs["Color"], e.inputs["Color"])
        ob = bpy.data.objects.new(f"LGT_TRN001_{f['name']}", ld)
        ob.location = tuple(c * G.MM for c in f["pos"])
        aim = f.get("aim")
        if aim is None:
            ob.rotation_euler = (0.0, 0.0, 0.0)  # -Z local = straight down
        else:
            # aim the light's -Z at a world point. No bpy.ops, no track
            # constraint, and no inline trigonometry either — see aim_euler.
            ob.rotation_euler = aim_euler(f["pos"], aim)
        col.objects.link(ob)
        made.append(ob)
    return made


def build_world(spec):
    import bpy
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    cfg = world(spec)
    bg.inputs[1].default_value = cfg["strength"]
    nt.links.new(_blackbody(nt, cfg["kelvin"]).outputs["Color"], bg.inputs[0])
    return w


def apply_film(spec, scene):
    cfg = film(spec)
    vs = scene.view_settings
    for vt in (cfg["view_transform"], "AgX", "Filmic", "Standard"):
        try:
            vs.view_transform = vt
            break
        except TypeError:
            continue
    try:
        vs.look = cfg["look"]
    except TypeError:
        pass
    vs.exposure = cfg["exposure"]
    return vs.view_transform
