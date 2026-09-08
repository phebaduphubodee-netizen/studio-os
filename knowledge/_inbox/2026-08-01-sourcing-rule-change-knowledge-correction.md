# Correction owed to `knowledge/styles/` — the sourcing rule it cites was cancelled

**Staged 2026-08-01. Tier: REPO-DECISION correction, not domain research.**
Source of the change: owner order, recorded verbatim in
`docs/DECISIONS-render-assets.md` (top entry, 2026-08-01).
Why this is staged rather than applied: `knowledge/` is READ + CITE only
(`knowledge/CLAUDE.md`) — a correction enters through this flow, never a hand-edit.

## What changed

The owner cancelled the *"฿0 + CC0/public-domain เท่านั้น"* sourcing clause. The
sourcing rule is now **any source whose licence permits commercial use of the
RENDER** — CC0/PD, Trimble General Model License (3D Warehouse), CC-BY with
attribution recorded, paid royalty-free libraries.

**Not changed, and this matters for both passages below:** every DELIVERY rule in
`docs/LICENSING.md` survives untouched — Combined-Work scene only, no standalone
model, no aggregation, no redistribution of a non-redistributable mesh, scale
asserted on every ingest. A wider sourcing rule did not widen what may be handed
over, and it did not turn silence into permission.

## Target: `knowledge/styles/style-and-asset-references-discord.md`

### §3.8 — grounds partly expired, conclusion partly survives

Current text rules the 3D Warehouse / 3dzip / 3df.pro collection links
REFERENCE-tier-only, citing *"budget = ฿0 … CC0-only … Geometry enters `assets/`
only with a per-model licence verified CC0"*.

* **EXPIRED**: the ฿0 clause, the CC0-only clause, and the requirement that a
  per-model licence verify as **CC0** specifically. 3D Warehouse geometry may now
  enter — into the gitignored, non-redistributable cache
  (`assets/shared/warehouse/`, `pipeline/scripts/warehouse.py`), never into a
  commit. This is live, not theoretical: 13 models were fetched and rendered on
  2026-08-01 under R8's build-vs-acquire order.
* **SURVIVES, and should be kept as the section's spine**: *"That is a silence in
  the source, not a permission."* A per-model licence check is still required; it
  simply no longer has to return CC0. It has to return a licence that PERMITS,
  and none of these threads state any licence terms at all.
* Suggested replacement grounds: cite `docs/DECISIONS-render-assets.md` **by date
  heading**, not by line number (see the citation note below).

### §4 (3DSKY bundles) — the ⛔ call must be RE-DERIVED, and stays ⛔ meanwhile

The section states its call *"rests on the studio's standing asset decision
alone, and that is enough: budget ฿0 … CC0-only … A priced bundle fails ฿0 before
any other question is asked."* **That sole stated ground is gone.**

The conclusion is very likely still right, on the independent half the same
section already records: the bundles are priced far below the rights-holder's own
retail ⇒ the licence is **UNCLEAR / unverifiable**. An unverifiable licence fails
the NEW rule too, because the new rule asks for a licence that *permits*
commercial use — silence and doubt both fail it.

**Interim status: still ⛔ DO NOT BUY, DO NOT INGEST.** A rule change is not a
licence. Whoever applies this correction should rewrite §4's grounds onto the
licence-risk argument and delete the ฿0 sentence, not weaken the verdict.

## Stale line-number citations in the same file

The 2026-08-01 entry was prepended to a newest-first log, shifting every line
citation into `docs/DECISIONS-render-assets.md` by **55**:

| in `style-and-asset-references-discord.md` | cited | now | anchor to use instead |
|---|---|---|---|
| §3.8 | `:59` | `:112` | 2026-07-12 entry, decision 2 |
| §3.8 | `:61-62` | `:114-115` | 2026-07-12 entry, decision 3 |
| §4 | `:59`, `:61-62` | as above | as above |
| §5 (3dsky price) | `:132` | `:187` | 2026-07-01 furniture-pack entry, options table |

**Do not re-number them — re-anchor them to the DATE HEADING.** A log that grows
at the top guarantees line-citation rot; `scripts/inbox_audit.py` and
`docs/strategy.md` §F were converted to date anchors in the same pass and are the
pattern to copy.

## Verification available to whoever applies this

`python scripts/asset_license.py` audits every git-TRACKED asset and fails closed
on one that declares no licence or declares a non-redistributable one — i.e. the
rule this correction describes is machine-checked, not only written down.
Wired into `bash scripts/test_guards.sh`.
