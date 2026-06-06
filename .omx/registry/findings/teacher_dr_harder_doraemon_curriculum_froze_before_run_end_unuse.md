---
title: "teacher dr_harder: DORAEMON curriculum froze before run end (unused headroom)"
tags: ["doraemon", "curriculum", "teacher"]
created: 2026-06-06T10:54:54.938651
updated: 2026-06-06T10:54:54.938651
sources: ["diagnose-20260606-194621"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# teacher dr_harder: DORAEMON curriculum froze before run end (unused headroom)

Teacher (trpo_main_teacher_260525_232805) DORAEMON stopped expanding DR well before the 5000-iter end: DORAEMON/entropy_before == DORAEMON/entropy_after == -19.68 with DORAEMON/kl_step = 0.0 (no trust-region step => no further widening), while DORAEMON/success_rate=0.968 and ess_ratio=0.883. Reward plateaued by iter 250 (single cross-metric changepoint, success S-curve knee). So the env ended EASY: success saturated far above alpha 0.5 but the curriculum left difficulty headroom unused. EVIDENCE via omx reduce tb-final on train TB (window=200); engine DIAGNOSIS line 1 ('DORAEMON may be expanding DR too slowly'). Re-analysis diagnose-20260606-194621 section doraemon. Consistent with the dr-harder motivation to push DR harder (kl_ub raise).
