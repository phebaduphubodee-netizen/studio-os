#!/usr/bin/env python3
"""debt_seed.py — cut `qa/critic-debt.json` from the critic corpus. PURE stdlib.

CLI-ONLY: run by hand, once per corpus. It SEEDS the ledger; `debt_check.py` is
the rung that runs in a path. Re-running it is how the recurrence numbers in the
ledger stay reproducible instead of being twenty figures somebody typed.

    python pipeline/scripts/debt_seed.py --census <census.json> [--top 21]
    python pipeline/scripts/debt_seed.py --census <census.json> --write

WHY THE RANKING IS A PROGRAM AND THE DOORS ARE NOT
---------------------------------------------------
Two halves, and they are deliberately different kinds of thing:

  CLASSES  MECHANICAL. Keyword rules over 367 filed items from 28 critic answer
           files. Multi-label on purpose — "the throw is rigid" and "the throw is
           glossy vinyl" are two different fixes and one sentence carries both.
           Recurrence is the number of FILES a class appears in, never the number
           of items, because one critic listing a defect three ways is one critic.
           1.1% of items match no class, and that residue prints.

  DOORS    AUTHORED. Which instrument can see a defect is a judgement, and
           pretending a regex made it would be the flattering move. Each door
           below carries the reason it was chosen, and nine of the twenty-one
           carry `none_yet` because NO instrument in this repo can see them.
           That number is the finding, not an embarrassment.

THE CORPUS LIVES UNDER `_private/` and stays there — it is this lane's own critic
answers about its own frames, and the census JSON is extraction output, not
domain truth. The ledger it writes carries only our own defect descriptions, no
target measurements and no client imagery, which is what makes the LEDGER
committable while the corpus is not.

RECONCILED AGAINST THE PLAN'S EARLIER FIGURES, because they differ and the
difference is informative:
  * cloth stiffness 28/28 — reproduces exactly.
  * "flat light 26/28" — reproduces exactly as the UNION of `flat-light` (20/28)
    and `no-contact-shadow` (25/28). The earlier pass lumped them; they are split
    here because they have different fixes (key direction and exposure vs contact
    occlusion), and a row whose fix is two fixes is the defect R9 calls one
    parameter carrying two things.
  * "faceting 26/28" does NOT reproduce. The tight class measures 19/28. The
    earlier figure was a looser grouping that swept in plastic-material reads
    (`faceted` + `one-white-material` + `no-surface-texture` reaches 28/28). The
    tight number is the one recorded, because a debt row has to name one fix.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER_REL = "qa/critic-debt.json"

# ---------------------------------------------------------------- the classes --
# (id, one-line defect, object regex, label regex). Both must match.
CLASSES = [
    ("cloth-rigid", "soft goods read rigid — no drape, compression or sag",
     r"(bedding|bedspread|pillow|duvet|throw|blanket|runner|linen|cloth|sham|"
     r"fur|satin|textile|bolster|cushion|sheet)",
     r"(stiff|rigid|slab|block|no drape|drape|compress|wrinkle|sag|fold|carved|"
     r"foam|board|plastic|vinyl|latex|foil|paper|frozen|weightless|lifeless|"
     r"crumple|physics|hard|sculpted|plaster|cardstock|card\b|tidy|loft|"
     r"razor|plane|puddle|hem|cotton wool|blob|ragged|lumpy|behave like cloth|"
     r"stitch|weave|seam|no fibre|strap|ribbon)"),
    ("no-contact-shadow", "nothing casts a contact shadow; every object floats",
     r".", r"(contact shadow|no shadow|shadows? (absent|missing)|float|hover|"
             r"pasted on|weightless|no floor shadow|casts no floor)"),
    ("empty-frame", "the picture frame holds no art",
     r"(picture|frame|art)",
     r"(empty|blank|placeholder|no art|unfinished|contains nothing)"),
    ("wood-texture", "wood reads as a decal — grain tiles, repeats, wrong scale",
     r"(wood|timber|grain|parquet|floor|herringbone|joinery|oak)",
     r"(tile|repeat|sticker|decal|pasted|printed|flat|no specular|scale|"
     r"stretched|wraps|no plank|no bevel|no joint|sheenless|no reflection|"
     r"uniformly bright)"),
    ("flat-light", "light is flat and directionless — no key, no falloff",
     r".", r"(flat( |-)?(light|lighting)|lighting (is )?flat|no key light|"
             r"shadowless|over(ly)?.?diffuse|too diffuse|even ambient|"
             r"directionless|no light direction|no visible light source|"
             r"no window|no daylight|filled to the same brightness|"
             r"uniform, shadows)"),
    ("styling-zero", "styling density near zero — no books, lamps, plants, trays",
     r".", r"(styling|unstyled|under.?styled|under.?dressed|undressed|no props|"
             r"empty of|bare|no lamp|no books|no plant|no curtain|lifeless|"
             r"lacks styling|no personal object|nothing prov|room empty|"
             r"no objects|no cushion|surfaces (all )?empty|shelves.*empty)"),
    ("faceted", "curved forms render faceted / low-poly, edges never eased",
     r".", r"(facet|low.?poly|polygon|unrounded|not eased|no bevel|no chamfer|"
             r"razor.?sharp|sharp edge|knife.?edge|oversimplified|primitive|"
             r"blocky|flat strips|capsule|extruded|inflated)"),
    ("seat-impossible", "the stool / chair / bench cannot stand as built",
     r"(stool|chair|bench|seat|footstool|pouf|vanity)",
     r"(primitive|placeholder|toilet|capsule|too small|too thin|too low|"
     r"frail|undersized|legs|shapeless|lump|overhang|featureless|"
     r"no seat|spindly|detached|miss the seat|stop short|proportion|"
     r"interpenetrat)"),
    ("one-white-material", "every surface is one white value — no material story",
     r".", r"(same (matte|white|off.?white|value|reflectance)|one white|"
             r"one (matte|value|reflectance)|no material separation|"
             r"no tonal hierarchy|share one|shares one|monochrome|"
             r"same material|clay|no material identity|read as default|"
             r"no differentiation|dissolve together|identically)"),
    ("joinery-hardware", "joinery has no handles, reveals, plinth or track",
     r"(wardrobe|joinery|door|cupboard|closet|rail|band)",
     r"(no handle|no pull|no hinge|no reveal|no plinth|no track|no hardware|"
     r"hairline|painted.?on|painted lines|zero.?depth|blank|no groove|"
     r"no backplate|no architrave|no jamb|floating handle|no bezel|"
     r"without handle|lacks (handle|shadow gap)|handle (reads|too|mounted)|"
     r"basic to read|one.?sided reveal|shadow gap|flush)"),
    ("unidentifiable-mass", "a mass in frame cannot be named as any object",
     r".", r"(unidentif|cannot be identified|cannot be named|unnameable|"
             r"no identifiable|unreadable|no readable identity|"
             r"resolves? (as|into) no|do not resolve|unexplained|unknown|"
             r"no identity|purposeless|no identifying|reads as nothing|"
             r"resolve as neither|neither .* nor|orphan|no identifiable "
             r"function|featureless|no readable function)"),
    ("glass-dead", "glazing is opaque or reflects nothing",
     r"(glass|glaz|sliding|partition|mirror|frosted)",
     r"(opaque|no reflection|reflects nothing|flat (opaque |grey )?|"
     r"lightbox|blown|transmits nothing|inconsistent|differ|"
     r"corresponding to nothing|no gradient|no detail|shows nothing|"
     r"glass response|zero reflection)"),
    ("headboard", "the headboard is absent, leaning, floating or implausible",
     r"(headboard|bed head)", r"."),
    ("rug-decal", "the rug is a zero-thickness decal — no pile, no compression",
     r"(rug|carpet)", r"."),
    ("downlights-dead", "modelled downlights emit no pool, scallop or falloff",
     r"(downlight|ceiling|fixture|light)",
     r"(emit no|emit nothing|no pool|no scallop|cast no|glow on the ceiling|"
     r"glow around|flat bright patch|no aperture|emits? but cast)"),
    ("camera", "wide lens: verticals converge, foreground objects crop",
     r".", r"(vertical|keystone|wide lens|too wide|lens|crop|skew|shear|"
             r"converge|rake|pitched|shows almost none|hidden by foreground)"),
    ("no-bedside", "no bedside surface, nightstand or reading light beside the bed",
     r"(nightstand|bedside|lamp|side table)",
     r"(no nightstand|no bedside|no lamp|no reading|bare|empty|unreachable|"
     r"do not resolve|above and behind)"),
    ("bed-monolith", "bed base / plinth reads as one carved podium, not a made bed",
     r"(bed|plinth|platform|base|mattress)",
     r"(monolith|one (carved |white )?(mass|block|foam)|podium|bathtub|planter|"
     r"merge|fuse|sanitaryware|extruded block|oversized|too thick|"
     r"one carved|square extruded|two.?tier|multi.?tier)"),
    ("cantilever-unsupported", "a slab cantilevers and ends unsupported in mid-air",
     r".", r"(cantilever|unsupported|ends? (in )?mid.?air|no visible support|"
             r"terminates? in mid.?air|floats? (clear|without)|"
             r"impossibly thick|over.?thick|no support|frozen midair|"
             r"stacked with no|butt.?joint|no return|disagree in height)"),
    ("junction-raw", "wall/floor/ceiling junctions are knife edges — no skirting",
     r"(junction|skirting|cornice|wall|ceiling|arris)",
     r"(no skirting|knife|sharp line|no shadow gap|no cornice|bare sharp|"
     r"die straight|no corner darkening|soft and rounded)"),
    ("no-surface-texture", "surfaces carry no imperfection — no paint texture, no weave",
     r".", r"(unnaturally smooth|too smooth|too perfect|no paint|no weave|"
             r"no imperfection|textureless|no fibre|no bump|"
             r"lack(s)? specular|no specularity|sheenless|no grain)"),
    ("window-blown", "the window is a blown white hole with no frame, sill or reveal",
     r"(window|blind|glaz)",
     r"(blown|white hole|no frame|no sill|no reveal|no view|sliver|ragged|"
     r"clipped|blown.?out|no curtain)"),
    ("no-functional-detail", "no switches, sockets, curtain track or services",
     r".", r"(switch|socket|air.?conditioning|curtain track|services)"),
    ("blocks-function", "an object blocks a door, drawer or circulation route",
     r".", r"(block(s|ing)? (a )?(door|the sliding|drawer)|parked (hard )?"
             r"(against|square in)|blocking doors|door.?s? (opening )?path|"
             r"unopenable|cannot open|in the doorway|blocks it)"),
    ("panel-decal", "a wall panel / TV / artwork reads as a flat card with no depth",
     r"(tv|panel|artwork|picture|frame|slab|rectangle|band|monolith)",
     r"(flat (card|graphic|chamfered|decal)|no depth|no bezel|matte black void|"
     r"decal|black card|no fixings|no plate|no mount|no cable|"
     r"no screen reflection)"),
    ("downlight-setout", "downlight set-out relates to no datum in the room",
     r"(downlight|ceiling)",
     r"(layout|set.?out|scattered|irregular|unaligned|unrelated|no grid|"
     r"too many)"),
    ("joinery-setout", "joinery panel widths align with nothing — sliver leaves",
     r"(wardrobe|joinery|panel|bay|leaf|door)",
     r"(width|sliver|unequal|arbitrar|align with nothing|aligns with neither|"
     r"set.?out|100mm|terminates bluntly|wrong)"),
    ("value-range", "value range collapsed — no dark anchor in the frame",
     r".", r"(no dark|dark value anchor|value range collapsed|no true black|"
             r"no silhouette|palette all|monochrome|no dark anchor)"),
    ("wood-tone-clash", "unrelated timber tones read as three different libraries",
     r"(wood|timber|oak|parquet|floor|joinery|grain)",
     r"(three|unrelated|clashing|different libraries|two clashing|species|"
     r"third value)"),
]

# ------------------------------------------------------------------ the doors --
# AUTHORED. class id -> (due_phase, closes_when, why this door and not another).
DOORS = {
    "cloth-rigid": ("P2",
        {"door": "scene_row", "row": "D8"},
        "D8 counts R8-ACQUIRE-class masses built as primitives, and its word list "
        "IS this defect's object list: pillow, cushion, bolster, sham, duvet, "
        "throw, blanket. r38 scores 7 against a threshold of 0."),
    "no-contact-shadow": ("P3",
        {"door": "none_yet", "blocked_on":
            "a LOCALISED contact-luminance probe at floor junctions. D6 measures "
            "the share of the whole frame below L=26, which a black TV screen "
            "satisfies while every object still floats — binding this row to D6 "
            "would be the tenth flattering scorer."},
        "The second most recurring defect in the corpus has no instrument. Saying "
        "so is the point of the door."),
    "empty-frame": ("P4",
        {"door": "none_yet", "blocked_on":
            "a material-side check that art / mirror / screen masses carry an "
            "image map. D7 already counts `artwork` and `art_mat` as styling "
            "objects, so the instrument we have is inflated BY this defect."},
        "Filed in 23 of 28 files and the only instrument that touches it counts "
        "the empty frame as a point in our favour."),
    "wood-texture": ("P2",
        {"door": "none_yet", "blocked_on":
            "a texture-map COVERAGE measure of our own scene — the share of "
            "materials carrying image maps, against the 50-66% measured in five "
            "production .blend files (blender-ground-truth-study-2026-07-30, our "
            "own file, 4.9% for us). texture_check.py cannot serve: it compares "
            "against a reference frame and DELIV-001 has no target."},
        "SC-4 ranks this the strongest measured realism lever in the plan, and "
        "nothing in the repo can score it without a target image."),
    "flat-light": ("P3",
        {"door": "image_row", "row": "D3"},
        "Flat light IS a compressed range: D3 is p1->p99 in stops, cut at the "
        "25th percentile of 658 delivered frames. P3's whole thesis (SC-4) is "
        "that the defect is RANGE, not lamp count."),
    "styling-zero": ("P4",
        {"door": "scene_row", "row": "D7"},
        ">=12 loose styling objects, counted from names. r38 scores 6. Reported "
        "and not scored in the standard until procurement closes the shortfall of "
        "8 — but a debt row does not need the standard's permission to be owed."),
    "faceted": ("P2",
        {"door": "scene_row", "row": "D9"},
        "D9 counts curved masses that no beauty.soft entry smooths. r38 scores "
        "16, and `beauty` is null in all ten specs r28-r38, so the softening code "
        "is dead in every shipping frame."),
    "seat-impossible": ("P2",
        {"door": "guard", "module": "placement_check", "verdict": "FLOATING",
         "match": "chair",
         "covers": "whether the seat and every leg are held up by something in "
                   "the built scene. NOT covered: proportion (legs too thin for "
                   "the seat), whether it reads as designed furniture, or whether "
                   "it is parked in a door's swing."},
        "'Legs stop short of the seat' and 'legs end at different heights' are "
        "placement_check's FLOATING verdict, which has been able to say so since "
        "2026-08-02 and was never asked."),
    "one-white-material": ("P2",
        {"door": "image_row", "row": "D10"},
        "D10 was cut for exactly this: a sighted judge named an amber-monochrome "
        "cast on our best frame and no other row could see it."),
    "joinery-hardware": ("P2",
        {"door": "object", "match": "pull", "min_count": 2,
         "covers": "whether joinery PULLS exist as drawable masses in the built "
                   "scene. NOT covered: reveals, plinths, hinges and track, which "
                   "are the rest of the same filed defect and have no door."},
        "An absence, so it resolves the way R10 says: point at the object in the "
        "BUILT scene or it is not there. THE FIRST MATCH WAS WRONG AND IT READ "
        "GREEN: `match: \"handle\"` with min_count 1 was already satisfied by "
        "`door_handle`, the ENTRANCE door's lever, which is in every TRN-002 spec "
        "and dump — so a row filed 16 times about a wardrobe with no hardware "
        "resolved against a mass nobody built for it, and the reason recorded "
        "here read 'no mass named handle/pull exists', which was false. A "
        "substring match is a door onto whatever happens to share a syllable."),
    "unidentifiable-mass": ("P2",
        {"door": "none_yet", "blocked_on":
            "a program for R10's identity test. rule_gate.audit_spec reads each "
            "mass's `prov` TAG, and the tags were honest even for lamp_stem — "
            "whose provenance literally read 'carries shade'. A tag cannot say "
            "whether the thing deserves to exist."},
        "R10 is the newest rule in CLAUDE.md and it is enforced by the owner's "
        "eye alone."),
    "glass-dead": ("P2",
        {"door": "none_yet", "blocked_on":
            "a material-side assertion that masses tagged as glazing carry "
            "transmission > 0 and roughness < 1 — trn002_materials has the "
            "channels, no rule reads them."},
        "Programmable and not programmed; the blocked_on is one commit of work."),
    "headboard": ("P2",
        {"door": "guard", "module": "placement_check", "verdict": "FLOATING",
         "match": "headboard",
         "covers": "whether a mass named headboard exists in the built scene and "
                   "is supported. NOT covered: whether it is VISIBLE at the head "
                   "of the bed at a believable size — r38b's critic wrote 'no "
                   "headboard' about a frame whose dump contains one."},
        "'A detached leaning slab touching neither mattress nor wall' is FLOATING "
        "verbatim. r37 deleted the invented 176 mm headboard and r38b's critic "
        "then read the bed as having no headboard at all."),
    "rug-decal": ("P2",
        {"door": "none_yet", "blocked_on":
            "a thickness floor for floor-laid soft goods, read off the built AABB "
            "(8-20 mm is the real range). D8 counts the rug but cannot tell a "
            "zero-thickness plane from a woven pile."},
        "Cheap to build and it needs the dump, not the spec."),
    "downlights-dead": ("P3",
        {"door": "none_yet", "blocked_on":
            "a check that every emissive mass produces a measurable luminance "
            "pool BELOW it. trn002_lightcheck measures per-object spread against "
            "a target frame; DELIV-001 has none."},
        "Twelve files say the downlights are modelled and emit nothing."),
    "camera": ("P1",
        {"door": "none_yet", "blocked_on":
            "placement_dump writes no camera record, so two-point perspective "
            "(rot_x ~ 0) cannot be asserted against the BUILT scene — only "
            "against the spec, which is a declaration."},
        "The fix is four lines in placement_dump plus one rule, and it is named "
        "here so it stops being invisible."),
    "no-bedside": ("P4",
        {"door": "object", "match": "lamp", "min_count": 2,
         "covers": "whether bedside lamps exist as drawable masses. NOT covered: "
                   "whether they are BESIDE THE BED — the dump carries AABBs and "
                   "a proximity test against the bed would say so, and nothing "
                   "here asks. min_count is 2 because a bed has two sides."},
        "An absence with a functional consequence a client sees: a bed with no "
        "bedside lamp cannot be switched off from the bed."),
    "bed-monolith": ("P2",
        {"door": "none_yet", "blocked_on":
            "a value-separation measure between adjacent masses (base vs mattress "
            "vs rug). id_mask.py already returns per-object ids and no rule in "
            "this repo consumes them."},
        "Another instrument that exists, is green, and is in no path."),
    "cantilever-unsupported": ("P2",
        {"door": "guard", "module": "placement_check", "verdict": "OVERHANG",
         "covers": "any group whose AABB overhangs its supports past the guard's "
                   "tolerance. NOT covered: a slab that is genuinely supported "
                   "but reads impossibly thick, which is a proportion judgement "
                   "no AABB makes."},
        "OVERHANG is this defect's name in the guard that already reads the built "
        "scene. No `match`, because the defect is about ANY slab — naming the "
        "objects it applies to is what R9b says a rule must never do."),
    "junction-raw": ("P2",
        {"door": "object", "match": "skirt", "min_count": 4,
         "covers": "whether skirting masses exist and reach every wall — 4, "
                   "because one stub on one wall of four would otherwise close a "
                   "row about the whole room. NOT covered: cornice, shadow gaps, "
                   "or whether the skirting meets the floor."},
        "An absence: no mass named skirting exists in any TRN-002 spec. Nine "
        "files name the knife-edged wall/floor junction."),
    "no-surface-texture": ("P2",
        {"door": "image_row", "row": "D5"},
        "D5 is the band-limited 4-32 px octave, two-sided so noise cannot buy it "
        "— the closest thing in the standard to 'the surface has grain'."),
}

# class id -> (what it is about, which craft it belongs to). Grouping only; no
# rule keys off these, so they carry no load beyond making the ledger readable.
FACETS = {
    "cloth-rigid": ("soft goods", "geometry"),
    "no-contact-shadow": ("whole frame", "light"),
    "empty-frame": ("artwork", "styling"),
    "wood-texture": ("timber surfaces", "material"),
    "flat-light": ("whole frame", "light"),
    "styling-zero": ("whole frame", "styling"),
    "faceted": ("curved masses", "geometry"),
    "seat-impossible": ("chair / stool / bench", "geometry"),
    "one-white-material": ("whole frame", "material"),
    "joinery-hardware": ("wardrobe / joinery", "geometry"),
    "unidentifiable-mass": ("loose masses", "geometry"),
    "glass-dead": ("glazing / mirror", "material"),
    "headboard": ("headboard", "geometry"),
    "rug-decal": ("rug", "geometry"),
    "downlights-dead": ("downlights", "light"),
    "camera": ("camera", "composition"),
    "no-bedside": ("bedside", "styling"),
    "bed-monolith": ("bed base", "material"),
    "cantilever-unsupported": ("joinery slabs", "geometry"),
    "junction-raw": ("wall / floor junction", "geometry"),
    "no-surface-texture": ("whole frame", "material"),
}

TIE_NOTE = ("21 rows, not 20. `junction-raw` and `no-surface-texture` tie at 9/28 "
            "on the boundary, and dropping one on a coin flip would be the "
            "builder choosing which debt to forget. The plan said top-20; this is "
            "the deviation, recorded rather than quietly taken.")


def classify(label, obj):
    t = (label + " || " + obj).lower()
    return [cid for cid, _n, o, l in CLASSES
            if re.search(o, t) and re.search(l, t)]


def rank(census):
    """[(class_id, name, files_set)] by descending recurrence, plus the residue."""
    per, unassigned, total = defaultdict(set), [], 0
    files = census["files"]
    for f in files:
        key = f"{f['round']}/{f['critic']}"
        for it in f["items"]:
            total += 1
            hits = classify(it["label"], it["object"])
            if not hits:
                unassigned.append((key, it["object"], it["label"]))
            for c in hits:
                per[c].add(key)
    order = sorted(CLASSES, key=lambda c: (-len(per[c[0]]), c[0]))
    return ([(cid, name, per[cid]) for cid, name, _o, _l in order],
            unassigned, total, len(files))


def build(census, top=21):
    ranked, unassigned, total, n_files = rank(census)
    rows = []
    for i, (cid, name, fs) in enumerate(ranked[:top], start=1):
        if cid not in DOORS:
            raise SystemExit(f"class {cid} is in the top {top} and has no door. "
                             f"Assign one in DOORS — a seeded row with no door "
                             f"is the queue this ledger replaces.")
        due, door, why = DOORS[cid]
        obj, kind = FACETS[cid]
        rounds = sorted({k.split("/")[0] for k in fs})
        rows.append({
            "id": f"DEBT-{i:02d}",
            "class": cid,
            "defect": name,
            "object": obj,
            "kind": kind,
            "filed_in": "TRN-002",
            "recurrence": {"files": len(fs), "of": n_files,
                           "first_round": rounds[0], "last_round": rounds[-1]},
            "crosses_into": "DELIV-001",
            "due_phase": due,
            "closes_when": door,
            "_why_this_door": why,
            "status": "open",
        })
    return rows, unassigned, total, n_files, ranked


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--census", required=True)
    ap.add_argument("--top", type=int, default=21)
    ap.add_argument("--write", action="store_true",
                    help="write qa/critic-debt.json (merges doors over the cut)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                   # noqa: BLE001
        pass

    with open(a.census, encoding="utf-8") as f:
        census = json.load(f)
    rows, unassigned, total, n_files, ranked = build(census, a.top)

    print(f"{total} filed items across {n_files} critic answer files")
    print(f"{'class':26s} {'files':>7s}  door")
    for cid, name, fs in ranked:
        mark = "  " if cid in {r['class'] for r in rows} else "--"
        door = DOORS.get(cid, (None, {"door": "-"}, None))[1]["door"]
        print(f"{mark}{cid:24s} {len(fs):3d}/{n_files:<3d}  {door}")
    print(f"\nunassigned {len(unassigned)} of {total} "
          f"({100.0 * len(unassigned) / total:.1f}%)")
    n_blind = sum(1 for r in rows if r["closes_when"]["door"] == "none_yet")
    print(f"seeded {len(rows)} rows; {n_blind} of them have NO instrument that "
          f"can see the defect")

    if a.write:
        out = {
            "_what": "The critic-debt ledger. Every row is a defect independent "
                     "critics filed against this studio's own frames often enough "
                     "that it is one debt re-billed, not a new finding each round. "
                     "Read by pipeline/scripts/debt_check.py; cut by "
                     "pipeline/scripts/debt_seed.py.",
            "_law": [
                "An item closes only when its door resolves against something "
                "BUILT (a placement dump, a rendered frame), or it is refuted "
                "with a NUMBER. Never with a sentence.",
                "A row may change status. It may never leave this file — "
                "deleting it reproduces the 357-filed / 22-built defect exactly.",
                "A spec is a declaration. No row closes against a spec, and a "
                "scene row rises above DECLARED only when a placement dump "
                "corroborates that the spec describes something that was built.",
                "Only RESOLVED is a pass. PARTIAL means an instrument's half "
                "holds and the instrument is narrower than the defect that was "
                "filed — a guard door cannot close a row on its own. "
                "DECLARED-ONLY means we said so; NOT RUN means we did not look.",
                "Existence is judged on the DRAWABLE population — a MESH the "
                "renderer draws. Hiding a mass must never close its debt.",
                "`none_yet` is an honest verdict, not an exemption: it must name "
                "what would have to be built, and it may never be marked built "
                "or refuted while it says so.",
            ],
            "_seeded_from": {
                "corpus": "_private/benchmark/reproduction/TRN-002/renders/"
                          "critique/*/ANSWER_*.md",
                "answer_files": n_files,
                "items_filed": total,
                "census": "_private/benchmark/reproduction/TRN-002/"
                          "critic-item-census-2026-08-10.json",
                "method": "keyword classes over extracted items, multi-label; "
                          "recurrence = number of ANSWER FILES a class appears "
                          "in, never the number of items",
                "unassigned_items": len(unassigned),
                "_note": TIE_NOTE,
                "_not_committed": "the corpus and the census are this lane's own "
                                  "critic answers and stay under _private/",
            },
            "rows": rows,
        }
        p = os.path.join(REPO, LEDGER_REL)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"wrote {LEDGER_REL} with {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
