"""
test_confidence.py -- unit tests for the base-read confidence calibrator.

Pins: the shared scale (owner-signed 1.0 > corroborated 0.70 > provenance 0.55 > assumed 0.30);
every abstain/suppress path (facing only for directional kinds; an owner signature suppresses;
a contained piece reads indoor); the say-unsure boundary the sofa sits on (0.55 vs 0.50); honest
coverage (a room with pieces = READ, none = ABSENT); and the REAL v4 sitting-room flagship (tub
chairs owner-signed facing -> no record; sofa provenance -> silent-OK; a rot-less chair -> fires).
"""
import json
import os

import placement_gate as PG
import confidence as C

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.normpath(os.path.join(
    HERE, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout", "v4"))


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _sig(records, field):
    return [r for r in records if r["signal"] == f"confidence:{field}"]


def _subjects(records):
    return {r["subjects"][0] for r in records}


# ---- the shared scale ----------------------------------------------------------------
def test_owner_signed_kind_is_one():
    piece = {"name": "x", "kind": "sofa", "w": 2000, "d": 900}
    confirmed = [{"name": "x", "kind": "sofa", "w": 2000, "d": 900}]
    score, basis = C.field_confidence(piece, "kind", confirmed)
    assert score == C.CONF_OWNER == 1.0 and basis == "owner-signed"


def test_owner_signed_facing_is_one_via_rot():
    piece = {"name": "c", "kind": "armchair", "w": 680, "d": 640, "rot": 8}
    confirmed = [{"name": "c", "rot": 8, "w": 680, "d": 640}]
    score, basis = C.field_confidence(piece, "facing", confirmed)
    assert score == 1.0 and basis == "owner-signed"


def test_owner_signed_zone_is_one():
    piece = {"name": "z", "kind": "chair", "w": 500, "d": 500}
    confirmed = [{"name": "z", "zone": "below_grade", "w": 500, "d": 500}]
    assert C.field_confidence(piece, "zone", confirmed)[0] == 1.0


def test_kind_prior_band_corroborates():
    piece = {"name": "x", "kind": "sofa", "w": 2000, "d": 900}
    score, basis = C.field_confidence(piece, "kind", None, {"prior_kind": "sofa"})
    assert score == C.CONF_CORROBORATED == 0.70
    # a DISAGREEING prior does not corroborate -> falls through to assumed
    assert C.field_confidence(piece, "kind", None, {"prior_kind": "bed"})[0] == C.CONF_ASSUMED


def test_kind_bf_code_is_provenance():
    piece = {"name": "cab", "kind": "cabinet", "w": 400, "d": 1575, "bf": "BF12-1"}
    score, basis = C.field_confidence(piece, "kind", None)
    assert score == C.CONF_PROVENANCE and "BF12-1" in basis


def test_kind_bare_handtype_is_assumed():
    piece = {"name": "t", "kind": "side_table", "w": 600, "d": 600}
    score, basis = C.field_confidence(piece, "kind", None)
    assert score == C.CONF_ASSUMED == 0.30


def test_facing_corroborated_by_strip_read():
    piece = {"name": "b", "kind": "bed", "w": 2000, "d": 1900, "rot": 90}
    assert C.field_confidence(piece, "facing", None, {"facing_agrees": True})[0] == 0.70


def test_facing_explicit_rot_is_provenance():
    piece = {"name": "s", "kind": "sofa", "w": 2200, "d": 1000, "rot": 90}
    score, basis = C.field_confidence(piece, "facing", None)
    assert score == C.CONF_PROVENANCE and "rot" in basis


def test_facing_source_is_provenance():
    piece = {"name": "s", "kind": "armchair", "w": 680, "d": 640, "facing_source": "owner-signed"}
    # no rot key, but facing_source present -> provenance (not assumed)
    assert C.field_confidence(piece, "facing", None)[0] == C.CONF_PROVENANCE


def test_facing_rotless_unsigned_is_assumed():
    piece = {"name": "chair", "kind": "chair", "w": 500, "d": 500}
    score, basis = C.field_confidence(piece, "facing", None)
    assert score == C.CONF_ASSUMED and "assumed south" in basis


def test_negated_note_does_not_credit_facing_provenance():
    # a note that says what the piece does NOT do is not provenance for which way it DOES face ->
    # the read falls through to ASSUMED so the say-unsure doubt fires (the safe more-doubt direction).
    piece = {"name": "ch", "kind": "chair", "w": 500, "d": 500, "note": "does NOT face the terrace"}
    assert C.field_confidence(piece, "facing", None)[0] == C.CONF_ASSUMED
    # sanity: a POSITIVE assertion still credits provenance (the guard is negation-only)
    piece2 = {"name": "c2", "kind": "chair", "w": 500, "d": 500, "note": "faces the window"}
    assert C.field_confidence(piece2, "facing", None)[0] == C.CONF_PROVENANCE


def test_negated_zone_note_does_not_credit_provenance():
    piece = {"name": "p", "kind": "chair", "w": 500, "d": 500, "note": "ไม่ใช่ระเบียง (ในห้อง)"}
    assert C.field_confidence(piece, "zone", None)[0] == C.CONF_ASSUMED


def test_zone_containment_corroborates_indoor():
    piece = {"name": "p", "kind": "chair", "w": 500, "d": 500}
    assert C.field_confidence(piece, "zone", None, {"zone_corroborated": True})[0] == 0.70


def test_zone_handset_is_provenance():
    piece = {"name": "p", "kind": "chair", "w": 500, "d": 500, "zone": "below_grade"}
    score, basis = C.field_confidence(piece, "zone", None)
    assert score == C.CONF_PROVENANCE and "below_grade" in basis


def test_zone_bare_is_assumed_indoor():
    piece = {"name": "p", "kind": "chair", "w": 500, "d": 500}
    assert C.field_confidence(piece, "zone", None)[0] == C.CONF_ASSUMED


# ---- the say-unsure boundary (the sofa case) -----------------------------------------
def test_boundary_provenance_is_above_threshold():
    # THE documented boundary: a provenance read (0.55) must sit ABOVE the say-unsure line (0.50)
    # so the sofa's explicit rot + note does NOT fire a record, while a bare assumption (0.30) does.
    assert C.CONF_PROVENANCE >= C.SAY_UNSURE_THRESHOLD > C.CONF_ASSUMED
    assert C.SAY_UNSURE_THRESHOLD == 0.50 and C.CONF_PROVENANCE == 0.55


# ---- abstain / suppress paths --------------------------------------------------------
def test_facing_not_eligible_for_nondirectional_kind():
    # a round side table has no facing -> no facing record even with no rot (abstain, not a false flag)
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "items": [{"name": "tbl", "kind": "side_table", "x": 1000, "y": 1000, "w": 600, "d": 600}]}
    recs = C.assess_room(spec)
    assert _sig(recs, "facing") == []


def test_owner_sign_suppresses_the_record():
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "items": [{"name": "ch", "kind": "chair", "x": 1000, "y": 1000, "w": 500, "d": 500}]}
    # unsigned: facing assumed -> a record fires
    assert _sig(C.assess_room(spec), "facing")
    # owner signs the rot -> facing 1.0 -> SUPPRESSED
    confirmed = [{"name": "ch", "rot": 180, "w": 500, "d": 500}]
    assert _sig(C.assess_room(spec, confirmed), "facing") == []


