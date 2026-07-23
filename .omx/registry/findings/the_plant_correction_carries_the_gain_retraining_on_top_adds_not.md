---
title: "The plant correction carries the gain; retraining on top adds nothing measurable"
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

# The plant correction carries the gain; retraining on top adds nothing measurable

The plant correction carries the gain; retraining on top adds nothing measurable and costs a sub-threshold amount of steady-state accuracy. | field | plant shift (B-A) | retrain (C-B) | seeds adverse on retrain | |:--|--:|--:|:--| | roll.ss_error | -0.043 deg | +0.110 deg | 3 / 3 | | roll.rise_time | +0.040 s | +0.147 s | 3 / 3 | | roll.os_env_mean | -3.934 deg | +0.054 deg | 2 / 3 | | roll.n_gt20 | -10.778 envs | +0.556 envs | 2 / 3 | | pitch.ss_error | +0.006 deg | +0.117 deg | 2 / 3 | Per-seed `roll.n_gt20` A -> B: 35.67 -> 16.33 (s30), 21.67 -> 9.00 (s31), 9.67 -> 9.33 (s32).

[EVIDENCE: paired by seed, `none` level, A -> B -> C]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The plant correction carries the gain; retraining on top adds nothing measurable and costs a sub-threshold amount of steady-state accuracy. | field | plant shift (B-A) | retrain (C-B) | seeds adverse on retrain | |:--|--:|--:|:--| | roll.ss_error | -0.043 deg | +0.110 deg | 3 / 3 | | roll.rise_time | +0.040 s | +0.147 s | 3 / 3 | | roll.os_env_mean | -3.934 deg | +0.054 deg | 2 / 3 | | roll.n_gt20 | -10.778 envs | +0.556 envs | 2 / 3 | | pitch.ss_error | +0.006 deg | +0.117 deg | 2 / 3 | Per-seed `roll.n_gt20` A -> B: 35.67 -> 16.33 (s30), 21.67 -> 9.00 (s31), 9.67 -> 9.33 (s32).

[EVIDENCE: paired by seed, `none` level, A -> B -> C]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
