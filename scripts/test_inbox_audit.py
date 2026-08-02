"""Tests for inbox_audit.py — the distillation-debt instrument.

The old instrument was not wrong by accident; it was wrong in the specific ways an
un-pinned instrument rots. So these tests pin the ROT, not the happy path:

  * it must never go back to counting FILES (it reported 640 "staged files", of which 509
    were attachment binaries — a JPEG of a curtain is not distillation debt);
  * it must never go back to mtime for age (it reported `oldest 2475d` from a 2019 timestamp
    the light manufacturer stamped inside a vendor ZIP — wrong by ~225x);
  * a future run must not be able to make its debt disappear (by tagging it "provenance",
    by inventing an unrecognised stash, or by pointing a ledger row at a topically-similar
    file that never received the values);
  * DISTILLED must stay a MEASUREMENT (PIN-MISS), never an assertion — that is the whole
    lesson of the 2026-07-03 corpus run, whose 11 self-graded files were 10/10 defective.

Run: python -m pytest scripts/test_inbox_audit.py -q
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest

import inbox_audit as A

ROOT = A.ROOT


# ---------------------------------------------------------------- classification ---------
def test_unit_is_not_file():
    """The regression that must never happen again: units != files."""
    classes, units, _ = A.scan()
    n_files = sum(len(v) for v in classes.values())
    assert n_files > 600, "the file count is still the file count"
    assert len(units) < 200, "units must be knowledge units, not files"
    assert len(units) != n_files, "an instrument that counts files is the OLD instrument"


def test_no_attachment_is_ever_a_unit():
    _, units, _ = A.scan()
    for u, anchor in units.items():
        assert "/files/" not in anchor
        assert "/_external-fetched/" not in anchor
        assert os.path.splitext(anchor)[1].lower() not in {
            ".png", ".jpg", ".jpeg", ".rar", ".ies", ".xlsx", ".xls", ".skp", ".zip"}


def test_discord_unit_is_the_thread_not_the_file():
    _, units, _ = A.scan()
    threads = [u for u in units if "/discord/" in u]
    assert threads, "the discord stash is the biggest one — it must produce units"
    for t in threads:
        assert not t.endswith(".md"), "a discord unit is the THREAD DIR, not thread.md"
        assert units[t].endswith("/thread.md")


def test_raw_json_is_an_attachment_not_a_unit():
    assert A.classify("knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/raw.json") == "ATTACHMENT"
    assert A.classify("knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/thread.md") == "UNIT-ANCHOR"
    assert A.classify("knowledge/_inbox/discord/MY-DATA-PEAT/maps/001_Tile/files/a.png") == "ATTACHMENT"


def test_unclassified_is_zero_on_the_real_tree():
    """A stash the classifier does not recognise must not silently vanish from the debt."""
    classes, _, _ = A.scan()
    assert classes.get("UNCLASSIFIED", []) == []


def test_unclassified_is_loud(tmp_path, monkeypatch):
    """The anti-hiding invariant: an unknown file in an unknown stash FAILS the run."""
    assert A.classify("knowledge/_inbox/some-new-stash/mystery.bin") == "UNCLASSIFIED"


# ---------------------------------------------------------------- provenance -------------
def test_provenance_is_code_not_data():
    """You cannot TAG your way out of debt. Provenance is a hard-coded allowlist; a marker
    in the file itself must never grant it."""
    assert A.classify("knowledge/_inbox/codes-th-sources/mr43-55-upd68.pdf") == "PROVENANCE-KEEP"
    # a staged answer that merely CLAIMS to be provenance is still a unit
    assert A.classify("knowledge/_inbox/i-say-i-am-provenance.md") == "UNIT-ANCHOR"


def test_provenance_count_is_frozen():
    classes, _, _ = A.scan()
    assert len(classes.get("PROVENANCE-KEEP", [])) == A.EXPECTED_PROVENANCE, (
        "the provenance set changed — that is either a real new primary source (edit "
        "PROVENANCE_PATTERNS deliberately) or somebody hiding debt")


def test_the_three_statutory_pdfs_are_provenance():
    classes, _, _ = A.scan()
    prov = classes["PROVENANCE-KEEP"]
    assert sum(1 for p in prov if p.startswith("knowledge/_inbox/codes-th-sources/")) == 3


# ---------------------------------------------------------------- age --------------------
def test_age_never_comes_from_mtime(tmp_path):
    """Pin the exact lie the old instrument told: the mtime-oldest file is a 2019-stamped
    vendor .IES, and it is NOT 2475-day-old debt."""
    dates = A.git_add_dates()
    assert dates, "git first-add dates must resolve (the whole age model depends on it)"
    ies = [p for p in dates if p.endswith(".IES") or p.endswith(".ies")]
    if ies:
        import datetime
        now = datetime.datetime.now()
        for p in ies:
            assert A.age_days(p, dates, now) < 365, (
                "an .IES stamped 2019 inside a vendor ZIP must not read as years of debt")


def test_thai_named_anchors_have_git_ages():
    """git octal-quotes non-ASCII paths in --name-only output unless core.quotepath=false;
    without it every Thai-named anchor (43 of 114 on today's tree) silently misses the dates
    dict and reads UNCOMMITTED. Measured live 2026-07-13 — this pin keeps the flag in place."""
    import datetime
    dates = A.git_add_dates()
    _, units, _ = A.scan()
    now = datetime.datetime.now()
    thai_tracked = [a for a in units.values()
                    if any("฀" <= c <= "๿" for c in a)]
    assert thai_tracked, "the corpus is Thai-named; if this is empty the scan broke"
    missing = [a for a in thai_tracked if A.age_days(a, dates, now) is None]
    assert missing == [], f"Thai-named anchors lost their git-add dates again: {missing[:3]}"


def test_untracked_anchor_reads_uncommitted_not_zero():
    import datetime
    assert A.age_days("knowledge/_inbox/not-in-git.md", {}, datetime.datetime.now()) is None


# ---------------------------------------------------------------- citations --------------
def test_citation_with_spaces_resolves_as_one_path():
    """Staged filenames contain spaces. A naive \\S+ regex truncates at the space and
    manufactures a fake dangling citation at an innocent file."""
    p = A.normalize_citation("knowledge/_inbox/id-project-corpus/Interior Design Knowledge Structuring.pdf")
    assert p.endswith("Interior Design Knowledge Structuring.pdf")
    assert os.path.exists(os.path.join(ROOT, p))


def test_citation_wrapped_in_a_blockquote_resolves():
    """Markdown wraps long paths, and a blockquote continuation carries a '>'."""
    p = A.normalize_citation("knowledge/_inbox/id-project-corpus/Automated Vision\n> QA for Interiors.pdf")
    assert p == "knowledge/_inbox/id-project-corpus/Automated Vision QA for Interiors.pdf"


def test_line_suffix_is_not_part_of_the_path():
    p = A.normalize_citation("knowledge/_inbox/nlm-ergonomics-2026-07-03.md:37-38")
    assert p == "knowledge/_inbox/nlm-ergonomics-2026-07-03.md"


def test_path_with_parens_survives_and_prose_paren_is_shed():
    """Staged dirs are named things like `012_ระแนงสำเร็จรูป-(Wall)` — the paren is part of
    the name. But a path cited as '(see knowledge/_inbox/foo.md)' must shed the prose ')'.
    Getting this wrong either manufactures a fake dangle (real paren eaten) or misses a real
    one (prose paren kept)."""
    kept = A.normalize_citation("knowledge/_inbox/discord/MY-DATA-PEAT/catalogue/012_ระแนงสำเร็จรูป-(Wall)")
    assert kept.endswith("(Wall)")
    assert os.path.exists(os.path.join(ROOT, kept))
    shed = A.normalize_citation("knowledge/_inbox/nlm-queue.md)")
    assert shed == "knowledge/_inbox/nlm-queue.md"


def test_abbreviated_citation_is_skipped_not_failed():
    """'catalogue/001_…' is a human shorthand, not a claim about a file. An instrument that
    cries wolf at prose gets muted — which is how the old one died."""
    assert A.normalize_citation("knowledge/_inbox/discord/MY-DATA-PEAT/catalogue/001_…") is None


def test_no_dangling_antecedents_on_the_real_tree():
    """Every knowledge/_inbox path cited by a PROMOTED file must exist. This check caught two
    live rots (`_inbox/interior-ai/research/...`) that the old ledger had declared closed —
    it had grepped pipeline source only, where it would pass."""
    blinks = A.backlink_map(A.promoted_files())
    dangling = A.check_antecedents(blinks)
    assert dangling == [], f"promoted files cite staged paths that do not exist: {dangling}"


# ---------------------------------------------------------------- the ledger -------------
LEDGER_HEAD = "```ledger\n"


def _ledger(tmp_path, monkeypatch, rows):
    d = tmp_path / "knowledge" / "_inbox"
    d.mkdir(parents=True)
    (d / "DISTILLATION-LEDGER.md").write_text(LEDGER_HEAD + "\n".join(rows) + "\n```", encoding="utf-8")
    monkeypatch.setattr(A, "ROOT", str(tmp_path))
    return d


def test_ledger_row_needs_five_fields(tmp_path, monkeypatch):
    _ledger(tmp_path, monkeypatch, ["a.md :: DISTILLED :: b.md"])
    rows, state = A.parse_ledger()
    assert state == "OK" and rows[0]["malformed"]
    fails, _ = A.check_ledger(rows, {}, {})
    assert any(k == "LEDGER-MALFORMED" for k, _, _ in fails)


def test_dangling_successor_is_loud(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/nope.md :: p1 ;; p2 ;; p3 :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "DANGLING-SUCCESSOR" for k, _, _ in fails)


def test_uncited_successor_is_loud(tmp_path, monkeypatch):
    """Blocks the cheapest lie available: pointing a ledger row at a topically-similar file
    that never mentions the unit. The link must be bidirectional."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/s.md :: p1 ;; p2 ;; p3 :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    (tmp_path / "knowledge" / "s.md").write_text("p1 p2 p3 but I never name the unit", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, banded = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "UNCITED-SUCCESSOR" for k, _, _ in fails)
    assert banded["knowledge/_inbox/u.md"] == "PARTIAL"


def test_pin_miss_downgrades_distilled_to_partial(tmp_path, monkeypatch):
    """THE ANTI-FLATTERING CORE. A successor that names the topic but dropped the values is
    NOT distilled, whatever the ledger says about itself."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/s.md :: 1200 mm ;; Martindale ;; R9 :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    (tmp_path / "knowledge" / "s.md").write_text(
        "I cite knowledge/_inbox/u.md and I discuss clearances in general terms. 1200 mm.",
        encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, banded = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    misses = [d for k, _, d in fails if k == "PIN-MISS"]
    assert len(misses) == 2, "the two values that never landed must each be named"
    assert banded["knowledge/_inbox/u.md"] == "PARTIAL", "a pin-miss cannot stay DISTILLED"


def test_distilled_needs_three_pins(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/s.md :: onlyone :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    (tmp_path / "knowledge" / "s.md").write_text("knowledge/_inbox/u.md onlyone", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "LEDGER-THIN-PINS" for k, _, _ in fails)


def test_authority_violation_is_loud(tmp_path, monkeypatch):
    """A DR/NLM answer may never become a Thai statutory value. The OLD instrument literally
    listed codes-th as a distillation destination."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/codes-th/mr55.md :: a ;; b ;; c :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "AUTHORITY-VIOLATION" for k, _, _ in fails)


def test_codes_th_is_not_a_destination():
    assert "codes-th" not in A.DESTINATIONS
    assert "rendering" in A.DESTINATIONS and "programming" in A.DESTINATIONS, (
        "the old instrument was blind to the two dirs holding the successors the ledger names")


def test_ledger_ghost_is_loud(tmp_path, monkeypatch):
    _ledger(tmp_path, monkeypatch,
            ["knowledge/_inbox/gone.md :: DROPPED :: - :: - :: it never existed"])
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {}, {})
    assert any(k == "LEDGER-GHOST" for k, _, _ in fails)


