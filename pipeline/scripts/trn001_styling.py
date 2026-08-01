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


def _cap(verts, faces, ring, flip):
    """Close a ring with a FAN to its own centroid, not with one face.

    Every generator here used to cap with `faces.append(list(ring))`, which on a
    32-segment lathe is a 32-gon — and pipeline/CLAUDE.md's export law forbids
    n-gons outright ("booleans produce n-gons that a SketchUp recipient will
    see"). We were producing them without a boolean in sight, while a probe
    measured ten of Blender's own organic tools at zero each. Triangles are
    allowed; a fan gives triangles and a centre vertex the cap can shade around."""
    if len(ring) < 3:
        return
    cx = sum(verts[i][0] for i in ring) / len(ring)
    cy = sum(verts[i][1] for i in ring) / len(ring)
    cz = sum(verts[i][2] for i in ring) / len(ring)
    c = len(verts)
    verts.append((cx, cy, cz))
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        faces.append([c, b, a] if flip else [c, a, b])


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
        _cap(verts, faces, rings[0], True)
    if len(rings[-1]) > 1:
        _cap(verts, faces, rings[-1], False)
    return verts, faces


# ------------------------------------------------------------------ figure ---
#
# THE SEATED FIGURES, BUILT. Round 5 refused to model them and round 10 upheld
# that refusal; the owner asked "ไหนพระล่ะ" and he is right, so the refusal is
# withdrawn and the reasoning corrected rather than quietly dropped. Decision
# (ข)'s words are "religious statuary used respectfully as-is" — that is a rule
# about ASSETS, saying do not distort a scanned image to fit, and it never said
# do not model one. A prayer room with no image in it is not a reproduction, and
# every Thai visualiser puts one in. Refusing was over-caution wearing the
# costume of respect, and it cost two rounds.
#
# Built the way everything else in this lane is built: MEASURED FIRST. The gilt
# is found by chroma inside a tight window and thresholded against that window's
# own background (the first, whole-frame attempt lit up the entire oak room,
# because wood is also R>G>B — the discriminator that works is SATURATION, not
# hue order), then back-projected onto the plane each figure stands on:
#
#   centre figure   total height 373 mm (flame tip z 1237 over a box top of 864)
#                   base 165 wide, lap 113, head 63, flame 21
#   gilt            linear RGB mean 0.351/0.207/0.074, p95 0.671/0.540/0.258
#                   — R/G 1.24 and G/B 2.09 at the highlight, i.e. polished gold
#
# The posture is ปางมารวิชัย (Bhumisparsha, subduing Mara), which is what the
# reference plainly shows and the most common form on a Thai home altar: right
# hand down over the right knee, left hand resting in the lap, legs crossed,
# robe over the left shoulder leaving the right bare, and a tall flame ushnisha.
# The right arm is a separate loft because it is the one part of the silhouette
# that a body-of-revolution cannot produce, and at ~200 px it is exactly what
# distinguishes this posture from any other.


def loft(rings, cx, cy, z0, height, seg=24):
    """Elliptical loft. rings = [(z_frac, half_x, half_y, dx_frac)] in FRACTIONS
    of the total height, so one canon of proportions serves every size. PURE.

    Not a lathe: a seated figure is wider than it is deep at the lap and the
    head leans forward of the base, so both the cross-section and the axis have
    to vary. A ring with half_x <= 0 collapses to a pole."""
    verts, ringidx = [], []
    for zf, hx, hy, dx in rings:
        z = z0 + zf * height
        ax, ay = hx * height, hy * height
        x0 = cx + dx * height
        if ax <= 1e-6 or ay <= 1e-6:
            ringidx.append([len(verts)])
            verts.append((x0, cy, z))
            continue
        r = []
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            r.append(len(verts))
            verts.append((x0 + ax * math.cos(a), cy + ay * math.sin(a), z))
        ringidx.append(r)
    faces = []
    for lo, hi in zip(ringidx, ringidx[1:]):
        if len(lo) == 1 and len(hi) == 1:
            continue
        if len(lo) == 1:
            faces.extend([[lo[0], hi[i], hi[(i + 1) % len(hi)]] for i in range(len(hi))])
        elif len(hi) == 1:
            faces.extend([[lo[i], lo[(i + 1) % len(lo)], hi[0]] for i in range(len(lo))])
        else:
            n = len(lo)
            faces.extend([[lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]] for i in range(n)])
    if len(ringidx[0]) > 1:
        _cap(verts, faces, ringidx[0], True)
    if len(ringidx[-1]) > 1:
        _cap(verts, faces, ringidx[-1], False)
    return verts, faces


