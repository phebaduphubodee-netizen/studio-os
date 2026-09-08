#!/usr/bin/env python3
"""experiment_3leg.py — the materialized-render A/B/C experiment driver (2026-07-14).

THE QUESTION (owner direction): move material+lighting design authority fully into the
spec (deterministic, ours) and narrow Gemini to a finishing pass — does the result beat
the current clay+full-repaint pipeline?

THE LEGS (one room, one camera):
  A = current pipeline baseline: hardcoded-palette Cycles control + render-hybrid@v004
      full repaint (EXISTING artifacts — no re-spend; e.g. R_PRJ002_SittingRoom_Cam01_v01)
  B = spec-materialized Cycles render + render-polish@v001 (photographic finishing only)
  C = spec-materialized Cycles render, untouched (no Gemini)

INSTRUMENTS (all call-site — qa/thresholds.yaml is PR-only and is NOT edited):
  - image_sanity per leg (deterministic Gate-1 floor)
  - overlay_fidelity B-vs-C: recall bound tightened to --recall-min (default 0.90 vs the
    wired DRAFT 0.80) because render-polish grants NO decor licence; precision reported
    (informational — texture drags it down by design, overlay_fidelity.py:16-18)
  - ΔE00 dominant-colour B-vs-C BOTH directions = the material-preservation instrument
    (brand_compliance is nearest-match asymmetric, so one direction alone can hide a
    swap); C-vs-A is reported too (how far the FF&E-true palette moved from the old look)
  - critique multi-roll MEANS (judge single-roll variance ±0.5 — render-hybrid
    labels.json _v005_evidence). The judge is UNCALIBRATED (M3.2): ADVISORY, never a gate.

MONEY: critique rolls and --make-leg-b are PAID Gemini calls — both default OFF and only
run when explicitly flagged. Everything else is free and deterministic.

Usage:
  python experiment_3leg.py --spec SPEC.json --leg-a A.png --leg-c C.png
      [--leg-b B.png | --make-leg-b] [--baseline-critique existing_critique.json]
      [--rolls N] [--model pro|flash] [--recall-min 0.90] --out DIR
"""
import argparse
import json
import os
import sys
import time

import material_presets

LEG_DESC = {
    "A": "baseline: hardcoded-palette control + render-hybrid@v004 full repaint",
    "B": "spec-materialized Cycles + render-polish@v001 finishing pass",
    "C": "spec-materialized Cycles, no Gemini",
}


# ---------------------------------------------------------------------------
# pure helpers (unit-tested without Pillow/numpy/network)
# ---------------------------------------------------------------------------

def summarize_rolls(rolls):
    """Mean per-dimension + mean overall + verdict tally over N critique rolls.
    Pure. Rolls with no numeric overall (ERROR verdicts) are excluded from means
    but counted in the tally — an API failure must not read as a low score."""
    scored = [r for r in rolls if isinstance(r.get("overall_0_5"), (int, float))]
    out = {"n_rolls": len(rolls), "n_scored": len(scored),
           "verdicts": {}, "mean_overall": None, "mean_scores": {}}
    for r in rolls:
        v = r.get("verdict", "ERROR")
        out["verdicts"][v] = out["verdicts"].get(v, 0) + 1
    if not scored:
        return out
    out["mean_overall"] = round(sum(r["overall_0_5"] for r in scored) / len(scored), 3)
    dims = set()
    for r in scored:
        dims.update((r.get("scores") or {}).keys())
    for d in sorted(dims):
        vals = [r["scores"][d] for r in scored
                if isinstance((r.get("scores") or {}).get(d), (int, float))]
        if vals:
            out["mean_scores"][d] = round(sum(vals) / len(vals), 3)
    return out


