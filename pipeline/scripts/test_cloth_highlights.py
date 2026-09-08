"""P2r-5 instrument: the highlight read must be able to CATCH a clipped family
on cloth, must NOT accuse a smooth bright rolloff, and must refuse to judge
what it cannot see (absence != pass, invisibility != clean)."""
import json
import os

import numpy as np
from PIL import Image

import cloth_highlights as CH
import value_probe as vp


def _write_pair(tmp_path, plane_ids, ids, frame_rgb):
    H, W = plane_ids.shape
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for i in np.unique(plane_ids):
        if i == 0:
            continue
        arr[plane_ids == i] = vp.id_to_srgb(int(i))
    render = str(tmp_path / "room_t.png")
    Image.fromarray(frame_rgb).save(render)
    mask = str(tmp_path / "room_t.matmask.png")
    Image.fromarray(arr).save(mask)
    with open(os.path.splitext(mask)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump({"schema": "matmask@1", "source": {},
                   "ids": {str(k): v for k, v in ids.items()},
                   "has_image": {}}, f)
    return render


def test_catches_clipped_family_on_cloth(tmp_path):
    plane = np.ones((50, 50), dtype=int)
    frame = np.full((50, 50, 3), 180, dtype=np.uint8)
    frame[:5, :5] = 255                       # 1% of the cloth clipped
    render = _write_pair(tmp_path, plane, {1: "bed_duvet"}, frame)
    res = CH.stats(render)
    fails, unjudgeable = CH.verdict(res["rows"], ("bed_duvet",))
    assert fails and fails[0][0] == "bed_duvet"
    assert not unjudgeable


def test_does_not_accuse_smooth_bright_rolloff(tmp_path):
    plane = np.ones((50, 50), dtype=int)
    ramp = np.tile(np.linspace(60, 240, 50).astype(np.uint8), (50, 1))
    frame = np.stack([ramp] * 3, axis=2)      # bright but never clipped
    render = _write_pair(tmp_path, plane, {1: "bed_duvet"}, frame)
    fails, unjudgeable = CH.verdict(CH.stats(render)["rows"], ("bed_duvet",))
    assert not fails and not unjudgeable


def test_single_blown_channel_is_caught(tmp_path):
    # peak channel, not luminance: R=255 with G/B dark must still read clipped
    plane = np.ones((50, 50), dtype=int)
    frame = np.full((50, 50, 3), 100, dtype=np.uint8)
    frame[:10, :10, 0] = 255
    render = _write_pair(tmp_path, plane, {1: "bed_duvet"}, frame)
    fails, _ = CH.verdict(CH.stats(render)["rows"], ("bed_duvet",))
    assert fails


def test_non_cloth_clipping_does_not_fail_the_verdict(tmp_path):
    plane = np.ones((50, 50), dtype=int)
    plane[:, 25:] = 2
    frame = np.full((50, 50, 3), 150, dtype=np.uint8)
    frame[:, 25:] = 255                       # the lamp face may clip
    render = _write_pair(tmp_path, plane, {1: "bed_duvet", 2: "lamp_opal"}, frame)
    res = CH.stats(render)
    fails, unjudgeable = CH.verdict(res["rows"], ("bed_duvet",))
    assert not fails and not unjudgeable
    lamp = [r for r in res["rows"] if r["material"] == "lamp_opal"][0]
    assert lamp["clip_share_pct"] > 99.0      # ...but the table still says so


def test_invisible_cloth_is_could_not_judge_never_clean(tmp_path):
    plane = np.ones((20, 20), dtype=int)      # bed_pillow nowhere in frame
    frame = np.full((20, 20, 3), 120, dtype=np.uint8)
    render = _write_pair(tmp_path, plane, {1: "bed_duvet"}, frame)
    fails, unjudgeable = CH.verdict(CH.stats(render)["rows"],
                                    ("bed_duvet", "bed_pillow"))
    assert not fails
    assert unjudgeable == ["bed_pillow"]


def test_missing_mask_is_none_never_a_number(tmp_path):
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    render = str(tmp_path / "room_t.png")
    Image.fromarray(frame).save(render)
    assert CH.stats(render) is None


def test_resolution_mismatch_refuses(tmp_path):
    plane = np.ones((20, 20), dtype=int)
    frame = np.full((20, 20, 3), 120, dtype=np.uint8)
    render = _write_pair(tmp_path, plane, {1: "bed_duvet"}, frame)
    big = np.full((40, 40, 3), 120, dtype=np.uint8)
    Image.fromarray(big).save(render)         # frame no longer matches mask
    res = CH.stats(render)
    assert res is not None and "error" in res
