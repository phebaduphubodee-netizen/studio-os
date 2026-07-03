#!/usr/bin/env python3
"""repair_loop.py — M3.3 Gates 1-4 + closed-loop critique & repair (SCAFFOLD).

Wires the vision feedback loop (blueprint §10.1) on top of the sequential gate
logic (§9.5): a rendered beauty pass is scored through Gates 1-4 fail-fast
(cheap→expensive), a FAIL drives a *targeted* re-render (minimal slot edit, never
a wholesale prompt rewrite — §10.1 step 4), and the loop caps at
`repair_loop.max_iterations` (qa/thresholds.yaml = 3). Unresolved-after-cap →
human triage in <project>/05_qa/_inbox/ with the full critique history attached.

DESIGN — why this is a scaffold, not a finished gate stack:
- The CONTROL STRUCTURE is real and deterministically tested (test_repair_loop.py):
  gate ordering, fail-fast (per-check), the 3-cycle cap, repair-directive
  synthesis, escalation, per-cycle scorecards, judge-infra handling.
- The VALIDATORS are injected. Wired for real today: Gate 0 clearance, Gate 1
  image sanity (image_sanity.py — deterministic blur/exposure/blank), Gate 2
  camera/structure (overlay_fidelity), Gate 3 LLM judge (critique.py) and Gate 3
  brand ΔE00 (delta_e00.py, when a brand palette is supplied). Still UNWIRED:
  Soft-TIFA, material albedo/metalness, lighting triangulation, consistency warp,
  revision LPIPS — declared, never silent-passed. (BRISQUE deliberately deferred
  in favour of image_sanity — see memory 'brisque-deferred'.)
- HONESTY DOCTRINE (carried from qa-report / suite_clearance): an UNWIRED gate is
  NEVER a silent pass, and it never BLOCKS resolution either — it is simply "not
  scored". Auto-resolve rests only on the wired validators that actually RAN
  (PASS/WARN); every RESOLVED result still routes to the human _inbox for
  per-image approval, the standing backstop for the unscored dimensions. WARN is
  a soft pass (§9.3) — it flags but does not block or trigger a repair.

INJECTION (so the loop is testable without API / GPU / Blender / a key):
    render_fn(control_png, prompt, out_png, *, tier) -> model_id str | True | False
    judge_fn(candidate_png, *, tier)                 -> critique dict
    structure_fn(control_png, candidate_png)         -> (recall, verdict) | None
    geometry_fn(spec, spec_path)                     -> (results, verdict)
    brand_fn(candidate_png)                          -> brand result dict | None   (optional)
Real adapters (lazy-imported so importing this module never needs a key/numpy)
are wired by default in main(); the test injects deterministic stubs.

COST: the real render_fn dispatches a PAID Gemini image call (~$0.04 flash /
~$0.13-0.25 pro per image) and the real judge_fn a paid vision call. Ask-tier —
run it deliberately. `--dry-run` exercises the whole control flow with stub
render+judge and spends nothing.

Blueprint: §9.5 (gate order), §9.3 (fail actions + thresholds), §10.1 (5-step
loop, cap 3), §9.4 (the judge must be M3.2-calibrated before it is trusted to
gate — see judge_calibrate.py; until PASS, a judge verdict is advisory).
"""
import json
import os
import sys
from datetime import date

# Windows console is cp1252 and cannot encode the report glyphs (→, ΔE); the same
# guard judge_calibrate.py / discord_ingest.py use.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# --- thresholds (qa/thresholds.yaml is the PR-controlled source of truth; these
# mirror it, the same hardcode-with-citation pattern judge_calibrate.py uses). ---
MAX_ITERATIONS = 3       # qa/thresholds.yaml repair_loop.max_iterations
JUDGE_PASS_BOUND = 4.0   # qa/thresholds.yaml client_qa.judge_score.pass_min (scale 5)
JUDGE_RETRIES = 3        # in-cycle retries when the critic itself errors (infra, not design)
PRO_IMAGE_MODEL = "gemini-3-pro-image-preview"  # the evidenced 4->5 photoreal lever

# status vocab (aligned with clearance_check / suite_clearance / overlay_fidelity)
PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"
# terminal outcomes
RESOLVED, ESCALATED, ABORTED_GATE0 = "RESOLVED", "ESCALATED", "ABORTED_GATE0"

