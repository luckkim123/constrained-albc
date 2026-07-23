---
title: "The `Reward/yaw_vel` gain is corroborated by the eval's yaw axis, so on that axi"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The `Reward/yaw_vel` gain is corroborated by the eval's yaw axis, so on that axi

The `Reward/yaw_vel` gain is corroborated by the eval's yaw axis, so on that axis it is a real behavioural improvement rather than a shaping artifact; the train/eval disagreement is CONCENTRATED in roll but is not roll-exclusive, since pitch `ss_jitter` regressed 31.9% while pitch `ss_error` improved.

[EVIDENCE: `Reward/yaw_vel` 2.23 vs 2.12 (+5.2%); `summary.json` none/yaw `os_env_mean` 1.943 vs 3.593 (-45.9%); none/pitch `ss_jitter` 0.0958 vs 0.0727 (+31.9%) with none/pitch `ss_error` 0.1863 vs 0.1946 (-4.3%)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
