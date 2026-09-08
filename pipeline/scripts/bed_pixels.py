#!/usr/bin/env python3
"""bed_pixels.py — R11 on a NAMED OBJECT: is our own mattress core visible in the frame?

    python pipeline/scripts/bed_pixels.py <beauty.png> <idmask.png> <idmask.json>
           [--scene <scene.json>] [--overlay <out.png>] [--json <out.json>] [--soft]
    python pipeline/scripts/bed_pixels.py --selftest

Exit: 0 the core is covered · 1 the core is showing · 2 COULD NOT RUN.

WHY IT EXISTS
-------------
On 2026-08-17 the bed was measured for the first time in the space the sighted
readers, the critics and the owner all judge in — IMAGE space, by object mask,
on `room_bedroom_suite_eye_p2r49`. Of the visible sleeping surface:

    acquired duvet (lofted)   182,192 px   31.5%
    acquired flat sheet       124,678 px   21.6%
    OUR OWN MATTRESS BOX      270,691 px   46.9%     delivered work: 0% on 7 of 7

The largest single thing in our bed is our own 218-polygon mattress. On that bed
the hand-built parts are 0.29% of the polygons and 57.4% of the pixels.

AND EVERY ACCEPTANCE NUMBER FOR THE BED WAS BLIND TO IT BY CONSTRUCTION. They are
computed in PLAN, by a top-down ray grid over the mattress rectangle, and the
failure is on the mattress's VERTICAL FLANKS, which have no plan area at all:

  * `coverage` 94.0% counts cloth ABOVE the mattress; a flank cannot be counted.
  * `fall_sides` 4/4 counts how MANY flanks carry cloth and never how MUCH, while
    the shipped cover is 86 mm narrower than the mattress (1734 vs 1820) and so
    reaches neither long flank; the flank it fails to reach is 396 mm of vertical
    face.
  * `p2_exit.duvet_fold` — the exit test's flagship crop, frozen in FRAME space —
    lands on 55.0% flat sheet, 40.8% mattress, 0.9% duvet. It has been scoring OUR
    MATTRESS against THEIR COMFORTER.
  * The render gate imported eleven modules, exactly one opened the picture, and
    that one scores the WHOLE FRAME. Nothing measured a NAMED OBJECT in the
    rendered image, though `id_mask` and `value_probe` had existed for weeks.

WHAT IT BLOCKS ON, AND WHY THAT IS NOT THE DEFECT ITSELF
--------------------------------------------------------
This rung started as a flat cut at the delivered value. Run BACKWARDS over every
masked frame this lane has on disk — the negative control that should precede any
new cut — that flat cut fails 15 of 15. It separates nothing, because a bare
mattress flank is in every frame this studio has ever made. A rung that is red on
every render is a rung somebody switches off, which CLAUDE.md says in R13's own
words, and it would halt the very rounds whose job is to fix it (R3).

What the same sweep DID show is a regression nothing caught:

    p2r31e   bare flank  11,694 px     hand-built cloth stack
    p2r44    bare flank 295,661 px     bought set
    p2r49    bare flank 254,849 px     bought set

a 23x rise across the rounds that replaced hand-built cloth with an acquired set,
while `coverage` read 94.0% and `fall_sides` read 4/4 the entire way — because
both are computed in PLAN and a vertical flank has zero plan area.

**THIS IS NOT AN ARGUMENT FOR REVERTING TO HAND-BUILT CLOTH.** His standing order
is that the bed cloth is ACQUIRED, given twice, and R13 exists because the builder
once read an instance verdict as repealing that class order. What p2r31e proves is
narrower and more useful: core-near-zero is REACHABLE on this bed, this camera and
this room, so the target is a property of the ASSET and not of the frame — and the
acquisition now has an acceptance test it never had.

So the split is:

  * BLOCKS — the number RISING against `qa/bed-pixels-baseline.json`, and the rung
    going BLIND (an object over the mattress wearing a material no role claims).
    Both are the builder's side, and both are matters of fact rather than degree.
  * PRINTS, on every run, into the render path, which is the channel the owner
    actually reads — the standing absolute number and how far it is from delivered
    work. It may never print like a pass, and the summary line is written off it.

The sliver floor is `value_probe.MIN_PIXELS`, this repo's existing definition of
"a sliver: reported, never ranked", reused rather than invented so an anti-aliased
rim cannot fail a genuinely made bed.

WHERE THE TARGET COMES FROM
---------------------------
Three fresh-context sighted readers (R10b), each given the seven delivered
bedroom frames plus our own p2r49, unlabelled, in a different fixed order, all
normalised to PNG at one long edge so neither format nor resolution could identify
ours. One written question: is any part of the mattress's vertical side face bare,
with a taut fitted sheet counting AS bare because it is the mattress's own shape
rather than bedding laid over it.

    delivered   16 of 18 legible readings `none`, 2 `sliver`, NONE above sliver
    ours        `most`, 3 readers of 3, none of them told which frame was ours

Archived with every per-frame answer at
`_private/deliv-001/flank-panel-2026-08-17/readings.json`. It establishes a FACT
and a DIRECTION, not a pixel number — the readers answer on a word scale and
delivered frames carry no object mask, so no delivered flank can be counted in
pixels. A cut is never typed by the builder (R4b).

WHY THE ROLES COME FROM THE MATERIAL AND NOT FROM THE NAME
----------------------------------------------------------
R9b: *"a rule that names the objects it applies to will always exempt the next
one"* — the guard it replaced covered 2 of 5 placed classes and every figure was
exempt. So this module never matches an object name. It reads the MATERIAL each
mesh renders in, which is the studio's own written statement of what the thing IS
(`value_ladder.MATERIAL_TONE` is keyed on the same six tokens), and it takes that
from the scene dump — surveyed across all 96 dumps on disk, every bed object in
this lane's history carries exactly one of six materials and none is missing.

Two assertions keep the derivation from going quietly blind, and both FAIL CLOSED:

  1. If no object in the mask roster carries the CORE role, the rung REFUSES
     (exit 2). It must never report 0% because it could not find the mattress.
     "Could not look" must never print like "looked and it was fine".
  2. Any object that OVERLAPS THE CORE IN PLAN, carries more than a sliver of
     visible pixels, and wears a material this table does not know is a
     VIOLATION naming the material. That is the object which might be bedding or
     might be core and nobody said which — the next one the allowlist would have
     exempted.

WHAT IT CANNOT SEE, said before anyone trusts it. It answers "is the core
visible", not "is the bed beautiful" and not "is the cloth believable". A duvet
that covers every pixel of the mattress and still reads as crumpled plastic passes
this rung — that judgment belongs to the critic ladder (R7/R7b/R7c) and to the
owner's eye (R3), and this replaces neither. It also cannot see the mattress's
TOP plane separately from its FLANK; it reports the core's pixel bbox so the
split is at least visible to a reader.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_probe as _vp                    # palette codec + the sliver floor

CORE = "core"          # the mattress body: the thing a made bed hides
BEDDING = "bedding"    # every cloth laid over it
FRAME = "frame"        # base, welts, headboard — furniture, not sleeping surface
HEAD = "head"          # pillows: cloth, but at the head, and not coverage
OTHER = "other"        # in the mask roster but not part of the bed at all

# WHAT EACH MATERIAL IS, in the vocabulary the build already writes into every
# scene dump. Surveyed 2026-08-17 across all 96 dumps in pipeline/output: bed
# objects wear exactly these six tokens and nothing else, in every round from
# p2r2 to p2r50. This is a ROLE table, not an allowlist — an object wearing a
# token that is not here does not become exempt, it becomes a violation (see
# `check`), provided it can touch the core.
ROLE_BY_MATERIAL = {
    "bed_mattress": CORE,
    "bed_coverlet": BEDDING,
    "bed_duvet":    BEDDING,
    "bed_throw":    BEDDING,
    "bed_pillow":   HEAD,
    "bed_base":     FRAME,        # base, welts and headboard: one upholstery token
    # p2r74: the 144 mm acquired headboard re-derived the bed's head contact
    # and moved the whole bed 84 mm toward the foot, so the mattress plan now
    # laps the foot bench by 41 mm (the duvet fall drapes over the bench edge —
    # real made-bed behaviour). The bench then tripped assertion 2 as an
    # UNKNOWN material touching the core. It is CLASSIFIED, not exempted-by-
    # being-new: a bench is furniture at the foot, never sleeping surface —
    # the same sentence bed_base carries.
    "acq_bench_seat": OTHER,      # foot bench (P2h role-split token)
    # ORD-25c: the acquired bed-foot throw (panel 2026-08-25d) lies ON the
    # core by design — bedding, same sentence as bed_throw; build_room renames
    # the scan's material to this name at import so the role channel holds.
    "acq_bed_throw": BEDDING,
    # p2r91 (D-181): ceiling luminaire anatomy — downlight/wash trim rings and
    # aperture discs at z~2.79 m. They overlap the mattress ONLY in plan, which
    # is the one axis this rung's overlap test reads, and a light fitting is
    # never sleeping surface — the same sentence acq_bench_seat carries. This
    # is a CLASSIFICATION, not an exemption: their pixels still count in the
    # roster, they just answer OTHER when asked "are you lying on the bed".
    "e5_trim_dark": OTHER,
    "e5_trim_lens": OTHER,
}

# WHERE THIS DISAGREES WITH THE 2026-08-17 DIAGNOSIS, said out loud so the two
# numbers reconcile instead of quietly differing. That probe read 46.9% by taking
# the sleeping surface as mattress + flat sheet + duvet and excluding the two
# SHAMS; this rung reads 44.0% on the same frame because the shams wear
# `bed_duvet` and no material can tell a sham from the duvet it matches — the
# ladder says so in its own words, *"a duvet cover and its euro shams are one
# fabric"* (value_ladder.HEAD_CLOTH). The verdict is identical either way, and
# that is the point of putting the CUT on the count: 270,691 px of visible core
# is 270,691 px whichever denominator is under it.

SLIVER_PX = _vp.MIN_PIXELS      # 200 — "below this an object is a sliver:
#                                 reported, never ranked" (value_probe)


class CouldNotRun(Exception):
    """The measurement could not be taken — a DIFFERENT answer from "the bed is
    made". Exit code 2, never 0. Same contract as pixel_check.NotComparable."""