# The gate stack (blueprint §9.5 order, §9.3 fail actions). `wired` = a real
# validator can run in-repo today; a wired check whose validator is unavailable
# at runtime records status UNWIRED (not scored) — never a silent pass.
# fmt: off
GATE_STACK = [
    # gate,            check,                       wired, fail_action
    ("gate1_execution", "image_sanity",             True,  "reseed_regenerate"),
    ("gate1_execution", "prompt_soft_tifa",         False, "reseed_regenerate"),
    ("gate2_physics",   "camera_structure",         True,  "reject_layout_drift"),
    ("gate2_physics",   "lighting_triangulation",   False, "relight"),
    ("gate2_physics",   "material_albedo_metalness", False, "material_repair"),
    ("gate3_client",    "brand_delta_e00",          True,  "correct_palette"),
    ("gate3_client",    "llm_judge_rubric",         True,  "prompt_augment_regenerate"),
    ("gate4_polish",    "consistency_warp",         False, "rerender_frames"),
    ("gate4_polish",    "revision_lpips",           False, "background_clamp"),
]
# fmt: on
GATE_ORDER = ["gate1_execution", "gate2_physics", "gate3_client", "gate4_polish"]

# A low judge dimension -> a concrete corrective directive (§10.1 step 4, minimal).
DIM_FIX = {
    "furniture_realism": "replace primitive/boxy furniture with realistic modeled pieces; correct proportions",
    "room_context": "anchor the subject in a complete room shell — no floating objects or void backgrounds",
    "lighting_quality": "layer the light rig (key/fill/practical); kill flat uniform lighting",
    "styling_and_life": "add tasteful styling and signs of life (textiles, plants, books, decor)",
    "photoreal_believability": "raise material/render fidelity; remove CG tells (see tier bump)",
    "palette_coherence": "unify the palette to the material_story; drop clashing hues",
    "composition": "improve framing and foreground depth per the camera brief",
    "proportion_and_scale": "correct object scale relative to human and room dimensions",
}


# --------------------------------------------------------------------------- #
# Gate evaluation                                                             #
# --------------------------------------------------------------------------- #
def _check(gate, name, wired, action, status, detail):
    return {"gate": gate, "check": name, "wired": wired,
            "status": status, "fail_action": action, "detail": detail}


def run_render_gates(candidate_png, control_png, ctx):
    """Run Gates 1-4 on one rendered candidate, fail-fast per-check.

    Returns {checks[], blocking_gate, blocking_check, wired_pass, judge,
    structure, brand, judge_error}. Once ANY wired check FAILs we stop — later
    checks/gates (incl. the expensive judge) are not spent. UNWIRED and WARN
    never stop the sequence; UNWIRED never counts toward a pass, WARN is a soft
    pass. `judge_error` = the critic itself failed after retries (infra, not a
    design defect) — the loop escalates without burning more renders.
    """
    checks = []
    judge = structure = brand = sanity = None
    blocking_gate = blocking_check = None
    judge_error = False

    for gate in GATE_ORDER:
        for (_g, name, wired, action) in [c for c in GATE_STACK if c[0] == gate]:
            if not wired:
                checks.append(_check(gate, name, wired, action, UNWIRED,
                                     "no validator wired (Phase 3) — not scored, not passed"))
                continue
            if name == "image_sanity":
                sanity = ctx["sanity_fn"](candidate_png) if ctx.get("sanity_fn") else None
                if sanity is None:
                    checks.append(_check(gate, name, wired, action, UNWIRED,
                                         "sanity validator unavailable (Pillow missing / no fn) — not scored"))
                else:
                    checks.append(_check(gate, name, wired, action, sanity["status"], sanity["detail"]))
            elif name == "camera_structure":
                structure = ctx["structure_fn"](control_png, candidate_png)
                if structure is None:
                    checks.append(_check(gate, name, wired, action, UNWIRED,
                                         "structure validator unavailable (numpy/pillow or control missing) — not scored"))
                else:
                    recall, verdict = structure
                    status = PASS if verdict == "PASS" else (WARN if verdict == "REVIEW" else FAIL)
                    checks.append(_check(gate, name, wired, action, status,
                                         f"structure recall {recall:.2f} -> {verdict} "
                                         f"(scene-dependent; the RED overlay is the human verdict)"))
            elif name == "brand_delta_e00":
                brand = ctx["brand_fn"](candidate_png) if ctx.get("brand_fn") else None
                if not brand or brand.get("status") is None:
                    checks.append(_check(gate, name, wired, action, UNWIRED,
                                         "no brand palette supplied — not scored"))
                else:
                    checks.append(_check(gate, name, wired, action, brand["status"], brand["detail"]))
            elif name == "llm_judge_rubric":
                judge = _judge_with_retry(ctx["judge_fn"], candidate_png, ctx["tier"])
                overall, verdict = judge.get("overall_0_5"), judge.get("verdict")
                if verdict == "ERROR" or overall is None:
                    judge_error = True
                    checks.append(_check(gate, name, wired, action, FAIL,
                                         f"judge unavailable after {JUDGE_RETRIES} retries "
                                         f"({judge.get('one_line', 'critic call failed')}) — infra, not design"))
                else:
                    ok = overall >= JUDGE_PASS_BOUND and verdict == "SHIP"
                    checks.append(_check(gate, name, wired, action, PASS if ok else FAIL,
                                         f"judge {overall}/5 verdict={verdict} "
                                         f"(pass = >= {JUDGE_PASS_BOUND} AND SHIP)"))
            # per-check fail-fast: stop the moment a WIRED check FAILs
            if checks[-1]["status"] == FAIL and checks[-1]["wired"]:
                blocking_gate, blocking_check = gate, name
                break
        if blocking_gate:
            break

    decisive = [c for c in checks if c["wired"] and c["status"] in (PASS, WARN, FAIL)]
    wired_pass = (blocking_gate is None) and bool(decisive) and all(c["status"] != FAIL for c in decisive)
    return {"checks": checks, "blocking_gate": blocking_gate, "blocking_check": blocking_check,
            "wired_pass": wired_pass, "judge": judge, "structure": structure,
            "brand": brand, "sanity": sanity, "judge_error": judge_error}


