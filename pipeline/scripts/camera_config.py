#!/usr/bin/env python3
"""camera_config.py — interior eye-camera height as a cited, testable constant.

The suite eye-camera height was a bare literal `1.5` m inside build_room.py
(add_suite_eye_camera), COUPLED to a second bare literal `1.55` m — the height at/
above which a built-in blocks the LEVEL line-of-sight ray used to pick a standing
spot. Those two must move together: an object blocks a level ray at eye height H iff
it is taller than ~H. Hardcoding them independently is a latent bug — change one and
the LOS solve silently mismatches the actual camera height.

M3.2 designer calibration (2026-07-03, golden-set GS-15 note): a practicing designer
rejected the renders' camera as "too high — ฝ้าเพดานดูเตี้ย; ผมใช้ความสูงมุมกล้อง
ประมาณ 1.0–1.2 ม." So the default drops 1.5 -> 1.15 m (band midpoint) and the ray
threshold follows it (1.55 -> ~1.20).

stdlib-only + importable ON PURPOSE: build_room.py imports bpy at module top and is
NOT importable for a unit test; this tiny module is, so the height + its coupling are
pinned by test_camera_config.py.

A/B for a paid batch:
    EYE_CAM_HEIGHT_M=1.5 blender -b --python build_room.py -- spec.json   # old height
AESTHETIC confirmation is a DESIGNER render A/B, NOT the LLM judge — M3.2 proved the
judge decalibrated (too lenient vs a designer's eye); see qa/reports/
judge-calibration-2026-07-03-designer-notes.md. This module only encodes the
designer's stated value + guarantees the LOS threshold stays coupled.
"""
import os

DEFAULT_EYE_CAM_HEIGHT_M = 1.15        # designer 1.0–1.2 m (M3.2 GS-15); was 1.5
DESIGNER_BAND_M = (1.0, 1.2)
RAY_BLOCK_MARGIN_M = 0.05              # a built-in blocks the level ray if taller than
                                       # eye + margin (the old 1.55 = 1.5 eye + 0.05)


def eye_cam_height_m():
    """Resolved eye height: env override (for a render A/B) else the designer default."""
    try:
        return float(os.environ.get("EYE_CAM_HEIGHT_M", DEFAULT_EYE_CAM_HEIGHT_M))
    except (TypeError, ValueError):
        return DEFAULT_EYE_CAM_HEIGHT_M


def ray_block_min_h_m(eye_h=None):
    """Height at/above which a built-in blocks the LEVEL eye ray — coupled to eye
    height so the standing-spot LOS solve always matches where the lens actually is."""
    base = eye_cam_height_m() if eye_h is None else eye_h
    return base + RAY_BLOCK_MARGIN_M


# module-level resolved values build_room.py reads (per-invocation script, so
# reading env once at import is correct)
EYE_CAM_HEIGHT_M = eye_cam_height_m()
RAY_BLOCK_MIN_H_M = ray_block_min_h_m()


def select_aim_element(elements, aim):
    """Pick the element the --eye camera should frame for EYE_AIM=<substr> (see
    build_room.add_suite_eye_camera). Priority: EXACT kind, then EXACT name, then a
    substring of kind or name — so EYE_AIM=tv frames a wall 'tv' before a 'tv_console',
    not the first arbitrary match. `elements` is the search pool (items + builtins) in
    priority order. Returns the element, or None when `aim` is falsy (default camera
    behaviour). Raises ValueError when aim is set but nothing matches OR the match lacks
    a usable footprint (x/y/w/d) — build_room turns that into a loud SystemExit rather
    than a bare KeyError mid-render. Pure/importable, so it is unit-testable (build_room
    is not — it imports bpy)."""
    if not aim:
        return None
    aim = str(aim).strip().lower()
    if not aim:
        return None

    def kind(e):
        return str(e.get("kind") or "").lower()

    def name(e):
        return str(e.get("name") or "").lower()

    el = (next((e for e in elements if kind(e) == aim), None)
          or next((e for e in elements if name(e) == aim), None)
          or next((e for e in elements if aim in kind(e) or aim in name(e)), None))
    if el is None:
        raise ValueError(f"EYE_AIM={aim!r} matched no item/builtin by kind or name")
    for k in ("x", "y", "w", "d"):
        if el.get(k) is None:
            raise ValueError(f"EYE_AIM match {name(el) or kind(el) or '?'!r} lacks '{k}' "
                             f"— cannot aim the camera at it")
    return el
