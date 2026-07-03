#!/usr/bin/env python3
"""test_repair_loop.py — deterministic acceptance for M3.3 (Gates 1-4 + repair loop).

Proves the CONTROL LOGIC with injected stubs — zero API / GPU / Blender / key.
M3.3 acceptance (blueprint §14): a flawed batch is >= 80% auto-resolved within
<= 3 iterations, the rest correctly ESCALATED with a full critique history.
Also pins the scrutiny fixes: the flash->pro tier lever, structure WARN as a
soft pass (not an escalation black hole), structure UNWIRED not blocking, judge
ERROR handled as infra (retry, no wasted render), Gate-0 UNWIRED proceeding
honestly, the repair-directive CONTENT, the knowledge/clients write guard, and
the >=80% boundary (a sub-80% batch must FAIL meets_m33).

Run: python pipeline/scripts/test_repair_loop.py   (prints N/N, exit 0/1)
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repair_loop as R  # noqa: E402


# --------------------------------------------------------------------------- #
# stub factories (each records call counts)                                   #
# --------------------------------------------------------------------------- #
def render_stub():
    calls = {"n": 0, "prompts": []}

    def fn(control, prompt, out, *, tier):
        calls["n"] += 1
        calls["prompts"].append(prompt)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"stub tier={tier}\n")
        return f"stub-{tier}-model"
    return fn, calls


def judge_stub(script):
    """script: list of (overall, verdict) per cycle; last entry repeats."""
    calls = {"n": 0, "tiers": []}

    def fn(candidate, *, tier):
        i = min(calls["n"], len(script) - 1)
        overall, verdict = script[i]
        calls["n"] += 1
        calls["tiers"].append(tier)
        return {"scores": {"styling_and_life": 3, "lighting_quality": 3, "composition": 4},
                "overall_0_5": overall, "verdict": verdict,
                "top_defects": ["cove light uneven", "wood grain repeats"],
                "one_line": "close but not client-ready", "if_client_deliverable": "no",
                "_artifact": os.path.basename(candidate), "_kind": "render", "_model": f"stub-{tier}"}
    return fn, calls


def error_judge():
    calls = {"n": 0}

    def fn(candidate, *, tier):
        calls["n"] += 1
        return {"scores": {}, "overall_0_5": None, "verdict": "ERROR", "top_defects": [],
                "one_line": "critique call failed: RuntimeError", "if_client_deliverable": "",
                "_artifact": os.path.basename(candidate), "_kind": "render", "_model": f"stub-{tier}"}
    return fn, calls


def structure_stub(verdict="PASS", recall=0.95):
    calls = {"n": 0}

    def fn(control, candidate):
        calls["n"] += 1
        return None if verdict is None else (recall, verdict)
    return fn, calls


def brand_stub(status):
    calls = {"n": 0}

    def fn(candidate):
        calls["n"] += 1
        if status is None:
            return None
        return {"status": status, "worst_delta": 3.0, "per_color": [3.0],
                "detail": "worst ΔE00 3.000 vs palette"}
    return fn, calls


def geometry_stub(verdict=R.PASS):
    def fn(spec, spec_path):
        return [{"status": verdict, "check": "gate0_stub", "detail": "stub"}], verdict
    return fn


def _dirs():
    d = tempfile.mkdtemp(prefix="repairloop_test_")
    return d, os.path.join(d, "out"), os.path.join(d, "05_qa")


def _run(stem, judge, render=None, structure=None, brand=None, geometry=None, **kw):
    d, out, qa = _dirs()
    render_fn, _rc = (render if render else render_stub())
    struct_fn, _sc = (structure if structure else structure_stub())
    brand_fn = brand[0] if brand else None
    res = R.repair_loop(
        stem, os.path.join(out, f"room_{stem}.png"), {"room": {"type": stem}}, "spec.json",
        {"room_type": stem}, registry_key="literal test prompt",
        render_fn=render_fn, judge_fn=judge, structure_fn=struct_fn, brand_fn=brand_fn,
        geometry_fn=(geometry or geometry_stub()), outdir=out, qa_dir=qa, **kw)
    return res, d, out, qa


# --------------------------------------------------------------------------- #
# tests                                                                        #
# --------------------------------------------------------------------------- #
def test_resolves_within_cap_and_tier_lever():
    judge, jc = judge_stub([(3.5, "REWORK"), (4.0, "SHIP")])
    res, d, _o, _q = _run("bed", judge)
    try:
        assert res["outcome"] == R.RESOLVED and res["cycles_used"] == 2
        assert res["accepted_cycle"] == 2 and len(res["scorecards"]) == 2
        assert res["history"][0]["tier"] == "flash" and res["history"][1]["tier"] == "pro"
        assert jc["tiers"] == ["flash", "pro"], "flash->pro tier lever must actually switch the judge tier"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_escalates_after_cap_with_history():
    judge, _jc = judge_stub([(3.0, "REWORK")])
    res, d, _o, _q = _run("liv", judge)
    try:
        assert res["outcome"] == R.ESCALATED and res["cycles_used"] == R.MAX_ITERATIONS == 3
        assert len(res["history"]) == 3 and len(res["scorecards"]) == 3
        ptr = res["inbox_pointer"]
        assert ptr and "escalated" in os.path.basename(ptr)
        assert "Unresolved after 3" in open(ptr, encoding="utf-8").read()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cap_never_exceeded():
    judge, jc = judge_stub([(2.0, "NOT_CLIENT_READY")])
    render, rc = render_stub()
    res, d, _o, _q = _run("x", judge, render=(render, rc))
    try:
        assert rc["n"] == 3 and jc["n"] == 3, f"cap breach: {rc['n']} renders"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_fail_fast_structure_blocks_judge():
    judge, jc = judge_stub([(5.0, "SHIP")])       # would pass IF ever called
    struct, sc = structure_stub("FAIL", recall=0.40)
    res, d, _o, _q = _run("drift", judge, structure=(struct, sc))
    try:
        assert res["outcome"] == R.ESCALATED
        assert jc["n"] == 0, "fail-fast: a structure FAIL must NOT spend the judge"
        assert sc["n"] == 3
        for h in res["history"]:
            assert h["blocking_check"] == "camera_structure"
            assert "structure clamp" in h.get("repair_directive", "")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_structure_review_is_soft_pass_and_resolves():
    # SCRUTINY FIX: a REVIEW-tier structure (WARN) must be a soft pass, not an
    # eternal escalation, and must not misroute the repair as a judge failure.
    judge, jc = judge_stub([(4.5, "SHIP")])
    struct, _sc = structure_stub("REVIEW", recall=0.70)
    res, d, _o, _q = _run("rev", judge, structure=(struct, None))
    try:
        assert res["outcome"] == R.RESOLVED and res["cycles_used"] == 1, res["outcome"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_structure_unwired_does_not_block_resolution():
    # SCRUTINY FIX: structure_fn None (numpy/pillow missing) => UNWIRED, which is
    # 'not scored' — it must NOT force wired_pass False forever.
    judge, _jc = judge_stub([(4.5, "SHIP")])
    struct, _sc = structure_stub(verdict=None)
    res, d, _o, _q = _run("uw", judge, structure=(struct, None))
    try:
        assert res["outcome"] == R.RESOLVED and res["cycles_used"] == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_judge_error_escalates_without_burning_renders():
    # SCRUTINY FIX: verdict ERROR = critic infra failure, not a design defect.
    # Retry the critic in-cycle; escalate immediately; never re-render.
    ej, jc = error_judge()
    render, rc = render_stub()
    res, d, _o, _q = _run("err", ej, render=(render, rc))
    try:
        assert res["outcome"] == R.ESCALATED and res["cycles_used"] == 1
        assert rc["n"] == 1, "must not re-render on a judge infra error"
        assert jc["n"] == R.JUDGE_RETRIES, "must retry the critic in-cycle"
        assert "Judge/critic unavailable" in open(res["inbox_pointer"], encoding="utf-8").read()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_brand_fail_blocks_before_judge_and_routes():
    judge, jc = judge_stub([(5.0, "SHIP")])       # would pass IF reached
    brand, bc = brand_stub("FAIL")
    res, d, _o, _q = _run("br", judge, brand=(brand, bc))
    try:
        assert res["outcome"] == R.ESCALATED
        assert jc["n"] == 0, "brand FAIL must fail-fast before the expensive judge"
        assert bc["n"] == 3
        for h in res["history"]:
            assert h["blocking_check"] == "brand_delta_e00"
            assert "palette correction" in h.get("repair_directive", "")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_brand_unwired_when_no_palette_still_resolves():
    judge, _jc = judge_stub([(4.5, "SHIP")])
    res, d, _o, _q = _run("nb", judge)   # brand_fn None
    try:
        assert res["outcome"] == R.RESOLVED
        card = json.load(open(res["scorecards"][0], encoding="utf-8"))
        statuses = {g["check"]: g["status"] for g in card["_gates"]}
        assert statuses["brand_delta_e00"] == R.UNWIRED  # declared, not silent-passed
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_gate0_fail_aborts_spends_nothing():
    judge, jc = judge_stub([(5.0, "SHIP")])
    render, rc = render_stub()
    res, d, _o, _q = _run("bad", judge, render=(render, rc), geometry=geometry_stub(R.FAIL))
    try:
        assert res["outcome"] == R.ABORTED_GATE0
        assert rc["n"] == 0 and jc["n"] == 0 and res["scorecards"] == []
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_gate0_unwired_proceeds_but_flagged_honest():
    # SCRUTINY FIX: an un-run Gate 0 (routing/parse) must NOT read as '0 fail — ok'.
    judge, _jc = judge_stub([(4.5, "SHIP")])
    geo = lambda spec, sp: ([{"status": R.UNWIRED, "check": "gate0_routing", "detail": "x"}], R.UNWIRED)  # noqa: E731
    res, d, _o, _q = _run("g0u", judge, geometry=geo)
    try:
        assert res["outcome"] == R.RESOLVED, "UNWIRED Gate 0 proceeds (upstream-gated)"
        body = open(res["inbox_pointer"], encoding="utf-8").read()
        assert "NOT re-verified" in body and "0 fail — ok" not in body
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_scorecard_is_critique_schema_no_fake_verdict():
    judge, _jc = judge_stub([(4.0, "SHIP")])
    res, d, _o, _q = _run("card", judge)
    try:
        card = json.load(open(res["scorecards"][0], encoding="utf-8"))
        for k in ("scores", "overall_0_5", "verdict", "top_defects", "one_line",
                  "if_client_deliverable", "_artifact", "_kind", "_model"):
            assert k in card, f"missing critique key {k}"
        for k in ("_cycle", "_gates", "_tier_intended", "_model_used", "_wired_pass", "_blocking_check"):
            assert k in card, f"missing repair-extension key {k}"
        statuses = {g["check"]: g["status"] for g in card["_gates"]}
        assert statuses["image_brisque"] == R.UNWIRED and statuses["camera_structure"] == R.PASS
        assert statuses["llm_judge_rubric"] == R.PASS
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_scorecard_verdict_null_when_judge_never_ran():
    # SCRUTINY FIX: a structure fail-fast means the judge never ran -> verdict must
    # be null (not scored), never a fabricated 'REWORK' that reads as a critic call.
    judge, _jc = judge_stub([(5.0, "SHIP")])
    struct, _sc = structure_stub("FAIL", recall=0.3)
    res, d, _o, _q = _run("nj", judge, structure=(struct, None))
    try:
        card = json.load(open(res["scorecards"][0], encoding="utf-8"))
        assert card["verdict"] is None and card["overall_0_5"] is None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_no_silent_pass_structure_fail_overrides_ship_judge():
    judge, _jc = judge_stub([(5.0, "SHIP")])
    struct, _sc = structure_stub("FAIL", recall=0.30)
    res, d, _o, _q = _run("silent", judge, structure=(struct, None))
    try:
        assert res["outcome"] == R.ESCALATED, "a SHIP judge cannot override a wired structure FAIL"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_repair_directive_content():
    # SCRUTINY FIX (untested feature): the §10.1 directive must inject the low-dim
    # DIM_FIX text AND the judge's top_defects into the next cycle's prompt.
    judge, _jc = judge_stub([(3.0, "REWORK"), (3.0, "REWORK")])
    render, rc = render_stub()
    res, d, _o, _q = _run("dir", judge, render=(render, rc))
    try:
        p2 = rc["prompts"][1]  # the cycle-2 prompt carries the repair directive
        assert "REPAIR: FIX" in p2
        assert "signs of life" in p2 or "flat uniform lighting" in p2, "DIM_FIX text missing"
        assert "cove light uneven" in p2, "top_defect not injected"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_guard_dir_refuses_knowledge_and_clients():
    judge, _jc = judge_stub([(5.0, "SHIP")])

    def _refused(sub):
        try:
            R.repair_loop("g", "room_g.png", {"room": {"type": "g"}}, "s.json", {"room_type": "g"},
                          registry_key="lit", render_fn=R._stub_render_fn, judge_fn=judge,
                          structure_fn=R._stub_structure_fn, geometry_fn=R._stub_geometry_fn,
                          outdir=os.path.join(R.ROOT, sub, "x"))
            return False
        except SystemExit:
            return True
    for forbidden in ("knowledge", "clients"):
        assert _refused(forbidden), f"must refuse to write under {forbidden}/"
    # SCRUTINY FIX: on a case-insensitive FS (Windows), case variants land in the
    # same sensitive tree and must ALSO be refused (the guard was case-sensitive).
    if os.path.normcase("A") == "a":
        for variant in ("Clients", "KNOWLEDGE"):
            assert _refused(variant), f"case-insensitive FS: must refuse {variant}/"


def test_make_brand_fn_is_crash_safe():
    # SCRUTINY FIX: the real brand adapter must degrade an unreadable candidate to
    # UNWIRED (None), never raise and kill the batch. Holds whether Pillow is
    # present (UnidentifiedImageError caught) or absent (ImportError caught).
    assert R.make_brand_fn([]) is None                       # empty palette -> not scored
    fn = R.make_brand_fn([(200, 60, 55)])
    assert fn is not None
    d = tempfile.mkdtemp(prefix="brandtest_")
    p = os.path.join(d, "not_an_image.png")
    with open(p, "w", encoding="utf-8") as f:
        f.write("this is text, not a PNG")
    try:
        assert fn(p) is None, "brand_fn must return None on an unreadable candidate, not raise"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_batch_80pct_resolve_meets_m33():
    render, rc = render_stub()
    struct, _sc = structure_stub()
    d, out, qa = _dirs()
    items = _batch_items(out, n_ok=4, n_stuck=1)
    try:
        _results, summary = R.repair_batch(items, registry_key="literal test prompt",
                                           render_fn=render, structure_fn=struct,
                                           geometry_fn=geometry_stub(), outdir=out, qa_dir=qa)
        assert summary["n"] == 5 and summary["resolved"] == 4 and summary["escalated"] == 1
        assert abs(summary["auto_resolve_rate"] - 0.8) < 1e-9
        assert summary["escalations_have_critiques"] is True and summary["meets_m33"] is True
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_batch_below_80pct_fails_m33():
    # SCRUTINY FIX: meets_m33 must be falsifiable at the boundary.
    render, _rc = render_stub()
    struct, _sc = structure_stub()
    d, out, qa = _dirs()
    items = _batch_items(out, n_ok=3, n_stuck=2)  # rate 0.6
    try:
        _results, summary = R.repair_batch(items, registry_key="literal test prompt",
                                           render_fn=render, structure_fn=struct,
                                           geometry_fn=geometry_stub(), outdir=out, qa_dir=qa)
        assert abs(summary["auto_resolve_rate"] - 0.6) < 1e-9
        assert summary["meets_m33"] is False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _batch_items(out, n_ok, n_stuck):
    items = []
    for i in range(n_ok):
        jf, _ = judge_stub([(3.0, "REWORK"), (4.5, "SHIP")])
        items.append({"stem": f"ok{i}", "control_png": os.path.join(out, f"room_ok{i}.png"),
                      "spec": {"room": {"type": f"ok{i}"}}, "spec_path": "s.json",
                      "base_slots": {"room_type": f"ok{i}"}, "judge_fn": jf})
    for i in range(n_stuck):
        jf, _ = judge_stub([(2.5, "NOT_CLIENT_READY")])
        items.append({"stem": f"stuck{i}", "control_png": os.path.join(out, f"room_stuck{i}.png"),
                      "spec": {"room": {"type": f"stuck{i}"}}, "spec_path": "s.json",
                      "base_slots": {"room_type": f"stuck{i}"}, "judge_fn": jf})
    return items


def test_gate_order_is_fail_fast_cheap_first():
    assert R.GATE_ORDER == ["gate1_execution", "gate2_physics", "gate3_client", "gate4_polish"]
    gates = {name: gate for (gate, name, *_r) in R.GATE_STACK}
    assert gates["camera_structure"] == "gate2_physics"
    assert gates["brand_delta_e00"] == "gate3_client" and gates["llm_judge_rubric"] == "gate3_client"


TESTS = [test_resolves_within_cap_and_tier_lever, test_escalates_after_cap_with_history,
         test_cap_never_exceeded, test_fail_fast_structure_blocks_judge,
         test_structure_review_is_soft_pass_and_resolves, test_structure_unwired_does_not_block_resolution,
         test_judge_error_escalates_without_burning_renders, test_brand_fail_blocks_before_judge_and_routes,
         test_brand_unwired_when_no_palette_still_resolves, test_gate0_fail_aborts_spends_nothing,
         test_gate0_unwired_proceeds_but_flagged_honest, test_scorecard_is_critique_schema_no_fake_verdict,
         test_scorecard_verdict_null_when_judge_never_ran, test_no_silent_pass_structure_fail_overrides_ship_judge,
         test_repair_directive_content, test_guard_dir_refuses_knowledge_and_clients,
         test_make_brand_fn_is_crash_safe, test_batch_80pct_resolve_meets_m33,
         test_batch_below_80pct_fails_m33, test_gate_order_is_fail_fast_cheap_first]


def main():
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
