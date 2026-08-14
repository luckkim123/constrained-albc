---
title: "The per-dim picture is NOT uniform: the aggregate gain is carried by a few dims "
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

# The per-dim picture is NOT uniform: the aggregate gain is carried by a few dims 

The per-dim picture is NOT uniform: the aggregate gain is carried by a few dims while one regresses, so "the latent got better" is a statement about the total, not about every coordinate.

[EVIDENCE: per-dim `1 - MSE_d/Var_d` at hard — dim 2 +1.0833, dim 8 +0.3390, dim 1 +0.2177, dim 6 +0.2168, dim 5 +0.1250, dim 3 +0.0362 against regressions at dim 0 (-0.3242), dim 7 (-0.0597) and dim 4 (-0.0229); both arms are distilled from the SAME teacher so dim indices correspond]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

The per-dim picture is NOT uniform: the aggregate gain is carried by a few dims while one regresses, so "the latent got better" is a statement about the total, not about every coordinate.

[EVIDENCE: per-dim `1 - MSE_d/Var_d` at hard — dim 2 +1.0833, dim 8 +0.3390, dim 1 +0.2177, dim 6 +0.2168, dim 5 +0.1250, dim 3 +0.0362 against regressions at dim 0 (-0.3242), dim 7 (-0.0597) and dim 4 (-0.0229); both arms are distilled from the SAME teacher so dim indices correspond]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
