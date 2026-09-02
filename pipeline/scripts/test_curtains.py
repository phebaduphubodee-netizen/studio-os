"""
test_curtains.py — the curtain layout invariants: pocket containment, the locked east
slot, corner mitres (no bare-glass band), real waves, fail-loud data validation.

Pure python, no bpy (curtains.py is bpy-free by design, same as millwork.py). Run:
    python -m pytest pipeline/scripts/test_curtains.py -q

The fixture is the REAL canonical master-suite geometry (mm): the glass-L (5 panes,
3 coplanar runs), the owner-traced track, the owner-decided 3-panel/2-layer make-up
with the ink-measured 250 pocket, and the builtins that interact with the pockets.

PINNING RULE (review 2026-07-17): geometry expectations are DERIVED from the
fixture's own data, never hardcoded from the current spec residuals — the known
#9c BF14 offset (spec slot 197 vs ink 250.8) must be TOLERATED by the code and the
suite must stay green the day the residual is fixed, not entrench it.
"""
import copy
import json
import os

import pytest

import curtains as C

SPEC = {
    "room": {
        "type": "master_suite",
        "outline_mm": [[0, -697.8], [5500, -697.8], [5500, 2650],
                       [5650, 2650], [5650, 8650], [0, 8650]],
        "ceiling_mm": 2800, "wall_thk_mm": 100,
        "openings": [
            {"id": "glz-south-w", "type": "glass", "rect": [0, -697.8, 3849, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-slider", "type": "glass", "rect": [3849, -697.8, 5249, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-south-e", "type": "glass", "rect": [5249, -697.8, 5500, -697.8],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-east", "type": "glass", "rect": [5500, -697.8, 5500, -148.6],
             "sill_mm": 0, "head_mm": 2800},
            {"id": "glz-west", "type": "glass", "rect": [0, -697.8, 0, 451],
             "sill_mm": 0, "head_mm": 2800},
        ],
    },
    "curtain_track": {"path_mm": [[0, 2650], [0, -450], [5500, -450], [5500, 110]]},
    # builtins that interact with the pockets: BF14 stands in the east band (its x
    # carries the KNOWN #9c residual), the ex-TV bookshelf stands 306 off the west wall
    "builtins": [
        {"name": "ผนังระแนงหัวเตียง BF14", "x": 5203, "y": -450, "w": 100, "d": 3250,
         "h": 2800},
        {"name": "ชั้นหนังสือ/โชว์ ผนังตะวันตก (ex-TV)", "x": 306, "y": 130, "w": 600,
         "d": 2046, "h": 1800},
    ],
    "curtains": {
        "count": 3,
        "pocket_mm": 250,
        "layers": [
            {"role": "blackout", "type": "opaque", "fold": "s_fold",
             "stack_depth_mm": 130, "position": "room side (front)"},
            {"role": "privacy", "type": "sheer", "fold": "3_pleat",
             "stack_depth_mm": 85, "position": "glass side (back)"},
        ],
    },
}

PLANES = {"west": ("x", 0.0, 1), "south": ("y", -697.8, 1), "east": ("x", 5500.0, -1)}
GLASS = {"west": (-697.8, 451.0), "south": (0.0, 5500.0), "east": (-697.8, -148.6)}

# ---- derived expectations (from the fixture's own numbers, not the code's output) ----
BF14 = SPEC["builtins"][0]
NEED = (C.GAP_GLASS_MM + C.GAP_ROOM_MM + C.LAYER_GAP_MM
        + sum(l["stack_depth_mm"] for l in SPEC["curtains"]["layers"]))       # 250
USABLE_E = min(250.0, PLANES["east"][1] - (BF14["x"] + BF14["w"]))            # 197
USABLE_S = min(250.0, BF14["y"] - PLANES["south"][1])                         # 247.8
SCALE_E = (USABLE_E - 35.0) / 215.0
# sheer (glass side): centre = 20 + amp; envelope outer edge = centre + amp
SHEER_OUT_W = C.GAP_GLASS_MM + 85.0                                           # 105
SHEER_OUT_E = C.GAP_GLASS_MM + 85.0 * SCALE_E                                 # 84.05
# mitre-extended/trimmed drawn extents (default state: sheers drawn)
DRAWN = {
    "west": (-697.8 + C.GAP_GLASS_MM, 451.0),                    # extended to own glass
    "east": (-697.8 + C.GAP_GLASS_MM, -148.6),                   # extended to own glass
    "south": (SHEER_OUT_W + C.LAYER_GAP_MM,                      # trimmed to meet west
              5500.0 - (SHEER_OUT_E + C.LAYER_GAP_MM)),          # ...and east sheers
}


def _ribbons(spec=None):
    return C.curtain_ribbons(spec if spec is not None else copy.deepcopy(SPEC))


def _dist_mm(rb):
    """Every point's distance (mm) from its leg's glass plane, into the room."""
    coord, plane, sign = PLANES[rb["leg"]]
    return [sign * ((x_m if coord == "x" else y_m) / C.MM - plane)
            for x_m, y_m in rb["pts"]]


def _run_mm(rb):
    """Every point's along-run coordinate (mm)."""
    coord, _, _ = PLANES[rb["leg"]]
    return [(y_m if coord == "x" else x_m) / C.MM for x_m, y_m in rb["pts"]]


def _get(rbs, leg, role):
    return next(r for r in rbs if r["leg"] == leg and r["role"] == role)


def test_three_legs_two_layers():
    rbs = _ribbons()
    assert len(rbs) == 6
    assert {r["leg"] for r in rbs} == {"west", "south", "east"}
    for leg in ("west", "south", "east"):
        assert {r["role"] for r in rbs if r["leg"] == leg} == {"blackout", "privacy"}


def test_every_point_inside_the_free_pocket():
    # fabric never through the glass, never proud of the leg's FREE pocket depth
    for rb in _ribbons():
        d = _dist_mm(rb)
        assert min(d) >= C.GAP_GLASS_MM - 0.1, (rb["name"], min(d))
        assert max(d) <= rb["pocket_used_mm"] - C.GAP_ROOM_MM + 0.1, (rb["name"], max(d))
        assert rb["pocket_used_mm"] <= 250.0


def test_layer_order_blackout_room_side():
    rbs = _ribbons()
    for leg in ("west", "south", "east"):
        assert min(_dist_mm(_get(rbs, leg, "blackout"))) \
            > max(_dist_mm(_get(rbs, leg, "privacy"))), leg


def test_east_slot_lock_derived_from_geometry():
    # fabric must clear the BF14 face the SCENE actually builds — squeezed and
    # disclosed while the #9c residual stands (usable 197), automatically full-depth
    # the day BF14 is ink-trued (this test derives, it does not entrench)
    face = BF14["x"] + BF14["w"]
    for rb in _ribbons():
        if rb["leg"] != "east":
            continue
        assert rb["pocket_used_mm"] == pytest.approx(USABLE_E), rb["name"]
        if USABLE_E < NEED:
            assert rb["squeezed_by"] and "BF14" in rb["squeezed_by"], rb["name"]
        else:
            assert rb["squeezed_by"] is None, rb["name"]
        for x_m, _ in rb["pts"]:
            assert face * C.MM + 1e-4 < x_m < 5500.0 * C.MM - 1e-4, rb["name"]


def test_west_full_south_marginal():
    # west: bookshelf 306 off the wall = outside the band; south: BF14's south end is
    # 247.8 from the glass — a real-but-negligible squeeze, derived not hardcoded
    for rb in _ribbons():
        if rb["leg"] == "west":
            assert rb["squeezed_by"] is None and rb["pocket_used_mm"] == 250.0
        elif rb["leg"] == "south":
            assert rb["pocket_used_mm"] == pytest.approx(USABLE_S), rb["name"]


def test_mitre_no_bare_glass_at_corners():
    # THE 3ce5f5e invariant: no floor-to-ceiling bare band beside a corner. Each
    # return sheer extends over its OWN full glass to GAP_GLASS short of the
    # neighbour's plane; the south sheer meets both return sheers (+LAYER_GAP)
    rbs = _ribbons()
    for leg, (lo, hi) in DRAWN.items():
        run = _run_mm(_get(rbs, leg, "privacy"))
        assert min(run) == pytest.approx(lo, abs=0.2), leg
        assert max(run) == pytest.approx(hi, abs=0.2), leg


def test_ribbons_never_cross():
    # perpendicular panels MEET at the mitres, never pass through each other: plan
    # bounding boxes of ribbons on different legs are disjoint
    rbs = _ribbons()
    def bbox(rb):
        xs = [p[0] for p in rb["pts"]]; ys = [p[1] for p in rb["pts"]]
        return min(xs), min(ys), max(xs), max(ys)
    for i, a in enumerate(rbs):
        for b in rbs[i + 1:]:
            if a["leg"] == b["leg"]:
                continue
            ax0, ay0, ax1, ay1 = bbox(a); bx0, by0, bx1, by1 = bbox(b)
            disjoint = ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0
            assert disjoint, (a["name"], b["name"])


def test_wave_is_real_and_fold_structured():
    # review 2026-07-17: flat centreline curtains passed every test. Pin the wave:
    # amplitude actually exercised both ways, and the fold count is in the geometry
    # (≈2 centreline crossings per fold), not just metadata
    for rb in _ribbons():
        d = _dist_mm(rb)
        c0, amp = rb["centre_off_mm"], rb["amp_mm"]
        assert max(d) >= c0 + 0.9 * amp, rb["name"]
        assert min(d) <= c0 - 0.9 * amp, rb["name"]
        signs = [1 if v > c0 else -1 for v in d if abs(v - c0) > amp * 0.05]
        crossings = sum(1 for s1, s2 in zip(signs, signs[1:]) if s1 != s2)
        assert crossings >= 2 * rb["n_folds"] - 2, (rb["name"], crossings)


def test_blackout_parks_off_glass_where_track_allows():
    rbs = _ribbons()
    west, east, south = (_get(rbs, l, "blackout") for l in ("west", "east", "south"))
    assert west["state"] == east["state"] == south["state"] == "parked"
    # west parks NORTH of the glass on the owner-traced track, STACKED AGAINST the
    # glass edge y451 (adjacency pinned — far-end parking is a different design)
    assert not west["over_glass_park"]
    wr = _run_mm(west)
    assert min(wr) == pytest.approx(451.0, abs=0.5) and max(wr) <= 2650.0 + 0.5
    # east parks in the slot behind BF14, stacked against the glass end y-148.6
    assert not east["over_glass_park"]
    er = _run_mm(east)
    assert min(er) == pytest.approx(-148.6, abs=0.5) and max(er) <= 110.0 + 0.5
    # south has no off-glass track: parks OVER glass at the lo end of its TRIMMED run
    assert south["over_glass_park"]
    sr = _run_mm(south)
    assert min(sr) == pytest.approx(DRAWN["south"][0], abs=0.5)
    assert max(sr) <= DRAWN["south"][0] \
        + C.STACK_FRACTION["s_fold"] * (DRAWN["south"][1] - DRAWN["south"][0]) + 1.0


def test_park_end_hi_moves_the_stack():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"park_end_over_glass": {"south": "hi"}}
    south = _get(_ribbons(spec), "south", "blackout")
    assert south["over_glass_park"]
    assert max(_run_mm(south)) == pytest.approx(DRAWN["south"][1], abs=0.5)


