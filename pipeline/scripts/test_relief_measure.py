#!/usr/bin/env python3
"""Tests for relief_measure.py, and for the sidecar-preservation guard it depends on.

WHAT THESE PIN, and it is the reason the file exists: the numbers in a `relief` block
must be RE-DERIVABLE from the texture files, and they must survive a `--backfill` of
the same sidecar. Both were false on 2026-08-29 — the block was hand-written prose and
`texture_scale.write_sidecar` rebuilt the dict from six keys, so one backfill would
have deleted it and returned the millwork to a flat map with nothing printed.
"""
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relief_measure as RM                                  # noqa: E402
import texture_scale as TS                                   # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _has(slug):
    return os.path.isdir(os.path.join(RM.TEX_ROOT, slug))


# ------------------------------------------------- the numbers must re-derive

@pytest.mark.parametrize("slug", ["oak_veneer_01", "plastered_wall_03"])
def test_every_stored_figure_reproduces_from_the_texture_files(slug):
    """THE WHOLE POINT. If this fails, either a texture changed or the method did —
    both are things a reader of the sidecar must be told about, and neither should be
    discoverable only by a frame looking wrong."""
    if not _has(slug):
        pytest.skip(f"{slug} not cached on this machine")
    p = os.path.join(RM.TEX_ROOT, slug, f"{slug}.scale.json")
    stored = json.load(open(p, encoding="utf-8")).get("relief")
    assert stored, f"{slug} carries no relief block"
    fresh = RM.measure(slug)
    for k, v in fresh.items():
        if isinstance(v, bool) or v is None:
            assert stored.get(k) == v, f"{slug}.{k}"
        else:
            assert abs(float(stored[k]) - v) <= RM.REPRO_TOL * max(abs(v), 1e-9), \
                f"{slug}.{k}: stored {stored[k]} vs measured {v}"


def test_the_two_live_slugs_both_REFUSE_their_displacement_map():
    """The refusal is a measurement, not a preference — and it is the finding that
    started this: a Bump driven off a map with this little spread delivers nothing."""
    for slug in ("oak_veneer_01", "plastered_wall_03"):
        if not _has(slug):
            pytest.skip(f"{slug} not cached")
        m = RM.measure(slug)
        assert m["displacement_map_usable_as_height"] is False
        assert m["displacement_map_std_8bit"] < RM.DISP_STD_MIN


def test_each_slug_carries_its_OWN_numbers_not_a_neighbours():
    """The first hand-written pair had plastered_wall_03's `method` copied verbatim
    from oak_veneer_01's, citing oak's std and oak's vendor slope on a plaster surface.
    Two slugs measuring the same is the tell."""
    if not (_has("oak_veneer_01") and _has("plastered_wall_03")):
        pytest.skip("both slugs needed")
    a, b = RM.measure("oak_veneer_01"), RM.measure("plastered_wall_03")
    assert a["vendor_mean_slope_deg"] != b["vendor_mean_slope_deg"]
    assert a["diffuse_mean_grad_per_m"] != b["diffuse_mean_grad_per_m"]
    assert a["bump_distance_m_from_diffuse"] != b["bump_distance_m_from_diffuse"]


def test_the_gradient_baseline_is_recorded_because_the_number_depends_on_it():
    """A mean image gradient is not scale-invariant, so a distance solved from one is
    only valid at the baseline it was differenced over. Storing the number without the
    baseline is what let it be described as reproducing the vendor slope full stop."""
    if not _has("oak_veneer_01"):
        pytest.skip("oak_veneer_01 not cached")
    m = RM.measure("oak_veneer_01")
    assert m["gradient_baseline_mm"] > 0
    # and the sRGB/linear gap is carried too, because the shader reads the linear one
    assert m["gradient_linear_per_m"] != m["diffuse_mean_grad_per_m"]


# --------------------------------------------- the block must survive a backfill

def test_write_sidecar_preserves_a_relief_block(tmp_path):
    """THE LANDMINE. `--backfill` re-derives six publisher fields; it does not own the
    file. Before this guard, one backfill silently deleted the relief block and the
    millwork went flat with nothing failing."""
    root = str(tmp_path)
    d = pathlib.Path(TS.texture_dir("slug_x", root))
    d.mkdir(parents=True)
    (d / "slug_x.scale.json").write_text(json.dumps({
        "slug": "slug_x", "dimensions_mm": [1000.0, 1000.0], "tile_m": 1.0,
        "aspect": 1.0, "source": "old", "note": "old",
        "relief": {"bump_distance_m_from_diffuse": 0.00123, "measured": "2026-08-29"},
    }), encoding="utf-8")
    TS.write_sidecar("slug_x", [2000.0, 2000.0], "new-source", root=root)
    back = json.load(open(d / "slug_x.scale.json", encoding="utf-8"))
    assert back["tile_m"] == 2.0 and back["source"] == "new-source"   # it did its job
    assert back["relief"]["bump_distance_m_from_diffuse"] == 0.00123  # and kept ours


def test_write_sidecar_still_works_with_no_previous_file(tmp_path):
    root = str(tmp_path)
    pathlib.Path(TS.texture_dir("slug_y", root)).mkdir(parents=True)
    rep = TS.write_sidecar("slug_y", [500.0, 500.0], "src", root=root)
    assert rep["tile_m"] == 0.5 and "relief" not in rep
