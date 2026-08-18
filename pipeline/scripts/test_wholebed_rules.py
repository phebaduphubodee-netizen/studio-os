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
            "field_fill_len": 0.95, "field_fill_w": 0.93}


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
