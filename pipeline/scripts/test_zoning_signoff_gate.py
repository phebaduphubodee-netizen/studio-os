"""
test_zoning_signoff_gate.py — the OWNER-SIGN ledger for semantic plan geometry.

These are the properties that make it a GATE and not a decoration. Every one of them is a thing the
round-4 free-text signature did NOT have.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zoning_signoff_gate as Z          # noqa: E402


SHEET = "654446_i-24-004-k._villavalley_2-_-01:p3"
NORTH = {"axis": "h", "face_lo": 4969.9, "face_hi": 5069.4, "gap_lo": 3120.0, "gap_hi": 7720.5}
BOGUS = {"axis": "h", "face_lo": 3905.2, "face_hi": 3999.4, "gap_lo": 3120.0, "gap_hi": 7720.5}
KEY_N = f"{SHEET}|h:4969.9:5069.4:3120.0:7720.5"


def entry(key, by="OWNER", date="2026-07-12", **kw):
    return {"key": key, "by": by, "date": date, **kw}


# ------------------------------------------------------------------ the key IS the whole mechanism
def test_the_canonical_key_is_sheet_namespaced_AND_geometric():
    assert Z.canonical_key(SHEET, NORTH) == KEY_N
    # a different LINE on the same sheet -> a different key. This is what kills ATTACK A.
    assert Z.canonical_key(SHEET, BOGUS) != KEY_N
    # the SAME line on a different sheet -> a different key. A signature is non-transferable.
    assert Z.canonical_key("other-sheet:p3", NORTH) != KEY_N


def test_ONE_signature_definition_in_this_studio():
    """sign_status is IMPORTED from ffe_signoff_gate. A second signing mechanism would be a second
    thing to get wrong; this asserts we did not build one."""
    import ffe_signoff_gate as F
    assert Z.sign_status is F.sign_status
    assert Z.load_signoff is F.load_signoff


@pytest.mark.parametrize("e,st", [
    (entry(KEY_N), "valid"),
    (entry(KEY_N, by="OWNER-CONFIRM-PENDING"), "pending"),   # the unsigned template never signs
    (entry(KEY_N, by=""), "pending"),
    (entry(KEY_N, date=""), "incomplete"),                   # a signer with no date cannot bind
    ({"by": "OWNER", "date": "2026-07-12"}, "incomplete"),   # a signer with no KEY binds nothing
    ("not a dict", "inert"),
])
def test_only_a_complete_owner_entry_is_a_signature(e, st):
    assert Z.sign_status(e) == st
    if st != "valid":
        assert Z.resolve_edge(KEY_N, [e]) is None, "a non-valid entry must never bind"


def test_a_valid_entry_binds_its_key_and_ONLY_its_key():
    led = [entry(KEY_N)]
    assert Z.resolve_edge(KEY_N, led)["by"] == "OWNER"
    assert Z.resolve_edge(Z.canonical_key(SHEET, BOGUS), led) is None


def test_the_key_match_is_EXACT_not_fuzzy():
    """ffe_signoff_gate's load-bearing bug was an OVER-TOLERANT key (a source abbreviation collapsed
    two products into one bindable bucket). Here, tolerance would mean one signature binding a line
    the owner never saw. Whitespace/case only."""
    led = [entry("  " + KEY_N.upper() + " \n")]
    assert Z.resolve_edge(KEY_N, led) is not None, "case/space normalisation must still bind"
    # one snapped millimetre away is a DIFFERENT line
    off = f"{SHEET}|h:4969.9:5069.4:3120.0:7721.5"
    assert Z.resolve_edge(off, led) is None


def test_LAST_valid_entry_wins_and_a_trailing_typo_cannot_ERASE_a_real_sign():
    """The owner APPENDS corrections (ffe_signoff_gate / placement_gate semantics)."""
    led = [entry(KEY_N, by="OWNER", date="2026-07-11"),
           entry(KEY_N, by="OWNER", date="2026-07-12", note="corrected")]
    assert Z.resolve_edge(KEY_N, led)["date"] == "2026-07-12"
    led.append(entry(KEY_N, by=""))                     # a pending/typo trailer
    assert Z.resolve_edge(KEY_N, led)["date"] == "2026-07-12", "a typo erased a real signature"


# --------------------------------------------------------------------------------- the fail-safes
@pytest.mark.parametrize("body", ["", "{ not json", '{"signed": "nope"}'])
def test_an_unreadable_or_odd_ledger_SIGNS_NOTHING(tmp_path, body):
    p = tmp_path / "zoning-signoff.json"
    p.write_text(body, encoding="utf-8")
    entries, sha, err = Z.load_ledger(str(p))
    assert entries == []
    assert Z.resolve_edge(KEY_N, entries) is None


def test_a_missing_ledger_signs_nothing_and_SAYS_SO():
    entries, sha, err = Z.load_ledger("/definitely/not/here.json")
    assert entries == [] and sha is None and "not found" in err


def test_the_sha256_pins_WHICH_ledger_authorised_a_run(tmp_path):
    p = tmp_path / "zoning-signoff.json"
    p.write_text(json.dumps({"signed": [entry(KEY_N)]}), encoding="utf-8")
    _, sha1, _ = Z.load_ledger(str(p))
    p.write_text(json.dumps({"signed": [entry(KEY_N), entry(KEY_N + "x")]}), encoding="utf-8")
    _, sha2, _ = Z.load_ledger(str(p))
    assert len(sha1) == 64 and sha1 != sha2, \
        "a ledger the agent rewrites must at least be ATTRIBUTABLE by hash"


# -------------------------------------------------- the audit block must be capable of being FALSE
def test_the_audit_block_has_NO_always_true_field():
    """Round 4 stamped `bijection_verified: True` into every artefact on disk, because a failed
    bijection refused the write. A constant is not an audit result. Both booleans emitted now VARY."""
    bound = [{"id": "OE00", "key": KEY_N, "spec": "h:4970:5069:3120:7720", "length_mm": 4600.5,
              "by": "OWNER", "date": "2026-07-12", "zone": "living", "note": "n"}]
    clean = Z.signoff_block("l.json", "a" * 64, [entry(KEY_N)], bound, SHEET)
    assert clean["orphans_present"] is False and clean["malformed_present"] is False

    # an owner entry for THIS sheet that binds no written edge -> ORPHAN, and the flag flips TRUE
    # in a WRITTEN artefact. (The owner signed a line the agent did not use: never silently dropped.)
    orphaned = Z.signoff_block("l.json", "a" * 64,
                               [entry(KEY_N), entry(f"{SHEET}|v:3020.5:3120.0:0.0:249.8")],
                               bound, SHEET)
    assert orphaned["orphans_present"] is True
    assert len(orphaned["orphan_entries"]) == 1

    # a real signer with a broken anchor -> MALFORMED, surfaced, also true in a written artefact
    mal = Z.signoff_block("l.json", "a" * 64,
                          [entry(KEY_N), {"by": "OWNER", "date": "2026-07-12"}], bound, SHEET)
    assert mal["malformed_present"] is True

    for b in (clean, orphaned, mal):
        assert "bijection_verified" not in json.dumps(b)


def test_an_entry_for_ANOTHER_sheet_is_not_an_orphan_here_and_never_binds():
    other = entry("some-other-sheet:p7|h:1.0:2.0:3.0:4.0")
    assert Z.orphans([other], [], SHEET) == [], "another sheet's signature is not this sheet's orphan"
    assert Z.resolve_edge(KEY_N, [other]) is None


def test_an_UNSCOPED_key_is_not_a_season_ticket():
    """A key with no sheet namespace binds nothing: it would otherwise be one signature for every
    sheet in the studio."""
    assert Z.entry_sheet(entry("h:4969.9:5069.4:3120.0:7720.5")) is None
    assert Z.resolve_edge(KEY_N, [entry("h:4969.9:5069.4:3120.0:7720.5")]) is None
