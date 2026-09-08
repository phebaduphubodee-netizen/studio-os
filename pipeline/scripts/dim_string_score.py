#!/usr/bin/env python3
"""dim_string_score.py — SCORE THE READER AGAINST THE ONLY GROUND TRUTH ON THIS SHEET.

WHY THIS FILE EXISTS
====================
_private/_takeoff-012/living012_takeoff.json used to be the "answer key" the reader was scored
against. It is not one any more, and it never really was after 2026-07-12: its geometry was
CORRECTED BY COPYING THE READER'S OUTPUT. Rebase it by its own declared frame.origin and it is
byte-for-byte 012p3-room-auto.json — outline 0.0 mm on all four vertices, all three opening rects
exact. A reader-vs-that-file diff is ZERO BY CONSTRUCTION. It can never falsify. (12th
flattering-scorer recurrence in this project; see MEMORY.)

THE ONE GEOMETRY GT ON THIS SHEET THAT IS INDEPENDENT OF US IS THE PRINTED DIMENSION STRINGS.
The designer typed them, in CAD, years before this reader existed. They are in the PDF TEXT layer;
our reader reads the VECTOR layer and has never looked at them.

v0.2 -- WHAT ROUND 5's ADVERSARIAL REVIEW PROVED WAS WRONG WITH v0.1
====================================================================
v0.1 scored 40/48 = 83.3% and it was a REAL instrument in one respect: it collapsed on scale error
and on face loss. But the reviewer RAN three attacks and all three landed:

  (a) IT WAS EXACTLY INVARIANT TO THE READER ORIGIN. It scored face-pair DELTAS. Translate the
      whole building by any amount and NOTHING changed -- and an origin bug is precisely the bug
      that silently broke the OLD extractor on this very sheet.
  (b) IT REWARDED OVER-EXTRACTION. True faces + a 100 mm phantom grid scored 48/51 = 94.1%,
      HIGHER than the honest reader. More faces = more pairs = more chances to bracket a string.
  (c) ITS DENOMINATOR COULD EVAPORATE. Cripple the reader to 4 faces/axis and off-ink went 4 -> 49
      while `addressable` collapsed 48 -> 3. n_off_ink was reported and NOTHING GATED ON IT.

v0.2 answers each with material THE SHEET ALREADY CARRIES. The headline moved 83.3% -> 78.4%.
That is the honest number; nothing was tuned to preserve 83.3%.

------------------------------------------------------------------------------------------------
FIX (a) -- THE ORIGIN ANCHOR.  An ABSOLUTE datum, from the TEXT LAYER ONLY.
------------------------------------------------------------------------------------------------
FIRST, THE TRAP, because it is the whole reason this was hard: the reader's faces AND the printed
strings are BOTH mapped into mm through the SAME (scale, origin). So they CO-MOVE. *Any* quantity
that compares a text position to a face position is EXACTLY origin-invariant, and so is every
face-pair delta. An anchor that re-derives the origin from the reader's own faces is circular and
measures nothing. There is exactly one way out: compare a TEXT-ONLY quantity against an ABSOLUTE
CONSTANT that the FRAME ITSELF declares.

The frame declares one: **origin = the building's SW OUTER corner**, i.e. the datum face is
x = 0.0 and y = 0.0, by definition.

And the text layer alone can predict where that face is. A CAD dimension numeral is drawn CENTRED
on the span it dimensions (measured on this sheet: median centring residual 0.33 mm, MAD 2.65 mm,
over the 40 matched strings -- and that residual is itself origin-invariant, so measuring it is not
a way of tuning the origin test). So a string of value V whose centre sits at c predicts its span:

        [ c - V/2 ,  c + V/2 ]        <-- TEXT LAYER ONLY. No reader face is consulted.

The OVERALL string on an axis (the printed "7820" on x, "9720" on y) dimensions the building's
outer faces. Therefore its NEAR endpoint c - V/2 is a text-only estimate of the datum face, and
the frame says that face is 0.0. So:

        ORIGIN RESIDUAL(axis) = (c - V/2) - 0.0            must be ~0

Measured on the honest reader: x = +0.7 mm, y = +1.0 mm.
Shift the reader origin 50 mm and the strings' mm centres shift with it while the DECLARED datum
does not move -- because it is the number zero. Residual -> -49.3 mm / -49.0 mm. THE GATE FIRES.

Selecting the overall string is done ORIGIN-INDEPENDENTLY: it is the largest-value string on the
axis that still FITS INSIDE the wall-ink extent (this is the only place faces are touched, and
only to reject the site dim "30000", which is 30 m of plot and dimensions no wall). Selection
cannot be moved by a translation, so the residual it produces is a real measurement.

The second anchor is the EXTENT anchor and it is origin-INVARIANT by construction -- it catches
SCALE, not origin, and it is reported as such, never conflated:

        EXTENT RESIDUAL(axis) = (max_ink_face - min_ink_face) - V_overall    must be ~0

ANCHOR_TOL_MM = 12.0 is FROZEN and DERIVED, not tuned: 3 x robust-sigma of the numeral-centring
residual, sigma = 1.4826 x MAD = 1.4826 x 2.65 = 3.93 mm -> 11.8 -> 12.0. The live MAD is
recomputed and PRINTED every run as a drift tripwire; it does NOT feed back into the tolerance.

HONEST LIMIT, stated plainly: the origin anchor rests on TWO printed numbers (7820 and 9720). That
is thin. It is exactly why the anchor is a HARD GATE and not a soft term: if the frame is wrong,
every "match" below it is a coincidence in a wrong frame and the scorecard REFUSES TO REPORT A
SCORE rather than reporting a flattering one.

------------------------------------------------------------------------------------------------
FIX (b) -- THE PRECISION TERM.  Hallucinated faces must COST something.
------------------------------------------------------------------------------------------------
        face_precision = (faces that are an endpoint of some MATCHED pair) / (faces emitted)
        HEADLINE       = F1( recall , face_precision )

This is NOT a purity measure and it is not claimed to be one. An honest reader's ceiling here is
74.1% (43 of 58 faces used), because 15 real wall faces are simply not dimensioned by any string
on this sheet. The term exists for one job: to make a phantom face COST. It does. The 100 mm
phantom grid that used to score 94.1% now reads face_precision 11.4% and F1 20.4%.

------------------------------------------------------------------------------------------------
FIX (c) -- THE OFF-INK GATE.  The denominator cannot evaporate any more.
------------------------------------------------------------------------------------------------
A string is EXCUSED as off-ink only if it sits OUTSIDE THE PRINTED BUILDING FOOTPRINT on its own
axis -- and the footprint is [0, V_overall], taken from the OVERALL PRINTED STRINGS, not from the
reader's faces. So the excuse cannot follow the reader down.

        n_scoreable = matched + unmatched + off_ink_INSIDE          <-- INSIDE = A MISS

This is derived, not tuned, and it CHANGES NOTHING for the honest reader: all four of its off-ink
strings ("30000" site dim, and three "100"s beyond the outer faces) are outside the footprint
already. Cripple the reader to 4 faces/axis and off-ink goes 4 -> 49, but 45 of those are INSIDE
the building and are now MISSES: n_scoreable stays 48 and recall collapses to 3/48 = 6.2%.

------------------------------------------------------------------------------------------------
THE MATCHER (declared, and deliberately dumb -- the null is what makes it mean anything)
------------------------------------------------------------------------------------------------
A string of value V on axis A at position c MATCHES a pair of reader-extracted ink faces (f0, f1)
on axis A iff:
    (1) the string sits ON the span:  |c - (f0+f1)/2|  <=  (f1-f0)/2 + ext/2
        where ext is the numeral's OWN drawn extent along A. The slack is not a fudge factor: a
        "100" at 1:50 is ~2 pt of paper and the numeral is ~13 pt, so the draughtsman MUST park it
        outside the span it labels. The slack is exactly the room the numeral itself takes up.
    (2) |(f1 - f0) - V| <= TOL_MM.
Of all bracketing pairs, the one with the smallest error is taken.

Three buckets, and the bucket is DERIVED, not tuned:
    MATCHED     — a bracketing pair exists and its error is within tolerance.
    UNMATCHED   — a bracketing pair exists, but no pair reproduces V. THE FAILURE CHANNEL.
    OFF-INK     — NO face pair on that axis brackets the string at all. Split (v0.2) into
                  OUTSIDE the printed footprint (excused, not scored) and INSIDE it (A MISS).

THE NULLS — READ THEM BEFORE YOU BELIEVE THE HEADLINE (unchanged from v0.1, deliberately)
=========================================================================================
    PERMUTATION NULL — keep every string's POSITION and AXIS, shuffle the VALUES between them.
    RANDOM-DIMS NULL — same positions, values drawn uniformly (5 mm steps) from the observed range.
Both are still computed on the raw addressable match rate so they remain comparable to v0.1
(23.4% / 4.8%). They are the THIRD independent catch for over-extraction: a phantom grid drives
the permutation null through the roof and the verdict line prints NO SIGNAL.

RESIDUAL -- WHAT IS STILL GAMEABLE. READ THIS BEFORE QUOTING 78.5%.
==================================================================
I attacked my own fix (b) and it has a hole. It is the 13th flattering-scorer recurrence in this
project and I am naming it rather than quietly shipping around it.

  THE MINIMAL-READER ATTACK (`--mutate minimal-reader`, MEASURED, not hypothesised).
  Emit ONLY the 43 faces that some printed string actually uses, and DELETE the 15 real wall faces
  the designer never dimensioned. Both anchors pass. Recall is untouched at 83.3%. face_precision
  goes to 100.0%. F1 = 90.9% -- IT BEATS THE HONEST READER'S 78.5% BY DELETING REAL WALLS.

  Why it is not fixable with the material on this sheet: there is NO ground truth for an
  UNDIMENSIONED face. The printed strings are the only GT here and they say nothing about the 15
  walls they do not dimension. A precision term built on "faces the strings used" therefore cannot
  distinguish "did not hallucinate" from "deleted the evidence".

  Why it is nevertheless not a live threat to THIS reader, stated precisely: to mount it, a reader
  must know WHICH faces the strings use -- i.e. it must READ THE TEXT LAYER, which is the GT, and
  which bluehouse_plan_reader is architecturally forbidden from touching. Every reachable honest
  failure -- random face loss, early termination, calibration drift -- LOWERS the score (drop-half
  30.7%, cripple-4 refused, origin+50 refused). Only a reader that CHEATS is rewarded, and this
  scorecard cannot tell a cheat from an honest reader. That is a real limit, not a cleared one.

  What would close it: a face-level GT independent of the dimension strings -- i.e. score the
  reader's ink against the raster/vector wall poche itself, not against the text. That is a
  different instrument and it is the honest next lever.

Second, smaller: the ORIGIN anchor rests on TWO printed numbers (7820, 9720). If the designer had
mis-centred either overall string by >12 mm, the anchor would be wrong. Measured centring MAD on
this sheet is 2.65 mm and the two residuals are 0.7 and 1.0 mm, so it holds here -- but it is thin,
and that thinness is exactly why the anchor REFUSES rather than deducting.

Third: under a gross scale error (x1.02) the chain corroboration itself breaks, so no overall
string is found and the origin anchor reports UNAVAILABLE rather than a residual. It fails CLOSED
(no anchor -> no score), which is the right direction, but the scorecard is then telling you "I
cannot anchor this sheet", not "the origin is wrong".

CLIENT DATA. The PDF is client data. This script is LOCAL ONLY and prints geometry — never pipe
its output anywhere external.

Usage:
    python pipeline/scripts/dim_string_score.py <pdf> <page> [--tol-mm 2.0] [--perms 2000]
                                                [--json OUT] [--seed 7] [--mutate NAME]
    --mutate is the INSTRUMENT'S OWN TEST HARNESS (see MUTATIONS): it deliberately breaks the
    reader and shows you the scorecard notice. `--mutate list` prints them.
"""
import argparse
import bisect
import json
import os
import random
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fitz  # PyMuPDF

