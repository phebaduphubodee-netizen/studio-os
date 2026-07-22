"""
softgoods.py — ELEMENT 8 (PRJ-2026-002): the COMPLIANT-SURFACE vocabulary.
Pure Python (NO bpy), metres in/out, deterministic, unit-tested.

WHY THIS MODULE EXISTS (2026-07-22, element8-styling DD ground phase)
--------------------------------------------------------------------
The owner's verdict on six rendered frames was "ยังดูไม่มี style", and before that
"ไม่มี design เลยแข็งมาก" and "เหลี่ยม" (rigid / boxy). The DD's ground phase looked at
the actual pixels and named ONE mechanism behind all of it:

    NOTHING IN THIS ROOM DEFORMS.

Every soft object in the suite was modelled with JOINERY's primitive — a bevelled box
with a level hem. The coverlet is a single flat plane with one seam and a uniform 60mm
radius on every edge; the two pillows are identical flat slabs at identical height; the
sheers corrugate at a perfectly uniform pitch; the rug is a zero-thickness plane with a
knife-cut edge. That is not several defects, it is one defect with one cause, and it is
the literal physical referent of the words the owner used. It also explains why THREE
previous "make it softer" passes failed (bevels -> floating base -> draped coverlet,
9d15bfc): each one was still a box with rounder corners. A bevel radius is not drape.

So element 8 does not begin by adding objects. It begins by giving the codebase the
primitive class it never had: surfaces that GATHER, SAG, CREASE and HANG. Objects come
second, and they are built FROM this vocabulary — which is why the same four functions
carry the bed's fall, the garments on the brass rails, the folded stacks on the open
shelves and the pillows at the head.

THE PHYSICS THAT MAKES CLOTH READ IN RAW CYCLES (no texture, no beauty pass)
---------------------------------------------------------------------------
Hanging fabric has one unmistakable signature: it is CONSTRAINED AT THE TOP AND FREE AT
THE BOTTOM. So the crease amplitude must GROW downward from ~0 at the suspension line,
the hem must wander in z (never level), and the fold pitch must be irregular (a uniform
pitch is what makes the existing sheers read as fluted acrylic panel). Every generator
here obeys those three rules, and shading is left SMOOTH so the undulation renders as a
soft gradient rather than facets.

DETERMINISM
-----------
Irregularity here is never random. `dev()` is a golden-ratio low-discrepancy sequence:
deterministic, unit-testable, never repeats and never clumps. Randomness would be mess;
a bounded derived deviation is a stylist's controlled irregularity. The same spec must
always build the same room — a render that differs run-to-run cannot be a structural
control for the beauty pass.

CONTRACT
--------
Every generator returns (verts, faces): verts = [(x, y, z), ...] in LOCAL metres with
the piece's own origin, faces = [(i, j, k, l), ...] quads (never n-gons — the export law
in pipeline/CLAUDE.md: n-gons are what a SketchUp recipient sees). The consumer
(build_room._smooth_mesh_obj) does from_pydata + smooth shading, data API only.
"""

import math

PHI_INV = 0.6180339887498949      # golden-ratio conjugate — low-discrepancy, never clumps
_SALT = 0.7548776662466927        # 2nd-dimension additive recurrence (plastic constant)

# A hem that wanders less than this reads as a machine cut; more than this reads as
# damage. Bounds, not magic: every caller passes its own fraction of these.
MAX_HEM_WANDER = 0.045            # m, peak-to-peak z wander at a free hem
MIN_SEGMENTS = 3                  # below this a "gathered" ribbon cannot show a fold

# `garment` does not span exactly `width`: the body flares below the waist and the whole
# piece may lean by `sway`. A caller sizing a garment to fit a carcass must bound the
# ACTUAL span, so the factor is published here instead of being re-derived (wrongly) at
# each call site. span <= width * GARMENT_FLARE + 2 * sway.
GARMENT_FLARE = 1.03


def _fail(msg):
    raise ValueError(f"softgoods: {msg}")


def dev(i, bound, salt=0):
    """Deterministic bounded deviation in [-bound, +bound] for index `i`.

    Golden-ratio additive recurrence: successive i are maximally separated, so a run of
    garments along a rail never falls into a visible beat pattern (the vault's own
    amateur red flag is "placing identical, repeating 3D assets across a scene" —
    qa-dimensions.md:309-310 — and a naive sin(i) does exactly that). `salt` picks an
    independent stream so a piece's x-deviation and its z-deviation never correlate."""
    t = ((i + 1) * PHI_INV + salt * _SALT) % 1.0
    return bound * (2.0 * t - 1.0)


