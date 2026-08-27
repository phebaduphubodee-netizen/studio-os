"""P2r-27 / D-156 — casework contents-light: the pure half, pinned.

The law under test (friend-pool, 50 delivered frames, 2026-08-26): LIGHT EXISTS
ONLY WHERE CONTENTS ARE. Strips derive from the occupied cell's own geometry —
never typed (R9); a CCT outside the residential warm family RAISES (PH-03); a
cell too small for the hardware is SKIPPED AND DISCLOSED, never silently capped."""
import pytest

import element5_lighting as e5


def _spec(cct=2700, **kw):
    cw = {"strip_w_mm": 10, "strip_h_mm": 4, "watts_per_m": 8, "cct_k": cct,
          "inset_mm": 40, "front_frac": 0.33}
    cw.update(kw)
    return {"lighting": {"schema": e5.SCHEMA, "casework": cw}}


def _cell(name="c0", x=2.353, y=2.8, z_top=0.438, ceil_z=2.482,
          dx=1.06, dy=0.6, axis="y", sign=-1):
    return {"name": name, "x": x, "y": y, "z_top": z_top, "ceil_z": ceil_z,
            "dx": dx, "dy": dy, "axis": axis, "sign": sign}


def test_one_strip_per_occupied_cell_and_none_elsewhere():
    strips, meta = e5.casework_strips(_spec(), [_cell(), _cell(name="c1", x=3.5)])
    assert len(strips) == 2 and meta["declared"] and meta["skipped"] == []
    # empty-cell darkness is the caller's side of the law: no cell in -> no strip out
    assert e5.casework_strips(_spec(), [])[0] == []


def test_strip_derives_inside_its_cell():
    c = _cell()
    (s,), _ = e5.casework_strips(_spec(), [c])
    assert c["x"] <= s["x"] and s["x"] + s["dx"] <= c["x"] + c["dx"] + 1e-9
    assert c["y"] <= s["y"] and s["y"] + s["dy"] <= c["y"] + c["dy"] + 1e-9
    # mounted under the cell ceiling, thickness = strip_h
    assert abs((s["z"] + s["dz"]) - c["ceil_z"]) < 1e-9 and abs(s["dz"] - 0.004) < 1e-9
    # run inset per side (axis 'y' = depth -> run is x): length = dx - 2*inset
    assert abs(s["dx"] - (c["dx"] - 0.08)) < 1e-9
    # watts derive from length, never a typed constant
    assert abs(s["watts"] - round(8 * s["dx"], 2)) < 1e-6


def test_front_frac_respects_sign():
    lo = e5.casework_strips(_spec(), [_cell(sign=-1)])[0][0]
    hi = e5.casework_strips(_spec(), [_cell(sign=+1)])[0][0]
    # front at the LOW end (sign -1) -> strip nearer the low y edge than sign +1's
    assert lo["y"] < hi["y"]


def test_cct_outside_family_raises():
    with pytest.raises(ValueError):
        e5.casework_strips(_spec(cct=4000), [_cell()])


def test_unknown_key_raises():
    with pytest.raises(ValueError):
        e5.casework_strips(_spec(nudge_mm=5), [_cell()])


def test_too_small_cell_skipped_and_disclosed():
    tiny = _cell(name="tiny", dx=0.05)
    strips, meta = e5.casework_strips(_spec(), [tiny, _cell()])
    assert len(strips) == 1
    assert [s["cell"] for s in meta["skipped"]] == ["tiny"]


def test_absent_block_is_optout_not_error():
    strips, meta = e5.casework_strips({"lighting": {"schema": e5.SCHEMA}}, [_cell()])
    assert strips == [] and meta["declared"] is False
