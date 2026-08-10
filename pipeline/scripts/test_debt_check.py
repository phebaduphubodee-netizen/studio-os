"""Tests for debt_check — the ledger that stops an accepted critic item from
being closed by a sentence.

The negative controls are the ways a debt can LOOK paid without being paid, and
every one of them is a move this repo has already made:

  * closed with prose              — 357 items filed, ~22 built. The whole reason.
  * closed against a SPEC          — "the file that renders is not automatically
                                     the file of record"; a spec is what we said.
  * refuted with taste             — R7 allows a refutation only WITH A
                                     MEASUREMENT, and nine flattering scorers
                                     came from the builder judging the builder.
  * the row quietly deleted        — the exact shape of the original defect.
  * a door onto nothing            — decisions_check's `where` naming a path that
                                     does not exist, applied to instruments.
  * a guard exonerating an absence — delete the headboard and nothing floats.
                                     R9b: a rule that names the objects it
                                     applies to will always exempt the next one.

The last tests walk the SHIPPED ledger and the lane's real spec rather than a
fixture, for the reason test_contact_check learned: a rule proved on a hand-made
dict is proved about the dict.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import debt_check as DC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASES = ["P0", "P1", "P2", "P3", "P4", "P5"]
STANDARD = {"rows": {"D1": {"metric": "mp", "direction": "min", "threshold": 2.0},
                     "D3": {"metric": "stops", "direction": "min", "threshold": 3.0},
                     "D5": {"metric": "octave_energy", "direction": "band",
                            "threshold": [6.0, 12.0]},
                     "D7": {"metric": "loose_objects", "direction": "min",
                            "threshold": 12},
                     "D8": {"metric": "primitive_acquire_class",
                            "direction": "max", "threshold": 0},
                     "D9": {"metric": "flat_shaded_curved", "direction": "max",
                            "threshold": 0}}}


def row(**kw):
    r = {"id": "DEBT-01", "defect": "soft goods read rigid", "object": "pillows",
         "kind": "geometry", "filed_in": "TRN-002",
         "recurrence": {"files": 28, "of": 28, "first_round": "r14",
                        "last_round": "r38b"},
         "crosses_into": "DELIV-001", "due_phase": "P2",
         "closes_when": {"door": "scene_row", "row": "D8"}, "status": "open"}
    r.update(kw)
    return r


def ledger(*rows, corpus=28):
    return {"_seeded_from": {"answer_files": corpus, "items_filed": 367},
            "rows": list(rows) or [row()]}


def v(l, **kw):
    kw.setdefault("plan_phases", PHASES)
    kw.setdefault("standard", STANDARD)
    return DC.check(l, **kw)


# ------------------------------------------------------------ well-formedness --

def test_a_well_formed_row_passes():
    assert v(ledger()) == []


def test_a_missing_ledger_names_the_file_and_never_raises():
    assert DC.load(os.path.join(REPO, "qa", "no-such-ledger.json")) is None
    out = DC.check(None)
    assert len(out) == 1 and "critic-debt" in out[0]


def test_a_malformed_ledger_is_none_not_a_traceback(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert DC.load(str(p)) is None


def test_missing_required_fields_are_named():
    r = row()
    del r["due_phase"], r["crosses_into"]
    out = v(ledger(r))
    assert any("due_phase" in s and "crosses_into" in s for s in out)


def test_a_duplicate_id_is_refused():
    out = v(ledger(row(), row()))
    assert any("declared twice" in s for s in out)


def test_status_outside_the_three_is_refused_by_name():
    out = v(ledger(row(status="accepted")))
    assert any("'accepted'" in s and "fourth value" in s for s in out)


def test_a_due_phase_the_plan_does_not_have_is_due_never():
    out = v(ledger(row(due_phase="P9")))
    assert any("due never" in s for s in out)


def test_recurrence_cannot_exceed_the_corpus():
    out = v(ledger(row(recurrence={"files": 40, "of": 28})))
    assert any("more files than the corpus holds" in s for s in out)


def test_two_denominators_break_the_ranking():
    out = v(ledger(row(recurrence={"files": 9, "of": 12})))
    assert any("Two denominators" in s for s in out)


# -------------------------------------------------------------------- the doors --

def test_a_row_with_no_door_is_refused():
    out = v(ledger(row(closes_when={"door": "somebody says so"})))
    assert any("closes_when.door" in s for s in out)


def test_an_image_row_door_may_not_name_a_scene_row():
    out = v(ledger(row(closes_when={"door": "image_row", "row": "D8"})))
    assert any("must name one of" in s for s in out)


def test_a_door_onto_a_row_the_standard_does_not_have_is_refused():
    out = v(ledger(row(closes_when={"door": "image_row", "row": "D2"})))
    assert any("not in" in s and "deliverable-standard" in s for s in out)


def test_an_object_door_needs_something_to_look_for():
    out = v(ledger(row(closes_when={"door": "object", "min_count": 1})))
    assert any("needs `match`" in s for s in out)


def test_none_yet_must_say_what_would_have_to_be_built():
    out = v(ledger(row(closes_when={"door": "none_yet"})))
    assert any("blocked_on" in s and "escape" in s for s in out)


def test_a_guard_door_onto_an_unknown_module_is_refused():
    out = v(ledger(row(closes_when={"door": "guard", "module": "vibes_check",
                                    "verdict": "FLOATING", "covers": "x"})))
    assert any("must name one of" in s for s in out)


def test_a_guard_door_onto_a_verdict_the_guard_never_emits_is_refused():
    out = v(ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                    "verdict": "UGLY", "covers": "x"})))
    assert any("never returns" in s for s in out)


def test_a_guard_door_must_declare_what_it_covers():
    out = v(ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                    "verdict": "FLOATING"})))
    assert any("COVERS" in s for s in out)


# ------------------------------------------------------------------- closing --

def test_built_with_no_evidence_is_a_sentence_not_a_closure():
    out = v(ledger(row(status="built", closed_by={"how": ""})))
    assert any("not through a sentence" in s for s in out)


def test_built_against_a_file_that_is_not_there_closed_against_nothing():
    out = v(ledger(row(status="built",
                       closed_by={"how": "D8 went to 0",
                                  "evidence": "renders/ghost.placement.json"})))
    assert any("does not exist" in s for s in out)


def test_built_against_a_spec_is_refused_because_a_spec_is_a_declaration():
    """An `object` door offered a spec. The spec IS recognised — by content — and
    refused for this door, which is different from not recognising it."""
    out = v(ledger(row(closes_when={"door": "object", "match": "lamp",
                                    "min_count": 1, "covers": "presence only"},
                       status="built",
                       closed_by={"how": "a lamp exists",
                                  "evidence": "training/TRN-002/spec_r38.json"})))
    assert any("a SPEC" in s and "what was BUILT" in s for s in out)


def test_a_spec_renamed_is_still_a_spec():
    """THE FILENAME HOLE. The first version refused a `.json` whose basename
    contained "spec"; renaming it to r38.json defeated the entire rule. Evidence
    is judged by CONTENT — the same lesson `reachability_check` learned when a
    prose MENTION of a module counted as calling it."""
    import shutil
    src = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    dst = os.path.join(REPO, "training", "TRN-002", "_tmp_renamed_r38.json")
    shutil.copyfile(src, dst)
    try:
        out = v(ledger(row(closes_when={"door": "object", "match": "lamp",
                                        "min_count": 1, "covers": "presence"},
                           status="built",
                           closed_by={"how": "x",
                                      "evidence": "training/TRN-002/"
                                                  "_tmp_renamed_r38.json"})))
        assert any("a SPEC" in s for s in out), out
    finally:
        os.remove(dst)


def test_a_built_row_reruns_its_own_door(tmp_path):
    """THE RULE, and the regression pin for the defect this module shipped with:
    `built` was verified by os.path.exists and a substring, so the 28-of-28 cloth
    row closed on the sentence "soft goods now drape" plus CLAUDE.md, and
    resolve() and due_now() skipped it forever after."""
    dump = tmp_path / "d.placement.json"
    dump.write_text(json.dumps({"objects": [
        {"name": "SM_X_chair_seat", "type": "MESH", "hidden_render": False,
         "rot_deg": [0, 0, 0], "min": [0, 0, 0], "max": [400, 400, 450]}]}),
        encoding="utf-8")
    # the door says >=2 pulls; the dump has none, so the closure is a lie
    r = row(closes_when={"door": "object", "match": "pull", "min_count": 2,
                         "covers": "pulls only"},
            status="built",
            closed_by={"how": "handles fitted", "evidence": str(dump)})
    out = DC.check(ledger(r), plan_phases=PHASES, standard=STANDARD, repo_root="/")
    assert any("re-running its own door" in s and "UNRESOLVED" in s for s in out), out


def test_a_row_closed_against_real_built_evidence_passes(tmp_path):
    """The accept side. Without this, tightening the rule until nothing can ever
    close would look identical to getting it right."""
    dump = tmp_path / "d.placement.json"
    dump.write_text(json.dumps({"objects": [
        {"name": "SM_X_pull_L", "type": "MESH", "hidden_render": False,
         "rot_deg": [0, 0, 0], "min": [0, 0, 0], "max": [20, 20, 120]},
        {"name": "SM_X_pull_R", "type": "MESH", "hidden_render": False,
         "rot_deg": [0, 0, 0], "min": [500, 0, 0], "max": [520, 20, 120]}]}),
        encoding="utf-8")
    r = row(closes_when={"door": "object", "match": "pull", "min_count": 2,
                         "covers": "pulls only"},
            status="built",
            closed_by={"how": "two pulls built", "evidence": str(dump)})
    assert DC.check(ledger(r), plan_phases=PHASES, standard=STANDARD,
                    repo_root="/") == []


def test_built_through_a_none_yet_door_is_a_contradiction():
    out = v(ledger(row(status="built",
                       closes_when={"door": "none_yet", "blocked_on": "an eye"},
                       closed_by={"how": "x", "evidence": "CLAUDE.md"})))
    assert any("One of the two is false" in s for s in out)


def test_a_refutation_with_no_number_is_taste():
    out = v(ledger(row(status="refuted",
                       refuted_by="it looks fine to me",
                       measured_in="CLAUDE.md")))
    assert any("never with taste" in s for s in out)


def test_a_refutation_with_a_number_but_no_file_is_refused():
    out = v(ledger(row(status="refuted", refuted_by="measured 8.4 mm",
                       measured_in="docs/nowhere.md")))
    assert any("does not exist" in s for s in out)


def test_a_measured_refutation_passes():
    assert v(ledger(row(status="refuted", refuted_by="measured 8.4 mm",
                        measured_in="CLAUDE.md"))) == []


# ------------------------------------------------------------------ the ratchet --

def test_a_row_may_change_status():
    was = ledger(row(status="open"))
    now = ledger(row(status="refuted", refuted_by="8.4 mm", measured_in="CLAUDE.md"))
    assert DC.ratchet(now, previous=was) == []


def test_a_row_may_never_vanish():
    was = ledger(row(id="DEBT-01"), row(id="DEBT-02"))
    now = ledger(row(id="DEBT-01"))
    out = DC.ratchet(now, previous=was)
    assert out and "DEBT-02" in out[0] and "never vanish" in out[0]


# ----------------------------------------------------------------- resolving --

SCENE = {"objects": [
    {"name": "SM_X_floor", "type": "MESH", "rot_deg": [0, 0, 0],
     "min": [0, 0, 0], "max": [4000, 4000, 10]},
    {"name": "SM_X_bed_headboard", "type": "MESH", "rot_deg": [0, 0, 0],
     "min": [100, 100, 10], "max": [2000, 200, 900]},
    {"name": "SM_X_lamp_bedside", "type": "MESH", "rot_deg": [0, 0, 0],
     "min": [300, 300, 10], "max": [400, 400, 500]},
]}


def by_id(res):
    return {r[0]: (r[1], r[2]) for r in res}


def test_an_object_door_resolves_against_the_built_scene():
    l = ledger(row(closes_when={"door": "object", "match": "lamp",
                                "min_count": 1}))
    assert by_id(DC.resolve(l, scene=SCENE, standard=STANDARD))["DEBT-01"][0] \
        == "RESOLVED"


def test_an_object_door_that_is_short_is_unresolved():
    l = ledger(row(closes_when={"door": "object", "match": "lamp",
                                "min_count": 3}))
    assert by_id(DC.resolve(l, scene=SCENE, standard=STANDARD))["DEBT-01"][0] \
        == "UNRESOLVED"


def test_the_sm_prefix_does_not_hide_the_object():
    assert "bed_headboard" in DC.scene_names(SCENE)


def test_a_spec_alone_is_declared_only_and_never_resolved():
    l = ledger(row(closes_when={"door": "object", "match": "lamp",
                                "min_count": 1}))
    spec = {"masses": [{"name": "lamp_bedside"}]}
    got = by_id(DC.resolve(l, spec=spec, standard=STANDARD))["DEBT-01"]
    assert got[0] == "DECLARED-ONLY" and "not a built scene" in got[1]


def test_a_scene_row_that_passes_on_a_spec_is_still_only_declared():
    l = ledger(row(closes_when={"door": "scene_row", "row": "D9"}))
    spec = {"masses": [{"name": "vase", "kind": "box"}]}   # 0 flat-shaded curved
    got = by_id(DC.resolve(l, spec=spec, standard=STANDARD))["DEBT-01"]
    assert got[0] == "DECLARED-ONLY"


def test_no_evidence_is_not_run_and_not_run_is_never_a_pass():
    l = ledger(row(closes_when={"door": "scene_row", "row": "D8"}))
    got = by_id(DC.resolve(l, standard=STANDARD))["DEBT-01"]
    assert got[0] == "NOT RUN"


def test_a_none_yet_row_is_never_resolved_by_any_evidence():
    l = ledger(row(closes_when={"door": "none_yet", "blocked_on": "an eye"}))
    got = by_id(DC.resolve(l, scene=SCENE, spec={"masses": []},
                           standard=STANDARD))["DEBT-01"]
    assert got[0] == "NOT RUN"


def test_a_hidden_mass_cannot_pay_an_object_door():
    """Hiding a mass must not close its debt. `hidden_render` is excluded from the
    frame, so an ABSENCE door paid by one is paid by nothing a viewer can see."""
    l = ledger(row(closes_when={"door": "object", "match": "lamp",
                                "min_count": 1, "covers": "presence"}))
    hidden = {"objects": [dict(o, hidden_render=True) for o in SCENE["objects"]]}
    assert by_id(DC.resolve(l, scene=hidden, standard=STANDARD))["DEBT-01"][0] \
        == "UNRESOLVED"


def test_a_light_named_like_the_object_is_not_the_object():
    """A LIGHT datablock called `lamp_glow` has no geometry and `placement_check`
    never examines it. It must not satisfy 'there is a lamp in the built scene'."""
    l = ledger(row(closes_when={"door": "object", "match": "lamp",
                                "min_count": 1, "covers": "presence"}))
    lights = {"objects": [{"name": "SM_X_lamp_glow", "type": "LIGHT",
                           "hidden_render": False, "rot_deg": [0, 0, 0],
                           "min": [0, 0, 0], "max": [0, 0, 0]}]}
    assert by_id(DC.resolve(l, scene=lights, standard=STANDARD))["DEBT-01"][0] \
        == "UNRESOLVED"


def test_the_guard_presence_test_uses_the_drawable_population():
    """Hiding the headboard must not turn its row into 'nothing floats'."""
    l = ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                "verdict": "FLOATING", "match": "headboard",
                                "covers": "support only"}))
    hidden = {"objects": [dict(o, hidden_render="headboard" in o["name"])
                          for o in SCENE["objects"]]}
    got = by_id(DC.resolve(l, scene=hidden, standard=STANDARD))["DEBT-01"]
    assert got[0] == "UNRESOLVED" and "not there" in got[1]


def _png(path, kind):
    from PIL import Image
    import numpy as np
    if kind == "flat":
        a = np.full((240, 320, 3), 128, dtype=np.uint8)
    else:                                   # a real range: true black to white
        g = np.linspace(0, 255, 320, dtype=np.uint8)
        a = np.dstack([np.tile(g, (240, 1))] * 3)
    Image.fromarray(a).save(path)
    return str(path)


def test_an_image_row_door_opens_the_picture(tmp_path):
    """R11. The image_row door is the only one that reads pixels, and no test
    resolved one against a frame — inverting its comparison left every test green
    while the flat-light row would have RESOLVED on the flattest frames."""
    import deliverable_check as DCH
    std = DCH.load_standard()
    l = ledger(row(closes_when={"door": "image_row", "row": "D3"}))
    p = _png(tmp_path / "range.png", "range")
    got = by_id(DC.resolve(l, frame=p, standard=std))["DEBT-01"]
    assert got[0] == "RESOLVED"
    # cross-check against the instrument itself, not against a literal
    assert str(DCH.measure_image(p)["stops"]) in got[1]


def test_a_flat_frame_cannot_pay_the_flat_light_debt(tmp_path):
    """The negative control. A uniform grey frame is the defect itself."""
    import deliverable_check as DCH
    l = ledger(row(closes_when={"door": "image_row", "row": "D3"}))
    got = by_id(DC.resolve(l, frame=_png(tmp_path / "flat.png", "flat"),
                           standard=DCH.load_standard()))["DEBT-01"]
    assert got[0] == "UNRESOLVED"


def test_a_guard_door_reads_the_built_scene():
    l = ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                "verdict": "FLOATING", "match": "headboard",
                                "covers": "support only"}))
    got = by_id(DC.resolve(l, scene=SCENE, standard=STANDARD))["DEBT-01"]
    assert got[0] == "PARTIAL" and "COVERS ONLY" in got[1]


def test_a_guard_cannot_exonerate_an_object_that_is_not_there():
    """Delete the headboard and nothing floats. The row must NOT close."""
    l = ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                "verdict": "FLOATING", "match": "headboard",
                                "covers": "support only"}))
    gone = {"objects": [o for o in SCENE["objects"]
                        if "headboard" not in o["name"]]}
    got = by_id(DC.resolve(l, scene=gone, standard=STANDARD))["DEBT-01"]
    assert got[0] == "UNRESOLVED" and "not there" in got[1]


def test_a_guard_finding_leaves_the_row_open():
    l = ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                "verdict": "FLOATING", "match": "shade",
                                "covers": "support only"}))
    floating = {"objects": SCENE["objects"] + [
        {"name": "SM_X_lamp_shade", "type": "MESH", "rot_deg": [0, 0, 0],
         "min": [3000, 3000, 1800], "max": [3200, 3200, 2000]}]}
    got = by_id(DC.resolve(l, scene=floating, standard=STANDARD))["DEBT-01"]
    assert got[0] == "UNRESOLVED" and "FLOATING" in got[1]


def test_a_guard_with_no_dump_is_not_run_never_resolved():
    l = ledger(row(closes_when={"door": "guard", "module": "placement_check",
                                "verdict": "OVERHANG", "covers": "AABB only"}))
    got = by_id(DC.resolve(l, standard=STANDARD))["DEBT-01"]
    assert got[0] == "NOT RUN"


# ---------------------------------------------------------------- what is due --

def test_a_debt_due_later_is_owed_not_failed():
    l = ledger(row(due_phase="P4"))
    assert DC.due_now(l, PHASES, "P1") == []


def test_a_debt_whose_phase_has_arrived_is_due():
    l = ledger(row(due_phase="P2"))
    assert DC.due_now(l, PHASES, "P2") == ["DEBT-01"]
    assert DC.due_now(l, PHASES, "P4") == ["DEBT-01"]


def test_a_closed_row_is_never_due():
    l = ledger(row(due_phase="P2", status="refuted", refuted_by="8 mm",
                   measured_in="CLAUDE.md"))
    assert DC.due_now(l, PHASES, "P4") == []


# ------------------------------------------------------------- the spec refusal --

def test_refuse_spec_names_the_file():
    out = DC.refuse_spec(ledger(), {"id": "TRN-002", "masses": []}, "spec_r38.json")
    assert out and "spec_r38.json" in out[0] and "SPEC" in out[0]
    assert any("CLOSING IS NOT DISCHARGING" in s for s in out)


def test_a_ledger_with_nothing_open_does_not_refuse_a_spec():
    l = ledger(row(status="refuted", refuted_by="8 mm", measured_in="CLAUDE.md"))
    assert DC.refuse_spec(l, {"id": "TRN-002", "masses": []}, "spec.json") == []


# ------------------------------------------------------------ the shipped files --

def test_the_shipped_ledger_is_honest():
    l = DC.load()
    assert l is not None, "qa/critic-debt.json must exist"
    import deliverable_check as DCH
    assert DC.check(l, plan_phases=DC._plan_phases(),
                    standard=DCH.load_standard()) == []


def test_the_shipped_ledger_carries_the_seeded_rows_and_their_counts():
    l = DC.load()
    rows = DC.rows(l)
    assert len(rows) >= 20, "the plan asks for the top-20 by recurrence"
    assert all(r["closes_when"]["door"] in DC.DOORS for r in rows)
    assert {r["id"] for r in rows} == {f"DEBT-{i:02d}"
                                       for i in range(1, len(rows) + 1)}
    top = rows[0]
    assert top["recurrence"]["files"] == 28 and top["recurrence"]["of"] == 28


def test_the_ledger_reports_what_no_instrument_can_see():
    """The honest counterweight. If this ever reads 0 without the doors changing,
    someone has quietly bound a defect to an instrument that cannot see it."""
    l = DC.load()
    t = DC.tally(l)
    assert t["none_yet"] > 0
    assert "no instrument" in DC.one_line(l)


def test_debt_check_refuses_spec_r38_by_name():
    """P0's exit test, item 5. r38 is TRN-002's last frame and the unit is being
    closed; closing it may not discharge a single row."""
    l = DC.load()
    p = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    out = DC.refuse_spec(l, spec, p)
    assert out, "spec_r38.json must be refused"
    assert "spec_r38.json" in out[0]
    assert any("TRN-002" in s for s in out)


def test_no_shipped_row_resolves_against_the_frame_that_filed_it():
    """Every one of the 21 rows was filed AGAINST r38. If any door resolves there,
    that door is matching the wrong thing — which is exactly what DEBT-10 did:
    `match: "handle"` was paid by `door_handle`, the ENTRANCE door's lever, while
    the wardrobe it was filed about had no hardware at all."""
    import deliverable_check as DCH
    p = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    dump = {"objects": [{"name": f"SM_TRN002_{m['name']}", "type": "MESH",
                         "hidden_render": False, "rot_deg": [0, 0, 0],
                         "min": [0, 0, 0], "max": [100, 100, 100]}
                        for m in spec["masses"]]}
    got = DC.resolve(DC.load(), scene=dump, spec=spec,
                     standard=DCH.load_standard())
    resolved = [(rid, d) for rid, verdict, d in got if verdict == "RESOLVED"]
    assert not resolved, f"a door resolved on the frame that filed it: {resolved}"


def test_object_doors_must_say_what_they_cover():
    out = v(ledger(row(closes_when={"door": "object", "match": "lamp",
                                    "min_count": 1})))
    assert any("COVERS" in s for s in out)


def test_min_count_true_is_not_one():
    """`isinstance(True, int)` is True, so `min_count: true` silently meant 1."""
    out = v(ledger(row(closes_when={"door": "object", "match": "x",
                                    "min_count": True, "covers": "y"})))
    assert any("positive integer" in s for s in out)


def test_a_bad_min_count_does_not_crash_resolve():
    """main() resolves BEFORE printing violations, so a bare int() here threw and
    took the violation list with it — a traceback replacing the named refusal."""
    l = ledger(row(closes_when={"door": "object", "match": "x",
                                "min_count": "two", "covers": "y"}))
    assert by_id(DC.resolve(l, scene=SCENE, standard=STANDARD))["DEBT-01"][0] \
        == "NOT RUN"


def test_a_truthy_non_dict_does_not_crash_the_gate_or_the_session_opener():
    """`(x or {}).get(...)` defends against None and lets a scalar through, so one
    mistyped field raised AttributeError out of rule_gate and plan_status — a
    traceback in the two paths load() promises will produce a named violation."""
    bad = {"_seeded_from": "twenty-eight files",
           "rows": [row(closes_when="scene_row D8", recurrence=[28, 28])]}
    DC.tally(bad)
    DC.one_line(bad)
    assert DC.check(bad, plan_phases=PHASES, standard=STANDARD)
    DC.resolve(bad, standard=STANDARD)
    DC.refuse_spec(bad, {"id": "TRN-002", "masses": []}, "spec.json")


def test_refuse_spec_survives_a_row_with_no_filed_in():
    """It filtered with .get and reported with [], so a malformation check() names
    raised KeyError first — inside main(), before the report could print."""
    r = row()
    del r["filed_in"]
    out = DC.refuse_spec(ledger(r), {"id": "TRN-002", "masses": []}, "spec.json")
    assert out and "spec.json" in out[0]


def test_an_empty_filed_in_does_not_match_every_spec():
    out = DC.refuse_spec(ledger(row(filed_in="")),
                         {"id": "TRN-002", "masses": []}, "spec.json")
    assert not any("filed against this spec's own unit" in s for s in out)


def test_an_unreadable_plan_is_unknown_not_nothing_owed():
    """With no plan, nothing can be DUE — and that silence turned the whole
    DUE-AND-UNPAID bite off while the run printed the all-clear."""
    out = DC.check(ledger(), plan_phases=[], standard=STANDARD)
    assert any("plan could not be read" in s and "unknown" in s for s in out)


def test_the_exit_codes_are_the_contract(capsys):
    """0 = the ledger is honest, 1 = it is not (or a spec was offered as
    discharge), 2 = COULD NOT RUN. The third one is the point of having them:
    `pixel_check` carries the same contract because a caller that cannot tell 2
    from 0 eventually reads 'not run' as 'passed'."""
    assert DC.main([]) == 0
    spec = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    assert DC.main(["--spec", spec]) == 1
    capsys.readouterr()


def test_could_not_run_is_not_softenable(capsys):
    """`--soft` downgrades a VIOLATION, never a failure to look. A ledger that
    cannot be read must not print like a ledger with nothing in it."""
    missing = os.path.join(REPO, "qa", "no-such-ledger.json")
    assert DC.main(["--ledger", missing]) == 2
    assert DC.main(["--ledger", missing, "--soft"]) == 2
    capsys.readouterr()


def test_a_due_and_unresolved_row_fails_the_run(capsys):
    """The bite. A P2 debt is owed while the lane is at P0 and must not fail —
    halting on owed work is the enforcement clause R3 revoked. The moment its own
    phase arrives, the same row is the builder's side slipping, which is exactly
    what `decisions_check` blocks on."""
    spec = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    assert DC.main(["--spec", spec, "--scene", os.devnull]) == 2  # unreadable
    capsys.readouterr()
    l = DC.load()
    phases = DC._plan_phases()
    assert DC.due_now(l, phases, "P0") == []
    assert DC.due_now(l, phases, "P2"), "P2 debts must come due at P2"


def test_the_real_r38_frame_leaves_the_soft_goods_row_open():
    """A pin on the instrument, not on the ledger: D8 counts 7 primitives in the
    R8-ACQUIRE class on r38, so the 28-of-28 row cannot resolve there."""
    import deliverable_check as DCH
    p = os.path.join(REPO, "training", "TRN-002", "spec_r38.json")
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    l = DC.load()
    got = by_id(DC.resolve(l, spec=spec, standard=DCH.load_standard()))
    assert got["DEBT-01"][0] == "UNRESOLVED"
    assert "primitive_acquire_class=7" in got["DEBT-01"][1]