# --------------------------------------------------------------------------- inputs

def load_sidecar(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if not (d.get("ids") or {}):
        raise CouldNotRun(f"{path}: no `ids` block — re-run id_mask.py")
    return d


def record_fused_body(sidecar_path, name):
    """Put the build's fused-body DECLARATION into THE FRAME'S OWN RECORD.

    Found 2026-08-23 by the frame corpus this module's own test walks: since
    p2r54 the staged bed is one shell, so the core exists only where the build
    DECLARES which object is the body — and that declaration lived nowhere but
    the command line `build_room` spawns this rung with (`--fused-body`). The
    rung therefore ran correctly at build time and NO LATER READER COULD EVER
    REPRODUCE IT: p2r54..p2r57 re-measure as `core_objects: []`, which is this
    module refusing exactly as designed, on four frames whose bed is right
    there in the mask.

    That is D-032's law one layer down — "a render state that lives only in the
    command line is reverted by forgetting to type it" — except a record cannot
    be re-typed after the fact. It is also the shape this module already warns
    about in `measure`: the semantics travel in the result so the ratchet can
    refuse to compare across them, which is worth nothing if the semantics do
    not survive the render that produced them.

    Written by the rung that RECEIVES the declaration, and only after the frame
    has corroborated it (see `main`), so a name the mask does not contain is
    never recorded. Idempotent. A DIFFERENT stored name is a disagreement
    between two builds about what the frame is made of, and this raises rather
    than overwriting — the same law the flag itself obeys three functions down:
    a rung must not pick a side silently.

    Returns "written" | "already".
    """
    with open(sidecar_path, encoding="utf-8") as f:
        d = json.load(f)
    have = d.get("fused_body")
    if have == name:
        return "already"
    if have:
        raise CouldNotRun(
            f"{sidecar_path} already records the fused bed body {have!r} and "
            f"this run declares {name!r}. Two builds disagree about what this "
            f"frame is made of; a record is not overwritten to settle it.")
    d["fused_body"] = name
    tmp = sidecar_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, sidecar_path)
    return "written"


def materials_from_dump(dump_path):
    """{object_name: [material, ...]} from a scene dump.

    PREFERRED over the mask sidecar's `wears`, and the reason is a real corruption
    on disk: `id_mask` captures `wears` after `map_census_mask` has already
    repainted every slot unless the caller passes a snapshot, and
    room_bedroom_suite_eye_p2r4's sidecar records all 21 of its objects wearing
    `census__5`..`census__10` — a real dict of real strings naming materials that
    existed for two seconds. The dump is written before any mask runs.
    """
    with open(dump_path, encoding="utf-8") as f:
        d = json.load(f)
    return {o["name"]: list(o.get("materials") or [])
            for o in (d.get("objects") or []) if o.get("name")}


