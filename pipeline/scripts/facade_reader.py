"""
facade_reader.py -- F4/F3: a ZONE-SCOPED reader that, per room, proposes the GLAZED FACADE
line on the room's south edge -- a clean 0..2 candidates the owner can scan and SIGN, instead
of hunting the ~300 thin-wall candidates the GLOBAL glazing_candidates pass dumps on a furnished
sheet.

    python facade_reader.py <plan.pdf> <walls.json> <out.json> <manifest.json>

WHY (measured on the real floor-2 sheet, PRJ-2026-002): glazing_candidates promotes EVERY thin
dark run with structural evidence (pair / wall-contact / length) across the WHOLE sheet -> 298
candidates, nearly all "strong", overwhelmingly furniture double-lines. The real south glazed
facade IS in there (a 0.48 pt pair at y~=99 & y~=200, ~4.9 m) but drowned; the owner cannot scan
298, so they still hand-annotate the boundary every design. zone_flag.facade_corroborated then
consumes that noisy list and authorises a facade on a LOW bar (any strong horizontal spanning
>=50% of the south edge just-south of it) -- a bar a furniture pair-run that happens to span the
edge can also trip.

This module is the missing PRODUCER (facade_corroborated stays the CONSUMER/authoriser, now fed a
clean per-room list). Per room it:
  1. SCOPES to a tight per-room south band BEFORE any scoring -- the datum is the room's own
     south (min-y) OUTLINE edge y_s (owner-drawn, never the inferred glazing line; same discipline
     as zone_flag rule 0). Band c-window [y_s - band_south(600), y_s + band_north(300)]: 600 mm
     south is < the ~1150 mm garden slab-lip offset, so the OUTER garden edge is excluded
     STRUCTURALLY by position (not luck-of-ranking); 300 mm north catches the real inner+frame
     pair yet stays inside the nearest indoor furniture (~585 mm in) so interior lines don't enter.
  2. requires a facade-SPECIFIC signature furniture double-lines structurally fail: a parallel
     PAIR (40..250 mm, glass drawn as glass+frame twins), a run length >= min_len(2000 mm), and a
     span of the OPEN part of the edge >= span_frac(0.7). A furniture double-line spans <1 m of a
     ~5 m edge -> rejected on span AND length. A WALLED south edge (collinear thick wall covering
     >= edge_cover_frac(0.6) of the span -- the exact union test zone_flag uses) makes the room
     ABSTAIN (no facade).
  3. emits the INNER member of each pair (nearest to y_s = the glass line, what corroboration
     wants), ranked by |c - y_s|, capped at 2, tier "glazed_facade", schema-compatible with
     zone_flag.facade_corroborated / _glazing_between (fields axis/score/c/span), so it is a
     DROP-IN corroboration feed.

HONESTY CONTRACT (mirrors glazing_candidates.py + pdf_extract_walls.merge_carried): the reader only
PROPOSES. It never writes placement-review.json, never sets corroborated on its own authority. The
output ships a confirm_facade_stub whose `by` is OWNER-CONFIRM-PENDING with an EMPTY (null) decision
-- a template, never pre-filled. The DURABLE truth lives in an owner sign (placement_gate.
confirmed_facade), which refuses to activate until `by` names the owner. Two-layer law: WHERE the
thin line is = machine-solved geometry; WHETHER it is glass = owner-signed facade-truth (the only
thing that STICKS across rebuilds). This module never FAILs a build and never auto-applies a class.

DEFERRED (honest): non-south / L-shaped / clerestory facades (v1 reads the south min-y edge only,
matching facade_datum's scope + the verified F3 case; a return leg abstains, never misfires); the
reconcile_facade geo-orphan lane; the render-layer glass-aperture that a signed facade could open;
the lower-width replay knob (ground truth confirms 0.48 pt is already inside extract_thin's gate --
width-0 is NOT the wound here). CAP-2 LIMITATION: candidates rank by |c - y_s| and cap at 2, so if
TWO OR MORE genuinely-distinct full-span (>=2000 mm, >=0.7 of the open edge) paired double-lines sat
NEARER the datum than the real facade, they could evict it -- physically implausible (the furniture
length+span defense clears the ~99 mm frame slot south of the glass, and the real sheet yields
exactly one such pair), but it is a real property; the owner sign is the backstop.
"""
import json
import os
import sys
import time

# pure geometry reused from the settled thin-line library (no fitz at these import sites)
from glazing_candidates import merge_runs, find_pair, run_endpoints, extract_thin
from pdf_extract_walls import _valid_seg
# pure facade helpers reused from the zone flagger (datum discipline + wall-union coverage)
from zone_flag import facade_datum, _axis_seg, _span_cover_frac

SCHEMA = "interior-ai/facade-candidates@0.1"

