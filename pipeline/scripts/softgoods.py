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


# ---------------------------------------------------------------------------
# SIMULATION FEEDSTOCK (2026-07-22 — owner correction: "you still can't use Blender")
#
# The generators below this block SHAPE cloth by hand. That was the wrong layer to
# solve it in: Blender ships a cloth solver that runs headless, deterministically
# (measured drift 0.000000000 m over two bakes), in 0.48 s for a 625-vert sheet, and
# it has the collision term whose absence made element 8 DISABLE the foot throw.
#
# The split that survives: layer 1 still decides WHERE cloth goes, HOW FINE it is
# discretised and WHAT IT MAY NOT VIOLATE — all pure, all unit-testable under plain
# `python`. It just stops pretending to know how cloth falls. These two helpers are
# that contract's feedstock; `drape.py` (layer 2) simulates them.
# ---------------------------------------------------------------------------

def flat_sheet(x0, y0, w, d, z, cell=0.028, cut=(), mitre=(), mitre_keep=0.6):
    """A flat QUAD grid in world XY at height `z` — the undeformed state of a
    simulated sheet. Returns (verts, faces) in WORLD metres.

    `cell` is a target EDGE LENGTH in metres, not a station count: the solver's
    fold size is governed by how finely the sheet is discretised, so a coverlet and
    a napkin must not share a station count or the napkin folds like a tarpaulin.
    Stations are derived from the actual extent, so this is resolution-stable.

    `cut` is a list of (x0, y0, x1, y1) world rects removed from the sheet — THE
    TAILOR'S CUT. A rectangle of cloth laid over a rectangular bed has a square
    flap at each corner where two overhangs meet, and that flap has nowhere to go:
    it hangs as a diagonal cowl that spreads OUTSIDE the bed's own footprint (first
    bake: 316 mm out, and it reached the floor). Real bedding solves this by cutting
    or mitring the corner, not by tuning stiffness. Vertices orphaned by the cut are
    dropped — a loose vertex is a free particle the solver drops to the floor.

    `mitre` is (x0, y0, x1, y1, ix, iy): a corner square ROUNDED to radius
    `mitre_keep` x its own size about the inner corner (ix, iy), instead of squared
    off. This is the third corner tried here and the reason is the same each time —
    what a corner must not have is a FREE EDGE.

      * Leave the square: the flap has nowhere to go, hangs as a diagonal cowl and
        spread 316 mm outside the bed, down to the floor.
      * Cut the square away: the two adjacent panels are left with free vertical
        edges meeting at a point, and they splay apart as they fall — two sharp tabs
        sticking out of the bed's silhouette, which is the "an engineer reads it as
        broken" defect, not a styling nit.
      * Cut it to a diagonal (a real mitre): same free edges, shorter. Same tabs.

    A rounded corner has ONE continuous boundary, so there is nothing to splay: the
    cloth turns the corner as a smooth cowl. Plenty of real bedding is cut this way."""
    if w <= 0 or d <= 0:
        raise ValueError(f"flat_sheet: degenerate extent {w}x{d}")
    nu = max(MIN_SEGMENTS, int(round(w / float(cell))))
    nv = max(MIN_SEGMENTS, int(round(d / float(cell))))
    grid = [(x0 + w * i / nu, y0 + d * j / nv, z)
            for j in range(nv + 1) for i in range(nu + 1)]

    def dropped(quad):
        cx = sum(grid[k][0] for k in quad) * 0.25
        cy = sum(grid[k][1] for k in quad) * 0.25
        if any(a <= cx <= c and b <= cy <= e for a, b, c, e in cut):
            return True
        for a, b, c, e, ix, iy in mitre:
            if a <= cx <= c and b <= cy <= e:
                u = abs(cx - ix) / max(c - a, 1e-9)
                v = abs(cy - iy) / max(e - b, 1e-9)
                if (u * u + v * v) ** 0.5 > _mitre_radius(u, v, mitre_keep):
                    return True
        return False

    keep, used = [], {}
    for j in range(nv):
        for i in range(nu):
            q = (j * (nu + 1) + i, j * (nu + 1) + i + 1,
                 (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i)
            if dropped(q):
                continue
            keep.append(q)
    if not keep:
        raise ValueError("flat_sheet: every face was cut away")
    verts, faces = [], []
    for q in keep:
        f = []
        for k in q:
            if k not in used:
                used[k] = len(verts)
                verts.append(grid[k])
            f.append(used[k])
        faces.append(tuple(f))
    # THE ARC-SNAP (LOOK round-2 #3). Dropping whole faces by their CENTRE leaves the
    # corner's free boundary as a STAIRCASE at cell resolution — and a staircase hem
    # drapes as a staircase: the coverlet's left corner broke in a squared 90°
    # drop→shelf→drop Z-step, knife-clean against the floor, which cloth cannot do. The
    # rounding promised "ONE continuous boundary"; the cut delivered it only to face
    # precision. So every kept vert past the boundary curve is PROJECTED onto it
    # (radially in the rect-normalised space, so an oblong corner snaps to its ellipse).
    # The curve itself is _mitre_radius: FULL overhang at both strip junctions, dipping
    # to mitre_keep on the diagonal — verts on the shared strip edges satisfy r <= 1
    # there, so the strips are untouched and the hem leaves each strip tangent instead
    # of stepping. Quads stay quads; only boundary geometry moves.
    if mitre:
        for n_, (vx, vy, vz) in enumerate(verts):
            for a, b, c, e, ix, iy in mitre:
                if a - 1e-9 <= vx <= c + 1e-9 and b - 1e-9 <= vy <= e + 1e-9:
                    u = abs(vx - ix) / max(c - a, 1e-9)
                    v = abs(vy - iy) / max(e - b, 1e-9)
                    r = (u * u + v * v) ** 0.5
                    f = _mitre_radius(u, v, mitre_keep)
                    if r > f:
                        s = f / r
                        verts[n_] = (ix + (vx - ix) * s, iy + (vy - iy) * s, vz)
                    break
    return verts, faces


def _mitre_radius(u, v, keep):
    """Free-boundary radius of a rounded corner cut, by direction (rect-normalised).

    LOOK round-2 #3 exposed what a CONSTANT radius does at a corner whose neighbours
    keep full overhang: the strips' hems reach r=1.0 while the corner cloth stops at
    r=keep, so the as-draped hem line breaks in a hard step where they meet — the
    squared drop→shelf→drop the verdict called "cloth cannot do this". The boundary
    must instead LEAVE each strip at the strip's own hem and shorten only through the
    diagonal: full radius (1.0) at θ=0 and θ=90°, dipping to `keep` between, blended
    with cos⁶(2θ) so the curve is tangent-flat at all three extremes. The exponent is
    6, not 2, and the first bake is why: cos² held the boundary near full radius over
    most of the arc, which nearly doubled the corner cloth — the corner cowl bulged
    past the plan line, and the search ladder paid for that corner-local bulge by
    stripping slack from the WHOLE coverlet (2.5% → 0.62%, folds ironed, hem 62 mm
    short) and then starving the throw stacked outboard of it. cos⁶ rises to the
    strip hem only within the last ~15° of arc: the step is still gone, the cloth
    budget stays essentially the mitre's. (A full square flap remains the recorded
    316mm-cowl failure — the dip is the design, the tangent is the fix.)"""
    th = math.atan2(v, u)
    c2 = math.cos(2.0 * th)
    return keep + (1.0 - keep) * (c2 * c2) ** 3


def folded_sheet(x0, y0, w, d, z, band, head, cell=0.028, lift=0.016):
    """A quad-grid sheet whose HEAD edge is already TURNED BACK over itself — the
    feedstock of a made bed's duvet. Returns (verts, faces) in WORLD metres.

    WHY (owner LOOK 2026-07-28, round 3): "เตียงยังดูแปลก ๆ เหมือนก้อนอะไรซักอย่างอยู่บน
    ผ้าปู". The duvet was the LAST bevelled box on the bed — a 90 mm slab inset 110 mm
    from every edge, floating mid-bed as an island, with a second box lying in front
    of it PLAYING the turned-back fold. Boxes don't read as bedding; the coverlet and
    the throw earned their cloth read from the solver, and the duvet gets the same
    physics. The fold is not authored as geometry-on-top: the sheet really is longer
    than its footprint by `band`, and the head-most strip is pre-bent 180° over the
    main panel (grid stays ONE connected lattice, doubled in plan over the fold
    strip, `lift` apart). The solver then settles the crease into a soft roll and
    the two layers into contact — which is what a hotel fold physically is.

    head: "x-"|"x+"|"y-"|"y+" — the side the crease faces (where the pillows are).
    The rect [x0..x0+w, y0..y0+d] is the FINAL plan footprint; total cloth length is
    footprint + band."""
    if w <= 0 or d <= 0:
        raise ValueError(f"folded_sheet: degenerate extent {w}x{d}")
    axis, sgn = head[0], head[1]
    if axis not in ("x", "y") or sgn not in ("+", "-"):
        raise ValueError(f"folded_sheet: bad head {head!r}")
    main = w if axis == "x" else d
    cross = d if axis == "x" else w
    if not 0 < band < main:
        raise ValueError(f"folded_sheet: band {band} outside (0, {main})")
    c0 = ((x0 + w) if sgn == "+" else x0) if axis == "x" else \
         ((y0 + d) if sgn == "+" else y0)
    into = -1.0 if sgn == "+" else 1.0
    t0 = y0 if axis == "x" else x0
    ns = max(MIN_SEGMENTS, int(round((band + main) / float(cell))))
    nt = max(MIN_SEGMENTS, int(round(cross / float(cell))))
    verts = []
    for i in range(ns + 1):
        s = -band + (band + main) * i / ns          # s<0 = the folded-back top layer
        u = c0 + into * abs(s)
        # the top layer rises to `lift` over ~2 cells so the crease is a bendable
        # hinge for the solver, not a zero-thickness pinch it must tear open
        zz = z + (lift * min(1.0, -s / (2.0 * cell)) if s < 0 else 0.0)
        for j in range(nt + 1):
            t = t0 + cross * j / nt
            verts.append((u, t, zz) if axis == "x" else (t, u, zz))
    faces = [(i * (nt + 1) + j, i * (nt + 1) + j + 1,
              (i + 1) * (nt + 1) + j + 1, (i + 1) * (nt + 1) + j)
             for i in range(ns) for j in range(nt)]
    return verts, faces


def verts_in_rect(verts, x0, y0, x1, y1, tol=1e-9):
    """Indices of `verts` whose XY falls inside a world rect — how a caller names
    the region a solver PINS.

    Pinning is what stops a long bake from letting a sheet creep toward its free
    end. It must name the cloth that is PHYSICALLY TRAPPED, never a whole grid row:
    the first cut pinned the entire head row of a coverlet, and because that row ran
    on through the overhanging wings, two lines of pinned vertices hung in mid-air
    holding both flanks rigidly out. The flanks then never fell at all, while the
    foot — unpinned — draped correctly. Pin the region, not the row."""
    return [n for n, p in enumerate(verts)
            if x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol]


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


def garment(width, drop, depth=0.085, nu=11, nv=7,
            fold=0.014, hem_wander=0.016, sway=0.010, salt=0, collar=0.0,
            sleeves=False):
    """One hanging garment as a closed lofted shell, WIDEST AT THE SHOULDER.

    Round-4 owner verdict ("เสื้อผ้าในตู้ ดูไม่เหมือนเสื้อผ้าจริง"): the previous
    profile — a narrow top opening out to a fuller body — is the silhouette of a
    GARMENT BAG, not a garment. A real hanging piece is widest across the hanger
    tips and its body falls slightly NARROWER below; and its identity lives in the
    sleeves hanging beside that body. So: wf(0)=1.0 easing down to a per-piece body
    fraction by the knee, plus (opt-in) two flattened sleeve tubes appended into
    the same mesh — each contained inside the shoulder span and inside the body's
    own thickness envelope, so the published bounds (span <= width*GARMENT_FLARE
    + 2*sway; pitch thickness budget) stay honest with sleeves on.

    Local origin is the garment's top-centre; +z is up, body occupies z in
    [-drop, 0]. Built as a closed elliptical loft (nu stations, nv rings): a
    garment seen edge-on is a soft lens, and a box on a rail is exactly the
    "beveled slab" reading this module exists to end."""
    if width <= 0 or drop <= 0 or depth <= 0:
        _fail(f"garment: degenerate {width}x{depth} drop {drop}")
    waves = ((2.0, 0.5), (5.0, 0.33), (9.0, 0.24))
    # PER-GARMENT POSE DNA (LOOK round-2 #5). The rail read as "cloned boards" because
    # dev() varied WIDTHS only: every piece shared one S-bend at one height, a
    # dead-level shoulder line off a single-point hook, and hems that kicked in
    # unison. The pose itself now derives from `salt`, inside the published bounds:
    #   knee   where the shoulder opens into the body (the old constant 0.35);
    #   flare  below-waist flare, <= 0.06 so GARMENT_FLARE stays the true span bound;
    #   slope  shoulder TIPS drop toward the ends — a hanger's arms angle down from
    #          the hook, a level top ring is a coat on a SHELF, not on a hanger;
    #   bow    a lateral C-or-S bow along the shoulder axis, zero at the hook so the
    #          piece still hangs FROM it, spent out of the sway budget so the
    #          published span bound (width*FLARE + 2*sway) stays honest;
    #   fold_g per-piece crease amplitude — phase already varied, depth never did.
    knee = 0.35 + dev(1, 0.07, salt + 31)
    flare_g = 0.04 + 0.02 * dev(2, 1.0, salt + 37)
    slope = garment_slope(drop, salt)
    bow_a = 0.55 * sway * dev(4, 1.0, salt + 43)
    bow_m = 0.3 + 0.7 * abs(dev(5, 1.0, salt + 47))      # 1 = C-bow, toward 0 = S-bow
    fold_g = fold * (0.65 + 0.35 * abs(dev(6, 1.0, salt + 53)))
    body = 0.74 + 0.04 * dev(7, 1.0, salt + 59)          # body width, fraction of shoulder
    # DEEP INWARD-ONLY DRAPE FOLDS (round 4, second cut). The first cut kept the
    # ±6 mm crease the pitch budget allows and the faces still rendered as flat
    # board — real hanging cloth folds 15-30 mm deep. The pitch cannot give that
    # outward, so the deep folds CARVE INWARD from the envelope (real folds are
    # valleys in the silhouette, not bumps past the hanger): envelope untouched,
    # pitch budget untouched, and the face finally stripes under light.
    fold_in = 0.018 * (0.7 + 0.3 * abs(dev(12, 1.0, salt + 83)))
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)                                    # 0 at shoulder, 1 at hem
        # width profile (round 4): WIDEST at the hanger tips, easing IN to a
        # genuinely narrower body by the knee — the side band this frees is where
        # the sleeves live, so the notch (shoulder -> sleeve -> body) is what the
        # camera reads as a shirt even when neighbours overlap. wf peaks at the
        # shoulder, so GARMENT_FLARE remains the true span bound.
        t = min(v / knee, 1.0)
        wf = 1.0 - (1.0 - body) * (t * t * (3 - 2 * t))      # smoothstep down to the body
        wf += flare_g * max(v - 0.5, 0.0)                    # a little flare below the waist
        rx = 0.5 * width * wf
        # THE SHOULDER CAP. The first render put the garments' full thickness right up to
        # the top ring, so each one presented a flat-topped rectangular strip to the
        # camera and the rail read as a row of paint swatches. A garment over a hanger
        # narrows to a ROUNDED RIDGE at the shoulder line and only reaches full body a
        # third of the way down — that curve is most of what says "clothing" when the
        # wardrobe is seen from the front and every garment is edge-on.
        # The HEM thins back down (round 4): a full-thickness bottom ring presented
        # a wide flat underside edge-band — the literal look of a board's edge.
        ry = 0.5 * depth * (0.22 + 0.78 * min(v / 0.34, 1.0) ** 0.7)
        ry *= 1.0 - 0.68 * max(v - 0.82, 0.0) / 0.18         # knife hem, not plank edge
        # lean + bow share the sway budget so their SUM can never exceed it: the bow
        # vanishes at v=0 (the hook) and at the hem line, mixing a C-shape with an
        # S-shape per piece — this is what breaks the one-bend-at-one-height clone.
        sw = (sway - abs(bow_a)) * (v ** 1.5) * dev(0, 1.0, salt + 3) \
            + bow_a * (bow_m * math.sin(math.pi * v)
                       + (1.0 - bow_m) * math.sin(2.0 * math.pi * v))
        hw = dev(j, hem_wander, salt + 2) if j == nv else 0.0
        # the hanger-arm term: fades out by the knee, fully formed at the top ring
        sl = slope * max(0.0, 1.0 - v / knee)
        for i in range(nu + 1):
            u = i / float(nu)
            a = 2.0 * math.pi * u
            amp = fold_g * (v ** 1.5)
            c = _crease(u, salt, waves)
            ca = math.cos(a)
            sa = math.sin(a)
            x = rx * ca + sw
            y = ry * sa + amp * c * (1.0 if sa >= 0 else -1.0)
            # the deep folds: carve the face TOWARD the midplane where the crease
            # field peaks, growing down the drop — valleys, never bumps, so the
            # thickness envelope (and with it the rail pitch budget) is untouched.
            pinch = min((fold_in / max(ry, 1e-6)) * max(c, 0.0) * (v ** 1.2), 0.85)
            y -= ry * sa * pinch
            # the same folds nick the silhouette edges inward a whisker, so the
            # side profile ripples instead of running dead straight
            x -= math.copysign(1.0, ca) * fold_in * 0.25 * max(-c, 0.0) * v * abs(ca)
            z = -drop * v + hw - sl * abs(ca) ** 1.6
            if collar and v < 0.10:
                # a COLLAR: the neck region (|x| small — front and back of the neck)
                # rises above the shoulder line, fading out by v=0.10. This is the one
                # cue that says SHIRT rather than felt blank (round-3 owner read:
                # "ผ้าที่แขวนในตู้ไม่สมจริง"). Capped by the caller under SHOULDER_DROP
                # so it never pokes above the rail.
                z += collar * math.exp(-(ca / 0.30) ** 2) * (1.0 - v / 0.10)
            verts.append((x, y, z))
    faces = _loft_faces(nv, nu)
    if sleeves:
        # SLEEVES (round 4): the silhouette cue no profile can fake — two flattened
        # tubes hanging from under the shoulder tips, drifting a touch INWARD (a
        # sleeve falls against the body, not away from it). Containment is by
        # construction, not by luck: tube centre sits rx_s inside the tip so the
        # outer edge never passes the shoulder (span bound untouched), and
        # |y| <= 0.006 + ry_s stays inside the body's own half-depth (pitch budget
        # untouched). Long/short is per-piece DNA; the cuff ring pinches to close.
        long_s = dev(8, 1.0, salt + 61) > -0.35              # most sleeves are long
        s_len = min(drop * (0.55 if long_s else 0.30) * (1.0 + 0.10 * dev(9, 1.0, salt + 71)),
                    drop * 0.80)
        # the tube lives in the side band the narrowed body freed: outer edge AT the
        # shoulder tip (span bound untouched), inner edge overlapping the body edge —
        # so below the cuff the silhouette STEPS in to the body. First cut buried the
        # sleeves inside the body's volume (quick-look fx: nothing visible); now the
        # tube also rides against one face (front for one arm, back for the other) so
        # it reads as a raised ridge under light, still inside the half-depth budget.
        rx_s = min(0.045, 0.24 * 0.5 * width)
        ry_s = min(0.014, 0.45 * 0.5 * depth)
        nus, nvs = 8, 6
        for side in (-1.0, 1.0):
            yo = (0.5 * depth * 0.95 - ry_s) * (side if dev(10, 1.0, salt + 79) > 0 else -side)
            base = len(verts)
            for j in range(nvs + 1):
                v = j / float(nvs)
                taper = (1.0 - 0.30 * v) * (0.35 if j == nvs else 1.0)
                xc = side * (0.5 * width - rx_s) * (1.0 - 0.08 * v)
                zc = -slope - v * s_len
                for i in range(nus + 1):
                    a = 2.0 * math.pi * i / float(nus)
                    verts.append((xc + rx_s * taper * math.cos(a),
                                  yo + ry_s * taper * math.sin(a), zc))
            faces.extend((fa + base, fb + base, fc + base, fe + base)
                         for (fa, fb, fc, fe) in _loft_faces(nvs, nus))
    return verts, faces


