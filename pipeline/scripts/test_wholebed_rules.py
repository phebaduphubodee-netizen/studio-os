"""Tests for wholebed_rules — pure, no bpy. Run: python -m pytest test_wholebed_rules.py -q

The negative-control candidates are real shelf residents: 0f56d8b6's footboard and
fa59acea's 1053-unit export are the cases the filters exist for.
"""
import wholebed_rules as R


def part(name, lo, hi, tris=1000):
    return {"name": name, "lo": lo, "hi": hi, "tris": tris}


def bed_parts():
    """A plausible whole bed in metres: frame, mattress, duvet, 2 pillows, headboard."""
    return [
        part("frame", (0.0, 0.0, 0.0), (2.10, 2.00, 0.30)),
        part("mattress", (0.05, 0.05, 0.25), (2.05, 1.95, 0.55)),
        part("duvet", (0.10, -0.05, 0.45), (2.00, 2.05, 0.65)),
        part("pillow_a", (1.55, 0.15, 0.55), (2.00, 0.95, 0.75)),
        part("pillow_b", (1.55, 1.05, 0.55), (2.00, 1.85, 0.75)),
        part("headboard", (2.05, -0.05, 0.0), (2.15, 2.05, 1.20)),
    ]


# ---- unit_factor ---------------------------------------------------------------
def test_unit_factor_metres_passes_through():
    f, _ = R.unit_factor(bed_parts())
    assert f == 1.0


def test_unit_factor_inches_detected():
    ps = [part("bed", (0, 0, 0), (84.0, 78.0, 22.0))]  # 84 in = 2.13 m
    f, _ = R.unit_factor(ps)
    assert f == 0.0254


def test_unit_factor_garbage_rejected():
    # fa59acea's real extents land nowhere at any factor together with a bed anchor
    ps = [part("blob", (0, 0, 0), (0.4, 0.3, 0.2))]
    f, why = R.unit_factor(ps)
    assert f is None and "unit factor" in why


# ---- pick_anchor / strip -------------------------------------------------------
def test_anchor_is_the_big_bed_part():
    a = R.pick_anchor(bed_parts())
    assert a and a["name"] in ("frame", "duvet", "mattress")


def test_anchor_refuses_a_lamp_only_file():
    ps = [part("lamp", (0, 0, 0), (0.3, 0.3, 0.6))]
    assert R.pick_anchor(ps) is None


def test_strip_drops_wall_pendant_and_neighbour_keeps_pillow():
    ps = bed_parts()
    anchor = R.pick_anchor(ps)
    wall = part("backdrop", (2.2, -1.0, 0.0), (2.25, 3.0, 2.9))
    pend = part("pendant", (1.0, -0.3, 1.6), (1.2, -0.1, 2.6))
    stand = part("nightstand", (0.5, 2.4, 0.0), (1.0, 2.9, 0.55))
    keep, dropped = R.strip(ps + [wall, pend, stand], anchor)
    dropped_names = {p["name"] for p, _ in dropped}
    assert {"backdrop", "pendant", "nightstand"} <= dropped_names
    assert {p["name"] for p in keep} >= {"frame", "mattress", "duvet", "pillow_a"}


# ---- head_end ------------------------------------------------------------------
def test_head_end_finds_the_tall_end():
    assert R.head_end(bed_parts(), axis=0) == "hi"


def test_head_end_refuses_a_flat_platform():
    ps = [part("slab", (0, 0, 0), (2.1, 2.0, 0.4))]
    assert R.head_end(ps, axis=0) is None


# ---- headboard_parts -----------------------------------------------------------
def test_separable_headboard_found_not_fused():
    ps = bed_parts()
    plane = 0.60
    sep, fused = R.headboard_parts(ps, plane, head_x=2.15, head="hi")
    assert [p["name"] for p in sep] == ["headboard"]
    assert fused is False


def test_fused_headboard_recorded_not_missed():
    # one mesh: bed body + built-in headboard rising 0.6 over the plane
    ps = [part("wholebed", (0.0, 0.0, 0.0), (2.15, 2.0, 1.20))]
    sep, fused = R.headboard_parts(ps, plane_z=0.60, head_x=2.15, head="hi")
    assert sep == [] and fused is True


def test_pillow_bank_survives_headboard_strip():
    """The first batch run's defect: e63ab045's pillows stood in the head band
    above plane+0.35 and were deleted as 'headboard'. Individual pillows are
    never half the bed wide — they must survive."""
    ps = bed_parts()
    tall_pillow = part("euro_sham", (1.75, 0.20, 0.55), (2.05, 1.00, 1.02))
    sep, fused = R.headboard_parts(ps + [tall_pillow], plane_z=0.60,
                                   head_x=2.15, head="hi")
    assert "euro_sham" not in [p["name"] for p in sep]
    assert fused is False


def test_nightstand_wing_not_tagged_headboard():
    """Band-reach alone tagged bd96c4ff's nightstand wings; a wing is neither
    wide across the bed nor a headboard."""
    ps = bed_parts()
    wing = part("wing", (1.80, -0.55, 0.0), (2.15, 0.0, 0.78))
    sep, fused = R.headboard_parts(ps + [wing], plane_z=0.60, head_x=2.15, head="hi")
    assert "wing" not in [p["name"] for p in sep]
    assert fused is False


# ---- foot_over_plane (the ink's no-footboard test) -----------------------------
def test_footboard_fails_the_ink():
    ps = bed_parts() + [part("footboard", (-0.10, 0.0, 0.0), (0.0, 2.0, 0.90))]
    rise = R.foot_over_plane(ps, plane_z=0.60, foot_x=-0.10, head="hi")
    assert rise > R.FOOT_ABOVE_PLANE_M


def test_rolled_duvet_edge_passes_the_ink():
    rise = R.foot_over_plane(bed_parts(), plane_z=0.60, foot_x=0.0, head="hi")
    assert rise <= R.FOOT_ABOVE_PLANE_M


