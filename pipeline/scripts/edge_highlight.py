#!/usr/bin/env python3
"""edge_highlight.py — CAN THE EDGES IN THIS FRAME CATCH A HIGHLIGHT AT ALL?
PURE (no bpy), reads a `scene-dump@2` written by `scene_dump.py`.

    python pipeline/scripts/edge_highlight.py <room_*.scene.json>

exit 0 = measured and reported (this rung is a REPORTING LINE, not a cut — see below)
exit 2 = COULD NOT RUN: no bevel widths in the dump, or no `mm_per_px` (no camera,
         or a dump written before the key). Never a pass.

WHY THIS EXISTS
---------------
Learned 2026-08-29 from `1i6woUR4iQA` (Vertex Arcade, "Make ANY FURNITURE in
Blender in 15 Minutes"). At 07:14 he stops with the model finished and says it is
still missing something, and his reason is a READING OF THE REFERENCE rather than
a preference: every reference photo carries a highlight along the edges, and the
way to get one is a bevel. Prescription: 2 segments, a few millimetres at most.

THE NUMBER DOES NOT TRANSFER AND THE REASON DOES, and separating those two is the
whole point of this file. His chair is a PRODUCT SHOT — the object fills the
frame, so 3 mm subtends many pixels. Ours is a room. Measured on the eye camera of
record (18 mm lens, 2400 px wide, master-suite):

    depth    mm/px     1.2 mm arris      5.0 mm bevel
    1.0 m    0.833        1.44 px           6.00 px
    2.0 m    1.667        0.72 px           3.00 px
    3.9 m    3.2          0.37 px           1.55 px      <- the millwork wall
    6.0 m    5.000        0.24 px           1.00 px

`MILL_BEVEL_M = 0.0012` was chosen in this repo for a good reason, written down at
its own definition: *"joinery arris: a cabinet edge is nearly sharp, not a 5mm
round-over."* That is TRUE OF THE WORLD and it renders as **0.37 px** — nothing.
Meanwhile the global suite bevel that the same file's docstring calls impossible
(*"a 5 mm round-over on a cabinet door is not a thing that exists"*) is the only
one still wider than a pixel out there.

So the requirement the video is really stating is a PIXEL-DOMAIN requirement —
"the edge must catch a highlight in the delivered frame" — and every bevel
decision in this repo's history was made in the MILLIMETRE domain, with nothing
that could see the mapping between the two. That mapping is now `mm_per_px`,
computed per object inside Blender against the real camera.

WHY IT IS A LINE AND NOT A CUT, said plainly so nobody promotes it by accident.
To fail a frame I would have to know how many pixels wide an edge highlight has
to be before an eye reads it as an edge, and **nobody here has measured that.**
Inventing a threshold would be the defect this repo files under "a number changed
to look productive" — and worse, it would be a cut whose authority came from this
file rather than from a reading of delivered work. The band that would settle it
is a measurement of the ANCHOR POOL: take the edge-highlight width, in pixels, off
delivered frames at a known scale. Until that exists this rung prints the
distribution into the render path — his channel (R11) — and names the largest
in-frame masses whose edges cannot be seen. The same reason and the same shape as
the plan's DELIVERED-WORK VALUE BAND, which is a reporting line for exactly this
reason.

WHAT IT CANNOT SEE, so the report is not read as more than it is:

  * a bevel that subtends two pixels is not thereby CORRECT — the highlight also
    needs a light to catch and a specular response to catch it with. This rung
    answers only the necessary half: whether there is enough geometry there for the
    question to be asked at all;
  * `bevel_m` is the Bevel modifier's `width` under Blender's default OFFSET mode,
    i.e. the distance from the original edge along each adjacent face. On a
    90-degree arris the chamfer that actually catches the light is ~1.41x that, so
    every px figure here is a LOWER BOUND;
  * `mm_per_px` is ONE sample at each object's bbox centre. For a mass that spans
    the room in depth — the floor is the worst case and it sorts to the top of the
    printout — the near edge subtends several times what the far edge does, and one
    number cannot say so;
  * masses with NO bevel modifier are counted and their area printed, but they have
    no px figure to band: they are 0 px by construction.
"""
import json
import os
import sys

