---
title: "teacher dr_harder: DORAEMON curriculum froze before run end (unused headroom)"
tags: ["doraemon", "curriculum", "teacher", "uniform-ceiling", "harddr-bounds", "correction"]
created: 2026-06-06T10:54:54.938651
updated: 2026-07-06T02:12:29.812639
sources: ["diagnose-20260606-194621", "trpo_main_teacher_260525_232805"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# teacher dr_harder: DORAEMON curriculum froze before run end (unused headroom)

Teacher (trpo_main_teacher_260525_232805) DORAEMON stopped expanding DR well before the 5000-iter end: DORAEMON/entropy_before == DORAEMON/entropy_after == -19.68 with DORAEMON/kl_step = 0.0 (no trust-region step => no further widening), while DORAEMON/success_rate=0.968 and ess_ratio=0.883. Reward plateaued by iter 250 (single cross-metric changepoint, success S-curve knee). So the env ended EASY: success saturated far above alpha 0.5 but the curriculum left difficulty headroom unused. EVIDENCE via omx reduce tb-final on train TB (window=200); engine DIAGNOSIS line 1 ('DORAEMON may be expanding DR too slowly'). Re-analysis diagnose-20260606-194621 section doraemon. Consistent with the dr-harder motivation to push DR harder (kl_ub raise).

---

## Update (2026-07-06T02:12:29.812639)

CORRECTION / DEEPER FINDING (2026-05-27, from doraemon_state.pt final Beta params) on the teacher 260525_232805 curriculum: the earlier "curriculum froze / expanding too slowly / ran out of time" framing was INCOMPLETE. The distribution shows DORAEMON essentially HIT ITS UNIFORM CEILING, not that it ran out of time.

FINAL Beta params (doraemon_state.pt): a = [1.9 x15, 1.0], b = [1.9 x15, 7.5].
- Beta(1,1)=uniform. 15/16 params sit at Beta(~1.9,~1.9) = essentially FLAT (slightly center-peaked, just past uniform) => DORAEMON expanded ~15/16 params to cover the FULL HardDR range nearly uniformly.
- 16th param Beta(1.0,7.5) = one-sided skew = ocean_current_strength (nominal=0 start via _NOMINAL_OVERRIDES).

IMPLICATION — the binding limit is END-STATE (b), not kl_ub or iter count: HardDR CONFIG bounds are NARROWER than the policy's competence. DORAEMON did its job and topped out at the uniform ceiling; the config ceiling is simply too low to keep pressuring the policy. success stayed 0.96, mode<0 (infeasible) fired 0x, DRwidth slope was still slightly + only because Beta 1.0->1.9 is a small nudge past uniform while already AT the flat plateau (slope + but near-saturated).

TREATMENT SHIFTS accordingly: to pressure the policy, WIDEN the HardDR config bounds (a human design decision), NOT raise kl_ub or add iterations. This reconciles the DRwidth-slope-still-positive observation with the "DR ended too easy" verdict.

RELATION to alpha / kl_ub findings: this is the "question B" answer (is the HardDR config itself big enough — NO). It is distinct from "question A" (did DORAEMON use its full allowance toward the fixed uniform target — YES, it reached ~uniform). phi_target=uniform=HardDR-range is a FIXED ceiling, so "% of the way to uniform" is a valid measure of allowance-used (A) but NOT an absolute difficulty measure (B); B needs physical authority analysis (e.g. TAM torque vs payload torque).

CAVEAT before widening bounds: confirm the 16D param->name mapping (_PARAM_DEFS order) and that some tiny-range params (water_density etc.) may already be physically "wide enough" even at uniform — needs a per-param physical-span review, not a blanket widening.

VERIFIED: doraemon_state.pt final Beta params (2026-05-27); reconciles with the froze/unused-headroom observation above (kl_step=0, entropy_before==entropy_after) which was the symptom, this is the root cause. Source run trpo_main_teacher_260525_232805.