def de_verdict_note(worst):
    """Reference note for a ΔE00 worst value. The 1.0/2.0 bands are the BRAND-palette
    bands (qa/thresholds.yaml brand_qa) quoted as familiar reference points — this
    image-vs-image use is an EXPERIMENT instrument, not the wired brand gate."""
    if worst is None:
        return "not scored"
    # boundary semantics mirror delta_e00.brand_compliance: PASS is STRICTLY below 1.0,
    # exactly 1.0 is already the warn band (blueprint §9.3, delta_e00.py:141-148).
    # WORDING IS DELIBERATELY WEAK on the pass band: k=6 whole-image dominant colours
    # are INSENSITIVE to a small-area per-piece swap (an armchair recolour barely moves
    # them) — no-signal is NOT proof of preservation (review finding 2026-07-14); the
    # per-piece truth instrument is the .blend probe + the overlay + the owner's eye.
    if worst < 1.0:
        return ("no whole-image dominant-colour shift detected (<1.0) — NOTE: this "
                "instrument cannot see small-area per-piece changes; not proof of "
                "preservation")
    if worst <= 2.0:
        return "dominant-colour shift in the warn band (1.0-2.0) — eyeball the pair"
    return "dominant-colour shift >2.0 — a large-area material/colour changed; inspect"


# ---------------------------------------------------------------------------
# instruments (lazy imports; each degrades to None = UNWIRED, never silent-pass)
# ---------------------------------------------------------------------------