from bluehouse_plan_reader import (RefuseSheet, ink_faces, read_bands, to_mm_bands, to_mm_rect)

TOL_MM = 2.0                 # a printed dim is reproduced iff the face pair is within this
NUMERAL = re.compile(r"[0-9]{2,5}")
DIM_MIN_MM, DIM_MAX_MM = 50.0, 30000.0   # a plausible printed dimension on a residential sheet

# FROZEN, DERIVED (see module docstring, FIX (a)). 3 x robust-sigma of the ORIGIN-INVARIANT
# numeral-centring residual: sigma = 1.4826 * MAD.
#     MAD = 2.65 mm on raw face coordinates      -> 3 sigma = 11.8 mm
#     MAD = 2.90 mm on 0.1-mm-rounded faces      -> 3 sigma = 12.9 mm   (what the scorecard prints)
# 12.0 sits between them, i.e. slightly TIGHTER than 3 sigma of the number the scorecard itself
# reports. That is the conservative direction and it is deliberate. The live MAD is printed every
# run as a DRIFT TRIPWIRE and MUST NOT feed back into this constant: a tolerance that widens itself
# when the reader gets worse is not a tolerance, it is an alibi.
ANCHOR_TOL_MM = 12.0
_CALIBRATION_MAD_MM = 2.65   # what ANCHOR_TOL_MM was derived from; pinned by a test


