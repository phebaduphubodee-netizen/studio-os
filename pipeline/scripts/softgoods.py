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

def flat_sheet(x0, y0, w, d, z, cell=0.028, cut=(), mitre=(), mitre_keep=0.6,
               salt=0, salt_rect=None, salt_amp=0.005):
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
    # PER-CORNER BIAS (round-6 lane B2 — the owed lane-C debt, C2 twice: the baked
    # coverlet's corner gathers "แตกเป็นเสี้ยน" identically L/R): verts OUTSIDE
    # `salt_rect` (the surface the sheet lies on — i.e. the skirt cloth only) get a
    # bounded in-plane deviation growing with overhang distance, so each corner
    # enters the solver with its own bias and the gathers stop mirroring. Applied
    # AFTER cut/mitre/arc-snap so topology and the continuous boundary are already
    # settled; salt=0 = the exact prior sheet.
    if salt and salt_rect:
        rx0, ry0, rx1, ry1 = salt_rect
        # `salt_amp` (p2r23): the deviation bound, default = the constant this block
        # always used, so every existing caller is byte-identical. A LAID edge (the
        # throw's on-bed head edge) wanders more than a falling hem's in-plane bias
        # — the caller passes its own bound, capped well under MAX_HEM_WANDER.
        for n_, (vx, vy, vz) in enumerate(verts):
            g = min(1.0, max(rx0 - vx, vx - rx1, ry0 - vy, vy - ry1, 0.0) / 0.15)
            if g > 0.0:
                verts[n_] = (vx + dev(n_ * 131, salt_amp, salt) * g,
                             vy + dev(n_ * 137, salt_amp, salt + 7) * g, vz)
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


