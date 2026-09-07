"""test_lighting_study_derive.py — known answers for the D18 lighting study.

Every test pins a DEFINITION or a POSITIVE CONTROL rather than a value, and names the mistake it
would catch. The unit's headline is an ABSENCE ("no file models a cord, none uses a CURVE"), and
an absence is only a finding if the reader is shown to find the thing when it is there — so the
control comes first.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lighting_study_derive as L  # noqa: E402
from study_probe_read import load, curves, meshes, bevel_mm  # noqa: E402

ART = os.path.join(L.REPO, "qa", "blenderkit-study-lighting.json")


@pytest.fixture(scope="module")
def art():
    with open(ART, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------- the control the absence needs


def test_the_curve_reader_finds_curves_when_they_exist():
    """POSITIVE CONTROL. 'Zero CURVE objects in all six lamps' is indistinguishable from 'the
    reader is broken' without this. Our own scene has 23, and the reader must return them with
    real bevel radii — if this ever fails, the note's headline is unsupported, not merely stale."""
    _, ours = load("_ours_p2r91")
    cs = curves(ours)
    assert len(cs) == 23
    assert all(bevel_mm(o) > 0 for o in cs)
    assert {bevel_mm(o) for o in cs} == {1.8}


def test_no_lamp_in_the_corpus_uses_a_curve(art):
    """The headline, held. If a future fetch adds one, this fails and R1 must be rewritten."""
    assert {k: v["n_curve"] for k, v in art["assets"].items()} == {
        "a2ff3a79": 0, "a6068c83": 0, "dafcda42": 0,
        "85f6c3d5": 0, "a6313486": 0, "a8348982": 0}


# ------------------------------------------------------------- emission


def test_emission_needs_a_colour_not_just_a_strength():
    """CAUGHT IN THIS UNIT, and the reason is NOT the one first written. A strength-only rule
    does not flag everything: measured, 21 of the 33 Principled materials carrying the field read
    1.0 (64%), and dafcda42 sets 0.0 on all three of its, so strength-only would flag NOTHING in
    that file. It is wrong in BOTH directions. A node-only rule meanwhile misses the two lamps
    that emit through a Principled. Both legs are required, and neither alone is conservative."""
    strength_only = {"materials": [{"name": "m", "node_hist": {"BSDF_PRINCIPLED": 1},
                                    "principled": {"Emission Strength": 1.0,
                                                   "Emission Color": [0.0, 0.0, 0.0]}}]}
    assert L._emitters(strength_only) == ([], [])
    real = {"materials": [{"name": "Light 01", "node_hist": {"BSDF_PRINCIPLED": 1},
                           "principled": {"Emission Strength": 1.0,
                                          "Emission Color": [1.0, 0.328, 0.0]}}]}
    em, bl = L._emitters(real)
    assert [e["material"] for e in em] == ["Light 01"] and bl == []


def test_a_near_black_emitter_is_reported_not_dropped(art):
    """a8348982's Steel.001 reads 0.016 — near black. Silently dropping it would hide a judgement
    call inside a count, so it is reported in its own list."""
    a = art["assets"]["a8348982"]
    assert [e["material"] for e in a["emitting_materials"]] == ["LED Bulb"]
    assert [b["material"] for b in a["borderline_emitters"]] == ["Steel.001"]


def test_two_lamps_emit_through_a_principled_not_an_emission_node(art):
    """The case a node-only detector missed, pinned by name."""
    for k in ("85f6c3d5", "a6313486"):
        em = art["assets"][k]["emitting_materials"]
        assert len(em) == 1 and em[0]["how"] == "principled"
        assert em[0]["emission_color"] == [1.0, 0.328, 0.0]


def test_every_asset_has_exactly_one_emitting_material(art):
    """6 of 6 — the row R3 rests on."""
    assert {k: len(v["emitting_materials"]) for k, v in art["assets"].items()} == {
        "a2ff3a79": 1, "a6068c83": 1, "dafcda42": 1,
        "85f6c3d5": 1, "a6313486": 1, "a8348982": 1}


# ------------------------------------------------------------- slenderness


def test_slenderness_is_middle_over_max_not_min_over_max():
    """A cord is slender in BOTH cross-section axes. Using min would call a flat panel slender."""
    assert L._slender({"dims_mm": [18.0, 18.0, 937.0]}) == pytest.approx(52.06, abs=0.6)
    assert L._slender({"dims_mm": [1000.0, 1000.0, 5.0]}) == 1.0     # a flat disc is NOT slender
    assert L._slender({"dims_mm": [1000.0, 5.0, 5.0]}) == 200.0      # a rod is


def test_the_object_named_wire_is_not_a_slender_member(art):
    """The trap this metric exists to catch: a2ff3a79 ships an object CALLED Wire, and a study
    that trusted names would have reported a modelled cord. Its bbox is 530 mm across."""
    w = [o for o in art["assets"]["a2ff3a79"]["objects"] if o["name"].strip() == "Wire"][0]
    assert w["dims_mm"][0] >= 500 and w["slenderness"] < 3.0


