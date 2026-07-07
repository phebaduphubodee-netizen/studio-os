"""
test_zone_flag.py — the deterministic indoor / outdoor_same_floor / below_grade flagger.

Pure geometry (point-in-poly, rect/polygon area fractions, facade corroboration, the element
classifier) needs no PDF. The last test is the PRODUCTION REPLAY: it runs the real
plan_cluster.extract_clusters on the real floor-2 PDF and asserts the machine flags the exact
below-grade garden tree the owner had to hand-drop (the F3 wound), with zero false positives on
the indoor pieces — it skips cleanly if PyMuPDF / the PDF are unavailable.

    python test_zone_flag.py     (or: pytest test_zone_flag.py)
"""
import glob
import json
import os

import zone_flag as Z

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))       # pipeline/scripts -> pipeline -> repo root


def _proj(rel):
    return os.path.join(_REPO, rel)

# ---- real floor-2 sitting-room fixtures (verified coordinates) ------------------------
SITTING_OUTLINE = [[5750, 0], [10650, 0], [10650, 6250], [5750, 6250]]
# the room's SOUTH glass facade (strong, full-width, just south of y=0) + the OUTER garden edge
FACADE_GLAZ = {"axis": "h", "c": 98.9, "span": [5752.3, 10649.8], "score": 4, "tier": "strong"}
OUTER_GLAZ = {"axis": "h", "c": -1151.6, "span": [3003.7, 10751.4], "score": 5, "tier": "strong"}
GLAZ = [FACADE_GLAZ, OUTER_GLAZ]
NO_SOUTH_WALL = []            # the real south edge is OPEN (glass, below the thick-wall gate)


def _rect_el(x, y, w, d, curve=False, unplaced=False, ref="e"):
    return {"ref": ref, "fp": (x, y, x + w, y + d), "w": w, "d": d,
            "area_m2": round(w * d / 1e6, 3), "curve": curve, "unplaced": unplaced}


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---- point-in-polygon + distance -----------------------------------------------------
def test_point_in_poly_inside_outside():
    assert Z.point_in_poly((8000, 3000), SITTING_OUTLINE)
    assert not Z.point_in_poly((8000, -500), SITTING_OUTLINE)   # south of the room
    assert not Z.point_in_poly((5000, 3000), SITTING_OUTLINE)   # west of the room


def test_dist_point_to_poly_boundary():
    # a point 100mm south of the south edge is 100mm from the polygon
    assert approx(Z.dist_point_to_poly((8000, -100), SITTING_OUTLINE), 100.0, 1e-3)
    assert approx(Z.dist_point_to_poly((8000, 0), SITTING_OUTLINE), 0.0, 1e-3)


# ---- area fractions ------------------------------------------------------------------
def test_rect_area_frac_inside_full_and_none():
    assert approx(Z.rect_area_frac_inside((6000, 1000, 6600, 1600), SITTING_OUTLINE), 1.0, 1e-6)
    assert approx(Z.rect_area_frac_inside((6000, -900, 6600, -300), SITTING_OUTLINE), 0.0, 1e-6)


def test_rect_area_frac_inside_half():
    # a rect straddling the south edge y=0: exactly half its area is inside
    assert approx(Z.rect_area_frac_inside((6000, -300, 6600, 300), SITTING_OUTLINE), 0.5, 1e-6)


def test_rect_frac_south_of():
    assert approx(Z.rect_frac_south_of((6000, -800, 6600, -200), 0), 1.0)   # fully south
    assert approx(Z.rect_frac_south_of((6000, 200, 6600, 800), 0), 0.0)     # fully north
    assert approx(Z.rect_frac_south_of((6000, -300, 6600, 300), 0), 0.5)    # half


# ---- facade inference ----------------------------------------------------------------
def test_facade_datum_south_edge():
    assert Z.facade_datum(SITTING_OUTLINE) == (0, 5750, 10650)


def test_facade_corroborated_true_on_open_glazed_south():
    ok, ev = Z.facade_corroborated(0, 5750, 10650, GLAZ, NO_SOUTH_WALL)
    assert ok and ev["glazing_c"] == 98.9          # nearest-to-datum strong line, not the -1151 outer


def test_facade_not_corroborated_without_glazing():
    ok, ev = Z.facade_corroborated(0, 5750, 10650, [], NO_SOUTH_WALL)
    assert not ok and ev["reason"] == "no_strong_south_glazing"


