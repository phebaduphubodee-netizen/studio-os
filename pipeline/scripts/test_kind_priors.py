"""test_kind_priors.py -- unit + mutation-pin tests for the deterministic size/aspect
priors lane. ALL fixtures are self-authored synthetic gt.json dicts written into tmp_path
-- never corpus files (CC BY-NC, never redistributed; same rule as the adapter tests).

    python -m pytest test_kind_priors.py -q
"""
import json
import os

import kind_priors


def _gt(tmp_path, name, units, elements, openings=None):
    """Write a minimal gt.json and return its directory."""
    doc = {"meta": {"units": units,
                    "scale_mm_per_unit": 100.0 if units == "mm" else None},
           "elements": elements, "openings": openings or []}
    fp = os.path.join(str(tmp_path), name + ".gt.json")
    with open(fp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return os.path.dirname(fp)


def _tables(n=60, w0=1600, d0=800, spread=100.0, kind="table"):
    """n elements whose larger side ~w0, smaller side ~d0, spread evenly +-spread."""
    els = []
    for i in range(n):
        off = (i / (n - 1) * 2 - 1) * spread          # -spread .. +spread
        els.append({"id": f"{kind}{i}", "kind": kind,
                    "x": 0, "y": 0, "w": w0 + off, "d": d0 + off})
    return els


def _p(kinds):
    return {"schema": kind_priors.SCHEMA, "meta": {"params": {}}, "kinds": kinds}


# ---- derive ------------------------------------------------------------------------------
def test_derive_bands_from_synthetic_gt(tmp_path):
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50)
    assert "table" in pr["kinds"]
    b = pr["kinds"]["table"]
    assert b["n"] == 60
    assert b["lo_mm"][0] <= 800 <= b["lo_mm"][1]
    assert b["hi_mm"][0] <= 1600 <= b["hi_mm"][1]
    assert pr["meta"]["params"] == {"q_lo": 0.10, "q_hi": 0.90, "pad_mm": 50.0,
                                    "aspect_pad": 1.15, "min_support": 50}


def test_svg_unit_files_are_excluded(tmp_path):
    """Mutation pin: a mutant that drops the units filter would fold the 16x8 raw-unit
    rows into the band and shift lo_mm[0] below 0 -- deriving twice from the SAME dir
    (so provenance basenames match) before and after the svg-unit file lands must yield
    byte-identical kinds dicts, and the units skip must be counted."""
    d = _gt(tmp_path, "mm_sheet", "mm", _tables())
    before = kind_priors.derive([d], min_support=50)
    _gt(tmp_path, "raw_sheet", "svg-unit", _tables(w0=16, d0=8, spread=1.0))
    after = kind_priors.derive([d], min_support=50)
    assert before["kinds"] == after["kinds"]
    assert after["meta"]["n_files_skipped_units"] == 1
    assert after["kinds"]["table"]["lo_mm"][0] > 0


def test_openings_never_enter_element_bands(tmp_path):
    """Door-sized rows (~999 mm) live in openings; if derive() ever sampled openings a
    phantom ~1 m band would land in furniture territory. Only elements are sampled."""
    doors = [{"type": "sliding", "x": 0, "y": 0, "w": 999, "d": 100} for _ in range(60)]
    d = _gt(tmp_path, "mixed", "mm", _tables(), openings=doors)
    pr = kind_priors.derive([d], min_support=50)
    assert pr["meta"]["n_elements_sampled"] == 60
    assert list(pr["kinds"].keys()) == ["table"]


def test_min_support_excludes_thin_kinds(tmp_path):
    d = _gt(tmp_path, "thin", "mm", _tables(n=3, kind="wardrobe"))
    pr = kind_priors.derive([d], min_support=5)
    assert "wardrobe" not in pr["kinds"]
    assert pr["excluded_low_support"]["wardrobe"] == 3


# ---- suggest -----------------------------------------------------------------------------
def test_suggest_unique_band_emits():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(1600, 800, p) == "table"


