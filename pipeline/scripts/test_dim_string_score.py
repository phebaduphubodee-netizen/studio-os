"""Tests for dim_string_score.py — the reader's REAL ground truth (D1).

The point of this instrument is that it CAN FAIL. So the tests are mostly about the ways it could
quietly stop being able to:
  * the null must be a real null (feed it a face set that answers everything, and the null must
    rise to meet the score -- that is what "no signal" looks like);
  * the matcher must not match a string to a face pair that does not bracket it;
  * the off-ink bucket must not become a place to hide failures;
  * the Thai split-mark bug must not silently eat the numerals.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest

import dim_string_score as D
from dim_string_score import (ANCHOR_TOL_MM, _best_pair_bruteforce, best_pair, chain_corroborates,
                              footprint, nulls, overall_string, run, score, split_off_ink)

_PDF = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "_private", "discord", "MY-DATA-PEAT",
    "โปรเจ็ก", "012_I-24-004-Kนุช-บ้าน-Villa-Valley-สุระ-2", "files",
    "654446_I-24-004-K._VillaValley_2-_-01.pdf"))
real_pdf = pytest.mark.skipif(not os.path.exists(_PDF), reason="client PDF not present")


# ------------------------------------------------------------------ the matcher, in isolation
def test_a_string_must_sit_ON_the_span_it_dimensions():
    faces = [0.0, 100.0, 1000.0, 1100.0]
    # a "1000" sitting at x=550 brackets the 100..1100 pair (1000 wide) -> matched
    assert best_pair(1000.0, 550.0, 200.0, faces)[0] == pytest.approx(0.0)
    # the SAME value parked far off to the side brackets nothing that reproduces it
    b = best_pair(1000.0, 5000.0, 200.0, faces)
    assert b is None, "a face pair the string does not sit on must NOT be matchable"


def test_the_slack_is_the_numerals_OWN_width_and_no_more():
    """A '100' at 1:50 cannot fit between the faces it labels, so the draughtsman parks it just
    outside. The slack is exactly that -- not a free radius."""
    faces = [0.0, 100.0]
    assert best_pair(100.0, 160.0, 200.0, faces) is not None, "just outside, within its own width"
    assert best_pair(100.0, 160.0, 10.0, faces) is None, "a NARROW glyph gets NO such licence"


def test_the_bucket_is_derived_not_tuned():
    """off-ink means literally 'no face pair on this axis brackets it', not 'far from the
    building'. There is no magic envelope constant to tune."""
    strings = [{"text": "999", "value_mm": 999.0, "axis": "x", "pos_mm": 50000.0,
                "extent_mm": 100.0, "at_mm": [50000.0, 0.0]}]
    m, u, o = score(strings, [0.0, 100.0], [0.0, 100.0], 2.0)
    assert (len(m), len(u), len(o)) == (0, 0, 1)
    assert o[0]["why"].startswith("no face pair")


# ------------------------------------------------------------------------------- THE NULL BITES
def test_the_NULL_RISES_when_the_face_set_can_answer_anything():
    """THE TEST THAT KEEPS THIS INSTRUMENT HONEST. Hand it a face set so dense that every value is
    reproducible somewhere, and the permutation null must climb to meet the score -- i.e. the
    scorecard must SAY 'no signal' rather than reporting a flattering headline. If this ever goes
    green with a low null, the null has stopped being a null."""
    faces = [float(v) for v in range(0, 5001, 5)]          # every 5 mm: answers almost anything
    strings = [{"text": str(v), "value_mm": float(v), "axis": "x", "pos_mm": 2500.0,
                "extent_mm": 400.0, "at_mm": [2500.0, 0.0]}
               for v in (100, 400, 900, 1600, 2500, 3600)]
    m, u, o = score(strings, faces, faces, 2.0)
    real = len(m) / max(len(m) + len(u), 1)
    n = nulls(strings, faces, faces, 2.0, 200, 7)
    assert real == 1.0, "a dense face set matches everything -- that is the point"
    assert n["permutation"]["mean"] > 95.0, \
        "and the NULL matches everything too, so the headline means NOTHING. The scorecard must " \
        "print 'NO SIGNAL' here."
    assert real * 100 <= n["permutation"]["p95"], "no separation = no signal"