def _judge_with_retry(judge_fn, candidate, tier):
    """Retry the critic on the SAME candidate when it returns ERROR (infra), so a
    transient Gemini failure never masquerades as a design defect / re-render."""
    result = None
    for _ in range(JUDGE_RETRIES):
        result = judge_fn(candidate, tier=tier)
        if result.get("verdict") != "ERROR" and result.get("overall_0_5") is not None:
            return result
    return result


# --------------------------------------------------------------------------- #
# Repair-directive synthesis (§10.1 step 4 — targeted, minimal)               #
# --------------------------------------------------------------------------- #
def build_repair_directive(gate_result, slots, tier):
    """From the BLOCKING check's evidence, produce (new_slots, new_tier, note).

    Keyed on the specific failing check (not a judge fallthrough): structure ->
    layout clamp; brand -> palette correction; judge -> tier bump (the evidenced
    flash->pro 4->5 lever) + low-dimension/defect FIX directives. Minimal edits:
    append 'FIX' text to the style_brief slot; never rewrite the base prompt.
    """
    fixes, note, new_tier = [], "", tier
    check = gate_result["blocking_check"]

    if check == "image_sanity":
        # Gate 1 EXECUTION fail = degenerate raw output. A fresh Gemini roll on the
        # same prompt IS the reseed (§9.5 'discard, reseed') — no slot/tier edit.
        s = gate_result.get("sanity") or {}
        note = f"regenerate — raw output failed image sanity ({s.get('detail', '')})"
    elif check == "camera_structure":
        fixes.append("keep the EXACT wall and furniture layout of the control image; "
                     "do not move, resize, add, or remove anything")
        note = "structure clamp (layout drift)"
    elif check == "brand_delta_e00" and gate_result["brand"]:
        targets = gate_result["brand"].get("palette_rgb")
        hexes = ", ".join("#%02X%02X%02X" % tuple(c) for c in targets) if targets else "the approved palette"
        fixes.append(f"shift the off-brand colours toward the approved brand palette [{hexes}] "
                     f"({gate_result['brand']['detail']})")
        note = "palette correction (brand ΔE00)"
    elif check == "llm_judge_rubric" and gate_result["judge"]:
        judge = gate_result["judge"]
        low = sorted((k for k, v in (judge.get("scores") or {}).items()
                      if isinstance(v, (int, float)) and v <= 3),
                     key=lambda k: judge["scores"][k])
        for dim in low:
            if dim in DIM_FIX:
                fixes.append(DIM_FIX[dim])
        for d in (judge.get("top_defects") or [])[:4]:
            fixes.append(str(d))
        if not fixes and judge.get("one_line"):
            fixes.append(judge["one_line"])
        if tier != "pro":                       # bump the image tier before prose churn
            new_tier, note = "pro", "judge fail — tier flash->pro (4->5 lever) + FIX directives"
        else:
            note = "judge fail — FIX directives (already pro tier)"
    else:
        note = "no actionable directive (unwired-only state — should not reach a repair)"

    new_slots = dict(slots)
    if fixes:
        base = slots.get("style_brief", "")
        suffix = " | REPAIR: " + "; ".join(f"FIX {f}" for f in fixes)
        new_slots["style_brief"] = (base + suffix).strip(" |")
    return new_slots, new_tier, note


