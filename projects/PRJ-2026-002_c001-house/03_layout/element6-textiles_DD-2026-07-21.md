# Element 6 — Textiles DD: casement sheers + ผ้าห้องน้ำ (2026-07-21)

**Provenance.** Workflow `element6-textiles-dd` wf_565485c7-985 — 9 agents (4 vault/repo
ground → 1 decide → 3 adversarial verify (coherence / ink+scope / buildability) → 1
omission critique). Core verdicts: **0 REFUTED**; every AMEND is applied in the text
below and marked `[AMENDED]`. Vault-first: **no fresh NLM DR** — vault + repo precedent
sufficed for this scope (the E2 pattern, recorded as a decision); every un-vaulted call
ships [est] / GAP / still_owner. Scope is deliberately SMALL: bedroom casement sheers,
the ensuite-casement fabric question, towels, bath mat. Nothing else. (Watch-item
answered: e4→e5 DD grew 14→37 agents; e6 = 9.)

Companion machine manifest: `element6-textiles_dd-decisions.json` (identity-only probes,
the director-review fix-b shape — first DD to carry one; pure pytest gate = follow-on).

---

## D-E6-1 — Bedroom casement sheers (glz-west-win1/2): inside-reveal flat sheers, suite sheer family, α 0.38, sill-length, drawn-only

**FORM:** inside-reveal flat sheer panels, one per casement, concealed slim rod at the
head INSIDE each punched reveal — NOT wall-track panels. (a) No ink pocket exists at the
casement band (the 250 pocket is glass-L-only; the dashed track L ends y2600); (b) wall
panels would stack over the flanking opal strips / cool mirror pier; (c) curtains.py
cannot express these windows — extending the west leg matches 3 coplanar x0 glass runs
(gaps 2447.4/1501.3 mm ≫ TOL_JOIN 25) → RAISE at curtains.py:273-275, z is hardcoded
floor-to-ceiling (:391-392, sill/head never read), and any extension re-derives the
BUILT west blackout's park zone; (d) punched windows in masonry are a different species
from the floor-to-ceiling glass-L. → **NEW pure module** (casement_sheers.py), not a
curtains.py extension.

**FABRIC + TONE:** join the suite's ONE sheer identity — the same `curtain_sheer`
material BY NAME, cool off-white linen-look, sheer_rgba [0.85,0.84,0.82] (composition,
not SKU), a hair off the plaster value so weave texture + self-shading make it read as
fabric (S12 Albers ground-subtraction: the sheer joins the 60% cool ground, oak keeps
its 30%; no new family, D1-A intact). SKU lane note (still_owner): mildew-resistant
synthetic with linen LOOK (tropical vault guidance); BSDF rough 0.75 / IOR 1.5 /
sheen 1.0 / sheen-rough 0.4-0.6.

**OPACITY:** α = 0.38, EXACTLY the built east sheer (`render_state.sheer_alpha`,
validated 0.05-0.9) — one sheer transmission suite-wide; PH-02 proven at this value.

**DROP:** sill-length — head 2200 down to ~15 mm above sill 1000 (all z [est]
render-tier). A longer drop dangles into the makeup zone above the h750 BF11 and adds
fabric mass to the pier composition. `[AMENDED — confrontation]` The vault carries a
contrary row: `knowledge/rendering/cycles-lighting-camera-presets.md:265` "Curtains:
floor-to-ceiling sheer or linen, required where windows exist" (verbatim in the cited
NLM table L102). It is REFERENCE-tier, NOT-WIRED, a living-room scene-dressing
candidate; the glass-L already gives the suite its floor-to-ceiling read; punched
casements over a h750 vanity are the argued exception — owned here as a design call.
(For D-E6-2, D-E4-1 outranks the same row.)