# ------------------------------------------------------------------------ against the real sheet
@real_pdf
def test_the_reader_reproduces_the_DESIGNERS_OWN_printed_dimensions():
    """THE SCORE. GT = the strings the designer typed in CAD. No human takeoff in this loop, and
    living012_takeoff.json is not consulted -- it CANNOT be, it is a copy of the reader (D1)."""
    sc = run(_PDF, 3, perms=300, seed=7)
    assert sc["n_strings"] == 52
    assert sc["n_matched"] == 40 and sc["n_addressable"] == 48
    assert sc["match_rate"] == pytest.approx(0.833, abs=0.01)
    assert sc["median_error_mm"] <= 0.5
    assert sc["worst_error_mm"] <= 2.0
    # AND IT IS NOT NOISE:
    assert 100 * sc["match_rate"] > sc["null"]["permutation"]["p95"] + 30, \
        "the score must clear the permutation null by a wide margin or it is face-density noise"
    assert sc["null"]["random_dims"]["mean"] < 10.0


@real_pdf
def test_the_scorecard_NAMES_the_strings_it_failed_to_match():
    """A scorer that only reports its wins is a press release. Every failure is named."""
    sc = run(_PDF, 3, perms=1, seed=7)
    assert len(sc["unmatched"]) == 8
    named = {(r["text"], r["axis"]) for r in sc["unmatched"]}
    # the two printed '400's are BF01's joinery depth -- drawn on the joinery pen, so the wall
    # reader legitimately has no face there. It is REPORTED, not swept up.
    assert ("400", "x") in named
    assert all("best_error_mm" in r and "best_faces_mm" in r for r in sc["unmatched"])
    assert all(r["best_error_mm"] > sc["tol_mm"] for r in sc["unmatched"])


@real_pdf
def test_the_THAI_split_mark_bug_does_NOT_touch_the_numerals():
    """This PDF splits Thai combining vowels/tone marks off their consonants. VERIFY, do not
    assume: every dimension string must arrive as a clean ASCII numeral."""
    sc = run(_PDF, 3, perms=1, seed=7)
    allstr = sc["matched"] + sc["unmatched"] + sc["off_ink"]
    assert len(allstr) == 52
    assert all(r["text"].isascii() and r["text"].isdigit() for r in allstr)
    # the tripwire itself must be live: it DID catch digit-bearing non-numeral spans on this page
    assert sc["text_layer_health"]["spans_with_digits_but_not_clean_numerals"], \
        "the tripwire found nothing at all -- suspect it is not actually running"


@real_pdf
def test_the_scorer_NEVER_reads_the_hand_takeoff_or_the_readers_own_room(monkeypatch):
    """D1's whole point, pinned BEHAVIOURALLY rather than by grepping the source (the source
    mentions the takeoff by name, in prose, precisely to say it must not be used).

    Any attempt to OPEN the hand takeoff -- or the reader's own emitted room-spec -- while scoring
    blows up. If the GT ever gets quietly re-contaminated with the reader's own output, this is
    what catches it."""
    import builtins
    real_open = builtins.open
    forbidden = ("living012_takeoff", "012p3-room-auto", "012p3-walls-mm", "012p3-openings")

    def guarded(path, *a, **k):
        if any(f in str(path) for f in forbidden):
            raise AssertionError("the scorer opened %s -- the GT is contaminated" % path)
        return real_open(path, *a, **k)

    monkeypatch.setattr(builtins, "open", guarded)
    sc = run(_PDF, 3, perms=1, seed=7)          # must complete with NO answer key in the loop
    assert sc["n_matched"] == 40


# =============================================================================================
#  v0.2 -- THE THREE THINGS THE ADVERSARIAL REVIEW PROVED v0.1 WAS BLIND TO.
#  Every one of these tests FAILS against v0.1. That is the only reason to believe them.
# =============================================================================================

