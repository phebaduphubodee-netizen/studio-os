"""Tests for existence_check — R10 as rows.

Every test here pins a defect this repo has already paid for once, named in the
assertion message. The instrument is new; the failures it is built to refuse are not.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import existence_check as EX  # noqa: E402


def box(name, x0, y0, z0, x1, y1, z1, frustum=True):
    return {"name": name, "hidden_render": False, "in_frustum": frustum,
            "aabb": [[x0, y0, z0], [x1, y1, z1]]}


def scene(*objs):
    return list(objs)


def ledger(objects=(), required=(), baseline=0):
    return {"baseline_unrowed": baseline, "objects": list(objects),
            "required_elements": list(required)}


KEEP = {"identity": "a thing", "exists": "sheet:SR-01", "held_by": "floor",
        "verdict": "keep", "operable": False}


def test_an_object_in_frame_with_no_row_is_a_violation_once_the_backlog_ratchets():
    objs = scene(box("bed__base", 0, 0, 0, 2, 2, 0.6))
    v, _n, s = EX.check(objs, ledger(baseline=0))
    assert s["unrowed"] == 1
    assert any("no R10 row" in x or "carry no R10 row" in x for x in v), (
        "R9b: a rule that names the objects it applies to will always exempt the "
        "next one — the list must come from the scene")


def test_the_backlog_is_a_ratchet_and_day_one_does_not_hard_fail():
    """R13: a machine that hard-fails every historical instance on day one gets
    switched off and joins them."""
    objs = scene(box("a__x", 0, 0, 0, 1, 1, 1), box("b__x", 3, 3, 0, 4, 4, 1))
    v, _n, s = EX.check(objs, ledger(baseline=2))
    assert s["unrowed"] == 2 and not v, "at the baseline, the backlog only prints"
    objs2 = objs + scene(box("c__x", 6, 6, 0, 7, 7, 1))
    v2, _n2, _s2 = EX.check(objs2, ledger(baseline=2))
    assert any("RATCHETS" in x for x in v2), "a NEW object must arrive with its row"


def test_pending_is_refused_by_name():
    objs = scene(box("bed__base", 0, 0, 0, 2, 2, 0.6))
    for bad in ("pending", "TBD", "todo", "later"):
        row = dict(KEEP, assembly="bed", verdict=bad)
        v, _n, _s = EX.check(objs, ledger([row]))
        assert any("refused BY NAME" in x for x in v), bad


def test_a_named_support_that_does_not_exist_is_refused():
    """R3's `where` test applied to a load path: a decision in force nowhere was
    never taken."""
    objs = scene(box("bench__acq0", 0, 0, 0, 0.5, 0.7, 0.5))
    row = dict(KEEP, assembly="bench", held_by="plinth__that_was_never_built")
    v, _n, _s = EX.check(objs, ledger([row]))
    assert any("is not in the built scene" in x for x in v)


def test_a_named_support_that_exists_but_is_elsewhere_is_refused():
    objs = scene(box("bench__acq0", 0, 0, 0, 0.5, 0.7, 0.5),
                 box("rug__x", 9, 9, 0, 12, 12, 0.02))
    row = dict(KEEP, assembly="bench", held_by="rug")
    v, _n, _s = EX.check(objs, ledger([row, dict(KEEP, assembly="rug",
                                                 held_by="floor")]))
    assert any("does not touch bench" in x for x in v), (
        "the message NAMES the component whose carrier is missing (p2r62): with a "
        "family row covering mirror twins, 'it' was ambiguous about which twin")


def test_a_reveal_claim_is_MEASURED_and_can_be_wrong():
    """The positive control R11 demands: an absence rung that cannot demonstrate it
    sees a present one is not evidence. Here the gap is really 10 mm."""
    objs = scene(box("m__bay_drawer_front0", 0, 0, 0.0, 0.5, 0.02, 0.24),
                 box("m__bay_drawer_front1", 0, 0, 0.25, 0.5, 0.02, 0.49))
    good = dict(KEEP, assembly="m", operable=True,
                opens_by={"reveal_mm": 10, "between": "drawer_front"})
    v, notes, _s = EX.check(objs, ledger([good]))
    assert not v and any("the gap is really there" in n for n in notes)
    bad = dict(good, opens_by={"reveal_mm": 32, "between": "drawer_front"})
    v2, _n2, _s2 = EX.check(objs, ledger([bad]))
    assert any("measures 10.0 mm" in x for x in v2), (
        "a claimed 32 mm finger reveal against a measured 10 mm shadow gap is the "
        "p2r47 drawer item, and the row may not assert its way past it")


def test_an_unmeasurable_reveal_is_not_a_pass():
    objs = scene(box("m__bay_solid", 0, 0, 0, 0.5, 0.02, 0.49))
    row = dict(KEEP, assembly="m", operable=True,
               opens_by={"reveal_mm": 10, "between": "drawer_front"})
    v, _n, _s = EX.check(objs, ledger([row]))
    assert any("COULD NOT MEASURE" in x for x in v)


def test_push_to_open_must_cite_a_signed_decision():
    """D6-A signs 'flat handleless microcement', so demanding a pull would fail the
    owner's own decision — but an invisible mechanism asserted with no signature is
    indistinguishable from having forgotten the handle."""
    objs = scene(box("m__bay_drawer_front0", 0, 0, 0, 0.5, 0.02, 0.24))
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="m", operable=True,
                                            opens_by={"push_to_open": "yes"})]))
    assert any("decision row that signed it" in x for x in v)
    v2, _n2, _s2 = EX.check(objs, ledger([dict(KEEP, assembly="m", operable=True,
                                               opens_by={"push_to_open": "D-097"})]))
    assert not v2


def test_operable_with_no_mechanism_at_all_is_refused():
    objs = scene(box("m__bay_drawer_front0", 0, 0, 0, 0.5, 0.02, 0.24))
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="m", operable=True)]))
    assert any("declared operable with no" in x for x in v)


def test_remove_that_is_still_in_the_scene_is_a_violation():
    """A decision recorded and not carried out — this repo's oldest shape."""
    objs = scene(box("lamp__stem", 0, 0, 0, 0.1, 0.1, 0.8))
    row = dict(KEEP, assembly="lamp", verdict="remove")
    v, _n, _s = EX.check(objs, ledger([row]))
    assert any("STILL IN" in x for x in v)


