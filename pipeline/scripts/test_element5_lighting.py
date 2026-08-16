"""test_element5_lighting.py — the element-5 lighting derivation invariants.

Pure python, no bpy. Run:  python -m pytest pipeline/scripts/test_element5_lighting.py -q

PINNING RULE (the curtain-build lesson, derive-not-entrench): expectations are
RE-DERIVED from the canonical FILE or from a modified copy of it — geometry moves
with the spec, [est] tunables (watts, cone) are validated structurally, never
frozen. The canonical-FILE test is the 831fc1b pattern: the real spec of record
must produce the DD's plan, so an uncommitted spec edit that breaks a decision
fails HERE, not silently in a render.
"""
import copy
import json
import math
import os

import pytest

import bathroom
import element5_lighting as E5
import suite_clearance

SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                         "projects", "PRJ-2026-002_c001-house", "03_layout",
                         "master-suite.CANONICAL.spec.json")


@pytest.fixture(scope="module")
def spec():
    with open(SPEC_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture()
def sp(spec):
    return copy.deepcopy(spec)


# ---------------------------------------------------------------- canonical FILE

def test_canonical_file_carries_the_block(spec):
    assert E5.applies(spec), "the canonical spec must carry lighting schema e5-layers@0.1"


def test_amendment_cove_and_sconces_derive_from_signed_geometry(spec):
    """E5 AMENDMENT (2026-07-30, gate #8): fixtures DERIVE — a moved wall or bed
    re-derives them, and a sconce off the BF14 run must RAISE, never clamp."""
    blk = E5.validate_block(spec)
    cove, sconces = E5.cove_and_sconces(spec, blk)
    bf = next(b for b in spec["builtins"] if b.get("bf") == blk["accent"]["target_bf"])
    ceil = float(spec["room"].get("ceiling_mm", 2800))
    assert cove["face_x"] == float(bf["x"]) and cove["len"] == float(bf["d"])
    assert cove["z"] == ceil - E5.COVE_DROP_MM
    assert cove["watts"] > 0
    bed = next(i for i in spec["items"] if i.get("kind") == "bed")
    cy = float(bed["y"]) + float(bed["d"]) / 2.0
    assert len(sconces) == 2
    ys = sorted(s["y"] for s in sconces)
    assert math.isclose(ys[0], cy - E5.SCONCE_SPREAD_MM)
    assert math.isclose(ys[1], cy + E5.SCONCE_SPREAD_MM)
    for s in sconces:
        assert float(bf["y"]) < s["y"] < float(bf["y"]) + float(bf["d"])
        assert s["z"] == E5.SCONCE_Z_MM


def test_amendment_reaches_the_schedule(spec):
    """Documentation law: the frame and the fixture schedule must tell one room."""
    fixtures, _ = E5.schedule_fixtures(spec)
    layers = [f.get("layer") for f in fixtures]
    assert layers.count("cove") == 1
    assert layers.count("sconce") == 2


def test_canonical_plan_counts(spec):
    p = E5.plan(spec)
    # cove+sconces joined 2026-07-30 (e5 amendment, gate #8 — see the amendment doc
    # in 04_visualization; the ask stood at three gates with four judges unanimous)
    assert p["meta"]["counts"] == {"cove": 1, "sconces": 2,
                                   "downlights": 18, "strips": 2, "bar": 1,
                                   "spots": 6, "lamps": 2}


def test_bedroom_grid_clips_bf09_3(spec):
    """The verify-lens catch (D-E5-1): row y~3394.6 lands 2 cans inside the
    floor-to-ceiling BF09-3 carcass — they must be DROPPED and DISCLOSED."""
    p = E5.plan(spec)
    bed = next(m for m in p["meta"]["zones"] if m["zone"] == "bedroom")
    assert bed["n_grid"] == 12 and bed["n"] == 10
    assert len(bed["dropped_in_masses"]) == 2
    assert all(d["mass"] == "BF09-3" for d in bed["dropped_in_masses"])
    assert 107.6 <= bed["achieved_lux"] <= 215.3      # wired bedroom band (10-20 fc)
    # positions re-derive, not hand-typed: all live points outside every mass
    masses = E5.full_height_rects(spec, "bedroom")
    for f in p["downlights"]:
        if f["zone"] == "bedroom":
            assert not any(r[0] < f["x"] < r[2] and r[1] < f["y"] < r[3] for r in masses)


def test_ensuite_six_at_283(spec):
    p = E5.plan(spec)
    en = next(m for m in p["meta"]["zones"] if "ensuite" in m["zone"])
    assert en["n"] == 6 and not en["dropped_in_masses"]
    assert abs(en["achieved_lux"] - 283.0) < 0.5      # inside wired 215.3-322.9 + LAW >=100
    xs = sorted({f["x"] for f in p["downlights"] if "ensuite" in f["zone"]})
    ys = sorted({f["y"] for f in p["downlights"] if "ensuite" in f["zone"]})
    assert xs == [525.0, 1575.0, 2625.0] and ys == [6550.0, 7950.0]


def test_bay_row_clips_bf09_1(spec):
    """D-E5-3 critique catch: the third bay can sits inside BF09-1's north leg."""
    p = E5.plan(spec)
    bay = next(m for m in p["meta"]["zones"] if "ตู้เสื้อผ้า" in m["zone"])
    assert bay["n_grid"] == 3 and bay["n"] == 2
    assert bay["dropped_in_masses"] and bay["rcp_placeholder"] is True
    assert bay["achieved_lux"] >= 107.6               # default band floor


def test_strips_sit_in_the_pier_margins(spec):
    """D-E5-4: strip centres derive from mirror edges + casement jambs (~51/50mm)."""
    p = E5.plan(spec)
    s = {x["name"]: x for x in p["strips"]}
    m = next(b for b in spec["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    win1_hi = 3498.3
    win2_lo = 4999.6
    s_c = (win1_hi + m["y_mm"]) / 2.0
    n_c = (m["y_mm"] + m["d_mm"] + win2_lo) / 2.0
    assert abs(s["bf11_strip_s"]["box"][1] + 15 - s_c) < 0.1     # box y + w/2 = centre
    assert abs(s["bf11_strip_n"]["box"][1] + 15 - n_c) < 0.1
    for x in s.values():
        assert x["box"][2] == m["sill_mm"] and x["box"][5] == m["h_mm"]   # the mirror field
        assert x["light"]["aim"][1] == m["y_mm"] + m["d_mm"] / 2.0        # seated axis y4249


def test_bar_derives_from_bathroom_constants(spec):
    """D-E5-5 ONE-SOURCE (scrutiny-hardened): the wash light AND the solid bar both
    re-derive from bathroom.BAR_*/MIRROR_* — asserted against those constants, never
    against frozen copies of their values (derive-not-entrench)."""
    p = E5.plan(spec)
    bar = p["bar"]
    z_under = bathroom.MIRROR_SILL + bathroom.MIRROR_H + bathroom.BAR_REVEAL
    assert abs(bar["z"] - (z_under + bathroom.BAR_H / 2.0)) < 1e-9
    assert abs(bar["size"][1] - bathroom.BAR_H) < 1e-9
    fx = next(f for f in spec["subrooms"][0]["fixtures"] if f["kind"].startswith("vanity"))
    assert abs(bar["x"] - (fx["x"] + fx["w"] / 2.0)) < 0.1
    parts = bathroom.vanity_parts(fx, taskbar=True)
    names = {q["name"] for q in parts}
    assert "vanity_taskbar_body" in names and "vanity_taskbar_opal" in names
    body = next(q for q in parts if q["name"] == "vanity_taskbar_body")
    opal = next(q for q in parts if q["name"] == "vanity_taskbar_opal")
    assert body["mat"] == "blackalu" and opal["mat"] == "opal"
    assert body["z"] == opal["z"] == z_under                      # above the mirror + reveal
    assert body["dx"] == opal["dx"] == fx["w"]                    # mirror-width, not counter
    assert opal["y"] > body["y"]                                  # opal = the room-side face
    # the e5 opt-in gate: a NON-e5 bathroom spec must NOT grow an emissive bar
    assert not any(q["name"].startswith("vanity_taskbar")
                   for q in bathroom.vanity_parts(fx, taskbar=False))
    # and a spec still carrying the retired profile keys RAISES as unknown (stale shape)
def test_stale_bar_profile_keys_raise(sp):
    sp["lighting"]["task"]["ensuite_mirror_bar"]["reveal_mm"] = 10
    with pytest.raises(ValueError, match="unknown key"):
        E5.plan(sp)


def test_strip_light_derives_with_mirror_x(sp):
    """Scrutiny catch: the paired light must ride the SAME referent as the box — a
    mirror moved to a non-x0 wall moves box AND light AND aim together."""
    m = next(b for b in sp["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    m["x_mm"] = 500
    p = E5.plan(sp)
    for s in p["strips"]:
        assert abs(s["light"]["x"] - (s["box"][0] + s["box"][3] + 20.0)) < 1e-9
        assert abs(s["light"]["aim"][0] - (500 + 1000.0)) < 1e-9


def test_bedroom_clip_sees_protruding_subroom_fixture(sp):
    """Scrutiny catch: a full-height SUBROOM fixture protruding into the bedroom band
    must clip bedroom cans too. (Rationale updated for the e7 truing, review catch
    E7R-5: BF09-2 was y5180..6680 pre-e7; the trued rect is y5199.5..6697.6 — it still
    crosses the y5850 bedroom/subroom line, so its south end still protrudes into the
    bedroom band, and the name-based assertion below is unchanged and still passes.
    Only this docstring's stale extents were wrong.)"""
    masses = E5.full_height_rects(sp, "bedroom")
    assert any(n == "BF09-2" for (_, _, _, _, n) in masses)
    # force a live hit: park a probe over grid can (941.7, 1757.6) — a spot no builtin
    # claims (BF09-3 would win the row-order tie at the y3394.6 cans)
    sp["subrooms"][1]["fixtures"].append(
        {"name": "probe", "kind": "wardrobe", "x": 800, "y": 1600, "w": 300, "d": 300, "h": 2800})
    p = E5.plan(sp)
    bed = next(z for z in p["meta"]["zones"] if z["zone"] == "bedroom")
    assert any(d["mass"] == "probe" for d in bed["dropped_in_masses"])


def test_coplanar_backer_skins_canonical(spec):
    """The canonical file now yields ZERO skins, and that is the correct answer.

    THIS TEST WAS A SNAPSHOT AND WENT RED WHEN THE DRAWING WON. It asserted one
    skin — BF10 backing the ensuite south edge over x650..3150 — and 0b98b98
    (2026-08-11, D-038) ink-trued BF10 off those numbers: x 650 -> 804, y 5250 ->
    5200, w 2500 -> 2498. Its face therefore sits at y=5800, fifty millimetres
    clear of the y=5850 edge, so the Cycles coplanar tie this skin exists to
    break CANNOT OCCUR and emitting a skin would be painting a fix over nothing.
    R12: the sheet outranks the derivation, so the conflict reopens the
    derivation — which is this expectation, not the ink.

    It stayed red for five days, which is its own finding: nothing runs the
    suite on a spec edit.

    The MECHANISM is pinned by the positive control below rather than by this
    file's current geometry — a snapshot cannot tell "the defect is gone" from
    "the detector is broken", and that is the whole distinction here.
    """
    assert E5.coplanar_backer_skins(spec) == []
    bf10 = next(b for b in spec["builtins"] if b.get("bf") == "BF10")
    assert abs(float(bf10["y"]) + float(bf10["d"]) - 5800.0) < 0.1


def test_coplanar_backer_skins_fire_when_a_face_lands_on_the_edge(sp):
    """POSITIVE CONTROL — put BF10's face back on the ensuite edge and the skin
    returns. Without this, the zero above is indistinguishable from a detector
    that has stopped detecting."""
    bf10 = next(b for b in sp["builtins"] if b.get("bf") == "BF10")
    bf10["y"] = float(bf10["y"]) + 50.0                          # face 5800 -> 5850
    skins = E5.coplanar_backer_skins(sp)
    # TWO, not one — and the second is a fact about the trued plan rather than a
    # quirk of this test. BF10 is x804..3302 since D-038, while the ensuite ends
    # at x3150: it overhangs the ensuite/wardrobe-bay party line by 152 mm, so it
    # backs an edge of BOTH subrooms. The pre-truing cabinet ran 650..3150, flush
    # with that line, which is why the old expectation of one skin held.
    assert len(skins) == 2
    ens = next(s for s in skins if s["dx"] > 1000)
    assert ens["backer"] == "BF10" and ens["edge"] == "y=5850"
    assert abs(ens["x"] - float(bf10["x"])) < 0.1
    assert abs(ens["dx"] - (3150.0 - float(bf10["x"]))) < 0.1
    assert ens["dz"] == sp["room"]["ceiling_mm"]                 # to the ROOM ceiling
    assert ens["y"] > 5850                                       # 2mm INSIDE the ensuite
    bay = next(s for s in skins if s is not ens)
    assert abs(bay["x"] - 3150.0) < 0.1
    assert abs(bay["dx"] - (float(bf10["x"]) + float(bf10["w"]) - 3150.0)) < 0.1


def test_coplanar_backer_skins_vanish_when_not_backed(sp):
    """The negative half of the same control, from the fired state."""
    bf10 = next(b for b in sp["builtins"] if b.get("bf") == "BF10")
    bf10["y"] = float(bf10["y"]) + 50.0                          # fires (see above)
    assert len(E5.coplanar_backer_skins(sp)) == 2                # both subrooms
    bf10["d"] = float(bf10["d"]) - 3                             # face now 3mm off
    assert E5.coplanar_backer_skins(sp) == []


def test_schedule_fixtures_match_render_plan(spec):
    """Scrutiny catch (the client-lane contradiction): suite_lighting.plan_lighting on
    an e5 spec must document THE SAME plan the render builds — one source."""
    import suite_lighting
    fixtures, meta = suite_lighting.plan_lighting(spec)
    assert meta["source"] == "e5-layers@0.1"
    p = E5.plan(spec)
    from collections import Counter
    layers = Counter(f["layer"] for f in fixtures)
    assert layers["ambient"] == len(p["downlights"]) == 18
    assert layers["task"] == len(p["strips"]) + 1 == 3            # 2 strips + the bar
    assert layers["accent"] == len(p["spots"]) == 6
    assert layers["decorative"] == len(p["lamps"]) == 2
    amb = {(f["x"], f["y"]) for f in fixtures if f["layer"] == "ambient"}
    assert amb == {(f["x"], f["y"]) for f in p["downlights"]}     # positions identical


def test_novel_geometry_guards_raise(sp):
    """Scrutiny finding: the three novel geometry RAISEs had no coverage."""
    # (a) strip margin collapse: widen the mirror into the pier margins
    m = next(b for b in sp["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    m["y_mm"], m["d_mm"] = 3500, 1499                             # margins ~2mm < strip_w
    with pytest.raises(ValueError, match="margin"):
        E5.plan(sp)


def test_accent_pool_off_run_raises(sp):
    bed = next(i for i in sp["items"] if i["kind"] == "bed")
    bed["y"] = 3500                                               # axis pushes pools past BF14's run
    with pytest.raises(ValueError, match="falls off"):
        E5.plan(sp)


def test_dry_strip_collapse_raises(sp):
    shower = next(f for f in sp["subrooms"][0]["fixtures"] if f["kind"] == "shower")
    shower["y"] = 6700                                            # curb crowds the vanity front
    with pytest.raises(ValueError, match="dry"):
        E5.plan(sp)


def test_mirror_missing_key_raises(sp):
    m = next(b for b in sp["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    del m["sill_mm"]
    with pytest.raises(ValueError, match="sill_mm"):
        E5.plan(sp)


def test_accent_pools_on_bf14_centred_on_bed(spec):
    p = E5.plan(spec)
    bf14 = next(b for b in spec["builtins"] if b.get("bf") == "BF14")
    bed = next(i for i in spec["items"] if i["kind"] == "bed")
    pools = [s for s in p["spots"] if s["name"].startswith("bf14_wash")]
    assert len(pools) == 4
    setback = spec["room"]["ceiling_mm"] / 3.0
    for s in pools:
        assert abs(s["x"] - (bf14["x"] - setback)) < 0.1          # H/3 wash setback
        assert s["aim"][0] == bf14["x"]                           # aimed at the slat face
        assert bf14["y"] < s["y"] < bf14["y"] + bf14["d"]         # on the run
        drop = s["z"] - s["aim"][2]
        tilt = math.degrees(math.atan(setback / drop))
        assert tilt < 40.0                                        # inside the gimbal [est]
    mean_y = sum(s["y"] for s in pools) / 4
    assert abs(mean_y - (bed["y"] + bed["d"] / 2.0)) < 0.1        # centred on the bed axis


def test_tub_wash_stands_in_the_drawn_dry_strip(spec):
    """D-E5-8 after the retraction: the row derives from vanity front .. shower curb,
    never from a statutory zone number."""
    p = E5.plan(spec)
    tubs = [s for s in p["spots"] if s["name"].startswith("tub_wash")]
    assert len(tubs) == 2
    fxs = spec["subrooms"][0]["fixtures"]
    van = next(f for f in fxs if f["kind"].startswith("vanity"))
    shower = next(f for f in fxs if f["kind"] == "shower")
    tub = next(f for f in fxs if f["kind"] == "bathtub")
    y_lo = van["y"] + van["d"]
    y_hi = min(tub["y"], shower["y"],
               next(f for f in fxs if f["kind"] == "glass_partition")["y"])
    for s in tubs:
        assert abs(s["y"] - (y_lo + y_hi) / 2.0) < 0.1
        assert s["aim"][1] == tub["y"] + tub["d"] / 2.0           # deck/water centreline
        assert s["aim"][2] == tub["h"]
    assert abs(tubs[0]["x"] + tubs[1]["x"] - 2 * (tub["x"] + tub["w"] / 2.0)) < 0.1


def test_lamp_glow_z_derives_from_the_built_shade(spec):
    """D-E5-6: emitter z derives from millwork's own part stack (the retracted 870
    [est] cannot recur). RE-DERIVED here from the parts, not frozen (derive-not-
    entrench): z_off = shade oz + dz/2 - h for the probe h."""
    g = E5.lamp_glow(spec)
    import millwork
    shade = next(p for p in millwork.nightstand_lamp_parts(0.5, 0.5, 0.52, lamp=True)
                 if p[0] == "lamp_shade")
    want = shade[3] + shade[6] / 2.0 - 0.52
    assert g and abs(g["z_off_m"] - want) < 1e-9
    p = E5.plan(spec)
    assert [l["rgb"] for l in p["lamps"]] == [(1.0, 0.88, 0.75)] * 2   # 2850K between anchors


def test_cct_family_audit(spec):
    p = E5.plan(spec)
    for c in p["meta"]["nominal_cct"]["electric"]:
        assert 2200 <= c <= 3000                                   # one warm family (PH-03)


# ---------------------------------------------------------------- fail-loud RAISES

def test_unknown_key_raises(sp):
    sp["lighting"]["accent"]["watss"] = 12
    with pytest.raises(ValueError, match="unknown key"):
        E5.plan(sp)


def test_renamed_bf_raises_not_reverts(sp):
    """The swallow the whole channel exists to kill: a BF rename must RAISE."""
    sp["lighting"]["accent"]["target_bf"] = "BF14X"
    with pytest.raises(ValueError, match="bf='BF14X'"):
        E5.plan(sp)


def test_missing_mirror_block_raises(sp):
    del next(b for b in sp["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    with pytest.raises(ValueError, match="design.mirror"):
        E5.plan(sp)


def test_missing_casement_raises(sp):
    sp["room"]["openings"] = [o for o in sp["room"]["openings"]
                              if o["id"] != "glz-west-win1"]
    with pytest.raises(ValueError, match="glz-west-win1"):
        E5.plan(sp)


def test_two_bathtubs_raise(sp):
    fxs = sp["subrooms"][0]["fixtures"]
    fxs.append(dict(next(f for f in fxs if f["kind"] == "bathtub")))
    with pytest.raises(ValueError, match="bathtub"):
        E5.plan(sp)


def test_lamp_glow_off_raises(sp):
    """Turning the decided glow off is an owner decision made in the open, not a flag flip."""
    sp["lighting"]["practicals"]["lamp_glow"] = False
    with pytest.raises(ValueError, match="lamp_glow"):
        E5.plan(sp)


def test_out_of_family_cct_raises(sp):
    next(i for i in sp["items"] if i["kind"] == "side_table")["lamp"]["cct_k"] = 4000
    with pytest.raises(ValueError, match="family"):
        E5.plan(sp)


def test_subroom_tiling_break_raises(sp):
    sp["subrooms"][0]["outline_mm"] = [[0, 6000], [3150, 6000], [3150, 8650], [0, 8650]]
    with pytest.raises(ValueError, match="band"):
        E5.plan(sp)


def test_missing_section_raises(sp):
    del sp["lighting"]["practicals"]
    with pytest.raises(ValueError, match="practicals"):
        E5.plan(sp)


def test_no_block_means_not_applies(sp):
    del sp["lighting"]
    assert not E5.applies(sp)
    assert E5.lamp_glow(sp) is None


# ---------------------------------------------------------------- derive-not-entrench

def test_ensuite_boundary_shift_rederives_fixtures(sp):
    """Positions are DERIVED, not frozen: moving the ensuite/bay party line
    x3150 -> 3250 (the band still tiles) re-derives the ensuite grid inside the
    NEW outline (a baked array — the rejected fixtures-override channel — would
    keep the old coordinates)."""
    base = {(f["x"], f["y"]) for f in E5.plan(sp)["downlights"] if "ensuite" in f["zone"]}
    sp["subrooms"][0]["outline_mm"] = [[0, 5850], [3250, 5850], [3250, 8650], [0, 8650]]
    sp["subrooms"][1]["outline_mm"] = [[3250, 5850], [5650, 5850], [5650, 8650], [3250, 8650]]
    p = E5.plan(sp)
    moved = {(f["x"], f["y"]) for f in p["downlights"] if "ensuite" in f["zone"]}
    assert moved != base
    for (x, y) in moved:
        assert 0 < x < 3250 and 5850 < y < 8650


def test_tub_move_moves_the_wash_aim(sp):
    tub = next(f for f in sp["subrooms"][0]["fixtures"] if f["kind"] == "bathtub")
    tub["y"] += 50
    p = E5.plan(sp)
    for s in p["spots"]:
        if s["name"].startswith("tub_wash"):
            assert s["aim"][1] == tub["y"] + tub["d"] / 2.0


def test_mirror_nudge_moves_strips(sp):
    m = next(b for b in sp["builtins"] if b.get("kind") == "vanity")["design"]["mirror"]
    m["sill_mm"] = 900
    p = E5.plan(sp)
    for s in p["strips"]:
        assert s["box"][2] == 900 and abs(s["light"]["z"] - (900 + m["h_mm"] / 2)) < 0.1
