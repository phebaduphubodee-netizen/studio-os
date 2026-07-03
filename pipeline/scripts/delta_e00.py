#!/usr/bin/env python3
"""delta_e00.py — CIEDE2000 colour difference + brand-palette compliance.

The deterministic estimator behind Gate 3's brand check (blueprint §9.3
brand_qa.delta_e00: pass < 1.0, warn 1.0-2.0, > 2.0 = non-compliant; §12.2
"compliance is a gate, not a footnote"). Pure stdlib — the CIEDE2000 math is
exact and validated against the Sharma et al. (2005) reference vectors
(test_delta_e00.py), the canonical correctness proof for any ΔE00 implementation.

Two layers, matching the repair_loop injection design:
  - srgb_to_lab / ciede2000 — pure math, no image deps, fully testable.
  - brand_compliance(sampled, palette) — the gate decision over sampled colours.
Pixel sampling from a real render (Pillow) lives in the caller / repair_loop
adapter, so this module imports nothing beyond `math` and stays testable with
zero external deps or model files.

Refs: Sharma, G., Wu, W., & Dalal, E. N. (2005). The CIEDE2000 color-difference
formula. Color Research & Application, 30(1), 21-30.
"""
import math

# brand_qa thresholds mirror qa/thresholds.yaml (PR-controlled source of truth).
BRAND_PASS_MAX = 1.0   # brand_qa.delta_e00.pass_max
BRAND_WARN_MAX = 2.0   # brand_qa.delta_e00.warn_max  (> this = non-compliant)

# D65 reference white (2° observer), the sRGB assumed white point.
_XN, _YN, _ZN = 0.95047, 1.00000, 1.08883


def srgb_to_lab(rgb, assume_255=True):
    """sRGB -> CIE L*a*b* (D65). rgb = (r,g,b) in 0-255 (default) or 0-1."""
    r, g, b = rgb
    if assume_255:
        r, g, b = r / 255.0, g / 255.0, b / 255.0

    def _lin(c):
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = _lin(r), _lin(g), _lin(b)

    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / _XN
    y = (0.2126729 * r + 0.7151522 * g + 0.0721750 * b) / _YN
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / _ZN

    def _f(t):
        return t ** (1.0 / 3.0) if t > (6.0 / 29.0) ** 3 else t / (3 * (6.0 / 29.0) ** 2) + 4.0 / 29.0
    fx, fy, fz = _f(x), _f(y), _f(z)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def ciede2000(lab1, lab2, kL=1.0, kC=1.0, kH=1.0):
    """CIEDE2000 ΔE00 between two CIE L*a*b* colours (Sharma 2005 formulation)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # 1. C'
    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    Cbar = (C1 + C2) / 2.0
    Cbar7 = Cbar ** 7
    G = 0.5 * (1.0 - math.sqrt(Cbar7 / (Cbar7 + 25.0 ** 7)))
    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = math.hypot(a1p, b1)
    C2p = math.hypot(a2p, b2)

    # h' in [0, 360)
    def _hp(bp, ap):
        if bp == 0 and ap == 0:
            return 0.0
        h = math.degrees(math.atan2(bp, ap))
        return h + 360.0 if h < 0 else h
    h1p = _hp(b1, a1p)
    h2p = _hp(b2, a2p)

    # 2. ΔL', ΔC', ΔH'
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360.0
    else:
        dhp = h2p - h1p + 360.0
    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)

    # 3. weighting
    Lbarp = (L1 + L2) / 2.0
    Cbarp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbarp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbarp = (h1p + h2p) / 2.0
    elif (h1p + h2p) < 360:
        hbarp = (h1p + h2p + 360.0) / 2.0
    else:
        hbarp = (h1p + h2p - 360.0) / 2.0

    T = (1.0
         - 0.17 * math.cos(math.radians(hbarp - 30.0))
         + 0.24 * math.cos(math.radians(2.0 * hbarp))
         + 0.32 * math.cos(math.radians(3.0 * hbarp + 6.0))
         - 0.20 * math.cos(math.radians(4.0 * hbarp - 63.0)))
    dtheta = 30.0 * math.exp(-(((hbarp - 275.0) / 25.0) ** 2))
    Cbarp7 = Cbarp ** 7
    RC = 2.0 * math.sqrt(Cbarp7 / (Cbarp7 + 25.0 ** 7))
    SL = 1.0 + (0.015 * (Lbarp - 50.0) ** 2) / math.sqrt(20.0 + (Lbarp - 50.0) ** 2)
    SC = 1.0 + 0.045 * Cbarp
    SH = 1.0 + 0.015 * Cbarp * T
    RT = -math.sin(math.radians(2.0 * dtheta)) * RC

    dL = dLp / (kL * SL)
    dC = dCp / (kC * SC)
    dH = dHp / (kH * SH)
    return math.sqrt(dL * dL + dC * dC + dH * dH + RT * dC * dH)


def delta_e00_rgb(rgb1, rgb2, assume_255=True):
    """Convenience: ΔE00 straight from two sRGB triples."""
    return ciede2000(srgb_to_lab(rgb1, assume_255), srgb_to_lab(rgb2, assume_255))


def brand_compliance(sampled_labs, palette_labs,
                     pass_max=BRAND_PASS_MAX, warn_max=BRAND_WARN_MAX):
    """Gate 3 brand decision: each sampled colour must sit within ΔE00 of SOME
    approved palette colour. Returns a result dict.

    sampled_labs / palette_labs: lists of (L,a,b). Convert sRGB with srgb_to_lab
    first. Empty palette -> the check is NOT scored (status None) — the caller
    must treat that as UNWIRED, never a silent pass.
    """
    if not palette_labs or not sampled_labs:
        return {"status": None, "worst_delta": None, "per_color": [],
                "detail": "no palette or no sampled colours — not scored"}
    per = []
    for lab in sampled_labs:
        d = min(ciede2000(lab, p) for p in palette_labs)
        per.append(round(d, 4))
    worst = max(per)
    # Blueprint §9.3: pass < 1.0 | warn 1.0-2.0 | > 2.0 non-compliant. So exactly
    # pass_max (1.0) is WARN, not PASS — PASS is strict below pass_max.
    if worst > warn_max:
        status = "FAIL"
    elif worst >= pass_max:
        status = "WARN"
    else:
        status = "PASS"
    return {"status": status, "worst_delta": round(worst, 4), "per_color": per,
            "detail": f"worst ΔE00 {worst:.3f} vs palette "
                      f"(pass < {pass_max}, warn {pass_max}-{warn_max}, > {warn_max} non-compliant)"}


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        # quick invariants; full Sharma table lives in test_delta_e00.py
        assert abs(ciede2000((50, 2.5, 0), (50, 2.5, 0))) < 1e-12, "identity != 0"
        assert abs(ciede2000((50, 2.5, 0), (50, 0, -2.5))
                   - ciede2000((50, 0, -2.5), (50, 2.5, 0))) < 1e-12, "not symmetric"
        assert abs(ciede2000((50, 2.5, 0), (73, 25, -18)) - 27.1492) < 1e-3, "Sharma #17"
        print("delta_e00 selftest OK (identity, symmetry, Sharma #17)")
    else:
        a, b = (200, 60, 55), (190, 65, 60)
        print(f"ΔE00 {a} vs {b} = {delta_e00_rgb(a, b):.3f}")