def rect_loft(rings, cx, cy, z0, height, corner=0.12):
    """Lofted rectangular stack with lightly cut corners. rings = [(z_frac,
    half_x, half_y)] in fractions of the total height. PURE.

    The figure's base is a stepped pedestal with sharp horizontal ledges, and an
    elliptical loft physically cannot make a ledge — the first cut built it as a
    body of revolution and it read as a soft blob under the figure. `corner`
    clips the plan corners so the gold catches an edge highlight instead of a
    hard black seam."""
    verts, idx = [], []
    for zf, hx, hy in rings:
        z = z0 + zf * height
        ax, ay = hx * height, hy * height
        if ax <= 1e-6 or ay <= 1e-6:
            idx.append([len(verts)])
            verts.append((cx, cy, z))
            continue
        c = corner * min(ax, ay)
        pts = [(ax - c, ay), (ax, ay - c), (ax, -ay + c), (ax - c, -ay),
               (-ax + c, -ay), (-ax, -ay + c), (-ax, ay - c), (-ax + c, ay)]
        ring = []
        for dx, dy in pts:
            ring.append(len(verts))
            verts.append((cx + dx, cy + dy, z))
        idx.append(ring)
    faces = []
    for lo, hi in zip(idx, idx[1:]):
        if len(lo) == 1 and len(hi) == 1:
            continue
        if len(lo) == 1:
            faces.extend([[lo[0], hi[i], hi[(i + 1) % len(hi)]] for i in range(len(hi))])
        elif len(hi) == 1:
            faces.extend([[lo[i], lo[(i + 1) % len(lo)], hi[0]] for i in range(len(lo))])
        else:
            n = len(lo)
            faces.extend([[lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]] for i in range(n)])
    if len(idx[0]) > 1:
        _cap(verts, faces, idx[0], True)
    if len(idx[-1]) > 1:
        _cap(verts, faces, idx[-1], False)
    return verts, faces


# THE BASE — ฐานชุกชี, a stepped pedestal, rectangular in plan. (z_frac, half_x,
# half_y) in fractions of the figure's TOTAL height. It carries the bottom 22%,
# which is what the reference shows: this is a tall base, not a foot.
BASE_CANON = [
    (0.000, 0.230, 0.185),
    (0.030, 0.230, 0.185),   # plinth, full width
    (0.036, 0.246, 0.198),   # the lip that catches the light
    (0.052, 0.246, 0.198),
    (0.060, 0.212, 0.171),   # step in
    (0.092, 0.196, 0.158),   # concave moulding — บัวคอด
    (0.118, 0.181, 0.146),
    (0.132, 0.196, 0.158),   # and back out
    (0.150, 0.222, 0.179),
    (0.163, 0.238, 0.192),   # top ledge
    (0.180, 0.238, 0.192),
    (0.188, 0.208, 0.168),   # the seat the figure sits on
    (0.205, 0.200, 0.162),
]

