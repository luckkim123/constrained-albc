---
title: "Mechanism: the 0–60 ms delay costs ~10% return, pinning most episodes below perf"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Mechanism: the 0–60 ms delay costs ~10% return, pinning most episodes below perf

Mechanism: the 0–60 ms delay costs ~10% return, pinning most episodes below performance_lb=250 so success stays < alpha=0.5; and the delay is NOT a DORAEMON dim, so the curriculum cannot ease it to restore feasibility.

[EVIDENCE: code control_delay_steps absent from doraemon.py _PARAM_DEFS (20 dims, none is delay); config.py performance_lb=250 alpha=0.5, baseline mean return ~247 sits just under lb so any ~10%-costly channel stalls the curriculum]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