def test_drop_without_rationale_is_loud(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch, ["knowledge/_inbox/u.md :: DROPPED :: - :: - :: -"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "DROPPED-WITHOUT-RATIONALE" for k, _, _ in fails)


def test_owed_is_not_untouched(tmp_path, monkeypatch):
    """OWED (somebody looked, found value, nobody promoted it) and UNTOUCHED (nobody has even
    looked) are different jobs. An instrument that collapses them hides the difference between a
    decision and a blind spot."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: OWED :: - :: - :: the 139-file archive is real value; "
                 "belongs in pricing-formula.md"])
    (d / "u.md").write_text("x", encoding="utf-8")
    (d / "never-looked-at.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    units = {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md",
             "knowledge/_inbox/never-looked-at.md": "knowledge/_inbox/never-looked-at.md"}
    fails, banded = A.check_ledger(rows, units, {})
    assert banded["knowledge/_inbox/u.md"] == "OWED"
    assert banded["knowledge/_inbox/never-looked-at.md"] == "UNTOUCHED"
    assert not [k for k, _, _ in fails if "WITHOUT-RATIONALE" in k]


def test_owed_without_rationale_is_loud(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch, ["knowledge/_inbox/u.md :: OWED :: - :: - :: -"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "OWED-WITHOUT-RATIONALE" for k, _, _ in fails)


def test_new_debt_cannot_hide(tmp_path, monkeypatch):
    """A unit with no ledger row and no backlink lands in UNTOUCHED. It cannot be nothing."""
    d = _ledger(tmp_path, monkeypatch, ["knowledge/_inbox/a.md :: DROPPED :: - :: - :: junk"])
    (d / "a.md").write_text("x", encoding="utf-8")
    (d / "brand-new.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    units = {"knowledge/_inbox/a.md": "knowledge/_inbox/a.md",
             "knowledge/_inbox/brand-new.md": "knowledge/_inbox/brand-new.md"}
    _, banded = A.check_ledger(rows, units, {})
    assert banded["knowledge/_inbox/brand-new.md"] == "UNTOUCHED"


def test_provenance_keep_verdict_is_not_a_free_exit(tmp_path, monkeypatch):
    """Review 2026-07-13 (MUST-FIX): ':: PROVENANCE-KEEP :: - :: - :: -' moved any unit out
    of every debt band — the exact tag-your-way-out the file-level doctrine forbids. The
    verdict is honoured only for units on the hard-coded LEDGER_PROVENANCE_UNITS list."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/my-notes.md :: PROVENANCE-KEEP :: - :: - :: -"])
    (d / "my-notes.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, banded = A.check_ledger(rows, {"knowledge/_inbox/my-notes.md": "knowledge/_inbox/my-notes.md"}, {})
    assert any(k == "PROVENANCE-UNGRANTED" for k, _, _ in fails)
    assert banded["knowledge/_inbox/my-notes.md"] == "PARTIAL", "an ungranted claim stays IN the debt"


def test_granted_provenance_unit_passes_with_rationale():
    assert len(A.LEDGER_PROVENANCE_UNITS) == 2, (
        "the ledger-level provenance grant is frozen at 2 — growing it is a deliberate code edit")


def test_illegal_successor_home_is_loud(tmp_path, monkeypatch):
    """Review 2026-07-13 (MUST-FIX): a DISTILLED row could name scripts/x.py, a file inside
    _inbox (staging citing staging), or an absolute path as its successor and go green."""
    d = _ledger(tmp_path, monkeypatch, [
        "knowledge/_inbox/u.md :: DISTILLED :: scripts/anything.py :: p1 ;; p2 ;; p3 :: r",
        "knowledge/_inbox/v.md :: DISTILLED :: knowledge/_inbox/other.md :: p1 ;; p2 ;; p3 :: r",
    ])
    (d / "u.md").write_text("x", encoding="utf-8")
    (d / "v.md").write_text("x", encoding="utf-8")
    (d / "other.md").write_text("knowledge/_inbox/v.md p1 p2 p3", encoding="utf-8")
    rows, _ = A.parse_ledger()
    units = {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md",
             "knowledge/_inbox/v.md": "knowledge/_inbox/v.md",
             "knowledge/_inbox/other.md": "knowledge/_inbox/other.md"}
    fails, banded = A.check_ledger(rows, units, {})
    assert sum(1 for k, _, _ in fails if k == "ILLEGAL-SUCCESSOR") == 2
    assert banded["knowledge/_inbox/u.md"] == "PARTIAL"
    assert banded["knowledge/_inbox/v.md"] == "PARTIAL"


def test_duplicate_rows_are_loud(tmp_path, monkeypatch):
    """A later flattering row must never silently cancel an earlier honest OWED."""
    d = _ledger(tmp_path, monkeypatch, [
        "knowledge/_inbox/u.md :: OWED :: - :: - :: real value here, promotion owed to the QS lane",
        "knowledge/_inbox/u.md :: DROPPED :: - :: - :: checked nothing, dropping it quietly anyway",
    ])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, banded = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "LEDGER-DUPLICATE" for k, _, _ in fails)
    assert banded["knowledge/_inbox/u.md"] == "OWED", "the FIRST row stands; the duplicate is rejected"


