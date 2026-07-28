"""R5 playblast-ladder armour (quicklook.py + its build_room consumption).

Why these pins exist: R5's whole value is that the cheap rung is (a) actually
cheap, (b) never overwrites the deliverable pair, and (c) actually WIRED — a
design decision must never be revertible by an omission, and a ladder rung that
build_room stopped consuming would revert R5 with every test green.
"""
import pathlib

import quicklook

SRC = (pathlib.Path(__file__).parent / "build_room.py").read_text(encoding="utf-8")


# ---- the rung is strictly cheaper ------------------------------------------------

def test_quick_is_strictly_cheaper_on_the_deliverable_pair():
    for samples, res in ((256, (2000, 1400)), (400, (2400, 1500)), (128, (1600, 1000))):
        qs, (qw, qh) = quicklook.quick_params(samples, res)
        assert qs < samples
        assert qw * qh <= res[0] * res[1] * 0.3   # ≤ ~1/4 the pixels (0.5 per axis)


def test_quick_never_exceeds_a_deliverable_already_cheaper_than_the_rung():
    # a hypothetical 16-sample deliverable must not be made MORE expensive
    qs, _ = quicklook.quick_params(16, (400, 300))
    assert qs == 16


def test_quick_never_returns_a_degenerate_frame():
    _, (w, h) = quicklook.quick_params(48, (20, 20))
    assert w >= 16 and h >= 16


# ---- the rung is wired (anti-omission armour, source-slice style) ----------------

def test_build_room_parses_the_quick_flag_and_forces_a_render():
    main = SRC.split('if __name__ == "__main__"', 1)[1]
    flag = main.split('"--quick"', 1)[1].split('if "--hero"', 1)[0]
    assert '_spec["_quick"] = True' in flag
    assert '_spec["render"] = True' in flag       # a quick-look that renders nothing is a no-op


def test_suite_path_applies_the_rung_and_renames_the_output():
    # slice: from the deliverable sample choice to the render call in build_suite.
    # The READER-side gate is pinned too (mutant-proven at review 2026-07-28:
    # renaming spec.get("_quick") left every pin green while --quick silently
    # became a full-price render OVERWRITING the deliverable pair).
    suite = SRC.split("_samples = 400 if hero else 256", 1)[1].split("render(name, samples=_samples", 1)[0]
    assert 'if spec.get("_quick"):' in suite                 # reader key == writer key
    assert "quicklook.quick_params(_samples, _res)" in suite
    assert 'name += "_" + quicklook.QUICK_SUFFIX' in suite   # never overwrite the deliverable pair


def test_reserved_ql_suffix_is_refused_before_build():
    # review 2026-07-28: `--suffix=ql --render` at full fidelity would write the
    # SAME output name as `--quick` — the one collision the _ql scheme promises
    # cannot happen. The refusal must sit in main AFTER the eyecam suffix merge.
    main = SRC.split('if __name__ == "__main__"', 1)[1]
    guard = main.split("_sfx_final", 1)[1]
    assert "quicklook.QUICK_SUFFIX" in guard
    assert "os._exit(1)" in guard.split("try:", 1)[0]         # hard exit, headless-safe


def test_rect_path_applies_the_rung_to_both_save_and_render():
    rect = SRC.split('name = r.get("type", "room")', 1)[1].split("built '", 1)[0]
    assert 'if spec.get("_quick"):' in rect                  # reader key == writer key
    assert "quicklook.quick_params(_qs, _qr)" in rect
    assert "save(name, samples=_qs, res=_qr)" in rect
    assert "render(name, samples=_qs, res=_qr)" in rect      # render must consume the SAME rung
