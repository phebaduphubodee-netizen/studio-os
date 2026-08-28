"""Tests for contrast_delta.py — lit-minus-shadow held on ONE material.

THE ONE THING THESE TESTS EXIST FOR. This rung's failure mode is that "this object has
no shadow on it" and "this object has a shadow of zero" both want to print a zero, and
they mean opposite things — the first is a refusal and the second is a reading. Every
refusal path below is pinned from the direction that would let it leak out as a number.

The second thing they pin is the positive control. An absence claim from an instrument
nobody proved can fire is worth nothing (exit-test clause 2b), so the control is tested
both ways: it must fire on pixels that can carry a step, and it must NOT quietly pass on
pixels that cannot.
"""

import json
import math

import pytest

import contrast_delta as CD


# ------------------------------------------------------------------- otsu

def test_otsu_finds_the_valley_between_two_clean_modes():
    vals = [40.0] * 500 + [160.0] * 500
    t, sep = CD.otsu(vals)
    assert 40 <= t < 160
    assert sep > 0.99          # two point masses: almost all variance is between-class


def test_separability_alone_cannot_tell_one_mode_from_two():
    # THE FINDING THAT SHAPED THIS MODULE, pinned so nobody re-simplifies the cut back to
    # separability. A UNIFORM histogram has exactly one mode and no shadow anywhere, yet
    # Otsu's split of it explains ~75% of the variance — past any floor worth setting.
    vals = [float(100 + (i % 40)) for i in range(4000)]
    _t, sep = CD.otsu(vals)
    assert sep > 0.7
    assert sep > CD.SEP_FLOOR          # a separability gate would have let this through


def test_otsu_refuses_a_sample_it_cannot_threshold():
    with pytest.raises(CD.ContrastError):
        CD.otsu([12.0])


# ------------------------------------------------------------------- valley_ratio

def test_valley_is_deep_between_two_separated_modes():
    vals = [40.0] * 500 + [160.0] * 500
    t, _sep = CD.otsu(vals)
    assert CD.valley_ratio(vals, t) < 0.1


def test_valley_is_full_across_a_flat_distribution():
    vals = [float(100 + (i % 40)) for i in range(4000)]
    t, _sep = CD.otsu(vals)
    assert CD.valley_ratio(vals, t) > CD.VALLEY_MAX


def test_valley_is_full_across_a_smooth_ramp():
    # A single surface shading off gradually is the exact case a shadow reading must not
    # claim, and it is the commonest thing in an interior render.
    vals = [float(v) for v in range(60, 200)] * 30
    t, _sep = CD.otsu(vals)
    assert CD.valley_ratio(vals, t) > CD.VALLEY_MAX


# ------------------------------------------------------------------- split_object

def test_split_reads_a_planted_gap_exactly():
    vals = [80.0] * 600 + [180.0] * 600
    row = CD.split_object(vals)
    assert row["ok"] is True
    assert row["shadow"] == pytest.approx(80.0)
    assert row["lit"] == pytest.approx(180.0)
    assert row["delta"] == pytest.approx(100.0)


def test_a_sliver_is_a_refusal_and_carries_no_delta():
    row = CD.split_object([100.0] * (CD.MIN_PIXELS - 1))
    assert row["ok"] is False
    assert row["reason"] == "sliver"
    assert "delta" not in row


def test_a_unimodal_object_is_refused_not_reported_as_zero():
    # THE CENTRAL CASE. A flatly-lit object still yields an Otsu threshold, and the two
    # medians either side of it still subtract to something. That something must never
    # reach the sheet as a reading.
    vals = [float(100 + (i % 40)) for i in range(4000)]
    row = CD.split_object(vals)
    assert row["ok"] is False
    assert row["reason"] == "unimodal"
    assert "delta" not in row


def test_a_smoothly_shaded_surface_is_refused():
    row = CD.split_object([float(v) for v in range(60, 200)] * 30)
    assert row["ok"] is False
    assert row["reason"] == "unimodal"