DEFAULTS = dict(
    off_tol=6.0,          # mm; merge_runs c-band (matches glazing_candidates so runs agree)
    gap_tol=160.0,        # mm; merge_runs along-axis bridge (door-frame breaks)
    pair_gap=(40.0, 250.0),   # mm; glass+frame twin separation (real facade pair: 101.6)
    pair_overlap=0.5,     # fraction of the shorter run the pair must overlap on-axis
    band_south=600.0,     # mm; how far SOUTH of y_s a facade run may sit (< garden slab-lip ~1150)
    band_north=300.0,     # mm; how far NORTH of y_s (into the room) -- catches the frame twin, but
    #                       < nearest indoor furniture (~585 mm) so interior lines don't enter
    span_frac=0.7,        # a facade spans >= this fraction of the OPEN part of the south edge
    min_len=2000.0,       # mm; a facade run is long (furniture double-lines are <1 m) -- backstop
    #                       so a short edge cannot let an ~800 mm furniture twin reach span_frac
    facade_wall_tol=120.0,    # mm; collinearity band for "thick wall runs along the edge"
    edge_cover_frac=0.6,  # edge is CLOSED (walled -> abstain) if walls cover >= this of the span
)


def _params(params=None):
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    return p


# ---- pure geometry (NO fitz -> unit-testable) -----------------------------------------
def facade_band(outline, params=None):
    """The room's south datum + suspect band, from its OWN south (min-y) outline edge. Reuses
    facade_datum verbatim so the reader and zone_flag pin the datum identically."""
    p = _params(params)
    y_s, xlo, xhi = facade_datum(outline)
    return {"y_s": y_s, "xlo": xlo, "xhi": xhi,
            "band_lo": y_s - p["band_south"], "band_hi": y_s + p["band_north"]}


def open_edge_span(y_s, xlo, xhi, wall_segs, params=None):
    """(walled_frac, open_span). walled_frac = UNIONED coverage of collinear thick-wall ink within
    facade_wall_tol of y_s over [xlo,xhi] (the exact test zone_flag.facade_corroborated uses -- on
    the union, so a wall decomposed into ~200 mm segments still counts); open_span = the length of
    the edge NOT backed by wall. A run's facade span is measured against open_span, so a mostly-
    walled edge with a small glass slot is judged on the slot, not the whole edge."""
    p = _params(params)
    ivs = []
    for s in wall_segs or []:
        a = _axis_seg(s)
        if a is None or a[0] != "h":
            continue
        if abs(a[1] - y_s) <= p["facade_wall_tol"]:
            ivs.append((a[2], a[3]))
    walled_frac = _span_cover_frac(ivs, xlo, xhi)
    open_span = max(0.0, (xhi - xlo)) * (1.0 - walled_frac)
    return walled_frac, open_span


def classify_facade(runs, y_s, xlo, xhi, wall_segs, params=None):
    """Glazed-facade candidates for ONE room's south edge, from merged horizontal RUNS. Returns
    0..2 dicts (schema-compatible with zone_flag.facade_corroborated). A run qualifies iff: it is
    horizontal and its c sits in the band [y_s-band_south, y_s+band_north]; the south edge is OPEN
    (walled_frac < edge_cover_frac -- else the whole room ABSTAINS); it has a parallel PAIR mate
    (40..250 mm); the INNER member (nearest y_s) is >= min_len; and that member spans >= span_frac
    of the OPEN edge. Emits the inner member (the glass line, deduped per pair), ranked |c - y_s|."""
    p = _params(params)
    walled_frac, open_span = open_edge_span(y_s, xlo, xhi, wall_segs, p)
    if walled_frac >= p["edge_cover_frac"] or open_span <= 0:
        return []                                   # walled-south firewall / degenerate edge

    def _span_frac(r):
        ov = min(r["hi"], xhi) - max(r["lo"], xlo)
        return max(0.0, ov) / open_span if open_span > 0 else 0.0

    band = [r for r in runs if r.get("axis") == "h"
            and p["band_south"] * -1 <= (r["c"] - y_s) <= p["band_north"]]
    # Keep ONLY long runs that span the open edge BEFORE pairing. This is the furniture defense:
    # a furniture double-line is short and spans <1 m of a ~5 m edge, so it is dropped here and can
    # neither surface itself nor STEAL the facade's pair (find_pair takes the nearest-gap mate, so a
    # furniture line 50 mm off the glass would otherwise out-compete the real frame twin 100 mm off).
    qualified = [r for r in band if r["length"] >= p["min_len"] and _span_frac(r) >= p["span_frac"]]
    cands = []
    seen_inner = set()
    for i, r in enumerate(qualified):
        mate = find_pair(i, qualified, p["pair_gap"], p["pair_overlap"])
        if mate is None:
            continue                                # a facade is drawn as glass + frame twins;
        #                                             a lone spanning run (glass? thin wall?) abstains
        a, b = qualified[i], qualified[mate]
        inner, outer = (a, b) if abs(a["c"] - y_s) <= abs(b["c"] - y_s) else (b, a)
        # dedupe on the emitted INNER line's POSITION, NOT the (i,mate) index-pair: in a cluster of
        # >=3 spanning runs the near-datum run is find_pair's mate for several pairs, so an index-pair
        # key would emit that ONE physical line 2-3x and (worse, under cap 2) evict the real facade.
        # Keyed on rounded c (not id) so two collinear runs at one position collapse even if a caller
        # hands in unmerged runs (merge_runs already unions within off_tol, so this is belt-and-braces).
        ikey = round(inner["c"], 1)
        if ikey in seen_inner:
            continue
        seen_inner.add(ikey)
        span_frac = _span_frac(inner)
        score = 3 + 1 + (1 if span_frac >= 0.9 else 0)   # base(spanning+open) + pair + full-width
        (x1, y1), (x2, y2) = run_endpoints(inner)
        cands.append({
            "axis": "h", "c": inner["c"], "span": [inner["lo"], inner["hi"]],
            "length_mm": inner["length"], "score": score, "tier": "glazed_facade",
            "span_frac": round(span_frac, 3), "pair_c": outer["c"],
            "evidence": {"walled_frac": round(walled_frac, 3), "open_span": round(open_span, 1),
                         "pieces": inner.get("pieces"), "coverage": inner.get("coverage")},
            "segments": [[[round(x1, 1), round(y1, 1)], [round(x2, 1), round(y2, 1)]]],
        })
    cands.sort(key=lambda c: abs(c["c"] - y_s))
    return cands[:2]


