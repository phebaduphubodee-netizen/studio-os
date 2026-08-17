"""bedcloth_rules.py — the DECISIONS a bed cover has to pass, as pure functions.

PURE, NO `bpy` (pipeline/CLAUDE.md layer law: rules + spec + clearance are plain
Python, only the middle layer is Blender). `bedcloth_fit` holds the Blender glue —
imports, rays, placement — and calls this for every judgement it makes, so the rules
can be tested without a scene and cannot quietly differ between the build and the
audition tools.

The two rules here have each already decided a purchase wrongly:

  PART CLASSIFICATION — one question ("does this part cover a third of the
  mattress?") was doing two jobs until p2r32, so the FIELD test was also deleting
  every accessory cloth, including one set's 374 x 1600 mm turned-down runner. The
  build was corrected; the audition tools kept the old copy until p2r41 and judged
  nine rounds of candidates with their runners removed.

  PLAN SCALE — a CEILING was used as a TARGET, twice. See `plan_scale`.
"""

# A part covering this fraction of the mattress plan IS the field: the cloth that has
# to cover the bed. Between EXTRA_FRAC and FIELD_FRAC it is something LYING ON the
# field (a runner, a folded top sheet) — kept, never counted as the cover.
FIELD_FRAC = 0.33
EXTRA_FRAC = 0.05
# The uploader's junk (a 2 m block, a 12-poly mattress slab) is always coarse, so the
# poly floor does the junk job on its own and the plan fractions do not have to.
POLY_FLOOR = 100
# A part earns its place by being the TOPMOST surface somewhere; below this share of
# its own footprint it is buried (the file's own mattress, a liner under the covers)
# and is dropped without ever reading a mesh NAME.
BURIED_SHARE = 0.15
# A duvet stands this much above its own fall — the loft, not a target.
LOFT_M = 0.32
# The two cuts an audition applies, as ONE definition. `bedcloth_bench` and
# `build_room` each carried their own copy of these numbers; the build's copy was
# also MISSING the drape clause entirely (see `built_survives`).
COVER_CUT = 0.80
FALL_CUT = 2


def limits_for(rect, top_z, base_z, loft=LOFT_M):
    """(limit_w, limit_d, limit_h), (cover_w, cover_d) — the CEILING a cover may not
    exceed and the FLOOR it must cover, both DERIVED from the bed (R9: never typed,
    and re-drawing the bed re-aims the rule).

    The plan ceiling is the mattress plus the cover's own drop on each side, because
    cloth that hangs cannot reach further out in plan than it hangs down. The height
    ceiling is that drop plus the loft."""
    fall = max(0.0, top_z - base_z)
    rw, rd = rect[2], rect[3]
    return (rw + 2.0 * fall, rd + 2.0 * fall, fall + loft), (rw, rd)


def classify_areas(items, mat_area, field_frac=FIELD_FRAC, extra_frac=EXTRA_FRAC,
                   poly_floor=POLY_FLOOR):
    """items: [(key, plan_area, poly_count)] -> (field, extra, drop) keys."""
    field, extra, drop = [], [], []
    for key, area, polys in items:
        if polys < poly_floor or area is None:
            drop.append(key)
        elif area >= mat_area * field_frac:
            field.append(key)
        elif area >= mat_area * extra_frac:
            extra.append(key)
        else:
            drop.append(key)
    return field, extra, drop


