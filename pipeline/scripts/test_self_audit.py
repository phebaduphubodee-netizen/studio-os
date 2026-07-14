"""
test_self_audit.py -- unit tests for the owner-free doubt aggregator.

Pins the taxonomy (which count maps to which severity), the two invariants that make the
list trustworthy -- FAIL (confident-wrong) ranks a band above REVIEW (doubt), and an
owner-resolved doubt leaves the ranked list -- plus schema-drift resilience (a v3 marker
missing the new keys must degrade to 0, never KeyError) and coverage honesty (a source
that persists nothing reports UNWIRED, never a silent clean pass).
"""
import self_audit as A


def _gate(rooms, **top):
    g = {"verdict": "REVIEW", "calibration": "PASS", "calibration_fails": [], "rooms": rooms}
    g.update(top)
    return g


def _room(name, **counts):
    r = {"room": name, "verdict": "REVIEW", "floating": []}
    r.update(counts)
    return r


# ---- collect_gate: taxonomy ------------------------------------------------------------
def test_each_count_maps_to_a_record_with_expected_severity():
    g = _gate([_room("bed", unplaced=1, merged_regions=2, identity_flags=1, facing_flags=3,
                      zone_open=1, long_thin=4, kind_flags=1, zone_flags=1)])
    recs = A.collect_gate(g)
    by = {r["kind"]: r for r in recs}
    assert by["unplaced"]["severity"] == "HIGH"
    assert by["merged_blob"]["severity"] == "HIGH" and by["merged_blob"]["count"] == 2
    assert by["identity"]["severity"] == "HIGH"
    assert by["facing"]["severity"] == "MEDIUM" and by["facing"]["count"] == 3
    assert by["zone_open"]["severity"] == "MEDIUM"
    assert by["long_thin"]["severity"] == "LOW" and by["long_thin"]["count"] == 4
    assert by["kind_regression"]["severity"] == "CRITICAL"
    assert by["zone_regression"]["severity"] == "CRITICAL"


def test_zero_counts_emit_nothing():
    recs = A.collect_gate(_gate([_room("bed", unplaced=0, merged_regions=0, facing_flags=0)]))
    assert recs == []


def test_dismissed_is_never_counted_as_open_doubt():
    # dismissed = owner already signed the blob off; the gate marker is post-adjudication
    recs = A.collect_gate(_gate([_room("bed", dismissed=5, merged_regions=0)]))
    assert not any(r["kind"] == "merged_blob" for r in recs)
    assert recs == []


def test_floating_is_critical_fail_not_doubt():
    recs = A.collect_gate(_gate([_room("bed", floating=["sofa_01", "bed_01"])]))
    f = next(r for r in recs if r["kind"] == "floating")
    assert f["severity"] == "CRITICAL" and f["count"] == 2 and f["scope"] == "room"


def test_calibration_fail_is_critical_project_scope():
    g = _gate([], calibration="FAIL", calibration_fails=[{"axis": "x", "mm": 6000}])
    recs = A.collect_gate(g)
    c = next(r for r in recs if r["kind"] == "calibration_fail")
    assert c["severity"] == "CRITICAL" and c["scope"] == "project"


def test_orphaned_signature_and_geo_orphan():
    g = _gate([], signature_reconcile={"checked": True, "matched": 1,
                                       "orphaned_names": ["bed_01"]},
              zone_reconcile={"checked": True, "matched": 0, "name_orphans": [],
                              "geo_orphans": 2})
    recs = A.collect_gate(g)
    assert any(r["kind"] == "orphaned_signature" and r["severity"] == "CRITICAL"
               for r in recs)
    geo = next(r for r in recs if r["kind"] == "geo_orphan_zone")
    assert geo["severity"] == "MEDIUM" and geo["count"] == 2


