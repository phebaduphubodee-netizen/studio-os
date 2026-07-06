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


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} gen_floor2_v4_specs tests passed")
