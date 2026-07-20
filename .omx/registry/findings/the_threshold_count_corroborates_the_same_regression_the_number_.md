---
title: "The threshold count corroborates the same regression: the number of envs whose r"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:25:41.244717
updated: 2026-07-20T03:58:45.859914
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The threshold count corroborates the same regression: the number of envs whose r

The threshold count corroborates the same regression: the number of envs whose roll overshoot exceeds 20% rises 14× at `none`. It is the same distribution seen through a threshold, so it adds confirmation, not independent evidence.

[EVIDENCE: summary.json roll/n_gt20 — recompute_metrics.py:121 `int(np.sum(os_clip > 20.0))` over `os_signed = sign*(peak_env-cur_tgt)/step_mag*100`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md

---

## Update (2026-07-20T03:34:26.111024)

The threshold count corroborates the same regression: the number of envs whose roll overshoot exceeds 20% rises 14× at `none`. It is the same distribution seen through a threshold, so it adds confirmation, not independent evidence.

[EVIDENCE: summary.json roll/n_gt20 — recompute_metrics.py:121 `int(np.sum(os_clip > 20.0))` over `os_signed = sign*(peak_env-cur_tgt)/step_mag*100`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md

---

## Update (2026-07-20T03:53:52.371991)

The threshold count corroborates the same regression: the number of envs whose roll overshoot exceeds 20% rises 14× at `none`. It is the same distribution seen through a threshold, so it adds confirmation, not independent evidence.

[EVIDENCE: summary.json roll/n_gt20 — recompute_metrics.py:121 `int(np.sum(os_clip > 20.0))` over `os_signed = sign*(peak_env-cur_tgt)/step_mag*100`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md

---

## Update (2026-07-20T03:58:45.859914)

The threshold count corroborates the same regression: the number of envs whose roll overshoot exceeds 20% rises 14× at `none`. It is the same distribution seen through a threshold, so it adds confirmation, not independent evidence.

[EVIDENCE: summary.json roll/n_gt20 — recompute_metrics.py:121 `int(np.sum(os_clip > 20.0))` over `os_signed = sign*(peak_env-cur_tgt)/step_mag*100`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md