def test_park_end_unknown_leg_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"park_end_over_glass": {"sooth": "hi"}}
    with pytest.raises(ValueError, match="unknown leg"):
        _ribbons(spec)
    spec["curtains"]["render_state"] = {"park_end_over_glass": {"south": "east-end"}}
    with pytest.raises(ValueError, match="'lo'\\|'hi'"):
        _ribbons(spec)


def test_no_curtains_block_is_a_no_op():
    spec = copy.deepcopy(SPEC)
    del spec["curtains"]
    assert _ribbons(spec) == []
    assert _ribbons({}) == []


def test_count_mismatch_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["count"] = 2
    with pytest.raises(ValueError, match="disagrees with itself"):
        _ribbons(spec)


def test_diagonal_track_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtain_track"]["path_mm"] = [[0, 2650], [500, -450]]
    with pytest.raises(ValueError, match="not axis-aligned"):
        _ribbons(spec)


def test_track_leg_with_no_glass_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtain_track"]["path_mm"].append([4000, 110])
    with pytest.raises(ValueError, match="no glass"):
        _ribbons(spec)


def test_layer_type_typo_fails_loud():
    # review 2026-07-17 HIGH: a typo'd type used to silently park the sheer (bare
    # glass) or render it opaque
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["layers"][1]["type"] = "voile"
    with pytest.raises(ValueError, match="opaque.*sheer|sheer.*opaque"):
        _ribbons(spec)


