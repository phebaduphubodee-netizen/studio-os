# Element 4 — Ensuite · Brass Tier B (Kohler `-2MB`) SKU-lock + quote sheet · 2026-07-19

**Tier: REFERENCE.** Follows the 2026-07-18 brass shortlist
([element4-ensuite_ffe-brassware-2026-07-18.md](element4-ensuite_ffe-brassware-2026-07-18.md),
sign-off B1.4). Task: get per-piece prices from Kohler/Boonthavorn to **lock SKUs**, and
**confirm every needed piece exists in one finish — "Vibrant Brushed Moderne Brass" (`-2MB`)**.
Product/price research only — **no client data in any query** (privacy-clean). Brief
`budget_ceiling_thb = null`, so nothing is checked against a ceiling. Prices are the
**current shop.kohler.co.th sale price (incl. tax), with list in parentheses** — a firm
project quote from Boonthavorn/a dealer may add a project discount; import lines carry **no
THB** and need a real importer quote.

Grounding: workflow `wf_fa7c58e2-f33` (1 finish-map + 7 per-fixture sweeps + adversarial
verifiers) + author's own re-fetch of the tall basin mixer and both accessory pages. Every
SKU/price below traces to a page that was actually retrieved; anything unfetched is tagged.

> **DECISION 2026-07-19 — owner chose Package B (modern-coherent, part-import).** Locked BOM →
> [element4-ensuite_ffe-brass-schedule-LOCKED-2026-07-19.md](element4-ensuite_ffe-brass-schedule-LOCKED-2026-07-19.md).
> Ink resolved the two blockers: deck tub filler IS drawn (needed); faucets deck-mounted (vessel per DD).

---

## ⭐ The one finding that matters (the prior caveat, resolved — and inverted)

The 07-18 shortlist worried `-2MB` was offered on *"~1 basin SKU"* in Thailand. **That fear is
wrong, but the real constraint is sharper than "is the finish available":**

> **`-2MB` is a real, live, first-party Kohler Thailand finish covering ALL SEVEN fixture types
> in stock — so an all-`-2MB` set IS buyable in Thailand today. The blocker is not the finish;
> it is _style × domestic-stock_.** In Thailand the `-2MB` finish on the **basin mixer, the bath
> filler, and the towel-rail/hook** lands ONLY on Kohler's **traditional _Memoirs_** line
> (stepped-column classic). The **modern** `-2MB` lines that would suit this deliberately-modern
> ensuite — Awaken, Components, Occasion, Avail — carry `-2MB` **but are US-import only, not
> stocked in TH**. The **showering** pieces (Anthem valve, Statement/Contemporary rain heads)
> and the **Cuff bidet spray** ARE modern + `-2MB` + Thai-stocked.

So the decision is **not** "which brass finish" (settled: `-2MB`). It is: **for the basin mixer,
bath filler, handshower-rail and accessories, do we (a) accept Kohler's _traditional Memoirs_
styling to buy everything in Thailand, (b) _import_ the modern `-2MB` pieces, or (c) break the
warm-satin story?** That is a **money-vs-coherence** call → the owner's (B1.4 tier/budget). My
recommendation is below the table.

Also settled: the piece we expected to be the gap — the **bidet spray / สายฉีดชำระ** — **exists in
`-2MB` and is in stock** (Cuff K-98100X-B-2MB). Hypothesis refuted.

---

## SKU-lock matrix (7 fixtures)

Legend — **Fit**: ✅ modern + `-2MB` + TH-stocked · 🟡 `-2MB` + TH-stocked but **traditional
Memoirs** styling · 🟠 modern + `-2MB` but **US-import** (no THB) · 🔴 no clean `-2MB` in TH.

