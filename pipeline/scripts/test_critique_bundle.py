"""Tests for critique_bundle.py — the R7b designer-critique paste bundle.

The one thing worth pinning here is the REFUSAL. A bundle is a thing that leaves
the machine, so the allowlist is a privacy boundary, not a convenience: the
target image and the anchor pool are another studio's delivered client work, and
sending them would both leak a client and show the judge the answer.
"""
import os

import pytest

import critique_bundle as CB


@pytest.fixture
def png(tmp_path):
    p = tmp_path / "trn001_blockout_r20.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    return str(p)


def test_our_own_render_is_sendable(png):
    assert CB.check_sendable(png) == png


@pytest.mark.parametrize("name", [
    "reproduction/TRN-001/target_of_record.png",
    "benchmark/look-bench/blind_trn001_r20_s0.png",
    "benchmark/anchors/delivered_0042.png",
    "clients/somebody/plan.png",
    "qa/golden-set/room_01.png",
])
def test_the_benchmark_and_client_work_are_refused(tmp_path, name):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    with pytest.raises(CB.RefusedError):
        CB.check_sendable(str(p))


def test_a_windows_separator_cannot_slip_a_refused_path_through(tmp_path):
    """The check normalises separators before matching — a path written with
    backslashes must refuse exactly like its POSIX twin."""
    p = tmp_path / "clients" / "x.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    with pytest.raises(CB.RefusedError):
        CB.check_sendable(str(p).replace("/", "\\"))


def test_a_non_image_is_refused_so_a_spec_or_a_note_cannot_ride_along(tmp_path):
    p = tmp_path / "spec.json"
    p.write_text("{}")
    with pytest.raises(CB.RefusedError, match="not an image"):
        CB.check_sendable(str(p))


def test_the_bundle_carries_the_render_the_prompt_and_instructions(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    got = sorted(os.listdir(d))
    assert got == ["PROMPT.md", "README.md", "trn001_blockout_r20.png"]


def test_the_prompt_goes_out_unedited(png, tmp_path):
    """ONE version of the critic prompt, edits via PR only — a bundle that
    rewrites it per round is a judge tuned by the builder."""
    d = CB.build(png, str(tmp_path / "out"))
    with open(os.path.join(d, "PROMPT.md"), encoding="utf-8") as a, \
            open(CB.PROMPT, encoding="utf-8") as b:
        assert a.read() == b.read()


def test_the_readme_names_the_render_and_the_refusal(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    txt = open(os.path.join(d, "README.md"), encoding="utf-8").read()
    assert "trn001_blockout_r20.png" in txt
    assert "target" in txt and "anchor" in txt


def test_building_twice_is_idempotent_rather_than_an_error(png, tmp_path):
    out = str(tmp_path / "out")
    assert CB.build(png, out) == CB.build(png, out)