def test_duplicate_layer_roles_fail_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["layers"][1]["role"] = "blackout"
    with pytest.raises(ValueError, match="duplicate role"):
        _ribbons(spec)


def test_ambiguous_position_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["layers"][0]["position"] = "in front of the glass"
    with pytest.raises(ValueError, match="exactly one"):
        _ribbons(spec)


def test_render_state_override_draws_the_blackout():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"blackout": "drawn"}
    rbs = _ribbons(spec)
    # return extents are layer-independent (extension end): unchanged; the south trim
    # legitimately widens to the blackout envelopes — derive it
    for leg in ("west", "east"):
        bl = _get(rbs, leg, "blackout")
        assert bl["state"] == "drawn"
        run = _run_mm(bl)
        assert min(run) == pytest.approx(DRAWN[leg][0], abs=0.2)
        assert max(run) == pytest.approx(DRAWN[leg][1], abs=0.2)
    bl_out_w = C.GAP_GLASS_MM + 85.0 + C.LAYER_GAP_MM + 130.0        # west blackout outer
    bl_out_e = C.GAP_GLASS_MM + (85.0 + 130.0) * SCALE_E + C.LAYER_GAP_MM
    s = _run_mm(_get(rbs, "south", "blackout"))
    assert min(s) == pytest.approx(bl_out_w + C.LAYER_GAP_MM, abs=0.2)
    assert max(s) == pytest.approx(5500.0 - (bl_out_e + C.LAYER_GAP_MM), abs=0.2)


