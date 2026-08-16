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


def survives(need_scale, scale, coverage, fall_sides,
             cover_cut=0.80, fall_cut=2):
    """The three HARD filters an audition applies before an eye is spent on a
    candidate, and the rank that replaces ranking on coverage alone.

    p2r31 ranked on coverage. Coverage is MAXIMISED by a cloth that lies flat on the
    mattress without reaching past it, so the ranking actively preferred the failure;
    the number that answered the real question was printed in the same table and read
    past (falls past 2 of 4 sides).

      size    the set covers the mattress within the ceiling — never stretched
      cover   coverage >= 0.80, the build's own cut (our mattress must not show)
      drape   fall_sides >= 2; on a bed against a headboard the reachable maximum
              is 3 (two flanks and the foot)

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
            "survives": bool(size_ok and covered and drapes)}
