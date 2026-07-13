---
title: "The engine \"entropy collapse -> exploration dead\" flag is a generic heuristic th"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The engine "entropy collapse -> exploration dead" flag is a generic heuristic th

The engine "entropy collapse -> exploration dead" flag is a generic heuristic that is NOT a problem here: at convergence low entropy is expected, and clip_fraction 0.005 confirms the policy is not saturating actions — the exact code-exec datum the §8.1 Lead-2 (init_noise_std / max_std revisit) needs, reading healthy.

[EVIDENCE: TB Policy/clip_fraction 0.0048 + Policy/mean_noise_std 0.109 + Policy/entropy −7.62 (Grad/sigma_step 0.0005)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

The engine "entropy collapse -> exploration dead" flag is a generic heuristic that is NOT a problem here: at convergence low entropy is expected, and clip_fraction 0.005 confirms the policy is not saturating actions — the exact code-exec datum the §8.1 Lead-2 (init_noise_std / max_std revisit) needs, reading healthy.

[EVIDENCE: TB Policy/clip_fraction 0.0048 + Policy/mean_noise_std 0.109 + Policy/entropy −7.62 (Grad/sigma_step 0.0005)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
