"""Tests for dim_check — pure, no bpy. Run: python -m pytest test_dim_check.py -q

The pinned negative control is the real p2r52 incident: a bought bed's mattress
squeezed to 1243x1569 mm by the whole-cluster fit while every rung stayed green
(ORD-2026-08-18-bed-too-small). dim_check exists so that class of frame fails in
arithmetic, before pixels (ORD-2026-08-22-front-door-dims).
"""
import json

import dim_check as DC


def ob(name, lo, hi, hidden=False):
    return {"name": name, "hidden_render": hidden,
            "aabb": [list(lo), list(hi)]}


def dump_of(objs):
    return {"schema": "scene-dump@2", "objects": objs}


def write(tmp_path, doc, name="scene.json"):
    p = tmp_path / name
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


GARM_SIG = [{"id": "T-1", "class": "garment_rail", "since": "2026-08-13",
             "cite": "ORD-2026-08-12-garment-scale-is-wrong",
             "signed_down_to_mm": 600}]


# ---- the pinned p2r52 control ---------------------------------------------------
def test_p2r52_squeezed_bed_fails():
    d = dump_of([ob("bed__frame__acq0", (0, 0, 0), (1.569, 1.243, 0.38))])
    findings, _ = DC.check(d, [])
    bed = [f for f in findings if f["cls"] == "bed"][0]
    assert bed["state"] == "fail", "1243x1569 is no standard bed and must refuse"


def test_thai_king_cluster_passes():
    d = dump_of([ob("bed__frame__acq0", (0, 0, 0), (2.000, 1.795, 0.38)),
                 ob("bed__cloth__acq0", (0.0, 0.05, 0.3), (1.95, 1.70, 0.55))])
    findings, _ = DC.check(d, [])
    bed = [f for f in findings if f["cls"] == "bed"][0]
    assert bed["state"] == "ok", bed


def test_hand_built_headboard_stays_out_of_the_cluster():
    """bed__headboard carries no __acq — it is R12 sheet-drawn millwork and must
    not stretch the acquired cluster's plan union."""
    d = dump_of([ob("bed__frame__acq0", (0, 0, 0), (2.000, 1.795, 0.38)),
                 ob("bed__headboard", (2.0, -0.1, 0), (2.06, 1.9, 1.1))])
    findings, _ = DC.check(d, [])
    bed = [f for f in findings if f["cls"] == "bed"][0]
    assert bed["state"] == "ok"


# ---- garment rails (ORD-2026-08-12's numbers) -----------------------------------
def rail(salt, z_hi, n=3):
    return [ob(f"mill__style_garmentacq{salt}_{i}__acq0",
               (0.1 * i, 0, 0.0), (0.1 * i + 0.3, 0.4, z_hi)) for i in range(n)]


def test_short_rail_unsigned_fails():
    findings, _ = DC.check(dump_of(rail(0, 0.614)), [])
    r = [f for f in findings if f["cls"] == "garment_rail"][0]
    assert r["state"] == "fail" and "DOLL" in r["why"]


def test_short_rail_signed_is_interim_never_pass():
    findings, _ = DC.check(dump_of(rail(0, 0.614)), GARM_SIG)
    r = [f for f in findings if f["cls"] == "garment_rail"][0]
    assert r["state"] == "interim" and r["sig"]["id"] == "T-1"


def test_signature_does_not_stretch_below_its_floor():
    """signed_down_to_mm 600: a 550 mm doll rail is a NEW worse instance — the
    signature covers the deficit it names, never the class (R13)."""
    findings, _ = DC.check(dump_of(rail(0, 0.550)), GARM_SIG)
    r = [f for f in findings if f["cls"] == "garment_rail"][0]
    assert r["state"] == "fail"


def test_adult_rail_passes():
    findings, _ = DC.check(dump_of(rail(0, 0.715)), [])
    r = [f for f in findings if f["cls"] == "garment_rail"][0]
    assert r["state"] == "ok"


# ---- height bands ---------------------------------------------------------------
def test_side_table_and_bench_bands():
    d = dump_of([ob("side_table__acq0", (0, 0, 0), (0.4, 0.4, 0.400)),
                 ob("side_table__acq0.001", (1, 0, 0), (1.4, 0.4, 0.620)),
                 ob("bench__acq0", (2, 0, 0.34), (2.4, 1.0, 0.406))])
    findings, _ = DC.check(d, [])
    st = {f["what"].split(" ")[0]: f["state"] for f in findings
          if f["cls"] == "side_table"}
    assert st["side_table__acq0"] == "ok"
    assert st["side_table__acq0.001"] == "fail"      # 620 > 480+25
    bench = [f for f in findings if f["cls"] == "bench"][0]
    assert bench["state"] == "ok"


