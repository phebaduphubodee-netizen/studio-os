"""P4b: the ONE loose-item convention D7 counts with. Pinned against the real
p3r2 census (the name stems that scene actually holds), so a rename that
silently drops a class from the count turns a test red instead of a phase
green."""
import item_convention as IC


def test_fold_stack_is_one_item_per_stack():
    assert IC.item_id("mill__style_fold0_0__towel") == "fold0"
    assert IC.item_id("mill__style_fold0_3__linen") == "fold0"
    assert IC.item_id("mill__style_fold20_1__backing") == "fold20"


def test_bench_books_are_items_per_book_and_throw_is_one():
    assert IC.item_id("deco__bench_book0_b0") == "book0"
    assert IC.item_id("deco__bench_book0_pg") == "book0"
    assert IC.item_id("deco__bench_book1_sp") == "book1"
    assert IC.item_id("deco__bench_throw") == "bench_throw"


def test_deco_groups_are_items():
    assert IC.item_id("deco__vase_tall__acq0") == "vase_tall"


def test_hanging_and_fixed_dressing_are_not_loose():
    # garments HANG (D-027/D-031 own them); rug/bed/millwork are not styling
    assert IC.item_id("mill__style_garmentacq3_0__acq5") is None
    assert IC.item_id("mill__style_hanger2_0") is None
    assert IC.item_id("rug__พรมใต้เตียง_(anti-monopoly_rug,_D1-A)") is None
    assert IC.item_id("bed__coverlet") is None
    assert IC.item_id("bench__seat") is None
    assert IC.item_id("e5_cove_pelmet") is None
    assert IC.item_id("mill__wardrobe_gable_3") is None
    assert IC.item_id("nightstand__lamp_shade") is None


def test_acc_textiles_carry_ids_visibility_decides():
    # ensuite towels ARE styling items; the FRUSTUM bit (not the convention)
    # is what keeps them out of a bedroom frame's count
    assert IC.item_id("mill__acc_bathtowelpair__acq1") == "acc_bathtowelpair"
    assert IC.item_id("mill__acc_robe0") == "acc_robe0"


def test_count_requires_frustum_bit_else_not_run():
    # an @1 dump (no in_frustum anywhere) must read NOT RUN, never 0
    recs = [{"name": "deco__bench_throw"}]
    n, ids, ran, _unk = IC.count_items(recs)
    assert ran is False
    n, ids, ran, _unk = IC.count_items([
        {"name": "deco__bench_throw", "in_frustum": True, "occluded": False},
        {"name": "mill__style_fold0_0__towel", "in_frustum": True,
         "occluded": True},                                 # part behind a gable
        {"name": "mill__style_fold0_1__towel", "in_frustum": True,
         "occluded": False},                                # ...but this part shows
        {"name": "mill__acc_robe0", "in_frustum": False},   # behind the camera
        {"name": "mill__acc_handtowelhook__acq0", "in_frustum": True,
         "occluded": True},                                 # through-wall: never counts
        {"name": "mill__style_garmentacq0_0__acq1", "in_frustum": True},
        {"name": "deco__bench_book0_b0", "in_frustum": True,
         "hidden_render": True},                            # hidden never counts
    ])
    assert ran is True
    assert ids == ["bench_throw", "fold0"]
    assert n == 2


# --------------------------------- the unknown-name channel (p2r79)

def test_the_acquired_deco_naming_is_an_item():
    """`place_model` writes `deco_<stem>__acq<N>` -- ONE underscore after "deco",
    because the double underscore is the item/part separator. The convention only
    knew `deco__`, so every bought styling object fell past every branch to the
    bare `return None`. Measured on the frame of record 2026-08-26: three of them
    in frustum, D7 printing 0."""
    assert IC.item_id("deco_books__acq0") == "books"
    assert IC.item_id("deco_books__acq1") == "books"
    assert IC.item_id("deco_bedthrow__acq0") == "bedthrow"
    assert IC.item_id("deco_plant__acq2") == "plant"


def test_an_unrecognised_name_is_unknown_and_not_excluded():
    """The distinction the convention could not express. A deliberate exclusion
    and a name no rule has ever seen both returned None, so a build that renames
    its objects silently empties the count instead of failing."""
    assert IC.classify("mill__style_garment0_0")[1] == "excluded"
    assert IC.classify("wall_3z")[1] == "excluded"
    assert IC.classify("deco__bench_book0_b0")[1] == "item"
    assert IC.classify("Sheet")[1] == "unknown"
    assert IC.classify("bf14_sconce_0")[1] == "unknown"


def test_count_items_returns_the_names_it_could_not_classify():
    """In the RETURN, not in a helper: a channel the caller must remember to read
    is a queue whose consumer never visits it."""
    n, ids, ran, unknown = IC.count_items([
        {"name": "deco_books__acq0", "in_frustum": True, "occluded": False},
        {"name": "wall_3z", "in_frustum": True, "occluded": False},
        {"name": "Sheet", "in_frustum": True, "occluded": False},
        {"name": "bf14_sconce_0", "in_frustum": False},
    ])
    assert ran is True
    assert n == 1 and ids == ["books"]
    assert unknown == ["Sheet"], "excluded names are not unknown, and out-of-frustum names are not reported"


def test_the_frustum_zero_case_still_reports_not_run_with_an_empty_unknown_list():
    n, ids, ran, unknown = IC.count_items([{"name": "deco__bench_throw"}])
    assert (n, ids, ran, unknown) == (0, [], False, [])