# ---- plan_scale_whole ----------------------------------------------------------
def test_scale_never_stretches():
    s, fl, fw = R.plan_scale_whole(1.90, 2.00)  # smaller than 2.000 x 2.149
    assert s == 1.0 and fl < 1.0 and fw < 1.0


def test_scale_shrinks_oversize_uniformly():
    s, fl, fw = R.plan_scale_whole(2.50, 2.20)
    assert s < 1.0
    assert abs(fl - 1.0) < 1e-6 or abs(fw - 1.0) < 1e-6  # one axis lands exactly


# ---- verdict -------------------------------------------------------------------
def base_row():
    return {"anchor_found": True, "orientation": "head at x-hi",
            "fill_len": 0.95, "fill_w": 0.93, "foot_over_plane_m": 0.05,
            "headboard_fused": False,
            "field_fill_len": 0.95, "field_fill_w": 0.93,
            "anchor_projected_mm": [1800, 2000],
            "anchor_std": {"name": "th_king_6ft", "slot_mm": [1800, 2000],
                           "worst_mm": 0, "within": True, "tol_mm": 50,
                           "part": "Matress",
                           "nearest_any": {"name": "th_king_6ft", "worst_mm": 0},
                           "best_uniform": {"scale": 1.0, "name": "th_king_6ft",
                                            "worst_mm": 0}},
            "mattress_fill": [1.0, 1.0],
            "frame_staged_mm": [1842, 2033], "made_bed_mm": [2079, 2128],
            "ink_bed_mm": [1981, 2134]}


def test_verdict_passes_a_clean_row():
    ok, why = R.verdict(base_row())
    assert ok and why == []


def test_verdict_fails_footboard_fill_fused_and_coinflip():
    row = base_row()
    row.update({"foot_over_plane_m": 0.40, "fill_len": 0.70,
                "headboard_fused": True, "orientation": "unresolved"})
    ok, why = R.verdict(row)
    assert not ok and len(why) == 4


def test_verdict_unmeasured_foot_is_named_not_clean():
    """Could-not-measure must never read as clean (the repo's exit-2 law): a None
    foot rise is a filter reason with the word UNMEASURED, never a silent pass and
    never a TypeError-crash."""
    row = base_row()
    row["foot_over_plane_m"] = None
    ok, why = R.verdict(row)
    assert not ok and any("UNMEASURED" in w for w in why)


def test_unit_factor_prefers_the_bed_scale_reading():
    """A file whose extent lands in the scene band under two factors resolves by
    which factor puts a bed-anchor-sized part in the anchor band; still-ambiguous
    files reject rather than guess (R8)."""
    ps = [part("bed", (0, 0, 0), (84.0, 78.0, 22.0)),   # 84 in = 2.13 m bed
          part("room", (0, 0, 0), (300.0, 250.0, 100.0))]  # drags extent large
    f, why = R.unit_factor(ps)
    assert f in (None, 0.0254)  # never a silent third guess
    if f is None:
        assert "ambiguous" in why or "unit factor" in why


# ---- integration strip (P2r-52, D-107) — fixtures are the WINNER'S own staged
# ---- millimetres from the p2r51 bench row, in metres, head at x-hi ------------
def winner_parts():
    """f52472c1 staged: anchor frame + mattress + duvet + burl panel + 2 shelf
    boards + plaid band + 2 pillows + 3 shams. Positions reconstructed from the
    id-coloured identification views (2026-08-18); sizes are the bench row's."""
    plane = 0.4276
    return {
        "plane": plane,
        "anchor": part("frame", (0.0, 0.0, 0.0), (1.592, 2.149, 0.199)),
        "mattress": part("mattress", (0.03, 0.44, 0.28), (1.599, 1.683, plane)),
        "duvet": part("duvet", (0.05, 0.30, 0.30), (1.272, 1.841, 0.819)),
        "burl": part("panel", (1.970, 0.0, 0.05), (1.994, 2.149, 0.727)),
        "board_s": part("board_s", (1.30, 0.10, 0.20), (1.314, 0.559, 0.331)),
        "board_n": part("board_n", (1.30, 1.59, 0.20), (1.314, 2.049, 0.331)),
        "plaid": part("plaid", (0.95, 0.60, plane), (1.304, 1.534, plane + 0.214)),
        "pillow_a": part("pillow_a", (1.45, 0.55, plane), (1.662, 1.038, plane + 0.354)),
        "pillow_b": part("pillow_b", (1.45, 1.10, plane), (1.662, 1.588, plane + 0.354)),
        "sham_a": part("sham_a", (1.60, 0.40, plane), (1.908, 0.894, plane + 0.452)),
        "sham_b": part("sham_b", (1.60, 0.90, plane), (1.908, 1.394, plane + 0.452)),
        "sham_c": part("sham_c", (1.60, 1.40, plane), (1.908, 1.894, plane + 0.452)),
    }


def _all(w):
    return [v for k, v in w.items() if k not in ("plane",)]


def test_head_panel_catches_the_burl_and_nothing_soft():
    w = winner_parts()
    hits = R.head_panel_parts(_all(w), w["plane"], head_x=2.0, head="hi",
                              bed_w=2.149, anchor=w["anchor"])
    assert [p["name"] for p in hits] == ["panel"]


def test_head_panel_spares_the_sham_bank():
    """The shams reach the head band and stand above the plane but are neither
    thin nor full-width — the first bench run's pillow-bank deletion is the
    mistake this assert pins against recurrence."""
    w = winner_parts()
    hits = R.head_panel_parts([w["sham_a"], w["sham_b"], w["sham_c"]], w["plane"],
                              head_x=2.0, head="hi", bed_w=2.149)
    assert hits == []


def test_dead_side_boards_catches_the_shelf_pair_only():
    w = winner_parts()
    hits = R.dead_side_boards(_all(w), w["plane"], anchor=w["anchor"])
    assert sorted(p["name"] for p in hits) == ["board_n", "board_s"]


