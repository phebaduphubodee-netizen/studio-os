"""Tests for glance.py's pure logic (parsing, selection, watch protocol).
No bpy anywhere: glance imports bpy only inside its in-Blender functions."""

import os

import pytest

import glance


# ------------------------------------------------------------------ parse_args

def test_defaults():
    cfg = glance.parse_args(["scene.blend"])
    assert cfg["blend"] == "scene.blend"
    assert cfg["mode"] == glance.DEFAULT_MODE
    assert cfg["scale"] == glance.DEFAULT_SCALE
    assert not cfg["watch"] and not cfg["snap"] and not cfg["stop"]


def test_mode_scale_out_cam():
    cfg = glance.parse_args(["s.blend", "--mode=workbench", "--scale=25",
                             "--out=x.png", "--cam=EyeCam"])
    assert (cfg["mode"], cfg["scale"], cfg["out"], cfg["cam"]) == \
        ("workbench", 25, "x.png", "EyeCam")


def test_unknown_mode_refused():
    with pytest.raises(SystemExit, match="unknown"):
        glance.parse_args(["s.blend", "--mode=cycles"])


@pytest.mark.parametrize("s", ["0", "101", "-5"])
def test_scale_out_of_range_refused(s):
    with pytest.raises(SystemExit, match="out of range"):
        glance.parse_args(["s.blend", f"--scale={s}"])


def test_scale_non_integer_refused():
    with pytest.raises(SystemExit, match="integer"):
        glance.parse_args(["s.blend", "--scale=half"])


def test_unknown_flag_refused_loudly():
    with pytest.raises(SystemExit, match="unknown flag"):
        glance.parse_args(["s.blend", "--quick"])


def test_two_positionals_refused():
    with pytest.raises(SystemExit, match="one .blend"):
        glance.parse_args(["a.blend", "b.blend"])


def test_watch_and_snap_conflict():
    with pytest.raises(SystemExit, match="pick one"):
        glance.parse_args(["s.blend", "--watch", "--snap"])


def test_blend_required_for_driver():
    with pytest.raises(SystemExit, match="need a .blend"):
        glance.parse_args(["--mode=eevee"])


def test_blend_not_required_in_blender():
    cfg = glance.parse_args(["--_inblender", "--mode=eevee"])
    assert cfg["inblender"] and cfg["blend"] is None


# ---------------------------------------------------------------- latest_blend

def test_latest_blend_picks_newest_and_skips_backups():
    entries = [("old.blend", 1.0), ("new.blend", 9.0),
               ("newest.blend1", 99.0),      # Blender backup, never a glance target
               ("note.txt", 100.0)]
    assert glance.latest_blend(entries) == "new.blend"


def test_latest_blend_empty():
    assert glance.latest_blend([("a.txt", 1.0)]) is None
    assert glance.latest_blend([]) is None


# ------------------------------------------------------- naming + engine choice

def test_default_out_names_mode():
    out = glance.default_out(os.path.join("d", "room_x.blend"), "eevee")
    assert out == os.path.join("d", "room_x_glance_eevee.png")


def test_engine_candidates():
    assert glance.engine_candidates("workbench") == ("BLENDER_WORKBENCH",)
    assert glance.engine_candidates("eevee")[0] == "BLENDER_EEVEE_NEXT"
    assert "BLENDER_EEVEE" in glance.engine_candidates("eevee")


# ------------------------------------------------------------- watch protocol

def test_request_roundtrip():
    txt = glance.make_request(7, "eevee", 50, "o.png", cam="Cam")
    req = glance.parse_request(txt)
    assert (req["seq"], req["mode"], req["scale"], req["out"], req["cam"],
            req["stop"]) == (7, "eevee", 50, "o.png", "Cam", False)


def test_request_stop():
    assert glance.parse_request(glance.make_request(1, "eevee", 50, None,
                                                    stop=True))["stop"] is True


def test_parse_request_refuses_junk():
    with pytest.raises(ValueError):
        glance.parse_request("[]")          # json but not a request
    with pytest.raises(ValueError):
        glance.parse_request('{"mode": "eevee"}')   # no seq


def test_ctl_paths_sit_next_to_blend():
    ctl = glance.ctl_paths(os.path.join("out", "room.blend"))
    for k in ("cmd", "done", "alive"):
        assert ctl[k].startswith(os.path.join("out", "room.blend") + ".glance")
    assert len({ctl["cmd"], ctl["done"], ctl["alive"]}) == 3


# ------------------------------------------------------------------ invocation

def test_build_blender_cmd_shape():
    cmd = glance.build_blender_cmd("blender.exe", "s.blend", "glance.py",
                                   ["--mode=eevee", "--watch"])
    assert cmd[:5] == ["blender.exe", "-b", "s.blend", "--python", "glance.py"]
    assert "--factory-startup" not in cmd          # the saved scene IS the point
    assert cmd[5] == "--" and "--_inblender" in cmd
    assert cmd.index("--_inblender") > cmd.index("--")


def test_find_blender_env_first(tmp_path):
    exe = tmp_path / "blender.exe"
    exe.write_text("x")
    got = glance.find_blender(env={"INTERIOR_BLENDER": str(exe)},
                              which=lambda n: "/path/blender",
                              globber=lambda p: [])
    assert got == str(exe)


def test_find_blender_path_then_glob(tmp_path):
    assert glance.find_blender(env={}, which=lambda n: "/path/blender",
                               globber=lambda p: []) == "/path/blender"
    a = tmp_path / "Blender 4.5"
    b = tmp_path / "Blender 5.1"
    for d in (a, b):
        d.mkdir()
        (d / "blender.exe").write_text("x")
    got = glance.find_blender(env={}, which=lambda n: None,
                              globber=lambda p: [str(a / "blender.exe"),
                                                 str(b / "blender.exe")])
    assert got == str(b / "blender.exe")            # newest install wins


def test_find_blender_none():
    assert glance.find_blender(env={}, which=lambda n: None,
                               globber=lambda p: []) is None