def test_contained_piece_not_flagged_for_zone():
    # a piece deep inside the outline reads indoor (0.70) -> no zone record (no crying wolf on an edge)
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": [{"name": "mid", "kind": "chair", "x": 1800, "y": 1800, "w": 500, "d": 500,
                       "rot": 0}]}
    assert _sig(C.assess_room(spec), "zone") == []


def test_uncontained_piece_fires_zone():
    # centroid well OUTSIDE the outline, unsigned -> assumed indoor is genuinely unverified -> fires
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "items": [{"name": "out", "kind": "chair", "x": 5000, "y": 5000, "w": 500, "d": 500,
                       "rot": 0}]}
    z = _sig(C.assess_room(spec), "zone")
    assert len(z) == 1 and z[0]["subjects"] == ["out"]


def test_record_confidence_is_one_minus_field_confidence():
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "items": [{"name": "k", "kind": "sofa", "x": 800, "y": 800, "w": 300, "d": 300}]}
    rec = _sig(C.assess_room(spec), "kind")[0]
    assert rec["confidence"] == round(1.0 - C.CONF_ASSUMED, 2) == 0.7
    assert rec["severity"] == "MEDIUM"          # fully-unsupported kind = MEDIUM


# ---- honest coverage -----------------------------------------------------------------
def test_coverage_read_vs_absent_are_distinguishable():
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "items": [{"name": "k", "kind": "sofa", "x": 800, "y": 800, "w": 300, "d": 300}]}
    cov = C.assess_coverage(spec)
    assert cov["status"] == "READ" and cov["pieces"] == 1 and cov["assessed_fields"] >= 1
    # a room with NO pieces is ABSENT -> distinct from a clean READ (never a silent pass)
    empty = C.assess_coverage({"room": {"type": "r", "outline_mm": [[0, 0], [1, 0], [1, 1]]}})
    assert empty["status"] == "ABSENT" and empty["pieces"] == 0