def test_v3_marker_missing_new_keys_does_not_crash():
    # older schema: no kind_flags/zone_flags/zone_*/signature_reconcile/zone_reconcile
    old = {"verdict": "REVIEW", "rooms": [{"room": "bed", "verdict": "REVIEW",
                                           "floating": [], "unplaced": 1}]}
    recs = A.collect_gate(old)                                # must not raise
    assert [r["kind"] for r in recs] == ["unplaced"]


# ---- facade suppression ----------------------------------------------------------------
def test_facade_candidate_open_without_signature():
    fac = {"candidates": [{"room": "sitting_room", "c": 98.9, "score": 5,
                           "tier": "glazed_facade", "length_mm": 4897}]}
    recs = A.collect_facade(fac, review={"confirmed": []})
    assert len(recs) == 1 and recs[0]["resolved"] is False
    assert recs[0]["severity"] == "MEDIUM"                   # score 5 -> MEDIUM


def test_facade_candidate_resolved_by_owner_sign():
    fac = {"candidates": [{"room": "sitting_room", "c": 98.9, "score": 5}]}
    review = {"confirmed": [{"room": "sitting_room", "facade": True, "c": 100.0,
                             "by": "owner (2026-07-08)"}]}
    recs = A.collect_facade(fac, review=review)
    assert recs[0]["resolved"] is True
    # a pending template must NOT resolve it
    review["confirmed"][0]["by"] = "OWNER-CONFIRM-PENDING (unsigned template)"
    assert A.collect_facade(fac, review=review)[0]["resolved"] is False


def test_weak_facade_candidate_is_low():
    fac = {"candidates": [{"room": "x", "c": 0, "score": 4, "tier": "glazed_facade"}]}
    assert A.collect_facade(fac)[0]["severity"] == "LOW"


def test_facade_wildcard_room_sign_resolves():
    # confirmed_facade contract supports a '*' room wildcard; the audit must honour it
    fac = {"candidates": [{"room": "sitting_room", "c": 100, "score": 5}]}
    review = {"confirmed": [{"room": "*", "facade": True, "c": 100.0, "by": "owner"}]}
    assert A.collect_facade(fac, review=review)[0]["resolved"] is True


def test_facade_non_bool_facade_does_not_resolve():
    # a facade:null / stringy entry is NOT a real sign -> must stay OPEN (no false suppress)
    fac = {"candidates": [{"room": "sitting_room", "c": 100, "score": 5}]}
    for bad in (None, "true", 1):
        review = {"confirmed": [{"room": "sitting_room", "facade": bad, "c": 100, "by": "o"}]}
        assert A.collect_facade(fac, review=review)[0]["resolved"] is False, bad


def test_facade_non_numeric_offset_does_not_crash_and_resolves():
    # a hand-edited non-numeric `c` on a real signed facade must not abort the audit
    fac = {"candidates": [{"room": "sitting_room", "c": 100, "score": 5}]}
    review = {"confirmed": [{"room": "sitting_room", "facade": True, "c": "n/a", "by": "o"}]}
    assert A.collect_facade(fac, review=review)[0]["resolved"] is True   # no exception


# ---- glazing is summarised, not enumerated ---------------------------------------------
def test_glazing_collapses_to_one_low_record():
    glz = {"candidates": [{"tier": "strong", "confirms_manual_patch": False}] * 200
                         + [{"tier": "weak", "confirms_manual_patch": False}] * 98}
    recs = A.collect_glazing(glz)
    assert len(recs) == 1 and recs[0]["severity"] == "LOW"
    # count is DOUBT multiplicity (one pile to skim); the raw 298 is magnitude + in detail
    assert recs[0]["count"] == 1 and recs[0]["magnitude"] == 298
    assert "298 unresolved" in recs[0]["detail"] and "200 strong" in recs[0]["detail"]


def test_glazing_resolved_runs_are_excluded():
    glz = {"candidates": [{"tier": "strong", "confirms_manual_patch": True},
                          {"tier": "weak", "confirms_manual_patch": False}]}
    recs = A.collect_glazing(glz)
    assert recs[0]["magnitude"] == 1                         # only the unresolved one counted