def test_facade_not_corroborated_when_south_is_walled():
    # a real 5000mm thick wall along y=0 closes the edge -> not a glazed facade
    wall = [[[5750, 0], [10650, 0]]]
    ok, ev = Z.facade_corroborated(0, 5750, 10650, GLAZ, wall)
    assert not ok and ev["reason"] == "south_edge_walled"


def test_weak_glazing_does_not_corroborate():
    weak = [{"axis": "h", "c": -300, "span": [5752, 10649], "score": 2, "tier": "weak"}]
    ok, _ = Z.facade_corroborated(0, 5750, 10650, weak, NO_SOUTH_WALL)
    assert not ok


# ---- classify_element (the incident) -------------------------------------------------
def _facade():
    y_s, xlo, xhi = Z.facade_datum(SITTING_OUTLINE)
    ok, ev = Z.facade_corroborated(y_s, xlo, xhi, GLAZ, NO_SOUTH_WALL)
    return {"y_s": y_s, "xlo": xlo, "xhi": xhi, "corroborated": ok, **ev}


def test_classify_tree_below_grade_strong():
    tree = _rect_el(6344, -830, 924, 846, curve=True, unplaced=True, ref="tree")
    r = Z.classify_element(tree, SITTING_OUTLINE, _facade(), GLAZ)
    assert r["zone"] == Z.BELOW and (r["indoor"], r["floor"]) == (False, False)
    assert r["confidence"] == "STRONG"             # curve + a glazing line between it and the datum


def test_classify_indoor_chair_near_facade():
    # the left tub chair at y=629 (centroid ~949) is INSIDE despite sitting near the glass
    chair = _rect_el(5991, 629, 680, 640, curve=True, ref="chairL")
    r = Z.classify_element(chair, SITTING_OUTLINE, _facade(), GLAZ)
    assert r["zone"] == Z.INDOOR and r["emit"] is False


def test_classify_organic_rug_inside_is_indoor_not_below():
    # curve=True must NOT flag an object the owner drew INSIDE the room (curve is a strengthener,
    # never a gate) — this is the "organic ink inside" false-positive guard
    rug = _rect_el(7000, 2500, 1500, 1000, curve=True, ref="rug")
    r = Z.classify_element(rug, SITTING_OUTLINE, _facade(), GLAZ)
    assert r["zone"] == Z.INDOOR


def test_classify_dim_tick_south_gets_no_proposal():
    tick = _rect_el(6000, -500, 200, 60, curve=False, ref="tick")   # below the size floor
    assert Z.classify_element(tick, SITTING_OUTLINE, _facade(), GLAZ) is None


def test_classify_abstains_when_not_corroborated():
    tree = _rect_el(6344, -830, 924, 846, curve=True, ref="tree")
    facade = {"y_s": 0, "xlo": 5750, "xhi": 10650, "corroborated": False, "glazing_c": None}
    assert Z.classify_element(tree, SITTING_OUTLINE, facade, []) is None


def test_classify_straddler_centroid_inside_is_indoor():
    # a piece straddling y=0 whose CENTROID lands north (inside) stays indoor (no confident below)
    strad = _rect_el(6000, -100, 600, 600, ref="strad")            # centroid y=200 inside
    r = Z.classify_element(strad, SITTING_OUTLINE, _facade(), GLAZ)
    assert r["zone"] == Z.INDOOR


def test_south_exterior_collapses_to_indoor_or_below_v1():
    # v1 SCOPE (honest): for a south-glazed facade, indoor-immunity (<=indoor_pad 150mm of the
    # boundary) and the below-margin (>y_below_margin 150mm south of the datum) MEET, so a south-
    # exterior element is either INDOOR (near the glass, immune) or BELOW_GRADE (well south). The
    # machine does NOT propose outdoor_same_floor in v1 — a same-level terrace needs a parapet loop
    # to tell from ground-below, which is the exact F3 ambiguity the owner sign arbitrates. OUTDOOR
    # stays a valid owner-SIGNABLE class (see placement_gate confirmed_zone tests).
    near = _rect_el(6000, -120, 600, 300, ref="near")      # centroid ~ -30, inside indoor_pad
    assert Z.classify_element(near, SITTING_OUTLINE, _facade(), GLAZ)["zone"] == Z.INDOOR
    far = _rect_el(6000, -1000, 900, 700, ref="far")       # centroid ~ -650, well below the datum
    assert Z.classify_element(far, SITTING_OUTLINE, _facade(), GLAZ)["zone"] == Z.BELOW