def trouser_fold(width, drop, depth=0.030, nu=9, nv=6, salt=0):
    """Trousers folded over a hanger's bar: a narrow, near-straight panel with a soft
    CYLINDRICAL ROLL at the top (the fold itself) and a gentle leg crease taper.

    A rail of nothing but shirt-shells is a rail of one species — part of why the
    owner read the wardrobe as cloned boards even after pose variation. Trousers are
    the second-commonest thing on a real rail and their silhouette differs in KIND:
    straight sides, no shoulder, half the drop (vault: trousers-on-hanger 500 mm).
    Origin = top-centre at the bar, +z up; body occupies z in [-drop, 0]."""
    if width <= 0 or drop <= 0 or depth <= 0:
        _fail(f"trouser_fold: degenerate {width}x{depth} drop {drop}")
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)
        # near-straight sides: a whisker of taper toward the cuffs, per-piece
        wf = 1.0 - 0.06 * v * (1.0 + 0.5 * dev(1, 1.0, salt + 73))
        rx = 0.5 * width * wf
        # the top ring is the FOLD: full roll radius immediately (a cylinder over the
        # bar), settling to the flat doubled-cloth thickness by ~a third down
        ry = 0.5 * depth * (1.0 - 0.55 * min(v / 0.30, 1.0))
        lean = 0.006 * (v ** 1.5) * dev(0, 1.0, salt + 3)
        hw = dev(j, 0.008, salt + 2) if j == nv else 0.0
        for i in range(nu + 1):
            a = 2.0 * math.pi * i / float(nu)
            verts.append((rx * math.cos(a) + lean, ry * math.sin(a),
                          -drop * v + hw))
    return verts, _loft_faces(nv, nu)


