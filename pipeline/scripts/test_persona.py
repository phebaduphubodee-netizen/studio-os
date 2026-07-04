#!/usr/bin/env python3
"""test_persona.py — pin the PERSONA-DRIVEN design layer (activity_taxonomy + persona).

The layer's value is HONESTY + the two-way link, so the tests assert the honest properties:
  (a) kind->activity is deterministic; a name is only a SOFT signal; a `serves` tag wins;
      a polymorphic/untagged kind is AMBIGUOUS (never guessed).
  (b) baseline dwelling needs (sleep/wash/store/eat) justify themselves; lifestyle elements
      need a stated persona activity or they are ORPHANs.
  (c) coverage is HOME-AWARE — a GAP only when NO room serves the activity (a bedroom is not
      faulted for lacking a kitchen).
  (d) the honest JUDGMENT boundary: a persona ritual with prose but no `activity` tag is
      FLAGGED un-mapped, never auto-inferred.
  (e) report() is advisory — verdict REVIEW/PASS/UNWIRED, NEVER a render-blocking FAIL; rows
      share {status, check, detail} with `persona:` prefixes; no persona -> UNWIRED.
  (f) it degrades, never throws; and it upgrades rationale.py's presence axis when a persona
      is supplied (and is a no-op without one).

Run: python pipeline/scripts/test_persona.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity_taxonomy as AT   # noqa: E402
import persona as P              # noqa: E402
import rationale as R            # noqa: E402


def _spec(fn):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", fn)
    assert os.path.exists(p), f"fixture spec missing: {p}"
    return json.load(open(p, encoding="utf-8"))


def _el(kind, name="x", **kw):
    return {"kind": kind, "name": name, "x": 0, "y": 0, "w": 600, "d": 600, "h": 700, **kw}


def _room(*items, type="living_condo", subrooms=None):
    return {"room": {"type": type, "outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": list(items), "builtins": [], "subrooms": subrooms or []}


# ---------------------------------------------------------------- taxonomy: element_activities
def test_kind_activity_deterministic():
    assert AT.element_activities(_el("bed"))["activities"] == ["sleep"]
    assert AT.element_activities(_el("desk"))["activities"] == ["work"]
    assert AT.element_activities(_el("wardrobe"))["activities"] == ["dress_store"]
    assert "bathe" in AT.element_activities(_el("shower"))["activities"]
    assert "groom" in AT.element_activities(_el("wc"))["activities"]


def test_name_signal_is_soft_and_unions_with_kind():
    # an armchair (kind->relax) NAMED a reading chair also serves 'read' (soft)
    ea = AT.element_activities(_el("armchair", name="เก้าอี้อ่านหนังสือ"))
    assert "relax" in ea["activities"] and "read" in ea["activities"]
    assert ea["source"] == "kind+name"


def test_serves_tag_wins_over_kind():
    ea = AT.element_activities(_el("cabinet", serves=["read"]))   # cabinet default = store
    assert ea["activities"] == ["read"] and ea["source"] == "serves"


def test_unknown_serves_falls_back_to_kind():
    ea = AT.element_activities(_el("bed", serves=["frobnicate"]))
    assert ea["activities"] == ["sleep"] and ea["source"] == "kind"


def test_polymorphic_untagged_is_ambiguous_never_guessed():
    ea = AT.element_activities(_el("stool", name="stool"))
    assert ea["activities"] == [] and ea["source"] == "ambiguous"


def test_vanity_stool_recovered_by_name():
    # the real ensuite stool: kind stool (ambiguous) but name signals grooming
    ea = AT.element_activities(_el("stool", name="เก้าอี้เครื่องแป้ง (vanity stool)"))
    assert ea["activities"] == ["groom"] and ea["source"] == "name"


def test_baseline_vs_lifestyle_split():
    assert "sleep" in AT.BASELINE_ACTIVITIES and "groom" in AT.BASELINE_ACTIVITIES
    assert "read" in AT.LIFESTYLE_ACTIVITIES and "work" in AT.LIFESTYLE_ACTIVITIES
    assert not (AT.BASELINE_ACTIVITIES & AT.LIFESTYLE_ACTIVITIES)


def test_kind_map_reuses_placement_logic_sets():
    import placement_logic as PL
    for k in PL.BED_KINDS:
        assert "sleep" in AT.KIND_ACTIVITY.get(k, [])
    for k in PL.BATH_WET_KINDS:
        assert "bathe" in AT.KIND_ACTIVITY.get(k, [])


# ---------------------------------------------------------------- derive_requirements (honesty)
def test_structured_activity_is_consumed_prose_is_flagged():
    persona = {"daily_rituals": [
        {"ritual": "reads before bed", "activity": "read", "cite": "x"},
        "makes coffee somewhere"]}      # a bare string: prose, no activity tag
    reqs, unmapped = P.derive_requirements(persona)
    acts = {r["activity"] for r in reqs}
    assert "read" in acts
    assert len(unmapped) == 1 and "no `activity` tag" in unmapped[0]["why"]


def test_priority_merges_ritual_and_must_have():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "r"}],
               "must_have": [{"want": "a reading spot", "activity": "read", "cite": "m"}]}
    reqs, _ = P.derive_requirements(persona)
    read = next(r for r in reqs if r["activity"] == "read")
    assert read["priority_label"] == "must_have" and len(read["sources"]) == 2


def test_wfh_implies_work():
    reqs, _ = P.derive_requirements({"work_pattern": {"wfh": True}})
    assert any(r["activity"] == "work" for r in reqs)


# ---------------------------------------------------------------- coverage (home-aware)
def test_gap_when_no_room_serves():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check(_room(_el("sofa")), persona)          # sofa serves relax/entertain, not read
    read = next(x for x in r["requirements"] if x["activity"] == "read")
    assert read["coverage"] == "gap"


def test_met_when_any_room_serves_home_aware():
    persona = {"daily_rituals": [{"ritual": "sleeps", "activity": "sleep", "cite": "x"},
                                 {"ritual": "reads", "activity": "read", "cite": "y"}]}
    living = _room(_el("armchair", name="reading chair"))          # serves read (name)
    bedroom = _room(_el("bed"), type="bedroom")                    # serves sleep
    r = P.check([living, bedroom], persona)
    cov = {x["activity"]: x["coverage"] for x in r["requirements"]}
    assert cov["read"] == "met" and cov["sleep"] == "met"


def test_orphan_lifestyle_element_not_in_persona():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check(_room(_el("tv", name="TV")), persona)   # tv serves relax; persona never relaxes
    tv = next(e for e in r["elements"] if e["kind"] == "tv")
    assert tv["coverage"] == "orphan"


def test_baseline_element_is_never_orphan():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check(_room(_el("wardrobe")), persona)        # dress_store is baseline
    w = next(e for e in r["elements"] if e["kind"] == "wardrobe")
    assert w["coverage"] == "served"


def test_ambiguous_element_flagged():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check(_room(_el("stool", name="stool")), persona)
    s = next(e for e in r["elements"] if e["kind"] == "stool")
    assert s["coverage"] == "ambiguous"


# ---------------------------------------------------------------- the real demo result
def test_demo_two_gaps_and_read_met():
    persona = _spec("persona_condo_demo.json")
    r = P.check([_spec("living_condo.json"), _spec("bedroom_suite.json")], persona)
    cov = {x["activity"]: x["coverage"] for x in r["requirements"]}
    assert cov["coffee_ritual"] == "gap", cov          # no balcony nook
    assert cov["work"] == "gap", cov                   # no desk
    assert cov["read"] == "met", cov                   # the reading-chair name signal
    assert cov["relax"] == "met" and cov["entertain"] == "met"


# ---------------------------------------------------------------- report() shape + verdict
def test_report_shape_prefixes_and_never_fails():
    persona = _spec("persona_condo_demo.json")
    results, verdict = P.report([_spec("living_condo.json"), _spec("bedroom_suite.json")], persona)
    assert verdict in ("REVIEW", "PASS", "UNWIRED")
    assert verdict != "FAIL"
    assert all(row["check"].startswith("persona:") for row in results)
    assert all(row["status"] != "FAIL" for row in results)          # advisory only
    assert any(row["check"].startswith("persona:gap:") for row in results)


def test_no_persona_is_unwired():
    results, verdict = P.report(_spec("living_condo.json"), None)
    assert verdict == "UNWIRED" and results == []


def test_report_row_shape():
    results, _ = P.report(_room(_el("sofa")),
                          {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]})
    for row in results:
        assert set(row) == {"status", "check", "detail"}


# ---------------------------------------------------------------- robustness (degrade, never throw)
def test_degrades_on_malformed_spec():
    results, verdict = P.report(
        {"items": [{"kind": "bed"}], "builtins": None, "subrooms": [{"fixtures": None}]},
        {"daily_rituals": [{"ritual": "x", "activity": "sleep", "cite": "c"}]})
    assert isinstance(results, list) and verdict in ("REVIEW", "PASS", "UNWIRED")


def test_degrades_on_non_dict_element():
    # a stray non-dict element (JUNK) must degrade OUT, not crash and not void the real bed's
    # coverage — the exact crash class the scrutiny caught (check/report/to_markdown all).
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    spec = {"room": {"type": "bedroom"}, "items": [_el("bed"), "JUNK"], "builtins": ["NOPE"], "subrooms": []}
    r = P.check(spec, persona)
    assert any(e["kind"] == "bed" for e in r["elements"])       # the real element survived
    results, verdict = P.report(spec, persona)
    assert any(row["check"].startswith("persona:gap:read") for row in results)  # real coverage, not one UNWIRED row
    assert "PERSONA COVERAGE" in P.to_markdown(spec, persona)   # to_markdown must not crash either


def test_degrades_on_non_dict_subroom():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check({"room": {"type": "bath"}, "subrooms": ["JUNK", {"fixtures": ["NOPE", _el("wc")]}]}, persona)
    assert isinstance(r, dict) and any(e["kind"] == "wc" for e in r["elements"])


def test_degrades_on_malformed_persona():
    r = P.check(_spec("living_condo.json"), {"daily_rituals": "not-a-list", "must_have": 42})
    assert isinstance(r, dict)                          # no throw


def test_rationale_degrades_on_non_dict_rationale_and_element():
    # rationale.report must not crash on a non-dict `rationale` field or a non-dict element
    spec = {"room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]], "type": "study"},
            "builtins": [{"kind": "cabinet", "name": "x", "x": 0, "y": 0, "w": 600, "d": 400, "h": 800,
                          "rationale": "just prose, not a dict"}, "JUNK"],
            "items": [], "subrooms": ["NOPE"]}
    rep = R.report(spec)                                # must not raise
    assert len(rep["elements"]) == 1                    # cabinet kept, JUNK skipped


# ---------------------------------------------------------------- fixes from adversarial scrutiny
def test_fused_baseline_element_still_orphan_for_unstated_lifestyle():
    # a headboard_tv = sleep(baseline)+relax; fusing the TV into a baseline built-in must NOT
    # hide the unstated 'relax' orphan (the fused-vs-standalone blind spot). Persona reads only.
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    r = P.check(_room(_el("headboard_tv", name="หัวเตียง+TV"), type="bedroom"), persona)
    ht = next(e for e in r["elements"] if e["kind"] == "headboard_tv")
    assert ht["coverage"] == "orphan" and "relax" in ht.get("unjustified", [])


def test_soft_name_signal_met_is_flagged_soft():
    persona = {"daily_rituals": [{"ritual": "reads", "activity": "read", "cite": "x"}]}
    results, _ = P.report(_room(_el("armchair", name="reading chair")), persona)
    read = next(r for r in results if r["check"] == "persona:met:read")
    assert "SOFT" in read["detail"]                     # a name-signal match is not a decisive one


def test_unknown_serves_tag_is_surfaced_not_swallowed():
    ea = AT.element_activities(_el("bed", serves=["frobnicate"]))
    assert ea["activities"] == ["sleep"]                # valid kind inference kept
    assert "unknown" in ea["detail"].lower() or "typo" in ea["detail"].lower()   # but the typo is flagged


def test_entertaining_never_makes_no_requirement():
    reqs_neg, _ = P.derive_requirements({"entertaining": {"frequency": "never"}})
    assert not any(r["activity"] == "entertain" for r in reqs_neg)
    reqs_pos, _ = P.derive_requirements({"entertaining": {"frequency": "monthly"}})
    assert any(r["activity"] == "entertain" for r in reqs_pos)


def test_priority_label_not_mislabelled_by_shared_numeric():
    persona = {"work_pattern": {"wfh": True},
               "nice_to_have": [{"want": "a plant to read by", "activity": "read", "cite": "x"}]}
    reqs, _ = P.derive_requirements(persona)
    assert next(r for r in reqs if r["activity"] == "work")["priority_label"] == "work"       # not "ritual"
    assert next(r for r in reqs if r["activity"] == "read")["priority_label"] == "nice_to_have"  # not "hobby"


def test_unmapped_ritual_forces_review_not_pass():
    persona = {"daily_rituals": ["I do something the taxonomy can't name"]}
    r = P.check(_room(_el("wardrobe")), persona)
    assert r["status"] == "WARN"                        # headline agrees with report()'s REVIEW
    results, verdict = P.report(_room(_el("wardrobe")), persona)
    assert verdict == "REVIEW" and any(x["check"] == "persona:unmapped-ritual" for x in results)


# ---------------------------------------------------------------- persona discovery (deliverable wiring)
def test_find_persona_inline_dict_and_absent():
    assert P.find_persona_for({"persona": {"persona_id": "X"}})["persona_id"] == "X"
    assert P.find_persona_for({"items": []}) == {}     # no persona anywhere -> {} (no-op, never throws)
    assert P.find_persona_for("not-a-dict") == {}


def test_find_persona_by_path_relative_to_spec():
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", "living_condo.json")
    got = P.find_persona_for({"persona": "persona_condo_demo.json"}, spec_path)
    assert got.get("persona_id") == "DEMO-condo-01"


def test_markdown_carries_gap_and_does_not_throw():
    md = P.to_markdown([_spec("living_condo.json"), _spec("bedroom_suite.json")],
                       _spec("persona_condo_demo.json"), name="home")
    assert "PERSONA COVERAGE" in md and "GAP" in md


# ---------------------------------------------------------------- rationale integration
def test_rationale_presence_upgrades_with_persona():
    spec = _spec("living_condo.json")
    persona = _spec("persona_condo_demo.json")
    rep = R.report(spec, persona)
    sofa = next(r for r in rep["elements"] if r["kind"] == "sofa")
    assert sofa["presence_why"]["grounded"] == "persona"
    assert "serves" in sofa["presence_why"]["text"]
    side = next(r for r in rep["elements"] if r["kind"] == "sideboard")
    assert side["presence_why"]["grounded"] == "activity"      # baseline dwelling need


def test_rationale_without_persona_is_unchanged():
    # the persona-less path must be byte-identical to before (presence never 'persona')
    rep = R.report(_spec("living_condo.json"))
    assert all(r["presence_why"]["grounded"] != "persona" for r in rep["elements"])


TESTS = [test_kind_activity_deterministic, test_name_signal_is_soft_and_unions_with_kind,
         test_serves_tag_wins_over_kind, test_unknown_serves_falls_back_to_kind,
         test_polymorphic_untagged_is_ambiguous_never_guessed, test_vanity_stool_recovered_by_name,
         test_baseline_vs_lifestyle_split, test_kind_map_reuses_placement_logic_sets,
         test_structured_activity_is_consumed_prose_is_flagged, test_priority_merges_ritual_and_must_have,
         test_wfh_implies_work, test_gap_when_no_room_serves, test_met_when_any_room_serves_home_aware,
         test_orphan_lifestyle_element_not_in_persona, test_baseline_element_is_never_orphan,
         test_ambiguous_element_flagged, test_demo_two_gaps_and_read_met,
         test_report_shape_prefixes_and_never_fails, test_no_persona_is_unwired, test_report_row_shape,
         test_degrades_on_malformed_spec, test_degrades_on_non_dict_element, test_degrades_on_non_dict_subroom,
         test_degrades_on_malformed_persona, test_rationale_degrades_on_non_dict_rationale_and_element,
         test_markdown_carries_gap_and_does_not_throw, test_rationale_presence_upgrades_with_persona,
         test_rationale_without_persona_is_unchanged,
         test_fused_baseline_element_still_orphan_for_unstated_lifestyle,
         test_soft_name_signal_met_is_flagged_soft, test_unknown_serves_tag_is_surfaced_not_swallowed,
         test_entertaining_never_makes_no_requirement, test_priority_label_not_mislabelled_by_shared_numeric,
         test_unmapped_ritual_forces_review_not_pass,
         test_find_persona_inline_dict_and_absent, test_find_persona_by_path_relative_to_spec]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