# THE FIGURE — (z_frac, half_x, half_y, dx_frac). Widened throughout: the first
# cut ran the lap at half_x 0.151 of total height and the reference's lap is
# nearly as wide as its base, at about 0.22. The head was enlarged and the flame
# shortened for the same reason — the silhouette has to read as a seated body,
# and at 0.35 width-to-height it read as a spire.
FIGURE_CANON = [
    (0.196, 0.150, 0.128, 0.000),   # rises out of the base
    (0.230, 0.206, 0.170, 0.004),
    (0.268, 0.228, 0.185, 0.008),
    (0.300, 0.232, 0.188, 0.012),   # knees — a SHELF, not a slope: the first cut
    (0.316, 0.230, 0.186, 0.014),   # sloped from here to the waist over a third
    (0.330, 0.196, 0.150, 0.016),   # of the figure and read as a cone
    (0.344, 0.150, 0.112, 0.018),
    (0.362, 0.122, 0.094, 0.020),
    (0.400, 0.098, 0.078, 0.022),
    (0.430, 0.090, 0.072, 0.024),   # waist
    (0.470, 0.104, 0.080, 0.026),
    (0.505, 0.132, 0.098, 0.027),   # shoulders — square, and wider than the head
    (0.545, 0.138, 0.101, 0.028),
    (0.566, 0.120, 0.090, 0.028),
    (0.580, 0.072, 0.060, 0.028),
    (0.590, 0.038, 0.036, 0.028),   # NECK — absent from the first cut, which is
    (0.606, 0.038, 0.036, 0.028),   # why the head merged into the shoulders
    (0.622, 0.056, 0.054, 0.028),
    (0.646, 0.068, 0.066, 0.028),   # jaw
    (0.678, 0.072, 0.070, 0.028),   # head — widest. The previous 0.098 made
    # the head 42% of the lap where the reference reads about 30%, and a head
    # that size turns the whole silhouette into an onion whatever else is right.
    (0.706, 0.069, 0.067, 0.028),
    (0.734, 0.058, 0.056, 0.028),   # crown, where the curls sit
    (0.758, 0.044, 0.043, 0.028),
    (0.778, 0.034, 0.033, 0.028),   # ushnisha
    (0.798, 0.026, 0.025, 0.028),
    (0.816, 0.019, 0.018, 0.028),   # the flame springs — slender, and SHORT:
    (0.848, 0.016, 0.015, 0.028),   # the first cut's bulbous finial was most of
    (0.888, 0.011, 0.010, 0.028),   # what made the silhouette read as a stupa
    (0.936, 0.006, 0.005, 0.028),
    (1.000, 0.000, 0.000, 0.028),   # tip
]

# The right arm, hanging from the shoulder down over the right knee — the one
# silhouette feature that names ปางมารวิชัย and that a body of revolution
# cannot make. Widened with the rest so it clears the torso and reads.
ARM_CANON = [
    (0.532, 0.052, 0.050, 0.120),
    (0.480, 0.054, 0.052, 0.162),
    (0.424, 0.052, 0.050, 0.192),
    (0.372, 0.048, 0.046, 0.208),
    (0.332, 0.036, 0.038, 0.218),
    (0.306, 0.038, 0.042, 0.214),   # the hand, over the right knee
    (0.290, 0.026, 0.032, 0.204),
]


def buddha_figure(origin, height_mm, mirror=False):
    """A seated gilt image on its stepped base. PURE — returns
    {"gilt": (verts, faces)} in mm. `mirror` flips the arm to the other side."""
    cx, cy, z0 = origin
    sgn = -1.0 if mirror else 1.0
    base = rect_loft(BASE_CANON, cx, cy, z0, height_mm)
    verts, faces = [], []
    for canon, seg in ((FIGURE_CANON, 24), (ARM_CANON, 10)):
        rings = [(zf, hx, hy, dx * sgn) for zf, hx, hy, dx in canon]
        v, f = loft(rings, cx, cy, z0, height_mm, seg=seg)
        off = len(verts)
        verts.extend(v)
        faces.extend([[i + off for i in face] for face in f])
    # TWO MESHES, because they want opposite shading. The base is a stepped
    # pedestal whose whole character is its ledges, and smooth shading rounded
    # every one of them away; the body is cast and polished and genuinely is
    # smooth. One answer for both was wrong for half the object.
    return {"gilt": (verts, faces), "gilt_flat": base}


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




