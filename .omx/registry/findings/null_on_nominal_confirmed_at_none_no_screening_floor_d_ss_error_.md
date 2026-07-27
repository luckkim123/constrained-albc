---
title: "NULL-on-nominal confirmed: at `none`, no screening floor (|d ss_error| >= 0.10 d"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T06:42:48.885806
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# NULL-on-nominal confirmed: at `none`, no screening floor (|d ss_error| >= 0.10 d

NULL-on-nominal confirmed: at `none`, no screening floor (|d ss_error| >= 0.10 deg, |d os_env_mean| >= 10 pp, |d n_gt20| >= 15 envs) is crossed on any axis in either direction; the PLAN.md section-7 informal verdict is reproduced on the exact pairing it recorded (anchor eval static_260723_091813). | axis | d ss_error (none) | d os_env_mean (none) | d n_gt20 (none) | floor verdict | |---|---|---|---|---| | roll | -0.027 deg | +2.03 pp | -0.3 envs | BELOW-FLOOR | | pitch | +0.044 deg | +0.24 pp | +0.0 envs | BELOW-FLOOR | | yaw | +0.000 rad/s | -0.71 pp | +0.0 envs | BELOW-FLOOR (NO-FLOOR for yaw ss_error) |

[EVIDENCE: compare.py paired --pair B0c:static_260723_091813:static_260724_073758, floors from _analyze/recompute_metrics.py DECISION_FLOORS]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
