---
title: "Shape: ss_error rises monotonically with DR level on both axes while overshoot F"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Shape: ss_error rises monotonically with DR level on both axes while overshoot F

Shape: ss_error rises monotonically with DR level on both axes while overshoot FALLS, and every overshoot level stays under the 20% line. The tail count is therefore driven by a widening per-env spread at `hard`, not by a rising central overshoot.

[EVIDENCE: `summary_attitude.png` (P-B1@shared) — SS Error panel roll 0.21/0.31/0.41/0.60 vs Overshoot panel roll 17.0/15.6/14.3/14.1 across none/soft/medium/hard; Survival panel flat at 100%]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

Shape: ss_error rises monotonically with DR level on both axes while overshoot FALLS, and every overshoot level stays under the 20% line. The tail count is therefore driven by a widening per-env spread at `hard`, not by a rising central overshoot.

[EVIDENCE: `summary_attitude.png` (P-B1@shared) — SS Error panel roll 0.21/0.31/0.41/0.60 vs Overshoot panel roll 17.0/15.6/14.3/14.1 across none/soft/medium/hard; Survival panel flat at 100%]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
