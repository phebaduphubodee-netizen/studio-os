"""
test_exterior.py — the exterior-view invariants: the spec-declared garden HDRI
resolves fail-loud (a typo must never silently render the studio default), and the
Juliet rail derives entirely from the named opening + outline (outside side, span,
bar packing) with every dimension coming from spec DATA.

Pure python, no bpy (exterior.py is bpy-free by design, same as curtains.py). Run:
    python -m pytest pipeline/scripts/test_exterior.py -q

The fixture is the REAL canonical master-suite geometry (mm): the glass-L south
wall, the operable slider (glz-slider) the owner's photo shows the rail outside of,
and the exterior block's [est] dims.

PINNING RULE (curtain-review lesson, 2026-07-17): every geometric expectation below
is DERIVED from the fixture's own numbers by independent arithmetic — never pasted
from the module's output — so the suite stays green when a dim is owner-nudged and
red when the derivation breaks.
"""
import copy
import json
import math
import os
import sys

import pytest

import exterior as E

SPEC = {
    "room": {
        "type": "master_suite",
        "outline_mm": [[0, -697.8], [5500, -697.8], [5500, 2650],
                       [5650, 2650], [5650, 8650], [0, 8650]],
        "ceiling_mm": 2800, "wall_thk_mm": 100,
        "openings": [
            {"id": "glz-south-w", "type": "glass", "rect": [0, -697.8, 3849, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-slider", "type": "glass", "rect": [3849, -697.8, 5249, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-south-e", "type": "glass", "rect": [5249, -697.8, 5500, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-east", "type": "glass", "rect": [5500, -697.8, 5500, -148.6],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-west", "type": "glass", "rect": [0, -697.8, 0, 451],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "door-sitting", "type": "door", "head_mm": 2400,
             "rect": [5650, 3400, 5650, 4622]},
        ],
    },
    "exterior": {
        "hdri": {"slug": "rainforest_trail", "strength": 0.55, "rot_deg": 0.0,
                 "exposure": 0.0, "look": "AgX - Medium High Contrast",
                 "license": "CC0", "why": "doc"},
        "juliet_rail": {"opening": "glz-slider", "height_mm": 1000,
                        "standoff_mm": 90, "side_margin_mm": 75, "member_mm": 40,
                        "bar_mm": 14, "gap_max_mm": 110, "finish": "black metal",
                        "provenance": "doc"},
    },
}

JR = SPEC["exterior"]["juliet_rail"]
SLIDER = SPEC["room"]["openings"][1]

# ---- derived expectations (fixture arithmetic, independent of the module) ----
GLASS_LO, GLASS_HI = SLIDER["rect"][0], SLIDER["rect"][2]          # 3849, 5249
RUN_LO = GLASS_LO - JR["side_margin_mm"]                            # 3774
RUN_HI = GLASS_HI + JR["side_margin_mm"]                            # 5324
SPAN = RUN_HI - RUN_LO                                              # 1550
CLEAR = SPAN - 2 * JR["member_mm"]                                  # 1470
N_BARS = math.ceil((CLEAR - JR["gap_max_mm"])
                   / (JR["bar_mm"] + JR["gap_max_mm"]))             # 11
GAP = (CLEAR - N_BARS * JR["bar_mm"]) / (N_BARS + 1)                # ~109.7
PLANE = SLIDER["rect"][1]                                           # -697.8 (south)
OUTER_FACE = PLANE - SPEC["room"]["wall_thk_mm"]                    # -797.8 (outside=-y)
CENTRE = OUTER_FACE - (JR["standoff_mm"] + JR["member_mm"] / 2.0)   # -907.8


def _spec(**edits):
    s = copy.deepcopy(SPEC)
    for dotted, v in edits.items():
        node = s
        keys = dotted.split("__")
        for k in keys[:-1]:
            node = node[k]
        if v is ...:
            del node[keys[-1]]
        else:
            node[keys[-1]] = v
    return s


def _parts():
    return E.juliet_rail_parts(copy.deepcopy(SPEC))


def test_pure_no_bpy():
    # not `"bpy" not in sys.modules`: other tests in the suite legitimately stub bpy
    # there — the LAYER-LAW invariant is that exterior itself never touches it
    assert "bpy" not in vars(E), "exterior.py must stay importable without Blender"


# ------------------------------- resolve_hdri --------------------------------

def test_hdri_absent_is_none():
    assert E.resolve_hdri({}) is None
    assert E.resolve_hdri({"exterior": {}}) is None
    assert E.resolve_hdri(None) is None


def test_hdri_valid_passthrough():
    env = E.resolve_hdri(copy.deepcopy(SPEC))
    assert env == {"slug": "rainforest_trail", "strength": 0.55, "rot_deg": 0.0,
                   "exposure": 0.0, "look": "AgX - Medium High Contrast"}


def test_hdri_defaults_when_only_slug():
    env = E.resolve_hdri({"exterior": {"hdri": {"slug": "pool"}}})
    assert env == {"slug": "pool", "strength": 1.0, "rot_deg": 0.0,
                   "exposure": 0.0, "look": ""}


@pytest.mark.parametrize("slug", ["", None, "Pool", "a/b", "../../etc", "a b", 7])
def test_hdri_bad_slug_raises(slug):
    with pytest.raises(ValueError, match="slug"):
        E.resolve_hdri({"exterior": {"hdri": {"slug": slug}}})


@pytest.mark.parametrize("key,val", [
    ("strength", 0.0), ("strength", 9.0), ("strength", "bright"),
    ("rot_deg", 720.0), ("exposure", -5.0), ("exposure", float("nan")),
])
def test_hdri_bad_number_raises(key, val):
    with pytest.raises(ValueError, match=key):
        E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", key: val}}})


def test_hdri_bad_look_type_raises():
    with pytest.raises(ValueError, match="look"):
        E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", "look": 3}}})


@pytest.mark.parametrize("look", [
    "AgX - Medium High Contrast", "Medium High Contrast", "High Contrast",
    "AgX - Very Low Contrast", "None", "",
])
def test_hdri_valid_look_names_pass(look):
    env = E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", "look": look}}})
    assert env["look"] == look


@pytest.mark.parametrize("look", [
    "Agx - Medium High Contrast",       # lowercase x — the finding's typo
    "AgX Medium High Contrast",         # missing dash — the finding's typo
    "AgX - Medium High Kontrast", "Punchy", "medium high contrast", "AgX",
])
def test_hdri_bad_look_value_raises(look):
    # the swallowed-look law: a typo'd look must fail LOUD in the pure resolver, not
    # silently render the default via _hdri_world's try/except:pass
    with pytest.raises(ValueError, match="look"):
        E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", "look": look}}})


def test_exterior_unknown_top_level_key_raises():
    # a typo'd BLOCK name silently reverts the decided garden/rail otherwise
    for bad in ("hdris", "juliet_rai", "juliette_rail"):
        s = {"room": SPEC["room"], "exterior": dict(SPEC["exterior"])}
        s["exterior"][bad] = s["exterior"].pop(
            "hdri" if bad == "hdris" else "juliet_rail")
        with pytest.raises(ValueError, match="unknown key"):
            E.resolve_hdri(s)
        with pytest.raises(ValueError, match="unknown key"):
            E.juliet_rail_parts(s)


def test_exterior_underscore_top_key_tolerated():
    s = {"room": SPEC["room"], "exterior": dict(SPEC["exterior"], _provenance="doc")}
    assert E.resolve_hdri(s)["slug"] == "rainforest_trail"
    assert E.juliet_rail_parts(s)[1]["n_bars"] == N_BARS


def test_hdri_unknown_key_raises():
    # the typo'd-key law: "strenght" must never silently keep the default
    with pytest.raises(ValueError, match="strenght"):
        E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", "strenght": 2.0}}})


def test_hdri_underscore_keys_tolerated():
    assert E.resolve_hdri({"exterior": {"hdri": {"slug": "pool", "_note": "x"}}})


# ----------------------------- juliet_rail_parts ------------------------------

def test_rail_absent_is_empty():
    parts, meta = E.juliet_rail_parts({"room": SPEC["room"]})
    assert parts == [] and meta is None


def test_rail_member_count_and_meta():
    parts, meta = _parts()
    assert meta["n_bars"] == N_BARS
    assert abs(meta["gap_mm"] - GAP) < 1e-6
    assert abs(meta["span_mm"] - SPAN) < 1e-6
    assert abs(meta["centreline_mm"] - CENTRE) < 1e-6
    assert meta["sign_out"] == -1                      # south wall: outside is -y
    assert len(parts) == 4 + N_BARS                    # 2 posts + top + bottom + bars
    assert len(parts) == len({p[0] for p in parts}), "duplicate part names"


def test_rail_outside_the_wall_at_standoff():
    # every member fully OUTSIDE the wall's outer face; nearest face exactly standoff
    parts, _ = _parts()
    y_faces = []
    for _, x, y, z, dx, dy, dz in parts:
        y_hi = (y + dy) / E.MM
        assert y_hi <= OUTER_FACE + 1e-6, "rail member inside the wall"
        y_faces.append(y_hi)
    assert abs(max(y_faces) - (OUTER_FACE - JR["standoff_mm"])) < 1e-6


def test_rail_members_on_one_centreline():
    parts, _ = _parts()
    for name, x, y, z, dx, dy, dz in parts:
        c = (y + dy / 2.0) / E.MM
        assert abs(c - CENTRE) < 1e-6, name


def test_rail_run_and_heights():
    parts, _ = _parts()
    xs = [(p[1] / E.MM, (p[1] + p[4]) / E.MM) for p in parts]
    assert abs(min(x0 for x0, _ in xs) - RUN_LO) < 1e-6
    assert abs(max(x1 for _, x1 in xs) - RUN_HI) < 1e-6
    top = next(p for p in parts if p[0].endswith("_top"))
    assert abs((top[3] + top[6]) - JR["height_mm"] * E.MM) < 1e-9   # handrail top
    for p in parts:
        if "_post_" in p[0]:
            assert abs(p[3] - (-E.DROP_BELOW_FLOOR_MM * E.MM)) < 1e-9


def test_rail_bars_between_bottom_and_top_rails():
    parts, _ = _parts()
    z_lo = (E.BOTTOM_SEAT_MM + JR["member_mm"]) * E.MM
    z_hi = (JR["height_mm"] - JR["member_mm"]) * E.MM
    bars = [p for p in parts if "_bar_" in p[0]]
    assert len(bars) == N_BARS
    for p in bars:
        assert abs(p[3] - z_lo) < 1e-9 and abs((p[3] + p[6]) - z_hi) < 1e-9, p[0]


def test_rail_gaps_uniform_and_below_max():
    parts, _ = _parts()
    edges = sorted([(p[1] / E.MM, (p[1] + p[4]) / E.MM) for p in parts
                    if "_bar_" in p[0] or "_post_" in p[0]])
    gaps = [b0 - a1 for (a0, a1), (b0, b1) in zip(edges, edges[1:])]
    assert all(g <= JR["gap_max_mm"] + 1e-6 for g in gaps), gaps
    assert max(gaps) - min(gaps) < 1e-6, "gaps must be equal"
    assert abs(gaps[0] - GAP) < 1e-6


def test_rail_bar_count_is_minimal():
    # the property the copied N_BARS formula stands in for: ONE fewer bar would push
    # the gap OVER gap_max. Guards against a shared over-packing bug that shrinks gaps
    # (which the <=gap_max test alone cannot catch — review 2026-07-17b).
    assert (CLEAR - (N_BARS - 1) * JR["bar_mm"]) / N_BARS > JR["gap_max_mm"]


def test_rail_east_wall_axis_generic():
    # same block pointed at the SE return: axis 'y' wall, outside is +x
    s = _spec(exterior__juliet_rail__opening="glz-east",
              exterior__juliet_rail__side_margin_mm=0)
    parts, meta = E.juliet_rail_parts(s)
    assert meta["sign_out"] == 1
    east_outer = 5500 + SPEC["room"]["wall_thk_mm"]
    x_los = [p[1] / E.MM for p in parts]
    assert abs(min(x_los) - (east_outer + JR["standoff_mm"])) < 1e-6
    ys = [(p[2] / E.MM, (p[2] + p[5]) / E.MM) for p in parts]
    assert abs(min(y0 for y0, _ in ys) - (-697.8)) < 1e-6
    assert abs(max(y1 for _, y1 in ys) - (-148.6)) < 1e-6


# ------------------------------- fail-loud paths ------------------------------

def test_unknown_opening_raises():
    with pytest.raises(ValueError, match="matches no room.openings"):
        E.juliet_rail_parts(_spec(exterior__juliet_rail__opening="glz-nope"))


def test_non_glass_opening_raises():
    with pytest.raises(ValueError, match="non-glass"):
        E.juliet_rail_parts(_spec(exterior__juliet_rail__opening="door-sitting"))


def test_missing_dim_raises():
    with pytest.raises(ValueError, match="height_mm missing"):
        E.juliet_rail_parts(_spec(exterior__juliet_rail__height_mm=...))


@pytest.mark.parametrize("key,val", [
    ("height_mm", 500), ("height_mm", 2400), ("standoff_mm", 1000),
    ("bar_mm", 2), ("gap_max_mm", 500), ("member_mm", 5),
])
def test_dim_out_of_range_raises(key, val):
    with pytest.raises(ValueError, match=key):
        E.juliet_rail_parts(_spec(**{f"exterior__juliet_rail__{key}": val}))


def test_unknown_rail_key_raises():
    with pytest.raises(ValueError, match="hieght_mm"):
        E.juliet_rail_parts(_spec(exterior__juliet_rail__hieght_mm=1100))


def test_missing_outline_raises():
    with pytest.raises(ValueError, match="outline"):
        E.juliet_rail_parts(_spec(room__outline_mm=[]))


def test_degenerate_opening_raises():
    s = _spec()
    s["room"]["openings"][1]["rect"] = [3849, -697.8, 3849, -697.8]
    with pytest.raises(ValueError, match="degenerate"):
        E.juliet_rail_parts(s)


def test_missing_opening_key_raises():
    with pytest.raises(ValueError, match="opening"):
        E.juliet_rail_parts(_spec(exterior__juliet_rail__opening=...))


def test_no_bar_field_raises():
    # a run so narrow the two posts leave no field: a guard rail with no guard is the
    # render-a-lie class; must RAISE, not materialize a bar-less rail
    s = _spec(exterior__juliet_rail__side_margin_mm=0)
    s["room"]["openings"][1]["rect"] = [3849, -697.8, 3849 + 180, -697.8]
    with pytest.raises(ValueError, match="no bar field"):
        E.juliet_rail_parts(s)


def test_ambiguous_outside_probe_raises():
    # an opening rect that does not lie on the outline perimeter -> both probes inside
    # -> the OUTSIDE is unresolvable; sign_out must never be a coin flip
    s = _spec()
    s["room"]["openings"][1]["rect"] = [2000, 4000, 3000, 4000]
    with pytest.raises(ValueError, match="cannot resolve the outside"):
        E.juliet_rail_parts(s)


# --------------------- the REAL canonical file (not a copy) -------------------

def _canonical_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(
        here, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout",
        "master-suite.CANONICAL.spec.json"))


def test_canonical_spec_integration():
    """Run the module on the file build_room actually consumes (not the in-file
    fixture copy): resolve_hdri + juliet_rail_parts, invariants derived from the
    file's OWN data. Goes green under an in-range owner nudge of the [est] dims and
    red the day the block name/derivation breaks — the sibling test_curtains
    convention (test_curtains.py:395)."""
    path = _canonical_path()
    if not os.path.exists(path):
        pytest.skip("canonical spec not present")
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    env = E.resolve_hdri(spec)
    assert env and env["slug"] == spec["exterior"]["hdri"]["slug"]

    parts, meta = E.juliet_rail_parts(spec)
    jr = spec["exterior"]["juliet_rail"]
    o = next(o for o in spec["room"]["openings"] if o["id"] == jr["opening"])
    assert o["type"] in E.GLASS_TYPES
    lo, hi = sorted((o["rect"][0], o["rect"][2]))          # slider runs along x
    span = (hi + jr["side_margin_mm"]) - (lo - jr["side_margin_mm"])
    clear = span - 2 * jr["member_mm"]
    n_bars = math.ceil((clear - jr["gap_max_mm"]) / (jr["bar_mm"] + jr["gap_max_mm"]))
    assert meta["n_bars"] == n_bars
    assert abs(meta["span_mm"] - span) < 1e-6
    assert len(parts) == 4 + n_bars
    # the physical gap the file's own numbers imply stays under its own gap_max
    assert meta["gap_mm"] <= jr["gap_max_mm"] + 1e-6
    # rail sits fully OUTSIDE the facade (south wall: outside is -y for this file)
    wall_thk = spec["room"]["wall_thk_mm"]
    outer = o["rect"][1] - wall_thk
    assert all((p[2] + p[5]) / E.MM <= outer + 1e-6 for p in parts)
