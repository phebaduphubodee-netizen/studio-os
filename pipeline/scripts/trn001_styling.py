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


# ------------------------------------------------------------------ floral ---
#
# THE LILIES ARE BUILT, AND THE BUDDHA IMAGES ARE NOT. Round 5 refused to
# hand-model the figures because decision (ข) says "religious statuary used
# respectfully as-is" and a crude hand-built figure would be bad work and
# disrespectful of its subject. That reasoning is upheld here — and it does not
# extend to cut flowers, which are ordinary props. Round 5 also recorded that
# "the pool holds 13 models": 13 was the LOCAL CACHE, not the pool. The real
# Poly Haven pool is 521 models and was searched exhaustively on 2026-08-01 —
# its only flowers are Namaqualand field flowers and ground cover (no cut stem,
# no arrangement) and its only figures are a gothic statue, a marble bust, a
# horse and three bronze sea animals. So round 5's CONCLUSION survives on the
# full pool while its EVIDENCE was a cache miss read as a source gap — the same
# shape as the vault search that ran in the wrong language.
#
# EVERY NUMBER BELOW IS MEASURED off the target, by chroma rather than by hand:
# this room is a neutral wood/white/gold set, so the strongly magenta pixels in
# it are the flowers and nothing else (the gold figures are warm — R>G and B<G —
# and the mask requires B>G, which is why they do not appear in it). The blobs
# were back-projected onto the vase plane the symmetric-pair solve already
# established, and the read CONTROLS on a value it already knew: each spray's
# lowest petal lands within 27 mm of its own vase rim.
#
#   left  spray  269.7 mm wide, 241.5 mm tall, centre +20.0 mm off the vase axis
#   right spray  204.3 mm wide, 219.5 mm tall, centre +18.4 mm off the vase axis
#   petal linear RGB 0.252/0.083/0.101 (L) and 0.302/0.101/0.124 (R)
#   stem  linear RGB 0.028/0.042/0.011 — a deep muted green
#
# And the acceptance test that matters more than any of them: inside its own
# bounding box the target's spray is only 34.5% (L) / 42.9% (R) petal, with
# 45-53% of the box still showing the wall behind. A SPRAY THAT READS AS A SOLID
# BALL IS WRONG EVEN IF ITS SILHOUETTE IS RIGHT, so the build is checked against
# that fraction, not against its own outline.


def _rnd(seed, i):
    """Deterministic pseudo-random in [0,1). Written out rather than taken from
    `random`, because a spray that changes when nothing changed cannot be
    bisected — and this project has spent whole rounds on renders that differed
    for reasons nobody could name."""
    x = (seed * 1103515245 + i * 12345 + 1013904223) & 0x7FFFFFFF
    x ^= x >> 13
    x = (x * 1274126177) & 0x7FFFFFFF
    return (x ^ (x >> 16)) / float(0x7FFFFFFF)


