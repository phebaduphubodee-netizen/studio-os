"""Tests for vanishing_check.py — the reference photo's own camera.

THE STRONGEST TEST IN HERE IS A ROUND TRIP. A synthetic pinhole camera with a KNOWN focal
length projects two families of world-parallel lines; the module is handed only the
resulting image segments and must recover the focal length it was never told. That is a
positive control by construction: if it cannot recover a camera it built itself, no reading
it gives about a real photograph means anything.

Everything else pins a refusal, because this rung's way of being useless is to return a
confident camera from lines that do not support one.
"""
import json
import math

import pytest

import vanishing_check as VC


# --------------------------------------------------------------- a synthetic camera

F_TRUE = 1000.0
W, H = 1920.0, 1080.0
P = (W / 2.0, H / 2.0)


def project(d, f=F_TRUE, principal=P):
    """Camera-space direction -> its vanishing point in the image."""
    return (principal[0] + f * d[0] / d[2], principal[1] + f * d[1] / d[2])


def segments_through(vp, anchors):
    """Image segments that all pass through `vp` — what a correct marking looks like."""
    return [[list(a), [vp[0] + 0.5 * (a[0] - vp[0]), vp[1] + 0.5 * (a[1] - vp[1])]]
            for a in anchors]


def _doc(**over):
    # Two horizontal world directions 90 degrees apart, seen by a camera yawed between
    # them: exactly the two-point interior perspective the tutorial marks.
    a = (math.cos(math.radians(30)), 0.0, math.sin(math.radians(30)))
    b = (math.cos(math.radians(120)), 0.0, math.sin(math.radians(120)))
    doc = {
        "image_size": [W, H],
        "signed_by": "builder", "signed_at": "2026-08-28",
        "axis_x": segments_through(project(a), [(100, 200), (150, 900), (400, 60)]),
        "axis_y": segments_through(project(b), [(1800, 250), (1700, 950), (1500, 80)]),
    }
    doc.update(over)
    return doc


# --------------------------------------------------------------- line / vp

def test_a_line_is_normalised_so_residuals_are_pixels():
    a, b, c = VC.line_from((0, 0), (10, 0))
    assert math.hypot(a, b) == pytest.approx(1.0)
    # a point 5 px above the x-axis is 5 px from the line
    assert abs(a * 0 + b * 5 + c) == pytest.approx(5.0)


def test_a_zero_length_segment_is_refused():
    with pytest.raises(VC.VanishingError):
        VC.line_from((3, 3), (3, 3))


def test_the_vanishing_point_of_concurrent_lines_is_that_point():
    vp = (2692.0, 540.0)
    got, resid, cond = VC.vanishing_point(segments_through(vp, [(100, 200), (150, 900),
                                                                (400, 60)]))
    assert got[0] == pytest.approx(vp[0], abs=1e-6)
    assert got[1] == pytest.approx(vp[1], abs=1e-6)
    assert resid == pytest.approx(0.0, abs=1e-6)
    assert cond > 0.01


def test_one_line_cannot_make_a_vanishing_point():
    with pytest.raises(VC.VanishingError):
        VC.vanishing_point([[[0, 0], [10, 10]]])


def test_parallel_lines_are_refused_as_a_point_at_infinity():
    # THE REFUSAL THAT MATTERS MOST for an interior: verticals in a level shot are parallel
    # in the image, and their "vanishing point" is numerically meaningless.
    with pytest.raises(VC.VanishingError) as e:
        VC.vanishing_point([[[0, 0], [0, 500]], [[300, 0], [300, 500]],
                            [[600, 0], [600, 500]]])
    assert "infinity" in str(e.value)


def test_lines_that_do_not_agree_are_refused_with_their_residual():
    good = segments_through((2692.0, 540.0), [(100, 200), (150, 900)])
    bad = [[[0, 0], [100, 900]]]           # points nowhere near that vanishing point
    with pytest.raises(VC.VanishingError) as e:
        VC.vanishing_point(good + bad)
    assert "px RMS" in str(e.value)


# --------------------------------------------------------------- focal length

def test_the_round_trip_recovers_a_focal_length_it_was_never_told():
    # THE POSITIVE CONTROL. Only image segments go in; F_TRUE comes back out.
    sol = VC.solve(_doc())
    assert sol["focal_px"] == pytest.approx(F_TRUE, rel=1e-6)


def test_the_round_trip_recovers_the_field_of_view():
    sol = VC.solve(_doc())
    expected = math.degrees(2 * math.atan(W / (2 * F_TRUE)))
    assert sol["fov_h_deg"] == pytest.approx(expected, rel=1e-9)


def test_a_positive_dot_product_is_refused_rather_than_returning_an_imaginary_camera():
    # Both vanishing points on the same side of the principal point cannot come from two
    # perpendicular world directions.
    with pytest.raises(VC.VanishingError) as e:
        VC.focal_from_vps((P[0] + 500, P[1]), (P[0] + 900, P[1]), P)
    assert "f^2 would be negative" in str(e.value)