def aabbs_from_dump(dump_path):
    with open(dump_path, encoding="utf-8") as f:
        d = json.load(f)
    return {o["name"]: o.get("aabb") for o in (d.get("objects") or [])
            if o.get("name") and o.get("aabb")}


def assert_dump_is_this_frames(dump_path, beauty_path):
    """The dump must come from the build that produced this beauty frame.

    `compose` already refuses a mask from another render, because `value_probe`
    paid for that rule: measuring one camera's pixels through another camera's
    mask "produces numbers that look exactly like evidence". The DUMP is the
    third file in the same joint and it was unguarded — and it decides both the
    roles and the mattress AABB the top/flank split is projected from.

    Measured before this guard existed: pairing p2r49's frame with p2r45's dump
    reports the core at 87.7% of the sleeping surface instead of 44.0%, silently,
    with the ratchet printing `held`. The build always writes the two together,
    so this can only be reached from the CLI — which is exactly where a probe
    gets pointed at last round's dump by hand.
    """
    with open(dump_path, encoding="utf-8") as f:
        blend = (json.load(f) or {}).get("blend")
    if not blend:
        raise CouldNotRun(f"{os.path.basename(dump_path)} records no `blend`, so "
                          f"there is no way to tell which render it describes")
    want = os.path.splitext(os.path.basename(beauty_path))[0]
    got = os.path.splitext(os.path.basename(blend))[0]
    if got != want:
        raise CouldNotRun(
            f"DUMP/BEAUTY MISMATCH: the scene dump was written from {got!r} but "
            f"the beauty frame is {want!r}. The dump decides every object's role "
            f"and the mattress AABB the top/flank split projects from, so this "
            f"would produce a number that looks exactly like evidence.")


def materials_for(sidecar, dump_path=None):
    """The material map, and WHERE it came from, so the report can say which.

    Raises CouldNotRun when neither source exists: a rung with no way to tell a
    mattress from a duvet has not measured a covered bed, it has not measured."""
    if dump_path and os.path.isfile(dump_path):
        m = materials_from_dump(dump_path)
        if m:
            return m, f"scene dump {os.path.basename(dump_path)}"
    wears = sidecar.get("wears") or {}
    if any(str(v).startswith("census__")
           for vals in wears.values() for v in vals):
        raise CouldNotRun(
            "the mask sidecar's `wears` records census__ materials — the snapshot "
            "was taken after map_census_mask repainted every slot, so it names "
            "materials that existed for two seconds. Pass --scene <scene.json>.")
    if wears:
        return {k: list(v) for k, v in wears.items()}, "id-mask sidecar `wears`"
    raise CouldNotRun(
        "no scene dump given and the mask sidecar carries no `wears` — there is "
        "no way to tell which mesh is the mattress. A rung that cannot name the "
        "core must not report that the core is covered.")


# --------------------------------------------------------------------------- roles

def roles_of(names, materials):
    """({object: role}, [(object, material)]) — the classified and the unknown.

    PURE. `names` is the mask roster {id: name}; `materials` is {name: [mat]}.
    An object with no material recorded at all is returned as unknown with
    material None, never silently dropped."""
    out, unknown = {}, []
    for nm in names.values():
        mats = materials.get(nm) or []
        role = next((ROLE_BY_MATERIAL[m] for m in mats if m in ROLE_BY_MATERIAL),
                    None)
        if role is None:
            unknown.append((nm, mats[0] if mats else None))
        else:
            out[nm] = role
    return out, unknown


def plan_overlaps(aabbs, core_names, pad_m=0.0):
    """{object names whose PLAN footprint intersects any core object's}.

    PURE. This is what makes assertion 2 tight rather than sweeping: an object
    across the room cannot be mistaken for uncovered bedding, and an object
    sitting on the mattress cannot be exempt for wearing a material nobody
    classified."""
    boxes = [aabbs[n] for n in core_names if aabbs.get(n)]
    hit = set()
    for nm, bb in aabbs.items():
        if not bb:
            continue
        (x0, y0, _), (x1, y1, _) = bb[0], bb[1]
        for (cx0, cy0, _), (cx1, cy1, _) in ((b[0], b[1]) for b in boxes):
            if (x0 - pad_m <= cx1 and x1 + pad_m >= cx0
                    and y0 - pad_m <= cy1 and y1 + pad_m >= cy0):
                hit.add(nm)
                break
    return hit


# --------------------------------------------------------------------------- projection

# A projected AABB is a SUPERSET of the mesh inside it, so the self-check below
# asserts containment, not equality — and it allows this much slack for the
# near-box mask filter and float rounding.
PROJ_TOL_PX = 6.0
PROJ_MIN_PX = 3000          # objects smaller than this are too slivered to check


def camera_from(sidecar, w, h):
    """The pinhole the frame was rendered with, from the mask sidecar's own
    fingerprint. Raises CouldNotRun when the sidecar predates it."""
    src = sidecar.get("source") or {}
    if not (src.get("matrix") and src.get("lens") and src.get("shift")):
        raise CouldNotRun(
            "the mask sidecar carries no camera fingerprint (matrix/lens/shift), "
            "so the mattress's TOP cannot be told from its FLANK on this frame")
    return {"matrix": src["matrix"], "lens": float(src["lens"]),
            "shift": [float(x) for x in src["shift"]], "w": int(w), "h": int(h)}


def project(points, cam):
    """World points (N,3) -> image (u, v) pixels, (N,2), NaN behind the camera.

    build_room pins `sensor_fit='HORIZONTAL'` on a 36 mm sensor, so BOTH axes
    scale by the image WIDTH and the aspect ratio is pure framing.

    THE SIGN OF `shift_y` IS EMPIRICAL, NOT ASSUMED, and the difference is 384 px
    on the hero frame — bigger than the feature this split exists to find. It was
    settled by the positive control in `projection_selfcheck`, which reproduces
    every large masked object's own pixel extent: `bed__headboard_welt_top`
    measures rows 727-744 and projects to 727-744.
    """
    import numpy as np
    P = np.asarray(points, float)
    M = np.linalg.inv(np.asarray(cam["matrix"], float))
    hom = np.concatenate([P, np.ones((len(P), 1))], axis=1)
    p = hom @ M.T
    z = -p[:, 2]
    k = cam["lens"] / 36.0 * cam["w"]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = cam["w"] * (0.5 + cam["shift"][0]) + p[:, 0] / z * k
        v = cam["h"] * 0.5 - p[:, 1] / z * k + cam["w"] * cam["shift"][1]
    bad = z <= 1e-6
    u[bad] = float("nan")
    v[bad] = float("nan")
    return np.stack([u, v], axis=1)


