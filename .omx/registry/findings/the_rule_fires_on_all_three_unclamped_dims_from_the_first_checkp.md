---
title: "The rule fires on all three unclamped dims from the first checkpoint after warmu"
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

# The rule fires on all three unclamped dims from the first checkpoint after warmu

The rule fires on all three unclamped dims from the first checkpoint after warmup and holds for the whole run, so the entropy bonus — not the IPO barrier — is the mechanism holding sigma off its floor.

[EVIDENCE: `exp(log_std)` read from `model_<it>.pt` `model_state_dict['log_std']`, both runs, `torch.load` under `/isaac-sim/python.sh`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
