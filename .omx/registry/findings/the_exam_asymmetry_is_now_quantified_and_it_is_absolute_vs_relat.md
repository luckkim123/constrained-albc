---
title: "The exam asymmetry is now quantified, and it is absolute-vs-relative, not merely"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:53:52.371991
updated: 2026-07-20T05:01:51.634643
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The exam asymmetry is now quantified, and it is absolute-vs-relative, not merely

The exam asymmetry is now quantified, and it is absolute-vs-relative, not merely "wider vs narrower": extend8k's learned DR IS the config ceiling, so ITS soft/medium/hard are fractions of the widest exam this configuration can express. The 5000-run's three deployment-relevant params ended far short of uniform (~14% of range), so its `hard` is a materially softer distribution. This is why the soft/medium/hard cross-run rows stay non-comparable while `none` remains fair — and it also means extend8k's own hard-level scores are NOT an easy-exam artifact.

[EVIDENCE: doraemon_state.pt Beta(dist_a, dist_b) at end of each run]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md

---

## Update (2026-07-20T03:58:45.859914)

The exam asymmetry is now quantified, and it is absolute-vs-relative, not merely "wider vs narrower": extend8k's learned DR IS the config ceiling, so ITS soft/medium/hard are fractions of the widest exam this configuration can express. The 5000-run's three deployment-relevant params ended far short of uniform (~14% of range), so its `hard` is a materially softer distribution. This is why the soft/medium/hard cross-run rows stay non-comparable while `none` remains fair — and it also means extend8k's own hard-level scores are NOT an easy-exam artifact.

[EVIDENCE: doraemon_state.pt Beta(dist_a, dist_b) at end of each run]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md

---

## Update (2026-07-20T05:01:51.634643)

The exam asymmetry is now quantified, and it is absolute-vs-relative, not merely "wider vs narrower": extend8k's learned DR IS the config ceiling, so ITS soft/medium/hard are fractions of the widest exam this configuration can express. The 5000-run's three deployment-relevant params ended far short of uniform (~14% of range), so its `hard` is a materially softer distribution. This is why the soft/medium/hard cross-run rows stay non-comparable while `none` remains fair — and it also means extend8k's own hard-level scores are NOT an easy-exam artifact.

[EVIDENCE: doraemon_state.pt Beta(dist_a, dist_b) at end of each run]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md