def _unit(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _frame(axis):
    """Orthonormal (u, v, w) with w along axis. The seed vector is swapped near
    the pole so the cross product never degenerates — a flower pointing straight
    up is the common case here, not the edge case."""
    w = _unit(axis)
    seed = (0.0, 0.0, 1.0) if abs(w[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _unit(_cross(seed, w))
    return u, _cross(w, u), w


def _tepal(verts, faces, centre, frame, azim, length, width, curl, seg=6):
    """One lily tepal: a tapered blade that rises, widens and then RECURVES —
    the backward curl is what stops six flat petals reading as a paper daisy."""
    u, v, w = frame
    ca, sa = math.cos(azim), math.sin(azim)
    rad = (u[0] * ca + v[0] * sa, u[1] * ca + v[1] * sa, u[2] * ca + v[2] * sa)
    side = (-u[0] * sa + v[0] * ca, -u[1] * sa + v[1] * ca, -u[2] * sa + v[2] * ca)
    rings = []
    for i in range(seg + 1):
        t = i / seg
        r = length * t
        h = length * (0.20 * math.sin(math.pi * min(t * 1.05, 1.0)) - curl * t * t)
        half = width * math.sin(math.pi * (t ** 0.45)) * (1.0 - 0.10 * t)
        spine = tuple(centre[k] + rad[k] * r + w[k] * h for k in range(3))
        if half <= 0.5:
            rings.append([len(verts)])
            verts.append(spine)
            continue
        ring = []
        for s in (-1.0, 1.0):
            ring.append(len(verts))
            verts.append(tuple(spine[k] + side[k] * half * s for k in range(3)))
        rings.append(ring)
    for lo, hi in zip(rings, rings[1:]):
        if len(lo) == 2 and len(hi) == 2:
            faces.append([lo[0], lo[1], hi[1], hi[0]])
        elif len(lo) == 2:
            faces.append([lo[0], lo[1], hi[0]])
        elif len(hi) == 2:
            faces.append([lo[0], hi[1], hi[0]])


def _tube(verts, faces, path, r0, r1, sides=5):
    """A stem. Thin enough that five sides is honest at this pixel size, and a
    tube rather than a line because a zero-width edge renders as nothing."""
    rings = []
    for i, p in enumerate(path):
        t = i / max(len(path) - 1, 1)
        r = r0 + (r1 - r0) * t
        nxt = path[min(i + 1, len(path) - 1)]
        prv = path[max(i - 1, 0)]
        u, v, _ = _frame(tuple(nxt[k] - prv[k] for k in range(3)) if nxt != prv
                         else (0.0, 0.0, 1.0))
        ring = []
        for s in range(sides):
            a = 2.0 * math.pi * s / sides
            ring.append(len(verts))
            verts.append(tuple(p[k] + (u[k] * math.cos(a) + v[k] * math.sin(a)) * r
                               for k in range(3)))
        rings.append(ring)
    for lo, hi in zip(rings, rings[1:]):
        for s in range(sides):
            t = (s + 1) % sides
            faces.append([lo[s], lo[t], hi[t], hi[s]])


def _leaf(verts, faces, base, axis, azim, length, width, droop, seg=4):
    """A lance-shaped leaf. Added because the FIRST LOOK at the built spray
    beside the reference showed the target's stems carrying dark green leaves and
    ours carrying none — the numeric checks (extent, fill fraction) could not see
    it, because a leaf is neither petal nor background to a magenta mask."""
    u, v, w = _frame(axis)
    ca, sa = math.cos(azim), math.sin(azim)
    rad = (u[0] * ca + v[0] * sa, u[1] * ca + v[1] * sa, u[2] * ca + v[2] * sa)
    side = (-u[0] * sa + v[0] * ca, -u[1] * sa + v[1] * ca, -u[2] * sa + v[2] * ca)
    rings = []
    for i in range(seg + 1):
        t = i / seg
        spine = tuple(base[k] + rad[k] * length * t - w[k] * droop * length * t * t
                      for k in range(3))
        half = width * math.sin(math.pi * (t ** 0.55))
        if half <= 0.4:
            rings.append([len(verts)]); verts.append(spine); continue
        ring = []
        for sgn in (-1.0, 1.0):
            ring.append(len(verts))
            verts.append(tuple(spine[k] + side[k] * half * sgn for k in range(3)))
        rings.append(ring)
    for lo, hi in zip(rings, rings[1:]):
        if len(lo) == 2 and len(hi) == 2:
            faces.append([lo[0], lo[1], hi[1], hi[0]])
        elif len(hi) == 1:
            faces.append([lo[0], lo[1], hi[0]])
        else:
            faces.append([lo[0], hi[1], hi[0]])


def floral_spray(origin, width_mm, height_mm, seed=1, flowers=7, buds=4):
    """A lily spray standing in a vase mouth. PURE — returns
    {"petal": (verts, faces), "stem": (verts, faces)} in mm.

    Two meshes, not one, because petal and stem are two measured colours and a
    single mesh with two slots would make the split a Blender detail instead of
    a spec decision."""
    half = width_mm / 2.0
    pv, pf, sv, sf = [], [], [], []
    n = flowers + buds
    for i in range(n):
        is_bud = i >= flowers
        # spiral the azimuths instead of spacing them evenly: an even fan is the
        # tell of a generated bouquet, and the golden angle is what a real stem
        # arrangement approximates anyway
        az = 2.39996 * i + 0.7 * _rnd(seed, i)
        # buds sit high and tight, open flowers splay low and wide
        rad = half * ((0.30 + 0.70 * _rnd(seed, 100 + i)) * (0.45 if is_bud else 1.0))
        top = height_mm * (0.05 + 0.85 * _rnd(seed, 200 + i))
        if is_bud:
            top = height_mm * (0.80 + 0.20 * _rnd(seed, 300 + i))
        end = (origin[0] + rad * math.cos(az), origin[1] + rad * math.sin(az),
               origin[2] + top)
        # a quadratic bezier so the stem leaves the vase vertically and only then
        # splays — a straight line from the mouth reads as a spike, not a stem
        ctl = (origin[0] + rad * 0.18 * math.cos(az),
               origin[1] + rad * 0.18 * math.sin(az),
               origin[2] + top * 0.62)
        path = []
        for k in range(7):
            t = k / 6.0
            path.append(tuple((1 - t) ** 2 * origin[j] + 2 * (1 - t) * t * ctl[j]
                              + t * t * end[j] for j in range(3)))
        _tube(sv, sf, path, 3.4, 2.0)
        tip = _unit(tuple(path[-1][j] - path[-2][j] for j in range(3)))
        # A LILY LOOKS AT YOU. Aiming each head along its own stem gave a splayed
        # starfish; in the reference every open flower faces roughly out of the
        # frame toward the viewer, which is what a florist arranges and what the
        # camera then sees. Blended rather than snapped, so the heads still fan.
        face = _unit((0.0, -1.0, 0.30))
        b = 0.60 if not is_bud else 0.25
        fr = _frame(tuple(tip[j] * (1 - b) + face[j] * b for j in range(3)))
        # leaves ride the stem, two per, alternating
        for li in range(2):
            lt = 0.45 + 0.28 * li
            k = int(lt * (len(path) - 1))
            _leaf(sv, sf, path[k], _unit(tuple(path[k + 1][j] - path[k - 1][j]
                                               for j in range(3))),
                  2.1 * li + 3.0 * _rnd(seed, 700 + i * 4 + li),
                  height_mm * (0.13 + 0.04 * _rnd(seed, 800 + i * 4 + li)),
                  height_mm * 0.022, 0.35)
        if is_bud:
            _tepal(pv, pf, path[-1], fr, 0.0, height_mm * 0.075,
                   height_mm * 0.020, 0.05, seg=4)
            for j in range(3):
                _tepal(pv, pf, path[-1], fr, 2.0944 * j + 0.4,
                       height_mm * 0.070, height_mm * 0.016, -0.10, seg=4)
            continue
        # A LILY IS A BIG FLOWER. At 0.17 of the spray height the heads came out
        # 41 mm across, and the measurement caught it in a way an outline check
        # never would: our petals landed as SEPARATE connected blobs 36 px wide
        # where the target's spray is one connected mass 111 px wide. The
        # target's own arithmetic says the size -- a 270 mm spray reading as one
        # blob means neighbouring heads touch, so a head must be a real fraction
        # of the spray, not a dot on a stem.
        L = height_mm * (0.21 + 0.05 * _rnd(seed, 400 + i))
        W = L * 0.42
        for j in range(6):
            _tepal(pv, pf, path[-1], fr, 1.0472 * j + 0.25 * _rnd(seed, 500 + i * 8 + j),
                   L, W, 0.17 + 0.06 * _rnd(seed, 600 + i * 8 + j))
        for j in range(5):
            _tepal(sv, sf, path[-1], fr, 1.2566 * j + 0.3,
                   L * 0.34, L * 0.030, -0.55, seg=3)
    return {"petal": (pv, pf), "stem": (sv, sf)}


# -------------------------------------------------------------------- plan ---

def plan(spec):
    """spec -> [placement dict]. PURE. Empty when the spec carries no styling,
    so every earlier round still builds byte-identically."""
    st = spec.get("styling") or {}
    out = []
    pair = st.get("vase_pair")
    if pair:
        # ONE offset, mirrored about the centre box — the relationship the owner's
        # pedestal correction established, applied to the pair he then caught
        # standing unequal. Two independent x values is what let them drift.
        bcx = spec["unit"]["box"].get("cx_mm", 0.0)
        for side, sgn, hk in (("L", -1, "height_L_mm"), ("R", +1, "height_R_mm")):
            out.append({"kind": "lathe", "name": f"vase_{side}", "profile": "VASE",
                        "pos_mm": (bcx + sgn * pair["offset_x_mm"],
                                   pair["y_mm"], pair["z_mm"]),
                        "height_mm": pair[hk], "material": "vase_dark", "cls": "vase"})
    fl = st.get("floral_pair")
    if fl and pair:
        bcx = spec["unit"]["box"].get("cx_mm", 0.0)
        for side, sgn, hk in (("L", -1, "height_L_mm"), ("R", +1, "height_R_mm")):
            d = fl[side]
            # the lean is stored per side AS MEASURED and is NOT mirrored: both
            # sprays sit ~+19 mm toward +x of their own vase axis, which is what
            # two independently arranged bunches in one room actually do, and
            # mirroring it would be the model asserting a symmetry the image
            # denies. (The vases themselves ARE mirrored — that is a joinery
            # relationship; this is not.)
            out.append({"kind": "spray", "name": f"floral_{side}",
                        "pos_mm": (bcx + sgn * pair["offset_x_mm"] + d["lean_x_mm"],
                                   pair["y_mm"], pair["z_mm"] + pair[hk]),
                        "width_mm": d["width_mm"], "height_mm": d["height_mm"],
                        "seed": d.get("seed", 1), "flowers": d.get("flowers", 7),
                        "buds": d.get("buds", 4),
                        "material": "lily_pink", "stem_material": "stem_green",
                        "cls": "floral"})
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

        if p["kind"] == "spray":
            parts = floral_spray(p["pos_mm"], p["width_mm"], p["height_mm"],
                                 seed=p["seed"], flowers=p["flowers"], buds=p["buds"])
            for part, matkey in (("petal", p["material"]), ("stem", p["stem_material"])):
                verts, faces = parts[part]
                me = bpy.data.meshes.new(f"SM_TRN001_{p['name']}_{part}")
                me.from_pydata([(x * G.MM, y * G.MM, z * G.MM) for x, y, z in verts],
                               [], faces)
                me.validate()
                for poly in me.polygons:
                    poly.use_smooth = True
                if materials and matkey in materials:
                    me.materials.append(materials[matkey])
                ob = bpy.data.objects.new(f"SM_TRN001_{p['name']}_{part}", me)
                col.objects.link(ob)
                made.append(ob)
            print(f"  STYLING: {p['name']} spray {p['width_mm']:.0f}x{p['height_mm']:.0f}mm "
                  f"{p['flowers']}+{p['buds']} heads, "
                  f"{len(parts['petal'][1])} petal faces / {len(parts['stem'][1])} stem faces")
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
