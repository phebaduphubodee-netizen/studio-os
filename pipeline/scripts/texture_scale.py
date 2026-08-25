"""texture_scale.py — R8's "scale is ASSERTED on every ingest", on the TEXTURE side.

    python pipeline/scripts/texture_scale.py            # check the registry
    python pipeline/scripts/texture_scale.py --backfill # write sidecars from the API
    python pipeline/scripts/texture_scale.py --sweep    # list every tile literal

exit 0 = every mapped texture renders at a size somebody asserted
exit 1 = a site maps a texture at a size nobody asserted, or an assertion no
         longer matches the code
exit 2 = COULD NOT RUN (registry unreadable, cache missing). Never a pass.

WHY THIS EXISTS, AND WHY IT IS NOT `asset_scale.py`
---------------------------------------------------
R8 has said "scale is ASSERTED on every ingest, never assumed" since 2026-08-01.
`asset_scale.py` implements that for MESHES — bands, a bounds reader, a
`<asset>.scale.json` sidecar, a door in `_model_path`, and a gate rung. The
TEXTURE side never got any of it, and on 2026-08-24 the cost was measured:

    slug                  declared        mapped at              ratio
    wood_floor            1699.9997 mm    2.4 m   room floor     1.4118  TYPED
    poly_wool_herringbone  270.08 mm      1.3 m   the rug        4.8134  TYPED
    rough_linen            270.71 mm      0.85 m  all soft goods 3.1399  TYPED
    oak_veneer_01         1830.0000 mm    1.83 m  millwork       1.0000  asserted
    plastered_wall_03     4000 mm         4.0 m   microcement    1.0000  asserted

NINE distinct live tile values for `wood_floor` alone, every one a bare literal.
The two rows that reproduce EXACTLY are the two where somebody wrote the number
down from the metadata — `material_presets.py:298` even says so in words
("dimensions [4000,4000] from the API on 2026-08-12 (scale asserted, never
assumed)"). The rows that were TYPED are the rows that are wrong. That is the
whole argument for this file: the method is already proven in this repo, on this
data, by the two people who used it.

TWO CORRECTIONS THE FIRST DRAFT OF THIS FILE GOT WRONG, kept because the shape of
the error is the point:
  * It listed the WALLS at 2.2 m = 1.2941x as a live defect. They are not.
    `surfaces.walls` resolves to factory "painted" (a flat colour) and
    `surfaces.feature_wall` to "proc_wood" (procedural, no image), so
    `_wall_uv(obj, tile_m=2.2)` writes a UV that nothing samples and the second
    such call is gated on a `pbr` factory this lane never selects. Correct
    arithmetic performed on a mapping no material wears — a declaration about the
    picture rather than the picture, which is the exact defect R11 exists to
    catch, committed by the audit of it.
  * It said the floor's boards were 254 mm and the artefact's 180 mm. Both were
    back-derived from `PLANK_PITCH_MM`, a constant THIS REPO chose for its own
    procedural veneer — a self-consistency check against our own number, which is
    the shape R7b warns about by name. Measured from the maps instead, the answer
    is 266.67 mm rendered against 188.889 mm real.

WHAT THE ERROR LOOKS LIKE IN THE PICTURE, because a ratio is not a defect
------------------------------------------------------------------------
The texture was MEASURED, not inferred: 9 board joints across the tile, found in
the AO and Displacement maps and confirmed independently by FFT harmonic (k=9)
and by circular autocorrelation, with the joint score separating from mid-board
by roughly 10x so the count does not depend on a threshold. Sub-pixel pitch
227.556 px at 0.8300780 mm/px = **188.889 mm per board** — and 9 x 189 mm =
1701 mm against the declared 1699.99969 mm, which is the publisher's metadata
confirming itself to 0.06%. 189 mm is an ordinary stocked engineered-oak width.

Mapped at 2.4 m those boards render **266.67 mm wide**. `build_room.py` declares
`PLANK_PITCH_MM = 180.0` with the comment "oak veneer leaf / plank width:
150-250 mm is the real range" — so the floor was drawing a board ABOVE this
repo's own stated maximum, and a search for a supplier selling ~267 mm returned
none (extra-wide oak is sold at 220 / 260 / 300 mm, not 267). The frame is not
being asked to match a taste; it is being asked to stop drawing a plank nobody
manufactures. At the asserted 1.7 m the boards render at their real 188.9 mm.

WHY IT HID FOR SEVEN WEEKS: `_planar_uv` divides u and v by the SAME tile_m, so
the stretch is isotropic. The planks keep their correct aspect ratio and the
floor is internally consistent — nothing inside it can reveal the error. It is
visible only by comparing the floor to an object of known size, or by reading
the texture's declared dimensions and counting features, which is what this
file now makes a rung do.

THE ONE HONEST COST, measured before this file was written and recorded here so
nobody has to rediscover it: at 2.40 m the visible floor shows **0.0%** repeated
texture — the oversize is *why* nothing repeats. At 1.70 m, 21.2% of visible
floor pixels become a duplicate pair, and the dominant pair is the floor sliver
LEFT of the bed against the sliver RIGHT of it (3.40 m apart laterally, 0.00 m in
depth, on a frontal-axial camera). Correcting the scale is therefore NOT free,
and a site that corrects it without also breaking the phase has traded one defect
for a worse-placed one. `departure` exists for exactly this: a site may map at
something other than the declared size, but it must say so and say why.

WHERE THE RUNGS GO — COPIED FROM THE MODEL SIDE ON PURPOSE
-----------------------------------------------------------
`asset_scale.write_sidecar`'s own docstring carries the lesson this file obeys:

    "IT LIVES HERE, NOT IN A FETCHER, because it was in one and that is why half
     the shelf was never asserted ... A step that only happens if each downloader
     remembers it is not a step."

So the fetcher is the CONVENIENCE, never the guarantee. The guarantee is (B) the
DOOR — `build_room._texset` is the one function every cached texture comes
through, and `declared_tile_m` is read there — and (C) this pure rung, called
from `rule_gate.check_room()`, which is the only entry point `build_room.py`
actually calls (`check()` is the retired reproduction lane and `enforce()` has no
production caller: wiring a new register to either is how this repo builds a
queue with no consumer).

NO ALLOWLIST (R9b). `sweep()` walks the whole tree for tile literals rather than
checking a list of files somebody remembered. "A rule that names the objects it
applies to will always exempt the next one." The historical backlog is a RATCHET
that may only fall, never a silent exemption — a machine that hard-fails all
sixteen cached sets on day one gets switched off and joins them (R13).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))

CACHE_REL = os.path.join("assets", "shared", "cc0", "textures")
REGISTRY_REL = os.path.join("qa", "texture-scale.json")

# A ratio is a measurement of a photograph against a mapping, so it is exact to
# the precision the API publishes. 0.5% is the slack for a preset that rounded
# 1699.9997 mm to 1.70 m, and nothing more.
RATIO_TOL = 0.005

# Minimum length of a `why`. Same spirit as decisions_check's 20 — a reason
# shorter than this is a label, and a label cannot be audited.
THIN_REASON_MIN = 20

# The sweep's targets: every shape this repo has ever used to set the world size
# of one texture repeat. Adding a NEW shape without adding it here is how the
# next one hides, so the list is deliberately broad and the ack list is a ratchet.
TILE_LITERAL_RE = re.compile(
    r"""(?x)
    (?:
        tile_m \s* = \s* (?P<a>\d+(?:\.\d+)?)      # tile_m=2.4  (call or preset)
      | uv_scale \s* = \s* (?P<b>\d+(?:\.\d+)?)    # trn002_build.py
      | grain_run_m \s* = \s* (?P<c>\d+(?:\.\d+)?) # the along-grain departure
    )""")

SWEPT_EXT = (".py",)
SWEPT_DIRS = ("pipeline", "projects", "templates", "scripts")


# --------------------------------------------------------------------------
# sidecars — what the photograph itself declares
# --------------------------------------------------------------------------

def texture_dir(slug, root=None):
    return os.path.join(root or REPO_ROOT, CACHE_REL, slug)


def sidecar_path(slug, root=None):
    """`<cache>/textures/<slug>/<slug>.scale.json` — beside the maps it describes,
    the same way asset_scale puts `<asset>.scale.json` beside the mesh."""
    return os.path.join(texture_dir(slug, root), slug + ".scale.json")


def read_sidecar(slug, root=None):
    p = sidecar_path(slug, root)
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def declared_tile_m(slug, root=None):
    """The world size of ONE repeat of this texture ACROSS U, in metres, as the
    source that published the photograph declares it. None when nobody asserted
    it.

    THE DOOR reads this. Returning None rather than a default is the whole
    point: a texture whose scale nobody asserted must not silently acquire a
    plausible one, because a plausible one is what 2.4 was.

    U ONLY, and callers of an anisotropic set must use `declared_aspect` too —
    see the note there."""
    d = declared_dimensions_mm(slug, root)
    return None if d is None else d[0] / 1000.0


def declared_dimensions_mm(slug, root=None):
    """(u_mm, v_mm) as published, or None."""
    sc = read_sidecar(slug, root)
    if not sc:
        return None
    d = sc.get("dimensions_mm")
    if not (isinstance(d, (list, tuple)) and len(d) >= 1):
        return None
    try:
        u = float(d[0])
        v = float(d[1]) if len(d) > 1 else u
    except (TypeError, ValueError):
        return None
    return (u, v)


def declared_tile_v_m(slug, root=None):
    """The world size of one repeat ACROSS V, in metres, as published. None when
    nobody asserted it.

    IT EXISTS BECAUSE `declared_tile_m` IS ONLY HALF THE ASSERTION. This law's own
    words are "A tile has TWO axes. `tile_m` asserts U and `tile_v_m` asserts V;
    one number may not stand for both, because four of the sixteen cached sets are
    not square." The registry has honoured that since birth (`tile_v_m` at the site
    level) but the READER side stopped at U, so every caller that went through the
    door got a square tile whatever the sidecar said. `poly_wool_herringbone` is
    270.0789 x 275.7000 mm — a 2.08% aspect the U-only door silently discarded.

    Falls back to the U size for a genuinely square set, so a caller may always
    pass both and a square tile costs nothing."""
    d = declared_dimensions_mm(slug, root)
    if d is None:
        return None
    return d[1] / 1000.0


def declared_aspect(slug, root=None):
    """v/u of the published tile. 1.0 for a square set.

    IT IS NOT DECORATION. Four of the sixteen sets this repo has cached are NOT
    square — `wood_cabinet_worn_long` is 1000 x 500 mm, a 2:1 tile. A mapping
    that carries ONE `tile_m` against a set like that draws V at twice its real
    size while U is exact, and the single number reads as if the whole thing had
    been asserted. That is the repo's own "one parameter carrying two things",
    on a photograph instead of a placement."""
    d = declared_dimensions_mm(slug, root)
    if d is None or not d[0]:
        return None
    return d[1] / d[0]


def write_sidecar(slug, dimensions_mm, source, root=None, note=None):
    """Record what the publisher declares. Pure I/O — the caller supplies the
    numbers, so this function is testable without a network."""
    d = texture_dir(slug, root)
    os.makedirs(d, exist_ok=True)
    dims = [float(x) for x in dimensions_mm]
    rep = {
        "slug": slug,
        "dimensions_mm": dims,
        "tile_m": round(dims[0] / 1000.0, 6),
        "aspect": round((dims[1] if len(dims) > 1 else dims[0]) / dims[0], 6),
        "source": source,
        "note": note or ("The world size of one repeat, as published. R8: scale "
                         "is ASSERTED on ingest, never assumed."),
    }
    with open(sidecar_path(slug, root), "w", encoding="utf-8", newline="") as f:
        json.dump(rep, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return rep


def cached_slugs(root=None):
    base = os.path.join(root or REPO_ROOT, CACHE_REL)
    try:
        return sorted(n for n in os.listdir(base)
                      if os.path.isdir(os.path.join(base, n)))
    except OSError:
        return []


# --------------------------------------------------------------------------
# the ratio, and what makes a departure legal
# --------------------------------------------------------------------------

def ratio(tile_m, declared_m):
    """How many times life-size this mapping draws the photograph."""
    if not declared_m:
        return None
    return float(tile_m) / float(declared_m)


def _read(root, rel):
    try:
        with open(os.path.join(root, rel), "r", encoding="utf-8",
                  errors="replace") as f:
            return f.read()
    except OSError:
        return None


def assert_violations(sid, site, root):
    """Borrowed in shape from `decisions_check.assert_violations`, which borrowed
    it from `orders_check.obeyed_assert`, because the defect is the same defect
    and a second dialect would be a second thing to get wrong: a row may name a
    file that EXISTS and still describe a mapping the file does not perform."""
    out = []
    aa = site.get("assert")
    if aa is None:
        return out
    if not isinstance(aa, list) or not aa:
        return [f"{sid}: `assert` must be a non-empty list of "
                f"{{file, pattern, why}} objects."]
    for i, a in enumerate(aa):
        tag = f"{sid} assert[{i}]"
        if not isinstance(a, dict):
            out.append(f"{tag}: not an object.")
            continue
        rel, pat, why = a.get("file"), a.get("pattern"), a.get("why")
        if not rel or not pat:
            out.append(f"{tag}: needs both `file` and `pattern`.")
            continue
        if not why or len(str(why).strip()) < THIN_REASON_MIN:
            out.append(f"{tag}: needs a `why` saying what the pattern proves.")
        txt = _read(root, rel)
        if txt is None:
            out.append(f"{tag}: names {rel}, which cannot be read. An assertion "
                       f"that cannot run must never read like one that passed.")
            continue
        try:
            hit = re.search(pat, txt, re.M) is not None
        except re.error as e:
            out.append(f"{tag}: pattern is not a valid regex ({e}).")
            continue
        if not hit:
            out.append(f"{tag}: /{pat}/ no longer matches {rel}. The site says "
                       f"what the build does with this texture and the build now "
                       f"does otherwise — reopen the row or carry it out.")
    return out


def site_violations(site, root, i=0):
    sid = site.get("id") or f"<site {i}>"
    out = []
    slug = site.get("slug")
    if not slug:
        return [f"{sid}: no `slug` — a mapping that cannot name its texture "
                f"cannot be checked against one."]
    if not site.get("surface"):
        out.append(f"{sid}: no `surface` — say WHICH thing in the frame wears "
                   f"this, or nobody can point at the consequence.")

    # R13's THIRD STATE. A site may be recorded UNFIXED — loudly, with a date so
    # its age prints and a named builder action to clear it — but it may never be
    # silent and it may never print as asserted. Without this the rung has only
    # two moves on a ratio it has measured but not yet decided: block the lane
    # (and get switched off in its first week, which R13 says in those words), or
    # sign a departure with an invented reason, which is worse because it launders
    # a defect into an assertion. `debt` is neither: it prints the measured ratio
    # every run, it does not block, and `debt_ratchet` stops the class from
    # growing.
    debt = site.get("debt")
    if debt not in (None, "", {}):
        if not isinstance(debt, dict):
            return out + [f"{sid} ({slug}): `debt` must be an object."]
        miss = [k for k in ("since", "restart_by", "measured_ratio")
                if not debt.get(k)]
        if miss:
            out.append(f"{sid} ({slug}): `debt` is missing {', '.join(miss)} — a "
                       f"debt with no age or no named action is a queue nobody "
                       f"has to visit.")
        if site.get("departure"):
            out.append(f"{sid} ({slug}): carries BOTH `debt` and `departure`. A "
                       f"ratio is either decided or it is not.")
        return out + assert_violations(sid, site, root)

    tile = site.get("tile_m")
    if tile is None:
        return out + [f"{sid} ({slug}): no `tile_m`."]
    try:
        tile = float(tile)
    except (TypeError, ValueError):
        return out + [f"{sid} ({slug}): `tile_m` is not a number."]

    declared = declared_tile_m(slug, root)
    if declared is None:
        out.append(f"{sid} ({slug}): NO SIDECAR — nothing has asserted what one "
                   f"repeat of this texture covers, so {tile} m is a number "
                   f"somebody typed. Run --backfill, or record a departure.")
        return out + assert_violations(sid, site, root)

    # SELF-CHECK, the shape pixel_check uses: the stored assertion must still
    # reproduce. A sidecar whose own tile_m disagrees with its own dimensions is
    # a hand-edited file, and a hand-edited assertion is not an assertion.
    sc = read_sidecar(slug, root) or {}
    stored = sc.get("tile_m")
    if stored is not None and abs(float(stored) - declared) > 1e-6:
        out.append(f"{sid} ({slug}): sidecar SELF-CHECK failed — it stores "
                   f"tile_m {stored} but its own dimensions_mm give {declared:.6f}.")

    # A TILE HAS TWO AXES AND ONE NUMBER MAY NOT STAND FOR BOTH.
    # `tile_m` is U. `tile_v_m` is V, optional only because most mappings are
    # uniform; absent, V is taken to be mapped at `tile_m` as well. Four of the
    # sixteen sets this repo has cached are NOT square (wood_cabinet_worn_long is
    # 1000 x 500 mm), so a uniform mapping of one of those draws V at twice life
    # size while U is exact -- and the single asserted-looking number hides it.
    # Same family as the repo's own "one parameter carrying two things".
    dims = declared_dimensions_mm(slug, root)
    declared_v = (dims[1] / 1000.0) if dims else declared
    tile_v = site.get("tile_v_m")
    tile_v = float(tile_v) if tile_v is not None else tile

    dep = site.get("departure")
    dep_axis = None
    if dep not in (None, "", {}):
        if not isinstance(dep, dict):
            out.append(f"{sid} ({slug}): `departure` must be an object carrying "
                       f"`axis`, `ratio` and `why`.")
            dep = None
        else:
            dep_axis = str(dep.get("axis") or "u").lower()
            if dep_axis not in ("u", "v", "both"):
                out.append(f"{sid} ({slug}): `departure.axis` must be u, v or "
                           f"both -- {dep_axis!r} names no axis.")
            why = dep.get("why")
            if not why or len(str(why).strip()) < THIN_REASON_MIN:
                out.append(f"{sid} ({slug}): a departure needs a `why` of at "
                           f"least {THIN_REASON_MIN} characters. 'looks better' "
                           f"is the reason 2.4 m survived for seven weeks.")
            if dep.get("ratio") is None:
                out.append(f"{sid} ({slug}): a departure must state its `ratio`, "
                           f"so the size it draws is written down and not "
                           f"recoverable only by dividing two other numbers.")

    for axis, t, d in (("u", tile, declared), ("v", tile_v, declared_v)):
        r = ratio(t, d)
        if r is None:
            continue
        if dep_axis in (axis, "both"):
            # `ratio` may be a number, or [u, v] when a UNIFORM mapping meets a
            # slightly non-square artefact: rough_linen is 270.71 x 271.30 mm, so
            # one scale produces two ratios (3.1399 and 3.1331) that differ by
            # more than RATIO_TOL. Forcing a single number there would have made
            # the register round one of them, which is the habit this file exists
            # to stop.
            raw = dep.get("ratio")
            try:
                dr = float(raw[0 if axis == "u" else 1]) if isinstance(
                    raw, (list, tuple)) else float(raw)
            except (TypeError, ValueError, IndexError):
                continue          # already reported above
            if abs(dr - r) > RATIO_TOL:
                out.append(f"{sid} ({slug}): departure on {axis.upper()} claims "
                           f"{dr:.4f}x and the numbers give {r:.4f}x.")
        elif abs(r - 1.0) > RATIO_TOL:
            out.append(f"{sid} ({slug}) on {site.get('surface')}: maps "
                       f"{axis.upper()} at {t} m against a declared {d:.4f} m = "
                       f"{r:.4f}x life size, with no `departure` recorded for "
                       f"that axis. Either map it at the asserted size, or sign "
                       f"the departure and say what it buys.")

    return out + assert_violations(sid, site, root)


# --------------------------------------------------------------------------
# the sweep — R9b, no allowlist
# --------------------------------------------------------------------------

def _slug_anchored_re(root=None):
    """A second pattern, anchored on the SLUG rather than on a keyword.

    THE FIRST VERSION OF THIS SWEEP MISSED AN ENTIRE LANE and the reason is worth
    keeping. `TILE_LITERAL_RE` looks for `tile_m=` / `uv_scale=` / `grain_run_m=`,
    which is every shape *build_room* uses — so it reported 12 hits and read like
    a clean census. The TRN lanes carry the tile as the FIFTH ELEMENT OF A
    POSITIONAL TUPLE (`"veneer_oak": ((r,g,b), 0.60, 0.0, "wood_floor", 3.2)`),
    which matches none of those keywords. Anchoring on the keyword is itself the
    allowlist R9b forbids, one level down: it names the SYNTAX it applies to and
    exempts the next syntax. The slug is DATA we already hold, so a line that
    names a cached texture and a number beside it is a candidate wherever it
    lives and whatever it looks like."""
    slugs = cached_slugs(root)
    if not slugs:
        return None
    alt = "|".join(re.escape(s) for s in sorted(slugs, key=len, reverse=True))
    return re.compile(r'["\'](?:%s)["\']\s*,\s*(\d+(?:\.\d+)?)' % alt)


def sweep(root=None):
    """Every tile literal in the tree, as (relpath, lineno, text).

    Walks rather than consulting a list of files, because a rule that names the
    files it applies to will always exempt the next one."""
    root = root or REPO_ROOT
    slug_re = _slug_anchored_re(root)
    hits = []
    for d in SWEPT_DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in ("__pycache__", ".git", "node_modules")]
            for fn in filenames:
                if not fn.endswith(SWEPT_EXT):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.read().splitlines()
                except OSError:
                    continue
                rel = os.path.relpath(p, root).replace("\\", "/")
                # The checker may not count ITSELF OR ITS OWN TESTS: its regex
                # source names every pattern it hunts for, and its test file is
                # made of deliberately-wrong fixtures (tile_m=2.4 against a
                # 1.7 m texture is the defect, written down on purpose). A rung
                # that scores its own source is a rung whose backlog number
                # moves when you edit a comment. NOTE the narrowness: this
                # skips two named files, NOT every test_*.py — excluding a
                # whole naming convention would be the allowlist R9b forbids,
                # and `test_trn001_geom.py` stays counted for that reason even
                # though its hit is a false positive.
                if rel.endswith(("pipeline/scripts/texture_scale.py",
                                 "pipeline/scripts/test_texture_scale.py")):
                    continue
                for n, ln in enumerate(lines, 1):
                    s = ln.strip()
                    if s.startswith("#"):
                        continue
                    if (TILE_LITERAL_RE.search(ln)
                            or (slug_re is not None and slug_re.search(ln))):
                        hits.append((rel, n, s[:160]))
    return hits


def sweep_violations(data, root=None):
    """The backlog is a RATCHET. It prints every run, it may fall, and it may
    never grow — which is the only shape that is honest on day one and still
    cannot be quietly ignored."""
    hits = sweep(root)
    base = data.get("sweep_baseline")
    if base is None:
        return hits, [f"texture-scale: no `sweep_baseline` — the unregistered "
                      f"backlog has no ceiling, so it can grow silently."]
    if len(hits) > int(base):
        return hits, [
            f"texture-scale: {len(hits)} tile literal(s) in the tree against a "
            f"baseline of {base}. The backlog is a ratchet and may only fall — "
            f"a NEW mapping must come in through the registry with its slug "
            f"asserted, not as another literal."]
    return hits, []


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def load(root=None, path_hint=REGISTRY_REL):
    p = os.path.join(root or REPO_ROOT, path_hint)
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def check(data, root=None):
    """Violations. Empty means every registered mapping draws its texture at a
    size somebody asserted, or says in writing why it does not."""
    root = root or REPO_ROOT
    if data is None:
        return [f"no readable texture-scale registry at {REGISTRY_REL}. R8 says "
                f"scale is asserted on every ingest; with no register there is "
                f"nothing to assert it against."]
    v = []
    sites = data.get("sites") or []
    if not sites:
        v.append("texture-scale: the registry holds no sites. An empty register "
                 "passes every check and proves nothing.")
    seen = set()
    for i, s in enumerate(sites):
        sid = s.get("id")
        if sid in seen:
            v.append(f"texture-scale: duplicate site id {sid!r}.")
        seen.add(sid)
        v += site_violations(s, root, i)
    _hits, sv = sweep_violations(data, root)
    v += sv
    # THE DEBT CLASS MAY NOT GROW. Same ratchet as the sweep, for the same reason:
    # a third state that can expand without limit is not a third state, it is an
    # exemption with a friendlier name.
    ndebt = len([s for s in sites if s.get("debt")])
    cap = data.get("debt_baseline")
    if cap is None:
        v.append("texture-scale: no `debt_baseline` — the unfixed class has no "
                 "ceiling, so it can grow silently.")
    elif ndebt > int(cap):
        v.append(f"texture-scale: {ndebt} site(s) carry unfixed scale debt "
                 f"against a baseline of {cap}. It may only fall.")
    return v


def summary(data, root=None):
    root = root or REPO_ROOT
    sites = (data or {}).get("sites") or []
    slugs = cached_slugs(root)
    with_sc = [s for s in slugs if read_sidecar(s, root)]
    deps = [s for s in sites if s.get("departure")]
    debts = [s for s in sites if s.get("debt")]
    return {
        "sites": len(sites),
        "departures": len(deps),
        "debt": len(debts),
        "debt_rows": debts,
        "debt_baseline": (data or {}).get("debt_baseline"),
        "cached": len(slugs),
        "asserted": len(with_sc),
        "sweep": len(sweep(root)),
        "baseline": (data or {}).get("sweep_baseline"),
    }


def lines(data, root=None):
    """One line, printed into the render path — his channel (R3/R11)."""
    s = summary(data, root)
    out = [f"TEXTURE SCALE: {s['asserted']}/{s['cached']} cached set(s) carry an "
           f"asserted size | {s['sites']} mapped site(s), {s['departures']} signed "
           f"departure(s) | {s['sweep']} tile literal(s) in tree "
           f"(baseline {s['baseline']})"]
    for d in s["debt_rows"]:
        out.append(f"  SCALE DEBT since {d['debt'].get('since')}: {d.get('slug')} "
                   f"on {d.get('surface')} renders at "
                   f"{d['debt'].get('measured_ratio')}x life size. "
                   f"{d['debt'].get('restart_by')}")
    if s["asserted"] < s["cached"]:
        out.append(f"  {s['cached'] - s['asserted']} cached texture set(s) have "
                   f"NO asserted size. Nothing may map them until they do — "
                   f"`python pipeline/scripts/texture_scale.py --backfill`.")
    return out


def _backfill(root=None, slugs=None):
    """Ask the publisher what it declares, once per slug, and write it down.
    Network lives ONLY here — everything above is pure so it can be tested."""
    import urllib.request
    root = root or REPO_ROOT
    todo = slugs or cached_slugs(root)
    ok = bad = 0
    for slug in todo:
        url = "https://api.polyhaven.com/info/" + slug
        try:
            # Poly Haven answers 403 without a User-Agent.
            rq = urllib.request.Request(
                url, headers={"User-Agent": "studio-os/1.0 (texture_scale)"})
            with urllib.request.urlopen(rq, timeout=30) as r:
                info = json.load(r)
        except Exception as e:                       # noqa: BLE001 - report, continue
            print(f"  {slug}: COULD NOT ASK ({type(e).__name__}: {e})")
            bad += 1
            continue
        dims = info.get("dimensions")
        if not dims:
            print(f"  {slug}: the publisher declares NO dimensions — this "
                  f"texture has no asserted size and may not be mapped.")
            bad += 1
            continue
        rep = write_sidecar(slug, dims, url, root)
        print(f"  {slug}: {rep['tile_m']} m  <- {dims}")
        ok += 1
    print(f"  backfill: {ok} asserted, {bad} could not be")
    return 0 if not bad else 1


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--backfill" in argv:
        argv.remove("--backfill")
        return _backfill(slugs=argv or None)
    if "--sweep" in argv:
        for rel, n, s in sweep():
            print(f"  {rel}:{n}: {s}")
        return 0
    data = load()
    if data is None:
        print(f"TEXTURE SCALE: COULD NOT RUN — no registry at {REGISTRY_REL}")
        return 2
    v = check(data)
    for ln in lines(data):
        print(ln)
    for x in v:
        print(f"  VIOLATION: {x}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
