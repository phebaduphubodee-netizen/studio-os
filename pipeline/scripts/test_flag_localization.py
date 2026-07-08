"""
test_flag_localization.py -- F7 harness tests on SYNTHETIC minimal specs ONLY.

Deliberately independent of the v4 project data AND of the parallel pane's in-flight rebuild_diff
edits: every spec is hand-built here, so a red bar means F7's own logic broke, never that a fixture
moved. We test what the IMPORTED suite modules actually do (never a hard-coupled copy of a threshold),
and we assert the two-layer law (signing the mutated value quiets the loud flag) directly against
rebuild_diff so the suppression contract is pinned at the source.

Run:  python -m pytest test_flag_localization.py -q   (cwd = pipeline/scripts)
"""
import copy
import json

import pytest

import flag_localization as F
import rebuild_diff as RD

# The box-180 fold (rebuild_diff._is_box_render) lives in an uncommitted sibling edit at the time F7
# was written. These two tests exercise the REAL imported module, so on a clean checkout that lands
# F7 BEFORE the fold they would go red for a commit-ordering reason, not a logic defect. Skip (never
# fail) when the fold is absent so F7 can be committed independently; when the fold is present they run
# for real and still catch a regression that DROPS it.
_HAS_BOX_FOLD = hasattr(RD, "_is_box_render")
_needs_box_fold = pytest.mark.skipif(
    not _HAS_BOX_FOLD,
    reason="rebuild_diff box-180 fold (_is_box_render) absent in this checkout -- box-flip probe N/A")


def base_spec():
    """A clean, correct read: a directional sofa + a render-symmetric coffee table, both drawn well
    INSIDE a rectangular sitting room. Every field the mutations touch (rot/kind/w/d/zone) is present
    and sane, so any NEW flag a run raises is attributable to the injected error, not to ambient junk."""
    return {
        "schema": "interior-ai/room-spec@0.2",
        "room": {"type": "sitting_room",
                 "outline_mm": [[0, 0], [6000, 0], [6000, 5000], [0, 5000]]},
        "builtins": [],
        "items": [
            {"name": "sofa1", "kind": "sofa", "x": 2000, "y": 2000, "w": 2000, "d": 900, "rot": 0},
            {"name": "table1", "kind": "coffee_table", "x": 2200, "y": 3200,
             "w": 1000, "d": 600, "rot": 0},
        ],
        "subrooms": [],
    }


def _run(classes, confirmed=None):
    return F.run_localization([("sitting_room", base_spec())], confirmed or [], classes=classes)


# ---- should-flag classes: recall + expected collector + band ---------------------------
def test_facing_flip_directional_hits_rebuild_critical():
    rep = _run(["facing_flip_directional"])
    a = rep["per_class"]["facing_flip_directional"]
    assert a["n_mutations"] == 1                       # only the sofa is directional
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    h = a["hits"][0]
    assert h["caught_by"] == ["rebuild_diff"]
    assert "CRITICAL" in h["got_severity"]            # a 180 flip of a directional piece = reversal


def test_kind_change_unsigned_hits_rebuild_high():
    rep = _run(["kind_change_unsigned"])
    a = rep["per_class"]["kind_change_unsigned"]
    assert a["n_mutations"] == 2                       # both items carry a kind
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    for h in a["hits"]:
        assert "rebuild_diff" in h["caught_by"]
        assert "HIGH" in h["got_severity"]


def test_kind_change_vs_signature_caught_but_HIGH_not_critical():
    # The mutation auto-appends a confirmed[] entry signing the ORIGINAL kind, then contradicts it.
    # HONESTY: within the tier-1 suite this is rebuild_diff HIGH, NOT the CRITICAL kind_regression band
    # (that band is placement_gate's -> self_audit.collect_gate, which F7 does not run). We assert the
    # REAL behaviour and that the expected-CRITICAL vs got-HIGH gap is visible (severity_match == 0).
    rep = _run(["kind_change_vs_signature"], confirmed=[])
    a = rep["per_class"]["kind_change_vs_signature"]
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    assert a["n_caught_by_expected"] == a["n_hit"]     # rebuild_diff (the expected collector) caught it
    assert a["n_severity_match"] == 0                  # expected CRITICAL, got HIGH -> the honest gap
    for h in a["hits"]:
        assert "rebuild_diff" in h["caught_by"] and "HIGH" in h["got_severity"]


