# PLAN-confirmed-kind-identity-ledger
Rank: 4/5

## Goal (incl. the measured number this moves)

Make owner-signed **identity (kind)** corrections stick across scene-graph rebuilds, exactly the way
owner-signed facing (rot) already does — the production-lane half of the identity wound the
benchmark lane measures as F1 = 0.0.

Today the overlay checklist literally prints (raster_overlay.py:186-188):

> "หมายเหตุ identity: คอลัมน์ kind ยังเซ็นเข้า ledger ไม่ได้ (schema ยังไม่มี confirmed_kind — slice ถัดไป)"

i.e. kind is the ONE semantic the owner cannot sign. This plan adds `confirmed_kind` mirroring the
`confirmed_rot` machinery (one shared matcher, generator apply, gate backstop, orphan protection,
paste-ready stubs), and — per the critic's correction — replaces the matcher ordering semantic with
**last-usable-match-wins** on BOTH rot and kind in the same change, so an APPENDED correction beats
an earlier valid-but-wrong entry (the paste workflow appends; edit-in-place was the old doctrine).

Measured numbers this moves (all objectively checkable, see ACCEPTANCE CRITERIA):

| metric | before (verified this session) | after |
|---|---|---|
| `python3 pipeline/scripts/test_placement_gate.py` | `71/71 placement_gate tests passed` | `82/82` |
| `python3 pipeline/scripts/test_raster_overlay.py` | `16/16 raster_overlay tests passed` | `19/19` |
| `python3 test_gen_floor2_v4_specs.py` (v4 dir) | `14/14 gen_floor2_v4_specs tests passed` | `17/17` |
| `python3 -m pytest pipeline/scripts/ -q` | `N passed` (green total RECORDED in Step 0) | `N + 14 passed` (+11 gate, +3 overlay; v4 tests are not collected here) |
| signable kind rows in review-read-vs-sheet.md | 0 (footer says un-signable) | 12 paste-ready kind stubs (6 master + 6 sitting loose pieces) |
| gate marker per-room `kind_flags` field | absent | present, `0` on the live project |
| scene-graph byte-identity under the unchanged live ledger | — | `git diff` on both scene-graphs EMPTY after regen |

## Why now (leverage)

- Identity is the owner's most-corrected fault class, and the two-layer law (geometric = machine,
  semantic = owner-only, signatures make corrections STICK) currently has a hole: a rebuild can
  re-roll a kind the owner already corrected verbally, with no ledger to catch it.
- Every interface to mirror already exists and is tested: `confirmed_rot`
  (pipeline/scripts/placement_gate.py:345), `resolve_rot` (:377), `reconcile_confirmed` (:404),
  `assert_signatures_applied` (projects/PRJ-2026-002_c001-house/03_layout/v4/gen_floor2_v4_specs.py:216),
  overlay stubs (pipeline/scripts/raster_overlay.py:177-184). This is a copy-the-proven-pattern slice.
- The ordering-semantics fix (last-usable-wins) closes a real shadowing hole in the EXISTING rot
  lane: today an earlier VALID entry shadows a later valid correction (confirmed_rot scans
  first-usable-wins, placement_gate.py:360-374) — a pasted correction is silently ignored.
- The adjacent deferred items (overlay-freshness-in-marker, run()-side reconcile backstop,
  tv_console arrow parity) are explicitly OUT of scope (a later slice, "F", owns them).

## Files to touch

All paths repo-relative to `c:/Users/teza_/OneDrive/Desktop/PlingPeat`. No NEW files.

1. `pipeline/scripts/placement_gate.py` [EXISTS] — matcher semantics + new kind functions + run()/marker/report wiring.
2. `pipeline/scripts/test_placement_gate.py` [EXISTS] — 11 new tests (71 → 82).
3. `projects/PRJ-2026-002_c001-house/03_layout/v4/gen_floor2_v4_specs.py` [EXISTS] — apply signed kind in snap/angled/bed/orchid; applied/inert reporting.
4. `projects/PRJ-2026-002_c001-house/03_layout/v4/test_gen_floor2_v4_specs.py` [EXISTS] — 3 new tests (14 → 17).
5. `pipeline/scripts/raster_overlay.py` [EXISTS] — checklist kind provenance + kind stub section + footer.
6. `pipeline/scripts/test_raster_overlay.py` [EXISTS] — update 1 test, add 3 (16 → 19).

Regenerated (never hand-edited) artifacts in `projects/PRJ-2026-002_c001-house/03_layout/v4/`:
`scene-graph.master_bedroom.json` + `scene-graph.sitting_room.json` (MUST come out byte-identical),
`review-read-vs-sheet.md` / `review-read-vs-sheet_*.png` / `overlay-v4-selfverify.png` (expected to
change: new kind section), `placement-gate.json` (rewritten by re-running the gate ONLY).

READ-ONLY, never edit: `projects/PRJ-2026-002_c001-house/03_layout/v4/placement-review.json`
(the live ledger — 4 dismissed + 2 owner-signed rot entries at lines 48-69; the byte-identity proof
depends on it staying untouched).

## Implementation order

Run everything from repo root `c:/Users/teza_/OneDrive/Desktop/PlingPeat` unless a step says
otherwise. PowerShell 5.1: NO `&&` — chain with `;` or separate commands. Use `python3` (the
verified shim), not `python`.

### Step 0 — record the baseline (must be green before you edit anything)

```powershell
python3 pipeline/scripts/test_placement_gate.py     # tail: "71/71 placement_gate tests passed"
python3 pipeline/scripts/test_raster_overlay.py     # tail: "16/16 raster_overlay tests passed"
cd "projects\PRJ-2026-002_c001-house\03_layout\v4"; python3 test_gen_floor2_v4_specs.py   # "14/14 ..."
cd ..; python3 test_gen_floor2_specs.py             # "11/11 gen_floor2_specs tests passed" (v3 suite)
cd ..\..\..                                         # back to repo root (03_layout is THREE levels deep)
python3 -m pytest pipeline/scripts/ -q              # require 0 failed / 0 errors; RECORD the green total as N
```
The four per-file counts (71/16/14/11) were verified on 2026-07-07 and are stable — other plan
items in flight do not touch those files; if any of THEM differs, STOP and report. The pytest
TOTAL is deliberately NOT pinned: other plans land in the same tree before/around this one, so
the absolute number moves. STOP only on failures/errors; otherwise RECORD the green total as
**N** — every suite-total expectation below (metrics table, Step 9, acceptance criterion 5) is
expressed relative to this N.

### Step 1 — `pipeline/scripts/placement_gate.py`: switch BOTH rot matchers to last-usable-wins

**1a.** Replace the scan loop of `confirmed_facing` (currently lines 326-334: `for e in confirmed or []:`
... `return fac` ... `return None`) so the LAST matching usable entry wins:

