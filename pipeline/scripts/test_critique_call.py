"""Tests for critique_call's mode declaration — R7b's bundle, honest about itself.

WHY: r34's C3 turn was spent on the playblast. A 540x410 frame (R5 `--quick`:
half res per axis, 64 samples) went to Gemini with no note saying so, and its
number-one item — its "fix only this" item — was that the picture is blurry and
looks unfinished. Correct about the image, useless about the work: measured at
the size a viewer sees, that frame carries 0.17x the high-frequency energy of
this lane's full frames. R7b fires C3 on every render and R5 puts the quick
frame first, so without a declaration that top slot was going to be wasted on
sampling forever.

The second test is the one that matters. The first version of `declare_mode`
globbed a single directory level, found no peer frames, and announced a
540x410 playblast as "full-fidelity" — the exact lie the function exists to
prevent, on its first run.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import critique_call as CC  # noqa: E402


def _png(path, w, h):
    """A valid IHDR is all `png_size` reads; the pixel data is never decoded."""
    import struct
    import zlib
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    chunk = (struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr
             + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk)
    return path


def _lane(tmp_path, quick_wh, full_wh):
    renders = tmp_path / "renders"
    bundle = renders / "critique" / "critique-x_quick"
    bundle.mkdir(parents=True)
    _png(renders / "full_a.png", *full_wh)
    return _png(bundle / "x_quick.png", *quick_wh)


def test_a_playblast_is_declared_as_one(tmp_path):
    r = _lane(tmp_path, (540, 410), (1080, 821))
    out = CC.declare_mode(r)
    assert "PLAYBLAST" in out
    assert "540x410" in out and "1080x821" in out


def test_the_peer_search_reaches_the_renders_dir_two_levels_up(tmp_path):
    # THE REGRESSION. A one-level glob finds nothing, and "no peers" silently
    # means "this is the biggest frame there is", i.e. full-fidelity.
    r = _lane(tmp_path, (540, 410), (1080, 821))
    assert "full-fidelity" not in CC.declare_mode(r)


def test_a_full_frame_is_declared_judgeable_on_every_axis(tmp_path):
    r = _lane(tmp_path, (1080, 821), (1080, 821))
    out = CC.declare_mode(r)
    assert "full-fidelity" in out and "PLAYBLAST" not in out


def test_the_playblast_note_names_what_the_judge_SHOULD_answer(tmp_path):
    # A "do not comment on X" with no "do comment on Y" spends the slot anyway.
    out = CC.declare_mode(_lane(tmp_path, (540, 410), (1080, 821)))
    for asked in ("สัดส่วน", "ตำแหน่ง", "องค์ประกอบ"):
        assert asked in out


def test_a_non_png_declares_nothing_rather_than_guessing(tmp_path):
    p = tmp_path / "not.png"
    p.write_bytes(b"nope")
    assert CC.declare_mode(p) == ""


def test_the_declaration_is_prepended_so_it_cannot_be_buried(tmp_path):
    r = _lane(tmp_path, (540, 410), (1080, 821))
    assert CC.declare_mode(r).startswith("**MODE:")


def test_the_real_r34_bundle_reads_as_a_playblast():
    repo = Path(CC.REPO)
    r = (repo / "_private/benchmark/reproduction/TRN-002/renders/critique"
         / "critique-trn002_mat_r34_quick" / "trn002_mat_r34_quick.png")
    if not r.exists():
        return  # private tree absent (fresh clone) — the synthetic cases cover it
    assert "PLAYBLAST" in CC.declare_mode(r)
