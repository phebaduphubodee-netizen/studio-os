"""Tests for value_probe.py — the per-OBJECT render measurement.

These pin the properties that make a MEASUREMENT trustworthy, because the reason this
module exists is that a hand-drawn region probe reported four different objects (155,
165, 178, 199) as one value at 183 +-2 and I believed it:
  - the palette round-trips exactly and id 0 stays reserved;
  - decoding is nearest-level, so a stray pixel cannot land on a wrong-but-legal id;
  - an object the probe could not see reports as ABSENT, never as dark;
  - and a mask from a different frame refuses to decode at all.

Pure python — no bpy, no Blender.
"""
import os

import pytest

import value_probe as vp


# --------------------------------------------------------------------------- where it writes

def test_the_mask_and_its_sidecar_land_in_the_same_directory():
    """The defect this pins, found 2026-08-02: the PNG went to C:\\_private\\ and the
    JSON to the repo, because Blender and Python disagree about a drive-less relative
    path on Windows. A sidecar whose job is to certify the image beside it cannot do
    that from a different directory."""
    png, js = vp.mask_paths(os.path.join("_private", "x", "mask.png"))
    assert os.path.dirname(png) == os.path.dirname(js)
    assert os.path.splitext(js)[1] == ".json"


def test_a_mask_path_is_absolute_so_two_writers_cannot_disagree_about_here():
    png, js = vp.mask_paths(os.path.join("_private", "x", "mask.png"))
    assert os.path.isabs(png) and os.path.isabs(js)


def test_an_already_absolute_path_is_left_where_the_caller_put_it():
    given = os.path.abspath(os.path.join("_private", "x", "mask.png"))
    png, _ = vp.mask_paths(given)
    assert png == given


# --------------------------------------------------------------------------- palette

def test_every_id_round_trips():
    for i in range(1, vp.MAX_ID + 1):
        assert vp.srgb_to_id(vp.id_to_srgb(i)) == i


def test_id_zero_is_reserved_for_not_measured():
    """A black pixel must never be confused with a measured object."""
    assert vp.srgb_to_id((0, 0, 0)) == 0
    with pytest.raises(vp.ProbeError):
        vp.id_to_srgb(0)


def test_ids_outside_the_palette_raise():
    for bad in (-1, vp.MAX_ID + 1, 10_000):
        with pytest.raises(vp.ProbeError, match="outside"):
            vp.id_to_srgb(bad)


def test_bool_is_not_an_id():
    """True == 1 in Python; an accidental boolean must not silently become object #1."""
    with pytest.raises(vp.ProbeError, match="must be an int"):
        vp.id_to_srgb(True)


def test_decoding_is_nearest_level_so_small_drift_cannot_change_the_id():
    """Filtering, PNG rounding or a colour-management surprise can move a channel a few
    codes. Half a level (25) is the guaranteed margin, so +-12 must be safe everywhere."""
    for i in (1, 37, 100, vp.MAX_ID):
        base = vp.id_to_srgb(i)
        for d in (-12, -5, 5, 12):
            drifted = tuple(min(255, max(0, c + d)) for c in base)
            assert vp.srgb_to_id(drifted) == i, (i, d)


def test_palette_capacity_matches_the_level_table():
    assert vp.MAX_ID == len(vp.LEVELS) ** 3 - 1


# --------------------------------------------------------------------------- luma

def test_luma_is_rec709_on_encoded_pixels():
    assert vp.luma((255, 255, 255)) == pytest.approx(255.0)
    assert vp.luma((0, 0, 0)) == 0.0
    assert vp.luma((255, 0, 0)) == pytest.approx(0.2126 * 255)


def test_luma_ranks_green_above_red_above_blue():
    """The Rec.709 weights are what makes this 'what the eye ranks' rather than a mean."""
    assert vp.luma((0, 255, 0)) > vp.luma((255, 0, 0)) > vp.luma((0, 0, 255))


# --------------------------------------------------------------------------- median

def test_median_is_odd_and_even_safe():
    assert vp.median([3, 1, 2]) == 2
    assert vp.median([4, 1, 2, 3]) == 2.5


def test_median_of_nothing_raises_rather_than_returning_zero():
    """A zero here would read as 'this object rendered black'."""
    with pytest.raises(vp.ProbeError):
        vp.median([])


def test_median_survives_a_rim_of_blended_edge_pixels():
    """Anti-aliased silhouettes put a minority of wrong-valued pixels in every bucket.
    That is exactly why the report is a median and not a mean."""
    body = [180.0] * 1000
    rim = [20.0] * 90 + [250.0] * 90
    assert vp.median(body + rim) == pytest.approx(180.0)
    mean = sum(body + rim) / len(body + rim)
    assert abs(mean - 180.0) > 1.0


# --------------------------------------------------------------------------- aggregate

def _samples(spec):
    for i, (v, n) in spec.items():
        for _ in range(n):
            yield (i, v)


def test_aggregate_reports_median_share_and_pixel_count():
    rows = vp.aggregate(_samples({1: (150.0, 400), 2: (200.0, 600)}),
                        {1: "bed__throw", 2: "bed__duvet"}, total_px=2000)
    by = {r["name"]: r for r in rows}
    assert by["bed__throw"]["value"] == pytest.approx(150.0)
    assert by["bed__duvet"]["px"] == 600
    assert by["bed__duvet"]["share"] == pytest.approx(0.3)


