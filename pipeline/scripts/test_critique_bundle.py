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
    assert got == ["PROMPT.md", "README.md", CB.C2_ASK, "trn001_blockout_r20.png"]


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


# --- R7c: the C2 ask is blind BY CONSTRUCTION ---------------------------------
# r35 fired C2 and C3 in parallel into one directory, so C3's answer sat in the
# folder the C2 agent had been pointed at. Nothing is known to be contaminated —
# the agent said it never opened the file — and that is the failure: R7c chose
# architecture over discipline on purpose when it retired the Cowork rung.

def test_the_bundle_ships_a_blind_c2_ask_dir(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    ask = os.path.join(d, CB.C2_ASK)
    assert sorted(os.listdir(ask)) == ["PROMPT.md", "README.md",
                                       "trn001_blockout_r20.png"]
    assert CB.assert_blind(ask) == ask


def test_the_ask_dir_holds_the_same_prompt_the_bundle_does(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    a = open(os.path.join(d, "PROMPT.md"), encoding="utf-8").read()
    b = open(os.path.join(d, CB.C2_ASK, "PROMPT.md"), encoding="utf-8").read()
    assert a == b


def test_another_critics_answer_in_the_ask_dir_is_refused(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    ask = os.path.join(d, CB.C2_ASK)
    with open(os.path.join(ask, "ANSWER_gemini25pro.md"), "w") as f:
        f.write("5 items")
    with pytest.raises(CB.RefusedError) as e:
        CB.assert_blind(ask)
    assert "ANSWER_gemini25pro.md" in str(e.value)


def test_rebuilding_the_ask_dir_sweeps_out_what_appeared_in_it(png, tmp_path):
    """A dir that merely STARTED blind is the discipline story again."""
    d = CB.build(png, str(tmp_path / "out"))
    ask = os.path.join(d, CB.C2_ASK)
    with open(os.path.join(ask, "ANSWER_claude-local-c2.md"), "w") as f:
        f.write("21 items")
    os.makedirs(os.path.join(ask, "stray"), exist_ok=True)
    CB.c2_ask_dir(d, "trn001_blockout_r20.png")
    assert sorted(os.listdir(ask)) == ["PROMPT.md", "README.md",
                                       "trn001_blockout_r20.png"]


def test_the_ask_dir_readme_says_where_to_point_the_agent(png, tmp_path):
    d = CB.build(png, str(tmp_path / "out"))
    txt = open(os.path.join(d, CB.C2_ASK, "README.md"), encoding="utf-8").read()
    assert "bundle root" in txt and "R7c" in txt


def test_a_bundle_with_two_renders_will_not_guess_which_one_to_ask_about(tmp_path):
    d = tmp_path / "critique-x"
    d.mkdir()
    for n in ("a.png", "b.png"):
        (d / n).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    (d / "PROMPT.md").write_text("judge this", encoding="utf-8")
    with pytest.raises(CB.RefusedError):
        CB.c2_ask_dir(str(d))
