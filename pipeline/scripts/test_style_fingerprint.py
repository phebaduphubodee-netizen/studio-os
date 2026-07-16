"""Tests for style_fingerprint.py -- the LOCAL render fingerprint (Stage B).

The load-bearing axes (chromatic_mono_index, neutral_share, warmth, lighting, black_hole)
are all PER-PIXEL and KMeans-free, so they are tested hermetically on synthetic images that
ALWAYS run. The KMeans palette is tested only for structural invariants (k=6 over-segments a
flat synthetic, so exact area shares are not asserted on synthetics -- that would be fragile).

The de-wood real-image tripwire is the acceptance test: it must (a) read walnut as MORE
mono-material than de-wood, and (b) read the UNCHANGED black-hole cavity as ~EQUAL in both --
the fingerprint must refuse to reward the hole nobody fixed. It skips VISIBLY (never silently)
if the two clay renders are absent, and the synthetic separation test still guards the logic.
"""
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import style_fingerprint as sf

REPO = Path(__file__).resolve().parents[2]
WALNUT = REPO / "assets/projects/PRJ-2026-002/maps/R_PRJ002_MasterSuite_Cam01_v01_control-clay.png"
DEWOOD = REPO / ("projects/PRJ-2026-002_c001-house/04_visualization/experiments/"
                 "dewood-2026-07-15/R_PRJ002_MasterSuite_dewood_clay.png")

WOOD = (180, 100, 40)     # a saturated warm wood -> LAB chroma well above CHROMA_NEUTRAL
COOL = (60, 120, 200)     # a cool blue
GRAY = (128, 128, 128)    # neutral
WHITE = (255, 255, 255)


def _png(tmp_path, arr, name="x.png"):
    p = tmp_path / name
    Image.fromarray(arr.astype(np.uint8)).save(p)
    return str(p)


def _solid(color, h=80, w=80):
    a = np.zeros((h, w, 3), np.uint8)
    a[:, :] = color
    return a


