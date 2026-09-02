"""Tests for blenderkit.py — the PURE half (env/URL/tier/file choice/refusal
wording/fetch plan/shortlist/clock/digest/bench rect) and the EXIT CONTRACT of
main() with the network, Blender and the log stubbed. No network, no Blender,
and the real qa/blenderkit-fetch-log.json is never touched (every run points
`--log` at a temp file).

Pinned hardest: (1) a FULL-PLAN asset with no key is refused BY THE ASK'S NAME
(ASK-031) and `shortlist` exits 2 in that state, never 0; (2) a transport
failure exits 2, never a traceback; (3) the month clock starts at the first
PAID download and never at a probe; (4) the order's obeyed_assert regex is
READ FROM THE LEDGER, not copied, and matches a paid fetch record while not
matching a free fetch, a dry run, or the current real log.
"""
import datetime
import json
import os
import re
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blenderkit as BK  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _result(free=True, files=None, **kw):
    r = {"assetBaseId": "aaaa-1", "id": "vvvv-1", "name": "A Bed",
         "category": "bed", "isFree": free, "canDownload": free,
         "license": "royalty_free",
         "dictParameters": {"dimensionX": 2.1, "dimensionY": 2.3,
                            "dimensionZ": 0.9, "faceCount": 1234,
                            "simulation": True},
         "files": files if files is not None else [
             {"fileType": "blend", "downloadUrl": BK.SITE + "/api/v1/downloads/1/"},
             {"fileType": "resolution_2K", "downloadUrl": BK.SITE + "/api/v1/downloads/2/"},
             {"fileType": "thumbnail", "downloadUrl": BK.SITE + "/api/v1/downloads/3/"}]}
    r.update(kw)
    return r


class TestEnv(unittest.TestCase):
    def test_parse_env_quotes_comments_export_and_inline_tail(self):
        env = BK.parse_env('# c\nexport A="x y"\nB=\'z\'\nC=plain # tail\nD="q" # c\n\nE\n')
        self.assertEqual(env["A"], "x y")
        self.assertEqual(env["B"], "z")
        self.assertEqual(env["C"], "plain")        # dotenv semantics: tail dropped
        self.assertEqual(env["D"], "q")
        self.assertNotIn("E", env)

    def test_headers_carry_bearer_only_with_key(self):
        self.assertNotIn("Authorization", BK.headers(None))
        self.assertEqual(BK.headers("k")["Authorization"], "Bearer k")

    def test_on_site_guards_the_key(self):
        self.assertTrue(BK.on_site(BK.SITE + "/api/v1/downloads/1/"))
        self.assertFalse(BK.on_site("https://evil.example/api/v1/downloads/1/"))
        self.assertFalse(BK.on_site(None))


class TestSearchUrl(unittest.TestCase):
    def test_tokens_joined_with_plus_and_qualifiers_kept(self):
        u = BK.search_url("asset_type:model  bed modern", page=2, page_size=50)
        self.assertIn("query=asset_type:model+bed+modern", u)
        self.assertIn("&page_size=50&page=2", u)


class TestRows(unittest.TestCase):
    def test_tier_and_row(self):
        r = BK.row_of(_result(free=False))
        self.assertEqual(r["tier"], "full_plan")
        self.assertEqual((r["dim_x_m"], r["faceCount"]), (2.1, 1234))
        self.assertEqual(BK.tier_of(_result(free=True)), "free")

    def test_file_entry_by_resolution(self):
        r = _result()
        self.assertEqual(BK.file_entry(r)["fileType"], "blend")
        self.assertEqual(BK.file_entry(r, "2K")["fileType"], "resolution_2K")
        self.assertIsNone(BK.file_entry(r, "1K"))
        with self.assertRaises(ValueError):
            BK.file_entry(r, "8K")


class TestRefusal(unittest.TestCase):
    def test_full_plan_without_key_names_the_ask_and_the_glimpse(self):
        m = BK.refusal(401, "full_plan", has_key=False)
        self.assertIn("ASK-031", m)
        self.assertIn(BK.KEY_NAME, m)
        self.assertIn("30 day glimpse", m)
        self.assertIn("$19.90", m)

    def test_free_without_key_is_not_a_plan_question(self):
        self.assertNotIn("ASK-031", BK.refusal(403, "free", has_key=False))

    def test_with_key_points_at_the_plan(self):
        self.assertIn("lapsed", BK.refusal(401, "full_plan", has_key=True))

    def test_exit_codes_404_is_an_answer_everything_else_could_not_run(self):
        self.assertEqual(BK.exit_code_for(404), 1)
        for st in (401, 403, 429, 500, 503, 0):
            self.assertEqual(BK.exit_code_for(st), 2, st)
        self.assertIn("rate-limited", BK.refusal(429, "free", True))
        self.assertIn("outage", BK.refusal(503, "free", True))


