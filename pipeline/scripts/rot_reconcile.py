"""
rot_reconcile.py -- resolve the ONE load-bearing caveat both structured3d_adapter.py and
render_mask_labels.py flag on F2_facing: the adapter emits GT `rot` as NATIVE YAW
(atan2(basis[0].y, basis[0].x), CCW from world +X, forward = basis[0]) while benchmark_reader
scores `rot` in build_floor's F(rot)=(sin rot, -cos rot) convention. Both files defer to a
future "reconcile the ~270deg offset AND the y-handedness before trusting F2's angular buckets."
This module DOES that reconciliation -- with NO render download -- and pins exactly what it
proves vs. what genuinely stays download-gated.

WHAT IS PROVEN HERE (coordinate-convention layer -- NOW SOLVED, no data needed):
  Given the adapter's chosen forward = basis[0], the build_floor rot of that SAME physical
  forward is a CONSTANT +90deg from the native yaw:

        build_floor_rot = (native_yaw + 90) mod 360        # a PURE ROTATION, not a mirror

  Proven three independent ways, all cross-checked in _prove():
    1. Closed form. F(rot)=(sin rot, -cos rot) inverts to rot = atan2(fx, -fy) for a forward
       (fx, fy). native = atan2(fy, fx). atan2(fx, -fy) is the angle of (-fy, fx), which is
       (fx, fy) rotated +90deg CCW -> rot = native + 90 for EVERY vector, not just cardinals.
    2. Rotation, NOT reflection. The relation is additive in native (+90 const). A handedness
       flip (the thing the adapter comment feared) would instead read rot = k - native (a SIGN
       flip on native). _prove() fits both hypotheses over a dense angle sweep and REJECTS the
       reflection: max |(native+90) - build| == 0 while any k-native candidate diverges. The
       "y_handedness_UNVALIDATED" worry is thereby settled -- there is no mirror to bake in.
    3. Canonical cardinals. The four cardinals land on facing_reader._FACING exactly
       (build 0->S, 90->E, 180->N, 270->W), the same convention as cross_signal:96 and
       benchmark_reader._CARDINAL_ROT -- so the +90 is checked against the repo's OWN facing
       convention code, not a re-transcription.
  And the CONSEQUENCE is exercised against the real scorer (benchmark_reader.score_facing):
  scoring native-yaw GT against a build_floor-emitting pred lands every facing object in the
  'flipped'/'wrong' bucket (cardinal_correct -> 0) though the read is physically perfect;
  applying native_yaw_to_build_floor first makes it 'exact' (cardinal_correct -> 1.0). That is
  the silent F2 corruption the adapter warned would appear "the moment a real reader emitting
  build_floor rot is scored" -- here reproduced and fixed.

WHY THERE IS NO MIRROR TO WORRY ABOUT (data-path evidence, not just algebra):
  The adapter comment hedged on y-handedness because "no rot-emitting reader exists to check
  against." Two facts close it without one: (a) the relation is provably a pure rotation (2
  above); (b) NOTHING flips Y in the scored data path -- synth_plan_2d draws x/y/w/d at mm
  scale 1.0 (its only invert_yaxis() is a cosmetic debug-plot axis label), and svg_plan_reader
  is "handedness-blind, so no flip is applied" (svg_plan_reader.py:45) and emits mm footprints
  in the SAME world frame GT uses -- which is exactly why detection IoU-matches at all. GT and
  any future reader therefore share one mm XY frame; the only difference is the +90 convention.

WHAT STILL STAYS DOWNLOAD-GATED (semantic layer -- honestly NOT solved here):
  This proves the offset between two ANGLE CONVENTIONS. It does NOT prove that Structured3D's
  basis[0] IS the object's semantic FRONT (vs its right/back/left axis). If S3D's local-x is,
  say, the object's right side, every GT facing is a further fixed 90deg off TRUE facing, and no
  coordinate algebra recovers that -- it needs the render masks / 3D-FRONT layout (the same
  owner download the label sidecar needs) to confirm which local axis is 'front'. So after this
  module, F2 is DATA-limited on TWO remaining axes, both download-gated, NEITHER a code bug:
    (i)  the basis[0]==front semantic check (render / 3D-FRONT), and
    (ii) a reader that actually EMITS rot -- svg_plan_reader emits NONE today (facing-blind), so
         F2 against it buckets every pair 'unreported' regardless of convention. A bare synth
         rectangle carries no facing cue for any reader to recover, so F2's angular buckets stay
         un-exercisable end-to-end until oriented symbols + a rot-emitting reader both land.
  Net correction to the two docstrings' caveat: the ~270deg/handedness worry is RESOLVED (pure
  +90, no mirror); the residual F2 caveat is the semantic front-axis + the missing rot-reader,
  which this module names precisely instead of the vague "reconcile before real reader."

ADJACENT FINDING (reported, NOT fixed here -- belongs to the adapter's geometry contract;
severity CORRECTED UP by adversarial verification 2026-07-09):
  placement_gate.footprint(x/y/w/d, rot) RE-ROTATES x/y/w/d by rot (it treats them as the
  UN-rotated placed rect, the benchmark generator's schema). But structured3d_adapter emits
  x/y/w/d as the ALREADY-rotated tight world AABB PLUS a separate rot. So in the KINDED lane
  (labels supplied -> rot emitted), a box at ANY rot other than 0/180 has a WRONG scored footprint
  (verified on a 1000x400 box):
      rot 0,180  -> IoU 1.0 (identical, safe)
      rot 90,270 -> TRANSPOSED (w/d swapped): IoU 0.25 vs the true AABB -> a DETECTION MISS
      rot 45,135 -> INFLATED up to ~2x area: IoU ~0.5
  90/270 are among the MOST COMMON furniture facings (a piece square-on to a side wall), so this is
  BROAD, not a rare diagonal tail -- and it is invisible to gt-vs-gt (symmetric). Fix belongs
  upstream: when emitting rot, emit x/y/w/d as the object's LOCAL (un-yawed) w x d so footprint()
  rebuilds the true oriented box. Flagged in qa/reports/ so wiring F2 for real also closes this.

USAGE:
  python rot_reconcile.py --prove                 # the full proof (no data), prints the checks
  python rot_reconcile.py --convert-gt in out     # rewrite a gt.json's rot native_yaw->build_floor
  native_yaw_to_build_floor(deg) / build_floor_to_native_yaw(deg) / forward_to_build_floor_rot(fx,fy)
  convert_gt_doc(doc) -> a copy with every element's rot converted + a meta stamp (pure; no I/O)
"""
import copy
import json
import math
import sys