def garment_slope(drop, salt):
    """The shoulder-tip drop of the garment at `salt` — ONE stream, published, because
    two consumers must agree on it: the garment's cloth follows this slope, and the
    hanger's ARMS must angle down with the very same value or the pair contradicts.

    The pre-commit review proved the first cut of the pose DNA did exactly that: slope
    ran to 0.053 while the recorded cover budget (styling.SHOULDER_DROP 0.020 above a
    bar at 0.030) is 10 mm — 40/40 salts hung cloth below the straight bar that
    suspends it. Coverage math with LINEAR arms and the cloth's ^1.6 profile: at the
    ring tip, cloth-minus-arm = 0.010 - 0.244*slope, so slope <= 0.038 keeps the cloth
    outside the arm at every station. Hence the band [0.017, 0.038] — still >= the
    12 mm the armour test demands, never enough to sag through the arm."""
    return min(0.0275 + 0.0105 * dev(3, 1.0, salt + 41), 0.25 * drop)


# The coverlet's corner-cut dip (see _mitre_radius). Lives HERE, not in drape.py, so
# the value that decides the corner's cloth budget is pinned by pure tests — fix #3
# shipped with zero armour once already (pre-commit review, 2026-07-28).
COVERLET_MITRE_KEEP = 0.45


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