def test_east_exterior_not_flagged_without_east_facade():
    # an object EAST of the room is NOT proposed outdoor: v1 only reasons about the corroborated
    # SOUTH facade, so a lateral-exterior element gets no proposal (no false lateral flag).
    east = _rect_el(11000, 3000, 800, 800, ref="east")
    assert Z.classify_element(east, SITTING_OUTLINE, _facade(), GLAZ) is None


# ---- zone_proposals (the whole incident room) ----------------------------------------
def test_zone_proposals_incident_one_below_zero_false_positive():
    tree = _rect_el(6344, -830, 924, 846, curve=True, unplaced=True, ref="tree")
    indoor_pieces = [
        _rect_el(5991, 629, 680, 640, curve=True, ref="chairL"),
        _rect_el(7300, 1085, 660, 640, curve=True, ref="chairR"),
        _rect_el(7061, 4147, 2202, 1008, ref="sofa"),
        _rect_el(6614, 1114, 600, 600, curve=True, ref="tableA"),
        _rect_el(9164, 4360, 600, 600, curve=True, ref="tableB"),
        _rect_el(5898, 2172, 1002, 402, ref="console"),
    ]
    res = Z.zone_proposals([tree] + indoor_pieces, SITTING_OUTLINE, GLAZ, NO_SOUTH_WALL)
    assert res["corroborated"]
    assert len(res["proposals"]) == 1                      # ONLY the tree
    assert res["proposals"][0]["ref"] == "tree" and res["proposals"][0]["zone"] == Z.BELOW
    assert all(p["zone"] == Z.INDOOR for p in res["indoor"])
    assert len(res["indoor"]) == 6                          # every drawn indoor piece stays indoor


# ---- adversarial-verification regressions --------------------------------------------
def test_walled_south_room_abstains_with_segmented_walls():
    # the real wall extract decomposes one wall into ~200mm segments; a per-segment length gate would
    # let a WALLED-south room falsely corroborate. Union-coverage fixes it: 200mm stubs spanning the
    # edge close it (abstain); an OPEN edge (no walls) corroborates.
    wall200 = [[[x, 0], [x + 200, 0]] for x in range(5750, 10650, 200)]
    ok, ev = Z.facade_corroborated(0, 5750, 10650, GLAZ, wall200)
    assert not ok and ev["reason"] == "south_edge_walled" and ev["wall_cover"] >= 0.6
    assert Z.facade_corroborated(0, 5750, 10650, GLAZ, [])[0]      # open edge still corroborates


def test_below_canopy_lapping_glass_surfaces_not_dropped():
    # a deep below-grade canopy whose top edge laps north over the glass (centroid ~300mm south,
    # frac_south ~0.65 < out_area_frac) must SURFACE via the below-centroid clause, not be silently
    # dropped — the dead zone that would re-open the F3 wound.
    canopy = _rect_el(6344, -1300, 1400, 2000, curve=True, unplaced=True, ref="canopy")  # cy=-300
    r = Z.classify_element(canopy, SITTING_OUTLINE, _facade(), GLAZ)
    assert r is not None and r["zone"] == Z.BELOW           # surfaces (was None before the fix)


def test_placed_proud_piece_is_low_not_strong():
    # a PLACED piece proud of the glass (a real bay-window seat is geometrically identical to a
    # below-grade object) must be LOW confidence, never STRONG — curve alone can't earn STRONG.
    bay = _rect_el(7000, -800, 1000, 700, curve=True, unplaced=False, ref="bay")
    r = Z.classify_element(bay, SITTING_OUTLINE, _facade(), GLAZ)
    assert r["zone"] == Z.BELOW and r["confidence"] == "LOW"
    # while the identical-geometry UNPLACED cluster (garden ink) earns STRONG
    treeish = _rect_el(7000, -800, 1000, 700, curve=True, unplaced=True, ref="tree2")
    assert Z.classify_element(treeish, SITTING_OUTLINE, _facade(), GLAZ)["confidence"] == "STRONG"