def test_glazing_all_resolved_emits_nothing():
    glz = {"candidates": [{"tier": "strong", "confirms_manual_patch": True}]}
    assert A.collect_glazing(glz) == []


# ---- ranking + scoring -----------------------------------------------------------------
def test_ranking_orders_critical_over_high_over_medium_over_low():
    recs = (A.collect_gate(_gate([_room("bed", long_thin=1, merged_regions=1, facing_flags=1,
                                        kind_flags=1)])))
    ranked = A.rank(recs)
    order = [r["severity"] for r in ranked]
    assert order == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def test_high_count_low_never_outranks_low_count_medium():
    # the exact bug the first live run exposed: a 294-count LOW glazing pile sorted ABOVE
    # the MEDIUM facade doubt. Band must dominate count.
    low_pile = A._rec("glazing", "glazing_unresolved", "global", "LOW", 294, "", "", "")
    med = A._rec("facade", "facade_candidate", "facade", "MEDIUM", 1, "", "", "")
    ranked = A.rank([low_pile, med])
    assert ranked[0] is med and ranked[1] is low_pile


def test_count_scales_score_within_band():
    one = A._rec("placement_gate", "merged_blob", "room", "HIGH", 1, "", "", "")
    three = A._rec("placement_gate", "merged_blob", "room", "HIGH", 3, "", "", "")
    assert three["score"] > one["score"]
    # ...but a single CRITICAL still outranks many HIGHs (band dominates count)
    crit = A._rec("calibration", "calibration_fail", "project", "CRITICAL", 1, "", "", "")
    assert crit["score"] > A._rec("x", "y", "room", "HIGH", 9, "", "", "")["score"]


def test_resolved_records_leave_the_ranked_list_and_score():
    open_r = A._rec("facade", "facade_candidate", "facade", "MEDIUM", 1, "", "", "",
                    resolved=False)
    done_r = A._rec("facade", "facade_candidate", "facade", "MEDIUM", 1, "", "", "",
                    resolved=True)
    assert A.rank([open_r, done_r]) == [open_r]
    assert A.doubt_score([open_r, done_r]) == open_r["score"]


def test_doubt_score_sums_open_weights():
    recs = A.collect_gate(_gate([_room("bed", merged_regions=1, facing_flags=1)]))
    assert A.doubt_score(recs) == A.SEVERITY_WEIGHT["HIGH"] + A.SEVERITY_WEIGHT["MEDIUM"]


def test_summarise_counts_by_severity():
    recs = A.collect_gate(_gate([_room("bed", kind_flags=1, merged_regions=1,
                                       facing_flags=1, long_thin=1)]))
    s = A.summarise(recs)
    assert s["by_severity"] == {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 1, "LOW": 1}
    assert s["open"] == 4 and s["resolved"] == 0


# ---- coverage honesty (in-process gates) ----------------------------------------------
def test_persona_unwired_without_persona_file():
    # a demo spec carries no persona -> UNWIRED, never a silent pass, zero records
    recs, cov = A.collect_persona([("x.json", {"room": {"type": "bedroom"}})])
    assert recs == [] and cov["status"] in ("UNWIRED", "ABSENT", "ERROR")


def test_persona_absent_with_no_specs():
    recs, cov = A.collect_persona([])
    assert recs == [] and cov["status"] == "ABSENT"


def test_sourceability_errored_spec_is_not_silent_read():
    # a spec whose check() raises (here: a non-existent path) must surface as ERROR, never
    # a clean READ with fail=0/review=0 -- the module's honest-coverage law
    recs, cov = A.collect_sourceability([("/no/such/scene-graph.bedroom.json", {})])
    assert recs == [] and cov["status"] == "ERROR"
    assert cov["errored"] == 1 and cov["reviewed"] == 0


