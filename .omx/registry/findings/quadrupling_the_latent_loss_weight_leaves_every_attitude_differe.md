---
title: "Quadrupling the latent loss weight leaves every attitude difference against A0 b"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Quadrupling the latent loss weight leaves every attitude difference against A0 b

Quadrupling the latent loss weight leaves every attitude difference against A0 below the declared decision floor, so together with B1a the campaign has now bracketed lambda from both sides and found no decision-grade control effect anywhere in [0, 4].

[EVIDENCE: summary.json decision_floors = {"ss_error": 0.1, "os_env_mean": 10.0, "n_gt20": 15.0}, decision_floors_protocol = "screening n=1 paired same-machine; |delta| below floor = noise"; B1b deltas -0.0069/-0.0155/+0.0361/-0.0744 deg and B1a deltas +0.0347/+0.0200/+0.0192/+0.0741 deg, largest magnitude 0.0744]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
