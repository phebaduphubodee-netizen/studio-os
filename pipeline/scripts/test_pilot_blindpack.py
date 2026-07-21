"""Tests for pilot_blindpack.py -- the blind sellability-pilot bundler.

The load-bearing property is BLINDNESS: no client string, no role marker, no real path may reach
pilot-blind.html. Several tests are MUTATION PROBES -- they plant a leak and assert the guard
catches it, so an all-green run cannot be a tautology (the failure mode the repo keeps finding).
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pilot_blindpack as pb

CLIENT = "SECRETCLIENTNAME"          # a fake client token we watch for leaks
WATERMARKED = "I-99-002/002/wm777.png"
PORTRAIT = "I-99-001/001/portrait1.jpg"


def make_fixture(tmp):
    """A minimal pilot-pairs.json: 2 our bedroom renders x 3 clean bedroom anchors + 1 living,
    plus the two anchors we exclude (a watermark + a portrait)."""
    def our(name):
        return {"name": name, "path": os.path.join(tmp, "renders", name), "provenance": "our lane"}

    def anc(ref, fname):
        return {"ref": ref, "path": os.path.join(tmp, CLIENT, "files", fname),
                "icode": ref.split("/")[0], "thread": "x", "maxdim": 4000, "room_word": "bedroom"}

    pairs = []
    beds_anchor = [("I-99-010/010/a1.jpg", "bed_a1.jpg"),
                   ("I-99-011/011/a2.jpg", "bed_a2.jpg"),
                   ("I-99-012/012/a3.jpg", "bed_a3.jpg")]
    our_beds = ["R_PRJ999_MasterSuite_Cam01_v01.png", "R_PRJ999_MasterSuite_Cam02_v04.png"]
    pid = 1
    for oname in our_beds:
        for ref, fn in beds_anchor:
            pairs.append({"pair_id": "P%02d" % pid, "room_type": "bedroom",
                          "ours": our(oname), "anchor": anc(ref, fn), "tripwire": None})
            pid += 1
    # one living pair (below parity: single clean living anchor)
    pairs.append({"pair_id": "P%02d" % pid, "room_type": "living",
                  "ours": our("R_PRJ999_LivingRoom_Cam01_v01.png"),
                  "anchor": anc("I-99-020/020/liv.jpg", "liv1.jpg"), "tripwire": None})
    pid += 1
    # the two excluded anchors (still bedroom-typed, so exclusion, not room, must drop them)
    pairs.append({"pair_id": "P%02d" % pid, "room_type": "bedroom",
                  "ours": our("R_PRJ999_MasterSuite_Cam01_v01.png"),
                  "anchor": anc(WATERMARKED, "wm.png"), "tripwire": None})
    pid += 1
    pairs.append({"pair_id": "P%02d" % pid, "room_type": "bedroom",
                  "ours": our("R_PRJ999_MasterSuite_Cam02_v04.png"),
                  "anchor": anc(PORTRAIT, "portrait.jpg"), "tripwire": None})
    return {"parity_minimum": 2, "our_lane": {}, "pairs": pairs, "tripwires": []}


@pytest.fixture
def built(tmp_path):
    tmp = str(tmp_path)
    fixture = make_fixture(tmp)
    pairs_json = os.path.join(tmp, "pilot-pairs.json")
    with open(pairs_json, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, ensure_ascii=False)
    # a real (tiny) clay file so the neg-control rides in even with --no-images
    from PIL import Image
    clay = os.path.join(tmp, "clay.png")
    Image.new("RGB", (40, 30), (200, 200, 200)).save(clay)
    out = os.path.join(tmp, "pilot-blind")
    rc = pb.main(["--pairs", pairs_json, "--out", out, "--clay", clay,
                  "--exclude", WATERMARKED, PORTRAIT, "--no-images"])
    assert rc == 0, "generator should succeed on a clean fixture"
    html = open(os.path.join(out, "pilot-blind.html"), encoding="utf-8").read()
    key = json.load(open(os.path.join(out, "pilot-blind-key.json"), encoding="utf-8"))
    md = open(os.path.join(out, "pilot-blind.md"), encoding="utf-8").read()
    return {"out": out, "html": html, "key": key, "md": md, "pairs_json": pairs_json,
            "clay": clay, "tmp": tmp}


# ---- exclusion -------------------------------------------------------------
def test_excluded_refs_never_pair(built):
    for ref in (WATERMARKED, PORTRAIT):
        assert not any(r["anchor_ref"] == ref for r in built["key"]["phase1"]), \
            f"{ref} must never reach a judging row"
    assert built["key"]["excluded_refs"] == [WATERMARKED, PORTRAIT]


def test_six_bedroom_gate_pairs_plus_one_living_advisory(built):
    p1 = built["key"]["phase1"]
    beds = [r for r in p1 if r["room_type"] == "bedroom"]
    livs = [r for r in p1 if r["room_type"] == "living"]
    assert len(beds) == 12, "2 renders x 3 anchors x 2 orders"
    assert len(livs) == 2, "1 living pair x 2 orders"
    assert all(r["advisory_below_parity"] for r in livs), "single living anchor => advisory"
    assert all(not r["advisory_below_parity"] for r in beds), "3 bedroom anchors => gate-eligible"


# ---- both-orders + tripwires ----------------------------------------------
def test_every_pair_in_both_orders(built):
    from collections import Counter
    c = Counter(r["pair_id"] for r in built["key"]["phase1"])
    assert c and all(v == 2 for v in c.values()), f"each pair needs exactly 2 orders: {c}"


def test_neg_control_and_selftie_present_and_phase2_only(built):
    p2 = built["key"]["phase2"]
    kinds = {r["kind"] for r in p2}
    assert "known-bad-must-lose" in kinds, "clay neg-control must ride in phase 2"
    assert "anchor-vs-itself" in kinds, "self-tie must ride in phase 2"
    assert {r["pair_id"] for r in p2} <= {"NEG", "TIE"}
    assert all(r["pair_id"] not in ("NEG", "TIE") for r in built["key"]["phase1"]), \
        "tripwires must NOT appear in phase 1"


def test_neg_and_selftie_use_different_anchors(built):
    # the neg control and the self-tie must not lean on ONE image (pick_bedroom_anchor's whole job)
    p2 = built["key"]["phase2"]
    neg_refs = {r["anchor_ref"] for r in p2 if r["pair_id"] == "NEG"}
    tie_refs = {r["anchor_ref"] for r in p2 if r["pair_id"] == "TIE"}
    assert neg_refs and tie_refs, "both tripwires must record their anchor ref"
    assert neg_refs.isdisjoint(tie_refs), "neg-control and self-tie must use DIFFERENT anchors"
    assert built["key"]["tripwire_anchor_overlap"] is False


# ---- blindness: the real html is clean ------------------------------------
def test_html_has_no_client_or_role_or_path(built):
    html = built["html"]
    for token in (CLIENT, "R_PRJ", "MasterSuite", "LivingRoom", "ours", "clay", "control-clay",
                  "I-99-010", built["tmp"]):
        assert token not in html, f"forbidden token leaked into html: {token!r}"


def test_every_img_src_is_opaque(built):
    import re
    srcs = re.findall(r"img\d{3}\.jpg", built["html"])
    assert srcs, "html should reference opaque images"
    # no real basename with an image extension may appear
    assert "bed_a1.jpg" not in built["html"] and "wm.png" not in built["html"]


def test_md_is_howto_and_spoiler_free(built):
    md = built["md"]
    # the md must NOT carry the ref->opaque map: listing anchors de-blinds ours by elimination
    for tok in ("R_PRJ", CLIENT, "I-99-010", "I-99-011", "I-99-020", "img001", "img004"):
        assert tok not in md, f"md must not reveal role/ref/opaque map: {tok!r}"
    assert "pilot-blind.html" in md and "pilot-blind-key.json" in md, "md is the how-to"


# ---- mutation probes: the guard is not a tautology ------------------------
def test_guard_catches_planted_client_token(built):
    slots = {os.path.join(built["tmp"], CLIENT, "files", "bed_a1.jpg"): {"role": "anchor"}}
    poisoned = built["html"].replace("</body>", f"<!-- {CLIENT} --></body>")
    hits, bad = pb.guard_html(poisoned, slots)
    assert CLIENT in hits, "guard must detect a planted client name (else it is a tautology)"


def test_guard_catches_non_opaque_src(built):
    poisoned = built["html"].replace("</body>", '<img src="imgs/bed_a1.jpg"></body>')
    hits, bad = pb.guard_html(poisoned, {})
    assert any("bed_a1.jpg" in b for b in bad), "guard must flag a non-opaque image src"


def test_generator_refuses_when_guard_would_trip(tmp_path, monkeypatch):
    """If build_html ever emitted a real path, main() must return 1, not write a trusted bundle."""
    tmp = str(tmp_path)
    fixture = make_fixture(tmp)
    pj = os.path.join(tmp, "p.json")
    json.dump(fixture, open(pj, "w", encoding="utf-8"))
    from PIL import Image
    clay = os.path.join(tmp, "clay.png"); Image.new("RGB", (10, 10)).save(clay)
    orig = pb.build_html
    monkeypatch.setattr(pb, "build_html", lambda a, b: orig(a, b) + f"<!--{CLIENT}-->")
    rc = pb.main(["--pairs", pj, "--out", os.path.join(tmp, "o"), "--clay", clay,
                  "--exclude", WATERMARKED, PORTRAIT, "--no-images"])
    assert rc == 1, "a leaked token must make the generator refuse (exit 1)"


# ---- determinism -----------------------------------------------------------
def test_deterministic_same_seed(built):
    out2 = os.path.join(built["tmp"], "pilot-blind-2")
    rc = pb.main(["--pairs", built["pairs_json"], "--out", out2, "--clay", built["clay"],
                  "--exclude", WATERMARKED, PORTRAIT, "--no-images"])
    assert rc == 0
    html2 = open(os.path.join(out2, "pilot-blind.html"), encoding="utf-8").read()
    assert html2 == built["html"], "same seed must reproduce byte-identical html"


def test_key_ours_side_matches_order(built):
    for r in built["key"]["phase1"]:
        assert r["ours_side"] == ("left" if r["order"] == "ours-left" else "right")


# ---- image normalisation ---------------------------------------------------
def test_normalise_caps_long_edge(tmp_path):
    from PIL import Image
    src = os.path.join(str(tmp_path), "big.png")
    Image.new("RGB", (4000, 2250), (10, 20, 30)).save(src)
    dst = os.path.join(str(tmp_path), "small.jpg")
    w, h = pb.normalise_image(src, dst)
    assert max(w, h) <= pb.DISPLAY_EDGE
    assert os.path.exists(dst)
    got = Image.open(dst)
    assert max(got.size) <= pb.DISPLAY_EDGE and got.format == "JPEG"


def test_small_image_not_upscaled(tmp_path):
    from PIL import Image
    src = os.path.join(str(tmp_path), "s.png"); Image.new("RGB", (800, 600)).save(src)
    dst = os.path.join(str(tmp_path), "s.jpg")
    w, h = pb.normalise_image(src, dst)
    assert (w, h) == (800, 600), "images already under the cap must not be upscaled"


# ---- two-phase gate: the clay must be isolated to phase 2 (blindness mechanism) ------
import re


def _p1p2(html):
    m = re.search(r"const P1 = (\[.*?\]), P2 = (\[.*?\]);", html, re.S)
    return json.loads(m.group(1)), json.loads(m.group(2))


def _rebuild(built):
    pilot = json.load(open(built["pairs_json"], encoding="utf-8"))
    kept, _, _ = pb.kept_pairs(pilot, [WATERMARKED, PORTRAIT])
    slots, phase1, phase2 = pb.build_slots(kept, built["clay"])
    return slots, pb.assign_opaque(slots)


def test_clay_neg_control_never_appears_in_phase1(built):
    """The clay is a massing of our OWN bedroom; if it shows in phase-1 the judge can match its
    geometry to our finished render and de-anonymise us. It must live ONLY in phase-2."""
    slots, opaque = _rebuild(built)
    clay_rp = [rp for rp, m in slots.items() if m["role"] == "neg_control"][0]
    clay_img = opaque[clay_rp]
    p1, p2 = _p1p2(built["html"])
    p1_imgs = {row[s] for row in p1 for s in ("left", "right")}
    p2_imgs = {row[s] for row in p2 for s in ("left", "right")}
    assert clay_img in p2_imgs, "clay must appear in phase 2"
    assert clay_img not in p1_imgs, "clay must NEVER appear in phase 1 (de-blinds our bedroom)"


def test_html_enforces_two_phase_lock(built):
    """The gating that keeps phase-2 hidden until phase-1 is answered lives in the HTML; pin the
    exact tokens so the most likely JS regressions turn a test red instead of shipping de-blinded."""
    h = built["html"]
    assert "#p2{display:none}" in h, "phase 2 must start hidden"
    assert 'id="lockbtn" disabled' in h, "lock button must start disabled"
    assert "n<tot" in h, "lock stays disabled until every phase-1 row is answered"


def test_guard_catches_static_role_word_with_empty_slots(built):
    """Mutation probe for the STATIC half of the guard: a bare role word not derivable from any
    path (empty slots) must still be caught -- else FORBIDDEN_STATIC could rot silently."""
    poisoned = built["html"].replace("</body>", "<!-- ours --></body>")
    hits, bad = pb.guard_html(poisoned, {})
    assert "ours" in hits, "static role word must be caught even with no path-derived tokens"


def test_unmatched_exclude_ref_refuses(tmp_path):
    """no-silent-drop: an --exclude ref that matches no pair (typo/format drift) must fail loud."""
    tmp = str(tmp_path)
    pj = os.path.join(tmp, "p.json")
    json.dump(make_fixture(tmp), open(pj, "w", encoding="utf-8"))
    from PIL import Image
    clay = os.path.join(tmp, "clay.png"); Image.new("RGB", (10, 10)).save(clay)
    rc = pb.main(["--pairs", pj, "--out", os.path.join(tmp, "o"), "--clay", clay,
                  "--exclude", "I-00-000/typo/nomatch.png", "--no-images"])
    assert rc == 1, "an --exclude ref matching nothing must refuse (fail-loud)"


def test_html_rows_agree_with_key(built):
    """The judge grades the html (opaque); the designer scores with the key. If the two disagree
    on any rid, every verdict is mislabeled. Pin html<->key agreement per row."""
    p1, _ = _p1p2(built["html"])
    rows = {r["rid"]: r for r in p1}
    for k in built["key"]["phase1"]:
        row = rows[k["rid"]]
        assert row[k["ours_side"]] == k["ours_img"], f"{k['rid']}: ours image/side mismatch"
        anchor_side = "right" if k["ours_side"] == "left" else "left"
        assert row[anchor_side] == k["anchor_img"], f"{k['rid']}: anchor image/side mismatch"


def test_key_carries_parity_and_unconfirmed_delivery(built):
    for r in built["key"]["phase1"]:
        assert "meets_anchor_parity" in r, "gate readiness is anchor-parity, honestly named"
        assert "anchor_delivery_signal" in r, "delivery status must ride with every row"
    assert built["key"]["delivery_status_caveat"], "unconfirmed-delivery caveat must be present"
    assert "OUTSTANDING" in built["key"]["known_rework_tripwire_status"], \
        "the real known-REWORK tripwire must be flagged outstanding, not silently covered by clay"
    assert "parity_census_before_exclusion" in built["key"]


def test_assign_opaque_is_path_independent(built):
    """Cross-machine reproducibility: opaque numbering keys on ref/name, not absolute path."""
    def s(prefix):
        return {f"{prefix}/x/bed_a1.jpg": {"role": "anchor", "ref": "I-99-010/010/a1.jpg"},
                f"{prefix}/y/r.png": {"role": "ours", "name": "R_PRJ999_MasterSuite_Cam01_v01.png"}}
    o1, o2 = pb.assign_opaque(s("/root_a")), pb.assign_opaque(s("/totally/different/root"))
    by_id1 = {("I-99-010/010/a1.jpg" if "bed" in rp else "r"): img for rp, img in o1.items()}
    by_id2 = {("I-99-010/010/a1.jpg" if "bed" in rp else "r"): img for rp, img in o2.items()}
    assert by_id1 == by_id2, "opaque numbering must not depend on the checkout path"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