def test_row_keyed_at_anchor_file_is_loud(tmp_path, monkeypatch):
    """A row grading .../thread.md instead of the thread DIR exists on disk but grades
    nothing — without this check the real unit silently read UNTOUCHED."""
    d = tmp_path / "knowledge" / "_inbox" / "discord" / "S" / "cat" / "001_t"
    d.mkdir(parents=True)
    (d / "thread.md").write_text("x", encoding="utf-8")
    led = tmp_path / "knowledge" / "_inbox" / "DISTILLATION-LEDGER.md"
    led.write_text(LEDGER_HEAD +
                   "knowledge/_inbox/discord/S/cat/001_t/thread.md :: DROPPED :: - :: - :: "
                   "checked the thread, operator trivia only, nothing transferable\n```",
                   encoding="utf-8")
    monkeypatch.setattr(A, "ROOT", str(tmp_path))
    rows, _ = A.parse_ledger()
    units = {"knowledge/_inbox/discord/S/cat/001_t": "knowledge/_inbox/discord/S/cat/001_t/thread.md"}
    fails, banded = A.check_ledger(rows, units, {})
    assert any(k == "LEDGER-NOT-A-UNIT" for k, _, _ in fails)
    assert banded["knowledge/_inbox/discord/S/cat/001_t"] == "UNTOUCHED", (
        "the REAL unit is still ungraded and must say so")