# Reported bands, in pixels of the delivered frame. They are BUCKETS FOR A REPORT
# and explicitly not thresholds — no branch in this file changes an exit code on
# them. Named so the printout is readable, and 1.0 px is in the list because it is
# the one boundary with a meaning that is not a matter of taste: below one pixel
# the feature cannot be resolved at all, whatever the lighting does.
BANDS = ((0.5, "invisible"), (1.0, "sub-pixel"), (2.0, "one-pixel"),
         (4.0, "readable"), (float("inf"), "wide"))


def bevel_px(rec):
    """Pixels subtended by this object's bevel in the delivered frame, or None if
    the dump cannot say. None is a THIRD STATE and callers must keep it that way:
    an object with no camera behind it has not been measured, and counting it as
    fine would be the vacuous zero this repo keeps re-filing."""
    w = rec.get("bevel_m")
    mpp = rec.get("mm_per_px")
    if w is None or not mpp:
        return None
    return (float(w) * 1000.0) / float(mpp)


def band(px):
    for hi, name in BANDS:
        if px < hi:
            return name
    return BANDS[-1][1]


def load(path):
    """-> (objects, render_res). `render_res` may be None; the caller REFUSES on
    that rather than carrying on, and the reason was found by running this rung
    for the first time on a real artefact instead of a synthetic one.

    The scene of record that day was `room_bedroom_suite_eye_p2r90_ql.blend` — a
    `_ql` PLAYBLAST, stored at 1200x900 while the delivered frame is 2400x1800.
    Every `mm_per_px` in it is therefore TWICE the delivered figure and every
    "how many pixels does this edge subtend" answer is HALF, so the first live
    report read 0.18 px on a millwork carcass that delivers at 0.36. Both numbers
    say the same thing here, which is exactly why it would have been easy to keep
    and wrong to keep: the day the two answers straddle a threshold, a report with
    no resolution on it is a wrong answer with no way to tell.

    R11's pixel rung already wrote the law for this in its own words — a sub-pixel
    comparison at half resolution is a DIFFERENT MEASUREMENT, and the rung refuses
    rather than rescaling. Refusing rather than doubling is the same choice: this
    file does not get to decide what the delivered resolution is."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    objs = doc.get("objects") if isinstance(doc, dict) else doc
    if not isinstance(objs, list):
        raise ValueError("no `objects` list in this dump")
    res = doc.get("render_res") if isinstance(doc, dict) else None
    if not (isinstance(res, (list, tuple)) and len(res) == 2
            and all(isinstance(v, (int, float)) and v > 0 for v in res)):
        res = None
    return objs, res


def measure(objs):
    """-> (rows, n_bevelled_in_frame, n_unmeasurable, n_no_bevel, area_no_bevel).

    Rows are in-frame, drawn, bevelled objects that could be measured, biggest
    surface area first. THE MASSES WITH NO BEVEL AT ALL ARE COUNTED SEPARATELY AND
    NOT DROPPED: a mass with no bevel modifier is a knife edge, which is the
    definitive answer to this file's own title question, and the first version of
    this function `continue`d past it so the worst case never printed. It is not a
    rare case — `_bevel_edges` skips every `ph_model` mass, so every acquired glTF
    object in the scene is structurally outside the bevelled population."""
    rows, unmeasurable = [], 0
    n_bev = 0
    n_no_bev, area_no_bev = 0, 0.0
    for o in objs:
        if o.get("hidden_render"):
            continue
        if o.get("bevel_m") is None:
            if o.get("in_frustum") is not False:
                n_no_bev += 1
                area_no_bev += float(o.get("area_m2") or 0.0)
            continue
        # in_frustum absent = the dump had no camera = unknown, not "out of frame".
        if o.get("in_frustum") is False:
            continue
        n_bev += 1
        px = bevel_px(o)
        if px is None:
            unmeasurable += 1
            continue
        rows.append({"name": o.get("name", "?"),
                     "px": px,
                     "mm": float(o["bevel_m"]) * 1000.0,
                     "segments": o.get("bevel_segments"),
                     "area_m2": float(o.get("area_m2") or 0.0),
                     "mm_per_px": float(o["mm_per_px"])})
    rows.sort(key=lambda r: -r["area_m2"])
    return rows, n_bev, unmeasurable, n_no_bev, area_no_bev


def main(argv):
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                   # noqa: BLE001
            pass
    if len(argv) != 1:
        print("usage: edge_highlight.py <room_*.scene.json>", file=sys.stderr)
        return 2
    path = argv[0]
    try:
        objs, res = load(path)
    except Exception as e:                                  # noqa: BLE001
        print(f"COULD NOT RUN: {os.path.basename(path)} — {e}", file=sys.stderr)
        return 2

    if res is None:
        print(f"COULD NOT RUN: {os.path.basename(path)} carries no `render_res`, "
              f"so the pixel counts below would have no resolution attached. A "
              f"playblast .blend stores 1200x900 where the delivered frame is "
              f"2400x1800 — the same edge reads 0.18 px or 0.36 px depending on "
              f"which one this dump came from, and this rung does not get to "
              f"guess. Re-run the build.", file=sys.stderr)
        return 2

    if not any(o.get("bevel_m") is not None for o in objs):
        print(f"COULD NOT RUN: no record in {os.path.basename(path)} carries a "
              f"`bevel_m` — either this scene bevels nothing (say so in the build, "
              f"not here) or the dump predates the key. Re-run the build.",
              file=sys.stderr)
        return 2
    if not any(o.get("mm_per_px") for o in objs):
        print(f"COULD NOT RUN: no record carries `mm_per_px` — the dump was written "
              f"with no camera in the scene, so millimetres cannot be turned into "
              f"pixels and 'can this edge be seen' has no answer here.",
              file=sys.stderr)
        return 2

    rows, n_bev, unmeasurable, n_no_bev, area_no_bev = measure(objs)
    if not rows:
        print("COULD NOT RUN: no in-frame bevelled mass could be measured "
              f"({n_bev} bevelled, {unmeasurable} without a camera behind them).",
              file=sys.stderr)
        return 2

    counts = {}
    for r in rows:
        counts[band(r["px"])] = counts.get(band(r["px"]), 0) + 1
    sub = sum(1 for r in rows if r["px"] < 1.0)

    print(f"measured at {int(res[0])}x{int(res[1])} — every pixel figure below is "
          f"AT THIS RESOLUTION; a playblast halves them against the delivered frame")
    print(f"{len(rows)} of {len(rows) + unmeasurable} in-frame bevelled masses "
          f"measured"
          + (f" · {unmeasurable} NOT measured (no camera behind them)"
             if unmeasurable else "")
          + (f" · {n_no_bev} in-frame masses carry NO bevel modifier at all "
             f"({area_no_bev:.1f} m², 0 px by construction — `_bevel_edges` skips "
             f"every ph_model/acquired mass)" if n_no_bev else ""))
    print("  " + " · ".join(f"{counts.get(n, 0)} {n}"
                            for _hi, n in BANDS if counts.get(n)))
    print(f"  {sub}/{len(rows)} ({100.0 * sub / len(rows):.0f}%) OF THE MEASURED "
          f"subtend LESS THAN ONE PIXEL — their edges cannot render a highlight at "
          f"this camera, whatever the light does"
          + (f" (the ratio is over the {len(rows)} measurable, not over the "
             f"{len(rows) + unmeasurable + n_no_bev} in-frame masses this rung saw)"
             if (unmeasurable or n_no_bev) else ""))
    print("  largest in-frame bevelled masses, by surface area:")
    for r in rows[:12]:
        seg = f"x{r['segments']}" if r["segments"] else ""
        print(f"    {r['name'][:44]:44s} {r['area_m2']:7.2f} m²  "
              f"{r['mm']:5.2f} mm{seg:3s} @ {r['mm_per_px']:5.2f} mm/px = "
              f"{r['px']:5.2f} px  [{band(r['px'])}]")
    print("  REPORTING LINE, NOT A CUT: the pixel width an edge highlight needs "
          "has never been measured off delivered work, and a threshold invented "
          "here would carry this file's authority instead of the anchor pool's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
