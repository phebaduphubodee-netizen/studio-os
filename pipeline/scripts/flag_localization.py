"""
flag_localization.py -- benchmark F7: does the tier-1 self-doubt suite's flag LAND ON THE
ACTUALLY-WRONG ITEM? -- measured with a MUTATION-MINTED ANSWER KEY (no external corpus, no owner).

    python flag_localization.py <project_dir> [--priors auto|none|PATH]   (default: auto)

WHY (the north star: make the machine "doubt itself at the RIGHT points", not merely "flag
more"). self_audit.py aggregates every scattered doubt into ONE ranked list; its docstring names
benchmark_reader.py as the sibling instrument, the two being "the same instrument split by
have-ground-truth? (no here, yes there)". benchmark_reader is the HAVE-GT half: it scores
flag-recall/precision against a real annotated corpus (Structured3D / FloorPlanCAD). F7 is the
NO-real-GT half done HONESTLY: we do not have an owner-labelled truth for a LIVE project, so we
MINT one -- take a KNOWN-GOOD read, inject exactly ONE deliberate error into ONE item, and ask
the suite "which item is wrong?". Because we planted the error we know the answer, so we can
measure LOCALIZATION recall (did a NEW flag land on the item we broke?) and LOCALIZATION
precision (of the new flags a single-item break raised, how many were ABOUT that item vs noise
splashed onto innocent neighbours?) with zero ground truth and zero owner.

This is the specificity instrument the first live self_audit run demanded: that run surfaced a
real unsigned facing-flip CRITICAL, but a doubt list is only trustworthy if a flag actually
FINGERS the broken piece rather than lighting up the whole room. F7 is how we regress that.

DESIGN LAWS (STUDIO-OS; mirrors the suite it measures):
  * OWNER-FREE / PURE core. run_localization + the mutation generators are pure functions over
    already-loaded spec dicts + the owner confirmed[] ledger. No disk, no prompting, no now()/
    random. The CLI/disk is a thin shell. Deterministic: every eligible item is mutated (never
    sampled) in a sorted, stable order; two runs give a byte-identical report.
  * DELTA METHODOLOGY (robust to LATENT base doubt). A live read is NOT clean -- it already
    carries open doubt. So we never ask "does the suite flag the mutated spec?" (it would flag the
    pre-existing junk too). We ask "what flag is NEW versus the UNMUTATED base?". base_flags are
    computed ONCE per spec; a mutation's new_flags are exactly those whose identity key was absent
    from the base. A localization HIT = a NEW flag whose subjects[] contain the mutated item's
    name. This isolates the injected error from the room's ambient doubt.
  * READ THE DOMAIN MODULES DIRECTLY. self_audit's collect_* wrappers fold subjects[] into a text
    suffix of `detail` (see self_audit._wrap_domain); the DOMAIN records keep a structured
    subjects[] list -- the clean localization key. So F7 calls cross_signal.check_room /
    anomaly_flags.check_room / confidence.assess_room / rebuild_diff.diff_rounds DIRECTLY (imported
    read-only) and matches the mutated item's NAME against subjects[]. Names are kept STABLE across
    every mutation (we mutate rot/kind/zone/w/d, never name) so the match is exact.
  * HONEST COVERAGE + HONEST MISSES. A MISS (a planted error the suite did not catch) is the most
    valuable output -- a known blind spot is a real finding, never hidden. We emit the keyentry for
    a should-flag mutation even when NOTHING fires today, so the blind spot is COUNTED and REPORTED.
    Each collector's own coverage (READ/UNWIRED/ABSENT/ERROR) rides beside the numbers, so a low
    recall under UNWIRED coverage reads as "did not look", not "clean". A RUNTIME raise inside a
    collector (during _collect_static/_collect_rebuild) degrades THAT collector to ERROR coverage and
    contributes no flags, never aborting the run. An IMPORT-time failure (a suite module that fails to
    load or drops a referenced attribute) is by design an intentional HARD CRASH at module load, not a
    degrade -- it is loud and impossible to mistake for a clean pass, and F7's own tables never render,
    so the honesty contract (no silent pass) survives without a per-collector import fallback.
  * FALSE-ACCEPTS FIRST. The one NONFLAG class (facing_flip_box) is the over-fire probe: a 180
    flip of a render-symmetric box is INVISIBLE in the output (rebuild_diff folds it away on
    purpose -- the "bench-180 false-CRITICAL" wound). We assert it raises NOTHING; an overfire
    there is a precision leak ranked ahead of any coverage gain.

MUTATION CLASSES (each keyed to a real suite behaviour; see the collector map in the module tests):
  facing_flip_directional  rot -> rot+180 on a directional (sofa/chair/bed) piece. Observable in
                           the render -> rebuild_diff CRITICAL reversal. expect FLAG.
  facing_flip_box          rot -> rot+180 on a NON-directional box/table. Render-symmetric ->
                           rebuild_diff folds it to 0. expect NONFLAG (the over-fire probe).
  kind_change_unsigned     kind -> a different, no-bound kind, no signature. rebuild_diff HIGH.
  kind_change_vs_signature kind changed AWAY from an owner-signed kind (the ledger signs the OLD
                           value). expect FLAG. NB (honesty): within the tier-1 suite this surfaces
                           as rebuild_diff HIGH, NOT the CRITICAL kind_regression band -- that band
                           is emitted by placement_gate -> self_audit.collect_gate, which F7 does
                           not run. The keyentry expects CRITICAL so the report SHOWS the gap.
  size_implausible         w,d -> impossible-for-kind. anomaly_flags HIGH.
  size_off_prior_band      w,d -> FAR outside the claimed kind's corpus quantile band while
                           INSIDE every built-in gross bound, so WITHOUT a kind-priors artifact
                           nothing fires: the class measures exactly the corpus tier's ADDED
                           catching power. anomaly_flags MEDIUM. Eligible only where that window
                           exists (sofa / armchair-via-chair on v4; bed/toilet/bathtub/wardrobe
                           have none -- their built-in bounds already sit at the corpus far-edge)
                           and only when `priors` is supplied; otherwise every item skips and the
                           lane reports unwired (the honest 'did not look').
  rot_stripped_directional rot removed from a directional piece (shipped as assumed-south).
                           confidence:facing say-unsure. expect FLAG.
  zone_below_grade_unsigned zone -> below_grade on an inside-drawn piece, unsigned. cross_signal
                           zone_vs_geometry HIGH.

NOT A CORPUS. F7 is the SYNTHETIC-answer-key lane: the "truth" is minted by mutation, so it
measures the suite's localization/specificity on ONE project's own good reads, not generalisation.
Its sibling benchmark_reader.py is the real-corpus lane (annotated GT, cross-project). Read the two
together: F7 says "the flag fingers the broken item here"; benchmark_reader says "the flags
generalise to items we never saw".
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import placement_gate as PG
import zone_flag as ZF
import cross_signal as CS
import anomaly_flags as AF
import confidence as CF
import rebuild_diff as RD
import self_audit as A

SCHEMA = "interior-ai/flag-localization@0.1"

# Kinds whose RENDER mesh carries a front (a 180 flip is OBSERVABLE) -- mirror rebuild_diff's own
# set so F7's notion of "directional" can never drift from the collector it measures.
DIRECTIONAL_KINDS = frozenset(RD._DIRECTIONAL_KINDS)
# Kinds for which a facing say-unsure is meaningful -- mirror confidence.FACING_KINDS (= PG._FACING_KINDS).
FACING_KINDS = frozenset(CF.FACING_KINDS)
# Kinds anomaly_flags carries a coarse built-in bound for -- only these can trip size_implausible.
BOUNDED_KINDS = frozenset(AF.BUILTIN_BOUNDS)
# Radially-symmetric shapes rebuild_diff never facing-flags -> not eligible for a facing mutation.
_ROUND_SHAPES = frozenset({"round", "circle", "disc", "disk", "oval"})
# No-built-in-bound kinds: an identity mutation targets one of these so the kind change does NOT
# also trip a size_implausible anomaly (keeping kind_change a clean single-collector probe).
_NO_BOUND_TARGETS = ("cabinet", "headboard")

SHOULD_FLAG_CLASSES = ("facing_flip_directional", "kind_change_unsigned",
                       "kind_change_vs_signature", "size_implausible",
                       "size_off_prior_band",
                       "rot_stripped_directional", "zone_below_grade_unsigned")
NONFLAG_CLASSES = ("facing_flip_box",)
ALL_CLASSES = SHOULD_FLAG_CLASSES + NONFLAG_CLASSES


# ---- item location + spec introspection (deterministic order) -------------------------
def _iter_items(spec):
    """Every mutable piece in a room-spec as [(locator, item), ...] in a STABLE, deterministic
    order: builtins, then loose items, then each subroom's fixtures. A locator is an opaque tuple
    that _get() resolves back to the SAME slot in a deepcopy, so a mutation edits exactly the piece
    the keyentry names. Non-dict members are skipped (a hand-assembled spec may carry junk)."""
    out = []
    for i, it in enumerate(spec.get("builtins") or []):
        if isinstance(it, dict):
            out.append((("builtins", i), it))
    for i, it in enumerate(spec.get("items") or []):
        if isinstance(it, dict):
            out.append((("items", i), it))
    for si, sr in enumerate(spec.get("subrooms") or []):
        if not isinstance(sr, dict):
            continue
        for fi, it in enumerate(sr.get("fixtures") or []):
            if isinstance(it, dict):
                out.append((("subrooms", si, "fixtures", fi), it))
    return out


def _get(spec, loc):
    """Resolve a locator (from _iter_items) to the live piece dict inside `spec`."""
    if loc[0] == "builtins":
        return spec["builtins"][loc[1]]
    if loc[0] == "items":
        return spec["items"][loc[1]]
    return spec["subrooms"][loc[1]]["fixtures"][loc[3]]


def _container(spec, loc):
    """(room_label, outline_mm) of the container the located piece lives in -- the MAIN room for a
    builtin/item, the owning subroom for a fixture. Used to scope a confirmed[] entry's room and to
    run the same inside-the-outline containment test cross_signal uses."""
    if loc[0] in ("builtins", "items"):
        room = spec.get("room") or {}
        return room.get("type"), (room.get("outline_mm") or [])
    sr = spec["subrooms"][loc[1]]
    return (sr.get("type") or sr.get("name")), (sr.get("outline_mm") or [])


def _kind(it):
    return PG._norm_kind(it.get("kind"))


def _is_round(it):
    return str(it.get("shape", "")).strip().lower() in _ROUND_SHAPES


def _centroid_inside(it, outline):
    """True iff the piece is indoor-immune against `outline` -- the EXACT 3-part OR cross_signal's
    check_zone_vs_geometry uses (centroid in poly, or within indoor_pad of it, or >= indoor_area_frac
    of the footprint inside). Pure; never raises on a degenerate outline."""
    if not outline or len(outline) < 3:
        return False
    try:
        fp = PG.footprint(it)
    except Exception:
        return False
    c = ((fp[0] + fp[2]) / 2.0, (fp[1] + fp[3]) / 2.0)
    try:
        if ZF.point_in_poly(c, outline):
            return True
        if ZF.dist_point_to_poly(c, outline) <= CS.DEFAULTS["indoor_pad"]:
            return True
        if ZF.rect_area_frac_inside(fp, outline) >= CS.DEFAULTS["indoor_area_frac"]:
            return True
    except Exception:
        return False
    return False


def _diff_target_kind(orig):
    """A different, no-built-in-bound kind for an identity mutation (so the re-kind does not ALSO
    trip a size anomaly). Returns None only if `orig` somehow equals every no-bound target."""
    for cand in _NO_BOUND_TARGETS:
        if cand != orig:
            return cand
    return None


# ---- mutation generators: pure (spec, locator[, confirmed]) -> (mutated_deepcopy, keyentry) ----
# Each returns None when the located item is INELIGIBLE for the class (the caller counts the skip),
# else a deepcopy of the whole spec with EXACTLY ONE field of ONE item changed, plus a keyentry:
#   {item, class, expect: "flag"|"nonflag", collectors: [expected], severity: <expected band|None>}
# A keyentry may carry a private "_extra_confirmed" (a ledger entry the mutation needs live); the
# runner merges it into `confirmed` for that mutation only and strips it before the report.

def _keyentry(name, cls, expect, collectors, severity, extra_confirmed=None, note=None):
    ke = {"item": name, "class": cls, "expect": expect,
          "collectors": list(collectors), "severity": severity}
    if extra_confirmed:
        ke["_extra_confirmed"] = extra_confirmed
    if note:
        ke["note"] = note
    return ke


def mut_facing_flip_directional(spec, loc, confirmed=None):
    it = _get(spec, loc)
    if _kind(it) not in DIRECTIONAL_KINDS or _is_round(it):
        return None
    name = it.get("name")
    if name is None:
        return None
    out = copy.deepcopy(spec)
    nit = _get(out, loc)
    nit["rot"] = ((PG._norm_rot(nit.get("rot")) or 0) + 180) % 360
    return out, _keyentry(name, "facing_flip_directional", "flag", ["rebuild_diff"], "CRITICAL")


def mut_facing_flip_box(spec, loc, confirmed=None):
    k = _kind(it := _get(spec, loc))
    if k is None or k in DIRECTIONAL_KINDS or _is_round(it):
        return None                          # need a real, NON-directional, non-round box/table
    name = it.get("name")
    if name is None:
        return None
    out = copy.deepcopy(spec)
    nit = _get(out, loc)
    nit["rot"] = ((PG._norm_rot(nit.get("rot")) or 0) + 180) % 360
    return out, _keyentry(name, "facing_flip_box", "nonflag", ["rebuild_diff"], None,
                          note="render-symmetric: a 180 flip is byte-identical mesh -> expect NO flag")


def mut_kind_change_unsigned(spec, loc, confirmed=None):
    orig = _kind(it := _get(spec, loc))
    if orig is None:
        return None
    target = _diff_target_kind(orig)
    if target is None:
        return None
    name = it.get("name")
    if name is None:
        return None
    out = copy.deepcopy(spec)
    _get(out, loc)["kind"] = target
    return out, _keyentry(name, "kind_change_unsigned", "flag", ["rebuild_diff"], "HIGH")


def mut_kind_change_vs_signature(spec, loc, confirmed=None):
    orig = _kind(it := _get(spec, loc))
    if orig is None:
        return None
    target = _diff_target_kind(orig)
    if target is None:
        return None
    name = it.get("name")
    if name is None:
        return None
    room, _outline = _container(spec, loc)
    # the owner-signed ledger entry pins the ORIGINAL kind; the mutation then contradicts it.
    entry = {"room": room, "name": name, "kind": orig, "w": it.get("w"), "d": it.get("d"),
             "by": "F7-mutation", "date": "2026-07-08",
             "note": "F7 answer-key: owner signed the original identity"}
    out = copy.deepcopy(spec)
    _get(out, loc)["kind"] = target
    # expect CRITICAL by DESIGN INTENT (a regressed owner signature); the tier-1 suite actually
    # surfaces this at rebuild_diff HIGH -- the CRITICAL kind_regression band lives in placement_gate,
    # outside F7's collectors. The keyentry keeps CRITICAL so the report's severity column SHOWS the gap.
    return out, _keyentry(name, "kind_change_vs_signature", "flag", ["rebuild_diff"], "CRITICAL",
                          extra_confirmed=[entry],
                          note="CRITICAL kind_regression is a placement_gate band; tier-1 catches this as HIGH")


def mut_size_implausible(spec, loc, confirmed=None):
    orig = _kind(it := _get(spec, loc))
    if orig not in BOUNDED_KINDS:
        return None                          # no built-in bound -> nothing to violate
    name = it.get("name")
    if name is None:
        return None
    # a piece whose kind the owner has SIGNED is adjudicated -> anomaly skips it; not eligible.
    try:
        signed = PG.confirmed_kind(it, confirmed or [])
    except Exception:
        signed = None
    if signed is not None and signed == orig:
        return None
    out = copy.deepcopy(spec)
    nit = _get(out, loc)
    nit["w"], nit["d"] = 100, 100            # 100x100mm is below every built-in min (short>=150) -> HIGH
    return out, _keyentry(name, "size_implausible", "flag", ["anomaly"], "HIGH")


def mut_size_off_prior_band(spec, loc, confirmed=None, priors=None):
    """Corpus-band catching power the coarse built-in bounds DON'T have: re-dimension the piece to
    sit FAR outside its claimed kind's corpus quantile band (anomaly's PRIOR_FAR margin, +10%)
    while staying INSIDE every built-in gross bound -- so with priors=None NOTHING fires and the
    class honestly reports unwired instead of pretending coverage. Kind goes through the prior
    lane's own vocabulary (AF.prior_band_kind): exempt kinds and unmapped kinds skip; a kind whose
    built-in bound already sits at/below the corpus far-edge (bed: 3023 > builtin 3000) has NO
    builtin-silent window and skips -- counted, never silently thinned. The short side is kept
    INSIDE the corpus band so exactly ONE axis carries the planted error."""
    if priors is None:
        return None                          # no corpus tier wired -> lane reports unwired
    it = _get(spec, loc)
    orig = _kind(it)
    if orig is None:
        return None
    band_kind = AF.prior_band_kind(orig)
    bands = AF._prior_bands(priors, band_kind) if band_kind else []
    if not bands:
        return None
    name = it.get("name")
    if name is None:
        return None
    try:
        signed = PG.confirmed_kind(it, confirmed or [])
    except Exception:
        signed = None
    if signed is not None and signed == orig:
        return None                          # owner-signed identity -> anomaly suppresses; not eligible
    # MULTI-CORPUS: the anomaly lane fires only FAR outside EVERY carrying doc, so the planted
    # long side must clear EVERY doc's far-edge (max of hi edges) and the in-band short side
    # must sit in the INTERSECTION of the docs' short bands. No intersection -> skip (counted,
    # never a fake catch). One doc reproduces the old arithmetic exactly.
    lo0 = lo1 = hi1 = None
    for band in bands:
        lo_band, hi_band = band.get("lo_mm"), band.get("hi_mm")
        if not (isinstance(lo_band, (list, tuple)) and isinstance(hi_band, (list, tuple))
                and len(lo_band) == 2 and len(hi_band) == 2):
            return None
        try:                                 # hostile band edges (strings/None) must SKIP this
            b_lo0, b_lo1 = float(lo_band[0]), float(lo_band[1])   # item, never crash the run --
            b_hi1 = float(hi_band[1])        # the generator runs OUTSIDE the guarded collectors
        except (TypeError, ValueError):
            return None
        lo0 = b_lo0 if lo0 is None else max(lo0, b_lo0)
        lo1 = b_lo1 if lo1 is None else min(lo1, b_lo1)
        hi1 = b_hi1 if hi1 is None else max(hi1, b_hi1)
    dims = AF._dims(it)
    if dims is None:
        return None
    if all((AF._far_outside(dims[0], b.get("lo_mm")) or AF._far_outside(dims[1], b.get("hi_mm")))
           for b in bands):
        return None                          # already far-out of EVERY doc -> base flag exists; not a NEW catch
    if lo0 > lo1:
        return None                          # docs' short bands do not intersect -> no window
    target_long = hi1 * (1.0 + AF.PRIOR_FAR) * 1.10
    target_short = max(lo0, min(target_long / 2.0, lo1))
    b = AF.BUILTIN_BOUNDS.get(orig)
    if b is not None:
        min_s, max_s, min_l, max_l, max_a = b
        if not (min_s <= dims[0] <= max_s and min_l <= dims[1] <= max_l and dims[2] <= max_a):
            # base piece ALREADY gross-violates its built-in bound -> a base HIGH size record
            # exists whose _flag_key (severity excluded) equals the mutation's MEDIUM record, so
            # the delta filter would score a fake MISS. Skip -- counted, a harness artifact must
            # never masquerade as a suite blind spot.
            return None
        if not (min_l <= target_long <= max_l):
            return None                      # no builtin-silent window for this kind
        target_short = min(max(target_short, min_s), max_s)
        if target_short <= 0 or target_long / target_short > max_a:
            return None
    if not (lo0 <= target_short <= lo1):
        return None                          # short must stay inside the band (single-axis error)
    out = copy.deepcopy(spec)
    nit = _get(out, loc)
    nit["w"], nit["d"] = round(target_short), round(target_long)
    return out, _keyentry(name, "size_off_prior_band", "flag", ["anomaly"], "MEDIUM")


def mut_rot_stripped_directional(spec, loc, confirmed=None):
    it = _get(spec, loc)
    if it.get("kind") not in FACING_KINDS:    # confidence keys facing off the RAW kind (see _eligible_fields)
        return None
    if it.get("rot") is None:
        return None                          # nothing to strip (already assumed)
    if it.get("facing_source"):
        return None                          # a provenance marker keeps it at 0.55 -> would not fire
    name = it.get("name")
    if name is None:
        return None
    try:
        if PG.confirmed_rot(it, confirmed or []) is not None:
            return None                      # owner-signed rot -> 1.0 -> would not fire
    except Exception:
        pass
    if CF._note_asserts(it, CF._FACING_WORDS):
        return None                          # a note asserting the facing keeps it at 0.55
    out = copy.deepcopy(spec)
    _get(out, loc).pop("rot", None)
    return out, _keyentry(name, "rot_stripped_directional", "flag", ["confidence"], None,
                          note="severity MEDIUM near a facade else LOW (assess_room geometry-dependent)")


def mut_zone_below_grade_unsigned(spec, loc, confirmed=None):
    it = _get(spec, loc)
    name = it.get("name")
    if name is None:
        return None
    if PG._norm_zone(it.get("zone")) is not None:
        return None                          # already carries a zone class -> not a fresh change
    if it.get("zone_source") == "owner-signed":
        return None
    try:
        if PG.confirmed_zone(it, confirmed or []) is not None:
            return None                      # owner-signed zone in the ledger -> cross_signal's
                                             # _owner_signed_zone adjudicates it away (early return,
                                             # zero new flags) -> a MISS that deflates recall. Mirror
                                             # the collector's suppression, as size/rot generators do.
    except Exception:
        pass
    _room, outline = _container(spec, loc)
    if not _centroid_inside(it, outline):
        return None                          # cross_signal only fires when the piece is drawn INSIDE
    out = copy.deepcopy(spec)
    _get(out, loc)["zone"] = "below_grade"
    return out, _keyentry(name, "zone_below_grade_unsigned", "flag", ["cross_signal"], "HIGH")


_GENERATORS = {
    "facing_flip_directional": mut_facing_flip_directional,
    "facing_flip_box": mut_facing_flip_box,
    "kind_change_unsigned": mut_kind_change_unsigned,
    "kind_change_vs_signature": mut_kind_change_vs_signature,
    "size_implausible": mut_size_implausible,
    "size_off_prior_band": mut_size_off_prior_band,   # the only generator that needs `priors`
    "rot_stripped_directional": mut_rot_stripped_directional,
    "zone_below_grade_unsigned": mut_zone_below_grade_unsigned,
}


# ---- suite runners (guarded: a broken module -> ERROR coverage, never a crash) --------
def _flag_key(collector, rec):
    """Identity key for a domain record -- (collector, signal, room, sorted subjects). Deliberately
    OMITS severity: a mutation that merely upgrades an existing base doubt's band on the SAME
    subject+signal is NOT counted as a new catch (the strict/honest direction -- we only credit a
    genuinely NEW doubt)."""
    subs = tuple(sorted(str(s) for s in (rec.get("subjects") or [])))
    return (collector, rec.get("signal"), rec.get("room"), subs)


def _collect_static(spec, confirmed, walls, glazing_cands, errors, priors=None):
    """cross_signal + anomaly + confidence records for ONE spec, tagged with their collector. Each
    call is guarded; a raising module records into `errors` and contributes no flags (never aborts).
    `priors` feeds anomaly's corpus band lane AND confidence's prior_kind corroboration context --
    the SAME wiring self_audit.collect_* uses, so F7 measures the suite as it actually runs."""
    out = []
    params = {"confirmed": confirmed} if confirmed else None
    ctx = None
    if priors is not None:
        try:
            import kind_priors as KP
            ctx = KP.build_prior_context([p for p, _sub in CF._all_pieces(spec)], priors)
        except Exception as e:
            errors.setdefault("prior_context", str(e))
    for collector, fn in (("cross_signal",
                           lambda: CS.check_room(spec, walls=walls, glazing_cands=glazing_cands,
                                                 params=params)),
                          ("anomaly",
                           lambda: AF.check_room(spec, priors=priors, params=params)),
                          ("confidence",
                           lambda: CF.assess_room(spec, confirmed, context=ctx))):
        try:
            for rec in fn() or []:
                out.append((collector, rec))
        except Exception as e:
            errors.setdefault(collector, str(e))
    return out


def _collect_rebuild(prior_spec, current_spec, confirmed, errors):
    """rebuild_diff records for prior->current (both single-spec lists), tagged 'rebuild_diff'."""
    out = []
    try:
        for rec in RD.diff_rounds([prior_spec], [current_spec], confirmed=confirmed) or []:
            out.append(("rebuild_diff", rec))
    except Exception as e:
        errors.setdefault("rebuild_diff", str(e))
    return out


def _coverage(base_specs, confirmed, walls, glazing_cands, priors=None):
    """Per-collector honest coverage over the UNMUTATED specs (READ/UNWIRED/ABSENT/ERROR), so a
    recall number is never read without the state of the collector that produced it. rebuild_diff is
    reported as base-vs-base (structurally UNWIRED -- no prior round on a live single-round project);
    F7 supplies the prior round SYNTHETICALLY (the unmutated base) per mutation, so its diff lane IS
    exercised even though a real prior round is absent -- noted explicitly."""
    cov = {}
    for collector, covfn in (
            ("cross_signal", lambda s: CS.check_coverage(s, walls=walls, glazing_cands=glazing_cands)),
            ("anomaly", lambda s: AF.check_coverage(s, priors=priors,
                                                    params={"confirmed": confirmed} if confirmed else None)),
            ("confidence", lambda s: CF.assess_coverage(s, confirmed))):
        statuses, note = [], None
        for _name, spec in base_specs:
            try:
                c = covfn(spec)
            except Exception as e:
                statuses.append("ERROR")
                note = f"{collector} coverage raised: {e}"
                continue
            if collector == "cross_signal":
                statuses.append("READ" if any(v.get("eligible") for v in c.values()) else "UNWIRED")
            elif collector == "anomaly":
                statuses.append(c.get("size_implausible", {}).get("status", "ABSENT"))
            else:
                statuses.append(c.get("status", "ABSENT"))
        cov[collector] = {"status": _fold_status(statuses), "per_spec": statuses, "note": note}
    # READ requires a USABLE artifact shape (same probe anomaly_flags.check_coverage applies) --
    # `priors is not None` alone would claim READ off a garbage doc while every mutation skips.
    usable_docs = AF._priors_docs(priors)
    cov["prior_band"] = {
        "status": "READ" if usable_docs else "UNWIRED",
        # the 1-doc string is FROZEN verbatim: the committed 2026-07-13 single-corpus report
        # regenerates byte-identically under this stem (same rule as the frozen stems below)
        "note": (("a kind-priors artifact feeds anomaly's corpus band + confidence's "
                  "prior_kind corroboration (and the size_off_prior_band class)")
                 if len(usable_docs) == 1 else
                 (f"{len(usable_docs)} kind-priors docs feed anomaly's corpus band + "
                  "confidence's prior_kind corroboration (and the size_off_prior_band class)")
                 if usable_docs else
                 ("a priors value was supplied but holds NO usable kind-priors doc (no kinds "
                  "dict) -- the corpus tier did not run" if priors is not None else
                  "no kind-priors artifact -- the corpus tier is unwired; size_off_prior_band "
                  "skips every item (reported unwired, never a silent pass)"))}
    # rebuild_diff: the real diff_coverage of base-vs-base + the F7 note that F7 injects the prior.
    try:
        rc = RD.diff_coverage([s for _n, s in base_specs], [s for _n, s in base_specs])
        cov["rebuild_diff"] = {"status": rc.get("status"), "shared_rooms": rc.get("shared_rooms"),
                               "note": "F7 supplies the prior round synthetically (unmutated base) "
                                       "per mutation; a REAL prior reading round is absent on this "
                                       "single-round project -- the diff lane is exercised, not idle"}
    except Exception as e:
        cov["rebuild_diff"] = {"status": "ERROR", "note": str(e)}
    return cov


def _fold_status(statuses):
    """Fold a per-spec status list into one collector verdict: READ if any spec READ; else the
    'loudest' non-READ (ERROR > UNWIRED > ABSENT). '' when nothing ran."""
    if not statuses:
        return "ABSENT"
    if "READ" in statuses:
        return "READ"
    for s in ("ERROR", "UNWIRED", "ABSENT"):
        if s in statuses:
            return s
    return statuses[0]


# ---- the harness ----------------------------------------------------------------------
def run_localization(base_specs, confirmed, classes=None, walls=None, glazing_cands=None,
                     priors=None):
    """Mutate EVERY eligible item of every spec, once per class, and measure whether a NEW flag
    lands on the mutated item. Returns a report dict.

    base_specs = [(name, spec_dict)] (name is display-only; rebuild matches by room.type). confirmed
    = the owner confirmed[] ledger list. classes = which mutation classes to run (default ALL).
    walls/glazing_cands feed cross_signal's facade checks (optional; absent -> those checks abstain).
    priors = a kind-priors artifact, a LIST of them, or None: wired into anomaly + confidence
    exactly as self_audit wires it (so F7 measures the live-suite configuration) and into the
    size_off_prior_band generator; None reproduces the priors-less suite bit-for-bit.

    DELTA: base_flags per spec computed once (static collectors on the unmutated spec + a base-vs-base
    rebuild, which is empty). For each (spec, item, class): build the one-field mutation, run the SAME
    collectors (rebuild's prior = the unmutated base spec), and take new_flags = flags whose identity
    key was not in base. HIT = a new flag whose subjects[] contain the mutated item's name."""
    classes = tuple(classes) if classes else ALL_CLASSES
    errors = {}
    per_class = {c: _empty_class() for c in classes}

    for spec_name, spec in base_specs:
        base = (_collect_static(spec, confirmed, walls, glazing_cands, errors, priors=priors)
                + _collect_rebuild(spec, spec, confirmed, errors))
        base_keys = {_flag_key(col, rec) for col, rec in base}
        for loc, _it in _iter_items(spec):
            for cls in classes:
                gen = _GENERATORS[cls]
                # only the prior-band generator consumes `priors`; the rest keep the uniform
                # (spec, loc, confirmed) signature untouched.
                res = (gen(spec, loc, confirmed, priors=priors)
                       if cls == "size_off_prior_band" else gen(spec, loc, confirmed))
                acc = per_class[cls]
                if res is None:
                    acc["n_skipped"] += 1
                    continue
                mutated, ke = res
                extra = ke.pop("_extra_confirmed", None)
                eff_conf = (list(confirmed) + extra) if extra else confirmed
                cur = (_collect_static(mutated, eff_conf, walls, glazing_cands, errors,
                                       priors=priors)
                       + _collect_rebuild(spec, mutated, eff_conf, errors))
                new = [(col, rec) for col, rec in cur if _flag_key(col, rec) not in base_keys]
                _score_mutation(acc, ke, new, spec_name)

    summary = _summarise(per_class, classes)
    coverage = _coverage(base_specs, confirmed, walls, glazing_cands, priors=priors)
    if errors:
        coverage["_collector_errors"] = errors
    return {"schema": SCHEMA, "n_specs": len(base_specs),
            "classes": list(classes), "per_class": per_class,
            "summary": summary, "coverage": coverage}


def _empty_class():
    return {"n_mutations": 0, "n_skipped": 0, "n_hit": 0,
            "n_caught_by_expected": 0, "n_severity_match": 0,
            "n_new_flags_total": 0, "n_new_flags_on_target": 0,
            "misses": [], "overfires": [], "hits": []}


def _score_mutation(acc, ke, new, spec_name):
    """Fold ONE mutation's outcome into its class accumulator. `new` = [(collector, record)]."""
    acc["n_mutations"] += 1
    name = ke["item"]
    on_target = [(col, rec) for col, rec in new
                 if name in {str(s) for s in (rec.get("subjects") or [])}]
    acc["n_new_flags_total"] += len(new)
    acc["n_new_flags_on_target"] += len(on_target)

    if ke["expect"] == "nonflag":
        if new:                              # ANY new flag on a render-inert mutation is an overfire
            acc["overfires"].append({
                "item": name, "spec": spec_name,
                "flags": sorted(f"{col}:{rec.get('signal')}[{rec.get('severity')}]"
                                for col, rec in new)})
        return

    if on_target:
        acc["n_hit"] += 1
        catchers = sorted({col for col, _rec in on_target})
        by_expected = [(col, rec) for col, rec in on_target if col in ke["collectors"]]
        if by_expected:
            acc["n_caught_by_expected"] += 1
        sev_match = (ke["severity"] is None
                     or any(rec.get("severity") == ke["severity"] for _col, rec in by_expected))
        if ke["severity"] is not None and sev_match:
            acc["n_severity_match"] += 1
        acc["hits"].append({
            "item": name, "spec": spec_name, "caught_by": catchers,
            "expected": ke["collectors"], "caught_by_expected": bool(by_expected),
            "expected_severity": ke["severity"],
            "got_severity": sorted({rec.get("severity") for col, rec in on_target
                                    if col in ke["collectors"]}) or
                            sorted({rec.get("severity") for _c, rec in on_target})})
    else:
        acc["misses"].append({
            "item": name, "spec": spec_name, "expected": ke["collectors"],
            "expected_severity": ke["severity"],
            "off_target_new_flags": sorted(f"{col}:{rec.get('signal')}" for col, rec in new),
            "note": ke.get("note")})


def _ratio(num, den):
    return round(num / den, 3) if den else None


def _summarise(per_class, classes):
    """Fold the per-class accumulators into the headline. HONESTY guards on top of the raw recall:
      * macro_recall counts ANY collector's on-target catch (a backstop by a non-target collector
        still lands on the item). That flatters the target lane, so we ALSO report
        macro_recall_by_expected (only the class's OWN collector) and list `backstopped_classes` --
        any should-flag lane whose headline recall is kept green solely by another collector. Without
        this a target-collector regression (e.g. cross_signal going zone-blind while rebuild_diff's
        _zone_change backstops the number) would read as clean.
      * a should-flag lane with ZERO eligible items (every item skipped) never ran at all -- it is NOT
        averaged into macro_recall (an empty denominator) and it is NOT blind (blind needs a real
        0/N). Such a lane is reported as `unwired_classes` and counted in n_exercised/n_should so a
        never-tested detection lane cannot hide behind an all-clean headline."""
    recalls = []
    recalls_by_expected = []
    blind = []
    unwired = []
    backstopped = []
    n_should = 0
    for cls in classes:
        if cls in NONFLAG_CLASSES:
            continue
        n_should += 1
        a = per_class[cls]
        if a["n_mutations"] == 0:
            unwired.append(cls)              # zero eligible items -> lane never exercised (not blind)
            continue
        r = _ratio(a["n_hit"], a["n_mutations"])
        rbe = _ratio(a["n_caught_by_expected"], a["n_mutations"])
        if r == 0.0:
            blind.append(cls)
        if rbe is not None and r is not None and rbe < r:
            backstopped.append(cls)          # kept green only by a non-target collector's catch
        if r is not None:
            recalls.append(r)
        if rbe is not None:
            recalls_by_expected.append(rbe)
    macro_recall = round(sum(recalls) / len(recalls), 3) if recalls else None
    macro_recall_by_expected = (round(sum(recalls_by_expected) / len(recalls_by_expected), 3)
                                if recalls_by_expected else None)
    tot = sum(per_class[c]["n_new_flags_total"] for c in classes if c in SHOULD_FLAG_CLASSES)
    ont = sum(per_class[c]["n_new_flags_on_target"] for c in classes if c in SHOULD_FLAG_CLASSES)
    overfire = sum(len(per_class[c]["overfires"]) for c in classes if c in NONFLAG_CLASSES)
    return {"macro_recall": macro_recall,
            "macro_recall_by_expected": macro_recall_by_expected,
            "precision_on_target": _ratio(ont, tot),
            "blind_classes": blind, "unwired_classes": unwired,
            "backstopped_classes": backstopped,
            "n_should_flag_classes": n_should,
            "n_exercised_classes": n_should - len(unwired),
            "overfire_mutations": overfire}


# ---- per-class table (shared by CLI stdout + md report) -------------------------------
def _class_rows(report):
    """[(class, recall, precision, caught_by_expected, severity_match, n_mut, n_skip, extra)]."""
    rows = []
    for cls in report["classes"]:
        a = report["per_class"][cls]
        if cls in NONFLAG_CLASSES:
            rows.append((cls, "n/a (nonflag)", "n/a",
                         f"overfire {len(a['overfires'])}/{a['n_mutations']}", "-",
                         a["n_mutations"], a["n_skipped"], "expect NO flag"))
            continue
        recall = _ratio(a["n_hit"], a["n_mutations"])
        prec = _ratio(a["n_new_flags_on_target"], a["n_new_flags_total"])
        cbe = _ratio(a["n_caught_by_expected"], a["n_mutations"])
        # severity-match is only meaningful when the class expects a specific band (some -- e.g.
        # rot_stripped -- have a geometry-dependent band, keyentry severity=None -> report "n/a").
        exp_sev = next((h["expected_severity"] for h in a["hits"]), None)
        sev = _ratio(a["n_severity_match"], a["n_hit"]) if (a["n_hit"] and exp_sev is not None) \
            else "n/a"
        rows.append((cls, recall, prec, cbe, sev, a["n_mutations"], a["n_skipped"], ""))
    return rows


# ---- disk / CLI shell -----------------------------------------------------------------
def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _load_project(project_dir):
    """Reuse self_audit's disk helpers to load the SAME per-room specs / walls / owner ledger the
    live audit reads (single source of truth for 'what is this project's current read'). Returns
    (base_specs, confirmed, walls, glazing_cands, layout_dir)."""
    project_dir = os.path.abspath(project_dir)
    gate_path = A._pick_gate(project_dir)[0]
    layout_dir = os.path.dirname(gate_path) if gate_path else os.path.join(project_dir, "03_layout")
    specs = A._find_specs(layout_dir)
    base_specs = [(os.path.basename(p), spec) for p, spec in specs]
    review = {}
    rp = os.path.join(layout_dir, "placement-review.json")
    if os.path.exists(rp):
        try:
            review = _load(rp)
        except Exception:
            review = {}
    confirmed = (review.get("confirmed") if isinstance(review, dict) else None) or []
    walls = A._load_walls(layout_dir)
    glazing_cands = None
    gp = os.path.join(layout_dir, "glazing-candidates.json")
    if os.path.exists(gp):
        try:
            gd = _load(gp)
            glazing_cands = gd.get("candidates") if isinstance(gd, dict) else None
        except Exception:
            glazing_cands = None
    return base_specs, confirmed, walls, glazing_cands, layout_dir


def render_md(report, project_dir):
    s = report["summary"]
    L = [f"# flag-localization (benchmark F7) -- {os.path.basename(os.path.abspath(project_dir))}",
         "",
         f"**macro localization-recall {s['macro_recall']}** "
         f"(by-expected {s['macro_recall_by_expected']}; "
         f"{s['n_exercised_classes']}/{s['n_should_flag_classes']} should-flag lanes exercised)"
         f"  ·  on-target precision {s['precision_on_target']}  ·  "
         f"overfire mutations {s['overfire_mutations']}  ·  "
         f"blind classes: {', '.join(s['blind_classes']) or 'none'}  ·  "
         f"unwired (never-exercised) classes: {', '.join(s['unwired_classes']) or 'none'}  ·  "
         f"backstopped-only classes: {', '.join(s['backstopped_classes']) or 'none'}",
         "",
         "> Synthetic-answer-key lane: the 'truth' is MINTED by injecting one deliberate error into "
         "one item of an otherwise-good read, so recall/precision measure whether the tier-1 "
         "self-doubt suite FINGERS the broken item on THIS project. This is NOT a corpus benchmark "
         "and does not measure generalisation -- its sibling `benchmark_reader.py` is the "
         "have-ground-truth corpus lane (annotated Structured3D / FloorPlanCAD).",
         "",
         "## Per-class recall / precision",
         "",
         "| class | recall | precision | caught-by-expected | severity-match | n_mut | n_skip |",
         "|---|---|---|---|---|---|---|"]
    for cls, recall, prec, cbe, sev, n_mut, n_skip, extra in _class_rows(report):
        tag = f" {extra}" if extra else ""
        L.append(f"| {cls}{tag} | {recall} | {prec} | {cbe} | {sev} | {n_mut} | {n_skip} |")
    L += ["", "recall = mutations whose planted error raised a NEW on-target flag by ANY collector / "
          "eligible mutations. by-expected recall = the same but crediting ONLY the collector the "
          "class targets (a lower by-expected number means another collector is backstopping the "
          "headline -- listed as *backstopped-only*, so a target-lane regression can't hide). "
          "precision = on-target new flags / all new flags (splash onto innocents lowers it). "
          "caught-by-expected = share caught by the collector the class targets. severity-match = of "
          "hits, share whose expected collector fired at the expected band. *unwired* should-flag "
          "classes had zero eligible items -- the lane was never exercised (distinct from *blind* = "
          "ran on real items and caught none).", ""]

    L.append("## Misses (planted errors the suite did NOT localize -- the blind spots)")
    any_miss = False
    for cls in report["classes"]:
        misses = report["per_class"][cls]["misses"]
        if not misses:
            continue
        any_miss = True
        L.append(f"### {cls}")
        for m in misses:
            off = f"; off-target noise: {m['off_target_new_flags']}" if m["off_target_new_flags"] else ""
            note = f"  (note: {m['note']})" if m.get("note") else ""
            L.append(f"- **{m['item']}** [{m['spec']}] — expected {m['expected']} "
                     f"@{m['expected_severity']}{off}{note}")
    if not any_miss:
        L.append("- (none — every eligible planted error raised an on-target flag)")
    L.append("")

    L.append("## Overfires (render-inert mutations that WRONGLY raised a flag -- precision leaks)")
    any_of = False
    for cls in NONFLAG_CLASSES:
        if cls not in report["per_class"]:
            continue
        for o in report["per_class"][cls]["overfires"]:
            any_of = True
            L.append(f"- **{o['item']}** [{o['spec']}] ({cls}) — raised {o['flags']}")
    if not any_of:
        L.append("- (none — every render-inert box-flip stayed silent, as designed)")
    L.append("")

    L.append("## Severity gaps (caught, but not at the expected band)")
    any_gap = False
    for cls in SHOULD_FLAG_CLASSES:
        a = report["per_class"].get(cls)
        if not a:
            continue
        for h in a["hits"]:
            if h["expected_severity"] is None or not h["caught_by_expected"]:
                continue
            if h["expected_severity"] not in (h["got_severity"] or []):
                any_gap = True
                L.append(f"- **{h['item']}** [{h['spec']}] ({cls}) — expected "
                         f"{h['expected_severity']}, got {h['got_severity']}")
    if not any_gap:
        L.append("- (none)")
    L.append("")

    L.append("## Collector coverage (was the lane even looking?)")
    for col, c in report["coverage"].items():
        if col == "_collector_errors":
            L.append(f"- **{col}**: {c}")
            continue
        note = f" — {c['note']}" if c.get("note") else ""
        L.append(f"- **{col}**: {c.get('status')}{note}")
    L += ["", "READ = the lane had eligible inputs; UNWIRED = ran but nothing eligible (never a "
          "pass); ABSENT = no input; ERROR = the lane raised (a blind spot in the harness itself). "
          "A low recall under UNWIRED/ERROR coverage means *did not look*, not *clean*.",
          "",
          "*Generated by flag_localization.py (F7). Sibling corpus lane: benchmark_reader.py.*"]
    return "\n".join(L)


def _print_table(report):
    s = report["summary"]
    print(f"F7 flag-localization: macro-recall {s['macro_recall']} "
          f"(by-expected {s['macro_recall_by_expected']}; "
          f"{s['n_exercised_classes']}/{s['n_should_flag_classes']} lanes exercised)  "
          f"precision {s['precision_on_target']}  "
          f"overfires {s['overfire_mutations']}  "
          f"blind={s['blind_classes'] or 'none'}  "
          f"unwired={s['unwired_classes'] or 'none'}  "
          f"backstopped={s['backstopped_classes'] or 'none'}")
    hdr = f"{'class':28} {'recall':>8} {'prec':>7} {'cbe':>6} {'sev':>6} {'mut':>4} {'skip':>5}"
    print(hdr)
    print("-" * len(hdr))
    for cls, recall, prec, cbe, sev, n_mut, n_skip, _extra in _class_rows(report):
        print(f"{cls:28} {str(recall):>8} {str(prec):>7} {str(cbe):>6} {str(sev):>6} "
              f"{n_mut:>4} {n_skip:>5}")


def _report_stem(priors):
    """STEM = CONFIG, keyed by doc IDENTITY (meta.source), never by count (review finding
    2026-07-14: count-keyed stems let an S3D-solo run overwrite the committed FloorPlanCAD
    record, and a kinds-less doc that passes KP.load overwrite it with an unwired run).
    Frozen stems exist ONLY for the exact configurations whose records are committed:
      None                          -> flag-localization-2026-07-08          (baseline)
      [floorplancad]                -> flag-localization-priors-2026-07-13   (FPC wiring)
      [floorplancad, structured3d]  -> flag-localization-priors-multi-2026-07-14
    Any other configuration (a different doc, a doc set with a stray/unusable member, a
    future third corpus) gets its own sources-keyed adhoc stem and can never clobber a
    frozen record."""
    if priors is None:
        return "flag-localization-2026-07-08"
    entries = list(priors) if isinstance(priors, (list, tuple)) else [priors]
    usable = AF._priors_docs(priors)
    sources = sorted(str((d.get("meta") or {}).get("source") or "floorplancad")
                     for d in usable)
    if len(usable) != len(entries):
        # a supplied set with ANY unusable member runs degraded (the confidence context path
        # errors on it) -- its report must never claim a frozen clean-config stem
        return ("flag-localization-priors-" + ("+".join(sources) if sources else "nodocs")
                + "-degraded-adhoc")
    if sources == ["floorplancad"]:
        return "flag-localization-priors-2026-07-13"
    if sources == ["floorplancad", "structured3d"]:
        return "flag-localization-priors-multi-2026-07-14"
    return "flag-localization-priors-" + "+".join(sources) + "-adhoc"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    project_dir = args[0]
    # --priors auto|none|PATH (default auto): auto = the SAME qa//knowledge/ discovery
    # self_audit uses, so F7 measures the configuration the live suite actually runs;
    # none = the frozen priors-less baseline (writes the original 2026-07-08 stem, byte-compat).
    priors_arg = "auto"
    if "--priors" in args:
        i = args.index("--priors")
        if i + 1 >= len(args):
            raise SystemExit("--priors needs a value: auto | none | <path>")
        priors_arg = args[i + 1]
    if priors_arg == "none":
        priors = None
    elif priors_arg == "auto":
        priors = A._load_priors(os.path.abspath(project_dir))
    else:
        import kind_priors as KP
        priors = KP.load(priors_arg)         # schema-checked, fails LOUDLY on a non-priors file
    base_specs, confirmed, walls, glazing_cands, _layout = _load_project(project_dir)
    if not base_specs:
        raise SystemExit(f"no scene-graph.*.json specs found under {project_dir}")
    report = run_localization(base_specs, confirmed, walls=walls, glazing_cands=glazing_cands,
                              priors=priors)

    _print_table(report)
    md = render_md(report, project_dir)
    # repo qa/reports (NEVER the v4 project dir -- the parallel pane owns v4 outputs)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    out_dir = os.path.join(repo_root, "qa", "reports")
    os.makedirs(out_dir, exist_ok=True)
    stem = _report_stem(priors)
    md_path = os.path.join(out_dir, stem + ".md")
    json_path = os.path.join(out_dir, stem + ".json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"\nwrote {md_path}\nwrote {json_path}")


if __name__ == "__main__":
    main()
