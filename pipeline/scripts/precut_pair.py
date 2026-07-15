"""precut_pair.py -- pair DESIGNER-LABELED delivered anchors against OUR render lane and emit
the 10-pair sellability pilot (qa/benchmark-sellability.md) for the DESIGNER to judge.

What this script refuses, and why (the same two refusals as benchmark_precut.py):
  * It NEVER assigns room_type to an anchor. Anchor room types come only from text the
    designer typed into the worksheet. Our OWN renders' room types come from their filenames
    (R_PRJ002_MasterSuite_Cam01_v01.png -> bedroom) -- that is provenance, not pixel-judging.
  * It NEVER promotes is_delivered. No label, no pair. A pilot paired against unconfirmed
    anchors would measure us against drafts -- a bar set low, wearing a benchmark's name.

Designer label grammar (either surface, both parsed; per-anchor beats project-row):
  * project table row: fill the last two cells   | ... | Y | bedroom |
  * per-anchor line:   append an arrow           - I-24-020/002/68888aac.jpg  5555px => Y bedroom
    (=> N marks not-delivered; room word may be Thai or English -- see ROOM_ALIASES)

Pairing law (from qa/benchmark-sellability.md):
  * same room type only; dup anchors never pair (their representative carries the cluster);
    photo-suspect anchors never pair until the eyeball audit clears them.
  * every unique pair is presented in BOTH A/B orders (position-bias tripwire);
  * tripwires ride along: the known-REWORK leg (must LOSE) and an anchor-vs-itself pair
    (must TIE), presented twice like everything else. Expectations live in the json and in a
    spoiler section BELOW the judging table -- never on the judging rows themselves.

Outputs (LOCAL-ONLY, all under _private/benchmark/, gitignored):
  pilot-pairs.md          the designer judging sheet -- I-CODED (anchors shown by ref, our
                          renders by basename; no client string reaches this file)
  pilot-pairs.json        machine/answer file: pairs + provenance + the tripwire spoiler
  pilot-anchor-paths.json ref -> real path ONLY, no spoiler -- the file the designer opens to
                          view an anchor image (keeps path-resolution off the answer key)
Exit codes: 0 = pilot written; 2 = WAITING on designer labels (how-to written instead);
1 = error / refused (existing sheet judged, unreadable input, --pairs < 1).
Privacy: stdout AND the md are I-CODED (refs/line-numbers, never a client name or raw label
text); the full client paths live only in the two gitignored json files.
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- room-type canonicalization: a WORD MAP for the designer's own label text. Adding an
# alias here is legal (string -> string); adding a heuristic that looks at the image is not.
# AMBIGUOUS words are the review's CRITICAL: in Thai the bare word "นั่งเล่น"/"ห้องนั่งเล่น"
# covers BOTH a living room and a private sitting room, and we run distinct `living` and
# `sitting` lanes. Silently routing it to one lane is the machine deciding a room distinction
# the designer did not make -- the exact refusal this script exists to hold. So an ambiguous
# word is SURFACED for disambiguation, never guessed (norm_room returns an "AMBIGUOUS:" marker).
ROOM_ALIASES = {
    "bedroom": {"bedroom", "master bedroom", "masterbedroom", "master", "master suite",
                "mastersuite", "bed", "ห้องนอน", "นอน", "ห้องนอนใหญ่", "ห้องนอนเล็ก"},
    "sitting": {"sitting", "sitting room", "sittingroom", "ห้องนั่งเล่นส่วนตัว"},
    "living": {"living", "living room", "livingroom", "ห้องรับแขก", "รับแขก"},
    "kitchen": {"kitchen", "ครัว", "ห้องครัว"},
    "bathroom": {"bathroom", "bath", "toilet", "wc", "ห้องน้ำ"},
    "dining": {"dining", "dining room", "ห้องอาหาร", "ห้องกินข้าว", "กินข้าว"},
}
ROOM_AMBIGUOUS = {
    "ห้องนั่งเล่น": ("sitting", "living"), "นั่งเล่น": ("sitting", "living"),
}
# our lane: filename Room token -> canonical room type (provenance, not pixels)
OUR_ROOMS = {"mastersuite": "bedroom", "masterbedroom": "bedroom", "bedroom": "bedroom",
             "sittingroom": "sitting", "livingroom": "living", "kitchen": "kitchen",
             "bathroom": "bathroom", "diningroom": "dining"}
RENDER_RE = re.compile(r"^R_PRJ(\d+)_([A-Za-z0-9]+)_Cam(\d+)_v(\d+)\.(png|jpe?g)$", re.I)
ARROW_RE = re.compile(r"=>\s*([YyNn])\b\s*(.*)$")
ANCHOR_LINE_RE = re.compile(r"^- (\S+/\S+)\s+(.*)$")
TABLE_ROW_RE = re.compile(r"^\|\s*([A-Z]+-\d{2}-\d{3}|UNCODED)\s*\|")
REF_RE = re.compile(r"^[A-Z]+-\d{2}-\d{3}/\w+/[0-9a-f]{6,}\.\w+$")   # I-coded ref shape

MAX_THREAD_REPEAT = 2       # per room type, at most 2 anchors from the same thread (diversity)
PARITY_MIN = 2              # the gate law: parity needs >= 2 delivered anchors per room type


def _row_cells(line):
    """A markdown table row -> its cells, tolerant of a missing leading/trailing pipe (GFM-legal
    and what Notepad/Obsidian/table-formatters routinely produce). '| a | b |' and 'a | b' and
    '| a | b' all yield ['a','b']. Load-bearing: the exact-cell-count checks this replaces were
    blind to a labeled row without a trailing pipe, and a re-gen then ERASED the label."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def norm_room(text):
    """Designer's room word -> canonical room type, an 'AMBIGUOUS:a|b' marker, or None.
    None and the marker are both SURFACED for the designer; neither is ever guessed into a lane."""
    t = re.sub(r"\s+", " ", (text or "").strip().lower())
    if not t:
        return None
    if t in ROOM_AMBIGUOUS:
        return "AMBIGUOUS:" + "|".join(ROOM_AMBIGUOUS[t])
    for canon, words in ROOM_ALIASES.items():
        if t == canon or t in words:
            return canon
    return None