def _aabb_corners(bb):
    (x0, y0, z0), (x1, y1, z1) = bb[0], bb[1]
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def projection_selfcheck(ids, names, aabbs, cam):
    """(ok, [line]) — does the projection reproduce the mask it will be used on?

    R11's SELF-CHECK-FIRST rule, and pixel_check's own: a derived number whose
    derivation no longer describes the file is arithmetic about nothing. Every
    object big enough to measure must have its MEASURED pixel rows contained in
    its PROJECTED AABB rows. If any fails, the split is not reported at all —
    a wrong split would put bare mattress in the 'top' bucket, which is the one
    place a flattering number could hide."""
    import numpy as np
    lines, ok = [], True
    for i, nm in names.items():
        bb = aabbs.get(nm)
        if not bb:
            continue
        sel = ids == i
        n = int(sel.sum())
        if n < PROJ_MIN_PX:
            continue
        ys, _xs = np.nonzero(sel)
        pv = project(_aabb_corners(bb), cam)[:, 1]
        if not np.isfinite(pv).all():
            lines.append(f"  {nm}: an AABB corner is behind the camera")
            ok = False
            continue
        lo, hi = float(np.nanmin(pv)), float(np.nanmax(pv))
        if ys.min() < lo - PROJ_TOL_PX or ys.max() > hi + PROJ_TOL_PX:
            lines.append(f"  {nm}: measured rows {ys.min()}-{ys.max()} fall "
                         f"outside projected {lo:.0f}-{hi:.0f}")
            ok = False
    return ok, lines


def split_core(ids, core_ids, bedding_ids, core_bb, cam):
    """(core_top, core_flank, bedding_top) pixel counts.

    The mattress's TOP FACE is projected as a quad; a core pixel inside it is the
    top plane and a core pixel outside it is the vertical FLANK. The split exists
    because the two have different authorities: the sighted-reader panel measured
    the TOP plane only — its written method excludes "all drape below the
    mattress-top line" — so the top share is comparable to delivered work and the
    flank is a separate question with its own reading."""
    import numpy as np
    (x0, y0, _z0), (x1, y1, z1) = core_bb[0], core_bb[1]
    quad = project([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], cam)
    if not np.isfinite(quad).all():
        raise CouldNotRun("the mattress's top face does not project (a corner is "
                          "behind the camera)")
    sel = np.isin(ids, core_ids)
    ys, xs = np.nonzero(sel)
    inside = _in_quad(xs + 0.5, ys + 0.5, quad)
    core_top = int(inside.sum())
    core_flank = int(len(xs) - core_top)
    bys, bxs = np.nonzero(np.isin(ids, bedding_ids))
    bed_top = int(_in_quad(bxs + 0.5, bys + 0.5, quad).sum()) if len(bxs) else 0
    return core_top, core_flank, bed_top


def _by_material(px_by_object, materials):
    """{material: pixels} — the same counts regrouped by what the mesh is made
    of, so a reader can recompute any share this rung does not name."""
    out = {}
    for nm, n in px_by_object.items():
        mats = materials.get(nm) or ["(no material)"]
        out[mats[0]] = out.get(mats[0], 0) + n
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _in_quad(u, v, quad):
    """Boolean mask: are the points inside the convex quad (4,2), cyclic order?"""
    import numpy as np
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    sign = None
    inside = np.ones(len(u), bool)
    for i in range(4):
        ax, ay = quad[i]
        bx, by = quad[(i + 1) % 4]
        cross = (bx - ax) * (v - ay) - (by - ay) * (u - ax)
        if sign is None:
            # Orientation from the quad itself, not assumed: a perspective view
            # from the other side of the bed reverses the winding.
            s = (bx - ax) * (quad[(i + 2) % 4][1] - ay) - \
                (by - ay) * (quad[(i + 2) % 4][0] - ax)
            sign = 1.0 if s >= 0 else -1.0
        inside &= (cross * sign) >= 0
    return inside


# --------------------------------------------------------------------------- measure

def compose(beauty_path, mask_path, sidecar):
    """{name: pixel count} for every id in the roster, plus the core's bbox.

    Raises CouldNotRun on a mask that did not come from this beauty frame — the
    provenance check `value_probe` earned: every non-hero camera in this build
    renders the same size, so a mask from another view passes a shape test and
    mis-attributes every pixel while reading exactly like evidence."""
    import numpy as np
    from PIL import Image

    src = sidecar.get("source") or {}
    b_stem = os.path.splitext(os.path.basename(beauty_path))[0]
    if src.get("blend") and src["blend"] != b_stem:
        raise CouldNotRun(
            f"MASK/BEAUTY MISMATCH: the mask was rendered from {src['blend']!r} "
            f"but the beauty frame is {b_stem!r}.")
    b = np.asarray(Image.open(beauty_path).convert("RGB"))
    m = np.asarray(Image.open(mask_path).convert("RGB")).astype(np.int16)
    if b.shape[:2] != m.shape[:2]:
        raise CouldNotRun(f"beauty {b.shape[:2]} and mask {m.shape[:2]} are not "
                          f"the same size — nothing here can be measured")
    ids = _vp.decode_ids(m)
    names = {int(k): v for k, v in (sidecar.get("ids") or {}).items()}
    px = {}
    for i, nm in names.items():
        px[nm] = int((ids == i).sum())
    return ids, names, px, b


