---
title: "The profile's diagnostic engine produces no diagnosis for a distillation run and"
tags: ["auto-captured", "trpo_sdeint_b4b_beta05_s30_260729_153436"]
created: 2026-07-29T07:25:05.571851
updated: 2026-07-30T03:54:24.726456
sources: ["/workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The profile's diagnostic engine produces no diagnosis for a distillation run and

The profile's diagnostic engine produces no diagnosis for a distillation run and cannot be cited for time-series structure here.

[EVIDENCE: analyze_training.py --tier 3 --deep on the B4b run returns "[TIER 1] Core Health STATUS: HEALTHY iters=0 last_step=0", resolves only iter/grad_norm/loss_action/time_collect/time_train as auto targets, emits no [DIAGNOSIS], changepoint, plateau or regime line, and reports both ruptures and hmmlearn unavailable under [DEEP]]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md

---

## Merged from the_profile_s_diagnostic_engine_produces_no_diagnosis_for_this_r.md (2026-07-30T03:54:24.726456)

# The profile's diagnostic engine produces no diagnosis for this run either, so no

The profile's diagnostic engine produces no diagnosis for this run either, so no changepoint, plateau or regime evidence is available for B1b and none is claimed.

[EVIDENCE: `analyze_training.py <b1b run> --tier 3 --deep` prints "[TIER 1] Core Health / STATUS: HEALTHY / iters=0 last_step=0" plus a [TARGETS] line resolving iter/grad_norm/loss_action/time_collect/time_train, with no [DIAGNOSIS], changepoint, plateau or regime output; `ruptures` and `hmmlearn` are additionally unavailable]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md


---

## Merged from the_profile_s_diagnostic_engine_still_returns_no_diagnosis_for_t.md (2026-07-30T03:54:24.726456)

# The profile's diagnostic engine still returns no diagnosis for this subject run,

The profile's diagnostic engine still returns no diagnosis for this subject run, so no changepoint, plateau or regime evidence is claimed here either.

[EVIDENCE: `analyze_training.py <a0g run> --tier 3 --deep` prints "[TIER 1] Core Health / STATUS: HEALTHY / iters=0 last_step=0" with a [TARGETS] line resolving iter/loss_action/grad_norm/time_collect/time_train and no [DIAGNOSIS], changepoint, plateau or regime output]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