def test_suggest_ambiguity_stays_unreported():
    """THE mutation pin: the mutant `return cands[0] if cands else None` (dropping the
    len == 1 check) would guess on ambiguity -- a false-accept, the exact flattering
    failure the scorer-honesty doctrine bans. Two identical bands -> None."""
    band = {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0], "aspect": [1.5, 2.5]}
    p = _p({"table": dict(band), "cabinet": dict(band)})
    assert kind_priors.suggest_kind(1600, 800, p) is None


def test_suggest_orientation_agnostic():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(800, 1600, p) == kind_priors.suggest_kind(1600, 800, p)


def test_suggest_outside_all_bands_is_none():
    p = _p({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0],
                      "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(10000, 10000, p) is None
    assert kind_priors.suggest_kind(0, 500, p) is None          # non-positive guard


def test_provenance_recorded_per_band(tmp_path):
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50)
    assert pr["schema"] == kind_priors.SCHEMA == "interior-ai/kind-priors@0.2"
    for row in pr["kinds"].values():
        assert isinstance(row["provenance"], str) and row["provenance"]
        assert isinstance(row["n"], int)


# ---- curve signature (v2) ----------------------------------------------------------------
def _pc(kinds):
    """priors doc with kinds that may carry a `curve` signature."""
    return {"schema": kind_priors.SCHEMA, "meta": {"params": {}}, "kinds": kinds}


# two bands that OVERLAP on size (a chair-vs-table style tie), split only by curve class
_TIE_BAND = {"lo_mm": [400.0, 700.0], "hi_mm": [400.0, 700.0], "aspect": [1.0, 1.5]}
_CURVED = {"n": 100, "frac": 0.95, "curve_n": 95}     # >= CURVE_HI
_BOXY = {"n": 100, "frac": 0.03, "curve_n": 3}        # <= CURVE_LO


def test_curve_breaks_a_size_tie_both_directions():
    p = _pc({"chair": {**_TIE_BAND, "curve": _CURVED},
             "table": {**_TIE_BAND, "curve": _BOXY}})
    assert kind_priors.suggest_kind(500, 550, p, curve=True) == "chair"   # curved -> not the BOXY table
    assert kind_priors.suggest_kind(500, 550, p, curve=False) == "table"  # boxy   -> not the CURVED chair
    assert kind_priors.suggest_kind(500, 550, p, curve=None) is None      # no curve info -> unreported


def test_curve_never_overrides_a_unique_size_hit():
    """A unique size membership must emit regardless of curve -- back-compat with the
    size-only lane (the 0.4% baseline must be reproducible)."""
    p = _pc({"bed": {"lo_mm": [800.0, 1000.0], "hi_mm": [1800.0, 2000.0],
                     "aspect": [1.5, 2.5], "curve": _BOXY}})
    assert kind_priors.suggest_kind(1900, 900, p, curve=True) == "bed"    # curve does NOT veto
    assert kind_priors.suggest_kind(1900, 900, p, curve=False) == "bed"


def test_curve_two_curved_kinds_stay_ambiguous():
    """Curve resolves a tie only when it leaves exactly one -- two curved kinds -> None."""
    p = _pc({"chair": {**_TIE_BAND, "curve": _CURVED},
             "toilet": {**_TIE_BAND, "curve": _CURVED}})
    assert kind_priors.suggest_kind(500, 550, p, curve=True) is None


def test_curve_under_support_signature_is_ignored():
    """A kind with < MIN_CURVE_SUPPORT pairs has an UNTRUSTED signature -> class None -> it is
    never DROPPED on curve, so a tie it is part of stays unresolved. Contrast: were its (boxy)
    signature trusted, a curved element would drop it and resolve to chair -- here it does not."""
    thin_boxy = {"n": kind_priors.MIN_CURVE_SUPPORT - 1, "frac": 0.0, "curve_n": 0}
    p = _pc({"chair": {**_TIE_BAND, "curve": _CURVED},        # trusted curved
             "table": {**_TIE_BAND, "curve": thin_boxy}})     # boxy but UNDER support -> untrusted
    assert kind_priors.suggest_kind(500, 550, p, curve=True) is None      # table not dropped -> 2 left
    # sanity: promote table's support over the bar and the SAME query now resolves to chair
    p["kinds"]["table"]["curve"] = {"n": 100, "frac": 0.0, "curve_n": 0}
    assert kind_priors.suggest_kind(500, 550, p, curve=True) == "chair"


