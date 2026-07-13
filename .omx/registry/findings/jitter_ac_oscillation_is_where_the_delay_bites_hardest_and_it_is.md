---
title: "Jitter (AC oscillation) is where the delay bites hardest and it is NOT confounde"
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

# Jitter (AC oscillation) is where the delay bites hardest and it is NOT confounde

Jitter (AC oscillation) is where the delay bites hardest and it is NOT confounded — at matched `none` e1's att_norm jitter is 4.75x the baseline, because the policy acts on stale state and oscillates around the setpoint.

[EVIDENCE: summary.json none att_norm ss_jitter e1 0.950 vs bl 0.200; roll none jitter e1 1.004 vs bl 0.215]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