def measure(beauty_path, mask_path, sidecar_path, dump_path=None,
            fused_body=None):
    """The whole measurement, as one dict. Raises CouldNotRun.

    `fused_body` (p2r54): the BUILD's declaration that the staged bed models
    frame and mattress as ONE shell — the named object is the bed BODY and is
    read as the core even though it wears the base upholstery (D3-1's signed
    deep linen, which is what its exposed corners visually are). This is a
    DECLARATION from the layer that staged the mesh, never an inference here:
    without it a roster with no core still REFUSES (the exit-2 law below), and
    with it the core question changes meaning — which is why the semantics
    travel in the result and the ratchet refuses to compare across them."""
    import numpy as np

    side = load_sidecar(sidecar_path)
    # NO FLAG? ASK THE FRAME. `record_fused_body` puts the build's
    # declaration into the sidecar, so a re-measure of an archived frame
    # reproduces the build's reading instead of refusing for want of a
    # command line nobody kept. An explicit argument still wins — the
    # caller that just staged the mesh outranks the file.
    declared_by = "argument" if fused_body else None
    if fused_body is None and side.get("fused_body"):
        fused_body = side["fused_body"]
        declared_by = "frame record"
    if dump_path and os.path.isfile(dump_path):
        assert_dump_is_this_frames(dump_path, beauty_path)
    materials, mat_src = materials_for(side, dump_path)
    ids, names, px, beauty = compose(beauty_path, mask_path, side)
    role, unknown = roles_of(names, materials)
    if fused_body:
        if fused_body not in names.values():
            raise CouldNotRun(
                f"the build declares a fused bed body {fused_body!r} but no such "
                f"object is in the mask roster — the declaration and the frame "
                f"disagree, and a rung must not pick a side silently.")
        role[fused_body] = CORE
        unknown = [(nm, mt) for nm, mt in unknown if nm != fused_body]

    core_names = sorted(n for n, r in role.items() if r == CORE)
    aabbs = aabbs_from_dump(dump_path) if dump_path and os.path.isfile(dump_path) else {}
    touching = plan_overlaps(aabbs, core_names) if (aabbs and core_names) else set()

    by_role = {CORE: 0, BEDDING: 0, HEAD: 0, FRAME: 0, OTHER: 0}
    for nm, n in px.items():
        by_role[role.get(nm, OTHER)] += n
    # An unclassified object goes to OTHER — never to a bed bucket. It is named
    # in the report either way, and it BLOCKS when it can touch the core (see
    # `check`). What it may never do is be quietly absorbed into a bed total:
    # that is how a new piece of bedding would come to prove its own coverage.

    core_px = by_role[CORE]
    sleep = core_px + by_role[BEDDING]
    sleep_head = sleep + by_role[HEAD]

    bbox = None
    core_ids = [i for i, nm in names.items() if role.get(nm) == CORE]
    if core_px:
        sel = np.isin(ids, core_ids)
        ys, xs = np.nonzero(sel)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

    # THE TOP/FLANK SPLIT, and it is REPORTED AS UNAVAILABLE rather than guessed
    # when anything it needs is missing. Its two halves answer to two different
    # authorities and neither may borrow the other's number.
    split, split_why = None, None
    try:
        cam = camera_from(side, beauty.shape[1], beauty.shape[0])
        if not aabbs:
            raise CouldNotRun("no scene dump, so no mattress AABB to project")
        ok, lines = projection_selfcheck(ids, names, aabbs, cam)
        if not ok:
            raise CouldNotRun("the projection does not reproduce this mask:\n"
                              + "\n".join(lines))
        boxes = [aabbs[n] for n in core_names if aabbs.get(n)]
        if not boxes:
            raise CouldNotRun("the core objects carry no AABB in the dump")
        core_bb = [[min(b[0][k] for b in boxes) for k in range(3)],
                   [max(b[1][k] for b in boxes) for k in range(3)]]
        bedding_ids = [i for i, nm in names.items() if role.get(nm) == BEDDING]
        top, flank, bed_top = split_core(ids, core_ids, bedding_ids, core_bb, cam)
        # WHAT IS LYING ON THE TOP PLANE, PER OBJECT. This is the quantity the
        # three sighted readers answered on p2r47 (25 / 30 / 40 percent for the
        # lofted top layer) and it lets anyone recompute their share from this
        # rung's output instead of taking a single number on trust. Measured the
        # day this shipped: the duvet-material pixels are 40.9% of the top plane,
        # inside the readers' own spread and at the top of it — which is the only
        # calibration this instrument has against human eyes, and it is why the
        # plan-space/image-space ambiguity the readings record flagged as
        # unresolved turns out to be 2.3 points (plan 43.2, image 40.9), not the
        # 15 one reader estimated.
        quad = project([(core_bb[0][0], core_bb[0][1], core_bb[1][2]),
                        (core_bb[1][0], core_bb[0][1], core_bb[1][2]),
                        (core_bb[1][0], core_bb[1][1], core_bb[1][2]),
                        (core_bb[0][0], core_bb[1][1], core_bb[1][2])], cam)
        top_by = {}
        for i, nm in names.items():
            s = ids == i
            if not s.any():
                continue
            yy, xx = np.nonzero(s)
            n = int(_in_quad(xx + 0.5, yy + 0.5, quad).sum())
            if n:
                top_by[nm] = n
        # NO `top_share` KEY. A first cut carried one, computed over
        # core+bedding, while the report's table divides by everything on the top
        # plane — two numbers a reader would reasonably assume were the same, and
        # nothing consumed either. A near-duplicate metric with a quietly
        # different denominator is how this lane got 43.2 and 40.9 and 46.9 for
        # "the same" quantity; the per-material table below carries the shares.
        split = {"core_top": top, "core_flank": flank, "bedding_top": bed_top,
                 "top_plane_px": sum(top_by.values()),
                 "top_by_object": top_by,
                 "top_by_material": _by_material(top_by, materials)}
    except CouldNotRun as e:
        split_why = str(e)

    return {
        "frame": os.path.basename(beauty_path),
        "resolution": [int(beauty.shape[1]), int(beauty.shape[0])],
        "core_semantics": (f"fused_body:{fused_body}" if fused_body
                           else "separable"),
        # WHICH LAYER SAID SO. Not decoration: "the build told me" and
        # "the frame remembered" are different evidence, and a frame that
        # can only be measured while its build is still running is the
        # defect record_fused_body exists to end.
        "core_semantics_from": declared_by,
        "material_source": mat_src,
        "roster": len(names),
        "px": px,
        "role": role,
        "unknown": unknown,
        "touching_core": sorted(touching),
        "core_objects": core_names,
        "by_role": by_role,
        "core_px": core_px,
        "sleeping_px": sleep,
        "sleeping_px_with_head": sleep_head,
        "core_share": (core_px / sleep) if sleep else None,
        "core_share_with_head": (core_px / sleep_head) if sleep_head else None,
        "core_bbox": bbox,
        "sliver_px": SLIVER_PX,
        "split": split,
        "split_unavailable": split_why,
    }


# --------------------------------------------------------------------------- verdict

