---
title: "`Grad/sigma_step` is three orders of magnitude below `Grad/actor_step` in every "
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `Grad/sigma_step` is three orders of magnitude below `Grad/actor_step` in every 

`Grad/sigma_step` is three orders of magnitude below `Grad/actor_step` in every run, which is the mechanism behind the collapsed-entropy/floored-`noise_std` reading: the sigma leg of the update has effectively stopped moving while the mean leg still updates.

[EVIDENCE: TB last-200 means — A1 `Grad/sigma_step` 0.00038 vs `Grad/actor_step` 0.01293 (ratio 0.029); same ordering in ref5k (0.00052 / 0.01568) and extend8k (0.00040 / 0.01477)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md

---

## Update (2026-07-21T10:26:11.609658)

`Grad/sigma_step` is three orders of magnitude below `Grad/actor_step` in every run, which is the mechanism behind the collapsed-entropy/floored-`noise_std` reading: the sigma leg of the update has effectively stopped moving while the mean leg still updates.

[EVIDENCE: TB last-200 means — A1 `Grad/sigma_step` 0.00038 vs `Grad/actor_step` 0.01293 (ratio 0.029); same ordering in ref5k (0.00052 / 0.01568) and extend8k (0.00040 / 0.01477)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