def plan_scale(size, limit, cover=None, max_scale=1.0):
    """Scale a cover of native size (w, d, h) for this bed.

    THE LIMIT IS A CEILING, NEVER A TARGET, and the difference is the whole reason
    the acquired leg kept rendering a flat white lump. Until p2r41 the slot was
    `min(bed outer line, mattress + 40 mm)` and the scale was `min(slot/native)` — a
    TARGET. On the master-suite bed that slot measures **1800 x 1949 mm while the
    mattress it must cover measures 1820 x 1969**, so the rule shrank every candidate
    SMALLER than the thing it was bought to cover. A duvet authored at 2200 mm for an
    1820 mm mattress — i.e. one carrying 190 mm of drape down each flank, which is
    what makes cloth read as cloth — was scaled to 0.82 until its hem sat inside the
    mattress edge. That is why p2r31 measured high coverage, 0-2 flanks and an
    eye-verdict of "flatter than the solver's duvet", and why the one metric it
    ranked on (coverage) preferred the smallest candidate: a cloth that cannot reach
    past the mattress covers its plan most efficiently.

    So the TARGET is the asset AS AUTHORED (scale 1.0 — it was modelled for a bed),
    and everything else is a ceiling: `max_scale` (a mesh is never stretched to fit),
    the plan ceiling and the height ceiling from `limits_for`. `cover` is the one
    FLOOR — the plan the set must actually cover, which is the spec's
    `model_requirements.covers` rule applied by the same code that scales.

    Returns (scale, rot_deg, fit_w, fit_d, plan_scale, need_scale); `need_scale` is
    None when no cover is declared, and a caller REJECTS when it exceeds `scale`.
    Rotation is DERIVED FROM BOTH BOXES — turn only when the set's long axis and the
    target's long axis disagree — never from a head string."""
    mw_, md_, mh_ = size
    lim_w, lim_d, lim_h = limit
    ref_w, ref_d = cover if cover else (lim_w, lim_d)
    rot = 90.0 if ((mw_ > md_) != (ref_w > ref_d)) else 0.0
    fit_w, fit_d = (lim_d, lim_w) if rot else (lim_w, lim_d)
    plan_s = min(fit_w / max(mw_, 1e-6), fit_d / max(md_, 1e-6))
    s = min(max_scale, plan_s, lim_h / max(mh_, 1e-6))
    need = None
    if cover:
        cw, cd = (ref_d, ref_w) if rot else (ref_w, ref_d)
        need = max(cw / max(mw_, 1e-6), cd / max(md_, 1e-6))
    return s, rot, fit_w, fit_d, plan_s, need


DUPLICATE_SHARE = 0.30


def lies_on_the_bed(part_top_z, mattress_top_z, loft=LOFT_M):
    """Is this EXTRA part cloth lying on the bed, or furniture the set brought along?

    `classify_areas` already says in words what EXTRA means — "something LYING ON the
    field (a runner, a folded top sheet)" — and nothing tested it, so the class took
    whatever the uploader shipped between 5% and 33% of the mattress plan. On
    d4698c95 that is a 735 x 359 x 545 mm bolster, and p2r47's audition rendered it
    standing upright on the near corner of the bed with our own acquired shams already
    at the head.

    THE BOUND IS `LOFT_M`, WHICH IS ALREADY DECLARED — "a duvet stands this much
    above its own fall" — so no number is invented here. It is the most a cloth ON
    this bed can rise. Measured on the set this rule was written from: the sheet tops
    out 7.5 mm above the mattress, the duvet 146.4, the folded runner 94.1, and the
    bolster 554.7. The nearest legitimate part has a factor of two of headroom.

    FIELD parts are deliberately NOT subject to this: the field IS the cover, and
    whether it is right is what `coverage` and `fall_sides` are for.
    """
    if part_top_z is None or mattress_top_z is None:
        return True, None
    rise = part_top_z - mattress_top_z
    return bool(rise <= loft + 1e-9), rise


def duplicate_of_placed(part_bb, placed_bbs, share=DUPLICATE_SHARE):
    """Is this set part occupying a volume the frame has ALREADY dressed?

    `part_bb` and each of `placed_bbs` are (x0, y0, z0, x1, y1, z1). Returns the
    largest fraction of the PART's own volume that sits inside one placed object, and
    whether that clears `share`.

    WHY IT IS NOT A NAME TEST. `_place_bed_cloth` has said since p2r44 what it is
    buying — "the duvet + its turned-down top sheet, as one dressed set. NOT the
    pillows (already acquired, D-025)" — and nothing enforced it, so a bedding set
    that ships with its own pillows puts a second pair on top of ours. p2r47 rendered
    exactly that: an 800 mm bolster standing upright through the acquired head set.
    A name test would need the uploader's names, which this repo has already been
    burned by trusting (a material called Charcoal that renders fluorescent green).
    Volume overlap with an object ALREADY in the frame is the geometric form of the
    same question, and membership of "already in the frame" comes from the value
    ladder's signed ACQUIRED_AS register, not from a list kept here (R9b).

    R9b calls AABB interpenetration ADVISORY because a box cannot tell interlocking
    from intersecting — which is why the threshold is a THIRD of the part's volume
    and not a touch. A duvet resting against a sham overlaps it slightly; a second
    pillow standing where ours stands does not.
    """
    if not part_bb or not placed_bbs:
        return 0.0, False
    vol = max(1e-12, (part_bb[3] - part_bb[0]) * (part_bb[4] - part_bb[1])
              * (part_bb[5] - part_bb[2]))
    best = 0.0
    for b in placed_bbs:
        if not b:
            continue
        ov = 1.0
        for k in range(3):
            lo = max(part_bb[k], b[k])
            hi = min(part_bb[k + 3], b[k + 3])
            ov *= max(0.0, hi - lo)
        best = max(best, ov / vol)
    return best, best >= share


