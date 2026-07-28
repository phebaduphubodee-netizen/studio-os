"""quicklook.py — R5 playblast-ladder rung parameters. PURE, no bpy.

THE RULE (knowledge/brand-standards/iteration-control-and-review-gates.md, R5,
adopted 2026-07-28): no full-frame deliverable render may be the FIRST look at a
change. The cheap rung exists to KILL bad work early (a crumpled bake, a dead
material, a camera that cannot see the decision) — it never CERTIFIES good work:
a gate still closes only on the full-fidelity pair (the amplitude-bisect law is
the recorded counterexample: an honest bump amplitude rendered as literally
nothing — visible only at full fidelity).

VFX grounding (playblast rule): nothing reaches the render farm without a cheap
preview passing first — full renders cost wall-clock hours, the preview verifies
plausibility in seconds. Here the whole build (cloth bakes included) still runs;
what the rung cuts is the RENDER spend, which dominated the 2026-07-28 round-3
waste (three failed bakes, each judged only after a full 256-sample frame).

Consumed by build_room.py (--quick). Kept pure so the ladder's arithmetic is
pytest-testable without Blender (LAYER LAW, pipeline/CLAUDE.md).
"""

# One rung, deliberately: a ladder with many knobs becomes a place to hide
# (R6: guard sets stay small and loud). 48 samples + OIDN denoise is enough for
# a LOOK verdict on shape/contact/read under this room's soft light; half
# resolution per axis = 1/4 the pixels.
QUICK_SAMPLES = 48
QUICK_SCALE = 0.5
QUICK_SUFFIX = "ql"


def quick_params(samples, res):
    """Deliverable (samples, (w, h)) -> the quick rung. Never returns MORE than
    the deliverable spend on either axis; never returns a zero dimension."""
    w, h = res
    return (min(QUICK_SAMPLES, int(samples)),
            (max(16, int(w * QUICK_SCALE)), max(16, int(h * QUICK_SCALE))))