# --------------------------------------------------------------------------- #
# Scorecards + escalation                                                      #
# --------------------------------------------------------------------------- #
def _scorecard(candidate_png, cycle, gate_result, tier, model_used):
    """Per-cycle scorecard in the critique.py schema (so qa-report globs it) plus
    repair-provenance extension keys. When the judge did not run (a cheaper gate
    fail-fasted), verdict/overall are null = 'not scored' — never a fake REWORK."""
    judge = gate_result["judge"] or {}
    return {
        "scores": judge.get("scores", {}),
        "overall_0_5": judge.get("overall_0_5"),
        "verdict": judge.get("verdict"),          # None if the judge never ran (honest 'not scored')
        "top_defects": judge.get("top_defects", []),
        "one_line": judge.get("one_line", ""),
        "if_client_deliverable": judge.get("if_client_deliverable", ""),
        "_artifact": os.path.basename(candidate_png),
        "_kind": "render",
        "_model": judge.get("_model", "n/a"),
        # --- repair-loop extension (qa-report ignores unknown keys) ---
        "_cycle": cycle,
        "_tier_intended": tier,
        "_model_used": model_used,                # the model the render ACTUALLY used (provenance)
        "_gates": [{"gate": c["gate"], "check": c["check"], "status": c["status"]} for c in gate_result["checks"]],
        "_blocking_check": gate_result["blocking_check"],
        "_wired_pass": gate_result["wired_pass"],
    }


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    return path


