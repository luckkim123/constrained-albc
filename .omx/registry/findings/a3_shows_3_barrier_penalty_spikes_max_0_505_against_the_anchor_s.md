---
title: "A3 shows 3 `barrier_penalty` spikes (max 0.505) against the anchor's 0, but thes"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# A3 shows 3 `barrier_penalty` spikes (max 0.505) against the anchor's 0, but thes

A3 shows 3 `barrier_penalty` spikes (max 0.505) against the anchor's 0, but these are not constraint events — the tag logs the LAST line-search candidate including rejected backtracks, and line search succeeded 100% of the time, so a positive isolated reading is a rejected-candidate artifact.

[EVIDENCE: `analyze_training.py` barrier_penalty last=-0.1268 spikes=3 max=0.505 vs anchor last=-0.1244 spikes=0; Policy/line_search_success = 1.0000 for A3; documented TB-tag trap for Train/barrier_penalty]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