def facade_candidates(thin_segs, wall_segs, rooms, params=None):
    """Run the classifier per room over shared merged thin runs. rooms = [(room_id, outline_abs)].
    Returns (flat candidates each tagged with 'room', per_room {room_id: n}). Runs are merged ONCE
    from the whole-sheet thin ink; the per-room band-filter is what scopes each room's scan."""
    p = _params(params)
    runs = merge_runs([s for s in (thin_segs or []) if _valid_seg(s)], p["off_tol"], p["gap_tol"])
    all_cands, per_room = [], {}
    for room_id, outline in rooms:
        try:
            y_s, xlo, xhi = facade_datum(outline)
        except (ValueError, IndexError, TypeError):
            per_room[room_id] = 0                   # a malformed outline scans nothing, never crashes
            continue
        rc = classify_facade(runs, y_s, xlo, xhi, wall_segs, p)
        for c in rc:
            c2 = dict(c)
            c2["room"] = room_id
            all_cands.append(c2)
        per_room[room_id] = len(rc)
    return all_cands, per_room


# ---- PDF side (fitz only at the edge; core above stays importable/testable) ------------
def _rooms_from_manifest(manifest_path):
    """(rooms, calib_note). rooms = [(room_id, outline_abs)] walked EXACTLY like placement_gate.run:
    id = furnish.id or spec.room.type; outline = room.outline_mm + offset_mm. A spec missing an
    outline is skipped (it scans nothing), never crashes the reader."""
    man_dir = os.path.dirname(os.path.abspath(manifest_path))
    man = json.load(open(manifest_path, encoding="utf-8"))
    rooms = []
    for f in man.get("furnish", []):
        sp = f.get("spec")
        if not sp:
            continue
        cand = sp if os.path.isabs(sp) and os.path.exists(sp) else os.path.join(man_dir, os.path.basename(sp))
        try:
            spec = json.load(open(cand, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        outline = (spec.get("room") or {}).get("outline_mm")
        if not isinstance(outline, list) or len(outline) < 3:
            continue
        off = tuple(f.get("offset_mm", [0, 0]))
        outline_abs = [[p[0] + off[0], p[1] + off[1]] for p in outline]
        rooms.append((f.get("id", (spec.get("room") or {}).get("type", "room")), outline_abs))
    return rooms


def render_facade_overlay(pdf, page, calib, cands, out_png, dpi=200):
    """Paint the classified facade line(s) over the TRUE sheet raster (same extent math as
    raster_overlay / render_candidates_overlay so frames can never disagree). GREEN = the facade
    line the owner scans; the owner then signs (or rejects) ONE line per glazed room, not 298."""
    import fitz
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    scale, ox, oy = calib
    doc = fitz.open(pdf)
    p = doc[page]
    pix = p.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    zoom = dpi / 72.0
    wpt, hpt = pix.width / zoom, pix.height / zoom
    ext = [(0 - ox) * scale, (wpt - ox) * scale, (oy - hpt) * scale, (oy - 0) * scale]
    fig, ax = plt.subplots(figsize=(pix.width / dpi * 1.1, pix.height / dpi * 1.1))
    ax.imshow(img, extent=ext, origin="upper", aspect="equal", zorder=0)
    for c in cands:
        (x1, y1), (x2, y2) = c["segments"][0]
        ax.plot([x1, x2], [y1, y2], color="#00a020", lw=2.4, alpha=0.9, zorder=3,
                solid_capstyle="butt")
        ax.annotate(f"{c.get('room', '')} facade  c={c['c']:.0f}", (min(x1, x2), (y1 + y2) / 2),
                    color="#00a020", fontsize=7, va="bottom")
    ax.set_title(f"GLAZED-FACADE candidates -- owner review, nothing auto-injected "
                 f"({len(cands)} line(s), one per glazed room)", fontsize=9)
    ax.set_xlabel("mm east")
    ax.set_ylabel("mm north")
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_png


def main():
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    pdf, walls_path, out, manifest = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    meta = json.load(open(walls_path, encoding="utf-8"))
    scale = meta["scale_mm_per_pt"]
    x0, y0 = meta["origin_pt"]
    page = meta["page"]
    src = os.path.basename(str(meta.get("source_pdf", ""))).replace("\\", "/").split("/")[-1]
    if src and os.path.basename(pdf) != src:
        print(f"WARNING: walls JSON was calibrated on '{src}', got '{os.path.basename(pdf)}' "
              f"-- coordinates are only valid if this is the same drawing")
    wall_segs = [s for s in meta.get("segments", []) if _valid_seg(s)]
    thin = extract_thin(pdf, page, scale, x0, y0)
    rooms = _rooms_from_manifest(manifest)
    cands, per_room = facade_candidates(thin, wall_segs, rooms)

    # a purely informational contrast: the global thin-wall dump the owner scans today (if present)
    global_glazing = None
    gpath = os.path.join(os.path.dirname(os.path.abspath(out)), "glazing-candidates.json")
    if os.path.exists(gpath):
        try:
            global_glazing = len((json.load(open(gpath, encoding="utf-8")) or {}).get("candidates", []))
        except (ValueError, OSError):
            global_glazing = None

    doc_out = {
        "schema": SCHEMA,
        "source_pdf": os.path.basename(pdf), "page": page,
        "walls_json": os.path.basename(walls_path),
        "scale_mm_per_pt": scale, "origin_pt": [x0, y0],
        "params": {k: v for k, v in DEFAULTS.items()},
        "stats": {"thin_segments": len(thin), "rooms_scanned": len(rooms),
                  "rooms_with_facade": sum(1 for n in per_room.values() if n),
                  "facade_candidates_total": len(cands),
                  "global_glazing_candidates": global_glazing,
                  "per_room": per_room},
        "candidates": cands,
        # a TEMPLATE, deliberately EMPTY of a decision: the owner sets facade true|false + the line,
        # then replaces `by` with a real signature. placement_gate.confirmed_facade refuses to
        # activate any entry whose `by` still says OWNER-CONFIRM-PENDING, so an unsigned paste is
        # machine-INERT (never flips corroboration). MERGE into placement-review.json's confirmed[].
        "confirm_facade_stub": {
            "date": time.strftime("%Y-%m-%d"),
            "by": "OWNER-CONFIRM-PENDING (unsigned template; confirmed_facade refuses to "
                  "activate until this names the owner)",
            "reason": "confirm the room's south edge: set facade true (glazed) or false (no glass / "
                      "kill-switch); if true, copy the candidate's c + span. Sign `by`. "
                      "MERGE into placement-review.json confirmed[] -- do not replace it.",
            "room": "", "facade": None, "c": None, "span": [],
        },
    }
    tmp = out + ".tmp"
    json.dump(doc_out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, out)
    overlay = os.path.splitext(out)[0] + ".png"
    try:
        render_facade_overlay(pdf, page, (scale, x0, y0), cands, overlay)
        print(f"wrote {overlay} (scan artifact: green = the glazed-facade line, one per glazed room)")
    except Exception as _e:                          # overlay is a convenience; JSON is the contract
        print(f"  [!] overlay skipped: {_e}")
    contrast = f" (vs {global_glazing} global glazing candidates)" if global_glazing is not None else ""
    print(f"wrote {out}: {len(cands)} glazed-facade candidate(s) across "
          f"{doc_out['stats']['rooms_with_facade']}/{len(rooms)} rooms{contrast}; "
          f"nothing auto-injected -- owner signs confirmed_facade to make it stick")
    for c in cands:
        print(f"  [{c['room']:>14}] c={c['c']:>8.1f}  span {c['span'][0]:.0f}..{c['span'][1]:.0f}  "
              f"len {c['length_mm']:>7.0f}  span_frac {c['span_frac']}  pair_c {c['pair_c']:.1f}  "
              f"score {c['score']}")


if __name__ == "__main__":
    main()