def test_an_anti_aliased_rim_is_refused_as_a_rim():
    # A big bright body with a thin dark fringe: separable, but the dark side is an edge,
    # not a lighting state.
    vals = [200.0] * 2000 + [40.0] * 40
    row = CD.split_object(vals)
    assert row["ok"] is False
    assert row["reason"] == "rim"
    assert row["share"] < CD.MIN_CLASS_SHARE


def test_refusals_still_carry_their_evidence():
    row = CD.split_object([float(100 + (i % 40)) for i in range(4000)])
    assert row["px"] == 4000
    assert "sep" in row and "valley" in row and row["detail"]


# ------------------------------------------------------------------- positive control

def test_control_fires_on_pixels_that_can_carry_a_step():
    vals = [100.0 + (i % 11) for i in range(2000)]     # flat: no real split available
    fired, recovered, _detail = CD.positive_control(vals)
    assert fired is True
    assert recovered == pytest.approx(CD.CONTROL_K, abs=CD.CONTROL_TOL)


def test_control_does_not_fire_when_there_are_too_few_pixels():
    fired, recovered, detail = CD.positive_control([100.0] * 10)
    assert fired is False
    assert recovered is None
    assert "px" in detail


def test_control_is_measured_against_the_objects_own_baseline():
    # An object that ALREADY has a wide spread must not let the control claim credit for
    # that spread: the recovered value is the planted step alone.
    vals = [float(v) for v in range(0, 200)] * 20      # a broad ramp, baseline gap ~100
    fired, recovered, _ = CD.positive_control(vals)
    assert fired is True
    assert recovered == pytest.approx(CD.CONTROL_K, abs=CD.CONTROL_TOL)


# ------------------------------------------------------------------- summarise / report

def _row(name, delta=None, ok=True, reason=None):
    if ok:
        return {"ok": True, "name": name, "px": 1000, "sep": 0.8, "valley": 0.1,
                "share": 0.4, "shadow": 100.0, "lit": 100.0 + delta,
                "delta": float(delta)}
    return {"ok": False, "name": name, "reason": reason, "px": 10, "detail": "d"}


def test_frame_delta_is_the_median_over_measured_objects_only():
    rows = [_row("a", 80), _row("b", 100), _row("c", 120),
            _row("d", ok=False, reason="unimodal")]
    ok, bad, frame, ref = CD.summarise(rows)
    assert len(ok) == 3 and len(bad) == 1
    assert frame == pytest.approx(100.0)
    assert ref is None


def test_a_frame_with_nothing_split_reports_none_never_zero():
    rows = [_row("a", ok=False, reason="unimodal"), _row("b", ok=False, reason="sliver")]
    ok, bad, frame, _ref = CD.summarise(rows)
    assert ok == []
    assert frame is None
    assert "no object in this frame" in CD.report(ok, bad, frame, None)


def test_report_names_every_object_it_could_not_read():
    rows = [_row("shelf", 90), _row("oven", ok=False, reason="rim")]
    ok, bad, frame, _ = CD.summarise(rows)
    text = CD.report(ok, bad, frame, None)
    assert "UNSPLIT 1" in text
    assert "oven" in text and "rim" in text


def test_no_reference_says_so_rather_than_implying_a_match():
    text = CD.report([_row("a", 100)], [], 100.0, None)
    assert "compares it to nothing" in text


# ------------------------------------------------------------------- reference side

def test_reference_pairs_become_one_delta_each():
    grid = {(10, 10): (170, 170, 170), (20, 20): (80, 80, 80)}
    rows = CD.reference_deltas(lambda x, y: grid[(x, y)],
                               [{"material": "marble", "lit": [10, 10],
                                 "shadow": [20, 20]}])
    assert rows[0]["delta"] == pytest.approx(90.0, abs=0.5)
    assert rows[0]["material"] == "marble"


def test_a_pair_without_a_material_is_refused_because_identity_is_signed():
    with pytest.raises(CD.ContrastError):
        CD.reference_deltas(lambda x, y: (0, 0, 0), [{"lit": [1, 1], "shadow": [2, 2]}])


