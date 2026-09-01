"""carry_check — WHAT CARRIES THIS MASS.

Every test below is a control on geometry this lane actually shipped, not on a
convenient synthetic. The two that matter most are the pair at the top: the SAME
rail fails before the p2r85 fix and passes after it, and the coat hanging on it
never becomes its carrier.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carry_check as CC                                    # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def box(name, x0, y0, z0, dx, dy, dz, frustum=True):
    return {"name": name, "min": [x0, y0, z0], "max": [x0 + dx, y0 + dy, z0 + dz],
            "in_frustum": frustum}


FLOOR = box("floor", 0, 0, -100, 4000, 3000, 100)
GABLE_L = box("gable_l", 0, 0, 0, 18, 600, 2400)
GABLE_R = box("gable_r", 1000, 0, 0, 18, 600, 2400)
# the p2r84 rail, to the millimetre: cell [18, 1000], rail inset 40 at each end
RAIL_SHORT = box("rail_p2r84", 58, 270, 1850, 924, 30, 30)
# the p2r85 rail: the cell's true clear span, 2 mm into each gable
RAIL_LANDED = box("rail_p2r85", 16, 270, 1850, 1006, 30, 30)


def how_of(objs):
    how, _ = CC.carriers(objs)
    return how


# --------------------------------------------------------------- the defect

def test_the_p2r84_rail_is_carried_by_nothing():
    """40 mm short of BOTH gables. Nine of these shipped in every frame this lane
    produced, and no rung in the repo could say so."""
    assert how_of([FLOOR, GABLE_L, GABLE_R, RAIL_SHORT])["rail_p2r84"] is None


def test_the_p2r85_rail_is_carried_by_its_gables():
    assert how_of([FLOOR, GABLE_L, GABLE_R, RAIL_LANDED])["rail_p2r85"] == "ANCHORED-TO"


def test_a_coat_never_becomes_the_rail_it_hangs_on():
    """THE HOLE THIS MODULE EXISTS TO CLOSE. `placement_check`'s FLOATING branch
    excused two of the nine rails because the garments hanging on them counted as
    contact — the graph read rail -> garment -> gable -> floor and called it
    supported. A mass excused by the load it carries."""
    coat = box("coat", 300, 200, 1000, 400, 140, 890)
    coat["max"][2] = 1890                                  # hook crown over the rail
    how = how_of([FLOOR, GABLE_L, GABLE_R, RAIL_SHORT, coat])
    assert how["rail_p2r84"] is None, "the coat must not hold up the rail"
    assert how["coat"] is None, "a coat on a floating rail is itself floating"


def test_the_same_coat_hangs_once_the_rail_lands():
    how = how_of([FLOOR, GABLE_L, GABLE_R, RAIL_LANDED, box("coat", 300, 200, 1000,
                                                            400, 140, 890)])
    assert how["rail_p2r85"] == "ANCHORED-TO"
    coat = box("coat", 300, 200, 1000, 400, 140, 890)
    coat["max"][2] = 1890
    how = how_of([FLOOR, GABLE_L, GABLE_R, RAIL_LANDED, coat])
    assert how["coat"] == "HUNG-ON"


def test_a_four_mm_hanger_plate_still_counts_as_hung():
    """MEASURED, not assumed: the garment sets in this room import their hanger as a
    4 mm plate over a 30 mm rail. The first cut of HUNG-ON demanded a 5 mm overlap on
    every axis and read seven real hangers as hanging on nothing. What makes it a
    hook is that it reaches OVER the member, not how thick it is."""
    hook = box("hook", 400, 276, 1820, 4, 18, 74)           # 4 mm plate, crown at 1894
    how = how_of([FLOOR, GABLE_L, GABLE_R, RAIL_LANDED, hook])
    assert how["hook"] == "HUNG-ON"


# --------------------------------------------------------------- asymmetry (1)

def test_anchoring_does_not_chain():
    """Leaning on a wall makes you stable; it does not make you a wall. Without
    this, a garment brushing a gable became a column that could then carry the rail
    it hangs from — and the defect this file exists for read GREEN."""
    # a garment that brushes the gable laterally: carried, but never an anchor
    coat = box("coat", 18, 200, 1000, 300, 140, 900)
    how, col = CC.carriers([FLOOR, GABLE_L, GABLE_R, RAIL_SHORT, coat])
    assert how["coat"] is not None, "a coat against the gable is carried"
    assert "coat" not in col, "and it is NOT a column"
    assert how["rail_p2r84"] is None, "so it cannot carry the rail"


def test_a_column_is_the_ground_or_what_rests_on_it():
    _, col = CC.carriers([FLOOR, GABLE_L, GABLE_R])
    assert col == {"floor", "gable_l", "gable_r"}


# --------------------------------------------------------------- the member test

@pytest.mark.parametrize("dims,expect", [
    ((924, 30, 30), 0),        # a hang rail
    ((30, 689, 30), 1),        # the same rail on the other axis
    ((6000, 110, 2800), None),  # a WALL is not a rail you hang things on
    ((650, 600, 18), None),    # nor a shelf
    ((18, 600, 2400), None),   # nor a vertical gable — you do not hang a coat on a post
    ((48, 14, 48), None),      # nor a rail's own socket flange
])
def test_member_axis_separates_rails_from_everything_else(dims, expect):
    assert CC.member_axis(box("x", 0, 0, 0, *dims)) == expect


# --------------------------------------------------------------- correct construction

def test_correct_construction_does_not_appear_in_the_report():
    """Six relations, six things a builder does. If any of these read as UNCARRIED
    the rung would be shouting at the frame instead of at the defect."""
    ceil = box("ceil", 0, 0, 2800, 4000, 3000, 50)
    wall = box("wall", 0, -110, 0, 4000, 110, 2900)
    shelf = box("shelf", 18, 0, 1200, 982, 600, 18)
    objs = [FLOOR, GABLE_L, GABLE_R, wall, ceil, shelf,
            box("book", 100, 100, 1218, 150, 200, 220),          # RESTS-ON
            box("trim", 500, 500, 2794, 96, 96, 6),              # HANGS-FROM
            box("strip", 200, 100, 1196, 400, 10, 4),            # HANGS-FROM (casework)
            box("mirror", 20, 590, 100, 900, 6, 2000),           # FIXED-IN the wall? no: face
            box("plate", 300, -1, 700, 86, 12, 86),              # ANCHORED-TO the wall
            box("front", 20, 0, 60, 400, 20, 200),               # FASTENED-TO a body
            box("body", 20, 20, 0, 400, 500, 700)]
    how = how_of(objs)
    unc = [n for n, v in how.items() if v is None]
    assert unc == [], f"correct construction reported as uncarried: {unc}"


def test_it_is_not_vacuously_empty():
    """A rung whose pass is 'we found nothing' must show it can fire on the same
    population (D-056). One floating mass among correct construction."""
    objs = [FLOOR, GABLE_L, GABLE_R, box("lamp_in_midair", 400, 300, 1500, 200, 200, 300)]
    assert how_of(objs)["lamp_in_midair"] is None


# --------------------------------------------------------------- the ledger

@pytest.mark.parametrize("row,why", [
    ({"prefix": "x", "verdict": "pending", "why": "w", "since": "d", "covers_n": 1},
     "'pending' is refused by name"),
    ({"prefix": "x", "verdict": "fix", "why": "w", "since": "d", "covers_n": 1},
     "fix with no restart_by is a shrug"),
    ({"prefix": "x", "verdict": "fix", "why": "w", "since": "d", "restart_by": "r"},
     "no covers_n means the row hides every new instance"),
    ({"prefix": "x", "verdict": "signed-gap", "why": "w", "since": "d", "covers_n": 1},
     "a signed gap must cite what signed it"),
    ({"prefix": "x", "verdict": "fix", "why": "w", "restart_by": "r", "covers_n": 1},
     "no since means the defect never prints its age"),
    ({"verdict": "fix", "why": "w", "since": "d", "restart_by": "r", "covers_n": 1},
     "a row that names nothing cannot be matched to anything"),
])
def test_the_ledger_refuses_a_dishonest_row(row, why):
    with pytest.raises(ValueError):
        CC.load_ledger_rows([row])


def test_a_stale_row_fails():
    """A ledger is a queue, and a queue nobody empties is this repo's own signature
    defect. A row for a mass that is carried again must be deleted in the commit
    that fixed it."""
    led = CC.load_ledger_rows([{"prefix": "gable", "verdict": "fix", "why": "w",
                                "since": "2026-08-27", "restart_by": "r",
                                "covers_n": 1}])
    v, _, _ = CC.check([FLOOR, GABLE_L, GABLE_R], led)
    assert any("STALE" in x for x in v)


def test_a_row_may_not_absorb_new_instances():
    led = CC.load_ledger_rows([{"prefix": "rail", "verdict": "fix", "why": "w",
                                "since": "2026-08-27", "restart_by": "r",
                                "covers_n": 1}])
    two = box("rail_second", 58, 400, 1050, 924, 30, 30)
    v, _, _ = CC.check([FLOOR, GABLE_L, GABLE_R, RAIL_SHORT, two], led)
    assert any("BACKLOG ROSE" in x for x in v)


def test_an_unrowed_uncarried_mass_is_a_violation():
    v, _, s = CC.check([FLOOR, GABLE_L, GABLE_R, RAIL_SHORT], [])
    assert s["uncarried"] == 1 and len(v) == 1 and "UNCARRIED" in v[0]


# --------------------------------------------------------------- the contract

def test_a_placement_dump_schema_is_refused_not_read_as_empty():
    """The schema without `aabb` is what placement_dump writes. Reading zero masses
    out of it and printing OK is the vacuous zero this repo keeps rebuilding."""
    import tempfile
    fd, p = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"objects": [{"name": "a", "type": "MESH",
                                "min": [0, 0, 0], "max": [1, 1, 1]}]}, f)
    try:
        with pytest.raises(ValueError):
            CC.load_dump(p)
    finally:
        os.unlink(p)


def test_could_not_run_exits_2_not_0():
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "pipeline", "scripts", "carry_check.py"),
                        os.path.join(REPO, "no", "such", "dump.json")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "COULD NOT RUN" in r.stdout


def test_selftest_passes():
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "pipeline", "scripts", "carry_check.py"),
                        "--selftest"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_render_path_spawns_it_and_hard_stops_on_2():
    """R11's sentence, applied here: 'could not look' must never print like 'looked
    and it was fine'. The wiring is asserted against the CODE, not a comment.

    MECHANISM CHANGED 2026-08-27, PROPERTY UNCHANGED (ORD-2026-08-27-every-round-
    sees-what-it-changed, item D). Both branches used to call `os._exit(1)` on the
    spot; they now call `_stop(...)`, and `_score_deliverable` takes every recorded
    stop together at the end. The reason is that exiting on the spot silenced every
    instrument after the one that fired — including the round's only EYE, which is
    why p2r83/p2r84/p2r86 carry no gen-diff artefact.

    This test now pins the property rather than the keyword, and pins it in TWO
    halves on purpose: a `_stop()` that nothing ever reads would satisfy the first
    half alone and would be a gate turned into a warning, which is the exact defect
    this repo has shipped before ("declared mandatory and then printed as a
    suggestion for a human to copy").
    """
    src = open(os.path.join(REPO, "pipeline", "scripts", "build_room.py"),
               encoding="utf-8").read()
    assert '"carry_check.py")' in src, "spawned as an argv element, not mentioned"
    blk = src.split('"carry_check.py")', 1)[1].split("# ---- FRONT DOOR", 1)[0]
    assert "_cy.returncode == 2" in blk and "_cy.returncode == 1" in blk
    # half 1: both exit codes still REFUSE the frame (neither is merely printed)
    assert blk.count("_stop(") == 2, "both exit codes are hard stops"
    # half 2: and the refusals are actually taken, with a real non-zero exit
    assert "if _stops:" in src, "_stops is filled and never read — a stop that stopped"
    tail = src.split("if _stops:", 1)[1][:600]
    assert "os._exit(1)" in tail, "the recorded stops no longer exit the build"


def test_the_repo_ledger_and_the_committed_frame_agree():
    """The ledger is not a document: it is checked against the frame of record. If
    this fails, either the scene moved or a row went stale — both are the point."""
    dump = os.path.join(REPO, "pipeline", "output",
                        "room_bedroom_suite_eye_p2r85.scene.json")
    if not os.path.exists(dump):
        pytest.skip("p2r85 frame of record not on this machine")
    objs = CC.load_dump(dump)
    led = CC.load_ledger(os.path.join(REPO, "qa", "carry-ledger.json"))
    v, _, _ = CC.check(objs, led)
    assert v == [], v


# --------------------------------------------------------------------------
# THE ZERO-MASS ROUTES. `load_dump` used to refuse exactly ONE of the ways it can
# come back with nothing, and the other two mattered more than the one it caught:
# with no names to match, `check()` files EVERY ledger row as LEDGER STALE, whose
# own text tells the reader to delete it "in the commit that fixed it". A scene
# this module could not read was therefore reported as a scene in which all nine
# open defects were FIXED.

def _dump_file(tmp_path, doc):
    p = tmp_path / "d.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


def test_a_dump_whose_top_key_is_not_objects_is_refused(tmp_path):
    """Schema drift. `doc.get("objects", ...)` yields [] and the old guard, which
    began `if objs and ...`, never armed."""
    with pytest.raises(ValueError, match="no objects at all"):
        CC.load_dump(_dump_file(tmp_path, {"OBJECTS": [
            {"name": "a", "aabb": [[0, 0, 0], [1, 1, 1]]}]}))


def test_a_dump_in_which_everything_is_hidden_is_refused(tmp_path):
    """`objs` is non-empty and `seen_aabb` is True, so the old guard was bypassed
    by design and returned an empty list — indistinguishable from a clean scene."""
    with pytest.raises(ValueError, match="hidden_render"):
        CC.load_dump(_dump_file(tmp_path, {"objects": [
            {"name": "a", "hidden_render": True,
             "aabb": [[0, 0, 0], [1, 1, 1]]}]}))


def test_a_placement_dump_handed_in_by_mistake_is_still_refused(tmp_path):
    """The one route the original guard did cover. It must keep working."""
    with pytest.raises(ValueError, match="aabb"):
        CC.load_dump(_dump_file(tmp_path, {"objects": [
            {"name": "a", "min": [0, 0, 0], "max": [1, 1, 1]}]}))


def test_a_real_dump_still_loads(tmp_path):
    """POSITIVE CONTROL. Without it, a `load_dump` that raised unconditionally
    would pass all three tests above."""
    got = CC.load_dump(_dump_file(tmp_path, {"objects": [
        {"name": "a", "aabb": [[0, 0, 0], [1, 1, 1]]}]}))
    assert [o["name"] for o in got] == ["a"]
    assert got[0]["max"] == [1000.0, 1000.0, 1000.0]      # metres -> mm