VERSION = "rot_reconcile v1.0"

# The single convention offset, proven below. build_floor rot = native yaw + this (mod 360).
NATIVE_TO_BUILDFLOOR_OFFSET_DEG = 90.0


def native_yaw_to_build_floor(deg):
    """Native yaw (atan2(basis[0].y, basis[0].x), CCW from +X) -> benchmark_reader build_floor
    rot (F(rot)=(sin,-cos)). A PURE +90deg rotation of convention (proven a rotation, not a
    mirror -- see _prove). None passes through (a rot-less element stays rot-less)."""
    if deg is None:
        return None
    return (float(deg) + NATIVE_TO_BUILDFLOOR_OFFSET_DEG) % 360.0


def build_floor_to_native_yaw(deg):
    """Inverse of native_yaw_to_build_floor (build_floor rot -> native yaw). -90deg (mod 360)."""
    if deg is None:
        return None
    return (float(deg) - NATIVE_TO_BUILDFLOOR_OFFSET_DEG) % 360.0


def forward_to_build_floor_rot(fx, fy):
    """A forward vector (the S3D basis[0] xy) -> build_floor rot directly, from the canonical
    inverse of F(rot)=(sin rot, -cos rot): rot = atan2(fx, -fy). Independent of the native-yaw
    path; _prove() asserts the two agree everywhere. Returns None for a ~zero-length vector
    (no facing to read) rather than a spurious angle."""
    if math.hypot(fx, fy) < 1e-9:
        return None
    return math.degrees(math.atan2(fx, -fy)) % 360.0


def native_yaw_of_forward(fx, fy):
    """The adapter's native yaw of a forward vector: atan2(fy, fx), CCW from +X (mm world)."""
    if math.hypot(fx, fy) < 1e-9:
        return None
    return math.degrees(math.atan2(fy, fx)) % 360.0


