"""Tests for sourcing_check — the rung that refuses to let "we have not bought
one" print as "one does not exist".

The negative control is D-074, filed 2026-08-16: a careful, honest survey of 68
cached folders, every one of them from a free tier, written up as a SOURCING GAP
and handed over as a procurement decision — while the three paid tiers R8
permits had never been attempted once in the repo's history. The lane's next
move was to go back to hand-modelling the object, which is the class R8 forbids.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sourcing_check as SC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROSTER = {"paid_permitted": True,
          "tiers": [{"id": "cc0", "name": "CC0", "cost": "฿0",
                     "owner_decision": False},
                    {"id": "warehouse", "name": "3D Warehouse", "cost": "฿0",
                     "owner_decision": False},
                    {"id": "paid-per-model", "name": "3dsky",
                     "cost": "$5-15", "owner_decision": True}]}

FULL = {"cc0": "searched: 40, 0 usable",
        "warehouse": "searched: 28, 2 survive",
        "paid-per-model": "searched: 0 results for this spec"}


def _row(**kw):
    d = {"id": "D-900", "unit": "DELIV-001", "decided_date": "2026-08-16",
         "question": "q", "in_effect": "ประกาศเป็น SOURCING GAP", "because": "b",
         "reverse_by": "r"}
    d.update(kw)
    return d


def _dec(rows):
    return {"decisions": rows}


def test_no_roster_is_itself_the_violation():
    v = SC.check(None, _dec([]), "DELIV-001", REPO)
    assert len(v) == 1 and "unfalsifiable" in v[0]


def test_a_gap_that_searched_everything_passes():
    assert SC.check(ROSTER, _dec([_row(tiers=FULL)]), "DELIV-001", REPO) == []


def test_a_gap_declared_in_prose_is_still_a_gap():
    # D-074 declared its gap in a sentence. A checker that only reads a key it
    # hoped somebody would set is a checker that never fires.
    v = SC.check(ROSTER, _dec([_row()]), "DELIV-001", REPO)
    assert any("no `tiers` record" in s for s in v)
    assert any("measured against 68 free-tier folders" in s for s in v)


def test_an_unmentioned_tier_reads_as_coverage_and_is_refused():
    t = dict(FULL)
    t.pop("paid-per-model")
    v = SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO)
    assert any("says nothing about paid-per-model" in s for s in v)


def test_the_whole_point_an_untried_paid_tier_makes_it_a_purchase_not_a_gap():
    t = dict(FULL, **{"paid-per-model": "not-attempted"})
    v = SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO)
    assert any("THAT IS NOT A GAP, IT IS AN UNMADE PURCHASE" in s for s in v)
    assert any("hand-modelling the class R8 forbids" in s for s in v)


def test_an_untried_FREE_tier_is_reported_but_is_not_the_same_charge():
    t = dict(FULL, cc0="not-attempted")
    v = SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO)
    assert not any("UNMADE PURCHASE" in s for s in v)


def test_a_free_text_status_is_a_status_nothing_can_count():
    t = dict(FULL, cc0="looked a bit")
    v = SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO)
    assert any("free-text status" in s for s in v)


def test_a_tier_that_is_not_in_the_roster_is_refused():
    t = dict(FULL, **{"ebay": "searched: 3"})
    v = SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO)
    assert any("not a tier in" in s for s in v)


def test_re_fencing_to_free_only_is_refused_in_his_own_words():
    v = SC.check(dict(ROSTER, paid_permitted=False), _dec([]), "DELIV-001", REPO)
    assert any("ยกเลิกข้อนี้" in s for s in v)


# --- a procurement ask has to be answerable ----------------------------------

def _ask_row(**kw):
    d = {"kind": "procurement-ask", "in_effect": "ส่งเป็นการตัดสินใจจัดซื้อ",
         "tiers": dict(FULL, **{"paid-per-model": "not-attempted"}),
         "ask_price": "$5-15", "ask_spec": "1820x1969 at <=1.0",
         "ask_routed_at": "qa/owner-asks.json"}
    d.update(kw)
    return _row(**d)


def test_a_priced_routed_ask_passes_even_with_an_untried_paid_tier():
    # This is the correct destination for the D-074 shape: not a gap, an ask.
    assert SC.check(ROSTER, _dec([_ask_row()]), "DELIV-001", REPO) == []


def test_an_ask_with_no_price_will_be_dropped():
    v = SC.check(ROSTER, _dec([_ask_row(ask_price=None)]), "DELIV-001", REPO)
    assert any("eight restatements" in s for s in v)


def test_an_ask_routed_nowhere_was_never_made():
    v = SC.check(ROSTER, _dec([_ask_row(ask_routed_at="qa/nope.json")]),
                 "DELIV-001", REPO)
    assert any("never made" in s for s in v)


def test_open_asks_age_oldest_first_and_answered_ones_drop_out():
    import datetime
    rows = [_ask_row(id="A", decided_date="2026-08-16"),
            _ask_row(id="B", decided_date="2026-07-01"),
            _ask_row(id="C", decided_date="2026-07-01", ask_answered="ซื้อเลย")]
    got = SC.open_asks(_dec(rows), "DELIV-001", datetime.date(2026, 8, 16))
    assert [d["id"] for d, _ in got] == ["B", "A"]
    assert got[0][1] == 46


# --- the real files -----------------------------------------------------------

def test_the_repos_own_roster_is_honest():
    data = SC.load(repo_root=REPO)
    assert data is not None
    assert data.get("paid_permitted") is True
    assert len(SC.paid_tiers(data)) >= 3


def test_the_live_register_declares_no_unpriced_gap():
    import json
    data = SC.load(repo_root=REPO)
    with open(os.path.join(REPO, "qa/open-decisions.json"), encoding="utf-8") as f:
        dec = json.load(f)
    assert SC.check(data, dec, "DELIV-001", REPO) == []


def test_reclassifying_a_gap_as_an_ask_costs_more_than_it_saves():
    """The `kind` key outranks the prose — a row that has been re-filed as an
    ask keeps its original words, because rewriting history to please a checker
    is worse than the checker being wrong. It is not an escape hatch: the ask
    has to carry a price, a measured spec and a channel that exists."""
    t = dict(FULL, **{"paid-per-model": "not-attempted"})
    still_a_gap = _row(tiers=t)
    assert any("UNMADE PURCHASE" in s for s in
               SC.check(ROSTER, _dec([still_a_gap]), "DELIV-001", REPO))
    reclassified = _ask_row(tiers=t)          # same prose, same untried tier
    assert SC.check(ROSTER, _dec([reclassified]), "DELIV-001", REPO) == []
    naked = _ask_row(tiers=t, ask_price=None, ask_spec=None)
    assert len(SC.check(ROSTER, _dec([naked]), "DELIV-001", REPO)) == 2


def test_a_superseded_gap_stops_governing_but_stays_in_the_file():
    t = dict(FULL, **{"paid-per-model": "not-attempted"})
    assert SC.check(ROSTER, _dec([_row(tiers=t, superseded_by="D-084")]),
                    "DELIV-001", REPO) == []


def test_n_a_is_not_not_attempted():
    """'the need is met so this tier is moot' and 'we never looked' are
    different sentences, and only the second one is the defect."""
    t = dict(FULL, **{"paid-per-model": "n/a: the class is filled"})
    assert SC.check(ROSTER, _dec([_row(tiers=t)]), "DELIV-001", REPO) == []
