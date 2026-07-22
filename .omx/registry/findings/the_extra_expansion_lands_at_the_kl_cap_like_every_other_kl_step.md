---
title: "The extra expansion lands at the KL cap like every other (kl_step=0.12 at all 19"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-22T01:58:11.799085
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The extra expansion lands at the KL cap like every other (kl_step=0.12 at all 19

The extra expansion lands at the KL cap like every other (kl_step=0.12 at all 19 firings) and ess_ratio stays healthy at 0.75, so the curriculum's importance-sampling did not degrade -- the wider box came from one more gate firing, not from looser steps.

[EVIDENCE: TB DORAEMON/kl_step all 19 nonzero values = 0.12; engine TIER 2 ess_ratio=0.75]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
