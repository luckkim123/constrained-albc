---
title: "Anchor degradation across DR is graceful on roll and steepest on the attitude no"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Anchor degradation across DR is graceful on roll and steepest on the attitude no

Anchor degradation across DR is graceful on roll and steepest on the attitude norm. | level | roll.ss_error | roll.os_env_mean | roll.n_gt20 | att_norm.ss_error | survival | |:--|--:|--:|--:|--:|--:| | none | 0.3896 | 15.86 | 12.11 | 0.5805 | 100.00 | | soft | 0.4006 | 14.66 | 8.67 | 0.5957 | 100.00 | | medium | 0.4644 | 14.30 | 9.22 | 0.6988 | 100.00 | | hard | 0.7235 | 14.39 | 10.78 | 1.0496 | 98.96 | `roll.os_env_mean` is essentially flat across DR (15.86 -> 14.39) while `ss_error` nearly doubles: the transient is a property of the plant/policy pair, the steady-state error is what DR loads.

[EVIDENCE: `summary.json`, anchor 3-seed means]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

Anchor degradation across DR is graceful on roll and steepest on the attitude norm. | level | roll.ss_error | roll.os_env_mean | roll.n_gt20 | att_norm.ss_error | survival | |:--|--:|--:|--:|--:|--:| | none | 0.3896 | 15.86 | 12.11 | 0.5805 | 100.00 | | soft | 0.4006 | 14.66 | 8.67 | 0.5957 | 100.00 | | medium | 0.4644 | 14.30 | 9.22 | 0.6988 | 100.00 | | hard | 0.7235 | 14.39 | 10.78 | 1.0496 | 98.96 | `roll.os_env_mean` is essentially flat across DR (15.86 -> 14.39) while `ss_error` nearly doubles: the transient is a property of the plant/policy pair, the steady-state error is what DR loads.

[EVIDENCE: `summary.json`, anchor 3-seed means]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
