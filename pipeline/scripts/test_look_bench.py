"""R4 look_bench armour: pool reuse, deterministic panels, LOCAL-ONLY guard.

The dangerous reverts here: (a) the panel silently drifting off the sellability
lane's audited pool definition (a second definition of "anchor" = the
flattering-scorer shape), (b) a non-deterministic panel making before/after
judgments incomparable, (c) sheets of client imagery landing somewhere
committable.
"""
import pytest

import look_bench


def _rec(path, wh, project="I-01/update"):
    return {"path": path, "wh": wh, "project": project, "bytes": 1}


# ---- pool = the audited definition ----------------------------------------------

def test_pool_excludes_site_photo_and_commercial_like_the_precut():
    cands = [
        _rec("a/Enscape_x.png", (3840, 2160)),                    # engine-named render: in
        _rec("b/img.png", (4032, 3024)),                          # 4:3 >=3000 no engine: site photo
        _rec("c/img.png", (2000, 1400), project="I-02/hospital"), # commercial: out
        _rec("d/img.png", (2000, 1400)),                          # plain residential render: in
    ]
    got = [c["path"] for c in look_bench.anchor_pool(cands)]
    assert got == ["a/Enscape_x.png", "d/img.png"]


def test_orientation_filter_is_apples_to_apples():
    cands = [_rec("p/img.png", (1000, 1600)), _rec("l/img.png", (1600, 1000))]
    assert [c["path"] for c in look_bench.anchor_pool(cands, want_orient="portrait")] == ["p/img.png"]


def test_select_pool_drops_starving_filters_and_says_so():
    # review 2026-07-28: --room bedroom (the docstring's own example) hit an
    # empty pool and a misleading exit; and a loosened panel was labeled with
    # the ORIGINAL orientation. select_pool returns the EFFECTIVE filters.
    cands = [_rec("l/img.png", (1600, 1000))]                 # landscape only, no room hint
    pool, eo, er = look_bench.select_pool(cands, "portrait", "bedroom")
    assert [c["path"] for c in pool] == ["l/img.png"]
    assert eo is None and er is None                          # both filters honestly dropped
    pool2, eo2, er2 = look_bench.select_pool(cands, "landscape", None)
    assert eo2 == "landscape" and er2 is None and pool2       # satisfiable filters kept


# ---- reproduction quarantine (R4 leakage law, qa/reproduction-curriculum.md r.2) --

def test_quarantined_project_never_reaches_the_pool_even_when_it_fits_all_filters():
    tgt = "โปรเจ็ก/002_TRN-target"
    cands = [_rec("t/Enscape_a.png", (2000, 2000), project=tgt),
             _rec("d/img.png", (2000, 1400))]
    got = look_bench.anchor_pool(cands, trained=frozenset({tgt}))
    assert [c["path"] for c in got] == ["d/img.png"]


def test_select_pool_fallback_chain_never_drops_the_quarantine():
    # The chain drops orient/room filters when they starve the pool; it must
    # NEVER drop the quarantine the same way — an all-quarantined pool comes
    # back EMPTY (main() then dies loudly), not silently repopulated.
    tgt = "โปรเจ็ก/002_TRN-target"
    cands = [_rec("t/Enscape_a.png", (2000, 2000), project=tgt)]
    pool, _, _ = look_bench.select_pool(cands, "portrait", "bedroom",
                                        trained=frozenset({tgt}))
    assert pool == []


def test_missing_or_empty_trained_file_is_fatal(tmp_path):
    # Training targets exist since 2026-07-30, so no-file / no-keys can only
    # mean the exclusion list was gutted — refuse, never silent-pass.
    with pytest.raises(SystemExit):
        look_bench.load_trained(str(tmp_path / "absent.json"))
    empty = tmp_path / "empty.json"
    empty.write_text('{"projects": []}', encoding="utf-8")
    with pytest.raises(SystemExit):
        look_bench.load_trained(str(empty))


def test_trained_file_of_record_loads_and_names_trn001_project():
    # The real exclusion list must exist and carry at least one project key.
    keys = look_bench.load_trained()
    assert len(keys) >= 1 and all(isinstance(k, str) and k for k in keys)


# ---- deterministic panel ---------------------------------------------------------

def test_same_name_and_salt_gives_the_same_panel_different_salt_a_new_one():
    pool = [_rec(f"x/{i}.png", (2000, 1400)) for i in range(40)]
    a = look_bench.pick(pool, "room_eye_ql.png", 5, salt=0)
    b = look_bench.pick(pool, "room_eye_ql.png", 5, salt=0)
    c = look_bench.pick(pool, "room_eye_ql.png", 5, salt=1)
    assert [r["path"] for r in a] == [r["path"] for r in b]
    assert [r["path"] for r in a] != [r["path"] for r in c]


def test_panel_never_asks_for_more_than_the_pool_holds():
    pool = [_rec(f"x/{i}.png", (2000, 1400)) for i in range(3)]
    assert len(look_bench.pick(pool, "n.png", 5)) == 3