def test_size_implausible_hits_anomaly_high():
    rep = _run(["size_implausible"])
    a = rep["per_class"]["size_implausible"]
    assert a["n_mutations"] == 2                       # sofa + coffee_table both have a built-in bound
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    for h in a["hits"]:
        assert "anomaly" in h["caught_by"] and "HIGH" in h["got_severity"]


def test_rot_stripped_directional_hits_confidence():
    rep = _run(["rot_stripped_directional"])
    a = rep["per_class"]["rot_stripped_directional"]
    assert a["n_mutations"] == 1                       # only the sofa is a facing-kind
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    assert "confidence" in a["hits"][0]["caught_by"]


def test_zone_below_grade_unsigned_hits_cross_signal():
    rep = _run(["zone_below_grade_unsigned"])
    a = rep["per_class"]["zone_below_grade_unsigned"]
    assert a["n_mutations"] == 2                       # both pieces are drawn inside the outline
    assert F._ratio(a["n_hit"], a["n_mutations"]) == 1.0
    for h in a["hits"]:
        assert "cross_signal" in h["caught_by"]


# ---- precision + the over-fire (nonflag) probe -----------------------------------------
def test_precision_single_item_is_on_target():
    # Only ONE item is mutated per run; every new flag must be ABOUT that item -> precision 1.0.
    rep = _run(["facing_flip_directional"])
    a = rep["per_class"]["facing_flip_directional"]
    assert a["n_new_flags_total"] >= 1
    assert F._ratio(a["n_new_flags_on_target"], a["n_new_flags_total"]) == 1.0


@_needs_box_fold
def test_facing_flip_box_does_not_overfire():
    # A 180 flip of a render-symmetric coffee table is byte-identical mesh. The IMPORTED rebuild_diff
    # folds a non-directional piece's rot into its 180 symmetry (_is_box_render) and abstains, so no
    # flag should fire. This is the "bench-180 false-CRITICAL" specificity guard. If the imported
    # rebuild_diff ever dropped that fold, this test would go red -- exactly the regression we want to
    # catch, NOT a hard-coupled copy of the fold. We also confirm the fold at the source below.
    rep = _run(["facing_flip_box"])
    a = rep["per_class"]["facing_flip_box"]
    assert a["n_mutations"] == 1                       # only the coffee table is a non-directional box
    assert a["overfires"] == []


@_needs_box_fold
def test_imported_rebuild_folds_box_180_flip():
    # Pin the assumption the over-fire test rests on, read from the IMPORTED module (not re-declared):
    # a non-directional kind flipped 180 yields no unexplained record; a directional one yields CRITICAL.
    box = {"name": "t", "kind": "coffee_table", "x": 0, "y": 0, "w": 1000, "d": 600, "rot": 0}
    box2 = dict(box, rot=180)
    recs = RD.diff_rounds([{"room": {"type": "r"}, "items": [box]}],
                          [{"room": {"type": "r"}, "items": [box2]}])
    assert not [r for r in recs if r["signal"] == "rebuild_diff:semantic_change_unexplained"]
    seat = {"name": "s", "kind": "sofa", "x": 0, "y": 0, "w": 2000, "d": 900, "rot": 0}
    seat2 = dict(seat, rot=180)
    recs2 = RD.diff_rounds([{"room": {"type": "r"}, "items": [seat]}],
                           [{"room": {"type": "r"}, "items": [seat2]}])
    assert any(r["signal"] == "rebuild_diff:semantic_change_unexplained" and r["severity"] == "CRITICAL"
               for r in recs2)


