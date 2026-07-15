---
title: "DORAEMON's own entropy proxy improved with the lower gate but `DORAEMON/entropy_"
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

# DORAEMON's own entropy proxy improved with the lower gate but `DORAEMON/entropy_

DORAEMON's own entropy proxy improved with the lower gate but `DORAEMON/entropy_before`==`DORAEMON/entropy_after` within each run — the `_optimize_entropy` accept step is at a fixed point, consistent with the wiki note on the accept step leaking the success floor.

[EVIDENCE: TB final-window `DORAEMON/entropy_before`=`DORAEMON/entropy_after`=-29.24 (baseline) / -21.65 (perflb); `doraemon_success_rate` (`DORAEMON/success_rate`) 0.407->0.712; `DORAEMON/kl_step` tracks the accept step, no anomaly either run]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
