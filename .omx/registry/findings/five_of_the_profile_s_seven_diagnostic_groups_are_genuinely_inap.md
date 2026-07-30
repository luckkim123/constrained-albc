---
title: "Five of the profile's seven diagnostic groups are genuinely inapplicable to this"
tags: ["auto-captured", "trpo_sdeint_b4b_beta05_s30_260729_153436"]
created: 2026-07-29T07:25:05.571851
updated: 2026-07-29T07:25:05.571851
sources: ["/workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Five of the profile's seven diagnostic groups are genuinely inapplicable to this

Five of the profile's seven diagnostic groups are genuinely inapplicable to this run, verified by dumping the raw scalar tag set rather than inferred from the engine reporting them empty.

[EVIDENCE: the B4b TB event file contains exactly 8 scalar tags, all under the student/ namespace (dagger_beta, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train), with no Reward/*, Policy/*, Loss/*, Encoder/*, Constraint/* or DORAEMON/* tag present]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