# ----------------------------------------------------------------- (a) THE ORIGIN ANCHOR
@real_pdf
def test_DEFECT_2a_a_50mm_ORIGIN_SHIFT_now_COLLAPSES_the_score():
    """THE FIX FOR THE BUG THAT SILENTLY BROKE THE OLD EXTRACTOR ON THIS VERY SHEET.

    The killer detail is the second half of this test: under a 50 mm origin shift EVERY v0.1
    quantity is BYTE-IDENTICAL to the baseline -- match_rate, recall, precision, median error, the
    nulls. v0.1 could not have seen this bug if it had run for a thousand years, because faces and
    text co-move through the same origin. Only the ABSOLUTE anchor -- text layer vs the frame's
    DECLARED datum 0.0 -- moves, and it moves by the full 50 mm."""
    base = run(_PDF, 3, perms=1, seed=7)
    shift = run(_PDF, 3, perms=1, seed=7, mutate="origin+50mm")

    # THE OLD INSTRUMENT SEES ABSOLUTELY NOTHING:
    assert shift["match_rate"] == base["match_rate"] == pytest.approx(0.833, abs=0.01)
    assert shift["recall"] == base["recall"]
    assert shift["face_precision"] == base["face_precision"]
    assert shift["n_matched"] == base["n_matched"] == 40
    assert shift["median_error_mm"] == base["median_error_mm"]

    # THE NEW ONE REFUSES THE FRAME:
    assert base["anchor_ok"] is True
    assert shift["anchor_ok"] is False
    assert base["headline_f1"] is not None
    assert shift["headline_f1"] is None, "a wrong frame must yield NO SCORE, not a lower score"
    res = {c["id"]: c["residual_mm"] for c in shift["anchor"]["checks"]}
    assert abs(res["ORIGIN-x"]) == pytest.approx(50, abs=2), res
    assert abs(res["ORIGIN-y"]) == pytest.approx(50, abs=2), res
    # ...and it is the ORIGIN checks that fired, not the extent ones (which are origin-invariant):
    ok = {c["id"]: c["ok"] for c in shift["anchor"]["checks"]}
    assert ok["ORIGIN-x"] is False and ok["ORIGIN-y"] is False
    assert ok["EXTENT-x"] is True and ok["EXTENT-y"] is True


@real_pdf
def test_the_ORIGIN_anchor_is_TEXT_LAYER_ONLY_and_therefore_not_circular():
    """An anchor that re-derives the origin FROM the reader's own faces is worthless. Pinned
    behaviourally: `overall_string` takes NO face argument at all, and `footprint` -- which decides
    who gets EXCUSED -- returns the same answer when handed deliberately garbage faces."""
    import inspect
    assert "fx" not in inspect.signature(overall_string).parameters
    assert "fy" not in inspect.signature(overall_string).parameters

    sc = run(_PDF, 3, perms=1, seed=7)
    strings = sc["matched"] + sc["unmatched"] + sc["off_ink"]
    good = footprint(strings, [0.0, 7820.0], [0.0, 9719.7])
    junk = footprint(strings, [0.0, 1.0], [0.0, 1.0])          # a reader that extracted nothing
    huge = footprint(strings, [-9e4, 9e4], [-9e4, 9e4])        # a reader that hallucinated the world
    assert good == junk == huge == {"x": [0.0, 7820.0], "y": [0.0, 9720.0]}, \
        "the EXCUSE must never be able to follow the reader down"


@real_pdf
def test_the_overall_string_is_the_CHAIN_corroborated_one_not_the_biggest_number():
    """The '30000' is a 30 m SITE/PLOT dimension. If it were crowned 'the overall', the footprint
    would balloon and the datum would be nonsense. It is rejected because NO CHAIN OF STRINGS SUMS
    TO IT -- a fact of the text layer, not a tuned envelope."""
    sc = run(_PDF, 3, perms=1, seed=7)
    strings = sc["matched"] + sc["unmatched"] + sc["off_ink"]
    assert overall_string(strings, "x")["text"] == "7820"     # NOT '30000', which is larger
    assert overall_string(strings, "y")["text"] == "9720"
    big = next(s for s in strings if s["text"] == "30000")
    assert chain_corroborates(big, strings) is False
    assert chain_corroborates(overall_string(strings, "x"), strings) is True