def test_exists_must_point_at_something_and_thin_reasons_are_refused():
    objs = scene(box("x__a", 0, 0, 0, 1, 1, 1))
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="x", exists="it is nice")]))
    assert any("points at nothing" in x for x in v)
    v2, _n2, _s2 = EX.check(objs, ledger([dict(KEEP, assembly="x",
                                               exists="not-in-drawing: n/a")]))
    assert any("character reason is refused" in x for x in v2)


def test_fix_needs_a_named_action_and_unresolved_needs_an_age():
    objs = scene(box("bench__acq0", 0, 0, 0, 0.5, 0.7, 0.5))
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="bench", verdict="fix")]))
    assert any("no `fix_by`" in x for x in v), "a fix nobody named is a wish"
    v2, _n2, _s2 = EX.check(objs, ledger([dict(KEEP, assembly="bench",
                                               verdict="unresolved")]))
    assert any("no `since`" in x for x in v2)


def test_a_required_element_declared_present_must_actually_be_there():
    objs = scene(box("bed__base", 0, 0, 0, 2, 2, 0.6))
    req = [{"element": "skirting", "why_required": "the wall-floor junction is drawn "
            "on every interior elevation", "present_as": "skirt", "min_parts": 4}]
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="bed")], req))
    assert any("names nothing in the built scene" in x for x in v)
    objs2 = objs + scene(*[box(f"skirt__e0_{i}", i, 0, 0, i + 1, 0.02, 0.1)
                           for i in range(4)])
    v2, _n2, _s2 = EX.check(objs2, ledger(
        [dict(KEEP, assembly="bed"),
         dict(KEEP, assembly="skirt", held_by="floor")], req))
    assert not v2, "four runs present, and the row now holds"


def test_a_required_element_may_not_be_silent():
    objs = scene(box("bed__base", 0, 0, 0, 2, 2, 0.6))
    req = [{"element": "sockets", "why_required": "the sconces are lit and something "
            "must switch them"}]
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="bed")], req))
    assert any("silence is the one state" in x for x in v)


def test_out_of_frustum_objects_need_no_row_but_unknown_ones_do():
    """The vacuous-zero law: absence of evidence must never read as clearance."""
    objs = scene(box("far__thing", 40, 40, 0, 41, 41, 1, frustum=False))
    v, _n, s = EX.check(objs, ledger(baseline=0))
    assert s["in_frame"] == 0 and not v
    unknown = [dict(box("far__thing", 40, 40, 0, 41, 41, 1))]
    del unknown[0]["in_frustum"]
    v2, _n2, s2 = EX.check(unknown, ledger(baseline=0))
    assert s2["in_frame"] == 1 and v2


