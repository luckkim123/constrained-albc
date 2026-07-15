---
title: "N/A: the tracking group is EVAL-side (`eval.py static` summary.json per-axis ss_"
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

# N/A: the tracking group is EVAL-side (`eval.py static` summary.json per-axis ss_

N/A: the tracking group is EVAL-side (`eval.py static` summary.json per-axis ss_error/roll/pitch/yaw). No eval exists for the perflb run, and exp-analyze does not launch eval (hard constraint D4/B8).

[EVIDENCE: `find <perflb run> -name summary.json -o -name '*.npz'` -> empty (verified: no eval artifacts under the perflb run tree)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