class TestPlanFetch(unittest.TestCase):
    ROWS = [{"assetBaseId": "a", "id": "va", "tier": "free"},
            {"assetBaseId": "b-1", "id": "vb", "tier": "full_plan"},
            {"assetBaseId": "c", "id": "vc", "tier": "full_plan"},
            {"assetBaseId": "d", "id": "vd", "tier": "free"}]

    def test_no_key_skips_every_full_plan_row_by_name(self):
        keep, skip = BK.plan_fetch(self.ROWS, {}, has_key=False)
        self.assertEqual([r["assetBaseId"] for r in keep], ["a", "d"])
        self.assertTrue(all("ASK-031" in s["why"] for s in skip))

    def test_cached_matches_base_dehyphened_and_version_ids(self):
        keep, skip = BK.plan_fetch(self.ROWS, {"b1": "dir-b", "vd": "dir-d"}, has_key=True)
        self.assertEqual([r["assetBaseId"] for r in keep], ["a", "c"])
        self.assertEqual([s["why"] for s in skip],
                         ["already cached as dir-b", "already cached as dir-d"])

    def test_limit_is_logged_not_silent(self):
        keep, skip = BK.plan_fetch(self.ROWS, {}, has_key=True, limit=1)
        self.assertEqual(len(keep), 1)
        self.assertEqual(sum(1 for s in skip if "past --limit" in s["why"]), 3)


class TestShortlistRows(unittest.TestCase):
    SL = {"ranked": [{"assetBaseId": "1", "tier": "full_plan", "bench_worthy": True},
                     {"assetBaseId": "2", "tier": "free", "bench_worthy": True},
                     {"assetBaseId": "3", "tier": "full_plan", "bench_worthy": False},
                     {"assetBaseId": "4", "tier": "full_plan", "bench_worthy": True}]}

    def test_bench_worthy_of_tier_in_rank_order(self):
        self.assertEqual([r["assetBaseId"] for r in BK.shortlist_rows(self.SL)], ["1", "4"])
        self.assertEqual([r["assetBaseId"] for r in BK.shortlist_rows(self.SL, "free")], ["2"])
        self.assertEqual(BK.shortlist_rows({}), [])


class TestMonthClock(unittest.TestCase):
    def test_not_started_by_free_fetch_dry_run_or_unfetched_paid(self):
        runs = [{"date_local": "2026-08-22", "tier": "free", "fetched": True},
                {"date_local": "2026-08-23", "tier": "full_plan", "fetched": False},
                {"date_local": "2026-08-23", "tier": "full_plan", "fetched": True, "probe": True}]
        self.assertIsNone(BK.month_clock(runs, datetime.date(2026, 8, 30)))

    def test_starts_at_first_paid_download_local_date(self):
        runs = [{"date_local": "2026-08-25", "at": "2026-08-26T01:00:00+00:00",
                 "tier": "full_plan", "fetched": True},
                {"date_local": "2026-08-24", "tier": "full_plan", "fetched": True},
                {"at": "2026-08-01T10:00:00+00:00", "tier": "free", "fetched": True}]
        first, elapsed, left = BK.month_clock(runs, datetime.date(2026, 9, 3))
        self.assertEqual(first, datetime.date(2026, 8, 24))
        self.assertEqual((elapsed, left), (10, 20))


class TestBenchRectAndDigest(unittest.TestCase):
    def test_bench_rect_is_derived_from_the_single_bed_item(self):
        spec = {"items": [{"kind": "rug", "x": 1}, {"kind": "bed", "x": 3204, "y": 226,
                                                    "w": 2000, "d": 1800}]}
        self.assertEqual(BK.bench_rect(spec), "3204,226,2000,1800")
        self.assertIsNone(BK.bench_rect({"items": []}))
        self.assertIsNone(BK.bench_rect({"items": [{"kind": "bed"}, {"kind": "bed"}]}))
        self.assertIsNone(BK.bench_rect({"items": [{"kind": "bed", "x": "?"}]}))

    def test_live_spec_yields_the_d114_rect_not_the_retired_one(self):
        rect = BK.bench_rect(BK.read_spec())
        self.assertIsNotNone(rect)
        self.assertNotEqual(rect, "3204,51,2000,2149")

    def test_digest_changes_with_any_of_its_three_inputs(self):
        a = BK.criteria_digest("x", b"c", b"p")
        self.assertNotEqual(a, BK.criteria_digest("y", b"c", b"p"))
        self.assertNotEqual(a, BK.criteria_digest("x", b"d", b"p"))
        self.assertNotEqual(a, BK.criteria_digest("x", b"c", b"q"))
        self.assertEqual(a, BK.criteria_digest("x", b"c", b"p"))

    def test_me_summary_is_scalar_plan_fields_only(self):
        s = BK.me_summary({"user": {"email": "x@y", "currentPlanName": "Full",
                                    "subscription": {"nested": 1}, "plan": 7}})
        self.assertEqual(s, {"currentPlanName": "Full", "plan": "7"})

    def test_scrub_strips_local_paths(self):
        self.assertNotIn("teza_", BK.scrub(r"C:\Users\teza_\x\y.json missing"))
        self.assertNotIn("_private/", BK.scrub("no _private/deliv-001/a.json"))


