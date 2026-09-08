"""item_convention.py — THE item-id convention for D7 (P4b, DELIV-001).

PURE — no bpy, no numpy. Imported by BOTH sides so there is exactly one
definition: `scene_dump` (inside Blender) stamps each mesh record with
`item_id`, and `deliverable_check` (plain python) counts distinct ids. Two
independent reimplementations of "what is an item" is how D7's two wrong
guesses would both have shipped.

WHAT COUNTS AS ONE LOOSE STYLING ITEM
--------------------------------------
The unit a stylist PLACES in one gesture, resting on a floor or furniture
surface through a derivable contact (R9):

  deco__bench_book{N}_*    -> one item per book  ("book0", "book1")
  deco__bench_throw        -> "bench_throw"
  deco__<other>            -> one item per deco group stem (vases, plant...)
  mill__style_fold{S}_{i}  -> one item per STACK  ("fold{S}") — a folded
                              stack is placed as a stack, not per shirt
  (P4a additions arrive through styling.py already carrying these names)

WHAT IS DELIBERATELY NOT AN ITEM, said here so the exclusion is a decision
and not an accident:
  * garments + hangers (style_garment*, style_hanger*) — they HANG from
    rails; D7's word is "loose", and the wardrobe dressing is already
    guarded by its own census (D-027 / D-031);
  * the rug — floor covering, not a placeable object;
  * lamps / practicals — spec fixtures with their own e5 row;
  * acc_* ensuite textiles — placed by the bathroom census; they are
    styling, but they live behind this camera; the frustum test below is
    what keeps them from inflating a FRAME's density score, and excluding
    them here too would hide a real count from a future overview lane.
    So: they carry ids, and visibility decides.

VISIBILITY IS PART OF THE ROW, NOT OF THE CONVENTION. `scene_dump` emits
`in_frustum` (bbox corner inside the active camera's frustum). D7 counts an
item only if some part of it is in frustum — otherwise the ensuite towels
close a BEDROOM styling phase (the 15th flattering scorer, pre-refused).
DECLARED LIMIT: no occlusion test — an item fully hidden behind the bed
still counts. Printed with the row so nobody reads the number as more than
it is.
"""
import re

_FOLD = re.compile(r"^mill__style_fold(\d+)_\d+")
_BOOK = re.compile(r"^deco__bench_book(\d+)_")
_ACC = re.compile(r"^mill__acc_([a-z_0-9]+?)(?:__|$)")
# THE ACQUIRED DECO NAMING, ADDED 2026-08-26 (p2r79). `place_model` names a
# bought styling object `deco_<stem>__acq<N>` — ONE underscore after "deco",
# because the double underscore is its item/part separator. The rule above it
# tests `n.startswith("deco__")`, so every acquired deco object fell past every
# branch and returned None from the bare `return None` at the end. Measured on
# the frame of record: `deco_books__acq0`, `deco_books__acq1` and
# `deco_bedthrow__acq0` are all IN FRUSTUM, and D7 printed **0 loose styling
# objects** — the row that P4 is scored on, reading zero off a naming
# convention the build stopped following rather than off the room.
_DECO_ACQ = re.compile(r"^deco_([a-z0-9_]+?)__acq\d+", re.I)
# BUILT-IN CONTENTS, ADDED p2r80b (ORD-2026-08-26-builtin-contents-unnatural).
# The p2r80 full frame put a hero bag and a rattan basket IN FRUSTUM as
# `wardrobe__acq<N>` and display pieces as `bookshelf_display__acq<N>`, and D7
# printed 2 — the p2r79 class, one prefix over. Those bare-tag names are
# UNGROUPABLE (one GLB imports as many meshes; Blender's .00N dedup makes
# `wardrobe__acq0.001` a DIFFERENT item from `wardrobe__acq0`), so the build
# now tags per item (`wardrobe_bag__acq*`, `bookshelf_vase__acq*`) and this
# rule counts one item per stem. LEGACY names: `wardrobe__acq<N>` CANNOT match
# (one underscore where the rule needs two) and stays in the unknown channel —
# grouping it would fabricate a count the naming cannot carry. The p2r80
# transitional `bookshelf_display__acq<N>` DOES match and collapses all five
# display pieces into ONE item — an under-count, which is the conservative
# direction for a min-threshold row; it disappears with the next build's
# per-item stems.
_BUILTIN_ACQ = re.compile(r"^(wardrobe|bookshelf)_([a-z0-9_]+?)__acq\d+", re.I)
_EXCLUDE = re.compile(r"style_garment|style_hanger|^rug__|lamp|^bed__|^bench__|"
                      r"^mill__(?!style_fold|acc_)|^e5_|^wall|^floor|^ceil")