def convert_gt_doc(doc):
    """A structured3d_adapter gt document (native-yaw rot) -> a COPY whose every element `rot`
    is build_floor rot, so a future rot-EMITTING reader can be scored against it correctly.
    Pure: no I/O, original untouched. Elements without a rot key are left exactly as-is (kind-
    less / rot-less honesty contract preserved). Stamps meta so the conversion is not invisible.
    NOTE: this fixes the ANGLE CONVENTION only; it does NOT assert basis[0] is the semantic front
    (still download-gated) -- the meta stamp says so.

    NOT idempotent by design: applying it twice would add 180deg = a silent facing REVERSAL. A doc
    that already carries meta.rot_reconciled RAISES (loud, matching the house 'never silent-wrong'
    doctrine -- cf. render_mask_labels.read_mask) rather than re-rotate."""
    if doc.get("meta", {}).get("rot_reconciled") is not None:
        raise ValueError("convert_gt_doc: doc already has meta.rot_reconciled -- rot is already "
                         "build_floor; converting again would add 180deg (a silent facing "
                         "reversal). Refusing. Convert the native-yaw adapter output ONCE.")
    out = copy.deepcopy(doc)
    n = 0
    for el in out.get("elements", []):
        if el.get("rot") is not None:
            el["rot"] = round(native_yaw_to_build_floor(el["rot"]), 1)
            n += 1
    meta = out.setdefault("meta", {})
    meta["rot_reconciled"] = {
        "by": VERSION, "offset_deg": NATIVE_TO_BUILDFLOOR_OFFSET_DEG,
        "convention": "build_floor F(rot)=(sin,-cos)  [was: native yaw atan2(basis[0].y,x)]",
        "n_rot_converted": n,
        "still_gated": "basis[0]==semantic-front is NOT asserted (needs render/3D-FRONT); "
                       "and no rot-emitting reader exists yet -- see rot_reconcile docstring",
    }
    return out


