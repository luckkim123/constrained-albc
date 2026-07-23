---
title: "`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `vx/vy/vz` are NaN at every DR level by construction — the main task is attitude

`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude-only (no `lin_vel` tracking target), so the linear-velocity rows carry no information for this run.

[EVIDENCE: A1 enhanced summary, vx/vy/vz all `nan` across none/soft/medium/hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md

---

## Update (2026-07-21T10:26:11.609658)

`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude-only (no `lin_vel` tracking target), so the linear-velocity rows carry no information for this run.

[EVIDENCE: A1 enhanced summary, vx/vy/vz all `nan` across none/soft/medium/hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md

---

## Update (2026-07-21T10:26:11.609658)

`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude-only with no `lin_vel` tracking target — so the linear-velocity rows carry no information for this run.

[EVIDENCE: A2 enhanced summary, vx/vy/vz all `nan` across none/soft/medium/hard; `COMPARISON SUMMARY` LinVel column `--` at all 4 levels]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