# ---- two-layer law: signing the MUTATED value suppresses the loud flag ------------------
def test_signing_the_mutated_value_suppresses():
    spec = base_spec()
    loc = ("items", 0)                                 # sofa1
    mutated, _ke = F.mut_facing_flip_directional(spec, loc)
    new_rot = F._get(mutated, loc)["rot"]              # the flipped value the owner must sign to quiet it
    it = F._get(mutated, loc)
    sign = [{"name": "sofa1", "rot": new_rot, "w": it["w"], "d": it["d"],
             "by": "owner", "date": "2026-07-08"}]

    loud = RD.diff_rounds([spec], [mutated], confirmed=[])
    assert any(r["signal"] == "rebuild_diff:semantic_change_unexplained" and r["severity"] == "CRITICAL"
               for r in loud)                          # unsigned -> loud CRITICAL
    quiet = RD.diff_rounds([spec], [mutated], confirmed=sign)
    assert not [r for r in quiet if r["signal"] == "rebuild_diff:semantic_change_unexplained"]
    assert any(r["signal"] == "rebuild_diff:semantic_change_signed" for r in quiet)  # LOW provenance only


# ---- determinism -----------------------------------------------------------------------
def test_two_runs_are_identical():
    r1 = _run(list(F.ALL_CLASSES))
    r2 = _run(list(F.ALL_CLASSES))
    assert json.dumps(r1, ensure_ascii=False, sort_keys=True) == \
           json.dumps(r2, ensure_ascii=False, sort_keys=True)


# ---- skips are counted (ineligible items never silently vanish) ------------------------
def test_ineligible_items_are_counted_as_skips():
    # facing_flip_directional: the coffee table is ineligible -> exactly one skip recorded.
    rep = _run(["facing_flip_directional"])
    a = rep["per_class"]["facing_flip_directional"]
    assert a["n_skipped"] == 1 and a["n_mutations"] == 1


# ---- honesty: a should-flag lane with ZERO eligible items is 'unwired', not clean ------
def _box_only_spec():
    """A room whose ONLY piece is a render-symmetric coffee table -> no directional/facing item, so
    facing_flip_directional and rot_stripped_directional skip every item (n_mutations == 0)."""
    return {"schema": "interior-ai/room-spec@0.2",
            "room": {"type": "sitting_room",
                     "outline_mm": [[0, 0], [6000, 0], [6000, 5000], [0, 5000]]},
            "builtins": [],
            "items": [{"name": "table1", "kind": "coffee_table",
                       "x": 2200, "y": 3200, "w": 1000, "d": 600, "rot": 0}],
            "subrooms": []}


def test_zero_eligible_class_is_reported_unwired_not_blind():
    rep = F.run_localization([("sitting_room", _box_only_spec())], [],
                             classes=["facing_flip_directional"])
    a = rep["per_class"]["facing_flip_directional"]
    assert a["n_mutations"] == 0 and a["n_skipped"] == 1     # nothing eligible -> never exercised
    s = rep["summary"]
    assert "facing_flip_directional" in s["unwired_classes"]  # surfaced as unwired ...
    assert "facing_flip_directional" not in s["blind_classes"]  # ... and NOT mistaken for blind
    assert s["n_exercised_classes"] == 0 and s["n_should_flag_classes"] == 1
    assert s["macro_recall"] is None                        # no exercised lane -> no false all-clean


# ---- honesty: by-expected recall is surfaced beside macro_recall (backstop can't hide) --
def test_by_expected_recall_is_surfaced():
    rep = _run(["zone_below_grade_unsigned"])
    s = rep["summary"]
    assert "macro_recall_by_expected" in s and "backstopped_classes" in s
    a = rep["per_class"]["zone_below_grade_unsigned"]
    # cross_signal (the target collector) actually fires here, so by-expected == overall and the lane
    # is NOT backstopped -- the metric only lights up when the target collector goes silent.
    assert a["n_caught_by_expected"] == a["n_hit"]
    assert s["macro_recall_by_expected"] == s["macro_recall"]
    assert "zone_below_grade_unsigned" not in s["backstopped_classes"]
