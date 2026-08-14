---
title: "Roll improves at every DR level and pitch degrades at every DR level, so the wid"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Roll improves at every DR level and pitch degrades at every DR level, so the wid

Roll improves at every DR level and pitch degrades at every DR level, so the widened observation buys roll accuracy with pitch accuracy rather than improving attitude uniformly.

[EVIDENCE: `summary.json` per-axis `ss_error` — roll -0.0856 / -0.0317 / -0.0627 / -0.0651 deg, pitch +0.0612 / +0.1336 / +0.1204 / +0.0953 deg across none/soft/medium/hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
