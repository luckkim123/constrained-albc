---
title: "perflb introduced ONE barrier-penalty spike (baseline had none) — the wider DR b"
tags: ["auto-captured", "trpo_perflb200_260715_023744"]
created: 2026-07-15T04:54:53.987453
updated: 2026-07-15T04:54:53.987453
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# perflb introduced ONE barrier-penalty spike (baseline had none) — the wider DR b

perflb introduced ONE barrier-penalty spike (baseline had none) — the wider DR briefly drove a constraint margin small enough for the barrier gradient to overwhelm reward. Low severity, but a watch item if DR expands further.

[EVIDENCE: engine TIER2 `barrier_penalty` baseline last=-0.1278 spikes(>0.01)=0 max=-0.027 ; perflb last=-0.1200 spikes=1 max=0.211 (+ engine DIAGNOSIS #2 in perflb only)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