# An acquired figure must be a BODY, not a relief. Two numbers, because either
# alone can be argued with: how deep it is against how wide, and whether that
# depth CHANGES down its height. A real seated figure is nearly as deep as it is
# wide at the lap and narrows toward the head; an extruded outline holds one
# depth all the way up. th_a measured 0.29 and 37% and shipped anyway, because
# it was only ever looked at from the front.
FIGURE_MIN_DEPTH_RATIO = 0.45
FIGURE_MIN_DEPTH_VARIATION = 0.25


def flatness(points, bands=10):
    """(depth/width, depth variation) for a world-space point cloud. PURE."""
    if len(points) < 8:
        return 0.0, 0.0
    z0 = min(p[2] for p in points)
    z1 = max(p[2] for p in points)
    if z1 - z0 < 1e-9:
        return 0.0, 0.0
    depths, widths = [], []
    for i in range(bands):
        a = z0 + (z1 - z0) * i / bands
        b = z0 + (z1 - z0) * (i + 1) / bands
        band = [p for p in points if a <= p[2] < b]
        if len(band) < 4:
            continue
        widths.append(max(p[0] for p in band) - min(p[0] for p in band))
        depths.append(max(p[1] for p in band) - min(p[1] for p in band))
    if not depths or max(depths) <= 0 or max(widths) <= 0:
        return 0.0, 0.0
    return (max(depths) / max(widths),
            (max(depths) - min(depths)) / max(depths))


def _asset_figure_path(slug):
    """A 3D Warehouse model in the (gitignored, non-CC0) warehouse cache."""
    return os.path.join(REPO, "assets", "shared", "warehouse", slug, f"{slug}.glb")