def test_panel_key_makes_two_DIFFERENT_frames_draw_the_same_anchors():
    """The defect this flag exists for: the panel used to be seeded by FILENAME,
    while the docstring said its purpose was judging a before/after of OUR frame
    against an identical panel — and a before/after always has two filenames. On
    2026-08-15 that drew two different panels for p2r35 and p2r36 at the same
    salt, and our frame placed 6/6 on one sheet and 4/6 on the other."""
    pool = [_rec(f"x/{i}.png", (2000, 1400)) for i in range(40)]
    before = look_bench.pick(pool, "room_eye_p2r35.png", 5, salt=236)
    after = look_bench.pick(pool, "room_eye_p2r36.png", 5, salt=236)
    assert [r["path"] for r in before] != [r["path"] for r in after], \
        "without a panel key, two frames must still draw different panels (the old behaviour)"

    b2 = look_bench.pick(pool, "room_eye_p2r35.png", 5, salt=236, panel_key="ab")
    a2 = look_bench.pick(pool, "room_eye_p2r36.png", 5, salt=236, panel_key="ab")
    assert [r["path"] for r in b2] == [r["path"] for r in a2]


def test_the_key_alone_does_NOT_make_two_sheets_comparable_and_the_fingerprint_says_so():
    """The key pins the DRAW; the pool is the BOX drawn from, and it moves with our
    own image's orientation, --room, the starve-fallback and candidates.json. A
    'comparable' line that cannot be checked would be the same defect as a scale
    ASSERTED in prose against the wrong file, so the fingerprint is printed beside
    the key and must change whenever the draw could."""
    pool = [_rec(f"x/{i}.png", (2000, 1400)) for i in range(40)]
    smaller = pool[:30]
    same_key_wider = look_bench.pick(pool, "a.png", 5, salt=1, panel_key="k")
    same_key_narrower = look_bench.pick(smaller, "b.png", 5, salt=1, panel_key="k")
    assert [r["path"] for r in same_key_wider] != [r["path"] for r in same_key_narrower]
    assert look_bench.panel_fingerprint(pool, 5) != look_bench.panel_fingerprint(smaller, 5)
    # and it must move with n as well as with the pool
    assert look_bench.panel_fingerprint(pool, 5) != look_bench.panel_fingerprint(pool, 6)
    # same box, twice -> same fingerprint
    assert look_bench.panel_fingerprint(pool, 5) == look_bench.panel_fingerprint(list(pool), 5)


# ---- LOCAL-ONLY guard ------------------------------------------------------------

def test_sheet_output_is_allowlisted_to_private_only():
    # ALLOWLIST pin (review 2026-07-28 refuted the denylist twice: NTFS case
    # variants passed straight through, and qa/, docs/, assets/ were never
    # banned at all). Everything not under REPO/_private/ is refused.
    import os
    for banned in ("knowledge/_inbox/sheets", "KNOWLEDGE/_inbox/sheets",
                   "clients/x", "Projects/PRJ-2026-002_c001-house/04_visualization",
                   "qa/reports/look", "docs/sheets", "assets/x", "."):
        with pytest.raises(SystemExit):
            look_bench._guard_out(banned)
    assert look_bench._guard_out(os.path.join(look_bench.REPO, "_private", "benchmark", "look-bench"))


def test_a_blind_panel_never_says_which_one_is_ours(tmp_path):
    """The finish test only means something if the judge is not told the answer.
    `compose` labels OURS and draws a red border round it — correct for R4's
    daily question, fatal for the closing one.

    Pinned on BEHAVIOUR, not on source text: the first cut of this test asserted
    "OURS" not in the function's source and failed on its own docstring, which is
    the test measuring the wrong thing in the smallest possible way."""
    from PIL import Image

    import look_bench as LB

    # 1. the slot moves. A "shuffle" that always returns 0 would pass an eyeball
    # check and fail the only thing it exists for.
    slots = {LB.blind_slot("frame.png", s, 6) for s in range(60)}
    assert len(slots) >= 4, f"blind slot barely moves: {sorted(slots)}"
    assert all(0 <= s < 6 for s in slots)
    assert LB.blind_slot("frame.png", 7, 6) == LB.blind_slot("frame.png", 7, 6)

    # 2. compose a real sheet from solid colours: ours is pure blue, the anchors
    # are greens no red channel can be confused with.
    ours = tmp_path / "ours.png"
    Image.new("RGB", (100, 100), (0, 0, 255)).save(ours)
    anchors = []
    for i in range(4):
        p = tmp_path / f"a{i}.png"
        Image.new("RGB", (100, 100), (0, 100 + i * 20, 0)).save(p)
        anchors.append(str(p))
    slot = LB.blind_slot("ours.png", 0, len(anchors) + 1)
    out, key = LB.compose_blind(str(ours), anchors, str(tmp_path / "blind.png"), slot)

    sheet = Image.open(out).convert("RGB")
    px = sheet.load()
    # 3. no red border anywhere: `compose` draws (255, 80, 80) around our cell,
    # and a blind sheet that kept it would hand the answer over.
    reds = sum(1 for y in range(sheet.height) for x in range(sheet.width)
               if px[x, y] == (255, 80, 80))
    assert reds == 0, f"{reds} border pixels give our frame away"

    # 4. our frame really is AT the slot — a blind sheet that quietly dropped it
    # would pass every check above while testing nothing at all.
    # cells are resized to CELL_H tall, so a square source is CELL_H wide —
    # derive the position, never assume the source size survived
    cw = LB.CELL_H
    cx = LB.PAD + slot * (cw + LB.PAD) + cw // 2
    cy = LB.LABEL_H + LB.PAD + LB.CELL_H // 2
    assert px[cx, cy][2] > 200 and px[cx, cy][1] < 60,         f"cell {slot} is {px[cx, cy]}, not our blue frame"

    # 5. the answer left the sheet rather than vanishing
    assert chr(ord("A") + slot) in open(key, encoding="utf-8").read()