def test_curve_default_arg_reproduces_size_only():
    p = _pc({"table": {"lo_mm": [700.0, 900.0], "hi_mm": [1500.0, 1700.0], "aspect": [1.5, 2.5]}})
    assert kind_priors.suggest_kind(1600, 800, p) == kind_priors.suggest_kind(1600, 800, p, curve=None)


def test_accumulate_curve_counts():
    pairs = [("chair", True), ("chair", True), ("chair", False), ("table", False),
             (None, True), ("table", False)]
    st = kind_priors.accumulate_curve(pairs)
    assert st == {"chair": {"n": 3, "curve": 2}, "table": {"n": 2, "curve": 0}}   # None kind dropped


def test_merge_curve_signatures_supports_and_bumps_schema():
    size = {"schema": "interior-ai/kind-priors@0.1", "meta": {},
            "kinds": {"chair": dict(_TIE_BAND), "sofa": dict(_TIE_BAND)}}
    stats = {"chair": {"n": 100, "curve": 88}, "sofa": {"n": 5, "curve": 5}}   # sofa under support
    aug = kind_priors.merge_curve_signatures(size, stats, source="gt-train-00")
    assert aug["schema"] == "interior-ai/kind-priors@0.2"
    assert aug["kinds"]["chair"]["curve"]["frac"] == 0.88 and aug["kinds"]["chair"]["curve"]["n"] == 100
    assert "curve" not in aug["kinds"]["sofa"]                 # under support -> no signature
    assert aug["meta"]["curve"]["kinds_with_signature"] == 1
    assert size["kinds"]["chair"].get("curve") is None         # input not mutated (deep copy)


def test_load_accepts_v01_and_v02(tmp_path):
    for schema in ("interior-ai/kind-priors@0.1", "interior-ai/kind-priors@0.2"):
        fp = os.path.join(str(tmp_path), schema.replace("/", "_") + ".json")
        json.dump({"schema": schema, "kinds": {}}, open(fp, "w"))
        assert kind_priors.load(fp)["schema"] == schema


# ---- build_prior_context (confidence corroboration injector, 2026-07-13 wiring) ----------
def _band(lo, hi, asp, n=60):
    return {"lo_mm": list(lo), "hi_mm": list(hi), "aspect": list(asp), "n": n}


def test_context_exact_agreement_injects_the_claimed_kind():
    priors = _p({"sofa": _band((514, 1122), (700, 2546), (1.0, 3.6))})
    ctx = kind_priors.build_prior_context(
        [{"name": "โซฟา", "kind": "sofa", "w": 2202, "d": 1008}], priors)
    assert ctx == {"โซฟา": {"prior_kind": "sofa"}}


def test_context_alias_agreement_injects_the_CLAIMED_string():
    # claimed 'armchair' uniquely hitting the corpus 'chair' band IS agreement -- the injected
    # value must equal the claimed string so confidence's equality check reads corroboration.
    priors = _p({"chair": _band((250, 615), (310, 688), (1.0, 1.55))})
    ctx = kind_priors.build_prior_context(
        [{"name": "tub", "kind": "armchair", "w": 510, "d": 546}], priors)
    assert ctx == {"tub": {"prior_kind": "armchair"}}


def test_context_disagreement_is_injected_raw_and_visible():
    # a 300x300 'side_table' uniquely fitting the urinal band must NOT corroborate -- the raw
    # suggestion is injected (visible), equality fails, and there is no downgrade path.
    priors = _p({"urinal": _band((220, 451), (290, 496), (1.0, 1.56))})
    ctx = kind_priors.build_prior_context(
        [{"name": "st", "kind": "side_table", "w": 300, "d": 300}], priors)
    assert ctx == {"st": {"prior_kind": "urinal"}}


def test_context_ambiguity_and_unnamed_inject_nothing():
    priors = _p({"chair": _band((250, 615), (310, 688), (1.0, 1.6)),
                 "stoolish": _band((250, 615), (310, 688), (1.0, 1.6))})
    ctx = kind_priors.build_prior_context(
        [{"name": "a", "kind": "chair", "w": 500, "d": 550},      # 2 candidates -> None
         {"kind": "chair", "w": 500, "d": 550}], priors)          # unnamed -> skipped
    assert ctx == {}