def test_ours_lamp_has_no_bulb_but_the_scene_does_emit(art):
    """CORRECTED BY VERIFICATION. The first version of this note claimed our scene had nothing
    emitting at all — and the script never ran the emitter test on our side, so the zero was
    prose, not a measurement. Run, it returns FIVE emitting materials on 41 objects, four of
    which are the hand-built sconce lenses the note dissects. What is genuinely zero is the
    NIGHTSTAND LAMP, and it is zero by Emission Strength 0.0, not by colour."""
    o = art["ours"]
    names = {r["name"] for r in o["table_lamp_objects"]}
    assert len(names) == 4                                   # two lamps, two parts each
    assert all("bulb" not in n.lower() for n in names)
    assert len(o["emitting_materials"]) == 5
    assert o["objects_wearing_an_emitting_material"] == 41
    assert "e5_sconce_lens" in {e["material"] for e in o["emitting_materials"]}
    assert o["n_light_objects_in_whole_scene"] == 54


def test_the_hanger_count_is_named_objects_not_curves(art):
    """The note gave 37 and 23 for the same population. 37 objects carry 'hanger' in the name;
    23 of them are CURVE and 14 are EMPTY. Neither number alone is the sentence."""
    h = art["ours"]["hanger_named_objects"]
    assert h == {"total": 37, "CURVE": 23, "EMPTY": 14}
    assert h["CURVE"] + h["EMPTY"] == h["total"]
    assert art["ours"]["n_curve_in_whole_scene"] == 23


def test_our_table_lamp_is_acquired_so_it_is_not_an_us_versus_them_comparison(art):
    """The marquee comparison was pro-against-pro and the note did not say so."""
    assert all("__acq" in r["name"] for r in art["ours"]["table_lamp_objects"])
    assert "BOUGHT" in art["ours"]["table_lamp_is_acquired"]


# --------------------------------------------------- R10 identity, as a number


def test_a_degenerate_mesh_is_not_the_object_its_name_claims(art):
    """CAUGHT BY VERIFICATION. `Emmiter` was filed as the corpus's densest bulb on the strength
    of its NAME — the exact move the study refuses one section earlier for `Wire`. Its bbox is
    456 mm and its whole surface totals 120 mm2. Real bulbs and this thing are three orders
    apart, so the reading needs no argument."""
    a = art["assets"]["a2ff3a79"]["objects"]
    emm = [o for o in a if o["name"].strip() == "Emmiter"][0]
    assert emm["surface_vs_bbox"] < 0.001
    real = []
    for k, nm in (("a6313486", "Light Bulb"), ("85f6c3d5", "Light"),
                  ("a8348982", "Led light bulb 40Watts")):
        real.append([o for o in art["assets"][k]["objects"]
                     if o["name"].strip() == nm][0]["surface_vs_bbox"])
    assert min(real) > 0.4, real                     # real bulbs: 0.49 .. 1.11
    assert min(real) / emm["surface_vs_bbox"] > 1000


def test_the_bulb_range_excludes_the_degenerate_one(art):
    """1,762-20,532, not 1,762-31,776: the old top came from the broken mesh."""
    verts = []
    for k, nm in (("a6313486", "Light Bulb"), ("85f6c3d5", "Light"),
                  ("a8348982", "Led light bulb 40Watts")):
        verts.append([o for o in art["assets"][k]["objects"]
                      if o["name"].strip() == nm][0]["verts"])
    assert min(verts) == 1762 and max(verts) == 20532
    ours = sum(r["verts"] for r in art["ours"]["table_lamp_objects"]
               if "lampacq-367" in r["name"])
    assert min(verts) < ours                # the free-tier bulb is SMALLER than our lamp


def test_density_and_raw_count_do_not_rank_the_same_way(art):
    """The note called a vertex COUNT ratio a density. They differ by 45x here."""
    bulb = [o for o in art["assets"]["a6313486"]["objects"]
            if o["name"].strip() == "Light Bulb"][0]
    lamp = [r for r in art["ours"]["table_lamp_objects"] if "lampacq-367" in r["name"]]
    ours_v = sum(r["verts"] for r in lamp)
    ours_a = sum(r["area_m2"] for r in lamp)
    by_count = bulb["verts"] / ours_v
    by_density = bulb["verts_per_m2"] / (ours_v / ours_a)
    assert round(by_count, 1) == 5.0
    assert round(by_density) == 224


def test_a_linked_emission_colour_is_undecidable_not_emitting():
    """A linked socket is recorded as a STRING. max("HUE"[:3]) returns a character, which either
    raises against a float or silently orders as text."""
    d = {"materials": [{"name": "linked", "node_hist": {"BSDF_PRINCIPLED": 1},
                        "principled": {"Emission Strength": 1.0,
                                       "Emission Color": "HUE_SAT<IMG:2_BaseColor.jpg>"}}]}
    em, bl = L._emitters(d)
    assert em == []
    assert len(bl) == 1 and "LINKED" in bl[0]["why"]
