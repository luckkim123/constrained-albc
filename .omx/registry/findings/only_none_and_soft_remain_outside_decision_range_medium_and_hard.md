---
title: "Only `none` and `soft` remain outside decision range; `medium` and `hard` are no"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Only `none` and `soft` remain outside decision range; `medium` and `hard` are no

Only `none` and `soft` remain outside decision range; `medium` and `hard` are now both positive, so the student explains more of the teacher latent's variance than a constant predictor does.

[EVIDENCE: X1 aggregate R2 = +0.0134 (none), -0.0466 (soft), +0.1838 (medium), +0.0645 (hard); the `none` value is excluded from any verdict because its denominator collapses — see the repeat-eval table]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

Only `none` and `soft` remain outside decision range; `medium` and `hard` are now both positive, so the student explains more of the teacher latent's variance than a constant predictor does.

[EVIDENCE: X1 aggregate R2 = +0.0134 (none), -0.0466 (soft), +0.1838 (medium), +0.0645 (hard); the `none` value is excluded from any verdict because its denominator collapses — see the repeat-eval table]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