def parse_worksheet_labels(text):
    """Both designer fill surfaces of precut-worksheet.md.
    Returns (project_labels {icode: (delivered, room_raw)}, anchor_labels {ref: (delivered,
    room_raw)}, malformed [{line_no, why} ...]). Only text the DESIGNER typed lands here.
    malformed carries LINE NUMBERS, never raw content -- a label line can hold a client name,
    and malformed is surfaced to the designer (privacy: content stays out of any egress channel).
    A U+FEFF BOM (editor re-save) is stripped so a labeled first row is not silently dropped."""
    project_labels, anchor_labels, malformed = {}, {}, []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.lstrip("﻿")
        stripped = line.strip()
        if TABLE_ROW_RE.match(stripped):
            cells = _row_cells(stripped)
            # [icode, distinct, dups, slugs, room_hint, DELIVERED, ROOM_TYPE] -> idx 5,6
            delivered = cells[5] if len(cells) > 5 else ""
            room = cells[6] if len(cells) > 6 else ""
            if not (delivered or room):
                continue
            flag = delivered.upper()
            if flag and flag not in ("Y", "N"):
                malformed.append({"line_no": i, "why": f"delivered cell is {delivered!r}, "
                                                        "not Y/N"})
                continue
            project_labels[TABLE_ROW_RE.match(stripped).group(1)] = (flag or None, room or None)
            continue
        am = ANCHOR_LINE_RE.match(stripped)
        if am and "=>" in stripped:
            arrow = ARROW_RE.search(stripped)
            if not arrow:
                malformed.append({"line_no": i, "why": "'=>' without a Y/N flag after it"})
                continue
            anchor_labels[am.group(1)] = (arrow.group(1).upper(), arrow.group(2).strip() or None)
    return project_labels, anchor_labels, malformed


def load_anchor_pool(precut):
    """Distinct, non-photo-suspect anchors with their precut metadata, keyed by ref."""
    suspects = {r["ref"] for r in precut.get("photo_suspect", [])}
    pool, dropped = {}, {"dup": 0, "photo_suspect": 0}
    for proj in precut["projects"]:
        for a in proj["anchors"]:
            if a.get("dup_of"):
                dropped["dup"] += 1
                continue
            if a["ref"] in suspects:
                dropped["photo_suspect"] += 1
                continue
            pool[a["ref"]] = {**a, "icode": proj["icode"]}
    return pool, dropped


