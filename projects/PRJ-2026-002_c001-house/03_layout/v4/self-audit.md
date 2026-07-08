# self-audit -- PRJ-2026-002_c001-house

**doubt-score 1291**  (31 open, 0 owner-resolved)  CRITICAL 1 · HIGH 1 · MEDIUM 18 · LOW 11

> The doubt-score reads meaningfully ONLY with the coverage line below: a low score under thin coverage means *did not look*, not *clean*.

## Ranked doubts (where I am least certain, worst first)
1. **[CRITICAL] semantic_change_unexplained** @bedroom_suite — ม้านั่งปลายเตียง (bench): facing REVERSED rot 180 -> 0 (delta 180 deg) between rounds, UNSIGNED  (flag-confidence 0.9)  [ม้านั่งปลายเตียง (bench)]
   - why: the rebuild re-derived this piece's facing from geometry and reversed a direction the prior round had with NO owner signature covering the new orientation -- the placement gate cannot see facing, so this is exactly the class of silent regression that slips
   - resolve: confirm the correct facing on the sheet and sign it (confirmed_rot); if the prior round was right, restore that rot
2. **[HIGH] semantic_change_unexplained** @sitting_room — โต๊ะวางกล้วยไม้ (console): identity changed kind 'cabinet' -> 'console' between rounds, UNSIGNED  (flag-confidence 0.9)  [คอนโซล+กล้วยไม้ BF12-2.70x40x280, โต๊ะวางกล้วยไม้ (console)]
   - why: the rebuild re-labelled what this piece IS with no owner signature covering the new kind -- identity is owner-layer truth, so a machine re-identification between rounds is a possible silent regression
   - resolve: confirm the piece's identity on the sheet and sign it (confirmed_kind); if the prior round was right, restore that kind
