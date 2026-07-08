"""test_rebuild_diff.py -- unit tests for the between-rounds regression instrument.

Pins the whole-instrument invariant: a SIGNED semantic change is quiet (LOW provenance, never a
regression flag); the SAME change UNSIGNED is loud (CRITICAL for a facing reversal, HIGH for an
identity/zone change, MEDIUM for a smaller facing swing). Plus: renamed pieces re-pair by geometry;
sub-threshold nudges + round pieces abstain; honest coverage says UNWIRED when there is no prior
round; and the REAL v3->v4 sitting-room diff behaves correctly with and without the owner ledger.
"""
import copy
import json
import os

import placement_gate as PG
import rebuild_diff as RD

HERE = os.path.dirname(os.path.abspath(__file__))
LAYOUT = os.path.abspath(os.path.join(
    HERE, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout"))
V3_SITTING = os.path.join(LAYOUT, "scene-graph.sitting_room.json")
V4_SITTING = os.path.join(LAYOUT, "v4", "scene-graph.sitting_room.json")
V3_MASTER = os.path.join(LAYOUT, "scene-graph.master_bedroom.json")
V4_MASTER = os.path.join(LAYOUT, "v4", "scene-graph.master_bedroom.json")
V4_REVIEW = os.path.join(LAYOUT, "v4", "placement-review.json")

TUB_L = "เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)"      # v4 (renamed) left tub chair
TUB_R = "เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)"      # v4 (renamed) right tub chair
BENCH = "ม้านั่งปลายเตียง (bench)"                          # end-of-bed bench (a plain box)


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _room(rt, builtins=None, items=None, subrooms=None):
    return {"room": {"type": rt}, "builtins": builtins or [], "items": items or [],
            "subrooms": subrooms or []}


def _unexplained(recs):
    return [r for r in recs if r["signal"] == "rebuild_diff:semantic_change_unexplained"]


def _touching(recs, name):
    return [r for r in recs if name in r["subjects"]]


# ---- (a) synthetic unit cases: each check + each severity band -------------------------
def test_facing_reversal_unsigned_is_critical():
    prior = _room("den", items=[{"name": "sofa", "kind": "sofa", "x": 0, "y": 0,
                                 "w": 2000, "d": 900, "rot": 0}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 180                       # south -> north, a clean reversal
    recs = RD.diff_rounds([prior], [curr])
    u = _unexplained(recs)
    assert len(u) == 1 and u[0]["severity"] == "CRITICAL"
    assert "sofa" in u[0]["subjects"] and u[0]["confidence"] >= 0.85


def test_facing_medium_swing_unsigned():
    prior = _room("den", items=[{"name": "chair", "kind": "armchair", "x": 0, "y": 0,
                                 "w": 600, "d": 600, "rot": 0}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 60                         # 60deg: > abstain, < flip -> MEDIUM
    u = _unexplained(RD.diff_rounds([prior], [curr]))
    assert len(u) == 1 and u[0]["severity"] == "MEDIUM"


def test_small_nudge_and_round_piece_abstain():
    # a sub-threshold nudge (12deg) emits nothing...
    prior = _room("den", items=[{"name": "chair", "kind": "armchair", "x": 0, "y": 0,
                                 "w": 600, "d": 600, "rot": 0}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 12
    assert RD.diff_rounds([prior], [curr]) == []
    # ...and a radially-symmetric (round) table's rot change is never a facing flag
    pr = _room("den", items=[{"name": "t", "kind": "side_table", "shape": "round",
                              "x": 0, "y": 0, "w": 600, "d": 600, "rot": 0}])
    cu = copy.deepcopy(pr)
    cu["items"][0]["rot"] = 200
    assert RD.diff_rounds([pr], [cu]) == []


def test_box_kind_180_flip_is_render_inert_and_abstains():
    # a bench is a plain box (NOT in _DIRECTIONAL_KINDS): the renderer draws it as a single centered
    # box, so a 180 flip is a byte-identical mesh -> NO facing flag, exactly as a round piece has no
    # facing. This is the bench-180 first-live-run false CRITICAL the render-symmetry fold closes.
    prior = _room("den", items=[{"name": "bench", "kind": "bench", "x": 0, "y": 0,
                                 "w": 500, "d": 1000, "rot": 180}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 0                          # 180 -> 0, would be a naive CRITICAL reversal
    assert RD.diff_rounds([prior], [curr]) == []
    # a TABLE renders as a centered top on 4 symmetric legs -> also 180-symmetric -> abstains too,
    # even though side_table IS in build_floor._FURN_KINDS (detailed mesh != directional mesh).
    pr = _room("den", items=[{"name": "t", "kind": "side_table", "x": 0, "y": 0,
                              "w": 400, "d": 600, "rot": 0}])
    cu = copy.deepcopy(pr)
    cu["items"][0]["rot"] = 180
    assert RD.diff_rounds([pr], [cu]) == []


def test_box_kind_90_turn_still_flags_medium():
    # a 90 turn of a NON-square box reorients its footprint (visible) -> folded delta 90 -> MEDIUM;
    # a box can never reach the reversal band, so this is the ceiling severity for a box facing move.
    prior = _room("den", items=[{"name": "b", "kind": "bench", "x": 0, "y": 0,
                                 "w": 500, "d": 1000, "rot": 0}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 90
    u = _unexplained(RD.diff_rounds([prior], [curr]))
    assert len(u) == 1 and u[0]["severity"] == "MEDIUM"


def test_directional_kind_180_flip_stays_critical():
    # regression guard for the fold: an ASYMMETRIC render (sofa/armchair/bed carry a back/headboard)
    # flipping 180 is a REAL visible reversal and must stay CRITICAL -- the fold must skip these.
    for kind in ("armchair", "sofa", "bed"):
        prior = _room("den", items=[{"name": "p", "kind": kind, "x": 0, "y": 0,
                                     "w": 1000, "d": 600, "rot": 0}])
        curr = copy.deepcopy(prior)
        curr["items"][0]["rot"] = 180
        u = _unexplained(RD.diff_rounds([prior], [curr]))
        assert len(u) == 1 and u[0]["severity"] == "CRITICAL", kind


def test_directional_kinds_match_furniture_asymmetric_builders():
    # _DIRECTIONAL_KINDS drives the render-symmetry fold; pin it to furniture.py's actual
    # 180-ASYMMETRIC builders (_sofa/_chair/_bed add a back/headboard; _table + _block are symmetric)
    # so a newly-added furniture builder cannot silently drift the instrument's sensitivity.
    import furniture as F
    asym = {F._sofa, F._chair, F._bed}
    derived = {k for k, b in F._BUILDERS.items() if b in asym}
    assert set(RD._DIRECTIONAL_KINDS) == derived


def test_kind_change_unsigned_is_high():
    prior = _room("den", items=[{"name": "p", "kind": "cabinet", "x": 0, "y": 0,
                                 "w": 700, "d": 400}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["kind"] = "console"
    u = _unexplained(RD.diff_rounds([prior], [curr]))
    assert len(u) == 1 and u[0]["severity"] == "HIGH"
    assert "cabinet" in u[0]["detail"] and "console" in u[0]["detail"]


def test_zone_change_unsigned_is_high():
    prior = _room("den", items=[{"name": "p", "kind": "planter", "x": 0, "y": 0,
                                 "w": 700, "d": 700, "zone": "outdoor_same_floor"}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["zone"] = "below_grade"
    u = _unexplained(RD.diff_rounds([prior], [curr]))
    assert len(u) == 1 and u[0]["severity"] == "HIGH"


def test_piece_added_and_dropped_are_low():
    prior = _room("den", items=[{"name": "gone", "kind": "stool", "x": 0, "y": 0,
                                 "w": 400, "d": 400}])
    curr = _room("den", items=[{"name": "fresh", "kind": "stool", "x": 9000, "y": 9000,
                                "w": 400, "d": 400}])
    recs = RD.diff_rounds([prior], [curr])
    sigs = {r["signal"]: r for r in recs}
    assert sigs["rebuild_diff:piece_dropped"]["severity"] == "LOW"
    assert sigs["rebuild_diff:piece_added"]["severity"] == "LOW"


# ---- (c) two-layer SUPPRESSION: an owner signature silences the doubt ------------------
def test_signed_reversal_is_suppressed_to_low_provenance():
    piece = {"name": "sofa", "kind": "sofa", "x": 0, "y": 0, "w": 2000, "d": 900, "rot": 0}
    prior = _room("den", items=[piece])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 180
    confirmed = [{"name": "sofa", "rot": 180, "w": 2000, "d": 900, "by": "owner"}]
    recs = RD.diff_rounds([prior], [curr], confirmed=confirmed)
    assert _unexplained(recs) == []                     # signature wins -> no regression flag
    prov = [r for r in recs if r["signal"] == "rebuild_diff:semantic_change_signed"]
    assert len(prov) == 1 and prov[0]["severity"] == "LOW"


def test_signed_kind_change_is_suppressed():
    prior = _room("den", items=[{"name": "p", "kind": "cabinet", "x": 0, "y": 0,
                                 "w": 700, "d": 400}])
    curr = copy.deepcopy(prior)
    curr["items"][0]["kind"] = "console"
    confirmed = [{"name": "p", "kind": "console", "w": 700, "d": 400, "by": "owner"}]
    assert _unexplained(RD.diff_rounds([prior], [curr], confirmed=confirmed)) == []


def test_signature_for_wrong_value_does_not_suppress():
    # owner signed rot 90, but the build FLIPPED to 180 -> the sign does NOT cover it -> loud
    piece = {"name": "sofa", "kind": "sofa", "x": 0, "y": 0, "w": 2000, "d": 900, "rot": 0}
    prior = _room("den", items=[piece])
    curr = copy.deepcopy(prior)
    curr["items"][0]["rot"] = 180
    confirmed = [{"name": "sofa", "rot": 90, "w": 2000, "d": 900, "by": "owner"}]
    u = _unexplained(RD.diff_rounds([prior], [curr], confirmed=confirmed))
    assert len(u) == 1 and u[0]["severity"] == "CRITICAL"


# ---- geometry pairing across a rename --------------------------------------------------
def test_match_pieces_pairs_renamed_by_geometry():
    prior = [{"name": "old-name", "kind": "armchair", "x": 5948, "y": 562, "w": 768, "d": 780}]
    curr = [{"name": "new-name", "kind": "armchair", "x": 5991, "y": 629, "w": 680, "d": 640,
             "rot": 8}]
    pairs = RD.match_pieces(prior, curr)
    assert len(pairs) == 1
    p, c = pairs[0]
    assert p is not None and c is not None              # paired, not drop+add
    assert p["name"] == "old-name" and c["name"] == "new-name"


def test_match_pieces_below_threshold_is_drop_plus_add():
    # the moved+rotated BF12-2 cabinet: IoU 0.0 -> honestly a drop and an add, never a false pair
    prior = [{"name": "a", "kind": "cabinet", "x": 6090, "y": 2210, "w": 700, "d": 400}]
    curr = [{"name": "b", "kind": "cabinet", "x": 5750, "y": 2650, "w": 400, "d": 700}]
    pairs = RD.match_pieces(prior, curr)
    assert (prior[0], None) in pairs and (None, curr[0]) in pairs


# ---- (d) honest coverage ---------------------------------------------------------------
def test_coverage_unwired_without_prior_round():
    cov = RD.diff_coverage(None, [_room("den")])
    assert cov["status"] == "UNWIRED"                   # first build: nothing to diff, NOT clean
    assert RD.diff_rounds(None, [_room("den")]) == []


def test_coverage_unwired_when_no_shared_room():
    cov = RD.diff_coverage([_room("kitchen")], [_room("den")])
    assert cov["status"] == "UNWIRED" and cov["shared_rooms"] == []


def test_coverage_read_and_absent():
    assert RD.diff_coverage([_room("den")], [_room("den")])["status"] == "READ"
    assert RD.diff_coverage([_room("den")], None)["status"] == "ABSENT"


def test_accepts_dict_keyed_by_room_type():
    prior = {"den": _room("den", items=[{"name": "s", "kind": "sofa", "x": 0, "y": 0,
                                         "w": 2000, "d": 900, "rot": 0}])}
    curr = copy.deepcopy(prior)
    curr["den"]["items"][0]["rot"] = 180
    assert len(_unexplained(RD.diff_rounds(prior, curr))) == 1


# ---- (b) REAL DATA: the v3 -> v4 sitting-room diff (the flagship wound) -----------------
def test_real_v3_to_v4_tub_chairs_signed_are_quiet():
    v3, v4 = _load(V3_SITTING), _load(V4_SITTING)
    confirmed = PG.load_confirmed(_load(V4_REVIEW))
    assert confirmed, "v4 placement-review.json must carry the owner-signed tub-chair rots"
    recs = RD.diff_rounds([v3], [v4], confirmed=confirmed)
    # the renamed tub chairs pair by geometry; their facing change is owner-signed (rot 8/332),
    # so NO unexplained regression flag touches either chair -- the whole point of the instrument
    for name in (TUB_L, TUB_R):
        assert _touching(_unexplained(recs), name) == [], name


def test_real_v3_to_v4_tub_chairs_unsigned_go_loud():
    # strip the owner ledger: the SAME geometry-derived facing change is now a possible regression.
    # the right chair swung 0 -> 332 (delta 28) -> a MEDIUM unexplained facing flag surfaces.
    v3, v4 = _load(V3_SITTING), _load(V4_SITTING)
    recs = RD.diff_rounds([v3], [v4], confirmed=None)
    tub_flags = _touching(_unexplained(recs), TUB_R)
    assert tub_flags, "an unsigned tub-chair facing change must surface"
    assert tub_flags[0]["signal"] == "rebuild_diff:semantic_change_unexplained"


def test_real_v3_to_v4_injected_flip_is_critical_and_signable():
    # inject the historical wound at reversal magnitude: the left tub chair silently swung to face
    # the INTERIOR (rot 190, away from the south glass). Unsigned -> CRITICAL; add the matching
    # owner signature -> suppressed. That asymmetry is the instrument.
    v3, v4 = _load(V3_SITTING), _load(V4_SITTING)
    regressed = copy.deepcopy(v4)
    tubL = next(it for it in regressed["items"] if it["name"] == TUB_L)
    tubL["rot"] = 190
    loud = _touching(_unexplained(RD.diff_rounds([v3], [regressed], confirmed=None)), TUB_L)
    assert loud and loud[0]["severity"] == "CRITICAL"
    signed = [{"name": TUB_L, "rot": 190, "w": tubL["w"], "d": tubL["d"], "by": "owner"}]
    assert _touching(_unexplained(RD.diff_rounds([v3], [regressed], confirmed=signed)), TUB_L) == []


def test_real_bench_180_is_render_inert_not_critical():
    # THE first-live-run false CRITICAL, on real data: v3 typed the end-of-bed bench rot 180; the v4
    # clean rebuild dropped it to 0/south. The bench is a plain box, so a 180 flip is a byte-identical
    # render -> it must NOT surface as the CRITICAL reversal the naive delta fired. (The bench's other
    # doubts -- unsigned hand-typed identity -- live in a different collector, not this facing lane.)
    v3, v4 = _load(V3_MASTER), _load(V4_MASTER)
    recs = RD.diff_rounds([v3], [v4], confirmed=None)
    assert _touching(_unexplained(recs), BENCH) == []


def test_real_diff_is_deterministic():
    v3, v4 = _load(V3_SITTING), _load(V4_SITTING)
    conf = PG.load_confirmed(_load(V4_REVIEW))
    a = RD.diff_rounds([v3], [v4], confirmed=conf)
    b = RD.diff_rounds([v3], [v4], confirmed=conf)
    assert a == b


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} rebuild_diff tests passed")
