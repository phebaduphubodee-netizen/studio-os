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
