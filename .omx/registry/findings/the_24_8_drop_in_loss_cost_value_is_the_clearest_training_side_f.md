---
title: "The 24.8% drop in `Loss/cost_value` is the clearest training-side fingerprint of"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The 24.8% drop in `Loss/cost_value` is the clearest training-side fingerprint of

The 24.8% drop in `Loss/cost_value` is the clearest training-side fingerprint of the manipulation, since the cost critic's target is the discounted constraint cost and lower action noise plausibly reduces its stochastic spread. The correlation is measured; the noise-to-cost-variance mechanism is an inference, not an isolated measurement.

[EVIDENCE: `Loss/cost_value` 0.59947 (A2) vs 0.79692 (anchor) against `Policy/mean_noise_std` 0.07661 vs 0.08610]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
