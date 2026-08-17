"""BED-CLOTH ACQUISITION BENCH — measure every candidate set against THIS bed,
before any of them costs a build.

Run:  blender -b <built>.blend --python bedcloth_bench.py -- <cache_dir> <out.json>
                                                            [slug,slug,...]

WHY IT EXISTS: p2r31's first acquired leg rendered a bare white mattress with a
knotted rag on it, and the coverage guard inside the build passed it — because that
guard compared BOUNDING BOXES, and a bounding box cannot tell a spread sheet from a
crumpled one (R9b's own lesson: an AABB cannot tell interlocking from intersecting).
This measures the thing itself, by ray.

REWRITTEN p2r41, and the reason is the finding of that round. This file used to carry
its OWN copy of the staging rules, and the copy was the pre-p2r32 one: parts were kept
only at >= 33% of the mattress plan, so every accessory cloth — one set's 374 x 1600 mm
turned-down runner among them — was DELETED before the candidate was measured or
photographed. From p2r32 to p2r41 the build dressed the bed with runners and the
audition judged the same files without them. It also computed a rotation and never
applied it. Staging now comes from `bedcloth_fit`, the module the build itself uses:
the audition and the frame cannot be two different objects again.

WHAT IS MEASURED, all derived from the bed in the open .blend — nothing typed:
  coverage    fraction of mattress plan points with cloth above them (RAY)
  relief_mm   p90-p10 spread of cloth height over the mattress
  fall_sides  how many of the four flanks carry cloth below the mattress top
  need_scale  the scale this asset needs to COVER this mattress — the spec's own
              `model_requirements.covers` rule (max_scale 1.0: never stretch)

AND THE RANK IS NOT COVERAGE, which is the mistake that decided a purchase. p2r31
ranked on coverage, and coverage is MAXIMISED by a cloth that lies flat on the mattress
without reaching past it — a duvet too small to drape scores best. The number that
answers the real question was printed in the same table and read past: falls past 2 of
4 sides. So the machine now applies four HARD filters and then stops:

    size_ok      need_scale <= 1.0     (a mesh is never stretched to fit)
    covered      coverage   >= 0.80    (the build's own cut: our mattress must not
                                        show through)
    drapes       fall_sides >= 2       (a cover falls over the flanks; on a bed
                                        against a headboard the reachable maximum
                                        is 3 — two sides and the foot)
    fine_enough  median world edge <= the coarsest BOUGHT cloth already accepted
                                        in this frame (p2r46; the control comes
                                        from the open .blend, not from a number)

THE FOURTH ONE IS NEW HERE AND THAT IS THE POINT. The first three all ask whether a
set FITS; none can see what the mesh is MADE OF, and 0afd4c6f passed all three at
43.5 mm against acquired pillows at 4.5-10.3 mm in the same frame — the build then
refused it on a cut this bench could not apply, because the control was derived
INLINE IN THE BUILD. An audition that cannot ask the build's question is an audition
that wastes the eye, which is the same defect as p2r32's deleted runners one rule on.

relief_mm stays REPORT-ONLY with both of its failure directions named — a crumple
(the signed DD says the room is made, not slept in) and a painted plane (what both
critics have filed for three rounds). No number in this repo can currently ground a
band for it, and inventing one would be taste wearing a threshold. The eye decides
style; the machine's job is only to stop the eye wasting time on sets that cannot fit,
cannot cover, or cannot drape. That split is the owner's practitioner rung, made into
a tool.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedcloth_fit as fit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE, OUT = argv[0], argv[1]
ONLY = set(argv[2].split(",")) if len(argv) > 2 and argv[2] else None

COVER_CUT = 0.80
FALL_CUT = 2
MAX_SCALE = 1.0

matt = bpy.data.objects["bed__mattress"]
mw = [matt.matrix_world @ v.co for v in matt.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
RECT = (MX0, MY0, MX1 - MX0, MY1 - MY0)
base = bpy.data.objects.get("bed__base")
bw = [base.matrix_world @ v.co for v in base.data.vertices] if base else mw
BZ = max(c.z for c in bw)                 # base top = where a hem may reach
# CEILING and FLOOR, both derived from the bed (see bedcloth_fit.plan_scale). The
# rule this replaces used min(bed outer line, mattress + 40 mm) as a TARGET, which on
# this bed is 1800 x 1949 against a mattress of 1820 x 1969 — it shrank every
# candidate to smaller than the thing it must cover.
LIMIT, COVER = fit.limits_for(RECT, MTOP, BZ)

# THE FINENESS CONTROL, read from this same .blend BEFORE the shipped bedding is
# stripped below: the acquired soft goods already ACCEPTED in this frame (membership
# from value_ladder.ACQUIRED_AS, never a list kept here). A candidate cover may not
# be coarser than the coarsest bought cloth standing beside it at the same distance
# from the same camera. Empty dict = the cut cannot run, which is NOT a pass.
CONTROL = fit.control_edges()
print("BENCH fineness control: " + (
    ", ".join(f"{k} {v:.1f} mm" for k, v in sorted(CONTROL.items()))
    + f"  -> limit {max(CONTROL.values()):.1f} mm" if CONTROL else
    "NONE — no acquired soft-goods mesh in this .blend, so the fineness cut "
    "CANNOT RUN and no candidate can survive it"))

print(f"BENCH bed: mattress {RECT[2]*1000:.0f} x {RECT[3]*1000:.0f} mm, top "
      f"{MTOP*1000:.0f}, base top {BZ*1000:.0f}, fall {(MTOP-BZ)*1000:.0f} mm; "
      f"must cover {COVER[0]*1000:.0f} x {COVER[1]*1000:.0f}, may not exceed "
      f"{LIMIT[0]*1000:.0f} x {LIMIT[1]*1000:.0f} x {LIMIT[2]*1000:.0f} mm "
      f"at scale <= {MAX_SCALE}")

# strip the bedding the build shipped so it cannot be measured as a candidate's cloth
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ("cloth__acq" in o.name or o.name in
                             ("bed__coverlet", "bed__duvet", "bed__throw")):
        bpy.data.objects.remove(o, do_unlink=True)

# WHAT THE FRAME HAS ALREADY DRESSED, read AFTER the strip above so the cloth being
# replaced is not in it. A candidate part landing inside one of these is that object
# bought twice — the set's own pillows on top of ours (D-025). Same signed register
# as the fineness control; see `bedcloth_rules.duplicate_of_placed`.
AVOID = fit.acquired_objs()
print("BENCH already dressed (candidate parts overlapping these are dropped): "
      + (", ".join(o.name for o in AVOID) if AVOID else "nothing"))

rows = []
for slug in sorted(os.listdir(CACHE)):
    d = os.path.join(CACHE, slug)
    if not os.path.isdir(d) or (ONLY and slug not in ONLY):
        continue
    glbs = [f for f in os.listdir(d) if f.endswith(".glb")]
    if not glbs:
        continue
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=os.path.join(d, glbs[0]))
    except Exception as e:                                    # noqa: BLE001
        rows.append({"slug": slug, "error": str(e)[:120]})
        print(f"BENCH {slug:14s} IMPORT FAILED: {str(e)[:60]}")
        continue
    news = [o for o in bpy.data.objects if o not in before]
    names = [o.name for o in news]
    row = {"slug": slug, "file": glbs[0]}
    st = fit.stage(news, RECT, MTOP, BZ, LIMIT, cover=COVER, max_scale=MAX_SCALE,
                   avoid=AVOID)
    if "reject" in st:
        row.update({"verdict": st["reject"], "parts_total": st.get("parts_total"),
                    "need_scale": st.get("need_scale"),
                    "native_mm": st.get("native_mm"), "survives": False})
        print(f"BENCH {slug:14s} — {st['reject']}")
    else:
        # THE CUTS COME FROM `bedcloth_rules`, NOT FROM A COPY HERE (p2r47). This
        # file used to recompute all three inline, which is the exact shape its own
        # docstring is about: a rule spread across its callers is a rule with one
        # exemption per caller. `size_ok` is now reported and does not decide — see
        # `bedcloth_rules.survives`.
        need = st["need_scale"]
        row3 = fit.survives(need, st["scale"], st["coverage"], st["fall_sides"],
                            COVER_CUT, FALL_CUT)
        size_ok, covered, drapes = row3["size_ok"], row3["covered"], row3["drapes"]
        # MEDIAN EDGE LENGTH, world mm, AND THE CUT — not just the rank (p2r46).
        # The three cuts above all ask whether the set FITS; none of them can see
        # what it is MADE OF, and the set this bench chose renders at 43.2 mm
        # against acquired pillows at 4.5-10.3 in the same frame. From p2r45 this
        # number was measured here and only RANKED on, because the control lived
        # inline in the build — so the audition nominated 0afd4c6f on three cuts
        # and the build refused it on a fourth the audition could not see. The
        # control is now `fit.control_edges()`, the same call the build makes, read
        # from the SAME open .blend the bed rect comes from. An audition that
        # cannot ask the build's question is an audition that wastes the eye.
        edge = max((fit.edge_mm(o) or 0.0) for o in st["field"]) or None
        # AND THE COVER'S OWN EDGE BESIDE IT. The cut stays on the COARSEST visible
        # field part — a coarse sheet the camera can see is a coarse sheet whichever
        # part it is — but a set whose cover is fine and whose underlayer is not is a
        # different fact from a set that is coarse throughout, and the row could not
        # tell them apart.
        cov_obj = bpy.data.objects.get(st.get("cover_name") or "")
        cov_edge = fit.edge_mm(cov_obj) if cov_obj is not None else None
        fine = fit.fineness(edge, CONTROL)
        row.update({
            "edge_mm": None if edge is None else round(edge, 1),
            "cover_edge_mm": None if cov_edge is None else round(cov_edge, 1),
            "cover_name": st.get("cover_name"),
            "fine_enough": fine["fine_enough"], "fineness": fine,
            "parts_total": st["parts_total"], "field": len(st["field"]),
            "extra": len(st["extra"]), "dropped": st["parts_dropped"],
            "buried": st["parts_buried"], "scale": round(st["scale"], 3),
            "rot": st["rot"], "native_mm": st["native_mm"],
            "coverage": round(st["coverage"], 3),
            "relief_mm": round(st["relief_mm"], 1),
            "fall_sides": st["fall_sides"], "need_scale": round(need, 3),
            "size_ok": size_ok, "covered": covered, "drapes": drapes,
            "survives": bool(row3["survives"] and fine["fine_enough"] is True)})
        print(f"BENCH {slug:14s} {len(st['field'])}F+{len(st['extra'])}E of "
              f"{st['parts_total']:2d}  scale {st['scale']:5.3f}  "
              f"cover {st['coverage']*100:5.1f}%  relief {st['relief_mm']:6.1f} mm  "
              f"fall {st['fall_sides']}/4  need {need:5.3f}x"
              f"{'' if size_ok else '!'}  "
              f"edge {('%6.1f mm' % edge) if edge else '   n/a '}"
              f"{(' (cover %.1f)' % cov_edge) if cov_edge else ''}  "
              f"{'SURVIVES' if row['survives'] else 'out: ' + ','.join(
                  k for k, ok in (('cover', covered), ('drape', drapes),
                                  ('fine', fine['fine_enough'])) if ok is not True)}")
    rows.append(row)
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"bed": {"mattress_mm": [round(RECT[2] * 1000), round(RECT[3] * 1000)],
                       "limit_mm": [round(v * 1000) for v in LIMIT],
                       "must_cover_mm": [round(v * 1000) for v in COVER],
                       "fall_mm": round((MTOP - BZ) * 1000)},
               "cuts": {"coverage": COVER_CUT, "fall_sides": FALL_CUT,
                        "max_scale": MAX_SCALE,
                        "fineness_control_mm": (max(CONTROL.values())
                                                if CONTROL else None),
                        "fineness_control": (max(CONTROL, key=CONTROL.get)
                                             if CONTROL else None)},
               "candidates": rows}, fh, indent=1)
# SURVIVORS ARE RANKED FINEST-FIRST, and the rank is the only thing that decides
# an ORDER here — the three cuts decide membership. p2r31 ranked on coverage and
# coverage is maximised by the failure; this ranks on the number that separated the
# meshes the critics accept from the one they called carved plastic.
surv = sorted((r for r in rows if r.get("survives")),
              key=lambda r: (r.get("edge_mm") is None, r.get("edge_mm") or 0.0))
print(f"BENCH wrote {OUT} ({len(rows)} candidate(s), {len(surv)} survive all four "
      f"cuts, finest mesh first): "
      + (", ".join(f"{r['slug']} ({r['edge_mm']} mm)" for r in surv)
         if surv else "(none)"))
