---
title: "Entropy and noise_std are collapsed on BOTH runs (the standing weakness, unchang"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Entropy and noise_std are collapsed on BOTH runs (the standing weakness, unchang

Entropy and noise_std are collapsed on BOTH runs (the standing weakness, unchanged by this probe, per wiki `the_single_real_weakness_exploration_is_dead...`) — bias_ema obs does not touch this. line_search_success (`ls_success`) is pinned at 1.00 on both (Policy/surrogate_loss trust-region step always accepted); Grad/actor_step and Grad/sigma_step are not separately broken out by the engine's tier-3 summary line for either run (both cite the same aggregate `kl=0.01` step-size proxy).

[EVIDENCE: engine deep output — entropy, noise_std, line_search_success (ls_success), kl]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md

---

## Update (2026-07-16T07:19:42.517477)

Entropy and noise_std are collapsed on BOTH runs (the standing weakness, unchanged by this probe, per wiki `the_single_real_weakness_exploration_is_dead...`) — bias_ema obs does not touch this. line_search_success (`ls_success`) is pinned at 1.00 on both (Policy/surrogate_loss trust-region step always accepted); Grad/actor_step and Grad/sigma_step are not separately broken out by the engine's tier-3 summary line for either run (both cite the same aggregate `kl=0.01` step-size proxy).

[EVIDENCE: engine deep output — entropy, noise_std, line_search_success (ls_success), kl]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
