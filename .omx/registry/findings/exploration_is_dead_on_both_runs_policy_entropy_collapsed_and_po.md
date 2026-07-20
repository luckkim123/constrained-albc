---
title: "Exploration is dead on BOTH runs — `Policy/entropy` collapsed and `Policy/mean_n"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Exploration is dead on BOTH runs — `Policy/entropy` collapsed and `Policy/mean_n

Exploration is dead on BOTH runs — `Policy/entropy` collapsed and `Policy/mean_noise_std` sits just above the `min_std=0.05` floor. This is a shared campaign-wide property, not a P-B1 effect, so it cannot explain the trade.

[EVIDENCE: TB final scalars: `Policy/entropy` -9.0695 (P-B1) vs -7.7728 (REF); `Policy/mean_noise_std` 0.0860 vs 0.0993; engine [DIAGNOSIS] item 1 on P-B1 flags "Entropy collapse + low noise -> exploration dead"; config `entropy_coef=0.003`, `min_std=0.05`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

Exploration is dead on BOTH runs — `Policy/entropy` collapsed and `Policy/mean_noise_std` sits just above the `min_std=0.05` floor. This is a shared campaign-wide property, not a P-B1 effect, so it cannot explain the trade.

[EVIDENCE: TB final scalars: `Policy/entropy` -9.0695 (P-B1) vs -7.7728 (REF); `Policy/mean_noise_std` 0.0860 vs 0.0993; engine [DIAGNOSIS] item 1 on P-B1 flags "Entropy collapse + low noise -> exploration dead"; config `entropy_coef=0.003`, `min_std=0.05`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