def test_render_state_typo_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"blckout": "drawn"}
    with pytest.raises(ValueError, match="unknown layer role"):
        _ribbons(spec)
    spec["curtains"]["render_state"] = {"blackout": "open"}
    with pytest.raises(ValueError, match="drawn.*parked|parked.*drawn"):
        _ribbons(spec)


def test_pocket_too_small_fails_loud():
    # the vault rule (opaque+sheer needs >=250) reproduced from geometry: a 240 pocket
    # (still wide enough to MATCH the track legs) must refuse the make-up
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["pocket_mm"] = 240
    with pytest.raises(ValueError, match="does not fit"):
        _ribbons(spec)


def test_obstacle_straddling_the_glass_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["builtins"].append({"name": "ghost pier", "x": -50, "y": -100, "w": 200,
                             "d": 300, "h": 2800})
    with pytest.raises(ValueError, match="straddles"):
        _ribbons(spec)


def test_pocket_fully_blocked_fails_loud():
    spec = copy.deepcopy(SPEC)
    spec["builtins"].append({"name": "blocker", "x": 1000, "y": -667.8, "w": 800,
                             "d": 300, "h": 2800})
    with pytest.raises(ValueError, match="compression floor|blocked"):
        _ribbons(spec)


def test_fold_count_survives_parking():
    # parking compresses the wavelength, never the fold count. Compared on the RETURN
    # legs only: their extents are state-independent (the south trim legitimately
    # shifts with the drawn set, changing its span and so its fold count)
    default = _ribbons()
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"blackout": "drawn", "privacy": "drawn"}
    alldrawn = _ribbons(spec)
    for leg in ("west", "east"):
        for role in ("blackout", "privacy"):
            assert _get(default, leg, role)["n_folds"] \
                == _get(alldrawn, leg, role)["n_folds"], (leg, role)


def test_parked_sheer_stacks_too():
    spec = copy.deepcopy(SPEC)
    spec["curtains"]["render_state"] = {"privacy": "parked"}
    west = _get(_ribbons(spec), "west", "privacy")
    assert west["state"] == "parked" and not west["over_glass_park"]
    run = _run_mm(west)
    assert min(run) == pytest.approx(451.0, abs=0.5)
    span = DRAWN["west"][1] - DRAWN["west"][0]
    assert max(run) <= 451.0 + C.STACK_FRACTION["3_pleat"] * span + 1.0


