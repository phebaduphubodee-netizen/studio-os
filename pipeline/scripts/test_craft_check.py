"""Tests for craft_check.

The load-bearing test is `test_the_published_table_is_reproduced_from_geometry`:
the segment table arrived from a Deep Research whose citation pointed at the DR's
own synthesised report, which is not a source this repo accepts. Rather than
quarantine the number or trust it, the module derives it — and this test is what
makes that claim checkable instead of asserted.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import craft_check as CC  # noqa: E402


def test_the_published_table_is_reproduced_from_geometry():
    # R (mm) -> segments per FULL circle, at D = 3000 mm, 1 arcminute.
    table = {2.5: 4, 5: 6, 10: 8, 25: 12, 50: 17, 100: 24, 250: 38, 500: 54}
    for r, n in table.items():
        assert CC.min_segments(r, 3000, quarter=False) == n, r


def test_quarter_and_full_agree():
    assert CC.min_segments(100, 3000, quarter=True) == 6      # 24 / 4
    assert CC.min_segments(100, 3000, quarter=False) == 24


def test_further_away_needs_fewer_segments():
    near = CC.min_segments(300, 2000, quarter=False)
    far = CC.min_segments(300, 8000, quarter=False)
    assert near > far


def test_a_radius_below_the_acuity_limit_needs_nothing():
    # A 2 mm fillet at 8 m subtends less than an arcminute whatever you do to it.
    assert CC.min_segments(2, 8000) == 1


def test_degenerate_inputs_do_not_raise():
    assert CC.min_segments(0, 3000) == 1
    assert CC.min_segments(100, 0) == 1


def test_acuity_is_a_knob_and_a_sharper_eye_demands_more():
    assert CC.min_segments(300, 4000, arcmin=0.5) > CC.min_segments(300, 4000, arcmin=1.0)


# --- the spec-level audit --------------------------------------------------

CAM = {"x_mm": 0.0, "y_mm": 0.0, "z_mm": 0.0}


def _spec(masses, cam=CAM):
    return {"camera": cam, "masses": masses}


def test_a_coarse_corner_near_the_camera_is_reported():
    spec = _spec([{"name": "bench", "kind": "oct", "cut": 200,
                   "c": [1000, 2000, 500], "s": [1, 1, 1]}])
    rows, short = CC.audit_silhouette(spec)
    assert len(rows) == 1 and len(short) == 1 and "bench" in short[0]


def test_a_fine_corner_far_away_passes():
    spec = _spec([{"name": "trim", "kind": "oct", "cut": 3,
                   "c": [3000, 4000, 1000], "s": [1, 1, 1]}])
    assert CC.audit_silhouette(spec)[1] == []


def test_an_explicit_seg_overrides_the_builder_default():
    m = {"name": "bench", "kind": "oct", "cut": 200, "c": [1000, 2000, 500],
         "s": [1, 1, 1], "seg": 32}
    assert CC.audit_silhouette(_spec([m]))[1] == []


def test_boxes_and_cloth_are_not_charged_for_corners_they_do_not_have():
    spec = _spec([{"name": "wall", "kind": "box", "cut": 200, "c": [1, 1, 1], "s": [1, 1, 1]},
                  {"name": "duvet", "kind": "cloth_duvet", "c": [1, 1, 1], "s": [1, 1, 1]}])
    assert CC.audit_silhouette(spec) == ([], [])


def test_an_oct_with_no_cut_is_a_square_prism_and_is_skipped():
    spec = _spec([{"name": "slab", "kind": "oct", "cut": 0, "c": [1, 1, 1], "s": [1, 1, 1]}])
    assert CC.audit_silhouette(spec) == ([], [])


def test_no_camera_is_a_reported_failure_not_a_silent_pass():
    rows, short = CC.audit_silhouette({"masses": [], "camera": {}})
    assert rows == [] and len(short) == 1 and "no solved camera" in short[0]


def test_the_reported_deviation_matches_the_formula():
    # The message quotes a sagitta; it must be the same one the maths used, or the
    # number in the report and the number in the decision are two different numbers.
    cut, seg = 300.0, 6
    spec = _spec([{"name": "bed", "kind": "oct", "cut": cut, "c": [3000, 4000, 0],
                   "s": [1, 1, 1], "seg": seg}])
    short = CC.audit_silhouette(spec)[1]
    sag = cut * (1 - math.cos((math.pi / 2 / seg) / 2))
    assert f"{sag:.2f} mm" in short[0]


# --- the knob this check reads has to reach the mesh ---------------------------
# Added 2026-08-08 after C3 read the rounded furniture as "low-poly, overly soft
# edges" and sending me to look proved the advisory had been unactionable all
# along: `craft_check` reads `m["seg"]`, NO spec has ever set it, and `_oct`
# hard-coded 6 without forwarding it. So the silhouette advisory named the same
# three masses every round and no edit to a spec could have silenced it.
#
# This is the TRN-001 roughness column again: a table set a value, the material
# path overrode it, and the column was dead for four rounds. The shape to hunt
# is A CHECKER THAT READS A FIELD THE BUILDER IGNORES — it measures a fiction
# and reports it with a decimal point.

def test_seg_actually_changes_the_mesh():
    import trn002_geom as G
    lo = G.oct_mesh((0, 0, 0), (1000, 1000, 1000), 200, seg=6)
    hi = G.oct_mesh((0, 0, 0), (1000, 1000, 1000), 200, seg=9)
    assert len(hi[0]) > len(lo[0]), "seg is inert in oct_mesh"
    assert (len(hi[0]) - len(lo[0])) == 8 * (9 - 6), \
        "four corners, top and bottom: each extra segment adds 8 verts"


def test_the_build_path_forwards_seg_to_the_mesh():
    # Source-level, deliberately. The build path needs bpy and cannot be
    # imported here, and the defect was not a wrong value — it was a parameter
    # that never travelled. A test that can only see the checker's side would
    # have passed throughout the years this was broken.
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "trn002_build.py"), encoding="utf-8").read()
    assert "seg=seg" in src, "_oct no longer forwards seg to oct_mesh"
    assert 'seg=int(m.get("seg", 6))' in src, \
        "the spec dispatch no longer reads seg off the mass"


def test_the_default_the_checker_assumes_is_the_default_the_builder_uses():
    import trn002_geom as G
    import inspect
    assert CC.DEFAULT_SEG == inspect.signature(G.oct_mesh).parameters["seg"].default, \
        "craft_check would grade every unset mass against the wrong baseline"


# --- cone_mesh: the shade idiom, added r35 -------------------------------------

def test_cone_is_triangles_only_and_winds_outward():
    import trn002_geom as G
    vs, fs = G.cone_mesh((0, 0, 1000), 90.0, 87.0, seg=24)
    assert all(len(f) == 3 for f in fs), "an n-gon cap is visible to a SketchUp recipient"
    assert G.inward_faces(vs, fs) == [], "first version had all 48 faces inverted"


def test_cone_apex_is_above_the_rim_when_point_up():
    import trn002_geom as G
    vs, _ = G.cone_mesh((0, 0, 1000), 90.0, 87.0, seg=24)
    zs = [v[2] for v in vs]
    assert abs(max(zs) * 1000 - 1000) < 1e-6
    assert abs(min(zs) * 1000 - (1000 - 87.0)) < 1e-6


def test_cone_rim_radius_is_the_radius_asked_for():
    import trn002_geom as G
    import math
    ax, ay = -1465.0, -4949.1
    vs, _ = G.cone_mesh((ax, ay, 1051.9), 89.6, 87.4, seg=24)
    rim = [v for v in vs[1:-1]]
    rr = [math.hypot(v[0] - ax / 1000.0, v[1] - ay / 1000.0) * 1000 for v in rim]
    assert max(abs(r - 89.6) for r in rr) < 1e-6


def test_seg_drives_the_cone_too():
    import trn002_geom as G
    assert len(G.cone_mesh((0, 0, 0), 50, 50, seg=32)[0]) \
        == len(G.cone_mesh((0, 0, 0), 50, 50, seg=24)[0]) + 8
