---
title: "Both TRPO step sizes are marginally smaller in E-obs76 but the gap is a few perc"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Both TRPO step sizes are marginally smaller in E-obs76 but the gap is a few perc

Both TRPO step sizes are marginally smaller in E-obs76 but the gap is a few percent, far short of anything that would indicate a different optimisation regime.

[EVIDENCE: `Grad/actor_step` 0.02341 -> 0.02062 (-11.9%) and `Grad/sigma_step` 0.00093 -> 0.00087 (-6.5%), TB final-50 means]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
