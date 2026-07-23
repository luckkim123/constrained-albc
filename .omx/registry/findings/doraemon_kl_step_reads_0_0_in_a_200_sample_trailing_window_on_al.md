---
title: "`DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — thi"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — thi

`DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — this is a LOGGING artifact, not a stalled curriculum. `DORAEMON/kl_step` has n=5000 samples of which only **19** are non-zero: the tag is written only at the ~20 curriculum update points implied by `step_interval=250` over 5000 iters. The trailing-200 window contains no update point. `DORAEMON/success_rate` by contrast has 4776 of 5000 non-zero and reads 0.808 at iter 4999.

[EVIDENCE: raw TB series, anchor s30]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

`DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — this is a LOGGING artifact, not a stalled curriculum. `DORAEMON/kl_step` has n=5000 samples of which only **19** are non-zero: the tag is written only at the ~20 curriculum update points implied by `step_interval=250` over 5000 iters. The trailing-200 window contains no update point. `DORAEMON/success_rate` by contrast has 4776 of 5000 non-zero and reads 0.808 at iter 4999.

[EVIDENCE: raw TB series, anchor s30]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
