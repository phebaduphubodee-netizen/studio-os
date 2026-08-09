"""Tests for trn002_materials — the PURE half only (no bpy).

The load-bearing one is test_every_mass_in_the_spec_has_a_material: the class of
defect it exists to catch is a mass silently falling through to a default, which
this repo has recorded as "a default nobody set is a decision nobody made".
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_materials as MAT  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "training", "TRN-002")


def _spec_files():
    """EVERY spec in the lane, not just the newest.

    This test used to pin spec_r7 by name and went green while the spec the
    builder actually renders drifted away from it. Checking them all also
    enforces the other half: a rename must not silently break a past round,
    because re-rendering a past round is how a regression gets caught."""
    import glob
    return sorted(glob.glob(os.path.join(LANE, "spec_r*.json")))


def _masses():
    out = []
    for p in _spec_files():
        with open(p, encoding="utf-8") as f:
            out += [m["name"] for m in json.load(f)["masses"]]
    return sorted(set(out))


def test_every_mass_in_the_spec_has_a_material():
    missing = []
    for name in _masses():
        try:
            MAT.material_for(name)
        except KeyError:
            missing.append(name)
    assert not missing, f"masses with no material rule: {missing}"


def test_unmapped_mass_raises_rather_than_defaulting():
    with pytest.raises(KeyError):
        MAT.material_for("a_mass_that_does_not_exist")


def test_exact_beats_prefix():
    # rev_* are reveals, but if an exact rule is ever added for one it must win
    assert MAT.material_for("rev_3") == "reveal_shadow"
    assert MAT.material_for("dl_1") == "lens_warm"
    assert MAT.material_for("shelf_board4") == "veneer_oak"


def test_the_left_run_is_one_material():
    """The critics' recurring 'it reads as two pieces stuck together' is answered
    by continuous material across the flush planes — so console, desk, pier and
    the etagere must resolve to the SAME key, and a change that splits them
    should fail here rather than in a critique.

    `desk_pier` is still in this tuple although r37 DELETED the mass, and that is
    not an oversight: the rule table is keyed by name across every spec this lane
    can still render, and r1..r36 all contain the pier. Taking it out of the
    table was tried at r37 and `test_every_mass_in_the_spec_has_a_material`
    refused it in one run."""
    keys = {MAT.material_for(n) for n in
            ("console", "desk", "desk_pier", "shelf_col_base", "shelf_col_back",
             "shelf_board2", "shelf_board3", "shelf_board4")}
    assert len(keys) == 1, f"the left run must be one material, got {keys}"


def test_every_assigned_key_exists_in_the_palette_once_filled():
    """PALETTE starts empty (values arrive from the measurement pass); once a
    key is present, EVERY assigned key must be present — a half-filled palette
    is how a mass gets rendered in default grey without anyone noticing."""
    if not MAT.PALETTE:
        pytest.skip("palette not yet populated by the measurement pass")
    assigned = {MAT.material_for(n) for n in _masses()}
    assert assigned <= set(MAT.PALETTE), (
        f"assigned but absent from PALETTE: {sorted(assigned - set(MAT.PALETTE))}")


def test_every_palette_row_declares_its_provenance():
    for key in MAT.PALETTE:
        assert key in MAT.PALETTE_PROV and MAT.PALETTE_PROV[key], (
            f"{key} has a value but no stated basis")


def test_retired_material_names_still_resolve():
    """A rename must never break a past round: re-rendering an old spec is how a
    regression is caught, and every retired key here (veneer_travertine, the
    lamp's two old masses, desk_panel) must still land on real palette values."""
    for retired in ("veneer_travertine",):
        assert retired in MAT.PALETTE, f"retired key {retired} dropped from PALETTE"
    for old_mass in ("lamp_shade", "lamp_stem", "desk_panel", "wardrobe", "chair"):
        assert MAT.material_for(old_mass) in MAT.PALETTE


def test_grain_rotation_only_names_real_materials():
    """MAP_ROT keyed to a material that does not exist is a silent no-op — the
    grain would stay wrong and nothing would say so."""
    assert set(MAT.MAP_ROT) <= set(MAT.PALETTE), (
        f"MAP_ROT names materials absent from PALETTE: "
        f"{sorted(set(MAT.MAP_ROT) - set(MAT.PALETTE))}")


def test_the_two_grain_directions_are_the_same_material_otherwise():
    """veneer_oak and veneer_oak_h differ ONLY in grain direction. If someone
    retunes one albedo and not the other the run splits into two woods, which is
    the defect this lane already paid for once under a different name."""
    a = MAT.PALETTE["veneer_oak"]
    b = MAT.PALETTE["veneer_oak_h"]
    assert a == b, f"the oak run has drifted into two materials: {a} vs {b}"
    assert "veneer_oak" not in MAT.MAP_ROT and "veneer_oak_h" in MAT.MAP_ROT


# ------------------------------------------------------------ fresnel (r29) --

def test_a_fresnel_row_naming_no_material_is_refused():
    """The whole point of this table is that a specular setting REACHES the
    render. A row keyed to a typo would no-op in silence, which is how this
    lane spent four rounds bracketing a number that never arrived."""
    with pytest.raises(KeyError):
        MAT.resolve_fresnel(MAT.PALETTE, {"screen_blak": (1.0, 0.0)})


def test_a_fresnel_row_must_be_ior_and_level():
    with pytest.raises(ValueError):
        MAT.resolve_fresnel(MAT.PALETTE, {"screen_black": (1.0,)})


def test_a_spec_override_wins_and_the_defaults_survive_it():
    out = MAT.resolve_fresnel(MAT.PALETTE, {"screen_black": (1.45, 0.15)})
    assert out["screen_black"] == (1.45, 0.15)
    for k, v in MAT.FRESNEL.items():
        if k != "screen_black":
            assert out[k] == v


def test_the_cavity_lining_is_darker_than_any_lit_surface_in_the_room():
    """The white liner WAS rendered and it missed: 0.348 against the target's
    0.0003. That result is what earns this row, so the pin is that the lining
    is its own dark material and not the cave's — and that it never drifts
    below a real textile, which would be typing a number to hit a pixel."""
    assert MAT.material_for("petcave_mouth") == "cave_liner"
    alb = MAT.PALETTE["cave_liner"][0]
    assert 0.005 <= sum(alb) / 3 <= 0.05, alb
    assert sum(alb) / 3 < min(sum(MAT.PALETTE[k][0]) / 3
                              for k in ("upholstery_bed", "rug_cream", "paint_white"))


# ------------------------------------------------- unworn rows (r30) --

def _newest_spec_masses():
    import re
    p = max(_spec_files(), key=lambda f: int(re.search(r"spec_r(\d+)", f).group(1)))
    with open(p, encoding="utf-8") as f:
        return [m["name"] for m in json.load(f)["masses"]]


def test_orphan_palette_rows_only_ever_shrink():
    """A RATCHET. Every row in PALETTE is a decision; a row no mass wears is a
    decision that never reached a render. The two known orphans are both things
    the target plainly shows — the venetian blind (which has a generator, a
    builder, a palette row, three tests and a light aimed at it, and has never
    had a mass in thirty specs) and the chair's black legs (built once at r12,
    dropped by r14, unnoticed for eighteen rounds). New ones are refused."""
    orphans = MAT.unworn_rows(_newest_spec_masses())
    new = orphans - MAT.ORPHAN_ROWS
    assert not new, f"new orphan palette rows: {sorted(new)}"


def test_the_orphan_list_is_not_stale():
    """The other half of a ratchet: once an orphan is built, it must leave the
    list. Otherwise the list becomes the permission slip it was written not to
    be."""
    orphans = MAT.unworn_rows(_newest_spec_masses())
    stale = MAT.ORPHAN_ROWS - orphans
    assert not stale, f"listed as orphans but now worn — delete them: {sorted(stale)}"


def test_every_emissive_key_has_a_palette_row():
    """`strip_led` sat in EMISSIVE with no PALETTE row for the whole lane, so
    build_materials — which iterates PALETTE — never created it. Same class."""
    missing = set(MAT.EMISSIVE) - set(MAT.PALETTE)
    assert not missing, f"EMISSIVE names with no material to attach to: {sorted(missing)}"
