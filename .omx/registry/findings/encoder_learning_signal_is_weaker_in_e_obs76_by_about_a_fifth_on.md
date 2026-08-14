---
title: "Encoder learning signal is weaker in E-obs76 by about a fifth on gradient norm a"
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

# Encoder learning signal is weaker in E-obs76 by about a fifth on gradient norm a

Encoder learning signal is weaker in E-obs76 by about a fifth on gradient norm and a third on step size, which is a lead for the re-run rather than a conclusion here.

[EVIDENCE: `Policy/encoder_grad_norm` 0.03976 -> 0.03267 (-17.8%) and `Grad/enc_step` 0.00245 -> 0.00156 (-36.3%), TB final-50 means]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
