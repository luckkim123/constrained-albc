---
title: "The `none`-level distribution stays DC-bias-like rather than heavy-tailed — the "
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

# The `none`-level distribution stays DC-bias-like rather than heavy-tailed — the 

The `none`-level distribution stays DC-bias-like rather than heavy-tailed — the roll `os_env_q90`/`os_env_mean` ratio is 1.085 for A2 against the anchor's 1.104, so the extra overshoot is a shift of the whole population, not a few blown-up envs.

[EVIDENCE: `summary.json` none/roll — A2 26.793/24.701 = 1.085; anchor 18.797/17.022 = 1.104]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