**RENDER/STATE — drawn-only `[AMENDED]`:** both sheers DRAWN. The casement block is
**drawn-only and RAISES on `parked`** until a park is designed: the east park derivation
(largest off-glass remainder) cannot exist inside a ~600 reveal whose rod spans only
glass — park would be None by construction; any jamb stack eats the ~500 clear core.
**No blackout at glz-west-win1/2 — recorded** (anti-reopen; the east glass-L carries the
suite's blackout; night privacy at the makeup zone = still_owner). **The mirror pier is
BARE — recorded:** no fabric, no holdback/tie-back hardware (brass holdbacks would also
violate no-brass-at-any-mirror).

**E5 posture respected verbatim:** D-E5-4 delivered the mirror face band with BARE
casements and leans on nothing here; these sheers are the declared E2 follow-on (win1's
spec note) that SOFTENS the backlight; no lumen derivation is re-run (sheer transmission
= declared vault GAP).

Grounding: spec.json:95-96 (win1/2, follow-on note), :144-149 + build_room.py:1043-1061
(sheer_rgba/α/`curtain_sheer` by name), :138 (still_owner boundary), :38 + :198 (the E2
follow-on + BF11 design origin); element2-west-wall_BUILD-2026-07-17.md (sheet draws
curtains here; BF11 x306 w498 h750; mirror 1400×700 on the pier);
element5-lighting_DD-2026-07-20.md:116-122, 254-255, 277 (bare-casement delivery, §10.5
hold-open, NOT-claimable); curtains.py:110-121, 264-308, 388-393 (incapacity, verified
live); knowledge/styles/color-composition.md#L312-L339 (S12), #L178-L195 (weave/
imperfection); knowledge/_inbox/nlm-element1-curtain-2026-07-16.md#L55-L69, L102-L103;
knowledge/materials/residential-materials.md#L149-L157 (mildew);
knowledge/materials/texture-sets-discord.md#L170-L178 (fabric BSDF);
knowledge/rendering/cycles-lighting-camera-presets.md:265 (the CONFRONTED contrary row).

[est]: sill 1000 / head 2200 (all four casements — owner/arch-plan), hem sill+15,
rod offset ~50 room-side of glass (vault GAP), fullness ~1.8× flat micro-wave (vault
GAP), BF11 498-vs-600 depth unresolved (moot for sill-length; recorded).

## D-E6-2 — Ensuite casements (glz-ensuite-win1/2): BARE — decided (CONFIRMED)

No sheer, no blind, no fabric — closes E5 §10 item 5. (1) BOTH casements sit fully
inside the shower spray enclosure (x55-1125 y7320-8596 vs win1 y7370.6-7872.0, win2
y7919.7-8421.2 — verifier: win2 is also fully inside, strengthening the call); no vault
file rates ANY textile for wet/spray zones, and the microcement DRY-only precedent (e4
DD §3) applies a fortiori to fabric. (2) D-E4-1: the garden through these black-alu
casements is the wet-side COHERENCE CARRIER — fabric removes the mechanism the
reverse-Albers scheme leans on. (3) Privacy is routed to GEOMETRY, not fabric: the
raised-sill question stays owner (spec win1 note; e4 DD §8 Q3 — cite both: Q3's literal
wording is z-for-framing/waterproofing). **Honest tier:** vault-CONSISTENT but
un-CITED (no document rates wet-zone textiles either way) — a design call this DD owns.
Build phase writes `D-E6-2 DECIDED BARE` onto BOTH opening copies (envelope :97-98 AND
subroom :218-219) + the ensuite story bit gains the anti-hallucination line (a Gemini
shower-curtain is the only revert channel — no build lane creates fabric there).

Grounding: spec subrooms[ensuite].openings + room.openings:97-98; e4 DD §2/§3/§8 Q3;
docs/strategy.md:1875-1878; e5 DD:254-255; material_presets.py:587-621 (ensuite bits) —
`[AMENDED citation]` the windows-as-luminance-point support lives in
lighting_story_bits (:624-638), not the ensuite bits; residential-materials#L153-157
(nearest datum, drapery tier). [est]: sill/head on both (privacy geometry rides on
unconfirmed z).

## D-E6-3 — Towels on the LOCKED Purist -2MB set: bar at shower exit, jamb hooks, greige-oatmeal terry `[AMENDED]`

