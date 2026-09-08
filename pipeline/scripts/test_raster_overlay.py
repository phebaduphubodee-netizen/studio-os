"""
test_raster_overlay.py — unit tests for the PURE overlay logic (no PDF/fitz needed).

The overlay is the REQUIRED pre-owner surfacing artifact: pieces are NUMBERED to match the
checklist rows, facing arrows are coloured by provenance (owner-signed vs hand-read), crops
derive from the room outlines (never hardcoded), and the calibration resolves exactly like
placement_gate.run. These pin that contract.

    python test_raster_overlay.py
"""
import raster_overlay as RO


def _spec(items=None, builtins=None, subrooms=None, outline=None):
    return {"room": {"outline_mm": outline or [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]},
            "builtins": builtins or [], "items": items or [], "subrooms": subrooms or []}


# ---- pieces (deterministic numbering order: builtins, items, subroom fixtures) ---------
def test_pieces_order_and_groups():
    sp = _spec(items=[{"name": "sofa", "kind": "sofa"}],
               builtins=[{"name": "bf", "kind": "cabinet"}],
               subrooms=[{"outline_mm": [[0, 0], [1, 0], [1, 1]],
                          "fixtures": [{"name": "wc", "kind": "toilet"}]}])
    got = RO.pieces(sp)
    assert [(g, it["name"]) for g, it in got] == [("builtin", "bf"), ("loose", "sofa"),
                                                 ("fixture", "wc")]


# ---- room_bbox / crops_for (derived from outlines, padded, union) ----------------------
def test_room_bbox_includes_subrooms_and_pad():
    sp = _spec(subrooms=[{"outline_mm": [[0, 3000], [4000, 3000], [4000, 5000], [0, 5000]],
                          "fixtures": []}])
    x0, y0, x1, y1 = RO.room_bbox(sp, pad=100)
    assert (x0, y0, x1, y1) == (-100, -100, 4100, 5100)


def test_room_bbox_offset_applied():
    bb = RO.room_bbox(_spec(), offset=(1000, 2000), pad=0)
    assert bb == (1000, 2000, 5000, 5000)


def test_room_bbox_no_outline_falls_back_to_piece_footprints():
    # a hand-built/foreign spec without outline_mm must still crop (union of piece bboxes),
    # not silently drop out of the overlay
    sp = {"room": {}, "builtins": [], "subrooms": [],
          "items": [{"name": "a", "kind": "sofa", "x": 100, "y": 200, "w": 400, "d": 600}]}
    assert RO.room_bbox(sp, pad=0) == (100, 200, 500, 800)


def test_room_bbox_nothing_at_all_is_none():
    assert RO.room_bbox({"room": {}, "builtins": [], "items": [], "subrooms": []}) is None


def test_crops_for_per_room_plus_full_union():
    rooms = [{"id": "a", "spec": _spec()},
             {"id": "b", "spec": _spec(outline=[[6000, 0], [9000, 0], [9000, 2000], [6000, 2000]])}]
    crops = dict(RO.crops_for(rooms, pad=0))
    assert set(crops) == {"a", "b", "full"}
    assert crops["full"] == (0, 0, 9000, 3000)          # union of both rooms


def test_crops_for_empty_rooms():
    assert RO.crops_for([]) == []


# ---- calibration resolution (mirror of placement_gate.run) -----------------------------
def test_resolve_calib_manifest_wins():
    assert RO.resolve_calib({"calibration": [30.0, 100.0, 200.0]}) == (30.0, 100.0, 200.0)


def test_resolve_calib_falls_back_to_shared_default():
    from plan_cluster import SCALE, OX, OY
    assert RO.resolve_calib({}) == (SCALE, OX, OY)      # same triple the gate defaults to


# ---- facing arrows: who gets one, what colour ------------------------------------------
def test_wants_arrow_facing_kinds_and_signed_any_kind():
    assert RO.wants_arrow({"kind": "sofa"}) is True
    assert RO.wants_arrow({"kind": "cabinet"}) is False                  # non-facing, unsigned
    assert RO.wants_arrow({"kind": "cabinet", "facing_source": "owner-signed"}) is True


def test_arrow_color_by_provenance():
    assert RO.arrow_color({"facing_source": "owner-signed"}) == RO.ARROW_SIGNED
    assert RO.arrow_color({"kind": "sofa"}) == RO.ARROW_HANDREAD


# ---- checklist: badges match pieces() order, provenance spelled out, stubs pasteable ---
def test_checklist_rows_match_piece_numbering():
    rooms = [{"id": "r", "spec": _spec(
        items=[{"name": "โซฟา", "kind": "sofa", "rot": 90, "w": 1000, "d": 2200},
               {"name": "เก้าอี้", "kind": "armchair", "rot": 8, "facing_source": "owner-signed"}],
        builtins=[{"name": "ตู้ BF", "kind": "cabinet"}])}]
    text = "\n".join(RO.checklist(rooms))
    assert "| A1 | ตู้ BF |" in text and "cabinet (builtin)" in text     # builtins numbered first
    assert "| A2 | โซฟา |" in text and "hand-read" in text              # unsigned facing flagged
    assert "| A3 | เก้าอี้ |" in text and "owner-signed" in text         # signed facing marked
    # the non-facing unsigned builtin gets a dash, not a false "check me"
    row1 = next(l for l in text.splitlines() if l.startswith("| A1 |"))
    assert "| – |" in row1
    # cardinal rot is glossed with its letter so the row is self-checkable
    assert "90 (หัน E)" in text


