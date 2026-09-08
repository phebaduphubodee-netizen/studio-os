# TRN-002 r38 — the thickness goes in, and half the round is withdrawn before it ships

Ordered under the owner's build law (dimension → objects complete → light) and under his
instruction for this round: *"ประกาศหน้าสัมผัสหัวเตียง↔ฐานเตียง (เตียงตามแผง หรือแผงตามเตียง)
แล้วใส่ความหนา 92.7 ที่วัดไว้แล้ว"*. Camera unchanged since r1 (`-4491, -7992, 1305`,
yaw 20.0417°, f 38.841 mm).

---

## สรุปสำหรับเจ้าของ

| item | ผล |
|---|---|
| `bed_headboard` หนา | 176 → **92.7 มม.** (ช่วงที่วัดได้ 84–95) หลังตรึงที่ผนังไม้ x=−1314 |
| หน้าสัมผัสที่ประกาศ | **หลังแผงชนผนังไม้** · และที่นอนวางบนฐานเตียง |
| หัวเตียง↔แผง | **ถอนออกก่อนส่ง** — ตั้งใจเลื่อนเตียงตามแผง แต่**ถูกวัดหักล้าง** |
| หัวเตียงจริงอยู่ไหน | ด้านข้างเตียงวิ่งต่อเนื่อง**เลย −1406.7 ไปจนชนผนัง** ⇒ แผงน่าจะเป็น**แผงแขวนผนัง** |
| หัวเตียงในสเปกตอนนี้ | **ตรึงไว้ที่ −1490 และประกาศว่าผิด** พร้อมหลักฐานและงานที่ r39 ต้องทำ |
| กันเกิดซ้ำ | `spec["contacts"]` + `contact_check.py` blocking ใน `rule_gate` (ประกาศ 2 ข้อ) |

---

## 1. คำถามของรอบนี้ ไม่ใช่ตัวเลข แต่เป็นฝั่งที่ตรึง

r37 วัดความหนาได้แล้วแต่ใส่ไม่ได้ และเขียนเหตุผลไว้เอง: *"The number is measured; which
contact survives is a RELATIONSHIP that nobody has declared."* มวลสามก้อนมาเจอกันที่ระนาบเดียว
บางแผงโดยตรึง**หลัง** → เตียงเหลือช่องว่าง 83.3 มม. · บางแผงโดยตรึง**หน้า** → แผงลอยห่างผนัง
ทั้งสองทางคือการแก้ตัวเลขสามตัวเดียวกัน ซึ่งเป็นรูปของ R9 เป๊ะ ๆ: **พิกัดเก็บผลลัพธ์ ไม่ใช่
ความสัมพันธ์** รอบที่พิมพ์พิกัดฝั่งใดฝั่งหนึ่งลงไปจึงไม่ได้ตัดสินใจ — มันซ่อนการตัดสินใจไว้

## 2. THE PANEL'S SIDE: the wall contact holds, and it survived being attacked

**(1) The back plane is already load-bearing for two derived numbers.** r37's `z_top`
(882.95) is the top arris back-projected onto x=−1314, and r35's near end (y=−4555.1) is the
outer silhouette back-projected onto the same plane. Measured this round, moving the panel
off the wall costs both:

| held | z_top | near end | panel length | panel stands off the oak |
|---|---|---|---|---|
| **back on the wall (adopted)** | 882.95 | −4555.1 | 2005.1 | 0.0 mm |
| front on the bed | **894.23** (+11.28) | **−4645.4** (−90.3) | **2095.4** | **85.8 mm** |

**(2) 176 mm is dead, and the argument that kills it is the SEPARATION, not an absence.**
The two visible lines on the near end are **18.5 px** apart and the top pair **2.95–3.66 px**,
where 176 mm requires ~38 px and 4.8–6.6 px — wrong by a factor of two, at fit rms
0.24–0.35 px.

