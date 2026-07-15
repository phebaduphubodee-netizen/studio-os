"""Sellability-benchmark PRE-CUT: turn the 1,144 raw candidates into the smallest, cleanest
pool of DELIVERED-render ANCHORS a designer has to bucket by room type -- and no more.

This is step 1 of the lane in qa/benchmark-sellability.md. It does ONLY what a machine can do
HONESTLY under the standing LOCAL-ONLY owner decision, and refuses to fake the two things it can't:

  WHAT THE MACHINE DOES (here):
    - strips the client's personal name off every project -> I-code only (I-24-020). The raw
      folder names carry real names (คุณ..., K.หมอ...); the standing decision forbids a personal
      name anywhere that can egress, so every artifact this writes is I-CODED.
    - separates site photos from renders by ASPECT, not size. The naive "max-dim >= 3000 = photo"
      filter drops 429 real renders (181 are 16:9, 170 are named Enscape_*): a 4K render is
      3840x2160, a phone photo is 4032x3024. Site photo := 4:3 aspect AND >=3000px AND not
      render-engine-named. Enscape provenance OVERRIDES size -- a named render is a render.
    - flags COMMERCIAL projects (hospital/clinic/hotel/spa/fitness/clubhouse/office) so the
      residential-lane benchmark isn't anchored to an operating-theatre render.
    - marks near-identical re-exports (aHash, same I-code) as an ADVISORY dup cluster. It NEVER
      deletes a candidate -- a false-merge would silently cost a distinct anchor, so dups are
      TAGGED (dup_of) and both survive; the designer sees the merge and can split it.
    - ranks residential render-anchors per project so the designer works the richest projects
      first and stops once 2-3 room types have >=2 anchors each.

  WHAT THE MACHINE REFUSES TO DO (designer-only, by construction):
    - ROOM TYPE. The one thing that needs eyes on the pixels -- and pixels may not enter any LLM
      context (that is the exact reason the Gemini judge is off the table). So room_type is a
      BLANK worksheet column the designer fills. The instrument does not guess a room it cannot see.
    - DELIVERY. "Actually delivered/paid" lives in the thread context, which the designer confirms.
      slug=='update' is recorded as a WEAK proposed signal, never as a fact. is_delivered is a
      blank worksheet column too.

  A pre-cut that GUESSED room type or ASSERTED delivery would be the flattering-scorer wearing a
  triage vest: it would hand the designer a bar built from the machine's own unverifiable labels.

Privacy: writes only under _private/ (gitignored). precut.json keeps real paths so the designer
can open the images locally (candidates.json already does, same gitignored pool). The human
worksheet and this script's STDOUT are I-CODED -- nothing that can egress carries a name.
NOTHING here calls any network. Refuses to overwrite a real pre-cut with an empty one.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Thai paths under piped cp1252

# ---------------------------------------------------------------------------
# FROZEN CONSTANTS. Every one of these is mutation-probed in test_benchmark_precut.py:
# flip it and a known fixture must change class, or the probe is a no-op. _assert_frozen()
# raises if any drifts, so a silent edit can't move the bar without a test noticing.
# ---------------------------------------------------------------------------
PHOTO_ASPECT = 4.0 / 3.0        # iPhone/site-camera native aspect
PHOTO_ASPECT_TOL = 0.05         # |aspect - 4:3| < this  => "4:3-class"
PHOTO_MIN_DIM = 3000            # a 4:3 image this large with no render name is a site photo
RENDER_MIN_DIM = 1000           # below this, too small to be a delivery-grade anchor
# Render-engine provenance in the filename => it is a render regardless of size/aspect.
# Substring match (uppercased). D5 Render actually exports 'D5_Render_*' / 'D5 Render' -- the
# old contiguous 'D5RENDER' token could never match its own engine (review: engine-token-fn).
RENDER_ENGINE_TOKENS = ("ENSCAPE", "ENSC", "LUMION", "VRAY", "V-RAY", "CORONA",
                        "D5_RENDER", "D5 RENDER", "D5RENDER")
# Commercial / non-residential markers (folder name). Our render lanes are residential; a
# hospital or hotel anchor is a different bar. Thai + English, matched case-insensitively.
# NOTE: substring match against the folder name -- a false-EXCLUDE (e.g. a home-office caught by
# "office") is made auditable by serializing every commercial exclusion + its matched keyword into
# precut.json['excluded'], NOT by guessing the keyword set perfectly (review: sector lens).
COMMERCIAL_KEYWORDS = (
    "รพ.", "โรงพยาบาล", "hospital", "คลินิก", "clinic", "ทันตกรรม", "dental",
    "โรงแรม", "โฮเทล", "hotel", "สปา", "spa", "fitness", "ฟิตเนส",
    "clubhouse", "คลับเฮ้าส์", "office", "ออฟฟิศ", "สำนักงาน", "แผนกการเงิน", "แผนกห้องคลอด",
    "ร้าน", "ร้านอาหาร", "คาเฟ่", "cafe", "restaurant", "โชว์รูม", "showroom", "retail",
)
# Top-level path segments known to be generic Discord channel categories -- SAFE to print. Any
# other segment-0 value is scrubbed to "OTHER-SLUG" before it can reach stdout/worksheet, so an
# upstream manifest whose first segment ever carried a client name cannot leak it (review: the
# one egress-capable field that was not I-coded). The I-code column is the real identifier.
SAFE_SLUGS = ("update", "โปรเจ็ก", "bluehouse")
# Room words that appear IN a folder name -> a weak room hint (most residential projects are
# whole-house and carry no room word, so this is usually None). Never a substitute for the
# designer's room_type; only surfaced as a hint.
ROOM_HINTS = {
    "ห้องน้ำ": "bathroom", "bathroom": "bathroom",
    "ห้องนอน": "bedroom", "bedroom": "bedroom",
    "ห้องนั่งเล่น": "living", "living": "living",
    "ห้องครัว": "kitchen", "ครัว": "kitchen", "kitchen": "kitchen",
    "ห้องคลอด": "delivery-room", "การเงิน": "finance-dept",
}
PHASH_SIDE = 8                  # aHash grid -> 64-bit
PHASH_HAMMING_MAX = 4           # <= this (same I-code) => advisory dup. Low on purpose: bias to
#                                 UNDER-merge, since a false-merge silently costs a real anchor.
ICODE_RE = re.compile(r"([IF])-(\d{2})-(\d{3})")

_FROZEN = {
    "PHOTO_ASPECT": PHOTO_ASPECT, "PHOTO_ASPECT_TOL": PHOTO_ASPECT_TOL,
    "PHOTO_MIN_DIM": PHOTO_MIN_DIM, "RENDER_MIN_DIM": RENDER_MIN_DIM,
    "PHASH_SIDE": PHASH_SIDE, "PHASH_HAMMING_MAX": PHASH_HAMMING_MAX,
}
_FROZEN_EXPECT = {
    "PHOTO_ASPECT": 4.0 / 3.0, "PHOTO_ASPECT_TOL": 0.05, "PHOTO_MIN_DIM": 3000,
    "RENDER_MIN_DIM": 1000, "PHASH_SIDE": 8, "PHASH_HAMMING_MAX": 4,
}


def _assert_frozen():
    drift = {k: (v, _FROZEN_EXPECT[k]) for k, v in _FROZEN.items() if v != _FROZEN_EXPECT[k]}
    if drift:
        raise AssertionError(
            "benchmark_precut constants drifted (re-run mutation probes, then update _FROZEN_EXPECT "
            f"deliberately): {drift}")


# ---------------------------------------------------------------------------
# Pure classifiers (no I/O) -- every one directly testable on a fixture.
# ---------------------------------------------------------------------------
def extract_icode(project):
    """'update/002_I-24-020-คุณมิกซ์' -> 'I-24-020'. None if the folder carries no I/F code."""
    m = ICODE_RE.search(project or "")
    return m.group(0) if m else None


def slug_of(project):
    return (project or "").split("/", 1)[0]


def safe_slug(project):
    """The segment-0 slug IF it is a known generic category, else 'OTHER-SLUG'. This is the only
    field that egresses to stdout/worksheet un-I-coded; whitelisting it closes the latent leak of
    a name ever sitting in segment 0 (real data: always 'update'/'โปรเจ็ก'/'bluehouse')."""
    s = slug_of(project)
    return s if s in SAFE_SLUGS else "OTHER-SLUG"


def thread_num(project):
    """The 'NNN' ordinal after the slug: 'update/002_...' -> '002'. '' if absent."""
    tail = (project or "").split("/", 1)[-1]
    m = re.match(r"(\d{2,3})_", tail)
    return m.group(1) if m else ""


def render_engine(filename):
    up = (filename or "").upper()
    for tok in RENDER_ENGINE_TOKENS:
        if tok in up:
            return tok
    return None


def dim_class(wh, engine):
    """'site_photo' | 'render' | 'small'. A render-engine name overrides the photo test."""
    w, h = wh
    mx, mn = max(w, h), max(1, min(w, h))
    aspect = mx / mn
    if engine:                                   # named render: never a photo, never too-small
        return "render"
    is_43 = abs(aspect - PHOTO_ASPECT) < PHOTO_ASPECT_TOL
    if is_43 and mx >= PHOTO_MIN_DIM:
        return "site_photo"
    if mx < RENDER_MIN_DIM:
        return "small"
    return "render"


def is_photo_suspect(wh, engine):
    """A 4:3 image BELOW PHOTO_MIN_DIM with no engine name: kept in the pool (it may be a small
    render) but FLAGGED, so the designer eyeballs whether it is actually a downscaled phone photo.
    This surfaces the 1000-2999px 4:3 band the >=3000 site-photo cut cannot reach (review: the
    'photo-cleanliness claim' honesty gap) -- it flags, it never excludes."""
    if engine:
        return False
    w, h = wh
    mx, mn = max(w, h), max(1, min(w, h))
    return abs(mx / mn - PHOTO_ASPECT) < PHOTO_ASPECT_TOL and RENDER_MIN_DIM <= mx < PHOTO_MIN_DIM


def sector(project):
    """('commercial'|'residential', matched_keyword|None). Keyword logged so the call is auditable."""
    low = (project or "").lower()
    for kw in COMMERCIAL_KEYWORDS:
        if kw.lower() in low:
            return "commercial", kw
    return "residential", None


def room_hint(project):
    low = (project or "").lower()
    for word, room in ROOM_HINTS.items():
        if word.lower() in low:
            return room
    return None


def delivery_signal(project):
    """WEAK, PROPOSED only. Never asserts delivery -- the designer confirms from thread context."""
    return "update-thread (proposed, unconfirmed)" if slug_of(project) == "update" \
        else "project-thread (proposed, unconfirmed)"


# ---------------------------------------------------------------------------
# Perceptual hash -- LOCAL pixels only. Never printed; used only for Hamming distance.
# ---------------------------------------------------------------------------
def phash_of(path):
    """64-bit aHash, or None on any read error (the image is KEPT and tagged, never dropped)."""
    try:
        from PIL import Image  # local import: tests that don't hash needn't have PIL loaded here
        with Image.open(path) as im:
            im = im.convert("L").resize((PHASH_SIDE, PHASH_SIDE))
            px = list(im.tobytes())          # 'L' 8x8 -> 64 raw bytes (getdata is deprecated)
        avg = sum(px) / len(px)
        bits = 0
        for i, p in enumerate(px):
            if p >= avg:
                bits |= (1 << i)
        return bits
    except Exception:
        return None


def hamming(a, b):
    return bin(a ^ b).count("1")


def ref_of(path):
    """Stable opaque handle for the worksheet: <icode>/<thread>/<8hex>.<ext>. No personal name."""
    norm = (path or "").replace("\\", "/")   # candidates.json uses '/'; be robust to Windows '\'
    ic = extract_icode(norm) or "UNCODED"
    th = ""
    m = re.search(r"/(\d{2,3})_", norm)
    if m:
        th = m.group(1)
    ext = os.path.splitext(norm)[1].lower().lstrip(".") or "img"
    h8 = hashlib.md5(norm.encode("utf-8")).hexdigest()[:8]
    return f"{ic}/{th}/{h8}.{ext}"


# ---------------------------------------------------------------------------
# Core: classify -> dedup -> rank. Returns a plain dict (testable without any file writes).
# ---------------------------------------------------------------------------
def build_precut(candidates):
    """candidates: list of {path, bytes, project, wh}. Returns the pre-cut structure."""
    rows = []
    drops = collections.Counter()
    for c in candidates:
        path = c["path"]
        fn = os.path.basename(path)
        engine = render_engine(fn)
        dc = dim_class(c["wh"], engine)
        sec, kw = sector(c["project"])
        row = {
            "path": path,
            "ref": ref_of(path),
            "icode": extract_icode(c["project"]) or "UNCODED",
            "slug": safe_slug(c["project"]),          # scrubbed: never a raw segment-0 name
            "thread": thread_num(c["project"]),
            "wh": c["wh"],
            "maxdim": max(c["wh"]),
            "bytes": c.get("bytes"),
            "engine": engine,
            "dim_class": dc,
            "photo_suspect": is_photo_suspect(c["wh"], engine),
            "sector": sec,
            "commercial_kw": kw,
            "room_hint": room_hint(c["project"]),
            "delivery_signal": delivery_signal(c["project"]),
        }
        rows.append(row)

    # The anchor pool = residential renders. Everything excluded is COUNTED, never silently gone.
    pool, excluded = [], []
    for r in rows:
        if r["dim_class"] != "render":
            drops[f"dim_class={r['dim_class']}"] += 1
            r["excluded_by"] = f"dim_class={r['dim_class']}"
            excluded.append(r)
        elif r["sector"] == "commercial":
            drops["commercial"] += 1
            r["excluded_by"] = f"commercial:{r['commercial_kw']}"
            excluded.append(r)
        else:
            pool.append(r)

    # Advisory dedup: only within the same I-code, only near-identical. Tag, never delete.
    hash_errors = 0
    by_icode = collections.defaultdict(list)
    for r in pool:
        r["phash"] = phash_of(r["path"])
        if r["phash"] is None:
            hash_errors += 1
        by_icode[r["icode"]].append(r)
    dup_clusters = 0
    for ic, items in by_icode.items():
        reps = []  # (phash, representative_row)
        for r in items:
            r["dup_of"] = None
            if r["phash"] is None:
                continue
            merged = False
            for rep_hash, rep in reps:
                if hamming(r["phash"], rep_hash) <= PHASH_HAMMING_MAX:
                    # keep the higher-resolution one as representative
                    if r["maxdim"] > rep["maxdim"]:
                        rep["dup_of"] = r["ref"]
                        reps.remove((rep_hash, rep))
                        reps.append((r["phash"], r))
                        r["dup_of"] = None
                    else:
                        r["dup_of"] = rep["ref"]
                    merged = True
                    dup_clusters += 1
                    break
            if not merged:
                reps.append((r["phash"], r))
        # Flatten dup_of chains: the rep-swap branch above (a higher-res dup arriving LAST) can
        # leave an earlier dup pointing at a row that itself became a dup -- a two-hop DUP-> chain.
        # Resolve every dup_of to the FINAL representative so the worksheet pointer is canonical.
        ref_row = {r["ref"]: r for r in items}
        for r in items:
            guard = 0
            while r["dup_of"] is not None:
                tgt = ref_row.get(r["dup_of"])
                if tgt is None or tgt["dup_of"] is None or guard > len(items):
                    break
                r["dup_of"] = tgt["dup_of"]
                guard += 1

    # Rank projects by DISTINCT (non-dup) render count.
    proj = collections.defaultdict(lambda: {"anchors": [], "distinct": 0, "dups": 0,
                                            "slugs": set(), "room_hint": None})
    for r in pool:
        p = proj[r["icode"]]
        p["anchors"].append(r)
        p["slugs"].add(r["slug"])
        if r["dup_of"] is None:
            p["distinct"] += 1
        else:
            p["dups"] += 1
        if r["room_hint"] and not p["room_hint"]:
            p["room_hint"] = r["room_hint"]
    ranked = sorted(proj.items(), key=lambda kv: -kv[1]["distinct"])

    return {
        "rows": rows, "pool": pool, "excluded": excluded, "ranked": ranked,
        "drops": dict(drops), "hash_errors": hash_errors, "dup_clusters": dup_clusters,
        "n_candidates": len(candidates), "n_pool": len(pool),
        "n_distinct": sum(1 for r in pool if r["dup_of"] is None),
        "photo_suspect": [r for r in pool if r["photo_suspect"]],
    }


# ---------------------------------------------------------------------------
# Writers + CLI
# ---------------------------------------------------------------------------
def write_outputs(pc, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # Machine-readable (real paths retained for the designer to open images locally; gitignored).
    js = {
        "generated_by": "benchmark_precut.py",
        "curation_state": "PRE-CUT -- residential render-anchors triaged; "
                          "is_delivered + room_type still DESIGNER-ONLY",
        "constants": _FROZEN,
        "n_candidates": pc["n_candidates"],
        "n_pool": pc["n_pool"],
        "n_distinct": pc["n_distinct"],
        "drops": pc["drops"],
        "dup_clusters": pc["dup_clusters"],
        "hash_errors": pc["hash_errors"],
        # Per-item exclusion trace so a real render wrongly dropped as site_photo/small/commercial
        # is AUDITABLE, not just counted -- the docstring's "never silently gone" made literal
        # (review: accounting lens). Path retained (gitignored) so the designer can open + reclaim.
        "excluded": [
            {k: r[k] for k in ("path", "ref", "icode", "maxdim", "wh", "engine",
                               "dim_class", "excluded_by")}
            for r in sorted(pc["excluded"], key=lambda r: (r["excluded_by"], -r["maxdim"]))
        ],
        # 4:3 sub-3000 anchors KEPT in the pool but flagged for a photo-vs-render eyeball.
        "photo_suspect": [
            {k: r[k] for k in ("path", "ref", "icode", "maxdim", "wh")}
            for r in sorted(pc["photo_suspect"], key=lambda r: -r["maxdim"])
        ],
        "projects": [
            {
                "icode": ic, "distinct": p["distinct"], "dups": p["dups"],
                "slugs": sorted(p["slugs"]), "room_hint": p["room_hint"],
                "anchors": [
                    {k: r[k] for k in ("path", "ref", "thread", "maxdim", "wh", "engine",
                                       "room_hint", "delivery_signal", "dup_of")}
                    for r in sorted(p["anchors"], key=lambda r: (-r["maxdim"],))
                ],
            }
            for ic, p in pc["ranked"]
        ],
    }
    with open(os.path.join(out_dir, "precut.json"), "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1)

    # Human worksheet: I-CODED, two BLANK columns the designer fills. Real path kept for opening.
    lines = [
        "# Sellability pre-cut worksheet (DESIGNER FILLS is_delivered + room_type)",
        "",
        "The machine triaged residential renders and stripped names to I-codes. It did NOT and",
        "CANNOT judge room type (needs pixels -> banned from any LLM) or delivery (thread context).",
        "Work top-down (richest projects first); stop once 2-3 room types have >=2 delivered anchors.",
        "",
        f"- candidates: {pc['n_candidates']}   residential-render pool: {pc['n_pool']}   "
        f"distinct (post-dedup): {pc['n_distinct']}",
        f"- excluded: {pc['drops']}   advisory dup-merges: {pc['dup_clusters']}   "
        f"hash-errors(kept): {pc['hash_errors']}",
        f"- AUDIT (precut.json): {len(pc['excluded'])} per-item exclusions listed + "
        f"{len(pc['photo_suspect'])} photo-suspect anchors flagged (see sections below).",
        "",
        "| icode | distinct | dups | slugs | room_hint | DELIVERED?(Y/N) | ROOM_TYPE(fill) |",
        "|-------|---------:|-----:|-------|-----------|-----------------|-----------------|",
    ]
    for ic, p in pc["ranked"]:
        lines.append(f"| {ic} | {p['distinct']} | {p['dups']} | {'+'.join(sorted(p['slugs']))} "
                     f"| {p['room_hint'] or ''} |  |  |")
    lines += [
        "",
        "## Per-anchor (open via precut.json 'path'); ref = <icode>/<thread>/<hash>",
        "",
    ]
    for ic, p in pc["ranked"]:
        if p["distinct"] == 0:
            continue
        lines.append(f"### {ic}  ({p['distinct']} distinct, {p['dups']} dup)"
                     + (f"  hint={p['room_hint']}" if p["room_hint"] else ""))
        for r in sorted(p["anchors"], key=lambda r: (-r["maxdim"],)):
            tag = f"  DUP->{r['dup_of']}" if r["dup_of"] else ""
            eng = f" {r['engine']}" if r["engine"] else ""
            sus = "  [photo-suspect]" if r["photo_suspect"] else ""
            lines.append(f"- {r['ref']}  {r['maxdim']}px{eng}{tag}{sus}")
        lines.append("")

    # AUDIT sections -- the two ways the coarse filter can be wrong, both surfaced for eyeballing.
    sp = [r for r in pc["excluded"] if r["excluded_by"] == "dim_class=site_photo"]
    lines += [
        "## AUDIT-A photo-suspect anchors KEPT in pool (4:3, <3000px, no engine name)",
        "Eyeball these: a phone photo would be here, but so would a small legit render. None removed.",
        "",
    ] + [f"- {r['ref']}  {r['maxdim']}px  ({r['wh'][0]}x{r['wh'][1]})"
         for r in sorted(pc["photo_suspect"], key=lambda r: -r["maxdim"])] + [
        "",
        f"## AUDIT-B site_photo EXCLUSIONS ({len(sp)}) -- verify none is a lost 4:3 render",
        "These were dropped as site photos (4:3 & >=3000px & no engine). Open a few to confirm.",
        "",
    ] + [f"- {r['ref']}  {r['maxdim']}px  ({r['wh'][0]}x{r['wh'][1]})"
         for r in sorted(sp, key=lambda r: -r["maxdim"])[:40]]
    if len(sp) > 40:
        lines.append(f"- ... {len(sp) - 40} more in precut.json['excluded'] (excluded_by=site_photo)")
    with open(os.path.join(out_dir, "precut-worksheet.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_summary(pc):
    print(f"candidates={pc['n_candidates']}  residential-render pool={pc['n_pool']}  "
          f"distinct={pc['n_distinct']}  dup-merges={pc['dup_clusters']}  "
          f"hash-errors(kept)={pc['hash_errors']}")
    print(f"excluded: {pc['drops']}")
    print("top residential projects (I-coded) by distinct render-anchors:")
    for ic, p in pc["ranked"][:15]:
        if p["distinct"] == 0:
            continue
        hint = f"  hint={p['room_hint']}" if p["room_hint"] else ""
        print(f"  {ic:>10}  distinct={p['distinct']:3d}  dup={p['dups']:2d}  "
              f"slugs={'+'.join(sorted(p['slugs']))}{hint}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates",
                    default=os.path.join(REPO, "_private", "benchmark", "candidates.json"))
    ap.add_argument("--out-dir", default=os.path.join(REPO, "_private", "benchmark"))
    ap.add_argument("--self-check", action="store_true",
                    help="assert frozen constants and exit 0 (CI smoke)")
    args = ap.parse_args(argv)

    _assert_frozen()
    if args.self_check:
        print("frozen constants OK")
        return 0

    if not os.path.exists(args.candidates):
        sys.exit(f"no candidates manifest at {args.candidates} -- the pool is gitignored and absent "
                 "on this machine. Refusing to write an empty pre-cut over a real one.")
    data = json.load(open(args.candidates, encoding="utf-8"))
    candidates = data["images"] if isinstance(data, dict) else data
    if not candidates:
        sys.exit("candidates manifest is empty; refusing to write an empty pre-cut.")

    pc = build_precut(candidates)
    write_outputs(pc, args.out_dir)
    print_summary(pc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
