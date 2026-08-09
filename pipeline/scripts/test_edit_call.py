#!/usr/bin/env python3
"""Tests for edit_call.py — the only thing in this repo that sends a frame OUT to an image
model and takes one back.

Nothing here talks to the network. What is pinned is the two things that are true before
any byte leaves and after any byte returns:
  - the egress refusal (the same pattern critique_call.py enforces, not a second copy),
  - the crop invariant: ONE slice cuts the beauty frame and its id mask, or every number
    downstream is measured through a mask that names other pixels.
"""
import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import critique_call
import edit_call as ec
import value_probe as vp


def test_the_forbidden_pattern_is_critique_calls_own_not_a_second_copy():
    """Two copies of 'what may not travel' drift apart, and the day they do is the day one
    of them is wrong about a client path."""
    assert ec.FORBIDDEN is critique_call.FORBIDDEN


@pytest.mark.parametrize("bad", ["look at target.jpg", "compare with the anchor pool",
                                 "see clients/somebody/plan.pdf"])
def test_a_prompt_naming_forbidden_material_is_refused_before_anything_is_sent(tmp_path, bad):
    p = tmp_path / "p.md"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        ec.main([str(tmp_path / "nope.png"), "T", "--prompt-file", str(p)])
    assert "refusing to send" in str(e.value)


def test_the_refusal_happens_before_the_render_is_even_opened(tmp_path):
    """Ordering is the point: a prompt that must not go out must not go out even when the
    render path is nonsense, so the check cannot be reached only on the happy path."""
    p = tmp_path / "p.md"
    p.write_text("target.png", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        ec.main([str(tmp_path / "does_not_exist.png"), "T", "--prompt-file", str(p)])
    assert "refusing to send" in str(e.value)          # not "missing …"


@pytest.mark.parametrize("size,ratio,want", [
    ((1080, 821), (4, 3), (1080, 810)),                # this lane's real frame
    ((1000, 1000), (4, 3), (1000, 750)),
    ((900, 300), (1, 1), (300, 300)),
    ((640, 480), (4, 3), (640, 480)),                  # already exact: untouched
])
def test_crop_to_aspect_lands_on_the_ratio_without_resampling(size, ratio, want):
    im = Image.new("RGB", size, (7, 11, 13))
    out = ec.crop_to_aspect(im, ratio)
    assert out.size == want
    assert abs(out.size[0] / out.size[1] - ratio[0] / ratio[1]) < 1e-9


def test_the_crop_preserves_palette_ids_exactly():
    """A mask that is RESAMPLED stops being a mask — blended ids belong to no object. The
    crop must move pixels, never mix them."""
    m = np.zeros((821, 1080, 3), dtype=np.uint8)
    m[300:500, 200:700] = vp.id_to_srgb(42)
    out = np.asarray(ec.crop_to_aspect(Image.fromarray(m), (4, 3)))
    ids = vp.decode_ids(out.astype(np.int16))
    assert set(np.unique(ids)) == {0, 42}


def _lane(tmp_path):
    """A minimal render + mask + sidecar triple, named the way the lane names them."""
    d = tmp_path / "renders"
    d.mkdir()
    beauty = np.full((821, 1080, 3), 30, dtype=np.uint8)
    beauty[300:500, 200:700] = 220
    mask = np.zeros((821, 1080, 3), dtype=np.uint8)
    mask[300:500, 200:700] = vp.id_to_srgb(1)
    Image.fromarray(beauty).save(d / "r1.png")
    Image.fromarray(mask).save(d / "r1.idmask.png")
    (d / "r1.idmask.json").write_text(
        json.dumps({"source": {"blend": "r1"}, "ids": {"1": "slab"}}), encoding="utf-8")
    return d


def test_prepare_cuts_beauty_and_mask_with_the_same_slice(tmp_path):
    d = _lane(tmp_path)
    b, m, j, size = ec.prepare(str(d / "r1.png"), str(d / "probe"), (4, 3))
    assert size == (1080, 810)
    assert Image.open(b).size == Image.open(m).size == size
    # the STEM survives, so edge_drift's mask/beauty provenance check still bites
    assert os.path.basename(b) == "r1.png" and os.path.basename(m) == "r1.idmask.png"
    assert json.load(open(j))["source"]["blend"] == "r1"


def test_prepare_refuses_when_the_mask_is_missing(tmp_path):
    d = _lane(tmp_path)
    os.remove(d / "r1.idmask.png")
    with pytest.raises(SystemExit) as e:
        ec.prepare(str(d / "r1.png"), str(d / "probe"), (4, 3))
    assert "id_mask" in str(e.value)


def test_a_desynced_crop_raises_rather_than_asserts(tmp_path, monkeypatch):
    """`python -O` strips asserts. The one invariant that makes every downstream number
    mean anything may not be stripped."""
    d = _lane(tmp_path)
    real = ec.crop_to_aspect
    calls = {"n": 0}

    def lopsided(img, ratio):
        calls["n"] += 1
        return real(img, ratio if calls["n"] == 1 else (1, 1))

    monkeypatch.setattr(ec, "crop_to_aspect", lopsided)
    with pytest.raises(ValueError, match="crop desynced"):
        ec.prepare(str(d / "r1.png"), str(d / "probe"), (4, 3))


def _fake_return(monkeypatch, tmp_path, shift):
    """Stand in for the API: hand back the frame we sent, with the slab moved `shift` px.
    No network, but the REAL main() path — prepare, decode, write, guard, exit code."""
    import base64
    import io

    def fake_post(model, key, png_bytes, prompt, aspect, size, timeout=300):
        # Derived from the frame actually SENT (already cropped), never re-painted from
        # the original — re-painting silently re-introduces the crop offset and the test
        # then measures the fixture instead of the guard. shift=0 is byte-identical.
        a = np.asarray(Image.open(io.BytesIO(png_bytes)).convert("RGB"))
        buf = io.BytesIO()
        Image.fromarray(np.roll(a, shift, axis=1)).save(buf, "PNG")
        return {"candidates": [{"content": {"parts": [
            {"inlineData": {"data": base64.b64encode(buf.getvalue()).decode()}}]}}]}

    monkeypatch.setattr(ec, "_post_rest", fake_post)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ec, "REPO", tmp_path)          # usage file stays in the tmp dir
    p = tmp_path / "p.md"
    p.write_text("photoreal, move nothing", encoding="utf-8")
    return str(p)