def test_hidden_masses_are_not_judged():
    d = dump_of([ob("side_table__acq0", (0, 0, 0), (0.4, 0.4, 0.9), hidden=True),
                 ob("bench__acq0", (2, 0, 0.34), (2.4, 1.0, 0.406))])
    findings, _ = DC.check(d, [])
    assert not [f for f in findings if f["cls"] == "side_table"]


# ---- exit-code contract (R11) ---------------------------------------------------
def test_missing_dump_is_exit_2(tmp_path):
    assert DC.main([str(tmp_path / "absent.json")]) == 2


def test_zero_judgeable_masses_is_exit_2(tmp_path):
    """Grammar drift must never read as a clean frame."""
    p = write(tmp_path, dump_of([ob("wall_n", (0, 0, 0), (5, 0.1, 2.8))]))
    assert DC.main([p]) == 2


def test_fail_is_exit_1(tmp_path):
    p = write(tmp_path, dump_of(
        [ob("bed__frame__acq0", (0, 0, 0), (1.569, 1.243, 0.38))]))
    empty = tmp_path / "none.json"
    empty.write_text('{"rows": []}', encoding="utf-8")
    assert DC.main([p, "--deficits", str(empty)]) == 1


def test_signed_interim_is_exit_0_and_loud(tmp_path, capsys):
    """The real repo register carries ORD-2026-08-12, so the signature validates;
    interim proceeds with the deficit printed, never silently."""
    p = write(tmp_path, dump_of(
        [ob("bed__frame__acq0", (0, 0, 0), (2.000, 1.795, 0.38))] + rail(0, 0.614)))
    dfp = tmp_path / "def.json"
    dfp.write_text(json.dumps({"rows": GARM_SIG}), encoding="utf-8")
    assert DC.main([p, "--deficits", str(dfp)]) == 0
    out = capsys.readouterr().out
    assert "INTERIM" in out and "DIMS:" in out


def test_unfindable_cite_loses_the_signature(tmp_path):
    """A signature citing an id no register holds was never given — fails closed."""
    p = write(tmp_path, dump_of(rail(0, 0.614)))
    dfp = tmp_path / "def.json"
    dfp.write_text(json.dumps({"rows": [dict(GARM_SIG[0],
                   cite="ORD-9999-99-99-not-a-row")]}), encoding="utf-8")
    assert DC.main([p, "--deficits", str(dfp)]) == 1


# ---------------------------------------------------------------------------------
# THE SLEEPING-PLANE RELATION (added 2026-08-24).
#
# NEGATIVE CONTROL FIRST: the numbers below are the ones the frame actually carried at
# p2r59/p2r60 — side_table top 400, bench seat top 406, mattress top 520. The GENERIC
# ergonomic bands pass both of those green (380-480 +/-25 and 400-450 +/-25), and D-045
# refused that generic band BY NAME. So a rung that only reads those bands cannot see a
# 120 mm gap in an owner-signed relation, and the first test asserts exactly that
# contradiction rather than trusting it.
def matt(lo, hi):
    o = ob("bed__frame__acq1", lo, hi)
    o["materials"] = ["bed_mattress"]
    return o


def test_the_two_rungs_disagree_about_the_same_number():
    """The whole case for this row: same object, same 400 mm, ok on one rung, fail on the
    other. If this ever stops being true the generic band has been changed and one of the
    two is now redundant — say which, in the round that does it."""
    d = dump_of([matt((0, 0, 0.273), (2.0, 1.8, 0.520)),
                 ob("side_table__acq0", (4.8, 2.0, 0.0), (5.2, 2.4, 0.400))])
    found, _ = DC.check(d, [])
    by = {f["cls"]: f for f in found}
    assert by["side_table"]["state"] == "ok"
    assert by["bedside_datum"]["state"] == "fail"
    assert by["bedside_datum"]["measured"] == 120


