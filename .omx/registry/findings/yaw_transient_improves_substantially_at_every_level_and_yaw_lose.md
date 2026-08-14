---
title: "Yaw transient improves substantially at every level and yaw loses its only over-"
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

# Yaw transient improves substantially at every level and yaw loses its only over-

Yaw transient improves substantially at every level and yaw loses its only over-threshold env at hard, at the cost of a sub-floor-class steady-state yaw increase that carries no registered floor.

[EVIDENCE: yaw `os_env_mean` 4.04 -> 1.40, 3.99 -> 1.61, 3.41 -> 1.90, 5.06 -> 3.09 pp; yaw `n_gt20` 0.50 -> 0.00 at hard; yaw `ss_error` +0.0031 / +0.0029 / +0.0024 / +0.0014 rad/s, all NO-FLOOR]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