def test_fov_and_focal_are_inverses():
    f = VC.focal_from_fov(60.0, 1920)
    assert VC.fov_deg(f, 1920) == pytest.approx(60.0)


def test_an_impossible_field_of_view_is_refused():
    with pytest.raises(VC.VanishingError):
        VC.focal_from_fov(180.0, 1920)
    with pytest.raises(VC.VanishingError):
        VC.focal_from_fov(0.0, 1920)


# --------------------------------------------------------------- orientation

def test_tilt_is_not_guessed_when_nobody_said_which_axis_is_up():
    # THE FINDING THAT SHAPED THIS FUNCTION. The tutorial's own two axes are the ceiling
    # edge and the shelves — both horizontal. A rung that picks "whichever looks more
    # vertical" would return a confident tilt for a pair with no vertical in it.
    sol = VC.solve(_doc())
    assert sol["orientation"]["tilt_deg"] is None
    assert "does not say which marked axis is the world vertical" in VC.report(sol)


def test_tilt_is_computed_once_the_vertical_axis_is_declared():
    sol = VC.solve(_doc(vertical_axis="y"))
    assert sol["orientation"]["tilt_deg"] is not None


def test_the_three_axes_are_orthonormal():
    o = VC.solve(_doc())["orientation"]
    for v in (o["x_axis"], o["y_axis"], o["z_axis"]):
        assert math.sqrt(sum(c * c for c in v)) == pytest.approx(1.0)
    dot = sum(a * b for a, b in zip(o["x_axis"], o["y_axis"]))
    assert dot == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------- the document

def test_an_unsigned_lines_file_is_refused():
    doc = _doc()
    doc.pop("signed_by")
    with pytest.raises(VC.VanishingError) as e:
        VC.solve(doc)
    assert "signed" in str(e.value)


def test_a_missing_axis_is_refused():
    doc = _doc()
    doc.pop("axis_y")
    with pytest.raises(VC.VanishingError):
        VC.solve(doc)


def test_the_principal_point_defaults_to_the_image_centre_and_can_be_overridden():
    assert VC.solve(_doc())["principal_point"] == [W / 2.0, H / 2.0]
    assert VC.load_lines(_doc(principal_point=[10, 20]))[2] == [10, 20]


def test_a_wrong_principal_point_is_caught_by_the_dot_product_not_absorbed():
    # A shifted principal point does not quietly rescale the focal length: with these two
    # vanishing points it makes the configuration impossible, and the rung says so rather
    # than returning a plausible camera. This is the whole value of the f^2 sign check.
    with pytest.raises(VC.VanishingError):
        VC.solve(_doc(principal_point=[10, 20]))


# --------------------------------------------------------------- comparison

def test_no_camera_of_ours_says_so_rather_than_implying_a_match():
    gap, lines = VC.compare(VC.solve(_doc()))
    assert gap is None
    assert "none given" in lines[0]


def test_a_matching_camera_reports_a_zero_gap():
    sol = VC.solve(_doc())
    gap, _lines = VC.compare(sol, our_focal_px=F_TRUE)
    assert gap == pytest.approx(0.0, abs=1e-6)


def test_a_wider_lens_of_ours_reports_a_positive_gap():
    sol = VC.solve(_doc())
    gap, _ = VC.compare(sol, our_focal_px=F_TRUE / 2.0)
    assert gap > 10.0


def test_our_camera_may_be_given_as_a_field_of_view():
    sol = VC.solve(_doc())
    gap, _ = VC.compare(sol, our_fov_deg=sol["fov_h_deg"])
    assert gap == pytest.approx(0.0, abs=1e-9)


def test_the_axis_that_produced_a_quarter_turn_error_is_refused():
    """THE NEGATIVE CONTROL, in the frame's own numbers (2026-08-29).

    Family B of the TRN-003 solve — the window transom at slope +0.04296 and the
    island's front edge at -0.03109 — is 4.24 deg wide. It sails through the
    conditioning test above (that one only catches a singularity, at 0.057 deg) and
    it is the axis an island was built a quarter turn out of. Family A, the
    cabinetry, is 25.97 deg wide and still solves.
    """
    B = [[[0, 690.88], [1000, 733.84]], [[0, 1270.75], [1000, 1239.66]]]
    with pytest.raises(VC.VanishingError) as e:
        VC.vanishing_point(B)
    assert "4.2" in str(e.value) and "10.0" in str(e.value)

    A = [[[0, 534.93], [1000, 265.09]], [[0, 1343.17], [1000, 1518.93]]]
    (u, v), _resid, _cond = VC.vanishing_point(A)
    # the solve of record put family A's vanishing point at (-1809, 1031)
    assert abs(u + 1809) < 20 and abs(v - 1031) < 20