def test_dead_side_boards_spares_the_mattress_and_frame():
    """The mattress top IS the plane (not below it) and the frame is the anchor
    (exempt by identity, not by tuning)."""
    w = winner_parts()
    hits = R.dead_side_boards([w["anchor"], w["mattress"]], w["plane"],
                              anchor=w["anchor"])
    assert hits == []


def test_flat_accent_catches_the_plaid_band_only():
    w = winner_parts()
    hits = R.flat_accents_on_bank(_all(w), w["plane"], anchor=w["anchor"])
    assert [p["name"] for p in hits] == ["plaid"]


def test_flat_accent_exempts_bedding_by_plan_share_not_by_name():
    """The duvet lies flatter than it is wide too — it is exempt because it IS
    the bedding field (>= 0.35 of the drawn plan), never because of a name."""
    w = winner_parts()
    hits = R.flat_accents_on_bank([w["duvet"]], w["plane"])
    assert hits == []


def test_flat_accent_spares_standing_pillows():
    w = winner_parts()
    hits = R.flat_accents_on_bank(
        [w["pillow_a"], w["pillow_b"], w["sham_a"]], w["plane"])
    assert hits == []


def test_frame_cluster_excludes_overhang_and_side_furniture():
    """The scale denominator: a nightstand wing outside the anchor's plan and a
    drape overhanging it stay OUT (bd96c4ff's fill failure was exactly the wing
    widening the file bbox); the mattress inside stays IN."""
    w = winner_parts()
    wing = part("wing", (0.2, -0.4, 0.0), (0.9, -0.05, 0.45))     # off the anchor
    drape = part("drape", (0.1, -0.1, 0.3), (1.5, 2.30, 0.7))     # overhangs both flanks
    cl = R.frame_cluster([w["anchor"], w["mattress"], wing, drape], w["anchor"])
    assert sorted(p["name"] for p in cl) == ["frame", "mattress"]


# ---- made_field / field_fill (P2r-53, ORD-2026-08-18-bed-too-small) -------------
def f52472c1_staged_parts():
    """The REAL p2r52 staging, metres, read off room_bedroom_suite_eye_p2r52
    .scene.json — the frame the owner failed from the image. Platform (anchor,
    with integral wings) 2149 wide; mattress 1243; cloth 1541; two sham pairs.
    Axis 0 = head-foot (drawn 2.000), axis 1 = width (drawn 2.149)."""
    return [
        part("platform", (3.534, 0.051, 0.004), (5.126, 2.200, 0.203)),
        part("mattress", (3.572, 0.510, 0.200), (5.141, 1.752, 0.347)),
        part("cloth",    (3.368, 0.342, 0.000), (4.591, 1.883, 0.519)),
        part("headset0", (4.787, 0.689, 0.334), (4.999, 1.176, 0.688)),
        part("headset1", (4.787, 1.126, 0.334), (4.999, 1.614, 0.688)),
    ]


def test_made_field_regression_f52472c1_is_refused():
    """The staged winner the owner failed: its made-bed field reaches 1541 mm of
    the drawn 2149 (0.72). The rule that did not exist on 2026-08-17 refuses it."""
    ps = f52472c1_staged_parts()
    anchor = ps[0]
    field = R.made_field(ps, anchor)
    assert {p["name"] for p in field} == {"mattress", "cloth", "headset0", "headset1"}
    fl, fw = R.field_fill(field)
    assert fw < R.MIN_FIELD_FILL, f"width fill {fw:.2f} must refuse"
    row = {"anchor_found": True, "orientation": "head at x-hi",
           "fill_len": 0.90, "fill_w": 1.0, "foot_over_plane_m": 0.0,
           "headboard_fused": False,
           "field_fill_len": fl, "field_fill_w": fw}
    ok, why = R.verdict(row)
    assert not ok and any("ORD-2026-08-18" in w for w in why)


def test_made_field_true_king_passes():
    """A wingless king: mattress 1.80 wide, duvet draping to 2.05, pillows.
    Its field reaches the drawn rectangle on both axes."""
    ps = [
        part("frame",    (0.05, 0.15, 0.0),  (2.00, 2.05, 0.30)),
        part("mattress", (0.10, 0.20, 0.28), (2.00, 2.00, 0.55)),
        part("duvet",    (0.02, 0.05, 0.40), (1.98, 2.10, 0.70)),
        part("pillow",   (1.55, 0.40, 0.55), (2.00, 1.80, 0.80)),
    ]
    anchor = ps[0]
    field = R.made_field(ps, anchor)
    fl, fw = R.field_fill(field)
    assert fl >= R.MIN_FIELD_FILL and fw >= R.MIN_FIELD_FILL


def test_made_field_excludes_standing_panel_keeps_bedding():
    """The burl head panel (24 mm thin, 677 tall) rises above the anchor but is
    hard furniture; the duvet is never plate-thin while standing tall."""
    ps = f52472c1_staged_parts()
    ps.append(part("burl_panel", (5.10, 0.051, 0.20), (5.124, 2.200, 0.877)))
    field = R.made_field(ps, ps[0])
    names = {p["name"] for p in field}
    assert "burl_panel" not in names and "cloth" in names


def test_field_fill_empty_is_zero_never_clean():
    assert R.field_fill([]) == (0.0, 0.0)


def test_verdict_field_unmeasured_is_named_not_clean():
    """A pre-rule bench row carries no field keys: UNMEASURED, never a pass."""
    row = base_row()
    del row["field_fill_len"], row["field_fill_w"]
    ok, why = R.verdict(row)
    assert not ok and any("UNMEASURED" in w for w in why)


# ---- ORD-2026-08-22 front door: projected mattress must be SOME standard size --
def test_verdict_nonstandard_projected_mattress_refused():
    """f52472c1's real staged numbers: wings capped s at 0.68 and the mattress
    projected to 1243x1569 — 336+ mm from every US and Thai standard. The p2r52
    frame shipped because no rung made this comparison; this one does."""
    row = base_row()
    row["anchor_projected_mm"] = [1243, 1569]
    row["anchor_std"].update({"worst_mm": 557, "within": False,
                              "nearest_any": {"name": "th_single_3_5ft", "worst_mm": 411},
                              "best_uniform": {"scale": 0.86, "name": "twin",
                                               "worst_mm": 21}})
    row["mattress_fill"] = [0.69, 0.78]
    ok, why = R.verdict(row)
    assert not ok and any("ORD-2026-08-22" in w for w in why)