def test_ANCHOR_TOL_is_FROZEN_and_DERIVED_not_tuned():
    """12.0 mm = 3 x robust-sigma of the ORIGIN-INVARIANT numeral-centring residual
    (sigma = 1.4826 x MAD = 1.4826 x 2.65 mm). A tolerance that widened itself when the reader got
    worse would be an alibi, not a tolerance -- so the live MAD is REPORTED but never fed back."""
    assert ANCHOR_TOL_MM == 12.0
    assert D._CALIBRATION_MAD_MM == 2.65
    assert 3 * 1.4826 * D._CALIBRATION_MAD_MM == pytest.approx(ANCHOR_TOL_MM, abs=0.3)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "dim_string_score.py"), encoding="utf-8").read()
    assert "ANCHOR_TOL_MM = 12.0" in src
    assert "ANCHOR_TOL_MM =" not in src.split("def ", 1)[1], \
        "ANCHOR_TOL_MM must never be reassigned at run time"


# ------------------------------------------------------- (b) THE OVER-EXTRACTION PENALTY
@real_pdf
def test_DEFECT_2b_the_PHANTOM_GRID_now_scores_WORSE_not_better():
    """`phantom-inside` is the honest form of the attack: true faces PLUS a 100 mm grid, confined
    inside the building so it does NOT trip the extent anchor. The recall REWARD is still there and
    still real -- 95.8% vs the honest reader's 83.3%, because more faces means more chances to
    bracket a string. The PRECISION TERM is what makes it cost more than it pays."""
    base = run(_PDF, 3, perms=1, seed=7)
    ph = run(_PDF, 3, perms=1, seed=7, mutate="phantom-inside")

    assert ph["anchor_ok"] is True, "this attack passes both anchors -- precision must do the work"
    assert ph["recall"] > base["recall"], \
        "the over-extraction REWARD is real and this test asserts it still exists"
    assert ph["face_precision"] < 0.35 < base["face_precision"]
    assert ph["headline_f1"] < base["headline_f1"], "THE WHOLE POINT: more faces must cost"
    assert ph["headline_f1"] == pytest.approx(0.427, abs=0.02)
    assert base["headline_f1"] == pytest.approx(0.785, abs=0.02)


@real_pdf
def test_the_100mm_grid_that_scored_94_PERCENT_in_v0_1_is_now_REFUSED():
    """The reviewer's exact attack: true faces + a 100 mm grid across the sheet -> 48/51 = 94.1%
    in v0.1, HIGHER than the honest reader. It still gets its inflated raw match rate. It gets no
    score, twice over: the extent anchor fires, AND the ungated F1 falls off a cliff."""
    ph = run(_PDF, 3, perms=200, seed=7, mutate="phantom-100mm")
    assert ph["match_rate"] > 0.93, "v0.1's flattering raw number is still there, on purpose"
    assert ph["anchor_ok"] is False and ph["headline_f1"] is None
    assert ph["f1_ungated"] < 0.30
    assert ph["face_precision"] < 0.20
    # third, independent catch: the permutation null goes through the roof -> 'NO SIGNAL'
    assert ph["null"]["permutation"]["p95"] >= 100 * ph["match_rate"] - 40