3. **[MEDIUM] kind** @bedroom_suite — kind='tv_console' on 'ตู้ทีวีสูง ผนังตะวันตก' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [ตู้ทีวีสูง ผนังตะวันตก]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
4. **[MEDIUM] kind** @bedroom_suite — kind='shower' on 'ฝักบัว (shower)' [ห้องน้ำในตัว (ensuite)] shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [ฝักบัว (shower)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
5. **[MEDIUM] kind** @bedroom_suite — kind='bench' on 'ม้านั่งปลายเตียง (bench)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [ม้านั่งปลายเตียง (bench)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
6. **[MEDIUM] kind** @bedroom_suite — kind='vanity_double' on 'อ่างล้างหน้าคู่ (ในห้องน้ำ)' [ห้องน้ำในตัว (ensuite)] shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [อ่างล้างหน้าคู่ (ในห้องน้ำ)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
7. **[MEDIUM] kind** @bedroom_suite — kind='bathtub' on 'อ่างอาบน้ำ (bathtub)' [ห้องน้ำในตัว (ensuite)] shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [อ่างอาบน้ำ (bathtub)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
8. **[MEDIUM] kind** @bedroom_suite — kind='armchair' on 'เก้าอี้ทำงาน (หันเข้าโต๊ะ W)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [เก้าอี้ทำงาน (หันเข้าโต๊ะ W)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
9. **[MEDIUM] kind** @bedroom_suite — kind='bed' on 'เตียง 7'x6.5' หัวตะวันออก' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [เตียง 7'x6.5' หัวตะวันออก]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
10. **[MEDIUM] kind** @bedroom_suite — kind='side_table' on 'โต๊ะข้างเตียง เหนือ (มีโคมไฟ)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โต๊ะข้างเตียง เหนือ (มีโคมไฟ)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
11. **[MEDIUM] kind** @bedroom_suite — kind='side_table' on 'โต๊ะข้างเตียง ใต้ (มีโคมไฟ)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โต๊ะข้างเตียง ใต้ (มีโคมไฟ)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
12. **[MEDIUM] kind** @bedroom_suite — kind='toilet' on 'โถสุขภัณฑ์ WC' [ห้องน้ำในตัว (ensuite)] shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โถสุขภัณฑ์ WC]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
13. **[MEDIUM] kind** @sitting_room — kind='armchair' on 'เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
14. **[MEDIUM] kind** @sitting_room — kind='armchair' on 'เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
15. **[MEDIUM] kind** @sitting_room — kind='sofa' on 'โซฟา 3 ที่นั่ง' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โซฟา 3 ที่นั่ง]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
16. **[MEDIUM] kind** @sitting_room — kind='side_table' on 'โต๊ะกลม (ข้างโซฟา)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โต๊ะกลม (ข้างโซฟา)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
17. **[MEDIUM] kind** @sitting_room — kind='side_table' on 'โต๊ะกลม (ระหว่างเก้าอี้)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โต๊ะกลม (ระหว่างเก้าอี้)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
18. **[MEDIUM] kind** @sitting_room — kind='console' on 'โต๊ะวางกล้วยไม้ (console)' shipped as certain, but hand-typed identity, no owner sign + no prior-band corroboration  (flag-confidence 0.7)  [โต๊ะวางกล้วยไม้ (console)]
   - why: identity is owner-only semantic truth and there is NO machine identity read; a hand-typed kind with no owner signature and no unique prior-band match is an unverified guess dressed as certainty
   - resolve: confirm the piece identity on the sheet and sign confirmed_kind (or bind a kind-priors band); silence is not verification
19. **[MEDIUM] facade_candidate** @sitting_room — glazed-facade candidate in sitting_room (score 5, glazed_facade, len 4898mm)
   - why: a strong thin-line run along the room's south edge looks like a glazed facade / window wall, but glass-vs-wall is an owner call
   - resolve: set facade true|false in confirm_facade_stub, sign `by`, and merge into placement-review.json confirmed[]
20. **[MEDIUM] zone_open** @sitting_room — 1 zone_open flag(s) in sitting_room
   - why: an open below-grade / outdoor zone PROPOSAL the machine refuses to auto-decide -- is this element indoor-this-floor or below grade / outside?
   - resolve: sign the zone on the piece (confirmed_zone) to resolve; STRONG/MEDIUM/LOW confidence lives in the gate stdout, not the marker
21. **[LOW] glazing_unresolved** — 294 unresolved global glazing-line candidates (246 strong) -- the raw pile facade_reader distils per-room
   - why: each is a thin-line run that MIGHT be glass; the pile is a review artifact (furniture double-lines can score 'strong'), not per-room truth
   - resolve: confirm real glass runs and copy their segments into the walls JSON manual_additions with a signed `by`; ignore the rest
22. **[LOW] long_thin** @master_bedroom — 1 long_thin flag(s) in master_bedroom
   - why: a narrow dropped component that MIGHT be a slim real piece (a shelf/ledge), not a dimension tick
   - resolve: confirm on the sheet; if a real piece, add it to the spec
23. **[LOW] zone_exterior_linework** @sitting_room — 1 zone_exterior_linework flag(s) in sitting_room
   - why: a candidate that may be exterior linework drawn through the storey
   - resolve: confirm indoor/outdoor and sign it
24. **[LOW] piece_added** @bedroom_suite — ตู้/ชั้น BF10 (250x60x280): NEW piece this round (absent last round)  (flag-confidence 0.5)  [ตู้/ชั้น BF10 (250x60x280)]
   - why: a piece appeared in the rebuild the prior round did not have -- usually intentional, but a silently-added piece should still be seen
   - resolve: confirm the piece belongs in this room; if spurious, remove it
25. **[LOW] piece_added** @bedroom_suite — ตู้เสื้อผ้า BF09-2 (150x60x280): NEW piece this round (absent last round)  (flag-confidence 0.5)  [ตู้เสื้อผ้า BF09-2 (150x60x280)]
   - why: a piece appeared in the rebuild the prior round did not have -- usually intentional, but a silently-added piece should still be seen
   - resolve: confirm the piece belongs in this room; if spurious, remove it
26. **[LOW] piece_added** @bedroom_suite — ตู้เสื้อผ้าเหนือเตียง BF09-3 (330x60x280): NEW piece this round (absent last round)  (flag-confidence 0.5)  [ตู้เสื้อผ้าเหนือเตียง BF09-3 (330x60x280)]
   - why: a piece appeared in the rebuild the prior round did not have -- usually intentional, but a silently-added piece should still be seen
   - resolve: confirm the piece belongs in this room; if spurious, remove it
27. **[LOW] piece_added** @bedroom_suite — ผนังระแนงหัวเตียง BF14 (325x10x280): NEW piece this round (absent last round)  (flag-confidence 0.5)  [ผนังระแนงหัวเตียง BF14 (325x10x280)]
   - why: a piece appeared in the rebuild the prior round did not have -- usually intentional, but a silently-added piece should still be seen
   - resolve: confirm the piece belongs in this room; if spurious, remove it
28. **[LOW] piece_added** @sitting_room — ตู้สูง BF12-2 (70x40x280): NEW piece this round (absent last round)  (flag-confidence 0.5)  [ตู้สูง BF12-2 (70x40x280)]
   - why: a piece appeared in the rebuild the prior round did not have -- usually intentional, but a silently-added piece should still be seen
   - resolve: confirm the piece belongs in this room; if spurious, remove it
29. **[LOW] piece_dropped** @bedroom_suite — ตู้เสื้อผ้าเหนือเตียง BF09-3.330x60x280: present last round, GONE this round  (flag-confidence 0.6)  [ตู้เสื้อผ้าเหนือเตียง BF09-3.330x60x280]
   - why: a piece the prior round had vanished in the rebuild -- a rebuild legitimately drops pieces, but a silently-lost one must not go unnoticed
   - resolve: confirm the removal was intentional; if not, restore the piece
30. **[LOW] piece_dropped** @bedroom_suite — ผนังระแนงหัวเตียง BF14.325x10x280: present last round, GONE this round  (flag-confidence 0.6)  [ผนังระแนงหัวเตียง BF14.325x10x280]
   - why: a piece the prior round had vanished in the rebuild -- a rebuild legitimately drops pieces, but a silently-lost one must not go unnoticed
   - resolve: confirm the removal was intentional; if not, restore the piece
31. **[LOW] semantic_change_signed** @sitting_room — เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน): facing rot 0 -> 332 (delta 28), owner-signed -> intentional  (flag-confidence 0.2)  [เก้าอี้ tub ขวา (หันออกสู่ระเบียง), เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)]
   - why: the orientation changed between rounds but an owner signature covers the new rot -- provenance trace, not a doubt
   - resolve: none -- adjudicated by the owner's confirmed_rot signature