def dim_strings(pdf, page_no, scale, x0, y0):
    """Every printed dimension string on the page, in the reader's own building frame.

    THE THAI BUG (checked, not assumed): this PDF's text layer splits Thai combining vowels/tone
    marks off their consonants, so Thai strings arrive mangled. The DIMENSION strings are pure
    ASCII numerals and are NOT affected -- but we do not take that on faith. `rejected_nonnumeric`
    counts every span we dropped, and `mixed_numeral_spans` names any span that CONTAINS digits but
    is not a clean numeral, which is what a mark-splitting bug would look like if it ever touched
    them. Both are printed in the scorecard.
    """
    doc = fitz.open(pdf)
    page = doc[page_no]
    out, mixed, rejected = [], [], 0
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            dx, dy = line["dir"]
            for span in line["spans"]:
                t = span["text"].strip()
                if not t:
                    continue
                if not re.fullmatch(r"[0-9]{2,5}", t):
                    rejected += 1
                    if NUMERAL.search(t):
                        mixed.append(t)
                    continue
                v = float(t)
                if not (DIM_MIN_MM <= v <= DIM_MAX_MM):
                    rejected += 1
                    continue
                r = to_mm_rect(span["bbox"], scale, x0, y0)
                axis = "x" if abs(dx) >= abs(dy) else "y"
                cx, cy = (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0
                out.append({
                    "text": t, "value_mm": v, "axis": axis,
                    "pos_mm": round(cx if axis == "x" else cy, 1),
                    "at_mm": [round(cx, 1), round(cy, 1)],
                    # the numeral's own drawn extent ALONG the axis it dimensions
                    "extent_mm": round((r[2] - r[0]) if axis == "x" else (r[3] - r[1]), 1),
                })
    doc.close()
    return out, mixed, rejected


def _best_pair_bruteforce(value, c, ext, faces):
    """The O(n^2) definition of the matcher. `best_pair` must agree with it EXACTLY -- pinned by
    test_the_fast_matcher_is_EXACTLY_the_slow_one. Kept because a speedup that quietly changes
    the score is the oldest way to fake progress in this repo."""
    best = None
    for i, f0 in enumerate(faces):
        for f1 in faces[i + 1:]:
            span = f1 - f0
            if abs(c - (f0 + f1) / 2.0) > span / 2.0 + ext / 2.0:
                continue                      # the numeral is not on this span
            err = abs(span - value)
            if best is None or err < best[0]:
                best = (err, f0, f1)
    return best


def best_pair(value, c, ext, faces):
    """The bracketing face pair that best reproduces `value`. None if NOTHING brackets the text.

    Identical to _best_pair_bruteforce, in O(n log n). The bracketing test rearranges exactly:
        |c - (f0+f1)/2| <= (f1-f0)/2 + ext/2   <=>   f0 <= c + ext/2  AND  f1 >= c - ext/2
    so for each admissible f0 the best f1 is the admissible face nearest f0+value, found by
    bisection. This matters because the 100 mm phantom-grid mutation has ~190 faces/axis and the
    permutation null runs the matcher hundreds of times.
    """
    if len(faces) < 2:
        return None
    hi_f0 = c + ext / 2.0
    lo_f1 = c - ext / 2.0
    best = None
    n = len(faces)
    for i, f0 in enumerate(faces):
        if f0 > hi_f0:
            break                                   # faces are sorted: no later f0 qualifies
        # admissible f1: index > i, and f1 >= lo_f1
        j_lo = max(i + 1, bisect.bisect_left(faces, lo_f1))
        if j_lo >= n:
            continue
        target = f0 + value
        j = bisect.bisect_left(faces, target, j_lo, n)
        for k in (j - 1, j):                        # the two candidates nearest f0+value
            if k < j_lo or k >= n:
                continue
            err = abs((faces[k] - f0) - value)
            if best is None or err < best[0] - 1e-12:
                best = (err, f0, faces[k])
    return best


def score(strings, fx, fy, tol=TOL_MM):
    matched, unmatched, off_ink = [], [], []
    for s in strings:
        faces = fx if s["axis"] == "x" else fy
        b = best_pair(s["value_mm"], s["pos_mm"], s["extent_mm"], faces)
        if b is None:
            off_ink.append({**s, "why": "no face pair on this axis brackets the string"})
        elif b[0] <= tol:
            matched.append({**s, "error_mm": round(b[0], 2),
                            "faces_mm": [round(b[1], 1), round(b[2], 1)],
                            "reader_mm": round(b[2] - b[1], 1)})
        else:
            unmatched.append({**s, "best_error_mm": round(b[0], 2),
                              "best_faces_mm": [round(b[1], 1), round(b[2], 1)],
                              "best_reader_mm": round(b[2] - b[1], 1)})
    return matched, unmatched, off_ink


def _rate(strings, fx, fy, tol):
    m, u, _ = score(strings, fx, fy, tol)
    return len(m) / max(len(m) + len(u), 1)


def nulls(strings, fx, fy, tol, perms, seed):
    """Two nulls. See the module docstring: WITHOUT THESE THE HEADLINE MEANS NOTHING.

    Unchanged from v0.1 on purpose -- they are computed on the raw addressable match rate so the
    numbers stay comparable across the version bump (23.4% permutation / 4.8% random on the honest
    reader). They are also the third independent catch for over-extraction."""
    rng = random.Random(seed)
    vals = [s["value_mm"] for s in strings]
    lo, hi = int(min(vals)), int(max(vals))
    perm, rand = [], []
    for _ in range(perms):
        sv = vals[:]
        rng.shuffle(sv)
        perm.append(_rate([{**s, "value_mm": sv[i]} for i, s in enumerate(strings)], fx, fy, tol))
        rand.append(_rate([{**s, "value_mm": float(rng.randrange(lo, hi + 1, 5))}
                           for s in strings], fx, fy, tol))

    def stat(a):
        a = sorted(a)
        return {"mean": round(100 * statistics.mean(a), 1),
                "p95": round(100 * a[min(int(0.95 * len(a)), len(a) - 1)], 1),
                "max": round(100 * a[-1], 1)}
    return {"permutation": stat(perm), "random_dims": stat(rand), "trials": perms, "seed": seed}


# ---------------------------------------------------------------------------------------------
#  THE ABSOLUTE ANCHOR  (FIX (a) + the footprint that FIX (c) needs)
# ---------------------------------------------------------------------------------------------
def chain_corroborates(ov, strings, tol=ANCHOR_TOL_MM):
    """Is this string's predicted span TILED by a chain of smaller strings on the same axis?

    This is the CAD fact that lets the overall dimension be identified WITHOUT LOOKING AT A SINGLE
    READER FACE: on a dimensioned sheet the overall runs on the outermost dimension line and the
    strings on the inner lines SUM TO IT. Walking from the overall's predicted span start, each
    step must land on another string's predicted span start.

    Verified on this sheet, text layer only:
        x: 7820 = 1200 + 1820 + 4800        (starts -3.0 / 1196.2 / 3023.0, cursor drift <= 4.5 mm)
        y: 9720 = 3635 + 1140 + 1560 + 1465 + 1920                        (cursor drift <= 5.4 mm)
        x: 30000 (the site/plot dim) is corroborated by NOTHING -- correctly rejected.
    """
    lo = ov["pos_mm"] - ov["value_mm"] / 2.0
    hi = ov["pos_mm"] + ov["value_mm"] / 2.0
    cand = [s for s in strings
            if s["axis"] == ov["axis"] and s is not ov and s["value_mm"] < ov["value_mm"]]
    starts = [s["pos_mm"] - s["value_mm"] / 2.0 for s in cand]
    seen = set()

    def walk(cursor, used):
        if abs(cursor - hi) <= tol:
            return True
        if cursor > hi + tol:
            return False
        key = (round(cursor, 1), used)
        if key in seen:
            return False
        seen.add(key)
        for i, s in enumerate(cand):
            if used >> i & 1:
                continue
            if abs(starts[i] - cursor) > tol:
                continue
            if walk(cursor + s["value_mm"], used | (1 << i)):
                return True
        return False

    return walk(lo, 0)


def overall_string(strings, axis):
    """The printed OVERALL dimension on `axis`: the building's outer-face-to-outer-face string.

    *** SELECTED FROM THE TEXT LAYER ALONE. NO READER FACE IS CONSULTED. ***  This is load-bearing
    twice over:

      1. ORIGIN. The residual this string produces is the ONLY origin-sensitive number in the
         scorecard. If its selection depended on the reader, the anchor would just be a circular
         restatement of the reader's own frame.
      2. THE FOOTPRINT (fix (c)). The off-ink EXCUSE is "outside the printed footprint", and the
         footprint is [0, V_overall]. My first cut of this function filtered candidates by the
         reader's ink extent -- and that reintroduced the evaporating denominator through the back
         door: cripple the reader and the ink extent shrinks, a SMALLER string gets crowned
         "overall", the footprint shrinks with it, and more strings get EXCUSED. The excuse must
         NEVER be able to follow the reader down. It cannot now: nothing here touches a face.

    The rule: the largest-value string on the axis that a CHAIN OF OTHER STRINGS SUMS TO. That
    rejects the "30000" site/plot dimension (30 m of land, dimensions no wall, no chain sums to it)
    without a hand-tuned envelope and without a face.
    """
    cand = sorted((s for s in strings if s["axis"] == axis),
                  key=lambda s: -s["value_mm"])
    for s in cand:
        if chain_corroborates(s, strings):
            return s
    return None


def anchors(strings, fx, fy):
    """The two absolute checks. They test DIFFERENT things and are never conflated:

    ORIGIN (text-layer only, origin-SENSITIVE):
        the overall string predicts its own span [c-V/2, c+V/2] from the TEXT LAYER ALONE.
        Its near endpoint IS the datum face, and the frame DECLARES that face to be 0.0.
    EXTENT (face-based, origin-INVARIANT):
        the reader's ink extent must equal the printed overall value. This catches SCALE.
    """
    out = {"tol_mm": ANCHOR_TOL_MM, "checks": [], "ok": True,
           "why": ("ORIGIN is text-layer-only vs the frame's DECLARED datum 0.0 (an origin bug is "
                   "invisible to any face-vs-face or text-vs-face comparison: they co-move). "
                   "EXTENT is face-based and origin-invariant: it catches SCALE, not origin.")}
    for axis, faces in (("x", fx), ("y", fy)):
        span = (faces[-1] - faces[0]) if len(faces) >= 2 else 0.0
        ov = overall_string(strings, axis)
        if ov is None:
            out["checks"].append({
                "id": "ORIGIN-%s" % axis, "ok": False, "residual_mm": None,
                "detail": "NO CHAIN-CORROBORATED OVERALL STRING on axis %s: there is nothing on "
                          "this sheet to anchor the frame to, so it REFUSES rather than guess."
                          % axis})
            out["ok"] = False
            continue
        datum_est = ov["pos_mm"] - ov["value_mm"] / 2.0     # TEXT ONLY. No face in this line.
        r_origin = datum_est - 0.0                          # the frame DECLARES the datum is 0.0
        r_extent = span - ov["value_mm"]
        out["checks"].append({
            "id": "ORIGIN-%s" % axis, "ok": abs(r_origin) <= ANCHOR_TOL_MM,
            "residual_mm": round(r_origin, 2), "overall_string": ov["text"],
            "detail": "printed '%s' is drawn centred at %.1f, so the TEXT ALONE puts the datum "
                      "face at %.1f mm; the frame declares it is 0.0"
                      % (ov["text"], ov["pos_mm"], datum_est)})
        out["checks"].append({
            "id": "EXTENT-%s" % axis, "ok": abs(r_extent) <= ANCHOR_TOL_MM,
            "residual_mm": round(r_extent, 2), "overall_string": ov["text"],
            "detail": "reader ink extent %.1f mm vs printed overall %s mm (origin-invariant: "
                      "this is the SCALE check)" % (span, ov["text"])})
        out["ok"] = out["ok"] and abs(r_origin) <= ANCHOR_TOL_MM and abs(r_extent) <= ANCHOR_TOL_MM
    out["footprint_mm"] = footprint(strings, fx, fy)
    return out


def footprint(strings, fx, fy):
    """The building footprint IN THE DECLARED FRAME, taken from the PRINTED OVERALL STRINGS:
    [0, V_overall] on each axis. NOT from the reader's faces -- that is the whole point of FIX (c):
    if the excuse for a missing string could shrink with the reader, a reader that stops extracting
    would excuse its way to a perfect score."""
    fp = {}
    for axis in ("x", "y"):                       # fx/fy accepted and DELIBERATELY NOT USED
        ov = overall_string(strings, axis)
        fp[axis] = [0.0, round(ov["value_mm"], 1)] if ov else None
    return fp


def split_off_ink(off_ink, fp):
    """OFF-INK is only an EXCUSE if the string sits OUTSIDE the printed building footprint on its
    own axis (the '30000' plot dim; the three '100's beyond the outer faces). A string INSIDE the
    building that no face pair can bracket is not a site note -- it is a face the reader LOST, and
    it is A MISS."""
    outside, inside = [], []
    for s in off_ink:
        b = fp.get(s["axis"])
        if b is None or s["pos_mm"] < b[0] or s["pos_mm"] > b[1]:
            outside.append({**s, "excused": "outside the printed building footprint on axis %s"
                                            % s["axis"]})
        else:
            inside.append({**s, "counted_as": "MISS -- inside the building, but the reader has no "
                                              "face pair that brackets it"})
    return outside, inside


def face_precision(matched, fx, fy):
    """FIX (b). Hallucinated faces must COST something. Not a purity measure -- see the docstring."""
    used = set()
    for r in matched:
        used.add((r["axis"], r["faces_mm"][0]))
        used.add((r["axis"], r["faces_mm"][1]))
    emitted = len(fx) + len(fy)
    return (len(used) / emitted if emitted else 0.0), len(used), emitted


def f1(recall, precision):
    return 0.0 if (recall + precision) == 0 else 2 * recall * precision / (recall + precision)


def centring_mad(matched):
    """The origin-INVARIANT numeral-centring residual, live. This is what ANCHOR_TOL_MM was derived
    from; it is reported as a DRIFT TRIPWIRE and must never feed back into the constant."""
    if not matched:
        return None
    res = [r["pos_mm"] - (r["faces_mm"][0] + r["faces_mm"][1]) / 2.0 for r in matched]
    med = statistics.median(res)
    return round(statistics.median([abs(v - med) for v in res]), 2)


# ---------------------------------------------------------------------------------------------
#  THE INSTRUMENT'S OWN TEST HARNESS -- deliberately break the reader and watch the score
# ---------------------------------------------------------------------------------------------
def _grid(lo, hi, step):
    v, out = lo, []
    while v <= hi + 1e-9:
        out.append(round(v, 1))
        v += step
    return out


MUTATIONS = {
    "baseline":       "the reader as it actually is",
    "origin+50mm":    "translate the reader's origin 50 mm on BOTH axes (v0.1 was blind to this)",
    "scale-x1.002":   "0.2% scale error",
    "scale-x1.02":    "2% scale error",
    "phantom-100mm":  "true faces PLUS a 100 mm grid across the whole sheet (a hallucinating "
                      "reader). This is the mutation that used to score 94.1%.",
    "phantom-inside": "true faces PLUS a 100 mm grid confined INSIDE the building, so it does NOT "
                      "trip the extent anchor. This isolates the PRECISION term.",
    "drop-half":      "keep every 2nd face (endpoints retained, so the anchor still passes)",
    "cripple-4":      "THE REVIEWER'S CRIPPLE: extraction dies after 4 faces/axis. In v0.1 this "
                      "EVAPORATED the denominator (off-ink 4 -> 49, addressable 48 -> 3).",
    "cripple-4-span": "4 faces/axis but SPREAD (endpoints kept), so every string is still "
                      "bracketed and the loss shows up as UNMATCHED rather than off-ink.",
    "minimal-reader": "THE HOLE I FOUND IN MY OWN FIX (b). Emit ONLY the 43 faces some string "
                      "uses; DELETE the 15 real, undimensioned wall faces. Precision -> 100%, "
                      "F1 -> 90.9%: it BEATS the honest reader by deleting real walls. Not fixed. "
                      "See RESIDUAL in the module docstring.",
}


def _mutate_faces(name, fx, fy):
    # the calibration mutations move (scale, origin) upstream of here, and `minimal-reader` needs
    # the strings, so it is applied in run(). All four are pass-throughs for the face set.
    if name in (None, "baseline", "origin+50mm", "scale-x1.002", "scale-x1.02", "minimal-reader"):
        return fx, fy
    if name == "phantom-100mm":
        return (sorted(set(fx) | set(_grid(-1000.0, 17800.0, 100.0))),
                sorted(set(fy) | set(_grid(-1000.0, 17800.0, 100.0))))
    if name == "phantom-inside":
        return (sorted(set(fx) | set(_grid(0.0, fx[-1], 100.0))),
                sorted(set(fy) | set(_grid(0.0, fy[-1], 100.0))))
    if name == "drop-half":
        keep = lambda f: sorted(set(f[::2]) | {f[0], f[-1]})
        return keep(fx), keep(fy)
    if name == "cripple-4":
        return fx[:4], fy[:4]                    # extraction dies early: the reviewer's cripple
    if name == "cripple-4-span":
        pick = lambda f: sorted({f[0], f[len(f) // 3], f[2 * len(f) // 3], f[-1]})
        return pick(fx), pick(fy)
    raise RefuseSheet("unknown mutation %r (known: %s)" % (name, ", ".join(MUTATIONS)))


def run(pdf, page_no, tol=TOL_MM, perms=2000, seed=7, mutate=None):
    if mutate not in (None,) and mutate not in MUTATIONS:
        raise RefuseSheet("unknown mutation %r (known: %s)" % (mutate, ", ".join(MUTATIONS)))
    bands_pt, steps_pt, scale, denom, modal, tb, gate, notes = read_bands(pdf, page_no)
    x0 = min(r[0] for r in bands_pt)
    y0 = max(r[3] for r in bands_pt)

    # --- the two mutations that break the CALIBRATION rather than the face set. They move the
    #     faces AND the text together, exactly as a real calibration bug would.
    if mutate == "origin+50mm":
        x0 += 50.0 / scale
        y0 += 50.0 / scale
    if mutate == "scale-x1.002":
        scale *= 1.002
    if mutate == "scale-x1.02":
        scale *= 1.02

    bands = to_mm_bands(bands_pt, scale, x0, y0)
    steps = to_mm_bands(steps_pt, scale, x0, y0)
    # THE READER'S OWN EXTRACTED GEOMETRY -- this is the thing under test. Wall poche + wall steps;
    # both are wall-pen ink and both have real faces. Nothing else is admitted: virtual edges and
    # closure infills are NOT faces and must never be scoreable (that would let the reader's own
    # inventions answer the designer's questions).
    fx, fy = ink_faces(bands + steps)
    fx, fy = _mutate_faces(mutate, fx, fy)
    strings, mixed, rejected = dim_strings(pdf, page_no, scale, x0, y0)
    if not strings:
        raise RefuseSheet("no printed dimension strings on this page: nothing to score against")

    if mutate == "minimal-reader":
        # needs the strings, so it cannot live in _mutate_faces. THIS MUTATION READS THE GT -- that
        # is the point of it: it is the attack an HONEST extractor cannot mount (it would have to
        # read the text layer it is architecturally forbidden from reading) and a CHEATING one can.
        m0, _, _ = score(strings, fx, fy, tol)
        keep = {"x": set(), "y": set()}
        for r in m0:
            keep[r["axis"]].update(r["faces_mm"])
        fx, fy = sorted(keep["x"]), sorted(keep["y"])

    m, u, o = score(strings, fx, fy, tol)
    anc = anchors(strings, fx, fy)
    off_out, off_in = split_off_ink(o, anc["footprint_mm"])

    addressable = len(m) + len(u)                       # v0.1's denominator (kept, as a component)
    scoreable = addressable + len(off_in)               # v0.2's denominator -- THE OFF-INK GATE
    recall = len(m) / max(scoreable, 1)
    prec, n_used, n_emitted = face_precision(m, fx, fy)
    the_f1 = f1(recall, prec)
    errs = [x["error_mm"] for x in m]
    return {
        "schema": "interior-ai/dim-string-scorecard@0.2",
        "source_pdf": os.path.basename(pdf),
        "page": page_no,
        "mutation": mutate or "baseline",
        "scale_mm_per_pt": round(scale, 5),
        "origin_pt": [round(x0, 2), round(y0, 2)],
        "gt": ("THE PRINTED DIMENSION STRINGS IN THE PDF TEXT LAYER. Drafted by the designer in "
               "CAD; this reader has never read the text layer. NO human takeoff is in this loop "
               "and living012_takeoff.json is NOT used."),
        "reader_faces": {"x": len(fx), "y": len(fy),
                         "from": "wall_poche + wall_step bands only (no virtual, no infill)"},
        "tol_mm": tol,

        # ---- THE HEADLINE (v0.2) ------------------------------------------------------------
        "anchor": anc,
        "anchor_ok": anc["ok"],
        "headline_f1": None if not anc["ok"] else round(the_f1, 4),
        "headline_note": ("NO SCORE -- THE FRAME IS REFUSED. An anchor failed, so the mm frame is "
                          "wrong and every 'match' below it is a coincidence measured in the wrong "
                          "frame. A score here would be worse than no score."
                          if not anc["ok"] else
                          "F1(recall, face_precision), reportable only because both absolute "
                          "anchors hold."),
        "recall": round(recall, 4),
        "face_precision": round(prec, 4),
        "f1_ungated": round(the_f1, 4),   # what F1 WOULD be; printed even when refused, for triage
        "faces_used_by_a_match": n_used,
        "faces_emitted": n_emitted,
        "centring_mad_mm": centring_mad(m),
        "centring_mad_calibration_mm": _CALIBRATION_MAD_MM,
        "anchor_tol_mm": ANCHOR_TOL_MM,

        # ---- components / v0.1 continuity ---------------------------------------------------
        "n_strings": len(strings),
        "n_addressable": addressable,
        "n_scoreable": scoreable,
        "n_matched": len(m),
        "n_unmatched": len(u),
        "n_off_ink": len(o),
        "n_off_ink_outside_footprint": len(off_out),
        "n_off_ink_inside_footprint": len(off_in),
        "match_rate": round(len(m) / max(addressable, 1), 4),   # v0.1's headline, now a COMPONENT
        "median_error_mm": round(statistics.median(errs), 2) if errs else None,
        "worst_error_mm": round(max(errs), 2) if errs else None,
        "matched": sorted(m, key=lambda r: -r["error_mm"]),
        "unmatched": sorted(u, key=lambda r: -r["best_error_mm"]),
        "off_ink": o,
        "off_ink_outside_footprint": off_out,
        "off_ink_inside_footprint": off_in,
        "text_layer_health": {
            "spans_rejected_non_numeral": rejected,
            "spans_with_digits_but_not_clean_numerals": sorted(set(mixed)),
            "thai_split_mark_bug": ("this PDF splits Thai combining marks off their consonants. "
                                    "VERIFIED not to touch the dimension strings: every one is a "
                                    "clean ASCII numeral. The list above is the tripwire -- if a "
                                    "numeral ever arrives mangled it shows up there."),
        },
        "null": nulls(strings, fx, fy, tol, perms, seed),
    }


def report(sc):
    # The tripwire list can contain Thai; a cp1252 console must not be able to kill the scorecard.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    n = sc["null"]
    W = 88
    print("=" * W)
    print("  PRINTED-DIMENSION SCORECARD v0.2 -- %s p%d   [mutation: %s]"
          % (sc["source_pdf"], sc["page"], sc["mutation"]))
    print("  GT = the designer's printed dimension strings. NO human takeoff in this loop.")
    print("=" * W)
    print("  ABSOLUTE ANCHORS (tol %.1f mm, frozen = 3 x robust-sigma of the centring residual)"
          % sc["anchor_tol_mm"])
    for c in sc["anchor"]["checks"]:
        print("    [%s] %-9s residual %9s mm   %s"
              % ("OK  " if c["ok"] else "FAIL", c["id"],
                 "n/a" if c["residual_mm"] is None else "%.2f" % c["residual_mm"], c["detail"]))
    print("    centring MAD this run %s mm  (calibration was %.2f mm -- drift tripwire)"
          % (sc["centring_mad_mm"], sc["centring_mad_calibration_mm"]))
    print("-" * W)
    if not sc["anchor_ok"]:
        print("  *** NO SCORE -- THE FRAME IS REFUSED ***")
        print("  %s" % sc["headline_note"])
        print("  (for triage only, NOT a score: F1 would have been %.1f%%, recall %.1f%%, "
              "face-precision %.1f%%)"
              % (100 * sc["f1_ungated"], 100 * sc["recall"], 100 * sc["face_precision"]))
    else:
        print("  HEADLINE  F1            : %.1f%%   <-- THE SCORE" % (100 * sc["headline_f1"]))
        print("    recall                : %.1f%%   (%d matched / %d scoreable)"
              % (100 * sc["recall"], sc["n_matched"], sc["n_scoreable"]))
        print("    face precision        : %.1f%%   (%d of %d emitted faces used by a match)"
              % (100 * sc["face_precision"], sc["faces_used_by_a_match"], sc["faces_emitted"]))
    print("-" * W)
    print("  reader faces extracted : %d on x, %d on y  (%s)"
          % (sc["reader_faces"]["x"], sc["reader_faces"]["y"], sc["reader_faces"]["from"]))
    print("  printed dim strings    : %d" % sc["n_strings"])
    print("    addressable          : %d   (v0.1's denominator; raw match rate %.1f%%)"
          % (sc["n_addressable"], 100 * sc["match_rate"]))
    print("    off-ink OUTSIDE fp   : %d   excused, NOT scored (site dims / beyond the outer face)"
          % sc["n_off_ink_outside_footprint"])
    print("    off-ink INSIDE fp    : %d   *** COUNTED AS MISSES *** (the off-ink gate)"
          % sc["n_off_ink_inside_footprint"])
    print("    -> SCOREABLE         : %d" % sc["n_scoreable"])
    print("  median error           : %s mm     worst error: %s mm"
          % (sc["median_error_mm"], sc["worst_error_mm"]))
    print("-" * W)
    print("  NULL permutation (values shuffled between the SAME positions, %d trials)"
          % n["trials"])
    print("    mean %.1f%%   p95 %.1f%%   max %.1f%%"
          % (n["permutation"]["mean"], n["permutation"]["p95"], n["permutation"]["max"]))
    print("  NULL random-dims (same positions, values drawn from the observed range)")
    print("    mean %.1f%%   p95 %.1f%%   max %.1f%%"
          % (n["random_dims"]["mean"], n["random_dims"]["p95"], n["random_dims"]["max"]))
    verdict = ("SIGNAL: the raw match rate is above the permutation null's p95, so it is not "
               "face-density noise." if 100 * sc["match_rate"] > n["permutation"]["p95"] else
               "*** NO SIGNAL: the raw match rate is INSIDE the permutation null. This is "
               "measuring the DENSITY OF THE FACE SET, not the reader. Do not quote it. ***")
    print("  -> %s" % verdict)
    print("-" * W)
    print("  UNMATCHED -- the designer printed these and the reader has no face pair for them:")
    if not sc["unmatched"]:
        print("    (none)")
    for r in sc["unmatched"][:12]:
        print("    %-6s mm  axis %s @ %8.1f   best reader span %8.1f  (off by %7.1f mm)"
              % (r["text"], r["axis"], r["pos_mm"], r["best_reader_mm"], r["best_error_mm"]))
    if len(sc["unmatched"]) > 12:
        print("    ... and %d more" % (len(sc["unmatched"]) - 12))
    print("  OFF-INK, EXCUSED (outside the printed footprint %s):" % sc["anchor"]["footprint_mm"])
    print("    " + (", ".join("%s@%s%.0f" % (r["text"], r["axis"], r["pos_mm"])
                              for r in sc["off_ink_outside_footprint"]) or "(none)"))
    print("  OFF-INK, INSIDE THE BUILDING -- these are MISSES, not excuses:")
    print("    " + (", ".join("%s@%s%.0f" % (r["text"], r["axis"], r["pos_mm"])
                              for r in sc["off_ink_inside_footprint"][:20]) or "(none)"))
    print("  text-layer health: %d non-numeral spans dropped; digit-bearing non-numerals: %s"
          % (sc["text_layer_health"]["spans_rejected_non_numeral"],
             sc["text_layer_health"]["spans_with_digits_but_not_clean_numerals"] or "none"))
    print("=" * W)
    return sc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("page", type=int, help="0-indexed page")
    ap.add_argument("--tol-mm", type=float, default=TOL_MM)
    ap.add_argument("--perms", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--json", default=None, help="write the scorecard (put it under _private/)")
    ap.add_argument("--mutate", default=None,
                    help="break the reader on purpose; 'list' prints the menu")
    a = ap.parse_args(argv)
    if a.mutate == "list":
        for k, v in MUTATIONS.items():
            print("  %-16s %s" % (k, v))
        return 0
    try:
        sc = run(a.pdf, a.page, a.tol_mm, a.perms, a.seed, a.mutate)
    except RefuseSheet as e:
        print("REFUSED: %s" % e)
        return 2
    report(sc)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(sc, f, indent=1, ensure_ascii=False)
        print("wrote %s" % a.json)
    return 0 if sc["anchor_ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