def test_a_returned_frame_that_moved_our_geometry_makes_the_producer_exit_nonzero(
        tmp_path, monkeypatch, capsys):
    """D-011 in its only enforceable form: the thing that PRODUCES the frame refuses to
    hand it over clean. An instrument nothing calls is a defect this repo has paid for
    once already — so this runs main() for real, not a grep of the source."""
    d = _lane(tmp_path)
    prompt = _fake_return(monkeypatch, tmp_path, shift=60)
    rc = ec.main([str(d / "r1.png"), "moved", "--prompt-file", prompt])
    assert rc == 1
    out = capsys.readouterr().out
    assert "DRIFT" in out and "NOT ADMISSIBLE" in out


def test_a_returned_frame_that_held_exits_zero(tmp_path, monkeypatch, capsys):
    d = _lane(tmp_path)
    prompt = _fake_return(monkeypatch, tmp_path, shift=0)
    assert ec.main([str(d / "r1.png"), "held", "--prompt-file", prompt]) == 0
    assert "NOT ADMISSIBLE" not in capsys.readouterr().out


def test_a_text_only_reply_is_not_read_as_a_clean_frame(tmp_path, monkeypatch, capsys):
    """A refusal is not an image. Returning 0 here would let 'the model declined' read as
    'the geometry held'."""
    d = _lane(tmp_path)
    prompt = _fake_return(monkeypatch, tmp_path, shift=0)
    monkeypatch.setattr(ec, "_post_rest", lambda *a, **k: {
        "candidates": [{"content": {"parts": [{"text": "I cannot edit this image."}]}}]})
    assert ec.main([str(d / "r1.png"), "refused", "--prompt-file", prompt]) == 1
    assert "NO IMAGE RETURNED" in capsys.readouterr().out
