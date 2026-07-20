---
title: "The hard-level heavy tail is NOT a small-scale ratio artifact — the absolute spr"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:53:52.371991
updated: 2026-07-20T03:58:45.859914
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The hard-level heavy tail is NOT a small-scale ratio artifact — the absolute spr

The hard-level heavy tail is NOT a small-scale ratio artifact — the absolute spread is large too, so the high CV cannot be dismissed as "the mean is tiny so the ratio blows up". That dismissal IS valid at `none` (CV 25.3% on a small mean) but does not carry to `hard`.

[EVIDENCE: static_260717_005643/summary.json roll]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md

---

## Update (2026-07-20T03:58:45.859914)

The hard-level heavy tail is NOT a small-scale ratio artifact — the absolute spread is large too, so the high CV cannot be dismissed as "the mean is tiny so the ratio blows up". That dismissal IS valid at `none` (CV 25.3% on a small mean) but does not carry to `hard`.

[EVIDENCE: static_260717_005643/summary.json roll ss_error / ss_error_std — steady-state only; per rule 03 the transient (overshoot) tail is a SEPARATE failure mode and is not mixed in here]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md
