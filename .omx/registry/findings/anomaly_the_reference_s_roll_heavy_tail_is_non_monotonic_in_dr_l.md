---
title: "ANOMALY — the reference's roll heavy-tail is NON-MONOTONIC in DR level: it more "
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

# ANOMALY — the reference's roll heavy-tail is NON-MONOTONIC in DR level: it more 

ANOMALY — the reference's roll heavy-tail is NON-MONOTONIC in DR level: it more than halves from `none` to `hard` (14.333 -> 6.667), whereas P-B1's doubles (4.333 -> 8.667). The reference has more >20-degree roll envs on nominal physics than on its own hard DR, which is the opposite of the expected direction and means the `hard` roll n_gt20 comparison rests on the reference's best tail level against P-B1's worst.

[EVIDENCE: `summary.json` n_gt20 roll, none vs hard, both evals (reference eval id `static_260715_004654`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

ANOMALY — the reference's roll heavy-tail is NON-MONOTONIC in DR level: it more than halves from `none` to `hard` (14.333 -> 6.667), whereas P-B1's doubles (4.333 -> 8.667). The reference has more >20-degree roll envs on nominal physics than on its own hard DR, which is the opposite of the expected direction and means the `hard` roll n_gt20 comparison rests on the reference's best tail level against P-B1's worst.

[EVIDENCE: `summary.json` n_gt20 roll, none vs hard, both evals (reference eval id `static_260715_004654`)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
