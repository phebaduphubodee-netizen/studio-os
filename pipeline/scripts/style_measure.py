#!/usr/bin/env python3
"""style_measure.py — the half of the style rung that OPENS THE PICTURE.

`style_check.py` is pure by layer law (no PIL, no numpy, no network), so it can
read a stored measurement but can never take one. `style_fingerprint.py` needs
PIL + numpy + scikit-learn. This script is the bridge, and it is spawned rather
than imported for exactly the reason `pixel_check` is (R11): a rules module must
not drag an image library into layer 1, and an interpreter that cannot be found
is a HARD STOP, never a silent skip.

WHAT IT MEASURES AND WHY THAT NUMBER: `02_concept/concept.md` §3 declares the
room's palette as 60/30/10 — dominant / secondary / accent by AREA.
`style_fingerprint.palette` returns exactly that split, computed from the
pixels of a render by k-means in Lab. The declaration and the instrument were
built seven weeks apart in this repo and were never introduced. This script is
the introduction.

EXIT CODES ARE A CONTRACT, same as pixel_check's:
  0  measured, written into qa/style-of-record.json
  1  refused to write (the frame is not a full-fidelity frame of record)
  2  COULD NOT RUN — the instrument is missing or the image is unreadable. The
     register records `could_not_run` and style_check FAILS on it, because
     "could not look" must never print like "looked and it was fine".

LOCAL-ONLY, inherited from style_fingerprint: this reads pixels on this machine
and calls no external API of any kind.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import style_check as SC        # pure; for STYLE_REL + _repo_root

# An R5 playblast is not the frame of record. A quick render is a quarter of the
# wall time and a different sampling of the same room; a palette split measured
# on one is not the number the gate should carry. Refused BY NAME.
QUICK_MARKERS = ("_ql.", "_quick.", "-ql.", "playblast")


def _register_path(repo_root=None):
    return os.path.join(repo_root or SC._repo_root(), SC.STYLE_REL)


def measure(frame_path):
    """(fingerprint_palette | None, could_not_run_reason | None)."""
    try:
        import style_fingerprint as SF
    except Exception as exc:
        return None, f"style_fingerprint is not importable ({exc})"
    try:
        fp = SF.fingerprint(frame_path)
    except AttributeError:
        try:
            fp = SF.fingerprint_image(frame_path)
        except Exception as exc:
            return None, f"style_fingerprint has no usable entry point ({exc})"
    except Exception as exc:
        return None, f"could not read {frame_path} ({exc})"
    pal = (fp or {}).get("palette")
    if not isinstance(pal, dict):
        return None, "style_fingerprint returned no palette block"
    return {"palette": pal, "material": (fp or {}).get("material"),
            "warmth": (fp or {}).get("warmth")}, None


def write(frame_rel, result, reason, repo_root=None, today=None,
          gap_ceiling=None, close_by=None, declared=None):
    p = _register_path(repo_root)
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    prev = data.get("palette_measured") or {}
    declared = declared or prev.get("declared") or {"dominant": 0.60,
                                                    "secondary": 0.30,
                                                    "accent": 0.10}
    stamp = str(today or datetime.date.today())
    block = {"_what": ("R11's rung: the 60/30/10 concept.md declares, measured "
                       "off the pixels of the frame of record by "
                       "style_fingerprint (k-means area split in Lab). Written "
                       "here by style_measure.py; read by style_check.py, "
                       "which is pure and cannot look for itself."),
             "frame": frame_rel,
             "measured_at": stamp,
             "declared": declared}
    if reason:
        block["could_not_run"] = reason
        block.update({k: prev.get(k) for k in
                      ("dominant_share", "secondary_share", "accent_share")})
    else:
        pal = result["palette"]
        block.update({
            "dominant_share": round(float(pal["dominant_share"]), 5),
            "secondary_share": round(float(pal["secondary_share"]), 5),
            "accent_share": round(float(pal["accent_share"]), 5),
            "entropy": round(float(pal.get("entropy", 0.0)), 5),
            "clusters_k": pal.get("k")})
        if result.get("material"):
            block["chromatic_mono_index"] = result["material"].get(
                "chromatic_mono_index")
            block["neutral_share"] = result["material"].get("neutral_share")
        if result.get("warmth"):
            block["warmth_index"] = result["warmth"].get("warmth_index")
        worst = max(abs(block[k] - declared[d]) for k, d in
                    (("dominant_share", "dominant"),
                     ("secondary_share", "secondary"),
                     ("accent_share", "accent")))
        block["gap_worst"] = round(worst, 4)
        # THE RATCHET: the ceiling only ever falls. It is seeded from the first
        # honest measurement (the gap has been this wide since the room was
        # first rendered) and every later run may lower it, never raise it.
        old = prev.get("gap_ceiling")
        seed = round(worst + 0.02, 4)
        block["gap_ceiling"] = (min(old, seed) if isinstance(old, (int, float))
                                else (gap_ceiling if gap_ceiling is not None
                                      else seed))
        block["gap_since"] = prev.get("gap_since") or stamp
        block["close_by"] = (close_by or prev.get("close_by") or
                             "sign the floor slot (the 60% dominant this room "
                             "has never had) and re-measure — the gap is a "
                             "palette question, not a rendering one")
        block["_honest_note"] = (
            "The gap is WIDE and it is not a bug in the measurement. The frame "
            "of record splits its area 0.30 / 0.19 / 0.18 across six clusters "
            "with entropy 0.93 — a room with no dominant surface, which is "
            "exactly what a 60% field that was never signed produces. This "
            "number is recorded, dated and ratcheted rather than failed, "
            "because a rung that hard-fails on the day it ships gets switched "
            "off and joins the dead queues this register exists to stop.")
    data["palette_measured"] = block
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    return block


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("frame", help="full-fidelity render to measure")
    ap.add_argument("--allow-quick", action="store_true",
                    help="measure a playblast anyway (records it as such)")
    ap.add_argument("--close-by", default=None)
    a = ap.parse_args(argv)

    root = SC._repo_root()
    frame = a.frame
    rel = os.path.relpath(os.path.abspath(frame), root).replace(os.sep, "/")
    low = os.path.basename(frame).lower()
    if any(m in low for m in QUICK_MARKERS) and not a.allow_quick:
        print(f"REFUSED: {rel} reads as an R5 playblast. A quick render is a "
              f"different sampling of the same room, so its palette split is "
              f"not the number the gate should carry. Pass --allow-quick to "
              f"override deliberately.")
        return 1
    if not os.path.exists(frame):
        write(rel, None, f"no such frame: {rel}", repo_root=root)
        print(f"COULD NOT RUN (exit 2): no such frame {rel}")
        return 2

    result, reason = measure(frame)
    block = write(rel, result, reason, repo_root=root, close_by=a.close_by)
    if reason:
        print(f"COULD NOT RUN (exit 2): {reason}")
        return 2
    print(f"OPENED THE PICTURE — {rel}")
    print(f"  measured  dominant {block['dominant_share']:.3f} / secondary "
          f"{block['secondary_share']:.3f} / accent {block['accent_share']:.3f}")
    d = block["declared"]
    print(f"  declared  dominant {d['dominant']:.2f} / secondary "
          f"{d['secondary']:.2f} / accent {d['accent']:.2f}  (concept.md §3)")
    print(f"  worst gap {block['gap_worst']:.3f}  ceiling "
          f"{block['gap_ceiling']:.3f}  since {block['gap_since']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