def test_verdict_refuses_a_pre_d120_frame_row_at_150():
    """chunkA's real Bolzan row: the FRAME projected at 0.91 to 1676x1951 with
    within=True at the cluster's +-150. The new rule must not read that shape
    as a bare-mattress pass — the old ledger can never pass again."""
    row = base_row()
    row["anchor_projected_mm"] = [1676, 1951]
    row["anchor_std"] = {"name": "th_king_6ft", "worst_mm": 124, "within": True}
    ok, why = R.verdict(row)
    assert not ok and any("+-150" in w and "D-120" in w for w in why)


def test_verdict_refuses_a_standard_bed_too_small_for_the_slot():
    """Slate (8968de2e): its Mattress is 1336x1895 — a 'full' within 36, so the
    front door said yes; under a 1641 quilt the cluster fill and the field both
    passed too. A bed 0.74 of the slot's width is the owner's 'เตียงเล็กไป'
    with a standard label on it (D-120: the slab answers to the SLOT)."""
    row = base_row()
    row["anchor_projected_mm"] = [1336, 1895]
    row["anchor_std"].update({"worst_mm": 464, "within": False,
                              "nearest_any": {"name": "full", "worst_mm": 36},
                              "best_uniform": {"scale": 1.0, "name": "full",
                                               "worst_mm": 36}})
    row["mattress_fill"] = [0.742, 0.948]
    ok, why = R.verdict(row)
    assert not ok
    assert any("it IS a full (within 36 mm)" in w for w in why)      # names the way out
    assert any("the mattress itself fills 0.74" in w for w in why)


def test_verdict_refuses_an_unmeasured_mattress_fill():
    row = base_row()
    del row["mattress_fill"]
    ok, why = R.verdict(row)
    assert not ok and any("mattress-vs-slot fill UNMEASURED" in w for w in why)


def test_verdict_missing_anchor_std_is_named_not_clean():
    """A row benched before the front-door rule: UNMEASURED, never a pass —
    the same ratchet the field rule set (an old ledger can never pass again)."""
    row = base_row()
    del row["anchor_std"], row["anchor_projected_mm"]
    ok, why = R.verdict(row)
    assert not ok and any("front-door" in w for w in why)


def test_field_fill_axis_len_maps_room_axes():
    """The integration hook runs after rotation: length may sit on either room
    axis. axis_len=1 measures length on y."""
    f = [part("duvet", (0.0, 0.0, 0.4), (2.10, 1.95, 0.7))]
    fl_a, fw_a = R.field_fill(f, fit_len=2.0, fit_w=2.149, axis_len=1)
    assert abs(fl_a - 1.95 / 2.0) < 1e-9 and abs(fw_a - 2.10 / 2.149) < 1e-9


# ---- field_verdict (the R13 third state) ---------------------------------------
def test_field_verdict_pass_needs_no_signature():
    assert R.field_verdict(0.95, 0.99) == "pass"


def test_field_verdict_deficit_unsigned_is_a_hard_stop():
    assert R.field_verdict(0.90, 0.72) == "fail"
    assert R.field_verdict(0.90, 0.72, signed={}) == "fail"
    assert R.field_verdict(0.90, 0.72, signed={"decision": "D-108"}) == "fail"


def test_field_verdict_signed_deficit_is_interim_never_pass():
    s = {"decision": "D-108", "ask": "ASK-028"}
    assert R.field_verdict(0.90, 0.72, signed=s) == "interim"
    # a signature cannot upgrade a passing field to anything else
    assert R.field_verdict(0.95, 0.99, signed=s) == "pass"


# ---- p2r54: the field's denominator must be the BED, not the file -------------
def rider_parts():
    """81d895fd staged (head normalized to x-hi): fused frame+mattress anchor,
    duvet draping past the foot, four pillows pressing the head, a foot throw,
    two under-mattress slabs — PLUS the furniture that rides along in the file:
    a two-layer fabric headboard WALL standing on the floor behind the head
    (wider than the frame by 0.59 m each side) and two flanking closet bodies
    with their doors. Extents are the 2026-08-18 probe of the GLB, native
    metres, axes rotated head-to-x-hi. The wall's width IS what the bench's
    field read as 'fill 1.00' — the defect this fixture pins."""
    return {
        "plane": 0.535,
        "anchor": part("frame", (-1.031, -0.794, 0.096), (1.016, 0.784, 0.454)),
        "duvet": part("duvet", (-1.170, -0.862, 0.0), (0.686, 0.850, 0.544)),
        "throw": part("throw", (-0.974, -1.021, 0.0), (-0.027, 0.967, 0.627)),
        "pillow_a": part("pillow_a", (0.633, -0.014, 0.441), (1.034, 0.759, 0.761)),
        "pillow_b": part("pillow_b", (0.679, -0.728, 0.394), (1.045, -0.016, 0.764)),
        "pillow_c": part("pillow_c", (0.566, -0.645, 0.430), (0.827, -0.086, 0.755)),
        "pillow_d": part("pillow_d", (0.561, 0.085, 0.460), (0.818, 0.628, 0.708)),
        "slab_hi": part("slab_hi", (-0.942, -0.699, 0.221), (0.958, 0.701, 0.421)),
        "slab_lo": part("slab_lo", (-0.942, -0.699, 0.001), (0.958, 0.701, 0.221)),
        "wall_1": part("wall_1", (0.948, -1.360, 0.0), (1.110, 1.399, 0.591)),
        "wall_2": part("wall_2", (0.981, -1.238, 0.0), (1.049, 1.274, 0.633)),
        "closet_a": part("closet_a", (0.563, 0.783, 0.001), (0.959, 1.283, 0.451)),
        "closet_b": part("closet_b", (0.563, -1.243, 0.001), (0.959, -0.743, 0.451)),
        "door_a": part("door_a", (0.579, 0.783, 0.061), (0.594, 1.283, 0.420)),
        "door_b": part("door_b", (0.579, -1.243, 0.061), (0.594, -0.743, 0.420)),
    }