def test_the_swapped_nightstand_lands_in_the_band():
    """1cf77b3a at scale 1.0: top 470 against a plane of 520 is 50 below — the band edge."""
    d = dump_of([matt((0, 0, 0.273), (2.0, 1.8, 0.520)),
                 ob("side_table__acq0", (4.8, 2.0, 0.0), (5.249, 2.449, 0.470))])
    found, _ = DC.check(d, [])
    assert {f["cls"]: f["state"] for f in found}["bedside_datum"] == "ok"


def test_no_mattress_material_is_unmeasured_not_a_pass():
    """R11's exit-code law applied to a number. A dump whose mattress lost its material
    must not read as a frame whose bedside relation is fine."""
    d = dump_of([ob("side_table__acq0", (4.8, 2.0, 0.0), (5.2, 2.4, 0.400))])
    found, _ = DC.check(d, [])
    f = {x["cls"]: x for x in found}["bedside_datum"]
    assert f["state"] == "fail" and "COULD NOT BE MEASURED" in f["why"]


def test_the_plane_is_read_by_material_not_by_name():
    """R9b: a rule that names the objects it applies to will always exempt the next one.
    A mattress that kept its vendor mesh name (the `Sheet` class of defect) is still
    found, because the role splitter dressed it."""
    o = ob("SomeVendorMeshName", (0, 0, 0.273), (2.0, 1.8, 0.520))
    o["materials"] = ["bed_mattress"]
    assert DC.sleeping_plane_mm([o]) == 520


BENCH_SIG = [{"id": "T-2", "class": "bench_datum", "since": "2026-08-24",
              "cite": "D-115", "signed_up_to_mm": 120}]


def test_a_ceiling_signature_covers_this_bench_and_refuses_a_worse_one():
    """For this class the measurement is HOW FAR BELOW the plane the top sits, so bigger
    is worse and a floor would sign off on arbitrarily worse benches — the opposite of
    the register's own CLASS != INSTANCE law."""
    assert DC._sig(BENCH_SIG, "bench_datum", 114)["id"] == "T-2"
    assert DC._sig(BENCH_SIG, "bench_datum", 121) is None


def test_a_signature_that_names_no_bound_is_refused():
    """An unbounded signature turns every future failure of the class into an interim,
    which is a signed deficit quietly becoming an exemption."""
    assert DC._sig([{"id": "T-3", "class": "bench_datum", "since": "2026-08-24",
                     "cite": "D-115"}], "bench_datum", 114) is None


def test_a_multi_mesh_nightstand_is_ONE_verdict_not_one_per_mesh():
    """THE BUG THIS RUNG SHIPPED WITH, and the fixture that hid it.

    The tests above use a ONE-MESH nightstand, so `for o in group` looked correct. The
    first real multi-mesh piece (1cf77b3a, p2r61q: a leg at z0..451, a sub-part at
    z0.2..419.6 and the round top at z419.6..469.9) produced FOUR bedside_datum rows
    across the two tables and failed the build — by asking of a table LEG whether it was
    a bedside surface. The bedside surface is the top of the PIECE.
    """
    parts = [ob("side_table__acq0", (4.8, 2.0, 0.0), (5.15, 2.09, 0.4511)),
             ob("side_table__acq1", (4.8, 2.0, 0.0002), (4.85, 2.14, 0.4196)),
             ob("side_table__acq2", (4.8, 2.0, 0.4196), (5.249, 2.449, 0.4699))]
    twin = [ob(o["name"] + ".001", o["aabb"][0], o["aabb"][1]) for o in parts]
    d = dump_of([matt((0, 0, 0.273), (2.0, 1.8, 0.520))] + parts + twin)
    rows = [f for f in DC.check(d, [])[0] if f["cls"] == "bedside_datum"]
    assert len(rows) == 2, f"one verdict per table, got {len(rows)}: {[r['what'] for r in rows]}"
    assert all(r["measured"] == 50 for r in rows), [r["measured"] for r in rows]
    assert all(r["state"] == "ok" for r in rows)


def test_the_bench_stays_one_piece_across_its_two_meshes():
    """The same grouping must not split the bench's seat and leg rail into two verdicts."""
    d = dump_of([matt((0, 0, 0.273), (2.0, 1.8, 0.520)),
                 ob("bench__acq0", (2.7, 0.6, 0.0405), (3.1, 1.6, 0.406)),
                 ob("bench__acq1", (2.75, 0.72, 0.0), (3.05, 1.53, 0.061))])
    rows = [f for f in DC.check(d, [])[0] if f["cls"] == "bench_datum"]
    assert len(rows) == 1 and rows[0]["measured"] == 114
