---
title: "Gate A closed at iteration 7250. All 29 expansions were accepted at the KL cap 0"
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Gate A closed at iteration 7250. All 29 expansions were accepted at the KL cap 0

Gate A closed at iteration 7250. All 29 expansions were accepted at the KL cap 0.12; from the 7500 boundary onward `DORAEMON/kl_step` is 0 and all 21 dims sit at Beta(1,1), with `ess_ratio` pinned at exactly 1.000 as the independent confirmation that there is nothing left to importance-reweight.

[EVIDENCE: `~/gate_read.py` Beta state, step_count 13401, 21/21 saturated; `DORAEMON/kl_step` 4.8e-04 -> 5.5e-05 -> 0 across the 6.5-7.25 / 7.25-8 / 8-8.75 windows]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