def _write_inbox(qa_dir, stem, candidate, kind, history, scorecards, geo_verdict, geo_results, reason=""):
    """Human-gate pointer into 05_qa/_inbox/ (blueprint §11.3). READY = wired
    gates passed, awaiting per-image approval; ESCALATED = unresolved after the
    cap (or judge infra down), full critique history attached. Writes markdown +
    references the scorecard JSON; image binaries live in assets/ under LFS."""
    inbox = os.path.join(qa_dir, "_inbox")
    os.makedirs(inbox, exist_ok=True)
    lines = [f"# {kind}: {stem}", "", f"generated {date.today()} by repair_loop.py (M3.3)", ""]
    if reason:
        lines += [f"> {reason}", ""]
    if kind == "READY":
        lines += [f"Wired gates PASSED at cycle {history[-1]['cycle']}. "
                  f"Candidate: `{os.path.basename(candidate)}`.", "",
                  "**Human approval required** — the UNWIRED gates (BRISQUE, Soft-TIFA, material, "
                  "lighting, consistency, revision — and brand ΔE00 if no palette was supplied) are "
                  "NOT scored; you are the backstop for those dimensions. Approve or send back.", ""]
    else:
        lines += [f"**Unresolved after {len(history)} cycle(s)** — routed to human triage "
                  f"per blueprint §10.1. Full critique history below.", ""]
    lines += ["## Cycle history", ""]
    for h in history:
        lines.append(f"- cycle {h.get('cycle', '?')} [{h.get('tier', '?')}"
                     f"{'' if not h.get('model_used') else '/' + str(h['model_used'])}]: "
                     f"overall={h.get('overall_0_5')} verdict={h.get('verdict')} "
                     f"blocking={h.get('blocking_check')} repair={h.get('repair_directive', '-')}")
    lines += ["", "## Scorecards", ""] + [f"- `{os.path.relpath(s, ROOT)}`" for s in scorecards]
    # Gate 0 line — honest about UNWIRED (never render an un-run precondition as 'ok')
    if geo_verdict == UNWIRED:
        g0 = "NOT re-verified in-loop (routing/parse) — relies on the upstream make_all Gate-0 pass"
    else:
        n_fail = sum(1 for r in (geo_results or []) if r.get("status") == FAIL)
        g0 = f"{geo_verdict} ({n_fail} fail)"
    lines += ["", f"## Gate 0 (geometry): {g0}"]
    path = os.path.join(inbox, f"{kind.lower()}_{stem}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------------- #
# The loop                                                                     #
# --------------------------------------------------------------------------- #
def repair_loop(stem, control_png, spec, spec_path, base_slots, *,
                render_fn, judge_fn, structure_fn, geometry_fn, brand_fn=None, sanity_fn=None,
                registry_key="@render-hybrid", outdir=None, qa_dir=None,
                tier="flash", max_iterations=MAX_ITERATIONS):
    """Run the closed-loop repair on one artifact. Injected fns keep it testable.
    Returns a LoopResult dict."""
    outdir = _guard_dir(outdir or os.path.join(ROOT, "pipeline", "output"))
    qa_dir = _guard_dir(qa_dir or os.path.join(outdir, "05_qa"))
    os.makedirs(outdir, exist_ok=True)   # real render_fn writes candidates here (edit() also mkdirs; stubs mkdir)
    slots = _seed_registry_defaults(registry_key, base_slots)

    def _result(outcome, cycle, cand, hist, cards, ptr, geo):
        return {"stem": stem, "outcome": outcome, "cycles_used": cycle,
                "accepted_cycle": cycle if outcome == RESOLVED else None,
                "scorecards": cards, "history": hist, "final_candidate": cand,
                "inbox_pointer": ptr, "gate0_verdict": geo}

    # Gate 0 precondition — geometry is a SPEC property (make_all already gated it
    # upstream); re-verify defensively and refuse to burn renders on an unbuildable
    # spec. UNWIRED (routing/parse) is NOT a pass — it proceeds (upstream held) but
    # is recorded honestly in the inbox, never as '0 fail — ok'.
    geo_results, geo_verdict = geometry_fn(spec, spec_path)
    if geo_verdict == FAIL:
        return _result(ABORTED_GATE0, 0, None, [{"gate0": FAIL, "results": geo_results,
                       "detail": "spec unbuildable — fix Gate 0, not the render"}], [], None, geo_verdict)

    scorecards, history, cur_tier = [], [], tier
    for cycle in range(1, max_iterations + 1):
        candidate = os.path.join(outdir, f"repaircand_{stem}_roll{cycle}.png")
        rendered = render_fn(control_png, ctx_prompt(registry_key, slots), candidate, tier=cur_tier)
        if not rendered:
            history.append({"cycle": cycle, "tier": cur_tier, "event": "render_failed"})
            continue
        model_used = rendered if isinstance(rendered, str) else None

        gate_result = run_render_gates(candidate, control_png, {
            "sanity_fn": sanity_fn, "structure_fn": structure_fn, "judge_fn": judge_fn,
            "brand_fn": brand_fn, "tier": cur_tier})
        card_path = _write_json(os.path.join(qa_dir, f"scorecard_{stem}_roll{cycle}.json"),
                                _scorecard(candidate, cycle, gate_result, cur_tier, model_used))
        scorecards.append(card_path)
        history.append({"cycle": cycle, "tier": cur_tier, "model_used": model_used,
                        "blocking_check": gate_result["blocking_check"],
                        "wired_pass": gate_result["wired_pass"],
                        "overall_0_5": (gate_result["judge"] or {}).get("overall_0_5"),
                        "verdict": (gate_result["judge"] or {}).get("verdict"),
                        "gates": [{"g": c["gate"], "c": c["check"], "s": c["status"]} for c in gate_result["checks"]]})

        if gate_result["wired_pass"]:
            ptr = _write_inbox(qa_dir, stem, candidate, "READY", history, scorecards, geo_verdict, geo_results)
            return _result(RESOLVED, cycle, candidate, history, scorecards, ptr, geo_verdict)

        if gate_result["judge_error"]:  # critic infra down — escalate, do NOT burn more renders
            history[-1]["repair_directive"] = "judge unavailable (infra)"
            ptr = _write_inbox(qa_dir, stem, None, "ESCALATED", history, scorecards, geo_verdict, geo_results,
                               reason="Judge/critic unavailable after retries — not a design defect. "
                                      "Fix the critic (GEMINI key/quota/network) and re-run; no renders wasted.")
            return _result(ESCALATED, cycle, None, history, scorecards, ptr, geo_verdict)

        slots, cur_tier, note = build_repair_directive(gate_result, slots, cur_tier)
        history[-1]["repair_directive"] = note

    ptr = _write_inbox(qa_dir, stem, None, "ESCALATED", history, scorecards, geo_verdict, geo_results)
    return _result(ESCALATED, max_iterations, None, history, scorecards, ptr, geo_verdict)


def ctx_prompt(registry_key, slots):
    """Resolve a '@' registry key -> compiled prompt (lazy-imports hybrid_render,
    which reads local registry JSON only — no API). A key not starting with '@'
    is literal prose (dry-run / tests), with the current style_brief appended."""
    if not registry_key.startswith("@"):
        sb = slots.get("style_brief", "")
        return registry_key + (" | " + sb if sb else "")
    import hybrid_render
    return hybrid_render.resolve_prompt(registry_key, slots)


def _seed_registry_defaults(registry_key, base_slots):
    """Seed base_slots with the registry version's default slot values so a repair
    APPENDS to the real base style_brief instead of overwriting it. Caller's slots
    (e.g. room_type) win. Literal keys / read failures pass base_slots through."""
    if not registry_key.startswith("@"):
        return dict(base_slots)
    try:
        import hybrid_render
        parts = registry_key.lstrip("@").split("@")
        intent, label = parts[0], (parts[1] if len(parts) > 1 else "staging")
        d = hybrid_render.REGISTRY / intent
        labels = json.loads((d / "labels.json").read_text(encoding="utf-8"))
        payload = json.loads((d / f"{labels[label]}.json").read_text(encoding="utf-8"))
        seeded = dict(payload.get("defaults", {}))
        seeded.update(base_slots)
        return seeded
    except Exception:
        return dict(base_slots)


def _guard_dir(path):
    """Hard boundary (root CLAUDE.md): generation/render tasks never write into
    knowledge/ or clients/. normcase folds Windows case-insensitivity and / vs \\
    so a variant like 'Clients/' or 'KNOWLEDGE/' cannot slip past the boundary on
    the (case-insensitive) deployment filesystem."""
    ap = os.path.normcase(os.path.abspath(path))
    for forbidden in ("knowledge", "clients"):
        forb = os.path.normcase(os.path.abspath(os.path.join(ROOT, forbidden)))
        if ap == forb or ap.startswith(forb + os.sep):
            raise SystemExit(f"refusing to write under {forbidden}/ (hard boundary): {path}")
    return path


def repair_batch(items, **kw):
    """Run repair_loop over a batch (the M3.3 acceptance unit). Summary reports
    the auto-resolve rate vs the >= 80% bound; 'correctly escalated with critiques'
    means every escalated item carries at least one scorecard."""
    results = [repair_loop(**{**it, **kw}) for it in items]
    n = len(results)
    resolved = [r for r in results if r["outcome"] == RESOLVED]
    escalated = [r for r in results if r["outcome"] == ESCALATED]
    aborted = [r for r in results if r["outcome"] == ABORTED_GATE0]
    rate = len(resolved) / n if n else 0.0
    escalations_have_critiques = all(r["scorecards"] for r in escalated)
    summary = {"n": n, "resolved": len(resolved), "escalated": len(escalated),
               "aborted_gate0": len(aborted), "auto_resolve_rate": rate,
               "escalations_have_critiques": escalations_have_critiques,
               "meets_m33": rate >= 0.80 and escalations_have_critiques}
    return results, summary


# --------------------------------------------------------------------------- #
# Real adapters (lazy — importing this module never needs a key/numpy/rules)   #
# --------------------------------------------------------------------------- #
def _real_render_fn(control, prompt, out, *, tier):
    """Call-time model selection (no import-time env capture) — the pro image
    model is genuinely tried first when tier=='pro'. Returns the model id used."""
    import hybrid_render
    return hybrid_render.edit(control, prompt, out, prefer=(PRO_IMAGE_MODEL if tier == "pro" else None))


def _real_judge_fn(candidate, *, tier):
    import critique  # hard-exits at import if GEMINI_API_KEY unset — real path only
    return critique.run_batch([candidate], kind="render",
                              model_key="pro" if tier == "pro" else "flash")[0]


def _real_structure_fn(control, candidate):
    if not (control and os.path.exists(control) and os.path.exists(candidate)):
        return None
    try:  # a missing dep OR an unreadable candidate degrades to UNWIRED, never crashes the loop
        import overlay_fidelity  # sys.exit at import if numpy/pillow missing
        recall, _prec, verdict, _png = overlay_fidelity.check(control, candidate)
        return (recall, verdict)
    except (SystemExit, Exception):  # noqa: BLE001
        return None


def _real_geometry_fn(spec, spec_path):
    """Route metric @0.2 -> suite_clearance, inch @0.1 -> clearance_check. Any
    parse/routing failure degrades to UNWIRED (not scored), never a crash."""
    room = spec.get("room") or {}
    is_metric = ("outline_mm" in room) or ("@0.2" in spec.get("schema", "")) or (spec.get("units") == "metric")
    try:
        if is_metric:
            import suite_clearance
            return suite_clearance.report(spec)   # (res, verdict) verdict in PASS/REVIEW/FAIL
        import clearance_check
        room_o, items, _spec = clearance_check.load_spec(spec_path)
        res = clearance_check.check(room_o, items)
        fails = sum(1 for r in res if r["status"] == FAIL)
        warns = sum(1 for r in res if r["status"] == WARN)
        return res, (FAIL if fails else ("REVIEW" if warns else PASS))  # REVIEW vocab, matches metric route
    except (SystemExit, Exception) as e:  # noqa: BLE001 — precondition must never crash the loop
        return [{"status": UNWIRED, "check": "gate0_routing", "detail": str(e)}], UNWIRED


def _real_sanity_fn(candidate):
    """Gate 1 image-execution check — deterministic, no model. image_sanity
    returns None (UNWIRED) on missing Pillow / an unreadable candidate."""
    import image_sanity
    return image_sanity.sanity_of_image(candidate)


def make_brand_fn(palette_rgb, sample_k=6):
    """Build a Gate-3 brand ΔE00 check from an approved palette (list of sRGB
    triples). Samples the candidate's dominant colours (Pillow) and scores each
    against the palette via delta_e00. Returns None if Pillow is missing OR the
    palette is empty -> the gate reads UNWIRED (not scored), never silent-pass."""
    if not palette_rgb:
        return None
    import delta_e00
    palette_lab = [delta_e00.srgb_to_lab(c) for c in palette_rgb]

    def brand_fn(candidate):
        try:  # missing Pillow OR an unreadable candidate -> UNWIRED (None), never a crash
            from PIL import Image
            im = Image.open(candidate).convert("RGB").resize((160, 160))
            pal = im.convert("P", palette=Image.ADAPTIVE, colors=sample_k).convert("RGB")
            colors = [c for _n, c in sorted(pal.getcolors(sample_k * 4) or [], reverse=True)[:sample_k]]
            sampled_lab = [delta_e00.srgb_to_lab(c) for c in colors]
            result = delta_e00.brand_compliance(sampled_lab, palette_lab)
            result["palette_rgb"] = palette_rgb   # so the repair directive can name the target colours
            return result
        except Exception:  # noqa: BLE001
            return None
    return brand_fn


def _hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# --------------------------------------------------------------------------- #
# Dry-run stubs (control-flow smoke test with zero spend)                      #
# --------------------------------------------------------------------------- #
def _stub_render_fn(control, prompt, out, *, tier):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"stub render tier={tier}\n")
    return f"stub-{tier}-model"