```python
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        fac = e.get("facing")
        if fac not in _CARDINALS:      # a truthy-but-non-cardinal typo ('south','N ',180) must NOT
            continue                   # count — the generator's rot_from_facing would apply nothing
        if e.get("name") == name and _size_consistent(piece, e, size_tol):
            best = fac                 # LAST usable match wins (append-a-correction workflow)
    return best
```

**1b.** Replace the scan loop of `confirmed_rot` (currently lines 360-374) the same way, PRESERVING
the within-entry precedence (numeric `rot` beats `facing` letter — the `continue` after taking the
numeric rot is load-bearing):

```python
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        if e.get("name") != name or not _size_consistent(piece, e, size_tol):
            continue
        r = _norm_rot(e.get("rot")) if e.get("rot") is not None else None
        if r is not None:
            best = r                   # explicit numeric rot wins within the entry (incl. non-cardinal)
            continue
        card = _CARD_ROT.get(e.get("facing"))
        if card is not None:
            best = card
        # an entry that matched name+size but carries no usable value is SKIPPED — it can neither
        # apply nor ERASE an earlier valid sign (last-USABLE-wins, not last-entry-wins)
    return best
```

**1c.** Update confirmed_rot's docstring (:352-356): replace the sentence beginning
"A name+size match that yields NO usable rot ..." with the LAST-usable-wins wording below
(the :371-373 inline comment is already removed by Step 1b's replacement). Add the same
one-sentence ordering note to confirmed_facing's docstring (:315-322), which currently
documents no ordering. Wording:
"LAST usable matching entry wins: the owner's paste workflow APPENDS corrections, so an appended
correction beats every earlier entry — valid or typo — while a trailing malformed entry never
erases an earlier valid sign. Same ordering semantic as confirmed_kind (shared-matcher law)."

**Check:** `python3 pipeline/scripts/test_placement_gate.py` → still `71/71`
(test_confirmed_rot_typo_then_correction_not_shadowed at test:440-460 passes under both semantics —
the correction is last; NO existing test pins first-wins across two valid entries — verified by
reading every confirmed_* test, test_placement_gate.py:335-460).

### Step 2 — `pipeline/scripts/placement_gate.py`: add the kind lane

Insert immediately AFTER the end of `resolve_rot` (line 392, i.e. before `def load_confirmed(led):`
at :395):

```python
def _norm_kind(k):
    """k -> stripped kind string, or None if unusable. kind is owner-signed IDENTITY: only a
    non-empty string counts; None/''/numbers are typos a later appended entry corrects. Exact
    (case-sensitive) — KIND_SYNONYMS normalization is the benchmark lane's business, not the
    ledger's."""
    if isinstance(k, str):
        k = k.strip()
        if k:
            return k
    return None


def confirmed_kind(piece, confirmed, size_tol=0.20):
    """The owner-signed KIND (identity) for a piece, or None. Matched by the SAME name+size join
    as confirmed_rot (exact name + orientation-agnostic ±20% size guard; a sizeless entry always
    matches), LAST usable matching entry wins (append-a-correction workflow). This is the matcher
    BOTH the gate (kind_flags, to suppress/raise) and the generators (resolve_kind, to APPLY) use
    — they can never disagree on what the owner signed."""
    name = piece.get("name")
    if name is None:
        return None
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        if e.get("name") != name or not _size_consistent(piece, e, size_tol):
            continue
        k = _norm_kind(e.get("kind"))
        if k is not None:
            best = k
    return best


def resolve_kind(name, hand_kind, w, d, confirmed):
    """GENERATOR helper mirroring resolve_rot: an owner-signed kind OVERRIDES the hand-read kind.
    Returns (kind, source): source='owner-signed' when a signature was found and applied (even if
    it equals hand_kind — provenance), else None with hand_kind unchanged and NOTHING emitted, so
    a regen against a ledger with no kind signs stays byte-identical.

    IDENTITY ONLY: callers MUST resolve kind AFTER cluster matching — a signature re-labels a
    piece, it never re-routes which drawn blob the piece snaps to (geometry stays machine-layer)."""
    if not confirmed:
        return hand_kind, None
    signed = confirmed_kind({"name": name, "w": w, "d": d}, confirmed)
    if signed is None:
        return hand_kind, None
    return signed, "owner-signed"


def entry_is_inert(e):
    """True when a confirmed[] entry carries NO usable payload (no numeric/cardinal rot AND no
    usable kind): it can bind a piece by name+size yet apply nothing. Reported honestly by the
    generator instead of hiding behind a reassuring 'N loaded' count."""
    if not isinstance(e, dict):
        return True
    return (_norm_rot(e.get("rot")) is None
            and _CARD_ROT.get(e.get("facing")) is None
            and _norm_kind(e.get("kind")) is None)
```

Insert immediately AFTER the end of `facing_flags` (its `return out`, line 490, before `def gate(`):

```python
def kind_flags(loose, confirmed=None):
    """Owner-signed IDENTITY backstop — the kind analog of facing_flags branch (1). For every
    loose piece with a signed kind: SUPPRESS when the built kind equals the sign (adjudicated),
    else raise 'contradicts_signed_kind' — the regression backstop. There is NO unsigned branch:
    no geometric identity read exists (identity is owner-only semantic truth; the gate's
    identity_check stays a double-claim detector only). A piece whose built kind is missing or
    malformed can never be shown to match -> flagged, so silence cannot silence a signature."""
    out = []
    for it in loose or []:
        signed = confirmed_kind(it, confirmed)
        if signed is None:
            continue
        built = _norm_kind(it.get("kind"))
        if built is not None and built == signed:
            continue
        out.append({"name": it.get("name"), "kind": built, "verdict": "contradicts_signed_kind",
                    "claimed": built, "read": signed, "confidence": 1.0})
    return out
```

### Step 3 — `pipeline/scripts/placement_gate.py`: wire run(), marker, report

**3a.** In `run()`, replace the two lines at :675-677

```python
        r["facing"] = facing_flags(loose, res["fsegs"], offset, confirmed=confirmed_room)
        if r["facing"] and order[r["verdict"]] < order["REVIEW"]:
            r["verdict"] = "REVIEW"        # a symbol-vs-typed facing disagreement needs a human
```
with:
```python
        r["facing"] = facing_flags(loose, res["fsegs"], offset, confirmed=confirmed_room)
        r["kind"] = kind_flags(loose, confirmed=confirmed_room)
        if (r["facing"] or r["kind"]) and order[r["verdict"]] < order["REVIEW"]:
            r["verdict"] = "REVIEW"        # a signed-semantic (facing/kind) disagreement needs a human
```

**3b.** In `run()`'s ledger print (:658-659) change `"signed facing(s) on file"` to
`"signed entr(y/ies) on file (facing/kind)"`.

**3c.** In `_write_marker` rooms rows (:714-722), after `"facing_flags": len(r.get("facing", [])),`
add:
```python
                   "kind_flags": len(r.get("kind", [])),
```

**3d.** In `_report`, after the facing print loop (ends :785) add:
```python
        for f in r.get("kind", []):
            print(f"    [KIND!]  '{f['name']}' built kind '{f['claimed']}' CONTRADICTS the owner-signed "
                  f"kind '{f['read']}' — a rebuild regressed a signed identity; regenerate to re-apply it")
```
and in the todo builder, after the facing todo block (ends ~:819) add:
```python
        for f in r.get("kind", []):
            todo.append(f"FIX  [{r['room']}] '{f['name']}' built kind '{f['claimed']}' CONTRADICTS the "
                        f"owner-signed kind '{f['read']}' — regenerate so the signed identity is re-applied")
```

**Check:** `python3 pipeline/scripts/test_placement_gate.py` → still `71/71` (nothing new pinned yet).

### Step 4 — `pipeline/scripts/test_placement_gate.py`: add 11 tests

Append BEFORE the `if __name__ == "__main__":` block (line 592). The file's module alias is `G`
(`import placement_gate as G` — same convention as every existing test).

```python
# ---- confirmed_kind: the identity ledger (mirrors confirmed_rot; shared-matcher law) ----
def test_confirmed_kind_matches_by_name():
    assert G.confirmed_kind({"name": "หีบ", "w": 800, "d": 800},
                            [{"name": "หีบ", "kind": "bench"}]) == "bench"
    assert G.confirmed_kind({"name": "other", "w": 800, "d": 800},
                            [{"name": "หีบ", "kind": "bench"}]) is None


def test_confirmed_kind_size_guard_rejects_reused_name():
    # a stale sign sized for a stool must NOT re-identify a big cabinet that reused the name
    assert G.confirmed_kind({"name": "c", "w": 2000, "d": 600},
                            [{"name": "c", "kind": "stool", "w": 300, "d": 300}]) is None
    # a sizeless entry still matches (cheap paste — stub pre-fills w/d but hand entries may not)
    assert G.confirmed_kind({"name": "c", "w": 2000, "d": 600},
                            [{"name": "c", "kind": "cabinet"}]) == "cabinet"


def test_confirmed_kind_last_valid_entry_wins():
    # APPEND-a-correction workflow: the owner pastes a corrected stub without deleting the old
    # one; the LATER valid entry must win (the shadowing hole this slice closes).
    conf = [{"name": "x", "kind": "cabinet", "w": 800, "d": 800},
            {"name": "x", "kind": "tv_console", "w": 800, "d": 800}]
    assert G.confirmed_kind({"name": "x", "w": 800, "d": 800}, conf) == "tv_console"


def test_confirmed_kind_malformed_entries_skipped_not_shadowing():
    piece = {"name": "x", "w": 800, "d": 800}
    # malformed FIRST: the correction is still honoured
    assert G.confirmed_kind(piece, [{"name": "x", "kind": ""},
                                    {"name": "x", "kind": "sofa"}]) == "sofa"
    # malformed LAST: must NOT erase the earlier valid sign (last-USABLE-wins, not last-entry)
    assert G.confirmed_kind(piece, [{"name": "x", "kind": "sofa"},
                                    {"name": "x", "kind": None}]) == "sofa"
    assert G.confirmed_kind(piece, [{"name": "x", "kind": 42}]) is None


def test_confirmed_rot_last_valid_entry_wins():
    # the SAME ordering semantic pinned on the rot matchers in the SAME change: gate, generator
    # and the legacy cardinal accessor must all agree on 'what did the owner sign LAST'.
    piece = {"name": "bed", "w": 2000, "d": 1800}
    assert G.confirmed_rot(piece, [{"name": "bed", "rot": 90, "w": 2000, "d": 1800},
                                   {"name": "bed", "rot": 270, "w": 2000, "d": 1800}]) == 270
    assert G.confirmed_facing(piece, [{"name": "bed", "facing": "E"},
                                      {"name": "bed", "facing": "W"}]) == "W"
    # a trailing MALFORMED entry does not erase the earlier valid sign
    assert G.confirmed_rot(piece, [{"name": "bed", "rot": 90, "w": 2000, "d": 1800},
                                   {"name": "bed", "rot": "junk", "w": 2000, "d": 1800}]) == 90


def test_rot_and_kind_payloads_are_independent():
    piece = {"name": "x", "w": 800, "d": 800}
    both = [{"name": "x", "rot": 90, "kind": "sofa"}]
    assert G.confirmed_rot(piece, both) == 90
    assert G.confirmed_kind(piece, both) == "sofa"
    # a kind-only sign is NOT a rot sign, and vice versa
    assert G.confirmed_rot(piece, [{"name": "x", "kind": "sofa"}]) is None
    assert G.confirmed_kind(piece, [{"name": "x", "rot": 90}]) is None


def test_resolve_kind_no_ledger_and_override():
    assert G.resolve_kind("x", "cabinet", 800, 800, []) == ("cabinet", None)
    assert G.resolve_kind("x", "cabinet", 800, 800, None) == ("cabinet", None)
    assert G.resolve_kind("x", "cabinet", 800, 800,
                          [{"name": "x", "kind": "tv_console"}]) == ("tv_console", "owner-signed")


def test_resolve_kind_agreeing_sign_still_tagged():
    # provenance even when the sign equals the hand read (mirrors resolve_rot :383-386)
    assert G.resolve_kind("x", "sofa", 800, 800,
                          [{"name": "x", "kind": "sofa"}]) == ("sofa", "owner-signed")


def test_kind_flags_suppress_and_contradict():
    it = {"name": "x", "kind": "tv_console", "x": 0, "y": 0, "w": 800, "d": 800}
    assert G.kind_flags([it], [{"name": "x", "kind": "tv_console"}]) == []   # adjudicated
    f = G.kind_flags([it], [{"name": "x", "kind": "wardrobe"}])
    assert len(f) == 1 and f[0]["verdict"] == "contradicts_signed_kind", f
    assert f[0]["claimed"] == "tv_console" and f[0]["read"] == "wardrobe", f
    assert G.kind_flags([it], []) == [] and G.kind_flags([it], None) == []


def test_kind_flags_missing_built_kind_never_suppresses():
    # a piece that LOST its kind (hand edit) can never be shown to match -> flagged, not silenced
    it = {"name": "x", "x": 0, "y": 0, "w": 800, "d": 800}
    f = G.kind_flags([it], [{"name": "x", "kind": "sofa"}])
    assert len(f) == 1 and f[0]["verdict"] == "contradicts_signed_kind", f


def test_entry_is_inert_classification():
    assert G.entry_is_inert({"name": "x", "w": 1, "d": 1})                       # no payload
    assert G.entry_is_inert({"name": "x", "rot": "junk", "facing": "bogus", "kind": ""})
    assert not G.entry_is_inert({"name": "x", "rot": 8})
    assert not G.entry_is_inert({"name": "x", "facing": "W"})
    assert not G.entry_is_inert({"name": "x", "kind": "bench"})
    assert G.entry_is_inert("not-a-dict") and G.entry_is_inert(None)
```

**Check:** `python3 pipeline/scripts/test_placement_gate.py` → `82/82 placement_gate tests passed`.

### Step 5 — `projects/PRJ-2026-002_c001-house/03_layout/v4/gen_floor2_v4_specs.py`: apply signed kind

**5a.** Import (line 61) — replace
`from placement_gate import resolve_rot, load_confirmed, reconcile_confirmed` with:
```python
from placement_gate import (resolve_rot, resolve_kind, load_confirmed,
                            reconcile_confirmed, entry_is_inert)
```

**5b.** `snap()` no-cluster branch (:139-145): after the `resolve_rot(...)` line add
`kind_eff, ksrc = resolve_kind(name, kind, 500, 500, confirmed)` (SAME 500,500 fallback join size
as rot); pass `kind_eff` (not `kind`) to `to_spec`; after the `if fsrc:` block add
```python
        if ksrc:
            it["kind_source"] = ksrc
```
and change the `_REPORT.append` third field from `kind` to `kind_eff`.

**5c.** `snap()` matched branch (:147-154): after `rot, fsrc = resolve_rot(name, FACE_ROT[face],
cl["w"], cl["d"], confirmed)` add `kind_eff, ksrc = resolve_kind(name, kind, cl["w"], cl["d"],
confirmed)`; pass `kind_eff` to `to_spec`; add the same `if ksrc:` block; `_REPORT` third field →
`kind_eff`. Append to snap's docstring: "kind is resolved AFTER the match too — an identity sign
re-labels the piece, it never re-routes which cluster it snaps to."

**5d.** `angled()` (:157-173): after `eff_rot, fsrc = resolve_rot(name, rot, w, d, confirmed)` add
`kind_eff, ksrc = resolve_kind(name, kind, w, d, confirmed)`; pass `kind_eff` to `to_spec`; add the
`if ksrc:` block; `_REPORT` third field → `kind_eff`.

**5e.** Bed direct path (:280-285) — mirror the rot lines exactly:
```python
    _bed_rot, _bed_src = resolve_rot("เตียง 7'x6.5' หัวตะวันออก", 270, 1981, 2134, confirmed_master)
    _bed_kind, _bed_ksrc = resolve_kind("เตียง 7'x6.5' หัวตะวันออก", "bed", 1981, 2134, confirmed_master)
    _bed = to_spec("เตียง 7'x6.5' หัวตะวันออก", _bed_kind, 4159, 1100, 1981, 2134, _bed_rot, 600,
                   note="head EAST vs BF14 slat; measured (merges with casework)")
    if _bed_src:
        _bed["facing_source"] = _bed_src
    if _bed_ksrc:
        _bed["kind_source"] = _bed_ksrc
```

**5f.** Orchid direct path (:376-382) — same pattern:
```python
    _orchid_rot, _orchid_src = resolve_rot(_orchid_name, FACE_ROT["S"], 1002, 402, confirmed_sitting)
    _orchid_kind, _orchid_ksrc = resolve_kind(_orchid_name, "console", 1002, 402, confirmed_sitting)
    _orchid = to_spec(_orchid_name, _orchid_kind, 6399, 2373, 1002, 402, _orchid_rot, 450,
                      note="orchid console table (drawn ~1002x402) — SEPARATE piece from BF12-2 (owner 2026-07-06)")
    if _orchid_src:
        _orchid["facing_source"] = _orchid_src
    if _orchid_ksrc:
        _orchid["kind_source"] = _orchid_ksrc
```

**5g.** Applied/inert report (:411-414) — replace with:
```python
    applied_f = sum(1 for it in master_items + sit_items if it.get("facing_source") == "owner-signed")
    applied_k = sum(1 for it in master_items + sit_items if it.get("kind_source") == "owner-signed")
    inert = sum(1 for e in confirmed_all if entry_is_inert(e))
    print(f"placement-review.json: {len(confirmed_all)} loaded, {applied_f} facing APPLIED, "
          f"{applied_k} kind APPLIED, 0 orphaned"
          + (f"; NOTE {inert} carry NO usable rot/facing/kind — fix the entry value(s)" if inert else ""))
```
(The old `inert = len(confirmed_all) - applied` arithmetic is WRONG once entries can carry kind:
a kind-only sign is applied, not inert.)

**5h.** Wording only: in `assert_signatures_applied`'s SystemExit message (:230-235) change
"owner-signed facing(s) bind to NO loose piece" → "owner-signed entr(y/ies) bind to NO loose piece"
and "The facing would re-roll" → "The signed value (facing and/or kind) would re-roll". Do NOT
change the `PLACEMENT-REVIEW ORPHAN` prefix (pinned by test:135 `"ORPHAN" in str(ex)`).
Also update the loader print at :264-265: "owner-signed facing(s) loaded" → "owner-signed entr(y/ies) loaded".
NO change to `reconcile_confirmed` or the four `assert_signatures_applied` call sites (:397-407) —
the name+size join already covers kind-only entries because it never inspects the payload
(placement_gate.py:416-423, verified).

**Check:** `cd "projects\PRJ-2026-002_c001-house\03_layout\v4"; python3 test_gen_floor2_v4_specs.py`
→ still `14/14` (existing tests don't touch kind).

### Step 6 — `projects/PRJ-2026-002_c001-house/03_layout/v4/test_gen_floor2_v4_specs.py`: add 3 tests

Append before the `if __name__ == "__main__":` block (line 163). Module alias is `G4`.

```python
# ---- confirmed_kind wiring: identity signs stick, geometry never moves -----------------
def test_v4_snap_kind_sign_changes_identity_not_geometry():
    G4._REPORT.clear()
    a = G4.snap("sitting_room", "หีบปลายเตียง", "cabinet", _cardcluster(curve=False), set(),
                (1400, 1400), "E", 800)
    G4._REPORT.clear()
    b = G4.snap("sitting_room", "หีบปลายเตียง", "cabinet", _cardcluster(curve=False), set(),
                (1400, 1400), "E", 800,
                confirmed=[{"name": "หีบปลายเตียง", "kind": "bench"}])
    assert b["kind"] == "bench" and b["kind_source"] == "owner-signed", b
    ga = {k: v for k, v in a.items() if k not in ("kind", "kind_source")}
    gb = {k: v for k, v in b.items() if k not in ("kind", "kind_source")}
    assert ga == gb, (ga, gb)     # the sign changed IDENTITY only — nothing geometric moved


def test_v4_kind_sign_never_changes_cluster_match():
    # rect cluster #1 sits ON the anchor; curved #2 is farther. Hand kind 'cabinet' (rect want)
    # matches #1 (score 0 vs 283+350). If the signed kind 'armchair' (curve want) were applied
    # BEFORE match(), the +350 mismatch penalty would flip the snap to #2 — a signature MOVING a
    # piece, geometry the owner never signed. Pin after-match application.
    cls = [{"id": 1, "x": 1000, "y": 1000, "w": 800, "d": 800, "curve": False, "area_m2": 0.64},
           {"id": 2, "x": 1200, "y": 1200, "w": 800, "d": 800, "curve": True, "area_m2": 0.64}]
    G4._REPORT.clear()
    it = G4.snap("sitting_room", "x", "cabinet", cls, set(), (1400, 1400), "E", 800,
                 confirmed=[{"name": "x", "kind": "armchair"}])
    assert it["cluster"] == 1, it
    assert it["kind"] == "armchair" and it["kind_source"] == "owner-signed", it


def test_v4_orphan_gate_covers_kind_only_sign():
    # kind-only signs ride the SAME name+size join — orphan protection covers them from day one
    G4._REPORT.clear()
    piece = G4.angled("sitting_room", "เก้าอี้ tub ซ้าย", "armchair", 6331, 949, 680, 640, 12, 750)
    bound = [{"name": "เก้าอี้ tub ซ้าย", "kind": "armchair", "w": 680, "d": 640}]
    assert len(G4.assert_signatures_applied([piece], bound)) == 1
    detached = [{"name": "ชื่อที่ไม่มีจริง", "kind": "armchair"}]
    try:
        G4.assert_signatures_applied([piece], detached, where="sitting_room")
        assert False, "a detached kind sign must orphan (hard-FAIL), not be silently skipped"
    except SystemExit as ex:
        assert "ORPHAN" in str(ex), ex
```

**Check:** `python3 test_gen_floor2_v4_specs.py` (from the v4 dir) → `17/17 gen_floor2_v4_specs tests passed`.

### Step 7 — `pipeline/scripts/raster_overlay.py`: checklist kind provenance + kind stubs

All inside `checklist()` (:139-189). Keep the table header text EXACTLY as-is
(`| badge | ชิ้น | kind (identity = human call) | rot | facing |`).

**7a.** Line 152: change `stubs = []` to
```python
    stubs = []
    kind_stubs = []
```

**7b.** Replace the per-piece row emission (:159-169) with:
```python
        for i, (group, it) in enumerate(pieces(r["spec"]), 1):
            rot = it.get("rot", 0)
            if it.get("facing_source") == "owner-signed":
                fac = "✓ owner-signed"
            elif wants_arrow(it):
                fac = "● hand-read — ตรวจ/เซ็น"
                stubs.append((f"{L}{i}", r["id"], it))
            else:
                fac = "–"
            kind_cell = f"{it.get('kind', '?')} ({group})"
            if it.get("kind_source") == "owner-signed":
                kind_cell += " ✓ owner-signed"
            elif group == "loose":
                # only LOOSE pieces consult the ledger (builtins/fixtures never do — a sign aimed
                # at one ORPHANS the generate), so only loose rows get a paste-ready kind stub.
                kind_stubs.append((f"{L}{i}", r["id"], it))
            lines.append(f"| {L}{i} | {it.get('name', '?')} | {kind_cell} "
                         f"| {_rot_gloss(rot)} | {fac} |")
```

**7c.** AFTER the existing `if stubs:` facing-stub section (ends line 185) and BEFORE the footer
line, insert (facing section MUST stay first — a test reads the first `{` line as a facing stub):
```python
    if kind_stubs:
        lines.append("## เซ็น kind (identity, แถว loose) — ถูกแล้ว = วาง stub ตามเดิม / ผิด = แก้ค่า `kind` ก่อนวาง")
        lines.append("")
        lines.append("วางลง `confirmed[]` ใน `placement-review.json` แล้ว regenerate — identity จะติดถาวร "
                     "(rebuild เปลี่ยนเองไม่ได้, gate ยก contradicts_signed_kind ถ้าเบี่ยง). วางเฉพาะแถวที่ "
                     "ตรวจด้วยตาแล้วจริง; แก้ทีหลัง = APPEND entry ใหม่ชื่อ+ขนาดเดิม (ตัวหลังชนะ):")
        lines.append("")
        for badge, room_id, it in kind_stubs:
            stub = {"room": room_id, "name": it.get("name"), "kind": it.get("kind"),
                    "w": it.get("w"), "d": it.get("d"),
                    "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
            lines.append(f"**{badge}** — {it.get('name', '?')}:")
            lines.append("```json")
            lines.append(json.dumps(stub, ensure_ascii=False))
            lines.append("```")
            lines.append("")
```
NOTE the stub has NO `"rot"` key — see EDGE CASES #4.

**7d.** Replace the footer (:186-188, the "ยังเซ็นเข้า ledger ไม่ได้" note) with:
```python
    lines.append("หมายเหตุ identity: คอลัมน์ kind เซ็นเข้า ledger ได้แล้ว (confirmed_kind) — วาง stub "
                 "จากส่วน 'เซ็น kind' ข้างบน; แก้ทีหลัง = APPEND entry ใหม่ (ชื่อ+ขนาดเดิม, ตัวหลังชนะ). "
                 "ชิ้น builtin/fixture ไม่มี stub (generator ไม่ apply sign) — แก้ identity ของพวกนั้น = "
                 "บอกเลข badge + ชนิดที่ถูก แล้วเราแก้ generator ให้")
```

### Step 8 — `pipeline/scripts/test_raster_overlay.py`: update 1 test, add 3

**8a.** REWRITE `test_checklist_signed_rows_get_no_stub` (:127-131) — the old assertion
`not any(l.startswith("{"))` now requires kind to be signed too:
```python
def test_checklist_signed_rows_get_no_stub():
    # facing AND kind both owner-signed -> nothing left to sign, no stub of either flavour
    rooms = [{"id": "r", "spec": _spec(
        items=[{"name": "เก้าอี้", "kind": "armchair", "rot": 8,
                "facing_source": "owner-signed", "kind_source": "owner-signed"}])}]
    text = RO.checklist(rooms)
    assert not any(l.startswith("{") for l in text)          # nothing to sign — no stub sections
```

**8b.** Append 3 new tests before the `__main__` block (:147):
```python
def test_checklist_kind_signed_marked_and_no_kind_stub():
    rooms = [{"id": "r", "spec": _spec(
        items=[{"name": "ตู้", "kind": "tv_console", "rot": 0,
                "facing_source": "owner-signed", "kind_source": "owner-signed"}])}]
    text = "\n".join(RO.checklist(rooms))
    assert "tv_console (loose) ✓ owner-signed" in text        # kind cell carries provenance
    assert "```json" not in text                              # signed both ways -> no stubs


def test_checklist_kind_stub_is_pasteable_and_rot_free():
    import json
    rooms = [{"id": "sitting_room", "spec": _spec(
        items=[{"name": "โซฟา 3 ที่นั่ง", "kind": "sofa", "rot": 90, "w": 1002, "d": 2202}])}]
    text = RO.checklist(rooms)
    stubs = [json.loads(l) for l in text if l.startswith("{")]
    assert len(stubs) == 2                                    # one facing stub + one kind stub
    fac, kin = stubs                                          # facing section is emitted FIRST
    assert "rot" in fac and "kind" not in fac                 # a facing stub signs facing ONLY
    assert kin["kind"] == "sofa" and "rot" not in kin         # a kind stub signs identity ONLY
    assert kin["room"] == "sitting_room" and kin["name"] == "โซฟา 3 ที่นั่ง"
    assert kin["w"] == 1002 and kin["d"] == 2202              # join keys pre-filled


def test_checklist_kind_stub_only_for_loose_group():
    rooms = [{"id": "r", "spec": _spec(
        builtins=[{"name": "ตู้ BF", "kind": "cabinet"}],
        subrooms=[{"name": "s", "outline_mm": [[0, 0], [1, 0], [1, 1], [0, 1]],
                   "fixtures": [{"name": "wc", "kind": "toilet"}]}])}]
    text = RO.checklist(rooms)
    # builtins/fixtures never consult the ledger — a stub for them would bait the owner into a
    # paste that hard-FAILs the generate as a PLACEMENT-REVIEW ORPHAN. No stub, no bait.
    assert not any(l.startswith("{") for l in text)
```

**Check:** `python3 pipeline/scripts/test_raster_overlay.py` → `19/19 raster_overlay tests passed`.

### Step 9 — full suite + shared-code regression sweep

```powershell
python3 -m pytest pipeline/scripts/ -q      # expect "N + 14 passed" (Step 0's N + 11 gate + 3 overlay), 0 failed
cd "projects\PRJ-2026-002_c001-house\03_layout"; python3 test_gen_floor2_specs.py   # "11/11 ..." (v3 also uses resolve_rot/confirmed_rot — verified it does NOT pin first-wins ordering, but prove it)
cd ..\..\..
```

### Step 10 — live-project proof: byte-identity + regenerated checklist + gate parity

The live ledger has 2 rot-only signs and ZERO kind signs, so the regenerated scene-graphs must be
**byte-identical** (resolve_kind finds no usable kind → hand kind unchanged, no `kind_source`
emitted; the 2 rot signs re-apply exactly as before — current scene-graph.sitting_room.json already
carries `"rot": 8` / `"rot": 332` + `facing_source`, verified at lines 86-102).

**10a.** Regenerate (from repo root; needs fitz/matplotlib/scipy — all present; ~20-60 s; the PDF
path contains Thai — keep the double quotes):
```powershell
python3 "projects\PRJ-2026-002_c001-house\03_layout\v4\gen_floor2_v4_specs.py" "projects\PRJ-2026-002_c001-house\00_intake\raw-local\The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf" "projects\PRJ-2026-002_c001-house\03_layout\v4\overlay-v4-selfverify.png" "projects\PRJ-2026-002_c001-house\03_layout\v4"
```
Expected stdout includes: `placement-review.json: 2 loaded, 2 facing APPLIED, 0 kind APPLIED, 0 orphaned`.

**10b.** Byte-identity:
```powershell
git diff --stat -- "projects/PRJ-2026-002_c001-house/03_layout/v4/scene-graph.master_bedroom.json" "projects/PRJ-2026-002_c001-house/03_layout/v4/scene-graph.sitting_room.json"
```
Expected: EMPTY output (no diff). This is what keeps the hash-pinned `placement-gate.json` marker
valid — its `inputs` sha1s (scene-graphs + manifest + walls + ledger) are all unchanged.

**10c.** Inspect the regenerated `review-read-vs-sheet.md`: it must contain the section
`## เซ็น kind (identity, แถว loose)` with **12** ```json kind stubs (6 master loose pieces: bed,
bench, 2 side tables, desk armchair, tv_console; 6 sitting: sofa, 2 tub armchairs, 2 round tables,
orchid console), each carrying `"kind"` and NO `"rot"`, plus the 3 pre-existing facing stubs
(bed / desk chair / sofa) — 15 json blocks total. The old "ยังเซ็นเข้า ledger ไม่ได้" footer must be gone.

**10d.** Re-run the gate (~15-45 s) and confirm parity:
```powershell
python3 pipeline\scripts\placement_gate.py "projects\PRJ-2026-002_c001-house\00_intake\raw-local\The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf" "projects\PRJ-2026-002_c001-house\03_layout\v4\floor2_v4-manifest.json"
```
Expected: exit code 0; verdict REVIEW (unchanged from the current marker — verified current
placement-gate.json says `"verdict": "REVIEW"`, both rooms REVIEW, facing_flags 0); the rewritten
marker's rooms rows now each contain `"kind_flags": 0`; `"calibration": "PASS"`.

**10e.** Matcher-parity smoke (no ledger writes, pure in-memory):
```powershell
python3 -c "import sys; sys.path.insert(0,'pipeline/scripts'); import placement_gate as G; p={'name':'x','kind':'cabinet','w':800,'d':800,'x':0,'y':0}; c=[{'name':'x','kind':'tv_console'}]; print(G.confirmed_kind(p,c), G.resolve_kind('x','cabinet',800,800,c), G.kind_flags([p],c)[0]['verdict'])"
```
Expected: `tv_console ('tv_console', 'owner-signed') contradicts_signed_kind`.

### Step 11 — wrap

Report results. If committing is requested, follow the repo ritual: scrutinize first, separate
logical commits per bundle (e.g. matcher+gate / generator / overlay / regenerated artifacts),
NEVER `git add -A`, never push. The regenerated md/PNG/marker artifacts belong with the change;
the three PNGs already untracked in git status (glazing-candidates.png, review-lounge-not-terrace.png,
review-terrace-aim.png) are NOT yours — leave them alone.

## Edge cases a weaker model would miss

Every item personally verified in code this session.

1. **"Mirror confirmed_rot exactly" and "last-entry-wins" CONFLICT — resolve it deliberately.**
   Current `confirmed_rot` is FIRST-usable-match-wins (placement_gate.py:360-374): malformed
   matches are skipped (so appended corrections beat earlier TYPOS) but an earlier VALID entry
   shadows a later valid correction. This plan switches ALL THREE accessors (`confirmed_facing`
   :314, `confirmed_rot` :345, new `confirmed_kind`) to LAST-USABLE-wins in the same change —
   changing only one diverges gate from generator from legacy accessor. The existing pin
   `test_confirmed_rot_typo_then_correction_not_shadowed` (test_placement_gate.py:440-460) passes
   under BOTH semantics (its correction is last) — keep it untouched; the NEW ordering pin is
   `test_confirmed_rot_last_valid_entry_wins`.
2. **Last-USABLE-wins, not last-ENTRY-wins.** A trailing malformed entry (`{"kind": ""}`,
   `{"rot": "junk"}`) must NOT erase an earlier valid sign — the loop only overwrites `best` when
   the entry yields a usable value. Pinned by
   `test_confirmed_kind_malformed_entries_skipped_not_shadowing` and the third assert of
   `test_confirmed_rot_last_valid_entry_wins`.
3. **Within-entry precedence must survive the rewrite:** numeric `rot` beats the `facing` letter
   inside one entry (placement_gate.py:365-370). In the new loop the `continue` after taking the
   numeric rot is load-bearing — without it the SAME entry's facing letter would overwrite the rot.
4. **A kind stub must NOT carry `"rot"`, and a facing stub must NOT carry `"kind"`.**
   `confirmed_rot` reads ANY `rot` key on a matched entry (placement_gate.py:365) — a rot-bearing
   kind stub silently signs FACING the owner never attested. The existing facing stub
   (raster_overlay.py:178-180) carries `rot/w/d` and no `kind`; keep it that way. Pinned by
   `test_checklist_kind_stub_is_pasteable_and_rot_free`.
5. **`pieces()` group tag is `"loose"`, not `"items"`** (raster_overlay.py:70:
   `out += [("loose", it) for it in spec.get("items", [])]`). Filter kind stubs on
   `group == "loose"`. The checklist row format `f"{kind} ({group})"` is pinned by
   `test_checklist_rows_match_piece_numbering` asserting `"cabinet (builtin)"` (test:96) — append
   the ✓ marker AFTER that string, never restructure the cell.
6. **`test_checklist_signed_rows_get_no_stub` (test_raster_overlay.py:127-131) WILL break** the
   moment kind stubs exist, because its fixture signs facing only — its armchair now earns a kind
   stub. Update the fixture to sign `kind_source` too (Step 8a) in the SAME change, or Step 8's
   suite run fails on a stale pin, not a real bug.
7. **Facing stub section must be emitted BEFORE the kind section:**
   `test_checklist_sign_stub_is_valid_pasteable_json` (test_raster_overlay.py:115-124) parses the
   FIRST line starting with `{` and asserts it has `rot`. Swapping section order silently breaks it.
8. **Resolve kind AFTER `match()`, never before.** `kind` feeds `_wants_curve`
   (gen_floor2_v4_specs.py:98-103) and the 350 mm `mismatch_penalty` inside `match()` (:110-129);
   `snap()` calls `match()` with the HAND kind at :138 and resolves rot only afterwards (":137
   Facing is resolved AFTER the match"). Applying a signed kind before match would let a signature
   MOVE a piece to a different cluster — geometry the owner never signed. Pinned by
   `test_v4_kind_sign_never_changes_cluster_match` (rect cluster at dist 0 vs curved at 283:
   before-match application flips the winner via +350).
9. **The no-cluster fallback joins on (500, 500)** (gen_floor2_v4_specs.py:140-141) — resolve_kind
   must use the SAME pair there, or a size-carrying sign matches in the matched branch but not the
   fallback branch (divergent behavior on the same piece name).
10. **`resolve_kind` sets `kind_source` even when signed == hand kind** (provenance; mirrors
    resolve_rot placement_gate.py:383-386, pinned by `test_resolve_kind_agreeing_sign_still_tagged`).
    Consequence: byte-identity holds only for pieces with NO kind sign — which is the entire live
    project today (placement-review.json:48-69 has exactly 2 rot-only entries, no `kind` keys),
    so Step 10b's empty diff is a valid proof.
11. **`kind_flags`: a missing/empty built kind must NEVER suppress** — it cannot be shown to match
    (mirrors "a MALFORMED built rot NEVER suppresses", placement_gate.py:461-466). Scorer-honesty
    doctrine: silence is not agreement.
12. **The old inert arithmetic becomes a lie:** `inert = len(confirmed_all) - applied`
    (gen_floor2_v4_specs.py:412) counts a kind-only sign as "bound a piece but set NO facing".
    Replace with the per-entry `entry_is_inert` check (Step 5g) — an entry is inert only when it
    carries NO usable rot/facing AND no usable kind.
13. **Marker schema growth is safe:** `build_floor.require_placement_gate` reads only
    `verdict`/`inputs`/`rooms[].floating`/`rooms[].unplaced` from placement-gate.json
    (build_floor.py:392-435) — adding `"kind_flags"` to rooms rows breaks nothing. But the marker
    is refreshed ONLY by re-running the gate (its own note, placement_gate.py:723) — never hand-edit it.
14. **Unknown signed kinds are rendered and gated safely:** overlay boxes fall back to grey
    (`KIND_COL.get(it.get("kind"), "#606060")`, raster_overlay.py:250) and the gate treats unknown
    kinds as LENIENT (`_is_strict`/FURN_KINDS, placement_gate.py:62-68). Do NOT add vocabulary
    validation — kind is owner truth; but know that a signed kind outside FURN_KINDS silently
    flips that piece's gate strictness to lenient (owner's call by design). Also never add
    green/orange box colors (pinned `test_box_colors_never_use_provenance_channel`,
    test_raster_overlay.py:134-144).
15. **Comparison is exact case-sensitive string equality after strip.** `KIND_SYNONYMS`
    normalization (tv_cabinet→tv_console etc.) belongs to the benchmark lane
    (benchmark_reader.py:61-62) — importing it here would make the ledger lane silently accept a
    kind the owner didn't sign.
16. **Room scoping is inherited automatically:** the gate filters
    `e.get("room") in (room_id, "*")` (placement_gate.py:670) and the generator pools by exact
    room / `"*"` / unknown-room-vs-empty (gen_floor2_v4_specs.py:396-407). Kind signs ride the same
    entries — DO NOT add a parallel filter. A kind sign aimed at a builtin/fixture must ORPHAN
    (builtins never consult the ledger, gen:387-390) — pinned by
    `test_v4_orphan_gate_covers_kind_only_sign`; the overlay must therefore never emit kind stubs
    for builtin/fixture rows (edge #5).
17. **A sizeless kind sign matches any same-named piece** — `_size_consistent` returns True when
    the entry has no w/d (placement_gate.py:303-305). Intended (cheap paste), asserted in
    `test_confirmed_kind_size_guard_rejects_reused_name`'s second assert.
18. **The shared code has a second consumer:** the v3 generator
    `projects/PRJ-2026-002_c001-house/03_layout/gen_floor2_specs.py` + its 11-test suite also
    import resolve_rot/confirmed_rot. Verified its tests do NOT pin first-wins ordering
    (test_gen_floor2_specs.py has no multi-entry ordering test) — but run it (Step 9) to prove it.
19. **Encoding:** every touched file contains Thai literals and is UTF-8. Edit with the Edit/Write
    tools ONLY — PowerShell `Out-File`/`Set-Content` default to UTF-16 and would corrupt them.
    pytest collection over pipeline/scripts also imports test_gate0.py/test_clearance_check.py
    which run whole suites at import — a broken placement_gate import surfaces as a COLLECTION
    error in seemingly unrelated files; read the first traceback, not the last.
20. **`run()` still does NOT reconcile orphans** (only the generator does) — that backstop is the
    NEXT slice ("F"), deliberately out of scope here. Do not bolt it on.

## Acceptance criteria

Each is a command + an observable result. All must hold.

1. `python3 pipeline/scripts/test_placement_gate.py` → last line `82/82 placement_gate tests passed` (was 71/71).
2. `python3 pipeline/scripts/test_raster_overlay.py` → `19/19 raster_overlay tests passed` (was 16/16).
3. In `projects/PRJ-2026-002_c001-house/03_layout/v4/`: `python3 test_gen_floor2_v4_specs.py` → `17/17 gen_floor2_v4_specs tests passed` (was 14/14).
4. In `projects/PRJ-2026-002_c001-house/03_layout/`: `python3 test_gen_floor2_specs.py` → `11/11 gen_floor2_specs tests passed` (unchanged — shared-matcher change is non-breaking for v3).
5. `python3 -m pytest pipeline/scripts/ -q` → `N + 14 passed`, where N is the green total RECORDED in Step 0 (+11 placement_gate + 3 raster_overlay; the 3 new v4 tests live outside pipeline/scripts/ and are not collected). 0 failures/errors; must never drop below N. Per-file: test_placement_gate 71→82, test_raster_overlay 16→19, test_gen_floor2_v4_specs 14→17 (these per-file counts ARE stable — item A does not touch those files). If the total differs from N + 14 the executor added/lost a test — reconcile before proceeding.
6. Regen (Step 10a) prints `placement-review.json: 2 loaded, 2 facing APPLIED, 0 kind APPLIED, 0 orphaned` and `git diff --stat` over the two scene-graph JSONs prints NOTHING (byte-identical ⇒ the hash-pinned gate marker stays valid without re-gating).
7. Regenerated `review-read-vs-sheet.md` contains `## เซ็น kind (identity` and exactly 12 kind-stub ```json blocks (each parseable, has `"kind"`, lacks `"rot"`), 3 facing stubs (unchanged), and NOT the string `ยังเซ็นเข้า ledger ไม่ได้`.
8. Gate re-run (Step 10d) exits 0, prints overall verdict REVIEW (same as the pre-change marker), and the rewritten `placement-gate.json` contains `"kind_flags": 0` in BOTH rooms rows, `"calibration": "PASS"`, `"facing_flags": 0`.
9. Matcher-parity one-liner (Step 10e) prints `tv_console ('tv_console', 'owner-signed') contradicts_signed_kind`.
10. Last-wins proof: `python3 -c "import sys; sys.path.insert(0,'pipeline/scripts'); import placement_gate as G; print(G.confirmed_rot({'name':'b','w':2000,'d':1800},[{'name':'b','rot':90,'w':2000,'d':1800},{'name':'b','rot':270,'w':2000,'d':1800}]))"` prints `270`.
11. `projects/PRJ-2026-002_c001-house/03_layout/v4/placement-review.json` is bit-for-bit untouched: `git diff -- "projects/PRJ-2026-002_c001-house/03_layout/v4/placement-review.json"` prints nothing.

## Do NOT

- **Never write into the live ledger.** `placement-review.json` gains entries ONLY by the owner's
  paste. Do not add kind entries "to demonstrate", do not transcribe machine/hand-read kinds into
  `confirmed[]` — a machine-authored signature is a forged attestation (the stub's
  `"by": "owner (ระบุวิธียืนยัน)"` field exists precisely to force owner attribution). Tests use
  in-memory fixtures only.
- **Never let a signature move geometry.** Signed kind applies AFTER cluster matching; if you find
  yourself passing the signed kind into `match()`/`_wants_curve`, stop — that is the wrong layer.
- **Never default the missing side to "agrees".** A piece with no/malformed built kind is FLAGGED
  against its sign, not suppressed; an entry with no usable payload applies nothing and is reported
  inert. (Scorer-honesty doctrine: missing data is never defaulted into a pass.)
- **Do not touch** `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.claude/settings.json`,
  `.gitattributes` (hook-enforced), and do not run destructive shell.
- **Do not extend the gate's machine-verified layer.** `identity_check` stays a double-claim
  detector; the ONLY machine kind check is signed-vs-built string equality. No geometric/ML kind
  inference in this lane (that is the benchmark lane's F1 experiment, item C).
- **Do not give kind stubs a `rot` key or facing stubs a `kind` key** (edge #4 — cross-signing).
- **Do not make builtins/fixtures consult the ledger** to "fix" an orphaned kind sign — the orphan
  IS the correct behavior; fix the ledger or the generator, per the existing error message.
- **Do not scope-creep** into tv_console arrow parity, overlay-hash-in-marker freshness, or a
  run()-side reconcile backstop (all deferred to slice F). Include nothing from them unless a step
  above already produced it for free.
- **Do not hand-edit** `placement-gate.json`, `scene-graph.*.json`, or `review-read-vs-sheet.*` —
  they are generated; re-run the generator/gate instead.
- **Do not rename/renumber the `PLACEMENT-REVIEW ORPHAN` message prefix** (pinned by
  test_gen_floor2_v4_specs.py:135) or the `type`/verdict strings other tests pin.
- **Do not push; never `git add -A`;** commit only if asked, following the scrutinize-first ritual.
- The corpus/benchmark lane is untouched by this plan — `svg_plan_reader.py` stays
  annotation-blind and `benchmark_reader.py` unmodified; if you find yourself editing either,
  you drifted off-item.