class TestKeyLine(unittest.TestCase):
    KEY = "abcdef0123456789abcdef0123456789"

    def test_replaces_existing_line_keeps_the_rest_and_newline_style(self):
        body = "A=1\r\nBLENDERKIT_API_KEY=old\r\nB=2\r\n"
        out = BK.upsert_env_line(body, "BLENDERKIT_API_KEY", self.KEY)
        self.assertEqual(out, f"A=1\r\nBLENDERKIT_API_KEY={self.KEY}\r\nB=2\r\n")

    def test_fills_the_commented_placeholder_or_appends(self):
        out = BK.upsert_env_line("# BLENDERKIT_API_KEY=\nX=1\n", "BLENDERKIT_API_KEY", self.KEY)
        self.assertEqual(out, f"BLENDERKIT_API_KEY={self.KEY}\nX=1\n")
        out = BK.upsert_env_line("X=1", "BLENDERKIT_API_KEY", self.KEY)
        self.assertTrue(out.startswith("X=1\n\n#"))
        self.assertTrue(out.endswith(f"BLENDERKIT_API_KEY={self.KEY}\n"))
        self.assertEqual(BK.parse_env(out)["BLENDERKIT_API_KEY"], self.KEY)

    def test_pick_addon_key_finds_legacy_or_extension_module(self):
        rows = [["io_scene_gltf2", None], ["bl_ext.blender_org.blenderkit", " k-1 "],
                ["blenderkit", "k-2"]]
        self.assertEqual(BK.pick_addon_key(rows), "k-1")
        self.assertIsNone(BK.pick_addon_key([["blenderkit", ""], ["other", "x"]]))
        self.assertIsNone(BK.pick_addon_key([]))

    def test_refuses_a_pasted_key_with_a_tail_space_or_quotes(self):
        for bad in ("abc", self.KEY + " # note", '"' + self.KEY + '"', self.KEY + " x", ""):
            with self.assertRaises(BK.Refused, msg=bad) as cm:
                BK.upsert_env_line("", "BLENDERKIT_API_KEY", bad)
            self.assertEqual(cm.exception.code, 1)