def _stub_sanity_fn(candidate):
    return {"status": PASS, "checks": [], "detail": "dry-run sanity PASS", "metrics": {}}


def _stub_structure_fn(control, candidate):
    return (0.95, "PASS")


def _stub_geometry_fn(spec, spec_path):
    return [{"status": PASS, "check": "gate0_stub", "detail": "dry-run"}], PASS


def _make_stub_judge(script):
    state = {"i": 0}

    def judge(candidate, *, tier):
        overall, verdict = script[min(state["i"], len(script) - 1)]
        state["i"] += 1
        return {"scores": {"styling_and_life": 3, "lighting_quality": 3}, "overall_0_5": overall,
                "verdict": verdict, "top_defects": ["cove light uneven", "wood grain repeats"],
                "one_line": "close but not client-ready", "if_client_deliverable": "no",
                "_artifact": os.path.basename(candidate), "_kind": "render", "_model": f"stub-{tier}"}
    return judge


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="M3.3 Gates 1-4 + repair loop")
    ap.add_argument("clay", help="clay STRUCTURAL CONTROL png (from build_room / make_all)")
    ap.add_argument("spec", help="room spec json (Gate 0 precondition)")
    ap.add_argument("registry_key", nargs="?", default="@render-hybrid",
                    help="prompt registry ref, e.g. @render-hybrid@production")
    ap.add_argument("--room-type", default=None, help="required slot if not in spec.room.type")
    ap.add_argument("--pro", action="store_true", help="start on the pro image tier")
    ap.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--qa-dir", default=None, help="project 05_qa/ dir for scorecards + _inbox")
    ap.add_argument("--brand-palette", default=None,
                    help="approved brand colours as comma-separated hex (e.g. '#C83C37,#2A2A2A') "
                         "— wires the Gate 3 brand ΔE00 check; omit and brand reads UNWIRED")
    ap.add_argument("--dry-run", action="store_true",
                    help="stub render+judge (zero spend) to exercise the control flow")
    args = ap.parse_args(argv)

    spec = json.load(open(args.spec, encoding="utf-8"))
    room_type = args.room_type or (spec.get("room") or {}).get("type")
    if not room_type:
        sys.exit("ERROR: room_type required (spec.room.type missing) — pass --room-type")
    stem = os.path.splitext(os.path.basename(args.clay))[0].replace("room_", "")
    base_slots = {"room_type": room_type}

    if args.dry_run:
        fns = dict(render_fn=_stub_render_fn, structure_fn=_stub_structure_fn, geometry_fn=_stub_geometry_fn,
                   sanity_fn=_stub_sanity_fn, judge_fn=_make_stub_judge([(3.5, "REWORK"), (4.0, "SHIP")]))
        registry_key = "literal dry-run prompt"  # bypass registry (no '@')
    else:
        print("repair_loop: PAID render/judge dispatch (ask-tier). Ctrl-C to abort.", file=sys.stderr)
        brand_fn = None
        if args.brand_palette:
            palette = [_hex_to_rgb(h) for h in args.brand_palette.split(",") if h.strip()]
            brand_fn = make_brand_fn(palette)
        fns = dict(render_fn=_real_render_fn, judge_fn=_real_judge_fn, structure_fn=_real_structure_fn,
                   geometry_fn=_real_geometry_fn, brand_fn=brand_fn, sanity_fn=_real_sanity_fn)
        registry_key = args.registry_key

    result = repair_loop(stem, args.clay, spec, args.spec, base_slots,
                         registry_key=registry_key, outdir=args.outdir, qa_dir=args.qa_dir,
                         tier="pro" if args.pro else "flash", max_iterations=args.max_iterations, **fns)

    print(f"\n=== repair_loop: {stem} ===")
    print(f"outcome        : {result['outcome']}")
    print(f"cycles used    : {result['cycles_used']} / {args.max_iterations}")
    print(f"gate0          : {result['gate0_verdict']}")
    if result["accepted_cycle"]:
        print(f"accepted cycle : {result['accepted_cycle']}  -> {os.path.basename(result['final_candidate'])}")
    for h in result["history"]:
        print(f"  cycle {h.get('cycle', '?')} [{h.get('tier', '?')}]: overall={h.get('overall_0_5')} "
              f"verdict={h.get('verdict')} blocking={h.get('blocking_check')} repair={h.get('repair_directive', '-')}")
    if result["inbox_pointer"]:
        print(f"inbox          : {os.path.relpath(result['inbox_pointer'], ROOT)}")
    print("\nNOTE: unwired gates are NOT scored — a RESOLVED result still needs human approval per image.")
    sys.exit(0 if result["outcome"] == RESOLVED else (2 if result["outcome"] == ABORTED_GATE0 else 1))


if __name__ == "__main__":
    main(sys.argv[1:])
