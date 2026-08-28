"""Tests for watch_local.py — the fail-closed door between our own video and a
transcription API.

THE ONE THING THESE TESTS EXIST FOR. The protection must not be a flag anyone types. So
every test below asks the same question from a different side: can a path that is OURS
reach a command line that lacks `--no-whisper`? The answer has to be no, including when
the caller actively asks for it.
"""
import os

import pytest

import watch_local as WL


REPO = os.path.abspath("/repo")


def _exists(known):
    return lambda p: os.path.abspath(p) in {os.path.abspath(k) for k in known}


# ------------------------------------------------------------------- classify

def test_a_url_is_public():
    assert WL.classify("https://www.youtube.com/watch?v=abc") == "url"
    assert WL.classify("http://example.com/a.mp4") == "url"


def test_a_file_inside_the_repo_is_ours():
    p = os.path.join(REPO, "projects", "PRJ", "turntable.mp4")
    assert WL.classify(p, repo=REPO, exists=_exists([p])) == "ours"


def test_any_path_under_the_repo_is_ours_even_a_directory_nobody_listed():
    # The named roots are a floor, not a fence: a directory invented tomorrow is covered
    # the day it exists, not the day someone remembers to add it (R9b's law).
    p = os.path.join(REPO, "some_new_dir", "clip.mov")
    assert WL.classify(p, repo=REPO, exists=_exists([p])) == "ours"


def test_a_file_outside_the_repo_is_foreign_not_public():
    p = os.path.abspath("/elsewhere/holiday.mp4")
    assert WL.classify(p, repo=REPO, exists=_exists([p])) == "foreign"


def test_a_path_that_does_not_exist_is_refused_never_treated_as_a_url():
    # THE CENTRAL REFUSAL. A typo must not fall through to "assume it is a URL".
    with pytest.raises(WL.RefusedError):
        WL.classify("/repo/projects/typo.mp4", repo=REPO, exists=_exists([]))


def test_an_empty_source_is_refused():
    with pytest.raises(WL.RefusedError):
        WL.classify("   ")


# ------------------------------------------------------------------- audit

def test_audit_explains_itself_for_every_class(monkeypatch):
    monkeypatch.setattr(WL, "classify", lambda s, repo=None: "ours")
    kind, why = WL.audit("x")
    assert kind == "ours" and "no audio leaves this machine" in why


def test_a_foreign_file_is_also_not_ours_to_send(monkeypatch):
    monkeypatch.setattr(WL, "classify", lambda s, repo=None: "foreign")
    _kind, why = WL.audit("x")
    assert "REFUSED" in why


# ------------------------------------------------------------------- build_argv

def test_our_media_gets_no_whisper_injected(monkeypatch):
    monkeypatch.setattr(WL, "audit", lambda s, repo=None: ("ours", "because"))
    argv = WL.build_argv("/repo/projects/a.mp4", ["--detail", "balanced"],
                         skill_dir="/S", python="py")
    assert argv[-1] == "--no-whisper"
    assert argv[:3] == ["py", os.path.join("/S", "scripts", "watch.py"),
                        "/repo/projects/a.mp4"]


def test_a_public_url_is_left_alone(monkeypatch):
    monkeypatch.setattr(WL, "audit", lambda s, repo=None: ("url", "because"))
    argv = WL.build_argv("https://y/w", [], skill_dir="/S", python="py")
    assert "--no-whisper" not in argv


def test_an_explicit_whisper_override_is_refused_by_name():
    # A flag that is silently ignored teaches the next caller that it works. Refuse loudly.
    with pytest.raises(WL.RefusedError):
        WL.build_argv("/repo/a.mp4", ["--whisper", "groq"], skill_dir="/S")
    with pytest.raises(WL.RefusedError):
        WL.build_argv("/repo/a.mp4", ["--whisper=openai"], skill_dir="/S")


def test_no_whisper_is_not_appended_twice(monkeypatch):
    monkeypatch.setattr(WL, "audit", lambda s, repo=None: ("ours", "because"))
    argv = WL.build_argv("/repo/a.mp4", ["--no-whisper"], skill_dir="/S", python="py")
    assert argv.count("--no-whisper") == 1


def test_a_foreign_file_is_protected_the_same_way(monkeypatch):
    monkeypatch.setattr(WL, "audit", lambda s, repo=None: ("foreign", "because"))
    argv = WL.build_argv("/elsewhere/a.mp4", [], skill_dir="/S", python="py")
    assert "--no-whisper" in argv


# ------------------------------------------------------------------- resolve_skill_dir

def test_a_missing_skill_is_a_hard_stop_not_a_warning():
    with pytest.raises(WL.RefusedError):
        WL.resolve_skill_dir(env={}, exists=lambda p: False)


def test_the_env_override_is_honoured():
    got = WL.resolve_skill_dir(env={WL.SKILL_DIR_ENV: "/custom"},
                               exists=lambda p: p == os.path.join("/custom", "scripts",
                                                                  "watch.py"))
    assert got == "/custom"
