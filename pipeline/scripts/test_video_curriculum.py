#!/usr/bin/env python3
"""Tests for video_curriculum.py.

The rule this file is written against (measurement-discipline, the flattering-scorer
shape recorded 14 times in this repo): a test must not compute its expectation from the
same helper the code under test uses. Every expectation below is a literal written by
hand, and every LOUD-FAIL case is driven by a ledger that is wrong in exactly one way.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video_curriculum as vc  # noqa: E402


def row(**over):
    r = {
        "id": "kmCHv3PG2XM",
        "url": "https://www.youtube.com/watch?v=kmCHv3PG2XM",
        "title": "Interior Designer Fixes 4 People's Bedrooms",
        "channel": "Architectural Digest",
        "minutes": 11.2,
        "g_items": ["G3"],
        "priority": "must",
        "status": "unwatched",
        "queued_at": "2026-08-28",
        "why": "critique order",
        "notes": None,
        "watched_at": None,
        "distilled_to": None,
    }
    r.update(over)
    return r


def led(*rows):
    return {"rows": list(rows)}


class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, rel, body):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        return rel.replace("\\", "/")

    def test_clean_unwatched_row_is_not_a_failure(self):
        fails, debts = vc.check(led(row()), repo=self.tmp)
        self.assertEqual(fails, [])
        self.assertEqual([d[0] for d in debts], ["unwatched-must"])

    def test_url_must_match_its_own_id(self):
        fails, _ = vc.check(led(row(url="https://www.youtube.com/watch?v=AAAAAAAAAAA")),
                            repo=self.tmp)
        self.assertTrue(any("url does not match" in f for f in fails), fails)

    def test_watched_without_notes_is_a_failure(self):
        fails, _ = vc.check(led(row(status="watched", watched_at="2026-08-28")),
                            repo=self.tmp)
        self.assertTrue(any("no notes path" in f for f in fails), fails)

    def test_watched_with_missing_notes_file_is_a_failure(self):
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes="nope/missing.md")),
            repo=self.tmp)
        self.assertTrue(any("notes path does not exist" in f for f in fails), fails)

    def test_watched_with_notes_but_no_distillation_is_debt_not_failure(self):
        n = self._write("notes/a.md", "watched it")
        fails, debts = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n)), repo=self.tmp)
        self.assertEqual(fails, [])
        self.assertEqual([d[0] for d in debts], ["watched-not-distilled"])

    def test_distilled_to_must_exist(self):
        n = self._write("notes/a.md", "watched it")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    distilled_to="knowledge/nope.md")), repo=self.tmp)
        self.assertTrue(any("does not exist" in f for f in fails), fails)

    def test_distilled_to_must_cite_the_video_id_back(self):
        n = self._write("notes/a.md", "watched it")
        d = self._write("knowledge/x.md", "a successor that never names its source")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n, distilled_to=d)),
            repo=self.tmp)
        self.assertTrue(any("never mentions the video id" in f for f in fails), fails)

    def test_distilled_to_citing_the_id_passes_and_clears_the_debt(self):
        n = self._write("notes/a.md", "watched it")
        d = self._write("knowledge/x.md", "derived from kmCHv3PG2XM, see notes")
        fails, debts = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n, distilled_to=d)),
            repo=self.tmp)
        self.assertEqual(fails, [])
        self.assertEqual(debts, [])

    # ---- the third state: a pick that returned nothing (2026-08-28) -----------------
    # Every expectation below is a literal. The state exists so that a video with NO usable
    # content stops being a debt without anything being written into knowledge/ from a source
    # that had nothing in it — and every test here is aimed at the way that state could rot
    # into the cheap way out of a hard distillation.

    def test_yield_none_with_reason_and_citation_clears_the_debt(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM returned no captions and its frames are "
                                      "title cards; no usable content was obtained.")
        fails, debts = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing was said "
                                          "or shown that could be quoted or measured.",
                                "recorded_in": n})),
            repo=self.tmp)
        self.assertEqual(fails, [])
        self.assertEqual(debts, [])

    def test_yield_none_reason_that_is_a_token_is_refused_by_name(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "nothing", "recorded_in": n})),
            repo=self.tmp)
        self.assertTrue(any("is a token, not a reason" in f for f in fails), fails)

    def test_yield_none_short_reason_is_a_failure(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "no captions, bad frames", "recorded_in": n})),
            repo=self.tmp)
        self.assertTrue(any("chars — under" in f for f in fails), fails)

    def test_yield_none_recorded_in_must_cite_the_video_id_back(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        other = self._write("notes/b.md", "a unit about some entirely different video")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing usable.",
                                "recorded_in": other})),
            repo=self.tmp)
        self.assertTrue(any("never mentions the video id" in f for f in fails), fails)

    def test_yield_none_recorded_in_must_exist(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing usable.",
                                "recorded_in": "knowledge/nope.md"})),
            repo=self.tmp)
        self.assertTrue(any("recorded_in names a path that does not exist" in f
                            for f in fails), fails)

    def test_yield_none_needs_recorded_in_at_all(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n,
                    yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing usable."})),
            repo=self.tmp)
        self.assertTrue(any("no recorded_in" in f for f in fails), fails)

    def test_yield_none_together_with_distilled_to_is_a_contradiction(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        d = self._write("knowledge/x.md", "kmCHv3PG2XM taught us a thing")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n, distilled_to=d,
                    yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing usable.",
                                "recorded_in": n})),
            repo=self.tmp)
        self.assertTrue(any("yielded something and nothing" in f for f in fails), fails)

    def test_yield_none_on_an_unwatched_row_is_a_failure(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(yield_none={"reason": "No English captions and every extracted frame is a "
                                          "title card or a blank transition; nothing usable.",
                                "recorded_in": n})),
            repo=self.tmp)
        self.assertTrue(any("only a video somebody actually watched" in f for f in fails), fails)

    def test_yield_none_must_be_an_object_not_a_flag(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        fails, _ = vc.check(
            led(row(status="watched", watched_at="2026-08-28", notes=n, yield_none=True)),
            repo=self.tmp)
        self.assertTrue(any("must be an object" in f for f in fails), fails)

    def test_distilled_without_watching_is_a_failure(self):
        d = self._write("knowledge/x.md", "kmCHv3PG2XM")
        fails, _ = vc.check(led(row(distilled_to=d)), repo=self.tmp)
        self.assertTrue(any("nothing can be distilled" in f for f in fails), fails)

    def test_dropped_needs_a_reason(self):
        fails, _ = vc.check(led(row(status="dropped")), repo=self.tmp)
        self.assertTrue(any("no drop_reason" in f for f in fails), fails)
        fails2, _ = vc.check(led(row(status="dropped", drop_reason="paywalled")),
                             repo=self.tmp)
        self.assertEqual(fails2, [])

    def test_duplicate_id_is_a_failure(self):
        fails, _ = vc.check(led(row(), row()), repo=self.tmp)
        self.assertTrue(any("duplicate id" in f for f in fails), fails)

    def test_bad_id_shape_is_a_failure(self):
        fails, _ = vc.check(led(row(id="short")), repo=self.tmp)
        self.assertTrue(any("not an 11-character" in f for f in fails), fails)

    def test_g_item_outside_the_range_is_a_failure(self):
        fails, _ = vc.check(led(row(g_items=["G11"])), repo=self.tmp)
        self.assertTrue(any("outside G1..G10" in f for f in fails), fails)

    def test_empty_g_items_is_a_failure(self):
        fails, _ = vc.check(led(row(g_items=[])), repo=self.tmp)
        self.assertTrue(any("no g_items" in f for f in fails), fails)

    def test_bad_status_and_priority(self):
        fails, _ = vc.check(led(row(status="maybe", priority="urgent")), repo=self.tmp)
        self.assertTrue(any("status 'maybe'" in f for f in fails), fails)
        self.assertTrue(any("priority 'urgent'" in f for f in fails), fails)


class TestHolesHeNamed(unittest.TestCase):
    """The hole rows exist because 21 asks routed to him were dropped, not refused. Every
    expectation is a literal."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _hole(self, **over):
        h = {"id": "HOLE-01", "verbatim": "ยังไม่เห็นมี video ที่เกี่ยวกับการจัดวางของตกแต่ง",
             "named_at": "2026-08-28", "measured": "0 of 56 watched rows show an object "
                                                   "being placed on a surface",
             "answered_by": ["kmCHv3PG2XM"], "closed_at": None}
        h.update(over)
        return h

    def test_a_hole_with_nothing_queued_is_a_failure(self):
        d = {"rows": [row()], "holes_named": [self._hole(answered_by=[])]}
        fails, _ = vc.check(d, repo=self.tmp)
        self.assertTrue(any("nothing queued against it" in f for f in fails), fails)

    def test_a_hole_must_carry_his_words(self):
        d = {"rows": [row()], "holes_named": [self._hole(verbatim="")]}
        fails, _ = vc.check(d, repo=self.tmp)
        self.assertTrue(any("no verbatim" in f for f in fails), fails)

    def test_a_hole_must_carry_a_measurement(self):
        d = {"rows": [row()], "holes_named": [self._hole(measured="")]}
        fails, _ = vc.check(d, repo=self.tmp)
        self.assertTrue(any("never counted" in f for f in fails), fails)

    def test_answered_by_must_name_rows_that_exist(self):
        d = {"rows": [row()], "holes_named": [self._hole(answered_by=["AAAAAAAAAAA"])]}
        fails, _ = vc.check(d, repo=self.tmp)
        self.assertTrue(any("is not a row in this ledger" in f for f in fails), fails)

    def test_hole_state_counts_watched_and_distilled(self):
        n = self._write("notes/a.md", "kmCHv3PG2XM")
        dd = self._write("knowledge/x.md", "kmCHv3PG2XM")
        rows = [row(status="watched", watched_at="2026-08-28", notes=n, distilled_to=dd),
                row(id="Sz4TC-VJ2PQ", url="https://www.youtube.com/watch?v=Sz4TC-VJ2PQ")]
        d = {"rows": rows,
             "holes_named": [self._hole(answered_by=["kmCHv3PG2XM", "Sz4TC-VJ2PQ"])]}
        state = vc.hole_state(d)
        self.assertEqual(len(state), 1)
        _, w, dist, tot = state[0]
        self.assertEqual((w, dist, tot), (1, 1, 2))

    def test_a_closed_hole_stops_printing(self):
        d = {"rows": [row()],
             "holes_named": [self._hole(closed_at="2026-09-01")]}
        self.assertEqual(vc.hole_state(d), [])

    def _write(self, rel, body):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        return rel.replace("\\", "/")