## Coverage (which of my doubt-sources actually reported)
- **placement_gate**: READ  verdict=REVIEW  calibration=PASS
- **facade**: READ  candidates=1  resolved=0
- **glazing**: READ  
- **sourceability**: UNWIRED  reviewed=2  errored=0  fail=0  review=0  unwired_elements=15
- **persona**: UNWIRED   — no persona.json for this project -- GAP/ORPHAN coverage cannot be computed (not a pass)
- **cross_signal**: READ  flags=0  eligible_checks=8  errored=0
- **anomaly**: READ  flags=0  errored=0  prior_band=UNWIRED (no corpus priors -- gross built-in bounds only)  no_bound_kinds=['cabinet', 'headboard']
- **confidence**: READ  assessed_fields=57  owner_signed=2  flagged_unsure=16  errored=0
- **rebuild_diff**: READ  shared_rooms=['bedroom_suite', 'sitting_room']  prior_rooms=['bedroom_suite', 'living_room', 'sitting_room']  current_rooms=['bedroom_suite', 'sitting_room']  prior_only=['living_room']  current_only=[]  flags=10 — diffed 2 shared room(s)

READ = reported; ABSENT = artifact/input not present; UNWIRED = ran but no eligible data (never a pass); ERROR = source failed (a blind spot in the audit itself). CRITICAL = confident-WRONG (regression/build-blocker), not doubt; HIGH/MEDIUM/LOW = open doubt.