def _crease(u, i_salt, waves):
    """Sum of `waves` = ((freq, amp), ...) sampled at perimeter fraction u, phase-offset
    per stream. Multi-wavelength on purpose: ONE frequency is a corrugation (the current
    sheers), several incommensurate ones read as cloth."""
    s = 0.0
    for k, (f, a) in enumerate(waves):
        ph = 2.0 * math.pi * (((k + 1) * PHI_INV + i_salt * _SALT) % 1.0)
        s += a * math.sin(2.0 * math.pi * f * u + ph)
    return s


def _grid_faces(nu, nv, wrap_u=False):
    """Quad indices for an (nu+1) x (nv+1) vertex lattice laid out v-major."""
    faces = []
    span = nu if wrap_u else nu
    for i in range(span):
        i2 = (i + 1) % (nu + 1) if wrap_u else i + 1
        for j in range(nv):
            a = i * (nv + 1) + j
            b = i2 * (nv + 1) + j
            faces.append((a, b, b + 1, a + 1))
    return faces


# ---------------------------------------------------------------------------
# 1. DRAPE SKIRT — the bed's fall, and any fabric that hangs off an edge.
# ---------------------------------------------------------------------------

def drape_skirt(w, d, drop, top_z=0.0, nu_per_m=40, nv=8,
                fold=0.020, hem_wander=0.018, sag=0.010, salt=0):
    """A gathered fabric skirt hanging around a w x d rectangle, from `top_z` down `drop`.

    THIS IS THE ELEMENT'S KEYSTONE. The near face of the bed is the single largest area
    in both frames the owner judges from, and it is currently one bevelled plane. Here it
    becomes a textile: the crease amplitude grows from 0 at the suspension line to `fold`
    at the free hem (constrained-top / free-bottom, the signature of hanging cloth), the
    fold pitch is multi-wavelength so it never corrugates, and the hem wanders in z so it
    is never level. `sag` dips the whole hem slightly at the middle of each long run,
    which is what a cloth does between two corners.

    Returns (verts, faces) with the rectangle's SW corner at local (0,0)."""
    if w <= 0 or d <= 0:
        _fail(f"drape_skirt: degenerate footprint {w}x{d}")
    if drop <= 0:
        _fail(f"drape_skirt: drop must be > 0 (got {drop})")
    if hem_wander > MAX_HEM_WANDER:
        _fail(f"drape_skirt: hem_wander {hem_wander} exceeds MAX_HEM_WANDER "
              f"{MAX_HEM_WANDER} — that is damage, not drape")
    perim = 2.0 * (w + d)
    nu = max(MIN_SEGMENTS * 4, int(round(perim * nu_per_m)))

    def wander(u):
        """SPATIALLY SMOOTH hem variation.

        The first cut used dev(i) here and the render showed why that is wrong: dev is a
        low-discrepancy sequence, so ADJACENT stations get maximally DIFFERENT values —
        exactly the property that makes it good for choosing garment widths and exactly
        the property that turns a hem into a sawtooth. In pixels it read as torn
        cardboard, not cloth. A hem is a continuous curve along the run, so its variation
        must be low-FREQUENCY, not per-station noise."""
        return _crease(u, salt + 31, ((1.0, 0.55), (2.0, 0.30), (3.0, 0.15)))

    # perimeter parameterisation: walk the rectangle, returning (x, y, outward normal)
    def on_perimeter(t):
        s = (t % 1.0) * perim
        if s <= w:
            return s, 0.0, (0.0, -1.0)                      # south edge, normal -y
        s -= w
        if s <= d:
            return w, s, (1.0, 0.0)                         # east edge
        s -= d
        if s <= w:
            return w - s, d, (0.0, 1.0)                     # north edge
        s -= w
        return 0.0, d - s, (-1.0, 0.0)                      # west edge

    # FOLD PITCH IS PHYSICAL, not a count. Specifying "13 cycles per perimeter" put the
    # folds 615mm apart on this bed (perimeter ~8.3m) — far too wide to read as fabric;
    # the render showed flat panels with a wavy edge. Real hanging cloth folds every
    # ~60-160mm, so the frequencies are solved FROM the perimeter to land in that band and
    # are rounded to whole cycles so the pattern still closes seamlessly around the loop.
    def cycles_for(wavelength_m):
        return max(2.0, float(round(perim / wavelength_m)))

    waves = ((cycles_for(0.170), 0.46), (cycles_for(0.105), 0.33),
             (cycles_for(0.075), 0.21))
    verts = []
    for i in range(nu + 1):
        u = i / float(nu)
        px, py, (nx, ny) = on_perimeter(u)
        c = _crease(u, salt, waves)
        # hem wander + a gentle sag toward the middle of each run
        hw = hem_wander * wander(u)
        sg = sag * math.sin(math.pi * ((u * 2.0) % 1.0))
        for j in range(nv + 1):
            v = j / float(nv)
            amp = fold * (v ** 1.6)                          # 0 at the top, max at the hem
            ox, oy = nx * amp * c, ny * amp * c
            z = top_z - drop * v - (hw + sg) * (v ** 2)
            verts.append((px + ox, py + oy, z))
    return verts, _grid_faces(nu, nv, wrap_u=True)


