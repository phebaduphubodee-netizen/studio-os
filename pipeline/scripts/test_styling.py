"""Tests for styling.py — ELEMENT 8, the styling layer derived from BUILT geometry.

These pin the two things that make this module different from a prop list:
  (1) DERIVATION — every object's position comes from an anchor part, so moving the
      anchor moves the object and DELETING the anchor RAISES. A hardcoded coordinate
      would re-create the exact defect the module exists to fix.
  (2) CONTAINMENT — the garment orientation blocker (both DD critics found it
      independently by running the numbers): a hanger's shoulder bar runs FRONT-TO-BACK
      across the carcass, not along the rail. Getting it backwards packs 4.8 m of cloth
      into a 635 mm rail. Several tests here exist only to make that unshippable.

Pure python — no bpy, no Blender.
"""
import pytest

import softgoods as sg
import styling as st


# --- fixtures modelled on the REAL built parts (millwork_parts on BF09-3, verified) ---

def rail(name="mill__wardrobe__rail_short0", x=2.411, y=3.070, z=1.050,
         dx=0.635, dy=0.030, dz=0.030):
    return {"name": name, "x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz}


def shelf(name="mill__wardrobe__shelf_ni0", x=2.419, y=2.785, z=0.400,
          dx=0.864, dy=0.600, dz=0.018):
    return {"name": name, "x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz}


def coverlet():
    """bed__coverlet as _build_bed actually emits it for the canonical master bed."""
    return {"name": "bed__coverlet", "x": 3.204, "y": 0.051, "z": 0.234,
            "dx": 1.988, "dy": 2.137, "dz": 0.372}


CARCASS_D = 0.600          # BF09-3's own depth
# The REAL clear drop under BF09-3's lower short-hang rail: rail top 1.065 less the
# plinth at 0.080. Using a made-up 0.900 here made the module's own budget guard fire —
# a fixture that is not the built geometry tests the wrong thing.
CLEAR_DROP = 0.985


# --------------------------------------------------------------------- find/derivation

def test_find_raises_when_the_anchor_is_missing():
    """The whole point. Three brass rails shipped BARE while wardrobe_bay_story_bits told
    the beauty pass garments hung on them; a silent [] is how that happened."""
    with pytest.raises(ValueError) as e:
        st.find([shelf()], "rail")
    assert "rail" in str(e.value)


def test_find_names_what_it_did_see():
    """A RAISE that does not say what WAS there sends the next reader to the wrong file."""
    with pytest.raises(ValueError) as e:
        st.find([shelf()], "rail")
    assert "shelf_ni0" in str(e.value)


def test_find_is_optional_when_asked():
    assert st.find([shelf()], "rail", required=False) == []


def test_find_matches_on_the_part_token_not_the_piece_name():
    """Anchor object names are `mill__<piece>__<token>` where <piece> is the spec's own
    (Thai) name with spaces underscored — NOT the `bf` code. Matching must key off the
    trailing token, or every pin breaks the first time a piece is renamed."""
    anchors = [rail(name="mill__ตู้เสื้อผ้าเหนือเตียง_BF09-3__rail_full")]
    assert len(st.find(anchors, "rail")) == 1


# ------------------------------------------------------- garments: the orientation law

def _garments(**kw):
    kw.setdefault("clear_depth", CARCASS_D)
    kw.setdefault("clear_drop", CLEAR_DROP)
    parts = st.garments_on_rail(rail(), st.SHORT_DROP, **kw)
    return [p for p in parts if "garment" in p["name"]]


def test_garment_thickness_runs_along_the_rail_not_its_shoulder():
    """THE BLOCKER. A garment on a hanger is ~50-70mm thick along the rail and ~450mm
    across it. If this inverts, a 635mm rail is asked to hold 4.8m of cloth."""
    for g in _garments():
        x0, y0, _, x1, y1, _ = sg.bbox(g["verts"])
        along, across = x1 - x0, y1 - y0            # rail runs along x in this fixture
        assert along < across * 0.35, (
            f"garment is {along * 1000:.0f}mm along the rail and only "
            f"{across * 1000:.0f}mm across it — the hanger is turned the wrong way")


def test_garments_do_not_interpenetrate():
    gs = sorted((sg.bbox(g["verts"])[0], sg.bbox(g["verts"])[3]) for g in _garments())
    for (_, a_hi), (b_lo, _) in zip(gs, gs[1:]):
        assert b_lo >= a_hi - 1e-9, "neighbouring garments overlap along the rail"


def test_the_garment_file_fits_on_its_rail():
    gs = [sg.bbox(g["verts"]) for g in _garments()]
    r = rail()
    assert min(b[0] for b in gs) >= r["x"] - 1e-9
    assert max(b[3] for b in gs) <= r["x"] + r["dx"] + 1e-9


def test_shoulders_stay_inside_the_host_carcass():
    """The containment bound must be solved on the garment's ACTUAL span (it flares below
    the waist and leans), not on its nominal width — otherwise the widest garment grows
    through a gable."""
    gs = [sg.bbox(g["verts"]) for g in _garments()]
    r = rail()
    ctr = r["y"] + r["dy"] * 0.5
    lo, hi = ctr - CARCASS_D * 0.5, ctr + CARCASS_D * 0.5
    assert min(b[1] for b in gs) >= lo, "garments protrude out the front of the carcass"
    assert max(b[4] for b in gs) <= hi, "garments push through the carcass back"


def test_garments_hang_below_their_rail():
    r = rail()
    for g in _garments():
        _, _, z0, _, _, z1 = sg.bbox(g["verts"])
        assert z1 <= r["z"] + r["dz"] + 1e-9
        assert z0 < r["z"]


def test_a_drop_longer_than_the_clear_space_raises():
    """A 1400mm dress on a rail with 900mm of air below does not 'look a bit long' — it
    passes through the shelf under it. RAISE, never clamp (the _build_bed clamp lesson)."""
    with pytest.raises(ValueError) as e:
        st.garments_on_rail(rail(), st.FULL_DROP, CARCASS_D, 0.90)
    assert "exceeds the derived budget" in str(e.value)


def test_no_garment_exceeds_the_clear_drop_even_with_variation():
    gs = _garments()
    r = rail()
    floor_z = r["z"] + r["dz"] * 0.5 - CLEAR_DROP
    for g in gs:
        assert sg.bbox(g["verts"])[2] >= floor_z - 1e-6


def test_a_rail_too_short_to_read_as_a_wardrobe_raises():
    """BF09-1-0's real rails are 263.9mm. A rail that can only hold two garments reads as
    a bare towel bar — which IS the defect. Say so rather than emitting two."""
    with pytest.raises(ValueError) as e:
        st.garments_on_rail(rail(dx=0.15), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    assert "MIN_GARMENTS" in str(e.value)


def test_a_shallow_host_raises_rather_than_shrinking_to_nothing():
    with pytest.raises(ValueError):
        st.garments_on_rail(rail(), st.SHORT_DROP, clear_depth=0.20, clear_drop=CLEAR_DROP)


def test_garments_carry_a_three_value_ladder():
    """Six frames contain essentially nothing below 35% luminance. The wardrobe is where
    dark clothes legitimately live, and all three identities are already signed."""
    toks = {p["name"].rsplit("__", 1)[-1] for p in _garments()}
    assert len(toks) >= 2
    assert toks <= {st.TOK_LINEN, st.TOK_INK, st.TOK_TERRY}


def test_every_garment_gets_a_hanger():
    parts = st.garments_on_rail(rail(), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    g = [p for p in parts if "garment" in p["name"]]
    h = [p for p in parts if "hanger" in p["name"]]
    assert len(g) == len(h) > 0


def test_hangers_are_metal_not_joinery_backer():
    """matte_black_ply is a joinery BACKER identity already carrying the slat backing;
    a hanger is metal, and element 5's black-anodised aluminium is already routed."""
    parts = st.garments_on_rail(rail(), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    for p in parts:
        if "hanger" in p["name"]:
            assert p["name"].endswith("__blackalu")


def test_garments_move_when_their_rail_moves():
    """DERIVATION, stated as a test: this is what a hardcoded coordinate would break."""
    a = sg.bbox(_garments()[0]["verts"])
    moved = st.garments_on_rail(rail(x=2.411 + 0.4), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    b = sg.bbox([p for p in moved if "garment" in p["name"]][0]["verts"])
    assert abs((b[0] - a[0]) - 0.4) < 1e-6


def test_garments_are_not_instanced_copies():
    """The vault's own amateur red flag: 'placing identical, repeating 3D assets across a
    scene'. Instancing one garment 30 times ADDS the CAD tell."""
    sils = {tuple(round(c, 5) for c in sg.bbox(g["verts"])) for g in _garments()}
    assert len(sils) == len(_garments())


def test_a_rail_running_along_y_orients_the_same_way():
    """BF09-3 runs along x; the bay's masses run along y. The law is the same."""
    r = rail(x=3.0, y=1.0, dx=0.030, dy=0.700)
    gs = [p for p in st.garments_on_rail(r, st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
          if "garment" in p["name"]]
    for g in gs:
        x0, y0, _, x1, y1, _ = sg.bbox(g["verts"])
        assert (y1 - y0) < (x1 - x0) * 0.35, "shoulder span runs along the rail"


# ------------------------------------------------------------------- shelves / stacks

def test_a_stack_sits_ON_its_shelf():
    sh = shelf()
    for p in st.stack_on_shelf(sh):
        assert p["z"] >= sh["z"] + sh["dz"] - 1e-9


def test_a_stack_never_overhangs_its_shelf():
    sh = shelf()
    for p in st.stack_on_shelf(sh, salt=3):
        assert p["x"] >= sh["x"] - 1e-9
        assert p["x"] + p["dx"] <= sh["x"] + sh["dx"] + 1e-9
        assert p["y"] >= sh["y"] - 1e-9
        assert p["y"] + p["dy"] <= sh["y"] + sh["dy"] + 1e-9


def test_a_stack_moves_with_its_shelf():
    a = st.stack_on_shelf(shelf())[0]
    b = st.stack_on_shelf(shelf(z=1.05))[0]
    assert abs((b["z"] - a["z"]) - 0.65) < 1e-9


def test_stack_rejects_a_bad_fraction():
    with pytest.raises(ValueError):
        st.stack_on_shelf(shelf(), frac_w=1.4)


# ------------------------------------------------------------------------ the bed head

def test_head_ranks_do_not_overlap():
    """Both DD critics found the same blocker: the bed head is FLUSH with BF14 (head edge
    x5204, wall face x5203), so shams cannot go BEHIND the pillows. The ranks are a
    re-derivation of the pillow zone, and they must tile without overlapping."""
    ranks, _ = st.head_ranks(1.988)
    for (a_from, a_d), (b_from, _) in zip(ranks, ranks[1:]):
        assert b_from >= a_from + a_d - 1e-9


def test_head_ranks_are_three_heights():
    ranks, _ = st.head_ranks(1.988)
    assert len(ranks) == 3


def test_head_ranks_total_is_returned_for_the_duvet_to_rederive_from():
    """`dv_from = pz + 0.14` must recompute from the NEW zone, or the duvet lands on the
    lumbar. A derivation that lives in two places drifts."""
    ranks, total = st.head_ranks(1.988)
    assert abs(total - (ranks[-1][0] + ranks[-1][1])) < 1e-9


def test_a_bed_too_short_for_three_ranks_raises():
    with pytest.raises(ValueError) as e:
        st.head_ranks(0.9)
    assert "rank" in str(e.value).lower()


def test_pillow_bank_stays_inside_the_bed_plan_rect():
    cov = coverlet()
    for p in st.pillow_bank(cov, "x", 1):
        x0, y0, _, x1, y1, _ = sg.bbox(p["verts"])
        assert x0 >= cov["x"] - 1e-6 and x1 <= cov["x"] + cov["dx"] + 1e-6
        assert y0 >= cov["y"] - 1e-6 and y1 <= cov["y"] + cov["dy"] + 1e-6


def test_pillow_bank_gives_three_distinct_heights():
    tops = sorted({round(sg.bbox(p["verts"])[5], 3) for p in st.pillow_bank(coverlet(), "x", 1)})
    assert len(tops) >= 3, f"a styled bed has three pillow heights, got {tops}"


def test_the_shams_are_the_tallest_rank():
    parts = {p["name"]: sg.bbox(p["verts"]) for p in st.pillow_bank(coverlet(), "x", 1)}
    sham = parts["bed__sham0"][5]
    pillow = parts["bed__pillowsoft0"][5]
    assert sham > pillow


def test_no_pillow_is_dented():
    """This owner's two prior rejections were both of things he read as BROKEN rather
    than ugly. A pressed pillow is the cue an engineer reads as a modelling error, and
    the DD deletes it on purpose — a test so it cannot creep back."""
    a = st.pillow_bank(coverlet(), "x", 1)
    b = st.pillow_bank(coverlet(), "x", 1)
    lhs = sg.bbox([p for p in a if p["name"] == "bed__pillowsoft0"][0]["verts"])
    rhs = sg.bbox([p for p in b if p["name"] == "bed__pillowsoft1"][0]["verts"])
    assert abs((lhs[5] - lhs[2]) - (rhs[5] - rhs[2])) < 1e-6


def test_the_lumbar_is_a_signed_textile_not_a_joinery_ply():
    names = [p["name"] for p in st.pillow_bank(coverlet(), "x", 1)]
    assert any(n.endswith(f"__{st.TOK_TERRY}") for n in names)


def test_pillow_bank_rejects_a_bad_head_axis():
    with pytest.raises(ValueError):
        st.pillow_bank(coverlet(), "z", 1)


def test_pillow_bank_rejects_a_bad_head_sign():
    with pytest.raises(ValueError):
        st.pillow_bank(coverlet(), "x", 0)


def test_pillow_bank_follows_the_head_to_the_other_end():
    cov = coverlet()
    east = sg.bbox([p for p in st.pillow_bank(cov, "x", 1) if "sham0" in p["name"]][0]["verts"])
    west = sg.bbox([p for p in st.pillow_bank(cov, "x", -1) if "sham0" in p["name"]][0]["verts"])
    assert east[0] > west[0]


# ------------------------------------------------------------------------- the drape

def test_the_drape_stays_within_the_coverlet_footprint():
    """The inset must exactly absorb the fold bulge — the CAD invariant by construction,
    not by hope."""
    cov = coverlet()
    d = st.bed_drape(cov, base_top=0.204)[0]
    x0, y0, _, x1, y1, _ = sg.bbox(d["verts"])
    assert x0 >= cov["x"] - 1e-6 and x1 <= cov["x"] + cov["dx"] + 1e-6
    assert y0 >= cov["y"] - 1e-6 and y1 <= cov["y"] + cov["dy"] + 1e-6


def test_the_drape_hangs_from_the_coverlet_top():
    cov = coverlet()
    _, _, z0, _, _, z1 = sg.bbox(st.bed_drape(cov, base_top=0.204)[0]["verts"])
    assert abs(z1 - (cov["z"] + cov["dz"])) < 1e-6
    assert z0 < cov["z"]


def test_the_drape_keeps_the_bed_prefix_so_it_misses_the_mill_router():
    """Bed soft goods take _build_bed's bespoke bedding materials. Routing them through
    mill__ would expose the hero object to the silent-oak default."""
    assert st.bed_drape(coverlet(), 0.204)[0]["name"].startswith("bed__")


def test_a_coverlet_too_small_to_inset_raises():
    tiny = dict(coverlet(), dx=0.02, dy=0.02)
    with pytest.raises(ValueError):
        st.bed_drape(tiny, base_top=0.0)


def test_the_throw_hangs_off_the_foot_edge():
    cov = coverlet()
    t = st.bed_throw(cov, "x", 1)[0]
    _, _, z0, _, _, z1 = sg.bbox(t["verts"])
    assert z1 <= cov["z"] + cov["dz"] + 0.02
    assert z0 < cov["z"] + cov["dz"] - 0.20, "the throw has no hanging tail"


# ------------------------------------------------------------------- surface vignettes

def test_book_stack_leans():
    xs = {round(p["x"], 6) for p in st.book_stack(1.0, 1.0, 0.52, n=3)}
    assert len(xs) == 3


def test_book_stack_rejects_zero():
    with pytest.raises(ValueError):
        st.book_stack(1.0, 1.0, 0.52, n=0)


def test_vessel_is_a_revolve_not_a_box():
    v, = st.vessel(1.0, 1.0, 0.52)
    xs = {round(p[0], 4) for p in v["verts"]}
    assert len(xs) > 6, "a vessel with 2 distinct x values is a box"


def test_vessel_rejects_degenerate():
    with pytest.raises(ValueError):
        st.vessel(1.0, 1.0, 0.52, r=0.0)


def test_every_emitted_part_declares_a_shape():
    parts = (st.garments_on_rail(rail(), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
             + st.stack_on_shelf(shelf())
             + st.bed_drape(coverlet(), 0.204)
             + st.pillow_bank(coverlet(), "x", 1)
             + st.bed_throw(coverlet(), "x", 1)
             + st.book_stack(1.0, 1.0, 0.52)
             + st.vessel(1.0, 1.0, 0.52)
             + st.tray(1.0, 1.0, 0.52))
    for p in parts:
        assert p["shape"] in ("box", "mesh"), p
        if p["shape"] == "mesh":
            assert p["verts"] and p["faces"]
        else:
            assert {"x", "y", "z", "dx", "dy", "dz"} <= set(p)


def test_every_emitted_part_is_deterministic():
    a = st.garments_on_rail(rail(), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    b = st.garments_on_rail(rail(), st.SHORT_DROP, CARCASS_D, CLEAR_DROP)
    assert [p["name"] for p in a] == [p["name"] for p in b]
    assert a[0]["verts"] == b[0]["verts"]


# ------------------------------------------------- the armour (D-E8-12), via the CANONICAL FILE

def _canonical():
    import io as _io, json as _json, os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..",
                      "projects", "PRJ-2026-002_c001-house", "03_layout",
                      "master-suite.CANONICAL.spec.json")
    return _json.load(_io.open(p, encoding="utf-8"))


def test_styling_story_bits_are_actually_called_by_material_story():
    """An un-called bit is a silent bit (D-E7-8). Proved through the canonical FILE, not a
    fixture, so the armour cannot pass here and be missing in the render that ships."""
    import material_presets as mp
    story = mp.material_story(None, _canonical())
    assert "HANGING GARMENTS fill all" in story
    assert "HANGING TEXTILE" in story
    assert "THREE-HEIGHT ladder" in story


def test_the_garment_count_in_the_prose_is_derived_not_written():
    """The e6 wound: a story bit hardcoded '2 bath towels' while the census said otherwise,
    and the polish would have painted back a towel the build had removed. Delete a rail
    source and the prose must follow it down."""
    import material_presets as mp
    spec = _canonical()
    full = mp.styling_story_bits(spec)
    n_full = int(full[0].split("fill all ")[1].split(" ")[0])
    stripped = dict(spec, builtins=[b for b in spec["builtins"] if not b.get("open")])
    fewer = mp.styling_story_bits(stripped)
    n_few = int(fewer[0].split("fill all ")[1].split(" ")[0])
    assert n_few < n_full, "prose count ignored a removed rail source"


def test_the_armour_stays_silent_when_there_is_nothing_to_describe():
    import material_presets as mp
    assert mp.styling_story_bits({"room": {"outline_mm": [[0, 0], [1, 0], [1, 1], [0, 1]]}}) == []


# ------------------- the ORCHESTRATORS the consumer actually calls (were untested)
# The pre-commit review found `dress_rails` and `dress_shelves` — the only two functions
# _add_styling calls — had ZERO coverage, which is why 1985 green tests could not see a
# regression that hard-failed four other room specs under real Blender.

def _wardrobe_anchors():
    """A minimal open-wardrobe piece: plinth + shelf + two stacked rails."""
    P = {"piece": "W", "kind": "wardrobe"}
    return [
        dict(P, name="mill__W__plinth", part="plinth", x=2.4, y=2.785, z=0.0,
             dx=0.9, dy=0.6, dz=0.08),
        dict(P, name="mill__W__shelf_sh", part="shelf_sh", x=2.4, y=2.785, z=2.5,
             dx=0.9, dy=0.6, dz=0.018),
        dict(P, name="mill__W__rail_short0", part="rail_short0", x=2.411, y=3.070,
             z=1.05, dx=0.635, dy=0.03, dz=0.03),
        dict(P, name="mill__W__rail_short1", part="rail_short1", x=2.411, y=3.070,
             z=2.05, dx=0.635, dy=0.03, dz=0.03),
    ]


def test_dress_rails_fills_every_rail_it_is_given():
    parts = st.dress_rails(_wardrobe_anchors(), min_rails=2)
    assert len([p for p in parts if "garment" in p["name"]]) >= 2 * st.MIN_GARMENTS


def test_dress_rails_derives_short_vs_full_hang_from_what_is_below():
    """The upper rail knows the lower rail is under it; the lower one only has the plinth.
    Neither length is declared anywhere."""
    a = _wardrobe_anchors()
    lo, hi = a[2], a[3]
    assert st.rail_clearances(lo, a)[1] < 1.25       # short hang: plinth is 970mm down
    assert st.rail_clearances(hi, a)[1] < 1.25       # short hang: the rail below is 970mm down


def test_a_closed_room_dresses_nothing_and_raises_nothing():
    """THE REGRESSION. A bedroom whose wardrobe is CLOSED has millwork and no rail — that
    is a design with no open dressing piece, not an omission. Demanding a rail from it
    hard-failed four room specs that built fine before this element existed."""
    closed = [{"name": "mill__C__door0", "piece": "C", "part": "door0", "kind": "wardrobe",
               "x": 0.0, "y": 0.0, "z": 0.08, "dx": 0.5, "dy": 0.02, "dz": 2.69}]
    assert st.dress_rails(closed, min_rails=0) == []


def test_a_room_that_DECLARED_an_open_piece_still_raises_when_its_rails_vanish():
    """The other half: the guard must stay armed where the decision exists. Scoping it to
    the spec's own declarations makes it STRONGER than the blanket demand it replaces."""
    closed = [{"name": "mill__C__door0", "piece": "C", "part": "door0", "kind": "wardrobe",
               "x": 0.0, "y": 0.0, "z": 0.08, "dx": 0.5, "dy": 0.02, "dz": 2.69}]
    with pytest.raises(ValueError) as e:
        st.dress_rails(closed, min_rails=1)
    assert "hang rail" in str(e.value)


def test_dress_shelves_refuses_a_display_bookshelf():
    """Folded knits on element 2's signed open display bookshelf — the one built with no
    back so the garden reads THROUGH it — is the wrong object in the wrong room. The host
    kind rides the anchor precisely so this lane can refuse it."""
    book = [dict(a, kind="bookshelf") for a in _wardrobe_anchors()]
    assert st.dress_shelves(book) == []


def test_dress_shelves_dresses_a_wardrobe_shelf():
    assert st.dress_shelves(_wardrobe_anchors(), every=1)


def test_dress_shelves_ignores_an_anchor_with_no_kind():
    """An unlabelled anchor is not evidence that knits belong there."""
    nokind = [{k: v for k, v in a.items() if k != "kind"} for a in _wardrobe_anchors()]
    assert st.dress_shelves(nokind) == []


# --------------------------------------------------- the throw's containment (was absent)

def test_the_throw_stays_inside_its_host_rect():
    """Measured at 45.9mm OUTSIDE the bed on the canonical spec, and in AABB collision with
    the foot bench on specs/master_bedroom.json. The generator's skew and its tail's
    outward swing are both outward terms, and neither was in any budget."""
    cov = coverlet()
    for sign in (1, -1):
        for axis in ("x", "y"):
            t = st.bed_throw(cov, axis, sign)[0]
            x0, y0, _, x1, y1, _ = sg.bbox(t["verts"])
            assert x0 >= cov["x"] - 1e-6 and x1 <= cov["x"] + cov["dx"] + 1e-6
            assert y0 >= cov["y"] - 1e-6 and y1 <= cov["y"] + cov["dy"] + 1e-6


def test_the_throw_raises_rather_than_overflowing_a_host_too_small_for_it():
    tiny = dict(coverlet(), dx=0.12, dy=0.12)
    with pytest.raises(ValueError):
        st.bed_throw(tiny, "x", 1)


def test_the_vessel_does_not_route_to_the_oak_default():
    """`porcelain` is a FIXTURE role with no mill_object_role branch — a mill__ name
    carrying it falls through to oak. Sanitaryware goes through fix__."""
    import material_presets as mp
    name = st.vessel(1.0, 1.0, 0.5)[0]["name"]
    assert name.startswith("fix__")
    assert mp.mill_object_role(name) == "oak"        # i.e. it never reaches that router