| # | Fixture (qty) | Fit | Locked SKU (`-2MB`) | Per-piece THB (sale / list) | Stock | Source |
|---|---|---|---|---|---|---|
| 1 | Basin mixer, **tall/vessel** (×2) | 🟡 | **K-23373T-B4-2MB** (Memoirs, tall, h327 · spout 175) | **14,990** (25,723) ea → **29,980**/pair | in stock | [kohler TH](https://shop.kohler.co.th/K-23373T-B4-2MB/) |
| 1-alt | Basin mixer, **modern** (×2) | 🟠 | **K-77959-4A-2MB** (Components Tall, vessel, 1.2gpm) *or* **K-27003-4K-2MB** (Occasion Tall) | **no THB** — US ~$130–450 ea | US only | [Components](https://www.homedepot.com/p/318218561)/[Occasion](https://www.homedepot.com/p/323136015) |
| 2 | Shower valve + trim, 2-outlet **thermostatic** | ✅ | **K-EX26346T-9-2MB** (Anthem trim) **+ K-26340X-NA** (valve body, concealed/no-finish) | 10,090 (14,840) + 12,390 (19,900) = **22,480** system | in stock | [trim](https://shop.kohler.co.th/K-26346T-9-2MB/) · [body](https://shop.kohler.co.th/k-26340x-na/) |
| 3 | Rain head + arm (ceiling) | ✅ | **K-26301T-2MB** (Statement Ø225 head) **+ K-26325T-2MB** (ceiling arm) | 13,890 (21,500) + 8,290 (12,300) = **22,180** | in stock | [head](https://shop.kohler.co.th/K-26301T-2MB/) · [arm](https://shop.kohler.co.th/K-26325T-2MB/) |
| 3-alt | Rain head, **wall rigid-arm one-piece** | ✅ | **K-33414T-2MB** (Contemporary 10″ sq) *or* K-33410T-2MB (12″ rd) | **12,590** / 17,490 | in stock | [shop-by-color](https://shop.kohler.co.th/shop-by-color/) |
| 4 | Handshower + slide rail | 🟠/🟡 | **head:** K-98952T-L-2MB (Rainduet, TH) · **rail:** **K-98341-2MB** (Awaken slidebar, US import) | head **3,590** (6,400) TH · rail **no THB** (US) | head in stock; rail US | [head](https://shop.kohler.co.th/kohler-rainduet-k-98952t-l-2mb/) · [rail](https://www.homedepot.com/p/317842536) |
| 5 | Bath filler, **deck-mount** | 🔴 | **no TH `-2MB` deck filler.** Import: **K-77985-2MB** (Components deck spout) + handles K-77990-9-2MB + valve, *or* **T33969-4-2MB** (Elate complete trim) | **no THB** — US ~$490 (spout) + parts | US only | [Components](https://www.kohler.com/en/products/bathtubs/shop-bathtub-faucets/components-deck-mount-bath-spout-w-tube-design-77985) |
| 6 | Towel rail + robe hook | 🟡 | **K-486T-2MB** (Memoirs 24″ rail) **+ K-492T-2MB** (hook) | 4,450 (8,795) + 2,650 (5,275) = **7,100** | in stock | [rail](https://shop.kohler.co.th/K-486T-2MB/) · [hook](https://shop.kohler.co.th/K-492T-2MB/) |
| 7 | Bidet spray / สายฉีดชำระ | ✅ | **K-98100X-B-2MB** (Cuff, 1.2m hose + bracket) | **3,390** (5,400) | in stock | [kohler TH](https://shop.kohler.co.th/K-98100X-2MB/) |

**Notes on the tricky lines.**
- **#1 basin type dependency:** if the basins are **vessel/countertop** the tall mixer above is
  right; if **undermount**, the standard Memoirs single-hole **K-454T-4V-2MB @ ฿13,170 (27,381)**
  fits and is cheaper. Confirm basin type from the ink before ordering. The 2 basin mixers sit on
  the **hero oak vanity** — this is the most visible brass in the room, so the modern-vs-Memoirs
  style call bites hardest here.
- **#2 valve body is `-NA` on purpose:** a concealed in-wall body has no visible finish, so `-NA`
  is correct — it is **not** a finish mismatch. Only the trim/panel (`-2MB`) shows.
- **#3 cost lever:** Statement = **ceiling** rain (needs in-ceiling plumbing); the Contemporary
  rigid-arm (**#3-alt**) is a **wall** one-piece and ~฿10k cheaper.
- **#4 the rail is the catch:** Kohler TH has **no slide bar in `-2MB`** at all (only a fixed
  Exhale connector-hook). Options: (a) drop the *sliding* rail → TH Rainduet head + a `-2MB`
  fixed hook (Refinia **K-99035T-2MB**, TH, price unfetched); (b) import the Awaken slidebar for a
  true modern slide rail; (c) a non-Kohler brass rail (finish-match risk on the bar).
- **#5 is the hardest piece:** the only `-2MB` "bath" item in TH is the **Memoirs wall combo
  K-31153T-B4-2MB @ ฿44,241** — a wall shower+bath+handshower unit, **not a deck filler**, and
  redundant with the separate shower. A true deck filler in `-2MB` is US-import; the TH-stocked
  warm fallback is **French Gold K-77985T-AF (polished, not satin → sheen clash)**. Recommend
  confirming the tub **fill method** against the ink before spending here.

---

## Two complete packages (pick the trade, then I lock it into the spec)

### Package A — "All-Thai, in-stock, all `-2MB`" · finish-coherent, **style-mixed**
Everything from shop.kohler.co.th today; accept **Memoirs traditional** basin + accessories, a
**fixed hook** instead of a sliding rail, and resolve the bath filler (Memoirs wall combo or a
French-Gold deck spout).
- Running total (tall basin ×2, Anthem, Statement head+arm, Rainduet head + est. hook, Memoirs
  accessories, Cuff): **≈ ฿90,000** — **plus the bath filler (open).** Lands inside the 07-18
  Tier-B band (~฿70–120k). No import, full Kohler-TH warranty, short lead time.
- Cost: a stepped-column *Memoirs* faucet on a minimalist floating-oak vanity is exactly the
  style clash the reverse-Albers signature (D-E4-1) is built to avoid.

### Package B — "Modern-coherent" · TH for what's modern, **import the rest** *(recommended for the hero pieces)*
- **Buy in TH now (modern + `-2MB` + stock):** Anthem valve/trim `22,480` · Statement rain head+arm
  `22,180` (or Contemporary wall `12,590`) · Rainduet handshower head `3,590` · Cuff bidet `3,390`
  → **≈ ฿51,600 TH.**
- **Import (modern + `-2MB`, USD anchors → needs an importer quote):** 2× tall basin mixer
  (Components K-77959-4A-2MB / Occasion K-27003-4K-2MB) · Awaken slide rail K-98341-2MB · deck bath
  filler (Components K-77985-2MB + handles/valve, or Elate T33969-4-2MB) · *optional* modern
  accessories (Composed K-73146-2MB / Purist K-14443-2MB).
- Cost: import duty/VAT + FX + shipping + **lead time**, and no Thai warranty channel on the
  imported lines.

**My recommendation (this is a money/intent call, so it's yours to set — I'm bringing a position,
not a menu):** go **Package B for the basin mixers above all** — they're the most-seen brass, right
on the signature vanity, and a traditional Memoirs mixer there quietly defeats the modern thesis.
Import the **deck filler** too (or delete it if the ink's fill method allows). Take the **slide rail
→ fixed `-2MB` hook** simplification to stay all-Thai on the wet wall. Leave **accessories on TH
Memoirs `-2MB`** (฿7,100, low-visibility, in stock) unless you want them modern enough to justify
importing hooks. That buys modern coherence exactly where the eye lands and spends import effort on
~3 lines, not 7.

---

## Ready-to-send quote-request sheet

I can't submit a quote to Boonthavorn from here (no channel), but these are the exact lines to send.
For the TH lines the shop.kohler.co.th price above **is** the current per-piece figure — a dealer
quote mainly buys a possible **project discount** off it.

**→ To a Boonthavorn brass counter / Kohler TH dealer (ask project price + lead time + stock):**
```
Finish for ALL lines: Vibrant Brushed Moderne Brass (2MB)
1. Basin mixer, tall     Memoirs K-23373T-B4-2MB        x2   (or undermount: K-454T-4V-2MB)
2. Shower valve trim     Anthem  K-EX26346T-9-2MB        x1  + valve body K-26340X-NA x1
3. Rain head + arm       Statement K-26301T-2MB + K-26325T-2MB  x1  (or wall: K-33414T-2MB)
4. Handshower (head)     Rainduet K-98952T-L-2MB         x1  + hook Refinia K-99035T-2MB x1
6. Towel rail + hook     Memoirs K-486T-2MB + K-492T-2MB x1 each
7. Bidet spray           Cuff    K-98100X-B-2MB          x1
(pop-up drain K-7119T-2MB — was OUT OF STOCK; confirm)
```
**→ To a Kohler US authorized reseller / a Thai importer (get landed THB incl. duty/VAT + lead time):**
```
Finish for ALL lines: Vibrant Brushed Moderne Brass (2MB)
1. Basin mixer, tall     Components K-77959-4A-2MB  (or Occasion K-27003-4K-2MB)   x2
4. Handshower slide bar  Awaken   K-98341-2MB   (+ handshower K-72414-G-2MB, or kit K-26914-Y-2MB)
5. Bath deck filler      Components K-77985-2MB + handles K-77990-9-2MB + rough-in valve
                         (or complete: Elate T33969-4-2MB)
6. (optional modern acc) Composed K-73146-2MB / Purist K-14443-2MB hooks
```

---

## Honest gaps / what a firm quote still has to settle
- **Basin type (vessel vs undermount)** decides tall vs standard mixer — confirm from the ink.
- **Tub fill method** (deck filler vs wall/handshower fill) decides whether line #5 is even bought.
- **Import lines have USD anchors only** — real landed THB (duty/VAT/FX/freight) needs the importer.
- Unfetched TH prices (Refinia hook K-99035T-2MB, Contemporary arm inclusion) — dealer confirms.
- **Render impact: none.** The render already uses a generic PVD-brass BSDF; locking these SKUs
  changes only the **sourceable spec**, not the image (per 07-18 shortlist).

## Sources
Kohler Thailand official e-shop (all TH prices/finish/stock, retrieved 2026-07-19):
[basin tall](https://shop.kohler.co.th/K-23373T-B4-2MB/) ·
[Anthem trim](https://shop.kohler.co.th/K-26346T-9-2MB/) · [valve body](https://shop.kohler.co.th/k-26340x-na/) ·
[Statement head](https://shop.kohler.co.th/K-26301T-2MB/) · [ceiling arm](https://shop.kohler.co.th/K-26325T-2MB/) ·
[Rainduet handshower](https://shop.kohler.co.th/kohler-rainduet-k-98952t-l-2mb/) ·
[towel rail](https://shop.kohler.co.th/K-486T-2MB/) · [hook](https://shop.kohler.co.th/K-492T-2MB/) ·
[Cuff bidet](https://shop.kohler.co.th/K-98100X-2MB/) · [shop-by-color 2MB filter](https://shop.kohler.co.th/shop-by-color/).
US catalog (proves modern `-2MB` exists globally; USD not THB):
[Components single-hole tall](https://www.homedepot.com/p/318218561) ·
[Occasion tall](https://www.homedepot.com/p/323136015) ·
[Composed K-73167-4-2MB](https://www.homedepot.com/p/319602377) ·
[Awaken slidebar K-98341-2MB](https://www.homedepot.com/p/317842536) ·
[Components deck spout K-77985-2MB](https://www.kohler.com/en/products/bathtubs/shop-bathtub-faucets/components-deck-mount-bath-spout-w-tube-design-77985) ·
[Components handles K-77990-9-2MB](https://www.homedepot.com/p/318218524).
