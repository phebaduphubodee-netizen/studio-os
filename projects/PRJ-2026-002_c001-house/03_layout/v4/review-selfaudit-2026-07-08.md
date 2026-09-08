# self-audit adjudication — 2026-07-08 (floor2 v4)

The tier-1 self-doubt suite's first live run ranked a **CRITICAL** (bench facing) and a **HIGH**
(console identity) at the top (doubt-score 1291). This is the payoff step — adjudicating them.
Both were adversarially verified against the real render/ledger code before any action.

## 1. CRITICAL "bench facing REVERSED 180→0" — was a **FALSE POSITIVE of the instrument** ✔ FIXED IN CODE

**Verdict: not a regression. No owner action, no facing to restore.** The instrument was crying wolf.

- v3 typed `ม้านั่งปลายเตียง (bench)` at `rot 180`; the v4 clean rebuild types face S → `rot 0`, and
  `to_spec` drops a zero rot (`if rot:`), so v4 renders it south. rebuild_diff measured |180−0|=180 ≥
  135 → CRITICAL.
- **But a bench renders as a single centered box** — it is NOT in `build_floor._FURN_KINDS`
  ([build_floor.py:31](../../../pipeline/scripts/build_floor.py#L31)), so `place_massing` takes the
  `add_oriented_box` else-branch ([build_floor.py:156](../../../pipeline/scripts/build_floor.py#L156)),
  rotated about its **centre**. **A rectangular box is 180-rotationally symmetric → a 180° flip is a
  byte-identical mesh.** v3-rot-180 and v4-rot-0 produce the *same scene*. Contrast the tub chairs
  (`armchair` ∈ `_FURN_KINDS` → `furniture.parts` adds a backrest → 180° really flips) — the genuine
  Row-5 wound. rebuild_diff only abstained on `shape=="round"`; it missed **box symmetry**.
- **Fix** ([rebuild_diff.py `_facing_change`](../../../pipeline/scripts/rebuild_diff.py)): when both
  rounds render a piece as a 180-symmetric mass (kind ∉ `_DIRECTIONAL_KINDS` = `{sofa, loveseat,
  chair, dining_chair, armchair, bed}` — the only asymmetric `furniture.py` builders; **tables fold
  too**, being a centred top on 4 symmetric legs), the rot change is folded into its 180 symmetry
  before judging. A box's folded delta maxes at 90 → a box can reach MEDIUM (a visible 90° reorient)
  but **never the reversal band**. Directional kinds skip the fold → the tub-chair CRITICAL is intact.
  Keyed off the render's own directional set, so if a kind later gains a front the instrument follows.
- **Verified:** `test_rebuild_diff.py` +5 tests (box abstain, box-90 MEDIUM, directional-stays-CRITICAL,
  furniture-sync, real bench v3→v4) and `test_self_audit.py` updated — **61 pass**. Live re-run:
  **doubt-score 1291 → 291, CRITICAL 1 → 0** (the false positive removed, nothing real hidden).

> The bench's *identity* ("bench") is still an open MEDIUM (hand-typed, unsigned) in a different
> lane — that is a real, separate doubt, untouched by this fix.

## 2. HIGH "console identity cabinet→console" — **TRUE POSITIVE; owner already decided; needs a durable signature**

**Verdict: real regression class, but the decision already exists — persist it as a signature.**

- v3's fused `คอนโซล+กล้วยไม้ BF12-2` (kind `cabinet`) paired to v4's `โต๊ะวางกล้วยไม้ (console)`
  (kind `console`) by geometry IoU **0.595** (a real pair; the v4 tall cabinet `ตู้สูง BF12-2` is IoU
  0.0 → correctly a separate added piece). The `cabinet→console` relabel is the **correct result of
  the owner's 2026-07-06 un-merge** (READING-NOTES-v4 L74 / DIFF-v4-vs-v3 L43: "BF12-2 tall cabinet ≠
  the orchid table — separate pieces"). But that decision lives **only in prose**, with no
  `confirmed_kind`, so rebuild_diff (correctly) reads it as an unsigned identity change — exactly the
  wound DIFF-v4-vs-v3 L31-33 warns about ("never left in a prose note").
- **Resolve = persist the un-merge as a durable owner signature.** This is owner-layer (two-layer law:
  identity is owner-only to sign), so it is **NOT applied here** — presented ready for one-word ratify.
  Signing it drops this HIGH to a LOW provenance trace AND makes `resolve_kind` force `console` every
  rebuild, so a future re-read cannot silently re-fuse/re-label it.

### Ready-to-sign entry (append to `placement-review.json` → `confirmed[]`) — OWNER RATIFY
```json
{
  "room": "sitting_room",
  "name": "โต๊ะวางกล้วยไม้ (console)",
  "kind": "console",
  "w": 1002,
  "d": 402,
  "by": "owner (2026-07-06 un-merge; ratified 2026-07-08)",
  "date": "2026-07-08",
  "note": "orchid table = console, separate from the BF12-2 tall cabinet (owner 2026-07-06). Locks resolve_kind so a rebuild cannot re-fuse/re-kind it. kind match is case-sensitive lowercase."
}
```
Recommended companion (locks the *other* half of the un-merge so BF12-2 cannot re-fuse) — copy the
exact name + w/d from `scene-graph.sitting_room.json` at sign time:
```json
{ "room": "sitting_room", "name": "ตู้สูง BF12-2 (70x40x280)", "kind": "cabinet",
  "w": 700, "d": 400, "by": "owner (2026-07-06 un-merge; ratified 2026-07-08)", "date": "2026-07-08" }
```

Signature schema (verified against `placement_gate.py`): binds by **exact name** + **±20% size**
(orientation-agnostic), `room` routes the pool; kind match is **case-sensitive** (`"console"`, not
`"Console"`); a name typo → loud orphan hard-fail at build (not silent); omitting kind → inert (silent).

## Net
- Instrument hardened (a whole class of render-inert facing flips will never false-CRITICAL again).
- The **one real open regression** (console) is one owner signature from closed.
- Doubt-score 291 now = HIGH console (100) + 18× MEDIUM unsigned hand-typed identities (180, the
  systemic "no owner signs + no corpus priors" band — the D/Structured3D-priors lane would corroborate
  these wholesale) + 11× LOW. Coverage line unchanged (honest).