def folded_sheet(x0, y0, w, d, z, band, head, cell=0.028, lift=0.016, salt=0,
                 crease_wander=0.0):
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
    footprint + band.

    salt != 0 breaks the feedstock's mirror symmetry (round-6 lane C, C2#4: the baked
    duvet's L/R corners came out mirror-images because a symmetric lattice over
    symmetric colliders gives the solver no reason to break the tie): main-panel verts
    get a bounded in-plane deviation that grows from zero at the fold to ~6mm at the
    free foot corners, so each corner enters the sim with its own bias. salt=0 is the
    exact pre-round-6 grid."""
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
    if not 0.0 <= crease_wander <= 2.0 * cell:
        raise ValueError(f"folded_sheet: crease_wander {crease_wander} outside "
                         f"0..2*cell ({2.0 * cell:.3f}) — beyond that the hinge "
                         f"cells shear and the crease reads torn, not sewn")
    verts = []
    for i in range(ns + 1):
        s = -band + (band + main) * i / ns          # s<0 = the folded-back top layer
        for j in range(nt + 1):
            t = t0 + cross * j / nt
            # crease wander (p2r23, C2 r19-r22 on the bench fold: the 180° crease
            # renders as a RULER because the fold line is geometrically straight).
            # A per-COLUMN shift of the arc-length origin moves where the fold
            # sits while both layers stay paired by construction (u depends on
            # |s_eff|, so the doubled plan and the crease move together and total
            # cloth length is untouched). 0.0 = the exact prior sheet.
            se = s + (dev(j, crease_wander, salt + 13) if crease_wander else 0.0)
            u = c0 + into * abs(se)
            # the top layer rises to `lift` over ~2 cells so the crease is a bendable
            # hinge for the solver, not a zero-thickness pinch it must tear open
            zz = z + (lift * min(1.0, -se / (2.0 * cell)) if se < 0 else 0.0)
            if salt and se > 0:
                g = se / main                     # 0 at the fold, 1 at the free foot edge
                u2 = u + into * dev(i * 131 + j, 0.006, salt) * g
                t2 = t + dev(i * 137 + j, 0.006, salt + 7) * g
            else:
                u2, t2 = u, t
            verts.append((u2, t2, zz) if axis == "x" else (t2, u2, zz))
    faces = [(i * (nt + 1) + j, i * (nt + 1) + j + 1,
              (i + 1) * (nt + 1) + j + 1, (i + 1) * (nt + 1) + j)
             for i in range(ns) for j in range(nt)]
    return verts, faces


def corner_dart(verts, faces, corner_xy, length, angle_deg=24.0, sew=()):
    """A TAILOR'S DART at a sheet corner — the DR's rank-4 "solver corner
    constraint" (dr-cloth-corner-drape-2026-08-11, sewing springs 10-25), made
    into feedstock. Returns (verts2, faces2, sew_edges): the wedge of faces
    inside the dart fan is REMOVED, the two cut boundaries are PAIRED with
    loose edges, and the cloth solver's sewing springs pull each pair together
    so the flat sheet closes into a shallow CONE at the corner — which is what
    a sewn corner dart physically is. The corner excess then hangs DOWN as a
    tailored cowl instead of standing as the card-fold ear three rounds of
    stiffness tuning could not drop.

    Geometry, all in plan XY (the pre-bake sheet is flat there): the dart apex
    sits `length` in from `corner_xy` along the corner bisector (derived from
    the sheet's own bbox — R9: the caller types no direction); the fan opens
    ±angle_deg/2 about the apex→corner ray. Faces whose centre falls inside
    the fan are dropped; boundary verts are classified by the SIGN of their
    cross product against the bisector and paired A↔B by radial order from the
    apex. Orphans are remapped away (a loose vertex is a free particle).

    Sew edges are LOOSE (no face) by construction — Blender treats faceless
    edges as sewing springs when use_sewing_springs is on; they never render.
    Contract unchanged for faces: quads only, no n-gons.

    `sew` carries a PREVIOUS dart's pairs through this cut: every call remaps
    vertex indices, so chaining two corners without threading the first pairs
    through the second call silently detaches the first seam — the trap this
    parameter exists to close. Pairs whose verts the new cut orphaned are
    dropped (their cloth is gone; a spring to nowhere would pin air)."""
    if length <= 0:
        raise ValueError(f"corner_dart: degenerate length {length}")
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    cx, cy = corner_xy
    # bisector points INTO the sheet: toward the bbox centre, axis-diagonal
    bx = 1.0 if cx <= (min(xs) + max(xs)) * 0.5 else -1.0
    by = 1.0 if cy <= (min(ys) + max(ys)) * 0.5 else -1.0
    inv = 1.0 / math.sqrt(2.0)
    ax, ay = cx + bx * length * inv, cy + by * length * inv   # dart apex
    rx, ry = (cx - ax) / length, (cy - ay) / length           # apex -> corner ray
    half = math.radians(angle_deg) * 0.5

    def _polar(px, py):
        dx, dy = px - ax, py - ay
        r = math.hypot(dx, dy)
        if r < 1e-12:
            return 0.0, 0.0, 0.0
        ang = math.atan2(dx * ry - dy * rx, dx * rx + dy * ry)  # signed vs ray
        return r, ang, dx * ry - dy * rx

    drop = []
    for f in faces:
        fx = sum(verts[k][0] for k in f) / len(f)
        fy = sum(verts[k][1] for k in f) / len(f)
        r, ang, _ = _polar(fx, fy)
        drop.append(r <= length * 1.05 and abs(ang) < half)
    if not any(drop):
        raise ValueError("corner_dart: fan removed no face — corner/length do "
                         "not touch this sheet (a silent no-op dart would read "
                         "as a mechanism that ran)")
    kept = [f for f, d in zip(faces, drop) if not d]
    used_kept = {k for f in kept for k in f}
    cut_verts = ({k for f, d in zip(faces, drop) if d for k in f} & used_kept)
    # pair the two cut banks. Two traps found by the first test run, both at
    # the APEX end where the fan is narrower than one cell: (1) the two banks
    # touch there, so a naive sign-split pairs same-bank NEIGHBOURS — filtered
    # by refusing any pair that shares a kept face (a real dart pair spans the
    # hole, so it can never share one); (2) banks come out unequal length, so
    # a zip mismatches radii — pair each A-vert to the NEAREST-radius free
    # B-vert instead.
    kept_at = {}
    for fi, f in enumerate(kept):
        for k in f:
            kept_at.setdefault(k, set()).add(fi)
    banks = {False: [], True: []}
    for k in cut_verts:
        r, ang, cross_s = _polar(*verts[k][:2])
        if r < 1e-9:
            continue
        banks[cross_s >= 0.0].append((r, k))
    a_bank = sorted(banks[False])
    b_free = sorted(banks[True])
    new_sew = []
    for ra, ka in a_bank:
        best = None
        for bi, (rb, kb) in enumerate(b_free):
            if kept_at.get(ka, set()) & kept_at.get(kb, set()):
                continue                      # shares a face -> same bank edge
            if best is None or abs(rb - ra) < abs(b_free[best][0] - ra):
                best = bi
        if best is not None and abs(b_free[best][0] - ra) < length * 0.5:
            new_sew.append((ka, b_free.pop(best)[1]))
    if not new_sew:
        raise ValueError("corner_dart: cut has no pairable banks — the fan ate "
                         "a whole strip; shrink angle or length")
    # remap to the kept population, dropping orphans
    remap, verts2 = {}, []
    for f in kept:
        for k in f:
            if k not in remap:
                remap[k] = len(verts2)
                verts2.append(verts[k])
    faces2 = [tuple(remap[k] for k in f) for f in kept]
    sew2 = [(remap[a], remap[b]) for a, b in list(sew) + new_sew
            if a in remap and b in remap and remap[a] != remap[b]]
    return verts2, faces2, sew2


def corner_dart_sites(mitre, keep, cell, min_cells=3.0):
    """Where a ROUND-CUT corner's dart goes — derived from the mitre's own
    geometry, nothing typed (R9). dr-cloth-corner-drape-2026-08-11 rank 4 put
    the dart on the duvet's SQUARE corners at p2r13 and the corner read moved
    class the same round; the coverlet's corners are cut round (mitre), so the
    corner point the duvet anchored to does not exist here — the cloth's own
    corner is the arc's diagonal DIP point (_mitre_radius dips to `keep` on the
    diagonal). Anchor there, and size the dart so corner_dart's own arithmetic
    (apex = anchor + length/sqrt(2) per axis, inward) lands the apex EXACTLY on
    the inner corner (ix, iy) — the mattress corner the drape pivots around, so
    the seam closes the hanging corner cloth into a cone and eats no lying
    cloth. A dart under `min_cells` grid cells is below the lattice's own
    resolution: it is SKIPPED and reported, because a sub-resolution dart is a
    mechanism that pretends to run (the --factory-startup family of lie).

    Returns (sites, skipped): sites as [((x, y), length)], skipped as
    human-readable strings the caller must PRINT, not swallow."""
    inv = 1.0 / math.sqrt(2.0)
    sites, skipped = [], []
    for (cx0, cy0, cx1, cy1, ix, iy) in mitre:
        sx, sy = cx1 - cx0, cy1 - cy0
        sgx = -1.0 if cx0 < ix else 1.0     # which way the corner block sticks out
        sgy = -1.0 if cy0 < iy else 1.0
        dip = (ix + sgx * keep * inv * sx, iy + sgy * keep * inv * sy)
        length = keep * 0.5 * (sx + sy)     # square by construction; mean is exact there
        if length < min_cells * cell:
            skipped.append("corner dart SKIPPED at (%.2f, %.2f) — derived length "
                           "%.0f mm is under %.0f cells; a sub-resolution dart "
                           "would read as a mechanism that ran"
                           % (ix, iy, length * 1000.0, min_cells))
            continue
        sites.append((dip, length))
    return sites, skipped


def boundary_verts(faces):
    """Vertex indices on the FREE BOUNDARY of a sheet — every edge used by
    exactly ONE face. Pure topology, so it is still right after corner_dart
    remaps indices (recompute AFTER the cut, never before — the same
    index-shift trap corner_dart's `sew` parameter documents).

    This is where a sewn hem physically lives: real bedding is hemmed on every
    free edge (turned under, stitched — two to three layers of cloth), and a
    dart's two cut banks are boundary edges too, so the seam that closes them
    inherits the same doubled read. The r18 critics filed the missing cue from
    both sides — C2: no hem/seam cue on any sewn good; C3: fold edges 'คมและ
    แข็งเหมือนแผ่นพลาสติก' — and the bed_base welts are the precedent: a CUE
    derived from what exists, never a redesign."""
    cnt = {}
    for f in faces:
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            e = (a, b) if a < b else (b, a)
            cnt[e] = cnt.get(e, 0) + 1
    out = set()
    for (a, b), c in cnt.items():
        if c == 1:
            out.add(a)
            out.add(b)
    return out


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
# 1.03 -> 1.10 at round 4-ref: the delivered-closet reference (I-24-062 #125386)
# shows sleeve cuffs splaying OUT past the shoulder tips; the splay is capped at
# 0.05*width inside garment(), so 1.10 stays the true span bound.
GARMENT_FLARE = 1.10
# Sleeve overhang budget, published for the caller's clear-drop solve: a hanging
# shirt's cuffs are its LOWEST point (same reference — cuffs fall past the body
# hem). lowest_z >= -(drop * SLEEVE_OVER + SLEEVE_PAD).
SLEEVE_OVER = 1.12
SLEEVE_PAD = 0.040


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


# --------------------------------------------------------------------------
# De-periodised slack (p2r24). Published so tests, drape.py and build_room.py
# share one truth. ENVELOPE scale on purpose: every wavelength sits well above
# the solved fold pitch (~60-100 mm at cell 0.022-0.028), so the field steers
# WHERE the solver spends its rest-length excess and never authors a wrinkle
# itself — the enter-smooth law (sim feedstock is FLAT; the solver is the only
# wrinkle author, round 5c) is untouched. Three incommensurate wavelengths for
# _crease's own reason: ONE frequency is a corrugation, several that never
# re-align read as cloth.
SLACK_WAVELENGTHS = (1.13, 0.47, 0.23)   # m, plan-space plane waves
SLACK_WAVE_AMPS = (0.5, 0.33, 0.22)


def slack_field(verts, salt=0, depth=0.5):
    """Per-vertex slack MULTIPLIER over the plan: 1 + depth * m(x, y) with
    m in [-1, 1] summed from three plane waves at incommensurate wavelengths,
    directions and phases drawn from the dev() recurrence family per `salt`.

    WHY (p2r24 — C2 and C3 at r23, independently): LINEAR bending bought the
    fall its secondary folds, but UNIFORM slack on a UNIFORM grid buckles at
    one wavelength, and both critics read the free hem as "a deliberate,
    perfectly regular sine". Real folds run in structured families along the
    drape's tension lines, not at a metronome pitch (trn002 reference study,
    knowledge/_inbox/trn002-reference-study). Modulating the excess across the
    sheet moves where buckles seed and how deep they grow — amplitude AND
    spacing stop being periodic while the solver stays the only wrinkle
    author. Deterministic, bounded, pure."""
    if not 0.0 <= depth < 1.0:
        _fail(f"slack_field: depth {depth} outside [0, 1) — a multiplier "
              f"crossing zero would flip slack into stretch")
    if depth == 0.0:
        return [1.0] * len(verts)
    waves = []
    norm = float(sum(SLACK_WAVE_AMPS))
    for k, (lam, amp) in enumerate(zip(SLACK_WAVELENGTHS, SLACK_WAVE_AMPS)):
        ang = 2.0 * math.pi * (((k + 1) * PHI_INV + salt * _SALT) % 1.0)
        ph = 2.0 * math.pi * (((k + 3) * PHI_INV + (salt + 11) * _SALT) % 1.0)
        waves.append((math.cos(ang), math.sin(ang),
                      2.0 * math.pi / lam, ph, amp / norm))
    return [1.0 + depth * sum(a * math.sin((dx * x + dy * y) * w + ph)
                              for dx, dy, w, ph, a in waves)
            for (x, y, _z) in verts]


def modulate_slack(weights, verts, salt=0, depth=0.5):
    """Apply slack_field to a {vertex index: weight} dict. Weights clamp to
    [0, 1] — they are vertex-group weights; bake_sheet lerps shrink from 0 to
    the full slack across them, so a weight above 1 has no meaning. depth=0
    returns an EQUAL dict: a disabled flag is byte-identical by construction."""
    field = slack_field(verts, salt=salt, depth=depth)
    return {i: min(1.0, max(0.0, w * field[i])) for i, w in weights.items()}


# --------------------------------------------------------------------------
# Plan-slab penetration (p2r24 garment-swing clamp). Pure: hanging garments on
# one rail share the same z band by construction, so PLAN penetration is volume
# penetration, and the clamp can be unit-tested without a scene.

def rot_aabb_half(hw, hd, theta):
    """Half-extents of the world AABB of a plan slab (half-width hw along its
    own long axis, half-depth hd) rotated by theta about its centre."""
    ca, sa = abs(math.cos(theta)), abs(math.sin(theta))
    return (hw * ca + hd * sa, hw * sa + hd * ca)


def aabb_penetration(c1, h1, c2, h2):
    """Min-axis penetration depth of two plan AABBs ((cx, cy), (hx, hy));
    0.0 when separated or touching.

    This is the SAME instrument the r23 triage used to confirm C2's garment
    interpenetration claim (thin-axis overlap 36-42 mm, three pairs), so the
    clamp drives the number the defect was measured in. An AABB over-reads a
    scissor crossing (R9b: an AABB cannot tell interlocking from
    intersecting) — over-reading here only opens slightly more air between
    garments, which is the safe side of the estimate."""
    ox = h1[0] + h2[0] - abs(c1[0] - c2[0])
    oy = h1[1] + h2[1] - abs(c1[1] - c2[1])
    return min(ox, oy) if (ox > 0.0 and oy > 0.0) else 0.0


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
            sleeves=False, carve=True):
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
    # carve=False = SMOOTH FEEDSTOCK for the solver (round 5c): every cloth that
    # ever passed in this room entered the sim smooth (the bed sheets are flat
    # grids); the garments were the only feedstock pre-wrinkled by hand, and two
    # wrinkle-authors fighting is where the unstabilisable pieces came from.
    # Analytic (non-sim) garments keep the carve — it is their only wrinkle author.
    fold_in = 0.018 * (0.7 + 0.3 * abs(dev(12, 1.0, salt + 83))) if carve else 0.0
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
            # irregular CRUMPLE (reference I-24-062: worn cloth wrinkles run in every
            # direction, not only as vertical valleys) — per-vertex, growing downward
            if carve:
                y += 0.004 * dev(i * 7 + j * 13, 1.0, salt + 87) * (v ** 0.8)
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
        # REFERENCE (delivered closet I-24-062 #125386, the round-4-ref board): the
        # sleeves are the LOWEST part of a hanging shirt — free tubes falling PAST
        # the body hem, splaying slightly outward, ending in a visible CUFF (a small
        # flare, then the buttoned pinch). The first cut guessed sleeves from priors
        # and hid them against the body; this one copies what the reference shows.
        long_s = dev(8, 1.0, salt + 61) > -0.35              # most sleeves are long
        # g9 full-fidelity LOOK vs the reference: wide-set splayed tubes read as an
        # OPEN coat flapping; the reference's sleeves hang CLOSE, overlapping the
        # body's edge. So: cuffs sit near the hem line (not dangling far below),
        # splay is a whisker, and the tube hugs the body face.
        s_len = drop * ((0.98 + 0.10 * abs(dev(9, 1.0, salt + 71))) if long_s else 0.55)
        splay = min(0.008, 0.03 * width)     # cuff drift OUT past the tip — inside GARMENT_FLARE
        rx_s = min(0.040, 0.20 * 0.5 * width)
        ry_s = min(0.024, 0.45 * 0.5 * depth)
        nus, nvs = 8, 7
        for side in (-1.0, 1.0):
            # (outside-birth was tried at round 5c and REFUTED by LOOK: with only
            # gravity, a tube born 3 mm off the body never returns — it hangs as a
            # separate stick. Inside the face band, self-collision keeps it honest.)
            yo = (0.5 * depth * 0.72 - 0.5 * ry_s) * (side if dev(10, 1.0, salt + 79) > 0 else -side)
            base = len(verts)
            for j in range(nvs + 1):
                v = j / float(nvs)
                taper = 1.0 - 0.24 * v
                if j == nvs - 1:
                    taper *= 1.18                            # the cuff's flare...
                if j == nvs:
                    taper *= 0.30                            # ...and its buttoned pinch
                xc = side * ((0.5 * width - rx_s) + splay * (v ** 1.6))
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


def hanger(width, hook_r=0.020, bar_drop=0.030, salt=0, arm_drop=0.0):
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
    t = 0.005                                # wire thickness — a hanger is WIRE. At 6mm,
    #                                          nine of them per rail rendered as a band of
    #                                          black sticks that dominated the frame; at
    #                                          3.5mm the C2 cold critic read the hangers as
    #                                          MISSING (hook invisible at render distance,
    #                                          round-6 lane C). 5mm is the slim black
    #                                          hanger of the closet reference: the hook
    #                                          reads, and a dressed rail still shows cloth,
    #                                          not sticks (garments cover their own arms).
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

def folded_knit(w, d, h, nu=17, salt=0, roll=0.42, sq=6.0):
    """ONE folded knit/towel: a soft-cornered RECTANGULAR slab — flat top and bottom,
    near-vertical sides, and a fold-roll radius (`roll*h`) where face meets side.

    WHY THIS EXISTS BESIDE `cushion` (P2r-4 folded half, LOOK 2026-08-12 on p2r20 at
    3x): the shelf stacks wore `cushion(pinch=0.06, edge=0.22)`, whose plan is a
    near-ellipse and whose radius profile `sin(phi)**edge` reaches full width only at
    mid-height — four of those stacked read as PANCAKES, and the reference of record
    (anchor I-24-062 file 206336_09-2-open.jpg, a delivered dressing room) shows
    folded knits as rectangles: flat top, sides that stay full-width, a small roll at
    the fold edges, silhouette lines that waver a millimetre — never ruler-straight,
    never domed. `cushion` cannot express a vertical side by its own math (a power of
    sin always domes), so the folded item gets its own profile rather than a cushion
    bent to a parameter corner the next reader has to decode.

    The cross-section is authored as a PROFILE SCHEDULE (R8 case (c), an extruded
    outline): flat bottom face -> quarter-round roll -> vertical side -> quarter-round
    roll -> flat top face, swept around a superellipse plan (exponent `sq`; corners
    soft but square). Stays INSIDE (0..w, 0..d) — the waver is inward-only — and
    fills 0..h EXACTLY (the stack's headroom contract); deterministic via
    `dev`/golden-phase; `salt` de-twins the edge waver between items."""
    if w <= 0 or d <= 0 or h <= 0:
        _fail(f"folded_knit: degenerate {w}x{d}x{h}")
    if not 0.05 <= roll <= 0.5:
        _fail(f"folded_knit: roll {roll} outside 0.05..0.5")
    cx, cy = w * 0.5, d * 0.5
    rr = min(roll * h, 0.4 * min(cx, cy))   # roll can never eat the plan
    # Row schedule down the cross-section boundary: (kind, t) where kind "face" rows
    # carry t = plan-scale s (0 = centre pole), and "roll"/"side" rows carry t = the
    # ABSOLUTE inset from the full outline (a real fold-roll is millimetres of inset,
    # not a proportion — a proportional roll on the long axis reads as a dome again).
    quarter = [(math.radians(q)) for q in (28.0, 58.0, 90.0)]
    rows = ([("face", 0.0, 0.0), ("face", 0.55, 0.0), ("face", 0.92, 0.0)]
            + [("roll", rr * (1.0 - math.sin(t)), rr * (1.0 - math.cos(t)))
               for t in quarter]
            + [("side", 0.0, h * 0.5)]
            + [("roll", rr * (1.0 - math.sin(t)), h - rr * (1.0 - math.cos(t)))
               for t in reversed(quarter)]
            + [("face", 0.92, h), ("face", 0.55, h), ("face", 0.0, h)])
    ph = 2.0 * math.pi * ((salt + 1) * PHI_INV % 1.0)
    verts = []
    for j, (kind, t, z) in enumerate(rows):
        for i in range(nu + 1):
            u = i / float(nu)
            a = 2.0 * math.pi * u
            ca, sa = math.cos(a), math.sin(a)
            sx = math.copysign(abs(ca) ** (2.0 / sq), ca)
            sy = math.copysign(abs(sa) ** (2.0 / sq), sa)
            if kind == "face":
                ex, ey = (cx - rr) * t, (cy - rr) * t
            else:
                ex, ey = cx - t, cy - t
            # edge waver, INWARD-only so the footprint stays exact: strongest on the
            # side/roll rows (the visible silhouette), zero at the centre poles
            wav = (0.5 - 0.5 * math.cos(math.pi * min(z, h - z) / max(h * 0.5, 1e-9))
                   if kind != "face" else t * 0.3)
            wob = 1.0 - 0.02 * wav * (1.0 + math.sin(2.0 * a + ph)) * 0.5 \
                - abs(dev(i * 13 + j, 0.008, salt=salt + 3)) * wav
            verts.append((cx + ex * sx * wob, cy + ey * sy * wob, z))
    return verts, _loft_faces(len(rows) - 1, nu)


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
    # PER-ITEM HEIGHT (round-6 lane C, C2#9 "perfect boxes"): equal slices are the one
    # thing a pile of folded knits never has — each item's thickness varies ±12%, then
    # the set is renormalised so the cumulative height stays EXACTLY n*item_h (the
    # caller's headroom contract against the shelf above is not negotiable).
    hs = [item_h * (1.0 + dev(k, 0.12, salt + 17)) for k in range(n)]
    hs = [hk * (n * item_h) / sum(hs) for hk in hs]
    out, z = [], 0.0
    for k in range(n):
        ox = dev(k, jitter_xy, salt)
        oy = dev(k, jitter_xy, salt + 5)
        sw = w * (1.0 - 0.035 * (k / max(n - 1, 1)))         # a stack tapers upward
        sd = d * (1.0 - 0.030 * (k / max(n - 1, 1)))
        out.append((ox + (w - sw) * 0.5, oy + (d - sd) * 0.5, z, sw, sd, hs[k]))
        z += hs[k]
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