> **The round's first argument for this was different and it was wrong.** It said 176 is
> *"refuted by absence"*: at u=989.27, where 176 puts the front arris, the strongest step over
> 101 rows is 2.9 L against 2.4–3.1 L of flat field. An adversarial pass ran the same
> statistic across a **same-frame, same-class control** — the bed plinth's own 90° vertical
> corner, white upholstered fabric meeting white upholstered fabric — and a corner that
> indisputably exists scores **3.50 L**. Under this room's flat light the panel's two faces
> differ by 0.8 L, so no corner on this object can make a step at any radius. **The absence
> test measured the lighting, not the geometry.** The conclusion is unchanged; the argument
> that reaches it is now the separation, and the absence sentence is out of the spec's
> permanent provenance. An absence is evidence only with a positive control beside it.

## 3. The number is HELD at 92.7, and here is the band it sits in

Both near-end verticals were re-fitted independently this round, with a different estimator
from r37's (gradient-peak parabola for the step, darkness-weighted centroid for the welt):

    outer silhouette   u = -0.00344 v + 1029.141    rms 0.371 px    101 rows
    welt line          u = -0.00794 v + 1012.871    rms 0.270 px    101 rows

    depth  87.1 mm (welt centre)   84.0 mm (welt's left flank)   92.7 mm (r37)
    a third party's independent fit of the same pair: 85.3 mm

and the top pair, re-fitted the same way, reproduces r37 where it is strong:

    top arris   v = +0.122656 u + 394.715   rms 0.105 px   61 cols
    -> z_top on x=-1314 = 883.56 mm, against the 882.95 r37 derived — 0.61 mm apart

**So the depth is 84–95 mm and the entire spread is the welt bead's own width (~9 mm ≈ 2 px
at 0.216 px/mm).** 92.7 is inside it and is the value of record; re-typing it inside a
feature's own width is how a number drifts.

> **The competing reading is NOT closed, and the round's first attempt to close it was
> mis-framed.** r35 read the u≈1008 line as *"an inner piping line"*. The write-up argued that
> one border cannot be 102 mm from the end and 0 mm from the top — but that compares a
> distance in **y** against a drop in **z**. Measured consistently, as a distance from the
> BACK plane, both lines sit ~85–102 mm in, which is self-consistent for a border seam on a
> 176 mm panel. What actually kills 176 is §2(2). What distinguishes "welt on the arris" from
> "border seam inboard of it" is craft, not pixels: upholstery welts sit at arrises, and the
> plinth in this same frame shows exactly that idiom. **That is a plausibility argument and it
> is labelled as one.**

## 4. THE BED'S SIDE: withdrawn, and the instrument that refuted it was ours

The round's first cut moved both bed head faces to the panel's front face (−1490 → −1406.7)
and declared the two joints as blocking contacts. **An adversarial pass refuted it, and the
refutation reproduced here on the first attempt.**

The instrument is not new. r16 fitted the plinth's near-side **base contact (z=12)** and its
**top arris (z=221)** to fix the bed's near face at y=−4180 — **at the foot.** Nobody had ever
run those two lines toward the head. Run out column by column and back-projected:

| u | 800 | 840 | 880 | 920 | 940 | 960 | 980 |
|---|---|---|---|---|---|---|---|
| y on z=12 | −4183 | −4198 | −4184 | −4181 | −4183 | −4234 | −4193 |
| contrast | 31 L | 92 L | 100 L | 88 L | **61 L** | 142 L | 132 L |
| y on z=221 | — | −4177 | −4170 | −4171 | −4169 | −4179 | −4179 |
| x reached | −2053 | −1886 | −1693 | −1502 | −1408 | −1353 | −1220 |

**The bed's near side is continuous past x = −1406.7, out to x ≈ −1220…−1300 — the wall.**
And the round's own §2 statistic, turned on the round: at u=939.74, where a head face at
−1406.7 must cut that line, the median strongest step is **4.0 L** against 3.0–4.0 L of flat
field. Nothing is there, by the very test the round had used to kill the 176.

**What it implies, and what is left open:** the base runs to the wall, so the upholstered
panel is **wall-hung above it** — which would also explain the one number nobody has ever
measured about it, `bed_headboard`'s bottom, typed z=0 since r1. That is not closed here. The
two lines wobble past u=960 (y −4234) and a terminus needs its own fit.