def check(m):
    """[violation str]. PURE — takes the dict `measure` returns.

    Raises CouldNotRun when the rung could not point at the mattress at all."""
    if not m["core_objects"]:
        raise CouldNotRun(
            f"no object in the {m['roster']}-object mask roster wears a material "
            f"this table calls the core (materials seen: "
            f"{sorted({x[1] for x in m['unknown'] if x[1]}) or 'none'}). The core "
            f"may be genuinely absent — an acquired whole bed carries its own — "
            f"but a rung that cannot POINT at the mattress must not report that "
            f"the mattress is covered.")
    v = []
    for nm, mat in m["unknown"]:
        if nm in m["touching_core"] and m["px"].get(nm, 0) > SLIVER_PX:
            v.append(
                f"{nm} overlaps the mattress in plan and carries "
                f"{m['px'][nm]:,} visible pixels, but wears {mat!r}, which no "
                f"role in ROLE_BY_MATERIAL claims. It is either bedding or it is "
                f"core and nothing on disk says which — classify it rather than "
                f"letting it be exempt by being new (R9b).")
    return v


def standing(m):
    """[line] — THE DEFECT AS IT STANDS, printed on every run, blocking nothing.

    WHY THIS IS NOT A VIOLATION, and it is a decision rather than a softening.
    Run backwards over all 15 masked frames in this lane's history, a flat cut at
    the delivered value fails every one of them: the bare flank has been in every
    frame this studio has ever made. A rung that is red on every render is a rung
    somebody switches off — CLAUDE.md's R13 says exactly that about machines that
    hard-fail every historical instance on day one — and it would halt the very
    rounds whose job is to fix it, which is the enforcement clause R3 revoked.

    So the ABSOLUTE number is a reporting line into the render path, which is the
    channel the owner actually reads, and what BLOCKS is the number RISING
    (`ratchet`) or the rung going BLIND (`check`). What this must never do is
    print like a pass, so it speaks on every run where the core is visible at
    all and the caller's summary line is written off its result.
    """
    if m["core_px"] <= SLIVER_PX:
        return []
    share = f"{100 * m['core_share']:.1f}%" if m["core_share"] else "n/a"
    s = m.get("split") or {}
    out = [f"OUR OWN MATTRESS IS VISIBLE: {m['core_px']:,} px ({share} of the "
           f"sleeping surface, sliver floor {SLIVER_PX} px)."]
    if s.get("core_flank") is not None:
        out.append(
            f"  {s['core_flank']:,} px of that is the mattress's VERTICAL SIDE "
            f"FACE, which every plan-space coverage number is blind to by "
            f"construction — a flank has zero plan area, so `coverage` and "
            f"`fall_sides` cannot see it however green they read.")
    out.append(
        "  Delivered work, read blind by three sighted readers over 7 frames "
        "(_private/deliv-001/flank-panel-2026-08-17/readings.json): 16 of 18 "
        "legible readings 'none', 2 'sliver', NONE above sliver. The same three "
        "readers, not told which frame was ours, put ours at 'most' 3 for 3.")
    return out


def report(m):
    lines = []
    lines.append(f"BED PIXELS — {m['frame']} at {m['resolution'][0]}x"
                 f"{m['resolution'][1]}, roles from {m['material_source']}")
    if m.get("core_semantics", "separable") != "separable":
        lines.append(f"  CORE SEMANTICS: {m['core_semantics']} — the staged "
                     f"bed models frame+mattress as one shell (build's "
                     f"declaration); every exposed pixel of the bed BODY "
                     f"counts as core, which is a stricter read than a "
                     f"separable mattress ever gets.")
    rows = sorted(((n, m["px"][n], m["role"].get(n, "?")) for n in m["px"]),
                  key=lambda r: -r[1])
    for nm, n, r in rows:
        if n:
            lines.append(f"  {n:9,d} px  {r:8s}  {nm}")
    b = m["by_role"]
    lines.append(f"  {'-' * 46}")
    lines.append(f"  sleeping surface = core + bedding = {m['sleeping_px']:,} px")
    lines.append(f"    core (our mattress)  {b[CORE]:9,d} px  "
                 + (f"{100 * m['core_share']:5.1f}%" if m["core_share"] else "    -"))
    lines.append(f"    bedding (all cloth)  {b[BEDDING]:9,d} px")
    lines.append(f"    head (pillows)       {b[HEAD]:9,d} px  "
                 f"(excluded from the surface: a pillow is not coverage)")
    lines.append(f"    frame (base/welts)   {b[FRAME]:9,d} px  (not sleeping surface)")
    lines.append(f"    other (not the bed)  {b[OTHER]:9,d} px  "
                 f"(in the mask roster, carrying no bed role)")
    if m["core_share_with_head"] is not None:
        lines.append(f"    core share counting head cloth: "
                     f"{100 * m['core_share_with_head']:.1f}%")
    if m["core_bbox"]:
        x0, y0, x1, y1 = m["core_bbox"]
        lines.append(f"    core pixels span x {x0}-{x1}, y {y0}-{y1} "
                     f"({x1 - x0 + 1} x {y1 - y0 + 1} px of frame)")
    s = m.get("split")
    if s:
        lines.append(f"  {'-' * 46}")
        lines.append(f"  SPLIT by the projected mattress-top face:")
        lines.append(f"    core on the TOP plane  {s['core_top']:9,d} px  of a "
                     f"{s['top_plane_px']:,} px top plane")
        lines.append(f"    core on the FLANK      {s['core_flank']:9,d} px  "
                     f"(the mattress's vertical side face, bare)")
        lines.append(f"    what covers the top plane, by material:")
        for mat, n in list(s["top_by_material"].items())[:6]:
            lines.append(f"      {n:9,d} px  {100 * n / s['top_plane_px']:5.1f}%"
                         f"  {mat}")
    elif m.get("split_unavailable"):
        lines.append(f"  SPLIT NOT AVAILABLE — {m['split_unavailable']}")
    if m["unknown"]:
        lines.append(f"  {len(m['unknown'])} object(s) carry no role: "
                     + ", ".join(f"{n} ({mat})" for n, mat in m["unknown"][:6]))
    return "\n".join(lines)


def overlay(beauty_path, mask_path, sidecar, role, out_png):
    """Write a false-colour PNG of what the bed is made of — red core, green
    bedding, blue head, grey frame. R11's own point: a rung that only prints a
    number leaves the reader nothing to look at, and this defect was invisible
    for 47 rounds precisely because everyone was reading numbers."""
    import numpy as np
    from PIL import Image

    tint = {CORE: (255, 40, 40), BEDDING: (60, 230, 90), HEAD: (255, 220, 60),
            FRAME: (170, 170, 170), OTHER: (110, 110, 130)}
    b = np.asarray(Image.open(beauty_path).convert("RGB")).astype(float)
    m = np.asarray(Image.open(mask_path).convert("RGB")).astype(np.int16)
    ids = _vp.decode_ids(m)
    names = {int(k): v for k, v in (sidecar.get("ids") or {}).items()}
    out = b * 0.30 + 40.0
    for i, nm in names.items():
        col = tint.get(role.get(nm))
        if col is None:
            continue
        sel = ids == i
        out[sel] = b[sel] * 0.45 + np.array(col, float) * 0.55
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(out_png)
    return out_png


