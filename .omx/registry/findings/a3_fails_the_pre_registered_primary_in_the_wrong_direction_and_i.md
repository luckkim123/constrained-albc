---
title: "A3 fails the pre-registered primary in the wrong direction and is therefore a DI"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# A3 fails the pre-registered primary in the wrong direction and is therefore a DI

A3 fails the pre-registered primary in the wrong direction and is therefore a DISCARD, with the manipulation check passing so the result is attributable to the floor lever itself.

[EVIDENCE: summary.json `none/roll/os_env_mean` A3 21.4858 vs anchor 17.0215 (+26.2%); `none/att_norm/ss_error` hard-level 0.7314 vs 0.7425 (-1.5%); per-dim exp(log_std) from model_4999.pt of both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