def label_anchors(pool, project_labels, anchor_labels):
    """Attach designer labels. The per-anchor arrow OVERRIDES the project row, but a bare
    `=> Y` (flag only, no room word) INHERITS the row's room instead of wiping it -- a
    confirmation label must not silently drop the anchor (review MINOR, fail-safe but wasteful).
    Returns (delivered {ref: rec+room fields}, skipped_counts, unmatched [{ref, why}]).
    unmatched carries a WHY code, never the raw room word -- the word can name a client
    (privacy). A project-row label on the UNCODED bucket is REFUSED: that bucket aggregates
    unrelated clients' folders, so one row would fan a delivered+room stamp across different
    buildings -- label UNCODED anchors individually with `=>` (review MAJOR, refusal-integrity)."""
    delivered, unmatched = {}, []
    skipped = {"unlabeled": 0, "room_word_but_no_delivered_flag": 0, "not_delivered": 0,
               "no_room_word": 0, "unknown_room_word": 0, "ambiguous_room_word": 0,
               "uncoded_project_row_refused": 0}
    for ref, rec in pool.items():
        flag = room_raw = source = None
        if rec["icode"] in project_labels and rec["icode"] != "UNCODED":
            flag, room_raw = project_labels[rec["icode"]]
            source = f"project-row {rec['icode']}"
        elif rec["icode"] == "UNCODED" and rec["icode"] in project_labels:
            skipped["uncoded_project_row_refused"] += 1
            # not `continue` -- an anchor-line label below can still legitimately label it
        if ref in anchor_labels:
            aflag, aroom = anchor_labels[ref]
            flag = aflag                                  # delivery always overrides
            if aroom is not None:                          # room overrides only when GIVEN;
                room_raw = aroom                           # a bare `=> Y` keeps the row's room
                source = "anchor-line"
            else:
                source = source or "anchor-line (flag only)"
        if flag is None:
            skipped["room_word_but_no_delivered_flag" if room_raw else "unlabeled"] += 1
            continue
        if flag != "Y":
            skipped["not_delivered"] += 1
            continue
        if not room_raw:
            skipped["no_room_word"] += 1
            unmatched.append({"ref": ref, "why": "delivered=Y but no room word "
                                                 "(add one, or fill the project row)"})
            continue
        room = norm_room(room_raw)
        if room is None:
            skipped["unknown_room_word"] += 1
            unmatched.append({"ref": ref, "why": "room word not recognized"})
            continue
        if room.startswith("AMBIGUOUS:"):
            skipped["ambiguous_room_word"] += 1
            unmatched.append({"ref": ref, "why": "ambiguous Thai room word -- type one of: "
                                                 + room.split(":", 1)[1].replace("|", " / ")})
            continue
        delivered[ref] = {**rec, "room_type": room, "room_word": room_raw,
                          "label_source": source}
    return delivered, skipped, unmatched


def discover_our_lane(renders_dir):
    """Our renders by (room, cam) -> latest version. Room type from the FILENAME (provenance)."""
    latest = {}
    unknown = []
    if not os.path.isdir(renders_dir):
        return {}, unknown
    for fn in sorted(os.listdir(renders_dir)):
        m = RENDER_RE.match(fn)
        if not m:
            continue
        room_tok = m.group(2).lower()
        room = OUR_ROOMS.get(room_tok)
        if room is None:
            unknown.append(fn)
            continue
        # key on the LOWERCASED token: RENDER_RE is case-insensitive, so MasterSuite vs
        # Mastersuite would otherwise be two lanes and a superseded version would survive as
        # a live leg (review MINOR: "superseded renders as ours").
        key = (room, room_tok, int(m.group(3)))
        v = int(m.group(4))
        if key not in latest or v > latest[key][0]:
            latest[key] = (v, fn)
    ours = {}
    for (room, room_tok, cam), (v, fn) in sorted(latest.items()):
        ours.setdefault(room, []).append({
            "name": fn, "path": os.path.join(renders_dir, fn),
            "provenance": f"our render lane: {room_tok} Cam{cam:02d} latest v{v:02d}"})
    return ours, unknown


def pick_anchors(cands, k):
    """Top-k by maxdim, at most MAX_THREAD_REPEAT per thread (diversity, deterministic)."""
    out, per_thread = [], {}
    for a in sorted(cands, key=lambda a: (-a["maxdim"], a["ref"])):
        if per_thread.get((a["icode"], a["thread"]), 0) >= MAX_THREAD_REPEAT:
            continue
        out.append(a)
        per_thread[(a["icode"], a["thread"])] = per_thread.get((a["icode"], a["thread"]), 0) + 1
        if len(out) >= k:
            break
    return out


