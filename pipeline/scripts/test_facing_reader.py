"""
test_facing_reader.py -- unit tests for the PURE facing cross-check (no PDF).

Covers the rot->facing cardinal map (incl. a non-cardinal -> None), opposite(),
the headboard/backrest inner-band read for all four back edges, and -- the
critical false-positive guard -- that a BARE outline reads "unknown", never a
false "disagree". check_piece is exercised for agree / disagree / unknown.

    python test_facing_reader.py
"""
import facing_reader as F


def _rect(x0, y0, x1, y1):
    """The 4 outermost outline segments of a bbox (must NOT score any band)."""
    return [[[x0, y0], [x1, y0]],      # S edge
            [[x0, y1], [x1, y1]],      # N edge
            [[x0, y0], [x0, y1]],      # W edge
            [[x1, y0], [x1, y1]]]      # E edge


def _vstrip(x, y0, y1):
    """A vertical stroke at constant x (a backrest along an E/W edge)."""
    return [[x, y0], [x, y1]]


def _hstrip(y, x0, x1):
    """A horizontal stroke at constant y (a backrest along an N/S edge)."""
    return [[x0, y], [x1, y]]


# ---- facing_from_rot / opposite ------------------------------------------------------
def test_facing_from_rot_cardinals():
    assert F.facing_from_rot(0) == "S"
    assert F.facing_from_rot(90) == "E"
    assert F.facing_from_rot(180) == "N"
    assert F.facing_from_rot(270) == "W"
    assert F.facing_from_rot(360) == "S"      # wraps
    assert F.facing_from_rot(-90) == "W"      # -90 % 360 == 270


def test_facing_from_rot_noncardinal_is_none():
    assert F.facing_from_rot(45) is None
    assert F.facing_from_rot(1) is None
    assert F.facing_from_rot(None) is None


def test_opposite():
    assert F.opposite("N") == "S"
    assert F.opposite("S") == "N"
    assert F.opposite("E") == "W"
    assert F.opposite("W") == "E"
    assert F.opposite(None) is None


# ---- bed: headboard on the EAST inner band -> faces WEST ------------------------------
def test_bed_headboard_east_reads_west_and_agrees():
    bbox = (0, 0, 2000, 2100)                 # W=2000, H=2100
    segs = _rect(*bbox) + [_vstrip(1850, 40, 2060)]   # strip ~150mm inside E edge
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] == "E", r
    assert r["facing"] == "W", r
    assert r["confidence"] > 0.5, r
    chk = F.check_piece(segs, bbox, rot=270)   # 270 faces WEST
    assert chk["claimed"] == "W" and chk["read"] == "W", chk
    assert chk["verdict"] == "agree", chk


# ---- sofa: backrest on the WEST inner band -> faces EAST ------------------------------
def test_sofa_backrest_west_reads_east_and_agrees():
    bbox = (0, 0, 2200, 900)                  # W=2200, H=900
    segs = _rect(*bbox) + [_vstrip(170, 60, 840)]     # strip ~170mm inside W edge
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] == "W", r
    assert r["facing"] == "E", r
    chk = F.check_piece(segs, bbox, rot=90)    # 90 faces EAST
    assert chk["verdict"] == "agree", chk


# ---- bed: headboard on the NORTH inner band -> faces SOUTH ----------------------------
def test_bed_headboard_north_reads_south():
    bbox = (0, 0, 1800, 2000)                 # H=2000; N band ~[1100,1900]
    segs = _rect(*bbox) + [_hstrip(1820, 40, 1760)]   # strip ~180mm below N edge
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] == "N", r
    assert r["facing"] == "S", r
    assert F.check_piece(segs, bbox, rot=0)["verdict"] == "agree"   # 0 faces SOUTH


# ---- CRITICAL: a bare outline has no strip -> unknown, never a false call -------------
def test_bare_rectangle_is_unknown_not_disagree():
    bbox = (0, 0, 2000, 2100)
    segs = _rect(*bbox)                        # outline only, no inner strip
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] is None, r
    assert r["facing"] is None, r
    for rot in (0, 90, 180, 270):
        chk = F.check_piece(segs, bbox, rot=rot)
        assert chk["verdict"] == "unknown", (rot, chk)


# ---- 180-deg flip is AMBIGUOUS (footboard vs inverted headboard): soft flag, NOT a false disagree ----
def test_front_edge_strip_180flip_is_ambiguous():
    # strip on the S edge while rot 0 claims facing S: the read back_edge (S) IS the claimed FRONT.
    # Geometry cannot tell a footboard on a correctly-faced bed from an inverted headboard, so the
    # verdict is 'ambiguous' -- not a false 'disagree', but NOT silent (the caller surfaces it as a
    # soft 'eyeball the orientation' REVIEW prompt; 180 is the commonest facing error).
    bbox = (0, 0, 2000, 2100)                 # S band ~[105,945]
    segs = _rect(*bbox) + [_hstrip(260, 90, 1910)]    # strip ~260mm above S edge
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] == "S" and r["facing"] == "N", r
    chk = F.check_piece(segs, bbox, rot=0)     # claims SOUTH; read back-edge == claimed front
    assert chk["verdict"] == "ambiguous", chk  # soft: prompt an eyeball, do NOT assert 'disagree'


# ---- PERPENDICULAR (90-deg) inconsistency IS a real disagree -------------------------
def test_perpendicular_strip_disagrees():
    # strip on the WEST edge while rot 0 claims facing S: read faces E, 90 deg off the claim,
    # and the read back-edge (W) is NOT the claimed front (S) -> genuine disagreement.
    bbox = (0, 0, 2000, 2100)                 # W band ~[100,900]
    segs = _rect(*bbox) + [_vstrip(150, 90, 2010)]
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] == "W" and r["facing"] == "E", r
    chk = F.check_piece(segs, bbox, rot=0)
    assert chk["claimed"] == "S" and chk["read"] == "E", chk
    assert chk["verdict"] == "disagree", chk


# ---- non-cardinal rot -> unknown regardless of geometry ------------------------------
def test_noncardinal_rot_is_unknown():
    bbox = (0, 0, 2000, 2100)
    segs = _rect(*bbox) + [_vstrip(1850, 40, 2060)]   # a real, readable E strip
    chk = F.check_piece(segs, bbox, rot=45)
    assert chk["claimed"] is None, chk
    assert chk["verdict"] == "unknown", chk


# ---- a symmetric piece (strips on BOTH opposite edges) washes out -> unknown ----------
def test_symmetric_strips_wash_out_to_unknown():
    bbox = (0, 0, 2000, 2100)
    segs = _rect(*bbox) + [_vstrip(1850, 40, 2060), _vstrip(150, 40, 2060)]
    r = F.read_facing(segs, bbox)
    assert r["back_edge"] is None, r           # E and W tie -> neither dominates
    assert F.check_piece(segs, bbox, rot=270)["verdict"] == "unknown"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} facing_reader tests passed")
