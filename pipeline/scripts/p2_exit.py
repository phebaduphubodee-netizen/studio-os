"""p2_exit.py — the P2 reopened-bar exit harness (plan item P2r-7).

WHY A COMMAND AND NOT A RITUAL: the r7 exit measured two crops whose frames
lived in a session scratchpad; the method survived only because the gate
artifact happened to copy it out by hand. A bar that lives in a scratchpad
drifts back to two pre-chosen spots the next time someone is tired. This file
IS the bar: every 100% crop of P2's reopened exit test, with its box, its
method and its anchor DECLARED here, so closing P2 is one command anyone can
re-run.

BOXES ARE FROZEN BEFORE THE FRAMES THEY JUDGE. The duvet/wood/rug boxes were
declared 2026-08-11 from the p3r2 frame, before the p2r8 frame existed
(instrument-before-build, the program's own law). The throw box is the r7
record verbatim (gate-DELIV001-P2r7). Moving a box is a recorded decision,
never a convenience — that is exactly the drift this command exists to stop.

LOCAL-ONLY (R10b): the anchor is the friend's DELIVERED CLIENT WORK. The hard
line is git — anchor-side crops and ours-beside-anchor composites are written
under _private/deliv-001/p2-exit/ (gitignored) and never enter a commit or a
critique bundle. Only OUR-side crops land in the project stage dir. Sending an
anchor to an external vendor stays off by default (a judge shown the answer
stops being a judge).

EXIT CODES ARE A CONTRACT (R11): 0 = every rung ran and every DECLARED cut
holds · 1 = a declared cut is broken · 2 = COULD NOT RUN (missing file, a _ql
playblast, a scene dump without aabb) — and "could not look" must never print
like "looked and it was fine". Rungs whose bar is judged-beside-anchor (the
two energy crops) print their numbers and archive their crops; they cut
nothing here because the reopened bar cuts them at the critic clause, not at
a number. The rug edge graduated from that list at P2r-3: its cut is declared
on the crop registry with its grounding.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deliverable_check as dc  # noqa: E402  — pure (no bpy); _octave_energy + LE1600 normalise
import edge_shadow as es  # noqa: E402  — pure; the shadow-line physics + contact derivation

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE_DIR = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house",
                         "04_visualization", "p2-exit-crops")
PRIVATE_DIR = os.path.join(REPO, "_private", "deliv-001", "p2-exit")

# The one delivered-bedroom anchor this suite reads (I-23-023 #499473 — the
# same image the throw was judged against at r7 and the bed rank dimensions
# derive from). Repo-relative so the registry survives a checkout move.
ANCHOR_BEDROOM = os.path.join(
    REPO, "_private", "discord", "MY-DATA-PEAT", "โปรเจ็ก",
    "002_I-23-023-คุณแอ้ม", "files", "499473_Bedroom_1_main.png")

# name -> dict. Boxes are (x0, y0, x1, y1) fractions of the LONG-EDGE-1600
# normalised image (deliverable_check's own normalise rule: resolution must
# not buy detail — ours 2400 and the anchor's 3840 meet at the same 1600).
CROPS = {
    "duvet_fold": {
        "kind": "octave_energy",
        "asks": "fold-structure energy of the duvet beside the delivered comforter",
        "ours_box": (0.70, 0.55, 0.955, 0.73),   # right-flank drape, textile-only
        "anchor": ANCHOR_BEDROOM,
        "anchor_box": (0.30, 0.83, 0.52, 0.99),  # foreground comforter with loft
        "declared": "2026-08-11 from the p3r2 frame, before p2r8 existed",
        # SUBJECT ADDED 2026-08-26 (p2r79). Measured from the matmask on the two
        # frames this box has judged most recently: at p2r77 the box held 21%
        # duvet / 28% curtain_sheer / 22% floor, and at p2r78rc 15% duvet / 48%
        # curtain. The "2.1x the delivered comforter" this rung printed for
        # rounds was mostly CURTAIN PLEATS — vertical high-frequency structure
        # scored against their foreground comforter.
        "subject_materials": ("bed_duvet", "bed_coverlet", "Brown textured fabric"),
        "mask_material": ("bed_duvet", "bed_coverlet"),
    },
    "throw_weave": {
        "kind": "octave_energy",
        "asks": "weave detail energy of the foot-of-bed throw (r7 exit crop, kept as trend)",
        "ours_box": (0.45, 0.52, 0.68, 0.68),    # r7 record verbatim
        "anchor": ANCHOR_BEDROOM,
        "anchor_box": (0.30, 0.80, 0.47, 0.95),  # r7 record verbatim
        "declared": "r7 (gate-DELIV001-P2r7) — 1.126x at close",
        # p2r29 (pre-registered at r27, opened at r28's third drift): the r7 box
        # is FROZEN IN FRAME SPACE while the cloth under it re-bakes downstream
        # of every duvet change — a dead box measures composition drift, not
        # weave. The mask half scopes the SAME band-energy to the throw's own
        # rendered pixels (matmask id), eroded by the band's outer radius so
        # neighbours cannot bleed into the blur. Both halves print: the box
        # stays as the r7 trend line, the mask answers whether the cloth or
        # the crop moved.
        #
        # THE SITE IS NAMED, THE MATERIALS THAT CAN CARRY IT ARE LISTED
        # (2026-08-26, p2r79 — the same correction cloth_edge got at p2r41, and
        # it should have been made here in the same commit). This half named the
        # single string "bed_throw", the acquired set dresses the SAME object as
        # `acq_bed_throw`, and the lookup miss fell through to
        # `_absent_by_declaration` — so the rung printed "N/A BY DECLARATION,
        # absent by decision, not unmeasured" on a frame that renders the throw
        # at 888-1195 x 946-1078 px. Both critics on this very frame put that
        # object's fringe at #1 and #2 and Gemini named it the one thing to fix.
        # A DECLARED ABSENCE MUST BE CHECKED AGAINST THE MASK BEFORE IT PRINTS:
        # a material that has pixels is present, whatever the ledger says.
        "mask_material": ("bed_throw", "acq_bed_throw", "bed_coverlet"),
        "subject_materials": ("bed_throw", "acq_bed_throw", "bed_coverlet",
                              "bed_duvet", "Brown textured fabric"),
    },
    "wood_boards": {
        "kind": "autocorr",
        "asks": "two adjacent veneer panels: no periodic figure repeat above the noise floor",
        "ours_box": (0.24, 0.03, 0.46, 0.20),    # two bay back-panels, no contents
        "declared": "2026-08-11 from the p3r2 frame (C3#2 tiling = positive control)",
        # The one box that survived the camera move: 66% veneer at p2r77, 63% at
        # p2r78rc (the 17% that entered is `e5_pelmet`, the cove head that came
        # into frame with the ceiling). Kept as declared; the guard now says so
        # out loud instead of nobody knowing either way.
        "subject_materials": ("m_millwork_oak_veneer_photo", "m_mill_backing"),
    },
    "rug_edge": {
        "kind": "edge_profile",
        "asks": "rug boundary reads as a rolled-over edge, not a 90-degree step",
        # THE SITE IS DERIVED FROM THE MASK, NOT TYPED (2026-08-26, p2r79 —
        # cloth_edge's p2r41 correction, finally applied to the box that needed
        # it most). The rug's edge is a CONTACT between two materials, so the
        # registry names the pair and the frame says where it is. In image space
        # the floor lies ABOVE the rug at the rug's far edge.
        "contact": (("m_floor_oak_engineered_floor_photo", "Texture"),
                    ("m_floor_oak_engineered_floor_photo", "rug_pile"),
                    ("floor", "Texture")),
        "subject_materials": ("Texture", "rug_pile",
                              "m_floor_oak_engineered_floor_photo"),
        "declared": "2026-08-11 from the p3r2 frame; SITE RE-DERIVED 2026-08-26",
        # CUT DECLARED at P2r-3 (was report-only): an ideal step reads 0-1 px by
        # this rung's own first-crossing rule and a resample-sharp real step
        # 1-2 px (edge_rise_width docstring), so >= 3.0 px sits strictly above
        # the whole step band. Grounded before the cut went live: the frame it
        # judges read 5.0 px two consecutive rounds (p2r14/p2r15).
        "cut_rise_px": 3.0,
        "retired_box": {
            "ours_box": (0.06, 0.82, 0.32, 0.99),
            "why": "THE BOX NEVER HELD THE EDGE, and it passed the declared cut "
                   "for fifteen rounds by measuring something else. Measured from "
                   "the matmask: at p2r77 it held 50% bed_base, 29% acq_bench_seat, "
                   "12% rug and 8% bed_duvet -- 0.8% of it was the rug/floor "
                   "boundary this rung is named after, so `6.0 px -> ROLLED (pass)` "
                   "was the BED PLINTH's edge against the rug. At p2r78rc the "
                   "owner's camera (D-152) slid the same fractions onto 93% open "
                   "rug field with no far edge in it at all, and it printed "
                   "`4.0 px -> ROLLED (pass)` off pile noise. In the same frame "
                   "C3 filed the rug as reading flat with no visible edge or "
                   "thickness -- the eye and the instrument did not disagree, the "
                   "instrument was never pointed at the thing. Kept rather than "
                   "deleted: a retired box with no record is how the same site "
                   "gets re-typed next round (cloth_edge's own words, p2r41).",
        },
    },
    "garment_shells": {
        "kind": "dup_shells",
        "asks": "coincident duplicate garment shells in the built scene == 0",
        "declared": "2026-08-11 (p3r2 .blend probe found acq0==acq10 class pairs)",
    },
    "cloth_edge": {
        "kind": "shadow_contact",
        "asks": "where one bed cloth lies on another, the boundary CASTS A LINE "
                "(finite thickness) instead of reading as a tonal ramp",
        # THE SITE IS NAMED, NOT TYPED (p2r41). Ordered pair, upper over lower in
        # IMAGE space: the throw's far hem, the long line where it lies flat on the
        # duvet. That is the edge both critics named in their own words ("the grey
        # band and the white below it"). See `retired_box` for what this replaces.
        # The site is "an accessory cloth's hem lying FLAT on the field cloth". Its
        # material names differ by leg — the simulated leg dresses the field as
        # bed_throw, the acquired leg as bed_coverlet — so the registry names the
        # site and lists the pairs that can carry it. Every present pair is
        # measured and the WORST is the answer (see rung_shadow_contact).
        # `acq_bed_throw` ADDED 2026-08-26 (p2r79): the acquired leg dresses the
        # accessory cloth under that name and it renders at frame centre, so a
        # pair list without it made the site "not in this frame" and the rung
        # printed a signed absence over an object that is plainly there. Same
        # correction as the throw_weave mask half in this commit.
        "contact": (("bed_duvet", "bed_throw"),
                    ("bed_duvet", "acq_bed_throw"),
                    ("bed_duvet", "bed_coverlet")),
        # THE CONTROL IS PART OF THE RUNG, not an afterthought. A low score here means
        # "no edge" only if the test demonstrably fires on an edge that certainly
        # occludes; otherwise it means "could not see" (R11). This control is the
        # ACQUIRED pillow's sham hem lying on our own cloth: same frame, same light,
        # same class of contact, and a pillow indisputably occludes.
        # THE CONTROL LIST GREW 2026-08-26 (p2r79) BECAUSE THE ONLY CONTROL WENT
        # AWAY. D-138 records that the acquired headset arrives as ONE fused
        # mesh, so no surface wears `bed_pillow` any more and the rung refused
        # every frame for lack of a control — a correct refusal that had no way
        # back. These are added under the rung's own criterion, which is
        # CERTAINTY OF OCCLUSION and not material class: a bench and a bed
        # plinth stand ON the rug, so if this frame's light produces contact
        # darkening at all, it produces it there. `max` picks the strictest
        # control that fires, so a longer list can only make the ratio harder.
        "control_contact": (("bed_pillow", "bed_duvet"),
                            ("bed_pillow", "bed_coverlet"),
                            ("acq_bench_seat", "Texture"),
                            ("bed_base", "Texture")),
        # SAME OBJECT, OTHER EDGES - report-only, and they are what make the finding
        # an argument instead of a number. The throw's hanging edges line at 95-99%
        # while its lying-flat hem lines at 35%, so the cause is not the cloth, not
        # the material and not the light: it is that one hem.
        "sibling_contacts": (("bed_throw", "bed_coverlet"),
                             ("bed_coverlet", "bed_throw"),
                             ("bed_coverlet", "bed_duvet")),
        # Declared as a RATIO to the control so it survives a light change: an absolute
        # percentage would drift with exposure, a ratio is about geometry.
        "cut_ratio": 0.5,
        "declared": "2026-08-15 from the p2r34 frame, after both critics named the "
                    "boundary and edge_rise_width scored it the same as a real hem "
                    "(2-9 px hem, 5 px ours, 5 px control - a rung that cannot "
                    "separate them). SITE RE-DERIVED 2026-08-16 (p2r41); cut, method "
                    "and physics unchanged. Live at re-derivation, on p2r39: ours "
                    "36.0% of columns (median 2.7 codes, n=633) vs the acquired sham "
                    "hem at 88.7% = 0.406x, while the SAME throw's hanging edges read "
                    "98.8% (median 28.1) and 95.5% (median 28.4) in the same frame.",
        "retired_box": {
            "ours_box": (0.5208, 0.5444, 0.6875, 0.6111),
            "control_box": (0.6250, 0.7944, 0.7917, 0.8667),
            "why": "the box held ONE material. Measured from the matmask on its own "
                   "declaration frame (p2r34) and on p2r36/p2r39: 99.6% bed_throw, "
                   "0.4% bed_duvet - no cloth-on-cloth boundary inside it at all. It "
                   "scored 2.8% / 9.3% / 13.6% of columns and printed READS AS PAINT "
                   "each time, and the p2r39 gate cited that as the measurement "
                   "confirming C2 #5. A working control proved the METHOD could see; "
                   "nothing ever checked that the BOX HELD A BOUNDARY. Kept here "
                   "rather than deleted, because a retired box with no record is how "
                   "the same site gets re-typed next round.",
        },
    },
}


def _norm_img(path):
    return dc._norm(dc._load(path))


def _crop(im, box):
    w, h = im.size
    return im.crop((round(box[0] * w), round(box[1] * h),
                    round(box[2] * w), round(box[3] * h)))


def _lum_arr(im):
    return dc._lum(np.asarray(im, dtype=np.float64))


# ---------------------------------------------------------------- rungs

def _erode(mask, r):
    """Binary erosion by r px via iterated 4-neighbour min — no scipy."""
    m = mask.copy()
    for _ in range(int(r)):
        p = np.pad(m, 1, mode="constant", constant_values=False)
        m = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1]
             & p[1:-1, :-2] & p[1:-1, 2:])
    return m


def _names(v):
    """One material name or several. A rung names a SITE; the materials that can
    dress it differ by leg (simulated vs acquired), so every registry field that
    takes a material takes a list of the names that can carry the same site."""
    return (v,) if isinstance(v, str) else tuple(v)


# HOW MUCH OF A DECLARED BOX MUST ACTUALLY BE ITS OWN SUBJECT.
#
# WHY THIS NUMBER EXISTS AT ALL (p2r79). Every box in this registry is a
# FRACTION OF THE FRAME, and the frame's camera is not a constant: the owner
# adopted the room-contained camera on 2026-08-26 (D-152) and every frozen box
# slid onto different objects in the same move. Nothing checked. The rungs went
# on printing passes:
#   rug_edge   0.8% rug at p2r77, 3.9% at p2r78rc — it scored the BED PLINTH,
#              then open pile with no edge in the box, and printed ROLLED both times
#   duvet_fold  21% duvet at p2r77, 15% at p2r78rc — the rest curtain and floor,
#              so "2.1x the delivered comforter" was mostly curtain pleats
# This repo had already found the identical defect on ONE crop (cloth_edge's
# `retired_box`, p2r41: "a working control proved the METHOD could see; nothing
# ever checked that the BOX HELD A BOUNDARY") and fixed it as a note about that
# one box. R9b's law, which this file is now obeying: a rule that names the
# objects it applies to will always exempt the next one. So the check is
# universal — every box-based rung declares its subject and is refused when the
# box is not on it.
#
# THE FLOOR IS 0.50 and it is deliberately generous. This is not a quality bar,
# it is a CAN-I-SEE-IT bar: below half, the number a rung prints is mostly about
# something the rung is not named after, and "could not look" must never print
# like "looked and it was fine" (R11's exit-code contract). Every box that was
# genuinely on its subject clears it comfortably (wood_boards 63-66%); the two
# that were not do not come close.
SUBJECT_MIN_SHARE = 0.50


def _subject_share(id_arr, name_to_id, ours_im, box, materials):
    """(share, [(material, share)]) of a declared box that is actually the
    materials the box names, measured on the render's own matmask.

    The mask is native resolution and the boxes are fractions, so both are
    expressed as fractions here and no pixel-space comparison is made — two
    coordinate systems compared silently is its own defect class in this repo."""
    H, W = id_arr.shape
    x0, y0, x1, y1 = box
    sub = id_arr[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
    if sub.size == 0:
        return 0.0, []
    id_to_name = {i: n for n, i in name_to_id.items()}
    vals, counts = np.unique(sub, return_counts=True)
    occ = sorted(((id_to_name.get(int(v), f"id{int(v)}"), int(n) / sub.size)
                  for v, n in zip(vals, counts)), key=lambda t: -t[1])
    want = set(_names(materials))
    share = sum(s for n, s in occ if n in want)
    return share, occ[:4]


def _has_pixels(id_arr, name_to_id, materials):
    """Which of the named materials actually render in this frame.

    THE GUARD ON A DECLARED ABSENCE (p2r79). `_absent_by_declaration` reads a
    LEDGER, and a ledger is a claim about a decision, not about this frame. The
    throw's mask half printed "absent by decision, not unmeasured" for rounds
    while `acq_bed_throw` rendered 0.80% of the frame at its centre — the object
    both critics ranked first. A material with pixels is present, whatever the
    register says, and the register is then the thing that is wrong."""
    out = []
    for m in _names(materials):
        mid = name_to_id.get(m)
        if mid is not None and bool((id_arr == mid).any()):
            out.append(m)
    return out


def _absent_by_declaration(material):
    """(decision_id, why) when this material's object is absent BY A SIGNED
    DECISION, else None.

    The table lives in `value_ladder.DECLARED_ABSENT` — one owner for the fact,
    read by everything that needs it, rather than a second copy here that can
    drift. Both modules are pure python, so the import is free. A missing or
    unreadable table returns None, i.e. falls back to COULD NOT RUN, because the
    fail-closed direction is to keep reporting the unknown.

    WITH SEVERAL NAMES it answers only when EVERY one of them is declared absent.
    One present leg makes the site present, and a site that is present must be
    measured or reported unreadable — never waved through as signed."""
    got = []
    try:
        import value_ladder as _vl
        table = {obj.replace("bed__", "bed_"): v
                 for obj, v in getattr(_vl, "DECLARED_ABSENT", {}).items()}
    except Exception:                                   # pragma: no cover
        return None
    for name in _names(material):
        # EXACT ONLY. A looser match (endswith, contains) would silence a
        # REAL could-not-run on a neighbouring material, and that is the one
        # direction this function must never fail in — the whole point of
        # the exit-code contract is that an unknown stays an unknown.
        if name not in table:
            return None
        got.append(table[name])
    if not got:
        return None
    # several rows -> name every decision, so the gate cites what it leaned on
    ids = "+".join(sorted({d for d, _w in got}))
    return ids, got[0][1]


def rung_octave_mask(ours_im, render_path, spec, lo=4, hi=32):
    """The mask half of an octave rung: same band, same 3-pass blur, but the
    mean runs over the named material's OWN rendered pixels (matmask id),
    eroded by hi//2 so the box blur cannot pull neighbouring materials into
    the band. Returns (res, why_not) — exactly one is None."""
    base = render_path.rsplit(".", 1)[0]
    mj, mp = base + ".matmask.json", base + ".matmask.png"
    if not (os.path.exists(mj) and os.path.exists(mp)):
        return None, "no matmask beside the render"
    meta = json.load(open(mj, encoding="utf-8"))
    # ONE SITE, SEVERAL MATERIALS THAT CAN CARRY IT (p2r79). A single string was
    # a name lookup that missed whenever the same object shipped under another
    # leg's material — and the miss printed as a signed absence. Every listed
    # material that is PRESENT joins the mask; the absent ones are reported.
    wanted = _names(spec["mask_material"])
    present = {v: int(k) for k, v in meta.get("ids", {}).items() if v in wanted}
    if not present:
        return None, (f"none of {', '.join(wanted)} are in the matmask ids")
    # the mask png stores ids as value_probe's sRGB palette triples (levels of
    # 51), never raw indices — decode first, or every lookup reads channel
    # noise as "zero pixels"
    import value_probe as _vp
    ids = _vp.decode_ids(np.asarray(Image.open(mp).convert("RGB")))
    mask_full = np.zeros(ids.shape, dtype=bool)
    for mid in present.values():
        mask_full |= ids == mid
    if not mask_full.any():
        return None, f"{', '.join(present)} have zero pixels in the mask"
    # to LE1600 (the same normalise rule as the luminance), NEAREST — an id is
    # a label, interpolating one invents materials
    w, h = ours_im.size
    mask = np.asarray(Image.fromarray(mask_full.astype(np.uint8) * 255)
                      .resize((w, h), Image.NEAREST)) > 127
    core = _erode(mask, hi // 2)
    if core.sum() < 2000:
        return None, (f"eroded {'+'.join(present)} core is {int(core.sum())} px "
                      f"— too thin to band-measure")
    L = _lum_arr(ours_im)
    band = np.abs(dc._blur(L, lo // 2) - dc._blur(L, hi // 2))
    e_ours = float(band[core].mean())
    anchor_c = _crop(_norm_img(spec["anchor"]), spec["anchor_box"])
    e_anchor = dc._octave_energy(_lum_arr(anchor_c))
    ys, xs = np.nonzero(mask)
    return {"ours": round(e_ours, 4), "anchor": round(e_anchor, 4),
            "ratio": round(e_ours / max(e_anchor, 1e-9), 3),
            "mask_px": int(mask.sum()), "core_px": int(core.sum()),
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            }, None


def rung_octave(ours_im, spec):
    """The r7 throw-crop method: LE1600 -> textile-only crop -> _octave_energy
    (mean |band 4-32 px|, 3-pass — the only variant that survived its own noise
    negative control). Returns (ours, anchor, ratio). Report-only: the reopened
    bar judges these crops at the critic clause, not at a number."""
    ours_c = _crop(ours_im, spec["ours_box"])
    anchor_c = _crop(_norm_img(spec["anchor"]), spec["anchor_box"])
    e_ours = dc._octave_energy(_lum_arr(ours_c))
    e_anchor = dc._octave_energy(_lum_arr(anchor_c))
    return ours_c, anchor_c, {
        "ours": round(e_ours, 4), "anchor": round(e_anchor, 4),
        "ratio": round(e_ours / max(e_anchor, 1e-9), 3),
    }


def _median_filter_1d(p, win=9):
    """Odd-window running median, edges padded by reflection. No scipy — the
    profile is a few hundred samples and a plain loop is honest and fast."""
    r = win // 2
    pad = np.concatenate([p[r:0:-1], p, p[-2:-2 - r:-1]])
    return np.array([np.median(pad[i:i + win]) for i in range(len(p))])


_SURROGATES = 32
# A normalised autocorrelation cannot exceed 1.0, so a FLOOR at or above 1.0 is
# not a strict bar — it is a failed estimate, and any verdict read against it is
# "could not look" wearing the face of "looked and it was clear" (R11).
_FLOOR_IMPOSSIBLE = 1.0


def autocorr_peak(L, min_lag=24, despike_win=9):
    """Max normalised autocorrelation of the DESPIKED column-mean profile at
    lag >= min_lag, plus a noise floor from shuffled surrogates.

    THE ASK IS FIGURE TILING, NOT PANEL EDGES. Two adjacent boards carrying the
    same cathedral figure repeat along x at the panel pitch — but so do the
    panel SEAMS, which are real, correct geometry. A rung that cannot tell them
    apart calls every well-built cabinet a tiling defect. The separation is
    width: a seam is a 1-3 px dark line, the figure is broad streaks — so the
    column profile is despiked with a running median before the correlation,
    which removes narrow combs and keeps broad repeats (verified both ways in
    the tests' synthetic controls).

    The verdict is peak vs the measured floor of shuffled surrogates (same
    histogram, no spatial order), not peak vs zero. Returns (peak, lag, floor)."""
    a = L - L.mean(axis=1, keepdims=True)
    p0 = a.mean(axis=0)
    W = len(p0)
    # HOW FAR TO SEARCH, and this bound was WRONG for five rounds (D-056). It was
    # W // 2, which EXCLUDES lag = W/2 — the lag of a TWO-TILE repeat, i.e. exactly
    # the case "two adjacent boards carrying the same figure" describes when the crop
    # frames two boards. The rung reported `no peak above floor` on every round while
    # being structurally unable to see its own headline case; a cross-vendor critic
    # filed the tiling item six times against that clean.
    # Extending to 0.75W is not a loosened threshold, it is the range the estimator
    # already supports: `ac` below is divided by (W - lag), so each lag is normalised
    # by its OWN overlap and a half-crop overlap is an honest sample. Past ~0.75W the
    # overlap gets short enough that the estimate is mostly noise, so the tail stays
    # refused rather than trusted.
    # The floor moves with it: surrogates walk this identical path, so a wider search
    # gives shuffled noise the same extra chances to peak and the bar rises to match.
    hi = int(W * 0.75)
    if min_lag >= hi:
        return 0.0, 0, 0.0

    def _peak_of(raw):
        # THE SURROGATE WALKS THE SAME PIPELINE AS THE FRAME. The first version
        # despiked only the real profile and shuffled the despiked result — so
        # the median filter's own short-range smoothness counted as "structure"
        # the surrogate lacked, and pure noise read as periodic (caught by this
        # file's own noise control). Despike AFTER shuffling, normalise by the
        # surrogate's own variance, and the bias enters both sides equally.
        #
        # AND THE PEAK MUST BE A LOCAL MAXIMUM THAT ROSE FROM A VALLEY. The
        # first live run on p2r8 called the global max at exactly min_lag
        # "PERIODIC": the profile was a smooth monotonic decay (broad grain
        # correlates over tens of px — real wood, no repeat), and a global-max
        # rule reads the shoulder of that decay as a peak. A periodic figure
        # dips BETWEEN repeats and rises again at the pitch, so the rung now
        # demands rise-from-preceding-valley >= prom_min. Pinned by the
        # broad-gradient control in the tests.
        prof = _median_filter_1d(raw, despike_win)
        prof = prof - prof.mean()
        var = float((prof * prof).mean())
        if var < 1e-12:
            return 0.0, 0
        f = np.fft.rfft(prof, n=2 * W)
        ac = np.fft.irfft(f * np.conj(f))[:W] / (W - np.arange(W)) / var
        best, best_lag = 0.0, 0
        prom_min = 0.25
        for m in range(max(min_lag, 1), hi - 1):
            if not (ac[m] >= ac[m - 1] and ac[m] >= ac[m + 1]):
                continue
            rise = float(ac[m] - ac[min_lag:m + 1].min())
            if rise < prom_min:
                continue
            if float(ac[m]) > best:
                best, best_lag = float(ac[m]), m
        return best, best_lag

    peak, lag = _peak_of(p0)
    rng = np.random.default_rng(0)  # fixed seed: same frame -> same floor
    # HOW MANY SURROGATES, and why it is no longer 8. `mean + 3*sd` over 8 draws
    # puts a 3-sigma bar on top of an 8-sample sd, which is itself so noisy that
    # the bar wanders further than the thing it is meant to bound. MEASURED on a
    # PERFECT repeat (an image tiled with its own left half, peak 1.000 by
    # construction) across 12 surrogate seeds: at n=8 the floor ranged
    # 0.541-1.260 and 1 of 12 seeds landed ABOVE 1.000; at n=32, 0.625-0.980 and
    # none did. The shipped seed was 0 — the single seed of the twelve that
    # blocked a perfect repeat. Pinning a seed made the number reproducible
    # without making it right: a reproducible draw is still one draw.
    floors = [_peak_of(p0[rng.permutation(W)])[0] for _ in range(_SURROGATES)]
    floor = float(np.mean(floors) + 3.0 * np.std(floors))
    return peak, lag, floor


def rung_autocorr(ours_im, spec):
    """Periodic figure repeat in the declared crop, WITH THE POSITIVE CONTROL
    THAT PROVES THE RUNG COULD HAVE FOUND ONE.

    THE CONTROL IS PART OF THE RUNG, not an afterthought — this file's own law,
    written for cloth_edge and owed here since D-056. A clean reading from an
    absence test means "no repeat" only if the same estimator, on the same
    pixels, at the same resolution, demonstrably fires when a repeat IS there.
    Otherwise it means "could not see", and the two must never print alike (R11).
    The control is built from THIS crop: its own left half, duplicated. That
    makes it immune to the thing that would otherwise silence the rung — a
    camera change altering the crop's pixel pitch until the repeat falls under
    `min_lag` or inside the despike window, which is exactly what a wider lens
    does to a slat wall."""
    c = _crop(ours_im, spec["ours_box"])
    L = _lum_arr(c)
    peak, lag, floor = autocorr_peak(L)
    half = L.shape[1] // 2
    res = {"peak": round(peak, 3), "lag_px": lag, "floor": round(floor, 3),
           "periodic": peak > floor}
    if half >= 24:
        cp, cl, cf = autocorr_peak(np.concatenate([L[:, :half], L[:, :half]],
                                                  axis=1))
        res.update(control_peak=round(cp, 3), control_lag=cl,
                   control_floor=round(cf, 3), control_fired=cp > cf)
    else:
        res.update(control_fired=False,
                   control_why="crop too narrow to build a tiled control")
    # A FLOOR AT OR ABOVE 1.0 IS NOT A HIGH BAR, IT IS A BROKEN MEASUREMENT.
    # Found the only way it could be — by running the control and watching a
    # perfect self-tiled repeat score peak 1.000 against floor 1.260 and print
    # `not periodic`. Refuse rather than report: the whole point of the D-056
    # control is that a clean absence has to be earned, and a floor the signal
    # cannot reach by construction means the rung never had the chance to fail.
    for _tag, _f in (("frame", floor), ("control", res.get("control_floor"))):
        if _f is not None and _f >= _FLOOR_IMPOSSIBLE:
            res["could_not_run"] = (
                f"the {_tag} noise floor came back {_f:.3f}, at or above the 1.0 "
                f"ceiling a normalised autocorrelation cannot exceed — the "
                f"surrogate estimate failed, so this crop has NO verdict. Widen "
                f"the crop or raise _SURROGATES; never read the clean as a pass.")
            res["periodic"] = None
            break
    return c, None, res


def edge_rise_width(L, lo_frac=0.1, hi_frac=0.9):
    """Median 10-90% rise width (px) of the strongest vertical transition per
    column. A resample-sharp 90-degree step reads ~1-2 px; a rolled-over edge
    reads wider and asymmetric. Cut declared at P2r-3 (see the crop registry)."""
    H, W = L.shape
    widths = []
    for x in range(W):
        col = L[:, x]
        g = np.abs(np.diff(col))
        if g.max() < 4.0:          # no real edge in this column
            continue
        y = int(np.argmax(g))
        a, b = max(0, y - 12), min(H - 1, y + 13)
        seg = col[a:b]
        v0, v1 = seg[0], seg[-1]
        if abs(v1 - v0) < 8.0:
            continue
        # first-crossing 10%/90% (an ideal step crosses both at the same sample
        # and reads 0-1 px — the between-samples count read an ideal step as
        # "no transition", which is the vacuous-NaN twin of the vacuous zero)
        s = (seg - v0) / (v1 - v0)
        i_lo = int(np.argmax(s >= lo_frac))
        i_hi = int(np.argmax(s >= hi_frac))
        if s[i_lo] >= lo_frac and s[i_hi] >= hi_frac and i_hi >= i_lo:
            widths.append(i_hi - i_lo)
    return float(np.median(widths)) if widths else float("nan")


def _contact_strip(L, cols, half=16):
    """A RECTIFIED strip: one column per contact column, each vertically centred
    on THAT column's own contact row.

    A rug's far edge recedes across the frame, so a plain rectangular crop of a
    sloped boundary is mostly not-the-boundary and `edge_rise_width`'s per-column
    argmax then finds whatever else is in the column. Straightening the line
    first is what makes the per-column measurement about the edge itself.
    Columns whose window would leave the image are dropped, not clamped —
    clamping would silently measure a different offset."""
    H, W = L.shape
    keep = [x for x in sorted(cols)
            if 0 <= x < W and half <= cols[x] < H - half]
    if not keep:
        return None
    return np.stack([L[cols[x] - half:cols[x] + half + 1, x] for x in keep],
                    axis=1)


def rung_edge(ours_im, spec, id_arr=None, name_to_id=None):
    """Rise width of the boundary this rung is named after.

    THE SITE COMES FROM THE MASK WHEN THE REGISTRY NAMES A CONTACT (p2r79), and
    from the declared box only when it does not. A box is a coordinate: it
    encodes where the edge WAS under one camera, and stays perfectly legal after
    the camera moves — which is R9's law about typed positions, in image space.
    Returns (archive_crop, None, res); res carries `site` so the gate line says
    which of the two it measured."""
    if spec.get("contact") and id_arr is not None:
        best, best_pair = None, None
        for pair in _pairs(spec["contact"]):
            try:
                cols = _contact_in(ours_im, id_arr, name_to_id, pair)
            except es.NoFeature:
                continue
            if cols and (best is None or len(cols) > len(best)):
                best, best_pair = cols, pair
        if not best:
            return None, None, {"rise_px_median": None, "site": "contact",
                                "could_not_run": (
                                    "no contact columns for any declared pair "
                                    + " / ".join(" over ".join(p) for p in
                                                 _pairs(spec["contact"])))}
        strip = _contact_strip(_lum_arr(ours_im), best)
        if strip is None or strip.shape[1] < 20:
            return None, None, {"rise_px_median": None, "site": "contact",
                                "could_not_run": "contact line too near the "
                                                 "frame edge to window"}
        w = edge_rise_width(strip)
        # AND WHETHER IT CASTS A LINE, report-only (p2r79). Rise width alone is
        # ONE-SIDED: the cut refuses a hard 90-degree step, and a rug that is
        # only a colour change painted on the floorboards gives a WIDE soft ramp
        # that sails past it. On the frame this was written against, C3 filed the
        # rug as "flat, part of the floor, no thickness, no edge" in the same
        # round the rung printed ROLLED. An object with thickness darkens the
        # floor where it meets it; a texture swap cannot. The number prints so
        # the eye and the instrument are arguing about the same thing — it cuts
        # nothing until it has been read beside anchors (R4).
        pct, med, n = es.shadow_line_at(_lum_arr(ours_im), best)
        return (_contact_crop(ours_im, best), None,
                {"rise_px_median": round(w, 2) if w == w else None,
                 "site": " over ".join(best_pair), "cols": len(best),
                 "line_pct": round(pct, 1), "line_med": round(med, 1),
                 "line_n": n})
    c = _crop(ours_im, spec["ours_box"])
    w = edge_rise_width(_lum_arr(c))
    return c, None, {"rise_px_median": round(w, 2) if w == w else None,
                     "site": "declared box"}


def rung_shadow_line(ours_im, spec):
    """Does the declared boundary CAST A LINE, or is it a tonal ramp?

    Delegates the measurement to `edge_shadow` so the physics lives in one place and
    carries its own tests. The rung's job here is to run the CONTROL in the same frame
    and express the result as a ratio — an absolute dip percentage would move with
    exposure, while the ratio to a certainly-occluding edge is about geometry.

    Returns (ours_crop, control_crop, res). res["ran"] is False when the control did
    not fire: then the frame's absence is UNREAD, and the caller must print
    could-not-run rather than a pass."""
    import edge_shadow as es
    co = _crop(ours_im, spec["ours_box"])
    cc = _crop(ours_im, spec["control_box"])
    o_pct, o_med, o_n = es.shadow_line(_lum_arr(co))
    c_pct, c_med, c_n = es.shadow_line(_lum_arr(cc))
    res = {"ours_pct": round(o_pct, 1), "ours_med": round(o_med, 1), "ours_n": o_n,
           "control_pct": round(c_pct, 1), "control_med": round(c_med, 1),
           "control_n": c_n, "ran": c_pct >= es.CONTROL_MIN_PCT}
    res["ratio"] = round(o_pct / c_pct, 3) if c_pct else None
    return co, cc, res


def _decoded_matmask(render_path):
    """(id array, {material name: id}) from the matmask beside a render, or
    (None, why). Shared by every rung that needs to know WHAT it is looking at
    rather than only WHERE it is looking."""
    base = render_path.rsplit(".", 1)[0]
    mj, mp = base + ".matmask.json", base + ".matmask.png"
    if not (os.path.exists(mj) and os.path.exists(mp)):
        return None, "no matmask beside the render"
    import value_probe as _vp
    meta = json.load(open(mj, encoding="utf-8"))
    ids = _vp.decode_ids(np.asarray(Image.open(mp).convert("RGB")))
    return (ids, {v: int(k) for k, v in meta.get("ids", {}).items()}), None


def _contact_in(ours_im, id_arr, name_to_id, pair):
    """Contact columns for an ordered material pair, expressed in `ours_im`'s
    pixel space. The mask is native resolution and the measurement runs on the
    LE1600 normalise (deliverable_check's rule), so the scale is applied HERE,
    once and visibly - two coordinate systems compared silently is its own
    defect class in this repo."""
    upper, lower = pair
    if upper not in name_to_id:
        raise es.NoFeature(f"material {upper!r} is not in the matmask")
    if lower not in name_to_id:
        raise es.NoFeature(f"material {lower!r} is not in the matmask")
    native = es.contact_columns(id_arr, name_to_id[upper], name_to_id[lower])
    H, W = id_arr.shape
    w1, h1 = ours_im.size
    sx, sy = w1 / float(W), h1 / float(H)
    grouped = {}
    for x, y in native.items():
        grouped.setdefault(int(round(x * sx)), []).append(int(round(y * sy)))
    return {x: int(np.median(v)) for x, v in grouped.items()}


def _contact_crop(ours_im, cols, pad=18):
    """The archived 100% crop for a derived site: the contact's own bounding box
    plus a margin, so a human opening the gate sees the line the number is about
    (R11 - a rung that only prints a number cannot be checked by eye)."""
    xs = sorted(cols)
    ys = [cols[x] for x in xs]
    w, h = ours_im.size
    box = (max(0, min(xs) - pad), max(0, min(ys) - pad),
           min(w, max(xs) + pad + 1), min(h, max(ys) + pad + 1))
    return ours_im.crop(box)


def _pairs(v):
    """One ordered pair, or a list of them. A site may be dressed differently on
    two legs of the same lane (the bed's accessory-on-field contact is
    duvet-over-throw when the cloth is simulated and duvet-over-coverlet when it is
    acquired), so the registry names the SITE and lists the material pairs that can
    carry it."""
    return [tuple(v)] if v and isinstance(v[0], str) else [tuple(p) for p in v]


def _measure_pairs(ours_im, L, id_arr, name_to_id, pairs):
    """[(name, pct, med, n)] for every pair PRESENT in this frame, and the reasons
    the others were not measurable."""
    got, missed = [], []
    for pair in pairs:
        nm = " over ".join(pair)
        try:
            cols = _contact_in(ours_im, id_arr, name_to_id, pair)
            pct, med, n = es.shadow_line_at(L, cols)
        except es.NoFeature as e:
            missed.append((nm, str(e)))
            continue
        got.append((nm, pct, med, n, cols))
    return got, missed


def rung_shadow_contact(ours_im, render_path, spec):
    """Does the NAMED contact cast a line? The site comes from the render's own
    material mask, never from a typed box.

    Where the registry lists several material pairs for one site, EVERY present pair
    is measured and the WORST is the rung's answer, while all of them print. Taking
    the worst is deliberate: picking the best-scoring present pair would be
    contact-shopping, the same flattering-selection this repo has paid for in nine
    other shapes. Controls go the other way for the same reason — the STRICTEST
    control that fires is the reference, so the ratio can only get harder.

    Returns (ours_crop, control_crop, res) or (None, None, {"could_not_run": why}).
    res["ran"] is False when the control did not fire - then the frame's absence
    is UNREAD and the caller must print could-not-run rather than a pass."""
    got, why = _decoded_matmask(render_path)
    if got is None:
        return None, None, {"could_not_run": why}
    id_arr, name_to_id = got
    L = _lum_arr(ours_im)
    ours, ours_missed = _measure_pairs(ours_im, L, id_arr, name_to_id,
                                       _pairs(spec["contact"]))
    ctrl, ctrl_missed = _measure_pairs(ours_im, L, id_arr, name_to_id,
                                       _pairs(spec["control_contact"]))
    if not ours:
        missing = sorted({m for pr in spec["contact"] for m in pr
                          if m not in name_to_id})
        return None, None, {"could_not_run": "; ".join(f"{n}: {w}"
                                                       for n, w in ours_missed),
                            "missing_materials": missing}
    if not ctrl:
        return None, None, {"could_not_run": "no control contact in this frame — "
                            + "; ".join(f"{n}: {w}" for n, w in ctrl_missed)}
    o_name, o_pct, o_med, o_n, oc = min(ours, key=lambda r: r[1])
    c_name, c_pct, c_med, c_n, cc = max(ctrl, key=lambda r: r[1])
    res = {"ours_pct": round(o_pct, 1), "ours_med": round(o_med, 1), "ours_n": o_n,
           "control_pct": round(c_pct, 1), "control_med": round(c_med, 1),
           "control_n": c_n, "ran": c_pct >= es.CONTROL_MIN_PCT,
           "contact": o_name, "control": c_name,
           "also_present": [{"contact": n, "pct": round(p, 1), "med": round(m, 1),
                             "n": k} for n, p, m, k, _ in ours if n != o_name],
           "not_in_frame": [n for n, _ in ours_missed + ctrl_missed]}
    res["ratio"] = round(o_pct / c_pct, 3) if c_pct else None
    sib_got, sib_missed = _measure_pairs(ours_im, L, id_arr, name_to_id,
                                         _pairs(spec.get("sibling_contacts", ())) 
                                         if spec.get("sibling_contacts") else [])
    res["siblings"] = ([{"contact": n, "pct": round(p, 1), "med": round(m, 1),
                         "n": k} for n, p, m, k, _ in sib_got]
                       + [{"contact": n, "why_not": w} for n, w in sib_missed])
    return _contact_crop(ours_im, oc), _contact_crop(ours_im, cc), res


def rung_dup_shells(scene_path):
    """Coincident duplicate shells among acquired garment/prop meshes, from the
    BUILT scene dump (never the spec — the file that renders is the file of
    record). Two records in the same item whose world AABBs agree to 0.1 mm on
    all six numbers are one mesh imported twice. CUT: count == 0."""
    with open(scene_path, encoding="utf-8") as f:
        d = json.load(f)
    objs = [o for o in d.get("objects", []) if "__acq" in o.get("name", "")]
    missing = [o["name"] for o in objs if "aabb" not in o]
    if missing:
        return None, {"could_not_run": f"scene dump has no aabb on {len(missing)} "
                      f"acquired records (pre-aabb dump) — rerun the build"}
    pairs = []
    by_item = {}
    for o in objs:
        stem = o["name"].split("__acq")[0]
        by_item.setdefault(stem, []).append(o)
    for stem, group in by_item.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = np.asarray(group[i]["aabb"], dtype=np.float64).ravel()
                b = np.asarray(group[j]["aabb"], dtype=np.float64).ravel()
                if a.shape == b.shape and np.all(np.abs(a - b) < 1e-4):
                    pairs.append((group[i]["name"], group[j]["name"]))
    return pairs, {"coincident_pairs": len(pairs)}


# ---------------------------------------------------------------- driver

def _save(im, *path):
    p = os.path.join(*path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    return os.path.relpath(p, REPO)


def _composite(ours_c, anchor_c):
    h = max(ours_c.size[1], anchor_c.size[1])
    w = ours_c.size[0] + anchor_c.size[0] + 4
    out = Image.new("RGB", (w, h), (20, 20, 20))
    out.paste(ours_c, (0, 0))
    out.paste(anchor_c, (ours_c.size[0] + 4, 0))
    return out


def run(render_path, scene_path=None, only=None, tag=None):
    base = os.path.basename(render_path)
    if base.rsplit(".", 1)[0].endswith("_ql"):
        print("P2-EXIT COULD NOT RUN: a _ql playblast is not the deliverable's "
              "size — a sub-pixel crop at half resolution is a different "
              "measurement (R5/R11). Render full fidelity first.")
        return 2
    if not os.path.exists(render_path):
        print(f"P2-EXIT COULD NOT RUN: no render at {render_path}")
        return 2
    tag = tag or base.rsplit(".", 1)[0].split("_")[-1]
    scene_path = scene_path or render_path.rsplit(".", 1)[0] + ".scene.json"
    ours_im = _norm_img(render_path)

    # ONE DECODE, SHARED. Every rung that needs to know WHAT it is looking at
    # rather than only WHERE reads this. It is fetched before the loop because
    # the subject guard below applies to every box-based rung — a check that is
    # fetched per-rung is a check somebody forgets to fetch for the next rung.
    mm, mm_why = _decoded_matmask(render_path)
    id_arr, name_to_id = mm if mm else (None, None)

    could_not = []
    broken = []
    keys = [only] if only else list(CROPS)
    for key in keys:
        spec = CROPS[key]
        kind = spec["kind"]
        # THE SUBJECT GUARD, and it runs before every box rung with no allowlist.
        # A declared box is a fraction of the frame; the camera under it is not a
        # constant (D-152 moved it on 2026-08-26 and every box slid with it).
        # A rung whose box is not on its own subject has not measured that
        # subject, and must say so rather than print a number about something
        # else. See SUBJECT_MIN_SHARE for what this cost before it existed.
        box_blind = None
        if spec.get("ours_box") and spec.get("subject_materials"):
            if id_arr is None:
                could_not.append((key, f"subject unverifiable: {mm_why}"))
                print(f"[{key}] COULD NOT RUN — cannot check the box is on its "
                      f"subject: {mm_why}")
                continue
            share, occ = _subject_share(id_arr, name_to_id, ours_im,
                                        spec["ours_box"],
                                        spec["subject_materials"])
            occ_s = ", ".join(f"{n} {s * 100:.0f}%" for n, s in occ)
            if share < SUBJECT_MIN_SHARE and not spec.get("contact"):
                # THE BOX IS BLIND, THE RUNG IS NOT NECESSARILY. A mask half
                # scopes the same measurement to the subject's own pixels and is
                # unaffected by where the camera put them, so it still runs and
                # still answers — the box half is what gets refused. Killing the
                # whole rung here would have thrown away the only reading that
                # survives a camera move.
                box_blind = (f"box is {share * 100:.1f}% its declared subject "
                             f"(needs >= {SUBJECT_MIN_SHARE * 100:.0f}%); under "
                             f"it: {occ_s}")
                print(f"[{key}] BOX COULD NOT RUN — the declared box is only "
                      f"{share * 100:.1f}% "
                      f"{'/'.join(_names(spec['subject_materials']))}; what is "
                      f"actually under it: {occ_s}")
                if not spec.get("mask_material"):
                    could_not.append((key, box_blind))
                    continue
            else:
                print(f"[{key}] subject check: box is {share * 100:.1f}% its own "
                      f"subject (floor {SUBJECT_MIN_SHARE * 100:.0f}%) — {occ_s}")
        if kind == "dup_shells":
            if not os.path.exists(scene_path):
                could_not.append((key, f"no scene dump at {scene_path}"))
                print(f"[{key}] COULD NOT RUN — no scene dump at {scene_path}")
                continue
            pairs, res = rung_dup_shells(scene_path)
            if pairs is None:
                could_not.append((key, res["could_not_run"]))
                print(f"[{key}] COULD NOT RUN — {res['could_not_run']}")
                continue
            ok = res["coincident_pairs"] == 0
            if not ok:
                broken.append(key)
            print(f"[{key}] coincident duplicate pairs = {res['coincident_pairs']} "
                  f"-> {'PASS' if ok else 'FAIL'}"
                  + ("" if ok else " " + "; ".join(f"{a}=={b}" for a, b in pairs[:6])))
            continue
        if "anchor" in spec and not os.path.exists(spec["anchor"]):
            could_not.append((key, "anchor image missing (local-only pool)"))
            print(f"[{key}] COULD NOT RUN — anchor image missing")
            continue
        if kind == "octave_energy":
            if box_blind is None:
                ours_c, anchor_c, res = rung_octave(ours_im, spec)
                p1 = _save(ours_c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
                _save(anchor_c, PRIVATE_DIR, tag, f"{key}-anchor-100pct.png")
                _save(_composite(ours_c, anchor_c), PRIVATE_DIR, tag,
                      f"{key}-beside-anchor.png")
                print(f"[{key}] energy ours {res['ours']} vs anchor "
                      f"{res['anchor']} -> {res['ratio']}x  (crop: {p1}; "
                      f"composite: _private, local-only)")
            if spec.get("mask_material"):
                mres, why = rung_octave_mask(ours_im, render_path, spec)
                declared = _absent_by_declaration(spec.get("mask_material"))
                # THE MASK IS THE AUTHORITY ON WHETHER A MATERIAL IS IN THE
                # FRAME, and the ledger is consulted only when it is not
                # (p2r79). The two answer questions in DIFFERENT NAMESPACES:
                # `value_ladder.DECLARED_ABSENT` is keyed by OBJECT
                # (`bed__duvet`, `bed__throw`), while this rung names a
                # MATERIAL — and the lookup used to bridge them with a
                # `bed__`->`bed_` string mangle. On an ACQUIRED set that is
                # exactly backwards: D-086 declares the object `bed__duvet`
                # absent BECAUSE the bought set is one fused mesh, and D-138
                # says in its own words that that fused mesh WEARS `bed_duvet`.
                # So the material renders 6.99% of this frame while its object
                # is correctly signed absent. Asking the mask first makes the
                # collision impossible: pixels present -> measure them; no
                # pixels -> then a signed absence is a real answer.
                shown = (_has_pixels(id_arr, name_to_id, spec["mask_material"])
                         if id_arr is not None else [])
                if mres is None and declared and not shown:
                    # ABSENT ON PURPOSE IS NOT COULD-NOT-RUN. p2r44: his order
                    # put the bed cloth on the acquire path, the acquired set
                    # falls to the bed line itself, and the greige foot runner
                    # is gone by a decision row with a measurement behind it. A
                    # rung that reports a signed absence as "could not look"
                    # prints a permanent unknown that everybody learns to skip
                    # — which is how a real could-not-look stops being read.
                    print(f"[{key}] N/A BY DECLARATION {declared[0]} — the "
                          f"material this half measures is absent by decision, "
                          f"not unmeasured. {declared[1]}")
                elif mres is None:
                    if declared and shown:
                        why = (f"{why} — and note {declared[0]} declares this "
                               f"site absent while {', '.join(shown)} renders "
                               f"here: that row is about the OBJECT, this rung "
                               f"is about the MATERIAL, and neither answers the "
                               f"other")
                    could_not.append((key, f"mask half: {why}"
                                           + (f"; and {box_blind}" if box_blind
                                              else "")))
                    print(f"[{key}] MASK HALF COULD NOT RUN — {why} "
                          f"(the box number above is composition-blind trend, "
                          f"not a substitute)")
                else:
                    print(f"[{key}] mask-scoped "
                          f"({'+'.join(_names(spec['mask_material']))}): "
                          f"energy {mres['ours']} vs anchor {mres['anchor']} "
                          f"-> {mres['ratio']}x  ({mres['core_px']} core px of "
                          f"{mres['mask_px']}, bbox {mres['bbox']})"
                          + ("  [THE ANSWER — the declared box is blind on this "
                             "frame]" if box_blind else ""))
            elif box_blind:
                could_not.append((key, box_blind))
        elif kind == "autocorr":
            c, _, res = rung_autocorr(ours_im, spec)
            p1 = _save(c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            verdict = "PERIODIC (cut broken)" if res["periodic"] else "no peak above floor"
            if res["periodic"]:
                broken.append(key)
            print(f"[{key}] autocorr peak {res['peak']} @ lag {res['lag_px']}px "
                  f"vs floor {res['floor']} -> {verdict}  (crop: {p1})")
            if not res["periodic"] and not res.get("control_fired"):
                # a clean absence test whose control did not fire has not looked
                why = res.get("control_why") or (
                    f"tiled control read {res.get('control_peak')} vs floor "
                    f"{res.get('control_floor')}")
                could_not.append((key, f"positive control did not fire: {why}"))
                print(f"[{key}] COULD NOT RUN — clean, but the tiled positive "
                      f"control did not fire either ({why}); on these pixels "
                      f"this rung cannot tell 'no repeat' from 'cannot see'")
            elif res.get("control_fired"):
                print(f"[{key}]   positive control (this crop's own left half, "
                      f"tiled): peak {res['control_peak']} @ lag "
                      f"{res['control_lag']}px vs floor {res['control_floor']} "
                      f"-> fires, so the clean reading above is a reading")
        elif kind == "edge_profile":
            c, _, res = rung_edge(ours_im, spec, id_arr, name_to_id)
            w = res["rise_px_median"]
            cut = spec.get("cut_rise_px")
            if c is None or w is None:
                # no measurable transition where one was declared to be —
                # "could not look" must never print like "looked and it was fine"
                why = res.get("could_not_run") or (
                    f"no luminance transition at the site ({res.get('site')})")
                could_not.append((key, why))
                print(f"[{key}] COULD NOT RUN — {why}")
                continue
            p1 = _save(c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            if cut is not None:
                ok = w >= cut
                if not ok:
                    broken.append(key)
                print(f"[{key}] edge 10-90% rise width median = {w} px vs cut "
                      f">= {cut} -> {'ROLLED (pass)' if ok else 'STEP (cut broken)'}"
                      f"  [site: {res.get('site')}"
                      + (f", {res['cols']} contact columns" if "cols" in res else "")
                      + f"]  (crop: {p1})")
                if "line_pct" in res:
                    print(f"[{key}]   does it CAST A LINE: {res['line_pct']}% of "
                          f"columns (median {res['line_med']} codes, "
                          f"n={res['line_n']}) — report-only; a wide soft ramp "
                          f"passes the rise cut whether the object has "
                          f"thickness or is painted on")
            else:
                print(f"[{key}] edge 10-90% rise width median = {w} px  "
                      f"[site: {res.get('site')}] (report-only; crop: {p1})")

        elif kind == "shadow_contact":
            co, cc, res = rung_shadow_contact(ours_im, render_path, spec)
            if co is None:
                # ABSENT ON PURPOSE IS NOT COULD-NOT-RUN (the octave rung's own
                # law, p2r52): when every cloth a contact pair needs is gone by
                # a signed decision (the whole-bed winner ships no throw and no
                # coverlet — D-083/D-107), the site does not exist in this
                # frame's construction. A future set that carries the layer
                # re-enters the matmask and re-arms the rung by itself.
                missing = res.get("missing_materials") or []
                decs = {m: _absent_by_declaration(m) for m in missing}
                if missing and all(decs.values()):
                    ids = sorted({d[0] for d in decs.values()})
                    print(f"[{key}] N/A BY DECLARATION {'+'.join(ids)} — every "
                          f"cloth this contact needs ({', '.join(missing)}) is "
                          f"absent by decision, not unmeasured.")
                    continue
                could_not.append((key, res["could_not_run"]))
                print(f"[{key}] COULD NOT RUN - {res['could_not_run']}")
                continue
            p1 = _save(co, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            _save(cc, STAGE_DIR, tag, f"{key}-control-100pct.png")
            if not res["ran"]:
                could_not.append((key, f"control {res['control']} lined only "
                                       f"{res['control_pct']}% of its columns - the "
                                       f"test did not fire"))
                print(f"[{key}] COULD NOT RUN - control ({res['control']}) fired at "
                      f"only {res['control_pct']}% (needs >= 60%)")
            else:
                cut = spec.get("cut_ratio")
                ok = cut is None or res["ratio"] >= cut
                if not ok:
                    broken.append(key)
                print(f"[{key}] shadow line at {res['contact']}: ours "
                      f"{res['ours_pct']}% of columns (median {res['ours_med']} "
                      f"codes, n={res['ours_n']}) vs control {res['control']} "
                      f"{res['control_pct']}% -> {res['ratio']}x"
                      + (f" vs cut >= {cut} -> "
                         f"{'CASTS A LINE (pass)' if ok else 'NO LINE (cut broken)'}"
                         if cut is not None else " (report-only)")
                      + f"  (crop: {p1})")
                for s in res.get("also_present", ()):
                    print(f"[{key}]   same site, other dressing {s['contact']}: "
                          f"{s['pct']}% (median {s['med']} codes, n={s['n']}) — "
                          f"the WORST present pair is the answer above")
                for s in res.get("not_in_frame", ()):
                    print(f"[{key}]   declared pair not in this frame: {s}")
                for s in res.get("siblings", ()):
                    if "why_not" in s:
                        print(f"[{key}]   same object, other edge {s['contact']}: "
                              f"not measurable - {s['why_not']}")
                    else:
                        print(f"[{key}]   same object, other edge {s['contact']}: "
                              f"{s['pct']}% (median {s['med']} codes, n={s['n']})")

        elif kind == "shadow_line":
            co, cc, res = rung_shadow_line(ours_im, spec)
            p1 = _save(co, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            _save(cc, STAGE_DIR, tag, f"{key}-control-100pct.png")
            if not res["ran"]:
                # The control did not fire, so a low score here is "could not see",
                # not "no defect". Refusing is the whole reason the control is in
                # the rung (R11).
                could_not.append((key, f"control lined only {res['control_pct']}% "
                                       f"of its columns — the test did not fire"))
                print(f"[{key}] COULD NOT RUN — control fired at only "
                      f"{res['control_pct']}% (needs >= 60%)")
            else:
                cut = spec.get("cut_ratio")
                ok = cut is None or res["ratio"] >= cut
                if not ok:
                    broken.append(key)
                print(f"[{key}] shadow line: ours {res['ours_pct']}% of columns "
                      f"(median {res['ours_med']} codes) vs control "
                      f"{res['control_pct']}% -> {res['ratio']}x"
                      + (f" vs cut >= {cut} -> "
                         f"{'CASTS A LINE (pass)' if ok else 'READS AS PAINT (cut broken)'}"
                         if cut is not None else " (report-only)")
                      + f"  (crop: {p1})")

    print()
    if could_not:
        print(f"P2-EXIT: {len(could_not)} rung(s) COULD NOT RUN — this is not a "
              "pass: " + "; ".join(f"{k} ({why})" for k, why in could_not))
        return 2
    if broken:
        print(f"P2-EXIT: declared cut broken on: {', '.join(broken)}")
        return 1
    print("P2-EXIT: every rung ran; declared cuts hold (energy rungs are "
          "judged beside anchors at the critic clause, not here)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("render")
    ap.add_argument("--scene", default=None)
    ap.add_argument("--only", choices=sorted(CROPS), default=None)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    sys.exit(run(args.render, scene_path=args.scene, only=args.only, tag=args.tag))


if __name__ == "__main__":
    main()
