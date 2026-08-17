"""Tests for warehouse.py's PURE half — the sweep planner and the shelf reader.

WHY THIS FILE EXISTS AT ALL, and the reason is a sentence this lane said out loud.
On 2026-08-17 the builder reported to the owner that the free asset tier was
"exhausted (68 models, one repository)". Measured the same hour: 68 was the whole
cache — tub chairs, towels, hung garments — of which exactly TEN ever staged as
bed cloth, and the number of bed-cloth QUERIES behind them could not be recovered
from disk at all, because `SOURCE.json` records what was downloaded and never what
was asked. R13's law one level in: not-found-in-ten is not does-not-exist, and a
claim of exhaustion that cannot be checked against the queries actually asked is
not a finding.

So the planner is tested the way this repo tests a rule that has already decided
something wrongly: with the FACTS OF THAT ROUND as fixtures, not with invented
ones.
"""
import json
import os

import pytest

import warehouse as W

# the shape `search()` returns, wrapped the way `sweep()` wraps it
def _hit(eid, q="duvet", title="t", dl=10, fmts=("glb",), b=1_000_000):
    return {"id": eid, "title": title, "downloads": dl, "fmts": list(fmts),
            "bytes": b, "query": q}


def test_plan_ranks_by_bytes_because_density_is_the_thing_the_lane_is_short_of():
    """The real numbers: every bed cover this lane auditioned is 1-3 MB and
    measures 15-124 mm median edge; the acquired PILLOWS that pass the fineness
    cut are 10.8 MB and 18.8 MB. Size is the only density signal available before
    a download, so it decides the ORDER of the queue."""
    keep, skip = W.plan_sweep(
        [_hit("small", b=1_600_000), _hit("big", b=101_000_000),
         _hit("mid", b=13_000_000)], have={})
    assert [r["id"] for r in keep] == ["big", "mid", "small"]
    assert skip == []


def test_size_never_decides_membership_unless_a_floor_is_asked_for():
    """`survives` calls an ungrounded band 'taste wearing a threshold'. A byte
    floor is exactly that, so bytes rank and never cut — until a caller says so."""
    keep, _ = W.plan_sweep([_hit("tiny", b=1)], have={})
    assert [r["id"] for r in keep] == ["tiny"]
    keep, skip = W.plan_sweep([_hit("tiny", b=1)], have={}, min_bytes=1000)
    assert keep == [] and "floor" in skip[0]["why"]


def test_a_ceiling_defers_loudly_and_is_never_a_verdict_on_the_model():
    """The top of the first real sweep was a 384 MB entity — a whole scene, not a
    bed cover. Bounding it is operational; the reason has to print (no silent
    caps), and the wording must not read as a judgement on the asset."""
    keep, skip = W.plan_sweep([_hit("huge", b=384_000_000)], have={},
                              max_bytes=140_000_000)
    assert keep == []
    assert "deferred, not judged" in skip[0]["why"]


def test_what_is_already_on_the_shelf_is_skipped_by_name_not_re_fetched():
    keep, skip = W.plan_sweep([_hit("0afd4c6f"), _hit("new")],
                              have={"0afd4c6f": "0afd4c6f-ef8f"})
    assert [r["id"] for r in keep] == ["new"]
    assert skip[0]["why"] == "already cached as 0afd4c6f-ef8f"


def test_one_model_answering_two_queries_is_fetched_once_and_both_asks_are_kept():
    """A sweep runs many queries on purpose; the same bed set comes back from
    'duvet' and from 'edredom'. Fetching it twice is waste, and DROPPING the
    second query is the provenance loss this whole change exists to stop."""
    keep, skip = W.plan_sweep(
        [_hit("dup", q="duvet"), _hit("dup", q="edredom")], have={})
    assert len(keep) == 1
    assert keep[0]["query"] == "duvet"
    assert keep[0]["also_found_by"] == ["edredom"]
    assert skip == []


def test_a_hit_with_no_glb_is_out_with_its_reason():
    keep, skip = W.plan_sweep([_hit("skponly", fmts=("skp",))], have={})
    assert keep == [] and skip[0]["why"] == "no glb binary"


def test_the_limit_cut_names_itself_so_a_shrunk_sweep_cannot_read_as_a_full_one():
    keep, skip = W.plan_sweep([_hit("a", b=3), _hit("b", b=2), _hit("c", b=1)],
                              have={}, limit=2)
    assert [r["id"] for r in keep] == ["a", "b"]
    assert [s["id"] for s in skip] == ["c"]
    assert "past --limit 2" in skip[0]["why"]


def test_a_query_that_returned_nothing_still_leaves_a_record(tmp_path):
    """THE POINT OF THE LOG. A sweep that fetches nothing is the single most
    important thing to have written down — it is the only evidence that can ever
    support 'we looked and there is nothing there'."""
    p = tmp_path / "SEARCH-LOG.json"
    W.log_sweep({"queries": ["colcha king size"], "n_hits": 0, "fetched": []},
                path=str(p))
    W.log_sweep({"queries": ["edredom king"], "n_hits": 12, "fetched": ["x"]},
                path=str(p))
    runs = json.load(open(p, encoding="utf-8"))["runs"]
    assert [r["queries"][0] for r in runs] == ["colcha king size", "edredom king"]
    assert runs[0]["fetched"] == []


def test_the_log_never_rewrites_a_prior_run(tmp_path):
    p = tmp_path / "SEARCH-LOG.json"
    W.log_sweep({"queries": ["a"]}, path=str(p))
    W.log_sweep({"queries": ["b"]}, path=str(p))
    W.log_sweep({"queries": ["c"]}, path=str(p))
    assert len(json.load(open(p, encoding="utf-8"))["runs"]) == 3


def test_cached_ids_reads_the_shelf_itself_not_the_log(tmp_path):
    """68 models predate the log entirely. The shelf is the fact."""
    for slug, eid in (("aaa", "id-a"), ("bbb", "id-b")):
        d = tmp_path / slug
        d.mkdir()
        (d / "SOURCE.json").write_text(json.dumps({"entity_id": eid}),
                                       encoding="utf-8")
    (tmp_path / "no-source").mkdir()
    assert W.cached_ids(str(tmp_path)) == {"id-a": "aaa", "id-b": "bbb"}


def test_cached_ids_survives_a_corrupt_sidecar_rather_than_refusing_the_shelf(tmp_path):
    d = tmp_path / "broken"
    d.mkdir()
    (d / "SOURCE.json").write_text("{not json", encoding="utf-8")
    ok = tmp_path / "fine"
    ok.mkdir()
    (ok / "SOURCE.json").write_text(json.dumps({"entity_id": "e"}), encoding="utf-8")
    assert W.cached_ids(str(tmp_path)) == {"e": "fine"}


def test_cached_ids_on_a_missing_cache_is_empty_not_an_exception(tmp_path):
    assert W.cached_ids(str(tmp_path / "nope")) == {}
