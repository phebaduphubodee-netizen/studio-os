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