# --------------------------------------------------------------------------- ratchet

BASELINE_REL = os.path.join("qa", "bed-pixels-baseline.json")
RATCHET_REL_TOL = 0.02          # 2% of the recorded number...
RATCHET_ABS_TOL = 200           # ...or one sliver, whichever is larger


def load_baseline(path=None, repo_root=None):
    """(baseline|None, path). An UNREADABLE baseline raises CouldNotRun.

    It used to let `json.JSONDecodeError` escape, and the caller turned that into
    an uncaught traceback and exit 1 — which is this module's code for "the bed
    got worse". A corrupt file would have printed as a regression. That is the
    same shape found in `orders_check` the same hour and recorded in
    `score_exit_policy`: a crashed rung must never read like a completed one.
    """
    p = path or os.path.join(repo_root or os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), BASELINE_REL)
    if not os.path.isfile(p):
        return None, p
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f), p
    except (OSError, ValueError) as e:
        raise CouldNotRun(f"the baseline at {p} is unreadable ({e}). A ratchet "
                          f"whose baseline cannot be read has not held; it has "
                          f"not run.")


def _same_camera(a, b):
    """Two camera fingerprints, compared as the SAME VIEW. A pixel count is only
    comparable against another count taken from the same place."""
    if not a or not b:
        return False
    return (a.get("res") == b.get("res") and a.get("lens") == b.get("lens")
            and a.get("shift") == b.get("shift")
            and a.get("matrix") == b.get("matrix"))


def ratchet(m, baseline, sidecar_source=None):
    """([violation], [note]) — has the bed got WORSE than the recorded round?

    WHY A RATCHET AND NOT A FLAT CUT, which is what this rung started as. Run
    backwards over every masked frame in the lane's history, a flat cut at the
    delivered value fails 15 of 15 — it separates nothing, because the defect has
    been in every frame we have ever made. A rung that is red on every run is a
    rung somebody turns off, and CLAUDE.md says so in R13's own words: *"a machine
    that hard-fails every historical instance on day one gets switched off and
    joins them"*.

    What the same sweep DOES show is a regression nothing caught: bare mattress
    on the flank went 11,694 px at p2r31e to 295,661 at p2r44 and 254,849 at
    p2r47 — a 23x rise, across the rounds that replaced hand-built cloth with a
    bought set, while `coverage` read 94.0% and `fall_sides` read 4/4 throughout.
    So the ABSOLUTE number prints on every run (it is the target, and it is the
    owner's channel), and what BLOCKS is the number rising. That is the same
    split `existence_check` uses for its unrowed backlog and `baseline_ratchet`
    uses for absent masses, and it is the half a flat cut could not have caught.

    A DIFFERENT CAMERA IS NOT A COMPARISON. Pixel counts are a property of the
    view, so a baseline taken from another camera is refused by name rather than
    silently compared — the same provenance rule `value_probe` earned when a mask
    from another view passed a shape check and mis-attributed every pixel.
    """
    if not baseline:
        return [], ["  ratchet DID NOT RUN — no baseline on file. This run's "
                    "numbers are the candidate baseline."], False
    if not _same_camera(baseline.get("camera"), sidecar_source):
        return [], [f"  ratchet DID NOT RUN — the baseline was taken from a "
                    f"different camera ({baseline.get('frame')}), so its pixel "
                    f"counts are not comparable to this frame's. Re-baseline "
                    f"deliberately."], False
    # p2r54 — SAME CAMERA IS NOT ENOUGH: the core's MEANING is part of the
    # measurement. A separable-mattress count (the slab alone; the base wears
    # its own role and is never counted) and a fused-body count (frame+mattress
    # one shell — every exposed pixel of the bed's body) answer different
    # questions, and comparing them printed a +2,492 px "regression" that was
    # actually the accounting change. Same law as the camera guard one line up.
    _bsem = baseline.get("core_semantics", "separable")
    _msem = m.get("core_semantics", "separable")
    if _bsem != _msem:
        return [], [f"  ratchet DID NOT RUN — the baseline's core is "
                    f"{_bsem!r} and this frame's is {_msem!r}: different bed "
                    f"constructions count different pixels as core, so the "
                    f"numbers are not comparable. Re-baseline deliberately "
                    f"with a decision row saying so."], False
    v, notes = [], []
    for key, label in (("core_px", "visible mattress"),
                       ("core_flank", "bare mattress FLANK")):
        was = baseline.get(key)
        now = m["core_px"] if key == "core_px" else (m.get("split") or {}).get(key)
        if was is None or now is None:
            continue
        allow = max(was * (1 + RATCHET_REL_TOL), was + RATCHET_ABS_TOL)
        if now > allow:
            v.append(
                f"RATCHET: {label} rose from {was:,} px at "
                f"{baseline.get('frame', '?')} to {now:,} px "
                f"({now - was:+,} px). The bed got worse and no plan-space "
                f"coverage number can see it.")
        else:
            notes.append(f"  ratchet {label}: {now:,} px against a baseline of "
                         f"{was:,} — {'held' if now <= was else 'inside tolerance'}")
    return v, notes, True


# --------------------------------------------------------------------------- control

