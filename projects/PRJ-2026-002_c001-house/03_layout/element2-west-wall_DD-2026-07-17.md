# Element 2 — West wall (bookshelf + BF11 makeup vanity)
## Design-Development decision record — 2026-07-17

> **What this is.** Element 2 of the master-suite DD: the WEST wall the bed FOOT
> faces — an OPEN display/book shelf (ex-TV, freestanding) at the south, and BF11,
> a LOW seated makeup/dressing vanity, at the north, with TWO casement windows in
> the wall above the vanity. After owner sign-off this folds into
> `master-suite.CANONICAL.spec.json`.
> **Method.** Geometry INK-TRUED from the designer's furniture plan (adversarial
> read, see Provenance), never invented; composition/ergonomics grounded vault-first,
> NLM only on vault gaps; every dimension traces to the drawn ink or a cited datum.
> **Privacy.** All plan reads are LOCAL; no client geometry leaves the machine.

---

## 0. The two pieces (INK-TRUED 2026-07-17)

> ⚠️ The canonical spec was **materially wrong** on this wall. All values below are
> reproduced 0–1 mm from the designer's ink and checked against the sheet's own
> printed dimensions (`700` / `2950` / `2850` ladder + the `BF11.320x60x280CM`
> label). Full record: `element2-west-wall_ink-read-2026-07-17.json` +
> `…-2026-07-17.png` (annotated). Frame = room mm, x EAST from the master west wall,
> y NORTH from the south glazing.

| piece | spec SAID | ink TRUTH | impact |
|---|---|---|---|
| bookshelf | x306, y130, d2046, h1800, "against wall" | back **x305.8**, front x905.6, **y248.1→2047.8** (len **1800**, not 2046), freestanding **250.8 mm off wall** | length −246; south end only y248→451 (~203) overlaps SW glass |
| BF11 vanity | **x0** (against wall), y2650, w600, d3200, h750 | back **x305.8** (FREESTANDING, 250.8 off wall), front x804.1, **y2600→5799.4** (len 3199 = label 320), **drawn depth 498.3** | spec's "against wall" REFUTED; this is the ~306 mm #9c flagged |
| west wall | "solid masonry north of ~y451" | **NOT solid** — two ~600 mm casement windows + two 200×200 piers | the whole west-elevation premise changes |

**Ink-true geometry (rock-solid):**

- **glz-west** (SW-corner glass): face x55 (spec x0), y-697.8→451.2, len 1149; masonry
  begins y498.8. Unchanged, re-confirmed against printed `700` (Δ2.2 mm).
- **Bookshelf** (open display, ex-TV, freestanding): back x305.8 / front x905.6
  (depth 599.9 ≈ 600), y248.1→2047.8 (len 1799.7 ≈ 1800). Back stands 250.8 mm off
  the wall face (a continuous furniture back-plane, shared with BF11). South end
  (y248→451, ~203 mm) overlaps glz-west; the rest backs solid masonry (y498→2048).
- **BF11 makeup vanity** (low, freestanding): back x305.8 / front x804.1 (drawn
  depth 498.3; **label says 600 — a ~102 mm designer-tier discrepancy, carried
  open**), y2600→5799.4 (len 3199.4 = label `320`). South base step y2600–2800
  widens WEST onto the 200×200 pier at x153.4. **Seated kneehole** inner face x353.4,
  y3549.1→4948.8 (len 1399.7), stool centred at y4249.
- **West wall face-map** (x55, S→N): glz-west (0.48pt glass) → masonry south run
  y498.8–2600 (~2101, the bed foot faces this) → 200×200 pier y2600–2800 → **WINDOW 1**
  rough y2898.4–3498.3 / clear y2949.2–3447.5 (~500), west-swinging casement →
  masonry mid run y3498.3–4999.6 (~1501, the mirror pier behind the kneehole) →
  **WINDOW 2** rough y4999.6–5599.5 / clear y5047.2–5548.7, west-swinging casement →
  200×200 pier y5697.9–5897.8 (NW corner).
