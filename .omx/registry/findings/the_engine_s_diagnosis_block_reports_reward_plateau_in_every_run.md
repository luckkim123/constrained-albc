---
title: "The engine's `DIAGNOSIS` block reports reward plateau in every run. \"Reward conv"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T04:54:21.766685
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The engine's `DIAGNOSIS` block reports reward plateau in every run. "Reward conv

The engine's `DIAGNOSIS` block reports reward plateau in every run. "Reward converged early (Q1-Q2) then plateaued. DORAEMON may be expanding DR too slowly." Additionally on s31 / s32 / Arm N / dgxseed30: "Reward plateaued in last 30% of training." `phase: warmup(1)->plateau(7)`, `plateau: YES since ~5-15%`, `stability cv=0.012`.

[EVIDENCE: engine `DIAGNOSIS` lines, all 7 runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