**So the bed does not move.** Both head faces are HELD at −1490 with a `why` carrying the
measurement, its cost (short by roughly 200–280 mm, now a *measured* error rather than an
unexamined one), and the fit r39 owes. Holding a contested number rather than improving it
toward −1290 is deliberate and is this lane's own idiom — r37 did exactly this for the
bench's depth: **a number under active contest may not drift while it is undetermined,
because the round after next cannot tell a correction from a guess.**

## 5. The corroboration that was quoted and is now withdrawn

The first cut also offered: hold the mattress's measured foot, put its head on the panel, and
it comes out 1987.3 mm — 7.3 mm from a manufactured 1980. **It is worthless as evidence and
the adversarial pass showed why, four ways:**

* the premise is false by our own vault file — Panero & Zelnik, already in `knowledge/`:
  bed 1905 mm = 75 in, so the value it replaced (1904) is **1.0 mm** from a standard length;
* it cannot fail — across the round's own 84–95 mm bracket the length runs 1984.9–1996.0 and
  **three of the four bracket values score better than the adopted one**;
* it prefers the rejected branch — leave the bed alone and 1904 is 1.0 mm from 1905;
* base rate — over a plausible 1850–2050 window, a two-size list at ±13 mm passes 23% of all
  lengths, the fuller list 51%.

And the sibling axis refutes the object anyway: the same mattress is **1719 mm** wide, 111 mm
from the nearest size anyone sells. The claim is out of the spec's provenance and out of the
contact register's `why`.

## 6. What stops the register itself from lying

`placement_check.py` reads the BUILT scene and cannot see this defect class: a bed and a
headboard 83 mm apart in x are **both standing on the floor** — neither floats, neither
overhangs, neither is tipped, and a gap is not interpenetration. Its own docstring asks for
the missing piece by name. So r38 adds `spec["contacts"]` + `contact_check.py`, blocking in
`rule_gate`: two faces on one axis, at the declared `gap_mm`, with the masses not overlapping
along that axis and **overlapping on the other two** (coplanar faces that never meet are a
contact in name only). Every row carries a `datum` naming the side that does not move.

**Two joints are declared, not four — and that is the register proving its own point.** The
two it was built for were refuted before they shipped. Had they gone in, a false relationship
would have been enforced as blocking law, which is strictly worse than leaving it undeclared.
*A register makes a claim checkable; it does not make it true.*

Advisory, one line, in the gate's own output: the geometry contains **46** vertical butt
joints and **1** carries a row. That hole is reported rather than closed — 45 of them are wall
and millwork joints no round has had a reason to reason about, and a gate that failed on all
of them would be muted inside one round.

## 7. Frame of record

Playblast first (R5), then full fidelity. **Two full frames this round**:
`trn002_mat_r38.png` (the withdrawn variant, kept because its critique bundle is triaged) and
**`trn002_mat_r38b.png`, the frame of record.** Placement gate **92 objects, 0 FAIL** on both.
Metric of record **n=22, mean 0.10 px, median 0.06, max 0.66** — unchanged, as predicted,
because every bed landmark in that table sits at the foot.

Measured on the frames, one operator on both (gradient-peak parabola, v 525..625):

| feature | target | r38 built | r37 built |
|---|---|---|---|
| near-end silhouette | u = 1027.17 (sd 0.38) | **1027.07** (sd 0.11) | 1027.62 |
| near-end front arris | u = 1008.99 (sd 0.71) | **1006.66** (sd 0.12) | **989.27** |

The panel's front arris was **19.04 px** from the target's line and is now **0.75 px**
(projected), 2.33 px measured frame-to-frame. That residual is the round's honest loose end:
read as a width our rim is 20.41 px against the target's 18.18, i.e. about 10 mm proud,
pointing at the LOW end of the bracket. It cannot be settled from this pair, because the
target's line is the crest of a welt bead and ours is a bare geometric corner — **the two
operators are not measuring the same kind of thing.** Modelling the welt makes it
like-for-like, and it is in the queue.