def _anchor_view(a):
    return {k: a[k] for k in ("ref", "path", "icode", "thread", "maxdim",
                              "room_word", "label_source", "delivery_signal")}


def _pair_key(room, ours_path, anchor_ref):
    """A CONTENT hash, stable across re-runs regardless of how many labels exist. pair_id
    (P01..) renumbers positionally when the set changes; pair_key does not, so a future tool
    can carry verdicts across a relabel (review MAJOR: positional identity loses prior work)."""
    h = hashlib.sha256(f"{room}|{os.path.basename(ours_path or '')}|{anchor_ref or ''}".encode())
    return "K" + h.hexdigest()[:10]


def build_pairs(delivered, ours, budget, tripwire_rework, tripwire_room):
    """Real pairs (round-robin across room lanes) + tripwires. Deterministic throughout."""
    by_room = {}
    for rec in delivered.values():
        by_room.setdefault(rec["room_type"], []).append(rec)
    lanes = []          # room types we can actually pair, richest first
    no_lane = sorted(r for r in by_room if r not in ours)
    for room in sorted(by_room, key=lambda r: (-len(by_room[r]), r)):
        if room in ours:
            lanes.append(room)

    pairs, n = [], 0
    # ANCHOR-major within a lane: (a0,o0),(a0,o1),(a0,o2),(a1,o0)... so every one of our
    # cameras is shown before an anchor repeats. o-major starved the later cameras under the
    # budget (review MINOR: Cam03 got zero rows though the budget could cover it).
    combos = {room: [(o, a) for a in pick_anchors(by_room[room], PARITY_MIN * len(ours[room]))
                     for o in ours[room]]
              for room in lanes}
    cursor = {room: 0 for room in lanes}
    while n < budget and any(cursor[r] < len(combos[r]) for r in lanes):
        for room in lanes:
            if n >= budget:
                break
            if cursor[room] >= len(combos[room]):
                continue
            o, a = combos[room][cursor[room]]
            cursor[room] += 1
            pairs.append({
                "pair_id": f"P{n + 1:02d}",
                "pair_key": _pair_key(room, o["path"], a["ref"]),
                "room_type": room,
                "below_parity_minimum": len(by_room[room]) < PARITY_MIN,
                "ours": o, "anchor": _anchor_view(a), "tripwire": None})
            n += 1

    tripwires = []
    rework_anchors = pick_anchors(by_room.get(tripwire_room, []), 2)
    if not tripwire_rework or not os.path.exists(tripwire_rework):
        # NEVER silent: a missing leg-C file drops the protocol-mandated must-lose control, so
        # the pilot must DISCLOSE it, not ship looking complete (review MAJOR).
        tripwires.append({"pair_id": "T-REWORK-UNAVAILABLE", "room_type": tripwire_room,
                          "unavailable": "the known-REWORK leg file is missing (%s) -- the "
                                         "must-LOSE control cannot run; DO NOT trust verdicts "
                                         "until it does" % (tripwire_rework or "<none>"),
                          "tripwire": {"kind": "known-rework-must-lose"}})
    elif not rework_anchors:
        tripwires.append({"pair_id": "T-REWORK-WAITING", "room_type": tripwire_room,
                          "unavailable": f"no delivered '{tripwire_room}' anchors labeled "
                                         "yet -- the known-REWORK tripwire waits",
                          "tripwire": {"kind": "known-rework-must-lose"}})
    else:
        for i, a in enumerate(rework_anchors):
            tripwires.append({
                "pair_id": f"T{i + 1:02d}", "room_type": tripwire_room,
                "pair_key": _pair_key(tripwire_room, tripwire_rework, a["ref"]),
                "below_parity_minimum": len(by_room.get(tripwire_room, [])) < PARITY_MIN,
                "ours": {"name": os.path.basename(tripwire_rework), "path": tripwire_rework,
                         "provenance": "KNOWN-REWORK leg (3-leg C, scored 1.5)"},
                "anchor": _anchor_view(a),
                "tripwire": {"kind": "known-rework-must-lose",
                             "expectation": "our side LOSES; a win means the harness is "
                                            "broken, not good news"}})
    all_anchors = [a for room in lanes for a in by_room[room]] \
        or [a for cands in by_room.values() for a in cands]
    if all_anchors:
        a = pick_anchors(all_anchors, 1)[0]
        tripwires.append({
            "pair_id": "TS01", "room_type": a["room_type"],
            "pair_key": _pair_key(a["room_type"], a["path"], a["ref"]),
            "ours": None, "anchor": _anchor_view(a),
            "tripwire": {"kind": "anchor-vs-itself",
                         "self_identifying": True,
                         "note": "same image both sides -- the judge WILL see it is a tie. That "
                                 "is fine: this row exists for the position-bias check (does the "
                                 "judge always pick a side?), which a knowing judge cannot fake.",
                         "expectation": "TIE (or 50/50 across the two presentations); a "
                                        "consistent side-preference is a judge/position defect"}})
    return pairs, tripwires, no_lane, by_room