def choose_cover(parts, limit, cover=None, max_scale=1.0):
    """WHICH PART OF THIS FILE IS THE COVER, and what scale does the set take from it.

    `parts` is [(key, (w, d, h))] in metres for every FIELD-classified part. Returns
    (key, plan_scale_row, feasible_count) where the row is `plan_scale`'s tuple for
    the chosen part, or (None, None, 0) when there is nothing to choose from.

    IT IS SOLVED ON A PART, NOT ON THE FILE, and the difference refused six sets.
    `limits_for` says what its height ceiling describes — the cover's own fall plus
    its loft — and it was being applied to the bounding box of everything kept. Any
    bedding set that ships with the bed it dresses is therefore judged by the BED's
    height: 22897dd4 holds a 2018 x 1827 x 213 mm sheet of 74,136 triangles inside a
    file standing 1243 mm tall, so the ceiling collapsed to 0.576x and the sheet's
    own 0.665x read as "too big to fit". R9b's law with the sign flipped — a rule
    applied to a group it does not describe will refuse the next one.

    THE PICK: among parts that can cover within the ceiling, the largest plan wins —
    that is the outermost cloth, the sheet the camera sees, and the accessories ride
    with it at the same scale (the author's internal proportions are not ours to
    edit). When none can, the pick is the part that comes CLOSEST to covering, so the
    set is still staged and still measured by ray rather than refused by a box.
    """
    rows = []
    for key, native in parts:
        row = plan_scale(native, limit, cover, max_scale)
        need = row[5]
        rows.append({"key": key, "native": native, "row": row, "need": need,
                     "plan": native[0] * native[1],
                     "ok": need is None or need <= row[0] + 1e-9})
    if not rows:
        return None, None, 0
    feasible = [r for r in rows if r["ok"]]
    pick = (max(feasible, key=lambda r: r["plan"]) if feasible
            else min(rows, key=lambda r: r["need"] if r["need"] is not None else 0.0))
    return pick["key"], pick["row"], len(feasible)


def fineness(cover_edge_mm, control_edges_mm):
    """Is this mesh fine enough to BE cloth — judged against the cloth already
    accepted beside it in the same frame?

    THE GAP THIS CLOSES, measured on p2r44. Two independent critics read the bed as
    "a carved solid, every fold two flat facets meeting at a knife edge". Every
    existing rung passed it, because all three of them ask whether the set FITS
    (`need_scale`, `coverage`, `fall_sides`) and none of them can see what the mesh
    is MADE OF. The set that shipped has a median edge of 43.2 mm in world; a mesh
    that coarse cannot carry a bending radius, so its folds can only be creases.

    AND THE CUT IS NOT INVENTED, which is the trap `survives` names for relief_mm
    ("inventing one would be taste wearing a threshold"). The frame carries its own
    control: the acquired PILLOWS in the same bed, from the same acquire pipeline,
    at the same distance from the same camera, measure 4.5 mm and 10.3 mm — and no
    critic has ever filed them. So the rule is a COMPARISON, not a constant: a
    bought cover may not be coarser than the coarsest bought cloth already accepted
    in the frame. It re-aims itself when the frame changes and there is no number in
    it for anyone to tune.

    `control_edges_mm` is {object name: median world edge mm} for the acquired
    soft-goods already in the scene — membership comes from `value_ladder.ACQUIRED_AS`,
    the signed register of which rungs are bought cloth, so this rule never grows an
    allowlist of its own (R9b: a rule that names the objects it applies to will
    always exempt the next one).

    Returns `ran: False` when there is nothing to control against. That is the THIRD
    STATE and it is never a pass — "could not look" must not print like "looked and
    it was fine" (R11's exit-code contract). The caller decides what to do with it.
    """
    ctrl = {k: float(v) for k, v in (control_edges_mm or {}).items()
            if v is not None and float(v) > 0.0}
    if cover_edge_mm is None or cover_edge_mm <= 0:
        return {"ran": False, "fine_enough": None, "cover_mm": cover_edge_mm,
                "why": "no edge length was measured on the cover"}
    if not ctrl:
        return {"ran": False, "fine_enough": None, "cover_mm": cover_edge_mm,
                "why": "no acquired soft-goods mesh in this frame to control "
                       "against — the cut is a comparison and has nothing to "
                       "compare with"}
    name = max(ctrl, key=lambda k: ctrl[k])
    limit = ctrl[name]
    return {"ran": True, "fine_enough": bool(cover_edge_mm <= limit + 1e-9),
            "cover_mm": float(cover_edge_mm), "control": name,
            "control_mm": limit, "ratio": float(cover_edge_mm) / limit}