def selftest():
    """THE POSITIVE CONTROL. R11's own record: r38 quoted "no step at u=989" as
    proof until a same-class corner that certainly exists scored the same 3.5 L.
    An absence rung that cannot demonstrate it sees a PRESENT core is not
    evidence, so this proves both directions and the fail-closed path."""
    names = {1: "bed__mattress", 2: "bed__cloth__acq1", 3: "bed__base",
             4: "bench__acq0"}
    mats = {"bed__mattress": ["bed_mattress"], "bed__cloth__acq1": ["bed_duvet"],
            "bed__base": ["bed_base"], "bench__acq0": ["Ottoman_01"]}
    role, unknown = roles_of(names, mats)
    assert role == {"bed__mattress": CORE, "bed__cloth__acq1": BEDDING,
                    "bed__base": FRAME}, role
    assert unknown == [("bench__acq0", "Ottoman_01")], unknown

    exposed = {"core_objects": ["bed__mattress"], "roster": 3, "unknown": [],
               "touching_core": [], "px": {}, "core_px": 5000,
               "core_share": 0.469, "sliver_px": SLIVER_PX,
               "split": {"core_flank": 4000}}
    assert check(exposed) == [], "the standing defect is printed, never a violation"
    assert standing(exposed) and "MATTRESS IS VISIBLE" in standing(exposed)[0]

    covered = dict(exposed, core_px=0, core_share=0.0)
    assert standing(covered) == [], standing(covered)

    rim = dict(exposed, core_px=SLIVER_PX, core_share=0.0003)
    assert standing(rim) == [], "an anti-aliased rim must not read as a bare bed"

    # THE RATCHET, both ways, and the case that matters most: it must not report
    # "held" when it could not compare at all.
    cam = {"res": [2400, 1800, 100], "lens": 24.0, "shift": [0, -0.08],
           "matrix": [[1, 0, 0, 0]]}
    base = dict(cam and {"camera": cam, "frame": "b", "core_px": 5000,
                         "core_flank": 4000})
    v, _n, ran = ratchet(exposed, base, cam)
    assert ran and v == [], v
    worse = dict(exposed, core_px=99_000, split={"core_flank": 90_000})
    v, _n, ran = ratchet(worse, base, cam)
    assert ran and len(v) == 2 and "rose from" in v[0], v
    v, _n, ran = ratchet(worse, base, dict(cam, res=[1200, 900, 100]))
    assert not ran and v == [], "a different camera is not a comparison"

    blind = dict(exposed, core_objects=[])
    try:
        check(blind)
    except CouldNotRun:
        pass
    else:                                               # pragma: no cover
        raise AssertionError("a roster with no core must REFUSE, not pass")

    newthing = dict(exposed, core_px=0, core_share=0.0,
                    unknown=[("bed__topper", "linen_x")],
                    touching_core=["bed__topper"], px={"bed__topper": 9000})
    v = check(newthing)
    assert len(v) == 1 and "bed__topper" in v[0], v

    far = dict(newthing, touching_core=[])
    assert check(far) == [], "an object that cannot touch the core is not this rung's"

    aabbs = {"m": [[0, 0, 0], [2, 2, 1]], "on": [[1, 1, 1], [3, 3, 2]],
             "away": [[9, 9, 0], [10, 10, 1]]}
    hit = plan_overlaps(aabbs, ["m"])
    assert hit == {"m", "on"}, hit
    print("SELFTEST bed_pixels: a visible core SPEAKS but does not block, a "
          "covered core and a sliver rim say nothing, the ratchet HOLDS on equal "
          "numbers and BITES on a rise, a different camera is REFUSED rather "
          "than compared, a roster with no core REFUSES (exit 2), and a new "
          "material over the mattress BLOCKS while the same material across the "
          "room does not. OK")
    return 0


# --------------------------------------------------------------------------- CLI

def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    soft = "--soft" in a
    if soft:
        a.remove("--soft")

    def opt(flag):
        if flag in a:
            i = a.index(flag)
            return a[i + 1], a[:i] + a[i + 2:]
        return None, a

    scene, a = opt("--scene")
    ov, a = opt("--overlay")
    js, a = opt("--json")
    baseline, a = opt("--baseline")
    fused, a = opt("--fused-body")
    if len(a) < 3:
        print("usage: bed_pixels.py <beauty.png> <idmask.png> <idmask.json> "
              "[--scene <scene.json>] [--overlay <png>] [--json <path>] [--soft]")
        return 2
    beauty, mask, sidecar_path = a[0], a[1], a[2]
    for p in (beauty, mask, sidecar_path):
        if not os.path.isfile(p):
            print(f"BED PIXELS: COULD NOT RUN — {p!r} is not a file")
            return 2
    try:
        m = measure(beauty, mask, sidecar_path, scene, fused_body=fused)
        # THE DECLARATION OUTLIVES THE COMMAND LINE. Written only now,
        # after `measure` has found the named object in this frame's own
        # mask roster — a name the frame does not corroborate is refused
        # above and never reaches the record.
        if fused:
            print(f"  fused-body declaration -> "
                  f"{record_fused_body(sidecar_path, fused)} "
                  f"({os.path.basename(sidecar_path)})")
        v = check(m)
    except CouldNotRun as e:
        print(f"BED PIXELS: COULD NOT RUN — {e}")
        return 0 if soft else 2
    except (OSError, ValueError) as e:
        print(f"BED PIXELS: COULD NOT RUN — {type(e).__name__}: {e}")
        return 0 if soft else 2

    print(report(m))
    if ov:
        try:
            print(f"  overlay -> {overlay(beauty, mask, load_sidecar(sidecar_path), m['role'], ov)}")
        except Exception as e:                          # noqa: BLE001
            print(f"  overlay FAILED ({type(e).__name__}: {e}) — the numbers above "
                  f"stand; only the picture of them is missing")
    if js:
        with open(js, "w", encoding="utf-8") as f:
            json.dump({k: val for k, val in m.items() if k != "role"}, f, indent=1)
        print(f"  json -> {js}")
    # THE STANDING DEFECT AND THE RATCHET, in that order. The standing lines
    # print on every run; the ratchet is what can fail the build.
    st = standing(m)
    try:
        base, base_path = load_baseline(baseline)
    except CouldNotRun as e:
        print(f"BED PIXELS: COULD NOT RUN — {e}")
        return 0 if soft else 2
    src = (load_sidecar(sidecar_path).get("source") or {})
    rv, rnotes, rran = ratchet(m, base,
                               {"res": src.get("res"), "lens": src.get("lens"),
                                "shift": src.get("shift"),
                                "matrix": src.get("matrix")})
    if st:
        print("")
        for s in st:
            print(f"~~ {s}")
    for n in rnotes:
        print(n)
    v += rv
    if v:
        print(f"\nBED PIXELS: {len(v)} violation(s)")
        for s in v:
            print(f"  !! {s}")
    elif st:
        # NEVER "the core is covered" while it is not, and never "held" when the
        # ratchet did not run. A summary line that contradicts the block above it
        # is how a reader learns to skip the block — and "could not compare"
        # reading like "compared and it was fine" is this rung's whole subject.
        print(f"\nBED PIXELS: the mattress is showing and the ratchet "
              + ("HELD — nothing got worse, nothing is fixed."
                 if rran else
                 "DID NOT RUN, so nothing was compared — that is not a pass.")
              + f" Baseline: {base_path if base else 'NONE ON FILE'}")
    else:
        print(f"\nBED PIXELS: the core is covered ({m['core_px']} px visible, "
              f"floor {SLIVER_PX})")
    return 0 if soft else (1 if v else 0)


if __name__ == "__main__":
    sys.exit(main())