def test_resolve_out_dir_gateless_writes_into_project_not_parent():
    # gateless project: never os.path.dirname(project_dir) (the parent) -> the project itself
    assert A._resolve_out_dir(None, None, "/repo/projects/PRJ-X") == "/repo/projects/PRJ-X"
    # with a gate marker: the marker's layout dir
    assert A._resolve_out_dir(None, "/repo/projects/PRJ-X/03_layout/v4/placement-gate.json",
                              "/repo/projects/PRJ-X") == \
        "/repo/projects/PRJ-X/03_layout/v4"
    # explicit --out always wins
    assert A._resolve_out_dir("/tmp/out", None, "/repo/projects/PRJ-X") == "/tmp/out"


# ---- Tier-1 self-doubt suite bridge (cross_signal / anomaly / confidence / rebuild_diff) --
def _rspec(rtype, items=None, builtins=None, subrooms=None, outline=None):
    return {"schema": "interior-ai/room-spec@0.2",
            "room": {"type": rtype, "wall_thk_mm": 100,
                     "outline_mm": outline or [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "builtins": builtins or [], "items": items or [], "subrooms": subrooms or []}


def test_wrap_domain_maps_signal_to_source_kind_band_and_folds_confidence():
    rec = {"signal": "cross_signal:facing_vs_kind", "severity": "HIGH", "confidence": 0.8,
           "room": "living_room", "subjects": ["reading chair"], "detail": "faces wall",
           "why": "w", "resolve_by": "r"}
    w = A._wrap_domain(rec)
    assert w["source"] == "cross_signal" and w["kind"] == "facing_vs_kind"
    assert w["severity"] == "HIGH" and w["room"] == "living_room" and w["count"] == 1
    assert "reading chair" in w["detail"] and "0.8" in w["detail"]   # subjects + flag-confidence folded in


def test_collect_cross_signal_flags_toilet_in_living_room_and_reports_read():
    spec = _rspec("living_room", items=[{"name": "WC", "kind": "toilet", "x": 200, "y": 200,
                                         "w": 400, "d": 700}])
    recs, cov = A.collect_cross_signal([("s.json", spec)], None, None, [])
    assert any(r["kind"] == "ffe_vs_room" and r["severity"] == "HIGH" for r in recs)
    assert cov["status"] == "READ"


def test_collect_rebuild_diff_unsigned_reversal_critical_signed_quiet():
    # a DIRECTIONAL kind (sofa: asymmetric render, a real front) is required for a 180 flip to be an
    # OBSERVABLE reversal -- a plain box (bench) folds away under 180 render symmetry (see the
    # companion test below and test_rebuild_diff). This pins the CRITICAL-vs-signed asymmetry.
    prior = _rspec("bed", items=[{"name": "b", "kind": "sofa", "x": 100, "y": 100,
                                  "w": 1200, "d": 400, "rot": 180}])
    curr = _rspec("bed", items=[{"name": "b", "kind": "sofa", "x": 100, "y": 100,
                                 "w": 1200, "d": 400, "rot": 0}])          # a 180 facing flip
    recs, cov = A.collect_rebuild_diff([prior], [curr], confirmed=[])
    assert any(r["kind"] == "semantic_change_unexplained" and r["severity"] == "CRITICAL"
               for r in recs)
    assert cov["status"] == "READ"
    # the SAME change, owner-signed -> quiet (no CRITICAL) -- the whole asymmetry
    signed = [{"name": "b", "rot": 0, "w": 1200, "d": 400}]
    recs2, _ = A.collect_rebuild_diff([prior], [curr], confirmed=signed)
    assert not any(r["severity"] == "CRITICAL" for r in recs2)


def test_collect_rebuild_diff_box_reversal_is_not_critical():
    # the bench-180 first-live-run false CRITICAL, through the aggregator: a plain box flipping 180
    # is render-inert, so collect_rebuild_diff must emit NO CRITICAL for it (only the module-level
    # facing lane is exercised here -- the box's identity doubts live in a separate collector).
    prior = _rspec("bed", items=[{"name": "b", "kind": "bench", "x": 100, "y": 100,
                                  "w": 1200, "d": 400, "rot": 180}])
    curr = _rspec("bed", items=[{"name": "b", "kind": "bench", "x": 100, "y": 100,
                                 "w": 1200, "d": 400, "rot": 0}])
    recs, _ = A.collect_rebuild_diff([prior], [curr], confirmed=[])
    assert not any(r["severity"] == "CRITICAL" for r in recs)


def test_collect_rebuild_diff_no_prior_round_is_unwired_not_clean():
    curr = _rspec("bed", items=[{"name": "b", "kind": "bench", "x": 100, "y": 100,
                                 "w": 1200, "d": 400, "rot": 0}])
    _recs, cov = A.collect_rebuild_diff([], [curr], confirmed=[])
    assert cov["status"] == "UNWIRED"          # a first build has nothing to diff (never a pass)


def test_collect_anomaly_prior_band_unwired_without_corpus():
    spec = _rspec("bedroom", items=[{"name": "b", "kind": "bed", "x": 0, "y": 0,
                                     "w": 1800, "d": 2000}])
    _recs, cov = A.collect_anomaly([("s.json", spec)], None, [])
    assert "UNWIRED" in cov["prior_band"] and cov["status"] == "READ"


def test_collect_confidence_flags_assumed_facing_and_signature_suppresses():
    spec = _rspec("r", items=[{"name": "ch", "kind": "chair", "x": 1800, "y": 1800,
                               "w": 500, "d": 500}])          # rotless -> facing assumed
    recs, cov = A.collect_confidence([("s.json", spec)], [])
    assert any(r["kind"] == "facing" for r in recs) and cov["flagged_unsure"] >= 1
    signed = [{"name": "ch", "rot": 180, "w": 500, "d": 500}]
    recs2, _ = A.collect_confidence([("s.json", spec)], signed)
    assert not any(r["kind"] == "facing" for r in recs2)      # owner sign -> 1.0 -> suppressed


def test_collect_confidence_prior_corroboration_drops_the_kind_doubt():
    # a hand-typed 'sofa' with nothing corroborating is ASSUMED (0.30 -> say-unsure record);
    # a priors artifact whose sofa band the footprint UNIQUELY hits corroborates it (0.70) and
    # the record disappears -- the exact v4 delta (doubt-score 291 -> 281, sofa item dropped).
    spec = _rspec("living", items=[{"name": "โซฟา", "kind": "sofa", "x": 1500, "y": 1500,
                                    "w": 2202, "d": 1008, "rot": 90,
                                    "facing_source": "sheet note"}])
    priors = {"schema": "interior-ai/kind-priors@0.1",
              "kinds": {"sofa": {"lo_mm": [514.1, 1121.9], "hi_mm": [699.7, 2545.3],
                                 "aspect": [1.0, 3.5612903225806454], "n": 310}}}
    recs, cov = A.collect_confidence([("s.json", spec)], [])
    assert any(r["kind"] == "kind" for r in recs)             # uncorroborated -> say-unsure
    assert cov["prior_corroboration"].startswith("UNWIRED")
    recs2, cov2 = A.collect_confidence([("s.json", spec)], [], priors)
    assert not any(r["kind"] == "kind" for r in recs2)        # band-corroborated -> silent-OK
    assert cov2["prior_corroboration"] == "WIRED"


def test_collect_confidence_dead_context_lane_reports_error_not_wired():
    # review finding 2026-07-13: an artifact whose context build raises on EVERY spec must not
    # be reported WIRED -- that would be a silent pass over a dead corroboration lane.
    spec = _rspec("living", items=[{"name": "x", "kind": "sofa", "x": 1500, "y": 1500,
                                    "w": 2202, "d": 1008}])
    broken = {"schema": "interior-ai/kind-priors@0.1"}         # no 'kinds' -> suggest_kind raises
    recs, cov = A.collect_confidence([("s.json", spec)], [], broken)
    assert cov["prior_corroboration"].startswith("ERROR")
    assert "degraded" in cov.get("note", "")
    assert any(r["kind"] == "kind" for r in recs)              # doubt STAYS open (no corroboration)


def test_load_priors_discovers_an_artifact_under_qa(tmp_path):
    import json
    qa = tmp_path / "qa" / "priors"
    qa.mkdir(parents=True)
    (qa / "my-kind-priors.json").write_text(json.dumps(
        {"schema": "interior-ai/kind-priors@0.2", "kinds": {}}), encoding="utf-8")
    proj = tmp_path / "projects" / "PRJ-X"
    proj.mkdir(parents=True)
    doc = A._load_priors(str(proj))
    assert doc is not None and doc["schema"].startswith("interior-ai/kind-priors")
    # a non-priors json with a matching filename must NOT load
    (qa / "my-kind-priors.json").write_text(json.dumps({"schema": "other/thing"}),
                                            encoding="utf-8")
    assert A._load_priors(str(proj)) is None


def test_round_version_parse():
    assert A._round_version("/x/03_layout/v4") == 4
    assert A._round_version("/x/03_layout") == 0
    assert A._round_version("/x/03_layout/v12/") == 12


def test_wrap_domain_is_non_raising_on_malformed_records():
    # a BUGGY module returning a non-dict, a non-string signal, or an out-of-taxonomy severity must
    # NOT crash the audit -- _wrap_domain drops/clamps instead of KeyError-ing self_audit to death.
    assert A._wrap_domain("not a dict") is None
    assert A._wrap_domain(42) is None
    clamped = A._wrap_domain({"signal": 123, "severity": "WARN", "detail": "d"})
    assert clamped is not None and clamped["severity"] == "LOW"       # bad band -> safe advisory
    kept = A._wrap_all(["junk", {"signal": "cross_signal:x", "severity": "HIGH", "detail": "d"}])
    assert len(kept) == 1 and kept[0]["severity"] == "HIGH"           # drops the junk, keeps the valid


def test_find_prior_specs_ignores_foreign_stage_scene_graphs():
    # rebuild_diff's prior round must be a LAYOUT reading round -- never a scene-graph copied into
    # another stage (a 04_visualization render ghost at an in-between version) picked purely by number.
    import os as _os
    import json as _json
    import tempfile
    import shutil
    root = tempfile.mkdtemp()
    try:
        proj = _os.path.join(root, "PRJ")
        lay = _os.path.join(proj, "03_layout")
        v4 = _os.path.join(lay, "v4")
        viz = _os.path.join(proj, "04_visualization", "v2")
        for d in (lay, v4, viz):
            _os.makedirs(d)

        def _sg(dirp, room, rot):
            with open(_os.path.join(dirp, f"scene-graph.{room}.json"), "w", encoding="utf-8") as fh:
                _json.dump({"room": {"type": room,
                                     "outline_mm": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]},
                            "items": [{"name": "p", "kind": "bench", "x": 0, "y": 0,
                                       "w": 800, "d": 400, "rot": rot}]}, fh)
        _sg(lay, "bed", 180)         # the TRUE prior: the layout root (v0)
        _sg(v4, "bed", 0)            # the current round (v4)
        _sg(viz, "ghostroom", 999)   # a foreign render-stage scene-graph at an in-between version
        prior = A._find_prior_specs(proj, v4)
        assert {s["room"]["type"] for s in prior} == {"bed"}   # layout root only, never the ghost
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_suite_collectors_absent_on_empty_specs():
    cs_r, cs_c = A.collect_cross_signal([], None, None, [])
    an_r, an_c = A.collect_anomaly([], None, [])
    cf_r, cf_c = A.collect_confidence([], [])
    for recs, cov in ((cs_r, cs_c), (an_r, an_c), (cf_r, cf_c)):
        assert recs == [] and cov["status"] == "ABSENT"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} self_audit tests passed")
