# Inspection blindness — literature evidence base (2026-08-04, two sweeps)

Provenance: two workflow sweeps on 2026-08-04. The scite MCP quota was
exhausted (250 calls/month; resets 2026-08-17 UTC; PAYG at
scite.ai/users/me/subscription then reconnect). ALL records below were
retrieved LIVE from public APIs — Crossref REST (api.crossref.org) and PubMed
E-utilities — every DOI/title/author/year comes from an actually-retrieved
record. Nothing is fabricated. Where an ABSTRACT was retrieved, effect sizes
are quoted from it; anything still carrying **[Q]** is a headline number from
model knowledge pending full-text verification (Cowork verification rung,
R7c). Retraction fields checked on retrieved Crossref records: none present.

Consumer: nlm-queue topic-1 entry (bundled with the SEIG deep-read) + STRANGER
SWEEP parameterisation (`qa/reproduction-curriculum.md`) + cold-critic prompt
review. Companion triage: `docs/research/2026-08-04-dr-queue-triage.md` §1.

## Verification-rung results (sweep 2 checked sweep 1's [Q] flags)

- **Drew 2013 gorilla numbers — CONFIRMED from retrieved abstract**: "A
  gorilla, 48 times the size of the average nodule, was inserted in the last
  case… Eighty-three percent of the radiologists did not see the gorilla."
  Both figures now citable.
- **Wolfe 2005 (7%→~30%) — PARTIAL**: retrieved abstract confirms the effect
  and direction ("target rarity leads to disturbingly inaccurate performance");
  the exact percentages remain [Q] pending full text.
- **Bruno 2015 (3-5% / ~30%) — NOT IN RETRIEVED TEXT**: abstract carries no
  numbers; both figures stay [Q].