class TestOAuthPure(unittest.TestCase):
    def test_pkce_pair_matches_the_addon_shape(self):
        import base64, hashlib
        v, c = BK.pkce_pair()
        self.assertEqual(len(v), 128)
        self.assertTrue(v.isalnum())
        self.assertNotIn("=", c)
        self.assertEqual(c, base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest())
                         .decode().replace("=", ""))

    def test_authorize_url_carries_every_addon_parameter(self):
        u = BK.authorize_url(62485, "st", "ch", "000000000000001")
        self.assertTrue(u.startswith(BK.SITE + "/o/authorize?client_id=" + BK.OAUTH_CLIENT_ID))
        for part in ("response_type=code", "state=st", "redirect_uri=http://localhost:62485/consumer/exchange/",
                     "code_challenge=ch", "code_challenge_method=S256", "system_id=000000000000001"):
            self.assertIn(part, u)

    def test_parse_callback_accepts_only_a_matching_state(self):
        self.assertEqual(BK.parse_callback("/consumer/exchange/?code=abc&state=s1", "s1"), ("code", "abc"))
        self.assertEqual(BK.parse_callback("/consumer/exchange/?code=abc&state=s2", "s1")[0], "error")
        self.assertEqual(BK.parse_callback("/consumer/exchange/?error=access_denied", "s1")[0], "error")
        self.assertEqual(BK.parse_callback("/other?code=abc&state=s1", "s1")[0], "error")
        self.assertEqual(BK.parse_callback("/consumer/exchange/?state=s1", "s1")[0], "error")

    def test_needs_refresh_margin(self):
        self.assertFalse(BK.needs_refresh(1000 + 601, 1000))
        self.assertTrue(BK.needs_refresh(1000 + 599, 1000))
        self.assertTrue(BK.needs_refresh(None, 1000))

    def test_write_key_stores_refresh_and_expiry_lines(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write("A=1\n")
            k = "k" * 32
            BK.write_key(k, repo=d, refresh="r" * 32, expires=1234.9)
            env = BK.parse_env(open(os.path.join(d, ".env"), encoding="utf-8").read())
            self.assertEqual((env["A"], env[BK.KEY_NAME], env[BK.REFRESH_NAME], env[BK.EXPIRES_NAME]),
                             ("1", k, "r" * 32, "1234"))
            self.assertEqual(BK.read_refresh(d), ("r" * 32, "1234"))


class TestBenchHelpers(unittest.TestCase):
    def test_latest_built_blend_picks_highest_round_not_playblast(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ("room_bedroom_suite_eye_p2r56.blend", "room_bedroom_suite_eye_p2r57.blend",
                      "room_bedroom_suite_eye_p2r58q_ql.blend", "room_bedroom_suite_eye_bed_hero_ql.blend"):
                open(os.path.join(d, n), "w").close()
            self.assertTrue(BK.latest_built_blend(d).endswith("p2r57.blend"))
            self.assertIsNone(BK.latest_built_blend(os.path.join(d, "nope")))

    def test_last_asserted_ids_skips_probes_and_empty_runs(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "log.json")
            BK.log_run({"cmd": "shortlist", "probe": False, "asserted_ids": ["a"]}, p)
            BK.log_run({"cmd": "shortlist", "probe": True, "asserted_ids": ["z"]}, p)
            BK.log_run({"cmd": "shortlist", "probe": False, "asserted_ids": []}, p)
            self.assertEqual(BK.last_asserted_ids(p), ["a"])

    def test_bench_cmd_shape(self):
        cmd = BK.bench_cmd("blender.exe", "r.blend", "out", "1,2,3,4", ["x", "y"], cache="c")
        self.assertEqual(cmd[:4], ["blender.exe", "-b", "r.blend", "--python"])
        self.assertTrue(cmd[4].endswith("wholebed_bench.py"))
        self.assertEqual(cmd[5:], ["--", "c", "out", "1,2,3,4", "x,y"])


class TestCacheAndLog(unittest.TestCase):
    def test_cached_ids_indexes_every_id_form_and_counts_by_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            for name, body, side in (
                    ("x-1", {"asset_base_id": "x-1", "asset_version_id": "vx", "tier": "full_plan"}, {"ok": True}),
                    ("y", {"asset_id": "y-2"}, {"ok": False}),
                    ("z", {"name": "no id"}, None)):
                os.makedirs(os.path.join(d, name))
                with open(os.path.join(d, name, "SOURCE.json"), "w") as fh:
                    json.dump(body, fh)
                if side is not None:
                    with open(os.path.join(d, name, f"{name}.scale.json"), "w") as fh:
                        json.dump(side, fh)
            os.makedirs(os.path.join(d, "no-source"))
            ids = BK.cached_ids(d)
            self.assertEqual(ids["x-1"], "x-1")
            self.assertEqual(ids["x1"], "x-1")
            self.assertEqual(ids["vx"], "x-1")
            self.assertEqual(ids["y-2"], "y")
            self.assertEqual(ids["y2"], "y")
            self.assertEqual(BK.shelf_counts(d)["full_plan"]["asserted"], 1)
            self.assertEqual(BK.shelf_counts(d)["free"],
                             {"asserted": 0, "refused": 1, "unasserted": 1})

    def test_log_run_appends_atomically_and_refuses_a_corrupt_log(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "log.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"_what": "hand-written"}, fh)
            BK.log_run({"at": "t1", "fetched": False}, p)
            BK.log_run({"at": "t2", "fetched": True, "tier": "full_plan"}, p)
            with open(p, encoding="utf-8") as fh:
                got = json.load(fh)
            self.assertEqual(got["_what"], "hand-written")
            self.assertEqual([r["at"] for r in got["runs"]], ["t1", "t2"])
            self.assertFalse(os.path.exists(p + ".tmp"))
            with open(p, "w", encoding="utf-8") as fh:
                fh.write('{"runs": [truncated')
            with self.assertRaises(BK.Refused) as cm:
                BK.log_run({"at": "t3"}, p)
            self.assertEqual(cm.exception.code, 2)
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), '{"runs": [truncated')   # untouched

    def test_export_cmd_has_factory_startup_and_autoexec_off(self):
        cmd = BK.export_cmd("blender.exe", "a.blend", "x.py", "a.glb")
        self.assertEqual(cmd[:5], ["blender.exe", "-b", "--factory-startup", "-Y", "-noaudio"])
        self.assertEqual(cmd[-1], "a.glb")

    def test_export_script_raises_subsurf_to_render_levels_before_baking(self):
        """STUDY-D11b: export_apply bakes through the viewport depsgraph, so the
        script must lift viewport levels to render_levels BEFORE the export
        call, on SUBSURF and MULTIRES, and print the count. Executed against a
        fake bpy so the ORDER of the two statements is what is pinned."""
        src = BK.EXPORT_SCRIPT
        self.assertLess(src.index("m.levels = m.render_levels"),
                        src.index("bpy.ops.export_scene.gltf("))
        self.assertIn("'MULTIRES'", src)
        self.assertIn("export_apply=True", src)
        compile(src, "<EXPORT_SCRIPT>", "exec")     # it is a valid program

        class _M:
            def __init__(s, t, lv, rl):
                s.type, s.levels, s.render_levels = t, lv, rl

        class _O:
            def __init__(s, mods):
                s.modifiers = mods
        mods = [_M("SUBSURF", 1, 2), _M("MULTIRES", 1, 3), _M("BEVEL", 0, 0),
                _M("SUBSURF", 2, 2)]
        calls = []

        class _NS:
            def __getattr__(s, k):
                return _NS()

            def __call__(s, *a, **kw):
                calls.append(kw)
                return {"FINISHED"}
        fake_bpy = type("bpy", (), {"data": type("d", (), {"objects": [_O(mods)]})(),
                                    "ops": _NS()})()
        printed = []
        saved_argv = sys.argv
        sys.modules["bpy"], sys.argv = fake_bpy, ["x", "--", "o.glb"]
        try:
            exec(compile(src, "<EXPORT_SCRIPT>", "exec"), {"print": printed.append})
        finally:
            del sys.modules["bpy"]
            sys.argv = saved_argv
        self.assertEqual([m.levels for m in mods], [2, 3, 0, 2])   # bevel untouched
        self.assertEqual(printed, ["EXPORT_GLB subsurf_raised_to_render_levels=2"])
        self.assertEqual(calls[-1]["export_apply"], True)
        self.assertEqual(calls[-1]["filepath"], "o.glb")
        self.assertIn(BK.EXPORT_BAKE, "subsurf@render_levels")


class TestOrderAssertion(unittest.TestCase):
    """The ORDER's obeyed_assert pattern is read from the ledger row, run on a
    record this module writes, and must match only a real paid fetch."""

    def _pattern(self):
        with open(os.path.join(REPO, "qa", "owner-orders.json"), encoding="utf-8") as fh:
            rows = json.load(fh)["orders"]
        row = next(o for o in rows if o["id"] == BK.ORDER)
        a = next(x for x in row["obeyed_assert"] if x["file"].endswith("blenderkit-fetch-log.json"))
        return a["pattern"]

    def _log_text(self, records):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "log.json")
            for r in records:
                BK.log_run(r, p)
            with open(p, encoding="utf-8") as fh:
                return fh.read()

    def test_matches_a_paid_fetch_only(self):
        pat = self._pattern()
        paid = BK._record("fetch", "k", asset="a", tier="full_plan", fetched=True)
        free = BK._record("fetch", None, asset="b", tier="free", fetched=True)
        dry = BK._record("shortlist", "k", probe=True, tier="full_plan", fetched=False)
        paid_probe = BK._record("shortlist", "k", probe=True, tier="full_plan", fetched=True)
        self.assertIsNotNone(re.search(pat, self._log_text([paid]), re.M))
        self.assertIsNone(re.search(pat, self._log_text([free, dry, paid_probe]), re.M))

    def test_the_real_ledger_agrees_with_the_real_log(self):
        """Once the real log carries a paid download (2026-08-22 23:51, the
        first ten full-plan beds), the order row may stay NOT-OBEYED only while
        another of its assertions still fails (the month's answer section) —
        which is exactly what orders_check enforces. So the invariant is: the
        committed ledger raises no violation on this row, whatever the log says."""
        import orders_check as OC
        data = OC.load(repo_root=REPO)
        bad = [v for v in OC.check_orders(data, REPO) if BK.ORDER in v]
        self.assertEqual(bad, [])
        pat = self._pattern()
        with open(os.path.join(REPO, "qa", "blenderkit-fetch-log.json"), encoding="utf-8") as fh:
            paid = re.search(pat, fh.read(), re.M) is not None
        row = next(o for o in data["orders"] if o["id"] == BK.ORDER)
        if row.get("status") == "obeyed":
            self.assertTrue(paid, "obeyed without a paid download on record")