# ---------------------------------------------------------------------------------------------
def _prove(verbose=True):
    """The whole reconciliation as executable assertions -- NO data download. Returns a dict of
    the proven facts. Raises AssertionError on any drift (this is the standing regression)."""
    import facing_reader as FR

    def say(*a):
        if verbose:
            print(*a)

    # 1. closed-form native+90 == the two vector methods, over a DENSE sweep (every degree),
    #    not just cardinals -- a cardinals-only check cannot distinguish +90 from a mirror.
    max_err_vec = 0.0
    for deg in range(0, 360):
        rad = math.radians(deg)
        fx, fy = math.cos(rad), math.sin(rad)      # a forward at native yaw = deg
        nat = native_yaw_of_forward(fx, fy)        # ~= deg
        bf_closed = native_yaw_to_build_floor(nat)
        bf_vector = forward_to_build_floor_rot(fx, fy)
        d = min((bf_closed - bf_vector) % 360.0, (bf_vector - bf_closed) % 360.0)
        max_err_vec = max(max_err_vec, d)
    assert max_err_vec < 1e-6, f"closed-form vs vector diverge by {max_err_vec} deg"
    say(f"  [1] closed-form (native+90) == vector inverse atan2(fx,-fy): "
        f"max diff {max_err_vec:.2e} deg over 360 headings")

    # 2. it is a ROTATION, not a REFLECTION. Fit build = native + C (rotation) and
    #    build = K - native (reflection) over the sweep; the rotation fits with 0 residual,
    #    the reflection cannot (this is what makes 'y-handedness' a non-issue -- there is no
    #    consistent mirror). Use forward_to_build_floor_rot as the ground-truth build value.
    def circ(a):
        return min(a % 360.0, (-a) % 360.0)
    rot_res = refl_res = 0.0
    # reflection constant K estimated from heading 0 (build there), then tested everywhere.
    K = forward_to_build_floor_rot(math.cos(0), math.sin(0)) + 0.0   # + native(0)=0
    for deg in range(0, 360):
        rad = math.radians(deg)
        nat = native_yaw_of_forward(math.cos(rad), math.sin(rad))
        build = forward_to_build_floor_rot(math.cos(rad), math.sin(rad))
        rot_res = max(rot_res, circ(build - (nat + 90.0)))
        refl_res = max(refl_res, circ(build - (K - nat)))
    assert rot_res < 1e-6, f"rotation hypothesis residual {rot_res}"
    assert refl_res > 45.0, (f"reflection hypothesis residual only {refl_res} -- cannot rule out "
                             f"a mirror; the offset may hide a handedness flip")
    say(f"  [2] rotation vs reflection: rotation residual {rot_res:.2e} deg (fits); "
        f"reflection residual {refl_res:.1f} deg (rejected) -> PURE ROTATION, no mirror")

    # 3. cardinals land on facing_reader's OWN convention letters (repo ground truth).
    card = {0.0: "S", 90.0: "E", 180.0: "N", 270.0: "W"}   # build_floor rot -> facing letter
    fwd_of = {"S": (0.0, -1.0), "E": (1.0, 0.0), "N": (0.0, 1.0), "W": (-1.0, 0.0)}
    for build_rot, letter in card.items():
        fx, fy = fwd_of[letter]
        got_build = forward_to_build_floor_rot(fx, fy)
        assert abs(circ(got_build - build_rot)) < 1e-6, (letter, got_build, build_rot)
        assert FR.facing_from_rot(build_rot) == letter, (build_rot, FR.facing_from_rot(build_rot))
        # and the native yaw of that same forward, +90, must reproduce build_rot
        nat = native_yaw_of_forward(fx, fy)
        assert abs(circ(native_yaw_to_build_floor(nat) - build_rot)) < 1e-6, (letter, nat)
    say("  [3] cardinals match facing_reader._FACING exactly "
        "(build 0->S,90->E,180->N,270->W) and native+90 reproduces each")

    # 4. the F2 CONSEQUENCE against the real scorer: native-yaw GT vs a build_floor-emitting
    #    pred scores NOT cardinal-correct; converting GT first scores exact. One facing element.
    #    NOTE the SQUARE box at a cardinal rot: placement_gate.footprint() RE-ROTATES x/y/w/d by
    #    rot, so a non-square box's AABB differs between rot=90 and rot=180 and the pair would fail
    #    to IoU-match (n=0) -- masking the angular effect behind a detection miss. A square at a
    #    cardinal keeps the AABB rot-invariant, isolating the convention's effect on the BUCKET.
    #    (That footprint() re-rotation vs the adapter's already-AABB x/y/w/d is a SEPARATE adapter
    #    schema issue this module reports but does not fix -- see the QA report.)
    import benchmark_reader as B
    # a bed at native yaw 90 (forward +Y). A correct reader emits build_floor rot = 180 (North).
    native_gt = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                               "rot": 90.0}]}
    reader_pred = {"elements": [{"id": "b", "kind": "bed", "x": 0, "y": 0, "w": 1500, "d": 1500,
                                 "rot": 180.0}]}                      # build_floor rot of +Y
    raw = B.score_pair(native_gt, reader_pred)["F2_facing"]
    assert raw["n"] == 1 and raw["hits"] == 0, raw          # 90 vs 180 -> 90deg off -> not correct
    fixed_gt = convert_gt_doc(native_gt)
    assert fixed_gt["elements"][0]["rot"] == 180.0, fixed_gt["elements"][0]["rot"]
    fixed = B.score_pair(fixed_gt, reader_pred)["F2_facing"]
    assert fixed["n"] == 1 and fixed["hits"] == 1 and fixed["cardinal_correct"] == 1.0, fixed
    say(f"  [4] score_facing consequence: native GT vs build_floor reader -> "
        f"cardinal_correct={raw['cardinal_correct']} (n={raw['n']}); after convert_gt_doc -> "
        f"cardinal_correct={fixed['cardinal_correct']} -- the exact silent-F2 corruption, fixed")

    # 5. round-trip inverse is clean.
    for deg in (0.0, 37.0, 90.0, 213.4, 359.9):
        assert circ(build_floor_to_native_yaw(native_yaw_to_build_floor(deg)) - deg) < 1e-9
    say("  [5] native->build->native round-trips clean")

    facts = {"offset_deg": NATIVE_TO_BUILDFLOOR_OFFSET_DEG, "is_rotation_not_reflection": True,
             "rotation_residual_deg": rot_res, "reflection_residual_deg": refl_res,
             "vector_vs_closed_max_diff_deg": max_err_vec,
             "coordinate_layer": "SOLVED", "semantic_front_axis": "download-gated (basis[0]==front unproven)",
             "rot_emitting_reader": "none exists (svg_plan_reader facing-blind)"}
    say(f"{VERSION}: PROOF PASS -- build_floor_rot = (native_yaw + 90) mod 360, pure rotation. "
        f"Residual F2 caveat is SEMANTIC (basis[0]==front) + no rot-reader, both download-gated.")
    return facts


def main(argv):
    if len(argv) >= 2 and argv[1] in ("--prove", "--selftest"):
        _prove(verbose=True)
    elif len(argv) >= 4 and argv[1] == "--convert-gt":
        doc = json.load(open(argv[2], encoding="utf-8"))
        out = convert_gt_doc(doc)
        json.dump(out, open(argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n = out["meta"]["rot_reconciled"]["n_rot_converted"]
        print(f"wrote {argv[3]}  ({n} element rot(s) native_yaw -> build_floor)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
