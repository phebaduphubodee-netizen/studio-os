"""Tests for room_masses — the adapter that lets rule_gate see a ROOM spec.

The thing being guarded against is the adapter INVENTING provenance. An adapter
that hands every object a plausible `prov` would turn R10 into a rubber stamp on
the one lane it was wired for, which is worse than the gate never running.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import room_masses as RM  # noqa: E402
import rule_gate as RG  # noqa: E402


# --- the provenance ladder, most authoritative first --------------------------

def test_ink_coordinates_read_as_measured():
    prov, why = RM.prov_from({"note": "ELEMENT 3: bench (INK x2654.5-3152.8 "
                                      "y625.8-1625.6, was spec 504x1002)"})
    assert prov.startswith("M(ink:") and "2654.5" in prov
    assert why is None


def test_an_ink_verb_without_coordinates_still_reads_as_measured():
    prov, _ = RM.prov_from({"note": "TRIM REVERSED 2026-07-16 on ink (was x5150)"})
    assert prov.startswith("M(ink read of record:")


def test_a_named_element_file_reads_as_measured():
    prov, _ = RM.prov_from({"note": "from element2-west-wall_ink-read-2026-07-17.json"})
    assert prov.startswith("M(") and "element2" in prov


def test_a_bf_id_reads_as_derived_from_the_DD_set():
    prov, _ = RM.prov_from({"bf": "BF10", "note": "dressing cabinet between "
                                                  "BF11 and BF09-2"})
    assert prov.startswith("D(BF10")


def test_an_owner_decision_with_no_sourced_dimensions_is_a_DECLARED_assumption():
    # The owner saying a stool belongs there does not say where w/d/h came from.
    # R10's answer to that is a declared assumption carrying a why — not an M.
    prov, why = RM.prov_from({"note": "vanity stool at the BF11 makeup table "
                                      "(owner 07-16, ex 'desk chair')"})
    assert prov.startswith("A(owner decision 07-16")
    assert why and "stool" in why


def test_an_object_whose_note_names_no_source_gets_NO_prov():
    # THE POINT OF THE WHOLE MODULE. A note that says only where a thing sits has
    # not said where its numbers came from, and inventing one here would make the
    # gate a rubber stamp.
    prov, why = RM.prov_from({"note": "sits against the south wall, left of the door"})
    assert prov is None and why is None


def test_an_object_with_no_note_at_all_gets_NO_prov():
    assert RM.prov_from({}) == (None, None)


# --- shape ---------------------------------------------------------------------

def test_a_trn002_shaped_spec_is_not_a_room_spec():
    # It must not be adapted into an empty mass list: empty reads to the gate as
    # a spec with nothing in it, which is a mute wearing the shape of a pass.
    assert RM.is_room_spec({"masses": [{"name": "wall"}]}) is False


def test_a_spec_with_items_is_a_room_spec():
    assert RM.is_room_spec({"items": [{"name": "bed"}]}) is True


def test_masses_carry_centre_and_size_when_the_geometry_is_there():
    m = RM.masses({"items": [{"name": "bed", "x": 100, "y": 200,
                              "w": 2000, "d": 2100, "h": 600,
                              "note": "INK x1.0"}]})[0]
    assert m["c"] == [100, 200, 300.0] and m["s"] == [2000, 2100, 600]


def test_builtins_come_before_items_and_the_order_is_stable():
    spec = {"items": [{"name": "i1"}], "builtins": [{"name": "b1"}]}
    assert [m["name"] for m in RM.masses(spec)] == ["b1", "i1"]


# --- the guard must be able to fail, and to pass ---------------------------------

def test_an_unprovenanced_object_reaches_rule_gate_as_a_violation():
    gs = RM.as_gate_spec({"items": [{"name": "mystery console",
                                     "note": "against the north wall"}]})
    v = RG.audit_spec(gs)
    assert len(v) == 1 and "no `prov`" in v[0]


def test_the_canonical_deliverable_spec_passes_R10():
    # The spec DELIV-001 renders. It has been ink-trued and owner-confirmed, and
    # it passes — so wiring this gate hard does not block the lane it was built
    # for. Measured 2026-08-10: 11 masses, 0 violations.
    p = os.path.join(RG.REPO_ROOT, "projects", "PRJ-2026-002_c001-house",
                     "03_layout", "master-suite.CANONICAL.spec.json")
    if not os.path.isfile(p):
        return
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    gs = RM.as_gate_spec(spec, p)
    assert len(gs["masses"]) == 11
    assert RG.audit_spec(gs) == []
