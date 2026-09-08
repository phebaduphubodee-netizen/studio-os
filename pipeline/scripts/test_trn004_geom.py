#!/usr/bin/env python3
"""test_trn004_geom.py — the pure half of TRN-004, tested without launching Blender.

Two kinds of test live here and they are not the same kind of claim:

  * DERIVATION tests pin arithmetic we rely on (a contact, a solved node value).
  * PROVENANCE tests pin the FACT THAT A NUMBER CAME FROM SOMEWHERE. A constant
    read off a video frame is a quotation; if someone silently "improves" it, the
    reproduction stops being a reproduction and nothing else in the repo notices.
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn004_geom as G


# --------------------------------------------------------------- contacts (R9)
def test_basin_rim_is_under_the_slab_not_on_it():
    """An UNDERMOUNT basin's rim is the slab's underside. Typing the counter
    height here is the one-number-two-meanings defect the placement audit named."""
    assert G.basin_rim_z_mm() == G.COUNTER_H_MM - G.COUNTER_T_MM
    assert G.basin_rim_z_mm() < G.counter_top_z_mm()
    assert G.basin_floor_z_mm() == G.basin_rim_z_mm() - G.BASIN_DEPTH_MM


def test_towel_layers_rest_on_each_other():
    z = G.towel_stack_layers()
    assert len(z) == G.TOWEL_STACK_N
    assert z[0] == G.counter_top_z_mm()          # the bottom towel is ON the counter
    for a, b in zip(z, z[1:]):
        assert b - a == pytest.approx(G.TOWEL_T_MM)   # each rests on the one below


def test_towel_roll_axis_is_one_radius_above_the_stack():
    top = G.counter_top_z_mm() + G.TOWEL_STACK_N * G.TOWEL_T_MM
    assert G.towel_roll_axis_z_mm() == pytest.approx(top + G.TOWEL_ROLL_D_MM / 2)


def test_a_thicker_towel_moves_every_layer_above_it(monkeypatch):
    """The point of deriving rather than typing: change one number, the stack
    follows. A typed z would stay legal and silently break the contact."""
    before = G.towel_roll_axis_z_mm()
    monkeypatch.setattr(G, "TOWEL_T_MM", G.TOWEL_T_MM + 10.0)
    assert G.towel_roll_axis_z_mm() == pytest.approx(
        before + 10.0 * G.TOWEL_STACK_N)


def test_basin_shell_is_the_shrink_offset_and_not_a_second_number():
    assert G.basin_shell_thickness_mm() is G.BASIN_SHRINK_MM


def test_mullion_centres_are_derived_from_the_run():
    c = G.mullion_bay_centres_mm(2600.0, 4)
    assert c == [0.0, 650.0, 1300.0, 1950.0, 2600.0]
    assert G.mullion_bay_centres_mm(3000.0, 3)[-1] == 3000.0
    with pytest.raises(ValueError):
        G.mullion_bay_centres_mm(2600.0, 0)


# --------------------------------------------------------------- the clip trap
def test_clip_end_guard_fails_closed_on_a_backdrop_it_cannot_see():
    ok, need = G.clip_end_is_sufficient()
    assert ok and need > G.backdrop_distance_m()
    # the real failure: someone leaves Blender's default far clip
    bad, need2 = G.clip_end_is_sufficient(clip_end_m=100.0)
    assert bad is False
    assert need2 == pytest.approx(G.backdrop_distance_m() * 1.5)


def test_backdrop_distance_uses_all_three_axes():
    """It sits 106 m out AND 40 m up; using y alone under-states it by ~7 m and
    would let a clip end pass that clips the plane's top."""
    assert G.backdrop_distance_m() > G.BACKDROP_Y_M
    assert G.backdrop_distance_m() == pytest.approx(113.33, abs=0.02)


# --------------------------------------------------------------- the slab solve
def test_the_videos_own_brick_values_make_TILE_not_slab():
    """THE FINDING THIS FILE EXISTS TO PIN. Copying the tutorial's node values
    gives 100x50 mm units. That is subway tile. If this test starts failing,
    either the constants were edited or the arithmetic changed — both matter."""
    w, h = G.brick_slab_size_m()
    assert (round(w * 1000), round(h * 1000)) == (100, 50)
    assert G.brick_mortar_width_m() * 1000 == pytest.approx(4.0)