def test_north_leg_naming():
    # a mini room with glass + track on the NORTH wall exercises the 4th leg name
    spec = {
        "room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]],
                 "ceiling_mm": 2600,
                 "openings": [{"id": "g", "type": "glass",
                               "rect": [0, 3000, 3000, 3000]}]},
        "curtain_track": {"path_mm": [[0, 2750], [3000, 2750]]},
        "curtains": {"count": 1, "pocket_mm": 250,
                     "layers": [{"role": "blackout", "type": "opaque",
                                 "fold": "s_fold", "stack_depth_mm": 130,
                                 "position": "room side (front)"}]},
    }
    rbs = C.curtain_ribbons(spec)
    assert {r["leg"] for r in rbs} == {"north"}
    for _, y_m in rbs[0]["pts"]:
        assert y_m < 3.0    # inward = -y: fabric inside the room


def test_vertical_span_is_floor_to_hidden_ceiling():
    for rb in _ribbons():
        assert rb["z0"] == pytest.approx(C.HEM_CLEAR_M)
        assert rb["z1"] == pytest.approx(2.8 + C.TOP_EMBED_M)
        assert rb["z1"] > 2.8


def test_canonical_spec_integration():
    """The real canonical file: 3 legs / 2 layers, only the south park over glass,
    containment + the east-face clearance derived from ITS OWN builtin geometry."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(
        here, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout",
        "master-suite.CANONICAL.spec.json"))
    if not os.path.exists(path):
        pytest.skip("canonical spec not present")
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    rbs = C.curtain_ribbons(spec)
    assert len(rbs) == 6
    assert {r["leg"] for r in rbs} == {"west", "south", "east"}
    assert [r["name"] for r in rbs if r["over_glass_park"]] \
        == ["curtain__south_blackout"]
    bf14 = next(b for b in spec["builtins"] if "BF14" in str(b.get("name")))
    face_m = (float(bf14["x"]) + float(bf14["w"])) * C.MM
    for rb in rbs:
        d = _dist_mm(rb)
        assert min(d) >= C.GAP_GLASS_MM - 0.1
        assert max(d) <= rb["pocket_used_mm"] - C.GAP_ROOM_MM + 0.1
        if rb["leg"] == "east":
            assert all(x > face_m for x, _ in rb["pts"]), rb["name"]
    # the mitre invariant on the real file: both return sheers cover their glass to
    # GAP_GLASS short of the south plane — the 3ce5f5e pale band stays dead
    for leg in ("west", "east"):
        run = _run_mm(_get(rbs, leg, "privacy"))
        assert min(run) <= -697.8 + C.GAP_GLASS_MM + 0.2, leg


# ---- the hanging lattice (LOOK round-2 #4) -------------------------------------------
# ribbon_mesh turns each plan ribbon into a (stations x rings) lattice under the e8
# softgoods law. These pin the law itself, on the real fixture geometry.

def _lattice(rb, nv=C.RIBBON_RINGS):
    verts, faces = C.ribbon_mesh(rb, nv=nv)
    n = len(rb["pts"])
    assert len(verts) == n * (nv + 1)
    assert len(faces) == (n - 1) * nv
    assert all(len(f) == 4 for f in faces)          # quads only (SketchUp law)
    cols = [verts[i * (nv + 1):(i + 1) * (nv + 1)] for i in range(n)]
    return cols


def _off_mm(rb, v):
    coord, plane, sign = PLANES[rb["leg"]]
    c = v[0] if coord == "x" else v[1]
    return sign * (c / C.MM - plane)


def test_lattice_top_ring_is_the_track_wave():
    # ring 0 = the owner-signed plan layout byte-for-byte, at the suspension height
    for rb in _ribbons():
        cols = _lattice(rb)
        for (px, py), col in zip(rb["pts"], cols):
            assert col[0][2] == pytest.approx(rb["z1"])
            assert (col[0][0], col[0][1]) == pytest.approx((px, py))


def test_lattice_stays_inside_the_layer_envelope():
    # the law may redistribute the wave, never enlarge it: every vert of every ring
    # within [centre-amp, centre+amp] -- the band the pocket stack was validated on
    for rb in _ribbons():
        lo = rb["centre_off_mm"] - rb["amp_mm"] - 1e-6
        hi = rb["centre_off_mm"] + rb["amp_mm"] + 1e-6
        for col in _lattice(rb):
            for v in col:
                assert lo <= _off_mm(rb, v) <= hi, rb["name"]


def test_lattice_hem_never_level_but_never_low():
    for rb in _ribbons():
        cols = _lattice(rb)
        hem = [col[-1][2] for col in cols]
        assert min(hem) >= rb["z0"] - 1e-9, rb["name"]          # floor clearance holds
        assert max(hem) <= rb["z0"] + C.HEM_WANDER_M + 1e-9
        assert max(hem) - min(hem) > 0.006, rb["name"]          # a LEVEL hem is the defect


def test_lattice_ends_stay_put_for_the_mitre_corners():
    # at both run ends every ring sits exactly on the track wave and the hem lands at
    # z0 -- a wandering end would open the L-corner where two legs meet
    for rb in _ribbons():
        cols = _lattice(rb)
        for col, k in ((cols[0], 0), (cols[-1], -1)):
            px, py = rb["pts"][k]
            for v in col:
                assert (v[0], v[1]) == pytest.approx((px, py)), rb["name"]
            assert col[-1][2] == pytest.approx(rb["z0"])


def test_lattice_breaks_the_metronome():
    # the hem ring must NOT be a scalar multiple of the top ring (that is the fluted
    # corrugation): station-wise gain top->hem must actually spread
    rb = _get(_ribbons(), "south", "privacy")           # the widest drawn sheer
    cols = _lattice(rb)
    gains = []
    for col in cols:
        top = _off_mm(rb, col[0]) - rb["centre_off_mm"]
        hem = _off_mm(rb, col[-1]) - rb["centre_off_mm"]
        if abs(top) > 0.4 * rb["amp_mm"]:
            gains.append(hem / top)
    assert max(gains) - min(gains) > 0.25, "hem is still a uniform copy of the track wave"


def test_lattice_deterministic():
    rb = _get(_ribbons(), "east", "privacy")
    assert C.ribbon_mesh(rb) == C.ribbon_mesh(rb)


# ------------------------------------------------------- the hem (P2r-39, 2026-09-02) --
# WHY THESE EXIST: HEM_CLEAR_M sat at 0.015 with no source and HEM_WANDER_M at 0.032 on
# top of it, so the hem floated 15-47 mm and 63.7% of the sheer's columns showed floor
# underneath in the render. Nothing in this file looked at a hem, so nothing failed.
def test_hem_grazes_the_floor_within_the_cited_band():
    """The cited grammar is 'hem 3-6 mm clear' (inbox-tier drapery-designer study,
    2026-08-28). The BASE clearance must sit in that band — not above it."""
    assert 0.003 <= C.HEM_CLEAR_M <= 0.006, C.HEM_CLEAR_M


def test_the_hems_highest_point_still_grazes():
    """The wander is deliberate (it is what stopped the hem reading as matched spikes),
    so this pins the SUM rather than banning it: even at full wander the hem must stay
    in a grazing read, not float."""
    top = C.HEM_CLEAR_M + C.HEM_WANDER_M
    assert top <= 0.015, f"hem tops out {top * 1000:.0f} mm off the floor"


def test_the_wander_mechanism_is_not_deleted():
    """Positive control for the test above: a future round must not satisfy the grazing
    bound by zeroing the irregularity, which would buy back the metronomic hem a LOOK
    round already paid to remove."""
    assert C.HEM_WANDER_M > 0.0
    assert C._HEM_WAVES and C._HEM_PLEAT_FRAC > 0.0


def test_built_ribbons_actually_hang_at_that_height(spec_fixture=None):
    """End-to-end: the constants above are only worth pinning if the geometry uses them."""
    import io as _io, json as _json, os as _os
    p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))), "projects", "PRJ-2026-002_c001-house", "03_layout",
        "master-suite.CANONICAL.spec.json")
    with _io.open(p, encoding="utf-8") as fh:
        spec = _json.load(fh)
    rbs = C.curtain_ribbons(spec)
    assert rbs
    for rb in rbs:
        assert rb["z0"] == C.HEM_CLEAR_M, rb["name"]
