"""trn001_styling.py — TRN-001 round 5: the styling rung.

Two layers as always (LAYER LAW): a PURE plan and lathe, importable under plain
python, and a bpy half that materialises it.

This is also the first live test of decision (ข) (qa/reproduction-curriculum.md
§Decisions): styling-tier ORGANIC objects use external CC0/PD assets, while
millwork stays build-not-buy, because the ground-truth study measured every pro
file leaning on assets for organics. The rung splits accordingly:

  * VASES — BUILT, after the CC0 route was tried and failed in a way worth
    recording. `ceramic_vase_03` was picked because its bounding box (112 x 414,
    aspect 0.271) matched the target vase's (71 x 269, aspect 0.264) to within
    3% — and it rendered as a flat tapered PLANK, because the asset is
    mispackaged (its mesh datablock is even named "Cube.001"). A bounding box
    cannot tell a vase from a board, exactly as round 3's figure metric could
    not tell veins from tile joints; both times the fix was to LOOK at the asset
    first, and the second time the lesson was already written down. The pool's
    one real vase, `ceramic_vase_01`, is a different vessel entirely — aspect
    0.51 against the target's 0.264, twice as fat. So the profile below was read
    off the target instead, row by row.
  * CANDLESTICKS — built. A turned candlestick is a solid of revolution, which
    is millwork by another name, and building it is the learning (ข) reserves
    for millwork.
  * STATUARY AND FLORALS — see `unavailable()`. The pool holds neither, and
    hand-modelling a Buddha image would be both bad work and disrespectful of
    the subject, which (ข) explicitly guards against with "used respectfully
    as-is". Reported to the gate rather than faked.

EVERY position below is BACK-PROJECTED from the target through the solved
camera, never placed by eye. The evidence they are right: the vase bases land
at z 433-451 against a step top of 455, and the candlestick bases at z 219-229
against a plinth top of 225 — surfaces the placement was never told about.

SCALE ASSERTION (pipeline/CLAUDE.md, a MUST on every ingest of external
geometry): no imported asset reaches the scene until its unit is RESOLVED and
checked. glTF declares metres, but a plausible-but-wrong-scale model is the
exact failure this studio sells against, so `_assert_scale` verifies the
imported bounds fall inside a per-class band and RAISES otherwise.
"""
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CC0_MODELS = os.path.join(REPO, "assets", "shared", "cc0", "models")

# plausible real-world size band per asset class, in mm (min, max) on the
# tallest axis — the assertion, not a guess: outside this the ingest FAILS
SCALE_BAND = {"vase": (80.0, 1200.0)}


def asset_path(slug):
    return os.path.join(CC0_MODELS, slug, f"{slug}_1k.gltf")


# ------------------------------------------------------------------- lathe ---

# Turned candlestick, measured off the target: base z 219-229 against a plinth
# top of 225, bronze body 292-351 mm, white taper carrying it to 397-457 mm
# overall. Profile is (z_mm, radius_mm) from the foot up.
CANDLESTICK = [
    (0.0, 34.0), (4.0, 33.0), (9.0, 26.0), (16.0, 14.0), (26.0, 8.0),
    (48.0, 6.5), (60.0, 9.5), (68.0, 8.0), (150.0, 5.5), (176.0, 8.5),
    (186.0, 7.0), (250.0, 5.5), (300.0, 6.0), (318.0, 10.0), (326.0, 18.5),
    (336.0, 19.5), (340.0, 13.0), (344.0, 11.5),
]
TAPER = [(0.0, 11.0), (6.0, 11.5), (96.0, 10.0), (103.0, 7.0), (106.0, 2.5)]

# The vase, READ OFF THE TARGET row by row rather than chosen from a catalogue:
# its silhouette was back-projected onto the plane it stands on, giving a base
# radius of 16.5 mm swelling to 40.1 at z=80 and necking to ~18 by z=212 — a
# slim teardrop. See the module docstring for why it is built and not imported.
VASE = [
    (0.0, 16.5), (16.0, 26.0), (32.0, 33.0), (48.0, 37.7), (64.0, 39.2),
    (80.0, 40.1), (97.0, 37.7), (113.0, 35.4), (130.0, 33.0), (146.0, 30.7),
    (163.0, 28.3), (179.0, 26.0), (196.0, 23.6), (212.0, 18.6), (221.0, 19.4),
    (228.0, 20.2), (231.0, 17.5),
]

PROFILES = {"CANDLESTICK": CANDLESTICK, "TAPER": TAPER, "VASE": VASE}