def test_slab_settings_solve_back_to_the_slab_you_asked_for():
    for slab_w, slab_h, joint in ((1.2, 0.6, 0.004), (0.8, 0.8, 0.003),
                                  (2.4, 1.2, 0.006)):
        s = G.brick_settings_for_slab(slab_w, slab_h, joint)
        w, h = G.brick_slab_size_m(s["scale"], s["brick_width"], s["row_height"])
        assert w == pytest.approx(slab_w)
        assert h == pytest.approx(slab_h)
        assert G.brick_mortar_width_m(s["scale"], s["mortar_size"]) == pytest.approx(joint)


def test_slab_solver_is_mapping_aware():
    """`Brick Width 0.5` has no unit until the mapping is fixed. Halve the metres
    per UV unit and the node values must change to keep the same real slab."""
    a = G.brick_settings_for_slab(1.2, 0.6, 0.004, uv_m_per_unit=1.0)
    b = G.brick_settings_for_slab(1.2, 0.6, 0.004, uv_m_per_unit=0.5)
    assert b["brick_width"] == pytest.approx(a["brick_width"] * 2)
    assert b["mortar_size"] == pytest.approx(a["mortar_size"] * 2)


def test_slab_solver_refuses_a_joint_that_cannot_fit():
    with pytest.raises(ValueError):
        G.brick_settings_for_slab(1.2, 0.6, 0.5)     # joint wider than half the slab
    with pytest.raises(ValueError):
        G.brick_settings_for_slab(1.2, 0.6, 0.0)
    with pytest.raises(ValueError):
        G.brick_settings_for_slab(0.0, 0.6, 0.004)


def test_brick_slab_size_refuses_a_zero_scale():
    with pytest.raises(ValueError):
        G.brick_slab_size_m(scale=0.0)
    with pytest.raises(ValueError):
        G.brick_mortar_width_m(scale=0.0)


# --------------------------------------------------------------- colour
def test_sconce_hex_converts_to_linear_and_stays_warm():
    r, g, b = G.sconce_rgb_linear()
    assert r == pytest.approx(1.0)
    assert r > g > b                       # warm by construction, not by opinion
    assert 0 <= b < 0.4


# --------------------------------------------------------------- provenance
def test_an_unknown_light_field_stays_unknown():
    """The video does not show the second light's colour temperature. The row
    must keep `None` — a default silently filled in is the defect this repo
    calls an invented measurement."""
    unknown = dict(G.unknown_light_fields())
    assert "ceiling_key" in unknown
    assert unknown["ceiling_key"] == ["kelvin"]
    assert all(r["watts"] is not None for r in G.light_rows())


def test_every_light_row_carries_its_source():
    for r in G.light_rows():
        assert r["source"].startswith("VID "), r
        assert r["shape"] in ("SQUARE", "DISK")
        assert 0 < r["spread_deg"] <= 180


def test_video_read_constants_are_quotations_not_round_numbers():
    """These came off a UI panel. Round numbers here would mean somebody typed a
    plausible value instead of reading one, which is exactly the substitution
    this reproduction is supposed to make impossible."""
    for name, val in (("BASIN_SHRINK_MM", G.BASIN_SHRINK_MM),
                      ("MIRROR_T_MM", G.MIRROR_T_MM),
                      ("BACKDROP_Y_M", G.BACKDROP_Y_M),
                      ("BACKDROP_Z_M", G.BACKDROP_Z_M)):
        assert val != round(val), f"{name} looks typed, not read"


def test_the_sconce_was_dimmed_after_a_look():
    """Both values are kept on purpose: the first is what the panel said, the
    second is what survived looking at the render. Collapsing them to one loses
    the fact that a look changed it."""
    assert G.SCONCE_EMISSION_FINAL < G.SCONCE_EMISSION_FIRST
    assert G.SCONCE_EMISSION_FINAL == pytest.approx(15.0)


def test_ambientcg_example_is_inert_reference_not_a_fetcher():
    """This constant records that the publisher declares a physical size. It must
    stay a plain record until a real fetcher exists — a half-wired source that
    looks reachable is worse than a documented gap."""
    assert G.AMBIENTCG_EXAMPLE["dimensions_m"] == 1.2
    assert G.AMBIENTCG_EXAMPLE["source"].startswith("VID ")
