---
title: "The TRPO machinery is healthy and configured identically to the anchor: the line"
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

# The TRPO machinery is healthy and configured identically to the anchor: the line

The TRPO machinery is healthy and configured identically to the anchor: the line search succeeded on every iteration after iter 0 and the KL step held at its budget.

[EVIDENCE: engine `[CONFIG]`/`[TIER 1]`/`[TIER 3]` — max_kl 0.005, ls_kl_margin 1.5, `line_search_success` (`Policy/line_search_success`) last-200 mean 1.00 (only failure is iter 0, in both runs), `kl` loss 0.01, lr 0.00 (fixed)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