def lathe(profile, cx, cy, z0, seg=32, scale=1.0):
    """Solid of revolution from a (z_mm, radius_mm) profile. PURE — returns
    (verts, faces) in mm, so it is testable without Blender.

    Rings are joined with quads and the ends closed with fans; a zero-radius
    entry collapses to a single pole vertex rather than a degenerate ring."""
    verts, rings = [], []
    for z, r in profile:
        z = z0 + z * scale
        r = r * scale
        if r <= 1e-6:
            rings.append([len(verts)])
            verts.append((cx, cy, z))
            continue
        ring = []
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            ring.append(len(verts))
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        rings.append(ring)

    faces = []
    for lo, hi in zip(rings, rings[1:]):
        if len(lo) == 1 and len(hi) == 1:
            continue
        if len(lo) == 1:
            faces.extend([[lo[0], hi[i], hi[(i + 1) % len(hi)]] for i in range(len(hi))])
        elif len(hi) == 1:
            faces.extend([[lo[i], lo[(i + 1) % len(lo)], hi[0]] for i in range(len(lo))])
        else:
            n = len(lo)
            faces.extend([[lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]] for i in range(n)])
    if len(rings[0]) > 1:
        faces.append(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        faces.append(list(rings[-1]))
    return verts, faces


# -------------------------------------------------------------------- plan ---

def plan(spec):
    """spec -> [placement dict]. PURE. Empty when the spec carries no styling,
    so every earlier round still builds byte-identically."""
    st = spec.get("styling") or {}
    out = []
    for v in st.get("vases", []):
        if v.get("slug"):
            out.append({"kind": "asset", "name": v["name"], "slug": v["slug"],
                        "pos_mm": (v["x_mm"], v["y_mm"], v["z_mm"]),
                        "height_mm": v["height_mm"], "rot_z": v.get("rot_z_deg", 0.0),
                        "material": v.get("material", "vase_dark"), "cls": "vase"})
            continue
        out.append({"kind": "lathe", "name": v["name"], "profile": "VASE",
                    "pos_mm": (v["x_mm"], v["y_mm"], v["z_mm"]),
                    "height_mm": v["height_mm"],
                    "material": v.get("material", "vase_dark"), "cls": "vase"})
    for c in st.get("candlesticks", []):
        out.append({"kind": "lathe", "name": c["name"], "profile": "CANDLESTICK",
                    "pos_mm": (c["x_mm"], c["y_mm"], c["z_mm"]),
                    "height_mm": c["bronze_h_mm"], "material": "bronze_dark",
                    "cls": "candlestick"})
        out.append({"kind": "lathe", "name": c["name"] + "_taper", "profile": "TAPER",
                    "pos_mm": (c["x_mm"], c["y_mm"], c["z_mm"] + c["bronze_h_mm"]),
                    "height_mm": c["total_h_mm"] - c["bronze_h_mm"],
                    "material": "wax_white", "cls": "candle"})
    return out


def unavailable(spec):
    """The (ข) classes the ฿0 CC0 pool cannot supply, reported rather than
    faked. This is the decision's first live test answering itself."""
    st = spec.get("styling") or {}
    return list(st.get("_unavailable", []))


def report(spec):
    rows = [f"  {p['name']:16s} {p['kind']:6s} {p['cls']:12s} "
            f"({p['pos_mm'][0]:8.1f},{p['pos_mm'][1]:7.1f},{p['pos_mm'][2]:7.1f}) "
            f"h={p['height_mm']:.0f}mm" for p in plan(spec)]
    miss = unavailable(spec)
    rows.append(f"  -> {len(plan(spec))} placed; {len(miss)} class(es) UNAVAILABLE "
                f"in the CC0 pool: {', '.join(miss) if miss else 'none'}")
    return "\n".join(rows)


# ----------------------------------------------------------------- bpy side ---

def _assert_scale(ob, cls):
    """A MUST on every external ingest (pipeline/CLAUDE.md): resolve the unit,
    never assume it. SketchUp exports imperial from metre-authored models — a
    0.0254x error that still looks like a model. Raises rather than scaling on."""
    dims = [d * 1000.0 for d in ob.dimensions]      # Blender metres -> mm
    tall = max(dims)
    lo, hi = SCALE_BAND.get(cls, (1.0, 1e9))
    if not (lo <= tall <= hi):
        raise ValueError(
            f"SCALE ASSERTION FAILED for {ob.name} ({cls}): tallest axis reads "
            f"{tall:.1f} mm, outside the plausible band {lo:.0f}-{hi:.0f} mm. "
            f"The file's unit is not what was assumed — resolve it, do not scale.")
    return tall


def _assert_placed(mesh_objs, p, tol_mm=8.0):
    """An asset that imported at the right SCALE can still land in the wrong
    PLACE, and the log will say it was placed because the log only reports what
    was asked for. That is what happened here: one vase reported "native 414mm
    -> 259mm (x0.625)" while sitting, unscaled, at the world origin. So the
    placement is now verified against the plan the same way the import is
    verified against physics — the two failures are the same shape, and only one
    of them had a guard."""
    pts = []
    for o in mesh_objs:
        pts.extend(o.matrix_world @ v.co for v in o.data.vertices)
    if not pts:
        raise ValueError(f"{p['name']}: placed asset has no geometry")
    zs = [q.z * 1000.0 for q in pts]
    xs = [q.x * 1000.0 for q in pts]
    ys = [q.y * 1000.0 for q in pts]
    want_x, want_y, want_z = p["pos_mm"]
    got_h = max(zs) - min(zs)
    if abs(min(zs) - want_z) > tol_mm:
        raise ValueError(f"{p['name']}: base landed at z={min(zs):.1f} mm, plan "
                         f"says {want_z:.1f} — the asset was not placed")
    if abs(got_h - p["height_mm"]) > max(tol_mm, 0.03 * p["height_mm"]):
        raise ValueError(f"{p['name']}: stands {got_h:.1f} mm, plan says "
                         f"{p['height_mm']:.1f} — the asset was not scaled")
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    if abs(cx - want_x) > 60.0 or abs(cy - want_y) > 60.0:
        raise ValueError(f"{p['name']}: centred at ({cx:.1f},{cy:.1f}) mm, plan "
                         f"says ({want_x:.1f},{want_y:.1f})")


def _import_gltf(path):
    import bpy
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)        # headless-safe (not a geometry op)
    return [o for o in bpy.data.objects if o not in before]