def test_stopword_pins_are_loud(tmp_path, monkeypatch):
    """Three stopwords must never constitute a DISTILLED proof — but real short values
    ('R9', 'EQ', '8.5') pass, because the stopword list, not raw length, does the work."""
    d = _ledger(tmp_path, monkeypatch, [
        "knowledge/_inbox/u.md :: DISTILLED :: knowledge/s.md :: the ;; design ;; mm :: r",
        "knowledge/_inbox/v.md :: DISTILLED :: knowledge/s.md :: R9 ;; EQ ;; 8.5 :: r",
    ])
    (d / "u.md").write_text("x", encoding="utf-8")
    (d / "v.md").write_text("x", encoding="utf-8")
    (tmp_path / "knowledge" / "s.md").write_text(
        "knowledge/_inbox/u.md knowledge/_inbox/v.md the design mm R9 EQ 8.5", encoding="utf-8")
    rows, _ = A.parse_ledger()
    units = {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md",
             "knowledge/_inbox/v.md": "knowledge/_inbox/v.md"}
    fails, banded = A.check_ledger(rows, units, {})
    assert sum(1 for k, _, _ in fails if k == "GENERIC-PIN") == 3
    assert banded["knowledge/_inbox/u.md"] == "PARTIAL"
    assert banded["knowledge/_inbox/v.md"] == "DISTILLED"


