# Blendkit API — what the search endpoint actually accepts, MEASURED (2026-08-23)

**TIER: REFERENCE, and the highest grade of the three files here** — this one is neither a
research answer nor a quoted contract. It is measurement, taken on this machine against the
live public endpoint, and every line reproduces in about forty seconds.

Method is the repo's own, already positive-controlled in `docs/blenderkit-month-2026-08-22.md`:
**a real filter splits the set and its halves sum to the unfiltered count; an unknown
qualifier silently answers 0, exactly like a deliberate misspelling; a malformed field name
answers HTTP 400.** All three behaviours were observed in the same session, which is what
makes "0 results" readable — on its own it proves nothing.

Endpoint, unauthenticated, no account needed:
`https://www.blenderkit.com/api/v1/search/?query=<url-encoded>&page_size=1` → `count`

---

## 1. The four operators a deep-research run recommended, and none of them exist

The 2026-08-23 DR (staged beside this file) devotes its §5 to "Advanced Search Operators"
and claims they *"dramatically increase your hit rate"*.

| query on `asset_type:model+bed` | count | reading |
|---|---:|---|
| (no filter) | **1244** | control — matches our own 2026-08-22 census exactly |
| `is_free:true` | **282** | known-real filter — also matches the census exactly |
| `rating:>=4` | **0** | DR-recommended |
| `resolution:8k` | **0** | DR-recommended |
| `license:cc0` | **0** | DR-recommended |
| `author:blenderkit` | **0** | DR-recommended |
| `zzznotafilter:9` | **0** | **negative control, invented by me** |

Four recommendations, four results identical to a string I made up to be wrong. This is the
third recorded instance of this research lane producing confident, specific, false detail
about prices, licences or interfaces; the standing rule holds — **a DR is a lead, and a
measurement is a finding.**

## 2. What is real, found by testing instead of asking

| filter | evidence it is real |
|---|---|
| `asset_type:` | model / material / scene / hdr / brush |
| `category_subtree:bed` | 1244 name-hit → **611** by category |
| `is_free:true` / `false` | **282 + 962 = 1244** — perfect split |
| `license:cc_zero` / `royalty_free` | **22 + 1222 = 1244** — perfect split (and note the DR's `cc0` spelling is the wrong one) |
| `manufacturer:<name>` | `bed+manufacturer:ikea` = 23 |
| `verification_status:validated` | real — but `uploaded` and `ready` both return 0, so every publicly searchable asset is already validated; the filter is a no-op on this corpus |
| filters compose | `license:cc_zero+is_free:true` = 10 against `cc_zero` alone = 22 |

Rejected outright with **HTTP 400** (the server knows these are not fields):
`quality_count:` · `faceCount:` · `textureResolutionMax:`

## 3. THE FINDING THAT CHANGES THE METHOD — server-side real-world SIZE filters

`dimensionX_gte` / `dimensionX_lte`, and the same for Y and Z. Metres, float. **The add-on's
own UI exposes none of these.**

```
asset_type:model+category_subtree:bed                              611
                            + dimensionX_gte:1.5                   551
                            + dimensionX_gte:1.5+dimensionX_lte:2.2 171
                            + dimensionZ_lte:1.0                   304
                            + dimensionX_gte:99                      0   ← sanity control
```

Why this matters more here than it would anywhere else: **the defect class that has cost this
lane the most rounds is dimensional.** D-109 — an instrument counted a 2,759 mm fabric
backdrop wall as bedding and declared the bed a pass. D-120 — `pick_anchor` fitted a bed
FRAME into a mattress slot and then scored it against a mattress table. Both were discovered
only after fetching, staging in Blender and measuring. This filter moves the size question
**in front of** the download.

It needs no code: the filters pass straight through the existing tool, which already prints
each row's dimensions.

```
$ python pipeline/scripts/blenderkit.py search \
    "asset_type:model+category_subtree:bed+dimensionX_gte:1.5+dimensionX_lte:2.2" --page-size 4
  free  626aa7dc  Bubble Round Soft Bed        2081x2466x937 mm   307685 faces
  free  4e650c66  Keywestbedding Phoenix       2110x2260x1194 mm  374441 faces
  free  686c5c9b  Keywestbedding Stansted      2110x2317x1294 mm  238163 faces
  free  f0a54602  Bunk bed                     1733x2032x1829 mm   88164 faces
```

The grammar is now printed by `blenderkit.py search --help`, not left in this file — a
finding parked in `knowledge/_inbox/` is the queue-with-no-consumer this repo bleeds from.

**AND THE LIMIT, stated so nobody over-reads the above.** The number is a SEARCH KEY, never a
spec. Blendkit's own uploader does not enforce scale — its dimensions check is commented out,
and the maintainers say so in writing — and the Terms disclaim measurement accuracy outright
(both quoted in `2026-08-23-primary-sources-terms.md`). `asset_scale` must still assert on
every ingest (R8). This narrows the shelf; it does not certify a size.

## 4. CC0 BEHIND THE PAYWALL — 236 assets, and they are the only permanent purchase

`license:cc_zero+is_free:false` returns real, named assets:

```
count: 12   (asset_type:model+bed+license:cc_zero+is_free:false)
  Cozy bed / Cloudrest Bed / Bed Komfort Prestigo Double / King Bed / Double Bed
  all: isFree=False  license=cc_zero
```

Census across the classes this studio actually needs:

| class | all | cc0 | cc0 free | **CC0 PAID** |
|---|---:|---:|---:|---:|
| table lamp | 5267 | 153 | 86 | **67** |
| plant | 4652 | 110 | 55 | **55** |
| cushion | 1543 | 46 | 19 | **27** |
| wall art | 2580 | 157 | 136 | **21** |
| vase | 2606 | 58 | 38 | **20** |
| bed | 1244 | 22 | 10 | **12** |
| mirror | 524 | 17 | 6 | **11** |
| clothes hanger | 1429 | 16 | 10 | **6** |
| books | 1069 | 36 | 31 | **5** |
| nightstand | 646 | 14 | 10 | **4** |
| shirt | 726 | 8 | 4 | **4** |
| tray | 258 | 8 | 4 | **4** |
| throw blanket | 114 | 2 | 2 | 0 |
| | | | **total** | **236** |

**Why this is the strongest single answer to "how does the month make the work better", and
why it does not depend on any claim in either research lane:** CC0 is a dedication by the
CREATOR, not a right rented from Blendkit. It is irrevocable and unconditional by its own
terms. Whatever the subscription contract says about lapsing — and the contract is in fact
generous, see the sibling file — it cannot touch a CC0 asset.

And `docs/LICENSING.md` already draws the line this lands on: **CC0 is committable to git;
royalty-free is gitignored, use-yes/redistribute-no.** So these 236 are the only Blendkit
assets that can become permanent, committed, versioned studio property rather than a
gitignored cache. They are reachable only while the plan is paid.

Caveats, so the number is not over-read: these are name-hit queries and classes overlap, so
236 is not 236 distinct objects; each still has to pass `dim_check` in its `asset_scale`
class and the D-119 style panel; and the licence field must be re-read per asset at fetch
time, which `blenderkit.py` already records raw.

---

## Reproduction

```python
import json, urllib.request, urllib.parse
def count(q):
    u = ("https://www.blenderkit.com/api/v1/search/?query="
         + urllib.parse.quote(q) + "&page_size=1")
    r = urllib.request.urlopen(
        urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60)
    return json.loads(r.read())["count"]
```

Always run a negative control in the same batch. Without `zzznotafilter:9` scoring 0 beside
them, the four fabricated operators above are indistinguishable from real filters that simply
matched nothing.