def build_styling(spec, materials=None):
    """Materialise plan() into the scene. Returns the objects created."""
    import bpy

    import trn001_geom as G

    made = []
    col = bpy.context.scene.collection
    for p in plan(spec):
        if p["kind"] == "asset":
            path = asset_path(p["slug"])
            if not os.path.exists(path):
                print(f"  STYLING: asset {p['slug']} missing at {path} — SKIPPED")
                continue
            objs = _import_gltf(path)
            mesh_objs = [o for o in objs if o.type == "MESH"]
            if not mesh_objs:
                print(f"  STYLING: {p['slug']} imported no mesh — SKIPPED")
                continue
            native_mm = _assert_scale(mesh_objs[0], p["cls"])
            k = p["height_mm"] / native_mm
            # Transform each mesh's ROOT ancestor, deduped — not "every object
            # whose parent is None". The second vase came back parented and so
            # matched neither branch, and it rendered at native size at the world
            # ORIGIN while the log cheerfully reported it scaled and placed.
            roots, seen_roots = [], set()
            for o in mesh_objs:
                r = o
                while r.parent is not None:
                    r = r.parent
                if r.name not in seen_roots:
                    seen_roots.add(r.name)
                    roots.append(r)
            for r in roots:
                r.scale = tuple(s * k for s in r.scale)
                r.rotation_euler = (r.rotation_euler[0], r.rotation_euler[1],
                                    math.radians(p["rot_z"]))
                r.location = tuple(c * G.MM for c in p["pos_mm"])
            for o in mesh_objs:
                o.name = f"SM_TRN001_{p['name']}"
                if materials and p["material"] in materials:
                    o.data.materials.clear()
                    o.data.materials.append(materials[p["material"]])
            bpy.context.view_layer.update()          # so world matrices are live
            _assert_placed(mesh_objs, p)
            print(f"  STYLING: {p['name']} <- {p['slug']} native {native_mm:.0f}mm "
                  f"-> {p['height_mm']:.0f}mm (x{k:.3f})")
            made.extend(objs)
            continue

        profile = PROFILES[p["profile"]]
        native = max(z for z, _ in profile)
        k = p["height_mm"] / native if native else 1.0
        cx, cy, cz = p["pos_mm"]
        verts, faces = lathe(profile, cx, cy, cz, scale=k)
        me = bpy.data.meshes.new(f"SM_TRN001_{p['name']}")
        me.from_pydata([(x * G.MM, y * G.MM, z * G.MM) for x, y, z in verts], [], faces)
        me.validate()
        for poly in me.polygons:
            poly.use_smooth = True
        if materials and p["material"] in materials:
            me.materials.append(materials[p["material"]])
        ob = bpy.data.objects.new(f"SM_TRN001_{p['name']}", me)
        col.objects.link(ob)
        made.append(ob)
    return made