def test_overlap_frac_separates_bed_layers_from_riders():
    w = rider_parts()
    assert R.plan_overlap_frac(w["duvet"], w["anchor"]) > 0.8
    assert R.plan_overlap_frac(w["throw"], w["anchor"]) > 0.7
    assert R.plan_overlap_frac(w["wall_1"], w["anchor"]) < 0.3
    assert R.plan_overlap_frac(w["closet_a"], w["anchor"]) < 0.1


def test_made_field_refuses_the_backdrop_wall():
    """The honest field: bedding + pillows + throw. The 2.759 m wall panel and
    the closets never count — the width the field reports must be the BED's
    (1.988 m), not the wall's. This is the number the first-ever 'field pass'
    was wrong by (0.888x1.00 printed; the bed itself reaches 0.835 on width at
    the containment-capped scale)."""
    w = rider_parts()
    f = R.made_field(_all(w), w["anchor"])
    names = sorted(p["name"] for p in f)
    assert "wall_1" not in names and "wall_2" not in names
    assert "closet_a" not in names and "closet_b" not in names
    assert {"duvet", "throw"} <= set(names)
    wid = max(p["hi"][1] for p in f) - min(p["lo"][1] for p in f)
    assert abs(wid - 1.988) < 0.01


def test_carry_ons_names_both_families_by_geometry():
    w = rider_parts()
    hits = R.carry_ons(_all(w), w["plane"], w["anchor"])
    got = {p["name"]: why for p, why in hits}
    assert set(got) == {"wall_1", "wall_2", "closet_a", "closet_b",
                        "door_a", "door_b"}
    assert "cabinet" in got["closet_a"] and "cabinet" in got["door_a"]
    assert "panelling" in got["wall_1"] and "panelling" in got["wall_2"]


def test_carry_ons_spares_every_bed_layer():
    w = rider_parts()
    hits = R.carry_ons([w["duvet"], w["throw"], w["pillow_a"], w["slab_hi"],
                        w["slab_lo"]], w["plane"], w["anchor"])
    assert hits == []


def test_flat_accent_head_term_spares_the_lying_pillow_bank():
    """81d895fd's pillows lie flatter than their plan (0.79-0.96 of smallest
    dim) — the pre-p2r54 flatness test alone ate two of them. They press the
    head (0.02-0.29 m), the plaid lies 0.70 m out on the field: the head term
    is what separates the measured families."""
    w = rider_parts()
    head_x = max(p["hi"][0] for p in _all(w))
    hits = R.flat_accents_on_bank(_all(w), w["plane"], anchor=w["anchor"],
                                  head_x=head_x, head="hi")
    assert hits == []


def test_flat_accent_head_term_still_catches_the_plaid():
    w = winner_parts()
    hits = R.flat_accents_on_bank(_all(w), w["plane"], anchor=w["anchor"],
                                  head_x=2.0, head="hi")
    assert [p["name"] for p in hits] == ["plaid"]


# ---- D-120: the MATTRESS by geometry; the frame is not the bed's size ---------
# The families below carry the NUMBERS measured on the cached candidates
# (wholebed_dump.py, 2026-08-23, native metres): a test that reproduces a real
# file's parts is a test that would have caught the real defect.
def _p(name, lo, hi, cover=None, top=None, relief=None):
    d = part(name, lo, hi)
    if cover is not None:
        d.update({"cover": cover, "top_med": top, "relief": relief})
    return d


def metropol_parts():
    """e2418055 — frame hollow (cover 0), mattress 1786 x 1980 x 247 flat slab,
    foot sheet strip, blanket with folds, low cushions. The frame is 1842 x 2033."""
    return {
        "frame": _p("Bed Frame", (0.0, 0.0, 0.034), (2.033, 1.842, 0.386), 0.0, None, None),
        "support": _p("Bed Support", (0.08, 0.10, 0.0), (1.95, 1.75, 0.059), 0.0, None, None),
        "matt": _p("Matress", (0.03, 0.028, 0.273), (2.01, 1.814, 0.520), 1.0, 0.513, 0.011),
        "sheet": _p("Sheet", (0.0, -0.12, 0.081), (0.576, 1.96, 0.541), 1.0, 0.523, 0.019),
        "blanket": _p("Blanket", (0.30, -0.09, 0.109), (1.66, 1.92, 0.543), 1.0, 0.513, 0.024),
        "cushions": _p("Cusions", (1.40, 0.0, 0.428), (1.99, 1.836, 0.857), 0.99, 0.786, 0.163),
        "head": _p("Head board", (1.62, -0.08, 0.036), (2.03, 1.92, 0.964), 0.92, 0.889, 0.258),
    }


def test_mattress_is_the_slab_not_the_frame_metropol():
    w = metropol_parts()
    ps = list(w.values())
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is w["frame"]                      # organising part: the frame
    m, note = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is w["matt"], note
    sz = R.size(m)
    # the front door at scale 1.0: 1786 x 1980 is the Thai 6 ft king within 20
    s = R.mattress_scale(sz[0], sz[1], 2.0, 1.8)
    assert s == 1.0
    assert abs(sz[1] * s - 1.786) < 0.002 and abs(sz[0] * s - 1.98) < 0.002


