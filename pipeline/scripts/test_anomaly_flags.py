"""test_anomaly_flags.py -- unit tests for the prior-violation doubt module.

Pins each check (size / aspect / count), each ABSTAIN + owner-sign SUPPRESS path, a REAL-data
case (the PRJ-2026-002 v4 sitting_room + master_bedroom, both CORRECT reads, must emit NOTHING --
the flagship no-false-positive guarantee), the two-layer suppression case, and coverage honesty
(no priors -> prior-band UNWIRED, never a silent clean pass; no pieces -> ABSENT).
"""
import json
import os

import anomaly_flags as AF

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(HERE, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout", "v4")


def _load(name):
    with open(os.path.join(V4, name), encoding="utf-8") as fh:
        return json.load(fh)


def _piece(name, kind, w, d, **extra):
    p = {"name": name, "kind": kind, "x": 0, "y": 0, "w": w, "d": d}
    p.update(extra)
    return p


def _room_spec(kind_type, items, builtins=None, subrooms=None):
    return {"schema": "interior-ai/room-spec@0.2",
            "room": {"type": kind_type, "outline_mm": [[0, 0], [5000, 0], [5000, 5000], [0, 5000]],
                     "wall_thk_mm": 100},
            "builtins": builtins or [], "items": items, "subrooms": subrooms or []}


# ---- record schema -----------------------------------------------------------------------------
def _assert_schema(r):
    for key in ("signal", "severity", "confidence", "room", "subjects", "detail", "why",
                "resolve_by"):
        assert key in r, f"missing {key}"
    assert r["signal"].startswith("anomaly_flags:")
    assert r["severity"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    assert 0.0 <= r["confidence"] <= 1.0
    assert isinstance(r["subjects"], list)


# ---- (1) size_implausible ----------------------------------------------------------------------
def test_bed_400x400_is_size_high():
    spec = _room_spec("bedroom", [_piece("เตียง", "bed", 400, 400)])
    recs = AF.check_room(spec)
    sizes = [r for r in recs if r["signal"] == "anomaly_flags:size_implausible"]
    assert len(sizes) == 1
    assert sizes[0]["severity"] == "HIGH"
    assert "bed" in sizes[0]["detail"] and "400" in sizes[0]["detail"]
    _assert_schema(sizes[0])


def test_size_never_relabels_only_doubts():
    # the record must POINT at a contradiction, never carry a corrected kind
    spec = _room_spec("bedroom", [_piece("x", "bed", 300, 300)])
    r = AF.check_room(spec)[0]
    assert "check" in r["resolve_by"].lower() or "owner-sign" in r["resolve_by"].lower()
    # module returns plain records, it does not mutate the spec piece
    assert spec["items"][0]["kind"] == "bed"


def test_l_sectional_sofa_single_aabb_not_size_flagged():
    # an L-/U-sectional entered as one bounding box has a large SHORT side; the widened sofa band
    # must NOT false-fire size_implausible on it (a common Thai living-room config).
    spec = _room_spec("living", [_piece("sectional", "sofa", 2800, 2800)])
    recs = [r for r in AF.check_room(spec) if r["signal"] == "anomaly_flags:size_implausible"]
    assert recs == []


def test_tiny_sofa_still_size_flagged():
    # widening max_short must NOT blind the gross case: a 400x400 "sofa" still trips min_short -> HIGH
    recs = [r for r in AF.check_room(_room_spec("living", [_piece("blob", "sofa", 400, 400)]))
            if r["signal"] == "anomaly_flags:size_implausible"]
    assert recs and recs[0]["severity"] == "HIGH"


def test_prior_band_medium_when_inside_builtin_but_far_outside_corpus():
    # a side_table well inside the generous built-in bounds but FAR below a tight corpus band
    priors = {"schema": "interior-ai/kind-priors@0.1",
              "kinds": {"side_table": {"lo_mm": [500, 700], "hi_mm": [500, 700],
                                       "aspect": [1.0, 1.3]}}}
    st = _piece("st", "side_table", 250, 250)          # inside built-in (>=150), far below band 500
    recs = AF.check_room(_room_spec("living", [st]), priors=priors)
    sizes = [r for r in recs if r["signal"] == "anomaly_flags:size_implausible"]
    assert len(sizes) == 1 and sizes[0]["severity"] == "MEDIUM"


def test_gross_builtin_supersedes_prior_band():
    # a bed at 400x400 is gross (HIGH), never demoted to a MEDIUM prior record
    priors = {"schema": "interior-ai/kind-priors@0.1",
              "kinds": {"bed": {"lo_mm": [1600, 1900], "hi_mm": [1900, 2200], "aspect": [1.0, 1.3]}}}
    recs = AF.check_room(_room_spec("bedroom", [_piece("b", "bed", 400, 400)]), priors=priors)
    sizes = [r for r in recs if r["signal"] == "anomaly_flags:size_implausible"]
    assert len(sizes) == 1 and sizes[0]["severity"] == "HIGH"


# ---- (2) aspect_implausible --------------------------------------------------------------------
def test_wardrobe_1to8_is_aspect_medium():
    # 400 x 3200 = 8:1 : within size bounds, but far too slim for a wardrobe (max ~7.5:1)
    spec = _room_spec("bedroom", [_piece("ตู้", "wardrobe", 400, 3200)])
    recs = AF.check_room(spec)
    asp = [r for r in recs if r["signal"] == "anomaly_flags:aspect_implausible"]
    assert len(asp) == 1 and asp[0]["severity"] == "MEDIUM"
    # size must NOT fire (both extents are within the generous wardrobe size band)
    assert not [r for r in recs if r["signal"] == "anomaly_flags:size_implausible"]


def test_nightstand_1to6_is_aspect_medium():
    spec = _room_spec("bedroom", [_piece("ns", "nightstand", 140, 840)])
    # 140 short trips size (min 150) too, but aspect 6:1 must also flag
    asp = [r for r in AF.check_room(spec) if r["signal"] == "anomaly_flags:aspect_implausible"]
    assert asp and asp[0]["severity"] == "MEDIUM"


# ---- (3) count_anomaly -------------------------------------------------------------------------
def test_three_nightstands_is_count_medium():
    ns = [_piece(f"ns{i}", "nightstand", 450, 400) for i in range(3)]
    recs = AF.check_room(_room_spec("bedroom", ns))
    cnt = [r for r in recs if r["signal"] == "anomaly_flags:count_anomaly"]
    assert len(cnt) == 1 and cnt[0]["severity"] == "MEDIUM"
    assert len(cnt[0]["subjects"]) == 3 and "3 'nightstand'" in cnt[0]["detail"]
    # three valid-sized nightstands must NOT also raise size/aspect
    assert not [r for r in recs if r["signal"] != "anomaly_flags:count_anomaly"]


def test_two_toilets_in_subroom_is_count_high():
    bath = {"name": "ห้องน้ำ", "type": "bathroom",
            "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]],
            "fixtures": [_piece("WC1", "toilet", 400, 700), _piece("WC2", "toilet", 400, 700)]}
    spec = _room_spec("bedroom", [], subrooms=[bath])
    cnt = [r for r in AF.check_room(spec) if r["signal"] == "anomaly_flags:count_anomaly"]
    assert len(cnt) == 1 and cnt[0]["severity"] == "HIGH"
    assert cnt[0]["room"] == "ห้องน้ำ"          # counted per-subroom, not whole-spec


def test_two_beds_is_count_medium():
    beds = [_piece("bed1", "bed", 1800, 2000), _piece("bed2", "bed", 1800, 2000)]
    cnt = [r for r in AF.check_room(_room_spec("bedroom", beds))
           if r["signal"] == "anomaly_flags:count_anomaly"]
    assert len(cnt) == 1 and cnt[0]["severity"] == "MEDIUM"


def test_two_bathrooms_one_toilet_each_is_not_flagged():
    # per-container counting: two separate bathrooms each with one toilet is NORMAL
    def bath(n):
        return {"name": n, "type": "bathroom",
                "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]],
                "fixtures": [_piece("WC", "toilet", 400, 700)]}
    spec = _room_spec("bedroom", [], subrooms=[bath("bath_a"), bath("bath_b")])
    assert [r for r in AF.check_room(spec) if r["signal"] == "anomaly_flags:count_anomaly"] == []


# ---- ABSTAIN / conservatism --------------------------------------------------------------------
def test_unknown_kind_is_abstained_and_reported_no_bound():
    # cabinet has NO built-in bound -> no flag (even a 300x4100 wall run), reported honestly
    spec = _room_spec("living", [_piece("BF13", "cabinet", 300, 4100)])
    assert AF.check_room(spec) == []
    cov = AF.check_coverage(spec)
    assert "cabinet" in cov["no_bound_kinds"]


def test_missing_or_zero_dims_abstains():
    # distinct kinds so no count fires -- isolates the dimension ABSTAIN path
    spec = _room_spec("bedroom", [_piece("b", "bed", 0, 400),          # zero extent
                                  {"name": "n", "kind": "wardrobe"}])  # no w/d at all
    assert AF.check_room(spec) == []                                   # never crashes, never flags


def test_unlabelled_piece_abstains():
    spec = _room_spec("bedroom", [{"name": "blob", "w": 400, "d": 400}])   # no kind
    assert AF.check_room(spec) == []


# ---- (c) TWO-LAYER SUPPRESSION -----------------------------------------------------------------
def test_owner_signed_kind_suppresses_size_flag():
    # an impossible 400x400 bed that the OWNER has SIGNED as 'bed' -> adjudicated, NO flag
    bed = _piece("เตียงเล็ก", "bed", 400, 400)
    unsigned = AF.check_room(_room_spec("bedroom", [bed]))
    assert any(r["signal"] == "anomaly_flags:size_implausible" for r in unsigned)
    confirmed = [{"name": "เตียงเล็ก", "kind": "bed", "w": 400, "d": 400,
                  "by": "owner (2026-07-08)"}]
    signed = AF.check_room(_room_spec("bedroom", [bed]), params={"confirmed": confirmed})
    assert signed == []                                               # owner signature wins


def test_owner_signed_count_is_suppressed():
    ns = [_piece(f"ns{i}", "nightstand", 450, 400) for i in range(3)]
    confirmed = [{"name": f"ns{i}", "kind": "nightstand", "w": 450, "d": 400} for i in range(3)]
    signed = AF.check_room(_room_spec("bedroom", ns), params={"confirmed": confirmed})
    assert [r for r in signed if r["signal"] == "anomaly_flags:count_anomaly"] == []
    # an UNSIGNED surplus still flags: sign only two, leave a third unsigned
    two = confirmed[:2]
    still = AF.check_room(_room_spec("bedroom", ns), params={"confirmed": two})
    assert not [r for r in still if r["signal"] == "anomaly_flags:count_anomaly"]  # 1 unsigned <= max


# ---- (b) REAL DATA: correct reads must emit NOTHING --------------------------------------------
def test_real_v4_sitting_room_emits_nothing():
    spec = _load("scene-graph.sitting_room.json")
    recs = AF.check_room(spec)
    assert recs == [], f"false-flagged a normal room: {[r['detail'] for r in recs]}"


def test_real_v4_master_bedroom_emits_nothing():
    spec = _load("scene-graph.master_bedroom.json")
    recs = AF.check_room(spec)
    assert recs == [], f"false-flagged a normal room: {[r['detail'] for r in recs]}"


def test_real_room_coverage_is_read_not_silent():
    spec = _load("scene-graph.sitting_room.json")
    cov = AF.check_coverage(spec)
    assert cov["size_implausible"]["status"] == "READ"
    assert cov["prior_band"]["status"] == "UNWIRED"          # no local corpus priors
    assert "unwired" in cov["prior_band"]["note"].lower()
    assert "cabinet" in cov["no_bound_kinds"]                # honest: cabinets were not bounded


# ---- (d) HONEST COVERAGE -----------------------------------------------------------------------
def test_coverage_prior_unwired_without_priors_and_read_with():
    spec = _room_spec("bedroom", [_piece("b", "bed", 1800, 2000)])
    assert AF.check_coverage(spec)["prior_band"]["status"] == "UNWIRED"
    priors = {"schema": "interior-ai/kind-priors@0.1",
              "kinds": {"bed": {"lo_mm": [1600, 1900], "hi_mm": [1900, 2200], "aspect": [1.0, 1.3]}}}
    assert AF.check_coverage(spec, priors=priors)["prior_band"]["status"] == "READ"


def test_coverage_absent_when_no_measurable_pieces():
    # empty room: distinguishable from a clean READ that found nothing
    empty = _room_spec("bedroom", [])
    cov = AF.check_coverage(empty)
    assert cov["size_implausible"]["status"] == "ABSENT"
    assert cov["size_implausible"]["measured_pieces"] == 0


def test_coverage_distinguishes_looked_from_did_not_look():
    # a room full of unbounded kinds: count container READ, but zero measured-with-bound is honest
    spec = _room_spec("living", [_piece("c", "cabinet", 300, 4100)])
    cov = AF.check_coverage(spec)
    assert cov["size_implausible"]["status"] == "READ"      # a measurable piece WAS looked at
    assert cov["no_bound_kinds"] == ["cabinet"]             # ...but this kind had no bound


# ---- determinism -------------------------------------------------------------------------------
def test_output_is_sorted_and_deterministic():
    pieces = [_piece("bed", "bed", 400, 400), _piece("ns", "nightstand", 140, 840)]
    pieces += [_piece(f"ns{i}", "nightstand", 450, 400) for i in range(3)]
    a = AF.check_room(_room_spec("bedroom", pieces))
    b = AF.check_room(_room_spec("bedroom", list(reversed(pieces))))
    assert [r["signal"] for r in a] == [r["signal"] for r in b]
    order = [AF.SEVERITY_ORDER[r["severity"]] for r in a]
    assert order == sorted(order)
    for r in a:
        _assert_schema(r)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} anomaly_flags tests passed")
