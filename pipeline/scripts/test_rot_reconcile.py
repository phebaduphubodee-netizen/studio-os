"""
test_rot_reconcile.py -- pin the native_yaw <-> build_floor reconciliation with HARD-CODED
expected values (the module's own _prove() is a sweep proof; these pin the exact numbers a
regression would move). Run: python -m pytest test_rot_reconcile.py -q  (or python test_rot_reconcile.py)
"""
import math

import rot_reconcile as R


def _circ(a):
    return min(a % 360.0, (-a) % 360.0)


def test_offset_is_ninety():
    assert R.NATIVE_TO_BUILDFLOOR_OFFSET_DEG == 90.0


def test_cardinals_native_to_build_floor_pinned():
    # native yaw (forward CCW from +X) -> build_floor rot; the four cardinals, hard-pinned.
    #   forward +X(native 0)=East->build 90; +Y(90)=North->180; -X(180)=West->270; -Y(270)=South->0
    assert R.native_yaw_to_build_floor(0.0) == 90.0
    assert R.native_yaw_to_build_floor(90.0) == 180.0
    assert R.native_yaw_to_build_floor(180.0) == 270.0
    assert R.native_yaw_to_build_floor(270.0) == 0.0


def test_forward_vector_to_build_floor_pinned():
    # F(rot)=(sin,-cos): South forward (0,-1)->0, East (1,0)->90, North (0,1)->180, West (-1,0)->270
    assert _circ(R.forward_to_build_floor_rot(0.0, -1.0) - 0.0) < 1e-9
    assert _circ(R.forward_to_build_floor_rot(1.0, 0.0) - 90.0) < 1e-9
    assert _circ(R.forward_to_build_floor_rot(0.0, 1.0) - 180.0) < 1e-9
    assert _circ(R.forward_to_build_floor_rot(-1.0, 0.0) - 270.0) < 1e-9


def test_closed_form_equals_vector_over_sweep():
    # native+90 must equal the independent vector inverse atan2(fx,-fy) for EVERY heading.
    worst = 0.0
    for deg in range(0, 360):
        rad = math.radians(deg)
        fx, fy = math.cos(rad), math.sin(rad)
        nat = R.native_yaw_of_forward(fx, fy)
        worst = max(worst, _circ(R.native_yaw_to_build_floor(nat) - R.forward_to_build_floor_rot(fx, fy)))
    assert worst < 1e-6, worst


def test_is_rotation_not_reflection():
    # a reflection (build = K - native) must NOT fit; only the +90 rotation fits with 0 residual.
    K = R.forward_to_build_floor_rot(1.0, 0.0) + 0.0   # build at native 0
    rot_res = refl_res = 0.0
    for deg in range(0, 360):
        rad = math.radians(deg)
        fx, fy = math.cos(rad), math.sin(rad)
        nat = R.native_yaw_of_forward(fx, fy)
        build = R.forward_to_build_floor_rot(fx, fy)
        rot_res = max(rot_res, _circ(build - (nat + 90.0)))
        refl_res = max(refl_res, _circ(build - (K - nat)))
    assert rot_res < 1e-6
    assert refl_res > 45.0        # the mirror hypothesis is decisively rejected


def test_round_trip_inverse():
    for deg in (0.0, 37.0, 90.0, 213.4, 359.9):
        assert _circ(R.build_floor_to_native_yaw(R.native_yaw_to_build_floor(deg)) - deg) < 1e-9


def test_none_passes_through():
    assert R.native_yaw_to_build_floor(None) is None
    assert R.build_floor_to_native_yaw(None) is None
    assert R.forward_to_build_floor_rot(0.0, 0.0) is None   # zero vector = no facing


def test_convert_gt_doc_withdrawn_raises_by_default():
    # PREMISE REFUTED 2026-07-09: applying the +90 to GT facing encodes basis[0] (the SIDE) as the
    # front and corrupts F2 by 90deg. convert_gt_doc must RAISE unless the algebra-only escape is set.
    doc = {"meta": {}, "elements": [{"id": "a", "kind": "bed", "x": 0, "y": 0, "w": 1, "d": 1,
                                     "rot": 90.0}]}
    try:
        R.convert_gt_doc(doc)
    except ValueError as e:
        assert "WITHDRAWN" in str(e)
        return
    raise AssertionError("convert_gt_doc must RAISE by default (the +90 corrupts F2)")


