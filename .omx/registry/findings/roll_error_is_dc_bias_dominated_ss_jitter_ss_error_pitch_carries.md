---
title: "Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger "
tags: []
created: 2026-07-20T08:43:43.750477
updated: 2026-07-20T08:43:43.750477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger 

Roll error is DC-bias dominated (ss_jitter << ss_error); pitch carries a larger AC fraction (ss_jitter up to ~0.6-0.7x ss_error). ss_jitter grew in absolute terms post-TAM (roll hard 0.181 -> 0.270 +49%, pitch hard 0.097 -> 0.163 +68%) but stays a minority fraction of ss_error, so there is no oscillatory blow-up.

[EVIDENCE: summary.json MATCHED hard roll ss_error 0.571 vs ss_jitter 0.270 (0.47x); MATCHED pitch none ss_jitter 0.146/ss_error 0.207=0.71, hard 0.163/0.295=0.55; void hard ss_jitter roll 0.181 -> 0.270, pitch 0.097 -> 0.163]

Downstream mechanism (diagnose-20260715-193800 report, generalization section): pitch generalizes more gracefully across DR levels than roll BECAUSE pitch error is mixed DC+AC while roll is DC-bias dominated -- the DC (bias) component is what DR stress disperses.

RESTORED 2026-07-20 (pass-2 gc audit): the 2026-07-20 gc deleted this page as "subsumed by report.md + rule 03", but (a) diagnose-20260715-193800 report line 91 cites this page BY SLUG as the mechanism behind pitch's graceful generalization, and (b) rule 03 codifies only the generic jitter-vs-ss distinction, not this per-axis composition claim. Restored with category session-log -> pattern.

