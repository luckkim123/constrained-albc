---
title: "The reward trajectory is the lineage's warmup-then-plateau shape with an almost "
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

# The reward trajectory is the lineage's warmup-then-plateau shape with an almost 

The reward trajectory is the lineage's warmup-then-plateau shape with an almost identical plateau onset, so the extra reward A2 earns is won inside the plateau rather than by converging differently.

[EVIDENCE: engine `[TRENDS]` — A2 phase warmup(1)->plateau(7), plateau since ~10%, cv=0.009, changepoints iter 436 and 3483; anchor plateau since ~10%, cv=0.009, changepoints iter 360 and 3499]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