def display_map(pairs, tripwires):
    """path -> I-CODED display token. Anchor paths show their REF (Discord basenames are
    uploader-controlled and can carry a client name -- review CRITICAL); our own renders and
    the rework leg show their basename (R_PRJ.../leg_c -- no client string)."""
    disp = {}
    for p in pairs + tripwires:
        if p.get("unavailable"):
            continue
        disp[p["anchor"]["path"]] = p["anchor"]["ref"]
        if p.get("ours"):
            disp[p["ours"]["path"]] = os.path.basename(p["ours"]["path"])
    return disp


def presentation_rows(pairs, tripwires):
    """Every judgeable pair twice (both orders), deterministically shuffled. The self-tie
    tripwire is the same image on both sides; it is presented twice for the 50/50 check.
    The shuffle seed is CONTENT-based (the actual image identities), so two same-shape pilots
    with different anchors do NOT put the tripwires at the same J-positions (review MINOR:
    a shape-only seed made tripwire positions learnable across sheets)."""
    rows = []
    for p in pairs + tripwires:
        if p.get("unavailable"):
            continue
        if p["tripwire"] and p["tripwire"]["kind"] == "anchor-vs-itself":
            left = right = p["anchor"]["path"]
            rows.append({"pair_id": p["pair_id"], "order": "AA", "left": left, "right": right})
            rows.append({"pair_id": p["pair_id"], "order": "AA2", "left": left, "right": right})
            continue
        ours, anch = p["ours"]["path"], p["anchor"]["path"]
        rows.append({"pair_id": p["pair_id"], "order": "ours-left", "left": ours, "right": anch})
        rows.append({"pair_id": p["pair_id"], "order": "ours-right", "left": anch, "right": ours})
    seed = hashlib.sha256(("pilot-v1:" + ",".join(sorted(
        r["pair_id"] + r["order"] + os.path.basename(r["left"]) + os.path.basename(r["right"])
        for r in rows))).encode()).hexdigest()
    random.Random(seed).shuffle(rows)
    for i, r in enumerate(rows):
        r["row"] = f"J{i + 1:02d}"
    return rows


def sheet_has_verdicts(text):
    """True iff an existing pilot sheet already carries designer work in the verdict OR note
    cell of any judging row (never overwrite either -- a note without a verdict is still hand
    labor the machine cannot re-derive)."""
    for line in text.splitlines():
        cells = _row_cells(line)
        if not cells or not re.match(r"^J\d+$", cells[0]):
            continue
        # [Jnn, LEFT, RIGHT, verdict, note] -- any cell PAST the RIGHT column (idx 2) that
        # carries text is designer work. Checking the tail (not fixed idx 3/4) survives a
        # dropped trailing pipe / a verdict typed in an odd column -- the exact shapes that
        # made the old exact-count guard OVERWRITE a judged sheet (review MAJOR, data-loss).
        if any(c for c in cells[3:]):
            return True
    return False


# pilot-pairs.json  = pairs/presentation/meta AND the tripwire spoiler (the machine/answer file)
# pilot-anchor-paths.json = {ref: real path} ONLY -- the file the designer opens to view an
#   image. Keeping the two apart is the no-priming fix (review MAJOR): the old single json
#   forced the designer through the tripwire expectations to resolve any anchor path.
JSON_NAME = "pilot-pairs.json"
PATHS_NAME = "pilot-anchor-paths.json"
MD_NAME = "pilot-pairs.md"


def _invalidate_stale(out_dir):
    """A prior successful run's json/paths files must not survive next to a WAITING md as a
    confident 'PILOT' that no longer corresponds to any sheet (review MINOR)."""
    for name in (JSON_NAME, PATHS_NAME):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            os.remove(p)