def test_aggregate_sorts_brightest_first():
    rows = vp.aggregate(_samples({1: (150.0, 400), 2: (200.0, 400), 3: (100.0, 400)}),
                        {1: "a", 2: "b", 3: "c"})
    assert [r["name"] for r in rows] == ["b", "a", "c"]


def test_an_object_with_no_pixels_is_reported_not_dropped():
    """An object the probe could not see is a FINDING. Dropping it is how a probe starts
    flattering — the report would read as 'everything checked out'."""
    rows = vp.aggregate(_samples({1: (150.0, 400)}), {1: "seen", 2: "occluded"})
    by = {r["name"]: r for r in rows}
    assert by["occluded"]["px"] == 0
    assert by["occluded"]["value"] is None


def test_a_sliver_is_reported_but_never_ranked():
    rows = vp.aggregate(_samples({1: (150.0, vp.MIN_PIXELS - 1)}), {1: "sliver"})
    assert rows[0]["px"] == vp.MIN_PIXELS - 1
    assert rows[0]["value"] is None


def test_samples_for_ids_nobody_asked_about_are_ignored():
    rows = vp.aggregate(_samples({1: (150.0, 400), 99: (10.0, 9999)}), {1: "asked"})
    assert len(rows) == 1 and rows[0]["value"] == pytest.approx(150.0)


def test_measured_map_omits_slivers_rather_than_zero_filling():
    """A rung measured on a piece the camera cannot see must reach value_ladder as
    MISSING (which it reports) and never as 0.0 (which it would rank as very dark)."""
    rows = vp.aggregate(_samples({1: (150.0, 400), 2: (200.0, 5)}), {1: "big", 2: "tiny"})
    m = vp.measured_map(rows)
    assert m == {"big": pytest.approx(150.0)}


def test_report_renders_every_row_including_the_unseen():
    rows = vp.aggregate(_samples({1: (150.0, 400)}), {1: "seen", 2: "gone"}, total_px=1000)
    text = vp.report(rows)
    assert "seen" in text and "gone" in text


# --------------------------------------------------------------------------- integration

def test_measured_map_feeds_value_ladder_check_render():
    """The two halves have to fit: the probe's output IS the ladder's input."""
    import value_ladder as vl
    names = {i: obj for i, (_n, obj, _v) in enumerate(vl.LADDER, start=1)}
    spec = {i: (target, 500) for i, (_n, _o, target) in enumerate(vl.LADDER, start=1)}
    rows = vp.aggregate(_samples(spec), names, total_px=10_000)
    assert vl.check_render(vp.measured_map(rows)) == []


# --------------------------------------------------------------------------- the real path

def test_the_numpy_decoder_agrees_exactly_with_the_pure_functions():
    """The CLI cannot use the scalar path over 2.8 M pixels, so `decode()` is a SECOND
    implementation of luma() + srgb_to_id() + aggregate(). Until this test existed, the
    only code that ever measured a real render was the one the tests did not cover — the
    tests proved a decoder that never ran. Equivalence proven beats equivalence assumed."""
    np = pytest.importorskip("numpy")
    ids = [1, 7, 40, 200]
    names = {i: f"obj{i}" for i in ids}
    h, w = 24, 40
    mask = np.zeros((h, w, 3), dtype=np.int16)
    beauty = np.zeros((h, w, 3), dtype=np.float32)
    rng = [(0, 6), (6, 14), (14, 20), (20, 24)]
    for (y0, y1), i in zip(rng, ids):
        mask[y0:y1, :, :] = np.array(vp.id_to_srgb(i), dtype=np.int16)
        for y in range(y0, y1):                       # a spread, so the median is a choice
            beauty[y, :, :] = 30 + 7 * i + (y - y0) * 3
    fast = {r["name"]: r for r in vp.decode(beauty, mask, names, min_px=1)}
    pure = {r["name"]: r for r in vp.aggregate(
        ((vp.srgb_to_id(tuple(mask[y, x])), vp.luma(tuple(beauty[y, x])))
         for y in range(h) for x in range(w)),
        names, total_px=h * w, min_px=1)}
    assert set(fast) == set(pure)
    for k in fast:
        assert fast[k]["px"] == pure[k]["px"], k
        assert fast[k]["value"] == pytest.approx(pure[k]["value"], abs=1e-4), k
        assert fast[k]["share"] == pytest.approx(pure[k]["share"]), k


def test_the_numpy_decoder_honours_the_sliver_floor_like_aggregate_does():
    np = pytest.importorskip("numpy")
    names = {3: "sliver"}
    mask = np.zeros((10, 10, 3), dtype=np.int16)
    mask[:2, :5] = np.array(vp.id_to_srgb(3), dtype=np.int16)
    beauty = np.full((10, 10, 3), 180.0, dtype=np.float32)
    rows = vp.decode(beauty, mask, names, min_px=vp.MIN_PIXELS)
    assert rows[0]["px"] == 10 and rows[0]["value"] is None