def dominant_colors(path, k=6):
    """The repair_loop.make_brand_fn sampling recipe, verbatim (repair_loop.py:540-546)."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB").resize((160, 160))
        pal = im.convert("P", palette=Image.ADAPTIVE, colors=k).convert("RGB")
        return [c for _n, c in sorted(pal.getcolors(k * 4) or [], reverse=True)[:k]]
    except Exception:  # noqa: BLE001
        return None


def de00_pair(path_a, path_b, k=6):
    """Dominant-colour CIEDE2000 between two IMAGES, both directions (brand_compliance
    is nearest-match asymmetric). Returns None (UNWIRED) if either sampling fails."""
    import delta_e00
    ca, cb = dominant_colors(path_a, k), dominant_colors(path_b, k)
    if not ca or not cb:
        return None
    la = [delta_e00.srgb_to_lab(c) for c in ca]
    lb = [delta_e00.srgb_to_lab(c) for c in cb]
    ab = delta_e00.brand_compliance(la, lb)
    ba = delta_e00.brand_compliance(lb, la)
    worst = max(ab.get("worst_delta") or 0.0, ba.get("worst_delta") or 0.0)
    return {"a_vs_b": ab, "b_vs_a": ba, "worst_both": round(worst, 3),
            "note": de_verdict_note(worst)}


def overlay_check(control, candidate, out_png, recall_min=None):
    """overlay_fidelity.check, REPORT-ONLY by default. Recall is scene-dependent
    (pipeline/scripts/README.md:57-59: eye-level grain-heavy scenes read 40-45% even
    when the structure is perfectly preserved) — a fixed bound would deliver a
    predetermined FAIL that reads as 'Gemini repainted' (review finding 2026-07-14).
    So: no verdict unless the caller EXPLICITLY passes --recall-min for a camera setup
    whose achievable recall is known; the declared real verdict is the RED channel of
    the overlay PNG under a human eye (overlay_fidelity.py:12)."""
    try:
        import overlay_fidelity
        recall, precision, wired_verdict, outp = overlay_fidelity.check(
            control, candidate, out_png)
    except SystemExit as e:          # module sys.exit()s without numpy/Pillow
        print(f"  (overlay UNWIRED: {e})")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  (overlay UNWIRED: {e})")
        return None
    out = {"recall": recall, "precision": precision,
           "wired_verdict_0.80": wired_verdict, "recall_min": recall_min,
           "overlay_png": outp}
    if recall_min is None:
        out["experiment_verdict"] = ("REPORT-ONLY (no bound set — recall is "
                                     "scene-dependent; eyeball the RED overlay channel)")
    else:
        out["experiment_verdict"] = "PASS" if recall >= recall_min else "FAIL"
    return out


def sanity(path):
    try:
        import image_sanity
        return image_sanity.sanity_of_image(path)
    except Exception as e:  # noqa: BLE001
        print(f"  (image_sanity UNWIRED: {e})")
        return None


def critique_rolls(path, n, model_key):
    """N PAID judge rolls. Lazy import — critique.py sys.exit()s AT IMPORT without a
    key (critique.py:48-50), which must not kill the free instruments."""
    if n <= 0:
        return []
    try:
        import critique as _cr
    except SystemExit as e:
        print(f"  (critique UNWIRED: {e})")
        return []
    rolls = []
    for i in range(n):
        try:
            r = _cr.critique(path, "render", model_key)
        except Exception as e:  # noqa: BLE001
            r = {"verdict": "ERROR", "one_line": str(e)}
        r["_roll"] = i + 1
        rolls.append(r)
        ov = r.get("overall_0_5")
        print(f"    roll {i + 1}/{n}: {r.get('verdict')} overall={ov}")
    return rolls


def make_leg_b(control_png, spec, out_png, model_pref):
    """Dispatch the polish pass: render-polish@dev with the material story computed from
    the SPEC (the truth), not hand-typed prose. PAID. Returns the model id used or None."""
    import hybrid_render
    resolved = material_presets.resolve_materials(spec)
    # spec passed (scrutiny 2026-07-21): without it the story drops EVERY data-driven
    # bit — millwork subparts, linen base/bench/tub-chair, the e5 lighting sentence —
    # so the paid polish pass would repaint decided materials + flatten decided light
    story = material_presets.material_story(resolved, spec)
    room_type = str(spec.get("room", {}).get("type", "room")).replace("_", " ")
    prompt = hybrid_render.resolve_prompt(
        "@render-polish@dev", {"room_type": room_type, "material_story": story})
    used = hybrid_render.edit(control_png, prompt, out_png, prefer=model_pref)
    return used or None


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def to_markdown(res):
    L = ["# 3-leg materialized-render experiment — " + res["room_type"],
         "", f"date: {res['date']}  |  spec: `{res['spec']}`", ""]
    L.append("| leg | what | image |")
    L.append("|---|---|---|")
    for leg in ("A", "B", "C"):
        img = res["legs"].get(leg, {}).get("image")
        L.append(f"| {leg} | {LEG_DESC[leg]} | `{img or 'MISSING'}` |")
    L += ["", "## Material story (the spec's truth)", "", res["material_story"], ""]
    for leg in ("A", "B", "C"):
        d = res["legs"].get(leg) or {}
        L.append(f"## Leg {leg}")
        L.append("")
        if not d.get("image"):
            L += ["MISSING — not scored.", ""]
            continue
        s = d.get("sanity")
        L.append(f"- image_sanity: {s.get('verdict') if s else 'UNWIRED'}")
        cs = d.get("critique_summary")
        if cs and cs.get("n_rolls"):
            L.append(f"- critique mean overall (n={cs['n_scored']}/{cs['n_rolls']} rolls): "
                     f"**{cs['mean_overall']}** verdicts={cs['verdicts']}")
            if cs.get("mean_scores"):
                dims = ", ".join(f"{k} {v}" for k, v in sorted(cs["mean_scores"].items()))
                L.append(f"- critique per-dim means: {dims}")
        elif d.get("baseline_critique"):
            b = d["baseline_critique"]
            L.append(f"- baseline critique (existing, single-roll): "
                     f"overall {b.get('overall_0_5')} {b.get('verdict')}")
        L.append("")
    ov = res.get("overlay_b_vs_c")
    L.append("## Structure: leg B vs its control (leg C)")
    L.append("")
    if ov:
        L.append(f"- recall {ov['recall']:.3f}, precision {ov['precision']:.3f} "
                 f"(informational) — {ov['experiment_verdict']}")
        L.append(f"- the deciding artifact is the overlay (RED = structure lost, "
                 f"GREEN = invented): `{ov['overlay_png']}`")
    else:
        L.append("- UNWIRED (missing dep or missing leg B)")
    L.append("")
    L.append("## Materials preserved: ΔE00 dominant colours")
    L.append("")
    for key, label in (("de_b_vs_c", "leg B vs leg C (did the polish repaint?)"),
                       ("de_c_vs_a", "leg C vs leg A (how far the FF&E-true palette moved)")):
        de = res.get(key)
        if de:
            L.append(f"- {label}: worst {de['worst_both']} — {de['note']}")
        else:
            L.append(f"- {label}: UNWIRED")
    L += ["", "## Verdict", "",
          "The judge is UNCALIBRATED (M3.2) — numbers above are advisory. "
          "The deciding eye is the owner's: compare the three images side by side.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--leg-a", required=True, help="existing baseline render PNG")
    ap.add_argument("--leg-c", required=True, help="spec-materialized Cycles PNG (also leg B's control)")
    ap.add_argument("--leg-b", default=None, help="polish output PNG (if already produced)")
    ap.add_argument("--make-leg-b", action="store_true",
                    help="PAID: dispatch render-polish@dev on --leg-c to produce leg B")
    ap.add_argument("--baseline-critique", default=None,
                    help="existing critique JSON for leg A (reused, no re-spend)")
    ap.add_argument("--rolls", type=int, default=0,
                    help="PAID: critique rolls per leg (0 = skip judging)")
    ap.add_argument("--model", default="pro", choices=("pro", "flash"))
    ap.add_argument("--recall-min", type=float, default=None,
                    help="OPTIONAL recall bound; omit for report-only (recall is "
                         "scene-dependent — README pipeline/scripts:57-59)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    resolved = material_presets.resolve_materials(spec)
    os.makedirs(args.out, exist_ok=True)

    leg_b = args.leg_b
    model_used = None
    if args.make_leg_b and not leg_b:
        leg_b = os.path.join(args.out, "leg_b_polish.png")
        pref = ("gemini-3-pro-image-preview" if args.model == "pro" else None)
        print(f"leg B: dispatching render-polish@dev ({args.model}) ...")
        model_used = make_leg_b(args.leg_c, spec, leg_b, pref)
        if not model_used:
            print("  leg B FAILED (no model produced an image) — scoring A and C only")
            leg_b = None

    res = {"date": time.strftime("%Y-%m-%d %H:%M"), "spec": args.spec,
           "room_type": str(spec.get("room", {}).get("type", "room")),
           "material_story": material_presets.material_story(resolved, spec),
           "leg_b_model_used": model_used, "legs": {}}

    for leg, img in (("A", args.leg_a), ("B", leg_b), ("C", args.leg_c)):
        d = {"image": img, "what": LEG_DESC[leg]}
        if img and os.path.exists(img):
            print(f"leg {leg}: sanity + {args.rolls} critique roll(s)")
            d["sanity"] = sanity(img)
            rolls = critique_rolls(img, args.rolls, args.model)
            if rolls:
                d["critique_rolls"] = rolls
                d["critique_summary"] = summarize_rolls(rolls)
        elif img:
            print(f"leg {leg}: MISSING image {img}")
            d["image"] = None
        res["legs"][leg] = d

    if args.baseline_critique:
        # fail LOUD on a bad path (a silently-missing baseline reads as 'no baseline'),
        # and pin the critique to leg A's identity — reusing another render's scorecard
        # as the baseline is the flattering-scorer shape (review finding 2026-07-14)
        with open(args.baseline_critique, encoding="utf-8") as f:
            bc = json.load(f)
        art = os.path.basename(str(bc.get("_artifact", "")))
        if art and art != os.path.basename(args.leg_a):
            print(f"  !! baseline critique WARN: _artifact {art!r} != leg A "
                  f"{os.path.basename(args.leg_a)!r} — recorded, but verify identity")
            bc["_identity_mismatch"] = True
        res["legs"]["A"]["baseline_critique"] = bc

    if leg_b and os.path.exists(leg_b):
        res["overlay_b_vs_c"] = overlay_check(
            args.leg_c, leg_b, os.path.join(args.out, "leg_b_vs_c.overlay.png"),
            args.recall_min)
        res["de_b_vs_c"] = de00_pair(leg_b, args.leg_c)
    res["de_c_vs_a"] = de00_pair(args.leg_c, args.leg_a)

    jp = os.path.join(args.out, "experiment_3leg.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    mp = os.path.join(args.out, "experiment_3leg.md")
    with open(mp, "w", encoding="utf-8") as f:
        f.write(to_markdown(res))
    print(f"wrote {jp}\nwrote {mp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