# ---------------------------------------------------------------- (c) THE OFF-INK GATE
@real_pdf
def test_DEFECT_2c_OFF_INK_can_no_longer_EVAPORATE_the_denominator():
    """v0.1: cripple the reader to 4 faces/axis and `addressable` collapsed 48 -> 3 while off-ink
    ballooned 4 -> 49. The reader scored on a denominator of THREE. v0.2 holds the denominator at
    48 because 45 of those off-ink strings sit INSIDE the printed footprint -- they are faces the
    reader LOST, not site notes -- and an off-ink string inside the building is A MISS."""
    base = run(_PDF, 3, perms=1, seed=7)
    cr = run(_PDF, 3, perms=1, seed=7, mutate="cripple-4")

    assert base["n_off_ink"] == 4 and base["n_off_ink_inside_footprint"] == 0
    assert cr["n_off_ink"] >= 45
    assert cr["n_off_ink_inside_footprint"] >= 45, "these are LOST FACES, not excuses"
    assert cr["n_addressable"] <= 5, "v0.1's denominator really does evaporate"
    assert cr["n_scoreable"] == base["n_scoreable"] == 48, "v0.2's does NOT"
    assert cr["match_rate"] > cr["recall"] * 4, "v0.1's rate is inflated by the tiny denominator"
    assert cr["recall"] < 0.05
    assert cr["anchor_ok"] is False and cr["headline_f1"] is None


@real_pdf
def test_the_four_EXCUSED_strings_are_excused_by_GEOMETRY_not_by_a_list():
    """All four off-ink strings on the honest reader sit OUTSIDE the printed footprint on their own
    axis: the 30 m site dim, and three '100's beyond the outer faces. The rule reproduces the
    hand-excused set exactly, with no allow-list and nothing tuned."""
    sc = run(_PDF, 3, perms=1, seed=7)
    assert sc["n_off_ink_outside_footprint"] == 4
    assert sc["n_off_ink_inside_footprint"] == 0
    assert {r["text"] for r in sc["off_ink_outside_footprint"]} == {"30000", "100"}
    fp = sc["anchor"]["footprint_mm"]
    for r in sc["off_ink_outside_footprint"]:
        lo, hi = fp[r["axis"]]
        assert r["pos_mm"] < lo or r["pos_mm"] > hi


def test_an_off_ink_string_INSIDE_the_building_is_a_MISS_not_an_excuse():
    inside = {"text": "900", "value_mm": 900.0, "axis": "x", "pos_mm": 3000.0,
              "extent_mm": 100.0, "at_mm": [3000.0, 0.0]}
    outside = {**inside, "pos_mm": 9999.0, "at_mm": [9999.0, 0.0]}
    out, ins = split_off_ink([inside, outside], {"x": [0.0, 7820.0], "y": [0.0, 9720.0]})
    assert len(ins) == 1 and ins[0]["pos_mm"] == 3000.0
    assert len(out) == 1 and out[0]["pos_mm"] == 9999.0


@real_pdf
def test_THE_HOLE_IN_MY_OWN_FIX_a_minimal_reader_still_BEATS_the_honest_one():
    """PINNING A HOLE OPEN, NOT CLOSED. 13th flattering-scorer recurrence in this project.

    Delete the 15 real wall faces the designer never dimensioned, keep the 43 that some string
    uses: both anchors pass, recall is untouched, face_precision hits 100% and F1 reaches 90.9% --
    BEATING the honest reader's 78.5% BY DELETING REAL WALLS.

    This test asserts the hole IS THERE. If someone later 'fixes' precision and this test goes red,
    read the RESIDUAL block before celebrating: the fix must distinguish 'did not hallucinate' from
    'deleted the evidence', and the printed strings contain no information about the faces they do
    not dimension. It needs a face-level GT (the wall poche itself), not a cleverer formula."""
    base = run(_PDF, 3, perms=1, seed=7)
    cheat = run(_PDF, 3, perms=1, seed=7, mutate="minimal-reader")

    assert cheat["anchor_ok"] is True, "it passes both anchors"
    assert cheat["faces_emitted"] == 43 and base["faces_emitted"] == 58, "15 real walls deleted"
    assert cheat["recall"] == base["recall"], "recall cannot see the deletion"
    assert cheat["face_precision"] == 1.0
    assert cheat["headline_f1"] > base["headline_f1"], \
        "THE HOLE: deleting real walls RAISES the score. Named in the RESIDUAL block, not hidden."
    assert cheat["headline_f1"] == pytest.approx(0.909, abs=0.02)
    # the one thing that DOES bound it: mounting this attack requires reading the text layer, i.e.
    # the GT. Honest face loss goes the other way, and that is what the next two assertions pin.
    assert run(_PDF, 3, perms=1, seed=7, mutate="drop-half")["headline_f1"] < base["headline_f1"]
    assert run(_PDF, 3, perms=1, seed=7, mutate="cripple-4")["headline_f1"] is None


