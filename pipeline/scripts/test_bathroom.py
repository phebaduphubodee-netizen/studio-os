"""Unit tests for bathroom.py (pure ensuite fixture massing). Run: python -m pytest."""
import bathroom as B

KNOWN_MATS = {"porcelain", "stone", "oak", "brass", "glass", "tray", "mirror"}

# ink-true footprints from element4-ensuite_ink-read-2026-07-18.json
VANITY = {"kind": "vanity_double", "name": "vanity", "x": 1077, "y": 5923, "w": 2047, "d": 654, "h": 850,
          "design": {"counter_x0_mm": 77, "counter_len_mm": 3047, "basin_ctr_x_mm": [1576.9, 2627.5]}}
WC = {"kind": "toilet", "name": "wc", "x": 55, "y": 6031, "w": 685, "d": 609, "h": 800}
TUB = {"kind": "bathtub", "name": "tub", "x": 1125, "y": 7596, "w": 2000, "d": 978, "h": 560}
SHOWER = {"kind": "shower", "name": "shower", "x": 55, "y": 7320, "w": 1070, "d": 1276, "h": 2200}
PART = {"kind": "glass_partition", "name": "partition", "x": 1125, "y": 7329, "w": 10, "d": 1266, "h": 2000}


def _all_positive(parts):
    return all(p["dx"] > 0 and p["dy"] > 0 and p["dz"] > 0 for p in parts)


def _mats_known(parts):
    return {p["mat"] for p in parts} <= KNOWN_MATS


def _bbox(p):
    return (p["x"], p["y"], p["x"] + p["dx"], p["y"] + p["dy"])


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _bbox(a)
    bx0, by0, bx1, by1 = _bbox(b)
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def test_all_fixtures_produce_positive_boxes_with_known_mats():
    for fx in (VANITY, WC, TUB, SHOWER, PART):
        parts = B.fixture_parts(fx)
        assert parts, f"{fx['kind']} produced no parts"
        assert _all_positive(parts), f"{fx['kind']} has a zero/negative box"
        assert _mats_known(parts), f"{fx['kind']} has an unknown material role"


def test_unknown_kind_falls_back_to_empty():
    assert B.fixture_parts({"kind": "sofa", "x": 0, "y": 0, "w": 1, "d": 1, "h": 1}) == []


def test_vanity_has_oak_cabinet_stone_counter_two_porcelain_basins_two_brass_taps():
    parts = {p["name"]: p for p in B.vanity_parts(VANITY)}
    assert parts["vanity_cabinet"]["mat"] == "oak"
    assert parts["vanity_counter"]["mat"] == "stone"
    basins = [p for n, p in parts.items() if "basin" in n]
    taps = [p for n, p in parts.items() if "tap" in n]
    assert len(basins) == 2 and all(p["mat"] == "porcelain" for p in basins)
    assert len(taps) == 2 and all(p["mat"] == "brass" for p in taps)


def test_vanity_counter_spans_the_full_3047_run_but_cabinet_does_not():
    parts = {p["name"]: p for p in B.vanity_parts(VANITY)}
    counter, ledge, cab = parts["vanity_counter"], parts["vanity_ledge"], parts["vanity_cabinet"]
    # counter (deep, over cabinet) + west ledge together cover x77..3124 (=3047)
    west = min(counter["x"], ledge["x"])
    east = max(counter["x"] + counter["dx"], ledge["x"] + ledge["dx"])
    assert abs(west - 77) < 2 and abs((east - west) - 3047) < 40, (west, east)
    # the OAK cabinet must NOT extend west of x1077 (else it builds through the SW WC)
    assert cab["x"] >= 1077 - 1, f"oak cabinet west edge {cab['x']} intrudes on the WC zone"


def test_vanity_oak_stays_a_low_accent_not_a_full_height_mass():
    # D1-A anti-monopoly: the oak gesture is the LOW cabinet body, never a wall-height block
    cab = next(p for p in B.vanity_parts(VANITY) if p["name"] == "vanity_cabinet")
    assert cab["z"] + cab["dz"] <= 850, "oak cabinet taller than the 850 counter — not a low accent"


def test_vanity_builds_the_decided_mirror_above_the_counter():
    # D-E4-2: the full-width frameless mirror is a DECIDED element — it must be BUILT, not
    # left to a note (the revert-by-omission trap). Above the counter, routed to the mirror role.
    mir = next((p for p in B.vanity_parts(VANITY) if "mirror" in p["name"]), None)
    assert mir is not None, "vanity mirror (D-E4-2) is missing — a decided element omitted"
    assert mir["mat"] == "mirror"
    assert mir["z"] >= VANITY["h"], "mirror must sit ABOVE the counter, not on/behind it"


def test_wc_does_not_collide_with_the_vanity_cabinet():
    cab = next(p for p in B.vanity_parts(VANITY) if p["name"] == "vanity_cabinet")
    for wp in B.toilet_parts(WC):
        assert not _overlap(wp, cab), f"WC part {wp['name']} overlaps the oak vanity cabinet"


def test_wc_tank_sits_at_the_west_wall_and_bowl_projects_east():
    parts = {p["name"]: p for p in B.toilet_parts(WC)}
    assert parts["wc_tank"]["x"] <= parts["wc_bowl"]["x"], "tank must be west of the bowl"


def test_tub_is_an_open_recess_four_aprons_plus_floor_plus_stone_deck():
    parts = {p["name"]: p for p in B.bathtub_parts(TUB)}
    for edge in ("apron_s", "apron_n", "apron_w", "apron_e"):
        assert f"tub_{edge}" in parts and parts[f"tub_{edge}"]["mat"] == "porcelain"
    assert parts["tub_floor"]["dz"] < TUB["h"], "tub floor must be below the rim (a recess)"
    assert any(p["mat"] == "stone" for n, p in parts.items() if "deck" in n), "no stone deck cap"


def test_shower_has_glass_screen_tray_and_brass_head():
    parts = {p["name"]: p for p in B.shower_parts(SHOWER)}
    assert parts["shower_screen"]["mat"] == "glass"
    assert parts["shower_tray"]["mat"] == "tray"
    assert parts["shower_head"]["mat"] == "brass"


def test_glass_partition_is_one_thin_glass_panel():
    parts = B.glass_partition_parts(PART)
    assert len(parts) == 1 and parts[0]["mat"] == "glass"
    assert parts[0]["dx"] >= B.GLASS_T - 0.01, "partition thinner than a glass panel"


def test_all_fixture_parts_aggregates_every_fixture():
    total = B.all_fixture_parts([VANITY, WC, TUB, SHOWER, PART])
    assert len(total) == sum(len(B.fixture_parts(fx)) for fx in (VANITY, WC, TUB, SHOWER, PART))