def write_waiting(out_dir, skipped, malformed, unmatched=(), labeled_unpairable=()):
    _invalidate_stale(out_dir)
    md = os.path.join(out_dir, MD_NAME)
    lines = [
        "# Sellability pilot -- WAITING ON DESIGNER LABELS",
        "",
        "ยังจับคู่ไม่ได้: worksheet ยังไม่มี anchor ที่ติดทั้ง delivered=Y และ room_type",
        f"(skipped: {skipped})",
        "",
        "## วิธีติด label ใน precut-worksheet.md (เลือกทางใดทางหนึ่ง)",
        "1. ตารางบนสุด: เติม 2 ช่องท้ายของแถวโปรเจกต์ เช่น  `| Y | bedroom |`",
        "   (ใช้เมื่อทั้งโปรเจกต์เป็นห้องเดียวกัน/ส่งมอบแล้วทั้งชุด; แถว UNCODED ใช้ไม่ได้ ต้องติดราย anchor)",
        "2. รายบรรทัด anchor: ต่อท้ายบรรทัดด้วย  `=> Y bedroom`  หรือ  `=> N`",
        "   (บรรทัด anchor ชนะตารางเสมอ)",
        "คำห้องที่เข้าใจ: " + "; ".join(f"{k}={sorted(v)[:4]}" for k, v in
                                        sorted(ROOM_ALIASES.items())),
        "",
        "แล้วรันใหม่:  python pipeline/scripts/precut_pair.py",
    ]
    # SURFACE hand labor that could not be used -- but by REF/LINE NO only, never raw label
    # text: a label line can hold a client name and this md is designer-facing (review MAJOR).
    if unmatched:
        lines += ["", "## anchor ที่ติด delivered แต่ห้องยังใช้ไม่ได้ (แก้คำห้อง)"]
        lines += [f"- {u['ref']}: {u['why']}" for u in unmatched]
    if labeled_unpairable:
        lines += ["", "## label ที่ติดบน ref ที่จับคู่ไม่ได้ (dup/photo-suspect/พิมพ์ผิด)"]
        lines += [f"- {r}" for r in labeled_unpairable if REF_RE.match(r)]
        n_bad = sum(1 for r in labeled_unpairable if not REF_RE.match(r))
        if n_bad:
            lines.append(f"- (+{n_bad} รายการที่ไม่ใช่รูปแบบ ref -- ดูใน stdout count เท่านั้น)")
    if malformed:
        lines += ["", "## บรรทัดที่อ่านไม่ออก (แก้แล้วรันใหม่) -- อ้างเลขบรรทัด ไม่โชว์เนื้อหา"]
        lines += [f"- worksheet บรรทัด {m['line_no']}: {m['why']}" for m in malformed]
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return md


