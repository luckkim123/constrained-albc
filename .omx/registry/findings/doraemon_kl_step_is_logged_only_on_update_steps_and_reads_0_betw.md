---
title: "`DORAEMON/kl_step` is logged only on update steps and reads 0 between them in BO"
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

# `DORAEMON/kl_step` is logged only on update steps and reads 0 between them in BO

`DORAEMON/kl_step` is logged only on update steps and reads 0 between them in BOTH runs, so its final-window difference is not evidence that either curriculum stalled.

[EVIDENCE: strided read of `DORAEMON/kl_step` — E-int is 0.0000 at steps 2350/3012/3675/4337/4735/4947 and 0.12 at 4999; E-obs76 is 0.12 at 1250/2500/3750/4500 and 0 over its last 249 logged points]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
