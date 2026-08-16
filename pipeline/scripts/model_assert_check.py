#!/usr/bin/env python3
"""Every model the spec names carries its OWN measured size, and the gate diffs
that number against the file — P2r-9.

WHAT WENT WRONG, IN THE OWNER'S SENTENCE FIRST (2026-08-16). He looked at the
acquired bed and said we had stacked something onto it. He was right before any
instrument was. The spec's `bed_models_note` said, in prose:

    "Scale ASSERTED as bedding_set: 2198.1 mm on y, band 1400-2900
     (sidecar 2026-08-14). The file also carries a 2 m junk cube, a 12-poly
     mattress slab and pillow-scale parts"

Every word of that belongs to `2b142a32`, the candidate this lane REJECTED after
the eye called it a slept-in crumple. The asset actually referenced, `ub806591a`,
measures **1599.9 mm** on y, has 6 primitives and all of them are cloth — and its
own sidecar said so, correctly, the whole time. Nobody was lying and nothing was
stale: the number was simply never DATA. It was a sentence, and a sentence is not
diffable, so a 1505 x 1600 mm duvet was scaled 1.236x onto a 1999.6 x 2148.8 mm
mattress, landed 139 and 299 mm short, and its hem came to rest ON the mattress
face instead of past it. We dressed a 2.1 m bed in a 1.5 m duvet for two rounds.

THE DEFECT IS THE CHANNEL, NOT THE NUMBER. This repo has now shipped the same
shape three times — a queue whose consumer never visits it (357 critic items /
~22 built), a held-out scoring set with no reader (`judge_lines`), and now a
measurement kept where only a human re-reading prose could ever check it. The fix
is never "be more careful with the note". It is to move the claim into a field a
program reads, and then to make a program read it.

WHAT THIS MODULE ENFORCES

  1. EVERY SPEC-SIDE MODEL REFERENCE HAS A ROW. Discovery is not an allowlist —
     R9b's law ("a rule that names the objects it applies to will always exempt
     the next one") applied to model references. Two INDEPENDENT detectors, and
     their union is the scope:
       (a) KEY SHAPE  — any key `model`, `*_model`, `*_models` (never `*_note`);
       (b) VALUE SHAPE — any string ANYWHERE in the spec that resolves to a
           model directory on either shelf. This one does not care what the key
           is called, so a reference filed under a new name still gets caught.

  2. NO ORPHAN ROWS. A row whose slug no reference points at is refused BY NAME.
     This is the p2r36 defect made structurally impossible: the numbers of a
     rejected candidate cannot sit in the file, because nothing points at it.

  3. THE ROW IS DIFFED THREE WAYS, and all three must agree:
       ASSERTED (the spec's own field)
         vs SIDECAR (`<asset>.scale.json`, written by asset_scale at ingest)
         vs LIVE (this checker re-reads the file's bounds, right now).
     The live leg is what makes a sidecar unable to go stale: swap the asset
     under a slug and the numbers part company. It is the same law `pixel_check`
     carries as SELF-CHECK — a stored measurement that no longer reproduces is
     not a measurement.

  4. THE BAND MUST STILL BE THE BAND. `asset_scale.BANDS[class]` and
     `MIN_DEPTH_RATIO[class]` are compared against what the sidecar recorded, so
     narrowing a band later re-opens every ingest that passed under the old one.

  5. FAIL CLOSED, AND SAY WHICH KIND OF FAILURE. Missing sidecar, missing file,
     unknown class, a sidecar written for a different file, and COULD-NOT-MEASURE
     are five different violations with five different sentences. "Could not
     look" must never print like "looked and it was fine" (R11).

WHAT IT DOES NOT DO, said plainly so a green line is not over-read. It answers
"is this the model we think it is, at the size we recorded". It does NOT answer
"is this model the right size for the slot it dresses" — a duvet can be honestly
1599.9 mm and still be too small for this bed, which is precisely what happened.
That question needs the slot, and it is `covers_mm` below: declared per reference,
checked only where declared, and absent everywhere else rather than guessed.

LAYER LAW: pure Python, no `bpy` (it is called from a gate, and from inside the
Blender build via rule_gate, which must stay importable in both).
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_scale as A                                      # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

SPEC_KEY = "model_assertions"

# A requirement is attached to a SITE, not to a model — so it outlives whatever
# model currently fills the site, and an EMPTY site keeps printing. That is the
# whole point: `covers` was written for the bed cloth, the bed cloth was then
# refused and removed, and a rule that lived on the removed row would have gone
# with it. A rule with no reader is this repo's oldest defect; a rule that
# reports UNFILLED every build is a declared gap.
REQ_KEY = "model_requirements"

# The two shelves, in the order `build_room._model_path` searches them. Keeping
# the order identical is not cosmetic: if the same slug existed on both, the gate
# must measure the file the build will actually load.
SHELVES = (("assets", "shared", "cc0", "models"),
           ("assets", "shared", "warehouse"))

# A key that HOLDS a model reference. `*_note` is excluded first and by name,
# because the note is exactly where the number used to live and must never be
# read as data again.
_MODEL_KEY = re.compile(r"^(model|.+_model|.+_models)$")
_NOTE_KEY = re.compile(r"_note$")

# Both stored to 0.1 mm by asset_scale, so anything above half a tenth is a real
# disagreement rather than a rounding artefact.
TOL_MM = 0.1

REQUIRED = ("class", "axis", "asserted_mm")


# ------------------------------------------------------------------ discovery --

def resolve(slug, repo_root=None):
    """The cached .glb/.gltf a slug names, or None. Mirrors build_room._model_path
    — the ONE door external geometry comes through — deliberately, so the gate
    measures the same bytes the build imports."""
    if not isinstance(slug, str) or not slug or os.sep in slug or "/" in slug:
        return None
    root = repo_root or REPO_ROOT
    for shelf in SHELVES:
        d = os.path.join(root, *shelf, slug)
        for pat in ("*.gltf", "*.glb"):
            hits = sorted(glob.glob(os.path.join(d, pat)))
            if hits:
                return hits[0]
    return None


def discover(spec, repo_root=None):
    """[(site, slug)] — every model reference in the spec, by BOTH detectors.

    `site` is a dotted path into the spec so a violation names where to go. The
    same slug may appear at several sites (a garment set is listed twice: once in
    `garment_models`, once in `garment_cut_first`); every site is reported and
    the row is shared, because the ROW is about the file.
    """
    out = []
    seen = set()

    def add(site, val):
        if isinstance(val, str) and (site, val) not in seen:
            seen.add((site, val))
            out.append((site, val))

    def walk(node, site, under_model_key):
        if isinstance(node, dict):
            for k, v in node.items():
                if _NOTE_KEY.search(str(k)):
                    continue                     # prose: rationale, never data
                if str(k) == SPEC_KEY:
                    continue                     # the assertions block itself
                # THE FLAG PROPAGATES DOWN THE WHOLE SUBTREE, and a test caught
                # the version that did not: `bed_models` holds {"cloth_set":
                # "<slug>"}, so a flag reset at each level meant the slug was
                # only ever found by the VALUE detector — i.e. only while the
                # file existed. Delete the asset and the reference silently left
                # scope, which is the failure this whole module is about. The
                # cost is that non-slug metadata under a model key would be
                # reported as a missing model; that is the loud direction, and
                # rationale belongs in a `*_note` key anyway.
                walk(v, f"{site}.{k}" if site else str(k),
                     under_model_key or bool(_MODEL_KEY.match(str(k))))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{site}[{i}]", under_model_key)
        elif isinstance(node, str):
            # (a) key shape — a `model`/`*_models` key holds references whatever
            # its value looks like, so a slug that has been DELETED off the shelf
            # is still discovered, and reported as absent rather than skipped.
            # (b) value shape — anything that resolves is a reference no matter
            # what the key is called.
            if under_model_key or resolve(node, repo_root):
                add(site, node)

    walk(spec, "", False)
    return out


def requirements_of(spec):
    """{site: requirement}. A requirement says what ANY model at that site has to
    be, whether or not one is there today."""
    blk = spec.get(REQ_KEY)
    if not isinstance(blk, dict):
        return {}
    return {k: v for k, v in blk.items()
            if isinstance(v, dict) and not str(k).startswith("_")}


def apply_requirements(row, sites, reqs):
    """(effective_row, violations). A requirement OVERRIDES nothing and ADDS
    everything: a row may not opt out of the site's rule by omitting a key, and
    it may not contradict it either — a row declaring a different class from the
    one the site requires is refused rather than silently preferred."""
    v = []
    out = dict(row)
    for s in sites:
        req = reqs.get(s)
        if not req:
            continue
        for k, want in req.items():
            if k in ("why", "note") or str(k).startswith("_"):
                continue
            have = out.get(k)
            if have is None:
                out[k] = want
            elif have != want:
                v.append(f"the site `{s}` REQUIRES {k}={want!r} and this row "
                         f"declares {k}={have!r}. The requirement is the site's, "
                         f"not the asset's — an asset that does not meet it is "
                         f"the wrong asset for the job.")
    return out, v


def rows_of(spec):
    """The declared assertions, {slug: row}. Never raises on a malformed block —
    a gate reports, it does not traceback."""
    blk = spec.get(SPEC_KEY)
    if not isinstance(blk, dict):
        return None
    return {k: v for k, v in blk.items()
            if isinstance(v, dict) and not str(k).startswith("_")}


# --------------------------------------------------------------------- checks --

def _sidecar_path(model_path):
    return os.path.splitext(model_path)[0] + ".scale.json"


_ITEM_SITE = re.compile(r"^items\[(\d+)\]")


def covers_need(spec, row, sites):
    """((w_mm, d_mm), violations) — the plan this model must COVER to do its job,
    or (None, violations) where the row declares nothing.

    DERIVED, NEVER TYPED (R9). `covers: {"item": 1, "inset_mm": 90}` reads the
    bed's own w/d out of the spec, so re-drawing the bed re-aims the requirement
    and no second copy of its size exists to drift. `inset_mm` is the one number
    the spec must carry, and it is a build constant with a citation
    (build_room.py mattress inset), not a measurement.

    It also checks the row points at the item it is DRESSING: a `covers` aimed at
    the wrong item would silently test the cloth against a nightstand.
    """
    v = []
    c = row.get("covers")
    if c is None:
        cm = row.get("covers_mm")
        if cm is None:
            return None, v
        try:
            return (float(cm[0]), float(cm[1])), v
        except (TypeError, ValueError, IndexError):
            return None, [f"covers_mm={cm!r} is not two numbers"]
    if not isinstance(c, dict) or "item" in c and not isinstance(c["item"], int):
        return None, [f"`covers` must be {{\"item\": <index>, \"inset_mm\": <mm>}}, "
                      f"got {c!r}"]
    items = spec.get("items") or []
    i = c.get("item")
    if not isinstance(i, int) or not (0 <= i < len(items)):
        return None, [f"`covers.item` = {i!r} is not an index into this spec's "
                      f"{len(items)} items"]
    named = {int(m.group(1)) for m in
             (_ITEM_SITE.match(s) for s in sites) if m}
    if named and i not in named:
        v.append(f"`covers.item` = {i} but this model is referenced from "
                 f"item(s) {sorted(named)}. A coverage requirement aimed at a "
                 f"different object measures nothing.")
    it = items[i]
    try:
        ins = float(c.get("inset_mm") or 0.0)
        return (float(it["w"]) - 2 * ins, float(it["d"]) - 2 * ins), v
    except (TypeError, ValueError, KeyError) as e:
        return None, v + [f"`covers.item` = {i} has no usable w/d ({e})"]


def verify(spec, slug, row, sites, repo_root=None):
    """(violations, line) for ONE reference. `line` is the one-line report that
    prints on every build — present even when the reference is broken, because a
    reference that vanishes from the printout is how this class of defect hides."""
    v = []
    where = ", ".join(sites)
    cls = row.get("class")
    axis = row.get("axis")
    val = row.get("asserted_mm")
    short = slug if len(slug) <= 12 else slug[:11] + "…"

    missing = [k for k in REQUIRED if row.get(k) in (None, "")]
    if missing:
        v.append(f"{SPEC_KEY}['{slug}'] is missing {', '.join(missing)}. An "
                 f"assertion with no number is the prose note again, in JSON.")
        return v, f"  MODEL ASSERT {short:<12} {where}  !! INCOMPLETE ROW"

    if not isinstance(val, (int, float)):
        v.append(f"{SPEC_KEY}['{slug}'].asserted_mm is {val!r}, not a number. "
                 f"The whole point of this field is that a program can diff it.")
        return v, f"  MODEL ASSERT {short:<12} {where}  !! asserted_mm not numeric"

    band = A.BANDS.get(cls)
    if band is None:
        v.append(f"{SPEC_KEY}['{slug}'] declares class '{cls}', which has no "
                 f"band in asset_scale.BANDS. An unknown class must not pass — "
                 f"'no band' and 'in band' reading alike is how an unasserted "
                 f"ingest gets called asserted.")
        return v, (f"  MODEL ASSERT {short:<12} {where}  !! unknown class "
                   f"'{cls}'")

    mp = resolve(slug, repo_root)
    if not mp:
        v.append(f"{SPEC_KEY}['{slug}'] names a model that is on neither shelf "
                 f"(cc0/models, warehouse). The spec asserts a size for a file "
                 f"that is not there; the build will fall back and this row "
                 f"will keep asserting.")
        return v, f"  MODEL ASSERT {short:<12} {where}  !! NO FILE ON EITHER SHELF"

    scp = _sidecar_path(mp)
    try:
        with open(scp, encoding="utf-8") as f:
            sc = json.load(f)
    except (OSError, ValueError) as e:
        v.append(f"{slug}: no readable scale sidecar beside {os.path.basename(mp)} "
                 f"({e}). pipeline/CLAUDE.md carries the assertion as a MUST — "
                 f"no external geometry reaches a spec until its unit is "
                 f"RESOLVED and asserted, never assumed.")
        return v, (f"  MODEL ASSERT {short:<12} {where}  !! NO SIDECAR "
                   f"({os.path.basename(mp)})")

    # The sidecar must be about THIS file. The p2r36 defect one level down: a
    # sidecar copied or left behind from another candidate reads perfectly.
    if str(sc.get("file")) != os.path.basename(mp):
        v.append(f"{slug}: the sidecar describes '{sc.get('file')}' but the "
                 f"build will load '{os.path.basename(mp)}'. A measurement of a "
                 f"different file is not a measurement of this one.")

    if sc.get("class") != cls:
        v.append(f"{slug}: the spec asserts class '{cls}', the sidecar was "
                 f"written for class '{sc.get('class')}'. Re-ingest with the "
                 f"class the spec means (asset_scale.py <file> <class>).")
    if sc.get("axis") != axis:
        v.append(f"{slug}: the spec asserts axis '{axis}', the sidecar measured "
                 f"'{sc.get('axis')}'. The axis is part of the claim — a class "
                 f"is diagnosed on the dimension its band names.")
    if not sc.get("ok"):
        v.append(f"{slug}: the sidecar says ok={sc.get('ok')} — this asset was "
                 f"REFUSED at ingest"
                 + (f" ({sc.get('planar_refusal')})" if sc.get("planar_refusal")
                    else "")
                 + ". A refused asset may not be referenced by the spec.")

    sm = sc.get("measured_mm")
    if not isinstance(sm, (int, float)) or abs(sm - val) > TOL_MM:
        v.append(f"{slug}: the spec asserts {val} mm on {axis}, the file's own "
                 f"sidecar reads {sm} mm. THIS IS THE p2r36 DEFECT — the number "
                 f"in the spec belonged to a different asset. The sidecar is "
                 f"measured from the file and wins; correct the spec.")

    # BAND STALENESS. If a band is narrowed after an ingest, the ingest has to be
    # re-run — otherwise the assertion is against a rule nobody enforces now.
    if list(sc.get("band_mm") or []) != [band[0], band[1]]:
        v.append(f"{slug}: the sidecar was asserted against band "
                 f"{sc.get('band_mm')} but class '{cls}' now reads "
                 f"[{band[0]}, {band[1]}]. Re-assert this ingest against the "
                 f"band in force.")
    if sc.get("min_ratio_for_class") != A.MIN_DEPTH_RATIO.get(cls):
        v.append(f"{slug}: the sidecar's planar floor "
                 f"({sc.get('min_ratio_for_class')}) is not the floor class "
                 f"'{cls}' carries now ({A.MIN_DEPTH_RATIO.get(cls)}). "
                 f"Re-assert.")

    # THE LIVE LEG. A sidecar is a claim about a file; this re-opens the file.
    live_txt = ""
    try:
        b = A.bounds_mm(mp)
    except (OSError, ValueError, KeyError, IndexError) as e:
        v.append(f"{slug}: COULD NOT MEASURE {os.path.basename(mp)} now ({e}). "
                 f"This is not a pass — an assertion that cannot be reproduced "
                 f"is not an assertion. Re-export the asset with accessor "
                 f"min/max, or drop the reference.")
        live_txt = " live=COULD-NOT-MEASURE"
    else:
        lv = (max(b["x_mm"], b["y_mm"]) if axis == "maxxy"
              else b.get(f"{axis}_mm"))
        live_txt = f" live={lv:.1f}" if isinstance(lv, float) else " live=?"
        if not isinstance(lv, float):
            v.append(f"{slug}: axis '{axis}' is not one of x/y/z/maxxy, so "
                     f"nothing could be re-measured.")
        elif abs(lv - val) > TOL_MM:
            v.append(f"{slug}: the spec asserts {val} mm on {axis}; re-measuring "
                     f"{os.path.basename(mp)} RIGHT NOW gives {lv:.1f} mm. The "
                     f"file under this slug is not the file that was asserted.")
        if isinstance(sc.get("prims"), int) and sc["prims"] != b["prims"]:
            v.append(f"{slug}: the sidecar recorded {sc['prims']} primitive(s), "
                     f"the file now holds {b['prims']}. Same slug, different "
                     f"asset — which is exactly how a rejected candidate's "
                     f"numbers ended up describing the chosen one.")

        # DECLARED-ONLY, never inferred: what this model has to COVER to do its
        # job. Absent for most references, and absent is silent. Where it IS
        # declared, it answers the question a band structurally cannot: a duvet
        # can be honestly 1599.9 mm and still be too small for this bed. That is
        # not a hypothetical — it is what the owner saw on p2r36 with every
        # instrument green, because "in band" and "big enough for THIS bed" are
        # different questions and only the first one had a reader.
        need, cv = covers_need(spec, row, sites)
        v += [f"{slug}: {s}" for s in cv]
        if need:
            # The mesh may be laid out either way round; place_model applies ONE
            # uniform scale, so the honest test is the best of the two
            # orientations at a single scale.
            have = sorted((b["x_mm"], b["y_mm"]))
            want = sorted(need)
            s = max(want[0] / max(have[0], 1e-9), want[1] / max(have[1], 1e-9))
            cap = row.get("max_scale")
            cap = float(cap) if isinstance(cap, (int, float)) else 1.0
            if s > cap + 1e-9:
                v.append(
                    f"{slug}: to cover {want[0]:.0f} x {want[1]:.0f} mm this "
                    f"{have[0]:.0f} x {have[1]:.0f} mm asset must be scaled "
                    f"{s:.3f}x, past the declared ceiling of {cap:.3f}x. It is "
                    f"the right UNIT and the wrong SIZE — acquire one that is "
                    f"already big enough, because stretching a mesh to fit is "
                    f"the 'plausible-but-wrong-scale model' this whole law "
                    f"exists to refuse.")

    band_txt = f"band {band[0]:g}-{band[1]:g}"
    line = (f"  MODEL ASSERT {short:<12} {cls:<19} {axis}={val:<8.1f} "
            f"sidecar={sm if isinstance(sm, (int, float)) else '?'}"
            f"{live_txt}  {band_txt}  <- {where}")
    return v, line


def check(spec, repo_root=None, extra=()):
    """(violations, lines). `extra` = [(site, slug)] the CALLER knows it can
    consume but the spec does not name — a hard-coded decor slug, a kind->slug
    default map. They are checked exactly like a spec reference, because the
    file gets imported exactly the same way."""
    root = repo_root or REPO_ROOT
    refs = list(discover(spec, root)) + [(s, g) for s, g in extra]
    by_slug = {}
    for site, slug in refs:
        by_slug.setdefault(slug, []).append(site)

    rows = rows_of(spec)
    if rows is None and by_slug:
        return ([f"this spec references {len(by_slug)} model(s)"
                 f"({', '.join(sorted(by_slug)[:4])}…) and carries no "
                 f"`{SPEC_KEY}` block. P2r-9: a size kept in prose is not data. "
                 f"Add one row per model with class / axis / asserted_mm."],
                [f"  MODEL ASSERT {s:<12} !! NO `{SPEC_KEY}` BLOCK"
                 for s in sorted(by_slug)])
    # No block AND no references is not an error — but the requirement sites
    # below still have to report, and the first cut of this function returned
    # here before they could. A spec that declares what a site must hold and
    # holds nothing yet is the exact state this lane is in after removing a
    # refused asset; going quiet about it would have retired the rule silently.
    rows = rows or {}

    reqs = requirements_of(spec)
    filled = {s for sites in by_slug.values() for s in sites}
    v, lines = [], []
    for slug in sorted(by_slug):
        sites = by_slug[slug]
        row = rows.get(slug)
        if row is not None:
            row, rq = apply_requirements(row, sites, reqs)
            v += [f"{slug}: {s}" for s in rq]
        if row is None:
            v.append(f"{', '.join(sites)} references model '{slug}' with no row "
                     f"in `{SPEC_KEY}`. Every model reference asserts its own "
                     f"size, or the size lives in prose again.")
            lines.append(f"  MODEL ASSERT {slug[:11]:<12} {', '.join(sites)}  "
                         f"!! NO ASSERTION ROW")
            continue
        rv, line = verify(spec, slug, row, sites, root)
        v += rv
        lines.append(line)

    # UNFILLED SITES. Reported, never a violation: an acquisition that has not
    # happened yet is a declared gap, and R10 says the absent thing is honest
    # while the wrong thing fabricates a reading. What it must NOT do is go
    # quiet — the requirement outlives the asset precisely so the next pick is
    # filtered before anything is rendered.
    for site in sorted(set(reqs) - filled):
        r = reqs[site]
        lines.append(f"  MODEL ASSERT {'(unfilled)':<12} {site} — NO MODEL YET; "
                     f"any pick must be class '{r.get('class')}'"
                     + (f", covering item {r['covers'].get('item')}"
                        if isinstance(r.get("covers"), dict) else "")
                     + (f" at scale <= {r['max_scale']}"
                        if r.get("max_scale") is not None else ""))

    # ORPHANS. The p2r36 shape, made impossible: a row for an asset nothing
    # points at is a measurement of a candidate we did not choose, sitting in the
    # file waiting to be read as if it described the one we did.
    for slug in sorted(set(rows) - set(by_slug)):
        v.append(f"`{SPEC_KEY}['{slug}']` asserts a size for a model no "
                 f"reference in this spec points at. Delete the row with the "
                 f"reference — an orphan assertion is how a REJECTED "
                 f"candidate's numbers came to describe the chosen one.")
        lines.append(f"  MODEL ASSERT {slug[:11]:<12} !! ORPHAN ROW (nothing "
                     f"references it)")
    if not lines:
        lines = ["  MODEL ASSERT: no model references in this spec"]
    return v, lines


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Diff every model size the spec asserts against the file's "
                    "own sidecar and a live re-measure. Exits 1 on a mismatch.")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--repo-root", default=None)
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    v, lines = check(spec, a.repo_root)
    for ln in lines:
        print(ln)
    for s in v:
        print(f"  !! {s}")
    print(f"MODEL ASSERT: {len(lines)} reference(s), {len(v)} violation(s)")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