def test_an_empty_samples_file_is_a_refusal_not_an_empty_match():
    with pytest.raises(CD.ContrastError):
        CD.reference_deltas(lambda x, y: (0, 0, 0), [])


def test_the_videos_own_numbers_reproduce():
    # 3D Shaker 15:00-15:45. Reference pairs 170/80, 250/150, 210/110; their render
    # 150/50 and 210/100. Both sides land on ~100 codes, which is the claim.
    def grey(v):
        return (v, v, v)

    ref = CD.reference_deltas(
        lambda x, y: grey(x),
        [{"material": "marble-a", "lit": [170, 0], "shadow": [80, 0]},
         {"material": "marble-b", "lit": [250, 0], "shadow": [150, 0]},
         {"material": "marble-c", "lit": [210, 0], "shadow": [110, 0]}])
    deltas = [r["delta"] for r in ref]
    assert all(d == pytest.approx(90.0, abs=10.5) for d in deltas)
    ours = [CD.split_object([50.0] * 600 + [150.0] * 600)["delta"],
            CD.split_object([100.0] * 600 + [210.0] * 600)["delta"]]
    assert all(abs(o - 100) <= 11 for o in ours)


# ------------------------------------------------------------------- average colour

def test_average_colour_is_the_mean_of_every_pixel():
    assert CD.average_color([(0, 0, 0), (200, 100, 50)]) == (100.0, 50.0, 25.0)


def test_average_colour_refuses_an_empty_image():
    with pytest.raises(CD.ContrastError):
        CD.average_color([])


def test_colour_gap_is_zero_for_identical_means():
    assert CD.color_gap((10, 20, 30), (10, 20, 30)) == pytest.approx(0.0)
    assert CD.color_gap((0, 0, 0), (3, 4, 0)) == pytest.approx(5.0)


# ------------------------------------------------------------------- frame path

def test_a_mask_that_is_not_the_frames_size_is_refused():
    np = pytest.importorskip("numpy")
    beauty = np.zeros((10, 10, 3), dtype=np.float32)
    mask = np.zeros((10, 11, 3), dtype=np.int16)
    with pytest.raises(CD.ContrastError):
        CD.measure_frame(beauty, mask, {1: "a"})


def test_measure_frame_reads_a_planted_two_tone_object():
    np = pytest.importorskip("numpy")
    h, w = 40, 40
    beauty = np.zeros((h, w, 3), dtype=np.float32)
    beauty[:20, :, :] = 60.0            # shadow half
    beauty[20:, :, :] = 160.0           # lit half
    mask = np.zeros((h, w, 3), dtype=np.int16)
    ident = 1
    mask[:, :] = CD.VP.id_to_srgb(ident)
    rows = CD.measure_frame(beauty, mask, {ident: "wall"}, min_px=100)
    assert len(rows) == 1
    assert rows[0]["ok"] is True
    assert rows[0]["delta"] == pytest.approx(100.0, abs=1.0)
    assert rows[0]["name"] == "wall"


def test_a_swapped_reference_pair_is_refused_not_reported_as_a_negative_delta():
    # FOUND BY RUNNING THE CLI, not by reading it: arbitrary sample coordinates produced a
    # REFERENCE of -4.1 codes and printed it as a reading. A negative lit-minus-shadow
    # cannot describe lighting; it means the two points are the wrong way round.
    def grey(v):
        return (v, v, v)

    with pytest.raises(CD.ContrastError) as e:
        CD.reference_deltas(lambda x, y: grey(x),
                            [{"material": "marble", "lit": [80, 0], "shadow": [170, 0]}])
    assert "not the brighter one" in str(e.value)


def test_an_equal_pair_is_refused_too():
    with pytest.raises(CD.ContrastError):
        CD.reference_deltas(lambda x, y: (100, 100, 100),
                            [{"material": "m", "lit": [1, 1], "shadow": [2, 2]}])
