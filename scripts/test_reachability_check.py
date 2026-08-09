"""Tests for reachability_check — the guard that says an unwired instrument is a defect.

Both directions, because a guard that fires on correct work gets muted and a guard that
fires on nothing is decoration:

  * a NEW unwired script must FAIL (that is the whole product)
  * a script reached only transitively must PASS (or every helper becomes a violation)
  * a `CLI-ONLY:` declaration must discharge it (dwg_ingest, ffe_schedule and upscale are
    tools a human runs, not defects) — and the declaration has to be IN THE FILE, where it
    lands in a diff, never in a list this checker keeps
  * the baseline may shrink and may never grow
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reachability_check as RC  # noqa: E402


# --- the reference walk ------------------------------------------------------

def test_an_import_is_a_reference():
    assert RC.references("import coverage_check as COV", {"coverage_check"}) == {"coverage_check"}
    assert RC.references("from coverage_check import audit", {"coverage_check"}) == {"coverage_check"}


def test_a_command_line_invocation_is_a_reference():
    assert RC.references("python3 scripts/vault_search.py 'q'", {"vault_search"}) == {"vault_search"}


def test_merely_NAMING_a_module_in_prose_is_not_a_reference():
    # This is the exact distinction that matters: before 2026-08-08 coverage_check was
    # named in a manifest docstring and a comment, and run by nobody.
    assert RC.references("see coverage_check for the missing-object half", {"coverage_check"}) == set()
    assert RC.references("`self_audit` auto-discovers it", {"self_audit"}) == set()


# --- the CLI-ONLY escape -----------------------------------------------------

def test_cli_only_is_read_from_the_file_header(tmp_path, monkeypatch):
    d = tmp_path / "scripts"
    d.mkdir()
    (d / "hand_tool.py").write_text('"""A tool.\n\nCLI-ONLY: run by hand during ingest.\n"""\n',
                                    encoding="utf-8")
    (d / "orphan.py").write_text('"""A tool with no declaration."""\n', encoding="utf-8")
    monkeypatch.setattr(RC, "ROOT", str(tmp_path))
    monkeypatch.setattr(RC, "SCRIPT_DIRS", ["scripts"])
    cli = RC.declared_cli_only(RC.modules())
    assert cli == {"hand_tool"}


def test_a_declaration_buried_past_the_header_does_not_count(tmp_path, monkeypatch):
    d = tmp_path / "scripts"
    d.mkdir()
    (d / "sneaky.py").write_text("\n" * 60 + "# CLI-ONLY: too far down to be a header\n",
                                 encoding="utf-8")
    monkeypatch.setattr(RC, "ROOT", str(tmp_path))
    monkeypatch.setattr(RC, "SCRIPT_DIRS", ["scripts"])
    assert RC.declared_cli_only(RC.modules()) == set()


# --- the ratchet -------------------------------------------------------------

def test_a_baseline_that_grew_is_refused():
    v = RC.baseline_ratchet(["a", "b"], {"a", "b"}, previous={"a"})
    assert len(v) == 1 and "GREW by ['b']" in v[0]


def test_a_baseline_that_shrank_is_the_whole_point():
    assert RC.baseline_ratchet(["a"], {"a"}, previous={"a", "b"}) == []


def test_swapping_one_orphan_for_another_still_counts_as_growth():
    v = RC.baseline_ratchet(["a", "c"], {"a", "c"}, previous={"a", "b"})
    assert len(v) == 1 and "'c'" in v[0]


def test_the_baseline_parser_ignores_comments_and_blanks():
    assert RC.read_baseline("# a note\n\nfoo\n  bar  \n") == {"foo", "bar"}


# --- the live tree -----------------------------------------------------------

def test_the_live_tree_has_no_NEW_unreached_instrument():
    # The 55 seeded on 2026-08-08 are declared debt. A 56th is a defect.
    report, violations = RC.audit()
    new = report["new_since_baseline"]
    assert not new, "new unwired instrument(s): %s" % new
    assert not violations, violations


def test_this_checker_is_itself_reached():
    # It is invoked from scripts/test_guards.sh. If that line is ever deleted, this guard
    # would go quiet while still passing -- the mute failure, one level up.
    report, _ = RC.audit()
    assert "reachability_check" not in report["unreached"]


def test_the_headline_numbers_are_still_true():
    # The docstring claims ~143 instruments and 29 unreached-with-tests. If those move a
    # lot, the file is describing a repo that no longer exists.
    report, _ = RC.audit()
    assert report["instruments"] > 100
    assert len(report["unreached_with_tests"]) >= 20, (
        "unreached-with-tests dropped to %d -- if that is real progress, update the "
        "docstring and this pin" % len(report["unreached_with_tests"]))