def test_two_rows_for_one_object_is_refused():
    objs = scene(box("bed__base", 0, 0, 0, 2, 2, 0.6))
    v, _n, _s = EX.check(objs, ledger([dict(KEEP, assembly="bed"),
                                       dict(KEEP, assembly="bed",
                                            verdict="remove")]))
    assert any("two rows" in x for x in v)


def test_the_shipped_ledger_and_the_shipped_dump_agree():
    """The instrument is pointed at the real files, not only at fixtures. It must at
    minimum LOAD both and produce a summary; a violation here is a finding, not a
    test failure, so only the could-not-run states are asserted."""
    repo = EX.REPO
    dump = os.path.join(repo, "pipeline/output/room_bedroom_suite_eye_p2r47.scene.json")
    if not os.path.exists(dump):
        return
    led = EX.load_ledger()
    objs = EX.load_dump(dump)
    _v, _n, s = EX.check(objs, led)
    assert s["assemblies"] > 0 and s["rows"] > 0
    assert s["baseline_unrowed"] is not None, (
        "the ledger must declare a baseline or the backlog has no ratchet")


def test_selftest_measures_a_reveal_that_is_there():
    assert EX.selftest() == 0


# --- a FAMILY row's load path, per component (p2r62) ---------------------------
# Collapsing the two bedside-lamp rows into one `nightstand` family row made the
# held_by test RUN for the first time (an exact-coordinate key never resolves in
# `by_name`, which is prefix-keyed, so those rows had never had a load path
# measured) — and it immediately reported a broken one for two lamps each sitting
# squarely on their own table. The cause was `by_name` collapsing a prefix to its
# LARGEST component: mirror twins have equal footprints, so "the largest" is an
# arbitrary one of them and the check compared a NORTH lamp against a SOUTH table.

def _twins(off_north=0.0, off_south=0.0):
    """Two tables and two lamps, mirrored across the room. Either offset slides that
    lamp off its own table without touching anything else."""
    return scene(
        box("side_table@0,0", 0.0, 0.0, 0.0, 0.4, 0.4, 0.40),
        box("side_table@0,3", 0.0, 3.0, 0.0, 0.4, 3.4, 0.40),
        box("nightstand@0,0", 0.08, 0.08 + off_south, 0.40, 0.32, 0.32 + off_south, 0.78),
        box("nightstand@0,3", 0.08, 3.08 + off_north, 0.40, 0.32, 3.32 + off_north, 0.78),
    )


def _family_row(**kw):
    return dict(KEEP, assembly="nightstand", held_by="side_table",
                exists="not-in-drawing: the plan draws the table, not the lamp on it",
                **kw)


def _table_rows():
    return [dict(KEEP, assembly="side_table@0,0"), dict(KEEP, assembly="side_table@0,3")]


def test_a_family_row_does_not_report_twins_as_a_broken_load_path():
    v, _n, _s = EX.check(_twins(), ledger([_family_row()] + _table_rows()))
    assert not [x for x in v if "does not touch" in x], (
        "each twin is on its own carrier; comparing one arbitrary representative "
        "against another is a coin flip, not a measurement: " + repr(v))


def test_a_family_row_fails_when_ANY_component_has_no_carrier_under_it():
    """The whole point of the family form: it must be STRICTLY MORE checked than the
    coordinate form it replaced, not less. EITHER twin, not just whichever one the
    scene happens to build first — a first-component-only check passes half the
    broken load paths and reads exactly like a check that ran.
    """
    for label, kw in (("south", {"off_south": 1.2}), ("north", {"off_north": 1.2})):
        v, _n, _s = EX.check(_twins(**kw), ledger([_family_row()] + _table_rows()))
        bad = [x for x in v if "does not touch" in x]
        assert bad, f"the {label} lamp is floating over open floor and nothing said so"
        assert "nightstand@" in bad[0], (
            "the message must name WHICH component lost its carrier: " + bad[0])


def test_an_exact_coordinate_row_still_gets_its_own_carrier_checked():
    row = dict(KEEP, assembly="nightstand@0,0", held_by="side_table@0,3",
               exists="not-in-drawing: the plan draws the table, not the lamp on it")
    v, _n, _s = EX.check(_twins(), ledger([row] + _table_rows()))
    assert [x for x in v if "does not touch" in x], (
        "a row pointing at the carrier ACROSS THE ROOM must still fail")


def test_components_resolves_a_prefix_and_prefers_an_exact_name():
    asms = EX.assemblies(_twins())
    assert len(EX.components("nightstand", asms)) == 2
    assert [a["name"] for a in EX.components("nightstand@0,0", asms)] == ["nightstand@0,0"]
    assert EX.components("nothing_here", asms) == []