# ---------------------------------------------------------------------------
# 2. GARMENT — what hangs on a brass rail.
# ---------------------------------------------------------------------------

def garment(width, drop, depth=0.085, shoulder=0.62, nu=11, nv=7,
            fold=0.014, hem_wander=0.016, sway=0.010, salt=0):
    """One hanging garment as a closed lofted shell: a narrow angled SHOULDER line at the
    top opening out to a fuller body, creases that grow downward, an irregular hem, and a
    small lateral `sway` so a rail of them never reads as a picket fence.

    `shoulder` is the shoulder width as a fraction of `width`. Local origin is the
    garment's top-centre; +z is up, so the body occupies z in [-drop, 0].

    Built as a closed elliptical loft (nu stations around, nv rings down) rather than a
    box: a garment seen from the side is a soft lens, and a box on a rail is exactly the
    "beveled slab" reading this module exists to end."""
    if width <= 0 or drop <= 0 or depth <= 0:
        _fail(f"garment: degenerate {width}x{depth} drop {drop}")
    if not 0.2 <= shoulder <= 1.0:
        _fail(f"garment: shoulder fraction {shoulder} outside 0.2..1.0")
    waves = ((2.0, 0.5), (5.0, 0.33), (9.0, 0.24))
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)                                    # 0 at shoulder, 1 at hem
        # width profile: shoulder -> full body over the top ~35%, then a slight flare
        t = min(v / 0.35, 1.0)
        wf = shoulder + (1.0 - shoulder) * (t * t * (3 - 2 * t))     # smoothstep
        wf += 0.06 * max(v - 0.5, 0.0)                       # a little flare below the waist
        rx = 0.5 * width * wf
        # THE SHOULDER CAP. The first render put the garments' full thickness right up to
        # the top ring, so each one presented a flat-topped rectangular strip to the
        # camera and the rail read as a row of paint swatches. A garment over a hanger
        # narrows to a ROUNDED RIDGE at the shoulder line and only reaches full body a
        # third of the way down — that curve is most of what says "clothing" when the
        # wardrobe is seen from the front and every garment is edge-on.
        ry = 0.5 * depth * (0.22 + 0.78 * min(v / 0.34, 1.0) ** 0.7)
        sw = sway * (v ** 1.5) * dev(0, 1.0, salt + 3)       # whole garment leans a touch
        hw = dev(j, hem_wander, salt + 2) if j == nv else 0.0
        for i in range(nu + 1):
            u = i / float(nu)
            a = 2.0 * math.pi * u
            amp = fold * (v ** 1.5)
            c = _crease(u, salt, waves)
            x = rx * math.cos(a) + sw
            y = ry * math.sin(a) + amp * c * (1.0 if math.sin(a) >= 0 else -1.0)
            z = -drop * v + hw
            verts.append((x, y, z))
    return verts, _loft_faces(nv, nu)


def _loft_faces(nv, nu):
    """Quads for an (nv+1) ring x (nu+1) station loft, closing the ring in u."""
    faces = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = (j + 1) * (nu + 1) + i + 1
            e = (j + 1) * (nu + 1) + i
            faces.append((a, b, c, e))
    return faces


