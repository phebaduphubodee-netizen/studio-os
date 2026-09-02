"""trade_dress — a brand mark on a bought mesh never reaches a client frame (pure).

D-183 (2026-09-01): the model-study probe of the p2r91 scene found `Cartier Gold.001`
with a packed `Cartier-logo` image on two bookshelf ornaments — a real trade mark on a
shelf in a frame meant for a client. `docs/LICENSING.md` had said since July that a
licence does not clear trade dress, and nothing READ that sentence at import time:
the asset passed scale, density and PBR checks and carried the logo through all of
them, because none of those rungs asks what the picture on the texture IS.

This module is the reader. It is deliberately a LEXICON and not an object list
(R9b: a rule that names the objects it applies to exempts the next one) — every
imported material and image name is scanned, whatever the mesh is. What it cannot do
is read pixels: a monogram baked into an unnamed `albedo.png` passes, and the study
note says so (organic.md, 8f19d91a's `LV_texture` is caught by NAME). That gap is
declared here so nobody reads a clean scan as a cleared frame.

Layer law: no bpy. `scan()` takes names, `pick_substitute()` takes names; the
Blender side (build_room.place_model) hands them in and swaps the slot.
"""
from __future__ import annotations

import re

# Word-boundary, case-insensitive. Tokens are BRAND MARKS that appear in asset
# material/image names in the wild; short marks that are also common words are
# anchored by a separator ("LV_" / "_LV") rather than matched bare.
BRAND_PATTERNS = (
    r"\bcartier\b", r"\blouis[\s_-]*vuitton\b", r"\blv\b",
    r"\bgucci\b", r"\bchanel\b", r"\bherm[eè]s\b", r"\bdior\b", r"\bprada\b",
    r"\bfendi\b", r"\bburberry\b", r"\brolex\b", r"\btiffany\b", r"\bbvlgari\b",
    r"\bbulgari\b", r"\bversace\b", r"\bbalenciaga\b", r"\bgoyard\b",
    r"\bnike\b", r"\badidas\b", r"\bsupreme\b", r"\bcoca[\s_-]*cola\b",
    r"\bstarbucks\b", r"\bmarlboro\b", r"\bapple[\s_-]*logo\b", r"\bsamsung\b",
    r"\bsony\b", r"\bdyson\b", r"\bnespresso\b", r"\bmonogram\b", r"\blogo\b",
)
_RX = [re.compile(p, re.IGNORECASE) for p in BRAND_PATTERNS]


_SEP = re.compile(r"[_\-.:/\\]+")


def hits(name: str) -> list[str]:
    """The brand patterns a single name trips (empty = clean by name). Separators
    (underscore, dash, dot, slashes) become spaces first: a regex word boundary
    treats the underscore as a word character, so `Cartier_Gold` would slip past
    the `cartier` pattern — the first test run caught it on `B_monogram`."""
    norm = _SEP.sub(" ", name or "")
    return [p for p, rx in zip(BRAND_PATTERNS, _RX) if rx.search(norm)]


def scan(materials: dict[str, list[str]]) -> dict[str, list[str]]:
    """materials: {material_name: [image names / filepaths on its nodes]} ->
    {material_name: [offending names]} for every material that trips by its own
    name or by any image it carries. Order of the input is kept."""
    out: dict[str, list[str]] = {}
    for mname, imgs in materials.items():
        bad = [n for n in [mname, *imgs] if hits(n)]
        if bad:
            out[mname] = bad
    return out


def pick_substitute(offender: str, materials: dict[str, list[str]]) -> str | None:
    """The plain sibling to swap in: a material of the SAME import that trips no
    pattern, preferring one with no image at all (a flat colour cannot carry a mark
    the lexicon missed). None when every sibling is branded or there is none —
    the caller then refuses the mesh, never ships it."""
    clean = [(m, imgs) for m, imgs in materials.items()
             if m != offender and not hits(m) and not any(hits(i) for i in imgs)]
    if not clean:
        return None
    clean.sort(key=lambda t: (len(t[1]) > 0, t[0]))
    return clean[0][0]
