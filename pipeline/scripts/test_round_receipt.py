"""Tests for round_receipt.py — the artefact an order about a recurring action can name.

WHY IT EXISTS, in one number: of 82 `obeyed_assert` entries across 37 owner orders, 3
name an artefact and 55 match a constant, a comment or a docstring. Twenty of the 37 rows
are held up by nothing a pipeline run could ever change — including the order R11 itself
came from, which is proven today by grepping for a symbol.
"""

import json
import os

import pytest

import round_receipt as RR


def _full(name="r1", **rungs):
    r = RR.new(name, quick=False, frame=True)
    for k, v in rungs.items():
        RR.note(r, k, v)
    return r


# ------------------------------------------------------------------ ran vs passed

def test_ran_records_execution_not_success():
    """A rung that ran and REFUSED the frame is evidence the rung is wired. Conflating
    the two is how 'could not run' starts reading like 'looked and it was fine'.

    The example is exit 1 -- the REFUSAL code. It used to be exit 2, which is the
    COULD-NOT-RUN code, so this test illustrated its own principle with the one
    value that contradicts it, and pinned the behaviour the docstring warns about.
    """
    r = RR.new("x")
    RR.note(r, "delta", True, exit_code=1)
    assert r["rungs"]["delta"]["ran"] is True
    assert r["rungs"]["delta"]["exit"] == 1


def test_exit_2_overrules_a_caller_that_claims_it_ran():
    """`qa/round-receipt-latest.json` really shipped `"delta": {"ran": true, "exit": 2}`.
    The caller set `ran` from "subprocess returned a CompletedProcess", so a rung that
    announced it could not measure was filed as one that measured -- and neither reader
    of this module looks at `exit`. The contract belongs to the field, not the caller."""
    r = RR.new("x")
    RR.note(r, "delta", True, exit_code=2)
    assert r["rungs"]["delta"]["ran"] is False
    assert r["rungs"]["delta"]["exit"] == 2
    assert "could_not_run" in r["rungs"]["delta"]


def test_a_could_not_run_rung_emits_no_proof_token():
    """The token is what an owner order greps for. A rung that could not run must not
    mint the evidence that it did -- that is R13's defect on R13's own machinery."""
    r = RR.new("x", quick=False, frame=True)
    RR.note(r, "delta", True, exit_code=2)
    RR.note(r, "dim_check", True, exit_code=0)
    r["last_full"] = {"rungs": r["rungs"]}
    assert RR.proof_tokens(r) == ["dim_check:ran"]


def test_a_declined_rung_carries_its_reason():
    r = RR.new("x")
    RR.note(r, "gen_diff", False, why="full-fidelity eye frames only (R5)")
    assert r["rungs"]["gen_diff"]["ran"] is False
    assert "R5" in r["rungs"]["gen_diff"]["why"]


def test_missing_is_not_the_same_as_declined():
    """Never reported and reported-as-not-run are different facts, and a receipt that
    cannot tell them apart is the ambiguity this file exists to end."""
    r = RR.new("x")
    RR.note(r, "delta", False, why="no beauty frame")
    miss = RR.missing(r)
    assert "delta" not in miss
    assert "gen_diff" in miss and "p2_exit" in miss
    assert "NEVER REPORTED" in RR.summary(r)


# ------------------------------------------------------------------ last_full

def test_a_full_round_records_last_full(tmp_path):
    RR.write(_full("r1", gen_diff=True), str(tmp_path))
    d = json.load(open(os.path.join(str(tmp_path), RR.RECEIPT_REL), encoding="utf-8"))
    assert d["last_full"]["round"] == "r1"
    assert d["last_full"]["rungs"]["gen_diff"]["ran"] is True


def test_a_quick_round_carries_last_full_forward(tmp_path):
    """THE POINT. R5 says the playblast rung stays cheap, so the pixel rungs correctly
    decline on a quick frame. If a quick round erased last_full, every order about
    'every render' would flip to not-obeyed after normal, correct work — and a rung that
    cries wolf after correct work gets switched off (R13's own warning)."""
    root = str(tmp_path)
    RR.write(_full("r1", gen_diff=True), root)
    q = RR.new("r2_ql", quick=True, frame=True)
    RR.note(q, "gen_diff", False, why="R5")
    RR.write(q, root)
    d = json.load(open(os.path.join(root, RR.RECEIPT_REL), encoding="utf-8"))
    assert d["rungs"]["gen_diff"]["ran"] is False        # this round, honestly
    assert d["last_full"]["round"] == "r1"              # the deliverable round, kept
    assert d["last_full"]["rungs"]["gen_diff"]["ran"] is True


def test_a_later_full_round_replaces_last_full(tmp_path):
    root = str(tmp_path)
    RR.write(_full("r1", gen_diff=True), root)
    RR.write(_full("r9", gen_diff=True), root)
    d = json.load(open(os.path.join(root, RR.RECEIPT_REL), encoding="utf-8"))
    assert d["last_full"]["round"] == "r9"


def test_history_copy_is_kept(tmp_path):
    """The latest file must never be the only evidence a round happened."""
    RR.write(_full("r1", gen_diff=True), str(tmp_path))
    assert os.path.isfile(os.path.join(str(tmp_path), "qa", "round-receipts", "r1.json"))


def test_load_returns_none_when_nothing_has_reported(tmp_path):
    assert RR.load(str(tmp_path)) is None


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
