"""Tests for contact_check — the register that keeps a joint from being two
independent numbers that happen to be equal.

The negative controls here are the ways a contact can LOOK declared and not be
one, and each of them is a defect shape this repo has already paid for:

  * the faces drifted apart          — TRN-002 r37/r38: kill the headboard's
                                       invented 176 mm and the bed's typed head
                                       coordinate stays legal, 83 mm away
  * the faces are equal by accident  — two masses that interpenetrate can carry
                                       equal face values out of centre arithmetic
  * the faces never meet             — coplanar and disjoint, the same test
                                       decisions_check applies to a `where` that
                                       names a path that does not exist
  * no datum                         — a joint with no held side is the R9 defect
                                       one level up: two numbers, no relationship

The last test walks the LANE'S OWN SPECS rather than a fixture, for the reason
test_trn002_materials learned the hard way: a rule proved on a hand-made dict is
proved about the dict.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contact_check as CC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "training", "TRN-002")


def _mass(name, c, s):
    return {"name": name, "c": list(c), "s": list(s), "value": 0.9,
            "prov": "M(fixture)", "seen": "YES"}


def _spec(masses, contacts):
    return {"masses": masses, "contacts": contacts}


def _pair(gap=0.0, **kw):
    """A panel at x -1406.7..-1314 and a bed butting its front face."""
    row = {"a": "bed", "a_face": "x_max", "b": "panel", "b_face": "x_min",
           "gap_mm": gap, "datum": "b", "why": "the bed is pushed to the panel"}
    row.update(kw)
    masses = [_mass("panel", (-1360.35, -3552.55, 441.475), (92.7, 2005.1, 882.95)),
              _mass("bed", (-2480.85, -3142.5, 110.5), (2148.3, 2075.0, 221))]
    return _spec(masses, [row])


# --- the joint holds ----------------------------------------------------------

def test_a_joint_that_holds_passes():
    assert CC.check(_pair()) == []


def test_face_value_reads_both_ends():
    m = _mass("panel", (-1360.35, 0, 0), (92.7, 10, 10))
    assert abs(CC.face_value(m, "x_max") - (-1314.0)) < 1e-9
    assert abs(CC.face_value(m, "x_min") - (-1406.7)) < 1e-9


def test_no_contacts_block_is_not_a_violation():
    """A spec from before the register existed must still render. The register
    is append-only in intent; absence is silence, not a broken claim."""
    assert CC.check({"masses": []}) == []


# --- the defect that earned the module ----------------------------------------

def test_the_faces_drifting_apart_fails():
    """r38's own defect: thin the panel and leave the bed where it was typed."""
    s = _pair()
    by = {m["name"]: m for m in s["masses"]}
    by["bed"]["c"][0] -= 83.3 / 2.0          # bed head slides back to -1490
    by["bed"]["s"][0] -= 83.3
    v = CC.check(s)
    assert len(v) == 1 and "83.3" in v[0].replace("83.300", "83.3")


def test_a_declared_gap_is_allowed_and_checked():
    s = _pair(gap=83.3)
    by = {m["name"]: m for m in s["masses"]}
    by["bed"]["c"][0] -= 83.3 / 2.0
    by["bed"]["s"][0] -= 83.3
    assert CC.check(s) == []                  # the gap is declared, so it holds
    assert len(CC.check(_pair(gap=83.3))) == 1   # ...and absent, it does not


# --- the ways a row can look like a contact and not be one --------------------

def test_equal_faces_on_interpenetrating_masses_is_not_a_joint():
    s = _pair()
    by = {m["name"]: m for m in s["masses"]}
    by["bed"]["s"][0] += 400.0                # grow the bed THROUGH the panel
    by["bed"]["c"][0] += 200.0
    v = CC.check(s)
    assert any("overlap" in x and "arithmetic, not a joint" in x for x in v)


def test_coplanar_but_disjoint_never_meet():
    s = _pair()
    by = {m["name"]: m for m in s["masses"]}
    by["bed"]["c"][1] -= 4000.0               # slide the bed out of the panel's run
    v = CC.check(s)
    assert any("never meet" in x for x in v)


def test_two_axes_is_a_typo_not_a_joint():
    v = CC.check(_pair(b_face="z_min"))
    assert any("different axes" in x for x in v)


def test_unknown_mass_and_unknown_face_are_named():
    assert any("not a mass" in x for x in CC.check(_pair(b="nosuch")))
    assert any("not one of" in x for x in CC.check(_pair(a_face="x_middle")))


def test_a_mass_cannot_touch_itself():
    assert any("itself" in x for x in CC.check(_pair(b="bed")))


def test_a_row_declared_twice_is_refused():
    s = _pair()
    s["contacts"].append(dict(s["contacts"][0]))
    assert any("twice" in x for x in CC.check(s))


# --- the fields that make the row mean something ------------------------------

def test_datum_is_required_and_must_name_a_side():
    assert any("datum" in x for x in CC.check(_pair(datum=None)))
    assert any("datum" in x for x in CC.check(_pair(datum="panel")))


def test_why_is_required():
    assert any("no `why`" in x for x in CC.check(_pair(why="   ")))


def test_a_negative_gap_is_refused_by_name():
    assert any("negative gap" in x for x in CC.check(_pair(gap=-5.0)))


def test_a_contacts_block_that_is_not_a_list_fails_closed():
    v = CC.check({"masses": [], "contacts": {"a": "x"}})
    assert len(v) == 1 and "not a list" in v[0]


# --- the advisory sweep -------------------------------------------------------

def test_butt_contacts_finds_the_joint_and_ignores_the_floor():
    """z coincidence is 'everything stands on the floor' — placement_check's
    job. This one only reports joints in PLAN."""
    s = _pair()
    s["masses"].append(_mass("floor", (-2000, -3000, -50), (6000, 6000, 100)))
    found = CC.butt_contacts(s)
    assert ("bed", "panel", "x") in found
    assert all(ax == "x" or ax == "y" for _, _, ax in found)


def test_undeclared_counts_what_has_no_row():
    s = _pair()
    s["masses"].append(_mass("wall", (-1290.0, -3552.55, 441.475),
                             (48.0, 2005.1, 882.95)))    # butts the panel's back
    notes = CC.undeclared(s)
    assert len(notes) == 1, "the advisory is ONE line — see its docstring"
    assert "1 of 2 vertical butt joints" in notes[0]
    assert ("panel", "wall", "x") in CC.undeclared_pairs(s)
    assert ("bed", "panel", "x") not in CC.undeclared_pairs(s)


def test_undeclared_says_so_when_everything_is_declared():
    notes = CC.undeclared(_pair())
    assert len(notes) == 1 and notes[0].startswith("all 1 vertical butt")


# --- and the lane itself ------------------------------------------------------

def test_every_canonical_trn002_spec_satisfies_its_own_declared_contacts():
    """Walks EVERY round, not the newest — re-rendering a past round is how this
    lane catches regressions, and a contact register that only holds for the
    latest spec would break every earlier round the first time one is rebuilt."""
    specs = sorted(glob.glob(os.path.join(LANE, "spec_r*.json")))
    assert specs, "no TRN-002 specs found — the pin cannot run"
    bad = []
    for p in specs:
        with open(p, encoding="utf-8") as f:
            spec = json.load(f)
        v = CC.check(spec)
        if v:
            bad.append(f"{os.path.basename(p)}: {v[0]}")
    assert not bad, "\n".join(bad)