# ------------------------------------------------------------------------ NO REGRESSIONS
@real_pdf
def test_the_two_NULLS_are_UNCHANGED_by_v0_2():
    """The hard constraint on this round: do not break the existing nulls. They are still computed
    on the raw addressable match rate, exactly as in v0.1, so the numbers stay comparable.

    PERMUTATION reproduces the briefed 23.4% EXACTLY.

    RANDOM-DIMS DOES NOT REPRODUCE THE BRIEFED 4.8%, AND I DID NOT BREAK IT. Its mean is 2.1%
    (2.0-2.3% across seeds 1/7/42 and 300/2000 perms). I checked this the only way that settles it:
    I re-ran the null with the O(n^2) matcher -- v0.1's literal code -- and both matchers return
    BYTE-IDENTICAL nulls (perm 23.4/31.2/41.7, random 2.1/6.2/10.4). So 4.8% was never this number
    in this configuration; the briefed figure is in the p95 range (4.2-6.2%), not the mean. Pinned
    to what the instrument actually says, not to what the brief said."""
    sc = run(_PDF, 3, perms=2000, seed=7)
    assert sc["null"]["permutation"]["mean"] == pytest.approx(23.4, abs=1.0)
    assert sc["null"]["random_dims"]["mean"] == pytest.approx(2.1, abs=1.0)
    assert sc["null"]["random_dims"]["mean"] < 5.0
    assert 100 * sc["match_rate"] > sc["null"]["permutation"]["p95"] + 30


def test_the_fast_matcher_is_EXACTLY_the_slow_one():
    """best_pair was rewritten O(n^2) -> O(n log n) so the 434-face phantom grid could run its
    nulls. A speedup that quietly changes the score is the oldest way to fake progress in this
    repo, so the O(n^2) DEFINITION is kept and the two are checked to agree on random inputs."""
    rng = random.Random(11)
    for _ in range(400):
        faces = sorted({round(rng.uniform(0, 8000), 1) for _ in range(rng.randint(2, 25))})
        v = round(rng.uniform(50, 8000), 1)
        c = round(rng.uniform(-500, 8500), 1)
        e = round(rng.uniform(10, 400), 1)
        a, b = best_pair(v, c, e, faces), _best_pair_bruteforce(v, c, e, faces)
        assert (a is None) == (b is None)
        if a is not None:
            assert a[0] == pytest.approx(b[0], abs=1e-9), (faces, v, c, e, a, b)


@real_pdf
def test_the_headline_MOVED_and_is_reported_honestly():
    """83.3% was the v0.1 headline. It is now a COMPONENT, not the score. The score is F1 of
    recall and face-precision, and it is LOWER. That is the correct direction."""
    sc = run(_PDF, 3, perms=1, seed=7)
    assert sc["schema"] == "interior-ai/dim-string-scorecard@0.2"
    assert sc["match_rate"] == pytest.approx(0.833, abs=0.01)     # v0.1's number, still printed
    assert sc["recall"] == pytest.approx(0.833, abs=0.01)
    assert sc["face_precision"] == pytest.approx(0.741, abs=0.01)
    assert sc["headline_f1"] == pytest.approx(0.785, abs=0.01)
    assert sc["headline_f1"] < sc["match_rate"], "the honest number is lower. Do not tune it back."
    assert sc["centring_mad_mm"] == pytest.approx(2.65, abs=0.5), \
        "the drift tripwire on the constant ANCHOR_TOL_MM was derived from"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