def item_id(name):
    """The loose-styling item this mesh part belongs to, or None."""
    return classify(name)[0]


def classify(name):
    """(item_id, verdict) — and the VERDICT is the half that had no channel.

    `verdict` is one of "item" (a rule matched), "excluded" (a rule says this is
    deliberately not a loose item) or **"unknown"** (no rule matched either way).
    The third case is the one this convention had no way to express: a name that
    fits no rule and no exclusion fell off the end of the function to a bare
    `return None`, identical in every way to a deliberate exclusion. So when the
    build renamed its acquired deco objects, the reader went blind on them and
    the blindness printed as the number 0 — which this module's own docstring
    forbids in its next sentence ("a 0 from a reader that cannot see is not a
    0"). It said that about an OLD DUMP and never about an unrecognised NAME."""
    n = str(name)
    m = _FOLD.match(n)
    if m:
        return f"fold{m.group(1)}", "item"
    m = _BOOK.match(n)
    if m:
        return f"book{m.group(1)}", "item"
    if n.startswith("deco__"):
        stem = n.split("__")[1]
        return re.sub(r"\.\d+$", "", stem), "item"
    m = _DECO_ACQ.match(n)
    if m:
        return m.group(1).lower(), "item"
    m = _BUILTIN_ACQ.match(n)
    if m:
        return f"{m.group(1).lower()}_{m.group(2).lower()}", "item"
    m = _ACC.match(n)
    if m:
        return f"acc_{m.group(1)}", "item"
    if _EXCLUDE.search(n):
        return None, "excluded"
    return None, "unknown"


def count_items(records):
    """records: iterable of dicts with `name`, optional `hidden_render`,
    optional `in_frustum`, optional `occluded` (scene_dump's camera ray-cast:
    the first live count let two ensuite robe hooks through the west wall
    into a bedroom styling count). An item counts when ANY of its parts is
    in frustum and not occluded. The ray-cast samples 5 points per part, so
    it errs toward OCCLUDED on thin shelf contents — the conservative
    direction for a min-threshold row: it can under-count density, never
    flatter it. Returns (n_items, sorted ids, ran, sorted unknown names); ran is
    False when no record carries `in_frustum` — an old dump must read NOT RUN,
    never 0 (a 0 from a reader that cannot see is not a 0).

    THE FOURTH ELEMENT IS THAT SAME SENTENCE APPLIED TO NAMES rather than to
    dump schemas (p2r79). Names in frustum that match no rule and no exclusion
    are returned so the caller must look at them: on 2026-08-26 this counter
    read 0 on a frame carrying `deco_books__acq0`, `deco_books__acq1` and
    `deco_bedthrow__acq0` in frustum, because the convention knew `deco__` and
    the build writes `deco_<stem>__acq<N>`. It is in the RETURN and not in a
    helper on purpose: a channel the caller has to remember to read is a queue
    whose consumer never visits it."""
    if not any("in_frustum" in r for r in records):
        return 0, [], False, []
    ids, unknown = set(), set()
    for r in records:
        if (r.get("hidden_render") or not r.get("in_frustum")
                or r.get("occluded")):
            continue
        i, verdict = classify(r.get("name", ""))
        if i:
            ids.add(i)
        elif verdict == "unknown":
            # IN FRUSTUM AND UNCLASSIFIABLE. Not counted (it may well not be
            # styling) but never silent: an unrecognised name is the shape this
            # row went blind in, and a count taken over names the reader does
            # not recognise is a claim about the CONVENTION, not about the room.
            unknown.add(r.get("name", ""))
    return len(ids), sorted(ids), True, sorted(unknown)
