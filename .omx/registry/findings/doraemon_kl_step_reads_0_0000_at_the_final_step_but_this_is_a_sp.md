---
title: "`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging a"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:13:39.392281
updated: 2026-07-20T05:01:51.634643
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging a

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md

---

## Update (2026-07-20T03:25:41.244717)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md

---

## Update (2026-07-20T03:34:26.111024)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md

---

## Update (2026-07-20T03:53:52.371991)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES. (Note the distinction from the saturation finding above: the LOGGING is sparse, and separately the curriculum genuinely did stop expanding at iter 7000 because it reached the ceiling.)

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md

---

## Update (2026-07-20T03:58:45.859914)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES. (Note the distinction from the saturation finding above: the LOGGING is sparse, and separately the curriculum genuinely did stop expanding at iter 7000 because it reached the ceiling.)

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md

---

## Update (2026-07-20T05:01:51.634643)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md

---

## Update (2026-07-20T05:01:51.634643)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-122425/report.md

---

## Update (2026-07-20T05:01:51.634643)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES.

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-123142/report.md

---

## Update (2026-07-20T05:01:51.634643)

`DORAEMON/kl_step` reads 0.0000 at the final step but this is a sparse-logging artifact, NOT a frozen curriculum — 26 of 8000 samples are non-zero, all at the 0.12 target. Sanity gate PASSES. (Note the distinction from the saturation finding above: the LOGGING is sparse, and separately the curriculum genuinely did stop expanding at iter 7000 because it reached the ceiling.)

[EVIDENCE: TB DORAEMON/kl_step — n=8000, nonzero=26, values ∈ {0.1086, 0.12}; entropy_before==entropy_after (−18.20) i.e. final logged step applied no further widening]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md