class TestGCoverage(unittest.TestCase):
    def test_dropped_rows_do_not_count_as_coverage(self):
        d = {"rows": [row(g_items=["G1"], status="dropped", drop_reason="dup")]}
        self.assertEqual(vc.g_coverage(d)["G1"], (0, 0, 0))

    def test_a_row_feeds_every_g_item_it_names(self):
        d = {"rows": [row(g_items=["G1", "G7"], status="watched", watched_at="2026-08-28",
                          notes="n", distilled_to="k")]}
        cov = vc.g_coverage(d)
        self.assertEqual(cov["G1"], (1, 1, 1))
        self.assertEqual(cov["G7"], (1, 1, 1))
        self.assertEqual(cov["G4"], (0, 0, 0))

    def test_watched_without_distillation_counts_watched_only(self):
        d = {"rows": [row(g_items=["G2"], status="watched", watched_at="2026-08-28",
                          notes="n")]}
        self.assertEqual(vc.g_coverage(d)["G2"], (1, 1, 0))


class TestAge(unittest.TestCase):
    def test_unparseable_date_is_none_not_zero(self):
        self.assertIsNone(vc._age_days("not-a-date"))
        self.assertIsNone(vc._age_days(None))

    def test_known_span(self):
        import datetime
        self.assertEqual(vc._age_days("2026-08-01", datetime.date(2026, 8, 28)), 27)


class TestReportLines(unittest.TestCase):
    def test_unreadable_ledger_prints_unknown_not_nothing(self):
        lines = vc.report_lines(path=os.path.join(tempfile.mkdtemp(), "nope.json"))
        self.assertTrue(any("unknown" in l for l in lines), lines)
        self.assertTrue(any("not zero" in l for l in lines), lines)

    def test_counts_appear(self):
        tmp = tempfile.mkdtemp()
        p = os.path.join(tmp, "led.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(led(row(), row(id="P5aaT-QUtFU",
                                     url="https://www.youtube.com/watch?v=P5aaT-QUtFU",
                                     status="dropped", drop_reason="x")), fh)
        lines = vc.report_lines(path=p, repo=tmp)
        joined = "\n".join(lines)
        self.assertIn("VIDEO CURRICULUM 2", joined)
        self.assertIn("ตัดออก 1", joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