def test_coverage_tally_matches_emitted_records():
    spec = {"room": {"type": "r", "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "builtins": [{"name": "cab", "kind": "cabinet", "x": 100, "y": 100, "w": 400, "d": 700,
                          "bf": "BF1"}],
            "items": [{"name": "so", "kind": "sofa", "x": 1000, "y": 1000, "w": 300, "d": 300}]}
    cov = C.assess_coverage(spec)
    # the cabinet's kind is provenance (bf) -> not flagged; the sofa's kind is assumed -> flagged
    assert cov["by_field"]["kind"]["provenance"] == 1
    assert cov["by_field"]["kind"]["assumed"] == 1
    flagged_kind = len(_sig(C.assess_room(spec), "kind"))
    assert flagged_kind == cov["by_field"]["kind"]["assumed"] == 1


# ---- REAL DATA: the v4 sitting-room flagship -----------------------------------------
def test_real_v4_sitting_room_flagship():
    spec = _load(os.path.join(V4, "scene-graph.sitting_room.json"))
    review = _load(os.path.join(V4, "placement-review.json"))
    confirmed = PG.load_confirmed(review)
    recs = C.assess_room(spec, confirmed)
    facing = _sig(recs, "facing")
    flagged = _subjects(facing)

    tub_left = "เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)"
    tub_right = "เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)"
    sofa = "โซฟา 3 ที่นั่ง"

    # (a) FLAGSHIP: the tub chairs' facing is owner-signed -> 1.0 -> NO say-unsure record.
    assert tub_left not in flagged and tub_right not in flagged
    tub_piece = next(p for p in spec["items"] if p["name"] == tub_left)
    assert C.field_confidence(tub_piece, "facing", confirmed)[0] == 1.0

    # (b) the sofa: explicit rot 90 + "faces EAST" note, NO owner sign -> provenance 0.55 -> silent-OK.
    sofa_piece = next(p for p in spec["items"] if p["name"] == sofa)
    assert C.field_confidence(sofa_piece, "facing", confirmed)[0] == C.CONF_PROVENANCE
    assert sofa not in flagged

    # (c) all pieces are geometrically contained -> zero zone false-positives on the real read.
    assert _sig(recs, "zone") == []

    # (d) honest coverage: READ, and the tub chairs show up as owner_signed for facing.
    cov = C.assess_coverage(spec, confirmed)
    assert cov["status"] == "READ"
    assert cov["by_field"]["facing"]["owner_signed"] == 2


def test_real_v4_synthetic_rotless_chair_fires():
    # the instrument earning its keep: drop a rot-less, unsigned chair by the glass into the real
    # room -> facing 0.30 -> a "assumed south-facing" record fires (near facade -> MEDIUM).
    spec = _load(os.path.join(V4, "scene-graph.sitting_room.json"))
    review = _load(os.path.join(V4, "placement-review.json"))
    confirmed = PG.load_confirmed(review)
    spec["items"].append({"name": "ghost chair", "kind": "chair", "x": 9000, "y": 200,
                          "w": 500, "d": 500})
    recs = C.assess_room(spec, confirmed)
    ghost = [r for r in _sig(recs, "facing") if r["subjects"] == ["ghost chair"]]
    assert len(ghost) == 1
    assert ghost[0]["severity"] == "MEDIUM"      # near the south facade -> the owner-arbitrated call
    assert "assumed south" in ghost[0]["detail"]


def test_real_v4_master_bedroom_no_facing_false_positive():
    # every facing-kind in the master bedroom carries an explicit rot (or a sign) -> provenance+ ->
    # NO facing say-unsure records (conservatism holds on the second real room).
    spec = _load(os.path.join(V4, "scene-graph.master_bedroom.json"))
    recs = C.assess_room(spec)
    assert _sig(recs, "facing") == []
    # ...yet coverage still proves it LOOKED (facing eligible for bed + work armchair), never silent.
    cov = C.assess_coverage(spec)
    assert cov["by_field"]["facing"]["eligible"] >= 2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} confidence tests passed")