def hanger(width, hook_r=0.015, bar_drop=0.030, salt=0):
    """A hanger silhouette above a garment's shoulder: a shoulder bar + a hook.

    Returns (verts, faces) with origin at the RAIL centre; the bar sits `bar_drop` below
    the rail and the hook rises to meet it. Small, but the repeated hook profile along a
    rail is the visual signature that says 'wardrobe' — without it, garments read as
    sheets pegged on a line (DD ground: 'Hangers themselves')."""
    if width <= 0:
        _fail(f"hanger: degenerate width {width}")
    hw = width * 0.5
    z0 = -bar_drop
    t = 0.0035                               # wire thickness — a hanger is WIRE. At 6mm,
    #                                          nine of them per rail rendered as a band of
    #                                          black sticks that dominated the frame.
    verts, faces = [], []

    def bar(x0, y0, z0_, dx, dy, dz):
        b = len(verts)
        for sx in (0.0, dx):
            for sy in (0.0, dy):
                for sz in (0.0, dz):
                    verts.append((x0 + sx, y0 + sy, z0_ + sz))
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            faces.append(tuple(b + i for i in q))

    bar(-hw, -t * 0.5, z0, width, t, t)                      # the shoulder bar
    # the stem from the bar up to the hook root, then the hook curl over the rail
    bar(-t * 0.5, -t * 0.5, z0, t, t, max(bar_drop - hook_r, t))
    n = 10
    b = len(verts)
    ring = [(hook_r * math.cos(math.pi * (1.0 - k / float(n))),
             hook_r * math.sin(math.pi * (1.0 - k / float(n))))
            for k in range(n + 1)]
    for cx, cz in ring:
        verts.append((cx - t * 0.5, -t * 0.5, cz))
        verts.append((cx + t * 0.5, -t * 0.5, cz))
        verts.append((cx + t * 0.5, t * 0.5, cz))
        verts.append((cx - t * 0.5, t * 0.5, cz))
    for k in range(n):
        a = b + k * 4
        c = b + (k + 1) * 4
        for m in range(4):
            faces.append((a + m, a + (m + 1) % 4, c + (m + 1) % 4, c + m))
    return verts, faces


# ---------------------------------------------------------------------------
# 3. CUSHION / PILLOW — a plump form, not a slab.
# ---------------------------------------------------------------------------

def cushion(w, d, h, nu=13, nv=9, pinch=0.30, dent=0.0, salt=0):
    """A plump pillow/cushion: a rounded superellipsoid whose CORNERS pinch in (the way a
    stuffed cover does) and whose top may carry a soft `dent`.

    `pinch` is how much the corners draw in (0 = a rounded box, 1 = a lens). `dent` sinks
    the top centre — a pillow that has been leaned on. Local origin = footprint SW corner
    at z0; the form fills (0..w, 0..d, 0..h).

    Replaces the `_rbox` slab whose "two identical flat pillows at identical height" the
    DD ground phase named as the loudest CAD tell at the bed head."""
    if w <= 0 or d <= 0 or h <= 0:
        _fail(f"cushion: degenerate {w}x{d}x{h}")
    if not 0.0 <= pinch <= 1.0:
        _fail(f"cushion: pinch {pinch} outside 0..1")
    # The 3% surface wobble below must live INSIDE the declared footprint, not spill past
    # it: this codebase's one hard geometric invariant is that a part never leaves its
    # plan bbox, and a pillow that overhangs its mattress by 2mm is a clipping artifact
    # the beauty pass would faithfully amplify. Pre-shrink the radii by the wobble peak.
    WOB = 0.03
    cx, cy = w * 0.5 / (1.0 + WOB), d * 0.5 / (1.0 + WOB)
    ox, oy = w * 0.5 - cx, d * 0.5 - cy       # re-centre in the footprint
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)
        phi = math.pi * v                                    # 0 = bottom pole, pi = top
        zf = 0.5 - 0.5 * math.cos(phi)                       # 0..1
        r = math.sin(phi)
        for i in range(nu + 1):
            u = i / float(nu)
            a = 2.0 * math.pi * u
            ca, sa = math.cos(a), math.sin(a)
            # superellipse: exponent > 2 keeps the sides full and pinches the corners
            e = 2.0 + 2.2 * pinch
            sx = math.copysign(abs(ca) ** (2.0 / e), ca)
            sy = math.copysign(abs(sa) ** (2.0 / e), sa)
            wob = 1.0 + WOB * math.sin(3.0 * a + 2.0 * math.pi * ((salt + 1) * PHI_INV % 1.0))
            x = ox + cx + cx * r * sx * wob
            y = oy + cy + cy * r * sy * wob
            z = h * zf
            if dent and zf > 0.55:                           # a soft press on the upper face
                z -= dent * ((zf - 0.55) / 0.45) * (1.0 - min(r * 1.4, 1.0))
            verts.append((x, y, z))
    return verts, _loft_faces(nv, nu)


