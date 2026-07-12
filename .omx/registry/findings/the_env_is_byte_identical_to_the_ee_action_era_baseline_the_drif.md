---
title: "The env is byte-identical to the ee-action-era baseline — the drift was measured"
tags: ["auto-captured", "trpo_main_teacher_260525_232805"]
created: 2026-07-12T18:26:43.465984
updated: 2026-07-12T18:26:43.465984
sources: ["experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The env is byte-identical to the ee-action-era baseline — the drift was measured

The env is byte-identical to the ee-action-era baseline — the drift was measured with instrumentation eval.py already logs; no `_cumulative_joint1` accumulator was added.

[EVIDENCE: eval.py:610-685 logs joint1_cmd/target/pos per step; eval.py:1171-1176 --flat-target zeros every command channel]
[CONFIDENCE: HIGH]

source report: experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md
