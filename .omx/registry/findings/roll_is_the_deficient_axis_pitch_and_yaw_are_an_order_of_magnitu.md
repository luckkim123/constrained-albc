---
title: "Roll is the deficient axis; pitch and yaw are an order of magnitude cleaner on t"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Roll is the deficient axis; pitch and yaw are an order of magnitude cleaner on t

Roll is the deficient axis; pitch and yaw are an order of magnitude cleaner on the tail metric. | axis | ss_error (deg) | p2p | os_env_mean (deg) | n_gt20 (/64) | rise_time (s) | |:--|--:|--:|--:|--:|--:| | roll | 0.3896 | 56.0% | 15.86 | 12.11 | 0.539 | | pitch | 0.3390 | 89.8% | 9.86 | 0.75 | 0.421 | | yaw | 0.0071 | 32.6% | 1.34 | 0.00 | 0.068 | `survival_pct` = 100.00 at none/soft/medium, 98.96 at hard.

[EVIDENCE: `summary.json` none level, 3 seeds, mean / p2p]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

Roll is the deficient axis; pitch and yaw are an order of magnitude cleaner on the tail metric. | axis | ss_error (deg) | p2p | os_env_mean (deg) | n_gt20 (/64) | rise_time (s) | |:--|--:|--:|--:|--:|--:| | roll | 0.3896 | 56.0% | 15.86 | 12.11 | 0.539 | | pitch | 0.3390 | 89.8% | 9.86 | 0.75 | 0.421 | | yaw | 0.0071 | 32.6% | 1.34 | 0.00 | 0.068 | `survival_pct` = 100.00 at none/soft/medium, 98.96 at hard.

[EVIDENCE: `summary.json` none level, 3 seeds, mean / p2p]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
