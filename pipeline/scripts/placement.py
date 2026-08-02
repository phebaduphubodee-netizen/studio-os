#!/usr/bin/env python3
"""placement.py — resolve a declared CONTACT into a world position. PURE: no bpy.

R9 (CLAUDE.md, owner order 2026-08-02): *a position that can be DERIVED from a
contact must never be TYPED.* This is the half that makes the defect class
unbuildable, rather than the half that catches it after the fact
(`placement_check.py`).

WHAT WAS WRONG WITH TYPING IT. A coordinate encodes a RESULT, never a
RELATIONSHIP. Resize the thing underneath and the stored triple stays perfectly
legal while the contact breaks in silence — nothing fails, because a coordinate is
always a legal coordinate. And with no declared parent, "centre it on the box" and
"stand it on the pedestal" become two edits to the SAME three numbers, so every
fix to one is a break to the other. That is rounds 15-18, in the spec's own words:
*"I optimised one relationship and broke another in the same edit, and did not
look at the second."*

A declaration cannot do that. `rest_on` and `centre_on` are two SEPARATE
statements; satisfying one cannot disturb the other, because neither is stored as
a number.

THE SCHEMA — everything is relative to a NAMED mass, never to the world:

    {"rest_on": "centre_box", "centre_on": "centre_box"}
    {"rest_on": "step", "mirror_about": "centre_box",
     "offset_x_mm": 920.9, "side": "L", "y_from": "step", "dy_mm": 10.5}
    {"rest_on": "plinth", "x_from": "plinth", "dx_mm": -268.8,
     "y_from": "plinth", "dy_mm": -117.0}

  z   <- rest_on            the TOP face of that mass (+ optional z_gap_mm)
  x,y <- centre_on          that mass's plan centre
  x   <- x_from + dx_mm     a MEASURED offset from a named datum's centre
  y   <- y_from + dy_mm     ditto
  x   <- mirror_about + offset_x_mm + side   one offset, two objects

IT FAILS CLOSED, AND THAT IS THE WHOLE POINT. An unknown mass name raises rather
than falling back to the origin — an asset that imports at the right scale and
lands at (0,0,0) while the log cheerfully reports it "placed" is a defect this
lane has already shipped. An axis left undetermined raises, because a silently
defaulted axis is exactly a typed coordinate with the typing hidden.

AND `nudge` IS BANNED BY NAME. `x_nudge_mm` was added to make a figure's
SILHOUETTE centre on a box, and it moved the figure across its own pedestal —
one number asked to satisfy two relationships. A nudge is not a fix; it is the
missing derivation wearing a knob. If a placement needs a correction, the
correction belongs in a named offset from a named datum, where the next reader can
see what it is measured FROM.
"""
NUDGE_KEYS = ("nudge", "fudge", "tweak", "offset_hack")


class PlacementError(ValueError):
    """Raised instead of guessing. Every message names the object and the axis."""


def support_table(masses):
    """{name: geometry} from the mass list. `c` is the centre, `s` the size."""
    t = {}
    for m in masses:
        c, s = m["c"], m["s"]
        t[m["name"]] = {"cx": c[0], "cy": c[1], "cz": c[2],
                        "w": s[0], "d": s[1], "h": s[2],
                        "top_z": c[2] + s[2] / 2.0,
                        "x0": c[0] - s[0] / 2.0, "x1": c[0] + s[0] / 2.0,
                        "y0": c[1] - s[1] / 2.0, "y1": c[1] + s[1] / 2.0}
    return t


def _mass(table, name, label, key):
    if name not in table:
        raise PlacementError(
            f"{label}: `{key}` names `{name}`, which is not a mass in this spec. "
            f"Refusing to guess — an object placed at a default lands at the world "
            f"origin while the log reports it placed.")
    return table[name]


def resolve(place, table, label="<object>"):
    """(x, y, z) in mm from a contact declaration. Raises rather than defaulting."""
    if not isinstance(place, dict) or not place:
        raise PlacementError(f"{label}: no `place` block. A position must be "
                             f"DERIVED from a contact, never typed (R9).")
    for k in place:
        kl = k.lower()
        if any(n in kl for n in NUDGE_KEYS):
            raise PlacementError(
                f"{label}: `{k}` is banned by R9. A nudge is the missing "
                f"derivation wearing a knob — it moved a figure off its own base "
                f"while centring it on a box. Express the correction as a named "
                f"offset from a named datum instead.")

    # --- z: what it stands on
    if "rest_on" not in place:
        raise PlacementError(f"{label}: no `rest_on`. Something has to hold it up.")
    sup = _mass(table, place["rest_on"], label, "rest_on")
    z = sup["top_z"] + float(place.get("z_gap_mm", 0.0))

    # --- x and y: exactly one source each, and no source is not an option
    x = y = None
    if "centre_on" in place:
        d = _mass(table, place["centre_on"], label, "centre_on")
        x, y = d["cx"], d["cy"]
    if "mirror_about" in place:
        if x is not None:
            raise PlacementError(f"{label}: `mirror_about` and `centre_on` both "
                                 f"claim x. Two sources for one axis is the defect "
                                 f"R9 exists to stop.")
        d = _mass(table, place["mirror_about"], label, "mirror_about")
        side = place.get("side")
        if side not in ("L", "R"):
            raise PlacementError(f"{label}: `mirror_about` needs side 'L' or 'R', "
                                 f"got {side!r}.")
        if "offset_x_mm" not in place:
            raise PlacementError(f"{label}: `mirror_about` needs `offset_x_mm`.")
        x = d["cx"] + (-1 if side == "L" else 1) * float(place["offset_x_mm"])
    if "x_from" in place:
        if x is not None:
            raise PlacementError(f"{label}: two sources claim x.")
        x = _mass(table, place["x_from"], label, "x_from")["cx"] \
            + float(place.get("dx_mm", 0.0))
    if "y_from" in place:
        if y is not None and "centre_on" in place:
            raise PlacementError(f"{label}: two sources claim y.")
        y = _mass(table, place["y_from"], label, "y_from")["cy"] \
            + float(place.get("dy_mm", 0.0))

    for axis, val in (("x", x), ("y", y)):
        if val is None:
            raise PlacementError(
                f"{label}: {axis} is undetermined. A silently defaulted axis is a "
                f"typed coordinate with the typing hidden — declare `centre_on`, "
                f"`{axis}_from`, or (for x) `mirror_about`.")
    return (x, y, z)


def contains(place, table, footprint_mm, pos, label="<object>", tol_mm=0.0):
    """Does the resolved footprint sit on the support it declares?

    The DECLARATION half of what `placement_check.py` measures in the built scene.
    Checking here as well is not duplication: this one runs before a single vertex
    exists and names the spec field that is wrong, while that one sees the geometry
    that actually rendered. Neither can replace the other — a spec-side check
    cannot see an object the spec does not know about, and a scene-side check
    cannot say which declaration to edit."""
    sup = table[place["rest_on"]]
    hw, hd = footprint_mm[0] / 2.0, footprint_mm[1] / 2.0
    over = max(sup["x0"] - (pos[0] - hw), (pos[0] + hw) - sup["x1"],
               sup["y0"] - (pos[1] - hd), (pos[1] + hd) - sup["y1"])
    if over > tol_mm:
        raise PlacementError(
            f"{label}: hangs {over:.1f}mm past `{place['rest_on']}`, the thing it "
            f"declares it stands on. Either the support is the wrong one or the "
            f"offset is measured from the wrong datum.")
    return True
