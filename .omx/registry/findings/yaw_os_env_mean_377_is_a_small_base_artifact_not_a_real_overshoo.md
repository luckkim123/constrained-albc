---
title: "yaw `os_env_mean` +377% is a small-base artifact, not a real overshoot regressio"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-23T02:21:27.244561
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# yaw `os_env_mean` +377% is a small-base artifact, not a real overshoot regressio

yaw `os_env_mean` +377% is a small-base artifact, not a real overshoot regression: the anchor base is 3.59 and yaw ss_error simultaneously IMPROVED 56%, so the percentage is arithmetically large but rides a near-zero denominator.

[EVIDENCE: summary.json none/yaw os_env_mean 17.14 vs 3.59, ss_error 0.0023 vs 0.0052]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

yaw `os_env_mean` +377% is a small-base artifact, not a real overshoot regression: the anchor base is 3.59 and yaw ss_error simultaneously IMPROVED 56%, so the percentage is arithmetically large but rides a near-zero denominator.

[EVIDENCE: summary.json none/yaw os_env_mean 17.14 vs 3.59, ss_error 0.0023 vs 0.0052]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