# ---------------------------------------------------------------------------
# 4. FOLDED STACK — what sits on an open shelf.
# ---------------------------------------------------------------------------

def folded_stack(w, d, n, item_h, salt=0, jitter_xy=0.012, jitter_rot=0.0):
    """`n` folded items stacked, each offset by a bounded deterministic deviation so the
    stack leans slightly rather than reading as one extruded block.

    Returns [(x, y, z, dx, dy, dz), ...] AABBs in local metres — a stack is the one soft
    object that really is boxy (a folded towel IS a rectangle), so it stays cheap boxes.
    What it must NOT be is perfectly aligned: `jitter_xy` is the whole point.

    The fold ROUNDING is left to the consumer's bevel — a folded edge is a real radius."""
    if n <= 0:
        _fail(f"folded_stack: n must be >= 1 (got {n})")
    if w <= 0 or d <= 0 or item_h <= 0:
        _fail(f"folded_stack: degenerate {w}x{d}x{item_h}")
    out = []
    for k in range(n):
        ox = dev(k, jitter_xy, salt)
        oy = dev(k, jitter_xy, salt + 5)
        sw = w * (1.0 - 0.035 * (k / max(n - 1, 1)))         # a stack tapers upward
        sd = d * (1.0 - 0.030 * (k / max(n - 1, 1)))
        out.append((ox + (w - sw) * 0.5, oy + (d - sd) * 0.5, k * item_h, sw, sd, item_h))
    return out


# ---------------------------------------------------------------------------
# 5. THROW — a length of cloth laid over something, with a hanging tail.
# ---------------------------------------------------------------------------

def throw(length, width, lay_z, tail_drop=0.0, nu=44, nv=9,
          ripple=0.016, skew=0.05, salt=0):
    """A throw/runner laid across a surface: a ripple across its width, a hem that is NOT
    parallel to the host edge (`skew`), and an optional `tail_drop` where it falls over
    the near edge.

    Local origin: the laid rectangle's corner at (0, 0, lay_z); `length` runs along x,
    `width` along y. The tail hangs at the y=0 edge. A throw is the one object that can
    make a coverlet read as fabric rather than foam (DD ground), and its hanging tail is
    the only vertical drape a flat-on hero frame would otherwise contain."""
    if length <= 0 or width <= 0:
        _fail(f"throw: degenerate {length}x{width}")
    if tail_drop < 0:
        _fail(f"throw: tail_drop must be >= 0 (got {tail_drop})")
    # Fold pitch is PHYSICAL (the drape_skirt lesson): cycles are solved from the run so
    # the folds land at ~110-190mm whatever the throw's length, and `nu` samples each fold
    # several times. The first cut fixed 11 cycles over an undersampled 17-station run,
    # which ALIASED into a hard zigzag.
    def cycles_for(wl):
        return max(2.0, float(round(length / wl)))
    waves = ((cycles_for(0.34), 0.52), (cycles_for(0.185), 0.31), (cycles_for(0.115), 0.17))
    verts = []
    total_v = width + tail_drop
    for i in range(nu + 1):
        u = i / float(nu)
        x = length * u
        c = _crease(u, salt, waves)
        for j in range(nv + 1):
            v = j / float(nv)
            s = v * total_v                                  # arclength from the far edge
            if s <= width:                                   # the part lying on the host
                y = width - s + skew * width * (u - 0.5)     # skewed hem: not parallel
                z = lay_z + ripple * c * math.sin(math.pi * min(s / max(width, 1e-6), 1.0))
            else:
                # THE TAIL. The crease belongs OUT OF PLANE, growing toward the free hem —
                # the same constrained-top/free-bottom law the drape obeys. Putting it in Z
                # instead (the first cut) left a FLAT sheet with a wavy bottom edge, which
                # renders as torn paper: a zigzag silhouette on the hero frame's foreground
                # is exactly the "reads as broken" cue this owner rejects.
                fall = s - width
                g = fall / max(tail_drop, 1e-6)
                y = (skew * width * (u - 0.5) - fall * 0.14
                     + ripple * 1.9 * (g ** 1.5) * c)        # real vertical folds
                z = lay_z - fall
            verts.append((x, y, z))
    return verts, _grid_faces(nu, nv, wrap_u=False)


def bbox(verts):
    """(x0, y0, z0, x1, y1, z1) of a vert list — the containment check every caller owes
    its host part (this codebase's CAD invariant: parts never leave the plan bbox)."""
    if not verts:
        _fail("bbox: empty vert list")
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)