def _left_right(c1, c2, h=80, w=80):
    a = np.zeros((h, w, 3), np.uint8)
    a[:, : w // 2] = c1
    a[:, w // 2:] = c2
    return a


# four saturated, hue-SPREAD colours (orange / blue / green / magenta) -> low hue_resultant
FOUR_HUES = [(200, 80, 60), (60, 140, 200), (70, 170, 90), (190, 70, 160)]


def _quadrants(colors, h=80, w=80):
    a = np.zeros((h, w, 3), np.uint8)
    a[: h // 2, : w // 2] = colors[0]
    a[: h // 2, w // 2:] = colors[1]
    a[h // 2:, : w // 2] = colors[2]
    a[h // 2:, w // 2:] = colors[3]
    return a


# ----------------------------- mono-material (the tripwire axis) -----------------------------

def test_mono_index_solid_hue_is_high(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _solid(WOOD)))
    assert fp["material"]["colored_share"] > 0.95
    assert fp["material"]["hue_resultant"] > 0.95
    assert fp["material"]["chromatic_mono_index"] > 0.9


def test_mono_index_neutral_is_near_zero(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _solid(GRAY)))
    assert fp["material"]["colored_share"] < 0.05
    assert fp["material"]["chromatic_mono_index"] < 0.05
    assert fp["material"]["neutral_share"] > 0.95


def test_mono_index_half_neutral_is_middling(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _left_right(WOOD, WHITE)))
    assert 0.4 < fp["material"]["colored_share"] < 0.6
    assert 0.4 < fp["material"]["chromatic_mono_index"] < 0.6


def test_mono_index_SEPARATES_the_three(tmp_path):
    """The core claim, mutation-style: adding a neutral base MUST lower the mono index.
    solid-hue > half-neutral > all-neutral, strictly. If this ever ties, the axis is dead."""
    solid = sf.fingerprint(_png(tmp_path, _solid(WOOD), "s.png"))["material"]["chromatic_mono_index"]
    half = sf.fingerprint(_png(tmp_path, _left_right(WOOD, WHITE), "h.png"))["material"]["chromatic_mono_index"]
    gray = sf.fingerprint(_png(tmp_path, _solid(GRAY), "g.png"))["material"]["chromatic_mono_index"]
    assert solid > half > gray


def test_multi_hue_reads_less_mono_than_single_hue(tmp_path):
    """KILLS the `hue_resultant := 1.0` mutation (review 2026-07-15, findings 2/6). Four saturated
    DIFFERENT hues at ~full colored area must read hue_resultant << 1 and chromatic_mono_index far
    below a single-hue field of the SAME colored area -- the ONLY test that exercises the
    discriminating (hue-spread) half of the index. Without it, dropping hue_resultant to a constant
    passes the whole suite, and a rich multi-material palette scores as maximally mono."""
    quad = sf.fingerprint(_png(tmp_path, _quadrants(FOUR_HUES), "q.png"))["material"]
    solid = sf.fingerprint(_png(tmp_path, _solid(WOOD), "s.png"))["material"]
    assert quad["colored_share"] > 0.9 and solid["colored_share"] > 0.9   # same (near-full) area
    assert quad["hue_resultant"] < 0.6                                     # hues spread (mutant=1.0)
    assert quad["chromatic_mono_index"] < 0.6                             # so LOW despite full area
    assert quad["chromatic_mono_index"] < solid["chromatic_mono_index"] - 0.3


def test_chromatic_index_is_blind_to_neutral_mono_KNOWN_LIMIT(tmp_path):
    """DOCUMENTED limitation, not a virtue (review 2026-07-15, findings 3/9). An all-white or
    all-grey room is a textbook DR §2 mono-material trap, yet the CHROMATIC index reads it ~0
    (least mono). Pinned so the blindness is a known caveated fact -- and so a future neutral-mono
    lane has a red test to turn green. See the OVERCLAIM GUARD caveat in _material()."""
    white = sf.fingerprint(_png(tmp_path, _solid((248, 246, 242)), "w.png"))["material"]
    gray = sf.fingerprint(_png(tmp_path, _solid((130, 130, 130)), "g2.png"))["material"]
    assert white["chromatic_mono_index"] < 0.05   # blind: reads NOT-mono though it IS mono
    assert gray["chromatic_mono_index"] < 0.05


# ----------------------------- warmth -----------------------------

def test_warmth_warm_positive_cool_negative(tmp_path):
    warm = sf.fingerprint(_png(tmp_path, _solid((200, 140, 60)), "w.png"))["warmth"]["warmth_index"]
    cool = sf.fingerprint(_png(tmp_path, _solid(COOL), "c.png"))["warmth"]["warmth_index"]
    assert warm > 15
    assert cool < 0
    assert warm > cool


# ----------------------------- lighting -----------------------------

def test_lighting_flat_gray_has_no_range(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _solid(GRAY)))
    assert fp["lighting"]["range"] < 1.0
    assert fp["lighting"]["std"] < 1.0


def test_lighting_gradient_has_wide_range(tmp_path):
    col = np.linspace(0, 255, 100).astype(np.uint8)
    arr = np.repeat(col[:, None, None], 100, axis=1).repeat(3, axis=2)  # vertical 0..255 gradient
    fp = sf.fingerprint(_png(tmp_path, arr))
    assert fp["lighting"]["range"] > 50


# ----------------------------- black-hole cavity (the "รู" wound) -----------------------------

def test_black_hole_share_matches_black_fraction(tmp_path):
    arr = np.full((100, 100, 3), 255, np.uint8)
    arr[:10, :] = 0        # exactly 10% pure black; 100px edge < WORK_MAX_EDGE so no resize
    fp = sf.fingerprint(_png(tmp_path, arr))
    assert abs(fp["wounds"]["black_hole_share"] - 0.10) < 0.02


def test_black_hole_zero_when_no_black(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _solid((90, 90, 90))))  # dark-ish but > BLACK_LEVEL
    assert fp["wounds"]["black_hole_share"] == 0.0


# ----------------------------- RGBA compositing (must be WHITE, not black) -----------------------------

def test_rgba_transparent_composites_over_white(tmp_path):
    """A transparent render bg must read as neutral white -- NOT as a black-hole. Catches the
    classic alpha-over-black bug that would fabricate a 100% cavity on every transparent PNG."""
    rgba = np.zeros((60, 60, 4), np.uint8)  # fully transparent
    p = tmp_path / "t.png"
    Image.fromarray(rgba, "RGBA").save(p)
    fp = sf.fingerprint(str(p))
    assert fp["material"]["neutral_share"] > 0.95
    assert fp["wounds"]["black_hole_share"] < 0.05


# ----------------------------- privacy: no client name leaves LOCAL (LAW 1) -----------------------------

def test_private_path_client_name_scrubbed_from_all_output(tmp_path):
    """LOCAL-ONLY law: a client's paid work lives under _private/ with PERSONAL NAMES in the folder
    AND uploader-controlled filenames; the law forbids surfacing a name 'even inside a quoted
    filename'. fingerprint()/--json/--out must never carry it. This plants a name in BOTH the
    folder and the basename and asserts total absence (review 2026-07-15, finding 1, HIGH)."""
    secret = "SomchaiPrivateClientName"
    d = tmp_path / "_private" / "discord" / secret
    d.mkdir(parents=True)
    p = d / f"{secret}-master-bed.png"
    Image.fromarray(_solid(WOOD)).save(p)
    fp = sf.fingerprint(str(p))
    assert fp["ref"].startswith("private:")
    assert secret not in json.dumps(fp)              # full serialized fingerprint (== --json/--out)
    assert secret not in sf._safe_ref(str(p))        # the scrubber itself
    # our own (non-_private) render paths pass through readable, unharmed
    assert sf._safe_ref("projects/PRJ-2026-002/R_x.png") == "projects/PRJ-2026-002/R_x.png"


# ----------------------------- robustness: tiny image must not crash -----------------------------

def test_tiny_image_below_palette_k_does_not_crash(tmp_path):
    """fingerprint() is a public entry point; a <PALETTE_K-pixel image must not raise from KMeans
    (review 2026-07-15, finding 10). Out-of-domain for real renders, but a graceful metric, not a
    stack trace."""
    fp = sf.fingerprint(_png(tmp_path, _solid(WOOD, h=2, w=2)))  # 4 px < PALETTE_K (6)
    assert fp["palette"]["k"] == sf.PALETTE_K
    assert 0.0 <= fp["material"]["chromatic_mono_index"] <= 1.0


# ----------------------------- palette structural invariants -----------------------------

def test_palette_shares_sum_to_one(tmp_path):
    fp = sf.fingerprint(_png(tmp_path, _left_right(WOOD, COOL)))
    total = sum(c["share"] for c in fp["palette"]["clusters"])
    assert abs(total - 1.0) < 1e-3
    assert fp["palette"]["k"] == sf.PALETTE_K
    assert 0.0 <= fp["palette"]["entropy"] <= 1.0


# ----------------------------- determinism -----------------------------

def test_determinism_same_bytes_same_fingerprint(tmp_path):
    p = _png(tmp_path, _left_right(WOOD, COOL))
    a = json.dumps(sf.fingerprint(p), sort_keys=True)
    b = json.dumps(sf.fingerprint(p), sort_keys=True)
    assert a == b


# ----------------------------- frozen constants (silent recalibration guard) -----------------------------

def test_frozen_constants():
    """A silent change to any of these re-scores the whole corpus. If you meant to move one,
    change it here too -- deliberately -- so the drift is a diff, never invisible."""
    assert sf.FINGERPRINT_VERSION == "1.0"
    assert sf.WORK_MAX_EDGE == 400
    assert sf.PALETTE_K == 6
    assert sf.KMEANS_SEED == 0
    assert sf.KMEANS_N_INIT == 3          # feeds palette clustering + entropy
    assert sf.CHROMA_NEUTRAL == 10.0
    assert sf.BLACK_LEVEL == 16
    assert sf.HIGHLIGHT_L == 85.0         # feeds lighting.highlight_share (a compare() axis)
    assert sf.SHADOW_L_LO == 5.0          # feeds lighting.shadow_share
    assert sf.SHADOW_L_HI == 25.0


# ----------------------------- the de-wood real-image ACCEPTANCE tripwire -----------------------------

@pytest.mark.skipif(not (WALNUT.exists() and DEWOOD.exists()),
                    reason="VISIBLE SKIP: de-wood clay tripwire renders absent (LFS not pulled?)")
def test_tripwire_dewood_directional():
    """WEAK real-image corroboration, NOT a materials-only control (confound caught by looking at
    the PNGs 2026-07-15): walnut is Cam01_v01 on the brown feature wall with a bare block bed;
    de-wood is a DIFFERENT eye_camera on the fluted WHITE headboard with added furniture. So the
    drop below is material swap + camera + staging, NOT the material lever alone. The CONTROLLED
    anti-flattering evidence lives in the synthetic tests above. This only checks the fingerprint
    ranks these two real designer-graded frames in the expected direction:
      1. the designer-rejected brown frame reads MORE chromatic-mono than the whiter frame.
      2. the whiter frame has a larger neutral base.
      3. both frames carry ~0.1% near-black at the SAME order of magnitude (a magnitude sanity
         check -- NOT a same-cavity before/after, since the cameras differ)."""
    wal = sf.fingerprint(str(WALNUT))
    dew = sf.fingerprint(str(DEWOOD))
    d = sf.compare(wal, dew)
    # 1. mono-material drops, and by a real margin (not noise)
    assert d["chromatic_mono_index"]["a"] > d["chromatic_mono_index"]["b"]
    assert d["chromatic_mono_index"]["delta"] < -0.2
    # 2. neutral base grows
    assert d["neutral_share"]["delta"] > 0.2
    # 3. black-hole ~equal: same order of magnitude, and it must NOT VANISH -- a drop toward zero
    #    would be the metric rewarding the untouched cavity. Scaled to the axis's ~0.1% signal, NOT
    #    a fixed 0.01 that greenlights a drop-to-zero (review 2026-07-15, findings 7/14: the old
    #    absolute threshold was ~7x the signal and structurally could not fail in the flattering
    #    direction). Both must also stay small (neither render has a genuinely large black region).
    a3, b3 = d["black_hole_share"]["a"], d["black_hole_share"]["b"]
    assert a3 < 0.01 and b3 < 0.01                        # neither frame has a large black region
    assert 0.4 * a3 <= b3 <= 2.5 * a3, f"black-hole magnitude drifted: {a3} -> {b3}"