def build_asset_figure(p, materials=None):
    """Import a bought/downloaded figure, CUT it, scale it, place it.

    Returns the objects made. Kept separate from the CC0 asset path in
    build_styling because the licence, the cache and the mining step are all
    different — Poly Haven is CC0 and arrives as one clean object, 3D Warehouse
    is free-to-use-not-redistribute and arrives as somebody's whole scene."""
    import bmesh
    import bpy

    import trn001_geom as G

    path = _asset_figure_path(p["slug"])
    if not os.path.exists(path):
        print(f"  STYLING: {p['name']} asset {p['slug']} not in the warehouse "
              f"cache — SKIPPED (run pipeline/scripts/warehouse.py fetch)")
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)        # headless-safe, not a geometry op
    objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in objs if o.type == "MESH" and len(o.data.polygons)]
    if not meshes:
        print(f"  STYLING: {p['name']} <- {p['slug']} imported no geometry — SKIPPED")
        return []

    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices]
    z0, z1 = min(zs), max(zs)
    cut = z0 + (z1 - z0) * float(p.get("z_keep", 0.0))

    # drop everything below the cut, in world space, on each mesh
    for o in meshes:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        mw = o.matrix_world
        doomed = [f for f in bm.faces
                  if sum(((mw @ v.co).z for v in f.verts)) / len(f.verts) < cut]
        if doomed:
            bmesh.ops.delete(bm, geom=doomed, context="FACES")
        bmesh.ops.delete(
            bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()

    bpy.context.view_layer.update()
    live = [o for o in meshes if len(o.data.polygons)]
    if not live:
        print(f"  STYLING: {p['name']} z_keep cut removed everything — SKIPPED")
        return objs

    # IS IT A BODY OR A COIN? Asserted on the CUT geometry, because a relief
    # mounted on a solid pedestal would pass the check on the whole model.
    pts = [tuple(o.matrix_world @ v.co) for o in live for v in o.data.vertices]
    ratio, variation = flatness(pts)
    if ratio < FIGURE_MIN_DEPTH_RATIO or variation < FIGURE_MIN_DEPTH_VARIATION:
        raise SystemExit(
            f"STYLING: {p['name']} <- {p['slug']} is FLAT — depth/width "
            f"{ratio:.2f} (min {FIGURE_MIN_DEPTH_RATIO}) and depth varies "
            f"{variation:.0%} down its height (min "
            f"{FIGURE_MIN_DEPTH_VARIATION:.0%}). That is an extruded outline "
            f"with a photograph on it, not a statue, and it reads as a coin "
            f"from every angle except the one it was chosen from.")
    zs = [(o.matrix_world @ v.co).z for o in live for v in o.data.vertices]
    xs = [(o.matrix_world @ v.co).x for o in live for v in o.data.vertices]
    ys = [(o.matrix_world @ v.co).y for o in live for v in o.data.vertices]
    native_mm = (max(zs) - min(zs)) / G.MM
    if native_mm < 1.0:
        print(f"  STYLING: {p['name']} degenerate after cut — SKIPPED")
        return objs
    k = p["height_mm"] / native_mm
    ctr = ((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0, min(zs))

    roots, seen = [], set()
    for o in live:
        r = o
        while r.parent is not None:
            r = r.parent
        if r.name not in seen:
            seen.add(r.name)
            roots.append(r)
    tgt = tuple(c * G.MM for c in p["pos_mm"])
    for r in roots:
        r.scale = tuple(s * k for s in r.scale)
        r.location = (r.location.x * k + tgt[0] - ctr[0] * k,
                      r.location.y * k + tgt[1] - ctr[1] * k,
                      r.location.z * k + tgt[2] - ctr[2] * k)
    for o in live:
        o.name = f"SM_TRN001_{p['name']}"
        # An acquired asset may keep its own materials or wear ours. Ours is a
        # MEASURED gilt (linear 0.85/0.63/0.26, metallic, roughness 0.18, read
        # off the target's own figures); a downloaded photogrammetry texture
        # carries someone else's lighting baked into it and fights this room's.
        if p.get("use_our_material") and materials and p["material"] in materials:
            o.data.materials.clear()
            o.data.materials.append(materials[p["material"]])

    # ASSERT the scale rather than trust it (pipeline/CLAUDE.md)
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ v.co).z for o in live for v in o.data.vertices]
    got = (max(zs) - min(zs)) / G.MM
    if abs(got - p["height_mm"]) > 2.0:
        raise SystemExit(f"STYLING: {p['name']} asked for {p['height_mm']:.0f}mm "
                         f"and got {got:.1f}mm — scale assertion FAILED")
    # R8 CUTS BOTH WAYS. The figure is acquired because free form cannot be
    # measured; its BASE is a stepped pedestal — boxes with ledges, recoverable
    # from measurement — so the base is BUILT, from the same BASE_CANON the
    # hand-built figure used. The reference shows the image standing on a gilt
    # tiered base and this asset has none.
    if p.get("base_h_mm"):
        import bpy as _b
        bh = float(p["base_h_mm"])
        bx, by, bz = p["pos_mm"]
        verts, faces_b = rect_loft(BASE_CANON, bx, by, bz, bh / 0.205)
        keep = bz + bh
        verts = [(x, y, min(z, keep)) for x, y, z in verts]
        me = _b.data.meshes.new(f"SM_TRN001_{p['name']}_base")
        me.from_pydata([(x * G.MM, y * G.MM, z * G.MM) for x, y, z in verts],
                       [], faces_b)
        me.validate()
        if materials and p["material"] in materials:
            me.materials.append(materials[p["material"]])
        ob = _b.data.objects.new(f"SM_TRN001_{p['name']}_base", me)
        col_ = _b.context.scene.collection
        col_.objects.link(ob)
        objs.append(ob)
        # and the figure stands ON it, not through it
        for r in roots:
            r.location = (r.location.x, r.location.y, r.location.z + bh * G.MM)

    faces = sum(len(o.data.polygons) for o in live)
    print(f"  STYLING: {p['name']} <- warehouse/{p['slug']} native "
          f"{native_mm:.0f}mm -> {got:.0f}mm (x{k:.4f}), z_keep "
          f"{p.get('z_keep', 0.0):.2f}, {faces} faces after the cut")
    return objs


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
                        "buds": d.get("buds", 4), "subsurf": d.get("subsurf", 0),
                        "material": "lily_pink", "stem_material": "stem_green",
                        "cls": "floral"})
    for fg in st.get("figures", []):
        out.append({"kind": "figure_asset" if fg.get("slug") else "figure",
                    "name": fg["name"], "slug": fg.get("slug"),
                    "z_keep": fg.get("z_keep", 0.0),
                    "use_our_material": bool(fg.get("use_our_material")),
                    "base_h_mm": fg.get("base_h_mm", 0.0),
                    "pos_mm": (fg["x_mm"], fg["y_mm"], fg["z_mm"]),
                    "height_mm": fg["height_mm"], "mirror": bool(fg.get("mirror")),
                    "subsurf": fg.get("subsurf", 0),
                    "material": "gilt", "cls": "figure"})
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

        if p["kind"] == "figure_asset":
            made.extend(build_asset_figure(p, materials))
            continue

        if p["kind"] == "figure":
            parts = buddha_figure(p["pos_mm"], p["height_mm"], mirror=p["mirror"])
            nf = 0
            for part, smooth in (("gilt", True), ("gilt_flat", False)):
                verts, faces = parts[part]
                nf += len(faces)
                me = bpy.data.meshes.new(f"SM_TRN001_{p['name']}_{part}")
                me.from_pydata([(x * G.MM, y * G.MM, z * G.MM) for x, y, z in verts],
                               [], faces)
                me.validate()
                for poly in me.polygons:
                    poly.use_smooth = smooth
                if materials and p["material"] in materials:
                    me.materials.append(materials[p["material"]])
                ob = bpy.data.objects.new(f"SM_TRN001_{p['name']}_{part}", me)
                # SUBDIVISION. The 2026-07-30 ground-truth study measured every
                # pro .blend file using it and ours at SUBSURF 0, and a probe
                # (2026-08-01) settled the rest: it is reachable from the DATA
                # API alone, it is deterministic, it costs 41 ms on this figure,
                # it takes it from 759 faces to 12,176 — and it REMOVES the 3
                # n-gons our own hand-built loft creates, which the export law
                # forbids. Five rounds of hand-tuning rings could not do what
                # two lines of modifier do, and that is the finding.
                # ...AND ONLY ON THE CAST BODY. The first cut applied it to
                # both meshes and the render refuted it on sight: subdivision
                # rounds away every edge you MEANT to be sharp, so it erased the
                # stepped pedestal's ledges — the exact thing flat shading had
                # just been introduced to save. The probe proved the modifier is
                # REACHABLE; it did not prove it is free, and a number is not a
                # look. The base is already a separate mesh for the shading
                # split, so the fix is the same boundary: smooth what is cast,
                # leave sharp what is cut.
                if p.get("subsurf") and smooth:
                    sub = ob.modifiers.new("subsurf", "SUBSURF")
                    sub.levels = sub.render_levels = int(p["subsurf"])
                col.objects.link(ob)
                made.append(ob)
            print(f"  STYLING: {p['name']} seated figure {p['height_mm']:.0f}mm "
                  f"({nf} faces, arm {'left' if p['mirror'] else 'right'})")
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
                if p.get("subsurf"):
                    sub = ob.modifiers.new("subsurf", "SUBSURF")
                    sub.levels = sub.render_levels = int(p["subsurf"])
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
