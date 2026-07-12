"""Tests for floor2_defect_gate -- the floor-level defect gate v4 was missing.

Load-bearing pins:
  - C1 catches a BF14xBF09-3-class deep interpenetration as FAIL, grades a graze REVIEW,
    ignores drawing-tolerance touches, and bakes rot through placement_gate.footprint;
  - C2 catches a piece poking out of its (sub)room by more than wall slack -- the
    BF09-2-out-of-the-wardrobe-bay class -- and stays quiet inside the slack;
  - C3 finds a doorway as a flanked 550-1300mm gap in collinear wall runs and flags a
    piece covering it; a non-doorway gap and an un-blocked doorway stay quiet;
  - C4 coverage: uncovered sheet ink -> missing run, attributed clipped_out (in the json,
    dropped by build_floor's midpoint rule -- mirrored EXACTLY) vs absent (not in json);
    covered ink emits nothing; adjacent missing runs merge into one defect;
  - signatures: an owner-signed fingerprint STICKS -- the defect reads SIGNED and stops
    blocking the verdict;
  - the whole gate output is json-serializable (it is written to disk every run).
"""
import json
import os
import tempfile

import floor2_defect_gate as G


def _sg(items=None, builtins=None, subrooms=None, outline=None):
    return {"schema": "t", "units": "mm", "room": {"outline_mm": outline or
            [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": items or [], "builtins": builtins or [], "subrooms": subrooms or []}


def _write(td, sg, walls=None, clip=None):
    sgp = os.path.join(td, "sg.json")
    json.dump(sg, open(sgp, "w", encoding="utf-8"), ensure_ascii=False)
    wp = os.path.join(td, "walls.json")
    json.dump({"schema": "t", "scale_mm_per_pt": 1.0, "origin_pt": [0, 0],
               "segments": walls or []}, open(wp, "w", encoding="utf-8"))
    mp = os.path.join(td, "manifest.json")
    json.dump({"furnish": [{"id": "room", "spec": sgp, "offset_mm": [0, 0]}],
               "walls_json": wp, "clip_zones": clip},
              open(mp, "w", encoding="utf-8"))
    return mp


def _run(td, sg, walls=None, clip=None):
    return G.run_gate(_write(td, sg, walls, clip), use_pdf=False)


# ---- C1 collision --------------------------------------------------------------------------
def test_c1_deep_interpenetration_fails():
    """The BF14 x BF09-3 class: 100 x 325 mm real overlap -> FAIL, with a move proposal."""
    sg = _sg(builtins=[
        {"name": "slat", "kind": "headboard", "x": 5150, "y": 0, "w": 100, "d": 3250},
        {"name": "wardrobe", "kind": "wardrobe", "x": 2300, "y": 2925, "w": 3300, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    c1 = [d for d in out["defects"] if d["check"] == "C1_collision"]
    assert len(c1) == 1 and c1[0]["severity"] == "FAIL"
    assert out["verdict"] == "FAIL"
    assert "ย้าย" in c1[0]["proposal"]


def test_c1_graze_is_review_and_touch_is_ignored():
    sg = _sg(builtins=[
        {"name": "a", "kind": "cabinet", "x": 0, "y": 0, "w": 1000, "d": 600},
        {"name": "b", "kind": "cabinet", "x": 975, "y": 0, "w": 1000, "d": 600},   # 25mm graze
        {"name": "c", "kind": "cabinet", "x": 1970, "y": 0, "w": 500, "d": 600}])  # 5mm touch
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    c1 = [d for d in out["defects"] if d["check"] == "C1_collision"]
    assert len(c1) == 1 and c1[0]["severity"] == "REVIEW"
    assert sorted(c1[0]["names"]) == ["a", "b"]


def test_c1_rot_is_baked_through_footprint():
    """A 2000x600 piece at rot 90 occupies 600x2000 -- no false overlap with a neighbour
    that only its UNROTATED rect would hit."""
    sg = _sg(items=[
        {"name": "r", "kind": "cabinet", "x": 0, "y": 0, "w": 2000, "d": 600, "rot": 90},
        {"name": "n", "kind": "cabinet", "x": 1500, "y": 900, "w": 400, "d": 400}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    assert not [d for d in out["defects"] if d["check"] == "C1_collision"]


# ---- C2 containment ------------------------------------------------------------------------
def test_c2_subroom_escape_fails_and_slack_is_quiet():
    """BF09-2 class: fixture assigned to a bay but poking 670mm out of it -> FAIL.
    A builtin overlapping its room outline by less than wall slack stays quiet."""
    sg = _sg(builtins=[{"name": "flush", "kind": "cabinet", "x": -100, "y": 0,
                        "w": 600, "d": 600}],
             subrooms=[{"name": "bay", "outline_mm": [[3000, 3000], [6000, 3000],
                                                      [6000, 6000], [3000, 6000]],
                        "fixtures": [{"name": "w2", "kind": "wardrobe",
                                      "x": 3000, "y": 2330, "w": 600, "d": 1500}]}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    c2 = [d for d in out["defects"] if d["check"] == "C2_out_of_room"]
    assert len(c2) == 1 and c2[0]["names"] == ["w2"] and c2[0]["severity"] == "FAIL"
    assert c2[0]["outside_mm"] > 500


# ---- C3 doorways ---------------------------------------------------------------------------
_WALL_RUNS = [[[0, 3000], [2000, 3000]], [[2900, 3000], [6000, 3000]]]   # 900mm gap


def test_c3_doorway_found_and_blocked_piece_flagged():
    sg = _sg(builtins=[{"name": "run", "kind": "wardrobe",
                        "x": 1500, "y": 2900, "w": 1200, "d": 200}])     # covers the gap
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=_WALL_RUNS)
    assert len(out["doorway_candidates"]) == 1
    c3 = [d for d in out["defects"] if d["check"] == "C3_door_blocked"]
    assert len(c3) == 1 and c3[0]["names"] == ["run"]
    assert c3[0]["severity"] == "REVIEW"           # "is it a real door" = owner call


def test_c3_unblocked_doorway_and_nondoor_gap_stay_quiet():
    sg = _sg(builtins=[{"name": "far", "kind": "cabinet", "x": 0, "y": 0,
                        "w": 600, "d": 600}])
    wide = [[[0, 3000], [2000, 3000]], [[3600, 3000], [6000, 3000]]]     # 1600mm: not a door
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=_WALL_RUNS)
        out2, *_ = _run(td, sg, walls=wide)
    assert not [d for d in out["defects"] if d["check"] == "C3_door_blocked"]
    assert len(out["doorway_candidates"]) == 1
    assert len(out2["doorway_candidates"]) == 0


# ---- C4 wall coverage ----------------------------------------------------------------------
def test_c4_missing_wall_causes_attributed():
    """One fresh run covered (quiet), one absent from json (absent), one in json but
    midpoint-clipped by build_floor's rule (clipped_out)."""
    zones = [[0, 0, 4000, 4000]]
    covered = [[0, 100], [3000, 100]]
    absent = [[0, 2000], [3000, 2000]]
    clipped = [[0, 3900], [9000, 3900]]            # midpoint x=4500 outside zone -> dropped
    all_json = [covered, clipped]
    built = [s for s in all_json if G._mid_in_zones(s, zones)]
    assert built == [covered]                       # the mirror of build_walls' rule
    missing, stats = G.coverage_missing([covered, absent, clipped], built, all_json, zones)
    causes = {m["cause"] for m in missing}
    assert len(missing) == 2
    assert causes == {"absent(not-in-walls-json)", "clipped_out(midpoint-rule)"}
    assert stats["coverage"] is not None and 0 < stats["coverage"] < 1


def test_c4_adjacent_missing_runs_merge():
    fresh = [[[0, 500], [1000, 500]], [[1020, 500], [2200, 500]]]
    missing, _ = G.coverage_missing(fresh, [], [], None)
    assert len(missing) == 1 and missing[0]["len_mm"] > 2000


# ---- C1 rotated pieces: exact OBB, not inflated AABB ----------------------------------------
def test_c1_diagonal_pieces_use_exact_obb_not_inflated_aabb():
    """The tub-chair class: a rot-8 chair whose AABB inflates ~80mm must NOT collide with
    a table its true rectangle clears; a genuinely overlapping diagonal pair must."""
    clear = _sg(items=[
        {"name": "chair", "kind": "armchair", "x": 0, "y": 0, "w": 680, "d": 640, "rot": 8},
        # in the AABB's inflated top-right corner zone (61x64mm AABB 'overlap') but
        # outside the true rotated rectangle -- the exact false-alarm class
        {"name": "table", "kind": "side_table", "x": 660, "y": 620, "w": 600, "d": 600}])
    hit = _sg(items=[
        {"name": "chair", "kind": "armchair", "x": 0, "y": 0, "w": 680, "d": 640, "rot": 8},
        {"name": "table", "kind": "side_table", "x": 520, "y": 0, "w": 600, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        out_clear, *_ = _run(td, clear)
        out_hit, *_ = _run(td, hit)
    assert not [d for d in out_clear["defects"] if d["check"] == "C1_collision"]
    assert [d for d in out_hit["defects"] if d["check"] == "C1_collision"]


# ---- C3 swing square + face dedupe -----------------------------------------------------------
def test_c3_double_face_wall_yields_one_doorway():
    """A double-lined wall (two parallel face bands 100mm apart) with the same gap must
    produce ONE doorway candidate, not one per face."""
    faces = [[[0, 3000], [2000, 3000]], [[2900, 3000], [6000, 3000]],
             [[0, 3100], [2000, 3100]], [[2900, 3100], [6000, 3100]]]
    sg = _sg()
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=faces)
    assert len(out["doorway_candidates"]) == 1


def test_c3_swing_square_obstruction_flagged():
    """A piece clear of the gap band but sitting square in the leaf's swing area."""
    sg = _sg(items=[{"name": "chest", "kind": "cabinet",
                     "x": 2100, "y": 3300, "w": 700, "d": 700}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=_WALL_RUNS)
    swing = [d for d in out["defects"] if d["check"] == "C3_swing_obstructed"]
    assert len(swing) == 1 and swing[0]["names"] == ["chest"]
    assert swing[0]["severity"] == "REVIEW"


# ---- C4b room-perimeter (the non-circular walls-incomplete detector) -------------------------
def test_c4b_unwalled_room_edge_flagged_and_walled_edge_quiet():
    """Room 6000x6000: south+west edges walled, north edge walled with a doorway gap
    (expected hole -> quiet), EAST edge has no wall at all -> exactly one C4b defect."""
    walls = [[[0, 0], [6000, 0]], [[0, 0], [0, 6000]],
             [[0, 6000], [2000, 6000]], [[2900, 6000], [6000, 6000]]]
    sg = _sg()
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=walls)
    c4b = [d for d in out["defects"] if d["check"] == "C4b_room_edge_unwalled"]
    assert len(c4b) == 1
    assert c4b[0]["edge"]["axis"] == "v" and abs(c4b[0]["edge"]["offset"] - 6000) < 1
    assert c4b[0]["severity"] == "REVIEW"


# ---- review-confirmed holes (2026-07-10 adversarial workflow), each pinned ------------------
def test_c4b_far_doorway_does_not_excuse_an_edge():
    """THE flattering hole (6th lane): a doorway candidate on the same AXIS but metres
    away must NOT be subtracted from a room edge's uncovered span. On the real run,
    out-of-scope doorways 12.7m away suppressed 45% of genuinely unwalled edge."""
    walls = [[[0, 0], [6000, 0]], [[0, 0], [0, 6000]], [[6000, 0], [6000, 6000]],
             # north edge y6000: NO wall at all
             # far parallel wall with a doorway-sized gap at y=12000 (same axis 'h')
             [[0, 12000], [2000, 12000]], [[2900, 12000], [6000, 12000]]]
    sg = _sg()
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=walls)
    c4b = [d for d in out["defects"] if d["check"] == "C4b_room_edge_unwalled"
           and d["edge"]["axis"] == "h" and abs(d["edge"]["offset"] - 6000) < 1]
    assert len(c4b) == 1, f"north edge not flagged whole: {c4b}"
    assert c4b[0]["edge"]["len_mm"] >= 5900          # the WHOLE edge, no far-door hole


def test_c3_out_of_scope_doorways_dropped_by_clip_zones():
    """Doorway candidates whose rect touches no clip zone are out-of-scope rooms --
    they must not reach the report count nor the C4b exclusion pool."""
    walls = [[[0, 3000], [2000, 3000]], [[2900, 3000], [6000, 3000]],       # in scope
             [[0, 15000], [2000, 15000]], [[2900, 15000], [6000, 15000]]]  # far room
    sg = _sg()
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=walls, clip=[[-500, -500, 6500, 7000]])
    assert len(out["doorway_candidates"]) == 1


def test_c1_thin_panel_speared_is_caught():
    """False-quiet hole: a 10mm glass panel speared by a wardrobe emitted ZERO records
    under the axis-overlap prescreen. The push-out metric must catch it as FAIL."""
    sg = _sg(builtins=[
        {"name": "glass", "kind": "partition", "x": 1000, "y": 0, "w": 10, "d": 3000},
        {"name": "wardrobe", "kind": "wardrobe", "x": 400, "y": 1000, "w": 1200, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    c1 = [d for d in out["defects"] if d["check"] == "C1_collision"]
    assert len(c1) == 1 and c1[0]["severity"] == "FAIL"
    assert c1[0]["depth_mm"] > 100                    # true push-out, not the 10mm extent


def test_c2_intrusion_into_another_room_flagged():
    """Membership-only containment missed a piece parked inside the NEIGHBOUR room."""
    sg_a = _sg(items=[{"name": "stray", "kind": "chair", "x": 7000, "y": 500,
                       "w": 600, "d": 600}])          # inside room B's poly
    sg_b = _sg(outline=[[6500, 0], [10000, 0], [10000, 4000], [6500, 4000]])
    with tempfile.TemporaryDirectory() as td:
        pa = os.path.join(td, "a.json")
        pb = os.path.join(td, "b.json")
        json.dump(sg_a, open(pa, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(sg_b, open(pb, "w", encoding="utf-8"), ensure_ascii=False)
        wp = os.path.join(td, "walls.json")
        json.dump({"schema": "t", "scale_mm_per_pt": 1.0, "origin_pt": [0, 0],
                   "segments": []}, open(wp, "w", encoding="utf-8"))
        mp = os.path.join(td, "manifest.json")
        json.dump({"furnish": [{"id": "A", "spec": pa}, {"id": "B", "spec": pb}],
                   "walls_json": wp, "clip_zones": None},
                  open(mp, "w", encoding="utf-8"))
        out, *_ = G.run_gate(mp, use_pdf=False)
    # 'stray' escapes A (FAIL) AND intrudes B (REVIEW) -- both must surface
    assert [d for d in out["defects"] if d["check"] == "C2_out_of_room"
            and d["names"] == ["stray"]]
    intr = [d for d in out["defects"] if d["check"] == "C2_intrudes_other_room"]
    assert len(intr) == 1 and intr[0]["names"] == ["stray"] and "B" in intr[0]["rooms"]


def test_c2_notch_crossing_piece_caught_by_edge_sampling():
    """L-shaped room whose notch cuts through a piece's MIDDLE: all 4 corners inside,
    the waist outside -- corner-only checking stayed quiet."""
    L_room = [[0, 0], [6000, 0], [6000, 6000], [3400, 6000], [3400, 2000],
              [2600, 2000], [2600, 6000], [0, 6000]]     # notch x2600-3400, y2000-6000
    sg = _sg(outline=L_room,
             items=[{"name": "beam", "kind": "bench", "x": 2000, "y": 800,
                     "w": 2000, "d": 400}])
    # piece y 800..1200 is BELOW the notch (inside); shift it INTO the notch:
    sg["items"][0]["y"] = 3000                           # y 3000..3400, crosses the notch
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg)
    c2 = [d for d in out["defects"] if d["check"] == "C2_out_of_room"]
    assert len(c2) == 1 and c2[0]["names"] == ["beam"]


def test_wall_bands_order_independent():
    segs = [[[0, 100], [1000, 100]], [[0, 155], [1000, 155]], [[0, 40], [1000, 40]]]
    a = G.wall_bands(segs)
    b = G.wall_bands(list(reversed(segs)))
    assert {k: v for k, v in a.items()} == {k: v for k, v in b.items()}


def test_answer_key_miss_forces_fail_and_absent_is_visible():
    sg = _sg(builtins=[{"name": "lone", "kind": "cabinet", "x": 0, "y": 0,
                        "w": 1000, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        mp = _write(td, sg)
        man = json.load(open(mp, encoding="utf-8"))
        man["defect_answer_key"] = [
            {"catch": "phantom-catch", "expect": "present", "check": "C1_collision",
             "names_any": ["lone"]},
            {"catch": "old-fixed-catch", "expect": "absent", "check": "C3_",
             "names_any": ["lone"]}]
        json.dump(man, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
        out, *_ = G.run_gate(mp, use_pdf=False)
    ak = {r["catch"]: r["status"] for r in out["answer_key"]}
    assert ak["phantom-catch"] == "MISS"
    assert ak["old-fixed-catch"] == "RESOLVED-ABSENT"
    assert out["verdict"] == "FAIL"                    # a MISS means the gate itself broke
    report = G.render_report(out)
    assert "answer key" in report and "หลุด" in report


# ---- signatures ----------------------------------------------------------------------------
def test_signed_defect_sticks_and_stops_blocking():
    sg = _sg(builtins=[
        {"name": "slat", "kind": "headboard", "x": 5150, "y": 0, "w": 100, "d": 3250},
        {"name": "wardrobe", "kind": "wardrobe", "x": 2300, "y": 2925, "w": 3300, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        mp = _write(td, sg)
        out, *_ = G.run_gate(mp, use_pdf=False)
        fp = [d for d in out["defects"] if d["check"] == "C1_collision"][0]["fingerprint"]
        json.dump({"signed": [{"fingerprint": fp, "by": "owner", "date": "2026-07-10",
                               "reason": "intended overlap"}]},
                  open(os.path.join(td, "defect-review.json"), "w", encoding="utf-8"))
        out2, *_ = G.run_gate(mp, use_pdf=False)
    assert out["verdict"] == "FAIL"
    d2 = [d for d in out2["defects"] if d["check"] == "C1_collision"][0]
    assert d2["severity"] == "SIGNED" and d2["signed"]["by"] == "owner"
    assert out2["verdict"] != "FAIL"


def test_output_is_json_serializable():
    sg = _sg(builtins=[{"name": "a", "kind": "cabinet", "x": 0, "y": 0,
                        "w": 1000, "d": 600}])
    with tempfile.TemporaryDirectory() as td:
        out, *_ = _run(td, sg, walls=_WALL_RUNS)
    json.dumps(out, ensure_ascii=False)


# ---- v1.2: declared openings vs doorway candidates + envelope edges -------------------------
def _openings_manifest(td, sg, walls, openings):
    """Manifest with an openings_json side file (absolute path -> run_gate uses it as-is)."""
    mp = _write(td, sg, walls)
    op = os.path.join(td, "openings.json")
    json.dump({"openings": openings}, open(op, "w", encoding="utf-8"))
    man = json.load(open(mp, encoding="utf-8"))
    man["openings_json"] = op
    json.dump(man, open(mp, "w", encoding="utf-8"))
    return mp


_GAP_WALLS = [[[0, 0], [3000, 0]], [[3900, 0], [7000, 0]]]      # flanked 900mm gap @h y0


def test_c3_undeclared_doorway_reviewed_and_declared_window_quiets_passage():
    """markup round 2 (2026-07-10): a gap the gate reads as a doorway MUST carry a
    declaration or a signature -- v1.1 silently trusted every gap (one was a window,
    one a missing wall+sliding door). A declared window also stops being a passage:
    a desk in front of it is normal (owner: BF11), so no door_blocked either."""
    desk = {"name": "desk", "kind": "desk", "x": 2950, "y": -150, "w": 1100, "d": 400}
    with tempfile.TemporaryDirectory() as td:
        out, *_ = G.run_gate(_openings_manifest(td, _sg(items=[desk]), _GAP_WALLS, []),
                             use_pdf=False)
    assert [d for d in out["defects"] if d["check"] == "C3_undeclared_doorway"]
    assert [d for d in out["defects"] if d["check"] == "C3_door_blocked"]
    with tempfile.TemporaryDirectory() as td:
        out, *_ = G.run_gate(_openings_manifest(
            td, _sg(items=[desk]), _GAP_WALLS,
            [{"id": "w9", "type": "window", "rect": [3000, -60, 3900, 60]}]), use_pdf=False)
    assert not [d for d in out["defects"] if d["check"].startswith("C3")]


def test_c3_sliding_skips_swing_but_blocking_still_flags():
    """A sliding door has no leaf: nothing swings, but a piece COVERING the gap still
    blocks passage. Both facts pinned so 'declared' never degrades into 'unchecked'."""
    in_swing = {"name": "chair", "kind": "chair", "x": 3200, "y": 300, "w": 600, "d": 500}
    covers = {"name": "chest", "kind": "cabinet", "x": 2950, "y": -150, "w": 1100, "d": 400}
    slide = [{"id": "s9", "type": "sliding", "rect": [3000, -60, 3900, 60]}]
    with tempfile.TemporaryDirectory() as td:
        out, *_ = G.run_gate(_openings_manifest(td, _sg(items=[in_swing]), _GAP_WALLS, slide),
                             use_pdf=False)
    assert not [d for d in out["defects"] if d["check"] == "C3_swing_obstructed"]
    with tempfile.TemporaryDirectory() as td:
        out, *_ = G.run_gate(_openings_manifest(td, _sg(items=[covers]), _GAP_WALLS, slide),
                             use_pdf=False)
    assert [d for d in out["defects"] if d["check"] == "C3_door_blocked"]


def test_c3_pending_confirm_opening_stays_review():
    """An opening declared from ink but not yet owner-confirmed keeps ONE standing
    REVIEW: 'declared' must not silently close the identity question (the semantic
    layer is owner-only)."""
    slide = [{"id": "s9", "type": "sliding", "rect": [3000, -60, 3900, 60],
              "owner_confirm_pending": True}]
    with tempfile.TemporaryDirectory() as td:
        out, *_ = G.run_gate(_openings_manifest(td, _sg(), _GAP_WALLS, slide), use_pdf=False)
    pend = [d for d in out["defects"] if d["check"] == "C3_opening_unconfirmed"]
    assert len(pend) == 1 and pend[0]["severity"] == "REVIEW"
    assert out["openings"]["pending_confirm"] == ["s9"]


def test_c4c_envelope_edge_open_fails_then_wall_or_opening_covers():
    """C4c sees what C4b's room rectangles cannot (fin/pier/party runs): an uncovered
    declared edge is FAIL; built walls or a declared opening rect on the line cover it.
    Pinned with a REAL detector so the round-2 answer-key 'absent' entries can never be
    trivially green (the flattering-scorer recurrence)."""
    edges = [{"axis": "v", "offset": 7100, "span": [2000, 2600], "note": "pier"}]
    open_runs = G.check_envelope_edges(edges, [], [])
    assert len(open_runs) == 1 and open_runs[0]["severity"] == "FAIL" \
        and open_runs[0]["check"] == "C4c_envelope_edge_open"
    glass = [{"id": "g9", "type": "window", "rect": [7050, 2000, 7150, 2550]}]
    assert G.check_envelope_edges(edges, [], glass) == []          # 50mm tail < PERIM_MISS
    wall = [[[7100, 2000], [7100, 2600]]]
    assert G.check_envelope_edges(edges, wall, []) == []
    far = [{"id": "g8", "type": "window", "rect": [9050, 2000, 9150, 2600]}]
    assert G.check_envelope_edges(edges, [], far), "an opening 2m away must not cover"


def test_answer_key_zone_within_scopes_matches():
    """Without zone_within, an 'absent' entry false-REAPPEARs on any same-check flag
    elsewhere on the floor (e.g. another signed C4b edge)."""
    defects = [
        {"check": "C4b_room_edge_unwalled", "names": ["roomA"], "severity": "REVIEW",
         "zone": [0, 0, 100, 100], "fingerprint": "aaa"},
        {"check": "C4b_room_edge_unwalled", "names": ["roomA"], "severity": "REVIEW",
         "zone": [5000, 5000, 5100, 5100], "fingerprint": "bbb"},
    ]
    rows = G.evaluate_answer_key(defects, [
        {"catch": "here", "expect": "absent", "check": "C4b",
         "zone_within": [4900, 4900, 5200, 5200]},
        {"catch": "elsewhere-clean", "expect": "absent", "check": "C4b",
         "zone_within": [200, 200, 300, 300]},
        {"catch": "must-see", "expect": "present", "check": "C4b",
         "zone_within": [50, 50, 60, 60]},
    ])
    assert rows[0]["status"] == "REAPPEARED" and rows[0]["fingerprints"] == ["bbb"]
    assert rows[1]["status"] == "RESOLVED-ABSENT"
    assert rows[2]["status"] == "CAUGHT" and rows[2]["fingerprints"] == ["aaa"]
