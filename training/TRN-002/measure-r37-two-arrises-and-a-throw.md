# TRN-002 r37 — gate-23 items 2, 3, 4: one object deleted, one derived, one refused

Ordered under the owner's build law (dimension → objects complete → light). Camera unchanged
since r1 (`-4491, -7992, 1305`, yaw 20.0417°, f 38.841 mm). Every fit below is a sub-pixel
half-level crossing, back-projected on a NAMED plane, re-taken this round rather than inherited.

---

## สรุปสำหรับเจ้าของ

| item | ผล |
|---|---|
| 2 `desk_pier` | **ลบออกจากเฟรม** — วัดแล้วไม่มีขอบอะไรตรงเส้นฐานของมันเลย (16–21 L เทียบ 40–93 L ของขอบจริงในเฟรมเดียวกัน) |
| 3b `bed_headboard` สูง | **ได้มาจากการอนุมาน 882.95 มม.** (เดิม 915 พิมพ์ไว้) — fit rms **0.102 px จาก 48 คอลัมน์** |
| 3b(ii) ความหนาหัวเตียง | **วัดได้ 92.7 มม.** (สร้างไว้ 176 ซึ่งไม่มีการวัดรองรับเลย) แต่ **ยังไม่ใส่** เพราะมันตัดหน้าสัมผัสกับฐานเตียง |
| 3a `bench` ลึก 600 | **ปฏิเสธที่จะพิมพ์ตัวเลข** — ผ้าคลุมทับสันบนทั้งเส้น เส้นตรงที่ลากได้ fit ได้แค่ rms **11.56 px** |
| 4 `seg` | **craft_check เขียวครั้งแรกของเลนนี้** |

---

## 1. `desk_pier` — the foot line is not in the picture, at any strength

Its own `seen` has said *NOT FOUND at its built location* since r34, but that verdict was taken
at a position r35 later moved by 1.3 m — so it could have been the location and not the object.
**Re-tested at the current position.** Foot corners project to (109.5, 683.9) / (148.6, 680.9).

| column | strongest |step| in v 655..705 | at v |
|---|---|---|
| u=115 | 16.3 | 685 |
| u=122 | 19.4 | 695 |
| u=130 | 16.5 | 696 |
| u=138 | 15.9 | 697 |
| u=146 | 21.0 | 698 |

Every real boundary measured in this same frame this round runs **40–93 L** (headboard arris
55–70; the wood block at u=80 gives +93). The 16–21 L here is herringbone texture, and it does
not even fall at the foot line. **There is no contact there.**

R10 applies literally: *an object invented to satisfy a structure is a declared assumption*, and
the absent thing is honest where the wrong thing fabricates a reading. It is REMOVED — not
resized, not absorbed into a neighbour — and `declared_gaps.desk_pier` records what is now
missing (whatever carries the far end of the worktop) and what would reopen it.

## 2. `bed_headboard` — the height is derived, and the plane is a contact

    top arris    v = 0.121770 u + 395.663      rms 0.102 px over 48 columns (u 770..1010)
                 residuals −0.31 … +0.20 px

**Which arris it is, is geometry and not a reading.** The camera sits at z = 1305 and this top is
near z = 900, so the camera is ABOVE the top face; the upper silhouette can then only be the
**top-BACK** arris. That plane is x = −1314, which is itself a CONTACT (the front face of
`ward_band`, gap 0.0 mm, r34) — the one datum here not in question.

    z_top = 882.95 mm      sd 0.95 mm across the 48 columns      built 915 → **−32.1 mm**

Gate-23's per-column estimate of ~30–33 mm was made independently of this fit and agrees.

> **A first pass at this fit came back rms 1.93 px and was thrown away, not reported.** `argmax`
> of the column gradient swaps between the arris and a second line 3 px below it, so the "line"
> was two lines interleaved. The fix is a seeded half-level crossing inside ±7 px, and the
> tell was in the residuals: a sawtooth, not scatter.

## 3. The depth is MEASURED — and deliberately not applied

That second line is real: **v = 0.120410 u + 400.069, rms 0.348 px over 44 columns**, sitting
3.05–3.32 px below the arris. And the panel's near end shows the same pair standing up:

| line | fit | rms | rows |
|---|---|---|---|
| outer silhouette | u = −0.00245 v + 1028.504 | 0.174 px | 26 |
| inner arris | u = −0.01571 v + 1016.073 | 0.440 px | 26 |

(the outer fit reproduces r35's `u = 1027.62`; separation 20.05 px)

Read as the two arrises of one narrow face, they give **depth 92.7 mm** (end pair) and
**101.2 mm** (top pair). The end pair is **6.8× more sensitive per mm** — 0.216 px/mm against
0.032 — so it carries, and the top pair corroborates to within 0.25 px of its own noise. The
built **176 mm carries no measurement anywhere in its provenance.**

**It is not applied this round, and the reason is R9.** `bed_platform`'s head-end face is at
x = −1490, which is exactly this panel's front face: they are in CONTACT. Hold the back at the
wall and a 92.7 mm panel opens an **83.3 mm gap** between bed and headboard; hold the front at
the bed and the panel leaves the wall. The number is measured; **which contact survives is a
RELATIONSHIP nobody has declared**, and typing either coordinate is precisely the defect R9
names. Carried to r38 with the measurement already in hand.

## 4. `bench` — the refusal IS the measurement

600 mm has been an `A` since r1 and gate-23 booked it for this round. It cannot be closed from
this view, and the number that says so: of **59 columns** across the mass only **12** carry a
rise of ≥60 L, and a straight line through them fits to **rms 11.56 px** — two orders worse than
every fit this lane accepts (0.10–0.44 px). A woven throw is draped over the whole visible top,
so the top arris is not an image feature at all. Solving the depth from that non-line returns
**25.5 mm** for an ottoman, which is what a derivation from a non-line returns.

`why` now carries the declaration in the open, including what it costs: at 600 the far-top ridge
stands ~55 px proud at u=860, so **this declaration is known to be wrong in the direction of too
deep**. It reverses when the soft-goods lane builds the throw — *the object occluding the datum
is one we have not built yet.*

> **The gate caught the first cut of this edit.** Writing the refusal into `prov` while leaving
> 600 sitting in `s` is exactly the shape R10's corollary names, and `rule_gate` said so by name.
> The ottoman is not invented, so it does not belong in `declared_gaps`; what is assumed is one
> of its dimensions, and that is what had to be declared.

## 5. `seg` — green for the first time

`craft_check` has named these two every round since r34. `bed_platform` R=300 at 5.37 m and
`bench` R=200 at 3.49 m each need 8 segments per quarter and carried 6. Both set to 8:
**SILHOUETTE clean, exit 0** — the first round this lane's craft check has passed.

---

## What is closed, and what is not

**Closed:** items 2, 3b (height), 4. `rule_gate` reads *79 masses, all justified*, exit 0, with
the coverage ratchet, the R1 cap and the decision log all checked.

**Open, with numbers in hand:** the headboard's depth (a declared CONTACT decision, r38) and the
bench's depth (blocked on an object we have not built). **No render this round** — the same
reasoning as r36: two known geometry defects remain, and a full frame would spend an R1 cycle
photographing them.