Schedule used EXACTLY as its three accessory rows stand — **no new rows, no towel ring**
(a ring reopens the one-PO/one-batch residual 5; the 18in K-14435-2MB is named INSIDE
row 4, so falling back is variant selection, not a schedule edit). Assignment (walls in
words; every position/AFF [est] render-tier):

- **K-14436-2MB 24in towel bar** → WEST wall x55, the ~680 segment between WC north
  (y6640) and shower curb (y7319.8) — within reach of the shower exit, serves shower AND
  tub. Carries 2 folded-over BATH towels. AFF 1100 [est]. Purist post/escutcheon end
  clearance vs 680 unverified (no cut-sheet) → 18in fallback within the locked row.
- **K-14443-2MB robe hooks ×2** → the east/party-wall door-jamb strips. SOUTH jamb
  (y5897.8-6596, beside the east basin) = the basins' HAND-TOWEL point (the no-ring
  answer; +1 hand towel folded on the Caesarstone between the basins — soft goods, no
  hardware). NORTH jamb (y7596+, fronting the tub-deck east end) = ROBE — **double-hung
  ×2 robes [est]** (2-person suite, 2 hooks total, one on towel duty — recorded, not
  silently absorbed). AFF 1650 [est]. `[AMENDED — named gap]` both jamb strips inherit
  the UNRESOLVED slide-vs-pocket door (e4 §8 Q1): a pocket outcome makes one strip a
  thin pocket skin — hook fixing/backing = constructability gap; render unaffected (the
  drawn leaf sits on the wardrobe-bay face).
- **K-14377-2MB paper holder** → `[AMENDED — collision fix]` the drafted band (beside
  the WC, y6031-6640, AFF 650) lands ON the built cistern massing (bathroom.py
  toilet_parts tank x55-255, y~6080-6591, z0-800). Re-sited: WEST wall immediately
  NORTH of the WC, band y~6640-6900, AFF 650 [est] — clear wall, seated-reach, below
  the bar's AFF-1100 line. (Placement mildly exceeds "towels+mat" but stays within the
  LOCKED accessory set — recorded.)

NOT used: the south mirror wall (mirror + task bar occupy it; the x77-1077 ledge strip
is bare but no row targets it), the frameless glass (nothing drilled or draped), the
shower interior west wall (casements + the ≥1829 tanking band). DD §7's niche
towel-shelf stays [GAP], not designed here (an oak shelf would fight the ~6% arithmetic).