class TestMainExitContract(unittest.TestCase):
    """main() with the edges stubbed: no network, no Blender, temp log."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "log.json")
        self.cache = os.path.join(self.tmp.name, "cache")
        os.makedirs(self.cache)
        self._saved = (BK.read_key, BK._get_json, BK.find_blender, BK.CACHE, BK.SHORTLIST)
        BK.CACHE = self.cache
        sl = os.path.join(self.tmp.name, "shortlist.json")
        with open(sl, "w", encoding="utf-8") as fh:
            json.dump({"ranked": [{"assetBaseId": "p-1", "id": "v1", "tier": "full_plan",
                                   "bench_worthy": True, "name": "Paid bed"}]}, fh)
        BK.SHORTLIST = sl

    def tearDown(self):
        BK.read_key, BK._get_json, BK.find_blender, BK.CACHE, BK.SHORTLIST = self._saved
        self.tmp.cleanup()

    def _runs(self):
        with open(self.log, encoding="utf-8") as fh:
            return json.load(fh)["runs"]

    def test_shortlist_without_key_exits_2_and_names_the_ask(self):
        BK.read_key = lambda repo=None: None
        self.assertEqual(BK.main(["--log", self.log, "shortlist"]), 2)
        runs = self._runs()
        self.assertEqual(runs[0]["cmd"], "shortlist")
        self.assertIn("ASK-031", runs[0]["refusals"]["*"])
        self.assertFalse(runs[0]["fetched"])

    def test_shortlist_dry_run_is_a_probe_and_exits_0(self):
        BK.read_key = lambda repo=None: None
        self.assertEqual(BK.main(["--log", self.log, "shortlist", "--dry-run"]), 0)
        self.assertTrue(self._runs()[0]["probe"])

    def test_status_without_key_exits_2(self):
        BK.read_key = lambda repo=None: None
        self.assertEqual(BK.main(["--log", self.log, "status"]), 2)

    def test_status_with_refused_key_exits_2(self):
        BK.read_key = lambda repo=None: "bad"
        BK._get_json = lambda url, key=None, timeout=60: (401, {"detail": "Invalid token."})
        self.assertEqual(BK.main(["--log", self.log, "status"]), 2)

    def test_transport_failure_exits_2_not_traceback(self):
        """Stubbed at urlopen, so the REAL _get_json does the conversion."""
        BK.read_key = lambda repo=None: None

        def boom(*a, **k):
            raise urllib.error.URLError("dns down")
        saved = BK.urllib.request.urlopen
        BK.urllib.request.urlopen = boom
        try:
            self.assertEqual(BK.main(["--log", self.log, "search", "bed"]), 2)
        finally:
            BK.urllib.request.urlopen = saved
        self.assertIn("could not reach", self._runs()[0]["refusal"])

    def test_shortlist_without_key_logs_one_row_not_two(self):
        BK.read_key = lambda repo=None: None
        self.assertEqual(BK.main(["--log", self.log, "shortlist"]), 2)
        runs = self._runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["exit"], 2)

    def test_full_plan_fetch_without_key_exits_2_by_name_and_leaves_no_dir(self):
        BK.read_key = lambda repo=None: None
        BK.find_blender = lambda: "blender.exe"
        paid = _result(free=False, assetBaseId="p-1")

        def fake(url, key=None, timeout=60):
            if "/search/" in url:
                return 200, {"results": [paid], "next": None}
            return 401, {"detail": "Unauthorized access. Please log in."}
        BK._get_json = fake
        self.assertEqual(BK.main(["--log", self.log, "fetch", "p-1"]), 2)
        self.assertIn("ASK-031", self._runs()[0]["refusal"])
        self.assertFalse(os.path.exists(os.path.join(self.cache, "p-1")))

    def test_bad_key_stops_the_walk_after_one_refusal(self):
        BK.read_key = lambda repo=None: "bad"
        BK.find_blender = lambda: "blender.exe"
        calls = []

        def fake(url, key=None, timeout=60):
            calls.append(url)
            return 401, {"detail": "Invalid token."}
        BK._get_json = fake
        self.assertEqual(BK.main(["--log", self.log, "shortlist"]), 2)
        self.assertEqual(len(calls), 1)
        self.assertIn("lapsed", self._runs()[0]["refusals"]["p-1"]["why"])


class TestResultsAreOutsideTheFreeze(unittest.TestCase):
    """The split of 2026-08-24: RUNNING the test must not edit the test.

    Before the split, recording one `free_baseline` — the very next step the criteria
    file's own protocol prescribes — moved the digest and made `status` print
    "CHANGED SINCE THE CLOCK STARTED ... the flattering-scorer defect". These tests pin
    both halves: recording a result is invisible to the hash, and CHANGING THE TEST
    (a query, a control flag, the pass rule, or adding a class) is still caught.
    """

    def _classes(self):
        with open(BK.CLASSES, encoding="utf-8") as fh:
            return json.load(fh)

    def _digest_for(self, obj):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "classes.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
            return BK.current_digest(classes_path=p)

    def test_recording_a_result_does_not_touch_the_criteria_file(self):
        """The results file is a separate path; the digest never reads it."""
        before = BK.current_digest()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "results.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"classes": {"cushion_throw": {"free_baseline": "0 of 20"}}}, fh)
            self.assertEqual(BK.load_results(p)["classes"]["cushion_throw"]["free_baseline"],
                             "0 of 20")
        self.assertEqual(before, BK.current_digest())

    def test_missing_results_file_is_empty_not_an_error(self):
        self.assertEqual(BK.load_results(os.path.join(tempfile.gettempdir(),
                                                      "no-such-results.json")), {})

    def test_editing_a_query_still_flips_the_digest(self):
        """NEGATIVE CONTROL. Loosening a freeze is the flattering-scorer move; this
        proves the freeze was not loosened, only relieved of the results.

        Both sides are re-serialised the same way, because the digest is over BYTES:
        comparing a re-emitted file against the on-disk one measures the JSON writer,
        not the edit. (That byte-sensitivity is itself real and deliberate — a
        whitespace reformat of the criteria file flips the freeze, which is the
        conservative direction for a freeze to be wrong in.)"""
        base = self._classes()
        edited = json.loads(json.dumps(base))
        edited["classes"][0]["queries"].append("asset_type:model+something+new")
        self.assertNotEqual(self._digest_for(edited), self._digest_for(base))

    def test_adding_a_class_still_flips_the_digest(self):
        """Choosing the test set after seeing results is exactly what must be caught,
        so the owner's new object classes go in `out_of_test`, never in here."""
        edited = json.loads(json.dumps(self._classes()))
        edited["classes"].append({"key": "table_lamp", "control": False,
                                  "asset_scale_class": "table_lamp",
                                  "queries": ["asset_type:model+table+lamp"],
                                  "free_baseline": None, "paid_result": None})
        self.assertNotEqual(self._digest_for(edited), self._digest_for(self._classes()))

    def test_changing_the_pass_rule_still_flips_the_digest(self):
        edited = json.loads(json.dumps(self._classes()))
        edited["_pass_rule"] = edited["_pass_rule"].replace(">= 3", ">= 1")
        self.assertNotEqual(self._digest_for(edited), self._digest_for(self._classes()))

    def test_the_real_results_file_declares_its_out_of_test_classes(self):
        """A class recorded here that is NOT pre-registered must be visibly fenced off."""
        res = BK.load_results()
        if not res:
            self.skipTest("no results recorded yet")
        registered = {c["key"] for c in self._classes()["classes"]}
        for key in (res.get("classes") or {}):
            self.assertIn(key, registered,
                          f"{key} is recorded as C2 evidence but was never "
                          f"pre-registered — it belongs under `out_of_test`")
        self.assertIn("out_of_test", res)


