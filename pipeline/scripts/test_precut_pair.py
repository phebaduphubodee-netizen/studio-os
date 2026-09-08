"""Tests + mutation probes for precut_pair.py.

Fixtures are SYNTHETIC (fake precut.json, fake worksheet, zero-byte render files, fake I-codes)
so nothing here touches the real client pool -- committed and CI-runnable without _private/.

The two REFUSALS under test are the lane's whole point (qa/benchmark-sellability.md):
an anchor pairs ONLY on designer-typed labels; the machine never invents room_type or
is_delivered. Every test that guards a refusal is mutation-probed: break the refusal in a
monkeypatched copy and watch the guard actually catch it (baseline pinned first, per repo law).
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precut_pair as P  # noqa: E402


# --------------------------------------------------------------------------- fixtures
def fake_precut(tmp_path):
    """2 fake projects: X-99-001 (3 distinct bedroom-ish anchors + 1 dup + 1 photo-suspect),
    X-99-002 (2 anchors). Paths are tmp files so nothing needs the real pool."""
    def anchor(icode, thread, h, maxdim, dup_of=None):
        p = tmp_path / f"{icode}_{thread}_{h}.jpg"
        p.write_bytes(b"x")
        return {"path": str(p), "ref": f"{icode}/{thread}/{h}.jpg", "thread": thread,
                "maxdim": maxdim, "wh": [maxdim, maxdim // 2], "engine": None,
                "room_hint": None, "delivery_signal": "update-thread (proposed, unconfirmed)",
                "dup_of": dup_of}

    a1 = anchor("X-99-001", "002", "aaaa1111", 5000)
    a2 = anchor("X-99-001", "002", "bbbb2222", 4000)
    a3 = anchor("X-99-001", "003", "cccc3333", 3500)
    dup = anchor("X-99-001", "002", "dddd4444", 3000, dup_of=a1["ref"])
    sus = anchor("X-99-001", "004", "eeee5555", 2500)
    b1 = anchor("X-99-002", "001", "ffff6666", 4500)
    b2 = anchor("X-99-002", "001", "gggg7777", 2600)
    pc = {"generated_by": "benchmark_precut.py", "photo_suspect": [{"ref": sus["ref"]}],
          "projects": [
              {"icode": "X-99-001", "anchors": [a1, a2, a3, dup, sus]},
              {"icode": "X-99-002", "anchors": [b1, b2]},
          ]}
    path = tmp_path / "precut.json"
    path.write_text(json.dumps(pc), encoding="utf-8")
    return path, dict(a1=a1, a2=a2, a3=a3, dup=dup, sus=sus, b1=b1, b2=b2)


def fake_worksheet(tmp_path, lines):
    ws = tmp_path / "precut-worksheet.md"
    ws.write_text("\n".join(lines), encoding="utf-8")
    return ws


def fake_renders(tmp_path, names=("R_PRJ002_MasterSuite_Cam01_v01.png",
                                  "R_PRJ002_MasterSuite_Cam02_v01.png",
                                  "R_PRJ002_MasterSuite_Cam02_v04.png",
                                  "R_PRJ002_SittingRoom_Cam01_v01.png")):
    rd = tmp_path / "renders"
    rd.mkdir(exist_ok=True)
    for n in names:
        (rd / n).write_bytes(b"x")
    return rd


def run_main(tmp_path, ws_lines, renders=None, tripwire=None, pairs=10, capsys=None):
    pc, refs = fake_precut(tmp_path)
    ws = fake_worksheet(tmp_path, ws_lines)
    rd = renders if renders is not None else fake_renders(tmp_path)
    trip = tripwire if tripwire is not None else str(tmp_path / "leg_c.png")
    if tripwire is None:
        (tmp_path / "leg_c.png").write_bytes(b"x")
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    rc = P.main(["--precut", str(pc), "--worksheet", str(ws), "--renders-dir", str(rd),
                 "--tripwire-rework", trip, "--tripwire-room", "sitting",
                 "--pairs", str(pairs), "--out-dir", str(out)])
    return rc, out, refs


TABLE_Y_BEDROOM = "| X-99-001 | 3 | 1 | update |  | Y | bedroom |"
TABLE_HEADER = "| icode | distinct | dups | slugs | room_hint | DELIVERED?(Y/N) | ROOM_TYPE(fill) |"


# --------------------------------------------------------------------------- label parsing
def test_the_machine_pairs_NOTHING_without_designer_labels(tmp_path):
    rc, out, _ = run_main(tmp_path, ["# ws", "- X-99-001/002/aaaa1111.jpg  5000px"])
    assert rc == 2, "no labels must be WAITING (exit 2), never a silent empty pilot"
    md = (out / "pilot-pairs.md").read_text(encoding="utf-8")
    assert "WAITING" in md and not (out / "pilot-pairs.json").exists()


def test_project_row_label_applies_to_the_projects_anchors(tmp_path):
    rc, out, refs = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    paired = {p["anchor"]["ref"] for p in js["pairs"]}
    assert refs["a1"]["ref"] in paired
    assert all(p["anchor"]["label_source"].startswith("project-row") for p in js["pairs"])


def test_anchor_line_arrow_BEATS_the_project_row(tmp_path):
    rc, out, refs = run_main(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "- X-99-001/002/aaaa1111.jpg  5000px => N",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    paired = {p["anchor"]["ref"] for p in js["pairs"]}
    assert refs["a1"]["ref"] not in paired, "per-anchor => N must override the row's Y"
    assert js["skipped_labels"]["not_delivered"] == 1


def test_N_labeled_and_unlabeled_anchors_never_pair(tmp_path):
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom",
        "- X-99-001/002/bbbb2222.jpg  4000px => N",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    paired = {p["anchor"]["ref"] for p in js["pairs"]}
    assert paired == {refs["a1"]["ref"]}
    assert js["skipped_labels"]["not_delivered"] == 1
    assert js["skipped_labels"]["unlabeled"] >= 3   # a3, b1, b2 untouched


def test_dup_and_photo_suspect_never_pair_even_when_labeled_Y(tmp_path):
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom",
        "- X-99-001/002/dddd4444.jpg  3000px => Y bedroom",
        "- X-99-001/004/eeee5555.jpg  2500px => Y bedroom",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    paired = {p["anchor"]["ref"] for p in js["pairs"]}
    assert refs["dup"]["ref"] not in paired, "a dup anchor must never pair"
    assert refs["sus"]["ref"] not in paired, "a photo-suspect anchor must never pair"
    assert js["dropped_from_pairing"] == {"dup": 1, "photo_suspect": 1}
    assert js["labeled_but_not_pairable"] == sorted([refs["dup"]["ref"], refs["sus"]["ref"]]), \
        "hand labor spent on an unpairable ref must be SURFACED, never silently unused"


def test_thai_room_word_normalizes_and_unknown_word_surfaces_not_guesses(tmp_path):
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y ห้องนอน",
        "- X-99-001/002/bbbb2222.jpg  4000px => Y โซฟาสีเทา",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert any(p["anchor"]["ref"] == refs["a1"]["ref"] and p["room_type"] == "bedroom"
               for p in js["pairs"])
    assert [u["ref"] for u in js["unmatched_room_words"]] == [refs["a2"]["ref"]]
    assert all(p["anchor"]["ref"] != refs["a2"]["ref"] for p in js["pairs"]), \
        "an unknown room word surfaces for the designer; it is never guessed into a lane"
    # the surfaced record carries a WHY code, never the raw word (which could name a client)
    assert "why" in js["unmatched_room_words"][0]
    assert "โซฟาสีเทา" not in json.dumps(js["unmatched_room_words"], ensure_ascii=False)


def test_ambiguous_thai_room_word_is_surfaced_not_routed_to_a_lane(tmp_path):
    """CRITICAL refusal: 'นั่งเล่น'/'ห้องนั่งเล่น' covers BOTH sitting and living in Thai and
    we run both lanes. The machine must NOT pick one -- it surfaces the ambiguity."""
    assert P.norm_room("ห้องนั่งเล่น") == "AMBIGUOUS:sitting|living"
    assert P.norm_room("นั่งเล่น") == "AMBIGUOUS:sitting|living"
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom",   # keeps a real pair so rc==0
        "- X-99-001/002/bbbb2222.jpg  4000px => Y ห้องนั่งเล่น",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert all(p["anchor"]["ref"] != refs["a2"]["ref"] for p in js["pairs"]), \
        "an ambiguous word must never be silently routed into sitting OR living"
    assert js["skipped_labels"]["ambiguous_room_word"] == 1
    surfaced = next(u for u in js["unmatched_room_words"] if u["ref"] == refs["a2"]["ref"])
    assert "sitting" in surfaced["why"] and "living" in surfaced["why"]


def test_MUTATION_ambiguous_word_routed_to_living_would_mis_pair(tmp_path, monkeypatch):
    """Proof the guard bites: if norm_room resolved the ambiguous word to 'living' (the old
    behavior), the anchor WOULD pair into the living lane. The test above is what catches it."""
    monkeypatch.setattr(P, "norm_room", lambda t: "living" if "นั่งเล่น" in (t or "") else None)
    rd = fake_renders(tmp_path, names=("R_PRJ002_LivingRoom_Cam01_v01.png",))
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/bbbb2222.jpg  4000px => Y ห้องนั่งเล่น",
    ], renders=rd)
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert any(p["room_type"] == "living" for p in js["pairs"]), \
        "mutant DID route the ambiguous word to living -- proving the ambiguity guard bites"


def test_labeled_room_with_no_render_lane_is_an_honest_gap_not_a_pair(tmp_path):
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y kitchen",
        "- X-99-001/002/bbbb2222.jpg  4000px => Y bedroom",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert js["rooms_without_render_lane"] == ["kitchen"]
    assert all(p["room_type"] != "kitchen" for p in js["pairs"])


# --------------------------------------------------------------------------- pairing law
def test_every_unique_pair_is_presented_in_BOTH_orders(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    orders = {}
    for r in js["presentation"]:
        orders.setdefault(r["pair_id"], set()).add(r["order"])
    for p in js["pairs"]:
        assert orders[p["pair_id"]] == {"ours-left", "ours-right"}, \
            f"{p['pair_id']} must appear once per order"


def test_presentation_order_is_deterministic_across_runs(tmp_path):
    rc1, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    js1 = (out / "pilot-pairs.json").read_text(encoding="utf-8")
    md1 = (out / "pilot-pairs.md").read_text(encoding="utf-8")
    os.remove(out / "pilot-pairs.md")
    os.remove(out / "pilot-pairs.json")
    rc2, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert (rc1, rc2) == (0, 0)
    assert (out / "pilot-pairs.json").read_text(encoding="utf-8") == js1
    assert (out / "pilot-pairs.md").read_text(encoding="utf-8") == md1


def test_budget_caps_real_pairs(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM], pairs=2)
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert len(js["pairs"]) == 2


def test_our_lane_takes_the_LATEST_version_per_camera(tmp_path):
    rd = fake_renders(tmp_path)
    ours, unknown = P.discover_our_lane(str(rd))
    names = [o["name"] for o in ours["bedroom"]]
    assert "R_PRJ002_MasterSuite_Cam02_v04.png" in names
    assert "R_PRJ002_MasterSuite_Cam02_v01.png" not in names, "superseded version must not pair"
    assert "R_PRJ002_MasterSuite_Cam01_v01.png" in names
    assert unknown == []


def test_below_parity_minimum_is_FLAGGED_not_hidden(tmp_path):
    rc, out, _ = run_main(tmp_path, ["- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom"])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert js["pairs"] and all(p["below_parity_minimum"] for p in js["pairs"]), \
        "1 anchor < PARITY_MIN=2 must be disclosed on every pair it produced"


# --------------------------------------------------------------------------- tripwires
def test_tripwires_exist_and_expectations_stay_OFF_the_judging_rows(tmp_path):
    rc, out, _ = run_main(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "- X-99-002/001/ffff6666.jpg  4500px => Y sitting",
        "- X-99-002/001/gggg7777.jpg  2600px => Y sitting",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    kinds = {t["tripwire"]["kind"] for t in js["tripwires"]}
    assert kinds == {"known-rework-must-lose", "anchor-vs-itself"}
    md = (out / "pilot-pairs.md").read_text(encoding="utf-8")
    table = md.split("## เฉลย tripwire")[0]
    assert "must-lose" not in table and "LOSES" not in table and "TIE" not in table, \
        "expectations must never prime the judging rows"
    assert "อ่านหลังตัดสินครบ" in md


def test_self_tie_tripwire_is_the_same_image_on_both_sides_twice(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    rows = [r for r in js["presentation"] if r["pair_id"] == "TS01"]
    assert len(rows) == 2 and all(r["left"] == r["right"] for r in rows)


def test_missing_sitting_anchors_leaves_the_rework_tripwire_WAITING_not_crossroom(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])   # bedroom only
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    waiting = [t for t in js["tripwires"] if t.get("unavailable")]
    assert waiting and waiting[0]["pair_id"] == "T-REWORK-WAITING", \
        "no sitting anchors -> the known-REWORK tripwire WAITS; it never pairs cross-room"
    assert all(t["room_type"] == "sitting" for t in js["tripwires"]
               if t["tripwire"]["kind"] == "known-rework-must-lose")


# --------------------------------------------------------------------------- overwrite guard
def test_a_sheet_with_designer_verdicts_is_NEVER_overwritten(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert rc == 0
    md = out / "pilot-pairs.md"
    judged = md.read_text(encoding="utf-8").replace("|  |  |", "| L | ok |", 1)
    md.write_text(judged, encoding="utf-8")
    pc = tmp_path / "precut.json"
    ws = tmp_path / "precut-worksheet.md"
    rc2 = P.main(["--precut", str(pc), "--worksheet", str(ws),
                  "--renders-dir", str(tmp_path / "renders"),
                  "--tripwire-rework", str(tmp_path / "leg_c.png"),
                  "--out-dir", str(out)])
    assert rc2 == 1
    assert md.read_text(encoding="utf-8") == judged, "judged sheet bytes must be untouched"


def test_sheet_has_verdicts_detector_baseline_and_mutation():
    blank = "| J01 | a.png | b.png |  |  |"
    filled = "| J01 | a.png | b.png | L |  |"
    note_only = "| J01 | a.png | b.png |  | แสงแปลก ๆ ขอดูอีกที |"
    assert not P.sheet_has_verdicts(blank), "baseline: a blank sheet must not read as judged"
    assert P.sheet_has_verdicts(filled), "a filled verdict cell must be detected"
    assert P.sheet_has_verdicts(note_only), "a note without a verdict is still hand labor"


def test_sheet_has_verdicts_survives_a_dropped_trailing_pipe(tmp_path):
    """DATA-LOSS: GFM lets a designer drop the trailing pipe; the old exact-7-cell check then
    read a judged row as blank and OVERWROTE it. Every judged shape must be detected."""
    assert P.sheet_has_verdicts("| J01 | a.png | b.png | L |"), "no trailing pipe, verdict set"
    assert P.sheet_has_verdicts("| J01 | a.png | b.png | L"), "no note cell at all, verdict set"
    assert P.sheet_has_verdicts("J01 | a.png | b.png | L | ok"), "no leading pipe either"
    assert not P.sheet_has_verdicts("| J01 | a.png | b.png |"), "truly blank stays blank"
    assert not P.sheet_has_verdicts("| J01 | a.png | b.png"), "blank, no trailing cells"


def test_judged_sheet_with_dropped_trailing_pipe_is_NOT_overwritten(tmp_path):
    rc, out, _ = run_main(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    assert rc == 0
    md = out / "pilot-pairs.md"
    # judge one row and drop its trailing empty note cell + pipe
    judged = md.read_text(encoding="utf-8").replace("|  |  |", "| L", 1)
    md.write_text(judged, encoding="utf-8")
    rc2 = P.main(["--precut", str(tmp_path / "precut.json"),
                  "--worksheet", str(tmp_path / "precut-worksheet.md"),
                  "--renders-dir", str(tmp_path / "renders"),
                  "--tripwire-rework", str(tmp_path / "leg_c.png"), "--out-dir", str(out)])
    assert rc2 == 1 and md.read_text(encoding="utf-8") == judged


def test_missing_rework_file_DISCLOSES_the_gap_never_silently_drops_it(tmp_path):
    """MAJOR: a missing leg-C file must still leave a T-REWORK-UNAVAILABLE record + stdout
    warning, so a pilot without the must-lose control cannot read as complete."""
    import io
    import contextlib
    pc, refs = fake_precut(tmp_path)
    ws = fake_worksheet(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "- X-99-002/001/ffff6666.jpg  4500px => Y sitting",
        "- X-99-002/001/gggg7777.jpg  2600px => Y sitting"])
    out = tmp_path / "out"
    out.mkdir()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = P.main(["--precut", str(pc), "--worksheet", str(ws),
                     "--renders-dir", str(fake_renders(tmp_path)),
                     "--tripwire-rework", str(tmp_path / "DOES_NOT_EXIST.png"),
                     "--out-dir", str(out)])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    unavailable = [t for t in js["tripwires"] if t.get("unavailable")]
    assert any(t["pair_id"] == "T-REWORK-UNAVAILABLE" for t in unavailable), \
        "missing rework file must produce a disclosed UNAVAILABLE record"
    assert "UNAVAILABLE" in buf.getvalue()


def test_bare_arrow_Y_inherits_the_project_row_room_instead_of_dropping(tmp_path):
    """MINOR fail-safe: '=> Y' with no room word must inherit the project row's room, not wipe
    it and drop the anchor the designer explicitly confirmed."""
    rc, out, refs = run_main(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "- X-99-001/002/aaaa1111.jpg  5000px => Y",   # bare confirm, room from the row
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    paired = {p["anchor"]["ref"]: p["room_type"] for p in js["pairs"]}
    assert paired.get(refs["a1"]["ref"]) == "bedroom", \
        "a bare '=> Y' under a bedroom project row must stay a bedroom, not drop"


def test_UNCODED_project_row_label_is_REFUSED_not_fanned_across_clients(tmp_path):
    """MAJOR refusal: UNCODED aggregates unrelated clients, so one project-row label must NOT
    stamp them all. Only per-anchor '=>' labels an UNCODED anchor."""
    pc, refs = fake_precut(tmp_path)
    data = json.loads(pc.read_text(encoding="utf-8"))
    data["projects"].append({"icode": "UNCODED", "anchors": [
        {"path": str(tmp_path / "u1.jpg"), "ref": "UNCODED/002/uuuu1111.jpg", "thread": "002",
         "maxdim": 4000, "wh": [4000, 2000], "engine": None, "room_hint": None,
         "delivery_signal": "x", "dup_of": None},
    ]})
    (tmp_path / "u1.jpg").write_bytes(b"x")
    pc.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ws = fake_worksheet(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "| UNCODED | 1 | 0 | update |  | Y | bedroom |"])
    out = tmp_path / "out"
    out.mkdir()
    (tmp_path / "leg_c.png").write_bytes(b"x")
    P.main(["--precut", str(pc), "--worksheet", str(ws),
            "--renders-dir", str(fake_renders(tmp_path)),
            "--tripwire-rework", str(tmp_path / "leg_c.png"), "--out-dir", str(out)])
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert all("UNCODED" not in p["anchor"]["ref"] for p in js["pairs"]), \
        "an UNCODED anchor must not pair via a project-row label"
    assert js["skipped_labels"]["uncoded_project_row_refused"] >= 1


def test_latest_version_key_is_case_insensitive(tmp_path):
    rd = fake_renders(tmp_path, names=("R_PRJ002_MasterSuite_Cam01_v01.png",
                                       "R_PRJ002_Mastersuite_Cam01_v03.png"))
    ours, _ = P.discover_our_lane(str(rd))
    names = [o["name"] for o in ours["bedroom"]]
    assert names == ["R_PRJ002_Mastersuite_Cam01_v03.png"], \
        "case drift in the room token must not resurrect a superseded version"


def test_labels_without_any_matching_lane_are_WAITING_not_a_triwire_only_sheet(tmp_path):
    rc, out, _ = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y kitchen",
    ])
    assert rc == 2, "labeled but unpairable must be WAITING, not a tripwire-only 'pilot'"
    assert not (out / "pilot-pairs.json").exists()


def test_room_word_without_delivered_flag_is_its_own_skip_counter(tmp_path):
    rc, out, _ = run_main(tmp_path, [
        TABLE_HEADER,
        "| X-99-001 | 3 | 1 | update |  |  | bedroom |",   # room typed, delivered left blank
        "- X-99-002/001/ffff6666.jpg  4500px => Y bedroom",
    ])
    assert rc == 0
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    assert js["skipped_labels"]["room_word_but_no_delivered_flag"] == 3, \
        "X-99-001's 3 distinct anchors carry a room word but no delivered flag"


# --------------------------------------------------------------------------- precut guard
def test_benchmark_precut_REFUSES_to_overwrite_a_labeled_worksheet(tmp_path):
    import benchmark_precut as B
    ws = tmp_path / "precut-worksheet.md"
    ws.write_text("\n".join([TABLE_HEADER, TABLE_Y_BEDROOM]), encoding="utf-8")
    pc = {"n_candidates": 0, "n_pool": 0, "n_distinct": 0, "drops": {}, "dup_clusters": 0,
          "hash_errors": 0, "excluded": [], "photo_suspect": [], "ranked": []}
    with pytest.raises(SystemExit) as e:
        B.write_outputs(pc, str(tmp_path))
    assert "DESIGNER labels" in str(e.value)
    # baseline: an UNLABELED worksheet regenerates fine (the guard is not a tautology)
    ws.write_text("\n".join([TABLE_HEADER, "| X-99-001 | 3 | 1 | update |  |  |  |"]),
                  encoding="utf-8")
    B.write_outputs(pc, str(tmp_path))
    assert "DESIGNER FILLS" in ws.read_text(encoding="utf-8")
    # and --force overwrites deliberately
    ws.write_text("\n".join([TABLE_HEADER, TABLE_Y_BEDROOM]), encoding="utf-8")
    B.write_outputs(pc, str(tmp_path), force=True)
    assert "| Y | bedroom |" not in ws.read_text(encoding="utf-8")


def test_a_freshly_generated_worksheet_does_NOT_read_as_a_designer_fill(tmp_path):
    """Invariant the '=> anywhere' guard depends on: the machine's OWN worksheet output must
    contain no designer-fill signal, or every benign regeneration would be blocked forever."""
    import benchmark_precut as B
    pc = {"n_candidates": 1, "n_pool": 1, "n_distinct": 1,
          "drops": {}, "dup_clusters": 0, "hash_errors": 0, "excluded": [], "photo_suspect": [],
          "ranked": [("X-99-001", {"distinct": 1, "dups": 0, "slugs": ["update"],
                                   "room_hint": None, "anchors": [
              {"path": str(tmp_path / "a.jpg"), "ref": "X-99-001/002/aaaa1111.jpg",
               "thread": "002", "maxdim": 4000, "wh": [4000, 2000], "engine": None,
               "room_hint": None, "delivery_signal": "x", "dup_of": None,
               "photo_suspect": False}]})]}
    B.write_outputs(pc, str(tmp_path), force=True)
    generated = (tmp_path / "precut-worksheet.md").read_text(encoding="utf-8")
    assert not B.worksheet_has_designer_fill(generated), \
        "the machine's own worksheet must not self-trip the designer-fill guard"


def test_benchmark_precut_guard_survives_a_dropped_trailing_pipe(tmp_path):
    """DATA-LOSS: a labeled row without a trailing pipe (GFM-legal) must still block re-gen."""
    import benchmark_precut as B
    assert B.worksheet_has_designer_fill("| X-99-001 | 3 | 1 | update |  | Y | bedroom"), \
        "trailing-pipe-less label row must be detected as a fill"
    assert B.worksheet_has_designer_fill("X-99-001 | 3 | 1 | update |  | Y | bedroom |"), \
        "leading-pipe-less label row too"
    assert B.worksheet_has_designer_fill("some line X => Y bedroom"), "a dashless arrow counts"
    assert not B.worksheet_has_designer_fill("| X-99-001 | 3 | 1 | update |  |  |  |"), \
        "a genuinely blank row must NOT read as a fill"


def test_benchmark_precut_REFUSES_an_unreadable_worksheet_fail_safe(tmp_path, monkeypatch):
    """FAIL-SAFE: an unreadable (locked / OneDrive placeholder) worksheet must REFUSE, never
    proceed to overwrite it as if empty."""
    import benchmark_precut as B
    ws = tmp_path / "precut-worksheet.md"
    ws.write_text("\n".join([TABLE_HEADER, TABLE_Y_BEDROOM]), encoding="utf-8")
    pc = {"n_candidates": 0, "n_pool": 0, "n_distinct": 0, "drops": {}, "dup_clusters": 0,
          "hash_errors": 0, "excluded": [], "photo_suspect": [], "ranked": []}
    real_open = open

    def boom(path, *a, **k):
        if str(path).endswith("precut-worksheet.md") and "r" in (a[0] if a else k.get("mode", "r")):
            raise PermissionError("file is locked")
        return real_open(path, *a, **k)
    monkeypatch.setattr("builtins.open", boom)
    with pytest.raises(SystemExit) as e:
        B.write_outputs(pc, str(tmp_path))
    assert "cannot read" in str(e.value).lower()


# --------------------------------------------------------------------------- refusal probes
def test_MUTATION_norm_room_guessing_an_unknown_word_would_be_caught(tmp_path, monkeypatch):
    """Break the refusal: make norm_room 'helpfully' default unknown words to bedroom. The
    unmatched-surface test above must go RED under this mutation -- proven here directly."""
    assert P.norm_room("โซฟาสีเทา") is None, "baseline: unknown word refuses"
    monkeypatch.setattr(P, "norm_room", lambda t: "bedroom" if (t or "").strip() else None)
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/bbbb2222.jpg  4000px => Y โซฟาสีเทา",
    ])
    js = json.loads((out / "pilot-pairs.json").read_text(encoding="utf-8"))
    mutated_paired = any(p["anchor"]["ref"] == refs["a2"]["ref"] for p in js["pairs"])
    assert mutated_paired, ("the mutation DID pair the unknown word -- which proves "
                            "test_thai_room_word... is the guard that would catch it")


def test_MUTATION_treating_unlabeled_as_delivered_would_be_caught(tmp_path, monkeypatch):
    """Break the other refusal: unlabeled anchors default to delivered. The WAITING test
    (exit 2) is the guard: under the mutation it would produce pairs instead."""
    orig = P.label_anchors

    def mutant(pool, plabels, alabels):
        delivered, skipped, unmatched = orig(pool, plabels, alabels)
        for ref, rec in pool.items():
            if ref not in delivered:
                delivered[ref] = {**rec, "room_type": "bedroom", "room_word": "GUESSED",
                                  "label_source": "MUTANT-DEFAULT"}
        return delivered, skipped, unmatched
    monkeypatch.setattr(P, "label_anchors", mutant)
    rc, out, _ = run_main(tmp_path, ["# ws, no labels at all"])
    assert rc == 0 and (out / "pilot-pairs.json").exists(), \
        "mutation produced a pilot from zero labels -- proving the WAITING test guards this"


def test_stdout_withholds_free_text_that_could_carry_a_client_name(tmp_path, capsys):
    """The one stdout channel that could leak a name: a designer's own label text (unknown
    room word, a pasted path). It must surface as a REF/COUNT, never the raw string. This
    plants a name-bearing label and asserts the name never reaches stdout."""
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom",         # a real pair so rc==0
        "- X-99-001/002/bbbb2222.jpg  4000px => Y ห้องนอนคุณสมชาย",   # unknown word w/ a name
        "- D:/discord/002_บ้านคุณสมชาย/final.jpg => Y bedroom",       # pasted path w/ a name
    ])
    assert rc == 0
    stdout = capsys.readouterr().out
    assert "คุณสมชาย" not in stdout, "a client name in a designer label reached stdout"
    assert "บ้านคุณสมชาย" not in stdout
    # but the loss IS surfaced: the ref of the unusable-room-word anchor is named
    assert refs["a2"]["ref"] in stdout
    # and the reason (with the name) is retrievable from the gitignored json only
    js = (out / "pilot-pairs.json").read_text(encoding="utf-8")
    assert "unmatched_room_words" in js


def test_MUTATION_stdout_leak_guard_can_actually_fail(tmp_path, capsys, monkeypatch):
    """The old stdout test asserted absence of strings that were never in the fixture -- it
    could not fail. This proves the new guard bites: a mutant that prints the raw room word
    to stdout makes test_stdout_withholds... RED (the name appears)."""
    def leaky(unmatched, labeled_unpairable, malformed):
        for u in unmatched:
            print("LEAK", u.get("why"), u.get("ref"))
    orig = P.label_anchors

    def carry_word(pool, pl, al):
        delivered, skipped, unmatched = orig(pool, pl, al)
        for u in unmatched:
            u["why"] = "room word not recognized: ห้องนอนคุณสมชาย"   # a mutant that keeps the word
        return delivered, skipped, unmatched
    monkeypatch.setattr(P, "label_anchors", carry_word)
    monkeypatch.setattr(P, "_print_surfacing", leaky)
    rc, out, refs = run_main(tmp_path, [
        "- X-99-001/002/aaaa1111.jpg  5000px => Y bedroom",
        "- X-99-001/002/bbbb2222.jpg  4000px => Y ห้องนอนคุณสมชาย",
    ])
    assert "คุณสมชาย" in capsys.readouterr().out, \
        "mutant leaked the name -- proving the stdout privacy test is a real guard, not a tautology"


def test_the_MD_sheet_is_icoded_even_when_the_client_name_is_in_the_BASENAME(tmp_path):
    """CRITICAL privacy: Discord attachment BASENAMES are uploader-controlled and can carry a
    client name (e.g. 'บ้านคุณทดสอบ_final.jpg'). The md sheet must show the anchor by its I-coded
    REF, never its basename; the real path lives only in the gitignored paths json."""
    pc, refs = fake_precut(tmp_path)
    named = tmp_path / "files"
    named.mkdir()
    img = named / "บ้านคุณทดสอบ_final.jpg"       # personal name in the FILENAME, not the dir
    img.write_bytes(b"x")
    data = json.loads(pc.read_text(encoding="utf-8"))
    data["projects"][0]["anchors"][0]["path"] = str(img)
    pc.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ws = fake_worksheet(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    out = tmp_path / "out"
    out.mkdir()
    (tmp_path / "leg_c.png").write_bytes(b"x")
    rc = P.main(["--precut", str(pc), "--worksheet", str(ws),
                 "--renders-dir", str(fake_renders(tmp_path)),
                 "--tripwire-rework", str(tmp_path / "leg_c.png"),
                 "--out-dir", str(out)])
    assert rc == 0
    md = (out / "pilot-pairs.md").read_text(encoding="utf-8")
    assert "คุณทดสอบ" not in md, "a client name in the basename reached the designer-facing sheet"
    assert refs["a1"]["ref"] in md, "the anchor must be shown by its I-coded ref"
    paths_json = (out / "pilot-anchor-paths.json").read_text(encoding="utf-8")
    assert "คุณทดสอบ" in paths_json, "the gitignored paths file must still carry the real path"


def test_the_path_lookup_file_has_NO_tripwire_spoiler(tmp_path):
    """No-priming: the file the designer opens to resolve anchor paths must not contain the
    tripwire expectations (the old single json forced them through the spoiler)."""
    rc, out, _ = run_main(tmp_path, [
        TABLE_HEADER, TABLE_Y_BEDROOM,
        "- X-99-002/001/ffff6666.jpg  4500px => Y sitting",
        "- X-99-002/001/gggg7777.jpg  2600px => Y sitting",
    ])
    assert rc == 0
    paths = (out / "pilot-anchor-paths.json").read_text(encoding="utf-8")
    assert "LOSES" not in paths and "TIE" not in paths and "expectation" not in paths
    assert "must-lose" not in paths


def test_basename_collision_between_two_anchors_does_not_corrupt_the_sheet(tmp_path):
    """Two anchors sharing a filename ('image.png' is a constant Discord name) must remain
    distinguishable -- the ref-based display makes them so; basename display collided them."""
    pc, refs = fake_precut(tmp_path)
    data = json.loads(pc.read_text(encoding="utf-8"))
    d = tmp_path / "d1"
    d.mkdir()
    d2 = tmp_path / "d2"
    d2.mkdir()
    (d / "image.png").write_bytes(b"x")
    (d2 / "image.png").write_bytes(b"x")
    data["projects"][0]["anchors"][0]["path"] = str(d / "image.png")
    data["projects"][0]["anchors"][1]["path"] = str(d2 / "image.png")
    pc.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ws = fake_worksheet(tmp_path, [TABLE_HEADER, TABLE_Y_BEDROOM])
    out = tmp_path / "out"
    out.mkdir()
    (tmp_path / "leg_c.png").write_bytes(b"x")
    P.main(["--precut", str(pc), "--worksheet", str(ws),
            "--renders-dir", str(fake_renders(tmp_path)),
            "--tripwire-rework", str(tmp_path / "leg_c.png"), "--out-dir", str(out)])
    md = (out / "pilot-pairs.md").read_text(encoding="utf-8")
    assert refs["a1"]["ref"] in md and refs["a2"]["ref"] in md, \
        "both colliding-basename anchors must appear distinctly (by ref)"
    paths = json.loads((out / "pilot-anchor-paths.json").read_text(encoding="utf-8"))["paths"]
    assert paths[refs["a1"]["ref"]] != paths[refs["a2"]["ref"]], "distinct paths per ref"
