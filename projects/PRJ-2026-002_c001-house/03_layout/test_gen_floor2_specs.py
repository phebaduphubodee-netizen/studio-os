"""
test_gen_floor2_specs.py -- unit tests for the CLUSTER-DRIVEN generator's PURE logic
(no PDF / no fitz — the generator is import-safe; main() holds the plan-reading side).

Focus = the rot_from_facing wiring: resolve_face applies an OWNER-SIGNED facing OVER the
hand-typed default, using the SAME matcher the gate uses (placement_gate.confirmed_rot via resolve_rot),
so generator and gate never disagree on 'what did the owner sign'. The load-bearing
guarantees under test:
  * BACKWARD-COMPAT — no confirmed[] ledger => hand-typed facing, NO provenance key, so a
    regeneration is byte-identical to the pre-wiring generator.
  * OVERRIDE — a signed facing changes the built rot (durable truth beats the re-rolled guess).
  * FOOTPRINT STABILITY — the common 180-deg correction leaves the axis-aligned footprint
    unchanged, so the placement-gate IoU is not disturbed by signing.
  * SINGLE SOURCE — after the generator applies a sign, the gate SEES agreement and suppresses
    its facing flag; the two halves compose to converge toward PASS.

    python test_gen_floor2_specs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_floor2_specs as G      # import-safe: sets up pipeline/scripts on the path too
import placement_gate as PG       # the gate half (same confirmed_rot matcher; resolve_rot re-exported as G.resolve_rot)
import facing_reader as FR        # rot<->facing (the gate reads it lazily inside facing_flags)


def _armchair_cluster(cid=7, x=1000, y=1000, w=800, d=800):
    return [{"id": cid, "x": x, "y": y, "w": w, "d": d, "curve": True, "area_m2": w * d / 1e6}]


def _fp(it):
    return (it["x"], it["y"], it["w"], it["d"])


# ---- resolve_rot (shared, from placement_gate) works in ROT space, cardinal + non-cardinal ----
# (the exhaustive confirmed_rot/resolve_rot unit tests live in test_placement_gate.py; these pin the
#  generator's re-exported name + the rot-space contract the snap tests below rely on)
def test_resolve_rot_no_ledger_is_handrot():
    assert G.resolve_rot("sofa", 90, 2000, 900, []) == (90, None)
    assert G.resolve_rot("sofa", 90, 2000, 900, None) == (90, None)


def test_resolve_rot_signed_overrides_cardinal_and_numeric():
    assert G.resolve_rot("sofa", 90, 2000, 900, [{"name": "sofa", "facing": "W"}]) == (270, "owner-signed")
    assert G.resolve_rot("chair", 12, 680, 640, [{"name": "chair", "rot": 335}]) == (335, "owner-signed")


def test_resolve_rot_size_guard_rejects_reused_name():
    conf = [{"name": "sofa", "facing": "W", "w": 500, "d": 500}]   # wrong size for a 2000x900 sofa
    assert G.resolve_rot("sofa", 90, 2000, 900, conf) == (90, None)


def test_resolve_rot_noncardinal_typo_ignored():
    for bad in ("south", "N ", "n", 180, "", None):
        assert G.resolve_rot("sofa", 90, 2000, 900, [{"name": "sofa", "facing": bad}]) == (90, None), bad


# ---- snap: no confirmed[] -> hand-typed rot, NO facing_source key (byte-identical) ----
def test_snap_no_confirmed_is_backward_compatible():
    G._REPORT.clear()
    it = G.snap("sitting_room", "เก้าอี้ X", "armchair", _armchair_cluster(), set(), (1400, 1400), "S", 750)
    assert it.get("rot", 0) == 0                 # S -> rot 0 (build_floor omits rot 0)
    assert "facing_source" not in it, it
    assert it["cluster"] == 7 and it["snap_mm"] == 0


# ---- snap: the confirmed param DEFAULTS to None (old call sites unaffected) -----------
def test_snap_confirmed_defaults_to_none():
    G._REPORT.clear()
    a = G.snap("sitting_room", "โซฟา", "sofa", _armchair_cluster(), set(), (1400, 1400), "E", 800)
    G._REPORT.clear()
    b = G.snap("sitting_room", "โซฟา", "sofa", _armchair_cluster(), set(), (1400, 1400), "E", 800, confirmed=None)
    assert a == b, (a, b)


# ---- snap: an owner-signed 180-flip changes rot but LEAVES the footprint stable -------
def test_snap_signed_180flip_reorients_rot_but_not_footprint():
    G._REPORT.clear()
    plain = G.snap("sitting_room", "เก้าอี้ X", "armchair", _armchair_cluster(), set(), (1400, 1400), "S", 750)
    G._REPORT.clear()
    signed = G.snap("sitting_room", "เก้าอี้ X", "armchair", _armchair_cluster(), set(), (1400, 1400), "S", 750,
                    confirmed=[{"name": "เก้าอี้ X", "facing": "N"}])   # S->N is the 180 flip
    assert signed["rot"] == 180 and signed["facing_source"] == "owner-signed", signed
    assert _fp(plain) == _fp(signed), "a 180-deg facing correction must not move the axis-aligned footprint"


# ---- snap: an owner-signed 90-deg override RE-ORIENTS the footprint (w/d swap) --------
def test_snap_signed_90deg_swaps_footprint():
    # a non-square cluster so the swap is observable
    cl = [{"id": 3, "x": 1000, "y": 1000, "w": 1800, "d": 600, "curve": True, "area_m2": 1.08}]
    G._REPORT.clear()
    it = G.snap("sitting_room", "โซฟา", "sofa", cl, set(), (1900, 1300), "S", 800,
                confirmed=[{"name": "โซฟา", "facing": "E"}])          # S->E is 90 deg
    assert it["rot"] == 90, it
    # to_spec swaps w/d for rot 90/270: footprint width/depth exchange vs the drawn bbox
    assert it["w"] == 600 and it["d"] == 1800, it


# ---- snap: a piece with NO matching ledger name is unchanged (no false override) ------
def test_snap_unmatched_name_unchanged():
    G._REPORT.clear()
    it = G.snap("sitting_room", "โต๊ะกลม", "side_table", _armchair_cluster(), set(), (1400, 1400), "S", 450,
                confirmed=[{"name": "โซฟา", "facing": "N"}], shape="round")
    assert "facing_source" not in it and it.get("rot", 0) == 0, it


# ---- snap: no-cluster FALLBACK still honours a name-only signature --------------------
def test_snap_no_cluster_fallback_applies_signature():
    G._REPORT.clear()
    # anchor far from any cluster -> 500x500 fallback box; a name-only (size-agnostic) sign applies
    it = G.snap("master_bedroom", "เตียง", "bed", _armchair_cluster(x=9000, y=9000), set(),
                (100, 100), "W", 600, confirmed=[{"name": "เตียง", "facing": "S"}])
    assert it["w"] == 500 and it["d"] == 500          # fallback box (honest miss)
    assert it.get("rot", 0) == 0 and it["facing_source"] == "owner-signed", it   # S -> rot 0, signed


# ---- SINGLE SOURCE: after the generator applies a sign, the GATE suppresses its flag --
def test_generator_and_gate_agree_after_signing():
    # A bed drawn with a headboard strip on the WEST inner band reads facing EAST. Suppose the
    # owner SIGNS facing 'E'. The generator builds the piece with rot = FACE_ROT['E'] = 90.
    sign = [{"name": "เตียง", "facing": "E"}]
    cl = [{"id": 1, "x": 0, "y": 0, "w": 2000, "d": 2100, "curve": False, "area_m2": 4.2}]
    G._REPORT.clear()
    it = G.snap("master_bedroom", "เตียง", "bed", cl, set(), (1000, 1050), "S", 600, confirmed=sign)
    # generator applied the sign:
    assert FR.facing_from_rot(it.get("rot", 0)) == "E", it
    # gate, given the SAME sign, sees the built rot AGREE and suppresses the facing flag
    # (empty fsegs: with agreement the gate never even reads the strip):
    assert PG.facing_flags([it], [], confirmed=sign) == [], "gate must suppress a correctly-applied sign"
    # and a CONTRADICTING build (rot flipped to face W) is raised, not suppressed:
    it_bad = dict(it, rot=270)
    flags = PG.facing_flags([it_bad], [], confirmed=sign)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} gen_floor2_specs tests passed")
