"""front_registry.py — the FRONT LAW's pure half. No bpy, no PIL, no network.

qa/model-front-registry.json holds one MEASURED row per model id a spec mass
names: `front_deg` (azimuth of the mesh's functional front at rot 0, probed by
front_probe.py and sighted-signed) or null + `no_front_reason` for a
rotation-invariant mass.

WHY (2026-08-26, debate proposal 1 — owner-approved). `model_rot` in
build_room.py fail-opened with `.get(slug, -90.0)`, so every acquired asset —
whose slug is a UUID guaranteed absent from the hand-typed table — got an
ASSUMED native front. Scale has been asserted at every ingest since P2r-9;
orientation never was. What that cost, measured the night this landed: the
Asta nightstands shipped with their drawer fronts in the wall they hug (gate
claim "verified from crop"; the owner refuted it from the render the same
day), and the vanity tub chair — native front 0, not -90 — rendered 90 degrees
off in every frame since it entered the spec, and nothing noticed.

THE THREE RUNGS THIS MODULE FEEDS:
  * build_room.model_rot — FAILS CLOSED on a missing row (the consumer that
    cannot be skipped: an unprobed model stops the build).
  * the item loop — a mass may declare `facing_derive` and the rot is DERIVED
    (placement.face_rot); `rot` + `facing_derive` together is refused.
  * rule_gate.check_room — `check_spec` below: a mass whose model has a
    numeric front may not carry a typed `rot` (R9 applied to rotation, with
    the same stop-loss logic: the p2r74->p2r75 nightstands were two typed
    facings, both wrong). `face_lines` prints spec-rot -> world-front per
    model mass into the render path, via facing_reader — the instrument that
    could answer "which way does this face" and had zero callers.
"""
import json
import os

import facing_reader as _fr
import placement as _pl

REGISTRY_REL = "qa/model-front-registry.json"
_MISSING = object()


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def load(root=None, path=None):
    """The registry dict, or None. Never raises — an unreadable registry must
    surface as a violation that names the file, not a traceback."""
    p = path or os.path.join(root or _root(), REGISTRY_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def front_deg(reg, model_id):
    """front_deg for a model id: a float, None (explicitly no front), or
    _MISSING when the registry has no row — three states, never two."""
    row = ((reg or {}).get("models") or {}).get(str(model_id))
    if row is None:
        return _MISSING
    return row.get("front_deg")


def is_missing(v):
    return v is _MISSING


def resolve_rot(spec_rot, front):
    """THE LAW, pure and testable: place_model.rot = spec_rot - 90 - front.
    A null front (rotation-invariant) passes spec_rot through unchanged."""
    if front is None:
        return float(spec_rot)
    return float(spec_rot) - 90.0 - float(front)


def spec_rot_of(item, label=None):
    """The item's SPEC-convention rot: derived from `facing_derive` when
    declared, else the typed `rot`, else 0. Raises PlacementError on two
    sources — same refusal as two sources for one axis in placement.resolve."""
    lbl = label or item.get("name") or item.get("kind") or "<item>"
    fd = item.get("facing_derive")
    if fd is not None:
        if "rot" in item:
            raise _pl.PlacementError(
                f"{lbl}: both `rot` and `facing_derive` claim the facing — "
                f"two sources for one axis (R9).")
        return _pl.face_rot(fd, lbl)
    return float(item.get("rot", 0.0))


def _model_items(spec):
    for it in (spec or {}).get("items", []) or []:
        if isinstance(it, dict) and it.get("model"):
            yield it


def check_spec(reg, spec, path_hint=REGISTRY_REL):
    """Violations, all the builder's side. `spec` None -> [] (the caller's
    roster says the rung could not run; silence must not read as a pass)."""
    if spec is None:
        return []
    v = []
    if reg is None:
        return [f"model-front registry unreadable at {path_hint} — every "
                f"spec-named model needs a MEASURED front row, and 'could not "
                f"look' must never print like 'looked and it was fine'."]
    for it in _model_items(spec):
        lbl = it.get("name") or it.get("kind") or "<item>"
        mdl = str(it.get("model"))
        fr = front_deg(reg, mdl)
        if is_missing(fr):
            v.append(f"{lbl}: model '{mdl}' has NO row in {path_hint}. Probe "
                     f"it (front_probe.py), sign the azimuth (or null + "
                     f"reason), and the build unblocks — an assumed front is "
                     f"how the nightstands faced the wall with every rung "
                     f"green.")
            continue
        if "rot" in it and it.get("facing_derive") is not None:
            v.append(f"{lbl}: both `rot` and `facing_derive` — two sources "
                     f"for one facing (R9).")
        elif fr is not None and "rot" in it:
            v.append(f"{lbl}: model '{mdl}' has a MEASURED front "
                     f"({fr:+.0f}°) and the spec TYPES its facing "
                     f"(rot {it.get('rot')}). Two typed facings on the "
                     f"nightstands were both wrong; declare the relationship "
                     f"(`facing_derive`: away_from_wall / toward_wall) and "
                     f"delete the number.")
        if it.get("facing_derive") is not None:
            try:
                spec_rot_of(it)
            except _pl.PlacementError as e:
                v.append(str(e))
    return v


def face_lines(spec, reg):
    """One printable line per model mass: where its front ends up in world.
    This is the line that, printed at p2r75, would have read 'front E — into
    the wall' while the gate said 'verified from crop'."""
    out = []
    for it in _model_items(spec or {}):
        lbl = it.get("name") or it.get("kind") or "<item>"
        mdl = str(it.get("model"))
        fr = front_deg(reg, mdl)
        if is_missing(fr):
            out.append(f"FRONT {lbl}: model '{mdl[:12]}…' UNMEASURED — "
                       f"model_rot will refuse this build")
            continue
        try:
            srot = spec_rot_of(it)
        except _pl.PlacementError as e:
            out.append(f"FRONT {lbl}: {e}")
            continue
        card = _fr.facing_from_rot(srot)
        src = "derived" if it.get("facing_derive") is not None else "typed"
        if fr is None:
            out.append(f"FRONT {lbl}: no functional front (registry) — "
                       f"rot {srot:g} passes through")
        else:
            out.append(f"FRONT {lbl}: spec rot {srot:g} ({src}) -> front "
                       f"{card or f'{srot:g}°'} "
                       f"(native {fr:+.0f}°, applied {resolve_rot(srot, fr):g})")
    return out


def summary(reg, spec):
    models = list(_model_items(spec or {}))
    if reg is None:
        return f"registry UNREADABLE; {len(models)} model mass(es) in spec"
    rows = (reg.get("models") or {})
    have = sum(1 for it in models if str(it.get("model")) in rows)
    derived = sum(1 for it in models if it.get("facing_derive") is not None)
    return (f"{have}/{len(models)} spec model(s) carry a measured front row; "
            f"{derived} facing(s) derived, {len(models) - derived} typed/none")
