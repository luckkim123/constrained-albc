---
title: "Arm N (8192 envs) is NULL: every `none` roll field sits inside the anchor's own "
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

# Arm N (8192 envs) is NULL: every `none` roll field sits inside the anchor's own 

Arm N (8192 envs) is NULL: every `none` roll field sits inside the anchor's own 3-seed band. | level | field | Arm N | anchor | delta | band | |:--|:--|--:|--:|--:|--:| | none | roll.ss_error | 0.3531 | 0.3896 | -9.4% | 56.0% | | none | roll.os_env_mean | 16.083 | 15.862 | +1.4% | 26.2% | | none | roll.n_gt20 | 13.33 | 12.11 | +10.1% | 24.8% | | hard | roll.ss_error | 0.7353 | 0.7235 | +1.6% | 33.7% | | hard | roll.n_gt20 | 8.67 | 10.78 | -19.6% | 64.9% | `survival_pct` at none: 100.00 vs 100.00.

[EVIDENCE: Arm N vs anchor 3-seed mean, with the anchor's own p2p band]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
