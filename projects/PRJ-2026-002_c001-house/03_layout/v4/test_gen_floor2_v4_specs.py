"""
test_gen_floor2_v4_specs.py -- unit tests for the LIVE v4 generator's facing wiring (no PDF).

v4 is the active floor-2 generator. It places CARDINAL loose pieces via snap() and the ANGLED
terrace tub chairs via angled() at a true drawn angle (rot 12/335). Both now apply an owner-signed
facing over the hand-read default through placement_gate.resolve_rot (the SAME confirmed_rot matcher
the gate checks), so:
  * BACKWARD-COMPAT — no confirmed[] => hand-read facing, NO facing_source (byte-identical regen).
  * NON-CARDINAL — an angled chair is signable via a numeric {"rot": ...}; a rebuild re-applies it
    instead of re-rolling the exact chair-facing the v3->v4 regression was about.
  * SINGLE SOURCE — after the generator applies a sign, the gate suppresses its facing flag; a
    contradicting build is raised. Cardinal + non-cardinal alike.

    python test_gen_floor2_v4_specs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_floor2_v4_specs as G4     # import-safe: sets up pipeline/scripts on the path too
import placement_gate as PG
import facing_reader as FR


def _cardcluster(cid=7, x=1000, y=1000, w=800, d=800, curve=True):
    return [{"id": cid, "x": x, "y": y, "w": w, "d": d, "curve": curve, "area_m2": w * d / 1e6}]


# ---- snap (CARDINAL): backward-compat + owner override --------------------------------
def test_v4_snap_no_confirmed_backward_compat():
    G4._REPORT.clear()
    it = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800)
    assert it["rot"] == 90 and "facing_source" not in it, it     # E -> 90, no sign


def test_v4_snap_confirmed_defaults_to_none():
    G4._REPORT.clear()
    a = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800)
    G4._REPORT.clear()
    b = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800, confirmed=None)
    assert a == b


def test_v4_snap_cardinal_override():
    G4._REPORT.clear()
    it = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800,
                 confirmed=[{"name": "โซฟา", "facing": "W"}])       # E(90) -> W(270), 180 flip
    assert it["rot"] == 270 and it["facing_source"] == "owner-signed", it


# ---- angled (NON-CARDINAL): backward-compat + numeric override ------------------------
def test_v4_angled_no_confirmed_keeps_drawn_angle():
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750)
    assert it["rot"] == 12 and it.get("angled") is True and "facing_source" not in it, it


def test_v4_angled_numeric_non_cardinal_override():
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "เก้าอี้ tub ขวา", "armchair", 7630, 1405, 660, 640, 12, 750,
                   confirmed=[{"name": "เก้าอี้ tub ขวา", "rot": 335}])
    assert it["rot"] == 335 and it["facing_source"] == "owner-signed", it   # the cardinal ledger could NOT do this


def test_v4_angled_cardinal_sign_applies_to_angled_piece():
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750,
                   confirmed=[{"name": "เก้าอี้ tub ซ้าย", "facing": "S"}])   # S -> rot 0
    assert it.get("rot", 0) == 0 and it["facing_source"] == "owner-signed", it


def test_v4_angled_size_guard_rejects_reused_name():
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750,
                   confirmed=[{"name": "เก้าอี้ tub ซ้าย", "rot": 335, "w": 300, "d": 300}])  # wrong size
    assert it["rot"] == 12 and "facing_source" not in it, it   # stale entry ignored -> drawn angle kept


def test_v4_angled_sign_landing_on_cardinal_does_not_transpose():
    # REGRESSION: an owner sign that resolves to EXACTLY 90/270 on an ANGLED piece must ROTATE the
    # oriented box, never trip to_spec's cluster-AABB pre-swap (which would store the rot=0 footprint
    # while claiming rot 90 -> a 90-deg-wrong render the gate self-consistently fails to flag).
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "tub", "armchair", 5000, 5000, 800, 600, 11, 760,
                   confirmed=[{"name": "tub", "rot": 90, "w": 800, "d": 600}])
    assert it["rot"] == 90 and it["facing_source"] == "owner-signed", it
    # oriented dims PRESERVED (no swap): the box is 800x600 in its own frame, sitting at rot 90
    assert it["w"] == 800 and it["d"] == 600, it
    # ...and the gate's rotated AABB is continuous (an 800x600 box at rot 90 -> 600x800), NOT the
    # rot=0 extents (800x600) the pre-swap bug produced.
    fp = PG.footprint(it)
    assert round(fp[2] - fp[0]) == 600 and round(fp[3] - fp[1]) == 800, fp
    # a cardinal facing sign that maps to 90 (E) reproduces identically (same swap trap)
    G4._REPORT.clear()
    it2 = G4.angled("sitting_room", "tub", "armchair", 5000, 5000, 800, 600, 11, 760,
                    confirmed=[{"name": "tub", "facing": "E", "w": 800, "d": 600}])
    assert it2["w"] == 800 and it2["d"] == 600 and it2["rot"] == 90, it2


# ---- SINGLE SOURCE: generator applies a NON-cardinal sign -> gate suppresses/raises ----
def test_v4_generator_and_gate_agree_non_cardinal():
    sign = [{"name": "เก้าอี้ tub ซ้าย", "rot": 335, "w": 680, "d": 640}]
    G4._REPORT.clear()
    it = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750, confirmed=sign)
    assert it["rot"] == 335                                   # generator applied the non-cardinal sign
    assert FR.facing_from_rot(it["rot"]) is None              # 335 is genuinely non-cardinal
    # gate, given the SAME sign, sees the built rot AGREE -> suppresses (no facing flag)
    assert PG.facing_flags([it], [], confirmed=sign) == [], "gate must suppress a correctly-applied non-cardinal sign"
    # a contradicting build (rot re-rolled back to the drawn 12) is raised, not suppressed
    it_bad = dict(it, rot=12)
    flags = PG.facing_flags([it_bad], [], confirmed=sign)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
    assert flags[0]["read"] == "rot335", flags               # non-cardinal shown as a deg label


# ---- orphan-signature gate: a detached sign hard-FAILs instead of silently re-rolling ----
def test_v4_orphan_gate_passes_when_signs_bind():
    G4._REPORT.clear()
    pieces = [G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750),
              G4.angled("sitting_room", "เก้าอี้ tub ขวา", "armchair", 7630, 1405, 660, 640, 335, 750)]
    confirmed = [{"name": "เก้าอี้ tub ซ้าย", "rot": 8, "w": 680, "d": 640},
                 {"name": "เก้าอี้ tub ขวา", "rot": 332, "w": 660, "d": 640}]
    assert len(G4.assert_signatures_applied(pieces, confirmed)) == 2


def test_v4_orphan_gate_fails_on_detached_sign():
    G4._REPORT.clear()
    pieces = [G4.angled("sitting_room", "เก้าอี้ tub RENAMED", "armchair", 6331, 949, 680, 640, 12, 750)]
    confirmed = [{"name": "เก้าอี้ tub ซ้าย", "rot": 8, "w": 680, "d": 640}]   # this name no longer exists
    raised = False
    try:
        G4.assert_signatures_applied(pieces, confirmed, where="sitting_room")
    except SystemExit as ex:
        raised = True
        assert "ORPHAN" in str(ex) and "เก้าอี้ tub ซ้าย" in str(ex), ex
    assert raised, "a detached signature must hard-FAIL the generate, not silently re-roll the facing"


def test_v4_orphan_gate_empty_ledger_is_noop():
    assert G4.assert_signatures_applied([{"name": "x", "kind": "bed", "w": 1, "d": 1}], []) == []


def test_v4_orphan_gate_wildcard_matches_union_pool():
    # main() routes a '*' (any-room) sign against the UNION of both rooms, so it must NOT be
    # false-orphaned merely because it doesn't live in one of them — it binds if it matches EITHER.
    master = [{"name": "bed", "kind": "bed", "w": 2000, "d": 2100, "rot": 270}]
    sitting = [{"name": "sofa", "kind": "sofa", "w": 1000, "d": 2200, "rot": 90}]
    wild = [{"name": "sofa", "rot": 90, "w": 1000, "d": 2200, "room": "*"}]
    assert len(G4.assert_signatures_applied(master + sitting, wild)) == 1     # binds in sitting, no false-block


def test_v4_orphan_gate_unknown_room_binds_to_nothing():
    # main() checks a sign whose room the generator never produces against an EMPTY pool -> always
    # orphan, so a typo'd 'room' can't be silently dropped by both room filters and skipped.
    stray = [{"name": "x", "rot": 0, "w": 1, "d": 1, "room": "kitchen"}]
    try:
        G4.assert_signatures_applied([], stray, where="unknown room")
        assert False, "a sign for a room the generator never produces must orphan"
    except SystemExit as ex:
        assert "ORPHAN" in str(ex), ex


# ---- confirmed_kind wiring: identity signs stick, geometry never moves -----------------
def test_v4_snap_kind_sign_changes_identity_not_geometry():
    G4._REPORT.clear()
    a = G4.snap("sitting_room", "หีบปลายเตียง", "cabinet", _cardcluster(curve=False), set(),
                (1400, 1400), "E", 800)
    G4._REPORT.clear()
    b = G4.snap("sitting_room", "หีบปลายเตียง", "cabinet", _cardcluster(curve=False), set(),
                (1400, 1400), "E", 800,
                confirmed=[{"name": "หีบปลายเตียง", "kind": "bench"}])
    assert b["kind"] == "bench" and b["kind_source"] == "owner-signed", b
    ga = {k: v for k, v in a.items() if k not in ("kind", "kind_source")}
    gb = {k: v for k, v in b.items() if k not in ("kind", "kind_source")}
    assert ga == gb, (ga, gb)     # the sign changed IDENTITY only — nothing geometric moved


def test_v4_kind_sign_never_changes_cluster_match():
    # rect cluster #1 sits ON the anchor; curved #2 is farther. Hand kind 'cabinet' (rect want)
    # matches #1 (score 0 vs 283+350). If the signed kind 'armchair' (curve want) were applied
    # BEFORE match(), the +350 mismatch penalty would flip the snap to #2 — a signature MOVING a
    # piece, geometry the owner never signed. Pin after-match application.
    cls = [{"id": 1, "x": 1000, "y": 1000, "w": 800, "d": 800, "curve": False, "area_m2": 0.64},
           {"id": 2, "x": 1200, "y": 1200, "w": 800, "d": 800, "curve": True, "area_m2": 0.64}]
    G4._REPORT.clear()
    it = G4.snap("sitting_room", "x", "cabinet", cls, set(), (1400, 1400), "E", 800,
                 confirmed=[{"name": "x", "kind": "armchair"}])
    assert it["cluster"] == 1, it
    assert it["kind"] == "armchair" and it["kind_source"] == "owner-signed", it


def test_v4_orphan_gate_covers_kind_only_sign():
    # kind-only signs ride the SAME name+size join — orphan protection covers them from day one
    G4._REPORT.clear()
    piece = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750)
    bound = [{"name": "เก้าอี้ tub ซ้าย", "kind": "armchair", "w": 680, "d": 640}]
    assert len(G4.assert_signatures_applied([piece], bound)) == 1
    detached = [{"name": "ชื่อที่ไม่มีจริง", "kind": "armchair"}]
    try:
        G4.assert_signatures_applied([piece], detached, where="sitting_room")
        assert False, "a detached kind sign must orphan (hard-FAIL), not be silently skipped"
    except SystemExit as ex:
        assert "ORPHAN" in str(ex), ex


# ---- zone wiring: an owner-signed ZONE stamps the spec item (mirrors kind), geometry never moves ----
def test_v4_snap_zone_sign_stamps_zone_and_source():
    G4._REPORT.clear()
    it = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800,
                 confirmed=[{"name": "โซฟา", "zone": "below_grade"}])
    assert it["zone"] == "below_grade" and it["zone_source"] == "owner-signed", it


def test_v4_snap_no_zone_sign_omits_zone_keys_byte_identical():
    # no sign AND a non-zone (facing) sign both leave the item free of zone keys -> byte-identical JSON
    G4._REPORT.clear()
    a = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800)
    G4._REPORT.clear()
    b = G4.snap("sitting_room", "โซฟา", "sofa", _cardcluster(), set(), (1400, 1400), "E", 800,
                confirmed=[{"name": "โซฟา", "facing": "W"}])
    assert "zone" not in a and "zone_source" not in a, a
    assert "zone" not in b and "zone_source" not in b, b


def test_v4_zone_sign_relabels_never_moves_geometry():
    G4._REPORT.clear()
    a = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750)
    G4._REPORT.clear()
    b = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750,
                  confirmed=[{"name": "เก้าอี้ tub ซ้าย", "zone": "below_grade", "w": 680, "d": 640}])
    assert b["zone"] == "below_grade" and b["zone_source"] == "owner-signed", b
    ga = {k: v for k, v in a.items() if k not in ("zone", "zone_source")}
    gb = {k: v for k, v in b.items() if k not in ("zone", "zone_source")}
    assert ga == gb, (ga, gb)      # the sign changed CLASS only — nothing geometric moved (mirror of kind test)


def test_v4_orphan_gate_covers_zone_only_sign():
    # a zone-only sign (no rot/kind/facing) must ride the SAME orphan protection: a detached one
    # hard-FAILs instead of silently reverting a below_grade piece to floor-2 placement.
    G4._REPORT.clear()
    piece = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750)
    bound = [{"name": "เก้าอี้ tub ซ้าย", "zone": "below_grade", "w": 680, "d": 640}]
    assert len(G4.assert_zone_signatures_applied([piece], [], bound)) == 1
    detached = [{"name": "ชื่อที่ไม่มีจริง", "zone": "below_grade"}]
    raised = False
    try:
        G4.assert_zone_signatures_applied([piece], [], detached, where="sitting_room")
    except SystemExit as ex:
        raised = True
        assert "ORPHAN" in str(ex), ex
    assert raised, "a detached zone sign must hard-FAIL, not silently revert to floor placement"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} gen_floor2_v4_specs tests passed")
