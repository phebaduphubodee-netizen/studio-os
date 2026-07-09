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


def test_convert_gt_doc_only_touches_rot_elements():
    doc = {"meta": {}, "elements": [
        {"id": "a", "kind": "bed", "x": 0, "y": 0, "w": 1, "d": 1, "rot": 90.0},
        {"id": "b", "x": 0, "y": 0, "w": 1, "d": 1},                 # rot-less -> untouched
    ]}
    out = R.convert_gt_doc(doc)
    assert out["elements"][0]["rot"] == 180.0                        # 90 native -> 180 build
    assert "rot" not in out["elements"][1]                          # honesty contract preserved
    assert doc["elements"][0]["rot"] == 90.0                        # original not mutated
    assert out["meta"]["rot_reconciled"]["n_rot_converted"] == 1


def test_convert_gt_doc_refuses_double_application():
    # applying twice would add 180deg (silent facing reversal) -> must RAISE, not re-rotate.
    doc = {"meta": {}, "elements": [{"id": "a", "kind": "bed", "x": 0, "y": 0, "w": 1, "d": 1,
                                     "rot": 90.0}]}
    once = R.convert_gt_doc(doc)
    try:
        R.convert_gt_doc(once)
    except ValueError:
        return
    raise AssertionError("convert_gt_doc must raise on an already-reconciled doc")


def test_score_facing_consequence_with_real_scorer():
    import benchmark_reader as B
    # square + cardinal rot: footprint() re-rotates x/y/w/d, so a square keeps the AABB rot-
    # invariant and the pair IoU-matches -- isolating the convention effect on the bucket.
    native_gt = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                               "rot": 90.0}]}
    reader_pred = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                                 "rot": 180.0}]}
    raw = B.score_pair(native_gt, reader_pred)["F2_facing"]
    assert raw["n"] == 1 and raw["hits"] == 0                        # convention mismatch = wrong
    fixed = B.score_pair(R.convert_gt_doc(native_gt), reader_pred)["F2_facing"]
    assert fixed["cardinal_correct"] == 1.0                          # reconciled = exact


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