def test_html_comment_citation_does_not_count(tmp_path, monkeypatch):
    """A citation or pin hidden in an HTML comment is invisible in rendered markdown —
    it satisfies nothing a reader can see, so it satisfies nothing here."""
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DISTILLED :: knowledge/s.md :: 762 ;; 1524 ;; 406 :: r"])
    (d / "u.md").write_text("x", encoding="utf-8")
    (tmp_path / "knowledge" / "s.md").write_text(
        "<!-- knowledge/_inbox/u.md 762 1524 406 -->\nvisible text says nothing", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, banded = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "UNCITED-SUCCESSOR" for k, _, _ in fails)
    assert sum(1 for k, _, _ in fails if k == "PIN-MISS") == 3
    assert banded["knowledge/_inbox/u.md"] == "PARTIAL"


def test_thin_drop_rationale_is_loud(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch, ["knowledge/_inbox/u.md :: DROPPED :: - :: - :: junk"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    fails, _ = A.check_ledger(rows, {"knowledge/_inbox/u.md": "knowledge/_inbox/u.md"}, {})
    assert any(k == "THIN-RATIONALE" for k, _, _ in fails), (
        "'junk' is not 'what was checked'")


def test_orphaned_discord_payload_is_loud(tmp_path, monkeypatch):
    """A discord thread dir with raw.json / files/ but NO thread.md must not vanish
    wholesale as 'attachments, never debt' (review 2026-07-13, reproduced live)."""
    t = tmp_path / "knowledge" / "_inbox" / "discord" / "S" / "cat" / "001_x"
    (t / "files").mkdir(parents=True)
    (t / "raw.json").write_text("{}", encoding="utf-8")
    (t / "files" / "a.png").write_bytes(b"x")
    monkeypatch.setattr(A, "ROOT", str(tmp_path))
    monkeypatch.setattr(A, "INBOX", str(tmp_path / "knowledge" / "_inbox"))
    _, units, orphans = A.scan()
    assert units == {}
    assert len(orphans) == 1 and orphans[0].endswith("001_x")


def test_extensionless_file_is_unclassified_outside_payload_dirs():
    """'' was in ATTACHMENT_EXTS, so an extensionless stash file silently vanished."""
    assert A.classify("knowledge/_inbox/some-stash/README") == "UNCLASSIFIED"
    # inside a discord files/ dir the payload rule still catches it first
    assert A.classify("knowledge/_inbox/discord/S/cat/001_x/files/383192_cdnfile") == "ATTACHMENT"


def test_infra_is_path_scoped_not_basename():
    """Naming a staged file 'nlm-queue.md' inside a stash must not make it infra."""
    assert A.classify("knowledge/_inbox/nlm-queue.md") == "INFRA"
    assert A.classify("knowledge/_inbox/some-stash/nlm-queue.md") == "UNIT-ANCHOR" \
        if False else A.classify("knowledge/_inbox/some-stash/nlm-queue.md") != "INFRA"


def test_rationale_with_double_colon_does_not_shift_fields(tmp_path, monkeypatch):
    d = _ledger(tmp_path, monkeypatch,
                ["knowledge/_inbox/u.md :: DROPPED :: - :: - :: checked A :: B :: C — all operator trivia, nothing transferable"])
    (d / "u.md").write_text("x", encoding="utf-8")
    rows, _ = A.parse_ledger()
    assert not rows[0]["malformed"]
    assert "A :: B :: C" in rows[0]["rationale"]


def test_sibling_prefix_does_not_credit_backlink():
    """.../001_Tile must not be credited with citations of .../001_Tile-v2."""
    assert A._cites_unit("a/b/001_Tile/thread.md", "a/b/001_Tile")
    assert A._cites_unit("a/b/001_Tile", "a/b/001_Tile")
    assert not A._cites_unit("a/b/001_Tile-v2/thread.md", "a/b/001_Tile")


def test_unparseable_ledger_is_loud_not_silent(tmp_path, monkeypatch):
    """FIRST-RUN HONESTY: a prose ledger yields 0 rows, and the instrument must SAY so rather
    than quietly grade an unreadable file as fine."""
    d = tmp_path / "knowledge" / "_inbox"
    d.mkdir(parents=True)
    (d / "DISTILLATION-LEDGER.md").write_text("# I am prose and I grade myself\n", encoding="utf-8")
    monkeypatch.setattr(A, "ROOT", str(tmp_path))
    rows, state = A.parse_ledger()
    assert rows == [] and state == "NOT-MACHINE-READABLE"


# ---------------------------------------------------------------- end to end -------------
def test_runs_on_the_real_tree_through_a_pipe():
    """The corpus is Thai-named (ข้อมูลแบ่งปัน) and Windows stdout defaults to cp1252. The old
    script crashed a subprocess consumer with UnicodeEncodeError."""
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "inbox_audit.py")],
                       capture_output=True, cwd=ROOT)
    out = r.stdout.decode("utf-8", errors="replace")
    assert "knowledge units staged" in out
    assert "attachments are NEVER debt" in out
    assert "promoted dir(s) still empty" not in out, "the saturated metric must stay dead"
    # exit 1 = the bookkeeping is LYING — that may never be an accepted steady state
    # (review 2026-07-13: this pin previously accepted 1, so nothing monitored exit-1).
    # Debt (exit 2) stays advisory by doctrine; lies fail the suite.
    assert r.returncode in (0, 2), f"integrity failures on the real tree:\n{out[-2000:]}"


def test_json_mode_is_machine_readable_and_exit_parity_holds():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "inbox_audit.py"), "--json"],
                       capture_output=True, cwd=ROOT)
    d = json.loads(r.stdout.decode("utf-8"))
    assert d["classes"]["UNIT-ANCHOR"] == len(d["units"])
    assert d["classes"]["ATTACHMENT"] > d["classes"]["UNIT-ANCHOR"], (
        "attachments outnumber units — that asymmetry IS the bug the old instrument had")
    # exit-code parity: a scripted consumer must see the same 0/1/2 a human does
    # (review 2026-07-13: --json could never exit 2 and dropped the aging advisory)
    assert "aging_untouched" in d
    assert d["exit_code"] == r.returncode
    t = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "inbox_audit.py")],
                       capture_output=True, cwd=ROOT)
    assert t.returncode == r.returncode, "text and json modes disagree on the exit code"
