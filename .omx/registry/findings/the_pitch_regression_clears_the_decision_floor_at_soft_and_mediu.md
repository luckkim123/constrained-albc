---
title: "The pitch regression clears the decision floor at soft and medium, so it is a RE"
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

# The pitch regression clears the decision floor at soft and medium, so it is a RE

The pitch regression clears the decision floor at soft and medium, so it is a REAL cost and not screening noise, even though it falls outside both H1 clauses.

[EVIDENCE: `floor_verdict` returns REAL for soft pitch (+0.1336 deg) and medium pitch (+0.1204 deg) against the 0.10 deg floor; H1 clause 1 tests the `none` level only and clause 2 tests `hard` att_norm only]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
