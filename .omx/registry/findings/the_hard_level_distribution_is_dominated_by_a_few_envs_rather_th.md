---
title: "The hard-level distribution is dominated by a few envs rather than uniformly shi"
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The hard-level distribution is dominated by a few envs rather than uniformly shi

The hard-level distribution is dominated by a few envs rather than uniformly shifted: `ss_error_std` is 4.4556 against a mean of 1.3198, a CV of 338% and the highest of any arm at any level in this campaign.

[EVIDENCE: `summary.json hard/att_norm/ss_error_std` 1.1679 (B2) -> 4.4556 (WIDE); jitter shows the same shape, `ss_jitter_std` 0.9294 -> 2.3358]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