def test_context_never_corroborates_an_exempt_kind():
    # the load-bearing pin: claimed 'cabinet' uniquely hitting the corpus freestanding-cabinet
    # band must NOT be injected at all -- corroborating repo 'cabinet' off that band is the same
    # population error as false-flagging it (repo cabinet includes built-in millwork runs).
    priors = _p({"cabinet": _band((250, 650), (355, 1280), (1.0, 3.45))})
    ctx = kind_priors.build_prior_context(
        [{"name": "ตู้", "kind": "cabinet", "w": 400, "d": 700}], priors)
    assert ctx == {}


def test_context_exemption_is_case_insensitive_like_confidence():
    # review finding 2026-07-13: confidence's equality LOWERCASES both sides, so a hand-typed
    # 'Cabinet' injected as a "disagreement" ({'prior_kind': 'cabinet'}) would still read as
    # CORROBORATED downstream -- the exemption (and agreement) decisions must therefore be made
    # on the lowercased claim. 'Cabinet'/'CABINET' must inject NOTHING.
    priors = _p({"cabinet": _band((250, 650), (355, 1280), (1.0, 3.45))})
    for claimed in ("Cabinet", "CABINET", " cabinet "):
        ctx = kind_priors.build_prior_context(
            [{"name": "ตู้", "kind": claimed, "w": 400, "d": 700}], priors)
        assert ctx == {}, claimed


def test_context_case_variant_agreement_still_corroborates():
    # ...and the flip side: a case-variant 'Sofa' IS the same identity under the codebase's own
    # equivalence (confidence lowercases), so agreement must still inject the claimed string.
    priors = _p({"sofa": _band((514, 1122), (700, 2546), (1.0, 3.6))})
    ctx = kind_priors.build_prior_context(
        [{"name": "s", "kind": "Sofa", "w": 2202, "d": 1008}], priors)
    assert ctx == {"s": {"prior_kind": "Sofa"}}


# ---- multi-corpus (2026-07-14 wiring: FloorPlanCAD + Structured3D live together) ----------
def test_as_docs_normalizes_none_dict_and_list():
    doc = _p({"sofa": _band((514, 1122), (700, 2546), (1.0, 3.6))})
    assert kind_priors.as_docs(None) == []
    assert kind_priors.as_docs(doc) == [doc]
    assert kind_priors.as_docs([doc, doc]) == [doc, doc]


def test_as_docs_raises_on_a_garbage_entry_never_shrinks_silently():
    # a dead doc must surface as an ERROR in the caller's coverage (the 2026-07-13 dead-lane
    # finding) -- silently dropping it would let a broken artifact read as WIRED-and-clean.
    doc = _p({"sofa": _band((514, 1122), (700, 2546), (1.0, 3.6))})
    for garbage in ({"schema": "interior-ai/kind-priors@0.2"}, "not-a-doc", 42):
        try:
            kind_priors.as_docs([doc, garbage])
            raise AssertionError(f"as_docs accepted {garbage!r}")
        except ValueError:
            pass


def test_context_single_doc_list_reproduces_dict_behaviour():
    priors = _p({"sofa": _band((514, 1122), (700, 2546), (1.0, 3.6)),
                 "urinal": _band((220, 451), (290, 496), (1.0, 1.56))})
    pieces = [{"name": "โซฟา", "kind": "sofa", "w": 2202, "d": 1008},
              {"name": "st", "kind": "side_table", "w": 300, "d": 300}]
    assert (kind_priors.build_prior_context(pieces, [priors])
            == kind_priors.build_prior_context(pieces, priors))


def test_context_second_doc_corroborates_when_first_is_ambiguous():
    # the Structured3D bed case: the drawn-symbol doc is ambiguous on the footprint, the
    # real-furniture doc uniquely agrees -- corroboration must fire (agree + no disagree).
    band = _band((1400, 2100), (1900, 2400), (1.0, 1.7))
    ambiguous = _p({"bed": dict(band), "rug": dict(band)})     # 2 candidates -> None
    real = _p({"bed": _band((1444, 2512), (1950, 3016), (1.0, 1.7))})
    ctx = kind_priors.build_prior_context(
        [{"name": "เตียง", "kind": "bed", "w": 2134, "d": 1981}], [ambiguous, real])
    assert ctx == {"เตียง": {"prior_kind": "bed"}}