def test_cluster_fit_was_the_defect_metropol():
    """THE NEGATIVE CONTROL, with the arithmetic the real bench actually ran.
    The old rule fitted the whole kept CLUSTER — frame plus the sheet's drape,
    2079 wide — into the 2000 x 1800 slot: s = 0.841, at which the real
    mattress projects to 1502 x 1665, which is no standard at either
    tolerance. (The frame ALONE would have fitted at 0.977 and passed, which
    is why the defect needed the cluster to appear at all.) The rule under
    test reads the mattress instead and returns exactly 1.0."""
    import ergonomics_ref as E
    s_cluster, _, _ = R.plan_scale_whole(2.128, 2.079, 2.0, 1.8)
    assert abs(s_cluster - 0.8658) < 0.001
    _, _, ok, worst = E.nearest_bed_size(round(1.786 * s_cluster * 1000),
                                         round(1.980 * s_cluster * 1000))
    assert not ok and worst > 150
    w = metropol_parts()
    m, _ = R.pick_mattress(list(w.values()), w["frame"], drawn_plan_m2=3.6)
    sz = R.size(m)
    assert R.mattress_scale(sz[0], sz[1], 2.0, 1.8) == 1.0


def test_seam_piping_never_the_mattress_obsidian():
    """b4915f0a: 'Base Seams' spans 1950 x 2144 over the Base (2023 x 2179) and
    holds NO surface (cover 0.00); 'Quilt Seams' cover 0.06. The Sheet (1671 x
    2012, cover 1.0, relief 0) is the slab; the Quilt has folds (relief 34)."""
    base = _p("Base", (0.0, 0.0, 0.001), (2.179, 2.023, 0.252), 1.0, 0.195, 0.0)
    seams = _p("Base Seams", (0.02, 0.04, 0.001), (2.164, 1.99, 0.201), 0.0, None, None)
    sheet = _p("Sheet", (0.08, 0.18, 0.169), (2.092, 1.851, 0.417), 1.0, 0.417, 0.0)
    quilt = _p("Quilt", (0.10, 0.06, 0.160), (2.06, 1.96, 0.469), 1.0, 0.437, 0.034)
    qseams = _p("Quilt Seams", (0.10, 0.07, 0.174), (2.06, 1.95, 0.451), 0.06, 0.425, 0.001)
    head = _p("Headboard", (1.90, 0.04, 0.001), (2.18, 1.99, 0.795), 1.0, 0.785, 0.066)
    ps = [base, seams, sheet, quilt, qseams, head]
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is base
    m, note = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is sheet, note


def test_hidden_face_mattress_still_qualifies_bolzan():
    """17aff0ff: the author deleted the mattress faces under the bedding —
    'mattres' 1800 x 2114 has cover 0.25 and relief 1 mm. The thin 'base bed'
    plate (35 mm) and the hollow body (cover 0) do not qualify; the half-bed
    blankets fail the span."""
    body = _p("body bed", (0.0, 0.0, 0.026), (2.144, 1.842, 0.316), 0.0, None, None)
    plate = _p("base bed", (0.07, 0.07, 0.0), (2.07, 1.77, 0.035), 0.0, None, None)
    matt = _p("mattres", (0.015, 0.021, 0.271), (2.129, 1.821, 0.539), 0.25, 0.537, 0.001)
    blanket = _p("blanket", (0.0, -0.03, 0.128), (0.788, 1.874, 0.574), 1.0, 0.562, 0.011)
    blanket2 = _p("blanket.001", (0.2, -0.06, 0.068), (0.939, 1.90, 0.615), 1.0, 0.59, 0.026)
    ps = [body, plate, matt, blanket, blanket2]
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is body
    m, note = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is matt, note
    # 1800 x 2114: no US/TH standard within +-50 at any uniform scale <= 1
    import ergonomics_ref as E
    sc, nm, worst = R.best_uniform_fit(1800, 2114, {**E.BED_SIZES_MM, **E.BED_SIZES_TH_MM})
    assert nm == "th_king_6ft" and 50 < worst < 60


def test_anchor_that_is_the_mattress_needs_a_frame_under_it_ikea():
    """10b19e20: 'Bedsheets' (1957 x 2013) out-plans the frame by 1% and is the
    anchor; the frame beneath (top 300 <= its bottom 290 + 50) is what makes it
    a mattress. Without anything under it, a lone slab is a platform, not a
    mattress (the anchor never passes the floor term on its own)."""
    sheets = _p("Bedsheets", (0.0, 0.0, 0.290), (2.013, 1.957, 0.567), 1.0, 0.533, 0.009)
    frame = _p("frame", (0.0, 0.01, 0.04), (2.02, 1.94, 0.30), 0.0, None, None)
    base = _p("Base", (0.02, 0.05, 0.0), (1.999, 1.91, 0.04), 1.0, 0.04, 0.0)
    ps = [sheets, frame, base]
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is sheets
    m, _ = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is sheets
    m2, note = R.pick_mattress([sheets], sheets, drawn_plan_m2=3.6)
    assert m2 is None and "no slab" in note


def test_one_mesh_bed_is_unmeasurable_not_a_frame_number_tierra():
    """b8359da9 is one mesh. No slab qualifies -> (None, why); the bench then
    records UNMEASURED and verdict refuses — never the frame's 2425 x 2484."""
    one = _p("Tierra Bed", (0.0, 0.0, -0.008), (2.484, 2.425, 0.705), 1.0, 0.438, 0.2)
    a = R.pick_anchor([one], drawn_plan_m2=3.6)
    m, note = R.pick_mattress([one], a, drawn_plan_m2=3.6)
    assert m is None and "one-mesh" in note
    row = base_row()
    row["anchor_projected_mm"] = None
    row["anchor_std"] = {"name": None, "worst_mm": None, "within": False, "unmeasured": note}
    ok, why = R.verdict(row)
    assert not ok and any("UNMEASURABLE" in w and "D-120" in w for w in why)


def test_unprobed_parts_never_qualify():
    """A part without cover/top_med/relief cannot be the mattress: could-not-
    measure must not read as a slab."""
    ps = bed_parts()
    a = R.pick_anchor(ps)
    m, note = R.pick_mattress(ps, a)
    assert m is None and "unprobed" in note


