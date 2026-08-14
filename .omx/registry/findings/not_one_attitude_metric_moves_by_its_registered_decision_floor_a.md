---
title: "Not one attitude metric moves by its registered decision floor, at any DR level,"
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

# Not one attitude metric moves by its registered decision floor, at any DR level,

Not one attitude metric moves by its registered decision floor, at any DR level, on any axis.

[EVIDENCE: `summary.json` of evals `static_260804_152454` (X1) and `static_260804_145821` (baseline); floors declared in the same files as `ss_error` 0.10, `ss_error_std` 0.60, `n_gt20` 15.0 envs, `os_env_mean` 10.0 pp of the commanded step (NOT deg: `summary.json`'s own `units` block declares `pp_of_step`, and 10 pp is 3.0 deg on the 30 deg roll/pitch step) — the largest `ss_error` move is hard roll +0.0149 and the largest `ss_error_std` move is hard roll +0.2500]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

Not one attitude metric moves by its registered decision floor, at any DR level, on any axis.

[EVIDENCE: `summary.json` of evals `static_260804_152454` (X1) and `static_260804_145821` (baseline); floors declared in the same files as `ss_error` 0.10, `ss_error_std` 0.60, `n_gt20` 15.0 envs, `os_env_mean` 10.0 pp of the commanded step (NOT deg: `summary.json`'s own `units` block declares `pp_of_step`, and 10 pp is 3.0 deg on the 30 deg roll/pitch step) — the largest `ss_error` move is hard roll +0.0149 and the largest `ss_error_std` move is hard roll +0.2500]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