def hanger(width, hook_r=0.015, bar_drop=0.030, salt=0, arm_drop=0.0):
    """A hanger silhouette above a garment's shoulder: two shoulder ARMS + a hook.

    Returns (verts, faces) with origin at the RAIL centre; the arms root `bar_drop`
    below the rail and the hook rises to meet it. Small, but the repeated hook profile
    along a rail is the visual signature that says 'wardrobe' — without it, garments
    read as sheets pegged on a line (DD ground: 'Hangers themselves').

    `arm_drop` angles each arm DOWN from the hook root to its tip — a real hanger's
    arms slope, and once the garment's shoulders slope too (pose DNA, LOOK round-2 #5)
    a straight bar is worse than a detail gap: the pre-commit review measured cloth
    hanging 13-43 mm BELOW a straight bar at every salt. The caller passes the SAME
    `garment_slope` its garment wears, so cloth and wire agree by construction."""
    if width <= 0:
        _fail(f"hanger: degenerate width {width}")
    if arm_drop < 0:
        _fail(f"hanger: arm_drop {arm_drop} must be >= 0")
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

    def arm(sx):
        """One sheared-box arm from the hook root out to x = sx*hw, its top face
        dropping linearly by `arm_drop` (planar quads: z is linear in x)."""
        b = len(verts)
        for x, zt in ((0.0, z0), (sx * hw, z0 - arm_drop)):
            verts.append((x, -t * 0.5, zt))
            verts.append((x, t * 0.5, zt))
            verts.append((x, t * 0.5, zt - t))
            verts.append((x, -t * 0.5, zt - t))
        for q in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
                  (0, 3, 2, 1), (4, 5, 6, 7)):
            faces.append(tuple(b + i for i in q))

    arm(1.0)                                                 # the two shoulder arms
    arm(-1.0)
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