def test_convert_gt_doc_only_touches_rot_elements():
    # _conditional_math_only exercises the +90 ALGEBRA only (never applied to live GT).
    doc = {"meta": {}, "elements": [
        {"id": "a", "kind": "bed", "x": 0, "y": 0, "w": 1, "d": 1, "rot": 90.0},
        {"id": "b", "x": 0, "y": 0, "w": 1, "d": 1},                 # rot-less -> untouched
    ]}
    out = R.convert_gt_doc(doc, _conditional_math_only=True)
    assert out["elements"][0]["rot"] == 180.0                        # 90 native +90 = 180 (basis[0]-as-front, NOT for live use)
    assert "rot" not in out["elements"][1]                          # honesty contract preserved
    assert doc["elements"][0]["rot"] == 90.0                        # original not mutated
    assert out["meta"]["rot_reconciled"]["n_rot_converted"] == 1


def test_convert_gt_doc_keeps_footprint_invariant_for_nonsquare():
    """native->build_floor is a +90 convention rotation, and placement_gate.footprint's AABB
    (w|cos|+d|sin| / w|sin|+d|cos|) TRANSPOSES under +90 unless w<->d are swapped (centre held).
    Since the adapter now emits the LOCAL un-yawed rect, convert_gt_doc must swap w<->d too, else a
    NON-square kinded box detection-misses ITSELF after reconcile. Squares (every other test here)
    are swap-invariant and cannot catch this -- so pin a 1000x400 box's footprint before == after."""
    import placement_gate as PG
    doc = {"meta": {}, "elements": [{"id": "b", "kind": "bed", "x": 100.0, "y": 200.0,
                                     "w": 1000.0, "d": 400.0, "rot": 90.0}]}
    before = PG.footprint(doc["elements"][0])
    out = R.convert_gt_doc(doc, _conditional_math_only=True)
    e = out["elements"][0]
    after = PG.footprint(e)
    assert e["rot"] == 180.0
    assert (e["w"], e["d"]) == (400.0, 1000.0)                       # w<->d swapped
    assert abs((e["x"] + e["w"] / 2.0) - 600.0) < 0.2               # centre x preserved (100+1000/2)
    assert abs((e["y"] + e["d"] / 2.0) - 400.0) < 0.2               # centre y preserved (200+400/2)
    for a, b in zip(before, after):
        assert abs(a - b) < 0.2, (before, after)                    # scored footprint INVARIANT
    assert doc["elements"][0]["w"] == 1000.0                        # original untouched (deepcopy)


def test_convert_gt_doc_refuses_double_application():
    # even in algebra-only mode, applying twice would add 180deg (silent facing reversal) -> RAISE.
    doc = {"meta": {}, "elements": [{"id": "a", "kind": "bed", "x": 0, "y": 0, "w": 1, "d": 1,
                                     "rot": 90.0}]}
    once = R.convert_gt_doc(doc, _conditional_math_only=True)
    try:
        R.convert_gt_doc(once, _conditional_math_only=True)
    except ValueError:
        return
    raise AssertionError("convert_gt_doc must raise on an already-reconciled doc")


def test_score_facing_consequence_the_plus90_corrupts_not_fixes():
    # CORRECTED 2026-07-09 (was: asserted the +90 'fixes' F2). A real reader reads the object's true
    # FRONT (into-room = (sinR,-cosR) for native yaw R) and encodes it in build_floor -> emits rot=R.
    # So native GT MATCHES a correct reader with NO conversion; the withdrawn +90 is what corrupts it.
    import benchmark_reader as B
    native_gt = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                               "rot": 90.0}]}
    correct_reader = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                                    "rot": 90.0}]}                    # build_floor rot of the TRUE front
    good = B.score_pair(native_gt, correct_reader)["F2_facing"]
    assert good["n"] == 1 and good["hits"] == 1 and good["cardinal_correct"] == 1.0  # native==correct, NO conversion
    corrupted_gt = R.convert_gt_doc(native_gt, _conditional_math_only=True)          # apply the withdrawn +90
    corrupted = B.score_pair(corrupted_gt, correct_reader)["F2_facing"]
    assert corrupted["n"] == 1 and corrupted["hits"] == 0            # +90 makes a correct reader 'wrong'


def test_prove_runs_clean():
    facts = R._prove(verbose=False)
    assert facts["offset_deg"] == 90.0
    assert facts["is_rotation_not_reflection"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"all {len(fns)} rot_reconcile tests PASS")