def test_context_any_unique_disagreement_blocks_corroboration():
    # THE multi-corpus anti-flattering pin: one doc uniquely agreeing must NOT outvote another
    # doc uniquely suggesting a DIFFERENT kind -- counter-evidence from an independent corpus
    # blocks the 0.70 and stays visible (the disagreeing suggestion is what gets injected).
    agreeing = _p({"bed": _band((1444, 2512), (1950, 3016), (1.0, 1.7))})
    disagreeing = _p({"altar": _band((1900, 2300), (1950, 2200), (1.0, 1.2))})
    ctx = kind_priors.build_prior_context(
        [{"name": "เตียง", "kind": "bed", "w": 2134, "d": 1981}], [agreeing, disagreeing])
    assert ctx == {"เตียง": {"prior_kind": "altar"}}


def test_context_alias_SOURCE_keyed_doc_agrees_never_fake_disagrees():
    # review finding 2026-07-14: a doc whose own vocabulary carries the claimed kind (keyed
    # 'armchair', not the alias target 'chair') suggested 'armchair', landed in the
    # DISAGREEMENT branch, and the injected string lowercase-equalled the claim -> read as
    # CORROBORATED through the wrong door. Saying the claim's own name IS agreement.
    armchair_doc = _p({"armchair": _band((500, 800), (600, 1000), (1.0, 1.6))})
    ctx = kind_priors.build_prior_context(
        [{"name": "ch", "kind": "armchair", "w": 700, "d": 900}], [armchair_doc])
    assert ctx == {"ch": {"prior_kind": "armchair"}}       # agreement branch (claimed string)
    # ...and a GENUINE unique disagreement from a second doc still blocks the 0.70 and is
    # what gets injected -- it can never be outvoted by the agreement:
    table_doc = _p({"altar": _band((650, 750), (850, 950), (1.0, 1.5))})
    ctx2 = kind_priors.build_prior_context(
        [{"name": "ch", "kind": "armchair", "w": 700, "d": 900}], [armchair_doc, table_doc])
    assert ctx2 == {"ch": {"prior_kind": "altar"}}
    # invariant restored: a disagreement injection never lowercase-equals the claim
    assert ctx2["ch"]["prior_kind"].lower() != "armchair"


def test_context_ambiguity_in_every_doc_still_injects_nothing():
    band = _band((1400, 2600), (1900, 3100), (1.0, 1.7))
    doc1 = _p({"bed": dict(band), "rug": dict(band)})
    doc2 = _p({"bed": dict(band), "mat": dict(band)})
    ctx = kind_priors.build_prior_context(
        [{"name": "เตียง", "kind": "bed", "w": 2134, "d": 1981}], [doc1, doc2])
    assert ctx == {}


# ---- derive: source + max_dispersion (Structured3D derivation, 2026-07-14) ----------------
def test_derive_source_prefixes_provenance_and_records_meta(tmp_path):
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50, source="structured3d")
    assert pr["kinds"]["table"]["provenance"].startswith("structured3d ")
    assert pr["meta"]["source"] == "structured3d"


def test_derive_default_output_is_byte_compatible(tmp_path):
    # the committed FloorPlanCAD artifact must stay reproducible: default derive() output
    # carries NO new keys -- no meta.source, no excluded_degenerate, no params.max_dispersion.
    d = _gt(tmp_path, "s", "mm", _tables())
    pr = kind_priors.derive([d], min_support=50)
    assert "source" not in pr["meta"]
    assert "excluded_degenerate" not in pr
    assert "max_dispersion" not in pr["meta"]["params"]
    assert pr["kinds"]["table"]["provenance"].startswith("floorplancad ")


