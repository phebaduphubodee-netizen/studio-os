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
    n, ids, ran = IC.count_items(recs)
    assert ran is False
    n, ids, ran = IC.count_items([
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
