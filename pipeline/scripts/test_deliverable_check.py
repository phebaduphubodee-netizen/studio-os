"""Tests for deliverable_check — the first gate in this repo whose thresholds
come from work that was actually sold rather than from the builder.

The negative controls are the nine ways this repo's previous scorers flattered
themselves: a metric payable in noise, a resolution bump buying detail, a NOT RUN
row printing like a pass, a conjunction so tight that real delivered work fails
it, and a threshold quietly chosen to fit our own frame.
"""
import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deliverable_check as DC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "_private", "benchmark", "reproduction", "TRN-002")
LD1 = os.path.join(REPO, "pipeline", "output", "room_bedroom_suite_eye_ld1.png")


def _img(path, w=800, h=600, seed=0, blocks=8, noise=0.0):
    """A field of soft blocks (structure in the 4-32 px octave) plus optional
    fine grain (the 1-3 px octave the band deliberately excludes)."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w))
    bs = max(1, min(w, h) // blocks)
    for y in range(0, h, bs):
        for x in range(0, w, bs):
            a[y:y + bs, x:x + bs] = rng.uniform(20, 230)
    if noise:
        a = a + rng.normal(0, noise, a.shape)
    a = np.clip(a, 0, 255)
    Image.fromarray(np.dstack([a, a, a]).astype("uint8")).save(path)
    return str(path)


def _std(**kw):
    s = {"mandatory": ["D1"], "scored": ["D2", "D3"], "scored_need": 2,
         "rows": {"D1": {"metric": "mp", "direction": "min", "threshold": 2.0},
                  "D2": {"metric": "p1", "direction": "max", "threshold": 30.0},
                  "D3": {"metric": "stops", "direction": "min", "threshold": 2.0},
                  "D4": {"metric": "clipped_pct", "direction": "max", "threshold": 0.3},
                  "D5": {"metric": "octave_energy", "direction": "band",
                         "threshold": [1.0, 3.5]},
                  "D6": {"metric": "dark_share_pct", "direction": "min", "threshold": 0.7},
                  "D10": {"metric": "chroma_iqr_deg", "direction": "min", "threshold": 3.0},
                  "D7": {"metric": "loose_objects", "direction": "min", "threshold": 12},
                  "D8": {"metric": "primitive_acquire_class", "direction": "max",
                         "threshold": 0},
                  "D9": {"metric": "flat_shaded_curved", "direction": "max",
                         "threshold": 0}}}
    s.update(kw)
    return s


# --- the metric cannot be bought ------------------------------------------------

def test_fine_grain_does_not_buy_the_detail_row(tmp_path):
    """THE ROW THAT JUSTIFIES BAND-LIMITING. An unrestricted mean |grad L| floor is
    payable in noise: add grain, a denoiser artefact or a 4k wood texture and the
    number rises while the frame gets uglier. Our own best frame scores 1.58x the
    reproduction target on the unrestricted metric, entirely from a slat wall."""
    clean = DC.measure_image(_img(tmp_path / "a.png", seed=1, noise=0.0))
    noisy = DC.measure_image(_img(tmp_path / "b.png", seed=1, noise=24.0))
    band_gain = noisy["octave_energy"] / clean["octave_energy"]
    L = DC._lum(DC._norm(DC._load(str(tmp_path / "b.png"))))
    Lc = DC._lum(DC._norm(DC._load(str(tmp_path / "a.png"))))
    raw_gain = (float(np.mean(np.hypot(*np.gradient(L))))
                / float(np.mean(np.hypot(*np.gradient(Lc)))))
    assert raw_gain > 3.0, "the unrestricted metric must be visibly gameable"
    # 1.25 and not 1.5: the first band-limited version measured mean|grad| OF the
    # bandpass and moved 3.45x here. A limit loose enough to have passed it would
    # not have caught it.
    assert band_gain < 1.25, f"band-limited metric moved {band_gain:.2f}x on pure noise"


def test_upscaling_does_not_buy_any_row_but_the_resolution_row(tmp_path):
    small = _img(tmp_path / "s.png", w=800, h=600, seed=3)
    im = Image.open(small).resize((1600, 1200), Image.LANCZOS)
    big = str(tmp_path / "b.png")
    im.save(big)
    a, b = DC.measure_image(small), DC.measure_image(big)
    assert b["mp"] > a["mp"] * 3.5
    for k in ("p1", "stops", "octave_energy", "dark_share_pct"):
        assert b[k] == pytest.approx(a[k], rel=0.12), f"{k} moved on a pure upscale"


# --- NOT RUN is never PASS -------------------------------------------------------

def test_a_scene_row_with_no_scene_is_not_run_not_pass(tmp_path):
    p = _img(tmp_path / "x.png")
    rows = {r[0]: r for r in DC.score(_std(), p, scene=None)}
    for rid in ("D7", "D8", "D9"):
        assert rows[rid][1] == "NOT RUN"
        assert "not the same as fine" in rows[rid][4]


def test_a_mandatory_row_that_did_not_run_cannot_qualify(tmp_path):
    p = _img(tmp_path / "x.png", w=2000, h=1500)
    std = _std(mandatory=["D1", "D8"])
    rows = DC.score(std, p, scene=None)
    ok, why = DC.qualifies(rows, std)
    assert not ok and "NOT RUN" in why


def test_summarise_reports_not_run_separately(tmp_path):
    p = _img(tmp_path / "x.png")
    s = DC.summarise(DC.score(_std(), p, scene=None))
    assert s["not_run"] == 3 and s["pass"] + s["fail"] == 7


# --- qualifying is a count, not a conjunction ------------------------------------

def test_qualifying_needs_every_mandatory_row(tmp_path):
    p = _img(tmp_path / "s.png", w=800, h=600)          # 0.48 MP, below D1
    std = _std()
    ok, why = DC.qualifies(DC.score(std, p, scene=None), std)
    assert not ok and "D1 is mandatory" in why


def test_one_scored_row_may_fail_when_the_count_still_clears():
    std = _std(scored=["D2", "D3", "D4"], scored_need=2)
    rows = [("D1", "PASS", 3, 2, ""), ("D2", "PASS", 1, 1, ""),
            ("D3", "FAIL", 1, 9, ""), ("D4", "PASS", 1, 1, "")]
    ok, why = DC.qualifies(rows, std)
    assert ok and "2/3" in why


def test_the_scored_need_is_not_a_conjunction():
    """28.6% of the 658 delivered frames pass all seven image rows. A standard
    that demands all of them rejects 71% of work that was sold to clients."""
    std = DC.load_standard()
    assert std["scored_need"] < len(std["scored"])


# --- thresholds come from the pool, not from us ----------------------------------

def test_every_image_threshold_cites_the_pool_that_produced_it():
    std = DC.load_standard()
    for rid in ("D1", "D2", "D3", "D4", "D5", "D6", "D10"):
        assert "delivered frames" in std["rows"][rid]["source"]
    for rid in ("D7", "D8", "D9"):
        assert std["rows"][rid]["source"] == "declared by the plan"


def test_a_thin_census_refuses_to_produce_thresholds():
    thin = [{"mp": 1.0, "p1": 1.0, "stops": 1.0, "clipped_pct": 0.0,
             "octave_energy": 1.0, "dark_share_pct": 1.0, "chroma_iqr_deg": 1.0}] * 10
    with pytest.raises(ValueError, match="preference, not a standard"):
        DC.cut_thresholds(thin)


def test_an_unreadable_pool_file_is_recorded_not_dropped(tmp_path):
    bad = str(tmp_path / "nope.png")
    rows = DC.census([_img(tmp_path / "ok.png"), bad])
    assert len(rows) == 2, "a file that will not open must stay in the denominator"
    assert "error" in rows[1]


# --- scene rows ------------------------------------------------------------------

def test_scene_rows_name_the_defects_the_owner_named_by_eye():
    spec = {"beauty": None, "masses": [
        {"name": "pillow_L", "kind": "oct"}, {"name": "bolster", "kind": "oct"},
        {"name": "chair_seat", "kind": "oct"}, {"name": "wall_a", "kind": "box"},
        {"name": "nightstand_books", "kind": "box"}]}
    m = DC.measure_scene_spec(spec)
    assert m["primitive_acquire_class"] == 3      # pillow, bolster, chair seat
    assert m["flat_shaded_curved"] == 3           # the three oct masses
    assert m["loose_objects"] == 1                # the books


def test_enabling_smooth_shading_clears_the_flat_shaded_row():
    spec = {"beauty": {"soft": {"pillow_L": {"smooth": True, "subsurf": 2}}},
            "masses": [{"name": "pillow_L", "kind": "oct"},
                       {"name": "bolster", "kind": "oct"}]}
    assert DC.measure_scene_spec(spec)["flat_shaded_curved"] == 1


# --- THE ACCEPTANCE CONTRACT -----------------------------------------------------
# A standard our best frame already passes is not a standard; one that fails work
# that was sold is measuring the wrong thing. It has to do both or be deleted.

@pytest.mark.skipif(not os.path.isfile(LD1), reason="frame not on this machine")
def test_it_does_not_qualify_our_own_best_frame():
    """A standard our best frame passes is not a standard.

    AND THE FIRST VERSION OF THIS TEST WAS WRONG IN A WAY WORTH KEEPING WRITTEN
    DOWN. It asserted that ld1 fails the detail row D5, because the draft metric —
    mean |grad| of the bandpass — put ld1 above the pool's p90 on the slat wall's
    high-frequency detail. Fixing that metric for a real defect (it moved 3.45x on
    pure noise) moved ld1 back inside the band, and the honest reading is that ld1's
    tone, range and 4-32 px structure ARE at delivered level. Five of six scored
    image rows pass.

    So the assertion is now the one that was actually intended: it must not
    QUALIFY. It does not, because D8 and D9 are mandatory and no scene dump exists
    for that frame, and because D10 catches the amber-monochrome cast that a
    sighted judge named independently.

    The test was NOT loosened to fit the measurement. The proxy ("fails >= 5 of 10
    rows") was invented before the measurement existed; the criterion it stood for
    still holds, and the row that fails names a defect a person named first."""
    std = DC.load_standard()
    rows = DC.score(std, LD1, scene=None)
    ok, why = DC.qualifies(rows, std)
    assert not ok, "a standard our best frame passes is not a standard"
    failed = {r[0] for r in rows if r[1] == "FAIL"}
    assert "D10" in failed, "the amber-monochrome cast a sighted judge named"
    not_run = {r[0] for r in rows if r[1] == "NOT RUN"}
    assert {"D8", "D9"} <= not_run and ("D8" in why or "D9" in why)


@pytest.mark.skipif(not os.path.isdir(LANE), reason="lane not on this machine")
def test_it_fails_the_frame_the_owner_rejected_on_at_least_eight_rows():
    std = DC.load_standard()
    spec = json.load(open(os.path.join(REPO, "training", "TRN-002", "spec_r38.json"),
                          encoding="utf-8"))
    rows = DC.score(std, os.path.join(LANE, "renders", "trn002_mat_r38c.png"),
                    DC.measure_scene_spec(spec))
    assert DC.summarise(rows)["fail"] >= 8
    assert not DC.qualifies(rows, std)[0]


@pytest.mark.skipif(not os.path.isdir(LANE), reason="lane not on this machine")
def test_the_reproduction_target_fails_on_resolution_and_passes_the_rest():
    """THE ROW THAT EXPLAINS WHY DELIV-001 EXISTS. The frame we spent 38 rounds
    reproducing is good work — it clears the tone and structure rows its own
    studio's output sets. It is 0.89 MP, the bottom decile of that studio's pool,
    so matching it pixel for pixel could never produce something sendable."""
    std = DC.load_standard()
    rows = {r[0]: r for r in DC.score(std, os.path.join(LANE, "target.jpg"), None)}
    assert rows["D1"][1] == "FAIL"
    for rid in ("D2", "D3", "D4", "D5", "D6"):
        assert rows[rid][1] == "PASS", f"{rid} failed on delivered work"


def test_half_of_delivered_work_clears_the_bar():
    """The bar is the median of what the friend's studio actually sold. Measured
    on the census: D1 + 5 of 6 qualifies 50.5% of the 658. If this drifts far from
    half, the standard has stopped describing deliverable work."""
    census = os.path.join(REPO, "_private", "benchmark", "census-2026-08-09.json")
    if not os.path.isfile(census):
        pytest.skip("census not on this machine")
    std = DC.load_standard()
    rows = [r for r in json.load(open(census, encoding="utf-8")) if "error" not in r]
    n = 0
    for m in rows:
        vs = []
        for rid in std["scored"]:
            t = std["rows"][rid]
            v, d, thr = m[t["metric"]], t["direction"], t["threshold"]
            vs.append((v >= thr) if d == "min" else (v <= thr) if d == "max"
                      else (thr[0] <= v <= thr[1]))
        if m["mp"] >= std["rows"]["D1"]["threshold"] and sum(vs) >= std["scored_need"]:
            n += 1
    share = n / len(rows)
    assert 0.40 <= share <= 0.62, f"{share:.1%} of delivered work qualifies"