def test_derive_max_dispersion_refuses_a_mixed_population(tmp_path):
    # a 'sofa' class whose labels mix cushion fragments (~100x150) with real sofas
    # (~900x2000) is NOT one size population: 10-90 short-side ratio ~9x. It must land in
    # excluded_degenerate WITH its measured ratios (dropped-and-counted), while a tight kind
    # in the same corpus keeps its band.
    els = (_tables(n=30, w0=150, d0=100, spread=5.0, kind="sofa")
           + _tables(n=30, w0=2000, d0=900, spread=50.0, kind="sofa")
           + _tables(n=60, w0=2000, d0=1500, spread=100.0, kind="bed"))
    d = _gt(tmp_path, "mix", "mm", els)
    pr = kind_priors.derive([d], min_support=50, max_dispersion=3.0)
    assert "sofa" not in pr["kinds"] and "bed" in pr["kinds"]
    deg = pr["excluded_degenerate"]["sofa"]
    assert deg["n"] == 60 and deg["lo_disp"] > 3.0
    assert pr["meta"]["params"]["max_dispersion"] == 3.0
    # without the gate the same corpus keeps the degenerate band -- the flag is opt-in
    pr2 = kind_priors.derive([d], min_support=50)
    assert "sofa" in pr2["kinds"] and "excluded_degenerate" not in pr2


def test_derive_counts_unlabelled_separately_from_malformed(tmp_path):
    # review finding 2026-07-14: 371k unlabelled Structured3D decor objects were counted as
    # 'malformed', misstating corpus health. Kindless -> unlabelled; bad dims -> malformed;
    # a fully-labelled corpus (FloorPlanCAD shape) emits NO unlabelled key (byte-compat).
    els = _tables() + [{"id": "u1", "x": 0, "y": 0, "w": 500, "d": 500},          # no kind
                       {"id": "m1", "kind": "table", "x": 0, "y": 0, "w": -5, "d": 500}]
    d = _gt(tmp_path, "mix", "mm", els)
    pr = kind_priors.derive([d], min_support=50)
    assert pr["meta"]["n_elements_unlabelled"] == 1
    assert pr["meta"]["n_elements_malformed"] == 1
    (tmp_path / "clean").mkdir()
    d2 = _gt(tmp_path / "clean", "s", "mm", _tables())
    pr2 = kind_priors.derive([d2], min_support=50)
    assert "n_elements_unlabelled" not in pr2["meta"]


def test_cli_flag_without_value_exits_with_usage_not_traceback(tmp_path):
    import pytest
    out = str(tmp_path / "out.json")
    d = _gt(tmp_path, "s", "mm", _tables())
    for argv in (["kind_priors.py", "--derive", out, d, "--source"],
                 ["kind_priors.py", "--derive", out, d, "--max-dispersion"],
                 ["kind_priors.py", "--derive", out, d, "--max-dispersion", "not-a-float"]):
        with pytest.raises(SystemExit):
            kind_priors.main(list(argv))


def test_committed_structured3d_artifact_frozen_constants():
    # frozen pin on the LANDED artifact (mirrors the unit-adoption U7 pattern): the 8 kept
    # kinds, the 5 dispersion-refused kinds, and the bed band that corroborates the v4 read.
    # A silent re-derive that changes any of these must fail the suite, not drift quietly.
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                      "qa", "priors", "kind-priors-structured3d-first3500.json")
    with open(fp, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert doc["schema"] == "interior-ai/kind-priors@0.2"
    assert doc["meta"]["source"] == "structured3d"
    assert sorted(doc["kinds"]) == ["bathtub", "bed", "chair", "desk", "dresser",
                                    "nightstand", "refrigerator", "sink"]
    assert sorted(doc["excluded_degenerate"]) == ["cabinet", "sofa", "table",
                                                  "toilet", "tv_panel"]
    bed = doc["kinds"]["bed"]
    assert bed["n"] == 5481
    assert bed["lo_mm"] == [1444.5, 2511.8] and bed["hi_mm"] == [1950.0, 3015.5]
    # no curve signatures: Structured3D bands are size-only (no reader curve lane ran)
    assert not any("curve" in b for b in doc["kinds"].values())
    # corpus health stated honestly: 371k decor objects are UNLABELLED (by design), 0 malformed
    assert doc["meta"]["n_elements_unlabelled"] == 371059
    assert doc["meta"]["n_elements_malformed"] == 0
    assert doc["meta"]["n_elements_sampled"] == 73346


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
