"""Tests for orders_check — the ledger that holds his orders so the builder
cannot out-argue one.

The negative controls here are the ways an order gets lost, and every one of
them is taken from something that actually happened in this repo rather than
invented:

  * an order quoted in a row's PROSE with no stance          (D-052, D-054)
  * a builder decision reversing a standing order            (D-072)
  * an assertion that reads the comment and not the line     (build_room.py:1651
                                                              vs :1668)
  * a subject decided over and over while the order stands   (ten rows)
  * an order "carried out" as a flag that ships OFF          (_ADULT_SCALE,
                                                              _DUVET_TUCKS, R11,
                                                              the R1 cap, gen-diff)

`test_the_prose_rule_fires_on_the_real_D_052` is the one that matters most: it
runs the rule against the ACTUAL row from the committed register, with the
stance this session added stripped back off, so "it would have caught it at r31"
is a measurement instead of a claim.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orders_check as OC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _order(**kw):
    o = {"id": "ORD-x", "date": "2026-08-14",
         "verbatim": "เอาผมออกจาก gate เลย ไม่ต้องรอผม",
         "recorded_at": "qa/open-decisions.json",
         "commands": "do the thing", "subject": "subj", "scope": "class",
         "standing": True, "retired_by": None,
         "obeyed_where": "CLAUDE.md", "obeyed_how": "wired",
         "obeyed_assert": []}
    o.update(kw)
    return o


def _led(orders, **kw):
    d = {"orders": orders}
    d.update(kw)
    return d


def _row(**kw):
    d = {"id": "D-900", "unit": "DELIV-001", "subject": "subj",
         "decided_round": 44, "decided_date": "2026-08-16",
         "decided_by": "builder", "question": "q", "in_effect": "e",
         "where": "CLAUDE.md", "because": "b", "reverse_by": "r",
         "owner_override": None, "override_date": None}
    d.update(kw)
    return d


def _dec(rows):
    return {"decisions": rows}


# --- the ledger has to exist and be pointable-at ------------------------------

def test_no_ledger_is_itself_the_violation():
    v = OC.check_orders(None, REPO)
    assert len(v) == 1 and "no readable orders ledger" in v[0]


def test_a_clean_order_passes():
    assert OC.check_orders(_led([_order()]), REPO) == []


def test_words_that_do_not_reproduce_are_refused():
    o = _order(verbatim="ผมไม่เคยพูดประโยคนี้เลยแม้แต่ครั้งเดียว")
    v = OC.check_orders(_led([o]), REPO)
    assert any("do not appear" in s for s in v)
    assert any("paraphrasing" in s for s in v)


def test_a_thai_quote_broken_by_a_line_wrap_still_reproduces():
    # CLAUDE.md wraps this order mid-WORD, and Thai has no inter-word spaces —
    # whitespace-collapsing alone reported his 2026-08-09 order as missing from
    # the file that quotes it.
    o = _order(verbatim="ผมขอบังคับให้ทุกกลไก ทุกขั้นตอนต้องมองรูปจริง",
               recorded_at="CLAUDE.md")
    assert OC.check_orders(_led([o]), REPO) == []


def test_an_order_obeyed_nowhere_was_never_carried_out():
    v = OC.check_orders(_led([_order(obeyed_where="qa/nope.json")]), REPO)
    assert any("does not exist" in s for s in v)


def test_an_order_with_no_words_needs_an_account_of_why():
    v = OC.check_orders(_led([_order(verbatim="")]), REPO)
    assert any("attributed upward" in s for s in v)
    ok = _order(verbatim="", verbatim_absent_because="only a paraphrase exists")
    assert OC.check_orders(_led([ok]), REPO) == []


# --- the assertion reads the LINE, not the comment above it -------------------

def test_a_broken_assertion_fails_and_quotes_him():
    o = _order(obeyed_assert=[{"file": "pipeline/scripts/build_room.py",
                               "pattern": "^_BED_CLOTH_ACQ = False",
                               "why": "why"}])
    v = OC.check_orders(_led([o]), REPO)
    assert any("DOES NOT OBEY THIS ORDER" in s for s in v)
    assert any("เอาผมออกจาก gate" in s for s in v)


def test_an_unreadable_file_is_unknown_not_obeyed():
    o = _order(obeyed_assert=[{"file": "pipeline/scripts/nope.py",
                               "pattern": "x", "why": "y"}])
    v = OC.check_orders(_led([o]), REPO)
    assert any("UNKNOWN, not obeyed" in s for s in v)


def test_an_absent_assertion_fires_when_the_forbidden_text_is_there():
    o = _order(obeyed_assert=[{"file": "CLAUDE.md", "pattern": "R8",
                               "absent": True, "why": "y"}])
    v = OC.check_orders(_led([o]), REPO)
    assert any("which this order forbids" in s for s in v)


def test_an_uncompilable_pattern_is_not_a_check():
    o = _order(obeyed_assert=[{"file": "CLAUDE.md", "pattern": "([",
                               "why": "y"}])
    v = OC.check_orders(_led([o]), REPO)
    assert any("will not\n" in s or "will not compile" in s.replace("\n", " ")
               for s in v)


# --- the builder may not overrule him with a measurement ----------------------

def test_a_builder_row_contradicting_a_standing_order_is_refused():
    led = _led([_order(id="ORD-a")])
    rows = _dec([_row(contradicts="ORD-a")])
    v = OC.check_decisions(led, rows, "DELIV-001", REPO)
    assert any("only he" in s for s in v)
    assert any("second thing to" in s for s in v)


def test_the_owner_may_reverse_himself():
    led = _led([_order(id="ORD-a")])
    rows = _dec([_row(contradicts="ORD-a", decided_by="owner",
                      owner_override="เอาแบบเดิมเถอะ", override_date="2026-08-17")])
    assert OC.check_decisions(led, rows, "DELIV-001", REPO) == []


def test_the_builder_may_not_sign_that_reversal_for_him():
    led = _led([_order(id="ORD-a")])
    rows = _dec([_row(contradicts="ORD-a", decided_by="owner")])
    v = OC.check_decisions(led, rows, "DELIV-001", REPO)
    assert any("may not sign for him" in s for s in v)


def test_a_superseded_contradiction_is_history_not_a_live_one():
    # Rows never leave this register, so without this the file would carry a
    # violation nothing could ever clear — which is the same as no violation.
    led = _led([_order(id="ORD-a")])
    rows = _dec([_row(contradicts="ORD-a", superseded_by="D-901")])
    assert OC.check_decisions(led, rows, "DELIV-001", REPO) == []


def test_a_stance_on_an_order_nobody_recorded_is_a_stance_on_nothing():
    v = OC.check_decisions(_led([]), _dec([_row(obeys="ORD-ghost")]),
                           "DELIV-001", REPO)
    assert any("not in qa/owner-orders.json" in s for s in v)


def test_a_governed_row_must_say_which_way_it_goes():
    led = _led([_order(id="ORD-a", subject="subj")])
    v = OC.check_decisions(led, _dec([_row()]), "DELIV-001", REPO)
    assert any("neither `obeys`" in s for s in v)


def test_a_row_filed_before_the_order_needs_no_stance():
    # A guard that demands the impossible gets deleted.
    led = _led([_order(id="ORD-a", subject="subj", date="2026-08-14")])
    old = _row(decided_date="2026-08-01")
    assert OC.check_decisions(led, _dec([old]), "DELIV-001", REPO) == []


# --- an order in prose is not an order to the machine -------------------------

def test_a_post_ratchet_row_quoting_an_order_in_prose_is_refused():
    rows = _dec([_row(id="D-999", subject=None,
                      question="พี่สั่งให้เอาผ้าออก")])
    v = OC.check_decisions(_led([]), rows, "DELIV-001", REPO)
    assert any("reports an owner order in prose" in s for s in v)


def test_the_prose_rule_fires_on_the_real_D_052():
    """THE NEGATIVE CONTROL. The actual committed row, with the stance this
    session added stripped back off and its id moved past the ratchet, so the
    claim 'this rung would have caught it the day it was written' is measured
    against the real text rather than a fixture."""
    with open(os.path.join(REPO, "qa/open-decisions.json"), encoding="utf-8") as f:
        real = json.load(f)
    d052 = next(d for d in real["decisions"] if d["id"] == "D-052")
    naked = {k: v for k, v in d052.items()
             if k not in ("obeys", "contradicts", "superseded_by")}
    naked["id"] = "D-999"                       # past the ratchet
    naked["subject"] = None                     # the state it was filed in
    v = OC.check_decisions(_led([]), _dec([naked]), "DELIV-001", REPO)
    assert any("reports an owner order in prose" in s for s in v), \
        "the row that started all of this must trip this rule"
    assert any("คำสั่งพี่" in s for s in v)


def test_a_missing_ratchet_key_checks_every_row_rather_than_none():
    # A missing config key that silently disables a rung is the shape this file
    # exists to end.
    rows = _dec([_row(id="D-001", subject=None, question="พี่สั่งให้ทำ")])
    v = OC.check_decisions(_led([]), rows, "DELIV-001", REPO)
    assert any("reports an owner order in prose" in s for s in v)


def test_the_standard_overrule_sentence_is_not_an_order_citation():
    # "พี่ overrule ได้จากรูป" closes half the rows in this register. A marker
    # list that caught it would fire on six innocent rows and be switched off.
    rows = _dec([_row(id="D-999", subject=None,
                      in_effect="พี่ overrule ได้ทุกเมื่อจากรูป")])
    assert OC.check_decisions(_led([]), rows, "DELIV-001", REPO) == []


def test_pre_ratchet_prose_rows_are_debt_not_failures():
    data = _led([], _subject_ratchet_from="D-080")
    rows = _dec([_row(id="D-010", subject=None, question="คำสั่งพี่ ...")])
    assert OC.check_decisions(data, rows, "DELIV-001", REPO) == []
    assert OC.prose_debt(data, rows, "DELIV-001") == ["D-010"]


# --- the stop-loss is a counter, and it can be cleared ------------------------

def _broken_order(**kw):
    return _order(obeyed_assert=[{"file": "pipeline/scripts/build_room.py",
                                  "pattern": "^_NEVER_GOING_TO_MATCH_XYZ",
                                  "why": "w"}], **kw)


def test_three_builder_decisions_on_a_disobeyed_order_stop_the_lane():
    led = _led([_broken_order(id="ORD-a", subject="subj", date="2026-08-14")])
    rows = _dec([_row(id="D-1", obeys="ORD-a"), _row(id="D-2", obeys="ORD-a"),
                 _row(id="D-3", obeys="ORD-a")])
    v = OC.check_decisions(led, rows, "DELIV-001", REPO)
    assert any("STOP-LOSS" in s for s in v)
    assert any("misclassified" in s for s in v)


def test_two_is_not_yet_the_stop_loss():
    led = _led([_broken_order(id="ORD-a", subject="subj", date="2026-08-14")])
    rows = _dec([_row(id="D-1", obeys="ORD-a"), _row(id="D-2", obeys="ORD-a")])
    assert not any("STOP-LOSS" in s
                   for s in OC.check_decisions(led, rows, "DELIV-001", REPO))


def test_carrying_the_order_out_clears_the_stop_loss():
    # A counter that can never be cleared is a counter that gets commented out.
    led = _led([_order(id="ORD-a", subject="subj", date="2026-08-14")])
    rows = _dec([_row(id="D-%d" % i, obeys="ORD-a") for i in range(5)])
    assert not any("STOP-LOSS" in s
                   for s in OC.check_decisions(led, rows, "DELIV-001", REPO))


def test_his_own_rows_do_not_count_against_the_stop_loss():
    led = _led([_broken_order(id="ORD-a", subject="subj", date="2026-08-14")])
    rows = _dec([_row(id="D-%d" % i, obeys="ORD-a", decided_by="owner",
                      owner_override="x", override_date="2026-08-16")
                 for i in range(5)])
    assert not any("STOP-LOSS" in s
                   for s in OC.check_decisions(led, rows, "DELIV-001", REPO))


def test_the_counter_sees_every_subject_even_ungoverned_ones():
    rows = _dec([_row(id="D-1", subject="rug"), _row(id="D-2", subject="rug")])
    assert OC.subject_tally(rows, "DELIV-001")[0] == ("rug", 2, ["D-1", "D-2"])


# --- the third state, which must never read as obedience ----------------------

def test_not_obeyed_needs_a_date_and_a_route_back():
    o = _order(status="not-obeyed", not_obeyed_because="the bay is too shallow")
    v = OC.check_orders(_led([o]), REPO)
    assert any("`since` date" in s for s in v)
    assert any("dropped order wearing a status" in s for s in v)


def test_blocked_by_must_name_an_ask_he_is_actually_holding():
    o = _order(status="not-obeyed", not_obeyed_because="x", since="2026-08-13",
               blocked_by="ASK-999")
    v = OC.check_orders(_led([o]), REPO)
    assert any("not an OPEN row" in s for s in v)


def test_a_real_open_ask_is_a_legitimate_blocker():
    # Reads the LIVE ask ledger by design — a blocker must name something he is
    # actually still holding. It used to hard-code ASK-001, then ASK-006, and
    # went red each time he answered (2026-09-01: ASK-006 answered, the test had
    # been failing at HEAD with nobody reading it). So it now takes the first
    # OPEN row, whichever that is; with the queue at zero it skips loudly rather
    # than asserting on a row that does not exist.
    with open(os.path.join(REPO, "qa", "owner-asks.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    rows = ledger["asks"] if isinstance(ledger, dict) else ledger
    open_ids = [r["id"] for r in rows if r.get("status") == "open"]
    if not open_ids:
        import pytest
        pytest.skip("no OPEN ask in qa/owner-asks.json — nothing to be blocked by")
    o = _order(status="not-obeyed", not_obeyed_because="x", since="2026-08-13",
               blocked_by=open_ids[0])
    assert OC.check_orders(_led([o]), REPO) == []


def test_restart_by_is_the_builders_own_debt_and_is_allowed():
    o = _order(status="not-obeyed", not_obeyed_because="x", since="2026-08-15",
               restart_by="run gen_diff on the next frame")
    assert OC.check_orders(_led([o]), REPO) == []


def test_pessimism_is_refused_too():
    o = _order(status="not-obeyed", not_obeyed_because="x", since="2026-08-15",
               restart_by="y",
               obeyed_assert=[{"file": "CLAUDE.md", "pattern": "R8", "why": "w"}])
    v = OC.check_orders(_led([o]), REPO)
    assert any("every assertion it carries holds" in s.replace("\n", " ")
               for s in v)


def test_obedience_reports_three_states_not_two():
    led = _led([_order(id="A"),
                _broken_order(id="B"),
                _order(id="C", status="not-obeyed", since="2026-08-13",
                       not_obeyed_because="x", blocked_by="ASK-001")])
    got = {o["id"]: (ok, detail) for o, ok, detail in OC.obedience(led, REPO)}
    assert got["A"][0] is True
    assert got["B"][0] is False and "BROKEN" in got["B"][1]
    assert got["C"][0] is False and "NOT OBEYED" in got["C"][1]


# --- only he retires his own order -------------------------------------------

def test_a_retired_order_must_name_the_decision_that_retired_it():
    v = OC.check_orders(_led([_order(standing=False)]), REPO)
    assert any("does not lapse" in s for s in v)


def test_retirement_must_point_at_a_decision_row():
    v = OC.check_orders(_led([_order(standing=False, retired_by="เพราะมันเก่า")]),
                        REPO)
    assert any("not a decision row id" in s for s in v)


# --- unit scoping -------------------------------------------------------------

def test_an_order_scoped_to_one_lane_does_not_govern_another():
    led = _led([_order(id="ORD-a", subject="subj", units=["DELIV-001"])])
    rows = _dec([_row(unit="TRN-002")])
    assert OC.check_decisions(led, rows, "TRN-002", REPO) == []


def test_an_order_with_no_units_governs_every_lane():
    led = _led([_order(id="ORD-a", subject="subj")])
    rows = _dec([_row(unit="TRN-002")])
    v = OC.check_decisions(led, rows, "TRN-002", REPO)
    assert any("neither `obeys`" in s for s in v)


# --- the real files -----------------------------------------------------------

def test_the_repos_own_orders_ledger_is_honest():
    data = OC.load(repo_root=REPO)
    assert data is not None, "the committed ledger must be readable"
    assert OC.check_orders(data, REPO) == []


def test_the_repos_own_register_takes_a_stance_where_it_must():
    """Every live row that is governed by a standing order names a stance.

    THE STOP-LOSS IS EXCLUDED HERE ON PURPOSE, and the distinction is the point.
    The other violations this function raises are BOOKKEEPING — a row that quotes
    his words with no stance, a decider called `pending`, a builder row that
    contradicts an order — and every one of them is fixable by editing the
    register, so a red test means someone must go and write something down.
    The stop-loss is not fixable that way: it fires while a real order is
    unobeyed and it clears only when the order is CARRIED OUT. Asserting it here
    would put a permanently-red test in the suite while the bed has no cloth,
    and a suite that is red for a reason nobody can close is a suite that stops
    being read — this repo's own recorded failure mode for guards. It is
    enforced where it bites instead: `rule_gate` blocks the render on it, which
    is what stopped p2r46 from producing a frame at all.
    """
    data = OC.load(repo_root=REPO)
    with open(os.path.join(REPO, "qa/open-decisions.json"), encoding="utf-8") as f:
        dec = json.load(f)
    v = OC.check_decisions(data, dec, "DELIV-001", REPO)
    assert [s for s in v if not s.startswith("STOP-LOSS:")] == []


def test_the_stop_loss_cleared_when_the_bed_cloth_order_was_carried_out():
    """THE FLIP THIS TEST WAS WRITTEN TO TAKE, taken on 2026-08-17 (p2r47).

    Its p2r46 form asserted the stop-loss was FIRING, and said in its own
    docstring: "When a qualifying cover is finally named, the assertion holds
    again, this fires no more, and THIS TEST FLIPS: change it then, do not
    silence it now." A cover was named — `bed_models.cloth_set` = d4698c95_flat,
    94.0% coverage and 4/4 flanks on the built scene — the order's assertions
    hold, and the counter cleared itself exactly as R13 specifies ("the stop-loss
    is a COUNTER that fires while the order is unobeyed and clears when it is
    carried out").

    It is kept as a LIVE test rather than deleted, in the direction that matters:
    if the subject ever accumulates builder decisions again while the order is
    unobeyed, this goes red on the next run.
    """
    data = OC.load(repo_root=REPO)
    with open(os.path.join(REPO, "qa/open-decisions.json"), encoding="utf-8") as f:
        dec = json.load(f)
    v = OC.check_decisions(data, dec, "DELIV-001", REPO)
    hits = [s for s in v if s.startswith("STOP-LOSS:")
            and "bed-cloth-build-vs-acquire" in s]
    assert hits == [], (
        "the bed-cloth order is carried out; a stop-loss here means either the "
        "spec stopped naming a surviving set or the subject is being decided "
        "again by the builder: " + "; ".join(hits))


def test_every_standing_order_still_reproduces_its_own_words():
    """His words are the artefact. If a file is reworded and a quote stops
    reproducing, this fails BEFORE the next render — which is the whole
    difference between an order and a memory of one."""
    data = OC.load(repo_root=REPO)
    for o in OC.orders(data, standing_only=True):
        if not o.get("verbatim"):
            assert o.get("verbatim_absent_because"), o["id"]
            continue
        hit = False
        for rel in OC._paths(o["recorded_at"]):
            txt = OC._read(REPO, rel)
            if txt and OC._find(txt, o["verbatim"])[1]:
                hit = True
        assert hit, f"{o['id']}: his words no longer appear in {o['recorded_at']}"


def test_the_bed_cloth_order_is_actually_obeyed_now():
    """The one this session was ordered to fix, asserted against the code."""
    data = OC.load(repo_root=REPO)
    o = next(x for x in OC.orders(data)
             if x["id"] == "ORD-2026-08-14-bed-cloth-is-acquired")
    assert OC._assert_violations(o["id"], o, REPO) == []


# --- a malformed stance is REPORTED, never raised -----------------------------
# 2026-08-17: a row filed `obeys` as a LIST of two order ids and `check_decisions`
# died on `unhashable type: 'list'`. A blocking gate module taken out by a
# TypeError is the shape score_exit_policy already records — python exits 1 on an
# uncaught exception and 1 is this tool's code for "ran and found violations", so
# a crashed rung reads exactly like a completed one.

def test_a_list_valued_stance_is_a_violation_and_not_a_crash():
    led = _led([_order(id="ORD-a"), _order(id="ORD-b")])
    rows = _dec([_row(obeys=["ORD-a", "ORD-b"])])
    v = OC.check_decisions(led, rows, "DELIV-001", REPO)
    assert any("stance as list" in s for s in v), v


def test_a_well_formed_stance_still_resolves():
    led = _led([_order(id="ORD-a")])
    v = OC.check_decisions(led, _dec([_row(obeys="ORD-a")]), "DELIV-001", REPO)
    assert not any("stance as" in s for s in v), v


# --- the visual-closure law (2026-08-26, debate proposal 1) -------------------


def _verdict_file(tmp_path, name="v.json", **kw):
    import json as _json
    d = {"order": "ORD-x", "item": 1, "owner_sentence": "x",
         "frames": ["f.png"], "verdict": "VISIBLE", "evidence": []}
    d.update(kw)
    p = tmp_path / name
    p.write_text(_json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return str(p)


def test_visual_obeyed_needs_verdicts():
    o = _order(visual=True)
    v = OC.check_orders(_led([o]), REPO)
    assert any("closure_verdicts" in s for s in v)


def test_visual_obeyed_with_visible_verdict_is_clean(tmp_path):
    o = _order(visual=True, closure_verdicts=[_verdict_file(tmp_path)])
    assert OC.check_orders(_led([o]), REPO) == []


def test_not_visible_verdict_blocks_obeyed(tmp_path):
    o = _order(visual=True, closure_verdicts=[
        _verdict_file(tmp_path, verdict="NOT-VISIBLE")])
    v = OC.check_orders(_led([o]), REPO)
    assert any("could not point at pixels" in s for s in v)


def test_overturned_verdict_no_longer_supports_closure(tmp_path):
    # the item-1 night: the verifier said VISIBLE, the front probe overturned it
    o = _order(visual=True, closure_verdicts=[
        _verdict_file(tmp_path, overturned={"by": "front_probe"})])
    v = OC.check_orders(_led([o]), REPO)
    assert any("OVERTURNED" in s for s in v)


def test_unreadable_verdict_is_unknown_not_obeyed():
    o = _order(visual=True, closure_verdicts=["no/such/verdict.json"])
    v = OC.check_orders(_led([o]), REPO)
    assert any("unreadable" in s for s in v)


def test_new_instance_list_must_declare_visual():
    o = _order(date="2026-08-27", scope="instance-list")
    v = OC.check_orders(_led([o]), REPO)
    assert any("must declare `visual`" in s for s in v)
    o2 = _order(date="2026-08-27", scope="instance-list", visual=False)
    assert not any("must declare" in s for s in OC.check_orders(_led([o2]), REPO))


def test_visual_not_obeyed_with_green_asserts_is_the_honest_state():
    # source greps holding while the frame is refuted is EXACTLY p2r75 —
    # a visual row may sit not-obeyed without the pessimism complaint.
    o = _order(visual=True, status="not-obeyed", not_obeyed_because="refuted",
               since="2026-08-25", restart_by="re-render + re-verify",
               obeyed_assert=[{"file": "CLAUDE.md", "pattern": "R13",
                               "why": "still true in source"}])
    v = OC.check_orders(_led([o]), REPO)
    assert not any("pessimistic" in s for s in v)


def test_negative_control_the_real_ord25b_cannot_reclaim_obeyed():
    """THE NIGHT, replayed against the real ledger: flip the real ORD-25b row
    back to 'obeyed' and the verdict files on disk refuse it — items 2-4 are
    still NOT-VISIBLE. (item1's entry now points at the p2r77 VISIBLE verdict,
    honestly earned: derived facing + fresh verifier with arrows on both pulls.)
    'It would have caught the false closure' stays a measurement, not a claim."""
    data = OC.load(repo_root=REPO)
    row = next(o for o in data["orders"]
               if o["id"] == "ORD-2026-08-25b-five-items-after-p2r74")
    assert row.get("visual") is True
    replay = dict(row, status="obeyed")
    v = OC.check_orders(_led([replay]), REPO)
    assert sum("could not point at pixels" in s for s in v) >= 3   # items 2-4


def test_negative_control_the_real_overturned_verdict_still_refuses():
    """The archived p2r76 item-1 verdict (VISIBLE, then OVERTURNED by the front
    probe) stays on disk as history — a row citing it can never print obeyed.
    The eye that read the blank framed back as a drawer front is permanently
    outvoted by the measurement, in the file itself."""
    o = _order(visual=True, closure_verdicts=[
        "projects/PRJ-2026-002_c001-house/04_visualization/closure-verdicts/"
        "ORD-2026-08-25b/item1/verdict.json"])
    v = OC.check_orders(_led([o]), REPO)
    assert any("OVERTURNED" in s for s in v)


def test_gate_grammar_refuses_the_closing_phrase(tmp_path):
    g = tmp_path / "projects" / "p" / "04_visualization"
    g.mkdir(parents=True)
    (g / "gate-X-2026-08-27.md").write_text(
        u"ลงพิกเซลครบ",
        encoding="utf-8")
    v = OC.check_gate_grammar(str(tmp_path))
    assert len(v) == 1 and "refused by name" in v[0]
    # pre-ratchet gates are history, not violations
    (g / "gate-Y-2026-08-25.md").write_text(u"x", encoding="utf-8")
    assert len(OC.check_gate_grammar(str(tmp_path))) == 1