def cushion(w, d, h, nu=13, nv=9, pinch=0.30, dent=0.0, salt=0, edge=0.30,
            seam=0.0, ear=1.2):
    """A plump pillow/cushion: a rounded superellipsoid whose CORNERS pinch in (the way a
    stuffed cover does) and whose top may carry a soft `dent`.

    `pinch` is how much the corners draw in (0 = a rounded box, 1 = a lens). `dent` sinks
    the top centre — a pillow that has been leaned on. Local origin = footprint SW corner
    at z0; the form fills (0..w, 0..d, 0..h).

    `edge` is the EDGE FULLNESS — the exponent on the vertical radius profile.
    2026-07-28, THE PEBBLE FIX (owner LOOK on the tonal-ladder renders): the first cut used
    r = sin(phi) raw, which is a hemisphere-profile — the plan radius collapses smoothly to
    zero at both poles, so every cushion's SILHOUETTE was a pointed lens. Six of them at
    the bed head read as pebbles/UFOs, and no value ladder can fix a wrong silhouette. A
    real pillow holds nearly full width for most of its height and turns a small rounded
    edge at top and bottom: r = sin(phi)**edge with edge < 1 does exactly that (at 10% of
    the height the plan is already at ~86% width instead of 60%). edge=1.0 reproduces the
    old lens for any caller that genuinely wants one.

    `seam` (metres) raises a piped SEAM RIDGE around the equator — the sewn edge of the
    case, and the single strongest cue that a soft form is a PILLOW and not a blob
    (owner LOOK 2026-07-28 round 3: "หมอนยังดูไม่เป็นหมอน เป็นก้อนอะไรไม่รู้ซ้อน ๆ กัน" — the
    forms were smooth ellipsoids with no sewn identity). `ear` amplifies the ridge at
    the four corners, where a real case's excess fabric sticks out as ears. Both spend
    from a pre-shrunk radius, so the footprint invariant still holds. A caller whose
    seam would LIE (a standing euro sham: its piped edge runs around the FACE, not in
    a horizontal ring at half-height) keeps seam=0.

    Replaces the `_rbox` slab whose "two identical flat pillows at identical height" the
    DD ground phase named as the loudest CAD tell at the bed head."""
    if w <= 0 or d <= 0 or h <= 0:
        _fail(f"cushion: degenerate {w}x{d}x{h}")
    if not 0.0 <= pinch <= 1.0:
        _fail(f"cushion: pinch {pinch} outside 0..1")
    if not 0.05 <= edge <= 1.0:
        _fail(f"cushion: edge {edge} outside 0.05..1.0")
    if seam < 0:
        _fail(f"cushion: seam {seam} must be >= 0")
    # The 3% surface wobble below must live INSIDE the declared footprint, not spill past
    # it: this codebase's one hard geometric invariant is that a part never leaves its
    # plan bbox, and a pillow that overhangs its mattress by 2mm is a clipping artifact
    # the beauty pass would faithfully amplify. Pre-shrink the radii by the wobble peak —
    # and by the seam ridge's own maximum reach (seam * (1 + ear)), for the same reason.
    WOB = 0.03
    s_max = seam * (1.0 + max(ear, 0.0))
    cx = (w * 0.5 - s_max) / (1.0 + WOB)
    cy = (d * 0.5 - s_max) / (1.0 + WOB)
    if cx <= 0 or cy <= 0:
        _fail(f"cushion: seam {seam} eats the whole {w}x{d} footprint")
    ox, oy = w * 0.5 - cx, d * 0.5 - cy       # re-centre in the footprint
    verts = []
    for j in range(nv + 1):
        v = j / float(nv)
        phi = math.pi * v                                    # 0 = bottom pole, pi = top
        zf = 0.5 - 0.5 * math.cos(phi)                       # 0..1
        r = math.sin(phi) ** edge
        g = math.exp(-((v - 0.5) / 0.07) ** 2) if seam else 0.0   # equator gaussian
        for i in range(nu + 1):
            u = i / float(nu)
            a = 2.0 * math.pi * u
            ca, sa = math.cos(a), math.sin(a)
            # superellipse: exponent > 2 keeps the sides full and pinches the corners
            e = 2.0 + 2.2 * pinch
            sx = math.copysign(abs(ca) ** (2.0 / e), ca)
            sy = math.copysign(abs(sa) ** (2.0 / e), sa)
            wob = 1.0 + WOB * math.sin(3.0 * a + 2.0 * math.pi * ((salt + 1) * PHI_INV % 1.0))
            px = cx * r * sx * wob
            py = cy * r * sy * wob
            if seam and g > 1e-4:
                # push the ridge outward along the plan direction; ears at the corners
                so = seam * g * (1.0 + ear * abs(ca * sa) ** 1.2)
                pl = math.hypot(px, py)
                if pl > 1e-9:
                    px += px / pl * so
                    py += py / pl * so
            x = ox + cx + px
            y = oy + cy + py
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


def bbox(verts):
    """(x0, y0, z0, x1, y1, z1) of a vert list — the containment check every caller owes
    its host part (this codebase's CAD invariant: parts never leave the plan bbox)."""
    if not verts:
        _fail("bbox: empty vert list")
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)
