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
            "headboard_fused": False}


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