class TestInstrumentFreeze(unittest.TestCase):
    """D-120's recorded blind spot, closed 2026-08-24.

    Half of C2's pass rule is "passes dim_check in its asset_scale class". The criteria
    digest hashes no code, so widening a band moved that criterion while `status` kept
    printing MATCH. Five of the seven classes still need bands WRITTEN before their first
    paid fetch — the moment a widened band is most tempting and least visible.
    """

    def _asc(self):
        import asset_scale
        return asset_scale

    def test_the_shipped_instrument_matches_its_stamp(self):
        self.assertEqual(BK.instrument_digest(), BK.INSTRUMENT_FROZEN_SHA,
                         "BANDS or MIN_DEPTH_RATIO moved without re-stamping "
                         "INSTRUMENT_FROZEN_SHA and saying which band and why")

    def test_widening_a_band_is_caught(self):
        a = self._asc()
        wide = dict(a.BANDS)
        wide["nightstand"] = (300.0, 900.0, "z", "widened with no source")
        self.assertNotEqual(BK.instrument_digest(wide, a.MIN_DEPTH_RATIO),
                            BK.INSTRUMENT_FROZEN_SHA)

    def test_adding_a_band_is_caught(self):
        a = self._asc()
        more = dict(a.BANDS)
        more["book_stack"] = (20.0, 200.0, "z", "a new class")
        self.assertNotEqual(BK.instrument_digest(more, a.MIN_DEPTH_RATIO),
                            BK.INSTRUMENT_FROZEN_SHA)

    def test_relaxing_a_depth_ratio_is_caught(self):
        """The planar refusal is the other half of the assert; relaxing it lets a cutout
        through as a solid, which is the D-109 defect class."""
        a = self._asc()
        r = dict(a.MIN_DEPTH_RATIO)
        r[sorted(r)[0]] = 0.01
        self.assertNotEqual(BK.instrument_digest(a.BANDS, r),
                            BK.INSTRUMENT_FROZEN_SHA)

    def test_it_is_honest_that_it_started_late(self):
        """It cannot speak for 08-22..08-24 and must not imply it can."""
        self.assertEqual(BK.INSTRUMENT_FROZEN_AT, "2026-08-24")
        self.assertNotEqual(BK.INSTRUMENT_FROZEN_AT, "2026-08-22")

    def test_the_two_digests_are_independent(self):
        """Re-stamping the instrument must never touch the criteria evidence, which was
        stamped at the clock start and is the only proof the criteria did not move."""
        a = self._asc()
        wide = dict(a.BANDS)
        wide["nightstand"] = (300.0, 900.0, "z", "widened")
        before = BK.current_digest()
        BK.instrument_digest(wide, a.MIN_DEPTH_RATIO)
        self.assertEqual(before, BK.current_digest())


