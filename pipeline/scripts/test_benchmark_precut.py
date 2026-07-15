"""Tests + mutation probes for benchmark_precut.py.

Fixtures are SYNTHETIC (tiny PNGs generated in-test, fake I-codes, a PLANTED fake personal name) so
nothing here touches the real client pool -- this file is committed and CI-runnable.

Mutation-probe discipline (repo law -- a green test proves nothing until watched go RED):
each frozen constant is monkeypatched to a mutated value and a known fixture must CHANGE class.
Every probe PREFLIGHTS the unmutated baseline first, so a broken import can't read as an all-RED
pass (the flattering-scorer shape wearing the probe's uniform). A probe that asserts a change
without first pinning the baseline is a no-op; both halves are asserted here.
"""
import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark_precut as B  # noqa: E402

PIL = pytest.importorskip("PIL.Image")


# --------------------------------------------------------------------------- fixtures
def _png(path, w, h, kind="gradient"):
    from PIL import Image
    im = Image.new("L", (w, h))
    px = []
    for y in range(h):
        for x in range(w):
            if kind == "gradient":
                px.append((x * 255) // max(1, w))
            elif kind == "inverted":
                px.append(255 - ((x * 255) // max(1, w)))
            elif kind == "gradient_noise":  # near-identical to gradient (one flipped block)
                v = (x * 255) // max(1, w)
                if x < 1 and y < 1:
                    v = 255 - v
                px.append(v)
            else:
                px.append(128)
    im.putdata(px)
    im.save(path)


# --------------------------------------------------------------------------- pure classifiers
def test_icode_strips_personal_name():
    assert B.extract_icode("update/002_I-24-020-คุณมิกซ์") == "I-24-020"
    assert B.extract_icode("โปรเจ็ก/015_F-24-004-คุณก้อย") == "F-24-004"
    assert B.extract_icode("โปรเจ็ก/001_คุณ-A") is None  # no code -> UNCODED downstream


def test_render_engine_detection():
    assert B.render_engine("236250_Enscape_2024-05.png") == "ENSCAPE"
    assert B.render_engine("LINE_ALBUM_2024_image.jpg") is None


def test_dim_class_16x9_4k_render_is_NOT_a_photo():
    # THE TRAP: a 4K 16:9 render is 3840x2160. Naive max>=3000 would call it a photo.
    assert B.dim_class([3840, 2160], None) == "render"
    # a real 4:3 site photo (iPhone) with no render name
    assert B.dim_class([4032, 3024], None) == "site_photo"
    # engine name OVERRIDES the photo test even at 4:3 / large
    assert B.dim_class([4000, 3000], "ENSCAPE") == "render"
    assert B.dim_class([1600, 900], None) == "render"
    assert B.dim_class([800, 600], None) == "small"


def test_sector_commercial_vs_residential():
    s, kw = B.sector("โปรเจ็ก/009_I-23-051-รพ.เซนต์แมรี่-แผนกห้องคลอด")
    assert s == "commercial" and kw
    s, kw = B.sector("โปรเจ็ก/027_I-25-004-โรงแรม,Fitness,Spa")
    assert s == "commercial"
    s, kw = B.sector("update/002_I-24-020-คุณมิกซ์")
    assert s == "residential" and kw is None


def test_room_hint_only_when_named():
    assert B.room_hint("โปรเจ็ก/013_F-24-001-ห้องน้ำ") == "bathroom"
    assert B.room_hint("update/002_I-24-020-คุณมิกซ์") is None  # whole-house -> no hint


def test_delivery_signal_never_asserts_delivered():
    for proj in ("update/002_I-24-020-x", "โปรเจ็ก/024_I-24-043-x"):
        sig = B.delivery_signal(proj)
        assert "proposed" in sig and "unconfirmed" in sig
        assert "delivered" not in sig.lower().replace("unconfirmed", "")


def test_phash_near_dup_close_far_apart(tmp_path):
    a = str(tmp_path / "a.png"); a2 = str(tmp_path / "a2.png"); b = str(tmp_path / "b.png")
    _png(a, 64, 64, "gradient"); _png(a2, 64, 64, "gradient_noise"); _png(b, 64, 64, "inverted")
    ha, ha2, hb = B.phash_of(a), B.phash_of(a2), B.phash_of(b)
    assert B.hamming(ha, ha2) <= B.PHASH_HAMMING_MAX      # near-dup merges
    assert B.hamming(ha, hb) > B.PHASH_HAMMING_MAX        # opposite does not


def test_phash_error_returns_none_and_keeps(tmp_path):
    assert B.phash_of(str(tmp_path / "missing.png")) is None


# --------------------------------------------------------------------------- integration
def _fixture_pool(tmp_path):
    """3 residential renders (2 near-dup, same icode), 1 commercial render, 1 site photo, 1 small.

    wh is DECLARED metadata (as in candidates.json), so the actual files stay 64x64 while the
    render-intended ones declare render-grade dimensions. Paths use '/' like the real manifest.
    """
    base = str(tmp_path).replace("\\", "/") + "/_p"
    specs = [
        # (relpath, declared_wh, actual_kind)
        ("update/002_I-24-020-คุณมิกซ์/files/1_Enscape.png", [1600, 900], "gradient"),
        ("update/002_I-24-020-คุณมิกซ์/files/2_Enscape.png", [1600, 900], "gradient_noise"),  # dup#1
        ("โปรเจ็ก/024_I-24-043-Pandora/files/3_view.png", [1920, 1080], "inverted"),          # distinct
        ("โปรเจ็ก/009_I-23-051-รพ.เซนต์แมรี่/files/4.png", [1600, 900], "gradient"),           # commercial
        ("โปรเจ็ก/002_I-23-023-photo/files/5.png", [4032, 3024], "flat"),                     # site photo
        ("โปรเจ็ก/024_I-24-043-Pandora/files/6.png", [800, 600], "flat"),                     # small
    ]
    cands = []
    for rel, wh, kind in specs:
        p = base + "/" + rel
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _png(p, 64, 64, kind)                       # tiny real file; wh below is the metadata
        cands.append({"path": p, "bytes": 1000, "project": rel.rsplit("/files/", 1)[0], "wh": wh})
    return cands


def test_build_precut_counts_and_never_deletes(tmp_path):
    cands = _fixture_pool(tmp_path)
    pc = B.build_precut(cands)
    assert len(pc["rows"]) == len(cands)                 # nothing silently dropped
    assert len(pc["pool"]) + len(pc["excluded"]) == len(cands)
    assert pc["drops"].get("commercial") == 1
    assert pc["drops"].get("dim_class=site_photo") == 1
    assert pc["drops"].get("dim_class=small") == 1
    assert pc["n_pool"] == 3                             # 2 Enscape + 1 Pandora view
    assert pc["dup_clusters"] == 1                       # the two Enscape near-dups
    assert pc["n_distinct"] == 2


def test_dedup_only_within_icode(tmp_path):
    # same near-dup content under DIFFERENT icodes must NOT merge
    base = str(tmp_path).replace("\\", "/") + "/_p"
    cands = []
    for rel in ("update/002_I-24-020-x/files/a_Enscape.png",
                "update/003_I-24-099-y/files/a_Enscape.png"):
        p = base + "/" + rel
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _png(p, 64, 64, "gradient")
        cands.append({"path": p, "bytes": 1, "project": rel.rsplit("/files/", 1)[0],
                      "wh": [1600, 900]})
    pc = B.build_precut(cands)
    assert pc["dup_clusters"] == 0                       # different icodes: never merged
    assert pc["n_distinct"] == 2


def test_worksheet_leaks_no_personal_name(tmp_path):
    cands = _fixture_pool(tmp_path)
    pc = B.build_precut(cands)
    out = tmp_path / "out"
    B.write_outputs(pc, str(out))
    ws = (out / "precut-worksheet.md").read_text(encoding="utf-8")
    for name in ("คุณมิกซ์", "Pandora", "เซนต์แมรี่"):
        assert name not in ws, f"worksheet leaked a personal/project name: {name}"
    # it MUST carry the I-codes instead
    assert "I-24-020" in ws and "I-24-043" in ws


# --------------------------------------------------------------------------- review hardening
def test_safe_slug_scrubs_a_name_in_segment_zero():
    assert B.safe_slug("update/002_I-24-020-x") == "update"
    assert B.safe_slug("โปรเจ็ก/024_I-24-043-x") == "โปรเจ็ก"
    # a personal name in segment-0 (upstream manifest shape change) must NOT pass through
    assert B.safe_slug("K.หมอสมชาย/renders/x.png") == "OTHER-SLUG"


def test_segment0_name_never_egresses_to_stdout_or_worksheet(tmp_path, capsys):
    # An anomalous manifest whose FIRST segment carries a client name. The name must appear in
    # NEITHER the stdout summary NOR the worksheet (the two egress-capable surfaces).
    base = str(tmp_path).replace("\\", "/") + "/_p"
    p = base + "/K.หมอสมชาย/005_I-24-100/files/1_Enscape.png"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    _png(p, 64, 64, "gradient")
    cands = [{"path": p, "bytes": 1, "project": "K.หมอสมชาย/005_I-24-100", "wh": [1600, 900]}]
    pc = B.build_precut(cands)
    out = tmp_path / "o"; B.write_outputs(pc, str(out))
    B.print_summary(pc)
    captured = capsys.readouterr().out
    ws = (out / "precut-worksheet.md").read_text(encoding="utf-8")
    assert "หมอสมชาย" not in ws and "หมอสมชาย" not in captured
    assert "OTHER-SLUG" in ws                       # scrubbed marker shown instead
    assert "I-24-100" in ws                          # the real (safe) identifier survives


def test_photo_suspect_flags_4x3_subthreshold_only():
    assert B.is_photo_suspect([2048, 1536], None) is True      # 4:3, 1000-2999, no engine
    assert B.is_photo_suspect([1920, 1080], None) is False     # 16:9 -> not photo-shaped
    assert B.is_photo_suspect([4032, 3024], None) is False     # >=3000 -> that's a site_photo
    assert B.is_photo_suspect([2048, 1536], "ENSCAPE") is False  # engine name overrides


def test_photo_suspect_kept_in_pool_and_flagged(tmp_path):
    base = str(tmp_path).replace("\\", "/") + "/_p"
    p = base + "/โปรเจ็ก/024_I-24-043-x/files/1.png"           # 2048x1536 4:3, no engine
    os.makedirs(os.path.dirname(p), exist_ok=True)
    _png(p, 64, 64, "gradient")
    cands = [{"path": p, "bytes": 1, "project": "โปรเจ็ก/024_I-24-043-x", "wh": [2048, 1536]}]
    pc = B.build_precut(cands)
    assert pc["n_pool"] == 1                                    # kept, NOT excluded
    assert len(pc["photo_suspect"]) == 1 and pc["pool"][0]["photo_suspect"] is True


def test_d5_render_provenance_now_matches_real_naming():
    assert B.render_engine("236_D5_Render_2024.png") == "D5_RENDER"
    assert B.render_engine("236_D5 Render_2024.png") == "D5 RENDER"


def test_excluded_and_photo_suspect_serialized_in_json(tmp_path):
    cands = _fixture_pool(tmp_path)
    pc = B.build_precut(cands)
    out = tmp_path / "o"; B.write_outputs(pc, str(out))
    import json as _json
    js = _json.loads((out / "precut.json").read_text(encoding="utf-8"))
    assert "excluded" in js and len(js["excluded"]) == 3       # commercial + site_photo + small
    assert {e["excluded_by"] for e in js["excluded"]} == {
        "commercial:รพ.", "dim_class=site_photo", "dim_class=small"}
    assert all("ref" in e and "excluded_by" in e for e in js["excluded"])
    assert "photo_suspect" in js                                # key present (empty for this fixture)


def test_dedup_chain_flattened_when_highres_arrives_last(tmp_path, monkeypatch):
    # r1,r2 same-icode near-dups (r2 dup of r1); r3 higher-res arrives LAST and swaps in as rep.
    # Without chain-flattening r2.dup_of would still point at r1 (itself now a dup) -- a 2-hop chain.
    base = str(tmp_path).replace("\\", "/") + "/_p"
    cands = []
    for name, wh in (("1", [1600, 900]), ("2", [1600, 900]), ("3", [1920, 1080])):
        p = base + f"/update/002_I-24-020-x/files/{name}_Enscape.png"
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _png(p, 64, 64, "gradient")
        cands.append({"path": p, "bytes": 1, "project": "update/002_I-24-020-x", "wh": wh})
    fake = {cands[0]["path"]: 0b000, cands[1]["path"]: 0b011, cands[2]["path"]: 0b000}
    monkeypatch.setattr(B, "phash_of", lambda path: fake[path])
    pc = B.build_precut(cands)
    assert pc["n_distinct"] == 1                                # only r3 is the representative
    ref_row = {r["ref"]: r for r in pc["pool"]}
    for r in pc["pool"]:                                        # no dup_of points at another dup
        if r["dup_of"] is not None:
            assert ref_row[r["dup_of"]]["dup_of"] is None, "dup_of chain not flattened"


# --------------------------------------------------------------------------- mutation probes
@pytest.fixture
def restore_module():
    """Reload benchmark_precut after any monkeypatch so later tests see pristine constants."""
    yield
    importlib.reload(B)


def _classify(wh, engine=None):
    return B.dim_class(wh, engine)


def test_probe_PHOTO_MIN_DIM_is_load_bearing(monkeypatch, restore_module):
    assert _classify([4032, 3024]) == "site_photo"               # PREFLIGHT baseline
    monkeypatch.setattr(B, "PHOTO_MIN_DIM", 5000)
    assert _classify([4032, 3024]) == "render"                   # mutation flips it -> RED-if-broken


def test_probe_PHOTO_ASPECT_TOL_is_load_bearing(monkeypatch, restore_module):
    assert _classify([3000, 2000]) == "render"                   # 3:2 large, baseline not a photo
    monkeypatch.setattr(B, "PHOTO_ASPECT_TOL", 0.30)             # 3:2 now inside 4:3 tolerance
    assert _classify([3000, 2000]) == "site_photo"


def test_probe_RENDER_MIN_DIM_is_load_bearing(monkeypatch, restore_module):
    assert _classify([1600, 900]) == "render"                    # baseline
    monkeypatch.setattr(B, "RENDER_MIN_DIM", 2000)
    assert _classify([1600, 900]) == "small"


def test_probe_engine_override_is_load_bearing(tmp_path, monkeypatch, restore_module):
    # A 4:3 large image NAMED Enscape must land in the pool (render); strip the provenance
    # token and the identical metadata reclassifies to an excluded site_photo. wh is declared
    # metadata (as in candidates.json), so a tiny file can stand in for a 4000x3000 render.
    root = tmp_path / "_p"; root.mkdir()
    p = root / "update/002_I-24-020-x/files/1_Enscape.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    _png(str(p), 64, 64, "gradient")
    cands = [{"path": str(p), "bytes": 1,
              "project": "update/002_I-24-020-x", "wh": [4000, 3000]}]
    assert B.build_precut(cands)["n_pool"] == 1                   # baseline: engine wins -> render
    monkeypatch.setattr(B, "RENDER_ENGINE_TOKENS", ())           # provenance stripped
    pc = B.build_precut(cands)
    assert pc["n_pool"] == 0 and pc["drops"].get("dim_class=site_photo") == 1


def test_probe_commercial_keyword_is_load_bearing(monkeypatch, restore_module):
    proj = "โปรเจ็ก/009_I-23-051-รพ.เซนต์แมรี่"
    assert B.sector(proj)[0] == "commercial"                     # baseline
    monkeypatch.setattr(B, "COMMERCIAL_KEYWORDS", ("nonexistent",))
    assert B.sector(proj)[0] == "residential"                    # keyword gone -> misclassified


def test_probe_PHASH_HAMMING_MAX_is_load_bearing(tmp_path, monkeypatch, restore_module):
    # Two same-icode renders whose hashes differ by exactly 2 bits. Baseline (max=4) merges;
    # threshold 0 must not. phash_of is monkeypatched so the distance is EXACT, not luck.
    base = str(tmp_path).replace("\\", "/") + "/_p"
    cands = []
    for i, rel in enumerate(("update/002_I-24-020-x/files/a_Enscape.png",
                             "update/002_I-24-020-x/files/b_Enscape.png")):
        p = base + "/" + rel
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _png(p, 64, 64, "gradient")
        cands.append({"path": p, "bytes": 1, "project": rel.rsplit("/files/", 1)[0],
                      "wh": [1600, 900]})
    fake = {cands[0]["path"]: 0b0000, cands[1]["path"]: 0b0011}   # hamming == 2
    monkeypatch.setattr(B, "phash_of", lambda path: fake[path])
    assert B.build_precut(cands)["dup_clusters"] == 1            # baseline: 2 <= 4 -> merge
    monkeypatch.setattr(B, "PHASH_HAMMING_MAX", 0)
    assert B.build_precut(cands)["dup_clusters"] == 0            # 2 <= 0 false -> no merge


# --------------------------------------------------------------------------- frozen guard
def test_frozen_constants_pass_and_drift_raises(monkeypatch):
    B._assert_frozen()                                           # pristine passes
    monkeypatch.setitem(B._FROZEN, "PHOTO_MIN_DIM", 9999)
    with pytest.raises(AssertionError):
        B._assert_frozen()