- **Curtain pocket** = 250.8 mm continuous (spec's 197 for the west leg was wrong);
  serpentine curtain symbols drawn at the SW glass AND both windows.
- **Stool/seat**: envelope x854.9–1400.8 / y3993.4–4494.5, centred on the kneehole
  (y4249). Curved back → reads as a tub chair, not a backless stool (owner-tier).

**OWNER-CONFIRMED PREMISE (2026-07-17, the fork that gated this DD):**
1. The two west openings are **casement windows** (open outward/west) — NOT doors,
   NOT furniture features. (The 0.48pt=glass inference, promoted to fact by the
   owner, exactly as the SW glass was.)
2. **BF11 is a LOW ~750 mm makeup vanity**, not a full-height 2800 dressing wall —
   the two windows show ABOVE the vanity, flanking the seated mirror station. The
   label's `280` (2800) is the designer's full-height family default; the owner's
   re-type to a seated vanity governs.

So the west wall reads, bed-foot-on: **a low makeup vanity below two daylight
windows that flank a central mirror (on the solid pier), an open display bookshelf
to its south glowing against the SW garden glass, and curtains dressing all the
glass in a 250 mm pocket.**

---

## §0b · What this sheet can and cannot be asked

Same discipline as element 1 (drawing-tier / pen-resolution law). At 1:75 a 0.6pt
pen covers 15.87 mm; the coord snap is ~3.17 mm — no difference finer than ~2.5 mm
is real. The furniture plan answers **WHERE / HOW BIG / WHAT IT IS CALLED** to
~2.5 mm and nothing else. It does **not** carry: window **sill/head heights**,
BF11's **height** (label-only), shelf/drawer **module**, mirror size, materials,
or curtain hardware — those are ours to DESIGN or the owner's/designer's to answer,
and their absence is not a finding. The one genuine drawing-vs-schedule conflict
(BF11 depth 498.3 drawn vs 600 labelled, ~102 mm) is beyond pen resolution and is
a real designer question (§3).

---

## §1. GROUNDED evidence (vault-cited — safe to gate a decision)

**Ergonomics — vanity** (`ergonomics/casework-fixture-clearances-th-practice.md §4.1,§2.4`;
`_inbox/nlm-element1-dressing-wall-2026-07-16.md`, Panero & Zelnik):
- Counter work-surface **711–762 AFF** → spec **h750 ✓ CONFIRMED**. Depth 600 standard
  (drawn 498 is shallow-but-workable for makeup; §3 flag).
- Knee/thigh clearance **≥196 mm**; popliteal seat **406–432** (the kneehole is 1400 wide
  — generous). Seated mirror centre **1120–1267 AFF**, face-to-mirror **457–610**, field
  **610–762**. Drawer faces **200–250**. Aisle 914 base → **widen 1067–1168** where it
  doubles as circulation.

**Ergonomics — open shelving** (`ergonomics/tv-viewing-and-furniture-dimensions.md#L41,68-69`;
`casework-fixture-clearances §L87-100`):
- Daily-reach zone **800–850 AFF**; display-shelf depth **350–400** (horizontal) / **<280**
  (tilted); decorative **1500–1600** (light) / **1800–2100** (needs reaching); standing reach
  ≤~2286. → a 1800-tall unit: daily/book at mid, display/light objects high.

**Lighting — makeup** (`lighting/lumen-method-and-fixture-placement.md §2`;
`lighting/residential-lighting.md §3`; floor `codes-th/mr39-…#L45`):
- **538–861 lux** on the face (vanity/grooming), **CRI ≥90**, **CCT 3000–4000 K**; **flank the
  mirror, never a single overhead**; statutory floor **100 lux**.

**Composition** (`styles/color-composition.md#L47-55,77-79,274`):
- **60-30-10 LOCKED**: plaster 60 (ground) / oak 30 (secondary) / brass 10 (accent).
  Single-large-focal + **odd groupings (3,5)**; never judge a finish colour independent of
  its light.

**Materials** (`materials/caesarstone-engineered-stone-th.md §5,L56,L75`;
`residential-materials.md#L64`; `render-defects.md#L51`; `aella-hardware-th.md#L24`;
`millwork-casework.md#L118-125`):
- **Caesarstone** engineered quartz: durable, **non-porous, no sealing**, tropical-moisture
  "excellent"; cool colours (Symphony Grey / Alpine Mist / Turbine Grey). Microcement
  wet-durability = vault gap.
- **PH-02 (brightness-ordering defect)**: brass/high-shelf/frame at the two windows (the
  luminance point) out-reads them → **brass only low-profile (vanity pulls) or skipped**;
  **frameless mirror**.
- Bookshelf carcass **cool non-oak** to hold 60-30-10 (the room is already oak-heavy; oak
  bookshelf + oak vanity would break the monopoly rule element 1 exists to escape).

**Render** (`brand-standards/render-quality.md §L44-140`; `render-defects.md#L51,52`):
- Light hierarchy ambient+task+accent; physical camera 35–50 mm ~f/2.8; balance
  natural+artificial (Shulman); contact shadows on every fold/edge; **garden HDRI
  visible-but-subdued** beyond the glazing (PH-02); sheer as the mirror-glare diffuser.

## §2. CONVENTION — verify before CDs (candidate values, not grounded)

- **Window sill ~1000 AFF [est]** to clear the 750 counter (industry practice; NOT in
  vault or codes-th — a genuine gap, §3). **Head ~2200–2400 [est]**.
- **Toe-kick 50–75 [est]** (shop practice; vault silent for vanities).
- **Shelf module** (vault gap — millwork.md explicitly carries "no spans/thicknesses"):
  studio-default shelf **~25 thick**, clear height **~300–350** (books+display mix), **max
  open span ≤900** before a vertical divider (= millwork `MAX_SPAN` 0.9).
- **Glass-backed open shelving support** — vault gap; DESIGNED here (open grid, no back
  panel; carried on sides + floor, garden shows through the south bay).

## §3. OPEN — supplier / owner / designer-gated (do NOT fabricate)

- **Window sill + head height** above the 750 vanity counter — NOT on the furniture
  plan (no elevation). Needed to place the two casement windows in z. `[est]` until
  the owner/architectural plan gives them; render-tier default to be chosen in §4.
- **BF11 depth 498.3 (drawn) vs 600 (label)** — ~102 mm, a real designer call. Render
  default = drawn 498.3 (the strokes), flagged for the designer; does not change the
  design, only the exact back-plane.
- **Curtains on the two west windows** — the sheet draws serpentine symbols there, so
  the intent to dress them is ink-supported, but the existing `curtain_track` west leg
  (y-450→2650) does not yet reach the windows (y2898+). Extending the west curtain
  treatment to the two windows is scoped as a coordinated follow-on to element-1's
  curtain system, not invented here.
- **Casement operability / handing** — the swing arcs read "opens west", but sash vs
  fixed and hardware are joinery/supplier tier.

## §4. DECISION MENU — design decisions (DECIDED, grounded; not a taste menu)

Per the element-1 D7 rule (owner is an engineer, not a designer): these are DECIDED
and will be built, rendered, and shown — not offered as A/B/C taste picks. The
governing idea: **the west wall is the COOL counterpoint to the warm oak signature
(east BF14 / north BF09-3)** — which is exactly how D1-A's 60-30-10 anti-monopoly is
kept (oak stays the 30% secondary; the west wall does not add a third oak mass).

**D2-1 · Bookshelf — open display, freestanding, glass-backed south bay** (decision B,
owner-signed 2026-07-17). Freestanding open grid, back x306 (250 off wall), **no solid
back panel** — display reads through to the wall/curtain, and at the south end (y248–451,
over glz-west) the **garden shows behind it as a lit backdrop** (sheer between). Grid:
horizontal shelves ~25 thick, clear ~300–350; **2 vertical dividers → 3 bays ~583**
(≤ MAX_SPAN 900); height 1800. **Material: COOL carcass + dividers** (plaster-grey /
microcement tone) with **OAK shelf boards** as the restrained warm thread that ties it to
the room without a third oak mass (§1 anti-monopoly). Display = odd groupings (3/5), one
sculptural object per bay; light objects high, books mid.

**D2-2 · BF11 — low seated makeup vanity** (~750, owner-signed). Counter at **750**
(within 711–762 ✓), depth **498 drawn** (flag vs label 600, §3; workable for makeup).
**Counter = Caesarstone** cool quartz (Symphony Grey / Alpine Mist) — durable, non-porous,
the cool contrast. Kneehole y3549–4949 (1400 wide), knee ≥196 ✓, tub-chair pulls in.
**Drawer banks flank the kneehole** (the two solid masses y2600–3549 S + y4949–5799 N),
faces 200–250, **microcement / cool fronts**, toe-kick 50–75 [est]. These masses sit
BELOW the two windows.

**D2-3 · Mirror + makeup lighting** (between the two windows). **Frameless mirror** on the
solid masonry pier (y3498–4999) behind the kneehole, **wide (~1400, fills the pier
between the windows) × field height ~700**, centre ~1200 AFF (seated eye 1120–1267);
no brass frame (PH-02). Makeup light: **task flanking the mirror** (vertical LED/sconce
each side), CRI ≥90, CCT 3000–3500 K, 538–861 lux on the face; the two windows give
daylight fill, **backlight controlled by the sheer as diffuser** (§1). Lighting fixtures
are stage-05 detail — recorded here, placed at build as render_state.

**D2-4 · Materials + brass under the luminance rule.** West wall = cool: Caesarstone
counter, microcement/cool drawer fronts + vanity body, cool bookshelf carcass, oak shelf
boards, frameless mirror. **Brass: low-profile only** — satin-brass vanity drawer pulls
(AELLA SB, L-series) low on the base, OR skipped from the west wall entirely (default:
minimal low pulls). **No brass at the mirror or high shelves** (PH-02: the windows are the
luminance point).

**D2-5 · The two casement windows as openings.** Add `glz-west-win1` (rough y2898.4–3498.3)
and `glz-west-win2` (rough y4999.6–5599.5) to `room.openings`, type glass. **sill ~1000
AFF [est]** (clears the 750 counter), **head ~2200 [est]** — render-tier, owner/arch-plan
to confirm (§3, §5). The garden HDRI (rainforest_trail, element-1 exterior) shows through
them, subdued vs interior task light (PH-02). Curtains on the two windows = coordinated
follow-on to element-1's curtain system (one continuous run, §3) — added as openings now;
window-curtain track extension may land this pass or next.

## §5. Owner / designer numbers still needed (minimal)

- **Window sill + head height** (vault + codes-th gap) — building with sill 1000 / head
  2200 [est]; nudge if the architectural plan differs.
- **BF11 depth** 498 (drawn) vs 600 (label) — building with drawn 498; designer to confirm.
- **Brass on the vanity pulls** — default minimal low pulls; owner may say none.
- **Makeup-light fixture + mirror SKU** — stage 05 / supplier tier.

## §6. After sign-off — fold into canonical spec

- `builtins` bookshelf: y 130→248.1, d 2046→1800, keep x306/w600/h1800; add
  freestanding + glass-backed-south-bay design block.
- `builtins` BF11: x 0→306 (freestanding), y 2650→2600, d 3200→3199, w 600→498.3
  (flag vs 600), keep h750; add low-vanity design block (counter/kneehole/drawers/mirror).
- `room.openings`: ADD glz-west-win1 (rough y2898.4–3498.3) + glz-west-win2 (rough
  y4999.6–5599.5), type glass/window, sill/head `[est]`.
- `room` west-wall note: "punctuated by two casement windows + two 200×200 piers".
- `curtains` west-leg slot: 197→250.8; note the two windows also carry drawn curtains.
- `eye_camera_variants`: ADD a bed-foot west-facing verify view.

---

## Provenance

- **Ink read**: workflow `west-wall-ink-read` (run `wf_f01c59ee-8d0`, 2026-07-17):
  5 independent readers each dumping ink via the recovered `ink.py` (committed
  calibration `floor2-walls-mm.json`, 26.45 mm/pt) → reconcile → 3-lens adversarial
  verify per load-bearing value → high-effort synthesize. 30/31 agents; the one
  errored lens (`verify:glz-west:stroke`) was independently confirmed by its two
  siblings. Result: `element2-west-wall_ink-read-2026-07-17.json`.
- **Owner premise** (casement windows + low vanity): confirmed 2026-07-17 in-session.
- **Base geometry**: designer furniture plan
  `00_intake/raw-local/The City …_Plan funiture 02.pdf` (page 1, vector).
- **Carried from element 1**: the locked palette (oak veneer / cool plaster /
  microcement / satin brass), the anti-monopoly 60-30-10 (D1-A), the
  brass-not-at-luminance rule, and the D7 decide-build-render-show discipline.
- **Design grounding — vault-first, NO fresh NLM DR (owner-accepted 2026-07-17).**
  Element 2 used 4 knowledge-manager (vault) lookups (cited, §1) + element-1's
  DISTILLED NLM files (`_inbox/nlm-element1-dressing-wall-2026-07-16.md`,
  `nlm-element1-curtain-2026-07-16.md`) — so the ergonomics/materials are
  NLM-grounded transitively. The composition-theory gaps the vault flagged
  (open-shelf module, glass-back support, bed-foot niche — §2) are filled with
  STUDIO-DEFAULT design values: the furniture plan does not carry them and they
  are ours to design. This is a LIGHTER grounding than element 1 (whose
  composition was grounded by a fresh NLM DR, notebook a5a43395). The owner
  asked "ชิ้นนี้ได้ทำ DR มั้ย?" and chose vault-sufficient — recorded so it reads
  as a DECISION, not an oversight. If the composition is ever contested, the DR
  on a5a43395 (open-display-as-focal, display-against-a-view, cool-vs-warm
  balance) is the grounding lever to pull.