def write_outputs(out_dir, pairs, tripwires, rows, meta):
    disp = display_map(pairs, tripwires)
    js = {"generated_by": "precut_pair.py",
          "curation_state": "PILOT -- designer-labeled anchors paired to our render lane; "
                            "verdicts DESIGNER-ONLY",
          **meta,
          "pairs": pairs, "tripwires": tripwires, "presentation": rows}
    with open(os.path.join(out_dir, JSON_NAME), "w", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False, indent=1)
    # the designer's path-lookup file: ref -> real path, and NOTHING else (no spoiler).
    paths = {p["anchor"]["ref"]: p["anchor"]["path"]
             for p in pairs + tripwires if not p.get("unavailable")}
    with open(os.path.join(out_dir, PATHS_NAME), "w", encoding="utf-8") as f:
        json.dump({"note": "ref -> full path, for opening anchor images; no verdict spoilers",
                   "paths": paths}, f, ensure_ascii=False, indent=1)

    L = [
        "# Sellability pilot -- designer judging sheet",
        "",
        "ดูทีละแถว: เปิดภาพ LEFT และ RIGHT เต็มจอ สลับไปมา แล้วตอบว่า *ถ้าลูกค้าจ่ายเงิน*",
        "ภาพไหนขายได้มากกว่า -- L / R / T (เสมอ) ลงในช่อง `ชนะ` (+เหตุผลสั้น ๆ ถ้ามี)",
        "แถวที่ชื่อขึ้นต้น R_PRJ = งานเรา; ที่เป็นรหัส I-xx = งานส่งมอบจริง -- ตัดสินจากภาพ ไม่ใช่ชื่อ",
        "ทำครบทุกแถวก่อนเปิดส่วนเฉลยล่างสุด",
        "",
        f"- คู่จริง {len(pairs)} คู่ (นำเสนอ 2 order ต่อคู่) + tripwire "
        f"{len([t for t in tripwires if not t.get('unavailable')])} คู่",
        "",
        "| # | LEFT | RIGHT | ชนะ(L/R/T) | note |",
        "|---|------|-------|------------|------|",
    ]
    for r in rows:
        L.append(f"| {r['row']} | {disp.get(r['left'], '?')} "
                 f"| {disp.get(r['right'], '?')} |  |  |")
    # OPEN section: our renders show a full path (no client name); anchors show their REF and
    # the file to resolve it -- pilot-anchor-paths.json, which holds NO tripwire spoiler.
    L += ["", f"## เปิดไฟล์ (anchor: หา path จาก {PATHS_NAME} ด้วย ref; md นี้ I-coded)", ""]
    seen = {}
    for r in rows:
        for path in (r["left"], r["right"]):
            seen.setdefault(disp.get(path, "?"), path)
    anchor_paths = {p["anchor"]["path"] for p in pairs + tripwires if not p.get("unavailable")}
    for token, path in sorted(seen.items()):
        if path in anchor_paths:
            L.append(f"- {token}  ->  {PATHS_NAME}")
        else:
            L.append(f"- {token}  ->  {path}")
    L += ["", "---", "", "## เฉลย tripwire -- อ่านหลังตัดสินครบทุกแถวแล้วเท่านั้น", ""]
    for t in tripwires:
        if t.get("unavailable"):
            L.append(f"- {t['pair_id']}: {t['unavailable']}")
        else:
            L.append(f"- {t['pair_id']} ({t['tripwire']['kind']}): {t['tripwire']['expectation']}")
    rows_of = {}
    for r in rows:
        rows_of.setdefault(r["pair_id"], []).append(r["row"])
    L += ["", "แถวของแต่ละคู่ (สำหรับเทียบ order-swap): "
          + "; ".join(f"{pid}={'+'.join(v)}" for pid, v in sorted(rows_of.items()))]
    with open(os.path.join(out_dir, MD_NAME), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def _read_text(path):
    """Read UTF-8 text. Any failure (missing / locked / OneDrive placeholder / wrong encoding)
    RAISES -- callers turn that into a refusal (fail-safe). Never returns '' on error, because
    '' reads downstream as 'no labels' and would license overwriting real hand labor."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Thai under piped cp1252
    ap = argparse.ArgumentParser(description=__doc__)
    bench = os.path.join(REPO, "_private", "benchmark")
    ap.add_argument("--precut", default=os.path.join(bench, "precut.json"))
    ap.add_argument("--worksheet", default=os.path.join(bench, "precut-worksheet.md"))
    ap.add_argument("--renders-dir",
                    default=os.path.join(REPO, "assets", "projects", "PRJ-2026-002", "renders"))
    ap.add_argument("--tripwire-rework",
                    default=os.path.join(REPO, "assets", "projects", "PRJ-2026-002",
                                         "experiments", "3leg-2026-07-14",
                                         "leg_c_materialized_cycles.png"))
    ap.add_argument("--tripwire-room", default="sitting",
                    help="the known-REWORK leg's room type (it is the sitting room)")
    ap.add_argument("--pairs", type=int, default=10)
    ap.add_argument("--out-dir", default=bench)
    args = ap.parse_args(argv)
    if args.pairs < 1:
        print(f"--pairs must be >= 1 (got {args.pairs})")
        return 1

    for path, what in ((args.precut, "precut.json (run benchmark_precut.py first)"),
                       (args.worksheet, "precut-worksheet.md")):
        if not os.path.exists(path):
            print(f"missing {what}")
            return 1

    existing = os.path.join(args.out_dir, MD_NAME)
    if os.path.exists(existing):
        try:
            existing_text = _read_text(existing)
        except OSError as e:
            print(f"REFUSED: cannot read the existing {MD_NAME} to check for verdicts ({e}). "
                  "Refusing to overwrite what might be judged work.")
            return 1
        if sheet_has_verdicts(existing_text):
            print(f"REFUSED: the existing {MD_NAME} already carries designer verdicts/notes. "
                  f"Move it AND {PATHS_NAME} aside together, then re-run -- this script never "
                  "overwrites judged work, and the two files must stay in sync.")
            return 1

    try:
        precut = json.loads(_read_text(args.precut))
        worksheet_text = _read_text(args.worksheet)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"REFUSED: cannot read inputs ({type(e).__name__}: {e}). Fix the file/encoding; "
              "nothing was written.")
        return 1
    pool, dropped = load_anchor_pool(precut)
    plabels, alabels, malformed = parse_worksheet_labels(worksheet_text)
    delivered, skipped, unmatched = label_anchors(pool, plabels, alabels)
    ours, unknown_renders = discover_our_lane(args.renders_dir)
    # a label the designer typed onto a ref that is NOT pairable (a dup, a photo-suspect, or a
    # typo'd ref) must be SURFACED, never silently unused -- hand labor is the scarce input here
    labeled_unpairable = sorted(r for r in alabels if r not in pool)

    if not delivered:
        md = write_waiting(args.out_dir, skipped, malformed, unmatched, labeled_unpairable)
        print(f"WAITING on designer labels -- 0 of {len(pool)} pairable anchors are labeled "
              f"delivered+room. How-to written: {os.path.basename(md)}")
        _print_surfacing(unmatched, labeled_unpairable, malformed)
        return 2

    pairs, tripwires, no_lane, by_room = build_pairs(
        delivered, ours, args.pairs, args.tripwire_rework, args.tripwire_room)
    if not pairs:
        md = write_waiting(args.out_dir, skipped, malformed, unmatched, labeled_unpairable)
        print(f"WAITING: {len(delivered)} anchors are labeled, but none lands in a room our "
              f"lane can render (labeled rooms without a lane: {no_lane}; our lanes: "
              f"{sorted(ours)}). A tripwire-only sheet measures nothing -- not written.")
        _print_surfacing(unmatched, labeled_unpairable, malformed)
        return 2
    rows = presentation_rows(pairs, tripwires)
    meta = {
        "anchor_pool_distinct": len(pool),
        "dropped_from_pairing": dropped,
        "skipped_labels": skipped,
        "unmatched_room_words": unmatched,
        "labeled_but_not_pairable": labeled_unpairable,
        "malformed_label_lines": malformed,
        "delivered_labeled": len(delivered),
        "delivered_by_room": {r: len(v) for r, v in sorted(by_room.items())},
        "rooms_without_render_lane": no_lane,
        "our_lane": {r: [o["name"] for o in v] for r, v in sorted(ours.items())},
        "unrecognized_render_files": unknown_renders,
        "parity_minimum": PARITY_MIN,
    }
    unavailable_trip = [t for t in tripwires if t.get("unavailable")]
    write_outputs(args.out_dir, pairs, tripwires, rows, meta)
    print(f"pilot: {len(pairs)} real pairs + "
          f"{len([t for t in tripwires if not t.get('unavailable')])} tripwire pairs "
          f"-> {len(rows)} judging rows")
    print(f"delivered-labeled anchors: {len(delivered)} "
          f"({', '.join(f'{r}:{n}' for r, n in sorted(meta['delivered_by_room'].items()))})")
    for t in unavailable_trip:
        print(f"TRIPWIRE UNAVAILABLE ({t['pair_id']}): {t['unavailable']}")
    if no_lane:
        print(f"labeled rooms with NO render lane on our side (honest gap): {no_lane}")
    for p in pairs:
        if p["below_parity_minimum"]:
            print(f"NOTE {p['pair_id']}: room '{p['room_type']}' has <{PARITY_MIN} delivered "
                  "anchors -- below the parity minimum, pilot-only evidence")
    _print_surfacing(unmatched, labeled_unpairable, malformed)
    return 0


def _print_surfacing(unmatched, labeled_unpairable, malformed):
    """stdout is I-CODED: surface hand labor that could not be used by REF/COUNT only, never
    the raw label text -- a designer label can carry a client name (review MAJOR, egress)."""
    if unmatched:
        print(f"labels with an unusable room word ({len(unmatched)}); refs need a fix: "
              f"{[u['ref'] for u in unmatched]}  (reasons in {JSON_NAME})")
    if labeled_unpairable:
        good = [r for r in labeled_unpairable if REF_RE.match(r)]
        bad = len(labeled_unpairable) - len(good)
        msg = f"labels on UNPAIRABLE refs (dup/photo-suspect -- label the representative): {good}"
        if bad:
            msg += f"  (+{bad} non-ref label target(s) withheld from stdout; see {JSON_NAME})"
        print(msg)
    if malformed:
        print(f"malformed worksheet lines: {len(malformed)} "
              f"(line numbers + reasons in {JSON_NAME}; content withheld)")


if __name__ == "__main__":
    sys.exit(main())
