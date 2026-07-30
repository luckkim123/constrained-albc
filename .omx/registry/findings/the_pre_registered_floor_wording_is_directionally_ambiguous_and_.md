---
title: "The pre-registered floor wording is directionally ambiguous and this run exposes"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The pre-registered floor wording is directionally ambiguous and this run exposes

The pre-registered floor wording is directionally ambiguous and this run exposes it: roll `ss_error` moved -0.111 deg, a magnitude exceeding the 0.10 deg floor, so a literal absolute-value reading of "any nominal floor breached" would classify a clear IMPROVEMENT as an H2 trigger.

[EVIDENCE: proposal line 123 fires H2 if "a nominal floor is breached at `none`" in |d| notation and names pitch as the predicted axis, while PLAN.md lines 583-585 define the same threshold as a significance test — "Call an effect REAL only if |d ss_error| >= 0.10 deg ... Below the floors: NULL/INCONCLUSIVE, never worse/better"]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