def test_flat_blanket_ties_go_to_the_larger_slab():
    """A blanket lying flat ON the mattress tops out at the same z (Metropol:
    both 513); the tie within 10 mm goes to the larger plan — the slab."""
    w = metropol_parts()
    w["blanket"]["relief"] = 0.010         # flatter than measured: a harder case
    ps = list(w.values())
    m, _ = R.pick_mattress(ps, w["frame"], drawn_plan_m2=3.6)
    assert m is w["matt"]


def test_draped_duvet_fails_the_floor_term():
    """81d895fd's duvet hem reaches the floor (lo z 0.0) — a mattress never
    does. Cube.015 (1400 x 1900 x 200, resting at 221) is the slab."""
    sheet = _p("Plane.029", (0.0, 0.0, 0.096), (2.047, 1.578, 0.454), 1.0, 0.443, 0.0)
    duvet = _p("Plane.030", (0.1, -0.07, 0.0), (1.956, 1.642, 0.544), 1.0, 0.482, 0.054)
    core = _p("Cube.015", (0.07, 0.089, 0.221), (1.97, 1.489, 0.421), 1.0, 0.421, 0.0)
    base = _p("Cube.016", (0.07, 0.089, 0.001), (1.97, 1.489, 0.221), 1.0, 0.221, 0.0)
    ps = [sheet, duvet, core, base]
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is sheet
    m, _ = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is core


def test_mattress_scale_never_stretches_and_reports_overhang():
    assert R.mattress_scale(1.98, 1.786, 2.0, 1.8) == 1.0          # smaller than the slot
    assert abs(R.mattress_scale(2.114, 1.80, 2.0, 1.8) - 0.946) < 0.001
    oh = R.overhang_mm(2.033, 1.842, 2.0, 1.8)
    assert oh == {"foot": 33, "side_each": 21}
    assert R.overhang_mm(1.9, 1.7, 2.0, 1.8) == {"foot": 0, "side_each": 0}


def test_frame_ink_cap_is_a_verdict_rule_cloth_is_not():
    """The drawn bed (SR-07, 1981 x 2134) is the widest FRAME the sheet allows.
    Metropol's frame (1842 x 2033) is inside and its sheet draping to 2079
    across is cloth over the gap — reported, never the verdict. Obsidian's
    base (2011 x 2166 at slot-fit) passes the ink by 30 / 32; a missing ink
    row is UNMEASURED."""
    ok, ow, ol = R.made_bed_within_ink(1.842, 2.033, 1.981, 2.134)
    assert ok and ow == 0 and ol == 0
    ok, ow, ol = R.made_bed_within_ink(2.011, 2.166, 1.981, 2.134)
    assert not ok and ow == 20 and ol == 22          # past the 10 mm ink tolerance
    row = base_row()                                  # made bed 2079 wide: passes
    ok, why = R.verdict(row)
    assert ok, why
    assert row["frame_staged_mm"] == [1842, 2033]
    row["frame_staged_mm"] = [2011, 2166]
    ok, why = R.verdict(row)
    assert not ok and any("SR-07" in w for w in why)
    row = base_row()
    row["ink_bed_mm"] = None
    ok, why = R.verdict(row)
    assert not ok and any("UNMEASURED" in w and "R12" in w for w in why)


def test_verdict_names_the_best_uniform_fit_when_refusing():
    """Ikea Nordli: a US king squeezed into the Thai-king slot lands at
    1800x1852 — no standard. With no other standard within tolerance the line
    reports the best uniform fit, so the reader can see whether ANY scale
    reaches a real bed (here 0.998 does, but the slot forbids it)."""
    row = base_row()
    row["anchor_projected_mm"] = [1800, 1852]
    row["anchor_std"].update({"worst_mm": 148, "within": False,
                              "nearest_any": {"name": "th_king_6ft", "worst_mm": 148},
                              "best_uniform": {"scale": 0.998, "name": "king",
                                               "worst_mm": 23}})
    row["mattress_fill"] = [1.0, 0.926]
    ok, why = R.verdict(row)
    assert not ok and any("best uniform scale 0.998 reaches king" in w for w in why)


# ---- the FRAME by geometry (review of D-120: the anchor is cloth on 4 of 11) --
def test_frame_extent_is_the_hard_stack_not_the_quilt():
    """Cloudrest (317c797d): pick_anchor is the QUILT (1882x1979), whose staged
    extent read INSIDE the ink while the real Base (1639x2217) is 70 mm past
    it. frame_extent takes the hard stack around the mattress instead."""
    base = _p("Base", (0.0, 0.0, 0.0), (2.217, 1.639, 0.190), 1.0, 0.190, 0.0)
    quilt = _p("Quilt", (0.06, -0.05, 0.007), (2.04, 1.93, 0.534), 1.0, 0.474, 0.054)
    qseams = _p("Quilt Seams", (0.10, 0.0, 0.007), (1.98, 1.79, 0.438), 0.0, None, None)
    sheet = _p("Sheet", (0.10, 0.03, 0.169), (2.11, 1.70, 0.417), 1.0, 0.417, 0.0)
    blanket = _p("Blanket", (0.0, 0.05, 0.001), (0.472, 1.92, 0.528), 1.0, 0.501, 0.019)
    ps = [base, quilt, qseams, sheet, blanket]
    a = R.pick_anchor(ps, drawn_plan_m2=3.6)
    assert a is quilt                                   # the anchor IS cloth here
    m, _ = R.pick_mattress(ps, a, drawn_plan_m2=3.6)
    assert m is sheet
    (lx, ly), (hx, hy), names = R.frame_extent(ps, m)
    assert "Base" in names and "Quilt" not in names and "Blanket" not in names
    # the hard length is the Base's own 2217 — 83 mm past the drawn 2134,
    # which the quilt-as-frame reading (1967 long) called INSIDE
    assert round((hx - lx) * 1000) == 2217
    ok, over_w, over_l = R.made_bed_within_ink((hy - ly), (hx - lx), 1.981, 2.134)
    assert not ok and over_l == 73
    # KNOWN OVER-READ, recorded rather than tuned away: the quilt's hollow SEAM
    # mesh sits low enough to count as hard, so the width reads 1790 instead of
    # the Base's 1639. It is reported with the part names in the row; it cannot
    # rescue a candidate (it only ever widens), and no cached file's verdict
    # turns on it.
    assert round((hy - ly) * 1000) == 1790 and "Quilt Seams" in names