def test_malformed_glazing_and_wall_skipped_not_crash():
    bad_glaz = [{"axis": "h", "c": 50, "span": [5752, None], "score": 4},   # span None
                {"axis": "h", "c": 50, "span": [5752], "score": 4},         # span len 1
                {"axis": "h", "c": 50, "span": [5752, 10649], "score": None}]  # score None
    for g in bad_glaz:
        ok, _ = Z.facade_corroborated(0, 5750, 10650, [g], [])
        assert ok is False                                  # skipped, no crash
    Z.facade_corroborated(0, 5750, 10650, GLAZ, [[[5750, None], [10650, 0]]])   # wall None coord: no crash


def test_empty_outline_area_frac_is_zero():
    assert Z.rect_area_frac_inside((0, 0, 10, 10), []) == 0.0           # empty encloses nothing
    assert Z.rect_area_frac_inside((0, 0, 10, 10), [[0, 0], [10, 0]]) == 0.0   # degenerate (2 pts)


# ---- PRODUCTION REPLAY (real PDF; skips if unavailable) ------------------------------
def _real_pdf():
    hits = glob.glob(_proj("projects/PRJ-2026-002_c001-house/00_intake/raw-local/*.pdf"))
    hits = [h for h in hits if "funiture" in os.path.basename(h)]
    return hits[0] if hits else None


def test_production_replay_flags_the_real_tree():
    try:
        import fitz  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("PyMuPDF not installed")
    pdf = _real_pdf()
    if not pdf or not os.path.exists(pdf):
        import pytest
        pytest.skip("real floor-2 PDF not present")
    from plan_cluster import extract_clusters
    from placement_gate import footprint, cluster_bbox
    calib = (26.45, 171.2, 596.5)

    # INVISIBILITY GUARD: the DEFAULT room zone (outline padded 150 -> y_min ~= -150) clips the
    # tree at y<0 out entirely — proving the dedicated south-band pass is REQUIRED, not optional.
    default_zone = (5600, -150, 10800, 6400)
    default_items = extract_clusters(pdf, 1, default_zone, 18.0, calib=calib)["items"]
    assert not any(it["y"] < -200 for it in default_items), "default zone should clip the tree"

    # SOUTH-BAND pass (what the gate now runs when the facade corroborates) surfaces the tree
    band = (5750, -2100, 10650, 150)
    south = extract_clusters(pdf, 1, band, 18.0, calib=calib)["items"]
    trees = [it for it in south if it["y"] < 0 and it["curve"]
             and 700 <= it["w"] <= 1200 and 700 <= it["d"] <= 1200]
    assert trees, "the organic garden tree cluster must surface in the south band"
    tree = trees[0]

    els = [{"ref": "tree", "fp": cluster_bbox(tree), "w": tree["w"], "d": tree["d"],
            "area_m2": tree.get("area_m2"), "curve": tree["curve"], "unplaced": True}]
    # the 6 real placed pieces, renderer-true footprints
    sg = json.load(open(_proj("projects/PRJ-2026-002_c001-house/03_layout/v4/scene-graph.sitting_room.json"),
                        encoding="utf-8"))
    for it in sg["items"] + sg["builtins"]:
        els.append({"ref": it["name"], "fp": footprint(it), "w": it["w"], "d": it["d"],
                    "curve": it.get("shape") == "round", "unplaced": False})
    glaz = json.load(open(_proj("projects/PRJ-2026-002_c001-house/03_layout/v4/glazing-candidates.json"),
                          encoding="utf-8"))["candidates"]
    walls = json.load(open(_proj("projects/PRJ-2026-002_c001-house/03_layout/v4/floor2-walls-mm.json"),
                           encoding="utf-8"))["segments"]
    res = Z.zone_proposals(els, SITTING_OUTLINE, glaz, walls)
    below = [p for p in res["proposals"] if p["zone"] == Z.BELOW]
    assert len(below) == 1 and below[0]["ref"] == "tree"          # the machine proposes below_grade
    assert below[0]["confidence"] == "STRONG"
    assert not any(p["zone"] != Z.INDOOR for p in res["indoor"])  # ZERO false positives on placed
    assert len(res["indoor"]) == len(sg["items"]) + len(sg["builtins"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = skipped = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except Exception as e:                     # a pytest.skip raises Skipped; treat as skip
            if type(e).__name__ in ("Skipped", "OutcomeException"):
                skipped += 1
                print(f"SKIP {fn.__name__}: {e}")
            else:
                raise
    print(f"{passed} passed, {skipped} skipped")
