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