def test_frame_extent_excludes_cloth_lying_on_the_mattress():
    """Metropol: the Sheet (2079 wide with its drape) and the Blanket lie ON
    the mattress, so the frame is the Bed Frame + Support + slab = 1842x2033,
    the number the ink cap must judge."""
    w = metropol_parts()
    ps = list(w.values())
    m, _ = R.pick_mattress(ps, w["frame"], drawn_plan_m2=3.6)
    (lx, ly), (hx, hy), names = R.frame_extent(ps, m)
    assert round((hy - ly) * 1000) == 1842 and round((hx - lx) * 1000) == 2033
    assert "Sheet" not in names and "Blanket" not in names and "Cusions" not in names


def test_overhang_staged_reads_from_where_the_frame_stands():
    """The built headboard band is emitted INSIDE the slot (60 of the 2000), so
    the head butts x=5.141 while the slot ends at 5.204: a foot measured from
    extents alone under-reads by 63 mm. Metropol's frame really stands 96 mm
    past the slot's foot line."""
    oh = R.overhang_staged_mm((3.108, 0.205), (5.141, 2.047),
                              3.204, 0.226, 5.204, 2.026)
    assert oh["foot"] == 96 and oh["head"] == 0
    assert oh["side_S"] == 21 and oh["side_N"] == 21
    inside = R.overhang_staged_mm((3.3, 0.3), (5.1, 1.9), 3.204, 0.226, 5.204, 2.026)
    assert inside == {"foot": 0, "head": 0, "side_S": 0, "side_N": 0}


def test_mattress_deck_and_tie_rules():
    """Two families the first cut got wrong, from the reviewers' constructions:
    a 100 mm slat deck inside the rails wins 'lowest top' over the mattress
    resting on it; and a hotel coverlet flat on the slab ties its top within
    a millimetre and out-plans it."""
    w = metropol_parts()
    deck = _p("slat_deck", (0.05, 0.05, 0.15), (2.00, 1.79, 0.273), 1.0, 0.273, 0.0)
    ps = list(w.values()) + [deck]
    m, note = R.pick_mattress(ps, w["frame"], drawn_plan_m2=3.6)
    assert m is w["matt"] and "deck" in note
    w2 = metropol_parts()
    coverlet = _p("coverlet", (0.0, -0.016, 0.109), (2.05, 1.85, 0.5126),
                  1.0, 0.5126, 0.019)
    ps2 = [w2["frame"], w2["support"], w2["matt"], coverlet]
    m2, _ = R.pick_mattress(ps2, w2["frame"], drawn_plan_m2=3.6)
    assert m2 is w2["matt"]           # the contained slab wins the tie, not the cloth


def test_neighbour_gaps_report_deep_overlaps_not_the_next_thing_out():
    """Obsidian staged: frame x 2.975..5.141, y 0.121..2.131 (2011 wide on the
    1800 slot). The north side table (spec y 2.005..2.405) sits 126 mm INTO
    the frame — the first cut's 100 mm window skipped it and named the
    wardrobe gable 687 mm away. The foot bench, which the frame overhangs by
    177 mm, is a W neighbour (a centre-of-plan test put it on N); the band's
    welt 1 mm past the head face is E, never S; a book on the bench rides
    with the bench's side; nothing 2 m+ away is reported."""
    frame_lo, frame_hi = (2.975, 0.121, 0.0), (5.141, 2.131, 0.25)
    others = [
        ("side_table_N", (4.803, 2.005, 0.0), (5.203, 2.405, 0.40)),
        ("side_table_S", (4.803, -0.210, 0.0), (5.203, 0.190, 0.40)),
        ("wardrobe_gable", (2.353, 2.818, 0.0), (5.654, 3.40, 2.8)),
        ("bench", (2.654, 0.626, 0.0), (3.152, 1.626, 0.41)),
        ("book_on_bench", (2.80, 1.00, 0.41), (3.10, 1.20, 0.45)),
        ("headboard_welt", (5.140, 0.20, 0.0), (5.20, 2.00, 1.10)),
        ("far_tv_console", (0.306, 0.128, 0.0), (0.906, 2.174, 0.6)),
    ]
    g = R.neighbour_gaps(frame_lo, frame_hi, others)
    assert g["N"] == {"gap_mm": -126, "object": "side_table_N"}
    assert g["S"] == {"gap_mm": -69, "object": "side_table_S"}
    assert g["W"] == {"gap_mm": -177, "object": "bench"}
    assert g["E"] == {"gap_mm": -1, "object": "headboard_welt"}
    g2 = R.neighbour_gaps(frame_lo, frame_hi, [others[2], others[6]])
    assert g2["N"] == {"gap_mm": 687, "object": "wardrobe_gable"} and g2["W"] is None


def test_neighbour_gaps_metropol_is_an_adjust_the_surroundings_number():
    """Metropol at scale 1.0: frame 1842 x 2033 centred on the 1800 slot with
    the head at the band -> the N table overlaps 42 mm, the S table clears
    by 15, the bench clears by 8. Those are P4's move-to-touch numbers."""
    frame_lo, frame_hi = (3.108, 0.205, 0.0), (5.141, 2.047, 0.25)
    others = [("side_table_N", (4.803, 2.005, 0.0), (5.203, 2.405, 0.40)),
              ("side_table_S", (4.803, -0.210, 0.0), (5.203, 0.190, 0.40)),
              ("bench", (2.602, 0.626, 0.0), (3.100, 1.626, 0.41))]
    g = R.neighbour_gaps(frame_lo, frame_hi, others)
    assert g["N"]["gap_mm"] == -42 and g["S"]["gap_mm"] == 15 and g["W"]["gap_mm"] == 8
