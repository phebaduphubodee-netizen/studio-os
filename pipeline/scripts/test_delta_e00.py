#!/usr/bin/env python3
"""test_delta_e00.py — CIEDE2000 validated against the Sharma et al. (2005) table.

The 34 published reference pairs are the canonical acceptance test for any
CIEDE2000 implementation — they specifically stress the hue-angle edge cases
(a*/b* near zero, ±180° wraparound) where naive implementations break. If all 34
match to 1e-4 and symmetry/identity hold, the formula is correct.

Run: python pipeline/scripts/test_delta_e00.py   (prints N/N, exit 0/1)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import delta_e00 as D  # noqa: E402

# (L1,a1,b1), (L2,a2,b2), expected ΔE00 — Sharma, Wu & Dalal (2005), Table 1.
SHARMA = [
    ((50.0000, 2.6772, -79.7751), (50.0000, 0.0000, -82.7485), 2.0425),
    ((50.0000, 3.1571, -77.2803), (50.0000, 0.0000, -82.7485), 2.8615),
    ((50.0000, 2.8361, -74.0200), (50.0000, 0.0000, -82.7485), 3.4412),
    ((50.0000, -1.3802, -84.2814), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, -1.1848, -84.8006), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, -0.9009, -85.5211), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, 0.0000, 0.0000), (50.0000, -1.0000, 2.0000), 2.3669),
    ((50.0000, -1.0000, 2.0000), (50.0000, 0.0000, 0.0000), 2.3669),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0009), 7.1792),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0010), 7.1792),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0011), 7.2195),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0012), 7.2195),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0009, -2.4900), 4.8045),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0010, -2.4900), 4.8045),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0011, -2.4900), 4.7461),
    ((50.0000, 2.5000, 0.0000), (50.0000, 0.0000, -2.5000), 4.3065),
    ((50.0000, 2.5000, 0.0000), (73.0000, 25.0000, -18.0000), 27.1492),
    ((50.0000, 2.5000, 0.0000), (61.0000, -5.0000, 29.0000), 22.8977),
    ((50.0000, 2.5000, 0.0000), (56.0000, -27.0000, -3.0000), 31.9030),
    ((50.0000, 2.5000, 0.0000), (58.0000, 24.0000, 15.0000), 19.4535),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.1736, 0.5854), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.2972, 0.0000), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 1.8634, 0.5757), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.2592, 0.3350), 1.0000),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((63.0109, -31.0961, -5.8663), (62.8187, -29.7946, -4.0864), 1.2630),
    ((61.2901, 3.7196, -5.3901), (61.4292, 2.2480, -4.9620), 1.8731),
    ((35.0831, -44.1164, 3.7933), (35.0232, -40.0716, 1.5901), 1.8645),
    ((22.7233, 20.0904, -46.6940), (23.0331, 14.9730, -42.5619), 2.0373),
    ((36.4612, 47.8580, 18.3852), (36.2715, 50.5065, 21.2231), 1.4146),
    ((90.8027, -2.0831, 1.4410), (91.1528, -1.6435, 0.0447), 1.4441),
    ((90.9257, -0.5406, -0.9208), (88.6381, -0.8985, -0.7239), 1.5381),
    ((6.7747, -0.2908, -2.4247), (5.8714, -0.0985, -2.2286), 0.6377),
    ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082),
]


def test_sharma_table():
    for i, (a, b, exp) in enumerate(SHARMA, 1):
        got = D.ciede2000(a, b)
        assert abs(got - exp) < 1e-4, f"Sharma #{i}: got {got:.4f}, expected {exp:.4f}"


def test_symmetry_and_identity():
    for a, b, _ in SHARMA:
        assert abs(D.ciede2000(a, b) - D.ciede2000(b, a)) < 1e-12, f"asymmetric: {a} {b}"
        assert D.ciede2000(a, a) == 0.0, f"identity nonzero: {a}"


def test_srgb_to_lab_anchors():
    L, a, b = D.srgb_to_lab((255, 255, 255))
    assert abs(L - 100) < 1e-2 and abs(a) < 1e-2 and abs(b) < 1e-2, f"white -> {(L, a, b)}"
    L0, _, _ = D.srgb_to_lab((0, 0, 0))
    assert abs(L0) < 1e-9, f"black L -> {L0}"
    # mid grey is achromatic: a,b ~ 0
    _, ag, bg = D.srgb_to_lab((119, 119, 119))
    assert abs(ag) < 1e-2 and abs(bg) < 1e-2, f"grey chroma -> {(ag, bg)}"


def test_brand_compliance_bands():
    palette = [D.srgb_to_lab((200, 60, 55))]           # a brand red
    exact = D.brand_compliance([D.srgb_to_lab((200, 60, 55))], palette)
    assert exact["status"] == "PASS" and exact["worst_delta"] == 0.0
    far = D.brand_compliance([D.srgb_to_lab((40, 120, 200))], palette)   # a blue
    assert far["status"] == "FAIL", far
    # empty palette must be 'not scored' (None) — never a silent pass
    none = D.brand_compliance([D.srgb_to_lab((0, 0, 0))], [])
    assert none["status"] is None


def test_band_boundaries_use_thresholds():
    # Blueprint §9.3: pass < 1.0 | warn 1.0-2.0 | > 2.0. Exactly 1.0 (pass_max) is
    # WARN, not PASS; a strictly-sub-1.0 delta is a clean PASS.
    base = (50.0, 2.5, 0.0)
    boundary = (50.0, 3.1736, 0.5854)   # Sharma pair -> ΔE00 == 1.0000 (== pass_max)
    assert D.brand_compliance([boundary], [base])["status"] == "WARN", "exactly 1.0 must be WARN, not PASS"
    near = D.srgb_to_lab((200, 60, 55))
    assert D.brand_compliance([near], [near])["status"] == "PASS"       # identical -> 0.0 < 1.0
    r2 = D.brand_compliance([(56.0, -27.0, -3.0)], [base])              # ΔE00 ~31.9 -> FAIL
    assert r2["status"] == "FAIL"


TESTS = [test_sharma_table, test_symmetry_and_identity, test_srgb_to_lab_anchors,
         test_brand_compliance_bands, test_band_boundaries_use_thresholds]


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
