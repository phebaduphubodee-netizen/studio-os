"""Tests for the FRONT LAW (front_registry + placement.face_rot + the gate rung).

The negative control is the REAL defect: a spec item shaped exactly like the
p2r75 nightstand rows (model 24c65eb4…, typed rot 90) must FAIL — that shape
shipped with every rung green and the owner refuted it from the render the
same night. "It would have caught it" is a measurement here, not a claim.
"""
import json
import os

import pytest

import front_registry as FR
import placement as PL

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASTA = "24c65eb4-765b-43f3-a171-266521dd06b1"


# ---------------------------------------------------------------- the pure law

def test_resolve_rot_collapses_for_minus_90_fronts():
    assert FR.resolve_rot(90, -90.0) == 90.0
    assert FR.resolve_rot(270, -90.0) == 270.0


def test_resolve_rot_corrects_a_zero_front():
    # tub_chair_c: native front 0 — the fail-open default applied 270 where the
    # law needs 180, which is the 90° error every frame carried.
    assert FR.resolve_rot(270, 0.0) == 180.0


def test_resolve_rot_null_front_passes_through():
    assert FR.resolve_rot(37.5, None) == 37.5


def test_face_rot_away_from_hugged_wall():
    assert PL.face_rot({"away_from_wall": "E"}) == 270.0   # face W, into the room
    assert PL.face_rot({"away_from_wall": "N"}) == 0.0     # face S
    assert PL.face_rot({"toward_wall": "W"}) == 270.0      # the tub chair


def test_face_rot_refuses_junk():
    with pytest.raises(PL.PlacementError):
        PL.face_rot({"away_from_wall": "NE"})              # not cardinal
    with pytest.raises(PL.PlacementError):
        PL.face_rot({"leans_toward": "W"})                 # unknown relationship
    with pytest.raises(PL.PlacementError):
        PL.face_rot({"away_from_wall": "E", "toward_wall": "W"})


def test_two_sources_for_one_facing_refused():
    with pytest.raises(PL.PlacementError):
        FR.spec_rot_of({"rot": 90, "facing_derive": {"away_from_wall": "E"}})


def test_spec_rot_of_derives_and_falls_back():
    assert FR.spec_rot_of({"facing_derive": {"away_from_wall": "E"}}) == 270.0
    assert FR.spec_rot_of({"rot": 180}) == 180.0
    assert FR.spec_rot_of({}) == 0.0


# ------------------------------------------------------------------- the rung

def _reg():
    return FR.load(root=ROOT)


def test_registry_of_record_loads_and_carries_the_asta():
    reg = _reg()
    assert reg is not None
    assert FR.front_deg(reg, ASTA) == -90.0
    assert FR.front_deg(reg, "tub_chair_c") == 0.0
    assert not FR.is_missing(FR.front_deg(reg, "5b8e98d779b84786ba8131ba3662c698"))


def test_negative_control_the_p2r75_shape_fails():
    # The exact shape that shipped: fronted model, TYPED rot, gate green.
    item = {"name": "โต๊ะข้างเตียง เหนือ", "kind": "side_table",
            "model": ASTA, "rot": 90}
    v = FR.check_spec(_reg(), {"items": [item]})
    assert len(v) == 1 and "TYPES its facing" in v[0]


def test_unmeasured_model_fails_closed():
    v = FR.check_spec(_reg(), {"items": [{"name": "x", "model": "no-such-id"}]})
    assert len(v) == 1 and "NO row" in v[0]


def test_unreadable_registry_is_a_violation_not_a_pass():
    v = FR.check_spec(None, {"items": [{"name": "x", "model": ASTA}]})
    assert len(v) == 1 and "unreadable" in v[0]


def test_derived_facing_on_fronted_model_passes():
    item = {"name": "x", "model": ASTA,
            "facing_derive": {"away_from_wall": "E"}}
    assert FR.check_spec(_reg(), {"items": [item]}) == []


def test_null_front_model_may_type_its_rot():
    item = {"name": "bench", "model": "5b8e98d779b84786ba8131ba3662c698",
            "rot": 90}
    assert FR.check_spec(_reg(), {"items": [item]}) == []


def test_face_lines_name_the_world_front():
    item = {"name": "nightstand", "model": ASTA,
            "facing_derive": {"away_from_wall": "E"}}
    lines = FR.face_lines({"items": [item]}, _reg())
    assert len(lines) == 1
    assert "front W" in lines[0] and "derived" in lines[0]


def test_spec_of_record_passes_the_rung():
    # The converted canonical spec: all three model masses must clear the rung.
    p = os.path.join(ROOT, "projects", "PRJ-2026-002_c001-house", "03_layout",
                     "master-suite.CANONICAL.spec.json")
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    assert FR.check_spec(_reg(), spec) == []
    lines = FR.face_lines(spec, _reg())
    assert len(lines) == 4        # bench + 2 nightstands + tub chair
    joined = " | ".join(lines)
    assert "UNMEASURED" not in joined
    # both nightstands and the tub chair face WEST by derivation now
    assert joined.count("front W") == 3