def test_checklist_badges_unique_across_rooms():
    # room letters make badge ids collision-free: A5 (master bed) can never read as B5
    rooms = [{"id": "master_bedroom", "spec": _spec(items=[{"name": "x", "kind": "bed"}])},
             {"id": "sitting_room", "spec": _spec(items=[{"name": "y", "kind": "sofa"}])}]
    text = "\n".join(RO.checklist(rooms))
    assert "## A — master_bedroom" in text and "## B — sitting_room" in text
    assert "| A1 | x |" in text and "| B1 | y |" in text


def test_checklist_sign_stub_is_valid_pasteable_json():
    import json
    rooms = [{"id": "sitting_room", "spec": _spec(
        items=[{"name": "โซฟา 3 ที่นั่ง", "kind": "sofa", "rot": 90, "w": 1002, "d": 2202}])}]
    text = RO.checklist(rooms)
    # the unsigned facing row gets a ready-to-paste stub: valid JSON, right join keys
    j = next(l for l in text if l.startswith("{"))
    stub = json.loads(j)                                     # must parse — no comments, no trailing comma
    assert stub["room"] == "sitting_room" and stub["name"] == "โซฟา 3 ที่นั่ง"
    assert stub["rot"] == 90 and stub["w"] == 1002 and stub["d"] == 2202   # gate's join keys pre-filled


def test_checklist_signed_rows_get_no_stub():
    # facing AND kind both owner-signed -> nothing left to sign, no stub of either flavour
    rooms = [{"id": "r", "spec": _spec(
        items=[{"name": "เก้าอี้", "kind": "armchair", "rot": 8,
                "facing_source": "owner-signed", "kind_source": "owner-signed"}])}]
    text = RO.checklist(rooms)
    assert not any(l.startswith("{") for l in text)          # nothing to sign — no stub sections


def test_box_colors_never_use_provenance_channel():
    # green/orange are reserved for the provenance ARROWS; a green wardrobe box would false-train
    # the scanning eye. Guard: no KIND_COL entry in the green or orange hue families.
    def rgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    for kind, col in RO.KIND_COL.items():
        r, g, b = rgb(col)
        assert not (g > r * 1.4 and g > b * 1.4), f"{kind} box {col} reads GREEN (signed channel)"
        assert not (r > 200 and 80 < g < 180 and b < 60), f"{kind} box {col} reads ORANGE (hand-read channel)"
    rs, gs, bs = rgb(RO.ARROW_SIGNED)
    assert gs > rs and gs > bs                                # the signed arrow itself IS green


def test_checklist_kind_signed_marked_and_no_kind_stub():
    rooms = [{"id": "r", "spec": _spec(
        items=[{"name": "ตู้", "kind": "tv_console", "rot": 0,
                "facing_source": "owner-signed", "kind_source": "owner-signed"}])}]
    text = "\n".join(RO.checklist(rooms))
    assert "tv_console (loose) ✓ owner-signed" in text        # kind cell carries provenance
    assert "```json" not in text                              # signed both ways -> no stubs


def test_checklist_kind_stub_is_pasteable_and_rot_free():
    import json
    rooms = [{"id": "sitting_room", "spec": _spec(
        items=[{"name": "โซฟา 3 ที่นั่ง", "kind": "sofa", "rot": 90, "w": 1002, "d": 2202}])}]
    text = RO.checklist(rooms)
    stubs = [json.loads(l) for l in text if l.startswith("{")]
    assert len(stubs) == 2                                    # one facing stub + one kind stub
    fac, kin = stubs                                          # facing section is emitted FIRST
    assert "rot" in fac and "kind" not in fac                 # a facing stub signs facing ONLY
    assert kin["kind"] == "sofa" and "rot" not in kin         # a kind stub signs identity ONLY
    assert kin["room"] == "sitting_room" and kin["name"] == "โซฟา 3 ที่นั่ง"
    assert kin["w"] == 1002 and kin["d"] == 2202              # join keys pre-filled


def test_checklist_kind_stub_only_for_loose_group():
    rooms = [{"id": "r", "spec": _spec(
        builtins=[{"name": "ตู้ BF", "kind": "cabinet"}],
        subrooms=[{"name": "s", "outline_mm": [[0, 0], [1, 0], [1, 1], [0, 1]],
                   "fixtures": [{"name": "wc", "kind": "toilet"}]}])}]
    text = RO.checklist(rooms)
    # builtins/fixtures never consult the ledger — a stub for them would bait the owner into a
    # paste that hard-FAILs the generate as a PLACEMENT-REVIEW ORPHAN. No stub, no bait.
    assert not any(l.startswith("{") for l in text)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} raster_overlay tests passed")