- **CITATION CORRECTION (sweep 2 caught sweep 1's error)**:
  10.1148/radiol.11110987 is a **1-page letter/comment** (Radiology
  261(3):1000-1, on Andriole et al. 10.1148/radiol.11091276), NOT the SOS
  programmatic review sweep 1 called it. SOS claims below are re-anchored to
  the retrieved experimental corpus (Berbaum 1998 + companions). The wrong
  characterization survived one sweep because the bibliographic record
  matched — the same lesson as the lane's "ข้อสรุปที่ถูกตีตกด้วยเครื่องมือ
  ที่พังยังไม่นับ": a record match is not a content match.

## L2 — Expert miss patterns (sweep 1, Crossref)

1. **Satisfaction of search (SOS)**: detecting one abnormality reduces
   detection of the remaining ones; demonstrated across radiographic
   modalities. — Berbaum et al. experimental corpus:
   https://doi.org/10.1016/s1076-6332(98)80006-8 (chest, eye-tracking),
   https://doi.org/10.1016/j.acra.2004.11.007 (abdominal),
   https://doi.org/10.1016/j.acra.2007.06.001 (SOS × CAD).
2. **SOS is not premature termination**: readers frequently FIXATE the lesions
   they miss — recognition/decision failure, not coverage. "Look harder" is
   not a fix. — Berbaum 1998, https://doi.org/10.1016/s1076-6332(98)80006-8
3. **Expert inattentional blindness**: 83% of radiologists missed a gorilla
   48× nodule size embedded in lung CT (retrieved-abstract CONFIRMED); many
   fixated it. — Drew, Võ & Wolfe 2013,
   https://doi.org/10.1177/0956797613479386
4. **Expertise can INCREASE inattentional blindness** in the expert's own
   domain. — Robson & Tangen 2023, https://doi.org/10.1186/s41235-023-00486-x
5. **Low-prevalence effect**: rare targets are missed far more often
   (direction confirmed; exact 7%→30% [Q]). — Wolfe, Horowitz & Kenner 2005,
   https://doi.org/10.1038/435439a; part correctable by allowing re-review
   (Fleck & Mitroff 2007, https://doi.org/10.1111/j.1467-9280.2007.02006.x),
   part not (Van Wert 2009, https://doi.org/10.3758/app.71.3.541).
6. **Independent double reading is standard of care** in mammography
   screening; inter-reader variability is what makes the second read additive.
   — Skaane 2012, https://doi.org/10.1258/ar.2011.110452; Beam 1996,
   https://doi.org/10.1016/s1076-6332(96)80296-0
7. **Radiology error is epidemiologically stable** ("has not changed since the
   1960s" — retrieved abstract); error reduction is a systems problem, not
   exhortation. Numeric rates [Q]. — Bruno, Walker & Abujudeh 2015,
   https://doi.org/10.1148/rg.2015150023

## L1 — Mechanisms of repeated-exposure blindness (sweep 2, Crossref+PubMed)

1. **Change blindness is structural**: no complete scene representation is
   ever formed; identification stays "extremely difficult, even when changes
   are large and made repeatedly"; attention allocates by high-level interest,
   so low-interest regions go unchecked indefinitely (full abstract
   retrieved). — Rensink, O'Regan & Clark 1997,
   https://doi.org/10.1111/j.1467-9280.1997.tb00427.x; real-world person-swap:
   Simons & Levin 1998, https://doi.org/10.3758/bf03208840 (miss magnitude [Q])
2. **Change blindness blindness**: people grossly overestimate their own
   detection ability ([Q]: majorities predict noticing changes ~0-11% actually
   detect); overconfidence persists and miss variance is carried by IMAGE
   properties, not by who looks — swapping in another confident human does not
   fix it (retrieved: "no advantage to using participants' own metacognitive
   judgements… differences among images … contribute the most"). — Levin et
   al. 2000, https://doi.org/10.1080/135062800394865; Barnas & Ward 2022,
   https://doi.org/10.1016/j.cognition.2022.105208
3. **Sustained inattentional blindness ~half of observers** ([Q] 46%);
   critically, **foreknowledge does not generalize**: viewers who knew the
   gorilla task spotted the KNOWN event and were slightly LESS likely to
   notice two new unexpected events (retrieved verbatim). — Simons & Chabris
   1999, https://doi.org/10.1068/p281059; Simons 2010,
   https://doi.org/10.1068/i0386
4. **Repetition blindness**: the second occurrence of near-identical content
   in rapid sequence fails to individuate ("type recognition without token
   individuation"; magnitudes [Q]). — Kanwisher 1987,
   https://doi.org/10.1016/0010-0277(87)90016-3
5. **Semantic satiation is associative and fast**: meaning-access degrades
   measurably within ~10 repetitions of the same cue while perceptual matching
   stays fast (full abstract retrieved) — staring degrades "is this right?"
   before it degrades seeing. — Tian & Huber 2010,
   https://doi.org/10.1016/j.cogpsych.2010.01.003; measurement-validity caveat
   on the older literature: Esposito & Pelton 1971,
   https://doi.org/10.1037/h0031001
6. **Scene grammar**: scene-consistent (plausible) objects are processed via
   schema shortcuts; violation classes list [Q] (no abstract in record). A
   defect that is PLAUSIBLE for the scene is the blindest class. — Biederman
   1982, https://doi.org/10.1016/0010-0285(82)90007-x
7. **Repeated exposure SHRINKS visual coverage** (closest retrieved answer to
   "how many exposures"): across repeated scene presentations, fixation
   duration increased while saccade length/frequency and fixation spread
   contracted — attention "successively became locally expressed" (full
   abstract retrieved). — Kaspar & König 2011,
   https://doi.org/10.1371/journal.pone.0021719

## L3 — Countermeasures with measured effects (sweep 2, PubMed/Crossref)

1. **Grey-scale inversion helps, but small and conditional**: ROC Az 0.73→0.77
   (p=0.02), and only on primary-class displays (full abstract retrieved). —
   Robinson et al., https://doi.org/10.1259/bjr/27961545
2. **2025 inversion replication: sensitivity NULL, specificity gain only**
   (73.1%→81.3%, attendings only) — inversion behaves as a FALSE-POSITIVE
   filter for the trained eye, not a miss-finder. — Mai et al. 2025,
   https://doi.org/10.1016/j.clinimag.2025.110676
3. **Systematic viewing NULL**: coverage did not correlate with performance
   (r=-.06); novices TRAINED to full coverage performed WORSE (F(2,71)=3.95,
   p=.02); experts are more systematic but imitating that does not transfer.
   — Kok et al. 2016, https://doi.org/10.1007/s10459-015-9624-y
4. **Debiasing ("think better") checklists NULL**, even on bias-engineered
   cases. — Sibbald et al. 2019, https://doi.org/10.1007/s10459-019-09875-8
5. **Content checklists are conditional**: accuracy 0.75 vs 0.49 control when
   the true diagnosis was ON the list; 0.43 (worse than control, ns) when OFF
   it; time cost +30-45% either way (all retrieved). — Kammer et al. 2021,
   https://doi.org/10.1111/medu.14596
6. **Checklist systematic review: a coin flip by TYPE**: 7/14 improved, 6
   null, 1 mixed; TASK-oriented 5/7 wins vs cognitive-process 4/10. —
   Al-Khafaji et al. 2022, https://doi.org/10.1136/bmjopen-2021-058219
7. **Forced-choice pairwise comparison wins the measurement itself**: smallest
   variance, most accurate, most time-efficient vs single-stimulus,
   double-stimulus, similarity rating (retrieved verbatim; image-quality
   domain). — Mantiuk et al. 2012,
   https://doi.org/10.1111/j.1467-8659.2012.03188.x
8. **Side-by-side vs sequential is a TRADE**: meta-analysis (30 tests,
   n=4,145): simultaneous ↑ correct identifications (target present),
   sequential ↑ correct rejections, and the sequential advantage is what
   survived real-world conditions. — Steblay et al. 2001,
   https://doi.org/10.1023/a:1012888715007
9. **Incubation is real and structured**: positive meta-analytic effect;
   larger after LONGER preparation; shrinks when the break is filled with
   high-demand work. — Sio & Ormerod 2009, https://doi.org/10.1037/a0014212
10. **Maker-blindness measured in proofreading**: PREDICTABILITY (prior
    memorisation, high-frequency words, constrained sentences) raises
    overlooking of errors; familiarity helped only when an additional
    feedback CHANNEL was added (auditory), and the gain was a sensitivity
    change. — Pilotti et al. 2009, https://doi.org/10.2466/pms.109.3.627-645
    (+ Pilotti 2004 companion, retrieved)

## L4 — Vigilance & prevalence in production lanes (sweep 2, PubMed)

1. **Vigilance decrement = OVERLOAD** (resource depletion, scales with task
   difficulty), not understimulation. — Warm, Parasuraman & Matthews 2008,
   https://doi.org/10.1518/001872008X312152
2. **Modern synthesis is a hybrid** (resource-control: executive control over
   allocation degrades, attention drifts). — Thomson, Besner & Smilek 2015,
   https://doi.org/10.1177/1745691614556681
3. **Low-prevalence miss = CRITERION SHIFT, not sensitivity loss**; most fixes
   fail; **brief high-prevalence retraining bursts WITH full feedback** hold
   the criterion through later low-prevalence periods (retrieved). — Wolfe et
   al. 2007, https://doi.org/10.1037/0096-3445.136.4.623
4. **The burst countermeasure transfers to professionals in the field** (125
   airport screeners; a single high-prevalence + feedback block improved the
   following low-prevalence block). — Wolfe et al. 2013,
   https://doi.org/10.1167/13.3.33
5. **PERCEIVED prevalence is the lever**: false "you missed targets" feedback
   liberalized criterion and raised hits (at false-alarm cost). — Schwark et
   al. 2012, https://doi.org/10.3758/s13414-012-0354-4
6. **Decrement appears within the FIRST 10 MINUTES of busy shifts** (4 months
   live airport screening, TIP-injected foils); recommendation: shorter
   bouts. — Meuter & Lacherez 2016, https://doi.org/10.1177/0018720815616306
7. **Micro-breaks are CONTESTED**: Ariga & Lleras 2011 positive
   (https://doi.org/10.1016/j.cognition.2010.12.007) but N=498 replication
   found the decrement in ALL groups with Bayesian support for the null —
   treat rest as hygiene, not a guard. — Helton & Russell 2012 (retrieved).
8. **Sequential two-person redundancy beats solo, and BLINDING matters**:
   blinded second inspectors kept full independent search effort; nonblinded
   ones (shown the first inspector's marks) cut their search short. — 2024,
   https://doi.org/10.1038/s41598-024-72210-8

## Protocol implications (merged, mapped to the ladder)

1. **Independence is the active ingredient** (Skaane/Beam; 2024 redundancy):
   blind the second reader to build history AND the first reader's findings;
   independence first, consensus second. Confirms R7c's
   blindness-is-the-instrument law from outside — and adds: showing the
   critic prior marks measurably SHORTENS their search.
2. **After the first defect is found, force a structured re-search of the
   REST of the frame** (SOS): "found and fixed it" is when a second full pass
   pays most. → STRANGER SWEEP should fire after each triage, not only
   pre-gate.
3. **Never prescribe "look harder"**: misses are recognition/decision
   failures on fixated content (Berbaum 1998; Drew 2013). Levers: WHO looks,
   WHAT question is asked, WHEN (before triage anchoring).
4. **Open-ended anomaly mandate for cold critics**: checklists of known
   classes recreate tuned search (Drew; Robson & Tangen; Simons 2010 —
   foreknowledge buys the known class, costs new ones). Verify
   `templates/cold-critic-prompt.md` carries an explicit "anything unexpected,
   whole-frame" clause.
5. **Zone-checklists/systematic scanning are NOT supported as trained
   discipline** (Kok null; trained-coverage novices worse; checklist review =
   coin flip, task-oriented > cognitive). The STRANGER SWEEP survives as a
   forced RE-ASK of cleared zones (SOS + prevalence logic), not as a
   scan-order protocol — parameterise it as "N oldest-cleared zones get the
   stranger question after each triage", never as an eye-path prescription.
6. **Inversion/flip is real but repositioned**: it filters false positives
   for experienced eyes (2025) more than it finds misses (small 2009 Az
   gain, display-dependent). Use flipped/inverted crops when TRIAGING
   disputed items (does the defect survive re-encoding?), not as the primary
   miss-finder. "Change the channel" generalizes: re-encode the artifact
   (mirror, invert, defocus, mask-strip) — Pilotti's added-channel result.
7. **Manage prevalence + criterion**: as renders get cleaner, misses on rare
   defects climb (criterion drift, not acuity). Countermeasures with field
   evidence: seed known-defect foils in review batches (TIP-style — also
   yields a running hit-rate metric per rung); surface the running
   escaped-defect ledger to the inspector (perceived-miss lever); allow
   correction/re-review. In this lane a miss costs far more than a false
   alarm, so a liberal criterion is the correct trade.
8. **Forced-choice paired judgments for critics and the owner** (Mantiuk):
   already the studio's instrument (look_bench --blind, RANK finish line) —
   now citation-grade. Side-by-side for finding differences; add a
   sequential pass as the false-alarm guard (Steblay trade).
9. **Mandatory break between building and judging, with the filler
   specified** (Sio & Ormerod): benefit grows with longer prior work; a
   break filled with heavy cognitive work forfeits the effect. In-house r4b
   data point (1 hour insufficient) is consistent: the gap was filled with
   build work. C1's own look never becomes fresh — budget bouts short
   (decrement within 10 minutes under load) and lean on off-machine rungs.
10. **Builder miss rates are an epidemiological constant to design around**
    (Bruno; Levin/Barnas: confidence is bias, image properties carry the
    miss). Citation-grade grounding for R3 (builder never closes) and R7's
    written-triage-not-taste.
11. **Plausible defects are the blindest class** (Biederman scene grammar):
    anything scene-legal defeats every human pass — exactly the class the
    R9/R9b instruments (contact derivation, universal placement guard) exist
    for. Eye for surprises, instruments for the plausible.
12. **Do not review near-identical variants in rapid sequence** (Kanwisher;
    Kaspar & König: coverage contracts with each exposure; Tian & Huber:
    meaning-judgment degrades within ~10 looks): space variant comparisons,
    interleave unrelated frames, time-box repeated inspection of one element.

## Residual gaps (for the queued DR / post-quota scite pass)

- Exposure-count → miss-rate curve: no parametric study retrieved; anchors are
  coverage contraction "within a handful of presentations" and ~10-repetition
  meaning degradation.
- Time-away DECAY for a maker's own artifact (proofreading-own-text analogue
  retrieved only via predictability; no duration-response curve).
- Label-withholding as a validated countermeasure: not retrieved.
- Full-text verification: Wolfe 2005 exact percentages; Bruno 2015 rates;
  Levin 2000 magnitudes; Simons & Chabris 46%; Kanwisher magnitudes;
  Biederman violation classes. (scite Smart-Citation support/contrast pass
  after 2026-08-17 or PAYG.)

## References

Al-Khafaji, J., et al. (2022). Checklists to reduce diagnostic error: a systematic review. *BMJ Open*. https://doi.org/10.1136/bmjopen-2021-058219
Ariga, A., & Lleras, A. (2011). Brief and rare mental "breaks" keep you focused. *Cognition*. https://doi.org/10.1016/j.cognition.2010.12.007
Barnas, A. J., & Ward, E. J. (2022). Metacognitive judgements of change detection predict change blindness. *Cognition*, 227, 105208. https://doi.org/10.1016/j.cognition.2022.105208
Beam, C. A., Sullivan, D. C., & Layde, P. M. (1996). Effect of human variability on independent double reading in screening mammography. *Academic Radiology*, 3. https://doi.org/10.1016/s1076-6332(96)80296-0
Berbaum, K. S., et al. (1998). Role of faulty visual search in the satisfaction of search effect in chest radiography. *Academic Radiology*. https://doi.org/10.1016/s1076-6332(98)80006-8
Berbaum, K. S., et al. (2005). Satisfaction of search in abdominal contrast studies. *Academic Radiology*. https://doi.org/10.1016/j.acra.2004.11.007
Berbaum, K. S., et al. (2007). Satisfaction of search & CAD in chest radiography. *Academic Radiology*. https://doi.org/10.1016/j.acra.2007.06.001
Biederman, I., et al. (1982). Scene perception: Detecting and judging objects undergoing relational violations. *Cognitive Psychology*. https://doi.org/10.1016/0010-0285(82)90007-x
Bruno, M. A., Walker, E. A., & Abujudeh, H. H. (2015). Understanding and confronting our mistakes. *RadioGraphics*, 35(6). https://doi.org/10.1148/rg.2015150023
Drew, T., Võ, M. L.-H., & Wolfe, J. M. (2013). The invisible gorilla strikes again. *Psychological Science*, 24(9). https://doi.org/10.1177/0956797613479386
Esposito, N. J., & Pelton, L. H. (1971). Review of the measurement of semantic satiation. *Psychological Bulletin*, 75(5). https://doi.org/10.1037/h0031001
Fleck, M. S., & Mitroff, S. R. (2007). Rare targets are rarely missed in correctable search. *Psychological Science*, 18(11). https://doi.org/10.1111/j.1467-9280.2007.02006.x
Helton, W. S., & Russell, P. N. (2012). Brief mental breaks and content-free cues may not keep you focused. *Experimental Brain Research* (retrieved record).
Kammer, J. E., et al. (2021). Differential diagnosis checklists reduce diagnostic error differentially. *Medical Education*. https://doi.org/10.1111/medu.14596
Kanwisher, N. G. (1987). Repetition blindness: Type recognition without token individuation. *Cognition*, 27(2). https://doi.org/10.1016/0010-0277(87)90016-3
Kaspar, K., & König, P. (2011). Overt attention and context factors: the impact of repeated presentations. *PLoS ONE*. https://doi.org/10.1371/journal.pone.0021719
Kok, E. M., et al. (2016). Systematic viewing in radiology: seeing more, missing less? *Advances in Health Sciences Education*. https://doi.org/10.1007/s10459-015-9624-y
Levin, D. T., et al. (2000). Change blindness blindness. *Visual Cognition*, 7(1-3). https://doi.org/10.1080/135062800394865
Mai, M., et al. (2025). Diagnostic value of grayscale inversion imaging for detecting pulmonary nodules. *Clinical Imaging*. https://doi.org/10.1016/j.clinimag.2025.110676
Mantiuk, R. K., Tomaszewska, A., & Mantiuk, R. (2012). Comparison of four subjective methods for image quality assessment. *Computer Graphics Forum*. https://doi.org/10.1111/j.1467-8659.2012.03188.x
Meuter, R. F. I., & Lacherez, P. F. (2016). When and why threats go undetected. *Human Factors*. https://doi.org/10.1177/0018720815616306
Pilotti, M., Chodorow, M., & Schauss, F. (2009). Text familiarity, word frequency, and sentential constraint in proofreading. *Perceptual and Motor Skills*. https://doi.org/10.2466/pms.109.3.627-645
Rensink, R. A., O'Regan, J. K., & Clark, J. J. (1997). To see or not to see: The need for attention to perceive changes in scenes. *Psychological Science*, 8(5). https://doi.org/10.1111/j.1467-9280.1997.tb00427.x
Robinson, J. W., et al. (2013). Grey-scale inversion improves detection of lung nodules. *British Journal of Radiology*. https://doi.org/10.1259/bjr/27961545
Robson, S. G., & Tangen, J. M. (2023). The invisible 800-pound gorilla: Expertise can increase inattentional blindness. *Cognitive Research: Principles and Implications*, 8. https://doi.org/10.1186/s41235-023-00486-x
Schwark, J., Sandry, J., MacDonald, J., & Dolgov, I. (2012). False feedback increases detection of low-prevalence targets. *Attention, Perception, & Psychophysics*. https://doi.org/10.3758/s13414-012-0354-4
Simons, D. J. (2010). Monkeying around with the gorillas in our midst. *i-Perception*, 1(1). https://doi.org/10.1068/i0386
Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst. *Perception*, 28(9). https://doi.org/10.1068/p281059
Simons, D. J., & Levin, D. T. (1998). Failure to detect changes to people during a real-world interaction. *Psychonomic Bulletin & Review*. https://doi.org/10.3758/bf03208840
Sio, U. N., & Ormerod, T. C. (2009). Does incubation enhance problem solving? A meta-analytic review. *Psychological Bulletin*. https://doi.org/10.1037/a0014212
Sibbald, M., et al. (2019). Debiasing versus knowledge retrieval checklists. *Advances in Health Sciences Education*. https://doi.org/10.1007/s10459-019-09875-8
Skaane, P., et al. (2012). Mammography screening using independent double reading with consensus. *Acta Radiologica*, 53. https://doi.org/10.1258/ar.2011.110452
Steblay, N., Dysart, J., Fulero, S., & Lindsay, R. C. L. (2001). Eyewitness accuracy rates in sequential and simultaneous lineup presentations. *Law and Human Behavior*. https://doi.org/10.1023/a:1012888715007
Thomson, D. R., Besner, D., & Smilek, D. (2015). A resource-control account of sustained attention. *Perspectives on Psychological Science*. https://doi.org/10.1177/1745691614556681
Tian, X., & Huber, D. E. (2010). Testing an associative account of semantic satiation. *Cognitive Psychology*, 60(4). https://doi.org/10.1016/j.cogpsych.2010.01.003
Van Wert, M. J., Horowitz, T. S., & Wolfe, J. M. (2009). Even in correctable search, some types of rare targets are frequently missed. *Attention, Perception, & Psychophysics*, 71(3). https://doi.org/10.3758/app.71.3.541
Warm, J. S., Parasuraman, R., & Matthews, G. (2008). Vigilance requires hard mental work and is stressful. *Human Factors*. https://doi.org/10.1518/001872008X312152
Wolfe, J. M., Horowitz, T. S., & Kenner, N. M. (2005). Rare items often missed in visual searches. *Nature*, 435. https://doi.org/10.1038/435439a
Wolfe, J. M., et al. (2007). Low target prevalence is a stubborn source of errors in visual search tasks. *JEP: General*. https://doi.org/10.1037/0096-3445.136.4.623
Wolfe, J. M., et al. (2013). [Prevalence burst transfer in professional airport screeners]. *Journal of Vision*. https://doi.org/10.1167/13.3.33
(2024). Sequential human redundancy in low-prevalence inspection; blinding and social loafing. *Scientific Reports*. https://doi.org/10.1038/s41598-024-72210-8