**TEXTILE + TONE:** towels EXTEND the suite's one textile family into terry —
greige-oatmeal matching D3-1/D3-2 stonewashed linen ("element 3+'s ผ้า starts here").
RGBA [est] composition-not-SKU; fibre/GSM/SKU still_owner (vault has NO bath-linen
guidance — extending the family to terry is itself an un-cited design call, owned).
Light neutral joins the 60% cool ground; the oak vanity stays the room's ONLY warmth;
NOT cream (the family's explicit rule); hardware = existing satin_brass #C4A45C
identity inside the locked 10%.

**Towel census (spec data, one source for emitters + story bit + LOOK):** bath ×2
(bar) · hand ×1 (south hook) + ×1 (folded, counter) · robe ×2 (north hook, double-hung)
· mat ×1 (D-E6-4).

Grounding: PURIST schedule rows 4-6 verbatim + residual 5; spec subrooms[ensuite]
fixtures/openings + door rect (segment arithmetic reproduced independently by 2
verifiers: door jambs 6596/7596 → 698 S / 1000 N; WC 6031+609=6640 → curb 7319.8 =
679.8); e4 DD §7 (AFF = [GAP]; towels-450 = casework §2.1/§2.2 datum);
knowledge/ergonomics/bathroom-kitchen-planning.md L32-34 (tanking ≥1829 excludes
in-shower hardware — no statutory smuggle); material_presets.py:198-203, :311
(satin_brass), :580-583 (NOT-cream — `[AMENDED citation]` items[stool], not
builtins[stool]), :587-621 (only-warmth); e3 DD §4 D3-1/D3-2;
color-composition#L47-L71 (60-30-10).

## D-E6-4 — Bath mat: greige-oatmeal flat mat at the shower entry gap, in the drawn dry strip `[AMENDED]`

ONE flat mat, greige-oatmeal, same one-textile family (RGBA [est]; SKU still_owner);
fibre = terry/poly blend with solution-dyed synthetic content (the SAME
residential-materials#L149-152 line that chose the rug's poly-wool). WHERE: in the
DRAWN dry strip (D-E5-8's own floor, vanity front y6577 → curb y7319.8/partition
y7329 — ~743 deep; the ink-read ~680 CIRCULATION strip y6640-7320 is a different,
narrower zoning band — not transplanted `[AMENDED]`), centered on the shower entry
gap, long axis E-W at the curb, ~500×800×20 [est]. It lives in the walking strip by
geometry (the only dry floor there) — kept small and single. **Entry-gap provenance
`[AMENDED]`:** the gap is NOT ink — it derives from bathroom.py:155-165 shower_parts
(`screen_w = W*0.55` → screen x55-643.5, entry ≈ x644-1125), a CONVENTION-tier build
constant; the build must DERIVE the mat centre from the built gap (screen end → shower
east edge), never hardcode x644 (a screen_w nudge would silently strand the mat — the
decided-data-through-swallows class). **Tub-wash claim DELETED `[AMENDED]`:** the
drafted "mat sits under the tub wash" is FALSE — element5_lighting.py:408-432 aims both
cones at x1625/x2625 into the tub; the mat (x~484-1284 at the curb) is outside both. No
pooling exists; a generic mat LOOK check stays, un-anchored to the wash. **Tub-exit
recorded:** the mat serves the SHOWER entry only; a tub bather steps onto the bare
drawn dry strip [est] — decided, not implied. Anti-monopoly: greige joins the cool 60%,
zero warm mass, MAT not rug (the bedroom's poly-wool herringbone keeps the suite's
textile-floor role), NOT cream.

Grounding: spec lighting.accent.tub_wash note (D-E5-8 drawn dry strip); e4 DD §1
(strip bounds); bathroom.py:155-165 (screen fraction — the corrected citation);
element5_lighting.py:408-432 (the refuted-pooling check); e3 DD §1/§4 D3-5;
residential-materials#L149-152; color-composition#L47-L71;
material_presets.py:580-583, :587-621.

## D-E6-5 — Wet/dry textile law (one line, recorded)

**No textile enters the wet zone.** No in-shower towel, nothing draped over the
frameless glass or the tub deck/edge, no fabric at the ensuite casements (D-E6-2).
D-E6-3/-4 each imply it; this line states it once and arms the story bit against the
Gemini towel-draping trope ("no towel over the glass or tub edge").

---

## Render state

Bedroom vanity/hero frames: glz-west-win1/2 softly veiled by DRAWN sill-length sheers
at α 0.38 — garden still the brightest plane, flanking opal strips + mirror pier fully
unoccluded (PH-02). Ensuite frames: both casements BARE with the garden read (the
wet-side coherence carrier); greige-oatmeal terry on the west-wall Purist bar + south
jamb hand-towel hook, robes on the north jamb; the single greige mat flat at the shower
entry gap in the drawn dry strip; lamps dim beneath the windows. (No mat-under-wash
claim — deleted per verify.)

## Build consequences (the anti-omission enumeration — build follows this list, and this list only)

1. **NEW pure module `casement_sheers.py`** (curtains.py MUST NOT be extended: 3-run
   match → RAISE; park re-derivation would move the built west blackout). Reads opening
   rect + sill_mm/head_mm; z = sill+15 → head (NOT floor-to-ceiling); declared
   constants beside the module (HEM/TOP pattern, honest [est]).
2. **NEW spec block `casement_sheers`** on glz-west-win1/2: form=flat_inside_reveal,
   reveal offset [est], per-window state `drawn` ONLY (parked → RAISE until a park is
   designed). α source = `spec.curtains.render_state.sheer_alpha` (ONE source of
   truth) — a CROSS-BLOCK dependency: fail-loud read + its own pin test (a spec that
   drops/renames the curtains block must RAISE, not strand the sheers). Unknown window
   id → RAISE; α bounds 0.05-0.9 (build_room:1054-1060 pattern). Data + consumer land
   in the SAME commit (the curtain no-consumer lesson).
3. **`_add_casement_sheers` in build_room**, mirroring `_add_curtains`: pure layout in
   the module, build_room extrudes ribbons + assigns the EXISTING `curtain_sheer`
   material BY NAME. **Ordering + existence:** the material is created only inside
   `_add_curtains` after its empty-ribbons early-return (:1037-1039, :1061) — run
   AFTER it and RAISE if `curtain_sheer` is absent (get-or-create would fork a second
   sheer identity). **`obj["ph_model"]=True` on every ribbon** (without it,
   `_bevel_edges` shreds the open ribbon — :273; the reason _add_curtains sets it).
   Match the east system's `--hero` skip explicitly + test it.
4. **Sheers story bit**, spec-gated on the new block, **WIRED into material_story()**
   (hand-append at material_presets.py:665-667 — an un-called bit function is silent):
   cool off-white linen-look sheers inside the two west casement reveals, α 0.38, join
   the plaster ground; garden windows stay the brightest source; opal strips never
   occluded; **no fabric on the mirror pier**. Gating test asserts through
   material_story(canonical spec) (the :573-583 pattern).
5. **ensuite_material_story_bits update ×2** (gate the BARE line on the ensuite
   subroom + its openings existing): (a) "both shower casements BARE black-alu — garden
   through them is the coherence carrier, NO curtain/blind/fabric"; (b) towels/mat:
   "greige-oatmeal terry on satin-brass Purist bar/hooks + single greige mat at the
   shower entry; the oak vanity stays the room's only warmth; **no towel over the glass
   or tub edge**" (D-E6-5). LOOK: greige must not read CREAM under the 2850K lamps
   (NOT-cream is tonal).
6. **Spec notes**: `D-E6-2 DECIDED BARE` appended to BOTH copies of
   glz-ensuite-win1/2 (envelope :97-98 AND subrooms :218-219) — inert anti-reopen data.
7. **bathroom.py accessory emitters** (constants beside the fixtures they serve,
   MIRROR_SILL pattern): towel_bar (610/457 on 2 posts, mat `brass`), robe_hook ×2
   (`brass`), paper_holder (`brass`, at the RE-SITED y6640-6900 band), draped towel
   masses (bar + south hook), folded hand towel (counter), bath_mat slab — textile
   parts all mat **`towel`** (ONE shared token for towels AND mat — two tokens double
   the router work; decided). Census from spec data (D-E6-3), one source.
8. **DISPATCH lane DECIDED: spec-gated accessory DATA on a new bathroom.py kind**
   (the taskbar-gate template :102-113). Fail-loud everywhere: unknown wall key →
   RAISE; missing AFF → RAISE or DECLARED [est] constant; **accessory-shaped data that
   routes to zero parts → RAISE** (bathroom.fixture_parts returns [] for unregistered
   kinds and build_suite's else-branch silently masses a white fix__ box — the swallow
   is real, build_room.py:2367-2370); canonical-spec test pins non-empty parts.
   Textiles ride as FIXTURE PARTS, not spec items (curtains._obstacles excludes rugs;
   _add_rug forces herringbone — the item lane is wrong; UNAPPLIABLE_KINDS refusal
   test pins the moot-ness).
9. **The `towel` token needs ALL THREE router branches** (the buildability verifier's
   catch — the closed fixture_part_name gate is one layer UP and does NOT protect
   these): (a) FIXTURE_MAT_OBJECT row `'towel': 'mill__{b}__towel'`; (b) a
   **mill_object_role branch** — that router still ends `return "oak"`
   (material_presets.py:296) and build_room maps unknown roles to WALNUT via
   `.get(_role, mill)` — a row alone ships every towel in oak veneer with NO raise;
   (c) the build_room role-dict entry + the terry material itself. **Terry material
   lives in `_suite_materials`** (blackalu/opal precedent — bathroom.py is PURE, part
   dicts carry no rgba; "color inside the builders" is unimplementable): greige-oatmeal
   RGBA [est], rough ~0.9, fabric sheen. Brass parts ride the EXISTING brass row — no
   new brass material.
10. **Tests**: casement_sheers pure layout (z from sill/head, RAISE paths), accessory
    emitters (brass + towel routing end-to-end, RAISE paths, census parts exist —
    hardware succeeding with zero soft masses must fail), fixture_part_name accepts
    `towel` + still RAISES others (**remove 'towel' from the raises-list
    test_material_presets.py:566 — its red test is the forced touch-point; add the row
    to the HAND-LISTED coupling loop :550-559**), canonical-FILE test for the new spec
    blocks, story-bit gating, `--hero`, cross-block α pin, ph_model pin, **the existing
    curtain tests run UNMODIFIED** (proves the east system untouched).
11. **Eye/LOOK**: (a) vanity/west cams — sheers must not occlude strips/pier (disjoint
    by construction: reveals y2898-3498/y4999-5599 vs strip centres y3523.7/y4974.3 —
    but verify by PROJECTION, not axis arithmetic) + PH-02 ordering with veiled
    casements (never rendered); (b) the west-wall bar at x55 is BEHIND the
    ensuite_mirror cam → new/shifted `in_subroom` eyecam variant to see bar + hooks +
    mat (clearing >0.35 m obstacles); (c) generic mat LOOK (no wash anchor); (d)
    paper-holder clear of the cistern.
12. **UNTOUCHED**: E5 (no lumen re-derivation — sheer transmission is a vault GAP;
    lighting_story_bits unchanged); the east curtain system (track, park zones, pocket
    250, blackout-parked); the Purist schedule FILE (18in fallback = spec data, not a
    schedule edit); no statutory values (wet IP / IEC-701 / RCD / membrane / DCOF /
    accessibility stay GAP — nothing here goes inside the shower anyway).

## GAPs / still_owner (held honest)

- Sill 1000 / head 2200 on ALL FOUR casements [est] — sheer drops + ensuite privacy
  geometry inherit the flag until owner/arch-plan confirms.
- Ensuite privacy (raised sill, e4 §8 Q3) = OWNER; BARE doesn't answer it; the answer
  is sill/glazing, never wet-zone fabric.
- The BARE ruling: vault-consistent, un-cited (no wet-zone textile rating exists either
  way) — a design call this DD owns.
- Towel-bar/hook/holder AFFs: NO vault value (e4 §7 [GAP]) — all [est] pending owner.
- Purist end clearance vs the 680 segment: unverified (no cut-sheet) — 18in fallback.
- No towel ring in the locked schedule — hand-towel point = south hook + counter
  staging; a ring = schedule change = owner's call.
- Bath-linen guidance (fibre/GSM/tone) + mat sizing: NOT IN VAULT — [est] +
  still_owner; the linen→terry family extension is an owned un-cited call.
- Curtain CONVENTION GAPs carry over unchanged: fullness, carrier spacing, hem gap,
  rod-to-glass offset, sheer transmission BSDF.
- BF11 498-vs-600 depth: still open with the designer (moot for sill-length).
- Slide-vs-pocket door (e4 §8 Q1) → jamb-hook fixing/backing constructability gap
  (named, render-safe).
- Towel shelf + shower niche: NO geometry anywhere — folded-towel storage undesigned;
  any future shelf must fight the ~6% warmth arithmetic first.
- Sheer/towel SKUs, rod hardware + cross-section, true mounting heights = still_owner
  (spec:138 boundary unchanged).

*Refs: workflow wf_565485c7-985 (journal in session transcript dir);
master-suite.CANONICAL.spec.json; element2/3/4/5 DD+BUILD docs;
element4-ensuite_ffe-brass-schedule-PURIST-2026-07-20.md; curtains.py; bathroom.py;
element5_lighting.py; material_presets.py; knowledge/styles/color-composition.md;
knowledge/materials/residential-materials.md, texture-sets-discord.md;
knowledge/ergonomics/bathroom-kitchen-planning.md;
knowledge/rendering/cycles-lighting-camera-presets.md;
knowledge/_inbox/nlm-element1-curtain-2026-07-16.md.*