class BaselineOrderIsARefusal(unittest.TestCase):
    """p2r86: three paid `hung_garments` were fetched before that class's free
    baseline, permanently contaminating it for the month's own C2 criterion. The
    protocol had been correct and PRINTED (in `status`) the whole time. These pin
    that it is now a REFUSAL, and that the refusal sits on the fetch path itself —
    not in a sibling command nobody is obliged to run."""

    def _classes(self, baseline=None, key="hung_garments", scale="garment_hung"):
        """A classes file in the p2r86 SHAPE, built from the real one so a schema
        change here is a test failure and not a silent pass."""
        with open(BK.CLASSES, encoding="utf-8") as fh:
            real = json.load(fh)
        row = next(c for c in real["classes"] if c.get("key") == key)
        row = dict(row, asset_scale_class=scale, free_baseline=baseline)
        real["classes"] = [row]
        d = tempfile.mkdtemp()
        path = os.path.join(d, "classes.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(real, fh)
        return path

    def _results(self, blob=None):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "results.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(blob or {}, fh)
        return path

    def test_the_p2r86_fetch_is_refused(self):
        why = BK.baseline_refusal("garment_hung", "full_plan",
                                  self._classes(), self._results())
        self.assertIsNotNone(why)
        self.assertIn("hung_garments", why)
        self.assertIn(BK.ORDER, why)
        self.assertIn("DOES NOT COUNT", why)

    def test_a_free_fetch_in_the_same_class_is_allowed(self):
        """The order is about the ORDER of measurement, not about spending. Running
        the free tier IS the baseline, so it can never be what the guard blocks."""
        self.assertIsNone(BK.baseline_refusal("garment_hung", "free",
                                              self._classes(), self._results()))

    def test_a_recorded_baseline_opens_the_class(self):
        rec = {"panel_passes": 0, "of": 20}
        self.assertIsNone(BK.baseline_refusal("garment_hung", "full_plan",
                                              self._classes(baseline=rec),
                                              self._results()))

    def test_the_baseline_may_live_in_the_unhashed_results_file(self):
        """Filling it in CLASSES moves the criteria digest (measured 2026-08-24), so
        the protocol writes results to the unhashed file. The guard must read BOTH or
        it would refuse every class that obeyed the freeze correctly."""
        res = self._results({"classes": {"hung_garments":
                                         {"free_baseline": {"panel_passes": 0}}}})
        self.assertIsNone(BK.baseline_refusal("garment_hung", "full_plan",
                                              self._classes(), res))

    def test_an_out_of_test_class_is_not_the_guards_business(self):
        """`book_stack` was never pre-registered; status already prints those as
        OUT-OF-TEST. A guard that blocked them would be inventing a rule."""
        self.assertIsNone(BK.baseline_refusal("book_stack", "full_plan",
                                              self._classes(), self._results()))

    def test_an_unclassed_paid_fetch_is_refused_by_r8(self):
        """The guard's own bypass: no class name, no join, no refusal. R8 already
        forbids it (scale is ASSERTED on every ingest)."""
        why = BK.baseline_refusal(None, "full_plan", self._classes(), self._results())
        self.assertIsNotNone(why)
        self.assertIn("R8", why)
        self.assertIsNone(BK.baseline_refusal(None, "free",
                                              self._classes(), self._results()))

    def test_the_refusal_is_ON_THE_FETCH_PATH(self):
        """The whole defect was a correct check wired to a command nobody had to run.
        So: call fetch() itself with a PAID result and no baseline, and prove it
        raises before a directory, a download or a Blender lookup happens."""
        cache = tempfile.mkdtemp()
        calls = []
        real_find = BK.find_blender
        BK.find_blender = lambda *a, **k: calls.append("blender")
        try:
            with self.assertRaises(BK.Refused) as cm:
                BK.fetch("aaaa-1", key="k", cls="garment_hung", cache=cache,
                         result=_result(free=False))
        finally:
            BK.find_blender = real_find
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("hung_garments", str(cm.exception))
        self.assertEqual(calls, [])
        self.assertEqual(os.listdir(cache), [])


if __name__ == "__main__":
    unittest.main()