def built_survives(coverage, fall_sides, cover_edge_mm=None, control_edges_mm=None,
                   cover_cut=COVER_CUT, fall_cut=FALL_CUT):
    """The same cuts, re-applied to numbers measured on the BUILT SCENE.

    WHY A SECOND APPLICATION IS NOT A DUPLICATE, and it is the third instance of the
    shape this file was written to end. The audition stages a candidate and measures
    it; the build then stages the same file, renames the parts, re-dresses their
    materials and runs the shading normaliser over them — and NOTHING measured the
    result. On p2r44 that mattered by exactly the width of the cut: the audition
    recorded `fall_sides 2/4` and the built scene measures **1/4** against a cut of
    2. The frame shipped a cover that drapes one flank, so the other three flanks
    render as our own 218-polygon mattress box — 332,879 px of it against the
    cover's 212,263.

    AND THE BUILD WAS ONLY EVER APPLYING TWO OF THE THREE CUTS. `_place_bed_cloth`
    tested `model_fit` and `coverage < 0.80` inline and printed `fall_sides` beside
    them without ever comparing it to anything — the drape clause existed in
    `survives`, which the build does not call. A rule spread across its callers is a
    rule with one exemption per caller (R9b, one level up), and this was that
    exemption.

    `need_scale` is not re-asked here: the scale was applied at staging, so at build
    time the question is answered by the geometry itself.
    """
    row = survives(None, 1.0, coverage, fall_sides, cover_cut, fall_cut)
    fine = fineness(cover_edge_mm, control_edges_mm)
    row["fineness"] = fine
    row["fine_enough"] = fine["fine_enough"]
    # A cut that could not run is NOT a pass. `survives` is the three fit clauses;
    # `blocks` is what a caller acts on, and it names could-not-run separately.
    row["survives"] = bool(row["covered"] and row["drapes"]
                           and fine["fine_enough"] is True)
    row["blocked_by"] = [k for k, ok in (("cover", row["covered"]),
                                         ("drape", row["drapes"]),
                                         ("fineness", fine["fine_enough"]))
                         if ok is not True]
    return row


def survives(need_scale, scale, coverage, fall_sides,
             cover_cut=COVER_CUT, fall_cut=FALL_CUT):
    """The three HARD filters an audition applies before an eye is spent on a
    candidate, and the rank that replaces ranking on coverage alone.

    p2r31 ranked on coverage. Coverage is MAXIMISED by a cloth that lies flat on the
    mattress without reaching past it, so the ranking actively preferred the failure;
    the number that answered the real question was printed in the same table and read
    past (falls past 2 of 4 sides).

      size    REPORTED, NOT A CUT since p2r47 — see below
      cover   coverage >= 0.80, the build's own cut (our mattress must not show)
      drape   fall_sides >= 2; on a bed against a headboard the reachable maximum
              is 3 (two flanks and the foot)

    SIZE WAS DEMOTED FROM A CUT TO A NUMBER, and the reason is that it asked the
    same question as the other two with a worse instrument. `need_scale` compares
    BOUNDING BOXES, and this whole bench exists because a bounding box was the wrong
    tool — its own opening line: "a bounding box cannot tell a spread sheet from a
    crumpled one... This measures the thing itself, by ray." As a cut it demanded a
    box spanning 100% of the mattress while `cover` — the ray version of the same
    question — is satisfied at 80%. On 2026-08-17 it refused five candidates at
    1.011x, 1.046x, 1.066x, 1.087x and 1.125x, and not one of them was ever rayed;
    the nearest missed by 20 mm on one axis of a bed the client's own drawing makes
    2149 mm wide. Nothing was loosened to arrange that: a cover too small still fails
    `cover` or `drape`, which measure the consequence instead of predicting it, and
    `max_scale` still binds the staging scale so no mesh is stretched to fit. What is
    given up is a cheap early-out; what is bought is that the eye and the rays get to
    see candidates a box refused sight unseen.

    relief_mm is deliberately NOT a filter: both of its failure directions are real
    (a crumple contradicts the signed DD, a painted plane is what both critics keep
    filing) and nothing in this repo can currently ground a band between them.
    Inventing one would be taste wearing a threshold. The eye decides style; the
    machine only stops the eye wasting time on sets that cannot fit, cover or drape.
    """
    size_ok = need_scale is None or need_scale <= scale + 1e-9
    covered = coverage >= cover_cut
    drapes = fall_sides >= fall_cut
    return {"size_ok": size_ok, "covered": covered, "drapes": drapes,
            "survives": bool(covered and drapes)}
